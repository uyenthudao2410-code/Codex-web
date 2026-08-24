"""Read-only PRL-D descriptive economics over one immutable v10 ledger snapshot.

Problem Resolution Lineage is a correlation and measurement plane.  This
reporter never creates a problem event, treats a user confirmation as EOCL
acceptance, infers a link from timestamps, or treats missing resource/money
coverage as zero.  It is intentionally descriptive until a natural reviewed
cohort meets the separately preregistered integrity gates.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from .ledger_analysis import LedgerFacts, LedgerReadSession
from .problem_lineage import PROBLEM_SCHEMA_VERSION, problem_event_hash_material


PROBLEM_RESOLUTION_ECONOMICS_SCHEMA_VERSION = 1
_CLOSED_STATES = frozenset({"RESOLVED_CONFIRMED", "RESOLVED_UNCONFIRMED", "SUPERSEDED", "ABANDONED"})
_ACTIVE_STAGES = frozenset({"preflight", "localization", "routing", "execution", "replan", "proof", "acceptance"})
_RESOLUTION_RELATIONS = frozenset({"PROVISIONAL_RESOLUTION", "CONFIRMED_RESOLUTION", "UNCONFIRMED_RESOLUTION"})


def _parse_utc(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _percentile(values: list[float], percentile: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil((percentile / 100) * len(ordered)) - 1))
    return round(ordered[index], 6)


def _ordered_values(values: list[float]) -> list[float] | None:
    return [round(item, 6) for item in sorted(values)] if 0 < len(values) <= 20 else None


def _safe_text(row: dict[str, Any], key: str) -> str:
    return str(row.get(key) or "").strip()


class ProblemLineageFacts:
    """Opt-in problem-table facts read from the same immutable snapshot.

    The base ``LedgerFacts`` contract keeps its eight default bulk loads.  PRL
    facts add exactly two table loads after a schema-version read, and are never
    loaded by unrelated analysis callers.
    """

    def __init__(self, *, schema_version: int, threads: list[dict[str, Any]], events: list[dict[str, Any]], fact_load_statements: int) -> None:
        self.schema_version = schema_version
        self.threads = threads
        self.events = events
        self.fact_load_statements = fact_load_statements
        self._events_by_problem: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in events:
            problem_id = _safe_text(event, "problem_id")
            if problem_id:
                self._events_by_problem[problem_id].append(event)
        for values in self._events_by_problem.values():
            values.sort(key=lambda item: int(item.get("seq") or 0))

    @classmethod
    def load(cls, reader: LedgerReadSession) -> "ProblemLineageFacts":
        schema_row = reader.one("PRAGMA user_version")
        schema_version = int(schema_row[0] if schema_row is not None else 0)
        if schema_version != PROBLEM_SCHEMA_VERSION:
            return cls(schema_version=schema_version, threads=[], events=[], fact_load_statements=1)
        threads = [dict(row) for row in reader.rows("SELECT * FROM problem_threads ORDER BY problem_id")]
        events = [dict(row) for row in reader.rows("SELECT * FROM problem_events ORDER BY problem_id, seq")]
        return cls(schema_version=schema_version, threads=threads, events=events, fact_load_statements=3)

    def events_for_problem(self, problem_id: str) -> list[dict[str, Any]]:
        return list(self._events_by_problem.get(problem_id, ()))

    def verify_chain(self, problem_id: str) -> dict[str, Any]:
        previous = ""
        events = self.events_for_problem(problem_id)
        for event in events:
            if _safe_text(event, "prev_hash") != previous:
                return {"ok": False, "reason": "prev_hash_mismatch"}
            material = problem_event_hash_material(
                event,
                state_before=_safe_text(event, "state_before"),
                state_after=_safe_text(event, "state_after"),
                prev_hash=previous,
            )
            expected = hashlib.sha256(
                json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            if expected != _safe_text(event, "event_hash"):
                return {"ok": False, "reason": "event_hash_mismatch"}
            previous = expected
        return {"ok": True, "event_count": len(events)}


def _primary_and_secondary_run_ids(events: list[dict[str, Any]]) -> tuple[set[str], set[str]]:
    primary: set[str] = set()
    secondary: set[str] = set()
    for event in events:
        if _safe_text(event, "link_status") != "EXACT":
            continue
        run_id = _safe_text(event, "run_id")
        if not run_id:
            continue
        if _safe_text(event, "link_role") == "PRIMARY":
            primary.add(run_id)
        elif _safe_text(event, "link_role") == "SECONDARY":
            secondary.add(run_id)
    return primary, secondary - primary


def _final_resolution_event(events: list[dict[str, Any]], state: str) -> dict[str, Any] | None:
    if state not in _CLOSED_STATES:
        return None
    matching = [event for event in events if _safe_text(event, "state_after") == state]
    return matching[-1] if matching else None


def _host_open_event(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        event for event in events
        if _safe_text(event, "provenance") == "HOST_OBSERVED"
        and _safe_text(event, "turn_id")
        and _safe_text(event, "trace_id")
        and _parse_utc(event.get("event_time")) is not None
    ]
    return min(candidates, key=lambda item: _parse_utc(item.get("event_time")) or datetime.max.replace(tzinfo=None)) if candidates else None


def _wall_ttpr_ms(events: list[dict[str, Any]], state: str) -> tuple[float | None, str | None]:
    start = _host_open_event(events)
    finish = _final_resolution_event(events, state)
    if start is None:
        return None, "host_visible_problem_start_missing"
    if finish is None:
        return None, "right_censored_unresolved_or_no_final_resolution"
    start_time = _parse_utc(start.get("event_time"))
    finish_time = _parse_utc(finish.get("event_time"))
    if start_time is None or finish_time is None:
        return None, "utc_event_time_missing_or_invalid"
    value = (finish_time - start_time).total_seconds() * 1000
    if value < 0:
        return None, "utc_clock_anomaly"
    return round(value, 6), None


def _merge_intervals(intervals: list[tuple[float, float]]) -> float:
    merged: list[list[float]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return round(sum(end - start for start, end in merged), 6)


def _restricted_ttpr(ledger: LedgerFacts, primary_run_ids: set[str]) -> tuple[float | None, str | None]:
    intervals_by_domain: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for run_id in primary_run_ids:
        for span in ledger.list_observation_spans(run_id, limit=1000):
            if _safe_text(span, "stage").lower() not in _ACTIVE_STAGES:
                continue
            domain = _safe_text(span, "clock_domain")
            start = span.get("start_ms")
            end = span.get("end_ms")
            if not domain or isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
                continue
            if not math.isfinite(float(start)) or not math.isfinite(float(end)) or float(end) < float(start):
                continue
            intervals_by_domain[domain].append((float(start), float(end)))
    if not intervals_by_domain:
        return None, "same_domain_active_segments_missing"
    if len(intervals_by_domain) != 1:
        return None, "multiple_clock_domains_not_summed"
    return _merge_intervals(next(iter(intervals_by_domain.values()))), None


def _run_economics(ledger: LedgerFacts, run_ids: set[str]) -> list[dict[str, Any]]:
    return [ledger.accepted_result_economics(run_id) for run_id in sorted(run_ids) if ledger.get_run(run_id) is not None]


def _trusted_technical_resolution(thread: dict[str, Any], primary_economics: list[dict[str, Any]]) -> str:
    floor = _safe_text(thread, "engineering_floor")
    if floor == "NOT_APPLICABLE":
        return "NOT_APPLICABLE"
    if not primary_economics:
        return "UNKNOWN"
    for economics in primary_economics:
        proof = economics.get("proof") if isinstance(economics.get("proof"), dict) else {}
        if economics.get("accepted") is True and int(proof.get("passed") or 0) > 0:
            return "TRUE"
    return "FALSE" if floor == "REQUIRED" else "UNKNOWN"


def _first_response_resolution(events: list[dict[str, Any]], state: str) -> bool:
    if state != "RESOLVED_CONFIRMED":
        return False
    first_resolution = next(
        (
            event for event in events
            if _safe_text(event, "relation_type") in _RESOLUTION_RELATIONS
            or _safe_text(event, "state_after") in {"PROVISIONALLY_RESOLVED", "RESOLVED_CONFIRMED"}
        ),
        None,
    )
    if first_resolution is None:
        return False
    resolution_seq = int(first_resolution.get("seq") or 0)
    correction_before = any(
        int(event.get("seq") or 0) < resolution_seq
        and (
            _safe_text(event, "state_after") == "REOPENED"
            or _safe_text(event, "economic_class") == "AVOIDABLE_CORRECTION"
        )
        for event in events
    )
    return not correction_before


def problem_resolution_economics_report(ledger: LedgerFacts, problems: ProblemLineageFacts) -> dict[str, Any]:
    """Project PRL-D descriptive counts without producing a causal treatment claim."""
    if not isinstance(ledger, LedgerFacts):
        raise TypeError("problem-resolution economics requires immutable LedgerFacts")
    if not isinstance(problems, ProblemLineageFacts):
        raise TypeError("problem-resolution economics requires immutable ProblemLineageFacts")
    if problems.schema_version != PROBLEM_SCHEMA_VERSION:
        return {
            "schema_version": PROBLEM_RESOLUTION_ECONOMICS_SCHEMA_VERSION,
            "status": "PRL_SCHEMA_INACTIVE",
            "observed_schema_version": problems.schema_version,
            "policy": {"no_writer": True, "no_historical_backfill": True, "unknown_is_not_zero": True},
        }

    link_status_counts = Counter(_safe_text(event, "link_status") or "UNKNOWN" for event in problems.events)
    thread_state_counts = Counter(_safe_text(thread, "resolution_state") or "UNKNOWN" for thread in problems.threads)
    economic_class_counts = Counter(_safe_text(event, "economic_class") or "UNKNOWN" for event in problems.events)
    causal_mechanism_counts = Counter(_safe_text(event, "causal_mechanism") or "UNKNOWN" for event in problems.events)
    chain_invalid = 0
    right_censored = 0
    reopened_ever = 0
    first_response_resolved = 0
    ttpr_values: list[float] = []
    ttpr_missing = Counter()
    restricted_values: list[float] = []
    restricted_missing = Counter()
    primary_runs_total = 0
    accepted_primary_before_resolution = 0
    waves_total = 0
    replans_total = 0
    proofs_total = 0
    secondary_runs_total = 0
    threads_with_secondary_allocation_missing = 0
    resource_observed_primary_runs = 0
    money_complete_primary_runs = 0
    trusted_counts = Counter()

    for thread in problems.threads:
        problem_id = _safe_text(thread, "problem_id")
        events = problems.events_for_problem(problem_id)
        if problems.verify_chain(problem_id).get("ok") is not True:
            chain_invalid += 1
        state = _safe_text(thread, "resolution_state")
        if state not in _CLOSED_STATES:
            right_censored += 1
        if any(_safe_text(event, "state_after") == "REOPENED" for event in events):
            reopened_ever += 1
        if _first_response_resolution(events, state):
            first_response_resolved += 1

        wall, wall_reason = _wall_ttpr_ms(events, state)
        if wall is None:
            ttpr_missing[wall_reason or "unknown"] += 1
        else:
            ttpr_values.append(wall)

        primary_ids, secondary_ids = _primary_and_secondary_run_ids(events)
        primary_economics = _run_economics(ledger, primary_ids)
        primary_runs_total += len(primary_ids)
        secondary_runs_total += len(secondary_ids)
        if secondary_ids:
            threads_with_secondary_allocation_missing += 1
        final = _final_resolution_event(events, state)
        final_time = _parse_utc(final.get("event_time")) if final is not None else None
        for run_id, economics in zip(sorted(primary_ids), primary_economics):
            run = ledger.get_run(run_id) or {}
            finish_time = _parse_utc(run.get("finished_at"))
            if economics.get("accepted") is True and final_time is not None and finish_time is not None and finish_time <= final_time:
                accepted_primary_before_resolution += 1
            waves = ledger.list_waves(run_id)
            waves_total += len(waves)
            replans_total += sum(1 for wave in waves if _safe_text(wave, "status") == "replanned")
            proof = economics.get("proof") if isinstance(economics.get("proof"), dict) else {}
            proofs_total += int(proof.get("records") or 0)
            provider = economics.get("provider_economics") if isinstance(economics.get("provider_economics"), dict) else {}
            if int(provider.get("usage_event_count") or 0) > 0:
                resource_observed_primary_runs += 1
            if provider.get("cost_complete") is True and provider.get("attribution_complete") is True:
                money_complete_primary_runs += 1

        restricted, restricted_reason = _restricted_ttpr(ledger, primary_ids)
        if restricted is None:
            restricted_missing[restricted_reason or "unknown"] += 1
        else:
            restricted_values.append(restricted)
        trusted_counts[_trusted_technical_resolution(thread, primary_economics)] += 1

    total_threads = len(problems.threads)
    total_events = len(problems.events)
    status = "NO_NATURAL_PROBLEM_EVENTS" if not total_events else "DESCRIPTIVE_ONLY"
    money_complete = primary_runs_total > 0 and money_complete_primary_runs == primary_runs_total and not secondary_runs_total
    return {
        "schema_version": PROBLEM_RESOLUTION_ECONOMICS_SCHEMA_VERSION,
        "problem_schema_version": problems.schema_version,
        "status": status,
        "denominators": {
            "problem_threads": total_threads,
            "problem_events": total_events,
            "exact_link_events": int(link_status_counts.get("EXACT", 0)),
            "ambiguous_link_events": int(link_status_counts.get("AMBIGUOUS", 0)),
            "unlinked_link_events": int(link_status_counts.get("UNLINKED", 0)),
            "right_censored_unresolved_threads": right_censored,
            "problem_chain_invalid_threads": chain_invalid,
        },
        "resolution_outcomes": {
            "state_counts": dict(sorted(thread_state_counts.items())),
            "confirmed_threads": int(thread_state_counts.get("RESOLVED_CONFIRMED", 0)),
            "unconfirmed_threads": int(thread_state_counts.get("RESOLVED_UNCONFIRMED", 0)),
            "reopened_ever_threads": reopened_ever,
            "first_response_confirmed_threads": first_response_resolved,
            "trusted_technical_resolution": {
                "true": int(trusted_counts.get("TRUE", 0)),
                "false": int(trusted_counts.get("FALSE", 0)),
                "unknown": int(trusted_counts.get("UNKNOWN", 0)),
                "not_applicable": int(trusted_counts.get("NOT_APPLICABLE", 0)),
                "user_confirmation_does_not_accept_eocl_run": True,
            },
        },
        "feedback_and_correction": {
            "economic_class_counts": dict(sorted(economic_class_counts.items())),
            "causal_mechanism_counts": dict(sorted(causal_mechanism_counts.items())),
            "avoidance_interpretation": "descriptive_event_labels_only; no_historical_causal_backfill",
        },
        "ttpr_wall_ms": {
            "definition": "first_exact_HOST_OBSERVED_problem_event_to_final_closed_problem_event_in_utc_wall_clock",
            "observed_terminal_threads": len(ttpr_values),
            "right_censored_threads": right_censored,
            "missing_or_invalid_reason_counts": dict(sorted(ttpr_missing.items())),
            "ordered_exact_values_ms_when_n_le_20": _ordered_values(ttpr_values),
            "p50": _percentile(ttpr_values, 50) if len(ttpr_values) >= 20 else None,
            "p90": _percentile(ttpr_values, 90) if len(ttpr_values) >= 20 else None,
            "small_n_policy": "exact_ordered_values_not_population_tail_inference",
        },
        "restricted_ttpr_ms": {
            "definition": "union_of_active_stage_intervals_only_when_all_primary_run_segments_share_one_declared_clock_domain",
            "active_stages": sorted(_ACTIVE_STAGES),
            "excluded_from_restricted_time": ["turn_received", "report_visible", "user_wait", "external_wait"],
            "observed_threads": len(restricted_values),
            "missing_reason_counts": dict(sorted(restricted_missing.items())),
            "ordered_exact_values_ms_when_n_le_20": _ordered_values(restricted_values),
            "p50": _percentile(restricted_values, 50) if len(restricted_values) >= 20 else None,
            "p90": _percentile(restricted_values, 90) if len(restricted_values) >= 20 else None,
            "cross_clock_domains_are_not_summed": True,
        },
        "execution_burden": {
            "primary_runs": primary_runs_total,
            "accepted_primary_runs_before_final_resolution": accepted_primary_before_resolution,
            "waves": waves_total,
            "replans": replans_total,
            "proof_records": proofs_total,
            "secondary_runs": secondary_runs_total,
            "threads_with_secondary_allocation_missing": threads_with_secondary_allocation_missing,
            "secondary_time_resource_cost_excluded_without_allocation_contract": True,
        },
        "resource_and_money_coverage": {
            "primary_runs": primary_runs_total,
            "primary_runs_with_observed_resource": resource_observed_primary_runs,
            "primary_resource_coverage": _ratio(resource_observed_primary_runs, primary_runs_total),
            "primary_runs_with_complete_measured_money": money_complete_primary_runs,
            "primary_money_coverage": _ratio(money_complete_primary_runs, primary_runs_total),
            "monetary_scalar_status": "AVAILABLE" if money_complete else "UNKNOWN",
            "missing_money_is_zero": False,
            "secondary_allocation_complete": secondary_runs_total == 0,
        },
        "policy": {
            "read_only_immutable_snapshot_required": True,
            "no_writer_or_schema_mutation": True,
            "no_raw_prompt_response_or_transcript": True,
            "no_timestamp_proximity_link": True,
            "no_historical_causal_backfill": True,
            "unresolved_threads_right_censored": True,
            "accepted_only_tail_as_population_effect_forbidden": True,
            "no_scalar_expected_loss": True,
            "automatic_policy_promotion": False,
        },
    }
