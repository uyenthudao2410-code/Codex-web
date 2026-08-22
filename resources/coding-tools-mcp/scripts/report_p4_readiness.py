from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.ledger_access import open_existing_ledger
from coding_tools_mcp.p5_treatment import p5_implementation_contract
from coding_tools_mcp.solution_economics import solution_shadow_population_report


def _git_text(root: Path, *args: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False, ""
    return result.returncode == 0, result.stdout.strip()


def _git_baseline_status(root: Path) -> dict[str, object]:
    repo_ok, inside = _git_text(root, "rev-parse", "--is-inside-work-tree")
    if not repo_ok or inside.lower() != "true":
        return {
            "is_repo": False,
            "worktree_clean": False,
            "source_worktree_clean": False,
            "raw_worktree_clean": False,
            "runtime_evidence_dirty_only": False,
            "cleanliness_scope": "source_excluding_runtime_evidence_v1",
            "upstream_configured": False,
            "head_matches_upstream": False,
            "p5_baseline_ready": False,
            "requirement": "clean_source_upstream_matched_head_v2",
        }
    head_ok, head = _git_text(root, "rev-parse", "HEAD")
    upstream_ok, upstream = _git_text(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    upstream_head_ok, upstream_head = _git_text(root, "rev-parse", "@{upstream}") if upstream_ok else (False, "")
    raw_status_ok, raw_status = _git_text(root, "status", "--porcelain=v1", "--untracked-files=all")
    source_status_ok, source_status = _git_text(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        ".",
        ":(exclude).coding-tools",
        ":(exclude).coding-tools/**",
    )
    source_worktree_clean = source_status_ok and not source_status
    raw_worktree_clean = raw_status_ok and not raw_status
    runtime_evidence_dirty_only = bool(
        raw_status_ok and source_status_ok and raw_status and not source_status
    )
    head_matches_upstream = bool(head_ok and upstream_head_ok and head and head == upstream_head)
    ready = bool(source_worktree_clean and upstream_ok and head_matches_upstream)
    return {
        "is_repo": True,
        "head": head if head_ok else None,
        "upstream": upstream if upstream_ok else None,
        "upstream_head": upstream_head if upstream_head_ok else None,
        # Backward-compatible key: P5 has always consumed worktree_clean. Its
        # intended meaning is source/product cleanliness, matching the runtime
        # orchestration identity which excludes volatile .coding-tools evidence.
        "worktree_clean": source_worktree_clean,
        "source_worktree_clean": source_worktree_clean,
        "raw_worktree_clean": raw_worktree_clean,
        "runtime_evidence_dirty_only": runtime_evidence_dirty_only,
        "cleanliness_scope": "source_excluding_runtime_evidence_v1",
        "upstream_configured": upstream_ok,
        "head_matches_upstream": head_matches_upstream,
        "p5_baseline_ready": ready,
        "requirement": "clean_source_upstream_matched_head_v2",
    }


def p4_readiness_report(workspace: Path, *, limit: int = 100) -> dict[str, object]:
    root = workspace.resolve()
    ledger_path = root / ".coding-tools" / "orchestration" / "ledger.sqlite3"
    if not ledger_path.is_file():
        return {
            "schema_version": 1,
            "state": "LEDGER_MISSING",
            "ledger_path": str(ledger_path),
            "p4_empirically_complete": False,
            "p5_controlled_treatment_may_be_opened": False,
            "automatic_policy_activation": False,
            "p5_automatic_start": False,
            "reason": "canonical_orchestration_ledger_missing",
        }

    ledger = open_existing_ledger(root)
    population = solution_shadow_population_report(ledger, limit=limit)
    cohort = population.get("cohort") if isinstance(population.get("cohort"), dict) else {}
    gate = population.get("p4_gate") if isinstance(population.get("p4_gate"), dict) else {}
    validation = population.get("predictive_validation") if isinstance(population.get("predictive_validation"), dict) else {}
    policy = population.get("policy") if isinstance(population.get("policy"), dict) else {}
    predictor_coverage = population.get("predictor_coverage") if isinstance(population.get("predictor_coverage"), dict) else {}
    workload_guidance = population.get("workload_guidance") if isinstance(population.get("workload_guidance"), dict) else {}
    measurement_design = population.get("measurement_design") if isinstance(population.get("measurement_design"), dict) else {}
    replan_diagnostics = population.get("replan_diagnostics") if isinstance(population.get("replan_diagnostics"), dict) else {}
    gate_predictive_ready = gate.get("can_answer_which_signals_predict_repair") is True
    validated_signals = validation.get("validated_signals") if isinstance(validation.get("validated_signals"), list) else []
    validated_predictive_signal_ready = any(
        isinstance(signal, str) and bool(signal.strip()) for signal in validated_signals
    )
    empirically_complete = gate_predictive_ready and validated_predictive_signal_ready
    git_baseline = _git_baseline_status(root)
    p5_baseline_ready = git_baseline.get("p5_baseline_ready") is True
    # P4-C is an optional later targeting/heterogeneity gate.  It cannot block
    # P5-A instrumentation/feasibility engineering, and it never activates an
    # epoch by itself.  The old coupled flag stays as an explicit deprecated
    # compatibility projection for callers that still consume it.
    legacy_predictive_treatment_ready = empirically_complete and p5_baseline_ready
    latest_epoch = ledger.p5_latest_epoch()
    epoch_lifecycle = str((latest_epoch or {}).get("lifecycle") or "NOT_READY")
    p5_engineering_ready = p5_baseline_ready
    p5_experiment_start_ready = bool(
        latest_epoch is not None and epoch_lifecycle in {"EPOCH_ACTIVE", "EPOCH_PAUSED"}
    )
    p5_implementation = p5_implementation_contract(
        experiment_start_ready=p5_experiment_start_ready,
        epoch_lifecycle=epoch_lifecycle,
        validated_signals=validated_signals,
        treatment_readiness=legacy_predictive_treatment_ready,
    )
    shadow_tasks = int(cohort.get("shadow_tasks") or 0)
    if empirically_complete and p5_baseline_ready:
        state = "EMPIRICALLY_COMPLETE"
    elif empirically_complete:
        state = "EMPIRICALLY_COMPLETE_BASELINE_NOT_READY"
    else:
        state = "COLLECTING" if shadow_tasks else "NO_SHADOW_EVIDENCE"
    return {
        "schema_version": 1,
        "state": state,
        "ledger_path": str(ledger_path),
        "population_scope": population.get("population_scope"),
        "scan_limit": population.get("scan_limit"),
        "scan_limit_semantics": population.get("scan_limit_semantics"),
        "cohort": cohort,
        "representative_predictor_variation": population.get("representative_predictor_variation"),
        "predictor_coverage": predictor_coverage,
        "workload_guidance": workload_guidance,
        "measurement_design": measurement_design,
        "replan_diagnostics": replan_diagnostics,
        "predictive_validation": validation,
        "p4_gate": gate,
        "p4_empirically_complete": empirically_complete,
        "git_baseline": git_baseline,
        "p5_baseline_ready": p5_baseline_ready,
        "p4_c_predictive_targeting_ready": empirically_complete,
        "p4_e_descriptive_ready": False,
        "p4_e_advisory_only": True,
        "p4_e_assignment_input_allowed": False,
        "p5_experiment_engineering_ready": p5_engineering_ready,
        "p5_experiment_start_ready": p5_experiment_start_ready,
        "p5_experiment_epoch_lifecycle": epoch_lifecycle,
        "p5_latest_epoch": (
            {
                "activation_epoch_id": latest_epoch.get("activation_epoch_id"),
                "experiment_id": latest_epoch.get("experiment_id"),
                "manifest_sha256": latest_epoch.get("manifest_sha256"),
                "lifecycle": latest_epoch.get("lifecycle"),
            }
            if latest_epoch is not None
            else None
        ),
        "p5_causal_efficacy_ready": False,
        "p5_universal_policy_promotion_ready": False,
        "p5_targeted_policy_ready": False,
        "p5_readiness_requirements": {
            "clean_upstream_matched_baseline": p5_baseline_ready,
            "source_experiment_engineering_available": True,
            "explicit_manifest_and_runtime_activation_required": False,
        },
        "p5_legacy_predictive_treatment_readiness": legacy_predictive_treatment_ready,
        "p5_controlled_treatment_may_be_opened": legacy_predictive_treatment_ready,
        "p5_controlled_treatment_may_be_opened_deprecated": True,
        "p5_implementation": p5_implementation,
        "automatic_policy_activation": False,
        "p5_automatic_start": False,
        "policy": policy,
        "content_free": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report the P4 Solution Economics Shadow readiness gate from the canonical orchestration ledger."
    )
    parser.add_argument("--workspace", default=str(REPOSITORY_ROOT))
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit non-zero unless representative predictive validation is available.",
    )
    parser.add_argument(
        "--require-p5-ready",
        action="store_true",
        help=(
            "Deprecated compatibility gate: exit non-zero unless the old P4-C predictive coupling and clean "
            "source baseline hold. This does not authorize opening a P5 epoch."
        ),
    )
    parser.add_argument(
        "--require-p5-experiment-active",
        action="store_true",
        help="Exit non-zero unless an explicitly opened P5 epoch is active or paused under its exact manifest.",
    )
    args = parser.parse_args()
    result = p4_readiness_report(Path(args.workspace), limit=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result["state"] == "LEDGER_MISSING":
        return 3
    if args.require_ready and result["p4_empirically_complete"] is not True:
        return 2
    if args.require_p5_ready and result["p5_controlled_treatment_may_be_opened"] is not True:
        return 4
    if args.require_p5_experiment_active and result["p5_experiment_start_ready"] is not True:
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
