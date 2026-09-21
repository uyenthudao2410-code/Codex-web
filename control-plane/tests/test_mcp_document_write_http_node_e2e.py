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
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest import mock

from control_plane import node_agent as node_agent_module
from control_plane.http_api import ControlPlaneHttpServer
from control_plane.mcp_facade import _completed_document_write_relay
from control_plane.mcp_oauth import (
    OAuthAccessIdentity,
    OAuthAuthenticationError,
    OAuthClientCredentials,
    OAuthIntrospectionConfiguration,
)
from control_plane.node_agent import (
    _install_approved_patch_policy_values,
    _policy_digest,
    _read_document_write_journal,
    heartbeat,
    poll_document_write_once,
)
from control_plane.store import ControlPlaneStore


ISSUER = "https://identity.example.test/tenant-document-write-http-node"
RESOURCE = "https://mcp.example.test"
INTROSPECTION_URL = f"{ISSUER}/introspect"
READ_SCOPE = "control-plane.inventory"
WRITE_SCOPE = "control-plane.patch"


class _StaticVerifier:
    def __init__(self, identity: OAuthAccessIdentity) -> None:
        self.identity = identity

    def authenticate(self, _token: str, *, required_scopes: object = None) -> OAuthAccessIdentity:
        if required_scopes is not None and not set(required_scopes) <= set(self.identity.scopes):
            raise OAuthAuthenticationError("OAuth access token is invalid.")
        return self.identity


class McpDocumentWriteHttpNodeE2ETests(unittest.TestCase):
    """Exercise central document admission through a real Recovery process."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mcp-document-write-http-node-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.repo_root = Path(__file__).resolve().parents[2]
        self.app_data_root = self.directory / "appdata"
        self.app_data_root.mkdir()
        self.data_root = self.app_data_root / "web-mcp-assistant"
        self.data_root.mkdir(parents=True)
        self.workspace_root = self.directory / "workspace"
        (self.workspace_root / "docs").mkdir(parents=True)
        (self.workspace_root / "input.md").write_text("# input\n", encoding="utf-8")

        self.store = ControlPlaneStore(self.directory / "control.sqlite3")
        self.owner_id = "owner_default"
        self.identity = OAuthAccessIdentity(
            issuer=ISSUER,
            subject="provider-subject-document-write-http-node",
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
            standing_write_enabled=True,
            exec_enabled=False,
        )
        self.verifier = _StaticVerifier(self.identity)
        operator_token = "o" * 40
        self.main_server = ControlPlaneHttpServer(
            ("127.0.0.1", 0), self.store, operator_token, mcp_enabled=False,
            mcp_oauth=self.configuration, mcp_oauth_verifier=self.verifier,
        )
        self.mcp_server = ControlPlaneHttpServer(
            ("127.0.0.1", 0), self.store, operator_token, mcp_enabled=True,
            mcp_ingress_only=True, mcp_oauth=self.configuration,
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
            owner_id=self.owner_id, issuer=ISSUER, subject=self.identity.subject
        )
        self.node = self.store.enroll_node(
            owner_id=self.owner_id,
            device_id="b3b8a0bb-4d2d-4f12-8c2a-9c7c0d8e1f02",
            endpoint_id="endpoint-http-document-write-e2e-001",
            display_name="HTTP document write fixture node",
        )
        self.endpoint_id = "endpoint-http-document-write-e2e-001"
        self.workspace_id = "workspace-http-document-write-e2e-001"
        self.workspace_generation = "generation-http-document-write-e2e-001"
        self.store.register_node_workspace(
            device_id=self.node["device_id"], workspace_id=self.workspace_id,
            workspace_generation=self.workspace_generation,
            display_name="HTTP document write fixture workspace",
            capabilities={"read": True, "write": True, "exec": False},
        )
        self.binding = self.store.create_binding(
            owner_id=self.owner_id, device_id=self.node["device_id"],
            workspace_id=self.workspace_id, workspace_generation=self.workspace_generation,
            display_name="HTTP document write fixture workspace",
        )
        self.config_path = self.data_root / "control-plane-node.json"
        self.registry_path = self.data_root / "control-plane-workspaces.json"
        self.config = {
            "server_url": self.main_url,
            "device_id": self.node["device_id"],
            "endpoint_id": self.endpoint_id,
            "node_secret": self.node["node_secret"],
        }
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        self.registry_path.write_text(json.dumps({
            "schema_version": 1,
            "entries": [{
                "workspace_id": self.workspace_id,
                "workspace_generation": self.workspace_generation,
                "canonical_path": str(self.workspace_root.resolve()),
                "display_name": "HTTP document write fixture workspace",
                "capabilities": {"read": True, "write": True, "exec": False},
                "created_at_ms": 1_700_000_000_000,
            }],
        }), encoding="utf-8")

        self.runtime_fixture_file = self.directory / "recovery-document-write-fixture.json"
        self.runtime_ready_file = self.directory / "recovery-document-write-ready.json"
        self.runtime_observation_file = self.directory / "recovery-document-write-observation.json"
        self.runtime_fixture_file.write_text(json.dumps({
            "app_data": str(self.app_data_root),
            "app_root": str(self.repo_root),
            "workspace": str(self.workspace_root.resolve()),
            "device_id": self.node["device_id"],
            "activation_epoch_id": "activation-http-document-write-e2e-001",
            "mcp_token": "mcp-runtime-document-write-fixture-token-0001",
            "ready_file": str(self.runtime_ready_file),
            "observation_file": str(self.runtime_observation_file),
            "process_instance_id": "mcp-process-http-document-write-e2e-001",
            "server_instance_id": "mcp-server-http-document-write-e2e-001",
            "tool_contract_sha256": "a" * 64,
            "crash_after_document_result": False,
        }), encoding="utf-8")
        self.runtime_process: subprocess.Popen[str] | None = None
        self._start_runtime_fixture()
        self.addCleanup(self._stop_runtime_fixture)

    def args(self) -> SimpleNamespace:
        return SimpleNamespace(
            config=str(self.config_path), workspace_registry=str(self.registry_path),
            data_root=str(self.data_root), project_root=str(self.repo_root), node="node",
            runtime_mode="development", timeout_seconds=20, replace=True,
            runtime_instance_id="mcp-process-http-document-write-e2e-001",
            mcp_server_instance_id="mcp-server-http-document-write-e2e-001",
            activation_epoch="activation-http-document-write-e2e-001",
            contract_version="sha256:" + "a" * 64, readiness="ready",
        )

    def _start_runtime_fixture(self) -> None:
        helper = self.repo_root / "tests" / "recovery-exec-process-fixture.cjs"
        self.runtime_ready_file.unlink(missing_ok=True)
        environment = dict(os.environ)
        environment["APPDATA"] = str(self.app_data_root)
        self.runtime_process = subprocess.Popen(
            ["node", str(helper), "--fixture", str(self.runtime_fixture_file)],
            cwd=self.repo_root, env=environment, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE, text=True,
        )
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if self.runtime_ready_file.is_file():
                return
            if self.runtime_process.poll() is not None:
                stderr = self.runtime_process.stderr.read() if self.runtime_process.stderr else ""
                self.fail(f"Recovery document fixture exited early: {stderr}")
            time.sleep(0.05)
        stderr = self.runtime_process.stderr.read() if self.runtime_process.stderr else ""
        self.fail(f"Recovery document fixture did not become ready: {stderr}")

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

    def _stop_servers(self) -> None:
        for server in (self.main_server, self.mcp_server):
            server.shutdown()
            server.server_close()
        for thread in self.threads:
            thread.join(timeout=2)

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
            "mcp_ready": True, "identity_current": True,
            "mcp_process_instance_id": "mcp-process-http-document-write-e2e-001",
            "mcp_server_instance_id": "mcp-server-http-document-write-e2e-001",
            "activation_epoch_id": "activation-http-document-write-e2e-001",
            "current_activation_epoch_id": "activation-http-document-write-e2e-001",
            "tool_contract_sha256": "a" * 64,
        }

    @staticmethod
    def _response(request: Request) -> tuple[int, dict[str, Any]]:
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            try:
                return error.code, json.loads(error.read())
            finally:
                error.close()

    def _mcp_post(self, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        return self._response(Request(
            f"{self.mcp_url}/mcp", data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": "Bearer opaque-source-fixture-token",
                "Content-Type": "application/json",
            }, method="POST",
        ))

    def _contract(self) -> dict[str, Any]:
        return {key: self.mcp_server.mcp_facade.contract[key] for key in ("schema_version", "profile", "sha256")}

    def _install_policy(self, contract: dict[str, Any]) -> dict[str, Any]:
        return _install_approved_patch_policy_values(
            self.args(), config_path=self.config_path, config=self.config,
            owner_id=self.owner_id, workspace_id=self.workspace_id,
            workspace_generation=self.workspace_generation, expires_at_ms=None,
            facade_contract=contract,
            allowed_relative_paths=["docs/report.md", "docs/report.docx", "input.md"],
            max_patch_bytes=4096, max_file_bytes=4096,
        )

    def _open_task(self, label: str, key: str) -> dict[str, Any]:
        status, response = self._mcp_post({
            "jsonrpc": "2.0", "id": f"{key}-open", "method": "tools/call",
            "params": {"name": "workspace_context", "arguments": {
                "operation": "task_open", "binding_id": self.binding["binding_id"],
                "label": label, "idempotency_key": key,
            }},
        })
        self.assertEqual(status, 200)
        task = response["result"]["structuredContent"]["task"]
        status, response = self._mcp_post({
            "jsonrpc": "2.0", "id": f"{key}-claim", "method": "tools/call",
            "params": {"name": "task_control", "arguments": {
                "operation": "writer_claim", "task_id": task["task_id"],
            }},
        })
        self.assertEqual(status, 200)
        self.assertEqual(response["result"]["structuredContent"]["writer_lease"]["state"], "held")
        return task

    def _queue_document(self, task: dict[str, Any], contract: dict[str, Any], *, operation: str, key: str) -> str:
        arguments: dict[str, Any] = {
            "operation": operation, "binding_id": self.binding["binding_id"],
            "task_id": task["task_id"],
            "target": "docs/report.md" if operation == "doc_create" else "docs/report.docx",
            "overwrite": False,
            "idempotency_key": key, "expected_facade_contract": contract,
        }
        if operation == "doc_create":
            arguments["title"] = "HTTP document fixture"
            arguments["content"] = "# HTTP document\n\nCreated by the node.\n"
        else:
            arguments["source"] = "input.md"
        status, response = self._mcp_post({
            "jsonrpc": "2.0", "id": f"{key}-queue", "method": "tools/call",
            "params": {"name": "document_workflow", "arguments": arguments},
        })
        self.assertEqual(status, 200)
        self.assertIn("result", response, msg=response)
        content = response["result"]["structuredContent"]
        self.assertEqual(content["execution"], "queued_for_local_admission")
        return content["action_id"]

    def _release_task(self, task: dict[str, Any], reason: str) -> None:
        status, response = self._mcp_post({
            "jsonrpc": "2.0", "id": f"{task['task_id']}-release", "method": "tools/call",
            "params": {"name": "task_control", "arguments": {
                "operation": "writer_release", "task_id": task["task_id"], "reason": reason,
            }},
        })
        self.assertEqual(status, 200)
        self.assertEqual(response["result"]["structuredContent"]["writer_lease"]["state"], "released")

    def _poll(self) -> dict[str, Any]:
        with mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch.dict(os.environ, {"APPDATA": str(self.app_data_root)}, clear=False), \
             redirect_stdout(io.StringIO()) as output:
            self.assertEqual(poll_document_write_once(self.args()), 0)
        return json.loads(output.getvalue())

    def _status(self, action_id: str) -> dict[str, Any]:
        status, response = self._mcp_post({
            "jsonrpc": "2.0", "id": f"{action_id}-status", "method": "tools/call",
            "params": {"name": "document_workflow", "arguments": {
                "operation": "doc_status", "action_id": action_id,
            }},
        })
        self.assertEqual(status, 200)
        return response["result"]["structuredContent"]

    def test_create_and_convert_write_files_through_real_recovery_process(self) -> None:
        contract = self._contract()
        policy = self._install_policy(contract)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)

        create_task = self._open_task("HTTP document create", "document-http-create-task-001")
        create_action = self._queue_document(
            create_task, contract, operation="doc_create", key="document-http-create-action-001"
        )
        create_poll = self._poll()
        self.assertEqual(create_poll["completed_action_ids"], [create_action])
        create_status = self._status(create_action)
        self.assertEqual(
            create_status["execution"], "completed_document_write_relay",
            msg=f"status={create_status}; relay={_completed_document_write_relay(self.store.action_observation(owner_id=self.owner_id, action_id=create_action), contract)}; contract={contract}; action={self.store.action_observation(owner_id=self.owner_id, action_id=create_action)}; journal={self.config_path.with_name(self.config_path.name + '.document-write-bridge-journal.json').read_text(encoding='utf-8')}",
        )
        self.assertEqual(create_status["document"]["target"], "docs/report.md")
        self.assertEqual(
            (self.workspace_root / "docs/report.md").read_text(encoding="utf-8"),
            "# HTTP document\n\nCreated by the node.\n",
        )
        self._release_task(create_task, "document-create-complete")

        convert_task = self._open_task("HTTP document convert", "document-http-convert-task-001")
        convert_action = self._queue_document(
            convert_task, contract, operation="doc_convert", key="document-http-convert-action-001"
        )
        convert_poll = self._poll()
        self.assertEqual(convert_poll["completed_action_ids"], [convert_action])
        convert_status = self._status(convert_action)
        self.assertEqual(convert_status["execution"], "completed_document_write_relay")
        self.assertEqual(convert_status["document"]["source"], "input.md")
        self.assertEqual(convert_status["document"]["target"], "docs/report.docx")
        self.assertTrue((self.workspace_root / "docs/report.docx").is_file())

        observation = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual(
            [item["operation"] for item in observation["mcp_calls"]],
            ["bind", "create", "bind", "convert"],
        )
        self.assertEqual(
            [item["action"] for item in observation["recovery_calls"]],
            ["runtime.control_plane_document_write", "runtime.control_plane_document_write"],
        )
        self.assertTrue(all(item["has_attestation"] for item in observation["mcp_calls"]))
        rendered = json.dumps(create_status) + json.dumps(convert_status)
        self.assertNotIn(self.config["node_secret"], rendered)
        self.assertNotIn(str(self.workspace_root), rendered)
        self.assertNotIn(_policy_digest(policy), rendered)

        journal = _read_document_write_journal(
            self.config_path.with_name(f"{self.config_path.name}.document-write-bridge-journal.json")
        )
        self.assertTrue(all(entry["state"] == "completed" for entry in journal["entries"].values()))
        self.assertTrue(all(entry["receipt"]["receipt_submitted"] for entry in journal["entries"].values()))

    def test_recovery_crash_after_document_effect_is_unknown_without_redelivery(self) -> None:
        contract = self._contract()
        self._install_policy(contract)
        fixture = json.loads(self.runtime_fixture_file.read_text(encoding="utf-8"))
        fixture["crash_after_document_result"] = True
        self.runtime_fixture_file.write_text(json.dumps(fixture), encoding="utf-8")
        # The fixture reads its launch flags once. Restart it so the crash is
        # injected after the local document effect but before the node receives
        # the IPC response/receipt.
        self._stop_runtime_fixture()
        self._start_runtime_fixture()
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)
        task = self._open_task("HTTP document crash", "document-http-crash-task-001")
        action_id = self._queue_document(
            task, contract, operation="doc_create", key="document-http-crash-action-001"
        )
        first = self._poll()
        self.assertEqual(
            first["unknown_action_ids"], [action_id],
            msg=f"poll={first}; action={self.store.action_observation(owner_id=self.owner_id, action_id=action_id)}; observation={self.runtime_observation_file.read_text(encoding='utf-8')}",
        )
        status = self._status(action_id)
        self.assertEqual(status["execution"], "local_document_effect_unknown_reconcile_required")
        self.assertTrue(status["reconciliation_required"])
        self.assertTrue((self.workspace_root / "docs/report.md").is_file())
        observation = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual(observation["document_runs"], 1)

    def test_lost_receipt_ack_replays_completed_document_without_redelivery(self) -> None:
        contract = self._contract()
        self._install_policy(contract)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(heartbeat(self.args()), 0)
        task = self._open_task("HTTP document lost ACK", "document-http-lost-ack-task-001")
        action_id = self._queue_document(
            task, contract, operation="doc_create", key="document-http-lost-ack-action-001"
        )

        original_submit = node_agent_module._submit_receipt
        submit_calls = 0

        def submit_then_drop_ack(config: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
            nonlocal submit_calls
            response = original_submit(config, entry)
            submit_calls += 1
            if submit_calls == 1:
                raise RuntimeError("CONTROL_PLANE_TRANSPORT_UNAVAILABLE_AFTER_COMMIT")
            return response

        # The central receipt is committed, but the node loses the transport
        # acknowledgement before its journal can mark the receipt submitted.
        with mock.patch("control_plane.node_agent._submit_receipt", side_effect=submit_then_drop_ack):
            with self.assertRaises(RuntimeError):
                self._poll()

        action = self.store.action_observation(owner_id=self.owner_id, action_id=action_id)
        self.assertEqual([receipt["receipt_state"] for receipt in action["receipts"]], ["completed"])
        second = self._poll()
        self.assertEqual(second["received_action_ids"], [])
        self.assertEqual(second["submitted_receipts"], 1)
        status = self._status(action_id)
        self.assertEqual(status["execution"], "completed_document_write_relay")
        self.assertTrue((self.workspace_root / "docs/report.md").is_file())
        observation = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual(observation["document_runs"], 1)
        self.assertEqual([item["operation"] for item in observation["mcp_calls"]], ["bind", "create"])
        self.assertEqual([item["action"] for item in observation["recovery_calls"]], ["runtime.control_plane_document_write"])
        self.assertEqual([item["operation"] for item in observation["mcp_calls"]], ["bind", "create"])
        self.assertEqual([item["action"] for item in observation["recovery_calls"]], ["runtime.control_plane_document_write"])
        # A second poll sees the terminal UNKNOWN receipt and cannot dispatch
        # the central action or call the local document tool again.
        second = self._poll()
        self.assertEqual(second["received_action_ids"], [])
        observation = json.loads(self.runtime_observation_file.read_text(encoding="utf-8"))
        self.assertEqual(observation["document_runs"], 1)


if __name__ == "__main__":
    unittest.main()
