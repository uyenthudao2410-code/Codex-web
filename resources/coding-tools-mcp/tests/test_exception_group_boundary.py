from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import ToolFailure, normalize_exception_group
from coding_tools_mcp.server import Runtime


class ExceptionGroupBoundaryTests(unittest.TestCase):
    def test_single_tool_failure_preserves_causal_identity(self) -> None:
        grouped = ExceptionGroup(
            "unhandled errors in a TaskGroup",
            [
                ToolFailure(
                    "SEMANTIC_PROVIDER_CALL_FAILED",
                    "semantic provider failed",
                    category="runtime",
                    retryable=True,
                    details={"provider": "native"},
                )
            ],
        )

        failure = normalize_exception_group(grouped)

        self.assertEqual(failure.code, "SEMANTIC_PROVIDER_CALL_FAILED")
        self.assertEqual(failure.category, "runtime")
        self.assertTrue(failure.retryable)
        self.assertEqual(failure.details["provider"], "native")
        self.assertTrue(failure.details["exception_group"])
        self.assertEqual(failure.details["leaf_count"], 1)

    def test_mixed_group_gets_typed_bounded_runtime_failure(self) -> None:
        grouped = ExceptionGroup(
            "unhandled errors in a TaskGroup",
            [
                ToolFailure("CHECK_FAILED", "check failed", category="runtime"),
                RuntimeError("transport child failed"),
            ],
        )

        failure = normalize_exception_group(grouped)

        self.assertEqual(failure.code, "ASYNC_TASK_GROUP_FAILED")
        self.assertEqual(failure.category, "runtime")
        self.assertFalse(failure.retryable)
        self.assertEqual(failure.details["leaf_count"], 2)
        self.assertEqual(failure.details["children"][0]["code"], "CHECK_FAILED")
        self.assertEqual(failure.details["children"][1]["type"], "RuntimeError")

    def test_call_tool_never_leaks_dispatch_exception_group(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="safe")
            try:
                grouped = ExceptionGroup(
                    "unhandled errors in a TaskGroup",
                    [RuntimeError("child task failed")],
                )
                with patch.object(runtime, "_call_tool_dispatch", side_effect=grouped):
                    result = runtime.call_tool("workspace_context", {"detail": "compact"})

                self.assertTrue(result["isError"])
                error = result["structuredContent"]["error"]
                self.assertEqual(error["code"], "ASYNC_TASK_GROUP_FAILED")
                self.assertEqual(error["category"], "runtime")
                self.assertEqual(error["details"]["leaf_count"], 1)
                self.assertEqual(error["details"]["children"][0]["type"], "RuntimeError")
                recent = runtime.performance_trace.get()["recent"][-1]
                self.assertEqual(recent["error_class"], "RUNTIME")
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
