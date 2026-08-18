from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.evaluation_report import current_ledger_baseline_report, evaluation_plane_report
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.solution_economics import (
    record_solution_shadow,
    solution_shadow_population_report,
    solution_shadow_run_report,
)


def recommendation(recommendation_id: str, *, risk: str = "low") -> dict[str, object]:
    return {
        "recommendation_id": recommendation_id,
        "candidate_solution_scope": "localized_file",
        "estimated_touched_surface": {"files": 1, "symbols": 2},
        "root_cause_confidence": "high",
        "oracle_strength": "strong",
        "expected_repair_risk": risk,
        "smallest_causal_solution": {
            "scope": "localized_symbol",
            "estimated_touched_surface": {"files": 1, "symbols": 1},
        },
    }


class SolutionEconomicsShadowTests(unittest.TestCase):
    def test_record_is_task_level_pre_write_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="feature", metadata={"workflow": "feature"})
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            first = record_solution_shadow(ledger, run_id=run_id, wave_id=wave_id, recommendation=recommendation("rec-1"))
            duplicate = record_solution_shadow(ledger, run_id=run_id, wave_id=wave_id, recommendation=recommendation("rec-1"))
            self.assertTrue(first["recorded"])
            self.assertFalse(duplicate["recorded"])
            ledger.append_event(run_id, wave_id=wave_id, event_type="write_lease_acquired")
            replay_after_write = record_solution_shadow(ledger, run_id=run_id, wave_id=wave_id, recommendation=recommendation("rec-1"))
            self.assertFalse(replay_after_write["recorded"])
            with self.assertRaisesRegex(ValueError, "already recorded"):
                record_solution_shadow(ledger, run_id=run_id, wave_id=wave_id, recommendation=recommendation("rec-2"))

    def test_late_or_ineligible_recommendation_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="bug", metadata={"workflow": "bugfix"})
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            ledger.append_event(run_id, wave_id=wave_id, event_type="write_lease_acquired")
            with self.assertRaisesRegex(ValueError, "before the first write lease"):
                record_solution_shadow(ledger, run_id=run_id, wave_id=wave_id, recommendation=recommendation("late"))

            other = ledger.create_run(objective="diagnose", metadata={"workflow": "diagnose"})
            other_wave = ledger.create_wave(other, execution_mode="mcp_only")
            with self.assertRaisesRegex(ValueError, "feature and bugfix"):
                record_solution_shadow(ledger, run_id=other, wave_id=other_wave, recommendation=recommendation("other"))

    def test_outcome_join_preserves_unknown_and_uses_durable_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="bugfix", metadata={"workflow": "bugfix"})
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            record_solution_shadow(ledger, run_id=run_id, wave_id=wave_id, recommendation=recommendation("joined"))
            ledger.append_event(run_id, wave_id=wave_id, event_type="write_lease_acquired")
            ledger.record_proof(
                run_id=run_id,
                wave_id=wave_id,
                stage_id="tests",
                stage_version="v1",
                input_fingerprint="fp",
                status="passed",
                duration_ms=25,
            )
            ledger.record_observation_span(run_id=run_id, wave_id=wave_id, span={
                "span_id": "local", "stage": "local_execution", "source": "test", "measurement": "observed",
                "clock_domain": "test:1", "start_ms": 10, "end_ms": 30,
            })
            ledger.record_observation_span(run_id=run_id, wave_id=wave_id, span={
                "span_id": "wait", "stage": "wait", "source": "test", "measurement": "observed",
                "clock_domain": "test:1", "start_ms": 30, "end_ms": 35,
            })
            ledger.record_quality_outcome(run_id=run_id, wave_id=wave_id, outcome={
                "source": "test", "oracle_pass": True, "critical_defect_count": 0, "manual_fix_required": False,
            })
            ledger.record_checkpoint(
                run_id=run_id,
                wave_id=wave_id,
                git_head="head",
                proof_fingerprint="proof",
                status="accepted",
                metadata={"accepted_files": {"complete": True, "count": 2, "files": [], "total_bytes": 0, "incomplete_reasons": []}},
            )
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")

            report = solution_shadow_run_report(ledger, run_id)
            outcome = report["outcome"]
            self.assertTrue(report["pre_mutation"]["recorded_before_first_write"])
            self.assertTrue(outcome["first_pass_accepted"])
            self.assertFalse(outcome["repair"]["repaired"])
            self.assertEqual(outcome["touched_surface"]["files"], 2)
            self.assertIsNone(outcome["touched_surface"]["lines"])
            self.assertIsNone(outcome["touched_surface"]["symbols"])
            self.assertEqual(outcome["proof_cost"]["duration_ms"], 25)
            self.assertEqual(outcome["local_execution_ms"], 20.0)
            self.assertEqual(outcome["wait_ms"], 5.0)
            self.assertFalse(outcome["manual_intervention"])

    def test_population_is_descriptive_only_and_exposes_repair_signal_buckets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            cases = (("low", "representative"), ("high", "representative"), ("medium", "synthetic"))
            for index, (risk, provenance) in enumerate(cases):
                run_id = ledger.create_run(
                    objective=f"feature-{risk}",
                    metadata={"workflow": "feature", "evaluation": {"provenance": provenance}},
                )
                wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
                record_solution_shadow(ledger, run_id=run_id, wave_id=wave_id, recommendation=recommendation(f"rec-{risk}", risk=risk))
                if risk == "high":
                    ledger.append_event(run_id, wave_id=wave_id, event_type="failure_observed", state_before="EXECUTING", state_after="REPLAN")
                    ledger.finish_wave(wave_id, status="replanned")
                    wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
                ledger.finish_wave(wave_id, status="accepted")
                ledger.finish_run(run_id, status="accepted")

            population = solution_shadow_population_report(ledger)
            self.assertEqual(population["cohort"]["terminal_shadow_tasks"], 3)
            self.assertEqual(population["cohort"]["terminal_provenance_counts"], {"representative": 2, "synthetic": 1})
            self.assertEqual(population["cohort"]["representative_terminal_shadow_tasks"], 2)
            self.assertEqual(population["cohort"]["representative_repaired_tasks"], 1)
            self.assertEqual(population["cohort"]["representative_nonrepaired_tasks"], 1)
            risks = {row["value"]: row for row in population["by_signal"]["expected_repair_risk"]}
            self.assertEqual(risks["low"]["repair_rate"], 0.0)
            self.assertEqual(risks["high"]["repair_rate"], 1.0)
            self.assertEqual(risks["medium"]["representative_sample_count"], 0)
            self.assertEqual(risks["low"]["representative_repair_rate"], 0.0)
            self.assertEqual(risks["high"]["representative_repair_rate"], 1.0)
            self.assertTrue(population["representative_predictor_variation"]["expected_repair_risk"])
            self.assertEqual(population["p4_gate"]["status"], "representative_descriptive_comparison_available_but_unvalidated")
            self.assertFalse(population["p4_gate"]["can_answer_which_signals_predict_repair"])
            self.assertFalse(population["p4_gate"]["automatic_policy_activation"])
            self.assertTrue(population["policy"]["loc_is_explanatory_not_objective"])
            self.assertTrue(population["policy"]["predictive_promotion_requires_representative_provenance"])

    def test_missing_evaluation_provenance_is_unlabeled_not_representative(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="organic feature", metadata={"workflow": "feature"})
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            record_solution_shadow(ledger, run_id=run_id, wave_id=wave_id, recommendation=recommendation("unlabeled"))
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")

            report = solution_shadow_run_report(ledger, run_id)
            population = solution_shadow_population_report(ledger)
            self.assertEqual(report["evidence_provenance"], "unlabeled")
            self.assertEqual(population["cohort"]["terminal_provenance_counts"], {"unlabeled": 1})
            self.assertEqual(population["cohort"]["representative_terminal_shadow_tasks"], 0)
            self.assertFalse(population["p4_gate"]["can_answer_which_signals_predict_repair"])

    def test_task_control_and_reports_expose_shadow_without_new_public_tool(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(temp)
            runtime = Runtime(root, permission_mode="dangerous")
            runtime._orchestration_workspace_identity = lambda _path: {"branch": "test", "base_head": "head", "worktree_fp": "worktree"}
            try:
                ctx, _ = runtime._agent_orchestration_context(
                    {"workflow": "feature", "phase": "prepare", "execution_mode": "mcp_only"},
                    objective="shadow feature",
                )
                result = runtime.task_control({
                    "action": "solution_shadow",
                    "run_id": ctx.run_id,
                    "wave_id": ctx.wave_id,
                    "solution_shadow_recommendation": recommendation("runtime-rec"),
                })
                self.assertTrue(result["recording"]["recorded"])
                self.assertEqual(result["solution_shadow"]["recommendation"]["recommendation_id"], "runtime-rec")
                self.assertEqual(len(runtime.exposed_tool_names()), 8)
                baseline = current_ledger_baseline_report(root)
                self.assertEqual(baseline["solution_economics_shadow"]["cohort"]["shadow_tasks"], 1)
                plane = evaluation_plane_report(root, run_id=ctx.run_id)
                self.assertEqual(plane["solution_economics_shadow"]["status"], "observed")
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
