from __future__ import annotations

from typing import Any

from .controller_reattach import controller_identity


_SESSION_EVENT = "cross_session_chatweb_session_started"
_ROTATION_EVENT = "cross_session_chatweb_session_rotated"
_CORE_EVENT = "continuity_core_recorded"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _problem_events(ledger: Any, problem_id: str, problem_revision: int) -> list[dict[str, Any]]:
    with ledger._lock, ledger._connect() as connection:
        rows = connection.execute(
            "SELECT * FROM events WHERE event_type IN (?,?,?) ORDER BY seq",
            (_SESSION_EVENT, _ROTATION_EVENT, _CORE_EVENT),
        ).fetchall()
    events = [ledger._event_row(row) for row in rows]
    return [
        event
        for event in events
        if _text((event.get("payload") or {}).get("problem_id")) == problem_id
        and int((event.get("payload") or {}).get("problem_revision") or 0)
        == problem_revision
    ]


def record_problem_product_session(
    ledger: Any,
    *,
    run_id: str,
    wave_id: str,
    problem_resolution: dict[str, Any],
    workspace_id: str,
    claimed_host_turn: dict[str, Any],
    hub_client: dict[str, Any],
) -> dict[str, Any] | None:
    """Record a host-derived product session only after exact Problem binding."""
    if _text(problem_resolution.get("work_origin")) != "problem":
        return None
    problem_id = _text(problem_resolution.get("problem_id"))
    problem_revision = problem_resolution.get("problem_revision")
    receipt_id = _text(claimed_host_turn.get("product_session_receipt_id"))
    if (
        not problem_id
        or isinstance(problem_revision, bool)
        or not isinstance(problem_revision, int)
        or problem_revision < 1
        or not workspace_id
        or not receipt_id
    ):
        return None
    handoff = ledger.problem_handoff_for_run(run_id)
    if (
        not isinstance(handoff, dict)
        or _text(handoff.get("active_problem_id")) != problem_id
        or int(handoff.get("problem_revision") or 0) != problem_revision
    ):
        return None
    client_id = _text(hub_client.get("client_id"))
    identity = controller_identity(hub_client, client_id)
    if identity is None:
        return None

    events = _problem_events(ledger, problem_id, problem_revision)
    sessions = [event for event in events if event.get("event_type") == _SESSION_EVENT]
    existing = next(
        (
            event
            for event in sessions
            if _text((event.get("payload") or {}).get("product_session_receipt_id"))
            == receipt_id
        ),
        None,
    )
    if existing is not None:
        return {"recorded": False, "session_event": existing, "rotation_event": None}

    transition = _text(claimed_host_turn.get("product_session_transition")).lower()
    prior_receipt = _text(claimed_host_turn.get("prior_product_session_receipt_id"))
    rotation_event = None
    if transition == "rotated" and prior_receipt and prior_receipt != receipt_id:
        prior_session = next(
            (
                event
                for event in reversed(sessions)
                if _text((event.get("payload") or {}).get("product_session_receipt_id"))
                == prior_receipt
            ),
            None,
        )
        core_event = next(
            (
                event
                for event in reversed(events)
                if event.get("event_type") == _CORE_EVENT
                and prior_session is not None
                and int(event.get("seq") or 0) > int(prior_session.get("seq") or 0)
                and _text((event.get("payload") or {}).get("workspace_id"))
                == workspace_id
            ),
            None,
        )
        if prior_session is not None and core_event is not None:
            rotation_event = ledger.append_event(
                run_id,
                wave_id=wave_id,
                event_type=_ROTATION_EVENT,
                payload={
                    "problem_id": problem_id,
                    "problem_revision": problem_revision,
                    "receipt_type": "CHATWEB_PRODUCT_SESSION_ROTATION_V1",
                    "outgoing_product_session_receipt_id": prior_receipt,
                    "incoming_product_session_receipt_id": receipt_id,
                    "session_event_id": prior_session["event_id"],
                    "core_event_id": core_event["event_id"],
                    "transition_source": "electron_host_navigation",
                },
            )

    session_role = "A" if not sessions else "B"
    session_event = ledger.append_event(
        run_id,
        wave_id=wave_id,
        event_type=_SESSION_EVENT,
        payload={
            "problem_id": problem_id,
            "problem_revision": problem_revision,
            "workspace_id": workspace_id,
            "session_role": session_role,
            "receipt_type": "CHATWEB_PRODUCT_SESSION_GOAL_PURSUIT_V1",
            "product_session_receipt_id": receipt_id,
            "controller_endpoint_id": identity["controller_endpoint_id"],
            "host_turn_id": _text(claimed_host_turn.get("turn_id")),
            "host_trace_id": _text(claimed_host_turn.get("trace_id")),
            "identity_source": "electron_host_product_session_receipt",
        },
    )
    return {
        "recorded": True,
        "session_event": session_event,
        "rotation_event": rotation_event,
    }


def record_current_continuity_core(runtime: Any, args: dict[str, Any], result: dict[str, Any]) -> None:
    """Bind a returned checkpoint core to the exact current Problem RUN/WAVE."""
    if _text(args.get("continuity_action")).lower() != "checkpoint":
        return
    core = result.get("continuity_core") if isinstance(result.get("continuity_core"), dict) else None
    if core is None:
        return
    state = runtime.task_state.get()
    projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
    run_id = _text(projection.get("run_id"))
    wave_id = _text(projection.get("wave_id"))
    if not run_id or not wave_id:
        return
    handoff = runtime.orchestration_ledger.problem_handoff_for_run(run_id)
    if (
        not isinstance(handoff, dict)
        or _text(handoff.get("active_problem_id")) != _text(core.get("problem_id"))
        or int(handoff.get("problem_revision") or 0)
        != int(core.get("problem_revision") or 0)
    ):
        return
    fingerprint = _text(core.get("continuity_core_fingerprint"))
    if not fingerprint:
        return
    events = _problem_events(
        runtime.orchestration_ledger,
        _text(core.get("problem_id")),
        int(core.get("problem_revision") or 0),
    )
    if any(
        event.get("event_type") == _CORE_EVENT
        and _text((event.get("payload") or {}).get("continuity_core_fingerprint"))
        == fingerprint
        for event in events
    ):
        return
    runtime.orchestration_ledger.append_event(
        run_id,
        wave_id=wave_id,
        event_type=_CORE_EVENT,
        payload={
            "problem_id": _text(core.get("problem_id")),
            "problem_revision": int(core.get("problem_revision") or 0),
            "workspace_id": _text(core.get("workspace_id")),
            "continuity_core_fingerprint": fingerprint,
            "knowledge_revision": int(core.get("knowledge_revision") or 0),
            "source_fingerprint": _text(core.get("source_fingerprint")),
            "runtime_behavior_fingerprint": _text(
                core.get("runtime_behavior_fingerprint")
            ),
            "recording_source": "runtime_continuity_checkpoint",
        },
    )
