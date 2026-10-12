"""Candidate Store observer and separately approved exact-scope reopen.

Observe is read-only. Reopen requires --execute and exact fresh service,
state, and activation pins. Recovery revokes the old pilot; replacement needs
the additional --replace-revoked-pilot flag. It retains the existing context,
grant, scope and expiry, never extends authority, restarts, deploys, restores
SQLite, revives a revoked decision, or replays a command. No secrets are output.
"""

from __future__ import annotations

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
OPERATION_DIR = HOME_DIR / ".local/state/codex-control-plane/owner-operations/rollout-r9"
MARKER = OPERATION_DIR / "authority-renewal-public.json"
BINDING = "bind_3e05bf64cb3e4bab93d930ae1692bebb"
DEVICE = "72ceec2d-e3f2-472f-8e3c-99fffe053035"
WORKSPACE = "workspace_dda1d78e9a21402aa6213f72af64f788"
GENERATION = "generation_c2f13e8d02344cf6a38a3f42ecfa59b6"
PRINCIPAL = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
GRANT = "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"
SCOPES = {"control-plane.inventory", "control-plane.read", "control-plane.patch"}
FAMILY_DIGEST = "825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed"
REASON = "Owner-approved Windows r9 activation: same Tools-Codex-web read/write/sandboxed exec scope for 60 minutes"
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
        preserved_tables = ('work_requests', 'actions', 'delivery_attempts', 'receipts', 'action_reconciliations', 'action_dispatch_dispositions', 'contexts', 'mcp_task_sessions', 'mcp_task_writer_leases', 'mcp_patch_acceptances', 'mcp_file_read_intents', 'mcp_approved_patch_intents', 'mcp_standing_patch_intents', 'mcp_exec_intents', 'mcp_artifact_intents', 'mcp_document_write_intents', 'mcp_read_only_intents')
        rows = {table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid")] for table in preserved_tables}
        result["preserved_action_task_context_families_sha256"] = digest(rows)
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



PRIOR_MARKER = MARKER
OPERATION_DIR = HOME_DIR / ".local/state/codex-control-plane/owner-operations/store-lookup-395c786893172924"
MARKER = OPERATION_DIR / "reopen-public.json"
CONTEXT = "ctx_655e717e5c634cc1922d0f0d2e9d33c6"
OLD_PILOT = "pilot_6c6dd3a9b03e4221af64068ff5ea0afd"
EXPIRES = 1791721156518
REOPEN_REASON = "Owner-approved Store lookup deployment: replace revoked pilot for exact existing Tools-Codex-web scope and unchanged expiry"


def save(marker: dict) -> None:
    require(OPERATION_DIR.is_dir() and not OPERATION_DIR.is_symlink(), "OPERATION_DIRECTORY_UNSAFE")
    metadata = OPERATION_DIR.stat()
    require(metadata.st_uid == os.getuid() and stat.S_IMODE(metadata.st_mode) == 0o700, "OPERATION_DIRECTORY_ACL_INVALID")
    descriptor, temporary = tempfile.mkstemp(prefix=".reopen-", dir=OPERATION_DIR)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(json.dumps(marker, separators=(",", ":")).encode())
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, MARKER)
    finally:
        Path(temporary).unlink(missing_ok=True)


def existing_authority(overview: dict, grant: dict, *, require_live: bool) -> tuple[dict, dict]:
    prior = json.loads(protected_file(PRIOR_MARKER))
    require(prior.get("operation") == "owner_approved_r9_same_scope_60m"
            and prior.get("source_revision") == "5ce5c51fc97584501d5d091e8c21df88250f55eb42e6e756384b234da8837b1f"
            and prior.get("binding_id") == BINDING and prior.get("device_id") == DEVICE
            and prior.get("workspace_id") == WORKSPACE and prior.get("workspace_generation") == GENERATION
            and prior.get("context_id") == CONTEXT and prior.get("pilot_id") == OLD_PILOT
            and prior.get("expires_at_ms") == EXPIRES and prior.get("service_grant_sha256") == digest(grant),
            "EXISTING_AUTHORITY_OR_GRANT_CHANGED")
    contexts = [row for row in overview["contexts"] if row.get("context_id") == CONTEXT]
    pilots = [row for row in overview["scoped_pilot_decisions"] if row.get("decision_id") == OLD_PILOT]
    require(len(contexts) == 1 and len(pilots) == 1, "EXISTING_CONTEXT_OR_PILOT_MISSING")
    context, pilot = contexts[0], pilots[0]
    require(context.get("binding_id") == BINDING and context.get("device_id") == DEVICE
            and context.get("workspace_id") == WORKSPACE and context.get("workspace_generation") == GENERATION
            and context.get("expires_at_ms") == EXPIRES and context.get("closed_at_ms") is None,
            "EXISTING_CONTEXT_CHANGED")
    require(pilot.get("binding_id") == BINDING and pilot.get("principal_id") == PRINCIPAL
            and pilot.get("expires_at_ms") == EXPIRES and pilot.get("owner_id") == context.get("owner_id"),
            "EXISTING_PILOT_SCOPE_CHANGED")
    if require_live:
        require(overview["observed_at_ms"] < EXPIRES <= grant.get("expires_at_ms", 0),
                "AUTHORIZED_WINDOW_EXPIRED_NO_RENEWAL")
        live = [row for row in overview["contexts"] if row.get("binding_id") == BINDING
                and row.get("closed_at_ms") is None and row.get("expires_at_ms", 0) > overview["observed_at_ms"]]
        require(len(live) == 1 and live[0]["context_id"] == CONTEXT, "OTHER_LIVE_CONTEXT_BLOCKS_REOPEN")
    return context, pilot


def ready_node(overview: dict, expected_epoch: str | None, *, require_ready: bool) -> dict:
    nodes = [row for row in overview["nodes"] if row.get("device_id") == DEVICE]
    require(len(nodes) == 1, "NODE_NOT_UNIQUE")
    node = nodes[0]
    if require_ready:
        require(expected_epoch and node.get("activation_epoch") == expected_epoch, "EXPECTED_ACTIVATION_REQUIRED")
        require(0 <= overview["observed_at_ms"] - node.get("last_seen_at_ms", 0) < 60000
                and node.get("readiness") == "ready" and node.get("policy_state") == "enabled"
                and node.get("policy_expires_at_ms", 0) > overview["observed_at_ms"], "NODE_NOT_FRESH_READY")
    return node


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("observe", "reopen"), nargs="?", default="observe")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--replace-revoked-pilot", action="store_true")
    parser.add_argument("--expected-service-instance")
    parser.add_argument("--expected-state-sha256")
    parser.add_argument("--expected-activation-epoch")
    arguments = parser.parse_args()
    origin, token, database, health, snapshot, overview, grant = inspect()
    context, old_pilot = existing_authority(overview, grant, require_live=False)
    node = ready_node(overview, arguments.expected_activation_epoch, require_ready=False)
    if arguments.action == "observe" or not arguments.execute:
        emit("store_candidate_read_only_preflight", ok=True, remote_mutation=False,
             observed_at_ms=overview["observed_at_ms"], source_revision=REVISION, package_source_sha256=PACKAGE,
             service_instance_id=health["service_instance_id"], admission=overview["admission"]["admission_mode"],
             state=snapshot, state_sha256=digest(snapshot), context_id=CONTEXT, old_pilot_id=OLD_PILOT,
             old_pilot_revoked=old_pilot.get("revoked_at_ms") is not None, expires_at_ms=EXPIRES,
             remaining_ms=max(0, EXPIRES - overview["observed_at_ms"]), service_grant_preserved=GRANT,
             service_grant_sha256=digest(grant), service_grant_scopes=sorted(SCOPES),
             node={field: node.get(field) for field in ("device_id", "readiness", "policy_state", "policy_reason",
                    "policy_expires_at_ms", "last_seen_at_ms", "activation_epoch")})
        return
    require(arguments.expected_service_instance == health["service_instance_id"], "EXPECTED_SERVICE_INSTANCE_REQUIRED")
    require(arguments.expected_state_sha256 == digest(snapshot), "EXPECTED_QUIESCENT_STATE_REQUIRED")
    existing_authority(overview, grant, require_live=True)
    ready_node(overview, arguments.expected_activation_epoch, require_ready=True)
    require(old_pilot.get("revoked_at_ms") is not None, "EXPECTED_RECOVERY_REVOKED_PILOT_REQUIRED")
    require(arguments.replace_revoked_pilot, "SCOPED_PILOT_REPLACEMENT_APPROVAL_REQUIRED")
    descriptor = os.open(INSTALL / ".owner-acceptance-deployment.lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise GuardFailure("OWNER_OPERATION_ALREADY_RUNNING") from None
        require(state(database) == snapshot, "STATE_CHANGED_BEFORE_OWNER_LOCK")
        if MARKER.exists():
            marker = json.loads(protected_file(MARKER))
            require(marker.get("operation") == "store_deploy_same_expiry_reopen"
                    and marker.get("source_revision") == REVISION and marker.get("service_instance_id") == health["service_instance_id"]
                    and marker.get("state") == snapshot and marker.get("context_sha256") == digest(context)
                    and marker.get("old_pilot_sha256") == digest(old_pilot) and marker.get("grant_sha256") == digest(grant)
                    and marker.get("activation_epoch") == arguments.expected_activation_epoch and marker.get("expires_at_ms") == EXPIRES,
                    "REOPEN_MARKER_CHANGED")
        else:
            require(overview["admission"]["admission_mode"] == "recovery", "REOPEN_PREPARATION_REQUIRES_RECOVERY")
            require(not OPERATION_DIR.exists() and not OPERATION_DIR.is_symlink(), "OPERATION_DIRECTORY_ALREADY_EXISTS")
            OPERATION_DIR.mkdir(parents=True, mode=0o700)
            marker = {"operation": "store_deploy_same_expiry_reopen", "source_revision": REVISION,
                      "service_instance_id": health["service_instance_id"], "state": snapshot,
                      "context_sha256": digest(context), "old_pilot_sha256": digest(old_pilot), "grant_sha256": digest(grant),
                      "activation_epoch": arguments.expected_activation_epoch, "expires_at_ms": EXPIRES, "phase": "prepared"}
            save(marker)
        current = api(origin, token, "/v1/ui/overview")
        require(digest(target(current)) == digest(grant), "SERVICE_GRANT_CHANGED")
        fresh_context, fresh_old = existing_authority(current, grant, require_live=True)
        require(fresh_context == context and fresh_old == old_pilot, "AUTHORITY_CHANGED_DURING_REOPEN")
        ready_node(current, arguments.expected_activation_epoch, require_ready=True)
        live = [row for row in current["scoped_pilot_decisions"] if row.get("revoked_at_ms") is None
                and row.get("expires_at_ms", 0) > current["observed_at_ms"]]
        if live:
            require(len(live) == 1 and live[0].get("binding_id") == BINDING and live[0].get("principal_id") == PRINCIPAL
                    and live[0].get("expires_at_ms") == EXPIRES and live[0].get("reason") == REOPEN_REASON,
                    "UNEXPECTED_LIVE_PILOT")
            require(marker.get("pilot_id") in {None, live[0]["decision_id"]}, "REPLACEMENT_PILOT_ID_CHANGED")
            pilot = live[0]
        else:
            require(current["admission"]["admission_mode"] == "recovery" and marker.get("pilot_id") is None
                    and marker.get("phase") == "prepared", "REPLACEMENT_PILOT_NOT_REPLAYABLE")
            pilot = api(origin, token, "/v1/scoped-pilot-decisions", {"principal_id": PRINCIPAL, "binding_id": BINDING,
                        "expires_at_ms": EXPIRES, "reason": REOPEN_REASON})
        require(pilot.get("binding_id") == BINDING and pilot.get("principal_id") == PRINCIPAL
                and pilot.get("expires_at_ms") == EXPIRES and pilot.get("revoked_at_ms") is None
                and pilot.get("owner_id") == context.get("owner_id"), "REPLACEMENT_PILOT_SCOPE_CHANGED")
        marker.update(pilot_id=pilot["decision_id"], phase="pilot_ready")
        save(marker)
        require(state(database) == snapshot, "PILOT_CREATION_CHANGED_ACTION_TASK_CONTEXT_STATE")
        fresh = api(origin, token, "/v1/ui/overview")
        existing_authority(fresh, target(fresh), require_live=True)
        ready_node(fresh, arguments.expected_activation_epoch, require_ready=True)
        require(fresh["admission"]["admission_mode"] in {"recovery", "scoped_pilot"}, "REOPEN_ADMISSION_CHANGED")
        if fresh["admission"]["admission_mode"] == "recovery":
            api(origin, token, "/v1/maintenance/admission", {"mode": "scoped_pilot"})
        final_health = api(origin, token, "/healthz")
        require(final_health.get("admission_mode") == "scoped_pilot"
                and final_health.get("service_instance_id") == health["service_instance_id"]
                and final_health.get("declared_source_revision") == REVISION
                and final_health.get("package_source_sha256") == PACKAGE, "REOPEN_HEALTH_CHANGED")
        require(state(database) == snapshot, "REOPEN_CHANGED_ACTION_TASK_CONTEXT_STATE")
        final = api(origin, token, "/v1/ui/overview")
        require(digest(target(final)) == digest(grant), "SERVICE_GRANT_MUTATED")
        final_context, final_old = existing_authority(final, grant, require_live=True)
        require(final_context == context and final_old == old_pilot, "EXISTING_AUTHORITY_MUTATED")
        ready_node(final, arguments.expected_activation_epoch, require_ready=True)
        marker["phase"] = "intake_reopened"
        save(marker)
        emit("store_candidate_intake_reopened", ok=True, remote_mutation=True, source_revision=REVISION,
             package_source_sha256=PACKAGE, service_instance_id=health["service_instance_id"],
             admission="scoped_pilot", context_id=CONTEXT, old_pilot_id=OLD_PILOT, replacement_pilot_id=pilot["decision_id"],
             expires_at_ms=EXPIRES, authority_window_extended=False, service_grant_preserved=GRANT,
             service_grant_changed=False, state=snapshot, state_sha256=digest(snapshot),
             activation_epoch=arguments.expected_activation_epoch, service_restart=False, ubuntu_code_deployed=False)
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        emit("store_candidate_guarded_operation_failed", ok=False,
             code=error.code if isinstance(error, GuardFailure) else "STORE_REOPEN_OPERATION_FAILED",
             next_action="OBSERVE_CURRENT_SERVICE_AND_PRIVATE_REOPEN_MARKER_BEFORE_RETRY; NO_AUTHORITY_RENEWAL; KEEP_INTAKE_CLOSED_IF_INCOMPLETE")
        raise SystemExit(2) from None
