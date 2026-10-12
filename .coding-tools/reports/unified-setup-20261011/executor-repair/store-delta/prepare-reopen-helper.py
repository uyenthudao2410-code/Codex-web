"""Prepare a snapshot-pinned observer/reopen helper; never execute remotely."""

import ast
import hashlib
import json
from pathlib import Path


out = Path(__file__).resolve().parent
packet = json.loads((out / "packet-manifest.json").read_bytes())
base_path = out.parent / "rollout-r9/ubuntu-r9-authority.py"
base = base_path.read_bytes()
assert hashlib.sha256(base).hexdigest() == "c86ff98e315651225a9f125132ce4ac4c84fe64a537d3021971d5333c9abf869"
prefix = base.decode().split("def save(marker: dict) -> None:", 1)[0]
prefix = prefix.replace('REVISION = "5ce5c51fc97584501d5d091e8c21df88250f55eb42e6e756384b234da8837b1f"',
                        'REVISION = "' + packet["source_revision"] + '"', 1)
prefix = prefix.replace('PACKAGE = "sha256:bb529f710342bf064fb5d2259ab1ad49e3733a6ca6db0c60b60ed67f119a7566"',
                        'PACKAGE = "' + packet["package_source_sha256"] + '"', 1)
prefix = prefix[prefix.index("from __future__") :]
prefix = '''"""Candidate Store observer and separately approved exact-scope reopen.

Observe is read-only. Reopen requires --execute and exact fresh service,
state, and activation pins. Recovery revokes the old pilot; replacement needs
the additional --replace-revoked-pilot flag. It retains the existing context,
grant, scope and expiry, never extends authority, restarts, deploys, restores
SQLite, revives a revoked decision, or replays a command. No secrets are output.
"""

''' + prefix
body = r'''
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
'''
tables = ("work_requests", "actions", "delivery_attempts", "receipts", "action_reconciliations",
          "action_dispatch_dispositions", "contexts", "mcp_task_sessions", "mcp_task_writer_leases",
          "mcp_patch_acceptances", "mcp_file_read_intents", "mcp_approved_patch_intents",
          "mcp_standing_patch_intents", "mcp_exec_intents", "mcp_artifact_intents",
          "mcp_document_write_intents", "mcp_read_only_intents")
insert = '        preserved_tables = ' + repr(tables) + '\n'
insert += '        rows = {table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid")] for table in preserved_tables}\n'
insert += '        result["preserved_action_task_context_families_sha256"] = digest(rows)\n'
needle = '        result["historical_action_families_sha256"] = digest(families)\n'
assert prefix.count(needle) == 1
prefix = prefix.replace(needle, needle + insert, 1)
helper = prefix + body
ast.parse(helper)
destination = out / "ubuntu-store-observe-reopen.py"
with destination.open("xb") as handle:
    handle.write(helper.encode())
receipt = {"operation": "guarded_store_observer_reopen_preparation", "source_revision": packet["source_revision"],
           "package_source_sha256": packet["package_source_sha256"], "helper_sha256": hashlib.sha256(helper.encode()).hexdigest(),
           "base_helper_sha256": hashlib.sha256(base).hexdigest(), "existing_context_id": "ctx_655e717e5c634cc1922d0f0d2e9d33c6",
           "revoked_pilot_to_preserve": "pilot_6c6dd3a9b03e4221af64068ff5ea0afd", "unchanged_expires_at_ms": 1791721156518,
           "replacement_pilot_requires_explicit_approval_flag": True, "authority_renewal": False,
           "remote_execution": False, "syntax": "pass"}
with (out / "reopen-helper-manifest.json").open("xb") as handle:
    handle.write((json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode())
print(json.dumps(receipt, sort_keys=True, indent=2))
