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
    record_solution_shadow_patch_surface,
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


def record_repair_patch(
    ledger: OrchestrationLedger,
    *,
    run_id: str,
    wave_id: str,
    label: str,
) -> None:
    record_solution_shadow_patch_surface(
        ledger,
        run_id=run_id,
        wave_id=wave_id,
        patch_result={
            "dry_run": False,
            "additions": 1,
            "removals": 0,
            "affected_files": [{"path": f"src/{label}.py", "operation": "update"}],
        },
    )


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
            self.assertFalse(outcome["repair"]["workflow_replanned"])
            self.assertFalse(outcome["repair"]["proof_only_replan"])
            self.assertEqual(outcome["repair"]["label_method"], "post_replan_applied_patch_delta_v1")
            self.assertEqual(outcome["touched_surface"]["files"], 2)
            self.assertIsNone(outcome["touched_surface"]["lines"])
            self.assertIsNone(outcome["touched_surface"]["symbols"])
            self.assertEqual(outcome["proof_cost"]["duration_ms"], 25)
            self.assertEqual(outcome["local_execution_ms"], 20.0)
            self.assertEqual(outcome["wait_ms"], 5.0)
            self.assertFalse(outcome["manual_intervention"])

    def test_applied_patch_surface_is_content_free_and_requires_receipt_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="feature", metadata={"workflow": "feature"})
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            record_solution_shadow(ledger, run_id=run_id, wave_id=wave_id, recommendation=recommendation("surface"))
            recorded = record_solution_shadow_patch_surface(
                ledger,
                run_id=run_id,
                wave_id=wave_id,
                patch_result={
                    "dry_run": False,
                    "additions": 4,
                    "removals": 2,
                    "affected_files": [{"path": "src/private_name.py", "operation": "update"}],
                },
            )
            self.assertTrue(recorded["recorded"])
            event = ledger.list_events(run_id)[-1]
            self.assertNotIn("private_name", str(event["payload"]))
            ledger.record_checkpoint(
                run_id=run_id,
                wave_id=wave_id,
                git_head="head",
                proof_fingerprint="proof",
                status="accepted",
                metadata={"accepted_files": {
                    "complete": True,
                    "count": 1,
                    "files": [{"path": "src/private_name.py", "state": "file", "sha256": "x"}],
                    "total_bytes": 1,
                    "incomplete_reasons": [],
                }},
            )
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")
            surface = solution_shadow_run_report(ledger, run_id)["outcome"]["touched_surface"]
            self.assertEqual(surface["lines"], 6)
            self.assertEqual(surface["observed_patch_additions"], 4)
            self.assertEqual(surface["observed_patch_removals"], 2)
            self.assertTrue(surface["line_coverage_complete"])
            self.assertEqual(surface["lines_measurement"], "applied_patch_delta_complete_v1")

            other = ledger.create_run(objective="feature2", metadata={"workflow": "feature"})
            other_wave = ledger.create_wave(other, execution_mode="mcp_only")
            record_solution_shadow(ledger, run_id=other, wave_id=other_wave, recommendation=recommendation("partial"))
            record_solution_shadow_patch_surface(
                ledger,
                run_id=other,
                wave_id=other_wave,
                patch_result={"dry_run": False, "additions": 1, "removals": 1, "affected_files": [{"path": "a.py"}]},
            )
            ledger.record_checkpoint(
                run_id=other,
                wave_id=other_wave,
                git_head="head",
                proof_fingerprint="proof",
                status="accepted",
                metadata={"accepted_files": {
                    "complete": True,
                    "count": 2,
                    "files": [{"path": "a.py"}, {"path": "command_generated.py"}],
                    "total_bytes": 2,
                    "incomplete_reasons": [],
                }},
            )
            ledger.finish_wave(other_wave, status="accepted")
            ledger.finish_run(other, status="accepted")
            partial = solution_shadow_run_report(ledger, other)["outcome"]["touched_surface"]
            self.assertIsNone(partial["lines"])
            self.assertEqual(partial["observed_patch_line_changes"], 2)
            self.assertFalse(partial["line_coverage_complete"])
            self.assertEqual(partial["lines_measurement"], "applied_patch_delta_incomplete_v1")

    def test_repair_label_requires_source_rework_after_replan(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))

            proof_only = ledger.create_run(
                objective="proof-only replan",
                metadata={"workflow": "bugfix", "evaluation": {"provenance": "representative"}},
            )
            proof_wave = ledger.create_wave(proof_only, execution_mode="mcp_only")
            record_solution_shadow(
                ledger,
                run_id=proof_only,
                wave_id=proof_wave,
                recommendation=recommendation("proof-only", risk="low"),
            )
            ledger.append_event(
                proof_only,
                wave_id=proof_wave,
                event_type="failure_observed",
                state_before="PROVING",
                state_after="REPLAN",
            )
            ledger.finish_wave(proof_wave, status="replanned")
            proof_wave = ledger.create_wave(proof_only, execution_mode="mcp_only")
            ledger.finish_wave(proof_wave, status="accepted")
            ledger.finish_run(proof_only, status="accepted")

            source_repair = ledger.create_run(
                objective="source repair",
                metadata={"workflow": "bugfix", "evaluation": {"provenance": "representative"}},
            )
            source_wave = ledger.create_wave(source_repair, execution_mode="mcp_only")
            record_solution_shadow(
                ledger,
                run_id=source_repair,
                wave_id=source_wave,
                recommendation=recommendation("source-repair", risk="high"),
            )
            ledger.append_event(
                source_repair,
                wave_id=source_wave,
                event_type="failure_observed",
                state_before="PROVING",
                state_after="REPLAN",
            )
            ledger.finish_wave(source_wave, status="replanned")
            source_wave = ledger.create_wave(source_repair, execution_mode="mcp_only")
            record_repair_patch(
                ledger,
                run_id=source_repair,
                wave_id=source_wave,
                label="source_repair",
            )
            ledger.finish_wave(source_wave, status="accepted")
            ledger.finish_run(source_repair, status="accepted")

            proof_report = solution_shadow_run_report(ledger, proof_only)
            source_report = solution_shadow_run_report(ledger, source_repair)
            self.assertTrue(proof_report["outcome"]["repair"]["workflow_replanned"])
            self.assertTrue(proof_report["outcome"]["repair"]["proof_only_replan"])
            self.assertFalse(proof_report["outcome"]["repair"]["repaired"])
            self.assertEqual(proof_report["outcome"]["repair"]["post_replan_patch_surface_events"], 0)
            self.assertTrue(source_report["outcome"]["repair"]["workflow_replanned"])
            self.assertFalse(source_report["outcome"]["repair"]["proof_only_replan"])
            self.assertTrue(source_report["outcome"]["repair"]["repaired"])
            self.assertEqual(source_report["outcome"]["repair"]["post_replan_patch_surface_events"], 1)

            population = solution_shadow_population_report(ledger)
            self.assertEqual(population["cohort"]["representative_repaired_tasks"], 1)
            self.assertEqual(population["cohort"]["representative_nonrepaired_tasks"], 1)
            self.assertEqual(
                population["predictive_validation"]["repair_label_method"],
                "post_replan_applied_patch_delta_v1",
            )
            self.assertTrue(population["policy"]["repair_label_uses_post_replan_patch_surface"])
            self.assertTrue(population["policy"]["workflow_replan_is_not_solution_repair"])

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
                    record_repair_patch(ledger, run_id=run_id, wave_id=wave_id, label=f"repair_{risk}")
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
            self.assertFalse(population["representative_predictor_variation"]["smallest_causal_solution_scope"])
            self.assertEqual(population["p4_gate"]["status"], "representative_descriptive_comparison_available_but_unvalidated")
            self.assertFalse(population["p4_gate"]["can_answer_which_signals_predict_repair"])
            self.assertFalse(population["p4_gate"]["automatic_policy_activation"])
            self.assertTrue(population["policy"]["loc_is_explanatory_not_objective"])
            self.assertTrue(population["policy"]["predictive_promotion_requires_representative_provenance"])

    def test_predictive_gate_requires_out_of_sample_gain_and_familywise_separation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            for index in range(24):
                repaired = index >= 12
                risk = "high" if repaired else "low"
                run_id = ledger.create_run(
                    objective=f"feature-{index}",
                    metadata={"workflow": "feature", "evaluation": {"provenance": "representative"}},
                )
                wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
                record_solution_shadow(
                    ledger,
                    run_id=run_id,
                    wave_id=wave_id,
                    recommendation=recommendation(f"predict-{index}", risk=risk),
                )
                if repaired:
                    ledger.append_event(
                        run_id,
                        wave_id=wave_id,
                        event_type="failure_observed",
                        state_before="EXECUTING",
                        state_after="REPLAN",
                    )
                    ledger.finish_wave(wave_id, status="replanned")
                    wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
                    record_repair_patch(
                        ledger,
                        run_id=run_id,
                        wave_id=wave_id,
                        label=f"predict_{index}",
                    )
                ledger.finish_wave(wave_id, status="accepted")
                ledger.finish_run(run_id, status="accepted")

            population = solution_shadow_population_report(ledger)
            validation = population["predictive_validation"]
            self.assertIn("expected_repair_risk", validation["validated_signals"])
            self.assertGreater(validation["signals"]["expected_repair_risk"]["leave_one_out_brier_gain"], 0)
            self.assertTrue(validation["signals"]["expected_repair_risk"]["separated_bucket_pairs"])
            self.assertTrue(population["p4_gate"]["can_answer_which_signals_predict_repair"])
            self.assertEqual(population["p4_gate"]["status"], "predictive_signal_validation_available")
            self.assertFalse(population["p4_gate"]["automatic_policy_activation"])
            self.assertFalse(population["policy"]["p5_automatic_start"])

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

    def test_frozen_chatgpt_task_control_schema_can_record_the_same_shadow_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(temp)
            runtime = Runtime(root, permission_mode="dangerous")
            runtime._orchestration_workspace_identity = lambda _path: {"branch": "test", "base_head": "head", "worktree_fp": "worktree"}
            try:
                ctx, _ = runtime._agent_orchestration_context(
                    {"workflow": "bugfix", "phase": "prepare", "execution_mode": "mcp_only"},
                    objective="frozen schema shadow bugfix",
                )
                result = runtime.task_control({
                    "action": "update",
                    "run_id": ctx.run_id,
                    "wave_id": ctx.wave_id,
                    "payload": {
                        "extension": "solution_shadow_v1",
                        "recommendation": recommendation("frozen-runtime-rec"),
                    },
                })
                self.assertTrue(result["recording"]["recorded"])
                self.assertEqual(result["transport"], "frozen_chatgpt_schema_extension_v1")
                self.assertEqual(result["solution_shadow"]["recommendation"]["recommendation_id"], "frozen-runtime-rec")
                self.assertFalse(result["production_behavior_changed"])
                self.assertEqual(len(runtime.exposed_tool_names()), 8)
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
