from __future__ import annotations

from contextlib import contextmanager, redirect_stdout
import io
import hashlib
import json
import sqlite3
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest import mock

from control_plane.http_api import (
    CSRF_HEADER_NAME,
    SESSION_COOKIE_NAME,
    ControlPlaneHttpServer,
    _package_source_sha256,
    _web_origin,
)
from control_plane.web_ui import WEB_UI_JAVASCRIPT
from control_plane.mcp_facade import _central_lifecycle_state
from control_plane.node_agent import poll_read_only_once
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
        self.web_origin = "https://operator.tailnet.example"
        self.server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            ControlPlaneStore(Path(self.tempdir.name) / "control.sqlite3"),
            self.operator_token,
            "a" * 40,
            web_origin=self.web_origin,
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

    def _request_with_headers(
        self,
        path: str,
        *,
        method: str,
        payload: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict, dict[str, str]]:
        request_headers = dict(headers or {})
        data = None
        if payload is not None:
            request_headers.setdefault("Content-Type", "application/json")
            data = json.dumps(payload).encode("utf-8")
        request = Request(f"{self.base_url}{path}", data=data, headers=request_headers, method=method)
        try:
            with urlopen(request, timeout=2) as response:
                return response.status, json.loads(response.read()), dict(response.headers.items())
        except HTTPError as error:
            try:
                return error.code, json.loads(error.read()), dict(error.headers.items())
            finally:
                error.close()

    def _ui_login(self) -> tuple[str, str]:
        status, response, headers = self._request_with_headers(
            "/v1/ui/login",
            method="POST",
            payload={"operator_token": self.operator_token},
            headers={"Origin": self.web_origin},
        )
        self.assertEqual(status, 200)
        self.assertTrue(response["authenticated"])
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertIn("Secure", headers["Set-Cookie"])
        self.assertIn("SameSite=Strict", headers["Set-Cookie"])
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        self.assertTrue(cookie.startswith(f"{SESSION_COOKIE_NAME}="))
        return cookie, response["csrf_token"]

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

    def test_browser_ui_approves_only_selected_pending_enrollment_with_csrf(self) -> None:
        node_secret = "b" * 40
        credential_hash = hashlib.sha256(
            json.dumps({"node_secret": node_secret}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        status, enrollment = self._post(
            "/v1/enrollment-requests",
            {
                "device_id": "device-browser-enrollment-0001",
                "endpoint_id": "endpoint-browser-enrollment-0001",
                "display_name": "Browser enrollment node",
                "credential_hash": credential_hash,
            },
        )
        self.assertEqual(status, 201)
        cookie, csrf_token = self._ui_login()

        status, forbidden, _headers = self._request_with_headers(
            f"/v1/ui/enrollment-requests/{enrollment['enrollment_id']}/approve",
            method="POST",
            payload={},
            headers={"Cookie": cookie, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")
        self.assertFalse(self.server.store.list_enrollment_requests()[0]["approved_at_ms"])
        self.assertEqual(self.server.store.health()["counts"]["nodes"], 0)

        status, invalid, _headers = self._request_with_headers(
            f"/v1/ui/enrollment-requests/{enrollment['enrollment_id']}/approve",
            method="POST",
            payload={"device_id": "another-node"},
            headers={"Cookie": cookie, "Origin": self.web_origin, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 400)
        self.assertEqual(invalid["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(self.server.store.health()["counts"]["nodes"], 0)

        status, approved, _headers = self._request_with_headers(
            f"/v1/ui/enrollment-requests/{enrollment['enrollment_id']}/approve",
            method="POST",
            payload={},
            headers={"Cookie": cookie, "Origin": self.web_origin, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 200)
        self.assertEqual(approved["device_id"], "device-browser-enrollment-0001")
        self.assertNotIn("node_secret", json.dumps(approved))
        self.assertEqual(self.server.store.health()["counts"]["nodes"], 1)
        self.assertEqual(self.server.store.health()["counts"]["bindings"], 0)
        self.assertEqual(self.server.store.health()["counts"]["contexts"], 0)
        self.assertEqual(self.server.store.health()["counts"]["actions"], 0)

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
        self.assertEqual(health["schema_version"], 8)
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

    def test_private_web_ui_requires_explicit_https_origin_and_serves_only_allowlisted_assets(self) -> None:
        request = Request(f"{self.base_url}/", method="GET")
        with urlopen(request, timeout=2) as response:
            document = response.read().decode("utf-8")
            self.assertIn("PRIVATE TAILNET OPERATOR CONSOLE", document)
            self.assertEqual(response.headers["Cache-Control"], "no-store")
            self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])

        request = Request(f"{self.base_url}/assets/control-plane-ui.js", method="GET")
        with urlopen(request, timeout=2) as response:
            javascript = response.read().decode("utf-8")
            self.assertEqual(response.headers["Content-Type"], "application/javascript; charset=utf-8")
            self.assertIn("credentials: 'same-origin'", javascript)
            self.assertIn("textContent", javascript)
            self.assertNotIn("localStorage", javascript)
            self.assertNotIn("sessionStorage", javascript)
        self.assertNotIn(self.operator_token, WEB_UI_JAVASCRIPT.decode("utf-8"))
        status, missing_asset = self._get("/assets/not-allowed.js")
        self.assertEqual(status, 404)
        self.assertEqual(missing_asset["error"]["code"], "NOT_FOUND")

        no_origin_status, no_origin, _headers = self._request_with_headers(
            "/v1/ui/login",
            method="POST",
            payload={"operator_token": self.operator_token},
        )
        self.assertEqual(no_origin_status, 403)
        self.assertEqual(no_origin["error"]["code"], "FORBIDDEN")
        wrong_origin_status, wrong_origin, _headers = self._request_with_headers(
            "/v1/ui/login",
            method="POST",
            payload={"operator_token": self.operator_token},
            headers={"Origin": "https://wrong.tailnet.example"},
        )
        self.assertEqual(wrong_origin_status, 403)
        self.assertEqual(wrong_origin["error"]["code"], "FORBIDDEN")

    def test_embedded_operator_ui_javascript_parses_before_it_is_served(self) -> None:
        completed = subprocess.run(
            ["node", "--check", "-"],
            input=WEB_UI_JAVASCRIPT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))

    def test_web_ui_session_read_model_and_admission_control_are_scoped_and_csrf_protected(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-web-ui-0001",
            endpoint_id="endpoint-web-ui-0001",
            display_name="Web UI Windows node",
        )
        binding = self.server.store.create_binding(
            owner_id="owner_default",
            device_id=node["device_id"],
            workspace_id="workspace-web-ui-0001",
            workspace_generation="generation-web-ui-0001",
            display_name="Web UI workspace",
        )
        context = self.server.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.server.store.clock() + 60_000,
        )
        request = self.server.store.create_work_request(
            owner_id="owner_default",
            context_id=context["context_id"],
            objective="private operator objective must not be in overview",
            criteria={"private": "criteria must not be in overview"},
            scope={"private": "scope must not be in overview"},
            expires_at_ms=self.server.store.clock() + 30_000,
        )
        action = self.server.store.seal_action(
            owner_id="owner_default",
            request_id=request["request_id"],
            tool_name="workspace_context",
            arguments={"private": "raw action arguments must not be in overview"},
            idempotency_key="web-ui-overview-action-0001",
            admission_reference="private-admission-reference-0001",
            expires_at_ms=self.server.store.clock() + 20_000,
        )
        self.server.store.heartbeat(
            device_id=node["device_id"],
            endpoint_id="endpoint-web-ui-0001",
            runtime_instance_id="web-ui-runtime-0001",
            mcp_server_instance_id="web-ui-mcp-0001",
            activation_epoch="web-ui-epoch-0001",
            contract_version="sha256:" + "b" * 64,
            readiness="ready",
        )
        attempt = self.server.store.poll_actions(device_id=node["device_id"])[0]
        self.server.store.record_receipt(
            device_id=node["device_id"],
            action_id=action["action_id"],
            attempt_id=attempt["attempt_id"],
            receipt_state="completed",
            local_handle="private local handle must not be in overview",
            payload={"private": "receipt payload must not be in overview"},
        )
        cookie, csrf_token = self._ui_login()

        session_status, session, _headers = self._request_with_headers(
            "/v1/ui/session",
            method="GET",
            headers={"Cookie": cookie},
        )
        self.assertEqual(session_status, 200)
        self.assertEqual(session["csrf_token"], csrf_token)

        status, overview, headers = self._request_with_headers(
            "/v1/ui/overview",
            method="GET",
            headers={"Cookie": cookie},
        )
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(overview["observation_kind"], "central_control_plane_read_model")
        self.assertEqual([item["device_id"] for item in overview["nodes"]], [node["device_id"]])
        self.assertEqual(overview["work_requests"][0]["context_id"], context["context_id"])
        self.assertEqual([item["action_id"] for item in overview["actions"]], [action["action_id"]])
        self.assertEqual(overview["actions"][0]["delivery_state"], "settled")
        self.assertEqual(overview["actions"][0]["latest_receipt_state"], "completed")
        self.assertEqual(overview["actions"][0]["receipt_count"], 1)
        overview_text = json.dumps(overview)
        self.assertNotIn("private operator objective", overview_text)
        self.assertNotIn("criteria must not", overview_text)
        self.assertNotIn("scope must not", overview_text)
        self.assertNotIn("raw action arguments", overview_text)
        self.assertNotIn("private-admission-reference-0001", overview_text)
        self.assertNotIn("private local handle", overview_text)
        self.assertNotIn("receipt payload", overview_text)
        self.assertNotIn(self.operator_token, overview_text)

        status, rejected, _headers = self._request_with_headers(
            "/v1/maintenance/admission",
            method="POST",
            payload={"mode": "recovery"},
            headers={"Cookie": cookie},
        )
        self.assertEqual(status, 403)
        self.assertEqual(rejected["error"]["code"], "FORBIDDEN")
        self.assertEqual(self.server.store.admission_status()["admission_mode"], "open")

        status, changed, _headers = self._request_with_headers(
            "/v1/maintenance/admission",
            method="POST",
            payload={"mode": "recovery"},
            headers={"Cookie": cookie, "Origin": self.web_origin, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 200)
        self.assertEqual(changed["admission_mode"], "recovery")

        status, reopen_rejected, _headers = self._request_with_headers(
            "/v1/maintenance/admission",
            method="POST",
            payload={"mode": "open"},
            headers={"Cookie": cookie, "Origin": self.web_origin, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 403)
        self.assertEqual(reopen_rejected["error"]["code"], "FORBIDDEN")
        self.assertEqual(self.server.store.admission_status()["admission_mode"], "recovery")

        # Existing non-browser bearer automation retains its explicit owner
        # path; the browser session cannot use that route to reopen admission.
        status, reopened = self._post(
            "/v1/maintenance/admission",
            {"mode": "open"},
            f"Bearer {self.operator_token}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(reopened["admission_mode"], "open")

        status, logged_out, headers = self._request_with_headers(
            "/v1/ui/logout",
            method="POST",
            payload={},
            headers={"Cookie": cookie, "Origin": self.web_origin, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 200)
        self.assertFalse(logged_out["authenticated"])
        self.assertIn("Max-Age=0", headers["Set-Cookie"])
        status, unauthorized, _headers = self._request_with_headers(
            "/v1/ui/overview",
            method="GET",
            headers={"Cookie": cookie},
        )
        self.assertEqual(status, 403)
        self.assertEqual(unauthorized["error"]["code"], "FORBIDDEN")

    def test_browser_overview_shows_redacted_node_policy_state_without_digest(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-browser-policy-0001",
            endpoint_id="endpoint-browser-policy-0001",
            display_name="Browser policy node",
        )
        policy_sha256 = "c" * 64
        self.server.store.heartbeat(
            device_id=node["device_id"],
            endpoint_id="endpoint-browser-policy-0001",
            runtime_instance_id="runtime-browser-policy-0001",
            mcp_server_instance_id="server-browser-policy-0001",
            activation_epoch="epoch-browser-policy-0001",
            contract_version="sha256:" + "d" * 64,
            readiness="ready",
            policy_observation={
                "state": "enabled",
                "expires_at_ms": self.server.store.clock() + 60_000,
                "policy_sha256": policy_sha256,
                "reason": "",
            },
        )
        cookie, _csrf_token = self._ui_login()
        status, overview, _headers = self._request_with_headers(
            "/v1/ui/overview",
            method="GET",
            headers={"Cookie": cookie},
        )
        self.assertEqual(status, 200)
        displayed = overview["nodes"][0]
        self.assertEqual(displayed["policy_state"], "enabled")
        self.assertIsNone(displayed["policy_reason"])
        self.assertNotIn("policy_sha256", displayed)
        self.assertNotIn(policy_sha256, json.dumps(overview))
        self.assertNotIn(node["node_secret"], json.dumps(overview))

    def test_browser_ui_queues_only_one_fixed_read_only_canary_per_live_session_context(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-browser-canary-0001",
            endpoint_id="endpoint-browser-canary-0001",
            display_name="Browser canary node",
        )
        binding = self.server.store.create_binding(
            owner_id="owner_default",
            device_id=node["device_id"],
            workspace_id="workspace-browser-canary-0001",
            workspace_generation="generation-browser-canary-0001",
            display_name="Browser canary workspace",
        )
        context = self.server.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.server.store.clock() + 60_000,
        )
        cookie, csrf_token = self._ui_login()

        status, forbidden, _headers = self._request_with_headers(
            "/v1/ui/read-only-requests",
            method="POST",
            payload={"context_id": context["context_id"]},
            headers={"Cookie": cookie, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")
        self.assertEqual(self.server.store.health()["counts"]["actions"], 0)

        status, invalid, _headers = self._request_with_headers(
            "/v1/ui/read-only-requests",
            method="POST",
            payload={"context_id": context["context_id"], "tool_name": "exec_command"},
            headers={"Cookie": cookie, "Origin": self.web_origin, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 400)
        self.assertEqual(invalid["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(self.server.store.health()["counts"]["actions"], 0)

        headers = {"Cookie": cookie, "Origin": self.web_origin, CSRF_HEADER_NAME: csrf_token}
        status, queued, _headers = self._request_with_headers(
            "/v1/ui/read-only-requests",
            method="POST",
            payload={"context_id": context["context_id"]},
            headers=headers,
        )
        self.assertEqual(status, 201, queued)
        self.assertFalse(queued["replayed"])
        self.assertGreater(queued["expires_at_ms"], self.server.store.clock())
        self.assertLessEqual(queued["expires_at_ms"], self.server.store.clock() + 10 * 60 * 1000)
        action = self.server.store.action(owner_id="owner_default", action_id=queued["action_id"])
        self.assertEqual(action["context_id"], context["context_id"])
        self.assertEqual(action["tool_name"], "workspace_context")
        self.assertEqual(json.loads(action["arguments_json"]), {"detail": "compact", "max_entries": 1})
        self.assertEqual(action["delivery_state"], "queued")
        self.assertEqual(self.server.store.health()["counts"]["actions"], 1)
        self.assertNotIn(self.operator_token, json.dumps(queued))

        status, replayed, _headers = self._request_with_headers(
            "/v1/ui/read-only-requests",
            method="POST",
            payload={"context_id": context["context_id"]},
            headers=headers,
        )
        self.assertEqual(status, 201)
        self.assertTrue(replayed["replayed"])
        self.assertEqual(replayed["action_id"], queued["action_id"])
        self.assertEqual(replayed["request_id"], queued["request_id"])
        self.assertEqual(self.server.store.health()["counts"]["actions"], 1)

    def test_browser_fixed_canary_flows_through_central_poll_and_receipt_to_redacted_overview(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-browser-flow-0001",
            endpoint_id="endpoint-browser-flow-0001",
            display_name="Browser flow node",
        )
        binding = self.server.store.create_binding(
            owner_id="owner_default",
            device_id=node["device_id"],
            workspace_id="workspace-browser-flow-0001",
            workspace_generation="generation-browser-flow-0001",
            display_name="Browser flow workspace",
        )
        context = self.server.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.server.store.clock() + 60_000,
        )
        cookie, csrf_token = self._ui_login()
        headers = {"Cookie": cookie, "Origin": self.web_origin, CSRF_HEADER_NAME: csrf_token}
        status, queued, _headers = self._request_with_headers(
            "/v1/ui/read-only-requests",
            method="POST",
            payload={"context_id": context["context_id"]},
            headers=headers,
        )
        self.assertEqual(status, 201, queued)

        runtime_identity = {
            "observation_schema_version": 1,
            "observation_kind": "mcp_identity_read_only",
            "mcp_ready": True,
            "identity_current": True,
            "mcp_process_instance_id": "mcp-process-browser-flow-0001",
            "mcp_server_instance_id": "mcp-server-browser-flow-0001",
            "activation_epoch_id": "activation-browser-flow-0001",
            "current_activation_epoch_id": "activation-browser-flow-0001",
            "tool_contract_sha256": "a" * 64,
        }
        self.server.store.heartbeat(
            device_id=node["device_id"],
            endpoint_id="endpoint-browser-flow-0001",
            runtime_instance_id=runtime_identity["mcp_process_instance_id"],
            mcp_server_instance_id=runtime_identity["mcp_server_instance_id"],
            activation_epoch=runtime_identity["activation_epoch_id"],
            contract_version="sha256:" + "a" * 64,
            readiness="ready",
        )
        config_path = Path(self.tempdir.name) / "browser-flow-node.json"
        config_path.write_text(json.dumps({
            "server_url": self.base_url,
            "device_id": node["device_id"],
            "endpoint_id": "endpoint-browser-flow-0001",
            "node_secret": node["node_secret"],
        }), encoding="utf-8")
        runtime_status = {
            "state": "CURRENT", "host": "available", "installation": "current",
            "mcp_update_pending": "false", "mcp_running_revision": "sha-current", "mcp_disk_revision": "sha-current",
            "components_ready": "true", "fully_ready": "true", "runtime_update_incomplete": "false",
            "runtime_telemetry_available": "true", "runtime_signal_stale": "false",
            "connector_state": "CURRENT_ACKNOWLEDGED", "connector_rediscovered": "true",
            "connector_rediscovered_at": "2026-09-16T00:00:00Z", "connector_freshness_mode": "current_process_discovery",
            "connector_refresh_required": "false", "connector_ack_pending": "false",
            "connector_current_sha": "sha-current", "connector_ack_sha": "sha-current", "error_code": "none",
        }

        def bridge(_args: object, _root: Path, request: dict) -> tuple[dict, None]:
            return ({
                "schema_version": 1,
                "operation_kind": "control_plane_read_only_workspace_context",
                "action_id": request["action_id"],
                "attempt_id": request["attempt_id"],
                "local_handle": "cp_ro_" + "b" * 48,
                "workspace_accessed": True,
                "policy_sha256": "c" * 64,
                "actor": {"client_id": "electron-control-plane-bridge", "client_type": "electron"},
                "runtime_identity": {
                    "activation_epoch_id": runtime_identity["activation_epoch_id"],
                    "process_instance_id": runtime_identity["mcp_process_instance_id"],
                    "server_instance_id": runtime_identity["mcp_server_instance_id"],
                    "tool_contract_sha256": "a" * 64,
                },
                "facade_contract": request["facade_contract"],
                "response_sha256": "d" * 64,
                "workspace": "E:/must-not-reach-central-or-browser",
            }, None)

        args = SimpleNamespace(
            config=str(config_path), project_root=str(Path(self.tempdir.name)), node="node",
            runtime_mode="development", timeout_seconds=20, limit=1,
        )
        with mock.patch("control_plane.node_agent._runtime_status", return_value=runtime_status), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=runtime_identity), \
             mock.patch("control_plane.node_agent.recovery_read_only_bridge", side_effect=bridge), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_read_only_once(args), 0)

        action = self.server.store.action_observation(owner_id="owner_default", action_id=queued["action_id"])
        self.assertEqual(action["delivery_state"], "settled")
        self.assertEqual(action["receipts"][0]["receipt_state"], "completed")
        status, overview, _headers = self._request_with_headers(
            "/v1/ui/overview",
            method="GET",
            headers={"Cookie": cookie},
        )
        self.assertEqual(status, 200)
        self.assertEqual(overview["actions"][0]["action_id"], queued["action_id"])
        self.assertEqual(overview["actions"][0]["delivery_state"], "settled")
        self.assertEqual(overview["actions"][0]["latest_receipt_state"], "completed")
        overview_text = json.dumps(overview)
        self.assertNotIn("must-not-reach-central-or-browser", overview_text)
        self.assertNotIn("cp_ro_", overview_text)
        self.assertNotIn(node["node_secret"], overview_text)

    def test_web_origin_validation_and_login_rate_limit_fail_closed(self) -> None:
        self.assertEqual(_web_origin("https://Operator.Tailnet.Example/"), self.web_origin)
        for invalid in ("http://operator.tailnet.example", "https://operator.tailnet.example/path", "https://user@operator.tailnet.example"):
            with self.assertRaises(ValueError):
                _web_origin(invalid)

        for _attempt in range(5):
            status, response, _headers = self._request_with_headers(
                "/v1/ui/login",
                method="POST",
                payload={"operator_token": "wrong"},
                headers={"Origin": self.web_origin},
            )
            self.assertEqual(status, 403)
            self.assertEqual(response["error"]["code"], "FORBIDDEN")
        status, response, _headers = self._request_with_headers(
            "/v1/ui/login",
            method="POST",
            payload={"operator_token": self.operator_token},
            headers={"Origin": self.web_origin},
        )
        self.assertEqual(status, 429)
        self.assertEqual(response["error"]["code"], "RATE_LIMITED")

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
