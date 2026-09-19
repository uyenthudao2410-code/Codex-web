from __future__ import annotations

import hashlib
import io
import json
import tempfile
import threading
import time
import unittest
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
    _file_read_projection_digest,
    _install_file_read_policy_values,
    _policy_digest,
    heartbeat,
    poll_file_read_once,
)
from control_plane.store import ControlPlaneStore


ISSUER = "https://identity.example.test/tenant-one"
RESOURCE = "https://mcp.example.test"
INTROSPECTION_URL = "https://identity.example.test/tenant-one/introspect"
SCOPE = "control-plane.inventory"


class _StaticVerifier:
    """A deterministic OAuth verifier for one isolated source fixture.

    This intentionally exercises the HTTP resource-server boundary rather
    than the network implementation of a real identity provider.  Provider
    reachability and a real browser OAuth callback remain live C1 evidence.
    """

    def __init__(self, identity: OAuthAccessIdentity) -> None:
        self.identity = identity

    def authenticate(self, _token: str, *, required_scopes: object = None) -> OAuthAccessIdentity:
        if required_scopes is not None and not set(required_scopes) <= set(self.identity.scopes):
            raise OAuthAuthenticationError("OAuth access token is invalid.")
        return self.identity


class McpFileReadHttpNodeE2ETests(unittest.TestCase):
    """Exercise C3's source-level HTTP handoff without a Windows assertion.

    The recovery bridge itself is replaced by a narrow result fixture here.
    Its independently packaged Electron/Recovery behavior stays covered by
    the bridge tests; this test instead catches drift among the public MCP
    facade, durable store, node-authenticated poll/receipt API, and node-agent
    lane/parser.
    """

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mcp-file-read-http-node-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.store = ControlPlaneStore(self.directory / "control.sqlite3")
        self.identity = OAuthAccessIdentity(
            issuer=ISSUER,
            subject="provider-subject-http-node-e2e",
            scopes=frozenset({SCOPE}),
        )
        self.configuration = OAuthIntrospectionConfiguration(
            issuer=ISSUER,
            resource=RESOURCE,
            introspection_url=INTROSPECTION_URL,
            required_scope=SCOPE,
            credentials=OAuthClientCredentials(
                client_id="fixture-introspection-client",
                client_secret="fixture-introspection-secret",
            ),
            file_read_enabled=True,
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
            device_id="node-http-file-read-e2e-001",
            endpoint_id="endpoint-http-file-read-e2e-001",
            display_name="HTTP file-read fixture node",
        )
        self.workspace_id = "workspace-http-file-read-e2e-001"
        self.workspace_generation = "generation-http-file-read-e2e-001"
        self.store.register_node_workspace(
            device_id=self.node["device_id"],
            workspace_id=self.workspace_id,
            workspace_generation=self.workspace_generation,
            display_name="HTTP file-read fixture workspace",
            capabilities={"read": True, "write": False, "exec": False},
        )
        self.binding = self.store.create_binding(
            owner_id=self.owner_id,
            device_id=self.node["device_id"],
            workspace_id=self.workspace_id,
            workspace_generation=self.workspace_generation,
            display_name="HTTP file-read fixture workspace",
        )
        self.workspace_root = self.directory / "workspace"
        self.workspace_root.mkdir()
        self.fixture_path = self.workspace_root / "fixture.txt"
        self.fixture_content = "line one\nline two\n"
        self.fixture_path.write_text(self.fixture_content, encoding="utf-8")
        self.config_path = self.directory / "node.json"
        self.registry_path = self.directory / "workspace-registry.json"
        self.data_root = self.directory / "node-data"
        self.config = {
            "server_url": self.main_url,
            "device_id": self.node["device_id"],
            "endpoint_id": "endpoint-http-file-read-e2e-001",
            "node_secret": self.node["node_secret"],
        }
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        self.registry_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "entries": [
                        {
                            "workspace_id": self.workspace_id,
                            "workspace_generation": self.workspace_generation,
                            "canonical_path": str(self.workspace_root.resolve()),
                            "display_name": "HTTP file-read fixture workspace",
                            "capabilities": {"read": True, "write": False, "exec": False},
                            "created_at_ms": 1_700_000_000_000,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

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
            runtime_instance_id="mcp-process-http-file-read-e2e-001",
            mcp_server_instance_id="mcp-server-http-file-read-e2e-001",
            activation_epoch="activation-http-file-read-e2e-001",
            contract_version="sha256:" + "a" * 64,
            readiness="ready",
        )

    @staticmethod
    def strict_status() -> dict[str, str]:
        return {
            "state": "CURRENT",
            "host": "available",
            "installation": "current",
            "mcp_update_pending": "false",
            "mcp_running_revision": "sha-current",
            "mcp_disk_revision": "sha-current",
            "components_ready": "true",
            "fully_ready": "true",
            "runtime_update_incomplete": "false",
            "runtime_telemetry_available": "true",
            "runtime_signal_stale": "false",
            "connector_state": "CURRENT_ACKNOWLEDGED",
            "connector_rediscovered": "true",
            "connector_rediscovered_at": "2026-09-15T00:00:00Z",
            "connector_freshness_mode": "current_process_discovery",
            "connector_refresh_required": "false",
            "connector_ack_pending": "false",
            "connector_current_sha": "sha-current",
            "connector_ack_sha": "sha-current",
            "error_code": "none",
        }

    @staticmethod
    def strict_identity() -> dict[str, object]:
        return {
            "observation_schema_version": 1,
            "observation_kind": "mcp_identity_read_only",
            "mcp_ready": True,
            "identity_current": True,
            "mcp_process_instance_id": "mcp-process-http-file-read-e2e-001",
            "mcp_server_instance_id": "mcp-server-http-file-read-e2e-001",
            "activation_epoch_id": "activation-http-file-read-e2e-001",
            "current_activation_epoch_id": "activation-http-file-read-e2e-001",
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
        return self._response(
            Request(
                f"{self.mcp_url}/mcp",
                data=json.dumps(body).encode("utf-8"),
                headers={"Authorization": "Bearer opaque-source-fixture-token", "Content-Type": "application/json"},
                method="POST",
            )
        )

    def _bridge_result(self, request: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
        content_bytes = self.fixture_content.encode("utf-8")
        file = {
            "path": request["path"],
            "content": self.fixture_content,
            "content_sha256": hashlib.sha256(content_bytes).hexdigest(),
            "encoding": "utf-8",
            "start_line": request["start_line"],
            "end_line": 2,
            "total_lines": 2,
            "total_bytes": len(content_bytes),
            "bytes_read": len(content_bytes),
            "truncated": False,
            "next_start_line": None,
        }
        return {
            "schema_version": 1,
            "operation_kind": "control_plane_bounded_file_read",
            "installation_id": None,
            "runtime_mode": "development",
            "action_id": request["action_id"],
            "attempt_id": request["attempt_id"],
            "local_handle": "cp_fr_" + "d" * 48,
            "file_accessed": True,
            "policy_sha256": _policy_digest(policy),
            "actor": {"client_id": "electron-control-plane-file-read-bridge", "client_type": "electron"},
            "runtime_identity": {
                "activation_epoch_id": "activation-http-file-read-e2e-001",
                "process_instance_id": "mcp-process-http-file-read-e2e-001",
                "server_instance_id": "mcp-server-http-file-read-e2e-001",
                "tool_contract_sha256": "a" * 64,
            },
            "facade_contract": request["facade_contract"],
            "file": file,
            "response_sha256": _file_read_projection_digest(file),
        }

    def test_mcp_oauth_to_node_lane_to_verified_read_status(self) -> None:
        contract = {
            key: self.mcp_server.mcp_facade.contract[key]
            for key in ("schema_version", "profile", "sha256")
        }
        policy = _install_file_read_policy_values(
            self.args(),
            config_path=self.config_path,
            config=self.config,
            owner_id=self.owner_id,
            workspace_id=self.workspace_id,
            workspace_generation=self.workspace_generation,
            # The central bounded-read action lasts up to five minutes, so the
            # locally confirmed policy must outlive that action while staying
            # within its 24-hour maximum.
            expires_at_ms=int(time.time() * 1000) + 10 * 60_000,
            facade_contract=contract,
            allowed_relative_paths=["fixture.txt"],
            max_bytes=1024,
            max_lines=20,
        )

        # The initial node heartbeat is a real Node-authenticated HTTP call,
        # not a direct store mutation. Its policy report is intentionally only
        # a compact observation; the bridge policy is rechecked below.
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)

        queued_status, queued = self._mcp_post(
            {
                "jsonrpc": "2.0",
                "id": "mcp-http-file-read-e2e-queue",
                "method": "tools/call",
                "params": {
                    "name": "workspace_context",
                    "arguments": {
                        "operation": "read_file",
                        "binding_id": self.binding["binding_id"],
                        "path": "fixture.txt",
                        "start_line": 1,
                        "max_lines": 20,
                        "max_bytes": 1024,
                        "idempotency_key": "mcp-http-file-read-e2e-queue-key",
                        "expected_facade_contract": contract,
                    },
                },
            }
        )
        self.assertEqual(queued_status, 200)
        queued_content = queued["result"]["structuredContent"]
        self.assertEqual(queued_content["execution"], "queued_for_local_admission")
        self.assertFalse(queued_content["file_accessed"])
        action_id = queued_content["action_id"]

        def bridge(
            _args: SimpleNamespace,
            _project_root: Path,
            request: dict[str, Any],
        ) -> tuple[dict[str, Any], None]:
            return self._bridge_result(request, policy), None

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_file_read_bridge", side_effect=bridge), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_file_read_once(self.args()), 0)

        settled = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(settled["delivery_state"], "settled")
        self.assertEqual([receipt["receipt_state"] for receipt in settled["receipts"]], ["completed"])
        self.assertEqual(len(settled["attempts"]), 1)

        observed_status, observed = self._mcp_post(
            {
                "jsonrpc": "2.0",
                "id": "mcp-http-file-read-e2e-status",
                "method": "tools/call",
                "params": {
                    "name": "workspace_context",
                    "arguments": {"operation": "read_status", "action_id": action_id},
                },
            }
        )
        self.assertEqual(observed_status, 200)
        content = observed["result"]["structuredContent"]
        self.assertEqual(content["execution"], "completed_file_read_relay")
        self.assertTrue(content["file_accessed"])
        self.assertEqual(content["file_read"]["file"]["content"], self.fixture_content)
        self.assertNotIn("policy_sha256", json.dumps(content))
        self.assertNotIn(str(self.workspace_root), json.dumps(content))


if __name__ == "__main__":
    unittest.main()
