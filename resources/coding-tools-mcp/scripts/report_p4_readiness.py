from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.solution_economics import solution_shadow_population_report


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
    empirically_complete = gate.get("can_answer_which_signals_predict_repair") is True
    shadow_tasks = int(cohort.get("shadow_tasks") or 0)
    state = "EMPIRICALLY_COMPLETE" if empirically_complete else "COLLECTING" if shadow_tasks else "NO_SHADOW_EVIDENCE"
    return {
        "schema_version": 1,
        "state": state,
        "ledger_path": str(ledger_path),
        "population_scope": population.get("population_scope"),
        "scan_limit": population.get("scan_limit"),
        "scan_limit_semantics": population.get("scan_limit_semantics"),
        "cohort": cohort,
        "predictive_validation": validation,
        "p4_gate": gate,
        "p4_empirically_complete": empirically_complete,
        "p5_controlled_treatment_may_be_opened": empirically_complete,
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
    args = parser.parse_args()
    result = p4_readiness_report(Path(args.workspace), limit=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result["state"] == "LEDGER_MISSING":
        return 3
    if args.require_ready and result["p4_empirically_complete"] is not True:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
