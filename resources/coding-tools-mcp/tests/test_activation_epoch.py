from __future__ import annotations

import copy
import http.client
import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.projection_rebuild import (
    PROJECTION_REBUILD_MAX_AGE_MS,
    canonical_sha256,
)
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
        # Most admission tests inspect an immediate snapshot. The dedicated
        # wait tests below exercise the bounded transport wait explicitly.
        waiter = patch("coding_tools_mcp.activation_lifecycle.ACTIVATION_BOOTSTRAP_WAIT_SECONDS", 0)
        waiter.start()
        self.addCleanup(waiter.stop)

    def tearDown(self) -> None:
        self.env.stop()
        self.temp.cleanup()

    def test_epoch_bound_missing_gate_defaults_closed(self) -> None:
        with patch.dict(
            os.environ,
            {"CODING_TOOLS_MCP_ACTIVATION_GATE": ""},
        ):
            runtime = Runtime(Path(self.temp.name))
        try:
            self.assertEqual(runtime.activation_gate_config, "closed")
            self.assertEqual(runtime.activation_admission, "closed")
            self.assertFalse(runtime.activation_admission_snapshot()["admission_open"])
            blocked = runtime.call_tool("task_control", {"action": "get"})
            self.assertTrue(blocked["isError"])
            self.assertEqual(
                blocked["structuredContent"]["error"]["code"],
                "RUNTIME_ACTIVATION_PENDING",
            )
        finally:
            runtime.close()

    def test_epoch_bound_open_or_unknown_gate_fails_closed(self) -> None:
        for configured_gate in ("open", "unexpected-value"):
            with self.subTest(configured_gate=configured_gate):
                with patch.dict(
                    os.environ,
                    {"CODING_TOOLS_MCP_ACTIVATION_GATE": configured_gate},
                ):
                    with self.assertRaises(ToolFailure) as failure:
                        Runtime(Path(self.temp.name))
                self.assertEqual(failure.exception.code, "ACTIVATION_GATE_INVALID")

    def test_legacy_runtime_without_epoch_keeps_implicit_open_gate(self) -> None:
        with patch.dict(
            os.environ,
            {
                "CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID": "",
                "CODING_TOOLS_MCP_ACTIVATION_GATE": "",
            },
        ):
            runtime = Runtime(Path(self.temp.name))
        try:
            self.assertEqual(runtime.activation_gate_config, "open")
            self.assertEqual(runtime.activation_admission, "open")
            self.assertTrue(runtime.activation_admission_snapshot()["admission_open"])
        finally:
            runtime.close()

    def test_closed_gate_returns_typed_pending_and_exact_epoch_opens_admission(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            blocked = runtime.call_tool("task_control", {"action": "get"})
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

    def test_workspace_bootstrap_deadline_is_terminal_without_workspace_access(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            for offset_ms in (-1, 0, 1):
                expired = offset_ms >= 0
                with self.subTest(offset_ms=offset_ms), patch(
                    "coding_tools_mcp.activation_lifecycle.time.time",
                    return_value=(self.expires_at_unix_ms + offset_ms) / 1000,
                ), patch.object(
                    runtime, "_set_request_workspace_scope",
                    side_effect=AssertionError("bootstrap must not select a workspace"),
                ), patch.object(
                    runtime, "_call_tool_dispatch",
                    side_effect=AssertionError("bootstrap must not dispatch a workspace tool"),
                ):
                    runtime.request_context.hub_client = {
                        "client_id": "chatweb-activation-deadline-test",
                        "client_type": "chatweb",
                        "identity_source": "attested_transport",
                        "attestation_verified": True,
                        "attestation_source": "managed_tunnel",
                    }
                    result = runtime.call_tool(
                        "workspace_context",
                        {"path": "outside-bootstrap-workspace", "detail": "compact"},
                    )
                self.assertEqual(result["isError"], expired)
                structured = result["structuredContent"]
                self.assertFalse(structured["completed"])
                self.assertFalse(structured["workspace_accessed"])
                self.assertEqual(structured["ok"], not expired)
                self.assertEqual(structured["retryable"], not expired)
                self.assertEqual(runtime.activation_admission, "closed")
                if expired:
                    self.assertNotIn("activation_bootstrap", structured)
                    self.assertEqual(structured["error"]["code"], "ACTIVATION_REQUEST_EXPIRED")
                    self.assertFalse(structured["error"]["retryable"])
                    self.assertEqual(
                        structured["error"]["details"]["expires_at_unix_ms"],
                        self.expires_at_unix_ms,
                    )
                    self.assertEqual(
                        structured["error"]["details"]["activation_epoch_id"], "epoch-test-001"
                    )
                else:
                    self.assertTrue(structured["activation_bootstrap"]["accepted"])
                    self.assertTrue(structured["activation_bootstrap"]["retry_required"])
        finally:
            runtime.close()

    def test_same_sha_workspace_bootstrap_allows_empty_predecessor_list(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            runtime.tool_contract["compatible_predecessor_sha256"] = []
            runtime.request_context.hub_client = {
                "client_id": "chatweb-same-sha-empty-predecessor",
                "client_type": "chatweb",
                "identity_source": "attested_transport",
                "attestation_verified": True,
                "attestation_source": "managed_tunnel",
            }
            with patch.object(
                runtime,
                "_set_request_workspace_scope",
                side_effect=AssertionError("same-SHA bootstrap must not select a workspace"),
            ), patch.object(
                runtime,
                "_call_tool_dispatch",
                side_effect=AssertionError("same-SHA bootstrap must not dispatch a workspace tool"),
            ):
                response = runtime.call_tool(
                    "workspace_context",
                    {"path": "must-not-read", "detail": "compact"},
                )

            self.assertFalse(response["isError"])
            value = response["structuredContent"]
            self.assertEqual(value["status"], "activation_pending")
            self.assertFalse(value["completed"])
            self.assertFalse(value["workspace_accessed"])
            self.assertTrue(value["retryable"])
            self.assertTrue(value["activation_bootstrap"]["accepted"])
            self.assertTrue(value["activation_bootstrap"]["retry_required"])
            self.assertEqual(
                value["activation_bootstrap"]["activation_epoch_id"],
                "epoch-test-001",
            )
            self.assertEqual(runtime.tool_contract["compatible_predecessor_sha256"], [])
        finally:
            runtime.close()

    def test_open_epoch_workspace_reads_survive_the_startup_deadline(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            runtime.complete_activation_epoch(
                "epoch-test-001", self.ready_commit_digest, self.expires_at_unix_ms
            )
            with patch(
                "coding_tools_mcp.activation_lifecycle.time.time",
                return_value=(self.expires_at_unix_ms + 1) / 1000,
            ):
                result = runtime.call_tool("workspace_context", {"detail": "compact"})
            self.assertFalse(result["isError"])
            self.assertTrue(result["structuredContent"]["ok"])
            self.assertNotIn("activation_bootstrap", result["structuredContent"])
            self.assertEqual(runtime.activation_admission, "open")
        finally:
            runtime.close()

    def test_pending_bootstrap_has_timing_identity_and_truthful_model_text(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            runtime.request_context.hub_client = {
                "client_id": "chatweb-bootstrap", "client_type": "chatweb",
                "identity_source": "attested_transport", "attestation_verified": True,
            }
            response = runtime.call_tool("workspace_context", {"path": "must-not-read"})
            value = response["structuredContent"]
            self.assertEqual(value["status"], "activation_pending")
            self.assertGreater(value["retry_after_ms"], 0)
            self.assertEqual(value["activation"]["expires_at_unix_ms"], self.expires_at_unix_ms)
            self.assertFalse(value["activation"]["admission_open"])
            self.assertEqual(value["activation_bootstrap"]["process_instance_id"], runtime.process_instance_id)
            rendered = "\n".join(block.get("text", "") for block in response["content"])
            self.assertIn("pending", rendered.lower())
            self.assertIn(str(value["retry_after_ms"]), rendered)
            self.assertIn(str(self.expires_at_unix_ms), rendered)
            self.assertNotIn("workspace_context: completed", rendered)
            self.assertTrue(runtime.connector_activation_bootstrap()["observed"])
            self.assertFalse(runtime.connector_client_contact()["observed"])
        finally:
            runtime.close()

    def test_attested_call_waits_for_exact_commit_then_reads_once(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        finished = []
        observed_receipt = threading.Event()
        original_record = runtime._record_activation_bootstrap_rpc_contact
        workspace_read = Mock(wraps=runtime.workspace_context)

        def record(*args, **kwargs):
            original_record(*args, **kwargs)
            observed_receipt.set()

        def call():
            runtime.request_context.hub_client = {
                "client_id": "chatweb-bootstrap", "client_type": "chatweb",
                "identity_source": "attested_transport", "attestation_verified": True,
            }
            finished.append(runtime.call_tool("workspace_context", {"detail": "compact"}))

        worker = threading.Thread(target=call)
        try:
            with patch("coding_tools_mcp.activation_lifecycle.ACTIVATION_BOOTSTRAP_WAIT_SECONDS", 2), patch.object(
                runtime, "_record_activation_bootstrap_rpc_contact", side_effect=record
            ), patch.dict(runtime._tool_handlers, {"workspace_context": workspace_read}), patch.object(
                runtime, "_set_request_workspace_scope", wraps=runtime._set_request_workspace_scope
            ) as workspace_scope:
                worker.start()
                self.assertTrue(observed_receipt.wait(1), "receipt must be visible before waiting")
                self.assertFalse(finished)
                self.assertEqual(runtime.active_tool_calls, 0, "bootstrap wait cannot block the final idle census")
                workspace_scope.assert_not_called()
                workspace_read.assert_not_called()
                with self.assertRaises(ToolFailure):
                    runtime.complete_activation_epoch("wrong-epoch", self.ready_commit_digest, self.expires_at_unix_ms)
                self.assertFalse(finished)
                runtime.complete_activation_epoch("epoch-test-001", self.ready_commit_digest, self.expires_at_unix_ms)
                worker.join(3)
                self.assertFalse(worker.is_alive())
            value = finished[0]["structuredContent"]
            self.assertTrue(value["completed"])
            self.assertTrue(value["workspace_accessed"])
            self.assertTrue(value["activation"]["admission_open"])
            self.assertEqual(value["workspace"], str(Path(self.temp.name).resolve()))
            self.assertNotIn("activation_bootstrap", value)
            workspace_read.assert_called_once()
            self.assertFalse(runtime.connector_activation_bootstrap()["workspace_accessed"])
        finally:
            if worker.ident is not None:
                worker.join(3)
            runtime.close()

    def test_bootstrap_wait_timeout_remains_pending_and_preserves_receipt(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            runtime.request_context.hub_client = {
                "client_id": "chatweb-wait-timeout", "client_type": "chatweb",
                "identity_source": "attested_transport", "attestation_verified": True,
            }
            with patch("coding_tools_mcp.activation_lifecycle.ACTIVATION_BOOTSTRAP_WAIT_SECONDS", 0.04), patch.object(
                runtime, "_set_request_workspace_scope", side_effect=AssertionError("no workspace before open")
            ):
                first = runtime.call_tool("workspace_context", {})["structuredContent"]
                receipt = runtime.connector_activation_bootstrap()
                second = runtime.call_tool("workspace_context", {})["structuredContent"]
            self.assertEqual(first["status"], "activation_pending")
            self.assertFalse(second["workspace_accessed"])
            self.assertEqual(runtime.connector_activation_bootstrap(), receipt)
            self.assertEqual(runtime.active_tool_calls, 0)
        finally:
            runtime.close()

    def test_activation_expiry_during_wait_is_terminal(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            runtime.activation_expires_at_unix_ms = int(time.time() * 1000) + 100
            runtime.request_context.hub_client = {
                "client_id": "chatweb-wait-expiry", "client_type": "chatweb",
                "identity_source": "attested_transport", "attestation_verified": True,
            }
            with patch("coding_tools_mcp.activation_lifecycle.ACTIVATION_BOOTSTRAP_WAIT_SECONDS", 1), patch.object(
                runtime, "_set_request_workspace_scope", side_effect=AssertionError("no workspace on expiry")
            ):
                response = runtime.call_tool("workspace_context", {})
            value = response["structuredContent"]
            self.assertTrue(response["isError"])
            self.assertEqual(value["error"]["code"], "ACTIVATION_REQUEST_EXPIRED")
            self.assertFalse(value["retryable"])
            self.assertFalse(value["workspace_accessed"])
        finally:
            runtime.close()

    def test_waiter_capacity_returns_pending_without_wait_or_workspace_access(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            runtime.request_context.hub_client = {
                "client_id": "chatweb-capacity", "client_type": "chatweb",
                "identity_source": "attested_transport", "attestation_verified": True,
            }
            for _ in range(4):
                self.assertTrue(runtime._activation_bootstrap_wait_slots.acquire(blocking=False))
            with patch.object(runtime._activation_admission_changed, "wait", side_effect=AssertionError("excess waiters must return")), patch.object(
                runtime, "_set_request_workspace_scope", side_effect=AssertionError("no workspace before open")
            ):
                value = runtime.call_tool("workspace_context", {})["structuredContent"]
            self.assertEqual(value["status"], "activation_pending")
            self.assertFalse(value["workspace_accessed"])
            self.assertFalse(runtime._activation_bootstrap_wait_slots.acquire(blocking=False))
        finally:
            for _ in range(4):
                runtime._activation_bootstrap_wait_slots.release()
            runtime.close()

    def test_rollback_wakes_waiter_without_dispatch(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        receipt_seen = threading.Event()
        response = []
        original_record = runtime._record_activation_bootstrap_rpc_contact

        def record(*args, **kwargs):
            original_record(*args, **kwargs)
            receipt_seen.set()

        def call():
            runtime.request_context.hub_client = {
                "client_id": "chatweb-wait-rollback", "client_type": "chatweb",
                "identity_source": "attested_transport", "attestation_verified": True,
            }
            response.append(runtime.call_tool("workspace_context", {}))

        worker = threading.Thread(target=call)
        try:
            with patch("coding_tools_mcp.activation_lifecycle.ACTIVATION_BOOTSTRAP_WAIT_SECONDS", 2), patch.object(
                runtime, "_record_activation_bootstrap_rpc_contact", side_effect=record
            ), patch.object(runtime, "_set_request_workspace_scope", side_effect=AssertionError("rollback never dispatches")):
                worker.start()
                self.assertTrue(receipt_seen.wait(1))
                runtime.close_activation_epoch("epoch-test-001")
                worker.join(1)
                self.assertFalse(worker.is_alive())
            value = response[0]["structuredContent"]
            self.assertEqual(value["error"]["code"], "ACTIVATION_ROLLED_BACK")
            self.assertFalse(value["retryable"])
            self.assertFalse(value["workspace_accessed"])
            for _ in range(4):
                self.assertTrue(runtime._activation_bootstrap_wait_slots.acquire(blocking=False))
            for _ in range(4):
                runtime._activation_bootstrap_wait_slots.release()
        finally:
            if worker.ident is not None:
                worker.join(3)
            runtime.close()

    def test_cached_workspace_success_has_fresh_admission_metadata(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            runtime.complete_activation_epoch("epoch-test-001", self.ready_commit_digest, self.expires_at_unix_ms)
            first = runtime.call_tool("workspace_context", {"detail": "compact"})["structuredContent"]
            with patch.object(runtime, "list_dir", side_effect=AssertionError("use the content cache")):
                second = runtime.call_tool("workspace_context", {"detail": "compact"})["structuredContent"]
            self.assertTrue(second["completed"])
            self.assertTrue(second["workspace_accessed"])
            self.assertTrue(second["activation"]["admission_open"])
            self.assertEqual(second["activation"]["ready_commit_digest"], self.ready_commit_digest)
            self.assertTrue(second["cache"]["hit"])
            runtime.close_activation_epoch("epoch-test-001", self.ready_commit_digest)
            refused = runtime.call_tool("workspace_context", {"detail": "compact"})["structuredContent"]
            self.assertFalse(refused["workspace_accessed"])
            self.assertEqual(refused["error"]["code"], "ACTIVATION_ROLLED_BACK")
            self.assertTrue(first["activation"]["admission_open"], "earlier response is immutable")
        finally:
            runtime.close()

    def test_runtime_shutdown_wakes_bootstrap_waiter(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        receipt_seen = threading.Event()
        response = []
        errors = []
        original_record = runtime._record_activation_bootstrap_rpc_contact

        def record(*args, **kwargs):
            original_record(*args, **kwargs)
            receipt_seen.set()

        def call():
            try:
                runtime.request_context.hub_client = {
                    "client_id": "chatweb-wait-shutdown", "client_type": "chatweb",
                    "identity_source": "attested_transport", "attestation_verified": True,
                }
                response.append(runtime.call_tool("workspace_context", {}))
            except BaseException as error:
                errors.append(error)

        worker = threading.Thread(target=call)
        try:
            with patch("coding_tools_mcp.activation_lifecycle.ACTIVATION_BOOTSTRAP_WAIT_SECONDS", 2), patch.object(
                runtime, "_record_activation_bootstrap_rpc_contact", side_effect=record
            ), patch.object(runtime, "_set_request_workspace_scope", side_effect=AssertionError("shutdown never dispatches")):
                worker.start()
                self.assertTrue(receipt_seen.wait(1))
                runtime.close()
                worker.join(1)
                self.assertFalse(worker.is_alive())
            self.assertFalse(errors, str(errors))
            value = response[0]["structuredContent"]
            self.assertEqual(value["error"]["code"], "RUNTIME_STOPPING")
            self.assertFalse(value["retryable"])
            self.assertFalse(value["workspace_accessed"])
        finally:
            if worker.ident is not None:
                worker.join(3)
            runtime.close()

    def test_rollback_is_terminal_for_workspace_bootstrap(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            runtime.close_activation_epoch("epoch-test-001")
            response = runtime.call_tool("workspace_context", {})
            value = response["structuredContent"]
            self.assertTrue(response["isError"])
            self.assertEqual(value["error"]["code"], "ACTIVATION_ROLLED_BACK")
            self.assertFalse(value["retryable"])
            self.assertFalse(value["workspace_accessed"])
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

    def test_completion_recaptures_only_stale_projection_rebuild_receipt(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            initial = runtime.projection_rebuild_snapshot()
            initial_receipt = initial["receipt"]
            self.assertTrue(initial["current"])
            self.assertIsInstance(initial_receipt, dict)
            stale_now_seconds = (
                int(initial_receipt["completed_at_unix_ms"]) + PROJECTION_REBUILD_MAX_AGE_MS + 1
            ) / 1000

            with patch("coding_tools_mcp.projection_rebuild.time.time", return_value=stale_now_seconds):
                stale = runtime.projection_rebuild_snapshot()
                self.assertEqual(stale["validation"]["reasons"], ["RECEIPT_STALE"])
                with patch.object(runtime, "_projection_rebuild_census", wraps=runtime._projection_rebuild_census) as census:
                    opened = runtime.complete_activation_epoch(
                        "epoch-test-001", self.ready_commit_digest, self.expires_at_unix_ms
                    )
                recaptured = runtime.projection_rebuild_snapshot()

            self.assertTrue(opened["ok"])
            self.assertEqual(opened["activation_admission"], "open")
            self.assertEqual(census.call_count, 1)
            self.assertTrue(recaptured["current"])
            self.assertNotEqual(
                initial_receipt["completed_at_unix_ms"],
                recaptured["receipt"]["completed_at_unix_ms"],
            )
            self.assertNotEqual(initial_receipt["integrity_sha256"], recaptured["receipt"]["integrity_sha256"])
        finally:
            runtime.close()

    def test_completion_keeps_non_stale_projection_failure_closed(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            receipt = copy.deepcopy(runtime._projection_rebuild_receipt)
            self.assertIsInstance(receipt, dict)
            receipt["process_instance_id"] = "unexpected-process-instance"
            receipt["integrity_sha256"] = canonical_sha256(
                {key: value for key, value in receipt.items() if key != "integrity_sha256"}
            )
            runtime._projection_rebuild_receipt = receipt

            with patch.object(runtime, "_projection_rebuild_census", wraps=runtime._projection_rebuild_census) as census:
                with self.assertRaises(ToolFailure) as failure:
                    runtime.complete_activation_epoch(
                        "epoch-test-001", self.ready_commit_digest, self.expires_at_unix_ms
                    )

            self.assertEqual(failure.exception.code, "UPDATE_INCOMPLETE")
            self.assertEqual(failure.exception.details["reasons"], ["PROCESS_INSTANCE_ID_MISMATCH"])
            self.assertEqual(census.call_count, 0)
            self.assertFalse(runtime.activation_admission_snapshot()["admission_open"])
        finally:
            runtime.close()

    def test_completion_rechecks_expiry_after_stale_receipt_recapture(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            initial = runtime.projection_rebuild_snapshot()
            initial_receipt = initial["receipt"]
            self.assertTrue(initial["current"])
            self.assertIsInstance(initial_receipt, dict)
            stale_now_seconds = (
                int(initial_receipt["completed_at_unix_ms"]) + PROJECTION_REBUILD_MAX_AGE_MS + 1
            ) / 1000
            expiry = 1_700_000_000_000
            runtime.activation_expires_at_unix_ms = expiry

            with patch("coding_tools_mcp.activation_lifecycle.time") as lifecycle_time:
                lifecycle_time.time.side_effect = [
                    (expiry - 1) / 1000,
                    (expiry - 1) / 1000,
                    expiry / 1000,
                ]
                with patch("coding_tools_mcp.projection_rebuild.time.time", return_value=stale_now_seconds):
                    with patch.object(
                        runtime,
                        "_projection_rebuild_census",
                        wraps=runtime._projection_rebuild_census,
                    ) as census:
                        with self.assertRaises(ToolFailure) as expired:
                            runtime.complete_activation_epoch(
                                "epoch-test-001", self.ready_commit_digest, expiry
                            )

            self.assertEqual(expired.exception.code, "ACTIVATION_REQUEST_EXPIRED")
            self.assertEqual(census.call_count, 1)
            self.assertFalse(runtime.activation_admission_snapshot()["admission_open"])
        finally:
            runtime.close()


if __name__ == "__main__":
    unittest.main()
