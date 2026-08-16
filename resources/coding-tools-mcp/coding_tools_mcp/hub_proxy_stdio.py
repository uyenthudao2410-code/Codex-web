from __future__ import annotations

import argparse
import http.client
import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, TextIO

MAX_LINE_BYTES = 1024 * 1024
HEARTBEAT_SECONDS = 15.0
DEFAULT_PROXY_CLIENT_ID = "codex-desktop"
DEFAULT_PROXY_CLIENT_TYPE = "codex_desktop"
PROXY_CLIENT_ID_HEADER = "X-Coding-Tools-Proxy-Client-Id"
PROXY_CLIENT_TYPE_HEADER = "X-Coding-Tools-Proxy-Client-Type"
ALLOWED_PROXY_CLIENTS = frozenset({
    (DEFAULT_PROXY_CLIENT_ID, DEFAULT_PROXY_CLIENT_TYPE),
    ("opencode", "opencode"),
})


def validate_proxy_identity(client_id: str, client_type: str) -> tuple[str, str]:
    identity = (str(client_id or "").strip(), str(client_type or "").strip())
    if identity not in ALLOWED_PROXY_CLIENTS:
        raise ValueError("Execution Hub proxy client identity is not allowlisted")
    return identity


def jsonrpc_error(request_id: Any, code: int, message: str, *, data: dict[str, Any] | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def request_id(request: Any) -> Any:
    return request.get("id") if isinstance(request, dict) else None


def mcp_name(request: dict[str, Any]) -> str:
    params = request.get("params") if isinstance(request.get("params"), dict) else {}
    value = params.get("name")
    return str(value) if isinstance(value, str) else ""


def structured_content_to_text(response: dict[str, Any]) -> dict[str, Any]:
    """Adapt MCP tool results for clients that ignore structuredContent.

    This is intentionally opt-in at the stdio proxy boundary. The canonical
    MCP response remains unchanged unless a frontend explicitly requests the
    compatibility mode. Keep structuredContent intact for MCP output-schema
    validation, and mirror the same payload into text for clients whose model
    presentation ignores structuredContent. Non-text content remains intact.
    """
    result = response.get("result")
    if not isinstance(result, dict) or "structuredContent" not in result:
        return response
    structured = result.get("structuredContent")
    if structured is None:
        return response
    text = json.dumps(structured, ensure_ascii=False, separators=(",", ":"))
    content = result.get("content")
    non_text_content = [
        item
        for item in (content if isinstance(content, list) else [])
        if isinstance(item, dict) and item.get("type") != "text"
    ]
    result["content"] = [{"type": "text", "text": text}, *non_text_content]
    return response


class HubProxyClient:
    def __init__(
        self,
        descriptor_path: Path,
        *,
        timeout_seconds: float = 35.0,
        client_id: str = DEFAULT_PROXY_CLIENT_ID,
        client_type: str = DEFAULT_PROXY_CLIENT_TYPE,
    ) -> None:
        self.descriptor_path = descriptor_path
        self.timeout_seconds = max(1.0, float(timeout_seconds))
        self.client_id, self.client_type = validate_proxy_identity(client_id, client_type)
        self.session_id = ""
        self.protocol_version = ""
        self._descriptor_identity = ""

    def _load_descriptor(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.descriptor_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("Execution Hub local gateway descriptor is unavailable") from exc
        if not isinstance(payload, dict) or payload.get("version") != 1:
            raise RuntimeError("Execution Hub local gateway descriptor is invalid")
        host = str(payload.get("host") or "")
        port = int(payload.get("port") or 0)
        token = str(payload.get("token") or "")
        if host not in {"127.0.0.1", "localhost"} or not (1 <= port <= 65535) or len(token) < 32:
            raise RuntimeError("Execution Hub local gateway descriptor is invalid")
        identity = f"{host}:{port}:{token}"
        if self._descriptor_identity and identity != self._descriptor_identity:
            self.session_id = ""
            self.protocol_version = ""
        self._descriptor_identity = identity
        return {"host": host, "port": port, "token": token}

    def call(self, request: dict[str, Any]) -> dict[str, Any] | None:
        try:
            descriptor = self._load_descriptor()
        except RuntimeError:
            return jsonrpc_error(request_id(request), -32001, "Execution Hub local gateway is unavailable")
        body = json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(body) > MAX_LINE_BYTES:
            return jsonrpc_error(request_id(request), -32600, "Request exceeds Execution Hub proxy limit")
        headers = {
            "Authorization": f"Bearer {descriptor['token']}",
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
            "Mcp-Method": str(request.get("method") or ""),
            PROXY_CLIENT_ID_HEADER: self.client_id,
            PROXY_CLIENT_TYPE_HEADER: self.client_type,
        }
        name = mcp_name(request)
        if name:
            headers["Mcp-Name"] = name
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        if self.protocol_version:
            headers["MCP-Protocol-Version"] = self.protocol_version
        connection = http.client.HTTPConnection(descriptor["host"], descriptor["port"], timeout=self.timeout_seconds)
        try:
            connection.request("POST", "/mcp", body=body, headers=headers)
            response = connection.getresponse()
            raw = response.read(MAX_LINE_BYTES + 1)
            if len(raw) > MAX_LINE_BYTES:
                return jsonrpc_error(request_id(request), -32001, "Execution Hub proxy response exceeded limit")
            if response.getheader("Mcp-Session-Id"):
                self.session_id = str(response.getheader("Mcp-Session-Id"))
            if not raw:
                return None
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return jsonrpc_error(request_id(request), -32001, "Execution Hub gateway returned invalid JSON")
            if response.status >= 400:
                return jsonrpc_error(
                    request_id(request),
                    -32001,
                    "Execution Hub gateway is unavailable",
                    data={"http_status": response.status},
                )
            if isinstance(payload, dict) and request.get("method") == "initialize":
                result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
                version = str(result.get("protocolVersion") or "")
                if version:
                    self.protocol_version = version
            return payload if isinstance(payload, dict) else jsonrpc_error(request_id(request), -32001, "Execution Hub gateway returned invalid response")
        except (OSError, http.client.HTTPException):
            return jsonrpc_error(request_id(request), -32001, "Execution Hub local gateway is unavailable")
        finally:
            connection.close()

    def heartbeat(self) -> bool:
        try:
            descriptor = self._load_descriptor()
        except RuntimeError:
            return False
        body = b"{}"
        connection = http.client.HTTPConnection(descriptor["host"], descriptor["port"], timeout=min(5.0, self.timeout_seconds))
        try:
            connection.request(
                "POST",
                "/__hub_proxy/heartbeat",
                body=body,
                headers={
                    "Authorization": f"Bearer {descriptor['token']}",
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body)),
                    PROXY_CLIENT_ID_HEADER: self.client_id,
                    PROXY_CLIENT_TYPE_HEADER: self.client_type,
                },
            )
            response = connection.getresponse()
            response.read(MAX_LINE_BYTES + 1)
            return 200 <= response.status < 300
        except (OSError, http.client.HTTPException):
            return False
        finally:
            connection.close()


def serve_proxy_stdio(
    descriptor_path: Path,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
    structured_content_as_text: bool = False,
    client_id: str = DEFAULT_PROXY_CLIENT_ID,
    client_type: str = DEFAULT_PROXY_CLIENT_TYPE,
) -> int:
    source = input_stream or sys.stdin
    sink = output_stream or sys.stdout
    client = HubProxyClient(descriptor_path, client_id=client_id, client_type=client_type)
    stop_heartbeat = threading.Event()

    def heartbeat_loop() -> None:
        client.heartbeat()
        while not stop_heartbeat.wait(HEARTBEAT_SECONDS):
            client.heartbeat()

    heartbeat_thread = threading.Thread(target=heartbeat_loop, name="coding-tools-hub-heartbeat", daemon=True)
    heartbeat_thread.start()
    try:
        for line in source:
            if not line.strip():
                continue
            if len(line.encode("utf-8", errors="replace")) > MAX_LINE_BYTES:
                response = jsonrpc_error(None, -32600, "Request exceeds Execution Hub proxy limit")
            else:
                try:
                    request = json.loads(line)
                except json.JSONDecodeError:
                    response = jsonrpc_error(None, -32700, "Parse error")
                else:
                    response = client.call(request) if isinstance(request, dict) else jsonrpc_error(None, -32600, "Invalid Request")
            if response is not None:
                if structured_content_as_text:
                    response = structured_content_to_text(response)
                encoded = json.dumps(response, ensure_ascii=False, separators=(",", ":"))
                if len(encoded.encode("utf-8")) > MAX_LINE_BYTES:
                    encoded = json.dumps(
                        jsonrpc_error(request_id(request) if isinstance(request, dict) else None, -32001, "Execution Hub proxy response exceeded compatibility limit"),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                sink.write(encoded + "\n")
                sink.flush()
    finally:
        stop_heartbeat.set()
        heartbeat_thread.join(timeout=0.5)
    return 0


def default_descriptor_path() -> str:
    configured = str(os.environ.get("CODING_TOOLS_MCP_PROXY_DESCRIPTOR") or "").strip()
    if configured:
        return configured
    appdata = str(os.environ.get("APPDATA") or "").strip()
    if not appdata:
        return ""
    return str(Path(appdata).expanduser() / "web-mcp-assistant" / "execution-hub-proxy.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Forward local MCP stdio clients to the Recovery Host-owned Coding Tools Runtime.")
    parser.add_argument(
        "--descriptor",
        default=default_descriptor_path(),
        help="Recovery Host Execution Hub proxy descriptor path",
    )
    parser.add_argument(
        "--structured-content-as-text",
        action="store_true",
        help="Mirror tools/call structuredContent into a text content block for MCP clients that ignore structuredContent",
    )
    parser.add_argument("--client-id", default=DEFAULT_PROXY_CLIENT_ID, help="Allowlisted local Execution Hub client id")
    parser.add_argument("--client-type", default=DEFAULT_PROXY_CLIENT_TYPE, help="Allowlisted local Execution Hub client type")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    descriptor = str(args.descriptor or "").strip()
    if not descriptor:
        print(
            "ERROR: --descriptor, CODING_TOOLS_MCP_PROXY_DESCRIPTOR, or an APPDATA-based descriptor is required",
            file=sys.stderr,
        )
        return 2
    try:
        return serve_proxy_stdio(
            Path(descriptor).expanduser(),
            structured_content_as_text=bool(args.structured_content_as_text),
            client_id=str(args.client_id or ""),
            client_type=str(args.client_type or ""),
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
