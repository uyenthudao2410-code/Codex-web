from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from control_plane.mcp_facade import ControlPlaneMcpFacade
from control_plane.store import ControlPlaneStore


SCOPE = "control-plane.inventory"
ISSUER = "https://identity.example.test/tenant-one"


class McpFileReadFacadeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mcp-file-read-facade-")
        self.addCleanup(self.temporary.cleanup)
        self.now = 1_700_000_000_000
        self.store = ControlPlaneStore(Path(self.temporary.name) / "control.sqlite3", clock=lambda: self.now)
        self.owner_id = "owner-default"
        self.node = self.store.enroll_node(
            owner_id=self.owner_id,
            device_id="file-read-node-0001",
            endpoint_id="file-read-endpoint-0001",
            display_name="File read node",
        )
        self.store.register_node_workspace(
            device_id=self.node["device_id"],
            workspace_id="file-read-workspace-0001",
            workspace_generation="file-read-generation-0001",
            display_name="File read workspace",
            capabilities={"read": True, "write": False, "exec": False},
        )
        self.binding = self.store.create_binding(
            owner_id=self.owner_id,
            device_id=self.node["device_id"],
            workspace_id="file-read-workspace-0001",
            workspace_generation="file-read-generation-0001",
            display_name="File read workspace",
        )
        self.principal = self.store.link_oauth_principal(
            owner_id=self.owner_id,
            issuer=ISSUER,
            subject="provider-subject-file-read-owner",
        )
        self.facade = ControlPlaneMcpFacade(
            self.store,
            oauth_scopes=(SCOPE,),
            oauth_file_read_enabled=True,
        )

    def call(self, arguments: dict, *, owner_id: str | None = None, principal_id: str | None = None) -> dict:
        response = self.facade.handle(
            {
                "jsonrpc": "2.0",
                "id": "mcp-file-read-call-0001",
                "method": "tools/call",
                "params": {"name": "workspace_context", "arguments": arguments},
            },
            owner_id=owner_id or self.owner_id,
            principal_id=principal_id or self.principal["principal_id"],
            granted_context_id=None,
        )
        assert response is not None
        return response

    def read_arguments(self, *, key: str = "idempotency-file-read-0001") -> dict:
        return {
            "operation": "read_file",
            "binding_id": self.binding["binding_id"],
            "path": "fixture.txt",
            "start_line": 1,
            "max_lines": 20,
            "max_bytes": 1024,
            "idempotency_key": key,
            "expected_facade_contract": {
                key: self.facade.contract[key] for key in ("schema_version", "profile", "sha256")
            },
        }

    def ready_node(self) -> None:
        self.store.heartbeat(
            device_id=self.node["device_id"],
            endpoint_id="file-read-endpoint-0001",
            runtime_instance_id="runtime-file-read-0001",
            mcp_server_instance_id="mcp-file-read-0001",
            activation_epoch="epoch-file-read-0001",
            contract_version="sha256:" + "a" * 64,
            readiness="ready",
        )

    def completed_payload(self, action_id: str, attempt_id: str, content: str = "line one\nline two\n") -> dict:
        content_bytes = content.encode("utf-8")
        file = {
            "path": "fixture.txt",
            "content": content,
            "content_sha256": hashlib.sha256(content_bytes).hexdigest(),
            "encoding": "utf-8",
            "start_line": 1,
            "end_line": len(content.splitlines()),
            "total_lines": len(content.splitlines()),
            "total_bytes": len(content_bytes),
            "bytes_read": len(content_bytes),
            "truncated": False,
            "next_start_line": None,
        }
        response_sha256 = hashlib.sha256(
            json.dumps(file, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()
        return {
            "schema_version": 1,
            "operation_kind": "control_plane_bounded_file_read",
            "file_accessed": True,
            "local_handle": "cp_fr_" + "b" * 48,
            "policy_sha256": "c" * 64,
            "actor": {
                "client_id": "electron-control-plane-file-read-bridge",
                "client_type": "electron",
            },
            "runtime_identity": {
                "activation_epoch_id": "epoch-file-read-0001",
                "process_instance_id": "runtime-file-read-0001",
                "server_instance_id": "mcp-file-read-0001",
                "tool_contract_sha256": "a" * 64,
            },
            "facade_contract": {
                key: self.facade.contract[key] for key in ("schema_version", "profile", "sha256")
            },
            "file": file,
            "response_sha256": response_sha256,
        }

    def test_file_read_is_account_scoped_and_delivered_only_to_the_new_lane(self) -> None:
        queued = self.call(self.read_arguments())
        result = queued["result"]["structuredContent"]
        self.assertEqual(result["execution"], "queued_for_local_admission")
        self.assertFalse(result["file_accessed"])
        action_id = result["action_id"]

        self.ready_node()
        self.assertEqual(self.store.poll_actions(device_id=self.node["device_id"], lane="generic"), [])
        deliveries = self.store.poll_actions(device_id=self.node["device_id"], lane="bounded_file_read")
        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries[0]["action_id"], action_id)
        self.assertEqual(deliveries[0]["mcp_file_read_intent_digest"], result["intent_digest"])
        self.assertNotIn("mcp_read_only_intent_digest", {key: value for key, value in deliveries[0].items() if value is not None})

        self.store.record_receipt(
            device_id=self.node["device_id"],
            action_id=action_id,
            attempt_id=deliveries[0]["attempt_id"],
            receipt_state="completed",
            local_handle="cp_fr_" + "b" * 48,
            payload=self.completed_payload(action_id, deliveries[0]["attempt_id"]),
        )
        observed = self.call({"operation": "read_status", "action_id": action_id})
        content = observed["result"]["structuredContent"]
        self.assertEqual(content["execution"], "completed_file_read_relay")
        self.assertTrue(content["file_accessed"])
        self.assertEqual(content["file_read"]["file"]["content"], "line one\nline two\n")
        self.assertNotIn("runtime_identity", content["file_read"])
        self.assertNotIn("policy_sha256", content["file_read"])

    def test_other_oauth_principal_cannot_observe_a_file_read_and_sensitive_receipts_are_not_relayed(self) -> None:
        queued = self.call(self.read_arguments())
        action_id = queued["result"]["structuredContent"]["action_id"]
        self.ready_node()
        delivery = self.store.poll_actions(device_id=self.node["device_id"], lane="bounded_file_read")[0]
        secret_payload = self.completed_payload(
            action_id,
            delivery["attempt_id"],
            "token = sk-example-secret-value-123456789\n",
        )
        self.store.record_receipt(
            device_id=self.node["device_id"],
            action_id=action_id,
            attempt_id=delivery["attempt_id"],
            receipt_state="completed",
            local_handle="cp_fr_" + "b" * 48,
            payload=secret_payload,
        )
        owner_b = "owner-other"
        principal_b = self.store.link_oauth_principal(
            owner_id=owner_b,
            issuer=ISSUER,
            subject="provider-subject-file-read-other",
        )
        foreign = self.call(
            {"operation": "read_status", "action_id": action_id},
            owner_id=owner_b,
            principal_id=principal_b["principal_id"],
        )
        self.assertEqual(foreign["error"]["data"]["code"], "NOT_FOUND")

        owner_status = self.call({"operation": "read_status", "action_id": action_id})
        content = owner_status["result"]["structuredContent"]
        self.assertFalse(content["file_accessed"])
        self.assertNotIn("file_read", content)


if __name__ == "__main__":
    unittest.main()
