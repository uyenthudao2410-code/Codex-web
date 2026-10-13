from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from control_plane.node_agent import (
    CONNECTED_AGENT_STATUS_FILE_NAME,
    run_connected_agent,
)


class ConnectedAgentStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.config_path = Path(self.tempdir.name) / "node.json"
        self.args = SimpleNamespace(
            config=str(self.config_path),
            workspace_registry=str(Path(self.tempdir.name) / "workspaces.json"),
            project_root=self.tempdir.name,
            node="node",
            runtime_mode="development",
            timeout_seconds=20,
            data_root=self.tempdir.name,
            interval_seconds=15,
            max_backoff_seconds=30,
            max_iterations=1,
        )

    def _run_iteration(self, side_effect) -> dict[str, object]:
        output = io.StringIO()
        with mock.patch("control_plane.node_agent._config", return_value={}), \
             mock.patch("control_plane.node_agent._connected_agent_iteration", side_effect=side_effect), \
             redirect_stdout(output):
            self.assertEqual(run_connected_agent(self.args), 0)
        status_path = Path(self.tempdir.name) / CONNECTED_AGENT_STATUS_FILE_NAME
        return json.loads(status_path.read_text(encoding="utf-8"))

    def test_successful_heartbeat_is_distinguished_from_later_poll_failure(self) -> None:
        def fail_during_poll(_args, *, on_heartbeat_success):
            on_heartbeat_success()
            raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT")

        status = self._run_iteration(fail_during_poll)

        self.assertEqual(status["last_iteration_state"], "degraded")
        self.assertEqual(status["last_heartbeat_state"], "succeeded")
        self.assertIsInstance(status["last_heartbeat_at_ms"], int)
        self.assertEqual(status["last_error_scope"], "capability_poll")
        self.assertEqual(status["last_error_code"], "CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT")

    def test_heartbeat_failure_records_only_a_sanitized_code(self) -> None:
        def fail_heartbeat(_args, *, on_heartbeat_success):
            del on_heartbeat_success
            raise RuntimeError("credential=do-not-record")

        status = self._run_iteration(fail_heartbeat)
        serialized = json.dumps(status)

        self.assertEqual(status["last_iteration_state"], "degraded")
        self.assertEqual(status["last_heartbeat_state"], "failed")
        self.assertEqual(status["last_error_scope"], "heartbeat")
        self.assertEqual(status["last_error_code"], "CONTROL_PLANE_BRIDGE_FAILED")
        self.assertNotIn("credential", serialized)
        self.assertNotIn("do-not-record", serialized)

    def test_diagnostic_write_failure_does_not_stop_the_agent_iteration(self) -> None:
        def succeed(_args, *, on_heartbeat_success):
            on_heartbeat_success()
            return []

        output = io.StringIO()
        with mock.patch("control_plane.node_agent._config", return_value={}), \
             mock.patch("control_plane.node_agent._connected_agent_iteration", side_effect=succeed), \
             mock.patch("control_plane.node_agent._write_json_atomic", side_effect=PermissionError("fixture")), \
             redirect_stdout(output):
            self.assertEqual(run_connected_agent(self.args), 0)

        records = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(records[1]["state"], "completed")
        self.assertEqual(records[-1]["execution"], "connected_agent_stopped")
        self.assertFalse((Path(self.tempdir.name) / CONNECTED_AGENT_STATUS_FILE_NAME).exists())


if __name__ == "__main__":
    unittest.main()
