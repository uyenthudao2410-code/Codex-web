from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import sqlite3
import subprocess
import tempfile
import threading
import time
import unittest
import zlib
from contextlib import closing, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest import mock
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import control_plane.node_agent as node_agent_module
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
    _install_exec_policy_values,
    _exec_policy_path,
    _write_json_atomic,
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
            device_id="b3b8a0bb-4d2d-4f12-8c2a-9c7c0d8e1f01",
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
        self.task = self.store.create_mcp_task_session(
            owner_id=self.owner_id,
            principal_id=self.principal["principal_id"],
            binding_id=self.binding["binding_id"],
            label="HTTP approved-patch fixture task",
            idempotency_key="http-approved-patch-task-key-0001",
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
        for server, thread in zip((self.main_server, self.mcp_server), self.threads):
            self._stop_server(server, thread)

    @staticmethod
    def _stop_server(server: ControlPlaneHttpServer, thread: threading.Thread) -> None:
        # Stop the selector loop before closing its socket. Separate unittest
        # cleanups run in reverse registration order, which otherwise closes
        # a standing-write fixture while serve_forever is still selecting.
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

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

    def _start_recovery_patch_fixture(
        self,
        *,
        crash_after_patch_result: bool = False,
        drop_after_patch_result: bool = False,
    ) -> tuple[SimpleNamespace, Path, dict[str, Any], Any]:
        """Start the real Recovery/Electron process fixture for standing patch proof."""

        repo_root = Path(__file__).resolve().parents[2]
        app_data = self.directory / "approved-recovery-appdata"
        data_root = app_data / "web-mcp-assistant"
        data_root.mkdir(parents=True)
        config_path = data_root / "control-plane-node.json"
        registry_path = data_root / "control-plane-workspaces.json"
        config = {
            "server_url": self.main_url,
            "device_id": self.node["device_id"],
            "endpoint_id": "endpoint-http-approved-patch-e2e-001",
            "node_secret": self.node["node_secret"],
        }
        config_path.write_text(json.dumps(config), encoding="utf-8")
        registry_path.write_text(json.dumps({
            "schema_version": 1,
            "entries": [{
                "workspace_id": self.workspace_id,
                "workspace_generation": self.workspace_generation,
                "canonical_path": str(self.workspace_root.resolve()),
                "display_name": "HTTP approved-patch Recovery fixture workspace",
                "capabilities": {"read": True, "write": True, "exec": False},
                "created_at_ms": 1_700_000_000_000,
            }],
        }), encoding="utf-8")
        ready_file = self.directory / "recovery-approved-patch-ready.json"
        observation_file = self.directory / "recovery-approved-patch-observation.json"
        fixture_file = self.directory / "recovery-approved-patch-fixture.json"
        fixture = {
            "app_data": str(app_data),
            "app_root": str(repo_root),
            "workspace": str(self.workspace_root.resolve()),
            "device_id": self.node["device_id"],
            "activation_epoch_id": "activation-http-approved-patch-e2e-001",
            "mcp_token": "mcp-runtime-approved-patch-fixture-token-0001",
            "ready_file": str(ready_file),
            "observation_file": str(observation_file),
            "process_instance_id": "mcp-process-http-approved-patch-e2e-001",
            "server_instance_id": "mcp-server-http-approved-patch-e2e-001",
            "tool_contract_sha256": "a" * 64,
            "patch_run_id": "1" * 32,
            "patch_wave_id": "2" * 32,
            "crash_after_patch_result": crash_after_patch_result,
            "drop_after_patch_result": drop_after_patch_result,
        }
        fixture_file.write_text(json.dumps(fixture), encoding="utf-8")
        process_holder: dict[str, Any] = {"process": None}

        def start() -> None:
            ready_file.unlink(missing_ok=True)
            environment = dict(os.environ)
            environment["APPDATA"] = str(app_data)
            process = subprocess.Popen(
                ["node", str(repo_root / "tests" / "recovery-exec-process-fixture.cjs"), "--fixture", str(fixture_file)],
                cwd=repo_root,
                env=environment,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            process_holder["process"] = process
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if ready_file.is_file():
                    return
                if process.poll() is not None:
                    stderr = process.stderr.read() if process.stderr else ""
                    self.fail(f"Approved-patch Recovery fixture exited early: {stderr}")
                time.sleep(0.05)
            stderr = process.stderr.read() if process.stderr else ""
            self.fail(f"Approved-patch Recovery fixture did not become ready: {stderr}")

        def stop() -> None:
            process = process_holder.get("process")
            if process is None:
                return
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            if process.stderr is not None:
                process.stderr.close()
            process_holder["process"] = None

        def restart(*, crash_after_patch_result: bool = False) -> None:
            stop()
            fixture["crash_after_patch_result"] = crash_after_patch_result
            fixture["drop_after_patch_result"] = False
            fixture_file.write_text(json.dumps(fixture), encoding="utf-8")
            start()

        start()
        self.addCleanup(stop)
        args = SimpleNamespace(
            config=str(config_path),
            workspace_registry=str(registry_path),
            data_root=str(data_root),
            project_root=str(repo_root),
            node="node",
            runtime_mode="development",
            timeout_seconds=20,
            runtime_instance_id="mcp-process-http-approved-patch-e2e-001",
            mcp_server_instance_id="mcp-server-http-approved-patch-e2e-001",
            activation_epoch="activation-http-approved-patch-e2e-001",
            contract_version="sha256:" + "a" * 64,
            readiness="ready",
        )
        return args, fixture_file, process_holder, restart

    def _standing_http_fixture(self, *, exec_enabled: bool = False) -> tuple[Any, str, Any, dict[str, Any]]:
        """Create a standing-write ingress with the real OAuth/MCP facade."""

        standing_configuration = OAuthIntrospectionConfiguration(
            issuer=ISSUER,
            resource=RESOURCE,
            introspection_url=INTROSPECTION_URL,
            required_scope=READ_SCOPE,
            credentials=OAuthClientCredentials(
                client_id="fixture-introspection-client",
                client_secret="fixture-introspection-secret",
            ),
            file_read_enabled=True,
            permission_requests_enabled=False,
            patch_write_scope=WRITE_SCOPE,
            approved_patch_enabled=False,
            standing_write_enabled=True,
            exec_enabled=exec_enabled,
        )
        standing_server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.store,
            "o" * 40,
            mcp_enabled=True,
            mcp_ingress_only=True,
            mcp_oauth=standing_configuration,
            mcp_oauth_verifier=self.verifier,
        )
        standing_thread = threading.Thread(target=standing_server.serve_forever, daemon=True)
        standing_thread.start()
        self.addCleanup(self._stop_server, standing_server, standing_thread)
        standing_url = f"http://127.0.0.1:{standing_server.server_port}"

        def standing_post(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            return self._response(Request(
                f"{standing_url}/mcp",
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Authorization": "Bearer opaque-source-fixture-token",
                    "Content-Type": "application/json",
                },
                method="POST",
            ))

        contract = {
            key: standing_server.mcp_facade.contract[key]
            for key in ("schema_version", "profile", "sha256")
        }
        return standing_server, standing_url, standing_post, contract

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
            "task_id": request["task_id"],
            "writer_lease_generation": request["writer_lease_generation"],
            "run_id": "a" * 32,
            "wave_id": "b" * 32,
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

    def test_standing_initial_verification_is_immutable_and_failed_proof_preserves_one_effect(self) -> None:
        _server, _url, post, contract = self._standing_http_fixture(exec_enabled=True)
        self.workspace_id = "workspace-http-initial-verification-001"
        self.workspace_generation = "generation-http-initial-verification-001"
        self.store.register_node_workspace(device_id=self.node["device_id"], workspace_id=self.workspace_id,
                                           workspace_generation=self.workspace_generation, display_name="Initial verification fixture",
                                           capabilities={"read": True, "write": True, "exec": True})
        self.binding = self.store.create_binding(owner_id=self.owner_id, device_id=self.node["device_id"], workspace_id=self.workspace_id,
                                                 workspace_generation=self.workspace_generation, display_name="Initial verification fixture")
        self.task = self.store.create_mcp_task_session(owner_id=self.owner_id, principal_id=self.principal["principal_id"],
                                                     binding_id=self.binding["binding_id"], label="Initial verification fixture task",
                                                     idempotency_key="http-initial-verification-task-key")
        registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        registry["entries"][0].update(workspace_id=self.workspace_id, workspace_generation=self.workspace_generation,
                                      capabilities={"read": True, "write": True, "exec": True})
        self.registry_path.write_text(json.dumps(registry), encoding="utf-8")
        policy = _install_approved_patch_policy_values(self.args(), config_path=self.config_path, config=self.config,
                                                      owner_id=self.owner_id, workspace_id=self.workspace_id, workspace_generation=self.workspace_generation,
                                                      facade_contract=contract, expires_at_ms=None, allowed_relative_paths=None,
                                                      allowed_relative_prefixes=["."], max_patch_bytes=4096, max_file_bytes=4096)
        exec_policy = _install_exec_policy_values(owner_id=self.owner_id, device_id=self.node["device_id"], endpoint_id=self.config["endpoint_id"],
                                                   workspace_id=self.workspace_id, workspace_generation=self.workspace_generation, server_origin=self.main_url,
                                                   facade_contract=contract, allowed_argv_prefixes=[["node", "--test"]], max_timeout_ms=60000, max_output_bytes=32768)
        _write_json_atomic(_exec_policy_path(self.args()), exec_policy)
        with redirect_stdout(io.StringIO()):
            heartbeat(self.args())
        self.store.claim_mcp_task_writer_lease(owner_id=self.owner_id, principal_id=self.principal["principal_id"], task_id=self.task["task_id"])
        patch = self._patch_envelope()
        plan = {"argv": ["node", "--test", "tests/fixture.test.js"], "cwd": "", "timeout_ms": 60000, "max_output_bytes": 32768}
        arguments = {"operation": "apply_patch", "binding_id": self.binding["binding_id"], "task_id": self.task["task_id"],
                     "path": "src/fixture.txt", "preimage_sha256": hashlib.sha256(self.initial_content).hexdigest(),
                     "patch_sha256": hashlib.sha256(patch.encode()).hexdigest(), "validation_profile": "targeted", "patch_envelope": patch,
                     "idempotency_key": "http-initial-verification-patch-key", "expected_facade_contract": contract, "verification": plan}
        def call(name, args):
            return post({"jsonrpc": "2.0", "id": "initial-verification-call", "method": "tools/call", "params": {"name": name, "arguments": args}})
        _, queued = call("agent_workflow", arguments)
        action_id = queued["result"]["structuredContent"]["action_id"]
        _, drift = call("agent_workflow", {**arguments, "verification": {**plan, "timeout_ms": 5000}})
        self.assertEqual(drift["result"]["structuredContent"]["code"], "CONFLICT")
        calls = []
        def bridge(_args, _root, request):
            self.assertEqual(request["verification"], plan)
            calls.append(request["action_id"])
            result = self._bridge_result(request, policy)
            result["initial_verification"] = {"plan_sha256": _approved_patch_projection_digest(plan), "proof_status": "failed", "proof_ids": [], "proof_fingerprint": None}
            result["response_sha256"] = _approved_patch_projection_digest({"file": result["file"], "initial_verification": result["initial_verification"]})
            return result, None
        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_approved_patch_bridge", side_effect=bridge), redirect_stdout(io.StringIO()):
            poll_approved_patch_once(self.args())
            poll_approved_patch_once(self.args())
        self.assertEqual(calls, [action_id])
        self.assertEqual(self.fixture_path.read_bytes(), self.updated_content)
        _, observed = call("agent_workflow", {"operation": "patch_status", "action_id": action_id})
        observation = observed["result"]["structuredContent"]
        self.assertTrue(observation["patch_applied"])
        self.assertEqual(observation["proof_status"], "failed")
        self.assertEqual(observation["local_semantic_acceptance"], "pending")
        self.assertEqual(observation["patch"]["run_id"], "a" * 32)
        _, replay = call("agent_workflow", arguments)
        self.assertTrue(replay["result"]["structuredContent"]["replayed"])
        self.assertEqual(replay["result"]["structuredContent"]["action_id"], action_id)

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
                    "task_id": self.task["task_id"],
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
                    "task_id": self.task["task_id"],
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
        with closing(sqlite3.connect(self.store.path)) as connection:
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

    def test_oauth_standing_write_to_node_patch_to_verified_status(self) -> None:
        """Exercise the shared-account standing path across the HTTP/node boundary."""

        standing_configuration = OAuthIntrospectionConfiguration(
            issuer=ISSUER,
            resource=RESOURCE,
            introspection_url=INTROSPECTION_URL,
            required_scope=READ_SCOPE,
            credentials=OAuthClientCredentials(
                client_id="fixture-introspection-client",
                client_secret="fixture-introspection-secret",
            ),
            file_read_enabled=True,
            permission_requests_enabled=False,
            patch_write_scope=WRITE_SCOPE,
            approved_patch_enabled=False,
            standing_write_enabled=True,
        )
        standing_server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.store,
            "o" * 40,
            mcp_enabled=True,
            mcp_ingress_only=True,
            mcp_oauth=standing_configuration,
            mcp_oauth_verifier=self.verifier,
        )
        standing_thread = threading.Thread(target=standing_server.serve_forever, daemon=True)
        standing_thread.start()
        self.addCleanup(self._stop_server, standing_server, standing_thread)
        standing_url = f"http://127.0.0.1:{standing_server.server_port}"

        def standing_post(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            return self._response(Request(
                f"{standing_url}/mcp",
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Authorization": "Bearer opaque-source-fixture-token",
                    "Content-Type": "application/json",
                },
                method="POST",
            ))

        contract = {
            key: standing_server.mcp_facade.contract[key]
            for key in ("schema_version", "profile", "sha256")
        }
        listed_status, listed = standing_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-standing-tools-list",
            "method": "tools/list",
            "params": {},
        })
        self.assertEqual(listed_status, 200)
        listed_tools = {tool["name"]: tool for tool in listed["result"]["tools"]}
        self.assertEqual(
            listed_tools["agent_workflow"]["_meta"]["control_plane"]["capability_state"],
            "standing_write",
        )
        self.assertEqual(contract["schema_version"], 31)
        self.assertEqual(contract["profile"], "control-plane-oauth-standing-write-v1")

        policy = _install_approved_patch_policy_values(
            self.args(),
            config_path=self.config_path,
            config=self.config,
            owner_id=self.owner_id,
            workspace_id=self.workspace_id,
            workspace_generation=self.workspace_generation,
            expires_at_ms=None,
            facade_contract=contract,
            allowed_relative_paths=["src/fixture.txt"],
            max_patch_bytes=4096,
            max_file_bytes=4096,
        )
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)

        claimed_status, claimed = standing_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-standing-writer-claim",
            "method": "tools/call",
            "params": {
                "name": "task_control",
                "arguments": {"operation": "writer_claim", "task_id": self.task["task_id"]},
            },
        })
        self.assertEqual(claimed_status, 200)
        self.assertEqual(
            claimed["result"]["structuredContent"]["writer_lease"]["state"],
            "held",
        )

        patch = self._patch_envelope()
        queued_status, queued = standing_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-standing-patch-queue",
            "method": "tools/call",
            "params": {
                "name": "agent_workflow",
                "arguments": {
                    "operation": "apply_patch",
                    "binding_id": self.binding["binding_id"],
                    "task_id": self.task["task_id"],
                    "path": "src/fixture.txt",
                    "preimage_sha256": hashlib.sha256(self.initial_content).hexdigest(),
                    "patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest(),
                    "validation_profile": "targeted",
                    "patch_envelope": patch,
                    "idempotency_key": "mcp-http-standing-patch-action-key",
                    "expected_facade_contract": contract,
                },
            },
        })
        self.assertEqual(queued_status, 200)
        queued_content = queued["result"]["structuredContent"]
        self.assertEqual(queued_content["authority_mode"], "standing")
        self.assertEqual(queued_content["execution"], "queued_for_standing_local_policy")
        self.assertFalse(queued_content["replayed"])
        self.assertNotIn("permission_request_id", queued_content)
        action_id = queued_content["action_id"]

        bridge_calls: list[str] = []

        def bridge(
            _args: SimpleNamespace,
            _project_root: Path,
            request: dict[str, Any],
        ) -> tuple[dict[str, Any], None]:
            self.assertEqual(request["authority_mode"], "standing")
            self.assertEqual(request["permission_request_id"], "standing")
            bridge_calls.append(request["action_id"])
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

        observed_status, observed = standing_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-standing-patch-status",
            "method": "tools/call",
            "params": {
                "name": "agent_workflow",
                "arguments": {"operation": "patch_status", "action_id": action_id},
            },
        })
        self.assertEqual(observed_status, 200)
        content = observed["result"]["structuredContent"]
        if content["execution"] != "effect_applied_pending_local_acceptance":
            raise AssertionError("standing status: " + json.dumps(content, sort_keys=True))
        self.assertTrue(content["patch_applied"])
        self.assertEqual(content["patch"]["file"]["path"], "src/fixture.txt")
        self.assertNotIn(patch, json.dumps(content))
        self.assertNotIn(str(self.workspace_root), json.dumps(content))

        # The central receipt may be committed before the node receives its
        # HTTP response.  Replaying the journal must submit the same digest,
        # receive the store's idempotent replay, and never invoke the mutation
        # bridge a second time.
        self.fixture_path.write_bytes(self.initial_content)
        retry_status, retry_queued = standing_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-standing-patch-lost-ack-queue",
            "method": "tools/call",
            "params": {
                "name": "agent_workflow",
                "arguments": {
                    "operation": "apply_patch",
                    "binding_id": self.binding["binding_id"],
                    "task_id": self.task["task_id"],
                    "path": "src/fixture.txt",
                    "preimage_sha256": hashlib.sha256(self.initial_content).hexdigest(),
                    "patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest(),
                    "validation_profile": "targeted",
                    "patch_envelope": patch,
                    "idempotency_key": "mcp-http-standing-patch-lost-ack-key",
                    "expected_facade_contract": contract,
                },
            },
        })
        self.assertEqual(retry_status, 200)
        lost_ack_action_id = retry_queued["result"]["structuredContent"]["action_id"]
        bridge_count_before = len(bridge_calls)
        original_submit_receipt = node_agent_module._submit_receipt
        lost_ack = False

        def submit_with_one_lost_ack(config: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
            nonlocal lost_ack
            response = original_submit_receipt(config, entry)
            receipt = entry.get("receipt")
            if (
                not lost_ack
                and isinstance(receipt, dict)
                and receipt.get("action_id") == lost_ack_action_id
            ):
                lost_ack = True
                raise OSError("standing receipt acknowledgement lost")
            return response

        with mock.patch("control_plane.node_agent._submit_receipt", side_effect=submit_with_one_lost_ack), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_approved_patch_bridge", side_effect=bridge), \
             self.assertRaisesRegex(OSError, "standing receipt acknowledgement lost"), \
             redirect_stdout(io.StringIO()):
            poll_approved_patch_once(self.args())
        self.assertTrue(lost_ack)
        self.assertEqual(len(bridge_calls), bridge_count_before + 1)
        self.assertEqual(self.fixture_path.read_bytes(), self.updated_content)

        with mock.patch("control_plane.node_agent._submit_receipt", side_effect=submit_with_one_lost_ack), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_approved_patch_bridge", side_effect=bridge), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_approved_patch_once(self.args()), 0)
        self.assertEqual(len(bridge_calls), bridge_count_before + 1)
        replayed = self.store.action_observation(owner_id=self.owner_id, action_id=lost_ack_action_id)
        self.assertEqual(replayed["delivery_state"], "settled")
        self.assertEqual([receipt["receipt_state"] for receipt in replayed["receipts"]], ["completed"])

        # A standing action whose preimage is stale must be rejected by the
        # local bridge before it can write.  The central standing scope alone
        # is not a claim that the current file still matches the task.
        stale_preimage_status, stale_preimage_queued = standing_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-standing-patch-stale-preimage-queue",
            "method": "tools/call",
            "params": {
                "name": "agent_workflow",
                "arguments": {
                    "operation": "apply_patch",
                    "binding_id": self.binding["binding_id"],
                    "task_id": self.task["task_id"],
                    "path": "src/fixture.txt",
                    "preimage_sha256": hashlib.sha256(self.initial_content).hexdigest(),
                    "patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest(),
                    "validation_profile": "targeted",
                    "patch_envelope": patch,
                    "idempotency_key": "mcp-http-standing-patch-stale-preimage-key",
                    "expected_facade_contract": contract,
                },
            },
        })
        self.assertEqual(stale_preimage_status, 200)
        stale_preimage_action_id = stale_preimage_queued["result"]["structuredContent"]["action_id"]
        stale_bridge_calls: list[str] = []

        def stale_preimage_bridge(
            _args: SimpleNamespace,
            _project_root: Path,
            request: dict[str, Any],
        ) -> tuple[None, str]:
            stale_bridge_calls.append(request["action_id"])
            return None, "CONTROL_PLANE_APPROVED_PATCH_PREIMAGE_MISMATCH"

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_approved_patch_bridge", side_effect=stale_preimage_bridge), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_approved_patch_once(self.args()), 0)
        self.assertEqual(stale_bridge_calls, [stale_preimage_action_id])
        self.assertEqual(self.fixture_path.read_bytes(), self.updated_content)
        stale_preimage_observation = self.store.action_observation(
            owner_id=self.owner_id,
            action_id=stale_preimage_action_id,
        )
        self.assertEqual(stale_preimage_observation["delivery_state"], "settled")
        self.assertEqual(
            [receipt["receipt_state"] for receipt in stale_preimage_observation["receipts"]],
            ["rejected"],
        )

        # A well-formed standing envelope for a relative path outside the
        # installed allowlist is rejected before the bridge and cannot create
        # a new file merely because the central account supplied that path.
        other_initial = b"other initial\n"
        other_updated = b"other updated\n"
        other_payload = base64.b64encode(zlib.compress(other_updated)).decode("ascii")
        other_patch = "\n".join((
            "*** Begin Patch",
            "*** Write Exact File: src/other.txt",
            "@@ encoding=zlib-base64 "
            f"preimage_sha256={hashlib.sha256(other_initial).hexdigest()} "
            f"postimage_sha256={hashlib.sha256(other_updated).hexdigest()}",
            "+" + other_payload,
            "*** End Patch",
            "",
        ))
        path_status, path_queued = standing_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-standing-patch-path-denied-queue",
            "method": "tools/call",
            "params": {
                "name": "agent_workflow",
                "arguments": {
                    "operation": "apply_patch",
                    "binding_id": self.binding["binding_id"],
                    "task_id": self.task["task_id"],
                    "path": "src/other.txt",
                    "preimage_sha256": hashlib.sha256(other_initial).hexdigest(),
                    "patch_sha256": hashlib.sha256(other_patch.encode("utf-8")).hexdigest(),
                    "validation_profile": "targeted",
                    "patch_envelope": other_patch,
                    "idempotency_key": "mcp-http-standing-patch-path-denied-key",
                    "expected_facade_contract": contract,
                },
            },
        })
        self.assertEqual(path_status, 200)
        path_action_id = path_queued["result"]["structuredContent"]["action_id"]
        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_approved_patch_bridge") as bridge, \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_approved_patch_once(self.args()), 0)
        bridge.assert_not_called()
        self.assertFalse((self.workspace_root / "src" / "other.txt").exists())
        path_observation = self.store.action_observation(owner_id=self.owner_id, action_id=path_action_id)
        self.assertEqual(path_observation["delivery_state"], "settled")
        self.assertEqual([receipt["receipt_state"] for receipt in path_observation["receipts"]], ["rejected"])

        # Once the mutation bridge has crossed its prepared boundary but cannot
        # determine whether the local effect happened, standing status must be
        # UNKNOWN/reconcile_required and a later poll must not redeliver it.
        unknown_status, unknown_queued = standing_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-standing-patch-unknown-queue",
            "method": "tools/call",
            "params": {
                "name": "agent_workflow",
                "arguments": {
                    "operation": "apply_patch",
                    "binding_id": self.binding["binding_id"],
                    "task_id": self.task["task_id"],
                    "path": "src/fixture.txt",
                    "preimage_sha256": hashlib.sha256(self.initial_content).hexdigest(),
                    "patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest(),
                    "validation_profile": "targeted",
                    "patch_envelope": patch,
                    "idempotency_key": "mcp-http-standing-patch-unknown-key",
                    "expected_facade_contract": contract,
                },
            },
        })
        self.assertEqual(unknown_status, 200)
        unknown_action_id = unknown_queued["result"]["structuredContent"]["action_id"]
        unknown_bridge_calls: list[str] = []

        def unknown_bridge(
            _args: SimpleNamespace,
            _project_root: Path,
            request: dict[str, Any],
        ) -> tuple[None, str]:
            unknown_bridge_calls.append(request["action_id"])
            return None, "CONTROL_PLANE_APPROVED_PATCH_TIMEOUT"

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_approved_patch_bridge", side_effect=unknown_bridge), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_approved_patch_once(self.args()), 0)
        self.assertEqual(unknown_bridge_calls, [unknown_action_id])
        unknown_observation = self.store.action_observation(owner_id=self.owner_id, action_id=unknown_action_id)
        self.assertEqual(unknown_observation["delivery_state"], "reconcile_required")
        self.assertEqual([receipt["receipt_state"] for receipt in unknown_observation["receipts"]], ["unknown"])

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_approved_patch_bridge") as unknown_retry_bridge, \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_approved_patch_once(self.args()), 0)
        unknown_retry_bridge.assert_not_called()
        unknown_status, unknown_projection = standing_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-standing-patch-unknown-status",
            "method": "tools/call",
            "params": {
                "name": "agent_workflow",
                "arguments": {"operation": "patch_status", "action_id": unknown_action_id},
            },
        })
        self.assertEqual(unknown_status, 200)
        unknown_content = unknown_projection["result"]["structuredContent"]
        self.assertEqual(unknown_content["execution"], "local_patch_effect_unknown_reconcile_required")
        self.assertEqual(unknown_content["patch_effect_state"], "unknown")
        self.assertTrue(unknown_content["reconciliation_required"])
        self.assertNotIn(patch, json.dumps(unknown_content))

        # A local policy/generation mismatch must reject the next action before
        # the mutation bridge.  The central standing scope remains valid, but
        # the node's current workspace generation is the final authority.
        stale_policy = {**policy, "workspace_generation": "generation-stale-0001"}
        (self.data_root / "control-plane-approved-patch-policy.json").write_text(
            json.dumps(stale_policy, separators=(",", ":")), encoding="utf-8"
        )
        stale_status, stale_queued = standing_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-standing-patch-stale-policy",
            "method": "tools/call",
            "params": {
                "name": "agent_workflow",
                "arguments": {
                    "operation": "apply_patch",
                    "binding_id": self.binding["binding_id"],
                    "task_id": self.task["task_id"],
                    "path": "src/fixture.txt",
                    "preimage_sha256": hashlib.sha256(self.initial_content).hexdigest(),
                    "patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest(),
                    "validation_profile": "targeted",
                    "patch_envelope": patch,
                    "idempotency_key": "mcp-http-standing-patch-stale-policy-key",
                    "expected_facade_contract": contract,
                },
            },
        })
        self.assertEqual(stale_status, 200)
        stale_action_id = stale_queued["result"]["structuredContent"]["action_id"]
        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_approved_patch_bridge") as bridge, \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_approved_patch_once(self.args()), 0)
        bridge.assert_not_called()
        stale_observation = self.store.action_observation(
            owner_id=self.owner_id,
            action_id=stale_action_id,
        )
        self.assertEqual(stale_observation["delivery_state"], "settled")
        self.assertEqual(
            [receipt["receipt_state"] for receipt in stale_observation["receipts"]],
            ["rejected"],
        )
        self.assertEqual(self.fixture_path.read_bytes(), self.updated_content)

    def test_oauth_standing_patch_recovery_crash_is_unknown_and_not_redelivered(self) -> None:
        """A real Recovery process crash after the local patch never retries it."""

        _standing_server, _standing_url, standing_post, contract = self._standing_http_fixture()
        runtime_args, fixture_file, process_holder, restart = self._start_recovery_patch_fixture(
            crash_after_patch_result=True,
        )
        runtime_config = json.loads(Path(runtime_args.config).read_text(encoding="utf-8"))
        _install_approved_patch_policy_values(
            runtime_args,
            config_path=Path(runtime_args.config),
            config=runtime_config,
            owner_id=self.owner_id,
            workspace_id=self.workspace_id,
            workspace_generation=self.workspace_generation,
            expires_at_ms=None,
            facade_contract=contract,
            allowed_relative_paths=["src/fixture.txt"],
            max_patch_bytes=4096,
            max_file_bytes=4096,
        )
        app_data = str(Path(runtime_args.data_root).parent)
        with mock.patch.dict(os.environ, {"APPDATA": app_data}, clear=False), redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(runtime_args), 0)

        claimed_status, claimed = standing_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-standing-recovery-crash-claim",
            "method": "tools/call",
            "params": {"name": "task_control", "arguments": {
                "operation": "writer_claim", "task_id": self.task["task_id"],
            }},
        })
        self.assertEqual(claimed_status, 200)
        self.assertEqual(claimed["result"]["structuredContent"]["writer_lease"]["state"], "held")
        patch = self._patch_envelope()
        queued_status, queued = standing_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-standing-recovery-crash-queue",
            "method": "tools/call",
            "params": {"name": "agent_workflow", "arguments": {
                "operation": "apply_patch",
                "binding_id": self.binding["binding_id"],
                "task_id": self.task["task_id"],
                "path": "src/fixture.txt",
                "preimage_sha256": hashlib.sha256(self.initial_content).hexdigest(),
                "patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest(),
                "validation_profile": "targeted",
                "patch_envelope": patch,
                "idempotency_key": "mcp-http-standing-recovery-crash-key",
                "expected_facade_contract": contract,
            }},
        })
        self.assertEqual(queued_status, 200)
        action_id = queued["result"]["structuredContent"]["action_id"]

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": app_data}, clear=False), \
             redirect_stdout(io.StringIO()) as first_output:
            self.assertEqual(poll_approved_patch_once(runtime_args), 0)
        first = json.loads(first_output.getvalue())
        self.assertEqual(
            first["unknown_action_ids"],
            [action_id],
            msg=json.dumps({"first": first, "observation": self.store.action_observation(owner_id=self.owner_id, action_id=action_id)}, sort_keys=True),
        )
        process = process_holder["process"]
        self.assertIsNotNone(process)
        process.wait(timeout=5)
        self.assertEqual(self.fixture_path.read_bytes(), self.updated_content)
        fixture = json.loads(fixture_file.read_text(encoding="utf-8"))
        observation = json.loads(Path(fixture["observation_file"]).read_text(encoding="utf-8"))
        self.assertEqual(observation["crash"]["stage"], "after_patch_result")
        self.assertEqual(sum(item["operation"] == "apply_patch" for item in observation["mcp_calls"]), 1)
        unknown = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(unknown["delivery_state"], "reconcile_required")
        self.assertEqual([item["receipt_state"] for item in unknown["receipts"]], ["unknown"])

        # The action is already reconcile-required.  A new Recovery process
        # may restart and heartbeat, but it must not receive a second patch.
        restart(crash_after_patch_result=False)
        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": app_data}, clear=False), \
             redirect_stdout(io.StringIO()) as second_output:
            self.assertEqual(poll_approved_patch_once(runtime_args), 0)
        second = json.loads(second_output.getvalue())
        self.assertEqual(second["received_action_ids"], [])
        fixture = json.loads(fixture_file.read_text(encoding="utf-8"))
        observation_after_restart = json.loads(Path(fixture["observation_file"]).read_text(encoding="utf-8"))
        self.assertEqual(sum(item["operation"] == "apply_patch" for item in observation_after_restart["mcp_calls"]), 1)
        self.assertEqual(self.fixture_path.read_bytes(), self.updated_content)

    def test_oauth_standing_patch_recovery_lost_ack_replays_without_second_effect(self) -> None:
        """A completed central receipt is replayed after ACK loss, not patched twice."""

        _standing_server, _standing_url, standing_post, contract = self._standing_http_fixture()
        runtime_args, fixture_file, _process_holder, _restart = self._start_recovery_patch_fixture()
        runtime_config = json.loads(Path(runtime_args.config).read_text(encoding="utf-8"))
        _install_approved_patch_policy_values(
            runtime_args,
            config_path=Path(runtime_args.config),
            config=runtime_config,
            owner_id=self.owner_id,
            workspace_id=self.workspace_id,
            workspace_generation=self.workspace_generation,
            expires_at_ms=None,
            facade_contract=contract,
            allowed_relative_paths=["src/fixture.txt"],
            max_patch_bytes=4096,
            max_file_bytes=4096,
        )
        app_data = str(Path(runtime_args.data_root).parent)
        with mock.patch.dict(os.environ, {"APPDATA": app_data}, clear=False), redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(runtime_args), 0)
        claimed_status, _claimed = standing_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-standing-recovery-ack-claim",
            "method": "tools/call",
            "params": {"name": "task_control", "arguments": {
                "operation": "writer_claim", "task_id": self.task["task_id"],
            }},
        })
        self.assertEqual(claimed_status, 200)
        patch = self._patch_envelope()
        queued_status, queued = standing_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-standing-recovery-ack-queue",
            "method": "tools/call",
            "params": {"name": "agent_workflow", "arguments": {
                "operation": "apply_patch",
                "binding_id": self.binding["binding_id"],
                "task_id": self.task["task_id"],
                "path": "src/fixture.txt",
                "preimage_sha256": hashlib.sha256(self.initial_content).hexdigest(),
                "patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest(),
                "validation_profile": "targeted",
                "patch_envelope": patch,
                "idempotency_key": "mcp-http-standing-recovery-ack-key",
                "expected_facade_contract": contract,
            }},
        })
        self.assertEqual(queued_status, 200)
        action_id = queued["result"]["structuredContent"]["action_id"]
        original_submit_receipt = node_agent_module._submit_receipt
        lost_ack = {"value": False}

        def submit_with_lost_ack(config: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
            response = original_submit_receipt(config, entry)
            receipt = entry.get("receipt")
            if not lost_ack["value"] and isinstance(receipt, dict) and receipt.get("action_id") == action_id:
                lost_ack["value"] = True
                raise OSError("approved-patch receipt acknowledgement lost")
            return response

        with mock.patch("control_plane.node_agent._submit_receipt", side_effect=submit_with_lost_ack), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": app_data}, clear=False), \
             redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(OSError, "approved-patch receipt acknowledgement lost"):
                poll_approved_patch_once(runtime_args)
        self.assertTrue(lost_ack["value"])
        self.assertEqual(self.fixture_path.read_bytes(), self.updated_content)
        fixture = json.loads(fixture_file.read_text(encoding="utf-8"))
        observation = json.loads(Path(fixture["observation_file"]).read_text(encoding="utf-8"))
        first_observation = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        if first_observation["receipts"] and first_observation["receipts"][0]["receipt_state"] != "completed":
            self.fail(json.dumps({"observation": observation, "central": first_observation}, sort_keys=True))
        self.assertEqual(sum(item["operation"] == "apply_patch" for item in observation["mcp_calls"]), 1)

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": app_data}, clear=False), \
             redirect_stdout(io.StringIO()) as replay_output:
            self.assertEqual(poll_approved_patch_once(runtime_args), 0)
        replay = json.loads(replay_output.getvalue())
        self.assertEqual(replay["received_action_ids"], [])
        fixture = json.loads(fixture_file.read_text(encoding="utf-8"))
        observation_after_replay = json.loads(Path(fixture["observation_file"]).read_text(encoding="utf-8"))
        self.assertEqual(sum(item["operation"] == "apply_patch" for item in observation_after_replay["mcp_calls"]), 1)
        settled = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(settled["delivery_state"], "settled", msg=json.dumps({"replay": replay, "observation": settled}, sort_keys=True))
        self.assertEqual([item["receipt_state"] for item in settled["receipts"]], ["completed"])

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
