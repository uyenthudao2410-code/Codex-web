"""Local-only assembly from the frozen r10 helpers; never calls a service."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
PRIOR = OUT.parents[1] / "store-delta"
AUTH = (PRIOR / "ubuntu-r10-store-authority-v2-pinned.py").read_text(encoding="utf-8")
DEPLOY = (PRIOR / "ubuntu-store-rollout.py").read_text(encoding="utf-8")

def extract(source, name):
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.Assign)) and
                (getattr(n, "name", None) == name or isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)))
    return "\n".join(source.splitlines()[node.lineno - 1:node.end_lineno]) + "\n\n"

header = '''"""Shared, pinned r11 rollout utilities. Values from protected files are never printed."""
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
LOCAL_ROOT, LOCAL_PROFILE = r"E:\\Github\\Tools-Codex-web", "web-mcp-assistant"
REASON = "Owner-approved r11 initial verification: exact Tools-Codex-web read/edit/sandboxed exec for one 60-minute window"
'''
header += "\n".join(extract(AUTH, n) for n in ("BINDING", "DEVICE", "WORKSPACE", "GENERATION", "PRINCIPAL", "GRANT", "SCOPES", "FAMILY_DIGEST", "HISTORICAL_IDS", "QUERIES"))
common = header + "\n".join(extract(AUTH, n) for n in ("GuardFailure", "require", "emit", "digest", "protected_file", "environment", "api", "target", "renewed_authority", "save"))
common += "\n".join(extract(DEPLOY, n) for n in ("run", "run_json", "file_hash", "private_directory", "atomic_bytes", "atomic_current", "service_pid"))
state = extract(AUTH, "state")
state = state.replace('with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5) as connection:', 'with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5)) as connection:')
state = state.replace('result["unsettled_actions"] == 13', 'result["unsettled_actions"] == len(HISTORICAL_IDS)')
state = state.replace("protected_tables = ('work_requests'", "protected_tables = ('mcp_permission_requests', 'work_requests'")
state = state.replace('dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid")', 'normalize_row(dict(row)) for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid")')
state = state.replace('result["target_unsettled_actions"]', 'result["contexts_sha256"] = digest([dict(row) for row in connection.execute("SELECT * FROM contexts ORDER BY rowid")])\n        result["target_unsettled_actions"]', 1)
state = state.replace('result["schema_version"] == SCHEMA', 'result["schema_version"] in {28, 29}')
common += '''
def normalize_row(row):
    # The only migration delta is nullable plan columns; null must preserve legacy row fingerprints.
    if row.get("verification_json") is None:
        row.pop("verification_json", None)
    return row

''' + state
common += '''
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
'''
compile(common, "r11_common.py", "exec")
with (OUT / "r11_common.py").open("x", encoding="utf-8", newline="\n") as handle:
    handle.write(common)
print(json.dumps({"common_sha256": hashlib.sha256(common.encode()).hexdigest(), "prepared_only": True}))
