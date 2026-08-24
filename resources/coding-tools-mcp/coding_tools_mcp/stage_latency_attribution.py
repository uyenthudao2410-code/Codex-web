"""Read-only A2 stage-level latency attribution over one ``LedgerFacts`` snapshot.

This module deliberately does not create spans, infer host links from time, or
open a writer connection.  It measures the coverage and duration evidence that
has actually been recorded by the canonical ledger.  A host-visible span is a
``report_visible`` stage; it remains host-visible timing, never model latency.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from .ledger_analysis import LedgerFacts


STAGE_LATENCY_SCHEMA_VERSION = 1
STAGE_VOCABULARY = (
    "turn_received",
    "preflight",
    "localization",
    "routing",
    "execution",
    "replan",
    "proof",
    "acceptance",
    "report_visible",
)
_BASE_REQUIRED_STAGES = tuple(stage for stage in STAGE_VOCABULARY if stage != "replan")
_COVERAGE_THRESHOLD = 0.90
_MIN_DECISION_COHORT = 50


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _percentile(values: list[float], percentile: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil((percentile / 100) * len(ordered)) - 1))
    return round(ordered[index], 6)


def _metadata(value: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    metadata = value.get("metadata") if isinstance(value.get("metadata"), dict) else {}
    evaluation = metadata.get("evaluation") if isinstance(metadata.get("evaluation"), dict) else {}
    return metadata, evaluation


def _host_eligible(run: dict[str, Any]) -> bool:
    metadata, _ = _metadata(run)
    marker = metadata.get("host_correlation") if isinstance(metadata.get("host_correlation"), dict) else {}
    return (
        marker.get("schema_version") == 1
        and str(marker.get("source") or "") == "electron_pending_host_turn"
        and marker.get("eligible") is True
    )


def _latest_wave_matches_source(ledger: LedgerFacts, run_id: str, source_head: str) -> bool:
    waves = ledger.list_waves(run_id)
    if not source_head or not waves:
        return False
    latest = max(waves, key=lambda item: (int(item.get("ordinal") or 0), str(item.get("wave_id") or "")))
    return str(latest.get("base_head") or "").strip().lower() == source_head.lower()


def _expected_stages(ledger: LedgerFacts, run_id: str) -> tuple[str, ...]:
    events = ledger.list_events(run_id)
    waves = ledger.list_waves(run_id)
    replan_observed = any(str(event.get("state_after") or "") == "REPLAN" for event in events) or any(
        str(wave.get("status") or "") == "replanned" for wave in waves
    )
    return _BASE_REQUIRED_STAGES + (("replan",) if replan_observed else ())


def _exact_host_binding(run: dict[str, Any], spans: list[dict[str, Any]]) -> bool:
    """Return only an exact ledger-to-ledger identity match.

    The host journal is intentionally not re-read here.  This reporter is a
    one-snapshot canonical-ledger projection; journal-to-ledger reconciliation
    remains the separate host-binding evidence report.
    """
    if not _host_eligible(run):
        return False
    _, evaluation = _metadata(run)
    turn_id = str(evaluation.get("turn_id") or "").strip()
    trace_id = str(evaluation.get("trace_id") or "").strip()
    if not turn_id or not trace_id:
        return False
    return any(
        str(span.get("stage") or "") == "report_visible"
        and str(span.get("turn_id") or "").strip() == turn_id
        and str(span.get("trace_id") or "").strip() == trace_id
        for span in spans
    )


def _duration_summary(values: list[float]) -> dict[str, Any]:
    return {
        "observed_span_count": len(values),
        "p50": _percentile(values, 50),
        "p90": _percentile(values, 90),
        "max": round(max(values), 6) if values else None,
    }


def stage_latency_attribution_report(
    ledger: LedgerFacts,
    *,
    source_head: str = "",
    min_decision_cohort: int = _MIN_DECISION_COHORT,
    coverage_threshold: float = _COVERAGE_THRESHOLD,
) -> dict[str, Any]:
    """Return descriptive A2 coverage on one preloaded immutable fact view.

    ``source_head`` is deliberately explicit.  Empty source identity means the
    report may describe all observed host-eligible records, but cannot call
    any of them current-source evidence.  The reporter never derives a span
    from timestamps, fills missing stages with zero, or sums durations across
    clock domains.
    """
    if not isinstance(ledger, LedgerFacts):
        raise TypeError("stage latency attribution requires immutable LedgerFacts")
    if not math.isfinite(float(coverage_threshold)) or not 0 < float(coverage_threshold) <= 1:
        raise ValueError("coverage_threshold must be in (0, 1]")
    min_cohort = max(1, int(min_decision_cohort))
    normalized_head = str(source_head or "").strip().lower()

    all_host_eligible = 0
    current_source_candidates: list[dict[str, Any]] = []
    unrecognized_span_count = 0
    total_span_count = 0
    per_stage_duration: dict[str, list[float]] = defaultdict(list)
    per_stage_domains: dict[str, set[str]] = defaultdict(set)
    per_stage_span_counts: dict[str, int] = defaultdict(int)
    rows: list[dict[str, Any]] = []

    for run in ledger.list_runs(limit=5000):
        run_id = str(run.get("run_id") or "").strip()
        if not run_id or not _host_eligible(run):
            continue
        all_host_eligible += 1
        if normalized_head and _latest_wave_matches_source(ledger, run_id, normalized_head):
            current_source_candidates.append(run)

    cohort = current_source_candidates if normalized_head else []
    expected_by_stage: dict[str, int] = defaultdict(int)
    recorded_by_stage: dict[str, int] = defaultdict(int)
    exact_binding_count = 0

    for run in cohort:
        run_id = str(run.get("run_id") or "")
        spans = ledger.list_observation_spans(run_id, limit=1000)
        known_stages: set[str] = set()
        for span in spans:
            total_span_count += 1
            stage = str(span.get("stage") or "").strip().lower()
            if stage not in STAGE_VOCABULARY:
                unrecognized_span_count += 1
                continue
            known_stages.add(stage)
            per_stage_span_counts[stage] += 1
            clock_domain = str(span.get("clock_domain") or "").strip()
            if clock_domain:
                per_stage_domains[stage].add(clock_domain)
            duration = span.get("duration_ms")
            if isinstance(duration, (int, float)) and not isinstance(duration, bool) and math.isfinite(float(duration)) and float(duration) >= 0:
                per_stage_duration[stage].append(float(duration))

        expected = _expected_stages(ledger, run_id)
        for stage in expected:
            expected_by_stage[stage] += 1
            if stage in known_stages:
                recorded_by_stage[stage] += 1
        exact_binding_count += int(_exact_host_binding(run, spans))
        rows.append({"expected": expected, "recorded": known_stages})

    stage_rows: list[dict[str, Any]] = []
    missing_over_threshold: list[str] = []
    expected_total = 0
    recorded_total = 0
    for stage in STAGE_VOCABULARY:
        expected = int(expected_by_stage.get(stage, 0))
        recorded = int(recorded_by_stage.get(stage, 0))
        missing = max(0, expected - recorded)
        missingness = _ratio(missing, expected)
        if expected:
            expected_total += expected
            recorded_total += recorded
        if missingness is not None and missingness > 1 - float(coverage_threshold):
            missing_over_threshold.append(stage)
        stage_rows.append({
            "stage": stage,
            "expected_runs": expected,
            "recorded_runs": recorded,
            "missing_runs": missing,
            "coverage": _ratio(recorded, expected),
            "missingness": missingness,
            "span_records": int(per_stage_span_counts.get(stage, 0)),
            "clock_domain_count": len(per_stage_domains.get(stage, set())),
            "duration_ms": _duration_summary(per_stage_duration.get(stage, [])),
            "duration_semantics": "within_each_declared_clock_domain_only; nonexclusive_per_stage_observations",
        })

    binding_coverage = _ratio(exact_binding_count, len(cohort))
    stage_completeness = _ratio(recorded_total, expected_total)
    if not normalized_head:
        status = "NO_CURRENT_SOURCE_IDENTITY"
    elif len(cohort) < min_cohort:
        status = "INSUFFICIENT_CURRENT_SOURCE_VOLUME"
    elif binding_coverage is None or binding_coverage < float(coverage_threshold):
        status = "HOST_BINDING_COVERAGE_BELOW_THRESHOLD"
    elif stage_completeness is None or stage_completeness < float(coverage_threshold) or missing_over_threshold:
        status = "STAGE_COMPLETENESS_BELOW_THRESHOLD"
    else:
        status = "MEASUREMENT_COVERAGE_READY"

    rankable = status == "MEASUREMENT_COVERAGE_READY"
    ranked = sorted(
        [
            {
                "stage": row["stage"],
                "affected_runs": row["recorded_runs"],
                "p90_duration_ms": row["duration_ms"]["p90"],
            }
            for row in stage_rows
            if row["recorded_runs"] and row["duration_ms"]["p90"] is not None
        ],
        key=lambda item: (-int(item["affected_runs"]), -float(item["p90_duration_ms"]), str(item["stage"])),
    ) if rankable else []

    return {
        "schema_version": STAGE_LATENCY_SCHEMA_VERSION,
        "status": status,
        "source_identity": {
            "source_head": normalized_head or None,
            "current_source_identity_explicit": bool(normalized_head),
            "matching_latest_wave_required": True,
        },
        "cohort": {
            "host_eligible_observed_runs": all_host_eligible,
            "current_source_eligible_runs": len(cohort),
            "minimum_decision_cohort": min_cohort,
            "natural_workload_required": True,
            "synthetic_workload_created": False,
        },
        "host_to_run_binding": {
            "exact_ledger_binding_runs": exact_binding_count,
            "coverage": binding_coverage,
            "threshold": round(float(coverage_threshold), 6),
            "method": "exact_turn_id_and_trace_id_against_report_visible_span",
            "timestamp_proximity_inference_forbidden": True,
        },
        "stage_completeness": {
            "expected_stage_observations": expected_total,
            "recorded_stage_observations": recorded_total,
            "coverage": stage_completeness,
            "threshold": round(float(coverage_threshold), 6),
            "stages_with_missingness_above_threshold": missing_over_threshold,
            "rows": stage_rows,
        },
        "unrecognized_span_records": unrecognized_span_count,
        "considered_span_records": total_span_count,
        "tail_mechanism_ranking": {
            "status": "DESCRIPTIVE_RANKING_READY" if rankable else "INSUFFICIENT_COVERAGE_FOR_INTERVENTION_RANKING",
            "rows": ranked[:3],
            "intervention_requires_frequency_excess_delay_and_affected_result_rate": True,
        },
        "policy": {
            "ledger_is_canonical_causal_source": True,
            "uses_one_immutable_ledger_facts_snapshot": True,
            "host_visible_latency_is_not_model_latency": True,
            "cross_clock_timestamp_subtraction_forbidden": True,
            "retry_overlap_and_dependency_not_inferred_from_duration": True,
            "missing_stage_is_not_zero_duration": True,
            "unrecognized_legacy_stage_is_not_rewritten": True,
            "no_scalar_expected_loss": True,
        },
    }
