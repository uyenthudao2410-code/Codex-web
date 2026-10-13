"""Read-only, content-free central observation of actual ChatGPT write/exec.

No actions are created/replayed and no credential, header, file content or raw
stdout/stderr is emitted. The expected diagnostic is extracted as a fixed
classification only. Run on svhome using trusted SSH stdin.
"""
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import time

GENERATION = "generation_a420c8bfcfcb4e42b5bb7fc5e5cec097"
DEVICE = "4c4b7a5b-7744-49ae-a490-78a528a00471"
BINDING = "bind_71661b1046884174b01c99af5f8546aa"
PILOT = "pilot_dfb3174078d842299c41c6638830e505"
EXEC_ACTION = "act_f1b0df9d4be84f31b931696ff8d8f295"
SINCE = 1791781800000  # 2026-10-12 12:10:00 +07


def main():
    pid = int(subprocess.check_output(["systemctl", "--user", "show", "codex-control-plane.service", "--property=MainPID", "--value"], text=True).strip())
    env = dict(item.split("=", 1) for item in Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in item)
    c = sqlite3.connect(Path(env["CONTROL_PLANE_DB"]).resolve().as_uri() + "?mode=ro", uri=True)
    c.execute("PRAGMA query_only=ON")
    c.execute("BEGIN")
    c.row_factory = sqlite3.Row
    actions = []
    for row in c.execute("SELECT * FROM actions WHERE workspace_generation=? AND created_at_ms>=? ORDER BY created_at_ms", (GENERATION, SINCE)):
        action = {key: row[key] for key in ("action_id", "tool_name", "principal_id") if key in row.keys()}
        action.update({key: row[key] for key in ("binding_id", "device_id", "workspace_id", "workspace_generation", "writer_lease_generation", "scoped_pilot_decision_id", "created_at_ms", "expires_at_ms", "delivery_state", "settled_at_ms")})
        args = json.loads(row["arguments_json"])
        action["operation"] = args.get("operation")
        action["attempts"] = [dict(r) for r in c.execute("SELECT * FROM delivery_attempts WHERE action_id=?", (row["action_id"],))]
        action["tasks"] = [dict(r) for r in c.execute("SELECT t.task_id,t.principal_id,t.binding_id,t.workspace_generation,t.created_at_ms,t.expires_at_ms,t.closed_at_ms FROM mcp_task_action_links l JOIN mcp_task_sessions t ON t.task_id=l.task_id WHERE l.action_id=?", (row["action_id"],))]
        exec_intent = c.execute("SELECT argv_json,argv_digest,cwd,timeout_ms,max_output_bytes,task_id,writer_lease_generation FROM mcp_exec_intents WHERE action_id=?", (row["action_id"],)).fetchone()
        if exec_intent:
            sealed = json.loads(exec_intent["argv_json"])
            argv = sealed["argv"]
            action["exec_intent"] = {k: exec_intent[k] for k in exec_intent.keys() if k != "argv_json"}
            action["exec_intent"]["exact_node_version_argv"] = argv == ["node", "--version"]
            if argv == ["node", "--version"]:
                action["exec_intent"]["argv"] = argv
        action["receipts"] = []
        for receipt in c.execute("SELECT receipt_id,receipt_state,received_at_ms,receipt_digest,payload_json FROM receipts WHERE action_id=? ORDER BY received_at_ms", (row["action_id"],)):
            payload = json.loads(receipt["payload_json"])
            observed = {k: receipt[k] for k in receipt.keys() if k != "payload_json"}
            observed["safe_payload"] = {k: payload[k] for k in ("action_id", "attempt_id", "operation_kind", "operation", "task_id", "writer_lease_generation", "job_id", "command_id", "run_id", "wave_id", "status", "exit_code", "timed_out", "output_bytes", "truncated", "runtime_identity", "facade_contract", "response_sha256", "code", "diagnostic_code") if k in payload}
            diagnostic = re.search(r"sandbox (wsb:[a-z0-9]{8}) is not started", str(payload.get("stderr") or "") + "\n" + str(payload.get("stdout") or ""))
            if diagnostic:
                observed["diagnostic_classification"] = "WINDOWS_SANDBOX_SESSION_NOT_STARTED"
                observed["sandbox_session_id"] = diagnostic.group(1)
                observed["expected_diagnostic_observed"] = True
            document = payload.get("result")
            if isinstance(document, dict):
                observed["document_result"] = {k: document[k] for k in ("operation", "format", "size", "sha256", "target") if k in document}
            file = payload.get("file")
            if isinstance(file, dict):
                observed["file_metadata"] = {k: file[k] for k in ("path", "content_sha256", "total_bytes", "bytes_read", "truncated") if k in file}
            action["receipts"].append(observed)
        actions.append(action)
    node = dict(c.execute("SELECT device_id,readiness,runtime_instance_id,mcp_server_instance_id,activation_epoch,contract_version,last_seen_at_ms FROM nodes WHERE device_id=?", (DEVICE,)).fetchone())
    pilot = dict(c.execute("SELECT decision_id,principal_id,binding_id,device_id,workspace_id,workspace_generation,expires_at_ms,revoked_at_ms FROM scoped_pilot_decisions WHERE decision_id=?", (PILOT,)).fetchone())
    tasks = [dict(r) for r in c.execute("SELECT task_id,principal_id,binding_id,workspace_generation,created_at_ms,closed_at_ms FROM mcp_task_sessions WHERE workspace_generation=? AND (created_at_ms>=? OR closed_at_ms IS NULL) ORDER BY created_at_ms", (GENERATION, SINCE))]
    census = {
        "open_tasks": c.execute("SELECT COUNT(*) FROM mcp_task_sessions WHERE workspace_generation=? AND closed_at_ms IS NULL", (GENERATION,)).fetchone()[0],
        "unreleased_writers": c.execute("SELECT COUNT(*) FROM mcp_task_writer_leases l JOIN mcp_task_sessions t ON t.task_id=l.task_id WHERE t.workspace_generation=? AND l.released_at_ms IS NULL", (GENERATION,)).fetchone()[0],
        "unsettled_current_generation_actions": c.execute("SELECT COUNT(*) FROM actions WHERE workspace_generation=? AND settled_at_ms IS NULL", (GENERATION,)).fetchone()[0],
    }
    original = next(a for a in actions if a["action_id"] == EXEC_ACTION)
    assert original["binding_id"] == BINDING and original["device_id"] == DEVICE
    assert original["scoped_pilot_decision_id"] == PILOT and original["delivery_state"] == "settled"
    assert original["exec_intent"]["exact_node_version_argv"] is True
    assert len(original["attempts"]) == 1 and len(original["receipts"]) == 1
    assert original["receipts"][0]["receipt_state"] == "failed"
    assert original["receipts"][0]["safe_payload"]["exit_code"] == 1
    assert original["receipts"][0]["expected_diagnostic_observed"] is True
    now = int(time.time() * 1000)
    print(json.dumps({"operation": "observe_actual_chatgpt_sandbox_not_started", "observed_at_ms": now,
                      "content_free": True, "mutation_performed": False, "original_action_replayed": False,
                      "since_ms": SINCE, "service_pid": pid, "actions": actions, "tasks": tasks,
                      "node": {**node, "heartbeat_age_ms": now - node["last_seen_at_ms"]},
                      "pilot": pilot, "current_generation_census": census,
                      "original_node_version_failure_verified": True,
                      "schema_and_shared_authority_admitted_actual_invocation": True,
                      "failure_boundary": "native_windows_sandbox_session_lifecycle"}, separators=(",", ":")))
    c.close()


if __name__ == "__main__":
    main()
