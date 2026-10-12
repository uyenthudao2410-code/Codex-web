"""Read-only host snapshots and exact NEW timeout action/native Job correlation.

Default captures one host snapshot. --action-id correlates the submitted node
receipt and native idempotency response to its exact durable Job, then captures
two fresh host snapshots. No cancellation, VM operation, ledger write or secret
output is permitted. Observation cannot authorize a runtime transition.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import tempfile
import time
import zlib

ROOT = Path(r"E:\Github\Tools-Codex-web")
PROFILE = Path(r"C:\Users\daoth\AppData\Roaming\web-mcp-assistant")
EPOCH = "activation-mv3qe36p-991f11f44f47d32ea2e217b1db882ff7"
PROCESS = "MQcujHCH34p39X2a"
SERVER = "QKd2cJO3fSYWo_tA"
DEVICE = "72ceec2d-e3f2-472f-8e3c-99fffe053035"
WORKSPACE = "workspace_dda1d78e9a21402aa6213f72af64f788"
GENERATION = "generation_c2f13e8d02344cf6a38a3f42ecfa59b6"
ARGV = ["node", "--test", "tests/control-plane-approved-patch-runtime.test.js"]
EXCLUDED = {"act_4193cf69c84542e7b13a91e492916ccd", "act_fc024ff0b54c4a8ba4c7c7b0228a7e76"}
CENSUS_SHA256 = "0ca287de959f503ddb675c47015ef2788363bd18c15cde3211a9af305ff95742"
HOST_SCRIPT = r"""$ErrorActionPreference='Stop'; $items=@(Get-Process | Where-Object {
  $_.ProcessName -match '^WindowsSandbox' -or $_.ProcessName -eq 'vmmemWindowsSandbox'
}); @{sandbox_process_count=$items.Count; sandbox_processes=@($items | ForEach-Object {
  @{name=$_.ProcessName; pid=$_.Id}
})} | ConvertTo-Json -Compress -Depth 4"""


class Refusal(Exception):
    pass


def require(condition, code):
    if not condition:
        raise Refusal(code)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def identity(value):
    require(isinstance(value, dict) and value.get("activation_epoch_id") == EPOCH
            and value.get("process_instance_id") == PROCESS and value.get("server_instance_id") == SERVER,
            "EXACT_R9_NATIVE_IDENTITY_REQUIRED")


def native_key(request):
    material = {key: request[key] for key in ("action_id", "attempt_id", "writer_lease_generation", "operation", "argv",
                "timeout_ms", "max_output_bytes", "facade_contract", "yield_time_ms", "wait_ms")}
    material["task_id"] = request["task_id"].strip()
    for key in ("command_id", "job_id", "local_handle", "consumer_id", "signal", "run_id", "wave_id", "cwd"):
        material[key] = request[key] or ""
    return "cpex_" + digest(material)[:56]


def decode_summary(record):
    if record["summary_codec"] == "zlib_json":
        value = json.loads(zlib.decompress(record["summary_blob"]))
    else:
        require(record["summary_codec"] == "plain_json", "UNKNOWN_SUMMARY_CODEC")
        value = json.loads(record["summary_json"])
    require(isinstance(value, dict), "NATIVE_SUMMARY_INVALID")
    return value


def read_census(after_canary=False):
    helper = Path(__file__).with_name("observe-r9-current.cjs")
    require(hashlib.sha256(helper.read_bytes()).hexdigest() == CENSUS_SHA256, "REVIEWED_READ_CENSUS_CHANGED")
    node = Path(r"C:\Program Files\nodejs\node.exe")
    require(node.is_file(), "REVIEWED_NODE_UNAVAILABLE")
    arguments = [str(node), str(helper)] + (["--after-canary"] if after_canary else [])
    observed = subprocess.run(arguments, cwd=ROOT, capture_output=True, text=True, timeout=60, check=False)
    require(observed.returncode == 0, "REVIEWED_READ_CENSUS_REFUSED")
    rows = [json.loads(line) for line in observed.stdout.splitlines() if line.strip()]
    require(len(rows) == 1 and rows[0]["ok"] is True and not rows[0]["blockers"]
            and rows[0]["pending_acceptance_records_unchanged"] is True,
            "CANONICAL_CENSUS_UNPROVEN")
    return {"evidence_file": rows[0]["evidence_file"], "evidence_sha256": rows[0]["evidence_sha256"],
            "observed_at": rows[0]["observed_at"], "mutations": rows[0]["mutations"]}


def host_snapshot():
    require(os.name == "nt" and Path.cwd().resolve() == ROOT.resolve(), "EXACT_WINDOWS_WORKSPACE_REQUIRED")
    shell = Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
    require(shell.is_file(), "TRUSTED_POWERSHELL_UNAVAILABLE")
    result = subprocess.run([str(shell), "-NoProfile", "-NonInteractive", "-Command", HOST_SCRIPT],
                            capture_output=True, text=True, timeout=15, check=False)
    require(result.returncode == 0, "HOST_OBSERVATION_FAILED")
    observed = json.loads(result.stdout)
    require(isinstance(observed.get("sandbox_process_count"), int), "HOST_OBSERVATION_INVALID")
    daemon = Path(tempfile.gettempdir()) / "wxc-wsb" / "state-aware" / "daemon.json"
    # Never open the daemon record: it contains a private IPC nonce.
    record_exists = os.path.lexists(daemon)
    observed.update(observed_at_ns=time.time_ns(), daemon_record_exists=record_exists,
                    daemon_record_read=False, ledger_mutated=False, command_replayed=False)
    observed["sandbox_absence_observed"] = observed["sandbox_process_count"] == 0 and not record_exists
    observed["observation_sha256"] = digest(observed)
    return observed


def correlate(action_id, task_id):
    require(re.fullmatch(r"act_[a-f0-9]{32}", action_id or "") and action_id not in EXCLUDED,
            "EXACT_NEW_ACTION_REQUIRED")
    require(re.fullmatch(r"task_[a-f0-9]{32}", task_id or ""), "EXACT_TASK_REQUIRED")
    journal = json.loads((PROFILE / "control-plane-node.json.exec-journal.json").read_text(encoding="utf-8"))
    entries = [entry for entry in journal["entries"].values() if entry.get("action_id") == action_id]
    require(len(entries) == 1, "EXACT_ONE_ATTEMPT_REQUIRED")
    entry = entries[0]
    request = entry["request"]
    require(request["action_id"] == action_id and request["attempt_id"] == entry["attempt_id"]
            and request["task_id"] == task_id and request["operation"] == "exec_run"
            and request["argv"] == ARGV and request["timeout_ms"] == 5000
            and request["max_output_bytes"] == 32768 and request["cwd"] == ""
            and request["device_id"] == DEVICE and request["workspace_id"] == WORKSPACE
            and request["workspace_generation"] == GENERATION, "EXACT_CANARY_REQUEST_REQUIRED")
    receipt = entry["receipt"]
    payload = receipt["payload"]
    require(receipt["receipt_submitted"] is True and receipt["receipt_state"] in {"failed", "completed"}
            and payload["action_id"] == action_id and payload["task_id"] == task_id
            and payload["status"] == "timeout" and payload["timed_out"] is True, "SUBMITTED_TIMEOUT_RECEIPT_REQUIRED")
    identity(payload["runtime_identity"])
    command, job_id = payload["command_id"], payload["job_id"]
    require(all(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value)
                for value in (command, job_id)), "EXACT_NATIVE_JOB_IDENTIFIERS_REQUIRED")
    ledger = ROOT / ".coding-tools/orchestration/ledger.sqlite3"
    require(ledger.is_file() and not ledger.is_symlink(), "CANONICAL_LEDGER_REQUIRED")
    with sqlite3.connect(ledger.as_uri() + "?mode=ro", uri=True, timeout=5) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        record = db.execute("SELECT * FROM idempotency_records WHERE idempotency_key=?", (native_key(request),)).fetchone()
        require(record is not None and record["finished_at"] is not None
                and record["process_instance_id"] == PROCESS, "EXACT_NATIVE_IDEMPOTENCY_REQUIRED")
        summary = decode_summary(record)
        structured = summary["tool_result"]["structuredContent"]
        require(structured["command_id"] == command and structured["execution_owner"]["job_id"] == job_id
                and structured["timed_out"] is True and structured["status"] == "timeout", "NATIVE_TIMEOUT_RESULT_REQUIRED")
        jobs = db.execute("SELECT job_id,command_id,run_id,wave_id,root_pid,owner,lifecycle_state,started_at,finished_at,"
                          "process_instance_id,runtime_instance_id FROM managed_process_jobs WHERE job_id=? AND command_id=?",
                          (job_id, command)).fetchall()
        require(len(jobs) == 1, "EXACT_DURABLE_JOB_REQUIRED")
        job = dict(jobs[0])
        require(job["root_pid"] > 0 and job["finished_at"] is not None
                and job["lifecycle_state"] in {"timeout", "timed_out"}
                and job["owner"] == "control-plane-exec-bridge" and job["process_instance_id"] == PROCESS
                and job["runtime_instance_id"] == SERVER and job["run_id"] == payload["run_id"]
                and job["wave_id"] == payload["wave_id"], "EXACT_TERMINAL_TIMEOUT_JOB_REQUIRED")
        active = db.execute("SELECT count(*) FROM managed_process_jobs WHERE process_instance_id=? "
                            "AND lifecycle_state IN ('starting','active','waiting','idle','running','terminating')", (PROCESS,)).fetchone()[0]
        require(active == 0, "R9_ACTIVE_JOBS_REMAIN")
    return {"action_id": action_id, "task_id": task_id, "attempt_id": entry["attempt_id"], "job": job,
            "native_idempotency_key": native_key(request), "runtime_identity": payload["runtime_identity"],
            "ledger_mutated": False, "command_replayed": False, "active_jobs": active}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action-id")
    parser.add_argument("--task-id")
    args = parser.parse_args()
    if args.action_id is None:
        require(args.task_id is None, "ACTION_AND_TASK_REQUIRED_TOGETHER")
        census = read_census()
        print(json.dumps({"phase": "r9_host_preflight", "ok": True, **host_snapshot(), "canonical_census": census}, separators=(",", ":")))
        return
    proof = correlate(args.action_id, args.task_id)
    census = read_census(after_canary=True)
    first = host_snapshot()
    time.sleep(2)
    second = host_snapshot()
    require(first["sandbox_absence_observed"] and second["sandbox_absence_observed"], "TWO_FRESH_ABSENCE_OBSERVATIONS_REQUIRED")
    print(json.dumps({"phase": "r9_timeout_native_and_host_observed", "ok": True, **proof, "canonical_census": census,
                      "host_observations": [first, second],
                      "vm_absence_observed_twice": True, "cleanup_api_confirmation_available": False,
                      "runtime_transition_authorized": False}, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Refusal as error:
        print(json.dumps({"phase": "r9_native_observation_refused", "ok": False, "code": str(error)}))
        raise SystemExit(1) from None
    except Exception:
        print(json.dumps({"phase": "r9_native_observation_refused", "ok": False, "code": "OBSERVATION_UNAVAILABLE"}))
        raise SystemExit(1) from None
