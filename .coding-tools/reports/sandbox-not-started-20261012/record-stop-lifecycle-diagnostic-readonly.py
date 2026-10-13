"""Record bounded, content-free original stop diagnostics; no WSB invocation."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "owned-sandbox-stop-proof.py"
spec = importlib.util.spec_from_file_location("readonly_stop_diagnostic_helpers", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
plan_path = HERE / "owned-stop-plan-b18bb16d623240db9d014361770302db.json"
plan = m.read_json(plan_path)
backend = plan["binding"]["backend"]
record_path = Path(backend["record_path"])
record = m.read_json(record_path)
log_path = record_path.parent / "daemon.log"
log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() and log_path.stat().st_size <= 262144 else ""
script = "@(Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'WindowsSandbox*' -or $_.Name -in @('vmmemWindowsSandbox','vmmemWindowsSandbox.exe') } | Select-Object Name,ProcessId,ParentProcessId) | ConvertTo-Json -Compress"
observed = subprocess.run(["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=8,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
m.require(observed.returncode == 0 and len(observed.stdout) <= 8192, "DIAGNOSTIC_INVENTORY_FAILED")
rows = json.loads(observed.stdout) if observed.stdout.strip() else []
if isinstance(rows, dict): rows = [rows]
for row in rows:
    row["ownership_inferred"] = False
    if row["Name"].lower().startswith("windowssandbox"):
        row["live_identity"] = m.process_identity(int(row["ProcessId"]))
receipt = {"schema_version": 1, "operation": "original_supported_stop_lifecycle_readonly_diagnostic",
           "observed_at_ms": int(time.time() * 1000), "original_stop_attempt_id": plan["binding"]["stop_attempt_id"],
           "original_plan_sha256": m.file_sha(plan_path), "original_stop_outcome_preserved": "UNKNOWN",
           "record": {"sandbox_id": record["sandbox_id"], "state": record["state"],
                      "mapped_folders_match_original": m.digest(record["mapped_folders"]) == backend["mapped_folders_sha256"],
                      "record_sha256": m.file_sha(record_path),
                      "daemon_record_absent": not (record_path.parent.parent / "daemon.json").exists()},
           "daemon_log_content_free": {"raw_log_saved": False,
                                       "teardown_targets_marker_present": "[wsb-vm] tearing down sandbox" in log,
                                       "host_exit_confirmed_marker_present": "[wsb-vm] all sandbox host processes confirmed gone" in log,
                                       "daemon_log_sha256": m.file_sha(log_path) if log_path.exists() else None,
                                       "log_mtime_ms": int(log_path.stat().st_mtime * 1000) if log_path.exists() else None},
           "host_inventory": rows,
           "earlier_kernel_observation": {"at_utc": "2026-10-12 06:10:52", "name": "vmmemWindowsSandbox", "pid": 28056,
                                          "parent_pid": 16828, "parent_name": "vmmemCmZygote", "ownership_inferred": False},
           "hcsdiag_list": "InsufficientPrivileges; no lifecycle effect requested",
           "diagnostic_wsb_list": {"invocations": 1, "documented_purpose": "list running sandbox environments",
                                   "reported_environment_count": 0,
                                   "child_pid_captured": False,
                                   "possible_effect": "WindowsSandboxServer PID27568 appeared after invocation",
                                   "attribution": "temporal correlation only; exact ownership unproven",
                                   "security_4688_window_utc": ["06:12:30", "06:13:10"], "security_4688_result": "NoMatchingEventsFound",
                                   "further_wsb_cli_invocations_permitted": False},
           "os_switch_deletion": {"at_utc": "2026-10-12 06:12:03.993785", "provider": "Microsoft-Windows-Hyper-V-VmSwitch",
                                  "event_id": 71, "port": "9D57A594-7A68-4F54-86C3-587B43160727", "result": "Delete complete"},
           "pinned_contract": {"source_commit": "cbe1774364ea2ec846f56ab744e43a416f751420",
                               "reference": "https://raw.githubusercontent.com/microsoft/mxc/cbe1774364ea2ec846f56ab744e43a416f751420/docs/windows-sandbox/windows-sandbox-reference.md",
                               "implementation": "https://raw.githubusercontent.com/microsoft/mxc/cbe1774364ea2ec846f56ab744e43a416f751420/src/backends/windows_sandbox/lifecycle/src/vm.rs",
                               "ownership_probe": "WindowsSandbox process prefix only",
                               "kernel_memory_processes": "not ownership targets; do not block launch after WindowsSandbox hosts exit",
                               "cooldown_seconds": 5},
           "runtime_adapter": {"cached_exact_workspace_path": "supported start of same sandbox ID before argv; no host-count precheck",
                               "cold_path_guard": "counts WindowsSandbox hosts plus vmmemWindowsSandbox"},
           "stop_replayed": False, "processes_terminated": False, "services_restarted": False,
           "database_mutated": False, "node_journal_modified": False, "nonce_saved": False}
saved = m.write_new(HERE / ("original-stop-lifecycle-readonly-diagnostic-" + str(receipt["observed_at_ms"]) + ".json"), receipt)
print(json.dumps({"ok": True, **saved, "host_process_count": len(rows), "original_stop_replayed": False}))
