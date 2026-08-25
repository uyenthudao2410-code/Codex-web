from __future__ import annotations

import hashlib
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.problem_lineage import PROBLEM_SCHEMA_VERSION, ProblemLineageError, problem_event_hash_material
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.tool_schema import input_schemas, validate_arguments


NOW = "2026-08-25T00:00:00Z"


def capsule(summary: str = "Resolve the bounded defect", criterion: str = "The focused proof passes") -> dict[str, object]:
    return {
        "objective_summary": summary,
        "acceptance_criteria": [{"criterion_id": "criterion-1", "summary": criterion}],
        "protected_invariants": ["Preserve the existing public contract"],
        "constraints": ["Do not store raw user content"],
        "unresolved_conditions": [],
    }


def open_event(identifier: str = "open-1", **overrides: object) -> dict[str, object]:
    event: dict[str, object] = {
        "operation": "open", "event_id": identifier, "task_id": "task-1",
        "task_class": "bugfix", "engineering_floor": "REQUIRED",
        "contract_capsule": capsule(),
        "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
    }
    event.update(overrides)
    return event


class ProblemLineageTests(unittest.TestCase):
    def _ledger(self) -> tuple[tempfile.TemporaryDirectory[str], OrchestrationLedger]:
        temporary = tempfile.TemporaryDirectory()
        ledger = OrchestrationLedger(Path(temporary.name))
        ledger.migrate_problem_lineage_schema()
        self.assertEqual(ledger.problem_lineage_schema_version(), PROBLEM_SCHEMA_VERSION)
        return temporary, ledger

    def test_v11_authority_feedback_and_runtime_owned_eligibility(self) -> None:
        temporary, ledger = self._ledger()
        try:
            with self.assertRaises(ProblemLineageError):
                ledger.problem_record_event(open_event("shadow-open"), now=NOW, authority_context="RUNTIME_OBSERVATION")
            opened = ledger.problem_record_event(open_event(), now=NOW, authority_context="RUNTIME_EXPLICIT_USER")
            problem_id = str(opened["event"]["problem_id"])
            self.assertTrue(opened["event"]["eligible_for_policy"])
            self.assertEqual(opened["event"]["recorded_at"], NOW)
            with self.assertRaises(ProblemLineageError):
                ledger.problem_record_event({**open_event("caller-eligibility"), "eligible_for_policy": True}, now=NOW, authority_context="RUNTIME_EXPLICIT_USER")
            observation = ledger.problem_record_event({
                "operation": "observe_feedback", "event_id": "shadow-observation", "problem_id": problem_id,
                "problem_revision": 1, "task_id": "task-1", "feedback_intent": "CONFIRM_RESOLVED",
                "provenance": "SHADOW_MODEL_INFERRED", "evidence_level": "INFERRED",
            }, now=NOW, authority_context="RUNTIME_OBSERVATION")
            self.assertEqual(observation["event"]["state_before"], "OPEN")
            self.assertEqual(observation["event"]["state_after"], "OPEN")
            self.assertFalse(observation["event"]["eligible_for_policy"])
            self.assertEqual(ledger.problem_get(problem_id)["thread"]["resolution_state"], "OPEN")
            with self.assertRaises(ProblemLineageError):
                ledger.problem_record_event({
                    "operation": "confirm", "event_id": "bad-confirm", "problem_id": problem_id,
                    "problem_revision": 1, "feedback_intent": "CONFIRM_RESOLVED",
                    "provenance": "SHADOW_MODEL_INFERRED", "evidence_level": "INFERRED",
                }, now=NOW, authority_context="RUNTIME_OBSERVATION")
            with self.assertRaises(ProblemLineageError):
                ledger.problem_record_event({
                    "operation": "block", "event_id": "untyped-block", "problem_id": problem_id,
                    "problem_revision": 1, "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED",
                }, now=NOW, authority_context="RUNTIME_GUARD")
            with self.assertRaises(ProblemLineageError):
                ledger.problem_record_event({
                    "operation": "reopen", "event_id": "ambiguous-reopen", "link_status": "UNLINKED",
                    "feedback_intent": "SAME_PROBLEM_STILL_FAILING",
                    "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
                }, now=NOW, authority_context="RUNTIME_EXPLICIT_USER")
            with self.assertRaises(ProblemLineageError):
                ledger.problem_record_event(open_event("mismatched-relation", relation_type="BLOCK"), now=NOW, authority_context="RUNTIME_EXPLICIT_USER")
        finally:
            temporary.cleanup()

    def test_reopen_keeps_revision_and_revise_uses_compare_and_swap(self) -> None:
        temporary, ledger = self._ledger()
        try:
            opened = ledger.problem_record_event(open_event(), now=NOW, authority_context="RUNTIME_EXPLICIT_USER")
            problem_id = str(opened["event"]["problem_id"])
            fingerprint = str(opened["event"]["contract_fingerprint"])
            ledger.problem_record_event({
                "operation": "provisional_resolve", "event_id": "technical-pass", "problem_id": problem_id,
                "problem_revision": 1, "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED",
            }, now=NOW, authority_context="RUNTIME_EOCL")
            reopened = ledger.problem_record_event({
                "operation": "reopen", "event_id": "same-problem-reopen", "problem_id": problem_id,
                "problem_revision": 1, "feedback_intent": "SAME_PROBLEM_STILL_FAILING",
                "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
            }, now=NOW, authority_context="RUNTIME_EXPLICIT_USER")
            self.assertEqual(reopened["event"]["problem_revision"], 1)
            self.assertEqual(reopened["event"]["reason_code"], "explicit_same_problem_correction")
            self.assertEqual(reopened["thread"]["thread"]["current_revision"], 1)
            revised = ledger.problem_record_event({
                "operation": "revise", "event_id": "revision-2", "problem_id": problem_id,
                "expected_revision": 1, "expected_contract_fingerprint": fingerprint,
                "task_class": "bugfix", "engineering_floor": "REQUIRED", "contract_capsule": capsule("Resolve the revised bounded defect"),
                "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
            }, now=NOW, authority_context="RUNTIME_EXPLICIT_USER")
            self.assertEqual(revised["event"]["problem_revision"], 2)
            self.assertEqual(revised["event"]["reason_code"], "explicit_contract_revision")
            self.assertEqual(revised["thread"]["thread"]["current_revision"], 2)
            self.assertEqual(revised["thread"]["thread"]["resolution_state"], "REVISED")
            with self.assertRaises(ProblemLineageError):
                ledger.problem_record_event({
                    "operation": "revise", "event_id": "stale-revision", "problem_id": problem_id,
                    "expected_revision": 1, "expected_contract_fingerprint": fingerprint,
                    "task_class": "bugfix", "engineering_floor": "REQUIRED", "contract_capsule": capsule("Another revision"),
                    "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
                }, now=NOW, authority_context="RUNTIME_EXPLICIT_USER")
            self.assertTrue(ledger.problem_verify_chain(problem_id)["ok"])
        finally:
            temporary.cleanup()

    def test_c3_exact_manifest_checkpoint_bridge_is_idempotent(self) -> None:
        temporary, ledger = self._ledger()
        try:
            opened = ledger.problem_record_event(open_event(), now=NOW, authority_context="RUNTIME_EXPLICIT_USER")
            problem_id, fingerprint = str(opened["event"]["problem_id"]), str(opened["event"]["contract_fingerprint"])
            context = {"schema_version": 1, "work_origin": "problem", "resolution_claim": "full_problem", "problem_id": problem_id, "problem_revision": 1, "contract_fingerprint": fingerprint, "engineering_floor": "REQUIRED", "policy_eligible": False}
            run_id = ledger.create_run(objective="fixture", metadata={"problem_resolution": context})
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", metadata={"problem_resolution": context})
            ledger.problem_record_event({
                "operation": "link", "event_id": "bind-run", "problem_id": problem_id, "problem_revision": 1,
                "run_id": run_id, "wave_id": wave_id, "relation_type": "ENGINEERING_ATTEMPT_BOUND",
                "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED",
            }, now=NOW, authority_context="RUNTIME_BINDING")
            proof_id = ledger.record_proof(run_id=run_id, wave_id=wave_id, stage_id="focused", stage_version="1", input_fingerprint="proof-input", status="passed")
            manifest = {"criterion-1": [proof_id]}
            self.assertTrue(ledger.problem_record_coverage_manifest(run_id=run_id, wave_id=wave_id, manifest=manifest)["recorded"])
            checkpoint_id = ledger.record_checkpoint(run_id=run_id, wave_id=wave_id, git_head="head", proof_fingerprint="proofs", status="accepted")
            bridge = ledger.problem_record_provisional_from_eocl(run_id=run_id, wave_id=wave_id, checkpoint_id=checkpoint_id, now=NOW)
            self.assertTrue(bridge["recorded"])
            replay = ledger.problem_record_provisional_from_eocl(run_id=run_id, wave_id=wave_id, checkpoint_id=checkpoint_id, now=NOW)
            self.assertFalse(replay["recorded"])
            thread = ledger.problem_get(problem_id)
            assert thread is not None
            self.assertEqual(thread["thread"]["resolution_state"], "PROVISIONALLY_RESOLVED")
            self.assertTrue(bridge["event"]["eligible_for_policy"])
        finally:
            temporary.cleanup()

    def test_v10_migration_preserves_hashes_as_legacy_and_ineligible(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            legacy = {
                "event_id": "legacy-event", "problem_id": "legacy-problem", "task_id": "task", "turn_id": "", "trace_id": "",
                "run_id": "", "wave_id": "", "capsule_id": "", "conversation_epoch": 0, "relation_type": "OPEN",
                "link_status": "EXACT", "link_role": "PRIMARY", "feedback_intent": "UNKNOWN", "causal_mechanism": "UNKNOWN",
                "economic_class": "UNKNOWN", "provenance": "HOST_OBSERVED", "evidence_level": "OBSERVED", "eligible_for_policy": True,
                "reason_code": "none", "criteria_count": 0, "criteria_fingerprint": "", "event_time": NOW,
            }
            old_hash = hashlib.sha256(json.dumps(problem_event_hash_material(legacy, state_before="", state_after="OPEN", prev_hash=""), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            request_hash = hashlib.sha256(b"legacy").hexdigest()
            with ledger._lock, ledger._connect() as connection:
                connection.executescript("""
                    CREATE TABLE problem_threads (problem_id TEXT PRIMARY KEY,current_revision INTEGER NOT NULL,resolution_state TEXT NOT NULL,task_class TEXT NOT NULL,engineering_floor TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,closed_at TEXT,latest_problem_event_seq INTEGER NOT NULL DEFAULT 0,latest_problem_event_hash TEXT NOT NULL DEFAULT '');
                    CREATE TABLE problem_events (seq INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT NOT NULL UNIQUE,problem_id TEXT,task_id TEXT NOT NULL DEFAULT '',turn_id TEXT NOT NULL DEFAULT '',trace_id TEXT NOT NULL DEFAULT '',run_id TEXT NOT NULL DEFAULT '',wave_id TEXT NOT NULL DEFAULT '',capsule_id TEXT NOT NULL DEFAULT '',conversation_epoch INTEGER NOT NULL DEFAULT 0,relation_type TEXT NOT NULL,link_status TEXT NOT NULL,link_role TEXT NOT NULL,feedback_intent TEXT NOT NULL,causal_mechanism TEXT NOT NULL,economic_class TEXT NOT NULL,provenance TEXT NOT NULL,evidence_level TEXT NOT NULL,eligible_for_policy INTEGER NOT NULL DEFAULT 0,state_before TEXT NOT NULL DEFAULT '',state_after TEXT NOT NULL DEFAULT '',reason_code TEXT NOT NULL DEFAULT 'none',criteria_count INTEGER NOT NULL DEFAULT 0,criteria_fingerprint TEXT NOT NULL DEFAULT '',request_hash TEXT NOT NULL,event_time TEXT NOT NULL,prev_hash TEXT NOT NULL DEFAULT '',event_hash TEXT NOT NULL);
                    PRAGMA user_version=10;
                """)
                connection.execute("INSERT INTO problem_threads VALUES(?,?,?,?,?,?,?,?,?,?)", ("legacy-problem", 1, "OPEN", "unknown", "UNKNOWN", NOW, NOW, None, 1, old_hash))
                connection.execute("""INSERT INTO problem_events(seq,event_id,problem_id,task_id,turn_id,trace_id,run_id,wave_id,capsule_id,conversation_epoch,relation_type,link_status,link_role,feedback_intent,causal_mechanism,economic_class,provenance,evidence_level,eligible_for_policy,state_before,state_after,reason_code,criteria_count,criteria_fingerprint,request_hash,event_time,prev_hash,event_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (1, legacy["event_id"], legacy["problem_id"], legacy["task_id"], "", "", "", "", "", 0, "OPEN", "EXACT", "PRIMARY", "UNKNOWN", "UNKNOWN", "UNKNOWN", "HOST_OBSERVED", "OBSERVED", 1, "", "OPEN", "none", 0, "", request_hash, NOW, "", old_hash))
            self.assertTrue(ledger.migrate_problem_lineage_schema(expected_schema_version=10)["migrated"])
            problem = ledger.problem_get("legacy-problem")
            assert problem is not None
            self.assertTrue(problem["legacy_or_missing_contract"])
            self.assertEqual(problem["events"][0]["event_schema_version"], 1)
            self.assertFalse(problem["events"][0]["eligible_for_policy"])
            self.assertTrue(ledger.problem_verify_chain("legacy-problem")["ok"])

    def test_runtime_autofills_host_identity_and_pins_declared_revision_before_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(temp)
            runtime = Runtime(root, permission_mode="safe")
            runtime._orchestration_workspace_identity = lambda _path: {"branch": "test", "base_head": "head", "worktree_fp": "worktree"}
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                opened = runtime.task_control({"action": "problem", "problem_event": open_event("runtime-open")})
                event = opened["problem"]["event"]
                problem_id, fingerprint = str(event["problem_id"]), str(event["contract_fingerprint"])
                pending = root / ".coding-tools" / "evaluation" / "chatweb-host-turn-pending.json"
                pending.parent.mkdir(parents=True, exist_ok=True)
                pending.write_text(json.dumps({"schema_version": 1, "turn_id": "turn-1", "trace_id": "trace-1", "staged_at_unix_ms": int(time.time() * 1000)}), encoding="utf-8")
                observed = runtime.task_control({"action": "problem", "problem_event": {"operation": "observe_feedback", "event_id": "host-observed", "problem_id": problem_id, "problem_revision": 1, "provenance": "HOST_OBSERVED", "evidence_level": "OBSERVED"}})
                self.assertEqual(observed["problem"]["event"]["turn_id"], "turn-1")
                ctx, _ = runtime._agent_orchestration_context({"workflow": "bugfix", "phase": "prepare", "execution_mode": "mcp_only", "problem_context": {"work_origin": "problem", "problem_id": problem_id, "problem_revision": 1, "contract_fingerprint": fingerprint, "resolution_claim": "none"}}, objective="pin revision before run")
                run = runtime.orchestration_ledger.get_run(ctx.run_id)
                assert run is not None
                self.assertEqual(run["metadata"]["problem_resolution"]["problem_revision"], 1)
                handoff = runtime.orchestration_ledger.problem_handoff_for_run(ctx.run_id)
                assert handoff is not None
                self.assertEqual(handoff["problem_revision"], 1)
            finally:
                runtime.close()

    def test_task_acceptance_bridges_only_a_covered_exact_full_problem_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                opened = runtime.task_control({"action": "problem", "problem_event": open_event("runtime-c3-open")})
                event = opened["problem"]["event"]
                problem_id = str(event["problem_id"])
                fingerprint = str(event["contract_fingerprint"])
                workflow = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "execute",
                    "execution_mode": "mcp_only",
                    "objective": "Set the bounded fixture value",
                    "evaluation": {"provenance": "benchmark"},
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                    "verification": "none",
                    "include_diff": False,
                    "problem_context": {
                        "work_origin": "problem",
                        "problem_id": problem_id,
                        "problem_revision": 1,
                        "contract_fingerprint": fingerprint,
                        "resolution_claim": "full_problem",
                    },
                })
                run_id = str(workflow["orchestration"]["run_id"])
                wave_id = str(workflow["orchestration"]["wave_id"])
                proof_id = runtime.orchestration_ledger.record_proof(
                    run_id=run_id,
                    wave_id=wave_id,
                    stage_id="focused",
                    stage_version="1",
                    input_fingerprint="runtime-c3-proof",
                    status="passed",
                )
                with self.assertRaises(ToolFailure) as missing_manifest:
                    runtime.task_control({"action": "accept", "run_id": run_id, "reason": "manifest is intentionally absent"})
                self.assertEqual(missing_manifest.exception.code, "PRL_COVERAGE_MANIFEST_REQUIRED")
                with self.assertRaises(ToolFailure) as invalid_manifest:
                    runtime.task_control({
                        "action": "accept", "run_id": run_id,
                        "reason": "manifest has no exact passed proof",
                        "problem_coverage_manifest": {"criterion-1": ["not-a-proof"]},
                    })
                self.assertEqual(invalid_manifest.exception.code, "PRL_COVERAGE_MANIFEST_INVALID")

                accepted = runtime.task_control({
                    "action": "accept",
                    "run_id": run_id,
                    "reason": "exact full-problem claim has passed proof coverage",
                    "problem_coverage_manifest": {"criterion-1": [proof_id]},
                })
                self.assertTrue(accepted["accepted"])
                self.assertTrue(accepted["problem_outcome_bridge"]["recorded"])
                self.assertEqual(runtime.orchestration_ledger.problem_get(problem_id)["thread"]["resolution_state"], "PROVISIONALLY_RESOLVED")

                confirmed = runtime.task_control({"action": "problem", "problem_event": {
                    "operation": "confirm", "event_id": "runtime-c3-confirm", "problem_id": problem_id,
                    "problem_revision": 1, "feedback_intent": "CONFIRM_RESOLVED",
                    "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
                }})
                self.assertEqual(confirmed["problem"]["event"]["reason_code"], "user_confirmation")
                reopened = runtime.task_control({"action": "problem", "problem_event": {
                    "operation": "reopen", "event_id": "runtime-c3-reopen", "problem_id": problem_id,
                    "problem_revision": 1, "feedback_intent": "SAME_PROBLEM_STILL_FAILING",
                    "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
                }})
                self.assertEqual(reopened["problem"]["event"]["problem_revision"], 1)
                self.assertEqual(reopened["problem"]["event"]["reason_code"], "explicit_same_problem_correction")
                self.assertEqual(reopened["problem"]["thread"]["thread"]["current_revision"], 1)
            finally:
                runtime.close()

    def test_schema_inactive_acceptance_remains_available_without_problem_closure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                workflow = runtime.agent_workflow({
                    "workflow": "bugfix", "phase": "execute", "execution_mode": "mcp_only",
                    "objective": "Accept without an activated PRL schema",
                    "evaluation": {"provenance": "benchmark"},
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                    "verification": "none", "include_diff": False,
                })
                accepted = runtime.task_control({
                    "action": "accept", "run_id": workflow["orchestration"]["run_id"],
                    "reason": "ordinary EOCL acceptance remains available",
                })
                self.assertTrue(accepted["accepted"])
                self.assertEqual(accepted["problem_outcome_bridge"], {"recorded": False, "reason": "schema_inactive"})
            finally:
                runtime.close()

    def test_non_full_problem_origins_accept_without_a_provisional_closure(self) -> None:
        for origin in ("unknown", "non_problem", "problem"):
            with self.subTest(origin=origin), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
                runtime = Runtime(root, permission_mode="dangerous")
                try:
                    runtime.orchestration_ledger.migrate_problem_lineage_schema()
                    request: dict[str, object] = {
                        "workflow": "bugfix", "phase": "execute", "execution_mode": "mcp_only",
                        "objective": f"Accept a {origin} attempt without full closure",
                        "evaluation": {"provenance": "benchmark"},
                        "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                        "verification": "none", "include_diff": False,
                    }
                    if origin == "non_problem":
                        request["problem_context"] = {"work_origin": "non_problem"}
                    elif origin == "problem":
                        opened = runtime.task_control({"action": "problem", "problem_event": open_event(f"{origin}-none-open")})
                        event = opened["problem"]["event"]
                        request["problem_context"] = {
                            "work_origin": "problem", "problem_id": str(event["problem_id"]),
                            "problem_revision": 1, "contract_fingerprint": str(event["contract_fingerprint"]),
                            "resolution_claim": "none",
                        }
                    workflow = runtime.agent_workflow(request)
                    accepted = runtime.task_control({
                        "action": "accept", "run_id": workflow["orchestration"]["run_id"],
                        "reason": "this is not a full-problem resolution claim",
                    })
                    self.assertTrue(accepted["accepted"])
                    self.assertEqual(
                        accepted["problem_outcome_bridge"],
                        {"recorded": False, "reason": "not_exact_full_problem_claim"},
                    )
                finally:
                    runtime.close()

    def test_public_schema_has_no_caller_state_or_policy_grant(self) -> None:
        schema = input_schemas()["task_control"]
        event_schema = schema["properties"]["problem_event"]
        self.assertEqual(schema["properties"]["action"]["enum"].count("problem"), 1)
        self.assertNotIn("eligible_for_policy", event_schema["properties"])
        self.assertNotIn("state", event_schema["properties"])
        with self.assertRaises(Exception):
            validate_arguments("task_control", {"action": "problem", "problem_event": {"operation": "open", "event_id": "bad", "eligible_for_policy": True}})


if __name__ == "__main__":
    unittest.main()
