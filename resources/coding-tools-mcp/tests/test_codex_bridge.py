from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.codex_bridge import (
    CodexAppServerBridge,
    CodexBridgeError,
    _is_within_workspace,
    _mcp_disable_args,
    configured_mcp_server_names,
    discover_codex_binary,
    sanitized_codex_env,
    _usage_economics,
)


class CodexBridgeTests(unittest.TestCase):
    def test_explicit_codex_binary_wins_without_path_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            binary = Path(temp) / "codex.exe"
            binary.write_bytes(b"stub")
            found = discover_codex_binary(
                {"CODING_TOOLS_MCP_CODEX_BIN": str(binary)},
                which=lambda _name: None,
            )
            self.assertEqual(found, binary.resolve())

    def test_desktop_cache_binary_is_discovered_from_localappdata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            binary = Path(temp) / "OpenAI" / "Codex" / "bin" / "build-a" / "codex.exe"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"stub")
            found = discover_codex_binary({"LOCALAPPDATA": temp}, which=lambda _name: None)
            self.assertEqual(found, binary.resolve())

    def test_workspace_filter_rejects_sibling_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "repo"
            workspace.mkdir()
            child = workspace / "src"
            child.mkdir()
            sibling = root / "other"
            sibling.mkdir()
            self.assertTrue(_is_within_workspace(child, workspace))
            self.assertFalse(_is_within_workspace(sibling, workspace))

    def test_codex_child_env_drops_bridge_credentials_only(self) -> None:
        cleaned = sanitized_codex_env({
            "PATH": "keep",
            "OPENAI_API_KEY": "provider-auth",
            "CODING_TOOLS_MCP_AUTH_TOKEN": "drop-me",
            "CODING_TOOLS_MCP_TOOL_MODE": "smart",
            "WEBCODEX_TOKEN": "drop-me-too",
        })
        self.assertEqual(cleaned["PATH"], "keep")
        self.assertEqual(cleaned["OPENAI_API_KEY"], "provider-auth")
        self.assertNotIn("CODING_TOOLS_MCP_AUTH_TOKEN", cleaned)
        self.assertNotIn("CODING_TOOLS_MCP_TOOL_MODE", cleaned)
        self.assertNotIn("WEBCODEX_TOKEN", cleaned)

    def test_configured_mcp_servers_are_discovered_and_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            (home / "config.toml").write_text(
                '[mcp_servers.alpha]\ncommand = "one"\n\n[mcp_servers.beta-two]\ncommand = "two"\n',
                encoding="utf-8",
            )
            names = configured_mcp_server_names(home)
            self.assertEqual(names, ["alpha", "beta-two"])
            self.assertEqual(
                _mcp_disable_args(names),
                [
                    "-c", "mcp_servers.alpha.enabled=false",
                    "-c", "mcp_servers.beta-two.enabled=false",
                ],
            )

    def test_ephemeral_fork_omits_defer_goal_continuation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bridge = CodexAppServerBridge(lambda: root)
            calls = []
            bridge._ensure_connected = lambda: None

            def fake_request(method, params):
                calls.append((method, dict(params)))
                if method == "thread/read":
                    return {"thread": {"cwd": str(root)}}
                if method == "thread/fork":
                    return {"thread": {"id": "forked-thread"}}
                if method == "turn/start":
                    return {"turn": {"id": "turn-1", "status": "inProgress"}}
                raise AssertionError(method)

            bridge._request = fake_request
            result = bridge.run("review", source_thread_id="source-thread")
            self.assertEqual(result["creation_mode"], "fork")
            fork_params = next(params for method, params in calls if method == "thread/fork")
            self.assertTrue(fork_params["ephemeral"])
            self.assertNotIn("deferGoalContinuation", fork_params)

    def test_packet_profile_overrides_desktop_ultra_and_disables_agentic_features(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bridge = CodexAppServerBridge(lambda: root)
            bridge._ensure_connected = lambda: None
            calls = []
            def fake_request(method, params):
                calls.append((method, dict(params)))
                if method == "thread/start":
                    return {"thread": {"id": "packet-thread", "model": "gpt-5.4-mini", "reasoningEffort": "low"}}
                if method == "turn/start":
                    return {"turn": {"id": "packet-turn", "status": "inProgress"}}
                raise AssertionError(method)
            bridge._request = fake_request
            result = bridge.run("review packet", profile="packet")
            thread_params = next(params for method, params in calls if method == "thread/start")
            turn_params = next(params for method, params in calls if method == "turn/start")
            self.assertEqual(result["route"]["model"], "gpt-5.4-mini")
            self.assertEqual(thread_params["config"]["model_reasoning_effort"], "low")
            self.assertFalse(thread_params["config"]["features"]["shell_tool"])
            self.assertFalse(thread_params["config"]["features"]["multi_agent"])
            self.assertEqual(turn_params["model"], "gpt-5.4-mini")
            self.assertEqual(turn_params["effort"], "low")

    def test_execution_profiles_encode_final_routing_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            bridge = CodexAppServerBridge(lambda: Path(temp))
            expected = {
                "candidate_mini": ("gpt-5.4-mini", "low", False, False),
                "candidate_luna": ("gpt-5.6-luna", "high", False, False),
                "cross_file": ("gpt-5.6-terra", "high", True, False),
                "deep_code": ("gpt-5.6-sol", "xhigh", True, False),
                "consequential": ("gpt-5.6-sol", "max", True, False),
                "parallel_extreme": ("gpt-5.6-sol", "ultra", True, True),
            }
            for profile, (model, effort, shell_tool, multi_agent) in expected.items():
                route = bridge._resolve_route(
                    profile=profile,
                    model=None,
                    effort=None,
                    source_thread_id=None,
                )
                self.assertEqual(route["model"], model)
                self.assertEqual(route["effort"], effort)
                self.assertEqual(route["features"]["shell_tool"], shell_tool)
                self.assertEqual(route["features"]["multi_agent"], multi_agent)
    def test_continue_reuses_only_bridge_owned_thread_and_preserves_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bridge = CodexAppServerBridge(lambda: root)
            bridge._ensure_connected = lambda: None
            bridge._owned_threads["owned"] = {"workspace": str(root), "profile": "packet", "model": "gpt-5.4-mini", "effort": "low"}
            bridge._latest_turn_by_thread["owned"] = "old-turn"
            bridge._turn_states["old-turn"] = {"thread_id": "owned", "status": "completed"}
            calls = []
            def fake_request(method, params):
                calls.append((method, dict(params)))
                if method == "turn/start":
                    return {"turn": {"id": "follow-turn", "status": "inProgress"}}
                raise AssertionError(method)
            bridge._request = fake_request
            result = bridge.continue_thread(thread_id="owned", prompt="follow up")
            self.assertEqual(result["creation_mode"], "continue")
            params = next(params for method, params in calls if method == "turn/start")
            self.assertEqual(params["model"], "gpt-5.4-mini")
            self.assertEqual(params["effort"], "low")
            with self.assertRaises(CodexBridgeError) as raised:
                bridge.continue_thread(thread_id="desktop-thread", prompt="no")
            self.assertEqual(raised.exception.code, "THREAD_NOT_OWNED")

    def test_capacity_error_opens_model_circuit_breaker(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            bridge = CodexAppServerBridge(lambda: Path(temp))
            bridge._turn_states["turn"] = {
                "thread_id": "owned", "status": "failed", "model": "gpt-5.6-terra", "profile": "critical", "effort": "medium",
                "started_monotonic": 0.0, "error": {"message": "Selected model is at capacity. Please try a different model.", "codexErrorInfo": "serverOverloaded"}, "finalized": False,
            }
            bridge._finalize_turn("turn")
            with self.assertRaises(CodexBridgeError) as raised:
                bridge._check_capacity("gpt-5.6-terra")
            self.assertEqual(raised.exception.code, "MODEL_CAPACITY_COOLDOWN")
            self.assertTrue(bridge._capacity_status())

    def test_deadline_interrupt_race_reobserves_terminal_turn(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bridge = CodexAppServerBridge(lambda: root)
            bridge._ensure_connected = lambda: None
            def fake_request(method, params):
                if method == "thread/start":
                    return {"thread": {"id": "deadline-thread"}}
                if method == "turn/start":
                    return {"turn": {"id": "deadline-turn", "status": "inProgress"}}
                raise AssertionError(method)
            bridge._request = fake_request
            observations = [
                {"terminal": False, "status": "inProgress", "next_cursor": 1},
                {"terminal": False, "status": "inProgress", "next_cursor": 2},
            ]
            bridge.observe = lambda **_kwargs: observations.pop(0)
            def raced_interrupt(**_kwargs):
                raise CodexBridgeError("APP_SERVER_ERROR", "no active turn to interrupt")
            bridge.interrupt = raced_interrupt
            result = bridge.run("review", profile="packet", deadline_ms=1)
            self.assertTrue(result["deadline_hit"])
            self.assertEqual(result["status"], "deadline")
            self.assertTrue(result["observation"]["terminal"])
            self.assertEqual(result["observation"]["deadline_resolution"], "app_server_reports_no_active_turn")

    def test_credit_estimate_uses_uncached_cached_and_output_rates(self) -> None:
        economics = _usage_economics({"last": {"inputTokens": 10_000, "cachedInputTokens": 8_000, "outputTokens": 100, "reasoningOutputTokens": 50}}, "gpt-5.6-luna")
        self.assertIsNotNone(economics)
        self.assertEqual(economics["uncached_input_tokens"], 2_000)
        self.assertEqual(economics["cached_input_tokens"], 8_000)
        self.assertAlmostEqual(economics["estimated_credits"], 0.085, places=6)

    def test_invalid_action_fails_without_starting_codex(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            bridge = CodexAppServerBridge(lambda: Path(temp))
            with self.assertRaises(CodexBridgeError) as raised:
                bridge.handle({"action": "take_over_desktop"})
            self.assertEqual(raised.exception.code, "INVALID_ACTION")


if __name__ == "__main__":
    unittest.main()
