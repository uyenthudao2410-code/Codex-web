from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def hub_client_activity_state(
    last_seen_at: object,
    *,
    active_seconds: float,
    recent_seconds: float = 600.0,
) -> str:
    text = str(last_seen_at or "").strip()
    if not text:
        return "NO_SIGNAL"
    try:
        observed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return "NO_SIGNAL"
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    age_seconds = max(
        0.0,
        datetime.now(timezone.utc).timestamp() - observed.astimezone(timezone.utc).timestamp(),
    )
    active_window = max(0.0, float(active_seconds))
    if age_seconds <= active_window:
        return "ACTIVE"
    if age_seconds <= max(active_window, float(recent_seconds)):
        return "RECENT"
    return "NO_SIGNAL"


def runtime_activity_snapshot(
    runtime: Any,
    *,
    write_active: bool = False,
    delegations: list[dict[str, Any]] | None = None,
    limit: int = 8,
) -> dict[str, Any]:
    bounded_limit = max(1, min(int(limit), 20))
    managed = runtime.execution_resource_governor.snapshot(limit=max(12, bounded_limit))
    active_job_states = {"starting", "running", "terminating", "orphaned"}
    managed_jobs = [
        dict(item)
        for item in (managed.get("jobs") or [])
        if str(item.get("lifecycle_state") or "").lower() in active_job_states
    ][:bounded_limit]
    with runtime.sessions_lock:
        live_exec_sessions = sum(
            1 for session in runtime.sessions.values() if session.process.poll() is None
        ) + max(0, int(runtime.starting_sessions))
    with runtime.background_operations_lock:
        active_background = [
            runtime._background_operation_snapshot(item)
            for item in runtime.background_operations.values()
            if item.get("workspace") == str(runtime.workspace.root)
            and item.get("event") is not None
            and not item["event"].is_set()
        ][:bounded_limit]
    terminal_delegations = {"completed", "failed", "cancelled", "stopped", "rejected"}
    active_delegations = [
        item
        for item in (delegations or [])
        if str(item.get("status") or "").strip()
        and str(item.get("status") or "").lower() not in terminal_delegations
    ]
    active_tool_calls = max(0, int(runtime.active_tool_calls))
    active_commands = max(
        max(0, int(managed.get("active_command_count") or 0)),
        live_exec_sessions,
    )
    state = (
        "DELEGATING"
        if active_delegations
        else "WRITING"
        if write_active
        else "ACTIVE"
        if active_tool_calls or active_commands or active_background
        else "IDLE"
    )
    return {
        "schema_version": 1,
        "state": state,
        "active": state != "IDLE",
        "active_tool_calls": active_tool_calls,
        "active_commands": active_commands,
        "active_background_operations": len(active_background),
        "active_delegations": len(active_delegations),
        "write_active": bool(write_active),
        "managed_jobs": managed_jobs,
        "background_operations": [
            {
                key: item.get(key)
                for key in ("operation_id", "tool", "status", "elapsed_seconds")
            }
            for item in active_background
        ],
    }


class RuntimeActivityMixin:
    hub_client_activity_state = staticmethod(hub_client_activity_state)
    runtime_activity_snapshot = runtime_activity_snapshot
