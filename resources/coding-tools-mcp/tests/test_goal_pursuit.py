from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.acceptance_receipts import passed_proof_fingerprint
from coding_tools_mcp.errors import JsonRpcError, ToolFailure
from coding_tools_mcp.goal_pursuit import GoalPursuitError
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.tool_schema import input_schemas, validate_arguments


NOW = "2026-09-01T00:00:00+00:00"


def capsule(label: str = "Goal", criteria: int = 2) -> dict[str, object]:
    return {
        "objective_summary": f"Resolve {label}",
        "acceptance_criteria": [
            {"criterion_id": f"{label.lower()}-criterion-{index}", "summary": f"{label} criterion {index} passes"}
            for index in range(1, criteria + 1)
        ],
        "protected_invariants": ["Preserve the eight-tool contract"],
        "constraints": ["No inferred authority"],
        "unresolved_conditions": [],
    }


def open_problem(ledger: OrchestrationLedger, label: str) -> dict[str, object]:
    return ledger.problem_record_event(
        {
            "operation": "open",
            "event_id": f"open-{label.lower()}",
            "task_id": f"task-{label.lower()}",
            "task_class": "feature",
            "engineering_floor": "REQUIRED",
            "contract_capsule": capsule(label),
            "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
            "evidence_level": "OBSERVED",
        },
        now=NOW,
        authority_context="RUNTIME_EXPLICIT_USER",
    )


def problem_context(opened: dict[str, object]) -> dict[str, object]:
    event = opened["event"]
    return {
        "schema_version": 1,
        "work_origin": "problem",
        "resolution_claim": "full_problem",
        "problem_id": event["problem_id"],
        "problem_revision": 1,
        "contract_fingerprint": event["contract_fingerprint"],
        "engineering_floor": "REQUIRED",
        "policy_eligible": False,
    }


def bind_run(
    ledger: OrchestrationLedger,
    opened: dict[str, object],
    *,
    suffix: str,
) -> tuple[str, str]:
    context = problem_context(opened)
    run_id = ledger.create_run(objective=f"attempt-{suffix}", metadata={"problem_resolution": context})
    wave_id = ledger.create_wave(
        run_id,
        execution_mode="mcp_only",
        metadata={"problem_resolution": context},
    )
    ledger.problem_record_event(
        {
            "operation": "link",
            "event_id": f"bind-{suffix}",
            "problem_id": opened["event"]["problem_id"],
            "problem_revision": 1,
            "run_id": run_id,
            "wave_id": wave_id,
            "relation_type": "ENGINEERING_ATTEMPT_BOUND",
            "provenance": "DETERMINISTIC_EVIDENCE",
            "evidence_level": "OBSERVED",
        },
        now=NOW,
        authority_context="RUNTIME_BINDING",
    )
    return run_id, wave_id


def resolution_envelope() -> dict[str, object]:
    return {
        "schema_version": 1,
        "direct_outcomes": [
            {"outcome_id": "goal-outcome", "summary": "The bounded Goal outcome is observable"}
        ],
        "relevant_invariants": ["Preserve the eight-tool contract"],
        "truth_domains": ["source", "runtime"],
        "adjacent_risks": [],
        "excluded_scope": ["Unrelated modules"],
        "required_evidence": [
            {
                "evidence_id": "goal-evidence",
                "kind": "focused_proof",
                "provenance": "exact accepted wave",
                "status": "observed",
            }
        ],
        "closure_falsification_probe": {
            "probe_id": "goal-probe",
            "method": "Re-run exact criterion proofs",
            "expected_failure_signal": "At least one criterion is not proven",
            "executed": True,
            "result": "passed",
        },
    }


def accepted_files(run_id: str, wave_id: str) -> dict[str, object]:
    return {
        "schema_version": 2,
        "source": "task_modified_files",
        "complete": True,
        "count": 0,
        "total_bytes": 0,
        "run_id": run_id,
        "wave_id": wave_id,
        "files": [],
        "incomplete_reasons": [],
    }


class GoalPursuitIdentityTests(unittest.TestCase):
    def test_only_unresolved_goal_is_exact_without_timestamp_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = OrchestrationLedger(Path(directory))
            ledger.migrate_problem_lineage_schema()
            opened = open_problem(ledger, "Alpha")
            identity = ledger.goal_pursuit_resolve_identity()
            self.assertEqual(identity["status"], "EXACT")
            self.assertEqual(identity["reason"], "ONLY_UNRESOLVED_GOAL")
            self.assertEqual(identity["problem_id"], opened["event"]["problem_id"])
            self.assertFalse(identity["timestamp_selection_used"])

    def test_multiple_unresolved_goals_fail_closed_to_bounded_sorted_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = OrchestrationLedger(Path(directory))
            ledger.migrate_problem_lineage_schema()
            first = open_problem(ledger, "Zulu")
            second = open_problem(ledger, "Alpha")
            with self.assertRaises(GoalPursuitError) as ambiguous:
                ledger.goal_pursuit_resolve_identity()
            self.assertEqual(ambiguous.exception.code, "GOAL_IDENTITY_AMBIGUOUS")
            self.assertEqual(ambiguous.exception.details["candidate_count"], 2)
            ids = [item["problem_id"] for item in ambiguous.exception.details["candidates"]]
            self.assertEqual(ids, sorted(ids))
            self.assertEqual(
                set(ids),
                {first["event"]["problem_id"], second["event"]["problem_id"]},
            )
            self.assertFalse(ambiguous.exception.details["timestamp_selection_used"])

    def test_unresolved_goal_candidates_are_paginated_without_skip_or_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = OrchestrationLedger(Path(directory))
            ledger.migrate_problem_lineage_schema()
            expected = sorted(
                str(open_problem(ledger, f"Paged-{index:02d}")["event"]["problem_id"])
                for index in range(13)
            )
            observed: list[str] = []
            cursor = ""
            while True:
                with self.assertRaises(GoalPursuitError) as ambiguous:
                    ledger.goal_pursuit_resolve_identity(
                        candidate_cursor=cursor,
                        candidate_limit=5,
                    )
                self.assertEqual(ambiguous.exception.code, "GOAL_IDENTITY_AMBIGUOUS")
                details = ambiguous.exception.details
                self.assertEqual(details["candidate_count"], 13)
                self.assertLessEqual(len(details["candidates"]), 5)
                observed.extend(item["problem_id"] for item in details["candidates"])
                next_cursor = details["next_candidate_cursor"]
                if not next_cursor:
                    self.assertFalse(details["candidate_page_has_more"])
                    break
                self.assertTrue(details["candidate_page_has_more"])
                cursor = next_cursor
            self.assertEqual(observed, expected)
            self.assertEqual(len(observed), len(set(observed)))

    def test_goal_candidate_cursor_fails_closed_when_backlog_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = OrchestrationLedger(Path(directory))
            ledger.migrate_problem_lineage_schema()
            for index in range(12):
                open_problem(ledger, f"Snapshot-{index:02d}")
            with self.assertRaises(GoalPursuitError) as first_page:
                ledger.goal_pursuit_resolve_identity(candidate_limit=4)
            cursor = first_page.exception.details["next_candidate_cursor"]
            self.assertTrue(cursor)
            open_problem(ledger, "Snapshot-New")
            with self.assertRaises(GoalPursuitError) as changed:
                ledger.goal_pursuit_resolve_identity(
                    candidate_cursor=cursor,
                    candidate_limit=4,
                )
            self.assertEqual(changed.exception.code, "GOAL_CANDIDATE_SNAPSHOT_CHANGED")

    def test_goal_candidate_cursor_is_tamper_evident_and_query_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = OrchestrationLedger(Path(directory))
            ledger.migrate_problem_lineage_schema()
            for index in range(12):
                open_problem(ledger, f"Tamper-{index:02d}")
            with self.assertRaises(GoalPursuitError) as first_page:
                ledger.goal_pursuit_resolve_identity(candidate_limit=4)
            cursor = first_page.exception.details["next_candidate_cursor"]
            tampered = cursor[:-1] + ("A" if cursor[-1] != "A" else "B")
            with self.assertRaises(GoalPursuitError) as invalid:
                ledger.goal_pursuit_resolve_identity(candidate_cursor=tampered)
            self.assertEqual(invalid.exception.code, "GOAL_CANDIDATE_CURSOR_INVALID")
            with self.assertRaises(GoalPursuitError) as scope_mismatch:
                ledger.goal_pursuit_resolve_identity(
                    candidate_cursor=cursor,
                    candidate_limit=5,
                )
            self.assertEqual(scope_mismatch.exception.code, "GOAL_CANDIDATE_CURSOR_SCOPE_MISMATCH")

    def test_exact_run_binding_resolves_and_conflicting_explicit_goal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = OrchestrationLedger(Path(directory))
            ledger.migrate_problem_lineage_schema()
            alpha = open_problem(ledger, "Alpha")
            beta = open_problem(ledger, "Beta")
            run_id, _wave_id = bind_run(ledger, alpha, suffix="alpha")
            identity = ledger.goal_pursuit_resolve_identity(run_id=run_id)
            self.assertEqual(identity["reason"], "EXACT_RUN_BINDING")
            self.assertEqual(identity["problem_id"], alpha["event"]["problem_id"])
            with self.assertRaises(GoalPursuitError) as conflict:
                ledger.goal_pursuit_resolve_identity(
                    problem_id=str(beta["event"]["problem_id"]),
                    problem_revision=1,
                    run_id=run_id,
                )
            self.assertEqual(conflict.exception.code, "GOAL_IDENTITY_CONFLICT")

    def test_explicit_unbound_run_is_not_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = OrchestrationLedger(Path(directory))
            ledger.migrate_problem_lineage_schema()
            open_problem(ledger, "Only")
            run_id = ledger.create_run(objective="unbound")
            with self.assertRaises(GoalPursuitError) as unbound:
                ledger.goal_pursuit_resolve_identity(run_id=run_id)
            self.assertEqual(unbound.exception.code, "GOAL_RUN_UNBOUND")
            with self.assertRaises(GoalPursuitError) as live_unbound:
                ledger.goal_pursuit_live_summary(run_id=run_id)
            self.assertEqual(live_unbound.exception.code, "GOAL_RUN_UNBOUND")


class GoalPursuitProjectionTests(unittest.TestCase):
    def test_exact_accepted_coverage_then_provisional_transition_changes_next_action(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = OrchestrationLedger(Path(directory))
            ledger.migrate_problem_lineage_schema()
            opened = open_problem(ledger, "Coverage")
            problem_id = str(opened["event"]["problem_id"])
            run_id, wave_id = bind_run(ledger, opened, suffix="coverage")
            proof_ids = []
            for index in range(1, 3):
                proof_ids.append(
                    ledger.record_proof(
                        run_id=run_id,
                        wave_id=wave_id,
                        stage_id=f"criterion-{index}",
                        stage_version="1",
                        input_fingerprint=f"input-{index}",
                        status="passed",
                    )
                )
            manifest = {
                "coverage-criterion-1": [proof_ids[0]],
                "coverage-criterion-2": [proof_ids[1]],
            }
            proof_fp = passed_proof_fingerprint(ledger.list_proofs(run_id, wave_id=wave_id))
            files = accepted_files(run_id, wave_id)
            outcome = ledger.problem_prepare_eocl_outcome_claim(
                run_id=run_id,
                wave_id=wave_id,
                git_head=hashlib.sha256(b"head").hexdigest(),
                worktree_fp=hashlib.sha256(b"worktree").hexdigest(),
                proof_fingerprint=proof_fp,
                accepted_files=files,
                durable_mutation=False,
                coverage_manifest=manifest,
                resolution_envelope=resolution_envelope(),
            )
            accepted = ledger.accept_checkpoint_atomic(
                run_id=run_id,
                wave_id=wave_id,
                git_head=hashlib.sha256(b"head").hexdigest(),
                proof_fingerprint=proof_fp,
                metadata={
                    "worktree_fp": hashlib.sha256(b"worktree").hexdigest(),
                    "accepted_files": files,
                    "problem_outcome_claim": outcome["claim"],
                    "problem_outcome_claim_sha256": outcome["claim_sha256"],
                },
            )
            projection = ledger.goal_pursuit_projection(
                problem_id=problem_id, problem_revision=1
            )
            self.assertEqual(projection["completion"]["criteria_proven"], 2)
            self.assertEqual(projection["completion"]["criteria_total"], 2)
            self.assertEqual(
                projection["resolution_status"],
                "ENGINEERING_COMPLETE_AWAITING_RECONCILIATION",
            )
            self.assertEqual(projection["next_action"], "RECONCILE_PROVISIONAL_RESOLUTION")
            self.assertTrue(projection["derived_projection_only"])
            self.assertEqual(
                projection["authority"],
                {
                    "mutation_authority_granted": False,
                    "acceptance_authority_granted": False,
                    "problem_revision_authority_granted": False,
                },
            )
            self.assertFalse(projection["timestamp_selection_used"])
            live = ledger.goal_pursuit_live_summary(run_id=run_id)
            self.assertEqual(live["kind"], "bounded_live_goal_pursuit_summary")
            self.assertEqual(live["identity"]["problem_id"], problem_id)
            self.assertEqual(live["identity"]["problem_revision"], 1)
            self.assertEqual(live["completion"]["status"], "observed")
            self.assertEqual(live["completion"]["criteria_proven"], 2)
            self.assertEqual(live["completion"]["criteria_total"], 2)
            self.assertEqual(
                live["resolution_status"],
                "ENGINEERING_COMPLETE_AWAITING_RECONCILIATION",
            )
            self.assertFalse(live["fact_window"]["truncated"])
            self.assertFalse(live["timestamp_selection_used"])
            checkpoint_id = str(accepted["checkpoint_id"])
            bridged = ledger.problem_record_provisional_from_eocl(
                run_id=run_id,
                wave_id=wave_id,
                checkpoint_id=checkpoint_id,
                now=NOW,
            )
            self.assertTrue(bridged["recorded"])
            provisional = ledger.goal_pursuit_projection(
                problem_id=problem_id, problem_revision=1
            )
            self.assertEqual(provisional["resolution_status"], "PROVISIONAL")
            self.assertEqual(provisional["next_action"], "OBTAIN_INDEPENDENT_OUTCOME")

    def test_passed_proof_without_exact_accepted_claim_does_not_satisfy_criterion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = OrchestrationLedger(Path(directory))
            ledger.migrate_problem_lineage_schema()
            opened = open_problem(ledger, "Weak")
            run_id, wave_id = bind_run(ledger, opened, suffix="weak")
            ledger.record_proof(
                run_id=run_id,
                wave_id=wave_id,
                stage_id="unbound-proof",
                stage_version="1",
                input_fingerprint="weak-input",
                status="passed",
            )
            projection = ledger.goal_pursuit_projection(
                problem_id=str(opened["event"]["problem_id"]), problem_revision=1
            )
            self.assertEqual(projection["completion"]["criteria_proven"], 0)
            self.assertEqual(projection["resolution_status"], "IN_PROGRESS")


class GoalPursuitSurfaceTests(unittest.TestCase):
    def test_task_control_schema_is_strict(self) -> None:
        schemas = input_schemas()
        self.assertIn("goal", schemas["task_control"]["properties"]["action"]["enum"])
        validate_arguments(
            "task_control",
            {
                "action": "goal",
                "goal_action": "get",
                "goal_event": {"problem_id": "problem-1", "problem_revision": 1},
            },
        )
        validate_arguments(
            "task_control",
            {
                "action": "goal",
                "goal_action": "resolve",
                "goal_event": {"candidate_limit": 25},
            },
        )
        with self.assertRaises(JsonRpcError):
            validate_arguments(
                "task_control",
                {
                    "action": "goal",
                    "goal_action": "get",
                    "goal_event": {"latest": True},
                },
            )

    def test_runtime_exposes_goal_under_smart_task_control_without_new_tool(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(directory))
            try:
                self.assertEqual(runtime.tool_contract["tool_count"], 8)
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                opened = open_problem(runtime.orchestration_ledger, "Runtime")
                result = runtime.task_control(
                    {
                        "action": "goal",
                        "goal_action": "get",
                        "goal_event": {
                            "problem_id": opened["event"]["problem_id"],
                            "problem_revision": 1,
                        },
                    }
                )
                self.assertEqual(result["goal_identity"]["status"], "EXACT")
                self.assertTrue(result["goal_pursuit"]["derived_projection_only"])
                self.assertFalse(result["authority_granted"])
            finally:
                runtime.close()

    def test_control_reports_ambiguity_instead_of_selecting_latest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Path(directory))
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                open_problem(runtime.orchestration_ledger, "First")
                open_problem(runtime.orchestration_ledger, "Second")
                with self.assertRaises(ToolFailure) as ambiguous:
                    runtime.task_control(
                        {"action": "goal", "goal_action": "get", "goal_event": {}}
                    )
                self.assertEqual(ambiguous.exception.code, "GOAL_IDENTITY_AMBIGUOUS")
                self.assertFalse(ambiguous.exception.details["timestamp_selection_used"])
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
