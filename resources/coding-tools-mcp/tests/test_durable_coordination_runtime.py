from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.server import Runtime


def _completed_bridge_result(turn_id: str) -> dict:
    response = {
        "status": "completed",
        "summary": f"completed {turn_id}",
        "question": None,
        "findings": [],
        "missing_proof": [],
        "next_action": "return to ChatWeb Sol",
        "confidence": "high",
    }
    return {
        "ok": True,
        "status": "completed",
        "thread_id": "persistent-thread",
        "turn_id": turn_id,
        "session_id": "persistent-session",
        "lifetime": "persistent",
        "creation_mode": "persistent_new" if turn_id == "turn-1" else "persistent_resume",
        "route": {
            "profile": "cross_file",
            "model": "gpt-5.6-terra",
            "effort": "high",
        },
        "observation": {
            "status": "completed",
            "terminal": True,
            "turn_id": turn_id,
            "agent_text": json.dumps(response),
            "wall_time_ms": 12,
            "economics": {"estimated_credits": 0.25},
            "deadline_hit": False,
        },
    }


class FakePersistentBridge:
    def __init__(self, *, owns: bool = False) -> None:
        self._owns = owns
        self.run_calls: list[dict] = []
        self.continue_calls: list[dict] = []
        self.resume_calls: list[dict] = []
        self.closed = False

    def run(self, prompt: str, **kwargs):
        self.run_calls.append({"prompt": prompt, **kwargs})
        self._owns = True
        return _completed_bridge_result("turn-1")

    def owns_thread(self, thread_id: str) -> bool:
        return self._owns and thread_id == "persistent-thread"

    def continue_thread(self, **kwargs):
        self.continue_calls.append(dict(kwargs))
        return _completed_bridge_result("turn-2")

    def resume_persistent_thread(self, **kwargs):
        self.resume_calls.append(dict(kwargs))
        self._owns = True
        return _completed_bridge_result("turn-2")

    def observe(self, **_kwargs):
        return _completed_bridge_result("turn-2")["observation"]

    def close(self):
        self.closed = True


class DurableCoordinationRuntimeTests(unittest.TestCase):
    def _runtime(self, root: Path) -> Runtime:
        runtime = Runtime(root, permission_mode="dangerous")
        runtime._orchestration_workspace_identity = lambda _path: {
            "base_head": "head-1",
            "worktree_fp": "worktree-1",
        }
        return runtime

    def test_runtime_orphans_only_operations_from_a_prior_process(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            ledger.start_background_operation(
                operation_id="old-operation",
                server_instance_id="prior-process",
                tool="agent_workflow",
                summary={"objective": "old work"},
            )

            runtime = self._runtime(root)
            try:
                self.assertEqual(runtime.orphaned_background_operations, 1)
                result = runtime.task_control(
                    {"action": "operation", "operation_id": "old-operation"}
                )
                operation = result["background_operation"]
                self.assertEqual(operation["status"], "orphaned")
                self.assertTrue(operation["durable_only"])
                self.assertEqual(
                    operation["summary"]["orphan_reason"],
                    "mcp_runtime_restarted",
                )
            finally:
                runtime.close()

    def test_background_completion_is_persisted_without_full_result_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = self._runtime(root)
            try:
                runtime._call_tool_sync = lambda *_args, **_kwargs: {
                    "structuredContent": {"status": "completed"}
                }
                operation, done = runtime._start_background_tool(
                    "agent_workflow",
                    {"phase": "run", "objective": "bounded work"},
                    request_id="request-1",
                )
                self.assertTrue(done.wait(2))
                durable = runtime.orchestration_ledger.get_background_operation(
                    operation["operation_id"]
                )
                self.assertIsNotNone(durable)
                assert durable is not None
                self.assertEqual(durable["status"], "completed")
                self.assertTrue(durable["summary"]["result_available_in_memory"])
                self.assertEqual(durable["summary"]["result_status"], "completed")
                self.assertNotIn("structuredContent", durable["summary"])
            finally:
                runtime.close()

    def test_reconnected_runtime_in_same_process_can_poll_live_operation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = self._runtime(root)
            gate = threading.Event()

            def slow_result(*_args, **_kwargs):
                gate.wait(2)
                return {"structuredContent": {"status": "completed"}}

            first._call_tool_sync = slow_result
            operation, done = first._start_background_tool(
                "agent_workflow",
                {"phase": "run", "objective": "survive HTTP reconnect"},
                request_id="request-live",
            )
            second = self._runtime(root)
            try:
                self.assertEqual(second.orphaned_background_operations, 0)
                polled = second.task_control(
                    {
                        "action": "operation",
                        "operation_id": operation["operation_id"],
                    }
                )["background_operation"]
                self.assertEqual(polled["status"], "running")
                self.assertFalse(polled.get("durable_only", False))
                gate.set()
                self.assertTrue(done.wait(2))
                completed = second.task_control(
                    {
                        "action": "operation",
                        "operation_id": operation["operation_id"],
                    }
                )["background_operation"]
                self.assertEqual(completed["status"], "completed")
                self.assertIn("result", completed)
            finally:
                gate.set()
                second.close()
                first.close()

    def test_handoff_capsule_and_message_ack_are_available_through_task_control(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = self._runtime(root)
            try:
                runtime.task_state.update(
                    {
                        "objective": "durable ChatWeb rollover",
                        "status": "active",
                        "current_step": "Persist compact state",
                        "next_step": "Open a fresh conversation",
                    }
                )
                message_id = runtime.orchestration_ledger.append_coordination_message(
                    direction="codex_to_chatweb",
                    kind="question",
                    payload={"question": "Which acceptance domain owns this change?"},
                )
                recorded = runtime.task_control(
                    {
                        "action": "handoff",
                        "handoff_action": "record",
                        "conversation_epoch": 3,
                        "payload": {
                            "goal": "continue without transcript replay",
                            "accept": ["single final authority"],
                            "next_action": "poll pending messages",
                        },
                    }
                )
                self.assertTrue(recorded["recorded"])
                self.assertEqual(recorded["capsule"]["conversation_epoch"], 3)
                self.assertIn(message_id, recorded["capsule"]["payload"]["runtime"]["pending_message_ids"])
                handoff_runtime = recorded["capsule"]["payload"]["runtime"]
                self.assertIn("workspace_id", handoff_runtime)
                self.assertIn("write_lease_id", handoff_runtime)
                self.assertIn("delegation_id", handoff_runtime)
                self.assertIn("proof_ids", handoff_runtime)

                fetched = runtime.task_control(
                    {"action": "handoff", "handoff_action": "get"}
                )
                self.assertEqual(
                    fetched["capsule"]["sha256"],
                    recorded["capsule"]["sha256"],
                )
                messages = runtime.task_control({"action": "messages"})["messages"]
                self.assertEqual([item["message_id"] for item in messages], [message_id])
                acknowledged = runtime.task_control(
                    {"action": "ack", "message_id": message_id}
                )
                self.assertTrue(acknowledged["acknowledged"])
                self.assertEqual(acknowledged["message"]["status"], "acknowledged")
            finally:
                runtime.close()

    def test_persistent_lane_resumes_after_runtime_object_rollover(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = self._runtime(root)
            first_bridge = FakePersistentBridge()
            first._codex_bridge.close()
            first._codex_bridge = first_bridge
            try:
                started = first.task_control(
                    {
                        "action": "lane",
                        "lane_action": "start",
                        "lane_id": "lane-1",
                        "semantic_key": "finance:invoice-recovery",
                        "prompt": "Inspect the bounded financial invariant and return evidence only.",
                        "profile": "cross_file",
                    }
                )
                self.assertEqual(started["status"], "started")
                self.assertEqual(started["lane"]["thread_id"], "persistent-thread")
                self.assertEqual(started["lane"]["session_id"], "persistent-session")
                self.assertEqual(started["lane"]["lifecycle"], "idle")
                self.assertEqual(first_bridge.run_calls[0]["lifetime"], "persistent")
            finally:
                first.close()

            second = self._runtime(root)
            second_bridge = FakePersistentBridge(owns=False)
            second._codex_bridge.close()
            second._codex_bridge = second_bridge
            try:
                continued = second.task_control(
                    {
                        "action": "lane",
                        "lane_action": "continue",
                        "lane_id": "lane-1",
                        "prompt": "Revalidate only the delta and return the next bounded result.",
                    }
                )
                self.assertEqual(continued["status"], "continued")
                self.assertEqual(len(second_bridge.resume_calls), 1)
                resume_call = second_bridge.resume_calls[0]
                self.assertEqual(resume_call["thread_id"], "persistent-thread")
                self.assertEqual(
                    resume_call["expected_session_id"],
                    "persistent-session",
                )
                pending = second.task_control(
                    {
                        "action": "messages",
                        "lane_id": "lane-1",
                        "direction": "codex_to_chatweb",
                    }
                )["messages"]
                self.assertEqual(len(pending), 2)
                self.assertTrue(all(item["kind"] == "result" for item in pending))
            finally:
                second.close()

    def test_lane_drift_requires_explicit_revalidation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = self._runtime(root)
            bridge = FakePersistentBridge()
            runtime._codex_bridge.close()
            runtime._codex_bridge = bridge
            try:
                runtime.task_control(
                    {
                        "action": "lane",
                        "lane_action": "start",
                        "lane_id": "lane-1",
                        "semantic_key": "backend:contract",
                        "prompt": "Inspect the bounded contract.",
                        "profile": "cross_file",
                    }
                )
                runtime._orchestration_workspace_identity = lambda _path: {
                    "base_head": "head-2",
                    "worktree_fp": "worktree-2",
                }
                blocked = runtime.task_control(
                    {
                        "action": "lane",
                        "lane_action": "continue",
                        "lane_id": "lane-1",
                        "prompt": "Continue without revalidation.",
                    }
                )
                self.assertEqual(blocked["status"], "blocked")
                self.assertEqual(blocked["reason"], "lane_base_drift")
                self.assertEqual(len(bridge.continue_calls), 0)
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
