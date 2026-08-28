from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.server import Runtime


class ActivationRestartEscapeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(
            os.environ,
            {
                "CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID": "epoch-restart-escape-001",
                "CODING_TOOLS_MCP_ACTIVATION_GATE": "closed",
                "CODING_TOOLS_MCP_ACTIVATION_EXPIRES_AT_UNIX_MS": "4000000000000",
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
            },
        )
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()
        self.temp.cleanup()

    def test_only_explicitly_confirmed_controlled_restart_crosses_closed_startup_admission(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            runtime._activation_enter_tool_call(
                "task_control",
                {"action": "restart_runtime", "confirm_restart": True},
            )
            self.assertEqual(runtime.active_tool_calls, 1)
            runtime._activation_leave_tool_call()
            self.assertEqual(runtime.active_tool_calls, 0)

            for args in (
                {"action": "restart_runtime", "confirm_restart": False},
                {"action": "get"},
            ):
                with self.assertRaises(ToolFailure) as blocked:
                    runtime._activation_enter_tool_call("task_control", args)
                self.assertEqual(blocked.exception.code, "RUNTIME_ACTIVATION_PENDING")
                self.assertEqual(runtime.active_tool_calls, 0)
        finally:
            runtime.close()


if __name__ == "__main__":
    unittest.main()
