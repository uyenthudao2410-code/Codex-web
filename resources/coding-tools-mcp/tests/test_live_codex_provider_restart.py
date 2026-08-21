from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.codex_bridge import CodexAppServerBridge, CodexBridgeError

STUB_PATH = str(Path(__file__).resolve().parent / "support" / "codex_app_server_stub.py")


class LiveCodexProviderRestartTests(unittest.TestCase):
    def _bridge_env(self, state_file: Path, control_file: Path) -> dict[str, str]:
        env = dict(os.environ)
        # The bridge deliberately validates that a Codex binary exists before
        # consulting the test-only argv override. Use the current Python
        # executable as that portable probe so this live stub does not depend
        # on Codex Desktop/CLI being installed on the CI host.
        env["CODING_TOOLS_MCP_CODEX_BIN"] = sys.executable
        env["CODING_TOOLS_MCP_CODEX_ARGV"] = json.dumps([
            sys.executable,
            STUB_PATH,
            "--state-file",
            str(state_file),
            "--control-file",
            str(control_file),
            "--turn-complete-delay-s",
            "0.2",
        ])
        return env

    def test_provider_crash_mid_turn_and_restart_resumes_same_thread(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_file = root / "stub-state.json"
            control_file = root / "stub-control.json"
            control_file.write_text(json.dumps({"crash_after_turn_start": True}), encoding="utf-8")
            with patch.dict(os.environ, self._bridge_env(state_file, control_file)):
                first = CodexAppServerBridge(lambda: root)
                try:
                    outcome = None
                    try:
                        outcome = first.run(
                            "review the fixture",
                            profile="packet",
                            wait_ms=1_000,
                        )
                    except CodexBridgeError as exc:
                        outcome = {"crash_error": exc.code, "thread_id": None}
                finally:
                    first.close()

            state = json.loads(state_file.read_text(encoding="utf-8"))
            threads = state.get("threads", {})
            self.assertEqual(len(threads), 1)
            thread_id = next(iter(threads))
            session_id = threads[thread_id]["sessionId"]
            turns_after_crash = state.get("turns", {})
            self.assertFalse(
                any(turn.get("thread_id") == thread_id and turn.get("completed") for turn in turns_after_crash.values()),
                "turn must not complete on the crashed provider",
            )
            if outcome and outcome.get("thread_id"):
                self.assertEqual(outcome["thread_id"], thread_id)
            control = json.loads(control_file.read_text(encoding="utf-8"))
            self.assertFalse(control.get("crash_after_turn_start"), "crash injection must be one-shot")

            with patch.dict(os.environ, self._bridge_env(state_file, control_file)):
                restored = CodexAppServerBridge(lambda: root)
                try:
                    resumed = restored.resume_persistent_thread(
                        thread_id=thread_id,
                        expected_session_id=session_id,
                        prompt="continue after provider restart",
                        profile="packet",
                        model="gpt-5.4-mini",
                        effort="low",
                        wait_ms=4_000,
                    )
                    observation = resumed.get("observation") or {}
                    self.assertTrue(observation.get("terminal"))
                    self.assertEqual(observation.get("status"), "completed")
                    self.assertIn("provider-restart-proof", observation.get("agent_text", ""))
                finally:
                    restored.close()

            state_after = json.loads(state_file.read_text(encoding="utf-8"))
            servers = state_after.get("servers", [])
            self.assertGreaterEqual(len(servers), 2)
            self.assertNotEqual(servers[0], servers[1])
            turns = state_after.get("turns", {})
            self.assertEqual(len(turns), 2)
            thread_ids = {turn["thread_id"] for turn in turns.values()}
            self.assertEqual(thread_ids, {thread_id})


if __name__ == "__main__":
    unittest.main()
