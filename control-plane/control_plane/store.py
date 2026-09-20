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
from urllib.parse import urlsplit


ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{2,127}$")
KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{7,255}$")
TASK_ID_PATTERN = re.compile(r"^task_[a-f0-9]{32}$")
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
SCHEMA_VERSION = 19
MCP_TASK_SESSION_MAX_TTL_MS = 24 * 60 * 60 * 1000
MAX_HEARTBEAT_AGE_MS = 60_000
MCP_READ_ONLY_WORKSPACE_CONTEXT_ARGUMENTS = {"detail": "compact", "max_entries": 1}
MCP_BOUNDED_FILE_READ_MAX_BYTES = 16 * 1024
MCP_BOUNDED_FILE_READ_MAX_LINES = 200
MCP_BOUNDED_FILE_READ_MAX_TTL_MS = 5 * 60 * 1000
# A permission request is deliberately shorter than a task/context window.
# It proves that an owner reviewed one exact proposed future mutation; it does
# not create a local policy or make an effect dispatchable by itself.
MCP_PATCH_PERMISSION_MAX_TTL_MS = 5 * 60 * 1000
MCP_PATCH_PERMISSION_TOOL_NAME = "agent_workflow"
MCP_PATCH_PERMISSION_OPERATION = "apply_patch"
MCP_PATCH_PERMISSION_VALIDATION_PROFILE = "targeted"
# The first write relay is intentionally narrow: one exact existing UTF-8
# file represented by Coding Tools' ``Write Exact File`` envelope.  The raw
# envelope must be kept briefly in the protected central database so the
# Windows node can receive a durable, idempotent action.  It is never copied
# into generic action arguments, events, normal owner projections, or MCP
# status results.  This explicit retention boundary is deliberately small
# until an encrypted/blob-backed payload mechanism is designed.
MCP_APPROVED_PATCH_MAX_BYTES = 32 * 1024
MCP_APPROVED_PATCH_TOOL_NAME = "agent_workflow"
MCP_APPROVED_PATCH_OPERATION = "apply_patch"
# Bounded exec is intentionally narrow: argv array without shell, cwd confined
# to the task workspace, explicit timeout/output caps. Central records the
# request; the Windows node revalidates argv against its local allowlist and
# enforces process/tree limits. cwd never implies filesystem confinement by
# itself: the bridge must enforce root containment and the local write lock.
MCP_EXEC_MAX_ARGV_ITEMS = 8
MCP_EXEC_MAX_ARGV_ITEM_BYTES = 256
MCP_EXEC_MAX_TIMEOUT_MS = 5 * 60 * 1000
MCP_EXEC_MIN_TIMEOUT_MS = 5_000
MCP_EXEC_MAX_OUTPUT_BYTES = 64 * 1024
MCP_EXEC_MAX_TTL_MS = 10 * 60 * 1000
MCP_EXEC_TOOL_NAME = "exec_command"
MCP_EXEC_OPERATION = "exec_run"
MCP_EXEC_CONTROL_TOOL_NAME = "command_control"
# Scoped artifacts reuse the file-read allowlist: docs are bounded UTF-8 text,
# images are bounded binary with an explicit MIME allowlist. Both are
# task-pinned reads; document bytes are never policy or instructions.
MCP_ARTIFACT_MAX_BYTES = 256 * 1024
MCP_ARTIFACT_IMAGE_MAX_BYTES = 1024 * 1024
MCP_ARTIFACT_MAX_TTL_MS = 5 * 60 * 1000
MCP_ARTIFACT_ALLOWED_MIME = ("image/png", "image/jpeg", "image/webp")
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
WORKSPACE_CAPABILITY_KEYS = frozenset({"read", "write", "exec"})


def _bounded_file_read_path(value: Any) -> str:
    """Accept one exact, policy-friendly relative POSIX file path.

    This is intentionally stricter than the local Coding MCP path resolver.
    The root facade is never a general remote filesystem interface: Windows
    will admit the exact result only when it also appears in a local allowlist.
    """

    if not isinstance(value, str):
        raise ValidationError("bounded file path is invalid.")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValidationError("bounded file path is invalid.") from error
    if (
        not encoded
        or len(encoded) > 512
        or value.startswith("/")
        or "\\" in value
        or ":" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ValidationError("bounded file path is invalid.")
    parts = value.split("/")
    if any(not part or part in {".", ".."} for part in parts):
        raise ValidationError("bounded file path is invalid.")
    lowered = [part.lower() for part in parts]
    sensitive_directories = {".git", ".ssh", ".aws", ".gnupg", "secrets", "secret", "credentials", "credential"}
    if any(part in sensitive_directories or part.startswith(".env") for part in lowered):
        raise ValidationError("bounded file path is not permitted.")
    basename = lowered[-1]
    if (
        basename in {"id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", "credentials", "credential"}
        or basename.endswith((".pem", ".key", ".p12", ".pfx"))
    ):
        raise ValidationError("bounded file path is not permitted.")
    return value


def _bounded_file_read_limits(*, start_line: Any, max_lines: Any, max_bytes: Any) -> tuple[int, int, int]:
    values = (start_line, max_lines, max_bytes)
    if any(not isinstance(value, int) or isinstance(value, bool) for value in values):
        raise ValidationError("bounded file read limits are invalid.")
    if not 1 <= start_line <= 1_000_000 or not 1 <= max_lines <= MCP_BOUNDED_FILE_READ_MAX_LINES or not 1 <= max_bytes <= MCP_BOUNDED_FILE_READ_MAX_BYTES:
        raise ValidationError("bounded file read limits are invalid.")
    return start_line, max_lines, max_bytes


def _mcp_exec_argv(value: Any) -> list[str]:
    """Validate structured argv without shell interpretation.

    The facade never accepts a command string, shell flag, environment map,
    or network addresses. Each item is a short printable token; the Windows
    node must additionally match the full argv against its local allowlist
    before spawn. An empty list, shell metacharacters and oversized items fail.
    """
    if not isinstance(value, list) or not 1 <= len(value) <= MCP_EXEC_MAX_ARGV_ITEMS:
        raise ValidationError("exec argv is invalid.")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValidationError("exec argv is invalid.")
        try:
            encoded = item.encode("utf-8")
        except UnicodeEncodeError as error:
            raise ValidationError("exec argv is invalid.") from error
        if not encoded or len(encoded) > MCP_EXEC_MAX_ARGV_ITEM_BYTES:
            raise ValidationError("exec argv is invalid.")
        if any(ord(c) < 32 or ord(c) == 127 for c in item):
            raise ValidationError("exec argv is invalid.")
        # Reject shell indirection at the central boundary; the bridge runs
        # with shell:false and must never reinterpret these tokens.
        if any(token in item for token in (";", "&&", "||", "`", "$(", "|", ">", "<", "\n", "\r")):
            raise ValidationError("exec argv must not contain shell metacharacters.")
        if item != item.strip() or not item:
            raise ValidationError("exec argv is invalid.")
        normalized.append(item)
    first = normalized[0].lower()
    if "/" in first or "\\" in first or ":" in first:
        raise ValidationError("exec command must be a bare executable name.")
    return normalized


def _mcp_exec_cwd(value: Any) -> str:
    """Validate a root-relative working directory, never a sandbox claim.

    An empty value means the workspace root. A relative POSIX path keeps the
    process start directory inside the selected root, but test/build steps can
    still write outside via absolute paths, symlinks or network calls. The
    bridge must enforce containment, the exec policy and the local write lock.
    """
    if value is None or value == "":
        return ""
    if not isinstance(value, str):
        raise ValidationError("exec cwd is invalid.")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValidationError("exec cwd is invalid.") from error
    if not encoded or len(encoded) > 512 or value.startswith("/") or "\\" in value or ":" in value:
        raise ValidationError("exec cwd is invalid.")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValidationError("exec cwd is invalid.")
    parts = value.split("/")
    if any(not part or part in {".", ".."} for part in parts):
        raise ValidationError("exec cwd is invalid.")
    return value


def _mcp_exec_limits(*, timeout_ms: Any, max_output_bytes: Any) -> tuple[int, int]:
    if not isinstance(timeout_ms, int) or isinstance(timeout_ms, bool):
        raise ValidationError("exec timeout is invalid.")
    if not isinstance(max_output_bytes, int) or isinstance(max_output_bytes, bool):
        raise ValidationError("exec output limit is invalid.")
    if not MCP_EXEC_MIN_TIMEOUT_MS <= timeout_ms <= MCP_EXEC_MAX_TIMEOUT_MS:
        raise ValidationError("exec timeout is invalid.")
    if not 1024 <= max_output_bytes <= MCP_EXEC_MAX_OUTPUT_BYTES:
        raise ValidationError("exec output limit is invalid.")
    return timeout_ms, max_output_bytes


def _mcp_patch_permission_scope(
    *,
    path: Any,
    preimage_sha256: Any,
    patch_sha256: Any,
    validation_profile: Any,
) -> dict[str, str]:
    """Validate the one non-executable C4 permission-request shape.

    This is *not* a general argument bag and does not contain patch text,
    command text, or a local filesystem path.  A later local mutation bridge
    will have to receive an independently supplied patch, derive the same
    digest, and revalidate its own policy before it can create an effect.
    """

    normalized_path = _bounded_file_read_path(path)
    normalized_hashes: dict[str, str] = {}
    for field, value in (("preimage_sha256", preimage_sha256), ("patch_sha256", patch_sha256)):
        if not isinstance(value, str):
            raise ValidationError(f"{field} is invalid.")
        candidate = value.strip().lower()
        if SHA256_PATTERN.fullmatch(candidate) is None:
            raise ValidationError(f"{field} is invalid.")
        normalized_hashes[field] = candidate
    if validation_profile != MCP_PATCH_PERMISSION_VALIDATION_PROFILE:
        raise ValidationError("validation_profile is invalid.")
    return {
        "path": normalized_path,
        "preimage_sha256": normalized_hashes["preimage_sha256"],
        "patch_sha256": normalized_hashes["patch_sha256"],
        "validation_profile": MCP_PATCH_PERMISSION_VALIDATION_PROFILE,
    }


def _mcp_approved_patch_envelope(
    value: Any,
    *,
    expected_path: str,
    expected_preimage_sha256: str,
    expected_patch_sha256: str,
) -> str:
    """Validate the initial single-file, exact-write C4 payload.

    ``request_permissions`` persists only digest-level approval evidence.  A
    subsequent approved action necessarily carries the raw patch to the local
    executor, but must prove that it is the exact bytes the owner reviewed.
    Keep the grammar deliberately smaller than the local ``apply_patch``
    grammar: no add/delete/move/multiple-file patch can accidentally enter the
    first central write lane.
    """

    if not isinstance(value, str):
        raise ValidationError("approved patch envelope is invalid.")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValidationError("approved patch envelope is invalid.") from error
    if (
        not encoded
        or len(encoded) > MCP_APPROVED_PATCH_MAX_BYTES
        or "\x00" in value
        or any(ord(character) < 32 and character not in {"\n", "\r", "\t"} for character in value)
    ):
        raise ValidationError("approved patch envelope is invalid.")
    actual_patch_sha256 = hashlib.sha256(encoded).hexdigest()
    if actual_patch_sha256 != expected_patch_sha256:
        raise ConflictError("approved patch bytes do not match the reviewed patch digest.")

    normalized = value.replace("\r\n", "\n")
    # The local parser only treats CRLF as transport framing.  An isolated CR
    # would make the central and local interpretation needlessly ambiguous.
    if "\r" in normalized:
        raise ValidationError("approved patch envelope is invalid.")
    lines = normalized.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if len(lines) < 5 or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        raise ValidationError("approved patch envelope must use the exact Write Exact File format.")
    if lines[1] != f"*** Write Exact File: {expected_path}":
        raise ValidationError("approved patch envelope path does not match the reviewed scope.")
    metadata_line = lines[2]
    if not metadata_line.startswith("@@ "):
        raise ValidationError("approved patch envelope is invalid.")
    metadata: dict[str, str] = {}
    for token in metadata_line.removeprefix("@@ ").split():
        key, separator, candidate = token.partition("=")
        if not separator or not key or key in metadata:
            raise ValidationError("approved patch envelope is invalid.")
        metadata[key] = candidate.lower()
    if set(metadata) != {"encoding", "preimage_sha256", "postimage_sha256"}:
        raise ValidationError("approved patch envelope is invalid.")
    if (
        metadata["encoding"] != "zlib-base64"
        or metadata["preimage_sha256"] != expected_preimage_sha256
        or SHA256_PATTERN.fullmatch(metadata["postimage_sha256"]) is None
        or not all(line.startswith("+") for line in lines[3:-1])
        or not lines[3:-1]
    ):
        raise ValidationError("approved patch envelope is invalid.")
    return value


def _workspace_capabilities(value: Any) -> dict[str, bool]:
    """Validate one node-declared capability inventory.

    This describes what the locally selected root *could* support.  It is not
    a task grant, local policy, or permission to execute an operation.  Keeping
    the shape small and exact lets a later central action bind to an immutable
    inventory record without accepting caller-defined capability names.
    """

    if not isinstance(value, dict) or set(value) != WORKSPACE_CAPABILITY_KEYS:
        raise ValidationError("workspace capabilities are invalid.")
    normalized: dict[str, bool] = {}
    for name in sorted(WORKSPACE_CAPABILITY_KEYS):
        enabled = value.get(name)
        if not isinstance(enabled, bool):
            raise ValidationError("workspace capabilities are invalid.")
        normalized[name] = enabled
    if not normalized["read"]:
        raise ValidationError("workspace read capability is required.")
    return normalized


def _mcp_access_token_digest(value: str) -> str:
    """Hash a root-MCP bearer without reusing the node-secret namespace.

    The raw bearer is returned exactly once when an operator creates a grant.
    The durable store and every observation surface retain only this
    domain-separated digest.
    """

    return hashlib.sha256(
        b"coding-tools-control-plane:mcp-access-grant:v1\0" + str(value or "").encode("utf-8")
    ).hexdigest()


def _oauth_issuer(value: Any) -> str:
    """Validate one exact HTTPS issuer identity without normalizing it.

    OAuth issuer matching is string-exact. The control plane therefore stores
    the configured issuer value verbatim after rejecting URL forms that cannot
    be a trusted OIDC/OAuth authorization-server identifier.
    """

    if not isinstance(value, str) or not value or value != value.strip():
        raise ValidationError("OAuth issuer is invalid.")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise ValidationError("OAuth issuer is invalid.") from error
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or port is not None and not 1 <= port <= 65535
    ):
        raise ValidationError("OAuth issuer is invalid.")
    return value


def _oauth_subject(value: Any) -> str:
    """Keep the IdP's opaque subject only long enough to derive a digest."""

    if not isinstance(value, str):
        raise ValidationError("OAuth subject is invalid.")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValidationError("OAuth subject is invalid.") from error
    if not encoded or len(encoded) > 1024 or any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValidationError("OAuth subject is invalid.")
    return value


def _oauth_subject_digest(*, issuer: str, subject: str) -> str:
    """Store an opaque mapping key, not a raw IdP subject or email address."""

    return hashlib.sha256(
        b"coding-tools-control-plane:oauth-principal:v1\0"
        + issuer.encode("utf-8")
        + b"\0"
        + subject.encode("utf-8")
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
                CREATE TABLE IF NOT EXISTS mcp_file_read_intents (
                    owner_id TEXT NOT NULL,
                    principal_id TEXT NOT NULL REFERENCES oauth_principals(principal_id),
                    idempotency_key TEXT NOT NULL,
                    intent_digest TEXT NOT NULL,
                    facade_schema_version INTEGER NOT NULL,
                    facade_profile TEXT NOT NULL,
                    facade_contract_sha256 TEXT NOT NULL,
                    binding_id TEXT NOT NULL REFERENCES bindings(binding_id),
                    request_id TEXT NOT NULL REFERENCES work_requests(request_id),
                    action_id TEXT NOT NULL REFERENCES actions(action_id),
                    created_at_ms INTEGER NOT NULL,
                    PRIMARY KEY(principal_id, idempotency_key),
                    UNIQUE(request_id),
                    UNIQUE(action_id)
                );
                CREATE TABLE IF NOT EXISTS mcp_permission_requests (
                    permission_request_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    principal_id TEXT NOT NULL REFERENCES oauth_principals(principal_id),
                    binding_id TEXT NOT NULL REFERENCES bindings(binding_id),
                    device_id TEXT NOT NULL,
                    endpoint_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    workspace_generation TEXT NOT NULL,
                    tool_name TEXT NOT NULL CHECK(tool_name = 'agent_workflow'),
                    operation TEXT NOT NULL CHECK(operation = 'apply_patch'),
                    relative_path TEXT NOT NULL,
                    preimage_sha256 TEXT NOT NULL,
                    patch_sha256 TEXT NOT NULL,
                    validation_profile TEXT NOT NULL CHECK(validation_profile = 'targeted'),
                    permission_digest TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    task_id TEXT,
                    facade_schema_version INTEGER NOT NULL,
                    facade_profile TEXT NOT NULL,
                    facade_contract_sha256 TEXT NOT NULL,
                    created_at_ms INTEGER NOT NULL,
                    expires_at_ms INTEGER NOT NULL,
                    state TEXT NOT NULL CHECK(state IN ('pending', 'approved', 'rejected')),
                    decided_at_ms INTEGER,
                    decided_by TEXT,
                    UNIQUE(principal_id, idempotency_key),
                    CHECK(
                        (state = 'pending' AND decided_at_ms IS NULL AND decided_by IS NULL)
                        OR (state IN ('approved', 'rejected') AND decided_at_ms IS NOT NULL AND decided_by IS NOT NULL)
                    )
                );
                CREATE TABLE IF NOT EXISTS mcp_approved_patch_intents (
                    owner_id TEXT NOT NULL,
                    principal_id TEXT NOT NULL REFERENCES oauth_principals(principal_id),
                    permission_request_id TEXT NOT NULL UNIQUE REFERENCES mcp_permission_requests(permission_request_id),
                    permission_digest TEXT NOT NULL,
                    binding_id TEXT NOT NULL REFERENCES bindings(binding_id),
                    idempotency_key TEXT NOT NULL,
                    intent_digest TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    preimage_sha256 TEXT NOT NULL,
                    patch_sha256 TEXT NOT NULL,
                    validation_profile TEXT NOT NULL CHECK(validation_profile = 'targeted'),
                    patch_envelope TEXT NOT NULL,
                    facade_schema_version INTEGER NOT NULL,
                    facade_profile TEXT NOT NULL,
                    facade_contract_sha256 TEXT NOT NULL,
                    request_id TEXT NOT NULL REFERENCES work_requests(request_id),
                    action_id TEXT NOT NULL REFERENCES actions(action_id),
                    created_at_ms INTEGER NOT NULL,
                    PRIMARY KEY(principal_id, idempotency_key),
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
                CREATE TABLE IF NOT EXISTS mcp_exec_intents (
                    owner_id TEXT NOT NULL,
                    principal_id TEXT NOT NULL REFERENCES oauth_principals(principal_id),
                    binding_id TEXT NOT NULL REFERENCES bindings(binding_id),
                    task_id TEXT REFERENCES mcp_task_sessions(task_id),
                    argv_json TEXT NOT NULL,
                    argv_digest TEXT NOT NULL,
                    cwd TEXT NOT NULL DEFAULT '',
                    timeout_ms INTEGER NOT NULL,
                    max_output_bytes INTEGER NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    intent_digest TEXT NOT NULL,
                    facade_schema_version INTEGER NOT NULL,
                    facade_profile TEXT NOT NULL,
                    facade_contract_sha256 TEXT NOT NULL,
                    request_id TEXT NOT NULL REFERENCES work_requests(request_id),
                    action_id TEXT NOT NULL REFERENCES actions(action_id),
                    created_at_ms INTEGER NOT NULL,
                    PRIMARY KEY(principal_id, idempotency_key),
                    UNIQUE(request_id),
                    UNIQUE(action_id)
                );
                CREATE TABLE IF NOT EXISTS mcp_exec_stop_requests (
                    action_id TEXT PRIMARY KEY REFERENCES actions(action_id),
                    owner_id TEXT NOT NULL,
                    principal_id TEXT NOT NULL REFERENCES oauth_principals(principal_id),
                    requested_at_ms INTEGER NOT NULL,
                    requested_by TEXT NOT NULL,
                    state TEXT NOT NULL CHECK(state IN ('pending', 'acknowledged')) DEFAULT 'pending',
                    acknowledged_at_ms INTEGER
                );
                CREATE TABLE IF NOT EXISTS mcp_artifact_intents (
                    owner_id TEXT NOT NULL,
                    principal_id TEXT NOT NULL REFERENCES oauth_principals(principal_id),
                    binding_id TEXT NOT NULL REFERENCES bindings(binding_id),
                    task_id TEXT REFERENCES mcp_task_sessions(task_id),
                    kind TEXT NOT NULL CHECK(kind IN ('document', 'image')),
                    path TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    intent_digest TEXT NOT NULL,
                    facade_schema_version INTEGER NOT NULL,
                    facade_profile TEXT NOT NULL,
                    facade_contract_sha256 TEXT NOT NULL,
                    request_id TEXT NOT NULL REFERENCES work_requests(request_id),
                    action_id TEXT NOT NULL REFERENCES actions(action_id),
                    created_at_ms INTEGER NOT NULL,
                    PRIMARY KEY(principal_id, idempotency_key),
                    UNIQUE(request_id),
                    UNIQUE(action_id)
                );
                CREATE TABLE IF NOT EXISTS oauth_principals (
                    principal_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    issuer TEXT NOT NULL,
                    subject_digest TEXT NOT NULL,
                    created_at_ms INTEGER NOT NULL,
                    revoked_at_ms INTEGER,
                    UNIQUE(issuer, subject_digest)
                );
                CREATE TABLE IF NOT EXISTS oauth_link_requests (
                    link_request_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    issuer TEXT NOT NULL,
                    subject_digest TEXT NOT NULL,
                    requested_at_ms INTEGER NOT NULL,
                    state TEXT NOT NULL CHECK(state IN ('pending', 'approved', 'rejected')),
                    decided_at_ms INTEGER,
                    decided_by TEXT,
                    principal_id TEXT REFERENCES oauth_principals(principal_id),
                    UNIQUE(issuer, subject_digest),
                    CHECK(
                        (state = 'pending' AND decided_at_ms IS NULL AND decided_by IS NULL AND principal_id IS NULL)
                        OR (state = 'approved' AND decided_at_ms IS NOT NULL AND decided_by IS NOT NULL AND principal_id IS NOT NULL)
                        OR (state = 'rejected' AND decided_at_ms IS NOT NULL AND decided_by IS NOT NULL AND principal_id IS NULL)
                    )
                );
                CREATE TABLE IF NOT EXISTS node_workspaces (
                    device_id TEXT NOT NULL REFERENCES nodes(device_id),
                    workspace_id TEXT NOT NULL,
                    workspace_generation TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    capabilities_json TEXT NOT NULL,
                    registered_at_ms INTEGER NOT NULL,
                    retired_at_ms INTEGER,
                    PRIMARY KEY(device_id, workspace_id, workspace_generation)
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
                CREATE TABLE IF NOT EXISTS mcp_task_sessions (
                    task_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    principal_id TEXT NOT NULL REFERENCES oauth_principals(principal_id),
                    binding_id TEXT NOT NULL REFERENCES bindings(binding_id),
                    device_id TEXT NOT NULL,
                    endpoint_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    workspace_generation TEXT NOT NULL,
                    label TEXT NOT NULL,
                    created_at_ms INTEGER NOT NULL,
                    expires_at_ms INTEGER NOT NULL,
                    closed_at_ms INTEGER,
                    close_reason TEXT
                );
                CREATE TABLE IF NOT EXISTS mcp_task_action_links (
                    task_id TEXT NOT NULL REFERENCES mcp_task_sessions(task_id),
                    action_id TEXT NOT NULL REFERENCES actions(action_id),
                    added_at_ms INTEGER NOT NULL,
                    PRIMARY KEY(task_id, action_id),
                    UNIQUE(action_id)
                );
                CREATE TABLE IF NOT EXISTS mcp_patch_acceptances (
                    action_id TEXT PRIMARY KEY REFERENCES actions(action_id),
                    owner_id TEXT NOT NULL,
                    principal_id TEXT NOT NULL REFERENCES oauth_principals(principal_id),
                    decision TEXT NOT NULL CHECK(decision IN ('accepted', 'rejected')),
                    decided_by TEXT NOT NULL,
                    decided_at_ms INTEGER NOT NULL,
                    note TEXT NOT NULL DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS actions_node_delivery_idx
                    ON actions(device_id, delivery_state, expires_at_ms);
                CREATE INDEX IF NOT EXISTS receipts_action_idx ON receipts(action_id, received_at_ms);
                CREATE INDEX IF NOT EXISTS mcp_read_only_intents_action_idx
                    ON mcp_read_only_intents(action_id);
                CREATE INDEX IF NOT EXISTS mcp_file_read_intents_action_idx
                    ON mcp_file_read_intents(action_id);
                CREATE INDEX IF NOT EXISTS mcp_file_read_intents_owner_principal_idx
                    ON mcp_file_read_intents(owner_id, principal_id, created_at_ms);
                CREATE INDEX IF NOT EXISTS mcp_permission_requests_owner_state_idx
                    ON mcp_permission_requests(owner_id, state, created_at_ms);
                CREATE INDEX IF NOT EXISTS mcp_permission_requests_binding_idx
                    ON mcp_permission_requests(binding_id, expires_at_ms);
                CREATE INDEX IF NOT EXISTS mcp_approved_patch_intents_action_idx
                    ON mcp_approved_patch_intents(action_id);
                CREATE INDEX IF NOT EXISTS mcp_approved_patch_intents_owner_principal_idx
                    ON mcp_approved_patch_intents(owner_id, principal_id, created_at_ms);
                CREATE INDEX IF NOT EXISTS mcp_access_grants_context_idx
                    ON mcp_access_grants(context_id, expires_at_ms);
                CREATE INDEX IF NOT EXISTS oauth_principals_owner_idx
                    ON oauth_principals(owner_id, revoked_at_ms, created_at_ms);
                CREATE INDEX IF NOT EXISTS oauth_link_requests_owner_state_idx
                    ON oauth_link_requests(owner_id, state, requested_at_ms);
                CREATE INDEX IF NOT EXISTS node_workspaces_current_idx
                    ON node_workspaces(device_id, workspace_id, retired_at_ms);
                CREATE INDEX IF NOT EXISTS action_reconciliations_owner_device_idx
                    ON action_reconciliations(owner_id, device_id, reconciled_at_ms);
                CREATE INDEX IF NOT EXISTS mcp_task_sessions_owner_principal_idx
                    ON mcp_task_sessions(owner_id, principal_id, created_at_ms);
                CREATE INDEX IF NOT EXISTS mcp_task_sessions_binding_idx
                    ON mcp_task_sessions(binding_id, expires_at_ms);
                CREATE INDEX IF NOT EXISTS mcp_task_action_links_action_idx
                    ON mcp_task_action_links(action_id);
                CREATE INDEX IF NOT EXISTS mcp_exec_intents_action_idx
                    ON mcp_exec_intents(action_id);
                CREATE INDEX IF NOT EXISTS mcp_exec_intents_owner_principal_idx
                    ON mcp_exec_intents(owner_id, principal_id, created_at_ms);
                CREATE INDEX IF NOT EXISTS mcp_artifact_intents_action_idx
                    ON mcp_artifact_intents(action_id);
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
                permission_columns = {
                    str(row["name"])
                    for row in connection.execute("PRAGMA table_info(mcp_permission_requests)").fetchall()
                }
                if "task_id" not in permission_columns:
                    connection.execute("ALTER TABLE mcp_permission_requests ADD COLUMN task_id TEXT")
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

    @staticmethod
    def _oauth_principal_projection(row: sqlite3.Row) -> dict[str, Any]:
        """Return no IdP subject, issuer, token, or credential material."""

        return {
            "principal_id": row["principal_id"],
            "owner_id": row["owner_id"],
            "created_at_ms": row["created_at_ms"],
            "revoked_at_ms": row["revoked_at_ms"],
            "state": "revoked" if row["revoked_at_ms"] is not None else "enabled",
        }

    @staticmethod
    def _oauth_link_request_projection(row: sqlite3.Row) -> dict[str, Any]:
        """Return an opaque account-link request for the owner Console.

        The pending request proves only that a verified OAuth identity asked to
        be linked to this control plane.  It intentionally omits its issuer,
        subject, digest, token, client address and any workspace information.
        The opaque request ID is sufficient for an authenticated owner to make
        an explicit approval or rejection decision.
        """

        return {
            "link_request_id": row["link_request_id"],
            "state": row["state"],
            "requested_at_ms": row["requested_at_ms"],
            "decided_at_ms": row["decided_at_ms"],
            "principal_id": row["principal_id"],
        }

    def _approve_pending_oauth_link_request(
        self,
        connection: sqlite3.Connection,
        *,
        owner_id: str,
        issuer: str,
        subject_digest: str,
        principal_id: str,
        decided_at_ms: int,
        allow_rejected: bool = False,
    ) -> None:
        """Attach a matching local request without projecting IdP identity.

        ``link_oauth_principal`` is retained as a private recovery/bootstrap
        route.  If it is used after the normal OAuth request was recorded, the
        durable request must not remain falsely pending.  A direct operator
        relink is an explicit decision, so it may supersede a prior rejection;
        the ordinary Console approval path never does.
        """

        request = connection.execute(
            """
            SELECT link_request_id, state
            FROM oauth_link_requests
            WHERE owner_id = ? AND issuer = ? AND subject_digest = ?
            """,
            (owner_id, issuer, subject_digest),
        ).fetchone()
        if request is None or (
            request["state"] != "pending"
            and not (allow_rejected and request["state"] == "rejected")
        ):
            return
        connection.execute(
            """
            UPDATE oauth_link_requests
            SET state = 'approved', decided_at_ms = ?, decided_by = ?, principal_id = ?
            WHERE link_request_id = ?
            """,
            (decided_at_ms, owner_id, principal_id, request["link_request_id"]),
        )
        self._event(
            connection,
            "oauth_link_request",
            request["link_request_id"],
            "oauth_link_request_approved",
            {"principal_id": principal_id},
        )

    def link_oauth_principal(self, *, owner_id: str, issuer: str, subject: str) -> dict[str, Any]:
        """Explicitly associate one verified IdP account with the current owner.

        This is a private operator/bootstrap operation. An otherwise-valid
        OAuth token can never infer this association or acquire the default
        owner merely by presenting a matching-looking email/claim.
        """

        owner_id = _text(owner_id, "owner_id")
        issuer = _oauth_issuer(issuer)
        subject = _oauth_subject(subject)
        subject_digest = _oauth_subject_digest(issuer=issuer, subject=subject)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM oauth_principals WHERE issuer = ? AND subject_digest = ?",
                (issuer, subject_digest),
            ).fetchone()
            if row is not None:
                if row["owner_id"] != owner_id:
                    connection.execute("ROLLBACK")
                    raise PermissionError("OAuth principal is already owned by another account.")
                if row["revoked_at_ms"] is not None:
                    now = self.clock()
                    connection.execute(
                        "UPDATE oauth_principals SET revoked_at_ms = NULL WHERE principal_id = ?",
                        (row["principal_id"],),
                    )
                    self._event(connection, "oauth_principal", row["principal_id"], "oauth_principal_relinked", {})
                    row = connection.execute(
                        "SELECT * FROM oauth_principals WHERE principal_id = ?",
                        (row["principal_id"],),
                    ).fetchone()
                else:
                    now = self.clock()
                self._approve_pending_oauth_link_request(
                    connection,
                    owner_id=owner_id,
                    issuer=issuer,
                    subject_digest=subject_digest,
                    principal_id=str(row["principal_id"]),
                    decided_at_ms=now,
                    allow_rejected=True,
                )
                connection.execute("COMMIT")
                return self._oauth_principal_projection(row)
            principal_id = f"oauthprn_{uuid.uuid4().hex}"
            now = self.clock()
            connection.execute(
                """
                INSERT INTO oauth_principals(
                    principal_id, owner_id, issuer, subject_digest, created_at_ms, revoked_at_ms
                ) VALUES (?, ?, ?, ?, ?, NULL)
                """,
                (principal_id, owner_id, issuer, subject_digest, now),
            )
            self._event(connection, "oauth_principal", principal_id, "oauth_principal_linked", {})
            row = connection.execute(
                "SELECT * FROM oauth_principals WHERE principal_id = ?",
                (principal_id,),
            ).fetchone()
            self._approve_pending_oauth_link_request(
                connection,
                owner_id=owner_id,
                issuer=issuer,
                subject_digest=subject_digest,
                principal_id=principal_id,
                decided_at_ms=now,
                allow_rejected=True,
            )
            connection.execute("COMMIT")
        return self._oauth_principal_projection(row)

    def resolve_or_request_oauth_principal(
        self,
        *,
        owner_id: str,
        issuer: str,
        subject: str,
    ) -> dict[str, Any]:
        """Resolve an enabled OAuth principal or record one opaque link request.

        The intended owner comes from the server's fixed control-plane scope,
        never from an OAuth claim or MCP arguments.  A valid but unmapped
        identity creates at most one durable pending request.  It receives no
        workspace, context or principal authority until the owner explicitly
        approves that request.  Rejected, revoked and foreign identities do
        not recreate requests or disclose who owns a matching account.
        """

        owner_id = _text(owner_id, "owner_id")
        issuer = _oauth_issuer(issuer)
        subject = _oauth_subject(subject)
        subject_digest = _oauth_subject_digest(issuer=issuer, subject=subject)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                principal = connection.execute(
                    """
                    SELECT principal_id, owner_id, revoked_at_ms
                    FROM oauth_principals
                    WHERE issuer = ? AND subject_digest = ?
                    """,
                    (issuer, subject_digest),
                ).fetchone()
                if principal is not None:
                    if principal["owner_id"] == owner_id and principal["revoked_at_ms"] is None:
                        result: dict[str, Any] = {
                            "state": "linked",
                            "principal_id": str(principal["principal_id"]),
                            "owner_id": owner_id,
                        }
                    elif principal["owner_id"] == owner_id:
                        result = {"state": "revoked"}
                    else:
                        result = {"state": "not_authorized"}
                    connection.execute("COMMIT")
                    return result

                request = connection.execute(
                    """
                    SELECT * FROM oauth_link_requests
                    WHERE issuer = ? AND subject_digest = ?
                    """,
                    (issuer, subject_digest),
                ).fetchone()
                if request is None:
                    now = self.clock()
                    link_request_id = f"oauthlink_{uuid.uuid4().hex}"
                    connection.execute(
                        """
                        INSERT INTO oauth_link_requests(
                            link_request_id, owner_id, issuer, subject_digest,
                            requested_at_ms, state, decided_at_ms, decided_by, principal_id
                        ) VALUES (?, ?, ?, ?, ?, 'pending', NULL, NULL, NULL)
                        """,
                        (link_request_id, owner_id, issuer, subject_digest, now),
                    )
                    self._event(connection, "oauth_link_request", link_request_id, "oauth_link_request_created", {})
                    request = connection.execute(
                        "SELECT * FROM oauth_link_requests WHERE link_request_id = ?",
                        (link_request_id,),
                    ).fetchone()
                if request is None:
                    raise RuntimeError("OAuth link request was not persisted.")
                if request["owner_id"] != owner_id:
                    result = {"state": "not_authorized"}
                elif request["state"] == "pending":
                    result = {"state": "pending", "link_request": self._oauth_link_request_projection(request)}
                else:
                    result = {"state": "not_authorized"}
                connection.execute("COMMIT")
                return result
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def list_oauth_link_requests(self, *, owner_id: str) -> list[dict[str, Any]]:
        """List the owner's opaque OAuth account-link requests only."""

        owner_id = _text(owner_id, "owner_id")
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM oauth_link_requests
                WHERE owner_id = ?
                ORDER BY CASE state WHEN 'pending' THEN 0 ELSE 1 END, requested_at_ms DESC, link_request_id
                """,
                (owner_id,),
            ).fetchall()
        return [self._oauth_link_request_projection(row) for row in rows]

    def approve_oauth_link_request(self, *, owner_id: str, link_request_id: str) -> dict[str, Any]:
        """Explicitly link one pending verified OAuth identity to this owner."""

        owner_id = _text(owner_id, "owner_id")
        link_request_id = _text(link_request_id, "link_request_id")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                request = connection.execute(
                    "SELECT * FROM oauth_link_requests WHERE link_request_id = ?",
                    (link_request_id,),
                ).fetchone()
                if request is None:
                    raise NotFoundError("OAuth account-link request does not exist.")
                if request["owner_id"] != owner_id:
                    raise PermissionError("OAuth account-link request is not owned by this operator.")
                if request["state"] == "rejected":
                    raise ConflictError("OAuth account-link request was rejected.")
                if request["state"] == "approved":
                    # Approval is idempotent only for the link request.  A
                    # later explicit principal revocation must never be
                    # silently undone by clicking/retrying this endpoint.
                    principal = connection.execute(
                        "SELECT * FROM oauth_principals WHERE principal_id = ?",
                        (request["principal_id"],),
                    ).fetchone()
                    if principal is None:
                        raise RuntimeError("approved OAuth link request has no principal.")
                    if principal["owner_id"] != owner_id:
                        raise PermissionError("OAuth principal is already owned by another account.")
                    connection.execute("COMMIT")
                    return {
                        "link_request": self._oauth_link_request_projection(request),
                        "principal": self._oauth_principal_projection(principal),
                    }

                principal = connection.execute(
                    "SELECT * FROM oauth_principals WHERE issuer = ? AND subject_digest = ?",
                    (request["issuer"], request["subject_digest"]),
                ).fetchone()
                now = self.clock()
                if principal is None:
                    principal_id = f"oauthprn_{uuid.uuid4().hex}"
                    connection.execute(
                        """
                        INSERT INTO oauth_principals(
                            principal_id, owner_id, issuer, subject_digest, created_at_ms, revoked_at_ms
                        ) VALUES (?, ?, ?, ?, ?, NULL)
                        """,
                        (principal_id, owner_id, request["issuer"], request["subject_digest"], now),
                    )
                    self._event(connection, "oauth_principal", principal_id, "oauth_principal_linked", {})
                    principal = connection.execute(
                        "SELECT * FROM oauth_principals WHERE principal_id = ?",
                        (principal_id,),
                    ).fetchone()
                elif principal["owner_id"] != owner_id:
                    raise PermissionError("OAuth principal is already owned by another account.")
                elif principal["revoked_at_ms"] is not None:
                    connection.execute(
                        "UPDATE oauth_principals SET revoked_at_ms = NULL WHERE principal_id = ?",
                        (principal["principal_id"],),
                    )
                    self._event(connection, "oauth_principal", principal["principal_id"], "oauth_principal_relinked", {})
                    principal = connection.execute(
                        "SELECT * FROM oauth_principals WHERE principal_id = ?",
                        (principal["principal_id"],),
                    ).fetchone()
                if principal is None:
                    raise RuntimeError("OAuth principal was not persisted.")

                self._approve_pending_oauth_link_request(
                    connection,
                    owner_id=owner_id,
                    issuer=str(request["issuer"]),
                    subject_digest=str(request["subject_digest"]),
                    principal_id=str(principal["principal_id"]),
                    decided_at_ms=now,
                )
                request = connection.execute(
                    "SELECT * FROM oauth_link_requests WHERE link_request_id = ?",
                    (link_request_id,),
                ).fetchone()
                if request is None:
                    raise RuntimeError("OAuth link request disappeared during approval.")
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return {
            "link_request": self._oauth_link_request_projection(request),
            "principal": self._oauth_principal_projection(principal),
        }

    def reject_oauth_link_request(self, *, owner_id: str, link_request_id: str) -> dict[str, Any]:
        """Reject one pending OAuth link without creating any account authority."""

        owner_id = _text(owner_id, "owner_id")
        link_request_id = _text(link_request_id, "link_request_id")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                request = connection.execute(
                    "SELECT * FROM oauth_link_requests WHERE link_request_id = ?",
                    (link_request_id,),
                ).fetchone()
                if request is None:
                    raise NotFoundError("OAuth account-link request does not exist.")
                if request["owner_id"] != owner_id:
                    raise PermissionError("OAuth account-link request is not owned by this operator.")
                if request["state"] == "approved":
                    raise ConflictError("OAuth account-link request was already approved.")
                if request["state"] == "pending":
                    now = self.clock()
                    connection.execute(
                        """
                        UPDATE oauth_link_requests
                        SET state = 'rejected', decided_at_ms = ?, decided_by = ?, principal_id = NULL
                        WHERE link_request_id = ?
                        """,
                        (now, owner_id, link_request_id),
                    )
                    self._event(connection, "oauth_link_request", link_request_id, "oauth_link_request_rejected", {})
                    request = connection.execute(
                        "SELECT * FROM oauth_link_requests WHERE link_request_id = ?",
                        (link_request_id,),
                    ).fetchone()
                if request is None:
                    raise RuntimeError("OAuth link request disappeared during rejection.")
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return self._oauth_link_request_projection(request)

    def resolve_oauth_principal(self, *, issuer: str, subject: str) -> dict[str, str]:
        """Resolve an already-linked verified account without exposing its claims."""

        issuer = _oauth_issuer(issuer)
        subject = _oauth_subject(subject)
        subject_digest = _oauth_subject_digest(issuer=issuer, subject=subject)
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT principal_id, owner_id, revoked_at_ms
                FROM oauth_principals
                WHERE issuer = ? AND subject_digest = ?
                """,
                (issuer, subject_digest),
            ).fetchone()
        if row is None or row["revoked_at_ms"] is not None:
            # A valid identity that was never shared (or was revoked) is an
            # authorization denial, not a reason to ask the client to login
            # again with the same account.
            raise PermissionError("authenticated OAuth account is not authorized for this control plane.")
        return {"principal_id": str(row["principal_id"]), "owner_id": str(row["owner_id"])}

    def list_oauth_principals(self, *, owner_id: str) -> list[dict[str, Any]]:
        """List the owner's redacted OAuth account links for revocation UI."""

        owner_id = _text(owner_id, "owner_id")
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM oauth_principals
                WHERE owner_id = ?
                ORDER BY created_at_ms, principal_id
                """,
                (owner_id,),
            ).fetchall()
        return [self._oauth_principal_projection(row) for row in rows]

    def revoke_oauth_principal(self, *, owner_id: str, principal_id: str) -> dict[str, Any]:
        """Block future OAuth requests without altering existing Job evidence."""

        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM oauth_principals WHERE principal_id = ?",
                (principal_id,),
            ).fetchone()
            if row is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("OAuth principal does not exist.")
            if row["owner_id"] != owner_id:
                connection.execute("ROLLBACK")
                raise PermissionError("OAuth principal is not owned by this account.")
            if row["revoked_at_ms"] is None:
                now = self.clock()
                connection.execute(
                    "UPDATE oauth_principals SET revoked_at_ms = ? WHERE principal_id = ?",
                    (now, principal_id),
                )
                self._event(connection, "oauth_principal", principal_id, "oauth_principal_revoked", {})
            row = connection.execute(
                "SELECT * FROM oauth_principals WHERE principal_id = ?",
                (principal_id,),
            ).fetchone()
            connection.execute("COMMIT")
        return self._oauth_principal_projection(row)

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

    @staticmethod
    def _workspace_registration_projection(row: sqlite3.Row, *, replayed: bool | None = None) -> dict[str, Any]:
        """Return credential-free registry metadata without any local path."""

        try:
            capabilities = _workspace_capabilities(json.loads(str(row["capabilities_json"])))
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise RuntimeError("stored workspace capabilities are invalid.") from error
        result: dict[str, Any] = {
            "device_id": row["device_id"],
            "workspace_id": row["workspace_id"],
            "workspace_generation": row["workspace_generation"],
            "display_name": row["display_name"],
            "capabilities": capabilities,
            "registered_at_ms": row["registered_at_ms"],
            "retired_at_ms": row["retired_at_ms"],
        }
        if replayed is not None:
            result["replayed"] = replayed
        return result

    def _retire_workspace_generation(
        self,
        connection: sqlite3.Connection,
        *,
        device_id: str,
        workspace_id: str,
        workspace_generation: str,
        reason: str,
        now: int,
    ) -> int:
        """Fence an old locally registered root without rewriting its history.

        A binding/context contains the workspace generation it was issued for.
        Reusing a stable workspace id after a local root change must therefore
        retire that generation, close its still-live contexts, and settle only
        actions that were never sent.  Sent actions remain durable evidence for
        the ordinary receipt/reconciliation path.
        """

        connection.execute(
            """
            UPDATE node_workspaces
            SET retired_at_ms = ?
            WHERE device_id = ? AND workspace_id = ? AND workspace_generation = ?
              AND retired_at_ms IS NULL
            """,
            (now, device_id, workspace_id, workspace_generation),
        )
        binding_rows = connection.execute(
            """
            SELECT binding_id FROM bindings
            WHERE device_id = ? AND workspace_id = ? AND workspace_generation = ?
              AND revoked_at_ms IS NULL
            """,
            (device_id, workspace_id, workspace_generation),
        ).fetchall()
        refused = 0
        for binding_row in binding_rows:
            binding_id = str(binding_row["binding_id"])
            connection.execute(
                "UPDATE bindings SET revoked_at_ms = ? WHERE binding_id = ? AND revoked_at_ms IS NULL",
                (now, binding_id),
            )
            connection.execute(
                "UPDATE contexts SET closed_at_ms = ? WHERE binding_id = ? AND closed_at_ms IS NULL",
                (now, binding_id),
            )
            refused += self._refuse_queued_actions(
                connection,
                action_column="binding_id",
                subject_id=binding_id,
                reason=reason,
                now=now,
            )
        return refused

    def register_node_workspace(
        self,
        *,
        device_id: str,
        workspace_id: str,
        workspace_generation: str,
        display_name: str,
        capabilities: dict[str, Any],
    ) -> dict[str, Any]:
        """Register one opaque, locally selected workspace from its node.

        The central record has no filesystem path or path hash.  A node chooses
        and canonicalizes the local directory before this boundary, then sends
        only its opaque identity, generation, display label and capability
        inventory.  This method does not create a binding, context, policy or
        task authority.
        """

        device_id = _text(device_id, "device_id")
        workspace_id = _text(workspace_id, "workspace_id")
        workspace_generation = _text(workspace_generation, "workspace_generation")
        display_name = str(display_name or "").strip()
        if not 1 <= len(display_name) <= 120:
            raise ValidationError("workspace display_name is invalid.")
        normalized_capabilities = _workspace_capabilities(capabilities)
        capabilities_json = _canonical_json(normalized_capabilities)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            node = connection.execute(
                "SELECT device_id, revoked_at_ms FROM nodes WHERE device_id = ?",
                (device_id,),
            ).fetchone()
            if node is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("device is not enrolled.")
            if node["revoked_at_ms"] is not None:
                connection.execute("ROLLBACK")
                raise ConflictError("node is revoked.")
            exact = connection.execute(
                """
                SELECT * FROM node_workspaces
                WHERE device_id = ? AND workspace_id = ? AND workspace_generation = ?
                """,
                (device_id, workspace_id, workspace_generation),
            ).fetchone()
            if exact is not None:
                if exact["retired_at_ms"] is not None:
                    connection.execute("ROLLBACK")
                    raise ConflictError("workspace generation is retired.")
                if exact["display_name"] != display_name or exact["capabilities_json"] != capabilities_json:
                    connection.execute("ROLLBACK")
                    raise ConflictError("workspace generation does not match registered inventory.")
                connection.execute("COMMIT")
                return self._workspace_registration_projection(exact, replayed=True)
            now = self.clock()
            current = connection.execute(
                """
                SELECT * FROM node_workspaces
                WHERE device_id = ? AND workspace_id = ? AND retired_at_ms IS NULL
                """,
                (device_id, workspace_id),
            ).fetchone()
            refused = 0
            if current is not None:
                refused = self._retire_workspace_generation(
                    connection,
                    device_id=device_id,
                    workspace_id=workspace_id,
                    workspace_generation=str(current["workspace_generation"]),
                    reason="workspace_generation_replaced",
                    now=now,
                )
            connection.execute(
                """
                INSERT INTO node_workspaces(
                    device_id, workspace_id, workspace_generation, display_name,
                    capabilities_json, registered_at_ms, retired_at_ms
                ) VALUES (?, ?, ?, ?, ?, ?, NULL)
                """,
                (device_id, workspace_id, workspace_generation, display_name, capabilities_json, now),
            )
            self._event(
                connection,
                "workspace",
                f"{device_id}:{workspace_id}:{workspace_generation}",
                "node_workspace_registered",
                {
                    "device_id": device_id,
                    "workspace_id": workspace_id,
                    "workspace_generation": workspace_generation,
                    "queued_actions_refused": refused,
                },
            )
            row = connection.execute(
                """
                SELECT * FROM node_workspaces
                WHERE device_id = ? AND workspace_id = ? AND workspace_generation = ?
                """,
                (device_id, workspace_id, workspace_generation),
            ).fetchone()
            connection.execute("COMMIT")
        return self._workspace_registration_projection(row, replayed=False)

    def retire_node_workspace(
        self,
        *,
        device_id: str,
        workspace_id: str,
        workspace_generation: str,
    ) -> dict[str, Any]:
        """Retire an exact node-owned workspace generation without deleting it."""

        device_id = _text(device_id, "device_id")
        workspace_id = _text(workspace_id, "workspace_id")
        workspace_generation = _text(workspace_generation, "workspace_generation")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            node = connection.execute(
                "SELECT device_id, revoked_at_ms FROM nodes WHERE device_id = ?",
                (device_id,),
            ).fetchone()
            if node is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("device is not enrolled.")
            if node["revoked_at_ms"] is not None:
                connection.execute("ROLLBACK")
                raise ConflictError("node is revoked.")
            row = connection.execute(
                """
                SELECT * FROM node_workspaces
                WHERE device_id = ? AND workspace_id = ? AND workspace_generation = ?
                """,
                (device_id, workspace_id, workspace_generation),
            ).fetchone()
            if row is None:
                connection.execute("ROLLBACK")
                raise NotFoundError("workspace registration does not exist.")
            if row["retired_at_ms"] is not None:
                connection.execute("COMMIT")
                return self._workspace_registration_projection(row, replayed=True)
            now = self.clock()
            refused = self._retire_workspace_generation(
                connection,
                device_id=device_id,
                workspace_id=workspace_id,
                workspace_generation=workspace_generation,
                reason="workspace_retired",
                now=now,
            )
            self._event(
                connection,
                "workspace",
                f"{device_id}:{workspace_id}:{workspace_generation}",
                "node_workspace_retired",
                {
                    "device_id": device_id,
                    "workspace_id": workspace_id,
                    "workspace_generation": workspace_generation,
                    "queued_actions_refused": refused,
                },
            )
            row = connection.execute(
                """
                SELECT * FROM node_workspaces
                WHERE device_id = ? AND workspace_id = ? AND workspace_generation = ?
                """,
                (device_id, workspace_id, workspace_generation),
            ).fetchone()
            connection.execute("COMMIT")
        return self._workspace_registration_projection(row, replayed=False)

    def list_node_workspaces(self, *, owner_id: str, device_id: str) -> list[dict[str, Any]]:
        """List the owner-scoped, path-free workspace inventory for one node."""

        owner_id = _text(owner_id, "owner_id")
        device_id = _text(device_id, "device_id")
        with self._connection() as connection:
            node = connection.execute(
                "SELECT owner_id FROM nodes WHERE device_id = ?",
                (device_id,),
            ).fetchone()
            if node is None:
                raise NotFoundError("device is not enrolled.")
            if node["owner_id"] != owner_id:
                raise PermissionError("node is not owned by this principal.")
            rows = connection.execute(
                f"""
                SELECT * FROM node_workspaces
                WHERE device_id = ?
                ORDER BY registered_at_ms, workspace_id, workspace_generation
                """,
                (device_id,),
            ).fetchall()
        return [self._workspace_registration_projection(row) for row in rows]

    @staticmethod
    def _require_current_workspace_registration(
        connection: sqlite3.Connection,
        *,
        device_id: str,
        workspace_id: str,
        workspace_generation: str,
    ) -> sqlite3.Row:
        """Require the exact node-confirmed root generation for new authority.

        Bindings and contexts are durable history, but they must not be a way
        to recreate authority for an unregistered or retired local root.  The
        registry is node-owned and path-free; this check compares only its
        opaque identity/generation inside the same SQLite transaction that
        creates the next authority record.
        """

        row = connection.execute(
            """
            SELECT * FROM node_workspaces
            WHERE device_id = ? AND workspace_id = ? AND workspace_generation = ?
              AND retired_at_ms IS NULL
            """,
            (device_id, workspace_id, workspace_generation),
        ).fetchone()
        if row is None:
            raise ConflictError("workspace registration is not current.")
        return row

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
            self._require_current_workspace_registration(
                connection,
                device_id=device_id,
                workspace_id=workspace_id,
                workspace_generation=workspace_generation,
            )
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

    def list_account_targets(self, *, owner_id: str) -> list[dict[str, Any]]:
        """List only currently shared, path-free targets for an OAuth account.

        An account connection is deliberately independent of a short-lived
        task context. This inventory does not create a context, policy, grant,
        or action and excludes bindings whose node/root generation is no longer
        current.
        """

        owner_id = _text(owner_id, "owner_id")
        with self._connection() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    b.binding_id, b.device_id, b.endpoint_id, b.workspace_id,
                    b.workspace_generation, b.display_name AS workspace_display_name,
                    b.created_at_ms AS binding_created_at_ms,
                    n.display_name AS node_display_name, n.last_seen_at_ms,
                    n.readiness, n.contract_version, n.policy_state,
                    n.policy_expires_at_ms, n.policy_observed_at_ms,
                    nw.capabilities_json, nw.registered_at_ms
                FROM bindings AS b
                JOIN nodes AS n ON n.device_id = b.device_id
                JOIN node_workspaces AS nw
                  ON nw.device_id = b.device_id
                 AND nw.workspace_id = b.workspace_id
                 AND nw.workspace_generation = b.workspace_generation
                 AND nw.retired_at_ms IS NULL
                WHERE b.owner_id = ?
                  AND b.revoked_at_ms IS NULL
                  AND n.owner_id = ?
                  AND n.revoked_at_ms IS NULL
                ORDER BY b.created_at_ms, b.binding_id
                """,
                (owner_id, owner_id),
            ).fetchall()
        targets: list[dict[str, Any]] = []
        for row in rows:
            try:
                capabilities = _workspace_capabilities(json.loads(str(row["capabilities_json"])))
            except (TypeError, ValueError, json.JSONDecodeError) as error:
                raise RuntimeError("stored workspace capabilities are invalid.") from error
            targets.append(
                {
                    "binding_id": row["binding_id"],
                    "device_id": row["device_id"],
                    "endpoint_id": row["endpoint_id"],
                    "node_display_name": row["node_display_name"],
                    "workspace_id": row["workspace_id"],
                    "workspace_generation": row["workspace_generation"],
                    "workspace_display_name": row["workspace_display_name"],
                    "capabilities": capabilities,
                    "binding_created_at_ms": row["binding_created_at_ms"],
                    "workspace_registered_at_ms": row["registered_at_ms"],
                    "last_seen_at_ms": row["last_seen_at_ms"],
                    "readiness": row["readiness"],
                    "contract_version": row["contract_version"],
                    "policy_state": row["policy_state"],
                    "policy_expires_at_ms": row["policy_expires_at_ms"],
                    "policy_observed_at_ms": row["policy_observed_at_ms"],
                }
            )
        return targets

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

    def _task_label(self, value: Any) -> str:
        if not isinstance(value, str):
            raise ValidationError("task label is invalid.")
        label = value.strip()
        if not 1 <= len(label.encode("utf-8")) <= 240 or any(ord(c) < 32 or ord(c) == 127 for c in label):
            raise ValidationError("task label is invalid.")
        return label

    def _require_live_mcp_task(
        self,
        connection: sqlite3.Connection,
        *,
        owner_id: str,
        principal_id: str,
        task_id: str,
        binding_id: str | None = None,
    ) -> sqlite3.Row:
        """Validate one durable task handle inside a write transaction.

        The task pins an immutable node/workspace/generation snapshot at
        creation. Every follow-up read/patch/exec call must present the same
        task handle; the store revalidates owner/principal, open state,
        expiry, binding revocation and workspace-generation currency. A
        caller-supplied chat_id is never trusted as a task selector.
        """
        if not isinstance(task_id, str) or TASK_ID_PATTERN.fullmatch(task_id) is None:
            raise ValidationError("task_id is invalid.")
        task = connection.execute(
            "SELECT * FROM mcp_task_sessions WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        if task is None:
            raise NotFoundError("task does not exist.")
        if task["owner_id"] != owner_id or task["principal_id"] != principal_id:
            raise PermissionError("task is not owned by this OAuth account.")
        if task["closed_at_ms"] is not None:
            raise ConflictError("task is closed.")
        now = self.clock()
        if int(task["expires_at_ms"]) <= now:
            raise ConflictError("task is expired.")
        if binding_id is not None and binding_id != task["binding_id"]:
            raise ConflictError("task is bound to a different workspace target.")
        live = connection.execute(
            """
            SELECT b.revoked_at_ms AS binding_revoked_at_ms,
                   n.revoked_at_ms AS node_revoked_at_ms,
                   n.endpoint_id AS node_endpoint_id,
                   nw.retired_at_ms AS workspace_retired_at_ms
            FROM bindings AS b
            JOIN nodes AS n ON n.device_id = b.device_id
            JOIN node_workspaces AS nw
              ON nw.device_id = b.device_id
             AND nw.workspace_id = b.workspace_id
             AND nw.workspace_generation = b.workspace_generation
            WHERE b.binding_id = ?
            """,
            (task["binding_id"],),
        ).fetchone()
        if live is None:
            raise ConflictError("task target is no longer registered.")
        if (
            live["binding_revoked_at_ms"] is not None
            or live["node_revoked_at_ms"] is not None
            or live["workspace_retired_at_ms"] is not None
        ):
            raise ConflictError("task target was revoked or retired.")
        if str(task["endpoint_id"]) != str(live["node_endpoint_id"]):
            raise ConflictError("task target endpoint changed.")
        self._require_current_workspace_registration(
            connection,
            device_id=str(task["device_id"]),
            workspace_id=str(task["workspace_id"]),
            workspace_generation=str(task["workspace_generation"]),
        )
        return task

    def create_mcp_task_session(
        self,
        *,
        owner_id: str,
        principal_id: str,
        binding_id: str,
        label: Any,
        ttl_ms: int | None = None,
    ) -> dict[str, Any]:
        """Open one durable multi-call task pinned to an explicit binding.

        The task handle is server-issued and opaque. It survives individual
        context/action expiry so a task can span read -> patch -> test ->
        observe calls. The target triple is immutable: closing the UI
        selection or opening a second chat/task never retargets this task.
        """
        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        binding_id = _text(binding_id, "binding_id")
        label = self._task_label(label)
        if ttl_ms is None:
            ttl_ms = MCP_TASK_SESSION_MAX_TTL_MS
        if not isinstance(ttl_ms, int) or isinstance(ttl_ms, bool) or not 60_000 <= ttl_ms <= MCP_TASK_SESSION_MAX_TTL_MS:
            raise ValidationError("task ttl is invalid.")
        task_id = f"task_{uuid.uuid4().hex}"
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                principal = connection.execute(
                    "SELECT owner_id, revoked_at_ms FROM oauth_principals WHERE principal_id = ?",
                    (principal_id,),
                ).fetchone()
                if principal is None or principal["owner_id"] != owner_id or principal["revoked_at_ms"] is not None:
                    raise PermissionError("authenticated OAuth account is not authorized for this control plane.")
                if self._admission_mode(connection) != "open":
                    raise ConflictError("central admission is in recovery mode.")
                live = connection.execute(
                    """
                    SELECT b.*, n.owner_id AS node_owner_id, n.endpoint_id AS node_endpoint_id,
                           n.revoked_at_ms AS node_revoked_at_ms,
                           nw.capabilities_json, nw.retired_at_ms AS workspace_retired_at_ms
                    FROM bindings AS b
                    JOIN nodes AS n ON n.device_id = b.device_id
                    JOIN node_workspaces AS nw
                      ON nw.device_id = b.device_id
                     AND nw.workspace_id = b.workspace_id
                     AND nw.workspace_generation = b.workspace_generation
                    WHERE b.binding_id = ?
                    """,
                    (binding_id,),
                ).fetchone()
                if live is None:
                    raise NotFoundError("binding does not exist.")
                if live["owner_id"] != owner_id or live["node_owner_id"] != owner_id:
                    raise PermissionError("binding is not owned by this OAuth account.")
                if (
                    live["revoked_at_ms"] is not None
                    or live["node_revoked_at_ms"] is not None
                    or live["workspace_retired_at_ms"] is not None
                    or live["node_endpoint_id"] != live["endpoint_id"]
                ):
                    raise ConflictError("selected binding is no longer dispatchable.")
                self._require_current_workspace_registration(
                    connection,
                    device_id=str(live["device_id"]),
                    workspace_id=str(live["workspace_id"]),
                    workspace_generation=str(live["workspace_generation"]),
                )
                now = self.clock()
                connection.execute(
                    """
                    INSERT INTO mcp_task_sessions(
                        task_id, owner_id, principal_id, binding_id, device_id,
                        endpoint_id, workspace_id, workspace_generation, label,
                        created_at_ms, expires_at_ms, closed_at_ms, close_reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)
                    """,
                    (
                        task_id, owner_id, principal_id, binding_id,
                        live["device_id"], live["endpoint_id"],
                        live["workspace_id"], live["workspace_generation"],
                        label, now, now + ttl_ms,
                    ),
                )
                self._event(connection, "mcp_task_session", task_id, "mcp_task_session_created", {"binding_id": binding_id})
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return self.mcp_task_session(owner_id=owner_id, principal_id=principal_id, task_id=task_id)

    def mcp_task_session(self, *, owner_id: str, principal_id: str, task_id: str) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        if not isinstance(task_id, str) or TASK_ID_PATTERN.fullmatch(task_id) is None:
            raise ValidationError("task_id is invalid.")
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM mcp_task_sessions WHERE task_id = ?", (task_id,)).fetchone()
        if row is None:
            raise NotFoundError("task does not exist.")
        if row["owner_id"] != owner_id or row["principal_id"] != principal_id:
            raise PermissionError("task is not owned by this OAuth account.")
        return _row(row) or {}

    def list_mcp_task_sessions(self, *, owner_id: str, principal_id: str | None = None) -> list[dict[str, Any]]:
        owner_id = _text(owner_id, "owner_id")
        with self._connection() as connection:
            if principal_id is None:
                rows = connection.execute(
                    "SELECT * FROM mcp_task_sessions WHERE owner_id = ? ORDER BY created_at_ms, task_id",
                    (owner_id,),
                ).fetchall()
            else:
                principal_id = _text(principal_id, "principal_id")
                rows = connection.execute(
                    "SELECT * FROM mcp_task_sessions WHERE owner_id = ? AND principal_id = ? ORDER BY created_at_ms, task_id",
                    (owner_id, principal_id),
                ).fetchall()
        return [dict(row) for row in rows]

    def close_mcp_task_session(
        self, *, owner_id: str, principal_id: str, task_id: str, reason: Any = "owner_closed"
    ) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        if not isinstance(task_id, str) or TASK_ID_PATTERN.fullmatch(task_id) is None:
            raise ValidationError("task_id is invalid.")
        if not isinstance(reason, str) or not reason.strip():
            raise ValidationError("close reason is invalid.")
        reason = reason.strip()[:64]
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute("SELECT * FROM mcp_task_sessions WHERE task_id = ?", (task_id,)).fetchone()
                if row is None:
                    raise NotFoundError("task does not exist.")
                if row["owner_id"] != owner_id or row["principal_id"] != principal_id:
                    raise PermissionError("task is not owned by this OAuth account.")
                if row["closed_at_ms"] is None:
                    now = self.clock()
                    connection.execute(
                        "UPDATE mcp_task_sessions SET closed_at_ms = ?, close_reason = ? WHERE task_id = ?",
                        (now, reason, task_id),
                    )
                    self._event(connection, "mcp_task_session", task_id, "mcp_task_session_closed", {"reason": reason})
                row = connection.execute("SELECT * FROM mcp_task_sessions WHERE task_id = ?", (task_id,)).fetchone()
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return _row(row) or {}

    def link_mcp_task_action(self, connection: sqlite3.Connection, *, task_id: str, action_id: str) -> None:
        connection.execute(
            "INSERT OR IGNORE INTO mcp_task_action_links(task_id, action_id, added_at_ms) VALUES (?, ?, ?)",
            (task_id, action_id, self.clock()),
        )

    def list_mcp_task_actions(self, *, owner_id: str, principal_id: str, task_id: str) -> list[dict[str, Any]]:
        task = self.mcp_task_session(owner_id=owner_id, principal_id=principal_id, task_id=task_id)
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT a.* FROM mcp_task_action_links AS l
                JOIN actions AS a ON a.action_id = l.action_id
                WHERE l.task_id = ? AND a.owner_id = ?
                ORDER BY a.created_at_ms, a.action_id
                """,
                (task["task_id"], owner_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def record_mcp_patch_acceptance(
        self, *, owner_id: str, principal_id: str, action_id: str, decision: Any, note: Any = "", decided_by: Any = "owner_console"
    ) -> dict[str, Any]:
        """Record local semantic acceptance for one verified applied patch.

        Acceptance is a human/controller verdict that the relayed postimage
        is satisfactory. Rejecting never reverts the Windows file; the owner
        must queue a corrective patch instead. Unknown-effect actions cannot
        be accepted until local reconciliation replaces UNKNOWN with a
        verified receipt.
        """
        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        action_id = _text(action_id, "action_id")
        if decision not in ("accepted", "rejected"):
            raise ValidationError("acceptance decision is invalid.")
        if not isinstance(note, str):
            raise ValidationError("acceptance note is invalid.")
        note = note.strip()[:500]
        if not isinstance(decided_by, str) or not 1 <= len(decided_by.strip()) <= 120:
            raise ValidationError("decided_by is invalid.")
        decided_by = decided_by.strip()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                principal = connection.execute(
                    "SELECT owner_id, revoked_at_ms FROM oauth_principals WHERE principal_id = ?",
                    (principal_id,),
                ).fetchone()
                if principal is None or principal["owner_id"] != owner_id or principal["revoked_at_ms"] is not None:
                    raise PermissionError("authenticated OAuth account is not authorized for this control plane.")
                action = connection.execute("SELECT * FROM actions WHERE action_id = ?", (action_id,)).fetchone()
                if action is None or action["owner_id"] != owner_id:
                    raise NotFoundError("action does not exist.")
                if action["tool_name"] != MCP_APPROVED_PATCH_TOOL_NAME:
                    raise ConflictError("only approved-patch actions carry local acceptance.")
                if action["delivery_state"] == "reconcile_required":
                    raise ConflictError("unknown-effect action requires local reconciliation before acceptance.")
                receipts = connection.execute(
                    "SELECT * FROM receipts WHERE action_id = ? ORDER BY received_at_ms DESC",
                    (action_id,),
                ).fetchall()
                if not any(r["receipt_state"] == "completed" for r in receipts):
                    raise ConflictError("patch has no verified completed receipt yet.")
                existing = connection.execute(
                    "SELECT * FROM mcp_patch_acceptances WHERE action_id = ?",
                    (action_id,),
                ).fetchone()
                if existing is not None:
                    if existing["decision"] != decision:
                        raise ConflictError("patch acceptance is already recorded.")
                    connection.execute("COMMIT")
                    return dict(existing)
                now = self.clock()
                connection.execute(
                    "INSERT INTO mcp_patch_acceptances(action_id, owner_id, principal_id, decision, decided_by, decided_at_ms, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (action_id, owner_id, principal_id, decision, decided_by, now, note),
                )
                self._event(connection, "action", action_id, f"mcp_patch_{decision}", {"decided_by": decided_by})
                row = connection.execute("SELECT * FROM mcp_patch_acceptances WHERE action_id = ?", (action_id,)).fetchone()
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return dict(row)

    def get_mcp_patch_acceptance(self, *, owner_id: str, action_id: str) -> dict[str, Any] | None:
        owner_id = _text(owner_id, "owner_id")
        action_id = _text(action_id, "action_id")
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM mcp_patch_acceptances WHERE action_id = ?", (action_id,)).fetchone()
        if row is None:
            return None
        if row["owner_id"] != owner_id:
            raise PermissionError("acceptance is not owned by this principal.")
        return dict(row)

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
        self._require_current_workspace_registration(
            connection,
            device_id=str(row["device_id"]),
            workspace_id=str(row["workspace_id"]),
            workspace_generation=str(row["workspace_generation"]),
        )
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

    def assigned_read_only_policy_context(
        self,
        *,
        device_id: str,
        workspace_id: str,
        workspace_generation: str,
    ) -> dict[str, Any]:
        """Resolve the one locally installable policy assignment for a node root.

        A Windows executor never receives a context identifier from its UI.
        The owner creates a normal short-lived context for an explicitly bound
        workspace in the Ubuntu Console; this lookup lets that exact node
        retrieve the resulting read-only policy template only after its local
        owner has selected the matching registered root.  Multiple live
        contexts are intentionally ambiguous rather than silently picking a
        "latest" authority window.

        The returned record is an internal server result.  HTTP callers must
        derive a policy template from it and must not expose ``context_id`` to
        the executor UI or a ChatGPT client.
        """

        device_id = _text(device_id, "device_id")
        workspace_id = _text(workspace_id, "workspace_id")
        workspace_generation = _text(workspace_generation, "workspace_generation")
        with self._connection() as connection:
            node = connection.execute(
                "SELECT device_id, owner_id, endpoint_id, revoked_at_ms FROM nodes WHERE device_id = ?",
                (device_id,),
            ).fetchone()
            if node is None:
                raise NotFoundError("device is not enrolled.")
            if node["revoked_at_ms"] is not None:
                raise ConflictError("node is revoked.")
            self._require_current_workspace_registration(
                connection,
                device_id=device_id,
                workspace_id=workspace_id,
                workspace_generation=workspace_generation,
            )
            rows = connection.execute(
                """
                SELECT c.*
                FROM contexts AS c
                JOIN bindings AS b ON b.binding_id = c.binding_id
                JOIN nodes AS n ON n.device_id = c.device_id
                WHERE c.device_id = ?
                  AND c.workspace_id = ?
                  AND c.workspace_generation = ?
                  AND c.closed_at_ms IS NULL
                  AND c.expires_at_ms > ?
                  AND b.revoked_at_ms IS NULL
                  AND n.revoked_at_ms IS NULL
                  AND c.owner_id = b.owner_id
                  AND b.owner_id = n.owner_id
                ORDER BY c.created_at_ms, c.context_id
                """,
                (device_id, workspace_id, workspace_generation, self.clock()),
            ).fetchall()
        if not rows:
            raise NotFoundError("no live read-only policy assignment exists for this workspace.")
        if len(rows) != 1:
            raise ConflictError("read-only policy assignment is ambiguous; close older contexts first.")
        return _row(rows[0]) or {}

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
            self._require_current_workspace_registration(
                connection,
                device_id=str(context["device_id"]),
                workspace_id=str(context["workspace_id"]),
                workspace_generation=str(context["workspace_generation"]),
            )
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
            self._require_current_workspace_registration(
                connection,
                device_id=str(context["device_id"]),
                workspace_id=str(context["workspace_id"]),
                workspace_generation=str(context["workspace_generation"]),
            )
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
                    c.device_id, c.workspace_id, c.workspace_generation,
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
            self._require_current_workspace_registration(
                connection,
                device_id=str(live["device_id"]),
                workspace_id=str(live["workspace_id"]),
                workspace_generation=str(live["workspace_generation"]),
            )
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
                    c.closed_at_ms, c.device_id, c.workspace_id, c.workspace_generation,
                    b.owner_id AS binding_owner_id, b.revoked_at_ms AS binding_revoked_at_ms,
                    n.owner_id AS node_owner_id, n.revoked_at_ms AS node_revoked_at_ms,
                    nw.registered_at_ms AS workspace_registered_at_ms,
                    nw.retired_at_ms AS workspace_retired_at_ms
                FROM mcp_access_grants g
                JOIN contexts c ON c.context_id = g.context_id
                JOIN bindings b ON b.binding_id = c.binding_id
                JOIN nodes n ON n.device_id = c.device_id
                LEFT JOIN node_workspaces nw
                    ON nw.device_id = c.device_id
                    AND nw.workspace_id = c.workspace_id
                    AND nw.workspace_generation = c.workspace_generation
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
            or row["workspace_registered_at_ms"] is None
            or row["workspace_retired_at_ms"] is not None
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
            self._require_current_workspace_registration(
                connection,
                device_id=str(live["device_id"]),
                workspace_id=str(live["workspace_id"]),
                workspace_generation=str(live["workspace_generation"]),
            )

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

    def request_mcp_bounded_file_read(
        self,
        *,
        owner_id: str,
        principal_id: str,
        binding_id: str,
        path: str,
        start_line: int,
        max_lines: int,
        max_bytes: int,
        idempotency_key: str,
        facade_contract: dict[str, Any],
        task_id: str | None = None,
    ) -> dict[str, Any]:
        """Atomically queue one OAuth-principal-scoped bounded file read.

        Unlike the historical compact-metadata lane, this creates a short-lived
        internal context from an explicit account binding.  The caller can
        neither select a path outside the local allowlist nor supply a target
        by display name, a stale context, or a client-controlled expiry.  A
        Windows policy/bridge remains the final local authority boundary.
        When ``task_id`` is supplied it must be a live server-issued task
        handle pinned to the same binding; the action is linked to that task
        so later patch/test/observe calls stay on the same target.
        """

        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        binding_id = _text(binding_id, "binding_id")
        path = _bounded_file_read_path(path)
        start_line, max_lines, max_bytes = _bounded_file_read_limits(
            start_line=start_line,
            max_lines=max_lines,
            max_bytes=max_bytes,
        )
        idempotency_key = _text(idempotency_key, "idempotency_key", pattern=KEY_PATTERN)
        facade_contract = _facade_contract(facade_contract)
        if task_id is not None and (not isinstance(task_id, str) or TASK_ID_PATTERN.fullmatch(task_id) is None):
            raise ValidationError("task_id is invalid.")
        intent = {
            "kind": "mcp_facade_bounded_file_read_v1",
            "principal_id": principal_id,
            "binding_id": binding_id,
            "task_id": task_id,
            "path": path,
            "start_line": start_line,
            "max_lines": max_lines,
            "max_bytes": max_bytes,
            "idempotency_key": idempotency_key,
            "facade_contract": facade_contract,
        }
        intent_digest = _digest(intent)
        # ``actions`` has an older owner/device idempotency uniqueness rule.
        # Namespace the public key by principal so two linked accounts cannot
        # conflict or observe each other's action merely by choosing the same
        # caller-supplied key.
        action_idempotency_key = "mcpfr_" + hashlib.sha256(
            f"{principal_id}\0{idempotency_key}".encode("utf-8")
        ).hexdigest()
        request_id = f"req_{uuid.uuid4().hex}"
        action_id = f"act_{uuid.uuid4().hex}"
        context_id = f"ctx_{uuid.uuid4().hex}"

        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                # Resolve the OAuth mapping inside the write transaction, not
                # only at HTTP ingress.  Revocation or reassignment between
                # authentication and queue creation must fail closed.
                principal = connection.execute(
                    "SELECT principal_id, owner_id, revoked_at_ms FROM oauth_principals WHERE principal_id = ?",
                    (principal_id,),
                ).fetchone()
                if principal is None or principal["owner_id"] != owner_id or principal["revoked_at_ms"] is not None:
                    raise PermissionError("authenticated OAuth account is not authorized for this control plane.")

                existing = connection.execute(
                    "SELECT * FROM mcp_file_read_intents WHERE principal_id = ? AND idempotency_key = ?",
                    (principal_id, idempotency_key),
                ).fetchone()
                if existing is not None:
                    if existing["intent_digest"] != intent_digest:
                        raise ConflictError("idempotency key is already bound to a different bounded file read.")
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
                    raise ConflictError("central admission is in recovery mode.")
                if task_id is not None:
                    self._require_live_mcp_task(
                        connection,
                        owner_id=owner_id,
                        principal_id=principal_id,
                        task_id=task_id,
                        binding_id=binding_id,
                    )
                live = connection.execute(
                    """
                    SELECT
                        b.binding_id, b.owner_id AS binding_owner_id, b.device_id,
                        b.endpoint_id, b.workspace_id, b.workspace_generation,
                        b.revoked_at_ms AS binding_revoked_at_ms,
                        n.owner_id AS node_owner_id, n.endpoint_id AS node_endpoint_id,
                        n.revoked_at_ms AS node_revoked_at_ms,
                        nw.capabilities_json, nw.retired_at_ms AS workspace_retired_at_ms
                    FROM bindings AS b
                    JOIN nodes AS n ON n.device_id = b.device_id
                    JOIN node_workspaces AS nw
                      ON nw.device_id = b.device_id
                     AND nw.workspace_id = b.workspace_id
                     AND nw.workspace_generation = b.workspace_generation
                    WHERE b.binding_id = ?
                    """,
                    (binding_id,),
                ).fetchone()
                if live is None:
                    raise NotFoundError("binding does not exist.")
                if live["binding_owner_id"] != owner_id or live["node_owner_id"] != owner_id:
                    raise PermissionError("binding is not owned by this OAuth account.")
                if (
                    live["binding_revoked_at_ms"] is not None
                    or live["node_revoked_at_ms"] is not None
                    or live["workspace_retired_at_ms"] is not None
                    or live["node_endpoint_id"] != live["endpoint_id"]
                ):
                    raise ConflictError("selected binding is no longer dispatchable.")
                try:
                    capabilities = _workspace_capabilities(json.loads(str(live["capabilities_json"])))
                except (TypeError, ValueError, json.JSONDecodeError) as error:
                    raise RuntimeError("stored workspace capabilities are invalid.") from error
                if capabilities["read"] is not True:
                    raise PermissionError("selected binding does not permit read access.")
                self._require_current_workspace_registration(
                    connection,
                    device_id=str(live["device_id"]),
                    workspace_id=str(live["workspace_id"]),
                    workspace_generation=str(live["workspace_generation"]),
                )

                expires_at_ms = now + MCP_BOUNDED_FILE_READ_MAX_TTL_MS
                action_arguments = {
                    "operation": "read_file",
                    "path": path,
                    "start_line": start_line,
                    "max_lines": max_lines,
                    "max_bytes": max_bytes,
                }
                action_immutable = {
                    "request_id": request_id,
                    "context_id": context_id,
                    "binding_id": binding_id,
                    "principal_id": principal_id,
                    "device_id": live["device_id"],
                    "endpoint_id": live["endpoint_id"],
                    "workspace_id": live["workspace_id"],
                    "workspace_generation": live["workspace_generation"],
                    "tool_name": "workspace_context",
                    "arguments": action_arguments,
                    "idempotency_key": action_idempotency_key,
                    "admission_reference": f"mcp_file_read:{intent_digest}",
                    "expires_at_ms": expires_at_ms,
                    "facade_contract": facade_contract,
                }
                action_digest = _digest(action_immutable)
                conflicting_action = connection.execute(
                    "SELECT action_id FROM actions WHERE owner_id = ? AND device_id = ? AND idempotency_key = ?",
                    (owner_id, live["device_id"], action_idempotency_key),
                ).fetchone()
                if conflicting_action is not None:
                    raise ConflictError("idempotency key is already bound to a different action.")

                connection.execute(
                    "INSERT INTO contexts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                    (
                        context_id,
                        owner_id,
                        binding_id,
                        live["device_id"],
                        live["endpoint_id"],
                        live["workspace_id"],
                        live["workspace_generation"],
                        now,
                        expires_at_ms,
                    ),
                )
                connection.execute(
                    "INSERT INTO work_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                    (
                        request_id,
                        owner_id,
                        context_id,
                        "Read one policy-bounded file through the local control-plane bridge.",
                        _canonical_json({"kind": "bounded_file_read", "tool_name": "workspace_context"}),
                        _canonical_json({"operation": "bounded_file_read", "binding_id": binding_id}),
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
                        action_id, owner_id, request_id, context_id, binding_id,
                        live["device_id"], live["endpoint_id"], live["workspace_id"], live["workspace_generation"],
                        "workspace_context", _canonical_json(action_arguments), action_digest,
                        action_idempotency_key, f"mcp_file_read:{intent_digest}", now, expires_at_ms,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO mcp_file_read_intents(
                        owner_id, principal_id, idempotency_key, intent_digest,
                        facade_schema_version, facade_profile, facade_contract_sha256,
                        binding_id, request_id, action_id, created_at_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        owner_id, principal_id, idempotency_key, intent_digest,
                        facade_contract["schema_version"], facade_contract["profile"], facade_contract["sha256"],
                        binding_id, request_id, action_id, now,
                    ),
                )
                self._event(
                    connection,
                    "work_request",
                    request_id,
                    "mcp_bounded_file_read_request_created",
                    {"binding_id": binding_id, "intent_digest": intent_digest},
                )
                self._event(connection, "action", action_id, "action_sealed", {"request_id": request_id, "digest": action_digest})
                if task_id is not None:
                    self.link_mcp_task_action(connection, task_id=task_id, action_id=action_id)
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return {
            "request_id": request_id,
            "action_id": action_id,
            "intent_digest": intent_digest,
            "facade_contract": facade_contract,
            "replayed": False,
        }

    def mcp_file_read_action_observation(
        self,
        *,
        owner_id: str,
        principal_id: str,
        action_id: str,
    ) -> dict[str, Any]:
        """Observe only a current principal's own bounded-file action."""

        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        action_id = _text(action_id, "action_id")
        with self._connection() as connection:
            principal = connection.execute(
                "SELECT owner_id, revoked_at_ms FROM oauth_principals WHERE principal_id = ?",
                (principal_id,),
            ).fetchone()
            if principal is None or principal["owner_id"] != owner_id or principal["revoked_at_ms"] is not None:
                raise PermissionError("authenticated OAuth account is not authorized for this control plane.")
            intent = connection.execute(
                """
                SELECT action_id FROM mcp_file_read_intents
                WHERE owner_id = ? AND principal_id = ? AND action_id = ?
                """,
                (owner_id, principal_id, action_id),
            ).fetchone()
        if intent is None:
            raise NotFoundError("bounded file read action does not exist.")
        return self.action_observation(owner_id=owner_id, action_id=action_id)

    @staticmethod
    def _mcp_permission_request_projection(
        row: sqlite3.Row,
        *,
        include_principal: bool,
    ) -> dict[str, Any]:
        """Return a precise but non-executable permission-request record.

        The relative path and content digests are the reviewable scope; raw
        patch content, a Windows root, node credentials and any future local
        policy are intentionally not part of this central projection.
        """

        result: dict[str, Any] = {
            "permission_request_id": row["permission_request_id"],
            "binding_id": row["binding_id"],
            "device_id": row["device_id"],
            "endpoint_id": row["endpoint_id"],
            "workspace_id": row["workspace_id"],
            "workspace_generation": row["workspace_generation"],
            "tool_name": row["tool_name"],
            "operation": row["operation"],
            "path": row["relative_path"],
            "preimage_sha256": row["preimage_sha256"],
            "patch_sha256": row["patch_sha256"],
            "validation_profile": row["validation_profile"],
            "permission_digest": row["permission_digest"],
            "task_id": row["task_id"] if "task_id" in row.keys() else None,
            "facade_contract": {
                "schema_version": row["facade_schema_version"],
                "profile": row["facade_profile"],
                "sha256": row["facade_contract_sha256"],
            },
            "created_at_ms": row["created_at_ms"],
            "expires_at_ms": row["expires_at_ms"],
            "state": row["state"],
            "decided_at_ms": row["decided_at_ms"],
        }
        if include_principal:
            result["principal_id"] = row["principal_id"]
        return result

    def _mcp_patch_permission_binding(
        self,
        connection: sqlite3.Connection,
        *,
        owner_id: str,
        binding_id: str,
        expected: sqlite3.Row | None = None,
    ) -> sqlite3.Row:
        """Validate the exact C4 target without treating it as local authority."""

        live = connection.execute(
            """
            SELECT
                b.binding_id, b.owner_id AS binding_owner_id, b.device_id,
                b.endpoint_id, b.workspace_id, b.workspace_generation,
                b.revoked_at_ms AS binding_revoked_at_ms,
                n.owner_id AS node_owner_id, n.endpoint_id AS node_endpoint_id,
                n.revoked_at_ms AS node_revoked_at_ms,
                nw.capabilities_json, nw.retired_at_ms AS workspace_retired_at_ms
            FROM bindings AS b
            JOIN nodes AS n ON n.device_id = b.device_id
            JOIN node_workspaces AS nw
              ON nw.device_id = b.device_id
             AND nw.workspace_id = b.workspace_id
             AND nw.workspace_generation = b.workspace_generation
            WHERE b.binding_id = ?
            """,
            (binding_id,),
        ).fetchone()
        if live is None:
            raise NotFoundError("binding does not exist.")
        if live["binding_owner_id"] != owner_id or live["node_owner_id"] != owner_id:
            raise PermissionError("binding is not owned by this OAuth account.")
        if (
            live["binding_revoked_at_ms"] is not None
            or live["node_revoked_at_ms"] is not None
            or live["workspace_retired_at_ms"] is not None
            or live["node_endpoint_id"] != live["endpoint_id"]
        ):
            raise ConflictError("selected binding is no longer dispatchable.")
        try:
            capabilities = _workspace_capabilities(json.loads(str(live["capabilities_json"])))
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise RuntimeError("stored workspace capabilities are invalid.") from error
        # This is an inventory ceiling only.  A future local bridge must still
        # reject the request unless its own current policy permits this exact
        # mutation; central approval never changes that policy.
        if capabilities["write"] is not True:
            raise PermissionError("selected binding does not advertise write capability.")
        self._require_current_workspace_registration(
            connection,
            device_id=str(live["device_id"]),
            workspace_id=str(live["workspace_id"]),
            workspace_generation=str(live["workspace_generation"]),
        )
        if expected is not None and (
            expected["binding_id"] != live["binding_id"]
            or expected["device_id"] != live["device_id"]
            or expected["endpoint_id"] != live["endpoint_id"]
            or expected["workspace_id"] != live["workspace_id"]
            or expected["workspace_generation"] != live["workspace_generation"]
        ):
            raise ConflictError("permission request target is no longer current.")
        return live

    def request_mcp_patch_permission(
        self,
        *,
        owner_id: str,
        principal_id: str,
        binding_id: str,
        path: Any,
        preimage_sha256: Any,
        patch_sha256: Any,
        validation_profile: Any,
        idempotency_key: str,
        facade_contract: dict[str, Any],
        task_id: str | None = None,
    ) -> dict[str, Any]:
        """Record one owner-reviewable C4 patch permission request.

        The request intentionally has no action, delivery attempt, local
        policy, execution descriptor or grant bearer.  Approval only records
        a durable central decision that a later C4 local bridge must bind to
        and revalidate before it can seal or execute a patch.
        """

        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        binding_id = _text(binding_id, "binding_id")
        idempotency_key = _text(idempotency_key, "idempotency_key", pattern=KEY_PATTERN)
        scope = _mcp_patch_permission_scope(
            path=path,
            preimage_sha256=preimage_sha256,
            patch_sha256=patch_sha256,
            validation_profile=validation_profile,
        )
        facade_contract = _facade_contract(facade_contract)
        if task_id is not None and (not isinstance(task_id, str) or TASK_ID_PATTERN.fullmatch(task_id) is None):
            raise ValidationError("task_id is invalid.")
        now = self.clock()
        expires_at_ms = now + MCP_PATCH_PERMISSION_MAX_TTL_MS
        immutable = {
            "owner_id": owner_id,
            "principal_id": principal_id,
            "binding_id": binding_id,
            "task_id": task_id,
            "tool_name": MCP_PATCH_PERMISSION_TOOL_NAME,
            "operation": MCP_PATCH_PERMISSION_OPERATION,
            "scope": scope,
            "idempotency_key": idempotency_key,
            "expires_at_ms": expires_at_ms,
            "facade_contract": facade_contract,
        }
        permission_digest = _digest(immutable)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                principal = connection.execute(
                    "SELECT owner_id, revoked_at_ms FROM oauth_principals WHERE principal_id = ?",
                    (principal_id,),
                ).fetchone()
                if principal is None or principal["owner_id"] != owner_id or principal["revoked_at_ms"] is not None:
                    raise PermissionError("authenticated OAuth account is not authorized for this control plane.")
                existing = connection.execute(
                    """
                    SELECT * FROM mcp_permission_requests
                    WHERE principal_id = ? AND idempotency_key = ?
                    """,
                    (principal_id, idempotency_key),
                ).fetchone()
                if existing is not None:
                    if existing["permission_digest"] != permission_digest:
                        raise ConflictError("idempotency key is already bound to a different permission request.")
                    connection.execute("COMMIT")
                    return self._mcp_permission_request_projection(existing, include_principal=False) | {"replayed": True}
                if self._admission_mode(connection) != "open":
                    raise ConflictError("central admission is in recovery mode.")
                if task_id is not None:
                    self._require_live_mcp_task(
                        connection,
                        owner_id=owner_id,
                        principal_id=principal_id,
                        task_id=task_id,
                        binding_id=binding_id,
                    )
                live = self._mcp_patch_permission_binding(
                    connection,
                    owner_id=owner_id,
                    binding_id=binding_id,
                )
                permission_request_id = f"permreq_{uuid.uuid4().hex}"
                connection.execute(
                    """
                    INSERT INTO mcp_permission_requests(
                        permission_request_id, owner_id, principal_id, binding_id,
                        device_id, endpoint_id, workspace_id, workspace_generation,
                        tool_name, operation, relative_path, preimage_sha256,
                        patch_sha256, validation_profile, permission_digest,
                        idempotency_key, task_id, facade_schema_version, facade_profile,
                        facade_contract_sha256, created_at_ms, expires_at_ms,
                        state, decided_at_ms, decided_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', NULL, NULL)
                    """,
                    (
                        permission_request_id, owner_id, principal_id, binding_id,
                        live["device_id"], live["endpoint_id"], live["workspace_id"], live["workspace_generation"],
                        MCP_PATCH_PERMISSION_TOOL_NAME, MCP_PATCH_PERMISSION_OPERATION,
                        scope["path"], scope["preimage_sha256"], scope["patch_sha256"], scope["validation_profile"],
                        permission_digest, idempotency_key, task_id,
                        facade_contract["schema_version"], facade_contract["profile"], facade_contract["sha256"],
                        now, expires_at_ms,
                    ),
                )
                self._event(
                    connection,
                    "mcp_permission_request",
                    permission_request_id,
                    "mcp_patch_permission_requested",
                    {"binding_id": binding_id, "permission_digest": permission_digest, "task_id": task_id},
                )
                row = connection.execute(
                    "SELECT * FROM mcp_permission_requests WHERE permission_request_id = ?",
                    (permission_request_id,),
                ).fetchone()
                if row is None:
                    raise RuntimeError("permission request was not persisted.")
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return self._mcp_permission_request_projection(row, include_principal=False) | {"replayed": False}

    def mcp_permission_request_observation(
        self,
        *,
        owner_id: str,
        principal_id: str,
        permission_request_id: str,
    ) -> dict[str, Any]:
        """Observe only the requesting OAuth principal's non-executable request."""

        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        permission_request_id = _text(permission_request_id, "permission_request_id")
        with self._connection() as connection:
            principal = connection.execute(
                "SELECT owner_id, revoked_at_ms FROM oauth_principals WHERE principal_id = ?",
                (principal_id,),
            ).fetchone()
            if principal is None or principal["owner_id"] != owner_id or principal["revoked_at_ms"] is not None:
                raise PermissionError("authenticated OAuth account is not authorized for this control plane.")
            row = connection.execute(
                """
                SELECT * FROM mcp_permission_requests
                WHERE permission_request_id = ? AND owner_id = ? AND principal_id = ?
                """,
                (permission_request_id, owner_id, principal_id),
            ).fetchone()
        if row is None:
            raise NotFoundError("permission request does not exist.")
        return self._mcp_permission_request_projection(row, include_principal=False)

    def list_mcp_permission_requests(self, *, owner_id: str) -> list[dict[str, Any]]:
        """List exact pending/decided scopes for the private owner Console."""

        owner_id = _text(owner_id, "owner_id")
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM mcp_permission_requests
                WHERE owner_id = ?
                ORDER BY CASE state WHEN 'pending' THEN 0 ELSE 1 END, created_at_ms DESC, permission_request_id
                """,
                (owner_id,),
            ).fetchall()
        return [self._mcp_permission_request_projection(row, include_principal=True) for row in rows]

    def list_mcp_patch_acceptances(self, *, owner_id: str, limit: int = 100) -> list[dict[str, Any]]:
        owner_id = _text(owner_id, "owner_id")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 500:
            raise ValidationError("limit is invalid.")
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM mcp_patch_acceptances WHERE owner_id = ? ORDER BY decided_at_ms DESC, action_id LIMIT ?",
                (owner_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_owner_mcp_task_sessions(self, *, owner_id: str) -> list[dict[str, Any]]:
        """Owner Console view across all linked OAuth principals."""

        return self.list_mcp_task_sessions(owner_id=owner_id, principal_id=None)

    def close_owner_mcp_task_session(self, *, owner_id: str, task_id: str, reason: str = "owner_console_closed") -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        if not isinstance(task_id, str) or TASK_ID_PATTERN.fullmatch(task_id) is None:
            raise ValidationError("task_id is invalid.")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute("SELECT * FROM mcp_task_sessions WHERE task_id = ?", (task_id,)).fetchone()
                if row is None:
                    raise NotFoundError("task does not exist.")
                if row["owner_id"] != owner_id:
                    raise PermissionError("task is not owned by this principal.")
                if row["closed_at_ms"] is None:
                    now = self.clock()
                    connection.execute(
                        "UPDATE mcp_task_sessions SET closed_at_ms = ?, close_reason = ? WHERE task_id = ?",
                        (now, reason[:64], task_id),
                    )
                    self._event(connection, "mcp_task_session", task_id, "mcp_task_session_closed", {"reason": reason[:64]})
                row = connection.execute("SELECT * FROM mcp_task_sessions WHERE task_id = ?", (task_id,)).fetchone()
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return _row(row) or {}

    def record_owner_mcp_patch_acceptance(
        self, *, owner_id: str, action_id: str, decision: str, note: str = "", decided_by: str = "owner_console"
    ) -> dict[str, Any]:
        """Owner Console acceptance without requiring the OAuth principal handle.

        The principal is resolved from the sealed approved-patch intent so the
        Console never needs to copy a principal token. Owner, target and
        receipt gates are identical to the principal path.
        """
        owner_id = _text(owner_id, "owner_id")
        action_id = _text(action_id, "action_id")
        with self._connection() as connection:
            intent = connection.execute(
                "SELECT principal_id FROM mcp_approved_patch_intents WHERE action_id = ?",
                (action_id,),
            ).fetchone()
        if intent is None:
            raise NotFoundError("approved-patch action does not exist.")
        return self.record_mcp_patch_acceptance(
            owner_id=owner_id,
            principal_id=str(intent["principal_id"]),
            action_id=action_id,
            decision=decision,
            note=note,
            decided_by=decided_by,
        )

    def approve_mcp_permission_request(self, *, owner_id: str, permission_request_id: str) -> dict[str, Any]:
        """Record owner approval without creating an action or local grant."""

        owner_id = _text(owner_id, "owner_id")
        permission_request_id = _text(permission_request_id, "permission_request_id")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    "SELECT * FROM mcp_permission_requests WHERE permission_request_id = ?",
                    (permission_request_id,),
                ).fetchone()
                if row is None:
                    raise NotFoundError("permission request does not exist.")
                if row["owner_id"] != owner_id:
                    raise PermissionError("permission request is not owned by this operator.")
                if row["state"] == "rejected":
                    raise ConflictError("permission request was rejected.")
                if row["state"] == "approved":
                    connection.execute("COMMIT")
                    return self._mcp_permission_request_projection(row, include_principal=True)
                now = self.clock()
                if row["expires_at_ms"] <= now:
                    raise ConflictError("permission request is expired.")
                principal = connection.execute(
                    "SELECT owner_id, revoked_at_ms FROM oauth_principals WHERE principal_id = ?",
                    (row["principal_id"],),
                ).fetchone()
                if principal is None or principal["owner_id"] != owner_id or principal["revoked_at_ms"] is not None:
                    raise ConflictError("permission request principal is no longer active.")
                if self._admission_mode(connection) != "open":
                    raise ConflictError("central admission is in recovery mode.")
                self._mcp_patch_permission_binding(
                    connection,
                    owner_id=owner_id,
                    binding_id=str(row["binding_id"]),
                    expected=row,
                )
                connection.execute(
                    """
                    UPDATE mcp_permission_requests
                    SET state = 'approved', decided_at_ms = ?, decided_by = ?
                    WHERE permission_request_id = ?
                    """,
                    (now, owner_id, permission_request_id),
                )
                self._event(
                    connection,
                    "mcp_permission_request",
                    permission_request_id,
                    "mcp_patch_permission_approved",
                    {"permission_digest": row["permission_digest"]},
                )
                row = connection.execute(
                    "SELECT * FROM mcp_permission_requests WHERE permission_request_id = ?",
                    (permission_request_id,),
                ).fetchone()
                if row is None:
                    raise RuntimeError("permission request disappeared during approval.")
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return self._mcp_permission_request_projection(row, include_principal=True)

    def reject_mcp_permission_request(self, *, owner_id: str, permission_request_id: str) -> dict[str, Any]:
        """Record a terminal owner rejection without affecting any local process."""

        owner_id = _text(owner_id, "owner_id")
        permission_request_id = _text(permission_request_id, "permission_request_id")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    "SELECT * FROM mcp_permission_requests WHERE permission_request_id = ?",
                    (permission_request_id,),
                ).fetchone()
                if row is None:
                    raise NotFoundError("permission request does not exist.")
                if row["owner_id"] != owner_id:
                    raise PermissionError("permission request is not owned by this operator.")
                if row["state"] == "approved":
                    raise ConflictError("permission request was already approved.")
                if row["state"] == "pending":
                    now = self.clock()
                    connection.execute(
                        """
                        UPDATE mcp_permission_requests
                        SET state = 'rejected', decided_at_ms = ?, decided_by = ?
                        WHERE permission_request_id = ?
                        """,
                        (now, owner_id, permission_request_id),
                    )
                    self._event(
                        connection,
                        "mcp_permission_request",
                        permission_request_id,
                        "mcp_patch_permission_rejected",
                        {"permission_digest": row["permission_digest"]},
                    )
                    row = connection.execute(
                        "SELECT * FROM mcp_permission_requests WHERE permission_request_id = ?",
                        (permission_request_id,),
                    ).fetchone()
                if row is None:
                    raise RuntimeError("permission request disappeared during rejection.")
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return self._mcp_permission_request_projection(row, include_principal=True)

    def request_mcp_approved_patch(
        self,
        *,
        owner_id: str,
        principal_id: str,
        permission_request_id: str,
        patch_envelope: Any,
        idempotency_key: str,
        facade_contract: dict[str, Any],
        task_id: str | None = None,
    ) -> dict[str, Any]:
        """Atomically seal one approved exact-file patch for the patch lane.

        The central approval row is necessary but not sufficient for an effect.
        This method creates the normal context/work-request/action lineage only
        after it has bound the exact approved principal, target generation,
        digest and short expiry.  The raw patch is retained solely in the
        dedicated intent table for delivery to the selected node; generic
        action arguments and all event payloads retain digests only.
        When the permission request was opened under a task, the same task
        handle must be presented here; the sealed action is linked to it.
        """

        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        permission_request_id = _text(permission_request_id, "permission_request_id")
        idempotency_key = _text(idempotency_key, "idempotency_key", pattern=KEY_PATTERN)
        facade_contract = _facade_contract(facade_contract)
        if task_id is not None and (not isinstance(task_id, str) or TASK_ID_PATTERN.fullmatch(task_id) is None):
            raise ValidationError("task_id is invalid.")
        request_id = f"req_{uuid.uuid4().hex}"
        action_id = f"act_{uuid.uuid4().hex}"
        context_id = f"ctx_{uuid.uuid4().hex}"

        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                principal = connection.execute(
                    "SELECT owner_id, revoked_at_ms FROM oauth_principals WHERE principal_id = ?",
                    (principal_id,),
                ).fetchone()
                if principal is None or principal["owner_id"] != owner_id or principal["revoked_at_ms"] is not None:
                    raise PermissionError("authenticated OAuth account is not authorized for this control plane.")
                permission = connection.execute(
                    "SELECT * FROM mcp_permission_requests WHERE permission_request_id = ?",
                    (permission_request_id,),
                ).fetchone()
                if permission is None:
                    raise NotFoundError("permission request does not exist.")
                if permission["owner_id"] != owner_id or permission["principal_id"] != principal_id:
                    raise PermissionError("permission request is not owned by this OAuth account.")
                approved_patch = _mcp_approved_patch_envelope(
                    patch_envelope,
                    expected_path=str(permission["relative_path"]),
                    expected_preimage_sha256=str(permission["preimage_sha256"]),
                    expected_patch_sha256=str(permission["patch_sha256"]),
                )
                permission_task_id = permission["task_id"] if "task_id" in permission.keys() else None
                effective_task_id = task_id if task_id is not None else permission_task_id
                if permission_task_id is not None and task_id is not None and task_id != permission_task_id:
                    raise ConflictError("approved patch task does not match its permission request task.")
                immutable = {
                    "kind": "mcp_facade_approved_patch_v1",
                    "owner_id": owner_id,
                    "principal_id": principal_id,
                    "permission_request_id": permission_request_id,
                    "permission_digest": permission["permission_digest"],
                    "binding_id": permission["binding_id"],
                    "task_id": effective_task_id,
                    "path": permission["relative_path"],
                    "preimage_sha256": permission["preimage_sha256"],
                    "patch_sha256": permission["patch_sha256"],
                    "validation_profile": permission["validation_profile"],
                    "idempotency_key": idempotency_key,
                    "facade_contract": facade_contract,
                }
                intent_digest = _digest(immutable)
                existing = connection.execute(
                    """
                    SELECT * FROM mcp_approved_patch_intents
                    WHERE principal_id = ? AND idempotency_key = ?
                    """,
                    (principal_id, idempotency_key),
                ).fetchone()
                if existing is not None:
                    if existing["intent_digest"] != intent_digest:
                        raise ConflictError("idempotency key is already bound to a different approved patch.")
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
                already_used = connection.execute(
                    "SELECT action_id FROM mcp_approved_patch_intents WHERE permission_request_id = ?",
                    (permission_request_id,),
                ).fetchone()
                if already_used is not None:
                    raise ConflictError("approved permission request is already bound to an action.")
                now = self.clock()
                if permission["state"] != "approved":
                    raise ConflictError("permission request is not approved.")
                if permission["expires_at_ms"] <= now:
                    raise ConflictError("permission request is expired.")
                if self._admission_mode(connection) != "open":
                    raise ConflictError("central admission is in recovery mode.")
                if effective_task_id is not None:
                    self._require_live_mcp_task(
                        connection,
                        owner_id=owner_id,
                        principal_id=principal_id,
                        task_id=str(effective_task_id),
                        binding_id=str(permission["binding_id"]),
                    )
                live = self._mcp_patch_permission_binding(
                    connection,
                    owner_id=owner_id,
                    binding_id=str(permission["binding_id"]),
                    expected=permission,
                )
                expires_at_ms = int(permission["expires_at_ms"])
                action_arguments = {
                    "operation": MCP_APPROVED_PATCH_OPERATION,
                    "permission_request_id": permission_request_id,
                    "path": str(permission["relative_path"]),
                    "preimage_sha256": str(permission["preimage_sha256"]),
                    "patch_sha256": str(permission["patch_sha256"]),
                    "validation_profile": MCP_PATCH_PERMISSION_VALIDATION_PROFILE,
                }
                action_idempotency_key = "mcpap_" + hashlib.sha256(
                    f"{principal_id}\0{idempotency_key}".encode("utf-8")
                ).hexdigest()
                action_immutable = {
                    "request_id": request_id,
                    "context_id": context_id,
                    "binding_id": permission["binding_id"],
                    "principal_id": principal_id,
                    "permission_request_id": permission_request_id,
                    "permission_digest": permission["permission_digest"],
                    "device_id": live["device_id"],
                    "endpoint_id": live["endpoint_id"],
                    "workspace_id": live["workspace_id"],
                    "workspace_generation": live["workspace_generation"],
                    "tool_name": MCP_APPROVED_PATCH_TOOL_NAME,
                    "arguments": action_arguments,
                    "idempotency_key": action_idempotency_key,
                    "admission_reference": f"mcp_approved_patch:{intent_digest}",
                    "expires_at_ms": expires_at_ms,
                    "facade_contract": facade_contract,
                }
                action_digest = _digest(action_immutable)
                conflicting_action = connection.execute(
                    "SELECT action_id FROM actions WHERE owner_id = ? AND device_id = ? AND idempotency_key = ?",
                    (owner_id, live["device_id"], action_idempotency_key),
                ).fetchone()
                if conflicting_action is not None:
                    raise ConflictError("idempotency key is already bound to a different action.")
                connection.execute(
                    "INSERT INTO contexts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                    (
                        context_id,
                        owner_id,
                        permission["binding_id"],
                        live["device_id"],
                        live["endpoint_id"],
                        live["workspace_id"],
                        live["workspace_generation"],
                        now,
                        expires_at_ms,
                    ),
                )
                connection.execute(
                    "INSERT INTO work_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                    (
                        request_id,
                        owner_id,
                        context_id,
                        "Apply one owner-approved exact patch through the local control-plane bridge.",
                        _canonical_json({"kind": "approved_patch", "tool_name": MCP_APPROVED_PATCH_TOOL_NAME}),
                        _canonical_json({"operation": "approved_patch", "permission_request_id": permission_request_id}),
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
                        context_id,
                        permission["binding_id"],
                        live["device_id"],
                        live["endpoint_id"],
                        live["workspace_id"],
                        live["workspace_generation"],
                        MCP_APPROVED_PATCH_TOOL_NAME,
                        _canonical_json(action_arguments),
                        action_digest,
                        action_idempotency_key,
                        f"mcp_approved_patch:{intent_digest}",
                        now,
                        expires_at_ms,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO mcp_approved_patch_intents(
                        owner_id, principal_id, permission_request_id, permission_digest,
                        binding_id, idempotency_key, intent_digest, relative_path,
                        preimage_sha256, patch_sha256, validation_profile, patch_envelope,
                        facade_schema_version, facade_profile, facade_contract_sha256,
                        request_id, action_id, created_at_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        owner_id,
                        principal_id,
                        permission_request_id,
                        permission["permission_digest"],
                        permission["binding_id"],
                        idempotency_key,
                        intent_digest,
                        permission["relative_path"],
                        permission["preimage_sha256"],
                        permission["patch_sha256"],
                        permission["validation_profile"],
                        approved_patch,
                        facade_contract["schema_version"],
                        facade_contract["profile"],
                        facade_contract["sha256"],
                        request_id,
                        action_id,
                        now,
                    ),
                )
                self._event(
                    connection,
                    "work_request",
                    request_id,
                    "mcp_approved_patch_request_created",
                    {
                        "permission_request_id": permission_request_id,
                        "intent_digest": intent_digest,
                    },
                )
                self._event(
                    connection,
                    "action",
                    action_id,
                    "action_sealed",
                    {"request_id": request_id, "digest": action_digest},
                )
                if effective_task_id is not None:
                    self.link_mcp_task_action(connection, task_id=str(effective_task_id), action_id=action_id)
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return {
            "request_id": request_id,
            "action_id": action_id,
            "intent_digest": intent_digest,
            "facade_contract": facade_contract,
            "replayed": False,
        }

    def mcp_approved_patch_action_observation(
        self,
        *,
        owner_id: str,
        principal_id: str,
        action_id: str,
    ) -> dict[str, Any]:
        """Observe an approved-patch lifecycle without returning its patch body."""

        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        action_id = _text(action_id, "action_id")
        with self._connection() as connection:
            principal = connection.execute(
                "SELECT owner_id, revoked_at_ms FROM oauth_principals WHERE principal_id = ?",
                (principal_id,),
            ).fetchone()
            if principal is None or principal["owner_id"] != owner_id or principal["revoked_at_ms"] is not None:
                raise PermissionError("authenticated OAuth account is not authorized for this control plane.")
            intent = connection.execute(
                """
                SELECT action_id FROM mcp_approved_patch_intents
                WHERE owner_id = ? AND principal_id = ? AND action_id = ?
                """,
                (owner_id, principal_id, action_id),
            ).fetchone()
        if intent is None:
            raise NotFoundError("approved patch action does not exist.")
        return self.action_observation(owner_id=owner_id, action_id=action_id)

    def mcp_approved_patch_expected_file(
        self,
        *,
        owner_id: str,
        principal_id: str,
        action_id: str,
    ) -> dict[str, Any]:
        """Return only the sealed, non-patch result fields for one action.

        The raw Write Exact File envelope is retained in the protected intent
        table solely for delivery to the local node.  A client-facing receipt
        projection still needs to prove its postimage against that sealed
        intent, so this helper parses the already-authorized envelope inside
        the central store and returns only digest-level fields.  It never
        returns patch bytes, compressed data, or a local workspace path.
        """

        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        action_id = _text(action_id, "action_id")
        with self._connection() as connection:
            principal = connection.execute(
                "SELECT owner_id, revoked_at_ms FROM oauth_principals WHERE principal_id = ?",
                (principal_id,),
            ).fetchone()
            if principal is None or principal["owner_id"] != owner_id or principal["revoked_at_ms"] is not None:
                raise PermissionError("authenticated OAuth account is not authorized for this control plane.")
            intent = connection.execute(
                """
                SELECT relative_path, preimage_sha256, patch_sha256, patch_envelope,
                       facade_schema_version, facade_profile, facade_contract_sha256
                FROM mcp_approved_patch_intents
                WHERE owner_id = ? AND principal_id = ? AND action_id = ?
                """,
                (owner_id, principal_id, action_id),
            ).fetchone()
        if intent is None:
            raise NotFoundError("approved patch action does not exist.")
        try:
            envelope = _mcp_approved_patch_envelope(
                intent["patch_envelope"],
                expected_path=str(intent["relative_path"]),
                expected_preimage_sha256=str(intent["preimage_sha256"]),
                expected_patch_sha256=str(intent["patch_sha256"]),
            )
            metadata = {
                key: value.lower()
                for key, _, value in (
                    token.partition("=")
                    for token in envelope.replace("\r\n", "\n").splitlines()[2].removeprefix("@@ ").split()
                )
            }
            postimage_sha256 = metadata["postimage_sha256"]
        except (KeyError, ValidationError, ConflictError) as error:
            raise RuntimeError("stored approved patch intent is invalid.") from error
        return {
            "path": str(intent["relative_path"]),
            "preimage_sha256": str(intent["preimage_sha256"]),
            "postimage_sha256": postimage_sha256,
            "patch_sha256": str(intent["patch_sha256"]),
            "facade_contract": {
                "schema_version": int(intent["facade_schema_version"]),
                "profile": str(intent["facade_profile"]),
                "sha256": str(intent["facade_contract_sha256"]),
            },
        }

    def request_mcp_exec(
        self,
        *,
        owner_id: str,
        principal_id: str,
        binding_id: str,
        argv: Any,
        cwd: Any = "",
        timeout_ms: int = 60_000,
        max_output_bytes: int = 32 * 1024,
        idempotency_key: str,
        facade_contract: dict[str, Any],
        task_id: str | None = None,
    ) -> dict[str, Any]:
        """Queue one bounded structured exec for local policy admission.

        Central validation is syntactic only: argv array without shell, cwd
        confined to a root-relative path, explicit timeout/output caps. The
        Windows node must match argv against its local allowlist, enforce the
        workspace write lock, resource limits and process-tree stop before any
        spawn. cwd is a start directory, never a confinement proof.
        """
        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        binding_id = _text(binding_id, "binding_id")
        argv = _mcp_exec_argv(argv)
        cwd = _mcp_exec_cwd(cwd)
        timeout_ms, max_output_bytes = _mcp_exec_limits(timeout_ms=timeout_ms, max_output_bytes=max_output_bytes)
        idempotency_key = _text(idempotency_key, "idempotency_key", pattern=KEY_PATTERN)
        facade_contract = _facade_contract(facade_contract)
        if task_id is not None and (not isinstance(task_id, str) or TASK_ID_PATTERN.fullmatch(task_id) is None):
            raise ValidationError("task_id is invalid.")
        argv_digest = _digest({"argv": argv})
        intent = {
            "kind": "mcp_facade_exec_v1",
            "principal_id": principal_id,
            "binding_id": binding_id,
            "task_id": task_id,
            "argv_digest": argv_digest,
            "cwd": cwd,
            "timeout_ms": timeout_ms,
            "max_output_bytes": max_output_bytes,
            "idempotency_key": idempotency_key,
            "facade_contract": facade_contract,
        }
        intent_digest = _digest(intent)
        action_idempotency_key = "mcpExec_" + hashlib.sha256(f"{principal_id}\0{idempotency_key}".encode()).hexdigest()
        request_id = f"req_{uuid.uuid4().hex}"
        action_id = f"act_{uuid.uuid4().hex}"
        context_id = f"ctx_{uuid.uuid4().hex}"
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                principal = connection.execute(
                    "SELECT owner_id, revoked_at_ms FROM oauth_principals WHERE principal_id = ?",
                    (principal_id,),
                ).fetchone()
                if principal is None or principal["owner_id"] != owner_id or principal["revoked_at_ms"] is not None:
                    raise PermissionError("authenticated OAuth account is not authorized for this control plane.")
                existing = connection.execute(
                    "SELECT * FROM mcp_exec_intents WHERE principal_id = ? AND idempotency_key = ?",
                    (principal_id, idempotency_key),
                ).fetchone()
                if existing is not None:
                    if existing["intent_digest"] != intent_digest:
                        raise ConflictError("idempotency key is already bound to a different exec.")
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
                    raise ConflictError("central admission is in recovery mode.")
                if task_id is not None:
                    self._require_live_mcp_task(connection, owner_id=owner_id, principal_id=principal_id, task_id=task_id, binding_id=binding_id)
                live = connection.execute(
                    """
                    SELECT b.binding_id, b.owner_id AS binding_owner_id, b.device_id,
                           b.endpoint_id, b.workspace_id, b.workspace_generation,
                           b.revoked_at_ms AS binding_revoked_at_ms,
                           n.owner_id AS node_owner_id, n.endpoint_id AS node_endpoint_id,
                           n.revoked_at_ms AS node_revoked_at_ms,
                           nw.capabilities_json, nw.retired_at_ms AS workspace_retired_at_ms
                    FROM bindings AS b
                    JOIN nodes AS n ON n.device_id = b.device_id
                    JOIN node_workspaces AS nw
                      ON nw.device_id = b.device_id
                     AND nw.workspace_id = b.workspace_id
                     AND nw.workspace_generation = b.workspace_generation
                    WHERE b.binding_id = ?
                    """,
                    (binding_id,),
                ).fetchone()
                if live is None:
                    raise NotFoundError("binding does not exist.")
                if live["binding_owner_id"] != owner_id or live["node_owner_id"] != owner_id:
                    raise PermissionError("binding is not owned by this OAuth account.")
                if (
                    live["binding_revoked_at_ms"] is not None
                    or live["node_revoked_at_ms"] is not None
                    or live["workspace_retired_at_ms"] is not None
                    or live["node_endpoint_id"] != live["endpoint_id"]
                ):
                    raise ConflictError("selected binding is no longer dispatchable.")
                try:
                    capabilities = _workspace_capabilities(json.loads(str(live["capabilities_json"])))
                except (TypeError, ValueError, json.JSONDecodeError) as error:
                    raise RuntimeError("stored workspace capabilities are invalid.") from error
                if capabilities["exec"] is not True:
                    raise PermissionError("selected binding does not permit exec access.")
                self._require_current_workspace_registration(
                    connection,
                    device_id=str(live["device_id"]),
                    workspace_id=str(live["workspace_id"]),
                    workspace_generation=str(live["workspace_generation"]),
                )
                expires_at_ms = now + MCP_EXEC_MAX_TTL_MS
                action_arguments = {"operation": MCP_EXEC_OPERATION, "argv_digest": argv_digest, "cwd": cwd,
                                    "timeout_ms": timeout_ms, "max_output_bytes": max_output_bytes}
                action_immutable = {"request_id": request_id, "context_id": context_id, "binding_id": binding_id,
                                    "principal_id": principal_id, "device_id": live["device_id"],
                                    "endpoint_id": live["endpoint_id"], "workspace_id": live["workspace_id"],
                                    "workspace_generation": live["workspace_generation"], "tool_name": MCP_EXEC_TOOL_NAME,
                                    "arguments": action_arguments, "idempotency_key": action_idempotency_key,
                                    "admission_reference": f"mcp_exec:{intent_digest}", "expires_at_ms": expires_at_ms,
                                    "facade_contract": facade_contract}
                action_digest = _digest(action_immutable)
                conflicting = connection.execute(
                    "SELECT action_id FROM actions WHERE owner_id = ? AND device_id = ? AND idempotency_key = ?",
                    (owner_id, live["device_id"], action_idempotency_key),
                ).fetchone()
                if conflicting is not None:
                    raise ConflictError("idempotency key is already bound to a different action.")
                connection.execute(
                    "INSERT INTO contexts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                    (context_id, owner_id, binding_id, live["device_id"], live["endpoint_id"],
                     live["workspace_id"], live["workspace_generation"], now, expires_at_ms),
                )
                connection.execute(
                    "INSERT INTO work_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                    (request_id, owner_id, context_id, "Run one bounded structured command through the local bridge.",
                     _canonical_json({"kind": "bounded_exec", "tool_name": MCP_EXEC_TOOL_NAME}),
                     _canonical_json({"operation": "bounded_exec", "binding_id": binding_id}), now, expires_at_ms),
                )
                connection.execute(
                    """INSERT INTO actions(action_id, owner_id, request_id, context_id, binding_id, device_id,
                        endpoint_id, workspace_id, workspace_generation, tool_name, arguments_json, action_digest,
                        idempotency_key, admission_reference, created_at_ms, expires_at_ms, delivery_state, settled_at_ms)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', NULL)""",
                    (action_id, owner_id, request_id, context_id, binding_id, live["device_id"], live["endpoint_id"],
                     live["workspace_id"], live["workspace_generation"], MCP_EXEC_TOOL_NAME,
                     _canonical_json(action_arguments), action_digest, action_idempotency_key,
                     f"mcp_exec:{intent_digest}", now, expires_at_ms),
                )
                connection.execute(
                    """INSERT INTO mcp_exec_intents(owner_id, principal_id, binding_id, task_id, argv_json, argv_digest,
                        cwd, timeout_ms, max_output_bytes, idempotency_key, intent_digest, facade_schema_version,
                        facade_profile, facade_contract_sha256, request_id, action_id, created_at_ms)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (owner_id, principal_id, binding_id, task_id, _canonical_json({"argv": argv}), argv_digest,
                     cwd, timeout_ms, max_output_bytes, idempotency_key, intent_digest,
                     facade_contract["schema_version"], facade_contract["profile"], facade_contract["sha256"],
                     request_id, action_id, now),
                )
                self._event(connection, "work_request", request_id, "mcp_exec_request_created",
                            {"binding_id": binding_id, "intent_digest": intent_digest, "task_id": task_id})
                self._event(connection, "action", action_id, "action_sealed", {"request_id": request_id, "digest": action_digest})
                if task_id is not None:
                    self.link_mcp_task_action(connection, task_id=task_id, action_id=action_id)
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return {"request_id": request_id, "action_id": action_id, "intent_digest": intent_digest,
                "facade_contract": facade_contract, "replayed": False}

    def mcp_exec_action_observation(self, *, owner_id: str, principal_id: str, action_id: str) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        action_id = _text(action_id, "action_id")
        with self._connection() as connection:
            principal = connection.execute(
                "SELECT owner_id, revoked_at_ms FROM oauth_principals WHERE principal_id = ?", (principal_id,)
            ).fetchone()
            if principal is None or principal["owner_id"] != owner_id or principal["revoked_at_ms"] is not None:
                raise PermissionError("authenticated OAuth account is not authorized for this control plane.")
            intent = connection.execute(
                "SELECT action_id FROM mcp_exec_intents WHERE owner_id = ? AND principal_id = ? AND action_id = ?",
                (owner_id, principal_id, action_id),
            ).fetchone()
        if intent is None:
            raise NotFoundError("exec action does not exist.")
        return self.action_observation(owner_id=owner_id, action_id=action_id)

    def mcp_exec_intent_for_delivery(self, *, action_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM mcp_exec_intents WHERE action_id = ?", (action_id,)).fetchone()
        return dict(row) if row is not None else None

    def request_mcp_exec_stop(self, *, owner_id: str, principal_id: str, action_id: str, requested_by: str = "mcp") -> dict[str, Any]:
        """Fence new dispatch and request stop for a running exec.

        Stop is a verified request, not a proof: the facade reports
        stop_pending until the node relays a terminal stopped receipt proving
        process-tree quiescence. Offline nodes stay pending, never success.
        Task expiry never blocks observing or stopping an existing action.
        """
        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        action_id = _text(action_id, "action_id")
        if not isinstance(requested_by, str) or not 1 <= len(requested_by.strip()) <= 64:
            raise ValidationError("requested_by is invalid.")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                principal = connection.execute(
                    "SELECT owner_id, revoked_at_ms FROM oauth_principals WHERE principal_id = ?", (principal_id,)
                ).fetchone()
                if principal is None or principal["owner_id"] != owner_id or principal["revoked_at_ms"] is not None:
                    raise PermissionError("authenticated OAuth account is not authorized for this control plane.")
                intent = connection.execute(
                    "SELECT * FROM mcp_exec_intents WHERE owner_id = ? AND principal_id = ? AND action_id = ?",
                    (owner_id, principal_id, action_id),
                ).fetchone()
                if intent is None:
                    raise NotFoundError("exec action does not exist.")
                action = connection.execute("SELECT * FROM actions WHERE action_id = ?", (action_id,)).fetchone()
                if action is None:
                    raise NotFoundError("action does not exist.")
                if action["tool_name"] != MCP_EXEC_TOOL_NAME:
                    raise ConflictError("only exec actions support stop.")
                existing = connection.execute(
                    "SELECT * FROM mcp_exec_stop_requests WHERE action_id = ?", (action_id,)
                ).fetchone()
                now = self.clock()
                if existing is None:
                    connection.execute(
                        "INSERT INTO mcp_exec_stop_requests(action_id, owner_id, principal_id, requested_at_ms, requested_by, state)"
                        " VALUES (?, ?, ?, ?, ?, 'pending')",
                        (action_id, owner_id, principal_id, now, requested_by.strip()),
                    )
                    self._event(connection, "action", action_id, "mcp_exec_stop_requested", {})
                row = connection.execute("SELECT * FROM mcp_exec_stop_requests WHERE action_id = ?", (action_id,)).fetchone()
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return dict(row)

    def acknowledge_mcp_exec_stop(self, *, action_id: str, device_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute("SELECT * FROM mcp_exec_stop_requests WHERE action_id = ?", (action_id,)).fetchone()
                if row is None:
                    connection.execute("COMMIT")
                    return None
                action = connection.execute("SELECT device_id FROM actions WHERE action_id = ?", (action_id,)).fetchone()
                if action is None or action["device_id"] != device_id:
                    raise PermissionError("stop request belongs to another device.")
                if row["state"] == "pending":
                    now = self.clock()
                    connection.execute(
                        "UPDATE mcp_exec_stop_requests SET state = 'acknowledged', acknowledged_at_ms = ? WHERE action_id = ?",
                        (now, action_id),
                    )
                row = connection.execute("SELECT * FROM mcp_exec_stop_requests WHERE action_id = ?", (action_id,)).fetchone()
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return dict(row)

    def list_mcp_exec_stop_requests(self, *, device_id: str) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                """SELECT s.* FROM mcp_exec_stop_requests AS s JOIN actions AS a ON a.action_id = s.action_id
                   WHERE a.device_id = ? AND s.state = 'pending' ORDER BY s.requested_at_ms""",
                (device_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_owner_exec_stops(self, *, owner_id: str, limit: int = 100) -> list[dict[str, Any]]:
        owner_id = _text(owner_id, "owner_id")
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM mcp_exec_stop_requests WHERE owner_id = ? ORDER BY requested_at_ms DESC LIMIT ?",
                (owner_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def request_mcp_artifact(
        self, *, owner_id: str, principal_id: str, binding_id: str, kind: str,
        path: str, idempotency_key: str, facade_contract: dict[str, Any],
        task_id: str | None = None,
    ) -> dict[str, Any]:
        """Queue one scoped document/image read for local allowlist admission.

        Docs are bounded UTF-8 text; images are bounded binary with MIME
        allowlisted at the node. Central checks path shape and capability;
        the Windows bridge revalidates the exact allowlist, size, MIME and
        target generation before any byte leaves the workspace.
        """
        if kind not in ("document", "image"):
            raise ValidationError("artifact kind is invalid.")
        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        binding_id = _text(binding_id, "binding_id")
        path = _bounded_file_read_path(path)
        idempotency_key = _text(idempotency_key, "idempotency_key", pattern=KEY_PATTERN)
        facade_contract = _facade_contract(facade_contract)
        if task_id is not None and (not isinstance(task_id, str) or TASK_ID_PATTERN.fullmatch(task_id) is None):
            raise ValidationError("task_id is invalid.")
        tool_name = "document_workflow" if kind == "document" else "view_image"
        intent = {"kind": f"mcp_facade_artifact_{kind}_v1", "principal_id": principal_id,
                  "binding_id": binding_id, "task_id": task_id, "path": path,
                  "idempotency_key": idempotency_key, "facade_contract": facade_contract}
        intent_digest = _digest(intent)
        action_idempotency_key = "mcpArtifact_" + hashlib.sha256(f"{principal_id}\0{kind}\0{idempotency_key}".encode()).hexdigest()
        request_id = f"req_{uuid.uuid4().hex}"
        action_id = f"act_{uuid.uuid4().hex}"
        context_id = f"ctx_{uuid.uuid4().hex}"
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                principal = connection.execute(
                    "SELECT owner_id, revoked_at_ms FROM oauth_principals WHERE principal_id = ?", (principal_id,)
                ).fetchone()
                if principal is None or principal["owner_id"] != owner_id or principal["revoked_at_ms"] is not None:
                    raise PermissionError("authenticated OAuth account is not authorized for this control plane.")
                existing = connection.execute(
                    "SELECT * FROM mcp_artifact_intents WHERE principal_id = ? AND idempotency_key = ?",
                    (principal_id, idempotency_key),
                ).fetchone()
                if existing is not None:
                    if existing["intent_digest"] != intent_digest or existing["binding_id"] != binding_id:
                        raise ConflictError("idempotency key is already bound to a different artifact read.")
                    connection.execute("COMMIT")
                    return {"request_id": existing["request_id"], "action_id": existing["action_id"],
                            "intent_digest": existing["intent_digest"],
                            "facade_contract": {"schema_version": existing["facade_schema_version"],
                                                "profile": existing["facade_profile"],
                                                "sha256": existing["facade_contract_sha256"]}, "replayed": True}
                now = self.clock()
                if self._admission_mode(connection) != "open":
                    raise ConflictError("central admission is in recovery mode.")
                if task_id is not None:
                    self._require_live_mcp_task(connection, owner_id=owner_id, principal_id=principal_id,
                                                task_id=task_id, binding_id=binding_id)
                live = connection.execute(
                    """SELECT b.binding_id, b.owner_id AS binding_owner_id, b.device_id, b.endpoint_id,
                              b.workspace_id, b.workspace_generation, b.revoked_at_ms AS binding_revoked_at_ms,
                              n.owner_id AS node_owner_id, n.endpoint_id AS node_endpoint_id,
                              n.revoked_at_ms AS node_revoked_at_ms, nw.capabilities_json,
                              nw.retired_at_ms AS workspace_retired_at_ms
                       FROM bindings AS b JOIN nodes AS n ON n.device_id = b.device_id
                       JOIN node_workspaces AS nw ON nw.device_id = b.device_id
                        AND nw.workspace_id = b.workspace_id AND nw.workspace_generation = b.workspace_generation
                       WHERE b.binding_id = ?""", (binding_id,)).fetchone()
                if live is None:
                    raise NotFoundError("binding does not exist.")
                if live["binding_owner_id"] != owner_id or live["node_owner_id"] != owner_id:
                    raise PermissionError("binding is not owned by this OAuth account.")
                if (live["binding_revoked_at_ms"] is not None or live["node_revoked_at_ms"] is not None
                        or live["workspace_retired_at_ms"] is not None or live["node_endpoint_id"] != live["endpoint_id"]):
                    raise ConflictError("selected binding is no longer dispatchable.")
                try:
                    capabilities = _workspace_capabilities(json.loads(str(live["capabilities_json"])))
                except (TypeError, ValueError, json.JSONDecodeError) as error:
                    raise RuntimeError("stored workspace capabilities are invalid.") from error
                if capabilities["read"] is not True:
                    raise PermissionError("selected binding does not permit read access.")
                self._require_current_workspace_registration(
                    connection, device_id=str(live["device_id"]), workspace_id=str(live["workspace_id"]),
                    workspace_generation=str(live["workspace_generation"]))
                expires_at_ms = now + MCP_ARTIFACT_MAX_TTL_MS
                action_arguments = {"operation": f"{kind}_read", "path": path}
                action_digest = _digest({"request_id": request_id, "context_id": context_id, "binding_id": binding_id,
                                         "principal_id": principal_id, "device_id": live["device_id"],
                                         "tool_name": tool_name, "arguments": action_arguments,
                                         "idempotency_key": action_idempotency_key, "expires_at_ms": expires_at_ms,
                                         "facade_contract": facade_contract})
                if connection.execute("SELECT action_id FROM actions WHERE owner_id = ? AND device_id = ? AND idempotency_key = ?",
                                      (owner_id, live["device_id"], action_idempotency_key)).fetchone() is not None:
                    raise ConflictError("idempotency key is already bound to a different action.")
                connection.execute("INSERT INTO contexts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                                   (context_id, owner_id, binding_id, live["device_id"], live["endpoint_id"],
                                    live["workspace_id"], live["workspace_generation"], now, expires_at_ms))
                connection.execute("INSERT INTO work_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                                   (request_id, owner_id, context_id, f"Read one scoped {kind} through the local bridge.",
                                    _canonical_json({"kind": f"artifact_{kind}", "tool_name": tool_name}),
                                    _canonical_json({"operation": f"{kind}_read", "binding_id": binding_id}), now, expires_at_ms))
                connection.execute(
                    """INSERT INTO actions(action_id, owner_id, request_id, context_id, binding_id, device_id,
                        endpoint_id, workspace_id, workspace_generation, tool_name, arguments_json, action_digest,
                        idempotency_key, admission_reference, created_at_ms, expires_at_ms, delivery_state, settled_at_ms)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', NULL)""",
                    (action_id, owner_id, request_id, context_id, binding_id, live["device_id"], live["endpoint_id"],
                     live["workspace_id"], live["workspace_generation"], tool_name, _canonical_json(action_arguments),
                     action_digest, action_idempotency_key, f"mcp_artifact_{kind}:{intent_digest}", now, expires_at_ms))
                connection.execute(
                    """INSERT INTO mcp_artifact_intents(owner_id, principal_id, binding_id, task_id, kind, path,
                        idempotency_key, intent_digest, facade_schema_version, facade_profile, facade_contract_sha256,
                        request_id, action_id, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (owner_id, principal_id, binding_id, task_id, kind, path, idempotency_key, intent_digest,
                     facade_contract["schema_version"], facade_contract["profile"], facade_contract["sha256"],
                     request_id, action_id, now))
                self._event(connection, "work_request", request_id, f"mcp_artifact_{kind}_request_created",
                            {"binding_id": binding_id, "intent_digest": intent_digest, "task_id": task_id})
                self._event(connection, "action", action_id, "action_sealed", {"request_id": request_id, "digest": action_digest})
                if task_id is not None:
                    self.link_mcp_task_action(connection, task_id=task_id, action_id=action_id)
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return {"request_id": request_id, "action_id": action_id, "intent_digest": intent_digest,
                "facade_contract": facade_contract, "replayed": False}

    def mcp_artifact_action_observation(self, *, owner_id: str, principal_id: str, action_id: str) -> dict[str, Any]:
        owner_id = _text(owner_id, "owner_id")
        principal_id = _text(principal_id, "principal_id")
        action_id = _text(action_id, "action_id")
        with self._connection() as connection:
            principal = connection.execute(
                "SELECT owner_id, revoked_at_ms FROM oauth_principals WHERE principal_id = ?", (principal_id,)).fetchone()
            if principal is None or principal["owner_id"] != owner_id or principal["revoked_at_ms"] is not None:
                raise PermissionError("authenticated OAuth account is not authorized for this control plane.")
            intent = connection.execute(
                "SELECT action_id FROM mcp_artifact_intents WHERE owner_id = ? AND principal_id = ? AND action_id = ?",
                (owner_id, principal_id, action_id)).fetchone()
        if intent is None:
            raise NotFoundError("artifact action does not exist.")
        return self.action_observation(owner_id=owner_id, action_id=action_id)

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
        if row["_workspace_registered_at_ms"] is None or row["_workspace_retired_at_ms"] is not None:
            return "workspace_registration_not_current"
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

    def poll_actions(
        self,
        *,
        device_id: str,
        limit: int = 10,
        lane: str | None = None,
    ) -> list[dict[str, Any]]:
        """Allocate delivery attempts for one explicit local execution lane.

        The historical callers that omit ``lane`` retain their prior behavior
        except that they can never claim a bounded-file action.  This prevents
        an old compact-metadata worker from dequeuing a new file payload before
        its separate policy/bridge has been installed.
        """

        device_id = _text(device_id, "device_id")
        limit = max(1, min(int(limit), 50))
        if lane is not None and lane not in {
            "generic",
            "read_only_workspace_context",
            "bounded_file_read",
            "approved_patch",
            "bounded_exec",
            "bounded_artifact",
        }:
            raise ValidationError("poll lane is invalid.")
        lane_predicate = {
            None: "f.action_id IS NULL AND p.action_id IS NULL AND e.action_id IS NULL AND a2.action_id IS NULL",
            "generic": "m.action_id IS NULL AND f.action_id IS NULL AND p.action_id IS NULL AND e.action_id IS NULL AND a2.action_id IS NULL",
            "read_only_workspace_context": "m.action_id IS NOT NULL AND f.action_id IS NULL AND p.action_id IS NULL AND e.action_id IS NULL AND a2.action_id IS NULL",
            "bounded_file_read": "f.action_id IS NOT NULL AND p.action_id IS NULL AND e.action_id IS NULL AND a2.action_id IS NULL",
            "approved_patch": "p.action_id IS NOT NULL",
            "bounded_exec": "e.action_id IS NOT NULL",
            "bounded_artifact": "a2.action_id IS NOT NULL",
        }[lane]
        now = self.clock()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if self._admission_mode(connection) != "open":
                connection.execute("COMMIT")
                return []
            rows = connection.execute(
                f"""
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
                    nw.registered_at_ms AS _workspace_registered_at_ms,
                    nw.retired_at_ms AS _workspace_retired_at_ms,
                    m.intent_digest AS mcp_read_only_intent_digest,
                    m.facade_schema_version AS mcp_facade_schema_version,
                    m.facade_profile AS mcp_facade_profile,
                    m.facade_contract_sha256 AS mcp_facade_contract_sha256,
                    f.intent_digest AS mcp_file_read_intent_digest,
                    f.facade_schema_version AS mcp_file_read_facade_schema_version,
                    f.facade_profile AS mcp_file_read_facade_profile,
                    f.facade_contract_sha256 AS mcp_file_read_facade_contract_sha256,
                    p.permission_request_id AS mcp_approved_patch_permission_request_id,
                    p.permission_digest AS mcp_approved_patch_permission_digest,
                    p.intent_digest AS mcp_approved_patch_intent_digest,
                    p.relative_path AS mcp_approved_patch_relative_path,
                    p.preimage_sha256 AS mcp_approved_patch_preimage_sha256,
                    p.patch_sha256 AS mcp_approved_patch_sha256,
                    p.validation_profile AS mcp_approved_patch_validation_profile,
                    p.patch_envelope AS mcp_approved_patch_envelope,
                    p.facade_schema_version AS mcp_approved_patch_facade_schema_version,
                    p.facade_profile AS mcp_approved_patch_facade_profile,
                    p.facade_contract_sha256 AS mcp_approved_patch_facade_contract_sha256,
                    e.argv_json AS mcp_exec_argv_json,
                    e.argv_digest AS mcp_exec_argv_digest,
                    e.cwd AS mcp_exec_cwd,
                    e.timeout_ms AS mcp_exec_timeout_ms,
                    e.max_output_bytes AS mcp_exec_max_output_bytes,
                    e.intent_digest AS mcp_exec_intent_digest,
                    e.facade_schema_version AS mcp_exec_facade_schema_version,
                    e.facade_profile AS mcp_exec_facade_profile,
                    e.facade_contract_sha256 AS mcp_exec_facade_contract_sha256,
                    a2.kind AS mcp_artifact_kind,
                    a2.path AS mcp_artifact_path,
                    a2.intent_digest AS mcp_artifact_intent_digest,
                    a2.facade_schema_version AS mcp_artifact_facade_schema_version,
                    a2.facade_profile AS mcp_artifact_facade_profile,
                    a2.facade_contract_sha256 AS mcp_artifact_facade_contract_sha256
                FROM actions a
                JOIN nodes n ON n.device_id = a.device_id
                JOIN bindings b ON b.binding_id = a.binding_id
                JOIN contexts c ON c.context_id = a.context_id
                JOIN work_requests w ON w.request_id = a.request_id
                LEFT JOIN node_workspaces nw
                    ON nw.device_id = a.device_id
                    AND nw.workspace_id = a.workspace_id
                    AND nw.workspace_generation = a.workspace_generation
                LEFT JOIN mcp_read_only_intents m ON m.action_id = a.action_id
                LEFT JOIN mcp_file_read_intents f ON f.action_id = a.action_id
                LEFT JOIN mcp_approved_patch_intents p ON p.action_id = a.action_id
                LEFT JOIN mcp_exec_intents e ON e.action_id = a.action_id
                LEFT JOIN mcp_artifact_intents a2 ON a2.action_id = a.action_id
                WHERE a.device_id = ? AND a.delivery_state = 'queued' AND {lane_predicate}
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
                       CASE WHEN approved_patch.action_id IS NULL THEN 0 ELSE 1 END AS approved_patch_candidate,
                       reconciliation.disposition AS reconciliation_disposition,
                       reconciliation.reconciled_at_ms
                FROM actions AS action
                LEFT JOIN action_reconciliations AS reconciliation
                  ON reconciliation.action_id = action.action_id
                LEFT JOIN mcp_approved_patch_intents AS approved_patch
                  ON approved_patch.action_id = action.action_id
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
            # This is only a safe lifecycle classification. It deliberately
            # reveals neither the exact patch envelope nor local acceptance
            # correlation, but lets the Console avoid presenting a completed
            # effect as semantic task acceptance.
            projection["approved_patch_candidate"] = bool(projection.get("approved_patch_candidate"))
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
                    "mcp_file_read_intents",
                    "mcp_permission_requests",
                    "mcp_approved_patch_intents",
                    "mcp_access_grants",
                    "oauth_principals",
                    "oauth_link_requests",
                    "node_workspaces",
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
