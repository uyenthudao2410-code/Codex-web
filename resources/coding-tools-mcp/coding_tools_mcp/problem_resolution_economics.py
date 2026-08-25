"""Read-only, revision-scoped PRL v11 measurement over one immutable snapshot.

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
from .problem_lineage import PROBLEM_EVENT_SCHEMA_CURRENT, PROBLEM_SCHEMA_VERSION, problem_event_hash_material


PROBLEM_RESOLUTION_ECONOMICS_SCHEMA_VERSION = 2
_ACTIVE_STAGES = frozenset({"preflight", "localization", "routing", "execution", "replan", "proof", "acceptance"})
_ADMINISTRATIVE_RELATIONS = frozenset({"BLOCK", "ABANDON"})


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

    def __init__(self, *, schema_version: int, threads: list[dict[str, Any]], revisions: list[dict[str, Any]], events: list[dict[str, Any]], fact_load_statements: int) -> None:
        self.schema_version = schema_version
        self.threads = threads
        self.revisions = revisions
        self.events = events
        self.fact_load_statements = fact_load_statements
        self._events_by_problem: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._events_by_revision: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
        self._revisions_by_problem: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in events:
            problem_id = _text(event.get("problem_id"))
            if problem_id:
                self._events_by_problem[problem_id].append(event)
            revision = event.get("problem_revision")
            if int(event.get("event_schema_version") or 1) == PROBLEM_EVENT_SCHEMA_CURRENT and problem_id and isinstance(revision, int) and not isinstance(revision, bool) and revision > 0:
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
        return list(self._events_by_problem.get(problem_id, ()))

    def events_for_revision(self, problem_id: str, revision: int) -> list[dict[str, Any]]:
        return list(self._events_by_revision.get((problem_id, revision), ()))

    def revisions_for_problem(self, problem_id: str) -> list[dict[str, Any]]:
        return list(self._revisions_by_problem.get(problem_id, ()))

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
    return int(event.get("event_schema_version") or 1) == PROBLEM_EVENT_SCHEMA_CURRENT and bool(event.get("eligible_for_policy"))


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


def _primary_runs(ledger: LedgerFacts, problem_id: str, revision: int, events: list[dict[str, Any]]) -> set[str]:
    candidates = {
        _text(event.get("run_id")) for event in events
        if _current_eligible(event) and _text(event.get("link_status")) == "EXACT" and _text(event.get("link_role")) == "PRIMARY"
        and _text(event.get("relation_type")) in {"LINK", "ENGINEERING_ATTEMPT_BOUND"} and _text(event.get("run_id"))
    }
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


def problem_resolution_economics_report(ledger: LedgerFacts, problems: ProblemLineageFacts) -> dict[str, Any]:
    if not isinstance(ledger, LedgerFacts) or not isinstance(problems, ProblemLineageFacts):
        raise TypeError("problem-resolution economics requires immutable LedgerFacts and ProblemLineageFacts")
    if problems.schema_version != PROBLEM_SCHEMA_VERSION:
        return {"schema_version": PROBLEM_RESOLUTION_ECONOMICS_SCHEMA_VERSION, "status": "PRL_SCHEMA_INACTIVE", "observed_schema_version": problems.schema_version, "policy": {"no_writer": True, "no_historical_backfill": True, "unknown_is_not_zero": True}}

    values: dict[str, list[float]] = {"provisional": [], "confirmed": [], "administrative": [], "interval_width": [], "active": []}
    missing: dict[str, Counter[str]] = {key: Counter() for key in values}
    censored: Counter[str] = Counter(); competing: Counter[str] = Counter(); revision_outcomes = Counter()
    intervals: list[dict[str, float]] = []; wall_intervals: list[dict[str, float]] = []
    chain_invalid = exact_links = coverage_complete = 0
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
            continue
        start, start_reason = _revision_start_event(revision, events)
        provisional, confirmed = _first_relation(events, "PROVISIONAL_RESOLUTION"), _first_relation(events, "CONFIRMED_RESOLUTION")
        disposition = _administrative_disposition(revision, events, problems.revisions_for_problem(problem_id), problems)
        for key, target in (("provisional", provisional), ("confirmed", confirmed), ("administrative", disposition)):
            outcome, duration, reason = _classify_duration(start, target, disposition if key != "administrative" else None)
            if outcome == "observed": values[key].append(float(duration))
            elif outcome == "censored": censored[key] += 1
            elif outcome == "competing": competing[key] += 1
            else: missing[key][reason or start_reason or "unknown"] += 1
        if provisional is not None: revision_outcomes["technical_full_pass_observed"] += 1
        if confirmed is not None: revision_outcomes["authoritative_confirmation_observed"] += 1
        if provisional is not None and confirmed is not None: revision_outcomes["trusted_resolution_observed"] += 1
        if disposition is not None: revision_outcomes["administrative_disposition_observed"] += 1
        if confirmed is not None:
            contradictory = max((int(event.get("seq") or 0) for event in events if _current_eligible(event) and _text(event.get("relation_type")) in {"REOPEN", "BLOCK", "ABANDON"} and int(event.get("seq") or 0) < int(confirmed.get("seq") or 0)), default=-1)
            candidates = [event for event in events if _current_eligible(event) and _text(event.get("relation_type")) == "PROVISIONAL_RESOLUTION" and contradictory < int(event.get("seq") or 0) < int(confirmed.get("seq") or 0)]
            lower = candidates[-1] if candidates else None
            outcome, width, reason = _classify_duration(lower, confirmed, disposition)
            if outcome == "observed":
                values["interval_width"].append(float(width))
                lower_from_start, _ = _elapsed_ms(start or {}, lower)
                upper_from_start, _ = _elapsed_ms(start or {}, confirmed)
                if lower_from_start is not None and upper_from_start is not None:
                    intervals.append({"lower_bound_from_start_ms": lower_from_start, "upper_bound_from_start_ms": upper_from_start, "width_ms": float(width)})
                    wall_intervals.append({"lower_bound_ms": lower_from_start, "upper_bound_ms": upper_from_start, "width_ms": float(width)})
            elif outcome == "censored": censored["interval_width"] += 1
            elif outcome == "competing": competing["interval_width"] += 1
            else: missing["interval_width"][reason or "technical_full_pass_before_confirmation_missing"] += 1
        elif disposition is not None:
            competing["interval_width"] += 1
        else:
            censored["interval_width"] += 1
        run_ids = _primary_runs(ledger, problem_id, number, events)
        active, active_reason = _restricted_active_ms(ledger, run_ids)
        if active is None: missing["active"][active_reason or "unknown"] += 1
        else: values["active"].append(active)
        exact_links += sum(1 for event in events if _text(event.get("link_status")) == "EXACT")
        for run_id in run_ids:
            coverage_complete += sum(1 for wave in ledger.list_waves(run_id) if isinstance(wave.get("metadata"), dict) and isinstance(wave["metadata"].get("problem_resolution"), dict) and isinstance(wave["metadata"]["problem_resolution"].get("coverage_manifest"), dict))

    current_events = sum(1 for event in problems.events if int(event.get("event_schema_version") or 1) == PROBLEM_EVENT_SCHEMA_CURRENT)
    legacy_events, revision_count = len(problems.events) - current_events, len(problems.revisions)
    metrics = {
        "time_to_provisional": _metric(values["provisional"], missing["provisional"], metric_name="TTFP", definition="attested revision start to deterministic provisional resolution", eligible=revision_count, censored=censored["provisional"], competing=competing["provisional"]),
        "time_to_confirmed_resolution": _metric(values["confirmed"], missing["confirmed"], metric_name="TTOC", definition="attested revision start to authoritative confirmation; not exact real-world resolution", eligible=revision_count, censored=censored["confirmed"], competing=competing["confirmed"]),
        "time_to_administrative_disposition": _metric(values["administrative"], missing["administrative"], metric_name="ADMINISTRATIVE_DISPOSITION", definition="attested revision start to block, abandon, or superseded-by-revision; never success", eligible=revision_count, censored=censored["administrative"], competing=competing["administrative"]),
        "resolution_interval_width_ms": _metric(values["interval_width"], missing["interval_width"], metric_name="RESOLUTION_INTERVAL_WIDTH", definition="latest valid technical full pass to observed authoritative confirmation", eligible=revision_count, censored=censored["interval_width"], competing=competing["interval_width"]),
    }
    trusted = revision_outcomes["trusted_resolution_observed"]
    return {
        "schema_version": PROBLEM_RESOLUTION_ECONOMICS_SCHEMA_VERSION, "problem_schema_version": problems.schema_version,
        "status": "DESCRIPTIVE_ONLY" if current_events else "NO_CURRENT_PRL_EVENTS",
        "analysis_unit": {"primary": "problem_revision", "key_fields": ["problem_id", "revision"], "thread_state_is_compatibility_projection_only": True},
        "denominators": {"problem_threads": len(problems.threads), "problem_revisions": revision_count, "analysis_problem_revisions": revision_count, "problem_events": len(problems.events), "current_v11_events": current_events, "legacy_events_excluded_from_policy": legacy_events, "exact_revision_link_events": exact_links, "problem_chain_invalid_threads": chain_invalid, "right_censored_unconfirmed_revisions": censored["confirmed"], "competing_administrative_revision_dispositions": competing["confirmed"]},
        "resolution_outcomes": {"state_counts": dict(sorted(thread_states.items())), "thread_projection_state_counts": dict(sorted(thread_states.items())), "provisional_threads": int(thread_states.get("PROVISIONALLY_RESOLVED", 0)), "confirmed_threads": int(thread_states.get("RESOLVED_CONFIRMED", 0)), "reopened_ever_threads": sum(1 for thread in problems.threads if any(_text(event.get("relation_type")) == "REOPEN" for event in problems.events_for_problem(_text(thread.get("problem_id"))))), "revision_outcomes": dict(sorted(revision_outcomes.items())), "trusted_resolution": {"unit": "problem_revision", "true": trusted, "unknown_or_untrusted": max(0, revision_count - trusted), "user_confirmation_does_not_accept_eocl_run": True}, "administrative_disposition_is_not_resolution": True},
        **metrics,
        "resolution_interval": {"unit": "problem_revision", "definition": "[latest valid technical full pass before confirmation, observed confirmation]; interval-censored real-world resolution", "observed_intervals": len(values["interval_width"]), "right_censored": censored["interval_width"], "competing_disposition": competing["interval_width"], "missing_or_invalid_reason_counts": dict(sorted(missing["interval_width"].items())), "ordered_exact_intervals_ms_when_n_le_20": intervals if 0 < len(intervals) <= 20 else None, "confirmation_is_not_exact_resolution_time": True},
        "ttpr_wall_ms": {"unit": "problem_revision", "definition": "attested authoritative start to interval-censored resolution", "point_estimate_status": "UNAVAILABLE_INTERVAL_CENSORED", "observed_intervals": len(wall_intervals), "ordered_exact_intervals_ms_when_n_le_20": wall_intervals if 0 < len(wall_intervals) <= 20 else None, "point_p50": None, "point_p90": None, "same_attested_clock_authority_required": True, "confirmation_is_not_exact_resolution_time": True},
        "restricted_ttpr_ms": {"definition": "union_of_active_stage_intervals_for_exact_primary_runs_of_one_problem_revision", "unit": "problem_revision", "active_stages": sorted(_ACTIVE_STAGES), "observed_revisions": len(values["active"]), "observed_threads": len(values["active"]), "missing_reason_counts": dict(sorted(missing["active"].items())), "ordered_exact_values_ms_when_n_le_20": _ordered(values["active"]), "p50": _percentile(values["active"], 50), "p90": _percentile(values["active"], 90), "cross_clock_domains_are_not_summed": True},
        "mechanics_coverage": {"exact_revision_binding_events": exact_links, "full_claim_waves_with_structural_manifest": coverage_complete, "outcome_observation_requires_authoritative_transition": True, "legacy_schema_events_policy_ineligible": True},
        "policy": {"read_only_immutable_snapshot_required": True, "no_writer_or_schema_mutation": True, "no_raw_prompt_response_or_transcript": True, "no_timestamp_proximity_link": True, "no_historical_causal_backfill": True, "silence_is_censored": True, "administrative_disposition_not_success": True, "automatic_policy_promotion": False},
    }
