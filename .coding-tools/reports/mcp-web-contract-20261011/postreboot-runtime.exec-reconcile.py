"""Prepare, or explicitly submit, one evidence-bound terminal failed receipt.

Default is read-only preparation. No command is executed or replayed. The
original unknown node journal remains unchanged, including after submission.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ACTION = "act_0dbe0e6b68a34afea0e93ca5e55e4b34"
ATTEMPT = "try_b165ade7805f44249af6efe4f3b0321e"
KEY = "cpex_448df604842b976cee7f2f66215209fca87d89cfb2a51cad955abde9"
JOB = "a389ace9d0b04ee5888a80929e817966"
COMMAND = "lpEXvw0QYM4KAWZD0EAhw5nm"
ROOT = Path(__file__).resolve().parents[3]
PROFILE = Path(os.environ["APPDATA"]) / "web-mcp-assistant"
CANDIDATE = ROOT / "dist/windows-candidate-mxc-wsb-cbe1774-mcp-feedback-1011-r4/win-unpacked"
parser = argparse.ArgumentParser()
parser.add_argument("--submit", action="store_true")
args = parser.parse_args()
journal_path = PROFILE / "control-plane-node.json.exec-journal.json"
journal_digest = hashlib.sha256(journal_path.read_bytes()).hexdigest()
journal = json.loads(journal_path.read_text("utf-8"))
entries = [entry for entry in journal["entries"].values() if entry["action_id"] == ACTION]
if len(entries) != 1:
    raise RuntimeError("EXACT_EXEC_JOURNAL_AMBIGUOUS")
entry = entries[0]
if entry.get("attempt_id") != ATTEMPT or entry.get("state") != "unknown":
    raise RuntimeError("EXACT_EXEC_JOURNAL_CHANGED")
if entry["receipt"].get("receipt_submitted") is not True:
    raise RuntimeError("ORIGINAL_UNKNOWN_RECEIPT_NOT_SUBMITTED")
if entry["receipt"]["payload"].get("diagnostic_code") != "CONTROL_PLANE_EXEC_TIMEOUT":
    raise RuntimeError("ORIGINAL_UNKNOWN_DIAGNOSTIC_CHANGED")
request = entry["request"]
idempotency_material = {
    key: request[key] for key in (
        "action_id", "attempt_id", "writer_lease_generation", "operation", "argv",
        "timeout_ms", "max_output_bytes", "facade_contract", "yield_time_ms", "wait_ms",
    )
}
idempotency_material["task_id"] = request["task_id"].strip()
for key in ("command_id", "job_id", "local_handle", "consumer_id", "signal", "run_id", "wave_id", "cwd"):
    idempotency_material[key] = request[key] or ""
derived_key = "cpex_" + hashlib.sha256(json.dumps(
    idempotency_material, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
).encode("utf-8")).hexdigest()[:56]
if derived_key != KEY:
    raise RuntimeError("EXACT_REQUEST_IDEMPOTENCY_CORRELATION_FAILED")
connection = sqlite3.connect(
    (ROOT / ".coding-tools/orchestration/ledger.sqlite3").as_uri() + "?mode=ro",
    uri=True, timeout=2,
)
connection.row_factory = sqlite3.Row
connection.execute("PRAGMA query_only=ON")
idem = connection.execute("SELECT * FROM idempotency_records WHERE idempotency_key=?", (KEY,)).fetchone()
job = connection.execute("SELECT * FROM managed_process_jobs WHERE job_id=?", (JOB,)).fetchone()
if idem is None or job is None:
    raise RuntimeError("EXACT_LOCAL_TERMINAL_EVIDENCE_MISSING")
if (idem["operation"], idem["status"], idem["error_code"]) != ("exec_command", "unknown", "SANDBOX_STATE_PHASE_FAILED"):
    raise RuntimeError("EXACT_LOCAL_IDEMPOTENCY_CHANGED")
if (job["command_id"], job["owner"], job["lifecycle_state"], job["root_pid"], job["root_process_token"]) != (COMMAND, "control-plane-exec-bridge", "spawn_failed", 0, ""):
    raise RuntimeError("EXACT_LOCAL_JOB_NOT_TERMINAL_SPAWN_FAILED")
if not job["finished_at"] or not idem["finished_at"]:
    raise RuntimeError("EXACT_LOCAL_JOB_NOT_FINISHED")
active_jobs = connection.execute("SELECT COUNT(*) FROM managed_process_jobs WHERE lifecycle_state IN ('starting','active','waiting','idle','running','terminating')").fetchone()[0]
if active_jobs:
    raise RuntimeError("LOCAL_ACTIVE_JOB_REMAINS")
connection.close()
process_check = subprocess.run(
    ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command",
     "$rows=@(Get-CimInstance Win32_Process -Filter 'name=\"wxc-exec.exe\" or name=\"wxc-windows-sandbox-daemon.exe\" or name=\"wxc-windows-sandbox-guest.exe\" or name=\"WindowsSandbox.exe\" or name=\"WindowsSandboxClient.exe\" or name=\"WindowsSandboxServer.exe\"'); $rows.Count"],
    capture_output=True, timeout=15, check=True,
    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
)
if process_check.stdout.decode("utf-8-sig").strip() != "0":
    raise RuntimeError("SANDBOX_HOST_PROCESS_REMAINS")
node_agent_path = CANDIDATE / "resources/resources/control-plane/node_agent.py"
if hashlib.sha256(node_agent_path.read_bytes()).hexdigest() != "3f044fd7883412c54d58fb54755d54dd133810ec0687c32efc6a41f96c23e8c2":
    raise RuntimeError("PACKAGED_NODE_AGENT_CHANGED")
spec = importlib.util.spec_from_file_location("exact_r4_node_agent", node_agent_path)
node_agent = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(node_agent)
payload = {
    "schema_version": 1,
    "operation_kind": "control_plane_exec",
    "code": "CONTROL_PLANE_EXEC_SANDBOX_START_FAILED_BEFORE_PROCESS",
    "diagnostic_code": "SANDBOX_STATE_PHASE_FAILED",
    "action_id": ACTION,
    "attempt_id": ATTEMPT,
    "task_id": entry["request"]["task_id"],
    "writer_lease_generation": entry["request"]["writer_lease_generation"],
    "command_id": COMMAND,
    "job_id": JOB,
    "native_idempotency_key": KEY,
    "native_job_lifecycle": "spawn_failed",
    "native_job_root_pid": 0,
    "native_job_finished_at": job["finished_at"],
    "native_idempotency_finished_at": idem["finished_at"],
    "execution_started": False,
    "output_verified": False,
    "reconciliation_evidence": "exact_request_digest_and_terminal_native_job_no_live_sandbox_processes",
}
reconciliation = {
    "action_id": ACTION, "attempt_id": ATTEMPT,
    "receipt": node_agent._journal_receipt(ACTION, ATTEMPT, "failed", "", payload),
}
response = None
if args.submit:
    config = node_agent._config(PROFILE / "control-plane-node.json")
    response = node_agent._submit_receipt(config, reconciliation)
    if response.get("action_id") != ACTION or response.get("attempt_id") != ATTEMPT or response.get("receipt_state") != "failed" or response.get("delivery_state") != "settled":
        raise RuntimeError("TERMINAL_RECONCILIATION_ACK_UNPROVEN")
if hashlib.sha256(journal_path.read_bytes()).hexdigest() != journal_digest:
    raise RuntimeError("ORIGINAL_UNKNOWN_JOURNAL_CHANGED_CONCURRENTLY")
report = {
    "observed_at": datetime.now(timezone.utc).isoformat(),
    "phase": "terminal_exec_reconciliation_submitted" if args.submit else "terminal_exec_reconciliation_prepared",
    "action_id": ACTION, "attempt_id": ATTEMPT,
    "receipt_state": "failed", "code": payload["code"],
    "job_id": JOB, "command_id": COMMAND,
    "exact_request_idempotency_correlation": derived_key == KEY,
    "native_job_lifecycle": "spawn_failed", "native_job_root_pid": 0,
    "native_idempotency_error_code": idem["error_code"],
    "native_job_finished_at": job["finished_at"],
    "active_managed_jobs": 0, "sandbox_host_processes": 0,
    "original_journal_sha256": journal_digest, "original_journal_preserved": True,
    "submitted": args.submit, "command_replayed": False,
    "exit_code_reported": False, "output_verified": False,
    "server_ack": {key: response.get(key) for key in ("receipt_id", "receipt_state", "delivery_state", "replayed")} if response else None,
}
line = json.dumps(report, separators=(",", ":"))
with Path(__file__).with_name("postreboot-runtime.jsonl").open("a", encoding="utf-8") as output:
    output.write(line + "\n")
print(line)
