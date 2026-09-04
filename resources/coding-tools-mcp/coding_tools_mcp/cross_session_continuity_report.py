"""Fail-closed TG6 proof oracle over one immutable ledger snapshot.

The report is deliberately unable to manufacture the manual Session A -> B
journey that it evaluates.  Product-session, UI, NO_ADVANCE and re-observation
claims require explicit content-free observation receipts; endpoint generation,
timestamps, unchanged counters and source presence are never substitutes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from .ledger_analysis import LedgerFacts, LedgerReadSession
from .problem_lineage import PROBLEM_SCHEMA_VERSION, problem_outcome_receipt_id
from .problem_resolution_economics import (
    ProblemLineageFacts,
    problem_resolution_economics_report,
)
from .resolution_contract import (
    ResolutionContractError,
    contract_sha256,
    normalize_resolution_envelope,
)


CROSS_SESSION_CONTINUITY_REPORT_SCHEMA_VERSION = 1
CROSS_SESSION_MAX_RECOVERY_REVISIONS = 32

_FACT_LIMITS = {
    "runs": 5_000,
    "waves": 10_000,
    "delegations": 20_000,
    "events": 50_000,
    "proofs": 50_000,
    "checkpoints": 20_000,
    "handoff_capsules": 20_000,
    "managed_process_jobs": 20_000,
    "background_operations": 20_000,
    "agent_lanes": 20_000,
    "hub_clients": 5_000,
    "controller_knowledge_checkpoints": 20_000,
    "controller_knowledge_acks": 20_000,
    "controller_reattach_receipts": 20_000,
}

_TABLE_ORDER = {
    "runs": "run_id",
    "waves": "run_id,ordinal,wave_id",
    "delegations": "wave_id,started_at,delegation_id",
    "events": "seq",
    "proofs": "run_id,wave_id,finished_at,proof_id",
    "checkpoints": "run_id,created_at,checkpoint_id",
    "handoff_capsules": "run_id,conversation_epoch,created_at,capsule_id",
    "managed_process_jobs": "run_id,wave_id,started_at,job_id",
    "background_operations": "run_id,wave_id,started_at,operation_id",
    "agent_lanes": "run_id,wave_id,created_at,lane_id",
    "hub_clients": "connected_at,client_id",
    "controller_knowledge_checkpoints": (
        "problem_id,problem_revision,knowledge_revision,checkpoint_id"
    ),
    "controller_knowledge_acks": "problem_id,problem_revision,created_at,ack_id",
    "controller_reattach_receipts": (
        "problem_id,problem_revision,generation,reattach_id"
    ),
}

_MATERIAL_KNOWLEDGE_EVENTS = frozenset(
    {
        "PROBLEM_OPENED",
        "PROBLEM_REVISED",
        "PROBLEM_REOPENED",
        "PROBLEM_BLOCKED",
        "PROBLEM_PROVISIONAL_RESOLVED",
        "PROBLEM_RESOLVED_CONFIRMED",
        "PROBLEM_ABANDONED",
        "CONTRACT_CHANGED",
        "CRITERION_COVERAGE_CHANGED",
        "AUTHORITY_CHANGED",
        "NEXT_CRITICAL_ACTION_CHANGED",
        "CONTINUITY_CAPSULE_REFRESHED",
    }
)

_OBSERVATION_RECEIPTS = {
    "session": "cross_session_chatweb_session_started",
    "rotation": "cross_session_chatweb_session_rotated",
    "no_advance": "controller_knowledge_no_advance_observed",
    "control_center": "execution_control_center_progress_observed",
    "continuity_core": "continuity_core_recorded",
    "reobserved": "managed_execution_reobserved",
    "reconstruction": "goal_reconstruction_observed",
    "criterion_completed": "remaining_criterion_completed",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    try:
        decoded = json.loads(str(value or "{}"))
    except (TypeError, json.JSONDecodeError):
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    try:
        decoded = json.loads(str(value or "[]"))
    except (TypeError, json.JSONDecodeError):
        return []
    return decoded if isinstance(decoded, list) else []


def _positive_revision(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("problem_revision must be a positive integer")
    return value


def _digest(value: Any) -> bool:
    text = _text(value).lower()
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def _revision_capsule(row: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    capsule = _json_object(row.get("typed_contract_capsule"))
    encoded = json.dumps(
        capsule,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    valid = bool(capsule) and hashlib.sha256(encoded).hexdigest() == _text(
        row.get("contract_fingerprint")
    )
    return capsule, valid


def _value_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _problem_key(problem_id: str, revision: int) -> str:
    return f"{problem_id}:revision:{revision}"


def _gate(
    gate_id: str,
    requirement: str,
    status: str,
    *,
    evidence_source: str,
    exact_receipt_ids: list[str] | tuple[str, ...] = (),
    missing_reason: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if status not in {"PASS", "INCOMPLETE", "UNAVAILABLE", "FACT_WINDOW_TRUNCATED"}:
        raise ValueError(f"invalid TG6 gate status: {status}")
    return {
        "gate_id": gate_id,
        "requirement": requirement,
        "status": status,
        "evidence_source": evidence_source,
        "exact_receipt_ids": sorted({_text(item) for item in exact_receipt_ids if _text(item)}),
        "missing_reason": None if status == "PASS" else (missing_reason or "required_receipt_missing"),
        "details": dict(details or {}),
    }


@dataclass(frozen=True)
class CrossSessionContinuityFacts:
    """Bounded opt-in facts loaded through the active immutable reader."""

    fact_rows: dict[str, tuple[dict[str, Any], ...]]
    available_tables: frozenset[str]
    truncated_tables: frozenset[str]
    fact_load_statements: int

    @classmethod
    def load(cls, reader: LedgerReadSession) -> "CrossSessionContinuityFacts":
        if not isinstance(reader, LedgerReadSession) or reader.connection is None:
            raise TypeError("cross-session facts require an active immutable LedgerReadSession")
        statement_start = reader.statement_count
        table_names = tuple(_TABLE_ORDER)
        placeholders = ",".join("?" for _ in table_names)
        available_rows = reader.rows(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name IN ({placeholders}) ORDER BY name",
            table_names,
        )
        available = {str(row["name"]) for row in available_rows}
        truncated: set[str] = set()
        facts: dict[str, tuple[dict[str, Any], ...]] = {}
        for table, order_by in _TABLE_ORDER.items():
            if table not in available:
                facts[table] = ()
                continue
            limit = _FACT_LIMITS[table]
            rows = reader.rows(
                f"SELECT * FROM {table} ORDER BY {order_by} LIMIT ?",
                (limit + 1,),
            )
            if len(rows) > limit:
                truncated.add(table)
            facts[table] = tuple(dict(row) for row in rows[:limit])
        return cls(
            fact_rows=facts,
            available_tables=frozenset(available),
            truncated_tables=frozenset(truncated),
            fact_load_statements=reader.statement_count - statement_start,
        )

    def rows(self, table: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self.fact_rows.get(table, ())]


def _binding(row: dict[str, Any]) -> dict[str, Any] | None:
    metadata = _json_object(row.get("metadata_json"))
    context = metadata.get("problem_resolution")
    if not isinstance(context, dict) or _text(context.get("work_origin")) != "problem":
        return None
    revision = context.get("problem_revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        return None
    workspace = metadata.get("workspace_identity")
    return {
        "problem_id": _text(context.get("problem_id")),
        "problem_revision": revision,
        "workspace_id": _text(workspace.get("workspace_id")) if isinstance(workspace, dict) else "",
    }


def _event(row: dict[str, Any]) -> dict[str, Any]:
    return {**row, "payload": _json_object(row.get("payload_json"))}


def _matches_problem(payload: dict[str, Any], problem_id: str, revision: int) -> bool:
    return (
        _text(payload.get("problem_id")) == problem_id
        and payload.get("problem_revision") == revision
    )


def _receipt_events(
    events: list[dict[str, Any]],
    event_type: str,
    problem_id: str,
    revision: int,
) -> list[dict[str, Any]]:
    return [
        row
        for row in events
        if _text(row.get("event_type")) == event_type
        and _matches_problem(row.get("payload") or {}, problem_id, revision)
    ]


def _status_from_missing(table: str, facts: CrossSessionContinuityFacts) -> str:
    return "UNAVAILABLE" if table not in facts.available_tables else "INCOMPLETE"


def _exact_primary_run_ids(events: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            _text(event.get("run_id"))
            for event in events
            if _text(event.get("link_status")) == "EXACT"
            and _text(event.get("link_role")) == "PRIMARY"
            and _text(event.get("relation_type")) in {"LINK", "ENGINEERING_ATTEMPT_BOUND"}
            and _text(event.get("run_id"))
        }
    )


def _problem_outcome_receipt_bound(event: dict[str, Any]) -> bool:
    if _text(event.get("relation_type")) != "CONFIRMED_RESOLUTION":
        return False
    expected = problem_outcome_receipt_id(
        receipt_type=_text(event.get("outcome_receipt_type")),
        event_id=_text(event.get("event_id")),
        problem_id=_text(event.get("problem_id")),
        problem_revision=int(event.get("problem_revision") or 0),
        turn_id=_text(event.get("turn_id")),
        trace_id=_text(event.get("trace_id")),
    )
    return _text(event.get("outcome_receipt_id")) == expected


def _inactive_report(
    problem_id: str,
    revision: int,
    problems: ProblemLineageFacts,
    facts: CrossSessionContinuityFacts,
) -> dict[str, Any]:
    requirements = (
        "exact Problem Revision has at least five criteria",
        "ChatWeb Session A starts exact Goal pursuit",
        "failed WAVE enters evidence-driven REPLAN",
        "material controller-knowledge checkpoint exists",
        "NO_ADVANCE reads are explicitly observed without revision inflation",
        "durable command or delegated execution exists",
        "progress is observed in Execution Control Center",
        "Continuity Core is durably recorded",
        "Session A is intentionally rotated",
        "Session B binds the same workspace and Problem Revision",
        "Session B presents a current or bounded-behind ACK",
        "bounded controller-knowledge recovery reaches current state",
        "Session B legally reattaches the controller role",
        "execution is re-observed without duplicate start",
        "exact criteria, gap, proofs and next action are reconstructed",
        "the remaining criterion is completed and proved",
        "closure falsifier passes",
        "independent outcome confirms or same-revision reopen occurs",
        "all receipts and economics stay on one exact Problem Revision",
    )
    reason = (
        "problem_lineage_schema_inactive"
        if problems.schema_version != PROBLEM_SCHEMA_VERSION
        else "exact_problem_revision_not_found"
    )
    gates = [
        _gate(
            f"TG6-{index:02d}",
            requirement,
            "UNAVAILABLE" if index > 1 else "INCOMPLETE",
            evidence_source="immutable_problem_lineage_snapshot",
            missing_reason=reason,
        )
        for index, requirement in enumerate(requirements, start=1)
    ]
    return {
        "schema_version": CROSS_SESSION_CONTINUITY_REPORT_SCHEMA_VERSION,
        "status": "INCOMPLETE",
        "accepted_real_cross_session_continuity_receipt": False,
        "no_partial_cross_session_claim": True,
        "problem_identity": {"problem_id": problem_id, "problem_revision": revision},
        "gates": gates,
        "gate_counts": {"PASS": 0, "INCOMPLETE": 1, "UNAVAILABLE": 18, "FACT_WINDOW_TRUNCATED": 0},
        "economics": {"status": "UNAVAILABLE", "missing_reason": reason, "unknown_is_not_zero": True},
        "fact_window": {
            "status": "BOUNDED",
            "fact_limits": dict(_FACT_LIMITS),
            "truncated_tables": sorted(set(problems.truncated_tables) | set(facts.truncated_tables)),
        },
        "policy": _policy(),
    }


def _policy() -> dict[str, Any]:
    return {
        "read_only_immutable_snapshot_required": True,
        "no_writer_or_schema_activation": True,
        "exact_problem_revision_required": True,
        "hard_fact_windows": True,
        "timestamp_proximity_attribution_forbidden": True,
        "endpoint_generation_is_not_product_session_identity": True,
        "unchanged_revision_is_not_no_advance_proof": True,
        "process_presence_is_not_durable_job_identity": True,
        "source_presence_is_not_control_center_visibility": True,
        "technical_proof_is_not_independent_outcome": True,
        "unknown_is_not_zero": True,
        "automatic_rotation_authority": False,
        "public_mcp_tool_added": False,
    }


def cross_session_continuity_report(
    ledger: LedgerFacts,
    problems: ProblemLineageFacts,
    facts: CrossSessionContinuityFacts,
    *,
    problem_id: str,
    problem_revision: int,
) -> dict[str, Any]:
    """Evaluate the TG6 journey without opening SQLite or creating workload."""

    if not isinstance(ledger, LedgerFacts):
        raise TypeError("cross-session report requires immutable LedgerFacts")
    if not isinstance(problems, ProblemLineageFacts):
        raise TypeError("cross-session report requires immutable ProblemLineageFacts")
    if not isinstance(facts, CrossSessionContinuityFacts):
        raise TypeError("cross-session report requires bounded CrossSessionContinuityFacts")
    problem = _text(problem_id)
    if not problem or len(problem) > 128:
        raise ValueError("problem_id is required and must be at most 128 characters")
    revision_number = _positive_revision(problem_revision)
    revision_rows = [
        row
        for row in problems.revisions_for_problem(problem)
        if int(row.get("revision") or 0) == revision_number
    ]
    if problems.schema_version != PROBLEM_SCHEMA_VERSION or len(revision_rows) != 1:
        return _inactive_report(problem, revision_number, problems, facts)

    truncated = sorted(set(problems.truncated_tables) | set(facts.truncated_tables))
    if truncated:
        base = _inactive_report(problem, revision_number, problems, facts)
        base["status"] = "FACT_WINDOW_TRUNCATED"
        base["gates"] = [
            _gate(
                row["gate_id"],
                row["requirement"],
                "FACT_WINDOW_TRUNCATED",
                evidence_source="bounded_immutable_snapshot",
                missing_reason="core_fact_window_truncated",
                details={"truncated_tables": truncated},
            )
            for row in base["gates"]
        ]
        base["gate_counts"] = {
            "PASS": 0,
            "INCOMPLETE": 0,
            "UNAVAILABLE": 0,
            "FACT_WINDOW_TRUNCATED": 19,
        }
        base["fact_window"] = {
            "status": "FACT_WINDOW_TRUNCATED",
            "fact_limits": dict(_FACT_LIMITS),
            "truncated_tables": truncated,
        }
        return base

    revision_row = revision_rows[0]
    problem_events = problems.events_for_revision(problem, revision_number)
    run_ids = _exact_primary_run_ids(problem_events)
    run_set = set(run_ids)
    run_rows = [row for row in facts.rows("runs") if _text(row.get("run_id")) in run_set]
    run_bindings = {_text(row.get("run_id")): _binding(row) for row in run_rows}
    binding_mismatches = sorted(
        run_id
        for run_id in run_ids
        if run_bindings.get(run_id) is None
        or run_bindings[run_id].get("problem_id") != problem
        or run_bindings[run_id].get("problem_revision") != revision_number
    )
    workspace_ids = {
        _text(binding.get("workspace_id"))
        for binding in run_bindings.values()
        if isinstance(binding, dict) and _text(binding.get("workspace_id"))
    }
    exact_workspace = next(iter(workspace_ids)) if len(workspace_ids) == 1 else ""
    wave_rows = [row for row in facts.rows("waves") if _text(row.get("run_id")) in run_set]
    wave_ids = {_text(row.get("wave_id")) for row in wave_rows}
    ledger_events = [
        _event(row) for row in facts.rows("events") if _text(row.get("run_id")) in run_set
    ]
    ledger_events.sort(key=lambda row: int(row.get("seq") or 0))
    proofs = [row for row in facts.rows("proofs") if _text(row.get("run_id")) in run_set]
    proof_by_id = {_text(row.get("proof_id")): row for row in proofs}
    accepted_checkpoints = [
        row
        for row in facts.rows("checkpoints")
        if _text(row.get("run_id")) in run_set and _text(row.get("status")) == "accepted"
    ]

    revision_capsule, revision_capsule_valid = _revision_capsule(revision_row)
    criteria = list(revision_capsule.get("acceptance_criteria") or [])
    criterion_ids = {
        _text(item.get("criterion_id")) for item in criteria if isinstance(item, dict) and _text(item.get("criterion_id"))
    }
    gates: list[dict[str, Any]] = []
    criteria_ok = (
        revision_capsule_valid
        and int(revision_row.get("criteria_count") or 0) >= 5
        and len(criterion_ids) == int(revision_row.get("criteria_count") or 0)
    )
    gates.append(
        _gate(
            "TG6-01",
            "exact Problem Revision has at least five criteria",
            "PASS" if criteria_ok else "INCOMPLETE",
            evidence_source="problem_revisions.typed_contract_capsule",
            exact_receipt_ids=[_problem_key(problem, revision_number)],
            missing_reason="fewer_than_five_valid_exact_revision_criteria",
            details={"criteria_count": int(revision_row.get("criteria_count") or 0)},
        )
    )

    session_events = _receipt_events(
        ledger_events, _OBSERVATION_RECEIPTS["session"], problem, revision_number
    )
    session_a = next(
        (
            row
            for row in session_events
            if _text((row.get("payload") or {}).get("session_role")).upper() == "A"
            and _text((row.get("payload") or {}).get("receipt_type"))
            == "CHATWEB_PRODUCT_SESSION_GOAL_PURSUIT_V1"
            and _text((row.get("payload") or {}).get("workspace_id")) == exact_workspace
            and _text((row.get("payload") or {}).get("product_session_receipt_id"))
        ),
        None,
    )
    gates.append(
        _gate(
            "TG6-02",
            "ChatWeb Session A starts exact Goal pursuit",
            "PASS" if session_a else "UNAVAILABLE",
            evidence_source=_OBSERVATION_RECEIPTS["session"],
            exact_receipt_ids=[
                _text(session_a.get("event_id")) if session_a else "",
                _text((session_a or {}).get("payload", {}).get("product_session_receipt_id")),
            ],
            missing_reason="typed_chatweb_product_session_a_receipt_unobserved",
        )
    )

    failures = [row for row in ledger_events if _text(row.get("event_type")) == "failure_observed"]
    available_replans = [
        row for row in ledger_events if _text(row.get("event_type")) == "wave_replanned"
    ]
    failure_replans: list[tuple[dict[str, Any], dict[str, Any]]] = []
    unmatched_failures: list[dict[str, Any]] = []
    for failure in failures:
        failure_class = _text((failure.get("payload") or {}).get("failure_class"))
        match_index = next(
            (
                index
                for index, replan in enumerate(available_replans)
                if failure_class
                and _text(replan.get("run_id")) == _text(failure.get("run_id"))
                and int(failure.get("seq") or 0) < int(replan.get("seq") or 0)
                and _text((replan.get("payload") or {}).get("reason")) == failure_class
            ),
            None,
        )
        if match_index is None:
            unmatched_failures.append(failure)
            continue
        failure_replans.append((failure, available_replans.pop(match_index)))
    exact_runs_ready = bool(run_ids) and not binding_mismatches and len(run_rows) == len(run_ids)
    clean_first_pass = exact_runs_ready and not failures
    failure_policy_passed = exact_runs_ready and (clean_first_pass or not unmatched_failures)
    failure_receipt_ids = [
        _text(event.get("event_id"))
        for pair in failure_replans
        for event in pair
    ]
    gates.append(
        _gate(
            "TG6-03",
            "every failed WAVE enters evidence-driven REPLAN, or exact run is clean first-pass",
            "PASS" if failure_policy_passed else "INCOMPLETE",
            evidence_source="exact_primary_problem_links+events.failure_observed+events.wave_replanned",
            exact_receipt_ids=failure_receipt_ids if failures else run_ids,
            missing_reason=(
                "exact_problem_linked_run_missing"
                if not exact_runs_ready
                else "failure_to_typed_replan_causal_pair_missing"
            ),
            details={
                "applicable": bool(failures) if exact_runs_ready else None,
                "clean_first_pass": clean_first_pass,
                "failure_count": len(failures),
                "matched_replan_count": len(failure_replans),
                "unmatched_failure_event_ids": [
                    _text(row.get("event_id")) for row in unmatched_failures
                ],
            },
        )
    )

    checkpoints = [
        row
        for row in facts.rows("controller_knowledge_checkpoints")
        if _text(row.get("problem_id")) == problem
        and int(row.get("problem_revision") or 0) == revision_number
        and _text(row.get("material_event_kind")) in _MATERIAL_KNOWLEDGE_EVENTS
        and (not exact_workspace or _text(row.get("workspace_id")) == exact_workspace)
    ]
    current_checkpoint = max(
        checkpoints, key=lambda row: int(row.get("knowledge_revision") or 0), default=None
    )
    gates.append(
        _gate(
            "TG6-04",
            "material controller-knowledge checkpoint exists",
            "PASS" if current_checkpoint else _status_from_missing("controller_knowledge_checkpoints", facts),
            evidence_source="controller_knowledge_checkpoints",
            exact_receipt_ids=[_text((current_checkpoint or {}).get("checkpoint_id"))],
            missing_reason="material_exact_revision_knowledge_checkpoint_missing",
        )
    )

    no_advance_events = _receipt_events(
        ledger_events, _OBSERVATION_RECEIPTS["no_advance"], problem, revision_number
    )
    no_advance = next(
        (
            row
            for row in no_advance_events
            if _text((row.get("payload") or {}).get("policy")) == "NO_ADVANCE"
            and int((row.get("payload") or {}).get("operation_count") or 0) >= 2
            and (row.get("payload") or {}).get("knowledge_revision_before")
            == (row.get("payload") or {}).get("knowledge_revision_after")
            and len((row.get("payload") or {}).get("operation_receipt_ids") or [])
            >= int((row.get("payload") or {}).get("operation_count") or 0)
        ),
        None,
    )
    gates.append(
        _gate(
            "TG6-05",
            "NO_ADVANCE reads are explicitly observed without revision inflation",
            "PASS" if no_advance else "UNAVAILABLE",
            evidence_source=_OBSERVATION_RECEIPTS["no_advance"],
            exact_receipt_ids=[_text((no_advance or {}).get("event_id"))],
            missing_reason="exact_no_advance_operation_observation_receipt_unobserved",
        )
    )

    jobs = [
        row
        for row in facts.rows("managed_process_jobs")
        if _text(row.get("run_id")) in run_set
        and _text(row.get("wave_id")) in wave_ids
        and _text(row.get("job_id"))
        and _text(row.get("command_id"))
    ]
    delegations = [
        row
        for row in facts.rows("delegations")
        if _text(row.get("wave_id")) in wave_ids and _text(row.get("delegation_id"))
    ]
    durable_ids = [_text(row.get("job_id")) for row in jobs] + [
        _text(row.get("delegation_id")) for row in delegations
    ]
    gates.append(
        _gate(
            "TG6-06",
            "durable command or delegated execution exists",
            "PASS" if durable_ids else "INCOMPLETE",
            evidence_source="managed_process_jobs|delegations",
            exact_receipt_ids=durable_ids,
            missing_reason="exact_run_durable_execution_identity_missing",
        )
    )

    control_events = _receipt_events(
        ledger_events, _OBSERVATION_RECEIPTS["control_center"], problem, revision_number
    )
    control_observation = next(
        (
            row
            for row in control_events
            if bool((row.get("payload") or {}).get("progress_visible"))
            and _text((row.get("payload") or {}).get("observer_plane"))
            == "execution_control_center"
            and _digest((row.get("payload") or {}).get("snapshot_fingerprint"))
        ),
        None,
    )
    gates.append(
        _gate(
            "TG6-07",
            "progress is observed in Execution Control Center",
            "PASS" if control_observation else "UNAVAILABLE",
            evidence_source=_OBSERVATION_RECEIPTS["control_center"],
            exact_receipt_ids=[_text((control_observation or {}).get("event_id"))],
            missing_reason="execution_control_center_observation_receipt_unobserved",
        )
    )

    core_events = _receipt_events(
        ledger_events, _OBSERVATION_RECEIPTS["continuity_core"], problem, revision_number
    )
    core_event = next(
        (
            row
            for row in core_events
            if _digest((row.get("payload") or {}).get("continuity_core_fingerprint"))
            and _text((row.get("payload") or {}).get("workspace_id")) == exact_workspace
        ),
        None,
    )
    gates.append(
        _gate(
            "TG6-08",
            "Continuity Core is durably recorded",
            "PASS" if core_event else "UNAVAILABLE",
            evidence_source=_OBSERVATION_RECEIPTS["continuity_core"],
            exact_receipt_ids=[_text((core_event or {}).get("event_id"))],
            missing_reason="exact_continuity_core_recording_receipt_unobserved",
        )
    )

    rotation_events = _receipt_events(
        ledger_events, _OBSERVATION_RECEIPTS["rotation"], problem, revision_number
    )
    rotation = next(
        (
            row
            for row in rotation_events
            if core_event
            and int(row.get("seq") or 0) > int(core_event.get("seq") or 0)
            and _text((row.get("payload") or {}).get("receipt_type"))
            == "CHATWEB_PRODUCT_SESSION_ROTATION_V1"
            and _text((row.get("payload") or {}).get("outgoing_product_session_receipt_id"))
            == _text((session_a or {}).get("payload", {}).get("product_session_receipt_id"))
        ),
        None,
    )
    gates.append(
        _gate(
            "TG6-09",
            "Session A is intentionally rotated",
            "PASS" if rotation else "UNAVAILABLE",
            evidence_source=_OBSERVATION_RECEIPTS["rotation"],
            exact_receipt_ids=[_text((rotation or {}).get("event_id"))],
            missing_reason="typed_intentional_chatweb_rotation_receipt_unobserved",
        )
    )

    session_b = next(
        (
            row
            for row in session_events
            if rotation
            and int(row.get("seq") or 0) > int(rotation.get("seq") or 0)
            and _text((row.get("payload") or {}).get("session_role")).upper() == "B"
            and _text((row.get("payload") or {}).get("receipt_type"))
            == "CHATWEB_PRODUCT_SESSION_GOAL_PURSUIT_V1"
            and _text((row.get("payload") or {}).get("workspace_id")) == exact_workspace
            and _text((row.get("payload") or {}).get("product_session_receipt_id"))
            and _text((row.get("payload") or {}).get("product_session_receipt_id"))
            != _text((session_a or {}).get("payload", {}).get("product_session_receipt_id"))
        ),
        None,
    )
    gates.append(
        _gate(
            "TG6-10",
            "Session B binds the same workspace and Problem Revision",
            "PASS" if session_b else "UNAVAILABLE",
            evidence_source=_OBSERVATION_RECEIPTS["session"],
            exact_receipt_ids=[
                _text((session_b or {}).get("event_id")),
                _text((session_b or {}).get("payload", {}).get("product_session_receipt_id")),
            ],
            missing_reason="typed_same_goal_chatweb_session_b_receipt_unobserved",
        )
    )

    acks = [
        {**row, "recovery": _json_object(row.get("recovery_json"))}
        for row in facts.rows("controller_knowledge_acks")
        if _text(row.get("problem_id")) == problem
        and int(row.get("problem_revision") or 0) == revision_number
        and (not exact_workspace or _text(row.get("workspace_id")) == exact_workspace)
        and _text(row.get("status")) in {"CURRENT", "BEHIND"}
    ]
    session_b_endpoint = _text((session_b or {}).get("payload", {}).get("controller_endpoint_id"))
    safe_acks = [
        row
        for row in acks
        if not session_b_endpoint or _text(row.get("controller_endpoint_id")) == session_b_endpoint
    ]
    ack = safe_acks[-1] if safe_acks else None
    gates.append(
        _gate(
            "TG6-11",
            "Session B presents a current or bounded-behind ACK",
            "PASS" if ack else _status_from_missing("controller_knowledge_acks", facts),
            evidence_source="controller_knowledge_acks",
            exact_receipt_ids=[_text((ack or {}).get("ack_id"))],
            missing_reason="safe_exact_session_b_ack_missing",
            details={"ack_status": _text((ack or {}).get("status")) or None},
        )
    )

    recovery_ok = False
    recovery_ids: list[str] = []
    if ack is not None and current_checkpoint is not None:
        current_revision = int(current_checkpoint.get("knowledge_revision") or 0)
        supplied = ack.get("knowledge_revision")
        if _text(ack.get("status")) == "CURRENT":
            recovery_ok = supplied == current_revision == int(ack.get("current_knowledge_revision") or 0)
        else:
            recovery = ack.get("recovery") or {}
            delta = recovery.get("delta") if isinstance(recovery.get("delta"), list) else []
            delta_revisions = [
                int(item.get("knowledge_revision") or 0) for item in delta if isinstance(item, dict)
            ]
            recovery_ok = (
                isinstance(supplied, int)
                and 0 < len(delta_revisions) <= CROSS_SESSION_MAX_RECOVERY_REVISIONS
                and bool(recovery.get("delta_complete"))
                and not bool(recovery.get("history_lost"))
                and delta_revisions == list(range(supplied + 1, current_revision + 1))
                and int(ack.get("current_knowledge_revision") or 0) == current_revision
            )
            recovery_ids = [
                _text(item.get("checkpoint_id")) for item in delta if isinstance(item, dict)
            ]
    gates.append(
        _gate(
            "TG6-12",
            "bounded controller-knowledge recovery reaches current state",
            "PASS" if recovery_ok else ("UNAVAILABLE" if ack is None else "INCOMPLETE"),
            evidence_source="controller_knowledge_acks.recovery_json",
            exact_receipt_ids=[_text((ack or {}).get("ack_id")), *recovery_ids],
            missing_reason="ack_recovery_not_exact_complete_and_bounded",
        )
    )

    clients = {_text(row.get("client_id")): row for row in facts.rows("hub_clients")}
    reattach_rows = [
        {**row, "active_run_transfers": _json_list(row.get("active_run_transfers_json"))}
        for row in facts.rows("controller_reattach_receipts")
        if _text(row.get("problem_id")) == problem
        and int(row.get("problem_revision") or 0) == revision_number
        and (not exact_workspace or _text(row.get("workspace_id")) == exact_workspace)
    ]
    legal_reattach = None
    for row in reattach_rows:
        client = clients.get(_text(row.get("owner_client_id")))
        owner_client_id = _text(row.get("owner_client_id"))
        client_identity_valid = bool(
            client
            and _text(client.get("client_id")) == owner_client_id
            and _text(client.get("client_type")) == "chatweb"
            and _text(client.get("role")) == "controller"
        )
        receipt_request_valid = _text(row.get("request_hash")) == _value_sha256(
            {
                "reattach_id": _text(row.get("reattach_id")),
                "workspace_id": _text(row.get("workspace_id")),
                "problem_id": _text(row.get("problem_id")),
                "problem_revision": int(row.get("problem_revision") or 0),
                "controller_endpoint_id": _text(row.get("controller_endpoint_id")),
                "owner_client_id": owner_client_id,
                "ack_id": _text(row.get("ack_id")),
                "ack_status": _text(row.get("ack_status")),
                "continuity_core_fingerprint": _text(row.get("continuity_core_fingerprint")),
                "source_fingerprint": _text(row.get("source_fingerprint")),
                "runtime_behavior_fingerprint": _text(row.get("runtime_behavior_fingerprint")),
            }
        )
        transfers = row.get("active_run_transfers") or []
        if (
            ack is not None
            and _text(row.get("ack_id")) == _text(ack.get("ack_id"))
            and _text(row.get("ack_status")) == _text(ack.get("status"))
            and int(row.get("generation") or 0) == int(row.get("prior_generation") or 0) + 1
            and client_identity_valid
            and receipt_request_valid
            and _text(row.get("controller_endpoint_id")) == _text(ack.get("controller_endpoint_id"))
            and 0 <= len(transfers) <= 32
            and all(
                isinstance(item, dict)
                and _text(item.get("run_id")) in run_set
                and _text(item.get("owner_client_id")) == _text(row.get("owner_client_id"))
                and _text(item.get("status")) == "active"
                for item in transfers
            )
            and _digest(row.get("continuity_core_fingerprint"))
            and _digest(row.get("source_fingerprint"))
            and _digest(row.get("runtime_behavior_fingerprint"))
            and current_checkpoint is not None
            and _text(row.get("source_fingerprint"))
            == _text(current_checkpoint.get("source_fingerprint"))
            and _text(row.get("runtime_behavior_fingerprint"))
            == _text(current_checkpoint.get("runtime_behavior_fingerprint"))
            and (core_event is None or _text(row.get("continuity_core_fingerprint")) == _text((core_event.get("payload") or {}).get("continuity_core_fingerprint")))
        ):
            legal_reattach = row
            break
    gates.append(
        _gate(
            "TG6-13",
            "Session B legally reattaches the controller role",
            "PASS" if legal_reattach else _status_from_missing("controller_reattach_receipts", facts),
            evidence_source="controller_reattach_receipts+hub_clients+controller_knowledge_acks",
            exact_receipt_ids=[_text((legal_reattach or {}).get("reattach_id"))],
            missing_reason="legal_same_role_exact_revision_reattach_receipt_missing",
        )
    )

    reobservations = _receipt_events(
        ledger_events, _OBSERVATION_RECEIPTS["reobserved"], problem, revision_number
    )
    job_ids = {_text(row.get("job_id")) for row in jobs}
    command_by_job = {_text(row.get("job_id")): _text(row.get("command_id")) for row in jobs}
    reobserved = next(
        (
            row
            for row in reobservations
            if session_b
            and int(row.get("seq") or 0) > int(session_b.get("seq") or 0)
            and _text((row.get("payload") or {}).get("job_id")) in job_ids
            and _text((row.get("payload") or {}).get("command_id"))
            == command_by_job.get(_text((row.get("payload") or {}).get("job_id")))
            and (row.get("payload") or {}).get("duplicate_execution_started") is False
            and _text((row.get("payload") or {}).get("reattach_id"))
            == _text((legal_reattach or {}).get("reattach_id"))
        ),
        None,
    )
    gates.append(
        _gate(
            "TG6-14",
            "execution is re-observed without duplicate start",
            "PASS" if reobserved else "UNAVAILABLE",
            evidence_source=_OBSERVATION_RECEIPTS["reobserved"],
            exact_receipt_ids=[
                _text((reobserved or {}).get("event_id")),
                _text((reobserved or {}).get("payload", {}).get("job_id")),
            ],
            missing_reason="explicit_same_job_reobservation_without_duplicate_receipt_missing",
        )
    )

    reconstruction_events = _receipt_events(
        ledger_events, _OBSERVATION_RECEIPTS["reconstruction"], problem, revision_number
    )
    reconstruction = next(
        (
            row
            for row in reconstruction_events
            if session_b
            and int(row.get("seq") or 0) > int(session_b.get("seq") or 0)
            and set((row.get("payload") or {}).get("criterion_ids") or []) == criterion_ids
            and int((row.get("payload") or {}).get("criteria_total") or 0) == len(criterion_ids)
            and isinstance((row.get("payload") or {}).get("proof_ids"), list)
            and bool((row.get("payload") or {}).get("proof_ids"))
            and all(
                _text(proof_id) in proof_by_id
                and _text(proof_by_id[_text(proof_id)].get("status")) == "passed"
                for proof_id in (row.get("payload") or {}).get("proof_ids") or []
            )
            and _text((row.get("payload") or {}).get("next_gap_id")) in criterion_ids
            and _text((row.get("payload") or {}).get("next_action"))
            and (row.get("payload") or {}).get("transcript_replayed") is False
        ),
        None,
    )
    gates.append(
        _gate(
            "TG6-15",
            "exact criteria, gap, proofs and next action are reconstructed",
            "PASS" if reconstruction else "UNAVAILABLE",
            evidence_source=_OBSERVATION_RECEIPTS["reconstruction"],
            exact_receipt_ids=[_text((reconstruction or {}).get("event_id"))],
            missing_reason="exact_session_b_goal_reconstruction_receipt_missing",
        )
    )

    completion_events = _receipt_events(
        ledger_events, _OBSERVATION_RECEIPTS["criterion_completed"], problem, revision_number
    )
    completion = next(
        (
            row
            for row in completion_events
            if session_b
            and int(row.get("seq") or 0) > int(session_b.get("seq") or 0)
            and _text((row.get("payload") or {}).get("criterion_id")) in criterion_ids
            and _text((row.get("payload") or {}).get("proof_id")) in proof_by_id
            and _text(proof_by_id[_text((row.get("payload") or {}).get("proof_id"))].get("status")) == "passed"
        ),
        None,
    )
    gates.append(
        _gate(
            "TG6-16",
            "the remaining criterion is completed and proved",
            "PASS" if completion else "UNAVAILABLE",
            evidence_source=_OBSERVATION_RECEIPTS["criterion_completed"] + "+proofs",
            exact_receipt_ids=[
                _text((completion or {}).get("event_id")),
                _text((completion or {}).get("payload", {}).get("proof_id")),
            ],
            missing_reason="session_b_remaining_criterion_passed_proof_receipt_missing",
        )
    )

    falsifier_receipts: list[str] = []
    for row in wave_rows:
        metadata = _json_object(row.get("metadata_json"))
        context = metadata.get("problem_resolution") if isinstance(metadata.get("problem_resolution"), dict) else {}
        claim = context.get("outcome_claim") if isinstance(context.get("outcome_claim"), dict) else {}
        claim_sha = _text(context.get("outcome_claim_sha256"))
        envelope = claim.get("resolution_envelope") if isinstance(claim.get("resolution_envelope"), dict) else {}
        try:
            normalized_envelope = normalize_resolution_envelope(envelope)
        except ResolutionContractError:
            normalized_envelope = {}
        claim_valid = (
            _text(claim.get("problem_id")) == problem
            and claim.get("problem_revision") == revision_number
            and claim_sha == _value_sha256(claim)
            and _text(claim.get("resolution_envelope_sha256"))
            == contract_sha256(normalized_envelope)
            and normalized_envelope == envelope
        )
        probe = normalized_envelope.get("closure_falsification_probe") if isinstance(normalized_envelope.get("closure_falsification_probe"), dict) else {}
        checkpoint = next(
            (
                item
                for item in accepted_checkpoints
                if _text(item.get("run_id")) == _text(row.get("run_id"))
                and _text(item.get("wave_id")) == _text(row.get("wave_id"))
                and _json_object(item.get("metadata_json")).get("problem_outcome_claim") == claim
                and _text(_json_object(item.get("metadata_json")).get("problem_outcome_claim_sha256")) == claim_sha
            ),
            None,
        )
        if claim_valid and checkpoint and probe.get("executed") is True and _text(probe.get("result")).lower() == "passed":
            falsifier_receipts = [
                _text(checkpoint.get("checkpoint_id")),
                _text(probe.get("probe_id")),
            ]
            break
    gates.append(
        _gate(
            "TG6-17",
            "closure falsifier passes",
            "PASS" if falsifier_receipts else "INCOMPLETE",
            evidence_source="waves.problem_resolution.resolution_envelope+accepted_checkpoint",
            exact_receipt_ids=falsifier_receipts,
            missing_reason="accepted_exact_revision_closure_falsifier_receipt_missing",
        )
    )

    outcome = next(
        (event for event in problem_events if _problem_outcome_receipt_bound(event)), None
    )
    reopen = next(
        (
            event
            for event in problem_events
            if _text(event.get("relation_type")) == "REOPEN"
            and bool(event.get("eligible_for_policy"))
            and _text(event.get("transition_authority")) in {"RUNTIME_EXPLICIT_USER", "RUNTIME_OUTCOME_RECEIPT"}
        ),
        None,
    )
    gates.append(
        _gate(
            "TG6-18",
            "independent outcome confirms or same-revision reopen occurs",
            "PASS" if outcome or reopen else "INCOMPLETE",
            evidence_source="problem_events.outcome_receipt|problem_events.same_revision_reopen",
            exact_receipt_ids=[_text((outcome or reopen or {}).get("event_id"))],
            missing_reason="independent_outcome_or_truthful_same_revision_reopen_missing",
            details={"outcome": "confirmed" if outcome else ("reopened" if reopen else None)},
        )
    )

    economics_report = problem_resolution_economics_report(ledger, problems)
    journeys = list((economics_report.get("problem_revision_journeys") or {}).get("journeys") or [])
    journey = next(
        (
            item
            for item in journeys
            if _text(item.get("problem_id")) == problem
            and int(item.get("problem_revision") or 0) == revision_number
        ),
        None,
    )
    summary = (economics_report.get("problem_revision_journeys") or {}).get("summary") or {}
    chain = problems.verify_chain(problem)
    correlation_ok = (
        bool(run_ids)
        and not binding_mismatches
        and len(workspace_ids) == 1
        and len(run_rows) == len(run_ids)
        and bool(chain.get("ok"))
        and journey is not None
        and not set(summary.get("run_attribution_conflicts") or []) & run_set
        and not set(summary.get("run_metadata_attribution_mismatches") or []) & run_set
        and all(_text(row.get("run_id")) in run_set for row in ledger_events)
        and all(_text(row.get("run_id")) in run_set for row in jobs)
        and all(_text(row.get("run_id")) in run_set for row in accepted_checkpoints)
    )
    economics_receipt = "economics:" + hashlib.sha256(
        json.dumps(
            {"problem_id": problem, "problem_revision": revision_number, "journey": journey},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:40] if journey is not None else ""
    gates.append(
        _gate(
            "TG6-19",
            "all receipts and economics stay on one exact Problem Revision",
            "PASS" if correlation_ok else "INCOMPLETE",
            evidence_source="exact_primary_problem_links+immutable_problem_resolution_economics",
            exact_receipt_ids=[*run_ids, economics_receipt],
            missing_reason="exact_problem_revision_correlation_or_economics_journey_incomplete",
            details={
                "workspace_id": exact_workspace or None,
                "exact_primary_run_ids": run_ids,
                "binding_mismatches": binding_mismatches,
                "economics_unknowns_preserved": True,
            },
        )
    )

    counts = {status: sum(1 for gate in gates if gate["status"] == status) for status in ("PASS", "INCOMPLETE", "UNAVAILABLE", "FACT_WINDOW_TRUNCATED")}
    accepted = counts["PASS"] == len(gates)
    session_receipts = [
        _text((session_a or {}).get("payload", {}).get("product_session_receipt_id")),
        _text((session_b or {}).get("payload", {}).get("product_session_receipt_id")),
    ]
    return {
        "schema_version": CROSS_SESSION_CONTINUITY_REPORT_SCHEMA_VERSION,
        "status": "PASS" if accepted else "INCOMPLETE",
        "accepted_real_cross_session_continuity_receipt": accepted,
        "no_partial_cross_session_claim": not accepted,
        "problem_identity": {
            "problem_id": problem,
            "problem_revision": revision_number,
            "workspace_id": exact_workspace or None,
            "contract_fingerprint": revision_row.get("contract_fingerprint"),
            "criteria_fingerprint": revision_row.get("criteria_fingerprint"),
        },
        "typed_product_session_receipts": {
            "status": "OBSERVED" if all(session_receipts) else "UNAVAILABLE",
            "count": 2 if all(session_receipts) else None,
            "receipt_ids": [item for item in session_receipts if item],
            "endpoint_generation_used_as_session_identity": False,
            "missing_reason": None if all(session_receipts) else "typed_product_session_receipts_incomplete",
        },
        "gates": gates,
        "gate_counts": counts,
        "economics": {
            "status": "AVAILABLE" if journey is not None else "UNAVAILABLE",
            "unit": "problem_revision",
            "journey": journey,
            "receipt_id": economics_receipt or None,
            "unknowns_preserved": True,
            "automatic_policy_promotion": False,
            "missing_reason": None if journey is not None else "exact_problem_revision_economics_journey_missing",
        },
        "fact_window": {
            "status": "BOUNDED",
            "fact_limits": dict(_FACT_LIMITS),
            "problem_fact_limits": dict(problems.fact_limits),
            "truncated_tables": [],
            "cross_session_fact_load_statements": facts.fact_load_statements,
            "problem_lineage_fact_load_statements": problems.fact_load_statements,
            "all_gate_reads_from_immutable_memory": True,
        },
        "policy": _policy(),
    }
