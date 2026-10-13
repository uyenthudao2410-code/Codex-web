"""Observe the original supported stop; never replay or perform lifecycle effects."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace
import time

HERE = Path(__file__).resolve().parent
ROOT = Path(r"E:\DEV\Codex-web")
SOURCE = HERE / "owned-sandbox-stop-proof.py"
REVIEWED_SOURCE_SHA = "5eb4615b8ef5aefbba2cec3835f087f2f537584f554c33dbe7802c10c8533fde"
spec = importlib.util.spec_from_file_location("original_stop_readonly_helpers", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def evidence(path, expected_sha):
    m.require(path.resolve().parent == HERE and m.file_sha(path) == expected_sha,
              "EXACT_ORIGINAL_STOP_EVIDENCE_CHANGED")
    return m.read_json(path)


def central_authority(args, original, current_generation):
    # Observe the unchanged original lineage and the explicitly renewed current
    # authority as different witnesses. Never rewrite the original generation.
    script = r'''
import json,sqlite3,subprocess
from pathlib import Path
pid=int(subprocess.check_output(['systemctl','--user','show','codex-control-plane.service','--property=MainPID','--value'],text=True))
e=dict(item.split('=',1) for item in Path(f'/proc/{pid}/environ').read_text().split('\0') if '=' in item)
c=sqlite3.connect(Path(e['CONTROL_PLANE_DB']).resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON');c.execute('BEGIN')
a=__ACTION__;t=__TASK__;g=__GENERATION__;device=__DEVICE__
def one(sql,params):
 r=c.execute(sql,params).fetchone();return dict(r) if r else None
action=one('SELECT action_id,device_id,workspace_id,workspace_generation,binding_id,delivery_state,settled_at_ms FROM actions WHERE action_id=?',(a,))
intent=one('SELECT task_id,writer_lease_generation FROM mcp_exec_intents WHERE action_id=?',(a,))
task=one('SELECT task_id,binding_id,workspace_id,workspace_generation,closed_at_ms FROM mcp_task_sessions WHERE task_id=?',(t,))
writer=one('SELECT task_id,binding_id,lease_generation,expires_at_ms,released_at_ms FROM mcp_task_writer_leases WHERE task_id=? ORDER BY lease_generation DESC LIMIT 1',(t,))
receipts=[]
for row in c.execute('SELECT receipt_id,receipt_state,payload_json FROM receipts WHERE action_id=?',(a,)):
 d=dict(row);p=json.loads(d.pop('payload_json'));d['safe_payload']={k:p[k] for k in ('job_id','command_id','exit_code','status','runtime_identity','task_id') if k in p};receipts.append(d)
result={'service_pid':pid,'action':action,'intent':intent,'task':task,'writer':writer,'task_exec_actions':[dict(r) for r in c.execute('SELECT a.action_id,a.delivery_state,a.settled_at_ms FROM actions a JOIN mcp_exec_intents i ON i.action_id=a.action_id WHERE i.task_id=? ORDER BY a.action_id',(t,))],'attempts':[dict(r) for r in c.execute('SELECT attempt_id,attempt_number FROM delivery_attempts WHERE action_id=?',(a,))],'receipts':receipts,'unsettled_generation_actions':c.execute('SELECT COUNT(*) FROM actions WHERE workspace_generation=? AND settled_at_ms IS NULL',(g,)).fetchone()[0],'other_open_generation_tasks':c.execute('SELECT COUNT(*) FROM mcp_task_sessions WHERE workspace_generation=? AND closed_at_ms IS NULL AND task_id<>?',(g,t)).fetchone()[0],'node':one('SELECT device_id,readiness,runtime_instance_id,mcp_server_instance_id,activation_epoch,last_seen_at_ms FROM nodes WHERE device_id=?',(device,))}
print(json.dumps(result,separators=(',',':')))
'''
    for key, value in {"ACTION": args.warm_action_id, "TASK": args.canary_task_id,
                       "GENERATION": m.GENERATION, "DEVICE": m.DEVICE}.items():
        script = script.replace("__" + key + "__", repr(value))
    result = subprocess.run(["ssh.exe", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "-o",
                             "StrictHostKeyChecking=yes", "svhome@100.116.112.22", "python3", "-B", "-"],
                            input=script, text=True, encoding="utf-8", capture_output=True, timeout=20,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    m.require(result.returncode == 0 and len(result.stdout) <= 196608, "READONLY_CENTRAL_OBSERVATION_FAILED")
    observed = json.loads(result.stdout)
    writer = observed.pop("writer")
    node = observed["node"]
    m.require(node and 0 <= int(time.time() * 1000) - node.pop("last_seen_at_ms") <= 30000,
              "EXACT_CURRENT_R6_NODE_NOT_READY")
    m.require(observed == {key: value for key, value in original.items() if key != "writer"},
              "ORIGINAL_COLD_WARM_GENERATION_ONE_LINEAGE_CHANGED")
    m.require(original["writer"]["lease_generation"] == original["intent"]["writer_lease_generation"] == 1
              and writer and writer["task_id"] == args.canary_task_id and writer["binding_id"] == m.BINDING
              and writer["lease_generation"] == current_generation == 2
              and writer["released_at_ms"] is None and writer["expires_at_ms"] > int(time.time() * 1000),
              "EXACT_RENEWED_CURRENT_GENERATION_TWO_AUTHORITY_NOT_FRESH")
    return {"original_writer_generation": 1, "current_writer": writer,
            "current_writer_fresh_unexpired": True, "original_lineage_unchanged": True}


def host_inventory():
    # Match the pinned backend's full WindowsSandbox prefix. CIM enumeration
    # does not activate Windows Sandbox and opens no individual process handle.
    script = "@(Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'WindowsSandbox*' -or $_.Name -in @('vmmemWindowsSandbox','vmmemWindowsSandbox.exe') } | Select-Object Name,ProcessId) | ConvertTo-Json -Compress"
    result = subprocess.run(["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=8,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    m.require(result.returncode == 0 and len(result.stdout) <= 8192, "HOST_VM_OBSERVATION_FAILED")
    rows = json.loads(result.stdout) if result.stdout.strip() else []
    if isinstance(rows, dict): rows = [rows]
    m.require(isinstance(rows, list) and len(rows) <= 32, "HOST_VM_OBSERVATION_INVALID")
    hosts, kernel = [], []
    for row in rows:
        name, pid = row["Name"], int(row["ProcessId"])
        item = {"name": name, "pid": pid}
        if name.lower() in {"vmmemwindowssandbox", "vmmemwindowssandbox.exe"}:
            kernel.append({**item, "ownership_inferred": False})
        else:
            hosts.append(item)
    return {"user_mode_hosts": hosts, "kernel_memory_observations": kernel}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("dispatch", "plan", "unknown", "package-proof"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("dispatch-sha256", "plan-sha256", "unknown-sha256", "observation-id"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--current-writer-generation", type=int, required=True)
    cli = parser.parse_args()
    m.require(Path.cwd().resolve() == ROOT and os.name == "nt", "EXACT_WINDOWS_WORKSPACE_REQUIRED")
    m.require(re.fullmatch(r"[a-f0-9]{32}", cli.observation_id), "OBSERVATION_UUID_REQUIRED")
    m.require(m.file_sha(SOURCE) == REVIEWED_SOURCE_SHA, "REVIEWED_READONLY_HELPER_CHANGED")
    started_ms = int(time.time() * 1000)
    dispatch = evidence(cli.dispatch, cli.dispatch_sha256)
    plan = evidence(cli.plan, cli.plan_sha256)
    unknown = evidence(cli.unknown, cli.unknown_sha256)
    m.require(dispatch["operation"] == "dispatch_owned_sandbox_supported_stop"
              and dispatch["producer_sha256"] == REVIEWED_SOURCE_SHA
              and dispatch["reviewed_plan_sha256"] == cli.plan_sha256
              and dispatch["effect_state"] == "dispatching"
              and plan["operation"] == "prepare_owned_sandbox_supported_stop"
              and plan["producer_sha256"] == REVIEWED_SOURCE_SHA
              and plan["stop_dispatched"] is False
              and dispatch["binding"] == plan["binding"]
              and dispatch["binding_sha256"] == plan["binding_sha256"] == m.digest(plan["binding"]),
              "EXACT_REVIEWED_ORIGINAL_DISPATCH_REQUIRED")
    bound = plan["binding"]
    attempt = bound["stop_attempt_id"]
    m.require(cli.dispatch.name == "owned-stop-dispatch-" + attempt + ".json"
              and cli.plan.name == "owned-stop-plan-" + attempt + ".json"
              and cli.unknown.name == "owned-stop-unknown-" + attempt + ".json"
              and unknown == {"operation": "owned_sandbox_supported_stop", "ok": False,
                             "code": "SUPPORTED_STOP_VM_SHUTDOWN_NOT_CONFIRMED",
                             "stop_invocation_attempted": True,
                             "effect_state": "unknown_requires_original_observation",
                             "automatic_retry_permitted": False, "nonce_saved": False},
              "EXACT_ORIGINAL_SHUTDOWN_UNKNOWN_REQUIRED")
    package, runtime, warm = (bound[key] for key in ("package", "runtime", "warm_receipt"))
    args = SimpleNamespace(candidate=Path(package["candidate"]), package_proof=cli.package_proof,
                           package_proof_sha256=package["package_manifest_sha256"],
                           activation_epoch=runtime["activation_epoch"],
                           process_instance_id=runtime["process_instance_id"],
                           server_instance_id=runtime["server_instance_id"],
                           native_pid=runtime["native_process"]["pid"],
                           native_process_start_token=runtime["native_process"]["supported_native_process_start_token"],
                           warm_receipt=Path(warm["path"]), warm_receipt_sha256=warm["sha256"],
                           canary_task_id=warm["task_id"], warm_job_id=warm["job_id"],
                           warm_action_id=warm["action_id"], service_pid=bound["central"]["service_pid"])
    m.require(m.package_facts(args) == package and m.runtime_facts(args, package) == runtime
              and m.warm_receipt_facts(args) == warm
              and m.native_job_facts(args, warm) == bound["native_warm_job"],
              "ORIGINAL_RUNTIME_JOBS_ACTIONS_OR_FRESH_WRITER_CHANGED")
    authority = central_authority(args, bound["central"], cli.current_writer_generation)
    backend = bound["backend"]
    record_path = Path(backend["record_path"])
    base = Path(os.environ["TEMP"]).resolve() / "wxc-wsb/state-aware"
    m.require(record_path.resolve() == base / backend["sandbox_id"][4:] / "record.json",
              "ORIGINAL_STOP_RECORD_PATH_CHANGED")
    record = m.read_json(record_path)
    m.require(record["sandbox_id"] == backend["sandbox_id"] and record["state"] == "stopped"
              and m.digest(record["mapped_folders"]) == backend["mapped_folders_sha256"]
              and not (base / "daemon.json").exists(),
              "ORIGINAL_STOP_MAPPING_OR_DAEMON_ABSENCE_NOT_CONFIRMED")
    hosts = host_inventory()
    first_host_absence_at_ms = int(time.time() * 1000) if not hosts["user_mode_hosts"] else None
    # Match pinned MXC's five-second backend/VHDX cooldown, retaining the kernel
    # aggregate as an observation only. No new lifecycle operation occurs.
    if first_host_absence_at_ms is not None:
        time.sleep(5)
        hosts = host_inventory()
    m.require(m.read_json(record_path) == record and not (base / "daemon.json").exists()
              and m.runtime_facts(args, package) == runtime
              and m.native_job_facts(args, warm) == bound["native_warm_job"],
              "ORIGINAL_POST_STOP_STATE_CHANGED_DURING_OBSERVATION")
    empty = not hosts["user_mode_hosts"] and first_host_absence_at_ms is not None
    authority_after = central_authority(args, bound["central"], cli.current_writer_generation)
    m.require(authority_after["current_writer"]["lease_generation"] == authority["current_writer"]["lease_generation"],
              "CURRENT_AUTHORITY_CHANGED_DURING_OBSERVATION")
    report = {"schema_version": 1, "operation": "original_owned_stop_readonly_supplement",
              "ok": empty, "observation_state": "verified_owned_hosts_absent" if empty else "owned_host_shutdown_pending",
              "observation_started_at_ms": started_ms, "observation_finished_at_ms": int(time.time() * 1000),
              "producer_sha256": m.file_sha(Path(__file__)), "original_stop_producer_sha256": REVIEWED_SOURCE_SHA,
              "original_stop_attempt_id": attempt, "original_stop_result_preserved": "UNKNOWN",
              "dispatch_sha256": cli.dispatch_sha256, "reviewed_plan_sha256": cli.plan_sha256,
              "original_unknown_sha256": cli.unknown_sha256, "original_binding_sha256": plan["binding_sha256"],
              "stop_invocation_count_by_observer": 0, "automatic_retry_permitted": False,
              "nonce_saved": False, "database_mutated": False, "node_journal_modified": False,
              "processes_terminated": False, "original_action_replayed": False,
              "authority": authority_after,
              "owned_host_absence_first_at_ms": first_host_absence_at_ms,
              "pinned_backend_cooldown_seconds": 5,
              "kernel_absence_required_by_pinned_backend": False,
              "pinned_backend_contract": "https://raw.githubusercontent.com/microsoft/mxc/cbe1774364ea2ec846f56ab744e43a416f751420/docs/windows-sandbox/windows-sandbox-reference.md",
              "pinned_backend_implementation": "https://raw.githubusercontent.com/microsoft/mxc/cbe1774364ea2ec846f56ab744e43a416f751420/src/backends/windows_sandbox/lifecycle/src/vm.rs",
              "observed": {"sandbox_id": backend["sandbox_id"], "record_state": "stopped",
                           "record_sha256": m.file_sha(record_path),
                           "mapped_folders_sha256": backend["mapped_folders_sha256"],
                           "daemon_record_absent": True,
                           "host_vm_process_count": len(hosts["user_mode_hosts"]),
                           "kernel_memory_process_count": len(hosts["kernel_memory_observations"]),
                           "host_processes": hosts, "same_native_runtime_alive": True,
                           "active_native_jobs": 0, "original_cold_warm_lineage_unchanged": True,
                           "same_task_writer_fresh_unexpired": True}}
    saved = m.write_new(HERE / ("owned-stop-readonly-supplement-" + cli.observation_id + ".json"), report)
    print(json.dumps({"operation": report["operation"], "ok": empty,
                      "observation_state": report["observation_state"], **saved, "observed": report["observed"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        code = code if re.fullmatch(r"[A-Za-z0-9_]{1,128}", code) else "READONLY_OBSERVATION_FAILED"
        print(json.dumps({"operation": "original_owned_stop_readonly_supplement", "ok": False,
                          "code": code, "stop_invocation_count_by_observer": 0,
                          "automatic_retry_permitted": False, "nonce_saved": False}))
        raise SystemExit(1)
