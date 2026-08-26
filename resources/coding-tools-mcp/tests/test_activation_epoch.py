from __future__ import annotations

import http.client
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.server import MCPHandler, Runtime, RuntimeHTTPServer


class ActivationEpochTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(
            os.environ,
            {
                "CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID": "epoch-test-001",
                "CODING_TOOLS_MCP_ACTIVATION_GATE": "closed",
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
            },
        )
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()
        self.temp.cleanup()

    def test_closed_gate_returns_typed_pending_and_exact_epoch_opens_admission(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            blocked = runtime.call_tool("workspace_context", {"detail": "compact"})
            self.assertTrue(blocked["isError"])
            self.assertEqual(blocked["structuredContent"]["error"]["code"], "RUNTIME_ACTIVATION_PENDING")
            self.assertEqual(runtime.activation_admission_snapshot()["activation_admission"], "closed")

            with self.assertRaises(ToolFailure) as mismatch:
                runtime.complete_activation_epoch("wrong-epoch")
            self.assertEqual(mismatch.exception.code, "UPDATE_INCOMPLETE")

            opened = runtime.complete_activation_epoch("epoch-test-001")
            self.assertTrue(opened["ok"])
            self.assertEqual(opened["activation_admission"], "open")
            allowed = runtime.call_tool("workspace_context", {"detail": "compact"})
            self.assertFalse(allowed["isError"])
        finally:
            runtime.close()

    def test_health_exposes_epoch_and_admission_state(self) -> None:
        runtime = Runtime(Path(self.temp.name), transport="http")
        server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
            try:
                connection.request("GET", "/__control/health")
                response = connection.getresponse()
                payload = json.loads(response.read().decode("utf-8"))
            finally:
                connection.close()
            self.assertEqual(response.status, 200)
            self.assertEqual(payload["activation_epoch_id"], "epoch-test-001")
            self.assertEqual(payload["activation_admission"], "closed")
            self.assertEqual(payload["activation"]["admission"], "closed")

            for request_id, method in ((2, "tools/list"), (3, "server/discover")):
                body = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": {}}).encode("utf-8")
                connection = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
                try:
                    connection.request("POST", "/mcp", body=body, headers={"Content-Type": "application/json"})
                    metadata_response = connection.getresponse()
                    metadata_payload = json.loads(metadata_response.read().decode("utf-8"))
                finally:
                    connection.close()
                self.assertEqual(metadata_response.status, 200)
                self.assertIn("result", metadata_payload)

            body = json.dumps({"action": "complete_epoch", "activation_epoch_id": "epoch-test-001"}).encode("utf-8")
            connection = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
            try:
                connection.request(
                    "POST",
                    "/__control/activation",
                    body=body,
                    headers={"Content-Type": "application/json"},
                )
                completion_response = connection.getresponse()
                completion_payload = json.loads(completion_response.read().decode("utf-8"))
            finally:
                connection.close()
            self.assertEqual(completion_response.status, 200)
            self.assertEqual(completion_payload["activation_admission"], "open")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()
