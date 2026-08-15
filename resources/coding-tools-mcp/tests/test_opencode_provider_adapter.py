from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.opencode_provider import OpenCodeProviderAdapter, OpenCodeProviderError, READ_ONLY_AGENT


STUB = r'''import json, os, sys, time
prompt = sys.stdin.read()
capture = os.environ.get("OPENCODE_STUB_CAPTURE")
if capture:
    with open(capture, "w", encoding="utf-8") as handle:
        json.dump({"argv": sys.argv[1:], "prompt": prompt, "config": json.loads(os.environ["OPENCODE_CONFIG_CONTENT"]), "dispatch_id": os.environ.get("CODING_TOOLS_MCP_PROVIDER_DISPATCH_ID"), "delegation_id": os.environ.get("CODING_TOOLS_MCP_PROVIDER_DELEGATION_ID")}, handle)
if "TOOLCALL_HANG" in prompt:
    print(json.dumps({"type":"step_start","timestamp":1,"sessionID":"ses-stub","part":{}}), flush=True)
    print(json.dumps({"type":"tool_use","timestamp":2,"sessionID":"ses-stub","part":{"type":"tool","tool":"read","state":{"status":"completed"}}}), flush=True)
    print(json.dumps({"type":"step_finish","timestamp":3,"sessionID":"ses-stub","part":{"reason":"tool-calls"}}), flush=True)
    time.sleep(2)
elif "SLEEP" in prompt:
    time.sleep(2)
print(json.dumps({"type":"text","timestamp":1,"sessionID":"ses-stub","part":{"type":"text","text":"bounded findings","time":{"end":1}}}), flush=True)
if "VIOLATE" in prompt:
    print(json.dumps({"type":"tool_use","timestamp":2,"sessionID":"ses-stub","part":{"type":"tool","tool":"bash","state":{"status":"completed"}}}), flush=True)
'''


class OpenCodeProviderAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.stub = self.root / "stub.py"
        self.stub.write_text(STUB, encoding="utf-8")
        self.capture = self.root / "capture.json"
        self.env = {
            "CODING_TOOLS_MCP_OPENCODE_ARGV": json.dumps([sys.executable, str(self.stub)]),
            "OPENCODE_STUB_CAPTURE": str(self.capture),
        }
        self.adapter = OpenCodeProviderAdapter(lambda: self.root)

    def tearDown(self) -> None:
        self.adapter.close()
        self.temp.cleanup()

    def wait_terminal(self, dispatch_id: str, timeout: float = 3.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            current = self.adapter.observe(dispatch_id)
            if current["status"] != "running":
                return current
            time.sleep(0.02)
        self.fail("provider dispatch did not become terminal")

    def test_prompt_uses_stdin_and_permissions_are_fail_closed(self) -> None:
        private_prompt = "PRIVATE PROMPT SHOULD NOT BE IN ARGV"
        with patch.dict(os.environ, self.env, clear=False):
            started = self.adapter.start(
                run_id="run",
                wave_id="wave",
                model="opencode-go/deepseek-v4-flash",
                prompt=private_prompt,
                timeout_ms=2000,
                request_id="req-1",
            )
            finished = self.wait_terminal(started["dispatch_id"])
        self.assertEqual(finished["status"], "completed")
        self.assertEqual(finished["session_id"], "ses-stub")
        self.assertEqual(finished["result_text"], "bounded findings")
        self.assertEqual(finished["capability_profile"], "opencode_readonly")
        artifact = finished["artifact_ref"]
        self.assertEqual(artifact["kind"], "provider_result")
        self.assertEqual(artifact["locator"], {"dispatch_id": started["dispatch_id"]})
        self.assertEqual(artifact["owner_run"], "run")
        self.assertEqual(artifact["owner_wave"], "wave")
        self.assertNotIn(private_prompt, json.dumps(artifact, ensure_ascii=False))
        captured = json.loads(self.capture.read_text(encoding="utf-8"))
        self.assertEqual(captured["prompt"], private_prompt)
        self.assertNotIn(private_prompt, " ".join(captured["argv"]))
        self.assertIn("run", captured["argv"])
        self.assertIn("--format", captured["argv"])
        self.assertIn("--agent", captured["argv"])
        self.assertIn(READ_ONLY_AGENT, captured["argv"])
        self.assertEqual(captured["dispatch_id"], started["dispatch_id"])
        self.assertEqual(captured["delegation_id"], started["delegation_id"])
        permission = captured["config"]["permission"]
        self.assertEqual(permission["*"], "deny")
        for tool in ("read", "glob", "grep", "list", "lsp"):
            self.assertEqual(permission[tool], "allow")
        agent_permission = captured["config"]["agent"][READ_ONLY_AGENT]["permission"]
        self.assertEqual(agent_permission["*"], "deny")
        self.assertNotIn("bash", {name for name, value in agent_permission.items() if value == "allow"})

    def test_allowlist_dedup_conflict_timeout_cancel_and_policy_detection(self) -> None:
        with patch.dict(os.environ, self.env, clear=False):
            with self.assertRaises(OpenCodeProviderError) as denied:
                self.adapter.start(run_id="run", wave_id="wave", model="other/model", prompt="x")
            self.assertEqual(denied.exception.code, "OPENCODE_MODEL_DENIED")

            first = self.adapter.start(
                run_id="run",
                wave_id="wave",
                model="opencode-go/deepseek-v4-pro",
                prompt="normal",
                request_id="same",
                timeout_ms=2000,
            )
            duplicate = self.adapter.start(
                run_id="run",
                wave_id="wave",
                model="opencode-go/deepseek-v4-pro",
                prompt="normal",
                request_id="same",
                timeout_ms=2000,
            )
            self.assertTrue(duplicate["deduplicated"])
            with self.assertRaises(OpenCodeProviderError) as conflict:
                self.adapter.start(
                    run_id="run",
                    wave_id="wave",
                    model="opencode-go/deepseek-v4-pro",
                    prompt="different",
                    request_id="same",
                    timeout_ms=2000,
                )
            self.assertEqual(conflict.exception.code, "OPENCODE_DISPATCH_CONFLICT")
            self.assertEqual(self.wait_terminal(first["dispatch_id"])["status"], "completed")

            timeout_dispatch = self.adapter.start(
                run_id="run",
                wave_id="wave",
                model="opencode-go/deepseek-v4-flash",
                prompt="SLEEP timeout",
                request_id="timeout",
                timeout_ms=100,
            )
            self.assertEqual(self.wait_terminal(timeout_dispatch["dispatch_id"])["status"], "timed_out")

            toolcall_timeout = self.adapter.start(
                run_id="run",
                wave_id="wave",
                model="opencode-go/deepseek-v4-flash",
                prompt="TOOLCALL_HANG",
                request_id="toolcall-timeout",
                # Give the stub enough startup time under broad-suite load to emit
                # its completed tool-call lifecycle before the intentional hang.
                timeout_ms=500,
            )
            toolcall_result = self.wait_terminal(toolcall_timeout["dispatch_id"])
            self.assertEqual(toolcall_result["status"], "timed_out")
            self.assertEqual(toolcall_result["error_class"], "provider_cli_idle_timeout_after_tool_calls")
            evidence = toolcall_result["lifecycle_evidence"]
            self.assertEqual(evidence["last_step_finish"], "tool-calls")
            self.assertEqual(evidence["last_tool"], "read")
            self.assertEqual(evidence["last_tool_status"], "completed")
            self.assertGreaterEqual(evidence["event_counts"]["step_finish"], 1)

            cancel_dispatch = self.adapter.start(
                run_id="run",
                wave_id="wave",
                model="opencode-go/deepseek-v4-flash",
                prompt="SLEEP cancel",
                request_id="cancel",
                timeout_ms=5000,
            )
            time.sleep(0.05)
            self.adapter.cancel(cancel_dispatch["dispatch_id"])
            self.assertEqual(self.wait_terminal(cancel_dispatch["dispatch_id"])["status"], "cancelled")

            violation = self.adapter.start(
                run_id="run",
                wave_id="wave",
                model="opencode-go/deepseek-v4-flash",
                prompt="VIOLATE",
                request_id="violate",
                timeout_ms=2000,
            )
            violation_result = self.wait_terminal(violation["dispatch_id"])
            self.assertEqual(violation_result["status"], "failed")
            self.assertEqual(violation_result["error_class"], "side_effect_policy_violation")

    def test_terminal_callback_receives_bounded_snapshot(self) -> None:
        callbacks = []
        adapter = OpenCodeProviderAdapter(lambda: self.root, on_terminal=lambda snapshot: callbacks.append(snapshot))
        try:
            with patch.dict(os.environ, self.env, clear=False):
                started = adapter.start(
                    run_id="run-callback",
                    wave_id="wave-callback",
                    model="opencode-go/deepseek-v4-flash",
                    prompt="callback",
                    request_id="callback",
                    timeout_ms=2000,
                )
                deadline = time.time() + 3
                while time.time() < deadline and not callbacks:
                    time.sleep(0.02)
            self.assertTrue(callbacks)
            self.assertEqual(callbacks[0]["dispatch_id"], started["dispatch_id"])
            self.assertEqual(callbacks[0]["status"], "completed")
            self.assertEqual(callbacks[0]["result_text"], "bounded findings")
        finally:
            adapter.close()


if __name__ == "__main__":
    unittest.main()
