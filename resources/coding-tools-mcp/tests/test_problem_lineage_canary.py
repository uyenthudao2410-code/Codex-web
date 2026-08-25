from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.ledger_analysis import open_ledger_analysis_snapshot
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.problem_lineage_canary import problem_lineage_canary_report
from coding_tools_mcp.problem_resolution_economics import ProblemLineageFacts


CAPSULE = {
    "objective_summary": "Resolve the canary fixture",
    "acceptance_criteria": [{"criterion_id": "criterion-1", "summary": "Focused proof passes"}],
    "protected_invariants": [],
    "constraints": [],
    "unresolved_conditions": [],
}


class ProblemLineageCanaryTests(unittest.TestCase):
    def test_v11_receipt_is_read_only_and_never_calls_fixture_events_natural(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            ledger.migrate_problem_lineage_schema()
            opened = ledger.problem_record_event(
                {
                    "operation": "open", "event_id": "open", "problem_id": "problem-fixture", "task_id": "task-fixture",
                    "task_class": "bugfix", "engineering_floor": "REQUIRED", "contract_capsule": CAPSULE,
                    "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
                },
                now="2026-08-25T00:00:00Z",
                authority_context="RUNTIME_EXPLICIT_USER",
            )
            run_id = ledger.create_run(objective="fixture")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            ledger.problem_record_event(
                {
                    "operation": "link", "event_id": "link", "problem_id": "problem-fixture", "problem_revision": 1,
                    "run_id": run_id, "wave_id": wave_id, "relation_type": "ENGINEERING_ATTEMPT_BOUND",
                    "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED",
                },
                now="2026-08-25T00:00:01Z",
                authority_context="RUNTIME_BINDING",
            )
            del opened
            ledger_path = root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
            before = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
            with open_ledger_analysis_snapshot(root) as snapshot:
                facts = ProblemLineageFacts.load(snapshot.reader)
                report = problem_lineage_canary_report(snapshot.ledger, facts, integrity_check="ok", foreign_key_violations=0)
            after = hashlib.sha256(ledger_path.read_bytes()).hexdigest()

            self.assertEqual(before, after)
            self.assertEqual(report["status"], "C4_SOURCE_READY_AWAITING_NATURAL_CANARY")
            self.assertFalse(report["natural_evidence"]["attested"])
            self.assertIsNone(report["natural_evidence"]["natural_event_count"])
            self.assertEqual(report["mechanics"]["exact_revision_binding"]["numerator"], 1)
            self.assertEqual(report["mechanics"]["exact_revision_binding"]["denominator"], 1)
            self.assertTrue(report["integrity"]["all_observed_checks_pass"])
            self.assertTrue(report["policy"]["no_writer_or_schema_mutation"])

    def test_inactive_schema_is_not_promoted_to_canary_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            OrchestrationLedger(root)
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_lineage_canary_report(
                    snapshot.ledger,
                    ProblemLineageFacts.load(snapshot.reader),
                    integrity_check="ok",
                    foreign_key_violations=0,
                )
            self.assertEqual(report["status"], "PRL_SCHEMA_INACTIVE")
            self.assertTrue(report["policy"]["no_writer"])

    def test_failed_integrity_gate_is_explicitly_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            ledger.migrate_problem_lineage_schema()
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_lineage_canary_report(
                    snapshot.ledger,
                    ProblemLineageFacts.load(snapshot.reader),
                    integrity_check="not ok",
                    foreign_key_violations=0,
                )
            self.assertEqual(report["status"], "C4_INTEGRITY_BLOCKED")


if __name__ == "__main__":
    unittest.main()
