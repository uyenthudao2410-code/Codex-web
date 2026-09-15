from __future__ import annotations

import hashlib
import json
import tempfile
import time
import unittest
import base64
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.problem_lineage import (
    PROBLEM_EVENT_SCHEMA_CURRENT,
    PROBLEM_HANDOFF_CONTRACT_EMBED_MAX_BYTES,
    PROBLEM_SCHEMA_VERSION,
    ProblemLineageError,
    problem_event_hash_material,
    problem_outcome_receipt_id,
)
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


def resolution_envelope() -> dict[str, object]:
    return {
        "schema_version": 1,
        "direct_outcomes": [{"outcome_id": "outcome-1", "summary": "The bounded user outcome is observable"}],
        "relevant_invariants": ["Preserve the existing public contract"],
        "truth_domains": ["source", "runtime"],
        "adjacent_risks": [],
        "excluded_scope": ["Unrelated modules"],
        "required_evidence": [{"evidence_id": "evidence-1", "kind": "focused_proof", "provenance": "exact accepted wave", "status": "observed"}],
        "closure_falsification_probe": {"probe_id": "probe-1", "method": "Run the focused closure check", "expected_failure_signal": "The bounded outcome remains contradicted", "executed": True, "result": "passed"},
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


def public_event(event: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in event.items() if key not in {"provenance", "evidence_level"}}


def attach_chatweb(runtime: Runtime, context: str = "prl-test") -> None:
    runtime.request_context.hub_client = {
        "client_id": "chatweb",
        "client_type": "chatweb",
        "role": "controller",
        "session_instance": "prl-session",
        "execution_context_id": context,
        "capabilities": {},
    }
    runtime._touch_hub_client(runtime.request_context.hub_client)


def stage_host_turn(
    root: Path,
    identifier: str,
    *,
    product_session_receipt_id: str = "",
    prior_product_session_receipt_id: str = "",
    product_session_transition: str = "",
) -> Path:
    pending = root / ".coding-tools" / "evaluation" / "chatweb-host-turn-pending.json"
    pending.parent.mkdir(parents=True, exist_ok=True)
    pending.write_text(json.dumps({
        "schema_version": 1,
        "turn_id": f"turn-{identifier}",
        "trace_id": f"trace-{identifier}",
        **(
            {"product_session_receipt_id": product_session_receipt_id}
            if product_session_receipt_id
            else {}
        ),
        **(
            {"prior_product_session_receipt_id": prior_product_session_receipt_id}
            if prior_product_session_receipt_id
            else {}
        ),
        **(
            {"product_session_transition": product_session_transition}
            if product_session_transition
            else {}
        ),
        "staged_at_unix_ms": int(time.time() * 1000),
    }), encoding="utf-8")
    return pending


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
            self.assertEqual(revised["event"]["relation_type"], "REVISION")
            self.assertEqual(revised["thread"]["thread"]["resolution_state"], "OPEN")
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

    def test_receipt_tamper_breaks_the_problem_event_hash_chain(self) -> None:
        temporary, ledger = self._ledger()
        try:
            opened = ledger.problem_record_event(open_event("receipt-chain-open"), now=NOW, authority_context="RUNTIME_EXPLICIT_USER")
            problem_id = str(opened["event"]["problem_id"])
            ledger.problem_record_event({
                "operation": "provisional_resolve",
                "event_id": "receipt-chain-provisional",
                "problem_id": problem_id,
                "problem_revision": 1,
                "provenance": "DETERMINISTIC_EVIDENCE",
                "evidence_level": "OBSERVED",
            }, now=NOW, authority_context="RUNTIME_EOCL")
            receipt_type = "CHATWEB_EXPLICIT_USER_OUTCOME_V1"
            with self.assertRaisesRegex(ProblemLineageError, "exact host turn and trace"):
                ledger.problem_record_event({
                    "operation": "confirm",
                    "event_id": "receipt-chain-hostless",
                    "problem_id": problem_id,
                    "problem_revision": 1,
                    "feedback_intent": "CONFIRM_RESOLVED",
                    "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
                    "evidence_level": "OBSERVED",
                    "outcome_receipt_type": receipt_type,
                    "outcome_receipt_id": problem_outcome_receipt_id(
                        receipt_type=receipt_type,
                        event_id="receipt-chain-hostless",
                        problem_id=problem_id,
                        problem_revision=1,
                        turn_id="",
                        trace_id="",
                    ),
                }, now=NOW, authority_context="RUNTIME_OUTCOME_RECEIPT")
            with self.assertRaisesRegex(ProblemLineageError, "does not match the exact problem revision and host turn binding"):
                ledger.problem_record_event({
                    "operation": "confirm",
                    "event_id": "receipt-chain-mismatched",
                    "problem_id": problem_id,
                    "problem_revision": 1,
                    "turn_id": "turn-receipt-chain",
                    "trace_id": "trace-receipt-chain",
                    "feedback_intent": "CONFIRM_RESOLVED",
                    "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
                    "evidence_level": "OBSERVED",
                    "outcome_receipt_type": receipt_type,
                    "outcome_receipt_id": "0" * 64,
                }, now=NOW, authority_context="RUNTIME_OUTCOME_RECEIPT")
            receipt_id = problem_outcome_receipt_id(
                receipt_type=receipt_type,
                event_id="receipt-chain-confirm",
                problem_id=problem_id,
                problem_revision=1,
                turn_id="turn-receipt-chain",
                trace_id="trace-receipt-chain",
            )
            confirmed = ledger.problem_record_event({
                "operation": "confirm",
                "event_id": "receipt-chain-confirm",
                "problem_id": problem_id,
                "problem_revision": 1,
                "turn_id": "turn-receipt-chain",
                "trace_id": "trace-receipt-chain",
                "feedback_intent": "CONFIRM_RESOLVED",
                "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
                "evidence_level": "OBSERVED",
                "outcome_receipt_type": receipt_type,
                "outcome_receipt_id": receipt_id,
            }, now=NOW, authority_context="RUNTIME_OUTCOME_RECEIPT")
            self.assertTrue(ledger.problem_verify_chain(problem_id)["ok"])
            self.assertEqual(confirmed["event"]["outcome_receipt_id"], receipt_id)
            with ledger._lock, ledger._connect() as connection:
                connection.execute(
                    "UPDATE problem_events SET outcome_receipt_id=? WHERE event_id=?",
                    ("0" * 64, "receipt-chain-confirm"),
                )
            verification = ledger.problem_verify_chain(problem_id)
            self.assertFalse(verification["ok"])
            self.assertEqual(verification["reason"], "event_hash_mismatch")
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
            proof_fingerprint = hashlib.sha256(f"{proof_id}:proof-input".encode()).hexdigest()
            files = accepted_files(run_id, wave_id)
            outcome = ledger.problem_prepare_eocl_outcome_claim(
                run_id=run_id, wave_id=wave_id, git_head="head", worktree_fp="worktree",
                proof_fingerprint=proof_fingerprint, accepted_files=files, durable_mutation=False,
                coverage_manifest=manifest, resolution_envelope=resolution_envelope(),
            )
            checkpoint = ledger.accept_checkpoint_atomic(
                run_id=run_id, wave_id=wave_id, git_head="head", proof_fingerprint=proof_fingerprint,
                metadata={"worktree_fp": "worktree", "accepted_files": files, "problem_outcome_claim": outcome["claim"], "problem_outcome_claim_sha256": outcome["claim_sha256"]},
            )
            checkpoint_id = str(checkpoint["checkpoint_id"])
            bridge = ledger.problem_record_provisional_from_eocl(run_id=run_id, wave_id=wave_id, checkpoint_id=checkpoint_id, now=NOW)
            self.assertTrue(bridge["recorded"])
            replay = ledger.problem_record_provisional_from_eocl(run_id=run_id, wave_id=wave_id, checkpoint_id=checkpoint_id, now=NOW)
            self.assertFalse(replay["recorded"])
            self.assertTrue(replay["idempotent"])
            thread = ledger.problem_get(problem_id)
            assert thread is not None
            self.assertEqual(thread["thread"]["resolution_state"], "PROVISIONALLY_RESOLVED")
            self.assertTrue(bridge["event"]["eligible_for_policy"])
            terminal = next(
                item for item in ledger.list_events(run_id)
                if item["event_type"] == "state_transition" and item["state_after"] == "CHECKPOINTED"
            )
            self.assertEqual(bridge["event"]["occurred_at"], terminal["event_time"])
            self.assertEqual(bridge["event"]["occurred_at_source"], "RUNTIME")
            self.assertEqual(bridge["event"]["clock_authority"], "RUNTIME_OWNED")
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
                attach_chatweb(runtime)
                stage_host_turn(root, "open")
                opened = runtime.task_control({"action": "problem", "problem_event": public_event(open_event("runtime-open"))})
                event = opened["problem"]["event"]
                problem_id, fingerprint = str(event["problem_id"]), str(event["contract_fingerprint"])
                stage_host_turn(root, "observed")
                observed = runtime.task_control({"action": "problem", "problem_event": {"operation": "observe_feedback", "event_id": "host-observed", "problem_id": problem_id, "problem_revision": 1}})
                self.assertEqual(observed["problem"]["event"]["turn_id"], "turn-observed")
                self.assertEqual(observed["receipt_id"], observed["problem"]["event"]["event_hash"])
                ctx, _ = runtime._agent_orchestration_context({"workflow": "bugfix", "phase": "prepare", "execution_mode": "mcp_only", "problem_context": {"work_origin": "problem", "problem_id": problem_id, "problem_revision": 1, "contract_fingerprint": fingerprint, "resolution_claim": "none"}}, objective="pin revision before run")
                run = runtime.orchestration_ledger.get_run(ctx.run_id)
                assert run is not None
                self.assertEqual(run["metadata"]["problem_resolution"]["problem_revision"], 1)
                handoff = runtime.orchestration_ledger.problem_handoff_for_run(ctx.run_id)
                assert handoff is not None
                self.assertEqual(handoff["schema_version"], 1)
                self.assertEqual(handoff["kind"], "derived_resolution_capsule")
                self.assertEqual(handoff["run_id"], ctx.run_id)
                self.assertEqual(handoff["problem_revision"], 1)
                self.assertEqual(handoff["contract_capsule"], capsule())
                self.assertTrue(handoff["contract_capsule_included"])
                self.assertEqual(handoff["criteria_count"], 1)
                self.assertEqual(len(handoff["criteria_fingerprint"]), 64)
                self.assertGreaterEqual(handoff["event_count"], 3)
                self.assertEqual(handoff["latest_event"]["relation_type"], "ENGINEERING_ATTEMPT_BOUND")
                self.assertFalse(handoff["same_revision_reopened"])
                self.assertFalse(handoff["outcome_receipt_observed"])
                self.assertFalse(handoff["fresh_context"]["transcript_required"])
                self.assertFalse(handoff["fresh_context"]["raw_transcript_included"])
                self.assertFalse(handoff["fresh_context"]["raw_source_included"])
                self.assertFalse(handoff["fresh_context"]["private_reasoning_included"])
                self.assertFalse(handoff["fresh_context"]["mutation_authority_granted"])
                self.assertFalse(handoff["fresh_context"]["acceptance_authority_granted"])
                self.assertFalse(handoff["fresh_context"]["exact_revision_refresh_required"])
            finally:
                runtime.close()

    def test_runtime_derives_attested_transport_identity_without_electron_pending_host_turn(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = Runtime(root, permission_mode="safe")
            pending = root / ".coding-tools" / "evaluation" / "chatweb-host-turn-pending.json"
            trace_id = "a" * 32
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                attach_chatweb(runtime, "attested-transport")
                self.assertFalse(pending.exists())

                with self.assertRaises(ToolFailure) as unavailable:
                    runtime.task_control({
                        "action": "problem",
                        "problem_event": public_event(open_event("unattested-transport-open")),
                    })
                self.assertEqual(unavailable.exception.code, "PRL_HOST_IDENTITY_UNAVAILABLE")
                self.assertFalse(pending.exists())

                runtime.request_context.hub_client.update({
                    "identity_source": "attested_transport",
                    "attestation_verified": True,
                })
                runtime.request_context.trace_context = {"trace_id": trace_id}
                with self.assertRaises(ToolFailure) as mismatch:
                    runtime.task_control({
                        "action": "problem",
                        "problem_event": public_event(open_event(
                            "attested-transport-mismatch",
                            turn_id="caller-turn",
                            trace_id="caller-trace",
                        )),
                    })
                self.assertEqual(mismatch.exception.code, "PRL_HOST_IDENTITY_MISMATCH")
                self.assertFalse(pending.exists())

                opened = runtime.task_control({
                    "action": "problem",
                    "problem_event": public_event(open_event("attested-transport-open")),
                })
                event = opened["problem"]["event"]
                self.assertEqual(event["problem_revision"], 1)
                self.assertEqual(event["turn_id"], f"chatweb-trace:{trace_id}")
                self.assertEqual(event["trace_id"], trace_id)
                self.assertEqual(event["provenance"], "CONTROLLER_REPORTED_EXPLICIT_USER")
                self.assertFalse(pending.exists())
            finally:
                runtime.close()

    def test_problem_run_records_host_product_session_and_continuity_core_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = Runtime(root, permission_mode="safe")
            workspace_id = "workspace-product-session"
            runtime._orchestration_workspace_identity = lambda _path: {
                "branch": "test",
                "base_head": "a" * 40,
                "worktree_fp": "b" * 64,
                "source_fingerprint": "c" * 64,
                "workspace_identity": {"workspace_id": workspace_id},
            }
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                attach_chatweb(runtime, "product-session")
                stage_host_turn(root, "product-open")
                opened = runtime.task_control(
                    {
                        "action": "problem",
                        "problem_event": public_event(open_event("product-open")),
                    }
                )
                event = opened["problem"]["event"]
                problem_id = str(event["problem_id"])
                fingerprint = str(event["contract_fingerprint"])
                session_receipt = "chatweb-product-session:" + "d" * 64
                stage_host_turn(
                    root,
                    "product-run",
                    product_session_receipt_id=session_receipt,
                    product_session_transition="observed",
                )
                ctx, _ = runtime._agent_orchestration_context(
                    {
                        "workflow": "bugfix",
                        "phase": "prepare",
                        "execution_mode": "mcp_only",
                        "problem_context": {
                            "work_origin": "problem",
                            "problem_id": problem_id,
                            "problem_revision": 1,
                            "contract_fingerprint": fingerprint,
                            "resolution_claim": "none",
                        },
                    },
                    objective="record exact product session",
                )
                session_event = next(
                    item
                    for item in runtime.orchestration_ledger.list_events(ctx.run_id)
                    if item["event_type"] == "cross_session_chatweb_session_started"
                )
                self.assertEqual(session_event["payload"]["session_role"], "A")
                self.assertEqual(
                    session_event["payload"]["product_session_receipt_id"],
                    session_receipt,
                )
                self.assertNotIn("conversation_id", session_event["payload"])

                checkpoint = runtime.task_control(
                    {
                        "action": "continuity",
                        "continuity_action": "checkpoint",
                        "continuity_event": {
                            "problem_id": problem_id,
                            "problem_revision": 1,
                            "material_event_kind": "PROBLEM_OPENED",
                            "material_event_id": str(event["event_id"]),
                        },
                    }
                )
                core_event = next(
                    item
                    for item in runtime.orchestration_ledger.list_events(ctx.run_id)
                    if item["event_type"] == "continuity_core_recorded"
                )
                self.assertEqual(core_event["payload"]["workspace_id"], workspace_id)
                self.assertEqual(
                    core_event["payload"]["continuity_core_fingerprint"],
                    checkpoint["continuity_core"]["continuity_core_fingerprint"],
                )
            finally:
                runtime.close()

    def test_derived_resolution_capsule_reports_reopen_receipt_and_oversize_refresh(self) -> None:
        temporary, ledger = self._ledger()
        try:
            opened = ledger.problem_record_event(
                open_event("resolution-capsule-open"),
                now=NOW,
                authority_context="RUNTIME_EXPLICIT_USER",
            )
            problem_id = str(opened["event"]["problem_id"])
            ledger.problem_record_event({
                "operation": "link", "event_id": "resolution-capsule-link",
                "problem_id": problem_id, "problem_revision": 1,
                "run_id": "run-resolution-capsule", "link_role": "PRIMARY",
                "relation_type": "ENGINEERING_ATTEMPT_BOUND",
                "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED",
            }, now=NOW, authority_context="RUNTIME_BINDING")
            ledger.problem_record_event({
                "operation": "provisional_resolve", "event_id": "resolution-capsule-provisional",
                "problem_id": problem_id, "problem_revision": 1,
                "run_id": "run-resolution-capsule",
                "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED",
            }, now=NOW, authority_context="RUNTIME_EOCL")
            receipt_id = problem_outcome_receipt_id(
                receipt_type="CHATWEB_EXPLICIT_USER_OUTCOME_V1",
                event_id="resolution-capsule-confirm",
                problem_id=problem_id,
                problem_revision=1,
                turn_id="turn-resolution-capsule",
                trace_id="trace-resolution-capsule",
            )
            ledger.problem_record_event({
                "operation": "confirm", "event_id": "resolution-capsule-confirm",
                "problem_id": problem_id, "problem_revision": 1,
                "turn_id": "turn-resolution-capsule", "trace_id": "trace-resolution-capsule",
                "feedback_intent": "CONFIRM_RESOLVED",
                "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
                "outcome_receipt_type": "CHATWEB_EXPLICIT_USER_OUTCOME_V1",
                "outcome_receipt_id": receipt_id,
            }, now=NOW, authority_context="RUNTIME_OUTCOME_RECEIPT")
            ledger.problem_record_event({
                "operation": "reopen", "event_id": "resolution-capsule-reopen",
                "problem_id": problem_id, "problem_revision": 1,
                "feedback_intent": "SAME_PROBLEM_STILL_FAILING",
                "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER", "evidence_level": "OBSERVED",
            }, now=NOW, authority_context="RUNTIME_EXPLICIT_USER")

            handoff = ledger.problem_handoff_for_run("run-resolution-capsule")
            assert handoff is not None
            self.assertEqual(handoff["problem_state"], "REOPENED")
            self.assertTrue(handoff["same_revision_reopened"])
            self.assertTrue(handoff["outcome_receipt_observed"])
            self.assertEqual(handoff["latest_event"]["relation_type"], "REOPEN")
            self.assertEqual(handoff["latest_event"]["reason_code"], "explicit_same_problem_correction")

            large_contract = capsule(summary="x" * 2_000)
            large_contract["acceptance_criteria"] = [
                {"criterion_id": f"criterion-{index}", "summary": "y" * 700}
                for index in range(1, 7)
            ]
            large_opened = ledger.problem_record_event(
                open_event("large-resolution-capsule-open", contract_capsule=large_contract),
                now=NOW,
                authority_context="RUNTIME_EXPLICIT_USER",
            )
            large_problem_id = str(large_opened["event"]["problem_id"])
            ledger.problem_record_event({
                "operation": "link", "event_id": "large-resolution-capsule-link",
                "problem_id": large_problem_id, "problem_revision": 1,
                "run_id": "run-large-resolution-capsule", "link_role": "PRIMARY",
                "relation_type": "ENGINEERING_ATTEMPT_BOUND",
                "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED",
            }, now=NOW, authority_context="RUNTIME_BINDING")
            large_handoff = ledger.problem_handoff_for_run("run-large-resolution-capsule")
            assert large_handoff is not None
            self.assertGreater(large_handoff["contract_capsule_bytes"], PROBLEM_HANDOFF_CONTRACT_EMBED_MAX_BYTES)
            self.assertIsNone(large_handoff["contract_capsule"])
            self.assertFalse(large_handoff["contract_capsule_included"])
            self.assertEqual(large_handoff["contract_capsule_omission_reason"], "EXCEEDS_HANDOFF_EMBED_BUDGET")
            self.assertTrue(large_handoff["fresh_context"]["exact_revision_refresh_required"])
        finally:
            temporary.cleanup()

    def test_invalid_shadow_frame_restores_pending_host_turn_before_run_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = Runtime(root, permission_mode="safe")
            runtime._orchestration_workspace_identity = lambda _path: {
                "branch": "test",
                "base_head": "head",
                "worktree_fp": "worktree",
            }
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                attach_chatweb(runtime, "invalid-frame")
                stage_host_turn(root, "invalid-frame-open")
                opened = runtime.task_control({
                    "action": "problem",
                    "problem_event": public_event(open_event("invalid-frame-open")),
                })
                event = opened["problem"]["event"]
                pending = stage_host_turn(root, "invalid-frame-run")
                with self.assertRaises(ToolFailure) as invalid:
                    runtime._agent_orchestration_context({
                        "workflow": "bugfix",
                        "phase": "prepare",
                        "execution_mode": "mcp_only",
                        "problem_context": {
                            "work_origin": "problem",
                            "problem_id": str(event["problem_id"]),
                            "problem_revision": 1,
                            "contract_fingerprint": str(event["contract_fingerprint"]),
                            "resolution_claim": "none",
                            "frame": {
                                "schema_version": 1,
                                "frame_id": "frame-invalid",
                                "frame_revision": 1,
                                "observation": "The bounded fixture is stale",
                                "a_star": {
                                    "domains": ["source"],
                                    "phenomena": ["stale fixture"],
                                    "ownership_boundaries": [],
                                    "relations": [],
                                },
                                "governing_invariants": [],
                                "ownership": [],
                                "hypotheses": [],
                                "counterevidence": [],
                                "decision_delta": {
                                    "tested_observation": "Focused fixture read",
                                    "changed_decision": False,
                                    "next_action": "Keep the run shadow-only",
                                    "rationale": "No bounded intervention is authorized",
                                },
                                "closure_falsifier": "A fresh read still reports stale state",
                                "authority_side_effects": True,
                            },
                        },
                    }, objective="reject an authority-bearing shadow frame")
                self.assertEqual(invalid.exception.code, "PRL_FRAME_INVALID")
                self.assertTrue(pending.exists())
                self.assertEqual(runtime.orchestration_ledger.list_runs(limit=10), [])
            finally:
                runtime.close()

    def test_task_acceptance_bridges_only_a_covered_exact_full_problem_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            runtime._orchestration_workspace_identity = lambda _path: {
                "branch": "test",
                "base_head": "a" * 40,
                "worktree_fp": "b" * 64,
            }
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                attach_chatweb(runtime, "runtime-c3")
                stage_host_turn(root, "runtime-c3-open")
                opened = runtime.task_control({"action": "problem", "problem_event": public_event(open_event("runtime-c3-open"))})
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
                        "frame": {
                            "schema_version": 1, "frame_id": "frame-runtime-c3", "frame_revision": 1,
                            "observation": "The bounded fixture value is incorrect",
                            "a_star": {"domains": ["source"], "phenomena": ["incorrect value"], "ownership_boundaries": [], "relations": []},
                            "governing_invariants": [{"invariant_id": "invariant-1", "summary": "Preserve the existing public contract"}],
                            "ownership": [], "hypotheses": [],
                            "counterevidence": [{
                                "observation_id": "observation-runtime-c3",
                                "summary": "A prior bounded intervention did not change the value",
                                "impact": "Review whether the current frame explains the unchanged observation",
                            }],
                            "decision_delta": {"tested_observation": "Focused fixture read", "changed_decision": True, "next_action": "Apply the bounded patch", "rationale": "The exact value is the selected cause"},
                            "closure_falsifier": "A focused read still shows the old value",
                        },
                    },
                })
                run_id = str(workflow["orchestration"]["run_id"])
                wave_id = str(workflow["orchestration"]["wave_id"])
                wave_metadata = runtime.orchestration_ledger.list_waves(run_id)[0]["metadata"]
                self.assertEqual(wave_metadata["problem_resolution"]["problem_frame"]["frame_id"], "frame-runtime-c3")
                advisory = wave_metadata["problem_resolution"]["counterevidence_frame_update_advisory"]
                self.assertEqual(advisory["status"], "COUNTEREVIDENCE_REQUIRES_FRAME_REVIEW")
                self.assertTrue(advisory["frame_update_or_explanation_recommended"])
                self.assertFalse(advisory["automatic_mutation_gate"])
                frame_event = next(item for item in runtime.orchestration_ledger.list_events(run_id, wave_id=wave_id) if item["event_type"] == "problem_frame_shadow")
                self.assertEqual(frame_event["payload"]["counterevidence_advisory_status"], "COUNTEREVIDENCE_REQUIRES_FRAME_REVIEW")
                self.assertTrue(frame_event["payload"]["frame_update_or_explanation_recommended"])
                self.assertFalse(frame_event["payload"]["materiality_inferred"])
                self.assertFalse(frame_event["payload"]["automatic_mutation_gate"])
                resolution_capsule = runtime.orchestration_ledger.problem_handoff_for_run(run_id)
                assert resolution_capsule is not None
                self.assertEqual(resolution_capsule["problem_frame_status"], "OBSERVED")
                self.assertEqual(resolution_capsule["problem_frame"]["frame_id"], "frame-runtime-c3")
                self.assertEqual(resolution_capsule["problem_frame"]["event_hash"], frame_event["event_hash"])
                self.assertEqual(resolution_capsule["problem_frame"]["counterevidence_count"], 1)
                self.assertTrue(resolution_capsule["problem_frame"]["decision_changed"])
                self.assertTrue(resolution_capsule["problem_frame"]["frame_update_or_explanation_recommended"])
                self.assertFalse(resolution_capsule["problem_frame"]["materiality_inferred"])
                self.assertFalse(resolution_capsule["problem_frame"]["authority_side_effects"])
                self.assertFalse(resolution_capsule["fresh_context"]["problem_frame_content_included"])
                recorded_handoff = runtime.task_control({
                    "action": "handoff",
                    "handoff_action": "record",
                    "run_id": run_id,
                    "wave_id": wave_id,
                    "payload": {"next_action": "Continue from the derived resolution capsule"},
                })
                self.assertTrue(recorded_handoff["recorded"])
                stored_lineage = recorded_handoff["capsule"]["payload"]["problem_lineage"]
                self.assertEqual(stored_lineage["kind"], "derived_resolution_capsule")
                self.assertEqual(stored_lineage["problem_frame"]["frame_sha256"], frame_event["payload"]["frame_sha256"])
                with self.assertRaises(ToolFailure) as reserved_handoff:
                    runtime.task_control({
                        "action": "handoff",
                        "handoff_action": "record",
                        "run_id": run_id,
                        "wave_id": wave_id,
                        "payload": {"problem_lineage": {"caller": "forged"}},
                    })
                self.assertEqual(reserved_handoff.exception.code, "HANDOFF_PRL_FIELD_RESERVED")
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
                self.assertEqual(invalid_manifest.exception.code, "PRL_OUTCOME_CLAIM_INVALID")
                with self.assertRaises(ToolFailure) as missing_envelope:
                    runtime.task_control({
                        "action": "accept", "run_id": run_id,
                        "reason": "full-problem closure omits its bounded envelope",
                        "problem_coverage_manifest": {"criterion-1": [proof_id]},
                    })
                self.assertEqual(
                    missing_envelope.exception.code,
                    "PRL_RESOLUTION_ENVELOPE_REQUIRED",
                )
                with self.assertRaises(ToolFailure) as invalid_envelope:
                    runtime.task_control({
                        "action": "accept", "run_id": run_id,
                        "reason": "the closure falsifier has not run",
                        "problem_coverage_manifest": {"criterion-1": [proof_id]},
                        "problem_resolution_envelope": {
                            **resolution_envelope(),
                            "closure_falsification_probe": {
                                **resolution_envelope()["closure_falsification_probe"],
                                "executed": False,
                            },
                        },
                    })
                self.assertEqual(
                    invalid_envelope.exception.code,
                    "PRL_RESOLUTION_ENVELOPE_INVALID",
                )

                with patch.object(
                    runtime.orchestration_ledger,
                    "problem_reconcile_provisional_from_checkpoint",
                    side_effect=OSError("injected post-checkpoint bridge failure"),
                ):
                    accepted = runtime.task_control({
                        "action": "accept",
                        "run_id": run_id,
                        "reason": "exact full-problem claim has passed proof coverage",
                        "problem_coverage_manifest": {"criterion-1": [proof_id]},
                        "problem_resolution_envelope": resolution_envelope(),
                    })
                self.assertTrue(accepted["accepted"])
                self.assertEqual(accepted["problem_outcome_bridge"]["status"], "RECONCILIATION_REQUIRED")
                self.assertEqual(runtime.orchestration_ledger.get_run(run_id)["status"], "accepted")
                checkpoint_id = runtime.orchestration_ledger.list_checkpoints(run_id, wave_id=wave_id)[-1]["checkpoint_id"]
                original_controller = dict(runtime.request_context.hub_client)
                runtime.request_context.hub_client = {
                    **original_controller,
                    "client_id": "chatweb-other-controller",
                }
                runtime._touch_hub_client(runtime.request_context.hub_client)
                with self.assertRaises(ToolFailure) as other_controller:
                    runtime.task_control({"action": "problem", "problem_event": {
                        "operation": "reconcile_provisional", "run_id": run_id,
                        "wave_id": wave_id, "checkpoint_id": checkpoint_id,
                    }})
                self.assertEqual(other_controller.exception.code, "CONTROLLER_LEASE_REQUIRED")
                runtime.request_context.hub_client = original_controller
                reconciled = runtime.task_control({"action": "problem", "problem_event": {
                    "operation": "reconcile_provisional", "run_id": run_id,
                    "wave_id": wave_id, "checkpoint_id": checkpoint_id,
                }})
                self.assertTrue(reconciled["problem"]["recorded"])
                self.assertEqual(reconciled["receipt_id"], reconciled["problem"]["event"]["event_hash"])
                replayed = runtime.task_control({"action": "problem", "problem_event": {
                    "operation": "reconcile_provisional", "run_id": run_id,
                    "wave_id": wave_id, "checkpoint_id": checkpoint_id,
                }})
                self.assertTrue(replayed["problem"]["idempotent"])
                self.assertEqual(runtime.orchestration_ledger.problem_get(problem_id)["thread"]["resolution_state"], "PROVISIONALLY_RESOLVED")

                stage_host_turn(root, "runtime-c3-confirm")
                confirmed = runtime.task_control({"action": "problem", "problem_event": {
                    "operation": "confirm", "event_id": "runtime-c3-confirm", "problem_id": problem_id,
                    "problem_revision": 1, "feedback_intent": "CONFIRM_RESOLVED",
                }})
                confirmation = confirmed["problem"]["event"]
                self.assertEqual(confirmation["reason_code"], "user_confirmation")
                self.assertEqual(confirmation["event_schema_version"], PROBLEM_EVENT_SCHEMA_CURRENT)
                self.assertEqual(confirmation["turn_id"], "turn-runtime-c3-confirm")
                self.assertEqual(confirmation["trace_id"], "trace-runtime-c3-confirm")
                self.assertEqual(confirmation["transition_authority"], "RUNTIME_OUTCOME_RECEIPT")
                self.assertEqual(confirmation["outcome_receipt_type"], "CHATWEB_EXPLICIT_USER_OUTCOME_V1")
                self.assertEqual(
                    confirmation["outcome_receipt_id"],
                    problem_outcome_receipt_id(
                        receipt_type="CHATWEB_EXPLICIT_USER_OUTCOME_V1",
                        event_id="runtime-c3-confirm",
                        problem_id=problem_id,
                        problem_revision=1,
                        turn_id="turn-runtime-c3-confirm",
                        trace_id="trace-runtime-c3-confirm",
                    ),
                )
                self.assertTrue(runtime.orchestration_ledger.problem_verify_chain(problem_id)["ok"])
                stage_host_turn(root, "runtime-c3-reopen")
                reopened = runtime.task_control({"action": "problem", "problem_event": {
                    "operation": "reopen", "event_id": "runtime-c3-reopen", "problem_id": problem_id,
                    "problem_revision": 1, "feedback_intent": "SAME_PROBLEM_STILL_FAILING",
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
                runtime.orchestration_ledger.record_proof(
                    run_id=workflow["orchestration"]["run_id"], wave_id=workflow["orchestration"]["wave_id"],
                    stage_id="focused", stage_version="1", input_fingerprint="schema-inactive-proof", status="passed",
                )
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
                    attach_chatweb(runtime, f"non-full-{origin}")
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
                        stage_host_turn(root, f"{origin}-none-open")
                        opened = runtime.task_control({"action": "problem", "problem_event": public_event(open_event(f"{origin}-none-open"))})
                        event = opened["problem"]["event"]
                        request["problem_context"] = {
                            "work_origin": "problem", "problem_id": str(event["problem_id"]),
                            "problem_revision": 1, "contract_fingerprint": str(event["contract_fingerprint"]),
                            "resolution_claim": "none",
                        }
                    workflow = runtime.agent_workflow(request)
                    runtime.orchestration_ledger.record_proof(
                        run_id=workflow["orchestration"]["run_id"], wave_id=workflow["orchestration"]["wave_id"],
                        stage_id="focused", stage_version="1", input_fingerprint=f"non-full-{origin}-proof", status="passed",
                    )
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

    def test_public_semantic_authority_is_runtime_derived_and_claim_restores_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = Runtime(root, permission_mode="safe")
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                attach_chatweb(runtime, "authority")
                with self.assertRaises(ToolFailure) as human:
                    runtime.task_control({"action": "problem", "problem_event": {**open_event("human"), "provenance": "HUMAN_ANNOTATED"}})
                self.assertEqual(human.exception.code, "PRL_HUMAN_REVIEW_RECEIPT_REQUIRED")
                with self.assertRaises(ToolFailure) as binding:
                    runtime.task_control({"action": "problem", "problem_event": {"operation": "link", "event_id": "public-link"}})
                self.assertEqual(binding.exception.code, "PRL_BINDING_RUNTIME_ONLY")
                with self.assertRaises(ToolFailure) as guard:
                    runtime.task_control({"action": "problem", "problem_event": {"operation": "block", "event_id": "public-guard", "provenance": "DETERMINISTIC_EVIDENCE"}})
                self.assertEqual(guard.exception.code, "PRL_GUARD_RUNTIME_ONLY")
                with self.assertRaises(ToolFailure) as clock:
                    runtime.task_control({"action": "problem", "problem_event": {**public_event(open_event("clock")), "occurred_at": NOW, "occurred_at_source": "EXPLICIT_USER"}})
                self.assertEqual(clock.exception.code, "PRL_CLOCK_FIELDS_FORBIDDEN")
                with self.assertRaises(ToolFailure) as outcome_receipt:
                    runtime.task_control({"action": "problem", "problem_event": {
                        "operation": "confirm",
                        "event_id": "caller-receipt",
                        "problem_id": "caller-problem",
                        "problem_revision": 1,
                        "feedback_intent": "CONFIRM_RESOLVED",
                        "outcome_receipt_type": "CHATWEB_EXPLICIT_USER_OUTCOME_V1",
                        "outcome_receipt_id": "0" * 64,
                    }})
                self.assertEqual(outcome_receipt.exception.code, "PRL_CALLER_OUTCOME_RECEIPT_FORBIDDEN")

                pending = stage_host_turn(root, "restore")
                with patch.object(runtime.orchestration_ledger, "problem_record_event", side_effect=ProblemLineageError("injected append failure")):
                    with self.assertRaises(ToolFailure) as failed:
                        runtime.task_control({"action": "problem", "problem_event": public_event(open_event("restored-open"))})
                self.assertEqual(failed.exception.code, "PRL_EVENT_INVALID")
                self.assertTrue(pending.exists())
                recorded = runtime.task_control({"action": "problem", "problem_event": public_event(open_event("restored-open"))})
                self.assertFalse(pending.exists())
                self.assertEqual(recorded["receipt_id"], recorded["problem"]["event"]["event_hash"])
                self.assertEqual(recorded["problem"]["event"]["transition_authority"], "RUNTIME_EXPLICIT_USER")
                self.assertEqual(recorded["problem"]["event"]["provenance"], "CONTROLLER_REPORTED_EXPLICIT_USER")
                self.assertEqual(recorded["problem"]["event"]["occurred_at"], "")
            finally:
                runtime.close()

    def test_not_applicable_requires_exact_non_code_dispositions_and_no_source_receipts(self) -> None:
        temporary, ledger = self._ledger()
        try:
            opened = ledger.problem_record_event(
                open_event("na-open", engineering_floor="NOT_APPLICABLE"),
                now=NOW,
                authority_context="RUNTIME_EXPLICIT_USER",
            )
            problem_id = str(opened["event"]["problem_id"])
            fingerprint = str(opened["event"]["contract_fingerprint"])
            context = {
                "schema_version": 1, "work_origin": "problem", "resolution_claim": "full_problem",
                "problem_id": problem_id, "problem_revision": 1, "contract_fingerprint": fingerprint,
                "engineering_floor": "NOT_APPLICABLE", "policy_eligible": False,
            }
            run_id = ledger.create_run(objective="non-code fixture", metadata={"problem_resolution": context})
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", metadata={"problem_resolution": context})
            client_id = "chatweb:non-code"
            ledger.upsert_hub_client(
                client_id=client_id, client_type="chatweb", role="controller", status="online",
                runtime_instance_id="runtime-na",
            )
            controller = ledger.acquire_controller_lease(
                run_id=run_id, owner_client_id=client_id, lease_id="lease-na", ttl_seconds=60,
            )
            authority = {
                "client_id": client_id, "client_type": "chatweb", "runtime_instance_id": "runtime-na",
                "lease_id": "lease-na", "fencing_token": controller["fencing_token"],
            }
            files = accepted_files(run_id, wave_id)
            with self.assertRaises(ProblemLineageError):
                ledger.problem_prepare_eocl_outcome_claim(
                    run_id=run_id, wave_id=wave_id, git_head="head", worktree_fp="worktree",
                    proof_fingerprint="", accepted_files=files, durable_mutation=False,
                    coverage_manifest={"criterion-1": []}, controller_authority=authority,
                )
            with self.assertRaises(ProblemLineageError):
                ledger.problem_prepare_eocl_outcome_claim(
                    run_id=run_id, wave_id=wave_id, git_head="head", worktree_fp="worktree",
                    proof_fingerprint="", accepted_files=files, durable_mutation=False,
                    criterion_dispositions={"criterion-1": "UNKNOWN"}, controller_authority=authority,
                )
            outcome = ledger.problem_prepare_eocl_outcome_claim(
                run_id=run_id, wave_id=wave_id, git_head="head", worktree_fp="worktree",
                proof_fingerprint="", accepted_files=files, durable_mutation=False,
                criterion_dispositions={"criterion-1": "SATISFIED_NON_CODE"}, resolution_envelope=resolution_envelope(), controller_authority=authority,
            )
            self.assertTrue(outcome["recorded"])
            replay = ledger.problem_prepare_eocl_outcome_claim(
                run_id=run_id, wave_id=wave_id, git_head="head", worktree_fp="worktree",
                proof_fingerprint="", accepted_files=files, durable_mutation=False,
                criterion_dispositions={"criterion-1": "SATISFIED_NON_CODE"}, resolution_envelope=resolution_envelope(), controller_authority=authority,
            )
            self.assertTrue(replay["idempotent"])
            self.assertEqual(replay["claim_sha256"], outcome["claim_sha256"])
        finally:
            temporary.cleanup()

    def test_contract_capsule_rejects_bounded_encoded_credentials_and_pii(self) -> None:
        temporary, ledger = self._ledger()
        try:
            encoded_header = base64.b64encode(b"Authorization: Bearer abcdefghijklmnop").decode("ascii")
            encoded_pii = base64.b64encode(b"admin@example.com").decode("ascii")
            encoded_pat = "github_pat_abcdefghijklmnopqrstuv".encode("utf-8").hex()
            leaks = [
                "api%5Fkey%3Dsupersecretvalue",
                "api%255Fkey%253Dsupersecretvalue",
                encoded_header,
                encoded_pat,
                "ａｐｉ＿ｋｅｙ＝abcdefghijklmnop",
                encoded_pii,
            ]
            for index, leak in enumerate(leaks):
                with self.assertRaises(ProblemLineageError):
                    ledger.problem_record_event(
                        open_event(f"encoded-leak-{index}", contract_capsule=capsule(leak)),
                        now=NOW,
                        authority_context="RUNTIME_EXPLICIT_USER",
                    )
        finally:
            temporary.cleanup()

    def test_contract_capsule_encoded_privacy_scan_preserves_benign_text(self) -> None:
        temporary, ledger = self._ledger()
        try:
            benign = ["Token budget is capped at 4096", "URL path /a%20b is expected", "c2VjcmV0YXJ5", "Checksum deadbeef1234", "Unicode emoji ✅"]
            for index, text in enumerate(benign):
                opened = ledger.problem_record_event(
                    open_event(f"benign-{index}", contract_capsule=capsule(text)),
                    now=NOW,
                    authority_context="RUNTIME_EXPLICIT_USER",
                )
                self.assertEqual(
                    ledger.problem_get(opened["event"]["problem_id"])["current_revision"]["capsule"]["objective_summary"],
                    text,
                )
        finally:
            temporary.cleanup()

    def test_reconciliation_preserves_historical_no_clock_provisional_event(self) -> None:
        temporary, ledger = self._ledger()
        try:
            opened = ledger.problem_record_event(open_event("legacy-clock-open"), now=NOW, authority_context="RUNTIME_EXPLICIT_USER")
            problem_id = str(opened["event"]["problem_id"])
            fingerprint = str(opened["event"]["contract_fingerprint"])
            context = {"schema_version": 1, "work_origin": "problem", "resolution_claim": "full_problem", "problem_id": problem_id, "problem_revision": 1, "contract_fingerprint": fingerprint, "engineering_floor": "REQUIRED", "policy_eligible": False}
            run_id = ledger.create_run(objective="historical bridge fixture", metadata={"problem_resolution": context})
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only", metadata={"problem_resolution": context})
            proof_id = ledger.record_proof(run_id=run_id, wave_id=wave_id, stage_id="focused", stage_version="1", input_fingerprint="legacy-clock-proof", status="passed")
            manifest = {"criterion-1": [proof_id]}
            proof_fingerprint = hashlib.sha256(f"{proof_id}:legacy-clock-proof".encode()).hexdigest()
            files = accepted_files(run_id, wave_id)
            outcome = ledger.problem_prepare_eocl_outcome_claim(
                run_id=run_id, wave_id=wave_id, git_head="head", worktree_fp="worktree",
                proof_fingerprint=proof_fingerprint, accepted_files=files, durable_mutation=False,
                coverage_manifest=manifest, resolution_envelope=resolution_envelope(),
            )
            checkpoint = ledger.accept_checkpoint_atomic(
                run_id=run_id, wave_id=wave_id, git_head="head", proof_fingerprint=proof_fingerprint,
                metadata={"worktree_fp": "worktree", "accepted_files": files, "problem_outcome_claim": outcome["claim"], "problem_outcome_claim_sha256": outcome["claim_sha256"]},
            )
            checkpoint_id = str(checkpoint["checkpoint_id"])
            legacy_event_id = "prl-provisional-v11-" + hashlib.sha256("\x1f".join((run_id, wave_id, problem_id, "1", checkpoint_id)).encode()).hexdigest()
            historical = ledger.problem_record_event({
                "operation": "provisional_resolve", "event_id": legacy_event_id,
                "problem_id": problem_id, "problem_revision": 1, "run_id": run_id, "wave_id": wave_id,
                "provenance": "DETERMINISTIC_EVIDENCE", "evidence_level": "OBSERVED",
            }, now=NOW, authority_context="RUNTIME_EOCL")
            replay = ledger.problem_record_provisional_from_eocl(run_id=run_id, wave_id=wave_id, checkpoint_id=checkpoint_id, now="2026-08-25T01:00:00Z")
            self.assertTrue(replay["idempotent"])
            self.assertEqual(replay["event"]["event_hash"], historical["event"]["event_hash"])
            self.assertEqual(replay["event"]["occurred_at"], "")
            self.assertEqual(replay["event"]["clock_authority"], "")
        finally:
            temporary.cleanup()

    def test_public_schema_has_no_caller_state_or_policy_grant(self) -> None:
        workflow_schema = input_schemas()["agent_workflow"]
        schema = input_schemas()["task_control"]
        event_schema = schema["properties"]["problem_event"]
        self.assertIn("problem_context", workflow_schema["properties"])
        for property_name in (
            "problem_resolution_envelope",
            "problem_coverage_manifest",
            "problem_criterion_dispositions",
        ):
            self.assertIn(property_name, schema["properties"])
        self.assertEqual(schema["properties"]["action"]["enum"].count("problem"), 1)
        self.assertNotIn("eligible_for_policy", event_schema["properties"])
        self.assertNotIn("state", event_schema["properties"])
        self.assertNotIn("outcome_receipt_type", event_schema["properties"])
        self.assertNotIn("outcome_receipt_id", event_schema["properties"])
        self.assertIn("reconcile_provisional", event_schema["properties"]["operation"]["enum"])
        self.assertEqual(
            schema["properties"]["problem_criterion_dispositions"]["additionalProperties"]["enum"],
            ["SATISFIED_NON_CODE"],
        )
        with self.assertRaises(Exception):
            validate_arguments("task_control", {"action": "problem", "problem_event": {"operation": "open", "event_id": "bad", "eligible_for_policy": True}})
        with self.assertRaises(Exception):
            validate_arguments("task_control", {"action": "problem", "problem_event": {
                "operation": "confirm",
                "event_id": "bad-receipt",
                "outcome_receipt_type": "CHATWEB_EXPLICIT_USER_OUTCOME_V1",
                "outcome_receipt_id": "0" * 64,
            }})


if __name__ == "__main__":
    unittest.main()
