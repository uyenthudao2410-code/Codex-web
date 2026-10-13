"""Observe r7 idle boundary after r6 VM disappeared; no lifecycle effects."""
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import time
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "owned-sandbox-stop-proof.py"
spec = importlib.util.spec_from_file_location("r7_idle_readonly_helpers", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.require(m.file_sha(SOURCE) == "5eb4615b8ef5aefbba2cec3835f087f2f537584f554c33dbe7802c10c8533fde", "EXACT_READONLY_HELPER_CHANGED")
manifest_path = HERE / "r7-candidate-verification.json"
manifest_sha = "1f349c684ef9f6581260ba0e1ee1b5011c39527e873a8e9b4957edecabea1855"
third_path = HERE / "r6-three-stage-4a0d3d7861ef45ad85b3574a749c0620-after_stop.ndjson"
third_sha = "88bdbe7a01ab92bdc205c82c25cb8f8942be750722cdd937e494b06ef96afa41"
m.require(m.file_sha(third_path) == third_sha, "ORIGINAL_THIRD_PROOF_CHANGED")
rows = [json.loads(line) for line in third_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
finals = [row for row in rows if row.get("phase") == "three_stage_complete" and row.get("ok") is True]
m.require(len(finals) == 1, "ONE_ORIGINAL_THREE_STAGE_SUCCESS_REQUIRED")
third = finals[0]
m.require(third["current_generation_census"] == {"open_tasks": 0, "unreleased_writers": 0, "unsettled_actions": 0}
          and set(third["proofs"]) == {"cold", "warm", "after_stop"}
          and third["proofs"]["after_stop"]["job_id"] == "5f93717118a540b0bf373c2763dfe606"
          and all(proof["exit_code"] == 0 and proof["attempt_number"] == 1 for proof in third["proofs"].values()),
          "ORIGINAL_THIRD_SUCCESS_OR_CLOSED_TASK_CHANGED")
args = SimpleNamespace(candidate=Path(m.read_json(manifest_path)["candidate"]), package_proof=manifest_path,
    package_proof_sha256=manifest_sha, native_pid=48080, native_process_start_token="134362609538543190",
    activation_epoch="activation-mv4vxaab-907c8a927b8eb80e4e7b8b56bdb150ed",
    process_instance_id="Gzm9K8GFf82uAtwO", server_instance_id="87JB3saNgxMlTI0m")
package = m.package_facts(args)
runtime = m.runtime_facts(args, package)

def native_jobs():
    c = sqlite3.connect((m.ROOT / ".coding-tools/orchestration/ledger.sqlite3").resolve().as_uri() + "?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA query_only=ON"); c.execute("BEGIN")
    count = c.execute("SELECT COUNT(*) FROM managed_process_jobs WHERE lifecycle_state IN ('starting','running','terminating','orphaned')").fetchone()[0]
    proofs = []
    for lane, proof in third["proofs"].items():
        row = c.execute("SELECT job_id,command_id,lifecycle_state,finished_at,process_instance_id,runtime_instance_id,metadata_json FROM managed_process_jobs WHERE job_id=?", (proof["job_id"],)).fetchone()
        m.require(row and row["lifecycle_state"] == "exited" and row["finished_at"]
                  and row["command_id"] == proof["command_id"]
                  and row["process_instance_id"] == proof["runtime_identity"]["process_instance_id"]
                  and row["runtime_instance_id"] == proof["runtime_identity"]["server_instance_id"]
                  and json.loads(row["metadata_json"]).get("exit_code") == 0, "ORIGINAL_NATIVE_JOB_NOT_TERMINAL_EXIT_ZERO")
        proofs.append({"lane": lane, "job_id": row["job_id"], "command_id": row["command_id"], "lifecycle_state": row["lifecycle_state"], "finished_at": row["finished_at"], "exit_code": 0})
    c.close()
    m.require(count == 0, "ACTIVE_NATIVE_JOB_PRESENT")
    return {"active_native_jobs": count, "original_r6_jobs": proofs}

native = native_jobs()
script = r'''
import json,sqlite3,subprocess,time
from pathlib import Path
pid=int(subprocess.check_output(['systemctl','--user','show','codex-control-plane.service','--property=MainPID','--value'],text=True))
e=dict(item.split('=',1) for item in Path(f'/proc/{pid}/environ').read_text().split('\0') if '=' in item)
c=sqlite3.connect(Path(e['CONTROL_PLANE_DB']).resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON');c.execute('BEGIN')
task=__TASK__;generation=__GENERATION__;device=__DEVICE__;proofs=__PROOFS__
def one(sql,p):
 r=c.execute(sql,p).fetchone();return dict(r) if r else None
lineage=[]
for lane,p in proofs.items():
 a=one('SELECT action_id,delivery_state,settled_at_ms,workspace_generation FROM actions WHERE action_id=?',(p['action_id'],))
 attempts=[dict(r) for r in c.execute('SELECT attempt_id,attempt_number FROM delivery_attempts WHERE action_id=?',(p['action_id'],))]
 receipts=[]
 for row in c.execute('SELECT receipt_id,receipt_state,payload_json FROM receipts WHERE action_id=?',(p['action_id'],)):
  d=dict(row);v=json.loads(d.pop('payload_json'));d['payload']={k:v[k] for k in ('job_id','command_id','exit_code','runtime_identity','task_id','writer_lease_generation')};receipts.append(d)
 lineage.append({'lane':lane,'action':a,'attempts':attempts,'receipts':receipts})
print(json.dumps({'service_pid':pid,'node':one('SELECT device_id,readiness,runtime_instance_id,mcp_server_instance_id,activation_epoch,last_seen_at_ms FROM nodes WHERE device_id=?',(device,)),'task':one('SELECT task_id,closed_at_ms,workspace_generation FROM mcp_task_sessions WHERE task_id=?',(task,)),'original_task_unreleased_writers':c.execute('SELECT COUNT(*) FROM mcp_task_writer_leases WHERE task_id=? AND released_at_ms IS NULL',(task,)).fetchone()[0],'census':{'open_tasks':c.execute('SELECT COUNT(*) FROM mcp_task_sessions WHERE workspace_generation=? AND closed_at_ms IS NULL',(generation,)).fetchone()[0],'unreleased_writers':c.execute('SELECT COUNT(*) FROM mcp_task_writer_leases l JOIN mcp_task_sessions t ON t.task_id=l.task_id WHERE t.workspace_generation=? AND l.released_at_ms IS NULL',(generation,)).fetchone()[0],'unsettled_actions':c.execute('SELECT COUNT(*) FROM actions WHERE workspace_generation=? AND settled_at_ms IS NULL',(generation,)).fetchone()[0]},'original_lineage':lineage},separators=(',',':')))
'''
for key, value in {"TASK": third["task_id"], "GENERATION": m.GENERATION, "DEVICE": m.DEVICE, "PROOFS": third["proofs"]}.items():
    script = script.replace("__" + key + "__", repr(value))
result = subprocess.run(["ssh.exe", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=yes", "svhome@100.116.112.22", "python3", "-B", "-"], input=script, text=True, encoding="utf-8", capture_output=True, timeout=20, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
m.require(result.returncode == 0 and len(result.stdout) <= 196608, "READONLY_CENTRAL_OBSERVATION_FAILED")
central = json.loads(result.stdout)
node = central["node"]
m.require(node and node["readiness"] == "ready" and node["runtime_instance_id"] == args.process_instance_id
          and node["mcp_server_instance_id"] == args.server_instance_id and node["activation_epoch"] == args.activation_epoch
          and 0 <= int(time.time() * 1000) - node["last_seen_at_ms"] <= 30000
          and central["task"]["task_id"] == third["task_id"] and central["task"]["closed_at_ms"]
          and central["task"]["workspace_generation"] == m.GENERATION and central["original_task_unreleased_writers"] == 0
          and central["census"] == {"open_tasks": 0, "unreleased_writers": 0, "unsettled_actions": 0}, "R7_NODE_OR_CENTRAL_IDLE_BOUNDARY_CHANGED")
for item in central["original_lineage"]:
    proof = third["proofs"][item["lane"]]
    m.require(item["action"]["delivery_state"] == "settled" and item["action"]["settled_at_ms"]
              and item["action"]["workspace_generation"] == m.GENERATION
              and item["attempts"] == [{"attempt_id": proof["attempt_id"], "attempt_number": 1}]
              and len(item["receipts"]) == 1, "ORIGINAL_CENTRAL_ACTION_OR_ATTEMPT_CHANGED")
    receipt = item["receipts"][0]
    m.require(receipt["receipt_id"] == proof["receipt_id"] and receipt["receipt_state"] == "completed"
              and receipt["payload"] == {"job_id": proof["job_id"], "command_id": proof["command_id"],
                  "exit_code": 0, "runtime_identity": proof["runtime_identity"], "task_id": third["task_id"],
                  "writer_lease_generation": proof["writer_lease_generation"]}, "ORIGINAL_CENTRAL_RECEIPT_CHANGED")
base = Path(os.environ["TEMP"]).resolve() / "wxc-wsb/state-aware"
record_path = base / "e68057a4/record.json"
record = m.read_json(record_path)
script = "@(Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'WindowsSandbox*' -or $_.Name -in @('vmmemWindowsSandbox','vmmemWindowsSandbox.exe','wxc-windows-sandbox-daemon.exe') } | Select-Object Name,ProcessId) | ConvertTo-Json -Compress"
inventory = subprocess.run(["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=8, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
m.require(inventory.returncode == 0 and len(inventory.stdout) <= 8192, "HOST_INVENTORY_FAILED")
hosts = json.loads(inventory.stdout) if inventory.stdout.strip() else []
m.require(hosts == [] and not (base / "daemon.json").exists() and record["sandbox_id"] == "wsb:e68057a4"
          and record["state"] == "started" and m.read_json(record_path) == record
          and m.runtime_facts(args, package) == runtime and native_jobs() == native
          and m.file_sha(third_path) == third_sha, "R7_FINAL_IDLE_BOUNDARY_OR_ORIGINAL_EVIDENCE_CHANGED")
report = {"schema_version": 1, "operation": "r7_empty_host_boundary_readonly_observation", "ok": True,
          "observed_at_ms": int(time.time() * 1000), "producer_sha256": m.file_sha(Path(__file__)),
          "package": package, "runtime": runtime, "native": native, "central": central,
          "host_process_count": 0, "host_inventory": [], "daemon_record_absent": True,
          "old_record": {"sandbox_id": "wsb:e68057a4", "state_observed": "started", "sha256": m.file_sha(record_path),
                         "mapped_folders_sha256": m.digest(record["mapped_folders"]), "manual_edit_performed": False,
                         "classification": "historical started record with no live daemon or Sandbox host"},
          "original_r6_third_receipt_sha256": third_sha, "original_stop_unknown_preserved": True,
          "lifecycle_mutation_performed": False, "deprovision_dispatched": False, "stop_replayed": False,
          "processes_terminated": False, "database_mutated": False, "node_journal_modified": False, "nonce_saved": False,
          "next_action": "Root may run the one fresh r7 cold shared write/read/patch/read/exec canary"}
saved = m.write_new(HERE / ("r7-pre-canary-empty-host-boundary-" + str(report["observed_at_ms"]) + ".json"), report)
print(json.dumps({"ok": True, **saved, "census": central["census"], "host_process_count": 0, "lifecycle_mutation_performed": False}))
