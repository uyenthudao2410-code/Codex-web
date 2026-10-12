"""Guarded pending-approval Store lookup Ubuntu rollout driver, executed by the authorized parent over SSH stdin.

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
BASE_REVISION = "5ce5c51fc97584501d5d091e8c21df88250f55eb42e6e756384b234da8837b1f"
BASE_PACKAGE = "sha256:bb529f710342bf064fb5d2259ab1ad49e3733a6ca6db0c60b60ed67f119a7566"
REVISION = "395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5"
PACKAGE = "sha256:83611914241508ad1f5ca96d017902cb6675fa15ea082f3aa4698f7cffe74419"
ARCHIVE_SHA256 = "bf76625554e32478202191c29ccdea0790448a47971db30af54a7aa5959d9061"
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
        preserved_tables = ('work_requests', 'actions', 'delivery_attempts', 'receipts', 'action_reconciliations', 'action_dispatch_dispositions', 'contexts', 'mcp_task_sessions', 'mcp_task_writer_leases', 'mcp_patch_acceptances', 'mcp_file_read_intents', 'mcp_approved_patch_intents', 'mcp_standing_patch_intents', 'mcp_exec_intents', 'mcp_artifact_intents', 'mcp_document_write_intents', 'mcp_read_only_intents')
        preserved_rows = {table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()] for table in preserved_tables}
        result["preserved_action_task_context_families_sha256"] = canonical_digest(preserved_rows)
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
    require(result["open_tasks"] == 0, "OPEN_TASKS_BLOCK_DEPLOYMENT")
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote-archive", required=True)
    parser.add_argument("--confirm-target", required=True)
    parser.add_argument("--confirm-revision", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    require(args.confirm_target == HOST and args.confirm_revision == REVISION, "EXPLICIT_TARGET_CONFIRMATION_MISMATCH")
    require(Path(args.remote_archive) == ARCHIVE, "REMOTE_ARCHIVE_TARGET_MISMATCH")
    require(os.name == "posix" and pwd.getpwuid(os.getuid()).pw_name == USER, "EXECUTION_HOST_OR_USER_MISMATCH")
    tailscale_addresses = run(["tailscale", "ip", "-4"], code="TAILSCALE_IDENTITY_UNAVAILABLE").decode().split()
    require(HOST in tailscale_addresses, "SERVER_ADDRESS_MISMATCH")
    require(CURRENT.is_symlink(), "CURRENT_IS_NOT_A_SYMLINK")
    old_link = os.readlink(CURRENT)
    baseline = CURRENT.resolve(strict=True)
    private_directory(RELEASES)
    old_env = protected_file(ENV_FILE)
    old_drop_in = protected_file(DROP_IN)
    values = parse_environment(old_env)
    require(values.get("CONTROL_PLANE_DECLARED_SOURCE_REVISION") == BASE_REVISION
            and values.get("CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256") == BASE_PACKAGE,
            "PROTECTED_BASELINE_IDENTITY_MISMATCH")
    database = Path(values["CONTROL_PLANE_DB"])
    token = values["CONTROL_PLANE_OPERATOR_TOKEN"]
    bind = values.get("CONTROL_PLANE_BIND", "127.0.0.1")
    if bind in {"0.0.0.0", "::"}:
        bind = "127.0.0.1"
    origin = f"http://{bind}:{int(values.get('CONTROL_PLANE_PORT', '8765'))}"
    validate_archive()
    baseline_receipt = verify_release(baseline, BASE_REVISION, BASE_PACKAGE)
    old_health = verify_health(origin, token, BASE_REVISION, BASE_PACKAGE)
    require(old_health["service_instance_id"] == "cp_d203277517b747e4b056ec0184d09709", "BASE_SERVICE_INSTANCE_CHANGED")
    old_pid = service_pid()
    launcher = run(["systemctl", "--user", "show", SERVICE, "--property=ExecStart", "--value"], code="SERVICE_COMMAND_UNAVAILABLE")
    require(str(CURRENT / "deploy/control-plane-launcher.sh").encode() in launcher, "SERVICE_LAUNCHER_MISMATCH")
    original_admission = json_request(origin, token, "/v1/maintenance/admission")["admission_mode"]
    require(original_admission == "scoped_pilot", "ORIGINAL_ADMISSION_NOT_SCOPED_PILOT")
    initial_counts = require_quiescent(database)
    require(initial_counts["historical_action_families_sha256"] == "825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed", "HISTORICAL_EVIDENCE_BASELINE_DRIFT")
    decisions = json_request(origin, token, "/v1/scoped-pilot-decisions")["scoped_pilot_decisions"]
    require(not any(row.get("revoked_at_ms") is None and row.get("expires_at_ms", 0) > int(time.time() * 1000) and (row.get("binding_id") != "bind_3e05bf64cb3e4bab93d930ae1692bebb" or row.get("principal_id") != "svcprn_cd98750c7c7e45678d201066dc1b7d7a") for row in decisions), "UNRELATED_LIVE_PILOT_BLOCKS_DEPLOYMENT")
    emit("preflight", ok=True, baseline=old_health, service_pid=old_pid, state=initial_counts,
         archive_sha256=ARCHIVE_SHA256, baseline_file_count=baseline_receipt["file_count"])
    if not args.execute:
        emit("preflight_complete", ok=True, remote_mutations=False)
        return 0

    import fcntl
    lock_descriptor = os.open(INSTALL / ".owner-acceptance-deployment.lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(lock_descriptor)
        raise GuardFailure("DEPLOYMENT_ALREADY_RUNNING") from None
    closed = configured = switched = restarted = False
    expected_env = expected_drop_in = None
    rollback = {}
    try:
        require(os.readlink(CURRENT) == old_link and protected_file(ENV_FILE) == old_env
                and protected_file(DROP_IN) == old_drop_in, "BASELINE_CONCURRENT_CHANGE")
        require_quiescent(database, expected=initial_counts)
        json_request(origin, token, "/v1/maintenance/admission", {"mode": "recovery"})
        closed = True
        require(json_request(origin, token, "/v1/maintenance/admission")["admission_mode"] == "recovery",
                "ADMISSION_NOT_CLOSED")
        require_quiescent(database, expected=initial_counts)
        emit("intake_closed", ok=True, admission="recovery", host=HOST, service=SERVICE, observed_at_ms=int(time.time() * 1000))
        private_directory(BACKUP_ROOT, create=True)
        backup_directory = BACKUP_ROOT / "store-lookup-395c786893172924"
        backup_directory.mkdir(mode=0o700)
        private_directory(backup_directory)
        atomic_bytes(backup_directory / "control-plane.env.before", old_env)
        atomic_bytes(backup_directory / "10-immutable-release.conf.before", old_drop_in)
        snapshot_path = backup_directory / "control-plane-before-hotfix.sqlite3"
        maintenance_environment = dict(os.environ, PYTHONPATH=str(baseline / "control-plane"), PYTHONDONTWRITEBYTECODE="1")
        snapshot = run_json(["/usr/bin/python3", "-B", "-m", "control_plane.maintenance", "snapshot", "--source", str(database),
                             "--destination", str(snapshot_path)], code="VERIFIED_BACKUP_FAILED", environment=maintenance_environment)
        os.chmod(snapshot_path, 0o600)
        inspection = run_json(["/usr/bin/python3", "-B", "-m", "control_plane.maintenance", "inspect-snapshot", "--source", str(snapshot_path),
                               "--expected-sha256", snapshot["snapshot_sha256"]], code="BACKUP_INSPECTION_FAILED", environment=maintenance_environment)
        require(inspection.get("sqlite_integrity") == "ok" and inspection.get("schema_version") == SCHEMA, "BACKUP_INTEGRITY_OR_SCHEMA_FAILED")
        require_quiescent(snapshot_path, expected=initial_counts)
        require_quiescent(database, expected=initial_counts)
        atomic_bytes(backup_directory / "snapshot-receipt.json", json.dumps(snapshot).encode())
        atomic_bytes(backup_directory / "inspection-receipt.json", json.dumps(inspection).encode())
        emit("backup_verified", ok=True, protected_backup_directory=str(backup_directory),
             snapshot_sha256=snapshot["snapshot_sha256"], schema_version=SCHEMA)
        candidate = extract_archive()
        candidate_receipt = verify_release(candidate, REVISION, PACKAGE)
        old_manifest = json.loads((baseline / "release-manifest.json").read_bytes())
        new_manifest = json.loads((candidate / "release-manifest.json").read_bytes())
        old_files = {row["path"]: row for row in old_manifest["files"]}
        new_files = {row["path"]: row for row in new_manifest["files"]}
        delta = [path for path in sorted(set(old_files) | set(new_files)) if old_files.get(path) != new_files.get(path)]
        require(delta == ["control-plane/control_plane/store.py"], "UNRELATED_RELEASE_DELTA")
        require(file_hash(baseline / delta[0]) == "99d3eba656a269886a842bc357a14222eb811bbb7dea8d0538c210d5f3edcf40" and file_hash(candidate / delta[0]) == "1d45615fff15e19dc50d4a7cead04b7566ed0acd87489f2ab5cd69adbc24a9e0", "FROZEN_STORE_DELTA_MISMATCH")
        require(canonical_digest(new_manifest["files"]) == REVISION, "SOURCE_SNAPSHOT_IDENTITY_MISMATCH")
        helper = candidate / "deploy/prepare-control-plane-activation.py"
        spec = importlib.util.spec_from_file_location("verified_activation_helper", helper)
        require(spec is not None and spec.loader is not None, "ACTIVATION_HELPER_UNAVAILABLE")
        activation = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(activation)
        expected_env_text = activation._replace_key(old_env.decode(), activation.REVISION_KEY, REVISION, environment=True)
        expected_env = activation._replace_key(expected_env_text, activation.FINGERPRINT_KEY, PACKAGE, environment=True).encode()
        expected_drop_text = activation._replace_key(old_drop_in.decode(), activation.REVISION_KEY, REVISION, environment=False)
        expected_drop_in = activation._replace_key(expected_drop_text, activation.FINGERPRINT_KEY, PACKAGE, environment=False).encode()
        helper_arguments = ["/usr/bin/python3", "-B", str(helper), "--release-dir", str(candidate), "--env-file", str(ENV_FILE), "--drop-in", str(DROP_IN)]
        check = run_json(helper_arguments + ["--check-only"], code="ACTIVATION_CHECK_FAILED")
        require(check.get("source_revision") == REVISION and check.get("package_source_sha256") == PACKAGE, "ACTIVATION_CHECK_IDENTITY_MISMATCH")
        require_quiescent(database, expected=initial_counts)
        require(protected_file(ENV_FILE) == old_env and protected_file(DROP_IN) == old_drop_in
                and os.readlink(CURRENT) == old_link, "CONFIGURATION_CONCURRENT_CHANGE")
        configured = True
        prepared = run_json(helper_arguments, code="ACTIVATION_PREPARATION_FAILED")
        require(prepared.get("environment_matches") is True and prepared.get("drop_in_matches") is True
                and protected_file(ENV_FILE) == expected_env and protected_file(DROP_IN) == expected_drop_in,
                "ACTIVATION_PREPARATION_MISMATCH")
        require_quiescent(database, expected=initial_counts)
        require(os.readlink(CURRENT) == old_link, "CURRENT_CONCURRENT_CHANGE")
        atomic_current(str(candidate))
        switched = True
        run(["systemctl", "--user", "daemon-reload"], code="SYSTEMD_RELOAD_FAILED")
        restarted = True
        run(["systemctl", "--user", "restart", SERVICE], code="SERVICE_RESTART_FAILED")
        new_health = wait_health(origin, token, REVISION, PACKAGE)
        new_pid = service_pid()
        require(new_pid != old_pid and new_health["service_instance_id"] != old_health["service_instance_id"]
                and new_health["started_at_ms"] > old_health["started_at_ms"], "NEW_SERVICE_INSTANCE_NOT_PROVEN")
        require(CURRENT.resolve() == candidate, "ACTIVATED_RELEASE_TARGET_MISMATCH")
        verify_release(candidate, REVISION, PACKAGE)
        final_counts = require_quiescent(database, expected=initial_counts)
        require(all(final_counts[key] == initial_counts[key] for key in ("actions", "tasks", "acceptances", "open_tasks")),
                "ACTION_OR_TASK_STATE_CHANGED")
        # recovery revokes old decisions. Renewal belongs to the parent; this
        # driver never creates a decision or opens the unscoped admission mode.
        active_decisions = [row for row in json_request(origin, token, "/v1/scoped-pilot-decisions")["scoped_pilot_decisions"]
                            if row.get("revoked_at_ms") is None and row.get("expires_at_ms", 0) > int(time.time() * 1000)]
        reopen_pending = len(active_decisions) != 1
        require(reopen_pending, "UNEXPECTED_LIVE_DECISION_AFTER_CLOSURE")
        final_admission = json_request(origin, token, "/v1/maintenance/admission")["admission_mode"]
        require(final_admission == "recovery", "FINAL_ADMISSION_MISMATCH")
        emit("deployment_complete", ok=True, source_revision=REVISION, package_source_sha256=PACKAGE,
             service_pid=new_pid, health=new_health, release_delta=delta, final_admission=final_admission,
             reopen_pending_owner_renewal=reopen_pending,
             next_action="SCOPED_PILOT_OWNER_RENEWAL_REQUIRED" if reopen_pending else "OWNER_ACCEPTANCE_EXISTING_VERIFIED_ACTION",
             file_count=candidate_receipt["file_count"], state=final_counts, database_restored=False, authority_renewed=False)
        return 0
    except Exception as error:
        failure_code = error.code if isinstance(error, GuardFailure) else "DEPLOYMENT_DRIVER_FAILED"
        try:
            if configured:
                require(protected_file(ENV_FILE) in (old_env, expected_env)
                        and protected_file(DROP_IN) in (old_drop_in, expected_drop_in), "ROLLBACK_CONFIG_CONCURRENT_CHANGE")
                atomic_bytes(ENV_FILE, old_env)
                atomic_bytes(DROP_IN, old_drop_in)
            if switched:
                require(os.readlink(CURRENT) in (old_link, str(candidate)), "ROLLBACK_CURRENT_CONCURRENT_CHANGE")
                atomic_current(old_link)
            if configured or switched or restarted:
                run(["systemctl", "--user", "daemon-reload"], code="ROLLBACK_SYSTEMD_RELOAD_FAILED")
                run(["systemctl", "--user", "restart", SERVICE], code="ROLLBACK_SERVICE_RESTART_FAILED")
            rollback_health = wait_health(origin, token, BASE_REVISION, BASE_PACKAGE)
            require_quiescent(database, expected=initial_counts)
            rollback = {"ok": True, "health": rollback_health, "admission": "recovery" if closed else original_admission,
                        "database_restored": False, "next_action": "OWNER_REVIEW_AND_SCOPED_PILOT_RENEWAL"}
        except Exception as rollback_error:
            rollback = {"ok": False, "code": rollback_error.code if isinstance(rollback_error, GuardFailure) else "ROLLBACK_FAILED",
                        "database_restored": False, "next_action": "OWNER_RECONCILE_CONFIG_CURRENT_AND_SERVICE_KEEP_INTAKE_CLOSED"}
        emit("deployment_failed", ok=False, code=failure_code, rollback=rollback)
        return 2
    finally:
        fcntl.flock(lock_descriptor, fcntl.LOCK_UN)
        os.close(lock_descriptor)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GuardFailure as error:
        emit("preflight_failed", ok=False, code=error.code, remote_mutations=False)
        raise SystemExit(2) from None
    except Exception:
        emit("preflight_failed", ok=False, code="DEPLOYMENT_PREFLIGHT_FAILED", remote_mutations=False)
        raise SystemExit(2) from None
