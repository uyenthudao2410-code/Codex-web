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
        # Operator decision 2026-10-13 (restored and hardened 2026-10-23): in
        # local mode a destructive command is gated by chat confirmation, not
        # a hard block.  A Boolean assertion is not accepted as evidence: the
        # server issues a single-use token bound to the exact normalized
        # command and current workspace, and redemption consumes it.
        token_shape = "dct_" + "x" * 43
        validate_arguments("exec_command", {"cmd": "git reset --hard", "confirm_destructive_token": token_shape})
        with self.assertRaises(JsonRpcError):
            validate_arguments("exec_command", {"cmd": "git reset --hard", "confirm_destructive": True})
        checks = (
            (self.runtime._check_command_policy, "git reset --hard"),
            (self.runtime._check_structured_argv_policy, ["git", "reset", "--hard"]),
        )
        with patch("coding_tools_mcp.exec_tools.is_sandboxed_execution", return_value=False):
            # A legacy Boolean does not pass the gate.
            with self.assertRaises(ToolFailure) as boolean_denied:
                self.runtime._check_command_policy("git reset --hard", {"confirm_destructive": True})
            self.assertEqual(boolean_denied.exception.code, "DESTRUCTIVE_CONFIRMATION_REQUIRED")

            for check, command in checks:
                with self.assertRaises(ToolFailure) as denied:
                    check(command, {})
                self.assertEqual(denied.exception.code, "DESTRUCTIVE_CONFIRMATION_REQUIRED")
                details = denied.exception.details
                token = details["confirmation_token"]
                self.assertTrue(token.startswith("dct_"))
                self.assertEqual(details["confirmation_arg"], "confirm_destructive_token")
                self.assertEqual(details["command"], "git reset --hard")
                self.assertEqual(
                    details["workspace_root"],
                    str(self.runtime._current_request_workspace_root().resolve(strict=False)),
                )
                self.assertEqual(details["expires_in_seconds"], 300)
                self.assertTrue(details["single_use"])

                # Sandboxed mode cannot redeem the token and does not consume it.
                with patch("coding_tools_mcp.exec_tools.is_sandboxed_execution", return_value=True):
                    with self.assertRaises(ToolFailure) as sandboxed:
                        check(command, {"confirm_destructive_token": token})
                    self.assertEqual(sandboxed.exception.code, "PERMISSION_REQUIRED")

                # The exact retry passes once; replaying the token does not.
                check(command, {"confirm_destructive_token": token})
                with self.assertRaises(ToolFailure) as replayed:
                    check(command, {"confirm_destructive_token": token})
                self.assertEqual(replayed.exception.code, "DESTRUCTIVE_CONFIRMATION_INVALID")

            # A token issued for one command cannot authorize another.
            with self.assertRaises(ToolFailure) as issued:
                self.runtime._check_command_policy("git reset --hard", {})
            reset_token = issued.exception.details["confirmation_token"]
            with self.assertRaises(ToolFailure) as mismatched:
                self.runtime._check_command_policy("git clean -fdx", {"confirm_destructive_token": reset_token})
            self.assertEqual(mismatched.exception.code, "DESTRUCTIVE_CONFIRMATION_INVALID")

            # A token is also bound to the workspace that received the challenge.
            with self.assertRaises(ToolFailure) as issued:
                self.runtime._check_command_policy("git reset --hard", {})
            workspace_token = issued.exception.details["confirmation_token"]
            with patch.object(
                self.runtime,
                "_current_request_workspace_root",
                return_value=self.root / "another-workspace",
            ):
                with self.assertRaises(ToolFailure) as wrong_workspace:
                    self.runtime._check_command_policy(
                        "git reset --hard", {"confirm_destructive_token": workspace_token}
                    )
                self.assertEqual(wrong_workspace.exception.code, "DESTRUCTIVE_CONFIRMATION_INVALID")

            # An expired token is rejected and replaced with a fresh challenge.
            with self.assertRaises(ToolFailure) as issued:
                self.runtime._check_command_policy("git reset --hard", {})
            expired_token = issued.exception.details["confirmation_token"]
            token_key = issued.exception.details["confirmation_token_sha256"]
            self.runtime._destructive_confirmation_tokens[token_key]["expires_at"] = 0
            with self.assertRaises(ToolFailure) as expired:
                self.runtime._check_command_policy(
                    "git reset --hard", {"confirm_destructive_token": expired_token}
                )
            self.assertEqual(expired.exception.code, "DESTRUCTIVE_CONFIRMATION_INVALID")
            self.assertNotEqual(expired.exception.details["confirmation_token"], expired_token)

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
