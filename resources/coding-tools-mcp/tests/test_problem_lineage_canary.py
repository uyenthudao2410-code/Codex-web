from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.ledger_analysis import open_ledger_analysis_snapshot
from coding_tools_mcp.acceptance_receipts import passed_proof_fingerprint
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

ENVELOPE = {
    "schema_version": 1,
    "direct_outcomes": [{"outcome_id": "outcome-1", "summary": "The bounded user outcome is observable"}],
    "relevant_invariants": ["Preserve the existing public contract"],
    "truth_domains": ["source", "runtime"],
    "adjacent_risks": [], "excluded_scope": ["Unrelated modules"],
    "required_evidence": [{"evidence_id": "evidence-1", "kind": "focused_proof", "provenance": "exact accepted wave", "status": "observed"}],
    "closure_falsification_probe": {"probe_id": "probe-1", "method": "Run the focused closure check", "expected_failure_signal": "The bounded outcome remains contradicted", "executed": True, "result": "passed"},
}


class ProblemLineageCanaryTests(unittest.TestCase):
    @staticmethod
    def _accepted_files(run_id: str, wave_id: str) -> dict[str, object]:
        return {"schema_version": 2, "source": "task_modified_files", "complete": True, "count": 0, "total_bytes": 0, "run_id": run_id, "wave_id": wave_id, "files": [], "incomplete_reasons": []}

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

    def test_current_revision_projection_tamper_blocks_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            ledger.migrate_problem_lineage_schema()
            ledger.problem_record_event({
                "operation": "open", "event_id": "open", "problem_id": "problem-fixture", "task_id": "task-fixture",
                "task_class": "bugfix", "engineering_floor": "REQUIRED", "contract_capsule": CAPSULE,
                "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
            }, now="2026-08-25T00:00:00Z", authority_context="RUNTIME_EXPLICIT_USER")
            path = root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
            connection = sqlite3.connect(path)
            try:
                connection.execute("UPDATE problem_threads SET current_revision=2 WHERE problem_id='problem-fixture'")
                connection.commit()
            finally:
                connection.close()
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_lineage_canary_report(snapshot.ledger, ProblemLineageFacts.load(snapshot.reader), integrity_check="ok", foreign_key_violations=0)
            self.assertEqual(report["status"], "C4_INTEGRITY_BLOCKED")
            self.assertGreater(report["integrity"]["current_revision_projection_invalid_threads"], 0)

    def test_encoded_private_capsule_blocks_even_with_recomputed_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            ledger.migrate_problem_lineage_schema()
            ledger.problem_record_event({
                "operation": "open", "event_id": "open", "problem_id": "problem-fixture", "task_id": "task-fixture",
                "task_class": "bugfix", "engineering_floor": "REQUIRED", "contract_capsule": CAPSULE,
                "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
            }, now="2026-08-25T00:00:00Z", authority_context="RUNTIME_EXPLICIT_USER")
            capsule = {**CAPSULE, "objective_summary": "api%5Fkey%3Dsupersecretvalue"}
            raw = json.dumps(capsule, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            path = root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
            connection = sqlite3.connect(path)
            try:
                connection.execute("UPDATE problem_revisions SET typed_contract_capsule=?, contract_fingerprint=? WHERE problem_id='problem-fixture' AND revision=1", (raw, hashlib.sha256(raw.encode()).hexdigest()))
                connection.commit()
            finally:
                connection.close()
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_lineage_canary_report(snapshot.ledger, ProblemLineageFacts.load(snapshot.reader), integrity_check="ok", foreign_key_violations=0)
            self.assertEqual(report["status"], "C4_INTEGRITY_BLOCKED")
            self.assertGreater(report["integrity"]["revision_contract_invalid_revisions"], 0)

    def test_exact_proof_checkpoint_and_bridge_are_required_for_full_claim_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            ledger.migrate_problem_lineage_schema()
            opened = ledger.problem_record_event({
                "operation": "open", "event_id": "open", "problem_id": "problem-fixture", "task_id": "task-fixture",
                "task_class": "bugfix", "engineering_floor": "REQUIRED", "contract_capsule": CAPSULE,
                "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
            }, now="2026-08-25T00:00:00Z", authority_context="RUNTIME_EXPLICIT_USER")
            context = {"schema_version": 1, "work_origin": "problem", "resolution_claim": "full_problem", "problem_id": "problem-fixture", "problem_revision": 1, "contract_fingerprint": opened["event"]["contract_fingerprint"], "engineering_floor": "REQUIRED", "policy_eligible": False}
            run_id = ledger.create_run(objective="fixture", metadata={"problem_resolution": context})
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", metadata={"problem_resolution": context})
            ledger.problem_record_event({
                "operation": "link", "event_id": "link", "problem_id": "problem-fixture", "problem_revision": 1,
                "run_id": run_id, "wave_id": wave_id, "relation_type": "ENGINEERING_ATTEMPT_BOUND",
                "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED",
            }, now="2026-08-25T00:00:01Z", authority_context="RUNTIME_BINDING")
            proof_id = ledger.record_proof(run_id=run_id, wave_id=wave_id, stage_id="focused", stage_version="1", input_fingerprint="proof", status="passed")
            proofs = ledger.list_proofs(run_id, wave_id=wave_id)
            proof_fp = passed_proof_fingerprint(proofs)
            files = self._accepted_files(run_id, wave_id)
            outcome = ledger.problem_prepare_eocl_outcome_claim(run_id=run_id, wave_id=wave_id, git_head="head", worktree_fp="worktree", proof_fingerprint=proof_fp, accepted_files=files, durable_mutation=False, coverage_manifest={"criterion-1": [proof_id]}, resolution_envelope=ENVELOPE)
            checkpoint = ledger.accept_checkpoint_atomic(run_id=run_id, wave_id=wave_id, git_head="head", proof_fingerprint=proof_fp, metadata={"worktree_fp": "worktree", "accepted_files": files, "problem_outcome_claim": outcome["claim"], "problem_outcome_claim_sha256": outcome["claim_sha256"]})
            ledger.problem_record_provisional_from_eocl(run_id=run_id, wave_id=wave_id, checkpoint_id=checkpoint["checkpoint_id"], now="2026-08-26T23:59:59Z")
            with open_ledger_analysis_snapshot(root) as snapshot:
                report = problem_lineage_canary_report(snapshot.ledger, ProblemLineageFacts.load(snapshot.reader), integrity_check="ok", foreign_key_violations=0)
            coverage = report["mechanics"]["criterion_to_proof_structural_coverage"]
            self.assertEqual(coverage["denominator"], 1)
            self.assertEqual(coverage["numerator"], 1)
            self.assertEqual(coverage["invalid_reason_counts"], {})


if __name__ == "__main__":
    unittest.main()
