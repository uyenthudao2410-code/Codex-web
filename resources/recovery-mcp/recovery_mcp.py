from __future__ import annotations

import argparse
import ctypes
import hmac
import json
import os
import secrets
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

MAX_BODY_BYTES = 64 * 1024
MAX_JSON_BYTES = 128 * 1024
SUPPORTED_PROTOCOLS = ("2024-11-05", "2025-03-26", "2025-06-18")
SERVER_VERSION = "1.0.0"
RECOVERY_PLANE_MODE = "independent_mcp_tunnel_v1"


def process_alive(pid: Any) -> bool:
    try:
        value = int(pid)
    except (TypeError, ValueError):
        return False
    if value <= 0:
        return False
    if os.name == "nt":
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, value)
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(value, 0)
        return True
    except OSError:
        return False


def read_json(path: Path, max_bytes: int = MAX_JSON_BYTES) -> dict[str, Any]:
    try:
        if not path.is_file() or path.stat().st_size > max_bytes:
            return {}
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def public_snapshot(data_root: Path) -> dict[str, Any]:
    host = read_json(data_root / "recovery-host.json", 16 * 1024)
    runtime = read_json(data_root / "runtime-state.json")
    supervisor = read_json(data_root / "recovery-supervisor-status.json")
    plane = read_json(data_root / "recovery-plane-state.json")
    host_pid = host.get("owner_pid")
    native_pid = runtime.get("nativePid")
    tunnel_pid = runtime.get("tunnelPid")
    recovery_mcp_pid = plane.get("recoveryMcpPid")
    recovery_tunnel_pid = plane.get("recoveryTunnelPid")
    activation_epoch_id = str(host.get("activation_epoch_id") or plane.get("activation_epoch_id") or "") or None
    return {
        "device": {"scope": "current_device_only", "device_id": str(host.get("device_id") or plane.get("device_id") or "") or None, "device_instance_id": str(host.get("device_instance_id") or plane.get("device_instance_id") or "") or None, "display_name": str(host.get("device_display_name") or "") or None},
        "activation_epoch_id": activation_epoch_id,
        "recovery_host": {"pid": host_pid if isinstance(host_pid, int) else None, "alive": process_alive(host_pid), "instance_id": str(host.get("instance_id") or "") or None, "activation_epoch_id": str(host.get("activation_epoch_id") or "") or None, "device_id": str(host.get("device_id") or "") or None, "device_instance_id": str(host.get("device_instance_id") or "") or None},
        "primary_runtime": {
            "coding_mcp_pid": native_pid if isinstance(native_pid, int) else None,
            "coding_mcp_alive": process_alive(native_pid),
            "coding_mcp_instance_id": str(runtime.get("nativeInstanceId") or "") or None,
            "coding_mcp_activation_epoch_id": str(runtime.get("nativeActivationEpochId") or "") or None,
            "coding_tunnel_pid": tunnel_pid if isinstance(tunnel_pid, int) else None,
            "coding_tunnel_alive": process_alive(tunnel_pid),
            "coding_tunnel_instance_id": str(runtime.get("tunnelInstanceId") or "") or None,
            "coding_tunnel_activation_epoch_id": str(runtime.get("tunnelActivationEpochId") or "") or None,
        },
        "recovery_plane": {
            "recovery_mcp_pid": recovery_mcp_pid if isinstance(recovery_mcp_pid, int) else None,
            "recovery_mcp_alive": process_alive(recovery_mcp_pid),
            "recovery_mcp_instance_id": str(plane.get("recoveryMcpInstanceId") or "") or None,
            "recovery_mcp_activation_epoch_id": str(plane.get("recoveryMcpActivationEpochId") or "") or None,
            "recovery_tunnel_pid": recovery_tunnel_pid if isinstance(recovery_tunnel_pid, int) else None,
            "recovery_tunnel_alive": process_alive(recovery_tunnel_pid),
            "recovery_tunnel_instance_id": str(plane.get("recoveryTunnelInstanceId") or "") or None,
            "recovery_tunnel_activation_epoch_id": str(plane.get("recoveryTunnelActivationEpochId") or "") or None,
            "recovery_tunnel_configured": bool(plane.get("recoveryTunnelConfigured")),
            "recovery_tunnel_state": str(plane.get("recoveryTunnelState") or "unknown"),
        },
        "supervisor": {
            "state": str(supervisor.get("state") or "unknown"),
            "pid": supervisor.get("supervisor_pid") if isinstance(supervisor.get("supervisor_pid"), int) else None,
            "last_error_code": str(supervisor.get("last_error_code") or "") or None,
        },
    }


def recovery_host_call(data_root: Path, action: str, expected_device_id: str = "", expected_device_instance_id: str = "") -> dict[str, Any]:
    if action != "health.repair":
        raise RuntimeError("Recovery MCP only permits the fixed health.repair action.")
    descriptor = read_json(data_root / "recovery-host.json", 16 * 1024)
    if descriptor.get("version") != 1 or descriptor.get("host") != "127.0.0.1" or descriptor.get("owner") != "recovery-host" or not process_alive(descriptor.get("owner_pid")):
        raise RuntimeError("Recovery Host descriptor identity is unavailable.")
    if expected_device_id and str(descriptor.get("device_id") or "") != expected_device_id:
        raise RuntimeError("Recovery Host descriptor belongs to another device.")
    if expected_device_instance_id and str(descriptor.get("device_instance_id") or "") != expected_device_instance_id:
        raise RuntimeError("Recovery Host descriptor belongs to another device lifecycle.")
    try:
        port = int(descriptor.get("port"))
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Recovery Host descriptor port is invalid.") from exc
    token = str(descriptor.get("token") or "")
    if port < 1 or port > 65535 or len(token) < 32:
        raise RuntimeError("Recovery Host descriptor is incomplete.")
    body = json.dumps({"action": action, "args": []}, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(f"http://127.0.0.1:{port}/v1/call", data=body, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, method="POST")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=5) as response:
            payload = response.read(MAX_JSON_BYTES + 1)
    except (OSError, urllib.error.URLError) as exc:
        raise RuntimeError("Recovery Host repair RPC is unavailable.") from exc
    if len(payload) > MAX_JSON_BYTES:
        raise RuntimeError("Recovery Host repair response exceeded the bounded size.")
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise RuntimeError("Recovery Host repair response is invalid.") from exc
    if not isinstance(value, dict) or value.get("ok") is not True:
        message = value.get("error", {}).get("message") if isinstance(value, dict) else None
        raise RuntimeError(str(message or "Recovery Host repair was refused."))
    return public_snapshot(data_root)


def tools() -> list[dict[str, Any]]:
    return [
        {
            "name": "recovery_status",
            "description": "Read secret-free Recovery Host, primary runtime, supervisor, and recovery-plane liveness.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
        },
        {
            "name": "repair_primary_runtime",
            "description": "Request the existing Recovery Host health.repair workflow for primary Coding MCP/Tunnel. Requires confirm=true.",
            "inputSchema": {"type": "object", "properties": {"confirm": {"type": "boolean", "const": True}}, "required": ["confirm"], "additionalProperties": False},
            "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False},
        },
    ]


def tool_result(value: dict[str, Any]) -> dict[str, Any]:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return {"content": [{"type": "text", "text": text}], "structuredContent": value, "isError": False}


class RecoveryMcpServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], token: str, data_root: Path, device_id: str = "", device_instance_id: str = "", device_display_name: str = "", activation_epoch_id: str = "", instance_id: str = ""):
        super().__init__(address, RecoveryMcpHandler)
        self.auth_token = token
        self.data_root = data_root
        self.device_id = device_id
        self.device_instance_id = device_instance_id
        self.device_display_name = device_display_name
        self.activation_epoch_id = activation_epoch_id
        # A fresh per-process identity is generated by the Recovery Plane
        # supervisor and passed through the environment.  Do not derive this
        # from the durable state file: that would allow a replacement process
        # to appear healthy while still carrying an old runtime identity.
        self.instance_id = instance_id
        self.session_id = secrets.token_urlsafe(24)


class RecoveryMcpHandler(BaseHTTPRequestHandler):
    server: RecoveryMcpServer
    protocol_version = "HTTP/1.1"

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _send_json(self, status: int, value: Any, *, session: bool = False, close: bool = False) -> None:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        if close:
            self.send_header("Connection", "close")
            self.close_connection = True
        if session:
            self.send_header("Mcp-Session-Id", self.server.session_id)
        self.end_headers()
        self.wfile.write(payload)

    def _authorized(self) -> bool:
        return hmac.compare_digest(self.headers.get("Authorization", ""), f"Bearer {self.server.auth_token}")

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/healthz":
            self._send_json(404, {"error": "not_found"})
            return
        self._send_json(200, {"ok": True, "service": "recovery-mcp", "mode": RECOVERY_PLANE_MODE, "pid": os.getpid(), "instance_id": self.server.instance_id or None, "device_id": self.server.device_id or None, "device_instance_id": self.server.device_instance_id or None, "device_display_name": self.server.device_display_name or None, "activation_epoch_id": self.server.activation_epoch_id or None})

    def do_DELETE(self) -> None:  # noqa: N802
        if self.path != "/mcp":
            self._send_json(404, {"error": "not_found"})
            return
        if not self._authorized():
            self._send_json(401, {"error": "unauthorized"})
            return
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/mcp":
            self._send_json(404, {"error": "not_found"}, close=True)
            return
        if not self._authorized():
            self._send_json(401, {"error": "unauthorized"}, close=True)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "invalid_content_length"}, close=True)
            return
        if length <= 0 or length > MAX_BODY_BYTES:
            self._send_json(413, {"error": "body_too_large"}, close=True)
            return
        try:
            request = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            self._send_json(400, {"error": "invalid_json"})
            return
        if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" or not isinstance(request.get("method"), str):
            self._send_json(400, {"error": "invalid_jsonrpc"})
            return
        response = self._handle_rpc(request)
        if response is None:
            self.send_response(202)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._send_json(200, response, session=request.get("method") == "initialize")

    def _handle_rpc(self, request: dict[str, Any]) -> dict[str, Any] | None:
        request_id = request.get("id")
        method = request["method"]
        params = request.get("params") if isinstance(request.get("params"), dict) else {}
        try:
            if method == "initialize":
                requested = str(params.get("protocolVersion") or "")
                protocol = requested if requested in SUPPORTED_PROTOCOLS else SUPPORTED_PROTOCOLS[-1]
                result = {"protocolVersion": protocol, "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "webmcp-recovery", "title": "WebMCP Recovery", "version": SERVER_VERSION}}
            elif method in {"notifications/initialized", "notifications/cancelled"}:
                return None
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": tools()}
            elif method == "tools/call":
                name = params.get("name")
                arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
                if name == "recovery_status":
                    result = tool_result(public_snapshot(self.server.data_root))
                elif name == "repair_primary_runtime":
                    if arguments.get("confirm") is not True:
                        raise ValueError("repair_primary_runtime requires confirm=true")
                    result = tool_result(recovery_host_call(self.server.data_root, "health.repair", self.server.device_id, self.server.device_instance_id))
                else:
                    raise KeyError("Unknown Recovery MCP tool")
            else:
                return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found"}}
            if request_id is None:
                return None
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except (KeyError, ValueError, RuntimeError) as exc:
            if request_id is None:
                return None
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": str(exc)}}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minimal independent WebMCP recovery plane")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--data-root", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.host != "127.0.0.1" or args.port < 1024 or args.port > 65535:
        raise SystemExit("Recovery MCP only supports 127.0.0.1 and a non-privileged valid port.")
    token = os.environ.get("WEBCODEX_RECOVERY_AUTH_TOKEN", "")
    if len(token) < 32:
        raise SystemExit("WEBCODEX_RECOVERY_AUTH_TOKEN is required.")
    data_root = Path(args.data_root).resolve()
    data_root.mkdir(parents=True, exist_ok=True)
    server = RecoveryMcpServer((args.host, args.port), token, data_root, os.environ.get("WEBCODEX_RECOVERY_DEVICE_ID", "").strip(), os.environ.get("WEBCODEX_RECOVERY_DEVICE_INSTANCE_ID", "").strip(), os.environ.get("WEBCODEX_RECOVERY_DEVICE_DISPLAY_NAME", "").strip()[:120], os.environ.get("WEBCODEX_ACTIVATION_EPOCH_ID", "").strip(), os.environ.get("WEBCODEX_RECOVERY_MCP_INSTANCE_ID", "").strip())
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
