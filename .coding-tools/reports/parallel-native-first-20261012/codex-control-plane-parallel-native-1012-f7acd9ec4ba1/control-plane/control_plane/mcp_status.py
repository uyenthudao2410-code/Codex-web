"""Safe terminal failure projection for connected MCP action observations."""

from __future__ import annotations

import json
import re
from typing import Any


_SAFE_CODE = re.compile(r"[A-Z][A-Z0-9_]{2,95}")
_TERMINAL_FAILURES = {
    "rejected": ("LOCAL_ACTION_REJECTED", "local_admission", "inspect_action"),
    "failed": ("LOCAL_ACTION_FAILED", "execution", "do_not_replay_automatically"),
    "stopped": ("LOCAL_ACTION_STOPPED", "execution", "do_not_replay_automatically"),
}


def _safe_code(value: Any) -> str | None:
    return value if isinstance(value, str) and _SAFE_CODE.fullmatch(value) else None


def terminal_failure(action: dict[str, Any]) -> dict[str, Any] | None:
    """Project only a settled action's latest terminal failure receipt.

    Store observations order receipts oldest to newest. Earlier UNKNOWN
    receipts remain history; neither UNKNOWN nor a diagnostic string proves a
    terminal failure. Raw receipt messages, paths and payloads never leave this
    projection, and a failure does not establish whether an effect occurred.
    """

    if action.get("delivery_state") != "settled":
        return None
    receipts = action.get("receipts")
    if not isinstance(receipts, list) or not receipts or not isinstance(receipts[-1], dict):
        return None
    receipt = receipts[-1]
    state = receipt.get("receipt_state")
    if not isinstance(state, str) or state not in _TERMINAL_FAILURES:
        return None

    payload: dict[str, Any] = {}
    raw = receipt.get("payload_json")
    if isinstance(raw, str) and len(raw) <= 64 * 1024:
        try:
            parsed = json.loads(raw)
        except (ValueError, RecursionError):
            parsed = None
        if isinstance(parsed, dict):
            payload = parsed

    fallback, category, next_action = _TERMINAL_FAILURES[state]
    code = _safe_code(payload.get("code")) or fallback
    failure: dict[str, Any] = {
        "code": code,
        "category": category,
        "retryable": False,
        "next_action": next_action,
    }
    diagnostic = _safe_code(payload.get("diagnostic_code"))
    if diagnostic is not None and diagnostic != code:
        failure["diagnostic_code"] = diagnostic
    return failure
