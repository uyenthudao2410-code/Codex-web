"""Guarded approved MCP web Ubuntu rollout driver, executed by the authorized parent over SSH stdin.

No authority renewal, patch replay, task mutation, Windows action or DB restore.
Child stdout/stderr and protected configuration values never reach stdout.
Without --execute, this performs only the archive/baseline/quiescence preflight.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import pwd
import shlex
import sqlite3
import stat
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.request


HOST = "100.116.112.22"
USER = "svhome"
SERVICE = "codex-control-plane.service"
BASE_REVISION = "beaa9d5ade4926ef231e3ec9d0a517fe93830e90"
BASE_PACKAGE = "sha256:acb5ae4713844015e32ee5005001583ae4c04e650c68fb599b22309c65dd2835"
REVISION = "5ce5c51fc97584501d5d091e8c21df88250f55eb42e6e756384b234da8837b1f"
PACKAGE = "sha256:bb529f710342bf064fb5d2259ab1ad49e3733a6ca6db0c60b60ed67f119a7566"
ARCHIVE_SHA256 = "ba38f233d2369835bc3d60f4d9af3e0b65f0ed71565303628f7a25ef42120b90"
SCHEMA = 28
HOME = Path("/home/svhome")
INSTALL = HOME / ".local/lib/codex-control-plane"
CURRENT = INSTALL / "current"
RELEASES = INSTALL / "releases"
INCOMING = INSTALL / "incoming"
RELEASE_NAME = f"codex-control-plane-{REVISION}"
ARCHIVE = INCOMING / f"{RELEASE_NAME}.tar.gz"
ENV_FILE = HOME / ".config/codex-control-plane/control-plane.env"
DROP_IN = HOME / ".config/systemd/user/codex-control-plane.service.d/10-immutable-release.conf"
BACKUP_ROOT = HOME / ".local/state/codex-control-plane/deployment-backups"
HEALTH_KEYS = ("ok", "schema_version", "service_instance_id", "started_at_ms", "declared_source_revision",
               "package_source_sha256", "expected_package_source_sha256", "admission_mode")
STATE_QUERIES = {
    "unsettled_actions": "SELECT COUNT(*) FROM actions WHERE delivery_state != 'settled'",
    "queued_actions": "SELECT COUNT(*) FROM actions WHERE delivery_state = 'queued'",
    "accepted_actions": "SELECT COUNT(*) FROM actions WHERE delivery_state = 'accepted'",
    "open_writers": "SELECT COUNT(*) FROM mcp_task_writer_leases WHERE released_at_ms IS NULL",
    "open_tasks": "SELECT COUNT(*) FROM mcp_task_sessions WHERE closed_at_ms IS NULL",
    "actions": "SELECT COUNT(*) FROM actions",
    "tasks": "SELECT COUNT(*) FROM mcp_task_sessions",
    "acceptances": "SELECT COUNT(*) FROM mcp_patch_acceptances",
}
HISTORICAL_ACTION_IDS = (
    "act_048df93488874a70aa97a7ee18ccbd03",
    "act_0f0a49c6424d42d3bc7bc49ad46e4ffa",
    "act_3764695f2cb24c0d9b6968d850316938",
    "act_6e513ba70ec640259621fefd5c41a721",
    "act_744496c6bd514d38a746cf8819aae9ad",
    "act_79f4c19cdc214151b701e11f7be6f9a7",
    "act_8b03301c00854a0a8747139835b0c72d",
    "act_8c6adfb23b434c838b06ce15e5972429",
    "act_95f2504bd6d04690944e2c79754c8ab2",
    "act_98db4071326d448ea39a4784eb967b4b",
    "act_b7523c58039d4f8a9f097b4b2d36e948",
    "act_dc23860c42a746c2bea9d9b6ee7c7f11",
    "act_fd27acab6b684d98825d326c1aff3276",
)
UNOBSERVED_ACTION_ID = "act_0f0a49c6424d42d3bc7bc49ad46e4ffa"


class GuardFailure(Exception):
    def __init__(self, code: str):
        self.code = code


def require(condition: bool, code: str) -> None:
    if not condition:
        raise GuardFailure(code)


def emit(phase: str, **fields: object) -> None:
    print(json.dumps({"phase": phase, **fields}, separators=(",", ":")), flush=True)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def protected_file(path: Path) -> bytes:
    require(not path.is_symlink() and path.is_file(), "PROTECTED_FILE_UNSAFE")
    metadata = path.stat()
    require(metadata.st_uid == os.getuid() and stat.S_IMODE(metadata.st_mode) == 0o600,
            "PROTECTED_FILE_OWNER_OR_MODE_MISMATCH")
    return path.read_bytes()


def private_directory(path: Path, *, create: bool = False) -> None:
    if create and not path.exists():
        path.mkdir(parents=True, mode=0o700)
    require(not path.is_symlink() and path.is_dir(), "PRIVATE_DIRECTORY_UNSAFE")
    metadata = path.stat()
    require(metadata.st_uid == os.getuid() and stat.S_IMODE(metadata.st_mode) == 0o700,
            "PRIVATE_DIRECTORY_OWNER_OR_MODE_MISMATCH")


def run(arguments: list[str], *, code: str, environment: dict | None = None, timeout: int = 45) -> bytes:
    try:
        result = subprocess.run(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=environment, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        raise GuardFailure(code) from None
    require(result.returncode == 0, code)
    return result.stdout


def run_json(arguments: list[str], *, code: str, environment: dict | None = None) -> dict:
    output = run(arguments, code=code, environment=environment)
    try:
        result = json.loads(output)
    except (ValueError, UnicodeError):
        raise GuardFailure(code) from None
    require(isinstance(result, dict), code)
    return result


def parse_environment(value: bytes) -> dict[str, str]:
    result = {}
    for line in value.decode("utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, raw = line.split("=", 1)
        require(key.strip() not in result, "DUPLICATE_ENVIRONMENT_KEY")
        parts = shlex.split(raw, comments=True)
        require(len(parts) <= 1, "ENVIRONMENT_VALUE_INVALID")
        result[key.strip()] = parts[0] if parts else ""
    return result


def json_request(origin: str, token: str, route: str, body: dict | None = None) -> dict:
    request = urllib.request.Request(
        origin + route, data=None if body is None else json.dumps(body).encode("utf-8"),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        method="GET" if body is None else "POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.load(response)
    except (OSError, ValueError, urllib.error.URLError):
        raise GuardFailure("CONTROL_PLANE_API_FAILED") from None
    require(isinstance(result, dict), "CONTROL_PLANE_API_INVALID")
    return result


def state_counts(database: Path) -> dict:
    require(database.is_absolute() and database.is_file() and not database.is_symlink(), "DATABASE_TARGET_UNSAFE")
    require(not database.resolve().is_relative_to(INSTALL.resolve()), "DATABASE_INSIDE_RELEASE_TREE")
    with sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True, timeout=5) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        result = {key: int(connection.execute(query).fetchone()[0]) for key, query in STATE_QUERIES.items()}
        result["schema_version"] = int(connection.execute("PRAGMA user_version").fetchone()[0])
        require(result["schema_version"] == SCHEMA, "DATABASE_SCHEMA_CHANGED")
        actions = [dict(row) for row in connection.execute(
            "SELECT * FROM actions WHERE delivery_state != 'settled' ORDER BY action_id"
        ).fetchall()]
        require(tuple(row["action_id"] for row in actions) == HISTORICAL_ACTION_IDS,
                "UNFENCED_OR_CHANGED_UNSETTLED_ACTIONS_BLOCK_DEPLOYMENT")
        families = []
        unknown_count = unobserved_count = 0
        observed_at_ms = int(time.time() * 1000)
        for action in actions:
            action_id = action["action_id"]
            require(action["tool_name"] == "workspace_context" and action["settled_at_ms"] is None
                    and isinstance(action["expires_at_ms"], int) and action["expires_at_ms"] <= observed_at_ms,
                    "HISTORICAL_ACTION_CONTRACT_INVALID")
            family = {"action": action}
            for table, ordering in (
                ("delivery_attempts", "attempt_number, attempt_id"),
                ("receipts", "received_at_ms, receipt_id"),
                ("action_reconciliations", "action_id"),
                ("action_dispatch_dispositions", "action_id"),
            ):
                family[table] = [dict(row) for row in connection.execute(
                    f"SELECT * FROM {table} WHERE action_id = ? ORDER BY {ordering}", (action_id,)
                ).fetchall()]
            attempts = family["delivery_attempts"]
            receipts = family["receipts"]
            reconciliations = family["action_reconciliations"]
            dispositions = family["action_dispatch_dispositions"]
            require(len(attempts) == 1, "HISTORICAL_ATTEMPT_COUNT_CHANGED")
            if action_id != UNOBSERVED_ACTION_ID:
                require(action["delivery_state"] == "reconcile_required" and len(receipts) == 1
                        and len(reconciliations) == 1 and not dispositions,
                        "HISTORICAL_UNKNOWN_FAMILY_INVALID")
                receipt = receipts[-1]
                disposition = reconciliations[0]
                require(receipt["receipt_state"] == "unknown" and receipt["device_id"] == action["device_id"]
                        and disposition["owner_id"] == action["owner_id"]
                        and disposition["device_id"] == action["device_id"]
                        and disposition["disposition"] == "quarantined_unknown"
                        and disposition["declaration"] == "HISTORICAL_READ_ONLY_UNKNOWN_EFFECT"
                        and disposition["receipt_id"] == receipt["receipt_id"]
                        and disposition["receipt_digest"] == receipt["receipt_digest"]
                        and disposition["receipt_received_at_ms"] == receipt["received_at_ms"],
                        "HISTORICAL_UNKNOWN_DISPOSITION_INVALID")
                evidence = {
                    "schema_version": 1, "action_id": action_id, "owner_id": action["owner_id"],
                    "device_id": action["device_id"], "tool_name": action["tool_name"],
                    "delivery_state": action["delivery_state"], "latest_receipt_id": receipt["receipt_id"],
                    "latest_receipt_state": receipt["receipt_state"],
                    "latest_receipt_digest": receipt["receipt_digest"],
                    "latest_receipt_received_at_ms": receipt["received_at_ms"],
                    "delivery_attempt_count": len(attempts),
                }
                unknown_count += 1
            else:
                require(action["delivery_state"] == "dispatch_unconfirmed" and not receipts
                        and not reconciliations and len(dispositions) == 1,
                        "HISTORICAL_UNOBSERVED_FAMILY_INVALID")
                attempt = attempts[0]
                disposition = dispositions[0]
                rationale = disposition["rationale"]
                require(disposition["owner_id"] == action["owner_id"]
                        and disposition["device_id"] == action["device_id"]
                        and disposition["attempt_id"] == attempt["attempt_id"]
                        and disposition["disposition"] == "historical_read_only_unobserved_dispatch"
                        and disposition["declaration"] == "HISTORICAL_READ_ONLY_UNOBSERVED_DISPATCH"
                        and disposition["action_expires_at_ms"] == action["expires_at_ms"]
                        and isinstance(disposition["decided_at_ms"], int)
                        and disposition["decided_at_ms"] >= action["expires_at_ms"]
                        and disposition["decided_by"] == action["owner_id"]
                        and isinstance(rationale, str) and rationale == rationale.strip()
                        and 1 <= len(rationale) <= 500
                        and all(ord(character) >= 32 and ord(character) != 127 for character in rationale),
                        "HISTORICAL_UNOBSERVED_DISPOSITION_INVALID")
                evidence = {
                    "schema_version": 1, "action_id": action_id, "owner_id": action["owner_id"],
                    "device_id": action["device_id"], "attempt_id": attempt["attempt_id"],
                    "attempt_number": attempt["attempt_number"], "dispatched_at_ms": attempt["dispatched_at_ms"],
                    "action_digest": action["action_digest"], "tool_name": action["tool_name"],
                    "delivery_state": action["delivery_state"], "action_expires_at_ms": action["expires_at_ms"],
                    "node_last_seen_at_ms": disposition["node_last_seen_at_ms"],
                    "node_readiness": disposition["node_readiness"],
                    "node_policy_state": disposition["node_policy_state"],
                    "node_policy_reason": disposition["node_policy_reason"],
                    "declaration": disposition["declaration"], "rationale": rationale,
                }
                unobserved_count += 1
            require(disposition["evidence_digest"] == canonical_digest(evidence),
                    "HISTORICAL_DISPOSITION_EVIDENCE_MISMATCH")
            families.append(family)
        result["quarantined_unknown_actions"] = unknown_count
        result["historical_unobserved_dispatch_actions"] = unobserved_count
        # Full immutable row families are hashed privately; payloads never leave the server.
        result["historical_action_families_sha256"] = canonical_digest(families)
    return result


def require_quiescent(database: Path, *, expected: dict | None = None) -> dict:
    result = state_counts(database)
    require(result["schema_version"] == SCHEMA, "DATABASE_SCHEMA_CHANGED")
    require(result["queued_actions"] == 0, "QUEUED_ACTIONS_BLOCK_DEPLOYMENT")
    require(result["accepted_actions"] == 0, "ACCEPTED_ACTIONS_BLOCK_DEPLOYMENT")
    require(result["unsettled_actions"] == 13 and result["quarantined_unknown_actions"] == 12
            and result["historical_unobserved_dispatch_actions"] == 1,
            "HISTORICAL_FENCE_COMPOSITION_CHANGED")
    require(result["open_writers"] == 0, "OPEN_WRITER_LEASES_BLOCK_DEPLOYMENT")
    if expected is not None:
        require(result == expected, "DEPLOYMENT_ACTION_TASK_OR_HISTORICAL_EVIDENCE_CHANGED")
    return result


def verify_release(release: Path, revision: str, fingerprint: str) -> dict:
    require(release.is_dir() and release.is_relative_to(RELEASES.resolve()), "RELEASE_TARGET_UNSAFE")
    receipt = run_json(["/usr/bin/python3", "-B", str(release / "deploy/control-plane-verify-release.py"),
                        "--release-dir", str(release)], code="RELEASE_INTEGRITY_FAILED")
    require(receipt.get("source_revision") == revision and receipt.get("package_source_sha256") == fingerprint,
            "RELEASE_IDENTITY_MISMATCH")
    require(receipt.get("control_plane_schema_version") == SCHEMA, "RELEASE_SCHEMA_MISMATCH")
    return receipt


def verify_health(origin: str, token: str, revision: str, fingerprint: str) -> dict:
    health = json_request(origin, token, "/healthz")
    require(health.get("ok") is True and health.get("schema_version") == SCHEMA, "SERVICE_HEALTH_OR_SCHEMA_FAILED")
    require(health.get("declared_source_revision") == revision, "SERVICE_REVISION_MISMATCH")
    require(health.get("package_source_sha256") == fingerprint
            and health.get("expected_package_source_sha256") == fingerprint, "SERVICE_BYTE_FINGERPRINT_MISMATCH")
    require(isinstance(health.get("service_instance_id"), str) and health["service_instance_id"], "SERVICE_INSTANCE_MISSING")
    return {key: health.get(key) for key in HEALTH_KEYS}


def wait_health(origin: str, token: str, revision: str, fingerprint: str) -> dict:
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        try:
            return verify_health(origin, token, revision, fingerprint)
        except GuardFailure:
            time.sleep(0.5)
    raise GuardFailure("SERVICE_HEALTH_TIMEOUT")


def service_pid() -> int:
    active = run(["systemctl", "--user", "is-active", SERVICE], code="SERVICE_NOT_ACTIVE").strip()
    require(active == b"active", "SERVICE_NOT_ACTIVE")
    raw = run(["systemctl", "--user", "show", SERVICE, "--property=MainPID", "--value"], code="SERVICE_PID_FAILED")
    require(raw.strip().isdigit() and int(raw) > 0, "SERVICE_PID_INVALID")
    return int(raw)


def validate_archive() -> None:
    private_directory(INCOMING)
    protected_file(ARCHIVE)
    require(file_hash(ARCHIVE) == ARCHIVE_SHA256, "ARCHIVE_SHA256_MISMATCH")
    with tarfile.open(ARCHIVE, "r:gz") as archive:
        for member in archive.getmembers():
            relative = PurePosixPath(member.name)
            require(not relative.is_absolute() and ".." not in relative.parts
                    and relative.parts and relative.parts[0] == RELEASE_NAME,
                    "ARCHIVE_PATH_INVALID")
            require(member.isdir() or member.isfile(), "ARCHIVE_LINK_OR_SPECIAL_FILE_DENIED")
            require(member.mode & 0o7000 == 0 and member.size <= 16 * 1024 * 1024, "ARCHIVE_MODE_OR_SIZE_INVALID")


def extract_archive() -> Path:
    target = RELEASES / RELEASE_NAME
    require(not target.exists() and not target.is_symlink(), "CANDIDATE_RELEASE_ALREADY_EXISTS")
    with tarfile.open(ARCHIVE, "r:gz") as archive:
        for member in archive.getmembers():
            destination = RELEASES / member.name
            if member.isdir():
                destination.mkdir(parents=True, mode=0o700, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
                source = archive.extractfile(member)
                require(source is not None, "ARCHIVE_FILE_READ_FAILED")
                with source, destination.open("xb") as output:
                    while block := source.read(1024 * 1024):
                        output.write(block)
                os.chmod(destination, 0o755 if member.mode & 0o111 else 0o600)
    return target.resolve()


def atomic_bytes(path: Path, content: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.hotfix-", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def atomic_current(target: str) -> None:
    temporary = INSTALL / f".current-hotfix-{os.getpid()}"
    require(not temporary.exists() and not temporary.is_symlink(), "CURRENT_TEMPORARY_ALREADY_EXISTS")
    try:
        temporary.symlink_to(target, target_is_directory=True)
        os.replace(temporary, CURRENT)
    finally:
        temporary.unlink(missing_ok=True)


"""Idempotent same-scope owner renewal appended to guarded driver definitions.

The pre-existing service grant remains valid and its scopes/credential are
preserved. Context and pilot are bounded to the one approved 60 minute window.
"""
import fcntl

BINDING = "bind_3e05bf64cb3e4bab93d930ae1692bebb"
DEVICE = "72ceec2d-e3f2-472f-8e3c-99fffe053035"
WORKSPACE = "workspace_dda1d78e9a21402aa6213f72af64f788"
GENERATION = "generation_c2f13e8d02344cf6a38a3f42ecfa59b6"
PRINCIPAL = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
GRANT = "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"
BACKUP = BACKUP_ROOT / "unified-setup-r7-5ce5c51fc9758450"
MARKER = BACKUP / "authority-renewal-public.json"
REASON = "Owner-approved frozen Console r7 rollout: same Tools-Codex-web read/write/sandboxed exec scope for 60 minutes"
lock_descriptor = None
try:
    require(pwd.getpwuid(os.getuid()).pw_name == USER, "EXECUTION_USER_MISMATCH")
    require(HOST in run(["tailscale", "ip", "-4"], code="TAILSCALE_IDENTITY_UNAVAILABLE").decode().split(), "SERVER_ADDRESS_MISMATCH")
    private_directory(BACKUP)
    lock_descriptor = os.open(INSTALL / ".owner-acceptance-deployment.lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise GuardFailure("DEPLOYMENT_OR_RENEWAL_ALREADY_RUNNING") from None
    values = parse_environment(protected_file(ENV_FILE))
    require(values.get("CONTROL_PLANE_MCP_SERVICE_EXEC_ENABLED") == "true", "EXISTING_EXEC_CONFIGURATION_CHANGED")
    token = values["CONTROL_PLANE_OPERATOR_TOKEN"]
    bind = values.get("CONTROL_PLANE_BIND", "127.0.0.1")
    if bind in ("0.0.0.0", "::"):
        bind = "127.0.0.1"
    origin = "http://" + bind + ":" + values.get("CONTROL_PLANE_PORT", "8765")
    health = verify_health(origin, token, REVISION, PACKAGE)
    verify_release(CURRENT.resolve(strict=True), REVISION, PACKAGE)
    database = Path(values["CONTROL_PLANE_DB"])
    initial = require_quiescent(database)
    require(initial["historical_action_families_sha256"] == "825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed", "HISTORICAL_EVIDENCE_CHANGED")
    overview = json_request(origin, token, "/v1/ui/overview")
    bindings = [row for row in overview["bindings"] if row.get("device_id") == DEVICE and row.get("workspace_id") == WORKSPACE and row.get("workspace_generation") == GENERATION and row.get("revoked_at_ms") is None]
    require(len(bindings) == 1 and bindings[0]["binding_id"] == BINDING, "EXACT_BINDING_CHANGED")
    registrations = [row for row in overview["workspace_registrations"] if row.get("device_id") == DEVICE and row.get("workspace_id") == WORKSPACE and row.get("workspace_generation") == GENERATION and row.get("retired_at_ms") is None]
    require(len(registrations) == 1 and registrations[0].get("display_name") == "Tools-Codex-web" and registrations[0]["capabilities"] == {"read": True, "write": True, "exec": True}, "CURRENT_REGISTRATION_CHANGED")
    grants = [row for row in overview["mcp_service_grants"] if row.get("grant_id") == GRANT]
    require(len(grants) == 1 and grants[0].get("principal_id") == PRINCIPAL and grants[0].get("revoked_at_ms") is None and set(grants[0]["scopes"]) == {"control-plane.inventory", "control-plane.read", "control-plane.patch"}, "EXISTING_SERVICE_GRANT_CHANGED")
    grant = grants[0]
    if MARKER.exists():
        receipt = json.loads(protected_file(MARKER))
        require(receipt.get("binding_id") == BINDING and receipt.get("source_revision") == REVISION and receipt.get("reason") == REASON, "RENEWAL_RECEIPT_MISMATCH")
        require(receipt["expires_at_ms"] == receipt["requested_at_ms"] + 3600000, "RENEWAL_RECEIPT_WINDOW_INVALID")
    else:
        require(overview["admission"]["admission_mode"] == "recovery", "RENEWAL_REQUIRES_CLOSED_INTAKE")
        require(not any(row.get("binding_id") == BINDING and row.get("closed_at_ms") is None and row["expires_at_ms"] > overview["observed_at_ms"] for row in overview["contexts"]), "UNEXPECTED_LIVE_CONTEXT")
        now = int(time.time() * 1000)
        receipt = {"source_revision": REVISION, "binding_id": BINDING, "requested_at_ms": now, "expires_at_ms": now + 3600000, "reason": REASON}
        atomic_bytes(MARKER, json.dumps(receipt, separators=(",", ":")).encode())
    expiry = receipt["expires_at_ms"]
    require(expiry > int(time.time() * 1000), "APPROVED_RENEWAL_WINDOW_EXPIRED")
    require(grant["expires_at_ms"] >= expiry, "EXISTING_SERVICE_GRANT_WINDOW_TOO_SHORT")
    require(not any(row.get("revoked_at_ms") is None and row.get("expires_at_ms", 0) > overview["observed_at_ms"] and (row.get("binding_id") != BINDING or row.get("principal_id") != PRINCIPAL or row["expires_at_ms"] != expiry) for row in overview["scoped_pilot_decisions"]), "UNRELATED_LIVE_PILOT")
    active = [row for row in overview["contexts"] if row.get("binding_id") == BINDING and row.get("closed_at_ms") is None and row["expires_at_ms"] > overview["observed_at_ms"]]
    require(len(active) <= 1 and all(row["expires_at_ms"] == expiry for row in active), "UNEXPECTED_ACTIVE_CONTEXT")
    require(overview["admission"]["admission_mode"] in ("recovery", "scoped_pilot"), "UNEXPECTED_ADMISSION_MODE")
    if not active:
        require(overview["admission"]["admission_mode"] == "recovery", "CONTEXT_CREATION_REQUIRES_CLOSED_INTAKE")
        target_context_ids = {row["context_id"] for row in overview["contexts"] if row.get("binding_id") == BINDING}
        require(all(row.get("delivery_state") == "settled" for row in overview.get("actions", []) if row.get("context_id") in target_context_ids), "UNSETTLED_CURRENT_BINDING_ACTION")
        for row in overview["contexts"]:
            if row.get("binding_id") == BINDING and row.get("closed_at_ms") is None:
                require(row["expires_at_ms"] <= overview["observed_at_ms"], "UNEXPIRED_CONTEXT_CLOSE_DENIED")
                json_request(origin, token, "/v1/contexts/" + row["context_id"] + "/close", {})
        context = json_request(origin, token, "/v1/contexts", {"binding_id": BINDING, "expires_at_ms": expiry})
    else:
        context = active[0]
    receipt["context_id"] = context["context_id"]
    atomic_bytes(MARKER, json.dumps(receipt, separators=(",", ":")).encode())
    overview = json_request(origin, token, "/v1/ui/overview")
    pilots = [row for row in overview["scoped_pilot_decisions"] if row.get("revoked_at_ms") is None and row["expires_at_ms"] > overview["observed_at_ms"]]
    require(len(pilots) <= 1 and all(row.get("binding_id") == BINDING and row.get("principal_id") == PRINCIPAL and row["expires_at_ms"] == expiry for row in pilots), "UNEXPECTED_LIVE_PILOT")
    if not pilots:
        require(overview["admission"]["admission_mode"] == "recovery", "PILOT_CREATION_REQUIRES_CLOSED_INTAKE")
        pilot = json_request(origin, token, "/v1/scoped-pilot-decisions", {"principal_id": PRINCIPAL, "binding_id": BINDING, "expires_at_ms": expiry, "reason": REASON})
    else:
        pilot = pilots[0]
    receipt["pilot_id"] = pilot["decision_id"]
    atomic_bytes(MARKER, json.dumps(receipt, separators=(",", ":")).encode())
    require_quiescent(database, expected=initial)
    if overview["admission"]["admission_mode"] == "recovery":
        json_request(origin, token, "/v1/maintenance/admission", {"mode": "scoped_pilot"})
    overview = json_request(origin, token, "/v1/ui/overview")
    require(overview["admission"]["admission_mode"] == "scoped_pilot", "SCOPED_PILOT_NOT_REOPENED")
    final_contexts = [row for row in overview["contexts"] if row.get("binding_id") == BINDING and row.get("closed_at_ms") is None and row["expires_at_ms"] > overview["observed_at_ms"]]
    final_pilots = [row for row in overview["scoped_pilot_decisions"] if row.get("revoked_at_ms") is None and row["expires_at_ms"] > overview["observed_at_ms"]]
    require(len(final_contexts) == 1 and final_contexts[0]["context_id"] == receipt["context_id"] and final_contexts[0]["expires_at_ms"] == expiry, "FINAL_CONTEXT_MISMATCH")
    require(len(final_pilots) == 1 and final_pilots[0]["decision_id"] == receipt["pilot_id"] and final_pilots[0]["binding_id"] == BINDING and final_pilots[0]["expires_at_ms"] == expiry, "FINAL_PILOT_MISMATCH")
    require([row for row in overview["mcp_service_grants"] if row.get("grant_id") == GRANT] == [grant], "SERVICE_GRANT_MUTATED")
    final = require_quiescent(database, expected=initial)
    receipt["completed_at_ms"] = overview["observed_at_ms"]
    atomic_bytes(MARKER, json.dumps(receipt, separators=(",", ":")).encode())
    emit("same_scope_renewal_complete", ok=True, source_revision=REVISION, binding_id=BINDING,
         context_id=receipt["context_id"], pilot_id=receipt["pilot_id"], requested_at_ms=receipt["requested_at_ms"], expires_at_ms=expiry,
         duration_ms=3600000, service_grant_preserved=GRANT, service_grant_scopes=grant["scopes"], service_grant_changed=False,
         policy_assignment={"device_id": DEVICE, "workspace_id": WORKSPACE, "workspace_generation": GENERATION, "context_id": receipt["context_id"], "expires_at_ms": expiry},
         admission="scoped_pilot", state=final, windows_policy_installed=False, exec_readiness_proven=False,
         next_action="INSTALL_SAME_SCOPE_WINDOWS_POLICY_AFTER_R7_ACTIVATION")
except Exception as error:
    emit("same_scope_renewal_failed", ok=False, code=error.code if isinstance(error, GuardFailure) else "RENEWAL_FAILED", next_action="INSPECT_PUBLIC_RENEWAL_RECEIPT_AND_CURRENT_CONTEXT_PILOT_BEFORE_RETRY")
    raise SystemExit(2) from None
finally:
    if lock_descriptor is not None:
        fcntl.flock(lock_descriptor, fcntl.LOCK_UN)
        os.close(lock_descriptor)
