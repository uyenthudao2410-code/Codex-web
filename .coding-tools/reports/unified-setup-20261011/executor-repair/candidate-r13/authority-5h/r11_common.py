"""Shared, pinned r11 rollout utilities. Values from protected files are never printed."""
from __future__ import annotations
import argparse
from contextlib import closing
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import pwd
import re
import shlex
import sqlite3
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
sys.dont_write_bytecode = True
HOST, USER, SERVICE = "100.116.112.22", "svhome", "codex-control-plane.service"
HOME_DIR = Path("/home/svhome")
INSTALL = HOME_DIR / ".local/lib/codex-control-plane"
CURRENT, RELEASES, INCOMING = INSTALL / "current", INSTALL / "releases", INSTALL / "incoming"
ARTIFACT_DIR = Path(__file__).resolve().parent
ENV_FILE = HOME_DIR / ".config/codex-control-plane/control-plane.env"
DROP_IN = HOME_DIR / ".config/systemd/user/codex-control-plane.service.d/10-immutable-release.conf"
BACKUP_ROOT = HOME_DIR / ".local/state/codex-control-plane/deployment-backups"
OPERATION_DIR = HOME_DIR / ".local/state/codex-control-plane/owner-operations/r11-initial-verification-60m"
MARKER = OPERATION_DIR / "authority-renewal-public.json"
BASE_REVISION = "395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5"
BASE_PACKAGE = "sha256:83611914241508ad1f5ca96d017902cb6675fa15ea082f3aa4698f7cffe74419"
REVISION = "9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c"
PACKAGE = "sha256:80a2e82115714f8e5e32cc7144e180b1f83ee8738e2af1e4821de8048128f7e8"
RECOVERY_REVISION = "81303f7cf4d006c5e6e2eeaffb578b57446b9dbd6730c9f34b2a7bec98b8c0cb"
RECOVERY_PACKAGE = "sha256:a3cdac42954c17199888bb85c32631ada4da55682cb62d57101999da1989bf8a"
RELEASE_NAME = "codex-control-plane-" + REVISION
ARCHIVE = INCOMING / (RELEASE_NAME + ".tar.gz")
IDENTITIES = {
 BASE_REVISION: {"package": BASE_PACKAGE, "schema": 28, "manifest": "c608465e22c2a1e4f5801cf93cb416c5bec9c66b412834f0bfed619a1f01ec8d"},
 REVISION: {"package": PACKAGE, "schema": 29, "manifest": "a9ecac2d8935cd36790ee08a49be090446a2458a10d7a4bf542f825e34e14e55", "archive": "7d1a0b015208b4fc257a52bc888cd8a15f559ce33cf04846953d533002b7c273"},
 RECOVERY_REVISION: {"package": RECOVERY_PACKAGE, "schema": 29, "manifest": "0b9bbc26d22f46dc4004be4b8150fdb72a06f870941a8b680344f5bd9d11ddd2", "archive": "7059225a0c7663b0a28899afc3d8603d496af85fb3d32789a5b8a9a2d055b3fc"}}
LOCAL_ROOT, LOCAL_PROFILE = r"E:\Github\Tools-Codex-web", "web-mcp-assistant"
REASON = "Owner-approved r11 initial verification: exact Tools-Codex-web read/edit/sandboxed exec for one 60-minute window"
BINDING = "bind_3e05bf64cb3e4bab93d930ae1692bebb"


DEVICE = "72ceec2d-e3f2-472f-8e3c-99fffe053035"


WORKSPACE = "workspace_dda1d78e9a21402aa6213f72af64f788"


GENERATION = "generation_c2f13e8d02344cf6a38a3f42ecfa59b6"


PRINCIPAL = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"


GRANT = "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"


SCOPES = {"control-plane.inventory", "control-plane.read", "control-plane.patch"}


FAMILY_DIGEST = "825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed"


HISTORICAL_IDS = (
    "act_048df93488874a70aa97a7ee18ccbd03", "act_0f0a49c6424d42d3bc7bc49ad46e4ffa",
    "act_3764695f2cb24c0d9b6968d850316938", "act_6e513ba70ec640259621fefd5c41a721",
    "act_744496c6bd514d38a746cf8819aae9ad", "act_79f4c19cdc214151b701e11f7be6f9a7",
    "act_8b03301c00854a0a8747139835b0c72d", "act_8c6adfb23b434c838b06ce15e5972429",
    "act_95f2504bd6d04690944e2c79754c8ab2", "act_98db4071326d448ea39a4784eb967b4b",
    "act_b7523c58039d4f8a9f097b4b2d36e948", "act_dc23860c42a746c2bea9d9b6ee7c7f11",
    "act_fd27acab6b684d98825d326c1aff3276",
)


QUERIES = {
    "unsettled_actions": "SELECT COUNT(*) FROM actions WHERE delivery_state!='settled'",
    "queued_actions": "SELECT COUNT(*) FROM actions WHERE delivery_state='queued'",
    "accepted_actions": "SELECT COUNT(*) FROM actions WHERE delivery_state='accepted'",
    "open_writers": "SELECT COUNT(*) FROM mcp_task_writer_leases WHERE released_at_ms IS NULL",
    "open_tasks": "SELECT COUNT(*) FROM mcp_task_sessions WHERE closed_at_ms IS NULL",
    "actions": "SELECT COUNT(*) FROM actions",
    "tasks": "SELECT COUNT(*) FROM mcp_task_sessions",
    "acceptances": "SELECT COUNT(*) FROM mcp_patch_acceptances",
    "unsettled_acceptances": "SELECT COUNT(*) FROM mcp_patch_acceptances p JOIN actions a ON a.action_id=p.action_id WHERE a.delivery_state!='settled'",
}

class GuardFailure(Exception):
    def __init__(self, code: str):
        self.code = code


def require(condition: bool, code: str) -> None:
    if not condition:
        raise GuardFailure(code)


def emit(phase: str, **fields: object) -> None:
    print(json.dumps({"phase": phase, **fields}, separators=(",", ":")), flush=True)


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def protected_file(path: Path) -> bytes:
    require(not path.is_symlink() and path.is_file(), "PROTECTED_FILE_UNSAFE")
    metadata = path.stat()
    require(metadata.st_uid == os.getuid() and stat.S_IMODE(metadata.st_mode) == 0o600,
            "PROTECTED_FILE_OWNER_OR_MODE_MISMATCH")
    return path.read_bytes()


def environment() -> dict[str, str]:
    values = {}
    for line in protected_file(ENV_FILE).decode().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, raw = line.split("=", 1)
        require(key.strip() not in values, "DUPLICATE_ENVIRONMENT_KEY")
        parts = shlex.split(raw, comments=True)
        require(len(parts) <= 1, "ENVIRONMENT_VALUE_INVALID")
        values[key.strip()] = parts[0] if parts else ""
    require(values.get("CONTROL_PLANE_MCP_SERVICE_EXEC_ENABLED") == "true", "EXEC_CONFIGURATION_CHANGED")
    return values


def api(origin: str, token: str, route: str, body: dict | None = None) -> dict:
    request = urllib.request.Request(origin + route,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        method="GET" if body is None else "POST")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.load(response)
    except (OSError, ValueError, urllib.error.URLError):
        raise GuardFailure("CONTROL_PLANE_API_FAILED") from None
    require(isinstance(result, dict), "CONTROL_PLANE_API_INVALID")
    return result


def target(overview: dict) -> dict:
    bindings = [row for row in overview["bindings"] if row.get("device_id") == DEVICE
                and row.get("workspace_id") == WORKSPACE and row.get("workspace_generation") == GENERATION
                and row.get("revoked_at_ms") is None]
    require(len(bindings) == 1 and bindings[0]["binding_id"] == BINDING, "EXACT_BINDING_CHANGED")
    registrations = [row for row in overview["workspace_registrations"] if row.get("device_id") == DEVICE
        and row.get("workspace_id") == WORKSPACE and row.get("workspace_generation") == GENERATION
        and row.get("retired_at_ms") is None]
    require(len(registrations) == 1 and registrations[0].get("display_name") == "Tools-Codex-web"
            and registrations[0].get("capabilities") == {"read": True, "write": True, "exec": True},
            "WORKSPACE_SCOPE_CHANGED")
    grants = [row for row in overview["mcp_service_grants"] if row.get("grant_id") == GRANT]
    require(len(grants) == 1 and grants[0].get("principal_id") == PRINCIPAL
            and grants[0].get("revoked_at_ms") is None and set(grants[0]["scopes"]) == SCOPES,
            "SERVICE_GRANT_CHANGED")
    require(not any(row.get("revoked_at_ms") is None and row["expires_at_ms"] > overview["observed_at_ms"]
                    and (row.get("binding_id") != BINDING or row.get("principal_id") != PRINCIPAL)
                    for row in overview["scoped_pilot_decisions"]), "UNRELATED_LIVE_PILOT")
    return grants[0]


def renewed_authority(overview: dict, marker: dict) -> None:
    now = overview["observed_at_ms"]
    expiry = marker.get("expires_at_ms")
    require(isinstance(expiry, int) and expiry == marker.get("requested_at_ms", 0) + 18000000 and now < expiry,
            "RENEWAL_WINDOW_EXPIRED_OR_INVALID")
    contexts = [row for row in overview["contexts"] if row.get("binding_id") == BINDING
                and row.get("closed_at_ms") is None and row["expires_at_ms"] > now]
    pilots = [row for row in overview["scoped_pilot_decisions"] if row.get("revoked_at_ms") is None
              and row["expires_at_ms"] > now]
    require(len(contexts) == 1 and contexts[0]["context_id"] == marker.get("context_id")
            and contexts[0]["device_id"] == DEVICE and contexts[0]["workspace_id"] == WORKSPACE
            and contexts[0]["workspace_generation"] == GENERATION and contexts[0]["expires_at_ms"] == expiry,
            "RENEWED_CONTEXT_CHANGED")
    require(len(pilots) == 1 and pilots[0]["decision_id"] == marker.get("pilot_id")
            and pilots[0]["binding_id"] == BINDING and pilots[0]["principal_id"] == PRINCIPAL
            and pilots[0]["device_id"] == DEVICE and pilots[0]["workspace_id"] == WORKSPACE
            and pilots[0]["workspace_generation"] == GENERATION and pilots[0]["expires_at_ms"] == expiry,
            "RENEWED_PILOT_CHANGED")


def save(marker: dict) -> None:
    require(OPERATION_DIR.is_dir() and not OPERATION_DIR.is_symlink(), "OPERATION_DIRECTORY_UNSAFE")
    metadata = OPERATION_DIR.stat()
    require(metadata.st_uid == os.getuid() and stat.S_IMODE(metadata.st_mode) == 0o700, "OPERATION_DIRECTORY_ACL_INVALID")
    descriptor, temporary = tempfile.mkstemp(prefix=".authority-", dir=OPERATION_DIR)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(json.dumps(marker, separators=(",", ":")).encode())
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, MARKER)
    finally:
        Path(temporary).unlink(missing_ok=True)

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


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def private_directory(path: Path, *, create: bool = False) -> None:
    if create and not path.exists():
        path.mkdir(parents=True, mode=0o700)
    require(not path.is_symlink() and path.is_dir(), "PRIVATE_DIRECTORY_UNSAFE")
    metadata = path.stat()
    require(metadata.st_uid == os.getuid() and stat.S_IMODE(metadata.st_mode) == 0o700,
            "PRIVATE_DIRECTORY_OWNER_OR_MODE_MISMATCH")


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


def service_pid() -> int:
    active = run(["systemctl", "--user", "is-active", SERVICE], code="SERVICE_NOT_ACTIVE").strip()
    require(active == b"active", "SERVICE_NOT_ACTIVE")
    raw = run(["systemctl", "--user", "show", SERVICE, "--property=MainPID", "--value"], code="SERVICE_PID_FAILED")
    require(raw.strip().isdigit() and int(raw) > 0, "SERVICE_PID_INVALID")
    return int(raw)


def normalize_row(row):
    # The only migration delta is nullable plan columns; null must preserve legacy row fingerprints.
    if row.get("verification_json") is None:
        row.pop("verification_json", None)
    return row

def state(database: Path) -> dict:
    require(database.is_absolute() and database.is_file() and not database.is_symlink(), "DATABASE_TARGET_UNSAFE")
    require(not database.resolve().is_relative_to(INSTALL.resolve()), "DATABASE_INSIDE_RELEASE")
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5)) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        result = {key: int(connection.execute(query).fetchone()[0]) for key, query in QUERIES.items()}
        result["schema_version"] = int(connection.execute("PRAGMA user_version").fetchone()[0])
        actions = [dict(row) for row in connection.execute(
            "SELECT * FROM actions WHERE delivery_state!='settled' ORDER BY action_id")]
        require(tuple(row["action_id"] for row in actions) == HISTORICAL_IDS, "UNFENCED_UNSETTLED_ACTIONS")
        families = []
        for action in actions:
            family = {"action": action}
            for table, ordering in (("delivery_attempts", "attempt_number, attempt_id"),
                ("receipts", "received_at_ms, receipt_id"), ("action_reconciliations", "action_id"),
                ("action_dispatch_dispositions", "action_id")):
                family[table] = [dict(row) for row in connection.execute(
                    f"SELECT * FROM {table} WHERE action_id=? ORDER BY {ordering}", (action["action_id"],))]
            families.append(family)
        result["historical_action_families_sha256"] = digest(families)
        protected_tables = ('mcp_permission_requests', 'work_requests', 'actions', 'delivery_attempts', 'receipts', 'action_reconciliations', 'action_dispatch_dispositions', 'mcp_task_sessions', 'mcp_task_writer_leases', 'mcp_patch_acceptances', 'mcp_file_read_intents', 'mcp_approved_patch_intents', 'mcp_standing_patch_intents', 'mcp_exec_intents', 'mcp_artifact_intents', 'mcp_document_write_intents', 'mcp_read_only_intents')
        protected_rows = {table: [normalize_row(dict(row)) for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid")] for table in protected_tables}
        result["all_action_task_intent_families_sha256"] = digest(protected_rows)
        result["patch_acceptances_sha256"] = digest([dict(row) for row in connection.execute(
            "SELECT * FROM mcp_patch_acceptances ORDER BY action_id")])
        result["contexts_sha256"] = digest([dict(row) for row in connection.execute("SELECT * FROM contexts ORDER BY rowid")])
        result["target_unsettled_actions"] = int(connection.execute(
            "SELECT COUNT(*) FROM actions WHERE binding_id=? AND delivery_state!='settled'", (BINDING,)).fetchone()[0])
    require(result["schema_version"] in {28, 29}, "DATABASE_SCHEMA_CHANGED")
    require(result["historical_action_families_sha256"] == FAMILY_DIGEST and result["unsettled_actions"] == len(HISTORICAL_IDS),
            "HISTORICAL_FAMILY_CHANGED")
    require(all(result[field] == 0 for field in ("queued_actions", "accepted_actions", "open_writers",
            "open_tasks", "unsettled_acceptances", "target_unsettled_actions")), "SYSTEM_NOT_QUIESCENT")
    return result


def verify_release(release, revision):
    identity = IDENTITIES[revision]
    require(release.is_dir() and release.is_relative_to(RELEASES.resolve()), "RELEASE_TARGET_UNSAFE")
    require(file_hash(release / "release-manifest.json") == identity["manifest"], "RELEASE_MANIFEST_CHANGED")
    verified = run_json(["/usr/bin/python3", "-B", str(release / "deploy/control-plane-verify-release.py"), "--release-dir", str(release)], code="RELEASE_INTEGRITY_FAILED")
    require(verified.get("source_revision") == revision and verified.get("package_source_sha256") == identity["package"]
            and verified.get("control_plane_schema_version") == identity["schema"] and verified.get("file_count") == 38, "RELEASE_IDENTITY_CHANGED")
    return verified

def inspect():
    require(os.name == "posix" and pwd.getpwuid(os.getuid()).pw_name == USER, "EXECUTION_USER_MISMATCH")
    require(HOST in run(["tailscale", "ip", "-4"], code="TAILSCALE_IDENTITY_UNAVAILABLE").decode().split(), "SERVER_ADDRESS_MISMATCH")
    service_pid()
    values = environment()
    bind = values.get("CONTROL_PLANE_BIND", "127.0.0.1")
    require(bind in {"127.0.0.1", "0.0.0.0", "::", HOST}, "SERVICE_BIND_CHANGED")
    origin = "http://" + (HOST if bind == HOST else "127.0.0.1") + ":" + values.get("CONTROL_PLANE_PORT", "8765")
    token = values["CONTROL_PLANE_OPERATOR_TOKEN"]
    health = api(origin, token, "/healthz")
    revision = health.get("declared_source_revision")
    require(revision in IDENTITIES, "SERVICE_SOURCE_NOT_PINNED")
    identity = IDENTITIES[revision]
    require(health.get("ok") is True and health.get("schema_version") == identity["schema"]
            and health.get("package_source_sha256") == identity["package"] and health.get("expected_package_source_sha256") == identity["package"], "SERVICE_HEALTH_OR_SOURCE_CHANGED")
    require(re.fullmatch(r"cp_[a-f0-9]{32}", str(health.get("service_instance_id") or "")), "SERVICE_INSTANCE_INVALID")
    require(values.get("CONTROL_PLANE_DECLARED_SOURCE_REVISION") == revision
            and values.get("CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256") == identity["package"], "PROTECTED_CONFIG_SOURCE_CHANGED")
    require(CURRENT.is_symlink(), "CURRENT_NOT_SYMLINK")
    release = CURRENT.resolve(strict=True)
    verify_release(release, revision)
    database = Path(values["CONTROL_PLANE_DB"])
    snapshot = state(database)
    require(snapshot["schema_version"] == identity["schema"], "DATABASE_SERVICE_SCHEMA_MISMATCH")
    overview = api(origin, token, "/v1/ui/overview")
    grant = target(overview)
    return origin, token, database, health, snapshot, overview, grant

def compare_history(before, after, *, migration=False, authority=False):
    expected = dict(before)
    actual = dict(after)
    if migration:
        expected.pop("schema_version"); actual.pop("schema_version")
    if authority:
        expected.pop("contexts_sha256"); actual.pop("contexts_sha256")
    require(expected == actual, "ACTION_TASK_PERMISSION_OR_HISTORY_CHANGED")

def public_observation(health, snapshot, overview, grant):
    nodes = [row for row in overview["nodes"] if row.get("device_id") == DEVICE]
    require(len(nodes) == 1, "NODE_NOT_UNIQUE")
    return {"observed_at_ms": overview["observed_at_ms"], "service_instance_id": health["service_instance_id"],
            "source_revision": health["declared_source_revision"], "package_source_sha256": health["package_source_sha256"],
            "admission": overview["admission"]["admission_mode"], "state": snapshot, "state_sha256": digest(snapshot),
            "binding_id": BINDING, "service_grant_sha256": digest(grant), "service_grant_preserved": GRANT,
            "service_grant_scopes": sorted(SCOPES), "node": {k: nodes[0].get(k) for k in ("device_id", "readiness", "policy_state", "policy_reason", "policy_expires_at_ms", "last_seen_at_ms", "activation_epoch", "runtime_instance_id", "mcp_server_instance_id", "contract_version")},
            "target_contexts": [{k: r.get(k) for k in ("context_id", "expires_at_ms", "closed_at_ms")} for r in overview["contexts"] if r.get("binding_id") == BINDING],
            "target_pilots": [{k: r.get(k) for k in ("decision_id", "expires_at_ms", "revoked_at_ms")} for r in overview["scoped_pilot_decisions"] if r.get("binding_id") == BINDING]}

def guard_arguments(args, health, snapshot, grant):
    require(args.operator_approved and args.confirm_target == HOST, "EXPLICIT_R11_TARGET_APPROVAL_REQUIRED")
    require(args.expected_service_instance == health["service_instance_id"], "EXPECTED_SERVICE_INSTANCE_REQUIRED")
    require(args.expected_state_sha256 == digest(snapshot), "EXPECTED_FRESH_QUIESCENT_STATE_REQUIRED")
    require(args.expected_grant_sha256 == digest(grant), "EXPECTED_UNCHANGED_GRANT_REQUIRED")
    require(type(args.observed_at_ms) is int and 0 <= int(time.time()*1000) - args.observed_at_ms < 60000, "EXPECTED_OBSERVATION_NOT_FRESH")

def operation_lock():
    path = INSTALL / ".owner-acceptance-deployment.lock"
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        metadata = os.fstat(descriptor)
        current = path.lstat()
        require(stat.S_ISREG(metadata.st_mode) and metadata.st_uid == os.getuid()
                and stat.S_IMODE(metadata.st_mode) == 0o600 and not stat.S_ISLNK(current.st_mode)
                and (metadata.st_dev, metadata.st_ino) == (current.st_dev, current.st_ino), "OWNER_LOCK_TARGET_UNSAFE")
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return descriptor
    except Exception:
        if "descriptor" in locals(): os.close(descriptor)
        raise GuardFailure("OWNER_LOCK_UNSAFE_OR_ALREADY_RUNNING") from None

def arguments(parser):
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--operator-approved", action="store_true")
    parser.add_argument("--confirm-target", default=HOST)
    parser.add_argument("--expected-service-instance")
    parser.add_argument("--expected-state-sha256")
    parser.add_argument("--expected-grant-sha256")
    parser.add_argument("--observed-at-ms", type=int)
