"""Small authenticated HTTP surface for the standalone control plane."""

from __future__ import annotations

import base64
import binascii
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
from threading import Lock, Thread
from typing import Any
from urllib.parse import urlsplit

from .mcp_facade import (
    STATELESS_MCP_PROTOCOL_VERSION,
    SUPPORTED_MCP_PROTOCOL_VERSIONS,
    ControlPlaneMcpFacade,
    _response_id,
    _rpc_error,
)
from .mcp_oauth import (
    OAuthAuthenticationError,
    OAuthIntrospectionConfiguration,
    OAuthIntrospectionVerifier,
    oauth_configuration_from_environment,
)
from .store import (
    ConflictError,
    ControlPlaneError,
    ControlPlaneStore,
    PermissionError,
    ValidationError,
)
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
MIN_OPERATOR_TOKEN_BYTES = 32
MAX_OPERATOR_TOKEN_BYTES = 512


class RateLimitError(ControlPlaneError):
    code = "RATE_LIMITED"


class McpAuthenticationError(ControlPlaneError):
    """MCP OAuth authentication needs a resource-metadata challenge."""

    code = "UNAUTHENTICATED"

    def __init__(self, message: str, *, required_scopes: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.required_scopes = required_scopes


class McpAccountLinkPendingError(PermissionError):
    """A verified OAuth identity awaits an explicit local owner decision."""

    code = "OAUTH_ACCOUNT_LINK_PENDING"

    def __init__(self, *, link_request_id: str) -> None:
        super().__init__("OAuth account link is pending owner approval.")
        self.link_request_id = link_request_id


def _operator_token_bytes(value: Any) -> bytes | None:
    """Return one safe operator-token representation without coercing input.

    ``hmac.compare_digest`` accepts either two strings or two byte strings,
    but its string variant deliberately rejects non-ASCII input. Browser JSON
    is untrusted, so converting an object to a string (or comparing a Unicode
    string directly) can turn an ordinary failed login into an internal error.
    The configured token and every presented token therefore have one small,
    explicit ASCII token shape before they reach the constant-time comparison.
    ``None`` deliberately covers wrong types, empty/oversize values, Unicode,
    whitespace, and control characters without disclosing which condition
    failed to the caller.
    """

    if not isinstance(value, str):
        return None
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError:
        return None
    if not MIN_OPERATOR_TOKEN_BYTES <= len(encoded) <= MAX_OPERATOR_TOKEN_BYTES:
        return None
    if any(byte < 33 or byte > 126 for byte in encoded):
        return None
    return encoded


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
        mcp_enabled: bool = True,
        mcp_ingress_only: bool = False,
        mcp_oauth: OAuthIntrospectionConfiguration | None = None,
        mcp_oauth_verifier: OAuthIntrospectionVerifier | None = None,
    ) -> None:
        operator_token_bytes = _operator_token_bytes(operator_token)
        if operator_token_bytes is None:
            raise ValueError(
                "CONTROL_PLANE_OPERATOR_TOKEN must be a 32-512 character printable ASCII token."
            )
        if mcp_ingress_only and not mcp_enabled:
            raise ValueError("an MCP ingress-only listener must enable the MCP route.")
        if mcp_oauth is None and mcp_oauth_verifier is not None:
            raise ValueError("an MCP OAuth verifier requires an MCP OAuth configuration.")
        self.store = store
        self.mcp_oauth = mcp_oauth
        self.mcp_oauth_verifier = (
            mcp_oauth_verifier
            if mcp_oauth_verifier is not None
            else OAuthIntrospectionVerifier(mcp_oauth)
            if mcp_oauth is not None
            else None
        )
        self.mcp_facade = ControlPlaneMcpFacade(
            store,
            oauth_scopes=(mcp_oauth.required_scope,) if mcp_oauth is not None else (),
            oauth_file_read_enabled=bool(mcp_oauth is not None and mcp_oauth.file_read_enabled),
            oauth_permission_requests_enabled=bool(
                mcp_oauth is not None and mcp_oauth.permission_requests_enabled
            ),
            oauth_patch_write_scope=mcp_oauth.patch_write_scope if mcp_oauth is not None else None,
            oauth_approved_patch_enabled=bool(
                mcp_oauth is not None and (
                    mcp_oauth.approved_patch_enabled or mcp_oauth.standing_write_enabled
                )
            ),
            oauth_standing_write_enabled=bool(
                mcp_oauth is not None and mcp_oauth.standing_write_enabled
            ),
            oauth_exec_enabled=bool(mcp_oauth is not None and mcp_oauth.exec_enabled),
        )
        # Keep only bytes so every later constant-time comparison has the
        # same representation. No route needs the raw text token.
        self.operator_token = operator_token_bytes
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
        # A Tunnel receives exactly this listener, never the private UI or
        # enrollment/admin API.  The primary listener can disable `/mcp` once
        # this separate loopback ingress is enabled by serve_from_environment.
        self.mcp_enabled = bool(mcp_enabled)
        self.mcp_ingress_only = bool(mcp_ingress_only)
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
        token = _operator_token_bytes(self._auth("Bearer"))
        if token is None or not hmac.compare_digest(token, self.server.operator_token):
            raise PermissionError("operator authentication failed.")
        return "owner_default"

    def _mcp_required_oauth_scopes(self, body: dict[str, Any]) -> tuple[str, ...]:
        """Choose the verified scope set from the requested public operation.

        The MCP facade independently validates the body before it can create
        an effect.  This small preclassification exists only so a missing
        mutation scope produces the accurate OAuth challenge instead of being
        accepted under the inventory-only resource scope.
        """

        configuration = self.server.mcp_oauth
        if configuration is None:
            return ()
        required = (configuration.required_scope,)
        if body.get("method") != "tools/call":
            return required
        params = body.get("params")
        if not isinstance(params, dict):
            return required
        name = params.get("name")
        if (
            name == "request_permissions"
            and configuration.permission_requests_enabled
        ) or (
            name == "agent_workflow"
            and (configuration.approved_patch_enabled or configuration.standing_write_enabled)
        ):
            if configuration.patch_write_scope is None:
                return required
            return (configuration.required_scope, configuration.patch_write_scope)
        return required

    def _mcp_client(self, *, required_scopes: tuple[str, ...] = ()) -> dict[str, Any]:
        """Authenticate one pilot grant or one verified OAuth access token.

        OAuth mode never falls back to the historical server-issued grant. A
        valid IdP token still needs an explicit local principal mapping before
        it can see inventory; raw token/claims never reach a node or receipt.
        """

        if self.server.mcp_oauth is None:
            return self.server.store.authenticate_mcp_access_token(access_token=self._auth("Bearer"))
        header = self.headers.get("Authorization")
        if not isinstance(header, str) or not header.startswith("Bearer "):
            raise McpAuthenticationError("OAuth authentication is required.", required_scopes=required_scopes)
        token = header[len("Bearer "):]
        if not token or token != token.strip() or "\r" in token or "\n" in token:
            raise McpAuthenticationError("OAuth authentication is required.", required_scopes=required_scopes)
        try:
            identity = (
                self.server.mcp_oauth_verifier.authenticate(token, required_scopes=required_scopes)
                if self.server.mcp_oauth_verifier is not None
                else None
            )
        except OAuthAuthenticationError:
            raise McpAuthenticationError("OAuth authentication is required.", required_scopes=required_scopes) from None
        if identity is None:
            raise McpAuthenticationError("OAuth authentication is required.", required_scopes=required_scopes)
        resolution = self.server.store.resolve_or_request_oauth_principal(
            owner_id="owner_default",
            issuer=identity.issuer,
            subject=identity.subject,
        )
        if resolution["state"] == "linked":
            return {
                "principal_id": str(resolution["principal_id"]),
                "owner_id": str(resolution["owner_id"]),
                "context_id": None,
                "oauth_scopes": frozenset(identity.scopes),
            }
        if resolution["state"] == "pending":
            # OAuth itself succeeded.  Do not issue another login challenge or
            # leak a subject; the private owner Console is the only place that
            # can approve the opaque request.  The request ID is safe to show
            # back to the authenticated caller, so they can tell the owner
            # which pending row to review without copying a bearer or claim.
            raise McpAccountLinkPendingError(
                link_request_id=str(resolution["link_request"]["link_request_id"])
            )
        raise PermissionError("authenticated OAuth account is not authorized for this control plane.")

    def _mcp_oauth_authentication_response(
        self,
        body: dict[str, Any],
        *,
        modern: bool,
        required_scopes: tuple[str, ...] = (),
    ) -> None:
        """Return both HTTP and MCP-level discovery signals for OAuth login."""

        configuration = self.server.mcp_oauth
        if configuration is None:
            raise RuntimeError("OAuth authentication response requires OAuth mode.")
        challenge = configuration.www_authenticate(required_scopes=required_scopes or None)
        request_id = _response_id(body)
        if body.get("method") == "tools/call" and request_id is not None:
            result: dict[str, Any] = {
                "content": [{"type": "text", "text": "OAuth authentication is required before this tool can be used."}],
                "structuredContent": {"code": "OAUTH_AUTHENTICATION_REQUIRED", "execution": "not_started"},
                "isError": True,
                "_meta": {"mcp/www_authenticate": [challenge]},
            }
            if modern:
                result = self.server.mcp_facade._stateless_result(result, cacheable=False)
            payload = {"jsonrpc": "2.0", "id": request_id, "result": result}
        else:
            payload = _rpc_error(request_id, -32001, "Authentication required", {"code": "UNAUTHENTICATED"})
            if request_id is None:
                payload.pop("id", None)
        self._json(HTTPStatus.UNAUTHORIZED, payload, headers={"WWW-Authenticate": challenge})

    def _mcp_oauth_link_pending_response(
        self,
        body: dict[str, Any],
        *,
        modern: bool,
        link_request_id: str,
    ) -> None:
        """Explain account-link approval without treating it as OAuth failure.

        A pending link proves that the resource server already verified an
        access token.  Returning ``WWW-Authenticate`` here would make the
        client repeat the same successful login and could create an onboarding
        loop.  The only correlation value is the opaque link-request ID.
        """

        request_id = _response_id(body)
        message = "OAuth account link is pending owner approval. Give the owner the opaque link request ID shown here."
        if body.get("method") == "tools/call" and request_id is not None:
            result: dict[str, Any] = {
                "content": [{"type": "text", "text": message}],
                "structuredContent": {
                    "code": "OAUTH_ACCOUNT_LINK_PENDING",
                    "execution": "not_started",
                    "account_link_request_id": link_request_id,
                },
                "isError": True,
            }
            if modern:
                result = self.server.mcp_facade._stateless_result(result, cacheable=False)
            payload = {"jsonrpc": "2.0", "id": request_id, "result": result}
        else:
            payload = _rpc_error(
                request_id,
                -32003,
                "OAuth account link pending",
                {
                    "code": "OAUTH_ACCOUNT_LINK_PENDING",
                    "account_link_request_id": link_request_id,
                },
            )
            if request_id is None:
                payload.pop("id", None)
        self._json(HTTPStatus.FORBIDDEN, payload)

    def _mcp_http_protocol(self, body: dict[str, Any]) -> tuple[bool, dict[str, Any] | None]:
        """Validate modern mirrored headers before dispatch, without session state.

        Keep legacy initialize/headerless clients working. A modern marker in
        either the header or body requires both to match; it cannot silently
        downgrade into the legacy path when one of them is missing.
        """
        header_version = self.headers.get("MCP-Protocol-Version")
        params = body.get("params")
        meta = params.get("_meta") if isinstance(params, dict) else None
        body_version = meta.get("io.modelcontextprotocol/protocolVersion") if isinstance(meta, dict) else None
        modern = header_version == STATELESS_MCP_PROTOCOL_VERSION or body_version == STATELESS_MCP_PROTOCOL_VERSION
        request_id = _response_id(body)
        for version in (header_version, body_version):
            if version is not None and (not isinstance(version, str) or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", version) is None):
                return modern, _rpc_error(request_id, -32602, "Protocol version must be a date string.")
            if version is not None and version not in SUPPORTED_MCP_PROTOCOL_VERSIONS:
                return modern, _rpc_error(
                    request_id, -32022, "Unsupported protocol version",
                    {"supported": list(SUPPORTED_MCP_PROTOCOL_VERSIONS), "requested": version},
                )
        if not modern:
            return False, None
        if header_version != body_version:
            return True, _rpc_error(request_id, -32020, "MCP-Protocol-Version must match params._meta protocolVersion.")
        method = body.get("method")
        if not isinstance(method, str) or self.headers.get("Mcp-Method") != method:
            return True, _rpc_error(request_id, -32020, "Mcp-Method must match the JSON-RPC method.")
        if method in {"tools/call", "resources/read", "prompts/get"}:
            name = params.get("uri" if method == "resources/read" else "name")
            header_name = self.headers.get("Mcp-Name")
            if isinstance(header_name, str) and header_name.startswith("=?base64?") and header_name.endswith("?="):
                try:
                    header_name = base64.b64decode(header_name[9:-2], validate=True).decode("utf-8")
                except (ValueError, binascii.Error, UnicodeDecodeError):
                    header_name = None
            elif isinstance(header_name, str) and (
                header_name != header_name.strip()
                or any(not (32 <= ord(char) <= 126 or char == "\t") for char in header_name)
            ):
                header_name = None
            if not isinstance(name, str) or not name or header_name != name:
                return True, _rpc_error(request_id, -32020, "Mcp-Name must match the named request.")
        return True, None

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

    def _create_ui_binding(self, body: dict[str, Any]) -> dict[str, Any]:
        """Create an explicit owner-scoped binding from the private console.

        The browser is deliberately not allowed to submit a path or a policy.
        ``workspace_id`` and ``workspace_generation`` are opaque identifiers
        whose local meaning is checked again by the separately installed node
        policy before it can dequeue anything.
        """
        if set(body) != {"device_id", "workspace_id", "workspace_generation", "display_name"}:
            raise ValidationError("browser binding payload is invalid.")
        owner_id = self._ui_operator(require_csrf=True)
        fields = {name: self._field(body, name) for name in body}
        if any(not isinstance(value, str) for value in fields.values()):
            raise ValidationError("browser binding fields must be strings.")
        return self.server.store.create_binding(owner_id=owner_id, **fields)

    def _create_ui_context(self, body: dict[str, Any]) -> dict[str, Any]:
        """Issue one short-lived context without trusting a browser clock."""
        if set(body) != {"binding_id", "duration_minutes"}:
            raise ValidationError("browser context payload is invalid.")
        owner_id = self._ui_operator(require_csrf=True)
        binding_id = self._field(body, "binding_id")
        duration_minutes = self._field(body, "duration_minutes")
        if not isinstance(binding_id, str) or isinstance(duration_minutes, bool) or not isinstance(duration_minutes, int):
            raise ValidationError("browser context fields are invalid.")
        # This is a temporary local authority window, not a server session or
        # a policy lifetime. Keep the browser path bounded from both sides.
        if not 5 <= duration_minutes <= 24 * 60:
            raise ValidationError("browser context duration must be between 5 minutes and 24 hours.")
        expires_at_ms = self.server.store.clock() + duration_minutes * 60 * 1000
        return self.server.store.create_context(
            owner_id=owner_id,
            binding_id=binding_id,
            expires_at_ms=expires_at_ms,
        )

    def _ui_revoke_binding(self, binding_id: str, body: dict[str, Any]) -> dict[str, Any]:
        if body:
            raise ValidationError("browser binding revocation payload is invalid.")
        return self.server.store.revoke_binding(
            owner_id=self._ui_operator(require_csrf=True),
            binding_id=binding_id,
        )

    def _ui_close_context(self, context_id: str, body: dict[str, Any]) -> dict[str, Any]:
        if body:
            raise ValidationError("browser context close payload is invalid.")
        return self.server.store.close_context(
            owner_id=self._ui_operator(require_csrf=True),
            context_id=context_id,
        )

    def _create_ui_task_session(self, body: dict[str, Any]) -> dict[str, Any]:
        """Open one Console task pinned to an explicit binding.

        The Console selects only an opaque binding already registered by the
        node; it never submits a Windows path. Principals are opaque IDs from
        the linked-account list so one owner can open tasks for any linked
        account without copying tokens.
        """
        if set(body) != {"principal_id", "binding_id", "label"}:
            raise ValidationError("browser task payload is invalid.")
        owner_id = self._ui_operator(require_csrf=True)
        principal_id = self._field(body, "principal_id")
        binding_id = self._field(body, "binding_id")
        label = self._field(body, "label")
        if not isinstance(principal_id, str) or not isinstance(binding_id, str) or not isinstance(label, str):
            raise ValidationError("browser task fields are invalid.")
        return self.server.store.create_mcp_task_session(
            owner_id=owner_id,
            principal_id=principal_id,
            binding_id=binding_id,
            label=label,
        )

    def _ui_close_task_session(self, task_id: str, body: dict[str, Any]) -> dict[str, Any]:
        if body:
            raise ValidationError("browser task close payload is invalid.")
        return self.server.store.close_owner_mcp_task_session(
            owner_id=self._ui_operator(require_csrf=True),
            task_id=task_id,
        )

    def _ui_record_patch_acceptance(self, action_id: str, body: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"decision"} and set(body) != {"decision", "note"}:
            raise ValidationError("browser patch acceptance payload is invalid.")
        decision = self._field(body, "decision")
        note = body.get("note", "")
        if decision not in ("accepted", "rejected") or not isinstance(note, str):
            raise ValidationError("browser patch acceptance fields are invalid.")
        return self.server.store.record_owner_mcp_patch_acceptance(
            owner_id=self._ui_operator(require_csrf=True),
            action_id=action_id,
            decision=decision,
            note=note,
        )

    def _ui_exec_stop(self, action_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Owner Console stop: fence dispatch and request verified stop.

        Like the MCP path this never claims success for an offline node; the
        actions table stays pending until a terminal stopped receipt arrives.
        """
        if body:
            raise ValidationError("browser exec stop payload is invalid.")
        owner_id = self._ui_operator(require_csrf=True)
        with self.server.store._connection() as connection:
            intent = connection.execute(
                "SELECT principal_id FROM mcp_exec_intents WHERE action_id = ?", (action_id,)
            ).fetchone()
        if intent is None:
            from .store import NotFoundError as _NotFound

            raise _NotFound("exec action does not exist.")
        return self.server.store.request_mcp_exec_stop(
            owner_id=owner_id, principal_id=str(intent["principal_id"]),
            action_id=action_id, requested_by="owner_console",
        )

    def _quarantine_historical_unknown_actions(self, body: dict[str, Any], *, browser: bool) -> dict[str, Any]:
        """Persist a deliberate operator disposition without changing the receipt.

        Browser calls require a same-origin CSRF-protected operator session;
        bearer calls remain available to the protected operator runbook.  The
        store validates each exact action again while holding one transaction.
        """

        if set(body) != {"device_id", "action_ids", "declaration"}:
            raise ValidationError("historical unknown quarantine payload is invalid.")
        owner_id = self._ui_operator(require_csrf=True) if browser else self._operator()
        return self.server.store.quarantine_historical_unknown_actions(
            owner_id=owner_id,
            device_id=self._field(body, "device_id"),
            action_ids=self._field(body, "action_ids"),
            declaration=self._field(body, "declaration"),
        )

    def _quarantine_historical_unobserved_dispatches(self, body: dict[str, Any], *, browser: bool) -> dict[str, Any]:
        """Persist a no-receipt historical disposition without faking a receipt."""

        if set(body) != {"device_id", "action_ids", "declaration", "rationale"}:
            raise ValidationError("historical unobserved dispatch payload is invalid.")
        owner_id = self._ui_operator(require_csrf=True) if browser else self._operator()
        return self.server.store.quarantine_historical_unobserved_dispatches(
            owner_id=owner_id,
            device_id=self._field(body, "device_id"),
            action_ids=self._field(body, "action_ids"),
            declaration=self._field(body, "declaration"),
            rationale=self._field(body, "rationale"),
        )

    def _node_read_only_policy_template(self, device_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Return a live-context template only to its authenticated executor.

        This is not an installed policy and does not change a node. The same-
        user Windows UI must still make an explicit local install decision; the
        returned metadata merely prevents copying a context from another node
        or inventing a facade contract in that UI.
        """
        if set(body) != {"context_id"} or not isinstance(body.get("context_id"), str):
            raise ValidationError("node policy template payload is invalid.")
        self._node(device_id)
        node = self.server.store.node(device_id=device_id)
        context = self.server.store.context(
            owner_id=str(node["owner_id"]),
            context_id=str(body["context_id"]),
            require_live=True,
        )
        if context["device_id"] != device_id or context["endpoint_id"] != node["endpoint_id"]:
            raise PermissionError("context is not assigned to this node.")
        return {"policy_template": self._read_only_policy_template(context)}

    def _read_only_policy_template(self, context: dict[str, Any]) -> dict[str, Any]:
        """Project the sole local-policy fields from an already-live context."""

        return {
            "owner_id": context["owner_id"],
            "device_id": context["device_id"],
            "endpoint_id": context["endpoint_id"],
            "workspace_id": context["workspace_id"],
            "workspace_generation": context["workspace_generation"],
            "expires_at_ms": context["expires_at_ms"],
            "facade_contract": {
                key: self.server.mcp_facade.contract[key]
                for key in ("schema_version", "profile", "sha256")
            },
        }

    def _node_assigned_read_only_policy_template(self, device_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Return a node's single owner-issued policy assignment without a context ID.

        The local owner chooses an already registered root in the Windows UI.
        The authenticated node then asks for the one live context exactly bound
        to that root.  This replaces copying a ``ctx_…`` value into Windows;
        it does not create a context, choose a workspace by display name, or
        grant policy for an unregistered root.
        """

        if set(body) != {"workspace_id", "workspace_generation"}:
            raise ValidationError("node assigned policy payload is invalid.")
        workspace_id = self._field(body, "workspace_id")
        workspace_generation = self._field(body, "workspace_generation")
        if not isinstance(workspace_id, str) or not isinstance(workspace_generation, str):
            raise ValidationError("node assigned policy fields are invalid.")
        self._node(device_id)
        context = self.server.store.assigned_read_only_policy_context(
            device_id=device_id,
            workspace_id=workspace_id,
            workspace_generation=workspace_generation,
        )
        return {"policy_template": self._read_only_policy_template(context)}

    def _register_node_workspace(self, device_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Accept a path-free workspace inventory only from its own node.

        The Electron/node side resolves the selected filesystem path locally.
        This listener receives no path, path hash, node secret in the body, or
        task authority.  A registration is deliberately separate from binding,
        context creation and local policy installation.
        """

        if set(body) != {"workspace_id", "workspace_generation", "display_name", "capabilities"}:
            raise ValidationError("node workspace registration payload is invalid.")
        self._node(device_id)
        return self.server.store.register_node_workspace(
            device_id=device_id,
            workspace_id=self._field(body, "workspace_id"),
            workspace_generation=self._field(body, "workspace_generation"),
            display_name=self._field(body, "display_name"),
            capabilities=self._field(body, "capabilities"),
        )

    def _retire_node_workspace(self, device_id: str, body: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"workspace_id", "workspace_generation"}:
            raise ValidationError("node workspace retirement payload is invalid.")
        self._node(device_id)
        return self.server.store.retire_node_workspace(
            device_id=device_id,
            workspace_id=self._field(body, "workspace_id"),
            workspace_generation=self._field(body, "workspace_generation"),
        )

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
                "mcp_authentication_mode": "oauth_introspection" if self.server.mcp_oauth is not None else "legacy_context_grant",
            }
        )
        return payload

    def _overview(self, *, owner_id: str) -> dict[str, Any]:
        """Return bounded central observations; no node credential or raw action payload."""

        work_requests = self.server.store.list_work_requests(owner_id=owner_id)
        nodes = self.server.store.list_nodes(owner_id=owner_id)
        workspace_registrations = [
            registration
            for node in nodes
            for registration in self.server.store.list_node_workspaces(
                owner_id=owner_id,
                device_id=str(node["device_id"]),
            )
        ]
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
                for node in nodes
            ],
            # A node registration is inventory only. It contains no local path
            # or secret and the browser cannot turn it into a policy/context
            # without the existing explicit binding/context calls below.
            "workspace_registrations": workspace_registrations,
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
            # OAuth requests are deliberately opaque: the Console may decide
            # yes/no using their ID and lifecycle, but never sees the IdP
            # subject, issuer, token, or a workspace target.
            "oauth_link_requests": self.server.store.list_oauth_link_requests(owner_id=owner_id),
            "oauth_principals": self.server.store.list_oauth_principals(owner_id=owner_id),
            # A permission request is a review record only.  The private
            # Console needs its exact bounded scope to decide it, but it never
            # receives patch text, a Windows absolute root or a local policy.
            "permission_requests": self.server.store.list_mcp_permission_requests(owner_id=owner_id),
            # Durable tasks pin one immutable target across many MCP calls so
            # two chats never retarget each other. Acceptance closes the
            # patch loop without reverting files; rejection needs a new patch.
            "task_sessions": self.server.store.list_owner_mcp_task_sessions(owner_id=owner_id),
            "patch_acceptances": self.server.store.list_mcp_patch_acceptances(owner_id=owner_id),
            # Exec stops stay pending until the node proves quiescence; the
            # Console stop button never claims success for an offline node.
            "exec_stops": self.server.store.list_owner_exec_stops(owner_id=owner_id),
        }

    def _login(self, body: dict[str, Any]) -> tuple[str, _OperatorSession]:
        self._require_web_origin()
        if set(body) != {"operator_token"}:
            raise ValidationError("operator login payload is invalid.")
        if self.server.operator_sessions is None or not self.server.operator_sessions.allow_login_attempt(self.client_address[0]):
            raise RateLimitError("too many operator login attempts; retry later.")
        presented = _operator_token_bytes(body.get("operator_token"))
        if presented is None or not hmac.compare_digest(presented, self.server.operator_token):
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
            if self.server.mcp_ingress_only:
                if self.path == "/.well-known/oauth-protected-resource" and self.server.mcp_oauth is not None:
                    self._json(HTTPStatus.OK, self.server.mcp_oauth.protected_resource_metadata())
                    return
                self._json(HTTPStatus.NOT_FOUND, {"error": {"code": "NOT_FOUND", "message": "route does not exist."}})
                return
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
            if self.path == "/v1/mcp-access-grants":
                self._json(
                    HTTPStatus.OK,
                    {"mcp_access_grants": self.server.store.list_mcp_access_grants(owner_id=self._operator())},
                )
                return
            if self.path == "/v1/oauth-principals":
                self._json(
                    HTTPStatus.OK,
                    {"oauth_principals": self.server.store.list_oauth_principals(owner_id=self._operator())},
                )
                return
            if self.path == "/v1/oauth-link-requests":
                self._json(
                    HTTPStatus.OK,
                    {"oauth_link_requests": self.server.store.list_oauth_link_requests(owner_id=self._operator())},
                )
                return
            if self.path == "/v1/permission-requests":
                self._json(
                    HTTPStatus.OK,
                    {"permission_requests": self.server.store.list_mcp_permission_requests(owner_id=self._operator())},
                )
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
            node_workspace_match = re.fullmatch(r"/v1/nodes/([^/]+)/workspace-registrations", self.path)
            if node_workspace_match:
                self._json(
                    HTTPStatus.OK,
                    {"workspace_registrations": self.server.store.list_node_workspaces(
                        owner_id=self._operator(),
                        device_id=node_workspace_match.group(1),
                    )},
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
            if self.server.mcp_ingress_only and self.path != "/mcp":
                self._json(HTTPStatus.NOT_FOUND, {"error": {"code": "NOT_FOUND", "message": "route does not exist."}})
                return
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
                if not self.server.mcp_enabled:
                    self._json(HTTPStatus.NOT_FOUND, {"error": {"code": "NOT_FOUND", "message": "route does not exist."}})
                    return
                modern, protocol_error = self._mcp_http_protocol(body)
                if protocol_error is not None:
                    if protocol_error.get("id") is None:
                        protocol_error.pop("id", None)
                    self._json(HTTPStatus.BAD_REQUEST, protocol_error)
                    return
                required_oauth_scopes = self._mcp_required_oauth_scopes(body)
                try:
                    principal = self._mcp_client(required_scopes=required_oauth_scopes)
                except McpAuthenticationError as error:
                    self._mcp_oauth_authentication_response(
                        body,
                        modern=modern,
                        required_scopes=error.required_scopes,
                    )
                    return
                except McpAccountLinkPendingError as error:
                    self._mcp_oauth_link_pending_response(
                        body,
                        modern=modern,
                        link_request_id=error.link_request_id,
                    )
                    return
                # The private Console's same-origin check protects its
                # cookie-backed browser routes.  A remote OAuth MCP client is
                # authenticated by its bearer token and may legitimately send
                # its own Origin (for example, the OpenAI client host), which
                # must never be compared to the Console origin.  Keep the
                # legacy grant boundary unchanged, and do not emit CORS
                # headers: an Origin alone is not authority in either mode.
                if modern and self.headers.get("Origin") and self.server.mcp_oauth is None:
                    self._require_web_origin()
                response = self.server.mcp_facade.handle(
                    body,
                    owner_id=str(principal["owner_id"]),
                    principal_id=str(principal["principal_id"]),
                    # OAuth inventory is account-scoped rather than bound to
                    # the historical one-context pilot grant.  Preserve None
                    # so a future context-gated OAuth operation cannot treat
                    # the literal text "None" as an authority identifier.
                    granted_context_id=principal["context_id"],
                    oauth_scopes=principal.get("oauth_scopes"),
                    stateless_2026=modern,
                )
                if response is None:
                    self.send_response(HTTPStatus.ACCEPTED)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                else:
                    status = HTTPStatus.OK
                    if modern and "error" in response:
                        status = HTTPStatus.NOT_FOUND if response["error"]["code"] == -32601 else HTTPStatus.BAD_REQUEST
                        if response.get("id") is None:
                            response.pop("id", None)
                    self._json(status, response)
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
            if self.path == "/v1/mcp-access-grants":
                if set(body) != {"context_id", "principal_id", "expires_at_ms"}:
                    raise ValidationError("MCP access grant payload is invalid.")
                result = self.server.store.create_mcp_access_grant(
                    owner_id=self._operator(),
                    context_id=self._field(body, "context_id"),
                    principal_id=self._field(body, "principal_id"),
                    expires_at_ms=self._field(body, "expires_at_ms"),
                )
                self._json(HTTPStatus.CREATED, result)
                return
            if self.path == "/v1/oauth-principals":
                if set(body) != {"issuer", "subject"}:
                    raise ValidationError("OAuth principal link payload is invalid.")
                result = self.server.store.link_oauth_principal(
                    owner_id=self._operator(),
                    issuer=self._field(body, "issuer"),
                    subject=self._field(body, "subject"),
                )
                self._json(HTTPStatus.CREATED, result)
                return
            oauth_principal_revoke_match = re.fullmatch(r"/v1/oauth-principals/([^/]+)/revoke", self.path)
            if oauth_principal_revoke_match:
                if body:
                    raise ValidationError("OAuth principal revocation payload is invalid.")
                result = self.server.store.revoke_oauth_principal(
                    owner_id=self._operator(),
                    principal_id=oauth_principal_revoke_match.group(1),
                )
                self._json(HTTPStatus.OK, result)
                return
            oauth_link_approve_match = re.fullmatch(r"/v1/oauth-link-requests/([^/]+)/approve", self.path)
            if oauth_link_approve_match:
                if body:
                    raise ValidationError("OAuth account-link approval payload is invalid.")
                result = self.server.store.approve_oauth_link_request(
                    owner_id=self._operator(),
                    link_request_id=oauth_link_approve_match.group(1),
                )
                self._json(HTTPStatus.OK, result)
                return
            oauth_link_reject_match = re.fullmatch(r"/v1/oauth-link-requests/([^/]+)/reject", self.path)
            if oauth_link_reject_match:
                if body:
                    raise ValidationError("OAuth account-link rejection payload is invalid.")
                result = self.server.store.reject_oauth_link_request(
                    owner_id=self._operator(),
                    link_request_id=oauth_link_reject_match.group(1),
                )
                self._json(HTTPStatus.OK, result)
                return
            permission_request_approve_match = re.fullmatch(r"/v1/permission-requests/([^/]+)/approve", self.path)
            if permission_request_approve_match:
                if body:
                    raise ValidationError("permission request approval payload is invalid.")
                result = self.server.store.approve_mcp_permission_request(
                    owner_id=self._operator(),
                    permission_request_id=permission_request_approve_match.group(1),
                )
                self._json(HTTPStatus.OK, result)
                return
            permission_request_reject_match = re.fullmatch(r"/v1/permission-requests/([^/]+)/reject", self.path)
            if permission_request_reject_match:
                if body:
                    raise ValidationError("permission request rejection payload is invalid.")
                result = self.server.store.reject_mcp_permission_request(
                    owner_id=self._operator(),
                    permission_request_id=permission_request_reject_match.group(1),
                )
                self._json(HTTPStatus.OK, result)
                return
            mcp_grant_revoke_match = re.fullmatch(r"/v1/mcp-access-grants/([^/]+)/revoke", self.path)
            if mcp_grant_revoke_match:
                if body:
                    raise ValidationError("MCP access grant revocation payload is invalid.")
                result = self.server.store.revoke_mcp_access_grant(
                    owner_id=self._operator(),
                    grant_id=mcp_grant_revoke_match.group(1),
                )
                self._json(HTTPStatus.OK, result)
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
            ui_oauth_link_approve_match = re.fullmatch(r"/v1/ui/oauth-link-requests/([^/]+)/approve", self.path)
            if ui_oauth_link_approve_match:
                if body:
                    raise ValidationError("browser OAuth account-link approval payload is invalid.")
                result = self.server.store.approve_oauth_link_request(
                    owner_id=self._ui_operator(require_csrf=True),
                    link_request_id=ui_oauth_link_approve_match.group(1),
                )
                self._json(HTTPStatus.OK, result)
                return
            ui_oauth_link_reject_match = re.fullmatch(r"/v1/ui/oauth-link-requests/([^/]+)/reject", self.path)
            if ui_oauth_link_reject_match:
                if body:
                    raise ValidationError("browser OAuth account-link rejection payload is invalid.")
                result = self.server.store.reject_oauth_link_request(
                    owner_id=self._ui_operator(require_csrf=True),
                    link_request_id=ui_oauth_link_reject_match.group(1),
                )
                self._json(HTTPStatus.OK, result)
                return
            ui_permission_request_approve_match = re.fullmatch(r"/v1/ui/permission-requests/([^/]+)/approve", self.path)
            if ui_permission_request_approve_match:
                if body:
                    raise ValidationError("browser permission request approval payload is invalid.")
                result = self.server.store.approve_mcp_permission_request(
                    owner_id=self._ui_operator(require_csrf=True),
                    permission_request_id=ui_permission_request_approve_match.group(1),
                )
                self._json(HTTPStatus.OK, result)
                return
            ui_permission_request_reject_match = re.fullmatch(r"/v1/ui/permission-requests/([^/]+)/reject", self.path)
            if ui_permission_request_reject_match:
                if body:
                    raise ValidationError("browser permission request rejection payload is invalid.")
                result = self.server.store.reject_mcp_permission_request(
                    owner_id=self._ui_operator(require_csrf=True),
                    permission_request_id=ui_permission_request_reject_match.group(1),
                )
                self._json(HTTPStatus.OK, result)
                return
            ui_oauth_principal_revoke_match = re.fullmatch(r"/v1/ui/oauth-principals/([^/]+)/revoke", self.path)
            if ui_oauth_principal_revoke_match:
                if body:
                    raise ValidationError("browser OAuth principal revocation payload is invalid.")
                result = self.server.store.revoke_oauth_principal(
                    owner_id=self._ui_operator(require_csrf=True),
                    principal_id=ui_oauth_principal_revoke_match.group(1),
                )
                self._json(HTTPStatus.OK, result)
                return
            if self.path == "/v1/maintenance/admission":
                self._operator_for_admission(mode=body.get("mode"))
                mode = self._field(body, "mode")
                result = self.server.store.set_admission_mode(mode=mode)
                self._json(HTTPStatus.OK, result)
                return
            if self.path == "/v1/ui/action-reconciliations/quarantine-historical-unknown":
                self._json(HTTPStatus.OK, self._quarantine_historical_unknown_actions(body, browser=True))
                return
            if self.path == "/v1/ui/action-dispositions/quarantine-historical-unobserved-dispatch":
                self._json(HTTPStatus.OK, self._quarantine_historical_unobserved_dispatches(body, browser=True))
                return
            if self.path == "/v1/ui/read-only-requests":
                self._json(HTTPStatus.CREATED, self._create_ui_read_only_request(body))
                return
            if self.path == "/v1/ui/bindings":
                self._json(HTTPStatus.CREATED, self._create_ui_binding(body))
                return
            if self.path == "/v1/ui/contexts":
                self._json(HTTPStatus.CREATED, self._create_ui_context(body))
                return
            ui_binding_revoke_match = re.fullmatch(r"/v1/ui/bindings/([^/]+)/revoke", self.path)
            if ui_binding_revoke_match:
                self._json(HTTPStatus.OK, self._ui_revoke_binding(ui_binding_revoke_match.group(1), body))
                return
            ui_context_close_match = re.fullmatch(r"/v1/ui/contexts/([^/]+)/close", self.path)
            if ui_context_close_match:
                self._json(HTTPStatus.OK, self._ui_close_context(ui_context_close_match.group(1), body))
                return
            if self.path == "/v1/ui/task-sessions":
                self._json(HTTPStatus.CREATED, self._create_ui_task_session(body))
                return
            ui_task_close_match = re.fullmatch(r"/v1/ui/task-sessions/([^/]+)/close", self.path)
            if ui_task_close_match:
                self._json(HTTPStatus.OK, self._ui_close_task_session(ui_task_close_match.group(1), body))
                return
            ui_patch_acceptance_match = re.fullmatch(r"/v1/ui/patch-acceptances/([^/]+)", self.path)
            if ui_patch_acceptance_match:
                self._json(HTTPStatus.OK, self._ui_record_patch_acceptance(ui_patch_acceptance_match.group(1), body))
                return
            ui_exec_stop_match = re.fullmatch(r"/v1/ui/exec-stops/([^/]+)", self.path)
            if ui_exec_stop_match:
                self._json(HTTPStatus.OK, self._ui_exec_stop(ui_exec_stop_match.group(1), body))
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
            if self.path == "/v1/action-reconciliations/quarantine-historical-unknown":
                self._json(HTTPStatus.OK, self._quarantine_historical_unknown_actions(body, browser=False))
                return
            if self.path == "/v1/action-dispositions/quarantine-historical-unobserved-dispatch":
                self._json(HTTPStatus.OK, self._quarantine_historical_unobserved_dispatches(body, browser=False))
                return
            node_rotation_prepare_match = re.fullmatch(
                r"/v1/nodes/([^/]+)/credential-rotation/prepare", self.path
            )
            if node_rotation_prepare_match:
                device_id = node_rotation_prepare_match.group(1)
                if set(body) != {"rotation_id", "current_generation", "next_credential_hash"}:
                    raise ValidationError("credential rotation prepare payload is invalid.")
                result = self.server.store.prepare_node_credential_rotation(
                    device_id=device_id,
                    node_secret=self._auth("Node"),
                    rotation_id=self._field(body, "rotation_id"),
                    current_generation=self._field(body, "current_generation"),
                    next_credential_hash=self._field(body, "next_credential_hash"),
                )
                self._json(HTTPStatus.OK, result)
                return
            node_rotation_activate_match = re.fullmatch(
                r"/v1/nodes/([^/]+)/credential-rotation/activate", self.path
            )
            if node_rotation_activate_match:
                device_id = node_rotation_activate_match.group(1)
                if set(body) != {"rotation_id"}:
                    raise ValidationError("credential rotation activate payload is invalid.")
                result = self.server.store.activate_node_credential_rotation(
                    device_id=device_id,
                    node_secret=self._auth("Node"),
                    rotation_id=self._field(body, "rotation_id"),
                )
                self._json(HTTPStatus.OK, result)
                return
            node_rotation_ack_match = re.fullmatch(
                r"/v1/nodes/([^/]+)/credential-rotation/ack", self.path
            )
            if node_rotation_ack_match:
                device_id = node_rotation_ack_match.group(1)
                if set(body) != {"rotation_id"}:
                    raise ValidationError("credential rotation acknowledgement payload is invalid.")
                result = self.server.store.acknowledge_node_credential_rotation(
                    device_id=device_id,
                    node_secret=self._auth("Node"),
                    rotation_id=self._field(body, "rotation_id"),
                )
                self._json(HTTPStatus.OK, result)
                return
            node_rotate_match = re.fullmatch(r"/v1/nodes/([^/]+)/rotate-credential", self.path)
            if node_rotate_match:
                # The former operator route generated a new secret centrally
                # and could invalidate a node before it persisted the new
                # value.  Keep the path recognizable for old clients, but
                # refuse the unsafe immediate switch; rotation is now a
                # node-mediated prepare/activate/ack protocol above.
                self._operator()
                raise ConflictError("node-mediated credential rotation is required.")
            node_revoke_match = re.fullmatch(r"/v1/nodes/([^/]+)/revoke", self.path)
            if node_revoke_match:
                result = self.server.store.revoke_node(owner_id=self._operator(), device_id=node_revoke_match.group(1))
                self._json(HTTPStatus.OK, result)
                return
            node_enrollment_status_match = re.fullmatch(r"/v1/nodes/([^/]+)/enrollment-status", self.path)
            if node_enrollment_status_match:
                # Pending requests do not have a node row yet, so this route
                # deliberately authenticates through the credential hash
                # rather than _node(), while keeping the response node-safe.
                device_id = node_enrollment_status_match.group(1)
                result = self.server.store.node_enrollment_status(
                    device_id=device_id,
                    node_secret=self._auth("Node"),
                )
                self._json(HTTPStatus.OK, result)
                return
            node_authority_status_match = re.fullmatch(r"/v1/nodes/([^/]+)/authority-status", self.path)
            if node_authority_status_match:
                # This is deliberately node-authenticated rather than an
                # operator/account inventory route.  The response is a
                # path-free projection for the Windows Settings screen and
                # never exposes owner/OAuth IDs, credentials or task data.
                if body:
                    raise ValidationError("node authority status payload is invalid.")
                device_id = node_authority_status_match.group(1)
                result = self.server.store.node_authority_status(
                    device_id=device_id,
                    node_secret=self._auth("Node"),
                )
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
            node_workspace_match = re.fullmatch(r"/v1/nodes/([^/]+)/workspace-registrations", self.path)
            if node_workspace_match:
                result = self._register_node_workspace(node_workspace_match.group(1), body)
                self._json(HTTPStatus.OK if result["replayed"] else HTTPStatus.CREATED, result)
                return
            node_workspace_retire_match = re.fullmatch(r"/v1/nodes/([^/]+)/workspace-registrations/retire", self.path)
            if node_workspace_retire_match:
                result = self._retire_node_workspace(node_workspace_retire_match.group(1), body)
                self._json(HTTPStatus.OK, result)
                return
            node_policy_template_match = re.fullmatch(r"/v1/nodes/([^/]+)/read-only-policy-template", self.path)
            if node_policy_template_match:
                self._json(
                    HTTPStatus.OK,
                    self._node_read_only_policy_template(node_policy_template_match.group(1), body),
                )
                return
            node_assigned_policy_match = re.fullmatch(r"/v1/nodes/([^/]+)/read-only-policy-assignment", self.path)
            if node_assigned_policy_match:
                self._json(
                    HTTPStatus.OK,
                    self._node_assigned_read_only_policy_template(node_assigned_policy_match.group(1), body),
                )
                return
            node_match = re.fullmatch(r"/v1/nodes/([^/]+)/poll", self.path)
            if node_match:
                device_id = node_match.group(1)
                self._node(device_id)
                if not set(body) <= {"limit", "lane"}:
                    raise ValidationError("node poll payload is invalid.")
                lane = body.get("lane")
                if lane is not None and not isinstance(lane, str):
                    raise ValidationError("node poll lane is invalid.")
                self._json(
                    HTTPStatus.OK,
                    {
                        "actions": self.server.store.poll_actions(
                            device_id=device_id,
                            limit=body.get("limit", 10),
                            lane=lane,
                        )
                    },
                )
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
            node_match = re.fullmatch(r"/v1/nodes/([^/]+)/exec-stops", self.path)
            if node_match:
                device_id = node_match.group(1)
                self._node(device_id)
                if body:
                    raise ValidationError("node exec-stop poll payload is invalid.")
                self._json(
                    HTTPStatus.OK,
                    {"stop_requests": self.server.store.list_mcp_exec_stop_requests(device_id=device_id)},
                )
                return
            node_match = re.fullmatch(r"/v1/nodes/([^/]+)/exec-stops/([^/]+)/acknowledge", self.path)
            if node_match:
                device_id, action_id = node_match.group(1), node_match.group(2)
                self._node(device_id)
                if body:
                    raise ValidationError("node exec-stop acknowledge payload is invalid.")
                result = self.server.store.acknowledge_mcp_exec_stop(action_id=action_id, device_id=device_id)
                self._json(HTTPStatus.OK, {"stop_request": result})
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


def _mcp_ingress_address_from_environment() -> tuple[str, int]:
    """Return the exact private listener address used by OpenAI Tunnel.

    The Tunnel client runs on this Ubuntu host, so an IPv4 loopback literal is
    sufficient and avoids a hostname resolving unexpectedly to a Tailnet or
    public address.  The dedicated listener is intentionally separate from
    ``CONTROL_PLANE_BIND``: that other address serves the Tailnet operator UI
    and node APIs, which must never be reachable through a Tunnel profile.
    """

    bind = str(os.environ.get("CONTROL_PLANE_MCP_BIND", "127.0.0.1")).strip()
    if bind != "127.0.0.1":
        raise ValueError("CONTROL_PLANE_MCP_BIND must be exactly 127.0.0.1.")
    try:
        port = int(os.environ.get("CONTROL_PLANE_MCP_PORT", "8766"))
    except ValueError as exc:
        raise ValueError("CONTROL_PLANE_MCP_PORT must be an integer.") from exc
    if not 1024 <= port <= 65535:
        raise ValueError("CONTROL_PLANE_MCP_PORT must be in the range 1024-65535.")
    return bind, port


def serve_from_environment() -> None:
    database = os.environ.get("CONTROL_PLANE_DB", "./var/control-plane.sqlite3")
    operator_token = os.environ.get("CONTROL_PLANE_OPERATOR_TOKEN", "")
    bind = os.environ.get("CONTROL_PLANE_BIND", "127.0.0.1")
    port = int(os.environ.get("CONTROL_PLANE_PORT", "8765"))
    mcp_bind, mcp_port = _mcp_ingress_address_from_environment()
    mcp_oauth = oauth_configuration_from_environment()
    store = ControlPlaneStore(database)
    shared = (
        store,
        operator_token,
        os.environ.get("CONTROL_PLANE_DECLARED_SOURCE_REVISION"),
        os.environ.get("CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256"),
    )
    # Bind both listeners before serving either one: a port collision must
    # fail the service start rather than leave a UI-only process looking ready.
    server = ControlPlaneHttpServer(
        (bind, port),
        *shared,
        web_origin=os.environ.get("CONTROL_PLANE_WEB_ORIGIN"),
        web_session_ttl_seconds=int(os.environ.get("CONTROL_PLANE_WEB_SESSION_TTL_SECONDS", str(DEFAULT_WEB_SESSION_TTL_SECONDS))),
        mcp_enabled=False,
        mcp_oauth=mcp_oauth,
    )
    mcp_server = ControlPlaneHttpServer(
        (mcp_bind, mcp_port),
        *shared,
        mcp_enabled=True,
        mcp_ingress_only=True,
        mcp_oauth=mcp_oauth,
    )
    mcp_thread = Thread(target=mcp_server.serve_forever, kwargs={"poll_interval": 0.5}, daemon=True)
    mcp_thread.start()
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        mcp_server.shutdown()
        mcp_server.server_close()
        mcp_thread.join(timeout=2)
        server.server_close()
