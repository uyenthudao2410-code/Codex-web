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

            def unexpected_n_plus_one(*_args, **_kwargs):
                raise AssertionError("operations analytics must use fixed-window batch evidence")

            ledger.accepted_result_economics = unexpected_n_plus_one
            ledger.accepted_result_evaluation = unexpected_n_plus_one
            ledger.list_waves = unexpected_n_plus_one
            result = operations_analytics(
                ledger,
                performance={
                    "run_metrics": {first: {"tool_calls": 7}},
                    "recent": [
                        {"run_id": first, "wave_id": first_wave, "invocation": {"invocation_id": f"inv-{index}"}}
                        for index in range(7)
                    ],
                },
                days=7,
                now="2026-08-19T08:00:00Z",
            )
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
            coverage = result["measurement_coverage"]
            self.assertEqual(coverage["missing_measurement_policy"], "unknown_not_zero")
            self.assertIsNone(coverage["controller_usage"]["coverage"])
            self.assertEqual(coverage["provider_usage"]["coverage"], 1.0)
            self.assertEqual(coverage["tool_invocation"]["coverage"], 1.0)
            self.assertEqual(coverage["tool_invocation"]["observed"], 7)
            self.assertEqual(coverage["tool_invocation"]["expected"], 7)
            self.assertEqual(coverage["tool_card_tokens"]["measurement"], "unobserved")
            self.assertIsNone(coverage["tool_card_tokens"]["coverage"])
            self.assertEqual(coverage["tool_card_tokens"]["missing_reason"], "client_receipt_not_exposed_by_mcp_transport")
            self.assertEqual(coverage["cost"]["coverage"], 0.5)
            self.assertEqual(coverage["exact_run_attribution"]["coverage"], 1.0)
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
            coverage = result["measurement_coverage"]
            self.assertIsNone(coverage["controller_usage"]["coverage"])
            self.assertIsNone(coverage["provider_usage"]["coverage"])
            self.assertIsNone(coverage["tool_invocation"]["coverage"])
            self.assertIsNone(coverage["cost"]["coverage"])
            self.assertIsNone(coverage["exact_run_attribution"]["coverage"])
            self.assertEqual(coverage["tool_card_tokens"]["measurement"], "unobserved")
            estimate = result["controller_token_estimate"]
            self.assertEqual(estimate["status"], "unknown")
            self.assertEqual(estimate["measurement"], "UNKNOWN")
            self.assertIsNone(estimate["estimate"])

    def test_controller_token_estimate_uses_exact_calibration_for_missing_runs(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            ledger = OrchestrationLedger(Path(raw))
            run_metrics = {}
            for index in range(5):
                run_id = ledger.create_run(objective=f"calibration-{index}")
                wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
                ledger.record_usage_event(
                    run_id=run_id,
                    wave_id=wave_id,
                    delegation_id=f"controller-{index}",
                    usage_event=build_usage_event(
                        run_id=run_id,
                        wave_id=wave_id,
                        delegation_id=f"controller-{index}",
                        provider_id="openai",
                        model_id="gpt-test",
                        status="completed",
                        source="chatweb:controller_usage",
                        input_tokens=300,
                        output_tokens=100,
                        actor="controller",
                        usage_provenance="client_reported",
                        attribution_status="exact",
                    ),
                )
                ledger.finish_wave(wave_id, status="accepted")
                ledger.finish_run(run_id, status="accepted")
                self._set_times(ledger, run_id, "2026-08-19T07:50:00Z", "2026-08-19T07:50:10Z")
                run_metrics[run_id] = {"tool_calls": 1, "model_visible_bytes": 1600}

            missing_run = ledger.create_run(objective="missing-controller")
            missing_wave = ledger.create_wave(missing_run, execution_mode="mcp_only")
            ledger.finish_wave(missing_wave, status="accepted")
            ledger.finish_run(missing_run, status="accepted")
            self._set_times(ledger, missing_run, "2026-08-19T07:55:00Z", "2026-08-19T07:55:10Z")
            run_metrics[missing_run] = {"tool_calls": 1, "model_visible_bytes": 4000}

            result = operations_analytics(
                ledger,
                performance={"run_metrics": run_metrics},
                days=7,
                now="2026-08-19T08:00:00Z",
            )
            estimate = result["controller_token_estimate"]
            self.assertEqual(estimate["status"], "calibrated_estimate")
            self.assertEqual(estimate["measurement"], "CALIBRATED_ESTIMATE")
            self.assertEqual(estimate["confidence"], "low")
            self.assertEqual(estimate["calibration_samples"], 5)
            self.assertEqual(estimate["missing_exact_runs"], 1)
            self.assertEqual(estimate["eligible_missing_runs"], 1)
            self.assertEqual(estimate["estimate"]["p10_total_tokens"], 1000)
            self.assertEqual(estimate["estimate"]["p50_total_tokens"], 1000)
            self.assertEqual(estimate["estimate"]["p90_total_tokens"], 1000)

    def test_controller_token_estimate_uses_separate_context_proxy_below_calibration_floor(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            ledger = OrchestrationLedger(Path(raw))
            run_id = ledger.create_run(objective="context-only")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")
            self._set_times(ledger, run_id, "2026-08-19T07:55:00Z", "2026-08-19T07:55:10Z")

            result = operations_analytics(
                ledger,
                performance={"run_metrics": {run_id: {"tool_calls": 1, "model_visible_bytes": 4000}}},
                days=7,
                now="2026-08-19T08:00:00Z",
            )
            estimate = result["controller_token_estimate"]
            self.assertEqual(estimate["status"], "context_estimate")
            self.assertEqual(estimate["measurement"], "CONTEXT_ESTIMATE")
            self.assertEqual(estimate["confidence"], "low")
            self.assertEqual(estimate["calibration_samples"], 0)
            self.assertEqual(estimate["missing_reason"], "exact_calibration_below_minimum")
            self.assertEqual(estimate["estimate"]["p10_context_tokens"], 667)
            self.assertEqual(estimate["estimate"]["p50_context_tokens"], 1000)
            self.assertEqual(estimate["estimate"]["p90_context_tokens"], 2000)
            self.assertTrue(estimate["estimate"]["not_controller_total"])

    def test_malformed_controller_usage_does_not_calibrate_partial_runs(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            ledger = OrchestrationLedger(Path(raw))
            metrics = {}
            cases = [
                ("malformed-only", ("malformed",), 40),
                ("mixed", ("valid", "malformed"), 50),
                ("valid-only", ("valid",), 55),
            ]
            for label, kinds, minute in cases:
                run_id = ledger.create_run(objective=label)
                wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
                for index, kind in enumerate(kinds):
                    delegation_id = f"{label}-{index}"
                    if kind == "valid":
                        ledger.record_usage_event(
                            run_id=run_id,
                            wave_id=wave_id,
                            delegation_id=delegation_id,
                            usage_event=build_usage_event(
                                run_id=run_id,
                                wave_id=wave_id,
                                delegation_id=delegation_id,
                                provider_id="openai",
                                model_id="gpt-test",
                                status="completed",
                                source="chatweb:controller_usage",
                                input_tokens=300,
                                output_tokens=100,
                                actor="controller",
                                usage_provenance="client_reported",
                                attribution_status="exact",
                            ),
                        )
                    else:
                        ledger.append_event(
                            run_id,
                            wave_id=wave_id,
                            delegation_id=delegation_id,
                            event_type="usage_event",
                            payload={
                                "usage_id": delegation_id,
                                "run_id": run_id,
                                "wave_id": wave_id,
                                "delegation_id": delegation_id,
                                "actor": "controller",
                                "attribution": {"status": "exact"},
                                "measurement": {"usage": "measured", "cost": "unobserved"},
                                "provenance": {"source": "chatweb:controller_usage"},
                                "usage": {"input_tokens": 300, "output_tokens": 100},
                                "accounting": {"profile": "unsupported-profile"},
                                "cost": {"provider_cost": None},
                            },
                        )
                ledger.finish_wave(wave_id, status="accepted")
                ledger.finish_run(run_id, status="accepted")
                self._set_times(
                    ledger, run_id,
                    f"2026-08-19T07:{minute:02d}:00Z",
                    f"2026-08-19T07:{minute:02d}:10Z",
                )
                metrics[run_id] = {"tool_calls": 1, "model_visible_bytes": 1600}

            result = operations_analytics(
                ledger, performance={"run_metrics": metrics},
                days=7, now="2026-08-19T08:00:00Z",
            )
            self.assertEqual(result["outcomes"]["terminal_runs"], 3)
            self.assertEqual(result["outcomes"]["accepted"], 3)
            coverage = result["measurement_coverage"]["controller_usage"]
            self.assertEqual(coverage["observed"], 4)
            self.assertEqual(coverage["exact"], 2)
            self.assertEqual(coverage["coverage"], 0.5)
            estimate = result["controller_token_estimate"]
            self.assertEqual(estimate["exact_runs"], 1)
            self.assertEqual(estimate["missing_exact_runs"], 2)
            self.assertEqual(estimate["eligible_missing_runs"], 2)
            self.assertEqual(estimate["calibration_samples"], 1)
            self.assertEqual(estimate["status"], "context_estimate")
            self.assertEqual(estimate["measurement"], "CONTEXT_ESTIMATE")



if __name__ == "__main__":
    unittest.main()
