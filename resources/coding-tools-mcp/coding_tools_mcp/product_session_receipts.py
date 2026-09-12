from __future__ import annotations

import hashlib
import json
from typing import Any

from .controller_reattach import controller_identity


_SESSION_EVENT = "cross_session_chatweb_session_started"
_ROTATION_EVENT = "cross_session_chatweb_session_rotated"
_CORE_EVENT = "continuity_core_recorded"
_READ_EVENT = "controller_knowledge_read_observed"
_NO_ADVANCE_EVENT = "controller_knowledge_no_advance_observed"
_CONTROL_CENTER_EVENT = "execution_control_center_progress_observed"
_REOBSERVED_EVENT = "managed_execution_reobserved"
_RECONSTRUCTION_EVENT = "goal_reconstruction_observed"
_CRITERION_COMPLETED_EVENT = "remaining_criterion_completed"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _exact_current_problem(runtime: Any, problem_id: str, problem_revision: int) -> dict[str, Any] | None:
    state = runtime.task_state.get()
    projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
    run_id = _text(projection.get("run_id"))
    wave_id = _text(projection.get("wave_id"))
    if not run_id or not wave_id:
        return None
    handoff = runtime.orchestration_ledger.problem_handoff_for_run(run_id)
    if (
        not isinstance(handoff, dict)
        or _text(handoff.get("active_problem_id")) != problem_id
        or int(handoff.get("problem_revision") or 0) != problem_revision
    ):
        return None
    run = runtime.orchestration_ledger.get_run(run_id) or {}
    metadata = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
    workspace = metadata.get("workspace_identity") if isinstance(metadata.get("workspace_identity"), dict) else {}
    return {
        "run_id": run_id,
        "wave_id": wave_id,
        "workspace_id": _text(workspace.get("workspace_id")),
        "handoff": handoff,
    }


def _problem_run_wave_pairs(ledger: Any, problem_id: str, problem_revision: int) -> list[tuple[str, str]]:
    with ledger._lock, ledger._connect() as connection:
        rows = connection.execute(
            """SELECT run_id,wave_id,MIN(seq) AS first_seq FROM problem_events
               WHERE problem_id=? AND problem_revision=? AND link_status='EXACT'
                 AND link_role='PRIMARY' AND relation_type IN ('LINK','ENGINEERING_ATTEMPT_BOUND')
                 AND run_id<>'' AND wave_id<>''
               GROUP BY run_id,wave_id
               ORDER BY first_seq,run_id,wave_id LIMIT 32""",
            (problem_id, problem_revision),
        ).fetchall()
    return [(str(row["run_id"]), str(row["wave_id"])) for row in rows]


def _problem_runtime_events(ledger: Any, problem_id: str, problem_revision: int) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    seen: set[str] = set()
    for run_id, _wave_id in _problem_run_wave_pairs(ledger, problem_id, problem_revision):
        if run_id in seen:
            continue
        seen.add(run_id)
        for event in ledger.list_events(run_id):
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            if (
                _text(payload.get("problem_id")) == problem_id
                and int(payload.get("problem_revision") or 0) == problem_revision
            ):
                events.append(event)
    events.sort(key=lambda item: int(item.get("seq") or 0))
    return events


def _append_unique_event(
    ledger: Any,
    *,
    run_id: str,
    wave_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    fingerprint = _sha256_json(payload)
    for event in ledger.list_events(run_id, wave_id=wave_id):
        if event.get("event_type") != event_type:
            continue
        existing = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if _text(existing.get("producer_receipt_fingerprint")) == fingerprint:
            return {"recorded": False, "event": event}
    durable = {**payload, "producer_receipt_fingerprint": fingerprint}
    event = ledger.append_event(run_id, wave_id=wave_id, event_type=event_type, payload=durable)
    return {"recorded": True, "event": event}


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


def record_continuity_read_receipt(
    runtime: Any, args: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any] | None:
    """Observe real continuity reads and emit NO_ADVANCE only from two durable reads."""
    if _text(args.get("continuity_action")).lower() != "get":
        return None
    core = result.get("continuity_core") if isinstance(result.get("continuity_core"), dict) else None
    if core is None:
        return None
    problem_id = _text(core.get("problem_id"))
    revision = core.get("problem_revision")
    if not problem_id or isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        return None
    binding = _exact_current_problem(runtime, problem_id, revision)
    if binding is None:
        return None
    knowledge_revision = int(core.get("knowledge_revision") or 0)
    read_event = runtime.orchestration_ledger.append_event(
        binding["run_id"],
        wave_id=binding["wave_id"],
        event_type=_READ_EVENT,
        payload={
            "problem_id": problem_id,
            "problem_revision": revision,
            "operation": "continuity.get",
            "knowledge_revision": knowledge_revision,
            "continuity_core_fingerprint": _text(core.get("continuity_core_fingerprint")),
        },
    )
    wave_events = runtime.orchestration_ledger.list_events(
        binding["run_id"], wave_id=binding["wave_id"]
    )
    reads = [
        event
        for event in wave_events
        if event.get("event_type") == _READ_EVENT
        and _text((event.get("payload") or {}).get("problem_id")) == problem_id
        and int((event.get("payload") or {}).get("problem_revision") or 0) == revision
        and int((event.get("payload") or {}).get("knowledge_revision") or 0) == knowledge_revision
    ]
    existing_no_advance = next(
        (
            event
            for event in reversed(wave_events)
            if event.get("event_type") == _NO_ADVANCE_EVENT
            and _text((event.get("payload") or {}).get("problem_id")) == problem_id
            and int((event.get("payload") or {}).get("problem_revision") or 0) == revision
            and int((event.get("payload") or {}).get("knowledge_revision_before") or 0)
            == knowledge_revision
            and int((event.get("payload") or {}).get("knowledge_revision_after") or 0)
            == knowledge_revision
        ),
        None,
    )
    if existing_no_advance is not None:
        return {"read_event": read_event, "no_advance_event": existing_no_advance}
    if len(reads) < 2:
        return {"read_event": read_event, "no_advance_event": None}
    # One exact representative pair is sufficient for a stable knowledge
    # revision. Later reads of the same revision must not recursively create
    # fresh evidence merely because the observer polled again.
    pair = reads[:2]
    operation_receipt_ids = [_text(event.get("event_id")) for event in pair]
    observed = _append_unique_event(
        runtime.orchestration_ledger,
        run_id=binding["run_id"],
        wave_id=binding["wave_id"],
        event_type=_NO_ADVANCE_EVENT,
        payload={
            "problem_id": problem_id,
            "problem_revision": revision,
            "policy": "NO_ADVANCE",
            "operation_count": len(operation_receipt_ids),
            "operation_receipt_ids": operation_receipt_ids,
            "knowledge_revision_before": knowledge_revision,
            "knowledge_revision_after": knowledge_revision,
            "observation_source": "runtime_continuity_get",
        },
    )
    return {"read_event": read_event, "no_advance_event": observed["event"]}


def record_execution_control_center_progress(
    runtime: Any,
    *,
    run_id: str,
    wave_id: str,
    span: dict[str, Any],
) -> dict[str, Any] | None:
    """Promote only an attested Electron Control Center observation to TG6 evidence."""
    identity = runtime._current_hub_client() or {}
    if (
        _text(identity.get("client_type")) != "electron"
        or _text(identity.get("role")) != "supervisor"
        or _text(identity.get("identity_source")) != "attested_transport"
        or identity.get("attestation_verified") is not True
    ):
        return None
    if (
        _text(span.get("stage")) != "report_visible"
        or _text(span.get("source")) != "electron_execution_control_center"
        or _text(span.get("measurement")) != "observed_control_center_progress"
        or _text(span.get("observer_plane")) != "execution_control_center"
    ):
        return None
    span_id = _text(span.get("span_id"))
    prefix = "execution-control-center:"
    snapshot_fingerprint = span_id[len(prefix):].lower() if span_id.startswith(prefix) else ""
    if len(snapshot_fingerprint) != 64 or any(char not in "0123456789abcdef" for char in snapshot_fingerprint):
        return None
    handoff = runtime.orchestration_ledger.problem_handoff_for_run(run_id)
    if not isinstance(handoff, dict):
        return None
    problem_id = _text(handoff.get("active_problem_id"))
    revision = int(handoff.get("problem_revision") or 0)
    binding = _exact_current_problem(runtime, problem_id, revision)
    if binding is None or binding["run_id"] != run_id or binding["wave_id"] != wave_id:
        return None
    return _append_unique_event(
        runtime.orchestration_ledger,
        run_id=run_id,
        wave_id=wave_id,
        event_type=_CONTROL_CENTER_EVENT,
        payload={
            "problem_id": problem_id,
            "problem_revision": revision,
            "observer_plane": "execution_control_center",
            "progress_visible": True,
            "snapshot_fingerprint": snapshot_fingerprint,
            "observation_span_id": span_id,
            "attestation_verified": True,
            "attestation_source": _text(identity.get("attestation_source")) or "managed_tunnel",
        },
    )["event"]


def _current_reattach(
    ledger: Any, *, workspace_id: str, problem_id: str, problem_revision: int
) -> dict[str, Any] | None:
    if not workspace_id:
        return None
    attachment = ledger.controller_goal_attachment(workspace_id=workspace_id, problem_id=problem_id)
    if not isinstance(attachment, dict) or int(attachment.get("problem_revision") or 0) != problem_revision:
        return None
    reattach_id = _text(attachment.get("last_reattach_id"))
    receipt = ledger.controller_reattach_receipt(reattach_id) if reattach_id else None
    if (
        not isinstance(receipt, dict)
        or _text(receipt.get("problem_id")) != problem_id
        or int(receipt.get("problem_revision") or 0) != problem_revision
        or _text(receipt.get("workspace_id")) != workspace_id
    ):
        return None
    return receipt


def record_goal_runtime_receipts(
    runtime: Any, args: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any] | None:
    """Reconstruct post-rotation Goal state from canonical PRL/proofs without transcripts."""
    if _text(args.get("goal_action") or "get").lower() not in {"get", "resolve"}:
        return None
    goal = result.get("goal_pursuit") if isinstance(result.get("goal_pursuit"), dict) else None
    identity = goal.get("identity") if isinstance(goal, dict) and isinstance(goal.get("identity"), dict) else {}
    problem_id = _text(identity.get("problem_id"))
    revision = identity.get("problem_revision")
    if not problem_id or isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        return None
    binding = _exact_current_problem(runtime, problem_id, revision)
    if binding is None:
        return None
    ledger = runtime.orchestration_ledger
    events = _problem_runtime_events(ledger, problem_id, revision)
    session_b = next(
        (
            event for event in reversed(events)
            if event.get("event_type") == _SESSION_EVENT
            and _text((event.get("payload") or {}).get("session_role")).upper() == "B"
            and _text((event.get("payload") or {}).get("workspace_id")) == binding["workspace_id"]
        ),
        None,
    )
    if session_b is None:
        return None
    reattach = _current_reattach(
        ledger,
        workspace_id=binding["workspace_id"],
        problem_id=problem_id,
        problem_revision=revision,
    )
    if reattach is None:
        return None
    endpoint = _text((session_b.get("payload") or {}).get("controller_endpoint_id"))
    if endpoint and endpoint != _text(reattach.get("controller_endpoint_id")):
        return None

    pairs = _problem_run_wave_pairs(ledger, problem_id, revision)
    jobs: list[dict[str, Any]] = []
    with ledger._lock, ledger._connect() as connection:
        for pair_run, pair_wave in pairs:
            rows = connection.execute(
                """SELECT job_id,command_id,run_id,wave_id,updated_at FROM managed_process_jobs
                   WHERE run_id=? AND wave_id=? AND job_id<>'' AND command_id<>''
                   ORDER BY updated_at DESC,job_id DESC LIMIT 1""",
                (pair_run, pair_wave),
            ).fetchall()
            jobs.extend(dict(row) for row in rows)
    latest_job = max(jobs, key=lambda row: (_text(row.get("updated_at")), _text(row.get("job_id"))), default=None)
    reobserved = None
    if latest_job is not None:
        reobserved = _append_unique_event(
            ledger,
            run_id=binding["run_id"],
            wave_id=binding["wave_id"],
            event_type=_REOBSERVED_EVENT,
            payload={
                "problem_id": problem_id,
                "problem_revision": revision,
                "job_id": _text(latest_job.get("job_id")),
                "command_id": _text(latest_job.get("command_id")),
                "reattach_id": _text(reattach.get("reattach_id")),
                "duplicate_execution_started": False,
                "session_b_event_id": _text(session_b.get("event_id")),
                "observation_source": "goal_read_existing_managed_job",
            },
        )["event"]

    criterion_coverage = goal.get("criterion_coverage") if isinstance(goal.get("criterion_coverage"), dict) else {}
    criterion_ids = sorted(_text(item) for item in criterion_coverage if _text(item))
    next_gap_id = _text(goal.get("next_critical_gap_id"))
    next_action = _text(goal.get("next_action"))
    proof_ids: list[str] = []
    for pair_run, pair_wave in pairs:
        proof_ids.extend(
            _text(proof.get("proof_id"))
            for proof in ledger.list_proofs(pair_run, wave_id=pair_wave)
            if _text(proof.get("status")) == "passed" and _text(proof.get("proof_id"))
        )
    proof_ids = sorted(set(proof_ids))[:32]
    reconstruction = None
    if criterion_ids and next_gap_id in criterion_ids and next_action and proof_ids:
        reconstruction = _append_unique_event(
            ledger,
            run_id=binding["run_id"],
            wave_id=binding["wave_id"],
            event_type=_RECONSTRUCTION_EVENT,
            payload={
                "problem_id": problem_id,
                "problem_revision": revision,
                "criteria_total": len(criterion_ids),
                "criterion_ids": criterion_ids,
                "proof_ids": proof_ids,
                "next_gap_id": next_gap_id,
                "next_action": next_action,
                "transcript_replayed": False,
                "ack_id": _text(reattach.get("ack_id")),
                "reattach_id": _text(reattach.get("reattach_id")),
                "reconstruction_source": "canonical_goal_projection_and_passed_proofs",
            },
        )["event"]
    return {"reobserved": reobserved, "reconstruction": reconstruction}


def record_accepted_remaining_criterion(
    runtime: Any,
    *,
    run_id: str,
    wave_id: str,
    coverage_manifest: Any,
    checkpoint_id: str,
) -> dict[str, Any] | None:
    """Record completion only for the exact gap previously reconstructed in Session B."""
    if not isinstance(coverage_manifest, dict) or not checkpoint_id:
        return None
    handoff = runtime.orchestration_ledger.problem_handoff_for_run(run_id)
    if not isinstance(handoff, dict):
        return None
    problem_id = _text(handoff.get("active_problem_id"))
    revision = int(handoff.get("problem_revision") or 0)
    binding = _exact_current_problem(runtime, problem_id, revision)
    if binding is None or binding["run_id"] != run_id or binding["wave_id"] != wave_id:
        return None
    events = _problem_runtime_events(runtime.orchestration_ledger, problem_id, revision)
    reconstruction = next(
        (
            event for event in reversed(events)
            if event.get("event_type") == _RECONSTRUCTION_EVENT
            and _text((event.get("payload") or {}).get("next_gap_id"))
        ),
        None,
    )
    if reconstruction is None:
        return None
    criterion_id = _text((reconstruction.get("payload") or {}).get("next_gap_id"))
    references = coverage_manifest.get(criterion_id)
    if not isinstance(references, list) or not references:
        return None
    passed = {
        _text(proof.get("proof_id"))
        for proof in runtime.orchestration_ledger.list_proofs(run_id, wave_id=wave_id)
        if _text(proof.get("status")) == "passed"
    }
    proof_id = next((_text(item) for item in references if _text(item) in passed), "")
    if not proof_id:
        return None
    return _append_unique_event(
        runtime.orchestration_ledger,
        run_id=run_id,
        wave_id=wave_id,
        event_type=_CRITERION_COMPLETED_EVENT,
        payload={
            "problem_id": problem_id,
            "problem_revision": revision,
            "criterion_id": criterion_id,
            "proof_id": proof_id,
            "checkpoint_id": checkpoint_id,
            "completion_source": "accepted_problem_coverage_manifest",
        },
    )["event"]
