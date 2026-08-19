from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
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
            "upstream_configured": False,
            "head_matches_upstream": False,
            "p5_baseline_ready": False,
            "requirement": "clean_upstream_matched_head_v1",
        }
    head_ok, head = _git_text(root, "rev-parse", "HEAD")
    upstream_ok, upstream = _git_text(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    upstream_head_ok, upstream_head = _git_text(root, "rev-parse", "@{upstream}") if upstream_ok else (False, "")
    status_ok, status = _git_text(root, "status", "--porcelain=v1", "--untracked-files=all")
    worktree_clean = status_ok and not status
    head_matches_upstream = bool(head_ok and upstream_head_ok and head and head == upstream_head)
    ready = bool(worktree_clean and upstream_ok and head_matches_upstream)
    return {
        "is_repo": True,
        "head": head if head_ok else None,
        "upstream": upstream if upstream_ok else None,
        "upstream_head": upstream_head if upstream_head_ok else None,
        "worktree_clean": worktree_clean,
        "upstream_configured": upstream_ok,
        "head_matches_upstream": head_matches_upstream,
        "p5_baseline_ready": ready,
        "requirement": "clean_upstream_matched_head_v1",
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

    ledger = OrchestrationLedger(root)
    population = solution_shadow_population_report(ledger, limit=limit)
    cohort = population.get("cohort") if isinstance(population.get("cohort"), dict) else {}
    gate = population.get("p4_gate") if isinstance(population.get("p4_gate"), dict) else {}
    validation = population.get("predictive_validation") if isinstance(population.get("predictive_validation"), dict) else {}
    policy = population.get("policy") if isinstance(population.get("policy"), dict) else {}
    predictor_coverage = population.get("predictor_coverage") if isinstance(population.get("predictor_coverage"), dict) else {}
    workload_guidance = population.get("workload_guidance") if isinstance(population.get("workload_guidance"), dict) else {}
    measurement_design = population.get("measurement_design") if isinstance(population.get("measurement_design"), dict) else {}
    replan_diagnostics = population.get("replan_diagnostics") if isinstance(population.get("replan_diagnostics"), dict) else {}
    empirically_complete = gate.get("can_answer_which_signals_predict_repair") is True
    git_baseline = _git_baseline_status(root)
    p5_baseline_ready = git_baseline.get("p5_baseline_ready") is True
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
        "p5_controlled_treatment_may_be_opened": empirically_complete and p5_baseline_ready,
        "automatic_policy_activation": False,
        "p5_automatic_start": False,
        "policy": policy,
        "content_free": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report the P4 Solution Economics Shadow readiness gate from the canonical orchestration ledger."
    )
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit non-zero unless representative predictive validation is available.",
    )
    parser.add_argument(
        "--require-p5-ready",
        action="store_true",
        help="Exit non-zero unless P4 is empirically complete and the Git baseline is clean and upstream-matched.",
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
