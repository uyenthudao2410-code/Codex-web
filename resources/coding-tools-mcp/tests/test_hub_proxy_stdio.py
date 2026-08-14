import io
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.hub_proxy_stdio import (
    HEARTBEAT_SECONDS,
    HubProxyClient,
    build_parser,
    serve_proxy_stdio,
    validate_proxy_identity,
)


class FakeGatewayHandler(BaseHTTPRequestHandler):
    server_version = "HubProxyTest/1"

    def log_message(self, _format, *_args):
        return

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(length).decode("utf-8"))
        self.server.observed.append({
            "path": self.path,
            "request": request,
            "authorization": self.headers.get("Authorization"),
            "session": self.headers.get("Mcp-Session-Id"),
            "protocol": self.headers.get("MCP-Protocol-Version"),
            "method": self.headers.get("Mcp-Method"),
            "name": self.headers.get("Mcp-Name"),
            "proxy_client_id": self.headers.get("X-Coding-Tools-Proxy-Client-Id"),
            "proxy_client_type": self.headers.get("X-Coding-Tools-Proxy-Client-Type"),
        })
        if self.headers.get("Authorization") != "Bearer gateway-token-abcdefghijklmnopqrstuvwxyz":
            body = json.dumps({"error": "unauthorized"}).encode()
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/__hub_proxy/heartbeat":
            body = json.dumps({"ok": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if request.get("method") == "initialize":
            payload = {"jsonrpc": "2.0", "id": request.get("id"), "result": {"protocolVersion": "2026-07-28", "capabilities": {}, "serverInfo": {"name": "test", "version": "1"}}}
            session = "session-1"
        elif request.get("method") == "tools/call":
            payload = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [{"type": "text", "text": "workspace_context: completed."}],
                    "structuredContent": {"ok": True, "workspace": "demo", "branch": "main"},
                    "isError": False,
                },
            }
            session = ""
        else:
            payload = {"jsonrpc": "2.0", "id": request.get("id"), "result": {"tools": []}}
            session = ""
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        if session:
            self.send_header("Mcp-Session-Id", session)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class HubProxyStdioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeGatewayHandler)
        self.server.observed = []
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.descriptor = Path(self.temp.name) / "hub-proxy.json"
        self.write_descriptor(self.server.server_address[1], "gateway-token-abcdefghijklmnopqrstuvwxyz")

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temp.cleanup()

    def write_descriptor(self, port, token):
        self.descriptor.write_text(json.dumps({"version": 1, "host": "127.0.0.1", "port": port, "token": token}), encoding="utf-8")

    def test_stdio_proxy_preserves_mcp_session_and_protocol_without_runtime_state(self):
        initialize = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"clientInfo": {"name": "codex", "version": "1"}}}
        tools = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        source = io.StringIO(json.dumps(initialize) + "\n" + json.dumps(tools) + "\n")
        sink = io.StringIO()
        self.assertEqual(serve_proxy_stdio(self.descriptor, input_stream=source, output_stream=sink), 0)
        responses = [json.loads(line) for line in sink.getvalue().splitlines()]
        self.assertEqual([item["id"] for item in responses], [1, 2])
        heartbeats = [item for item in self.server.observed if item["path"] == "/__hub_proxy/heartbeat"]
        mcp_requests = [item for item in self.server.observed if item["path"] == "/mcp"]
        self.assertGreaterEqual(len(heartbeats), 1)
        self.assertLess(HEARTBEAT_SECONDS, 45.0)
        self.assertEqual(len(mcp_requests), 2)
        self.assertEqual(mcp_requests[0]["session"], None)
        self.assertEqual(mcp_requests[1]["session"], "session-1")
        self.assertEqual(mcp_requests[1]["protocol"], "2026-07-28")
        self.assertEqual(mcp_requests[1]["method"], "tools/list")
        self.assertTrue(all(item["proxy_client_id"] == "codex-desktop" for item in self.server.observed))
        self.assertTrue(all(item["proxy_client_type"] == "codex_desktop" for item in self.server.observed))
        self.assertEqual(sorted(path.name for path in Path(self.temp.name).iterdir()), ["hub-proxy.json"])

    def test_opencode_identity_is_forwarded_on_mcp_and_heartbeat(self):
        request = {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}}
        source = io.StringIO(json.dumps(request) + "\n")
        sink = io.StringIO()
        self.assertEqual(
            serve_proxy_stdio(
                self.descriptor,
                input_stream=source,
                output_stream=sink,
                client_id="opencode",
                client_type="opencode",
            ),
            0,
        )
        self.assertTrue(self.server.observed)
        self.assertTrue(all(item["proxy_client_id"] == "opencode" for item in self.server.observed))
        self.assertTrue(all(item["proxy_client_type"] == "opencode" for item in self.server.observed))

    def test_proxy_identity_rejects_non_allowlisted_or_mismatched_pairs(self):
        self.assertEqual(validate_proxy_identity("opencode", "opencode"), ("opencode", "opencode"))
        with self.assertRaises(ValueError):
            validate_proxy_identity("chatweb", "chatweb")
        with self.assertRaises(ValueError):
            validate_proxy_identity("opencode", "codex_desktop")

    def test_descriptor_rotation_drops_old_upstream_session(self):
        client = HubProxyClient(self.descriptor)
        first = client.call({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertIn("result", first)
        self.assertEqual(client.session_id, "session-1")
        self.write_descriptor(self.server.server_address[1], "gateway-token-rotated-abcdefghijklmnopqrstuvwxyz")
        failed = client.call({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        self.assertIn("error", failed)
        self.assertEqual(client.session_id, "")

    def test_missing_descriptor_returns_typed_jsonrpc_error_and_loop_continues(self):
        self.descriptor.unlink()
        source = io.StringIO('{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\nnot-json\n')
        sink = io.StringIO()
        serve_proxy_stdio(self.descriptor, input_stream=source, output_stream=sink)
        responses = [json.loads(line) for line in sink.getvalue().splitlines()]
        self.assertEqual(responses[0]["error"]["code"], -32001)
        self.assertEqual(responses[1]["error"]["code"], -32700)

    def test_parser_uses_appdata_descriptor_when_no_explicit_descriptor_is_configured(self):
        appdata = str(Path(self.temp.name) / "AppData" / "Roaming")
        with patch.dict(os.environ, {"APPDATA": appdata}, clear=True):
            args = build_parser().parse_args([])
        self.assertEqual(
            args.descriptor,
            str(Path(appdata) / "web-mcp-assistant" / "execution-hub-proxy.json"),
        )

    def test_parser_prefers_proxy_descriptor_environment_override_over_appdata(self):
        explicit = str(Path(self.temp.name) / "explicit-descriptor.json")
        with patch.dict(
            os.environ,
            {
                "APPDATA": str(Path(self.temp.name) / "AppData" / "Roaming"),
                "CODING_TOOLS_MCP_PROXY_DESCRIPTOR": explicit,
            },
            clear=True,
        ):
            args = build_parser().parse_args([])
        self.assertEqual(args.descriptor, explicit)

    def test_default_mode_preserves_structured_content(self):
        request = {"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": "workspace_context", "arguments": {}}}
        source = io.StringIO(json.dumps(request) + "\n")
        sink = io.StringIO()
        serve_proxy_stdio(self.descriptor, input_stream=source, output_stream=sink)
        response = json.loads(sink.getvalue())
        self.assertEqual(response["result"]["structuredContent"]["branch"], "main")
        self.assertEqual(response["result"]["content"][0]["text"], "workspace_context: completed.")

    def test_compatibility_mode_mirrors_structured_content_into_text(self):
        request = {"jsonrpc": "2.0", "id": 10, "method": "tools/call", "params": {"name": "workspace_context", "arguments": {}}}
        source = io.StringIO(json.dumps(request) + "\n")
        sink = io.StringIO()
        serve_proxy_stdio(
            self.descriptor,
            input_stream=source,
            output_stream=sink,
            structured_content_as_text=True,
        )
        response = json.loads(sink.getvalue())
        self.assertEqual(
            response["result"]["structuredContent"],
            {"ok": True, "workspace": "demo", "branch": "main"},
        )
        self.assertEqual(
            json.loads(response["result"]["content"][0]["text"]),
            {"ok": True, "workspace": "demo", "branch": "main"},
        )
        self.assertEqual(response["result"]["isError"], False)

    def test_parser_exposes_structured_content_compatibility_flag(self):
        args = build_parser().parse_args(["--structured-content-as-text"])
        self.assertTrue(args.structured_content_as_text)
        self.assertEqual(args.client_id, "codex-desktop")
        self.assertEqual(args.client_type, "codex_desktop")

        open_code = build_parser().parse_args(["--client-id", "opencode", "--client-type", "opencode"])
        self.assertEqual(open_code.client_id, "opencode")
        self.assertEqual(open_code.client_type, "opencode")


if __name__ == "__main__":
    unittest.main()
