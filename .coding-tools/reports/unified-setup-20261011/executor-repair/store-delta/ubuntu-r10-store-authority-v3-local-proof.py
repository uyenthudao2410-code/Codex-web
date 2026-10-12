"""Pending-approval r10 + Store395 exact-scope authority helper.

Default/observe is read-only. Mutations require --execute, --operator-approved,
fresh exact service/state pins and the unchanged prior grant digest. Reopen
requires the fresh r10 activation epoch and a ready node; close/renew can
prepare authority from a fresh owner-transmitted, independently pinned local r9 proof.
A stale/unreported central predecessor is never relabeled ready, and no old agent is started.
One protected operation marker anchors exactly one 60-minute context/pilot
window at the first renewal; retries never extend it or create duplicates.
Only supported owner APIs close the prior owner context, revoke prior pilots,
create one replacement context/pilot, and reopen scoped_pilot. No deployment,
restart, SQL data writes, local standing-policy changes, standalone Sandbox
probe, command replay, pending RUN acceptance, or credential output occurs.
"""

from __future__ import annotations

import sys
from datetime import datetime

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shlex
import sqlite3
import stat
import subprocess
import tempfile
import time
import urllib.error
import urllib.request


HOST = "100.116.112.22"
USER = "svhome"
SERVICE = "codex-control-plane.service"
REVISION = "395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5"
PACKAGE = "sha256:83611914241508ad1f5ca96d017902cb6675fa15ea082f3aa4698f7cffe74419"
SCHEMA = 28
HOME_DIR = Path("/home/svhome")
INSTALL = HOME_DIR / ".local/lib/codex-control-plane"
CURRENT = INSTALL / "current"
RELEASES = INSTALL / "releases"
ENV_FILE = HOME_DIR / ".config/codex-control-plane/control-plane.env"
OPERATION_DIR = HOME_DIR / ".local/state/codex-control-plane/owner-operations/r10-store395-60m-v3-local-proof"
PREDECESSOR_EPOCH = "activation-mv3qe36p-991f11f44f47d32ea2e217b1db882ff7"
PRIOR_R9_MARKER = HOME_DIR / ".local/state/codex-control-plane/owner-operations/rollout-r9/authority-renewal-public.json"
PRIOR_CONTEXT = "ctx_655e717e5c634cc1922d0f0d2e9d33c6"
MARKER = OPERATION_DIR / "authority-renewal-public.json"
BINDING = "bind_3e05bf64cb3e4bab93d930ae1692bebb"
DEVICE = "72ceec2d-e3f2-472f-8e3c-99fffe053035"
WORKSPACE = "workspace_dda1d78e9a21402aa6213f72af64f788"
GENERATION = "generation_c2f13e8d02344cf6a38a3f42ecfa59b6"
PRINCIPAL = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
GRANT = "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"
SCOPES = {"control-plane.inventory", "control-plane.read", "control-plane.patch"}
FAMILY_DIGEST = "825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed"
REASON = "Owner-approved Windows r10 activation and Store395 deployment: same exact Tools-Codex-web read/write/sandboxed exec scope for one 60-minute window"
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


def run(arguments: list[str], code: str) -> bytes:
    try:
        completed = subprocess.run(arguments, capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise GuardFailure(code) from None
    require(completed.returncode == 0, code)
    return completed.stdout


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


def state(database: Path) -> dict:
    require(database.is_absolute() and database.is_file() and not database.is_symlink(), "DATABASE_TARGET_UNSAFE")
    require(not database.resolve().is_relative_to(INSTALL.resolve()), "DATABASE_INSIDE_RELEASE")
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5) as connection:
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
        protected_tables = ('work_requests', 'actions', 'delivery_attempts', 'receipts', 'action_reconciliations', 'action_dispatch_dispositions', 'mcp_task_sessions', 'mcp_task_writer_leases', 'mcp_patch_acceptances', 'mcp_file_read_intents', 'mcp_approved_patch_intents', 'mcp_standing_patch_intents', 'mcp_exec_intents', 'mcp_artifact_intents', 'mcp_document_write_intents', 'mcp_read_only_intents')
        protected_rows = {table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid")] for table in protected_tables}
        result["all_action_task_intent_families_sha256"] = digest(protected_rows)
        result["patch_acceptances_sha256"] = digest([dict(row) for row in connection.execute(
            "SELECT * FROM mcp_patch_acceptances ORDER BY action_id")])
        result["target_unsettled_actions"] = int(connection.execute(
            "SELECT COUNT(*) FROM actions WHERE binding_id=? AND delivery_state!='settled'", (BINDING,)).fetchone()[0])
    require(result["schema_version"] == SCHEMA, "DATABASE_SCHEMA_CHANGED")
    require(result["historical_action_families_sha256"] == FAMILY_DIGEST and result["unsettled_actions"] == 13,
            "HISTORICAL_FAMILY_CHANGED")
    require(all(result[field] == 0 for field in ("queued_actions", "accepted_actions", "open_writers",
            "open_tasks", "unsettled_acceptances", "target_unsettled_actions")), "SYSTEM_NOT_QUIESCENT")
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


def inspect() -> tuple[str, str, Path, dict, dict, dict, dict]:
    require(pwd.getpwuid(os.getuid()).pw_name == USER, "EXECUTION_USER_MISMATCH")
    require(HOST in run(["tailscale", "ip", "-4"], "TAILSCALE_IDENTITY_UNAVAILABLE").decode().split(), "SERVER_ADDRESS_MISMATCH")
    require(run(["systemctl", "--user", "is-active", SERVICE], "SERVICE_NOT_ACTIVE").strip() == b"active", "SERVICE_NOT_ACTIVE")
    values = environment()
    bind = values.get("CONTROL_PLANE_BIND", "127.0.0.1")
    require(bind in {"127.0.0.1", "0.0.0.0", "::", HOST}, "SERVICE_BIND_CHANGED")
    origin = "http://" + (HOST if bind == HOST else "127.0.0.1") + ":" + values.get("CONTROL_PLANE_PORT", "8765")
    token = values["CONTROL_PLANE_OPERATOR_TOKEN"]
    health = api(origin, token, "/healthz")
    require(health.get("ok") is True and health.get("schema_version") == SCHEMA, "SERVICE_HEALTH_FAILED")
    require(health.get("declared_source_revision") == REVISION
            and health.get("package_source_sha256") == PACKAGE
            and health.get("expected_package_source_sha256") == PACKAGE, "SERVICE_SOURCE_CHANGED")
    require(isinstance(health.get("service_instance_id"), str)
            and re.fullmatch(r"cp_[a-f0-9]{32}", health["service_instance_id"]), "SERVICE_INSTANCE_INVALID")
    release = CURRENT.resolve(strict=True)
    require(release.is_dir() and release.is_relative_to(RELEASES.resolve()), "RELEASE_TARGET_UNSAFE")
    verified = json.loads(run(["/usr/bin/python3", "-B", str(release / "deploy/control-plane-verify-release.py"),
                              "--release-dir", str(release)], "RELEASE_INTEGRITY_FAILED"))
    require(verified.get("source_revision") == REVISION and verified.get("package_source_sha256") == PACKAGE
            and verified.get("control_plane_schema_version") == SCHEMA, "RELEASE_IDENTITY_CHANGED")
    database = Path(values["CONTROL_PLANE_DB"])
    snapshot = state(database)
    overview = api(origin, token, "/v1/ui/overview")
    grant = target(overview)
    return origin, token, database, health, snapshot, overview, grant


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


def marker_identity(marker: dict, health: dict, snapshot: dict, grant: dict) -> None:
    require(marker.get("operation") == "owner_approved_r10_store395_same_scope_60m_v3_local_proof" and marker.get("source_revision") == REVISION
            and marker.get("binding_id") == BINDING and marker.get("device_id") == DEVICE
            and marker.get("workspace_id") == WORKSPACE and marker.get("workspace_generation") == GENERATION
            and marker.get("reason") == REASON, "MARKER_IDENTITY_CHANGED")
    require(marker.get("service_instance_id") == health["service_instance_id"], "SERVICE_RESTARTED_DURING_OPERATION")
    require(marker.get("initial_state") == snapshot, "ACTION_TASK_ACCEPTANCE_OR_HISTORY_CHANGED")
    require(marker.get("service_grant_sha256") == digest(grant), "SERVICE_GRANT_MUTATED")


def renewed_authority(overview: dict, marker: dict) -> None:
    now = overview["observed_at_ms"]
    expiry = marker.get("expires_at_ms")
    require(isinstance(expiry, int) and expiry == marker.get("requested_at_ms", 0) + 3600000 and now < expiry,
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



LOCAL_ROOT = r"E:\Github\Tools-Codex-web"
LOCAL_HEAD = "2c554f59cb7b8ffc86ce5e0e28076c792777642f"
LOCAL_PARITY = "c9f6fe1313b6004519a61bebf3f8f173a74cfd1d563bef48fce87908ed72f57c"
LOCAL_PACKAGE = {"archive_sha256": "3bc75601041ef35b9fd894878b9f1905117512e3fc6f74d6102575b0f1edb226",
                 "executable_sha256": "fadc2feb4bb566b3fa22f22ea918c7175f39fa6b74eb7ccb9d2a1d6bab1b6211"}
LOCAL_DESCRIPTOR = {"installation_id": "e65d60602938af2f1c6e8cd9e8c59352ff2a5e24a268a45a98114726cdd8210d",
    "instance_id": "6006092b7a061f47b20a0b27c1f34f1d", "owner_pid": 1128,
    "owner_process_start_token": "134361911908524600"}
LOCAL_PROCESSES = {"owner": {"pid": 1128, "process_start_token": "134361911908524600"},
    "ui": {"pid": 25296, "process_start_token": "134361911886531150"},
    "native": {"pid": 9212, "process_start_token": "134361911931895600"}}
LOCAL_PENDING = {"run_id": "95e909f0040a448faa9f1f3257e2ee2c", "wave_id": "c101beadfc6d4f2fbc13845052c84693",
    "run_record_sha256": "a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590",
    "wave_record_sha256": "59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce", "unchanged": True}
LOCAL_DURABLE = {"activation_epoch_id": PREDECESSOR_EPOCH,
    "operation_id": "full-clean-mv3qdvfq-a83d4dacc8a5de0588fb6ba5", "state": "READY", "admission_state": "OPEN",
    "ready_commit_digest": "f85415b88bd6b9b1442a40fbb308d69d6aa4d7e0a8c9ee690a86ef5a5f22fe3e"}
LOCAL_RAW_EPOCH = {**{key: value for key, value in LOCAL_DURABLE.items() if key != "admission_state"},
                   "admission_open": True, "update_incomplete": False}
LOCAL_POLICY_HASHES = {"file_read": "62bd90f00fc6ab196afe07ddea82996a22a2686cd82e7d3c83c12914f99df6e6",
    "approved_patch": "3e78ebb89ab90ef2b33964d922bd1294c17fd741c218322cf4efb4ee7f574d2b",
    "exec": "31125fd75f5147770eecde7b926e3c46efd1f5ee83a55b58d180f8b200966367"}
LOCAL_ARGV_HASH = "6c67e3aa54d9dae49c41feff2d2b5c56100760b60cdef6a2a4eca392d9063597"
OTHER_VARIANT_MARKERS = tuple(HOME_DIR / ".local/state/codex-control-plane/owner-operations" / name / "authority-renewal-public.json"
    for name in ("r10-store395-60m-v2-pinned", "r10-store395-60m-v2", "r10-store395-60m"))


def partial_exact(value: object, expected: dict, code: str) -> None:
    require(isinstance(value, dict) and all(type(value.get(key)) is type(item) and value.get(key) == item
            for key, item in expected.items()), code)


def validate_local_preparation(raw: bytes, expected_sha: object, *, now_ms: int) -> dict:
    require(isinstance(expected_sha, str) and re.fullmatch(r"[a-f0-9]{64}", expected_sha) is not None,
            "EXPECTED_LOCAL_PREPARATION_SHA256_REQUIRED")
    require(0 < len(raw) <= 131072 and hashlib.sha256(raw).hexdigest() == expected_sha,
            "LOCAL_PREPARATION_BYTES_CHANGED")
    try:
        proof = json.loads(raw)
        require(isinstance(proof, dict), "LOCAL_PREPARATION_SCHEMA_INVALID")
        timestamp = str(proof.get("observed_at") or "")
        require(timestamp.endswith("Z"), "LOCAL_PREPARATION_TIMESTAMP_INVALID")
        observed = int(datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp() * 1000)
    except (ValueError, TypeError, OverflowError):
        raise GuardFailure("LOCAL_PREPARATION_SCHEMA_INVALID") from None
    require(0 <= now_ms - observed < 60000, "LOCAL_PREPARATION_NOT_FRESH")
    partial_exact(proof, {"kind": "r9_local_authority_preparation_v1", "schema_version": 1,
        "repository_head": LOCAL_HEAD, "parity_sha256": LOCAL_PARITY,
        "runtime_mutated": False, "server_mutated": False, "sandbox_probe_performed": False},
        "LOCAL_PREPARATION_SCHEMA_OR_SOURCE_CHANGED")
    partial_exact(proof.get("target"), {"binding_id": BINDING, "device_id": DEVICE, "workspace_id": WORKSPACE,
        "workspace_generation": GENERATION, "root": LOCAL_ROOT, "profile": "web-mcp-assistant"}, "LOCAL_TARGET_CHANGED")
    partial_exact((proof.get("packages") or {}).get("r9"), LOCAL_PACKAGE, "LOCAL_PACKAGE_CHANGED")
    partial_exact(proof.get("descriptor"), LOCAL_DESCRIPTOR, "LOCAL_DESCRIPTOR_CHANGED")
    for role, expected in LOCAL_PROCESSES.items():
        partial_exact(proof.get(role), {**expected, "state": "live"}, "LOCAL_" + role.upper() + "_IDENTITY_CHANGED")
    require(proof.get("ui_instance_id") == "2d80b88288e54bcc40f86f6ad45adcf6", "LOCAL_UI_INSTANCE_CHANGED")
    partial_exact(proof.get("agent"), {"state": "absent", "pid": 7108}, "OLD_AGENT_MUST_REMAIN_ABSENT")
    partial_exact(proof.get("durable"), LOCAL_DURABLE, "LOCAL_DURABLE_READY_CHANGED")
    partial_exact(proof.get("raw_epoch"), LOCAL_RAW_EPOCH, "LOCAL_RAW_EPOCH_CHANGED")
    partial_exact(proof.get("pending_acceptance"), LOCAL_PENDING, "LOCAL_PENDING_ACCEPTANCE_CHANGED")
    policies = proof.get("policies")
    require(isinstance(policies, dict) and policies.get("workspace_root_verified") is True
            and policies.get("standalone_probe_performed") is False, "LOCAL_POLICY_OBSERVATION_INVALID")
    for role, policy_hash in LOCAL_POLICY_HASHES.items():
        partial_exact(policies.get(role), {"state": "enabled", "enabled": True, "workspace_id": WORKSPACE,
            "workspace_generation": GENERATION, "policy_sha256": policy_hash}, "LOCAL_STANDING_POLICY_CHANGED")
    partial_exact(policies.get("exec"), {"allowed_argv_prefix_count": 6,
        "allowed_argv_prefixes_sha256": LOCAL_ARGV_HASH}, "LOCAL_EXEC_ALLOWLIST_CHANGED")
    census = proof.get("census")
    require(isinstance(census, dict) and census.get("ledger_mutated") is False
            and census.get("content_free") is True, "LOCAL_CENSUS_INVALID")
    partial_exact(census.get("counts"), {key: 0 for key in ("active_tool_calls", "active_commands", "starting_commands",
        "active_background_operations", "active_managed_processes", "foreign_heavy_processes", "active_agent_lanes")},
        "LOCAL_ACTIVE_JOB_OR_LANE")
    partial_exact(census.get("lifecycle"), {"unexplained_active_runs": 0, "unbound_live_resource_residues": 0,
        "projection_drift": False, "awaiting_acceptance_runs": [LOCAL_PENDING["run_id"]],
        "live_owned_runs": [], "active_p5_runs": [], "blockers": ["live_runtime_state_process"]}, "LOCAL_LIFECYCLE_CHANGED")
    partial_exact(census, {"safe": False, "code": "RUNTIME_BUSY", "reason": "live_runtime_state_process"},
        "LOCAL_CENSUS_BOUNDARY_CHANGED")
    require((census.get("snapshot") or {}).get("integrity_check") == ["ok"]
            and re.fullmatch(r"[a-f0-9]{64}", str((census.get("snapshot") or {}).get("logical_sha256") or "")) is not None,
            "LOCAL_LEDGER_INTEGRITY_INVALID")
    vm = proof.get("vm_zero_proof")
    partial_exact(vm, {"phase": "independent_vm_zero_proof", "ok": True,
        "vm_termination_performed": False, "sandbox_probe_performed": False}, "LOCAL_VM_ZERO_PROOF_INVALID")
    for role, observer in (("host", "GetProcessWindowsSandbox"), ("daemon", "CimMxcBackend")):
        row = vm.get(role)
        partial_exact(row, {"observer": observer, "count": 0, "content_free": True}, "LOCAL_VM_NOT_ZERO")
        require(type(row.get("begun_at_ms")) is int and type(row.get("observed_at_ms")) is int
                and 0 <= now_ms - row["observed_at_ms"] < 60000
                and row["begun_at_ms"] <= row["observed_at_ms"] <= observed,
                "LOCAL_VM_ZERO_OBSERVATION_NOT_FRESH")
    return {"sha256": expected_sha, "observed_at_ms": observed, "proof": proof}


def persist_local_preparation(raw: bytes, preparation: dict) -> None:
    destination = OPERATION_DIR / ("local-preparation-" + preparation["sha256"] + ".json")
    if destination.exists():
        require(protected_file(destination) == raw, "LOCAL_PROOF_ARCHIVE_CHANGED")
        return
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("observe", "close", "renew", "reopen"), nargs="?", default="observe")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--operator-approved", action="store_true")
    parser.add_argument("--expected-service-instance")
    parser.add_argument("--expected-state-sha256")
    parser.add_argument("--expected-activation-epoch")
    parser.add_argument("--local-preparation-stdin", action="store_true")
    parser.add_argument("--expected-local-preparation-sha256")
    arguments = parser.parse_args()
    origin, token, database, health, snapshot, overview, grant = inspect()
    if arguments.action == "observe" or not arguments.execute:
        nodes = [row for row in overview["nodes"] if row.get("device_id") == DEVICE]
        require(len(nodes) == 1, "NODE_NOT_UNIQUE")
        node = nodes[0]
        emit("r10_store_read_only_preflight", ok=True, remote_mutation=False, observed_at_ms=overview["observed_at_ms"],
             service_instance_id=health["service_instance_id"], source_revision=REVISION, package_source_sha256=PACKAGE,
             admission=overview["admission"]["admission_mode"], state=snapshot, state_sha256=digest(snapshot),
             binding_id=BINDING, service_grant_preserved=GRANT, service_grant_scopes=sorted(SCOPES),
             node={field: node.get(field) for field in ("device_id", "readiness", "policy_state", "policy_reason",
                    "policy_expires_at_ms", "last_seen_at_ms", "activation_epoch")},
             target_contexts=[{field: row.get(field) for field in ("context_id", "expires_at_ms", "closed_at_ms")}
                              for row in overview["contexts"] if row.get("binding_id") == BINDING],
             target_pilots=[{field: row.get(field) for field in ("decision_id", "expires_at_ms", "revoked_at_ms")}
                            for row in overview["scoped_pilot_decisions"] if row.get("binding_id") == BINDING])
        return
    require(arguments.operator_approved, "EXPLICIT_R10_STORE_60M_OWNER_APPROVAL_REQUIRED")
    require(arguments.expected_service_instance == health["service_instance_id"], "EXPECTED_SERVICE_INSTANCE_REQUIRED")
    local_preparation = None
    local_preparation_raw = b""
    if arguments.action in {"close", "renew"}:
        require(arguments.expected_activation_epoch == PREDECESSOR_EPOCH and arguments.local_preparation_stdin,
                "EXACT_LOCAL_R9_PREPARATION_REQUIRED")
        local_preparation_raw = sys.stdin.buffer.read(131073)
        local_preparation = validate_local_preparation(local_preparation_raw,
            arguments.expected_local_preparation_sha256, now_ms=int(time.time() * 1000))
    else:
        require(arguments.expected_activation_epoch and arguments.expected_activation_epoch != PREDECESSOR_EPOCH,
                "NEW_R10_ACTIVATION_REQUIRED_FOR_REOPEN")
    prior_r9 = json.loads(protected_file(PRIOR_R9_MARKER))
    require(prior_r9.get("operation") == "owner_approved_r9_same_scope_60m"
            and prior_r9.get("binding_id") == BINDING and prior_r9.get("device_id") == DEVICE
            and prior_r9.get("workspace_id") == WORKSPACE and prior_r9.get("workspace_generation") == GENERATION
            and prior_r9.get("context_id") == PRIOR_CONTEXT and prior_r9.get("service_grant_sha256") == digest(grant),
            "EXISTING_R9_SCOPE_OR_GRANT_CHANGED")
    require(arguments.expected_state_sha256 == digest(snapshot), "EXPECTED_QUIESCENT_STATE_REQUIRED")
    descriptor = os.open(INSTALL / ".owner-acceptance-deployment.lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise GuardFailure("OWNER_OPERATION_ALREADY_RUNNING") from None
        require(state(database) == snapshot, "STATE_CHANGED_BEFORE_OWNER_LOCK")
        if MARKER.exists():
            marker = json.loads(protected_file(MARKER))
            marker_identity(marker, health, snapshot, grant)
            require(marker.get("operator_approved") is True and marker.get("predecessor_epoch") == PREDECESSOR_EPOCH,
                    "OPERATOR_APPROVAL_OR_PREDECESSOR_MARKER_CHANGED")
        else:
            require(arguments.action == "close", "CLOSE_PREPARATION_REQUIRED")
            require(not any(path.exists() for path in OTHER_VARIANT_MARKERS), "OTHER_VARIANT_MARKER_EXISTS_DO_NOT_REANCHOR")
            unclosed_contexts = [row for row in overview["contexts"] if row.get("binding_id") == BINDING
                                and row.get("closed_at_ms") is None]
            require(all(row.get("context_id") == PRIOR_CONTEXT for row in unclosed_contexts),
                    "UNEXPECTED_UNCLOSED_CONTEXTS_BLOCK_AUTHORITY_RENEWAL")
            require(not OPERATION_DIR.exists() and not OPERATION_DIR.is_symlink(), "OPERATION_DIRECTORY_ALREADY_EXISTS")
            OPERATION_DIR.mkdir(parents=True, mode=0o700)
            marker = {"operation": "owner_approved_r10_store395_same_scope_60m_v3_local_proof", "source_revision": REVISION,
                "binding_id": BINDING, "device_id": DEVICE, "workspace_id": WORKSPACE, "workspace_generation": GENERATION,
                "reason": REASON, "service_instance_id": health["service_instance_id"], "initial_state": snapshot,
                "operator_approved": True, "predecessor_epoch": PREDECESSOR_EPOCH,
                "service_grant_sha256": digest(grant), "phase": "close_prepared",
                "old_context_ids": [row["context_id"] for row in overview["contexts"] if row.get("binding_id") == BINDING
                                    and row.get("context_id") == PRIOR_CONTEXT and row.get("closed_at_ms") is None],
                "old_pilot_ids": [row["decision_id"] for row in overview["scoped_pilot_decisions"]
                                  if row.get("binding_id") == BINDING and row.get("principal_id") == PRINCIPAL
                                  and row.get("revoked_at_ms") is None]}
            save(marker)
        if local_preparation is not None:
            require(0 <= int(time.time() * 1000) - local_preparation["observed_at_ms"] < 60000,
                    "LOCAL_PREPARATION_EXPIRED_BEFORE_OWNER_MUTATION")
            persist_local_preparation(local_preparation_raw, local_preparation)
            if "initial_local_preparation_sha256" not in marker:
                marker["initial_local_preparation_sha256"] = local_preparation["sha256"]
            marker["local_preparation_sha256"] = local_preparation["sha256"]
            marker["local_preparation_observed_at_ms"] = local_preparation["observed_at_ms"]
            save(marker)
        if arguments.action == "close":
            require(marker["phase"] in {"close_prepared", "intake_closed"}, "CLOSE_PHASE_CHANGED")
            require(overview["admission"]["admission_mode"] in {"scoped_pilot", "recovery"}, "ADMISSION_MODE_CHANGED")
            if overview["admission"]["admission_mode"] != "recovery":
                api(origin, token, "/v1/maintenance/admission", {"mode": "recovery"})
            require(api(origin, token, "/healthz")["admission_mode"] == "recovery", "INTAKE_NOT_CLOSED")
            require(state(database) == snapshot, "INTAKE_CLOSE_CHANGED_ACTION_STATE")
            marker["phase"] = "intake_closed"
            save(marker)
        elif arguments.action == "renew":
            require(marker["phase"] in {"intake_closed", "renewal_prepared", "authority_renewed"}, "RENEW_PHASE_CHANGED")
            require(overview["admission"]["admission_mode"] == "recovery", "RENEWAL_REQUIRES_CLOSED_INTAKE")
            if "expires_at_ms" not in marker:
                marker.update(requested_at_ms=int(time.time() * 1000), phase="renewal_prepared")
                marker["expires_at_ms"] = marker["requested_at_ms"] + 3600000
                save(marker)
            expiry = marker["expires_at_ms"]
            require(expiry > int(time.time() * 1000) and expiry <= grant["expires_at_ms"], "RENEWAL_OR_SERVICE_GRANT_WINDOW_INVALID")
            for context_id in marker["old_context_ids"]:
                rows = [row for row in overview["contexts"] if row["context_id"] == context_id and row.get("binding_id") == BINDING]
                require(len(rows) == 1, "OLD_CONTEXT_TARGET_CHANGED")
                if rows[0]["closed_at_ms"] is None:
                    api(origin, token, "/v1/contexts/" + context_id + "/close", {})
            for pilot_id in marker["old_pilot_ids"]:
                rows = [row for row in overview["scoped_pilot_decisions"] if row["decision_id"] == pilot_id
                        and row.get("binding_id") == BINDING and row.get("principal_id") == PRINCIPAL]
                require(len(rows) == 1, "OLD_PILOT_TARGET_CHANGED")
                if rows[0]["revoked_at_ms"] is None:
                    api(origin, token, "/v1/scoped-pilot-decisions/" + pilot_id + "/revoke", {})
            overview = api(origin, token, "/v1/ui/overview")
            contexts = [row for row in overview["contexts"] if row.get("binding_id") == BINDING
                        and row.get("closed_at_ms") is None and row["expires_at_ms"] > overview["observed_at_ms"]]
            require(len(contexts) <= 1 and all(row["expires_at_ms"] == expiry for row in contexts), "UNEXPECTED_ACTIVE_CONTEXT")
            context = contexts[0] if contexts else api(origin, token, "/v1/contexts", {"binding_id": BINDING, "expires_at_ms": expiry})
            marker["context_id"] = context["context_id"]
            save(marker)
            overview = api(origin, token, "/v1/ui/overview")
            pilots = [row for row in overview["scoped_pilot_decisions"] if row.get("revoked_at_ms") is None
                      and row["expires_at_ms"] > overview["observed_at_ms"]]
            require(len(pilots) <= 1 and all(row["binding_id"] == BINDING and row["principal_id"] == PRINCIPAL
                    and row["expires_at_ms"] == expiry and row.get("reason") == REASON for row in pilots), "UNEXPECTED_LIVE_PILOT")
            pilot = pilots[0] if pilots else api(origin, token, "/v1/scoped-pilot-decisions", {
                "principal_id": PRINCIPAL, "binding_id": BINDING, "expires_at_ms": expiry, "reason": REASON})
            marker["pilot_id"] = pilot["decision_id"]
            save(marker)
            renewed_authority(api(origin, token, "/v1/ui/overview"), marker)
            require(state(database) == snapshot, "RENEWAL_CHANGED_ACTION_TASK_OR_ACCEPTANCE_STATE")
            marker["phase"] = "authority_renewed"
            save(marker)
        else:
            require(marker["phase"] in {"authority_renewed", "intake_reopened"}, "REOPEN_PHASE_CHANGED")
            require(arguments.expected_activation_epoch and marker.get("activation_epoch") in {None, arguments.expected_activation_epoch},
                    "EXPECTED_R10_ACTIVATION_OR_REOPEN_MARKER_CHANGED")
            renewed_authority(overview, marker)
            nodes = [row for row in overview["nodes"] if row.get("device_id") == DEVICE]
            require(len(nodes) == 1, "NODE_NOT_UNIQUE")
            node = nodes[0]
            require(arguments.expected_activation_epoch and node.get("activation_epoch") == arguments.expected_activation_epoch,
                    "EXPECTED_R10_ACTIVATION_REQUIRED")
            require(0 <= overview["observed_at_ms"] - node.get("last_seen_at_ms", 0) < 60000
                    and node.get("readiness") == "ready" and node.get("policy_state") == "enabled"
                    and node.get("policy_expires_at_ms", 0) > overview["observed_at_ms"], "R10_NODE_NOT_FRESH_READY")
            require(overview["admission"]["admission_mode"] in {"recovery", "scoped_pilot"}, "REOPEN_ADMISSION_CHANGED")
            if overview["admission"]["admission_mode"] == "recovery":
                api(origin, token, "/v1/maintenance/admission", {"mode": "scoped_pilot"})
            require(api(origin, token, "/healthz")["admission_mode"] == "scoped_pilot", "INTAKE_NOT_REOPENED")
            require(state(database) == snapshot, "REOPEN_CHANGED_ACTION_TASK_OR_ACCEPTANCE_STATE")
            marker["phase"] = "intake_reopened"
            marker["activation_epoch"] = arguments.expected_activation_epoch
            save(marker)
        final_health = api(origin, token, "/healthz")
        require(final_health["service_instance_id"] == marker["service_instance_id"], "SERVICE_RESTARTED_DURING_OPERATION")
        final_overview = api(origin, token, "/v1/ui/overview")
        require(digest(target(final_overview)) == marker["service_grant_sha256"], "SERVICE_GRANT_MUTATED")
        emit({"intake_closed": "intake_closed", "authority_renewed": "same_scope_renewal_complete",
              "intake_reopened": "intake_reopened"}[marker["phase"]], ok=True, remote_mutation=True, source_revision=REVISION,
             host=HOST, service=SERVICE, observed_at_ms=final_overview["observed_at_ms"],
             service_instance_id=marker["service_instance_id"], service_restart=False, ubuntu_code_deployed=False,
             admission=final_health["admission_mode"], binding_id=BINDING, state=snapshot,
             requested_at_ms=marker.get("requested_at_ms"), expires_at_ms=marker.get("expires_at_ms"),
             context_id=marker.get("context_id"), pilot_id=marker.get("pilot_id"), duration_ms=3600000,
             local_preparation_sha256=marker.get("local_preparation_sha256"),
             local_preparation_observed_at_ms=marker.get("local_preparation_observed_at_ms"),
             initial_local_preparation_sha256=marker.get("initial_local_preparation_sha256"),
             policy_assignment=None if marker.get("context_id") is None else {
                 "device_id": DEVICE, "workspace_id": WORKSPACE, "workspace_generation": GENERATION,
                 "context_id": marker["context_id"], "expires_at_ms": marker["expires_at_ms"]},
             service_grant_preserved=GRANT, service_grant_changed=False, activation_epoch=marker.get("activation_epoch"))
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        emit("r10_store_guarded_operation_failed", ok=False,
             code=error.code if isinstance(error, GuardFailure) else "R10_STORE_OPERATION_FAILED",
             next_action="INSPECT_PUBLIC_MARKER_AND_CURRENT_STATE_BEFORE_RETRY; KEEP_INTAKE_CLOSED_ON_INCOMPLETE_RENEWAL")
        raise SystemExit(2) from None
