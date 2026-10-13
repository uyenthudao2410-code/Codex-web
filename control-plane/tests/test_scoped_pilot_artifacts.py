"""Private service document/artifact lanes retain scoped pilot authority."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from control_plane.mcp_facade import ControlPlaneMcpFacade
from control_plane.store import ConflictError, ControlPlaneStore


class ScopedPilotArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="scoped-pilot-artifacts-")
        self.addCleanup(temporary.cleanup)
        self.now = 1_700_000_000_000
        self.store = ControlPlaneStore(Path(temporary.name) / "control.sqlite3", clock=lambda: self.now)
        self.store.enroll_node(owner_id="owner_default", device_id="device-documents",
                               endpoint_id="endpoint-documents", display_name="Document node")
        for workspace in ("documents", "other"):
            self.store.register_node_workspace(
                device_id="device-documents", workspace_id="workspace-" + workspace,
                workspace_generation="generation-1", display_name=workspace,
                capabilities={"read": True, "write": True, "exec": True},
            )
        self.binding = self.store.create_binding(
            owner_id="owner_default", device_id="device-documents", workspace_id="workspace-documents",
            workspace_generation="generation-1", display_name="Documents",
        )["binding_id"]
        self.other_binding = self.store.create_binding(
            owner_id="owner_default", device_id="device-documents", workspace_id="workspace-other",
            workspace_generation="generation-1", display_name="Other",
        )["binding_id"]
        self.principal = self.store.create_private_tunnel_service_principal(owner_id="owner_default")["principal_id"]
        self.store.heartbeat(
            device_id="device-documents", endpoint_id="endpoint-documents", runtime_instance_id="runtime-documents",
            mcp_server_instance_id="server-documents", activation_epoch="epoch-documents",
            contract_version="smart-v3", readiness="ready",
        )
        self.store.set_admission_mode(mode="recovery")
        self.decision = self.store.create_scoped_pilot_decision(
            owner_id="owner_default", principal_id=self.principal, binding_id=self.binding,
            expires_at_ms=self.now + 120_000, reason="Document and artifact pilot",
        )
        self.store.set_admission_mode(mode="scoped_pilot")
        self.facade = ControlPlaneMcpFacade(
            self.store, auth_kind="private_tunnel_service", oauth_scopes=("control-plane.inventory",),
            oauth_file_read_enabled=True, oauth_patch_write_scope="control-plane.patch",
            oauth_approved_patch_enabled=True, oauth_standing_write_enabled=True, oauth_exec_enabled=True,
        )
        self.contract = {key: self.facade.contract[key] for key in ("schema_version", "profile", "sha256")}
        self.task = self._task()

    def _task(self) -> str:
        return self.store.create_mcp_task_session(
            owner_id="owner_default", principal_id=self.principal,
            binding_id=self.binding, label="Scoped document work",
        )["task_id"]

    def _document(self, key: str, **overrides: object) -> dict:
        arguments = {
            "owner_id": "owner_default", "principal_id": self.principal, "binding_id": self.binding,
            "task_id": self.task, "operation": "document_create", "target": "docs/created.txt",
            "content": "Scoped document content\n", "idempotency_key": key, "facade_contract": self.contract,
            **overrides,
        }
        return self.store.request_mcp_document_write(**arguments)

    def _artifact(self, key: str, **overrides: object) -> dict:
        return self.store.request_mcp_artifact(
            **{
                "owner_id": "owner_default", "principal_id": self.principal, "binding_id": self.binding,
                "task_id": self.task, "kind": "document", "path": "docs/created.txt",
                "idempotency_key": key, "facade_contract": self.contract, **overrides,
            }
        )

    def _action(self, intent: dict) -> dict:
        return self.store.action(owner_id="owner_default", action_id=intent["action_id"])

    def _poll(self, lane: str) -> list[dict]:
        return self.store.poll_actions(device_id="device-documents", lane=lane)

    def test_shared_mcp_doc_create_and_convert_queue_and_dispatch_original_actions(self) -> None:
        for operation, fields in (
            ("doc_create", {"target": "docs/created.txt", "content": "Created content\n"}),
            ("doc_convert", {"source": "docs/created.txt", "target": "docs/converted.docx"}),
        ):
            with self.subTest(operation=operation):
                arguments = {
                    "operation": operation, "binding_id": self.binding, "task_id": self.task,
                    "idempotency_key": "document-facade-" + operation,
                    "expected_facade_contract": self.contract, **fields,
                }
                response = self.facade.handle(
                    {"jsonrpc": "2.0", "id": operation, "method": "tools/call",
                     "params": {"name": "document_workflow", "arguments": arguments}},
                    owner_id="owner_default", principal_id=self.principal, granted_context_id=None,
                    oauth_scopes=frozenset({"control-plane.inventory", "control-plane.read", "control-plane.patch"}),
                )
                self.assertIsNotNone(response)
                self.assertNotIn("error", response)
                self.assertIsNot(response["result"].get("isError"), True, response["result"].get("structuredContent"))
                intent = response["result"]["structuredContent"]
                action_id = intent["action_id"]
                action = self._action(intent)
                self.assertEqual(action["scoped_pilot_decision_id"], self.decision["decision_id"])
                delivered = self._poll("document_write")
                self.assertEqual([row["action_id"] for row in delivered], [action_id])
                self.assertEqual(delivered[0]["mcp_document_write_task_id"], self.task)
                self.assertGreater(delivered[0]["mcp_document_write_writer_lease_generation"], 0)
                replay = self.facade.handle(
                    {"jsonrpc": "2.0", "id": operation, "method": "tools/call",
                     "params": {"name": "document_workflow", "arguments": arguments}},
                    owner_id="owner_default", principal_id=self.principal, granted_context_id=None,
                    oauth_scopes=frozenset({"control-plane.inventory", "control-plane.read", "control-plane.patch"}),
                )
                self.assertEqual(replay["result"]["structuredContent"]["action_id"], action_id)
                self.assertEqual(self._poll("document_write"), [])

    def test_document_write_cannot_use_another_binding_principal_or_closed_task(self) -> None:
        another_principal = self.store.create_private_tunnel_service_principal(owner_id="owner_default")["principal_id"]
        for key, fields in (
            ("wrong-binding", {"binding_id": self.other_binding}),
            ("wrong-principal", {"principal_id": another_principal}),
        ):
            with self.subTest(key=key), self.assertRaises(ConflictError):
                self._document("document-" + key, **fields)
        self.store.close_mcp_task_session(owner_id="owner_default", principal_id=self.principal, task_id=self.task)
        with self.assertRaises(ConflictError):
            self._document("document-closed-task")
        self.assertEqual(self.store.health()["counts"]["actions"], 0)

    def test_competing_writer_blocks_intake_and_released_writer_blocks_delivery(self) -> None:
        other_task = self._task()
        self.store.claim_mcp_task_writer_lease(owner_id="owner_default", principal_id=self.principal, task_id=other_task)
        with self.assertRaises(ConflictError):
            self._document("document-writer-conflict")
        self.store.release_mcp_task_writer_lease(owner_id="owner_default", principal_id=self.principal, task_id=other_task)
        intent = self._document("document-writer-current")
        self.store.release_mcp_task_writer_lease(owner_id="owner_default", principal_id=self.principal, task_id=self.task)
        self.store.claim_mcp_task_writer_lease(owner_id="owner_default", principal_id=self.principal, task_id=other_task)
        self.assertEqual(self._poll("document_write"), [])
        self.assertEqual(self._action(intent)["delivery_state"], "settled")

    def test_document_and_image_reads_are_pilot_pinned_with_and_without_tasks(self) -> None:
        for kind in ("document", "image"):
            for task_id in (self.task, None):
                with self.subTest(kind=kind, task_id=task_id):
                    intent = self._artifact(
                        f"artifact-{kind}-{'task' if task_id else 'without-task'}", kind=kind,
                        path="docs/input.txt" if kind == "document" else "assets/image.png", task_id=task_id,
                    )
                    self.assertEqual(self._action(intent)["scoped_pilot_decision_id"], self.decision["decision_id"])
                    self.assertEqual([row["action_id"] for row in self._poll("bounded_artifact")], [intent["action_id"]])

    def test_artifact_cannot_retarget_and_closed_task_never_dispatches(self) -> None:
        with self.assertRaises(ConflictError):
            self._artifact("artifact-wrong-binding", binding_id=self.other_binding)
        intent = self._artifact("artifact-task-to-close")
        self.store.close_mcp_task_session(owner_id="owner_default", principal_id=self.principal, task_id=self.task)
        self.assertEqual(self._poll("bounded_artifact"), [])
        self.assertEqual(self._action(intent)["delivery_state"], "queued")

    def test_pilot_revocation_fences_both_lanes_even_after_global_open(self) -> None:
        self._document("document-before-revoke")
        self._artifact("artifact-before-revoke")
        self.store.revoke_scoped_pilot_decision(owner_id="owner_default", decision_id=self.decision["decision_id"])
        self.store.set_admission_mode(mode="open")
        self.assertEqual(self._poll("document_write"), [])
        self.assertEqual(self._poll("bounded_artifact"), [])
        with self.assertRaises(ConflictError):
            self._document("document-after-revoke")
        with self.assertRaises(ConflictError):
            self._artifact("artifact-after-revoke")

    def test_pilot_expiry_fences_both_lanes_with_a_fresh_ready_node(self) -> None:
        self._document("document-before-expiry")
        self._artifact("artifact-before-expiry")
        self.now = self.decision["expires_at_ms"]
        self.store.heartbeat(
            device_id="device-documents", endpoint_id="endpoint-documents", runtime_instance_id="runtime-documents",
            mcp_server_instance_id="server-documents", activation_epoch="epoch-documents",
            contract_version="smart-v3", readiness="ready",
        )
        self.store.set_admission_mode(mode="open")
        self.assertEqual(self._poll("document_write"), [])
        self.assertEqual(self._poll("bounded_artifact"), [])

    def test_missing_action_or_task_pilot_lineage_is_never_global_authority(self) -> None:
        document = self._document("document-lost-lineage")
        artifact = self._artifact("artifact-lost-lineage", task_id=None)
        with self.store._connection() as connection:
            connection.execute("UPDATE actions SET scoped_pilot_decision_id=NULL WHERE action_id=?", (artifact["action_id"],))
            connection.execute("UPDATE mcp_task_sessions SET scoped_pilot_decision_id=NULL WHERE task_id=?", (self.task,))
        self.store.set_admission_mode(mode="open")
        self.assertEqual(self._poll("document_write"), [])
        self.assertEqual(self._poll("bounded_artifact"), [])
        self.assertEqual(self._action(document)["delivery_state"], "queued")


if __name__ == "__main__":
    unittest.main()
