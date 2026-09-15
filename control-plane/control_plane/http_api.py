"""Small authenticated HTTP surface for the standalone control plane."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import time
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .mcp_facade import ControlPlaneMcpFacade
from .store import ControlPlaneError, ControlPlaneStore, PermissionError, ValidationError


MAX_BODY_BYTES = 128 * 1024
AUTH_PATTERN = re.compile(r"^(Bearer|Node) ([A-Za-z0-9_-]{16,512})$")
SOURCE_REVISION_PATTERN = re.compile(r"^[0-9a-f]{40,64}$")
SOURCE_FINGERPRINT_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


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
        super().__init__(address, ControlPlaneHandler)


class ControlPlaneHandler(BaseHTTPRequestHandler):
    server: ControlPlaneHttpServer
    protocol_version = "HTTP/1.1"

    def log_message(self, _format: str, *_args: Any) -> None:
        # HTTP auth and payloads must never be written to stderr/service logs.
        return

    def _json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
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
        if not __import__("hmac").compare_digest(token, self.server.operator_token):
            raise PermissionError("operator authentication failed.")
        return "owner_default"

    def _node(self, device_id: str) -> None:
        self.server.store.authenticate_node(device_id=device_id, node_secret=self._auth("Node"))

    @staticmethod
    def _field(body: dict[str, Any], name: str) -> Any:
        if name not in body:
            raise ValidationError(f"{name} is required.")
        return body[name]

    def do_GET(self) -> None:  # noqa: N802
        try:
            if self.path == "/healthz":
                payload = self.server.store.health()
                payload.update(
                    {
                        "service": "coding-tools-control-plane",
                        "service_instance_id": self.server.service_instance_id,
                        "package_source_sha256": self.server.package_source_sha256,
                        "expected_package_source_sha256": self.server.expected_package_source_sha256,
                        "started_at_ms": self.server.started_at_ms,
                        # This is deployment-supplied metadata, not an
                        # attestation of the bytes loaded by Python. Operators
                        # still need an exact service/unit/check-out proof.
                        "declared_source_revision": self.server.declared_source_revision,
                    }
                )
                self._json(HTTPStatus.OK if payload["ok"] else HTTPStatus.SERVICE_UNAVAILABLE, payload)
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
            if self.path == "/v1/maintenance/admission":
                self._operator()
                result = self.server.store.set_admission_mode(mode=self._field(body, "mode"))
                self._json(HTTPStatus.OK, result)
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
    )
    server.serve_forever(poll_interval=0.5)
