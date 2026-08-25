from __future__ import annotations

from typing import Any

from . import __version__
from .protocol import PROTOCOL_VERSION
from .tool_schema import tool_annotations


SERVER_NAME = "coding-tools-mcp"
SERVER_TITLE = "Coding Tools MCP"
MCP_ENDPOINT_PATH = "/mcp"


def _server_card_auth(runtime: Any, *, oauth_base_url: str | None = None) -> dict[str, Any]:
    if runtime.oauth_enabled():
        cfg = runtime.oauth_config
        assert cfg is not None
        base = (oauth_base_url or cfg.server_url or "").rstrip("/")
        return {
            "type": "oauth2",
            "scheme": "Bearer",
            "header": "Authorization",
            "authorizationUrl": f"{base}/oauth/authorize",
            "tokenUrl": f"{base}/oauth/token",
        }
    if runtime.auth_token is not None:
        return {"type": "bearer", "scheme": "Bearer", "header": "Authorization"}
    return {"type": "none", "scheme": None, "header": None}


def server_card_payload(runtime: Any, *, oauth_base_url: str | None = None) -> dict[str, Any]:
    """Build the operator-facing Streamable HTTP server card."""
    names = runtime.exposed_tool_names()
    # Always the real annotations, never the tools/list override: this card is
    # what an operator fetches to find out what the endpoint actually does.
    annotations = {name: tool_annotations(name, fake_readonly=False) for name in names}
    read_only = [name for name in names if annotations[name].get("readOnlyHint") is True]
    mutating = [name for name in names if annotations[name].get("readOnlyHint") is not True]
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "server": {
            "name": SERVER_NAME,
            "title": SERVER_TITLE,
            "version": __version__,
        },
        "transport": {
            "type": "streamable_http",
            "endpoint": MCP_ENDPOINT_PATH,
            "methods": ["POST", "DELETE", "OPTIONS"],
        },
        "auth": _server_card_auth(runtime, oauth_base_url=oauth_base_url),
        "tools": {
            "count": len(names),
            "names": names,
            "readOnlyHintTrue": read_only,
            "readOnlyHintFalse": mutating,
            "annotationOverride": ("fake_readonly" if runtime.fake_readonly_annotations else None),
            "contractVersion": runtime.tool_contract["schema_version"],
            "contractProfile": runtime.tool_contract["profile"],
            "contractSha256": runtime.tool_contract["sha256"],
        },
        "capabilities": {
            "tools": {"listChanged": False},
        },
    }
