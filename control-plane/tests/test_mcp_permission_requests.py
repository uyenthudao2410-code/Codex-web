from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import tempfile
import unittest
import zlib
from contextlib import closing
from pathlib import Path

from control_plane.mcp_facade import ControlPlaneMcpFacade
from control_plane.store import (
    ConflictError,
    ControlPlaneStore,
    MCP_PATCH_PERMISSION_VALIDATION_PROFILE,
    PermissionError,
    SCHEMA_VERSION,
    ValidationError,
)


ISSUER = "https://identity.example.test/tenant-permission"
SCOPE = "control-plane.inventory"
WRITE_SCOPE = "control-plane.patch"


class McpPermissionRequestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mcp-permission-request-")
        self.addCleanup(self.temporary.cleanup)
        self.now = 1_700_000_000_000
        self.store = ControlPlaneStore(Path(self.temporary.name) / "control.sqlite3", clock=lambda: self.now)
        self.owner_id = "owner-default"
        self.node = self.store.enroll_node(
            owner_id=self.owner_id,
            device_id="permission-node-0001",
            endpoint_id="permission-endpoint-0001",
            display_name="Permission node",
        )
        self.store.register_node_workspace(
            device_id=self.node["device_id"],
            workspace_id="permission-workspace-0001",
            workspace_generation="permission-generation-0001",
            display_name="Permission workspace",
            capabilities={"read": True, "write": True, "exec": False},
        )
        self.binding = self.store.create_binding(
            owner_id=self.owner_id,
            device_id=self.node["device_id"],
            workspace_id="permission-workspace-0001",
            workspace_generation="permission-generation-0001",
            display_name="Permission workspace",
        )
        self.principal = self.store.link_oauth_principal(
            owner_id=self.owner_id,
            issuer=ISSUER,
            subject="provider-subject-permission-owner",
        )
        self.facade = ControlPlaneMcpFacade(
            self.store,
            oauth_scopes=(SCOPE,),
            oauth_file_read_enabled=True,
            oauth_permission_requests_enabled=True,
            oauth_patch_write_scope=WRITE_SCOPE,
        )

    def _expected_contract(self) -> dict:
        return {key: self.facade.contract[key] for key in ("schema_version", "profile", "sha256")}

    def _request_arguments(self, *, key: str = "permission-request-key-0001") -> dict:
        return {
            "operation": "request_patch",
            "binding_id": self.binding["binding_id"],
            "path": "src/fixture.txt",
            "preimage_sha256": "a" * 64,
            "patch_sha256": "b" * 64,
            "validation_profile": MCP_PATCH_PERMISSION_VALIDATION_PROFILE,
            "idempotency_key": key,
            "expected_facade_contract": self._expected_contract(),
        }

    def _call(self, arguments: dict, *, principal_id: str | None = None, owner_id: str | None = None) -> dict:
        response = self.facade.handle(
            {
                "jsonrpc": "2.0",
                "id": "mcp-permission-request-0001",
                "method": "tools/call",
                "params": {"name": "request_permissions", "arguments": arguments},
            },
            owner_id=owner_id or self.owner_id,
            principal_id=principal_id or self.principal["principal_id"],
            granted_context_id=None,
            oauth_scopes=frozenset({SCOPE, WRITE_SCOPE}),
        )
        assert response is not None
        return response

    def _exact_patch(self, content: str = "updated fixture\n") -> str:
        payload = base64.b64encode(zlib.compress(content.encode("utf-8"))).decode("ascii")
        return "\n".join((
            "*** Begin Patch",
            "*** Write Exact File: src/fixture.txt",
            "@@ encoding=zlib-base64 preimage_sha256=" + "a" * 64 + " postimage_sha256="
            + hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "+" + payload,
            "*** End Patch",
            "",
        ))

    def _approved_permission(self, *, key: str = "permission-request-key-approved-patch") -> tuple[str, str]:
        patch = self._exact_patch()
        arguments = self._request_arguments(key=key)
        arguments["patch_sha256"] = hashlib.sha256(patch.encode("utf-8")).hexdigest()
        pending = self._call(arguments)
        request_id = pending["result"]["structuredContent"]["permission_request"]["permission_request_id"]
        self.store.approve_mcp_permission_request(owner_id=self.owner_id, permission_request_id=request_id)
        return request_id, patch

    def test_request_is_precise_but_creates_no_action_context_or_local_effect(self) -> None:
        response = self._call(self._request_arguments())
        content = response["result"]["structuredContent"]
        self.assertEqual(content["observation_kind"], "control_plane_patch_permission_request")
        self.assertEqual(content["execution"], "not_started")
        self.assertEqual(content["local_admission"], "not_requested")
        self.assertFalse(content["workspace_accessed"])
        request = content["permission_request"]
        self.assertEqual(request["state"], "pending")
        self.assertEqual(request["tool_name"], "agent_workflow")
        self.assertEqual(request["operation"], "apply_patch")
        self.assertEqual(request["path"], "src/fixture.txt")
        self.assertEqual(request["preimage_sha256"], "a" * 64)
        self.assertEqual(request["patch_sha256"], "b" * 64)
        self.assertNotIn("principal_id", request)
        self.assertNotIn("action_id", json.dumps(response))
        counts = self.store.health()["counts"]
        self.assertEqual(counts["mcp_permission_requests"], 1)
        self.assertEqual(counts["contexts"], 0)
        self.assertEqual(counts["work_requests"], 0)
        self.assertEqual(counts["actions"], 0)
        self.assertEqual(self.store.poll_actions(device_id=self.node["device_id"]), [])
        with closing(sqlite3.connect(self.store.path)) as connection:
            events = "\n".join(row[0] for row in connection.execute("SELECT details_json FROM events"))
        self.assertNotIn("src/fixture.txt", events)
        self.assertNotIn("a" * 64, events)
        self.assertNotIn("b" * 64, events)

    def test_idempotency_and_contract_pin_are_exact(self) -> None:
        first = self._call(self._request_arguments())
        first_request = first["result"]["structuredContent"]["permission_request"]
        self.assertFalse(first_request["replayed"])
        replay = self._call(self._request_arguments())
        replay_request = replay["result"]["structuredContent"]["permission_request"]
        self.assertTrue(replay_request["replayed"])
        self.assertEqual(replay_request["permission_request_id"], first_request["permission_request_id"])

        changed = self._request_arguments()
        changed["patch_sha256"] = "c" * 64
        conflict = self._call(changed)
        self.assertEqual(conflict["error"]["data"]["code"], "CONFLICT")
        self.assertEqual(self.store.health()["counts"]["mcp_permission_requests"], 1)

        stale_contract = self._request_arguments(key="permission-request-key-0002")
        stale_contract["expected_facade_contract"] = {**self._expected_contract(), "sha256": "d" * 64}
        rejected = self._call(stale_contract)
        self.assertEqual(rejected["error"]["data"]["code"], "CONTRACT_MISMATCH")
        self.assertEqual(self.store.health()["counts"]["mcp_permission_requests"], 1)

        malformed_path = self._request_arguments(key="permission-request-key-malformed-path")
        malformed_path["path"] = chr(0xD800)
        malformed = self._call(malformed_path)
        self.assertEqual(malformed["error"]["data"]["code"], "VALIDATION_ERROR")
        self.assertEqual(self.store.health()["counts"]["mcp_permission_requests"], 1)

    def test_approval_is_owner_scoped_and_still_has_no_execution_effect(self) -> None:
        pending = self._call(self._request_arguments())
        request_id = pending["result"]["structuredContent"]["permission_request"]["permission_request_id"]
        with self.assertRaises(PermissionError):
            self.store.approve_mcp_permission_request(owner_id="owner-other", permission_request_id=request_id)

        approved = self.store.approve_mcp_permission_request(owner_id=self.owner_id, permission_request_id=request_id)
        self.assertEqual(approved["state"], "approved")
        self.assertIsInstance(approved["decided_at_ms"], int)
        self.assertEqual(self.store.health()["counts"]["actions"], 0)
        self.assertEqual(self.store.poll_actions(device_id=self.node["device_id"]), [])

        observed = self._call({"operation": "status", "permission_request_id": request_id})
        status = observed["result"]["structuredContent"]
        self.assertEqual(status["execution"], "not_started")
        self.assertEqual(status["permission_request"]["state"], "approved")
        self.assertNotIn("local_handle", json.dumps(status))

    def test_request_and_approval_revalidate_the_current_write_target(self) -> None:
        no_write_node = self.store.enroll_node(
            owner_id=self.owner_id,
            device_id="permission-node-readonly-0001",
            endpoint_id="permission-endpoint-readonly-0001",
            display_name="Read only node",
        )
        self.store.register_node_workspace(
            device_id=no_write_node["device_id"],
            workspace_id="permission-workspace-readonly-0001",
            workspace_generation="permission-generation-readonly-0001",
            display_name="Read only workspace",
            capabilities={"read": True, "write": False, "exec": False},
        )
        no_write_binding = self.store.create_binding(
            owner_id=self.owner_id,
            device_id=no_write_node["device_id"],
            workspace_id="permission-workspace-readonly-0001",
            workspace_generation="permission-generation-readonly-0001",
            display_name="Read only workspace",
        )
        arguments = self._request_arguments(key="permission-request-key-readonly")
        arguments["binding_id"] = no_write_binding["binding_id"]
        rejected = self._call(arguments)
        self.assertEqual(rejected["error"]["data"]["code"], "FORBIDDEN")

        pending = self._call(self._request_arguments(key="permission-request-key-revoke"))
        request_id = pending["result"]["structuredContent"]["permission_request"]["permission_request_id"]
        self.store.revoke_binding(owner_id=self.owner_id, binding_id=self.binding["binding_id"])
        with self.assertRaises(ConflictError):
            self.store.approve_mcp_permission_request(owner_id=self.owner_id, permission_request_id=request_id)
        self.assertEqual(self.store.health()["counts"]["actions"], 0)

    def test_other_principal_cannot_observe_or_reuse_a_permission_request(self) -> None:
        pending = self._call(self._request_arguments())
        request_id = pending["result"]["structuredContent"]["permission_request"]["permission_request_id"]
        other = self.store.link_oauth_principal(
            owner_id=self.owner_id,
            issuer=ISSUER,
            subject="provider-subject-permission-other",
        )
        observed = self._call(
            {"operation": "status", "permission_request_id": request_id},
            principal_id=other["principal_id"],
        )
        self.assertEqual(observed["error"]["data"]["code"], "NOT_FOUND")

        foreign = self._request_arguments()
        foreign["idempotency_key"] = "permission-request-key-other"
        foreign_response = self._call(foreign, principal_id=other["principal_id"])
        self.assertEqual(foreign_response["result"]["structuredContent"]["permission_request"]["state"], "pending")
        self.assertEqual(self.store.health()["counts"]["mcp_permission_requests"], 2)

    def test_v14_database_gains_permission_request_table_without_rewriting_history(self) -> None:
        legacy_path = Path(self.temporary.name) / "v14-permission-requests.sqlite3"
        ControlPlaneStore(legacy_path, clock=lambda: self.now)
        with closing(sqlite3.connect(legacy_path)) as connection:
            connection.execute("DROP TABLE mcp_permission_requests")
            connection.execute("PRAGMA user_version = 14")
            connection.commit()

        migrated = ControlPlaneStore(legacy_path, clock=lambda: self.now)
        self.assertEqual(migrated.health()["schema_version"], SCHEMA_VERSION)
        self.assertEqual(migrated.health()["counts"]["mcp_permission_requests"], 0)
        with closing(sqlite3.connect(legacy_path)) as connection:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            indices = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'index'")}
        self.assertIn("mcp_permission_requests", tables)
        self.assertIn("mcp_permission_requests_owner_state_idx", indices)

    def test_permission_tool_is_opt_in_and_does_not_make_other_mutation_tools_available(self) -> None:
        tools = self.facade.handle(
            {"jsonrpc": "2.0", "id": "tools-list-permission-0001", "method": "tools/list", "params": {}},
            owner_id=self.owner_id,
            principal_id=self.principal["principal_id"],
            granted_context_id=None,
        )
        assert tools is not None
        by_name = {tool["name"]: tool for tool in tools["result"]["tools"]}
        self.assertEqual(by_name["request_permissions"]["_meta"]["control_plane"]["capability_state"], "permission_request_candidate")
        self.assertEqual(by_name["request_permissions"]["_meta"]["control_plane"]["execution"], "no_local_execution")
        self.assertEqual(by_name["agent_workflow"]["_meta"]["control_plane"]["capability_state"], "unavailable")
        self.assertEqual(by_name["exec_command"]["_meta"]["control_plane"]["reason"], "LOCAL_ADMISSION_BRIDGE_REQUIRED")

        disabled = ControlPlaneMcpFacade(
            self.store,
            oauth_scopes=(SCOPE,),
            oauth_file_read_enabled=True,
        )
        disabled_tools = disabled.handle(
            {"jsonrpc": "2.0", "id": "tools-list-permission-disabled-0001", "method": "tools/list", "params": {}},
            owner_id=self.owner_id,
            principal_id=self.principal["principal_id"],
            granted_context_id=None,
        )
        assert disabled_tools is not None
        disabled_by_name = {tool["name"]: tool for tool in disabled_tools["result"]["tools"]}
        self.assertEqual(disabled_by_name["request_permissions"]["_meta"]["control_plane"]["capability_state"], "unavailable")

    def test_approved_patch_seals_exact_permission_into_its_own_delivery_lane(self) -> None:
        permission_request_id, patch = self._approved_permission()
        contract = self._expected_contract()
        queued = self.store.request_mcp_approved_patch(
            owner_id=self.owner_id,
            principal_id=self.principal["principal_id"],
            permission_request_id=permission_request_id,
            patch_envelope=patch,
            idempotency_key="approved-patch-action-key-0001",
            facade_contract=contract,
        )
        self.assertFalse(queued["replayed"])
        self.assertEqual(self.store.health()["counts"]["mcp_approved_patch_intents"], 1)
        observation = self.store.mcp_approved_patch_action_observation(
            owner_id=self.owner_id,
            principal_id=self.principal["principal_id"],
            action_id=queued["action_id"],
        )
        self.assertEqual(json.loads(observation["arguments_json"])["operation"], "apply_patch")
        self.assertNotIn(patch, json.dumps(observation))
        with closing(sqlite3.connect(self.store.path)) as connection:
            event_text = "\n".join(row[0] for row in connection.execute("SELECT details_json FROM events"))
            persisted_patch = connection.execute(
                "SELECT patch_envelope FROM mcp_approved_patch_intents WHERE action_id = ?",
                (queued["action_id"],),
            ).fetchone()[0]
        self.assertEqual(persisted_patch, patch)
        self.assertNotIn(patch, event_text)

        self.store.heartbeat(
            device_id=self.node["device_id"],
            endpoint_id="permission-endpoint-0001",
            runtime_instance_id="permission-runtime-0001",
            mcp_server_instance_id="permission-mcp-0001",
            activation_epoch="permission-epoch-0001",
            contract_version="sha256:" + "c" * 64,
            readiness="ready",
        )
        self.assertEqual(self.store.poll_actions(device_id=self.node["device_id"], lane="generic"), [])
        self.assertEqual(self.store.poll_actions(device_id=self.node["device_id"], lane="bounded_file_read"), [])
        deliveries = self.store.poll_actions(device_id=self.node["device_id"], lane="approved_patch")
        self.assertEqual(len(deliveries), 1)
        delivery = deliveries[0]
        self.assertEqual(delivery["action_id"], queued["action_id"])
        self.assertEqual(delivery["mcp_approved_patch_permission_request_id"], permission_request_id)
        self.assertEqual(delivery["mcp_approved_patch_envelope"], patch)
        self.assertNotIn("patch_envelope", json.loads(delivery["arguments_json"]))

        replay = self.store.request_mcp_approved_patch(
            owner_id=self.owner_id,
            principal_id=self.principal["principal_id"],
            permission_request_id=permission_request_id,
            patch_envelope=patch,
            idempotency_key="approved-patch-action-key-0001",
            facade_contract=contract,
        )
        self.assertTrue(replay["replayed"])
        self.assertEqual(replay["action_id"], queued["action_id"])

    def test_approved_patch_rejects_digest_or_scope_drift_without_queueing_effect(self) -> None:
        permission_request_id, patch = self._approved_permission(key="permission-request-key-patch-drift")
        contract = self._expected_contract()
        with self.assertRaises(ConflictError):
            self.store.request_mcp_approved_patch(
                owner_id=self.owner_id,
                principal_id=self.principal["principal_id"],
                permission_request_id=permission_request_id,
                patch_envelope=patch + " ",
                idempotency_key="approved-patch-action-key-drift-0001",
                facade_contract=contract,
            )
        self.assertEqual(self.store.health()["counts"]["actions"], 0)

        malformed = patch.replace("*** Write Exact File: src/fixture.txt", "*** Update File: src/fixture.txt")
        malformed_arguments = self._request_arguments(key="permission-request-key-malformed-envelope")
        malformed_arguments["patch_sha256"] = hashlib.sha256(malformed.encode("utf-8")).hexdigest()
        pending = self._call(malformed_arguments)
        malformed_request_id = pending["result"]["structuredContent"]["permission_request"]["permission_request_id"]
        self.store.approve_mcp_permission_request(owner_id=self.owner_id, permission_request_id=malformed_request_id)
        with self.assertRaises(ValidationError):
            self.store.request_mcp_approved_patch(
                owner_id=self.owner_id,
                principal_id=self.principal["principal_id"],
                permission_request_id=malformed_request_id,
                patch_envelope=malformed,
                idempotency_key="approved-patch-action-key-malformed-0001",
                facade_contract=contract,
            )
        self.assertEqual(self.store.health()["counts"]["actions"], 0)

    def test_v15_database_gains_approved_patch_intent_table_without_rewriting_history(self) -> None:
        legacy_path = Path(self.temporary.name) / "v15-approved-patch-intents.sqlite3"
        ControlPlaneStore(legacy_path, clock=lambda: self.now)
        with closing(sqlite3.connect(legacy_path)) as connection:
            connection.execute("DROP TABLE mcp_approved_patch_intents")
            connection.execute("PRAGMA user_version = 15")
            connection.commit()

        migrated = ControlPlaneStore(legacy_path, clock=lambda: self.now)
        self.assertEqual(migrated.health()["schema_version"], SCHEMA_VERSION)
        self.assertEqual(migrated.health()["counts"]["mcp_approved_patch_intents"], 0)
        with closing(sqlite3.connect(legacy_path)) as connection:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            indices = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'index'")}
        self.assertIn("mcp_approved_patch_intents", tables)
        self.assertIn("mcp_approved_patch_intents_action_idx", indices)


if __name__ == "__main__":
    unittest.main()
