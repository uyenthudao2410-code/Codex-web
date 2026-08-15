from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from benchmarks.runtime_activation import build_snapshot
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.performance_trace import PerformanceTraceStore


class RuntimeActivationSnapshotTests(unittest.TestCase):
    def test_snapshot_uses_v5_required_idempotency_gate_and_durable_tta(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            trace = PerformanceTraceStore(root)
            trace.record(
                tool="workspace_context",
                started_monotonic=1.0,
                finished_monotonic=1.1,
                idempotency_eligible=False,
            )
            trace.record(
                tool="exec_command",
                started_monotonic=2.0,
                finished_monotonic=2.2,
                idempotency_eligible=True,
                idempotency_key_present=True,
                idempotency_policy="optional",
                idempotency_key_source="explicit",
                proof_cache_eligible=2,
                proof_cache_hits=1,
                proof_cache_misses=1,
                proof_cache_miss_reasons={"cold": 1},
                proof_cache_saved_ms=900,
                localization={
                    "semantic_available": True,
                    "query_count": 4,
                    "semantic_attempted": 4,
                    "semantic_handled": 3,
                    "text_fallback_queries": 1,
                },
                orchestration={"run_id": "run-measured", "route_resolved": "deterministic", "execution_mode": "mcp_only"},
            )
            trace.record(
                tool="agent_workflow",
                started_monotonic=3.0,
                finished_monotonic=3.2,
                ok=False,
                idempotency_eligible=True,
                idempotency_key_present=True,
                idempotency_policy="required",
                idempotency_key_source="derived",
                idempotency_operation="agent_workflow:execute",
                error_class="deadline",
                phase_timing={"source": "monotonic_local", "queue_ms": 5, "model_wall_ms": 25, "total_ms": 40},
                orchestration={"run_id": "run-measured", "route_resolved": "mini", "execution_mode": "bounded_candidate"},
            )
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(
                objective="measurement",
                metadata={"workflow": "diagnose", "phase": "run", "branch": "main"},
            )
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="head")
            ledger.append_event(
                run_id,
                wave_id=wave_id,
                event_type="route_selected",
                payload={"requested": "deterministic", "resolved": "deterministic"},
            )
            source_proof = ledger.record_proof(
                run_id=run_id,
                wave_id=wave_id,
                stage_id="verify:tests",
                stage_version="1",
                input_fingerprint="runtime-snapshot-fingerprint",
                status="passed",
                duration_ms=321,
            )
            ledger.append_event(
                run_id,
                wave_id=wave_id,
                event_type="proof_cache_hit",
                payload={
                    "stage_id": "verify:tests",
                    "stage_version": "1",
                    "input_fingerprint": "runtime-snapshot-fingerprint",
                    "source_proof_id": source_proof,
                },
            )
            ledger.record_checkpoint(
                run_id=run_id,
                wave_id=wave_id,
                git_head="head",
                proof_fingerprint="runtime-proof",
                status="accepted",
            )
            time.sleep(0.01)
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")
            snapshot = build_snapshot(root)
            performance = snapshot["performance"]
            self.assertEqual(snapshot["schema_version"], 3)
            self.assertEqual(performance["version"], 5)
            self.assertEqual(performance["idempotency_eligible_calls"], 2)
            self.assertEqual(performance["idempotency_eligible_key_calls"], 2)
            self.assertEqual(performance["idempotency_legacy_coverage"], 1.0)
            self.assertEqual(performance["idempotency_required_calls"], 1)
            self.assertEqual(performance["idempotency_required_key_calls"], 1)
            self.assertEqual(performance["idempotency_required_coverage"], 1.0)
            self.assertEqual(performance["idempotency_policy_epoch"], "task_epoch_v1")
            self.assertEqual(performance["idempotency_current_policy_required_calls"], 1)
            self.assertEqual(performance["idempotency_current_policy_required_key_calls"], 1)
            self.assertEqual(performance["idempotency_current_policy_required_coverage"], 1.0)
            self.assertEqual(
                performance["idempotency_current_policy_by_operation"]["agent_workflow:execute"]["keyed"],
                1,
            )
            self.assertEqual(performance["idempotency_optional_calls"], 1)
            self.assertEqual(performance["idempotency_optional_key_calls"], 1)
            self.assertEqual(performance["idempotency_auto_key_calls"], 1)
            self.assertEqual(performance["idempotency_coverage"], 1.0)
            self.assertEqual(performance["idempotency_coverage_source"], "required_current_policy")
            self.assertEqual(performance["idempotency_coverage_target"], 0.95)
            self.assertTrue(performance["idempotency_coverage_gate_passed"])
            self.assertEqual(performance["idempotency_v5_epoch"], "post_activation_only")
            self.assertEqual(performance["error_class_counts"], {"DEADLINE": 1})
            self.assertEqual(performance["error_classified_samples"], 1)
            self.assertEqual(performance["error_unknown_samples"], 0)
            self.assertEqual(performance["error_unknown_share"], 0.0)
            self.assertEqual(performance["phase_timing_samples"], 1)
            self.assertEqual(performance["phase_timing_ms"], {"queue_ms": 5, "model_wall_ms": 25, "total_ms": 40})
            self.assertTrue(performance["phase_timing_available"])
            self.assertEqual(performance["proof_cache_eligible"], 2)
            self.assertEqual(performance["proof_cache_hits"], 1)
            self.assertEqual(performance["proof_cache_misses"], 1)
            self.assertEqual(performance["proof_cache_miss_reasons"], {"cold": 1})
            self.assertEqual(performance["proof_cache_saved_ms"], 900)
            self.assertEqual(performance["localization_samples"], 1)
            self.assertEqual(performance["localization_queries"], 4)
            self.assertEqual(performance["lsp_available_rate"], 1.0)
            self.assertEqual(performance["lsp_hit_rate"], 0.75)
            self.assertEqual(performance["fallback_search_rate"], 0.25)
            self.assertEqual(snapshot["ledger"]["accepted_run_tta"]["n"], 1)
            self.assertEqual(
                snapshot["ledger"]["accepted_run_cohort_coverage"],
                {"total": 1, "complete": 1, "incomplete": 0, "complete_ratio": 1.0},
            )
            cohort = snapshot["ledger"]["accepted_run_cohorts"][0]
            self.assertEqual(cohort["entry_surface"], "agent_workflow")
            self.assertEqual(cohort["route"], "deterministic")
            self.assertEqual(cohort["task_class"], "diagnose")
            self.assertEqual(cohort["acceptance_status"], "accepted")
            self.assertEqual(cohort["repair_status"], "first_pass")
            opportunity = snapshot["ledger"]["proof_cache_opportunity"]
            self.assertEqual(opportunity["eligible"], 1)
            self.assertEqual(opportunity["hits"], 1)
            self.assertEqual(opportunity["saved_ms"], 321)
            self.assertTrue(opportunity["saved_ms_complete"])
            self.assertEqual(opportunity["run_relation"]["accepted_run_opportunities"], 1)
            self.assertEqual(opportunity["run_relation"]["accepted_checkpoint_opportunities"], 1)
            self.assertFalse(opportunity["raw_input_fingerprints_included"])
            self.assertEqual(snapshot["evidence_class"], "local_runtime_measurement_snapshot")

    def test_snapshot_keeps_v4_legacy_coverage_separate_from_v5_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_dir = root / ".coding-tools"
            state_dir.mkdir(parents=True)
            (state_dir / "performance.json").write_text(
                '{"version":4,"tool_calls":10,"errors":2,"idempotency_eligible_calls":5,"idempotency_eligible_key_calls":2}',
                encoding="utf-8",
            )
            performance = build_snapshot(root)["performance"]
            self.assertEqual(performance["version"], 4)
            self.assertEqual(performance["idempotency_legacy_coverage"], 0.4)
            self.assertEqual(performance["idempotency_required_calls"], 0)
            self.assertIsNone(performance["idempotency_required_coverage"])
            self.assertEqual(performance["idempotency_coverage"], 0.4)
            self.assertEqual(performance["idempotency_coverage_source"], "legacy_v4")
            self.assertEqual(performance["idempotency_v5_epoch"], "not_active")
            self.assertIsNone(performance["error_unknown_share"])
            self.assertFalse(performance["phase_timing_available"])

    def test_current_policy_epoch_preserves_cumulative_required_history_without_backfill(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_dir = root / ".coding-tools"
            state_dir.mkdir(parents=True)
            (state_dir / "performance.json").write_text(
                json.dumps({
                    "version": 5,
                    "tool_calls": 30,
                    "idempotency_required_calls": 30,
                    "idempotency_required_key_calls": 22,
                }),
                encoding="utf-8",
            )

            trace = PerformanceTraceStore(root)
            migrated = trace.record(
                tool="agent_workflow",
                started_monotonic=1.0,
                finished_monotonic=1.1,
                idempotency_eligible=True,
                idempotency_key_present=True,
                idempotency_policy="required",
                idempotency_key_source="derived",
                idempotency_operation="agent_workflow:execute",
            )
            self.assertEqual(migrated["idempotency_required_calls"], 31)
            self.assertEqual(migrated["idempotency_required_key_calls"], 23)
            self.assertEqual(migrated["idempotency_current_policy_required_calls"], 1)
            self.assertEqual(migrated["idempotency_current_policy_required_key_calls"], 1)
            self.assertEqual(
                migrated["idempotency_current_policy_by_operation"],
                {"agent_workflow:execute": {"calls": 1, "keyed": 1, "missing": 0, "missing_reasons": {}}},
            )

            performance = build_snapshot(root)["performance"]
            self.assertEqual(performance["idempotency_required_coverage"], round(23 / 31, 6))
            self.assertEqual(performance["idempotency_current_policy_required_coverage"], 1.0)
            self.assertEqual(performance["idempotency_coverage"], 1.0)
            self.assertEqual(performance["idempotency_coverage_source"], "required_current_policy")
            self.assertTrue(performance["idempotency_coverage_gate_passed"])

    def test_snapshot_marks_replanned_run_as_repaired_and_uses_latest_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(
                objective="repair measurement",
                metadata={"workflow": "bugfix", "phase": "run", "branch": "main"},
            )
            first_wave = ledger.create_wave(run_id, execution_mode="bounded_candidate", base_head="head")
            ledger.append_event(
                run_id,
                wave_id=first_wave,
                event_type="route_selected",
                payload={"requested": "mini", "resolved": "mini"},
            )
            ledger.finish_wave(first_wave, status="replanned")
            second_wave = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="head")
            ledger.append_event(
                run_id,
                wave_id=second_wave,
                event_type="route_selected",
                payload={"requested": "deterministic", "resolved": "deterministic"},
            )
            ledger.finish_wave(second_wave, status="accepted")
            ledger.finish_run(run_id, status="accepted")

            cohort = build_snapshot(root)["ledger"]["accepted_run_cohorts"][0]
            self.assertEqual(cohort["route"], "deterministic")
            self.assertEqual(cohort["task_class"], "bugfix")
            self.assertEqual(cohort["repair_status"], "repaired")

    def test_snapshot_keeps_missing_cohort_dimensions_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="legacy measurement")
            ledger.finish_run(run_id, status="accepted")

            snapshot = build_snapshot(root)
            self.assertEqual(
                snapshot["ledger"]["accepted_run_cohort_coverage"],
                {"total": 1, "complete": 0, "incomplete": 1, "complete_ratio": 0.0},
            )
            cohort = snapshot["ledger"]["accepted_run_cohorts"][0]
            self.assertEqual(cohort["entry_surface"], "unknown")
            self.assertEqual(cohort["route"], "unknown")
            self.assertEqual(cohort["task_class"], "unknown")
            self.assertEqual(cohort["repair_status"], "first_pass")


if __name__ == "__main__":
    unittest.main()
