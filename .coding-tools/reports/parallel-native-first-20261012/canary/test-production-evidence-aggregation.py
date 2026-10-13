"""Offline checks for truthful partial, interval and immutable-history summaries."""
import copy
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("aggregation", Path(__file__).with_name("aggregate-production-evidence.py"))
AGG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AGG)


class AggregationTests(unittest.TestCase):
    def test_partial_canary_never_fills_missing_build_or_closure(self):
        value = AGG.canary([{"operation": "native_first_shared_mcp_canary", "phase": "final", "ok": False,
            "attempt_id": "a" * 32, "proofs": {"read_001": {"action_id": "act_" + "b" * 32}},
            "requires_reconciliation": True, "unresolved_original_actions": ["read_002"]}])
        self.assertEqual(value["proof_counts"]["reads"], 1)
        self.assertEqual(value["proof_counts"]["patches"], 0)
        self.assertIsNone(value["build_proof"])
        self.assertIsNone(value["task_closed_verified"])
        self.assertIsNone(value["counts_agree"])
        self.assertTrue(value["requires_reconciliation"])

    def test_reported_overlap_does_not_replace_measured_intervals(self):
        value = AGG.overlap({"operation": "parallel_native_overlap_canary", "phase": "final", "ok": True,
            "overlap": {"overlap_duration_ms": 10}, "targets": [
                {"proofs": {"node_overlap": {"job_id": "job-first", "started_at_ms": 100, "finished_at_ms": 200}}},
                {"proofs": {"node_overlap": {"job_id": "job-second", "started_at_ms": 210, "finished_at_ms": 300}}}]})
        self.assertEqual(value["derived_overlap_duration_ms"], -10)
        self.assertFalse(value["positive_interval_overlap"])
        value = AGG.overlap({"operation": "parallel_native_overlap_canary", "phase": "final", "targets": []})
        self.assertIsNone(value["positive_interval_overlap"])

    def test_changed_original_receipt_or_settlement_breaks_history_preservation(self):
        before = {"unknown_projection_truncated": False, "historical_unknown_actions_preserved": [
            {"action_id": "act-original", "delivery_state": "reconcile_required", "settled_at_ms": None,
             "delivery_attempts": [{"attempt_id": "try-original"}], "receipts": [{"receipt_state": "unknown"}]}]}
        after = copy.deepcopy(before)
        self.assertTrue(AGG.unknowns(before, after)["preserved_prior_history"])
        after["historical_unknown_actions_preserved"][0]["receipts"][0]["receipt_state"] = "accepted"
        self.assertFalse(AGG.unknowns(before, after)["preserved_prior_history"])
        self.assertIsNone(AGG.unknowns({}, {})["preserved_prior_history"])
        empty = {"unknown_projection_truncated": False, "historical_unknown_actions_preserved": []}
        self.assertIsNone(AGG.unknowns(empty, empty)["preserved_prior_history"])


if __name__ == "__main__":
    unittest.main()
