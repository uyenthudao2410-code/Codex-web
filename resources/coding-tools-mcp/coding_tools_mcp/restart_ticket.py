from __future__ import annotations

import json
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from .activation_capability import valid_activation_operation_id

SUPERVISOR_RESTART_TICKET_TTL_MS = 60_000
SUPERVISOR_RESTART_RESPONSE_GRACE_MS = 2_000
SUPERVISOR_RESTART_TICKET_PREFIX = "restart-"
SUPERVISOR_RESTART_MAX_CLOCK_SKEW_MS = 5_000


def build_supervisor_restart_ticket(
    *,
    ticket_id: str,
    now_ms: int,
    workspace: str,
    process_instance_id: str,
    server_instance_id: str,
    tool_contract_sha256: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "version": 1,
        "action": "restart",
        "ticket_id": ticket_id,
        "operation_id": ticket_id,
        "activation_mode": "full_clean_activation",
        "full_clean_required": True,
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "requested_at_unix_ms": now_ms,
        "not_before_unix_ms": now_ms + SUPERVISOR_RESTART_RESPONSE_GRACE_MS,
        "expires_at_unix_ms": now_ms + SUPERVISOR_RESTART_TICKET_TTL_MS,
        "workspace": workspace,
        "process_instance_id": process_instance_id,
        "server_instance_id": server_instance_id,
        "tool_contract_sha256": tool_contract_sha256,
        "reason": reason[:500],
    }


def supervisor_restart_ticket_matches(
    value: Any,
    *,
    now_ms: int,
    workspace: str,
    process_instance_id: str,
    server_instance_id: str,
    tool_contract_sha256: str,
    fence_operation_id: str,
) -> bool:
    if not isinstance(value, dict) or type(value.get("version")) is not int:
        return False
    ticket_id = value.get("ticket_id")
    requested_at = value.get("requested_at_unix_ms")
    not_before = value.get("not_before_unix_ms")
    expires_at = value.get("expires_at_unix_ms")
    if not all(type(item) is int for item in (requested_at, not_before, expires_at)):
        return False
    return bool(
        value.get("version") == 1
        and value.get("action") == "restart"
        and isinstance(ticket_id, str)
        and valid_activation_operation_id(ticket_id)
        and isinstance(value.get("operation_id"), str)
        and value.get("operation_id") == ticket_id
        and value.get("activation_mode") == "full_clean_activation"
        and value.get("full_clean_required") is True
        and isinstance(value.get("workspace"), str)
        and value.get("workspace", "").casefold() == workspace.casefold()
        and value.get("process_instance_id") == process_instance_id
        and value.get("server_instance_id") == server_instance_id
        and value.get("tool_contract_sha256") == tool_contract_sha256
        and fence_operation_id == ticket_id
        and requested_at > 0
        and requested_at <= now_ms + SUPERVISOR_RESTART_MAX_CLOCK_SKEW_MS
        and now_ms - requested_at <= SUPERVISOR_RESTART_TICKET_TTL_MS
        and requested_at < not_before < expires_at
        and expires_at - requested_at <= SUPERVISOR_RESTART_TICKET_TTL_MS
        # Expiry is an exact fail-closed boundary.  A ticket at
        # ``now_ms == expires_at`` is already expired and cannot be replayed.
        and expires_at > now_ms
    )


def supervisor_restart_response(ticket: dict[str, Any], *, already_pending: bool) -> dict[str, Any]:
    return {
        "accepted": True,
        "already_pending": already_pending,
        "restart_ticket": str(ticket["ticket_id"]),
        "expected_disconnect": True,
        "supervisor": "electron",
        "not_before_unix_ms": int(ticket["not_before_unix_ms"]),
        "expires_at_unix_ms": int(ticket["expires_at_unix_ms"]),
        "recommended_next_action": (
            "Allow the Electron supervisor to consume the pending ticket, then reconnect and verify runtime instance ids changed."
            if already_pending else
            "The Electron supervisor will restart after this tool response has time to flush. Reconnect, then verify process_instance_id and server_instance_id changed."
        ),
    }


def observe_installed_restart_ticket(
    request_path: Path,
    expected_ticket: dict[str, Any],
) -> Literal["exact", "absent", "different", "unknown"]:
    """Classify post-replace state without treating an unreadable target as absent."""
    try:
        target_stat = request_path.stat()
    except FileNotFoundError:
        return "absent"
    except OSError:
        return "unknown"
    if not stat.S_ISREG(target_stat.st_mode):
        return "different"
    try:
        installed = json.loads(request_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "unknown"
    return "exact" if installed == expected_ticket else "different"
