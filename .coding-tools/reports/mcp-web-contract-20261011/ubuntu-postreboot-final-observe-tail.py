"""Read-only final MCP inventory/tasks/actions/authority observation.

Caller supplies OBSERVER_NEW_ACTION and excludes only the old and new action
IDs from the driver's historical-family query. Global counts remain complete.
Sealed arguments, credential files, headers and raw receipt messages stay private.
"""
import re

OLD_ACTION = "act_0dbe0e6b68a34afea0e93ca5e55e4b34"
NEW_ACTION = globals().get("OBSERVER_NEW_ACTION")
BINDING = "bind_3e05bf64cb3e4bab93d930ae1692bebb"
CONTEXT = "ctx_80a102323c14412fa539a396a1edd034"
PILOT = "pilot_4723468161ec46269ea73e93e854f52a"
EXPIRY = 1791710784008
SAFE_CODE = re.compile(r"[A-Z][A-Z0-9_]{2,95}")
SAFE_STATE = re.compile(r"[a-z][a-z0-9_]{0,63}")


def project_action(action):
    fields = lambda row, keys: {key: row.get(key) for key in keys}
    receipts = []
    for receipt in action.get("receipts", []):
        payload = json.loads(receipt.get("payload_json") or "{}")
        require(isinstance(payload, dict), "RECEIPT_PAYLOAD_INVALID")
        projected = fields(receipt, ("receipt_id", "receipt_state", "received_at_ms", "receipt_digest"))
        projected["local_handle_present"] = bool(receipt.get("local_handle"))
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
        if isinstance(payload.get("exit_code"), int) and not isinstance(payload["exit_code"], bool):
            projected["exit_code"] = payload["exit_code"]
        receipts.append(projected)
    return {
        **fields(action, ("action_id", "task_id", "binding_id", "tool_name", "delivery_state", "created_at_ms", "expires_at_ms", "settled_at_ms", "writer_lease_generation")),
        "sealed_arguments_sha256": hashlib.sha256(action["arguments_json"].encode("utf-8")).hexdigest(),
        "attempts": [fields(row, ("attempt_id", "attempt_number", "dispatched_at_ms")) for row in action.get("attempts", [])],
        "receipts": receipts,
        "reconciliation_present": action.get("reconciliation") is not None,
        "dispatch_disposition_present": action.get("dispatch_disposition") is not None,
    }


try:
    require(isinstance(NEW_ACTION, str) and re.fullmatch(r"act_[a-f0-9]{32}", NEW_ACTION) is not None and NEW_ACTION != OLD_ACTION, "NEW_ACTION_ID_REQUIRED")
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
    old = json_request(origin, token, "/v1/actions/" + OLD_ACTION)
    new = json_request(origin, token, "/v1/actions/" + NEW_ACTION)
    for action, expected in ((old, OLD_ACTION), (new, NEW_ACTION)):
        require(action.get("action_id") == expected and action.get("binding_id") == BINDING and action.get("tool_name") == "exec_command", "ACTION_IDENTITY_CHANGED")
    require(hashlib.sha256(old["arguments_json"].encode("utf-8")).hexdigest() == "1a4d8eca040801140b3e6ce0921bf76d8cc00fb766fbe8d5fd363bf2c297908b", "OLD_SEALED_ARGUMENTS_CHANGED")
    old_receipts = [row for row in old.get("receipts", []) if row.get("receipt_id") == "rcpt_dd5cdb6d64b246f29633daf1dd8ab307"]
    require(len(old_receipts) == 1 and old_receipts[0]["receipt_state"] == "unknown" and old_receipts[0]["receipt_digest"] == "951ee9c9aafffb0b17994246648c24c3acd71d416a883c8d3122597b14cffaad", "OLD_UNKNOWN_RECEIPT_CHANGED")
    database = Path(values["CONTROL_PLANE_DB"])
    state = state_counts(database)
    require(state["historical_action_families_sha256"] == "825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed", "HISTORICAL_EVIDENCE_CHANGED")
    with sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True, timeout=5) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        nonhistorical = [dict(row) for row in connection.execute("SELECT action_id, tool_name, delivery_state, settled_at_ms FROM actions WHERE delivery_state != 'settled' ORDER BY action_id") if row["action_id"] not in HISTORICAL_ACTION_IDS]
        require(all(row["action_id"] in (OLD_ACTION, NEW_ACTION) for row in nonhistorical), "OTHER_UNRESOLVED_ACTION_PRESENT")
        task_rows = [dict(row) for row in connection.execute("SELECT task_id, binding_id, created_at_ms, expires_at_ms, closed_at_ms FROM mcp_task_sessions WHERE binding_id = ? ORDER BY created_at_ms, task_id", (BINDING,))]
        writer_rows = [dict(row) for row in connection.execute("SELECT task_id, lease_generation, expires_at_ms, released_at_ms FROM mcp_task_writer_leases WHERE binding_id = ? ORDER BY lease_generation", (BINDING,))]
    standing = [row for row in overview["contexts"] if row.get("context_id") == CONTEXT]
    require(len(standing) == 1 and standing[0]["binding_id"] == BINDING and standing[0]["expires_at_ms"] == EXPIRY and standing[0].get("closed_at_ms") is None, "STANDING_CONTEXT_CHANGED")
    pilots = [row for row in overview["scoped_pilot_decisions"] if row.get("decision_id") == PILOT]
    require(len(pilots) == 1 and pilots[0]["binding_id"] == BINDING and pilots[0]["expires_at_ms"] == EXPIRY and pilots[0].get("revoked_at_ms") is None, "PILOT_CHANGED")
    require(overview["admission"]["admission_mode"] == "scoped_pilot", "ADMISSION_CHANGED")
    tunnel = parse_environment(protected_file(HOME / ".config/codex-control-plane/mcp-tunnel.env"))
    header_path = Path(tunnel["CONTROL_PLANE_MCP_AUTH_HEADER_FILE"])
    require(header_path.is_file() and not header_path.is_symlink(), "HEADER_TARGET_UNSAFE")
    header_metadata = header_path.stat()
    require(header_metadata.st_uid == os.getuid() and stat.S_IMODE(header_metadata.st_mode) in (0o400, 0o600), "HEADER_FILE_ACL_INVALID")
    authorization = header_path.read_text().strip()
    require(authorization.startswith("Bearer "), "HEADER_FORMAT_INVALID")
    mcp_origin = "http://127.0.0.1:" + values.get("CONTROL_PLANE_MCP_PORT", "8766")
    def metadata_call(operation, number):
        request = urllib.request.Request(mcp_origin + "/mcp", data=json.dumps({"jsonrpc": "2.0", "id": number, "method": "tools/call", "params": {"name": "workspace_context", "arguments": {"operation": operation}}}).encode(), headers={"Authorization": authorization, "Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                result = json.load(response)
        except (OSError, ValueError, urllib.error.URLError):
            raise GuardFailure("MCP_METADATA_READ_FAILED") from None
        require("error" not in result and result.get("result", {}).get("isError") is not True, "MCP_METADATA_TOOL_FAILED")
        return result["result"]["structuredContent"]
    inventory = metadata_call("inventory", 1)
    task_list = metadata_call("task_list", 2)
    require(len(inventory["targets"]) == 1 and inventory["targets"][0]["binding_id"] == BINDING, "INVENTORY_TARGET_CHANGED")
    fields = lambda row, keys: {key: row.get(key) for key in keys}
    nodes = [row for row in overview["nodes"] if row.get("device_id") == new.get("device_id")]
    require(len(nodes) == 1, "NODE_NOT_UNIQUE")
    node = nodes[0]
    emit("postreboot_final_server_observation", ok=True, observed_at_ms=observed, remote_mutations=False,
         metadata_operations=["inventory", "task_list"], health=health, service_pid=service_pid(), release_verification=verification,
         state=state, historical_unresolved_count=13, nonhistorical_unresolved_actions=nonhistorical,
         old_unknown_receipt_preserved=True, old_action=project_action(old), new_action=project_action(new),
         task_rows=task_rows, writer_leases=writer_rows,
         mcp_tasks=[fields(row, ("task_id", "binding_id", "created_at_ms", "expires_at_ms", "closed_at_ms")) for row in task_list["tasks"]],
         inventory_contract=inventory["tool_contract"], inventory_path_format=inventory["path_format"],
         inventory_target=fields(inventory["targets"][0], ("binding_id", "presence_state", "readiness", "dispatch_state", "policy_state")),
         authority_valid=(observed < EXPIRY), context_id=CONTEXT, pilot_id=PILOT, authority_expires_at_ms=EXPIRY, authority_remaining_ms=EXPIRY-observed,
         node=fields(node, ("device_id", "readiness", "policy_state", "policy_reason", "policy_expires_at_ms", "activation_epoch", "last_seen_at_ms")), heartbeat_age_ms=observed-node["last_seen_at_ms"])
except Exception as error:
    emit("postreboot_final_server_observation_failed", ok=False, code=error.code if isinstance(error, GuardFailure) else "POSTREBOOT_FINAL_OBSERVATION_FAILED", remote_mutations=False)
    raise SystemExit(2) from None
