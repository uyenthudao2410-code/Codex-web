"""Read-only r9b serving/MCP, selected Autocad scope, renewal and device census.

No action dispatch, admission changes, renewal, cleanup or database mutations.
Credentials and environment values remain in memory. Unknown historical actions
are projected separately and never counted as completed or deleted.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request


DEVICE = "4c4b7a5b-7744-49ae-a490-78a528a00471"
PRINCIPAL = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
GRANT = "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"
WORKSPACE = "workspace_bc86004be2684b958ab7a9a6f9530cd7"
GENERATION = "generation_03f9c04f1b14414fa4bfa7d91cc8ea7a"
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
RENEWAL_SERVICE = "codex-control-plane-authority-renewal.service"
RENEWAL_TIMER = "codex-control-plane-authority-renewal.timer"


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def show(unit, fields):
    output = subprocess.check_output(
        ["systemctl", "--user", "show", unit, *("--property=" + field for field in fields)],
        text=True, timeout=10,
    )
    require(len(output.encode()) <= 16 * 1024, "SYSTEMD_STATUS_TOO_LARGE")
    return {key: value for line in output.splitlines() if "=" in line
            for key, value in [line.split("=", 1)] if key in fields}


def json_response(request, maximum):
    with urllib.request.urlopen(request, timeout=10) as response:
        raw = response.read(maximum + 1)
    require(len(raw) <= maximum, "READONLY_RESPONSE_TOO_LARGE")
    payload = json.loads(raw)
    require(isinstance(payload, dict), "READONLY_RESPONSE_NOT_OBJECT")
    return payload


def rpc(port, method, params, token, name=None):
    params = {**params, "_meta": {
        "io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientCapabilities": {},
    }}
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json",
               "Accept": "application/json", "MCP-Protocol-Version": "2026-07-28",
               "Mcp-Method": method}
    if name:
        headers["Mcp-Name"] = name
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/mcp",
        data=json.dumps({"jsonrpc": "2.0", "id": "r9-final-readonly", "method": method,
                         "params": params}, separators=(",", ":")).encode(),
        headers=headers, method="POST",
    )
    response = json_response(request, 196608)
    require("error" not in response and response.get("id") == "r9-final-readonly", "READONLY_MCP_RPC_FAILED")
    result = response.get("result")
    require(isinstance(result, dict) and result.get("isError") is not True, "READONLY_MCP_TOOL_FAILED")
    return result


def census(connection, now, *, workspace_id=None, generation=None):
    clauses = ["device_id=?"]
    values = [DEVICE]
    if workspace_id is not None:
        clauses.extend(["workspace_id=?", "workspace_generation=?"])
        values.extend([workspace_id, generation])
    predicate = " AND ".join(clauses)
    count = lambda sql, extra=(): connection.execute(sql, (*values, *extra)).fetchone()[0]
    tasks = count(f"SELECT COUNT(*) FROM mcp_task_sessions WHERE {predicate} AND closed_at_ms IS NULL")
    live_tasks = count(f"SELECT COUNT(*) FROM mcp_task_sessions WHERE {predicate} AND closed_at_ms IS NULL AND expires_at_ms>?", (now,))
    writer_predicate = " AND ".join("t." + clause for clause in clauses)
    writers = count("SELECT COUNT(*) FROM mcp_task_writer_leases l JOIN mcp_task_sessions t ON t.task_id=l.task_id "
                    f"WHERE {writer_predicate} AND l.released_at_ms IS NULL")
    live_writers = count("SELECT COUNT(*) FROM mcp_task_writer_leases l JOIN mcp_task_sessions t ON t.task_id=l.task_id "
                         f"WHERE {writer_predicate} AND l.released_at_ms IS NULL AND l.expires_at_ms>?", (now,))
    unsettled = count(f"SELECT COUNT(*) FROM actions WHERE {predicate} AND settled_at_ms IS NULL")
    states = {row["delivery_state"]: row["count"] for row in connection.execute(
        f"SELECT delivery_state,COUNT(*) AS count FROM actions WHERE {predicate} AND settled_at_ms IS NULL GROUP BY delivery_state",
        values,
    )}
    return {"unclosed_tasks": tasks, "live_open_tasks": live_tasks,
            "expired_unclosed_tasks": tasks - live_tasks, "unreleased_writers": writers,
            "live_writers": live_writers, "expired_unreleased_writers": writers - live_writers,
            "unsettled_actions": unsettled, "unsettled_by_delivery_state": states,
            "queued_actions": states.get("queued", 0),
            "active_dispatch_actions": sum(states.get(state, 0) for state in ("dispatch_unconfirmed", "accepted")),
            "reconciliation_required_actions": states.get("reconcile_required", 0)}


def renewal_configuration():
    allowed = {
        "CONTROL_PLANE_SCOPED_PILOT_DECISION_ID", "CONTROL_PLANE_MCP_SERVICE_GRANT_ID",
        "CONTROL_PLANE_AUTHORITY_RENEWAL_ENABLED", "CONTROL_PLANE_AUTHORITY_PILOT_TTL_SECONDS",
        "CONTROL_PLANE_AUTHORITY_PILOT_WINDOW_SECONDS",
    }
    configuration = {}
    for line in (Path.home() / ".config/codex-control-plane/control-plane.env").read_text().splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key not in allowed:
            continue
        value = value.strip().strip("\"'")
        if key.endswith("_ID"):
            require(IDENTIFIER.fullmatch(value), "RENEWAL_ID_INVALID")
        elif key.endswith("_ENABLED"):
            require(value in {"true", "false"}, "RENEWAL_ENABLED_INVALID")
        else:
            require(value.isdigit() and 1 <= int(value) <= 86400, "RENEWAL_WINDOW_OR_TTL_INVALID")
        configuration[key] = value
    return configuration


def last_safe_renewal_receipt(service):
    """Project only known ID/expiry fields from the latest systemd invocation."""
    invocation = service.get("InvocationID", "")
    if not re.fullmatch(r"[a-f0-9]{32}", invocation):
        return {"state": "no_current_invocation_receipt"}
    try:
        output = subprocess.check_output([
            "journalctl", "--user", "--unit=" + RENEWAL_SERVICE,
            "_SYSTEMD_INVOCATION_ID=" + invocation, "--output=json", "--no-pager", "-n", "100",
        ], text=True, timeout=10)
        require(len(output.encode()) <= 196608, "RENEWAL_JOURNAL_TOO_LARGE")
        selected = None
        for line in output.splitlines():
            message = json.loads(line).get("MESSAGE")
            if not isinstance(message, str) or len(message.encode()) > 16384:
                continue
            try:
                receipt = json.loads(message)
            except (ValueError, TypeError):
                continue
            if (isinstance(receipt, dict) and receipt.get("ok") is True
                    and isinstance(receipt.get("enabled"), bool)):
                selected = receipt
        if selected is None:
            return {"state": "no_success_receipt_in_current_invocation", "invocation_id": invocation}
        projection = {"state": "success_receipt_projected", "invocation_id": invocation,
                      "enabled": selected["enabled"]}
        for field in ("grant_id", "configured_decision_id", "decision_id"):
            value = selected.get(field)
            require(isinstance(value, str) and IDENTIFIER.fullmatch(value), "RENEWAL_RECEIPT_ID_INVALID")
            projection[field] = value
        require(selected.get("admission_mode") in {"scoped_pilot", "recovery", "open"}, "RENEWAL_RECEIPT_MODE_INVALID")
        projection["admission_mode"] = selected["admission_mode"]
        projection["followed_selected_pilot"] = selected.get("followed_selected_pilot") is True
        for field in ("grant", "decision"):
            item = selected.get(field)
            require(isinstance(item, dict) and isinstance(item.get("renewed"), bool)
                    and isinstance(item.get("expires_at_ms"), int) and not isinstance(item["expires_at_ms"], bool)
                    and item["expires_at_ms"] > 0, "RENEWAL_RECEIPT_EXPIRY_INVALID")
            projection[field] = {"renewed": item["renewed"], "expires_at_ms": item["expires_at_ms"]}
        return projection
    except Exception:
        return {"state": "success_receipt_not_verified", "invocation_id": invocation}


def main():
    service = show("codex-control-plane.service", ["MainPID", "ActiveState", "SubState"])
    pid = int(service["MainPID"])
    require(pid > 1, "CONTROL_PLANE_NOT_RUNNING")
    environment = dict(item.split("=", 1) for item in
                       Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in item)
    require(environment.get("CONTROL_PLANE_MCP_AUTH_MODE") == "private_tunnel_service"
            and environment.get("CONTROL_PLANE_MCP_SERVICE_PRINCIPAL_ID") == PRINCIPAL
            and environment.get("CONTROL_PLANE_MCP_SERVICE_GRANT_ID") == GRANT,
            "SERVICE_AUTHORITY_CHANGED")
    require(environment.get("CONTROL_PLANE_MCP_BIND", "127.0.0.1") == "127.0.0.1", "MCP_NOT_LOOPBACK")
    port = int(environment.get("CONTROL_PLANE_MCP_PORT", "8766"))
    require(1024 <= port <= 65535, "MCP_PORT_INVALID")
    database = Path(environment["CONTROL_PLANE_DB"])
    if not database.is_absolute():
        database = Path(f"/proc/{pid}/cwd").resolve() / database
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    connection.row_factory = sqlite3.Row
    credential = Path.home() / ".config/codex-control-plane/ubuntu-root-mcp-authorization"
    metadata = credential.lstat()
    require(stat.S_ISREG(metadata.st_mode) and metadata.st_uid == os.getuid()
            and metadata.st_mode & 0o077 == 0 and metadata.st_size <= 65536, "CREDENTIAL_NOT_PROTECTED")
    token = credential.read_text().strip().removeprefix("Bearer ")
    require(re.fullmatch(r"mcpsvc_[A-Za-z0-9_-]{32,128}", token), "CREDENTIAL_FORMAT_INVALID")
    inventory = rpc(port, "tools/call", {"name": "workspace_context", "arguments": {"operation": "inventory"}},
                    token, "workspace_context")["structuredContent"]
    tools = rpc(port, "tools/list", {}, token)["tools"]
    now = int(time.time() * 1000)
    connection.execute("BEGIN")
    pilots = [dict(row) for row in connection.execute(
        "SELECT decision_id,owner_id,principal_id,binding_id,device_id,endpoint_id,workspace_id,workspace_generation,"
        "created_at_ms,expires_at_ms,revoked_at_ms FROM scoped_pilot_decisions WHERE revoked_at_ms IS NULL AND expires_at_ms>?",
        (now,),
    )]
    require(len(pilots) == 1, "LIVE_PILOT_NOT_UNIQUE")
    pilot = pilots[0]
    require(pilot["device_id"] == DEVICE and pilot["principal_id"] == PRINCIPAL
            and pilot["workspace_id"] == WORKSPACE and pilot["workspace_generation"] == GENERATION,
            "AUTOCAD_PILOT_NOT_SELECTED")
    require(inventory.get("principal_id") == PRINCIPAL and len(inventory.get("targets", [])) == 1,
            "SHARED_INVENTORY_NOT_EXACT")
    target = inventory["targets"][0]
    require(all(target.get(field) == pilot[field] for field in
                ("device_id", "binding_id", "workspace_id", "workspace_generation")), "INVENTORY_PILOT_DISAGREES")
    grant = dict(connection.execute(
        "SELECT grant_id,owner_id,principal_id,scopes_json,expires_at_ms,revoked_at_ms FROM mcp_service_grants WHERE grant_id=?",
        (GRANT,),
    ).fetchone())
    grant["scopes"] = json.loads(grant.pop("scopes_json"))
    node = dict(connection.execute(
        "SELECT device_id,owner_id,endpoint_id,readiness,runtime_instance_id,mcp_server_instance_id,activation_epoch,"
        "contract_version,last_seen_at_ms,revoked_at_ms FROM nodes WHERE device_id=?", (DEVICE,),
    ).fetchone())
    require(grant["owner_id"] == pilot["owner_id"] == node["owner_id"]
            and grant["principal_id"] == PRINCIPAL and grant["revoked_at_ms"] is None
            and grant["expires_at_ms"] > now and node["revoked_at_ms"] is None
            and node["endpoint_id"] == pilot["endpoint_id"], "OBSERVED_AUTHORITY_IDENTITY_DISAGREES")
    current = census(connection, now, workspace_id=pilot["workspace_id"], generation=pilot["workspace_generation"])
    device = census(connection, now)
    unknown_history = [dict(row) for row in connection.execute(
        "SELECT a.action_id,a.workspace_id,a.workspace_generation,a.delivery_state,a.expires_at_ms,a.settled_at_ms,"
        "r.disposition,r.reconciled_at_ms FROM actions a LEFT JOIN action_reconciliations r ON r.action_id=a.action_id "
        "WHERE a.device_id=? AND a.settled_at_ms IS NULL AND a.delivery_state='reconcile_required' "
        "ORDER BY a.created_at_ms,a.action_id LIMIT 100", (DEVICE,),
    )]
    for action in unknown_history:
        action["selected_generation"] = action["workspace_id"] == pilot["workspace_id"] and action["workspace_generation"] == pilot["workspace_generation"]
        action["expired"] = action["expires_at_ms"] <= now
    admission = dict(connection.execute(
        "SELECT state_value AS admission_mode,changed_at_ms FROM control_plane_state WHERE state_key='admission_mode'",
    ).fetchone())
    renewal_events = [dict(row) for row in connection.execute(
        "SELECT event_id,subject_id,created_at_ms FROM events WHERE subject_type='scoped_pilot_decision' "
        "AND subject_id=? AND event_type='scoped_pilot_decision_renewed' ORDER BY created_at_ms DESC LIMIT 5",
        (pilot["decision_id"],),
    )]
    integrity = connection.execute("PRAGMA integrity_check").fetchall()
    integrity_ok = len(integrity) == 1 and integrity[0][0] == "ok"
    connection.close()
    renewal = renewal_configuration()
    renewal_service = show(RENEWAL_SERVICE, ["ActiveState", "SubState", "Result", "ExecMainStatus", "InvocationID",
                                                   "ExecMainStartTimestamp", "ExecMainExitTimestamp"])
    renewal_receipt = last_safe_renewal_receipt(renewal_service)
    renewal_receipt["selected_scope_matches_live_pilot"] = renewal_receipt.get("decision_id") == pilot["decision_id"]
    health = json_response("https://svhome.tail0e4032.ts.net/healthz", 65536)
    try:
        with urllib.request.urlopen("http://127.0.0.1:8768/readyz", timeout=5) as response:
            tunnel = {"status": response.status, "ready": response.status == 200}
    except Exception as error:
        tunnel = {"status": getattr(error, "code", None), "ready": False}
    running_root = Path(f"/proc/{pid}/cwd").resolve()
    renewal_script = running_root / "deploy/control-plane-authority-renewal.py"
    renewal_script_hash = hashlib.sha256(renewal_script.read_bytes()).hexdigest() if renewal_script.is_file() else None
    result = {
        "operation": "final_readonly_autocad_shared_server_surface", "observed_at_ms": now,
        "service_pid": pid, "service": service, "admission": admission,
        "health": {key: health.get(key) for key in ("ok", "schema_version", "declared_source_revision", "package_source_sha256",
                   "expected_package_source_sha256", "service_instance_id")},
        "tool_contract": inventory["tool_contract"], "principal_id": inventory["principal_id"],
        "tool_input_properties": {tool["name"]: list(tool["inputSchema"].get("properties", {})) for tool in tools},
        "live_pilot": pilot, "selected_target": {key: target.get(key) for key in ("binding_id", "device_id", "workspace_id",
            "workspace_generation", "readiness", "presence_state", "dispatch_state", "capabilities")},
        "service_grant": grant, "node": {**node, "heartbeat_age_ms": now - node["last_seen_at_ms"]},
        "current_generation_census": current, "all_current_device_census": device,
        "current_generation_idle": current["unclosed_tasks"] == current["unreleased_writers"] == current["unsettled_actions"] == 0,
        "current_device_live_task_writer_idle": device["live_open_tasks"] == device["live_writers"] == 0,
        "historical_unknown_actions_preserved": unknown_history,
        "unknown_action_projection_limit": 100,
        "unknown_action_projection_truncated": device["reconciliation_required_actions"] > len(unknown_history),
        "history_note": "Historical unknown actions remain unresolved evidence; selected-generation idle does not declare them completed.",
        "renewal_configuration": renewal, "renewal_serving_script_sha256": renewal_script_hash,
        "renewal_timer": show(RENEWAL_TIMER, ["ActiveState", "UnitFileState", "NextElapseUSecRealtime", "LastTriggerUSec"]),
        "renewal_service": renewal_service, "last_safe_renewal_receipt": renewal_receipt,
        "selected_pilot_renewal_events": renewal_events, "tunnel_ready": tunnel,
        "sqlite_integrity_ok": integrity_ok, "sqlite_integrity": "ok" if integrity_ok else "not_ok",
        "database_mutations_performed": False,
    }
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,95}", str(error)) else type(error).__name__
        print(json.dumps({"operation": "final_readonly_autocad_shared_server_surface", "ok": False,
                          "error_code": code}, separators=(",", ":")))
        sys.exit(1)
