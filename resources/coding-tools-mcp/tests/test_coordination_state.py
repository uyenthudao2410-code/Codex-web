from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.orchestration_ledger import (
    HANDOFF_CAPSULE_MAX_BYTES,
    OrchestrationLedger,
)


class CoordinationStateTests(unittest.TestCase):
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
