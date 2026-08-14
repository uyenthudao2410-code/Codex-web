from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


class OrchestrationLedgerTests(unittest.TestCase):
    def test_events_survive_restart_and_hash_chain_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="ship behavior", task_id="task-1")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="abc", worktree_fp="fp")
            ledger.append_event(run_id, wave_id=wave_id, event_type="preflight", state_after="PREFLIGHT")
            ledger.append_event(run_id, wave_id=wave_id, event_type="ready", state_before="PREFLIGHT", state_after="READY")

            restored = OrchestrationLedger(root)
            events = restored.list_events(run_id)
            self.assertEqual([item["event_type"] for item in events], ["preflight", "ready"])
            integrity = restored.verify_chain(run_id)
            self.assertTrue(integrity["ok"])
            self.assertEqual(integrity["checked"], 2)

    def test_sensitive_payload_is_redacted_but_identity_remains(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="safe audit")
            wave_id = ledger.create_wave(run_id, execution_mode="bounded_candidate")
            ledger.append_event(
                run_id,
                wave_id=wave_id,
                event_type="model_dispatch_started",
                payload={
                    "prompt": "super secret prompt",
                    "api_token": "secret-token",
                    "model": "gpt-test",
                    "economics": {
                        "input_tokens": 1200,
                        "cached_input_tokens": 900,
                        "output_tokens": 80,
                        "reasoning_output_tokens": 12,
                        "cached_tokens": 900,
                        "token": "must-stay-secret",
                        "input_tokens_string": "not-a-counter",
                    },
                },
            )
            payload = ledger.list_events(run_id)[0]["payload"]
            self.assertEqual(payload["api_token"], "[REDACTED]")
            self.assertTrue(payload["prompt"]["redacted"])
            self.assertEqual(payload["model"], "gpt-test")
            self.assertEqual(len(payload["prompt"]["sha256"]), 64)
            economics = payload["economics"]
            self.assertEqual(economics["input_tokens"], 1200)
            self.assertEqual(economics["cached_input_tokens"], 900)
            self.assertEqual(economics["output_tokens"], 80)
            self.assertEqual(economics["reasoning_output_tokens"], 12)
            self.assertEqual(economics["cached_tokens"], 900)
            self.assertEqual(economics["token"], "[REDACTED]")
            self.assertEqual(economics["input_tokens_string"], "[REDACTED]")

    def test_external_delegation_upsert_is_idempotent_monotonic_and_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="external telemetry")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            common = dict(
                delegation_id="opencode-delegation",
                wave_id=wave_id,
                authority_owner="opencode",
                route_requested="opencode",
                route_resolved="opencode-go/deepseek-v4-flash",
                model="opencode-go/deepseek-v4-flash",
            )
            first = ledger.upsert_external_delegation(**common, status="active", metadata={"economics": {"input_tokens": 10, "output_tokens": 2, "cache_read_tokens": 4}})
            nested = ledger.upsert_external_delegation(**common, status="active", metadata={"timing": {"queue_ms": 2, "provider_ms": None, "total_ms": None}})
            self.assertTrue(nested["changed"])
            self.assertEqual(nested["delegation"]["metadata"]["timing"]["queue_ms"], 2)
            self.assertTrue(first["created"])
            duplicate = ledger.upsert_external_delegation(**common, status="active", metadata={"economics": {"input_tokens": 10, "output_tokens": 2, "cache_read_tokens": 4}})
            self.assertFalse(duplicate["changed"])
            completed = ledger.upsert_external_delegation(**common, status="completed", metadata={"economics": {"input_tokens": 100, "output_tokens": 20, "cache_read_tokens": 40}})
            self.assertTrue(completed["terminal_transition"])
            stale = ledger.upsert_external_delegation(**common, status="active", metadata={"economics": {"input_tokens": 1, "output_tokens": 1, "cache_read_tokens": 1}})
            self.assertFalse(stale["changed"])
            self.assertEqual(stale["delegation"]["status"], "completed")
            self.assertEqual(stale["delegation"]["metadata"]["economics"]["input_tokens"], 100)
            self.assertEqual(stale["delegation"]["metadata"]["economics"]["cache_read_tokens"], 40)

    def test_external_delegation_aggregates_message_economics_and_freezes_conflicting_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="aggregate provider messages")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            common = dict(
                delegation_id="opencode-provider-aggregate",
                wave_id=wave_id,
                authority_owner="opencode",
                route_requested="opencode",
                route_resolved="opencode-go/deepseek-v4-flash",
                model="opencode-go/deepseek-v4-flash",
            )
            first = ledger.upsert_external_delegation(**common, status="active", metadata={"message_economics": {"msg-1": {"input_tokens": 100, "output_tokens": 10, "provider_cost": 0.001, "duration_ms": 600}}})
            duplicate = ledger.upsert_external_delegation(**common, status="active", metadata={"message_economics": {"msg-1": {"input_tokens": 100, "output_tokens": 10, "provider_cost": 0.001, "duration_ms": 600}}})
            self.assertTrue(first["created"])
            self.assertFalse(duplicate["changed"])
            second = ledger.upsert_external_delegation(**common, status="completed", metadata={"message_economics": {"msg-2": {"input_tokens": 50, "output_tokens": 5, "provider_cost": 0.002, "duration_ms": 300}}})
            economics = second["delegation"]["metadata"]["economics"]
            self.assertEqual((economics["input_tokens"], economics["output_tokens"]), (150, 15))
            self.assertAlmostEqual(economics["provider_cost"], 0.003)
            self.assertEqual(second["delegation"]["metadata"]["provider_message_duration_ms"], 900)
            conflicting = ledger.upsert_external_delegation(**common, status="failed", metadata={"error_class": "deadline_or_timeout", "timing": {"total_ms": 45000}})
            self.assertFalse(conflicting["changed"])
            self.assertEqual(conflicting["delegation"]["status"], "completed")
            self.assertNotIn("error_class", conflicting["delegation"]["metadata"])

    def test_shadow_route_record_is_idempotent_and_projects_actual_run_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="shadow routing")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            recommendation = {
                "recommendation_id": "shadow-route-1",
                "mode": "shadow_only",
                "features": {"side_effect_class": "read_only", "scope": "broad"},
                "recommendation": {"route": "opencode_read_only_flash", "model": "opencode-go/deepseek-v4-flash"},
                "automatic_dispatch": False,
                "mutation_allowed": False,
            }
            first = ledger.record_shadow_route(run_id=run_id, wave_id=wave_id, recommendation=recommendation)
            duplicate = ledger.record_shadow_route(run_id=run_id, wave_id=wave_id, recommendation=recommendation)
            self.assertTrue(first["recorded"])
            self.assertFalse(duplicate["recorded"])
            ledger.upsert_external_delegation(
                delegation_id="actual-1",
                wave_id=wave_id,
                authority_owner="opencode",
                route_requested="opencode_read_only",
                route_resolved="opencode-go/deepseek-v4-flash",
                model="opencode-go/deepseek-v4-flash",
                status="completed",
                metadata={"side_effect_class": "read_only"},
            )
            projected = ledger.routing_evidence(run_id)
            self.assertEqual(len(projected["shadow_recommendations"]), 1)
            self.assertEqual(projected["shadow_recommendations"][0]["recommendation_id"], "shadow-route-1")
            self.assertEqual(len(projected["actual_delegations"]), 1)
            self.assertEqual(projected["actual_delegations"][0]["delegation_id"], "actual-1")
            self.assertEqual(projected["accepted_result"]["run_id"], run_id)
            self.assertFalse(projected["accepted_result"]["accepted"])

    def test_routing_evidence_projects_similar_accepted_cohorts_and_warm_threads(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            for repaired in (False, True):
                historical = ledger.create_run(objective="historical bugfix", metadata={"workflow": "bugfix"})
                first_wave = ledger.create_wave(historical, execution_mode="bounded_candidate")
                ledger.append_event(
                    historical,
                    wave_id=first_wave,
                    event_type="route_selected",
                    payload={"resolved": "mini", "model": "gpt-5.4-mini", "effort": "low", "profile": "candidate_mini"},
                )
                if repaired:
                    ledger.finish_wave(first_wave, status="replanned")
                    second_wave = ledger.create_wave(historical, execution_mode="bounded_candidate")
                    ledger.append_event(
                        historical,
                        wave_id=second_wave,
                        event_type="route_selected",
                        payload={"resolved": "mini", "model": "gpt-5.4-mini", "effort": "low", "profile": "candidate_mini"},
                    )
                    ledger.finish_wave(second_wave, status="accepted")
                else:
                    ledger.finish_wave(first_wave, status="accepted")
                ledger.finish_run(historical, status="accepted")

            current = ledger.create_run(objective="current bugfix", metadata={"workflow": "bugfix"})
            current_wave = ledger.create_wave(current, execution_mode="mcp_only")
            ledger.upsert_agent_lane(
                lane_id="warm-lane",
                run_id=current,
                wave_id=current_wave,
                semantic_key="review",
                lifecycle="idle",
                thread_id="thread-warm",
            )
            ledger.upsert_agent_lane(
                lane_id="waiting-lane",
                run_id=current,
                wave_id=current_wave,
                semantic_key="investigate",
                lifecycle="waiting",
            )

            projected = ledger.routing_evidence(current)
            cohorts = projected["similar_accepted_cohorts"]
            self.assertEqual(cohorts["task_class"], "bugfix")
            self.assertEqual(cohorts["sampled_runs"], 2)
            self.assertEqual(len(cohorts["cohorts"]), 1)
            mini = cohorts["cohorts"][0]
            self.assertEqual(mini["route"], "mini")
            self.assertEqual(mini["accepted_results"], 2)
            self.assertEqual(mini["first_pass_accepted"], 1)
            self.assertEqual(mini["first_pass_rate"], 0.5)
            self.assertEqual(mini["repaired_results"], 1)
            self.assertIsNone(mini["provider_cost"]["total"])
            self.assertEqual(mini["provider_cost"]["measurement"], "unobserved")
            health = projected["warm_thread_health"]
            self.assertEqual(health["lane_count"], 2)
            self.assertEqual(health["reusable_lane_count"], 1)
            self.assertEqual(health["reusable_lane_ids"], ["warm-lane"])
            self.assertFalse(health["automatic_reuse"])
            self.assertTrue(cohorts["model_free"])
            self.assertTrue(health["content_free"])

    def test_accepted_result_economics_keeps_measured_provider_cost_separate_from_estimated_credits(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="accepted economics", metadata={"workflow": "bugfix"})
            first_wave = ledger.create_wave(run_id, execution_mode="bounded_candidate")
            ledger.append_event(
                run_id,
                wave_id=first_wave,
                event_type="route_selected",
                payload={"requested": "mini", "resolved": "mini", "model": "gpt-5.4-mini", "effort": "low", "profile": "candidate_mini"},
            )
            candidate = ledger.create_delegation(
                first_wave,
                authority_owner="CODEX:mini",
                route_requested="mini",
                route_resolved="mini",
                model="gpt-5.4-mini",
                effort="low",
                metadata={"economics": {"estimated_credits": 0.125, "pricing_basis": "observed-rate-card", "model": "gpt-5.4-mini"}},
            )
            ledger.finish_delegation(candidate, status="blocked")
            ledger.append_event(run_id, wave_id=first_wave, delegation_id=candidate, event_type="failure_observed", payload={"failure_class": "CANDIDATE_BLOCKED"})
            ledger.record_proof(
                run_id=run_id,
                wave_id=first_wave,
                stage_id="focused",
                stage_version="1",
                input_fingerprint="failed-proof",
                status="failed",
            )
            ledger.finish_wave(first_wave, status="replanned")

            second_wave = ledger.create_wave(run_id, execution_mode="mcp_only")
            ledger.append_event(
                run_id,
                wave_id=second_wave,
                event_type="route_selected",
                payload={"requested": "opencode", "resolved": "opencode_read_only_flash", "model": "opencode-go/deepseek-v4-flash", "effort": None, "profile": "read_only"},
            )
            provider_delegation = ledger.create_delegation(
                second_wave,
                authority_owner="OPENCODE:flash",
                route_requested="opencode",
                route_resolved="opencode_read_only_flash",
                model="opencode-go/deepseek-v4-flash",
                metadata={"timing": {"queue_ms": 12, "provider_ms": 34, "total_ms": 46}},
            )
            ledger.finish_delegation(provider_delegation, status="completed")
            ledger.record_usage_event(
                run_id=run_id,
                wave_id=second_wave,
                delegation_id=provider_delegation,
                usage_event={
                    "schema_version": 1,
                    "usage_id": "usage-1",
                    "run_id": run_id,
                    "wave_id": second_wave,
                    "delegation_id": provider_delegation,
                    "provider_id": "opencode-go",
                    "model_id": "deepseek-v4-flash",
                    "model": "opencode-go/deepseek-v4-flash",
                    "status": "completed",
                    "measurement": {"usage": "measured", "cost": "measured"},
                    "usage": {"input_tokens": 100, "cached_input_tokens": 40, "uncached_input_tokens": 60, "output_tokens": 12, "reasoning_output_tokens": 2, "cache_read_tokens": 40, "cache_write_tokens": 1},
                    "cost": {"provider_cost": 0.003, "kind": "provider_reported"},
                },
            )
            ledger.record_proof(
                run_id=run_id,
                wave_id=second_wave,
                stage_id="focused",
                stage_version="1",
                input_fingerprint="green-proof",
                status="passed",
            )
            ledger.record_checkpoint(
                run_id=run_id,
                wave_id=second_wave,
                git_head="head",
                proof_fingerprint="green-proof",
                status="accepted",
            )
            ledger.finish_wave(second_wave, status="accepted")
            ledger.finish_run(run_id, status="accepted")

            evidence = ledger.accepted_result_economics(run_id)
            self.assertTrue(evidence["accepted"])
            self.assertFalse(evidence["first_pass_accepted"])
            self.assertEqual(evidence["repair"], {"replan_count": 1, "failure_event_count": 1})
            self.assertEqual(evidence["route"]["resolved"], "opencode_read_only_flash")
            self.assertEqual(evidence["route"]["model"], "opencode-go/deepseek-v4-flash")
            self.assertEqual(evidence["proof"]["records"], 2)
            self.assertEqual(evidence["proof"]["passed"], 1)
            self.assertEqual(evidence["proof"]["failed"], 1)
            self.assertEqual(evidence["proof"]["accepted_checkpoint_count"], 1)
            self.assertEqual(evidence["phase_timing"]["source"], "eocl_event_timestamps")
            self.assertIsInstance(evidence["phase_timing"]["by_state_ms"], dict)
            self.assertIsInstance(evidence["phase_timing"]["methodology_phase_ms"], dict)
            if evidence["tta_ms"]:
                self.assertGreaterEqual(evidence["phase_timing"]["tta_coverage"], 0)
                self.assertLessEqual(evidence["phase_timing"]["tta_coverage"], 1)
            self.assertEqual(evidence["provider_economics"]["usage_event_count"], 1)
            self.assertTrue(evidence["provider_economics"]["cost_complete"])
            self.assertAlmostEqual(evidence["provider_economics"]["provider_cost"], 0.003)
            self.assertEqual(evidence["provider_economics"]["usage"]["input_tokens"], 100)
            self.assertEqual(evidence["provider_economics"]["usage"]["cached_input_tokens"], 40)
            self.assertEqual(evidence["provider_economics"]["timing"]["measurement"], "delegation_metadata")
            self.assertTrue(evidence["provider_economics"]["timing"]["overlaps_eocl_windows"])
            self.assertEqual(evidence["provider_economics"]["timing"]["components_ms"], {"queue_ms": 12, "provider_ms": 34, "total_ms": 46})
            self.assertEqual(evidence["provider_economics"]["timing"]["sample_counts"], {"queue_ms": 1, "provider_ms": 1, "total_ms": 1})
            self.assertEqual(evidence["candidate_economics"]["estimated_credits"], 0.125)
            self.assertEqual(evidence["candidate_economics"]["pricing_bases"], ["observed-rate-card"])
            self.assertEqual(evidence["critical_defects"], {"status": "unknown", "count": None, "source": "not_recorded"})
            self.assertIsNotNone(evidence["tta_ms"])
            self.assertEqual(ledger.routing_evidence(run_id)["accepted_result"], evidence)

    def test_accepted_result_provider_cost_is_unknown_when_cost_coverage_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="partial provider economics")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            common = {
                "schema_version": 1,
                "run_id": run_id,
                "wave_id": wave_id,
                "provider_id": "provider",
                "model_id": "model",
                "model": "provider/model",
                "status": "completed",
                "usage": {"input_tokens": 10, "cached_input_tokens": 0, "uncached_input_tokens": 10, "output_tokens": 1, "reasoning_output_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0},
            }
            ledger.record_usage_event(
                run_id=run_id,
                wave_id=wave_id,
                delegation_id="d1",
                usage_event={**common, "usage_id": "u1", "delegation_id": "d1", "measurement": {"usage": "measured", "cost": "measured"}, "cost": {"provider_cost": 0.001}},
            )
            ledger.record_usage_event(
                run_id=run_id,
                wave_id=wave_id,
                delegation_id="d2",
                usage_event={**common, "usage_id": "u2", "delegation_id": "d2", "measurement": {"usage": "measured", "cost": "unobserved"}, "cost": {"provider_cost": None}},
            )
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")
            provider = ledger.accepted_result_economics(run_id)["provider_economics"]
            self.assertEqual(provider["usage_event_count"], 2)
            self.assertEqual(provider["cost_measured_event_count"], 1)
            self.assertFalse(provider["cost_complete"])
            self.assertIsNone(provider["provider_cost"])
            self.assertEqual(provider["usage"]["input_tokens"], 20)

    def test_export_summary_includes_checkpoint_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="accepted behavior", task_id="task-checkpoint")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="abc123", worktree_fp="fp")
            checkpoint_id = ledger.record_checkpoint(
                run_id=run_id,
                wave_id=wave_id,
                git_head="abc123",
                proof_fingerprint="proof-fp",
                status="accepted",
                metadata={"accepted_by": "ChatWeb Sol"},
            )

            summary = ledger.export_summary(run_id)

            self.assertEqual(len(summary["checkpoints"]), 1)
            checkpoint = summary["checkpoints"][0]
            self.assertEqual(checkpoint["checkpoint_id"], checkpoint_id)
            self.assertEqual(checkpoint["wave_id"], wave_id)
            self.assertEqual(checkpoint["git_head"], "abc123")
            self.assertEqual(checkpoint["proof_fingerprint"], "proof-fp")
            self.assertEqual(checkpoint["status"], "accepted")
            self.assertEqual(checkpoint["metadata"]["accepted_by"], "ChatWeb Sol")


    def test_event_replay_uses_stable_non_consumptive_sequence_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="replay")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            for index in range(5):
                ledger.append_event(run_id, wave_id=wave_id, event_type=f"event-{index}")
            page1 = ledger.list_events_since(run_id, after_seq=0, limit=2)
            self.assertEqual([item["event_type"] for item in page1["events"]], ["event-0", "event-1"])
            self.assertTrue(page1["has_more"])
            page1_again = ledger.list_events_since(run_id, after_seq=0, limit=2)
            self.assertEqual(page1_again["events"], page1["events"])
            page2 = ledger.list_events_since(run_id, after_seq=page1["next_after_seq"], limit=10)
            self.assertEqual([item["event_type"] for item in page2["events"]], ["event-2", "event-3", "event-4"])
            self.assertFalse(page2["has_more"])

    def test_flight_recorder_and_phase_timing_are_bounded_and_timestamp_derived(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="flight recorder")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            ledger.append_event(run_id, wave_id=wave_id, event_type="preflight", state_after="PREFLIGHT", event_time="2026-08-14T00:00:00.000Z")
            ledger.append_event(run_id, wave_id=wave_id, event_type="routed", state_before="PREFLIGHT", state_after="ROUTED", event_time="2026-08-14T00:00:00.100Z")
            ledger.append_event(run_id, wave_id=wave_id, event_type="execute", state_before="ROUTED", state_after="EXECUTING", event_time="2026-08-14T00:00:00.300Z")
            ledger.append_event(run_id, wave_id=wave_id, event_type="prove", state_before="EXECUTING", state_after="PROVING", event_time="2026-08-14T00:00:00.500Z", payload={"prompt": "must remain redacted"})
            timing = ledger.run_phase_timing(run_id)
            self.assertEqual(timing["source"], "eocl_event_timestamps")
            self.assertEqual(timing["by_state_ms"]["PREFLIGHT"], 100)
            self.assertEqual(timing["by_state_ms"]["ROUTED"], 200)
            self.assertEqual(timing["by_state_ms"]["EXECUTING"], 200)
            self.assertEqual(timing["methodology_phase_ms"]["preflight_ms"], 100)
            self.assertEqual(timing["methodology_phase_ms"]["dispatch_window_ms"], 200)
            self.assertEqual(timing["methodology_phase_ms"]["execution_window_ms"], 200)
            self.assertIsNone(timing["methodology_phase_ms"]["proof_ms"])
            self.assertEqual(timing["observed_ms"], 500)
            self.assertIsNone(timing["tta_ms"])
            self.assertIsNone(timing["unattributed_ms"])
            self.assertIsNone(timing["tta_coverage"])
            self.assertFalse(timing["meets_coverage_floor"])
            self.assertFalse(timing["meets_coverage_target"])
            self.assertIsNone(timing["segments"][-1]["duration_ms"])
            self.assertFalse(timing["complete"])
            recorder = ledger.flight_recorder(run_id, limit=2)
            self.assertEqual([item["state_after"] for item in recorder["events"]], ["EXECUTING", "PROVING"])
            self.assertTrue(recorder["has_more"])
            self.assertTrue(recorder["events"][-1]["payload"]["prompt"]["redacted"])
            delta = ledger.flight_recorder(run_id, after_seq=recorder["events"][-2]["seq"], limit=10)
            self.assertEqual([item["state_after"] for item in delta["events"]], ["PROVING"])
            self.assertFalse(delta["has_more"])
            self.assertEqual(len(ledger.list_runs(limit=1)), 1)

    def test_terminal_phase_timing_reports_unattributed_time_and_coverage_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="coverage truth")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            with ledger._lock, ledger._connect() as connection:
                connection.execute(
                    "UPDATE runs SET started_at=?, finished_at=?, status='accepted' WHERE run_id=?",
                    ("2026-08-14T00:00:00.000Z", "2026-08-14T00:00:01.000Z", run_id),
                )
            ledger.append_event(run_id, wave_id=wave_id, event_type="preflight", state_after="PREFLIGHT", event_time="2026-08-14T00:00:00.100Z")
            ledger.append_event(run_id, wave_id=wave_id, event_type="routed", state_before="PREFLIGHT", state_after="ROUTED", event_time="2026-08-14T00:00:00.300Z")
            ledger.append_event(run_id, wave_id=wave_id, event_type="execute", state_before="ROUTED", state_after="EXECUTING", event_time="2026-08-14T00:00:00.600Z")
            ledger.append_event(run_id, wave_id=wave_id, event_type="prove", state_before="EXECUTING", state_after="PROVING", event_time="2026-08-14T00:00:00.800Z")

            timing = ledger.run_phase_timing(run_id)
            self.assertEqual(timing["tta_ms"], 1000)
            self.assertEqual(timing["observed_ms"], 900)
            self.assertEqual(timing["unattributed_ms"], 100)
            self.assertEqual(timing["tta_coverage"], 0.9)
            self.assertEqual(timing["coverage_floor"], 0.9)
            self.assertEqual(timing["coverage_target"], 0.95)
            self.assertTrue(timing["meets_coverage_floor"])
            self.assertFalse(timing["meets_coverage_target"])
            self.assertTrue(timing["complete"])

    def test_evidence_query_is_bounded_wave_scoped_and_content_free(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="resume evidence", task_id="task-evidence")
            first_wave = ledger.create_wave(run_id, execution_mode="mcp_only")
            second_wave = ledger.create_wave(run_id, execution_mode="bounded_candidate")
            ledger.append_event(run_id, wave_id=first_wave, event_type="first-wave", state_after="READY")
            first_second_wave_event = ledger.append_event(
                run_id,
                wave_id=second_wave,
                event_type="dispatch",
                state_after="EXECUTING",
                payload={"prompt": "never expose this prompt"},
            )
            ledger.append_event(run_id, wave_id=second_wave, event_type="prove", state_after="PROVING")
            ledger.append_event(run_id, wave_id=second_wave, event_type="accept", state_after="ACCEPTING")
            proof_id = ledger.record_proof(
                run_id=run_id,
                wave_id=second_wave,
                stage_id="focused",
                stage_version="1",
                input_fingerprint="fp",
                status="passed",
            )
            delegation_id = ledger.create_delegation(
                second_wave,
                authority_owner="CODEX:mini",
                route_requested="mini",
                route_resolved="mini",
                model="gpt-5.4-mini",
                effort="low",
                metadata={"prompt": "delegation prompt is redacted in storage"},
            )
            checkpoint_id = ledger.record_checkpoint(
                run_id=run_id,
                wave_id=second_wave,
                git_head="head",
                proof_fingerprint="proof-fp",
            )
            capsule = ledger.record_handoff_capsule(
                run_id=run_id,
                wave_id=second_wave,
                payload={"next_action": "continue evidence"},
            )

            recent = ledger.evidence_query(run_id, wave_id=second_wave, limit=2)
            self.assertEqual(recent["query"]["wave_id"], second_wave)
            self.assertEqual([item["wave_id"] for item in recent["events"]], [second_wave, second_wave])
            self.assertEqual([item["event_type"] for item in recent["events"]], ["prove", "accept"])
            self.assertTrue(recent["omitted_earlier_events"])
            self.assertEqual(recent["relationships"]["task_id"], "task-evidence")
            self.assertEqual(recent["relationships"]["proof_ids"], [proof_id])
            self.assertEqual(recent["relationships"]["delegation_ids"], [delegation_id])
            self.assertEqual(recent["relationships"]["checkpoint_ids"], [checkpoint_id])
            self.assertEqual(recent["latest_handoff_capsule"]["capsule_id"], capsule["capsule_id"])
            self.assertNotIn("payload", recent["latest_handoff_capsule"])
            self.assertEqual(recent["proofs"][0]["artifact_ref"]["kind"], "orchestration_proof")
            self.assertTrue(recent["proofs"][0]["artifact_ref"]["restart_safe"])
            self.assertEqual(recent["latest_handoff_capsule"]["artifact_ref"]["kind"], "handoff_capsule")
            self.assertTrue(recent["latest_handoff_capsule"]["artifact_ref"]["content_addressed"])
            self.assertTrue(recent["model_free"])
            self.assertTrue(recent["content_free"])
            self.assertFalse(recent["raw_transcript_included"])

            delta = ledger.evidence_query(
                run_id,
                wave_id=second_wave,
                after_seq=first_second_wave_event["seq"],
                limit=1,
            )
            self.assertEqual([item["event_type"] for item in delta["events"]], ["prove"])
            self.assertTrue(delta["has_more"])
            self.assertFalse(delta["omitted_earlier_events"])
            self.assertTrue(delta["integrity"]["ok"])

    def test_session_query_prunes_by_priority_under_one_item_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective="priority resume", task_id="task-priority")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            ledger.append_event(run_id, wave_id=wave_id, event_type="context_prepared", state_after="PREFLIGHT", payload={"prompt": "never expose raw prompt"})
            ledger.append_event(run_id, wave_id=wave_id, event_type="route_selected", state_after="ROUTED")
            ledger.append_event(run_id, wave_id=wave_id, event_type="failure_observed", state_after="REPLAN")
            ledger.append_event(run_id, wave_id=wave_id, event_type="awaiting_final_acceptance", state_after="ACCEPTING")
            proof_id = ledger.record_proof(
                run_id=run_id,
                wave_id=wave_id,
                stage_id="focused",
                stage_version="1",
                input_fingerprint="fp-priority",
                status="passed",
            )
            ledger.record_checkpoint(
                run_id=run_id,
                wave_id=wave_id,
                git_head="head-priority",
                proof_fingerprint="proof-priority",
            )
            ledger.create_delegation(
                wave_id,
                authority_owner="CODEX:mini",
                route_requested="mini",
                route_resolved="mini",
                model="gpt-5.4-mini",
                effort="low",
            )
            ledger.record_handoff_capsule(
                run_id=run_id,
                wave_id=wave_id,
                payload={"next_action": "continue"},
            )

            session = ledger.session_query(run_id, wave_id=wave_id, limit=6)
            self.assertEqual(session["query"]["mode"], "model_free_priority")
            self.assertEqual(session["query"]["limit"], 6)
            self.assertLessEqual(len(session["items"]), 6)
            self.assertGreater(session["pruning"]["omitted_items"], 0)
            ranks = {"critical": 0, "acceptance": 1, "proof": 2, "route": 3, "context": 4, "recent": 5}
            projected = [ranks[item["priority"]] for item in session["items"]]
            self.assertEqual(projected, sorted(projected))
            self.assertEqual(session["items"][0]["priority"], "critical")
            proof_items = [item for item in session["items"] if item.get("kind") == "proof"]
            self.assertTrue(proof_items)
            self.assertEqual(proof_items[0]["proof_id"], proof_id)
            self.assertEqual(proof_items[0]["artifact_ref"]["kind"], "orchestration_proof")
            self.assertNotIn("never expose raw prompt", json.dumps(session, ensure_ascii=False))
            self.assertTrue(session["model_free"])
            self.assertTrue(session["content_free"])
            self.assertFalse(session["raw_transcript_included"])

    def test_durable_idempotency_deduplicates_and_rejects_conflicting_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = OrchestrationLedger(root)
            claim = first.claim_idempotency(
                idempotency_key="workflow-1",
                operation="agent_workflow",
                request_hash="hash-a",
                process_instance_id="process-a",
            )
            self.assertTrue(claim["claimed"])
            completed = first.finish_idempotency(
                "workflow-1", request_hash="hash-a", status="completed", summary={"run_id": "run-a"}
            )
            self.assertEqual(completed["status"], "completed")

            restored = OrchestrationLedger(root)
            duplicate = restored.claim_idempotency(
                idempotency_key="workflow-1",
                operation="agent_workflow",
                request_hash="hash-a",
                process_instance_id="process-b",
            )
            self.assertFalse(duplicate["claimed"])
            self.assertEqual(duplicate["reason"], "completed")
            self.assertEqual(duplicate["record"]["summary"]["run_id"], "run-a")

            conflict = restored.claim_idempotency(
                idempotency_key="workflow-1",
                operation="agent_workflow",
                request_hash="hash-b",
                process_instance_id="process-b",
            )
            self.assertEqual(conflict["reason"], "conflict")

    def test_in_progress_idempotency_becomes_unknown_after_process_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            ledger.claim_idempotency(
                idempotency_key="workflow-crash",
                operation="agent_workflow",
                request_hash="hash-crash",
                process_instance_id="old-process",
            )
            changed = ledger.mark_orphaned_idempotency(current_process_instance_id="new-process")
            self.assertEqual(changed, 1)
            record = ledger.get_idempotency("workflow-crash")
            self.assertEqual(record["status"], "unknown")
            self.assertEqual(record["summary"]["outcome_unknown_reason"], "mcp_process_restarted")


if __name__ == "__main__":
    unittest.main()
