"""Read-only continuation appended to the guarded rollout driver definitions."""
try:
    require(pwd.getpwuid(os.getuid()).pw_name == USER, "EXECUTION_USER_MISMATCH")
    require(HOST in run(["tailscale", "ip", "-4"], code="TAILSCALE_IDENTITY_UNAVAILABLE").decode().split(), "SERVER_ADDRESS_MISMATCH")
    values = parse_environment(protected_file(ENV_FILE))
    database = Path(values["CONTROL_PLANE_DB"])
    token = values["CONTROL_PLANE_OPERATOR_TOKEN"]
    bind = values.get("CONTROL_PLANE_BIND", "127.0.0.1")
    if bind in ("0.0.0.0", "::"):
        bind = "127.0.0.1"
    origin = "http://" + bind + ":" + values.get("CONTROL_PLANE_PORT", "8765")
    overview = json_request(origin, token, "/v1/ui/overview")
    observed = overview["observed_at_ms"]
    binding_id = "bind_3e05bf64cb3e4bab93d930ae1692bebb"
    principal_id = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
    bindings = [row for row in overview["bindings"] if row.get("binding_id") == binding_id]
    require(len(bindings) == 1, "EXPECTED_BINDING_MISSING")
    binding = bindings[0]
    device_id = binding["device_id"]
    ids = {row["context_id"] for row in overview["contexts"] if row.get("binding_id") == binding_id}
    fields = lambda row, keys: {key: row.get(key) for key in keys}
    health = json_request(origin, token, "/healthz")
    revision = health.get("declared_source_revision")
    fingerprint = health.get("package_source_sha256")
    require(revision in (BASE_REVISION, REVISION), "UNEXPECTED_LIVE_REVISION")
    expected_package = BASE_PACKAGE if revision == BASE_REVISION else PACKAGE
    require(fingerprint == expected_package, "UNEXPECTED_LIVE_PACKAGE")
    release = CURRENT.resolve(strict=True)
    verification = verify_release(release, revision, expected_package)
    state = require_quiescent(database)
    emit("live_inspection", ok=True, observed_at_ms=observed,
         release=str(release), service_pid=service_pid(), health={key: health.get(key) for key in HEALTH_KEYS},
         release_verification=verification, state=state,
         exec_enabled=values.get("CONTROL_PLANE_MCP_SERVICE_EXEC_ENABLED") == "true",
         binding=fields(binding, ("binding_id", "device_id", "workspace_id", "workspace_generation", "revoked_at_ms")),
         registrations=[fields(row, ("device_id", "workspace_id", "workspace_generation", "display_name", "capabilities", "retired_at_ms")) for row in overview["workspace_registrations"] if row.get("device_id") == device_id and row.get("workspace_id") == binding["workspace_id"]],
         grants=[fields(row, ("grant_id", "principal_id", "scopes", "expires_at_ms", "revoked_at_ms", "binding_id", "allowed_binding_ids")) for row in overview["mcp_service_grants"] if row.get("principal_id") == principal_id],
         contexts=[fields(row, ("context_id", "binding_id", "expires_at_ms", "closed_at_ms")) for row in overview["contexts"] if row.get("binding_id") == binding_id],
         pilots=[fields(row, ("decision_id", "principal_id", "binding_id", "expires_at_ms", "revoked_at_ms")) for row in overview["scoped_pilot_decisions"] if row.get("principal_id") == principal_id],
         nodes=[fields(row, ("device_id", "endpoint_id", "last_seen_at_ms", "readiness", "policy_state", "policy_expires_at_ms", "policy_reason", "activation_epoch")) for row in overview["nodes"] if row.get("device_id") == device_id],
         current_actions=[fields(row, ("action_id", "tool_name", "delivery_state", "latest_receipt_state", "receipt_count")) for row in overview.get("actions", []) if row.get("context_id") in ids],
         archive_present=ARCHIVE.exists(), candidate_present=(RELEASES / RELEASE_NAME).exists(), remote_mutations=False)
except Exception as error:
    emit("live_inspection_failed", ok=False, code=error.code if isinstance(error, GuardFailure) else "LIVE_INSPECTION_FAILED", remote_mutations=False)
    raise SystemExit(2) from None
