"""Tool failures give clients safe, actionable feedback without granting authority."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from control_plane.mcp_facade import ControlPlaneMcpFacade
from control_plane.store import ControlPlaneStore


READ_SCOPE = "control-plane.inventory"
CONTENT_SCOPE = "control-plane.read"
WRITE_SCOPE = "control-plane.patch"


class McpClientFeedbackTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="mcp-client-feedback-")
        self.addCleanup(temporary.cleanup)
        self.store = ControlPlaneStore(Path(temporary.name) / "control.sqlite3")
        self.owner_id = "feedback-owner"
        node = self.store.enroll_node(
            owner_id=self.owner_id,
            device_id="feedback-node-001",
            endpoint_id="feedback-endpoint-001",
            display_name="Feedback node",
        )
        self.store.register_node_workspace(
            device_id=node["device_id"],
            workspace_id="feedback-workspace-001",
            workspace_generation="feedback-generation-001",
            display_name="Feedback workspace",
            capabilities={"read": True, "write": False, "exec": False},
        )
        self.binding = self.store.create_binding(
            owner_id=self.owner_id,
            device_id=node["device_id"],
            workspace_id="feedback-workspace-001",
            workspace_generation="feedback-generation-001",
            display_name="Feedback workspace",
        )
        principal = self.store.link_oauth_principal(
            owner_id=self.owner_id,
            issuer="https://identity.example.test/feedback",
            subject="feedback-owner-subject",
        )
        self.principal_id = principal["principal_id"]
        self.facade = ControlPlaneMcpFacade(
            self.store, oauth_scopes=(READ_SCOPE,), oauth_file_read_enabled=True,
        )

    def private_facade(self, *, exec_enabled: bool = True) -> ControlPlaneMcpFacade:
        return ControlPlaneMcpFacade(
            self.store,
            auth_kind="private_tunnel_service",
            oauth_scopes=(READ_SCOPE,),
            oauth_file_read_enabled=True,
            oauth_patch_write_scope=WRITE_SCOPE,
            oauth_approved_patch_enabled=True,
            oauth_standing_write_enabled=True,
            oauth_exec_enabled=exec_enabled,
        )

    def handle(self, request: dict, *, facade: ControlPlaneMcpFacade | None = None) -> dict:
        response = (facade or self.facade).handle(
            request,
            owner_id=self.owner_id,
            principal_id=self.principal_id,
            granted_context_id=None,
            oauth_scopes=frozenset({READ_SCOPE, CONTENT_SCOPE, WRITE_SCOPE}),
        )
        assert response is not None
        return response

    def call(self, arguments: object, *, name: str = "workspace_context",
             facade: ControlPlaneMcpFacade | None = None) -> dict:
        return self.handle(
            {"jsonrpc": "2.0", "id": "feedback-call", "method": "tools/call",
             "params": {"name": name, "arguments": arguments}},
            facade=facade,
        )

    def read_arguments(self, *, facade: ControlPlaneMcpFacade | None = None) -> dict:
        contract = (facade or self.facade).contract
        return {
            "operation": "read_file",
            "binding_id": self.binding["binding_id"],
            "path": "fixture.txt",
            "idempotency_key": "feedback-file-read-001",
            "expected_facade_contract": {
                key: contract[key] for key in ("schema_version", "profile", "sha256")
            },
        }

    def error_feedback(self, response: dict, *, code: str, operation: str | None = None) -> dict:
        self.assertNotIn("error", response)
        result = response["result"]
        self.assertTrue(result["isError"])
        feedback = result["structuredContent"]
        self.assertEqual(feedback["code"], code)
        self.assertEqual(feedback["execution"], "not_started")
        self.assertEqual(feedback["tool_name"], "workspace_context")
        if operation is not None:
            self.assertEqual(feedback["operation"], operation)
        self.assertTrue(feedback["message"])
        self.assertTrue(feedback["next_action"])
        self.assertTrue(any(item.get("text") for item in result["content"] if item["type"] == "text"))
        return feedback

    def assert_no_actions(self) -> None:
        self.assertEqual(self.store.list_action_lifecycle(owner_id=self.owner_id), [])

    def test_inventory_contract_can_be_copied_into_a_read_and_replayed(self) -> None:
        inventory_result = self.call({"operation": "inventory"})["result"]
        self.assertFalse(inventory_result["isError"])
        inventory = inventory_result["structuredContent"]
        expected = {key: self.facade.contract[key] for key in ("schema_version", "profile", "sha256")}
        self.assertEqual(inventory["tool_contract"], expected)
        self.assertEqual(inventory["path_format"], "workspace_relative_posix")
        self.assertFalse(inventory["workspace_accessed"])
        self.assert_no_actions()

        arguments = self.read_arguments()
        arguments["expected_facade_contract"] = inventory["tool_contract"]
        first = self.call(arguments)["result"]
        self.assertFalse(first["isError"])
        queued = first["structuredContent"]
        self.assertEqual(queued["execution"], "queued_for_local_admission")
        self.assertFalse(queued["file_accessed"])
        replay = self.call(arguments)["result"]["structuredContent"]
        self.assertEqual(replay["action_id"], queued["action_id"])
        self.assertTrue(replay["replayed"])
        self.assertEqual(len(self.store.list_action_lifecycle(owner_id=self.owner_id)), 1)

    def test_reported_wrong_profile_and_local_runtime_hash_show_exact_mismatch(self) -> None:
        facade = self.private_facade()
        arguments = self.read_arguments(facade=facade)
        arguments["expected_facade_contract"] = {
            "schema_version": 32,
            "profile": "workspace_context",
            "sha256": "bc44c044a0b08dfdea80b8ba0dfcc080e180e21a5460dbf9726b49ac1fa769b0",
        }
        feedback = self.error_feedback(
            self.call(arguments, facade=facade), code="CONTRACT_MISMATCH", operation="read_file",
        )
        self.assertEqual(feedback["mismatch_fields"], ["profile", "sha256"])
        self.assertEqual(feedback["expected_facade_contract"], {
            key: facade.contract[key] for key in ("schema_version", "profile", "sha256")
        })
        self.assert_no_actions()

    def test_missing_required_fields_are_named_before_any_action_is_created(self) -> None:
        arguments = self.read_arguments()
        del arguments["idempotency_key"]
        del arguments["expected_facade_contract"]
        feedback = self.error_feedback(self.call(arguments), code="VALIDATION_ERROR", operation="read_file")
        self.assertEqual(feedback["validation"]["missing_fields"], ["expected_facade_contract", "idempotency_key"])
        self.assert_no_actions()

    def test_unexpected_nested_bounds_are_rejected_with_a_field_diagnostic(self) -> None:
        arguments = self.read_arguments()
        arguments["bounds"] = {"max_lines": 10}
        feedback = self.error_feedback(self.call(arguments), code="VALIDATION_ERROR", operation="read_file")
        self.assertEqual(feedback["validation"]["unexpected_fields"], ["<unknown>"])
        self.assert_no_actions()

    def test_known_fields_for_another_operation_are_named_and_still_rejected(self) -> None:
        arguments = {
            "operation": "task_open", "binding_id": self.binding["binding_id"],
            "label": "Feedback task", "idempotency_key": "feedback-task-open-001",
            "expected_facade_contract": self.read_arguments()["expected_facade_contract"],
        }
        feedback = self.error_feedback(self.call(arguments), code="VALIDATION_ERROR", operation="task_open")
        self.assertEqual(feedback["validation"]["unexpected_fields"], ["expected_facade_contract"])
        self.assertEqual(self.call({"operation": "task_list"})["result"]["structuredContent"]["tasks"], [])
        self.assert_no_actions()

    def test_wrong_types_and_operations_have_readable_field_diagnostics(self) -> None:
        for field, value in (("max_lines", None), ("max_lines", "20"),
                             ("operation", "read_directory"), ("operation", None),
                             ("operation", []), ("operation", {})):
            with self.subTest(field=field, value=value):
                arguments = self.read_arguments()
                arguments[field] = value
                feedback = self.error_feedback(self.call(arguments), code="VALIDATION_ERROR")
                self.assertIn(field, feedback["validation"]["invalid_fields"])
        self.assert_no_actions()

    def test_feedback_never_echoes_offending_values_or_arbitrary_unknown_keys(self) -> None:
        secret_marker = "secret-value-not-for-client-feedback"
        for arguments in (
            {**self.read_arguments(), secret_marker: secret_marker},
            {**self.read_arguments(), "operation": secret_marker},
            {**self.read_arguments(), "expected_facade_contract": secret_marker},
        ):
            with self.subTest(argument_names=[key for key in arguments if key != secret_marker]):
                response = self.call(arguments)
                self.error_feedback(response, code="VALIDATION_ERROR")
                self.assertNotIn(secret_marker, json.dumps(response))
        self.assert_no_actions()

    def test_absolute_and_parent_paths_remain_rejected_without_leaking_paths(self) -> None:
        for path in ("E:/DEV/Codex-web/control-plane/mcp_facade.py", "../fixture.txt", "private\\fixture.txt"):
            with self.subTest(path_kind=path.split("/")[0]):
                arguments = self.read_arguments()
                arguments["path"] = path
                response = self.call(arguments)
                feedback = self.error_feedback(response, code="VALIDATION_ERROR", operation="read_file")
                self.assertNotIn(path, json.dumps(feedback))
                self.assertIn("path", feedback["validation"]["invalid_fields"])
        self.assert_no_actions()

    def test_protocol_errors_and_unknown_tools_stay_json_rpc_errors(self) -> None:
        cases = (
            ({"jsonrpc": "1.0", "id": "bad-protocol", "method": "tools/call",
              "params": {"name": "workspace_context", "arguments": {"operation": "inventory"}}}, -32600),
            ({"jsonrpc": "2.0", "id": "bad-params", "method": "tools/call", "params": []}, -32602),
            ({"jsonrpc": "2.0", "id": "bad-arguments", "method": "tools/call",
              "params": {"name": "workspace_context", "arguments": []}}, -32602),
            ({"jsonrpc": "2.0", "id": "unknown-tool", "method": "tools/call",
              "params": {"name": "unknown_tool", "arguments": {}}}, -32602),
            ({"jsonrpc": "2.0", "id": "unknown-method", "method": "unknown/method"}, -32601),
        )
        for request, code in cases:
            with self.subTest(request_id=request["id"]):
                response = self.handle(request)
                self.assertEqual(response["error"]["code"], code)
                self.assertNotIn("result", response)
        self.assert_no_actions()

    def test_private_inventory_exposes_relay_availability_without_claiming_local_readiness(self) -> None:
        for enabled in (False, True):
            with self.subTest(exec_enabled=enabled):
                facade = self.private_facade(exec_enabled=enabled)
                with mock.patch.object(self.store, "list_account_targets", return_value=[]):
                    inventory = self.call({"operation": "inventory"}, facade=facade)["result"]["structuredContent"]
                capabilities = inventory["relay_capabilities"]
                self.assertFalse(inventory["workspace_accessed"])
                advertised = {tool["name"]: tool["_meta"]["control_plane"] for tool in facade.contract["tools"]}
                for name in ("workspace_context", "exec_command"):
                    relay = capabilities[name]
                    self.assertEqual(relay["capability_state"], advertised[name]["capability_state"])
                    self.assertEqual(relay["implemented_operations"], advertised[name].get("implemented_operations", []))
                self.assertEqual(capabilities["workspace_context"]["local_admission"], "unverified")
                self.assertEqual(capabilities["exec_command"]["local_admission"], "unverified" if enabled else "not_applicable")
                self.assertEqual(capabilities["exec_command"]["relay_enabled"], enabled)
                self.assertEqual("exec_run" in capabilities["exec_command"]["implemented_operations"], enabled)
        self.assert_no_actions()


if __name__ == "__main__":
    unittest.main()
