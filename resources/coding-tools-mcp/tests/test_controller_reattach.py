from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import JsonRpcError, ToolFailure
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.tool_schema import input_schemas, validate_arguments


NOW = "2026-09-01T00:00:00+00:00"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def contract(summary: str = "Preserve exact Goal continuity") -> dict[str, object]:
    return {
        "objective_summary": summary,
        "acceptance_criteria": [
            {"criterion_id": "criterion-1", "summary": "Old endpoint is fenced"},
            {"criterion_id": "criterion-2", "summary": "New endpoint resumes exactly"},
        ],
        "protected_invariants": ["Eight public tools", "No duplicate authority"],
        "constraints": ["No transcript replay"],
        "unresolved_conditions": [],
    }


def open_problem(ledger: OrchestrationLedger, event_id: str = "reattach-open") -> str:
    opened = ledger.problem_record_event(
        {
            "operation": "open",
            "event_id": event_id,
            "task_id": "task-reattach",
            "task_class": "feature",
            "engineering_floor": "REQUIRED",
            "contract_capsule": contract(),
            "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
            "evidence_level": "OBSERVED",
        },
        now=NOW,
        authority_context="RUNTIME_EXPLICIT_USER",
    )
    return str(opened["event"]["problem_id"])


def attach(runtime: Runtime, label: str) -> dict[str, str]:
    runtime.request_context.hub_client = {
        "client_id": "chatweb",
        "client_type": "chatweb",
        "role": "controller",
        "session_instance": f"session-{label}",
        "execution_context_id": digest(label)[:16],
        "capabilities": {},
    }
    runtime._touch_hub_client(runtime.request_context.hub_client)
    identity = runtime._continuity_current_controller_identity(required=True)
    assert identity is not None
    return identity


def record_checkpoint(
    runtime: Runtime,
    problem_id: str,
    *,
    problem_revision: int,
    event_id: str,
    kind: str,
) -> dict[str, object]:
    return runtime.task_control(
        {
            "action": "continuity",
            "continuity_action": "checkpoint",
            "continuity_event": {
                "problem_id": problem_id,
                "problem_revision": problem_revision,
                "material_event_kind": kind,
                "material_event_id": event_id,
            },
        }
    )


def current_core(runtime: Runtime, problem_id: str, problem_revision: int = 1) -> dict[str, object]:
    return runtime.task_control(
        {
            "action": "continuity",
            "continuity_action": "get",
            "continuity_event": {
                "problem_id": problem_id,
                "problem_revision": problem_revision,
            },
        }
    )["continuity_core"]


def reattach(
    runtime: Runtime,
    problem_id: str,
    *,
    problem_revision: int = 1,
    reattach_id: str,
    ack_id: str,
    core_fingerprint: str,
    knowledge_revision: int | None = None,
) -> dict[str, object]:
    event: dict[str, object] = {
        "problem_id": problem_id,
        "problem_revision": problem_revision,
        "reattach_id": reattach_id,
        "ack_id": ack_id,
        "continuity_core_fingerprint": core_fingerprint,
    }
    if knowledge_revision is not None:
        event["knowledge_revision"] = knowledge_revision
    return runtime.task_control(
        {
            "action": "continuity",
            "continuity_action": "reattach",
            "continuity_event": event,
        }
    )


def problem_context(runtime: Runtime, problem_id: str, problem_revision: int = 1) -> dict[str, object]:
    problem = runtime.orchestration_ledger.problem_get(problem_id)
    assert problem is not None
    return {
        "work_origin": "problem",
        "resolution_claim": "none",
        "problem_id": problem_id,
        "problem_revision": problem_revision,
        "contract_fingerprint": str(problem["current_revision"]["contract_fingerprint"]),
    }


def begin_problem_run(runtime: Runtime, problem_id: str, problem_revision: int = 1) -> str:
    objective = "Continue the exact durable Goal"
    context, _identity = runtime._agent_orchestration_context(
        {
            "workflow": "bugfix",
            "phase": "prepare",
            "objective": objective,
            "execution_mode": "mcp_only",
            "problem_context": problem_context(runtime, problem_id, problem_revision),
        },
        objective=objective,
    )
    return context.run_id


def advance_run_to_state(runtime: Runtime, run_id: str, target: str) -> None:
    context = runtime.orchestration_control.snapshot(run_id)
    assert context is not None
    runtime.orchestration_control.mark_ready(context)
    runtime.orchestration_control.select_route(
        context,
        {
            "requested": "deterministic",
            "selected": "deterministic",
            "reason": "controller continuity regression fixture",
        },
    )
    runtime.orchestration_control.transition(context, "EXECUTING", reason="fixture")
    if target in {"PROVING", "ACCEPTING"}:
        runtime.orchestration_control.transition(context, "PROVING", reason="fixture")
    if target == "ACCEPTING":
        runtime.orchestration_control.transition(context, "ACCEPTING", reason="fixture")


def release_run_controller(runtime: Runtime, run_id: str) -> dict[str, object]:
    lease = runtime.orchestration_ledger.get_controller_lease(run_id)
    assert lease is not None
    released = runtime.orchestration_ledger.release_controller_lease(
        run_id=run_id,
        owner_client_id=str(lease["owner_client_id"]),
        lease_id=str(lease["lease_id"]),
        fencing_token=int(lease["fencing_token"]),
    )
    assert released
    return lease


class ControllerReattachTests(unittest.TestCase):
    def test_unactivated_problem_ledger_does_not_break_unbound_run_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = OrchestrationLedger(Path(directory) / "ledger.sqlite3")
            run_id = ledger.create_run(objective="Ordinary non-Problem work")

            self.assertIsNone(ledger.controller_run_problem_binding(run_id))

    def test_schema_is_strict_and_public_tool_count_remains_eight(self) -> None:
        schemas = input_schemas()
        actions = schemas["task_control"]["properties"]["continuity_action"]["enum"]
        self.assertIn("reattach", actions)
        validate_arguments(
            "task_control",
            {
                "action": "continuity",
                "continuity_action": "reattach",
                "continuity_event": {
                    "problem_id": "problem-1",
                    "problem_revision": 1,
                    "reattach_id": "reattach-1",
                    "ack_id": "ack-1",
                    "continuity_core_fingerprint": digest("core"),
                },
            },
        )
        with self.assertRaises(JsonRpcError):
            validate_arguments(
                "task_control",
                {
                    "action": "continuity",
                    "continuity_action": "reattach",
                    "continuity_event": {
                        "problem_id": "problem-1",
                        "problem_revision": 1,
                        "reattach_id": "reattach-1",
                        "ack_id": "ack-1",
                        "continuity_core_fingerprint": "not-a-digest",
                    },
                },
            )
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(directory))
            try:
                self.assertEqual(runtime.tool_contract["tool_count"], 8)
            finally:
                runtime.close()

    def test_idle_reattach_replay_and_old_endpoint_new_run_fence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = Runtime(root)
            first.orchestration_ledger.migrate_problem_lineage_schema()
            problem_id = open_problem(first.orchestration_ledger, "idle-open")
            attach(first, "a-idle")
            checkpoint = record_checkpoint(
                first,
                problem_id,
                problem_revision=1,
                event_id="idle-checkpoint",
                kind="PROBLEM_OPENED",
            )
            self.assertEqual(checkpoint["knowledge_checkpoint"]["status"], "ADVANCED")
            second = Runtime(root)
            try:
                attach(second, "b-idle")
                core = current_core(second, problem_id)
                request = {
                    "problem_revision": 1,
                    "reattach_id": "idle-reattach",
                    "ack_id": "idle-ack",
                    "core_fingerprint": str(core["continuity_core_fingerprint"]),
                    "knowledge_revision": 1,
                }
                transferred = reattach(second, problem_id, **request)
                receipt = transferred["controller_reattach"]
                self.assertEqual(receipt["status"], "REATTACHED")
                self.assertEqual(receipt["generation"], 1)
                self.assertEqual(receipt["active_run_transfers"], [])
                self.assertEqual(transferred["knowledge_ack"]["ack"]["status"], "CURRENT")
                self.assertFalse(transferred["write_authority_granted"])
                replay = reattach(second, problem_id, **request)
                self.assertEqual(replay["controller_reattach"]["status"], "IDEMPOTENT")
                self.assertEqual(replay["controller_reattach"]["generation"], 1)
                with self.assertRaises(ToolFailure) as conflict:
                    reattach(
                        second,
                        problem_id,
                        **{**request, "ack_id": "idle-conflicting-ack"},
                    )
                self.assertEqual(
                    conflict.exception.code, "CONTROLLER_REATTACH_IDENTITY_CONFLICT"
                )

                before = len(first.orchestration_ledger.list_runs(limit=100))
                with self.assertRaises(ToolFailure) as stale:
                    begin_problem_run(first, problem_id)
                self.assertEqual(stale.exception.code, "GOAL_CONTROLLER_FENCE_STALE")
                self.assertEqual(len(first.orchestration_ledger.list_runs(limit=100)), before)

                run_id = begin_problem_run(second, problem_id)
                lease = second.orchestration_ledger.get_controller_lease(run_id)
                assert lease is not None
                self.assertEqual(
                    lease["owner_client_id"],
                    second._continuity_current_controller_identity(required=True)["owner_client_id"],
                )
            finally:
                second.close()
                first.close()

    def test_active_run_transfers_atomically_and_old_endpoint_stays_fenced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = Runtime(root)
            first.orchestration_ledger.migrate_problem_lineage_schema()
            problem_id = open_problem(first.orchestration_ledger, "active-open")
            first_identity = attach(first, "a-active")
            record_checkpoint(
                first,
                problem_id,
                problem_revision=1,
                event_id="active-checkpoint",
                kind="PROBLEM_OPENED",
            )
            run_id = begin_problem_run(first, problem_id)
            before_lease = first.orchestration_ledger.get_controller_lease(run_id)
            assert before_lease is not None
            self.assertEqual(before_lease["owner_client_id"], first_identity["owner_client_id"])
            second = Runtime(root)
            try:
                second_identity = attach(second, "b-active")
                core = current_core(second, problem_id)
                with self.assertRaises(ToolFailure) as handoff:
                    reattach(
                        second,
                        problem_id,
                        reattach_id="active-reattach",
                        ack_id="active-ack",
                        core_fingerprint=str(core["continuity_core_fingerprint"]),
                        knowledge_revision=1,
                    )
                self.assertEqual(handoff.exception.code, "CONTROLLER_HANDOFF_REQUIRED")
                self.assertTrue(
                    first.orchestration_ledger.release_controller_lease(
                        run_id=run_id,
                        owner_client_id=str(before_lease["owner_client_id"]),
                        lease_id=str(before_lease["lease_id"]),
                        fencing_token=int(before_lease["fencing_token"]),
                    )
                )
                result = reattach(
                    second,
                    problem_id,
                    reattach_id="active-reattach",
                    ack_id="active-ack",
                    core_fingerprint=str(core["continuity_core_fingerprint"]),
                    knowledge_revision=1,
                )
                transfers = result["controller_reattach"]["active_run_transfers"]
                self.assertEqual([item["run_id"] for item in transfers], [run_id])
                after_lease = second.orchestration_ledger.get_controller_lease(run_id)
                assert after_lease is not None
                self.assertEqual(after_lease["owner_client_id"], second_identity["owner_client_id"])
                self.assertEqual(
                    after_lease["fencing_token"], before_lease["fencing_token"] + 1
                )
                with self.assertRaises(ToolFailure) as stale:
                    first._require_hub_controller(run_id)
                self.assertEqual(stale.exception.code, "GOAL_CONTROLLER_FENCE_STALE")
                self.assertTrue(second._require_hub_controller(run_id))
                replay = reattach(
                    second,
                    problem_id,
                    reattach_id="active-reattach",
                    ack_id="active-ack",
                    core_fingerprint=str(core["continuity_core_fingerprint"]),
                    knowledge_revision=1,
                )
                self.assertTrue(replay["controller_reattach"]["idempotent"])
                self.assertEqual(
                    second.orchestration_ledger.get_controller_lease(run_id)["fencing_token"],
                    after_lease["fencing_token"],
                )
            finally:
                second.close()
                first.close()

    def test_stale_missing_and_future_ack_recovery_are_typed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Path(directory))
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                problem_id = open_problem(runtime.orchestration_ledger, "ack-open")
                attach(runtime, "checkpoint-owner")
                record_checkpoint(
                    runtime,
                    problem_id,
                    problem_revision=1,
                    event_id="ack-material-1",
                    kind="PROBLEM_OPENED",
                )
                runtime.orchestration_ledger.problem_record_event(
                    {
                        "operation": "provisional_resolve",
                        "event_id": "ack-provisional",
                        "problem_id": problem_id,
                        "problem_revision": 1,
                        "provenance": "DETERMINISTIC_EVIDENCE",
                        "evidence_level": "OBSERVED",
                    },
                    now=NOW,
                    authority_context="RUNTIME_EOCL",
                )
                record_checkpoint(
                    runtime,
                    problem_id,
                    problem_revision=1,
                    event_id="ack-material-2",
                    kind="NEXT_CRITICAL_ACTION_CHANGED",
                )

                attach(runtime, "behind-controller")
                behind_core = current_core(runtime, problem_id)
                behind = reattach(
                    runtime,
                    problem_id,
                    reattach_id="behind-reattach",
                    ack_id="behind-ack",
                    core_fingerprint=str(behind_core["continuity_core_fingerprint"]),
                    knowledge_revision=1,
                )
                self.assertEqual(behind["knowledge_ack"]["ack"]["status"], "BEHIND")
                self.assertEqual(behind["controller_reattach"]["generation"], 1)

                attach(runtime, "missing-controller")
                missing_core = current_core(runtime, problem_id)
                missing = reattach(
                    runtime,
                    problem_id,
                    reattach_id="missing-reattach",
                    ack_id="missing-ack",
                    core_fingerprint=str(missing_core["continuity_core_fingerprint"]),
                )
                self.assertEqual(missing["knowledge_ack"]["ack"]["status"], "MISSING")
                self.assertEqual(missing["controller_reattach"]["generation"], 2)

                attach(runtime, "future-controller")
                future_core = current_core(runtime, problem_id)
                with self.assertRaises(ToolFailure) as unsafe:
                    reattach(
                        runtime,
                        problem_id,
                        reattach_id="future-reattach",
                        ack_id="future-ack",
                        core_fingerprint=str(future_core["continuity_core_fingerprint"]),
                        knowledge_revision=3,
                    )
                self.assertEqual(unsafe.exception.code, "CONTROLLER_REATTACH_ACK_UNSAFE")
                attachment = runtime.orchestration_ledger.controller_goal_attachment(
                    workspace_id=str(future_core["workspace_id"]), problem_id=problem_id
                )
                assert attachment is not None
                self.assertEqual(attachment["generation"], 2)
            finally:
                runtime.close()

    def test_active_run_from_prior_problem_revision_blocks_reattach(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = Runtime(root)
            first.orchestration_ledger.migrate_problem_lineage_schema()
            problem_id = open_problem(first.orchestration_ledger, "revision-run-open")
            attach(first, "revision-a")
            record_checkpoint(
                first,
                problem_id,
                problem_revision=1,
                event_id="revision-material-1",
                kind="PROBLEM_OPENED",
            )
            run_id = begin_problem_run(first, problem_id)
            problem = first.orchestration_ledger.problem_get(problem_id)
            assert problem is not None
            first.orchestration_ledger.problem_record_event(
                {
                    "operation": "revise",
                    "event_id": "revision-run-revise",
                    "problem_id": problem_id,
                    "expected_revision": 1,
                    "expected_contract_fingerprint": str(
                        problem["current_revision"]["contract_fingerprint"]
                    ),
                    "task_class": "feature",
                    "engineering_floor": "REQUIRED",
                    "contract_capsule": contract("Current Revision Two"),
                    "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
                    "evidence_level": "OBSERVED",
                },
                now=NOW,
                authority_context="RUNTIME_EXPLICIT_USER",
            )
            second = Runtime(root)
            try:
                attach(second, "revision-b")
                record_checkpoint(
                    second,
                    problem_id,
                    problem_revision=2,
                    event_id="revision-material-2",
                    kind="PROBLEM_REVISED",
                )
                core = current_core(second, problem_id, 2)
                with self.assertRaises(ToolFailure) as conflict:
                    reattach(
                        second,
                        problem_id,
                        problem_revision=2,
                        reattach_id="revision-run-reattach",
                        ack_id="revision-run-ack",
                        core_fingerprint=str(core["continuity_core_fingerprint"]),
                        knowledge_revision=2,
                    )
                self.assertEqual(
                    conflict.exception.code,
                    "CONTROLLER_REATTACH_ACTIVE_RUN_REVISION_CONFLICT",
                )
                self.assertEqual(conflict.exception.details["conflicts"][0]["run_id"], run_id)
                self.assertIsNone(
                    second.orchestration_ledger.controller_goal_attachment(
                        workspace_id=str(core["workspace_id"]), problem_id=problem_id
                    )
                )
            finally:
                second.close()
                first.close()

    def test_capsule_source_runtime_revision_and_goal_ambiguity_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Path(directory))
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                problem_id = open_problem(runtime.orchestration_ledger, "fresh-open")
                attach(runtime, "fresh-controller")
                record_checkpoint(
                    runtime,
                    problem_id,
                    problem_revision=1,
                    event_id="fresh-material",
                    kind="PROBLEM_OPENED",
                )
                core = current_core(runtime, problem_id)
                original_source = runtime._orchestration_workspace_identity(".")
                drifted_source = copy.deepcopy(original_source)
                drifted_source["source_fingerprint"] = digest("drifted-source")
                with patch.object(
                    runtime, "_orchestration_workspace_identity", return_value=drifted_source
                ):
                    with self.assertRaises(ToolFailure) as stale_source:
                        reattach(
                            runtime,
                            problem_id,
                            reattach_id="source-drift-reattach",
                            ack_id="source-drift-ack",
                            core_fingerprint=str(core["continuity_core_fingerprint"]),
                            knowledge_revision=1,
                        )
                self.assertEqual(stale_source.exception.code, "CAPSULE_STALE")
                with patch.object(
                    runtime,
                    "_loaded_behavior_identity",
                    return_value={"fingerprint": digest("drifted-runtime")},
                ):
                    with self.assertRaises(ToolFailure) as stale_runtime:
                        reattach(
                            runtime,
                            problem_id,
                            reattach_id="runtime-drift-reattach",
                            ack_id="runtime-drift-ack",
                            core_fingerprint=str(core["continuity_core_fingerprint"]),
                            knowledge_revision=1,
                        )
                self.assertEqual(stale_runtime.exception.code, "CAPSULE_STALE")

                core = current_core(runtime, problem_id)
                result = reattach(
                    runtime,
                    problem_id,
                    reattach_id="fresh-reattach",
                    ack_id="fresh-ack",
                    core_fingerprint=str(core["continuity_core_fingerprint"]),
                    knowledge_revision=1,
                )
                self.assertEqual(result["controller_reattach"]["generation"], 1)
                problem = runtime.orchestration_ledger.problem_get(problem_id)
                assert problem is not None
                runtime.orchestration_ledger.problem_record_event(
                    {
                        "operation": "revise",
                        "event_id": "fresh-revision-2",
                        "problem_id": problem_id,
                        "expected_revision": 1,
                        "expected_contract_fingerprint": str(
                            problem["current_revision"]["contract_fingerprint"]
                        ),
                        "task_class": "feature",
                        "engineering_floor": "REQUIRED",
                        "contract_capsule": contract("Revised exact Goal"),
                        "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
                        "evidence_level": "OBSERVED",
                    },
                    now=NOW,
                    authority_context="RUNTIME_EXPLICIT_USER",
                )
                with self.assertRaises(ToolFailure) as revision_fence:
                    begin_problem_run(runtime, problem_id, 2)
                self.assertEqual(
                    revision_fence.exception.code,
                    "GOAL_CONTROLLER_REVISION_REATTACH_REQUIRED",
                )

                open_problem(runtime.orchestration_ledger, "second-open")
                with self.assertRaises(ToolFailure) as ambiguous:
                    runtime.task_control(
                        {
                            "action": "continuity",
                            "continuity_action": "get",
                            "continuity_event": {},
                        }
                    )
                self.assertEqual(ambiguous.exception.code, "GOAL_IDENTITY_AMBIGUOUS")
                self.assertEqual(ambiguous.exception.details["candidate_count"], 2)
            finally:
                runtime.close()

    def test_cross_instance_exact_reattach_advances_generation_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = Runtime(root)
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                problem_id = open_problem(runtime.orchestration_ledger, "race-open")
                identity = attach(runtime, "race-controller")
                record_checkpoint(
                    runtime,
                    problem_id,
                    problem_revision=1,
                    event_id="race-material",
                    kind="PROBLEM_OPENED",
                )
                core = current_core(runtime, problem_id)
                workspace_id = str(core["workspace_id"])
                source, _workspace, runtime_fp = runtime._continuity_runtime_identity()
                acked = runtime.orchestration_ledger.controller_ack_knowledge(
                    ack_id="race-ack",
                    workspace_id=workspace_id,
                    problem_id=problem_id,
                    problem_revision=1,
                    knowledge_revision=1,
                    controller_endpoint_id=identity["controller_endpoint_id"],
                )["ack"]
                first = OrchestrationLedger(root)
                second = OrchestrationLedger(root)
                barrier = threading.Barrier(2)

                def run(ledger: OrchestrationLedger) -> dict[str, object]:
                    barrier.wait(timeout=5)
                    return ledger.controller_reattach_goal(
                        reattach_id="race-reattach",
                        workspace_id=workspace_id,
                        problem_id=problem_id,
                        problem_revision=1,
                        controller_endpoint_id=identity["controller_endpoint_id"],
                        owner_client_id=identity["owner_client_id"],
                        ack_id=acked["ack_id"],
                        ack_status=acked["status"],
                        continuity_core_fingerprint=str(core["continuity_core_fingerprint"]),
                        source_fingerprint=str(source["source_fingerprint"]),
                        runtime_behavior_fingerprint=runtime_fp,
                    )

                with ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(run, (first, second)))
                self.assertEqual(
                    sorted(item["status"] for item in results),
                    ["IDEMPOTENT", "REATTACHED"],
                )
                attachment = first.controller_goal_attachment(
                    workspace_id=workspace_id, problem_id=problem_id
                )
                assert attachment is not None
                self.assertEqual(attachment["generation"], 1)
            finally:
                runtime.close()

    def test_proving_and_accepting_reattach_preserve_state_and_single_owner(self) -> None:
        for target in ("PROVING", "ACCEPTING"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                first = Runtime(root)
                first.orchestration_ledger.migrate_problem_lineage_schema()
                problem_id = open_problem(
                    first.orchestration_ledger,
                    f"{target.lower()}-open",
                )
                attach(first, f"{target.lower()}-a")
                record_checkpoint(
                    first,
                    problem_id,
                    problem_revision=1,
                    event_id=f"{target.lower()}-checkpoint",
                    kind="PROBLEM_OPENED",
                )
                run_id = begin_problem_run(first, problem_id)
                advance_run_to_state(first, run_id, target)
                prior_lease = release_run_controller(first, run_id)
                second = Runtime(root)
                try:
                    attach(second, f"{target.lower()}-b")
                    core = current_core(second, problem_id)
                    result = reattach(
                        second,
                        problem_id,
                        reattach_id=f"{target.lower()}-reattach",
                        ack_id=f"{target.lower()}-ack",
                        core_fingerprint=str(core["continuity_core_fingerprint"]),
                        knowledge_revision=1,
                    )

                    resumed = second.orchestration_control.snapshot(run_id)
                    assert resumed is not None
                    self.assertEqual(resumed.state, target)
                    self.assertFalse(result["write_authority_granted"])
                    self.assertFalse(result["acceptance_authority_granted"])
                    self.assertEqual(
                        [
                            item["run_id"]
                            for item in result["controller_reattach"][
                                "active_run_transfers"
                            ]
                        ],
                        [run_id],
                    )
                    current_lease = second.orchestration_ledger.get_controller_lease(run_id)
                    assert current_lease is not None
                    self.assertEqual(
                        int(current_lease["fencing_token"]),
                        int(prior_lease["fencing_token"]) + 1,
                    )
                    with self.assertRaises(ToolFailure) as stale:
                        first._require_hub_controller(run_id)
                    self.assertEqual(stale.exception.code, "GOAL_CONTROLLER_FENCE_STALE")
                    self.assertTrue(second._require_hub_controller(run_id))
                finally:
                    second.close()
                    first.close()

    def test_active_job_and_terminal_result_reobserve_without_duplication(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = Runtime(root)
            runtime.orchestration_ledger.migrate_problem_lineage_schema()
            problem_id = open_problem(runtime.orchestration_ledger, "job-open")
            attach(runtime, "job-a")
            record_checkpoint(
                runtime,
                problem_id,
                problem_revision=1,
                event_id="job-checkpoint",
                kind="PROBLEM_OPENED",
            )
            run_id = begin_problem_run(runtime, problem_id)
            context = runtime.orchestration_control.snapshot(run_id)
            assert context is not None
            admission = runtime.execution_resource_governor.admit(
                command="git status --short",
                command_id="reattach-active-command",
                run_id=run_id,
                wave_id=context.wave_id,
                resource_class="LIGHT",
            )
            operation_id = "reattach-terminal-result"
            runtime.orchestration_ledger.start_background_operation(
                operation_id=operation_id,
                server_instance_id=runtime.server_instance_id,
                tool="agent_workflow",
                run_id=run_id,
                wave_id=context.wave_id,
                summary={"fixture": True},
            )
            runtime.orchestration_ledger.finish_background_operation(
                operation_id,
                status="completed",
                summary={
                    "worker_terminalized": True,
                    "result_available_in_memory": True,
                    "result_status": "completed",
                },
            )
            try:
                release_run_controller(runtime, run_id)
                attach(runtime, "job-b")
                core = current_core(runtime, problem_id)
                result = reattach(
                    runtime,
                    problem_id,
                    reattach_id="job-reattach",
                    ack_id="job-ack",
                    core_fingerprint=str(core["continuity_core_fingerprint"]),
                    knowledge_revision=1,
                )
                self.assertEqual(
                    [
                        item["run_id"]
                        for item in result["controller_reattach"]["active_run_transfers"]
                    ],
                    [run_id],
                )

                first_jobs = runtime.execution_resource_governor.snapshot(
                    limit=20,
                    reconcile=False,
                )
                second_jobs = runtime.execution_resource_governor.snapshot(
                    limit=20,
                    reconcile=False,
                )
                active_ids = [
                    item["job_id"]
                    for item in first_jobs["jobs"]
                    if item["lifecycle_state"] in {"starting", "running"}
                ]
                self.assertEqual(active_ids, [admission.job_id])
                self.assertEqual(first_jobs["jobs"], second_jobs["jobs"])
                first_result = runtime.orchestration_ledger.get_background_operation(
                    operation_id
                )
                second_result = runtime.orchestration_ledger.get_background_operation(
                    operation_id
                )
                self.assertEqual(first_result, second_result)
                assert first_result is not None
                self.assertEqual(first_result["status"], "completed")
                with (
                    runtime.orchestration_ledger._lock,
                    runtime.orchestration_ledger._connect() as connection,
                ):
                    job_count = connection.execute(
                        "SELECT COUNT(*) FROM managed_process_jobs WHERE job_id=?",
                        (admission.job_id,),
                    ).fetchone()[0]
                    result_count = connection.execute(
                        "SELECT COUNT(*) FROM background_operations WHERE operation_id=?",
                        (operation_id,),
                    ).fetchone()[0]
                self.assertEqual(job_count, 1)
                self.assertEqual(result_count, 1)
            finally:
                runtime.execution_resource_governor.complete(
                    admission.job_id,
                    lifecycle_state="exited",
                    exit_code=0,
                )
                runtime.close()

    def test_history_lost_ack_refuses_reattach_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Path(directory))
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                problem_id = open_problem(runtime.orchestration_ledger, "history-open")
                attach(runtime, "history-a")
                source, workspace_id, runtime_fp = runtime._continuity_runtime_identity()
                source_fp = str(source["source_fingerprint"])
                for revision in range(1, 35):
                    runtime.orchestration_ledger.controller_record_knowledge_checkpoint(
                        workspace_id=workspace_id,
                        problem_id=problem_id,
                        problem_revision=1,
                        material_event_kind="NEXT_CRITICAL_ACTION_CHANGED",
                        material_event_id=f"history-material-{revision}",
                        material_state_fingerprint=digest(f"history-state-{revision}"),
                        capsule_fingerprint=digest(f"history-capsule-{revision}"),
                        source_fingerprint=source_fp,
                        runtime_behavior_fingerprint=runtime_fp,
                    )
                attach(runtime, "history-b")
                core = current_core(runtime, problem_id)
                with self.assertRaises(ToolFailure) as lost:
                    reattach(
                        runtime,
                        problem_id,
                        reattach_id="history-reattach",
                        ack_id="history-ack",
                        core_fingerprint=str(core["continuity_core_fingerprint"]),
                        knowledge_revision=1,
                    )
                self.assertEqual(lost.exception.code, "CONTROLLER_REATTACH_ACK_UNSAFE")
                self.assertEqual(lost.exception.details["ack_status"], "HISTORY_LOST")
                self.assertTrue(lost.exception.details["recovery"]["history_lost"])
                self.assertIsNone(
                    runtime.orchestration_ledger.controller_goal_attachment(
                        workspace_id=workspace_id,
                        problem_id=problem_id,
                    )
                )
                with (
                    runtime.orchestration_ledger._lock,
                    runtime.orchestration_ledger._connect() as connection,
                ):
                    ack = connection.execute(
                        "SELECT status,recovery_json FROM controller_knowledge_acks WHERE ack_id=?",
                        ("history-ack",),
                    ).fetchone()
                    checkpoint_count = connection.execute(
                        "SELECT COUNT(*) FROM controller_knowledge_checkpoints WHERE problem_id=?",
                        (problem_id,),
                    ).fetchone()[0]
                assert ack is not None
                self.assertEqual(ack["status"], "HISTORY_LOST")
                self.assertTrue(json.loads(ack["recovery_json"])["history_lost"])
                self.assertEqual(checkpoint_count, 34)
            finally:
                runtime.close()

    def test_workspace_mismatch_keeps_ack_separate_but_grants_no_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(Path(directory))
            try:
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                problem_id = open_problem(runtime.orchestration_ledger, "workspace-open")
                attach(runtime, "workspace-a")
                record_checkpoint(
                    runtime,
                    problem_id,
                    problem_revision=1,
                    event_id="workspace-checkpoint",
                    kind="PROBLEM_OPENED",
                )
                run_id = runtime.orchestration_ledger.create_run(
                    objective="Wrong workspace fixture",
                    metadata={
                        "problem_resolution": {
                            "work_origin": "problem",
                            "problem_id": problem_id,
                            "problem_revision": 1,
                        },
                        "workspace_identity": {"workspace_id": "workspace-other"},
                    },
                )
                attach(runtime, "workspace-b")
                core = current_core(runtime, problem_id)
                with self.assertRaises(ToolFailure) as mismatch:
                    reattach(
                        runtime,
                        problem_id,
                        reattach_id="workspace-reattach",
                        ack_id="workspace-ack",
                        core_fingerprint=str(core["continuity_core_fingerprint"]),
                        knowledge_revision=1,
                    )
                self.assertEqual(mismatch.exception.code, "WORKSPACE_SCOPE_MISMATCH")
                self.assertIsNone(runtime.orchestration_ledger.get_controller_lease(run_id))
                self.assertIsNone(
                    runtime.orchestration_ledger.controller_goal_attachment(
                        workspace_id=str(core["workspace_id"]),
                        problem_id=problem_id,
                    )
                )
                with (
                    runtime.orchestration_ledger._lock,
                    runtime.orchestration_ledger._connect() as connection,
                ):
                    ack = connection.execute(
                        "SELECT status FROM controller_knowledge_acks WHERE ack_id=?",
                        ("workspace-ack",),
                    ).fetchone()
                    checkpoint_count = connection.execute(
                        "SELECT COUNT(*) FROM controller_knowledge_checkpoints WHERE problem_id=?",
                        (problem_id,),
                    ).fetchone()[0]
                assert ack is not None
                self.assertEqual(ack["status"], "CURRENT")
                self.assertEqual(checkpoint_count, 1)
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
