from __future__ import annotations

import io
import json
import os
import subprocess
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
    _exec_journal_key,
    _install_exec_policy_values,
    _policy_digest,
    _read_exec_journal,
    _write_json_atomic,
    heartbeat,
    poll_exec_once,
)
from control_plane.store import ControlPlaneStore


ISSUER = "https://identity.example.test/tenant-exec-http-node"
RESOURCE = "https://mcp.example.test"
INTROSPECTION_URL = f"{ISSUER}/introspect"
READ_SCOPE = "control-plane.inventory"
WRITE_SCOPE = "control-plane.patch"


class _StaticVerifier:
    """Deterministic OAuth verifier for the real local HTTP ingress fixture."""

    def __init__(
        self,
        identity: OAuthAccessIdentity,
        *,
        identities: dict[str, OAuthAccessIdentity] | None = None,
    ) -> None:
        self.identity = identity
        self.identities = identities or {}

    def authenticate(self, token: str, *, required_scopes: object = None) -> OAuthAccessIdentity:
        identity = self.identities.get(token, self.identity)
        if required_scopes is not None and not set(required_scopes) <= set(identity.scopes):
            raise OAuthAuthenticationError("OAuth access token is invalid.")
        return identity


class McpExecHttpNodeE2ETests(unittest.TestCase):
    """Exercise OAuth → central queue → node exec poll → status/output.

    Central HTTP/OAuth, node heartbeat/poll, local policy, durable journal,
    receipt submission and MCP status/output projections are real.  The
    Recovery bridge is exercised through a separate Node process owning a real
    RecoveryIpcServer and RuntimeOrchestrator.controlPlaneExec; only the local
    Coding Tools MCP peer is deterministic HTTP fixture infrastructure.
    """

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mcp-exec-http-node-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.repo_root = Path(__file__).resolve().parents[2]
        self.app_data_root = self.directory / "appdata"
        self.app_data_root.mkdir()
        self.data_root = self.app_data_root / "web-mcp-assistant"
        self.store = ControlPlaneStore(self.directory / "control.sqlite3")
        self.owner_id = "owner_default"
        self.identity = OAuthAccessIdentity(
            issuer=ISSUER,
            subject="provider-subject-exec-http-node",
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
            exec_enabled=True,
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

        self.principal = self.store.link_oauth_principal(
            owner_id=self.owner_id,
            issuer=ISSUER,
            subject=self.identity.subject,
        )
        self.node = self.store.enroll_node(
            owner_id=self.owner_id,
            device_id="b3b8a0bb-4d2d-4f12-8c2a-9c7c0d8e1f01",
            endpoint_id="endpoint-http-exec-e2e-001",
            display_name="HTTP exec fixture node",
        )
        self.endpoint_id = "endpoint-http-exec-e2e-001"
        self.workspace_id = "workspace-http-exec-e2e-001"
        self.workspace_generation = "generation-http-exec-e2e-001"
        self.store.register_node_workspace(
            device_id=self.node["device_id"],
            workspace_id=self.workspace_id,
            workspace_generation=self.workspace_generation,
            display_name="HTTP exec fixture workspace",
            capabilities={"read": True, "write": True, "exec": True},
        )
        self.binding = self.store.create_binding(
            owner_id=self.owner_id,
            device_id=self.node["device_id"],
            workspace_id=self.workspace_id,
            workspace_generation=self.workspace_generation,
            display_name="HTTP exec fixture workspace",
        )
        self.workspace_root = self.directory / "workspace"
        self.workspace_root.mkdir()
        self.config_path = self.data_root / "control-plane-node.json"
        self.registry_path = self.data_root / "control-plane-workspaces.json"
        self.data_root.mkdir(parents=True)
        self.config = {
            "server_url": self.main_url,
            "device_id": self.node["device_id"],
            "endpoint_id": self.endpoint_id,
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
                            "display_name": "HTTP exec fixture workspace",
                            "capabilities": {"read": True, "write": True, "exec": True},
                            "created_at_ms": 1_700_000_000_000,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.runtime_fixture_file = self.directory / "recovery-exec-fixture.json"
        self.runtime_ready_file = self.directory / "recovery-exec-ready.json"
        self.runtime_observation_file = self.directory / "recovery-exec-observation.json"
        self.runtime_fixture_file.write_text(
            json.dumps(
                {
                    "app_data": str(self.app_data_root),
                    "app_root": str(self.repo_root),
                    "workspace": str(self.workspace_root.resolve()),
                    "device_id": self.node["device_id"],
                    "activation_epoch_id": "activation-http-exec-e2e-001",
                    "mcp_token": "mcp-runtime-fixture-token-0001",
                    "ready_file": str(self.runtime_ready_file),
                    "observation_file": str(self.runtime_observation_file),
                    "process_instance_id": "mcp-process-http-exec-e2e-001",
                    "server_instance_id": "mcp-server-http-exec-e2e-001",
                    "tool_contract_sha256": "a" * 64,
                    "poll_running_until_stop": self._testMethodName in {
                        "test_oauth_exec_stop_runs_through_real_recovery_job",
                        "test_oauth_exec_stop_pending_survives_recovery_restart",
                    },
                    # The parity test sends one terminal command per poll so
                    # four local workflow classes can share the same durable
                    # task/writer/receipt path without waiting on a synthetic
                    # running Job between each command.
                    "exec_terminal_first": self._testMethodName in {
                        "test_oauth_exec_workflow_parity_uses_one_local_lane",
                        "test_two_oauth_clients_route_exec_to_same_bound_node_and_receipt",
                    },
                    "drop_after_exec_run": self._testMethodName == "test_oauth_exec_mcp_disconnect_becomes_unknown_without_retry",
                    "crash_after_exec_run": self._testMethodName == "test_oauth_exec_recovery_process_crash_restarts_without_redelivery",
                    "crash_after_terminal_result": self._testMethodName == "test_oauth_exec_terminal_result_lost_on_recovery_crash_requires_reconcile",
                    "crash_after_exec_stop": self._testMethodName == "test_oauth_exec_stop_pending_survives_recovery_restart",
                }
            ),
            encoding="utf-8",
        )
        self.runtime_process = None
        self._start_runtime_fixture()
        self.addCleanup(self._stop_runtime_fixture)

    def _start_runtime_fixture(self) -> None:
        helper = self.repo_root / "tests" / "recovery-exec-process-fixture.cjs"
        self.runtime_ready_file.unlink(missing_ok=True)
        environment = dict(os.environ)
        environment["APPDATA"] = str(self.app_data_root)
        self.runtime_process = subprocess.Popen(
            ["node", str(helper), "--fixture", str(self.runtime_fixture_file)],
            cwd=self.repo_root,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if self.runtime_ready_file.is_file():
                return
            if self.runtime_process.poll() is not None:
                stderr = self.runtime_process.stderr.read() if self.runtime_process.stderr else ""
                self.fail(f"Recovery process fixture exited early: {stderr}")
            time.sleep(0.05)
        stderr = self.runtime_process.stderr.read() if self.runtime_process.stderr else ""
        self.fail(f"Recovery process fixture did not become ready: {stderr}")

    def _stop_runtime_fixture(self) -> None:
        process = self.runtime_process
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
        self.runtime_process = None

    def _restart_runtime_fixture(self, *, crash_after_exec_run: bool = False) -> None:
        """Restart the real Recovery process while preserving its journal observation."""

        self._stop_runtime_fixture()
        fixture = json.loads(self.runtime_fixture_file.read_text(encoding="utf-8"))
        fixture["crash_after_exec_run"] = crash_after_exec_run
        self.runtime_fixture_file.write_text(json.dumps(fixture), encoding="utf-8")
        self._start_runtime_fixture()

    def _crash_runtime_fixture(self) -> None:
        """Kill the Recovery process without running its graceful descriptor cleanup."""

        process = self.runtime_process
        if process is None:
            return
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        if process.stderr is not None:
            process.stderr.close()
        self.runtime_process = None

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
            project_root=str(self.repo_root),
            node="node",
            runtime_mode="development",
            timeout_seconds=20,
            runtime_instance_id="mcp-process-http-exec-e2e-001",
            mcp_server_instance_id="mcp-server-http-exec-e2e-001",
            activation_epoch="activation-http-exec-e2e-001",
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
            "mcp_process_instance_id": "mcp-process-http-exec-e2e-001",
            "mcp_server_instance_id": "mcp-server-http-exec-e2e-001",
            "activation_epoch_id": "activation-http-exec-e2e-001",
            "current_activation_epoch_id": "activation-http-exec-e2e-001",
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

    def _mcp_post_as(self, token: str, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        return self._response(
            Request(
                f"{self.mcp_url}/mcp",
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
        )

    def _mcp_post(self, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        return self._mcp_post_as("opaque-source-fixture-token", body)

    def _contract(self) -> dict[str, Any]:
        return {
            key: self.mcp_server.mcp_facade.contract[key]
            for key in ("schema_version", "profile", "sha256")
        }

    def _install_policy(
        self,
        contract: dict[str, Any],
        *,
        allowed_argv_prefixes: list[list[str]] | None = None,
    ) -> dict[str, Any]:
        policy = _install_exec_policy_values(
            owner_id=self.owner_id,
            device_id=self.node["device_id"],
            endpoint_id=self.endpoint_id,
            workspace_id=self.workspace_id,
            workspace_generation=self.workspace_generation,
            server_origin=self.main_url,
            facade_contract=contract,
            allowed_argv_prefixes=allowed_argv_prefixes or [["python3", "-c"]],
            max_timeout_ms=60_000,
            max_output_bytes=32_768,
        )
        _write_json_atomic(self.data_root / "control-plane-exec-policy.json", policy)
        return policy

    def _open_and_queue_exec(
        self,
        contract: dict[str, Any],
        *,
        label: str,
        task_key: str,
        action_key: str,
    ) -> tuple[dict[str, Any], str]:
        """Open one writer-owned task and queue the fixed fixture command."""

        opened_status, opened = self._mcp_post({
            "jsonrpc": "2.0", "id": f"{task_key}-open", "method": "tools/call",
            "params": {"name": "workspace_context", "arguments": {
                "operation": "task_open", "binding_id": self.binding["binding_id"],
                "label": label, "idempotency_key": task_key,
            }},
        })
        self.assertEqual(opened_status, 200)
        task = opened["result"]["structuredContent"]["task"]
        claimed_status, claimed = self._mcp_post({
            "jsonrpc": "2.0", "id": f"{task_key}-claim", "method": "tools/call",
            "params": {"name": "task_control", "arguments": {
                "operation": "writer_claim", "task_id": task["task_id"],
            }},
        })
        self.assertEqual(claimed_status, 200)
        self.assertEqual(claimed["result"]["structuredContent"]["writer_lease"]["state"], "held")
        queued_status, queued = self._mcp_post({
            "jsonrpc": "2.0", "id": f"{action_key}-queue", "method": "tools/call",
            "params": {"name": "exec_command", "arguments": {
                "operation": "exec_run", "binding_id": self.binding["binding_id"],
                "task_id": task["task_id"], "argv": ["python3", "-c", "print('lost-ack')"],
                "cwd": "", "timeout_ms": 60_000, "max_output_bytes": 32_768,
                "idempotency_key": action_key, "expected_facade_contract": contract,
            }},
        })
        self.assertEqual(queued_status, 200)
        return task, queued["result"]["structuredContent"]["action_id"]

    def test_oauth_exec_workflow_parity_uses_one_local_lane(self) -> None:
        """Git/build/test/deploy all stay on the same local structured lane.

        The command names are deliberately supplied by the node's standing
        allowlist.  Ubuntu only carries structured argv and the task target;
        it does not gain a second executor or a shell/deployment policy.
        The deterministic MCP peer records the exact argv received by the
        Recovery process so this test proves routing and receipt parity, not
        that a Linux fixture is a Windows toolchain or live deployment.
        """

        contract = self._contract()
        workflow_commands = [
            ("git", ["git", "--version"]),
            ("build", ["npm", "run", "build"]),
            ("test", ["npm", "test"]),
            ("deploy", ["npm", "run", "deploy"]),
        ]
        policy = self._install_policy(
            contract,
            allowed_argv_prefixes=[command for _label, command in workflow_commands],
        )
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)

        opened_status, opened = self._mcp_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-exec-parity-task-open",
            "method": "tools/call",
            "params": {"name": "workspace_context", "arguments": {
                "operation": "task_open",
                "binding_id": self.binding["binding_id"],
                "label": "Git build test deploy parity",
                "idempotency_key": "mcp-http-exec-parity-task-open-key",
            }},
        })
        self.assertEqual(opened_status, 200)
        task = opened["result"]["structuredContent"]["task"]
        claimed_status, claimed = self._mcp_post({
            "jsonrpc": "2.0",
            "id": "mcp-http-exec-parity-writer-claim",
            "method": "tools/call",
            "params": {"name": "task_control", "arguments": {
                "operation": "writer_claim", "task_id": task["task_id"],
            }},
        })
        self.assertEqual(claimed_status, 200)
        self.assertEqual(claimed["result"]["structuredContent"]["writer_lease"]["state"], "held")

        action_ids: list[str] = []
        for index, (_label, argv) in enumerate(workflow_commands, start=1):
            queued_status, queued = self._mcp_post({
                "jsonrpc": "2.0",
                "id": f"mcp-http-exec-parity-queue-{index}",
                "method": "tools/call",
                "params": {"name": "exec_command", "arguments": {
                    "operation": "exec_run",
                    "binding_id": self.binding["binding_id"],
                    "task_id": task["task_id"],
                    "argv": argv,
                    "cwd": "",
                    "timeout_ms": 60_000,
                    "max_output_bytes": 32_768,
                    "idempotency_key": f"mcp-http-exec-parity-action-{index:03d}",
                    "expected_facade_contract": contract,
                }},
            })
            self.assertEqual(queued_status, 200)
            queued_content = queued["result"]["structuredContent"]
            self.assertEqual(queued_content["execution"], "queued_for_local_admission")
            action_id = queued_content["action_id"]
            action_ids.append(action_id)
            with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
                 mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
                 mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
                 redirect_stdout(io.StringIO()) as poll_output:
                self.assertEqual(poll_exec_once(self.args()), 0)
            poll_receipt = json.loads(poll_output.getvalue())
            self.assertEqual(poll_receipt["received_action_ids"], [action_id])
            settled = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
            self.assertEqual(settled["delivery_state"], "settled")
            self.assertEqual([item["receipt_state"] for item in settled["receipts"]], ["completed"])
            payload = json.loads(settled["receipts"][-1]["payload_json"])
            self.assertEqual(payload["exit_code"], 0)
            self.assertEqual(payload["task_id"], task["task_id"])
            self.assertEqual(payload["writer_lease_generation"], 1)

        observation = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        routed_argv = [item["argv"] for item in observation["mcp_calls"] if item["operation"] == "exec_run"]
        self.assertEqual(routed_argv, [command for _label, command in workflow_commands])
        self.assertEqual(
            [item["action"] for item in observation["recovery_calls"]],
            ["runtime.control_plane_exec"] * len(workflow_commands),
        )
        linked = self.store.list_mcp_task_actions(
            owner_id=self.owner_id,
            principal_id=self.principal["principal_id"],
            task_id=task["task_id"],
        )
        self.assertEqual([row["action_id"] for row in linked], action_ids)
        # The public task link is owner/principal scoped; use the central
        # observation path for the exact four action ids instead of exposing a
        # local credential or absolute workspace path.
        for action_id in action_ids:
            observed = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
            self.assertEqual(observed["task_id"], task["task_id"])
        self.assertNotIn(self.config["node_secret"], json.dumps(observation))
        self.assertNotIn(str(self.workspace_root), json.dumps(observation))

    def test_oauth_exec_runs_through_http_node_journal_and_terminal_status(self) -> None:
        contract = self._contract()
        policy = self._install_policy(contract)

        # Node admission uses the real authenticated HTTP heartbeat, so the
        # central poll route will allocate a durable attempt below.
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)

        opened_status, opened = self._mcp_post(
            {
                "jsonrpc": "2.0",
                "id": "mcp-http-exec-task-open",
                "method": "tools/call",
                "params": {
                    "name": "workspace_context",
                    "arguments": {
                        "operation": "task_open",
                        "binding_id": self.binding["binding_id"],
                        "label": "HTTP exec fixture task",
                        "idempotency_key": "mcp-http-exec-task-open-key",
                    },
                },
            }
        )
        self.assertEqual(opened_status, 200)
        task = opened["result"]["structuredContent"]["task"]

        claimed_status, claimed = self._mcp_post(
            {
                "jsonrpc": "2.0",
                "id": "mcp-http-exec-writer-claim",
                "method": "tools/call",
                "params": {
                    "name": "task_control",
                    "arguments": {"operation": "writer_claim", "task_id": task["task_id"]},
                },
            }
        )
        self.assertEqual(claimed_status, 200)
        self.assertEqual(claimed["result"]["structuredContent"]["writer_lease"]["state"], "held")

        queued_status, queued = self._mcp_post(
            {
                "jsonrpc": "2.0",
                "id": "mcp-http-exec-queue",
                "method": "tools/call",
                "params": {
                    "name": "exec_command",
                    "arguments": {
                        "operation": "exec_run",
                        "binding_id": self.binding["binding_id"],
                        "task_id": task["task_id"],
                        "argv": ["python3", "-c", "print('http-node-exec')"],
                        "cwd": "",
                        "timeout_ms": 60_000,
                        "max_output_bytes": 32_768,
                        "idempotency_key": "mcp-http-exec-action-key",
                        "expected_facade_contract": contract,
                    },
                },
            }
        )
        self.assertEqual(queued_status, 200)
        queued_content = queued["result"]["structuredContent"]
        self.assertEqual(queued_content["execution"], "queued_for_local_admission")
        action_id = queued_content["action_id"]
        action_before = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(action_before["writer_lease_generation"], 1)
        self.assertEqual(action_before["task_id"], task["task_id"])

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as first_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        first_receipt = json.loads(first_output.getvalue())
        self.assertEqual(first_receipt["execution"], "exec_once")
        self.assertEqual(first_receipt["received_action_ids"], [action_id])
        self.assertEqual(
            first_receipt["completed_action_ids"],
            [f"{action_id}:running"],
            msg=f"first node poll did not accept the running Job: {first_receipt}; action={self.store.action_observation(owner_id=self.owner_id, action_id=action_id)}; observation={self.runtime_observation_file.read_text(encoding='utf-8')}",
        )

        accepted = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(accepted["delivery_state"], "accepted")
        self.assertEqual([item["receipt_state"] for item in accepted["receipts"]], ["accepted"])
        local_handle = accepted["receipts"][0]["local_handle"]

        running_status, running = self._mcp_post(
            {
                "jsonrpc": "2.0",
                "id": "mcp-http-exec-running-status",
                "method": "tools/call",
                "params": {
                    "name": "exec_command",
                    "arguments": {"operation": "exec_status", "action_id": action_id},
                },
            }
        )
        self.assertEqual(running_status, 200)
        running_content = running["result"]["structuredContent"]
        self.assertEqual(running_content["execution"], "local_admission_pending_or_running")
        self.assertEqual(running_content["process_state"], "pending_or_running")
        self.assertIsNone(running_content["exit_code"])

        running_output_status, running_output = self._mcp_post(
            {
                "jsonrpc": "2.0",
                "id": "mcp-http-exec-running-output",
                "method": "tools/call",
                "params": {
                    "name": "command_control",
                    "arguments": {"operation": "exec_output", "action_id": action_id, "cursor": 0, "max_bytes": 4096},
                },
            }
        )
        self.assertEqual(running_output_status, 200)
        self.assertFalse(running_output["result"]["structuredContent"]["has_output"])

        # A second node poll observes the journaled handle, calls exec_poll,
        # and submits the terminal receipt.  It must not dequeue/spawn again.
        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as second_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        second_receipt = json.loads(second_output.getvalue())
        self.assertEqual(second_receipt["received_action_ids"], [])
        ready = json.loads(self.runtime_ready_file.read_text(encoding="utf-8"))
        command_id = ready["command"]["command_id"]
        observation = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual([item["operation"] for item in observation["mcp_calls"]], ["bind", "exec_run", "bind", "poll"])
        self.assertEqual([item["action"] for item in observation["recovery_calls"]], ["runtime.control_plane_exec", "runtime.control_plane_exec"])
        self.assertTrue(all(item["has_attestation"] for item in observation["mcp_calls"]))

        settled = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(settled["delivery_state"], "settled")
        self.assertEqual([item["receipt_state"] for item in settled["receipts"]], ["accepted", "completed"])
        terminal_payload = json.loads(settled["receipts"][-1]["payload_json"])
        self.assertEqual(terminal_payload["task_id"], task["task_id"])
        self.assertEqual(terminal_payload["writer_lease_generation"], 1)
        self.assertEqual(terminal_payload["command_id"], command_id)
        self.assertEqual(terminal_payload["job_id"], ready["command"]["job_id"])
        self.assertEqual(terminal_payload["run_id"], "run-recovery-exec-fixture-001")
        self.assertEqual(terminal_payload["wave_id"], "wave-recovery-exec-fixture-001")

        terminal_status, terminal = self._mcp_post(
            {
                "jsonrpc": "2.0",
                "id": "mcp-http-exec-terminal-status",
                "method": "tools/call",
                "params": {
                    "name": "exec_command",
                    "arguments": {"operation": "exec_status", "action_id": action_id},
                },
            }
        )
        self.assertEqual(terminal_status, 200)
        terminal_content = terminal["result"]["structuredContent"]
        self.assertEqual(terminal_content["execution"], "completed_exec_relay")
        self.assertEqual(terminal_content["process_state"], "completed")
        self.assertEqual(terminal_content["exit_code"], 0)
        self.assertEqual(terminal_content["exec"]["output_bytes"], len("fixture process completed\n".encode()))

        output_status, output = self._mcp_post(
            {
                "jsonrpc": "2.0",
                "id": "mcp-http-exec-terminal-output",
                "method": "tools/call",
                "params": {
                    "name": "command_control",
                    "arguments": {"operation": "exec_output", "action_id": action_id, "cursor": 0, "max_bytes": 4096},
                },
            }
        )
        self.assertEqual(output_status, 200)
        output_content = output["result"]["structuredContent"]
        self.assertTrue(output_content["has_output"])
        self.assertIn("fixture process completed", output_content["output"])
        rendered = json.dumps(terminal_content) + json.dumps(output_content)
        self.assertNotIn(self.config["node_secret"], rendered)
        self.assertNotIn(str(self.workspace_root), rendered)
        self.assertNotIn(_policy_digest(policy), rendered)

        journal_path = self.config_path.with_name(f"{self.config_path.name}.exec-journal.json")
        journal = _read_exec_journal(journal_path)
        saved = journal["entries"][_exec_journal_key(action_id, settled["attempts"][0]["attempt_id"])]
        self.assertEqual(saved["state"], "completed")
        self.assertEqual(saved["receipt"]["local_handle"], local_handle)
        self.assertTrue(saved["receipt"]["receipt_submitted"])

    def test_two_oauth_clients_route_exec_to_same_bound_node_and_receipt(self) -> None:
        """Two access tokens for one account drive one pinned local target.

        Client A owns the task/writer lease and queues the command.  The node
        executes it once, while client B (the same issuer/subject account)
        reads the terminal status and output.  This is the concrete
        account-shared placement contract: the chat client is not the
        execution host and the task never retargets away from the selected
        binding.
        """

        self.verifier.identities = {
            "client-a-token": self.identity,
            "client-b-token": self.identity,
        }
        contract = self._contract()
        policy = self._install_policy(contract)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)

        def post(token: str, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            return self._mcp_post_as(token, body)

        opened_status, opened = post(
            "client-a-token",
            {
                "jsonrpc": "2.0",
                "id": "shared-exec-task-open",
                "method": "tools/call",
                "params": {
                    "name": "workspace_context",
                    "arguments": {
                        "operation": "task_open",
                        "binding_id": self.binding["binding_id"],
                        "label": "Shared account execution task",
                        "idempotency_key": "shared-exec-task-open-key",
                    },
                },
            },
        )
        self.assertEqual(opened_status, 200)
        task = opened["result"]["structuredContent"]["task"]

        claimed_status, claimed = post(
            "client-a-token",
            {
                "jsonrpc": "2.0",
                "id": "shared-exec-task-claim",
                "method": "tools/call",
                "params": {
                    "name": "task_control",
                    "arguments": {"operation": "writer_claim", "task_id": task["task_id"]},
                },
            },
        )
        self.assertEqual(claimed_status, 200)
        self.assertEqual(claimed["result"]["structuredContent"]["writer_lease"]["state"], "held")

        queued_status, queued = post(
            "client-a-token",
            {
                "jsonrpc": "2.0",
                "id": "shared-exec-action-queue",
                "method": "tools/call",
                "params": {
                    "name": "exec_command",
                    "arguments": {
                        "operation": "exec_run",
                        "binding_id": self.binding["binding_id"],
                        "task_id": task["task_id"],
                        "argv": ["python3", "-c", "print('shared-account')"],
                        "cwd": "",
                        "timeout_ms": 60_000,
                        "max_output_bytes": 32_768,
                        "idempotency_key": "shared-exec-action-key",
                        "expected_facade_contract": contract,
                    },
                },
            },
        )
        self.assertEqual(queued_status, 200)
        action_id = queued["result"]["structuredContent"]["action_id"]
        before = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(before["binding_id"], self.binding["binding_id"])
        self.assertEqual(before["device_id"], self.node["device_id"])
        self.assertEqual(before["workspace_id"], self.workspace_id)
        self.assertEqual(before["workspace_generation"], self.workspace_generation)

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as poll_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        receipt = json.loads(poll_output.getvalue())
        self.assertEqual(receipt["received_action_ids"], [action_id])
        self.assertEqual(receipt["completed_action_ids"], [action_id])

        settled = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(settled["delivery_state"], "settled")
        self.assertEqual([item["receipt_state"] for item in settled["receipts"]], ["completed"])
        self.assertEqual(settled["binding_id"], self.binding["binding_id"])
        self.assertEqual(settled["device_id"], self.node["device_id"])

        status, observed = post(
            "client-b-token",
            {
                "jsonrpc": "2.0",
                "id": "shared-exec-status-from-client-b",
                "method": "tools/call",
                "params": {
                    "name": "exec_command",
                    "arguments": {"operation": "exec_status", "action_id": action_id},
                },
            },
        )
        self.assertEqual(status, 200)
        observed_content = observed["result"]["structuredContent"]
        self.assertEqual(observed_content["execution"], "completed_exec_relay")
        self.assertEqual(observed_content["process_state"], "completed")
        self.assertEqual(observed_content["exit_code"], 0)

        output_status, output = post(
            "client-b-token",
            {
                "jsonrpc": "2.0",
                "id": "shared-exec-output-from-client-b",
                "method": "tools/call",
                "params": {
                    "name": "command_control",
                    "arguments": {"operation": "exec_output", "action_id": action_id, "cursor": 0, "max_bytes": 4096},
                },
            },
        )
        self.assertEqual(output_status, 200)
        output_content = output["result"]["structuredContent"]
        self.assertTrue(output_content["has_output"])
        self.assertIn("fixture process completed", output_content["output"])
        rendered = json.dumps(observed_content) + json.dumps(output_content)
        self.assertNotIn(self.config["node_secret"], rendered)
        self.assertNotIn(str(self.workspace_root), rendered)
        self.assertNotIn(_policy_digest(policy), rendered)

    def test_oauth_exec_replays_lost_accepted_receipt_without_respawn(self) -> None:
        """A lost receipt ACK is replayed before resume and never reruns exec_run."""

        contract = self._contract()
        self._install_policy(contract)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)
        task, action_id = self._open_and_queue_exec(
            contract,
            label="HTTP exec lost-ACK fixture task",
            task_key="mcp-http-exec-lost-ack-task-key",
            action_key="mcp-http-exec-lost-ack-action-key",
        )

        original_request = __import__("control_plane.node_agent", fromlist=["_request"])._request
        dropped = {"value": False}

        def lose_first_receipt_ack(
            url: str,
            path: str,
            payload: dict[str, Any],
            authorization: str | None = None,
        ) -> dict[str, Any]:
            response = original_request(url, path, payload, authorization)
            if path.endswith("/receipts") and not dropped["value"]:
                dropped["value"] = True
                raise RuntimeError("CONTROL_PLANE_TRANSPORT_UNAVAILABLE")
            return response

        # The central HTTP handler has already committed the accepted receipt
        # when the wrapper drops the response.  The node process must leave the
        # exact journal entry pending and surface the transport fault.
        with mock.patch("control_plane.node_agent._request", side_effect=lose_first_receipt_ack), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, "CONTROL_PLANE_TRANSPORT_UNAVAILABLE"):
                poll_exec_once(self.args())

        accepted = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(accepted["delivery_state"], "accepted")
        self.assertEqual([item["receipt_state"] for item in accepted["receipts"]], ["accepted"])
        journal = _read_exec_journal(self.config_path.with_name(f"{self.config_path.name}.exec-journal.json"))
        entry = journal["entries"][_exec_journal_key(action_id, accepted["attempts"][0]["attempt_id"])]
        self.assertEqual(entry["state"], "running")
        self.assertFalse(entry["receipt"]["receipt_submitted"])

        # The next invocation replays the same accepted receipt first, then
        # observes the same local handle.  It must not call exec_run again.
        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as second_output:
            try:
                self.assertEqual(poll_exec_once(self.args()), 0)
            except RuntimeError as error:
                self.fail(
                    f"lost-ACK replay failed: {error}; action={self.store.action_observation(owner_id=self.owner_id, action_id=action_id)}; "
                    f"journal={self.config_path.with_name(self.config_path.name + '.exec-journal.json').read_text(encoding='utf-8')}"
                )
        second_receipt = json.loads(second_output.getvalue())
        self.assertEqual(second_receipt["received_action_ids"], [])
        self.assertEqual(second_receipt["resumed"]["completed"], [action_id])
        settled = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(settled["delivery_state"], "settled")
        self.assertEqual([item["receipt_state"] for item in settled["receipts"]], ["accepted", "completed"])

        observation = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual(
            [item["operation"] for item in observation["mcp_calls"]],
            ["bind", "exec_run", "bind", "poll"],
        )
        self.assertEqual(
            [item["operation"] for item in observation["recovery_calls"]],
            ["exec_run", "exec_poll"],
        )

    def test_oauth_exec_mcp_disconnect_becomes_unknown_without_retry(self) -> None:
        """A local MCP disconnect after exec_run becomes reconcile-required once."""

        contract = self._contract()
        self._install_policy(contract)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)
        task, action_id = self._open_and_queue_exec(
            contract,
            label="HTTP exec MCP disconnect fixture task",
            task_key="mcp-http-exec-disconnect-task-key",
            action_key="mcp-http-exec-disconnect-action-key",
        )

        # The real Recovery process reaches the fixture MCP peer, which closes
        # the socket after recording exec_run.  No second bridge call is safe:
        # the durable result is unknown and central must require reconciliation.
        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as first_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        first_receipt = json.loads(first_output.getvalue())
        self.assertEqual(first_receipt["received_action_ids"], [action_id])
        self.assertEqual(first_receipt["unknown_action_ids"], [action_id])
        unknown = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(unknown["delivery_state"], "reconcile_required")
        self.assertEqual([item["receipt_state"] for item in unknown["receipts"]], ["unknown"])

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as second_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        second_receipt = json.loads(second_output.getvalue())
        self.assertEqual(second_receipt["received_action_ids"], [])
        self.assertEqual(second_receipt["submitted_receipts"], 0)
        final = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(final["delivery_state"], "reconcile_required")
        self.assertEqual([item["receipt_state"] for item in final["receipts"]], ["unknown"])

        observation = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual([item["operation"] for item in observation["mcp_calls"]], ["bind", "exec_run"])
        self.assertEqual([item["operation"] for item in observation["recovery_calls"]], ["exec_run"])
        self.assertEqual(task["task_id"], final["task_id"])

    def test_oauth_exec_recovery_process_crash_restarts_without_redelivery(self) -> None:
        """A Recovery process crash after exec_run is unknown, never redelivered."""

        contract = self._contract()
        self._install_policy(contract)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)
        task, action_id = self._open_and_queue_exec(
            contract,
            label="HTTP exec Recovery crash fixture task",
            task_key="mcp-http-exec-recovery-crash-task-key",
            action_key="mcp-http-exec-recovery-crash-action-key",
        )

        crashed_pid = self.runtime_process.pid
        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as first_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        first_receipt = json.loads(first_output.getvalue())
        self.assertEqual(first_receipt["received_action_ids"], [action_id])
        self.assertEqual(first_receipt["unknown_action_ids"], [action_id])
        self.assertIsNotNone(self.runtime_process.poll(), "fixture must have crashed")

        unknown = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(unknown["delivery_state"], "reconcile_required")
        self.assertEqual([item["receipt_state"] for item in unknown["receipts"]], ["unknown"])
        observation_after_crash = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual(observation_after_crash["crash"]["stage"], "after_exec_run")

        # Restart the same Recovery installation and descriptor.  The queued
        # action is already reconcile-required, so this process must not see a
        # second exec_run even though the node polls again.
        self._restart_runtime_fixture(crash_after_exec_run=False)
        self.assertNotEqual(self.runtime_process.pid, crashed_pid)
        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as second_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        second_receipt = json.loads(second_output.getvalue())
        self.assertEqual(second_receipt["received_action_ids"], [])
        self.assertEqual(second_receipt["submitted_receipts"], 0)

        final = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(final["task_id"], task["task_id"])
        self.assertEqual(final["delivery_state"], "reconcile_required")
        self.assertEqual([item["receipt_state"] for item in final["receipts"]], ["unknown"])
        observation = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual(len(observation["launches"]), 2)
        self.assertEqual([item["operation"] for item in observation["mcp_calls"]], ["bind", "exec_run"])
        self.assertEqual([item["operation"] for item in observation["recovery_calls"]], ["exec_run"])

    def test_oauth_exec_running_job_restarts_and_polls_without_respawn(self) -> None:
        """A running local Job survives Recovery restart through its handle journal."""

        contract = self._contract()
        self._install_policy(contract)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)
        task, action_id = self._open_and_queue_exec(
            contract,
            label="HTTP exec Recovery running-restart fixture task",
            task_key="mcp-http-exec-running-restart-task-key",
            action_key="mcp-http-exec-running-restart-action-key",
        )

        first_pid = self.runtime_process.pid
        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as first_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        self.assertEqual(json.loads(first_output.getvalue())["completed_action_ids"], [f"{action_id}:running"])
        accepted = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(accepted["delivery_state"], "accepted")
        self.assertEqual([item["receipt_state"] for item in accepted["receipts"]], ["accepted"])

        # Kill the Recovery process after the node has durably received the
        # running handle, then start a fresh process on the same data root.
        self._crash_runtime_fixture()
        self._restart_runtime_fixture()
        self.assertNotEqual(self.runtime_process.pid, first_pid)

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as second_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        second_receipt = json.loads(second_output.getvalue())
        self.assertEqual(second_receipt["received_action_ids"], [])
        self.assertEqual(second_receipt["resumed"]["completed"], [action_id])

        final = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(final["task_id"], task["task_id"])
        self.assertEqual(final["delivery_state"], "settled")
        self.assertEqual([item["receipt_state"] for item in final["receipts"]], ["accepted", "completed"])
        observation = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual(len(observation["launches"]), 2)
        self.assertEqual(
            [item["operation"] for item in observation["mcp_calls"]],
            ["bind", "exec_run", "bind", "poll"],
        )
        self.assertEqual(
            [item["operation"] for item in observation["recovery_calls"]],
            ["exec_run", "exec_poll"],
        )

    def test_oauth_exec_terminal_result_lost_on_recovery_crash_requires_reconcile(self) -> None:
        """Terminal local evidence lost before bridge ACK remains unknown after restart."""

        contract = self._contract()
        self._install_policy(contract)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)
        task, action_id = self._open_and_queue_exec(
            contract,
            label="HTTP exec Recovery terminal-crash fixture task",
            task_key="mcp-http-exec-terminal-crash-task-key",
            action_key="mcp-http-exec-terminal-crash-action-key",
        )

        crashed_pid = self.runtime_process.pid
        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as first_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        first_receipt = json.loads(first_output.getvalue())
        self.assertEqual(first_receipt["received_action_ids"], [action_id])
        self.assertEqual(first_receipt["unknown_action_ids"], [action_id])
        self.assertIsNotNone(self.runtime_process.poll(), "fixture must have crashed")
        unknown = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(unknown["task_id"], task["task_id"])
        self.assertEqual(unknown["delivery_state"], "reconcile_required")
        self.assertEqual([item["receipt_state"] for item in unknown["receipts"]], ["unknown"])
        observation_after_crash = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual(observation_after_crash["crash"]["stage"], "after_terminal_result")

        self._restart_runtime_fixture(crash_after_exec_run=False)
        self.assertNotEqual(self.runtime_process.pid, crashed_pid)
        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as second_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        second_receipt = json.loads(second_output.getvalue())
        self.assertEqual(second_receipt["received_action_ids"], [])
        self.assertEqual(second_receipt["submitted_receipts"], 0)
        final = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(final["delivery_state"], "reconcile_required")
        self.assertEqual([item["receipt_state"] for item in final["receipts"]], ["unknown"])
        observation = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual(len(observation["launches"]), 2)
        self.assertEqual([item["operation"] for item in observation["mcp_calls"]], ["bind", "exec_run"])
        self.assertEqual([item["operation"] for item in observation["recovery_calls"]], ["exec_run"])

    def test_oauth_exec_replays_lost_terminal_receipt_ack_without_relay(self) -> None:
        """A terminal receipt committed before ACK loss is replayed unchanged."""

        contract = self._contract()
        self._install_policy(contract)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)
        _task, action_id = self._open_and_queue_exec(
            contract,
            label="HTTP exec terminal ACK-loss fixture task",
            task_key="mcp-http-exec-terminal-ack-task-key",
            action_key="mcp-http-exec-terminal-ack-action-key",
        )

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as first_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        self.assertEqual(json.loads(first_output.getvalue())["completed_action_ids"], [f"{action_id}:running"])

        original_request = __import__("control_plane.node_agent", fromlist=["_request"])._request
        dropped = {"value": False}

        def lose_terminal_receipt_ack(
            url: str,
            path: str,
            payload: dict[str, Any],
            authorization: str | None = None,
        ) -> dict[str, Any]:
            response = original_request(url, path, payload, authorization)
            if (
                path.endswith("/receipts")
                and payload.get("receipt_state") == "completed"
                and not dropped["value"]
            ):
                dropped["value"] = True
                raise OSError("terminal receipt acknowledgement lost")
            return response

        with mock.patch("control_plane.node_agent._request", side_effect=lose_terminal_receipt_ack), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(OSError, "terminal receipt acknowledgement lost"):
                poll_exec_once(self.args())

        settled = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(settled["delivery_state"], "settled")
        self.assertEqual([item["receipt_state"] for item in settled["receipts"]], ["accepted", "completed"])
        journal_path = self.config_path.with_name(f"{self.config_path.name}.exec-journal.json")
        journal = _read_exec_journal(journal_path)
        entry = journal["entries"][_exec_journal_key(action_id, settled["attempts"][0]["attempt_id"])]
        self.assertEqual(entry["state"], "completed")
        self.assertFalse(entry["receipt"]["receipt_submitted"])

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as retry_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        retry_receipt = json.loads(retry_output.getvalue())
        self.assertEqual(retry_receipt["received_action_ids"], [])
        self.assertEqual(retry_receipt["submitted_receipts"], 1)
        replayed = _read_exec_journal(journal_path)["entries"][_exec_journal_key(action_id, settled["attempts"][0]["attempt_id"])]
        self.assertTrue(replayed["receipt"]["receipt_submitted"])

        observation = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual([item["operation"] for item in observation["mcp_calls"]], ["bind", "exec_run", "bind", "poll"])
        self.assertEqual([item["operation"] for item in observation["recovery_calls"]], ["exec_run", "exec_poll"])

    def test_oauth_exec_terminal_receipt_ack_loss_survives_recovery_restart_without_relay(self) -> None:
        """A committed terminal receipt remains replayable after Recovery restarts."""

        contract = self._contract()
        self._install_policy(contract)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)
        task, action_id = self._open_and_queue_exec(
            contract,
            label="HTTP exec terminal ACK-loss Recovery restart task",
            task_key="mcp-http-exec-terminal-restart-task-key",
            action_key="mcp-http-exec-terminal-restart-action-key",
        )

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as first_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        self.assertEqual(json.loads(first_output.getvalue())["completed_action_ids"], [f"{action_id}:running"])

        original_request = __import__("control_plane.node_agent", fromlist=["_request"])._request
        dropped = {"value": False}
        crashed_pid = self.runtime_process.pid

        def lose_terminal_ack_after_recovery_restart(
            url: str,
            path: str,
            payload: dict[str, Any],
            authorization: str | None = None,
        ) -> dict[str, Any]:
            response = original_request(url, path, payload, authorization)
            if (
                path.endswith("/receipts")
                and payload.get("receipt_state") == "completed"
                and not dropped["value"]
            ):
                dropped["value"] = True
                # Central has committed the terminal receipt.  Kill the
                # Recovery process before the node sees the HTTP ACK.
                self._crash_runtime_fixture()
                raise OSError("terminal receipt acknowledgement lost across Recovery restart")
            return response

        with mock.patch("control_plane.node_agent._request", side_effect=lose_terminal_ack_after_recovery_restart), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(OSError, "terminal receipt acknowledgement lost across Recovery restart"):
                poll_exec_once(self.args())

        settled = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(settled["task_id"], task["task_id"])
        self.assertEqual(settled["delivery_state"], "settled")
        self.assertEqual([item["receipt_state"] for item in settled["receipts"]], ["accepted", "completed"])
        journal_path = self.config_path.with_name(f"{self.config_path.name}.exec-journal.json")
        entry = _read_exec_journal(journal_path)["entries"][_exec_journal_key(action_id, settled["attempts"][0]["attempt_id"])]
        self.assertEqual(entry["state"], "completed")
        self.assertFalse(entry["receipt"]["receipt_submitted"])
        self.assertIsNotNone(crashed_pid)

        self._restart_runtime_fixture()
        self.assertNotEqual(self.runtime_process.pid, crashed_pid)
        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as retry_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        retry = json.loads(retry_output.getvalue())
        self.assertEqual(retry["received_action_ids"], [])
        self.assertEqual(retry["submitted_receipts"], 1)
        replayed = _read_exec_journal(journal_path)["entries"][_exec_journal_key(action_id, settled["attempts"][0]["attempt_id"])]
        self.assertTrue(replayed["receipt"]["receipt_submitted"])
        observation = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual(len(observation["launches"]), 2)
        self.assertEqual([item["operation"] for item in observation["mcp_calls"]], ["bind", "exec_run", "bind", "poll"])
        self.assertEqual([item["operation"] for item in observation["recovery_calls"]], ["exec_run", "exec_poll"])

    def test_oauth_exec_stop_pending_survives_recovery_restart(self) -> None:
        """A stop accepted locally remains pending until the restarted process polls it."""

        contract = self._contract()
        self._install_policy(contract)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)
        task, action_id = self._open_and_queue_exec(
            contract,
            label="HTTP exec stop-pending Recovery restart task",
            task_key="mcp-http-exec-stop-restart-task-key",
            action_key="mcp-http-exec-stop-restart-action-key",
        )

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as first_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        self.assertEqual(json.loads(first_output.getvalue())["completed_action_ids"], [f"{action_id}:running"])

        stop_status, stop = self._mcp_post({
            "jsonrpc": "2.0", "id": "mcp-http-exec-stop-restart-request", "method": "tools/call",
            "params": {"name": "command_control", "arguments": {
                "operation": "exec_stop", "action_id": action_id,
            }},
        })
        self.assertEqual(stop_status, 200)
        self.assertEqual(stop["result"]["structuredContent"]["stop_state"], "pending")

        crashed_pid = self.runtime_process.pid
        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as stop_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        first_stop = json.loads(stop_output.getvalue())
        self.assertEqual(first_stop["acknowledged_stop_action_ids"], [])
        self.assertEqual(first_stop["pending_stop_action_ids"], [action_id])
        self.assertIsNotNone(self.runtime_process)
        self.assertIsNotNone(self.runtime_process.poll(), "Recovery must crash after accepting exec_stop")

        pending = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(pending["delivery_state"], "accepted")
        self.assertEqual([item["receipt_state"] for item in pending["receipts"]], ["accepted"])
        observation_after_crash = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual(observation_after_crash["crash"]["stage"], "after_exec_stop")

        self._restart_runtime_fixture()
        self.assertNotEqual(self.runtime_process.pid, crashed_pid)
        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as retry_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        retry = json.loads(retry_output.getvalue())
        self.assertEqual(retry["received_action_ids"], [])
        self.assertEqual(retry["acknowledged_stop_action_ids"], [action_id])
        self.assertEqual(retry["pending_stop_action_ids"], [])

        settled = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(settled["task_id"], task["task_id"])
        self.assertEqual(settled["delivery_state"], "settled")
        self.assertEqual([item["receipt_state"] for item in settled["receipts"]], ["accepted", "stopped"])
        stopped_payload = json.loads(settled["receipts"][-1]["payload_json"])
        self.assertEqual(stopped_payload["status"], "stopped")
        self.assertEqual(stopped_payload["exit_code"], 143)
        observation = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual(len(observation["launches"]), 2)
        self.assertEqual(
            [item["operation"] for item in observation["mcp_calls"]],
            ["bind", "exec_run", "bind", "poll", "bind", "kill", "bind", "poll"],
        )
        self.assertEqual(
            [item["operation"] for item in observation["recovery_calls"]],
            ["exec_run", "exec_poll", "exec_stop", "exec_poll"],
        )

    def test_oauth_exec_stop_runs_through_real_recovery_job(self) -> None:
        """A stop remains pending until the real Recovery bridge proves quiescence."""

        contract = self._contract()
        self._install_policy(contract)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)

        opened_status, opened = self._mcp_post({
            "jsonrpc": "2.0", "id": "mcp-http-exec-stop-task-open", "method": "tools/call",
            "params": {"name": "workspace_context", "arguments": {
                "operation": "task_open", "binding_id": self.binding["binding_id"],
                "label": "HTTP exec stop fixture task", "idempotency_key": "mcp-http-exec-stop-task-key",
            }},
        })
        self.assertEqual(opened_status, 200)
        task = opened["result"]["structuredContent"]["task"]
        claimed_status, claimed = self._mcp_post({
            "jsonrpc": "2.0", "id": "mcp-http-exec-stop-writer-claim", "method": "tools/call",
            "params": {"name": "task_control", "arguments": {
                "operation": "writer_claim", "task_id": task["task_id"],
            }},
        })
        self.assertEqual(claimed_status, 200)
        self.assertEqual(claimed["result"]["structuredContent"]["writer_lease"]["state"], "held")
        queued_status, queued = self._mcp_post({
            "jsonrpc": "2.0", "id": "mcp-http-exec-stop-queue", "method": "tools/call",
            "params": {"name": "exec_command", "arguments": {
                "operation": "exec_run", "binding_id": self.binding["binding_id"],
                "task_id": task["task_id"], "argv": ["python3", "-c", "print('stop-me')"],
                "cwd": "", "timeout_ms": 60_000, "max_output_bytes": 32_768,
                "idempotency_key": "mcp-http-exec-stop-action-key", "expected_facade_contract": contract,
            }},
        })
        self.assertEqual(queued_status, 200)
        action_id = queued["result"]["structuredContent"]["action_id"]

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as first_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        self.assertEqual(json.loads(first_output.getvalue())["completed_action_ids"], [f"{action_id}:running"])

        stop_status, stop = self._mcp_post({
            "jsonrpc": "2.0", "id": "mcp-http-exec-stop-request", "method": "tools/call",
            "params": {"name": "command_control", "arguments": {
                "operation": "exec_stop", "action_id": action_id,
            }},
        })
        self.assertEqual(stop_status, 200)
        self.assertEqual(stop["result"]["structuredContent"]["stop_state"], "pending")

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as second_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        second_receipt = json.loads(second_output.getvalue())
        self.assertEqual(second_receipt["received_action_ids"], [])
        self.assertEqual(
            second_receipt["acknowledged_stop_action_ids"],
            [action_id],
            msg=f"stop was not acknowledged: {second_receipt}; action={self.store.action_observation(owner_id=self.owner_id, action_id=action_id)}; journal={self.config_path.with_name(self.config_path.name + '.exec-journal.json').read_text(encoding='utf-8')}; observation={self.runtime_observation_file.read_text(encoding='utf-8')}",
        )

        settled = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(settled["delivery_state"], "settled")
        self.assertEqual([item["receipt_state"] for item in settled["receipts"]], ["accepted", "stopped"])
        stopped_payload = json.loads(settled["receipts"][-1]["payload_json"])
        self.assertEqual(stopped_payload["status"], "stopped")
        self.assertEqual(stopped_payload["exit_code"], 143)

        observation = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual(
            [item["operation"] for item in observation["mcp_calls"]],
            ["bind", "exec_run", "bind", "poll", "bind", "kill"],
        )
        self.assertEqual(
            [item["operation"] for item in observation["recovery_calls"]],
            ["exec_run", "exec_poll", "exec_stop"],
        )
        final_status, final = self._mcp_post({
            "jsonrpc": "2.0", "id": "mcp-http-exec-stop-confirmed", "method": "tools/call",
            "params": {"name": "command_control", "arguments": {
                "operation": "exec_stop", "action_id": action_id,
            }},
        })
        self.assertEqual(final_status, 200)
        self.assertEqual(final["result"]["structuredContent"]["stop_state"], "stopped_or_finished")

    def test_oauth_exec_writer_lease_survives_real_job_until_terminal_handoff(self) -> None:
        """A real local Job keeps the binding writer lease until terminal receipt."""

        contract = self._contract()
        self._install_policy(contract)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)
        task_a, action_id = self._open_and_queue_exec(
            contract,
            label="HTTP exec writer handoff task A",
            task_key="mcp-http-exec-writer-job-task-a-key",
            action_key="mcp-http-exec-writer-job-action-a-key",
        )

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as first_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        self.assertEqual(json.loads(first_output.getvalue())["completed_action_ids"], [f"{action_id}:running"])

        opened_status, opened = self._mcp_post({
            "jsonrpc": "2.0", "id": "mcp-http-exec-writer-job-task-b-open", "method": "tools/call",
            "params": {"name": "workspace_context", "arguments": {
                "operation": "task_open", "binding_id": self.binding["binding_id"],
                "label": "HTTP exec writer handoff task B",
                "idempotency_key": "mcp-http-exec-writer-job-task-b-key",
            }},
        })
        self.assertEqual(opened_status, 200)
        task_b = opened["result"]["structuredContent"]["task"]

        claim_status, claim = self._mcp_post({
            "jsonrpc": "2.0", "id": "mcp-http-exec-writer-job-task-b-claim", "method": "tools/call",
            "params": {"name": "task_control", "arguments": {
                "operation": "writer_claim", "task_id": task_b["task_id"],
            }},
        })
        self.assertEqual(claim_status, 200)
        self.assertEqual(claim["error"]["data"]["code"], "CONFLICT")

        release_while_running_status, release_while_running = self._mcp_post({
            "jsonrpc": "2.0", "id": "mcp-http-exec-writer-job-task-a-release-running", "method": "tools/call",
            "params": {"name": "task_control", "arguments": {
                "operation": "writer_release", "task_id": task_a["task_id"], "reason": "handoff-too-early",
            }},
        })
        self.assertEqual(release_while_running_status, 200)
        self.assertEqual(release_while_running["error"]["data"]["code"], "CONFLICT")

        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as terminal_output:
            self.assertEqual(poll_exec_once(self.args()), 0)
        terminal = json.loads(terminal_output.getvalue())
        self.assertEqual(terminal["resumed"]["completed"], [action_id])
        settled = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual(settled["delivery_state"], "settled")
        self.assertEqual([item["receipt_state"] for item in settled["receipts"]], ["accepted", "completed"])

        release_status, released = self._mcp_post({
            "jsonrpc": "2.0", "id": "mcp-http-exec-writer-job-task-a-release-terminal", "method": "tools/call",
            "params": {"name": "task_control", "arguments": {
                "operation": "writer_release", "task_id": task_a["task_id"], "reason": "handoff-terminal",
            }},
        })
        self.assertEqual(release_status, 200)
        self.assertEqual(released["result"]["structuredContent"]["writer_lease"]["state"], "released")

        claim_b_status, claimed_b = self._mcp_post({
            "jsonrpc": "2.0", "id": "mcp-http-exec-writer-job-task-b-claim-after-terminal", "method": "tools/call",
            "params": {"name": "task_control", "arguments": {
                "operation": "writer_claim", "task_id": task_b["task_id"],
            }},
        })
        self.assertEqual(claim_b_status, 200)
        lease_b = claimed_b["result"]["structuredContent"]["writer_lease"]
        self.assertEqual(lease_b["state"], "held")
        self.assertEqual(lease_b["lease_generation"], 1)
        observation = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual([item["operation"] for item in observation["mcp_calls"]], ["bind", "exec_run", "bind", "poll"])
        self.assertEqual([item["operation"] for item in observation["recovery_calls"]], ["exec_run", "exec_poll"])


if __name__ == "__main__":
    unittest.main()
