"""Bounded Problem-Revision journey and resource projections.

This module consumes only immutable in-memory ledger facts.  It deliberately
keeps controller, provider, tool, continuity, and human evidence in separate
planes so absent telemetry cannot become a plausible zero or a double-counted
"total model tokens" value.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from .usage_ledger import CANONICAL_USAGE_KEYS, canonical_usage_payload


_CORRECTION_INTENTS = frozenset(
    {
        "SAME_PROBLEM_STILL_FAILING",
        "CORRECT_UNDERSTANDING",
        "CORRECT_TARGET_OR_SCOPE",
        "CORRECT_TECHNICAL_RESULT",
        "CORRECT_PROOF_OR_VERIFICATION",
        "ADD_CONSTRAINT_OR_REQUIREMENT",
    }
)
_REJECTED_RUN_STATES = frozenset({"rejected", "aborted", "failed"})
_REJECTED_WAVE_STATES = frozenset({"rejected", "aborted", "failed"})
_RECOVERY_ACK_STATES = frozenset({"BEHIND", "MISSING", "INVALID", "FUTURE", "HISTORY_LOST"})


def _text(value: Any) -> str:
    return str(value or "").strip()


def _unknown(reason: str, *, unit: str, field: str = "value") -> dict[str, Any]:
    return {
        "status": "UNAVAILABLE",
        field: None,
        "unit": unit,
        "missing_reason": reason,
        "unknown_is_not_zero": True,
    }


def _observed(value: Any, *, unit: str, field: str = "value", source: str) -> dict[str, Any]:
    return {
        "status": "OBSERVED",
        field: value,
        "unit": unit,
        "source": source,
        "missing_reason": None,
        "unknown_is_not_zero": True,
    }


def _ratio(numerator: int, denominator: int, *, reason: str) -> dict[str, Any]:
    return {
        "status": "OBSERVED" if denominator else "UNAVAILABLE",
        "numerator": numerator,
        "denominator": denominator,
        "rate": round(numerator / denominator, 6) if denominator else None,
        "missing_reason": None if denominator else reason,
        "unknown_is_not_zero": True,
    }


def _problem_context(wave: dict[str, Any]) -> dict[str, Any]:
    metadata = wave.get("metadata") if isinstance(wave.get("metadata"), dict) else {}
    context = metadata.get("problem_resolution") if isinstance(metadata.get("problem_resolution"), dict) else {}
    return context if isinstance(context, dict) else {}


def _exact_revision_attempts(
    ledger: Any,
    events: list[dict[str, Any]],
    problem_id: str,
    revision: int,
) -> tuple[dict[str, tuple[str, ...]], list[str]]:
    """Return exact Problem-Revision RUN -> eligible WAVE attribution.

    An exact primary link establishes that a RUN belongs to the revision, but
    it does not make every WAVE or usage event in that RUN attributable.  The
    returned WAVE IDs therefore require their own durable Problem Resolution
    context to match.  This keeps a later unrelated WAVE in a reused RUN from
    being charged to the original Problem Revision.
    """
    candidates = {
        _text(event.get("run_id"))
        for event in events
        if int(event.get("event_schema_version") or 1) >= 2
        and bool(event.get("eligible_for_policy"))
        and _text(event.get("link_status")) == "EXACT"
        and _text(event.get("link_role")) == "PRIMARY"
        and _text(event.get("relation_type")) in {"LINK", "ENGINEERING_ATTEMPT_BOUND"}
        and _text(event.get("run_id"))
    }
    result: dict[str, tuple[str, ...]] = {}
    mismatched: list[str] = []
    for run_id in sorted(candidates):
        wave_ids = tuple(
            sorted(
                _text(wave.get("wave_id"))
                for wave in ledger.list_waves(run_id)
                if _text(wave.get("wave_id"))
                and _problem_context(wave).get("work_origin") == "problem"
                and _problem_context(wave).get("problem_id") == problem_id
                and _problem_context(wave).get("problem_revision") == revision
            )
        )
        if wave_ids:
            result[run_id] = wave_ids
        else:
            mismatched.append(run_id)
    return result, mismatched


def _actor_usage(
    events: list[dict[str, Any]],
    actor: str,
    *,
    run_id: str,
    eligible_wave_ids: set[str],
    provider_dispatches: int = 0,
) -> dict[str, Any]:
    actor_events = [event for event in events if _text(event.get("actor") or "provider").lower() == actor]
    selected: list[dict[str, Any]] = []
    excluded = Counter()
    for event in actor_events:
        if _text(event.get("run_id")) != run_id:
            excluded["run_id_mismatch"] += 1
        elif _text(event.get("wave_id")) not in eligible_wave_ids:
            excluded["wave_not_exact_problem_revision"] += 1
        elif _text((event.get("attribution") or {}).get("status")).lower() != "exact":
            excluded["attribution_not_exact"] += 1
        else:
            selected.append(event)
    excluded_count = sum(excluded.values())
    if not selected and not actor_events and actor == "provider" and provider_dispatches == 0:
        return {
            "status": "OBSERVED_ZERO",
            "event_count": 0,
            "candidate_event_count": 0,
            "excluded_event_count": 0,
            "exclusion_reason_counts": {},
            "usage": {key: 0 for key in CANONICAL_USAGE_KEYS},
            "cost": {"value": 0.0, "complete": True, "measured_event_count": 0},
            "source": "no_provider_delegation_or_usage_event_in_exact_problem_wave",
            "missing_reason": None,
            "unknown_is_not_zero": True,
        }
    if not selected:
        return {
            "status": "UNOBSERVED",
            "event_count": 0,
            "candidate_event_count": len(actor_events),
            "excluded_event_count": excluded_count,
            "exclusion_reason_counts": dict(sorted(excluded.items())),
            "usage": None,
            "cost": {"value": None, "complete": False, "measured_event_count": 0},
            "source": "durable_usage_events_exact_problem_revision_wave",
            "missing_reason": (
                f"no_exact_{actor}_usage_event_for_exact_problem_wave"
                if excluded_count
                else f"no_exact_{actor}_usage_event_for_run"
            ),
            "unknown_is_not_zero": True,
        }
    usage = {key: 0 for key in CANONICAL_USAGE_KEYS}
    invalid = 0
    measured_costs: list[float] = []
    for event in selected:
        try:
            canonical = canonical_usage_payload(event)
        except (TypeError, ValueError):
            invalid += 1
            continue
        for key in CANONICAL_USAGE_KEYS:
            value = canonical.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
                usage[key] += int(value)
        measurement = event.get("measurement") if isinstance(event.get("measurement"), dict) else {}
        cost = event.get("cost") if isinstance(event.get("cost"), dict) else {}
        measured = cost.get("provider_cost")
        if measurement.get("cost") == "measured" and isinstance(measured, (int, float)) and not isinstance(measured, bool) and measured >= 0:
            measured_costs.append(float(measured))
    complete = invalid == 0 and excluded_count == 0
    cost_complete = complete and len(measured_costs) == len(selected)
    if complete:
        status = "OBSERVED"
        missing_reason = None
    elif invalid and not excluded_count:
        status = "PARTIAL_INVALID_EVENT"
        missing_reason = "invalid_usage_event_present"
    else:
        status = "PARTIAL"
        missing_reason = "usage_event_attribution_or_payload_incomplete_for_problem_revision"
    return {
        "status": status,
        "event_count": len(selected),
        "candidate_event_count": len(actor_events),
        "excluded_event_count": excluded_count,
        "exclusion_reason_counts": dict(sorted(excluded.items())),
        "invalid_event_count": invalid,
        "usage": usage if complete else None,
        "cost": {
            "value": round(sum(measured_costs), 12) if cost_complete else None,
            "complete": cost_complete,
            "measured_event_count": len(measured_costs),
        },
        "source": "durable_usage_events_exact_problem_revision_wave_separated_by_actor",
        "missing_reason": missing_reason,
        "unknown_is_not_zero": True,
    }


def _run_projection(ledger: Any, run_id: str, *, eligible_wave_ids: set[str]) -> dict[str, Any]:
    run = ledger.get_run(run_id) or {}
    all_waves = ledger.list_waves(run_id)
    waves = [wave for wave in all_waves if _text(wave.get("wave_id")) in eligible_wave_ids]
    events = ledger.list_events(run_id)
    delegations = [item for wave in waves for item in ledger.list_delegations(_text(wave.get("wave_id")))]
    usage_events = ledger.list_usage_events(run_id, limit=None)
    economics = ledger.accepted_result_economics(run_id)
    quality = ledger.latest_quality_outcome(run_id)
    wave_states = Counter(_text(wave.get("status")).lower() or "unknown" for wave in waves)
    replan_events = sum(1 for event in events if _text(event.get("event_type")) == "wave_replanned")
    status = _text(run.get("status")).lower() or "unknown"
    phase = economics.get("phase_timing") if isinstance(economics.get("phase_timing"), dict) else {}
    methodology = phase.get("methodology_phase_ms") if isinstance(phase.get("methodology_phase_ms"), dict) else {}
    phase_attribution_complete = len(waves) == len(all_waves)
    return {
        "run_id": run_id,
        "status": status,
        "terminal": bool(run.get("finished_at")),
        "accepted": status == "accepted",
        "rejected_or_aborted": status in _REJECTED_RUN_STATES,
        "first_pass_accepted": bool(economics.get("first_pass_accepted")),
        "wave_count": len(waves),
        "wave_status_counts": dict(sorted(wave_states.items())),
        "replan_wave_count": int(wave_states.get("replanned", 0)),
        "replan_event_count": replan_events,
        "rejected_wave_count": sum(wave_states.get(item, 0) for item in _REJECTED_WAVE_STATES),
        "failure_event_count": int((economics.get("repair") or {}).get("failure_event_count") or 0),
        "tta_ms": economics.get("tta_ms"),
        "phase_timing": {
            "complete": bool(phase.get("complete")) and phase_attribution_complete,
            "attribution_complete": phase_attribution_complete,
            "execution_ms": methodology.get("execution_window_ms") if phase_attribution_complete else None,
            "proof_ms": methodology.get("proof_ms") if phase_attribution_complete else None,
            "acceptance_ms": methodology.get("accept_wait_ms") if phase_attribution_complete else None,
            "replan_ms": methodology.get("replan_ms") if phase_attribution_complete else None,
            "missing_reason": None if phase_attribution_complete else "run_contains_non_exact_problem_waves",
        },
        "proof": dict(economics.get("proof") or {}),
        "resources": {
            "controller": _actor_usage(
                usage_events,
                "controller",
                run_id=run_id,
                eligible_wave_ids=eligible_wave_ids,
            ),
            "provider": _actor_usage(
                usage_events,
                "provider",
                run_id=run_id,
                eligible_wave_ids=eligible_wave_ids,
                provider_dispatches=len(delegations),
            ),
            "token_planes_are_non_overlapping_but_not_summed": True,
            "combined_model_tokens": None,
        },
        "quality": {
            "observed": isinstance(quality, dict),
            "manual_fix_required": quality.get("manual_fix_required") if isinstance(quality, dict) and isinstance(quality.get("manual_fix_required"), bool) else None,
            "critical_defect_count": quality.get("critical_defect_count") if isinstance(quality, dict) and isinstance(quality.get("critical_defect_count"), int) else None,
            "noncritical_defect_count": quality.get("noncritical_defect_count") if isinstance(quality, dict) and isinstance(quality.get("noncritical_defect_count"), int) else None,
            "rollback_required": quality.get("rollback_required") if isinstance(quality, dict) and isinstance(quality.get("rollback_required"), bool) else None,
        },
    }


def _sum_phase(runs: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [run["phase_timing"].get(key) for run in runs]
    observed = [float(value) for value in values if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0]
    return {
        "status": "OBSERVED" if len(observed) == len(values) and values else ("PARTIAL" if observed else "UNAVAILABLE"),
        "value_ms": round(sum(observed), 6) if observed else None,
        "observed_runs": len(observed),
        "run_count": len(values),
        "missing_reason": None if len(observed) == len(values) and values else "run_phase_timing_incomplete",
        "unknown_is_not_zero": True,
    }


def _combine_actor(runs: list[dict[str, Any]], actor: str) -> dict[str, Any]:
    planes = [run["resources"][actor] for run in runs]
    observed = [plane for plane in planes if plane.get("status") in {"OBSERVED", "OBSERVED_ZERO"}]
    attribution_incomplete = [
        plane
        for plane in planes
        if str(plane.get("status") or "").startswith("PARTIAL")
        or int(plane.get("excluded_event_count") or 0) > 0
    ]
    usage = {key: 0 for key in CANONICAL_USAGE_KEYS}
    exclusion_reasons = Counter()
    for plane in planes:
        reasons = plane.get("exclusion_reason_counts") if isinstance(plane.get("exclusion_reason_counts"), dict) else {}
        for reason, count in reasons.items():
            if isinstance(count, int) and not isinstance(count, bool) and count > 0:
                exclusion_reasons[_text(reason) or "unknown"] += count
    for plane in observed:
        for key in CANONICAL_USAGE_KEYS:
            usage[key] += int((plane.get("usage") or {}).get(key) or 0)
    cost_complete = bool(planes) and len(observed) == len(planes) and all(bool((plane.get("cost") or {}).get("complete")) for plane in planes)
    complete = bool(planes) and len(observed) == len(planes)
    partial = bool(observed or attribution_incomplete)
    return {
        "status": "OBSERVED" if complete else ("PARTIAL" if partial else "UNAVAILABLE"),
        "observed_runs": len(observed),
        "attribution_incomplete_runs": len(attribution_incomplete),
        "run_count": len(planes),
        "event_count": sum(int(plane.get("event_count") or 0) for plane in planes),
        "candidate_event_count": sum(int(plane.get("candidate_event_count") or 0) for plane in planes),
        "excluded_event_count": sum(int(plane.get("excluded_event_count") or 0) for plane in planes),
        "exclusion_reason_counts": dict(sorted(exclusion_reasons.items())),
        "usage": usage if observed else None,
        "cost": {
            "value": round(sum(float((plane.get("cost") or {}).get("value") or 0.0) for plane in planes), 12) if cost_complete else None,
            "complete": cost_complete,
        },
        "missing_reason": (
            None
            if complete
            else (
                f"{actor}_usage_attribution_incomplete_for_exact_problem_revision"
                if attribution_incomplete
                else f"{actor}_usage_not_observed_for_every_exact_run"
            )
        ),
        "unknown_is_not_zero": True,
    }


def _continuity_projection(problems: Any, problem_id: str, revision: int, run_ids: set[str]) -> dict[str, Any]:
    tables = set(problems.available_fact_tables)
    checkpoints = [row for row in problems.optional_rows("controller_knowledge_checkpoints") if _text(row.get("problem_id")) == problem_id and int(row.get("problem_revision") or 0) == revision]
    acks = [row for row in problems.optional_rows("controller_knowledge_acks") if _text(row.get("problem_id")) == problem_id and int(row.get("problem_revision") or 0) == revision]
    reattach = [row for row in problems.optional_rows("controller_reattach_receipts") if _text(row.get("problem_id")) == problem_id and int(row.get("problem_revision") or 0) == revision]
    capsules = [row for row in problems.optional_rows("handoff_capsules") if _text(row.get("run_id")) in run_ids]
    ack_states = Counter(_text(row.get("status")).upper() or "UNKNOWN" for row in acks)
    recovery_rows = [row for row in acks if _text(row.get("status")).upper() in _RECOVERY_ACK_STATES]
    delta_bytes = 0
    invalid_recovery_payloads = 0
    for row in recovery_rows:
        try:
            recovery = json.loads(_text(row.get("recovery_json")) or "{}")
            delta = recovery.get("delta") if isinstance(recovery, dict) else []
            delta_bytes += len(json.dumps(delta, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
        except (TypeError, json.JSONDecodeError):
            invalid_recovery_payloads += 1
    capsule_bytes = sum(len(_text(row.get("payload_json")).encode("utf-8")) for row in capsules)
    epochs = sorted({int(row.get("conversation_epoch") or 0) for row in capsules if int(row.get("conversation_epoch") or 0) > 0})
    endpoints = sorted({_text(row.get("controller_endpoint_id")) for row in [*acks, *reattach] if _text(row.get("controller_endpoint_id"))})
    continuity_tables = {
        "knowledge": "controller_knowledge_checkpoints" in tables,
        "ack": "controller_knowledge_acks" in tables,
        "reattach": "controller_reattach_receipts" in tables,
        "capsule": "handoff_capsules" in tables,
    }
    return {
        "controller_knowledge_checkpoints": _observed(len(checkpoints), unit="checkpoint", source="controller_knowledge_checkpoints") if continuity_tables["knowledge"] else _unknown("controller_knowledge_checkpoint_table_not_activated", unit="checkpoint"),
        "controller_recovery_events": _observed(len(recovery_rows), unit="knowledge_ack", source="typed_controller_knowledge_ack_status") if continuity_tables["ack"] else _unknown("controller_knowledge_ack_table_not_activated", unit="knowledge_ack"),
        "knowledge_ack_status_counts": dict(sorted(ack_states.items())),
        "recovery_delta_bytes": {
            **(_observed(delta_bytes, unit="utf8_json_byte", source="canonical_recovery_delta_json") if continuity_tables["ack"] and not invalid_recovery_payloads else _unknown("invalid_or_unavailable_recovery_delta_payload", unit="utf8_json_byte")),
            "invalid_recovery_payloads": invalid_recovery_payloads,
        },
        "stale_ack_recoveries": _observed(int(ack_states.get("BEHIND", 0)), unit="knowledge_ack", source="BEHIND_ack_with_bounded_delta") if continuity_tables["ack"] else _unknown("controller_knowledge_ack_table_not_activated", unit="knowledge_ack"),
        "invalid_or_unrecoverable_acks": _observed(sum(ack_states.get(item, 0) for item in {"INVALID", "FUTURE", "HISTORY_LOST"}), unit="knowledge_ack", source="typed_controller_knowledge_ack_status") if continuity_tables["ack"] else _unknown("controller_knowledge_ack_table_not_activated", unit="knowledge_ack"),
        "invalid_ack_recoveries": _unknown("invalid_future_or_history_lost_ack_does_not_prove_successful_recovery", unit="knowledge_ack"),
        "resume_successes": _observed(len(reattach), unit="reattach_receipt", source="controller_reattach_receipts") if continuity_tables["reattach"] else _unknown("controller_reattach_table_not_activated", unit="reattach_receipt"),
        "resume_attempts": _unknown("failed_reattach_attempts_are_not_durably_recorded", unit="resume_attempt"),
        "resume_ms": _unknown("reattach_start_and_reconstruction_completion_same_clock_not_recorded", unit="millisecond", field="value_ms"),
        "manual_resume_actions": _unknown("reattach_receipt_does_not_label_manual_vs_automatic_action", unit="action"),
        "capsule_bytes": _observed(capsule_bytes, unit="utf8_payload_byte", source="handoff_capsules.payload_json") if continuity_tables["capsule"] else _unknown("handoff_capsule_table_not_available", unit="utf8_payload_byte"),
        "capsule_count": _observed(len(capsules), unit="handoff_capsule", source="exact_run_linked_handoff_capsules") if continuity_tables["capsule"] else _unknown("handoff_capsule_table_not_available", unit="handoff_capsule"),
        "capsule_build_ms": _unknown("capsule_build_duration_not_recorded", unit="millisecond", field="value_ms"),
        "conversation_epochs_observed": _observed(epochs, unit="conversation_epoch", source="exact_run_linked_handoff_capsules", field="values") if continuity_tables["capsule"] else _unknown("handoff_capsule_table_not_available", unit="conversation_epoch", field="values"),
        "controller_endpoints_observed": _observed(endpoints, unit="opaque_controller_endpoint", source="ack_and_reattach_receipts", field="values") if continuity_tables["ack"] or continuity_tables["reattach"] else _unknown("controller_endpoint_receipts_not_activated", unit="opaque_controller_endpoint", field="values"),
        "chatweb_product_sessions_observed": _unknown("opaque_controller_endpoint_is_not_exact_product_chat_session_identity", unit="product_chat_session", field="values"),
        "rotation_count": _unknown("handoff_capsule_does_not_prove_product_session_rotation_completed", unit="rotation"),
        "duplicate_localization_after_resume": _unknown("causal_duplicate_localization_receipt_not_recorded", unit="operation"),
        "repeated_tool_reads_after_resume": _unknown("causal_repeated_read_receipt_not_recorded", unit="operation"),
        "no_advance_hot_path_count": _unknown("no_advance_decisions_are_not_durably_recorded", unit="decision"),
        "table_availability": continuity_tables,
    }


def _lifecycle_economics(events: list[dict[str, Any]], time: dict[str, Any]) -> dict[str, Any]:
    """Describe only lifecycle partitions that can be supported by exact facts.

    The ledger records an active-stage union for exact primary RUNs and an
    interval-censored Problem-Revision confirmation window.  It does not bind
    an active span to a particular technical acceptance event, or bind a
    reopened attempt to the reopen event clock.  Keep those allocations
    unavailable instead of inventing a partition from timestamp proximity.
    """
    provisional = next(
        (
            event
            for event in events
            if _text(event.get("relation_type")) == "PROVISIONAL_RESOLUTION"
            and bool(event.get("eligible_for_policy"))
        ),
        None,
    )
    confirmed = next(
        (
            event
            for event in events
            if _text(event.get("relation_type")) == "CONFIRMED_RESOLUTION"
            and bool(event.get("eligible_for_policy"))
        ),
        None,
    )
    reopens = [
        event
        for event in events
        if _text(event.get("relation_type")) == "REOPEN" and bool(event.get("eligible_for_policy"))
    ]
    active_union = time.get("restricted_ttpr_active_ms")
    confirmation_interval = time.get("ttpr_wall_interval")
    return {
        "schema_version": 1,
        "unit": "problem_revision",
        "policy": {
            "no_timestamp_proximity_partition": True,
            "no_cross_clock_sum": True,
            "unknown_is_not_zero": True,
            "later_unrelated_observation_not_charged": True,
        },
        "segments": {
            "pre_technical_acceptance": {
                "status": "UNAVAILABLE",
                "value_ms": None,
                "technical_acceptance_event_observed": provisional is not None,
                "active_stage_union": active_union,
                "missing_reason": "exact_active_span_to_technical_acceptance_boundary_not_recorded",
                "unknown_is_not_zero": True,
            },
            "post_technical_acceptance_confirmation_observation": {
                "status": (
                    _text(confirmation_interval.get("status"))
                    if isinstance(confirmation_interval, dict)
                    else "UNAVAILABLE"
                ),
                "value_ms": None,
                "technical_acceptance_event_observed": provisional is not None,
                "confirmation_event_observed": confirmed is not None,
                "confirmation_interval": dict(confirmation_interval)
                if isinstance(confirmation_interval, dict)
                else _unknown("technical_acceptance_to_confirmation_interval_not_recorded", unit="millisecond", field="value_ms"),
                "measurement": "interval_censored_attested_problem_event_clock",
                "not_an_exact_real_world_resolution_time": True,
                "unknown_is_not_zero": True,
            },
            "same_revision_reopened_rework": {
                "status": "OBSERVED_STRUCTURE_ONLY",
                "value_ms": None,
                "reopen_event_count": len(reopens),
                "first_reopen_event_seq": int(reopens[0].get("seq") or 0) if reopens else None,
                "missing_reason": "reopen_to_exact_run_or_wave_clock_boundary_not_recorded",
                "unknown_is_not_zero": True,
            },
            "later_unrelated_observation": {
                "status": "OUT_OF_SCOPE_UNOBSERVED",
                "value_ms": None,
                "excluded_from_problem_revision_economics": True,
                "missing_reason": "outside_exact_problem_revision_boundary",
                "unknown_is_not_zero": True,
            },
        },
    }


def problem_revision_journeys(
    ledger: Any,
    problems: Any,
    *,
    time_facts: list[dict[str, Any]],
    receipt_bound: Any,
) -> dict[str, Any]:
    """Return bounded exact-linked journeys without opening SQLite."""

    time_by_revision = {(item["problem_id"], int(item["problem_revision"])): item for item in time_facts}
    journeys: list[dict[str, Any]] = []
    all_run_ids: set[str] = set()
    attribution_conflicts: set[str] = set()
    attribution_mismatches: set[str] = set()
    for revision_row in problems.revisions:
        problem_id = _text(revision_row.get("problem_id"))
        revision = int(revision_row.get("revision") or 0)
        if not problem_id or revision < 1:
            continue
        events = problems.events_for_revision(problem_id, revision)
        attempts, mismatched_run_ids = _exact_revision_attempts(ledger, events, problem_id, revision)
        run_ids = list(attempts)
        attribution_mismatches.update(mismatched_run_ids)
        for run_id in run_ids:
            if run_id in all_run_ids:
                attribution_conflicts.add(run_id)
            all_run_ids.add(run_id)
        runs = [
            _run_projection(ledger, run_id, eligible_wave_ids=set(attempts[run_id]))
            for run_id in run_ids
        ]
        waves = sum(run["wave_count"] for run in runs)
        controller = _combine_actor(runs, "controller")
        provider = _combine_actor(runs, "provider")
        rework_runs = [
            run for run in runs
            if run["rejected_or_aborted"] or run["replan_wave_count"] or run["replan_event_count"]
        ]
        rework_controller = _combine_actor(rework_runs, "controller")
        rework_provider = _combine_actor(rework_runs, "provider")
        continuity = _continuity_projection(problems, problem_id, revision, set(run_ids))
        correction_events = [
            event for event in events
            if int(event.get("event_schema_version") or 1) >= 2
            and bool(event.get("eligible_for_policy"))
            and _text(event.get("provenance")) == "CONTROLLER_REPORTED_EXPLICIT_USER"
            and _text(event.get("feedback_intent")) in _CORRECTION_INTENTS
        ]
        correction_turns = {_text(event.get("turn_id")) for event in correction_events if _text(event.get("turn_id"))}
        unidentified_corrections = len(correction_events) - len([event for event in correction_events if _text(event.get("turn_id"))])
        manual_fix_values = [run["quality"]["manual_fix_required"] for run in runs]
        manual_fix_complete = bool(runs) and all(isinstance(value, bool) for value in manual_fix_values)
        confirmed = next((event for event in events if _text(event.get("relation_type")) == "CONFIRMED_RESOLUTION" and bool(event.get("eligible_for_policy"))), None)
        reopen_count = sum(1 for event in events if _text(event.get("relation_type")) == "REOPEN" and bool(event.get("eligible_for_policy")))
        time = time_by_revision.get((problem_id, revision), {})
        lifecycle = _lifecycle_economics(events, time)
        run_status_counts = Counter(run["status"] for run in runs)
        terminal_run_status_counts = Counter(run["status"] for run in runs if run["terminal"])
        wave_status_counts = Counter(
            status
            for run in runs
            for status, count in run["wave_status_counts"].items()
            for _ in range(int(count))
        )
        terminal_wave_status_counts = Counter(
            _text(wave.get("status")).lower() or "unknown"
            for run_id in run_ids
            for wave in ledger.list_waves(run_id)
            if _text(wave.get("wave_id")) in set(attempts[run_id]) and bool(wave.get("finished_at"))
        )
        total_cost_complete = bool(runs) and controller["cost"]["complete"] and provider["cost"]["complete"]
        total_cost = round(float(controller["cost"]["value"]) + float(provider["cost"]["value"]), 12) if total_cost_complete else None
        journeys.append(
            {
                "problem_id": problem_id,
                "problem_revision": revision,
                "outcome": {
                    "resolved_confirmed": confirmed is not None,
                    "receipt_bound_confirmation": bool(confirmed is not None and receipt_bound(confirmed)),
                    "reopen_count": reopen_count,
                    "false_closure_count": int(bool(reopen_count and any(_text(event.get("relation_type")) == "PROVISIONAL_RESOLUTION" for event in events))),
                },
                "time": {
                    **time,
                    "execution_ms": _sum_phase(runs, "execution_ms"),
                    "proof_ms": _sum_phase(runs, "proof_ms"),
                    "acceptance_ms": _sum_phase(runs, "acceptance_ms"),
                    "replan_ms": _sum_phase(runs, "replan_ms"),
                    "controller_gap_ms_observed": _unknown("same_clock_controller_idle_gap_not_recorded", unit="millisecond", field="value_ms"),
                },
                "lifecycle_economics": lifecycle,
                "topology": {
                    "run_count": len(runs),
                    "wave_count": waves,
                    "accepted_run_count": sum(int(run["accepted"]) for run in runs),
                    "rejected_or_aborted_run_count": sum(int(run["rejected_or_aborted"]) for run in runs),
                    "run_status_counts": dict(sorted(run_status_counts.items())),
                    "terminal_run_status_counts": dict(sorted(terminal_run_status_counts.items())),
                    "wave_status_counts": dict(sorted(wave_status_counts.items())),
                    "terminal_wave_status_counts": dict(sorted(terminal_wave_status_counts.items())),
                    "replan_wave_count": sum(run["replan_wave_count"] for run in runs),
                    "replan_event_count": sum(run["replan_event_count"] for run in runs),
                    "rejected_wave_count": sum(run["rejected_wave_count"] for run in runs),
                    "controller_knowledge_checkpoints": continuity["controller_knowledge_checkpoints"],
                    "controller_recovery_events": continuity["controller_recovery_events"],
                    "conversation_epochs": continuity["conversation_epochs_observed"],
                    "chatweb_sessions_observed": continuity["chatweb_product_sessions_observed"],
                    "rotation_count": continuity["rotation_count"],
                },
                "resources": {
                    "controller_tokens_exact_when_available": controller,
                    "provider_tokens": provider,
                    "model_visible_tool_bytes": _unknown("problem_attributed_model_visible_tool_bytes_not_recorded", unit="byte"),
                    "recovery_delta_bytes": continuity["recovery_delta_bytes"],
                    "large_result_continuation_bytes": _unknown("problem_attributed_large_result_continuation_bytes_not_recorded", unit="byte"),
                    "tool_invocation_count": _unknown("problem_attributed_tool_invocation_receipts_not_recorded", unit="tool_invocation"),
                    "retained_output_bytes": _unknown("problem_attributed_retained_output_bytes_not_recorded", unit="byte"),
                    "monetary_cost_complete_when_available": {
                        "status": "OBSERVED" if total_cost_complete else "UNAVAILABLE",
                        "value": total_cost,
                        "unit": "currency_as_reported",
                        "complete": total_cost_complete,
                        "missing_reason": None if total_cost_complete else "controller_or_provider_cost_plane_incomplete",
                        "unknown_is_not_zero": True,
                    },
                    "cross_plane_token_sum_forbidden": True,
                    "combined_model_tokens": None,
                    "rework": {
                        "run_ids": [run["run_id"] for run in rework_runs],
                        "controller": rework_controller,
                        "provider": rework_provider,
                        "controller_token_ratio": (
                            round(float((rework_controller.get("usage") or {}).get("total_tokens") or 0) / float((controller.get("usage") or {}).get("total_tokens")), 6)
                            if rework_controller.get("status") == "OBSERVED"
                            and controller.get("status") == "OBSERVED"
                            and float((controller.get("usage") or {}).get("total_tokens") or 0) > 0
                            else None
                        ),
                        "provider_token_ratio": (
                            round(float((rework_provider.get("usage") or {}).get("total_tokens") or 0) / float((provider.get("usage") or {}).get("total_tokens")), 6)
                            if rework_provider.get("status") == "OBSERVED"
                            and provider.get("status") == "OBSERVED"
                            and float((provider.get("usage") or {}).get("total_tokens") or 0) > 0
                            else None
                        ),
                        "cross_plane_ratio_forbidden": True,
                    },
                },
                "continuity": continuity,
                "human": {
                    "user_correction_turns": {
                        "status": "OBSERVED" if not unidentified_corrections else "PARTIAL",
                        "value": len(correction_turns) if not unidentified_corrections else None,
                        "observed_distinct_turns": len(correction_turns),
                        "unidentified_correction_events": unidentified_corrections,
                        "source": "typed_explicit_user_problem_feedback",
                        "missing_reason": None if not unidentified_corrections else "correction_event_turn_identity_missing",
                        "unknown_is_not_zero": True,
                    },
                    "manual_resume_actions": continuity["manual_resume_actions"],
                    "manual_fix_required": {
                        "status": "OBSERVED" if manual_fix_complete else "UNAVAILABLE",
                        "value": any(manual_fix_values) if manual_fix_complete else None,
                        "runs_requiring_manual_fix": sum(int(value) for value in manual_fix_values if isinstance(value, bool)),
                        "observed_runs": sum(int(isinstance(value, bool)) for value in manual_fix_values),
                        "run_count": len(runs),
                        "missing_reason": None if manual_fix_complete else "quality_outcome_manual_fix_not_recorded_for_every_run",
                        "unknown_is_not_zero": True,
                    },
                },
                "coverage": {
                    "controller_usage": _ratio(controller["observed_runs"], len(runs), reason="no_exact_runs"),
                    "provider_usage": _ratio(provider["observed_runs"], len(runs), reason="no_exact_runs"),
                    "tool_invocation": {"status": "UNAVAILABLE", "rate": None, "missing_reason": "problem_attributed_tool_invocation_receipts_not_recorded", "unknown_is_not_zero": True},
                    "problem_attribution": _ratio(len(runs), len(run_ids) + len(mismatched_run_ids), reason="no_exact_primary_run_links"),
                    "session_identity": {"status": "UNAVAILABLE", "rate": None, "missing_reason": "exact_product_chat_session_identity_not_exposed", "unknown_is_not_zero": True},
                    "continuity_revision": (
                        _ratio(1, 1, reason="continuity_table_state_unavailable")
                        if continuity["table_availability"]["knowledge"]
                        else {"status": "UNAVAILABLE", "numerator": None, "denominator": 1, "rate": None, "missing_reason": "controller_knowledge_checkpoint_table_not_activated", "unknown_is_not_zero": True}
                    ),
                    "outcome_receipt": _ratio(int(bool(confirmed is not None and receipt_bound(confirmed))), 1, reason="problem_revision_missing"),
                },
                "nested_per_run_economics": runs,
                "avoided_duplicate_read_or_localization": _unknown("causal_avoidance_receipt_not_recorded", unit="operation"),
            }
        )
    return {
        "schema_version": 2,
        "unit": "problem_revision",
        "journeys": journeys,
        "summary": {
            "problem_revision_count": len(journeys),
            "exact_linked_run_count": len(all_run_ids),
            "exact_linked_wave_count": sum(item["topology"]["wave_count"] for item in journeys),
            "accepted_run_count": sum(item["topology"]["accepted_run_count"] for item in journeys),
            "rejected_or_aborted_run_count": sum(item["topology"]["rejected_or_aborted_run_count"] for item in journeys),
            "replan_wave_count": sum(item["topology"]["replan_wave_count"] for item in journeys),
            "run_attribution_conflicts": sorted(attribution_conflicts),
            "run_metadata_attribution_mismatches": sorted(attribution_mismatches),
        },
        "query_evidence": {
            "ledger_fact_load_statements": int(getattr(ledger, "fact_load_statements", 0)),
            "problem_fact_load_statements": problems.fact_load_statements,
            "total_snapshot_fact_load_statements": int(getattr(ledger, "fact_load_statements", 0)) + problems.fact_load_statements,
            "n_plus_one_sqlite_queries": 0,
            "all_nested_run_wave_event_reads_from_immutable_memory": True,
            "fact_limits": dict(problems.fact_limits),
            "truncated_tables": sorted(problems.truncated_tables),
        },
        "policy": {
            "controller_provider_tool_planes_separate": True,
            "combined_token_total_with_cross_plane_overlap": None,
            "missing_is_unknown_not_zero": True,
            "timestamp_proximity_attribution_forbidden": True,
            "causal_avoidance_claim_requires_receipt": True,
            "read_only_no_schema_activation": True,
        },
    }
