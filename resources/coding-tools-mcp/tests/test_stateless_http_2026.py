from __future__ import annotations

import http.client
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.protocol import STATELESS_PROTOCOL_VERSION
from coding_tools_mcp.server import MCPHandler, Runtime, RuntimeHTTPServer


EXPECTED_SMART_TOOLS = {
    "workspace_context",
    "agent_workflow",
    "task_control",
    "document_workflow",
    "exec_command",
    "command_control",
    "request_permissions",
    "view_image",
}


def modern_params(extra: dict | None = None) -> dict:
    payload = dict(extra or {})
    payload["_meta"] = {
        "io.modelcontextprotocol/protocolVersion": STATELESS_PROTOCOL_VERSION,
        "io.modelcontextprotocol/clientCapabilities": {},
        "io.modelcontextprotocol/clientInfo": {"name": "raw-canary", "version": "1"},
    }
    return payload


class StatelessHttp2026Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(
            os.environ,
            {
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_STATELESS_HTTP_2026": "1",
            },
        )
        self.env.start()
        self.runtime = Runtime(Path(self.temp.name), transport="http")
        self.server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, self.runtime, runtime_factory=None)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = int(self.server.server_address[1])

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.assertFalse(self.thread.is_alive())
        self.env.stop()
        self.temp.cleanup()

    def request(self, method: str, params: dict, *, request_id: int = 1, extra_headers: dict[str, str] | None = None) -> tuple[int, dict[str, str], dict]:
        headers = {
            "Content-Type": "application/json",
            "MCP-Protocol-Version": STATELESS_PROTOCOL_VERSION,
            "Mcp-Method": method,
        }
        headers.update(extra_headers or {})
        body = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}).encode("utf-8")
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("POST", "/mcp", body=body, headers=headers)
            response = connection.getresponse()
            raw = response.read()
            decoded = json.loads(raw.decode("utf-8")) if raw else {}
            return response.status, {key.lower(): value for key, value in response.getheaders()}, decoded
        finally:
            connection.close()

    def test_discover_and_tools_list_are_stateless_and_self_describing(self) -> None:
        status, headers, body = self.request("server/discover", modern_params())
        self.assertEqual(status, 200)
        self.assertNotIn("mcp-session-id", headers)
        result = body["result"]
        self.assertIn(STATELESS_PROTOCOL_VERSION, result["supportedVersions"])
        self.assertEqual(result["resultType"], "complete")
        self.assertEqual(result["ttlMs"], 0)
        self.assertEqual(result["cacheScope"], "private")
        self.assertEqual(result["_meta"]["io.modelcontextprotocol/serverInfo"]["name"], "coding-tools-mcp")

        status, headers, body = self.request("tools/list", modern_params(), request_id=2)
        self.assertEqual(status, 200)
        self.assertNotIn("mcp-session-id", headers)
        self.assertEqual({tool["name"] for tool in body["result"]["tools"]}, EXPECTED_SMART_TOOLS)
        self.assertEqual(body["result"]["resultType"], "complete")

    def test_tools_call_ignores_legacy_session_header_and_never_echoes_it(self) -> None:
        status, headers, body = self.request(
            "tools/call",
            modern_params({"name": "workspace_context", "arguments": {"detail": "compact", "path": "."}}),
            request_id=3,
            extra_headers={"Mcp-Name": "workspace_context", "Mcp-Session-Id": "legacy-session-must-be-ignored"},
        )
        self.assertEqual(status, 200)
        self.assertNotIn("mcp-session-id", headers)
        self.assertEqual(body["result"]["resultType"], "complete")
        self.assertFalse(body["result"]["isError"])

    def test_header_and_meta_contract_fail_closed(self) -> None:
        status, _, body = self.request("tools/list", modern_params(), extra_headers={"Mcp-Method": "wrong/method"})
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], -32020)

        missing_caps = {"_meta": {"io.modelcontextprotocol/protocolVersion": STATELESS_PROTOCOL_VERSION}}
        status, _, body = self.request("tools/list", missing_caps, request_id=4)
        self.assertEqual(status, 200)
        self.assertEqual(body["error"]["code"], -32602)

        status, _, body = self.request("tools/call", modern_params({"name": "workspace_context", "arguments": {}}), request_id=5)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], -32020)

    def test_modern_initialize_is_removed(self) -> None:
        status, headers, body = self.request("initialize", modern_params(), request_id=6)
        self.assertEqual(status, 404)
        self.assertNotIn("mcp-session-id", headers)
        self.assertEqual(body["error"]["code"], -32601)

    def test_canary_disabled_rejects_modern_request_without_affecting_legacy_default(self) -> None:
        with patch.dict(os.environ, {"CODING_TOOLS_MCP_STATELESS_HTTP_2026": "0"}):
            status, headers, body = self.request("tools/list", modern_params(), request_id=7)
        self.assertEqual(status, 400)
        self.assertNotIn("mcp-session-id", headers)
        self.assertEqual(body["error"]["code"], -32022)


if __name__ == "__main__":
    unittest.main()
