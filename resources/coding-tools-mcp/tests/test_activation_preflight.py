from __future__ import annotations

import http.client
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from coding_tools_mcp.server import MCPHandler, Runtime, RuntimeHTTPServer


class ActivationPreflightTests(unittest.TestCase):
    def test_authenticated_control_endpoint_prepares_and_cancels_fence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), auth_token="activation-token")
            server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = int(server.server_address[1])
            operation_id = "activation-operation-http-0001"
            try:
                body = json.dumps({
                    "action": "prepare",
                    "operation_id": operation_id,
                    "expires_at_unix_ms": int(time.time() * 1000) + 30_000,
                    "workspace": str(Path(temp).resolve()),
                    "allow_acceptance_pending": False,
                })
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                connection.request("POST", "/__control/activation", body=body, headers={
                    "Authorization": "Bearer activation-token",
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body.encode("utf-8"))),
                })
                response = connection.getresponse()
                prepared = json.loads(response.read())
                self.assertEqual(response.status, 200)
                self.assertTrue(prepared["fenced"])
                connection.close()

                cancel_body = json.dumps({"action": "cancel", "operation_id": operation_id})
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                connection.request("POST", "/__control/activation", body=cancel_body, headers={
                    "Authorization": "Bearer activation-token",
                    "Content-Type": "application/json",
                    "Content-Length": str(len(cancel_body.encode("utf-8"))),
                })
                response = connection.getresponse()
                cancelled = json.loads(response.read())
                self.assertEqual(response.status, 200)
                self.assertTrue(cancelled["cancelled"])
                connection.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_prepare_fences_new_tool_calls_until_cancelled(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            operation_id = "activation-operation-0001"
            try:
                prepared = runtime.activation_preflight(
                    operation_id=operation_id,
                    expires_at_unix_ms=int(time.time() * 1000) + 30_000,
                    prepare=True,
                )
                self.assertTrue(prepared["safe"])
                self.assertTrue(prepared["fenced"])
                blocked = runtime.call_tool("server_info", {})
                self.assertTrue(blocked["isError"])
                self.assertEqual(
                    blocked["structuredContent"]["error"]["code"],
                    "RUNTIME_ACTIVATION_PENDING",
                )
                self.assertTrue(runtime.cancel_activation(operation_id))
                self.assertFalse(runtime.call_tool("server_info", {})["isError"])
            finally:
                runtime.close()

    def test_active_tool_call_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                runtime.active_tool_calls = 1
                result = runtime.activation_preflight()
                self.assertFalse(result["safe"])
                self.assertEqual(result["code"], "RUNTIME_BUSY")
                self.assertEqual(result["counts"]["active_tool_calls"], 1)
            finally:
                runtime.active_tool_calls = 0
                runtime.close()

    def test_accepting_requires_explicit_preservation_and_valid_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                active_run = {"run_id": "run-accepting"}
                accepting = SimpleNamespace(state="ACCEPTING")
                with (
                    patch.object(runtime.orchestration_ledger, "current_active_run", return_value=active_run),
                    patch.object(runtime.orchestration_control, "snapshot", return_value=accepting),
                    patch.object(runtime.orchestration_ledger, "verify_chain", return_value={"ok": True}),
                ):
                    refused = runtime.activation_preflight()
                    self.assertFalse(refused["safe"])
                    self.assertEqual(refused["code"], "ACCEPTANCE_PENDING")
                    allowed = runtime.activation_preflight(allow_acceptance_pending=True)
                    self.assertTrue(allowed["safe"])
                    self.assertTrue(allowed["acceptance_pending"])
            finally:
                runtime.close()

    def test_non_accepting_active_orchestration_and_bad_integrity_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                active_run = {"run_id": "run-active"}
                with (
                    patch.object(runtime.orchestration_ledger, "current_active_run", return_value=active_run),
                    patch.object(runtime.orchestration_control, "snapshot", return_value=SimpleNamespace(state="PROVING")),
                    patch.object(runtime.orchestration_ledger, "verify_chain", return_value={"ok": True}),
                ):
                    self.assertEqual(runtime.activation_preflight()["code"], "RUNTIME_BUSY")
                with (
                    patch.object(runtime.orchestration_ledger, "current_active_run", return_value=active_run),
                    patch.object(runtime.orchestration_control, "snapshot", return_value=SimpleNamespace(state="ACCEPTING")),
                    patch.object(runtime.orchestration_ledger, "verify_chain", return_value={"ok": False}),
                ):
                    self.assertEqual(
                        runtime.activation_preflight(allow_acceptance_pending=True)["code"],
                        "ORCHESTRATION_STATE_UNCERTAIN",
                    )
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
