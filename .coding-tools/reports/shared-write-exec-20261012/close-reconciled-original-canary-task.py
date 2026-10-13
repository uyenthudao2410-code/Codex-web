"""Release/close only the original settled canary task via canonical MCP.

Run on svhome through SSH stdin. SQLite is read-only. The only mutations are
the two exact supported calls below; credentials and raw results stay private.
"""
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import subprocess
import time
import urllib.error
import urllib.request

TASK = "task_44cc616e4b8b4180b046974651f52557"
ACTION = "act_051f354f679c45779fc32dab793e43c6"
ATTEMPT = "try_764317ee30904d34ab41452a7c25bfb7"
UNKNOWN = "rcpt_8816464bf6db4589a0e58316c5fee19f"
BINDING = "bind_71661b1046884174b01c99af5f8546aa"
GENERATION = "generation_a420c8bfcfcb4e42b5bb7fc5e5cec097"
DEVICE = "4c4b7a5b-7744-49ae-a490-78a528a00471"
PILOT = "pilot_dfb3174078d842299c41c6638830e505"
PRINCIPAL = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
GRANT = "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"
PROTOCOL = "2026-07-28"
PHASE = "preflight"


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def sha_json(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def census(connection):
    return {
        "open_tasks": connection.execute("SELECT COUNT(*) FROM mcp_task_sessions WHERE workspace_generation=? AND closed_at_ms IS NULL", (GENERATION,)).fetchone()[0],
        "unreleased_writers": connection.execute("SELECT COUNT(*) FROM mcp_task_writer_leases l JOIN mcp_task_sessions t ON t.task_id=l.task_id WHERE t.workspace_generation=? AND l.released_at_ms IS NULL", (GENERATION,)).fetchone()[0],
        "unsettled_current_generation_actions": connection.execute("SELECT COUNT(*) FROM actions WHERE workspace_generation=? AND settled_at_ms IS NULL", (GENERATION,)).fetchone()[0],
    }


def main():
    global PHASE
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-close-exact-reconciled-task", action="store_true", required=True)
    parser.parse_args()
    pid = int(subprocess.check_output(["systemctl", "--user", "show", "codex-control-plane.service", "--property=MainPID", "--value"], text=True).strip())
    require(pid == 921509, "REVIEWED_SERVING_PROCESS_CHANGED")
    environment = dict(item.split("=", 1) for item in Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in item)
    require(environment["CONTROL_PLANE_MCP_AUTH_MODE"] == "private_tunnel_service"
            and environment["CONTROL_PLANE_MCP_SERVICE_PRINCIPAL_ID"] == PRINCIPAL
            and environment["CONTROL_PLANE_MCP_SERVICE_GRANT_ID"] == GRANT,
            "CANONICAL_PRIVATE_SERVICE_CHANGED")
    connection = sqlite3.connect(Path(environment["CONTROL_PLANE_DB"]).resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    task = connection.execute("SELECT * FROM mcp_task_sessions WHERE task_id=?", (TASK,)).fetchone()
    require(task is not None and task["binding_id"] == BINDING and task["principal_id"] == PRINCIPAL
            and task["workspace_generation"] == GENERATION and task["closed_at_ms"] is None,
            "EXACT_ORIGINAL_TASK_NOT_OPEN")
    original = connection.execute("SELECT delivery_state,settled_at_ms,device_id,workspace_generation FROM actions WHERE action_id=?", (ACTION,)).fetchone()
    require(original and original["delivery_state"] == "settled" and original["settled_at_ms"] is not None
            and original["device_id"] == DEVICE and original["workspace_generation"] == GENERATION,
            "ORIGINAL_ACTION_NOT_VERIFIED_SETTLED")
    receipts = connection.execute("SELECT receipt_id,receipt_state,payload_json,local_handle FROM receipts WHERE action_id=?", (ACTION,)).fetchall()
    require(len(receipts) == 2
            and sum(r["receipt_id"] == UNKNOWN and r["receipt_state"] == "unknown" for r in receipts) == 1,
            "ORIGINAL_UNKNOWN_RECEIPT_NOT_PRESERVED")
    failed = [r for r in receipts if r["receipt_state"] == "failed"]
    require(len(failed) == 1 and failed[0]["local_handle"] == ""
            and sha_json(json.loads(failed[0]["payload_json"])) == "55e0556baa657e094d16d6a95f7f94a207ac0af572d83e0bb19d6ee9950310e7",
            "EXACT_OBSERVER_FAILED_RECEIPT_MISSING")
    attempts = connection.execute("SELECT attempt_id FROM delivery_attempts WHERE action_id=?", (ACTION,)).fetchall()
    require(len(attempts) == 1 and attempts[0]["attempt_id"] == ATTEMPT, "ORIGINAL_ATTEMPT_CHANGED")
    require(census(connection) == {"open_tasks": 1, "unreleased_writers": 1, "unsettled_current_generation_actions": 0},
            "OTHER_CURRENT_TASK_OR_ACTION_PRESENT")
    pilot = dict(connection.execute("SELECT * FROM scoped_pilot_decisions WHERE decision_id=?", (PILOT,)).fetchone())
    require(pilot["binding_id"] == BINDING and pilot["device_id"] == DEVICE
            and pilot["workspace_generation"] == GENERATION and pilot["principal_id"] == PRINCIPAL
            and pilot["revoked_at_ms"] is None and pilot["expires_at_ms"] > int(time.time() * 1000) + 60000,
            "ORIGINAL_PILOT_CHANGED")
    credential = Path.home() / ".config/codex-control-plane/ubuntu-root-mcp-authorization"
    info = credential.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_mode & 0o077 == 0,
            "CANONICAL_CREDENTIAL_NOT_PROTECTED")
    token = credential.read_text().strip().removeprefix("Bearer ")
    require(re.fullmatch(r"mcpsvc_[A-Za-z0-9_-]{32,128}", token), "CANONICAL_CREDENTIAL_FORMAT_INVALID")
    grant = connection.execute("SELECT token_digest,principal_id,expires_at_ms,revoked_at_ms FROM mcp_service_grants WHERE grant_id=?", (GRANT,)).fetchone()
    expected = hashlib.sha256(b"coding-tools-control-plane:mcp-service-grant:v1\0" + token.encode()).hexdigest()
    require(grant and hmac.compare_digest(expected, grant["token_digest"])
            and grant["principal_id"] == PRINCIPAL and grant["revoked_at_ms"] is None
            and grant["expires_at_ms"] > int(time.time() * 1000) + 60000, "EXACT_LIVE_SERVICE_GRANT_REQUIRED")

    def call(name, arguments):
        body = {"jsonrpc": "2.0", "id": arguments["operation"], "method": "tools/call", "params": {
            "name": name, "arguments": arguments, "_meta": {
                "io.modelcontextprotocol/protocolVersion": PROTOCOL,
                "io.modelcontextprotocol/clientCapabilities": {}}}}
        request = urllib.request.Request("http://127.0.0.1:8766/mcp", data=json.dumps(body).encode(), method="POST",
                                         headers={"Authorization": "Bearer " + token,
                                                  "Content-Type": "application/json", "Accept": "application/json",
                                                  "MCP-Protocol-Version": PROTOCOL,
                                                  "Mcp-Method": "tools/call", "Mcp-Name": name})
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read(196609)
        require(len(raw) <= 196608, "MCP_RESPONSE_TOO_LARGE")
        result = json.loads(raw)
        require("error" not in result and result.get("result", {}).get("isError") is not True,
                "SUPPORTED_TASK_CLEANUP_REJECTED")

    PHASE = "writer_release"
    call("task_control", {"operation": "writer_release", "task_id": TASK,
                          "reason": "original_native_PROTECTED_PATH_WRITE_reconciled_failed"})
    require(census(connection) == {"open_tasks": 1, "unreleased_writers": 0, "unsettled_current_generation_actions": 0},
            "ORIGINAL_WRITER_RELEASE_NOT_VERIFIED")
    PHASE = "task_close"
    call("workspace_context", {"operation": "task_close", "task_id": TASK})
    after = census(connection)
    require(after == {"open_tasks": 0, "unreleased_writers": 0, "unsettled_current_generation_actions": 0},
            "ORIGINAL_TASK_CLOSE_NOT_VERIFIED")
    require(dict(connection.execute("SELECT * FROM scoped_pilot_decisions WHERE decision_id=?", (PILOT,)).fetchone()) == pilot,
            "PILOT_CHANGED_DURING_TASK_CLEANUP")
    node = dict(connection.execute("SELECT device_id,readiness,runtime_instance_id,mcp_server_instance_id,activation_epoch,last_seen_at_ms FROM nodes WHERE device_id=?", (DEVICE,)).fetchone())
    require(node["readiness"] == "ready" and node["runtime_instance_id"] == "ev_bVSX46CWc8WG5"
            and node["mcp_server_instance_id"] == "XobFwIqZETgu9SLo"
            and node["activation_epoch"] == "activation-mv4r64ul-235cac58cc9592bd08ffc95abe94a111"
            and 0 <= int(time.time() * 1000) - node["last_seen_at_ms"] <= 30000,
            "EXACT_R5_NODE_NOT_CURRENT_READY")
    print(json.dumps({"operation": "close_reconciled_original_canary_task", "ok": True,
                      "observed_at_ms": int(time.time() * 1000), "task_id": TASK, "action_id": ACTION,
                      "supported_mcp_calls": ["task_control.writer_release", "workspace_context.task_close"],
                      "current_generation_census": after, "node": node,
                      "unknown_receipt_preserved": True, "database_writer_instantiated": False,
                      "original_action_replayed": False, "pilot_unchanged": True}, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else "HTTP_" + str(error.code) if isinstance(error, urllib.error.HTTPError) else type(error).__name__
        print(json.dumps({"operation": "close_reconciled_original_canary_task", "ok": False,
                          "phase": PHASE, "code": code}))
        raise SystemExit(1)
