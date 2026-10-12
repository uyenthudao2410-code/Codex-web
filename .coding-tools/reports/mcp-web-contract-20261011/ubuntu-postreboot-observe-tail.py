"""Read-only post-reboot server observation. Append to guarded driver definitions.

No authority renewal, service mutation, action submission or payload output.
Node readiness is observed without requiring it while Windows recovers.
"""
try:
    require(pwd.getpwuid(os.getuid()).pw_name == USER, "EXECUTION_USER_MISMATCH")
    require(HOST in run(["tailscale", "ip", "-4"], code="TAILSCALE_IDENTITY_UNAVAILABLE").decode().split(), "SERVER_ADDRESS_MISMATCH")
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
    observed = overview["observed_at_ms"]
    binding_id = "bind_3e05bf64cb3e4bab93d930ae1692bebb"
    context_id = "ctx_80a102323c14412fa539a396a1edd034"
    pilot_id = "pilot_4723468161ec46269ea73e93e854f52a"
    device_id = "72ceec2d-e3f2-472f-8e3c-99fffe053035"
    workspace_id = "workspace_dda1d78e9a21402aa6213f72af64f788"
    generation = "generation_c2f13e8d02344cf6a38a3f42ecfa59b6"
    principal_id = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
    expiry = 1791710784008
    require(observed < expiry, "APPROVED_WINDOW_EXPIRED")
    require(values.get("CONTROL_PLANE_MCP_SERVICE_EXEC_ENABLED") == "true", "EXEC_CONFIGURATION_CHANGED")
    bindings = [row for row in overview["bindings"] if row.get("binding_id") == binding_id]
    require(len(bindings) == 1 and bindings[0].get("revoked_at_ms") is None and bindings[0]["device_id"] == device_id and bindings[0]["workspace_id"] == workspace_id and bindings[0]["workspace_generation"] == generation, "EXACT_BINDING_CHANGED")
    registrations = [row for row in overview["workspace_registrations"] if row.get("device_id") == device_id and row.get("workspace_id") == workspace_id and row.get("workspace_generation") == generation and row.get("retired_at_ms") is None]
    require(len(registrations) == 1 and registrations[0].get("display_name") == "Tools-Codex-web" and registrations[0]["capabilities"] == {"read": True, "write": True, "exec": True}, "CURRENT_REGISTRATION_CHANGED")
    contexts = [row for row in overview["contexts"] if row.get("binding_id") == binding_id and row.get("closed_at_ms") is None and row["expires_at_ms"] > observed]
    standing = [row for row in contexts if row["context_id"] == context_id]
    require(len(standing) == 1 and standing[0]["expires_at_ms"] == expiry and all(row["expires_at_ms"] <= expiry for row in contexts), "STANDING_CONTEXT_CHANGED")
    pilots = [row for row in overview["scoped_pilot_decisions"] if row.get("revoked_at_ms") is None and row["expires_at_ms"] > observed]
    require(len(pilots) == 1 and pilots[0]["decision_id"] == pilot_id and pilots[0]["principal_id"] == principal_id and pilots[0]["binding_id"] == binding_id and pilots[0]["expires_at_ms"] == expiry, "PILOT_CHANGED")
    grants = [row for row in overview["mcp_service_grants"] if row.get("grant_id") == "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"]
    require(len(grants) == 1 and grants[0]["principal_id"] == principal_id and grants[0].get("revoked_at_ms") is None and grants[0]["expires_at_ms"] >= expiry and set(grants[0]["scopes"]) == {"control-plane.inventory", "control-plane.read", "control-plane.patch"}, "SERVICE_GRANT_CHANGED")
    require(overview["admission"]["admission_mode"] == "scoped_pilot", "ADMISSION_CHANGED")
    state = state_counts(Path(values["CONTROL_PLANE_DB"]))
    require(state["historical_action_families_sha256"] == "825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed", "HISTORICAL_EVIDENCE_CHANGED")
    nodes = [row for row in overview["nodes"] if row.get("device_id") == device_id]
    require(len(nodes) == 1, "NODE_NOT_UNIQUE")
    node = nodes[0]
    context_ids = {row["context_id"] for row in overview["contexts"] if row.get("binding_id") == binding_id}
    fields = lambda row, keys: {key: row.get(key) for key in keys}
    emit("postreboot_server_observation", ok=True, observed_at_ms=observed, remote_mutations=False,
         health=health, service_pid=service_pid(), release_verification=verification,
         authority_valid=True, authority_expires_at_ms=expiry, authority_remaining_ms=expiry-observed,
         binding=fields(bindings[0], ("binding_id", "device_id", "workspace_id", "workspace_generation", "revoked_at_ms")),
         registered_capabilities=registrations[0]["capabilities"], context_id=context_id, pilot_id=pilot_id,
         service_grant_scopes=grants[0]["scopes"], service_grant_expires_at_ms=grants[0]["expires_at_ms"],
         admission="scoped_pilot", exec_enabled=True, state=state,
         node=fields(node, ("device_id", "endpoint_id", "presence_state", "readiness", "policy_state", "policy_expires_at_ms", "policy_reason", "activation_epoch", "last_seen_at_ms")),
         heartbeat_age_ms=observed-node["last_seen_at_ms"],
         binding_actions=[fields(row, ("action_id", "tool_name", "delivery_state", "latest_receipt_state", "receipt_count")) for row in overview.get("actions", []) if row.get("context_id") in context_ids],
         exec_readiness_proven=False)
except Exception as error:
    emit("postreboot_server_observation_failed", ok=False, code=error.code if isinstance(error, GuardFailure) else "POSTREBOOT_OBSERVATION_FAILED", remote_mutations=False)
    raise SystemExit(2) from None
