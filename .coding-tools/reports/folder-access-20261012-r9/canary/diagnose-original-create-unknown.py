"""Read-only fixed-target diagnostic; credentials and raw receipt payloads stay private."""
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request

ACTION = "act_ed8982433bf347ef8c32aebc17b23d43"
TASK = "task_09461f4e2d3b4992811812e816a6edbc"
PID = 946413
DEVICE = "4c4b7a5b-7744-49ae-a490-78a528a00471"
PRINCIPAL = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
GRANT = "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"


def require(value, code):
    if not value:
        raise RuntimeError(code)


def codes(value, prefix="", found=None):
    found = {} if found is None else found
    if isinstance(value, dict):
        for key, item in value.items():
            location = prefix + "." + key if prefix else key
            if key in {"code", "diagnostic_code", "error_code", "reason_code", "failure_code", "rejection_code", "effect_state", "state", "operation_kind"} and isinstance(item, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,127}", item):
                found[location] = item
            elif key in {"exit_code", "returncode", "byte_count", "bytes_written", "schema_version", "receipt_submitted", "effect_applied", "effect_started"} and isinstance(item, (int, bool)):
                found[location] = item
            if isinstance(item, (dict, list)):
                codes(item, location, found)
    elif isinstance(value, list):
        for index, item in enumerate(value[:64]):
            codes(item, prefix + "[" + str(index) + "]", found)
    return found


def pick(row, names):
    return {key: row[key] for key in names if key in row.keys()}


def main():
    current_pid = int(subprocess.check_output(["systemctl", "--user", "show", "codex-control-plane.service", "--property=MainPID", "--value"], text=True).strip())
    require(current_pid == PID, "EXACT_RUNNING_SERVICE_CHANGED")
    environment = dict(item.split("=", 1) for item in Path(f"/proc/{PID}/environ").read_text().split("\0") if "=" in item)
    require(environment.get("CONTROL_PLANE_MCP_AUTH_MODE") == "private_tunnel_service" and environment.get("CONTROL_PLANE_MCP_SERVICE_PRINCIPAL_ID") == PRINCIPAL and environment.get("CONTROL_PLANE_MCP_SERVICE_GRANT_ID") == GRANT, "EXACT_PRIVATE_SERVICE_CHANGED")
    database = Path(environment["CONTROL_PLANE_DB"])
    if not database.is_absolute():
        database = Path(f"/proc/{PID}/cwd").resolve() / database
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    connection.row_factory = sqlite3.Row
    connection.execute("BEGIN")
    action = connection.execute("SELECT * FROM actions WHERE action_id=?", (ACTION,)).fetchone()
    require(action is not None and action["device_id"] == DEVICE, "EXACT_ACTION_NOT_FOUND")
    task = connection.execute("SELECT * FROM mcp_task_sessions WHERE task_id=?", (TASK,)).fetchone()
    require(task is not None and task["principal_id"] == PRINCIPAL, "EXACT_TASK_NOT_FOUND")
    attempts = connection.execute("SELECT * FROM delivery_attempts WHERE action_id=? ORDER BY attempt_number", (ACTION,)).fetchall()
    receipts = connection.execute("SELECT * FROM receipts WHERE action_id=? ORDER BY received_at_ms", (ACTION,)).fetchall()
    receipt_summaries = []
    for row in receipts:
        payload = json.loads(row["payload_json"])
        receipt_summaries.append({**pick(row, ("receipt_id", "receipt_state", "attempt_id", "received_at_ms", "receipt_digest")), "payload_keys": sorted(payload), "safe_codes": codes(payload), "payload_sha256": hashlib.sha256(row["payload_json"].encode()).hexdigest()})
    report = {"operation": "diagnose_original_create_unknown", "read_only": True, "observed_at_ms": int(time.time() * 1000), "service_pid": PID, "action": pick(action, ("action_id", "action_digest", "tool_name", "device_id", "workspace_id", "workspace_generation", "delivery_state", "created_at_ms", "expires_at_ms", "settled_at_ms")), "task": pick(task, ("task_id", "principal_id", "binding_id", "workspace_id", "workspace_generation", "scoped_pilot_decision_id", "closed_at_ms")), "attempts": [pick(row, ("attempt_id", "attempt_number", "dispatched_at_ms", "receipt_state")) for row in attempts], "receipts": receipt_summaries}
    connection.rollback()
    connection.close()
    token = Path("/home/svhome/.config/codex-control-plane/ubuntu-root-mcp-authorization").read_text().strip()
    if token.startswith("Bearer "):
        token = token[7:]
    require(re.fullmatch(r"mcpsvc_[A-Za-z0-9_-]{32,128}", token) is not None, "CANONICAL_CREDENTIAL_FORMAT_INVALID")
    port = int(environment.get("CONTROL_PLANE_MCP_PORT", "8766"))
    print(json.dumps({**report, "phase": "database_snapshot"}, separators=(",", ":")), flush=True)
    request = urllib.request.Request(f"http://127.0.0.1:{port}/mcp", data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "document_workflow", "arguments": {"operation": "doc_status", "action_id": ACTION}, "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}}}).encode(), headers={"Authorization": "Bearer " + token, "Content-Type": "application/json", "Accept": "application/json", "MCP-Protocol-Version": "2026-07-28", "Mcp-Method": "tools/call", "Mcp-Name": "document_workflow"}, method="POST")
    with urllib.request.urlopen(request, timeout=15) as response:
        body = json.loads(response.read(196608))
    require(body.get("id") == 1 and "error" not in body, "READ_ONLY_MCP_STATUS_FAILED")
    result = body.get("result", {})
    require(result.get("isError") is not True, "READ_ONLY_MCP_STATUS_TOOL_ERROR")
    observed = result.get("structuredContent", {})
    require(observed.get("action", {}).get("action_id") == ACTION, "STATUS_ACTION_CHANGED")
    report["mcp_status"] = {"execution": observed.get("execution"), "reconciliation_required": observed.get("reconciliation_required"), "action": observed.get("action")}
    print(json.dumps(report, separators=(",", ":")))


try:
    main()
except Exception as error:
    code = "HTTP_" + str(error.code) if isinstance(error, urllib.error.HTTPError) else str(error) if isinstance(error, RuntimeError) and re.fullmatch(r"[A-Z_]+", str(error)) else type(error).__name__
    print(json.dumps({"operation": "diagnose_original_create_unknown", "read_only": True, "ok": False, "code": code}))
    raise SystemExit(1)
