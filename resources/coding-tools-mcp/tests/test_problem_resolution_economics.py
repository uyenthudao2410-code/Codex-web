from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.ledger_analysis import open_ledger_analysis_snapshot
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.problem_resolution_economics import ProblemLineageFacts, problem_resolution_economics_report


CAPSULE = {
    "objective_summary": "Resolve the report fixture",
    "acceptance_criteria": [{"criterion_id": "criterion-1", "summary": "Focused proof passes"}],
    "protected_invariants": [], "constraints": [], "unresolved_conditions": [],
}


class ProblemResolutionEconomicsTests(unittest.TestCase):
    def _fixture(self, root: Path) -> None:
        ledger = OrchestrationLedger(root)
        ledger.migrate_problem_lineage_schema()
        opened = ledger.problem_record_event({
            "operation": "open", "event_id": "open", "problem_id": "problem-fixture", "task_id": "task-fixture",
            "task_class": "bugfix", "engineering_floor": "REQUIRED", "contract_capsule": CAPSULE,
            "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
            "occurred_at": "2026-08-25T00:00:00Z", "occurred_at_source": "EXPLICIT_USER",
        }, now="2026-08-25T00:00:01Z", authority_context="RUNTIME_EXPLICIT_USER")
        fingerprint = opened["event"]["contract_fingerprint"]
        context = {"schema_version": 1, "work_origin": "problem", "resolution_claim": "full_problem", "problem_id": "problem-fixture", "problem_revision": 1, "contract_fingerprint": fingerprint, "engineering_floor": "REQUIRED", "policy_eligible": False}
        run_id = ledger.create_run(objective="fixture", metadata={"problem_resolution": context})
        wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", metadata={"problem_resolution": context})
        ledger.problem_record_event({
            "operation": "link", "event_id": "link", "problem_id": "problem-fixture", "problem_revision": 1,
            "run_id": run_id, "wave_id": wave_id, "relation_type": "ENGINEERING_ATTEMPT_BOUND",
            "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED",
        }, now="2026-08-25T00:00:02Z", authority_context="RUNTIME_BINDING")
        proof = ledger.record_proof(run_id=run_id, wave_id=wave_id, stage_id="focused", stage_version="1", input_fingerprint="proof", status="passed")
        ledger.problem_record_coverage_manifest(run_id=run_id, wave_id=wave_id, manifest={"criterion-1": [proof]})
        checkpoint = ledger.record_checkpoint(run_id=run_id, wave_id=wave_id, git_head="head", proof_fingerprint="proof", status="accepted")
        ledger.problem_record_provisional_from_eocl(run_id=run_id, wave_id=wave_id, checkpoint_id=checkpoint, now="2026-08-25T00:00:03Z")
        ledger.problem_record_event({
            "operation": "confirm", "event_id": "confirm", "problem_id": "problem-fixture", "problem_revision": 1,
            "feedback_intent": "CONFIRM_RESOLVED", "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
            "occurred_at": "2026-08-25T00:01:00Z", "occurred_at_source": "EXPLICIT_USER",
        }, now="2026-08-25T00:01:01Z", authority_context="RUNTIME_EXPLICIT_USER")

    def test_report_separates_resolution_from_administrative_disposition(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self._fixture(root)
            with open_ledger_analysis_snapshot(root) as snapshot:
                facts = ProblemLineageFacts.load(snapshot.reader)
                report = problem_resolution_economics_report(snapshot.ledger, facts)
            self.assertEqual(report["status"], "DESCRIPTIVE_ONLY")
            self.assertEqual(report["denominators"]["problem_threads"], 1)
            self.assertEqual(report["resolution_outcomes"]["confirmed_threads"], 1)
            self.assertEqual(report["resolution_outcomes"]["trusted_resolution"]["true"], 1)
            self.assertEqual(report["mechanics_coverage"]["full_claim_waves_with_structural_manifest"], 1)
            self.assertTrue(report["resolution_outcomes"]["administrative_disposition_is_not_resolution"])
            self.assertEqual(report["time_to_administrative_disposition"]["observed"], 0)
            self.assertIn("attested_occurrence_clock_missing", report["time_to_provisional"]["missing_or_invalid_reason_counts"])

    def test_v9_snapshot_is_inactive_and_writer_free(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); OrchestrationLedger(root)
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_resolution_economics_report(snapshot.ledger, ProblemLineageFacts.load(snapshot.reader))
            self.assertEqual(report["status"], "PRL_SCHEMA_INACTIVE")
            self.assertTrue(report["policy"]["no_writer"])


if __name__ == "__main__":
    unittest.main()
