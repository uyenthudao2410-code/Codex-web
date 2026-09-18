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
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
SCHEMA_VERSION = 10
MAX_HEARTBEAT_AGE_MS = 60_000
MCP_READ_ONLY_WORKSPACE_CONTEXT_ARGUMENTS = {"detail": "compact", "max_entries": 1}
TERMINAL_RECEIPT_STATES = {"rejected", "completed", "failed"}
RECONCILIATION_RECEIPT_STATES = {"unknown"}
QUARANTINE_UNKNOWN_DISPOSITION = "quarantined_unknown"
QUARANTINE_UNKNOWN_DECLARATION = "HISTORICAL_READ_ONLY_UNKNOWN_EFFECT"
UNVERIFIED_RUNTIME_IDENTITIES = {"", "none", "unknown", "unreported", "unverified"}
POLICY_OBSERVATION_STATES = {"unobserved", "enabled", "expired_or_disabled", "unavailable"}
POLICY_REASON_PATTERN = re.compile(r"^[A-Z0-9_]{3,96}$")
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


def _mcp_access_token_digest(value: str) -> str:
    """Hash a root-MCP bearer without reusing the node-secret namespace.

    The raw bearer is returned exactly once when an operator creates a grant.
    The durable store and every observation surface retain only this
    domain-separated digest.
    """

    return hashlib.sha256(
        b"coding-tools-control-plane:mcp-access-grant:v1\0" + str(value or "").encode("utf-8")
    ).hexdigest()


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


def _facade_contract(value: Any) -> dict[str, int | str]:
    """Validate portable façade metadata without claiming it is local authority.

    The central façade is responsible for comparing these fields to the
    contract it is serving.  The store only makes a validated snapshot durable
    in the exact read-only intent/action lineage, so a later node policy can
    reject a changed façade contract without inferring a local MCP contract.
    """

    if not isinstance(value, dict) or set(value) != {"schema_version", "profile", "sha256"}:
        raise ValidationError("facade_contract is invalid.")
    schema_version = value.get("schema_version")
    if not isinstance(schema_version, int) or isinstance(schema_version, bool) or not 1 <= schema_version <= 1_000_000:
        raise ValidationError("facade_contract schema_version is invalid.")
    profile = _text(value.get("profile"), "facade_contract profile")
    sha256 = str(value.get("sha256") or "").strip().lower()
    if SHA256_PATTERN.fullmatch(sha256) is None:
        raise ValidationError("facade_contract sha256 is invalid.")
    return {"schema_version": schema_version, "profile": profile, "sha256": sha256}


def _now() -> int:
    return int(time.time() * 1000)


def _reported_runtime_identity(value: Any) -> bool:
    return str(value or "").strip().lower() not in UNVERIFIED_RUNTIME_IDENTITIES


def _node_policy_observation(value: Any) -> dict[str, Any] | None:
    """Validate a compact, credential-free local policy observation.

    This is intentionally node-reported telemetry, never central execution
    authority.  The central service stores enough to show why the fixed
    read-only lane is unavailable without receiving a local policy file,
    workspace path, credential, or arbitrary diagnostic text.
    """

    if value is None:
        # Older nodes may still heartbeat.  Preserve their last observation
        # rather than rewriting it to a misleading synthetic state.
        return None
    if not isinstance(value, dict) or set(value) != {"state", "expires_at_ms", "policy_sha256", "reason"}:
        raise ValidationError("policy_observation is invalid.")
    state = str(value.get("state") or "").strip().lower()
    if state not in POLICY_OBSERVATION_STATES - {"unobserved"}:
        raise ValidationError("policy_observation state is invalid.")
    expires_at_ms = value.get("expires_at_ms")
    policy_sha256 = value.get("policy_sha256")
    reason = str(value.get("reason") or "").strip()
    if state in {"enabled", "expired_or_disabled"}:
        if not isinstance(expires_at_ms, int) or isinstance(expires_at_ms, bool) or expires_at_ms <= 0:
            raise ValidationError("policy_observation expiry is invalid.")
        if not isinstance(policy_sha256, str) or SHA256_PATTERN.fullmatch(policy_sha256.strip().lower()) is None:
            raise ValidationError("policy_observation digest is invalid.")
        if reason:
            raise ValidationError("policy_observation reason is invalid.")
        return {
            "state": state,
            "expires_at_ms": expires_at_ms,
            "policy_sha256": policy_sha256.strip().lower(),
            "reason": None,
        }
    if expires_at_ms is not None or policy_sha256 is not None or POLICY_REASON_PATTERN.fullmatch(reason) is None:
        raise ValidationError("policy_observation unavailable state is invalid.")
    return {"state": state, "expires_at_ms": None, "policy_sha256": None, "reason": reason}


def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_verified_snapshot(snapshot_path: str | Path, *, expected_sha256: str | None = None) -> dict[str, Any]:
    """Read one completed snapshot without initializing, migrating, or restoring it.

    A live WAL-mode database must first be copied through
    :func:`create_verified_backup`: hashing its main file alone would not bind
    the current logical WAL state. A completed snapshot has no sidecars, so the
    returned SHA-256 identifies the artifact the operator is about to use in a
    separately approved restore/reconciliation procedure.
    """
    snapshot_path = Path(snapshot_path).expanduser().resolve()
    if not snapshot_path.is_file():
        raise NotFoundError("snapshot database does not exist.")
    if Path(f"{snapshot_path}-wal").exists() or Path(f"{snapshot_path}-shm").exists():
        raise ConflictError("snapshot has SQLite WAL sidecars; create a verified snapshot before inspection.")
    expected = str(expected_sha256 or "").strip().lower()
    if expected and not SHA256_PATTERN.fullmatch(expected):
        raise ValidationError("expected snapshot SHA-256 is invalid.")
    snapshot_sha256 = _file_sha256(snapshot_path)
    if expected and not hmac.compare_digest(expected, snapshot_sha256):
        raise ConflictError("snapshot SHA-256 does not match the expected artifact.")
    # ``immutable=1`` prevents SQLite from creating shared-memory sidecars for
    # a completed artifact. It is safe only because this command rejects WAL
    # sidecars and is deliberately not an inspector for a live database.
    source_uri = f"{snapshot_path.as_uri()}?mode=ro&immutable=1"
    connection = sqlite3.connect(source_uri, uri=True, timeout=5.0, isolation_level=None)
    try:
        connection.row_factory = sqlite3.Row
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        if integrity != "ok":
            raise RuntimeError("snapshot integrity verification failed.")
        schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        tables = {
            str(row["name"])
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
        delivery_state_counts: dict[str, int] = {}
        quarantined_unknown_action_count = 0
        if "actions" in tables:
            delivery_state_counts = {
                str(row["delivery_state"]): int(row["count"])
                for row in connection.execute(
                    "SELECT delivery_state, COUNT(*) AS count FROM actions GROUP BY delivery_state ORDER BY delivery_state"
                ).fetchall()
            }
            if "action_reconciliations" in tables:
                quarantined_unknown_action_count = int(
                    connection.execute(
                        """
                        SELECT COUNT(*)
                        FROM actions AS action
                        JOIN action_reconciliations AS reconciliation
                          ON reconciliation.action_id = action.action_id
                        WHERE action.delivery_state = 'reconcile_required'
                          AND reconciliation.disposition = ?
                        """,
                        (QUARANTINE_UNKNOWN_DISPOSITION,),
                    ).fetchone()[0]
                )
        admission_mode: str | None = None
        if "control_plane_state" in tables:
            row = connection.execute(
                "SELECT state_value FROM control_plane_state WHERE state_key = 'admission_mode'"
            ).fetchone()
            admission_mode = str(row["state_value"]) if row is not None else None
    finally:
        connection.close()
    unresolved_action_count = sum(
        delivery_state_counts.get(state, 0)
        for state in ("dispatch_unconfirmed", "accepted", "reconcile_required")
    )
    unquarantined_unresolved_action_count = unresolved_action_count - quarantined_unknown_action_count
    return {
        "sqlite_integrity": integrity,
        "schema_version": schema_version,
        "snapshot_sha256": snapshot_sha256,
        "admission_mode": admission_mode,
        "delivery_state_counts": delivery_state_counts,
        "unresolved_action_count": unresolved_action_count,
        "quarantined_unknown_action_count": quarantined_unknown_action_count,
        "unquarantined_unresolved_action_count": unquarantined_unresolved_action_count,
    }


def create_verified_backup(source_path: str | Path, destination_path: str | Path) -> dict[str, int | str]:
    """Snapshot an existing SQLite database without initializing or migrating it.

    This is deliberately a module-level operation rather than a ``Store``
    constructor call: an operator may need a snapshot *before* allowing new
    source to initialize or migrate a production database.  The source is
    opened with SQLite's read-only URI mode, while the destination is a new,
    verified, non-overwriting file.
    """
    source_path = Path(source_path).expanduser().resolve()
    destination = Path(destination_path).expanduser().resolve()
    if not source_path.is_file():
        raise NotFoundError("backup source database does not exist.")
    if destination == source_path:
        raise ValidationError("backup destination must differ from the source database.")
    if destination.exists():
        raise ConflictError("backup destination already exists.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.partial")
    try:
        source_uri = f"{source_path.as_uri()}?mode=ro"
        source = sqlite3.connect(source_uri, uri=True, timeout=5.0, isolation_level=None)
        try:
            source.execute("PRAGMA busy_timeout = 5000")
            snapshot = sqlite3.connect(staging, timeout=5.0, isolation_level=None)
            try:
                source.backup(snapshot)
                integrity = str(snapshot.execute("PRAGMA integrity_check").fetchone()[0])
                source_version = int(source.execute("PRAGMA user_version").fetchone()[0])
                snapshot_version = int(snapshot.execute("PRAGMA user_version").fetchone()[0])
                if integrity != "ok" or snapshot_version != source_version:
                    raise RuntimeError("SQLite Backup API snapshot verification failed.")
            finally:
                snapshot.close()
        finally:
            source.close()
        # Bind the operator receipt to the immutable staged bytes before the
        # destination becomes visible. This is an artifact fingerprint, not a
        # proof of source deployment identity or restore acceptance.
        snapshot_sha256 = _file_sha256(staging)
        staging.replace(destination)
    except Exception:
        for artifact in (
            staging,
            Path(f"{staging}-journal"),
            Path(f"{staging}-shm"),
            Path(f"{staging}-wal"),
        ):
            try:
                artifact.unlink(missing_ok=True)
            except OSError:
                pass
        raise
    return {
        "sqlite_integrity": integrity,
        "schema_version": snapshot_version,
        "bytes": destination.stat().st_size,
        "snapshot_sha256": snapshot_sha256,
    }


def create_recovery_restore_candidate(
    source_path: str | Path,
    destination_path: str | Path,
    *,
    expected_sha256: str | None = None,
) -> dict[str, int | str]:
    """Create a new, durable-recovery SQLite restore candidate from a snapshot.

    This deliberately does not replace a live database, stop/start a service,
    change a production admission state, or contact a node.  Its one purpose is
    to prevent an older snapshot's potentially ``open`` admission mode from
    becoming an unreviewed dispatch state when an operator prepares a separate
    restore artifact.  A production service switch still requires the approved
    recovery/reconciliation procedure and explicit authority.
    """

    source = Path(source_path).expanduser().resolve()
    destination = Path(destination_path).expanduser().resolve()
    inspected_source = inspect_verified_snapshot(source, expected_sha256=expected_sha256)
    if int(inspected_source["schema_version"]) != SCHEMA_VERSION:
        raise ConflictError("restore candidate requires an exact current control-plane schema snapshot.")
    if inspected_source["admission_mode"] not in {"open", "recovery"}:
        raise ConflictError("restore candidate source has no valid durable admission mode.")
    if destination == source:
        raise ValidationError("restore candidate destination must differ from the source snapshot.")
    if destination.exists():
        raise ConflictError("restore candidate destination already exists.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.partial")
    try:
        source_uri = f"{source.as_uri()}?mode=ro&immutable=1"
        read_only_source = sqlite3.connect(source_uri, uri=True, timeout=5.0, isolation_level=None)
        try:
            candidate = sqlite3.connect(staging, timeout=5.0, isolation_level=None)
            try:
                read_only_source.backup(candidate)
            finally:
                candidate.close()
        finally:
            read_only_source.close()

        candidate = sqlite3.connect(staging, timeout=5.0, isolation_level=None)
        try:
            # Keep the candidate self-contained rather than creating WAL/SHM
            # siblings which inspection intentionally rejects.
            candidate.execute("PRAGMA journal_mode = DELETE")
            candidate.execute("PRAGMA foreign_keys = ON")
            candidate.execute("BEGIN IMMEDIATE")
            admission = candidate.execute(
                "SELECT state_value FROM control_plane_state WHERE state_key = 'admission_mode'"
            ).fetchone()
            if admission is None or str(admission[0]) not in {"open", "recovery"}:
                candidate.execute("ROLLBACK")
                raise ConflictError("restore candidate source has no valid durable admission mode.")
            changed_at_ms = int(time.time() * 1000)
            candidate.execute(
                "UPDATE control_plane_state SET state_value = 'recovery', changed_at_ms = ? WHERE state_key = 'admission_mode'",
                (changed_at_ms,),
            )
            candidate.execute(
                "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
                (
                    f"evt_{uuid.uuid4().hex}",
                    "control_plane",
                    "admission",
                    "recovery_restore_candidate_prepared",
                    _canonical_json({"source_snapshot_sha256": inspected_source["snapshot_sha256"]}),
                    changed_at_ms,
                ),
            )
            candidate.execute("COMMIT")
            integrity = str(candidate.execute("PRAGMA integrity_check").fetchone()[0])
            schema_version = int(candidate.execute("PRAGMA user_version").fetchone()[0])
            if integrity != "ok" or schema_version != SCHEMA_VERSION:
                raise RuntimeError("recovery restore candidate verification failed.")
        finally:
            candidate.close()

        candidate_sha256 = _file_sha256(staging)
        inspected_candidate = inspect_verified_snapshot(staging, expected_sha256=candidate_sha256)
        if inspected_candidate["admission_mode"] != "recovery":
            raise RuntimeError("recovery restore candidate did not retain the admission lock.")
        staging.replace(destination)
    except Exception:
        for artifact in (
            staging,
            Path(f"{staging}-journal"),
            Path(f"{staging}-shm"),
            Path(f"{staging}-wal"),
        ):
            try:
                artifact.unlink(missing_ok=True)
            except OSError:
                pass
        raise
    return {
        "sqlite_integrity": integrity,
        "schema_version": schema_version,
        "source_snapshot_sha256": str(inspected_source["snapshot_sha256"]),
        "candidate_sha256": candidate_sha256,
        "admission_mode": "recovery",
        "bytes": destination.stat().st_size,
    }


class ControlPlaneStore:
    """Single-process SQLite store; all mutation methods are transactional."""

    def __init__(
        self,
        database_path: str | Path,
        *,
        clock: Any = _now,
        heartbeat_max_age_ms: int = MAX_HEARTBEAT_AGE_MS,
    ) -> None:
        self.path = Path(database_path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self.heartbeat_max_age_ms = max(1, int(heartbeat_max_age_ms))
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
            current_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if current_version > SCHEMA_VERSION:
                raise RuntimeError("control-plane database schema is newer than this source.")
            connection.execute("BEGIN IMMEDIATE")
            try:
                for statement in filter(
                    str.strip,
                    """
                CREATE TABLE IF NOT EXISTS nodes (
                    device_id TEXT PRIMARY KEY,
                    endpoint_id TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    credential_hash TEXT NOT NULL,
                    credential_created_at_ms INTEGER NOT NULL,
                    credential_generation INTEGER NOT NULL DEFAULT 1,
                    revoked_at_ms INTEGER,
                    last_seen_at_ms INTEGER,
                    runtime_instance_id TEXT,
                    mcp_server_instance_id TEXT,
                    activation_epoch TEXT,
                    contract_version TEXT,
                    readiness TEXT NOT NULL DEFAULT 'unknown',
                    policy_state TEXT NOT NULL DEFAULT 'unobserved',
                    policy_expires_at_ms INTEGER,
                    policy_sha256 TEXT,
                    policy_observed_at_ms INTEGER,
                    policy_reason TEXT
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
                    receipt_digest TEXT,
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
                CREATE TABLE IF NOT EXISTS control_plane_state (
                    state_key TEXT PRIMARY KEY,
                    state_value TEXT NOT NULL,
                    changed_at_ms INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS mcp_read_only_intents (
                    owner_id TEXT NOT NULL,
                    principal_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    intent_digest TEXT NOT NULL,
                    facade_schema_version INTEGER NOT NULL,
                    facade_profile TEXT NOT NULL,
                    facade_contract_sha256 TEXT NOT NULL,
                    request_id TEXT NOT NULL REFERENCES work_requests(request_id),
                    action_id TEXT NOT NULL REFERENCES actions(action_id),
                    created_at_ms INTEGER NOT NULL,
                    PRIMARY KEY(owner_id, idempotency_key),
                    UNIQUE(request_id),
                    UNIQUE(action_id)
                );
                CREATE TABLE IF NOT EXISTS mcp_access_grants (
                    grant_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    principal_id TEXT NOT NULL,
                    context_id TEXT NOT NULL REFERENCES contexts(context_id),
                    token_digest TEXT NOT NULL UNIQUE,
                    created_at_ms INTEGER NOT NULL,
                    expires_at_ms INTEGER NOT NULL,
                    revoked_at_ms INTEGER
                );
                CREATE TABLE IF NOT EXISTS action_reconciliations (
                    action_id TEXT PRIMARY KEY REFERENCES actions(action_id),
                    owner_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    disposition TEXT NOT NULL CHECK(disposition = 'quarantined_unknown'),
                    declaration TEXT NOT NULL CHECK(declaration = 'HISTORICAL_READ_ONLY_UNKNOWN_EFFECT'),
                    receipt_id TEXT NOT NULL,
                    receipt_digest TEXT NOT NULL,
                    receipt_received_at_ms INTEGER NOT NULL,
                    evidence_digest TEXT NOT NULL,
                    reconciled_at_ms INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS actions_node_delivery_idx
                    ON actions(device_id, delivery_state, expires_at_ms);
                CREATE INDEX IF NOT EXISTS receipts_action_idx ON receipts(action_id, received_at_ms);
                CREATE INDEX IF NOT EXISTS mcp_read_only_intents_action_idx
                    ON mcp_read_only_intents(action_id);
                CREATE INDEX IF NOT EXISTS mcp_access_grants_context_idx
                    ON mcp_access_grants(context_id, expires_at_ms);
                CREATE INDEX IF NOT EXISTS action_reconciliations_owner_device_idx
                    ON action_reconciliations(owner_id, device_id, reconciled_at_ms);
                    """.split(";"),
                ):
                    connection.execute(statement)
                connection.execute(
                    "INSERT OR IGNORE INTO control_plane_state(state_key, state_value, changed_at_ms) VALUES ('admission_mode', 'open', ?)",
                    (self.clock(),),
                )
                node_columns = {str(row["name"]) for row in connection.execute("PRAGMA table_info(nodes)").fetchall()}
                if "credential_generation" not in node_columns:
                    connection.execute("ALTER TABLE nodes ADD COLUMN credential_generation INTEGER NOT NULL DEFAULT 1")
                if "mcp_server_instance_id" not in node_columns:
                    connection.execute("ALTER TABLE nodes ADD COLUMN mcp_server_instance_id TEXT")
                if "policy_state" not in node_columns:
                    connection.execute("ALTER TABLE nodes ADD COLUMN policy_state TEXT NOT NULL DEFAULT 'unobserved'")
                if "policy_expires_at_ms" not in node_columns:
                    connection.execute("ALTER TABLE nodes ADD COLUMN policy_expires_at_ms INTEGER")
                if "policy_sha256" not in node_columns:
                    connection.execute("ALTER TABLE nodes ADD COLUMN policy_sha256 TEXT")
                if "policy_observed_at_ms" not in node_columns:
                    connection.execute("ALTER TABLE nodes ADD COLUMN policy_observed_at_ms INTEGER")
                if "policy_reason" not in node_columns:
                    connection.execute("ALTER TABLE nodes ADD COLUMN policy_reason TEXT")
                receipt_columns = {str(row["name"]) for row in connection.execute("PRAGMA table_info(receipts)").fetchall()}
                if "receipt_digest" not in receipt_columns:
                    connection.execute("ALTER TABLE receipts ADD COLUMN receipt_digest TEXT")
                intent_columns = {
                    str(row["name"])
                    for row in connection.execute("PRAGMA table_info(mcp_read_only_intents)").fetchall()
                }
                # A pre-v7 fixed intent has no portable façade contract pin.
                # Retain it as durable history, but leave its empty fields for
                # the node's read-only bridge to reject before any local call.
                if "facade_schema_version" not in intent_columns:
                    connection.execute("ALTER TABLE mcp_read_only_intents ADD COLUMN facade_schema_version INTEGER NOT NULL DEFAULT 0")
                if "facade_profile" not in intent_columns:
                    connection.execute("ALTER TABLE mcp_read_only_intents ADD COLUMN facade_profile TEXT NOT NULL DEFAULT ''")
                if "facade_contract_sha256" not in intent_columns:
                    connection.execute("ALTER TABLE mcp_read_only_intents ADD COLUMN facade_contract_sha256 TEXT NOT NULL DEFAULT ''")
                # Earlier façade requests predate a root-MCP client identity.
                # Keep that history inspectable, but never let it authenticate
                # a new scoped grant or be mistaken for a current principal.
                if "principal_id" not in intent_columns:
                    connection.execute(
                        "ALTER TABLE mcp_read_only_intents ADD COLUMN principal_id TEXT NOT NULL DEFAULT 'legacy_unscoped'"
                    )
                # A pre-v2 receipt did not persist an attempt binding. Retain it as
                # historical evidence but never infer that a new receipt replays it.
                connection.execute(
                    "UPDATE receipts SET receipt_digest = 'legacy:' || receipt_id WHERE receipt_digest IS NULL OR receipt_digest = ''"
                )
                connection.execute("CREATE INDEX IF NOT EXISTS receipts_action_digest_idx ON receipts(action_id, receipt_digest)")
                connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            except Exception:
                connection.execute("ROLLBACK")
                raise
            else:
                connection.execute("COMMIT")

    def backup_to(self, destination_path: str | Path) -> dict[str, int | str]:
        """Create one verified, non-overwriting SQLite Backup API snapshot.

        This is intentionally explicit rather than an implicit startup side
        effect. Operators can preserve a consistent snapshot before a live
        migration or restore drill without treating a normal health check as a
        backup procedure.
        """
        return create_verified_backup(self.path, destination_path)

    @staticmethod
    def _admission_mode(connection: sqlite3.Connection) -> str:
        row = connection.execute(
            "SELECT state_value FROM control_plane_state WHERE state_key = 'admission_mode'"
        ).fetchone()
        mode = str(row["state_value"]) if row is not None else "recovery"
        return mode if mode in {"open", "recovery"} else "recovery"

    def admission_status(self) -> dict[str, Any]:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT state_value, changed_at_ms FROM control_plane_state WHERE state_key = 'admission_mode'"
            ).fetchone()
        mode = str(row["state_value"]) if row is not None else "recovery"
        return {
            "admission_mode": mode if mode in {"open", "recovery"} else "recovery",
            "changed_at_ms": row["changed_at_ms"] if row is not None else None,
        }

    def set_admission_mode(self, *, mode: str) -> dict[str, Any]:
        mode = str(mode or "").strip().lower()
        if mode not in {"open", "recovery"}:
            raise ValidationError("admission mode is invalid.")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = self._admission_mode(connection)
            if current != mode:
                now = self.clock()
                connection.execute(
                    "UPDATE control_plane_state SET state_value = ?, changed_at_ms = ? WHERE state_key = 'admission_mode'",
                    (mode, now),
                )
                self._event(connection, "control_plane", "admission", "admission_mode_changed", {"mode": mode})
            connection.execute("COMMIT")
        return self.admission_status()

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

    def heartbeat(self, *, device_id: str, endpoint_id: str, runtime_instance_id: str, activation_epoch: str, contract_version: str, readiness: str, mcp_server_instance_id: str = "", policy_observation: Any = None) -> dict[str, Any]:
        device_id = _text(device_id, "device_id")
        endpoint_id = _text(endpoint_id, "endpoint_id")
        readiness = str(readiness or "unknown").strip().lower()
        if readiness not in {"ready", "degraded", "blocked", "unknown"}:
            raise ValidationError("readiness is invalid.")
        policy = _node_policy_observation(policy_observation)
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
            assignments = [
                "last_seen_at_ms = ?", "runtime_instance_id = ?", "mcp_server_instance_id = ?",
                "activation_epoch = ?", "contract_version = ?", "readiness = ?",
            ]
            values: list[Any] = [
                now, str(runtime_instance_id or "")[:128], str(mcp_server_instance_id or "")[:128],
                str(activation_epoch or "")[:128], str(contract_version or "")[:128], readiness,
            ]
            if policy is not None:
                assignments.extend([
                    "policy_state = ?", "policy_expires_at_ms = ?", "policy_sha256 = ?",
                    "policy_observed_at_ms = ?", "policy_reason = ?",
                ])
                values.extend([
                    policy["state"], policy["expires_at_ms"], policy["policy_sha256"], now, policy["reason"],
                ])
            values.append(device_id)
            connection.execute(f"UPDATE nodes SET {', '.join(assignments)} WHERE device_id = ?", values)
            event = {"readiness": readiness}
            if policy is not None:
                event["policy_state"] = policy["state"]
            self._event(connection, "node", device_id, "node_heartbeat", event)
            connection.execute("COMMIT")
        return self.node(device_id=device_id)

    def node(self, *, device_id: str) -> dict[str, Any]:
        device_id = _text(device_id, "device_id")
        with self._connection() as connection:
            row = connection.execute(
                "SELECT device_id, endpoint_id, owner_id, display_name, credential_created_at_ms, credential_generation, revoked_at_ms, last_seen_at_ms, runtime_instance_id, mcp_server_instance_id, activation_epoch, contract_version, readiness, policy_state, policy_expires_at_ms, policy_sha256, policy_observed_at_ms, policy_reason FROM nodes WHERE device_id = ?",
                (device_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError("device is not enrolled.")
        return _row(row) or {}

    def node_observation(self, *, owner_id: str, device_id: str) -> dict[str, Any]:
        """Return a credential-free node projection only to its owner."""
        owner_id = _text(owner_id, "owner_id")
        node = self.node(device_id=device_id)
        if node["owner_id"] != owner_id:
            raise PermissionError("node is not owned by this principal.")
        return node

    def list_nodes(self, *, owner_id: str) -> list[dict[str, Any]]:
        """List owner-scoped node inventory without credential material."""
        owner_id = _text(owner_id, "owner_id")
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT device_id, endpoint_id, owner_id, display_name, credential_created_at_ms, credential_generation, revoked_at_ms, last_seen_at_ms, runtime_instance_id, mcp_server_instance_id, activation_epoch, contract_version, readiness, policy_state, policy_expires_at_ms, policy_sha256, policy_observed_at_ms, policy_reason FROM nodes WHERE owner_id = ? ORDER BY device_id",
                (owner_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _refuse_queued_actions(
        self,
        connection: sqlite3.Connection,
        *,
        action_column: str,
        subject_id: str,
        reason: str,
        now: int,
    ) -> int:
        """Settle only never-sent actions; prior sends remain reconcilable evidence."""
        if action_column not in {"device_id", "binding_id", "context_id", "request_id"}:
            raise RuntimeError("unsupported action refusal scope.")
        rows = connection.execute(
            f"SELECT action_id FROM actions WHERE {action_column} = ? AND delivery_state = 'queued'",
            (subject_id,),
        ).fetchall()
        for row in rows:
            connection.execute(
                "UPDATE actions SET delivery_state = 'settled', settled_at_ms = ? WHERE action_id = ?",
                (now, row["action_id"]),
            )
            self._event(connection, "action", row["action_id"], "action_dispatch_refused", {"reason": reason})
        return len(rows)

    def rotate_node_credential(self, *, owner_id: str, device_id: str) -> dict[str, str | int]:
        owner_id = _text(owner_id, "owner_id")
        device_id = _text(device_id, "device_id")
        new_secret = secrets.token_urlsafe(32)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            node = self._node_for_owner(connection, owner_id, device_id)
            now = self.clock()
            generation = int(node["credential_generation"]) + 1
            connection.execute(
                "UPDATE nodes SET credential_hash = ?, credential_created_at_ms = ?, credential_generation = ? WHERE device_id = ?",
                (_digest({"node_secret": new_secret}), now, generation, device_id),
            )
            self._event(connection, "node", device_id, "node_credential_rotated", {"credential_generation": generation})
            connection.execute("COMMIT")
        return {"device_id": device_id, "node_secret": new_secret, "credential_generation": generation}

    def revoke_node(self, *, owner_id: str, device_id: str) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        device_id = _text(device_id, "device_id")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            node = connection.execute("SELECT * FROM nodes WHERE device_id = ?", (device_id,)).fetchone()
            if node is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("device is not enrolled.")
            if node["owner_id"] != owner_id:
                connection.execute("ROLLBACK")
                raise PermissionError("device is not owned by this principal.")
            if node["revoked_at_ms"] is None:
                now = self.clock()
                connection.execute("UPDATE nodes SET revoked_at_ms = ? WHERE device_id = ?", (now, device_id))
                refused = self._refuse_queued_actions(
                    connection,
                    action_column="device_id",
                    subject_id=device_id,
                    reason="node_revoked",
                    now=now,
                )
                self._event(connection, "node", device_id, "node_revoked", {"queued_actions_refused": refused})
            connection.execute("COMMIT")
        return self.node(device_id=device_id)

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

    def revoke_binding(self, *, owner_id: str, binding_id: str) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        binding_id = _text(binding_id, "binding_id")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            binding = connection.execute("SELECT * FROM bindings WHERE binding_id = ?", (binding_id,)).fetchone()
            if binding is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("binding does not exist.")
            if binding["owner_id"] != owner_id:
                connection.execute("ROLLBACK")
                raise PermissionError("binding is not owned by this principal.")
            if binding["revoked_at_ms"] is None:
                now = self.clock()
                connection.execute("UPDATE bindings SET revoked_at_ms = ? WHERE binding_id = ?", (now, binding_id))
                refused = self._refuse_queued_actions(
                    connection,
                    action_column="binding_id",
                    subject_id=binding_id,
                    reason="binding_revoked",
                    now=now,
                )
                self._event(connection, "binding", binding_id, "binding_revoked", {"queued_actions_refused": refused})
            row = connection.execute("SELECT * FROM bindings WHERE binding_id = ?", (binding_id,)).fetchone()
            connection.execute("COMMIT")
        return _row(row) or {}

    def _live_binding_for_new_context(self, connection: sqlite3.Connection, owner_id: str, binding_id: str) -> sqlite3.Row:
        """Return the binding only while its node can admit a fresh context.

        A binding is durable evidence and intentionally remains inspectable after
        its node is revoked. That must not permit a new context to be attached
        to the revoked target during the gap between a preliminary read and an
        insert transaction.
        """
        row = connection.execute(
            """
            SELECT b.*, n.owner_id AS node_owner_id, n.revoked_at_ms AS node_revoked_at_ms
            FROM bindings b
            JOIN nodes n ON n.device_id = b.device_id
            WHERE b.binding_id = ?
            """,
            (binding_id,),
        ).fetchone()
        if row is None:
            raise NotFoundError("binding does not exist.")
        if row["owner_id"] != owner_id or row["node_owner_id"] != owner_id:
            raise PermissionError("binding authority does not match this principal.")
        if row["revoked_at_ms"] is not None:
            raise ConflictError("binding is revoked.")
        if row["node_revoked_at_ms"] is not None:
            raise ConflictError("node is revoked.")
        return row

    def create_context(self, *, owner_id: str, binding_id: str, expires_at_ms: int) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        binding_id = _text(binding_id, "binding_id")
        expires_at_ms = int(expires_at_ms)
        context_id = f"ctx_{uuid.uuid4().hex}"
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            now = self.clock()
            if expires_at_ms <= now:
                connection.execute("ROLLBACK")
                raise ValidationError("context expiry must be in the future.")
            binding = self._live_binding_for_new_context(connection, owner_id, binding_id)
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

    def list_contexts(self, *, owner_id: str) -> list[dict[str, Any]]:
        """List owner-scoped durable contexts, including closed/expired evidence."""
        owner_id = _text(owner_id, "owner_id")
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM contexts WHERE owner_id = ? ORDER BY created_at_ms, context_id",
                (owner_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_work_request(self, *, owner_id: str, context_id: str, objective: str, criteria: dict[str, Any], scope: dict[str, Any], expires_at_ms: int) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        context_id = _text(context_id, "context_id")
        objective = str(objective or "").strip()
        if not 1 <= len(objective) <= 4000:
            raise ValidationError("objective is invalid.")
        criteria = _object(criteria, "criteria")
        scope = _object(scope, "scope")
        expires_at_ms = int(expires_at_ms)
        request_id = f"req_{uuid.uuid4().hex}"
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            context = connection.execute(
                """
                SELECT
                    c.*, b.owner_id AS binding_owner_id, b.revoked_at_ms AS binding_revoked_at_ms,
                    n.owner_id AS node_owner_id, n.revoked_at_ms AS node_revoked_at_ms
                FROM contexts c
                JOIN bindings b ON b.binding_id = c.binding_id
                JOIN nodes n ON n.device_id = c.device_id
                WHERE c.context_id = ?
                """,
                (context_id,),
            ).fetchone()
            if context is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("context does not exist.")
            if context["owner_id"] != owner_id or context["binding_owner_id"] != owner_id or context["node_owner_id"] != owner_id:
                connection.execute("ROLLBACK")
                raise PermissionError("context authority does not match this principal.")
            transaction_now = self.clock()
            if expires_at_ms <= transaction_now or expires_at_ms > context["expires_at_ms"]:
                connection.execute("ROLLBACK")
                raise ValidationError("work request expiry is invalid.")
            if context["closed_at_ms"] is not None or context["expires_at_ms"] <= transaction_now:
                connection.execute("ROLLBACK")
                raise ConflictError("context is not live.")
            if context["binding_revoked_at_ms"] is not None:
                connection.execute("ROLLBACK")
                raise ConflictError("binding is revoked.")
            if context["node_revoked_at_ms"] is not None:
                connection.execute("ROLLBACK")
                raise ConflictError("node is revoked.")
            connection.execute(
                "INSERT INTO work_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                (request_id, owner_id, context["context_id"], objective, _canonical_json(criteria), _canonical_json(scope), transaction_now, expires_at_ms),
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

    def list_work_requests(self, *, owner_id: str) -> list[dict[str, Any]]:
        """List owner-scoped requests; cancellation remains visible as evidence."""
        owner_id = _text(owner_id, "owner_id")
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM work_requests WHERE owner_id = ? ORDER BY created_at_ms, request_id",
                (owner_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def work_request_observation(self, *, owner_id: str, request_id: str) -> dict[str, Any]:
        """Return a request and its non-payload action lineage to the owner.

        This is an observation surface, not a reconciliation or execution API.
        It intentionally omits action arguments and admission references; those
        remain available only from the already owner-scoped action observation.
        """
        request = self.work_request(owner_id=owner_id, request_id=request_id)
        with self._connection() as connection:
            actions = connection.execute(
                "SELECT action_id, context_id, binding_id, device_id, endpoint_id, workspace_id, workspace_generation, tool_name, action_digest, idempotency_key, created_at_ms, expires_at_ms, delivery_state, settled_at_ms FROM actions WHERE request_id = ? ORDER BY created_at_ms, action_id",
                (request_id,),
            ).fetchall()
        request["actions"] = [dict(action) for action in actions]
        return request

    def close_context(self, *, owner_id: str, context_id: str) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        context_id = _text(context_id, "context_id")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            context = connection.execute("SELECT * FROM contexts WHERE context_id = ?", (context_id,)).fetchone()
            if context is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("context does not exist.")
            if context["owner_id"] != owner_id:
                connection.execute("ROLLBACK")
                raise PermissionError("context is not owned by this principal.")
            if context["closed_at_ms"] is None:
                now = self.clock()
                connection.execute("UPDATE contexts SET closed_at_ms = ? WHERE context_id = ?", (now, context_id))
                refused = self._refuse_queued_actions(
                    connection,
                    action_column="context_id",
                    subject_id=context_id,
                    reason="context_closed",
                    now=now,
                )
                self._event(connection, "context", context_id, "context_closed", {"queued_actions_refused": refused})
            row = connection.execute("SELECT * FROM contexts WHERE context_id = ?", (context_id,)).fetchone()
            connection.execute("COMMIT")
        return _row(row) or {}

    def cancel_work_request(self, *, owner_id: str, request_id: str) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        request_id = _text(request_id, "request_id")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            request = connection.execute("SELECT * FROM work_requests WHERE request_id = ?", (request_id,)).fetchone()
            if request is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("work request does not exist.")
            if request["owner_id"] != owner_id:
                connection.execute("ROLLBACK")
                raise PermissionError("work request is not owned by this principal.")
            if request["canceled_at_ms"] is None:
                now = self.clock()
                connection.execute("UPDATE work_requests SET canceled_at_ms = ? WHERE request_id = ?", (now, request_id))
                refused = self._refuse_queued_actions(
                    connection,
                    action_column="request_id",
                    subject_id=request_id,
                    reason="work_request_canceled",
                    now=now,
                )
                self._event(connection, "work_request", request_id, "work_request_canceled", {"queued_actions_refused": refused})
            row = connection.execute("SELECT * FROM work_requests WHERE request_id = ?", (request_id,)).fetchone()
            connection.execute("COMMIT")
        return _row(row) or {}

    def seal_action(self, *, owner_id: str, request_id: str, tool_name: str, arguments: dict[str, Any], idempotency_key: str, admission_reference: str, expires_at_ms: int) -> dict[str, Any]:
        request = self.work_request(owner_id=owner_id, request_id=request_id)
        now = self.clock()
        if request["canceled_at_ms"] is not None or request["expires_at_ms"] <= now:
            raise ConflictError("work request is not dispatchable.")
        context = self.context(owner_id=owner_id, context_id=request["context_id"], require_live=True)
        self.binding(owner_id=owner_id, binding_id=context["binding_id"])
        tool_name = _text(tool_name, "tool_name")
        if tool_name not in ALLOWED_TOOL_NAMES:
            raise ValidationError("tool_name is not in the smart-v3 surface.")
        arguments = _object(arguments, "arguments")
        if tool_name == "workspace_context" and arguments == MCP_READ_ONLY_WORKSPACE_CONTEXT_ARGUMENTS:
            raise ValidationError("fixed read-only workspace_context is reserved for the MCP facade intent lane.")
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
            if self._admission_mode(connection) != "open":
                connection.execute("ROLLBACK")
                raise ConflictError("central admission is in recovery mode.")
            live = connection.execute(
                """
                SELECT
                    w.owner_id AS request_owner_id, w.context_id AS request_context_id,
                    w.expires_at_ms AS request_expires_at_ms, w.canceled_at_ms AS request_canceled_at_ms,
                    c.binding_id AS context_binding_id, c.device_id AS context_device_id,
                    c.endpoint_id AS context_endpoint_id, c.workspace_id AS context_workspace_id,
                    c.workspace_generation AS context_workspace_generation,
                    c.expires_at_ms AS context_expires_at_ms, c.closed_at_ms AS context_closed_at_ms,
                    b.owner_id AS binding_owner_id, b.device_id AS binding_device_id,
                    b.endpoint_id AS binding_endpoint_id, b.workspace_id AS binding_workspace_id,
                    b.workspace_generation AS binding_workspace_generation, b.revoked_at_ms AS binding_revoked_at_ms,
                    n.owner_id AS node_owner_id, n.endpoint_id AS node_endpoint_id, n.revoked_at_ms AS node_revoked_at_ms
                FROM work_requests w
                JOIN contexts c ON c.context_id = w.context_id
                JOIN bindings b ON b.binding_id = c.binding_id
                JOIN nodes n ON n.device_id = c.device_id
                WHERE w.request_id = ?
                """,
                (request_id,),
            ).fetchone()
            transaction_now = self.clock()
            if live is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("work request does not exist.")
            if live["request_owner_id"] != owner_id or live["binding_owner_id"] != owner_id or live["node_owner_id"] != owner_id:
                connection.execute("ROLLBACK")
                raise PermissionError("work request authority does not match this principal.")
            if (
                live["request_context_id"] != context["context_id"]
                or live["context_binding_id"] != context["binding_id"]
                or live["context_device_id"] != context["device_id"]
                or live["context_endpoint_id"] != context["endpoint_id"]
                or live["context_workspace_id"] != context["workspace_id"]
                or live["context_workspace_generation"] != context["workspace_generation"]
                or live["binding_device_id"] != context["device_id"]
                or live["binding_endpoint_id"] != context["endpoint_id"]
                or live["binding_workspace_id"] != context["workspace_id"]
                or live["binding_workspace_generation"] != context["workspace_generation"]
                or live["node_endpoint_id"] != context["endpoint_id"]
            ):
                connection.execute("ROLLBACK")
                raise ConflictError("sealed action identity is no longer current.")
            if (
                live["request_canceled_at_ms"] is not None
                or live["request_expires_at_ms"] <= transaction_now
                or live["context_closed_at_ms"] is not None
                or live["context_expires_at_ms"] <= transaction_now
                or live["binding_revoked_at_ms"] is not None
                or live["node_revoked_at_ms"] is not None
                or expires_at_ms <= transaction_now
            ):
                connection.execute("ROLLBACK")
                raise ConflictError("work request authority is not dispatchable.")
            connection.execute(
                "INSERT INTO actions(action_id, owner_id, request_id, context_id, binding_id, device_id, endpoint_id, workspace_id, workspace_generation, tool_name, arguments_json, action_digest, idempotency_key, admission_reference, created_at_ms, expires_at_ms, delivery_state, settled_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                (action_id, owner_id, request_id, context["context_id"], context["binding_id"], context["device_id"], context["endpoint_id"], context["workspace_id"], context["workspace_generation"], tool_name, _canonical_json(arguments), digest, idempotency_key, admission_reference, transaction_now, expires_at_ms, "queued"),
            )
            self._event(connection, "action", action_id, "action_sealed", {"request_id": request_id, "digest": digest})
            connection.execute("COMMIT")
        return self.action(owner_id=owner_id, action_id=action_id)

    def create_mcp_access_grant(
        self,
        *,
        owner_id: str,
        context_id: str,
        principal_id: str,
        expires_at_ms: int,
    ) -> dict[str, Any]:
        """Issue one context-bound bearer for the root MCP ingress.

        This is deliberately not the operator bearer and does not create a
        local action.  Its audience is one external MCP client/controller,
        its target is one existing context, and closing that context or
        revoking its binding/node makes the bearer unusable even before the
        recorded expiry.
        """

        owner_id = _text(owner_id, "owner_id")
        context_id = _text(context_id, "context_id")
        principal_id = _text(principal_id, "principal_id")
        if isinstance(expires_at_ms, bool):
            raise ValidationError("MCP access grant expiry is invalid.")
        try:
            expires_at_ms = int(expires_at_ms)
        except (TypeError, ValueError) as error:
            raise ValidationError("MCP access grant expiry is invalid.") from error

        access_token = f"mcp_{secrets.token_urlsafe(32)}"
        token_digest = _mcp_access_token_digest(access_token)
        grant_id = f"mcpgrant_{uuid.uuid4().hex}"
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            now = self.clock()
            live = connection.execute(
                """
                SELECT
                    c.context_id, c.owner_id AS context_owner_id,
                    c.expires_at_ms AS context_expires_at_ms, c.closed_at_ms,
                    b.owner_id AS binding_owner_id, b.revoked_at_ms AS binding_revoked_at_ms,
                    n.owner_id AS node_owner_id, n.revoked_at_ms AS node_revoked_at_ms
                FROM contexts c
                JOIN bindings b ON b.binding_id = c.binding_id
                JOIN nodes n ON n.device_id = c.device_id
                WHERE c.context_id = ?
                """,
                (context_id,),
            ).fetchone()
            if live is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("context does not exist.")
            if (
                live["context_owner_id"] != owner_id
                or live["binding_owner_id"] != owner_id
                or live["node_owner_id"] != owner_id
            ):
                connection.execute("ROLLBACK")
                raise PermissionError("context authority does not match this principal.")
            if (
                live["closed_at_ms"] is not None
                or live["binding_revoked_at_ms"] is not None
                or live["node_revoked_at_ms"] is not None
                or expires_at_ms <= now
                or expires_at_ms > live["context_expires_at_ms"]
            ):
                connection.execute("ROLLBACK")
                raise ConflictError("MCP access grant authority is not live.")
            connection.execute(
                """
                INSERT INTO mcp_access_grants(
                    grant_id, owner_id, principal_id, context_id, token_digest,
                    created_at_ms, expires_at_ms, revoked_at_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (grant_id, owner_id, principal_id, context_id, token_digest, now, expires_at_ms),
            )
            self._event(
                connection,
                "mcp_access_grant",
                grant_id,
                "mcp_access_grant_created",
                {"principal_id": principal_id, "context_id": context_id, "expires_at_ms": expires_at_ms},
            )
            connection.execute("COMMIT")
        return {
            "grant_id": grant_id,
            "owner_id": owner_id,
            "principal_id": principal_id,
            "context_id": context_id,
            "expires_at_ms": expires_at_ms,
            # This is the only raw-token return path. It must be handled by
            # the protected caller and never copied into an observation/log.
            "access_token": access_token,
        }

    def authenticate_mcp_access_token(self, *, access_token: str) -> dict[str, Any]:
        """Resolve one unrevoked, still-live root-MCP bearer to its scope."""

        token_digest = _mcp_access_token_digest(access_token)
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT
                    g.grant_id, g.owner_id, g.principal_id, g.context_id,
                    g.token_digest, g.expires_at_ms, g.revoked_at_ms,
                    c.owner_id AS context_owner_id, c.expires_at_ms AS context_expires_at_ms,
                    c.closed_at_ms,
                    b.owner_id AS binding_owner_id, b.revoked_at_ms AS binding_revoked_at_ms,
                    n.owner_id AS node_owner_id, n.revoked_at_ms AS node_revoked_at_ms
                FROM mcp_access_grants g
                JOIN contexts c ON c.context_id = g.context_id
                JOIN bindings b ON b.binding_id = c.binding_id
                JOIN nodes n ON n.device_id = c.device_id
                WHERE g.token_digest = ?
                """,
                (token_digest,),
            ).fetchone()
        if row is None or not hmac.compare_digest(str(row["token_digest"]), token_digest):
            raise PermissionError("MCP client authentication failed.")
        now = self.clock()
        if (
            row["revoked_at_ms"] is not None
            or row["expires_at_ms"] <= now
            or row["context_expires_at_ms"] <= now
            or row["closed_at_ms"] is not None
            or row["binding_revoked_at_ms"] is not None
            or row["node_revoked_at_ms"] is not None
            or row["context_owner_id"] != row["owner_id"]
            or row["binding_owner_id"] != row["owner_id"]
            or row["node_owner_id"] != row["owner_id"]
        ):
            raise PermissionError("MCP client access grant is no longer live.")
        return {
            key: row[key]
            for key in ("grant_id", "owner_id", "principal_id", "context_id", "expires_at_ms")
        }

    def list_mcp_access_grants(self, *, owner_id: str) -> list[dict[str, Any]]:
        """Return redacted grant metadata for operator lifecycle control."""

        owner_id = _text(owner_id, "owner_id")
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT grant_id, owner_id, principal_id, context_id,
                       created_at_ms, expires_at_ms, revoked_at_ms
                FROM mcp_access_grants
                WHERE owner_id = ?
                ORDER BY created_at_ms, grant_id
                """,
                (owner_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def revoke_mcp_access_grant(self, *, owner_id: str, grant_id: str) -> dict[str, Any]:
        """Revoke a root-MCP bearer without altering unrelated node authority."""

        owner_id = _text(owner_id, "owner_id")
        grant_id = _text(grant_id, "grant_id")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM mcp_access_grants WHERE grant_id = ?", (grant_id,)).fetchone()
            if row is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("MCP access grant does not exist.")
            if row["owner_id"] != owner_id:
                connection.execute("ROLLBACK")
                raise PermissionError("MCP access grant is not owned by this principal.")
            if row["revoked_at_ms"] is None:
                now = self.clock()
                connection.execute("UPDATE mcp_access_grants SET revoked_at_ms = ? WHERE grant_id = ?", (now, grant_id))
                self._event(connection, "mcp_access_grant", grant_id, "mcp_access_grant_revoked", {})
            result = connection.execute(
                """
                SELECT grant_id, owner_id, principal_id, context_id,
                       created_at_ms, expires_at_ms, revoked_at_ms
                FROM mcp_access_grants WHERE grant_id = ?
                """,
                (grant_id,),
            ).fetchone()
            connection.execute("COMMIT")
        return _row(result) or {}

    def request_mcp_read_only_workspace_context(
        self,
        *,
        owner_id: str,
        context_id: str,
        idempotency_key: str,
        expires_at_ms: int,
        facade_contract: dict[str, Any],
        principal_id: str = "operator_browser",
    ) -> dict[str, Any]:
        """Atomically create one fixed read-only request and sealed action.

        This is deliberately narrower than ``create_work_request`` plus
        ``seal_action``: clients cannot select a different tool, arguments,
        objective, admission reference, target, or execution route. The
        caller receives only a durable central intent; a node must still pass
        its local policy, strict runtime and actor gates before any local MCP
        call can happen.
        """
        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        context_id = _text(context_id, "context_id")
        idempotency_key = _text(idempotency_key, "idempotency_key", pattern=KEY_PATTERN)
        if isinstance(expires_at_ms, bool):
            raise ValidationError("expires_at_ms is invalid.")
        try:
            expires_at_ms = int(expires_at_ms)
        except (TypeError, ValueError) as error:
            raise ValidationError("expires_at_ms is invalid.") from error
        facade_contract = _facade_contract(facade_contract)

        arguments = dict(MCP_READ_ONLY_WORKSPACE_CONTEXT_ARGUMENTS)
        intent = {
            "kind": "mcp_facade_read_only_workspace_context_v4",
            "principal_id": principal_id,
            "context_id": context_id,
            "tool_name": "workspace_context",
            "arguments": arguments,
            "idempotency_key": idempotency_key,
            "expires_at_ms": expires_at_ms,
            "facade_contract": facade_contract,
        }
        intent_digest = _digest(intent)
        request_id = f"req_{uuid.uuid4().hex}"
        action_id = f"act_{uuid.uuid4().hex}"

        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM mcp_read_only_intents WHERE owner_id = ? AND idempotency_key = ?",
                (owner_id, idempotency_key),
            ).fetchone()
            if existing is not None:
                if existing["intent_digest"] != intent_digest:
                    connection.execute("ROLLBACK")
                    raise ConflictError("idempotency key is already bound to a different read-only request.")
                connection.execute("COMMIT")
                return {
                    "request_id": existing["request_id"],
                    "action_id": existing["action_id"],
                    "intent_digest": existing["intent_digest"],
                    "facade_contract": {
                        "schema_version": existing["facade_schema_version"],
                        "profile": existing["facade_profile"],
                        "sha256": existing["facade_contract_sha256"],
                    },
                    "replayed": True,
                }

            now = self.clock()
            if self._admission_mode(connection) != "open":
                connection.execute("ROLLBACK")
                raise ConflictError("central admission is in recovery mode.")
            live = connection.execute(
                """
                SELECT
                    c.context_id, c.owner_id AS context_owner_id, c.binding_id,
                    c.device_id, c.endpoint_id, c.workspace_id, c.workspace_generation,
                    c.expires_at_ms AS context_expires_at_ms, c.closed_at_ms,
                    b.owner_id AS binding_owner_id, b.device_id AS binding_device_id,
                    b.endpoint_id AS binding_endpoint_id, b.workspace_id AS binding_workspace_id,
                    b.workspace_generation AS binding_workspace_generation, b.revoked_at_ms AS binding_revoked_at_ms,
                    n.owner_id AS node_owner_id, n.endpoint_id AS node_endpoint_id, n.revoked_at_ms AS node_revoked_at_ms
                FROM contexts c
                JOIN bindings b ON b.binding_id = c.binding_id
                JOIN nodes n ON n.device_id = c.device_id
                WHERE c.context_id = ?
                """,
                (context_id,),
            ).fetchone()
            if live is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("context does not exist.")
            if live["context_owner_id"] != owner_id or live["binding_owner_id"] != owner_id or live["node_owner_id"] != owner_id:
                connection.execute("ROLLBACK")
                raise PermissionError("context authority does not match this principal.")
            if (
                live["closed_at_ms"] is not None
                or live["binding_revoked_at_ms"] is not None
                or live["node_revoked_at_ms"] is not None
                or expires_at_ms <= now
                or expires_at_ms > live["context_expires_at_ms"]
            ):
                connection.execute("ROLLBACK")
                raise ConflictError("read-only request authority is not dispatchable.")
            if (
                live["binding_device_id"] != live["device_id"]
                or live["binding_endpoint_id"] != live["endpoint_id"]
                or live["binding_workspace_id"] != live["workspace_id"]
                or live["binding_workspace_generation"] != live["workspace_generation"]
                or live["node_endpoint_id"] != live["endpoint_id"]
            ):
                connection.execute("ROLLBACK")
                raise ConflictError("context identity is no longer current.")

            action_immutable = {
                "request_id": request_id,
                "context_id": live["context_id"],
                "binding_id": live["binding_id"],
                "device_id": live["device_id"],
                "endpoint_id": live["endpoint_id"],
                "workspace_id": live["workspace_id"],
                "workspace_generation": live["workspace_generation"],
                "tool_name": "workspace_context",
                "arguments": arguments,
                "idempotency_key": idempotency_key,
                "admission_reference": f"mcp_facade:{intent_digest}",
                "expires_at_ms": expires_at_ms,
                "facade_contract": facade_contract,
            }
            action_digest = _digest(action_immutable)
            conflicting_action = connection.execute(
                "SELECT action_id FROM actions WHERE owner_id = ? AND device_id = ? AND idempotency_key = ?",
                (owner_id, live["device_id"], idempotency_key),
            ).fetchone()
            if conflicting_action is not None:
                connection.execute("ROLLBACK")
                raise ConflictError("idempotency key is already bound to a different action.")

            connection.execute(
                "INSERT INTO work_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                (
                    request_id,
                    owner_id,
                    live["context_id"],
                    "Read compact workspace context through the local control-plane bridge.",
                    _canonical_json({"kind": "read_only", "tool_name": "workspace_context"}),
                    _canonical_json({"operation": "workspace_context", "arguments": arguments}),
                    now,
                    expires_at_ms,
                ),
            )
            connection.execute(
                """
                INSERT INTO actions(
                    action_id, owner_id, request_id, context_id, binding_id, device_id,
                    endpoint_id, workspace_id, workspace_generation, tool_name,
                    arguments_json, action_digest, idempotency_key, admission_reference,
                    created_at_ms, expires_at_ms, delivery_state, settled_at_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', NULL)
                """,
                (
                    action_id,
                    owner_id,
                    request_id,
                    live["context_id"],
                    live["binding_id"],
                    live["device_id"],
                    live["endpoint_id"],
                    live["workspace_id"],
                    live["workspace_generation"],
                    "workspace_context",
                    _canonical_json(arguments),
                    action_digest,
                    idempotency_key,
                    f"mcp_facade:{intent_digest}",
                    now,
                    expires_at_ms,
                ),
            )
            connection.execute(
                """
                INSERT INTO mcp_read_only_intents(
                    owner_id, principal_id, idempotency_key, intent_digest,
                    facade_schema_version, facade_profile, facade_contract_sha256,
                    request_id, action_id, created_at_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    owner_id,
                    principal_id,
                    idempotency_key,
                    intent_digest,
                    facade_contract["schema_version"],
                    facade_contract["profile"],
                    facade_contract["sha256"],
                    request_id,
                    action_id,
                    now,
                ),
            )
            self._event(connection, "work_request", request_id, "mcp_read_only_request_created", {"context_id": context_id, "intent_digest": intent_digest})
            self._event(connection, "action", action_id, "action_sealed", {"request_id": request_id, "digest": action_digest})
            connection.execute("COMMIT")
        return {
            "request_id": request_id,
            "action_id": action_id,
            "intent_digest": intent_digest,
            "facade_contract": facade_contract,
            "replayed": False,
        }

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

    @staticmethod
    def _dispatch_refusal_reason(row: sqlite3.Row, now: int) -> str | None:
        """Return a terminal reason only when the sealed authority is invalid now.

        A merely stale or non-ready node is intentionally not terminalized: the
        action stays queued and may be dispatched after a fresh, attributable
        heartbeat. A changed/revoked/expired authority must never be delivered.
        """
        if row["expires_at_ms"] <= now:
            return "action_expired"
        if row["_node_revoked_at_ms"] is not None:
            return "node_revoked"
        if row["_binding_revoked_at_ms"] is not None:
            return "binding_revoked"
        if row["_context_closed_at_ms"] is not None or row["_context_expires_at_ms"] <= now:
            return "context_not_live"
        if row["_request_canceled_at_ms"] is not None or row["_request_expires_at_ms"] <= now:
            return "work_request_not_live"
        if (
            row["endpoint_id"] != row["_node_endpoint_id"]
            or row["endpoint_id"] != row["_binding_endpoint_id"]
            or row["endpoint_id"] != row["_context_endpoint_id"]
            or row["workspace_id"] != row["_binding_workspace_id"]
            or row["workspace_id"] != row["_context_workspace_id"]
            or row["workspace_generation"] != row["_binding_workspace_generation"]
            or row["workspace_generation"] != row["_context_workspace_generation"]
            or row["device_id"] != row["_binding_device_id"]
            or row["device_id"] != row["_context_device_id"]
        ):
            return "sealed_identity_mismatch"
        return None

    def _node_is_dispatchable(self, row: sqlite3.Row, now: int) -> bool:
        last_seen_at_ms = row["_node_last_seen_at_ms"]
        return (
            row["_node_readiness"] == "ready"
            and isinstance(last_seen_at_ms, int)
            and last_seen_at_ms + self.heartbeat_max_age_ms >= now
            and _reported_runtime_identity(row["_node_runtime_instance_id"])
            and _reported_runtime_identity(row["_node_mcp_server_instance_id"])
            and _reported_runtime_identity(row["_node_activation_epoch"])
            and _reported_runtime_identity(row["_node_contract_version"])
        )

    def poll_actions(self, *, device_id: str, limit: int = 10) -> list[dict[str, Any]]:
        device_id = _text(device_id, "device_id")
        limit = max(1, min(int(limit), 50))
        now = self.clock()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if self._admission_mode(connection) != "open":
                connection.execute("COMMIT")
                return []
            rows = connection.execute(
                """
                SELECT
                    a.*,
                    n.endpoint_id AS _node_endpoint_id,
                    n.revoked_at_ms AS _node_revoked_at_ms,
                    n.last_seen_at_ms AS _node_last_seen_at_ms,
                    n.runtime_instance_id AS _node_runtime_instance_id,
                    n.mcp_server_instance_id AS _node_mcp_server_instance_id,
                    n.activation_epoch AS _node_activation_epoch,
                    n.contract_version AS _node_contract_version,
                    n.readiness AS _node_readiness,
                    b.device_id AS _binding_device_id,
                    b.endpoint_id AS _binding_endpoint_id,
                    b.workspace_id AS _binding_workspace_id,
                    b.workspace_generation AS _binding_workspace_generation,
                    b.revoked_at_ms AS _binding_revoked_at_ms,
                    c.device_id AS _context_device_id,
                    c.endpoint_id AS _context_endpoint_id,
                    c.workspace_id AS _context_workspace_id,
                    c.workspace_generation AS _context_workspace_generation,
                    c.closed_at_ms AS _context_closed_at_ms,
                    c.expires_at_ms AS _context_expires_at_ms,
                    w.canceled_at_ms AS _request_canceled_at_ms,
                    w.expires_at_ms AS _request_expires_at_ms,
                    m.intent_digest AS mcp_read_only_intent_digest,
                    m.facade_schema_version AS mcp_facade_schema_version,
                    m.facade_profile AS mcp_facade_profile,
                    m.facade_contract_sha256 AS mcp_facade_contract_sha256
                FROM actions a
                JOIN nodes n ON n.device_id = a.device_id
                JOIN bindings b ON b.binding_id = a.binding_id
                JOIN contexts c ON c.context_id = a.context_id
                JOIN work_requests w ON w.request_id = a.request_id
                LEFT JOIN mcp_read_only_intents m ON m.action_id = a.action_id
                WHERE a.device_id = ? AND a.delivery_state = 'queued'
                ORDER BY a.created_at_ms
                LIMIT ?
                """,
                (device_id, limit),
            ).fetchall()
            result: list[dict[str, Any]] = []
            for row in rows:
                refusal_reason = self._dispatch_refusal_reason(row, now)
                if refusal_reason is not None:
                    connection.execute(
                        "UPDATE actions SET delivery_state = 'settled', settled_at_ms = ? WHERE action_id = ?",
                        (now, row["action_id"]),
                    )
                    self._event(
                        connection,
                        "action",
                        row["action_id"],
                        "action_dispatch_refused",
                        {"reason": refusal_reason},
                    )
                    continue
                if not self._node_is_dispatchable(row, now):
                    continue
                attempts = connection.execute("SELECT COUNT(*) FROM delivery_attempts WHERE action_id = ?", (row["action_id"],)).fetchone()[0]
                connection.execute("UPDATE actions SET delivery_state = 'dispatch_unconfirmed' WHERE action_id = ?", (row["action_id"],))
                attempt_id = f"try_{uuid.uuid4().hex}"
                connection.execute(
                    "INSERT INTO delivery_attempts VALUES (?, ?, ?, ?)",
                    (attempt_id, row["action_id"], attempts + 1, now),
                )
                self._event(connection, "action", row["action_id"], "action_delivery_attempted", {"attempt": attempts + 1, "attempt_id": attempt_id})
                payload = {key: row[key] for key in row.keys() if not key.startswith("_")}
                payload["delivery_state"] = "dispatch_unconfirmed"
                payload["attempt_id"] = attempt_id
                result.append(payload)
            connection.execute("COMMIT")
        return result

    def record_receipt(
        self,
        *,
        device_id: str,
        action_id: str,
        attempt_id: str,
        receipt_state: str,
        local_handle: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        device_id = _text(device_id, "device_id")
        action_id = _text(action_id, "action_id")
        attempt_id = _text(attempt_id, "attempt_id")
        receipt_state = str(receipt_state or "").strip().lower()
        if receipt_state not in {"accepted", *TERMINAL_RECEIPT_STATES, *RECONCILIATION_RECEIPT_STATES}:
            raise ValidationError("receipt_state is invalid.")
        payload = _object(payload, "payload")
        local_handle = str(local_handle or "").strip()[:256]
        if receipt_state in {"accepted", "completed"} and not local_handle:
            raise ValidationError("local_handle is required for accepted or completed receipts.")
        receipt_digest = _digest(
            {
                "attempt_id": attempt_id,
                "receipt_state": receipt_state,
                "local_handle": local_handle,
                "payload": payload,
            }
        )
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            action = connection.execute("SELECT * FROM actions WHERE action_id = ?", (action_id,)).fetchone()
            if action is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("action does not exist.")
            if action["device_id"] != device_id:
                connection.execute("ROLLBACK")
                raise PermissionError("action belongs to another device.")
            attempt = connection.execute(
                "SELECT * FROM delivery_attempts WHERE attempt_id = ? AND action_id = ?",
                (attempt_id, action_id),
            ).fetchone()
            if attempt is None:
                connection.execute("ROLLBACK")
                raise ConflictError("receipt does not bind to a delivered attempt.")
            existing = connection.execute(
                "SELECT * FROM receipts WHERE action_id = ? AND receipt_digest = ?",
                (action_id, receipt_digest),
            ).fetchone()
            if existing is not None:
                connection.execute("COMMIT")
                return {
                    "receipt_id": existing["receipt_id"],
                    "action_id": action_id,
                    "attempt_id": attempt_id,
                    "receipt_state": existing["receipt_state"],
                    "delivery_state": action["delivery_state"],
                    "replayed": True,
                }
            if action["delivery_state"] == "queued":
                connection.execute("ROLLBACK")
                raise ConflictError("action has not been delivered to this node.")
            if action["delivery_state"] == "settled":
                connection.execute("ROLLBACK")
                raise ConflictError("action is already settled.")
            if action["delivery_state"] == "accepted" and receipt_state in {"accepted", "unknown"}:
                connection.execute("ROLLBACK")
                raise ConflictError("action is already accepted; a terminal receipt is required.")
            if action["delivery_state"] == "reconcile_required" and receipt_state in {"accepted", "unknown"}:
                connection.execute("ROLLBACK")
                raise ConflictError("action requires a terminal reconciliation receipt.")
            if action["delivery_state"] == "accepted" and receipt_state in TERMINAL_RECEIPT_STATES:
                accepted = connection.execute(
                    "SELECT local_handle FROM receipts WHERE action_id = ? AND receipt_state = 'accepted' ORDER BY received_at_ms DESC LIMIT 1",
                    (action_id,),
                ).fetchone()
                if accepted is None or accepted["local_handle"] != local_handle:
                    connection.execute("ROLLBACK")
                    raise ConflictError("terminal receipt local_handle does not match accepted receipt.")
            receipt_id = f"rcpt_{uuid.uuid4().hex}"
            now = self.clock()
            connection.execute(
                "INSERT INTO receipts(receipt_id, action_id, device_id, local_handle, receipt_state, payload_json, receipt_digest, received_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (receipt_id, action_id, device_id, local_handle, receipt_state, _canonical_json(payload), receipt_digest, now),
            )
            if receipt_state in TERMINAL_RECEIPT_STATES:
                delivery_state = "settled"
            elif receipt_state in RECONCILIATION_RECEIPT_STATES:
                delivery_state = "reconcile_required"
            else:
                delivery_state = "accepted"
            settled_at = now if delivery_state == "settled" else None
            connection.execute("UPDATE actions SET delivery_state = ?, settled_at_ms = ? WHERE action_id = ?", (delivery_state, settled_at, action_id))
            self._event(connection, "action", action_id, "action_receipt_recorded", {"receipt_state": receipt_state, "delivery_state": delivery_state})
            connection.execute("COMMIT")
        return {
            "receipt_id": receipt_id,
            "action_id": action_id,
            "attempt_id": attempt_id,
            "receipt_state": receipt_state,
            "delivery_state": delivery_state,
            "replayed": False,
        }

    def quarantine_historical_unknown_actions(
        self,
        *,
        owner_id: str,
        device_id: str,
        action_ids: Any,
        declaration: str,
    ) -> dict[str, Any]:
        """Record a deliberate, non-terminal disposition for historic unknown reads.

        This is a narrow operator risk acceptance for a fixed read-only canary
        whose local effect cannot be determined after the original delivery.
        It never modifies the immutable receipt, does not settle the action,
        and cannot make the action eligible for redelivery.  A reconciliation
        record is durable audit evidence, not a claim about what Windows did.
        """

        owner_id = _text(owner_id, "owner_id")
        device_id = _text(device_id, "device_id")
        if declaration != QUARANTINE_UNKNOWN_DECLARATION:
            raise ValidationError("historical unknown declaration is invalid.")
        if not isinstance(action_ids, list) or not 1 <= len(action_ids) <= 50:
            raise ValidationError("action_ids must contain between 1 and 50 exact action IDs.")
        normalized_action_ids = [_text(value, "action_id") for value in action_ids]
        if len(set(normalized_action_ids)) != len(normalized_action_ids):
            raise ValidationError("action_ids must not contain duplicates.")

        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            node = connection.execute(
                "SELECT owner_id FROM nodes WHERE device_id = ?", (device_id,)
            ).fetchone()
            if node is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("device is not enrolled.")
            if node["owner_id"] != owner_id:
                connection.execute("ROLLBACK")
                raise PermissionError("device is not owned by this principal.")
            # Reconciliation is historical evidence handling, not new
            # execution authority; a revoked node must not erase the owner's
            # ability to make this disposition for its earlier unknown action.
            now = self.clock()
            reconciled: list[dict[str, Any]] = []
            try:
                for action_id in normalized_action_ids:
                    action = connection.execute(
                        "SELECT * FROM actions WHERE action_id = ?", (action_id,)
                    ).fetchone()
                    if action is None:
                        raise NotFoundError("action does not exist.")
                    if action["owner_id"] != owner_id:
                        raise PermissionError("action is not owned by this principal.")
                    if action["device_id"] != device_id:
                        raise ConflictError("action does not belong to the selected device.")
                    if action["tool_name"] != "workspace_context":
                        raise ConflictError("only workspace_context actions can be quarantined as historical unknowns.")
                    if action["delivery_state"] != "reconcile_required":
                        raise ConflictError("action is not awaiting historical unknown reconciliation.")
                    existing = connection.execute(
                        "SELECT action_id FROM action_reconciliations WHERE action_id = ?", (action_id,)
                    ).fetchone()
                    if existing is not None:
                        raise ConflictError("action already has an operator reconciliation disposition.")
                    receipt = connection.execute(
                        """
                        SELECT receipt_id, receipt_state, receipt_digest, received_at_ms
                        FROM receipts
                        WHERE action_id = ?
                        ORDER BY received_at_ms DESC, receipt_id DESC
                        LIMIT 1
                        """,
                        (action_id,),
                    ).fetchone()
                    if receipt is None or receipt["receipt_state"] != "unknown":
                        raise ConflictError("action does not retain an unknown latest receipt.")
                    attempt_count = int(
                        connection.execute(
                            "SELECT COUNT(*) FROM delivery_attempts WHERE action_id = ?", (action_id,)
                        ).fetchone()[0]
                    )
                    evidence_digest = _digest(
                        {
                            "schema_version": 1,
                            "action_id": action_id,
                            "owner_id": owner_id,
                            "device_id": device_id,
                            "tool_name": action["tool_name"],
                            "delivery_state": action["delivery_state"],
                            "latest_receipt_id": receipt["receipt_id"],
                            "latest_receipt_state": receipt["receipt_state"],
                            "latest_receipt_digest": receipt["receipt_digest"],
                            "latest_receipt_received_at_ms": receipt["received_at_ms"],
                            "delivery_attempt_count": attempt_count,
                        }
                    )
                    connection.execute(
                        """
                        INSERT INTO action_reconciliations(
                            action_id, owner_id, device_id, disposition, declaration,
                            receipt_id, receipt_digest, receipt_received_at_ms,
                            evidence_digest, reconciled_at_ms
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            action_id,
                            owner_id,
                            device_id,
                            QUARANTINE_UNKNOWN_DISPOSITION,
                            QUARANTINE_UNKNOWN_DECLARATION,
                            receipt["receipt_id"],
                            receipt["receipt_digest"],
                            receipt["received_at_ms"],
                            evidence_digest,
                            now,
                        ),
                    )
                    self._event(
                        connection,
                        "action",
                        action_id,
                        "action_historical_unknown_quarantined",
                        {
                            "disposition": QUARANTINE_UNKNOWN_DISPOSITION,
                            "declaration": QUARANTINE_UNKNOWN_DECLARATION,
                            "evidence_digest": evidence_digest,
                        },
                    )
                    reconciled.append(
                        {
                            "action_id": action_id,
                            "disposition": QUARANTINE_UNKNOWN_DISPOSITION,
                            "reconciled_at_ms": now,
                        }
                    )
            except Exception:
                connection.execute("ROLLBACK")
                raise
            connection.execute("COMMIT")
        return {
            "device_id": device_id,
            "declaration": QUARANTINE_UNKNOWN_DECLARATION,
            "actions": reconciled,
        }

    def action_observation(self, *, owner_id: str, action_id: str) -> dict[str, Any]:
        """Return owner-scoped immutable action, delivery attempts, and receipts."""
        action = self.action(owner_id=owner_id, action_id=action_id)
        with self._connection() as connection:
            attempts = connection.execute(
                "SELECT attempt_id, attempt_number, dispatched_at_ms FROM delivery_attempts WHERE action_id = ? ORDER BY attempt_number",
                (action_id,),
            ).fetchall()
            receipts = connection.execute(
                "SELECT receipt_id, action_id, device_id, local_handle, receipt_state, payload_json, receipt_digest, received_at_ms FROM receipts WHERE action_id = ? ORDER BY received_at_ms, receipt_id",
                (action_id,),
            ).fetchall()
            reconciliation = connection.execute(
                """
                SELECT action_id, owner_id, device_id, disposition, declaration,
                       receipt_id, receipt_digest, receipt_received_at_ms,
                       evidence_digest, reconciled_at_ms
                FROM action_reconciliations
                WHERE action_id = ?
                """,
                (action_id,),
            ).fetchone()
        action["attempts"] = [dict(item) for item in attempts]
        action["receipts"] = [dict(item) for item in receipts]
        action["reconciliation"] = _row(reconciliation)
        return action

    def list_action_lifecycle(self, *, owner_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """List bounded, credential-free action lifecycle projections for an owner.

        This is deliberately narrower than :meth:`action_observation`: the
        browser dashboard needs to distinguish queued, uncertain, accepted and
        terminal work, but must not receive immutable arguments, admission
        references, local handles, raw receipt payloads or receipt digests.
        """
        owner_id = _text(owner_id, "owner_id")
        try:
            bounded_limit = max(1, min(int(limit), 100))
        except (TypeError, ValueError) as error:
            raise ValidationError("action lifecycle limit is invalid.") from error
        with self._connection() as connection:
            actions = connection.execute(
                """
                SELECT action.action_id, action.request_id, action.context_id,
                       action.device_id, action.tool_name, action.created_at_ms,
                       action.expires_at_ms, action.delivery_state, action.settled_at_ms,
                       reconciliation.disposition AS reconciliation_disposition,
                       reconciliation.reconciled_at_ms
                FROM actions AS action
                LEFT JOIN action_reconciliations AS reconciliation
                  ON reconciliation.action_id = action.action_id
                WHERE action.owner_id = ?
                ORDER BY action.created_at_ms DESC, action.action_id DESC
                LIMIT ?
                """,
                (owner_id, bounded_limit),
            ).fetchall()
            action_ids = [str(action["action_id"]) for action in actions]
            receipt_rows: list[sqlite3.Row] = []
            if action_ids:
                placeholders = ", ".join("?" for _ in action_ids)
                receipt_rows = connection.execute(
                    f"""
                    SELECT action_id, receipt_state, received_at_ms
                    FROM receipts
                    WHERE action_id IN ({placeholders})
                    ORDER BY action_id, received_at_ms DESC, receipt_id DESC
                    """,
                    action_ids,
                ).fetchall()
        receipts_by_action: dict[str, list[sqlite3.Row]] = {}
        for receipt in receipt_rows:
            receipts_by_action.setdefault(str(receipt["action_id"]), []).append(receipt)
        result: list[dict[str, Any]] = []
        for action in actions:
            projection = dict(action)
            receipts = receipts_by_action.get(str(action["action_id"]), [])
            projection["receipt_count"] = len(receipts)
            projection["latest_receipt_state"] = receipts[0]["receipt_state"] if receipts else None
            projection["latest_receipt_at_ms"] = receipts[0]["received_at_ms"] if receipts else None
            result.append(projection)
        return result

    def health(self) -> dict[str, Any]:
        with self._connection() as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            admission_mode = self._admission_mode(connection)
            counts = {
                name: connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                for name in (
                    "nodes",
                    "enrollment_requests",
                    "bindings",
                    "contexts",
                    "work_requests",
                    "actions",
                    "receipts",
                    "mcp_read_only_intents",
                    "mcp_access_grants",
                    "action_reconciliations",
                )
            }
            unresolved_action_count = int(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM actions
                    WHERE delivery_state IN ('dispatch_unconfirmed', 'accepted', 'reconcile_required')
                    """
                ).fetchone()[0]
            )
            quarantined_unknown_action_count = int(
                connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM actions AS action
                    JOIN action_reconciliations AS reconciliation
                      ON reconciliation.action_id = action.action_id
                    WHERE action.delivery_state = 'reconcile_required'
                      AND reconciliation.disposition = ?
                    """,
                    (QUARANTINE_UNKNOWN_DISPOSITION,),
                ).fetchone()[0]
            )
        return {
            "ok": integrity == "ok",
            "sqlite_integrity": integrity,
            "schema_version": schema_version,
            "admission_mode": admission_mode,
            "counts": counts,
            "unresolved_action_count": unresolved_action_count,
            "quarantined_unknown_action_count": quarantined_unknown_action_count,
            "unquarantined_unresolved_action_count": unresolved_action_count - quarantined_unknown_action_count,
        }
