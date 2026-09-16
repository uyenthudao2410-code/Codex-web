"""Small authenticated HTTP surface for the standalone control plane."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from dataclasses import dataclass
from http.cookies import CookieError, SimpleCookie
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import urlsplit

from .mcp_facade import ControlPlaneMcpFacade
from .store import ControlPlaneError, ControlPlaneStore, PermissionError, ValidationError
from .web_ui import WEB_UI_CSP, WEB_UI_CSS, WEB_UI_HTML, WEB_UI_JAVASCRIPT


MAX_BODY_BYTES = 128 * 1024
AUTH_PATTERN = re.compile(r"^(Bearer|Node) ([A-Za-z0-9_-]{16,512})$")
SOURCE_REVISION_PATTERN = re.compile(r"^[0-9a-f]{40,64}$")
SOURCE_FINGERPRINT_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
SESSION_COOKIE_NAME = "__Host-cp_operator_session"
CSRF_HEADER_NAME = "X-Control-Plane-CSRF"
DEFAULT_WEB_SESSION_TTL_SECONDS = 30 * 60
MAX_LOGIN_ATTEMPTS_PER_WINDOW = 5
LOGIN_WINDOW_SECONDS = 5 * 60
MAX_LOGIN_RATE_LIMIT_KEYS = 4096
BROWSER_READ_ONLY_MAX_TTL_MS = 10 * 60 * 1000


class RateLimitError(ControlPlaneError):
    code = "RATE_LIMITED"


def _web_origin(value: str | None) -> str | None:
    """Validate the one HTTPS origin allowed to host the operator console.

    The standalone server can sit behind a Tailnet HTTPS reverse proxy.  A
    canonical configured origin avoids deriving CSRF policy from an untrusted
    Host header and keeps the console disabled until that HTTPS boundary is
    deliberately chosen.
    """

    origin = str(value or "").strip()
    if not origin:
        return None
    try:
        parsed = urlsplit(origin)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("CONTROL_PLANE_WEB_ORIGIN must be one HTTPS origin without a path.") from exc
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
        or port is not None and not 1 <= port <= 65535
    ):
        raise ValueError("CONTROL_PLANE_WEB_ORIGIN must be one HTTPS origin without a path.")
    # Browsers serialize an Origin without a trailing slash or default HTTPS
    # port. Host names are case-insensitive; a non-default port is significant.
    hostname = parsed.hostname.lower()
    display_host = f"[{hostname}]" if ":" in hostname else hostname
    return f"https://{display_host}{'' if port in {None, 443} else f':{port}'}"


@dataclass(frozen=True)
class _OperatorSession:
    owner_id: str
    csrf_token: str
    expires_at_ms: int


@dataclass(frozen=True)
class _BrowserReadOnlyIntent:
    idempotency_key: str
    expires_at_ms: int


class _OperatorSessions:
    """Process-local, expiry-bound operator sessions and login throttling."""

    def __init__(self, *, ttl_seconds: int = DEFAULT_WEB_SESSION_TTL_SECONDS) -> None:
        if not isinstance(ttl_seconds, int) or isinstance(ttl_seconds, bool) or ttl_seconds < 60:
            raise ValueError("operator session TTL must be at least 60 seconds.")
        self._ttl_ms = ttl_seconds * 1000
        self._sessions: dict[str, _OperatorSession] = {}
        self._read_only_intents: dict[tuple[str, str], _BrowserReadOnlyIntent] = {}
        self._login_attempts: dict[str, tuple[int, int]] = {}
        self._lock = Lock()

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    def _purge(self, now_ms: int) -> None:
        for token, session in tuple(self._sessions.items()):
            if session.expires_at_ms <= now_ms:
                self._sessions.pop(token, None)
        for key in tuple(self._read_only_intents):
            if key[0] not in self._sessions:
                self._read_only_intents.pop(key, None)
        window_ms = LOGIN_WINDOW_SECONDS * 1000
        for remote_address, (_count, started_at_ms) in tuple(self._login_attempts.items()):
            if started_at_ms + window_ms <= now_ms:
                self._login_attempts.pop(remote_address, None)

    def allow_login_attempt(self, remote_address: str) -> bool:
        now_ms = self._now_ms()
        remote_address = str(remote_address or "")[:256]
        with self._lock:
            self._purge(now_ms)
            count, started_at_ms = self._login_attempts.get(remote_address, (0, now_ms))
            if started_at_ms + LOGIN_WINDOW_SECONDS * 1000 <= now_ms:
                count, started_at_ms = 0, now_ms
            if count >= MAX_LOGIN_ATTEMPTS_PER_WINDOW:
                return False
            if remote_address not in self._login_attempts and len(self._login_attempts) >= MAX_LOGIN_RATE_LIMIT_KEYS:
                self._login_attempts.pop(next(iter(self._login_attempts)), None)
            self._login_attempts[remote_address] = (count + 1, started_at_ms)
            return True

    def create(self, *, owner_id: str) -> tuple[str, _OperatorSession]:
        now_ms = self._now_ms()
        token = secrets.token_urlsafe(32)
        session = _OperatorSession(
            owner_id=owner_id,
            csrf_token=secrets.token_urlsafe(32),
            expires_at_ms=now_ms + self._ttl_ms,
        )
        with self._lock:
            self._purge(now_ms)
            self._sessions[token] = session
        return token, session

    def lookup(self, token: str) -> _OperatorSession | None:
        now_ms = self._now_ms()
        with self._lock:
            self._purge(now_ms)
            return self._sessions.get(str(token or ""))

    def invalidate(self, token: str) -> None:
        with self._lock:
            normalized_token = str(token or "")
            self._sessions.pop(normalized_token, None)
            for key in tuple(self._read_only_intents):
                if key[0] == normalized_token:
                    self._read_only_intents.pop(key, None)

    def read_only_intent(
        self,
        *,
        token: str,
        context_id: str,
        context_expires_at_ms: int,
    ) -> _BrowserReadOnlyIntent:
        """Return one short-lived fixed canary intent per live browser session.

        The idempotency key and expiry are server-controlled.  A reload or
        response loss in the same authenticated session therefore replays one
        central action rather than silently creating another local read.
        """
        now_ms = self._now_ms()
        normalized_token = str(token or "")
        normalized_context = str(context_id or "")
        with self._lock:
            self._purge(now_ms)
            if normalized_token not in self._sessions:
                raise PermissionError("operator session is expired or invalid.")
            key = (normalized_token, normalized_context)
            existing = self._read_only_intents.get(key)
            if existing is not None and existing.expires_at_ms > now_ms:
                return existing
            expires_at_ms = min(int(context_expires_at_ms), now_ms + BROWSER_READ_ONLY_MAX_TTL_MS)
            if expires_at_ms <= now_ms:
                raise ValidationError("context is no longer live for the browser canary.")
            intent = _BrowserReadOnlyIntent(
                idempotency_key=f"uiro_{secrets.token_urlsafe(24)}",
                expires_at_ms=expires_at_ms,
            )
            self._read_only_intents[key] = intent
            return intent


def _declared_source_revision(value: str | None) -> str | None:
    revision = str(value or "").strip().lower()
    if not revision:
        return None
    if not SOURCE_REVISION_PATTERN.fullmatch(revision):
        raise ValueError("CONTROL_PLANE_DECLARED_SOURCE_REVISION must be a 40-64 character lowercase Git revision.")
    return revision


def _expected_package_source_sha256(value: str | None) -> str | None:
    fingerprint = str(value or "").strip().lower()
    if not fingerprint:
        return None
    if not SOURCE_FINGERPRINT_PATTERN.fullmatch(fingerprint):
        raise ValueError(
            "CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256 must be a lowercase sha256:<64-hex> fingerprint."
        )
    return fingerprint


def _package_source_sha256(package_root: Path | None = None) -> str:
    """Return a content-free, deterministic fingerprint of package source.

    The value is calculated once at HTTP-server startup from all immediate
    ``*.py`` files in the installed ``control_plane`` package.  File names and
    each file's byte digest are domain-separated before being folded into the
    aggregate, so adding, removing, renaming, or changing a source file changes
    the result without disclosing the source contents or host paths.

    It intentionally does *not* attest the service manager, deployment unit,
    environment, loaded extension modules, or an external source receipt.
    Operators must still compare it to the selected package artifact and the
    service/unit checkout evidence.
    """

    root = (package_root or Path(__file__).resolve().parent).resolve()
    source_files = sorted(path for path in root.glob("*.py") if path.is_file())
    if not source_files:
        raise RuntimeError("control_plane package source files are unavailable for fingerprinting.")

    aggregate = hashlib.sha256()
    for source_path in source_files:
        aggregate.update(source_path.name.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(hashlib.sha256(source_path.read_bytes()).digest())
        aggregate.update(b"\0")
    return f"sha256:{aggregate.hexdigest()}"


class ControlPlaneHttpServer(ThreadingHTTPServer):
    def __init__(
        self,
        address: tuple[str, int],
        store: ControlPlaneStore,
        operator_token: str,
        declared_source_revision: str | None = None,
        expected_package_source_sha256: str | None = None,
        web_origin: str | None = None,
        web_session_ttl_seconds: int = DEFAULT_WEB_SESSION_TTL_SECONDS,
    ) -> None:
        if len(operator_token) < 32:
            raise ValueError("CONTROL_PLANE_OPERATOR_TOKEN must have at least 32 characters.")
        self.store = store
        self.mcp_facade = ControlPlaneMcpFacade(store)
        self.operator_token = operator_token
        self.declared_source_revision = _declared_source_revision(declared_source_revision)
        self.started_at_ms = int(time.time() * 1000)
        # A process-lifetime identifier lets an operator correlate health
        # samples to one server instance. It is deliberately not an attestation
        # of source bytes, configuration, or external process ownership.
        self.service_instance_id = f"cp_{uuid.uuid4().hex}"
        # This is a deterministic fingerprint of the package source that was
        # present when this server process started. It is evidence to compare
        # against a deployment artifact, not a replacement for that artifact's
        # receipt or service-manager provenance.
        self.package_source_sha256 = _package_source_sha256()
        self.expected_package_source_sha256 = _expected_package_source_sha256(expected_package_source_sha256)
        if (
            self.expected_package_source_sha256 is not None
            and self.expected_package_source_sha256 != self.package_source_sha256
        ):
            raise ValueError("CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256 does not match the installed package source.")
        self.web_origin = _web_origin(web_origin)
        self.web_session_ttl_seconds = web_session_ttl_seconds
        self.operator_sessions = _OperatorSessions(ttl_seconds=web_session_ttl_seconds) if self.web_origin else None
        super().__init__(address, ControlPlaneHandler)


class ControlPlaneHandler(BaseHTTPRequestHandler):
    server: ControlPlaneHttpServer
    protocol_version = "HTTP/1.1"

    def log_message(self, _format: str, *_args: Any) -> None:
        # HTTP auth and payloads must never be written to stderr/service logs.
        return

    def _json(
        self,
        status: HTTPStatus,
        payload: dict[str, Any],
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _asset(self, *, content_type: str, body: bytes) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", WEB_UI_CSP)
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        self.end_headers()
        self.wfile.write(body)

    def _storage_unavailable(self) -> None:
        # Do not expose SQLite errors, database paths, or transaction details to
        # the caller. A failed durable write must never be represented as a
        # successfully accepted central intent or action.
        self._json(
            HTTPStatus.SERVICE_UNAVAILABLE,
            {
                "error": {
                    "code": "DURABLE_STORAGE_UNAVAILABLE",
                    "message": "durable control-plane storage is unavailable.",
                }
            },
        )

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BODY_BYTES:
            raise ValidationError("request body length is invalid.")
        try:
            parsed = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationError("request body must be valid JSON.") from exc
        if not isinstance(parsed, dict):
            raise ValidationError("request body must be an object.")
        return parsed

    def _auth(self, expected_kind: str) -> str:
        match = AUTH_PATTERN.fullmatch(str(self.headers.get("Authorization", "")))
        if match is None or match.group(1) != expected_kind:
            raise PermissionError("authentication is required.")
        return match.group(2)

    def _operator(self) -> str:
        token = self._auth("Bearer")
        if not hmac.compare_digest(token, self.server.operator_token):
            raise PermissionError("operator authentication failed.")
        return "owner_default"

    def _require_web_origin(self) -> None:
        if self.server.web_origin is None:
            raise PermissionError("private operator UI is not configured.")
        origin = str(self.headers.get("Origin", "")).strip()
        if not origin or not hmac.compare_digest(origin, self.server.web_origin):
            raise PermissionError("same-origin operator request is required.")

    def _session_cookie_token(self) -> str:
        try:
            parsed = SimpleCookie(str(self.headers.get("Cookie", "")))
        except (CookieError, ValueError):
            raise PermissionError("operator session is invalid.") from None
        morsel = parsed.get(SESSION_COOKIE_NAME)
        if morsel is None:
            raise PermissionError("operator session is required.")
        return str(morsel.value)

    def _operator_session(self) -> tuple[str, _OperatorSession]:
        if self.server.operator_sessions is None:
            raise PermissionError("private operator UI is not configured.")
        token = self._session_cookie_token()
        session = self.server.operator_sessions.lookup(token)
        if session is None:
            raise PermissionError("operator session is expired or invalid.")
        return token, session

    def _ui_operator(self, *, require_csrf: bool = False) -> str:
        _token, session = self._operator_session()
        if require_csrf:
            self._require_web_origin()
            presented = str(self.headers.get(CSRF_HEADER_NAME, ""))
            if not presented or not hmac.compare_digest(presented, session.csrf_token):
                raise PermissionError("operator CSRF validation failed.")
        return session.owner_id

    def _ui_or_bearer_operator(self) -> str:
        if self.headers.get("Authorization"):
            return self._operator()
        return self._ui_operator()

    def _operator_for_admission(self, *, mode: str) -> str:
        """Preserve bearer automation while allowing only browser fail-safe close."""

        if self.headers.get("Authorization"):
            return self._operator()
        owner_id = self._ui_operator(require_csrf=True)
        if mode != "recovery":
            raise PermissionError("browser UI can only close admission; reopen requires the operator runbook.")
        return owner_id

    def _create_ui_read_only_request(self, body: dict[str, Any]) -> dict[str, Any]:
        """Queue exactly the fixed façade canary for one live browser context."""
        if set(body) != {"context_id"}:
            raise ValidationError("browser read-only request payload is invalid.")
        _token, session = self._operator_session()
        owner_id = self._ui_operator(require_csrf=True)
        context_id = self._field(body, "context_id")
        if not isinstance(context_id, str):
            raise ValidationError("context_id is invalid.")
        context = self.server.store.context(owner_id=owner_id, context_id=context_id, require_live=True)
        if self.server.operator_sessions is None:
            raise PermissionError("private operator UI is not configured.")
        intent = self.server.operator_sessions.read_only_intent(
            token=_token,
            context_id=context["context_id"],
            context_expires_at_ms=context["expires_at_ms"],
        )
        result = self.server.store.request_mcp_read_only_workspace_context(
            owner_id=owner_id,
            context_id=context["context_id"],
            idempotency_key=intent.idempotency_key,
            expires_at_ms=intent.expires_at_ms,
            facade_contract={
                key: self.server.mcp_facade.contract[key]
                for key in ("schema_version", "profile", "sha256")
            },
        )
        return {
            key: result[key]
            for key in ("request_id", "action_id", "replayed")
        } | {"expires_at_ms": intent.expires_at_ms}

    def _session_cookie(self, token: str, *, expires: bool = False) -> str:
        if expires:
            return f"{SESSION_COOKIE_NAME}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Strict"
        return (
            f"{SESSION_COOKIE_NAME}={token}; Path=/; Max-Age={self.server.web_session_ttl_seconds}; "
            "HttpOnly; Secure; SameSite=Strict"
        )

    def _health_payload(self) -> dict[str, Any]:
        payload = self.server.store.health()
        payload.update(
            {
                "service": "coding-tools-control-plane",
                "service_instance_id": self.server.service_instance_id,
                "package_source_sha256": self.server.package_source_sha256,
                "expected_package_source_sha256": self.server.expected_package_source_sha256,
                "started_at_ms": self.server.started_at_ms,
                # This is deployment-supplied metadata, not an attestation of
                # loaded bytes. Operators still need service/unit proof.
                "declared_source_revision": self.server.declared_source_revision,
            }
        )
        return payload

    def _overview(self, *, owner_id: str) -> dict[str, Any]:
        """Return bounded central observations; no node credential or raw action payload."""

        work_requests = self.server.store.list_work_requests(owner_id=owner_id)
        return {
            "observation_kind": "central_control_plane_read_model",
            "observed_at_ms": int(time.time() * 1000),
            "health": self._health_payload(),
            "admission": self.server.store.admission_status(),
            # The browser only needs current inventory/readiness and the
            # compact policy state.  A policy digest is useful local/central
            # correlation evidence, but is not required for this UI and stays
            # out of its no-store response along with ownership internals.
            "nodes": [
                {
                    key: node[key]
                    for key in (
                        "device_id", "endpoint_id", "display_name", "revoked_at_ms",
                        "last_seen_at_ms", "runtime_instance_id", "mcp_server_instance_id",
                        "activation_epoch", "contract_version", "readiness", "policy_state",
                        "policy_expires_at_ms", "policy_observed_at_ms", "policy_reason",
                    )
                }
                for node in self.server.store.list_nodes(owner_id=owner_id)
            ],
            "bindings": self.server.store.list_bindings(owner_id=owner_id),
            "contexts": self.server.store.list_contexts(owner_id=owner_id),
            # Browser overview deliberately omits raw objective, criteria and
            # scope text. Those can contain private task data and are not needed
            # to distinguish a saved request from a confirmed local effect.
            "work_requests": [
                {
                    key: request[key]
                    for key in ("request_id", "context_id", "created_at_ms", "expires_at_ms", "canceled_at_ms")
                }
                for request in work_requests
            ],
            # The dashboard needs lifecycle truth, but never raw tool
            # arguments, admission references, local handles or receipt
            # payloads.  Those remain out of the browser read model.
            "actions": self.server.store.list_action_lifecycle(owner_id=owner_id),
            "enrollment_requests": self.server.store.list_enrollment_requests(),
        }

    def _login(self, body: dict[str, Any]) -> tuple[str, _OperatorSession]:
        self._require_web_origin()
        if set(body) != {"operator_token"}:
            raise ValidationError("operator login payload is invalid.")
        if self.server.operator_sessions is None or not self.server.operator_sessions.allow_login_attempt(self.client_address[0]):
            raise RateLimitError("too many operator login attempts; retry later.")
        presented = str(body.get("operator_token") or "")
        if not hmac.compare_digest(presented, self.server.operator_token):
            raise PermissionError("operator authentication failed.")
        return self.server.operator_sessions.create(owner_id="owner_default")

    def _node(self, device_id: str) -> None:
        self.server.store.authenticate_node(device_id=device_id, node_secret=self._auth("Node"))

    @staticmethod
    def _field(body: dict[str, Any], name: str) -> Any:
        if name not in body:
            raise ValidationError(f"{name} is required.")
        return body[name]

    def do_GET(self) -> None:  # noqa: N802
        try:
            if self.server.web_origin is not None and self.path == "/":
                self._asset(content_type="text/html; charset=utf-8", body=WEB_UI_HTML)
                return
            if self.server.web_origin is not None and self.path == "/assets/control-plane-ui.css":
                self._asset(content_type="text/css; charset=utf-8", body=WEB_UI_CSS)
                return
            if self.server.web_origin is not None and self.path == "/assets/control-plane-ui.js":
                self._asset(content_type="application/javascript; charset=utf-8", body=WEB_UI_JAVASCRIPT)
                return
            if self.path == "/healthz":
                payload = self._health_payload()
                self._json(HTTPStatus.OK if payload["ok"] else HTTPStatus.SERVICE_UNAVAILABLE, payload)
                return
            if self.path == "/v1/ui/session":
                _token, session = self._operator_session()
                self._json(
                    HTTPStatus.OK,
                    {"authenticated": True, "expires_at_ms": session.expires_at_ms, "csrf_token": session.csrf_token},
                )
                return
            if self.path == "/v1/ui/overview":
                self._json(HTTPStatus.OK, self._overview(owner_id=self._ui_or_bearer_operator()))
                return
            if self.path == "/v1/nodes":
                self._json(HTTPStatus.OK, {"nodes": self.server.store.list_nodes(owner_id=self._operator())})
                return
            if self.path == "/v1/bindings":
                self._json(HTTPStatus.OK, {"bindings": self.server.store.list_bindings(owner_id=self._operator())})
                return
            if self.path == "/v1/contexts":
                self._json(HTTPStatus.OK, {"contexts": self.server.store.list_contexts(owner_id=self._operator())})
                return
            if self.path == "/v1/work-requests":
                self._json(HTTPStatus.OK, {"work_requests": self.server.store.list_work_requests(owner_id=self._operator())})
                return
            if self.path == "/v1/enrollment-requests":
                self._operator()
                self._json(HTTPStatus.OK, {"enrollment_requests": self.server.store.list_enrollment_requests()})
                return
            if self.path == "/v1/maintenance/admission":
                self._operator()
                self._json(HTTPStatus.OK, self.server.store.admission_status())
                return
            action_match = re.fullmatch(r"/v1/actions/([^/]+)", self.path)
            if action_match:
                self._json(
                    HTTPStatus.OK,
                    self.server.store.action_observation(owner_id=self._operator(), action_id=action_match.group(1)),
                )
                return
            node_match = re.fullmatch(r"/v1/nodes/([^/]+)", self.path)
            if node_match:
                self._json(
                    HTTPStatus.OK,
                    self.server.store.node_observation(owner_id=self._operator(), device_id=node_match.group(1)),
                )
                return
            context_match = re.fullmatch(r"/v1/contexts/([^/]+)", self.path)
            if context_match:
                self._json(
                    HTTPStatus.OK,
                    self.server.store.context(owner_id=self._operator(), context_id=context_match.group(1)),
                )
                return
            request_match = re.fullmatch(r"/v1/work-requests/([^/]+)", self.path)
            if request_match:
                self._json(
                    HTTPStatus.OK,
                    self.server.store.work_request_observation(owner_id=self._operator(), request_id=request_match.group(1)),
                )
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": {"code": "NOT_FOUND", "message": "route does not exist."}})
        except ControlPlaneError as error:
            self._error(error)
        except sqlite3.Error:
            self._storage_unavailable()

    def do_POST(self) -> None:  # noqa: N802
        try:
            body = self._body()
            if self.path == "/v1/ui/login":
                token, session = self._login(body)
                self._json(
                    HTTPStatus.OK,
                    {"authenticated": True, "expires_at_ms": session.expires_at_ms, "csrf_token": session.csrf_token},
                    headers={"Set-Cookie": self._session_cookie(token)},
                )
                return
            if self.path == "/v1/ui/logout":
                if body:
                    raise ValidationError("operator logout payload is invalid.")
                token, _session = self._operator_session()
                self._ui_operator(require_csrf=True)
                if self.server.operator_sessions is not None:
                    self.server.operator_sessions.invalidate(token)
                self._json(
                    HTTPStatus.OK,
                    {"authenticated": False},
                    headers={"Set-Cookie": self._session_cookie("", expires=True)},
                )
                return
            if self.path == "/mcp":
                # The central facade accepts only the operator identity in this
                # pilot. It never forwards this token or body to a node.
                response = self.server.mcp_facade.handle(body, owner_id=self._operator())
                if response is None:
                    self.send_response(HTTPStatus.ACCEPTED)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                else:
                    self._json(HTTPStatus.OK, response)
                return
            if self.path == "/v1/nodes/enroll":
                owner = self._operator()
                result = self.server.store.enroll_node(
                    owner_id=owner,
                    device_id=self._field(body, "device_id"),
                    endpoint_id=self._field(body, "endpoint_id"),
                    display_name=self._field(body, "display_name"),
                )
                self._json(HTTPStatus.CREATED, result)
                return
            if self.path == "/v1/enrollment-requests":
                result = self.server.store.request_enrollment(
                    device_id=self._field(body, "device_id"),
                    endpoint_id=self._field(body, "endpoint_id"),
                    display_name=self._field(body, "display_name"),
                    credential_hash=self._field(body, "credential_hash"),
                )
                self._json(HTTPStatus.CREATED, result)
                return
            request_match = re.fullmatch(r"/v1/enrollment-requests/([^/]+)/approve", self.path)
            if request_match:
                result = self.server.store.approve_enrollment(owner_id=self._operator(), enrollment_id=request_match.group(1))
                self._json(HTTPStatus.OK, result)
                return
            ui_enrollment_match = re.fullmatch(r"/v1/ui/enrollment-requests/([^/]+)/approve", self.path)
            if ui_enrollment_match:
                if body:
                    raise ValidationError("browser enrollment approval payload is invalid.")
                owner_id = self._ui_operator(require_csrf=True)
                result = self.server.store.approve_enrollment(
                    owner_id=owner_id,
                    enrollment_id=ui_enrollment_match.group(1),
                )
                self._json(HTTPStatus.OK, result)
                return
            if self.path == "/v1/maintenance/admission":
                self._operator_for_admission(mode=body.get("mode"))
                mode = self._field(body, "mode")
                result = self.server.store.set_admission_mode(mode=mode)
                self._json(HTTPStatus.OK, result)
                return
            if self.path == "/v1/ui/read-only-requests":
                self._json(HTTPStatus.CREATED, self._create_ui_read_only_request(body))
                return
            binding_match = re.fullmatch(r"/v1/bindings/([^/]+)/revoke", self.path)
            if binding_match:
                result = self.server.store.revoke_binding(owner_id=self._operator(), binding_id=binding_match.group(1))
                self._json(HTTPStatus.OK, result)
                return
            if self.path == "/v1/bindings":
                result = self.server.store.create_binding(
                    owner_id=self._operator(),
                    device_id=self._field(body, "device_id"),
                    workspace_id=self._field(body, "workspace_id"),
                    workspace_generation=self._field(body, "workspace_generation"),
                    display_name=self._field(body, "display_name"),
                )
                self._json(HTTPStatus.CREATED, result)
                return
            context_match = re.fullmatch(r"/v1/contexts/([^/]+)/close", self.path)
            if context_match:
                result = self.server.store.close_context(owner_id=self._operator(), context_id=context_match.group(1))
                self._json(HTTPStatus.OK, result)
                return
            if self.path == "/v1/contexts":
                result = self.server.store.create_context(
                    owner_id=self._operator(),
                    binding_id=self._field(body, "binding_id"),
                    expires_at_ms=self._field(body, "expires_at_ms"),
                )
                self._json(HTTPStatus.CREATED, result)
                return
            request_match = re.fullmatch(r"/v1/work-requests/([^/]+)/cancel", self.path)
            if request_match:
                result = self.server.store.cancel_work_request(owner_id=self._operator(), request_id=request_match.group(1))
                self._json(HTTPStatus.OK, result)
                return
            if self.path == "/v1/work-requests":
                result = self.server.store.create_work_request(
                    owner_id=self._operator(),
                    context_id=self._field(body, "context_id"),
                    objective=self._field(body, "objective"),
                    criteria=self._field(body, "criteria"),
                    scope=self._field(body, "scope"),
                    expires_at_ms=self._field(body, "expires_at_ms"),
                )
                self._json(HTTPStatus.CREATED, result)
                return
            if self.path == "/v1/actions":
                result = self.server.store.seal_action(
                    owner_id=self._operator(),
                    request_id=self._field(body, "request_id"),
                    tool_name=self._field(body, "tool_name"),
                    arguments=self._field(body, "arguments"),
                    idempotency_key=self._field(body, "idempotency_key"),
                    admission_reference=self._field(body, "admission_reference"),
                    expires_at_ms=self._field(body, "expires_at_ms"),
                )
                self._json(HTTPStatus.CREATED, result)
                return
            node_rotate_match = re.fullmatch(r"/v1/nodes/([^/]+)/rotate-credential", self.path)
            if node_rotate_match:
                result = self.server.store.rotate_node_credential(owner_id=self._operator(), device_id=node_rotate_match.group(1))
                self._json(HTTPStatus.OK, result)
                return
            node_revoke_match = re.fullmatch(r"/v1/nodes/([^/]+)/revoke", self.path)
            if node_revoke_match:
                result = self.server.store.revoke_node(owner_id=self._operator(), device_id=node_revoke_match.group(1))
                self._json(HTTPStatus.OK, result)
                return
            node_match = re.fullmatch(r"/v1/nodes/([^/]+)/heartbeat", self.path)
            if node_match:
                device_id = node_match.group(1)
                self._node(device_id)
                result = self.server.store.heartbeat(
                    device_id=device_id,
                    endpoint_id=self._field(body, "endpoint_id"),
                    runtime_instance_id=body.get("runtime_instance_id", ""),
                    mcp_server_instance_id=body.get("mcp_server_instance_id", ""),
                    activation_epoch=body.get("activation_epoch", ""),
                    contract_version=body.get("contract_version", ""),
                    readiness=body.get("readiness", "unknown"),
                    policy_observation=body.get("policy_observation"),
                )
                self._json(HTTPStatus.OK, result)
                return
            node_match = re.fullmatch(r"/v1/nodes/([^/]+)/poll", self.path)
            if node_match:
                device_id = node_match.group(1)
                self._node(device_id)
                self._json(HTTPStatus.OK, {"actions": self.server.store.poll_actions(device_id=device_id, limit=body.get("limit", 10))})
                return
            node_match = re.fullmatch(r"/v1/nodes/([^/]+)/receipts", self.path)
            if node_match:
                device_id = node_match.group(1)
                self._node(device_id)
                result = self.server.store.record_receipt(
                    device_id=device_id,
                    action_id=self._field(body, "action_id"),
                    attempt_id=self._field(body, "attempt_id"),
                    receipt_state=self._field(body, "receipt_state"),
                    local_handle=body.get("local_handle", ""),
                    payload=body.get("payload", {}),
                )
                self._json(HTTPStatus.OK if result["replayed"] else HTTPStatus.CREATED, result)
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": {"code": "NOT_FOUND", "message": "route does not exist."}})
        except ControlPlaneError as error:
            self._error(error)
        except sqlite3.Error:
            self._storage_unavailable()
        except (TypeError, ValueError) as error:
            self._error(ValidationError(str(error)))

    def _error(self, error: ControlPlaneError) -> None:
        status = HTTPStatus.BAD_REQUEST
        if isinstance(error, PermissionError):
            status = HTTPStatus.FORBIDDEN
        elif isinstance(error, RateLimitError):
            status = HTTPStatus.TOO_MANY_REQUESTS
        elif error.code == "NOT_FOUND":
            status = HTTPStatus.NOT_FOUND
        elif error.code == "CONFLICT":
            status = HTTPStatus.CONFLICT
        self._json(status, {"error": {"code": error.code, "message": str(error)}})


def serve_from_environment() -> None:
    database = os.environ.get("CONTROL_PLANE_DB", "./var/control-plane.sqlite3")
    operator_token = os.environ.get("CONTROL_PLANE_OPERATOR_TOKEN", "")
    bind = os.environ.get("CONTROL_PLANE_BIND", "127.0.0.1")
    port = int(os.environ.get("CONTROL_PLANE_PORT", "8765"))
    server = ControlPlaneHttpServer(
        (bind, port),
        ControlPlaneStore(database),
        operator_token,
        os.environ.get("CONTROL_PLANE_DECLARED_SOURCE_REVISION"),
        os.environ.get("CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256"),
        os.environ.get("CONTROL_PLANE_WEB_ORIGIN"),
        int(os.environ.get("CONTROL_PLANE_WEB_SESSION_TTL_SECONDS", str(DEFAULT_WEB_SESSION_TTL_SECONDS))),
    )
    server.serve_forever(poll_interval=0.5)
