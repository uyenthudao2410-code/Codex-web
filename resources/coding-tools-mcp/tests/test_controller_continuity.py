from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.controller_continuity import (
    CONTINUITY_CORE_OUTER_BUDGET_BYTES,
    ControllerContinuityError,
    build_continuity_core,
    validate_continuity_core_currentness,
)
from coding_tools_mcp.context_observability import (
    context_observability_projection,
    controller_knowledge_for_run,
)
from coding_tools_mcp.errors import JsonRpcError
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.problem_lineage import PROBLEM_SCHEMA_VERSION
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.tool_schema import input_schemas, validate_arguments


NOW = "2026-09-01T00:00:00+00:00"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def contract(criteria: int = 2, *, large: bool = False) -> dict[str, object]:
    criterion_items = []
    for index in range(criteria):
        suffix = ("-" + "i" * 105) if large else ""
        criterion_items.append(
            {
                "criterion_id": f"criterion-{index:03d}{suffix}",
                "summary": (f"Criterion {index} " + "s" * 780) if large else f"Criterion {index} passes",
            }
        )
    return {
        "objective_summary": "O" * (20_000 if large else 40),
        "acceptance_criteria": criterion_items,
        "protected_invariants": ["No public tool growth", "No authority grant"],
        "constraints": ["No transcript persistence"],
        "unresolved_conditions": [],
    }


def open_problem(ledger: OrchestrationLedger, identifier: str = "open-continuity") -> str:
    opened = ledger.problem_record_event(
        {
            "operation": "open",
            "event_id": identifier,
            "task_id": "task-continuity",
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


def attach_chatweb(runtime: Runtime) -> None:
    runtime.request_context.hub_client = {
        "client_id": "continuity-chatweb",
        "client_type": "chatweb",
        "role": "controller",
        "session_instance": "continuity-session",
        "execution_context_id": "continuity-context",
        "capabilities": {},
    }
    runtime._touch_hub_client(runtime.request_context.hub_client)


class ControllerContinuityLedgerTests(unittest.TestCase):
    def test_domain_schema_does_not_take_over_global_prl_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = OrchestrationLedger(Path(directory))
            connection = sqlite3.connect(ledger.path)
            try:
                self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 9)
            finally:
                connection.close()
            self.assertEqual(ledger.controller_continuity_schema_version(), 1)
            ledger.migrate_problem_lineage_schema()
            connection = sqlite3.connect(ledger.path)
            try:
                self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], PROBLEM_SCHEMA_VERSION)
                self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
            finally:
                connection.close()
            self.assertEqual(ledger.controller_continuity_schema_version(), 1)

    def test_policy_checkpoint_idempotency_conflict_and_reopen_durability(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = OrchestrationLedger(root)
            ledger.migrate_problem_lineage_schema()
            problem_id = open_problem(ledger)
            common = {
                "workspace_id": "workspace-continuity",
                "problem_id": problem_id,
                "problem_revision": 1,
                "capsule_fingerprint": digest("capsule-1"),
                "source_fingerprint": digest("source-1"),
                "runtime_behavior_fingerprint": digest("runtime-1"),
                "created_at": NOW,
            }
            self.assertEqual(ledger.controller_knowledge_policy("REPOSITORY_READ"), "NO_ADVANCE")
            self.assertEqual(ledger.controller_knowledge_policy("CONTINUITY_ACK"), "RECOVERY_ONLY")
            self.assertEqual(ledger.controller_knowledge_policy("not-classified"), "CONSERVATIVE_UNKNOWN")
            read = ledger.controller_record_knowledge_checkpoint(
                **common,
                material_event_kind="REPOSITORY_READ",
                material_event_id="read-1",
                material_state_fingerprint=digest("state-1"),
            )
            self.assertEqual(read["status"], "NO_ADVANCE")
            self.assertIsNone(read["checkpoint"])
            first = ledger.controller_record_knowledge_checkpoint(
                **common,
                material_event_kind="PROBLEM_OPENED",
                material_event_id="material-1",
                material_state_fingerprint=digest("state-1"),
            )
            self.assertEqual(first["status"], "ADVANCED")
            self.assertEqual(first["checkpoint"]["knowledge_revision"], 1)
            replay = ledger.controller_record_knowledge_checkpoint(
                **common,
                material_event_kind="PROBLEM_OPENED",
                material_event_id="material-1",
                material_state_fingerprint=digest("state-1"),
            )
            self.assertEqual(replay["status"], "IDEMPOTENT")
            self.assertTrue(replay["idempotent"])
            unchanged = ledger.controller_record_knowledge_checkpoint(
                **common,
                material_event_kind="CRITERION_COVERAGE_CHANGED",
                material_event_id="material-2",
                material_state_fingerprint=digest("state-1"),
            )
            self.assertEqual(unchanged["status"], "NO_ADVANCE_UNCHANGED_STATE")
            with self.assertRaises(ControllerContinuityError) as conflict:
                ledger.controller_record_knowledge_checkpoint(
                    **common,
                    material_event_kind="PROBLEM_OPENED",
                    material_event_id="material-1",
                    material_state_fingerprint=digest("state-conflict"),
                )
            self.assertEqual(conflict.exception.code, "MATERIAL_EVENT_STATE_CONFLICT")
            second = ledger.controller_record_knowledge_checkpoint(
                **{**common, "capsule_fingerprint": digest("capsule-2")},
                material_event_kind="CRITERION_COVERAGE_CHANGED",
                material_event_id="material-3",
                material_state_fingerprint=digest("state-2"),
            )
            self.assertEqual(second["checkpoint"]["knowledge_revision"], 2)
            reopened = OrchestrationLedger(root)
            self.assertEqual(
                reopened.controller_current_knowledge(
                    workspace_id="workspace-continuity", problem_id=problem_id
                )["knowledge_revision"],
                2,
            )

    def test_exact_host_observation_records_current_knowledge_without_replay_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = OrchestrationLedger(Path(directory))
            ledger.migrate_problem_lineage_schema()
            problem_id = open_problem(ledger, "open-host-knowledge")
            run_id = ledger.create_run(
                objective="observe exact controller knowledge",
                metadata={
                    "workspace_identity": {"workspace_id": "workspace-host-knowledge"},
                    "problem_resolution": {
                        "work_origin": "problem",
                        "problem_id": problem_id,
                        "problem_revision": 1,
                    },
                },
            )
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            common = {
                "workspace_id": "workspace-host-knowledge",
                "problem_id": problem_id,
                "problem_revision": 1,
                "source_fingerprint": digest("source-host"),
                "runtime_behavior_fingerprint": digest("runtime-host"),
                "created_at": NOW,
            }
            ledger.controller_record_knowledge_checkpoint(
                **common,
                material_event_kind="PROBLEM_OPENED",
                material_event_id="host-material-1",
                material_state_fingerprint=digest("host-state-1"),
                capsule_fingerprint=digest("host-capsule-1"),
            )
            span = {
                "span_id": "host-span-knowledge",
                "stage": "assistant_response_visible",
                "source": "electron_chatgpt_dom",
                "measurement": "observed_user_visible_to_first_assistant_visible",
                "clock_domain": "electron-navigation-1",
                "start_ms": 10.0,
                "end_ms": 25.0,
                "observer_plane": "electron_chatgpt_dom",
                "turn_id": "turn-host-knowledge",
                "trace_id": "trace-host-knowledge",
            }
            recorded = ledger.record_observation_span(run_id=run_id, wave_id=wave_id, span=span)
            watermark = recorded["controller_knowledge_at_observation"]
            self.assertEqual(watermark["status"], "observed")
            self.assertEqual(watermark["linkage"], "exact_run_problem_binding")
            self.assertEqual(watermark["problem_id"], problem_id)
            self.assertEqual(watermark["problem_revision"], 1)
            self.assertEqual(watermark["knowledge_revision"], 1)

            ledger.controller_record_knowledge_checkpoint(
                **common,
                material_event_kind="CRITERION_COVERAGE_CHANGED",
                material_event_id="host-material-2",
                material_state_fingerprint=digest("host-state-2"),
                capsule_fingerprint=digest("host-capsule-2"),
            )
            replay = ledger.record_observation_span(run_id=run_id, wave_id=wave_id, span=span)
            self.assertFalse(replay["recorded"])
            self.assertEqual(replay["controller_knowledge_at_observation"]["knowledge_revision"], 1)
            knowledge = controller_knowledge_for_run(ledger, run_id)
            projection = context_observability_projection(
                run_id=run_id,
                clients=[{
                    "client_type": "chatweb",
                    "role": "controller",
                    "session_instance": "opaque-transport-session",
                }],
                direct_usage={
                    "controller": {
                        "turn_id": "turn-host-knowledge",
                        "trace_id": "trace-host-knowledge",
                        "measurement": {"usage": "measured"},
                        "provenance": {"usage": "client_reported"},
                    }
                },
                capsule={"conversation_epoch": 2, "bytes": 512},
                events=[{
                    "event_type": "observation_span_recorded",
                    "payload": recorded,
                }],
                counts={"events": 3},
                controller_knowledge=knowledge,
            )
            matrix = projection["capability_matrix"]
            self.assertEqual(matrix["controller_knowledge_revision"]["status"], "supported")
            self.assertEqual(matrix["controller_knowledge_revision"]["observation"], "observed")
            self.assertEqual(matrix["controller_knowledge_revision"]["knowledge_revision"], 2)
            self.assertEqual(matrix["exact_session_identity"]["status"], "partial")
            self.assertEqual(matrix["exact_context_pressure"]["status"], "unobserved")
            self.assertEqual(
                projection["material_host_observation_linkage"]["recent_knowledge_linked_span_count"],
                1,
            )

    def test_ack_statuses_are_typed_idempotent_and_never_advance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = OrchestrationLedger(Path(directory))
            ledger.migrate_problem_lineage_schema()
            problem_id = open_problem(ledger, "open-ack")
            for number, event_kind in enumerate(
                ("PROBLEM_OPENED", "CRITERION_COVERAGE_CHANGED", "NEXT_CRITICAL_ACTION_CHANGED"),
                start=1,
            ):
                ledger.controller_record_knowledge_checkpoint(
                    workspace_id="workspace-ack",
                    problem_id=problem_id,
                    problem_revision=1,
                    material_event_kind=event_kind,
                    material_event_id=f"event-{number}",
                    material_state_fingerprint=digest(f"state-{number}"),
                    capsule_fingerprint=digest(f"capsule-{number}"),
                    source_fingerprint=digest("source"),
                    runtime_behavior_fingerprint=digest("runtime"),
                    created_at=NOW,
                )

            def ack(identifier: str, revision: int | None, *, problem_revision: int = 1, limit: int = 32):
                return ledger.controller_ack_knowledge(
                    ack_id=identifier,
                    workspace_id="workspace-ack",
                    problem_id=problem_id,
                    problem_revision=problem_revision,
                    knowledge_revision=revision,
                    controller_endpoint_id="controller-endpoint",
                    recovery_limit=limit,
                    created_at=NOW,
                )

            current = ack("ack-current", 3)
            self.assertEqual(current["ack"]["status"], "CURRENT")
            behind = ack("ack-behind", 2)
            self.assertEqual(behind["ack"]["status"], "BEHIND")
            self.assertEqual([item["knowledge_revision"] for item in behind["ack"]["recovery"]["delta"]], [3])
            self.assertEqual(ack("ack-missing", None)["ack"]["status"], "MISSING")
            self.assertEqual(ack("ack-invalid", 1, problem_revision=2)["ack"]["status"], "INVALID")
            self.assertEqual(ack("ack-future", 4)["ack"]["status"], "FUTURE")
            history_lost = ack("ack-history", 1, limit=1)
            self.assertEqual(history_lost["ack"]["status"], "HISTORY_LOST")
            self.assertTrue(history_lost["ack"]["recovery"]["history_lost"])
            replay = ack("ack-current", 3)
            self.assertTrue(replay["idempotent"])
            with self.assertRaises(ControllerContinuityError) as conflict:
                ack("ack-current", 2)
            self.assertEqual(conflict.exception.code, "CONTROLLER_ACK_IDENTITY_CONFLICT")
            self.assertEqual(
                ledger.controller_current_knowledge(
                    workspace_id="workspace-ack", problem_id=problem_id
                )["knowledge_revision"],
                3,
            )

    def test_cross_instance_exact_replay_advances_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_ledger = OrchestrationLedger(root)
            first_ledger.migrate_problem_lineage_schema()
            problem_id = open_problem(first_ledger, "open-concurrent")
            second_ledger = OrchestrationLedger(root)
            barrier = threading.Barrier(2)

            def record(ledger: OrchestrationLedger) -> dict[str, object]:
                barrier.wait(timeout=5)
                return ledger.controller_record_knowledge_checkpoint(
                    workspace_id="workspace-concurrent",
                    problem_id=problem_id,
                    problem_revision=1,
                    material_event_kind="PROBLEM_OPENED",
                    material_event_id="concurrent-event",
                    material_state_fingerprint=digest("concurrent-state"),
                    capsule_fingerprint=digest("concurrent-capsule"),
                    source_fingerprint=digest("concurrent-source"),
                    runtime_behavior_fingerprint=digest("concurrent-runtime"),
                    created_at=NOW,
                )

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(record, (first_ledger, second_ledger)))
            self.assertEqual(sorted(item["status"] for item in results), ["ADVANCED", "IDEMPOTENT"])
            self.assertEqual(
                first_ledger.controller_current_knowledge(
                    workspace_id="workspace-concurrent", problem_id=problem_id
                )["knowledge_revision"],
                1,
            )


class ContinuityCoreTests(unittest.TestCase):
    def _oversized_inputs(self) -> dict[str, object]:
        capsule = contract(100, large=True)
        criteria_json = json.dumps(capsule, sort_keys=True, separators=(",", ":"))
        contract_fp = hashlib.sha256(criteria_json.encode("utf-8")).hexdigest()
        criteria_only = json.dumps(capsule["acceptance_criteria"], sort_keys=True, separators=(",", ":"))
        criteria_fp = hashlib.sha256(criteria_only.encode("utf-8")).hexdigest()
        return {
            "workspace_id": "workspace-core",
            "problem_projection": {
                "thread": {
                    "problem_id": "problem-core",
                    "current_revision": 1,
                    "resolution_state": "OPEN",
                },
                "current_revision": {
                    "contract_fingerprint": contract_fp,
                    "criteria_fingerprint": criteria_fp,
                    "capsule": capsule,
                },
            },
            "knowledge_checkpoint": {
                "knowledge_revision": 2,
                "material_state_fingerprint": digest("material"),
                "capsule_fingerprint": digest("capsule"),
            },
            "source_identity": {
                "base_head": digest("head"),
                "worktree_fp": digest("worktree"),
                "source_fingerprint": digest("source"),
            },
            "runtime_behavior_fingerprint": digest("runtime"),
            "goal_projection": {
                "resolution_status": "ENGINEERING_COMPLETE_AWAITING_RECONCILIATION",
                "next_action": "RECONCILE_PROVISIONAL_RESOLUTION",
                "next_critical_gap": "Independent outcome remains unresolved",
                "criterion_coverage": {},
            },
            "execution_attempts": [
                {
                    "run_id": f"run-{index}-" + "r" * 100,
                    "wave_id": f"wave-{index}-" + "w" * 100,
                    "status": "accepted",
                    "checkpoint_id": f"checkpoint-{index}",
                }
                for index in range(50)
            ],
            "correlation_bindings": [
                {
                    "run_id": f"run-{index}",
                    "turn_id": f"turn-{index}-" + "t" * 100,
                    "trace_id": f"trace-{index}-" + "x" * 100,
                    "relation": "EXACT",
                }
                for index in range(20)
            ],
        }

    def test_core_is_deterministic_bounded_and_omits_in_frozen_order(self) -> None:
        inputs = self._oversized_inputs()
        first = build_continuity_core(**inputs)
        second = build_continuity_core(**inputs)
        self.assertEqual(first, second)
        encoded = json.dumps(first, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.assertLessEqual(len(encoded), CONTINUITY_CORE_OUTER_BUDGET_BYTES)
        self.assertEqual(first["serialized_bytes"], len(encoded))
        self.assertEqual(
            [item["reason"] for item in first["omissions"]],
            [
                "CORRELATION_OMITTED_FOR_BUDGET",
                "EXECUTION_ATTEMPTS_OMITTED_FOR_BUDGET",
                "CRITERION_DETAILS_OMITTED_FOR_BUDGET",
                "OBJECTIVE_SUMMARY_OMITTED_FOR_BUDGET",
                "REMAINING_CRITERIA_TRUNCATED_FOR_BUDGET",
            ],
        )
        self.assertTrue(first["exact_read_refresh_required"])
        self.assertFalse(first["enrichment_included"])
        self.assertEqual(
            first["authority"],
            {
                "mutation_authority_granted": False,
                "acceptance_authority_granted": False,
                "problem_revision_authority_granted": False,
            },
        )
        lowered = encoded.decode("utf-8").lower()
        for forbidden in ("transcript", "chain_of_thought", "private_reasoning", "stdout", "stderr", "raw_prompt"):
            self.assertNotIn(forbidden, lowered)
        self.assertEqual(
            validate_continuity_core_currentness(
                first,
                current_source_fingerprint=digest("source"),
                current_runtime_behavior_fingerprint=digest("runtime"),
            )["status"],
            "CURRENT",
        )

    def test_source_and_runtime_currentness_fail_closed(self) -> None:
        core = build_continuity_core(**self._oversized_inputs())
        with self.assertRaises(ControllerContinuityError) as source:
            validate_continuity_core_currentness(
                core,
                current_source_fingerprint=digest("different-source"),
                current_runtime_behavior_fingerprint=digest("runtime"),
            )
        self.assertEqual(source.exception.code, "CONTINUITY_SOURCE_STALE")
        with self.assertRaises(ControllerContinuityError) as runtime:
            validate_continuity_core_currentness(
                core,
                current_source_fingerprint=digest("source"),
                current_runtime_behavior_fingerprint=digest("different-runtime"),
            )
        self.assertEqual(runtime.exception.code, "CONTINUITY_RUNTIME_STALE")
        self.assertEqual(
            validate_continuity_core_currentness(
                core,
                current_source_fingerprint=None,
                current_runtime_behavior_fingerprint=None,
            )["status"],
            "UNKNOWN",
        )


class ControllerContinuitySurfaceTests(unittest.TestCase):
    def test_task_control_schema_is_strict_and_public_tool_count_is_unchanged(self) -> None:
        schemas = input_schemas()
        self.assertIn("continuity", schemas["task_control"]["properties"]["action"]["enum"])
        validate_arguments(
            "task_control",
            {
                "action": "continuity",
                "continuity_action": "get",
                "continuity_event": {"problem_id": "problem-1", "problem_revision": 1},
            },
        )
        with self.assertRaises(JsonRpcError):
            validate_arguments(
                "task_control",
                {
                    "action": "continuity",
                    "continuity_action": "get",
                    "continuity_event": {
                        "problem_id": "problem-1",
                        "problem_revision": 1,
                        "source_fingerprint": digest("caller-forgery"),
                    },
                },
            )

    def test_runtime_checkpoint_get_and_ack_are_bounded_and_non_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(directory))
            try:
                self.assertEqual(runtime.tool_contract["tool_count"], 8)
                runtime.orchestration_ledger.migrate_problem_lineage_schema()
                problem_id = open_problem(runtime.orchestration_ledger, "runtime-open")
                attach_chatweb(runtime)
                checkpoint = runtime.task_control(
                    {
                        "action": "continuity",
                        "continuity_action": "checkpoint",
                        "continuity_event": {
                            "problem_id": problem_id,
                            "problem_revision": 1,
                            "material_event_kind": "PROBLEM_OPENED",
                            "material_event_id": "runtime-material-1",
                        },
                    }
                )
                self.assertEqual(checkpoint["knowledge_checkpoint"]["status"], "ADVANCED")
                self.assertFalse(checkpoint["authority_granted"])
                goal = runtime.task_control(
                    {
                        "action": "goal",
                        "goal_action": "get",
                        "goal_event": {"problem_id": problem_id, "problem_revision": 1},
                    }
                )["goal_pursuit"]
                self.assertEqual(goal["knowledge_revision"], 1)
                self.assertEqual(
                    checkpoint["continuity_core"]["resolution_status"],
                    goal["resolution_status"],
                )
                self.assertEqual(checkpoint["continuity_core"]["next_action"], goal["next_action"])
                current = runtime.task_control(
                    {
                        "action": "continuity",
                        "continuity_action": "get",
                        "continuity_event": {"problem_id": problem_id, "problem_revision": 1},
                    }
                )
                self.assertEqual(current["currentness"]["status"], "CURRENT")
                acknowledged = runtime.task_control(
                    {
                        "action": "continuity",
                        "continuity_action": "ack",
                        "continuity_event": {
                            "problem_id": problem_id,
                            "problem_revision": 1,
                            "ack_id": "runtime-ack-1",
                            "knowledge_revision": 1,
                        },
                    }
                )
                self.assertEqual(acknowledged["knowledge_ack"]["ack"]["status"], "CURRENT")
                self.assertFalse(acknowledged["authority_granted"])
                self.assertEqual(
                    runtime.orchestration_ledger.goal_pursuit_projection(
                        problem_id=problem_id, problem_revision=1
                    )["knowledge_revision"],
                    1,
                )
                self.assertLessEqual(
                    acknowledged["continuity_core"]["serialized_bytes"],
                    CONTINUITY_CORE_OUTER_BUDGET_BYTES,
                )
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
