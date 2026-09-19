from __future__ import annotations

import base64
import hashlib
import io
import json
import sqlite3
import tempfile
import threading
import time
import unittest
import zlib
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest import mock
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from control_plane.http_api import ControlPlaneHttpServer
from control_plane.mcp_oauth import (
    OAuthAccessIdentity,
    OAuthAuthenticationError,
    OAuthClientCredentials,
    OAuthIntrospectionConfiguration,
)
from control_plane.node_agent import (
    _approved_patch_projection_digest,
    _install_approved_patch_policy_values,
    _policy_digest,
    heartbeat,
    poll_approved_patch_once,
)
from control_plane.store import ControlPlaneStore


ISSUER = "https://identity.example.test/tenant-approved-patch"
RESOURCE = "https://mcp.example.test"
INTROSPECTION_URL = "https://identity.example.test/tenant-approved-patch/introspect"
READ_SCOPE = "control-plane.inventory"
WRITE_SCOPE = "control-plane.patch"


class _StaticVerifier:
    """Deterministic OAuth boundary for this source-only integration test."""

    def __init__(self, identity: OAuthAccessIdentity) -> None:
        self.identity = identity

    def authenticate(self, _token: str, *, required_scopes: object = None) -> OAuthAccessIdentity:
        if required_scopes is not None and not set(required_scopes) <= set(self.identity.scopes):
            raise OAuthAuthenticationError("OAuth access token is invalid.")
        return self.identity


class McpApprovedPatchHttpNodeE2ETests(unittest.TestCase):
    """Exercise C4's sealed patch handoff without claiming a Windows canary.

    The mocked bridge below is deliberately narrow and applies a fixture only
    after the node agent has reconstructed and locally admitted the sealed
    action.  Electron/Recovery IPC is covered by its own bridge tests.  This
    test catches integration drift across OAuth MCP, Console approval, durable
    action/poll/receipt HTTP routes, node policy checks, and result projection.
    """

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mcp-approved-patch-http-node-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.store = ControlPlaneStore(self.directory / "control.sqlite3")
        self.identity = OAuthAccessIdentity(
            issuer=ISSUER,
            subject="provider-subject-approved-patch-http-node",
            scopes=frozenset({READ_SCOPE, WRITE_SCOPE}),
        )
        self.configuration = OAuthIntrospectionConfiguration(
            issuer=ISSUER,
            resource=RESOURCE,
            introspection_url=INTROSPECTION_URL,
            required_scope=READ_SCOPE,
            credentials=OAuthClientCredentials(
                client_id="fixture-introspection-client",
                client_secret="fixture-introspection-secret",
            ),
            file_read_enabled=True,
            permission_requests_enabled=True,
            patch_write_scope=WRITE_SCOPE,
            approved_patch_enabled=True,
        )
        self.verifier = _StaticVerifier(self.identity)
        self.main_server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.store,
            "o" * 40,
            mcp_enabled=False,
            mcp_oauth=self.configuration,
            mcp_oauth_verifier=self.verifier,
        )
        self.mcp_server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.store,
            "o" * 40,
            mcp_enabled=True,
            mcp_ingress_only=True,
            mcp_oauth=self.configuration,
            mcp_oauth_verifier=self.verifier,
        )
        self.threads = [
            threading.Thread(target=self.main_server.serve_forever, daemon=True),
            threading.Thread(target=self.mcp_server.serve_forever, daemon=True),
        ]
        for thread in self.threads:
            thread.start()
        self.addCleanup(self._stop_servers)
        self.main_url = f"http://127.0.0.1:{self.main_server.server_port}"
        self.mcp_url = f"http://127.0.0.1:{self.mcp_server.server_port}"

        self.owner_id = "owner_default"
        self.principal = self.store.link_oauth_principal(
            owner_id=self.owner_id,
            issuer=ISSUER,
            subject=self.identity.subject,
        )
        self.node = self.store.enroll_node(
            owner_id=self.owner_id,
            device_id="node-http-approved-patch-e2e-001",
            endpoint_id="endpoint-http-approved-patch-e2e-001",
            display_name="HTTP approved-patch fixture node",
        )
        self.workspace_id = "workspace-http-approved-patch-e2e-001"
        self.workspace_generation = "generation-http-approved-patch-e2e-001"
        self.store.register_node_workspace(
            device_id=self.node["device_id"],
            workspace_id=self.workspace_id,
            workspace_generation=self.workspace_generation,
            display_name="HTTP approved-patch fixture workspace",
            capabilities={"read": True, "write": True, "exec": False},
        )
        self.binding = self.store.create_binding(
            owner_id=self.owner_id,
            device_id=self.node["device_id"],
            workspace_id=self.workspace_id,
            workspace_generation=self.workspace_generation,
            display_name="HTTP approved-patch fixture workspace",
        )
        self.workspace_root = self.directory / "workspace"
        self.fixture_path = self.workspace_root / "src" / "fixture.txt"
        self.fixture_path.parent.mkdir(parents=True)
        self.initial_content = b"initial fixture\n"
        self.updated_content = b"updated fixture\n"
        self.fixture_path.write_bytes(self.initial_content)
        self.config_path = self.directory / "node.json"
        self.registry_path = self.directory / "workspace-registry.json"
        self.data_root = self.directory / "node-data"
        self.config = {
            "server_url": self.main_url,
            "device_id": self.node["device_id"],
            "endpoint_id": "endpoint-http-approved-patch-e2e-001",
            "node_secret": self.node["node_secret"],
        }
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        self.registry_path.write_text(json.dumps({
            "schema_version": 1,
            "entries": [{
                "workspace_id": self.workspace_id,
                "workspace_generation": self.workspace_generation,
                "canonical_path": str(self.workspace_root.resolve()),
                "display_name": "HTTP approved-patch fixture workspace",
                "capabilities": {"read": True, "write": True, "exec": False},
                "created_at_ms": 1_700_000_000_000,
            }],
        }), encoding="utf-8")

    def _stop_servers(self) -> None:
        for server in (self.main_server, self.mcp_server):
            server.shutdown()
            server.server_close()
        for thread in self.threads:
            thread.join(timeout=2)

    def args(self) -> SimpleNamespace:
        return SimpleNamespace(
            config=str(self.config_path),
            workspace_registry=str(self.registry_path),
            data_root=str(self.data_root),
            project_root=str(Path.cwd()),
            node="node",
            runtime_mode="development",
            timeout_seconds=20,
            runtime_instance_id="mcp-process-http-approved-patch-e2e-001",
            mcp_server_instance_id="mcp-server-http-approved-patch-e2e-001",
            activation_epoch="activation-http-approved-patch-e2e-001",
            contract_version="sha256:" + "a" * 64,
            readiness="ready",
        )

    @staticmethod
    def strict_status() -> dict[str, str]:
        return {
            "state": "CURRENT", "host": "available", "installation": "current",
            "mcp_update_pending": "false", "mcp_running_revision": "sha-current",
            "mcp_disk_revision": "sha-current", "components_ready": "true",
            "fully_ready": "true", "runtime_update_incomplete": "false",
            "runtime_telemetry_available": "true", "runtime_signal_stale": "false",
            "connector_state": "CURRENT_ACKNOWLEDGED", "connector_rediscovered": "true",
            "connector_rediscovered_at": "2026-09-15T00:00:00Z",
            "connector_freshness_mode": "current_process_discovery",
            "connector_refresh_required": "false", "connector_ack_pending": "false",
            "connector_current_sha": "sha-current", "connector_ack_sha": "sha-current",
            "error_code": "none",
        }

    @staticmethod
    def strict_identity() -> dict[str, object]:
        return {
            "observation_schema_version": 1,
            "observation_kind": "mcp_identity_read_only",
            "mcp_ready": True,
            "identity_current": True,
            "mcp_process_instance_id": "mcp-process-http-approved-patch-e2e-001",
            "mcp_server_instance_id": "mcp-server-http-approved-patch-e2e-001",
            "activation_epoch_id": "activation-http-approved-patch-e2e-001",
            "current_activation_epoch_id": "activation-http-approved-patch-e2e-001",
            "tool_contract_sha256": "a" * 64,
        }

    @staticmethod
    def _response(request: Request) -> tuple[int, dict[str, Any]]:
        try:
            with urlopen(request, timeout=2) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            try:
                return error.code, json.loads(error.read())
            finally:
                error.close()

    def _mcp_post(self, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        return self._response(Request(
            f"{self.mcp_url}/mcp",
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": "Bearer opaque-source-fixture-token", "Content-Type": "application/json"},
            method="POST",
        ))

    def _approve(self, permission_request_id: str) -> None:
        status, response = self._response(Request(
            f"{self.main_url}/v1/permission-requests/{permission_request_id}/approve",
            data=b"{}",
            headers={"Authorization": "Bearer " + "o" * 40, "Content-Type": "application/json"},
            method="POST",
        ))
        self.assertEqual(status, 200)
        self.assertEqual(response["state"], "approved")

    def _patch_envelope(self) -> str:
        payload = base64.b64encode(zlib.compress(self.updated_content)).decode("ascii")
        return "\n".join((
            "*** Begin Patch",
            "*** Write Exact File: src/fixture.txt",
            "@@ encoding=zlib-base64 "
            f"preimage_sha256={hashlib.sha256(self.initial_content).hexdigest()} "
            f"postimage_sha256={hashlib.sha256(self.updated_content).hexdigest()}",
            "+" + payload,
            "*** End Patch",
            "",
        ))

    def _bridge_result(self, request: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
        patch_lines = str(request["patch_envelope"]).splitlines()[3:-1]
        postimage = zlib.decompress(base64.b64decode("".join(line[1:] for line in patch_lines)))
        self.assertEqual(hashlib.sha256(self.fixture_path.read_bytes()).hexdigest(), request["preimage_sha256"])
        self.fixture_path.write_bytes(postimage)
        file = {
            "path": request["path"],
            "preimage_sha256": request["preimage_sha256"],
            "postimage_sha256": hashlib.sha256(postimage).hexdigest(),
            "bytes_written": len(postimage),
        }
        return {
            "schema_version": 1,
            "operation_kind": "control_plane_approved_patch",
            "installation_id": None,
            "runtime_mode": "development",
            "action_id": request["action_id"],
            "attempt_id": request["attempt_id"],
            "local_handle": "cp_ap_" + "d" * 48,
            "patch_applied": True,
            "local_semantic_acceptance": "pending",
            "policy_sha256": _policy_digest(policy),
            "actor": {"client_id": "electron-control-plane-approved-patch-bridge", "client_type": "electron"},
            "runtime_identity": {
                "activation_epoch_id": "activation-http-approved-patch-e2e-001",
                "process_instance_id": "mcp-process-http-approved-patch-e2e-001",
                "server_instance_id": "mcp-server-http-approved-patch-e2e-001",
                "tool_contract_sha256": "a" * 64,
            },
            "facade_contract": request["facade_contract"],
            "file": file,
            "response_sha256": _approved_patch_projection_digest(file),
        }

    def test_oauth_permission_to_node_patch_to_verified_status(self) -> None:
        contract = {
            key: self.mcp_server.mcp_facade.contract[key]
            for key in ("schema_version", "profile", "sha256")
        }
        policy = _install_approved_patch_policy_values(
            self.args(),
            config_path=self.config_path,
            config=self.config,
            owner_id=self.owner_id,
            workspace_id=self.workspace_id,
            workspace_generation=self.workspace_generation,
            expires_at_ms=int(time.time() * 1000) + 10 * 60_000,
            facade_contract=contract,
            allowed_relative_paths=["src/fixture.txt"],
            max_patch_bytes=4096,
            max_file_bytes=4096,
        )
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)

        patch = self._patch_envelope()
        permission_status, permission = self._mcp_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-approved-patch-permission",
            "method": "tools/call",
            "params": {
                "name": "request_permissions",
                "arguments": {
                    "operation": "request_patch",
                    "binding_id": self.binding["binding_id"],
                    "path": "src/fixture.txt",
                    "preimage_sha256": hashlib.sha256(self.initial_content).hexdigest(),
                    "patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest(),
                    "validation_profile": "targeted",
                    "idempotency_key": "mcp-http-approved-patch-permission-key",
                    "expected_facade_contract": contract,
                },
            },
        })
        self.assertEqual(permission_status, 200)
        request_id = permission["result"]["structuredContent"]["permission_request"]["permission_request_id"]
        self.assertEqual(permission["result"]["structuredContent"]["execution"], "not_started")
        self._approve(request_id)

        queued_status, queued = self._mcp_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-approved-patch-queue",
            "method": "tools/call",
            "params": {
                "name": "agent_workflow",
                "arguments": {
                    "operation": "apply_patch",
                    "permission_request_id": request_id,
                    "patch_envelope": patch,
                    "idempotency_key": "mcp-http-approved-patch-action-key",
                    "expected_facade_contract": contract,
                },
            },
        })
        self.assertEqual(queued_status, 200)
        queued_content = queued["result"]["structuredContent"]
        self.assertEqual(queued_content["execution"], "queued_for_local_patch_policy")
        self.assertFalse(queued_content["patch_applied"])
        action_id = queued_content["action_id"]

        def bridge(
            _args: SimpleNamespace,
            _project_root: Path,
            request: dict[str, Any],
        ) -> tuple[dict[str, Any], None]:
            return self._bridge_result(request, policy), None

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_approved_patch_bridge", side_effect=bridge), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_approved_patch_once(self.args()), 0)

        self.assertEqual(self.fixture_path.read_bytes(), self.updated_content)
        settled = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(settled["delivery_state"], "settled")
        self.assertEqual([receipt["receipt_state"] for receipt in settled["receipts"]], ["completed"])
        lifecycle = self.store.list_action_lifecycle(owner_id=self.owner_id)
        self.assertTrue(next(item for item in lifecycle if item["action_id"] == action_id)["approved_patch_candidate"])

        observed_status, observed = self._mcp_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-approved-patch-status",
            "method": "tools/call",
            "params": {
                "name": "agent_workflow",
                "arguments": {"operation": "patch_status", "action_id": action_id},
            },
        })
        self.assertEqual(observed_status, 200)
        content = observed["result"]["structuredContent"]
        self.assertEqual(content["execution"], "effect_applied_pending_local_acceptance")
        self.assertTrue(content["patch_applied"])
        self.assertEqual(content["local_semantic_acceptance"], "pending")
        self.assertEqual(content["local_admission"], "effect_applied_local_acceptance_pending")
        self.assertNotIn("accepted", content["execution"])
        self.assertEqual(content["patch"]["file"], {
            "path": "src/fixture.txt",
            "preimage_sha256": hashlib.sha256(self.initial_content).hexdigest(),
            "postimage_sha256": hashlib.sha256(self.updated_content).hexdigest(),
            "bytes_written": len(self.updated_content),
        })
        rendered = json.dumps(content)
        self.assertNotIn(patch, rendered)
        self.assertNotIn(str(self.workspace_root), rendered)
        self.assertNotIn("policy_sha256", rendered)
        self.assertNotIn("local_handle", rendered)

        # A completed receipt remains untrusted input at the final MCP
        # boundary.  Simulate storage corruption after durable acceptance;
        # status must withdraw the relay rather than report a patch as applied.
        with sqlite3.connect(self.store.path) as connection:
            raw_payload = connection.execute(
                "SELECT payload_json FROM receipts WHERE action_id = ?",
                (action_id,),
            ).fetchone()[0]
            tampered_payload = json.loads(raw_payload)
            tampered_payload["file"]["postimage_sha256"] = "0" * 64
            connection.execute(
                "UPDATE receipts SET payload_json = ? WHERE action_id = ?",
                (json.dumps(tampered_payload, separators=(",", ":")), action_id),
            )
            connection.commit()
        rejected_status, rejected = self._mcp_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-approved-patch-tampered-status",
            "method": "tools/call",
            "params": {
                "name": "agent_workflow",
                "arguments": {"operation": "patch_status", "action_id": action_id},
            },
        })
        self.assertEqual(rejected_status, 200)
        rejected_content = rejected["result"]["structuredContent"]
        self.assertEqual(rejected_content["execution"], "local_patch_receipt_pending_or_unverified")
        self.assertFalse(rejected_content["patch_applied"])
        self.assertNotIn("patch", rejected_content)

    def test_unknown_patch_effect_requires_local_reconciliation_without_retry(self) -> None:
        """A prepared mutation that loses its outcome is never reported as pending.

        This stays a source-fixture test: the important cross-boundary
        assertion is that a normal OAuth status caller sees an explicit
        UNKNOWN/no-retry state, while the sealed patch, local root and node
        diagnostic remain absent from the projection.
        """

        contract = {
            key: self.mcp_server.mcp_facade.contract[key]
            for key in ("schema_version", "profile", "sha256")
        }
        patch = self._patch_envelope()
        permission = self.store.request_mcp_patch_permission(
            owner_id=self.owner_id,
            principal_id=self.principal["principal_id"],
            binding_id=self.binding["binding_id"],
            path="src/fixture.txt",
            preimage_sha256=hashlib.sha256(self.initial_content).hexdigest(),
            patch_sha256=hashlib.sha256(patch.encode("utf-8")).hexdigest(),
            validation_profile="targeted",
            idempotency_key="mcp-http-approved-patch-unknown-permission-key",
            facade_contract=contract,
        )
        self.store.approve_mcp_permission_request(
            owner_id=self.owner_id,
            permission_request_id=permission["permission_request_id"],
        )
        queued = self.store.request_mcp_approved_patch(
            owner_id=self.owner_id,
            principal_id=self.principal["principal_id"],
            permission_request_id=permission["permission_request_id"],
            patch_envelope=patch,
            idempotency_key="mcp-http-approved-patch-unknown-action-key",
            facade_contract=contract,
        )
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)
        deliveries = self.store.poll_actions(
            device_id=self.node["device_id"],
            lane="approved_patch",
        )
        self.assertEqual(len(deliveries), 1)
        delivery = deliveries[0]
        self.assertEqual(delivery["action_id"], queued["action_id"])
        self.store.record_receipt(
            device_id=self.node["device_id"],
            action_id=delivery["action_id"],
            attempt_id=delivery["attempt_id"],
            receipt_state="unknown",
            local_handle="",
            payload={
                "schema_version": 1,
                "operation_kind": "control_plane_approved_patch",
                "code": "CONTROL_PLANE_APPROVED_PATCH_EFFECT_UNKNOWN",
                "diagnostic_code": "CONTROL_PLANE_APPROVED_PATCH_PREPARED_RECOVERED",
            },
        )
        self.assertEqual(
            self.store.poll_actions(device_id=self.node["device_id"], lane="approved_patch"),
            [],
        )

        observed_status, observed = self._mcp_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-approved-patch-unknown-status",
            "method": "tools/call",
            "params": {
                "name": "agent_workflow",
                "arguments": {"operation": "patch_status", "action_id": queued["action_id"]},
            },
        })
        self.assertEqual(observed_status, 200)
        content = observed["result"]["structuredContent"]
        self.assertEqual(content["execution"], "local_patch_effect_unknown_reconcile_required")
        self.assertIsNone(content["patch_applied"])
        self.assertEqual(content["patch_effect_state"], "unknown")
        self.assertEqual(content["local_admission"], "unknown_effect_do_not_retry")
        self.assertEqual(content["local_semantic_acceptance"], "unknown")
        self.assertTrue(content["reconciliation_required"])
        self.assertEqual(content["action"]["delivery_state"], "reconcile_required")
        self.assertEqual(content["action"]["central_lifecycle_state"], "reconcile_required")
        rendered = json.dumps(content)
        self.assertNotIn(patch, rendered)
        self.assertNotIn(str(self.workspace_root), rendered)
        self.assertNotIn("PREPARED_RECOVERED", rendered)
        self.assertNotIn("local_handle", rendered)
        self.assertIn("Do not retry", observed["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
