from __future__ import annotations

import tempfile
import time
import unittest
import json
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import JsonRpcError, ToolFailure
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.problem_lineage import PROBLEM_SCHEMA_VERSION, ProblemLineageError
from coding_tools_mcp.server import Runtime, validate_arguments
from coding_tools_mcp.tool_schema import input_schemas


def event_id(value: str) -> str:
    return value.replace("_", "-")


class ProblemLineageTests(unittest.TestCase):
    @staticmethod
    def open_event(*, identifier: str = "problem-open", task_id: str = "task-1") -> dict[str, object]:
        return {
            "operation": "open",
            "event_id": event_id(identifier),
            "task_id": task_id,
            "task_class": "feature",
            "engineering_floor": "REQUIRED",
            "relation_type": "OPEN",
            "link_status": "EXACT",
            "link_role": "PRIMARY",
            "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
            "evidence_level": "OBSERVED",
            "eligible_for_policy": True,
        }

    def test_v10_activation_is_forward_only_and_never_constructor_implicit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            self.assertEqual(ledger.problem_lineage_schema_version(), 9)
            migrated = ledger.migrate_problem_lineage_schema()
            self.assertTrue(migrated["migrated"])
            self.assertEqual(migrated["schema_version"], PROBLEM_SCHEMA_VERSION)
            replay = ledger.migrate_problem_lineage_schema()
            self.assertFalse(replay["migrated"])
            self.assertEqual(ledger.problem_lineage_schema_version(), PROBLEM_SCHEMA_VERSION)
            restarted = OrchestrationLedger(Path(temp))
            self.assertEqual(restarted.problem_lineage_schema_version(), PROBLEM_SCHEMA_VERSION)
            with self.assertRaises(ProblemLineageError):
                ledger.migrate_problem_lineage_schema(expected_schema_version=8)

    def test_typed_open_link_feedback_reopen_chain_and_idempotency(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            ledger.migrate_problem_lineage_schema()
            opened = ledger.problem_record_event(self.open_event(), now="2026-08-23T00:00:00Z")
            self.assertTrue(opened["recorded"])
            problem_id = opened["thread"]["thread"]["problem_id"]
            replay = ledger.problem_record_event(self.open_event(), now="2026-08-23T00:01:00Z")
            self.assertTrue(replay["idempotent"])
            self.assertEqual(replay["event"]["event_id"], "problem-open")

            run_id = ledger.create_run(objective="fixture engineering run", task_id="task-1")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            linked = ledger.problem_record_event({
                "operation": "link", "event_id": "problem-link", "problem_id": problem_id,
                "task_id": "task-1", "run_id": run_id, "wave_id": wave_id,
                "relation_type": "ENGINEERING_ATTEMPT_BOUND", "link_status": "EXACT", "link_role": "PRIMARY",
                "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED", "eligible_for_policy": True,
            }, now="2026-08-23T00:02:00Z")
            self.assertTrue(linked["recorded"])
            provisional = ledger.problem_record_event({
                "operation": "resolution", "event_id": "problem-provisional", "problem_id": problem_id,
                "task_id": "task-1", "run_id": run_id, "wave_id": wave_id,
                "relation_type": "PROVISIONAL_RESOLUTION", "link_status": "EXACT", "link_role": "SECONDARY",
                "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED", "eligible_for_policy": True,
                "state": "PROVISIONALLY_RESOLVED",
            }, now="2026-08-23T00:03:00Z")
            self.assertEqual(provisional["thread"]["thread"]["resolution_state"], "PROVISIONALLY_RESOLVED")
            confirmation = ledger.problem_record_event({
                "operation": "feedback", "event_id": "problem-confirm", "problem_id": problem_id,
                "task_id": "task-1", "run_id": run_id, "wave_id": wave_id,
                "relation_type": "USER_FEEDBACK", "link_status": "EXACT", "link_role": "SECONDARY",
                "feedback_intent": "CONFIRM_RESOLVED", "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
                "evidence_level": "OBSERVED", "eligible_for_policy": True, "reason_code": "user_confirmation",
            }, now="2026-08-23T00:04:00Z")
            self.assertEqual(confirmation["thread"]["thread"]["resolution_state"], "RESOLVED_CONFIRMED")
            # PRL feedback is evaluation evidence only: it must not accept an
            # EOCL run or mutate its execution state.
            self.assertEqual(ledger.get_run(run_id)["status"], "active")
            reopened = ledger.problem_record_event({
                "operation": "reopen", "event_id": "problem-reopen", "problem_id": problem_id,
                "task_id": "task-1", "relation_type": "REOPEN", "link_status": "EXACT", "link_role": "SECONDARY",
                "feedback_intent": "SAME_PROBLEM_STILL_FAILING", "causal_mechanism": "UNKNOWN",
                "economic_class": "UNKNOWN", "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
                "evidence_level": "OBSERVED", "eligible_for_policy": True, "reason_code": "explicit_same_problem_correction",
            }, now="2026-08-23T00:05:00Z")
            self.assertEqual(reopened["thread"]["thread"]["resolution_state"], "REOPENED")
            self.assertEqual(reopened["thread"]["thread"]["current_revision"], 2)
            self.assertTrue(ledger.problem_verify_chain(problem_id)["ok"])

    def test_ambiguous_unlinked_event_is_excluded_and_no_raw_payload_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            ledger.migrate_problem_lineage_schema()
            ambiguous = ledger.problem_record_event({
                "operation": "link", "event_id": "ambiguous-link", "task_id": "task-ambiguous",
                "relation_type": "LINK", "link_status": "AMBIGUOUS", "link_role": "SECONDARY",
                "provenance": "SHADOW_MODEL_INFERRED", "evidence_level": "INFERRED", "eligible_for_policy": False,
                "reason_code": "ambiguous_relation",
            }, now="2026-08-23T00:00:00Z")
            self.assertIsNone(ambiguous["thread"])
            self.assertFalse(ambiguous["event"]["eligible_for_policy"])
            with self.assertRaises(ProblemLineageError):
                ledger.problem_record_event({**self.open_event(identifier="payload-rejected"), "payload_json": {"prompt": "must not persist"}}, now="2026-08-23T00:01:00Z")
            with self.assertRaises(ProblemLineageError):
                ledger.problem_record_event({
                    "operation": "link", "event_id": "ambiguous-policy", "link_status": "AMBIGUOUS",
                    "link_role": "SECONDARY", "relation_type": "LINK", "eligible_for_policy": True,
                }, now="2026-08-23T00:02:00Z")

    def test_problem_feedback_without_engineering_run_is_content_free_and_not_counted_as_avoidable_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            ledger.migrate_problem_lineage_schema()
            opened = ledger.problem_record_event({
                **self.open_event(identifier="diagnosis-open", task_id="task-diagnosis"),
                "task_class": "diagnose", "engineering_floor": "NOT_APPLICABLE",
            }, now="2026-08-23T00:00:00Z")
            problem_id = opened["thread"]["thread"]["problem_id"]
            provisional = ledger.problem_record_event({
                "operation": "resolution", "event_id": "diagnosis-provisional", "problem_id": problem_id,
                "task_id": "task-diagnosis", "relation_type": "PROVISIONAL_RESOLUTION",
                "link_status": "EXACT", "link_role": "SECONDARY", "provenance": "DETERMINISTIC_EVIDENCE",
                "evidence_level": "OBSERVED", "eligible_for_policy": False, "state": "PROVISIONALLY_RESOLVED",
            }, now="2026-08-23T00:01:00Z")
            self.assertEqual(provisional["thread"]["thread"]["resolution_state"], "PROVISIONALLY_RESOLVED")
            confirmed = ledger.problem_record_event({
                "operation": "feedback", "event_id": "diagnosis-confirm", "problem_id": problem_id,
                "task_id": "task-diagnosis", "relation_type": "USER_FEEDBACK", "link_status": "EXACT",
                "link_role": "SECONDARY", "feedback_intent": "CONFIRM_RESOLVED",
                "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
                "eligible_for_policy": True, "reason_code": "user_confirmation",
            }, now="2026-08-23T00:02:00Z")
            self.assertEqual(confirmed["thread"]["thread"]["resolution_state"], "RESOLVED_CONFIRMED")
            stored = ledger.problem_get(problem_id)
            assert stored is not None
            self.assertTrue(all(not item["run_id"] and not item["wave_id"] for item in stored["events"]))

            growth = ledger.problem_record_event({
                **self.open_event(identifier="growth-open", task_id="task-growth"),
                "task_class": "diagnose", "engineering_floor": "NOT_APPLICABLE",
            }, now="2026-08-23T00:03:00Z")
            growth_problem_id = growth["thread"]["thread"]["problem_id"]
            classified = ledger.problem_record_event({
                "operation": "feedback", "event_id": "growth-feedback", "problem_id": growth_problem_id,
                "task_id": "task-growth", "relation_type": "USER_FEEDBACK", "link_status": "EXACT",
                "link_role": "SECONDARY", "feedback_intent": "ADD_CONSTRAINT_OR_REQUIREMENT",
                "causal_mechanism": "REQUIREMENT_EVOLUTION", "economic_class": "LEGITIMATE_REQUIREMENT_GROWTH",
                "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
                "eligible_for_policy": True,
            }, now="2026-08-23T00:04:00Z")
            self.assertEqual(classified["event"]["economic_class"], "LEGITIMATE_REQUIREMENT_GROWTH")
            self.assertEqual(classified["event"]["causal_mechanism"], "REQUIREMENT_EVOLUTION")

    def test_primary_run_conflict_and_event_replay_conflict_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            ledger.migrate_problem_lineage_schema()
            first = ledger.problem_record_event(self.open_event(identifier="first-open"), now="2026-08-23T00:00:00Z")
            second = ledger.problem_record_event(self.open_event(identifier="second-open"), now="2026-08-23T00:00:01Z")
            first_problem = first["thread"]["thread"]["problem_id"]
            second_problem = second["thread"]["thread"]["problem_id"]
            run_id = ledger.create_run(objective="single primary", task_id="task-1")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            base = {
                "operation": "link", "event_id": "first-primary", "problem_id": first_problem, "task_id": "task-1",
                "run_id": run_id, "wave_id": wave_id, "relation_type": "LINK", "link_status": "EXACT", "link_role": "PRIMARY",
                "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED", "eligible_for_policy": True,
            }
            ledger.problem_record_event(base, now="2026-08-23T00:01:00Z")
            with self.assertRaises(ProblemLineageError):
                ledger.problem_record_event({**base, "event_id": "duplicate-primary"}, now="2026-08-23T00:01:00Z")
            with self.assertRaises(ProblemLineageError):
                ledger.problem_record_event({**base, "event_id": "second-primary", "problem_id": second_problem}, now="2026-08-23T00:01:01Z")
            with self.assertRaises(ProblemLineageError):
                ledger.problem_record_event({**base, "economic_class": "AVOIDABLE_CORRECTION"}, now="2026-08-23T00:01:02Z")

    def test_task_control_problem_schema_keeps_eight_tools_and_requires_explicit_activation(self) -> None:
        schema = input_schemas()["task_control"]
        self.assertIn("problem", schema["properties"]["action"]["enum"])
        self.assertIn("problem_event", schema["properties"])
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            runtime = Runtime(Path(temp), permission_mode="safe")
            try:
                self.assertEqual(runtime.tool_contract["tool_count"], 8)
                with self.assertRaises(ToolFailure) as denied:
                    runtime.task_control({"action": "problem", "problem_event": self.open_event()})
                self.assertEqual(denied.exception.code, "PRL_SCHEMA_NOT_ACTIVATED")
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                opened = runtime.task_control({"action": "problem", "problem_event": self.open_event(identifier="runtime-open")})
                problem_id = opened["problem"]["thread"]["thread"]["problem_id"]
                got = runtime.task_control({"action": "problem", "problem_event": {"operation": "get", "problem_id": problem_id}})
                self.assertEqual(got["problem"]["thread"]["problem_id"], problem_id)
                with self.assertRaises(ToolFailure) as invalid:
                    runtime.task_control({"action": "problem", "problem_event": {**self.open_event(identifier="bad-runtime"), "payload_json": {}}})
                self.assertEqual(invalid.exception.code, "PRL_EVENT_INVALID")
                with self.assertRaises(JsonRpcError):
                    validate_arguments("task_control", {"action": "problem", "problem_event": {"operation": "open", "event_id": "schema-extra", "payload_json": {}}})
            finally:
                runtime.close()

    def test_host_observed_event_peeks_exact_identity_without_consuming_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(temp)
            runtime = Runtime(root, permission_mode="safe")
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                pending = root / ".coding-tools" / "evaluation" / "chatweb-host-turn-pending.json"
                pending.parent.mkdir(parents=True, exist_ok=True)
                pending.write_text(json.dumps({
                    "schema_version": 1, "turn_id": "turn-host-1", "trace_id": "trace-host-1", "staged_at_unix_ms": int(time.time() * 1000),
                }), encoding="utf-8")
                opened = runtime.task_control({"action": "problem", "problem_event": {
                    **self.open_event(identifier="host-open"),
                    "turn_id": "turn-host-1", "trace_id": "trace-host-1", "provenance": "HOST_OBSERVED",
                }})
                self.assertTrue(opened["problem"]["recorded"])
                self.assertTrue(pending.exists())
                with self.assertRaises(ToolFailure) as mismatch:
                    runtime.task_control({"action": "problem", "problem_event": {
                        **self.open_event(identifier="host-mismatch"),
                        "turn_id": "turn-other", "trace_id": "trace-host-1", "provenance": "HOST_OBSERVED",
                    }})
                self.assertEqual(mismatch.exception.code, "PRL_HOST_IDENTITY_MISMATCH")
            finally:
                runtime.close()

    def test_claimed_host_turn_creates_exact_engineering_attempt_and_derived_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(temp)
            runtime = Runtime(root, permission_mode="safe")
            runtime._orchestration_workspace_identity = lambda _path: {"branch": "test", "base_head": "head", "worktree_fp": "worktree"}
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                pending = root / ".coding-tools" / "evaluation" / "chatweb-host-turn-pending.json"
                pending.parent.mkdir(parents=True, exist_ok=True)
                pending.write_text(json.dumps({
                    "schema_version": 1, "turn_id": "turn-bind-1", "trace_id": "trace-bind-1", "staged_at_unix_ms": 1,
                }), encoding="utf-8")
                with patch("coding_tools_mcp.host_correlation.time.time", return_value=0.001):
                    opened = runtime.task_control({"action": "problem", "problem_event": {
                        **self.open_event(identifier="bind-open", task_id="task-bind"),
                        "turn_id": "turn-bind-1", "trace_id": "trace-bind-1", "provenance": "HOST_OBSERVED",
                    }})
                    problem_id = opened["problem"]["thread"]["thread"]["problem_id"]
                    ctx, _ = runtime._agent_orchestration_context(
                        {"workflow": "diagnose", "phase": "prepare", "execution_mode": "mcp_only"},
                        objective="bind the exact host turn",
                    )
                problem = runtime.orchestration_ledger.problem_get(problem_id)
                assert problem is not None
                binding = [item for item in problem["events"] if item["relation_type"] == "ENGINEERING_ATTEMPT_BOUND"]
                self.assertEqual(len(binding), 1)
                self.assertEqual(binding[0]["run_id"], ctx.run_id)
                self.assertEqual(binding[0]["wave_id"], ctx.wave_id)
                self.assertEqual(binding[0]["turn_id"], "turn-bind-1")
                self.assertEqual(binding[0]["trace_id"], "trace-bind-1")
                self.assertEqual(binding[0]["link_status"], "EXACT")
                self.assertEqual(binding[0]["link_role"], "PRIMARY")
                self.assertFalse(pending.exists())
                recorded = runtime.task_control({
                    "action": "handoff", "handoff_action": "record", "payload": {"next_action": "continue exact proof"},
                })
                capsule = recorded["capsule"]["payload"]["problem_lineage"]
                self.assertEqual(capsule["active_problem_id"], problem_id)
                self.assertEqual(capsule["problem_state"], "OPEN")
                self.assertNotIn("prompt", json.dumps(capsule))
            finally:
                runtime.close()

    def test_ambiguous_host_identity_records_missingness_without_merging_problem_threads(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(temp)
            runtime = Runtime(root, permission_mode="safe")
            runtime._orchestration_workspace_identity = lambda _path: {"branch": "test", "base_head": "head", "worktree_fp": "worktree"}
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                pending = root / ".coding-tools" / "evaluation" / "chatweb-host-turn-pending.json"
                pending.parent.mkdir(parents=True, exist_ok=True)
                pending.write_text(json.dumps({
                    "schema_version": 1, "turn_id": "turn-ambiguous-1", "trace_id": "trace-ambiguous-1", "staged_at_unix_ms": 1,
                }), encoding="utf-8")
                with patch("coding_tools_mcp.host_correlation.time.time", return_value=0.001):
                    for identifier in ("ambiguous-open-a", "ambiguous-open-b"):
                        runtime.task_control({"action": "problem", "problem_event": {
                            **self.open_event(identifier=identifier, task_id="task-ambiguous"),
                            "turn_id": "turn-ambiguous-1", "trace_id": "trace-ambiguous-1", "provenance": "HOST_OBSERVED",
                        }})
                    ctx, _ = runtime._agent_orchestration_context(
                        {"workflow": "diagnose", "phase": "prepare", "execution_mode": "mcp_only"},
                        objective="retain ambiguous host relation",
                    )
                with runtime.orchestration_ledger._connect() as connection:
                    row = connection.execute(
                        "SELECT problem_id,link_status,link_role,reason_code FROM problem_events WHERE run_id=?",
                        (ctx.run_id,),
                    ).fetchone()
                assert row is not None
                self.assertIsNone(row["problem_id"])
                self.assertEqual(row["link_status"], "AMBIGUOUS")
                self.assertEqual(row["link_role"], "SECONDARY")
                self.assertEqual(row["reason_code"], "ambiguous_relation")
            finally:
                runtime.close()

    def test_expired_pending_host_identity_is_not_accepted_for_problem_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(temp)
            runtime = Runtime(root, permission_mode="safe")
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                pending = root / ".coding-tools" / "evaluation" / "chatweb-host-turn-pending.json"
                pending.parent.mkdir(parents=True, exist_ok=True)
                pending.write_text(json.dumps({
                    "schema_version": 1, "turn_id": "turn-expired", "trace_id": "trace-expired", "staged_at_unix_ms": 1,
                }), encoding="utf-8")
                with self.assertRaises(ToolFailure) as unavailable:
                    runtime.task_control({"action": "problem", "problem_event": {
                        **self.open_event(identifier="expired-open"),
                        "turn_id": "turn-expired", "trace_id": "trace-expired", "provenance": "HOST_OBSERVED",
                    }})
                self.assertEqual(unavailable.exception.code, "PRL_HOST_IDENTITY_UNAVAILABLE")
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
