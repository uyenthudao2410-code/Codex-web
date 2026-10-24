from __future__ import annotations

"""Persistent App Server lane restoration, isolated from bridge transport."""

import time
from pathlib import Path
from typing import Any, Callable



_TERMINAL_TURN_STATUSES = frozenset({"completed", "failed", "interrupted"})


def _active_turn_ids(thread: object) -> list[str]:
    """Turn ids a thread object still reports as non-terminal.

    The App Server persists turns with the thread, so a turn whose terminal
    event was never persisted (e.g. an interrupt processed by a previous
    App Server process that then restarted) comes back reported as
    inProgress by thread/read / thread/resume even though no live process
    is running it. Those are the orphan turns resume must reconcile.
    """
    turns = thread.get("turns") if isinstance(thread, dict) else None
    active: list[str] = []
    for turn in turns if isinstance(turns, list) else []:
        if not isinstance(turn, dict):
            continue
        turn_id = str(turn.get("id") or "").strip()
        status = str(turn.get("status") or "inProgress")
        if turn_id and status not in _TERMINAL_TURN_STATUSES:
            active.append(turn_id)
    return active


def _thread_reports_active(thread: object) -> bool:
    status = thread.get("status") if isinstance(thread, dict) else None
    if isinstance(status, dict):
        return str(status.get("type") or "") in {"active", "inProgress"}
    return str(status or "") in {"active", "inProgress"}


def _tracked_active_turn_ids(bridge: Any, thread_id: str) -> list[str]:
    """Non-terminal turns the bridge itself tracks for this thread.

    At restore time this bridge instance has launched no turn on the
    thread, so any non-terminal tracked entry can only have been learned
    from an App Server notification (e.g. a turn/started replayed during
    thread/resume) — it is the same orphan the server still reports.
    """
    with bridge._condition:
        return [
            str(turn_id)
            for turn_id, state in bridge._turn_states.items()
            if isinstance(state, dict)
            and state.get("thread_id") == thread_id
            and str(state.get("status", "inProgress")) not in _TERMINAL_TURN_STATUSES
        ]


def _reconcile_orphan_turns(
    bridge: Any,
    *,
    error_type: Callable[..., Exception],
    thread_id: str,
    thread_objects: list[object],
) -> list[str]:
    """Interrupt every orphan active turn the App Server still reports.

    Deterministic reconciliation, not a blind retry: interrupt by the exact
    turn id the server reported, then re-read the thread and verify no
    non-terminal turn remains. A server answer of "no active turn" is the
    benign race (the turn terminalized between read and interrupt) and is
    accepted only when the verification read confirms the thread is clean.
    Raises PERSISTENT_ORPHAN_TURN_NOT_CLEARED when the orphan survives.
    """
    candidates: list[str] = []
    for thread in thread_objects:
        for turn_id in _active_turn_ids(thread):
            if turn_id not in candidates:
                candidates.append(turn_id)
    for turn_id in _tracked_active_turn_ids(bridge, thread_id):
        if turn_id not in candidates:
            candidates.append(turn_id)
    if not candidates:
        return []
    for turn_id in candidates:
        try:
            bridge._request("turn/interrupt", {"threadId": thread_id, "turnId": turn_id})
        except Exception as exc:
            if "no active turn" not in str(exc).lower():
                raise error_type(
                    "PERSISTENT_ORPHAN_TURN_NOT_CLEARED",
                    "The App Server still reports an active turn for the persisted lane, and interrupting that orphaned turn failed.",
                    details={"thread_id": thread_id, "turn_id": turn_id},
                ) from exc
    verify_result = bridge._request(
        "thread/read",
        {"threadId": thread_id, "includeTurns": True},
    )
    verify_thread = verify_result.get("thread") if isinstance(verify_result, dict) else None
    remaining = _active_turn_ids(verify_thread)
    if remaining:
        raise error_type(
            "PERSISTENT_ORPHAN_TURN_NOT_CLEARED",
            "The App Server still reports an active turn for the persisted lane after an interrupt attempt.",
            details={"thread_id": thread_id, "turn_ids": remaining},
        )
    final_statuses: dict[str, str] = {}
    verify_turns = verify_thread.get("turns") if isinstance(verify_thread, dict) else None
    for turn in verify_turns if isinstance(verify_turns, list) else []:
        if isinstance(turn, dict) and str(turn.get("id") or "").strip():
            final_statuses[str(turn["id"])] = str(turn.get("status") or "")
    with bridge._condition:
        # The verification read is the source of truth: any turn this
        # bridge still tracks as active for the thread is terminal now
        # (interrupted by the reconciliation above, or already terminal
        # server-side), so the continue guard must not keep blocking on it.
        for turn_id, state in bridge._turn_states.items():
            if not isinstance(state, dict) or state.get("thread_id") != thread_id:
                continue
            if str(state.get("status", "inProgress")) in _TERMINAL_TURN_STATUSES:
                continue
            reported = final_statuses.get(str(turn_id))
            state["status"] = reported if reported in _TERMINAL_TURN_STATUSES else "interrupted"
        bridge._condition.notify_all()
    return candidates


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
        {"threadId": thread_id, "includeTurns": True},
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
    thread_objects: list[object] = [source, resumed]
    if (
        not _active_turn_ids(source)
        and not _active_turn_ids(resumed)
        and not _tracked_active_turn_ids(bridge, thread_id)
        and (_thread_reports_active(source) or _thread_reports_active(resumed))
    ):
        # The thread status claims an active turn but neither object named
        # it: one post-resume read (the thread is loaded now) must identify
        # it before the lane can be called clean.
        reread_result = bridge._request(
            "thread/read",
            {"threadId": thread_id, "includeTurns": True},
        )
        reread = reread_result.get("thread") if isinstance(reread_result, dict) else None
        if isinstance(reread, dict):
            thread_objects.append(reread)
    reconciled_orphans = _reconcile_orphan_turns(
        bridge,
        error_type=error_type,
        thread_id=thread_id,
        thread_objects=thread_objects,
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
        "reconciled_orphan_turns": reconciled_orphans,
    }
