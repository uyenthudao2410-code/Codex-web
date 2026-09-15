from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest import mock

from control_plane.http_api import ControlPlaneHttpServer, _package_source_sha256
from control_plane.mcp_facade import _central_lifecycle_state
from control_plane.store import ControlPlaneStore


class _CommitFailingConnection:
    """Inject a post-write COMMIT failure while preserving SQLite rollback semantics."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def execute(self, statement: str, parameters: object = ()) -> sqlite3.Cursor:
        if statement.strip().upper() == "COMMIT":
            self._connection.execute("ROLLBACK")
            raise sqlite3.OperationalError("simulated durable commit failure at /private/control-plane.sqlite3")
        return self._connection.execute(statement, parameters)

    def __getattr__(self, name: str) -> object:
        return getattr(self._connection, name)


class ControlPlaneHttpApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.operator_token = "o" * 40
        self.server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            ControlPlaneStore(Path(self.tempdir.name) / "control.sqlite3"),
            self.operator_token,
            "a" * 40,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tempdir.cleanup()

    def _post(self, path: str, payload: dict, authorization: str | None = None) -> tuple[int, dict]:
        headers = {"Content-Type": "application/json"}
        if authorization:
            headers["Authorization"] = authorization
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=2) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            try:
                return error.code, json.loads(error.read())
            finally:
                error.close()

    def _get(self, path: str, authorization: str | None = None) -> tuple[int, dict]:
        headers = {"Authorization": authorization} if authorization else {}
        request = Request(f"{self.base_url}{path}", headers=headers, method="GET")
        try:
            with urlopen(request, timeout=2) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            try:
                return error.code, json.loads(error.read())
            finally:
                error.close()

    def test_two_step_enrollment_never_exposes_node_secret_to_operator(self) -> None:
        node_secret = "n" * 40
        credential_hash = hashlib.sha256(
            json.dumps({"node_secret": node_secret}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        status, enrollment = self._post(
            "/v1/enrollment-requests",
            {
                "device_id": "device-http-canary",
                "endpoint_id": "endpoint-http-canary",
                "display_name": "HTTP Canary",
                "credential_hash": credential_hash,
            },
        )
        self.assertEqual(status, 201)
        self.assertNotIn("node_secret", enrollment)

        status, forbidden = self._post(
            f"/v1/enrollment-requests/{enrollment['enrollment_id']}/approve",
            {},
        )
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")

        status, approved = self._post(
            f"/v1/enrollment-requests/{enrollment['enrollment_id']}/approve",
            {},
            f"Bearer {self.operator_token}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(approved["device_id"], "device-http-canary")
        self.assertNotIn("node_secret", approved)

        status, heartbeat = self._post(
            "/v1/nodes/device-http-canary/heartbeat",
            {
                "endpoint_id": "endpoint-http-canary",
                "runtime_instance_id": "mcp-process-http-0001",
                "mcp_server_instance_id": "mcp-server-http-0001",
                "activation_epoch": "epoch-http-0001",
                "contract_version": "sha256:" + "a" * 64,
                "readiness": "unknown",
            },
            f"Node {node_secret}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(heartbeat["readiness"], "unknown")
        self.assertEqual(heartbeat["mcp_server_instance_id"], "mcp-server-http-0001")

    def test_action_observation_route_requires_operator_authority(self) -> None:
        status, forbidden = self._get("/v1/actions/action-does-not-exist")
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")
        status, missing = self._get("/v1/actions/action-does-not-exist", f"Bearer {self.operator_token}")
        self.assertEqual(status, 404)
        self.assertEqual(missing["error"]["code"], "NOT_FOUND")

    def test_health_reports_schema_admission_and_declared_source_without_auth(self) -> None:
        status, health = self._get("/healthz")
        self.assertEqual(status, 200)
        self.assertTrue(health["ok"])
        self.assertEqual(health["sqlite_integrity"], "ok")
        self.assertEqual(health["schema_version"], 7)
        self.assertEqual(health["admission_mode"], "open")
        self.assertEqual(health["declared_source_revision"], "a" * 40)
        self.assertEqual(health["service_instance_id"], self.server.service_instance_id)
        self.assertRegex(health["service_instance_id"], r"^cp_[a-f0-9]{32}$")
        self.assertEqual(health["package_source_sha256"], self.server.package_source_sha256)
        self.assertRegex(health["package_source_sha256"], r"^sha256:[a-f0-9]{64}$")
        self.assertIsNone(health["expected_package_source_sha256"])
        repeat_status, repeated_health = self._get("/healthz")
        self.assertEqual(repeat_status, 200)
        self.assertEqual(repeated_health["service_instance_id"], health["service_instance_id"])
        self.assertEqual(repeated_health["package_source_sha256"], health["package_source_sha256"])

    def test_package_source_fingerprint_binds_names_and_file_bytes_without_paths(self) -> None:
        package_root = Path(self.tempdir.name) / "fingerprint-package"
        package_root.mkdir()
        (package_root / "alpha.py").write_bytes(b"alpha source\n")
        (package_root / "beta.py").write_bytes(b"beta source\n")
        (package_root / "ignored.txt").write_bytes(b"must not be part of the package fingerprint\n")

        expected = hashlib.sha256()
        for name in ("alpha.py", "beta.py"):
            expected.update(name.encode("utf-8"))
            expected.update(b"\0")
            expected.update(hashlib.sha256((package_root / name).read_bytes()).digest())
            expected.update(b"\0")
        self.assertEqual(_package_source_sha256(package_root), f"sha256:{expected.hexdigest()}")

        (package_root / "beta.py").write_bytes(b"beta source changed\n")
        self.assertNotEqual(_package_source_sha256(package_root), f"sha256:{expected.hexdigest()}")

    def test_invalid_declared_source_revision_refuses_server_start(self) -> None:
        with self.assertRaisesRegex(ValueError, "DECLARED_SOURCE_REVISION"):
            ControlPlaneHttpServer(
                ("127.0.0.1", 0),
                ControlPlaneStore(Path(self.tempdir.name) / "invalid-control.sqlite3"),
                self.operator_token,
                "not-a-git-revision",
            )

    def test_sqlite_failure_is_a_typed_content_free_service_unavailable_response(self) -> None:
        with mock.patch.object(
            self.server.store,
            "health",
            side_effect=sqlite3.OperationalError("simulated database or disk is full at /private/path"),
        ):
            status, response = self._get("/healthz")
        self.assertEqual(status, 503)
        self.assertEqual(response, {
            "error": {
                "code": "DURABLE_STORAGE_UNAVAILABLE",
                "message": "durable control-plane storage is unavailable.",
            }
        })

    def test_mcp_fixed_intent_commit_failure_is_content_free_and_durable_noop(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-mcp-commit-failure-0001",
            endpoint_id="endpoint-mcp-commit-failure-0001",
            display_name="MCP commit failure fixture",
        )
        binding = self.server.store.create_binding(
            owner_id="owner_default",
            device_id=node["device_id"],
            workspace_id="workspace-mcp-commit-failure-0001",
            workspace_generation="generation-mcp-commit-failure-0001",
            display_name="MCP commit failure workspace",
        )
        context = self.server.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.server.store.clock() + 60_000,
        )
        before = self.server.store.health()["counts"]
        original_connection = self.server.store._connection
        with original_connection() as connection:
            before_event_count = int(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0])

        @contextmanager
        def failing_connection() -> object:
            with original_connection() as connection:
                yield _CommitFailingConnection(connection)

        request = {
            "jsonrpc": "2.0",
            "id": "mcp-fixed-intent-commit-failure-0001",
            "method": "tools/call",
            "params": {
                "name": "workspace_context",
                "arguments": {
                    "context_id": context["context_id"],
                    "operation": "request_read_only",
                    "idempotency_key": "mcp-fixed-intent-commit-failure-key-0001",
                    "expires_at_ms": self.server.store.clock() + 20_000,
                    "expected_facade_contract": {
                        key: self.server.mcp_facade.contract[key]
                        for key in ("schema_version", "profile", "sha256")
                    },
                },
            },
        }
        with mock.patch.object(self.server.store, "_connection", failing_connection):
            status, response = self._post("/mcp", request, f"Bearer {self.operator_token}")

        self.assertEqual(status, 503)
        self.assertEqual(response, {
            "error": {
                "code": "DURABLE_STORAGE_UNAVAILABLE",
                "message": "durable control-plane storage is unavailable.",
            }
        })
        self.assertNotIn("private", json.dumps(response))
        after = self.server.store.health()["counts"]
        for name in ("mcp_read_only_intents", "work_requests", "actions"):
            self.assertEqual(after[name], before[name], name)
        with original_connection() as connection:
            after_event_count = int(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0])
        self.assertEqual(after_event_count, before_event_count)

    def test_expected_package_source_fingerprint_must_be_valid_and_exact(self) -> None:
        actual = _package_source_sha256()
        matching = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            ControlPlaneStore(Path(self.tempdir.name) / "matching-fingerprint.sqlite3"),
            self.operator_token,
            "a" * 40,
            actual,
        )
        try:
            self.assertEqual(matching.package_source_sha256, actual)
            self.assertEqual(matching.expected_package_source_sha256, actual)
        finally:
            matching.server_close()

        with self.assertRaisesRegex(ValueError, "EXPECTED_PACKAGE_SOURCE_SHA256"):
            ControlPlaneHttpServer(
                ("127.0.0.1", 0),
                ControlPlaneStore(Path(self.tempdir.name) / "invalid-fingerprint.sqlite3"),
                self.operator_token,
                "a" * 40,
                "not-a-fingerprint",
            )

        with self.assertRaisesRegex(ValueError, "does not match"):
            ControlPlaneHttpServer(
                ("127.0.0.1", 0),
                ControlPlaneStore(Path(self.tempdir.name) / "mismatched-fingerprint.sqlite3"),
                self.operator_token,
                "a" * 40,
                "sha256:" + "0" * 64,
            )

    def test_mcp_facade_authenticates_and_queues_only_the_fixed_read_only_intent(self) -> None:
        initialize = {
            "jsonrpc": "2.0",
            "id": "initialize-001",
            "method": "initialize",
            "params": {"protocolVersion": "2025-11-25", "clientInfo": {"name": "control-plane-test", "version": "1.0"}},
        }
        status, forbidden = self._post("/mcp", initialize)
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")

        status, initialized = self._post("/mcp", initialize, f"Bearer {self.operator_token}")
        self.assertEqual(status, 200)
        self.assertEqual(initialized["result"]["protocolVersion"], "2025-11-25")
        self.assertEqual(initialized["result"]["_meta"]["control_plane"]["execution"], "local_admission_required")

        status, listed = self._post(
            "/mcp",
            {"jsonrpc": "2.0", "id": "list-001", "method": "tools/list", "params": {}},
            f"Bearer {self.operator_token}",
        )
        self.assertEqual(status, 200)
        tools = listed["result"]["tools"]
        self.assertEqual(
            [tool["name"] for tool in tools],
            [
                "workspace_context",
                "agent_workflow",
                "task_control",
                "document_workflow",
                "exec_command",
                "command_control",
                "request_permissions",
                "view_image",
            ],
        )
        self.assertTrue(all(tool["inputSchema"]["additionalProperties"] is False for tool in tools))

        discover = {
            "jsonrpc": "2.0",
            "id": "discover-001",
            "method": "server/discover",
            "params": {},
        }
        status, discovered = self._post("/mcp", discover, f"Bearer {self.operator_token}")
        self.assertEqual(status, 200)
        discovery = discovered["result"]
        self.assertEqual(discovery["protocolVersion"], initialized["result"]["protocolVersion"])
        self.assertEqual(discovery["serverInfo"], initialized["result"]["serverInfo"])
        self.assertEqual(discovery["_meta"], initialized["result"]["_meta"])
        self.assertEqual(
            [tool["name"] for tool in discovery["tools"]],
            [tool["name"] for tool in tools],
        )
        self.assertTrue(all(tool["inputSchema"]["additionalProperties"] is False for tool in discovery["tools"]))

        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-mcp-facade-001",
            endpoint_id="endpoint-mcp-facade-001",
            display_name="MCP facade canary",
        )
        binding = self.server.store.create_binding(
            owner_id="owner_default",
            device_id=node["device_id"],
            workspace_id="workspace-mcp-facade-001",
            workspace_generation="generation-mcp-facade-001",
            display_name="MCP facade workspace",
        )
        context = self.server.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.server.store.clock() + 60_000,
        )
        call = {
            "jsonrpc": "2.0",
            "id": "call-001",
            "method": "tools/call",
            "params": {"name": "workspace_context", "arguments": {"context_id": context["context_id"]}},
        }
        status, observed = self._post("/mcp", call, f"Bearer {self.operator_token}")
        self.assertEqual(status, 200)
        workspace = observed["result"]["structuredContent"]
        self.assertFalse(workspace["workspace_accessed"])
        self.assertEqual(workspace["execution"], "not_implemented")
        self.assertEqual(workspace["local_admission"], "unverified")
        self.assertEqual(workspace["context"]["context_id"], context["context_id"])

        call["id"] = "call-request-read-only-001"
        call["params"]["arguments"] = {
            "context_id": context["context_id"],
            "operation": "request_read_only",
            "idempotency_key": "mcp-facade-action-status-0001",
            "expires_at_ms": self.server.store.clock() + 20_000,
            "expected_facade_contract": {
                key: self.server.mcp_facade.contract[key]
                for key in ("schema_version", "profile", "sha256")
            },
        }
        status, queued = self._post("/mcp", call, f"Bearer {self.operator_token}")
        self.assertEqual(status, 200)
        intent = queued["result"]["structuredContent"]
        self.assertFalse(intent["workspace_accessed"])
        self.assertEqual(intent["execution"], "queued_for_local_admission")
        self.assertEqual(intent["local_admission"], "required")
        self.assertFalse(intent["replayed"])
        self.assertEqual(intent["facade_contract"], {
            key: self.server.mcp_facade.contract[key]
            for key in ("schema_version", "profile", "sha256")
        })
        self.assertEqual(intent["action"]["tool_name"], "workspace_context")
        self.assertEqual(intent["action"]["central_lifecycle_state"], "queued")
        self.assertEqual(self.server.store.health()["counts"]["mcp_read_only_intents"], 1)
        action = {"action_id": intent["action_id"]}

        call["id"] = "call-request-read-only-replay-001"
        status, replayed = self._post("/mcp", call, f"Bearer {self.operator_token}")
        self.assertEqual(status, 200)
        replay = replayed["result"]["structuredContent"]
        self.assertTrue(replay["replayed"])
        self.assertEqual(replay["request_id"], intent["request_id"])
        self.assertEqual(replay["action_id"], action["action_id"])

        call["id"] = "call-request-read-only-conflict-001"
        call["params"]["arguments"]["expires_at_ms"] += 1
        status, conflict = self._post("/mcp", call, f"Bearer {self.operator_token}")
        self.assertEqual(status, 200)
        self.assertEqual(conflict["error"]["code"], -32602)
        self.assertEqual(self.server.store.health()["counts"]["actions"], 1)
        call["params"]["arguments"]["expires_at_ms"] -= 1

        call["id"] = "call-request-read-only-contract-mismatch-001"
        call["params"]["arguments"]["expected_facade_contract"] = {
            "schema_version": self.server.mcp_facade.contract["schema_version"],
            "profile": self.server.mcp_facade.contract["profile"],
            "sha256": "0" * 64,
        }
        status, mismatch = self._post("/mcp", call, f"Bearer {self.operator_token}")
        self.assertEqual(status, 200)
        self.assertEqual(mismatch["error"]["code"], -32602)
        self.assertEqual(mismatch["error"]["data"]["code"], "CONTRACT_MISMATCH")
        self.assertEqual(self.server.store.health()["counts"]["actions"], 1)
        call["params"]["arguments"]["expected_facade_contract"] = {
            key: self.server.mcp_facade.contract[key]
            for key in ("schema_version", "profile", "sha256")
        }

        self.server.store.heartbeat(
            device_id=node["device_id"],
            endpoint_id="endpoint-mcp-facade-001",
            runtime_instance_id="mcp-process-facade-status-0001",
            mcp_server_instance_id="mcp-server-facade-status-0001",
            activation_epoch="activation-facade-status-0001",
            contract_version="sha256:" + "a" * 64,
            readiness="ready",
        )
        polled = self.server.store.poll_actions(device_id=node["device_id"])
        self.assertEqual([item["action_id"] for item in polled], [action["action_id"]])
        attempt = polled[0]
        call["id"] = "call-action-dispatch-unconfirmed-001"
        call["params"]["arguments"] = {
            "context_id": context["context_id"],
            "action_id": action["action_id"],
        }
        status, dispatch_unconfirmed = self._post("/mcp", call, f"Bearer {self.operator_token}")
        self.assertEqual(status, 200)
        self.assertEqual(
            dispatch_unconfirmed["result"]["structuredContent"]["action"]["central_lifecycle_state"],
            "dispatch_unconfirmed",
        )
        self.server.store.record_receipt(
            device_id=node["device_id"],
            action_id=action["action_id"],
            attempt_id=attempt["attempt_id"],
            receipt_state="completed",
            local_handle="local-handle-must-not-reach-facade",
            payload={"workspace": "E:/must-not-reach-facade", "raw_response": "must-not-reach-facade"},
        )
        call["id"] = "call-action-status-001"
        call["params"]["arguments"] = {
            "context_id": context["context_id"],
            "action_id": action["action_id"],
        }
        status, action_observed = self._post("/mcp", call, f"Bearer {self.operator_token}")
        self.assertEqual(status, 200)
        lifecycle = action_observed["result"]["structuredContent"]["action"]
        self.assertEqual(lifecycle["action_id"], action["action_id"])
        self.assertEqual(lifecycle["delivery_state"], "settled")
        self.assertEqual(lifecycle["central_lifecycle_state"], "completed")
        self.assertEqual(len(lifecycle["attempts"]), 1)
        self.assertEqual(len(lifecycle["receipts"]), 1)
        self.assertEqual(lifecycle["receipts"][0]["receipt_state"], "completed")
        self.assertNotIn("arguments_json", json.dumps(lifecycle))
        self.assertNotIn("admission_reference", json.dumps(lifecycle))
        self.assertNotIn("must-not-reach-facade", json.dumps(lifecycle))

        other_context = self.server.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.server.store.clock() + 60_000,
        )
        call["id"] = "call-action-status-foreign-context"
        call["params"]["arguments"]["context_id"] = other_context["context_id"]
        status, wrong_context = self._post("/mcp", call, f"Bearer {self.operator_token}")
        self.assertEqual(status, 200)
        self.assertEqual(wrong_context["error"]["code"], -32602)

        call["id"] = "call-002"
        call["params"]["name"] = "exec_command"
        status, rejected = self._post("/mcp", call, f"Bearer {self.operator_token}")
        self.assertEqual(status, 200)
        self.assertTrue(rejected["result"]["isError"])
        self.assertEqual(rejected["result"]["structuredContent"]["code"], "LOCAL_ADMISSION_BRIDGE_REQUIRED")
        self.assertEqual(self.server.store.health()["counts"]["actions"], 1,
                         "unavailable public tools must not create a second action")

        status, invalid_tool = self._post(
            "/mcp",
            {"jsonrpc": "2.0", "id": "call-003", "method": "tools/call", "params": {"name": "unknown", "arguments": {"context_id": context["context_id"]}}},
            f"Bearer {self.operator_token}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(invalid_tool["error"]["code"], -32602)

        status, malformed = self._post(
            "/mcp",
            {"jsonrpc": "2.0", "id": True, "method": "ping", "params": {}},
            f"Bearer {self.operator_token}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(malformed["error"]["code"], -32600)

    def test_facade_lifecycle_state_never_infers_local_execution_or_outcome(self) -> None:
        self.assertEqual(_central_lifecycle_state({"delivery_state": "queued", "receipts": []}), "queued")
        self.assertEqual(
            _central_lifecycle_state({"delivery_state": "dispatch_unconfirmed", "receipts": []}),
            "dispatch_unconfirmed",
        )
        self.assertEqual(_central_lifecycle_state({"delivery_state": "accepted", "receipts": []}), "accepted")
        self.assertEqual(
            _central_lifecycle_state({"delivery_state": "reconcile_required", "receipts": []}),
            "reconcile_required",
        )
        self.assertEqual(
            _central_lifecycle_state({"delivery_state": "settled", "receipts": [{"receipt_state": "completed"}]}),
            "completed",
        )
        self.assertEqual(
            _central_lifecycle_state({"delivery_state": "settled", "receipts": [{"receipt_state": "rejected"}]}),
            "rejected",
        )
        self.assertEqual(
            _central_lifecycle_state({"delivery_state": "settled", "receipts": [{"receipt_state": "failed"}]}),
            "failed",
        )
        self.assertEqual(
            _central_lifecycle_state({"delivery_state": "settled", "receipts": []}),
            "settled_without_receipt",
        )
        self.assertEqual(
            _central_lifecycle_state({"delivery_state": "settled", "receipts": [{"receipt_state": "accepted"}]}),
            "settled_with_nonterminal_receipt",
        )
        self.assertEqual(
            _central_lifecycle_state({"delivery_state": "unexpected", "receipts": []}),
            "unrecognized_central_lifecycle_state",
        )

    def test_owner_observation_inventory_routes_are_authenticated_and_credential_free(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-observation-canary",
            endpoint_id="endpoint-observation-canary",
            display_name="Observation Canary",
        )
        binding = self.server.store.create_binding(
            owner_id="owner_default",
            device_id=node["device_id"],
            workspace_id="workspace-observation-canary",
            workspace_generation="generation-observation-canary",
            display_name="Observation workspace",
        )
        now = self.server.store.clock()
        context = self.server.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=now + 60_000,
        )
        request = self.server.store.create_work_request(
            owner_id="owner_default",
            context_id=context["context_id"],
            objective="Observe lineage",
            criteria={"kind": "read_only"},
            scope={"root": "canary"},
            expires_at_ms=now + 30_000,
        )
        action = self.server.store.seal_action(
            owner_id="owner_default",
            request_id=request["request_id"],
            tool_name="workspace_context",
            arguments={"mode": "status"},
            idempotency_key="action-key-http-0020",
            admission_reference="admission-http-0020",
            expires_at_ms=now + 20_000,
        )
        for path in (
            "/v1/nodes",
            f"/v1/nodes/{node['device_id']}",
            "/v1/contexts",
            f"/v1/contexts/{context['context_id']}",
            "/v1/work-requests",
            f"/v1/work-requests/{request['request_id']}",
        ):
            status, forbidden = self._get(path)
            self.assertEqual(status, 403, path)
            self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")

        auth = f"Bearer {self.operator_token}"
        status, nodes = self._get("/v1/nodes", auth)
        self.assertEqual(status, 200)
        self.assertEqual(nodes["nodes"][0]["device_id"], node["device_id"])
        self.assertNotIn("credential_hash", nodes["nodes"][0])
        self.assertNotIn("node_secret", nodes["nodes"][0])
        status, observed_request = self._get(f"/v1/work-requests/{request['request_id']}", auth)
        self.assertEqual(status, 200)
        self.assertEqual(observed_request["actions"][0]["action_id"], action["action_id"])
        self.assertNotIn("arguments_json", observed_request["actions"][0])
        self.assertNotIn("admission_reference", observed_request["actions"][0])

    def test_authority_lifecycle_routes_require_operator(self) -> None:
        for path in (
            "/v1/maintenance/admission",
            "/v1/nodes/device-http-canary/revoke",
            "/v1/nodes/device-http-canary/rotate-credential",
            "/v1/bindings/binding-http-canary/revoke",
            "/v1/contexts/context-http-canary/close",
            "/v1/work-requests/request-http-canary/cancel",
        ):
            status, forbidden = self._post(path, {})
            self.assertEqual(status, 403, path)
            self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")
        status, forbidden = self._get("/v1/maintenance/admission")
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")
