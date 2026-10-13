"""Observe automatic retirement of one owned Sandbox; never start or stop it."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import re
import time

import psutil

ROOT = Path(r"E:\DEV\Codex-web")
PROFILE = Path(os.environ.get("APPDATA", "")) / "web-mcp-assistant"
HOST_NAMES = {"windowssandbox.exe", "windowssandboxclient.exe", "windowssandboxserver.exe", "windowssandboxremotesession.exe"}
SANDBOX_MEMORY_NAMES = {"vmmemwindowssandbox", "vmmemwindowssandbox.exe", "vmmemwsb", "vmmemwsb.exe"}


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def read(file):
    require(file.is_file() and file.stat().st_size <= 2097152, "BOUNDED_JSON_REQUIRED")
    return json.loads(file.read_text(encoding="utf-8-sig"))


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def pathkey(value):
    return os.path.normcase(os.path.normpath(str(value))).casefold()


def identity(pid):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
                                      ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME))
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    handle = kernel.OpenProcess(0x1000, False, int(pid))
    require(bool(handle), "EXACT_PROCESS_HANDLE_UNAVAILABLE")
    try:
        created, exited, system, user = (wintypes.FILETIME() for _ in range(4))
        require(kernel.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(system), ctypes.byref(user)),
                "EXACT_PROCESS_CREATION_UNAVAILABLE")
        process = psutil.Process(int(pid))
        return {"pid": int(pid), "creation_time": str((created.dwHighDateTime << 32) | created.dwLowDateTime),
                "executable_path": str(Path(process.exe()).resolve())}
    finally:
        kernel.CloseHandle(handle)


def process_sample():
    hosts, memory = [], []
    for process in psutil.process_iter(["pid", "name", "memory_info"]):
        try:
            name = (process.info["name"] or "").lower()
            if name not in HOST_NAMES and not name.startswith("vmmem"):
                continue
            usage = process.info["memory_info"]
            row = {"pid": process.pid, "name": process.info["name"], "working_set_bytes": usage.rss,
                   "private_bytes": getattr(usage, "private", None)}
            if name in HOST_NAMES:
                hosts.append({**row, **identity(process.pid)})
            else:
                memory.append({**row, "ownership_inferred": False, "sandbox_named_aggregate": name in SANDBOX_MEMORY_NAMES})
        except psutil.NoSuchProcess:
            continue
        except psutil.AccessDenied:
            require(False, "RELEVANT_PROCESS_MEMORY_UNAVAILABLE")
    return {"observed_at_ms": int(time.time() * 1000), "user_mode_hosts": hosts, "kernel_memory": memory}


def runtime(pins, candidate):
    state = read(PROFILE / "runtime-state.json")
    epoch = read(PROFILE / "activation-epoch.json")["current"]
    require(epoch["activation_epoch_id"] == pins["activation_epoch"] and epoch["state"] == "READY"
            and epoch["admission_state"] == "OPEN", "EXACT_READY_EPOCH_CHANGED")
    require(isinstance(pins.get("supervisor_instance_id"), str)
            and re.fullmatch(r"[a-f0-9]{24}", pins["supervisor_instance_id"])
            and type(pins.get("native_pid")) is int and pins["native_pid"] > 1
            and isinstance(pins.get("native_process_start_token"), str)
            and re.fullmatch(r"[0-9]{16,20}", pins["native_process_start_token"]), "EXACT_LAUNCHER_PINS_REQUIRED")
    require(state["nativeActivationEpochId"] == pins["activation_epoch"]
            and state["nativeInstanceId"] == pins["supervisor_instance_id"]
            and state["nativePid"] == pins["native_pid"]
            and str(state["nativeProcessStartToken"]) == pins["native_process_start_token"]
            and pathkey(state["nativeModuleRoot"]) == pathkey(candidate / "resources/resources/coding-tools-mcp"), "EXACT_NATIVE_MODULE_CHANGED")
    live = identity(state["nativePid"])
    normalized = str(int(live["creation_time"]) - int(live["creation_time"]) % 10)
    require(normalized == str(state["nativeProcessStartToken"]) and pathkey(live["executable_path"]) == pathkey(state["nativeCommand"]),
            "EXACT_NATIVE_PROCESS_CHANGED")
    return {"activation_epoch_id": epoch["activation_epoch_id"], "supervisor_instance_id": state["nativeInstanceId"],
            "reviewed_mcp_process_instance_id": pins["process_instance_id"], "native_process": live}


def terminal_receipt(file):
    if not file.exists():
        return None
    require(file.stat().st_size <= 2097152, "REMOTE_RECEIPT_TOO_LARGE")
    rows = []
    for line in file.read_text(encoding="utf-8-sig").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue  # An append may still be in progress.
        if row.get("operation") == "isolated_idle_shared_mcp_canary":
            rows.append(row)
    verified = [row for row in rows if row.get("phase") == "isolated_terminal_verified"]
    finals = [row for row in rows if row.get("phase") == "final"]
    if not verified:
        return None
    require(len(verified) == 1, "MULTIPLE_ISOLATED_TERMINAL_RECEIPTS")
    return {"terminal": verified[0], "final": finals[-1] if finals else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pins", type=Path, required=True)
    parser.add_argument("--parity-proof", type=Path, required=True)
    parser.add_argument("--remote-receipt", type=Path, required=True)
    parser.add_argument("--ready-signal", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(os.name == "nt" and not args.output.exists() and not args.ready_signal.exists(), "ONE_NEW_WINDOWS_OBSERVATION_REQUIRED")
    pins, parity = read(args.pins), read(args.parity_proof)
    candidate = Path(parity["candidate"]).resolve()
    require(candidate.is_relative_to(ROOT / "dist") and parity["ok"] is True
            and sha(candidate / "Coding Tools MCP.exe") == parity["executable_sha256"]
            and sha(candidate / "resources/app.asar") == parity["app_asar_sha256"], "EXACT_PACKAGE_REQUIRED")
    backend = candidate / "resources/resources/tools/mxc-windows-sandbox"
    provenance = read(backend / "mxc-windows-sandbox.provenance.json")
    daemon_exe = backend / "wxc-windows-sandbox-daemon.exe"
    require(sha(daemon_exe) == provenance["binaries"][daemon_exe.name]["sha256"], "EXACT_DAEMON_BINARY_REQUIRED")
    base = Path(os.environ["TEMP"]).resolve() / "wxc-wsb/state-aware"
    daemon_file = base / "daemon.json"
    initial_runtime = runtime(pins, candidate)
    before = process_sample()
    require(not daemon_file.exists() and not before["user_mode_hosts"], "BASELINE_HAS_SANDBOX_OWNER_REVIEW_REQUIRED")
    args.ready_signal.write_text(json.dumps({"observer_ready": True, "observed_at_ms": int(time.time() * 1000)}), encoding="utf-8")
    warm = None
    samples = [before]
    started = time.monotonic()
    last_status = started
    report = {"schema_version": 1, "operation": "automatic_owned_sandbox_idle_observation", "ok": False,
              "capture_started_at_ms": before["observed_at_ms"], "pins_sha256": sha(args.pins), "parity_sha256": sha(args.parity_proof),
              "expected_idle_seconds": 30, "deprovision_phase_bound_seconds": 210, "runtime": initial_runtime,
              "vm_started_by_observer": False, "lifecycle_mutation_performed": False, "nonce_saved": False,
              "command_lines_collected": False, "before": before}
    try:
        deadline = started + 600
        while time.monotonic() < deadline:
            sample = process_sample()
            samples.append(sample)
            require(runtime(pins, candidate) == initial_runtime, "NATIVE_RUNTIME_CHANGED_DURING_IDLE_OBSERVATION")
            if warm is None and daemon_file.exists():
                daemon = read(daemon_file)
                sandbox_id = daemon.get("active_sandbox_id")
                if daemon.get("ready") is True and isinstance(sandbox_id, str) and re.fullmatch(r"wsb:[a-f0-9]{8}", sandbox_id):
                    record_file = base / sandbox_id[4:] / "record.json"
                    record = read(record_file)
                    mappings = record.get("mapped_folders", [])
                    writable = [entry for entry in mappings if entry.get("read_only") is False]
                    require(record.get("sandbox_id") == sandbox_id and record.get("state") == "started"
                            and len(writable) == 1 and pathkey(writable[0]["host"]) == pathkey(ROOT), "EXACT_CODEX_SANDBOX_MAPPING_REQUIRED")
                    live = identity(daemon["pid"])
                    require(live["creation_time"] == str(daemon["pid_creation_time"])
                            and pathkey(live["executable_path"]) == pathkey(daemon_exe), "EXACT_OWNED_DAEMON_REQUIRED")
                    owned_hosts = {(int(item["pid"]), str(item["creation_time"])) for item in daemon["vm_processes"]}
                    observed_hosts = {(item["pid"], item["creation_time"]) for item in sample["user_mode_hosts"]}
                    if not observed_hosts:
                        time.sleep(0.5)
                        continue
                    require(bool(owned_hosts) and owned_hosts == observed_hosts, "FOREIGN_OR_UNPROVEN_SANDBOX_HOST")
                    warm = {"sandbox_id": sandbox_id, "observed_at_ms": sample["observed_at_ms"], "daemon_process": live,
                            "record_path": str(record_file), "record_sha256": sha(record_file),
                            "mapped_folders_sha256": hashlib.sha256(json.dumps(mappings, sort_keys=True).encode()).hexdigest(),
                            "exact_writable_workspace": str(ROOT), "owned_hosts": sample["user_mode_hosts"], "sample": sample,
                            "daemon_sha256": sha(daemon_exe)}
                    report["warm"] = warm
                    print(json.dumps({"phase": "warm_owned_sandbox_observed", "sandbox_id": sandbox_id,
                                      "observed_at_ms": warm["observed_at_ms"]}), flush=True)
            receipt = terminal_receipt(args.remote_receipt)
            if receipt and warm:
                terminal = receipt["terminal"]
                require(terminal.get("execution_backend") == "isolated" and terminal.get("isolation_level") == "hypervisor"
                        and terminal.get("policy_decision") == "isolated_preferred" and terminal.get("exit_code") == 0,
                        "EXACT_ISOLATED_TERMINAL_PROOF_REQUIRED")
                deadline = min(deadline, time.monotonic() + max(0, (terminal["terminal_observed_at_ms"] + 270000 - int(time.time() * 1000)) / 1000))
                original_daemon_alive = psutil.pid_exists(warm["daemon_process"]["pid"])
                owned_record_absent = not Path(warm["record_path"]).exists()
                sandbox_memory_absent = not any(item["sandbox_named_aggregate"] for item in sample["kernel_memory"])
                settled = not daemon_file.exists() and not sample["user_mode_hosts"] and not original_daemon_alive and owned_record_absent and sandbox_memory_absent
                if settled and receipt["final"] and receipt["final"].get("ok") is True:
                    require(sample["observed_at_ms"] - warm["observed_at_ms"] >= 25000, "IDLE_TEARDOWN_TOO_EARLY_OR_EXTERNAL")
                    report.update(ok=True, after=sample, terminal=terminal, task_cleanup=receipt["final"],
                                  owned_record_absent=True, owned_daemon_absent=True, original_owned_hosts_absent=True,
                                  sandbox_named_memory_aggregate_absent=True,
                                  teardown_observed_at_ms=sample["observed_at_ms"],
                                  terminal_to_teardown_ms=sample["observed_at_ms"] - terminal["terminal_observed_at_ms"],
                                  proof_kind="isolated terminal Job plus automatic owned record/process disappearance with unchanged MCP",
                                  peak_observed_sandbox_working_set_bytes=max((sum(item["working_set_bytes"] for item in row["user_mode_hosts"]
                                      + [item for item in row["kernel_memory"] if item["sandbox_named_aggregate"]]) for row in samples), default=0),
                                  final_sandbox_working_set_bytes=0)
                    break
            if time.monotonic() - last_status >= 45:
                print(json.dumps({"phase": "observing_original_owned_idle", "warm_owner_observed": warm is not None,
                                  "terminal_observed": receipt is not None, "observed_at_ms": int(time.time() * 1000)}), flush=True)
                last_status = time.monotonic()
            time.sleep(0.5)
        require(report["ok"], "AUTOMATIC_IDLE_RETIREMENT_NOT_PROVEN")
    except Exception as error:
        report["error_code"] = str(error) if isinstance(error, RuntimeError) and re.fullmatch(r"[A-Z_]{3,100}", str(error)) else type(error).__name__
    finally:
        report.update(capture_finished_at_ms=int(time.time() * 1000), sample_count=len(samples),
                      samples=samples, limitation="No dedicated idle teardown receipt exists. Kernel aggregates are observations and carry no process ownership authority.")
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2)
            stream.write("\n")
        print(json.dumps({"ok": report["ok"], "report_path": str(args.output), "error_code": report.get("error_code")}), flush=True)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
