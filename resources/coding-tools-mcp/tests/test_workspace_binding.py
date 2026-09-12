from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from coding_tools_mcp.endpoint_identity import (
    endpoint_identity_payload,
    workspace_binding_id,
)
from coding_tools_mcp.server import Runtime


class WorkspaceBindingIdTests(unittest.TestCase):
    def test_binding_is_deterministic_and_opaque(self) -> None:
        first = workspace_binding_id(
            device_instance_id="device-instance-1",
            workspace_root=Path("/tmp/ws"),
            generation=3,
        )
        second = workspace_binding_id(
            device_instance_id="device-instance-1",
            workspace_root=Path("/tmp/ws"),
            generation=3,
        )
        self.assertEqual(first, second)
        self.assertRegex(first, r"^[0-9a-f]{64}$")
        self.assertNotIn("/tmp/ws", first)
        self.assertNotIn("device-instance-1", first)

    def test_binding_rotates_on_every_axis(self) -> None:
        base = workspace_binding_id(
            device_instance_id="device-instance-1",
            workspace_root=Path("/tmp/ws"),
            generation=3,
        )
        self.assertNotEqual(
            base,
            workspace_binding_id(
                device_instance_id="device-instance-2",
                workspace_root=Path("/tmp/ws"),
                generation=3,
            ),
        )
        self.assertNotEqual(
            base,
            workspace_binding_id(
                device_instance_id="device-instance-1",
                workspace_root=Path("/tmp/other"),
                generation=3,
            ),
        )
        self.assertNotEqual(
            base,
            workspace_binding_id(
                device_instance_id="device-instance-1",
                workspace_root=Path("/tmp/ws"),
                generation=4,
            ),
        )

    def test_endpoint_payload_carries_stable_binding(self) -> None:
        runtime = SimpleNamespace(workspace_generation=7, activation_epoch_id="epoch-x")
        with patch.dict(
            os.environ,
            {
                "CODING_TOOLS_MCP_DEVICE_ID": "device-id-1",
                "CODING_TOOLS_MCP_DEVICE_INSTANCE_ID": "device-instance-1",
                "CODING_TOOLS_MCP_DEVICE_DISPLAY_NAME": "Test Box",
            },
        ):
            payload = endpoint_identity_payload(
                runtime, workspace_root=Path("/tmp/ws"), workspace_id="ws-1"
            )
        self.assertEqual(
            payload["workspace_binding_id"],
            workspace_binding_id(
                device_instance_id="device-instance-1",
                workspace_root=Path("/tmp/ws"),
                generation=7,
            ),
        )
        self.assertEqual(payload["workspace_generation"], 7)


class WorkspaceBindingBootstrapTests(unittest.TestCase):
    expires_at_unix_ms = 4_000_000_000_000

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(
            os.environ,
            {
                "CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID": "epoch-binding-001",
                "CODING_TOOLS_MCP_ACTIVATION_GATE": "closed",
                "CODING_TOOLS_MCP_ACTIVATION_EXPIRES_AT_UNIX_MS": str(
                    self.expires_at_unix_ms
                ),
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_DEVICE_INSTANCE_ID": "device-instance-binding-1",
            },
        )
        self.env.start()
        waiter = patch("coding_tools_mcp.activation_lifecycle.ACTIVATION_BOOTSTRAP_WAIT_SECONDS", 0)
        waiter.start()
        self.addCleanup(waiter.stop)

    def tearDown(self) -> None:
        self.env.stop()
        self.temp.cleanup()

    def _attested_runtime(self) -> Runtime:
        runtime = Runtime(Path(self.temp.name))
        runtime.request_context.hub_client = {
            "client_id": "chatweb-binding-test",
            "client_type": "chatweb",
            "identity_source": "attested_transport",
            "attestation_verified": True,
            "attestation_source": "managed_tunnel",
        }
        return runtime

    def test_accepted_bootstrap_reports_binding_without_workspace_access(self) -> None:
        runtime = self._attested_runtime()
        try:
            with patch.object(
                runtime,
                "list_dir",
                side_effect=AssertionError("bootstrap must not list files"),
            ):
                result = runtime.call_tool("workspace_context", {"detail": "compact"})
            self.assertFalse(result["isError"])
            structured = result["structuredContent"]
            self.assertTrue(structured["ok"])
            self.assertFalse(structured["workspace_accessed"])
            binding = structured["workspace_binding"]
            self.assertEqual(
                binding["workspace_binding_id"],
                workspace_binding_id(
                    device_instance_id="device-instance-binding-1",
                    workspace_root=Path(self.temp.name),
                    generation=runtime.workspace_generation,
                ),
            )
            self.assertEqual(binding["workspace_generation"], runtime.workspace_generation)
            self.assertTrue(binding["available"])
            # Only the bare name travels; the full path stays out of the block.
            self.assertNotIn(self.temp.name, json.dumps(binding))
        finally:
            runtime.close()

    def test_expired_bootstrap_reports_binding_for_dead_epoch(self) -> None:
        runtime = self._attested_runtime()
        try:
            with patch(
                "coding_tools_mcp.activation_lifecycle.time.time",
                return_value=(self.expires_at_unix_ms + 1) / 1000,
            ):
                result = runtime.call_tool("workspace_context", {"detail": "compact"})
            structured = result["structuredContent"]
            self.assertTrue(result["isError"])
            self.assertEqual(
                structured["error"]["code"], "ACTIVATION_REQUEST_EXPIRED"
            )
            self.assertNotIn("activation_bootstrap", structured)
            binding = structured["workspace_binding"]
            self.assertTrue(binding["available"])
            self.assertEqual(
                binding["workspace_binding_id"],
                workspace_binding_id(
                    device_instance_id="device-instance-binding-1",
                    workspace_root=Path(self.temp.name),
                    generation=runtime.workspace_generation,
                ),
            )
        finally:
            runtime.close()

    def test_dot_path_resolves_to_active_runtime_root_not_process_cwd(self) -> None:
        runtime = Runtime(Path(self.temp.name))
        try:
            opened = runtime.complete_activation_epoch(
                "epoch-binding-001", "a" * 64, self.expires_at_unix_ms
            )
            self.assertTrue(opened["ok"])
            result = runtime.call_tool("workspace_context", {"path": ".", "detail": "compact"})
            self.assertFalse(result["isError"])
            structured = result["structuredContent"]
            self.assertTrue(structured["ok"])
            self.assertNotEqual(os.getcwd(), str(Path(self.temp.name).resolve()))
            self.assertEqual(
                Path(structured["workspace"]).resolve(strict=False),
                Path(self.temp.name).resolve(strict=False),
            )
        finally:
            runtime.close()

    def test_workspace_switch_stales_previous_binding_contact(self) -> None:
        import tempfile as _tempfile

        from coding_tools_mcp.endpoint_identity import workspace_binding_id as _binding_id

        runtime = self._attested_runtime()
        other = _tempfile.TemporaryDirectory()
        try:
            before = runtime.connector_activation_bootstrap(blocking=False)
            # No contact yet: nothing current.
            self.assertFalse(before["current_contract_contact"])
            request = {"method": "tools/call", "params": {"name": "workspace_context"}}
            identity = {
                "client_id": "chatweb-binding-switch",
                "client_type": "chatweb",
                "identity_source": "attested_transport",
                "attestation_verified": True,
                "attestation_source": "managed_tunnel",
                "capabilities": {},
            }

            def accepted_response() -> dict:
                return {
                    "result": {
                        "structuredContent": {
                            "ok": True,
                            "completed": False,
                            "retryable": True,
                            "workspace_accessed": False,
                            "activation_bootstrap": {
                                "schema_version": 1,
                                "kind": "connector_compatibility_bootstrap",
                                "accepted": True,
                                "retry_required": True,
                                "activation_epoch_id": "epoch-binding-001",
                            },
                        }
                    }
                }

            runtime._record_activation_bootstrap_rpc_contact(
                request, accepted_response(), identity
            )
            contact = runtime.connector_activation_bootstrap(blocking=False)
            self.assertTrue(contact["current_contract_contact"])
            first_binding = contact["workspace_binding_id"]
            first_generation = contact["workspace_generation"]
            self.assertEqual(
                first_binding,
                _binding_id(
                    device_instance_id="device-instance-binding-1",
                    workspace_root=Path(self.temp.name),
                    generation=first_generation,
                ),
            )
            switched = runtime.switch_workspace(Path(other.name))
            self.assertTrue(switched["changed"])
            self.assertGreater(switched["generation"], first_generation)
            stale = runtime.connector_activation_bootstrap(blocking=False)
            self.assertFalse(
                stale["current_contract_contact"],
                "a pre-switch receipt must stop counting after the binding rotates",
            )
            # The projection echoes the stored receipt; the live generation has
            # moved on, which is exactly why the contact above is stale.
            self.assertNotEqual(stale["workspace_generation"], switched["generation"])
        finally:
            other.cleanup()
            runtime.close()

    def test_missing_drive_reports_typed_unavailable_without_fallback(self) -> None:
        import shutil as _shutil

        gone = Path(self.temp.name) / "gone-workspace"
        gone.mkdir()
        runtime = Runtime(gone)
        try:
            opened = runtime.complete_activation_epoch(
                "epoch-binding-001", "a" * 64, self.expires_at_unix_ms
            )
            self.assertTrue(opened["ok"])
            _shutil.rmtree(gone, ignore_errors=True)
            result = runtime.call_tool("workspace_context", {"path": ".", "detail": "compact"})
            self.assertTrue(result["isError"])
            structured = result["structuredContent"]
            self.assertEqual(structured["error"]["code"], "WORKSPACE_UNAVAILABLE")
            self.assertFalse(structured["error"]["retryable"])
            binding = structured["error"]["details"]["workspace_binding"]
            self.assertFalse(binding["available"])
            self.assertIsNotNone(binding["workspace_binding_id"])
        finally:
            runtime.close()


if __name__ == "__main__":
    unittest.main()
