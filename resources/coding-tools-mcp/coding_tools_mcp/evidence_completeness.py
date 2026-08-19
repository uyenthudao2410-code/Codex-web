from __future__ import annotations

from pathlib import Path
from typing import Any

from .orchestration_ledger import OrchestrationLedger
from .solution_economics import solution_shadow_run_report


CURRENT_HOST_OBSERVATION_SCHEMA_VERSION = 5


def _exact_host_run_correlation(
    ledger: OrchestrationLedger,
    host_events: list[dict[str, Any]],
    run_id: str,
) -> dict[str, Any]:
    spans = ledger.list_observation_spans(run_id, limit=1000)
    candidates = [
        item for item in host_events
        if item.get('schema_version') == CURRENT_HOST_OBSERVATION_SCHEMA_VERSION
        and item.get('event_type') == 'host_turn_span'
        and item.get('measurement') == 'observed_user_visible_to_first_assistant_visible'
        and str(item.get('run_id') or '').strip() == run_id
        and str(item.get('trace_id') or '').strip()
        and str(item.get('turn_id') or '').strip()
    ]
    exact = []
    for span in spans:
        if span.get('observer_plane') != 'electron_chatgpt_dom':
            continue
        trace_id = str(span.get('trace_id') or '').strip()
        turn_id = str(span.get('turn_id') or '').strip()
        if not trace_id or not turn_id:
            continue
        if any(
            str(item.get('span_id') or '').strip() == str(span.get('span_id') or '').strip()
            and str(item.get('trace_id') or '').strip() == trace_id
            and str(item.get('turn_id') or '').strip() == turn_id
            for item in candidates
        ):
            exact.append(span)
    return {
        'status': 'PASS' if exact else 'MISSING',
        'exact_span_count': len(exact),
        'journal_candidate_count': len(candidates),
        'inference_forbidden': not bool(exact),
    }


def _workspace_identity_evidence(
    run: dict[str, Any],
    proofs: list[dict[str, Any]],
    checkpoints: list[dict[str, Any]],
) -> dict[str, Any]:
    metadata = run.get('metadata') if isinstance(run.get('metadata'), dict) else {}
    identity = metadata.get('workspace_identity') if isinstance(metadata.get('workspace_identity'), dict) else {}
    root_id = str(identity.get('root_id') or '').strip()
    workspace_id = str(identity.get('workspace_id') or '').strip()
    session_workspace_id = str(identity.get('session_workspace_id') or '').strip()
    scope_matches = identity.get('scope_matches_session_workspace')
    ids_complete = bool(root_id and workspace_id and session_workspace_id)
    ids_coherent = bool(ids_complete and root_id == workspace_id == session_workspace_id and scope_matches is True)
    mismatch = bool(ids_complete and not ids_coherent) or scope_matches is False
    checked_artifacts = 0
    mismatch_artifacts = 0
    for item in [*proofs, *checkpoints]:
        item_metadata = item.get('metadata') if isinstance(item.get('metadata'), dict) else {}
        observed = item_metadata.get('workspace_identity') if isinstance(item_metadata.get('workspace_identity'), dict) else {}
        if not observed:
            continue
        checked_artifacts += 1
        observed_root = str(observed.get('root_id') or '').strip()
        observed_workspace = str(observed.get('workspace_id') or '').strip()
        if (
            (root_id and observed_root and observed_root != root_id)
            or (workspace_id and observed_workspace and observed_workspace != workspace_id)
            or observed.get('scope_matches_session_workspace') is False
        ):
            mismatch = True
            mismatch_artifacts += 1
    instrumented = str(metadata.get('measurement_integrity_epoch') or '') == 'workspace_identity_v1'
    contamination = 'YES' if mismatch else 'NO' if instrumented and ids_coherent else 'UNKNOWN'
    return {
        'status': 'PASS' if ids_coherent and not mismatch else 'FAIL',
        'cross_project_contaminated': contamination,
        'instrumented': instrumented,
        'checked_identity_artifacts': checked_artifacts,
        'mismatched_identity_artifacts': mismatch_artifacts,
        'content_free': True,
    }


def evidence_completeness_run_report(
    workspace: Path,
    run_id: str,
    *,
    ledger: OrchestrationLedger | None = None,
    host_events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    root = workspace.resolve()
    ledger = ledger or OrchestrationLedger(root)
    run_id = str(run_id or '').strip()
    run = ledger.get_run(run_id)
    if run is None:
        return {'schema_version': 1, 'run_id': run_id, 'status': 'missing', 'promotion_eligible': 'NO'}

    events = ledger.list_events(run_id)
    proofs = ledger.list_proofs(run_id)
    checkpoints = ledger.list_checkpoints(run_id)
    economics = ledger.accepted_result_economics(run_id)
    evaluation = ledger.accepted_result_evaluation(run_id)
    shadow = solution_shadow_run_report(ledger, run_id)
    host = _exact_host_run_correlation(ledger, host_events or [], run_id)
    workspace_identity = _workspace_identity_evidence(run, proofs, checkpoints)
    metadata = run.get('metadata') if isinstance(run.get('metadata'), dict) else {}
    evaluation_metadata = metadata.get('evaluation') if isinstance(metadata.get('evaluation'), dict) else {}
    provenance = str(evaluation_metadata.get('provenance') or 'unlabeled').lower()
    workflow = str(metadata.get('workflow') or '').lower()
    terminal = str(run.get('status') or '').lower() != 'active'

    shadow_status = 'PASS' if shadow.get('status') == 'observed' else 'MISSING'
    pre_mutation = shadow.get('pre_mutation') if isinstance(shadow.get('pre_mutation'), dict) else {}
    pre_write_order = (
        'PASS' if pre_mutation.get('recorded_before_first_write') is True
        else 'FAIL' if shadow_status == 'PASS'
        else 'MISSING'
    )
    patch_events = [item for item in events if str(item.get('event_type') or '') == 'patch_surface_observed']
    patch_complete = bool(patch_events) and all(
        (item.get('payload') if isinstance(item.get('payload'), dict) else {}).get('complete') is not False
        for item in patch_events
    )
    actual_patch_surface = 'PASS' if patch_complete else 'FAIL' if patch_events else 'MISSING'
    passed_proofs = [item for item in proofs if str(item.get('status') or '') == 'passed']
    failed_or_nonpass = [item for item in proofs if str(item.get('status') or '') != 'passed']
    proof_status = 'PASS' if passed_proofs else 'FAIL' if proofs else 'MISSING'
    quality = economics.get('quality_outcome') if isinstance(economics.get('quality_outcome'), dict) else {}
    quality_status = 'PASS' if quality else 'MISSING'
    total_cost = evaluation.get('total_monetary_cost') if isinstance(evaluation.get('total_monetary_cost'), dict) else {}
    total_cost_value = total_cost.get('value')
    cost_known = bool(
        total_cost.get('complete') is True
        and isinstance(total_cost_value, (int, float))
        and not isinstance(total_cost_value, bool)
    )

    promotion_blockers = []
    if provenance != 'representative':
        promotion_blockers.append('non_representative_provenance')
    if workflow not in {'feature', 'bugfix'}:
        promotion_blockers.append('workflow_not_p4_eligible')
    if shadow_status != 'PASS':
        promotion_blockers.append('solution_shadow_missing')
    if pre_write_order != 'PASS':
        promotion_blockers.append('pre_write_order_not_proven')
    if actual_patch_surface != 'PASS':
        promotion_blockers.append('actual_patch_surface_missing_or_incomplete')
    if proof_status != 'PASS':
        promotion_blockers.append('passing_proof_missing')
    if workspace_identity['status'] != 'PASS':
        promotion_blockers.append('workspace_identity_incomplete')
    if workspace_identity['cross_project_contaminated'] != 'NO':
        promotion_blockers.append('workspace_contamination_not_ruled_out')
    if not terminal:
        promotion_blockers.append('run_not_terminal')
    promotion_eligible = not promotion_blockers

    if provenance in {'benchmark', 'synthetic'}:
        cohort = provenance
    elif promotion_eligible:
        cohort = 'representative'
    elif terminal:
        cohort = 'historical_observational'
    else:
        cohort = 'collecting'

    return {
        'schema_version': 1,
        'run_id': run_id,
        'status': 'observed',
        'workflow': workflow or None,
        'run_status': str(run.get('status') or ''),
        'workspace_identity': workspace_identity['status'],
        'host_turn_correlation': host['status'],
        'provenance': provenance,
        'solution_shadow': shadow_status,
        'pre_write_order': pre_write_order,
        'actual_patch_surface': actual_patch_surface,
        'proof': proof_status,
        'quality_outcome': quality_status,
        'cost_usage': 'KNOWN' if cost_known else 'UNKNOWN',
        'cross_project_contaminated': workspace_identity['cross_project_contaminated'],
        'promotion_eligible': 'YES' if promotion_eligible else 'NO',
        'cohort': cohort,
        'details': {
            'workspace_identity': workspace_identity,
            'host_turn_correlation': host,
            'patch_surface_event_count': len(patch_events),
            'proof_records': {'passed': len(passed_proofs), 'failed_or_nonpass': len(failed_or_nonpass)},
            'quality_source': str(quality.get('source') or '') or None,
            'cost': {
                'value': float(total_cost_value) if cost_known else None,
                'complete': bool(total_cost.get('complete')),
                'reason': total_cost.get('reason'),
            },
            'promotion_blockers': promotion_blockers,
        },
        'policy': {
            'content_free': True,
            'historical_observational_is_not_p4_predictor_validation': cohort == 'historical_observational',
            'unknown_is_not_zero': True,
            'no_retroactive_shadow_backfill': True,
        },
    }


def evidence_completeness_population_report(
    workspace: Path,
    *,
    ledger: OrchestrationLedger,
    host_events: list[dict[str, Any]],
    limit: int = 50,
) -> dict[str, Any]:
    bounded_limit = max(1, min(int(limit), 100))
    rows = [
        evidence_completeness_run_report(
            workspace,
            str(run.get('run_id') or ''),
            ledger=ledger,
            host_events=host_events,
        )
        for run in ledger.list_runs(limit=bounded_limit)
    ]
    cohort_counts: dict[str, int] = {}
    contamination_counts: dict[str, int] = {}
    for row in rows:
        cohort = str(row.get('cohort') or 'unknown')
        contamination = str(row.get('cross_project_contaminated') or 'UNKNOWN')
        cohort_counts[cohort] = cohort_counts.get(cohort, 0) + 1
        contamination_counts[contamination] = contamination_counts.get(contamination, 0) + 1
    required_coverage = {
        'workspace_identity': 'PASS',
        'host_turn_correlation': 'PASS',
        'solution_shadow': 'PASS',
        'pre_write_order': 'PASS',
        'actual_patch_surface': 'PASS',
        'proof': 'PASS',
        'quality_outcome': 'PASS',
        'cost_usage': 'KNOWN',
    }
    return {
        'schema_version': 1,
        'bounded_recent_run_count': len(rows),
        'bounded_recent_limit': bounded_limit,
        'cohort_counts': cohort_counts,
        'cross_project_contamination_counts': contamination_counts,
        'promotion_eligible_runs': sum(1 for row in rows if row.get('promotion_eligible') == 'YES'),
        'coverage': {
            field: sum(1 for row in rows if row.get(field) == required)
            for field, required in required_coverage.items()
        },
        'runs': rows,
        'policy': {
            'bounded_projection_not_historical_mutation': True,
            'historical_observational_is_not_p4_predictor_validation': True,
            'benchmark_and_synthetic_preserve_explicit_provenance': True,
            'unknown_is_not_zero': True,
        },
    }
