from __future__ import annotations

import hashlib
import re
import secrets
from collections.abc import Callable
from typing import Any


STATELESS_TASK_CONTEXT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
STATELESS_TASK_CONTEXT_META_KEY = "io.coding-tools/taskContextId"
TASK_CONTROL_CONTINUATION_ACTIONS = frozenset({
    "get", "history", "audit", "events", "messages", "ack", "accept", "reject",
})


def resolve_stateless_task_context(
    request: dict[str, Any],
    *,
    identity_from_request: Callable[[dict[str, Any]], dict[str, Any]],
    recover_exact_run_context: Callable[[str, str], str],
) -> tuple[dict[str, Any], str, str]:
    """Resolve one MCP-2026 application context without collapsing isolation."""
    task_context_id = ""
    dispatch_request = request
    if request.get("method") == "tools/call":
        params = request.get("params") if isinstance(request.get("params"), dict) else {}
        arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else None
        if arguments is not None:
            supplied = arguments.get("task_context_id")
            if supplied is not None:
                if not isinstance(supplied, str) or not STATELESS_TASK_CONTEXT_ID_RE.fullmatch(supplied):
                    raise ValueError("task_context_id must match [A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
                task_context_id = supplied
            if "task_context_id" in arguments:
                clean_arguments = dict(arguments)
                clean_arguments.pop("task_context_id", None)
                clean_params = dict(params)
                clean_params["arguments"] = clean_arguments
                dispatch_request = dict(request)
                dispatch_request["params"] = clean_params
            if not task_context_id and str(params.get("name") or "").strip() == "task_control":
                action = str(arguments.get("action") or "get").strip().lower()
                run_id = str(arguments.get("run_id") or "").strip()
                exact_selector = (
                    (action != "ack" or bool(str(arguments.get("message_id") or "").strip()))
                    and (action not in {"accept", "reject"} or bool(str(arguments.get("wave_id") or "").strip()))
                )
                if action in TASK_CONTROL_CONTINUATION_ACTIONS and run_id and exact_selector:
                    identity = identity_from_request(request)
                    if str(identity.get("client_type") or "") == "chatweb":
                        task_context_id = recover_exact_run_context(
                            run_id,
                            str(identity.get("client_id") or "chatweb"),
                        )
    if not task_context_id:
        task_context_id = f"ctx_{secrets.token_hex(16)}"
    execution_context_id = "mcp2026:" + hashlib.sha256(
        f"mcp2026-task:{task_context_id}".encode("utf-8")
    ).hexdigest()[:56]
    return dispatch_request, task_context_id, execution_context_id
