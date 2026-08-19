from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.operations_analytics import operations_analytics
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.usage_events import build_usage_event


class OperationsAnalyticsTests(unittest.TestCase):
    def _set_times(self, ledger: OrchestrationLedger, run_id: str, started: str, finished: str) -> None:
        with ledger._lock, ledger._connect() as connection:
            connection.execute("UPDATE runs SET started_at=?, finished_at=? WHERE run_id=?", (started, finished, run_id))

    def test_projection_aggregates_outcomes_tta_replans_and_coverage_without_zero_imputation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            ledger = OrchestrationLedger(Path(raw))
            first = ledger.create_run(objective="first pass", metadata={"evaluation": {"controller": {"monetary_cost": 0.02, "source": "client_reported"}}})
            first_wave = ledger.create_wave(first, execution_mode="mcp_only")
            ledger.finish_wave(first_wave, status="accepted")
            ledger.record_usage_event(
                run_id=first,
                wave_id=first_wave,
                delegation_id="provider-1",
                usage_event=build_usage_event(
                    run_id=first,
                    wave_id=first_wave,
                    delegation_id="provider-1",
                    provider_id="openai",
                    model_id="gpt-test",
                    status="completed",
                    source="opencode:provider_dispatch",
                    input_tokens=100,
                    cached_input_tokens=0,
                    output_tokens=20,
                    reasoning_output_tokens=0,
                    provider_cost=0.01,
                ),
            )
            ledger.finish_run(first, status="accepted")
            self._set_times(ledger, first, "2026-08-19T07:59:00Z", "2026-08-19T07:59:10Z")

            repaired = ledger.create_run(objective="replanned")
            wave_a = ledger.create_wave(repaired, execution_mode="mcp_only")
            ledger.finish_wave(wave_a, status="replanned")
            wave_b = ledger.create_wave(repaired, execution_mode="mcp_only")
            ledger.finish_wave(wave_b, status="accepted")
            ledger.finish_run(repaired, status="accepted")
            self._set_times(ledger, repaired, "2026-08-19T07:50:00Z", "2026-08-19T07:52:00Z")

            aborted = ledger.create_run(objective="aborted")
            aborted_wave = ledger.create_wave(aborted, execution_mode="mcp_only")
            ledger.finish_wave(aborted_wave, status="aborted")
            ledger.finish_run(aborted, status="aborted")
            self._set_times(ledger, aborted, "2026-08-19T07:40:00Z", "2026-08-19T07:41:00Z")

            result = operations_analytics(ledger, performance={"run_metrics": {first: {"tool_calls": 7}}}, days=7, now="2026-08-19T08:00:00Z")
            self.assertEqual(result["measurement"], "accepted_result_operations_v1")
            self.assertEqual(result["missing_measurement_policy"], "unknown_not_zero")
            self.assertEqual(result["outcomes"]["terminal_runs"], 3)
            self.assertEqual(result["outcomes"]["accepted"], 2)
            self.assertEqual(result["outcomes"]["acceptance_rate"], 0.666667)
            self.assertEqual(result["outcomes"]["first_pass_accepted"], 1)
            self.assertEqual(result["outcomes"]["first_pass_rate"], 0.5)
            self.assertEqual(result["speed"]["tta_samples"], 2)
            self.assertEqual(result["speed"]["p50_ms"], 10000)
            self.assertEqual(result["speed"]["p90_ms"], 120000)
            efficiency = result["efficiency"]
            self.assertEqual(efficiency["wave_count_total"], 3)
            self.assertEqual(efficiency["waves_per_accepted"], 1.5)
            self.assertEqual(efficiency["replanned_accepted"], 1)
            self.assertEqual(efficiency["replan_rate"], 0.5)
            self.assertEqual(efficiency["tool_calls"]["observed_accepted"], 1)
            self.assertEqual(efficiency["tool_calls"]["missing_accepted"], 1)
            self.assertEqual(efficiency["tool_calls"]["coverage"], 0.5)
            self.assertEqual(efficiency["tool_calls"]["mean_per_observed_accepted"], 7.0)
            provider = result["cost"]["provider_observed"]
            self.assertEqual(provider["complete_accepted"], 1)
            self.assertEqual(provider["missing_accepted"], 1)
            self.assertEqual(provider["total_usd"], 0.01)
            total = result["cost"]["total_system"]
            self.assertEqual(total["complete_accepted"], 1)
            self.assertEqual(total["missing_accepted"], 1)
            self.assertEqual(total["total_usd"], 0.03)
            self.assertEqual(len(result["hourly"]), 168)

    def test_empty_window_keeps_rates_and_cost_measurements_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            ledger = OrchestrationLedger(Path(raw))
            result = operations_analytics(ledger, performance={"run_metrics": {}}, now="2026-08-19T08:00:00Z")
            self.assertEqual(result["outcomes"]["terminal_runs"], 0)
            self.assertIsNone(result["outcomes"]["acceptance_rate"])
            self.assertIsNone(result["outcomes"]["first_pass_rate"])
            self.assertIsNone(result["speed"]["p50_ms"])
            self.assertIsNone(result["efficiency"]["tool_calls"]["coverage"])
            self.assertIsNone(result["efficiency"]["tool_calls"]["total_observed"])
            self.assertIsNone(result["cost"]["provider_observed"]["total_usd"])
            self.assertIsNone(result["cost"]["total_system"]["total_usd"])


if __name__ == "__main__":
    unittest.main()
