from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from coding_tools_mcp.ledger_analysis import LedgerReadSession
from coding_tools_mcp.lifecycle_reconciliation import (
    LifecycleReconciliationError,
    logical_ledger_sha256,
)
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


class LifecycleReconciliationTests(unittest.TestCase):
    def _terminal_parent_lane(self, root: Path) -> tuple[OrchestrationLedger, str, str, str]:
        ledger = OrchestrationLedger(root)
        run_id = ledger.create_run(objective="terminal parent")
        wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
        lane_id = ledger.upsert_agent_lane(
            lane_id="lane-terminal-parent",
            run_id=run_id,
            wave_id=wave_id,
            semantic_key="test:terminal-parent",
            role="executor",
            lifecycle="active",
        )
        ledger.finish_run(run_id, status="accepted")
        return ledger, run_id, wave_id, lane_id

    @staticmethod
    def _guards(ledger: OrchestrationLedger, lane_id: str) -> dict[str, object]:
        with LedgerReadSession(ledger.path) as session:
            assert session.connection is not None
            row = session.one(
                """SELECT l.updated_at,l.lifecycle,r.status,l.run_id
                   FROM agent_lanes l JOIN runs r ON r.run_id=l.run_id WHERE l.lane_id=?""",
                (lane_id,),
            )
            assert row is not None
            event = session.one(
                "SELECT seq,event_hash FROM events WHERE run_id=? ORDER BY seq DESC LIMIT 1",
                (str(row["run_id"]),),
            )
            return {
                "expected_logical_sha256": logical_ledger_sha256(session.connection),
                "expected_lane_updated_at": str(row["updated_at"]),
                "expected_run_status": str(row["status"]),
                "expected_run_last_event_seq": int(event["seq"] or 0) if event is not None else 0,
                "expected_run_last_event_hash": str(event["event_hash"] or "") if event is not None else "",
            }

    def test_exact_terminal_parent_lane_reconciliation_is_hash_chained_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger, run_id, wave_id, lane_id = self._terminal_parent_lane(Path(temp))
            result = ledger.reconcile_terminal_parent_lane(
                lane_id=lane_id,
                authority="test-authority",
                **self._guards(ledger, lane_id),
            )
            self.assertTrue(result["changed"])
            self.assertFalse(result["idempotent"])
            self.assertEqual(result["run_id"], run_id)
            self.assertEqual(result["wave_id"], wave_id)
            self.assertEqual(ledger.get_agent_lane(lane_id)["lifecycle"], "closed")
            events = ledger.list_events(run_id)
            self.assertEqual(events[-1]["event_type"], "terminal_parent_lane_reconciled")
            self.assertEqual(events[-1]["state_after"], "CLOSED")
            messages = ledger.list_coordination_messages(lane_id=lane_id)
            self.assertEqual(messages[-1]["kind"], "lane_closed")
            self.assertTrue(ledger.verify_chain(run_id)["ok"])

            replay = ledger.reconcile_terminal_parent_lane(
                lane_id=lane_id,
                authority="test-authority",
                **self._guards(ledger, lane_id),
            )
            self.assertFalse(replay["changed"])
            self.assertTrue(replay["idempotent"])
            self.assertEqual(len([item for item in ledger.list_events(run_id) if item["event_type"] == "terminal_parent_lane_reconciled"]), 1)

    def test_guard_drift_refuses_without_mutating_lane(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger, _run_id, _wave_id, lane_id = self._terminal_parent_lane(Path(temp))
            guards = self._guards(ledger, lane_id)
            guards["expected_logical_sha256"] = "f" * 64
            with self.assertRaisesRegex(LifecycleReconciliationError, "logical ledger snapshot changed"):
                ledger.reconcile_terminal_parent_lane(
                    lane_id=lane_id,
                    authority="test-authority",
                    **guards,
                )
            self.assertEqual(ledger.get_agent_lane(lane_id)["lifecycle"], "active")

    def test_active_parent_is_not_a_reconciliation_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="live parent")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            lane_id = ledger.upsert_agent_lane(
                lane_id="lane-live-parent",
                run_id=run_id,
                wave_id=wave_id,
                semantic_key="test:live-parent",
                role="executor",
                lifecycle="active",
            )
            guards = self._guards(ledger, lane_id)
            guards["expected_run_status"] = "active"
            with self.assertRaisesRegex(LifecycleReconciliationError, "expected parent status is not terminal"):
                ledger.reconcile_terminal_parent_lane(
                    lane_id=lane_id,
                    authority="test-authority",
                    **guards,
                )
            self.assertEqual(ledger.get_agent_lane(lane_id)["lifecycle"], "active")

    @staticmethod
    def _managed_job_guards(ledger: OrchestrationLedger, job_id: str) -> dict[str, object]:
        with LedgerReadSession(ledger.path) as session:
            assert session.connection is not None
            row = session.one("SELECT * FROM managed_process_jobs WHERE job_id=?", (job_id,))
            assert row is not None
            return {
                "expected_logical_sha256": logical_ledger_sha256(session.connection),
                "expected_job_updated_at": str(row["updated_at"]),
                "expected_lifecycle_state": str(row["lifecycle_state"]),
                "expected_checkout_id": str(row["checkout_id"]),
            }

    def _foreign_job(self, root: Path) -> tuple[OrchestrationLedger, str]:
        ledger = OrchestrationLedger(root)
        job_id = "foreign-gone-job"
        with ledger._lock, ledger._connect() as connection:
            connection.execute(
                """INSERT INTO managed_process_jobs(
                    job_id,run_id,wave_id,command_id,owner,checkout_id,resource_class,root_pid,
                    root_process_token,process_instance_id,runtime_instance_id,lifecycle_state,
                    started_at,updated_at,finished_at,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    job_id, "", "", "foreign-command", "foreign-owner", "foreign-checkout", "MEDIUM",
                    4242, "expected-token", "foreign-process", "foreign-runtime", "running",
                    "2026-01-01T00:00:00.000Z", "2026-01-01T00:00:00.000Z", None, "{}",
                ),
            )
        return ledger, job_id

    def test_gone_foreign_job_quiesces_without_terminating_a_process(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger, job_id = self._foreign_job(Path(temp))
            with mock.patch("coding_tools_mcp.execution_resources.process_is_alive", return_value=False):
                result = ledger.reconcile_gone_managed_process_job(
                    job_id=job_id,
                    authority="test-authority",
                    **self._managed_job_guards(ledger, job_id),
                )
            self.assertTrue(result["changed"])
            self.assertEqual(result["lifecycle_state"], "quiesced")
            self.assertEqual(result["recovery_reason"], "root_process_gone")
            self.assertTrue(result["out_of_run_receipt"])
            with LedgerReadSession(ledger.path) as session:
                row = session.one("SELECT lifecycle_state,finished_at FROM managed_process_jobs WHERE job_id=?", (job_id,))
            assert row is not None
            self.assertEqual(row["lifecycle_state"], "quiesced")
            self.assertTrue(str(row["finished_at"] or ""))

    def test_live_matching_foreign_job_remains_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger, job_id = self._foreign_job(Path(temp))
            with (
                mock.patch("coding_tools_mcp.execution_resources.process_is_alive", return_value=True),
                mock.patch("coding_tools_mcp.execution_resources.process_identity_token", return_value="expected-token"),
            ):
                with self.assertRaisesRegex(LifecycleReconciliationError, "remains live"):
                    ledger.reconcile_gone_managed_process_job(
                        job_id=job_id,
                        authority="test-authority",
                        **self._managed_job_guards(ledger, job_id),
                    )
            with LedgerReadSession(ledger.path) as session:
                row = session.one("SELECT lifecycle_state FROM managed_process_jobs WHERE job_id=?", (job_id,))
            assert row is not None
            self.assertEqual(row["lifecycle_state"], "running")

    def test_unbound_live_lane_closes_only_with_exact_logical_and_version_guards(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            lane_id = ledger.upsert_agent_lane(
                lane_id="unbound-lane",
                run_id="",
                wave_id="",
                semantic_key="",
                role="executor",
                lifecycle="active",
            )
            with LedgerReadSession(ledger.path) as session:
                assert session.connection is not None
                lane = session.one("SELECT updated_at FROM agent_lanes WHERE lane_id=?", (lane_id,))
                assert lane is not None
                guards = {
                    "expected_logical_sha256": logical_ledger_sha256(session.connection),
                    "expected_lane_updated_at": str(lane["updated_at"]),
                }
            result = ledger.reconcile_unbound_agent_lane(
                lane_id=lane_id,
                authority="test-authority",
                **guards,
            )
            self.assertTrue(result["changed"])
            self.assertTrue(result["out_of_run_receipt"])
            self.assertEqual(ledger.get_agent_lane(lane_id)["lifecycle"], "closed")
            messages = ledger.list_coordination_messages(lane_id=lane_id)
            self.assertEqual(messages[-1]["kind"], "lane_closed")


if __name__ == "__main__":
    unittest.main()
