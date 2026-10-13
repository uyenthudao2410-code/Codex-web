"""Run the bounded WinAPI child probe through the source native adapter only.

This fixture uses a temporary workspace and an attested bridge identity. It does
not contact the production MCP, mutate persisted policy, start a VM, or change
the repository runtime. The command's durable Job/receipt facts are retained in
the JSON report for review before any live packaged dispatch.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "resources" / "coding-tools-mcp"
REPORT_DIR = Path(__file__).resolve().parent
LAUNCHER = REPORT_DIR / "token-child-launcher.js"
sys.path.insert(0, str(SOURCE))
from coding_tools_mcp.server import Runtime  # noqa: E402


def run() -> dict:
    started = datetime.now(timezone.utc).isoformat()
    head = __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    with tempfile.TemporaryDirectory(prefix="codex-token-native-fixture-", dir=str(Path(__file__).anchor)) as directory:
        workspace = Path(directory)
        fixture_dir = workspace / "token-probe"
        fixture_dir.mkdir()
        # ProcessContainer grants only the temporary workspace root. Keep both
        # the launcher and direct child inside that root; referencing the
        # repository evidence path would correctly be denied by the file fence.
        fixture_launcher = fixture_dir / LAUNCHER.name
        fixture_binary = fixture_dir / "token-child-probe.exe"
        shutil.copyfile(LAUNCHER, fixture_launcher)
        shutil.copyfile(REPORT_DIR / "token-child-probe.exe", fixture_binary)
        runtime = Runtime(workspace)
        runtime.request_context.hub_client = {
            "client_id": "electron-control-plane-exec-bridge",
            "client_type": "electron",
            "attestation_verified": True,
        }
        vm_calls = 0
        try:
            argv = ["node", str(fixture_launcher)]
            with patch(
                "coding_tools_mcp.exec_tools.build_mxc_windows_sandbox_invocation",
                side_effect=AssertionError("VM adapter forbidden in token fixture"),
            ) as vm:
                result = runtime.exec_command({
                    "cmd": "node",
                    "argv": argv,
                    "_windows_execution_mode": "native_only",
                    "_windows_native_argv_prefixes": [argv],
                    "yield_time_ms": 30_000,
                    "max_output_bytes": 65_536,
                    "verbosity": "full",
                })
                while result.get("status") == "running":
                    result = runtime.command_control({
                        "action": "poll",
                        "command_id": result["command_id"],
                        "yield_time_ms": 1_000,
                        "verbosity": "full",
                    })
                vm_calls = vm.call_count
            launcher_report = None
            try:
                launcher_report = json.loads(str(result.get("stdout") or "").strip())
            except (TypeError, ValueError, json.JSONDecodeError):
                launcher_report = None
            facts = launcher_report.get("child_facts") if isinstance(launcher_report, dict) else None
            receipt = {
                key: result.get(key)
                for key in (
                    "command_id", "job_id", "status", "durable_lifecycle_state", "exit_code",
                    "execution_backend", "isolation_level", "policy_decision",
                )
            }
            owner = result.get("execution_owner") if isinstance(result.get("execution_owner"), dict) else {}
            receipt["job_id"] = owner.get("job_id")
            receipt["owner_run_id"] = owner.get("run_id")
            receipt["owner_wave_id"] = owner.get("wave_id")
            durable_job = runtime.execution_resource_governor.find_exact_job(
                command_id=str(result.get("command_id") or ""),
                job_id=str(owner.get("job_id") or ""),
            )
            receipt["durable_lifecycle_state"] = durable_job.get("lifecycle_state") if isinstance(durable_job, dict) else None
            receipt.update({
                "stderr_empty": not bool(result.get("stderr")),
                "stderr_sha256": hashlib.sha256(str(result.get("stderr") or "").encode()).hexdigest(),
                "vm_adapter_calls": vm_calls,
            })
            return {
                "schema_version": 1,
                "operation": "native_child_token_source_fixture",
                "ok": bool(result.get("exit_code") == 0 and isinstance(facts, dict) and facts.get("complete") is True),
                "observed_git_head": head,
                "capture_started_utc": started,
                "capture_finished_utc": datetime.now(timezone.utc).isoformat(),
                "scope": "source Runtime native-only temporary workspace; no production MCP/service/policy mutation",
                "argv": argv,
                "receipt": receipt,
                "durable_job": durable_job,
                "launcher_report": launcher_report,
                "child_facts": facts,
                "production_native_claim": False,
            }
        finally:
            runtime.close()


if __name__ == "__main__":
    report = run()
    output = REPORT_DIR / f"token-child-native-fixture-{int(time.time() * 1000)}.json"
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
