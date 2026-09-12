from __future__ import annotations

import hashlib
import hmac
import re
from typing import Any

ACTIVATION_OPERATION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$")
ACTIVATION_PROOF_RE = re.compile(r"^[a-f0-9]{64}$")
ACTIVATION_CONTROL_ALLOWED_FIELDS = {
    "prepare": {"action", "operation_id", "expires_at_unix_ms", "workspace", "allow_acceptance_pending", "source_checkpoint"},
    "cancel": {"action", "operation_id"},
    "verify": {"action", "operation_id", "workspace", "source_checkpoint", "allow_acceptance_pending"},
    "complete_epoch": {"action", "activation_epoch_id", "ready_commit_digest", "expires_at_unix_ms"},
    "close_epoch": {"action", "activation_epoch_id", "ready_commit_digest"},
}


def valid_activation_operation_id(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    raw = value
    operation_id = raw.strip()
    return raw == operation_id and ACTIVATION_OPERATION_ID_RE.fullmatch(operation_id) is not None


def valid_activation_control_payload(action: str, payload: dict[str, Any]) -> bool:
    allowed = ACTIVATION_CONTROL_ALLOWED_FIELDS.get(action)
    return allowed is not None and not set(payload).difference(allowed)


def recovery_activation_capability(headers: Any, runtime: Any) -> dict[str, Any]:
    """Authenticate the exact Recovery Host post-tool-call activation census.

    Authentication lets the Recovery Host present the operation id that owns
    the durable activation fence.  It deliberately does *not* discount an
    active tool call.  The signed snapshot must keep returning ``RUNTIME_BUSY``
    until the initiating ``restart_runtime`` call has actually left the MCP
    tool boundary; the Recovery Host then retries the same durable ticket.
    """
    operation_id = str(headers.get("X-Coding-Tools-Activation-Operation", "")).strip()
    proof = str(headers.get("X-Coding-Tools-Activation-Proof", "")).strip().lower()
    token = getattr(runtime, "auth_token", None)
    authorization = str(headers.get("Authorization", "")).strip()
    if not token or authorization != f"Bearer {token}":
        return {"operation_id": "", "ignore_active_tool_calls": 0}
    if not ACTIVATION_OPERATION_ID_RE.fullmatch(operation_id) or not ACTIVATION_PROOF_RE.fullmatch(proof):
        return {"operation_id": "", "ignore_active_tool_calls": 0}
    expected = hmac.new(
        str(token).encode("utf-8"),
        f"coding-tools-mcp-activation-preflight:{operation_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(proof, expected):
        return {"operation_id": "", "ignore_active_tool_calls": 0}
    return {"operation_id": operation_id, "ignore_active_tool_calls": 0}


def recovery_activation_ignore_active_tool_calls(headers: Any, runtime: Any) -> int:
    """Compatibility projection; external recovery never discounts tool calls."""
    return int(recovery_activation_capability(headers, runtime)["ignore_active_tool_calls"])
