"""Observe the exact successful r5 exec journal and native terminal job read-only."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ACTION = "act_2de8172636ef4cdba9e388c203855f6b"
ROOT = Path(__file__).resolve().parents[3]
PROFILE = Path(os.environ["APPDATA"]) / "web-mcp-assistant"
journal = json.loads((PROFILE / "control-plane-node.json.exec-journal.json").read_text("utf-8"))
entries = [entry for entry in journal["entries"].values() if entry["action_id"] == ACTION]
if len(entries) != 1:
    raise RuntimeError("EXACT_SUCCESSFUL_EXEC_JOURNAL_AMBIGUOUS")
entry = entries[0]
receipt = entry["receipt"]
payload = receipt["payload"]
if (entry["state"], receipt["receipt_state"], receipt.get("receipt_submitted"), payload["status"], payload["exit_code"]) != ("completed", "completed", True, "exited", 0):
    raise RuntimeError("EXACT_SUCCESSFUL_EXEC_RECEIPT_UNPROVEN")
command_id, job_id = payload["command_id"], payload["job_id"]
connection = sqlite3.connect(
    (ROOT / ".coding-tools/orchestration/ledger.sqlite3").as_uri() + "?mode=ro",
    uri=True, timeout=2,
)
connection.row_factory = sqlite3.Row
connection.execute("PRAGMA query_only=ON")
row = connection.execute(
    "SELECT job_id,command_id,owner,lifecycle_state,root_pid,root_process_token,started_at,updated_at,finished_at,metadata_json "
    "FROM managed_process_jobs WHERE job_id=? AND command_id=?", (job_id, command_id),
).fetchone()
if row is None or row["owner"] != "control-plane-exec-bridge" or row["lifecycle_state"] != "exited" or not row["finished_at"]:
    raise RuntimeError("EXACT_SUCCESSFUL_NATIVE_JOB_UNPROVEN")
job = dict(row)
metadata = json.loads(job.pop("metadata_json"))
if metadata.get("exit_code") != 0:
    raise RuntimeError("EXACT_NATIVE_EXIT_CODE_UNPROVEN")
job["exit_code"] = metadata["exit_code"]
active_jobs = connection.execute(
    "SELECT COUNT(*) FROM managed_process_jobs WHERE lifecycle_state IN ('starting','active','waiting','idle','running','terminating')"
).fetchone()[0]
connection.close()
if active_jobs:
    raise RuntimeError("ACTIVE_NATIVE_JOBS_REMAIN")
value = {
    "observed_at": datetime.now(timezone.utc).isoformat(),
    "phase": "final_exact_r5_native_job_observation",
    "action_id": ACTION, "attempt_id": entry["attempt_id"],
    "task_id": payload["task_id"],
    "journal_state": entry["state"],
    "receipt_state": receipt["receipt_state"], "receipt_submitted": True,
    "command_id": command_id, "job_id": job_id,
    "status": payload["status"], "exit_code": payload["exit_code"],
    "output_bytes": payload["output_bytes"],
    "stdout_sha256": hashlib.sha256(payload["stdout"].encode("utf-8")).hexdigest(),
    "stderr_sha256": hashlib.sha256(payload["stderr"].encode("utf-8")).hexdigest(),
    "response_sha256": payload["response_sha256"],
    "managed_job": job, "active_managed_job_count": active_jobs,
    "read_only": True, "sqlite_query_only": True,
    "command_replayed": False, "runtime_mutated": False,
}
line = json.dumps(value, separators=(",", ":"))
with Path(__file__).with_name("postreboot-runtime.r5-activation.jsonl").open("a", encoding="utf-8") as output:
    output.write(line + "\n")
print(line)
