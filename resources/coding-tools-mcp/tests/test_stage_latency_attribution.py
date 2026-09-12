from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.ledger_analysis import open_ledger_analysis_snapshot
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.stage_latency_attribution import STAGE_VOCABULARY, stage_latency_attribution_report


class StageLatencyAttributionTests(unittest.TestCase):
    @staticmethod
    def _host_metadata(*, source: str = "electron_pending_host_turn") -> dict[str, object]:
        marker: dict[str, object] = {"schema_version": 1, "source": source, "eligible": True}
        if source == "attested_chatweb_transport_trace":
            marker["content_free"] = True
        return {
            "host_correlation": marker,
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

    def test_acceptance_components_are_reported_without_polluting_legacy_stage_duration(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = self._record_complete_fixture(ledger, source_head="current-head")
            wave_id = ledger.list_waves(run_id)[-1]["wave_id"]
            ledger.append_event(run_id, wave_id=wave_id, event_type="observation_stage_anchor_recorded", payload={
                "stage": "acceptance", "source": "coding_mcp_runtime", "measurement": "stage_start_anchor",
                "clock_domain": "coding-mcp:fixture", "start_ms": 60.0, "observer_plane": "coding_mcp_runtime",
            })
            ledger.record_observation_span(run_id=run_id, wave_id=wave_id, span={
                "span_id": f"a2-acceptance-wait-v1:{wave_id}", "stage": "acceptance",
                "source": "coding_mcp_runtime", "measurement": "acceptance_wait",
                "clock_domain": "coding-mcp:fixture", "start_ms": 60.0, "end_ms": 70.0,
            })
            ledger.record_observation_span(run_id=run_id, wave_id=wave_id, span={
                "span_id": f"a2-controller-processing-v1:{wave_id}", "stage": "acceptance",
                "source": "coding_mcp_runtime", "measurement": "controller_processing",
                "clock_domain": "coding-mcp:fixture", "start_ms": 70.0, "end_ms": 75.0,
            })
            ledger.record_checkpoint(run_id=run_id, wave_id=wave_id, git_head="current-head", proof_fingerprint="proof", status="accepted")
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = stage_latency_attribution_report(snapshot.ledger, source_head="current-head", min_decision_cohort=1)

            attribution = report["acceptance_attribution"]
            self.assertEqual(attribution["accepted_current_source_runs"], 1)
            self.assertEqual(attribution["controller_processing_ms"]["coverage"], 1.0)
            self.assertEqual(attribution["controller_processing_ms"]["duration_ms"]["p50"], 5.0)
            self.assertEqual(attribution["acceptance_wait_ms"]["coverage"], 1.0)
            self.assertEqual(attribution["acceptance_wait_ms"]["duration_ms"]["p50"], 10.0)
            acceptance_row = next(item for item in report["stage_completeness"]["rows"] if item["stage"] == "acceptance")
            self.assertEqual(acceptance_row["duration_ms"]["observed_span_count"], 1)
            self.assertTrue(attribution["cross_clock_subtraction_forbidden"])

    def test_attested_transport_binding_contributes_acceptance_without_report_visible_span(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(
                objective="natural transport-style fixture",
                metadata=self._host_metadata(source="attested_chatweb_transport_trace"),
            )
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="current-head")
            for ordinal, stage in enumerate(("preflight", "localization", "routing", "execution", "proof", "acceptance")):
                ledger.record_observation_span(run_id=run_id, wave_id=wave_id, span={
                    "span_id": f"stage-{stage}", "stage": stage, "source": "coding_mcp_runtime",
                    "measurement": "observed_stage_duration", "clock_domain": "coding-mcp:fixture",
                    "start_ms": ordinal * 10.0, "end_ms": ordinal * 10.0 + 5.0,
                })
            ledger.append_event(run_id, wave_id=wave_id, event_type="observation_stage_anchor_recorded", payload={
                "stage": "acceptance", "source": "coding_mcp_runtime", "measurement": "stage_start_anchor",
                "clock_domain": "coding-mcp:fixture", "start_ms": 60.0,
            })
            ledger.record_observation_span(run_id=run_id, wave_id=wave_id, span={
                "span_id": f"a2-acceptance-wait-v1:{wave_id}", "stage": "acceptance",
                "source": "coding_mcp_runtime", "measurement": "acceptance_wait",
                "clock_domain": "coding-mcp:fixture", "start_ms": 60.0, "end_ms": 70.0,
            })
            ledger.record_observation_span(run_id=run_id, wave_id=wave_id, span={
                "span_id": f"a2-controller-processing-v1:{wave_id}", "stage": "acceptance",
                "source": "coding_mcp_runtime", "measurement": "controller_processing",
                "clock_domain": "coding-mcp:fixture", "start_ms": 70.0, "end_ms": 75.0,
            })
            ledger.record_checkpoint(
                run_id=run_id, wave_id=wave_id, git_head="current-head", proof_fingerprint="proof", status="accepted"
            )
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = stage_latency_attribution_report(snapshot.ledger, source_head="current-head", min_decision_cohort=1)

            self.assertEqual(report["cohort"]["current_source_eligible_runs"], 1)
            self.assertEqual(report["host_to_run_binding"]["exact_ledger_binding_runs"], 1)
            self.assertEqual(report["host_to_run_binding"]["coverage"], 1.0)
            self.assertEqual(report["acceptance_attribution"]["accepted_current_source_runs"], 1)
            self.assertEqual(report["acceptance_attribution"]["controller_processing_ms"]["coverage"], 1.0)
            self.assertEqual(report["acceptance_attribution"]["acceptance_wait_ms"]["coverage"], 1.0)
            visible = next(item for item in report["stage_completeness"]["rows"] if item["stage"] == "report_visible")
            self.assertEqual(visible["recorded_runs"], 0)
            self.assertEqual(report["status"], "STAGE_COMPLETENESS_BELOW_THRESHOLD")

    def test_acceptance_wait_remains_unknown_when_anchor_and_controller_clocks_differ(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = self._record_complete_fixture(ledger, source_head="current-head")
            wave_id = ledger.list_waves(run_id)[-1]["wave_id"]
            ledger.append_event(run_id, wave_id=wave_id, event_type="observation_stage_anchor_recorded", payload={
                "stage": "acceptance", "source": "coding_mcp_runtime", "measurement": "stage_start_anchor",
                "clock_domain": "coding-mcp:old", "start_ms": 60.0,
            })
            ledger.record_observation_span(run_id=run_id, wave_id=wave_id, span={
                "span_id": f"a2-controller-processing-v1:{wave_id}", "stage": "acceptance",
                "source": "coding_mcp_runtime", "measurement": "controller_processing",
                "clock_domain": "coding-mcp:new", "start_ms": 70.0, "end_ms": 75.0,
            })
            ledger.record_checkpoint(run_id=run_id, wave_id=wave_id, git_head="current-head", proof_fingerprint="proof", status="accepted")
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = stage_latency_attribution_report(snapshot.ledger, source_head="current-head", min_decision_cohort=1)

            wait = report["acceptance_attribution"]["acceptance_wait_ms"]
            self.assertEqual(wait["same_clock_eligible_runs"], 0)
            self.assertEqual(wait["cross_clock_excluded_runs"], 1)
            self.assertIsNone(wait["coverage"])
            self.assertIsNone(wait["duration_ms"]["p50"])


if __name__ == "__main__":
    unittest.main()
