"""Read-only PRL-D v11 measurement over one immutable canonical snapshot.

This reporter describes observed coverage and timestamps.  It never writes,
backfills semantic intent, treats confirmation as EOCL acceptance, turns
silence into success, or counts administrative disposition as resolution.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from .ledger_analysis import LedgerFacts, LedgerReadSession
from .problem_lineage import PROBLEM_EVENT_SCHEMA_CURRENT, PROBLEM_SCHEMA_VERSION, problem_event_hash_material


PROBLEM_RESOLUTION_ECONOMICS_SCHEMA_VERSION = 2
_ACTIVE_STAGES = frozenset({"preflight", "localization", "routing", "execution", "replan", "proof", "acceptance"})
_OPEN_STATES = frozenset({"OPEN", "REOPENED", "REVISED", "PROVISIONALLY_RESOLVED"})
_ADMINISTRATIVE_STATES = frozenset({"BLOCKED", "ABANDONED", "SUPERSEDED"})


def _text(value: Any) -> str:
    return str(value or "").strip()


def _time(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(_text(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _ordered(values: list[float]) -> list[float] | None:
    return [round(item, 6) for item in sorted(values)] if 0 < len(values) <= 20 else None


def _fact_event(row: Any) -> dict[str, Any]:
    """Normalize SQLite booleans exactly as the canonical event projection does.

    Event hashes were written from Python booleans.  SQLite returns the stored
    integer, whose JSON encoding differs (``0``/``1`` rather than
    ``false``/``true``); retaining it would make every otherwise-valid chain
    look corrupt to a read-only reporter.
    """
    event = dict(row)
    raw_eligible = bool(event.get("eligible_for_policy"))
    if int(event.get("event_schema_version") or 1) <= 1:
        event["legacy_eligible_for_policy"] = raw_eligible
        event["eligible_for_policy"] = False
    else:
        event["eligible_for_policy"] = raw_eligible
    return event


def _percentile(values: list[float], percentile: int) -> float | None:
    if len(values) < 20:
        return None
    ordered = sorted(values)
    return round(ordered[max(0, min(len(ordered) - 1, math.ceil(len(ordered) * percentile / 100) - 1))], 6)


class ProblemLineageFacts:
    """Opt-in PRL table facts from an immutable read-only snapshot."""

    def __init__(self, *, schema_version: int, threads: list[dict[str, Any]], revisions: list[dict[str, Any]], events: list[dict[str, Any]], fact_load_statements: int) -> None:
        self.schema_version = schema_version
        self.threads = threads
        self.revisions = revisions
        self.events = events
        self.fact_load_statements = fact_load_statements
        self._events: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in events:
            if _text(event.get("problem_id")):
                self._events[_text(event["problem_id"])].append(event)
        for values in self._events.values():
            values.sort(key=lambda item: int(item.get("seq") or 0))

    @classmethod
    def load(cls, reader: LedgerReadSession) -> "ProblemLineageFacts":
        row = reader.one("PRAGMA user_version")
        schema = int(row[0] if row is not None else 0)
        if schema != PROBLEM_SCHEMA_VERSION:
            return cls(schema_version=schema, threads=[], revisions=[], events=[], fact_load_statements=1)
        return cls(
            schema_version=schema,
            threads=[dict(row) for row in reader.rows("SELECT * FROM problem_threads ORDER BY problem_id")],
            revisions=[dict(row) for row in reader.rows("SELECT * FROM problem_revisions ORDER BY problem_id,revision")],
            events=[_fact_event(row) for row in reader.rows("SELECT * FROM problem_events ORDER BY problem_id,seq")],
            fact_load_statements=4,
        )

    def events_for_problem(self, problem_id: str) -> list[dict[str, Any]]:
        return list(self._events.get(problem_id, ()))

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


def _current_event(event: dict[str, Any]) -> bool:
    return int(event.get("event_schema_version") or 1) == PROBLEM_EVENT_SCHEMA_CURRENT


def _eligible_event(event: dict[str, Any]) -> bool:
    return _current_event(event) and bool(event.get("eligible_for_policy"))


def _attested_time(event: dict[str, Any]) -> datetime | None:
    if not _current_event(event) or not _text(event.get("clock_authority")):
        return None
    return _time(event.get("occurred_at"))


def _first(events: list[dict[str, Any]], relation: str) -> dict[str, Any] | None:
    return next((event for event in events if _eligible_event(event) and _text(event.get("relation_type")) == relation), None)


def _duration(events: list[dict[str, Any]], relation: str) -> tuple[float | None, str | None]:
    start, finish = _first(events, "OPEN"), _first(events, relation)
    if start is None:
        return None, "eligible_problem_open_missing"
    if finish is None:
        return None, "right_censored_or_no_observed_outcome"
    start_at, finish_at = _attested_time(start), _attested_time(finish)
    if start_at is None or finish_at is None:
        return None, "attested_occurrence_clock_missing"
    result = (finish_at - start_at).total_seconds() * 1000
    return (round(result, 6), None) if result >= 0 else (None, "clock_order_anomaly")


def _primary_runs(events: list[dict[str, Any]]) -> set[str]:
    return {
        _text(event.get("run_id")) for event in events
        if _current_event(event) and _text(event.get("link_status")) == "EXACT"
        and _text(event.get("link_role")) == "PRIMARY"
        and _text(event.get("relation_type")) in {"LINK", "ENGINEERING_ATTEMPT_BOUND"}
        and _text(event.get("run_id"))
    }


def _restricted_active_ms(ledger: LedgerFacts, run_ids: set[str]) -> tuple[float | None, str | None]:
    intervals: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for run_id in run_ids:
        for span in ledger.list_observation_spans(run_id, limit=1000):
            if _text(span.get("stage")).lower() not in _ACTIVE_STAGES:
                continue
            domain, start, end = _text(span.get("clock_domain")), span.get("start_ms"), span.get("end_ms")
            if not domain or isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or float(end) < float(start):
                continue
            intervals[domain].append((float(start), float(end)))
    if not intervals:
        return None, "same_domain_active_segments_missing"
    if len(intervals) != 1:
        return None, "multiple_clock_domains_not_summed"
    total, end = 0.0, -math.inf
    for start, finish in sorted(intervals.popitem()[1]):
        if start > end:
            total += finish - start
            end = finish
        elif finish > end:
            total += finish - end
            end = finish
    return round(total, 6), None


def _metric(values: list[float], missing: Counter[str], *, definition: str, censored: int) -> dict[str, Any]:
    return {
        "definition": definition,
        "observed": len(values),
        "right_censored_or_competing": censored,
        "missing_or_invalid_reason_counts": dict(sorted(missing.items())),
        "ordered_exact_values_ms_when_n_le_20": _ordered(values),
        "p50": _percentile(values, 50),
        "p90": _percentile(values, 90),
        "small_n_policy": "exact_ordered_values_not_population_tail_inference",
    }


def problem_resolution_economics_report(ledger: LedgerFacts, problems: ProblemLineageFacts) -> dict[str, Any]:
    if not isinstance(ledger, LedgerFacts) or not isinstance(problems, ProblemLineageFacts):
        raise TypeError("problem-resolution economics requires immutable LedgerFacts and ProblemLineageFacts")
    if problems.schema_version != PROBLEM_SCHEMA_VERSION:
        return {"schema_version": PROBLEM_RESOLUTION_ECONOMICS_SCHEMA_VERSION, "status": "PRL_SCHEMA_INACTIVE", "observed_schema_version": problems.schema_version, "policy": {"no_writer": True, "no_historical_backfill": True, "unknown_is_not_zero": True}}

    state_counts = Counter(_text(thread.get("resolution_state")) or "UNKNOWN" for thread in problems.threads)
    provisional_values: list[float] = []; confirmed_values: list[float] = []; administrative_values: list[float] = []
    provisional_missing: Counter[str] = Counter(); confirmed_missing: Counter[str] = Counter(); administrative_missing: Counter[str] = Counter()
    chain_invalid = reopened = exact_links = current_events = legacy_events = coverage_complete = trusted = 0
    censored = competing = active_observed = 0
    for thread in problems.threads:
        problem_id = _text(thread.get("problem_id")); events = problems.events_for_problem(problem_id)
        if not problems.verify_chain(problem_id).get("ok"): chain_invalid += 1
        current_events += sum(1 for event in events if _current_event(event)); legacy_events += sum(1 for event in events if not _current_event(event))
        exact_links += sum(1 for event in events if _current_event(event) and _text(event.get("link_status")) == "EXACT" and event.get("problem_revision") is not None)
        if any(_text(event.get("state_after")) == "REOPENED" for event in events): reopened += 1
        state = _text(thread.get("resolution_state"))
        if state in _OPEN_STATES: censored += 1
        if state in _ADMINISTRATIVE_STATES: competing += 1
        for relation, values, missing in (("PROVISIONAL_RESOLUTION", provisional_values, provisional_missing), ("CONFIRMED_RESOLUTION", confirmed_values, confirmed_missing)):
            duration, reason = _duration(events, relation)
            if duration is None: missing[reason or "unknown"] += 1
            else: values.append(duration)
        administrative_event = next((event for event in events if _eligible_event(event) and _text(event.get("state_after")) in _ADMINISTRATIVE_STATES), None)
        if administrative_event is None:
            administrative_missing["no_administrative_disposition"] += 1
        else:
            start = _first(events, "OPEN"); started_at, finished_at = _attested_time(start or {}), _attested_time(administrative_event)
            if started_at is None or finished_at is None or finished_at < started_at: administrative_missing["attested_occurrence_clock_missing"] += 1
            else: administrative_values.append(round((finished_at - started_at).total_seconds() * 1000, 6))
        run_ids = _primary_runs(events)
        active, _reason = _restricted_active_ms(ledger, run_ids)
        if active is not None: active_observed += 1
        for run_id in run_ids:
            wave_rows = ledger.list_waves(run_id)
            for wave in wave_rows:
                context = (wave.get("metadata") or {}).get("problem_resolution") if isinstance(wave.get("metadata"), dict) else {}
                if isinstance(context, dict) and context.get("work_origin") == "problem" and context.get("resolution_claim") == "full_problem" and isinstance(context.get("coverage_manifest"), dict):
                    coverage_complete += 1
        if state == "RESOLVED_CONFIRMED" and any(_text(event.get("relation_type")) == "PROVISIONAL_RESOLUTION" and _eligible_event(event) for event in events):
            trusted += 1

    total_threads = len(problems.threads)
    return {
        "schema_version": PROBLEM_RESOLUTION_ECONOMICS_SCHEMA_VERSION,
        "problem_schema_version": problems.schema_version,
        "status": "DESCRIPTIVE_ONLY" if current_events else "NO_CURRENT_PRL_EVENTS",
        "denominators": {"problem_threads": total_threads, "problem_revisions": len(problems.revisions), "problem_events": len(problems.events), "current_v11_events": current_events, "legacy_events_excluded_from_policy": legacy_events, "exact_revision_link_events": exact_links, "right_censored_unconfirmed_threads": censored, "competing_administrative_dispositions": competing, "problem_chain_invalid_threads": chain_invalid},
        "resolution_outcomes": {"state_counts": dict(sorted(state_counts.items())), "provisional_threads": int(state_counts.get("PROVISIONALLY_RESOLVED", 0)), "confirmed_threads": int(state_counts.get("RESOLVED_CONFIRMED", 0)), "reopened_ever_threads": reopened, "trusted_resolution": {"true": trusted, "unknown_or_untrusted": max(0, int(state_counts.get("RESOLVED_CONFIRMED", 0)) - trusted), "user_confirmation_does_not_accept_eocl_run": True}, "administrative_disposition_is_not_resolution": True},
        "time_to_provisional": _metric(provisional_values, provisional_missing, definition="attested_problem_open_to_deterministic_provisional_resolution", censored=censored + competing),
        "time_to_confirmed_resolution": _metric(confirmed_values, confirmed_missing, definition="attested_problem_open_to_authoritative_confirmation; true resolution may be interval-censored", censored=censored + competing),
        "time_to_administrative_disposition": _metric(administrative_values, administrative_missing, definition="attested_problem_open_to_block_or_abandon; never counted as success", censored=censored),
        "ttpr_wall_ms": _metric(provisional_values, provisional_missing, definition="alias_of_time_to_provisional; only attested occurrence clocks", censored=censored + competing),
        "restricted_ttpr_ms": {"definition": "union_of_active_stage_intervals_only_when_all_primary segments_share_one clock domain", "active_stages": sorted(_ACTIVE_STAGES), "observed_threads": active_observed, "cross_clock_domains_are_not_summed": True},
        "mechanics_coverage": {"exact_revision_binding_events": exact_links, "full_claim_waves_with_structural_manifest": coverage_complete, "outcome_observation_requires_authoritative_transition": True, "legacy_schema_events_policy_ineligible": True},
        "policy": {"read_only_immutable_snapshot_required": True, "no_writer_or_schema_mutation": True, "no_raw_prompt_response_or_transcript": True, "no_timestamp_proximity_link": True, "no_historical_causal_backfill": True, "silence_is_censored": True, "administrative_disposition_not_success": True, "automatic_policy_promotion": False},
    }
