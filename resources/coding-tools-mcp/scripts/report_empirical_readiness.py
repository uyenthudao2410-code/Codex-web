#!/usr/bin/env python3
"""Emit a compact empirical readiness report from immutable orchestration snapshots."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
for entry in (str(SCRIPT_DIR), str(PACKAGE_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from coding_tools_mcp.cross_session_continuity_report import CrossSessionContinuityFacts  # noqa: E402
from coding_tools_mcp.ledger_access import open_existing_ledger_analysis  # noqa: E402
from coding_tools_mcp.natural_problem_cohort import (  # noqa: E402
    _exact_primary_run_ids,
    _run_natural_provenance,
    natural_problem_cohort_report,
)
from coding_tools_mcp.problem_resolution_economics import (  # noqa: E402
    ProblemLineageFacts,
    problem_resolution_economics_report,
)
from report_lifecycle_census import report as lifecycle_census_report  # noqa: E402
from report_p4_readiness import p4_readiness_report  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_STALE_AFTER_SECONDS = 24 * 60 * 60


def _unknown(reason: str, *, unit: str = "value") -> dict[str, Any]:
    return {
        "status": "UNAVAILABLE",
        "value": None,
        "unit": unit,
        "missing_reason": reason,
        "unknown_is_not_zero": True,
    }


def _revision_identity(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "problem_id": str(row.get("problem_id") or ""),
        "problem_revision": int(row.get("revision") or row.get("problem_revision") or 0),
    }


def _typed_natural_revision(ledger: Any, problems: Any, revision_row: dict[str, Any]) -> bool:
    identity = _revision_identity(revision_row)
    problem_id = identity["problem_id"]
    revision = identity["problem_revision"]
    if not problem_id or revision < 1:
        return False
    run_ids = _exact_primary_run_ids(problems.events_for_revision(problem_id, revision))
    if not run_ids:
        return False
    runs = [ledger.get_run(run_id) or {} for run_id in run_ids]
    provenance = [_run_natural_provenance(run) for run in runs]
    return bool(
        len(runs) == len(run_ids)
        and all(item.get("status") == "PASS" for item in provenance)
        and problems.verify_chain(problem_id).get("ok") is True
    )


def _current_natural_suffix_start(ledger: Any, problems: Any) -> dict[str, Any] | None:
    ordered = sorted(
        problems.revisions,
        key=lambda row: (
            int(row.get("created_event_seq") or 0),
            str(row.get("problem_id") or ""),
            int(row.get("revision") or 0),
        ),
    )
    if not ordered:
        return None
    eligible = [_typed_natural_revision(ledger, problems, row) for row in ordered]
    latest_eligible_index = next(
        (index for index in range(len(eligible) - 1, -1, -1) if eligible[index]),
        None,
    )
    if latest_eligible_index is None:
        return None
    index = latest_eligible_index
    while index > 0 and eligible[index - 1]:
        index -= 1
    return _revision_identity(ordered[index])


def _run_policy_eligible(ledger: Any, run_id: str) -> bool | None:
    run = ledger.get_run(run_id) or {}
    metadata = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
    resolution = (
        metadata.get("problem_resolution")
        if isinstance(metadata.get("problem_resolution"), dict)
        else {}
    )
    value = resolution.get("policy_eligible")
    return value if isinstance(value, bool) else None


def _full_problem_binding(
    record: dict[str, Any], problem_id: str, problem_revision: int
) -> bool:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    resolution = (
        metadata.get("problem_resolution")
        if isinstance(metadata.get("problem_resolution"), dict)
        else {}
    )
    return bool(
        resolution.get("work_origin") == "problem"
        and resolution.get("resolution_claim") == "full_problem"
        and resolution.get("problem_id") == problem_id
        and int(resolution.get("problem_revision") or 0) == problem_revision
    )


def _canonical_technical_acceptance(
    ledger: Any, problems: Any, row: dict[str, Any]
) -> bool:
    identity = _revision_identity(row)
    problem_id = identity["problem_id"]
    problem_revision = identity["problem_revision"]
    natural = row.get("natural_problem_eligibility") or {}
    exact_run_ids = set(natural.get("exact_primary_run_ids") or [])
    if not problem_id or problem_revision < 1 or not exact_run_ids:
        return False
    if problems.verify_chain(problem_id).get("ok") is not True:
        return False
    for event in problems.events_for_revision(problem_id, problem_revision):
        run_id = str(event.get("run_id") or "")
        wave_id = str(event.get("wave_id") or "")
        if not (
            event.get("eligible_for_policy") is True
            and event.get("relation_type") == "PROVISIONAL_RESOLUTION"
            and event.get("provenance") == "DETERMINISTIC_EVIDENCE"
            and event.get("evidence_level") == "OBSERVED"
            and event.get("link_status") == "EXACT"
            and event.get("link_role") == "PRIMARY"
            and event.get("state_after") == "PROVISIONALLY_RESOLVED"
            and event.get("transition_authority") in {"RUNTIME_EOCL", "RUNTIME_RECONCILIATION"}
            and run_id in exact_run_ids
            and wave_id
        ):
            continue
        run = ledger.get_run(run_id) or {}
        if str(run.get("status") or "").lower() != "accepted":
            continue
        if not _full_problem_binding(run, problem_id, problem_revision):
            continue
        wave = next(
            (item for item in ledger.list_waves(run_id) if str(item.get("wave_id") or "") == wave_id),
            None,
        )
        if not wave or str(wave.get("status") or "").lower() != "accepted":
            continue
        if not _full_problem_binding(wave, problem_id, problem_revision):
            continue
        if any(
            str(checkpoint.get("status") or "").lower() == "accepted"
            and str(checkpoint.get("wave_id") or "") == wave_id
            for checkpoint in ledger.list_checkpoints(run_id)
        ):
            return True
    return False


def _compact_natural_row(ledger: Any, problems: Any, row: dict[str, Any]) -> dict[str, Any]:
    natural = row.get("natural_problem_eligibility") or {}
    metrics = row.get("metrics") or {}
    ttpr = metrics.get("ttpr") if isinstance(metrics.get("ttpr"), dict) else {}
    resource = (
        metrics.get("resource_economics")
        if isinstance(metrics.get("resource_economics"), dict)
        else {}
    )
    trusted = (
        metrics.get("trusted_resolution")
        if isinstance(metrics.get("trusted_resolution"), dict)
        else {}
    )
    run_ids = list(natural.get("exact_primary_run_ids") or [])
    run_statuses = {
        run_id: str((ledger.get_run(run_id) or {}).get("status") or "UNKNOWN")
        for run_id in run_ids
    }
    return {
        "problem_id": row.get("problem_id"),
        "problem_revision": row.get("problem_revision"),
        "typed_natural": natural.get("eligible") is True,
        "run_ids": run_ids,
        "run_statuses": run_statuses,
        "technically_accepted": _canonical_technical_acceptance(ledger, problems, row),
        "run_policy_eligible": [_run_policy_eligible(ledger, run_id) for run_id in run_ids],
        "trusted_resolution": {
            "receipt_bound_confirmation": trusted.get("receipt_bound_confirmation"),
            "resolved_confirmed": trusted.get("resolved_confirmed"),
            "false_closure_count": trusted.get("false_closure_count"),
            "reopen_count": trusted.get("reopen_count"),
        },
        "timing": {
            "execution_ms": ttpr.get(
                "execution_ms", _unknown("execution_timing_missing", unit="millisecond")
            ),
            "proof_ms": ttpr.get(
                "proof_ms", _unknown("proof_timing_missing", unit="millisecond")
            ),
            "acceptance_ms": ttpr.get(
                "acceptance_ms", _unknown("acceptance_timing_missing", unit="millisecond")
            ),
            "replan_ms": ttpr.get(
                "replan_ms", _unknown("replan_timing_missing", unit="millisecond")
            ),
            "restricted_ttpr_active_ms": ttpr.get(
                "restricted_ttpr_active_ms",
                _unknown("restricted_ttpr_missing", unit="millisecond"),
            ),
        },
        "economics": {
            "controller_tokens": resource.get(
                "controller_tokens_exact_when_available",
                _unknown("controller_usage_missing", unit="token"),
            ),
            "provider_tokens": resource.get(
                "provider_tokens", _unknown("provider_usage_missing", unit="token")
            ),
            "monetary_cost": resource.get(
                "monetary_cost_complete_when_available",
                _unknown("cost_planes_incomplete", unit="currency_as_reported"),
            ),
            "rework": resource.get(
                "rework", _unknown("rework_usage_missing", unit="token")
            ),
            "tool_invocations": resource.get(
                "tool_invocation_count",
                _unknown("tool_invocation_receipts_missing", unit="tool_invocation"),
            ),
        },
        "governance_friction": metrics.get("governance_friction") or {},
        "usage_coverage": metrics.get("usage_coverage") or {},
    }


def _stale_subtype(record: dict[str, Any], ledger: Any) -> str:
    run_id = str(record.get("run_id") or "")
    ownership = record.get("ownership") if isinstance(record.get("ownership"), dict) else {}
    if any(value is True for value in ownership.values()):
        return "LIVE_OWNERSHIP_PRESENT"
    run = ledger.get_run(run_id) or {}
    if str(run.get("status") or "").lower() != "active":
        return "NON_ACTIVE_STATUS_CONTRADICTION"
    if ledger.list_checkpoints(run_id):
        return "CHECKPOINT_PRESENT_ACTIVE_RUN"
    latest_state = str(record.get("latest_state_after") or "").upper()
    if latest_state in {"CHECKPOINTED", "BLOCKED", "ABORTED", "STALE", "RECONCILED"}:
        return "TERMINAL_STATE_ACTIVE_RUN"
    if any(
        str(item.get("status") or "").lower() == "passed"
        for item in ledger.list_proofs(run_id)
    ):
        return "PASSED_PROOF_NO_ACCEPTED_CHECKPOINT"
    return "INACTIVE_ACTIVE_RUN_NO_TERMINAL_EVIDENCE"


def _stale_audit(
    lifecycle: dict[str, Any], ledger: Any, *, include_details: bool = False
) -> dict[str, Any]:
    candidates = [
        row
        for row in lifecycle.get("runs") or []
        if row.get("classification") == "THRESHOLD_SENSITIVE_STALE_CANDIDATE"
    ]
    over_threshold = [
        row
        for row in candidates
        if "meets_current_stale_threshold" in (row.get("reasons") or [])
    ]
    ordered = sorted(
        over_threshold,
        key=lambda row: float(row.get("activity_age_seconds") or 0.0),
        reverse=True,
    )
    audit = {
        "audit_only": True,
        "reconciliation_performed": False,
        "threshold_sensitive_candidates": len(candidates),
        "beyond_current_stale_threshold": len(over_threshold),
        "below_current_stale_threshold": len(candidates) - len(over_threshold),
        "sample_limit": 10,
        "sample": [
            {
                "run_id": row.get("run_id"),
                "activity_age_seconds": row.get("activity_age_seconds"),
                "latest_state_after": row.get("latest_state_after"),
                "subtype": _stale_subtype(row, ledger),
                "last_event": row.get("last_event"),
            }
            for row in ordered[:10]
        ],
    }
    if include_details:
        audit["details"] = [
            {
                "run_id": row.get("run_id"),
                "activity_age_seconds": row.get("activity_age_seconds"),
                "meets_current_stale_threshold": "meets_current_stale_threshold"
                in (row.get("reasons") or []),
                "latest_state_after": row.get("latest_state_after"),
                "subtype": _stale_subtype(row, ledger),
                "last_event": row.get("last_event"),
            }
            for row in sorted(
                candidates,
                key=lambda item: float(item.get("activity_age_seconds") or 0.0),
                reverse=True,
            )
        ]
    return audit


def _independent_outcome_coverage(economics: dict[str, Any]) -> dict[str, Any]:
    revision4 = (
        economics.get("revision_4_metrics")
        if isinstance(economics.get("revision_4_metrics"), dict)
        else {}
    )
    value = revision4.get("independent_outcome_evidence_coverage")
    return (
        value
        if isinstance(value, dict)
        else _unknown("independent_user_outcome_coverage_not_reported", unit="coverage")
    )


def _independent_outcome_complete(outcome: dict[str, Any]) -> bool:
    """Check the producer's coverage contract without treating unknown as complete."""
    numerator = outcome.get("numerator")
    denominator = outcome.get("denominator")
    coverage = outcome.get("coverage")
    return (
        outcome.get("status") == "AVAILABLE"
        and isinstance(numerator, int)
        and not isinstance(numerator, bool)
        and isinstance(denominator, int)
        and not isinstance(denominator, bool)
        and denominator > 0
        and numerator == denominator
        and isinstance(coverage, (int, float))
        and not isinstance(coverage, bool)
        and coverage == 1.0
    )


def _p4_compact(
    p4: dict[str, Any], cohort: dict[str, Any], outcome_coverage: dict[str, Any]
) -> dict[str, Any]:
    predictive = (
        p4.get("predictive_validation")
        if isinstance(p4.get("predictive_validation"), dict)
        else {}
    )
    git_baseline = p4.get("git_baseline") if isinstance(p4.get("git_baseline"), dict) else {}
    n5 = ((cohort.get("decision_checkpoints") or {}).get("n5") or {})
    blockers: list[str] = []
    if p4.get("p4_empirically_complete") is not True:
        blockers.append("p4_predictive_validation_incomplete")
    blockers.extend(str(item) for item in predictive.get("validation_blockers") or [])
    if p4.get("p5_baseline_ready") is not True:
        blockers.append("clean_upstream_matched_source_baseline_missing")
    if n5.get("decision") != "DESCRIPTIVE_REVIEW_REQUIRED":
        blockers.append("natural_problem_cohort_n5_incomplete")
    if int(n5.get("real_cross_session_pass_rows") or 0) < 5:
        blockers.append("five_real_cross_session_natural_rows_missing")
    if not _independent_outcome_complete(outcome_coverage):
        blockers.append("independent_user_outcome_coverage_incomplete")
    if p4.get("p5_experiment_start_ready") is not True:
        blockers.append("explicit_active_or_paused_p5_epoch_missing")
    blockers = list(dict.fromkeys(blockers))
    return {
        "state": p4.get("state"),
        "p4_empirically_complete": p4.get("p4_empirically_complete"),
        "p4_gate": p4.get("p4_gate") or {},
        "predictive_validation_status": predictive.get("status"),
        "validation_blockers": predictive.get("validation_blockers") or [],
        "git_baseline": {
            "source_worktree_clean": git_baseline.get("source_worktree_clean"),
            "upstream_configured": git_baseline.get("upstream_configured"),
            "head_matches_upstream": git_baseline.get("head_matches_upstream"),
            "p5_baseline_ready": git_baseline.get("p5_baseline_ready"),
        },
        "p5_runtime_contract": {
            "engineering_ready": p4.get("p5_experiment_engineering_ready"),
            "experiment_start_ready": p4.get("p5_experiment_start_ready"),
            "epoch_lifecycle": p4.get("p5_experiment_epoch_lifecycle"),
            "latest_epoch": p4.get("p5_latest_epoch"),
            "controlled_treatment_may_be_opened_deprecated": p4.get(
                "p5_controlled_treatment_may_be_opened"
            ),
            "automatic_policy_activation": p4.get("automatic_policy_activation"),
            "automatic_start": p4.get("p5_automatic_start"),
        },
        "operator_advisory": {
            "eligible_to_recommend_p5_open": not blockers,
            "blockers": blockers,
            "advisory_only_never_opens_epoch": True,
        },
    }


def empirical_readiness_report(
    workspace: Path,
    *,
    observed_at: float | None = None,
    stale_after_seconds: float = DEFAULT_STALE_AFTER_SECONDS,
    p4_limit: int = 100,
    start_problem_id: str = "",
    start_problem_revision: int = 1,
    stale_details: bool = False,
) -> dict[str, Any]:
    root = Path(workspace).resolve(strict=False)
    now = time.time() if observed_at is None else float(observed_at)
    lifecycle = lifecycle_census_report(
        root,
        observed_at=now,
        grace_seconds=15 * 60,
        stale_after_seconds=stale_after_seconds,
    )
    with open_existing_ledger_analysis(root) as snapshot:
        problems = ProblemLineageFacts.load(snapshot.reader)
        continuity = CrossSessionContinuityFacts.load(snapshot.reader)
        if start_problem_id:
            start = {
                "problem_id": start_problem_id,
                "problem_revision": int(start_problem_revision),
            }
            start_source = "explicit_exact_start"
        else:
            start = _current_natural_suffix_start(snapshot.ledger, problems)
            start_source = "current_contiguous_typed_natural_suffix"
        if start is None:
            cohort = {
                "schema_version": 1,
                "status": "NO_CURRENT_TYPED_NATURAL_SUFFIX",
                "cohort": {"selected_rows": 0, "typed_natural_rows": 0},
                "raw_rows": [],
                "decision_checkpoints": {},
                "missingness": {
                    "missing_is_unknown_not_zero": True,
                    "reason_counts": {"typed_natural_suffix_missing": 1},
                },
            }
        else:
            cohort = natural_problem_cohort_report(
                snapshot.ledger,
                problems,
                continuity,
                start_problem_id=start["problem_id"],
                start_problem_revision=start["problem_revision"],
                target_n=5,
            )
        economics = problem_resolution_economics_report(snapshot.ledger, problems)
        outcome_coverage = _independent_outcome_coverage(economics)
        compact_rows = [
            _compact_natural_row(snapshot.ledger, problems, row)
            for row in cohort.get("raw_rows") or []
        ]
        technically_accepted = sum(int(row["technically_accepted"]) for row in compact_rows)
        confirmed = sum(
            int((row.get("trusted_resolution") or {}).get("resolved_confirmed") is True)
            for row in compact_rows
        )
        policy_eligible_true = sum(
            1
            for row in compact_rows
            for value in row.get("run_policy_eligible") or []
            if value is True
        )
        policy_eligible_unknown = sum(
            1
            for row in compact_rows
            for value in row.get("run_policy_eligible") or []
            if value is None
        )
        p4 = p4_readiness_report(root, limit=p4_limit, ledger=snapshot.ledger)
        stale_audit = _stale_audit(
            lifecycle, snapshot.ledger, include_details=stale_details
        )
        snapshot_contract = {
            "immutable_backup_api_copy": True,
            "canonical_writer_instantiated": False,
            "analysis_fact_load_statements": snapshot.statement_count,
            "problem_lineage_fact_load_statements": problems.fact_load_statements,
            "cross_session_fact_load_statements": continuity.fact_load_statements,
            "live_backup_connections": snapshot.live_backup_connections,
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "OK",
        "natural_cohort": {
            "status": cohort.get("status"),
            "start": start,
            "start_source": start_source,
            "observed_problem_revisions": len(compact_rows),
            "typed_natural_revisions": int(
                (cohort.get("cohort") or {}).get("typed_natural_rows") or 0
            ),
            "technically_accepted_revisions": technically_accepted,
            "confirmed_resolved_revisions": confirmed,
            "policy_eligible_primary_runs": policy_eligible_true,
            "policy_eligibility_unknown_primary_runs": policy_eligible_unknown,
            "independent_user_outcome_coverage": outcome_coverage,
            "decision_checkpoints": cohort.get("decision_checkpoints") or {},
            "missingness": cohort.get("missingness") or {},
            "rows": compact_rows,
        },
        "p4_p5_readiness": _p4_compact(p4, cohort, outcome_coverage),
        "stale_run_audit": stale_audit,
        "lifecycle_summary": lifecycle.get("summary") or {},
        "snapshot": {
            "analysis": snapshot_contract,
            "lifecycle": lifecycle.get("snapshot") or {},
            "independent_immutable_snapshots": True,
        },
        "read_contract": {
            "canonical_writer_instantiated": False,
            "runtime_instantiated_by_reporter": False,
            "stale_reconciliation_called": False,
            "p5_mutation_called": False,
            "objective_text_inference_used": False,
        },
        "content_free": True,
        "mutated_canonical_ledger": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--stale-after-seconds", type=float, default=DEFAULT_STALE_AFTER_SECONDS)
    parser.add_argument("--p4-limit", type=int, default=100)
    parser.add_argument("--start-problem-id", default="")
    parser.add_argument("--start-problem-revision", type=int, default=1)
    parser.add_argument("--stale-details", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = empirical_readiness_report(
            args.workspace,
            stale_after_seconds=args.stale_after_seconds,
            p4_limit=args.p4_limit,
            start_problem_id=args.start_problem_id,
            start_problem_revision=args.start_problem_revision,
            stale_details=args.stale_details,
        )
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__}, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
