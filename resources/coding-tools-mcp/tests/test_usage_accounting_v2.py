from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.usage_events import build_usage_event
from coding_tools_mcp.usage_pricing import MODEL_PRICING, derive_cost


class UsageAccountingV2Tests(unittest.TestCase):
    def test_reasoning_rate_prices_nonreasoning_output_only_once(self) -> None:
        with patch.dict(
            MODEL_PRICING,
            {"reasoning-test": {"input": 1.0, "output": 2.0, "reasoning": 4.0}},
            clear=False,
        ):
            derived = derive_cost(
                {
                    "input_total_tokens": 10,
                    "input_uncached_tokens": 10,
                    "input_cached_tokens": 0,
                    "input_cache_creation_tokens": 0,
                    "output_total_tokens": 50,
                    "output_nonreasoning_tokens": 30,
                    "output_reasoning_tokens": 20,
                },
                "reasoning-test",
            )
        self.assertIsNotNone(derived)
        total, components = derived
        self.assertAlmostEqual(total, (10 * 1 + 30 * 2 + 20 * 4) / 1_000_000)
        self.assertAlmostEqual(components["output"], 30 * 2 / 1_000_000)
        self.assertAlmostEqual(components["reasoning"], 20 * 4 / 1_000_000)

    def test_derived_cost_fails_closed_when_nonzero_category_has_no_rate(self) -> None:
        self.assertIsNone(
            derive_cost(
                {
                    "input_total_tokens": 1000,
                    "input_uncached_tokens": 600,
                    "input_cached_tokens": 400,
                    "input_cache_creation_tokens": 0,
                    "output_total_tokens": 10,
                    "output_reasoning_tokens": 0,
                    "output_nonreasoning_tokens": 10,
                },
                "gpt-5.6-sol",
            )
        )

    def test_usage_id_duplicate_is_exact_and_canonical_counters_survive_sanitization(self) -> None:
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
            first = ledger.record_usage_event(
                run_id=run_id, wave_id=wave_id, delegation_id="delegation-3", usage_event=usage
            )
            duplicate = ledger.record_usage_event(
                run_id=run_id, wave_id=wave_id, delegation_id="delegation-3", usage_event=usage
            )
            self.assertTrue(first["recorded"])
            self.assertFalse(duplicate["recorded"])
            projected = ledger.list_usage_events(run_id)
            self.assertEqual(projected[0]["usage"]["input_total_tokens"], 12)
            self.assertEqual(projected[0]["usage"]["total_tokens"], 12)

            conflicting = copy.deepcopy(usage)
            conflicting["usage"]["output_tokens"] = 1
            with self.assertRaisesRegex(ValueError, "different evidence"):
                ledger.record_usage_event(
                    run_id=run_id,
                    wave_id=wave_id,
                    delegation_id="delegation-3",
                    usage_event=conflicting,
                )

    def test_controller_usage_unobserved_is_unknown_not_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="provider-only-window")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            provider = build_usage_event(
                run_id=run_id,
                wave_id=wave_id,
                delegation_id="provider-only",
                provider_id="opencode-go",
                model_id="deepseek-v4-flash",
                status="completed",
                source="opencode:provider_dispatch",
                input_tokens=100,
                cached_input_tokens=20,
                output_tokens=10,
                reasoning_output_tokens=2,
                provider_cost=0.001,
            )
            ledger.append_event(
                run_id,
                wave_id=wave_id,
                delegation_id="provider-only",
                event_type="usage_event",
                payload=provider,
                event_time="2026-08-19T07:58:00Z",
            )

            analytics = ledger.usage_analytics(days=7, now="2026-08-19T08:00:00Z")
            controller = analytics["controller_usage"]
            self.assertEqual(controller["status"], "unobserved")
            self.assertEqual(controller["event_count"], 0)
            self.assertIsNone(controller["usage"])
            self.assertIsNone(controller["cost"])
            self.assertIsNone(controller["provenance"])
            self.assertEqual(controller["missing_measurement_policy"], "unknown_not_zero")
            self.assertEqual(controller["missing_reason"], "no_exact_controller_usage_event_in_window")
            self.assertEqual(analytics["overall"]["event_count"], 1)
            self.assertEqual(analytics["overall"]["usage"]["total_tokens"], 110)

    def test_seven_day_analytics_is_unbounded_and_separates_cost_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="analytics")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")

            for index in range(10):
                event = build_usage_event(
                    run_id=run_id,
                    wave_id=wave_id,
                    delegation_id=f"provider-{index}",
                    provider_id="opencode-go",
                    model_id="deepseek-v4-flash",
                    status="completed",
                    source="opencode:provider_dispatch",
                    input_tokens=100,
                    cached_input_tokens=20,
                    output_tokens=10,
                    reasoning_output_tokens=2,
                    provider_cost=0.001 if index < 9 else None,
                )
                ledger.append_event(
                    run_id,
                    wave_id=wave_id,
                    delegation_id=f"provider-{index}",
                    event_type="usage_event",
                    payload=event,
                    event_time=f"2026-08-19T06:{index:02d}:00Z",
                )

            for index, minute in enumerate((57, 59)):
                event = build_usage_event(
                    run_id=run_id,
                    wave_id=wave_id,
                    delegation_id=f"controller-{index}",
                    provider_id="chatweb",
                    model_id="gpt-5.6-sol",
                    status="completed",
                    source="chatweb:mcp_meta",
                    input_tokens=50,
                    cached_input_tokens=10,
                    output_tokens=5,
                    reasoning_output_tokens=1,
                    provider_cost=0.0005,
                    usage_provenance="client_reported",
                    cost_provenance="client_reported",
                    actor="controller",
                )
                ledger.append_event(
                    run_id,
                    wave_id=wave_id,
                    delegation_id=f"controller-{index}",
                    event_type="usage_event",
                    payload=event,
                    event_time=f"2026-08-19T07:{minute:02d}:00Z",
                )

            old = build_usage_event(
                run_id=run_id,
                wave_id=wave_id,
                delegation_id="old",
                provider_id="opencode-go",
                model_id="deepseek-v4-flash",
                status="completed",
                source="old",
                input_tokens=999,
                output_tokens=999,
                provider_cost=1.0,
            )
            ledger.append_event(
                run_id,
                wave_id=wave_id,
                delegation_id="old",
                event_type="usage_event",
                payload=old,
                event_time="2026-08-11T07:59:00Z",
            )

            self.assertEqual(len(ledger.recent_usage_events(limit=8)), 8)
            analytics = ledger.usage_analytics(days=7, now="2026-08-19T08:00:00Z")
            self.assertEqual(analytics["window"]["source_event_count"], 12)
            self.assertEqual(analytics["overall"]["event_count"], 12)
            self.assertEqual(analytics["overall"]["usage"]["input_total_tokens"], 1100)
            self.assertEqual(analytics["overall"]["usage"]["output_total_tokens"], 110)
            self.assertEqual(analytics["overall"]["usage"]["total_tokens"], 1210)
            self.assertEqual(analytics["rolling_5m"]["event_count"], 2)
            self.assertEqual(analytics["rolling_5m"]["usage"]["total_tokens"], 110)
            controller = analytics["controller_usage"]
            self.assertEqual(controller["status"], "observed")
            self.assertEqual(controller["event_count"], 2)
            self.assertEqual(controller["usage"]["total_tokens"], 110)
            self.assertEqual(controller["provenance"]["usage"]["client_reported"], 2)
            self.assertIsNone(controller["missing_reason"])
            actors = {item["actor"]: item for item in analytics["by_actor"]}
            self.assertEqual(actors["provider"]["event_count"], 10)
            self.assertEqual(actors["controller"]["event_count"], 2)
            self.assertEqual(len(analytics["hourly"]), 2)
            self.assertEqual(analytics["overall"]["cost"]["measured_event_count"], 11)
            self.assertEqual(analytics["overall"]["cost"]["derived_event_count"], 1)
            self.assertAlmostEqual(analytics["overall"]["cost"]["measured_usd"], 0.01)
            self.assertAlmostEqual(analytics["overall"]["cost"]["derived_usd"], 0.00002716)

    def test_provider_economics_excludes_controller_usage_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="provider-only")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            for actor, input_tokens, cost in (("provider", 100, 0.001), ("controller", 50, 0.002)):
                delegation_id = f"{actor}-usage"
                event = build_usage_event(
                    run_id=run_id,
                    wave_id=wave_id,
                    delegation_id=delegation_id,
                    provider_id="opencode-go" if actor == "provider" else "chatweb",
                    model_id="deepseek-v4-flash" if actor == "provider" else "gpt-5.6-sol",
                    status="completed",
                    source="opencode:provider_dispatch" if actor == "provider" else "chatweb:mcp_meta",
                    input_tokens=input_tokens,
                    output_tokens=10,
                    provider_cost=cost,
                    actor=actor,
                    usage_provenance="provider_reported" if actor == "provider" else "client_reported",
                )
                ledger.record_usage_event(
                    run_id=run_id,
                    wave_id=wave_id,
                    delegation_id=delegation_id,
                    usage_event=event,
                )
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")
            provider = ledger.accepted_result_economics(run_id)["provider_economics"]
            self.assertEqual(provider["usage_event_count"], 1)
            self.assertEqual(provider["usage"]["input_tokens"], 100)
            self.assertEqual(provider["usage"]["input_total_tokens"], 100)
            self.assertAlmostEqual(provider["provider_cost"], 0.001)


if __name__ == "__main__":
    unittest.main()
