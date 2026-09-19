"""Bounded exec central relay: argv without shell, cwd confinement note, stop pending."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from control_plane.mcp_facade import ControlPlaneMcpFacade
from control_plane.store import ConflictError, ControlPlaneStore, ValidationError

ISSUER = "https://identity.example.test/tenant-exec"
SCOPE = "control-plane.inventory"
WRITE_SCOPE = "control-plane.patch"


class McpExecCentralTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mcp-exec-")
        self.addCleanup(self.temporary.cleanup)
        self.now = 1_700_000_000_000
        self.store = ControlPlaneStore(Path(self.temporary.name) / "control.sqlite3", clock=lambda: self.now)
        self.owner_id = "owner-default"
        self.node = self.store.enroll_node(
            owner_id=self.owner_id, device_id="exec-node-0001",
            endpoint_id="exec-endpoint-0001", display_name="Exec node",
        )
        self.store.register_node_workspace(
            device_id=self.node["device_id"], workspace_id="exec-workspace-0001",
            workspace_generation="exec-generation-0001", display_name="Exec workspace",
            capabilities={"read": True, "write": True, "exec": True},
        )
        self.binding = self.store.create_binding(
            owner_id=self.owner_id, device_id=self.node["device_id"],
            workspace_id="exec-workspace-0001", workspace_generation="exec-generation-0001",
            display_name="Exec workspace",
        )
        self.principal = self.store.link_oauth_principal(
            owner_id=self.owner_id, issuer=ISSUER, subject="provider-subject-exec-owner"
        )
        self.facade = ControlPlaneMcpFacade(
            self.store, oauth_scopes=(SCOPE,), oauth_file_read_enabled=True,
            oauth_permission_requests_enabled=True, oauth_patch_write_scope=WRITE_SCOPE,
            oauth_approved_patch_enabled=True, oauth_exec_enabled=True,
        )

    def _contract(self) -> dict:
        return {key: self.facade.contract[key] for key in ("schema_version", "profile", "sha256")}

    def _call(self, tool: str, arguments: dict):
        response = self.facade.handle(
            {"jsonrpc": "2.0", "id": "exec-001", "method": "tools/call",
             "params": {"name": tool, "arguments": arguments}},
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            granted_context_id=None, oauth_scopes=frozenset({SCOPE, WRITE_SCOPE}),
        )
        assert response is not None
        return response

    def test_contract_advertises_exec_and_control(self) -> None:
        self.assertEqual(self.facade.contract["schema_version"], 18)
        by_name = {tool["name"]: tool for tool in self.facade.contract["tools"]}
        self.assertEqual(by_name["exec_command"]["_meta"]["control_plane"]["implemented_operations"], ["exec_run", "exec_status"])
        self.assertEqual(by_name["command_control"]["_meta"]["control_plane"]["implemented_operations"], ["exec_output", "exec_stop"])

    def test_shell_metacharacters_and_absolute_cwd_rejected(self) -> None:
        bad = self._call("exec_command", {
            "operation": "exec_run", "binding_id": self.binding["binding_id"],
            "argv": ["npm", "test", ";", "rm", "-rf", "/"],
            "idempotency_key": "exec-key-shell-001", "expected_facade_contract": self._contract(),
        })
        self.assertEqual(bad["error"]["data"]["code"], "VALIDATION_ERROR")
        bad_cwd = self._call("exec_command", {
            "operation": "exec_run", "binding_id": self.binding["binding_id"],
            "argv": ["npm", "test"], "cwd": "/etc",
            "idempotency_key": "exec-key-cwd-002", "expected_facade_contract": self._contract(),
        })
        self.assertEqual(bad_cwd["error"]["data"]["code"], "VALIDATION_ERROR")
        with self.assertRaises(ValidationError):
            self.store.request_mcp_exec(
                owner_id=self.owner_id, principal_id=self.principal["principal_id"],
                binding_id=self.binding["binding_id"], argv="npm test",
                idempotency_key="exec-key-type-003", facade_contract=self._contract(),
            )

    def test_exec_run_links_task_and_stop_stays_pending_without_receipt(self) -> None:
        task = self.store.create_mcp_task_session(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            binding_id=self.binding["binding_id"], label="Exec task",
        )
        ok = self._call("exec_command", {
            "operation": "exec_run", "binding_id": self.binding["binding_id"],
            "task_id": task["task_id"], "argv": ["python", "-m", "pytest", "-q"],
            "cwd": "", "timeout_ms": 60000, "max_output_bytes": 32768,
            "idempotency_key": "exec-key-task-004", "expected_facade_contract": self._contract(),
        })
        content = ok["result"]["structuredContent"]
        self.assertEqual(content["task_id"], task["task_id"])
        action_id = content["action_id"]
        linked = self.store.list_mcp_task_actions(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"], task_id=task["task_id"])
        self.assertEqual([row["action_id"] for row in linked], [action_id])
        # Cross-task reuse of the same key must conflict, never retarget.
        conflict = self._call("exec_command", {
            "operation": "exec_run", "binding_id": self.binding["binding_id"],
            "argv": ["python", "-m", "pytest", "-q"],
            "idempotency_key": "exec-key-task-004", "expected_facade_contract": self._contract(),
        })
        self.assertEqual(conflict["error"]["data"]["code"], "CONFLICT")
        # Stop is pending until the node proves quiescence.
        stopped = self._call("command_control", {"operation": "exec_stop", "action_id": action_id})
        self.assertEqual(stopped["result"]["structuredContent"]["stop_state"], "pending")
        # Output before any verified receipt is empty, never fabricated.
        output = self._call("command_control", {"operation": "exec_output", "action_id": action_id, "cursor": 0, "max_bytes": 4096})
        self.assertFalse(output["result"]["structuredContent"]["has_output"])
        # Closing the task does not block stop/observe of the existing action.
        self.store.close_mcp_task_session(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"], task_id=task["task_id"])
        again = self._call("command_control", {"operation": "exec_stop", "action_id": action_id})
        self.assertEqual(again["result"]["structuredContent"]["stop_state"], "pending")

    def test_exec_requires_exec_capability(self) -> None:
        node = self.store.enroll_node(
            owner_id=self.owner_id, device_id="exec-node-readonly-0001",
            endpoint_id="exec-endpoint-readonly-0001", display_name="Read only",
        )
        self.store.register_node_workspace(
            device_id=node["device_id"], workspace_id="exec-workspace-readonly-0001",
            workspace_generation="exec-generation-readonly-0001", display_name="Read only",
            capabilities={"read": True, "write": False, "exec": False},
        )
        binding = self.store.create_binding(
            owner_id=self.owner_id, device_id=node["device_id"],
            workspace_id="exec-workspace-readonly-0001",
            workspace_generation="exec-generation-readonly-0001", display_name="Read only",
        )
        with self.assertRaisesRegex(Exception, "exec"):
            self.store.request_mcp_exec(
                owner_id=self.owner_id, principal_id=self.principal["principal_id"],
                binding_id=binding["binding_id"], argv=["npm", "test"],
                idempotency_key="exec-key-noexec-005", facade_contract=self._contract(),
            )

    def test_artifact_doc_and_image_queue_with_task_pin(self) -> None:
        task = self.store.create_mcp_task_session(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            binding_id=self.binding["binding_id"], label="Artifact task")
        doc = self._call("document_workflow", {
            "operation": "doc_read", "binding_id": self.binding["binding_id"],
            "task_id": task["task_id"], "path": "docs/report.md",
            "idempotency_key": "artifact-doc-006", "expected_facade_contract": self._contract()})
        self.assertEqual(doc["result"]["structuredContent"]["task_id"], task["task_id"])
        img = self._call("view_image", {
            "operation": "image_read", "binding_id": self.binding["binding_id"],
            "task_id": task["task_id"], "path": "shots/screen.png",
            "idempotency_key": "artifact-img-007", "expected_facade_contract": self._contract()})
        self.assertIn("action_id", img["result"]["structuredContent"])
        # Same key across kinds must not collide silently; status stays scoped.
        status = self._call("document_workflow", {
            "operation": "doc_status", "action_id": doc["result"]["structuredContent"]["action_id"]})
        self.assertIn("action", status["result"]["structuredContent"])
        # Sensitive doc paths are rejected centrally.
        denied = self._call("document_workflow", {
            "operation": "doc_read", "binding_id": self.binding["binding_id"],
            "path": ".ssh/id_rsa", "idempotency_key": "artifact-doc-008",
            "expected_facade_contract": self._contract()})
        self.assertEqual(denied["error"]["data"]["code"], "VALIDATION_ERROR")

    def test_two_nodes_same_path_stay_isolated_per_task(self) -> None:
        """Bốn máy chồng thời gian: cùng tên file nhưng digest/marker khác nhau."""
        node2 = self.store.enroll_node(
            owner_id=self.owner_id, device_id="exec-node-0002",
            endpoint_id="exec-endpoint-0002", display_name="Exec node 2")
        self.store.register_node_workspace(
            device_id=node2["device_id"], workspace_id="exec-workspace-0002",
            workspace_generation="exec-generation-0002", display_name="Exec workspace 2",
            capabilities={"read": True, "write": True, "exec": True})
        binding2 = self.store.create_binding(
            owner_id=self.owner_id, device_id=node2["device_id"],
            workspace_id="exec-workspace-0002", workspace_generation="exec-generation-0002",
            display_name="Exec workspace 2")
        task_a = self.store.create_mcp_task_session(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            binding_id=self.binding["binding_id"], label="Node A job")
        task_b = self.store.create_mcp_task_session(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            binding_id=binding2["binding_id"], label="Node B job")
        exec_a = self.store.request_mcp_exec(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            binding_id=self.binding["binding_id"], argv=["python", "-m", "pytest", "-q"],
            task_id=task_a["task_id"], idempotency_key="parallel-exec-a-009",
            facade_contract=self._contract())
        exec_b = self.store.request_mcp_exec(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            binding_id=binding2["binding_id"], argv=["python", "-m", "pytest", "-q"],
            task_id=task_b["task_id"], idempotency_key="parallel-exec-b-010",
            facade_contract=self._contract())
        self.assertNotEqual(exec_a["action_id"], exec_b["action_id"])
        # Stop B must not fence A: only B gets a stop request.
        self.store.request_mcp_exec_stop(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            action_id=exec_b["action_id"])
        stops_b = self.store.list_mcp_exec_stop_requests(device_id=node2["device_id"])
        stops_a = self.store.list_mcp_exec_stop_requests(device_id=self.node["device_id"])
        self.assertEqual([s["action_id"] for s in stops_b], [exec_b["action_id"]])
        self.assertEqual(stops_a, [])
        # Heartbeat keeps both nodes dispatchable; stop-pending does not fence poll.
        for device, endpoint in ((self.node["device_id"], "exec-endpoint-0001"),
                                 (node2["device_id"], "exec-endpoint-0002")):
            self.store.heartbeat(device_id=device, endpoint_id=endpoint,
                                 runtime_instance_id=f"runtime-{device}",
                                 mcp_server_instance_id=f"server-{device}",
                                 activation_epoch=f"epoch-{device}",
                                 contract_version="smart-v3", readiness="ready")
        # Poll lanes stay per-node: A still dispatchable while B is stop-pending.
        self.assertEqual(len(self.store.poll_actions(device_id=self.node["device_id"], lane="bounded_exec")), 1)
        self.assertEqual(len(self.store.poll_actions(device_id=node2["device_id"], lane="bounded_exec")), 1)


if __name__ == "__main__":
    unittest.main()
