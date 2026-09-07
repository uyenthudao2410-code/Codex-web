"""Read-only, revision-scoped PRL v12 measurement over one immutable snapshot.

The reporter is deliberately descriptive. It never turns a thread projection
into an outcome for an older revision, silently sums incompatible clocks, or
converts missing observations into zero-duration results.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from .ledger_analysis import LedgerFacts, LedgerReadSession
from .problem_lineage import (
    PROBLEM_EVENT_SCHEMA_CURRENT,
    PROBLEM_EVENT_SCHEMA_V11,
    PROBLEM_SCHEMA_VERSION,
    problem_event_hash_material,
    problem_outcome_receipt_id,
)
from .problem_resolution_journey import problem_revision_journeys


PROBLEM_RESOLUTION_ECONOMICS_SCHEMA_VERSION = 7
_ACTIVE_STAGES = frozenset({"preflight", "localization", "routing", "execution", "replan", "proof", "acceptance"})
_ADMINISTRATIVE_RELATIONS = frozenset({"BLOCK", "ABANDON"})
_FACT_LIMITS = {
    "problem_threads": 5_000,
    "problem_revisions": 5_000,
    "problem_events": 50_000,
    "controller_knowledge_checkpoints": 20_000,
    "controller_knowledge_acks": 20_000,
    "controller_reattach_receipts": 20_000,
    "handoff_capsules": 20_000,
}
_OPTIONAL_FACT_TABLES = (
    "controller_knowledge_checkpoints",
    "controller_knowledge_acks",
    "controller_reattach_receipts",
    "handoff_capsules",
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _time(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(_text(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _ordered(values: list[float]) -> list[float] | None:
    return [round(item, 6) for item in sorted(values)] if 0 < len(values) <= 20 else None


def _percentile(values: list[float], percentile: int) -> float | None:
    if len(values) < 20:
        return None
    ordered = sorted(values)
    return round(ordered[max(0, min(len(ordered) - 1, math.ceil(len(ordered) * percentile / 100) - 1))], 6)


def _fact_event(row: Any) -> dict[str, Any]:
    event = dict(row)
    raw_eligible = bool(event.get("eligible_for_policy"))
    if int(event.get("event_schema_version") or 1) <= 1:
        event["legacy_eligible_for_policy"] = raw_eligible
        event["eligible_for_policy"] = False
    else:
        event["eligible_for_policy"] = raw_eligible
    return event


class ProblemLineageFacts:
    """Opt-in PRL facts from an immutable read-only snapshot.

    ``events_for_problem`` keeps legacy events for chain verification. All
    outcome measurement uses ``events_for_revision`` and cannot reassign old
    events to a later revision.
    """

    def __init__(
        self,
        *,
        schema_version: int,
        threads: list[dict[str, Any]],
        revisions: list[dict[str, Any]],
        events: list[dict[str, Any]],
        fact_load_statements: int,
        optional_facts: dict[str, list[dict[str, Any]]] | None = None,
        available_fact_tables: set[str] | None = None,
        truncated_tables: set[str] | None = None,
    ) -> None:
        self.schema_version = schema_version
        self.threads = threads
        self.revisions = revisions
        self.events = events
        self.fact_load_statements = fact_load_statements
        self.fact_limits = dict(_FACT_LIMITS)
        self.available_fact_tables = frozenset(available_fact_tables or set())
        self.truncated_tables = frozenset(truncated_tables or set())
        self._optional_facts = {name: list(rows) for name, rows in (optional_facts or {}).items()}
        self._events_by_problem: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._events_by_revision: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
        self._revisions_by_problem: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in events:
            problem_id = _text(event.get("problem_id"))
            if problem_id:
                self._events_by_problem[problem_id].append(event)
            revision = event.get("problem_revision")
            if int(event.get("event_schema_version") or 1) >= PROBLEM_EVENT_SCHEMA_V11 and problem_id and isinstance(revision, int) and not isinstance(revision, bool) and revision > 0:
                self._events_by_revision[(problem_id, revision)].append(event)
        for revision in revisions:
            problem_id = _text(revision.get("problem_id"))
            if problem_id:
                self._revisions_by_problem[problem_id].append(revision)
        for values in self._events_by_problem.values():
            values.sort(key=lambda item: int(item.get("seq") or 0))
        for values in self._events_by_revision.values():
            values.sort(key=lambda item: int(item.get("seq") or 0))
        for values in self._revisions_by_problem.values():
            values.sort(key=lambda item: int(item.get("revision") or 0))

    @classmethod
    def load(cls, reader: LedgerReadSession) -> "ProblemLineageFacts":
        statement_start = reader.statement_count
        row = reader.one("PRAGMA user_version")
        schema = int(row[0] if row is not None else 0)
        if schema != PROBLEM_SCHEMA_VERSION:
            return cls(
                schema_version=schema,
                threads=[],
                revisions=[],
                events=[],
                fact_load_statements=reader.statement_count - statement_start,
            )

        truncated: set[str] = set()

        def bounded_rows(table: str, order_by: str) -> list[dict[str, Any]]:
            limit = _FACT_LIMITS[table]
            rows = reader.rows(f"SELECT * FROM {table} ORDER BY {order_by} LIMIT ?", (limit + 1,))
            if len(rows) > limit:
                truncated.add(table)
            return [dict(item) for item in rows[:limit]]

        available_rows = reader.rows(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name IN (?,?,?,?) ORDER BY name",
            _OPTIONAL_FACT_TABLES,
        )
        available = {str(item["name"]) for item in available_rows}
        optional: dict[str, list[dict[str, Any]]] = {}
        optional_order = {
            "controller_knowledge_checkpoints": "problem_id,problem_revision,knowledge_revision,checkpoint_id",
            "controller_knowledge_acks": "problem_id,problem_revision,created_at,ack_id",
            "controller_reattach_receipts": "problem_id,problem_revision,generation,reattach_id",
            "handoff_capsules": "run_id,conversation_epoch,created_at,capsule_id",
        }
        for table in _OPTIONAL_FACT_TABLES:
            if table in available:
                optional[table] = bounded_rows(table, optional_order[table])
        return cls(
            schema_version=schema,
            threads=bounded_rows("problem_threads", "problem_id"),
            revisions=bounded_rows("problem_revisions", "problem_id,revision"),
            events=[_fact_event(item) for item in bounded_rows("problem_events", "problem_id,seq")],
            fact_load_statements=reader.statement_count - statement_start,
            optional_facts=optional,
            available_fact_tables=available,
            truncated_tables=truncated,
        )

    def events_for_problem(self, problem_id: str) -> list[dict[str, Any]]:
        return list(self._events_by_problem.get(problem_id, ()))

    def events_for_revision(self, problem_id: str, revision: int) -> list[dict[str, Any]]:
        return list(self._events_by_revision.get((problem_id, revision), ()))

    def revisions_for_problem(self, problem_id: str) -> list[dict[str, Any]]:
        return list(self._revisions_by_problem.get(problem_id, ()))

    def optional_rows(self, table: str) -> list[dict[str, Any]]:
        return list(self._optional_facts.get(table, ()))

    def verify_chain(self, problem_id: str) -> dict[str, Any]:
        previous = ""
        events = self.events_for_problem(problem_id)
        for event in events:
            if _text(event.get("prev_hash")) != previous:
                return {"ok": False, "reason": "prev_hash_mismatch"}
            material = problem_event_hash_material(event, state_before=_text(event.get("state_before")), state_after=_text(event.get("state_after")), prev_hash=previous)
            expected = hashlib.sha256(json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if expected != _text(event.get("event_hash")):
                return {"ok": False, "reason": "event_hash_mismatch"}
            previous = expected
        return {"ok": True, "event_count": len(events)}


def _current_eligible(event: dict[str, Any]) -> bool:
    return int(event.get("event_schema_version") or 1) >= PROBLEM_EVENT_SCHEMA_V11 and bool(event.get("eligible_for_policy"))


def _independent_outcome_receipt_bound(event: dict[str, Any]) -> bool:
    if int(event.get("event_schema_version") or 1) < PROBLEM_EVENT_SCHEMA_CURRENT:
        return False
    receipt_type = _text(event.get("outcome_receipt_type"))
    receipt_id = _text(event.get("outcome_receipt_id")).lower()
    if (
        receipt_type != "CHATWEB_EXPLICIT_USER_OUTCOME_V1"
        or _text(event.get("relation_type")) != "CONFIRMED_RESOLUTION"
        or _text(event.get("transition_authority")) != "RUNTIME_OUTCOME_RECEIPT"
        or _text(event.get("provenance")) != "CONTROLLER_REPORTED_EXPLICIT_USER"
        or _text(event.get("evidence_level")) != "OBSERVED"
        or not _text(event.get("turn_id"))
        or not _text(event.get("trace_id"))
    ):
        return False
    expected = problem_outcome_receipt_id(
        receipt_type=receipt_type,
        event_id=_text(event.get("event_id")),
        problem_id=_text(event.get("problem_id")),
        problem_revision=int(event.get("problem_revision") or 0),
        turn_id=_text(event.get("turn_id")),
        trace_id=_text(event.get("trace_id")),
    )
    return receipt_id == expected


def _attested_clock(event: dict[str, Any]) -> tuple[datetime, str] | None:
    if not _current_eligible(event):
        return None
    occurred = _time(event.get("occurred_at"))
    authority = _text(event.get("clock_authority"))
    if occurred is None or not _text(event.get("occurred_at_source")) or not authority:
        return None
    return occurred, authority


def _elapsed_ms(start: dict[str, Any], finish: dict[str, Any]) -> tuple[float | None, str | None]:
    start_clock, finish_clock = _attested_clock(start), _attested_clock(finish)
    if start_clock is None or finish_clock is None:
        return None, "attested_occurrence_clock_missing"
    if start_clock[1] != finish_clock[1]:
        return None, "attested_clock_authority_mismatch"
    elapsed = (finish_clock[0] - start_clock[0]).total_seconds() * 1000
    return (round(elapsed, 6), None) if elapsed >= 0 else (None, "clock_order_anomaly")


def _revision_start_event(revision: dict[str, Any], events: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str | None]:
    sequence = revision.get("created_event_seq")
    number = revision.get("revision")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        return None, "revision_start_event_missing"
    target = next((event for event in events if int(event.get("seq") or 0) == sequence), None)
    if target is None or not _current_eligible(target):
        return None, "revision_start_event_ineligible"
    if _text(target.get("relation_type")) != ("OPEN" if number == 1 else "REVISION"):
        return None, "revision_start_event_relation_mismatch"
    return target, None


def _first_relation(events: list[dict[str, Any]], relation: str) -> dict[str, Any] | None:
    return next((event for event in events if _current_eligible(event) and _text(event.get("relation_type")) == relation), None)


def _administrative_disposition(revision: dict[str, Any], events: list[dict[str, Any]], all_revisions: list[dict[str, Any]], facts: ProblemLineageFacts) -> dict[str, Any] | None:
    candidates = [event for event in events if _current_eligible(event) and _text(event.get("relation_type")) in _ADMINISTRATIVE_RELATIONS]
    number = int(revision.get("revision") or 0)
    successor_row = next((item for item in all_revisions if int(item.get("revision") or 0) == number + 1), None)
    if successor_row is not None:
        successor, _ = _revision_start_event(successor_row, facts.events_for_revision(_text(revision.get("problem_id")), number + 1))
        if successor is not None:
            candidates.append({**successor, "derived_disposition": "SUPERSEDED_BY_REVISION"})
    return min(candidates, key=lambda event: int(event.get("seq") or 0), default=None)


def _exact_primary_linked_runs(events: list[dict[str, Any]]) -> set[str]:
    return {
        _text(event.get("run_id")) for event in events
        if _current_eligible(event) and _text(event.get("link_status")) == "EXACT" and _text(event.get("link_role")) == "PRIMARY"
        and _text(event.get("relation_type")) in {"LINK", "ENGINEERING_ATTEMPT_BOUND"} and _text(event.get("run_id"))
    }


def _primary_runs(ledger: LedgerFacts, problem_id: str, revision: int, events: list[dict[str, Any]]) -> set[str]:
    candidates = _exact_primary_linked_runs(events)
    result: set[str] = set()
    for run_id in candidates:
        for wave in ledger.list_waves(run_id):
            metadata = wave.get("metadata") if isinstance(wave.get("metadata"), dict) else {}
            context = metadata.get("problem_resolution") if isinstance(metadata.get("problem_resolution"), dict) else {}
            if isinstance(context, dict) and context.get("work_origin") == "problem" and context.get("resolution_claim") == "full_problem" and context.get("problem_id") == problem_id and context.get("problem_revision") == revision:
                result.add(run_id)
    return result


def _restricted_active_ms(ledger: LedgerFacts, run_ids: set[str]) -> tuple[float | None, str | None]:
    if not run_ids:
        return None, "exact_primary_runs_missing"
    intervals: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for run_id in run_ids:
        for span in ledger.list_observation_spans(run_id, limit=1000):
            if _text(span.get("stage")).lower() not in _ACTIVE_STAGES:
                continue
            domain, start, end = _text(span.get("clock_domain")), span.get("start_ms"), span.get("end_ms")
            if not domain or isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or not math.isfinite(float(start)) or not math.isfinite(float(end)) or float(end) < float(start):
                return None, "invalid_active_segment_present"
            intervals[domain].append((float(start), float(end)))
    if not intervals:
        return None, "same_domain_active_segments_missing"
    if len(intervals) != 1:
        return None, "multiple_clock_domains_not_summed"
    total, end = 0.0, -math.inf
    for start, finish in sorted(next(iter(intervals.values()))):
        if start > end:
            total += finish - start
            end = finish
        elif finish > end:
            total += finish - end
    return round(total, 6), None


def _metric(values: list[float], missing: Counter[str], *, metric_name: str, definition: str, eligible: int, censored: int, competing: int) -> dict[str, Any]:
    return {
        "metric_name": metric_name, "unit": "problem_revision", "definition": definition,
        "eligible_revision_units": eligible, "observed": len(values), "right_censored": censored,
        "competing_disposition": competing, "right_censored_or_competing": censored + competing,
        "missing_or_invalid_reason_counts": dict(sorted(missing.items())),
        "ordered_exact_values_ms_when_n_le_20": _ordered(values), "p50": _percentile(values, 50), "p90": _percentile(values, 90),
        "small_n_policy": "exact_ordered_values_not_population_tail_inference",
    }


def _classify_duration(start: dict[str, Any] | None, target: dict[str, Any] | None, disposition: dict[str, Any] | None) -> tuple[str, float | None, str | None]:
    if start is None:
        return "missing", None, "revision_start_event_missing"
    target_seq = int(target.get("seq") or 0) if target is not None else math.inf
    disposition_seq = int(disposition.get("seq") or 0) if disposition is not None else math.inf
    if disposition_seq < target_seq:
        return "competing", None, None
    if target is None:
        return "censored", None, None
    value, reason = _elapsed_ms(start, target)
    return ("observed", value, None) if value is not None else ("missing", None, reason)


def _revision_time_value(outcome: str, value: float | None, reason: str | None, *, definition: str) -> dict[str, Any]:
    status = {
        "observed": "OBSERVED",
        "censored": "RIGHT_CENSORED",
        "competing": "COMPETING_DISPOSITION",
        "missing": "UNAVAILABLE",
    }.get(outcome, "UNAVAILABLE")
    return {
        "status": status,
        "value_ms": round(float(value), 6) if value is not None else None,
        "definition": definition,
        "missing_reason": reason if status == "UNAVAILABLE" else None,
        "unknown_is_not_zero": True,
    }


def problem_resolution_economics_report(ledger: LedgerFacts, problems: ProblemLineageFacts) -> dict[str, Any]:
    if not isinstance(ledger, LedgerFacts) or not isinstance(problems, ProblemLineageFacts):
        raise TypeError("problem-resolution economics requires immutable LedgerFacts and ProblemLineageFacts")
    if problems.schema_version != PROBLEM_SCHEMA_VERSION:
        return {"schema_version": PROBLEM_RESOLUTION_ECONOMICS_SCHEMA_VERSION, "status": "PRL_SCHEMA_INACTIVE", "observed_schema_version": problems.schema_version, "policy": {"no_writer": True, "no_historical_backfill": True, "unknown_is_not_zero": True}}
    if problems.truncated_tables:
        return {
            "schema_version": PROBLEM_RESOLUTION_ECONOMICS_SCHEMA_VERSION,
            "status": "FACT_WINDOW_TRUNCATED",
            "truncated_tables": sorted(problems.truncated_tables),
            "fact_limits": dict(problems.fact_limits),
            "policy": {
                "no_partial_causal_or_economic_projection": True,
                "no_writer": True,
                "unknown_is_not_zero": True,
            },
        }

    values: dict[str, list[float]] = {"provisional": [], "confirmed": [], "administrative": [], "interval_width": [], "active": []}
    missing: dict[str, Counter[str]] = {key: Counter() for key in values}
    censored: Counter[str] = Counter()
    competing: Counter[str] = Counter()
    revision_outcomes = Counter()
    intervals: list[dict[str, float]] = []
    wall_intervals: list[dict[str, float]] = []
    time_facts: list[dict[str, Any]] = []
    chain_invalid = exact_links = coverage_complete = receipt_bound_confirmations = 0
    thread_states = Counter(_text(thread.get("resolution_state")) or "UNKNOWN" for thread in problems.threads)

    for revision in problems.revisions:
        problem_id, number = _text(revision.get("problem_id")), int(revision.get("revision") or 0)
        if not problem_id or number < 1:
            continue
        events = problems.events_for_revision(problem_id, number)
        if not problems.verify_chain(problem_id).get("ok"):
            chain_invalid += 1
            for key in ("provisional", "confirmed", "administrative", "interval_width"):
                missing[key]["problem_event_chain_invalid"] += 1
            time_facts.append(
                {
                    "problem_id": problem_id,
                    "problem_revision": number,
                    "ttoc_wall_ms": _revision_time_value(
                        "missing",
                        None,
                        "problem_event_chain_invalid",
                        definition="attested revision start to authoritative confirmation; not exact real-world resolution",
                    ),
                    "ttpr_wall_interval": {
                        "status": "UNAVAILABLE",
                        "lower_bound_ms": None,
                        "upper_bound_ms": None,
                        "missing_reason": "problem_event_chain_invalid",
                        "unknown_is_not_zero": True,
                    },
                    "restricted_ttpr_active_ms": _revision_time_value(
                        "missing",
                        None,
                        "problem_event_chain_invalid",
                        definition="union of exact-primary-run active intervals in one clock domain",
                    ),
                }
            )
            continue
        start, start_reason = _revision_start_event(revision, events)
        provisional, confirmed = _first_relation(events, "PROVISIONAL_RESOLUTION"), _first_relation(events, "CONFIRMED_RESOLUTION")
        disposition = _administrative_disposition(revision, events, problems.revisions_for_problem(problem_id), problems)
        revision_time: dict[str, Any] = {"problem_id": problem_id, "problem_revision": number}
        for key, target in (("provisional", provisional), ("confirmed", confirmed), ("administrative", disposition)):
            outcome, duration, reason = _classify_duration(start, target, disposition if key != "administrative" else None)
            if outcome == "observed":
                values[key].append(float(duration))
            elif outcome == "censored":
                censored[key] += 1
            elif outcome == "competing":
                competing[key] += 1
            else:
                missing[key][reason or start_reason or "unknown"] += 1
            if key == "confirmed":
                revision_time["ttoc_wall_ms"] = _revision_time_value(
                    outcome,
                    duration,
                    reason or start_reason,
                    definition="attested revision start to authoritative confirmation; not exact real-world resolution",
                )
        if provisional is not None:
            revision_outcomes["technical_full_pass_observed"] += 1
        interval_outcome = "censored"
        interval_reason: str | None = None
        if confirmed is not None:
            revision_outcomes["authoritative_confirmation_observed"] += 1
        if confirmed is not None and _independent_outcome_receipt_bound(confirmed):
            receipt_bound_confirmations += 1
        if provisional is not None and confirmed is not None:
            revision_outcomes["trusted_resolution_observed"] += 1
        if disposition is not None:
            revision_outcomes["administrative_disposition_observed"] += 1
        if confirmed is not None:
            contradictory = max((int(event.get("seq") or 0) for event in events if _current_eligible(event) and _text(event.get("relation_type")) in {"REOPEN", "BLOCK", "ABANDON"} and int(event.get("seq") or 0) < int(confirmed.get("seq") or 0)), default=-1)
            candidates = [event for event in events if _current_eligible(event) and _text(event.get("relation_type")) == "PROVISIONAL_RESOLUTION" and contradictory < int(event.get("seq") or 0) < int(confirmed.get("seq") or 0)]
            lower = candidates[-1] if candidates else None
            outcome, width, reason = _classify_duration(lower, confirmed, disposition)
            interval_outcome, interval_reason = outcome, reason
            if outcome == "observed":
                values["interval_width"].append(float(width))
                lower_from_start, _ = _elapsed_ms(start or {}, lower)
                upper_from_start, _ = _elapsed_ms(start or {}, confirmed)
                if lower_from_start is not None and upper_from_start is not None:
                    intervals.append({"lower_bound_from_start_ms": lower_from_start, "upper_bound_from_start_ms": upper_from_start, "width_ms": float(width)})
                    wall_intervals.append({"lower_bound_ms": lower_from_start, "upper_bound_ms": upper_from_start, "width_ms": float(width)})
                    revision_time["ttpr_wall_interval"] = {
                        "status": "OBSERVED_INTERVAL_CENSORED",
                        "lower_bound_ms": lower_from_start,
                        "upper_bound_ms": upper_from_start,
                        "width_ms": float(width),
                        "confirmation_is_not_exact_resolution_time": True,
                        "missing_reason": None,
                        "unknown_is_not_zero": True,
                    }
            elif outcome == "censored":
                censored["interval_width"] += 1
            elif outcome == "competing":
                competing["interval_width"] += 1
            else:
                missing["interval_width"][reason or "technical_full_pass_before_confirmation_missing"] += 1
        elif disposition is not None:
            interval_outcome = "competing"
            competing["interval_width"] += 1
        else:
            censored["interval_width"] += 1
        if "ttpr_wall_interval" not in revision_time:
            interval_status = {
                "censored": "RIGHT_CENSORED",
                "competing": "COMPETING_DISPOSITION",
                "missing": "UNAVAILABLE",
            }.get(interval_outcome, "UNAVAILABLE")
            revision_time["ttpr_wall_interval"] = {
                "status": interval_status,
                "lower_bound_ms": None,
                "upper_bound_ms": None,
                "width_ms": None,
                "missing_reason": interval_reason if interval_status == "UNAVAILABLE" else None,
                "confirmation_is_not_exact_resolution_time": True,
                "unknown_is_not_zero": True,
            }
        run_ids = _primary_runs(ledger, problem_id, number, events)
        active, active_reason = _restricted_active_ms(ledger, run_ids)
        if active is None:
            missing["active"][active_reason or "unknown"] += 1
            revision_time["restricted_ttpr_active_ms"] = _revision_time_value(
                "missing",
                None,
                active_reason or "unknown",
                definition="union of exact-primary-run active intervals in one clock domain",
            )
        else:
            values["active"].append(active)
            revision_time["restricted_ttpr_active_ms"] = _revision_time_value(
                "observed",
                active,
                None,
                definition="union of exact-primary-run active intervals in one clock domain",
            )
        time_facts.append(revision_time)
        exact_links += sum(1 for event in events if _text(event.get("link_status")) == "EXACT")
        for run_id in run_ids:
            coverage_complete += sum(1 for wave in ledger.list_waves(run_id) if isinstance(wave.get("metadata"), dict) and isinstance(wave["metadata"].get("problem_resolution"), dict) and isinstance(wave["metadata"]["problem_resolution"].get("coverage_manifest"), dict))

    current_events = sum(1 for event in problems.events if int(event.get("event_schema_version") or 1) >= PROBLEM_EVENT_SCHEMA_V11)
    legacy_events, revision_count = len(problems.events) - current_events, len(problems.revisions)
    metrics = {
        "time_to_provisional": _metric(values["provisional"], missing["provisional"], metric_name="TTFP", definition="attested revision start to deterministic provisional resolution", eligible=revision_count, censored=censored["provisional"], competing=competing["provisional"]),
        "time_to_confirmed_resolution": _metric(values["confirmed"], missing["confirmed"], metric_name="TTOC", definition="attested revision start to authoritative confirmation; not exact real-world resolution", eligible=revision_count, censored=censored["confirmed"], competing=competing["confirmed"]),
        "time_to_administrative_disposition": _metric(values["administrative"], missing["administrative"], metric_name="ADMINISTRATIVE_DISPOSITION", definition="attested revision start to block, abandon, or superseded-by-revision; never success", eligible=revision_count, censored=censored["administrative"], competing=competing["administrative"]),
        "resolution_interval_width_ms": _metric(values["interval_width"], missing["interval_width"], metric_name="RESOLUTION_INTERVAL_WIDTH", definition="latest valid technical full pass to observed authoritative confirmation", eligible=revision_count, censored=censored["interval_width"], competing=competing["interval_width"]),
    }
    trusted = revision_outcomes["trusted_resolution_observed"]
    # Revision-4 diagnostics are descriptive only.  They intentionally use
    # problem-revision denominators and never infer a missing outcome from a
    # technical checkpoint or from a silent interval.
    first_pass = false_closure = 0
    frame_events = decision_changed = 0
    counterevidence_frame_events = counterevidence_advisory_events = 0
    frame_revisions: set[tuple[str, int, str, int]] = set()
    envelope_claims = envelope_with_observed_evidence = 0
    run_counts_by_revision: Counter[tuple[str, int]] = Counter()
    control_friction: Counter[str] = Counter()
    for revision in problems.revisions:
        problem_id, number = _text(revision.get("problem_id")), int(revision.get("revision") or 0)
        events = problems.events_for_revision(problem_id, number)
        primary_runs = _exact_primary_linked_runs(events)
        run_counts_by_revision[(problem_id, number)] = len(primary_runs)
        provisional, confirmed = _first_relation(events, "PROVISIONAL_RESOLUTION"), _first_relation(events, "CONFIRMED_RESOLUTION")
        reopen_seq = min((int(event.get("seq") or 0) for event in events if _current_eligible(event) and _text(event.get("relation_type")) == "REOPEN"), default=0)
        if provisional is not None and confirmed is not None and len(primary_runs) == 1 and not reopen_seq:
            first_pass += 1
        if provisional is not None and reopen_seq and reopen_seq > int(provisional.get("seq") or 0):
            false_closure += 1
        for run_id in primary_runs:
            for event in ledger.list_events(run_id):
                if str(event.get("event_type") or "") == "problem_frame_shadow":
                    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
                    if str(payload.get("problem_id") or "") == problem_id and int(payload.get("problem_revision") or 0) == number:
                        frame_events += 1
                        frame_revisions.add((problem_id, number, str(payload.get("frame_id") or ""), int(payload.get("frame_revision") or 0)))
                        decision_changed += int(bool(payload.get("decision_changed")))
                        if int(payload.get("counterevidence_count") or 0) > 0:
                            counterevidence_frame_events += 1
                            if (
                                str(payload.get("counterevidence_advisory_status") or "") == "COUNTEREVIDENCE_REQUIRES_FRAME_REVIEW"
                                and bool(payload.get("frame_update_or_explanation_recommended"))
                                and not bool(payload.get("materiality_inferred"))
                                and not bool(payload.get("automatic_mutation_gate"))
                            ):
                                counterevidence_advisory_events += 1
            for wave in ledger.list_waves(run_id):
                metadata = wave.get("metadata") if isinstance(wave.get("metadata"), dict) else {}
                context = metadata.get("problem_resolution") if isinstance(metadata.get("problem_resolution"), dict) else {}
                claim = context.get("outcome_claim") if isinstance(context.get("outcome_claim"), dict) else {}
                envelope = claim.get("resolution_envelope") if isinstance(claim.get("resolution_envelope"), dict) else None
                if envelope is not None:
                    envelope_claims += 1
                    evidence = envelope.get("required_evidence") if isinstance(envelope.get("required_evidence"), list) else []
                    if any(str(item.get("status") or "").lower() == "observed" for item in evidence if isinstance(item, dict)):
                        envelope_with_observed_evidence += 1
                for event in ledger.list_events(run_id, wave_id=str(wave.get("wave_id") or "")):
                    if str(event.get("event_type") or "") == "wave_replanned":
                        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
                        reason = str(payload.get("reason") or "unknown").strip().lower()
                        control_friction[reason if reason else "unknown"] += 1
    multi_primary_run_revisions = sum(1 for value in run_counts_by_revision.values() if value > 1)
    revision_metrics = {
        "first_pass_trusted_resolution": {"unit": "problem_revision", "numerator": first_pass, "denominator": revision_count, "rate": round(first_pass / revision_count, 6) if revision_count else None, "policy": "descriptive_only"},
        "false_closure": {"unit": "problem_revision", "numerator": false_closure, "denominator": revision_count, "rate": round(false_closure / revision_count, 6) if revision_count else None, "definition": "provisional technical closure followed by same-revision reopen", "unknown_is_not_zero": True},
        "frame_revisions": {"unit": "problem_revision", "observed_frame_events": frame_events, "distinct_frame_revisions": len(frame_revisions), "mean_per_revision": round(len(frame_revisions) / revision_count, 6) if revision_count else None},
        "decision_delta_shadow_attestation_rate": {"unit": "problem_frame_shadow_event", "changed_decision_attestations": decision_changed, "observed_shadow_events": frame_events, "rate": round(decision_changed / frame_events, 6) if frame_events else None, "classification": "shadow_attested", "causal_value_proven": False},
        "counterevidence_frame_update_advisory_coverage": {"unit": "problem_frame_shadow_with_counterevidence", "observed_counterevidence_events": counterevidence_frame_events, "events_with_update_or_explain_advisory": counterevidence_advisory_events, "coverage": round(counterevidence_advisory_events / counterevidence_frame_events, 6) if counterevidence_frame_events else None, "classification": "descriptive_advisory_only", "materiality_inferred": False, "automatic_mutation_gate": False},
        "resolution_envelope_evidence_attestation_coverage": {"unit": "full_problem_claim", "claims": envelope_claims, "claims_with_observed_attestation": envelope_with_observed_evidence, "coverage": round(envelope_with_observed_evidence / envelope_claims, 6) if envelope_claims else None, "classification": "descriptive_attested_not_independent_confirmation", "receipt_bound": False, "technical_proof_is_not_user_outcome": True},
        "multi_primary_run_revision_rate": {"unit": "problem_revision", "revisions_with_multiple_primary_runs": multi_primary_run_revisions, "denominator": revision_count, "rate": round(multi_primary_run_revisions / revision_count, 6) if revision_count else None, "classification": "descriptive_multiple_attempt_proxy", "semantic_sibling_linkage_proven": False, "timestamp_or_keyword_inference_forbidden": True},
        "framing_regret": {"unit": "avoidable_work_after_material_counterevidence", "status": "UNAVAILABLE", "value_ms": None, "missing_reason": "material_counterevidence_availability_clock_and_avoidable_work_attribution_not_recorded", "timestamp_or_keyword_inference_forbidden": True, "unknown_is_not_zero": True},
        "true_sibling_recurrence": {"unit": "problem_revision", "status": "UNAVAILABLE", "rate": None, "missing_reason": "explicit_semantic_sibling_linkage_not_recorded", "multi_primary_run_is_proxy_only": True, "unknown_is_not_zero": True},
        "independent_outcome_evidence_coverage": {
            "unit": "problem_revision",
            "status": "AVAILABLE",
            "numerator": receipt_bound_confirmations,
            "denominator": revision_count,
            "coverage": round(receipt_bound_confirmations / revision_count, 6) if revision_count else None,
            "authoritative_confirmation_events": int(revision_outcomes["authoritative_confirmation_observed"]),
            "receipt_bound_confirmation_events": receipt_bound_confirmations,
            "unbound_authoritative_confirmation_events": max(0, int(revision_outcomes["authoritative_confirmation_observed"]) - receipt_bound_confirmations),
            "receipt_type": "CHATWEB_EXPLICIT_USER_OUTCOME_V1",
            "independence_definition": "host_attested_explicit_user_outcome_not_derived_from_technical_proof",
            "historical_confirmations_not_backfilled": True,
            "unknown_is_not_zero": True,
        },
        "control_friction_decomposition": {"unit": "wave_replanned_event", "counts": dict(sorted(control_friction.items())), "classification": "descriptive_structured_reason_only", "unknown_is_not_zero": True},
    }
    journeys = problem_revision_journeys(
        ledger,
        problems,
        time_facts=time_facts,
        receipt_bound=_independent_outcome_receipt_bound,
    )
    return {
        "schema_version": PROBLEM_RESOLUTION_ECONOMICS_SCHEMA_VERSION, "problem_schema_version": problems.schema_version,
        "status": "DESCRIPTIVE_ONLY" if current_events else "NO_CURRENT_PRL_EVENTS",
        "analysis_unit": {"primary": "problem_revision", "key_fields": ["problem_id", "revision"], "thread_state_is_compatibility_projection_only": True},
        "denominators": {"problem_threads": len(problems.threads), "problem_revisions": revision_count, "analysis_problem_revisions": revision_count, "problem_events": len(problems.events), "current_policy_schema_events": current_events, "legacy_events_excluded_from_policy": legacy_events, "exact_revision_link_events": exact_links, "problem_chain_invalid_threads": chain_invalid, "right_censored_unconfirmed_revisions": censored["confirmed"], "competing_administrative_revision_dispositions": competing["confirmed"]},
        "resolution_outcomes": {"state_counts": dict(sorted(thread_states.items())), "thread_projection_state_counts": dict(sorted(thread_states.items())), "provisional_threads": int(thread_states.get("PROVISIONALLY_RESOLVED", 0)), "confirmed_threads": int(thread_states.get("RESOLVED_CONFIRMED", 0)), "reopened_ever_threads": sum(1 for thread in problems.threads if any(_text(event.get("relation_type")) == "REOPEN" for event in problems.events_for_problem(_text(thread.get("problem_id"))))), "revision_outcomes": dict(sorted(revision_outcomes.items())), "trusted_resolution": {"unit": "problem_revision", "true": trusted, "unknown_or_untrusted": max(0, revision_count - trusted), "user_confirmation_does_not_accept_eocl_run": True}, "administrative_disposition_is_not_resolution": True},
        **metrics,
        "resolution_interval": {"unit": "problem_revision", "definition": "[latest valid technical full pass before confirmation, observed confirmation]; interval-censored real-world resolution", "observed_intervals": len(values["interval_width"]), "right_censored": censored["interval_width"], "competing_disposition": competing["interval_width"], "missing_or_invalid_reason_counts": dict(sorted(missing["interval_width"].items())), "ordered_exact_intervals_ms_when_n_le_20": intervals if 0 < len(intervals) <= 20 else None, "confirmation_is_not_exact_resolution_time": True},
        "ttpr_wall_ms": {"unit": "problem_revision", "definition": "attested authoritative start to interval-censored resolution", "point_estimate_status": "UNAVAILABLE_INTERVAL_CENSORED", "observed_intervals": len(wall_intervals), "ordered_exact_intervals_ms_when_n_le_20": wall_intervals if 0 < len(wall_intervals) <= 20 else None, "point_p50": None, "point_p90": None, "same_attested_clock_authority_required": True, "confirmation_is_not_exact_resolution_time": True},
        "restricted_ttpr_ms": {"definition": "union_of_active_stage_intervals_for_exact_primary_runs_of_one_problem_revision", "unit": "problem_revision", "active_stages": sorted(_ACTIVE_STAGES), "observed_revisions": len(values["active"]), "observed_threads": len(values["active"]), "missing_reason_counts": dict(sorted(missing["active"].items())), "ordered_exact_values_ms_when_n_le_20": _ordered(values["active"]), "p50": _percentile(values["active"], 50), "p90": _percentile(values["active"], 90), "cross_clock_domains_are_not_summed": True},
        "mechanics_coverage": {"exact_revision_binding_events": exact_links, "full_claim_waves_with_structural_manifest": coverage_complete, "receipt_bound_outcome_confirmations": receipt_bound_confirmations, "outcome_observation_requires_authoritative_transition": True, "legacy_schema_events_policy_ineligible": True},
        "policy": {"read_only_immutable_snapshot_required": True, "no_writer_or_schema_mutation": True, "no_raw_prompt_response_or_transcript": True, "no_timestamp_proximity_link": True, "no_historical_causal_backfill": True, "silence_is_censored": True, "administrative_disposition_not_success": True, "automatic_policy_promotion": False},
        "revision_4_metrics": revision_metrics,
        "problem_revision_journeys": journeys,
    }
