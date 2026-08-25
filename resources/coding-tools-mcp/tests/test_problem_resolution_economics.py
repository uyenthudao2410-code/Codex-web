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
        # The reporter fixture needs an observed deterministic technical pass;
        # its direct ledger setup is not an EOCL acceptance/reconciliation test.
        ledger.problem_record_event({
            "operation": "provisional_resolve", "event_id": "provisional", "problem_id": "problem-fixture", "problem_revision": 1,
            "run_id": run_id, "wave_id": wave_id, "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED",
            "occurred_at": "2026-08-25T00:00:30Z", "occurred_at_source": "RUNTIME",
        }, now="2026-08-25T00:00:31Z", authority_context="RUNTIME_EOCL")
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
            self.assertEqual(report["denominators"]["problem_chain_invalid_threads"], 0)
            self.assertTrue(report["resolution_outcomes"]["administrative_disposition_is_not_resolution"])
            self.assertEqual(report["time_to_administrative_disposition"]["observed"], 0)
            self.assertIn("attested_clock_authority_mismatch", report["time_to_provisional"]["missing_or_invalid_reason_counts"])

    def test_v9_snapshot_is_inactive_and_writer_free(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); OrchestrationLedger(root)
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_resolution_economics_report(snapshot.ledger, ProblemLineageFacts.load(snapshot.reader))
            self.assertEqual(report["status"], "PRL_SCHEMA_INACTIVE")
            self.assertTrue(report["policy"]["no_writer"])

    def test_revision_metrics_do_not_reinterpret_an_older_confirmed_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self._fixture(root)
            ledger = OrchestrationLedger(root)
            current = ledger.problem_get("problem-fixture")["current_revision"]
            revised = ledger.problem_record_event({
                "operation": "revise", "event_id": "revise-2", "problem_id": "problem-fixture",
                "expected_revision": 1, "expected_contract_fingerprint": current["contract_fingerprint"],
                "task_class": "bugfix", "engineering_floor": "REQUIRED", "contract_capsule": CAPSULE,
                "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
                "occurred_at": "2026-08-25T00:02:00Z", "occurred_at_source": "EXPLICIT_USER",
            }, now="2026-08-25T00:02:01Z", authority_context="RUNTIME_EXPLICIT_USER")
            self.assertEqual(revised["event"]["relation_type"], "REVISION")
            self.assertEqual(revised["thread"]["thread"]["resolution_state"], "OPEN")
            ledger.problem_record_event({
                "operation": "block", "event_id": "block-2", "problem_id": "problem-fixture", "problem_revision": 2,
                "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED",
                "reason_code": "blocked_external_dependency",
                "occurred_at": "2026-08-25T00:03:00Z", "occurred_at_source": "RUNTIME",
            }, now="2026-08-25T00:03:01Z", authority_context="RUNTIME_GUARD")
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_resolution_economics_report(snapshot.ledger, ProblemLineageFacts.load(snapshot.reader))
            self.assertEqual(report["analysis_unit"]["primary"], "problem_revision")
            self.assertEqual(report["denominators"]["analysis_problem_revisions"], 2)
            self.assertEqual(report["resolution_outcomes"]["trusted_resolution"]["true"], 1)
            self.assertEqual(report["time_to_confirmed_resolution"]["observed"], 1)

    def test_clock_authority_mismatch_is_missing_not_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self._fixture(root)
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_resolution_economics_report(snapshot.ledger, ProblemLineageFacts.load(snapshot.reader))
            metric = report["time_to_provisional"]
            self.assertEqual(metric["observed"], 0)
            self.assertEqual(metric["ordered_exact_values_ms_when_n_le_20"], None)
            self.assertEqual(metric["missing_or_invalid_reason_counts"]["attested_clock_authority_mismatch"], 1)


if __name__ == "__main__":
    unittest.main()
