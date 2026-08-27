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
    ready_commit_digest = "a" * 64
    expires_at_unix_ms = 4_000_000_000_000

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(
            os.environ,
            {
                "CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID": "epoch-test-001",
                "CODING_TOOLS_MCP_ACTIVATION_GATE": "closed",
                "CODING_TOOLS_MCP_ACTIVATION_EXPIRES_AT_UNIX_MS": str(self.expires_at_unix_ms),
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
                runtime.complete_activation_epoch(
                    "wrong-epoch", self.ready_commit_digest, self.expires_at_unix_ms
                )
            self.assertEqual(mismatch.exception.code, "UPDATE_INCOMPLETE")

            with self.assertRaises(ToolFailure) as missing_digest:
                runtime.complete_activation_epoch("epoch-test-001", "", self.expires_at_unix_ms)
            self.assertEqual(
                missing_digest.exception.code,
                "ACTIVATION_EPOCH_READY_COMMIT_DIGEST_INVALID",
            )

            opened = runtime.complete_activation_epoch(
                "epoch-test-001", self.ready_commit_digest, self.expires_at_unix_ms
            )
            self.assertTrue(opened["ok"])
            self.assertEqual(opened["activation_admission"], "open")
            self.assertEqual(opened["ready_commit_digest"], self.ready_commit_digest)
            self.assertEqual(opened["expires_at_unix_ms"], self.expires_at_unix_ms)
            self.assertEqual(
                runtime.complete_activation_epoch(
                    "epoch-test-001", self.ready_commit_digest, self.expires_at_unix_ms
                )["activation_admission"],
                "open",
            )
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

            body = json.dumps({
                "action": "complete_epoch",
                "activation_epoch_id": "epoch-test-001",
                "ready_commit_digest": self.ready_commit_digest,
                "expires_at_unix_ms": self.expires_at_unix_ms,
            }).encode("utf-8")
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
            self.assertEqual(completion_payload["ready_commit_digest"], self.ready_commit_digest)

            close_body = json.dumps({
                "action": "close_epoch",
                "activation_epoch_id": "epoch-test-001",
                "ready_commit_digest": self.ready_commit_digest,
            }).encode("utf-8")
            connection = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
            try:
                connection.request(
                    "POST",
                    "/__control/activation",
                    body=close_body,
                    headers={"Content-Type": "application/json"},
                )
                close_response = connection.getresponse()
                close_payload = json.loads(close_response.read().decode("utf-8"))
            finally:
                connection.close()
            self.assertEqual(close_response.status, 200)
            self.assertFalse(close_payload["admission_open"])
            self.assertTrue(close_payload["completion_closed"])

            with self.assertRaises(ToolFailure) as reopened:
                runtime.complete_activation_epoch(
                    "epoch-test-001", self.ready_commit_digest, self.expires_at_unix_ms
                )
            self.assertEqual(reopened.exception.code, "UPDATE_INCOMPLETE")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())

    def test_health_remains_fail_closed_and_responsive_during_activation_census(self) -> None:
        runtime = Runtime(Path(self.temp.name), transport="http")
        server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        runtime.activation_lock.acquire()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=2)
            try:
                connection.request("GET", "/__control/health")
                response = connection.getresponse()
                payload = json.loads(response.read().decode("utf-8"))
            finally:
                connection.close()
            self.assertEqual(response.status, 200)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["activation_epoch_id"], "epoch-test-001")
            self.assertEqual(payload["activation_admission"], "closed")
            self.assertFalse(payload["admission_open"])
            self.assertTrue(payload["snapshot_busy"])
        finally:
            runtime.activation_lock.release()
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            runtime.close()
            self.assertFalse(thread.is_alive())

    def test_health_remains_responsive_when_observational_locks_are_busy(self) -> None:
        runtime = Runtime(Path(self.temp.name), transport="http")
        server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        lock_cases = (
            (runtime.sessions_lock, "sessions_snapshot_busy"),
            (runtime.tool_discovery_lock, "connector_tool_discovery"),
            (runtime.tool_contact_lock, "connector_client_contact"),
            (server.sessions._lock, "http_sessions"),
        )
        try:
            for lock, busy_field in lock_cases:
                lock.acquire()
                try:
                    connection = http.client.HTTPConnection(
                        "127.0.0.1", server.server_address[1], timeout=2
                    )
                    try:
                        connection.request("GET", "/__control/health")
                        response = connection.getresponse()
                        payload = json.loads(response.read().decode("utf-8"))
                    finally:
                        connection.close()
                finally:
                    lock.release()
                self.assertEqual(response.status, 200)
                self.assertTrue(payload["ready"])
                self.assertTrue(payload["health_snapshot_busy"])
                if busy_field == "sessions_snapshot_busy":
                    self.assertTrue(payload[busy_field])
                    self.assertIsNone(payload["active_commands"])
                    self.assertIsNone(payload["retained_outputs"])
                else:
                    self.assertTrue(payload[busy_field]["snapshot_busy"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            runtime.close()
            self.assertFalse(thread.is_alive())

    def test_closed_epoch_can_preserve_durable_acceptance_without_weakening_other_preflight_gates(self) -> None:
        with patch.dict(
            os.environ,
            {"CODING_TOOLS_MCP_ACTIVATION_ALLOW_ACCEPTANCE_PENDING": "true"},
        ):
            runtime = Runtime(Path(self.temp.name))
        try:
            self.assertTrue(runtime.activation_allow_acceptance_pending)
            with patch.object(
                runtime,
                "activation_preflight",
                return_value={"safe": True, "code": "READY"},
            ) as preflight:
                snapshot = runtime.activation_preflight_snapshot(
                    operation_id="activation-operation-test-0001"
                )
            self.assertTrue(snapshot["safe"])
            self.assertTrue(preflight.call_args.kwargs["allow_acceptance_pending"])
            self.assertEqual(preflight.call_args.kwargs["ignore_active_tool_calls"], 0)
        finally:
            runtime.close()

    def test_completion_refuses_expiry_mismatch_and_exact_deadline(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            with self.assertRaises(ToolFailure) as mismatch:
                runtime.complete_activation_epoch(
                    "epoch-test-001",
                    self.ready_commit_digest,
                    self.expires_at_unix_ms - 1,
                )
            self.assertEqual(mismatch.exception.code, "UPDATE_INCOMPLETE")
            self.assertFalse(runtime.activation_admission_snapshot()["admission_open"])

            runtime.activation_expires_at_unix_ms = 1_700_000_000_000
            with patch("coding_tools_mcp.activation_lifecycle.time.time", return_value=1_700_000_000):
                with self.assertRaises(ToolFailure) as expired:
                    runtime.complete_activation_epoch(
                        "epoch-test-001",
                        self.ready_commit_digest,
                        1_700_000_000_000,
                    )
            self.assertEqual(expired.exception.code, "ACTIVATION_REQUEST_EXPIRED")
            self.assertFalse(runtime.activation_admission_snapshot()["admission_open"])
        finally:
            runtime.close()


if __name__ == "__main__":
    unittest.main()
