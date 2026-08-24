from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from coding_tools_mcp.ledger_analysis import LedgerReadSession
from coding_tools_mcp.lifecycle_reconciliation import LifecycleReconciliationError, logical_ledger_sha256
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.stale_run_reconciliation import (
    ExactStaleRunReconciliationError,
    preflight_exact_stale_run_reconciliation,
    reconcile_exact_stale_run,
)


class ExactStaleRunReconciliationTests(unittest.TestCase):
    @staticmethod
    def _future() -> float:
        # The production maintenance threshold is 24 hours.  Keep this fixture
        # beyond that same threshold rather than weakening the authority for a
        # unit test.
        return time.time() + (48 * 60 * 60)

    @staticmethod
    def _activate(root: Path, run_id: str, *, observed_at: float) -> dict[str, object]:
        preflight = preflight_exact_stale_run_reconciliation(root, run_id=run_id, observed_at=observed_at)
        snapshot = preflight["snapshot"]
        return reconcile_exact_stale_run(
            root,
            run_id=run_id,
            observed_at=observed_at,
            expected_snapshot_sha256=str(snapshot["sha256"]),
            expected_logical_sha256=str(snapshot["logical_sha256"]),
            runtime_stopped=True,
            authority="test-authority",
        ).projection()

    def test_exact_reconciliation_is_hash_chained_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="abandoned")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            observed_at = self._future()

            receipt = self._activate(root, run_id, observed_at=observed_at)
            self.assertTrue(receipt["reconciliation"]["changed"])
            self.assertTrue(receipt["reconciliation"]["chain_ok"])
            self.assertEqual(ledger.get_run(run_id)["status"], "stale")
            self.assertEqual(next(item for item in ledger.list_waves(run_id) if item["wave_id"] == wave_id)["status"], "aborted")
            events = ledger.list_events(run_id)
            self.assertEqual(events[-1]["event_type"], "run_stale_reconciled")
            self.assertTrue(any(item["event_type"] == "wave_lifecycle_reconciled" for item in events))
            self.assertTrue(ledger.verify_chain(run_id)["ok"])

            replay = self._activate(root, run_id, observed_at=observed_at)
            self.assertFalse(replay["reconciliation"]["changed"])
            self.assertTrue(replay["reconciliation"]["idempotent"])
            self.assertEqual(replay["postflight"]["target"]["classification"], "RECONCILED_STALE")
            self.assertEqual(len([item for item in ledger.list_events(run_id) if item["event_type"] == "run_stale_reconciled"]), 1)

    def test_terminal_run_without_exact_receipt_is_not_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="already terminal")
            ledger.finish_run(run_id, status="stale")
            with self.assertRaisesRegex(ExactStaleRunReconciliationError, "absent from the immutable lifecycle census"):
                preflight_exact_stale_run_reconciliation(root, run_id=run_id, observed_at=self._future())

    def test_guard_drift_refuses_without_mutating_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="abandoned")
            ledger.create_wave(run_id, execution_mode="mcp_only")
            observed_at = self._future()
            preflight = preflight_exact_stale_run_reconciliation(root, run_id=run_id, observed_at=observed_at)
            ledger.append_event(run_id, event_type="guard_drift", state_after="PREFLIGHT", payload={})
            target = preflight["target"]
            snapshot = preflight["snapshot"]
            with self.assertRaisesRegex(LifecycleReconciliationError, "logical ledger snapshot changed"):
                ledger.reconcile_exact_stale_run(
                    run_id=run_id,
                    expected_logical_sha256=str(snapshot["logical_sha256"]),
                    expected_run_status=str(target["status"]),
                    expected_latest_activity_at=str(target["latest_activity_at"]),
                    expected_run_last_event_seq=int(target["last_event_seq"]),
                    expected_run_last_event_hash=str(target["last_event_hash"]),
                    observed_at_unix_seconds=observed_at,
                    stale_after_seconds=float(preflight["stale_after_seconds"]),
                    authority="test-authority",
                )
            self.assertEqual(ledger.get_run(run_id)["status"], "active")

    def test_live_owner_and_runtime_stop_boundaries_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="still owned")
            ledger.create_wave(run_id, execution_mode="mcp_only")
            ledger.upsert_hub_client(client_id="controller", client_type="chatweb", role="controller")
            ledger.acquire_controller_lease(run_id=run_id, owner_client_id="controller", lease_id="live", ttl_seconds=10_000_000)
            with self.assertRaisesRegex(ExactStaleRunReconciliationError, "target_not_threshold_candidate"):
                preflight_exact_stale_run_reconciliation(root, run_id=run_id, observed_at=self._future())

            inactive = ledger.create_run(objective="inactive")
            ledger.create_wave(inactive, execution_mode="mcp_only")
            observed_at = self._future()
            preflight = preflight_exact_stale_run_reconciliation(root, run_id=inactive, observed_at=observed_at)
            snapshot = preflight["snapshot"]
            with self.assertRaisesRegex(ExactStaleRunReconciliationError, "stopped-runtime"):
                reconcile_exact_stale_run(
                    root,
                    run_id=inactive,
                    observed_at=observed_at,
                    expected_snapshot_sha256=str(snapshot["sha256"]),
                    expected_logical_sha256=str(snapshot["logical_sha256"]),
                    runtime_stopped=False,
                    authority="test-authority",
                )
            self.assertEqual(ledger.get_run(inactive)["status"], "active")

    def test_exact_method_never_uses_bulk_stale_helper(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="abandoned")
            ledger.create_wave(run_id, execution_mode="mcp_only")
            observed_at = self._future()
            preflight = preflight_exact_stale_run_reconciliation(root, run_id=run_id, observed_at=observed_at)
            target = preflight["target"]
            snapshot = preflight["snapshot"]
            original = ledger.reconcile_stale_runs
            ledger.reconcile_stale_runs = lambda **_kwargs: (_ for _ in ()).throw(AssertionError("bulk reconciliation must not run"))  # type: ignore[method-assign]
            try:
                result = ledger.reconcile_exact_stale_run(
                    run_id=run_id,
                    expected_logical_sha256=str(snapshot["logical_sha256"]),
                    expected_run_status=str(target["status"]),
                    expected_latest_activity_at=str(target["latest_activity_at"]),
                    expected_run_last_event_seq=int(target["last_event_seq"]),
                    expected_run_last_event_hash=str(target["last_event_hash"]),
                    observed_at_unix_seconds=observed_at,
                    stale_after_seconds=float(preflight["stale_after_seconds"]),
                    authority="test-authority",
                )
            finally:
                ledger.reconcile_stale_runs = original  # type: ignore[method-assign]
            self.assertTrue(result["changed"])
            with LedgerReadSession(ledger.path) as session:
                assert session.connection is not None
                self.assertEqual(logical_ledger_sha256(session.connection), logical_ledger_sha256(session.connection))


if __name__ == "__main__":
    unittest.main()
