from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from coding_tools_mcp.ledger_analysis import open_ledger_analysis_snapshot
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.problem_resolution_economics import ProblemLineageFacts, problem_resolution_economics_report


def _stamp(offset_seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class ProblemResolutionEconomicsTests(unittest.TestCase):
    def _resolved_fixture(self, root: Path) -> None:
        ledger = OrchestrationLedger(root)
        ledger.migrate_problem_lineage_schema()
        run_id = ledger.create_run(objective="fixture only")
        wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", base_head="fixture-head")
        for index, stage in enumerate(("preflight", "execution", "proof", "acceptance")):
            ledger.record_observation_span(
                run_id=run_id,
                wave_id=wave_id,
                span={
                    "span_id": f"fixture-{stage}", "stage": stage, "source": "coding_mcp",
                    "measurement": "observed_stage_duration", "clock_domain": "coding-mcp:fixture",
                    "start_ms": index * 10, "end_ms": index * 10 + 10,
                },
            )
        ledger.record_proof(run_id=run_id, wave_id=wave_id, stage_id="fixture", stage_version="1", input_fingerprint="fixture-proof", status="passed")
        ledger.finish_wave(wave_id, status="accepted")
        ledger.finish_run(run_id, status="accepted")
        problem_id = "problem-fixture"
        ledger.problem_record_event({
            "operation": "open", "event_id": "open-fixture", "problem_id": problem_id, "task_id": "task-fixture",
            "turn_id": "turn-fixture", "trace_id": "trace-fixture", "task_class": "feature", "engineering_floor": "REQUIRED",
            "provenance": "HOST_OBSERVED", "evidence_level": "OBSERVED", "event_time": _stamp(-3),
        }, now=_stamp(-3))
        ledger.problem_record_event({
            "operation": "link", "event_id": "link-fixture", "problem_id": problem_id, "task_id": "task-fixture",
            "turn_id": "turn-fixture", "trace_id": "trace-fixture", "run_id": run_id, "wave_id": wave_id,
            "relation_type": "ENGINEERING_ATTEMPT_BOUND", "link_role": "PRIMARY", "provenance": "DETERMINISTIC_EVIDENCE",
            "evidence_level": "DERIVED_HIGH_CONFIDENCE", "reason_code": "engineering_attempt_bound", "event_time": _stamp(-2),
        }, now=_stamp(-2))
        ledger.problem_record_event({
            "operation": "resolution", "event_id": "provisional-fixture", "problem_id": problem_id, "task_id": "task-fixture",
            "relation_type": "PROVISIONAL_RESOLUTION", "state": "PROVISIONALLY_RESOLVED", "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
            "evidence_level": "OBSERVED", "event_time": _stamp(-1),
        }, now=_stamp(-1))
        ledger.problem_record_event({
            "operation": "feedback", "event_id": "confirm-fixture", "problem_id": problem_id, "task_id": "task-fixture",
            "relation_type": "USER_FEEDBACK", "feedback_intent": "CONFIRM_RESOLVED", "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
            "evidence_level": "OBSERVED", "reason_code": "user_confirmation", "event_time": _stamp(1),
        }, now=_stamp(1))

    def test_immutable_report_describes_confirmed_problem_without_raw_identity_or_money_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._resolved_fixture(root)
            with open_ledger_analysis_snapshot(root) as snapshot:
                self.assertEqual(snapshot.statement_count, 8)
                problems = ProblemLineageFacts.load(snapshot.reader)
                self.assertEqual(snapshot.statement_count, 11)
                report = problem_resolution_economics_report(snapshot.ledger, problems)
                self.assertEqual(snapshot.statement_count, 11)

            self.assertEqual(report["status"], "DESCRIPTIVE_ONLY")
            self.assertEqual(report["denominators"]["problem_threads"], 1)
            self.assertEqual(report["resolution_outcomes"]["confirmed_threads"], 1)
            self.assertEqual(report["resolution_outcomes"]["trusted_technical_resolution"]["true"], 1)
            self.assertEqual(report["ttpr_wall_ms"]["observed_terminal_threads"], 1)
            self.assertEqual(report["restricted_ttpr_ms"]["observed_threads"], 1)
            self.assertEqual(report["resource_and_money_coverage"]["monetary_scalar_status"], "UNKNOWN")
            self.assertFalse(report["resource_and_money_coverage"]["missing_money_is_zero"])
            self.assertNotIn("problem-fixture", json.dumps(report))
            self.assertTrue(report["policy"]["unresolved_threads_right_censored"])

    def test_ambiguous_and_secondary_links_are_missingness_not_double_counted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            ledger.migrate_problem_lineage_schema()
            primary = ledger.create_run(objective="fixture only")
            secondary = ledger.create_run(objective="fixture only")
            problem_id = "problem-open"
            ledger.problem_record_event({
                "operation": "open", "event_id": "open-open", "problem_id": problem_id, "task_id": "task-open",
                "turn_id": "turn-open", "trace_id": "trace-open", "engineering_floor": "REQUIRED",
                "provenance": "HOST_OBSERVED", "evidence_level": "OBSERVED", "event_time": _stamp(-1),
            }, now=_stamp(-1))
            ledger.problem_record_event({
                "operation": "link", "event_id": "primary-open", "problem_id": problem_id, "task_id": "task-open",
                "run_id": primary, "relation_type": "ENGINEERING_ATTEMPT_BOUND", "link_role": "PRIMARY",
                "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "DERIVED_HIGH_CONFIDENCE", "event_time": _stamp(0),
            }, now=_stamp(0))
            ledger.problem_record_event({
                "operation": "link", "event_id": "secondary-open", "problem_id": problem_id, "task_id": "task-open",
                "run_id": secondary, "relation_type": "LINK", "link_role": "SECONDARY",
                "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "DERIVED_HIGH_CONFIDENCE", "event_time": _stamp(0),
            }, now=_stamp(0))
            ledger.problem_record_event({
                "operation": "feedback", "event_id": "ambiguous-open", "task_id": "task-open", "link_status": "AMBIGUOUS",
                "relation_type": "USER_FEEDBACK", "reason_code": "ambiguous_relation", "provenance": "UNKNOWN", "event_time": _stamp(1),
            }, now=_stamp(1))
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_resolution_economics_report(snapshot.ledger, ProblemLineageFacts.load(snapshot.reader))

            self.assertEqual(report["denominators"]["ambiguous_link_events"], 1)
            self.assertEqual(report["denominators"]["right_censored_unresolved_threads"], 1)
            self.assertEqual(report["execution_burden"]["primary_runs"], 1)
            self.assertEqual(report["execution_burden"]["secondary_runs"], 1)
            self.assertEqual(report["execution_burden"]["threads_with_secondary_allocation_missing"], 1)
            self.assertEqual(report["restricted_ttpr_ms"]["observed_threads"], 0)
            self.assertTrue(report["policy"]["no_timestamp_proximity_link"])

    def test_v9_snapshot_is_reported_as_schema_inactive_without_writer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            OrchestrationLedger(root)
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_resolution_economics_report(snapshot.ledger, ProblemLineageFacts.load(snapshot.reader))
            self.assertEqual(report["status"], "PRL_SCHEMA_INACTIVE")
            self.assertTrue(report["policy"]["no_writer"])


if __name__ == "__main__":
    unittest.main()
