from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from control_plane.node_agent import main as node_agent_main


class WorkspaceReplacementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(prefix="workspace-replacement-")
        self.root = Path(self.tempdir.name)
        self.workspace = self.root / "fixture-workspace"
        self.workspace.mkdir()
        self.config = self.root / "node.json"
        self.registry = self.root / "control-plane-workspaces.json"
        self.data_root = self.root / "profile"
        self.data_root.mkdir()
        self.config.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-replace-0001",
            "endpoint_id": "endpoint-replace-0001",
            "node_secret": "node-secret-replacement-test",
        }), encoding="utf-8")
        self.registry.write_text(json.dumps({
            "schema_version": 1,
            "entries": [{
                "workspace_id": "workspace-replace-0001",
                "workspace_generation": "generation-replace-old-0001",
                "canonical_path": str(self.workspace.resolve()),
                "display_name": "fixture-workspace",
                "capabilities": {"read": True, "write": False, "exec": False},
                "created_at_ms": 1_700_000_000_000,
            }],
        }), encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def args(self, *, confirm: bool = True, write: bool = True, execute: bool = True) -> list[str]:
        value = [
            "replace-workspace",
            "--config", str(self.config),
            "--workspace-registry", str(self.registry),
            "--workspace-path", str(self.workspace),
            "--display-name", "fixture-workspace",
            "--capability-read",
            "--project-root", str(self.root),
            "--node", "node",
            "--runtime-mode", "development",
            "--data-root", str(self.data_root),
        ]
        if write:
            value.insert(value.index("--project-root"), "--capability-write")
        if execute:
            value.insert(value.index("--project-root"), "--capability-exec")
        if confirm:
            value.insert(value.index("--project-root"), "--confirm-replace")
        return value

    @staticmethod
    def retirement_response() -> dict[str, object]:
        return {
            "device_id": "device-replace-0001",
            "workspace_id": "workspace-replace-0001",
            "workspace_generation": "generation-replace-old-0001",
            "display_name": "fixture-workspace",
            "capabilities": {"read": True, "write": False, "exec": False},
            "registered_at_ms": 1_700_000_000_000,
            "retired_at_ms": 1_700_000_000_100,
            "replayed": False,
        }

    @staticmethod
    def registration_response(*, generation: str, replayed: bool = False, malformed: bool = False) -> dict[str, object]:
        value = {
            "device_id": "device-replace-0001",
            "workspace_id": "workspace-replace-0001",
            "workspace_generation": generation,
            "display_name": "fixture-workspace",
            "capabilities": {"read": True, "write": True, "exec": True},
            "registered_at_ms": 1_700_000_000_200,
            "retired_at_ms": None,
            "replayed": replayed,
        }
        if malformed:
            value["retired_at_ms"] = 1_700_000_000_201
        return value

    def invoke(self, argv: list[str]) -> tuple[int, str, str]:
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = node_agent_main(argv)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_replacement_retire_registers_new_generation_before_local_commit(self) -> None:
        calls: list[tuple[str, dict[str, object]]] = []
        (self.data_root / "control-plane-exec-policy.json").write_text(json.dumps({
            "schema_version": 2,
            "enabled": True,
            "authority_mode": "standing",
            "server_origin": "https://control.example.test",
            "owner_id": "owner-replace-0001",
            "device_id": "device-replace-0001",
            "endpoint_id": "endpoint-replace-0001",
            "workspace_id": "workspace-replace-0001",
            "workspace_generation": "generation-replace-old-0001",
            "expires_at_ms": None,
            "facade_contract": {"schema_version": 1, "profile": "replace", "sha256": "a" * 64},
            "allowed_argv_prefixes": [["python"]],
            "max_timeout_ms": 5_000,
            "max_output_bytes": 1_024,
            "max_concurrent": 1,
        }), encoding="utf-8")

        def request(_origin: str, route: str, payload: dict[str, object], _auth: str) -> dict[str, object]:
            calls.append((route, payload))
            if route.endswith("/retire"):
                return self.retirement_response()
            return self.registration_response(generation=str(payload["workspace_generation"]))

        with mock.patch("control_plane.node_agent._request", side_effect=request):
            result, stdout, stderr = self.invoke(self.args())
        self.assertEqual(result, 0, stderr)
        receipt = json.loads(stdout)
        self.assertEqual(receipt["state"], "replaced")
        self.assertEqual(receipt["old_workspace_generation"], "generation-replace-old-0001")
        self.assertTrue(str(receipt["workspace_generation"]).startswith("generation_"))
        self.assertEqual(receipt["capabilities"], {"read": True, "write": True, "exec": True})
        self.assertEqual([route.rsplit("/", 1)[-1] for route, _ in calls], ["retire", "workspace-registrations"])
        self.assertNotIn("canonical_path", calls[0][1])
        self.assertNotIn(str(self.workspace), json.dumps(calls))
        registry = json.loads(self.registry.read_text(encoding="utf-8"))
        self.assertEqual(len(registry["entries"]), 1)
        self.assertEqual(registry["entries"][0]["workspace_generation"], receipt["workspace_generation"])
        self.assertEqual(registry["entries"][0]["capabilities"], receipt["capabilities"])
        self.assertFalse(json.loads((self.data_root / "control-plane-exec-policy.json").read_text(encoding="utf-8"))["enabled"])
        self.assertFalse((self.config.with_name(f"{self.config.name}.control-plane-workspace-replacement.json")).exists())

    def test_lost_registration_ack_resumes_register_phase_without_second_retire(self) -> None:
        calls: list[tuple[str, dict[str, object]]] = []
        registration_attempts = 0

        def request(_origin: str, route: str, payload: dict[str, object], _auth: str) -> dict[str, object]:
            nonlocal registration_attempts
            calls.append((route, payload))
            if route.endswith("/retire"):
                return self.retirement_response()
            registration_attempts += 1
            if registration_attempts == 1:
                return self.registration_response(generation=str(payload["workspace_generation"]), malformed=True)
            return self.registration_response(generation=str(payload["workspace_generation"]), replayed=True)

        with mock.patch("control_plane.node_agent._request", side_effect=request):
            first_result, _stdout, first_stderr = self.invoke(self.args())
            self.assertEqual(first_result, 1, first_stderr)
            journal_path = self.config.with_name(f"{self.config.name}.control-plane-workspace-replacement.json")
            journal = json.loads(journal_path.read_text(encoding="utf-8"))
            self.assertEqual(journal["phase"], "register_sent")
            old_registry = json.loads(self.registry.read_text(encoding="utf-8"))
            self.assertEqual(old_registry["entries"][0]["workspace_generation"], "generation-replace-old-0001")
            second_result, second_stdout, second_stderr = self.invoke(self.args())
        self.assertEqual(second_result, 0, second_stderr)
        receipt = json.loads(second_stdout)
        self.assertTrue(receipt["replayed"])
        self.assertEqual([route.rsplit("/", 1)[-1] for route, _ in calls], ["retire", "workspace-registrations", "workspace-registrations"])
        self.assertFalse(journal_path.exists())
        new_registry = json.loads(self.registry.read_text(encoding="utf-8"))
        self.assertEqual(new_registry["entries"][0]["workspace_generation"], receipt["workspace_generation"])

    def test_replacement_requires_explicit_confirmation(self) -> None:
        with mock.patch("control_plane.node_agent._request") as request:
            result, _stdout, stderr = self.invoke(self.args(confirm=False))
        self.assertEqual(result, 1)
        self.assertIn("CONTROL_PLANE_WORKSPACE_REPLACEMENT_CONFIRMATION_REQUIRED", stderr)
        request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
