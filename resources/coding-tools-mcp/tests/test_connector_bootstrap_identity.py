from __future__ import annotations

import unittest
from types import SimpleNamespace

from coding_tools_mcp.http_hub_identity import HTTPHubIdentityMixin
from coding_tools_mcp.connector_attestation import CONNECTOR_ATTESTATION_HEADER, build_connector_attestation


class IdentityProbe(HTTPHubIdentityMixin):
    def __init__(self, headers: dict[str, str], *, secret: str = "") -> None:
        self.headers = headers
        self.runtime = SimpleNamespace(
            http_session_id="",
            execution_context_id="ctx-test",
            connector_attestation_secret=secret or None,
            activation_epoch_id="epoch-test",
            process_instance_id="process-test",
            server_instance_id="server-test",
            tool_contract={"sha256": "a" * 64},
        )


class ConnectorBootstrapIdentityTests(unittest.TestCase):
    def request(self) -> dict:
        return {
            "method": "tools/call",
            "params": {
                "_meta": {
                    "io.modelcontextprotocol/clientInfo": {"name": "ChatGPT", "version": "1"}
                }
            },
        }

    def test_explicit_chatweb_id_without_type_keeps_chatweb_identity(self) -> None:
        for client_id in ("chatweb", "chatweb-bootstrap-123", "chatweb_session", "chatweb:ctx", "chatweb.desktop"):
            identity = IdentityProbe({"X-Coding-Tools-Client-Id": client_id})._hub_identity_from_request(self.request())
            self.assertEqual(identity["client_id"], client_id)
            self.assertEqual(identity["client_type"], "chatweb")
            self.assertEqual(identity["role"], "controller")

    def test_untyped_non_chatweb_id_remains_generic_client(self) -> None:
        identity = IdentityProbe({"X-Coding-Tools-Client-Id": "desktop-123"})._hub_identity_from_request(self.request())
        self.assertEqual(identity["client_type"], "client")
        self.assertEqual(identity["role"], "client")

    def test_explicit_client_type_remains_authoritative(self) -> None:
        identity = IdentityProbe({
            "X-Coding-Tools-Client-Id": "electron-panel",
            "X-Coding-Tools-Client-Type": "electron",
        })._hub_identity_from_request(self.request())
        self.assertEqual(identity["client_type"], "electron")
        self.assertEqual(identity["role"], "supervisor")

    def test_identity_source_distinguishes_transport_headers_from_implicit_defaults(self) -> None:
        explicit = IdentityProbe({
            "X-Coding-Tools-Client-Id": "chatweb",
            "X-Coding-Tools-Client-Type": "chatweb",
        })._hub_identity_from_request(self.request())
        self.assertEqual(explicit["identity_source"], "explicit_headers")

        implicit = IdentityProbe({})._hub_identity_from_request(self.request())
        self.assertEqual(implicit["identity_source"], "implicit_default")
        self.assertEqual(implicit["client_type"], "chatweb")

    def test_attestation_upgrades_explicit_identity_to_managed_transport(self) -> None:
        headers = {
            "X-Coding-Tools-Client-Id": "chatweb",
            "X-Coding-Tools-Client-Type": "chatweb",
        }
        headers[CONNECTOR_ATTESTATION_HEADER] = build_connector_attestation(
            "identity-test-secret",
            client_id="chatweb",
            client_type="chatweb",
            activation_epoch_id="epoch-test",
            process_instance_id="process-test",
            server_instance_id="server-test",
            contract_sha256="a" * 64,
        )
        identity = IdentityProbe(headers, secret="identity-test-secret")._hub_identity_from_request(self.request())
        self.assertEqual(identity["identity_source"], "attested_transport")
        self.assertTrue(identity["attestation_verified"])

    def test_explicit_identity_without_attestation_stays_untrusted(self) -> None:
        identity = IdentityProbe({
            "X-Coding-Tools-Client-Id": "chatweb",
            "X-Coding-Tools-Client-Type": "chatweb",
        }, secret="identity-test-secret")._hub_identity_from_request(self.request())
        self.assertEqual(identity["identity_source"], "explicit_headers")
        self.assertFalse(identity["attestation_verified"])


if __name__ == "__main__":
    unittest.main()
