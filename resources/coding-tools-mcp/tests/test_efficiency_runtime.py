from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.performance_trace import PerformanceTraceStore
from coding_tools_mcp.server import Runtime, server_card_payload


class EfficiencyRuntimeTests(unittest.TestCase):
    def test_performance_trace_v3_records_eligible_idempotency_proof_savings_and_run_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            store = PerformanceTraceStore(Path(temp))
            state = store.record(
                tool="agent_workflow",
                started_monotonic=10.0,
                finished_monotonic=11.0,
                request_bytes=100,
                response_bytes=200,
                idempotency_eligible=True,
                idempotency_key_present=True,
                proof_cache_hits=2,
                proof_cache_saved_ms=1750,
                orchestration={
                    "run_id": "run-1",
                    "wave_id": "wave-1",
                    "execution_mode": "mcp_only",
                    "route_requested": "auto",
                    "route_resolved": "deterministic",
                    "orchestration_state": "ACCEPTING",
                },
            )
            self.assertEqual(state["version"], 3)
            self.assertEqual(state["idempotency_eligible_calls"], 1)
            self.assertEqual(state["idempotency_eligible_key_calls"], 1)
            self.assertEqual(state["idempotency_key_calls"], 1)
            self.assertEqual(state["proof_cache_hits"], 2)
            self.assertEqual(state["proof_cache_saved_ms"], 1750)
            self.assertEqual(state["execution_mode_counts"], {"mcp_only": 1})
            self.assertEqual(state["route_resolved_counts"], {"deterministic": 1})
            self.assertEqual(state["orchestration_state_counts"], {"ACCEPTING": 1})
            event = state["recent"][-1]
            self.assertTrue(event["idempotency_eligible"])
            self.assertTrue(event["idempotency_key_present"])
            self.assertEqual(event["proof_cache_hits"], 2)
            self.assertEqual(event["route_resolved"], "deterministic")
            metric = state["run_metrics"]["run-1"]
            self.assertEqual(metric["tool_calls"], 1)
            self.assertEqual(metric["idempotency_eligible_calls"], 1)
            self.assertEqual(metric["idempotency_eligible_key_calls"], 1)
            self.assertEqual(metric["proof_cache_saved_ms"], 1750)

    def test_idempotency_coverage_denominator_uses_only_mutating_or_expensive_calls(self) -> None:
        self.assertFalse(Runtime._idempotency_eligible_call("workspace_context", {}))
        self.assertFalse(Runtime._idempotency_eligible_call("agent_workflow", {"phase": "prepare"}))
        self.assertTrue(Runtime._idempotency_eligible_call("agent_workflow", {"phase": "execute"}))
        self.assertTrue(Runtime._idempotency_eligible_call("exec_command", {"cmd": "echo ok"}))
        self.assertFalse(Runtime._idempotency_eligible_call("command_control", {"action": "poll"}))
        self.assertTrue(Runtime._idempotency_eligible_call("command_control", {"action": "kill"}))
        self.assertFalse(Runtime._idempotency_eligible_call("task_control", {"action": "handoff", "handoff_action": "get"}))
        self.assertTrue(Runtime._idempotency_eligible_call("task_control", {"action": "handoff", "handoff_action": "record"}))
        self.assertTrue(Runtime._idempotency_eligible_call("task_control", {"action": "restart_runtime"}))

    def test_workspace_context_exposes_non_secret_runtime_activation_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            runtime = Runtime(Path(temp), permission_mode="safe")
            try:
                compact = runtime.workspace_context({"detail": "compact"})
                self.assertNotIn("runtime", compact)
                context = runtime.workspace_context({"detail": "full"})
                identity = context["runtime"]
                self.assertEqual(identity["server_instance_id"], runtime.server_instance_id)
                self.assertEqual(identity["process_instance_id"], runtime.process_instance_id)
                self.assertEqual(identity["performance_trace_version"], 3)
                contract = identity["tool_contract"]
                self.assertEqual(contract["schema_version"], 1)
                self.assertEqual(contract["profile"], "smart-v3")
                self.assertEqual(contract["tool_count"], 8)
                self.assertEqual(len(contract["sha256"]), 64)
                card = server_card_payload(runtime)
                self.assertEqual(card["tools"]["contractSha256"], contract["sha256"])
                self.assertNotIn("auth_token", identity)
            finally:
                runtime.close()

    def test_stale_run_reconciliation_preserves_live_owners(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            now = time.time()
            stale_run = ledger.create_run(objective="abandoned")
            protected_run = ledger.create_run(objective="still running")
            ledger.start_background_operation(
                operation_id="op-live",
                server_instance_id="server",
                tool="agent_workflow",
                run_id=protected_run,
                summary={},
            )
            reconciled = ledger.reconcile_stale_runs(stale_after_seconds=3600, now=now + 7200)
            self.assertIn(stale_run, reconciled)
            self.assertNotIn(protected_run, reconciled)
            self.assertEqual(ledger.get_run(stale_run)["status"], "stale")
            self.assertEqual(ledger.get_run(protected_run)["status"], "active")
            events = ledger.list_events(stale_run)
            self.assertEqual(events[-1]["event_type"], "run_stale_reconciled")
            self.assertEqual(events[-1]["state_after"], "ABORTED")

    @unittest.skipUnless(shutil.which("git"), "git is required")
    def test_orchestration_identity_ignores_runtime_state_but_detects_source_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            source = root / "app.py"
            source.write_text("VALUE = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "app.py"], cwd=root, check=True, capture_output=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "base"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            runtime = Runtime(root, permission_mode="safe")
            try:
                first = runtime._orchestration_workspace_identity(".")
                runtime_state = root / ".coding-tools" / "volatile.json"
                runtime_state.parent.mkdir(parents=True, exist_ok=True)
                runtime_state.write_text('{"tick": 1}\n', encoding="utf-8")
                second = runtime._orchestration_workspace_identity(".")
                self.assertEqual(first["worktree_fp"], second["worktree_fp"])
                self.assertNotIn(".coding-tools/volatile.json", second["dirty_paths"])
                source.write_text("VALUE = 2\n", encoding="utf-8")
                third = runtime._orchestration_workspace_identity(".")
                self.assertNotEqual(second["worktree_fp"], third["worktree_fp"])
                self.assertIn("app.py", third["dirty_paths"])
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
