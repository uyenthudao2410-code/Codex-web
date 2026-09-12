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


STAGE_LATENCY_SCHEMA_VERSION = 2
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
# ``turn_received`` is an exact identity/milestone.  It is not a duration span
# and therefore must not create a fake zero-duration record or a missing-time
# denominator.  ``replan`` is measured only when it is actually reached.
_MILESTONE_STAGES = ("turn_received",)
_TIMED_STAGE_VOCABULARY = tuple(stage for stage in STAGE_VOCABULARY if stage not in {*_MILESTONE_STAGES})
_BASE_REQUIRED_STAGES = tuple(stage for stage in _TIMED_STAGE_VOCABULARY if stage != "replan")
_COVERAGE_THRESHOLD = 0.90
_MIN_DECISION_COHORT = 50
_ACCEPTANCE_COMPONENT_MEASUREMENTS = frozenset({"controller_processing", "acceptance_wait"})
_SERVER_OWNED_HOST_CORRELATION_SOURCES = frozenset({
    "electron_pending_host_turn",
    "attested_chatweb_transport_trace",
})


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
        and str(marker.get("source") or "") in _SERVER_OWNED_HOST_CORRELATION_SOURCES
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
    metadata, evaluation = _metadata(run)
    marker = metadata.get("host_correlation") if isinstance(metadata.get("host_correlation"), dict) else {}
    host_source = str(marker.get("source") or "").strip()
    turn_id = str(evaluation.get("turn_id") or "").strip()
    trace_id = str(evaluation.get("trace_id") or "").strip()
    if not turn_id or not trace_id:
        return False
    if host_source == "attested_chatweb_transport_trace":
        # This marker is created only by the server from an attested ChatWeb
        # controller transport plus its validated request trace.  It is an
        # exact content-free host-to-run binding and does not require a later
        # report-visible DOM span to prove that identity.
        return marker.get("content_free") is True
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


def _span_duration(span: dict[str, Any] | None) -> float | None:
    if not isinstance(span, dict):
        return None
    value = span.get("duration_ms")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) < 0:
        return None
    return float(value)


def _primary_stage_measurement(stage: str, measurement: str) -> bool:
    if stage == "report_visible":
        return measurement == "observed_host_visible"
    return measurement == "observed_stage_duration"


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
    accepted_current_source_runs = 0
    controller_processing_durations: list[float] = []
    acceptance_wait_durations: list[float] = []
    acceptance_same_clock_eligible = 0
    acceptance_cross_clock_excluded = 0
    acceptance_anchor_missing = 0
    controller_processing_missing = 0
    acceptance_wait_missing_same_clock = 0

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
            measurement = str(span.get("measurement") or "").strip().lower()
            if stage == "acceptance" and measurement in _ACCEPTANCE_COMPONENT_MEASUREMENTS:
                continue
            if not _primary_stage_measurement(stage, measurement):
                continue
            known_stages.add(stage)
            per_stage_span_counts[stage] += 1
            clock_domain = str(span.get("clock_domain") or "").strip()
            if clock_domain:
                per_stage_domains[stage].add(clock_domain)
            duration = _span_duration(span)
            if duration is not None:
                per_stage_duration[stage].append(duration)

        expected = _expected_stages(ledger, run_id)
        for stage in expected:
            expected_by_stage[stage] += 1
            if stage in known_stages:
                recorded_by_stage[stage] += 1
        exact_binding_count += int(_exact_host_binding(run, spans))
        rows.append({"expected": expected, "recorded": known_stages})

        waves = ledger.list_waves(run_id)
        latest_wave = max(waves, key=lambda item: (int(item.get("ordinal") or 0), str(item.get("wave_id") or ""))) if waves else {}
        latest_wave_id = str(latest_wave.get("wave_id") or "")
        accepted_checkpoint = any(
            str(item.get("status") or "").lower() == "accepted"
            for item in ledger.list_checkpoints(run_id, wave_id=latest_wave_id)
        ) if latest_wave_id else False
        if accepted_checkpoint:
            accepted_current_source_runs += 1
            processing = next((
                item for item in spans
                if str(item.get("span_id") or "") == f"a2-controller-processing-v1:{latest_wave_id}"
                and str(item.get("measurement") or "").strip().lower() == "controller_processing"
            ), None)
            processing_duration = _span_duration(processing)
            if processing_duration is None:
                controller_processing_missing += 1
            else:
                controller_processing_durations.append(processing_duration)

            anchor = next((
                item for item in reversed(ledger.list_events(run_id, wave_id=latest_wave_id))
                if str(item.get("event_type") or "") == "observation_stage_anchor_recorded"
                and str((item.get("payload") or {}).get("stage") or "").strip().lower() == "acceptance"
            ), None)
            anchor_payload = anchor.get("payload") if isinstance(anchor, dict) and isinstance(anchor.get("payload"), dict) else {}
            anchor_domain = str(anchor_payload.get("clock_domain") or "").strip()
            anchor_start = anchor_payload.get("start_ms")
            processing_domain = str(processing.get("clock_domain") or "").strip() if isinstance(processing, dict) else ""
            processing_start = processing.get("start_ms") if isinstance(processing, dict) else None
            anchor_valid = (
                bool(anchor_domain)
                and not isinstance(anchor_start, bool)
                and isinstance(anchor_start, (int, float))
                and math.isfinite(float(anchor_start))
                and float(anchor_start) >= 0
            )
            processing_start_valid = (
                processing_duration is not None
                and bool(processing_domain)
                and not isinstance(processing_start, bool)
                and isinstance(processing_start, (int, float))
                and math.isfinite(float(processing_start))
                and float(processing_start) >= 0
            )
            if not anchor_valid:
                acceptance_anchor_missing += 1
            elif processing_start_valid:
                if anchor_domain != processing_domain:
                    acceptance_cross_clock_excluded += 1
                elif float(anchor_start) <= float(processing_start):
                    acceptance_same_clock_eligible += 1
                    wait = next((
                        item for item in spans
                        if str(item.get("span_id") or "") == f"a2-acceptance-wait-v1:{latest_wave_id}"
                        and str(item.get("measurement") or "").strip().lower() == "acceptance_wait"
                        and str(item.get("clock_domain") or "").strip() == processing_domain
                    ), None)
                    wait_duration = _span_duration(wait)
                    if wait_duration is None:
                        acceptance_wait_missing_same_clock += 1
                    else:
                        acceptance_wait_durations.append(wait_duration)
                else:
                    acceptance_wait_missing_same_clock += 1

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
            "method": "server_owned_attested_transport_trace_or_exact_report_visible_trace_turn",
            "timestamp_proximity_inference_forbidden": True,
        },
        "stage_completeness": {
            "duration_stage_vocabulary": list(_TIMED_STAGE_VOCABULARY),
            "milestone_vocabulary": list(_MILESTONE_STAGES),
            "expected_stage_observations": expected_total,
            "recorded_stage_observations": recorded_total,
            "coverage": stage_completeness,
            "threshold": round(float(coverage_threshold), 6),
            "stages_with_missingness_above_threshold": missing_over_threshold,
            "rows": stage_rows,
        },
        "acceptance_attribution": {
            "accepted_current_source_runs": accepted_current_source_runs,
            "controller_processing_ms": {
                "observed_runs": len(controller_processing_durations),
                "missing_runs": controller_processing_missing,
                "coverage": _ratio(len(controller_processing_durations), accepted_current_source_runs),
                "duration_ms": _duration_summary(controller_processing_durations),
            },
            "acceptance_wait_ms": {
                "same_clock_eligible_runs": acceptance_same_clock_eligible,
                "observed_runs": len(acceptance_wait_durations),
                "missing_same_clock_runs": acceptance_wait_missing_same_clock,
                "coverage": _ratio(len(acceptance_wait_durations), acceptance_same_clock_eligible),
                "duration_ms": _duration_summary(acceptance_wait_durations),
                "anchor_missing_runs": acceptance_anchor_missing,
                "cross_clock_excluded_runs": acceptance_cross_clock_excluded,
            },
            "same_clock_required": True,
            "cross_clock_subtraction_forbidden": True,
            "legacy_acceptance_span_is_nonexclusive": True,
            "missing_or_cross_clock_remains_unknown": True,
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
            "acceptance_components_require_same_clock_domain": True,
            "retry_overlap_and_dependency_not_inferred_from_duration": True,
            "missing_stage_is_not_zero_duration": True,
            "unrecognized_legacy_stage_is_not_rewritten": True,
            "no_scalar_expected_loss": True,
        },
    }
