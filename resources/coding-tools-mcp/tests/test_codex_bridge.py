from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_persistent_restore_reclaims_the_registered_lane_without_turn_start(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bridge = CodexAppServerBridge(lambda: root)
            bridge._ensure_connected = lambda: None
            calls = []

            def fake_request(method, params):
                calls.append((method, dict(params)))
                if method == "thread/read":
                    return {"thread": {"id": "persistent-thread", "sessionId": "session-1", "cwd": str(root)}}
                if method == "thread/resume":
                    return {"thread": {"id": "persistent-thread", "sessionId": "session-1", "cwd": str(root)}}
                raise AssertionError(method)

            bridge._request = fake_request
            restored = bridge.restore_persistent_thread(
                thread_id="persistent-thread",
                expected_session_id="session-1",
                profile="continuation_proposal",
                model="gpt-5.6-sol",
                effort="xhigh",
            )
            self.assertEqual(restored["creation_mode"], "persistent_restore")
            self.assertEqual(restored["session_id"], "session-1")
            self.assertTrue(bridge.owns_thread("persistent-thread"))
            self.assertEqual([method for method, _params in calls], ["thread/read", "thread/resume"])

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

    def test_chat_profile_is_conversational_but_keeps_bridge_invariants(self) -> None:
        # W3 native chat: the chat profile resolves to a conversational route,
        # yet the turn still launches under the bridge-wide invariants
        # (approvalPolicy=never, read-only sandbox, no network).
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bridge = CodexAppServerBridge(lambda: root)
            route = bridge._resolve_route(profile="chat", model=None, effort=None, source_thread_id=None)
            self.assertEqual(route["model"], "gpt-5.6-terra")
            self.assertEqual(route["effort"], "medium")
            self.assertTrue(route["features"]["shell_tool"])
            self.assertFalse(route["features"]["multi_agent"])
            self.assertIn("built-in chat assistant", route["base_instructions"])

            bridge._ensure_connected = lambda: None
            calls = []

            def fake_request(method, params):
                calls.append((method, dict(params)))
                if method == "thread/start":
                    return {"thread": {"id": "chat-thread", "sessionId": "chat-session"}}
                if method == "turn/start":
                    return {"turn": {"id": "chat-turn", "status": "inProgress"}}
                raise AssertionError(method)

            bridge._request = fake_request
            result = bridge.run("Xin chào, workspace này có gì?", profile="chat")
            self.assertEqual(result["thread_id"], "chat-thread")
            self.assertEqual(result["route"]["profile"], "chat")
            thread_params = next(params for method, params in calls if method == "thread/start")
            turn_params = next(params for method, params in calls if method == "turn/start")
            self.assertEqual(thread_params["approvalPolicy"], "never")
            self.assertEqual(thread_params["sandbox"], "read-only")
            self.assertIn("built-in chat assistant", thread_params["baseInstructions"])
            self.assertEqual(turn_params["sandboxPolicy"], {"type": "readOnly", "networkAccess": False})
            # The new thread is bridge-owned, so the chat panel may continue it.
            self.assertTrue(bridge.owns_thread("chat-thread"))

    def test_continuation_profile_is_fixed_no_tools_and_rejects_custom_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bridge = CodexAppServerBridge(lambda: root)
            bridge._ensure_connected = lambda: None
            calls = []

            def fake_request(method, params):
                calls.append((method, dict(params)))
                if method == "thread/start":
                    return {"thread": {"id": "continuation-thread", "sessionId": "continuation-session"}}
                if method == "turn/start":
                    return {"turn": {"id": "continuation-turn", "status": "inProgress"}}
                raise AssertionError(method)

            bridge._request = fake_request
            result = bridge.run("proposal", profile="continuation_proposal", lifetime="persistent")
            self.assertEqual(result["route"]["model"], "gpt-5.6-sol")
            self.assertEqual(result["route"]["effort"], "xhigh")
            thread_params = next(params for method, params in calls if method == "thread/start")
            turn_params = next(params for method, params in calls if method == "turn/start")
            self.assertFalse(thread_params["config"]["features"]["shell_tool"])
            self.assertFalse(thread_params["config"]["features"]["multi_agent"])
            self.assertEqual(turn_params["sandboxPolicy"], {"type": "readOnly", "networkAccess": False})
            self.assertNotIn("outputSchema", turn_params)
            with self.assertRaises(CodexBridgeError) as override:
                bridge._resolve_route(profile="continuation_proposal", model="gpt-5.6-luna", effort="high", source_thread_id=None)
            self.assertEqual(override.exception.code, "PROFILE_ROUTE_LOCKED")

            strict = CodexAppServerBridge(lambda: root)
            strict._ensure_connected = lambda: None
            with patch.dict("os.environ", {"CODING_TOOLS_MCP_CODEX_ARGV": '["codex","app-server"]'}):
                with self.assertRaises(CodexBridgeError) as custom:
                    strict.run("proposal", profile="continuation_proposal")
            self.assertEqual(custom.exception.code, "CONTINUATION_PROFILE_UNCERTIFIED_LAUNCH")

    def test_turn_start_response_preserves_terminal_notification_state(self) -> None:
        terminal_cases = (
            ("completed", None),
            ("failed", {"message": "terminal failure"}),
            ("interrupted", None),
        )
        for index, (terminal_status, terminal_error) in enumerate(terminal_cases, start=1):
            with self.subTest(status=terminal_status), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                bridge = CodexAppServerBridge(lambda: root)
                bridge._ensure_connected = lambda: None
                thread_id = f"terminal-thread-{index}"
                turn_id = f"terminal-turn-{index}"
                usage = {
                    "last": {"inputTokens": 10, "cachedInputTokens": 2, "outputTokens": 3, "reasoningOutputTokens": 1},
                    "total": {"inputTokens": 10, "cachedInputTokens": 2, "outputTokens": 3, "reasoningOutputTokens": 1},
                    "modelContextWindow": 1_000,
                }

                def fake_request(method, _params):
                    if method == "thread/start":
                        return {"thread": {"id": thread_id}}
                    if method == "turn/start":
                        bridge._record_notification(
                            "item/completed",
                            {
                                "threadId": thread_id,
                                "turnId": turn_id,
                                "item": {"type": "agentMessage", "text": f"terminal text {terminal_status}"},
                            },
                        )
                        bridge._record_notification(
                            "thread/tokenUsage/updated",
                            {"threadId": thread_id, "turnId": turn_id, "tokenUsage": usage},
                        )
                        bridge._record_notification(
                            "turn/completed",
                            {
                                "threadId": thread_id,
                                "turn": {"id": turn_id, "status": terminal_status, "error": terminal_error},
                            },
                        )
                        bridge._turn_states[turn_id]["started_monotonic"] = 123.0
                        bridge._turn_states[turn_id]["finalized"] = True
                        return {
                            "turn": {
                                "id": turn_id,
                                "status": "inProgress",
                                "error": {"message": "stale turn/start response"},
                            }
                        }
                    raise AssertionError(method)

                bridge._request = fake_request
                result = bridge.run("review packet", profile="packet")
                state = bridge._turn_states[turn_id]
                self.assertEqual(result["status"], terminal_status)
                self.assertEqual(state["status"], terminal_status)
                self.assertEqual(state["error"], terminal_error)
                self.assertEqual(state["agent_text"], f"terminal text {terminal_status}")
                self.assertEqual(
                    state["token_usage"],
                    {"last": usage["last"], "total": usage["total"], "model_context_window": 1_000},
                )
                self.assertEqual(state["started_monotonic"], 123.0)
                self.assertTrue(state["finalized"])

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
            clock = [0.0]
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
            def fake_observe(**_kwargs):
                clock[0] = 0.002
                return observations.pop(0)
            bridge.observe = fake_observe
            def raced_interrupt(**_kwargs):
                raise CodexBridgeError("APP_SERVER_ERROR", "no active turn to interrupt")
            bridge.interrupt = raced_interrupt
            with patch("coding_tools_mcp.codex_bridge.time.monotonic", side_effect=lambda: clock[0]):
                result = bridge.run("review", profile="packet", deadline_ms=1)
            self.assertTrue(result["deadline_hit"])
            self.assertEqual(result["status"], "deadline")
            self.assertTrue(result["observation"]["terminal"])
            self.assertEqual(result["observation"]["deadline_resolution"], "app_server_reports_no_active_turn")

    def test_deadline_keeps_observing_after_turn_started_until_terminal(self) -> None:
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
                {"terminal": True, "status": "completed", "next_cursor": 2},
            ]
            observed = []
            def fake_observe(**kwargs):
                observed.append(kwargs)
                return observations.pop(0)
            bridge.observe = fake_observe
            bridge.interrupt = lambda **_kwargs: self.fail("turn/started must not be treated as a deadline")
            with patch("coding_tools_mcp.codex_bridge.time.monotonic", return_value=0.0):
                result = bridge.run("review", profile="packet", deadline_ms=100)
            self.assertEqual(len(observed), 2)
            self.assertEqual([item["after_cursor"] for item in observed], [0, 1])
            self.assertFalse(result["deadline_hit"])
            self.assertEqual(result["status"], "completed")
            self.assertTrue(result["observation"]["terminal"])

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

    def test_handle_resume_reowns_a_registered_chat_thread_without_a_turn(self) -> None:
        # W3-C: after a sidecar restart the Work Hub chat service asks the
        # new bridge instance to take back the exact thread it registered
        # at creation (thread_id + session_id). Resume must restore
        # ownership through thread/read + thread/resume and launch no turn.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bridge = CodexAppServerBridge(lambda: root)
            bridge._ensure_connected = lambda: None
            calls = []

            def fake_request(method, params):
                calls.append((method, dict(params)))
                if method == "thread/read":
                    return {"thread": {"id": "chat-thread", "sessionId": "chat-session", "cwd": str(root)}}
                if method == "thread/resume":
                    return {"thread": {"id": "chat-thread", "sessionId": "chat-session", "cwd": str(root), "model": "gpt-5.6-terra", "reasoningEffort": "medium"}}
                raise AssertionError(method)

            bridge._request = fake_request
            result = bridge.handle({
                "action": "resume",
                "thread_id": "chat-thread",
                "session_id": "chat-session",
                "profile": "chat",
            })
            self.assertTrue(result["resumed"])
            self.assertEqual(result["thread_id"], "chat-thread")
            self.assertEqual(result["session_id"], "chat-session")
            self.assertEqual(result["route"], {"profile": "chat", "model": "gpt-5.6-terra", "effort": "medium"})
            self.assertNotIn("base_instructions", result["route"])
            self.assertTrue(bridge.owns_thread("chat-thread"))
            self.assertEqual([method for method, _params in calls], ["thread/read", "thread/resume"])
            resume_params = next(params for method, params in calls if method == "thread/resume")
            self.assertEqual(resume_params["approvalPolicy"], "never")
            self.assertEqual(resume_params["sandbox"], "read-only")

    def test_handle_resume_refuses_a_session_identity_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bridge = CodexAppServerBridge(lambda: root)
            bridge._ensure_connected = lambda: None
            bridge._request = lambda method, _params: {
                "thread": {"id": "chat-thread", "sessionId": "other-session", "cwd": str(root)}
            } if method == "thread/read" else None
            with self.assertRaises(CodexBridgeError) as raised:
                bridge.handle({
                    "action": "resume",
                    "thread_id": "chat-thread",
                    "session_id": "chat-session",
                    "profile": "chat",
                })
            self.assertEqual(raised.exception.code, "PERSISTENT_SESSION_MISMATCH")
            self.assertFalse(bridge.owns_thread("chat-thread"))

    def test_chat_run_accepts_model_and_effort_overrides_without_breaking_invariants(self) -> None:
        # W3-C selector: profile chat is not route-locked, so run/continue
        # may carry a model/effort override; the turn still launches with
        # approvalPolicy=never, a read-only sandbox and no network.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bridge = CodexAppServerBridge(lambda: root)
            bridge._ensure_connected = lambda: None
            calls = []

            def fake_request(method, params):
                calls.append((method, dict(params)))
                if method == "thread/start":
                    return {"thread": {"id": "chat-thread", "sessionId": "chat-session"}}
                if method == "turn/start":
                    return {"turn": {"id": "chat-turn", "status": "inProgress"}}
                raise AssertionError(method)

            bridge._request = fake_request
            result = bridge.run("Chào", profile="chat", model="gpt-5.6-sol", effort="high", lifetime="persistent")
            self.assertEqual(result["route"]["model"], "gpt-5.6-sol")
            self.assertEqual(result["route"]["effort"], "high")
            self.assertEqual(result["lifetime"], "persistent")
            self.assertEqual(result["creation_mode"], "persistent_new")
            thread_params = next(params for method, params in calls if method == "thread/start")
            turn_params = next(params for method, params in calls if method == "turn/start")
            self.assertFalse(thread_params["ephemeral"])
            self.assertEqual(thread_params["config"]["model_reasoning_effort"], "high")
            self.assertEqual(thread_params["approvalPolicy"], "never")
            self.assertEqual(turn_params["model"], "gpt-5.6-sol")
            self.assertEqual(turn_params["effort"], "high")
            self.assertEqual(turn_params["sandboxPolicy"], {"type": "readOnly", "networkAccess": False})

            bridge._turn_states["chat-turn"] = {"thread_id": "chat-thread", "status": "completed"}
            bridge._latest_turn_by_thread["chat-thread"] = "chat-turn"
            calls.clear()
            follow = bridge.continue_thread(thread_id="chat-thread", prompt="Tiếp", model="gpt-5.6-luna", effort="low")
            self.assertEqual(follow["route"]["model"], "gpt-5.6-luna")
            self.assertEqual(follow["route"]["effort"], "low")
            turn_params = next(params for method, params in calls if method == "turn/start")
            self.assertEqual(turn_params["model"], "gpt-5.6-luna")
            self.assertEqual(turn_params["effort"], "low")

    def test_invalid_action_fails_without_starting_codex(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            bridge = CodexAppServerBridge(lambda: Path(temp))
            with self.assertRaises(CodexBridgeError) as raised:
                bridge.handle({"action": "take_over_desktop"})
            self.assertEqual(raised.exception.code, "INVALID_ACTION")


if __name__ == "__main__":
    unittest.main()
