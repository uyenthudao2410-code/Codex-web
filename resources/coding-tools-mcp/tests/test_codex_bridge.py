from __future__ import annotations

import tempfile
import threading
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
from coding_tools_mcp.secret_broker import OPENAI_API_KEY_HANDLE, SecretBroker


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

    def test_codex_child_env_uses_core_env_and_brokered_provider_secret_only(self) -> None:
        source = {
            "PATH": "keep",
            "OPENAI_API_KEY": "ambient-provider-auth-must-not-pass",
            "UNRELATED_SECRET": "ambient-secret-must-not-pass",
            "PYTHONPATH": "ambient-loader-path-must-not-pass",
            "CODING_TOOLS_MCP_AUTH_TOKEN": "drop-me",
            "CODING_TOOLS_MCP_TOOL_MODE": "smart",
            "WEBCODEX_TOKEN": "drop-me-too",
        }
        without_broker = sanitized_codex_env(source)
        self.assertEqual(without_broker["PATH"], "keep")
        self.assertNotIn("OPENAI_API_KEY", without_broker)
        self.assertNotIn("UNRELATED_SECRET", without_broker)
        self.assertNotIn("PYTHONPATH", without_broker)

        broker = SecretBroker({OPENAI_API_KEY_HANDLE: "brokered-provider-auth"})
        cleaned = sanitized_codex_env(source, secret_broker=broker)
        self.assertEqual(cleaned["PATH"], "keep")
        self.assertEqual(cleaned["OPENAI_API_KEY"], "brokered-provider-auth")
        self.assertNotIn("CODING_TOOLS_MCP_AUTH_TOKEN", cleaned)
        self.assertNotIn("CODING_TOOLS_MCP_TOOL_MODE", cleaned)
        self.assertNotIn("WEBCODEX_TOKEN", cleaned)
        self.assertNotIn("UNRELATED_SECRET", cleaned)
        self.assertNotIn("PYTHONPATH", cleaned)

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

    def test_persistent_lane_can_be_resumed_by_a_new_bridge_instance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = CodexAppServerBridge(lambda: root)
            first._ensure_connected = lambda: None
            first_calls = []

            def first_request(method, params):
                first_calls.append((method, dict(params)))
                if method == "thread/start":
                    return {
                        "thread": {
                            "id": "persistent-thread",
                            "sessionId": "session-1",
                            "cwd": str(root),
                            "model": "gpt-5.6-terra",
                            "reasoningEffort": "high",
                        }
                    }
                if method == "turn/start":
                    return {"turn": {"id": "turn-1", "status": "inProgress"}}
                raise AssertionError(method)

            first._request = first_request
            started = first.run(
                "investigate the bounded lane",
                profile="cross_file",
                lifetime="persistent",
            )
            start_params = next(params for method, params in first_calls if method == "thread/start")
            self.assertFalse(start_params["ephemeral"])
            self.assertEqual(started["creation_mode"], "persistent_new")
            self.assertEqual(started["lifetime"], "persistent")
            self.assertEqual(started["session_id"], "session-1")

            restored = CodexAppServerBridge(lambda: root)
            restored._ensure_connected = lambda: None
            restored_calls = []

            def restored_request(method, params):
                restored_calls.append((method, dict(params)))
                if method == "thread/read":
                    return {
                        "thread": {
                            "id": "persistent-thread",
                            "sessionId": "session-1",
                            "cwd": str(root),
                        }
                    }
                if method == "thread/resume":
                    return {
                        "thread": {
                            "id": "persistent-thread",
                            "sessionId": "session-1",
                            "cwd": str(root),
                            "model": "gpt-5.6-terra",
                            "reasoningEffort": "high",
                        }
                    }
                if method == "turn/start":
                    return {"turn": {"id": "turn-2", "status": "inProgress"}}
                raise AssertionError(method)

            restored._request = restored_request
            resumed = restored.resume_persistent_thread(
                thread_id="persistent-thread",
                expected_session_id="session-1",
                prompt="continue from the durable lane state",
                profile="cross_file",
                model="gpt-5.6-terra",
                effort="high",
            )
            self.assertEqual(resumed["creation_mode"], "persistent_resume")
            self.assertEqual(resumed["lifetime"], "persistent")
            self.assertEqual(resumed["session_id"], "session-1")
            methods = [method for method, _params in restored_calls]
            self.assertEqual(methods[:3], ["thread/read", "thread/resume", "turn/start"])
            resume_params = next(params for method, params in restored_calls if method == "thread/resume")
            self.assertEqual(resume_params["threadId"], "persistent-thread")
            self.assertEqual(resume_params["approvalPolicy"], "never")
            self.assertEqual(resume_params["sandbox"], "read-only")

    def test_persistent_resume_rejects_workspace_or_session_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sibling = root.parent / f"{root.name}-sibling"
            sibling.mkdir(exist_ok=True)
            bridge = CodexAppServerBridge(lambda: root)
            bridge._ensure_connected = lambda: None
            bridge._request = lambda method, _params: {
                "thread": {
                    "id": "persistent-thread",
                    "sessionId": "other-session",
                    "cwd": str(sibling),
                }
            } if method == "thread/read" else None
            with self.assertRaises(CodexBridgeError) as raised:
                bridge.resume_persistent_thread(
                    thread_id="persistent-thread",
                    expected_session_id="session-1",
                    prompt="continue",
                    profile="cross_file",
                )
            self.assertEqual(raised.exception.code, "PERSISTENT_WORKSPACE_MISMATCH")
            sibling.rmdir()

            bridge._request = lambda method, _params: {
                "thread": {
                    "id": "persistent-thread",
                    "cwd": str(root),
                }
            } if method == "thread/read" else None
            with self.assertRaises(CodexBridgeError) as raised:
                bridge.resume_persistent_thread(
                    thread_id="persistent-thread",
                    expected_session_id="session-1",
                    prompt="continue",
                    profile="cross_file",
                )
            self.assertEqual(raised.exception.code, "PERSISTENT_SESSION_MISMATCH")

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

    def test_observe_wakes_for_meaningful_turn_started_event(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            bridge = CodexAppServerBridge(lambda: Path(temp))
            bridge._ensure_connected = lambda: None
            bridge._owned_threads["owned"] = {"workspace": temp}
            bridge._latest_turn_by_thread["owned"] = "turn"
            bridge._turn_states["turn"] = {"thread_id": "owned", "status": "inProgress"}
            waiting = threading.Event()
            original_wait = bridge._condition.wait

            def signal_wait(timeout=None):
                waiting.set()
                return original_wait(timeout)

            bridge._condition.wait = signal_wait
            result: dict = {}
            observer = threading.Thread(
                target=lambda: result.update(
                    bridge.observe(thread_id="owned", turn_id="turn", after_cursor=0, wait_ms=1_000)
                ),
            )
            observer.start()
            self.assertTrue(waiting.wait(timeout=1))
            bridge._append_event(
                "turn/started",
                {"threadId": "owned", "turn": {"id": "turn", "status": "inProgress"}},
                server_request=False,
            )
            observer.join(timeout=1)
            self.assertFalse(observer.is_alive())
            self.assertEqual([item["method"] for item in result["events"]], ["turn/started"])
            self.assertFalse(result["history_gap"])

    def test_observe_reports_evicted_cursor_gap_and_rebaselines(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            bridge = CodexAppServerBridge(lambda: Path(temp))
            bridge._ensure_connected = lambda: None
            bridge._owned_threads["owned"] = {"workspace": temp}
            bridge._latest_turn_by_thread["owned"] = "turn"
            bridge._turn_states["turn"] = {"thread_id": "owned", "status": "inProgress"}
            for _ in range(401):
                bridge._append_event(
                    "turn/started",
                    {"threadId": "owned", "turn": {"id": "turn", "status": "inProgress"}},
                    server_request=False,
                )
            result = bridge.observe(thread_id="owned", turn_id="turn", after_cursor=0, max_events=5)
            self.assertTrue(result["history_gap"])
            self.assertEqual(result["history_floor_cursor"], 2)
            self.assertEqual([item["cursor"] for item in result["events"]], [2, 3, 4, 5, 6])
            self.assertEqual(result["next_cursor"], 6)

    def test_credit_estimate_uses_uncached_cached_and_output_rates(self) -> None:
        economics = _usage_economics({"last": {"inputTokens": 10_000, "cachedInputTokens": 8_000, "outputTokens": 100, "reasoningOutputTokens": 50}}, "gpt-5.6-luna")
        self.assertIsNotNone(economics)
        self.assertEqual(economics["uncached_input_tokens"], 2_000)
        self.assertEqual(economics["cached_input_tokens"], 8_000)
        self.assertAlmostEqual(economics["estimated_credits"], 0.085, places=6)
        self.assertTrue(economics["measured"])
        self.assertEqual(economics["usage_provenance"], "provider_reported")
        self.assertEqual(economics["usage_source"], "codex_app_server:thread/tokenUsage/updated")
        self.assertEqual(economics["accounting_profile"], "openai_compatible")

    def test_usage_economics_rejects_incomplete_or_invalid_exact_token_receipts(self) -> None:
        invalid = (
            {"inputTokens": 10, "cachedInputTokens": 2, "outputTokens": 3},
            {"inputTokens": 10, "cachedInputTokens": 2, "outputTokens": 3, "reasoningOutputTokens": True},
            {"inputTokens": -1, "cachedInputTokens": 0, "outputTokens": 3, "reasoningOutputTokens": 1},
            {"inputTokens": 10, "cachedInputTokens": 11, "outputTokens": 3, "reasoningOutputTokens": 1},
            {"inputTokens": 10, "cachedInputTokens": 2, "outputTokens": 3, "reasoningOutputTokens": 4},
        )
        for last in invalid:
            with self.subTest(last=last):
                self.assertIsNone(_usage_economics({"last": last}, "gpt-5.6-luna"))

    def test_invalid_action_fails_without_starting_codex(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            bridge = CodexAppServerBridge(lambda: Path(temp))
            with self.assertRaises(CodexBridgeError) as raised:
                bridge.handle({"action": "take_over_desktop"})
            self.assertEqual(raised.exception.code, "INVALID_ACTION")


if __name__ == "__main__":
    unittest.main()
