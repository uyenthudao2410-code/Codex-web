"""Read-only, content-free observation of the one post-reboot exec attempt."""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ACTION = "act_0dbe0e6b68a34afea0e93ca5e55e4b34"
KEY = "cpex_448df604842b976cee7f2f66215209fca87d89cfb2a51cad955abde9"
JOB = "a389ace9d0b04ee5888a80929e817966"
ROOT = Path(__file__).resolve().parents[3]
PROFILE = Path(os.environ["APPDATA"]) / "web-mcp-assistant"

connection = sqlite3.connect(
    (ROOT / ".coding-tools/orchestration/ledger.sqlite3").as_uri() + "?mode=ro",
    uri=True,
    timeout=2,
)
connection.row_factory = sqlite3.Row
connection.execute("PRAGMA query_only=ON")
idempotency = connection.execute(
    "SELECT idempotency_key, operation, status, error_code, started_at, updated_at, finished_at, summary_json "
    "FROM idempotency_records WHERE idempotency_key=?", (KEY,),
).fetchone()
job = connection.execute(
    "SELECT job_id, command_id, owner, lifecycle_state, root_pid, root_process_token, "
    "started_at, updated_at, finished_at, metadata_json FROM managed_process_jobs WHERE job_id=?",
    (JOB,),
).fetchone()
if idempotency is None or job is None:
    raise RuntimeError("EXACT_EXEC_OBSERVATION_MISSING")
idempotency_value = dict(idempotency)
summary = json.loads(idempotency_value.pop("summary_json"))
idempotency_value["summary"] = {
    key: summary[key] for key in ("category", "error_code", "outcome_unknown") if key in summary
}
job_value = dict(job)
metadata = json.loads(job_value.pop("metadata_json"))
job_value["exit_code"] = metadata.get("exit_code")
active_jobs = connection.execute(
    "SELECT COUNT(*) FROM managed_process_jobs WHERE lifecycle_state "
    "IN ('starting','active','waiting','idle','running','terminating')"
).fetchone()[0]
connection.close()
journal = json.loads((PROFILE / "control-plane-node.json.exec-journal.json").read_text("utf-8"))
entries = [entry for entry in journal["entries"].values() if entry["action_id"] == ACTION]
if len(entries) != 1:
    raise RuntimeError("EXACT_EXEC_JOURNAL_AMBIGUOUS")
entry = entries[0]
receipt = entry["receipt"]
process_query = r"""
$processRows = @(Get-CimInstance Win32_Process -Filter 'name="wxc-exec.exe" or name="wxc-windows-sandbox-daemon.exe" or name="wxc-windows-sandbox-guest.exe" or name="WindowsSandbox.exe" or name="WindowsSandboxClient.exe" or name="WindowsSandboxServer.exe"' | ForEach-Object {
  [PSCustomObject]@{ pid=$_.ProcessId; parent_pid=$_.ParentProcessId; executable=$_.ExecutablePath; started_at=$_.CreationDate.ToUniversalTime().ToString('o') }
})
ConvertTo-Json -InputObject $processRows -Compress
"""
process_result = subprocess.run(
    ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", process_query],
    capture_output=True, timeout=15, check=True,
    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
)
processes = json.loads(process_result.stdout.decode("utf-8-sig"))
value = {
    "observed_at": datetime.now(timezone.utc).isoformat(),
    "phase": "exact_exec_read_only_observation",
    "action_id": ACTION,
    "attempt_id": entry["attempt_id"],
    "journal_state": entry["state"],
    "receipt_state": receipt["receipt_state"],
    "receipt_submitted": receipt.get("receipt_submitted"),
    "receipt_code": receipt["payload"].get("code"),
    "receipt_diagnostic_code": receipt["payload"].get("diagnostic_code"),
    "local_idempotency": idempotency_value,
    "managed_job": job_value,
    "active_managed_job_count": active_jobs,
    "sandbox_host_processes": processes,
    "native_effect": "terminal_spawn_failed",
    "central_state_requires_explicit_reconciliation": True,
    "read_only": True,
    "command_replayed": False,
    "writer_released": False,
}
line = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
with Path(__file__).with_name("postreboot-runtime.jsonl").open("a", encoding="utf-8") as output:
    output.write(line + "\n")
print(line)
