from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from coding_tools_mcp.operator_report import (
    PROBLEM_REPORT_SECTION,
    REPORT_CONTRACT,
    build_operator_completion_report,
)


class _ProblemLedger:
    run_id = "a" * 32
    wave_id = "b" * 32

    def get_run(self, run_id: str) -> dict:
        assert run_id == self.run_id
        return {"status": "active"}

    def list_waves(self, run_id: str) -> list[dict]:
        assert run_id == self.run_id
        return [{"wave_id": self.wave_id, "status": "active"}]

    def list_proofs(self, run_id: str, *, wave_id: str) -> list[dict]:
        return []

    def list_checkpoints(self, run_id: str, *, wave_id: str) -> list[dict]:
        return []

    def list_events(self, run_id: str, *, wave_id: str) -> list[dict]:
        return []

    def wave_objective_provenance(self, run_id: str, wave_id: str) -> dict:
        return {"objective_source": "problem_fixture"}

    def verify_chain(self, run_id: str) -> dict:
        return {"ok": True, "checked": 3}

    def problem_handoff_for_run(self, run_id: str) -> dict:
        return {
            "active_problem_id": "prl-report-visible",
            "problem_revision": 2,
            "problem_state": "OPEN",
            "context_status": "VALID",
            "contract_fingerprint": "c" * 64,
            "contract_capsule_included": True,
            "contract_capsule_omission_reason": None,
            "contract_capsule": {
                "objective_summary": "Make the current Problem visible in operator reports",
                "acceptance_criteria": [
                    {"criterion_id": "report.problem", "summary": "Problem identity is visible"},
                    {"criterion_id": "report.progress", "summary": "Criterion progress is visible"},
                ],
                "unresolved_conditions": ["Live auto-resume proof remains"],
            },
            "latest_feedback_relation": "SAME_PROBLEM_STILL_FAILING",
            "event_count": 7,
            "latest_event": {
                "seq": 7,
                "event_id": "d" * 32,
                "event_hash": "e" * 64,
                "relation_type": "USER_FEEDBACK",
                "state_after": "OPEN",
                "reason_code": "none",
                "recorded_at": "2026-09-11T06:00:00Z",
            },
        }

    def goal_pursuit_live_summary(self, *, run_id: str) -> dict:
        assert run_id == self.run_id
        return {
            "resolution_status": "IN_PROGRESS",
            "completion": {
                "status": "observed",
                "criteria_total": 2,
                "criteria_proven": 1,
                "criteria_unresolved": 1,
                "exact_coverage_status": "PARTIAL",
                "missing_reason": None,
            },
            "next_critical_gap_id": "report.progress",
            "next_critical_gap": "Criterion progress is visible",
            "next_action": "SATISFY_UNRESOLVED_CRITERION",
            "fact_window": {"truncated": False, "missing_reason": None},
        }

    def continuity_telemetry_summary(
        self, *, problem_id: str, problem_revision: int, limit: int
    ) -> dict:
        assert problem_id == "prl-report-visible"
        assert problem_revision == 2
        assert limit == 1000
        return {
            "complete": True,
            "event_count": 9,
            "manual_nudge_count": 2,
            "interruption_count": 1,
            "replan_count": 2,
            "report_gate_count": 3,
            "continuation_attempt_count": 2,
            "continuation_success_count": 1,
            "continuation_failure_count": 1,
            "reconnect_count": 1,
            "restart_count": 0,
            "resume_count": 1,
            "duplicate_effect_prevented_count": 1,
            "terminal_count": 0,
            "blocker_count": 1,
            "accepted_checkpoint_count": 1,
            "time_to_resume_ms": {"count": 1, "total_ms": 80, "max_ms": 80, "avg_ms": 80.0},
            "replan_duration_ms": None,
            "report_gate_wait_ms": {"count": 1, "total_ms": 120, "max_ms": 120, "avg_ms": 120.0},
            "counts_by_code": {"RAW_PROMPT_MUST_NOT_APPEAR": 99},
        }


def _ctx(ledger: _ProblemLedger) -> SimpleNamespace:
    return SimpleNamespace(
        run_id=ledger.run_id,
        wave_id=ledger.wave_id,
        state="REPLAN",
        base_head="f" * 40,
        worktree_fp="1" * 64,
        contract_fp="2" * 64,
    )


class OperatorReportProblemVisibilityTests(unittest.TestCase):
    def test_problem_bound_report_surfaces_authoritative_problem_progress_and_metrics(self) -> None:
        ledger = _ProblemLedger()
        report = build_operator_completion_report(
            ledger=ledger,
            ctx=_ctx(ledger),
            task_state={
                "status": "waiting",
                "modified_files": [],
                "orchestration": {"run_id": ledger.run_id, "wave_id": ledger.wave_id},
            },
            reports={},
        )

        problem = report["problem_resolution"]
        self.assertEqual(report["report_contract"][2], PROBLEM_REPORT_SECTION)
        self.assertEqual(problem["problem_id"], "prl-report-visible")
        self.assertEqual(problem["problem_revision"], 2)
        self.assertEqual(problem["problem_state"], "OPEN")
        self.assertEqual(problem["resolution_status"], "IN_PROGRESS")
        self.assertEqual(problem["objective_summary"], "Make the current Problem visible in operator reports")
        self.assertEqual(problem["progress"]["criteria_total"], 2)
        self.assertEqual(problem["progress"]["criteria_proven"], 1)
        self.assertEqual(problem["progress"]["criteria_unresolved"], 1)
        self.assertEqual(problem["progress"]["coverage_status"], "PARTIAL")
        self.assertEqual(problem["unresolved_conditions"], ["Live auto-resume proof remains"])
        self.assertEqual(problem["current_attempt"]["run_id"], ledger.run_id)
        self.assertEqual(problem["current_attempt"]["wave_id"], ledger.wave_id)
        self.assertEqual(problem["latest_feedback_relation"], "SAME_PROBLEM_STILL_FAILING")
        telemetry = problem["optimization_telemetry"]
        self.assertEqual(telemetry["status"], "AVAILABLE")
        self.assertEqual(telemetry["manual_nudge_count"], 2)
        self.assertEqual(telemetry["report_gate_count"], 3)
        self.assertEqual(telemetry["continuation_failure_count"], 1)
        self.assertEqual(telemetry["duplicate_effect_prevented_count"], 1)
        self.assertNotIn("counts_by_code", telemetry)
        self.assertTrue(problem["content_free"])
        self.assertTrue(problem["derived_projection_only"])
        self.assertFalse(problem["authority_granted"])

        encoded = json.dumps(report, sort_keys=True)
        for forbidden in ("raw_prompt", "transcript", "stdout", "stderr", "private_reasoning"):
            self.assertNotIn(forbidden, encoded.lower())

    def test_non_problem_report_keeps_existing_contract_and_omits_problem_section(self) -> None:
        class NonProblemLedger(_ProblemLedger):
            def problem_handoff_for_run(self, run_id: str) -> None:
                return None

        ledger = NonProblemLedger()
        report = build_operator_completion_report(
            ledger=ledger,
            ctx=_ctx(ledger),
            task_state={"orchestration": {"run_id": ledger.run_id, "wave_id": ledger.wave_id}},
            reports={},
        )
        self.assertEqual(report["report_contract"], REPORT_CONTRACT)
        self.assertNotIn("problem_resolution", report)

    def test_problem_subread_failure_is_visible_as_unavailable_not_inferred(self) -> None:
        class GoalFailureLedger(_ProblemLedger):
            def goal_pursuit_live_summary(self, *, run_id: str) -> dict:
                error = ValueError("details must not be surfaced")
                error.code = "GOAL_FACT_WINDOW_UNAVAILABLE"  # type: ignore[attr-defined]
                raise error

            def continuity_telemetry_summary(self, **kwargs: object) -> dict:
                raise RuntimeError("database path must not be surfaced")

        ledger = GoalFailureLedger()
        report = build_operator_completion_report(
            ledger=ledger,
            ctx=_ctx(ledger),
            task_state={"orchestration": {"run_id": ledger.run_id, "wave_id": ledger.wave_id}},
            reports={},
        )
        problem = report["problem_resolution"]
        self.assertEqual(problem["progress"]["status"], "UNAVAILABLE")
        self.assertEqual(problem["progress"]["missing_reason"], "GOAL_FACT_WINDOW_UNAVAILABLE")
        self.assertEqual(problem["optimization_telemetry"]["status"], "UNAVAILABLE")
        self.assertEqual(problem["optimization_telemetry"]["missing_reason"], "RuntimeError")
        encoded = json.dumps(problem, sort_keys=True)
        self.assertNotIn("details must not be surfaced", encoded)
        self.assertNotIn("database path must not be surfaced", encoded)


if __name__ == "__main__":
    unittest.main()
