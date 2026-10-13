"""Prepare, then stop one proven owned r6 sandbox through supported phase stop.

Default mode observes and saves a review plan. Execute requires that exact plan
and SHA, an unused stop-attempt UUID, settled warm canary lineage, and fresh
ownership guards. The only lifecycle mutation is one packaged _run_envelope
stop call. Nonce stays in memory; no log, config secret or raw output is saved.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import socket
import sqlite3
import subprocess
import sys
import time

ROOT = Path(r"E:\DEV\Codex-web")
REPORTS = ROOT / ".coding-tools/reports/sandbox-not-started-20261012"
PROFILE = Path(os.environ.get("APPDATA", "")) / "web-mcp-assistant"
BACKEND_NAMES = {"wxc-exec.exe", "wxc-windows-sandbox-daemon.exe", "wxc-windows-sandbox-guest.exe",
                 "mxc-windows-sandbox.provenance.json"}
DEVICE = "4c4b7a5b-7744-49ae-a490-78a528a00471"
WORKSPACE = "workspace_f93b5bac9dc74fae9cea66f44c4ebc94"
BINDING = "bind_71661b1046884174b01c99af5f8546aa"
GENERATION = "generation_a420c8bfcfcb4e42b5bb7fc5e5cec097"
DISPATCHED = False
FAILURE_PATH = None


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    require(path.is_file() and path.stat().st_size <= 1048576, "BOUNDED_EVIDENCE_FILE_REQUIRED")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def same_path(left, right):
    return os.path.normcase(str(Path(left).resolve())) == os.path.normcase(str(Path(right).resolve()))


def write_new(path, report):
    with path.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write("\n")
    return {"path": str(path), "sha256": file_sha(path)}


def process_identity(pid):
    """Use live Win32 handles and exact FILETIME; never terminate a process."""
    require(os.name == "nt" and isinstance(pid, int) and pid > 0, "WIN32_PROCESS_IDENTITY_REQUIRED")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    kernel.GetProcessTimes.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME))
    kernel.QueryFullProcessImageNameW.argtypes = (wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                ctypes.POINTER(wintypes.DWORD))
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    handle = kernel.OpenProcess(0x1000, False, pid)
    require(bool(handle), "LIVE_PROCESS_HANDLE_UNAVAILABLE")
    try:
        exit_code = wintypes.DWORD()
        require(kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)) and exit_code.value == 259,
                "EXACT_PROCESS_NOT_LIVE")
        created, exited, kernel_time, user_time = (wintypes.FILETIME() for _ in range(4))
        require(kernel.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited),
                                      ctypes.byref(kernel_time), ctypes.byref(user_time)), "PROCESS_CREATION_TIME_UNAVAILABLE")
        size = wintypes.DWORD(32768)
        image = ctypes.create_unicode_buffer(size.value)
        require(kernel.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size)),
                "PROCESS_EXECUTABLE_UNAVAILABLE")
        return {"pid": pid, "creation_time": str((created.dwHighDateTime << 32) | created.dwLowDateTime),
                "executable_path": str(Path(image.value).resolve())}
    finally:
        kernel.CloseHandle(handle)


def host_processes(*, prove_user_mode_identity=True):
    script = "@(Get-CimInstance Win32_Process | Where-Object { $_.Name -in @('WindowsSandbox.exe','WindowsSandboxClient.exe','WindowsSandboxServer.exe','WindowsSandboxRemoteSession.exe','vmmemWindowsSandbox.exe','vmmemWindowsSandbox') } | Select-Object Name,ProcessId) | ConvertTo-Json -Compress"
    result = subprocess.run(["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=8,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    require(result.returncode == 0 and len(result.stdout) <= 8192, "HOST_VM_OBSERVATION_FAILED")
    rows = json.loads(result.stdout) if result.stdout.strip() else []
    if isinstance(rows, dict):
        rows = [rows]
    require(isinstance(rows, list) and len(rows) <= 32, "HOST_VM_OBSERVATION_INVALID")
    user_mode, kernel_memory = [], []
    for row in rows:
        name, pid = row["Name"], int(row["ProcessId"])
        if name.lower() in {"vmmemwindowssandbox", "vmmemwindowssandbox.exe"}:
            # This opaque kernel aggregate is outside the vendor VM ownership set.
            # Its presence is observation only; it grants no termination authority.
            kernel_memory.append({"name": name, "pid": pid, "ownership_inferred": False})
        else:
            identity = process_identity(pid) if prove_user_mode_identity else {"pid": pid}
            user_mode.append({"name": name, **identity})
    return {"user_mode_hosts": user_mode, "kernel_memory_observations": kernel_memory}


def package_facts(args):
    candidate = args.candidate.resolve(strict=True)
    require(candidate.is_relative_to(ROOT / "dist") and candidate.name == "win-unpacked",
            "EXACT_REPOSITORY_CANDIDATE_REQUIRED")
    require(args.package_proof.resolve().parent == REPORTS and file_sha(args.package_proof) == args.package_proof_sha256,
            "REVIEWED_PACKAGE_MANIFEST_CHANGED")
    manifest = read_json(args.package_proof)
    require(manifest.get("ok") is True and same_path(manifest["candidate"], candidate),
            "VERIFIED_R6_MANIFEST_IDENTITY_REQUIRED")
    resources = candidate / "resources/resources"
    adapter = resources / "coding-tools-mcp/coding_tools_mcp/windows_mxc_state_aware.py"
    backend = resources / "tools/mxc-windows-sandbox"
    require(set(manifest["backend_hashes"]) == BACKEND_NAMES,
            "EXACT_BACKEND_MANIFEST_REQUIRED")
    files = {candidate / "resources/app.asar": manifest["app_asar_sha256"],
             candidate / "Coding Tools MCP.exe": manifest["executable_sha256"],
             adapter: manifest["packaged_adapter_sha256"],
             **{backend / name: expected for name, expected in manifest["backend_hashes"].items()}}
    for path, expected in files.items():
        require(re.fullmatch(r"[a-f0-9]{64}", expected) and file_sha(path) == expected,
                "EXACT_MANIFESTED_R6_PACKAGE_CHANGED")
    return {"candidate": str(candidate), "resources": str(resources), "backend": str(backend),
            "module_root": str(resources / "coding-tools-mcp"), "adapter_sha256": manifest["packaged_adapter_sha256"],
            "daemon_sha256": manifest["backend_hashes"]["wxc-windows-sandbox-daemon.exe"],
            "package_manifest_sha256": args.package_proof_sha256,
            "package_hashes": {str(path.relative_to(candidate)): expected for path, expected in files.items()}}


def runtime_facts(args, package):
    state = read_json(PROFILE / "runtime-state.json")
    epoch = read_json(PROFILE / "activation-epoch.json")["current"]
    require(state["nativePid"] == args.native_pid
            and str(state["nativeProcessStartToken"]) == args.native_process_start_token
            and state["nativeActivationEpochId"] == args.activation_epoch
            and same_path(state["nativeModuleRoot"], package["module_root"])
            and same_path(state["nativeCommand"], Path(package["resources"]) / "native-python/pythonw.exe"),
            "EXACT_MANIFESTED_NATIVE_RUNTIME_CHANGED")
    require(epoch["activation_epoch_id"] == args.activation_epoch and epoch["state"] == "READY"
            and epoch["admission_state"] == "OPEN", "EXACT_READY_OPEN_EPOCH_REQUIRED")
    live = process_identity(args.native_pid)
    # Electron's supported native identity contract floors FILETIME to microseconds.
    # Daemon and vendor VM identities below still compare exact Win32 FILETIME.
    exact_creation = int(live["creation_time"])
    supported_native_token = str(exact_creation - exact_creation % 10)
    require(supported_native_token == args.native_process_start_token
            and same_path(live["executable_path"], state["nativeCommand"]), "LIVE_NATIVE_PROCESS_IDENTITY_CHANGED")
    live["supported_native_process_start_token"] = supported_native_token
    live["native_token_normalization"] = "exact_FILETIME_minus_modulo_10"
    return {"activation_epoch": args.activation_epoch, "process_instance_id": args.process_instance_id,
            "server_instance_id": args.server_instance_id, "native_process": live,
            "native_module_root": state["nativeModuleRoot"], "epoch_state": epoch["state"],
            "admission_state": epoch["admission_state"]}


def warm_receipt_facts(args):
    require(args.warm_receipt.resolve().is_relative_to(ROOT / ".coding-tools/reports")
            and file_sha(args.warm_receipt) == args.warm_receipt_sha256
            and args.warm_receipt.stat().st_size <= 196608, "EXACT_BOUNDED_WARM_RECEIPT_REQUIRED")
    text = args.warm_receipt.read_text(encoding="utf-8-sig")
    try:
        parsed = json.loads(text)
        rows = [parsed]
    except json.JSONDecodeError:
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    ready = [row for row in rows if row.get("phase") == "ready_for_root_supported_owned_vm_stop"
             and row.get("ok") is True]
    require(len(ready) == 1, "ONE_SUCCESSFUL_ORIGINAL_WARM_READY_CHECKPOINT_REQUIRED")
    final = ready[0]
    require(final["task_id"] == args.canary_task_id and set(final["proofs"]) == {"cold", "warm"}
            and final["current_generation_census"] == {"open_tasks": 1, "unreleased_writers": 1, "unsettled_actions": 0},
            "WARM_CHECKPOINT_TASK_OR_CENSUS_CHANGED")
    receipt = final["proofs"]["warm"]
    require(receipt["job_id"] == args.warm_job_id and receipt["action_id"] == args.warm_action_id,
            "WARM_ORIGINAL_JOB_RECEIPT_IDENTITY_CHANGED")
    for lane, proof in final["proofs"].items():
        require(proof["lane"] == lane and proof["attempt_number"] == 1 and proof["exit_code"] == 0
                and re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", proof["version"])
                and proof["runtime_identity"]["activation_epoch_id"] == args.activation_epoch
                and proof["runtime_identity"]["process_instance_id"] == args.process_instance_id
                and proof["runtime_identity"]["server_instance_id"] == args.server_instance_id,
                "COMPLETED_STAGE_PROOF_IDENTITY_CHANGED")
    require(final["proofs"]["cold"]["version"] == receipt["version"], "COLD_WARM_NODE_VERSION_CHANGED")
    return {"path": str(args.warm_receipt), "sha256": args.warm_receipt_sha256,
            "task_id": args.canary_task_id, "action_id": args.warm_action_id, "job_id": args.warm_job_id,
            "receipt_id": receipt["receipt_id"], "attempt_id": receipt["attempt_id"], "exit_code": 0,
            "writer_lease_generation": final["writer_lease_generation"],
            "stage_proofs": final["proofs"]}


def native_job_facts(args, warm):
    c = sqlite3.connect((ROOT / ".coding-tools/orchestration/ledger.sqlite3").resolve().as_uri() + "?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA query_only=ON")
    c.execute("BEGIN")
    jobs = []
    for lane in ("cold", "warm"):
        proof = warm["stage_proofs"][lane]
        row = c.execute("SELECT * FROM managed_process_jobs WHERE job_id=?", (proof["job_id"],)).fetchone()
        require(row is not None, "ORIGINAL_CANARY_NATIVE_JOB_MISSING")
        job = dict(row)
        metadata = json.loads(job.pop("metadata_json"))
        require(job["lifecycle_state"] == "exited" and job["finished_at"] and metadata.get("exit_code") == 0
                and job["command_id"] == proof["command_id"]
                and job["process_instance_id"] == args.process_instance_id
                and job["runtime_instance_id"] == args.server_instance_id, "ORIGINAL_CANARY_NATIVE_JOB_NOT_TERMINAL")
        jobs.append({"lane": lane, "job_id": job["job_id"], "command_id": job["command_id"],
                     "lifecycle_state": job["lifecycle_state"], "finished_at": job["finished_at"],
                     "process_instance_id": job["process_instance_id"], "runtime_instance_id": job["runtime_instance_id"],
                     "exit_code": 0, "metadata_sha256": digest(metadata)})
    active = c.execute("SELECT COUNT(*) FROM managed_process_jobs WHERE lifecycle_state IN ('starting','running','terminating','orphaned')").fetchone()[0]
    c.close()
    require(active == 0, "ACTIVE_NATIVE_JOB_PRESENT_DO_NOT_STOP")
    return {"original_stage_jobs": jobs, "active_job_count": active}


def central_facts(args, warm):
    script = r'''
import json,sqlite3,subprocess,time
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
                       "GENERATION": GENERATION, "DEVICE": DEVICE}.items():
        script = script.replace("__" + key + "__", repr(value))
    result = subprocess.run(["ssh.exe", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "-o",
                             "StrictHostKeyChecking=yes", "svhome@100.116.112.22", "python3", "-B", "-"],
                            input=script, text=True, encoding="utf-8", capture_output=True, timeout=20,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    require(result.returncode == 0 and len(result.stdout) <= 196608, "READONLY_CENTRAL_OBSERVATION_FAILED")
    observed = json.loads(result.stdout)
    a, t, i, writer = (observed[key] for key in ("action", "task", "intent", "writer"))
    require(observed["service_pid"] == args.service_pid and a and t and i and writer
            and a["action_id"] == args.warm_action_id and a["device_id"] == DEVICE
            and a["workspace_id"] == WORKSPACE and a["workspace_generation"] == GENERATION
            and a["binding_id"] == BINDING and a["delivery_state"] == "settled" and a["settled_at_ms"]
            and i["task_id"] == args.canary_task_id and t["binding_id"] == BINDING
            and t["workspace_id"] == WORKSPACE and t["workspace_generation"] == GENERATION
            and t["closed_at_ms"] is None and writer["task_id"] == args.canary_task_id
            and writer["binding_id"] == BINDING and writer["released_at_ms"] is None
            and writer["expires_at_ms"] > int(time.time() * 1000)
            and writer["lease_generation"] == i["writer_lease_generation"] == warm["writer_lease_generation"]
            and observed["unsettled_generation_actions"] == 0 and observed["other_open_generation_tasks"] == 0,
            "CENTRAL_WARM_BOUNDARY_NOT_EXCLUSIVE_SETTLED")
    attempts, receipts = observed["attempts"], observed["receipts"]
    proof = warm["stage_proofs"]["warm"]
    stage_ids = {item["action_id"] for item in warm["stage_proofs"].values()}
    require(len(stage_ids) == 2 and len(observed["task_exec_actions"]) == 2
            and {item["action_id"] for item in observed["task_exec_actions"]} == stage_ids
            and all(item["delivery_state"] == "settled" and item["settled_at_ms"]
                    for item in observed["task_exec_actions"]), "EXACT_COLD_WARM_ACTIONS_NOT_SETTLED")
    require(len(attempts) == len(receipts) == 1 and attempts[0]["attempt_number"] == 1
            and attempts[0]["attempt_id"] == proof["attempt_id"]
            and receipts[0]["receipt_id"] == proof["receipt_id"]
            and receipts[0]["receipt_state"] == "completed"
            and receipts[0]["safe_payload"]["job_id"] == args.warm_job_id
            and receipts[0]["safe_payload"]["command_id"] == proof["command_id"]
            and receipts[0]["safe_payload"]["runtime_identity"] == proof["runtime_identity"]
            and receipts[0]["safe_payload"]["exit_code"] == 0
            and receipts[0]["safe_payload"]["task_id"] == args.canary_task_id,
            "CENTRAL_ORIGINAL_WARM_RECEIPT_CHANGED")
    node = observed["node"]
    require(node and node["readiness"] == "ready" and node["runtime_instance_id"] == args.process_instance_id
            and node["mcp_server_instance_id"] == args.server_instance_id and node["activation_epoch"] == args.activation_epoch
            and 0 <= int(time.time() * 1000) - node["last_seen_at_ms"] <= 30000,
            "EXACT_CURRENT_R6_NODE_NOT_READY")
    # Volatile heartbeat time is excluded from exact before/after comparison.
    node.pop("last_seen_at_ms")
    # The exact holder renews this expiry every 20s; guard freshness, compare stable identity.
    writer.pop("expires_at_ms")
    writer["fresh_unexpired_observed"] = True
    return observed


def owned_backend(args, package):
    require(re.fullmatch(r"wsb:[0-9a-f]{8}", args.sandbox_id), "EXACT_SANDBOX_TOKEN_REQUIRED")
    base = Path(os.environ["TEMP"]).resolve() / "wxc-wsb/state-aware"
    daemon_path, record_path = base / "daemon.json", base / args.sandbox_id[4:] / "record.json"
    daemon, record = read_json(daemon_path), read_json(record_path)
    require(daemon["active_sandbox_id"] == args.sandbox_id and daemon["ready"] is True
            and daemon["protocol_version"] == 1 and re.fullmatch(r"[0-9a-f]{32}", daemon["nonce"])
            and record["sandbox_id"] == args.sandbox_id and record["state"] == "started",
            "EXACT_LIVE_STARTED_SANDBOX_REQUIRED")
    mappings = record["mapped_folders"]
    writable = [entry for entry in mappings if entry.get("read_only") is False]
    require(len(writable) == 1 and same_path(writable[0]["host"], ROOT), "EXACT_WORKSPACE_MAPPING_REQUIRED")
    for entry in mappings:
        require(entry.get("read_only") in (True, False) and isinstance(entry.get("host"), str)
                and isinstance(entry.get("sandbox"), str), "MAPPED_FOLDER_RECORD_INVALID")
    live = process_identity(int(daemon["pid"]))
    expected_daemon = Path(package["backend"]) / "wxc-windows-sandbox-daemon.exe"
    require(live["creation_time"] == str(daemon["pid_creation_time"])
            and same_path(live["executable_path"], expected_daemon)
            and file_sha(Path(live["executable_path"])) == package["daemon_sha256"],
            "LIVE_DAEMON_NOT_EXACT_R6_PACKAGE")
    hosts = host_processes()
    proof = {(int(item["pid"]), str(item["creation_time"])) for item in daemon["vm_processes"]}
    actual = {(item["pid"], item["creation_time"]) for item in hosts["user_mode_hosts"]}
    require(bool(proof) and actual == proof, "FOREIGN_OR_UNPROVEN_VM_PROCESS_PRESENT")
    port = daemon["ipc_port"]
    require(isinstance(port, int) and 1024 <= port <= 65535, "DAEMON_IPC_PORT_INVALID")
    with socket.create_connection(("127.0.0.1", port), timeout=3) as connection:
        connection.settimeout(3)
        connection.sendall(("PING " + daemon["nonce"] + "\n").encode("ascii"))
        reply = b""
        while b"\n" not in reply and len(reply) <= 64:
            part = connection.recv(65 - len(reply))
            if not part:
                break
            reply += part
    require(reply == b"PONG\n", "AUTHENTICATED_LIVE_DAEMON_PING_FAILED")
    require(read_json(daemon_path) == daemon and read_json(record_path) == record,
            "DAEMON_IDENTITY_OR_MAPPING_CHANGED_DURING_OBSERVATION")
    return daemon, {"sandbox_id": args.sandbox_id, "record_path": str(record_path),
                   "record_sha256": file_sha(record_path), "record_state": "started",
                   "mapped_folders_sha256": digest(mappings), "workspace_mapping_exact": True,
                   "daemon_process": live, "daemon_executable_sha256": package["daemon_sha256"],
                   "authenticated_nonce_ping_verified": True, "nonce_saved": False,
                   "host_processes": hosts, "vendor_ownership_exact": True}


def main():
    global DISPATCHED, FAILURE_PATH
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate", "package-proof", "warm-receipt"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("package-proof-sha256", "warm-receipt-sha256", "activation-epoch", "process-instance-id",
                 "server-instance-id", "native-process-start-token", "canary-task-id", "warm-job-id",
                 "warm-action-id", "sandbox-id", "stop-attempt-id"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--native-pid", type=int, required=True)
    parser.add_argument("--service-pid", type=int, required=True)
    parser.add_argument("--execute-reviewed-plan", type=Path)
    parser.add_argument("--reviewed-plan-sha256")
    args = parser.parse_args()
    require(Path.cwd().resolve() == ROOT and os.name == "nt", "EXACT_WINDOWS_WORKSPACE_REQUIRED")
    require(re.fullmatch(r"[a-f0-9]{32}", args.stop_attempt_id), "STOP_ATTEMPT_UUID_REQUIRED")
    require(bool(args.execute_reviewed_plan) == bool(args.reviewed_plan_sha256), "EXACT_REVIEWED_PLAN_PAIR_REQUIRED")
    dispatch_path = REPORTS / ("owned-stop-dispatch-" + args.stop_attempt_id + ".json")
    FAILURE_PATH = REPORTS / ("owned-stop-unknown-" + args.stop_attempt_id + ".json")
    require(not dispatch_path.exists() and not FAILURE_PATH.exists(), "STOP_ATTEMPT_ALREADY_USED_DO_NOT_REPLAY")
    reviewed = None
    if args.execute_reviewed_plan:
        require(args.execute_reviewed_plan.resolve().parent == REPORTS
                and file_sha(args.execute_reviewed_plan) == args.reviewed_plan_sha256, "REVIEWED_STOP_PLAN_CHANGED")
        reviewed = read_json(args.execute_reviewed_plan)
        require(reviewed["stop_dispatched"] is False and reviewed["producer_sha256"] == file_sha(Path(__file__))
                and 0 <= int(time.time() * 1000) - reviewed["observed_at_ms"] <= 900000,
                "REVIEWED_STOP_PLAN_NOT_CURRENT")
    package = package_facts(args)
    runtime = runtime_facts(args, package)
    receipt = warm_receipt_facts(args)
    native = native_job_facts(args, receipt)
    central = central_facts(args, receipt)
    daemon, backend = owned_backend(args, package)
    binding = {"stop_attempt_id": args.stop_attempt_id, "package": package, "runtime": runtime,
               "warm_receipt": receipt, "native_warm_job": native, "central": central, "backend": backend}
    report = {"schema_version": 1, "operation": "prepare_owned_sandbox_supported_stop",
              "observed_at_ms": int(time.time() * 1000), "producer_sha256": file_sha(Path(__file__)),
              "stop_dispatched": False, "nonce_saved": False, "database_mutated": False,
              "node_journal_modified": False, "phase": "stop", "deprovision_performed": False,
              "original_warm_action_replayed": False, "binding": binding, "binding_sha256": digest(binding)}
    if reviewed is None:
        saved = write_new(REPORTS / ("owned-stop-plan-" + args.stop_attempt_id + ".json"), report)
        print(json.dumps({"operation": report["operation"], "ok": True, **saved, "stop_dispatched": False}))
        return
    require(reviewed["binding"] == binding and reviewed["binding_sha256"] == digest(binding),
            "REVIEWED_OWNERSHIP_OR_WARM_LINEAGE_CHANGED")
    # Import leaf adapter only. The serving Runtime and its cached manager remain alive.
    sys.path.insert(0, package["module_root"])
    module = importlib.import_module("coding_tools_mcp.windows_mxc_state_aware")
    require(same_path(module.__file__, Path(package["module_root"]) / "coding_tools_mcp/windows_mxc_state_aware.py")
            and file_sha(Path(module.__file__)) == package["adapter_sha256"], "EXACT_REVIEWED_R6_ADAPTER_REQUIRED")
    manager = module.MxcWindowsSandboxManager(executor_directory=Path(package["backend"]))
    module.verify_mxc_windows_sandbox_candidate()
    # Final identity, nonce, creation-time, mapping, runtime and quiescence fences.
    daemon_again, backend_again = owned_backend(args, package)
    require(daemon_again == daemon and backend_again == backend
            and runtime_facts(args, package) == runtime and native_job_facts(args, receipt) == native
            and central_facts(args, receipt) == central and package_facts(args) == package,
            "ORIGINAL_OWNERSHIP_CHANGED_BEFORE_STOP")
    write_new(dispatch_path, {**report, "operation": "dispatch_owned_sandbox_supported_stop",
              "reviewed_plan_sha256": args.reviewed_plan_sha256, "effect_state": "dispatching"})
    DISPATCHED = True
    result = manager._run_envelope(module._phase_config("stop", args.sandbox_id),
                                   timeout_seconds=module.MAX_MXC_WSB_PHASE_SECONDS)
    require(isinstance(result, dict), "SUPPORTED_STOP_RESULT_INVALID")
    base = Path(os.environ["TEMP"]).resolve() / "wxc-wsb/state-aware"
    record = read_json(Path(backend["record_path"]))
    require(record["sandbox_id"] == args.sandbox_id and record["state"] == "stopped"
            and digest(record["mapped_folders"]) == backend["mapped_folders_sha256"]
            and not (base / "daemon.json").exists(),
            "SUPPORTED_STOP_NOT_VERIFIED_MAPPING_PRESERVED_DAEMON_GONE")
    # Windows may retain its opaque memory aggregate briefly after owned STOP.
    # Observe bounded shutdown only; never terminate any remaining process.
    shutdown_deadline = time.monotonic() + 30
    while True:
        after_hosts = host_processes(prove_user_mode_identity=False)
        if not after_hosts["user_mode_hosts"] and not after_hosts["kernel_memory_observations"]:
            break
        require(time.monotonic() < shutdown_deadline, "SUPPORTED_STOP_VM_SHUTDOWN_NOT_CONFIRMED")
        time.sleep(0.5)
    require(runtime_facts(args, package) == runtime and native_job_facts(args, receipt) == native
            and central_facts(args, receipt) == central, "WARM_RUNTIME_OR_LINEAGE_CHANGED_AFTER_STOP")
    report.update(operation="owned_sandbox_supported_stop_verified", observed_at_ms=int(time.time() * 1000),
                  stop_dispatched=True, stop_invocation_count=1, reviewed_plan_sha256=args.reviewed_plan_sha256,
                  result_sha256=digest(result), result_keys=sorted(result),
                  after={"sandbox_id": args.sandbox_id, "record_state": "stopped",
                         "mapped_folders_sha256": digest(record["mapped_folders"]),
                         "record_sha256": file_sha(Path(backend["record_path"])), "daemon_record_absent": True,
                         "host_vm_process_count": 0, "kernel_memory_process_count": 0,
                         "bounded_shutdown_observation_seconds": 30, "same_native_runtime_alive": True,
                         "central_warm_action_unchanged_settled": True})
    saved = write_new(REPORTS / ("owned-stop-receipt-" + args.stop_attempt_id + ".json"), report)
    print(json.dumps({"operation": report["operation"], "ok": True, **saved, "stop_dispatched": True,
                      "after": report["after"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else getattr(error, "code", type(error).__name__)
        code = code if isinstance(code, str) and re.fullmatch(r"[A-Za-z0-9_]{1,128}", code) else "STOP_OBSERVER_FAILED"
        failure = {"operation": "owned_sandbox_supported_stop", "ok": False, "code": code,
                   "stop_invocation_attempted": DISPATCHED,
                   "effect_state": "unknown_requires_original_observation" if DISPATCHED else "not_dispatched",
                   "automatic_retry_permitted": False, "nonce_saved": False}
        if DISPATCHED and FAILURE_PATH is not None and not FAILURE_PATH.exists():
            write_new(FAILURE_PATH, failure)
        print(json.dumps(failure))
        raise SystemExit(1)
