"""Exact-target 60m owner API driver. Observe is read-only; root executes live actions."""
from r11_common import *

OPERATION = "owner_approved_r11_initial_verification_60m"

def marker_check(marker, snapshot, grant):
    require(marker.get("operation") == OPERATION and marker.get("binding_id") == BINDING
            and marker.get("device_id") == DEVICE and marker.get("workspace_id") == WORKSPACE
            and marker.get("workspace_generation") == GENERATION and marker.get("root") == LOCAL_ROOT
            and marker.get("profile") == LOCAL_PROFILE and marker.get("service_grant_sha256") == digest(grant), "R11_MARKER_OR_GRANT_CHANGED")
    compare_history(marker["initial_state"], snapshot, migration=True, authority=marker.get("phase") in {"renewal_prepared", "authority_renewed", "intake_reopened"})

def renew(origin, token, overview, marker, grant):
    require(overview["admission"]["admission_mode"] == "recovery", "RENEW_REQUIRES_CLOSED_INTAKE")
    if "expires_at_ms" not in marker:
        marker.update(requested_at_ms=int(time.time()*1000), phase="renewal_prepared")
        marker["expires_at_ms"] = marker["requested_at_ms"] + 3600000
        save(marker)
    expiry = marker["expires_at_ms"]
    require(type(expiry) is int and expiry == marker["requested_at_ms"] + 3600000
            and int(time.time()*1000) < expiry <= grant["expires_at_ms"], "WINDOW_OR_SERVICE_GRANT_EXPIRED")
    for context_id in marker["old_context_ids"]:
        rows = [r for r in overview["contexts"] if r.get("context_id") == context_id and r.get("binding_id") == BINDING]
        require(len(rows) == 1, "OLD_CONTEXT_CHANGED")
        if rows[0].get("closed_at_ms") is None:
            api(origin, token, "/v1/contexts/" + context_id + "/close", {})
    overview = api(origin, token, "/v1/ui/overview")
    contexts = [r for r in overview["contexts"] if r.get("binding_id") == BINDING and r.get("closed_at_ms") is None]
    require(len(contexts) <= 1 and all(r["expires_at_ms"] == expiry for r in contexts), "UNEXPECTED_UNCLOSED_CONTEXT")
    context = contexts[0] if contexts else api(origin, token, "/v1/contexts", {"binding_id": BINDING, "expires_at_ms": expiry})
    marker["context_id"] = context["context_id"]
    save(marker)
    overview = api(origin, token, "/v1/ui/overview")
    pilots = [r for r in overview["scoped_pilot_decisions"] if r.get("revoked_at_ms") is None]
    require(len(pilots) <= 1 and all(r.get("binding_id") == BINDING and r.get("principal_id") == PRINCIPAL
            and r["expires_at_ms"] == expiry and r.get("reason") == REASON for r in pilots), "UNEXPECTED_UNREVOKED_PILOT")
    pilot = pilots[0] if pilots else api(origin, token, "/v1/scoped-pilot-decisions", {
        "principal_id": PRINCIPAL, "binding_id": BINDING, "expires_at_ms": expiry, "reason": REASON})
    marker["pilot_id"] = pilot["decision_id"]
    save(marker)
    renewed_authority(api(origin, token, "/v1/ui/overview"), marker)
    marker["phase"] = "authority_renewed"
    save(marker)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("observe", "close", "renew", "reopen"), nargs="?", default="observe")
    arguments(parser)
    for field in ("activation-epoch", "runtime-instance", "mcp-instance", "contract-version"):
        parser.add_argument("--expected-" + field)
    args = parser.parse_args()
    origin, token, database, health, snapshot, overview, grant = inspect()
    if args.action == "observe" or not args.execute:
        emit("r11_read_only_observation", ok=True, remote_mutation=False, **public_observation(health, snapshot, overview, grant))
        return
    guard_arguments(args, health, snapshot, grant)
    require(health["declared_source_revision"] == (BASE_REVISION if args.action == "close" else REVISION), "R11_AUTHORITY_SOURCE_PHASE_CHANGED")
    descriptor = operation_lock()
    try:
        require(state(database) == snapshot, "STATE_CHANGED_BEFORE_OWNER_LOCK")
        if MARKER.exists():
            marker = json.loads(protected_file(MARKER))
            marker_check(marker, snapshot, grant)
        else:
            require(args.action == "close" and not OPERATION_DIR.exists() and not OPERATION_DIR.is_symlink(), "NEW_CLOSE_REQUIRED_NO_OLD_MARKER_REANCHOR")
            OPERATION_DIR.mkdir(parents=True, mode=0o700)
            marker = {"operation": OPERATION, "binding_id": BINDING, "device_id": DEVICE, "workspace_id": WORKSPACE,
                      "workspace_generation": GENERATION, "root": LOCAL_ROOT, "profile": LOCAL_PROFILE,
                      "source_revision": REVISION, "initial_service_instance": health["service_instance_id"], "initial_state": snapshot,
                      "service_grant_sha256": digest(grant), "phase": "close_prepared",
                      "old_context_ids": [r["context_id"] for r in overview["contexts"] if r.get("binding_id") == BINDING and r.get("closed_at_ms") is None]}
            save(marker)
        if args.action == "close":
            require(marker["phase"] in {"close_prepared", "intake_closed"}, "CLOSE_PHASE_CHANGED")
            require(overview["admission"]["admission_mode"] in {"scoped_pilot", "recovery"}, "INTAKE_CHANGED")
            if overview["admission"]["admission_mode"] != "recovery":
                api(origin, token, "/v1/maintenance/admission", {"mode": "recovery"})
            require(api(origin, token, "/healthz")["admission_mode"] == "recovery", "INTAKE_NOT_CLOSED")
            marker["phase"] = "intake_closed"
            save(marker)
        elif args.action == "renew":
            require(marker["phase"] in {"intake_closed", "renewal_prepared", "authority_renewed"}, "RENEW_PHASE_CHANGED")
            require(health["service_instance_id"] != marker["initial_service_instance"], "NEW_R11_SERVICE_INSTANCE_REQUIRED")
            marker["service_instance_id"] = health["service_instance_id"]
            renew(origin, token, overview, marker, grant)
        else:
            require(marker["phase"] in {"authority_renewed", "intake_reopened"} and marker.get("service_instance_id") == health["service_instance_id"], "R11_REOPEN_PHASE_OR_INSTANCE_CHANGED")
            renewed_authority(overview, marker)
            nodes = [r for r in overview["nodes"] if r.get("device_id") == DEVICE]
            require(len(nodes) == 1, "NODE_NOT_UNIQUE")
            node = nodes[0]
            for argument, field in ((args.expected_activation_epoch, "activation_epoch"), (args.expected_runtime_instance, "runtime_instance_id"),
                                    (args.expected_mcp_instance, "mcp_server_instance_id"), (args.expected_contract_version, "contract_version")):
                require(isinstance(argument, str) and argument and node.get(field) == argument, "EXPECTED_R11_NODE_IDENTITY_REQUIRED")
            require(0 <= overview["observed_at_ms"] - node.get("last_seen_at_ms", 0) < 60000 and node.get("readiness") == "ready"
                    and node.get("policy_state") == "enabled" and node.get("policy_expires_at_ms") == marker["expires_at_ms"], "R11_NODE_NOT_FRESH_READY_OR_EXACT_POLICY_WINDOW")
            require(overview["admission"]["admission_mode"] in {"recovery", "scoped_pilot"}, "REOPEN_ADMISSION_CHANGED")
            if overview["admission"]["admission_mode"] == "recovery":
                api(origin, token, "/v1/maintenance/admission", {"mode": "scoped_pilot"})
            require(api(origin, token, "/healthz")["admission_mode"] == "scoped_pilot", "SCOPED_INTAKE_NOT_REOPENED")
            marker.update(phase="intake_reopened", activation_epoch=args.expected_activation_epoch,
                          runtime_instance_id=args.expected_runtime_instance, mcp_server_instance_id=args.expected_mcp_instance)
            save(marker)
        final_health = api(origin, token, "/healthz")
        final_overview = api(origin, token, "/v1/ui/overview")
        final_state = state(database)
        require(final_health["service_instance_id"] == health["service_instance_id"] and digest(target(final_overview)) == digest(grant), "SERVICE_OR_GRANT_CHANGED_DURING_AUTHORITY_OPERATION")
        compare_history(snapshot, final_state, authority=args.action == "renew")
        emit(marker["phase"], ok=True, host=HOST, service=SERVICE, source_revision=final_health["declared_source_revision"],
             package_source_sha256=final_health["package_source_sha256"], service_instance_id=final_health["service_instance_id"],
             binding_id=BINDING, device_id=DEVICE, workspace_id=WORKSPACE, workspace_generation=GENERATION, root=LOCAL_ROOT, profile=LOCAL_PROFILE,
             admission=final_health["admission_mode"], observed_at_ms=final_overview["observed_at_ms"], state=final_state, state_sha256=digest(final_state),
             service_grant_preserved=GRANT, service_grant_sha256=digest(grant), service_grant_changed=False,
             requested_at_ms=marker.get("requested_at_ms"), expires_at_ms=marker.get("expires_at_ms"), duration_ms=3600000,
             context_id=marker.get("context_id"), pilot_id=marker.get("pilot_id"), remote_mutation=True,
             policy_assignment=None if marker.get("context_id") is None else {"binding_id": BINDING, "device_id": DEVICE, "workspace_id": WORKSPACE,
                 "workspace_generation": GENERATION, "root": LOCAL_ROOT, "profile": LOCAL_PROFILE, "context_id": marker["context_id"], "expires_at_ms": marker["expires_at_ms"]})
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        emit("r11_authority_failed", ok=False, code=error.code if isinstance(error, GuardFailure) else "R11_AUTHORITY_FAILED",
             next_action="KEEP_INTAKE_CLOSED_INSPECT_MARKER_AND_FRESH_STATE_NO_WINDOW_REANCHOR")
        raise SystemExit(2) from None
