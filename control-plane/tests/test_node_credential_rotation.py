from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from control_plane import node_agent
from control_plane.store import ConflictError, ControlPlaneStore, PermissionError


class NodeCredentialRotationStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="node-credential-rotation-store-")
        self.addCleanup(self.temporary.cleanup)
        self.now = 1_700_000_000_000
        self.store = ControlPlaneStore(
            Path(self.temporary.name) / "control.sqlite3",
            clock=lambda: self.now,
        )
        enrolled = self.store.enroll_node(
            owner_id="owner_default",
            device_id="device-rotation",
            endpoint_id="endpoint-rotation",
            display_name="Rotation fixture",
        )
        self.current_secret = enrolled["node_secret"]
        self.next_secret = "next-node-credential-0000000001"
        self.rotation_id = "rotate_" + "a" * 32

    def _prepare(self) -> dict:
        return self.store.prepare_node_credential_rotation(
            device_id="device-rotation",
            node_secret=self.current_secret,
            rotation_id=self.rotation_id,
            current_generation=1,
            next_credential_hash=node_agent._credential_hash(self.next_secret),
        )

    def test_prepare_is_idempotent_and_does_not_switch_authentication(self) -> None:
        prepared = self._prepare()
        replayed = self._prepare()
        self.assertEqual(prepared, replayed)
        self.assertEqual(prepared["state"], "prepared")
        self.assertEqual(prepared["current_generation"], 1)
        self.assertEqual(prepared["next_generation"], 2)
        self.store.authenticate_node(device_id="device-rotation", node_secret=self.current_secret)
        with self.assertRaises(PermissionError):
            self.store.authenticate_node(device_id="device-rotation", node_secret=self.next_secret)

    def test_activate_accepts_both_credentials_until_new_credential_ack(self) -> None:
        self._prepare()
        activated = self.store.activate_node_credential_rotation(
            device_id="device-rotation",
            node_secret=self.current_secret,
            rotation_id=self.rotation_id,
        )
        self.assertEqual(activated["state"], "activated")
        self.store.authenticate_node(device_id="device-rotation", node_secret=self.current_secret)
        self.store.authenticate_node(device_id="device-rotation", node_secret=self.next_secret)
        status = self.store.node_enrollment_status(
            device_id="device-rotation",
            node_secret=self.next_secret,
        )
        self.assertEqual(status["credential_generation"], 2)

        completed = self.store.acknowledge_node_credential_rotation(
            device_id="device-rotation",
            node_secret=self.next_secret,
            rotation_id=self.rotation_id,
        )
        self.assertEqual(completed["state"], "completed")
        with self.assertRaises(PermissionError):
            self.store.authenticate_node(device_id="device-rotation", node_secret=self.current_secret)
        authenticated = self.store.authenticate_node(device_id="device-rotation", node_secret=self.next_secret)
        self.assertEqual(authenticated["credential_generation"], 2)
        self.assertEqual(
            self.store.acknowledge_node_credential_rotation(
                device_id="device-rotation",
                node_secret=self.next_secret,
                rotation_id=self.rotation_id,
            ),
            completed,
        )

    def test_second_rotation_is_blocked_until_first_is_completed(self) -> None:
        self._prepare()
        with self.assertRaises(ConflictError):
            self.store.prepare_node_credential_rotation(
                device_id="device-rotation",
                node_secret=self.current_secret,
                rotation_id="rotate_" + "b" * 32,
                current_generation=1,
                next_credential_hash=node_agent._credential_hash("another-next-node-credential-0001"),
            )


class NodeCredentialRotationAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="node-credential-rotation-agent-")
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "control-plane-node.json"
        self.current_secret = "current-node-credential-0000001"
        self.args = SimpleNamespace(config=str(self.path))

    def _config(self, **overrides: object) -> dict:
        result = {
            "schema_version": 1,
            "server_url": "http://127.0.0.1:8765",
            "device_id": "device-rotation-agent",
            "endpoint_id": "endpoint-rotation-agent",
            "display_name": "Rotation agent fixture",
            "node_secret": self.current_secret,
            "credential_generation": 1,
            "enrollment_state": "approved",
            "enrollment_id": "enroll_rotation_agent",
        }
        result.update(overrides)
        return result

    @staticmethod
    def _response(rotation_id: str, device_id: str, state: str, *, generation: int = 1) -> dict:
        return {
            "rotation_id": rotation_id,
            "device_id": device_id,
            "state": state,
            "current_generation": generation,
            "next_generation": generation + 1,
            "created_at_ms": 1_700_000_000_000,
            "activated_at_ms": 1_700_000_000_001 if state in {"activated", "completed"} else None,
            "completed_at_ms": 1_700_000_000_002 if state == "completed" else None,
        }

    def test_agent_runs_prepare_activate_promote_ack_without_printing_secret(self) -> None:
        node_agent._write_config(self.path, self._config())
        calls: list[tuple[str, str, dict, str | None]] = []
        def request(url: str, path: str, payload: dict, authorization: str | None = None) -> dict:
            calls.append((url, path, payload, authorization))
            if path.endswith("/prepare"):
                return self._response(payload["rotation_id"], "device-rotation-agent", "prepared")
            if path.endswith("/activate"):
                return self._response(payload["rotation_id"], "device-rotation-agent", "activated")
            if path.endswith("/ack"):
                return self._response(payload["rotation_id"], "device-rotation-agent", "completed")
            raise AssertionError(path)

        output = io.StringIO()
        with mock.patch.object(node_agent, "_request", side_effect=request), contextlib.redirect_stdout(output):
            self.assertEqual(node_agent.rotate_node_credential(self.args), 0)

        persisted = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["credential_generation"], 2)
        self.assertEqual(persisted["credential_rotation_state"], "completed")
        self.assertNotIn("node_secret_pending", persisted)
        self.assertNotIn(self.current_secret, output.getvalue())
        self.assertEqual(len(calls), 3)
        self.assertTrue(calls[0][3].startswith("Node "))
        self.assertEqual(calls[0][3], calls[1][3])
        self.assertNotEqual(calls[1][3], calls[2][3])
        self.assertEqual(json.loads(output.getvalue())["state"], "completed")

    def test_agent_resumes_after_activate_ack_loss_from_promoted_config(self) -> None:
        pending = "promoted-node-credential-0000001"
        rotation_id = "rotate_" + "d" * 32
        node_agent._write_config(
            self.path,
            self._config(
                node_secret=pending,
                credential_rotation_id=rotation_id,
                credential_rotation_state="promoted",
                credential_rotation_next_generation=2,
                node_secret_pending=pending,
            ),
        )
        calls: list[tuple[str, str, dict, str | None]] = []

        def request(url: str, path: str, payload: dict, authorization: str | None = None) -> dict:
            calls.append((url, path, payload, authorization))
            self.assertTrue(path.endswith("/ack"))
            return self._response(rotation_id, "device-rotation-agent", "completed")

        with mock.patch.object(node_agent, "_request", side_effect=request):
            self.assertEqual(node_agent.rotate_node_credential(self.args), 0)
        persisted = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["credential_rotation_state"], "completed")
        self.assertEqual(persisted["credential_generation"], 2)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
