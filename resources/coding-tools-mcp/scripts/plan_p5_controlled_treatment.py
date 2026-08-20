from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))
SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from coding_tools_mcp.p5_treatment import p5_controlled_treatment_plan
from report_p4_readiness import p4_readiness_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plan explicit P5 controlled-treatment enrollment without mutating runtime or ledger state."
    )
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--task-class", required=True, choices=("feature", "bugfix"))
    parser.add_argument("--stable-quality-oracle", action="store_true")
    parser.add_argument("--causal-fix-gate", action="store_true")
    parser.add_argument("--oracle-settled-before-mutation", action="store_true")
    parser.add_argument("--bounded-change-surface", action="store_true")
    parser.add_argument("--request-explicit-enrollment", action="store_true")
    parser.add_argument("--require-eligible", action="store_true")
    args = parser.parse_args()

    readiness = p4_readiness_report(Path(args.workspace))
    plan = p5_controlled_treatment_plan(
        readiness,
        task_class=args.task_class,
        stable_quality_oracle=args.stable_quality_oracle,
        causal_fix_gate_passed=args.causal_fix_gate,
        oracle_settled_before_mutation=args.oracle_settled_before_mutation,
        bounded_change_surface=args.bounded_change_surface,
        explicit_enrollment_requested=args.request_explicit_enrollment,
    )
    print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_eligible and plan["explicit_enrollment_may_proceed"] is not True:
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
