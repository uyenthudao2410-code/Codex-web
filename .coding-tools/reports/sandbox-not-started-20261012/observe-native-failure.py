"""Read the original failed action and backend lifecycle without execution effects.

The only write is a new content-free diagnostic in this evidence directory.
Canonical SQLite, node journal, profile, sandbox state and logs are read-only.
No workflow, receipt, command, VM, credential or runtime is instantiated.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import time

ROOT = Path(r"E:\DEV\Codex-web")
REPORTS = ROOT / ".coding-tools/reports/sandbox-not-started-20261012"
PROFILE = Path(os.environ["APPDATA"]) / "web-mcp-assistant"
FAILED_JOB = "41d336e59e8340078b97d35760b4a649"
SUCCESS_JOB = "65c2908a7371487cbfbb22ee1d60c262"
FAILED_ACTION = "act_f1b0df9d4be84f31b931696ff8d8f295"
SANDBOX = "wsb:90b652fe"


def sha(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def output_summary(value):
    return {"bytes": len(value.encode()), "sha256": sha(value.encode()),
            "contains_not_started": "not started" in value,
            "sandbox_ids": re.findall(r"wsb:[a-f0-9]+", value)}


def native_facts():
    ledger = ROOT / ".coding-tools/orchestration/ledger.sqlite3"
    c = sqlite3.connect(ledger.resolve().as_uri() + "?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA query_only=ON")
    c.execute("BEGIN")
    jobs = []
    for identity in (SUCCESS_JOB, FAILED_JOB):
        d = dict(c.execute("SELECT * FROM managed_process_jobs WHERE job_id=?", (identity,)).fetchone())
        metadata = json.loads(d.pop("metadata_json"))
        d["metadata_sha256"] = sha(canonical(metadata))
        d["exit_code"] = metadata.get("exit_code")
        jobs.append(d)
    idem = [dict(r) for r in c.execute(
        "SELECT idempotency_key,operation,status,process_instance_id,run_id,wave_id,started_at,finished_at,error_code "
        "FROM idempotency_records WHERE started_at>=? ORDER BY started_at",
        ("2026-10-12T05:10:00",))]
    events = []
    for row in c.execute("SELECT * FROM events WHERE event_time>=? ORDER BY seq", ("2026-10-12T05:10:00",)):
        if any(identity in row["payload_json"] for identity in (FAILED_JOB, jobs[1]["command_id"], SANDBOX)):
            d = {k: row[k] for k in ("seq", "event_id", "run_id", "wave_id", "event_type", "event_time", "event_hash")}
            d["payload_sha256"] = sha(row["payload_json"].encode())
            events.append(d)
    active = c.execute("SELECT COUNT(*) FROM managed_process_jobs WHERE process_instance_id=? "
                       "AND lifecycle_state IN ('starting','running','stopping')", (jobs[1]["process_instance_id"],)).fetchone()[0]
    c.close()
    return {"jobs": jobs, "idempotency_since_utc0510": idem,
            "exact_identity_events_since_utc0510": events,
            "native_active_managed_job_count": active,
            "read_contract": {"mode": "ro", "query_only": True, "transaction": True,
                              "canonical_writer_instantiated": False}}


def journal_facts():
    p = PROFILE / "control-plane-node.json.exec-journal.json"
    result = []
    for key, entry in read_json(p).get("entries", {}).items():
        payload = entry.get("receipt", {}).get("payload", {})
        if payload.get("job_id") not in (FAILED_JOB, SUCCESS_JOB):
            continue
        result.append({"entry_key": key, "entry_sha256": sha(canonical(entry)),
                       "state": entry.get("state"), "action_id": entry.get("action_id"),
                       "attempt_id": entry.get("attempt_id"),
                       "receipt_state": entry["receipt"].get("receipt_state"),
                       "receipt_submitted": entry["receipt"].get("receipt_submitted"),
                       "safe_payload": {k: payload[k] for k in ("job_id", "command_id", "status", "exit_code",
                           "runtime_identity", "output_bytes", "timed_out", "truncated", "run_id", "wave_id") if k in payload},
                       "outputs": {k: output_summary(payload.get(k, "")) for k in ("stdout", "stderr")}})
    return {"path": str(p), "sha256": sha(p.read_bytes()), "entries": result, "modified_by_observer": False}


def backend_facts():
    base = Path(os.environ["TEMP"]) / "wxc-wsb/state-aware"
    token_dir = base / "90b652fe"
    record = token_dir / "record.json"
    log = token_dir / "daemon.log"
    d = read_json(record)
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    flags = {
        "prior_guest_ready": "received Ready from guest agent",
        "prior_daemon_ready": "ready; holding wsb:90b652fe",
        "unexpected_vm_exit": "Windows Sandbox VM exited unexpectedly (host processes gone)",
        "host_processes_confirmed_gone": "all sandbox host processes confirmed gone",
        "teardown_confirmed_record_cleared": "teardown confirmed VM gone; clearing record",
        "daemon_exited": "[wsb-daemon] exiting",
    }
    classified = {name: [{"line": i + 1, "sha256": sha(line.encode())}
                         for i, line in enumerate(lines) if text in line] for name, text in flags.items()}
    return {"sandbox_id": SANDBOX, "global_daemon_record_exists": (base / "daemon.json").exists(),
            "token_record": {"path": str(record), "sha256": sha(record.read_bytes()),
                             "state": d.get("state"), "sandbox_id": d.get("sandbox_id"),
                             "modified_at_unix_ms": int(record.stat().st_mtime * 1000)},
            "daemon_log": {"path": str(log), "sha256": sha(log.read_bytes()),
                           "bytes": log.stat().st_size, "line_count": len(lines),
                           "modified_at_unix_ms": int(log.stat().st_mtime * 1000), "classified_lines": classified}}


def central_facts():
    # Raw rows and output stay private; only identities, hashes and counts return.
    script = r'''
import hashlib,json,sqlite3,subprocess,time
from pathlib import Path
pid=int(subprocess.check_output(['systemctl','--user','show','codex-control-plane.service','--property=MainPID','--value'],text=True))
environment=dict(i.split('=',1) for i in Path(f'/proc/{pid}/environ').read_text().split('\0') if '=' in i)
c=sqlite3.connect(Path(environment['CONTROL_PLANE_DB']).resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON');c.execute('BEGIN')
a='act_f1b0df9d4be84f31b931696ff8d8f295'
action=dict(c.execute('SELECT action_id,device_id,workspace_id,workspace_generation,binding_id,delivery_state,created_at_ms,settled_at_ms FROM actions WHERE action_id=?',(a,)).fetchone())
intent=dict(c.execute('SELECT task_id,idempotency_key,argv_json,created_at_ms,writer_lease_generation FROM mcp_exec_intents WHERE action_id=?',(a,)).fetchone());argv_envelope=json.loads(intent.pop('argv_json'));argv=argv_envelope['argv']
intent['argv_sha256']=hashlib.sha256(json.dumps(argv_envelope,separators=(',',':')).encode()).hexdigest()
intent['argv_storage_schema']='object_with_argv_list'
intent['executable_basename']=str(argv[0]).replace('\\','/').split('/')[-1] if isinstance(argv,list) and argv else None
intent['argv_tail_is_version']=isinstance(argv,list) and argv[1:]==['--version']
receipts=[]
for row in c.execute('SELECT receipt_id,receipt_state,payload_json,local_handle,received_at_ms FROM receipts WHERE action_id=?',(a,)):
 d=dict(row);p=json.loads(d.pop('payload_json'));d['payload_sha256']=hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest();d['safe_payload']={k:p[k] for k in ('job_id','command_id','exit_code','status','runtime_identity','run_id','wave_id') if k in p};receipts.append(d)
g=action['workspace_generation'];task=dict(c.execute('SELECT task_id,closed_at_ms,expires_at_ms FROM mcp_task_sessions WHERE task_id=?',(intent['task_id'],)).fetchone());writer=dict(c.execute('SELECT task_id,lease_generation,released_at_ms FROM mcp_task_writer_leases WHERE task_id=?',(intent['task_id'],)).fetchone())
census={'open_tasks':c.execute('SELECT COUNT(*) FROM mcp_task_sessions WHERE workspace_generation=? AND closed_at_ms IS NULL',(g,)).fetchone()[0],'unreleased_writers':c.execute('SELECT COUNT(*) FROM mcp_task_writer_leases l JOIN mcp_task_sessions t ON t.task_id=l.task_id WHERE t.workspace_generation=? AND l.released_at_ms IS NULL',(g,)).fetchone()[0],'unsettled_actions':c.execute('SELECT COUNT(*) FROM actions WHERE workspace_generation=? AND settled_at_ms IS NULL',(g,)).fetchone()[0]}
node=dict(c.execute('SELECT device_id,readiness,runtime_instance_id,mcp_server_instance_id,activation_epoch,last_seen_at_ms FROM nodes WHERE device_id=?',(action['device_id'],)).fetchone())
print(json.dumps({'observed_at_ms':int(time.time()*1000),'service_pid':pid,'action':action,'intent':intent,'attempts':[dict(r) for r in c.execute('SELECT attempt_id,attempt_number,dispatched_at_ms FROM delivery_attempts WHERE action_id=?',(a,))],'receipts':receipts,'task':task,'writer':writer,'current_generation_census':census,'node':node},separators=(',',':')))
'''
    result = subprocess.run(["ssh.exe", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "-o",
                             "StrictHostKeyChecking=yes", "svhome@100.116.112.22", "python3", "-B", "-"],
                            input=script, text=True, encoding="utf-8", capture_output=True, timeout=25,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if result.returncode != 0 or len(result.stdout) > 196608:
        raise RuntimeError("READONLY_CENTRAL_OBSERVATION_FAILED")
    return json.loads(result.stdout)


def main():
    native, journal, backend, central = native_facts(), journal_facts(), backend_facts(), central_facts()
    runtime = read_json(PROFILE / "runtime-state.json")
    epoch = read_json(PROFILE / "activation-epoch.json")["current"]
    good, failed = native["jobs"]
    package = ROOT / "dist/windows-candidate-mxc-wsb-cbe1774-machine-write-exec-1012-r5b/win-unpacked/resources/resources/coding-tools-mcp/coding_tools_mcp/windows_mxc_state_aware.py"
    source = package.read_text(encoding="utf-8")
    report = {"schema_version": 1, "operation": "original_sandbox_not_started_readonly_diagnostic",
        "observed_at_ms": int(time.time() * 1000), "producer_sha256": sha(Path(__file__).read_bytes()),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "supersedes_intent_shape_parsing_in": "original-failure-diagnostic-1791783479887.json",
        "evidence_window_start_utc": "2026-10-12T05:10:00Z", "sample_size_failed_jobs": 1,
        "canonical_ledger_mutated": False, "node_journal_modified": False,
        "failed_action_replayed": False, "new_execution_or_vm_started": False,
        "native": native, "node_journal": journal, "backend": backend, "central": central,
        "current_runtime": {k: runtime.get(k) for k in ("nativePid", "nativeProcessStartToken", "nativeInstanceId", "nativeActivationEpochId", "startedAt", "manualStop")},
        "current_epoch": {k: epoch.get(k) for k in ("activation_epoch_id", "state", "admission_state", "ready_at", "updated_at")},
        "packaged_adapter": {"path": str(package), "sha256": sha(package.read_bytes()),
            "cached_same_workspace_return_before_host_count": source.index("return self._active.sandbox_id") < source.index("if self._host_process_count():")},
        "classification": {"reason": "cached_backend_identity_after_confirmed_vm_exit",
            "inference_from_measured_lifecycle_and_source_order": True,
            "native_process_and_runtime_match_prior_success": good["process_instance_id"] == failed["process_instance_id"] and good["runtime_instance_id"] == failed["runtime_instance_id"],
            "native_epoch_stale_supported": False, "initial_spawn_race_supported": False,
            "failed_phase": "state_aware_exec_before_guest_argv_dispatch",
            "vm_disappearance_trigger": "not_established_by_available_evidence",
            "current_quiescence_requires_live_os_corroboration": True}}
    p = REPORTS / ("original-failure-diagnostic-" + str(report["observed_at_ms"]) + ".json")
    with p.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(json.dumps({"operation": report["operation"], "ok": True, "report_path": str(p),
                      "report_sha256": sha(p.read_bytes()), "classification": report["classification"],
                      "current_generation_census": central["current_generation_census"]}, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"operation": "original_sandbox_not_started_readonly_diagnostic", "ok": False,
                          "code": str(error) if isinstance(error, RuntimeError) else type(error).__name__}))
        raise SystemExit(1)
