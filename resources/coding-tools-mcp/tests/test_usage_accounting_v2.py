from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.usage_events import build_usage_event, usage_event_from_controller_report
from coding_tools_mcp.usage_pricing import MODEL_PRICING, PRICING_REVISION, derive_cost


class UsageAccountingV2Tests(unittest.TestCase):
    def test_attribution_status_is_derived_and_explicit_status_must_match(self) -> None:
        base = {
            "provider_id": "fixture-provider",
            "model_id": "fixture-model",
            "status": "completed",
            "source": "attribution-test",
            "input_tokens": 1,
            "output_tokens": 1,
        }
        inferred_cases = (
            (("", "", ""), "unassigned"),
            (("run", "", ""), "partial"),
            (("run", "wave", ""), "partial"),
            (("run", "wave", "delegation"), "exact"),
        )
        for index, (identities, expected) in enumerate(inferred_cases):
            with self.subTest(kind="inferred", identities=identities):
                event = build_usage_event(
                    run_id=identities[0],
                    wave_id=identities[1],
                    delegation_id=identities[2],
                    identity_key=f"inferred-{index}",
                    **base,
                )
                self.assertEqual(event["attribution"]["status"], expected)
            with self.subTest(kind="matching-explicit", identities=identities):
                event = build_usage_event(
                    run_id=identities[0],
                    wave_id=identities[1],
                    delegation_id=identities[2],
                    identity_key=f"explicit-{index}",
                    attribution_status=expected,
                    **base,
                )
                self.assertEqual(event["attribution"]["status"], expected)

        mismatches = (
            (("", "", ""), "exact"),
            (("run", "", ""), "exact"),
            (("run", "wave", "delegation"), "partial"),
            (("run", "wave", "delegation"), "unassigned"),
        )
        for identities, explicit in mismatches:
            with self.subTest(kind="mismatch", identities=identities, explicit=explicit):
                with self.assertRaisesRegex(
                    ValueError,
                    "does not match identity-derived status",
                ):
                    build_usage_event(
                        run_id=identities[0],
                        wave_id=identities[1],
                        delegation_id=identities[2],
                        identity_key=f"mismatch-{explicit}-{'-'.join(identities)}",
                        attribution_status=explicit,
                        **base,
                    )

    def test_ledger_and_analytics_do_not_upgrade_partial_attribution(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="partial attribution persistence")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            event = build_usage_event(
                run_id=run_id,
                wave_id="",
                delegation_id="",
                provider_id="fixture-partial",
                model_id="fixture-model",
                status="completed",
                source="partial-attribution-test",
                input_tokens=3,
                output_tokens=1,
            )
            self.assertEqual(event["attribution"]["status"], "partial")

            recorded = ledger.record_usage_event(
                run_id=run_id,
                wave_id=wave_id,
                delegation_id="outer-ledger-binding",
                usage_event=event,
            )
            self.assertTrue(recorded["recorded"])
            stored = ledger.list_usage_events(run_id, limit=None)
            self.assertEqual(stored[0]["attribution"]["status"], "partial")

            analytics = ledger.usage_analytics(days=1, now=stored[0]["event_time"])
            provider = next(
                item
                for item in analytics["by_provider"]
                if item["provider_id"] == "fixture-partial"
            )
            self.assertEqual(provider["event_count"], 1)
            self.assertNotIn("attribution", provider)
            self.assertNotEqual(
                (provider.get("attribution") or {}).get("status"),
                "exact",
            )
            self.assertEqual(analytics["window"]["invalid_event_count"], 0)

    def test_controller_usage_deduplicates_across_waves_without_changing_provider_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="controller cross-wave idempotency")
            first_wave = ledger.create_wave(run_id, execution_mode="mcp_only")
            second_wave = ledger.create_wave(run_id, execution_mode="mcp_only")
            report = {
                "schema_version": 1,
                "turn_id": "chatweb-turn-stable-across-replan",
                "trace_id": "trace-stable-across-replan",
                "provider_id": "openai",
                "model_id": "gpt-5.6-sol",
                "source": "client_reported",
                "accounting_profile": "openai_compatible",
                "input_tokens": 100,
                "cached_input_tokens": 30,
                "output_tokens": 20,
                "reasoning_output_tokens": 5,
            }

            first_event = usage_event_from_controller_report(run_id=run_id, wave_id=first_wave, report=report)
            replay_event = usage_event_from_controller_report(run_id=run_id, wave_id=second_wave, report=report)
            self.assertEqual(first_event["usage_id"], replay_event["usage_id"])
            self.assertNotEqual(first_event["delegation_id"], replay_event["delegation_id"])

            first = ledger.record_usage_event(
                run_id=run_id,
                wave_id=first_wave,
                delegation_id=first_event["delegation_id"],
                usage_event=first_event,
            )
            duplicate = ledger.record_usage_event(
                run_id=run_id,
                wave_id=second_wave,
                delegation_id=replay_event["delegation_id"],
                usage_event=replay_event,
            )
            self.assertTrue(first["recorded"])
            self.assertFalse(duplicate["recorded"])
            stored = ledger.list_usage_events(run_id)
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored[0]["wave_id"], first_wave)
            self.assertEqual(stored[0]["delegation_id"], first_event["delegation_id"])

            conflicting_event = usage_event_from_controller_report(
                run_id=run_id,
                wave_id=second_wave,
                report={**report, "output_tokens": 21},
            )
            self.assertEqual(first_event["usage_id"], conflicting_event["usage_id"])
            with self.assertRaisesRegex(ValueError, "different evidence"):
                ledger.record_usage_event(
                    run_id=run_id,
                    wave_id=second_wave,
                    delegation_id=conflicting_event["delegation_id"],
                    usage_event=conflicting_event,
                )

            provider_first = build_usage_event(
                run_id=run_id,
                wave_id=first_wave,
                delegation_id="provider-stable-delegation",
                provider_id="opencode-go",
                model_id="deepseek-v4-flash",
                status="completed",
                source="provider-test",
                input_tokens=10,
                output_tokens=2,
            )
            provider_second = build_usage_event(
                run_id=run_id,
                wave_id=second_wave,
                delegation_id="provider-stable-delegation",
                provider_id="opencode-go",
                model_id="deepseek-v4-flash",
                status="completed",
                source="provider-test",
                input_tokens=10,
                output_tokens=2,
            )
            self.assertNotEqual(provider_first["usage_id"], provider_second["usage_id"])

    def test_provider_fixture_round_trips_exact_values_cost_provenance_and_attribution(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="provider exact round trip")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            event = build_usage_event(
                run_id=run_id,
                wave_id=wave_id,
                delegation_id="provider-fixture",
                provider_id="fixture-provider",
                model_id="gpt-5.6-sol",
                status="completed",
                source="provider-fixture",
                input_tokens=3824,
                cached_input_tokens=3000,
                output_tokens=14,
                reasoning_output_tokens=4,
                provider_cost=0.0042,
            )
            self.assertEqual(event["attribution"]["status"], "exact")
            self.assertEqual(event["usage"]["input_total_tokens"], 3824)
            self.assertEqual(event["usage"]["input_cached_tokens"], 3000)
            self.assertEqual(event["usage"]["input_uncached_tokens"], 824)
            self.assertEqual(event["usage"]["output_total_tokens"], 14)
            self.assertEqual(event["usage"]["output_reasoning_tokens"], 4)
            self.assertEqual(event["usage"]["total_tokens"], 3838)
            self.assertEqual(event["provenance"]["usage"], "provider_reported")
            self.assertEqual(event["provenance"]["cost"], "provider_reported")
            self.assertEqual(event["measurement"]["cost"], "measured")
            self.assertEqual(event["cost"]["provider_cost"], 0.0042)
            self.assertIsNone(event["cost"]["derived_cost_usd"])
            self.assertIsNone(event["cost"]["pricing_revision"])

            recorded = ledger.record_usage_event(
                run_id=run_id,
                wave_id=wave_id,
                delegation_id="provider-fixture",
                usage_event=event,
            )
            self.assertTrue(recorded["recorded"])
            stored = ledger.list_usage_events(run_id, limit=None)
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored[0]["attribution"]["status"], "exact")
            analytics = ledger.usage_analytics(days=1, now=stored[0]["event_time"])
            provider = next(item for item in analytics["by_provider"] if item["provider_id"] == "fixture-provider")
            self.assertEqual(provider["usage"]["input_total_tokens"], 3824)
            self.assertEqual(provider["usage"]["input_cached_tokens"], 3000)
            self.assertEqual(provider["usage"]["input_uncached_tokens"], 824)
            self.assertEqual(provider["usage"]["output_total_tokens"], 14)
            self.assertEqual(provider["usage"]["output_reasoning_tokens"], 4)
            self.assertEqual(provider["usage"]["total_tokens"], 3838)
            self.assertAlmostEqual(provider["cost"]["measured_usd"], 0.0042)
            self.assertEqual(provider["cost"]["derived_event_count"], 0)
            self.assertEqual(provider["provenance"]["usage"], {"provider_reported": 1})
            self.assertEqual(provider["provenance"]["cost"], {"provider_reported": 1})

    def test_derived_cost_carries_pricing_revision_without_overriding_reported_cost(self) -> None:
        event = build_usage_event(
            run_id="run-pricing",
            wave_id="wave-pricing",
            delegation_id="delegation-pricing",
            provider_id="opencode-go",
            model_id="deepseek-v4-flash",
            status="completed",
            source="provider-pricing",
            input_tokens=100,
            cached_input_tokens=20,
            output_tokens=10,
            reasoning_output_tokens=2,
            provider_cost=None,
        )
        self.assertEqual(event["measurement"]["cost"], "derived")
        self.assertEqual(event["provenance"]["cost"], "pricing_derived")
        self.assertEqual(event["cost"]["kind"], "pricing_derived")
        self.assertIsNotNone(event["cost"]["derived_cost_usd"])
        self.assertEqual(event["cost"]["pricing_revision"], PRICING_REVISION)

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
