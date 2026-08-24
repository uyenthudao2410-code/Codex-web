from __future__ import annotations

from typing import Any

from .errors import normalize_exception_group
from .mcp_http_handler import MCPHandler as BaseMCPHandler
from .protocol import jsonrpc_error, response_id


class ExceptionSafeMCPHandler(BaseMCPHandler):
    """Keep unexpected dispatch failures inside the JSON-RPC boundary.

    The primary handler owns stateless MCP-2026 normalization, request-scoped
    workspace binding, controller registration, and cleanup.  This subclass
    must wrap that implementation rather than reimplement it: duplicating the
    dispatch path silently bypassed the task-context admission contract in the
    production bootstrap handler.
    """

    def handle_rpc(
        self,
        request: dict[str, Any],
        *,
        stateless_2026: bool = False,
    ) -> dict[str, Any] | None:
        try:
            return super().handle_rpc(request, stateless_2026=stateless_2026)
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
        except Exception as exc:  # noqa: BLE001 - HTTP must always answer with JSON-RPC
            return jsonrpc_error(response_id(request), -32603, str(exc))
