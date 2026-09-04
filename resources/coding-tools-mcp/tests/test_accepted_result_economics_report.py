from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.accepted_result_economics_report import accepted_result_economics_report
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.usage_events import build_usage_event, usage_event_from_controller_report


class AcceptedResultEconomicsReportTests(unittest.TestCase):
    def test_w6_multi_wave_economics_separates_final_rework_and_preserves_plane_overlap_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="multi-wave economics", metadata={"workflow": "feature"})
            rework_wave = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="a" * 40)
            rework_controller = usage_event_from_controller_report(run_id=run_id, wave_id=rework_wave, report={
                "schema_version": 1, "turn_id": "turn-rework", "trace_id": "trace-rework",
                "provider_id": "openai", "model_id": "gpt-5.6-sol", "source": "client_reported",
                "accounting_profile": "openai_compatible", "input_tokens": 100, "cached_input_tokens": 30,
                "output_tokens": 20, "reasoning_output_tokens": 5, "monetary_cost": 0.01,
            })
            rework_provider = build_usage_event(run_id=run_id, wave_id=rework_wave, delegation_id="provider-rework", provider_id="fixture", model_id="fixture-model", status="completed", source="provider-fixture", input_tokens=80, output_tokens=12, provider_cost=0.003)
            for event in (rework_controller, rework_provider):
                ledger.record_usage_event(run_id=run_id, wave_id=rework_wave, delegation_id=str(event["delegation_id"]), usage_event=event)
            ledger.finish_wave(rework_wave, status="replanned")

            final_wave = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="a" * 40)
            final_controller = usage_event_from_controller_report(run_id=run_id, wave_id=final_wave, report={
                "schema_version": 1, "turn_id": "turn-final", "trace_id": "trace-final",
                "provider_id": "openai", "model_id": "gpt-5.6-sol", "source": "client_reported",
                "accounting_profile": "openai_compatible", "input_tokens": 50, "cached_input_tokens": 10,
                "output_tokens": 10, "reasoning_output_tokens": 2, "monetary_cost": 0.005,
            })
            final_provider = build_usage_event(run_id=run_id, wave_id=final_wave, delegation_id="provider-final", provider_id="fixture", model_id="fixture-model", status="completed", source="provider-fixture", input_tokens=40, output_tokens=8, provider_cost=0.002)
            for event in (final_controller, final_provider):
                ledger.record_usage_event(run_id=run_id, wave_id=final_wave, delegation_id=str(event["delegation_id"]), usage_event=event)
            ledger.finish_wave(final_wave, status="accepted")
            ledger.finish_run(run_id, status="accepted")

            performance = {
                "run_metrics": {run_id: {"tool_calls": 2, "errors": 0, "local_execution_ms": 20, "estimated_wait_ms": 0, "request_bytes": 30, "response_bytes": 60, "model_visible_bytes": 15}},
                "recent": [
                    {"run_id": run_id, "wave_id": rework_wave, "ok": True, "duration_ms": 8, "request_bytes": 10, "response_bytes": 20, "model_visible_bytes": 5, "invocation": {"invocation_id": "inv-rework", "turn_id": "turn-rework", "trace_context": {"trace_id": "trace-rework"}}},
                    {"run_id": run_id, "wave_id": final_wave, "ok": True, "duration_ms": 12, "request_bytes": 20, "response_bytes": 40, "model_visible_bytes": 10, "invocation": {"invocation_id": "inv-final", "turn_id": "turn-final", "trace_context": {"trace_id": "trace-final"}}},
                ],
            }
            (root / ".coding-tools" / "performance.json").write_text(json.dumps(performance), encoding="utf-8")
            report = accepted_result_economics_report(root, ledger, source_head="a" * 40, source_worktree_clean=True)
            run = report["accepted_result_economics"]["runs"][0]
            self.assertEqual(run["final_wave_id"], final_wave)
            self.assertEqual(run["rework_wave_ids"], [rework_wave])
            self.assertEqual(run["usage"]["rework"]["controller"]["usage"]["total_tokens"], 120)
            self.assertEqual(run["usage"]["final"]["controller"]["usage"]["total_tokens"], 60)
            self.assertEqual(run["usage"]["rework"]["provider"]["usage"]["total_tokens"], 92)
            self.assertEqual(run["usage"]["final"]["provider"]["usage"]["total_tokens"], 48)
            self.assertEqual(run["coverage"]["controller_usage"], 1.0)
            self.assertEqual(run["coverage"]["provider_usage"], 1.0)
            self.assertEqual(run["coverage"]["tool_invocation"], 1.0)
            self.assertEqual(run["coverage"]["exact_run_attribution"], 1.0)
            self.assertTrue(run["tool_context"]["split_complete"])
            self.assertEqual(run["tool_context"]["final_rework_split"]["rework"]["model_visible_bytes"], 5)
            self.assertEqual(run["tool_context"]["final_rework_split"]["final"]["model_visible_bytes"], 10)
            self.assertEqual(run["correlation"]["turn_ids"], ["turn-final", "turn-rework"])
            self.assertEqual(run["correlation"]["trace_ids"], ["trace-final", "trace-rework"])
            self.assertIsNone(run["system_totals"]["tokens"])
            self.assertIsNone(run["system_totals"]["cost_usd"])
            self.assertEqual(run["system_totals"]["reason"], "cross_plane_overlap_not_proven")
            self.assertFalse(report["resource_vector"]["monetary_and_token_coverage"]["car_available"])

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
