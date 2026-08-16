from __future__ import annotations

import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.budget_control import BudgetDeadline, RetryPolicy
from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.server import TOOL_REGISTRY, Runtime


class RetryPolicyTests(unittest.TestCase):
    def test_backoff_is_capped_and_should_retry_is_bounded(self) -> None:
        policy = RetryPolicy(max_attempts=3, base_delay_seconds=0.25, max_delay_seconds=2.0, jitter=0.0)
        self.assertTrue(policy.should_retry(0))
        self.assertTrue(policy.should_retry(1))
        self.assertTrue(policy.should_retry(2))
        self.assertFalse(policy.should_retry(3))
        self.assertEqual(policy.delay_for(1), 0.25)
        self.assertEqual(policy.delay_for(2), 0.5)
        for failure in range(3, 20):
            self.assertLessEqual(policy.delay_for(failure), 2.0)

    def test_delays_never_go_negative_with_jitter(self) -> None:
        policy = RetryPolicy(max_attempts=4, base_delay_seconds=0.1, max_delay_seconds=1.0, jitter=0.5)
        for failure in range(1, 12):
            self.assertGreaterEqual(policy.delay_for(failure), 0.0)


class BudgetDeadlineTests(unittest.TestCase):
    def test_runtime_exceeded_raises_terminal_failure(self) -> None:
        budget = BudgetDeadline(max_runtime_seconds=0.05)
        time.sleep(0.08)
        with self.assertRaises(ToolFailure) as caught:
            budget.check()
        self.assertEqual(caught.exception.code, "WORKFLOW_RUNTIME_EXCEEDED")
        self.assertEqual(budget.exceeded, "runtime")
        self.assertFalse(caught.exception.retryable)

    def test_inactivity_exceeded_raises_and_touch_resets_it(self) -> None:
        budget = BudgetDeadline(max_runtime_seconds=60, inactivity_timeout_seconds=0.05)
        budget.touch()
        time.sleep(0.08)
        with self.assertRaises(ToolFailure) as caught:
            budget.check()
        self.assertEqual(caught.exception.code, "WORKFLOW_INACTIVITY_EXCEEDED")
        self.assertEqual(budget.exceeded, "inactivity")
        reset = BudgetDeadline(max_runtime_seconds=60, inactivity_timeout_seconds=0.05)
        time.sleep(0.03)
        reset.touch()
        time.sleep(0.03)
        reset.check()

    def test_remaining_seconds_is_non_negative(self) -> None:
        budget = BudgetDeadline(max_runtime_seconds=60)
        self.assertGreater(budget.remaining_seconds(), 0)


class ReadRetryDispatchTests(unittest.TestCase):
    def test_retryable_read_failure_is_retried_with_backoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                calls: list[int] = []

                def flaky_handler(args: dict) -> dict:
                    calls.append(1)
                    if len(calls) < 2:
                        raise ToolFailure(
                            "TRANSIENT_READ_FAILURE",
                            "Temporary read failure.",
                            category="runtime",
                            retryable=True,
                        )
                    return {"ok": True, "summary": "recovered"}

                spec = TOOL_REGISTRY["server_info"]
                payload = runtime._invoke_with_read_retry("server_info", flaky_handler, {}, spec)
                self.assertEqual(payload["summary"], "recovered")
                self.assertEqual(len(calls), 2)
            finally:
                runtime.close()

    def test_terminal_read_failure_is_not_retried(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                calls: list[int] = []

                def terminal_handler(args: dict) -> dict:
                    calls.append(1)
                    raise ToolFailure("READ_PERMANENT", "Permanent.", category="runtime", retryable=False)

                spec = TOOL_REGISTRY["server_info"]
                with self.assertRaises(ToolFailure) as caught:
                    runtime._invoke_with_read_retry("server_info", terminal_handler, {}, spec)
                self.assertEqual(caught.exception.code, "READ_PERMANENT")
                self.assertEqual(len(calls), 1)
            finally:
                runtime.close()

    def test_mutation_failure_is_never_auto_retried(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                calls: list[int] = []

                def mutation_handler(args: dict) -> dict:
                    calls.append(1)
                    raise ToolFailure("MUTATION_TRANSIENT", "Transient write failure.", category="runtime", retryable=True)

                spec = TOOL_REGISTRY["exec_command"]
                with self.assertRaises(ToolFailure):
                    runtime._invoke_with_read_retry("exec_command", mutation_handler, {}, spec)
                self.assertEqual(len(calls), 1)
            finally:
                runtime.close()


class BackgroundBudgetWatchdogTests(unittest.TestCase):
    def test_agent_workflow_outer_budget_honors_max_runtime_seconds(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            release = threading.Event()

            def blocked_call(name, arguments, request_id=None):
                del name, arguments, request_id
                release.wait(2)
                return {"ok": True}

            try:
                with patch.object(runtime, "_call_tool_sync", side_effect=blocked_call):
                    operation, done = runtime._start_background_tool(
                        "agent_workflow",
                        {"max_runtime_seconds": 7, "timeout_seconds": 600},
                        request_id=None,
                    )
                    self.assertEqual(operation["budget"].max_runtime_seconds, 7)
                    release.set()
                    self.assertTrue(done.wait(2))

                release.clear()
                with patch.object(runtime, "_call_tool_sync", side_effect=blocked_call):
                    operation, done = runtime._start_background_tool(
                        "agent_workflow",
                        {"max_runtime_seconds": 7, "timeout_seconds": 3},
                        request_id=None,
                    )
                    self.assertEqual(operation["budget"].max_runtime_seconds, 3)
                    release.set()
                    self.assertTrue(done.wait(2))

                release.clear()
                with patch.object(runtime, "_call_tool_sync", side_effect=blocked_call):
                    operation, done = runtime._start_background_tool(
                        "server_info",
                        {"timeout_seconds": 11},
                        request_id=None,
                    )
                    self.assertEqual(operation["budget"].max_runtime_seconds, 11)
                    release.set()
                    self.assertTrue(done.wait(2))
            finally:
                release.set()
                runtime.close()

    def test_finished_background_operation_elapsed_and_budget_are_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                event = threading.Event()
                event.set()
                operation = {
                    "operation_id": "finished-op",
                    "tool": "agent_workflow",
                    "workspace": str(Path(temp)),
                    "started_monotonic": 10.0,
                    "finished_monotonic": 12.9,
                    "finished_at": "2026-08-17T00:00:00+00:00",
                    "finished_budget_remaining_seconds": 42.5,
                    "event": event,
                    "result": {"ok": True},
                    "error": None,
                    "budget": BudgetDeadline(max_runtime_seconds=60),
                }
                with patch("coding_tools_mcp.server.time.monotonic", return_value=999.0):
                    snapshot = runtime._background_operation_snapshot(operation)
                self.assertEqual(snapshot["status"], "completed")
                self.assertEqual(snapshot["elapsed_seconds"], 2)
                self.assertEqual(snapshot["budget"]["remaining_seconds"], 42.5)
                self.assertEqual(snapshot["finished_at"], operation["finished_at"])
            finally:
                runtime.close()

    def test_background_operation_is_marked_failed_when_runtime_budget_exceeded(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:

                def slow_handler(args: dict) -> dict:
                    time.sleep(3)
                    return {"ok": True, "summary": "late"}

                with (
                    patch.dict(runtime._tool_handlers, {"server_info": slow_handler}),
                    patch("coding_tools_mcp.server.validate_arguments", lambda *args, **kwargs: None),
                    patch("coding_tools_mcp.server.BACKGROUND_BUDGET_TERMINAL_GRACE_SECONDS", 0.05),
                ):
                    operation, done = runtime._start_background_tool(
                        "server_info",
                        {"timeout_seconds": 1},
                        request_id=None,
                    )
                    self.assertTrue(done.wait(6))
                    snapshot = runtime._background_operation_snapshot(operation)
                    self.assertEqual(snapshot["status"], "failed")
                    error = snapshot.get("error") or {}
                    self.assertEqual(error.get("code"), "WORKFLOW_RUNTIME_EXCEEDED")
                    budget = snapshot.get("budget") or {}
                    self.assertEqual(budget.get("exceeded"), "runtime")
            finally:
                runtime.close()

    def test_background_runtime_budget_is_propagated_to_worker_cancellation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                cancellation_seen = threading.Event()
                worker_returned = threading.Event()

                def cooperative_handler(args: dict) -> dict:
                    del args
                    deadline = time.monotonic() + 3
                    while time.monotonic() < deadline:
                        if runtime._background_operation_cancelled():
                            cancellation_seen.set()
                            time.sleep(0.1)
                            worker_returned.set()
                            return {"ok": False, "status": "cancelled"}
                        time.sleep(0.01)
                    return {"ok": True, "summary": "unexpected late completion"}

                with (
                    patch.dict(runtime._tool_handlers, {"server_info": cooperative_handler}),
                    patch("coding_tools_mcp.server.validate_arguments", lambda *args, **kwargs: None),
                    patch("coding_tools_mcp.server.BACKGROUND_BUDGET_POLL_SECONDS", 0.01),
                    patch("coding_tools_mcp.server.BACKGROUND_BUDGET_TERMINAL_GRACE_SECONDS", 0.5),
                ):
                    operation, done = runtime._start_background_tool(
                        "server_info",
                        {"timeout_seconds": 1},
                        request_id=None,
                    )
                    self.assertTrue(cancellation_seen.wait(2))
                    self.assertFalse(done.is_set(), "budget expiry must request cancellation before publishing terminal state")
                    self.assertTrue(worker_returned.wait(1))
                    self.assertTrue(done.wait(1))
                    snapshot = runtime._background_operation_snapshot(operation)
                    self.assertEqual(snapshot["status"], "failed")
                    self.assertEqual((snapshot.get("error") or {}).get("code"), "WORKFLOW_RUNTIME_EXCEEDED")
                    self.assertIn("finished_at", snapshot)
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
