from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.ledger_analysis import open_ledger_analysis_snapshot
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.stage_latency_attribution import STAGE_VOCABULARY, stage_latency_attribution_report


class StageLatencyAttributionTests(unittest.TestCase):
    @staticmethod
    def _host_metadata() -> dict[str, object]:
        return {
            "host_correlation": {"schema_version": 1, "source": "electron_pending_host_turn", "eligible": True},
            "evaluation": {"provenance": "representative", "turn_id": "turn-a", "trace_id": "trace-a"},
        }

    def _record_complete_fixture(self, ledger: OrchestrationLedger, *, source_head: str) -> str:
        run_id = ledger.create_run(objective="fixture only", metadata=self._host_metadata())
        wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head=source_head)
        for ordinal, stage in enumerate(STAGE_VOCABULARY):
            ledger.record_observation_span(
                run_id=run_id,
                wave_id=wave_id,
                span={
                    "span_id": f"span-{stage}",
                    "stage": stage,
                    "source": "electron_chatgpt_dom" if stage == "report_visible" else "coding_mcp",
                    "measurement": "observed_host_visible" if stage == "report_visible" else "observed_stage_duration",
                    "clock_domain": "electron-renderer:fixture" if stage == "report_visible" else "coding-mcp:fixture",
                    "start_ms": ordinal * 10,
                    "end_ms": ordinal * 10 + 5,
                    **({"turn_id": "turn-a", "trace_id": "trace-a", "observer_plane": "electron_chatgpt_dom"} if stage == "report_visible" else {}),
                },
            )
        return run_id

    def test_uses_one_immutable_facts_snapshot_and_reports_complete_fixture_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            self._record_complete_fixture(ledger, source_head="current-head")
            with open_ledger_analysis_snapshot(root) as snapshot:
                self.assertEqual(snapshot.statement_count, 8)
                report = stage_latency_attribution_report(snapshot.ledger, source_head="current-head", min_decision_cohort=1)
                self.assertEqual(snapshot.statement_count, 8)
                self.assertEqual(snapshot.live_backup_connections, 1)

            self.assertEqual(report["status"], "MEASUREMENT_COVERAGE_READY")
            self.assertEqual(report["host_to_run_binding"]["coverage"], 1.0)
            self.assertEqual(report["stage_completeness"]["coverage"], 1.0)
            self.assertEqual(report["unrecognized_span_records"], 0)
            self.assertTrue(report["policy"]["cross_clock_timestamp_subtraction_forbidden"])
            self.assertTrue(report["policy"]["missing_stage_is_not_zero_duration"])
            self.assertEqual(report["tail_mechanism_ranking"]["status"], "DESCRIPTIVE_RANKING_READY")

    def test_missing_host_identity_never_uses_timestamp_proximity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="fixture only", metadata=self._host_metadata())
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="current-head")
            ledger.record_observation_span(
                run_id=run_id,
                wave_id=wave_id,
                span={
                    "span_id": "visible", "stage": "report_visible", "source": "electron_chatgpt_dom",
                    "measurement": "observed_host_visible", "clock_domain": "electron-renderer:fixture",
                    "start_ms": 100, "end_ms": 125, "turn_id": "different-turn", "trace_id": "different-trace",
                    "observer_plane": "electron_chatgpt_dom",
                },
            )
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = stage_latency_attribution_report(snapshot.ledger, source_head="current-head", min_decision_cohort=1)

            self.assertEqual(report["status"], "HOST_BINDING_COVERAGE_BELOW_THRESHOLD")
            self.assertEqual(report["host_to_run_binding"]["exact_ledger_binding_runs"], 0)
            self.assertTrue(report["host_to_run_binding"]["timestamp_proximity_inference_forbidden"])
            self.assertEqual(report["stage_completeness"]["coverage"], 0.142857)
            self.assertEqual(report["stage_completeness"]["rows"][0]["stage"], "turn_received")
            self.assertEqual(report["stage_completeness"]["rows"][0]["expected_runs"], 0)
            self.assertNotIn("turn_received", report["stage_completeness"]["stages_with_missingness_above_threshold"])

    def test_unrecognized_legacy_stages_are_descriptive_not_rewritten_or_counted_as_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="fixture only", metadata=self._host_metadata())
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="current-head")
            ledger.record_observation_span(
                run_id=run_id,
                wave_id=wave_id,
                span={
                    "span_id": "legacy", "stage": "host_turn_span", "source": "electron_chatgpt_dom",
                    "measurement": "observed_host_visible", "clock_domain": "electron-renderer:fixture",
                    "start_ms": 1, "end_ms": 2, "turn_id": "turn-a", "trace_id": "trace-a",
                },
            )
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = stage_latency_attribution_report(snapshot.ledger, source_head="current-head", min_decision_cohort=1)

            self.assertEqual(report["unrecognized_span_records"], 1)
            self.assertEqual(report["stage_completeness"]["recorded_stage_observations"], 0)
            self.assertEqual(report["status"], "HOST_BINDING_COVERAGE_BELOW_THRESHOLD")
            self.assertTrue(report["policy"]["unrecognized_legacy_stage_is_not_rewritten"])


if __name__ == "__main__":
    unittest.main()
