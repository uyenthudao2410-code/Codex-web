from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.orchestration_ledger import (
    HANDOFF_CAPSULE_MAX_BYTES,
    OrchestrationLedger,
)


class CoordinationStateTests(unittest.TestCase):
    def test_hub_clients_and_independent_cursors_survive_store_recreation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            ledger.upsert_hub_client(
                client_id="chatweb",
                client_type="chatweb",
                role="controller",
                runtime_instance_id="runtime-1",
                contract_sha="abc",
            )
            ledger.upsert_hub_client(
                client_id="codex-desktop",
                client_type="codex_desktop",
                role="worker",
                runtime_instance_id="runtime-1",
                contract_sha="abc",
            )
            ledger.create_run(run_id="run-1", objective="hub cursor test")
            ledger.advance_hub_client_cursor(client_id="chatweb", run_id="run-1", last_event_seq=12)
            ledger.advance_hub_client_cursor(client_id="codex-desktop", run_id="run-1", last_event_seq=7)
            ledger.advance_hub_client_cursor(client_id="chatweb", run_id="run-1", last_event_seq=5)

            restored = OrchestrationLedger(root)
            clients = {row["client_id"]: row for row in restored.list_hub_clients()}
            self.assertTrue(clients["chatweb"]["online"])
            self.assertTrue(clients["codex-desktop"]["online"])
            self.assertEqual(clients["chatweb"]["runtime_instance_id"], "runtime-1")
            self.assertEqual(restored.get_hub_client_cursor(client_id="chatweb", run_id="run-1")["last_event_seq"], 12)
            self.assertEqual(restored.get_hub_client_cursor(client_id="codex-desktop", run_id="run-1")["last_event_seq"], 7)

    def test_controller_lease_is_separate_fenced_and_rejects_competing_owner(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            ledger.create_run(run_id="run-1", objective="controller test")
            ledger.upsert_hub_client(client_id="chatweb", client_type="chatweb", role="controller")
            ledger.upsert_hub_client(client_id="codex-desktop", client_type="codex_desktop", role="worker")
            first = ledger.acquire_controller_lease(
                run_id="run-1", owner_client_id="chatweb", lease_id="lease-chat", ttl_seconds=60
            )
            self.assertTrue(first["acquired"])
            self.assertEqual(first["fencing_token"], 1)
            renewed = ledger.acquire_controller_lease(
                run_id="run-1", owner_client_id="chatweb", lease_id="lease-chat", ttl_seconds=60
            )
            self.assertTrue(renewed["acquired"])
            self.assertTrue(renewed["renewed"])
            self.assertEqual(renewed["fencing_token"], 1)
            blocked = ledger.acquire_controller_lease(
                run_id="run-1", owner_client_id="codex-desktop", lease_id="lease-desktop", ttl_seconds=60
            )
            self.assertFalse(blocked["acquired"])
            self.assertEqual(blocked["reason"], "active_lease")
            self.assertTrue(ledger.assert_controller_lease(
                run_id="run-1", owner_client_id="chatweb", lease_id="lease-chat", fencing_token=1
            )["valid"])
            self.assertFalse(ledger.assert_controller_lease(
                run_id="run-1", owner_client_id="chatweb", lease_id="lease-chat", fencing_token=0
            )["valid"])

    def test_controller_expiry_allows_new_owner_with_incremented_token(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            ledger.create_run(run_id="run-1", objective="controller expiry test")
            ledger.upsert_hub_client(client_id="chatweb", client_type="chatweb", role="controller")
            ledger.upsert_hub_client(client_id="codex-desktop", client_type="codex_desktop", role="worker")
            first = ledger.acquire_controller_lease(
                run_id="run-1", owner_client_id="chatweb", lease_id="lease-chat", ttl_seconds=1
            )
            with ledger._lock, ledger._connect() as connection:
                connection.execute(
                    "UPDATE controller_leases SET expires_at=0 WHERE run_id='run-1'"
                )
            second = ledger.acquire_controller_lease(
                run_id="run-1", owner_client_id="codex-desktop", lease_id="lease-desktop", ttl_seconds=60
            )
            self.assertTrue(second["acquired"])
            self.assertEqual(second["fencing_token"], first["fencing_token"] + 1)
            self.assertEqual(second["owner_client_id"], "codex-desktop")

    def test_controller_expiry_same_owner_reacquires_with_incremented_token(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            ledger.create_run(run_id="run-1", objective="controller same-owner expiry test")
            ledger.upsert_hub_client(client_id="chatweb", client_type="chatweb", role="controller")
            first = ledger.acquire_controller_lease(
                run_id="run-1", owner_client_id="chatweb", lease_id="client:chatweb", ttl_seconds=1
            )
            with ledger._lock, ledger._connect() as connection:
                connection.execute("UPDATE controller_leases SET expires_at=0 WHERE run_id='run-1'")
            second = ledger.acquire_controller_lease(
                run_id="run-1", owner_client_id="chatweb", lease_id="client:chatweb", ttl_seconds=60
            )
            self.assertTrue(second["acquired"])
            self.assertFalse(second["renewed"])
            self.assertEqual(second["fencing_token"], first["fencing_token"] + 1)
            self.assertEqual(second["owner_client_id"], "chatweb")

    def test_operator_controller_transfer_requires_online_registered_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            ledger.create_run(run_id="run-1", objective="controller transfer test")
            ledger.upsert_hub_client(client_id="chatweb", client_type="chatweb", role="controller")
            ledger.acquire_controller_lease(
                run_id="run-1", owner_client_id="chatweb", lease_id="lease-chat", ttl_seconds=60
            )
            offline = ledger.operator_transfer_controller(
                run_id="run-1", target_client_id="codex-desktop", lease_id="lease-desktop"
            )
            self.assertFalse(offline["transferred"])
            self.assertEqual(offline["reason"], "target_offline")
            ledger.upsert_hub_client(client_id="codex-desktop", client_type="codex_desktop", role="worker")
            moved = ledger.operator_transfer_controller(
                run_id="run-1", target_client_id="codex-desktop", lease_id="lease-desktop"
            )
            self.assertTrue(moved["transferred"])
            self.assertEqual(moved["owner_client_id"], "codex-desktop")
            self.assertEqual(moved["fencing_token"], 2)
            self.assertFalse(ledger.assert_controller_lease(
                run_id="run-1", owner_client_id="chatweb", lease_id="lease-chat", fencing_token=1
            )["valid"])

    def test_hub_authority_and_cursor_reject_unknown_references(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            ledger.upsert_hub_client(client_id="chatweb", client_type="chatweb", role="controller")
            with self.assertRaisesRegex(ValueError, "run does not exist"):
                ledger.advance_hub_client_cursor(client_id="chatweb", run_id="missing", last_event_seq=1)
            ledger.create_run(run_id="run-1", objective="reference validation")
            with self.assertRaisesRegex(ValueError, "not registered"):
                ledger.advance_hub_client_cursor(client_id="missing", run_id="run-1", last_event_seq=1)
            with self.assertRaisesRegex(ValueError, "not registered"):
                ledger.acquire_controller_lease(
                    run_id="run-1", owner_client_id="missing", lease_id="lease-missing", ttl_seconds=60
                )
            with self.assertRaisesRegex(ValueError, "run does not exist"):
                ledger.acquire_controller_lease(
                    run_id="missing", owner_client_id="chatweb", lease_id="lease-chat", ttl_seconds=60
                )

    def test_only_one_live_lane_can_claim_a_semantic_workstream(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            first = ledger.upsert_agent_lane(
                lane_id="lane-1",
                run_id="run-1",
                semantic_key="finance:recovery",
                lifecycle="active",
            )
            second = ledger.upsert_agent_lane(
                lane_id="lane-2",
                run_id="run-1",
                semantic_key="finance:recovery",
                lifecycle="active",
            )
            self.assertEqual(first, "lane-1")
            self.assertEqual(second, "lane-1")
            self.assertEqual(
                [row["lane_id"] for row in ledger.list_agent_lanes(run_id="run-1")],
                ["lane-1"],
            )

    def test_agent_lane_survives_store_recreation_and_semantic_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = OrchestrationLedger(root)
            first.upsert_agent_lane(
                lane_id="lane-1",
                run_id="run-1",
                wave_id="wave-1",
                semantic_key="finance:invoice-recovery",
                role="executor",
                thread_id="thread-1",
                session_id="session-1",
                lifecycle="waiting",
                profile="cross_file",
                model="gpt-5.6-terra",
                effort="high",
                base_head="abc",
                worktree_fp="work",
                contract_fp="contract",
                last_turn_id="turn-1",
                metadata={"owner": "codex"},
            )

            restored = OrchestrationLedger(root)
            lane = restored.find_agent_lane(
                run_id="run-1",
                semantic_key="finance:invoice-recovery",
            )
            self.assertIsNotNone(lane)
            assert lane is not None
            self.assertEqual(lane["thread_id"], "thread-1")
            self.assertEqual(lane["session_id"], "session-1")
            self.assertEqual(lane["metadata"]["owner"], "codex")

            updated = restored.update_agent_lane(
                "lane-1",
                lifecycle="active",
                last_turn_id="turn-2",
                metadata={"resumed": True},
            )
            self.assertIsNotNone(updated)
            assert updated is not None
            self.assertEqual(updated["lifecycle"], "active")
            self.assertEqual(updated["last_turn_id"], "turn-2")
            self.assertTrue(updated["metadata"]["resumed"])

    def test_coordination_message_is_durable_redacted_and_acknowledgeable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            message_id = ledger.append_coordination_message(
                run_id="run-1",
                wave_id="wave-1",
                lane_id="lane-1",
                direction="chatweb_to_codex",
                kind="instruction",
                payload={"summary": "inspect invariant", "prompt": "do not persist me"},
                base_head="abc",
                worktree_fp="work",
            )

            restored = OrchestrationLedger(root)
            messages = restored.list_coordination_messages(
                run_id="run-1",
                status="pending",
            )
            self.assertEqual([row["message_id"] for row in messages], [message_id])
            self.assertEqual(messages[0]["payload"]["summary"], "inspect invariant")
            self.assertTrue(messages[0]["payload"]["prompt"]["redacted"])
            self.assertNotIn("do not persist me", str(messages[0]))

            acknowledged = restored.acknowledge_coordination_message(message_id)
            self.assertIsNotNone(acknowledged)
            assert acknowledged is not None
            self.assertEqual(acknowledged["status"], "acknowledged")
            self.assertTrue(acknowledged["acknowledged_at"])

    def test_handoff_capsule_is_bounded_hashed_and_latest_is_restorable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            created = ledger.record_handoff_capsule(
                run_id="run-1",
                wave_id="wave-1",
                conversation_epoch=2,
                payload={
                    "goal": "continue durable coordination",
                    "accept": ["tests green", "single final authority"],
                    "active_lane_ids": ["lane-1"],
                    "next_action": "resume lane-1",
                },
            )
            self.assertLessEqual(created["bytes"], HANDOFF_CAPSULE_MAX_BYTES)
            self.assertEqual(len(created["sha256"]), 64)

            latest = OrchestrationLedger(root).latest_handoff_capsule(run_id="run-1")
            self.assertIsNotNone(latest)
            assert latest is not None
            self.assertEqual(latest["conversation_epoch"], 2)
            self.assertEqual(latest["payload"]["next_action"], "resume lane-1")
            self.assertEqual(latest["sha256"], created["sha256"])

            with self.assertRaises(ValueError):
                ledger.record_handoff_capsule(
                    run_id="run-1",
                    payload={"goal": "x" * (HANDOFF_CAPSULE_MAX_BYTES + 100)},
                )

    def test_background_operation_becomes_truthfully_orphaned_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = OrchestrationLedger(root)
            first.start_background_operation(
                operation_id="operation-1",
                server_instance_id="server-old",
                tool="agent_workflow",
                task_id="task-1",
                run_id="run-1",
                wave_id="wave-1",
                summary={"objective": "long task"},
            )

            restored = OrchestrationLedger(root)
            changed = restored.mark_orphaned_background_operations(
                current_server_instance_id="server-new"
            )
            self.assertEqual(changed, 1)
            operation = restored.get_background_operation("operation-1")
            self.assertIsNotNone(operation)
            assert operation is not None
            self.assertEqual(operation["status"], "orphaned")
            self.assertEqual(
                operation["summary"]["orphan_reason"],
                "mcp_runtime_restarted",
            )


if __name__ == "__main__":
    unittest.main()
