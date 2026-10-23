from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import JsonRpcError, ToolFailure
from coding_tools_mcp.processes import WindowsJobLimits, spawn_process
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.tool_schema import validate_arguments


@unittest.skipUnless(os.name == "nt", "Windows host-user execution")
class WindowsLocalExecutionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="local-exec-proof-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.runtime = Runtime(self.root)
        self.addCleanup(self.runtime.close)
        self.runtime.request_context.hub_client = {
            "client_id": "electron-control-plane-exec-bridge",
            "client_type": "electron", "attestation_verified": True,
        }
        # Select the branch without changing process-global environment.
        mode = patch("coding_tools_mcp.exec_tools.is_sandboxed_execution", return_value=False)
        mode.start()
        self.addCleanup(mode.stop)

    def _script(self, content):
        (self.root / "probe.py").write_text(content, encoding="utf-8")
        return {
            "cmd": sys.executable, "argv": [sys.executable, "probe.py"],
            "yield_time_ms": 1000, "verbosity": "full",
        }

    def _assert_local_job(self, result):
        self.assertEqual(result["execution_backend"], "local")
        self.assertEqual(result["isolation_level"], "host_user")
        self.assertEqual(result["policy_decision"], "operator_local")
        job = self.runtime.execution_resource_governor.find_exact_job(command_id=result["command_id"])
        self.assertEqual(job["job_id"], result["execution_owner"]["job_id"])
        recorded = next(row for row in self.runtime.execution_resource_governor._rows() if row["job_id"] == job["job_id"])
        self.assertEqual(recorded["metadata"]["execution_backend"], "local")
        return job

    def test_direct_structured_command_keeps_backend_job_and_limits(self):
        arguments = self._script("print('LOCAL_MODE_OK')\n")
        with (
            patch("coding_tools_mcp.exec_tools.decide_windows_execution") as router,
            patch("coding_tools_mcp.exec_tools.build_mxc_invocation") as container,
            patch("coding_tools_mcp.exec_tools.build_mxc_windows_sandbox_invocation") as vm,
            patch("coding_tools_mcp.exec_tools.spawn_process", wraps=spawn_process) as spawn,
        ):
            result = self.runtime.exec_command(arguments)
        self.assertEqual(result["status"], "exited", result)
        self.assertEqual(result["exit_code"], 0, result)
        self.assertIn("LOCAL_MODE_OK", result["stdout"])
        self.assertEqual(self._assert_local_job(result)["lifecycle_state"], "exited")
        router.assert_not_called()
        container.assert_not_called()
        vm.assert_not_called()
        self.assertEqual(spawn.call_args.args[0], arguments["argv"])
        self.assertFalse(spawn.call_args.kwargs["shell"])
        self.assertEqual(spawn.call_args.kwargs["windows_job_limits"], WindowsJobLimits(cpu_time_ms=30_000))
        observed = self.runtime.command_control({"action": "poll", "command_id": result["command_id"], "yield_time_ms": 0})
        self._assert_local_job(observed)

    def test_direct_shell_command_reports_host_user_backend(self):
        result = self.runtime.exec_command({"cmd": "echo LOCAL_SHELL_OK", "yield_time_ms": 1000, "verbosity": "full"})
        self.assertEqual(result["exit_code"], 0, result)
        self.assertIn("LOCAL_SHELL_OK", result["stdout"])
        self._assert_local_job(result)

    def test_local_timeout_keeps_terminal_job(self):
        arguments = self._script("import time\ntime.sleep(30)\n")
        result = self.runtime.exec_command({**arguments, "timeout_ms": 150})
        self.assertTrue(result["timed_out"], result)
        self.assertNotEqual(result["status"], "running", result)
        self.assertEqual(self._assert_local_job(result)["lifecycle_state"], "timeout")

    def test_local_cancellation_settles_same_job(self):
        arguments = self._script("import time\ntime.sleep(30)\n")
        started = self.runtime.exec_command({**arguments, "yield_time_ms": 0})
        self.assertEqual(started["status"], "running")
        self._assert_local_job(started)
        stopped = self.runtime.command_control({"action": "kill", "command_id": started["command_id"], "wait_ms": 1000})
        self.assertTrue(stopped["killed"], stopped)
        self.assertEqual(stopped["command_id"], started["command_id"])
        self.assertNotEqual(self._assert_local_job(stopped)["lifecycle_state"], "running")
        self.assertNotIn(started["command_id"], self.runtime.sessions)

    def test_destructive_command_requires_chat_confirmation_in_local_mode(self):
        # Operator decision 2026-10-13 (restored 2026-10-23): in local mode a
        # destructive command is gated by chat confirmation, not a hard block.
        # The schema accepts the confirmation flag...
        validate_arguments("exec_command", {"cmd": "git reset --hard", "confirm_destructive": True})
        checks = (
            (self.runtime._check_command_policy, "git reset --hard"),
            (self.runtime._check_structured_argv_policy, ["git", "reset", "--hard"]),
        )
        # ...local mode: no flag -> DESTRUCTIVE_CONFIRMATION_REQUIRED; with the
        # flag (after the user confirmed in chat) -> the gate passes.
        with patch("coding_tools_mcp.exec_tools.is_sandboxed_execution", return_value=False):
            for check, command in checks:
                with self.assertRaises(ToolFailure) as denied:
                    check(command, {})
                self.assertEqual(denied.exception.code, "DESTRUCTIVE_CONFIRMATION_REQUIRED")
                check(command, {"confirm_destructive": True})
        # ...sandboxed mode: the flag is NOT a shortcut; the hard block stays.
        with patch("coding_tools_mcp.exec_tools.is_sandboxed_execution", return_value=True):
            for check, command in checks:
                with self.assertRaises(ToolFailure) as denied:
                    check(command, {"confirm_destructive": True})
                self.assertEqual(denied.exception.code, "PERMISSION_REQUIRED")

    def test_explicit_sandboxed_native_failure_never_uses_host(self):
        failure = ToolFailure("SANDBOX_UNAVAILABLE", "fixture unavailable", category="security")
        with (
            patch("coding_tools_mcp.exec_tools.is_sandboxed_execution", return_value=True),
            patch("coding_tools_mcp.exec_tools.build_mxc_invocation", side_effect=failure) as native,
            patch("coding_tools_mcp.exec_tools.build_mxc_windows_sandbox_invocation") as vm,
            patch("coding_tools_mcp.exec_tools.spawn_process") as spawn,
        ):
            with self.assertRaises(ToolFailure) as denied:
                self.runtime.exec_command({"cmd": "node", "argv": ["node", "--version"], "_windows_execution_mode": "native_only"})
        self.assertIs(denied.exception, failure)
        native.assert_called_once()
        vm.assert_not_called()
        spawn.assert_not_called()
        self.assertEqual(self.runtime.starting_sessions, 0)

    def test_explicit_sandboxed_native_only_denies_unapproved_build(self):
        with (
            patch("coding_tools_mcp.exec_tools.is_sandboxed_execution", return_value=True),
            patch("coding_tools_mcp.exec_tools.build_mxc_invocation") as native,
            patch("coding_tools_mcp.exec_tools.build_mxc_windows_sandbox_invocation") as vm,
            patch("coding_tools_mcp.exec_tools.spawn_process") as spawn,
        ):
            with self.assertRaises(ToolFailure) as denied:
                self.runtime.exec_command({"cmd": "node", "argv": ["node", "build.js"], "_windows_execution_mode": "native_only"})
        self.assertEqual(denied.exception.code, "NATIVE_EXECUTION_NOT_APPROVED")
        native.assert_not_called()
        vm.assert_not_called()
        spawn.assert_not_called()

    def test_explicit_sandboxed_isolated_failure_never_uses_host(self):
        failure = ToolFailure("SANDBOX_STATE_PHASE_FAILED", "fixture unavailable", category="security")
        with (
            patch("coding_tools_mcp.exec_tools.is_sandboxed_execution", return_value=True),
            patch("coding_tools_mcp.exec_tools.windows_sandbox_feature_enabled", return_value=True),
            patch("coding_tools_mcp.exec_tools.build_mxc_invocation") as native,
            patch("coding_tools_mcp.exec_tools.build_mxc_windows_sandbox_invocation", side_effect=failure) as vm,
            patch("coding_tools_mcp.exec_tools.spawn_process") as spawn,
        ):
            with self.assertRaises(ToolFailure) as denied:
                self.runtime.exec_command({"cmd": "node", "argv": ["node", "--version"], "_windows_execution_mode": "isolated"})
        self.assertIs(denied.exception, failure)
        native.assert_not_called()
        vm.assert_called_once()
        spawn.assert_not_called()


if __name__ == "__main__":
    unittest.main()
