from __future__ import annotations

import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

from coding_tools_mcp.completed_agent_lane_reconciliation import (
    ExactCompletedAgentLaneReconciliationError,
    preflight_exact_completed_agent_lane_reconciliation,
    reconcile_exact_completed_agent_lane,
)
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


class ExactCompletedAgentLaneReconciliationTests(unittest.TestCase):
    @staticmethod
    def _observed_at() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    @staticmethod
    def _fixture(root: Path, *, state: str = "ACCEPTING") -> tuple[OrchestrationLedger, dict[str, str]]:
        ledger = OrchestrationLedger(root)
        run_id = ledger.create_run(objective="external review")
        wave_id = ledger.create_wave(run_id, execution_mode="deep_single_lane")
        ledger.append_event(run_id, wave_id=wave_id, event_type="review_submitted", state_after=state, payload={})
        values = {
            "lane_id": "lane-external-review",
            "run_id": run_id,
            "wave_id": wave_id,
            "semantic_key": "test:external-review",
            "thread_id": "thread-external-review",
            "session_id": "thread-external-review",
            "expected_lane_last_turn_id": "turn-interrupted",
            "external_completed_turn_id": "turn-completed",
            "external_thread_status": "idle",
            "externally_observed_at": ExactCompletedAgentLaneReconciliationTests._observed_at(),
        }
        ledger.upsert_agent_lane(
            lane_id=values["lane_id"],
            run_id=run_id,
            wave_id=wave_id,
            semantic_key=values["semantic_key"],
            role="reviewer",
            thread_id=values["thread_id"],
            session_id=values["session_id"],
            lifecycle="active",
            last_turn_id=values["expected_lane_last_turn_id"],
        )
        return ledger, values

    @staticmethod
    def _preflight(root: Path, values: dict[str, str]) -> dict[str, object]:
        return preflight_exact_completed_agent_lane_reconciliation(
            root,
            **values,
            observed_at=time.time(),
        )

    def _reconcile(self, root: Path, values: dict[str, str]) -> dict[str, object]:
        preflight = self._preflight(root, values)
        snapshot = preflight["snapshot"]
        assert isinstance(snapshot, dict)
        return reconcile_exact_completed_agent_lane(
            root,
            **values,
            observed_at=time.time(),
            expected_snapshot_sha256=str(snapshot["sha256"]),
            expected_logical_sha256=str(snapshot["logical_sha256"]),
            runtime_stopped=True,
            authority="test-authority",
        ).projection()

    def test_exact_completed_lane_reconciliation_is_hash_chained_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger, values = self._fixture(root)
            receipt = self._reconcile(root, values)
            self.assertTrue(receipt["reconciliation"]["changed"])
            self.assertTrue(receipt["reconciliation"]["chain_ok"])
            self.assertEqual(ledger.get_agent_lane(values["lane_id"])["lifecycle"], "closed")
            self.assertEqual(ledger.get_run(values["run_id"])["status"], "active")
            self.assertEqual(ledger.list_waves(values["run_id"])[0]["status"], "active")
            events = ledger.list_events(values["run_id"])
            self.assertEqual(events[-1]["event_type"], "completed_agent_lane_reconciled")
            self.assertEqual(events[-1]["state_after"], "ACCEPTING")
            self.assertEqual(events[-1]["payload"]["external_completed_turn_id"], "turn-completed")
            messages = ledger.list_coordination_messages(lane_id=values["lane_id"])
            self.assertEqual(messages[-1]["kind"], "completed_agent_lane_reconciled")
            self.assertTrue(ledger.verify_chain(values["run_id"])["ok"])

            replay = self._reconcile(root, values)
            self.assertFalse(replay["reconciliation"]["changed"])
            self.assertTrue(replay["reconciliation"]["idempotent"])
            self.assertEqual(
                len([item for item in ledger.list_events(values["run_id"]) if item["event_type"] == "completed_agent_lane_reconciled"]),
                1,
            )

    def test_snapshot_drift_refuses_without_closing_lane(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger, values = self._fixture(root)
            preflight = self._preflight(root, values)
            snapshot = preflight["snapshot"]
            assert isinstance(snapshot, dict)
            ledger.append_event(
                values["run_id"],
                wave_id=values["wave_id"],
                event_type="guard_drift",
                state_after="ACCEPTING",
                payload={},
            )
            with self.assertRaisesRegex(ExactCompletedAgentLaneReconciliationError, "physical snapshot changed"):
                reconcile_exact_completed_agent_lane(
                    root,
                    **values,
                    observed_at=time.time(),
                    expected_snapshot_sha256=str(snapshot["sha256"]),
                    expected_logical_sha256=str(snapshot["logical_sha256"]),
                    runtime_stopped=True,
                    authority="test-authority",
                )
            self.assertEqual(ledger.get_agent_lane(values["lane_id"])["lifecycle"], "active")

    def test_exact_thread_identity_mismatch_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger, values = self._fixture(root)
            values["thread_id"] = "wrong-thread"
            with self.assertRaisesRegex(ExactCompletedAgentLaneReconciliationError, "thread_id_mismatch"):
                self._preflight(root, values)
            self.assertEqual(ledger.get_agent_lane(values["lane_id"])["lifecycle"], "active")

    def test_non_accepting_parent_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger, values = self._fixture(root, state="PROVING")
            with self.assertRaisesRegex(ExactCompletedAgentLaneReconciliationError, "parent_run_not_accepting"):
                self._preflight(root, values)
            self.assertEqual(ledger.get_agent_lane(values["lane_id"])["lifecycle"], "active")

    def test_live_controller_ownership_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger, values = self._fixture(root)
            ledger.upsert_hub_client(client_id="controller", client_type="chatweb", role="controller")
            ledger.acquire_controller_lease(
                run_id=values["run_id"],
                owner_client_id="controller",
                lease_id="live-controller",
                ttl_seconds=10_000,
            )
            with self.assertRaisesRegex(ExactCompletedAgentLaneReconciliationError, "competing_live_ownership"):
                self._preflight(root, values)
            self.assertEqual(ledger.get_agent_lane(values["lane_id"])["lifecycle"], "active")

    def test_interrupted_lane_turn_cannot_be_reused_as_completion_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger, values = self._fixture(root)
            values["external_completed_turn_id"] = values["expected_lane_last_turn_id"]
            with self.assertRaisesRegex(ExactCompletedAgentLaneReconciliationError, "completion_turn_not_later"):
                self._preflight(root, values)
            self.assertEqual(ledger.get_agent_lane(values["lane_id"])["lifecycle"], "active")

    def test_runtime_stopped_attestation_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger, values = self._fixture(root)
            preflight = self._preflight(root, values)
            snapshot = preflight["snapshot"]
            assert isinstance(snapshot, dict)
            with self.assertRaisesRegex(ExactCompletedAgentLaneReconciliationError, "stopped-runtime"):
                reconcile_exact_completed_agent_lane(
                    root,
                    **values,
                    observed_at=time.time(),
                    expected_snapshot_sha256=str(snapshot["sha256"]),
                    expected_logical_sha256=str(snapshot["logical_sha256"]),
                    runtime_stopped=False,
                    authority="test-authority",
                )
            self.assertEqual(ledger.get_agent_lane(values["lane_id"])["lifecycle"], "active")


if __name__ == "__main__":
    unittest.main()
