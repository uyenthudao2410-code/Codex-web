from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.server import Runtime


class ExecSpawnFailureTests(unittest.TestCase):
    def _run_failure(self, *, lookup_unavailable=False):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Path(directory), permission_mode="dangerous")
            runtime.request_context.hub_client = {
                "client_id": "electron-control-plane-exec-bridge",
                "client_type": "electron", "attestation_verified": True,
            }
            failure = ToolFailure("SANDBOX_STATE_PHASE_FAILED", "Lifecycle failed.",
                retryable=True, details={"phase": "start", "backend_error_code": "backend_error"})
            try:
                with (
                    patch("coding_tools_mcp.exec_tools.os.name", "nt"),
                    patch("coding_tools_mcp.exec_tools.is_sandboxed_execution", return_value=True),
                    patch("coding_tools_mcp.exec_tools.windows_sandbox_feature_enabled", return_value=True),
                    patch("coding_tools_mcp.exec_tools.build_mxc_windows_sandbox_invocation", side_effect=failure),
                    patch("coding_tools_mcp.exec_tools.spawn_process") as spawn,
                ):
                    if lookup_unavailable:
                        with patch.object(runtime.execution_resource_governor, "find_exact_job", side_effect=OSError("unavailable")):
                            with self.assertRaises(ToolFailure) as observed:
                                runtime.exec_command({"cmd": "node", "argv": ["node", "--version"], "_windows_execution_mode": "isolated"})
                    else:
                        with self.assertRaises(ToolFailure) as observed:
                            runtime.exec_command({"cmd": "node", "argv": ["node", "--version"], "_windows_execution_mode": "isolated"})
                spawn.assert_not_called()
                self.assertIs(observed.exception, failure)
                rows = runtime.execution_resource_governor._rows()
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["lifecycle_state"], "spawn_failed")
                self.assertEqual(runtime.starting_sessions, 0)
                return failure, rows[0]
            finally:
                runtime.close()

    def test_no_process_failure_has_exact_durable_terminal_evidence(self):
        failure, row = self._run_failure()
        self.assertFalse(failure.retryable)
        self.assertEqual(failure.details["job_id"], row["job_id"])
        self.assertEqual(failure.details["command_id"], row["command_id"])
        self.assertEqual(failure.details["job_lifecycle"], "spawn_failed")
        self.assertEqual(failure.details["root_pid"], 0)
        self.assertIs(failure.details["execution_started"], False)
        self.assertEqual(failure.details["job_finished_at"], row["finished_at"])
        self.assertEqual(failure.details["phase"], "start")
        self.assertEqual(failure.details["backend_error_code"], "backend_error")

    def test_unavailable_job_proof_preserves_unknown_without_invented_fields(self):
        failure, _ = self._run_failure(lookup_unavailable=True)
        self.assertTrue(failure.retryable)
        self.assertNotIn("execution_started", failure.details)
        self.assertNotIn("job_id", failure.details)

    def test_spawn_function_exception_cannot_claim_no_process_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Path(directory), permission_mode="dangerous")
            failure = ToolFailure("PROCESS_BIND_FAILED", "Uncertain process creation.", retryable=True)
            try:
                with patch("coding_tools_mcp.exec_tools.spawn_process", side_effect=failure):
                    with self.assertRaises(ToolFailure):
                        runtime.exec_command({"cmd": "echo test"})
                self.assertTrue(failure.retryable)
                self.assertNotIn("execution_started", failure.details)
                self.assertNotIn("job_id", failure.details)
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
