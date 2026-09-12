from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from coding_tools_mcp.ledger_analysis import LedgerReadSession
from coding_tools_mcp.lifecycle_reconciliation import LifecycleReconciliationError, logical_ledger_sha256
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.stale_run_reconciliation import (
    ExactStaleRunReconciliationError,
    preflight_exact_stale_runs_reconciliation,
    preflight_exact_stale_run_reconciliation,
    reconcile_exact_stale_runs,
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

    def test_live_owned_managed_job_is_not_global_reconciliation_residue(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="abandoned")
            ledger.create_wave(run_id, execution_mode="mcp_only")
            observed_at = self._future()

            from coding_tools_mcp import stale_run_reconciliation as stale_module
            original = stale_module.lifecycle_census

            def with_live_owned_job(*args, **kwargs):
                census = original(*args, **kwargs)
                census["managed_jobs"] = [{"classification": "LIVE_OWNED", "run_id": "unrelated-live-run"}]
                return census

            with mock.patch.object(stale_module, "lifecycle_census", side_effect=with_live_owned_job):
                preflight = preflight_exact_stale_run_reconciliation(root, run_id=run_id, observed_at=observed_at)

            self.assertFalse(preflight["lifecycle"]["managed_job_residue"])

    def test_managed_job_residue_classifications_still_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="abandoned")
            ledger.create_wave(run_id, execution_mode="mcp_only")
            observed_at = self._future()

            from coding_tools_mcp import stale_run_reconciliation as stale_module
            original = stale_module.lifecycle_census

            for classification in ("STALE_MANAGED_JOB_RESIDUE", "ORPHANED_OR_FOREIGN_MANAGED_JOB"):
                with self.subTest(classification=classification):
                    def with_residue(*args, _classification=classification, **kwargs):
                        census = original(*args, **kwargs)
                        census["managed_jobs"] = [{"classification": _classification}]
                        return census

                    with mock.patch.object(stale_module, "lifecycle_census", side_effect=with_residue):
                        with self.assertRaisesRegex(ExactStaleRunReconciliationError, "managed_job_residue"):
                            preflight_exact_stale_run_reconciliation(root, run_id=run_id, observed_at=observed_at)

    def test_batch_uses_one_preflight_one_postflight_and_reconciles_all_targets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_ids = [ledger.create_run(objective=f"abandoned-{index}") for index in range(4)]
            for run_id in run_ids:
                ledger.create_wave(run_id, execution_mode="mcp_only")
            observed_at = self._future()

            from coding_tools_mcp import stale_run_reconciliation as stale_module
            with mock.patch.object(stale_module, "lifecycle_census", wraps=stale_module.lifecycle_census) as census:
                receipt = reconcile_exact_stale_runs(
                    root,
                    run_ids=run_ids,
                    observed_at=observed_at,
                    runtime_stopped=True,
                    authority="test-batch-authority",
                ).projection()

            self.assertEqual(census.call_count, 2)
            self.assertTrue(receipt["reconciliation"]["changed"])
            self.assertTrue(receipt["reconciliation"]["chain_ok"])
            self.assertEqual([item["run_id"] for item in receipt["reconciliation"]["results"]], run_ids)
            self.assertEqual([item["run_id"] for item in receipt["postflight"]["targets"]], run_ids)
            for run_id in run_ids:
                self.assertEqual(ledger.get_run(run_id)["status"], "stale")
                self.assertTrue(ledger.verify_chain(run_id)["ok"])

    def test_batch_guard_failure_rolls_back_without_prefix_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_ids = [ledger.create_run(objective=f"rollback-{index}") for index in range(3)]
            for run_id in run_ids:
                ledger.create_wave(run_id, execution_mode="mcp_only")
            observed_at = self._future()
            preflight = preflight_exact_stale_runs_reconciliation(root, run_ids=run_ids, observed_at=observed_at)
            targets = [
                {
                    "run_id": target["run_id"],
                    "status": target["status"],
                    "latest_activity_at": target["latest_activity_at"],
                    "last_event_seq": target["last_event_seq"],
                    "last_event_hash": target["last_event_hash"],
                }
                for target in preflight["targets"]
            ]
            targets[1]["last_event_seq"] = int(targets[1]["last_event_seq"]) + 1

            with self.assertRaisesRegex(LifecycleReconciliationError, "batch guard changed"):
                ledger.reconcile_exact_stale_runs(
                    targets=targets,
                    expected_logical_sha256=str(preflight["snapshot"]["logical_sha256"]),
                    observed_at_unix_seconds=observed_at,
                    stale_after_seconds=float(preflight["stale_after_seconds"]),
                    authority="test-batch-authority",
                )
            for run_id in run_ids:
                self.assertEqual(ledger.get_run(run_id)["status"], "active")
                self.assertFalse(any(item["event_type"] == "run_stale_reconciled" for item in ledger.list_events(run_id)))
                self.assertTrue(ledger.verify_chain(run_id)["ok"])


if __name__ == "__main__":
    unittest.main()
