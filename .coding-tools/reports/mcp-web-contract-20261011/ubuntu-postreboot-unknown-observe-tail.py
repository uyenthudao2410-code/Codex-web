"""Read-only observation of the one new post-reboot UNKNOWN exec action.

The caller narrows the driver's historical-family query to exclude this exact
new action. Global state counts are unchanged; historical thirteen families
remain validated separately. Sealed arguments and receipt messages stay private.
"""
import re

ACTION = "act_0dbe0e6b68a34afea0e93ca5e55e4b34"
TASK = "task_80f4e34defce4c139bc8c6a0ffa2984b"
BINDING = "bind_3e05bf64cb3e4bab93d930ae1692bebb"
SAFE_CODE = re.compile(r"[A-Z][A-Z0-9_]{2,95}")
SAFE_STATE = re.compile(r"[a-z][a-z0-9_]{0,63}")

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
    overview = json_request(origin, token, "/v1/ui/overview")
    action = json_request(origin, token, "/v1/actions/" + ACTION)
    require(action.get("action_id") == ACTION and action.get("task_id") == TASK and action.get("binding_id") == BINDING, "EXPECTED_ACTION_IDENTITY_CHANGED")
    require(action.get("tool_name") == "exec_command", "EXPECTED_ACTION_TOOL_CHANGED")
    database = Path(values["CONTROL_PLANE_DB"])
    state = state_counts(database)
    require(state["historical_action_families_sha256"] == "825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed", "HISTORICAL_EVIDENCE_CHANGED")
    with sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True, timeout=5) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        nonhistorical = [dict(row) for row in connection.execute("SELECT action_id, tool_name, delivery_state, settled_at_ms FROM actions WHERE delivery_state != 'settled' ORDER BY action_id") if row["action_id"] not in HISTORICAL_ACTION_IDS]
        require(len(nonhistorical) == 1 and nonhistorical[0]["action_id"] == ACTION, "OTHER_UNRESOLVED_ACTION_PRESENT")
        intent = connection.execute("SELECT argv_json, argv_digest, cwd, timeout_ms, max_output_bytes FROM mcp_exec_intents WHERE action_id = ? AND task_id = ?", (ACTION, TASK)).fetchone()
        require(intent is not None, "EXEC_INTENT_MISSING")
        argv = json.loads(intent["argv_json"])
        expected_command_matches = argv == {"argv": ["node", "--test", "tests/control-plane-approved-patch-runtime.test.js"]}
        writer_rows = [dict(row) for row in connection.execute("SELECT task_id, lease_generation, expires_at_ms, released_at_ms FROM mcp_task_writer_leases WHERE task_id = ? ORDER BY lease_generation", (TASK,))]
        task = connection.execute("SELECT task_id, binding_id, created_at_ms, expires_at_ms, closed_at_ms FROM mcp_task_sessions WHERE task_id = ?", (TASK,)).fetchone()
        require(task is not None, "EXEC_TASK_MISSING")
    receipts = []
    for row in action.get("receipts", []):
        payload = json.loads(row.get("payload_json") or "{}")
        require(isinstance(payload, dict), "RECEIPT_PAYLOAD_INVALID")
        projected = {"receipt_id": row.get("receipt_id"), "receipt_state": row.get("receipt_state"), "received_at_ms": row.get("received_at_ms"), "local_handle_present": bool(row.get("local_handle")), "receipt_digest": row.get("receipt_digest")}
        for key in ("code", "diagnostic_code"):
            value = payload.get(key)
            if isinstance(value, str) and SAFE_CODE.fullmatch(value):
                projected[key] = value
        for key in ("operation_kind", "process_state", "phase", "category"):
            value = payload.get(key)
            if isinstance(value, str) and SAFE_STATE.fullmatch(value):
                projected[key] = value
        for key in ("command_id", "job_id", "local_handle"):
            projected[key + "_in_payload_present"] = bool(payload.get(key))
        receipts.append(projected)
    observed = overview["observed_at_ms"]
    nodes = [row for row in overview["nodes"] if row.get("device_id") == action.get("device_id")]
    require(len(nodes) == 1, "NODE_NOT_UNIQUE")
    node = nodes[0]
    fields = lambda row, keys: {key: row.get(key) for key in keys}
    arguments = json.loads(action.get("arguments_json") or "{}")
    emit("postreboot_unknown_exec_observation", ok=True, observed_at_ms=observed, remote_mutations=False,
         health=health, service_pid=service_pid(), state=state,
         historical_unresolved_count=13, new_unresolved_count=len(nonhistorical), nonhistorical_actions=nonhistorical,
         action=fields(action, ("action_id", "task_id", "binding_id", "tool_name", "delivery_state", "created_at_ms", "expires_at_ms", "settled_at_ms", "writer_lease_generation")),
         sealed_arguments_sha256=hashlib.sha256(action["arguments_json"].encode("utf-8")).hexdigest(),
         expected_command_matches=expected_command_matches, cwd_empty=(intent["cwd"] == ""),
         sealed_intent_argv_digest_matches=(arguments.get("argv_digest") == intent["argv_digest"]),
         sealed_timeout_matches_intent=(arguments.get("timeout_ms") == intent["timeout_ms"]),
         max_output_32768_matches=(arguments.get("max_output_bytes") == intent["max_output_bytes"] == 32768),
         attempts=[fields(row, ("attempt_id", "attempt_number", "dispatched_at_ms")) for row in action.get("attempts", [])],
         receipts=receipts, reconciliation_present=action.get("reconciliation") is not None,
         dispatch_disposition_present=action.get("dispatch_disposition") is not None,
         task=fields(dict(task), ("task_id", "binding_id", "created_at_ms", "expires_at_ms", "closed_at_ms")), writer_leases=writer_rows,
         node=fields(node, ("device_id", "readiness", "policy_state", "policy_reason", "policy_expires_at_ms", "activation_epoch", "last_seen_at_ms")),
         heartbeat_age_ms=observed-node["last_seen_at_ms"], authority_remaining_ms=1791710784008-observed,
         exec_readiness_proven=False)
except Exception as error:
    emit("postreboot_unknown_exec_observation_failed", ok=False, code=error.code if isinstance(error, GuardFailure) else "POSTREBOOT_UNKNOWN_OBSERVATION_FAILED", remote_mutations=False)
    raise SystemExit(2) from None
