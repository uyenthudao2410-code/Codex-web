"""SQLite-backed durable intake and dispatch records.

This module intentionally does not execute a Coding Tools call.  It records a
targeted request before it is delivered and expects an authenticated node to
admit the local work under that node's existing authority boundary.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{2,127}$")
KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{7,255}$")
TERMINAL_RECEIPT_STATES = {"rejected", "completed", "failed", "unknown"}
ALLOWED_TOOL_NAMES = {
    "workspace_context",
    "agent_workflow",
    "task_control",
    "document_workflow",
    "exec_command",
    "command_control",
    "request_permissions",
    "view_image",
}


class ControlPlaneError(RuntimeError):
    """Base class for expected request failures."""

    code = "CONTROL_PLANE_ERROR"


class ValidationError(ControlPlaneError):
    code = "VALIDATION_ERROR"


class NotFoundError(ControlPlaneError):
    code = "NOT_FOUND"


class PermissionError(ControlPlaneError):
    code = "FORBIDDEN"


class ConflictError(ControlPlaneError):
    code = "CONFLICT"


def _text(value: Any, field: str, *, pattern: re.Pattern[str] = ID_PATTERN) -> str:
    text = str(value or "").strip()
    if not pattern.fullmatch(text):
        raise ValidationError(f"{field} is invalid.")
    return text


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{field} must be an object.")
    return value


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValidationError("payload must be JSON serializable.") from exc


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _now() -> int:
    return int(time.time() * 1000)


def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


class ControlPlaneStore:
    """Single-process SQLite store; all mutation methods are transactional."""

    def __init__(self, database_path: str | Path, *, clock: Any = _now) -> None:
        self.path = Path(database_path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=5.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA busy_timeout = 5000")
            yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS nodes (
                    device_id TEXT PRIMARY KEY,
                    endpoint_id TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    credential_hash TEXT NOT NULL,
                    credential_created_at_ms INTEGER NOT NULL,
                    revoked_at_ms INTEGER,
                    last_seen_at_ms INTEGER,
                    runtime_instance_id TEXT,
                    activation_epoch TEXT,
                    contract_version TEXT,
                    readiness TEXT NOT NULL DEFAULT 'unknown'
                );
                CREATE TABLE IF NOT EXISTS enrollment_requests (
                    enrollment_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL UNIQUE,
                    endpoint_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    credential_hash TEXT NOT NULL,
                    requested_at_ms INTEGER NOT NULL,
                    approved_at_ms INTEGER,
                    approved_by TEXT
                );
                CREATE TABLE IF NOT EXISTS bindings (
                    binding_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    device_id TEXT NOT NULL REFERENCES nodes(device_id),
                    endpoint_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    workspace_generation TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    created_at_ms INTEGER NOT NULL,
                    revoked_at_ms INTEGER
                );
                CREATE TABLE IF NOT EXISTS contexts (
                    context_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    binding_id TEXT NOT NULL REFERENCES bindings(binding_id),
                    device_id TEXT NOT NULL,
                    endpoint_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    workspace_generation TEXT NOT NULL,
                    created_at_ms INTEGER NOT NULL,
                    expires_at_ms INTEGER NOT NULL,
                    closed_at_ms INTEGER
                );
                CREATE TABLE IF NOT EXISTS work_requests (
                    request_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    context_id TEXT NOT NULL REFERENCES contexts(context_id),
                    objective TEXT NOT NULL,
                    criteria_json TEXT NOT NULL,
                    scope_json TEXT NOT NULL,
                    created_at_ms INTEGER NOT NULL,
                    expires_at_ms INTEGER NOT NULL,
                    canceled_at_ms INTEGER
                );
                CREATE TABLE IF NOT EXISTS actions (
                    action_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    request_id TEXT NOT NULL REFERENCES work_requests(request_id),
                    context_id TEXT NOT NULL REFERENCES contexts(context_id),
                    binding_id TEXT NOT NULL REFERENCES bindings(binding_id),
                    device_id TEXT NOT NULL,
                    endpoint_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    workspace_generation TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    arguments_json TEXT NOT NULL,
                    action_digest TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    admission_reference TEXT NOT NULL,
                    created_at_ms INTEGER NOT NULL,
                    expires_at_ms INTEGER NOT NULL,
                    delivery_state TEXT NOT NULL,
                    settled_at_ms INTEGER,
                    UNIQUE(owner_id, device_id, idempotency_key)
                );
                CREATE TABLE IF NOT EXISTS delivery_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL REFERENCES actions(action_id),
                    attempt_number INTEGER NOT NULL,
                    dispatched_at_ms INTEGER NOT NULL,
                    UNIQUE(action_id, attempt_number)
                );
                CREATE TABLE IF NOT EXISTS receipts (
                    receipt_id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL REFERENCES actions(action_id),
                    device_id TEXT NOT NULL,
                    local_handle TEXT,
                    receipt_state TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    received_at_ms INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    subject_type TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    created_at_ms INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS actions_node_delivery_idx
                    ON actions(device_id, delivery_state, expires_at_ms);
                CREATE INDEX IF NOT EXISTS receipts_action_idx ON receipts(action_id, received_at_ms);
                """
            )

    def _event(self, connection: sqlite3.Connection, subject_type: str, subject_id: str, event_type: str, details: dict[str, Any]) -> None:
        connection.execute(
            "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
            (f"evt_{uuid.uuid4().hex}", subject_type, subject_id, event_type, _canonical_json(details), self.clock()),
        )

    def _node_for_owner(self, connection: sqlite3.Connection, owner_id: str, device_id: str) -> sqlite3.Row:
        row = connection.execute("SELECT * FROM nodes WHERE device_id = ?", (device_id,)).fetchone()
        if row is None:
            raise NotFoundError("device is not enrolled.")
        if row["owner_id"] != owner_id:
            raise PermissionError("device is not owned by this principal.")
        if row["revoked_at_ms"] is not None:
            raise ConflictError("device credential is revoked.")
        return row

    def enroll_node(self, *, owner_id: str, device_id: str, endpoint_id: str, display_name: str) -> dict[str, str]:
        owner_id = _text(owner_id, "owner_id")
        device_id = _text(device_id, "device_id")
        endpoint_id = _text(endpoint_id, "endpoint_id")
        display_name = str(display_name or "").strip()
        if not 1 <= len(display_name) <= 120:
            raise ValidationError("display_name is invalid.")
        secret = secrets.token_urlsafe(32)
        secret_hash = _digest({"node_secret": secret})
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute("SELECT owner_id FROM nodes WHERE device_id = ?", (device_id,)).fetchone()
            if existing is not None:
                connection.execute("ROLLBACK")
                raise ConflictError("device is already enrolled; rotate credentials explicitly instead.")
            now = self.clock()
            connection.execute(
                "INSERT INTO nodes(device_id, endpoint_id, owner_id, display_name, credential_hash, credential_created_at_ms) VALUES (?, ?, ?, ?, ?, ?)",
                (device_id, endpoint_id, owner_id, display_name, secret_hash, now),
            )
            self._event(connection, "node", device_id, "node_enrolled", {"owner_id": owner_id, "endpoint_id": endpoint_id})
            connection.execute("COMMIT")
        return {"device_id": device_id, "node_secret": secret}

    def request_enrollment(self, *, device_id: str, endpoint_id: str, display_name: str, credential_hash: str) -> dict[str, Any]:
        """Store a node-generated credential hash pending operator approval."""
        device_id = _text(device_id, "device_id")
        endpoint_id = _text(endpoint_id, "endpoint_id")
        display_name = str(display_name or "").strip()
        credential_hash = str(credential_hash or "").strip().lower()
        if not 1 <= len(display_name) <= 120:
            raise ValidationError("display_name is invalid.")
        if not re.fullmatch(r"[0-9a-f]{64}", credential_hash):
            raise ValidationError("credential_hash is invalid.")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute("SELECT 1 FROM nodes WHERE device_id = ?", (device_id,)).fetchone() is not None:
                connection.execute("ROLLBACK")
                raise ConflictError("device is already enrolled.")
            existing = connection.execute("SELECT * FROM enrollment_requests WHERE device_id = ?", (device_id,)).fetchone()
            if existing is not None:
                if existing["credential_hash"] != credential_hash or existing["endpoint_id"] != endpoint_id:
                    connection.execute("ROLLBACK")
                    raise ConflictError("a different enrollment request already exists for this device.")
                connection.execute("COMMIT")
                return _row(existing) or {}
            enrollment_id = f"enroll_{uuid.uuid4().hex}"
            now = self.clock()
            connection.execute(
                "INSERT INTO enrollment_requests VALUES (?, ?, ?, ?, ?, ?, NULL, NULL)",
                (enrollment_id, device_id, endpoint_id, display_name, credential_hash, now),
            )
            self._event(connection, "enrollment", enrollment_id, "enrollment_requested", {"device_id": device_id, "endpoint_id": endpoint_id})
            connection.execute("COMMIT")
        return self.enrollment_request(enrollment_id=enrollment_id)

    def enrollment_request(self, *, enrollment_id: str) -> dict[str, Any]:
        enrollment_id = _text(enrollment_id, "enrollment_id")
        with self._connection() as connection:
            row = connection.execute("SELECT enrollment_id, device_id, endpoint_id, display_name, requested_at_ms, approved_at_ms, approved_by FROM enrollment_requests WHERE enrollment_id = ?", (enrollment_id,)).fetchone()
        if row is None:
            raise NotFoundError("enrollment request does not exist.")
        return _row(row) or {}

    def list_enrollment_requests(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT enrollment_id, device_id, endpoint_id, display_name, requested_at_ms, approved_at_ms, approved_by FROM enrollment_requests ORDER BY requested_at_ms"
            ).fetchall()
        return [dict(row) for row in rows]

    def approve_enrollment(self, *, owner_id: str, enrollment_id: str) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        enrollment_id = _text(enrollment_id, "enrollment_id")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            request = connection.execute("SELECT * FROM enrollment_requests WHERE enrollment_id = ?", (enrollment_id,)).fetchone()
            if request is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("enrollment request does not exist.")
            if request["approved_at_ms"] is not None:
                connection.execute("ROLLBACK")
                raise ConflictError("enrollment request is already approved.")
            if connection.execute("SELECT 1 FROM nodes WHERE device_id = ?", (request["device_id"],)).fetchone() is not None:
                connection.execute("ROLLBACK")
                raise ConflictError("device is already enrolled.")
            now = self.clock()
            connection.execute(
                "INSERT INTO nodes(device_id, endpoint_id, owner_id, display_name, credential_hash, credential_created_at_ms) VALUES (?, ?, ?, ?, ?, ?)",
                (request["device_id"], request["endpoint_id"], owner_id, request["display_name"], request["credential_hash"], now),
            )
            connection.execute("UPDATE enrollment_requests SET approved_at_ms = ?, approved_by = ? WHERE enrollment_id = ?", (now, owner_id, enrollment_id))
            self._event(connection, "node", request["device_id"], "node_enrollment_approved", {"enrollment_id": enrollment_id, "owner_id": owner_id})
            connection.execute("COMMIT")
        return self.node(device_id=request["device_id"])

    def authenticate_node(self, *, device_id: str, node_secret: str) -> dict[str, Any]:
        device_id = _text(device_id, "device_id")
        provided_hash = _digest({"node_secret": str(node_secret or "")})
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM nodes WHERE device_id = ?", (device_id,)).fetchone()
        if row is None or row["revoked_at_ms"] is not None or not hmac.compare_digest(row["credential_hash"], provided_hash):
            raise PermissionError("node authentication failed.")
        return _row(row) or {}

    def heartbeat(self, *, device_id: str, endpoint_id: str, runtime_instance_id: str, activation_epoch: str, contract_version: str, readiness: str) -> dict[str, Any]:
        device_id = _text(device_id, "device_id")
        endpoint_id = _text(endpoint_id, "endpoint_id")
        readiness = str(readiness or "unknown").strip().lower()
        if readiness not in {"ready", "degraded", "blocked", "unknown"}:
            raise ValidationError("readiness is invalid.")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT endpoint_id FROM nodes WHERE device_id = ?", (device_id,)).fetchone()
            if row is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("device is not enrolled.")
            if row["endpoint_id"] != endpoint_id:
                connection.execute("ROLLBACK")
                raise ConflictError("endpoint identity does not match enrollment.")
            now = self.clock()
            connection.execute(
                "UPDATE nodes SET last_seen_at_ms = ?, runtime_instance_id = ?, activation_epoch = ?, contract_version = ?, readiness = ? WHERE device_id = ?",
                (now, str(runtime_instance_id or "")[:128], str(activation_epoch or "")[:128], str(contract_version or "")[:128], readiness, device_id),
            )
            self._event(connection, "node", device_id, "node_heartbeat", {"readiness": readiness})
            connection.execute("COMMIT")
        return self.node(device_id=device_id)

    def node(self, *, device_id: str) -> dict[str, Any]:
        device_id = _text(device_id, "device_id")
        with self._connection() as connection:
            row = connection.execute(
                "SELECT device_id, endpoint_id, owner_id, display_name, revoked_at_ms, last_seen_at_ms, runtime_instance_id, activation_epoch, contract_version, readiness FROM nodes WHERE device_id = ?",
                (device_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError("device is not enrolled.")
        return _row(row) or {}

    def create_binding(self, *, owner_id: str, device_id: str, workspace_id: str, workspace_generation: str, display_name: str) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        device_id = _text(device_id, "device_id")
        workspace_id = _text(workspace_id, "workspace_id")
        workspace_generation = _text(workspace_generation, "workspace_generation")
        display_name = str(display_name or "").strip()
        if not 1 <= len(display_name) <= 120:
            raise ValidationError("display_name is invalid.")
        binding_id = f"bind_{uuid.uuid4().hex}"
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            node = self._node_for_owner(connection, owner_id, device_id)
            connection.execute(
                "INSERT INTO bindings VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                (binding_id, owner_id, device_id, node["endpoint_id"], workspace_id, workspace_generation, display_name, self.clock()),
            )
            self._event(connection, "binding", binding_id, "binding_created", {"device_id": device_id, "workspace_id": workspace_id})
            connection.execute("COMMIT")
        return self.binding(owner_id=owner_id, binding_id=binding_id)

    def binding(self, *, owner_id: str, binding_id: str) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        binding_id = _text(binding_id, "binding_id")
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM bindings WHERE binding_id = ?", (binding_id,)).fetchone()
        if row is None:
            raise NotFoundError("binding does not exist.")
        if row["owner_id"] != owner_id:
            raise PermissionError("binding is not owned by this principal.")
        if row["revoked_at_ms"] is not None:
            raise ConflictError("binding is revoked.")
        return _row(row) or {}

    def list_bindings(self, *, owner_id: str) -> list[dict[str, Any]]:
        owner_id = _text(owner_id, "owner_id")
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT b.*, n.last_seen_at_ms, n.readiness, n.contract_version FROM bindings b JOIN nodes n ON n.device_id = b.device_id WHERE b.owner_id = ? AND b.revoked_at_ms IS NULL ORDER BY b.created_at_ms",
                (owner_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_context(self, *, owner_id: str, binding_id: str, expires_at_ms: int) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        binding = self.binding(owner_id=owner_id, binding_id=binding_id)
        now = self.clock()
        expires_at_ms = int(expires_at_ms)
        if expires_at_ms <= now:
            raise ValidationError("context expiry must be in the future.")
        context_id = f"ctx_{uuid.uuid4().hex}"
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO contexts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                (context_id, owner_id, binding["binding_id"], binding["device_id"], binding["endpoint_id"], binding["workspace_id"], binding["workspace_generation"], now, expires_at_ms),
            )
            self._event(connection, "context", context_id, "context_created", {"binding_id": binding["binding_id"]})
            connection.execute("COMMIT")
        return self.context(owner_id=owner_id, context_id=context_id)

    def context(self, *, owner_id: str, context_id: str, require_live: bool = False) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        context_id = _text(context_id, "context_id")
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM contexts WHERE context_id = ?", (context_id,)).fetchone()
        if row is None:
            raise NotFoundError("context does not exist.")
        if row["owner_id"] != owner_id:
            raise PermissionError("context is not owned by this principal.")
        if require_live and (row["closed_at_ms"] is not None or row["expires_at_ms"] <= self.clock()):
            raise ConflictError("context is not live.")
        return _row(row) or {}

    def create_work_request(self, *, owner_id: str, context_id: str, objective: str, criteria: dict[str, Any], scope: dict[str, Any], expires_at_ms: int) -> dict[str, Any]:
        context = self.context(owner_id=owner_id, context_id=context_id, require_live=True)
        objective = str(objective or "").strip()
        if not 1 <= len(objective) <= 4000:
            raise ValidationError("objective is invalid.")
        criteria = _object(criteria, "criteria")
        scope = _object(scope, "scope")
        expires_at_ms = int(expires_at_ms)
        now = self.clock()
        if expires_at_ms <= now or expires_at_ms > context["expires_at_ms"]:
            raise ValidationError("work request expiry is invalid.")
        request_id = f"req_{uuid.uuid4().hex}"
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO work_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                (request_id, owner_id, context["context_id"], objective, _canonical_json(criteria), _canonical_json(scope), now, expires_at_ms),
            )
            self._event(connection, "work_request", request_id, "work_request_created", {"context_id": context["context_id"]})
            connection.execute("COMMIT")
        return self.work_request(owner_id=owner_id, request_id=request_id)

    def work_request(self, *, owner_id: str, request_id: str) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        request_id = _text(request_id, "request_id")
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM work_requests WHERE request_id = ?", (request_id,)).fetchone()
        if row is None:
            raise NotFoundError("work request does not exist.")
        if row["owner_id"] != owner_id:
            raise PermissionError("work request is not owned by this principal.")
        return _row(row) or {}

    def seal_action(self, *, owner_id: str, request_id: str, tool_name: str, arguments: dict[str, Any], idempotency_key: str, admission_reference: str, expires_at_ms: int) -> dict[str, Any]:
        request = self.work_request(owner_id=owner_id, request_id=request_id)
        now = self.clock()
        if request["canceled_at_ms"] is not None or request["expires_at_ms"] <= now:
            raise ConflictError("work request is not dispatchable.")
        context = self.context(owner_id=owner_id, context_id=request["context_id"], require_live=True)
        tool_name = _text(tool_name, "tool_name")
        if tool_name not in ALLOWED_TOOL_NAMES:
            raise ValidationError("tool_name is not in the smart-v3 surface.")
        arguments = _object(arguments, "arguments")
        idempotency_key = _text(idempotency_key, "idempotency_key", pattern=KEY_PATTERN)
        admission_reference = _text(admission_reference, "admission_reference")
        expires_at_ms = int(expires_at_ms)
        if expires_at_ms <= now or expires_at_ms > request["expires_at_ms"]:
            raise ValidationError("action expiry is invalid.")
        immutable = {
            "request_id": request_id,
            "context_id": context["context_id"],
            "binding_id": context["binding_id"],
            "device_id": context["device_id"],
            "endpoint_id": context["endpoint_id"],
            "workspace_id": context["workspace_id"],
            "workspace_generation": context["workspace_generation"],
            "tool_name": tool_name,
            "arguments": arguments,
            "idempotency_key": idempotency_key,
            "admission_reference": admission_reference,
            "expires_at_ms": expires_at_ms,
        }
        digest = _digest(immutable)
        action_id = f"act_{uuid.uuid4().hex}"
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM actions WHERE owner_id = ? AND device_id = ? AND idempotency_key = ?",
                (owner_id, context["device_id"], idempotency_key),
            ).fetchone()
            if existing is not None:
                if existing["action_digest"] != digest:
                    connection.execute("ROLLBACK")
                    raise ConflictError("idempotency key is already bound to a different action.")
                connection.execute("COMMIT")
                return _row(existing) or {}
            connection.execute(
                "INSERT INTO actions(action_id, owner_id, request_id, context_id, binding_id, device_id, endpoint_id, workspace_id, workspace_generation, tool_name, arguments_json, action_digest, idempotency_key, admission_reference, created_at_ms, expires_at_ms, delivery_state, settled_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                (action_id, owner_id, request_id, context["context_id"], context["binding_id"], context["device_id"], context["endpoint_id"], context["workspace_id"], context["workspace_generation"], tool_name, _canonical_json(arguments), digest, idempotency_key, admission_reference, now, expires_at_ms, "queued"),
            )
            self._event(connection, "action", action_id, "action_sealed", {"request_id": request_id, "digest": digest})
            connection.execute("COMMIT")
        return self.action(owner_id=owner_id, action_id=action_id)

    def action(self, *, owner_id: str, action_id: str) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        action_id = _text(action_id, "action_id")
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM actions WHERE action_id = ?", (action_id,)).fetchone()
        if row is None:
            raise NotFoundError("action does not exist.")
        if row["owner_id"] != owner_id:
            raise PermissionError("action is not owned by this principal.")
        return _row(row) or {}

    def poll_actions(self, *, device_id: str, limit: int = 10) -> list[dict[str, Any]]:
        device_id = _text(device_id, "device_id")
        limit = max(1, min(int(limit), 50))
        now = self.clock()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                "SELECT * FROM actions WHERE device_id = ? AND delivery_state IN ('queued', 'dispatch_unconfirmed') AND expires_at_ms > ? ORDER BY created_at_ms LIMIT ?",
                (device_id, now, limit),
            ).fetchall()
            result: list[dict[str, Any]] = []
            for row in rows:
                attempts = connection.execute("SELECT COUNT(*) FROM delivery_attempts WHERE action_id = ?", (row["action_id"],)).fetchone()[0]
                connection.execute("UPDATE actions SET delivery_state = 'dispatch_unconfirmed' WHERE action_id = ?", (row["action_id"],))
                connection.execute(
                    "INSERT INTO delivery_attempts VALUES (?, ?, ?, ?)",
                    (f"try_{uuid.uuid4().hex}", row["action_id"], attempts + 1, now),
                )
                self._event(connection, "action", row["action_id"], "action_delivery_attempted", {"attempt": attempts + 1})
                payload = _row(row) or {}
                payload["delivery_state"] = "dispatch_unconfirmed"
                result.append(payload)
            connection.execute("COMMIT")
        return result

    def record_receipt(self, *, device_id: str, action_id: str, receipt_state: str, local_handle: str, payload: dict[str, Any]) -> dict[str, Any]:
        device_id = _text(device_id, "device_id")
        action_id = _text(action_id, "action_id")
        receipt_state = str(receipt_state or "").strip().lower()
        if receipt_state not in {"accepted", *TERMINAL_RECEIPT_STATES}:
            raise ValidationError("receipt_state is invalid.")
        payload = _object(payload, "payload")
        local_handle = str(local_handle or "").strip()[:256]
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            action = connection.execute("SELECT * FROM actions WHERE action_id = ?", (action_id,)).fetchone()
            if action is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("action does not exist.")
            if action["device_id"] != device_id:
                connection.execute("ROLLBACK")
                raise PermissionError("action belongs to another device.")
            if action["delivery_state"] == "queued":
                connection.execute("ROLLBACK")
                raise ConflictError("action has not been delivered to this node.")
            if action["delivery_state"] == "settled":
                connection.execute("ROLLBACK")
                raise ConflictError("action is already settled.")
            receipt_id = f"rcpt_{uuid.uuid4().hex}"
            now = self.clock()
            connection.execute(
                "INSERT INTO receipts VALUES (?, ?, ?, ?, ?, ?, ?)",
                (receipt_id, action_id, device_id, local_handle, receipt_state, _canonical_json(payload), now),
            )
            delivery_state = "settled" if receipt_state in TERMINAL_RECEIPT_STATES else "accepted"
            settled_at = now if delivery_state == "settled" else None
            connection.execute("UPDATE actions SET delivery_state = ?, settled_at_ms = ? WHERE action_id = ?", (delivery_state, settled_at, action_id))
            self._event(connection, "action", action_id, "action_receipt_recorded", {"receipt_state": receipt_state, "delivery_state": delivery_state})
            connection.execute("COMMIT")
        return {"receipt_id": receipt_id, "action_id": action_id, "delivery_state": delivery_state}

    def health(self) -> dict[str, Any]:
        with self._connection() as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            counts = {
                name: connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                for name in ("nodes", "enrollment_requests", "bindings", "contexts", "work_requests", "actions", "receipts")
            }
        return {"ok": integrity == "ok", "sqlite_integrity": integrity, "counts": counts}
