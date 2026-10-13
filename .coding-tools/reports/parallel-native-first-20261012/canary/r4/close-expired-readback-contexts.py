"""Close only the two never-delivered, expired readback contexts via owner API."""
import json, sqlite3, subprocess, time, urllib.request
from pathlib import Path

EXPECTED = {
    "act_35a75277c9ae475d80fe261538a25f8c": "task_bbcc6734f25c459facf993daa17d7b0d",
    "act_07d238b6f4e84217a92fe7ac05c9c4dd": "task_31f64ba3f35d423089d90e19e6d2118a",
}
WORKSPACE = "workspace_f93b5bac9dc74fae9cea66f44c4ebc94"
GENERATION = "generation_a420c8bfcfcb4e42b5bb7fc5e5cec097"

def require(ok, code):
    if not ok:
        raise RuntimeError(code)

def main():
    pid = int(subprocess.check_output(["systemctl", "--user", "show", "codex-control-plane.service", "--property=MainPID", "--value"], text=True))
    require(pid == 970133, "SERVING_PROCESS_CHANGED")
    env = dict(x.split("=", 1) for x in Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in x)
    database = Path(env["CONTROL_PLANE_DB"])
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    now = int(time.time() * 1000)
    rows = []
    for aid, task_id in EXPECTED.items():
        action = connection.execute("SELECT * FROM actions WHERE action_id=?", (aid,)).fetchone()
        require(action is not None and action["delivery_state"] == "queued" and action["settled_at_ms"] is None and action["expires_at_ms"] < now, "ACTION_NOT_EXACT_EXPIRED_QUEUE")
        require(action["workspace_id"] == WORKSPACE and action["workspace_generation"] == GENERATION and action["tool_name"] == "workspace_context", "ACTION_SCOPE_CHANGED")
        arguments = json.loads(action["arguments_json"])
        require(arguments["operation"] == "read_file" and arguments["path"] == "tests/fixtures/native-first-canary/build-artifact.txt", "ACTION_NOT_ARTIFACT_READBACK")
        require(connection.execute("SELECT COUNT(*) FROM delivery_attempts WHERE action_id=?", (aid,)).fetchone()[0] == 0, "ACTION_WAS_DELIVERED")
        require(connection.execute("SELECT COUNT(*) FROM receipts WHERE action_id=?", (aid,)).fetchone()[0] == 0, "ACTION_HAS_RECEIPT")
        require(connection.execute("SELECT COUNT(*) FROM actions WHERE context_id=?", (action["context_id"],)).fetchone()[0] == 1, "CONTEXT_NOT_EXCLUSIVE")
        task = connection.execute("SELECT closed_at_ms FROM mcp_task_sessions WHERE task_id=?", (task_id,)).fetchone()
        require(task is not None and task[0] is not None, "TASK_NOT_CLOSED")
        require(connection.execute("SELECT COUNT(*) FROM mcp_task_writer_leases WHERE task_id=? AND released_at_ms IS NULL", (task_id,)).fetchone()[0] == 0, "TASK_WRITER_NOT_RELEASED")
        require(connection.execute("SELECT task_id FROM mcp_task_action_links WHERE action_id=?", (aid,)).fetchone()[0] == task_id, "TASK_LINK_CHANGED")
        context = connection.execute("SELECT closed_at_ms FROM contexts WHERE context_id=?", (action["context_id"],)).fetchone()
        require(context is not None and context[0] is None, "CONTEXT_ALREADY_CLOSED")
        rows.append(dict(action))
    port = int(env.get("CONTROL_PLANE_PORT", "8765"))
    bind = env.get("CONTROL_PLANE_BIND", "127.0.0.1")
    results = []
    for row in rows:
        request = urllib.request.Request(f"http://{bind}:{port}/v1/contexts/{row['context_id']}/close", data=b"{}", method="POST", headers={"Authorization": "Bearer " + env["CONTROL_PLANE_OPERATOR_TOKEN"], "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read(65536))
        require(result.get("context_id") == row["context_id"] and result.get("closed_at_ms") is not None, "CONTEXT_CLOSE_NOT_VERIFIED")
        action = connection.execute("SELECT delivery_state,settled_at_ms FROM actions WHERE action_id=?", (row["action_id"],)).fetchone()
        require(action[0] == "settled" and action[1] is not None, "ACTION_NOT_REFUSED")
        require(connection.execute("SELECT COUNT(*) FROM delivery_attempts WHERE action_id=?", (row["action_id"],)).fetchone()[0] == 0 and connection.execute("SELECT COUNT(*) FROM receipts WHERE action_id=?", (row["action_id"],)).fetchone()[0] == 0, "ACTION_DELIVERY_CHANGED")
        results.append({"action_id": row["action_id"], "context_id": row["context_id"], "delivery_state": action[0], "settled_at_ms": action[1], "delivery_attempts": 0, "receipts": 0, "reason": "context_closed"})
    connection.close()
    print(json.dumps({"operation": "close_expired_readback_contexts", "ok": True, "observed_at_ms": int(time.time() * 1000), "source_service_pid": pid, "action_replay_performed": False, "new_dispatch_performed": False, "failed_canary_receipts_preserved": True, "actions": results}, separators=(",", ":")), flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"operation": "close_expired_readback_contexts", "ok": False, "error_code": str(error) if isinstance(error, RuntimeError) else type(error).__name__}), flush=True)
        raise SystemExit(1)
