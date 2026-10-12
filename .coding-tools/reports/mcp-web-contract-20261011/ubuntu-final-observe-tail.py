"""Final read-only deployed-state observation appended to driver definitions."""
try:
    require(pwd.getpwuid(os.getuid()).pw_name == USER, "EXECUTION_USER_MISMATCH")
    values = parse_environment(protected_file(ENV_FILE))
    bind = values.get("CONTROL_PLANE_BIND", "127.0.0.1")
    if bind in ("0.0.0.0", "::"):
        bind = "127.0.0.1"
    origin = "http://" + bind + ":" + values.get("CONTROL_PLANE_PORT", "8765")
    token = values["CONTROL_PLANE_OPERATOR_TOKEN"]
    health = verify_health(origin, token, REVISION, PACKAGE)
    verification = verify_release(CURRENT.resolve(strict=True), REVISION, PACKAGE)
    require(verification["file_count"] == 38, "RELEASE_FILE_COUNT_CHANGED")
    overview = json_request(origin, token, "/v1/ui/overview")
    state = require_quiescent(Path(values["CONTROL_PLANE_DB"]))
    require(state["historical_action_families_sha256"] == "825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed", "HISTORICAL_EVIDENCE_CHANGED")
    binding_id = "bind_3e05bf64cb3e4bab93d930ae1692bebb"
    device_id = "72ceec2d-e3f2-472f-8e3c-99fffe053035"
    expiry = 1791710784008
    contexts = [row for row in overview["contexts"] if row.get("binding_id") == binding_id and row.get("closed_at_ms") is None and row["expires_at_ms"] > overview["observed_at_ms"]]
    pilots = [row for row in overview["scoped_pilot_decisions"] if row.get("revoked_at_ms") is None and row["expires_at_ms"] > overview["observed_at_ms"]]
    standing_contexts = [row for row in contexts if row["context_id"] == "ctx_80a102323c14412fa539a396a1edd034"]
    require(len(standing_contexts) == 1 and standing_contexts[0]["expires_at_ms"] == expiry and all(row["expires_at_ms"] <= expiry for row in contexts), "FINAL_CONTEXT_CHANGED")
    require(len(pilots) == 1 and pilots[0]["decision_id"] == "pilot_4723468161ec46269ea73e93e854f52a" and pilots[0]["binding_id"] == binding_id and pilots[0]["expires_at_ms"] == expiry, "FINAL_PILOT_CHANGED")
    require(overview["admission"]["admission_mode"] == "scoped_pilot", "FINAL_ADMISSION_CHANGED")
    nodes = [row for row in overview["nodes"] if row.get("device_id") == device_id]
    require(len(nodes) == 1, "FINAL_NODE_NOT_UNIQUE")
    node = nodes[0]
    heartbeat_age = overview["observed_at_ms"] - node["last_seen_at_ms"]
    require(0 <= heartbeat_age < 90000 and node.get("readiness") == "ready" and node.get("policy_state") == "enabled" and node.get("policy_expires_at_ms", 0) > overview["observed_at_ms"], "FINAL_NODE_READINESS_NOT_PROVEN")
    action_ids = ("act_c8412bf197ee427fb9a983ad0bd19ab2", "act_a600a322c7cc4dbf95c2c66b055820e4")
    actions = [row for row in overview["actions"] if row.get("action_id") in action_ids]
    require(len(actions) == 2 and all(row.get("delivery_state") == "settled" and row.get("latest_receipt_state") == "completed" for row in actions), "FINAL_PROOF_ACTIONS_NOT_SETTLED")
    fields = lambda row, keys: {key: row.get(key) for key in keys}
    emit("final_ubuntu_observation", ok=True, observed_at_ms=overview["observed_at_ms"], remote_mutations=False,
         health=health, service_pid=service_pid(), release_verification=verification, state=state,
         binding_id=binding_id, context_id=standing_contexts[0]["context_id"], pilot_id=pilots[0]["decision_id"], authority_expires_at_ms=expiry,
         live_binding_context_count=len(contexts), all_contexts_within_approved_expiry=True,
         admission="scoped_pilot", node=fields(node, ("device_id", "endpoint_id", "readiness", "policy_state", "policy_expires_at_ms", "activation_epoch", "last_seen_at_ms")),
         heartbeat_age_ms=heartbeat_age, node_online_fresh_heartbeat=True,
         proof_actions=[fields(row, ("action_id", "tool_name", "delivery_state", "latest_receipt_state", "receipt_count")) for row in actions],
         exec_readiness_proven=False)
except Exception as error:
    emit("final_ubuntu_observation_failed", ok=False, code=error.code if isinstance(error, GuardFailure) else "FINAL_OBSERVATION_FAILED", remote_mutations=False)
    raise SystemExit(2) from None
