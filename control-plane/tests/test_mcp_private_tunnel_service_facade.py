"""The shared private tunnel uses a service principal, not OAuth user identity."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from control_plane.mcp_facade import ControlPlaneMcpFacade, tool_contract
from control_plane.store import ControlPlaneStore


READ_SCOPE = "control-plane.inventory"
CONTENT_SCOPE = "control-plane.read"
WRITE_SCOPE = "control-plane.patch"


class PrivateTunnelServiceFacadeTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="mcp-private-service-")
        self.addCleanup(temporary.cleanup)
        self.store = ControlPlaneStore(Path(temporary.name) / "control.sqlite3")
        self.facade = ControlPlaneMcpFacade(
            self.store,
            auth_kind="private_tunnel_service",
            oauth_scopes=(READ_SCOPE,),
            oauth_file_read_enabled=True,
            oauth_patch_write_scope=WRITE_SCOPE,
            oauth_approved_patch_enabled=True,
            oauth_standing_write_enabled=True,
            oauth_exec_enabled=True,
        )

    def _call(self, name: str, arguments: dict, scopes: frozenset[str] | None) -> dict:
        response = self.facade.handle(
            {"jsonrpc": "2.0", "id": "private-service-call", "method": "tools/call",
             "params": {"name": name, "arguments": arguments}},
            owner_id="shared-service-owner",
            principal_id="shared-service-principal",
            granted_context_id=None,
            oauth_scopes=scopes,
        )
        assert response is not None
        return response

    def test_discovery_advertises_account_lanes_without_oauth_identity(self) -> None:
        contract = self.facade.contract
        self.assertEqual(contract["schema_version"], 32)
        self.assertEqual(contract["profile"], "control-plane-private-tunnel-service-v1")
        oauth_contract = tool_contract(
            oauth_scopes=(READ_SCOPE,), oauth_file_read_enabled=True,
            oauth_patch_write_scope=WRITE_SCOPE, oauth_approved_patch_enabled=True,
            oauth_standing_write_enabled=True, oauth_exec_enabled=True,
        )
        self.assertNotEqual(contract["sha256"], oauth_contract["sha256"])
        self.assertEqual(oauth_contract["tools"][0]["securitySchemes"],
                         [{"type": "oauth2", "scopes": [READ_SCOPE]}])
        by_name = {tool["name"]: tool for tool in contract["tools"]}
        self.assertEqual(by_name["workspace_context"]["_meta"]["control_plane"]["implemented_operations"],
                         ["inventory", "task_open", "task_list", "task_close", "read_file", "read_status"])
        self.assertEqual(by_name["agent_workflow"]["_meta"]["control_plane"]["implemented_operations"],
                         ["apply_patch", "patch_status"])
        self.assertEqual(by_name["exec_command"]["_meta"]["control_plane"]["implemented_operations"],
                         ["exec_run", "exec_status"])
        for tool in contract["tools"]:
            self.assertNotIn("securitySchemes", tool)
            self.assertNotIn("securitySchemes", tool["_meta"])
            self.assertEqual(tool["_meta"]["control_plane"]["access_scope"], "private_tunnel_service")
            self.assertNotIn("OAuth", json.dumps(tool))

        discovered = self.facade.handle(
            {"jsonrpc": "2.0", "id": "private-service-discover", "method": "server/discover"},
            owner_id="shared-service-owner", principal_id="shared-service-principal",
            granted_context_id=None, oauth_scopes=frozenset({READ_SCOPE}),
        )
        assert discovered is not None
        self.assertEqual(discovered["result"]["_meta"]["control_plane"]["access_scope"],
                         "private_tunnel_service")
        self.assertNotIn("OAuth", discovered["result"]["instructions"])

    def test_declared_scopes_do_not_authorize_service_calls(self) -> None:
        for verified_scopes in (None, frozenset()):
            with self.subTest(verified_scopes=verified_scopes):
                denied = self._call("workspace_context", {"operation": "inventory"}, verified_scopes)
                self.assertEqual(denied["result"]["structuredContent"]["code"], "SERVICE_SCOPE_REQUIRED")

    def test_private_service_permission_review_is_unavailable_as_tool_result(self) -> None:
        by_name = {tool["name"]: tool for tool in self.facade.contract["tools"]}
        self.assertEqual(
            by_name["request_permissions"]["_meta"]["control_plane"]["implemented_operations"],
            [],
        )
        denied = self._call("request_permissions", {}, frozenset({READ_SCOPE, CONTENT_SCOPE, WRITE_SCOPE}))
        self.assertNotIn("error", denied)
        self.assertTrue(denied["result"]["isError"])
        self.assertEqual(denied["result"]["structuredContent"]["code"], "LOCAL_ADMISSION_BRIDGE_REQUIRED")
        self.assertEqual(denied["result"]["structuredContent"]["execution"], "not_implemented")
        self.assertEqual(denied["result"]["structuredContent"]["tool_name"], "request_permissions")
        self.assertEqual(self.store.health()["counts"]["mcp_permission_requests"], 0)

    def test_shared_service_inventory_shows_only_live_bindings(self) -> None:
        targets = [
            {"binding_id": "bind-selected", "binding_state": "active", "workspace_state": "active", "node_state": "active"},
            {"binding_id": "bind-other", "binding_state": "active", "workspace_state": "active", "node_state": "active"},
            {"binding_id": "bind-revoked", "binding_state": "revoked", "workspace_state": "active", "node_state": "active"},
            {"binding_id": "bind-retired", "binding_state": "active", "workspace_state": "retired", "node_state": "active"},
            {"binding_id": "bind-dead-node", "binding_state": "active", "workspace_state": "active", "node_state": "revoked"},
        ]
        with mock.patch.object(self.store, "list_account_targets", return_value=targets):
            inventory = self._call("workspace_context", {"operation": "inventory"}, frozenset({READ_SCOPE}))
        self.assertEqual(inventory["result"]["structuredContent"]["targets"], targets[:2])
        with mock.patch.object(self.store, "list_account_targets", return_value=[]):
            empty = self._call("workspace_context", {"operation": "inventory"}, frozenset({READ_SCOPE}))
        self.assertEqual(empty["result"]["structuredContent"]["targets"], [])

    def test_write_and_exec_require_verified_write_scope(self) -> None:
        for name, arguments in (
            ("agent_workflow", {"operation": "patch_status", "action_id": "action-001"}),
            ("exec_command", {"operation": "exec_status", "action_id": "action-001"}),
        ):
            with self.subTest(name=name):
                denied = self._call(name, arguments, frozenset({READ_SCOPE, CONTENT_SCOPE}))
                self.assertEqual(denied["result"]["structuredContent"]["code"],
                                 "SERVICE_WRITE_SCOPE_REQUIRED")
                self.assertTrue(denied["result"]["isError"])

    def test_inventory_only_grant_cannot_read_content_or_command_output(self) -> None:
        for name, arguments in (
            ("workspace_context", {"operation": "read_status", "action_id": "action-001"}),
            ("workspace_context", {"operation": "read_file", "binding_id": "bind-001", "path": "README.md",
                                   "start_line": 1, "max_lines": 1, "max_bytes": 256,
                                   "idempotency_key": "read-001", "expected_facade_contract": {
                                       key: self.facade.contract[key] for key in ("schema_version", "profile", "sha256")
                                   }}),
            ("command_control", {"operation": "exec_output", "action_id": "action-001", "cursor": 0, "max_bytes": 256}),
            ("view_image", {"operation": "image_status", "action_id": "action-001"}),
        ):
            with self.subTest(name=name, operation=arguments["operation"]):
                denied = self._call(name, arguments, frozenset({READ_SCOPE}))
                self.assertEqual(denied["result"]["structuredContent"]["code"],
                                 "SERVICE_READ_SCOPE_REQUIRED")
                self.assertTrue(denied["result"]["isError"])

    def test_command_output_requires_write_scope_after_read_scope(self) -> None:
        denied = self._call(
            "command_control",
            {"operation": "exec_output", "action_id": "action-001", "cursor": 0, "max_bytes": 256},
            frozenset({READ_SCOPE, CONTENT_SCOPE}),
        )
        self.assertEqual(denied["result"]["structuredContent"]["code"],
                         "SERVICE_WRITE_SCOPE_REQUIRED")

    def test_read_only_service_grant_cannot_take_writer_lease_or_close_task(self) -> None:
        for name, arguments in (
            ("task_control", {"operation": "writer_claim", "task_id": "task_" + "a" * 32}),
            ("task_control", {"operation": "writer_release", "task_id": "task_" + "a" * 32}),
            ("workspace_context", {"operation": "task_close", "task_id": "task_" + "a" * 32}),
        ):
            with self.subTest(name=name, operation=arguments["operation"]):
                denied = self._call(name, arguments, frozenset({READ_SCOPE, CONTENT_SCOPE}))
                self.assertEqual(denied["result"]["structuredContent"]["code"],
                                 "SERVICE_WRITE_SCOPE_REQUIRED")

    def test_legacy_contract_is_unchanged(self) -> None:
        legacy = ControlPlaneMcpFacade(self.store)
        self.assertEqual(legacy.contract, tool_contract())
        self.assertEqual(legacy.contract["schema_version"], 8)
        self.assertEqual(legacy._access_scope, "server_issued_context_grant")
        self.assertEqual(legacy.contract["tools"][0]["_meta"]["control_plane"]["implemented_operations"],
                         ["status", "request_read_only"])

    def test_service_mode_requires_distinct_declared_scopes(self) -> None:
        with self.assertRaises(ValueError):
            ControlPlaneMcpFacade(self.store, auth_kind="")
        with self.assertRaises(ValueError):
            ControlPlaneMcpFacade(self.store, auth_kind="private_tunnel_service")
        with self.assertRaises(ValueError):
            ControlPlaneMcpFacade(
                self.store, auth_kind="private_tunnel_service", oauth_scopes=(READ_SCOPE,),
                oauth_file_read_enabled=True, oauth_patch_write_scope=READ_SCOPE,
                oauth_standing_write_enabled=True,
            )


if __name__ == "__main__":
    unittest.main()
