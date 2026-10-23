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
    _mcp_ingress_address_from_environment,
    _package_source_sha256,
    _web_origin,
)
from control_plane.web_ui import WEB_UI_HTML, WEB_UI_JAVASCRIPT
from control_plane.mcp_facade import _central_lifecycle_state
from control_plane.node_agent import _credential_hash, poll_read_only_once
from control_plane.store import ControlPlaneStore, PermissionError, SCHEMA_VERSION


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

    def _registered_binding(
        self,
        *,
        owner_id: str,
        device_id: str,
        workspace_id: str,
        workspace_generation: str,
        display_name: str,
    ) -> dict:
        self.server.store.register_node_workspace(
            device_id=device_id,
            workspace_id=workspace_id,
            workspace_generation=workspace_generation,
            display_name=display_name,
            capabilities={"read": True, "write": False, "exec": False},
        )
        return self.server.store.create_binding(
            owner_id=owner_id,
            device_id=device_id,
            workspace_id=workspace_id,
            workspace_generation=workspace_generation,
            display_name=display_name,
        )

    def test_shared_service_and_scoped_pilot_operator_routes_stay_redacted_and_csrf_protected(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default", device_id="device-pilot-http",
            endpoint_id="endpoint-pilot-http", display_name="Pilot node",
        )
        binding = self._registered_binding(
            owner_id="owner_default", device_id=node["device_id"],
            workspace_id="workspace-pilot-http", workspace_generation="generation-pilot-http",
            display_name="Pilot workspace",
        )
        status, principal = self._post(
            "/v1/mcp-service-principals", {}, f"Bearer {self.operator_token}",
        )
        self.assertEqual(status, 201)
        status, grant = self._post("/v1/mcp-service-grants", {
            "principal_id": principal["principal_id"],
            "expires_at_ms": self.server.store.clock() + 60_000,
            "scopes": ["control-plane.inventory", "control-plane.read", "control-plane.patch"],
        }, f"Bearer {self.operator_token}")
        self.assertEqual(status, 201)
        self.assertIn("access_token", grant)
        self.server.store.set_admission_mode(mode="recovery")
        status, decision = self._post("/v1/scoped-pilot-decisions", {
            "principal_id": principal["principal_id"],
            "binding_id": binding["binding_id"],
            "expires_at_ms": self.server.store.clock() + 60_000,
            "reason": "Exact selected workspace pilot",
        }, f"Bearer {self.operator_token}")
        self.assertEqual(status, 201)
        status, overview = self._get("/v1/ui/overview", f"Bearer {self.operator_token}")
        self.assertEqual(status, 200)
        self.assertEqual(len(overview["mcp_service_principals"]), 1)
        self.assertEqual(len(overview["mcp_service_grants"]), 1)
        self.assertEqual(len(overview["scoped_pilot_decisions"]), 1)
        self.assertNotIn(grant["access_token"], json.dumps(overview))
        self.assertNotIn("token_digest", json.dumps(overview))
        renewed_grant_expiry = self.server.store.clock() + 120_000
        status, renewed_grant = self._post(
            f"/v1/mcp-service-grants/{grant['grant_id']}/renew",
            {"expires_at_ms": renewed_grant_expiry},
            f"Bearer {self.operator_token}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(renewed_grant["expires_at_ms"], renewed_grant_expiry)
        renewed_decision_expiry = self.server.store.clock() + 120_000
        status, renewed_decision = self._post(
            f"/v1/scoped-pilot-decisions/{decision['decision_id']}/renew",
            {"expires_at_ms": renewed_decision_expiry},
            f"Bearer {self.operator_token}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(renewed_decision["expires_at_ms"], renewed_decision_expiry)
        cookie, csrf = self._ui_login()
        status, forbidden, _ = self._request_with_headers(
            f"/v1/ui/scoped-pilot-decisions/{decision['decision_id']}/revoke",
            method="POST", payload={}, headers={"Origin": self.web_origin, "Cookie": cookie},
        )
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")
        headers = {"Origin": self.web_origin, "Cookie": cookie, CSRF_HEADER_NAME: csrf}
        status, revoked, _ = self._request_with_headers(
            f"/v1/ui/scoped-pilot-decisions/{decision['decision_id']}/revoke",
            method="POST", payload={}, headers=headers,
        )
        self.assertEqual(status, 200)
        self.assertIsNotNone(revoked["revoked_at_ms"])
        status, revoked_grant, _ = self._request_with_headers(
            f"/v1/ui/mcp-service-grants/{grant['grant_id']}/revoke",
            method="POST", payload={}, headers=headers,
        )
        self.assertEqual(status, 200)
        self.assertIsNotNone(revoked_grant["revoked_at_ms"])

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

    def test_node_enrollment_status_reconciles_pending_approved_and_revoked_without_operator_auth(self) -> None:
        node_secret = "status-node-secret-0001"
        credential_hash = hashlib.sha256(
            json.dumps({"node_secret": node_secret}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        status, request = self._post(
            "/v1/enrollment-requests",
            {
                "device_id": "device-http-status-0001",
                "endpoint_id": "endpoint-http-status-0001",
                "display_name": "HTTP status node",
                "credential_hash": credential_hash,
            },
        )
        self.assertEqual(status, 201)
        status, pending = self._post(
            "/v1/nodes/device-http-status-0001/enrollment-status",
            {"enrollment_id": request["enrollment_id"]},
            f"Node {node_secret}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(pending["state"], "pending_operator_approval")
        status, forbidden = self._post(
            "/v1/nodes/device-http-status-0001/enrollment-status",
            {},
            "Node wrong-status-secret-0001",
        )
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")
        status, _approved = self._post(
            f"/v1/enrollment-requests/{request['enrollment_id']}/approve",
            {},
            f"Bearer {self.operator_token}",
        )
        self.assertEqual(status, 200)
        status, approved = self._post(
            "/v1/nodes/device-http-status-0001/enrollment-status",
            {},
            f"Node {node_secret}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(approved["state"], "approved")
        self.assertEqual(approved["credential_generation"], 1)
        self.server.store.revoke_node(owner_id="owner_default", device_id="device-http-status-0001")
        status, revoked = self._post(
            "/v1/nodes/device-http-status-0001/enrollment-status",
            {},
            f"Node {node_secret}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(revoked["state"], "revoked")

    def test_node_authority_status_is_node_authenticated_and_path_free(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-http-authority-0001",
            endpoint_id="endpoint-http-authority-0001",
            display_name="HTTP authority node",
        )
        registration = self.server.store.register_node_workspace(
            device_id=node["device_id"],
            workspace_id="workspace-http-authority-0001",
            workspace_generation="generation-http-authority-0001",
            display_name="HTTP authority workspace",
            capabilities={"read": True, "write": False, "exec": False},
        )
        self.server.store.create_binding(
            owner_id="owner_default",
            device_id=node["device_id"],
            workspace_id=registration["workspace_id"],
            workspace_generation=registration["workspace_generation"],
            display_name=registration["display_name"],
        )
        status, projection = self._post(
            f"/v1/nodes/{node['device_id']}/authority-status",
            {},
            f"Node {node['node_secret']}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(projection["state"], "active")
        self.assertEqual(projection["dispatchable_target_count"], 1)
        self.assertEqual(projection["targets"][0]["workspace_id"], "workspace-http-authority-0001")
        self.assertEqual(projection["targets"][0]["workspace_generation"], "generation-http-authority-0001")
        serialized = json.dumps(projection)
        self.assertNotIn("owner_id", serialized)
        self.assertNotIn("binding_id", serialized)
        self.assertNotIn("path", serialized)

        status, forbidden = self._post(
            f"/v1/nodes/{node['device_id']}/authority-status",
            {},
            "Node wrong-authority-secret-0001",
        )
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")
        status, invalid = self._post(
            f"/v1/nodes/{node['device_id']}/authority-status",
            {"unexpected": True},
            f"Node {node['node_secret']}",
        )
        self.assertEqual(status, 400)
        self.assertEqual(invalid["error"]["code"], "VALIDATION_ERROR")

    def test_node_workspace_retirement_requires_node_auth_and_closes_exact_context(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-http-retire-0001",
            endpoint_id="endpoint-http-retire-0001",
            display_name="HTTP retire node",
        )
        registration_payload = {
            "workspace_id": "workspace-http-retire-0001",
            "workspace_generation": "generation-http-retire-0001",
            "display_name": "HTTP retire workspace",
            "capabilities": {"read": True, "write": False, "exec": False},
        }
        status, registration = self._post(
            "/v1/nodes/device-http-retire-0001/workspace-registrations",
            registration_payload,
            f"Node {node['node_secret']}",
        )
        self.assertEqual(status, 201)
        binding = self.server.store.create_binding(
            owner_id="owner_default",
            device_id=node["device_id"],
            workspace_id=registration_payload["workspace_id"],
            workspace_generation=registration_payload["workspace_generation"],
            display_name=registration_payload["display_name"],
        )
        context = self.server.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.server.store.clock() + 60_000,
        )
        retirement_payload = {
            "workspace_id": registration_payload["workspace_id"],
            "workspace_generation": registration_payload["workspace_generation"],
        }
        status, forbidden = self._post(
            "/v1/nodes/device-http-retire-0001/workspace-registrations/retire",
            retirement_payload,
        )
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")
        status, retired = self._post(
            "/v1/nodes/device-http-retire-0001/workspace-registrations/retire",
            retirement_payload,
            f"Node {node['node_secret']}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(retired["workspace_id"], registration["workspace_id"])
        self.assertIsInstance(retired["retired_at_ms"], int)
        self.assertFalse(retired["replayed"])
        self.assertNotIn("path", json.dumps(retired))
        closed = self.server.store.context(owner_id="owner_default", context_id=context["context_id"])
        self.assertIsNotNone(closed["closed_at_ms"])
        status, replayed = self._post(
            "/v1/nodes/device-http-retire-0001/workspace-registrations/retire",
            retirement_payload,
            f"Node {node['node_secret']}",
        )
        self.assertEqual(status, 200)
        self.assertTrue(replayed["replayed"])

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

    def test_browser_ui_decides_opaque_oauth_link_requests_with_csrf(self) -> None:
        issuer = "https://identity.example.test/tenant-browser"
        alice_subject = "alice-browser@example.test"
        bob_subject = "bob-browser@example.test"
        alice = self.server.store.resolve_or_request_oauth_principal(
            owner_id="owner_default",
            issuer=issuer,
            subject=alice_subject,
        )["link_request"]
        bob = self.server.store.resolve_or_request_oauth_principal(
            owner_id="owner_default",
            issuer=issuer,
            subject=bob_subject,
        )["link_request"]
        cookie, csrf_token = self._ui_login()

        status, overview, _headers = self._request_with_headers(
            "/v1/ui/overview",
            method="GET",
            headers={"Cookie": cookie},
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            {item["link_request_id"] for item in overview["oauth_link_requests"]},
            {alice["link_request_id"], bob["link_request_id"]},
        )
        overview_text = json.dumps(overview)
        self.assertNotIn(issuer, overview_text)
        self.assertNotIn(alice_subject, overview_text)
        self.assertNotIn(bob_subject, overview_text)

        status, forbidden, _headers = self._request_with_headers(
            f"/v1/ui/oauth-link-requests/{alice['link_request_id']}/approve",
            method="POST",
            payload={},
            headers={"Cookie": cookie, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")

        headers = {"Cookie": cookie, "Origin": self.web_origin, CSRF_HEADER_NAME: csrf_token}
        status, approved, _headers = self._request_with_headers(
            f"/v1/ui/oauth-link-requests/{alice['link_request_id']}/approve",
            method="POST",
            payload={},
            headers=headers,
        )
        self.assertEqual(status, 200)
        self.assertEqual(approved["link_request"]["state"], "approved")
        self.assertEqual(approved["principal"]["state"], "enabled")
        self.assertEqual(
            self.server.store.resolve_oauth_principal(issuer=issuer, subject=alice_subject),
            {"principal_id": approved["principal"]["principal_id"], "owner_id": "owner_default"},
        )

        status, rejected, _headers = self._request_with_headers(
            f"/v1/ui/oauth-link-requests/{bob['link_request_id']}/reject",
            method="POST",
            payload={},
            headers=headers,
        )
        self.assertEqual(status, 200)
        self.assertEqual(rejected["state"], "rejected")
        self.assertIsNone(rejected["principal_id"])
        self.assertNotIn(issuer, json.dumps(rejected))
        status, after, _headers = self._request_with_headers(
            "/v1/ui/overview",
            method="GET",
            headers={"Cookie": cookie},
        )
        self.assertEqual(status, 200)
        principal = after["oauth_principals"][0]
        self.assertEqual(principal["principal_id"], approved["principal"]["principal_id"])
        self.assertEqual(principal["state"], "enabled")
        status, forbidden_revoke, _headers = self._request_with_headers(
            f"/v1/ui/oauth-principals/{principal['principal_id']}/revoke",
            method="POST",
            payload={},
            headers={"Cookie": cookie, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 403)
        self.assertEqual(forbidden_revoke["error"]["code"], "FORBIDDEN")
        status, revoked, _headers = self._request_with_headers(
            f"/v1/ui/oauth-principals/{principal['principal_id']}/revoke",
            method="POST",
            payload={},
            headers=headers,
        )
        self.assertEqual(status, 200)
        self.assertEqual(revoked["state"], "revoked")
        with self.assertRaises(PermissionError):
            self.server.store.resolve_oauth_principal(issuer=issuer, subject=alice_subject)
        self.assertIn("oauth-link-requests", WEB_UI_JAVASCRIPT.decode("utf-8"))
        self.assertIn("oauth-principals", WEB_UI_JAVASCRIPT.decode("utf-8"))
        self.assertIn("Liên kết tài khoản OAuth", WEB_UI_HTML.decode("utf-8"))

    def test_browser_ui_decides_patch_permission_request_with_origin_and_csrf(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-browser-permission-0001",
            endpoint_id="endpoint-browser-permission-0001",
            display_name="Browser permission node",
        )
        self.server.store.register_node_workspace(
            device_id=node["device_id"],
            workspace_id="workspace-browser-permission-0001",
            workspace_generation="generation-browser-permission-0001",
            display_name="Browser permission workspace",
            capabilities={"read": True, "write": True, "exec": False},
        )
        binding = self.server.store.create_binding(
            owner_id="owner_default",
            device_id=node["device_id"],
            workspace_id="workspace-browser-permission-0001",
            workspace_generation="generation-browser-permission-0001",
            display_name="Browser permission workspace",
        )
        principal = self.server.store.link_oauth_principal(
            owner_id="owner_default",
            issuer="https://identity.example.test/tenant-browser-permission",
            subject="browser-permission-subject",
        )
        request = self.server.store.request_mcp_patch_permission(
            owner_id="owner_default",
            principal_id=principal["principal_id"],
            binding_id=binding["binding_id"],
            path="src/fixture.txt",
            preimage_sha256="a" * 64,
            patch_sha256="b" * 64,
            validation_profile="targeted",
            idempotency_key="browser-permission-request-key-0001",
            facade_contract={
                key: self.server.mcp_facade.contract[key]
                for key in ("schema_version", "profile", "sha256")
            },
        )
        cookie, csrf_token = self._ui_login()

        status, overview, _headers = self._request_with_headers(
            "/v1/ui/overview",
            method="GET",
            headers={"Cookie": cookie},
        )
        self.assertEqual(status, 200)
        self.assertEqual(overview["permission_requests"][0]["permission_request_id"], request["permission_request_id"])
        self.assertEqual(overview["permission_requests"][0]["path"], "src/fixture.txt")
        self.assertNotIn("action_id", json.dumps(overview["permission_requests"][0]))

        url = f"/v1/ui/permission-requests/{request['permission_request_id']}/approve"
        status, forbidden, _headers = self._request_with_headers(
            url,
            method="POST",
            payload={},
            headers={"Cookie": cookie, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")
        self.assertEqual(self.server.store.list_mcp_permission_requests(owner_id="owner_default")[0]["state"], "pending")

        status, approved, _headers = self._request_with_headers(
            url,
            method="POST",
            payload={},
            headers={"Cookie": cookie, "Origin": self.web_origin, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 200)
        self.assertEqual(approved["state"], "approved")
        self.assertEqual(self.server.store.health()["counts"]["actions"], 0)
        self.assertIn("permission-requests", WEB_UI_JAVASCRIPT.decode("utf-8"))
        self.assertIn("Yêu cầu quyền patch", WEB_UI_HTML.decode("utf-8"))

    def test_browser_operator_can_create_and_revoke_bounded_binding_context_with_csrf(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-browser-binding-0001",
            endpoint_id="endpoint-browser-binding-0001",
            display_name="Browser binding node",
        )
        registration_payload = {
            "workspace_id": "workspace-browser-binding-0001",
            "workspace_generation": "generation-browser-binding-0001",
            "display_name": "Browser binding workspace",
            "capabilities": {"read": True, "write": False, "exec": False},
        }
        status, unauthenticated_registration = self._post(
            f"/v1/nodes/{node['device_id']}/workspace-registrations",
            registration_payload,
        )
        self.assertEqual(status, 403)
        self.assertEqual(unauthenticated_registration["error"]["code"], "FORBIDDEN")
        status, registration = self._post(
            f"/v1/nodes/{node['device_id']}/workspace-registrations",
            registration_payload,
            f"Node {node['node_secret']}",
        )
        self.assertEqual(status, 201)
        self.assertEqual(registration["workspace_id"], registration_payload["workspace_id"])
        self.assertEqual(registration["capabilities"], registration_payload["capabilities"])
        self.assertNotIn("path", json.dumps(registration))
        status, registrations = self._get(
            f"/v1/nodes/{node['device_id']}/workspace-registrations",
            f"Bearer {self.operator_token}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(registrations["workspace_registrations"], [{
            **{key: registration[key] for key in (
                "device_id", "workspace_id", "workspace_generation", "display_name", "capabilities",
                "registered_at_ms", "retired_at_ms",
            )},
        }])
        self.assertNotIn(node["node_secret"], json.dumps(registrations))
        cookie, csrf_token = self._ui_login()
        payload = {
            "device_id": node["device_id"],
            "workspace_id": "workspace-browser-binding-0001",
            "workspace_generation": "generation-browser-binding-0001",
            "display_name": "Browser binding workspace",
        }
        status, forbidden, _headers = self._request_with_headers(
            "/v1/ui/bindings",
            method="POST",
            payload=payload,
            headers={"Cookie": cookie, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")
        self.assertEqual(self.server.store.health()["counts"]["bindings"], 0)

        status, binding, _headers = self._request_with_headers(
            "/v1/ui/bindings",
            method="POST",
            payload=payload,
            headers={"Cookie": cookie, "Origin": self.web_origin, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 201)
        self.assertEqual(binding["device_id"], node["device_id"])
        self.assertNotIn("credential", json.dumps(binding))

        status, invalid_context, _headers = self._request_with_headers(
            "/v1/ui/contexts",
            method="POST",
            payload={"binding_id": binding["binding_id"], "duration_minutes": 2},
            headers={"Cookie": cookie, "Origin": self.web_origin, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 400)
        self.assertEqual(invalid_context["error"]["code"], "VALIDATION_ERROR")

        before_context = self.server.store.clock()
        status, context, _headers = self._request_with_headers(
            "/v1/ui/contexts",
            method="POST",
            payload={"binding_id": binding["binding_id"], "duration_minutes": 15},
            headers={"Cookie": cookie, "Origin": self.web_origin, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 201)
        self.assertGreaterEqual(context["expires_at_ms"], before_context + 15 * 60 * 1000)
        self.assertLessEqual(context["expires_at_ms"], self.server.store.clock() + 15 * 60 * 1000)

        status, closed, _headers = self._request_with_headers(
            f"/v1/ui/contexts/{context['context_id']}/close",
            method="POST",
            payload={},
            headers={"Cookie": cookie, "Origin": self.web_origin, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 200)
        self.assertIsNotNone(closed["closed_at_ms"])

        status, revoked, _headers = self._request_with_headers(
            f"/v1/ui/bindings/{binding['binding_id']}/revoke",
            method="POST",
            payload={},
            headers={"Cookie": cookie, "Origin": self.web_origin, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 200)
        self.assertIsNotNone(revoked["revoked_at_ms"])

        self.assertIn("/v1/ui/bindings", WEB_UI_JAVASCRIPT.decode("utf-8"))
        self.assertIn("duration_minutes", WEB_UI_JAVASCRIPT.decode("utf-8"))
        self.assertIn("Thu hồi binding", WEB_UI_JAVASCRIPT.decode("utf-8"))

    def test_historical_unknown_quarantine_requires_operator_authentication_and_preserves_receipt(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-http-quarantine-0001",
            endpoint_id="endpoint-http-quarantine-0001",
            display_name="HTTP quarantine node",
        )
        binding = self._registered_binding(
            owner_id="owner_default",
            device_id=node["device_id"],
            workspace_id="workspace-http-quarantine-0001",
            workspace_generation="generation-http-quarantine-0001",
            display_name="HTTP quarantine workspace",
        )
        context = self.server.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.server.store.clock() + 60_000,
        )
        request = self.server.store.create_work_request(
            owner_id="owner_default",
            context_id=context["context_id"],
            objective="Historical read-only uncertainty fixture",
            criteria={"kind": "read_only"},
            scope={"kind": "fixture"},
            expires_at_ms=self.server.store.clock() + 30_000,
        )
        action = self.server.store.seal_action(
            owner_id="owner_default",
            request_id=request["request_id"],
            tool_name="workspace_context",
            arguments={"mode": "status"},
            idempotency_key="http-quarantine-action-key-0001",
            admission_reference="http-quarantine-admission-0001",
            expires_at_ms=self.server.store.clock() + 20_000,
        )
        self.server.store.heartbeat(
            device_id=node["device_id"],
            endpoint_id="endpoint-http-quarantine-0001",
            runtime_instance_id="runtime-http-quarantine-0001",
            mcp_server_instance_id="server-http-quarantine-0001",
            activation_epoch="epoch-http-quarantine-0001",
            contract_version="smart-v3",
            readiness="ready",
        )
        attempt = self.server.store.poll_actions(device_id=node["device_id"])[0]["attempt_id"]
        self.server.store.record_receipt(
            device_id=node["device_id"],
            action_id=action["action_id"],
            attempt_id=attempt,
            receipt_state="unknown",
            local_handle="",
            payload={"reason": "fixture_unknown"},
        )
        payload = {
            "device_id": node["device_id"],
            "action_ids": [action["action_id"]],
            "declaration": "HISTORICAL_READ_ONLY_UNKNOWN_EFFECT",
        }
        path = "/v1/action-reconciliations/quarantine-historical-unknown"
        status, forbidden = self._post(path, payload)
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")

        cookie, csrf_token = self._ui_login()
        ui_path = "/v1/ui/action-reconciliations/quarantine-historical-unknown"
        status, csrf_rejected, _headers = self._request_with_headers(
            ui_path,
            method="POST",
            payload=payload,
            headers={"Cookie": cookie, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 403)
        self.assertEqual(csrf_rejected["error"]["code"], "FORBIDDEN")

        status, quarantined, _headers = self._request_with_headers(
            ui_path,
            method="POST",
            payload=payload,
            headers={"Cookie": cookie, "Origin": self.web_origin, CSRF_HEADER_NAME: csrf_token},
        )
        self.assertEqual(status, 200)
        self.assertEqual(quarantined["actions"][0]["action_id"], action["action_id"])
        self.assertNotIn("receipt_digest", json.dumps(quarantined))
        observation = self.server.store.action_observation(owner_id="owner_default", action_id=action["action_id"])
        self.assertEqual(observation["delivery_state"], "reconcile_required")
        self.assertEqual(observation["receipts"][-1]["receipt_state"], "unknown")
        self.assertEqual(observation["reconciliation"]["disposition"], "quarantined_unknown")
        self.assertIn("quarantine-historical-unknown", WEB_UI_JAVASCRIPT.decode("utf-8"))
        self.assertIn("HISTORICAL_READ_ONLY_UNKNOWN_EFFECT", WEB_UI_HTML.decode("utf-8"))

    def test_historical_unobserved_dispatch_route_requires_operator_and_preserves_no_receipt(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-http-unobserved-0001",
            endpoint_id="endpoint-http-unobserved-0001",
            display_name="HTTP unobserved node",
        )
        binding = self._registered_binding(
            owner_id="owner_default",
            device_id=node["device_id"],
            workspace_id="workspace-http-unobserved-0001",
            workspace_generation="generation-http-unobserved-0001",
            display_name="HTTP unobserved workspace",
        )
        context = self.server.store.create_context(
            owner_id="owner_default", binding_id=binding["binding_id"], expires_at_ms=self.server.store.clock() + 60_000
        )
        request = self.server.store.create_work_request(
            owner_id="owner_default",
            context_id=context["context_id"],
            objective="Historical unobserved dispatch fixture",
            criteria={"kind": "read_only"},
            scope={"kind": "fixture"},
            expires_at_ms=self.server.store.clock() + 30_000,
        )
        action = self.server.store.seal_action(
            owner_id="owner_default",
            request_id=request["request_id"],
            tool_name="workspace_context",
            arguments={"mode": "status"},
            idempotency_key="http-unobserved-action-key-0001",
            admission_reference="http-unobserved-admission-0001",
            expires_at_ms=self.server.store.clock() + 20_000,
        )
        self.server.store.heartbeat(
            device_id=node["device_id"],
            endpoint_id="endpoint-http-unobserved-0001",
            runtime_instance_id="runtime-http-unobserved-0001",
            mcp_server_instance_id="server-http-unobserved-0001",
            activation_epoch="epoch-http-unobserved-0001",
            contract_version="smart-v3",
            readiness="ready",
        )
        self.server.store.poll_actions(device_id=node["device_id"])
        self.server.store.clock = lambda: action["expires_at_ms"] + 1
        payload = {
            "device_id": node["device_id"],
            "action_ids": [action["action_id"]],
            "declaration": "HISTORICAL_READ_ONLY_UNOBSERVED_DISPATCH",
            "rationale": "legacy read-only dispatch expired without node evidence",
        }
        path = "/v1/action-dispositions/quarantine-historical-unobserved-dispatch"
        status, forbidden = self._post(path, payload)
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")
        status, result = self._post(path, payload, authorization=f"Bearer {self.operator_token}")
        self.assertEqual(status, 200)
        self.assertEqual(result["actions"][0]["action_id"], action["action_id"])
        observation = self.server.store.action_observation(owner_id="owner_default", action_id=action["action_id"])
        self.assertEqual(observation["delivery_state"], "dispatch_unconfirmed")
        self.assertEqual(observation["receipts"], [])
        self.assertEqual(observation["dispatch_disposition"]["declaration"], "HISTORICAL_READ_ONLY_UNOBSERVED_DISPATCH")
        self.assertIn("HISTORICAL_READ_ONLY_UNOBSERVED_DISPATCH", WEB_UI_HTML.decode("utf-8"))

    def test_node_policy_template_is_bound_to_its_live_context_and_node_credential(self) -> None:
        first = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-policy-template-0001",
            endpoint_id="endpoint-policy-template-0001",
            display_name="Policy template node",
        )
        second = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-policy-template-0002",
            endpoint_id="endpoint-policy-template-0002",
            display_name="Other policy template node",
        )
        binding = self._registered_binding(
            owner_id="owner_default",
            device_id=first["device_id"],
            workspace_id="workspace-policy-template-0001",
            workspace_generation="generation-policy-template-0001",
            display_name="Policy template workspace",
        )
        context = self.server.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.server.store.clock() + 60_000,
        )
        path = f"/v1/nodes/{first['device_id']}/read-only-policy-template"
        status, template = self._post(path, {"context_id": context["context_id"]}, f"Node {first['node_secret']}")
        self.assertEqual(status, 200)
        policy = template["policy_template"]
        self.assertEqual(policy["device_id"], first["device_id"])
        self.assertEqual(policy["endpoint_id"], "endpoint-policy-template-0001")
        self.assertEqual(policy["workspace_id"], binding["workspace_id"])
        self.assertNotIn("node_secret", json.dumps(template))
        self.assertNotIn("credential", json.dumps(template))

        status, forbidden = self._post(
            f"/v1/nodes/{second['device_id']}/read-only-policy-template",
            {"context_id": context["context_id"]},
            f"Node {second['node_secret']}",
        )
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")

        self.server.store.close_context(owner_id="owner_default", context_id=context["context_id"])
        status, closed = self._post(path, {"context_id": context["context_id"]}, f"Node {first['node_secret']}")
        self.assertEqual(status, 409)
        self.assertEqual(closed["error"]["code"], "CONFLICT")

    def test_node_can_fetch_only_one_live_policy_assignment_for_its_registered_root(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-policy-assignment-0001",
            endpoint_id="endpoint-policy-assignment-0001",
            display_name="Policy assignment node",
        )
        binding = self._registered_binding(
            owner_id="owner_default",
            device_id=node["device_id"],
            workspace_id="workspace-policy-assignment-0001",
            workspace_generation="generation-policy-assignment-0001",
            display_name="Policy assignment workspace",
        )
        path = f"/v1/nodes/{node['device_id']}/read-only-policy-assignment"
        request = {
            "workspace_id": binding["workspace_id"],
            "workspace_generation": binding["workspace_generation"],
        }

        status, missing = self._post(path, request, f"Node {node['node_secret']}")
        self.assertEqual(status, 404)
        self.assertEqual(missing["error"]["code"], "NOT_FOUND")

        context = self.server.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.server.store.clock() + 60_000,
        )
        status, assignment = self._post(path, request, f"Node {node['node_secret']}")
        self.assertEqual(status, 200)
        template = assignment["policy_template"]
        self.assertEqual(template["workspace_id"], request["workspace_id"])
        self.assertEqual(template["workspace_generation"], request["workspace_generation"])
        self.assertNotIn("context_id", json.dumps(assignment))
        self.assertNotIn("node_secret", json.dumps(assignment))

        duplicate = self.server.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.server.store.clock() + 60_000,
        )
        status, ambiguous = self._post(path, request, f"Node {node['node_secret']}")
        self.assertEqual(status, 409)
        self.assertEqual(ambiguous["error"]["code"], "CONFLICT")

        self.server.store.close_context(owner_id="owner_default", context_id=duplicate["context_id"])
        status, restored = self._post(path, request, f"Node {node['node_secret']}")
        self.assertEqual(status, 200)
        self.assertEqual(restored["policy_template"]["owner_id"], "owner_default")

        status, malformed = self._post(
            path,
            {**request, "unexpected": True},
            f"Node {node['node_secret']}",
        )
        self.assertEqual(status, 400)
        self.assertEqual(malformed["error"]["code"], "VALIDATION_ERROR")
        self.server.store.close_context(owner_id="owner_default", context_id=context["context_id"])

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
        self.assertEqual(health["schema_version"], SCHEMA_VERSION)
        self.assertEqual(health["mcp_authentication_mode"], "legacy_context_grant")
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

    def test_dedicated_loopback_mcp_ingress_exposes_no_ui_or_admin_route(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-mcp-ingress-001",
            endpoint_id="endpoint-mcp-ingress-001",
            display_name="MCP ingress fixture",
        )
        binding = self._registered_binding(
            owner_id="owner_default",
            device_id=node["device_id"],
            workspace_id="workspace-mcp-ingress-001",
            workspace_generation="generation-mcp-ingress-001",
            display_name="MCP ingress workspace",
        )
        context = self.server.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.server.store.clock() + 60_000,
        )
        grant = self.server.store.create_mcp_access_grant(
            owner_id="owner_default",
            context_id=context["context_id"],
            principal_id="openai-ubuntu-root-ingress-fixture",
            expires_at_ms=self.server.store.clock() + 30_000,
        )
        ingress = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.server.store,
            self.operator_token,
            "a" * 40,
            mcp_enabled=True,
            mcp_ingress_only=True,
        )
        ingress_thread = threading.Thread(target=ingress.serve_forever, daemon=True)
        ingress_thread.start()
        ingress_url = f"http://127.0.0.1:{ingress.server_port}"
        try:
            def request(path: str, *, method: str, payload: dict | None = None, authorization: str | None = None) -> tuple[int, dict]:
                headers = {"Content-Type": "application/json"} if payload is not None else {}
                if authorization:
                    headers["Authorization"] = authorization
                raw = json.dumps(payload).encode("utf-8") if payload is not None else None
                candidate = Request(f"{ingress_url}{path}", data=raw, headers=headers, method=method)
                try:
                    with urlopen(candidate, timeout=2) as response:
                        return response.status, json.loads(response.read())
                except HTTPError as error:
                    try:
                        return error.code, json.loads(error.read())
                    finally:
                        error.close()

            status, health = request("/healthz", method="GET")
            self.assertEqual(status, 404)
            self.assertEqual(health["error"]["code"], "NOT_FOUND")
            status, admin = request(
                "/v1/mcp-access-grants",
                method="POST",
                payload={},
                authorization=f"Bearer {self.operator_token}",
            )
            self.assertEqual(status, 404)
            self.assertEqual(admin["error"]["code"], "NOT_FOUND")
            status, initialized = request(
                "/mcp",
                method="POST",
                payload={"jsonrpc": "2.0", "id": "ingress-init-001", "method": "initialize", "params": {}},
                authorization=f"Bearer {grant['access_token']}",
            )
            self.assertEqual(status, 200)
            self.assertEqual(initialized["result"]["_meta"]["control_plane"]["access_scope"], "server_issued_context_grant")
        finally:
            ingress.shutdown()
            ingress.server_close()
            ingress_thread.join(timeout=2)

        primary_without_mcp = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.server.store,
            self.operator_token,
            "a" * 40,
            mcp_enabled=False,
        )
        primary_thread = threading.Thread(target=primary_without_mcp.serve_forever, daemon=True)
        primary_thread.start()
        try:
            request = Request(
                f"http://127.0.0.1:{primary_without_mcp.server_port}/mcp",
                data=json.dumps({"jsonrpc": "2.0", "id": "disabled-primary-001", "method": "initialize", "params": {}}).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {grant['access_token']}"},
                method="POST",
            )
            with self.assertRaises(HTTPError) as rejected:
                urlopen(request, timeout=2)
            self.assertEqual(rejected.exception.code, 404)
            rejected.exception.close()
        finally:
            primary_without_mcp.shutdown()
            primary_without_mcp.server_close()
            primary_thread.join(timeout=2)

    def test_mcp_ingress_environment_is_loopback_and_range_limited(self) -> None:
        with mock.patch.dict("os.environ", {"CONTROL_PLANE_MCP_BIND": "127.0.0.1", "CONTROL_PLANE_MCP_PORT": "8766"}, clear=True):
            self.assertEqual(_mcp_ingress_address_from_environment(), ("127.0.0.1", 8766))
        for environment in (
            {"CONTROL_PLANE_MCP_BIND": "100.116.112.22", "CONTROL_PLANE_MCP_PORT": "8766"},
            {"CONTROL_PLANE_MCP_BIND": "127.0.0.1", "CONTROL_PLANE_MCP_PORT": "0"},
            {"CONTROL_PLANE_MCP_BIND": "127.0.0.1", "CONTROL_PLANE_MCP_PORT": "not-a-port"},
        ):
            with mock.patch.dict("os.environ", environment, clear=True), self.assertRaises(ValueError):
                _mcp_ingress_address_from_environment()

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
            self.assertIn("function nodeReadiness", javascript)
            self.assertIn("không coi executor sẵn sàng", javascript)
            self.assertIn("không cấp quyền task", javascript)
        self.assertIn("binding-workspace-registration", javascript)
        self.assertIn("workspace-registrations-body", javascript)
        self.assertIn("mcp-authentication-mode", javascript)
        self.assertNotIn("binding-workspace-id", javascript)
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
        self.assertIn("effect đã áp — chờ proof/semantic acceptance local".encode("utf-8"), WEB_UI_JAVASCRIPT)
        self.assertIn("patch có thể đã áp tại Windows; phải đối soát local, không retry".encode("utf-8"), WEB_UI_JAVASCRIPT)
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
        binding = self._registered_binding(
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
        self.assertEqual(len(overview["workspace_registrations"]), 1)
        registration = overview["workspace_registrations"][0]
        self.assertEqual({key: registration[key] for key in (
            "device_id", "workspace_id", "workspace_generation", "display_name", "capabilities", "retired_at_ms",
        )}, {
            "device_id": node["device_id"],
            "workspace_id": "workspace-web-ui-0001",
            "workspace_generation": "generation-web-ui-0001",
            "display_name": "Web UI workspace",
            "capabilities": {"read": True, "write": False, "exec": False},
            "retired_at_ms": None,
        })
        self.assertIsInstance(registration["registered_at_ms"], int)
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
        self.assertNotIn(node["node_secret"], overview_text)

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
        binding = self._registered_binding(
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
        binding = self._registered_binding(
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
                "workspace_summary": {
                    "schema_version": 1,
                    "project": {"type": "node", "name": "office-fixture", "version": "1.0.0"},
                    "entries": [{"name": "office-marker.txt", "type": "file", "size_bytes": 17, "is_hidden": False, "is_ignored": False}],
                    "entries_truncated": False,
                    "git": {"is_repo": True, "branch": "main", "changed_count": 0, "truncated": False},
                },
                "workspace_summary_sha256": "e" * 64,
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

    def test_operator_login_rejects_non_ascii_wrong_type_and_invalid_length_without_internal_error(self) -> None:
        # Login throttling is covered independently above. Reset the
        # in-memory fixture between malformed credential shapes so this test
        # proves all validation branches instead of treating its own earlier
        # failures as a rate-limit result.
        invalid_values = (
            "",
            "x" * 513,
            "đ" * 32,
            ["x" * 40],
            {"token": "x" * 40},
            None,
        )
        for value in invalid_values:
            with self.subTest(value_type=type(value).__name__):
                status, response, _headers = self._request_with_headers(
                    "/v1/ui/login",
                    method="POST",
                    payload={"operator_token": value},
                    headers={"Origin": self.web_origin},
                )
                self.assertEqual(status, 403)
                self.assertEqual(response["error"]["code"], "FORBIDDEN")
                self.assertEqual(response["error"]["message"], "operator authentication failed.")
                self.assertNotIn("đ", json.dumps(response, ensure_ascii=False))
                assert self.server.operator_sessions is not None
                self.server.operator_sessions._login_attempts.clear()

    def test_server_refuses_non_ascii_operator_token_at_startup(self) -> None:
        with self.assertRaisesRegex(ValueError, "printable ASCII"):
            ControlPlaneHttpServer(
                ("127.0.0.1", 0),
                ControlPlaneStore(Path(self.tempdir.name) / "unicode-operator.sqlite3"),
                "đ" * 32,
            )

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
        binding = self._registered_binding(
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
        grant = self.server.store.create_mcp_access_grant(
            owner_id="owner_default",
            context_id=context["context_id"],
            principal_id="openai-tunnel-commit-failure-fixture",
            expires_at_ms=self.server.store.clock() + 30_000,
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
            status, response = self._post("/mcp", request, f"Bearer {grant['access_token']}")

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

    def _mcp_wire_grant(self) -> dict:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-mcp-wire-001",
            endpoint_id="endpoint-mcp-wire-001",
            display_name="MCP wire fixture",
        )
        binding = self._registered_binding(
            owner_id="owner_default",
            device_id=node["device_id"],
            workspace_id="workspace-mcp-wire-001",
            workspace_generation="generation-mcp-wire-001",
            display_name="MCP wire workspace",
        )
        context = self.server.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.server.store.clock() + 60_000,
        )
        return self.server.store.create_mcp_access_grant(
            owner_id="owner_default",
            context_id=context["context_id"],
            principal_id="mcp-wire-fixture",
            expires_at_ms=self.server.store.clock() + 30_000,
        )

    def test_mcp_initialize_negotiates_only_supported_tool_protocol_versions(self) -> None:
        grant = self._mcp_wire_grant()
        self.server.store.set_admission_mode(mode="recovery")
        for offered, negotiated in (
            ("2025-11-25", "2025-11-25"),
            ("2025-06-18", "2025-06-18"),
            ("2025-03-26", "2025-11-25"),
            ("2026-07-28", "2025-11-25"),
            ("2024-11-05", "2025-11-25"),
            ("2099-01-01", "2025-11-25"),
        ):
            with self.subTest(offered=offered):
                status, response = self._post(
                    "/mcp",
                    {"jsonrpc": "2.0", "id": "wire-init", "method": "initialize", "params": {"protocolVersion": offered}},
                    f"Bearer {grant['access_token']}",
                )
                self.assertEqual(status, 200)
                self.assertEqual(response["result"]["protocolVersion"], negotiated)
                self.assertEqual(response["result"]["capabilities"], {"tools": {"listChanged": False}})
        for invalid in (None, True, 1, [], ""):
            with self.subTest(invalid=invalid):
                status, response = self._post(
                    "/mcp",
                    {"jsonrpc": "2.0", "id": "wire-invalid-init", "method": "initialize", "params": {"protocolVersion": invalid}},
                    f"Bearer {grant['access_token']}",
                )
                self.assertEqual(status, 200)
                self.assertEqual(response["error"]["code"], -32602)
        self.assertEqual(self.server.store.admission_status()["admission_mode"], "recovery")

    def test_mcp_notifications_are_authenticated_empty_responses_without_tool_effects(self) -> None:
        grant = self._mcp_wire_grant()
        authorization = f"Bearer {grant['access_token']}"
        initialized = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        for denied_authorization in (None, f"Bearer {self.operator_token}"):
            with self.subTest(denied_authorization=bool(denied_authorization)):
                status, rejected = self._post("/mcp", initialized, denied_authorization)
                self.assertEqual(status, 403)
                self.assertEqual(rejected["error"]["code"], "FORBIDDEN")

        for notification in (
            initialized,
            {**initialized, "params": {"_meta": {"fixture": True}}},
            {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": "unrelated-request"}},
            {"jsonrpc": "2.0", "method": "notifications/unknown", "params": {}},
        ):
            with self.subTest(method=notification["method"]):
                request = Request(
                    f"{self.base_url}/mcp",
                    data=json.dumps(notification).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                        "MCP-Protocol-Version": "2025-11-25",
                        "Authorization": authorization,
                    },
                    method="POST",
                )
                with urlopen(request, timeout=2) as response:
                    self.assertEqual(response.status, 202)
                    self.assertEqual(response.read(), b"")
                    self.assertEqual(response.headers["Content-Length"], "0")
                    self.assertNotIn("Mcp-Session-Id", response.headers)

        missing_id_call = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "workspace_context",
                "arguments": {
                    "context_id": grant["context_id"],
                    "operation": "request_read_only",
                    "idempotency_key": "wire-notification-must-not-enqueue",
                    "expires_at_ms": self.server.store.clock() + 20_000,
                    "expected_facade_contract": {
                        key: self.server.mcp_facade.contract[key]
                        for key in ("schema_version", "profile", "sha256")
                    },
                },
            },
        }
        for invalid in (
            missing_id_call,
            {**initialized, "jsonrpc": "invalid"},
            {**initialized, "params": []},
            {**initialized, "params": None},
            {**initialized, "method": "notifications/"},
        ):
            with self.subTest(invalid=invalid.get("method")):
                status, rejected = self._post("/mcp", invalid, authorization)
                self.assertEqual(status, 400)
                self.assertEqual(rejected["error"]["code"], "VALIDATION_ERROR")
        status, rejected = self._post("/mcp", {**missing_id_call, "id": None}, authorization)
        self.assertEqual(status, 200)
        self.assertEqual(rejected["error"]["code"], -32600)
        counts = self.server.store.health()["counts"]
        for collection in ("mcp_read_only_intents", "work_requests", "actions"):
            self.assertEqual(counts[collection], 0, "notifications must never queue a tool action")

    @staticmethod
    def _modern_mcp_body(method: str, params: dict | None = None) -> dict:
        return {
            "jsonrpc": "2.0", "id": "modern-fixture-001", "method": method,
            "params": {
                **(params or {}),
                "_meta": {
                    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
                    "io.modelcontextprotocol/clientCapabilities": {},
                    "io.modelcontextprotocol/clientInfo": {"name": "modern-fixture", "version": "1.0"},
                },
            },
        }

    def _modern_mcp_post(
        self, grant: dict, body: dict, header_overrides: dict[str, str | None] | None = None,
    ) -> tuple[int, dict, dict[str, str]]:
        headers = {
            "Authorization": f"Bearer {grant['access_token']}",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": "2026-07-28",
            "Mcp-Method": body["method"],
        }
        if body["method"] == "tools/call":
            headers["Mcp-Name"] = body["params"]["name"]
        for key, value in (header_overrides or {}).items():
            if value is None:
                headers.pop(key, None)
            else:
                headers[key] = value
        return self._request_with_headers("/mcp", method="POST", payload=body, headers=headers)

    def test_modern_mcp_discovery_list_and_status_need_no_initialize_or_session(self) -> None:
        grant = self._mcp_wire_grant()
        self.server.store.set_admission_mode(mode="recovery")
        contract_before = json.dumps(self.server.mcp_facade.contract, sort_keys=True)
        status, discovered, headers = self._modern_mcp_post(grant, self._modern_mcp_body("server/discover"))
        self.assertEqual(status, 200)
        self.assertNotIn("Mcp-Session-Id", headers)
        discovery = discovered["result"]
        self.assertEqual(discovery["supportedVersions"], ["2026-07-28", "2025-11-25", "2025-06-18"])
        self.assertEqual(discovery["capabilities"], {"tools": {"listChanged": False}})
        self.assertEqual(discovery["resultType"], "complete")
        self.assertEqual(discovery["ttlMs"], 0)
        self.assertEqual(discovery["cacheScope"], "private")
        self.assertNotIn("protocolVersion", discovery)
        self.assertNotIn("serverInfo", discovery)
        server_info = {"name": "coding-tools-control-plane", "version": "0.1.0"}
        self.assertEqual(discovery["_meta"]["io.modelcontextprotocol/serverInfo"], server_info)

        listed_body = self._modern_mcp_body("tools/list")
        # Identity is advisory and optional; client capabilities remain required.
        listed_body["params"]["_meta"].pop("io.modelcontextprotocol/clientInfo")
        status, listed, headers = self._modern_mcp_post(grant, listed_body, {"Mcp-Session-Id": "untrusted-ignored"})
        self.assertEqual(status, 200)
        self.assertNotIn("Mcp-Session-Id", headers)
        self.assertEqual(listed["result"]["tools"], self.server.mcp_facade.contract["tools"])
        self.assertEqual(len(listed["result"]["tools"]), 8)
        self.assertEqual(listed["result"]["resultType"], "complete")
        self.assertEqual(listed["result"]["ttlMs"], 0)
        self.assertEqual(listed["result"]["cacheScope"], "private")
        self.assertEqual(listed["result"]["_meta"]["control_plane"], discovery["_meta"]["control_plane"])

        call = self._modern_mcp_body("tools/call", {
            "name": "workspace_context", "arguments": {"context_id": grant["context_id"], "operation": "status"},
        })
        status, observed, _ = self._modern_mcp_post(grant, call)
        self.assertEqual(status, 200)
        self.assertEqual(observed["result"]["resultType"], "complete")
        self.assertNotIn("ttlMs", observed["result"])
        self.assertEqual(observed["result"]["_meta"]["io.modelcontextprotocol/serverInfo"], server_info)
        self.assertFalse(observed["result"]["structuredContent"]["workspace_accessed"])
        self.assertEqual(observed["result"]["structuredContent"]["context"]["context_id"], grant["context_id"])
        self.assertEqual(json.dumps(self.server.mcp_facade.contract, sort_keys=True), contract_before)
        self.assertEqual(self.server.store.admission_status()["admission_mode"], "recovery")
        for collection in ("mcp_read_only_intents", "work_requests", "actions"):
            self.assertEqual(self.server.store.health()["counts"][collection], 0)

    def test_modern_mcp_headers_fail_closed_before_tool_dispatch(self) -> None:
        grant = self._mcp_wire_grant()
        call = self._modern_mcp_body("tools/call", {
            "name": "workspace_context", "arguments": {"context_id": grant["context_id"]},
        })
        for overrides in (
            {"MCP-Protocol-Version": None}, {"MCP-Protocol-Version": "2025-11-25"},
            {"Mcp-Method": None}, {"Mcp-Method": "tools/list"},
            {"Mcp-Name": None}, {"Mcp-Name": "exec_command"},
            {"Mcp-Name": "=?base64?invalid!?="},
        ):
            with self.subTest(headers=overrides):
                status, rejected, _ = self._modern_mcp_post(grant, call, overrides)
                self.assertEqual(status, 400)
                self.assertEqual(rejected["error"]["code"], -32020)
                self.assertEqual(rejected["id"], call["id"])
        status, accepted, _ = self._modern_mcp_post(grant, call, {"Mcp-Name": "=?base64?d29ya3NwYWNlX2NvbnRleHQ=?="})
        self.assertEqual(status, 200)
        self.assertFalse(accepted["result"]["structuredContent"]["workspace_accessed"])

        for body_change in ({}, {"_meta": {}}, {"_meta": None}):
            request = {**call, "params": {"name": "workspace_context", **body_change}}
            status, rejected, _ = self._modern_mcp_post(grant, request)
            self.assertEqual(status, 400)
            self.assertEqual(rejected["error"]["code"], -32020)

    def test_modern_mcp_metadata_is_required_on_every_request(self) -> None:
        grant = self._mcp_wire_grant()
        status, _, _ = self._modern_mcp_post(grant, self._modern_mcp_body("server/discover"))
        self.assertEqual(status, 200)
        for field, value in (
            ("io.modelcontextprotocol/clientCapabilities", None),
            ("io.modelcontextprotocol/clientCapabilities", []),
            ("io.modelcontextprotocol/clientInfo", None),
            ("io.modelcontextprotocol/clientInfo", {"name": "missing-version"}),
            ("io.modelcontextprotocol/clientInfo", {"name": 4, "version": "1"}),
        ):
            with self.subTest(field=field, value=value):
                request = self._modern_mcp_body("tools/list")
                request["params"]["_meta"][field] = value
                status, rejected, _ = self._modern_mcp_post(grant, request)
                self.assertEqual(status, 400)
                self.assertEqual(rejected["error"]["code"], -32602)
        request = self._modern_mcp_body("tools/list")
        request["params"]["_meta"].pop("io.modelcontextprotocol/clientCapabilities")
        status, rejected, _ = self._modern_mcp_post(grant, request)
        self.assertEqual(status, 400)
        self.assertEqual(rejected["error"]["code"], -32602)

    def test_modern_mcp_unsupported_versions_and_legacy_only_methods_are_explicit(self) -> None:
        grant = self._mcp_wire_grant()
        request = self._modern_mcp_body("server/discover")
        request["params"]["_meta"]["io.modelcontextprotocol/protocolVersion"] = "2099-01-01"
        status, rejected, _ = self._modern_mcp_post(grant, request, {"MCP-Protocol-Version": "2099-01-01"})
        self.assertEqual(status, 400)
        self.assertEqual(rejected["error"]["code"], -32022)
        self.assertEqual(rejected["error"]["data"], {
            "supported": ["2026-07-28", "2025-11-25", "2025-06-18"], "requested": "2099-01-01",
        })
        for method in ("initialize", "ping", "notifications/initialized", "unknown/method"):
            with self.subTest(method=method):
                status, rejected, _ = self._modern_mcp_post(grant, self._modern_mcp_body(method))
                self.assertEqual(status, 404)
                self.assertEqual(rejected["error"]["code"], -32601)

    def test_modern_mcp_preserves_auth_context_scope_and_unimplemented_tools(self) -> None:
        grant = self._mcp_wire_grant()
        request = self._modern_mcp_body("server/discover")
        for authorization in (None, f"Bearer {self.operator_token}"):
            status, rejected, _ = self._modern_mcp_post(grant, request, {"Authorization": authorization})
            self.assertEqual(status, 403)
            self.assertEqual(rejected["error"]["code"], "FORBIDDEN")
        status, rejected, _ = self._modern_mcp_post(grant, request, {"Origin": "https://untrusted.example"})
        self.assertEqual(status, 403)
        self.assertEqual(rejected["error"]["code"], "FORBIDDEN")

        call = self._modern_mcp_body("tools/call", {
            "name": "workspace_context", "arguments": {"context_id": "ctx_outside_access_grant"},
        })
        status, rejected, _ = self._modern_mcp_post(grant, call)
        # Tool-level refusals are complete results with isError and the
        # refusal code in structuredContent (the client-feedback contract),
        # not JSON-RPC errors.
        self.assertEqual(status, 200)
        self.assertEqual(rejected["result"]["resultType"], "complete")
        self.assertTrue(rejected["result"]["isError"])
        self.assertEqual(rejected["result"]["structuredContent"]["code"], "FORBIDDEN")
        call["params"]["arguments"] = {}
        call["params"]["name"] = "exec_command"
        status, unavailable, _ = self._modern_mcp_post(grant, call)
        self.assertEqual(status, 200)
        self.assertEqual(unavailable["result"]["resultType"], "complete")
        self.assertTrue(unavailable["result"]["isError"])
        self.assertEqual(unavailable["result"]["structuredContent"]["code"], "LOCAL_ADMISSION_BRIDGE_REQUIRED")
        self.server.store.revoke_mcp_access_grant(owner_id="owner_default", grant_id=grant["grant_id"])
        status, rejected, _ = self._modern_mcp_post(grant, request)
        self.assertEqual(status, 403)
        self.assertEqual(rejected["error"]["code"], "FORBIDDEN")

    def test_modern_mcp_invalid_ids_and_recovery_never_enqueue(self) -> None:
        grant = self._mcp_wire_grant()
        call = self._modern_mcp_body("tools/call", {
            "name": "workspace_context",
            "arguments": {
                "context_id": grant["context_id"], "operation": "request_read_only",
                "idempotency_key": "modern-invalid-id-no-effect",
                "expires_at_ms": self.server.store.clock() + 20_000,
                "expected_facade_contract": {
                    key: self.server.mcp_facade.contract[key] for key in ("schema_version", "profile", "sha256")
                },
            },
        })
        # Exercise invalid request IDs while admission is open, so it cannot
        # mask an accidental tool side effect.
        for invalid_id in (None, True, [], {}):
            status, rejected, _ = self._modern_mcp_post(grant, {**call, "id": invalid_id})
            self.assertEqual(status, 400)
            self.assertEqual(rejected["error"]["code"], -32600)
            self.assertNotIn("id", rejected)
        without_id = dict(call)
        without_id.pop("id")
        status, rejected, _ = self._modern_mcp_post(grant, without_id)
        self.assertEqual(status, 400)
        self.assertEqual(rejected["error"]["code"], "VALIDATION_ERROR")
        self.server.store.set_admission_mode(mode="recovery")
        status, rejected, _ = self._modern_mcp_post(grant, call)
        # Recovery-mode refusal is a tool-level CONFLICT feedback result
        # (isError, execution not_started); the counts below prove it had
        # no side effect.
        self.assertEqual(status, 200)
        self.assertTrue(rejected["result"]["isError"])
        self.assertEqual(rejected["result"]["structuredContent"]["code"], "CONFLICT")
        self.assertEqual(rejected["result"]["structuredContent"]["execution"], "not_started")
        for collection in ("mcp_read_only_intents", "work_requests", "actions"):
            self.assertEqual(self.server.store.health()["counts"][collection], 0)
        self.assertEqual(self.server.store.admission_status()["admission_mode"], "recovery")

    def test_mcp_facade_authenticates_and_queues_only_the_fixed_read_only_intent(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-mcp-facade-001",
            endpoint_id="endpoint-mcp-facade-001",
            display_name="MCP facade canary",
        )
        binding = self._registered_binding(
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
        grant = self.server.store.create_mcp_access_grant(
            owner_id="owner_default",
            context_id=context["context_id"],
            principal_id="openai-tunnel-fixture-001",
            expires_at_ms=self.server.store.clock() + 30_000,
        )
        mcp_authorization = f"Bearer {grant['access_token']}"
        initialize = {
            "jsonrpc": "2.0",
            "id": "initialize-001",
            "method": "initialize",
            "params": {"protocolVersion": "2025-11-25", "clientInfo": {"name": "control-plane-test", "version": "1.0"}},
        }
        status, forbidden = self._post("/mcp", initialize)
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")

        status, operator_forbidden = self._post("/mcp", initialize, f"Bearer {self.operator_token}")
        self.assertEqual(status, 403)
        self.assertEqual(operator_forbidden["error"]["code"], "FORBIDDEN")

        status, initialized = self._post("/mcp", initialize, mcp_authorization)
        self.assertEqual(status, 200)
        self.assertEqual(initialized["result"]["protocolVersion"], "2025-11-25")
        self.assertEqual(initialized["result"]["_meta"]["control_plane"]["execution"], "local_admission_required")
        self.assertEqual(initialized["result"]["_meta"]["control_plane"]["access_scope"], "server_issued_context_grant")

        status, listed = self._post(
            "/mcp",
            {"jsonrpc": "2.0", "id": "list-001", "method": "tools/list", "params": {}},
            mcp_authorization,
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
        workspace_tool = next(tool for tool in tools if tool["name"] == "workspace_context")
        self.assertEqual(workspace_tool["_meta"]["control_plane"]["capability_state"], "implemented")
        self.assertEqual(
            workspace_tool["_meta"]["control_plane"]["implemented_operations"],
            ["status", "request_read_only"],
        )
        for tool in tools:
            if tool["name"] == "workspace_context":
                continue
            self.assertEqual(tool["inputSchema"], {"type": "object", "additionalProperties": False, "properties": {}})
            self.assertEqual(tool["_meta"]["control_plane"]["capability_state"], "unavailable")

        discover = {
            "jsonrpc": "2.0",
            "id": "discover-001",
            "method": "server/discover",
            "params": {},
        }
        status, discovered = self._post("/mcp", discover, mcp_authorization)
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

        call = {
            "jsonrpc": "2.0",
            "id": "call-001",
            "method": "tools/call",
            "params": {"name": "workspace_context", "arguments": {"context_id": context["context_id"]}},
        }
        status, observed = self._post("/mcp", call, mcp_authorization)
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
        status, queued = self._post("/mcp", call, mcp_authorization)
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
        status, replayed = self._post("/mcp", call, mcp_authorization)
        self.assertEqual(status, 200)
        replay = replayed["result"]["structuredContent"]
        self.assertTrue(replay["replayed"])
        self.assertEqual(replay["request_id"], intent["request_id"])
        self.assertEqual(replay["action_id"], action["action_id"])

        call["id"] = "call-request-read-only-conflict-001"
        call["params"]["arguments"]["expires_at_ms"] += 1
        status, conflict = self._post("/mcp", call, mcp_authorization)
        self.assertEqual(status, 200)
        self.assertTrue(conflict["result"]["isError"])
        self.assertEqual(conflict["result"]["structuredContent"]["code"], "CONFLICT")
        self.assertEqual(self.server.store.health()["counts"]["actions"], 1)
        call["params"]["arguments"]["expires_at_ms"] -= 1

        call["id"] = "call-request-read-only-contract-mismatch-001"
        call["params"]["arguments"]["expected_facade_contract"] = {
            "schema_version": self.server.mcp_facade.contract["schema_version"],
            "profile": self.server.mcp_facade.contract["profile"],
            "sha256": "0" * 64,
        }
        status, mismatch = self._post("/mcp", call, mcp_authorization)
        self.assertEqual(status, 200)
        self.assertTrue(mismatch["result"]["isError"])
        self.assertEqual(mismatch["result"]["structuredContent"]["code"], "CONTRACT_MISMATCH")
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
        status, dispatch_unconfirmed = self._post("/mcp", call, mcp_authorization)
        self.assertEqual(status, 200)
        self.assertEqual(
            dispatch_unconfirmed["result"]["structuredContent"]["action"]["central_lifecycle_state"],
            "dispatch_unconfirmed",
        )
        workspace_summary = {
            "schema_version": 1,
            "project": {"type": "node", "name": "office-fixture", "version": "1.0.0"},
            "entries": [{"name": "office-marker.txt", "type": "file", "size_bytes": 17, "is_hidden": False, "is_ignored": False}],
            "entries_truncated": False,
            "git": {"is_repo": True, "branch": "main", "changed_count": 0, "truncated": False},
        }
        workspace_summary_sha256 = hashlib.sha256(
            json.dumps(workspace_summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        self.server.store.record_receipt(
            device_id=node["device_id"],
            action_id=action["action_id"],
            attempt_id=attempt["attempt_id"],
            receipt_state="completed",
            local_handle="local-handle-must-not-reach-facade",
            payload={
                "schema_version": 1,
                "operation_kind": "control_plane_read_only_workspace_context",
                "workspace_accessed": True,
                "actor": {"client_id": "electron-control-plane-bridge", "client_type": "electron"},
                "facade_contract": {
                    key: self.server.mcp_facade.contract[key]
                    for key in ("schema_version", "profile", "sha256")
                },
                "workspace_summary": workspace_summary,
                "workspace_summary_sha256": workspace_summary_sha256,
                "response_sha256": "a" * 64,
                "workspace": "E:/must-not-reach-facade",
                "raw_response": "must-not-reach-facade",
            },
        )
        call["id"] = "call-action-status-001"
        call["params"]["arguments"] = {
            "context_id": context["context_id"],
            "action_id": action["action_id"],
        }
        status, action_observed = self._post("/mcp", call, mcp_authorization)
        self.assertEqual(status, 200)
        lifecycle = action_observed["result"]["structuredContent"]["action"]
        self.assertEqual(lifecycle["action_id"], action["action_id"])
        self.assertEqual(lifecycle["delivery_state"], "settled")
        self.assertEqual(lifecycle["central_lifecycle_state"], "completed")
        self.assertEqual(len(lifecycle["attempts"]), 1)
        self.assertEqual(len(lifecycle["receipts"]), 1)
        self.assertEqual(lifecycle["receipts"][0]["receipt_state"], "completed")
        relay = action_observed["result"]["structuredContent"]
        self.assertTrue(relay["workspace_accessed"])
        self.assertEqual(relay["execution"], "completed_read_relay")
        self.assertEqual(relay["workspace_read"]["workspace_summary"], workspace_summary)
        self.assertEqual(relay["workspace_read"]["workspace_summary_sha256"], workspace_summary_sha256)
        self.assertNotIn("arguments_json", json.dumps(lifecycle))
        self.assertNotIn("admission_reference", json.dumps(lifecycle))
        self.assertNotIn("must-not-reach-facade", json.dumps(lifecycle))
        self.assertNotIn("must-not-reach-facade", json.dumps(relay))
        self.assertNotIn("local-handle-must-not-reach-facade", json.dumps(relay))

        other_context = self.server.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.server.store.clock() + 60_000,
        )
        call["id"] = "call-action-status-foreign-context"
        call["params"]["arguments"]["context_id"] = other_context["context_id"]
        status, wrong_context = self._post("/mcp", call, mcp_authorization)
        self.assertEqual(status, 200)
        self.assertTrue(wrong_context["result"]["isError"])
        self.assertEqual(wrong_context["result"]["structuredContent"]["code"], "FORBIDDEN")

        call["id"] = "call-002"
        call["params"]["arguments"] = {}
        call["params"]["name"] = "exec_command"
        status, rejected = self._post("/mcp", call, mcp_authorization)
        self.assertEqual(status, 200)
        self.assertTrue(rejected["result"]["isError"])
        self.assertEqual(rejected["result"]["structuredContent"]["code"], "LOCAL_ADMISSION_BRIDGE_REQUIRED")
        self.assertEqual(self.server.store.health()["counts"]["actions"], 1,
                         "unavailable public tools must not create a second action")

        status, invalid_tool = self._post(
            "/mcp",
            {"jsonrpc": "2.0", "id": "call-003", "method": "tools/call", "params": {"name": "unknown", "arguments": {"context_id": context["context_id"]}}},
            mcp_authorization,
        )
        self.assertEqual(status, 200)
        self.assertEqual(invalid_tool["error"]["code"], -32602)

        status, malformed = self._post(
            "/mcp",
            {"jsonrpc": "2.0", "id": True, "method": "ping", "params": {}},
            mcp_authorization,
        )
        self.assertEqual(status, 200)
        self.assertEqual(malformed["error"]["code"], -32600)

    def test_operator_issues_and_revokes_a_redacted_context_scoped_mcp_grant(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-mcp-grant-http-001",
            endpoint_id="endpoint-mcp-grant-http-001",
            display_name="MCP grant HTTP canary",
        )
        binding = self._registered_binding(
            owner_id="owner_default",
            device_id=node["device_id"],
            workspace_id="workspace-mcp-grant-http-001",
            workspace_generation="generation-mcp-grant-http-001",
            display_name="MCP grant HTTP workspace",
        )
        context = self.server.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.server.store.clock() + 60_000,
        )
        body = {
            "context_id": context["context_id"],
            "principal_id": "openai-tunnel-http-fixture",
            "expires_at_ms": self.server.store.clock() + 30_000,
        }
        status, forbidden = self._post("/v1/mcp-access-grants", body)
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")

        status, created = self._post("/v1/mcp-access-grants", body, f"Bearer {self.operator_token}")
        self.assertEqual(status, 201)
        self.assertEqual(created["context_id"], context["context_id"])
        self.assertEqual(created["principal_id"], body["principal_id"])
        self.assertRegex(created["access_token"], r"^mcp_[A-Za-z0-9_-]{32,}$")

        status, listed = self._get("/v1/mcp-access-grants", f"Bearer {self.operator_token}")
        self.assertEqual(status, 200)
        self.assertEqual(len(listed["mcp_access_grants"]), 1)
        self.assertNotIn("access_token", json.dumps(listed))
        self.assertNotIn("token_digest", json.dumps(listed))

        initialize = {"jsonrpc": "2.0", "id": "grant-init", "method": "initialize", "params": {}}
        status, initialized = self._post("/mcp", initialize, f"Bearer {created['access_token']}")
        self.assertEqual(status, 200)
        self.assertEqual(initialized["result"]["protocolVersion"], "2025-11-25")

        status, invalid_revoke = self._post(
            f"/v1/mcp-access-grants/{created['grant_id']}/revoke",
            {"unexpected": True},
            f"Bearer {self.operator_token}",
        )
        self.assertEqual(status, 400)
        self.assertEqual(invalid_revoke["error"]["code"], "VALIDATION_ERROR")
        status, revoked = self._post(
            f"/v1/mcp-access-grants/{created['grant_id']}/revoke",
            {},
            f"Bearer {self.operator_token}",
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(revoked["revoked_at_ms"], int)
        status, revoked_token = self._post("/mcp", initialize, f"Bearer {created['access_token']}")
        self.assertEqual(status, 403)
        self.assertEqual(revoked_token["error"]["code"], "FORBIDDEN")

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
        binding = self._registered_binding(
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

    def test_node_credential_rotation_is_node_mediated_and_replay_safe(self) -> None:
        node = self.server.store.enroll_node(
            owner_id="owner_default",
            device_id="device-http-rotation",
            endpoint_id="endpoint-http-rotation",
            display_name="HTTP rotation fixture",
        )
        current_secret = node["node_secret"]
        next_secret = "next-http-node-credential-000001"
        rotation_id = "rotate_" + "e" * 32
        node_auth = f"Node {current_secret}"
        status, prepared = self._post(
            f"/v1/nodes/{node['device_id']}/credential-rotation/prepare",
            {
                "rotation_id": rotation_id,
                "current_generation": 1,
                "next_credential_hash": _credential_hash(next_secret),
            },
            node_auth,
        )
        self.assertEqual(status, 200)
        self.assertEqual(prepared["state"], "prepared")
        status, replayed = self._post(
            f"/v1/nodes/{node['device_id']}/credential-rotation/prepare",
            {
                "rotation_id": rotation_id,
                "current_generation": 1,
                "next_credential_hash": _credential_hash(next_secret),
            },
            node_auth,
        )
        self.assertEqual(status, 200)
        self.assertEqual(replayed, prepared)

        status, activated = self._post(
            f"/v1/nodes/{node['device_id']}/credential-rotation/activate",
            {"rotation_id": rotation_id},
            node_auth,
        )
        self.assertEqual(status, 200)
        self.assertEqual(activated["state"], "activated")
        status, activated_replay = self._post(
            f"/v1/nodes/{node['device_id']}/credential-rotation/activate",
            {"rotation_id": rotation_id},
            node_auth,
        )
        self.assertEqual(status, 200)
        self.assertEqual(activated_replay, activated)

        status, completed = self._post(
            f"/v1/nodes/{node['device_id']}/credential-rotation/ack",
            {"rotation_id": rotation_id},
            f"Node {next_secret}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(completed["state"], "completed")
        status, completed_replay = self._post(
            f"/v1/nodes/{node['device_id']}/credential-rotation/ack",
            {"rotation_id": rotation_id},
            f"Node {next_secret}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(completed_replay, completed)
        status, old_status = self._post(
            f"/v1/nodes/{node['device_id']}/enrollment-status",
            {},
            node_auth,
        )
        self.assertEqual(status, 403)
        status, new_status = self._post(
            f"/v1/nodes/{node['device_id']}/enrollment-status",
            {},
            f"Node {next_secret}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(new_status["credential_generation"], 2)

        status, refused = self._post(
            f"/v1/nodes/{node['device_id']}/rotate-credential",
            {},
            f"Bearer {self.operator_token}",
        )
        self.assertEqual(status, 409)
        self.assertEqual(refused["error"]["code"], "CONFLICT")
