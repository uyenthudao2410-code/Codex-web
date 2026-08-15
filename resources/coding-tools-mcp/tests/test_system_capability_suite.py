from __future__ import annotations

"""Deep capability evaluation suite.

Covers the deployment-critical behaviors identified in the system analysis
reports (docs/research/2026-08-14_*): routing classification invariants,
context/output budget enforcement, durable long-horizon orchestration,
transport/tunnel resilience (stateless HTTP, session aliasing, aborted
clients), idempotent retry safety, routing economics regression thresholds
and lenient in-process latency baselines.

Methodology anchors: SWE-bench (real-task acceptance), tau-bench (pass^k
reliability), fault-injection/chaos patterns (aborted client, session churn,
process restart), and the repo's own Phase 1/2 measured cost constants.
"""

import http.client
import json
import os
import socket
import statistics
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.orchestration_ledger import HANDOFF_CAPSULE_MAX_BYTES
from coding_tools_mcp.protocol import STATELESS_PROTOCOL_VERSION
from coding_tools_mcp.server import AGENT_EXECUTION_ROUTES, MCPHandler, Runtime, RuntimeHTTPServer
from coding_tools_mcp.textutils import truncate_text_head, truncate_text_tail


def make_runtime(root: Path) -> Runtime:
    runtime = Runtime(root)
    return runtime


# --------------------------------------------------------------------------
# 1. Routing classification matrix
# --------------------------------------------------------------------------

class RoutingMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.runtime = Runtime(Path(self.temp.name))

    def tearDown(self) -> None:
        self.runtime.close()
        self.temp.cleanup()

    def route(self, workflow, n_paths, n_bytes, strong_oracle=False, requested="auto", allow_high_cost=False):
        prepared = {"selected_paths": [f"p{i}.py" for i in range(n_paths)], "total_content_bytes": n_bytes}
        return self.runtime._select_agent_execution_route(
            workflow=workflow, prepared=prepared, requested=requested,
            allow_high_cost=allow_high_cost, strong_oracle=strong_oracle,
        )

    def test_workflow_prefers_deterministic_lane(self) -> None:
        for workflow in ("diagnose", "document", "resume", "build_release", "greenfield"):
            result = self.route(workflow, 50, 500_000, strong_oracle=True)
            self.assertEqual(result["selected"], "deterministic", workflow)
            self.assertIsNone(result["profile"])

    def test_auto_holds_deterministic_until_paired_roi_evidence(self) -> None:
        for workflow, n_paths, n_bytes, oracle in (
            ("bugfix", 2, 24_000, True),
            ("bugfix", 2, 24_000, False),
            ("bugfix", 3, 24_000, True),
            ("test_failure", 1, 10_000, True),
            ("feature", 1, 10_000, True),
            ("feature", 8, 200_000, False),
        ):
            result = self.route(workflow, n_paths, n_bytes, strong_oracle=oracle)
            self.assertEqual(result["selected"], "deterministic")
            self.assertEqual(result["reason"], "roi_gate_hold_insufficient_paired_evidence")

    def test_explicit_study_and_escalation_routes_remain_available(self) -> None:
        self.assertEqual(self.route("bugfix", 2, 24_000, strong_oracle=True, requested="mini")["selected"], "mini")
        self.assertEqual(self.route("feature", 4, 60_000, requested="luna")["selected"], "luna")
        self.assertEqual(self.route("feature", 8, 200_000, requested="sol_xhigh")["selected"], "sol_xhigh")
        self.assertEqual(self.route("feature", 8, 200_000, requested="terra")["selected"], "terra")

    def test_high_cost_gate_blocks_max_and_ultra(self) -> None:
        for name in ("sol_max", "sol_ultra"):
            with self.assertRaises(ToolFailure) as ctx:
                self.route("feature", 8, 200_000, requested=name)
            self.assertEqual(ctx.exception.code, "HIGH_COST_ACK_REQUIRED")
            granted = self.route("feature", 8, 200_000, requested=name, allow_high_cost=True)
            self.assertEqual(granted["selected"], name)
            self.assertTrue(granted["high_cost"])

    def test_unknown_route_rejected_and_explicit_route_honored(self) -> None:
        with self.assertRaises(ToolFailure) as ctx:
            self.route("feature", 1, 100, requested="ultra_plus")
        self.assertEqual(ctx.exception.code, "INVALID_EXECUTION_ROUTE")
        self.assertEqual(self.route("feature", 50, 500_000, requested="mini")["selected"], "mini")
        self.assertEqual(self.route("bugfix", 1, 100, requested="deterministic")["selected"], "deterministic")

    def test_auto_is_always_deterministic_during_roi_measurement(self) -> None:
        for workflow in ("bugfix", "feature", "refactor", "test_failure"):
            for n_paths in (1, 2, 4, 8, 50):
                for n_bytes in (100, 24_000, 60_000, 500_000):
                    selected = self.route(workflow, n_paths, n_bytes, strong_oracle=True)["selected"]
                    self.assertEqual(selected, "deterministic")

    def test_decision_is_deterministic(self) -> None:
        inputs = [
            ("bugfix", 2, 12_000, True), ("feature", 3, 40_000, False),
            ("feature", 8, 200_000, False), ("diagnose", 0, 0, False),
        ]
        for workflow, n_paths, n_bytes, oracle in inputs:
            first = self.route(workflow, n_paths, n_bytes, strong_oracle=oracle)
            for _ in range(5):
                again = self.route(workflow, n_paths, n_bytes, strong_oracle=oracle)
                self.assertEqual(first, again)

    def test_route_specs_are_self_consistent(self) -> None:
        for name, spec in AGENT_EXECUTION_ROUTES.items():
            self.assertIn(spec["model"], ("gpt-5.4-mini", "gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol"), name)
            self.assertGreater(spec["deadline_ms"], 0, name)
            if name in ("sol_max", "sol_ultra"):
                self.assertTrue(spec["high_cost"], name)
            else:
                self.assertFalse(spec["high_cost"], name)


# --------------------------------------------------------------------------
# 2. Context / output budget enforcement
# --------------------------------------------------------------------------

class ContextBudgetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.runtime = Runtime(Path(self.temp.name))

    def tearDown(self) -> None:
        self.runtime.close()
        self.temp.cleanup()

    def test_head_truncation_respects_lines_and_bytes(self) -> None:
        text = "\n".join(f"line-{index:04d}" for index in range(500))
        result = truncate_text_head(text, max_lines=100, max_bytes=2048)
        self.assertTrue(result.truncated)
        self.assertEqual(result.truncated_by, "lines")
        self.assertLessEqual(result.output_lines, 100)
        self.assertLessEqual(len(result.content.encode("utf-8")), 2048)
        self.assertIn("line-0000", result.content)

    def test_tail_truncation_keeps_final_lines(self) -> None:
        text = "\n".join(f"line-{index:04d}" for index in range(500))
        result = truncate_text_tail(text, max_lines=100, max_bytes=2048)
        self.assertTrue(result.truncated)
        self.assertIn("line-0499", result.content)
        self.assertNotIn("line-0000", result.content)

    def test_exact_fit_is_not_marked_truncated(self) -> None:
        text = "x" * 100
        result = truncate_text_head(text, max_lines=10, max_bytes=1000)
        self.assertFalse(result.truncated)

    def test_long_command_output_is_capped_and_retainable(self) -> None:
        payload = 120 * 1024
        result = self.runtime.call_tool("exec_command", {
            "cmd": f'"{sys.executable}" -c "import sys; sys.stdout.write(\'A\'*{payload})"',
            "yield_time_ms": 5000,
            "max_output_bytes": 4096,
            "verbosity": "full",
        })
        sc = result["structuredContent"]
        self.assertFalse(result.get("isError"))
        self.assertTrue(sc.get("truncated"))
        self.assertTrue(sc.get("stdout_truncated"))
        self.assertEqual(sc.get("stdout_truncated_by"), "bytes")
        self.assertLessEqual(sc.get("stdout_output_bytes"), 4096)
        retention = sc.get("output_retention", {}).get("stdout", {})
        # response is capped, but the full stream is retained for continuation
        self.assertEqual(retention.get("total_retained_bytes"), retention.get("total_stream_bytes"))
        self.assertEqual(retention.get("total_stream_bytes"), payload)
        self.assertTrue(sc.get("output_ref"))
        next_actions = sc.get("next_actions") or []
        self.assertTrue(any(item.get("tool") == "read_output" for item in next_actions))
        diagnostics = sc.get("diagnostics") or []
        self.assertTrue(any(item.get("code") == "OUTPUT_TRUNCATED" for item in diagnostics))

    def test_small_command_is_not_truncated(self) -> None:
        result = self.runtime.call_tool("exec_command", {
            "cmd": "echo small-output",
            "yield_time_ms": 3000,
            "max_output_bytes": 8192,
            "verbosity": "full",
        })
        sc = result["structuredContent"]
        self.assertFalse(sc.get("truncated"))
        self.assertFalse(sc.get("stdout_truncated"))
        self.assertEqual(sc.get("stdout_dropped_bytes"), 0)

    def test_failed_command_reports_exit_code_without_crashing(self) -> None:
        result = self.runtime.call_tool("exec_command", {
            "cmd": f'"{sys.executable}" -c "import sys; sys.stderr.write(\'boom\'); sys.exit(7)"',
            "yield_time_ms": 5000,
            "max_output_bytes": 4096,
            "verbosity": "full",
        })
        sc = result["structuredContent"]
        self.assertEqual(sc.get("status"), "exited")
        self.assertEqual(sc.get("exit_code"), 7)
        self.assertIn("boom", sc.get("stderr", ""))


# --------------------------------------------------------------------------
# 3. Long-horizon orchestration lifecycle
# --------------------------------------------------------------------------

class LongHorizonLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.runtime = Runtime(Path(self.temp.name))
        self.ledger = self.runtime.orchestration_ledger

    def tearDown(self) -> None:
        self.runtime.close()
        self.temp.cleanup()

    def build_run(self) -> str:
        run_id = self.ledger.create_run(objective="Deep lifecycle probe", task_id="task-1")
        wave = self.ledger.create_wave(run_id, execution_mode="mcp_only", base_head="abc1234")
        for index, event_type in enumerate(("run_started", "context_prepared", "readiness_checked", "route_selected")):
            self.ledger.append_event(
                run_id, wave_id=wave, event_type=event_type,
                state_before="PREFLIGHT" if index == 0 else "PREPARED",
                state_after="PREPARED" if index == 0 else "READY",
                payload={"step": index},
            )
        self.ledger.record_proof(
            run_id=run_id, wave_id=wave, stage_id="verify:tests", stage_version="1",
            input_fingerprint="fp-123", status="passed", duration_ms=3200,
        )
        self.ledger.finish_wave(wave, status="accepted")
        self.ledger.record_checkpoint(run_id=run_id, wave_id=wave, git_head="abc1234", proof_fingerprint="fp-123")
        self.ledger.finish_run(run_id, status="accepted")
        return run_id

    def test_full_run_chain_is_integrity_verified(self) -> None:
        run_id = self.build_run()
        summary = self.ledger.export_summary(run_id)
        self.assertEqual(summary["run"]["status"], "accepted")
        self.assertEqual(summary["waves"][0]["execution_mode"], "mcp_only")
        self.assertEqual(len(summary["events"]), 4)
        self.assertEqual(len(summary["proofs"]), 1)
        self.assertEqual(len(summary["checkpoints"]), 1)
        integrity = summary["integrity"]
        self.assertTrue(integrity["ok"], integrity)

    def test_event_replay_paginates(self) -> None:
        run_id = self.ledger.create_run(objective="pagination probe")
        for index in range(250):
            self.ledger.append_event(run_id, event_type=f"step_{index}", payload={"i": index})
        page1 = self.ledger.list_events_since(run_id, after_seq=0, limit=100)
        self.assertEqual(len(page1["events"]), 100)
        self.assertTrue(page1["has_more"])
        page2 = self.ledger.list_events_since(run_id, after_seq=page1["next_after_seq"], limit=100)
        self.assertEqual(len(page2["events"]), 100)
        page3 = self.ledger.list_events_since(run_id, after_seq=page2["next_after_seq"], limit=100)
        self.assertEqual(len(page3["events"]), 50)
        self.assertFalse(page3["has_more"])

    def test_handoff_capsule_round_trip(self) -> None:
        run_id = self.ledger.create_run(objective="capsule probe")
        capsule = self.ledger.record_handoff_capsule(
            run_id=run_id, conversation_epoch=1,
            payload={"goal": "ship", "next_action": "run verify:tests"},
        )
        self.assertLessEqual(capsule["bytes"], HANDOFF_CAPSULE_MAX_BYTES)
        latest = self.ledger.latest_handoff_capsule(run_id=run_id)
        self.assertIsNotNone(latest)
        self.assertEqual(latest["capsule_id"], capsule["capsule_id"])
        self.assertEqual(latest["payload"]["next_action"], "run verify:tests")

    def test_oversized_capsule_is_rejected(self) -> None:
        run_id = self.ledger.create_run(objective="oversized capsule probe")
        with self.assertRaises(ValueError):
            self.ledger.record_handoff_capsule(run_id=run_id, payload={"transcript": "x" * (HANDOFF_CAPSULE_MAX_BYTES + 64)})

    def test_proof_cache_returns_prior_pass(self) -> None:
        run_id = self.build_run()
        cached = self.ledger.find_cached_pass(stage_id="verify:tests", stage_version="1", input_fingerprint="fp-123")
        self.assertIsNotNone(cached)
        self.assertEqual(cached["status"], "passed")
        self.assertEqual(cached["cache_hit"], False)  # original run itself
        missing = self.ledger.find_cached_pass(stage_id="verify:tests", stage_version="1", input_fingerprint="fp-other")
        self.assertIsNone(missing)

    def test_active_run_scope_and_stale_run_observation(self) -> None:
        finished = self.build_run()
        abandoned = [self.ledger.create_run(objective=f"abandoned {i}") for i in range(5)]
        self.assertEqual(len(abandoned), 5)
        self.assertNotEqual(finished, abandoned[0])
        still_running = self.ledger.create_run(objective="still running")
        current = self.ledger.current_active_run()
        self.assertIsNotNone(current)
        self.assertEqual(current["run_id"], still_running)
        self.assertEqual(current["status"], "active")
        # Gap measurement (W1 in the analysis report): nothing auto-closes
        # abandoned active runs. Record the behavior so the gap stays visible.
        self.assertEqual(self.ledger.list_waves(finished)[0]["status"], "accepted")

    def test_idempotent_replay_after_restart_has_single_side_effect(self) -> None:
        root = Path(self.temp.name)
        marker = root / "marker.txt"
        args = {
            "cmd": "echo ran >> marker.txt",
            "yield_time_ms": 1000,
            "max_output_bytes": 4096,
            "verbosity": "full",
            "idempotency_key": "deep-suite-key",
        }
        first = self.runtime
        first.call_tool("exec_command", dict(args))
        first.close()
        restored = Runtime(root)
        try:
            replay = restored.call_tool("exec_command", dict(args))
            self.assertTrue(replay["structuredContent"].get("deduplicated"))
            lines = marker.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len([line for line in lines if line.strip() == "ran"]), 1)
        finally:
            restored.close()


# --------------------------------------------------------------------------
# 4. Transport / tunnel resilience
# --------------------------------------------------------------------------

class TransportResilienceTests(unittest.TestCase):
    TOKEN = "deep-suite-token-0123456789"

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.runtime = Runtime(Path(cls.temp.name), transport="http", auth_token=cls.TOKEN)
        cls.server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, cls.runtime, runtime_factory=None)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = int(cls.server.server_address[1])

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.runtime.close()
        cls.temp.cleanup()

    def post_stateless(self, method="tools/call", name="task_control", arguments=None, extra_headers=None, request_id="deep-suite-1"):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.TOKEN}",
            "MCP-Protocol-Version": STATELESS_PROTOCOL_VERSION,
            "Mcp-Method": method,
        }
        if name:
            headers["Mcp-Name"] = name
        headers.update(extra_headers or {})
        params = {"name": name, "arguments": arguments or {}}
        params["_meta"] = {
            "io.modelcontextprotocol/protocolVersion": STATELESS_PROTOCOL_VERSION,
            "io.modelcontextprotocol/clientCapabilities": {},
            "io.modelcontextprotocol/clientInfo": {"name": "deep-suite", "version": "1"},
        }
        body = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}).encode("utf-8")
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("POST", "/mcp", body=body, headers=headers)
            response = connection.getresponse()
            raw = response.read()
            return response.status, json.loads(raw.decode("utf-8")) if raw else {}
        finally:
            connection.close()

    def test_orchestration_endpoint_auth_and_shape(self) -> None:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        connection.request("GET", "/__control/orchestration")
        response = connection.getresponse()
        self.assertEqual(response.status, 401)
        connection.close()
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        connection.request("GET", "/__control/orchestration", headers={"Authorization": f"Bearer {self.TOKEN}"})
        response = connection.getresponse()
        body = json.loads(response.read().decode("utf-8"))
        connection.close()
        self.assertEqual(response.status, 200)
        for key in ("task", "run_id", "events", "proofs", "capsule", "counts", "integrity"):
            self.assertIn(key, body, key)

    def test_session_churn_survives_fresh_aliases(self) -> None:
        for index in range(30):
            status, body = self.post_stateless(
                method="tools/call", name="exec_command",
                arguments={
                    "cmd": "echo churn-ok",
                    "yield_time_ms": 3000,
                    "max_output_bytes": 4096,
                    "verbosity": "full",
                },
                request_id=f"churn-{index}",
            )
            self.assertEqual(status, 200, body)
            self.assertNotIn("error", body)

    def test_client_abort_mid_response_does_not_kill_server(self) -> None:
        sock = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        sock.sendall(
            b"GET /__control/orchestration HTTP/1.1\r\n"
            b"Host: 127.0.0.1\r\n"
            + f"Authorization: Bearer {self.TOKEN}\r\n".encode()
            + b"Connection: close\r\n\r\n"
        )
        sock.close()
        time.sleep(0.2)
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        connection.request("GET", "/__control/health", headers={"Authorization": f"Bearer {self.TOKEN}"})
        response = connection.getresponse()
        body = json.loads(response.read().decode("utf-8"))
        connection.close()
        self.assertEqual(response.status, 200)
        self.assertTrue(body.get("ready"))

    def test_partial_upload_then_disconnect_leaves_no_broken_state(self) -> None:
        sock = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        sock.sendall(
            b"POST /mcp HTTP/1.1\r\n"
            b"Host: 127.0.0.1\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: 100000\r\n"
            + f"Authorization: Bearer {self.TOKEN}\r\n".encode()
            + b"MCP-Protocol-Version: 2026-07-28\r\n\r\n"
            + b'{"jsonrpc":"2.0","id":"partial"'
        )
        sock.close()
        time.sleep(0.2)
        status, body = self.post_stateless(arguments={"action": "get"}, request_id="after-partial")
        self.assertEqual(status, 200, body)

    def test_stateless_validation_matrix(self) -> None:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        params = {"name": "task_control", "arguments": {"action": "get"}}
        body = json.dumps({"jsonrpc": "2.0", "id": "no-meta", "method": "tools/call", "params": params})
        connection.request(
            "POST", "/mcp", body=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.TOKEN}",
                "MCP-Protocol-Version": STATELESS_PROTOCOL_VERSION,
                "Mcp-Method": "tools/call",
                "Mcp-Name": "task_control",
            },
        )
        response = connection.getresponse()
        self.assertEqual(response.status, 400)
        parsed = json.loads(response.read().decode("utf-8"))
        self.assertIn(parsed["error"]["code"], (-32602, -32020))
        connection.close()


# --------------------------------------------------------------------------
# 5. Routing economics regression thresholds
# --------------------------------------------------------------------------

CRED = {"mini": 0.1380, "luna": 0.2597, "sol_xhigh": 1.3173}
TTA = {"mini": 10.2, "luna": 10.1, "sol_xhigh": 11.2, "deterministic": 3.3}
PENALTY = 22.8
P_REPAIR_SOL = 0.95
P_SUCCESS = {
    "localized_strong_oracle": {"mini": 0.75, "luna": 0.85, "sol_xhigh": 0.97},
    "bounded_leaf": {"mini": 0.40, "luna": 0.85, "sol_xhigh": 0.95},
    "broad_deep": {"mini": 0.10, "luna": 0.35, "sol_xhigh": 0.92},
}
MIX = [("localized_strong_oracle", 35), ("bounded_leaf", 20), ("broad_deep", 15), ("deterministic_class", 30)]


def economics_sim(strategy: str) -> tuple[float, float, float, float, float]:
    cred = tta = accepted = wasted = critical_miss = 0.0
    for name, count in MIX:
        if name == "deterministic_class":
            accepted += count
            tta += count * TTA["deterministic"]
            continue
        if strategy == "adaptive":
            if name == "localized_strong_oracle":
                first = "mini"
            elif name == "bounded_leaf":
                first = "luna"
            else:
                first = "sol_xhigh"
        elif strategy == "ladder":
            pm = P_SUCCESS[name]["mini"]
            pl = P_SUCCESS[name]["luna"]
            cred += count * (CRED["mini"] + (1 - pm) * CRED["luna"] + (1 - pm) * (1 - pl) * CRED["sol_xhigh"])
            tta += count * (TTA["mini"] + (1 - pm) * (TTA["luna"] + PENALTY) + (1 - pm) * (1 - pl) * (TTA["sol_xhigh"] + PENALTY))
            accepted += count * (pm + (1 - pm) * pl + (1 - pm) * (1 - pl) * P_REPAIR_SOL)
            wasted += count * ((1 - pm) + (1 - pm) * (1 - pl))
            critical_miss += count * (1 - (pm + (1 - pm) * pl + (1 - pm) * (1 - pl) * P_REPAIR_SOL))
            continue
        else:
            first = {"all_sol_xhigh": "sol_xhigh", "all_luna": "luna", "all_mini": "mini"}[strategy]
        p1 = P_SUCCESS[name][first]
        cred += count * CRED[first]
        tta += count * TTA[first]
        fail = count * (1 - p1)
        cred += fail * CRED["sol_xhigh"]
        tta += fail * (TTA["sol_xhigh"] + PENALTY)
        wasted += fail
        accepted += count * p1 + fail * P_REPAIR_SOL
        critical_miss += fail * (1 - P_REPAIR_SOL)
    return cred, tta, accepted, wasted, critical_miss


class RoutingEconomicsTests(unittest.TestCase):
    def test_adaptive_beats_all_sol_by_wide_margin(self) -> None:
        adaptive = economics_sim("adaptive")
        all_sol = economics_sim("all_sol_xhigh")
        savings = (1 - adaptive[0] / all_sol[0]) * 100
        self.assertGreater(savings, 40, f"tiết kiệm chỉ {savings:.1f}%")
        self.assertLess(adaptive[4], all_sol[4] + 0.6)

    def test_ladder_is_wasteful_despite_low_credits(self) -> None:
        adaptive = economics_sim("adaptive")
        ladder = economics_sim("ladder")
        self.assertLess(ladder[0], adaptive[0])
        self.assertGreater(ladder[3], 3 * adaptive[3])
        self.assertGreater(ladder[1], adaptive[1])

    def test_all_mini_is_most_dangerous(self) -> None:
        mini = economics_sim("all_mini")
        adaptive = economics_sim("adaptive")
        self.assertGreater(mini[4], adaptive[4] * 2)

    def test_deterministic_lane_costs_zero_credits(self) -> None:
        cred, tta, accepted, *_ = economics_sim("adaptive")
        self.assertGreaterEqual(accepted, 99.0)
        # 30 deterministic tasks contribute exactly their TTA and no credits
        base_without_deterministic = (
            35 * CRED["mini"] + 20 * CRED["luna"] + 15 * CRED["sol_xhigh"]
        )
        self.assertGreaterEqual(cred, base_without_deterministic)
        self.assertLess(cred, base_without_deterministic + 35 * CRED["sol_xhigh"])

    def test_sensitivity_is_monotonic(self) -> None:
        original = dict(P_SUCCESS["localized_strong_oracle"])
        costs = []
        for pm in (0.5, 0.6, 0.7, 0.8, 0.9):
            P_SUCCESS["localized_strong_oracle"]["mini"] = pm
            costs.append(economics_sim("adaptive")[0])
        P_SUCCESS["localized_strong_oracle"] = original
        self.assertEqual(costs, sorted(costs, reverse=True))


# --------------------------------------------------------------------------
# 6. Lenient in-process latency baselines
# --------------------------------------------------------------------------

class PerfBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.runtime = Runtime(Path(self.temp.name))

    def tearDown(self) -> None:
        self.runtime.close()
        self.temp.cleanup()

    def test_echo_command_median_latency(self) -> None:
        durations = []
        for _ in range(12):
            started = time.monotonic()
            result = self.runtime.call_tool("exec_command", {
                "cmd": "echo perf-probe",
                "yield_time_ms": 3000,
                "max_output_bytes": 4096,
                "verbosity": "full",
            })
            durations.append((time.monotonic() - started) * 1000)
            self.assertFalse(result.get("isError"))
        self.assertLess(statistics.median(durations), 600, f"median {statistics.median(durations):.0f}ms")

    def test_routing_decision_latency(self) -> None:
        durations = []
        prepared_small = {"selected_paths": ["a.py", "b.py"], "total_content_bytes": 12_000}
        prepared_big = {"selected_paths": [f"f{i}.py" for i in range(8)], "total_content_bytes": 200_000}
        for _ in range(60):
            started = time.monotonic()
            self.runtime._select_agent_execution_route(
                workflow="bugfix", prepared=prepared_small, requested="auto",
                allow_high_cost=False, strong_oracle=True,
            )
            self.runtime._select_agent_execution_route(
                workflow="feature", prepared=prepared_big, requested="auto",
                allow_high_cost=False, strong_oracle=False,
            )
            durations.append((time.monotonic() - started) * 1000)
        self.assertLess(statistics.median(durations), 10, f"median {statistics.median(durations):.2f}ms")

    def test_text_truncation_throughput(self) -> None:
        text = ("x" * 120 + "\n") * 20_000
        durations = []
        for _ in range(15):
            started = time.monotonic()
            truncate_text_tail(text, max_lines=2000, max_bytes=50 * 1024)
            durations.append((time.monotonic() - started) * 1000)
        self.assertLess(statistics.median(durations), 100, f"median {statistics.median(durations):.1f}ms")
