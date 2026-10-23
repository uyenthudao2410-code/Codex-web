from __future__ import annotations

"""W4 wiring tests: driver -> send checkpoint + Goal completion signal.

Covers the two seams left open by the W4 logic port
(``continuation_send_state``):

1. When a continuation dispatch outcome is unknown (``DISPATCH_UNKNOWN`` /
   ``PROOF_OUTCOME_UNKNOWN``), the driver persists a durable
   ``possibly_sent`` send checkpoint on the RUN's handoff capsule so the
   next resume receives ``RECONCILE_BEFORE_REPLAY`` instead of risking a
   replay.
2. The episode machinery in the driver consumes ``goal_completion_signal``:
   a complete signal stops any further dispatch, and ``may_continue=False``
   (episode budgets exhausted) stops with the signal's exact reason.
"""

import hashlib
import json
import os
import shutil
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.continuation_send_state import (
    SEND_STATE_CONFIRMED,
    SEND_STATE_POSSIBLY_SENT,
    goal_completion_signal,
    handoff_resume_directive,
)
from coding_tools_mcp.run_continuation import (
    bind_run_continuation_consent,
    build_goal_continuation_policy,
    build_run_continuation_policy,
    continuation_consent_descriptor,
)
from coding_tools_mcp.server import Runtime


@contextmanager
def _temporary_test_directory():
    directory = tempfile.mkdtemp(prefix="continuation-wiring-test-")
    try:
        yield directory
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _check_definition(check_id: str = "unit") -> dict[str, object]:
    definition = {
        "check_id": check_id,
        "argv": ["python", "-m", "pytest", "tests/test_target.py"],
        "cwd": "resources/coding-tools-mcp",
        "environment_hash": "a" * 64,
    }
    return {**definition, "definition_hash": _digest(definition)}


def _grant_request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "action": "grant",
        "read_paths": ["resources/coding-tools-mcp/coding_tools_mcp/target.py"],
        "write_paths": ["resources/coding-tools-mcp/coding_tools_mcp/target.py"],
        "protected_paths": ["resources/coding-tools-mcp/coding_tools_mcp/server.py"],
        "approved_checks": [_check_definition()],
        "max_duration_seconds": 120,
        "max_decision_turns": 4,
        "max_patch_attempts": 2,
    }
    request.update(overrides)
    return request


def _run_policy(runtime: Runtime, run_id: str) -> dict[str, object]:
    behavior = runtime._loaded_behavior_identity()
    return build_run_continuation_policy(
        _grant_request(),
        run_id=run_id,
        workspace_id="workspace-test",
        problem_id="problem-test",
        problem_revision=1,
        contract_fingerprint="b" * 64,
        tool_contract_sha256=str(runtime.tool_contract["sha256"]),
        runtime_behavior_fingerprint=str(behavior["fingerprint"]),
        activation_epoch_id="epoch-test",
        activation_admission="open",
        issuer_client_id="chatweb-test",
    )


def _goal_policy(runtime: Runtime, origin_run_id: str, **overrides: object) -> dict[str, object]:
    behavior = runtime._loaded_behavior_identity()
    goal = build_goal_continuation_policy(
        _grant_request(**overrides),
        origin_run_id=origin_run_id,
        workspace_id="workspace-test",
        problem_id="problem-test",
        problem_revision=1,
        contract_fingerprint="b" * 64,
        tool_contract_sha256=str(runtime.tool_contract["sha256"]),
        runtime_behavior_fingerprint=str(behavior["fingerprint"]),
        activation_epoch_id="epoch-test",
        activation_admission="open",
        issuer_client_id="chatweb-test",
        controller_generation=7,
        controller_endpoint_id="endpoint-test",
        controller_owner_client_id="chatweb-test",
        wave_id="wave-origin",
    )
    descriptor = continuation_consent_descriptor(goal)
    return bind_run_continuation_consent(
        goal,
        {
            "receipt_id": "chatweb-continuation-consent:wiring",
            "turn_id": "chatweb-turn:wiring",
            "trace_id": "trace-wiring",
            "descriptor": descriptor,
        },
    )


def _problem_bound_run(runtime: Runtime, *, objective: str) -> str:
    ledger = runtime.orchestration_ledger
    run_id = ledger.create_run(
        objective=objective,
        metadata={
            "problem_resolution": {
                "work_origin": "problem",
                "problem_id": "problem-test",
                "problem_revision": 1,
            },
            "workspace_identity": {"workspace_id": "workspace-test"},
        },
    )
    ledger.create_wave(run_id, execution_mode="deep_single_lane")
    return run_id


_GOAL_ATTACHMENT = {
    "workspace_id": "workspace-test",
    "problem_id": "problem-test",
    "problem_revision": 1,
    "generation": 7,
    "owner_client_id": "chatweb-test",
    "controller_endpoint_id": "endpoint-test",
}


class DispatchUnknownCheckpointTests(unittest.TestCase):
    def _dispatched_runtime(self, runtime: Runtime) -> str:
        """Issue + claim + reserve + dispatch one run continuation action."""
        ledger = runtime.orchestration_ledger
        run_id = ledger.create_run(objective="continuation dispatch unknown wiring")
        ledger.create_wave(run_id, execution_mode="deep_single_lane")
        ledger.issue_run_continuation(
            run_id=run_id, policy=_run_policy(runtime, run_id), issuer_receipt_sha256="e" * 64,
        )
        claim = ledger.claim_run_continuation(
            run_id=run_id,
            runtime_instance_id=runtime._run_continuation_runtime_instance_id(),
            expected_generation=0,
        )
        generation = int(claim["continuation"]["driver_generation"])
        reserved = ledger.reserve_run_continuation_action(
            run_id=run_id,
            driver_generation=generation,
            runtime_instance_id=runtime._run_continuation_runtime_instance_id(),
            action_kind="proposal",
            request_hash="9" * 64,
            evidence_hash="a" * 64,
            evidence_paths=[],
            expected_action_seq=1,
        )
        ledger.set_run_continuation_dispatch(
            run_id=run_id,
            driver_generation=generation,
            runtime_instance_id=runtime._run_continuation_runtime_instance_id(),
            action_id=str(reserved["action_id"]),
            lane_id="lane-test",
            thread_id="thread-test",
            turn_id="turn-test",
        )
        return run_id

    def test_dispatch_unknown_records_possibly_sent_checkpoint(self) -> None:
        with _temporary_test_directory() as directory, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(directory))
            try:
                run_id = self._dispatched_runtime(runtime)
                with (
                    patch.object(
                        runtime,
                        "activation_admission_snapshot",
                        return_value={"admission": "open", "activation_epoch_id": "epoch-current"},
                    ),
                    patch.object(runtime._codex_bridge, "owns_thread", return_value=False),
                ):
                    observed = runtime._run_continuation_observe_driver(run_id=run_id)
                self.assertEqual(observed["status"], "DISPATCH_UNKNOWN")
                self.assertEqual(
                    observed["send_checkpoint"],
                    {"state": SEND_STATE_POSSIBLY_SENT, "recorded": True},
                )
                capsule = runtime.orchestration_ledger.latest_handoff_capsule(run_id=run_id)
                self.assertIsNotNone(capsule)
                assert capsule is not None
                checkpoint = capsule["payload"]["send_checkpoint"]
                self.assertEqual(checkpoint, {"state": SEND_STATE_POSSIBLY_SENT, "message_id": ""})
                marker = capsule["payload"]["continuation_dispatch_unknown"]
                self.assertEqual(marker["reason"], "bridge_turn_not_owned_after_restart")
                self.assertTrue(marker["action_id"])
                # The resume side of the contract: the next conversation is
                # told to reconcile, never to replay.
                directive = handoff_resume_directive(checkpoint)
                self.assertEqual(directive["directive"], "RECONCILE_BEFORE_REPLAY")
                self.assertFalse(directive["may_replay"])
                self.assertTrue(directive["requires_reconciliation"])
            finally:
                runtime.close()

    def test_checkpoint_never_downgrades_a_confirmed_send(self) -> None:
        with _temporary_test_directory() as directory, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(directory))
            try:
                run_id = self._dispatched_runtime(runtime)
                runtime.orchestration_ledger.record_handoff_capsule(
                    run_id=run_id,
                    payload={
                        "goal": "already sent and confirmed",
                        "send_checkpoint": {"state": SEND_STATE_CONFIRMED, "message_id": "m-1"},
                    },
                )
                with (
                    patch.object(
                        runtime,
                        "activation_admission_snapshot",
                        return_value={"admission": "open", "activation_epoch_id": "epoch-current"},
                    ),
                    patch.object(runtime._codex_bridge, "owns_thread", return_value=False),
                ):
                    observed = runtime._run_continuation_observe_driver(run_id=run_id)
                self.assertEqual(observed["status"], "DISPATCH_UNKNOWN")
                # Monotonicity: a confirmed effect is terminal; the unknown
                # dispatch of a later action must not rewrite it.
                self.assertEqual(
                    observed["send_checkpoint"],
                    {"state": SEND_STATE_POSSIBLY_SENT, "recorded": False},
                )
                capsule = runtime.orchestration_ledger.latest_handoff_capsule(run_id=run_id)
                self.assertIsNotNone(capsule)
                assert capsule is not None
                self.assertEqual(
                    capsule["payload"]["send_checkpoint"],
                    {"state": SEND_STATE_CONFIRMED, "message_id": "m-1"},
                )
            finally:
                runtime.close()


class EpisodeGoalSignalGateTests(unittest.TestCase):
    def _episode_child_runtime(
        self, runtime: Runtime, **grant_overrides: object
    ) -> tuple[str, int, str]:
        """Materialize one Goal-episode child RUN with a dispatched action."""
        ledger = runtime.orchestration_ledger
        origin_run = _problem_bound_run(runtime, objective="wiring goal origin")
        child_run = _problem_bound_run(runtime, objective="wiring goal child")
        parent_policy = _goal_policy(runtime, origin_run, **grant_overrides)
        # Runtime.orchestration_ledger is a compatibility view delegating to
        # the primary ledger; internal self-calls land on the primary, so the
        # precondition stub must be installed there.
        with patch.object(
            ledger._primary, "_controller_assert_goal_run_precondition", return_value=_GOAL_ATTACHMENT
        ):
            issued = ledger.issue_goal_continuation(
                policy=parent_policy, issuer_receipt_sha256="e" * 64
            )
            episode_id = str(issued["goal_continuation"]["episode_id"])
            ledger.materialize_goal_continuation(
                run_id=child_run, episode_id=episode_id, grant_wave_id="wave-child"
            )
        claim = ledger.claim_run_continuation(
            run_id=child_run,
            runtime_instance_id=runtime._run_continuation_runtime_instance_id(),
            expected_generation=0,
        )
        generation = int(claim["continuation"]["driver_generation"])
        reserved = ledger.reserve_run_continuation_action(
            run_id=child_run,
            driver_generation=generation,
            runtime_instance_id=runtime._run_continuation_runtime_instance_id(),
            action_kind="proposal",
            request_hash="9" * 64,
            evidence_hash="a" * 64,
            evidence_paths=[],
            expected_action_seq=1,
        )
        action_id = str(reserved["action_id"])
        ledger.set_run_continuation_dispatch(
            run_id=child_run,
            driver_generation=generation,
            runtime_instance_id=runtime._run_continuation_runtime_instance_id(),
            action_id=action_id,
            lane_id="lane-test",
            thread_id="thread-test",
            turn_id="turn-one",
        )
        return child_run, generation, action_id

    def _observe(self, runtime: Runtime, run_id: str, proposal: dict[str, object], signal: dict):
        observation = {
            "terminal": True,
            "status": "completed",
            "agent_text": json.dumps(proposal),
            "next_cursor": 3,
        }
        summary = {"completion": {"criterion_signal": signal}}
        with (
            patch.object(
                runtime,
                "activation_admission_snapshot",
                return_value={"admission": "open", "activation_epoch_id": "epoch-current"},
            ),
            patch.object(runtime._codex_bridge, "owns_thread", return_value=True),
            patch.object(runtime._codex_bridge, "observe", return_value=observation),
            patch.object(runtime._codex_bridge, "continue_thread") as continued,
            patch.object(
                runtime.orchestration_ledger,
                "goal_pursuit_live_summary",
                return_value=summary,
            ),
        ):
            result = runtime._run_continuation_observe_driver(run_id=run_id)
        return result, continued

    def test_complete_signal_stops_further_dispatch(self) -> None:
        with _temporary_test_directory() as directory, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(directory))
            try:
                child_run, _generation, _action_id = self._episode_child_runtime(runtime)
                signal = goal_completion_signal(
                    {"c1": {"status": "PROVEN"}, "c2": {"status": "SATISFIED_NON_CODE"}}
                )
                result, continued = self._observe(
                    runtime,
                    child_run,
                    {
                        "kind": "READ",
                        "reason": "Gather more evidence before patching.",
                        "evidence_hash": "a" * 64,
                        "read_requests": [
                            {"path": "resources/coding-tools-mcp/coding_tools_mcp/target.py"}
                        ],
                    },
                    signal,
                )
                self.assertEqual(result["status"], "GOAL_COMPLETE")
                self.assertEqual(result["reason"], "CRITERIA_COMPLETE")
                self.assertTrue(result["goal_signal"]["complete"])
                self.assertFalse(result["continue_observing"])
                # The core rule: a complete Goal gets no further dispatch.
                continued.assert_not_called()
                raw = runtime.orchestration_ledger._run_continuation_get_raw(child_run)
                self.assertIsNotNone(raw)
                assert raw is not None
                self.assertEqual(raw["pending_action_id"], "")
                self.assertFalse(raw["enabled"])
            finally:
                runtime.close()

    def test_exhausted_episode_budget_stops_with_signal_reason(self) -> None:
        with _temporary_test_directory() as directory, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(directory))
            try:
                # One decision turn total: reserving the dispatched action
                # spends it, so the episode budget is exhausted by the time
                # the model asks for a repair continuation.
                child_run, _generation, _action_id = self._episode_child_runtime(
                    runtime, max_decision_turns=1
                )
                signal = goal_completion_signal(
                    {"c1": {"status": "PROVEN"}, "c2": {"status": "UNRESOLVED"}}
                )
                result, continued = self._observe(
                    runtime,
                    child_run,
                    {
                        "kind": "BLOCKED",
                        "reason": "The model cannot proceed without help.",
                        "evidence_hash": "a" * 64,
                    },
                    signal,
                )
                self.assertEqual(result["status"], "PAUSED")
                self.assertEqual(result["reason"], "DECISION_TURNS_EXHAUSTED")
                self.assertFalse(result["goal_signal"]["may_continue"])
                self.assertIn(
                    "DECISION_TURNS_EXHAUSTED", result["goal_signal"]["incomplete_reasons"]
                )
                self.assertFalse(result["continue_observing"])
                continued.assert_not_called()
                raw = runtime.orchestration_ledger._run_continuation_get_raw(child_run)
                self.assertIsNotNone(raw)
                assert raw is not None
                self.assertEqual(raw["pending_action_id"], "")
                self.assertFalse(raw["enabled"])
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
