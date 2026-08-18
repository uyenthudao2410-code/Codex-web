from __future__ import annotations

from typing import Any

from .errors import normalize_exception_group
from .mcp_http_handler import MCPHandler as BaseMCPHandler
from .protocol import dispatch_rpc, jsonrpc_error, response_id


class ExceptionSafeMCPHandler(BaseMCPHandler):
    """Keep pre-dispatch hub failures inside the structured JSON-RPC boundary."""

    def handle_rpc(
        self,
        request: dict[str, Any],
        *,
        stateless_2026: bool = False,
    ) -> dict[str, Any] | None:
        runtime = self.runtime
        try:
            identity = self._hub_identity_from_request(request)
            runtime.request_context.hub_client = identity
            runtime._touch_hub_client(identity)
            return dispatch_rpc(runtime, request, stateless_2026=stateless_2026)
        except ValueError as exc:
            return jsonrpc_error(response_id(request), -32602, str(exc))
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
        finally:
            if hasattr(runtime.request_context, "hub_client"):
                delattr(runtime.request_context, "hub_client")
