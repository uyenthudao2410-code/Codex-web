from __future__ import annotations

"""Persistent App Server lane restoration, isolated from bridge transport."""

import time
from pathlib import Path
from typing import Any, Callable


def restore_persistent_thread(
    bridge: Any,
    *,
    error_type: Callable[..., Exception],
    workspace_contains: Callable[[object, Path], bool],
    thread_id: str,
    profile: str,
    model: str | None = None,
    effort: str | None = None,
    expected_session_id: str = "",
    deadline_ms: int = 0,
    output_schema: dict[str, Any] | None = None,
    wait_ms: int = 0,
) -> dict[str, Any]:
    """Restore a registry-authorized persistent lane without starting a turn.

    This is intentionally not a model-facing action. The caller must first
    resolve the thread from the durable orchestration lane registry so an
    arbitrary live Codex Desktop thread cannot be claimed by the bridge.
    """
    if not thread_id:
        raise error_type("THREAD_ID_REQUIRED", "A persisted lane thread_id is required.")
    workspace = bridge._workspace()
    route = bridge._resolve_route(
        profile=profile,
        model=model,
        effort=effort,
        source_thread_id="history-source" if profile == "history" else None,
        continuing=True,
    )
    bridge._ensure_connected()
    bridge._assert_profile_launch_policy(route)
    source_result = bridge._request(
        "thread/read",
        {"threadId": thread_id, "includeTurns": False},
    )
    source = source_result.get("thread") if isinstance(source_result, dict) else None
    if not isinstance(source, dict):
        raise error_type(
            "PERSISTENT_THREAD_NOT_FOUND",
            "Codex did not return the persisted lane thread.",
            details={"thread_id": thread_id},
        )
    if not workspace_contains(source.get("cwd"), workspace):
        raise error_type(
            "PERSISTENT_WORKSPACE_MISMATCH",
            "The persisted lane belongs to a different workspace.",
            details={
                "thread_id": thread_id,
                "source_cwd": source.get("cwd"),
                "workspace": str(workspace),
            },
        )
    actual_session_id = str(source.get("sessionId") or "")
    if expected_session_id and actual_session_id != expected_session_id:
        raise error_type(
            "PERSISTENT_SESSION_MISMATCH",
            "The persisted lane session identity no longer matches the durable registry.",
            details={
                "thread_id": thread_id,
                "expected_session_id": expected_session_id,
                "actual_session_id": actual_session_id,
            },
        )
    bridge._check_capacity(route["model"])
    resume_response = bridge._request(
        "thread/resume",
        {
            "threadId": thread_id,
            **bridge._thread_route_params(route, workspace),
        },
    )
    resumed = resume_response.get("thread") if isinstance(resume_response, dict) else None
    if not isinstance(resumed, dict) or str(resumed.get("id") or thread_id) != thread_id:
        raise error_type(
            "PERSISTENT_THREAD_RESUME_FAILED",
            "Codex did not confirm the persisted lane thread during resume.",
            details={"thread_id": thread_id},
        )
    with bridge._condition:
        bridge._owned_threads[thread_id] = {
            "workspace": str(workspace),
            "source_thread_id": None,
            "created_at": time.time(),
            "mode": "persistent_resume",
            "lifetime": "persistent",
            "profile": route["profile"],
            "model": route["model"],
            "effort": route["effort"],
            "session_id": str(resumed.get("sessionId") or actual_session_id),
            "reported_model": resumed.get("model"),
            "reported_effort": resumed.get("reasoningEffort"),
            "restored": True,
        }
    return {
        "ok": True,
        "thread_id": thread_id,
        "session_id": str(resumed.get("sessionId") or actual_session_id),
        "creation_mode": "persistent_restore",
        "lifetime": "persistent",
        "route": route,
    }
