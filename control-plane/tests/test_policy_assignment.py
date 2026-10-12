"""Owner policy assignments remain distinct from sealed MCP operation contexts."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from control_plane.store import ConflictError, ControlPlaneStore, NotFoundError


FACADE_CONTRACT = {
    "schema_version": 3,
    "profile": "control-plane-read-only-queue-v2",
    "sha256": "f" * 64,
}


class ReadOnlyPolicyAssignmentTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="policy-assignment-")
        self.addCleanup(temporary.cleanup)
        self.now = 1_700_000_000_000
        self.store = ControlPlaneStore(Path(temporary.name) / "control.sqlite3", clock=lambda: self.now)
        self.owner_id = "owner-default"
        self.node = self.store.enroll_node(
            owner_id=self.owner_id, device_id="policy-node-0001",
            endpoint_id="policy-endpoint-0001", display_name="Policy node",
        )
        self.store.register_node_workspace(
            device_id=self.node["device_id"], workspace_id="policy-workspace-0001",
            workspace_generation="policy-generation-0001", display_name="Policy workspace",
            capabilities={"read": True, "write": True, "exec": True},
        )
        self.binding = self.store.create_binding(
            owner_id=self.owner_id, device_id=self.node["device_id"],
            workspace_id="policy-workspace-0001", workspace_generation="policy-generation-0001",
            display_name="Policy workspace",
        )
        self.principal = self.store.link_oauth_principal(
            owner_id=self.owner_id, issuer="https://identity.example.test/policy",
            subject="policy-owner-0001",
        )

    def _owner_context(self) -> dict:
        return self.store.create_context(
            owner_id=self.owner_id, binding_id=self.binding["binding_id"],
            expires_at_ms=self.now + 60_000,
        )

    def _assignment(self) -> dict:
        return self.store.assigned_read_only_policy_context(
            device_id=self.node["device_id"], workspace_id=self.binding["workspace_id"],
            workspace_generation=self.binding["workspace_generation"],
        )

    def _operations(self, *, task_id: str | None = None) -> tuple[dict, dict]:
        exec_intent = self.store.request_mcp_exec(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            binding_id=self.binding["binding_id"], task_id=task_id,
            argv=["node", "--version"], idempotency_key="policy-exec-0001",
            facade_contract=FACADE_CONTRACT,
        )
        read_intent = self.store.request_mcp_bounded_file_read(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            binding_id=self.binding["binding_id"], task_id=task_id,
            path="README.md", start_line=1, max_lines=5, max_bytes=1024,
            idempotency_key="policy-read-0001", facade_contract=FACADE_CONTRACT,
        )
        return exec_intent, read_intent

    def _authority_rows(self) -> dict:
        with self.store._connection() as connection:
            return {
                name: [tuple(row) for row in connection.execute(f"SELECT * FROM {name} ORDER BY rowid")]
                for name in (
                    "contexts", "work_requests", "actions", "events", "mcp_exec_intents",
                    "mcp_file_read_intents", "mcp_task_sessions", "mcp_task_action_links",
                    "mcp_task_writer_leases",
                )
            }

    def test_owner_assignment_survives_generated_exec_and_read_contexts(self) -> None:
        context = self._owner_context()
        self._operations()
        self.assertEqual(len(self.store.list_contexts(owner_id=self.owner_id)), 3)
        self.assertEqual(self._assignment()["context_id"], context["context_id"])

    def test_multiple_owner_assignments_still_conflict_with_operation_contexts(self) -> None:
        self._owner_context()
        self._owner_context()
        self._operations()
        with self.assertRaisesRegex(ConflictError, "ambiguous"):
            self._assignment()

    def test_operation_contexts_alone_are_not_a_policy_assignment(self) -> None:
        self._operations()
        before = self._authority_rows()
        with self.assertRaisesRegex(NotFoundError, "no live read-only policy assignment"):
            self._assignment()
        self.assertEqual(self._authority_rows(), before)

    def test_assignment_lookup_preserves_live_task_and_action_authority(self) -> None:
        context = self._owner_context()
        task = self.store.create_mcp_task_session(
            owner_id=self.owner_id, principal_id=self.principal["principal_id"],
            binding_id=self.binding["binding_id"], label="Active operation task",
        )
        intents = self._operations(task_id=task["task_id"])
        before = self._authority_rows()
        self.assertEqual(self._assignment()["context_id"], context["context_id"])
        self.assertEqual(self._authority_rows(), before)
        for intent in intents:
            action = self.store.action(owner_id=self.owner_id, action_id=intent["action_id"])
            self.assertEqual(action["delivery_state"], "queued")
            self.assertIsNone(self.store.context(
                owner_id=self.owner_id, context_id=action["context_id"], require_live=True,
            )["closed_at_ms"])
        self.assertEqual(
            self.store.mcp_exec_intent_for_delivery(action_id=intents[0]["action_id"])["task_id"],
            task["task_id"],
        )

    def test_compact_metadata_intent_keeps_its_owner_assignment(self) -> None:
        context = self._owner_context()
        self.store.request_mcp_read_only_workspace_context(
            owner_id=self.owner_id, context_id=context["context_id"],
            principal_id=self.principal["principal_id"],
            idempotency_key="policy-metadata-0001", expires_at_ms=self.now + 30_000,
            facade_contract=FACADE_CONTRACT,
        )
        self._operations()
        self.assertEqual(self._assignment()["context_id"], context["context_id"])

    def test_inconsistent_intent_request_is_not_treated_as_generated_authority(self) -> None:
        context = self._owner_context()
        exec_intent, _ = self._operations()
        other_request = self.store.create_work_request(
            owner_id=self.owner_id, context_id=context["context_id"],
            objective="Unrelated owner request", criteria={}, scope={},
            expires_at_ms=self.now + 30_000,
        )
        with self.store._connection() as connection:
            connection.execute(
                "UPDATE mcp_exec_intents SET request_id = ? WHERE action_id = ?",
                (other_request["request_id"], exec_intent["action_id"]),
            )
        with self.assertRaisesRegex(ConflictError, "ambiguous"):
            self._assignment()


if __name__ == "__main__":
    unittest.main()
