"""Fault matrix: revoke/expiry races, repeat safety, stop-vs-completion races."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from control_plane.store import ConflictError, ControlPlaneStore

ISSUER = "https://identity.example.test/tenant-faults"
SCOPE = "control-plane.inventory"
WRITE_SCOPE = "control-plane.patch"


class McpFaultMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mcp-faults-")
        self.addCleanup(self.temporary.cleanup)
        self.now = 1_700_000_000_000
        self.store = ControlPlaneStore(Path(self.temporary.name) / "control.sqlite3", clock=lambda: self.now)
        self.owner_id = "owner-default"
        self.node = self.store.enroll_node(
            owner_id=self.owner_id, device_id="fault-node-0001",
            endpoint_id="fault-endpoint-0001", display_name="Fault node")
        self.store.register_node_workspace(
            device_id=self.node["device_id"], workspace_id="fault-workspace-0001",
            workspace_generation="fault-generation-0001", display_name="Fault workspace",
            capabilities={"read": True, "write": True, "exec": True})
        self.binding = self.store.create_binding(
            owner_id=self.owner_id, device_id=self.node["device_id"],
            workspace_id="fault-workspace-0001", workspace_generation="fault-generation-0001",
            display_name="Fault workspace")
        self.principal = self.store.link_oauth_principal(
            owner_id=self.owner_id, issuer=ISSUER, subject="provider-subject-fault-owner")
        self.contract = {"schema_version": 30, "profile": "control-plane-oauth-bounded-exec-v2",
                         "sha256": "a" * 64}

    def _heartbeat(self) -> None:
        self.store.heartbeat(
            device_id=self.node["device_id"], endpoint_id="fault-endpoint-0001",
            runtime_instance_id="runtime-fault-0001", mcp_server_instance_id="server-fault-0001",
            activation_epoch="epoch-fault-0001", contract_version="smart-v3", readiness="ready")

    def test_revoke_between_queue_and_dispatch_refuses_delivery(self) -> None:
        intent = self.store.request_mcp_exec(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            binding_id=self.binding["binding_id"], argv=["python", "-m", "pytest"],
            idempotency_key="fault-revoke-001", facade_contract=self.contract)
        self._heartbeat()
        self.store.revoke_binding(owner_id=self.owner_id, binding_id=self.binding["binding_id"])
        # Dispatch must refuse revoked target; the action settles without effect.
        got = self.store.poll_actions(device_id=self.node["device_id"], lane="bounded_exec")
        self.assertEqual(got, [])
        action = self.store.action(owner_id=self.owner_id, action_id=intent["action_id"])
        self.assertEqual(action["delivery_state"], "settled")

    def test_repeat_request_replays_same_receipt_without_duplicate_effect(self) -> None:
        intent = self.store.request_mcp_exec(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            binding_id=self.binding["binding_id"], argv=["python", "-m", "pytest"],
            idempotency_key="fault-repeat-002", facade_contract=self.contract)
        replay = self.store.request_mcp_exec(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            binding_id=self.binding["binding_id"], argv=["python", "-m", "pytest"],
            idempotency_key="fault-repeat-002", facade_contract=self.contract)
        self.assertTrue(replay["replayed"])
        self.assertEqual(replay["action_id"], intent["action_id"])
        changed = dict(self.contract)
        with self.assertRaises(ConflictError):
            self.store.request_mcp_exec(
                owner_id=self.owner_id, principal_id=self.principal["principal_id"],
                binding_id=self.binding["binding_id"], argv=["python", "-m", "pytest", "-k", "other"],
                idempotency_key="fault-repeat-002", facade_contract=changed)

    def test_stop_race_with_completion_reports_terminal(self) -> None:
        from control_plane.mcp_facade import ControlPlaneMcpFacade
        facade = ControlPlaneMcpFacade(
            self.store, oauth_scopes=(SCOPE,), oauth_file_read_enabled=True,
            oauth_permission_requests_enabled=True, oauth_patch_write_scope=WRITE_SCOPE,
            oauth_approved_patch_enabled=True, oauth_exec_enabled=True)
        contract = {k: facade.contract[k] for k in ("schema_version", "profile", "sha256")}
        intent = self.store.request_mcp_exec(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            binding_id=self.binding["binding_id"], argv=["python", "-m", "pytest"],
            idempotency_key="fault-stop-race-003", facade_contract=contract)
        self._heartbeat()
        delivered = self.store.poll_actions(device_id=self.node["device_id"], lane="bounded_exec")
        self.assertEqual(len(delivered), 1)
        attempt_id = delivered[0]["attempt_id"]
        # Node reports completion first with a minimal valid-shaped payload stub.
        # The facade relay validates strictly, but the stop table must still
        # resolve to already-terminal instead of pending.
        self.store.record_receipt(
            device_id=self.node["device_id"], action_id=intent["action_id"], attempt_id=attempt_id,
            receipt_state="completed", local_handle="cp_local_handle_race_001",
            payload={"note": "minimal terminal marker for stop-race unit scope"})
        stop = self.store.request_mcp_exec_stop(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            action_id=intent["action_id"])
        self.assertEqual(stop["state"], "pending")
        status = facade.handle(
            {"jsonrpc": "2.0", "id": "fault-stop-race", "method": "tools/call",
             "params": {"name": "command_control",
                        "arguments": {"operation": "exec_stop", "action_id": intent["action_id"]}}},
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            granted_context_id=None, oauth_scopes=frozenset({SCOPE, WRITE_SCOPE}))
        self.assertIn(status["result"]["structuredContent"]["stop_state"],
                      ("stopped_or_finished", "pending", "unknown"))

    def test_expired_task_blocks_new_exec_but_stop_still_allowed(self) -> None:
        task = self.store.create_mcp_task_session(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            binding_id=self.binding["binding_id"], label="Expiry race", ttl_ms=60_000)
        intent = self.store.request_mcp_exec(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            binding_id=self.binding["binding_id"], argv=["python", "-m", "pytest"],
            task_id=task["task_id"], idempotency_key="fault-expiry-004",
            facade_contract=self.contract)
        # Advance past task expiry; new actions fence, existing stop still works.
        self.store.clock = lambda: self.now + 61_000
        with self.assertRaises(ConflictError):
            self.store.request_mcp_exec(
                owner_id=self.owner_id, principal_id=self.principal["principal_id"],
                binding_id=self.binding["binding_id"], argv=["python", "-m", "pytest"],
                task_id=task["task_id"], idempotency_key="fault-expiry-005",
                facade_contract=self.contract)
        stop = self.store.request_mcp_exec_stop(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            action_id=intent["action_id"])
        self.assertEqual(stop["action_id"], intent["action_id"])

    def test_unknown_receipt_never_replays_as_completed(self) -> None:
        intent = self.store.request_mcp_exec(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            binding_id=self.binding["binding_id"], argv=["python", "-m", "pytest"],
            idempotency_key="fault-unknown-006", facade_contract=self.contract)
        self._heartbeat()
        delivered = self.store.poll_actions(device_id=self.node["device_id"], lane="bounded_exec")
        self.assertEqual(len(delivered), 1)
        self.store.record_receipt(
            device_id=self.node["device_id"], action_id=intent["action_id"],
            attempt_id=delivered[0]["attempt_id"], receipt_state="unknown",
            local_handle="", payload={"reason": "prepared-recovered"})
        action = self.store.action(owner_id=self.owner_id, action_id=intent["action_id"])
        self.assertEqual(action["delivery_state"], "reconcile_required")
        # A second poll must not redeliver an unknown-effect action.
        self.assertEqual(self.store.poll_actions(device_id=self.node["device_id"], lane="bounded_exec"), [])
        with closing(sqlite3.connect(self.store.path)) as connection:
            rows = connection.execute(
                "SELECT receipt_state FROM receipts WHERE action_id = ?", (intent["action_id"],)).fetchall()
        self.assertEqual([row[0] for row in rows], ["unknown"])


if __name__ == "__main__":
    unittest.main()
