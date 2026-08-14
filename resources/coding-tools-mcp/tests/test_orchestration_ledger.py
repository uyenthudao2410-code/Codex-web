from __future__ import annotations

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
