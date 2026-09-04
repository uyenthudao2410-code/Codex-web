"""Read-only TG9 cohort projection over consecutive natural Problem Revisions.

The reporter composes existing immutable PRL economics and TG6 receipts.  It
does not enroll workload, infer natural provenance from objective text, skip an
unsuccessful row, or turn absent session-boundary evidence into a zero.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from .cross_session_continuity_report import (
    CrossSessionContinuityFacts,
    cross_session_continuity_report,
)
from .ledger_analysis import LedgerFacts
from .problem_lineage import PROBLEM_SCHEMA_VERSION
from .problem_resolution_economics import (
    ProblemLineageFacts,
    problem_resolution_economics_report,
)


NATURAL_PROBLEM_COHORT_SCHEMA_VERSION = 1
NATURAL_PROBLEM_COHORT_TARGETS = frozenset({5, 10})
_REPRESENTATIVE_PROVENANCE = frozenset(
    {"representative", "representative_project_task", "organic_representative"}
)
_AMBIGUITY_FAILURES = frozenset({"PATCH_AMBIGUOUS", "PATCH_CONTEXT_AMBIGUOUS"})
_STALE_SCOPE_FAILURES = frozenset(
    {
        "BASE_DRIFT",
        "CANDIDATE_SCOPE_VIOLATION",
        "CONTRACT_DRIFT",
        "STALE_SCOPE",
        "STALE_WORKSPACE_CONTEXT",
    }
)


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


def _observed(value: Any, *, unit: str, source: str, field: str = "value") -> dict[str, Any]:
    return {
        "status": "OBSERVED",
        field: value,
        "unit": unit,
        "source": source,
        "missing_reason": None,
        "unknown_is_not_zero": True,
    }


def _gate(report: dict[str, Any], gate_id: str) -> dict[str, Any]:
    return next(
        (item for item in report.get("gates") or [] if item.get("gate_id") == gate_id),
        {},
    )


def _event_payload(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("payload")
    if isinstance(value, dict):
        return dict(value)
    try:
        decoded = json.loads(_text(row.get("payload_json")) or "{}")
    except (TypeError, json.JSONDecodeError):
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _exact_primary_run_ids(events: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            _text(event.get("run_id"))
            for event in events
            if int(event.get("event_schema_version") or 1) >= 2
            and bool(event.get("eligible_for_policy"))
            and _text(event.get("link_status")) == "EXACT"
            and _text(event.get("link_role")) == "PRIMARY"
            and _text(event.get("relation_type"))
            in {"LINK", "ENGINEERING_ATTEMPT_BOUND"}
            and _text(event.get("run_id"))
        }
    )


def _run_natural_provenance(run: dict[str, Any]) -> dict[str, Any]:
    metadata = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
    evaluation = (
        metadata.get("evaluation") if isinstance(metadata.get("evaluation"), dict) else {}
    )
    provenance = _text(
        evaluation.get("provenance")
        or metadata.get("promotion_provenance")
        or metadata.get("evidence_provenance")
    ).lower()
    provenance_source = _text(metadata.get("provenance_source"))
    explicit_natural = (
        evaluation.get("representative_natural_task") is True
        or metadata.get("representative_natural_task") is True
        or provenance == "organic_representative"
        or (
            provenance == "representative"
            and provenance_source == "runtime_default_organic_v1"
        )
    )
    representative = provenance in _REPRESENTATIVE_PROVENANCE
    return {
        "run_id": _text(run.get("run_id")),
        "status": "PASS" if representative and explicit_natural else "UNAVAILABLE",
        "provenance": provenance or None,
        "provenance_source": provenance_source or None,
        "representative": representative,
        "explicit_natural": explicit_natural,
        "objective_text_inference_used": False,
        "missing_reason": (
            None
            if representative and explicit_natural
            else "typed_representative_natural_provenance_missing"
        ),
    }


def _prewrite_binding(
    ledger: LedgerFacts,
    run_ids: list[str],
    problem_id: str,
    revision: int,
) -> dict[str, Any]:
    if not run_ids:
        return _unknown("exact_primary_run_missing", unit="problem_revision_binding")
    rows: list[dict[str, Any]] = []
    for run_id in run_ids:
        run = ledger.get_run(run_id) or {}
        metadata = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
        context = (
            metadata.get("problem_resolution")
            if isinstance(metadata.get("problem_resolution"), dict)
            else {}
        )
        exact = (
            context.get("work_origin") == "problem"
            and context.get("problem_id") == problem_id
            and context.get("problem_revision") == revision
        )
        first_write = next(
            (
                event
                for event in ledger.list_events(run_id)
                if _text(event.get("event_type")) == "write_lease_acquired"
            ),
            None,
        )
        rows.append(
            {
                "run_id": run_id,
                "exact_problem_revision_in_run_creation_metadata": exact,
                "first_material_write_event_observed": first_write is not None,
                "first_material_write_seq": (
                    int(first_write.get("seq") or 0) if first_write is not None else None
                ),
            }
        )
    passed = sum(int(row["exact_problem_revision_in_run_creation_metadata"]) for row in rows)
    return {
        "status": "PASS" if passed == len(rows) else "FAIL",
        "numerator": passed,
        "denominator": len(rows),
        "coverage": round(passed / len(rows), 6),
        "unit": "exact_primary_run",
        "rows": rows,
        "source": "immutable_run_creation_metadata_precedes_run_event_log",
        "missing_reason": None if passed == len(rows) else "exact_prewrite_binding_incomplete",
        "unknown_is_not_zero": True,
    }


def _failure_incidence(ledger: LedgerFacts, run_ids: list[str]) -> dict[str, Any]:
    if not run_ids:
        return {
            "edit_ambiguity": _unknown("exact_primary_run_missing", unit="failure_event"),
            "stale_or_scope_rejection": _unknown(
                "exact_primary_run_missing", unit="failure_event"
            ),
            "failure_class_counts": {},
        }
    classes: Counter[str] = Counter()
    for run_id in run_ids:
        for event in ledger.list_events(run_id):
            if _text(event.get("event_type")) != "failure_observed":
                continue
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            classes[_text(payload.get("failure_class")).upper() or "UNKNOWN"] += 1
    return {
        "edit_ambiguity": _observed(
            sum(classes[item] for item in _AMBIGUITY_FAILURES),
            unit="failure_event",
            source="exact_run_failure_observed.failure_class",
        ),
        "stale_or_scope_rejection": _observed(
            sum(classes[item] for item in _STALE_SCOPE_FAILURES),
            unit="failure_event",
            source="exact_run_failure_observed.failure_class",
        ),
        "failure_class_counts": dict(sorted(classes.items())),
    }


def _egri_enrichment(ledger: LedgerFacts, run_ids: list[str]) -> dict[str, Any]:
    if not run_ids:
        return _unknown("exact_primary_run_missing", unit="problem_frame_shadow")
    count = sum(
        1
        for run_id in run_ids
        for event in ledger.list_events(run_id)
        if _text(event.get("event_type")) == "problem_frame_shadow"
    )
    return {
        **_observed(
            count,
            unit="problem_frame_shadow",
            source="exact_run_problem_frame_shadow_events",
        ),
        "enrichment": "PRESENT" if count else "ABSENT",
        "causal_value_proven": False,
    }


def _journey_by_identity(economics: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    journeys = (economics.get("problem_revision_journeys") or {}).get("journeys") or []
    return {
        (_text(row.get("problem_id")), int(row.get("problem_revision") or 0)): row
        for row in journeys
        if _text(row.get("problem_id")) and int(row.get("problem_revision") or 0) > 0
    }


def _session_boundary(cross_session: dict[str, Any]) -> dict[str, Any]:
    accepted = cross_session.get("accepted_real_cross_session_continuity_receipt") is True
    observed_gate_ids = [
        gate_id
        for gate_id in ("TG6-02", "TG6-09", "TG6-10")
        if _gate(cross_session, gate_id).get("status") == "PASS"
    ]
    if accepted:
        condition = "REAL_CROSS_SESSION_PASS"
    elif observed_gate_ids:
        condition = "INSTRUMENTED_BOUNDARY_INCOMPLETE"
    else:
        condition = "SESSION_BOUNDARY_UNOBSERVED"
    return {
        "status": "PASS" if accepted else "UNAVAILABLE",
        "condition": condition,
        "accepted_real_cross_session_continuity_receipt": accepted,
        "observed_boundary_gate_ids": observed_gate_ids,
        "gate_counts": dict(cross_session.get("gate_counts") or {}),
        "missing_reason": None if accepted else "full_tg6_cross_session_receipt_missing",
        "endpoint_generation_used_as_product_session_identity": False,
        "unknown_is_not_zero": True,
    }


def _raw_row(
    ledger: LedgerFacts,
    problems: ProblemLineageFacts,
    continuity_facts: CrossSessionContinuityFacts,
    journey: dict[str, Any] | None,
    revision_row: dict[str, Any],
) -> dict[str, Any]:
    problem_id = _text(revision_row.get("problem_id"))
    revision = int(revision_row.get("revision") or 0)
    problem_events = problems.events_for_revision(problem_id, revision)
    run_ids = _exact_primary_run_ids(problem_events)
    runs = [ledger.get_run(run_id) or {} for run_id in run_ids]
    provenance_rows = [_run_natural_provenance(run) for run in runs]
    chain = problems.verify_chain(problem_id)
    natural = bool(
        run_ids
        and len(runs) == len(run_ids)
        and all(row.get("status") == "PASS" for row in provenance_rows)
        and chain.get("ok") is True
    )
    cross_session = cross_session_continuity_report(
        ledger,
        problems,
        continuity_facts,
        problem_id=problem_id,
        problem_revision=revision,
    )
    journey_value = journey or {}
    continuity = (
        journey_value.get("continuity")
        if isinstance(journey_value.get("continuity"), dict)
        else {}
    )
    topology = (
        journey_value.get("topology")
        if isinstance(journey_value.get("topology"), dict)
        else {}
    )
    resources = (
        journey_value.get("resources")
        if isinstance(journey_value.get("resources"), dict)
        else {}
    )
    failure = _failure_incidence(ledger, run_ids)
    core_receipts = sum(
        1
        for run_id in run_ids
        for event in ledger.list_events(run_id)
        if _text(event.get("event_type")) == "continuity_core_recorded"
    )
    exact_ledger_events = [
        row
        for row in continuity_facts.rows("events")
        if _text(row.get("run_id")) in set(run_ids)
    ]
    session_receipt_ids = {
        _text(_event_payload(row).get("product_session_receipt_id"))
        for row in exact_ledger_events
        if _text(row.get("event_type")) == "cross_session_chatweb_session_started"
        and _event_payload(row).get("problem_id") == problem_id
        and _event_payload(row).get("problem_revision") == revision
        and _text(_event_payload(row).get("receipt_type"))
        == "CHATWEB_PRODUCT_SESSION_GOAL_PURSUIT_V1"
        and _text(_event_payload(row).get("product_session_receipt_id"))
    }
    rotation_receipt_ids = {
        _text(row.get("event_id"))
        for row in exact_ledger_events
        if _text(row.get("event_type")) == "cross_session_chatweb_session_rotated"
        and _event_payload(row).get("problem_id") == problem_id
        and _event_payload(row).get("problem_revision") == revision
        and _text(_event_payload(row).get("receipt_type"))
        == "CHATWEB_PRODUCT_SESSION_ROTATION_V1"
        and _text(_event_payload(row).get("outgoing_product_session_receipt_id"))
    }
    session_count = (
        _observed(
            len(session_receipt_ids),
            unit="product_session",
            source="typed_exact_problem_chatweb_product_session_receipts",
        )
        if session_receipt_ids
        else _unknown(
            "typed_product_session_receipt_unobserved", unit="product_session"
        )
    )
    rotation_count = (
        _observed(
            len(rotation_receipt_ids),
            unit="typed_intentional_rotation",
            source="typed_exact_problem_rotation_receipts",
        )
        if rotation_receipt_ids
        else _unknown(
            "typed_intentional_rotation_receipt_unobserved",
            unit="typed_intentional_rotation",
        )
    )
    return {
        "problem_id": problem_id,
        "problem_revision": revision,
        "created_event_seq": int(revision_row.get("created_event_seq") or 0),
        "created_at": _text(revision_row.get("created_at")) or None,
        "natural_problem_eligibility": {
            "status": "PASS" if natural else "UNAVAILABLE",
            "eligible": natural,
            "exact_primary_run_ids": run_ids,
            "run_provenance": provenance_rows,
            "problem_event_chain_valid": chain.get("ok") is True,
            "success_or_terminal_status_filter_used": False,
            "objective_text_inference_used": False,
            "missing_reason": None if natural else "typed_natural_problem_evidence_incomplete",
        },
        "metrics": {
            "problem_revision_before_first_material_write": _prewrite_binding(
                ledger, run_ids, problem_id, revision
            ),
            "trusted_resolution": dict(journey_value.get("outcome") or {})
            if journey
            else _unknown("exact_problem_revision_journey_missing", unit="problem_revision"),
            "ttpr": dict(journey_value.get("time") or {})
            if journey
            else _unknown("exact_problem_revision_journey_missing", unit="millisecond"),
            "sessions_per_problem": session_count,
            "rotations_per_problem": rotation_count,
            "controller_knowledge_checkpoints": continuity.get(
                "controller_knowledge_checkpoints",
                _unknown("continuity_journey_missing", unit="checkpoint"),
            ),
            "stale_or_missing_recovery": {
                "events": continuity.get(
                    "controller_recovery_events",
                    _unknown("continuity_journey_missing", unit="knowledge_ack"),
                ),
                "stale_ack_recoveries": continuity.get(
                    "stale_ack_recoveries",
                    _unknown("continuity_journey_missing", unit="knowledge_ack"),
                ),
                "ack_status_counts": dict(continuity.get("knowledge_ack_status_counts") or {}),
            },
            "resume": {
                "attempts": continuity.get(
                    "resume_attempts", _unknown("continuity_journey_missing", unit="attempt")
                ),
                "successes": continuity.get(
                    "resume_successes",
                    _unknown("continuity_journey_missing", unit="reattach_receipt"),
                ),
                "reconstruction_time": continuity.get(
                    "resume_ms", _unknown("continuity_journey_missing", unit="millisecond")
                ),
            },
            "duplicate_after_resume": {
                "localization": continuity.get(
                    "duplicate_localization_after_resume",
                    _unknown("continuity_journey_missing", unit="operation"),
                ),
                "repeated_reads": continuity.get(
                    "repeated_tool_reads_after_resume",
                    _unknown("continuity_journey_missing", unit="operation"),
                ),
            },
            "large_result_continuation": _unknown(
                "problem_attributed_large_result_continuation_receipt_not_recorded",
                unit="continuation",
            ),
            "edit_ambiguity_and_stale_scope_rejection": failure,
            "user_correction_turns": (
                (journey_value.get("human") or {}).get(
                    "user_correction_turns",
                    _unknown("exact_problem_revision_journey_missing", unit="turn"),
                )
            ),
            "usage_coverage": {
                "controller": (journey_value.get("coverage") or {}).get(
                    "controller_usage",
                    _unknown("exact_problem_revision_journey_missing", unit="coverage"),
                ),
                "provider": (journey_value.get("coverage") or {}).get(
                    "provider_usage",
                    _unknown("exact_problem_revision_journey_missing", unit="coverage"),
                ),
                "tool": (journey_value.get("coverage") or {}).get(
                    "tool_invocation",
                    _unknown("problem_attributed_tool_receipts_missing", unit="coverage"),
                ),
            },
            "governance_friction": {
                "run_count": topology.get("run_count"),
                "wave_count": topology.get("wave_count"),
                "replan_event_count": topology.get("replan_event_count"),
                "rejected_or_aborted_run_count": topology.get(
                    "rejected_or_aborted_run_count"
                ),
                "failure_class_counts": failure["failure_class_counts"],
                "classification": "descriptive_structured_receipts_only",
            },
            "continuity_core_overhead": {
                "core_receipts": _observed(
                    core_receipts,
                    unit="continuity_core_receipt",
                    source="exact_run_continuity_core_recorded_events",
                )
                if run_ids
                else _unknown("exact_primary_run_missing", unit="continuity_core_receipt"),
                "recovery_delta_bytes": continuity.get(
                    "recovery_delta_bytes",
                    _unknown("continuity_journey_missing", unit="utf8_json_byte"),
                ),
                "capsule_bytes": continuity.get(
                    "capsule_bytes",
                    _unknown("continuity_journey_missing", unit="utf8_payload_byte"),
                ),
                "build_time": continuity.get(
                    "capsule_build_ms",
                    _unknown("continuity_journey_missing", unit="millisecond"),
                ),
            },
            "egri_enrichment": _egri_enrichment(ledger, run_ids),
            "session_boundary_condition": _session_boundary(cross_session),
            "resource_economics": resources,
        },
    }


def _missingness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    reasons: Counter[str] = Counter()

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            status = _text(value.get("status")).upper()
            if status in {"UNAVAILABLE", "PARTIAL", "FAIL", "INCOMPLETE"}:
                counts[path or "root"] += 1
                reasons[_text(value.get("missing_reason")) or status.lower()] += 1
            for key, child in value.items():
                visit(child, f"{path}.{key}" if path else str(key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    for row in rows:
        visit(row.get("metrics") or {}, "metrics")
    return {
        "missing_or_incomplete_observation_count": sum(counts.values()),
        "by_metric_path": dict(sorted(counts.items())),
        "reason_counts": dict(sorted(reasons.items())),
        "missing_is_unknown_not_zero": True,
    }


def _checkpoint(rows: list[dict[str, Any]], n: int) -> dict[str, Any]:
    prefix = rows[:n]
    complete = len(prefix) == n
    natural = sum(
        int((row.get("natural_problem_eligibility") or {}).get("eligible") is True)
        for row in prefix
    )
    cross_session = sum(
        int(
            ((row.get("metrics") or {}).get("session_boundary_condition") or {}).get(
                "accepted_real_cross_session_continuity_receipt"
            )
            is True
        )
        for row in prefix
    )
    false_closures = sum(
        int(((row.get("metrics") or {}).get("trusted_resolution") or {}).get("false_closure_count") or 0)
        for row in prefix
    )
    reopens = sum(
        int(((row.get("metrics") or {}).get("trusted_resolution") or {}).get("reopen_count") or 0)
        for row in prefix
    )
    if not complete:
        decision = "COLLECTING"
    elif natural != n:
        decision = "REJECT_NONCONSECUTIVE_OR_UNVERIFIED_NATURAL_COHORT"
    else:
        decision = "DESCRIPTIVE_REVIEW_REQUIRED"
    return {
        "n": n,
        "status": "READY_FOR_DESCRIPTIVE_REVIEW" if decision == "DESCRIPTIVE_REVIEW_REQUIRED" else decision,
        "decision": decision,
        "observed_rows": len(prefix),
        "typed_natural_rows": natural,
        "real_cross_session_pass_rows": cross_session,
        "false_closure_count": false_closures,
        "reopen_count": reopens,
        "row_identities": [
            {"problem_id": row["problem_id"], "problem_revision": row["problem_revision"]}
            for row in prefix
        ],
        "material_reduction_conclusion": None,
        "causal_claim_allowed": False,
        "operator_review_required": complete and natural == n,
    }


def natural_problem_cohort_report(
    ledger: LedgerFacts,
    problems: ProblemLineageFacts,
    continuity_facts: CrossSessionContinuityFacts,
    *,
    start_problem_id: str,
    start_problem_revision: int,
    target_n: int = 10,
) -> dict[str, Any]:
    """Project a fixed chronological prefix without opening SQLite or writing state."""

    if not isinstance(ledger, LedgerFacts):
        raise TypeError("natural Problem cohort requires immutable LedgerFacts")
    if not isinstance(problems, ProblemLineageFacts):
        raise TypeError("natural Problem cohort requires immutable ProblemLineageFacts")
    if not isinstance(continuity_facts, CrossSessionContinuityFacts):
        raise TypeError("natural Problem cohort requires CrossSessionContinuityFacts")
    start_id = _text(start_problem_id)
    if not start_id or len(start_id) > 128:
        raise ValueError("start_problem_id is required and must be at most 128 characters")
    if isinstance(start_problem_revision, bool) or start_problem_revision < 1:
        raise ValueError("start_problem_revision must be a positive integer")
    if target_n not in NATURAL_PROBLEM_COHORT_TARGETS:
        raise ValueError("target_n must be 5 or 10")

    truncated = sorted(set(problems.truncated_tables) | set(continuity_facts.truncated_tables))
    if truncated:
        return {
            "schema_version": NATURAL_PROBLEM_COHORT_SCHEMA_VERSION,
            "status": "FACT_WINDOW_TRUNCATED",
            "raw_rows": [],
            "truncated_tables": truncated,
            "policy": {
                "no_partial_cohort_projection": True,
                "read_only_immutable_snapshot_required": True,
                "unknown_is_not_zero": True,
            },
        }
    if problems.schema_version != PROBLEM_SCHEMA_VERSION:
        return {
            "schema_version": NATURAL_PROBLEM_COHORT_SCHEMA_VERSION,
            "status": "PRL_SCHEMA_INACTIVE",
            "observed_problem_schema_version": problems.schema_version,
            "raw_rows": [],
            "policy": {"no_writer_or_schema_activation": True, "unknown_is_not_zero": True},
        }

    ordered = sorted(
        problems.revisions,
        key=lambda row: (
            int(row.get("created_event_seq") or 0),
            _text(row.get("problem_id")),
            int(row.get("revision") or 0),
        ),
    )
    start_index = next(
        (
            index
            for index, row in enumerate(ordered)
            if _text(row.get("problem_id")) == start_id
            and int(row.get("revision") or 0) == start_problem_revision
        ),
        None,
    )
    if start_index is None:
        return {
            "schema_version": NATURAL_PROBLEM_COHORT_SCHEMA_VERSION,
            "status": "COHORT_START_NOT_FOUND",
            "cohort_start": {
                "problem_id": start_id,
                "problem_revision": start_problem_revision,
            },
            "raw_rows": [],
            "policy": {"no_nearest_match_or_fallback": True, "unknown_is_not_zero": True},
        }

    economics = problem_resolution_economics_report(ledger, problems)
    journeys = _journey_by_identity(economics)
    selected = ordered[start_index : start_index + target_n]
    rows = [
        _raw_row(
            ledger,
            problems,
            continuity_facts,
            journeys.get((_text(row.get("problem_id")), int(row.get("revision") or 0))),
            row,
        )
        for row in selected
    ]
    checkpoint_5 = _checkpoint(rows, 5)
    checkpoint_10 = _checkpoint(rows, 10)
    natural_rows = sum(
        int((row.get("natural_problem_eligibility") or {}).get("eligible") is True)
        for row in rows
    )
    manual_safe = (
        checkpoint_5["decision"] == "DESCRIPTIVE_REVIEW_REQUIRED"
        and checkpoint_5["real_cross_session_pass_rows"] == 5
        and checkpoint_5["false_closure_count"] == 0
        and checkpoint_5["reopen_count"] == 0
    )
    if len(rows) < 5:
        status = "COLLECTING"
    elif natural_rows < len(rows):
        status = "COHORT_PROVENANCE_INCOMPLETE"
    elif checkpoint_5["real_cross_session_pass_rows"] < 5:
        status = "DESCRIPTIVE_COHORT_CONTINUITY_INCOMPLETE"
    else:
        status = "DESCRIPTIVE_COHORT_READY"
    return {
        "schema_version": NATURAL_PROBLEM_COHORT_SCHEMA_VERSION,
        "status": status,
        "analysis_unit": "problem_revision",
        "cohort": {
            "start_identity": {
                "problem_id": start_id,
                "problem_revision": start_problem_revision,
                "created_event_seq": int(ordered[start_index].get("created_event_seq") or 0),
            },
            "target_n": target_n,
            "selected_rows": len(rows),
            "typed_natural_rows": natural_rows,
            "selection": "fixed_exact_start_then_next_problem_revisions_in_created_event_seq_order",
            "success_terminal_or_session_boundary_filter_used": False,
            "rows_skipped_after_start": 0,
            "pre_registration_receipt": None,
            "pre_registration_missing_preserves_descriptive_only_status": True,
        },
        "raw_rows": rows,
        "missingness": _missingness(rows),
        "decision_checkpoints": {"n5": checkpoint_5, "n10": checkpoint_10},
        "tg10_manual_continuity_safety_gate": {
            "status": "PASS" if manual_safe else "HOLD",
            "manual_continuity_proven_safe": manual_safe,
            "minimum_real_cross_session_pass_rows": 5,
            "state_loss_proxy": "exact_TG6_reconstruction_and_same_revision_correlation",
            "duplicate_execution_proxy": "TG6_managed_execution_reobserved_without_duplicate_start",
            "advisory_study_may_be_prepared": manual_safe,
            "study_arm_assignment_authorized": False,
            "automatic_hard_rotation_authorized": False,
            "missing_reason": None if manual_safe else "five_safe_real_cross_session_rows_not_proven",
        },
        "query_evidence": {
            "ledger_fact_load_statements": ledger.fact_load_statements,
            "problem_fact_load_statements": problems.fact_load_statements,
            "cross_session_fact_load_statements": continuity_facts.fact_load_statements,
            "all_nested_reads_from_immutable_memory": True,
            "sqlite_queries_per_problem_revision": 0,
        },
        "policy": {
            "read_only_immutable_snapshot_required": True,
            "no_writer_problem_run_wave_epoch_or_schema_activation": True,
            "typed_natural_provenance_required": True,
            "objective_text_inference_forbidden": True,
            "consecutive_rows_cannot_be_cherry_picked": True,
            "raw_rows_and_missingness_retained": True,
            "missing_is_unknown_not_zero": True,
            "descriptive_cohort_is_not_causal_evidence": True,
            "automatic_policy_promotion": False,
            "automatic_rotation_authority": False,
            "public_mcp_tool_added": False,
        },
    }
