from __future__ import annotations

from typing import Any

from .endpoint_identity import (
    ENDPOINT_META_KEY,
    ENDPOINT_ROUTING_INSTRUCTIONS_META_KEY,
    endpoint_identity_payload,
    endpoint_routing_instructions,
    endpoint_server_title,
)
from .errors import JsonRpcError, normalize_exception_group


PROTOCOL_VERSION = "2025-11-25"
STATELESS_PROTOCOL_VERSION = "2026-07-28"
LEGACY_PROTOCOL_VERSIONS = (PROTOCOL_VERSION, "2025-06-18", "2025-03-26")
SUPPORTED_PROTOCOL_VERSIONS = (STATELESS_PROTOCOL_VERSION, *LEGACY_PROTOCOL_VERSIONS)


def jsonrpc_error(
    request_id: str | int | None, code: int, message: str, data: Any = None
) -> dict[str, Any]:
    """Build a JSON-RPC error response envelope."""
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def invalid_request_response() -> dict[str, Any]:
    return jsonrpc_error(None, -32600, "Invalid Request")


def response_id(request: dict[str, Any]) -> str | int | None:
    """Return a response-safe JSON-RPC id, using null for invalid or absent ids."""

    value = request.get("id")
    if isinstance(value, str) or (isinstance(value, int) and not isinstance(value, bool)):
        return value
    return None


def validate_rpc_envelope(request: dict[str, Any]) -> None:
    if request.get("jsonrpc") != "2.0":
        raise JsonRpcError(-32600, "Invalid Request: jsonrpc must be 2.0", {"reason": "jsonrpc_version"})
    method = request.get("method")
    if not isinstance(method, str) or not method:
        raise JsonRpcError(-32600, "Invalid Request: method must be a string", {"reason": "method"})
    if "id" in request and not (
        request["id"] is None
        or isinstance(request["id"], str)
        or (isinstance(request["id"], int) and not isinstance(request["id"], bool))
    ):
        raise JsonRpcError(-32600, "Invalid Request: id must be string, integer, or null", {"reason": "id"})


def rpc_params(request: dict[str, Any]) -> dict[str, Any]:
    params = request.get("params", {})
    if params is None:
        return {}
    if not isinstance(params, dict):
        raise JsonRpcError(-32602, "MCP method params must be an object")
    return params


def validate_initialize_params(params: dict[str, Any]) -> str:
    requested = params.get("protocolVersion")
    if requested is None:
        return PROTOCOL_VERSION
    if not legacy_protocol_version_is_supported(requested):
        raise JsonRpcError(
            -32602,
            "Unsupported MCP protocol version",
            {"supported": list(LEGACY_PROTOCOL_VERSIONS), "received": requested},
        )
    return str(requested)


def validate_initialize_request(request: dict[str, Any]) -> None:
    if "id" not in request or request.get("id") is None:
        raise JsonRpcError(-32600, "initialize must be a JSON-RPC request with a non-null id")


def protocol_version_is_supported(version: Any) -> bool:
    return isinstance(version, str) and version in SUPPORTED_PROTOCOL_VERSIONS


def legacy_protocol_version_is_supported(version: Any) -> bool:
    return isinstance(version, str) and version in LEGACY_PROTOCOL_VERSIONS


def request_protocol_version(request: dict[str, Any]) -> str | None:
    params = request.get("params")
    if not isinstance(params, dict):
        return None
    meta = params.get("_meta")
    if not isinstance(meta, dict):
        return None
    value = meta.get("io.modelcontextprotocol/protocolVersion")
    return value if isinstance(value, str) else None


def validate_stateless_request_meta(request: dict[str, Any]) -> None:
    params = rpc_params(request)
    meta = params.get("_meta")
    if not isinstance(meta, dict):
        raise JsonRpcError(-32602, "Invalid params: MCP 2026-07-28 requests require params._meta")
    version = meta.get("io.modelcontextprotocol/protocolVersion")
    if version != STATELESS_PROTOCOL_VERSION:
        raise JsonRpcError(-32602, "Invalid params: MCP 2026-07-28 requests require matching params._meta protocolVersion")
    if request.get("id") is not None:
        capabilities = meta.get("io.modelcontextprotocol/clientCapabilities")
        if not isinstance(capabilities, dict):
            raise JsonRpcError(-32602, "Invalid params: MCP 2026-07-28 requests require params._meta clientCapabilities")
        client_info = meta.get("io.modelcontextprotocol/clientInfo")
        if client_info is not None and not (
            isinstance(client_info, dict)
            and isinstance(client_info.get("name"), str)
            and isinstance(client_info.get("version"), str)
        ):
            raise JsonRpcError(-32602, "Invalid params: params._meta clientInfo must contain string name and version fields when present")


def _stateless_result(runtime: Any, result: dict[str, Any], *, cacheable: bool) -> dict[str, Any]:
    decorated = dict(result)
    decorated.setdefault("resultType", "complete")
    if cacheable:
        decorated.setdefault("ttlMs", 0)
        decorated.setdefault("cacheScope", "private")
    meta = decorated.get("_meta")
    if not isinstance(meta, dict):
        meta = {}
        decorated["_meta"] = meta
    server_info = runtime.server_info_payload()
    endpoint = server_info.get("endpoint")
    if not isinstance(endpoint, dict):
        endpoint = endpoint_identity_payload(runtime)
    meta.setdefault("io.modelcontextprotocol/serverInfo", {
        "name": "coding-tools-mcp",
        "title": str(server_info.get("title") or endpoint_server_title(endpoint)),
        "version": str(server_info.get("version", "")),
    })
    meta.setdefault(ENDPOINT_META_KEY, endpoint)
    meta.setdefault(
        ENDPOINT_ROUTING_INSTRUCTIONS_META_KEY,
        endpoint_routing_instructions(endpoint),
    )
    return decorated


def dispatch_rpc(
    runtime: Any,
    request: dict[str, Any],
    *,
    stateless_2026: bool = False,
) -> dict[str, Any] | None:
    """Dispatch one MCP JSON-RPC request against a runtime, shared by all transports.

    Handshake state lives on ``runtime.initialized``; transports add only their
    transport-specific framing (session headers, stream handling) around this.
    Returns None for notifications and requests without an id.
    """

    request_id = request.get("id")
    try:
        validate_rpc_envelope(request)
        method = request["method"]
        params = rpc_params(request)
        if stateless_2026:
            validate_stateless_request_meta(request)
        if not stateless_2026 and not runtime.initialized and method not in {"initialize", "ping", "server/discover"}:
            raise JsonRpcError(-32002, "Server not initialized")
        if method == "server/discover" and stateless_2026:
            # Stateless MCP clients can obtain the public tool inventory through
            # server/discover without issuing a separate tools/list request.
            # Record that real client contact under the same process/contract
            # binding as tools/list, while preserving the discover response
            # shape and its cache contract.
            runtime.list_tools()
            result = _stateless_result(
                runtime,
                {
                    "supportedVersions": list(SUPPORTED_PROTOCOL_VERSIONS),
                    "capabilities": {"tools": {"listChanged": False}},
                },
                cacheable=True,
            )
        elif stateless_2026 and method in {"initialize", "ping", "notifications/initialized", "notifications/cancelled"}:
            raise JsonRpcError(-32601, f"Unknown method: {method}")
        elif method == "initialize":
            validate_initialize_request(request)
            runtime.protocol_version = validate_initialize_params(params)
            client_info = params.get("clientInfo")
            result = runtime.initialize(client_info if isinstance(client_info, dict) else None)
            # The negotiated version recorded above is authoritative for the
            # session: HTTP session checks compare later MCP-Protocol-Version
            # headers against it. Runtime.initialize() can read the version
            # through a shared-runtime delegate (HTTPSessionRuntimeView),
            # which still holds the server default, so pin the result to the
            # negotiated value. Otherwise a client that negotiates a legacy
            # version (e.g. Codex rmcp sends 2025-06-18) echoes the default
            # 2025-11-25 in its next header and is rejected with HTTP 400
            # "MCP-Protocol-Version does not match the initialized session".
            if isinstance(result, dict):
                result["protocolVersion"] = runtime.protocol_version
            runtime.initialized = True
        elif method == "notifications/initialized":
            return None
        elif method == "notifications/cancelled":
            cancelled_request_id = params.get("requestId")
            if isinstance(cancelled_request_id, (str, int)) and not isinstance(cancelled_request_id, bool):
                runtime.cancel_request(cancelled_request_id)
            return None
        elif method == "ping":
            result = {}
        elif method == "server/discover":
            server_info = runtime.server_info_payload()
            endpoint = server_info.get("endpoint")
            if not isinstance(endpoint, dict):
                endpoint = endpoint_identity_payload(runtime)
            routing_instructions = endpoint_routing_instructions(endpoint)
            result = {
                "protocolVersion": runtime.protocol_version,
                "serverInfo": {
                    "name": "coding-tools-mcp",
                    "title": str(server_info.get("title") or endpoint_server_title(endpoint)),
                    "version": server_info.get("version", ""),
                },
                "capabilities": {"tools": {"listChanged": False}},
                "tools": runtime.list_tools().get("tools", []),
                "instructions": routing_instructions,
                "_meta": {
                    ENDPOINT_META_KEY: endpoint,
                    ENDPOINT_ROUTING_INSTRUCTIONS_META_KEY: routing_instructions,
                },
            }
        elif method == "tools/list":
            result = runtime.list_tools()
            if stateless_2026:
                result = _stateless_result(runtime, result, cacheable=True)
        elif method == "tools/call":
            if not isinstance(params.get("name"), str):
                raise JsonRpcError(-32602, "tools/call requires a tool name")
            arguments = params.get("arguments") or {}
            if not isinstance(arguments, dict):
                raise JsonRpcError(-32602, "tools/call arguments must be an object")
            result = runtime.call_tool(params["name"], arguments, request_id=request_id)
            if stateless_2026:
                result = _stateless_result(runtime, result, cacheable=False)
        else:
            raise JsonRpcError(-32601, f"Unknown method: {method}")
        if request_id is None:
            return None
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except JsonRpcError as exc:
        return jsonrpc_error(response_id(request), exc.code, exc.message, exc.data)
    except ExceptionGroup as exc:
        failure = normalize_exception_group(exc)
        return jsonrpc_error(
            response_id(request),
            -32603,
            failure.message,
            {
                "code": failure.code,
                "category": failure.category,
                "retryable": failure.retryable,
                "details": failure.details,
            },
        )
