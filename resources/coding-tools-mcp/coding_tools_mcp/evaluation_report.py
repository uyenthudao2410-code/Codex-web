from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .orchestration_ledger import OrchestrationLedger


HOST_JOURNAL_RELATIVE = Path('.coding-tools') / 'evaluation' / 'chatweb-host-observations.jsonl'
CURRENT_HOST_OBSERVATION_SCHEMA_VERSION = 5
LEGACY_HOST_OBSERVATION_SCHEMA_VERSIONS = {1, 2, 3, 4}


def _percentile(values: list[float], percentile: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, min(len(ordered), (len(ordered) * percentile + 99) // 100))
    return round(float(ordered[rank - 1]), 6)


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _count_map(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for raw_key, raw_count in value.items():
        if isinstance(raw_count, bool):
            continue
        try:
            count = max(0, int(raw_count))
        except (TypeError, ValueError):
            continue
        if count:
            result[str(raw_key)] = count
    return result


def _load_host_events(workspace: Path, *, max_events: int = 10000) -> tuple[list[dict[str, Any]], Path]:
    target = workspace / HOST_JOURNAL_RELATIVE
    files = [Path(f'{target}.1'), target]
    events: list[dict[str, Any]] = []
    for file in files:
        if not file.exists():
            continue
        try:
            lines = file.read_text(encoding='utf-8', errors='replace').splitlines()
        except OSError:
            continue
        for line in lines:
            if len(events) >= max_events:
                break
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict) and item.get('schema_version') in LEGACY_HOST_OBSERVATION_SCHEMA_VERSIONS | {CURRENT_HOST_OBSERVATION_SCHEMA_VERSION}:
                events.append(item)
        if len(events) >= max_events:
            break
    return events, target


def host_visible_summary(workspace: Path) -> dict[str, Any]:
    events, target = _load_host_events(workspace)
    current_events = [item for item in events if item.get('schema_version') == CURRENT_HOST_OBSERVATION_SCHEMA_VERSION]
    spans: list[float] = []
    for item in current_events:
        if item.get('event_type') != 'host_turn_span':
            continue
        if item.get('measurement') != 'observed_user_visible_to_first_assistant_visible':
            continue
        duration = item.get('duration_ms')
        if isinstance(duration, (int, float)) and not isinstance(duration, bool) and float(duration) >= 0:
            spans.append(float(duration))
    return {
        'status': 'observed' if spans else 'no_host_turn_spans',
        'journal_path': str(target),
        'event_count': len(current_events),
        'ignored_legacy_event_count': len(events) - len(current_events),
        'turn_span_count': len(spans),
        'measurement': 'user_turn_visible_to_first_assistant_visible',
        'measurement_source': 'electron_chatgpt_dom',
        'not_model_latency': True,
        'duration_ms': {
            'p50': _percentile(spans, 50),
            'p90': _percentile(spans, 90),
            'min': round(min(spans), 6) if spans else None,
            'max': round(max(spans), 6) if spans else None,
        },
    }


def host_binding_summary(workspace: Path, *, ledger: OrchestrationLedger | None = None) -> dict[str, Any]:
    root = workspace.resolve()
    ledger = ledger or OrchestrationLedger(root)
    events, target = _load_host_events(root)
    spans = [
        item for item in events
        if item.get('schema_version') == CURRENT_HOST_OBSERVATION_SCHEMA_VERSION
        and item.get('event_type') == 'host_turn_span'
        and item.get('measurement') == 'observed_user_visible_to_first_assistant_visible'
    ]
    bound = [
        item for item in spans
        if str(item.get('run_id') or '').strip() and str(item.get('wave_id') or '').strip()
    ]
    explicit = [
        item for item in bound
        if str(item.get('trace_id') or '').strip() and str(item.get('turn_id') or '').strip()
    ]
    exact_correlations = 0
    exact_run_ids: set[str] = set()
    for item in explicit:
        run_id = str(item.get('run_id') or '').strip()
        wave_id = str(item.get('wave_id') or '').strip()
        if ledger.get_run(run_id) is None:
            continue
        if not any(str(wave.get('wave_id') or '') == wave_id for wave in ledger.list_waves(run_id)):
            continue
        for span in ledger.list_observation_spans(run_id, limit=1000):
            if span.get('observer_plane') != 'electron_chatgpt_dom':
                continue
            if (
                str(span.get('span_id') or '').strip() == str(item.get('span_id') or '').strip()
                and str(span.get('trace_id') or '').strip() == str(item.get('trace_id') or '').strip()
                and str(span.get('turn_id') or '').strip() == str(item.get('turn_id') or '').strip()
            ):
                exact_correlations += 1
                exact_run_ids.add(run_id)
                break
    eligible_runs = ledger.host_observation_eligible_runs()
    eligible_run_ids = {str(item.get('run_id') or '') for item in eligible_runs if str(item.get('run_id') or '')}
    eligible_with_host_span = len(eligible_run_ids & exact_run_ids)
    eligible_total = len(eligible_run_ids)
    total = len(spans)
    return {
        'status': 'observed' if spans else 'no_host_turn_spans',
        'journal_path': str(target),
        'host_spans_total': total,
        'host_spans_with_run_binding': len(bound),
        'host_binding_rate': round(len(bound) / total, 6) if total else None,
        'host_spans_with_trace_turn_identity': len(explicit),
        'exact_ledger_correlations': exact_correlations,
        'exact_correlated_run_count': len(exact_run_ids),
        'eligible_runs_total': eligible_total,
        'eligible_runs_with_host_span': eligible_with_host_span,
        'eligible_run_host_coverage': round(eligible_with_host_span / eligible_total, 6) if eligible_total else None,
        'eligible_run_coverage_status': 'observed' if eligible_total else 'no_instrumented_eligible_runs',
        'eligible_run_coverage_basis': 'server_owned_host_correlation_marker_v1',
        'historical_eligible_run_coverage_status': 'not_reconstructable_without_durable_eligibility_marker',
        'historical_eligible_run_coverage_reason': (
            'pre-marker run metadata cannot distinguish an organic Electron pending-host-turn claim '
            'from caller-supplied controlled trace/turn identity'
        ),
        'timestamp_proximity_inference_forbidden': True,
    }


def current_ledger_baseline_report(workspace: Path) -> dict[str, Any]:
    root = workspace.resolve()
    ledger = OrchestrationLedger(root)
    routing_regret = ledger.paired_policy_evaluation()
    performance_path = root / '.coding-tools' / 'performance.json'
    performance = _read_json_object(performance_path)
    cumulative_counts = _count_map(performance.get('error_class_counts'))
    cumulative_samples = sum(cumulative_counts.values())
    cumulative_unknown = int(cumulative_counts.get('UNKNOWN', 0))
    current_counts = _count_map(performance.get('error_taxonomy_current_counts'))
    current_samples = sum(current_counts.values())
    current_unknown = int(current_counts.get('UNKNOWN', 0))
    current_typed = current_samples - current_unknown
    return {
        'schema_version': 1,
        'captured_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'ledger_path': str(root / '.coding-tools' / 'orchestration' / 'ledger.sqlite3'),
        'population': ledger.current_baseline_summary(),
        'organic_rework': ledger.organic_rework_summary(limit=5000),
        'routing_placement_regret': routing_regret,
        'host_visible': host_visible_summary(root),
        'host_binding': host_binding_summary(root, ledger=ledger),
        'error_taxonomy': {
            'source': str(performance_path),
            'provenance': 'supplemental_performance_projection',
            'causal_source': 'orchestration_ledger',
            'cumulative_projection': {
                'counts': cumulative_counts,
                'samples': cumulative_samples,
                'unknown_samples': cumulative_unknown,
                'typed_coverage': round((cumulative_samples - cumulative_unknown) / cumulative_samples, 6) if cumulative_samples else None,
            },
            'current_epoch': {
                'epoch': str(performance.get('error_taxonomy_epoch') or '').strip() or None,
                'counts': current_counts,
                'samples': current_samples,
                'typed_samples': current_typed,
                'unknown_samples': current_unknown,
                'typed_coverage': round(current_typed / current_samples, 6) if current_samples else None,
                'unknown_share': round(current_unknown / current_samples, 6) if current_samples else None,
                'status': 'observed' if current_samples else 'no_current_epoch_samples',
            },
            'historical_backfill': False,
            'historical_unknown_reclassification_forbidden': True,
        },
        'policy': {
            'ledger_is_causal_source': True,
            'performance_projection_is_not_causal_source': True,
            'unknown_is_not_zero': True,
            'host_latency_is_not_model_latency': True,
            'timestamp_proximity_join_forbidden': True,
            'routing_regret_requires_explicit_representative_pairs': True,
            'routing_regret_cross_task_counterfactual_forbidden': True,
        },
    }


def evaluation_plane_report(workspace: Path, *, run_id: str = '') -> dict[str, Any]:
    root = workspace.resolve()
    host = host_visible_summary(root)
    host_events, _ = _load_host_events(root)
    run_id = str(run_id or '').strip()
    if not run_id:
        causal = {
            'status': 'not_requested',
            'complete': False,
            'reasons': ['run_id_not_supplied'],
            'critical_path_ms': None,
        }
        correlation = {
            'status': 'unlinked_no_explicit_run',
            'inference_forbidden': True,
        }
    else:
        ledger = OrchestrationLedger(root)
        if ledger.get_run(run_id) is None:
            raise ValueError('run_id was not found in orchestration ledger')
        causal = ledger.critical_path_analysis(run_id)
        spans = ledger.list_observation_spans(run_id, limit=1000)
        journal_host_spans = [
            item for item in host_events
            if item.get('schema_version') == CURRENT_HOST_OBSERVATION_SCHEMA_VERSION
            and item.get('event_type') == 'host_turn_span'
            and item.get('measurement') == 'observed_user_visible_to_first_assistant_visible'
            and str(item.get('run_id') or '').strip() == run_id
            and str(item.get('trace_id') or '').strip()
            and str(item.get('turn_id') or '').strip()
        ]
        explicitly_correlated_host = []
        for item in spans:
            if item.get('observer_plane') != 'electron_chatgpt_dom':
                continue
            trace_id = str(item.get('trace_id') or '').strip()
            turn_id = str(item.get('turn_id') or '').strip()
            if not trace_id or not turn_id:
                continue
            if any(
                str(host_span.get('trace_id') or '').strip() == trace_id
                and str(host_span.get('turn_id') or '').strip() == turn_id
                and str(host_span.get('span_id') or '').strip() == str(item.get('span_id') or '').strip()
                for host_span in journal_host_spans
            ):
                explicitly_correlated_host.append(item)
        correlation = {
            'status': 'explicit_host_run_identity_present' if explicitly_correlated_host else 'unlinked_no_stable_turn_to_run_identity',
            'explicit_host_span_count': len(explicitly_correlated_host),
            'journal_explicit_candidate_count': len(journal_host_spans),
            'inference_forbidden': not bool(explicitly_correlated_host),
        }
    return {
        'schema_version': 1,
        'north_star': 'quality_floor_then_total_cost_and_time_to_accepted_result',
        'host_visible': host,
        'causal_run': causal,
        'host_to_run_correlation': correlation,
        'policy': {
            'never_treat_inter_tool_wait_as_model_latency': True,
            'never_join_clock_domains_by_timestamp_proximity': True,
            'unknown_is_not_zero': True,
        },
    }
