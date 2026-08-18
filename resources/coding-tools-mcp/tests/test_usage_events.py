from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.usage_events import build_usage_event, usage_event_from_provider_delegation, usage_event_from_provider_telemetry
from coding_tools_mcp.usage_pricing import derive_cost, price_of


class UsageEventTests(unittest.TestCase):
    def test_provider_telemetry_preserves_measured_usage_and_unknown_timing(self) -> None:
        event = usage_event_from_provider_telemetry(
            run_id="run-1",
            wave_id="wave-1",
            delegation_id="delegation-1",
            telemetry={
                "provider_id": "opencode-go",
                "model_id": "deepseek-v4-flash",
                "status": "completed",
                "input_tokens": 100,
                "output_tokens": 20,
                "reasoning_output_tokens": 4,
                "cache_read_tokens": 40,
                "cache_write_tokens": 2,
                "provider_cost": 0.004,
                "duration_ms": 600,
            },
        )
        self.assertEqual(event["usage"]["cached_input_tokens"], 40)
        self.assertEqual(event["usage"]["uncached_input_tokens"], 60)
        self.assertEqual(event["cost"]["provider_cost"], 0.004)
        self.assertIsNone(event["timing"]["queue_ms"])
        self.assertEqual(event["timing"]["provider_ms"], 600)
        self.assertIsNone(event["timing"]["total_ms"])
        self.assertEqual(event["measurement"]["queue_timing"], "unobserved")

    def test_failed_usage_records_typed_error_only(self) -> None:
        raw = "RateLimitError-super-secret-message"
        event = build_usage_event(
            run_id="run-2",
            wave_id="wave-2",
            delegation_id="delegation-2",
            provider_id="opencode-go",
            model_id="deepseek-v4-pro",
            status="failed",
            source="test",
            error_name=raw,
        )
        self.assertEqual(event["error"]["class"], "capacity_or_rate_limit")
        self.assertNotIn(raw, repr(event))

    def test_aggregated_provider_delegation_builds_one_terminal_usage_event(self) -> None:
        event = usage_event_from_provider_delegation(
            run_id="run-a",
            wave_id="wave-a",
            delegation={
                "delegation_id": "delegation-a",
                "model": "opencode-go/deepseek-v4-flash",
                "status": "failed",
                "metadata": {
                    "provider_id": "opencode-go",
                    "model_id": "deepseek-v4-flash",
                    "economics": {"measured": True, "input_tokens": 150, "cached_input_tokens": 40, "output_tokens": 15, "reasoning_output_tokens": 2, "cache_read_tokens": 40, "cache_write_tokens": 1, "provider_cost": 0.003},
                    "provider_message_duration_ms": 900,
                    "timing": {"queue_ms": 2},
                    "error_class": "provider_cli_idle_timeout_after_tool_calls",
                },
            },
            total_ms=45000,
        )
        self.assertIsNotNone(event)
        self.assertEqual(event["usage"]["input_tokens"], 150)
        self.assertEqual(event["usage"]["uncached_input_tokens"], 110)
        self.assertAlmostEqual(event["cost"]["provider_cost"], 0.003)
        self.assertEqual(event["timing"]["provider_ms"], 900)
        self.assertEqual(event["timing"]["total_ms"], 45000)
        self.assertEqual(event["error"]["class"], "deadline_or_timeout")

    def test_pricing_lookup_matches_repo_lane_rates(self) -> None:
        self.assertEqual(price_of("deepseek-v4-flash", "input"), 0.28)
        self.assertEqual(price_of("deepseek-v4-flash", "output"), 0.42)
        self.assertEqual(price_of("deepseek-v4-flash", "cached"), 0.028)
        self.assertEqual(price_of("opencode-go/deepseek-v4-pro", "input"), 0.28)
        self.assertEqual(price_of("gpt-5.4-mini", "input"), 0.15)
        self.assertEqual(price_of("gpt-5.6-luna", "output"), 0.6)
        self.assertEqual(price_of("gpt-5.6-terra", "input"), 2.5)
        self.assertEqual(price_of("gpt-5.6-sol", "input"), 10)
        self.assertEqual(price_of("gpt-5.6-sol", "output"), 40)
        self.assertIsNone(price_of("gpt-5.6-sol", "reasoning"))
        self.assertIsNone(price_of("unknown-model", "input"))
        self.assertIsNone(price_of("deepseek-v4-flash", "bogus"))

    def test_derived_cost_when_provider_cost_missing(self) -> None:
        event = build_usage_event(
            run_id="run-d",
            wave_id="wave-d",
            delegation_id="delegation-d",
            provider_id="opencode-go",
            model_id="deepseek-v4-flash",
            status="completed",
            source="test",
            input_tokens=1000,
            cached_input_tokens=400,
            output_tokens=200,
            reasoning_output_tokens=20,
            cache_write_tokens=5,
        )
        self.assertIsNone(event["cost"]["provider_cost"])
        self.assertEqual(event["cost"]["kind"], "pricing_derived")
        self.assertEqual(event["provenance"]["cost"], "pricing_derived")
        self.assertEqual(event["measurement"]["cost"], "derived")
        self.assertAlmostEqual(event["cost"]["derived_cost_usd"], (600 * 0.28 + 400 * 0.028 + 200 * 0.42) / 1_000_000)
        self.assertEqual(event["cost"]["derived_components"]["input"], 600 * 0.28 / 1_000_000)
        self.assertNotIn("reasoning", event["cost"]["derived_components"])

    def test_no_derived_cost_for_unknown_model(self) -> None:
        event = build_usage_event(
            run_id="run-e",
            wave_id="wave-e",
            delegation_id="delegation-e",
            provider_id="some-provider",
            model_id="unknown-xyz",
            status="completed",
            source="test",
            input_tokens=1000,
            output_tokens=200,
        )
        self.assertIsNone(event["cost"]["provider_cost"])
        self.assertIsNone(event["cost"]["derived_cost_usd"])
        self.assertEqual(event["cost"]["kind"], "unobserved")
        self.assertIsNone(derive_cost({"input_tokens": 1000, "output_tokens": 200}, "unknown-xyz"))

    def test_provider_cost_wins_over_derived_pricing(self) -> None:
        event = build_usage_event(
            run_id="run-f",
            wave_id="wave-f",
            delegation_id="delegation-f",
            provider_id="opencode-go",
            model_id="deepseek-v4-flash",
            status="completed",
            source="test",
            input_tokens=1000,
            cached_input_tokens=400,
            output_tokens=200,
            provider_cost=0.004,
        )
        self.assertEqual(event["cost"]["provider_cost"], 0.004)
        self.assertEqual(event["cost"]["kind"], "provider_reported")
        self.assertIsNone(event["cost"]["derived_cost_usd"])
        self.assertIsNone(event["cost"]["derived_components"])

    def test_ledger_usage_projection_is_sanitized_and_ordered(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="measure")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            usage = build_usage_event(
                run_id=run_id,
                wave_id=wave_id,
                delegation_id="delegation-3",
                provider_id="opencode-go",
                model_id="deepseek-v4-flash",
                status="completed",
                source="test",
                input_tokens=12,
                cached_input_tokens=2,
                provider_cost=0.001,
            )
            first = ledger.record_usage_event(run_id=run_id, wave_id=wave_id, delegation_id="delegation-3", usage_event=usage)
            duplicate = ledger.record_usage_event(run_id=run_id, wave_id=wave_id, delegation_id="delegation-3", usage_event=usage)
            self.assertTrue(first["recorded"])
            self.assertFalse(duplicate["recorded"])
            projected = ledger.list_usage_events(run_id)
            self.assertEqual(len(projected), 1)
            self.assertEqual(projected[0]["usage_id"], usage["usage_id"])
            self.assertEqual(projected[0]["usage"]["input_tokens"], 12)


if __name__ == "__main__":
    unittest.main()
