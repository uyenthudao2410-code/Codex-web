"""Small authenticated HTTP surface for the standalone control plane."""

from __future__ import annotations

import json
import os
import re
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .store import ControlPlaneError, ControlPlaneStore, PermissionError, ValidationError


MAX_BODY_BYTES = 128 * 1024
AUTH_PATTERN = re.compile(r"^(Bearer|Node) ([A-Za-z0-9_-]{16,512})$")


class ControlPlaneHttpServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], store: ControlPlaneStore, operator_token: str) -> None:
        if len(operator_token) < 32:
            raise ValueError("CONTROL_PLANE_OPERATOR_TOKEN must have at least 32 characters.")
        self.store = store
        self.operator_token = operator_token
        self.started_at_ms = int(time.time() * 1000)
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
                payload.update({"service": "coding-tools-control-plane", "started_at_ms": self.server.started_at_ms})
                self._json(HTTPStatus.OK if payload["ok"] else HTTPStatus.SERVICE_UNAVAILABLE, payload)
                return
            if self.path == "/v1/bindings":
                self._json(HTTPStatus.OK, {"bindings": self.server.store.list_bindings(owner_id=self._operator())})
                return
            if self.path == "/v1/enrollment-requests":
                self._operator()
                self._json(HTTPStatus.OK, {"enrollment_requests": self.server.store.list_enrollment_requests()})
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": {"code": "NOT_FOUND", "message": "route does not exist."}})
        except ControlPlaneError as error:
            self._error(error)

    def do_POST(self) -> None:  # noqa: N802
        try:
            body = self._body()
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
            if self.path == "/v1/contexts":
                result = self.server.store.create_context(
                    owner_id=self._operator(),
                    binding_id=self._field(body, "binding_id"),
                    expires_at_ms=self._field(body, "expires_at_ms"),
                )
                self._json(HTTPStatus.CREATED, result)
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
            node_match = re.fullmatch(r"/v1/nodes/([^/]+)/heartbeat", self.path)
            if node_match:
                device_id = node_match.group(1)
                self._node(device_id)
                result = self.server.store.heartbeat(
                    device_id=device_id,
                    endpoint_id=self._field(body, "endpoint_id"),
                    runtime_instance_id=body.get("runtime_instance_id", ""),
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
                    receipt_state=self._field(body, "receipt_state"),
                    local_handle=body.get("local_handle", ""),
                    payload=body.get("payload", {}),
                )
                self._json(HTTPStatus.CREATED, result)
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": {"code": "NOT_FOUND", "message": "route does not exist."}})
        except ControlPlaneError as error:
            self._error(error)
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
    server = ControlPlaneHttpServer((bind, port), ControlPlaneStore(database), operator_token)
    server.serve_forever(poll_interval=0.5)
