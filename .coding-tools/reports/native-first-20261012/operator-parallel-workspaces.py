"""Supported operator API packet, run over strict SSH stdin with quarantine/reissue.

No SQL writes, receipt settlement, action replay, credential output or grant changes.
The controller must deploy the reviewed additive candidate before reissue.
"""
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

DEVICE = "4c4b7a5b-7744-49ae-a490-78a528a00471"
ENDPOINT = "executor-4c4b7a5b-7744-49ae-a490-78a528a00471"
OWNER = "owner_default"
PRINCIPAL = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
GRANT = "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"
ANCHOR = "pilot_833530c73c72491ba0163037ae80e8f0"
SCOPES = [
    {"name": "Codex-web", "workspace_id": "workspace_f93b5bac9dc74fae9cea66f44c4ebc94", "workspace_generation": "generation_a420c8bfcfcb4e42b5bb7fc5e5cec097", "binding_id": "bind_71661b1046884174b01c99af5f8546aa"},
    {"name": "Autocad", "workspace_id": "workspace_bc86004be2684b958ab7a9a6f9530cd7", "workspace_generation": "generation_03f9c04f1b14414fa4bfa7d91cc8ea7a", "binding_id": "bind_8cd903180f3146099fea128bf55c0b4b"},
]
READS = ["act_9db9b985a3d648b5b941f2e13a30ee47", "act_52409c69f1b84e08bb3fdd86747f79c3", "act_3849e259d55546639794cec40f63fea8"]
DECLARATION = "HISTORICAL_READ_ONLY_UNKNOWN_EFFECT"


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def state():
    service = subprocess.run(["systemctl", "--user", "show", "codex-control-plane.service", "--property=MainPID", "--value"], capture_output=True, text=True, timeout=10, check=True)
    pid = int(service.stdout.strip())
    require(pid > 1, "SERVICE_NOT_RUNNING")
    environment = dict(item.split("=", 1) for item in Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in item)
    require(environment.get("CONTROL_PLANE_MCP_SERVICE_PRINCIPAL_ID") == PRINCIPAL and environment.get("CONTROL_PLANE_MCP_SERVICE_GRANT_ID") == GRANT, "CONFIGURED_SERVICE_IDENTITY_CHANGED")
    bind = environment.get("CONTROL_PLANE_BIND", "127.0.0.1")
    port = int(environment.get("CONTROL_PLANE_PORT", "8765"))
    require(bind in {"127.0.0.1", "100.116.112.22"} and 1024 <= port <= 65535, "OPERATOR_BIND_UNEXPECTED")
    database = Path(environment["CONTROL_PLANE_DB"])
    if not database.is_absolute():
        database = Path(f"/proc/{pid}/cwd").resolve() / database
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    token = environment["CONTROL_PLANE_OPERATOR_TOKEN"]
    require(bool(token), "OPERATOR_TOKEN_MISSING")
    return connection, f"http://{bind}:{port}", token


def api(base, token, path, body=None):
    request = Request(base + path, method="GET" if body is None else "POST", headers={"Authorization": "Bearer " + token, "Content-Type": "application/json", "Accept": "application/json"}, data=None if body is None else json.dumps(body, separators=(",", ":")).encode())
    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read(1048577)
        require(len(raw) <= 1048576, "OPERATOR_RESPONSE_TOO_LARGE")
        result = json.loads(raw)
        require(isinstance(result, dict), "OPERATOR_RESPONSE_INVALID")
        return result
    except HTTPError as error:
        raise RuntimeError("OPERATOR_API_HTTP_" + str(error.code)) from None


def historical_digest(connection):
    connection.execute("BEGIN")
    try:
        history = {name: [dict(row) for action in READS for row in connection.execute("SELECT * FROM " + name + " WHERE action_id=?", (action,))]
                   for name in ("actions", "delivery_attempts", "receipts")}
        return hashlib.sha256(json.dumps(history, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    finally:
        connection.execute("ROLLBACK")


def quarantine(connection, base, token):
    pending = []
    for action_id in READS:
        row = connection.execute("SELECT * FROM actions WHERE action_id=?", (action_id,)).fetchone()
        require(row is not None and row["owner_id"] == OWNER and row["device_id"] == DEVICE and row["binding_id"] == SCOPES[1]["binding_id"] and row["workspace_id"] == SCOPES[1]["workspace_id"] and row["workspace_generation"] == SCOPES[1]["workspace_generation"] and row["tool_name"] == "workspace_context" and row["delivery_state"] == "reconcile_required" and row["settled_at_ms"] is None, "UNKNOWN_READ_SCOPE_OR_STATE_CHANGED")
        receipt = connection.execute("SELECT * FROM receipts WHERE action_id=? ORDER BY received_at_ms DESC,receipt_id DESC LIMIT 1", (action_id,)).fetchone()
        require(receipt is not None and receipt["receipt_state"] == "unknown" and not receipt["local_handle"], "UNKNOWN_RECEIPT_CHANGED")
        require(connection.execute("SELECT 1 FROM mcp_file_read_intents WHERE action_id=? AND principal_id=? AND binding_id=?", (action_id, PRINCIPAL, SCOPES[1]["binding_id"])).fetchone() is not None, "UNKNOWN_FILE_READ_INTENT_CHANGED")
        disposition = connection.execute("SELECT disposition,declaration FROM action_reconciliations WHERE action_id=?", (action_id,)).fetchone()
        if disposition is None:
            pending.append(action_id)
        else:
            require(disposition["disposition"] == "quarantined_unknown" and disposition["declaration"] == DECLARATION, "UNKNOWN_DISPOSITION_CHANGED")
    before = historical_digest(connection)
    if pending:
        result = api(base, token, "/v1/action-reconciliations/quarantine-historical-unknown", {"device_id": DEVICE, "action_ids": pending, "declaration": DECLARATION})
        require({item["action_id"] for item in result["actions"]} == set(pending), "QUARANTINE_RECEIPT_CHANGED")
    require(historical_digest(connection) == before, "UNKNOWN_HISTORY_MUTATED")
    return {"quarantined_action_ids": READS, "new_dispositions": len(pending), "immutable_history_sha256": before, "actions_settled": False, "actions_replayed": False}


def reissue(connection, base, token):
    require(api(base, token, "/v1/maintenance/admission").get("admission_mode") == "recovery", "REISSUE_REQUIRES_RECOVERY_FENCE")
    now = int(time.time() * 1000)
    grant = connection.execute("SELECT * FROM mcp_service_grants WHERE grant_id=?", (GRANT,)).fetchone()
    anchor = connection.execute("SELECT * FROM scoped_pilot_decisions WHERE decision_id=?", (ANCHOR,)).fetchone()
    require(grant is not None and anchor is not None and grant["owner_id"] == OWNER and grant["principal_id"] == PRINCIPAL and grant["revoked_at_ms"] is None, "SERVICE_GRANT_CHANGED")
    require(all(anchor[field] == value for field, value in {"owner_id": OWNER, "principal_id": PRINCIPAL, "device_id": DEVICE, "endpoint_id": ENDPOINT, **{field: SCOPES[1][field] for field in ("binding_id", "workspace_id", "workspace_generation")}}.items()) and anchor["revoked_at_ms"] is not None, "REVOKED_ANCHOR_CHANGED")
    expiry = min(anchor["expires_at_ms"], grant["expires_at_ms"], now + 24 * 60 * 60 * 1000 - 1000)
    require(expiry > now + 60000, "APPROVED_AUTHORITY_WINDOW_EXPIRED")
    for scope in SCOPES:
        binding = connection.execute("SELECT * FROM bindings WHERE binding_id=?", (scope["binding_id"],)).fetchone()
        require(binding is not None and binding["revoked_at_ms"] is None and all(binding[field] == value for field, value in {"owner_id": OWNER, "device_id": DEVICE, "endpoint_id": ENDPOINT, **{field: scope[field] for field in ("workspace_id", "workspace_generation")}}.items()), "TARGET_BINDING_CHANGED")
        require(connection.execute("SELECT 1 FROM node_workspaces WHERE device_id=? AND workspace_id=? AND workspace_generation=? AND retired_at_ms IS NULL", (DEVICE, scope["workspace_id"], scope["workspace_generation"])).fetchone() is not None, "TARGET_GENERATION_CHANGED")
    pins = []
    for scope in SCOPES:
        current = api(base, token, "/v1/scoped-pilot-decisions")["scoped_pilot_decisions"]
        active = [item for item in current if item["principal_id"] == PRINCIPAL and item["binding_id"] == scope["binding_id"] and item["revoked_at_ms"] is None and item["expires_at_ms"] > now]
        require(len(active) <= 1, "AMBIGUOUS_TARGET_DECISIONS")
        decision = active[0] if active else api(base, token, "/v1/scoped-pilot-decisions", {"principal_id": PRINCIPAL, "binding_id": scope["binding_id"], "expires_at_ms": expiry, "reason": "Authorized parallel Codex-web and Autocad activation"})
        require(all(decision[field] == value for field, value in {"owner_id": OWNER, "principal_id": PRINCIPAL, "device_id": DEVICE, "endpoint_id": ENDPOINT, **{field: scope[field] for field in ("binding_id", "workspace_id", "workspace_generation")}}.items()) and decision["revoked_at_ms"] is None and decision["expires_at_ms"] == expiry, "REISSUED_SCOPE_CHANGED")
        pins.append({**scope, "decision_id": decision["decision_id"], "expires_at_ms": expiry})
    require(api(base, token, "/v1/maintenance/admission", {"mode": "scoped_pilot"}).get("admission_mode") == "scoped_pilot", "ADMISSION_REOPEN_FAILED")
    return {"device_id": DEVICE, "endpoint_id": ENDPOINT, "principal_id": PRINCIPAL, "grant_id": GRANT, "configured_anchor_decision_id": ANCHOR, "targets": pins, "admission_mode": "scoped_pilot", "grant_changed": False}


def main():
    mode = sys.argv[1] if len(sys.argv) == 2 else ""
    require(mode in {"quarantine", "reissue"}, "PACKET_MODE_REQUIRED")
    connection, base, token = state()
    result = quarantine(connection, base, token) if mode == "quarantine" else reissue(connection, base, token)
    print(json.dumps({"ok": True, "mode": mode, **result}, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print(json.dumps({"ok": False, "error_code": code, "action_replay_performed": False}, separators=(",", ":")))
        sys.exit(2)
