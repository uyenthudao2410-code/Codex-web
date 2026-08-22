from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.accepted_result_economics_report import accepted_result_economics_report
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


class AcceptedResultEconomicsReportTests(unittest.TestCase):
    def test_current_source_dre_and_resource_vector_preserve_unknown_cost(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            head = "a" * 40
            first = ledger.create_run(objective="feature", metadata={"workflow": "feature"})
            first_wave = ledger.create_wave(first, execution_mode="mcp_only", base_head=head)
            ledger.finish_wave(first_wave, status="accepted")
            ledger.finish_run(first, status="accepted")
            repaired = ledger.create_run(objective="bugfix", metadata={"workflow": "bugfix"})
            repair_wave = ledger.create_wave(repaired, execution_mode="mcp_only", base_head=head)
            ledger.append_event(repaired, wave_id=repair_wave, event_type="failure_observed", state_before="EXECUTING", state_after="REPLAN", payload={"failure_class": "BASE_DRIFT"})
            ledger.finish_wave(repair_wave, status="replanned")
            accepted_wave = ledger.create_wave(repaired, execution_mode="mcp_only", base_head=head)
            ledger.append_event(repaired, wave_id=accepted_wave, event_type="failure_observed", state_before="PROVING", state_after="REPLAN", payload={"failure_class": "SOL_REJECTED"})
            ledger.finish_wave(accepted_wave, status="accepted")
            ledger.finish_run(repaired, status="accepted")
            performance = {"local_execution_ms": 100, "estimated_wait_ms": 700, "run_metrics": {first: {"local_execution_ms": 20, "estimated_wait_ms": 30, "tool_calls": 2, "errors": 0, "request_bytes": 10, "response_bytes": 100, "model_visible_bytes": 20}, repaired: {"local_execution_ms": 80, "estimated_wait_ms": 670, "tool_calls": 5, "errors": 1, "request_bytes": 20, "response_bytes": 200, "model_visible_bytes": 30}}}
            (root / ".coding-tools" / "performance.json").write_text(json.dumps(performance), encoding="utf-8")
            report = accepted_result_economics_report(root, ledger, source_head=head, source_worktree_clean=True)
            current = report["current_source_dre"]
            self.assertEqual(current["accepted_runs"], 2)
            self.assertEqual(current["mechanisms"]["source_base_drift"]["events"], 1)
            self.assertEqual(current["mechanisms"]["acceptance_correction"]["events"], 1)
            self.assertTrue(current["exact_current_source_window"])
            resource = report["resource_vector"]
            self.assertEqual(resource["all_accepted"]["estimated_wait_to_local_execution_ratio"], 7.0)
            self.assertFalse(resource["monetary_and_token_coverage"]["missing_monetary_cost_is_zero"])
            self.assertFalse(resource["monetary_and_token_coverage"]["car_available"])

    def test_dirty_source_keeps_head_window_descriptive_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            head = "a" * 40
            run_id = ledger.create_run(objective="feature", metadata={"workflow": "feature"})
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head=head)
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")
            current = accepted_result_economics_report(root, ledger, source_head=head, source_worktree_clean=False)["current_source_dre"]
            self.assertFalse(current["exact_current_source_window"])
            self.assertEqual(current["decision_status"], "head_window_descriptive_current_worktree_not_clean")

    def test_current_source_window_fails_honestly_when_no_run_matches_head(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="feature", metadata={"workflow": "feature"})
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="b" * 40)
            ledger.finish_wave(wave_id, status="accepted")
            ledger.finish_run(run_id, status="accepted")
            current = accepted_result_economics_report(root, ledger, source_head="a" * 40, source_worktree_clean=True)["current_source_dre"]
            self.assertEqual(current["accepted_runs"], 0)
            self.assertEqual(current["decision_status"], "insufficient_head_window_volume")


if __name__ == "__main__":
    unittest.main()
