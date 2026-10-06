from __future__ import annotations

import io
import json
import os
import sqlite3
import tempfile
import threading
import unittest
from contextlib import closing
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from control_plane.http_api import ControlPlaneHttpServer
from control_plane.mcp_facade import PUBLIC_TOOL_NAMES, STATELESS_MCP_PROTOCOL_VERSION
from control_plane.mcp_oauth import (
    MCP_AUTH_MODE_OAUTH_INTROSPECTION,
    MCP_AUTH_MODE_PRIVATE_TUNNEL_SERVICE,
    OAuthAccessIdentity,
    OAuthAuthenticationError,
    OAuthClientCredentials,
    OAuthConfigurationError,
    OAuthIntrospectionConfiguration,
    OAuthIntrospectionVerifier,
    PrivateTunnelServiceConfiguration,
    oauth_configuration_from_environment,
    private_service_configuration_from_environment,
)
from control_plane.store import (
    ConflictError,
    ControlPlaneStore,
    MCP_PATCH_PERMISSION_VALIDATION_PROFILE,
    PermissionError,
    SCHEMA_VERSION,
)


ISSUER = "https://identity.example.test/tenant-one"
RESOURCE = "https://mcp.example.test"
INTROSPECTION_URL = "https://identity.example.test/tenant-one/introspect"
SCOPE = "control-plane.inventory"
WRITE_SCOPE = "control-plane.patch"


class PrivateTunnelServiceConfigurationTests(unittest.TestCase):
    def test_personal_tunnel_needs_service_identity_not_openai_account_ids(self) -> None:
        # OpenAI transport provisioning is separate from the local service
        # contract. No plan, organization or ChatGPT workspace ID is supplied.
        env = {
            "CONTROL_PLANE_MCP_AUTH_MODE": MCP_AUTH_MODE_PRIVATE_TUNNEL_SERVICE,
            "CONTROL_PLANE_MCP_SERVICE_PRINCIPAL_ID": "svcprn_" + "a" * 32,
            "CONTROL_PLANE_MCP_SERVICE_SCOPE": SCOPE,
        }
        config = private_service_configuration_from_environment(env)
        self.assertIsNotNone(config)
        self.assertIsNone(oauth_configuration_from_environment(env))
        self.assertEqual(config.verified_scopes, frozenset({SCOPE}))
        self.assertFalse(config.file_read_enabled)
        self.assertFalse(config.standing_write_enabled)
        self.assertFalse(config.exec_enabled)

    def test_explicit_shared_service_mode_is_distinct_from_oauth_and_legacy(self) -> None:
        env = {
            "CONTROL_PLANE_MCP_AUTH_MODE": MCP_AUTH_MODE_PRIVATE_TUNNEL_SERVICE,
            "CONTROL_PLANE_MCP_SERVICE_PRINCIPAL_ID": "svcprn_" + "a" * 32,
            "CONTROL_PLANE_MCP_SERVICE_SCOPE": SCOPE,
            "CONTROL_PLANE_MCP_SERVICE_PATCH_WRITE_SCOPE": WRITE_SCOPE,
            "CONTROL_PLANE_MCP_SERVICE_FILE_READ_ENABLED": "true",
            "CONTROL_PLANE_MCP_SERVICE_STANDING_WRITE_ENABLED": "true",
            "CONTROL_PLANE_MCP_SERVICE_EXEC_ENABLED": "true",
        }
        self.assertIsNone(oauth_configuration_from_environment(env))
        config = private_service_configuration_from_environment(env)
        self.assertIsNotNone(config)
        self.assertEqual(config.principal_id, "svcprn_" + "a" * 32)
        self.assertEqual(config.verified_scopes, frozenset({SCOPE, "control-plane.read", WRITE_SCOPE}))
        self.assertTrue(config.exec_enabled)
        self.assertIsNone(private_service_configuration_from_environment({}))

    def test_shared_service_mode_rejects_partial_or_cross_mode_privilege(self) -> None:
        base = {
            "CONTROL_PLANE_MCP_AUTH_MODE": MCP_AUTH_MODE_PRIVATE_TUNNEL_SERVICE,
            "CONTROL_PLANE_MCP_SERVICE_PRINCIPAL_ID": "svcprn_" + "a" * 32,
            "CONTROL_PLANE_MCP_SERVICE_SCOPE": SCOPE,
        }
        for patch in (
            {"CONTROL_PLANE_MCP_SERVICE_EXEC_ENABLED": "true"},
            {"CONTROL_PLANE_MCP_SERVICE_STANDING_WRITE_ENABLED": "true"},
            {"CONTROL_PLANE_MCP_SERVICE_PATCH_WRITE_SCOPE": SCOPE,
             "CONTROL_PLANE_MCP_SERVICE_FILE_READ_ENABLED": "true",
             "CONTROL_PLANE_MCP_SERVICE_STANDING_WRITE_ENABLED": "true"},
        ):
            with self.subTest(patch=patch):
                candidate = {**base, **patch}
                with self.assertRaises(OAuthConfigurationError):
                    private_service_configuration_from_environment(candidate)
        with self.assertRaises(OAuthConfigurationError):
            oauth_configuration_from_environment({**base, "CONTROL_PLANE_MCP_OAUTH_RESOURCE": RESOURCE})
        with self.assertRaises(OAuthConfigurationError):
            private_service_configuration_from_environment({
                **base, "CONTROL_PLANE_MCP_AUTH_MODE": "legacy_context_grant",
            })
        with self.assertRaises(OAuthConfigurationError):
            private_service_configuration_from_environment({
                **base, "CONTROL_PLANE_MCP_SERVICE_SCOPE": "control-plane.typo",
            })
        with self.assertRaises(OAuthConfigurationError):
            private_service_configuration_from_environment({
                **base,
                "CONTROL_PLANE_MCP_SERVICE_PATCH_WRITE_SCOPE": "control-plane.custom",
                "CONTROL_PLANE_MCP_SERVICE_FILE_READ_ENABLED": "true",
                "CONTROL_PLANE_MCP_SERVICE_STANDING_WRITE_ENABLED": "true",
            })


class PrivateTunnelServiceHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="control-plane-private-service-http-")
        self.addCleanup(self.temporary.cleanup)
        self.store = ControlPlaneStore(Path(self.temporary.name) / "control.sqlite3")
        self.principal = self.store.create_private_tunnel_service_principal(owner_id="owner_default")
        self.configuration = PrivateTunnelServiceConfiguration(
            principal_id=self.principal["principal_id"],
            required_scope=SCOPE,
            patch_write_scope=WRITE_SCOPE,
            file_read_enabled=True,
            standing_write_enabled=True,
            exec_enabled=True,
        )
        self.server = ControlPlaneHttpServer(
            ("127.0.0.1", 0), self.store, "o" * 40,
            mcp_private_service=self.configuration,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method: str, path: str, *, body: dict[str, Any] | None = None,
                bearer: str | None = None,
                extra_headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        headers.update(extra_headers or {})
        request = Request(self.url + path, data=payload, headers=headers, method=method)
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            try:
                return error.code, json.loads(error.read())
            finally:
                error.close()

    def test_operator_provisioned_shared_service_has_no_chatgpt_user_claim_and_revokes(self) -> None:
        operator = "o" * 40
        status, forbidden = self.request("POST", "/v1/mcp-service-principals", body={})
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")
        status, created = self.request("POST", "/v1/mcp-service-principals", body={}, bearer=operator)
        self.assertEqual(status, 201)
        self.assertRegex(created["principal_id"], r"^svcprn_[a-f0-9]{32}$")
        status, grant = self.request("POST", "/v1/mcp-service-grants", body={
            "principal_id": self.principal["principal_id"],
            "expires_at_ms": self.store.clock() + 60_000,
            "scopes": [SCOPE, "control-plane.read", WRITE_SCOPE],
        }, bearer=operator)
        self.assertEqual(status, 201)
        self.assertRegex(grant["access_token"], r"^mcpsvc_[A-Za-z0-9_-]{32,}$")
        status, listed = self.request("GET", "/v1/mcp-service-grants", bearer=operator)
        self.assertEqual(status, 200)
        self.assertEqual(len(listed["mcp_service_grants"]), 1)
        self.assertNotIn("access_token", json.dumps(listed))
        self.assertNotIn("token_digest", json.dumps(listed))
        status, tools = self.request("POST", "/mcp", body={
            "jsonrpc": "2.0", "id": "list", "method": "tools/list", "params": {},
        }, bearer=grant["access_token"])
        self.assertEqual(status, 200)
        status, cross_origin = self.request("POST", "/mcp", body={
            "jsonrpc": "2.0", "id": "simple-form", "method": "tools/list", "params": {},
        }, bearer=grant["access_token"], extra_headers={
            "Origin": "https://untrusted.example.invalid", "Content-Type": "text/plain",
        })
        self.assertEqual(status, 415)
        self.assertEqual(cross_origin["error"]["code"], "UNSUPPORTED_MEDIA_TYPE")
        descriptors = {tool["name"]: tool for tool in tools["result"]["tools"]}
        self.assertEqual(len(descriptors), 8)
        self.assertEqual(descriptors["agent_workflow"]["_meta"]["control_plane"]["capability_state"], "standing_write")
        self.assertNotIn("securitySchemes", descriptors["agent_workflow"])
        self.assertEqual(descriptors["agent_workflow"]["_meta"]["control_plane"]["access_scope"], "private_tunnel_service")
        status, inventoried = self.request("POST", "/mcp", body={
            "jsonrpc": "2.0", "id": "inventory", "method": "tools/call", "params": {
                "name": "workspace_context", "arguments": {"operation": "inventory"},
            },
        }, bearer=grant["access_token"])
        self.assertEqual(status, 200)
        self.assertNotIn("error", inventoried)
        self.assertEqual(inventoried["result"]["structuredContent"]["observation_kind"], "control_plane_account_target_inventory")
        modern_body = {
            "jsonrpc": "2.0", "id": "modern-list", "method": "tools/list",
            "params": {"_meta": {
                "io.modelcontextprotocol/protocolVersion": "2026-07-28",
                "io.modelcontextprotocol/clientCapabilities": {},
                "io.modelcontextprotocol/clientInfo": {"name": "service-fixture", "version": "1"},
            }},
        }
        status, modern = self.request("POST", "/mcp", body=modern_body,
            bearer=grant["access_token"], extra_headers={
                "Origin": "https://chatgpt.com",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2026-07-28",
                "Mcp-Method": "tools/list",
            })
        self.assertEqual(status, 200)
        self.assertEqual(len(modern["result"]["tools"]), 8)
        status, revoked = self.request("POST", f"/v1/mcp-service-grants/{grant['grant_id']}/revoke",
                                       body={}, bearer=operator)
        self.assertEqual(status, 200)
        self.assertIsInstance(revoked["revoked_at_ms"], int)
        status, denied = self.request("POST", "/mcp", body={
            "jsonrpc": "2.0", "id": "list-again", "method": "tools/list", "params": {},
        }, bearer=grant["access_token"])
        self.assertEqual(status, 403)
        self.assertEqual(denied["error"]["code"], "FORBIDDEN")

    def test_private_service_auth_rejects_unknown_principal_without_oauth_fallback(self) -> None:
        foreign = self.store.create_private_tunnel_service_principal(owner_id="owner_default")
        grant = self.store.create_mcp_service_grant(
            owner_id="owner_default", principal_id=foreign["principal_id"],
            expires_at_ms=self.store.clock() + 60_000,
            scopes=[SCOPE],
        )
        status, denied = self.request("POST", "/mcp", body={
            "jsonrpc": "2.0", "id": "foreign", "method": "tools/list", "params": {},
        }, bearer=grant["access_token"])
        self.assertEqual(status, 403)
        self.assertEqual(denied["error"]["code"], "FORBIDDEN")

    def test_inventory_only_service_grant_cannot_read_content_at_http_ingress(self) -> None:
        grant = self.store.create_mcp_service_grant(
            owner_id="owner_default", principal_id=self.principal["principal_id"],
            expires_at_ms=self.store.clock() + 60_000, scopes=[SCOPE],
        )
        status, inventory = self.request("POST", "/mcp", body={
            "jsonrpc": "2.0", "id": "inventory-only", "method": "tools/call",
            "params": {"name": "workspace_context", "arguments": {"operation": "inventory"}},
        }, bearer=grant["access_token"])
        self.assertEqual(status, 200)
        self.assertFalse(inventory["result"]["isError"])
        status, denied = self.request("POST", "/mcp", body={
            "jsonrpc": "2.0", "id": "read-denied", "method": "tools/call",
            "params": {"name": "workspace_context", "arguments": {
                "operation": "read_status", "action_id": "action-001",
            }},
        }, bearer=grant["access_token"])
        self.assertEqual(status, 200)
        self.assertEqual(denied["result"]["structuredContent"]["code"], "SERVICE_READ_SCOPE_REQUIRED")
        self.assertTrue(denied["result"]["isError"])

    def test_node_policy_authority_requires_exact_active_writable_binding(self) -> None:
        node = self.store.enroll_node(
            owner_id="owner_default", device_id="device-policy-authority",
            endpoint_id="endpoint-policy-authority", display_name="Policy node",
        )
        path = "/v1/nodes/device-policy-authority/policy-authority"
        selection = {
            "workspace_id": "workspace-policy-authority",
            "workspace_generation": "generation-policy-authority",
        }
        node_headers = {"Authorization": f"Node {node['node_secret']}"}
        status, denied = self.request("POST", path, body=selection)
        self.assertEqual(status, 403)
        self.assertEqual(denied["error"]["code"], "FORBIDDEN")
        self.store.register_node_workspace(
            device_id=node["device_id"], display_name="Selected workspace",
            capabilities={"read": True, "write": True, "exec": False}, **selection,
        )
        status, unbound = self.request("POST", path, body=selection, extra_headers=node_headers)
        self.assertEqual(status, 409)
        self.assertEqual(unbound["error"]["code"], "CONFLICT")
        binding = self.store.create_binding(
            owner_id="owner_default", device_id=node["device_id"],
            display_name="Selected workspace", **selection,
        )
        status, authority = self.request("POST", path, body=selection, extra_headers=node_headers)
        self.assertEqual(status, 200)
        self.assertEqual(authority["owner_id"], "owner_default")
        self.assertEqual(authority["workspace_generation"], selection["workspace_generation"])
        self.assertEqual(authority["binding_count"], 1)
        self.assertTrue(authority["standing_write_enabled"])
        self.assertTrue(authority["exec_enabled"])
        self.assertEqual(authority["exec_binding_count"], 0)
        self.assertEqual(authority["facade_contract"], {
            key: self.server.mcp_facade.contract[key]
            for key in ("schema_version", "profile", "sha256")
        })
        self.assertNotIn("node_secret", json.dumps(authority))
        status, wrong_generation = self.request("POST", path, body={
            **selection, "workspace_generation": "generation-other",
        }, extra_headers=node_headers)
        self.assertEqual(status, 409)
        self.assertEqual(wrong_generation["error"]["code"], "CONFLICT")
        self.store.revoke_binding(owner_id="owner_default", binding_id=binding["binding_id"])
        status, revoked = self.request("POST", path, body=selection, extra_headers=node_headers)
        self.assertEqual(status, 409)
        self.assertEqual(revoked["error"]["code"], "CONFLICT")

        foreign_node = self.store.enroll_node(
            owner_id="owner_foreign", device_id="device-policy-foreign",
            endpoint_id="endpoint-policy-foreign", display_name="Foreign node",
        )
        self.store.register_node_workspace(
            device_id=foreign_node["device_id"], display_name="Foreign workspace",
            capabilities={"read": True, "write": True, "exec": False}, **selection,
        )
        self.store.create_binding(
            owner_id="owner_foreign", device_id=foreign_node["device_id"],
            display_name="Foreign workspace", **selection,
        )
        status, foreign = self.request(
            "POST", "/v1/nodes/device-policy-foreign/policy-authority", body=selection,
            extra_headers={"Authorization": f"Node {foreign_node['node_secret']}"},
        )
        self.assertEqual(status, 409)
        self.assertEqual(foreign["error"]["code"], "CONFLICT")


class _Response:
    """Small urllib-like response deliberately lacking ``getcode``."""

    def __init__(self, payload: Any, *, status: int = 200, content_type: str = "application/json") -> None:
        self.status = status
        self.headers = {"Content-Type": content_type}
        self._payload = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        self.closed = False

    def read(self, _limit: int) -> bytes:
        return self._payload

    def close(self) -> None:
        self.closed = True


class _StaticVerifier:
    """A deterministic resource-server verifier for HTTP-boundary tests."""

    def __init__(
        self,
        identity: OAuthAccessIdentity | None = None,
        *,
        reject: bool = False,
        identities: dict[str, OAuthAccessIdentity] | None = None,
    ) -> None:
        self.identity = identity
        self.reject = reject
        self.identities = identities or {}
        self.tokens: list[str] = []

    def authenticate(self, token: str, *, required_scopes: object = None) -> OAuthAccessIdentity:
        self.tokens.append(token)
        identity = self.identities.get(token, self.identity)
        if self.reject or identity is None:
            raise OAuthAuthenticationError("OAuth access token is invalid.")
        if required_scopes is not None and not set(required_scopes) <= set(identity.scopes):
            raise OAuthAuthenticationError("OAuth access token is invalid.")
        return identity


def _configuration(
    *,
    file_read_enabled: bool = False,
    permission_requests_enabled: bool = False,
    approved_patch_enabled: bool = False,
    exec_enabled: bool = False,
) -> OAuthIntrospectionConfiguration:
    return OAuthIntrospectionConfiguration(
        issuer=ISSUER,
        resource=RESOURCE,
        introspection_url=INTROSPECTION_URL,
        required_scope=SCOPE,
        credentials=OAuthClientCredentials(client_id="control-plane-introspection", client_secret="fixture-secret"),
        file_read_enabled=file_read_enabled,
        permission_requests_enabled=permission_requests_enabled,
        patch_write_scope=WRITE_SCOPE if permission_requests_enabled else None,
        approved_patch_enabled=approved_patch_enabled,
        exec_enabled=exec_enabled,
    )


class OAuthConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="control-plane-oauth-")
        self.addCleanup(self.temporary.cleanup)
        self.credential_file = Path(self.temporary.name) / "introspection.json"
        self._write_credentials({"client_id": "fixture-client", "client_secret": "fixture-secret"})

    def _write_credentials(self, document: Any, mode: int = 0o600) -> None:
        self.credential_file.write_text(json.dumps(document), encoding="utf-8")
        self.credential_file.chmod(mode)

    def _environment(self, **overrides: str) -> dict[str, str]:
        environment = {
            "CONTROL_PLANE_MCP_AUTH_MODE": MCP_AUTH_MODE_OAUTH_INTROSPECTION,
            "CONTROL_PLANE_MCP_OAUTH_RESOURCE": RESOURCE,
            "CONTROL_PLANE_MCP_OAUTH_ISSUER": ISSUER,
            "CONTROL_PLANE_MCP_OAUTH_INTROSPECTION_URL": INTROSPECTION_URL,
            "CONTROL_PLANE_MCP_OAUTH_CREDENTIAL_FILE": str(self.credential_file),
            "CONTROL_PLANE_MCP_OAUTH_SCOPE": SCOPE,
        }
        environment.update(overrides)
        return environment

    def test_requires_complete_https_oauth_configuration(self) -> None:
        configuration = oauth_configuration_from_environment(self._environment())
        assert configuration is not None
        self.assertEqual(configuration.issuer, ISSUER)
        self.assertEqual(configuration.resource, RESOURCE)
        self.assertEqual(configuration.protected_resource_metadata(), {
            "resource": RESOURCE,
            "authorization_servers": [ISSUER],
            "scopes_supported": [SCOPE],
        })
        self.assertIn("resource_metadata=\"https://mcp.example.test/.well-known/oauth-protected-resource\"", configuration.www_authenticate())

        invalid_environments = (
            {"CONTROL_PLANE_MCP_AUTH_MODE": "unknown"},
            {"CONTROL_PLANE_MCP_OAUTH_RESOURCE": "http://mcp.example.test"},
            {"CONTROL_PLANE_MCP_OAUTH_ISSUER": "https://identity.example.test?issuer=wrong"},
            {"CONTROL_PLANE_MCP_OAUTH_INTROSPECTION_URL": "http://identity.example.test/introspect"},
            {"CONTROL_PLANE_MCP_OAUTH_SCOPE": "two scopes"},
        )
        for overrides in invalid_environments:
            with self.subTest(overrides=overrides):
                environment = self._environment(**overrides)
                if overrides.get("CONTROL_PLANE_MCP_AUTH_MODE") == "unknown":
                    environment = overrides
                with self.assertRaises(OAuthConfigurationError):
                    oauth_configuration_from_environment(environment)

        for absent in (
            "CONTROL_PLANE_MCP_OAUTH_RESOURCE",
            "CONTROL_PLANE_MCP_OAUTH_ISSUER",
            "CONTROL_PLANE_MCP_OAUTH_INTROSPECTION_URL",
            "CONTROL_PLANE_MCP_OAUTH_CREDENTIAL_FILE",
            "CONTROL_PLANE_MCP_OAUTH_SCOPE",
        ):
            with self.subTest(absent=absent):
                environment = self._environment()
                environment.pop(absent)
                with self.assertRaises(OAuthConfigurationError):
                    oauth_configuration_from_environment(environment)

    def test_legacy_mode_rejects_accidental_oauth_settings(self) -> None:
        with self.assertRaises(OAuthConfigurationError):
            oauth_configuration_from_environment({"CONTROL_PLANE_MCP_OAUTH_RESOURCE": RESOURCE})
        with self.assertRaises(OAuthConfigurationError):
            oauth_configuration_from_environment({"CONTROL_PLANE_MCP_OAUTH_FILE_READ_ENABLED": "false"})
        with self.assertRaises(OAuthConfigurationError):
            oauth_configuration_from_environment({"CONTROL_PLANE_MCP_OAUTH_PERMISSION_REQUESTS_ENABLED": "false"})
        self.assertIsNone(oauth_configuration_from_environment({}))

    def test_bounded_file_read_gate_is_opt_in_and_exact(self) -> None:
        default_configuration = oauth_configuration_from_environment(self._environment())
        assert default_configuration is not None
        self.assertFalse(default_configuration.file_read_enabled)

        enabled_configuration = oauth_configuration_from_environment(
            self._environment(CONTROL_PLANE_MCP_OAUTH_FILE_READ_ENABLED="true")
        )
        assert enabled_configuration is not None
        self.assertTrue(enabled_configuration.file_read_enabled)
        self.assertFalse(enabled_configuration.permission_requests_enabled)

        for value in ("TRUE", "False", "0", "yes", " ", "true "):
            with self.subTest(value=value):
                with self.assertRaises(OAuthConfigurationError):
                    oauth_configuration_from_environment(
                        self._environment(CONTROL_PLANE_MCP_OAUTH_FILE_READ_ENABLED=value)
                    )

    def test_permission_request_gate_is_opt_in_and_requires_bounded_file_read_candidate(self) -> None:
        default_configuration = oauth_configuration_from_environment(self._environment())
        assert default_configuration is not None
        self.assertFalse(default_configuration.permission_requests_enabled)

        enabled_configuration = oauth_configuration_from_environment(
            self._environment(
                CONTROL_PLANE_MCP_OAUTH_FILE_READ_ENABLED="true",
                CONTROL_PLANE_MCP_OAUTH_PERMISSION_REQUESTS_ENABLED="true",
                CONTROL_PLANE_MCP_OAUTH_PATCH_WRITE_SCOPE=WRITE_SCOPE,
            )
        )
        assert enabled_configuration is not None
        self.assertTrue(enabled_configuration.file_read_enabled)
        self.assertTrue(enabled_configuration.permission_requests_enabled)

        with self.assertRaises(OAuthConfigurationError):
            oauth_configuration_from_environment(
                self._environment(CONTROL_PLANE_MCP_OAUTH_PERMISSION_REQUESTS_ENABLED="true")
            )
        for value in ("TRUE", "False", "0", "yes", " ", "true "):
            with self.subTest(value=value):
                with self.assertRaises(OAuthConfigurationError):
                    oauth_configuration_from_environment(
                        self._environment(
                            CONTROL_PLANE_MCP_OAUTH_FILE_READ_ENABLED="true",
                            CONTROL_PLANE_MCP_OAUTH_PERMISSION_REQUESTS_ENABLED=value,
                            CONTROL_PLANE_MCP_OAUTH_PATCH_WRITE_SCOPE=WRITE_SCOPE,
                        )
                        )

    def test_standing_write_and_exec_profile_is_explicit_and_fail_closed(self) -> None:
        configuration = oauth_configuration_from_environment(
            self._environment(
                CONTROL_PLANE_MCP_OAUTH_FILE_READ_ENABLED="true",
                CONTROL_PLANE_MCP_OAUTH_STANDING_WRITE_ENABLED="true",
                CONTROL_PLANE_MCP_OAUTH_PATCH_WRITE_SCOPE=WRITE_SCOPE,
                CONTROL_PLANE_MCP_OAUTH_EXEC_ENABLED="true",
            )
        )
        assert configuration is not None
        self.assertTrue(configuration.file_read_enabled)
        self.assertTrue(configuration.standing_write_enabled)
        self.assertTrue(configuration.exec_enabled)
        self.assertFalse(configuration.permission_requests_enabled)
        self.assertFalse(configuration.approved_patch_enabled)
        self.assertEqual(configuration.patch_write_scope, WRITE_SCOPE)

        invalid_cases = (
            {
                "CONTROL_PLANE_MCP_OAUTH_FILE_READ_ENABLED": "true",
                "CONTROL_PLANE_MCP_OAUTH_STANDING_WRITE_ENABLED": "true",
            },
            {
                "CONTROL_PLANE_MCP_OAUTH_EXEC_ENABLED": "true",
            },
            {
                "CONTROL_PLANE_MCP_OAUTH_PATCH_WRITE_SCOPE": WRITE_SCOPE,
            },
            {
                "CONTROL_PLANE_MCP_OAUTH_FILE_READ_ENABLED": "true",
                "CONTROL_PLANE_MCP_OAUTH_STANDING_WRITE_ENABLED": "TRUE",
                "CONTROL_PLANE_MCP_OAUTH_PATCH_WRITE_SCOPE": WRITE_SCOPE,
            },
        )
        for overrides in invalid_cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(OAuthConfigurationError):
                    oauth_configuration_from_environment(self._environment(**overrides))

    def test_credentials_must_be_owner_private_regular_json(self) -> None:
        for mode in (0o644, 0o640, 0o700):
            with self.subTest(mode=oct(mode)):
                self._write_credentials({"client_id": "fixture-client", "client_secret": "fixture-secret"}, mode)
                with self.assertRaises(OAuthConfigurationError):
                    oauth_configuration_from_environment(self._environment())

        self._write_credentials({"client_id": "fixture-client"})
        with self.assertRaises(OAuthConfigurationError):
            oauth_configuration_from_environment(self._environment())

        self._write_credentials({"client_id": "fixture-client", "client_secret": "fixture-secret", "extra": "no"})
        with self.assertRaises(OAuthConfigurationError):
            oauth_configuration_from_environment(self._environment())

        target = Path(self.temporary.name) / "credential-target"
        target.write_text(json.dumps({"client_id": "fixture-client", "client_secret": "fixture-secret"}), encoding="utf-8")
        target.chmod(0o600)
        link = Path(self.temporary.name) / "credential-link"
        link.symlink_to(target)
        with self.assertRaises(OAuthConfigurationError):
            oauth_configuration_from_environment(self._environment(CONTROL_PLANE_MCP_OAUTH_CREDENTIAL_FILE=str(link)))


class OAuthIntrospectionVerifierTests(unittest.TestCase):
    def _verifier(self, payload: Any, *, status: int = 200, content_type: str = "application/json", now: float = 1000) -> OAuthIntrospectionVerifier:
        response = _Response(payload, status=status, content_type=content_type)
        return OAuthIntrospectionVerifier(
            _configuration(),
            clock_seconds=lambda: now,
            transport=lambda _request: response,
        )

    @staticmethod
    def _valid_payload(**overrides: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "active": True,
            "iss": ISSUER,
            "sub": "opaque-provider-subject-001",
            "aud": [RESOURCE],
            "scope": f"openid {SCOPE}",
            "exp": 2000,
            "token_type": "Bearer",
        }
        payload.update(overrides)
        return payload

    def test_valid_introspection_uses_authenticated_access_token_exchange(self) -> None:
        captured: list[Request] = []

        def transport(request: Request) -> _Response:
            captured.append(request)
            return _Response(self._valid_payload())

        identity = OAuthIntrospectionVerifier(
            _configuration(),
            clock_seconds=lambda: 1000,
            transport=transport,
        ).authenticate("opaque-access-token-001")
        self.assertEqual(identity.issuer, ISSUER)
        self.assertEqual(identity.subject, "opaque-provider-subject-001")
        self.assertIn(SCOPE, identity.scopes)
        self.assertEqual(len(captured), 1)
        request = captured[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.full_url, INTROSPECTION_URL)
        self.assertIn("Basic ", request.get_header("Authorization"))
        self.assertEqual(request.get_header("Content-type"), "application/x-www-form-urlencoded")
        self.assertIn(b"token=opaque-access-token-001", request.data or b"")
        self.assertIn(b"token_type_hint=access_token", request.data or b"")

    def test_rejects_invalid_introspection_claims_and_id_token_like_inputs(self) -> None:
        invalid_payloads = (
            self._valid_payload(active=False),
            self._valid_payload(iss="https://identity.example.test/other"),
            self._valid_payload(aud=[]),
            self._valid_payload(aud="https://other-resource.example.test"),
            self._valid_payload(scope="openid"),
            self._valid_payload(scope=[SCOPE]),
            self._valid_payload(exp=1000),
            self._valid_payload(exp=True),
            self._valid_payload(exp=float("nan")),
            self._valid_payload(exp=float("inf")),
            self._valid_payload(nbf=1001),
            self._valid_payload(nbf=True),
            self._valid_payload(nbf=float("nan")),
            # A positive introspection result must still describe a Bearer
            # access token; an ID token or unknown token type is never MCP
            # authority even when issuer/audience/scope happen to match.
            self._valid_payload(token_type="id_token"),
            self._valid_payload(token_type="MAC"),
            self._valid_payload(token_type=None),
            # A JWT-shaped string is never decoded locally. An IdP that says
            # it is not an active access token cannot be bypassed by claims
            # encoded in the string itself.
            {"active": False, "iss": ISSUER, "sub": "id-token-subject", "aud": RESOURCE, "scope": SCOPE, "exp": 2000},
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(OAuthAuthenticationError):
                    self._verifier(payload).authenticate("eyJhbGciOiJub25lIn0.eyJzdWIiOiJmb3JnZWQifQ.sig")

    def test_rejects_bad_transport_responses_and_malformed_tokens(self) -> None:
        cases = (
            (_Response(self._valid_payload(), status=302), "opaque-token"),
            (_Response(self._valid_payload(), content_type="text/plain"), "opaque-token"),
            (_Response(b"not-json"), "opaque-token"),
            (_Response(b"{" + b"x" * (16 * 1024 + 1)), "opaque-token"),
        )
        for response, token in cases:
            with self.subTest(response=response.status, content_type=response.headers["Content-Type"]):
                verifier = OAuthIntrospectionVerifier(_configuration(), transport=lambda _request, item=response: item)
                with self.assertRaises(OAuthAuthenticationError):
                    verifier.authenticate(token)

        for error in (
            HTTPError(INTROSPECTION_URL, 500, "failure", {}, io.BytesIO(b"{}")),
            URLError("offline"),
        ):
            with self.subTest(error=type(error).__name__):
                verifier = OAuthIntrospectionVerifier(_configuration(), transport=lambda _request, item=error: (_ for _ in ()).throw(item))
                try:
                    with self.assertRaises(OAuthAuthenticationError):
                        verifier.authenticate("opaque-token")
                finally:
                    if isinstance(error, HTTPError):
                        error.close()

        verifier = self._verifier(self._valid_payload())
        for token in ("", " space", "token ", "đ" * 10, "x" * 8193):
            with self.subTest(token_length=len(token)):
                with self.assertRaises(OAuthAuthenticationError):
                    verifier.authenticate(token)


class OAuthPrincipalStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="control-plane-oauth-store-")
        self.addCleanup(self.temporary.cleanup)
        self.now = 1_700_000_000_000
        self.store = ControlPlaneStore(Path(self.temporary.name) / "control.sqlite3", clock=lambda: self.now)

    def _target(self, *, owner_id: str, suffix: str, generation: str = "generation-001") -> dict[str, Any]:
        node = self.store.enroll_node(
            owner_id=owner_id,
            device_id=f"device-{suffix}",
            endpoint_id=f"endpoint-{suffix}",
            display_name=f"Node {suffix}",
        )
        self.store.register_node_workspace(
            device_id=node["device_id"],
            workspace_id=f"workspace-{suffix}",
            workspace_generation=generation,
            display_name=f"Workspace {suffix}",
            capabilities={"read": True, "write": False, "exec": False},
        )
        return self.store.create_binding(
            owner_id=owner_id,
            device_id=node["device_id"],
            workspace_id=f"workspace-{suffix}",
            workspace_generation=generation,
            display_name=f"Workspace {suffix}",
        )

    def test_only_explicit_enabled_mapping_resolves_and_projections_are_redacted(self) -> None:
        subject = "provider-user-alice@example.test"
        with self.assertRaises(PermissionError):
            self.store.resolve_oauth_principal(issuer=ISSUER, subject=subject)

        linked = self.store.link_oauth_principal(owner_id="owner-default", issuer=ISSUER, subject=subject)
        self.assertEqual(linked["state"], "enabled")
        self.assertNotIn("subject", linked)
        self.assertNotIn("issuer", linked)
        self.assertEqual(
            self.store.resolve_oauth_principal(issuer=ISSUER, subject=subject),
            {"principal_id": linked["principal_id"], "owner_id": "owner-default"},
        )
        listed = self.store.list_oauth_principals(owner_id="owner-default")
        self.assertEqual(listed, [linked])
        projection_text = json.dumps(listed)
        self.assertNotIn(subject, projection_text)
        self.assertNotIn(ISSUER, projection_text)
        with closing(sqlite3.connect(self.store.path)) as connection:
            events = "\n".join(row[0] for row in connection.execute("SELECT details_json FROM events"))
        self.assertNotIn(subject, events)
        self.assertNotIn(ISSUER, events)

        revoked = self.store.revoke_oauth_principal(owner_id="owner-default", principal_id=linked["principal_id"])
        self.assertEqual(revoked["state"], "revoked")
        with self.assertRaises(PermissionError):
            self.store.resolve_oauth_principal(issuer=ISSUER, subject=subject)

    def test_verified_identity_creates_one_opaque_pending_link_request_until_owner_approves(self) -> None:
        subject = "provider-user-pending@example.test"
        pending = self.store.resolve_or_request_oauth_principal(
            owner_id="owner-a",
            issuer=ISSUER,
            subject=subject,
        )
        self.assertEqual(pending["state"], "pending")
        request = pending["link_request"]
        self.assertEqual(request["state"], "pending")
        self.assertIsNone(request["principal_id"])
        rendered = json.dumps(request)
        self.assertNotIn(subject, rendered)
        self.assertNotIn(ISSUER, rendered)

        replay = self.store.resolve_or_request_oauth_principal(
            owner_id="owner-a",
            issuer=ISSUER,
            subject=subject,
        )
        self.assertEqual(replay["state"], "pending")
        self.assertEqual(replay["link_request"]["link_request_id"], request["link_request_id"])
        self.assertEqual(self.store.list_oauth_link_requests(owner_id="owner-a"), [request])
        self.assertEqual(self.store.list_oauth_link_requests(owner_id="owner-b"), [])

        # A different owner never gets a second request or a hint about the
        # original owner of the same verified account.
        foreign = self.store.resolve_or_request_oauth_principal(
            owner_id="owner-b",
            issuer=ISSUER,
            subject=subject,
        )
        self.assertEqual(foreign, {"state": "not_authorized"})
        self.assertEqual(self.store.list_oauth_link_requests(owner_id="owner-b"), [])

        approved = self.store.approve_oauth_link_request(
            owner_id="owner-a",
            link_request_id=request["link_request_id"],
        )
        self.assertEqual(approved["link_request"]["state"], "approved")
        self.assertEqual(approved["principal"]["state"], "enabled")
        self.assertEqual(approved["link_request"]["principal_id"], approved["principal"]["principal_id"])
        self.assertNotIn(subject, json.dumps(approved))
        self.assertNotIn(ISSUER, json.dumps(approved))
        self.assertEqual(
            self.store.resolve_or_request_oauth_principal(
                owner_id="owner-a",
                issuer=ISSUER,
                subject=subject,
            ),
            {
                "state": "linked",
                "principal_id": approved["principal"]["principal_id"],
                "owner_id": "owner-a",
            },
        )
        self.store.revoke_oauth_principal(
            owner_id="owner-a",
            principal_id=approved["principal"]["principal_id"],
        )
        idempotent_approval = self.store.approve_oauth_link_request(
            owner_id="owner-a",
            link_request_id=request["link_request_id"],
        )
        self.assertEqual(idempotent_approval["link_request"]["state"], "approved")
        self.assertEqual(idempotent_approval["principal"]["state"], "revoked")
        self.assertEqual(
            self.store.resolve_or_request_oauth_principal(
                owner_id="owner-a",
                issuer=ISSUER,
                subject=subject,
            ),
            {"state": "revoked"},
        )
        with closing(sqlite3.connect(self.store.path)) as connection:
            events = "\n".join(row[0] for row in connection.execute("SELECT details_json FROM events"))
        self.assertNotIn(subject, events)
        self.assertNotIn(ISSUER, events)

    def test_rejected_or_revoked_oauth_identity_cannot_reopen_its_own_link_request(self) -> None:
        subject = "provider-user-rejected@example.test"
        pending = self.store.resolve_or_request_oauth_principal(
            owner_id="owner-a",
            issuer=ISSUER,
            subject=subject,
        )["link_request"]
        rejected = self.store.reject_oauth_link_request(
            owner_id="owner-a",
            link_request_id=pending["link_request_id"],
        )
        self.assertEqual(rejected["state"], "rejected")
        self.assertIsNone(rejected["principal_id"])
        self.assertEqual(
            self.store.resolve_or_request_oauth_principal(
                owner_id="owner-a",
                issuer=ISSUER,
                subject=subject,
            ),
            {"state": "not_authorized"},
        )
        with self.assertRaises(ConflictError):
            self.store.approve_oauth_link_request(owner_id="owner-a", link_request_id=pending["link_request_id"])
        with self.assertRaises(PermissionError):
            self.store.reject_oauth_link_request(owner_id="owner-b", link_request_id=pending["link_request_id"])
        self.assertEqual(self.store.health()["counts"]["oauth_principals"], 0)
        self.assertEqual(self.store.health()["counts"]["oauth_link_requests"], 1)

    def test_v13_database_gains_opaque_link_request_table_without_rewriting_principal_mapping(self) -> None:
        legacy_path = Path(self.temporary.name) / "v13-oauth-principals.sqlite3"
        source = ControlPlaneStore(legacy_path, clock=lambda: self.now)
        linked = source.link_oauth_principal(
            owner_id="owner-a",
            issuer=ISSUER,
            subject="provider-user-existing@example.test",
        )
        with closing(sqlite3.connect(legacy_path)) as connection:
            connection.execute("DROP TABLE oauth_link_requests")
            connection.execute("PRAGMA user_version = 13")
            connection.commit()

        migrated = ControlPlaneStore(legacy_path, clock=lambda: self.now)
        self.assertEqual(
            migrated.resolve_oauth_principal(
                issuer=ISSUER,
                subject="provider-user-existing@example.test",
            ),
            {"principal_id": linked["principal_id"], "owner_id": "owner-a"},
        )
        with closing(sqlite3.connect(legacy_path)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
            self.assertIn(
                "oauth_link_requests",
                {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")},
            )
            self.assertIn(
                "oauth_link_requests_owner_state_idx",
                {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'index'")},
            )
        pending = migrated.resolve_or_request_oauth_principal(
            owner_id="owner-a",
            issuer=ISSUER,
            subject="provider-user-new@example.test",
        )
        self.assertEqual(pending["state"], "pending")
        self.assertEqual(migrated.health()["counts"]["oauth_link_requests"], 1)

    def test_account_target_inventory_cannot_cross_owners_and_reports_retired_roots(self) -> None:
        binding_a = self._target(owner_id="owner-a", suffix="a")
        self._target(owner_id="owner-b", suffix="b")
        alice = self.store.link_oauth_principal(owner_id="owner-a", issuer=ISSUER, subject="subject-alice")
        bob = self.store.link_oauth_principal(owner_id="owner-b", issuer=ISSUER, subject="subject-bob")
        self.assertEqual([item["principal_id"] for item in self.store.list_oauth_principals(owner_id="owner-a")], [alice["principal_id"]])
        self.assertEqual([item["principal_id"] for item in self.store.list_oauth_principals(owner_id="owner-b")], [bob["principal_id"]])
        with self.assertRaises(PermissionError):
            self.store.link_oauth_principal(owner_id="owner-a", issuer=ISSUER, subject="subject-bob")

        targets_a = self.store.list_account_targets(owner_id="owner-a")
        self.assertEqual([item["binding_id"] for item in targets_a], [binding_a["binding_id"]])
        self.assertNotIn("path", json.dumps(targets_a))
        self.assertNotIn("workspace-b", json.dumps(targets_a))

        node_a = binding_a["device_id"]
        self.store.register_node_workspace(
            device_id=node_a,
            workspace_id="workspace-a",
            workspace_generation="generation-002",
            display_name="Workspace A replacement",
            capabilities={"read": True, "write": False, "exec": False},
        )
        retired = self.store.list_account_targets(owner_id="owner-a")
        self.assertEqual([item["binding_id"] for item in retired], [binding_a["binding_id"]])
        self.assertEqual(retired[0]["binding_state"], "revoked")
        self.assertEqual(retired[0]["workspace_state"], "retired")
        self.assertEqual(retired[0]["dispatch_state"], "binding_revoked")
        self.assertEqual(retired[0]["dispatch_blockers"], ["binding_revoked", "workspace_retired"])
        self.assertFalse(retired[0]["capabilities"]["write"])
        replacement = self.store.create_binding(
            owner_id="owner-a",
            device_id=node_a,
            workspace_id="workspace-a",
            workspace_generation="generation-002",
            display_name="Workspace A replacement",
        )
        self.assertEqual(
            {item["binding_id"] for item in self.store.list_account_targets(owner_id="owner-a")},
            {binding_a["binding_id"], replacement["binding_id"]},
        )
        current = next(
            item for item in self.store.list_account_targets(owner_id="owner-a")
            if item["binding_id"] == replacement["binding_id"]
        )
        self.assertEqual(current["workspace_state"], "active")
        self.assertEqual(current["dispatch_state"], "dispatchable")

    def test_account_target_inventory_reports_revoked_binding_without_making_it_dispatchable(self) -> None:
        binding = self._target(owner_id="owner-a", suffix="revoked")
        revoked = self.store.revoke_binding(owner_id="owner-a", binding_id=binding["binding_id"])
        self.assertIsInstance(revoked["revoked_at_ms"], int)

        targets = self.store.list_account_targets(owner_id="owner-a")
        self.assertEqual([item["binding_id"] for item in targets], [binding["binding_id"]])
        target = targets[0]
        self.assertEqual(target["binding_state"], "revoked")
        self.assertEqual(target["workspace_state"], "active")
        self.assertEqual(target["dispatch_state"], "binding_revoked")
        self.assertEqual(target["dispatch_blockers"], ["binding_revoked"])
        self.assertEqual(target["binding_revoked_at_ms"], revoked["revoked_at_ms"])
        self.assertNotIn("canonical_path", json.dumps(target))
        self.assertNotIn("node_secret", json.dumps(target))

    def test_account_target_inventory_distinguishes_unknown_online_and_stale_presence(self) -> None:
        binding = self._target(owner_id="owner-a", suffix="presence")

        initial = self.store.list_account_targets(owner_id="owner-a")[0]
        self.assertEqual(initial["binding_id"], binding["binding_id"])
        self.assertEqual(initial["presence_state"], "unknown")
        self.assertIsNone(initial["heartbeat_age_ms"])

        self.store.heartbeat(
            device_id=binding["device_id"],
            endpoint_id=binding["endpoint_id"],
            runtime_instance_id="runtime-presence-0001",
            mcp_server_instance_id="mcp-presence-0001",
            activation_epoch="epoch-presence-0001",
            contract_version="smart-v3-presence",
            readiness="degraded",
        )
        online = self.store.list_account_targets(owner_id="owner-a")[0]
        self.assertEqual(online["presence_state"], "online")
        self.assertEqual(online["heartbeat_age_ms"], 0)

        self.now += self.store.heartbeat_max_age_ms + 1
        stale = self.store.list_account_targets(owner_id="owner-a")[0]
        self.assertEqual(stale["presence_state"], "offline")
        self.assertEqual(stale["heartbeat_age_ms"], self.store.heartbeat_max_age_ms + 1)

    def test_account_target_inventory_reports_policy_expiry_from_the_read_clock(self) -> None:
        binding = self._target(owner_id="owner-a", suffix="policy-expiry")
        self.store.heartbeat(
            device_id=binding["device_id"],
            endpoint_id=binding["endpoint_id"],
            runtime_instance_id="runtime-policy-expiry-0001",
            mcp_server_instance_id="mcp-policy-expiry-0001",
            activation_epoch="epoch-policy-expiry-0001",
            contract_version="smart-v3-policy-expiry",
            readiness="ready",
            policy_observation={
                "state": "enabled",
                "expires_at_ms": self.now + 1_000,
                "policy_sha256": "a" * 64,
                "reason": "",
            },
        )

        current = self.store.list_account_targets(owner_id="owner-a")[0]
        self.assertEqual(current["policy_state"], "enabled")
        self.assertEqual(current["policy_observed_at_ms"], current["last_seen_at_ms"])

        self.now += 1_000
        expired = self.store.list_account_targets(owner_id="owner-a")[0]
        self.assertEqual(expired["policy_state"], "expired_or_disabled")

    def test_account_target_inventory_fails_closed_after_heartbeat_without_policy_observation(self) -> None:
        binding = self._target(owner_id="owner-a", suffix="policy-stale")
        self.store.heartbeat(
            device_id=binding["device_id"],
            endpoint_id=binding["endpoint_id"],
            runtime_instance_id="runtime-policy-stale-0001",
            mcp_server_instance_id="mcp-policy-stale-0001",
            activation_epoch="epoch-policy-stale-0001",
            contract_version="smart-v3-policy-stale",
            readiness="ready",
            policy_observation={
                "state": "enabled",
                "expires_at_ms": self.now + 60_000,
                "policy_sha256": "b" * 64,
                "reason": "",
            },
        )
        self.now += 1
        self.store.heartbeat(
            device_id=binding["device_id"],
            endpoint_id=binding["endpoint_id"],
            runtime_instance_id="runtime-policy-stale-0002",
            mcp_server_instance_id="mcp-policy-stale-0002",
            activation_epoch="epoch-policy-stale-0002",
            contract_version="smart-v3-policy-stale",
            readiness="ready",
        )

        target = self.store.list_account_targets(owner_id="owner-a")[0]
        self.assertEqual(target["policy_state"], "unobserved")
        self.assertNotEqual(target["policy_observed_at_ms"], target["last_seen_at_ms"])

    def test_account_target_inventory_does_not_treat_policy_from_offline_node_as_current(self) -> None:
        binding = self._target(owner_id="owner-a", suffix="policy-offline")
        self.store.heartbeat(
            device_id=binding["device_id"],
            endpoint_id=binding["endpoint_id"],
            runtime_instance_id="runtime-policy-offline-0001",
            mcp_server_instance_id="mcp-policy-offline-0001",
            activation_epoch="epoch-policy-offline-0001",
            contract_version="smart-v3-policy-offline",
            readiness="ready",
            policy_observation={
                "state": "enabled",
                "expires_at_ms": self.now + 60_000,
                "policy_sha256": "c" * 64,
                "reason": "",
            },
        )
        self.now += self.store.heartbeat_max_age_ms + 1

        target = self.store.list_account_targets(owner_id="owner-a")[0]
        self.assertEqual(target["presence_state"], "offline")
        self.assertEqual(target["policy_state"], "unobserved")


class OAuthMcpHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="control-plane-oauth-http-")
        self.addCleanup(self.temporary.cleanup)
        self.store = ControlPlaneStore(Path(self.temporary.name) / "control.sqlite3")
        self.identity = OAuthAccessIdentity(issuer=ISSUER, subject="provider-user-alice", scopes=frozenset({SCOPE, WRITE_SCOPE}))
        self.verifier = _StaticVerifier(self.identity)
        self.main_server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.store,
            "o" * 40,
            mcp_enabled=False,
            mcp_oauth=_configuration(),
            mcp_oauth_verifier=self.verifier,
        )
        self.mcp_server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.store,
            "o" * 40,
            mcp_enabled=True,
            mcp_ingress_only=True,
            mcp_oauth=_configuration(),
            mcp_oauth_verifier=self.verifier,
        )
        self.threads = [
            threading.Thread(target=self.main_server.serve_forever, daemon=True),
            threading.Thread(target=self.mcp_server.serve_forever, daemon=True),
        ]
        for thread in self.threads:
            thread.start()
        self.main_url = f"http://127.0.0.1:{self.main_server.server_port}"
        self.mcp_url = f"http://127.0.0.1:{self.mcp_server.server_port}"

    def tearDown(self) -> None:
        for server in (self.main_server, self.mcp_server):
            server.shutdown()
            server.server_close()
        for thread in self.threads:
            thread.join(timeout=2)

    @staticmethod
    def _response(request: Request) -> tuple[int, dict[str, Any], dict[str, str]]:
        try:
            with urlopen(request, timeout=2) as response:
                return response.status, json.loads(response.read()), {key.lower(): value for key, value in response.headers.items()}
        except HTTPError as error:
            try:
                return error.code, json.loads(error.read()), {key.lower(): value for key, value in error.headers.items()}
            finally:
                error.close()

    def _get(self, base_url: str, path: str, authorization: str | None = None) -> tuple[int, dict[str, Any], dict[str, str]]:
        headers = {"Authorization": authorization} if authorization else {}
        return self._response(Request(f"{base_url}{path}", headers=headers, method="GET"))

    def _mcp_post(
        self,
        body: dict[str, Any],
        authorization: str | None = None,
        additional_headers: dict[str, str] | None = None,
        base_url: str | None = None,
    ) -> tuple[int, dict[str, Any], dict[str, str]]:
        headers = {"Content-Type": "application/json"}
        headers.update(additional_headers or {})
        if authorization is not None:
            headers["Authorization"] = authorization
        return self._response(Request(
            f"{base_url or self.mcp_url}/mcp",
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        ))

    def _main_post(
        self,
        path: str,
        body: dict[str, Any],
        authorization: str | None = None,
    ) -> tuple[int, dict[str, Any], dict[str, str]]:
        headers = {"Content-Type": "application/json"}
        if authorization is not None:
            headers["Authorization"] = authorization
        return self._response(Request(
            f"{self.main_url}{path}",
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        ))

    def _link_and_target(self, *, write: bool = False, execute: bool = False, suffix: str = "001") -> dict[str, Any]:
        self.store.link_oauth_principal(owner_id="owner_default", issuer=ISSUER, subject=self.identity.subject)
        node = self.store.enroll_node(
            owner_id="owner_default",
            device_id=f"oauth-http-node-{suffix}",
            endpoint_id=f"oauth-http-endpoint-{suffix}",
            display_name=f"OAuth HTTP node {suffix}",
        )
        self.store.register_node_workspace(
            device_id=node["device_id"],
            workspace_id=f"oauth-http-workspace-{suffix}",
            workspace_generation=f"oauth-http-generation-{suffix}",
            display_name=f"OAuth HTTP workspace {suffix}",
            capabilities={"read": True, "write": write, "exec": execute},
        )
        return self.store.create_binding(
            owner_id="owner_default",
            device_id=node["device_id"],
            workspace_id=f"oauth-http-workspace-{suffix}",
            workspace_generation=f"oauth-http-generation-{suffix}",
            display_name=f"OAuth HTTP workspace {suffix}",
        )

    def test_metadata_is_only_available_from_oauth_mcp_ingress(self) -> None:
        status, metadata, _headers = self._get(self.mcp_url, "/.well-known/oauth-protected-resource")
        self.assertEqual(status, 200)
        self.assertEqual(metadata["resource"], RESOURCE)
        self.assertEqual(metadata["authorization_servers"], [ISSUER])
        for path in ("/healthz", "/", "/v1/nodes", "/mcp"):
            with self.subTest(path=path):
                status, response, _headers = self._get(self.mcp_url, path)
                self.assertEqual(status, 404)
                self.assertEqual(response["error"]["code"], "NOT_FOUND")
        status, response, _headers = self._get(self.main_url, "/.well-known/oauth-protected-resource")
        self.assertEqual(status, 404)
        self.assertEqual(response["error"]["code"], "NOT_FOUND")
        status, health, _headers = self._get(self.main_url, "/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(health["mcp_authentication_mode"], MCP_AUTH_MODE_OAUTH_INTROSPECTION)

        legacy = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.store,
            "o" * 40,
            mcp_enabled=True,
            mcp_ingress_only=True,
        )
        legacy_thread = threading.Thread(target=legacy.serve_forever, daemon=True)
        legacy_thread.start()
        try:
            status, response, _headers = self._get(
                f"http://127.0.0.1:{legacy.server_port}",
                "/.well-known/oauth-protected-resource",
            )
            self.assertEqual(status, 404)
            self.assertEqual(response["error"]["code"], "NOT_FOUND")
        finally:
            legacy.shutdown()
            legacy.server_close()
            legacy_thread.join(timeout=2)

    def test_missing_or_invalid_oauth_gets_challenge_but_unmapped_identity_creates_opaque_pending_link(self) -> None:
        call = {
            "jsonrpc": "2.0",
            "id": "oauth-auth-call-001",
            "method": "tools/call",
            "params": {"name": "workspace_context", "arguments": {"operation": "inventory"}},
        }
        status, response, headers = self._mcp_post(call)
        self.assertEqual(status, 401)
        self.assertIn("www-authenticate", headers)
        self.assertIn("resource_metadata=\"https://mcp.example.test/.well-known/oauth-protected-resource\"", headers["www-authenticate"])
        self.assertTrue(response["result"]["isError"])
        self.assertIn("mcp/www_authenticate", response["result"]["_meta"])

        status, response, headers = self._mcp_post(call, "Bearer opaque-valid-but-unmapped")
        self.assertEqual(status, 403)
        self.assertTrue(response["result"]["isError"])
        self.assertEqual(response["result"]["structuredContent"]["code"], "OAUTH_ACCOUNT_LINK_PENDING")
        self.assertNotIn("www-authenticate", headers)
        pending = self.store.list_oauth_link_requests(owner_id="owner_default")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["state"], "pending")
        self.assertEqual(
            response["result"]["structuredContent"]["account_link_request_id"],
            pending[0]["link_request_id"],
        )
        self.assertNotIn(self.identity.subject, json.dumps(pending))
        self.assertNotIn(ISSUER, json.dumps(pending))

        self.verifier.reject = True
        status, response, headers = self._mcp_post(call, "Bearer mcp_legacy-pilot-grant-must-not-fallback")
        self.assertEqual(status, 401)
        self.assertIn("www-authenticate", headers)
        self.assertIn("mcp/www_authenticate", response["result"]["_meta"])

    def test_owner_approval_of_an_opaque_link_request_is_required_before_inventory(self) -> None:
        call = {
            "jsonrpc": "2.0",
            "id": "oauth-link-request-001",
            "method": "tools/call",
            "params": {"name": "workspace_context", "arguments": {"operation": "inventory"}},
        }
        status, pending_response, _headers = self._mcp_post(call, "Bearer opaque-valid-access-token")
        self.assertEqual(status, 403)
        self.assertEqual(pending_response["result"]["structuredContent"]["code"], "OAUTH_ACCOUNT_LINK_PENDING")

        operator_auth = "Bearer " + "o" * 40
        status, listed, _headers = self._get(self.main_url, "/v1/oauth-link-requests", operator_auth)
        self.assertEqual(status, 200)
        self.assertEqual(len(listed["oauth_link_requests"]), 1)
        request = listed["oauth_link_requests"][0]
        self.assertEqual(request["state"], "pending")
        self.assertNotIn(self.identity.subject, json.dumps(listed))
        self.assertNotIn(ISSUER, json.dumps(listed))

        status, forbidden, _headers = self._main_post(
            f"/v1/oauth-link-requests/{request['link_request_id']}/approve",
            {},
        )
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")

        status, approved, _headers = self._main_post(
            f"/v1/oauth-link-requests/{request['link_request_id']}/approve",
            {},
            operator_auth,
        )
        self.assertEqual(status, 200)
        self.assertEqual(approved["link_request"]["state"], "approved")
        self.assertEqual(approved["principal"]["state"], "enabled")
        self.assertNotIn(self.identity.subject, json.dumps(approved))
        self.assertNotIn(ISSUER, json.dumps(approved))

        status, inventory, _headers = self._mcp_post(call, "Bearer opaque-valid-access-token")
        self.assertEqual(status, 200)
        content = inventory["result"]["structuredContent"]
        self.assertEqual(content["observation_kind"], "control_plane_account_target_inventory")
        self.assertEqual(content["targets"], [])
        self.assertFalse(content["workspace_accessed"])

    def test_mapped_account_can_discover_and_inventory_without_creating_authority(self) -> None:
        binding = self._link_and_target()
        before = self.store.health()["counts"].copy()
        authorization = "Bearer opaque-valid-access-token"
        initialize = {"jsonrpc": "2.0", "id": "oauth-initialize-001", "method": "initialize", "params": {}}
        status, initialized, _headers = self._mcp_post(initialize, authorization)
        self.assertEqual(status, 200)
        self.assertEqual(initialized["result"]["_meta"]["control_plane"]["access_scope"], "oauth_account")

        status, listed, _headers = self._mcp_post(
            {"jsonrpc": "2.0", "id": "oauth-tools-list-001", "method": "tools/list", "params": {}},
            authorization,
        )
        self.assertEqual(status, 200)
        tools = listed["result"]["tools"]
        self.assertEqual([tool["name"] for tool in tools], list(PUBLIC_TOOL_NAMES))
        for tool in tools:
            self.assertEqual(tool["securitySchemes"], [{"type": "oauth2", "scopes": [SCOPE]}])
            self.assertEqual(tool["_meta"]["securitySchemes"], tool["securitySchemes"])

        inventory = {
            "jsonrpc": "2.0",
            "id": "oauth-inventory-001",
            "method": "tools/call",
            "params": {"name": "workspace_context", "arguments": {"operation": "inventory"}},
        }
        status, response, _headers = self._mcp_post(inventory, authorization)
        self.assertEqual(status, 200)
        content = response["result"]["structuredContent"]
        self.assertEqual(content["observation_kind"], "control_plane_account_target_inventory")
        self.assertEqual([target["binding_id"] for target in content["targets"]], [binding["binding_id"]])
        self.assertFalse(content["workspace_accessed"])
        after = self.store.health()["counts"]
        for name in ("contexts", "work_requests", "actions", "mcp_read_only_intents"):
            self.assertEqual(after[name], before[name])

    def test_oauth_inventory_keeps_revoked_binding_visible_but_not_dispatchable(self) -> None:
        binding = self._link_and_target(write=True)
        revoked = self.store.revoke_binding(owner_id="owner_default", binding_id=binding["binding_id"])
        call = {
            "jsonrpc": "2.0",
            "id": "oauth-revoked-inventory-001",
            "method": "tools/call",
            "params": {"name": "workspace_context", "arguments": {"operation": "inventory"}},
        }

        status, response, _headers = self._mcp_post(call, "Bearer opaque-valid-access-token")
        self.assertEqual(status, 200)
        targets = response["result"]["structuredContent"]["targets"]
        self.assertEqual([item["binding_id"] for item in targets], [binding["binding_id"]])
        target = targets[0]
        self.assertEqual(target["binding_state"], "revoked")
        self.assertEqual(target["dispatch_state"], "binding_revoked")
        self.assertEqual(target["dispatch_blockers"], ["binding_revoked"])
        self.assertEqual(target["binding_revoked_at_ms"], revoked["revoked_at_ms"])
        self.assertNotIn("canonical_path", json.dumps(response))
        self.assertNotIn("node_secret", json.dumps(response))

    def test_revoked_oauth_principal_cannot_use_http_inventory_or_leak_target(self) -> None:
        """Principal revocation is an account denial, not a new link request."""

        binding = self._link_and_target(write=True)
        principal = self.store.resolve_oauth_principal(issuer=ISSUER, subject=self.identity.subject)
        self.store.revoke_oauth_principal(owner_id="owner_default", principal_id=principal["principal_id"])
        call = {
            "jsonrpc": "2.0",
            "id": "oauth-principal-revoked-inventory-001",
            "method": "tools/call",
            "params": {"name": "workspace_context", "arguments": {"operation": "inventory"}},
        }

        status, response, headers = self._mcp_post(call, "Bearer opaque-valid-access-token")
        self.assertEqual(status, 403)
        self.assertEqual(response["error"]["code"], "FORBIDDEN")
        self.assertNotIn("WWW-Authenticate", {key.title(): value for key, value in headers.items()})
        rendered = json.dumps(response)
        self.assertNotIn(binding["binding_id"], rendered)
        self.assertNotIn("canonical_path", rendered)
        self.assertNotIn("node_secret", rendered)
        self.assertNotIn("OAUTH_ACCOUNT_LINK_PENDING", rendered)

    def test_oauth_inventory_keeps_retired_generation_visible_and_task_open_fails_closed(self) -> None:
        """Retiring a generation never retargets a public task to its replacement."""

        binding = self._link_and_target(write=True)
        self.store.register_node_workspace(
            device_id=binding["device_id"],
            workspace_id=binding["workspace_id"],
            workspace_generation=f"{binding['workspace_generation']}-replacement",
            display_name="OAuth HTTP workspace replacement",
            capabilities={"read": True, "write": True, "exec": False},
        )
        candidate_server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.store,
            "o" * 40,
            mcp_enabled=True,
            mcp_ingress_only=True,
            mcp_oauth=_configuration(file_read_enabled=True),
            mcp_oauth_verifier=self.verifier,
        )
        candidate_thread = threading.Thread(target=candidate_server.serve_forever, daemon=True)
        candidate_thread.start()
        candidate_url = f"http://127.0.0.1:{candidate_server.server_port}"
        try:
            inventory = {
                "jsonrpc": "2.0",
                "id": "oauth-retired-inventory-001",
                "method": "tools/call",
                "params": {"name": "workspace_context", "arguments": {"operation": "inventory"}},
            }
            status, response, _headers = self._mcp_post(
                inventory,
                "Bearer opaque-valid-access-token",
                base_url=candidate_url,
            )
            self.assertEqual(status, 200)
            target = response["result"]["structuredContent"]["targets"][0]
            self.assertEqual(target["binding_id"], binding["binding_id"])
            self.assertEqual(target["binding_state"], "revoked")
            self.assertEqual(target["workspace_state"], "retired")
            self.assertEqual(target["dispatch_state"], "binding_revoked")
            self.assertEqual(target["dispatch_blockers"], ["binding_revoked", "workspace_retired"])
            self.assertNotIn("canonical_path", json.dumps(response))
            self.assertNotIn("node_secret", json.dumps(response))

            task_open = {
                "jsonrpc": "2.0",
                "id": "oauth-retired-task-open-001",
                "method": "tools/call",
                "params": {"name": "workspace_context", "arguments": {
                    "operation": "task_open",
                    "binding_id": binding["binding_id"],
                    "label": "Must reject retired generation",
                    "idempotency_key": "oauth-retired-task-open-001",
                }},
            }
            status, rejected, _headers = self._mcp_post(
                task_open,
                "Bearer opaque-valid-access-token",
                base_url=candidate_url,
            )
            self.assertEqual(status, 200)
            self.assertEqual(rejected["error"]["data"]["code"], "CONFLICT")
            self.assertIn("no longer dispatchable", rejected["error"]["data"]["message"])
        finally:
            candidate_server.shutdown()
            candidate_server.server_close()
            candidate_thread.join(timeout=2)

    def test_oauth_inventory_keeps_revoked_node_visible_and_task_open_fails_closed(self) -> None:
        """A shared account can see the node lifecycle state but cannot open work on it."""

        binding = self._link_and_target(write=True)
        revoked = self.store.revoke_node(owner_id="owner_default", device_id=binding["device_id"])
        candidate_server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.store,
            "o" * 40,
            mcp_enabled=True,
            mcp_ingress_only=True,
            mcp_oauth=_configuration(file_read_enabled=True),
            mcp_oauth_verifier=self.verifier,
        )
        candidate_thread = threading.Thread(target=candidate_server.serve_forever, daemon=True)
        candidate_thread.start()
        candidate_url = f"http://127.0.0.1:{candidate_server.server_port}"
        try:
            inventory = {
                "jsonrpc": "2.0",
                "id": "oauth-node-revoked-inventory-001",
                "method": "tools/call",
                "params": {"name": "workspace_context", "arguments": {"operation": "inventory"}},
            }
            status, response, _headers = self._mcp_post(
                inventory,
                "Bearer opaque-valid-access-token",
                base_url=candidate_url,
            )
            self.assertEqual(status, 200)
            target = response["result"]["structuredContent"]["targets"][0]
            self.assertEqual(target["binding_id"], binding["binding_id"])
            self.assertEqual(target["binding_state"], "active")
            self.assertEqual(target["node_state"], "revoked")
            self.assertEqual(target["workspace_state"], "active")
            self.assertEqual(target["dispatch_state"], "node_revoked")
            self.assertEqual(target["dispatch_blockers"], ["node_revoked"])
            self.assertEqual(target["node_revoked_at_ms"], revoked["revoked_at_ms"])
            self.assertNotIn("canonical_path", json.dumps(response))
            self.assertNotIn("node_secret", json.dumps(response))

            task_open = {
                "jsonrpc": "2.0",
                "id": "oauth-node-revoked-task-open-001",
                "method": "tools/call",
                "params": {"name": "workspace_context", "arguments": {
                    "operation": "task_open",
                    "binding_id": binding["binding_id"],
                    "label": "Must reject revoked node",
                    "idempotency_key": "oauth-node-revoked-task-open-001",
                }},
            }
            status, rejected, _headers = self._mcp_post(
                task_open,
                "Bearer opaque-valid-access-token",
                base_url=candidate_url,
            )
            self.assertEqual(status, 200)
            self.assertEqual(rejected["error"]["data"]["code"], "CONFLICT")
            self.assertIn("no longer dispatchable", rejected["error"]["data"]["message"])
        finally:
            candidate_server.shutdown()
            candidate_server.server_close()
            candidate_thread.join(timeout=2)

    def test_two_clients_same_oauth_principal_share_binding_and_observe_one_task(self) -> None:
        """Different access tokens for one linked account retain one target and task lineage."""

        self.verifier.identities = {
            "client-a-token": self.identity,
            "client-b-token": self.identity,
        }
        binding = self._link_and_target(write=True)
        candidate_server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.store,
            "o" * 40,
            mcp_enabled=True,
            mcp_ingress_only=True,
            mcp_oauth=_configuration(file_read_enabled=True),
            mcp_oauth_verifier=self.verifier,
        )
        candidate_thread = threading.Thread(target=candidate_server.serve_forever, daemon=True)
        candidate_thread.start()
        candidate_url = f"http://127.0.0.1:{candidate_server.server_port}"
        inventory = {
            "jsonrpc": "2.0",
            "id": "shared-account-inventory-001",
            "method": "tools/call",
            "params": {"name": "workspace_context", "arguments": {"operation": "inventory"}},
        }
        seen = []
        try:
            for token in ("client-a-token", "client-b-token"):
                status, response, _headers = self._mcp_post(inventory, f"Bearer {token}", base_url=candidate_url)
                self.assertEqual(status, 200)
                targets = response["result"]["structuredContent"]["targets"]
                self.assertEqual([target["binding_id"] for target in targets], [binding["binding_id"]])
                seen.append(targets[0]["binding_id"])
            self.assertEqual(seen[0], seen[1])

            open_task = {
                "jsonrpc": "2.0",
                "id": "shared-account-task-open-001",
                "method": "tools/call",
                "params": {"name": "workspace_context", "arguments": {
                    "operation": "task_open",
                    "binding_id": binding["binding_id"],
                    "label": "Two client shared task",
                    "idempotency_key": "shared-account-task-open-001",
                }},
            }
            status, opened, _headers = self._mcp_post(open_task, "Bearer client-a-token", base_url=candidate_url)
            self.assertEqual(status, 200)
            task = opened["result"]["structuredContent"]["task"]
            self.assertEqual(task["binding_id"], binding["binding_id"])

            replay_status, replayed, _headers = self._mcp_post(open_task, "Bearer client-b-token", base_url=candidate_url)
            self.assertEqual(replay_status, 200)
            self.assertEqual(replayed["result"]["structuredContent"]["task"]["task_id"], task["task_id"])

            observe = {
                "jsonrpc": "2.0",
                "id": "shared-account-task-observe-001",
                "method": "tools/call",
                "params": {"name": "task_control", "arguments": {
                    "operation": "task_observe", "task_id": task["task_id"],
                }},
            }
            status, observed, _headers = self._mcp_post(observe, "Bearer client-b-token", base_url=candidate_url)
            self.assertEqual(status, 200)
            projection = observed["result"]["structuredContent"]
            self.assertEqual(projection["task"]["binding_id"], binding["binding_id"])
            self.assertNotIn("node_secret", json.dumps(projection))
            self.assertNotIn("arguments_json", json.dumps(projection))
        finally:
            candidate_server.shutdown()
            candidate_server.server_close()
            candidate_thread.join(timeout=2)

    def test_same_account_selects_multiple_bindings_without_retargeting_existing_task(self) -> None:
        """A shared account may choose another host without moving an open task."""

        self.verifier.identities = {
            "client-a-token": self.identity,
            "client-b-token": self.identity,
        }
        binding_a = self._link_and_target(write=True, execute=True, suffix="001")
        binding_b = self._link_and_target(write=True, execute=True, suffix="002")
        candidate_server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.store,
            "o" * 40,
            mcp_enabled=True,
            mcp_ingress_only=True,
            mcp_oauth=_configuration(file_read_enabled=True),
            mcp_oauth_verifier=self.verifier,
        )
        candidate_thread = threading.Thread(target=candidate_server.serve_forever, daemon=True)
        candidate_thread.start()
        candidate_url = f"http://127.0.0.1:{candidate_server.server_port}"

        def call(token: str, request: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            status, response, _headers = self._mcp_post(
                request,
                f"Bearer {token}",
                base_url=candidate_url,
            )
            return status, response

        def inventory(token: str, request_id: str) -> list[dict[str, Any]]:
            status, response = call(token, {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {"name": "workspace_context", "arguments": {"operation": "inventory"}},
            })
            self.assertEqual(status, 200)
            return response["result"]["structuredContent"]["targets"]

        def open_task(token: str, binding_id: str, request_id: str, key: str) -> dict[str, Any]:
            status, response = call(token, {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {"name": "workspace_context", "arguments": {
                    "operation": "task_open",
                    "binding_id": binding_id,
                    "label": request_id,
                    "idempotency_key": key,
                }},
            })
            self.assertEqual(status, 200)
            return response["result"]["structuredContent"]["task"]

        try:
            targets_a = inventory("client-a-token", "multi-binding-inventory-a")
            targets_b = inventory("client-b-token", "multi-binding-inventory-b")
            expected_ids = {binding_a["binding_id"], binding_b["binding_id"]}
            self.assertEqual({target["binding_id"] for target in targets_a}, expected_ids)
            self.assertEqual({target["binding_id"] for target in targets_b}, expected_ids)

            task_a = open_task("client-a-token", binding_a["binding_id"], "multi-binding-task-a", "multi-binding-task-a-key")
            task_b = open_task("client-b-token", binding_b["binding_id"], "multi-binding-task-b", "multi-binding-task-b-key")
            self.assertEqual(task_a["binding_id"], binding_a["binding_id"])
            self.assertEqual(task_b["binding_id"], binding_b["binding_id"])
            self.assertNotEqual(task_a["task_id"], task_b["task_id"])

            status, observed = call("client-b-token", {
                "jsonrpc": "2.0",
                "id": "multi-binding-task-a-observe",
                "method": "tools/call",
                "params": {"name": "task_control", "arguments": {
                    "operation": "task_observe",
                    "task_id": task_a["task_id"],
                }},
            })
            self.assertEqual(status, 200)
            projection = observed["result"]["structuredContent"]
            self.assertEqual(projection["task"]["binding_id"], binding_a["binding_id"])
            self.assertEqual(projection["task"]["device_id"], binding_a["device_id"])
            self.assertNotIn("node_secret", json.dumps(projection))
            self.assertNotIn("canonical_path", json.dumps(projection))
        finally:
            candidate_server.shutdown()
            candidate_server.server_close()
            candidate_thread.join(timeout=2)

    def test_two_clients_same_oauth_principal_handoff_writer_lease_over_http(self) -> None:
        """A shared account serializes mutations across two HTTP clients."""

        self.verifier.identities = {
            "client-a-token": self.identity,
            "client-b-token": self.identity,
        }
        binding = self._link_and_target(write=True)
        candidate_server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.store,
            "o" * 40,
            mcp_enabled=True,
            mcp_ingress_only=True,
            mcp_oauth=_configuration(file_read_enabled=True),
            mcp_oauth_verifier=self.verifier,
        )
        candidate_thread = threading.Thread(target=candidate_server.serve_forever, daemon=True)
        candidate_thread.start()
        candidate_url = f"http://127.0.0.1:{candidate_server.server_port}"

        def call(token: str, request: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            status, response, _headers = self._mcp_post(
                request,
                f"Bearer {token}",
                base_url=candidate_url,
            )
            return status, response

        def task_open(*, token: str, request_id: str, idempotency_key: str, label: str) -> dict[str, Any]:
            status, response = call(
                token,
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "tools/call",
                    "params": {"name": "workspace_context", "arguments": {
                        "operation": "task_open",
                        "binding_id": binding["binding_id"],
                        "label": label,
                        "idempotency_key": idempotency_key,
                    }},
                },
            )
            self.assertEqual(status, 200)
            return response["result"]["structuredContent"]["task"]

        def task_control(*, token: str, request_id: str, operation: str, task_id: str, reason: str | None = None) -> tuple[int, dict[str, Any]]:
            arguments: dict[str, Any] = {"operation": operation, "task_id": task_id}
            if reason is not None:
                arguments["reason"] = reason
            return call(
                token,
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "tools/call",
                    "params": {"name": "task_control", "arguments": arguments},
                },
            )

        try:
            task_a = task_open(
                token="client-a-token",
                request_id="shared-writer-task-a-open-001",
                idempotency_key="shared-writer-task-a-open-001",
                label="Shared writer client A",
            )
            status, claimed_a = task_control(
                token="client-a-token",
                request_id="shared-writer-task-a-claim-001",
                operation="writer_claim",
                task_id=task_a["task_id"],
            )
            self.assertEqual(status, 200)
            lease_a = claimed_a["result"]["structuredContent"]["writer_lease"]
            self.assertEqual(lease_a["state"], "held")
            self.assertEqual(lease_a["lease_generation"], 1)

            task_b = task_open(
                token="client-b-token",
                request_id="shared-writer-task-b-open-001",
                idempotency_key="shared-writer-task-b-open-001",
                label="Shared writer client B",
            )
            self.assertEqual(task_b["binding_id"], binding["binding_id"])
            status, rejected = task_control(
                token="client-b-token",
                request_id="shared-writer-task-b-claim-001",
                operation="writer_claim",
                task_id=task_b["task_id"],
            )
            self.assertEqual(status, 200)
            self.assertEqual(rejected["error"]["data"]["code"], "CONFLICT")
            self.assertIn("another task", rejected["error"]["data"]["message"])

            status, released = task_control(
                token="client-a-token",
                request_id="shared-writer-task-a-release-001",
                operation="writer_release",
                task_id=task_a["task_id"],
                reason="client-handoff",
            )
            self.assertEqual(status, 200)
            lease_released = released["result"]["structuredContent"]["writer_lease"]
            self.assertEqual(lease_released["state"], "released")
            self.assertEqual(lease_released["lease_generation"], 1)

            status, claimed_b = task_control(
                token="client-b-token",
                request_id="shared-writer-task-b-claim-002",
                operation="writer_claim",
                task_id=task_b["task_id"],
            )
            self.assertEqual(status, 200)
            lease_b = claimed_b["result"]["structuredContent"]["writer_lease"]
            self.assertEqual(lease_b["state"], "held")
            # Generations are monotonic per task; the task identity is also
            # sealed into every action, so a new task starts at generation 1
            # without being able to replay task A's authority.
            self.assertEqual(lease_b["lease_generation"], 1)
            self.assertEqual(lease_b["binding_id"], binding["binding_id"])

            serialized = json.dumps(claimed_b)
            self.assertNotIn("node_secret", serialized)
            self.assertNotIn("arguments_json", serialized)
        finally:
            candidate_server.shutdown()
            candidate_server.server_close()
            candidate_thread.join(timeout=2)

    def test_writer_lease_blocks_cross_client_exec_before_dispatch_over_http(self) -> None:
        """A competing task cannot create an exec action before handoff."""

        self.verifier.identities = {
            "client-a-token": self.identity,
            "client-b-token": self.identity,
        }
        binding = self._link_and_target(write=True, execute=True)
        candidate_server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.store,
            "o" * 40,
            mcp_enabled=True,
            mcp_ingress_only=True,
            mcp_oauth=_configuration(
                file_read_enabled=True,
                permission_requests_enabled=True,
                approved_patch_enabled=True,
                exec_enabled=True,
            ),
            mcp_oauth_verifier=self.verifier,
        )
        candidate_thread = threading.Thread(target=candidate_server.serve_forever, daemon=True)
        candidate_thread.start()
        candidate_url = f"http://127.0.0.1:{candidate_server.server_port}"

        def call(token: str, request: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            status, response, _headers = self._mcp_post(
                request,
                f"Bearer {token}",
                base_url=candidate_url,
            )
            return status, response

        try:
            expected_contract = {
                key: candidate_server.mcp_facade.contract[key]
                for key in ("schema_version", "profile", "sha256")
            }

            def open_task(token: str, request_id: str, idempotency_key: str, label: str) -> dict[str, Any]:
                status, response = call(
                    token,
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "method": "tools/call",
                        "params": {"name": "workspace_context", "arguments": {
                            "operation": "task_open",
                            "binding_id": binding["binding_id"],
                            "label": label,
                            "idempotency_key": idempotency_key,
                        }},
                    },
                )
                self.assertEqual(status, 200)
                return response["result"]["structuredContent"]["task"]

            def control(token: str, request_id: str, operation: str, task_id: str) -> tuple[int, dict[str, Any]]:
                return call(
                    token,
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "method": "tools/call",
                        "params": {"name": "task_control", "arguments": {
                            "operation": operation,
                            "task_id": task_id,
                        }},
                    },
                )

            def exec_run(token: str, request_id: str, task_id: str, idempotency_key: str) -> tuple[int, dict[str, Any]]:
                return call(
                    token,
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "method": "tools/call",
                        "params": {"name": "exec_command", "arguments": {
                            "operation": "exec_run",
                            "binding_id": binding["binding_id"],
                            "task_id": task_id,
                            "argv": ["python", "-c", "print('writer-guard')"],
                            "idempotency_key": idempotency_key,
                            "expected_facade_contract": expected_contract,
                        }},
                    },
                )

            task_a = open_task(
                "client-a-token", "shared-exec-task-a-open-001", "shared-exec-task-a-open-001", "Exec writer A"
            )
            status, claimed = control("client-a-token", "shared-exec-task-a-claim-001", "writer_claim", task_a["task_id"])
            self.assertEqual(status, 200)
            self.assertEqual(claimed["result"]["structuredContent"]["writer_lease"]["state"], "held")
            task_b = open_task(
                "client-b-token", "shared-exec-task-b-open-001", "shared-exec-task-b-open-001", "Exec writer B"
            )
            before = self.store.health()["counts"].copy()
            status, rejected = exec_run("client-b-token", "shared-exec-task-b-run-001", task_b["task_id"], "shared-exec-key-001")
            self.assertEqual(status, 200)
            self.assertEqual(rejected["error"]["data"]["code"], "CONFLICT")
            after = self.store.health()["counts"]
            for count_name in ("contexts", "work_requests", "actions"):
                self.assertEqual(after[count_name], before[count_name], count_name)

            status, released = control("client-a-token", "shared-exec-task-a-release-001", "writer_release", task_a["task_id"])
            self.assertEqual(status, 200)
            self.assertEqual(released["result"]["structuredContent"]["writer_lease"]["state"], "released")
            status, accepted = exec_run("client-b-token", "shared-exec-task-b-run-002", task_b["task_id"], "shared-exec-key-001")
            self.assertEqual(status, 200)
            result = accepted["result"]["structuredContent"]
            self.assertEqual(result["task_id"], task_b["task_id"])
            action = self.store.action(owner_id="owner_default", action_id=result["action_id"])
            self.assertEqual(action["delivery_state"], "queued")
            intent = self.store.mcp_exec_intent_for_delivery(action_id=result["action_id"])
            self.assertIsNotNone(intent)
            assert intent is not None
            self.assertEqual(intent["task_id"], task_b["task_id"])
            self.assertEqual(intent["writer_lease_generation"], 1)
        finally:
            candidate_server.shutdown()
            candidate_server.server_close()
            candidate_thread.join(timeout=2)

    def test_task_control_routes_writer_handoff_through_oauth_ingress(self) -> None:
        """A linked account can observe/hand off a task without node secrets."""

        binding = self._link_and_target(write=True)
        candidate_server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.store,
            "o" * 40,
            mcp_enabled=True,
            mcp_ingress_only=True,
            mcp_oauth=_configuration(file_read_enabled=True),
            mcp_oauth_verifier=self.verifier,
        )
        candidate_thread = threading.Thread(target=candidate_server.serve_forever, daemon=True)
        candidate_thread.start()
        candidate_url = f"http://127.0.0.1:{candidate_server.server_port}"
        authorization = "Bearer opaque-valid-access-token"
        try:
            status, listed, _headers = self._mcp_post(
                {"jsonrpc": "2.0", "id": "task-control-tools-001", "method": "tools/list", "params": {}},
                authorization,
                base_url=candidate_url,
            )
            self.assertEqual(status, 200)
            by_name = {tool["name"]: tool for tool in listed["result"]["tools"]}
            self.assertEqual(
                by_name["task_control"]["_meta"]["control_plane"]["implemented_operations"],
                ["task_observe", "writer_claim", "writer_release"],
            )
            task_open = {
                "jsonrpc": "2.0",
                "id": "task-control-open-001",
                "method": "tools/call",
                "params": {"name": "workspace_context", "arguments": {
                    "operation": "task_open",
                    "binding_id": binding["binding_id"],
                    "label": "OAuth handoff",
                    "idempotency_key": "oauth-task-control-open-001",
                }},
            }
            status, opened, _headers = self._mcp_post(task_open, authorization, base_url=candidate_url)
            self.assertEqual(status, 200)
            task_id = opened["result"]["structuredContent"]["task"]["task_id"]
            claim = {
                "jsonrpc": "2.0",
                "id": "task-control-claim-001",
                "method": "tools/call",
                "params": {"name": "task_control", "arguments": {
                    "operation": "writer_claim", "task_id": task_id,
                }},
            }
            status, claimed, _headers = self._mcp_post(claim, authorization, base_url=candidate_url)
            self.assertEqual(status, 200)
            self.assertEqual(claimed["result"]["structuredContent"]["writer_lease"]["state"], "held")
            observe = {
                "jsonrpc": "2.0",
                "id": "task-control-observe-001",
                "method": "tools/call",
                "params": {"name": "task_control", "arguments": {
                    "operation": "task_observe", "task_id": task_id,
                }},
            }
            status, observed, _headers = self._mcp_post(observe, authorization, base_url=candidate_url)
            self.assertEqual(status, 200)
            projection = observed["result"]["structuredContent"]
            self.assertEqual(projection["task"]["binding_id"], binding["binding_id"])
            self.assertNotIn("node_secret", json.dumps(projection))
            self.assertNotIn("arguments_json", json.dumps(projection))
            release = {
                "jsonrpc": "2.0",
                "id": "task-control-release-001",
                "method": "tools/call",
                "params": {"name": "task_control", "arguments": {
                    "operation": "writer_release", "task_id": task_id, "reason": "http-handoff",
                }},
            }
            status, released, _headers = self._mcp_post(release, authorization, base_url=candidate_url)
            self.assertEqual(status, 200)
            self.assertEqual(released["result"]["structuredContent"]["writer_lease"]["state"], "released")
        finally:
            candidate_server.shutdown()
            candidate_server.server_close()
            candidate_thread.join(timeout=2)

    def test_permission_request_candidate_is_wired_through_oauth_http_ingress_without_effect(self) -> None:
        """The HTTP server must preserve the opt-in flag all the way to MCP.

        This is intentionally stronger than a facade-only contract test: the
        OAuth-configured ingress must expose the candidate descriptor and may
        persist a reviewed scope, but it must still be unable to create an
        action, pollable delivery, local policy, or process effect.
        """

        binding = self._link_and_target(write=True)
        authorization = "Bearer opaque-valid-access-token"
        tools_list = {"jsonrpc": "2.0", "id": "oauth-permission-tools-list-001", "method": "tools/list", "params": {}}

        status, baseline, _headers = self._mcp_post(tools_list, authorization)
        self.assertEqual(status, 200)
        baseline_by_name = {tool["name"]: tool for tool in baseline["result"]["tools"]}
        self.assertEqual(
            baseline_by_name["request_permissions"]["_meta"]["control_plane"]["capability_state"],
            "unavailable",
        )

        candidate_server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            self.store,
            "o" * 40,
            mcp_enabled=True,
            mcp_ingress_only=True,
            mcp_oauth=_configuration(file_read_enabled=True, permission_requests_enabled=True),
            mcp_oauth_verifier=self.verifier,
        )
        candidate_thread = threading.Thread(target=candidate_server.serve_forever, daemon=True)
        candidate_thread.start()
        candidate_url = f"http://127.0.0.1:{candidate_server.server_port}"
        try:
            status, listed, _headers = self._mcp_post(tools_list, authorization, base_url=candidate_url)
            self.assertEqual(status, 200)
            by_name = {tool["name"]: tool for tool in listed["result"]["tools"]}
            self.assertEqual(
                by_name["request_permissions"]["_meta"]["control_plane"]["capability_state"],
                "permission_request_candidate",
            )
            self.assertEqual(
                by_name["request_permissions"]["_meta"]["control_plane"]["execution"],
                "no_local_execution",
            )
            self.assertEqual(
                by_name["agent_workflow"]["_meta"]["control_plane"]["capability_state"],
                "unavailable",
            )

            expected_contract = {
                key: candidate_server.mcp_facade.contract[key]
                for key in ("schema_version", "profile", "sha256")
            }
            permission_request = {
                "jsonrpc": "2.0",
                "id": "oauth-permission-request-001",
                "method": "tools/call",
                "params": {
                    "name": "request_permissions",
                    "arguments": {
                        "operation": "request_patch",
                        "binding_id": binding["binding_id"],
                        "path": "src/fixture.txt",
                        "preimage_sha256": "a" * 64,
                        "patch_sha256": "b" * 64,
                        "validation_profile": MCP_PATCH_PERMISSION_VALIDATION_PROFILE,
                        "idempotency_key": "oauth-http-permission-request-0001",
                        "expected_facade_contract": expected_contract,
                    },
                },
            }
            status, response, _headers = self._mcp_post(permission_request, authorization, base_url=candidate_url)
            self.assertEqual(status, 200)
            content = response["result"]["structuredContent"]
            self.assertEqual(content["execution"], "not_started")
            self.assertEqual(content["local_admission"], "not_requested")
            self.assertFalse(content["workspace_accessed"])
            self.assertEqual(content["permission_request"]["state"], "pending")
            self.assertEqual(self.store.health()["counts"]["mcp_permission_requests"], 1)
            self.assertEqual(self.store.health()["counts"]["actions"], 0)
            self.assertEqual(self.store.poll_actions(device_id=binding["device_id"]), [])
        finally:
            candidate_server.shutdown()
            candidate_server.server_close()
            candidate_thread.join(timeout=2)

    def test_modern_oauth_client_origin_uses_bearer_not_private_console_origin(self) -> None:
        """An OpenAI-host Origin is not a Console cookie/CSRF origin.

        OAuth remains the only authentication boundary and this response must
        not become browser-readable via CORS merely because it accepts the
        standard Origin header.
        """

        self._link_and_target()
        request = {
            "jsonrpc": "2.0",
            "id": "oauth-modern-origin-001",
            "method": "tools/call",
            "params": {
                "name": "workspace_context",
                "arguments": {"operation": "inventory"},
                "_meta": {
                    "io.modelcontextprotocol/protocolVersion": STATELESS_MCP_PROTOCOL_VERSION,
                    "io.modelcontextprotocol/clientCapabilities": {},
                    "io.modelcontextprotocol/clientInfo": {"name": "openai-client", "version": "1.0"},
                },
            },
        }
        status, response, headers = self._mcp_post(
            request,
            "Bearer opaque-valid-access-token",
            {
                "Origin": "https://chatgpt.com",
                "MCP-Protocol-Version": STATELESS_MCP_PROTOCOL_VERSION,
                "Mcp-Method": "tools/call",
                "Mcp-Name": "workspace_context",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["result"]["structuredContent"]["observation_kind"], "control_plane_account_target_inventory")
        self.assertEqual(response["result"]["resultType"], "complete")
        self.assertNotIn("access-control-allow-origin", headers)


if __name__ == "__main__":
    unittest.main()
