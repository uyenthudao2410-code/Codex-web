from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from control_plane.node_agent import parse_dev_ui_status, runtime_readiness
from control_plane.store import ConflictError, ControlPlaneStore, PermissionError


class ControlPlaneStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.now = 1_700_000_000_000
        self.store = ControlPlaneStore(Path(self.tempdir.name) / "control.sqlite3", clock=lambda: self.now)
        enrolled = self.store.enroll_node(owner_id="owner_default", device_id="device-alpha", endpoint_id="endpoint-alpha", display_name="Windows Canary")
        self.node_secret = enrolled["node_secret"]

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _request(self) -> tuple[dict, dict]:
        binding = self.store.create_binding(owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-alpha", workspace_generation="generation-1", display_name="Canary workspace")
        context = self.store.create_context(owner_id="owner_default", binding_id=binding["binding_id"], expires_at_ms=self.now + 60_000)
        request = self.store.create_work_request(owner_id="owner_default", context_id=context["context_id"], objective="Inspect canary", criteria={"kind": "read_only"}, scope={"root": "canary"}, expires_at_ms=self.now + 30_000)
        return context, request

    def test_context_is_owner_and_binding_scoped(self) -> None:
        context, _ = self._request()
        with self.assertRaises(PermissionError):
            self.store.context(owner_id="another_owner", context_id=context["context_id"])
        self.assertEqual(context["device_id"], "device-alpha")
        self.assertEqual(context["workspace_id"], "workspace-alpha")

    def test_sealed_action_replays_only_when_immutable_payload_matches(self) -> None:
        _, request = self._request()
        first = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0001", admission_reference="admission-0001", expires_at_ms=self.now + 20_000)
        replay = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0001", admission_reference="admission-0001", expires_at_ms=self.now + 20_000)
        self.assertEqual(first["action_id"], replay["action_id"])
        with self.assertRaises(ConflictError):
            self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "other"}, idempotency_key="action-key-0001", admission_reference="admission-0001", expires_at_ms=self.now + 20_000)

    def test_poll_marks_delivery_unknown_before_return_and_receipt_settles(self) -> None:
        _, request = self._request()
        action = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0002", admission_reference="admission-0002", expires_at_ms=self.now + 20_000)
        polled = self.store.poll_actions(device_id="device-alpha")
        self.assertEqual([item["action_id"] for item in polled], [action["action_id"]])
        self.assertEqual(polled[0]["delivery_state"], "dispatch_unconfirmed")
        retry = self.store.poll_actions(device_id="device-alpha")
        self.assertEqual(retry[0]["action_id"], action["action_id"])
        receipt = self.store.record_receipt(device_id="device-alpha", action_id=action["action_id"], receipt_state="completed", local_handle="cmd-1", payload={"proof": "ok"})
        self.assertEqual(receipt["delivery_state"], "settled")
        self.assertEqual(self.store.poll_actions(device_id="device-alpha"), [])

    def test_cross_node_receipt_is_refused(self) -> None:
        _, request = self._request()
        action = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0003", admission_reference="admission-0003", expires_at_ms=self.now + 20_000)
        with self.assertRaises(PermissionError):
            self.store.record_receipt(device_id="device-other", action_id=action["action_id"], receipt_state="accepted", local_handle="", payload={})

    def test_unknown_tool_and_receipt_before_poll_are_refused(self) -> None:
        _, request = self._request()
        with self.assertRaisesRegex(Exception, "smart-v3"):
            self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="arbitrary_shell", arguments={}, idempotency_key="action-key-0004", admission_reference="admission-0004", expires_at_ms=self.now + 20_000)
        action = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0005", admission_reference="admission-0005", expires_at_ms=self.now + 20_000)
        with self.assertRaises(ConflictError):
            self.store.record_receipt(device_id="device-alpha", action_id=action["action_id"], receipt_state="accepted", local_handle="", payload={})

    def test_node_generated_enrollment_requires_explicit_approval(self) -> None:
        request = self.store.request_enrollment(device_id="device-beta", endpoint_id="endpoint-beta", display_name="Second node", credential_hash="a" * 64)
        self.assertIsNone(request["approved_at_ms"])
        approved = self.store.approve_enrollment(owner_id="owner_default", enrollment_id=request["enrollment_id"])
        self.assertEqual(approved["device_id"], "device-beta")
        with self.assertRaises(PermissionError):
            self.store.authenticate_node(device_id="device-beta", node_secret="not-the-requested-secret")

    def test_runtime_heartbeat_is_fail_closed_for_incomplete_hub(self) -> None:
        pending = parse_dev_ui_status(
            "DEV_UI STATUS state=CURRENT host=available instance=runtime-1 components_ready=false fully_ready=false "
            "runtime_telemetry_available=true error_code=none"
        )
        self.assertEqual(runtime_readiness(pending), ("degraded", "admission_or_connector_pending"))
        ready = parse_dev_ui_status(
            "DEV_UI STATUS state=CURRENT host=available instance=runtime-2 components_ready=true fully_ready=true "
            "runtime_telemetry_available=true error_code=none"
        )
        self.assertEqual(runtime_readiness(ready), ("ready", "fully_ready"))
        self.assertEqual(runtime_readiness({"state": "MISSING", "host": "unavailable"}), ("blocked", "runtime_unavailable"))
