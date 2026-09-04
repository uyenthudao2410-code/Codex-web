from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.usage_events import usage_event_from_provider_delegation


class UsageHistoryW9Tests(unittest.TestCase):
    def make_ledger(self) -> tuple[tempfile.TemporaryDirectory[str], OrchestrationLedger, str, str]:
        temp = tempfile.TemporaryDirectory()
        ledger = OrchestrationLedger(Path(temp.name))
        run_id = ledger.create_run(objective="w9-history-test")
        wave_id = ledger.create_wave(
            run_id,
            execution_mode="mcp_only",
            base_head="a" * 40,
            worktree_fp="b" * 64,
        )
        return temp, ledger, run_id, wave_id

    @staticmethod
    def economics(*, measured: bool, input_tokens: int = 10, provider_cost: float = 0.001) -> dict[str, object]:
        return {
            "input_tokens": input_tokens,
            "cached_input_tokens": 2,
            "output_tokens": 4,
            "reasoning_output_tokens": 1,
            "cache_read_tokens": 2,
            "cache_write_tokens": 0,
            "provider_cost": provider_cost,
            "measured": measured,
            "source": "opencode" if measured else "rate_card_estimate",
        }

    def test_exact_only_backfill_is_append_only_and_idempotent(self) -> None:
        temp, ledger, run_id, wave_id = self.make_ledger()
        self.addCleanup(temp.cleanup)

        exact_id = ledger.create_delegation(
            wave_id,
            authority_owner="provider",
            model="deepseek-v4-flash",
            metadata={"provider": "opencode-go", "economics": self.economics(measured=True)},
            delegation_id="historical-exact",
        )
        ledger.finish_delegation(exact_id, status="completed")
        failed_id = ledger.create_delegation(
            wave_id,
            authority_owner="provider",
            model="deepseek-v4-flash",
            metadata={"provider": "opencode-go", "economics": self.economics(measured=True, input_tokens=7)},
            delegation_id="historical-failed-exact",
        )
        ledger.finish_delegation(failed_id, status="failed")
        estimated_id = ledger.create_delegation(
            wave_id,
            authority_owner="provider",
            model="deepseek-v4-flash",
            metadata={"provider": "opencode-go", "economics": self.economics(measured=False, input_tokens=999)},
            delegation_id="historical-estimated",
        )
        ledger.finish_delegation(estimated_id, status="completed")

        exact_before = ledger.get_delegation(exact_id)
        failed_before = ledger.get_delegation(failed_id)
        estimated_before = ledger.get_delegation(estimated_id)
        self.assertIsNotNone(exact_before)
        self.assertIsNotNone(failed_before)
        self.assertIsNotNone(estimated_before)

        first = ledger.backfill_measured_provider_usage(page_size=1)
        self.assertEqual(first["examined"], 3)
        self.assertEqual(first["eligible"], 2)
        self.assertEqual(first["recorded"], 2)
        self.assertEqual(first["already_present"], 0)
        self.assertEqual(first["skipped_unmeasured_or_inexact"], 1)
        self.assertTrue(first["query"]["bounded_keyset"])
        self.assertEqual(first["query"]["page_size"], 1)
        self.assertLessEqual(first["query"]["max_page_rows"], 1)
        self.assertFalse(first["provenance_rewritten"])
        self.assertFalse(first["estimates_promoted"])

        usage_events = ledger.list_usage_events(run_id, limit=None)
        self.assertEqual(len(usage_events), 2)
        by_delegation = {item["delegation_id"]: item for item in usage_events}
        self.assertEqual(set(by_delegation), {exact_id, failed_id})
        self.assertEqual(by_delegation[exact_id]["event_time"], exact_before["finished_at"])
        self.assertEqual(by_delegation[failed_id]["event_time"], failed_before["finished_at"])
        self.assertTrue(all(item["measurement"]["usage"] == "measured" for item in usage_events))

        self.assertEqual(ledger.get_delegation(exact_id)["metadata"], exact_before["metadata"])
        self.assertEqual(ledger.get_delegation(failed_id)["metadata"], failed_before["metadata"])
        self.assertEqual(ledger.get_delegation(estimated_id)["metadata"], estimated_before["metadata"])

        second = ledger.backfill_measured_provider_usage(page_size=2)
        self.assertEqual(second["eligible"], 2)
        self.assertEqual(second["recorded"], 0)
        self.assertEqual(second["already_present"], 2)
        self.assertEqual(len(ledger.list_usage_events(run_id, limit=None)), 2)

    def test_longitudinal_analytics_is_complete_but_page_bounded(self) -> None:
        temp, ledger, run_id, wave_id = self.make_ledger()
        self.addCleanup(temp.cleanup)
        event_time = "2026-09-01T12:00:00.000Z"
        total = 256

        for index in range(total):
            delegation_id = f"bulk-{index:04d}"
            usage_event = usage_event_from_provider_delegation(
                run_id=run_id,
                wave_id=wave_id,
                delegation={
                    "delegation_id": delegation_id,
                    "model": "deepseek-v4-flash",
                    "status": "completed",
                    "metadata": {
                        "provider": "opencode-go",
                        "economics": self.economics(measured=True, input_tokens=1, provider_cost=0.0001),
                    },
                },
            )
            self.assertIsNotNone(usage_event)
            ledger.record_usage_event(
                run_id=run_id,
                wave_id=wave_id,
                delegation_id=delegation_id,
                usage_event=usage_event,
                event_time=event_time,
            )

        started = time.monotonic()
        analytics = ledger.usage_analytics(
            days=365,
            now="2026-09-02T12:00:00.000Z",
            page_size=17,
        )
        elapsed = time.monotonic() - started

        self.assertEqual(analytics["window"]["source_event_count"], total)
        self.assertEqual(analytics["window"]["aggregated_event_count"], total)
        self.assertEqual(analytics["window"]["invalid_event_count"], 0)
        self.assertEqual(analytics["overall"]["usage"]["input_total_tokens"], total)
        self.assertTrue(analytics["query"]["bounded_keyset"])
        self.assertEqual(analytics["query"]["page_size"], 17)
        self.assertGreater(analytics["query"]["pages_read"], 1)
        self.assertLessEqual(analytics["query"]["max_page_rows"], 17)
        self.assertGreaterEqual(analytics["query"]["snapshot_max_seq"], total)
        self.assertLess(elapsed, 5.0)

        coverage = analytics["coverage_by_time"]
        self.assertEqual(coverage["granularity"], "day")
        self.assertEqual(coverage["missing_measurement_policy"], "unknown_not_zero")
        self.assertEqual(len(coverage["buckets"]), 1)
        self.assertEqual(coverage["buckets"][0]["day"], "2026-09-01")
        self.assertEqual(coverage["buckets"][0]["source_event_count"], total)
        self.assertEqual(coverage["buckets"][0]["usage_measurement"]["measured"], total)
        self.assertEqual(analytics["controller_usage"]["status"], "unobserved")
        self.assertEqual(analytics["controller_usage"]["missing_measurement_policy"], "unknown_not_zero")

    def test_w9_query_indexes_exist_and_usage_time_plan_is_indexed(self) -> None:
        temp, ledger, _run_id, _wave_id = self.make_ledger()
        self.addCleanup(temp.cleanup)
        with ledger._lock, ledger._connect() as connection:
            event_indexes = {row["name"] for row in connection.execute("PRAGMA index_list(events)").fetchall()}
            delegation_indexes = {row["name"] for row in connection.execute("PRAGMA index_list(delegations)").fetchall()}
            plan_rows = connection.execute(
                """EXPLAIN QUERY PLAN SELECT * FROM events
                   WHERE event_type='usage_event'
                     AND event_time >= ? AND event_time <= ?
                     AND seq <= ?
                   ORDER BY event_time,seq
                   LIMIT ?""",
                ("2026-01-01T00:00:00.000Z", "2026-12-31T23:59:59.999Z", 999999, 17),
            ).fetchall()
        self.assertIn("idx_events_type_time_seq", event_indexes)
        self.assertIn("idx_events_usage_id", event_indexes)
        self.assertIn("idx_delegations_terminal_finished_id", delegation_indexes)
        plan = " ".join(str(row["detail"]) for row in plan_rows)
        self.assertIn("idx_events_type_time_seq", plan)


if __name__ == "__main__":
    unittest.main()
