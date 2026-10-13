"""Read only final serving source, shared schema, pilot/timer and job census."""
import json
from pathlib import Path
import sqlite3
import subprocess
import time
import urllib.request


def show(unit, fields):
    args = ["systemctl", "--user", "show", unit]
    args.extend("--property=" + field for field in fields)
    return dict(line.split("=", 1) for line in subprocess.check_output(args, text=True).splitlines() if "=" in line)


def rpc(method, params, token, name=None):
    params = {**params, "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}}
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json", "Accept": "application/json",
               "MCP-Protocol-Version": "2026-07-28", "Mcp-Method": method}
    if name:
        headers["Mcp-Name"] = name
    request = urllib.request.Request("http://127.0.0.1:8766/mcp", data=json.dumps({"jsonrpc": "2.0", "id": "final-inspection", "method": method, "params": params}).encode(), headers=headers, method="POST")
    return json.loads(urllib.request.urlopen(request, timeout=5).read(196608))["result"]


def main():
    pid = int(show("codex-control-plane.service", ["MainPID"])["MainPID"])
    env = dict(item.split("=", 1) for item in Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in item)
    connection = sqlite3.connect(Path(env["CONTROL_PLANE_DB"]).resolve().as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    connection.row_factory = sqlite3.Row
    token = (Path.home() / ".config/codex-control-plane/ubuntu-root-mcp-authorization").read_text().strip().removeprefix("Bearer ")
    inventory = rpc("tools/call", {"name": "workspace_context", "arguments": {"operation": "inventory"}}, token, "workspace_context")["structuredContent"]
    tools = rpc("tools/list", {}, token)["tools"]
    now = int(time.time() * 1000)
    pilot = [dict(row) for row in connection.execute("SELECT decision_id,principal_id,binding_id,device_id,workspace_id,workspace_generation,expires_at_ms,revoked_at_ms FROM scoped_pilot_decisions WHERE revoked_at_ms IS NULL AND expires_at_ms>?", (now,))]
    grant = dict(connection.execute("SELECT grant_id,principal_id,scopes_json,expires_at_ms,revoked_at_ms FROM mcp_service_grants WHERE grant_id='mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd'").fetchone())
    node = dict(connection.execute("SELECT device_id,readiness,runtime_instance_id,mcp_server_instance_id,activation_epoch,contract_version,last_seen_at_ms FROM nodes WHERE device_id='4c4b7a5b-7744-49ae-a490-78a528a00471'").fetchone())
    census = {
        "open_tasks": connection.execute("SELECT COUNT(*) FROM mcp_task_sessions WHERE workspace_generation='generation_a420c8bfcfcb4e42b5bb7fc5e5cec097' AND closed_at_ms IS NULL").fetchone()[0],
        "unreleased_writers": connection.execute("SELECT COUNT(*) FROM mcp_task_writer_leases l JOIN mcp_task_sessions t ON t.task_id=l.task_id WHERE t.workspace_generation='generation_a420c8bfcfcb4e42b5bb7fc5e5cec097' AND l.released_at_ms IS NULL").fetchone()[0],
        "unsettled_current_generation_actions": connection.execute("SELECT COUNT(*) FROM actions WHERE workspace_generation='generation_a420c8bfcfcb4e42b5bb7fc5e5cec097' AND settled_at_ms IS NULL").fetchone()[0],
    }
    config = (Path.home() / ".config/codex-control-plane/control-plane.env").read_text().splitlines()
    allowed = {"CONTROL_PLANE_SCOPED_PILOT_DECISION_ID", "CONTROL_PLANE_MCP_SERVICE_GRANT_ID", "CONTROL_PLANE_AUTHORITY_RENEWAL_ENABLED", "CONTROL_PLANE_AUTHORITY_PILOT_TTL_SECONDS", "CONTROL_PLANE_AUTHORITY_PILOT_WINDOW_SECONDS"}
    renewal = {line.split("=", 1)[0]: line.split("=", 1)[1] for line in config if "=" in line and line.split("=", 1)[0] in allowed}
    with urllib.request.urlopen("https://svhome.tail0e4032.ts.net/healthz", timeout=5) as response:
        health = json.loads(response.read(65536))
    try:
        with urllib.request.urlopen("http://127.0.0.1:8768/readyz", timeout=5) as response:
            tunnel_ready = {"status": response.status, "ready": response.status == 200}
    except Exception as error:
        tunnel_ready = {"status": getattr(error, "code", None), "ready": False}
    result = {
        "operation": "final_readonly_shared_server_surface", "observed_at_ms": now, "service_pid": pid,
        "health": {key: health.get(key) for key in ("ok", "schema_version", "declared_source_revision", "package_source_sha256", "expected_package_source_sha256", "service_instance_id")},
        "tool_contract": inventory["tool_contract"], "principal_id": inventory["principal_id"],
        "tool_input_properties": {tool["name"]: list(tool["inputSchema"].get("properties", {})) for tool in tools},
        "live_pilot": pilot, "service_grant": grant, "node": {**node, "heartbeat_age_ms": now - node["last_seen_at_ms"]},
        "current_generation_census": census, "renewal_configuration": renewal,
        "renewal_timer": show("codex-control-plane-authority-renewal.timer", ["ActiveState", "UnitFileState", "NextElapseUSecRealtime"]),
        "renewal_service": show("codex-control-plane-authority-renewal.service", ["Result", "ExecMainStatus"]),
        "tunnel_ready": tunnel_ready, "sqlite_integrity": connection.execute("PRAGMA integrity_check").fetchone()[0],
    }
    connection.close()
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
