"""Read-only, bounded correlation of a live MCP receipt to its durable Job."""
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

sys.dont_write_bytecode = True
ROOT = Path(r"E:\Github\Tools-Codex-web")
PROFILE = Path(r"C:\Users\daoth\AppData\Roaming\web-mcp-assistant")


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


try:
    action_id, response_sha256 = sys.argv[1:]
    require(re.fullmatch(r"act_[a-f0-9]{32}", action_id), "ACTION_ID_INVALID")
    require(re.fullmatch(r"[a-f0-9]{64}", response_sha256), "RESPONSE_HASH_INVALID")
    journal = json.loads((PROFILE / "control-plane-node.json.exec-journal.json").read_text())
    entries = [entry for entry in journal["entries"].values() if entry.get("action_id") == action_id]
    require(len(entries) == 1, "EXACT_ONE_ATTEMPT_REQUIRED")
    receipt = entries[0]["receipt"]
    payload = receipt["payload"]
    require(receipt["receipt_submitted"] is True and receipt["receipt_state"] == "completed"
            and payload["response_sha256"] == response_sha256 and payload["exit_code"] == 0,
            "MATCHING_SUBMITTED_TERMINAL_RECEIPT_REQUIRED")
    command_id, job_id = payload["command_id"], payload["job_id"]
    require(all(isinstance(value, str) and re.fullmatch(r"[a-zA-Z0-9_-]{1,128}", value)
                for value in (command_id, job_id)), "JOB_IDENTIFIER_INVALID")
    with sqlite3.connect((ROOT / ".coding-tools/orchestration/ledger.sqlite3").as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        rows = connection.execute("SELECT job_id,command_id,run_id,wave_id,root_pid,lifecycle_state,started_at,finished_at "
                                  "FROM managed_process_jobs WHERE job_id=? AND command_id=?", (job_id, command_id)).fetchall()
        require(len(rows) == 1, "EXACT_DURABLE_JOB_REQUIRED")
        job = dict(rows[0])
        require(job["root_pid"] > 0 and job["finished_at"] is not None
                and job["lifecycle_state"] in {"completed", "exited"}, "REAL_TERMINAL_PROCESS_REQUIRED")
        require(job["run_id"] == payload["run_id"] and job["wave_id"] == payload["wave_id"], "JOB_LINEAGE_MISMATCH")
    output = payload["stdout"] + payload["stderr"]
    print(json.dumps({"phase": "native_job_correlated", "ok": True, "action_id": action_id,
                      "attempt_id": entries[0]["attempt_id"], "task_id": payload["task_id"],
                      "job": job, "exit_code": 0, "response_sha256": response_sha256,
                      "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
                      "runtime_identity": payload["runtime_identity"], "ledger_mutated": False}, separators=(",", ":")))
except Exception as error:
    print(json.dumps({"phase": "native_job_correlation_failed", "ok": False,
                      "code": str(error) if isinstance(error, RuntimeError) else type(error).__name__}, separators=(",", ":")))
    raise SystemExit(1) from None
