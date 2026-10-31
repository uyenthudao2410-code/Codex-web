"""Only an explicitly confirmed current local root may select central authority."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from control_plane.node_agent import main as node_agent_main


class NodeWorkspaceActivationCliTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="workspace-activation-cli-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.workspace = self.root / "Autocad"
        self.workspace.mkdir()
        self.config = self.root / "node.json"
        self.config.write_text(json.dumps({"server_url": "https://control.example.test", "device_id": "device-alpha",
            "endpoint_id": "endpoint-alpha", "node_secret": "node-secret-activation-test"}), encoding="utf-8")
        self.registry = self.root / "control-plane-workspaces.json"
        self.entry = {"workspace_id": "workspace-activation-0001", "workspace_generation": "generation-activation-0001",
            "canonical_path": str(self.workspace.resolve()), "display_name": "Autocad",
            "capabilities": {"read": True, "write": True, "exec": True}, "created_at_ms": 1_700_000_000_000}
        self.save_registry()
        self.response = {"device_id": "device-alpha", "workspace_id": self.entry["workspace_id"],
            "workspace_generation": self.entry["workspace_generation"], "binding_id": "bind_" + "a" * 32,
            "state": "active"}

    def save_registry(self, entries=None) -> None:
        self.registry.write_text(json.dumps({"schema_version": 1, "entries": [self.entry] if entries is None else entries}),
                                 encoding="utf-8")

    def args(self, *, confirm=True) -> list[str]:
        result = ["activate-workspace", "--config", str(self.config), "--workspace-registry", str(self.registry),
            "--workspace-id", self.entry["workspace_id"], "--workspace-generation", self.entry["workspace_generation"],
            "--project-root", str(self.root), "--runtime-mode", "development"]
        if confirm:
            result.append("--confirm-activate")
        return result

    def invoke(self, args=None) -> tuple[int, str, str]:
        output, errors = StringIO(), StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = node_agent_main(self.args() if args is None else args)
        return code, output.getvalue(), errors.getvalue()

    def test_confirmed_selection_sends_only_exact_ids_and_outputs_path_free_receipt(self) -> None:
        registry_before = self.registry.read_bytes()
        with mock.patch("control_plane.node_agent._request", return_value=self.response) as request:
            code, output, errors = self.invoke()
        self.assertEqual(code, 0, errors)
        self.assertEqual(json.loads(output), self.response)
        request.assert_called_once_with("https://control.example.test", "/v1/nodes/device-alpha/activate-workspace",
            {"workspace_id": self.entry["workspace_id"], "workspace_generation": self.entry["workspace_generation"],
             "confirm_activate": True}, "Node node-secret-activation-test")
        self.assertNotIn(str(self.workspace), output)
        self.assertNotIn("node-secret", output + errors)
        self.assertEqual(self.registry.read_bytes(), registry_before)

    def test_confirmation_missing_blocks_before_network(self) -> None:
        with mock.patch("control_plane.node_agent._request") as request:
            code, output, errors = self.invoke(self.args(confirm=False))
        self.assertEqual(code, 1)
        self.assertEqual(output, "")
        self.assertIn("CONTROL_PLANE_WORKSPACE_ACTIVATION_CONFIRMATION_REQUIRED", errors)
        request.assert_not_called()

    def test_missing_generation_or_missing_local_directory_blocks_before_network(self) -> None:
        with mock.patch("control_plane.node_agent._request") as request:
            args = self.args()
            args[args.index("--workspace-generation") + 1] = "generation-missing-0001"
            self.assertEqual(self.invoke(args)[0], 1)
            self.workspace.rmdir()
            self.assertEqual(self.invoke()[0], 1)
        request.assert_not_called()

    def test_response_identity_shape_lifetime_and_types_are_strict(self) -> None:
        invalids = [
            {**self.response, "device_id": "other-device"},
            {**self.response, "workspace_id": "other-workspace"},
            {**self.response, "workspace_generation": "other-generation"},
            {**self.response, "binding_id": "invalid"},
            {**self.response, "pilot_decision_id": "pilot_" + "b" * 32},
            {**self.response, "expires_at_ms": 1},
            {**self.response, "state": "active", "replayed": False},
            {k: v for k, v in self.response.items() if k != "state"},
            {**self.response, "state": "registered"},
            {**self.response, "workspace_path": str(self.workspace)},
        ]
        for response in invalids:
            with self.subTest(response=response), mock.patch("control_plane.node_agent._request", return_value=response):
                code, output, errors = self.invoke()
                self.assertEqual(code, 1)
                self.assertEqual(output, "")
                self.assertIn("CONTROL_PLANE_WORKSPACE_ACTIVATION_RESPONSE_INVALID", errors)
                self.assertNotIn("node-secret", errors)

    def test_local_root_removed_during_request_does_not_emit_success(self) -> None:
        def request(*args):
            self.save_registry(entries=[])
            return self.response
        with mock.patch("control_plane.node_agent._request", side_effect=request):
            code, output, errors = self.invoke()
        self.assertEqual(code, 1)
        self.assertEqual(output, "")
        self.assertIn("CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT", errors)

    def test_local_capability_changed_during_request_does_not_emit_success(self) -> None:
        def request(*args):
            self.entry = {**self.entry, "capabilities": {"read": True, "write": False, "exec": False}}
            self.save_registry()
            return self.response
        with mock.patch("control_plane.node_agent._request", side_effect=request):
            code, output, errors = self.invoke()
        self.assertEqual(code, 1)
        self.assertEqual(output, "")
        self.assertIn("CONTROL_PLANE_WORKSPACE_ACTIVATION_LOCAL_STATE_CHANGED", errors)

    def test_lost_response_is_not_automatically_replayed(self) -> None:
        with mock.patch("control_plane.node_agent._request", side_effect=RuntimeError("CONTROL_PLANE_REQUEST_FAILED")) as request:
            code, output, errors = self.invoke()
        self.assertEqual(code, 1)
        self.assertEqual(output, "")
        self.assertIn("CONTROL_PLANE_REQUEST_FAILED", errors)
        self.assertEqual(request.call_count, 1)
        with mock.patch("control_plane.node_agent._request", return_value=self.response) as retry:
            code, output, errors = self.invoke()
        self.assertEqual(code, 0, errors)
        self.assertEqual(json.loads(output), self.response)
        self.assertEqual(retry.call_count, 1)


if __name__ == "__main__":
    unittest.main()
