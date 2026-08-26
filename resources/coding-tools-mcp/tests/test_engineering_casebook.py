from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.orchestration_control import OrchestrationControl
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.server import MCPHandler, Runtime
from coding_tools_mcp.truth_snapshot import build_truth_snapshot, match_state


class ExecutableEngineeringCasebookTests(unittest.TestCase):
    """Deterministic regressions for accepted Coding Web engineering lessons."""

    def test_case_01_replan_changes_wave_objective_without_rewriting_run_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            control = OrchestrationControl(root, ledger)
            ctx = control.begin(
                objective="Build NSIS package",
                task_id="casebook-objective-provenance",
                execution_mode="deep_single_lane",
                base_head="abc",
                worktree_fp="fp-1",
            )
            control.mark_ready(ctx)
            control.select_route(ctx, {"requested": "sol_xhigh", "selected": "sol_xhigh"})
            control.acquire_write_lease(ctx, owner="MCP", mode="deep_single_lane")
            failure_class = control.record_failure(ctx, "DEADLINE")
            self.assertEqual(failure_class, "DEADLINE")
            self.assertEqual(ctx.state, "REPLAN")

            control.begin_replan_wave(
                ctx,
                execution_mode="deep_single_lane",
                base_head="abc",
                worktree_fp="fp-2",
                contract_fp="",
                reason="replace packaging objective with provenance-only repair",
                objective="Verify wave objective provenance only",
            )

            run = ledger.get_run(ctx.run_id)
            provenance = ledger.wave_objective_provenance(ctx.run_id, wave_id=ctx.wave_id)
            self.assertEqual(run["objective"], "Build NSIS package")
            self.assertEqual(provenance["effective_objective"], "Verify wave objective provenance only")
            self.assertEqual(provenance["objective_revision"], 2)
            self.assertTrue(provenance["objective_changed_from_previous"])
            self.assertTrue(provenance["objective_hash_valid"])
            self.assertEqual(provenance["objective_source"], "replan_request")

    def test_case_02_mismatch_and_missing_package_evidence_never_become_green(self) -> None:
        snapshot = build_truth_snapshot(
            source={
                "base_head": "source-new",
                "source_fingerprint": "fp-source",
                "dirty_source_paths": ["renderer/panel.js"],
            },
            runtime_identity={
                "runtime_version": "0.4.3",
                "process_instance_id": "process",
                "server_instance_id": "server",
                "code_revision": "runtime-old",
                "tool_contract": {"profile": "smart-v3", "tool_count": 8},
            },
            orchestration={
                "run_id": "run",
                "wave_id": "wave",
                "state": "ACCEPTING",
                "base_head": "source-new",
                "worktree_fp": "fp-source",
            },
            objective={
                "run_initial_objective": "initial",
                "effective_objective": "current",
                "objective_revision": 2,
                "objective_hash_valid": True,
            },
            proof={"proof_id": "proof", "status": "passed"},
            checkpoint={},
            package=None,
        )

        self.assertEqual(snapshot["comparisons"]["runtime_code_vs_source_head"], "MISMATCHED")
        self.assertEqual(snapshot["comparisons"]["wave_base_vs_source_head"], "MATCHED")
        self.assertEqual(snapshot["comparisons"]["wave_worktree_vs_source_worktree"], "MATCHED")
        self.assertEqual(snapshot["package"]["state"], "UNKNOWN")
        self.assertEqual(snapshot["comparisons"]["package_revision_vs_source_head"], "UNKNOWN")
        self.assertTrue(snapshot["source"]["dirty"])

    def test_case_03_unknown_and_not_applicable_are_distinct_claim_states(self) -> None:
        self.assertEqual(match_state(None, "expected"), "UNKNOWN")
        self.assertEqual(match_state("", "expected"), "UNKNOWN")
        self.assertEqual(match_state("observed", None), "UNKNOWN")
        self.assertEqual(match_state("observed", "expected", applicable=False), "NOT_APPLICABLE")
        self.assertNotEqual(match_state(None, "expected"), "MATCHED")
        self.assertNotEqual(match_state("observed", "expected", applicable=False), "MATCHED")

    def test_case_04_active_run_from_another_task_is_never_adopted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                first = runtime.task_state.update({"objective": "Owned run", "status": "active"})
                ctx = runtime.orchestration_control.begin(
                    objective="Owned run",
                    task_id=str(first["task_id"]),
                    execution_mode="mcp_only",
                    base_head="test-head",
                    worktree_fp="test-worktree",
                )
                second = runtime.task_state.update({
                    "objective": "Different task",
                    "status": "active",
                    "new_task": True,
                })

                self.assertNotEqual(second["task_id"], first["task_id"])
                self.assertFalse(second.get("orchestration"))
                self.assertEqual(runtime.orchestration_ledger.current_active_run()["run_id"], ctx.run_id)
                self.assertIsNone(runtime.orchestration_ledger.current_active_run(task_id=str(second["task_id"])))
                self.assertFalse(runtime._reconcile_task_orchestration_projection())
                current = runtime.task_state.get()
                self.assertEqual(current["task_id"], second["task_id"])
                self.assertFalse(current.get("orchestration"))
            finally:
                runtime.close()

    def test_case_05_stale_run_reconciliation_preserves_live_owner(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            now = time.time()
            stale_run = ledger.create_run(objective="abandoned")
            stale_wave = ledger.create_wave(stale_run, execution_mode="mcp_only")
            live_run = ledger.create_run(objective="still running")
            ledger.create_wave(live_run, execution_mode="mcp_only")
            ledger.start_background_operation(
                operation_id="casebook-live-operation",
                server_instance_id="casebook-server",
                tool="agent_workflow",
                run_id=live_run,
                summary={},
            )

            candidates = ledger.stale_run_candidates(stale_after_seconds=3600, now=now + 7200)
            self.assertIn(stale_run, candidates)
            self.assertNotIn(live_run, candidates)
            self.assertEqual(ledger.reconcile_stale_runs(stale_after_seconds=3600, now=now + 7200), [stale_run])
            self.assertEqual(ledger.get_run(stale_run)["status"], "stale")
            self.assertEqual(ledger.get_run(live_run)["status"], "active")
            stale_wave_row = next(item for item in ledger.list_waves(stale_run) if item["wave_id"] == stale_wave)
            self.assertEqual(stale_wave_row["status"], "aborted")
            self.assertEqual(ledger.list_events(stale_run)[-1]["event_type"], "run_stale_reconciled")

    def test_case_06_final_acceptance_is_fail_closed_and_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                result = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "execute",
                    "objective": "casebook acceptance fixture",
                    "evaluation": {"provenance": "benchmark"},
                    "execution_mode": "mcp_only",
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                    "verification": "none",
                    "include_diff": False,
                })
                run_id = result["orchestration"]["run_id"]
                wave_id = result["orchestration"]["wave_id"]
                report = result["orchestration"]["completion_report"]
                self.assertEqual(result["orchestration"]["orchestration_state"], "ACCEPTING")
                self.assertEqual(report["accepted_or_not"], "PENDING_FINAL_ACCEPTANCE")
                self.assertTrue(report["operator_visible_required"])

                with self.assertRaises(ToolFailure) as wrong_wave:
                    runtime.task_control({
                        "action": "accept",
                        "run_id": run_id,
                        "wave_id": "not-the-current-wave",
                        "reason": "must fail closed",
                    })
                self.assertEqual(wrong_wave.exception.code, "ORCHESTRATION_WAVE_MISMATCH")

                runtime.orchestration_ledger.record_proof(
                    run_id=run_id,
                    wave_id=wave_id,
                    stage_id="casebook-acceptance",
                    stage_version="1",
                    input_fingerprint="casebook-acceptance-proof",
                    status="passed",
                    duration_ms=1,
                )

                accepted = runtime.task_control({
                    "action": "accept",
                    "run_id": run_id,
                    "wave_id": wave_id,
                    "reason": "casebook accepts the exact proven wave",
                })
                self.assertTrue(accepted["accepted"])
                self.assertEqual(accepted["orchestration"]["orchestration_state"], "CHECKPOINTED")
                self.assertEqual(accepted["completion_report"]["accepted_or_not"], "ACCEPTED")
                self.assertTrue(accepted["completion_report"]["operator_visible_required"])
            finally:
                runtime.close()

    def test_case_07_operator_projection_consumes_read_only_truth_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(temp), permission_mode="safe")
            try:
                task = runtime.task_state.ensure_started("casebook operator truth")
                ctx = runtime.orchestration_control.begin(
                    objective="casebook operator truth",
                    task_id=str(task["task_id"]),
                    execution_mode="mcp_only",
                    base_head="abc",
                    worktree_fp="fp",
                )
                runtime.task_state.set_orchestration_projection(ctx.projection(), event="casebook_truth_linked")
                handler = object.__new__(MCPHandler)
                handler._runtime = runtime
                projection = handler.control_orchestration_snapshot()
                truth = projection["truth_snapshot"]

                self.assertTrue(truth["read_only"])
                self.assertEqual(truth["runtime"]["process_instance_id"], runtime.process_instance_id)
                self.assertEqual(truth["runtime"]["server_instance_id"], runtime.server_instance_id)
                self.assertEqual(truth["runtime"]["tool_contract"]["profile"], "smart-v3")
                self.assertEqual(truth["runtime"]["tool_contract"]["tool_count"], 8)
                self.assertEqual(truth["orchestration"]["run_id"], ctx.run_id)
                self.assertEqual(truth["orchestration"]["wave_id"], ctx.wave_id)
                self.assertEqual(truth["orchestration"]["effective_objective"], "casebook operator truth")
                self.assertNotIn("auth_token", str(truth).lower())
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
