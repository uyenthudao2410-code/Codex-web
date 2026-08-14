from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from benchmarks.runtime_activation import build_snapshot
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.performance_trace import PerformanceTraceStore


class RuntimeActivationSnapshotTests(unittest.TestCase):
    def test_snapshot_uses_explicit_idempotency_denominator_and_durable_tta(self) -> None:
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
                proof_cache_hits=1,
                proof_cache_saved_ms=900,
                orchestration={"run_id": "run-measured", "route_resolved": "deterministic", "execution_mode": "mcp_only"},
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
            time.sleep(0.01)
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")
            snapshot = build_snapshot(root)
            performance = snapshot["performance"]
            self.assertEqual(snapshot["schema_version"], 2)
            self.assertEqual(performance["version"], 3)
            self.assertEqual(performance["idempotency_eligible_calls"], 1)
            self.assertEqual(performance["idempotency_eligible_key_calls"], 1)
            self.assertEqual(performance["idempotency_coverage"], 1.0)
            self.assertEqual(performance["proof_cache_saved_ms"], 900)
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
            self.assertEqual(snapshot["evidence_class"], "local_runtime_measurement_snapshot")

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
