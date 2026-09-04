from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.cross_session_continuity_report import CrossSessionContinuityFacts
from coding_tools_mcp.ledger_analysis import open_ledger_analysis_snapshot
from coding_tools_mcp.natural_problem_cohort import natural_problem_cohort_report
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.problem_resolution_economics import ProblemLineageFacts


def capsule(index: int) -> dict[str, object]:
    return {
        "objective_summary": f"Resolve natural Problem {index}",
        "acceptance_criteria": [
            {"criterion_id": f"problem-{index}-criterion-{criterion}", "summary": "Pass"}
            for criterion in range(1, 6)
        ],
        "protected_invariants": [],
        "constraints": [],
        "unresolved_conditions": [],
    }


class NaturalProblemCohortTests(unittest.TestCase):
    def _fixture(self, root: Path, *, count: int = 6, unlabeled_index: int = 0) -> None:
        ledger = OrchestrationLedger(root)
        ledger.migrate_problem_lineage_schema()
        for index in range(1, count + 1):
            problem_id = f"problem-natural-{index}"
            opened = ledger.problem_record_event(
                {
                    "operation": "open",
                    "event_id": f"open-{index}",
                    "problem_id": problem_id,
                    "task_id": f"task-{index}",
                    "task_class": "bugfix",
                    "engineering_floor": "REQUIRED",
                    "contract_capsule": capsule(index),
                    "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
                    "evidence_level": "OBSERVED",
                    "occurred_at": f"2026-09-01T00:{index:02d}:00Z",
                    "occurred_at_source": "EXPLICIT_USER",
                },
                now=f"2026-09-01T00:{index:02d}:01Z",
                authority_context="RUNTIME_EXPLICIT_USER",
            )
            context = {
                "schema_version": 1,
                "work_origin": "problem",
                "resolution_claim": "full_problem",
                "problem_id": problem_id,
                "problem_revision": 1,
                "contract_fingerprint": opened["event"]["contract_fingerprint"],
                "engineering_floor": "REQUIRED",
                "policy_eligible": False,
            }
            metadata = {"workflow": "bugfix", "problem_resolution": context}
            if index != unlabeled_index:
                metadata.update(
                    {
                        "evaluation": {"provenance": "representative"},
                        "provenance_source": "runtime_default_organic_v1",
                    }
                )
            run_id = ledger.create_run(
                objective=f"Natural Problem {index}", metadata=metadata
            )
            wave_id = ledger.create_wave(
                run_id, execution_mode="mcp_only", metadata={"problem_resolution": context}
            )
            ledger.problem_record_event(
                {
                    "operation": "link",
                    "event_id": f"link-{index}",
                    "problem_id": problem_id,
                    "problem_revision": 1,
                    "run_id": run_id,
                    "wave_id": wave_id,
                    "relation_type": "ENGINEERING_ATTEMPT_BOUND",
                    "provenance": "DETERMINISTIC_EVIDENCE",
                    "evidence_level": "OBSERVED",
                },
                now=f"2026-09-01T00:{index:02d}:02Z",
                authority_context="RUNTIME_BINDING",
            )

    def _report(self, root: Path, *, target_n: int = 5) -> dict[str, object]:
        with open_ledger_analysis_snapshot(root) as snapshot:
            problems = ProblemLineageFacts.load(snapshot.reader)
            continuity = CrossSessionContinuityFacts.load(snapshot.reader)
            return natural_problem_cohort_report(
                snapshot.ledger,
                problems,
                continuity,
                start_problem_id="problem-natural-1",
                start_problem_revision=1,
                target_n=target_n,
            )

    def test_fixed_prefix_retains_unverified_row_instead_of_cherry_picking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root, unlabeled_index=3)
            report = self._report(root)
        self.assertEqual(report["status"], "COHORT_PROVENANCE_INCOMPLETE")
        self.assertEqual(len(report["raw_rows"]), 5)
        self.assertEqual(report["raw_rows"][2]["problem_id"], "problem-natural-3")
        self.assertFalse(
            report["raw_rows"][2]["natural_problem_eligibility"]["eligible"]
        )
        self.assertEqual(report["cohort"]["rows_skipped_after_start"], 0)
        self.assertEqual(
            report["decision_checkpoints"]["n5"]["decision"],
            "REJECT_NONCONSECUTIVE_OR_UNVERIFIED_NATURAL_COHORT",
        )

    def test_five_natural_rows_remain_descriptive_until_real_tg6_receipts_exist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root, count=5)
            report = self._report(root)
        self.assertEqual(report["status"], "DESCRIPTIVE_COHORT_CONTINUITY_INCOMPLETE")
        self.assertEqual(report["cohort"]["typed_natural_rows"], 5)
        self.assertEqual(
            report["decision_checkpoints"]["n5"]["real_cross_session_pass_rows"], 0
        )
        self.assertFalse(
            report["tg10_manual_continuity_safety_gate"][
                "manual_continuity_proven_safe"
            ]
        )
        self.assertFalse(report["policy"]["automatic_policy_promotion"])
        self.assertGreater(
            report["missingness"]["missing_or_incomplete_observation_count"], 0
        )

    def test_fact_truncation_blocks_all_partial_cohort_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root, count=5)
            with open_ledger_analysis_snapshot(root) as snapshot:
                problems = ProblemLineageFacts.load(snapshot.reader)
                loaded = CrossSessionContinuityFacts.load(snapshot.reader)
                truncated = CrossSessionContinuityFacts(
                    fact_rows=loaded.fact_rows,
                    available_tables=loaded.available_tables,
                    truncated_tables=frozenset({"events"}),
                    fact_load_statements=loaded.fact_load_statements,
                )
                report = natural_problem_cohort_report(
                    snapshot.ledger,
                    problems,
                    truncated,
                    start_problem_id="problem-natural-1",
                    start_problem_revision=1,
                    target_n=5,
                )
        self.assertEqual(report["status"], "FACT_WINDOW_TRUNCATED")
        self.assertEqual(report["raw_rows"], [])
        self.assertTrue(report["policy"]["no_partial_cohort_projection"])

    def test_missing_exact_start_never_falls_back_to_nearest_problem(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root, count=5)
            with open_ledger_analysis_snapshot(root) as snapshot:
                problems = ProblemLineageFacts.load(snapshot.reader)
                continuity = CrossSessionContinuityFacts.load(snapshot.reader)
                report = natural_problem_cohort_report(
                    snapshot.ledger,
                    problems,
                    continuity,
                    start_problem_id="problem-missing",
                    start_problem_revision=1,
                    target_n=5,
                )
        self.assertEqual(report["status"], "COHORT_START_NOT_FOUND")
        self.assertEqual(report["raw_rows"], [])
        self.assertTrue(report["policy"]["no_nearest_match_or_fallback"])


if __name__ == "__main__":
    unittest.main()
