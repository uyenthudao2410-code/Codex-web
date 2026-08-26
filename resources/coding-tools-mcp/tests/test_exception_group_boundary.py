from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from coding_tools_mcp.errors import ToolFailure, normalize_exception_group
from coding_tools_mcp.http_exception_boundary import ExceptionSafeMCPHandler
from coding_tools_mcp.protocol import dispatch_rpc
from coding_tools_mcp.server import MCPHandler, Runtime, RuntimeHTTPServer


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

    def test_protocol_never_stringifies_exception_group(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="safe")
            try:
                runtime.initialized = True
                grouped = ExceptionGroup(
                    "unhandled errors in a TaskGroup",
                    [RuntimeError("protocol child task failed")],
                )
                request = {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "tools/call",
                    "params": {
                        "name": "workspace_context",
                        "arguments": {"detail": "compact"},
                    },
                }
                with patch.object(runtime, "call_tool", side_effect=grouped):
                    response = dispatch_rpc(runtime, request)

                self.assertIsNotNone(response)
                assert response is not None
                error = response["error"]
                self.assertEqual(error["code"], -32603)
                self.assertEqual(
                    error["message"],
                    "Concurrent runtime tasks failed; inspect the structured child failures.",
                )
                data = error["data"]
                self.assertEqual(data["code"], "ASYNC_TASK_GROUP_FAILED")
                self.assertEqual(data["category"], "runtime")
                self.assertFalse(data["retryable"])
                self.assertEqual(data["details"]["leaf_count"], 1)
                self.assertEqual(
                    data["details"]["children"][0]["type"],
                    "RuntimeError",
                )
            finally:
                runtime.close()

    def test_http_pre_dispatch_boundary_never_stringifies_exception_group(self) -> None:
        grouped = ExceptionGroup(
            "unhandled errors in a TaskGroup",
            [RuntimeError("hub reconciliation child failed")],
        )

        class FailingRuntime:
            def __init__(self) -> None:
                self.request_context = SimpleNamespace()

            def _touch_hub_client(self, _identity: dict[str, object]) -> None:
                raise grouped

        runtime = FailingRuntime()
        handler = object.__new__(ExceptionSafeMCPHandler)
        handler._runtime = runtime
        handler.headers = {}
        request = {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {
                "name": "workspace_context",
                "arguments": {"detail": "compact"},
            },
        }
        with patch.object(
            ExceptionSafeMCPHandler,
            "_hub_identity_from_request",
            return_value={"client_id": "chatweb", "client_type": "chatweb", "role": "controller"},
        ):
            response = handler.handle_rpc(request)

        self.assertIsNotNone(response)
        assert response is not None
        error = response["error"]
        self.assertEqual(error["code"], -32603)
        self.assertEqual(
            error["message"],
            "Concurrent runtime tasks failed; inspect the structured child failures.",
        )
        data = error["data"]
        self.assertEqual(data["code"], "ASYNC_TASK_GROUP_FAILED")
        self.assertEqual(data["details"]["leaf_count"], 1)
        self.assertEqual(data["details"]["children"][0]["type"], "RuntimeError")
        self.assertFalse(hasattr(runtime.request_context, "hub_client"))

    def test_http_tools_call_returns_typed_exception_group_error(self) -> None:
        """The live HTTP dispatch path must never expose a raw TaskGroup error."""
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), transport="http", permission_mode="safe")
            server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                grouped = ExceptionGroup(
                    "unhandled errors in a TaskGroup",
                    [RuntimeError("live tool child failed")],
                )
                request = {
                    "jsonrpc": "2.0",
                    "id": 17,
                    "method": "tools/call",
                    "params": {
                        "name": "workspace_context",
                        "arguments": {"detail": "compact"},
                    },
                }
                body = json.dumps(request).encode("utf-8")
                with patch.object(runtime, "call_tool", side_effect=grouped):
                    connection = http.client.HTTPConnection(
                        "127.0.0.1", server.server_address[1], timeout=5
                    )
                    try:
                        connection.request(
                            "POST",
                            "/mcp",
                            body=body,
                            headers={
                                "Content-Type": "application/json",
                                "Content-Length": str(len(body)),
                            },
                        )
                        response = connection.getresponse()
                        payload = json.loads(response.read().decode("utf-8"))
                    finally:
                        connection.close()

                self.assertEqual(response.status, 200)
                error = payload["error"]
                self.assertEqual(error["code"], -32603)
                self.assertEqual(
                    error["message"],
                    "Concurrent runtime tasks failed; inspect the structured child failures.",
                )
                self.assertNotIn("ExceptionGroup", error["message"])
                self.assertEqual(error["data"]["code"], "ASYNC_TASK_GROUP_FAILED")
                self.assertEqual(error["data"]["details"]["leaf_count"], 1)
                self.assertEqual(error["data"]["details"]["children"][0]["type"], "RuntimeError")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                runtime.close()


if __name__ == "__main__":
    unittest.main()
