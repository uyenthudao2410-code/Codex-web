from __future__ import annotations

import unittest
from types import SimpleNamespace

from coding_tools_mcp.http_hub_identity import HTTPHubIdentityMixin


class IdentityProbe(HTTPHubIdentityMixin):
    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers
        self.runtime = SimpleNamespace(http_session_id="", execution_context_id="ctx-test")


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


if __name__ == "__main__":
    unittest.main()
