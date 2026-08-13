from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.server import Runtime


class PrincipalSessionQuotaTests(unittest.TestCase):
    def _spawn_sleeper(self, runtime: Runtime, principal: str) -> dict:
        return runtime.exec_command({
            "cmd": f'"{sys.executable}" sleep_probe.py',
            "yield_time_ms": 0,
            "max_output_bytes": 4096,
            "verbosity": "full",
            "principal_id": principal,
        })

    def test_per_principal_slot_quota_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sleep_probe.py").write_text(
                "import time\ntime.sleep(20)\n", encoding="utf-8"
            )
            runtime = Runtime(root)
            try:
                with patch("coding_tools_mcp.server.PRINCIPAL_MAX_ACTIVE_SESSIONS", 2):
                    first = self._spawn_sleeper(runtime, "chatweb")
                    self.assertEqual(first["status"], "running")
                    second = self._spawn_sleeper(runtime, "chatweb")
                    self.assertEqual(second["status"], "running")
                    with self.assertRaises(ToolFailure) as caught:
                        self._spawn_sleeper(runtime, "chatweb")
                    self.assertEqual(caught.exception.code, "SESSION_LIMIT_REACHED")
                    details = caught.exception.details or {}
                    self.assertEqual(details.get("principal_id"), "chatweb")
                    other = self._spawn_sleeper(runtime, "desktop")
                    self.assertEqual(other["status"], "running")
                    self.assertEqual(runtime.principal_active_counts.get("chatweb"), 2)
                    self.assertEqual(runtime.principal_active_counts.get("desktop"), 1)
            finally:
                runtime.close()

    def test_completed_session_releases_principal_slot(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                with patch("coding_tools_mcp.server.PRINCIPAL_MAX_ACTIVE_SESSIONS", 1):
                    first = runtime.exec_command({
                        "cmd": "echo done",
                        "yield_time_ms": 2000,
                        "max_output_bytes": 4096,
                        "verbosity": "full",
                        "principal_id": "chatweb",
                    })
                    self.assertEqual(first["status"], "exited")
                    self.assertEqual(runtime.principal_active_counts.get("chatweb", 0), 0)
                    second = runtime.exec_command({
                        "cmd": "echo again",
                        "yield_time_ms": 2000,
                        "max_output_bytes": 4096,
                        "verbosity": "full",
                        "principal_id": "chatweb",
                    })
                    self.assertEqual(second["status"], "exited")
            finally:
                runtime.close()


class PrincipalOutputEvictionTests(unittest.TestCase):
    def test_principal_overflow_evicts_only_that_principals_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                session_a = MagicMock()
                session_a.retained_bytes = 100
                session_a.completed_at = 1.0
                session_b = MagicMock()
                session_b.retained_bytes = 10
                session_b.completed_at = 2.0
                runtime.output_sessions = {"a": session_a, "b": session_b}
                runtime.session_principals = {"a": "chatweb", "b": "desktop"}
                with patch(
                    "coding_tools_mcp.server.PRINCIPAL_MAX_RETAINED_OUTPUT_BYTES", 50
                ):
                    with runtime.sessions_lock:
                        runtime._evict_principal_overflow_locked()
                self.assertNotIn("a", runtime.output_sessions)
                self.assertIn("b", runtime.output_sessions)
                self.assertNotIn("a", runtime.session_principals)
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
