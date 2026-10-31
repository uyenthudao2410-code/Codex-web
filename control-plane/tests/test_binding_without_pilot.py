"""No-pilot contract: live binding alone authorises intake, poll, and authority.

A live binding with a live node and a current registration is sufficient.
No scoped_pilot_decisions row is created, consulted, or required anywhere
on these paths, and stale pilot rows left in the kept history table are
ignored: they neither grant nor block.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from control_plane.store import ControlPlaneStore


CONTRACT = {"schema_version": 3, "profile": "control-plane-read-only-queue-v2", "sha256": "f" * 64}


class BindingWithoutPilotTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="binding-without-pilot-")
        self.addCleanup(temporary.cleanup)
        self.now = 1_700_000_000_000
        self.store = ControlPlaneStore(Path(temporary.name) / "control.sqlite3", clock=lambda: self.now)
        self.node = self.store.enroll_node(owner_id="owner_default", device_id="device-alpha",
                                           endpoint_id="endpoint-alpha", display_name="Windows node")
        self.store.register_node_workspace(
            device_id="device-alpha", workspace_id="workspace-alpha",
            workspace_generation="generation-1", display_name="Alpha",
            capabilities={"read": True, "write": True, "exec": True},
        )
        self.binding = self.store.create_binding(
            owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-alpha",
            workspace_generation="generation-1", display_name="Alpha",
        )
        self.principal = self.store.create_private_tunnel_service_principal(owner_id="owner_default")["principal_id"]
        self.store.heartbeat(device_id="device-alpha", endpoint_id="endpoint-alpha", runtime_instance_id="runtime-alpha",
                             mcp_server_instance_id="server-alpha", activation_epoch="epoch-alpha",
                             contract_version="smart-v3", readiness="ready")
        self.store.set_admission_mode(mode="open")

    def table(self, name: str) -> list[dict]:
        with self.store._connection() as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM " + name)]

    def test_task_open_intake_without_pilot_leaves_decision_column_null(self) -> None:
        task = self.store.create_mcp_task_session(
            owner_id="owner_default", principal_id=self.principal,
            binding_id=self.binding["binding_id"], label="Work",
        )
        row = self.table("mcp_task_sessions")[0]
        self.assertEqual(row["task_id"], task["task_id"])
        self.assertIsNone(row["scoped_pilot_decision_id"])
        self.assertEqual(self.table("scoped_pilot_decisions"), [])

    def test_file_read_and_exec_intake_without_pilot(self) -> None:
        task = self.store.create_mcp_task_session(
            owner_id="owner_default", principal_id=self.principal,
            binding_id=self.binding["binding_id"], label="Work",
        )
        read = self.store.request_mcp_bounded_file_read(
            owner_id="owner_default", principal_id=self.principal, binding_id=self.binding["binding_id"],
            path="README.md", start_line=1, max_lines=5, max_bytes=1024, idempotency_key="nopilot-read-0001",
            facade_contract=CONTRACT,
        )
        executed = self.store.request_mcp_exec(
            owner_id="owner_default", principal_id=self.principal, binding_id=self.binding["binding_id"],
            task_id=task["task_id"], argv=["python", "-c", "print('ok')"],
            idempotency_key="nopilot-exec-0001", facade_contract=CONTRACT,
        )
        rows = {row["action_id"]: row for row in self.table("actions")}
        self.assertIsNone(rows[read["action_id"]]["scoped_pilot_decision_id"])
        self.assertIsNone(rows[executed["action_id"]]["scoped_pilot_decision_id"])
        self.assertEqual(self.table("scoped_pilot_decisions"), [])

    def test_poll_delivers_without_pilot(self) -> None:
        read = self.store.request_mcp_bounded_file_read(
            owner_id="owner_default", principal_id=self.principal, binding_id=self.binding["binding_id"],
            path="README.md", start_line=1, max_lines=5, max_bytes=1024, idempotency_key="nopilot-poll-0001",
            facade_contract=CONTRACT,
        )
        scoped = self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read",
                                         workspace_id="workspace-alpha", workspace_generation="generation-1")
        self.assertEqual([item["action_id"] for item in scoped], [read["action_id"]])
        delivered = self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read")
        self.assertEqual(delivered, [])

    def test_policy_authority_without_pilot(self) -> None:
        authority = self.store.node_authority_status(
            device_id="device-alpha", node_secret=self.node["node_secret"], principal_id=self.principal,
        )
        self.assertEqual(authority["state"], "active")
        self.assertEqual([target["workspace_id"] for target in authority["targets"]], ["workspace-alpha"])

    def test_activation_idempotent_without_pilot(self) -> None:
        first = self.store.activate_node_workspace(
            device_id="device-alpha", principal_id=self.principal,
            workspace_id="workspace-alpha", workspace_generation="generation-1",
        )
        self.assertEqual(first["binding_id"], self.binding["binding_id"])
        self.assertEqual(first["state"], "active")
        second = self.store.activate_node_workspace(
            device_id="device-alpha", principal_id=self.principal,
            workspace_id="workspace-alpha", workspace_generation="generation-1",
        )
        self.assertEqual(second, first)
        self.assertEqual(len(self.table("bindings")), 1)
        self.assertEqual(self.table("scoped_pilot_decisions"), [])

    def test_old_pilot_rows_are_ignored(self) -> None:
        with self.store._connection() as connection:
            for decision_id, expires_at_ms, revoked_at_ms in (
                ("pilot_" + "e" * 32, self.now - 1, None),
                ("pilot_" + "f" * 32, self.now + 3_600_000, self.now),
            ):
                connection.execute(
                    "INSERT INTO scoped_pilot_decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (decision_id, "owner_default", self.principal, self.binding["binding_id"], "device-alpha",
                     "endpoint-alpha", "workspace-alpha", "generation-1", "legacy row",
                     self.now - 3_600_000, expires_at_ms, revoked_at_ms),
                )
        task = self.store.create_mcp_task_session(
            owner_id="owner_default", principal_id=self.principal,
            binding_id=self.binding["binding_id"], label="Work after legacy rows",
        )
        self.assertIsNotNone(task["task_id"])
        read = self.store.request_mcp_bounded_file_read(
            owner_id="owner_default", principal_id=self.principal, binding_id=self.binding["binding_id"],
            path="README.md", start_line=1, max_lines=5, max_bytes=1024, idempotency_key="nopilot-legacy-0001",
            facade_contract=CONTRACT,
        )
        delivered = self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read")
        self.assertEqual([item["action_id"] for item in delivered], [read["action_id"]])
        authority = self.store.node_authority_status(
            device_id="device-alpha", node_secret=self.node["node_secret"], principal_id=self.principal,
        )
        self.assertEqual(authority["state"], "active")
        activated = self.store.activate_node_workspace(
            device_id="device-alpha", principal_id=self.principal,
            workspace_id="workspace-alpha", workspace_generation="generation-1",
        )
        self.assertEqual(activated["binding_id"], self.binding["binding_id"])
        self.assertEqual(len(self.table("scoped_pilot_decisions")), 2)


if __name__ == "__main__":
    unittest.main()
