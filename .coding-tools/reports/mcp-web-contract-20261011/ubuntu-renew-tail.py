"""Idempotent same-scope owner renewal appended to guarded driver definitions.

The pre-existing service grant remains valid and its scopes/credential are
preserved. Context and pilot are bounded to the one approved 60 minute window.
"""
import fcntl

BINDING = "bind_3e05bf64cb3e4bab93d930ae1692bebb"
DEVICE = "72ceec2d-e3f2-472f-8e3c-99fffe053035"
WORKSPACE = "workspace_dda1d78e9a21402aa6213f72af64f788"
GENERATION = "generation_c2f13e8d02344cf6a38a3f42ecfa59b6"
PRINCIPAL = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
GRANT = "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"
BACKUP = BACKUP_ROOT / "mcp-web-contract-20261011T082438Z"
MARKER = BACKUP / "authority-renewal-public.json"
REASON = "Owner-approved beaa9d5a rollout: same Tools-Codex-web read/write/sandboxed exec scope for 60 minutes"
lock_descriptor = None
try:
    require(pwd.getpwuid(os.getuid()).pw_name == USER, "EXECUTION_USER_MISMATCH")
    require(HOST in run(["tailscale", "ip", "-4"], code="TAILSCALE_IDENTITY_UNAVAILABLE").decode().split(), "SERVER_ADDRESS_MISMATCH")
    private_directory(BACKUP)
    lock_descriptor = os.open(INSTALL / ".owner-acceptance-deployment.lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise GuardFailure("DEPLOYMENT_OR_RENEWAL_ALREADY_RUNNING") from None
    values = parse_environment(protected_file(ENV_FILE))
    require(values.get("CONTROL_PLANE_MCP_SERVICE_EXEC_ENABLED") == "true", "EXISTING_EXEC_CONFIGURATION_CHANGED")
    token = values["CONTROL_PLANE_OPERATOR_TOKEN"]
    bind = values.get("CONTROL_PLANE_BIND", "127.0.0.1")
    if bind in ("0.0.0.0", "::"):
        bind = "127.0.0.1"
    origin = "http://" + bind + ":" + values.get("CONTROL_PLANE_PORT", "8765")
    health = verify_health(origin, token, REVISION, PACKAGE)
    verify_release(CURRENT.resolve(strict=True), REVISION, PACKAGE)
    database = Path(values["CONTROL_PLANE_DB"])
    initial = require_quiescent(database)
    require(initial["historical_action_families_sha256"] == "825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed", "HISTORICAL_EVIDENCE_CHANGED")
    overview = json_request(origin, token, "/v1/ui/overview")
    bindings = [row for row in overview["bindings"] if row.get("device_id") == DEVICE and row.get("workspace_id") == WORKSPACE and row.get("workspace_generation") == GENERATION and row.get("revoked_at_ms") is None]
    require(len(bindings) == 1 and bindings[0]["binding_id"] == BINDING, "EXACT_BINDING_CHANGED")
    registrations = [row for row in overview["workspace_registrations"] if row.get("device_id") == DEVICE and row.get("workspace_id") == WORKSPACE and row.get("workspace_generation") == GENERATION and row.get("retired_at_ms") is None]
    require(len(registrations) == 1 and registrations[0].get("display_name") == "Tools-Codex-web" and registrations[0]["capabilities"] == {"read": True, "write": True, "exec": True}, "CURRENT_REGISTRATION_CHANGED")
    grants = [row for row in overview["mcp_service_grants"] if row.get("grant_id") == GRANT]
    require(len(grants) == 1 and grants[0].get("principal_id") == PRINCIPAL and grants[0].get("revoked_at_ms") is None and set(grants[0]["scopes"]) == {"control-plane.inventory", "control-plane.read", "control-plane.patch"}, "EXISTING_SERVICE_GRANT_CHANGED")
    grant = grants[0]
    if MARKER.exists():
        receipt = json.loads(protected_file(MARKER))
        require(receipt.get("binding_id") == BINDING and receipt.get("source_revision") == REVISION and receipt.get("reason") == REASON, "RENEWAL_RECEIPT_MISMATCH")
        require(receipt["expires_at_ms"] == receipt["requested_at_ms"] + 3600000, "RENEWAL_RECEIPT_WINDOW_INVALID")
    else:
        require(overview["admission"]["admission_mode"] == "recovery", "RENEWAL_REQUIRES_CLOSED_INTAKE")
        require(not any(row.get("binding_id") == BINDING and row.get("closed_at_ms") is None and row["expires_at_ms"] > overview["observed_at_ms"] for row in overview["contexts"]), "UNEXPECTED_LIVE_CONTEXT")
        now = int(time.time() * 1000)
        receipt = {"source_revision": REVISION, "binding_id": BINDING, "requested_at_ms": now, "expires_at_ms": now + 3600000, "reason": REASON}
        atomic_bytes(MARKER, json.dumps(receipt, separators=(",", ":")).encode())
    expiry = receipt["expires_at_ms"]
    require(expiry > int(time.time() * 1000), "APPROVED_RENEWAL_WINDOW_EXPIRED")
    require(grant["expires_at_ms"] >= expiry, "EXISTING_SERVICE_GRANT_WINDOW_TOO_SHORT")
    require(not any(row.get("revoked_at_ms") is None and row.get("expires_at_ms", 0) > overview["observed_at_ms"] and (row.get("binding_id") != BINDING or row.get("principal_id") != PRINCIPAL or row["expires_at_ms"] != expiry) for row in overview["scoped_pilot_decisions"]), "UNRELATED_LIVE_PILOT")
    active = [row for row in overview["contexts"] if row.get("binding_id") == BINDING and row.get("closed_at_ms") is None and row["expires_at_ms"] > overview["observed_at_ms"]]
    require(len(active) <= 1 and all(row["expires_at_ms"] == expiry for row in active), "UNEXPECTED_ACTIVE_CONTEXT")
    require(overview["admission"]["admission_mode"] in ("recovery", "scoped_pilot"), "UNEXPECTED_ADMISSION_MODE")
    if not active:
        require(overview["admission"]["admission_mode"] == "recovery", "CONTEXT_CREATION_REQUIRES_CLOSED_INTAKE")
        target_context_ids = {row["context_id"] for row in overview["contexts"] if row.get("binding_id") == BINDING}
        require(all(row.get("delivery_state") == "settled" for row in overview.get("actions", []) if row.get("context_id") in target_context_ids), "UNSETTLED_CURRENT_BINDING_ACTION")
        for row in overview["contexts"]:
            if row.get("binding_id") == BINDING and row.get("closed_at_ms") is None:
                require(row["expires_at_ms"] <= overview["observed_at_ms"], "UNEXPIRED_CONTEXT_CLOSE_DENIED")
                json_request(origin, token, "/v1/contexts/" + row["context_id"] + "/close", {})
        context = json_request(origin, token, "/v1/contexts", {"binding_id": BINDING, "expires_at_ms": expiry})
    else:
        context = active[0]
    receipt["context_id"] = context["context_id"]
    atomic_bytes(MARKER, json.dumps(receipt, separators=(",", ":")).encode())
    overview = json_request(origin, token, "/v1/ui/overview")
    pilots = [row for row in overview["scoped_pilot_decisions"] if row.get("revoked_at_ms") is None and row["expires_at_ms"] > overview["observed_at_ms"]]
    require(len(pilots) <= 1 and all(row.get("binding_id") == BINDING and row.get("principal_id") == PRINCIPAL and row["expires_at_ms"] == expiry for row in pilots), "UNEXPECTED_LIVE_PILOT")
    if not pilots:
        require(overview["admission"]["admission_mode"] == "recovery", "PILOT_CREATION_REQUIRES_CLOSED_INTAKE")
        pilot = json_request(origin, token, "/v1/scoped-pilot-decisions", {"principal_id": PRINCIPAL, "binding_id": BINDING, "expires_at_ms": expiry, "reason": REASON})
    else:
        pilot = pilots[0]
    receipt["pilot_id"] = pilot["decision_id"]
    atomic_bytes(MARKER, json.dumps(receipt, separators=(",", ":")).encode())
    require_quiescent(database, expected=initial)
    if overview["admission"]["admission_mode"] == "recovery":
        json_request(origin, token, "/v1/maintenance/admission", {"mode": "scoped_pilot"})
    overview = json_request(origin, token, "/v1/ui/overview")
    require(overview["admission"]["admission_mode"] == "scoped_pilot", "SCOPED_PILOT_NOT_REOPENED")
    final_contexts = [row for row in overview["contexts"] if row.get("binding_id") == BINDING and row.get("closed_at_ms") is None and row["expires_at_ms"] > overview["observed_at_ms"]]
    final_pilots = [row for row in overview["scoped_pilot_decisions"] if row.get("revoked_at_ms") is None and row["expires_at_ms"] > overview["observed_at_ms"]]
    require(len(final_contexts) == 1 and final_contexts[0]["context_id"] == receipt["context_id"] and final_contexts[0]["expires_at_ms"] == expiry, "FINAL_CONTEXT_MISMATCH")
    require(len(final_pilots) == 1 and final_pilots[0]["decision_id"] == receipt["pilot_id"] and final_pilots[0]["binding_id"] == BINDING and final_pilots[0]["expires_at_ms"] == expiry, "FINAL_PILOT_MISMATCH")
    require([row for row in overview["mcp_service_grants"] if row.get("grant_id") == GRANT] == [grant], "SERVICE_GRANT_MUTATED")
    final = require_quiescent(database, expected=initial)
    receipt["completed_at_ms"] = overview["observed_at_ms"]
    atomic_bytes(MARKER, json.dumps(receipt, separators=(",", ":")).encode())
    emit("same_scope_renewal_complete", ok=True, source_revision=REVISION, binding_id=BINDING,
         context_id=receipt["context_id"], pilot_id=receipt["pilot_id"], requested_at_ms=receipt["requested_at_ms"], expires_at_ms=expiry,
         duration_ms=3600000, service_grant_preserved=GRANT, service_grant_scopes=grant["scopes"], service_grant_changed=False,
         policy_assignment={"device_id": DEVICE, "workspace_id": WORKSPACE, "workspace_generation": GENERATION, "context_id": receipt["context_id"], "expires_at_ms": expiry},
         admission="scoped_pilot", state=final, windows_policy_installed=False, exec_readiness_proven=False,
         next_action="INSTALL_SAME_SCOPE_WINDOWS_POLICY_AND_ACTIVATE_R4")
except Exception as error:
    emit("same_scope_renewal_failed", ok=False, code=error.code if isinstance(error, GuardFailure) else "RENEWAL_FAILED", next_action="INSPECT_PUBLIC_RENEWAL_RECEIPT_AND_CURRENT_CONTEXT_PILOT_BEFORE_RETRY")
    raise SystemExit(2) from None
finally:
    if lock_descriptor is not None:
        fcntl.flock(lock_descriptor, fcntl.LOCK_UN)
        os.close(lock_descriptor)
