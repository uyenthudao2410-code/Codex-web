from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))
SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from coding_tools_mcp.p5_treatment import p5_controlled_treatment_plan
from report_p4_readiness import p4_readiness_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plan arm-neutral P5 enrollment without mutating runtime, opening an epoch, or changing treatment behavior."
    )
    parser.add_argument("--workspace", default=str(REPOSITORY_ROOT))
    parser.add_argument("--task-class", required=True, choices=("feature", "bugfix"))
    parser.add_argument("--stable-quality-oracle", action="store_true")
    parser.add_argument("--bounded-change-surface", action="store_true")
    parser.add_argument("--exact-source-identity", action="store_true")
    parser.add_argument("--no-conflicting-writer-or-lease", action="store_true")
    parser.add_argument("--no-stale-or-recovery-state", action="store_true")
    parser.add_argument("--representative-natural-task", action="store_true")
    parser.add_argument("--not-high-risk", action="store_true")
    parser.add_argument("--common-execution-contract", action="store_true")
    parser.add_argument("--causal-fix-gate", action="store_true", help="Deprecated: treatment-arm protocol detail; ignored during pre-assignment eligibility.")
    parser.add_argument("--oracle-settled-before-mutation", action="store_true", help="Deprecated: treatment-arm protocol detail; ignored during pre-assignment eligibility.")
    parser.add_argument("--request-explicit-enrollment", action="store_true")
    parser.add_argument("--require-eligible", action="store_true")
    args = parser.parse_args()

    readiness = p4_readiness_report(Path(args.workspace))
    plan = p5_controlled_treatment_plan(
        readiness,
        task_class=args.task_class,
        stable_quality_oracle=args.stable_quality_oracle,
        bounded_change_surface=args.bounded_change_surface,
        exact_source_identity_available=args.exact_source_identity,
        no_conflicting_writer_or_lease=args.no_conflicting_writer_or_lease,
        no_stale_or_recovery_state=args.no_stale_or_recovery_state,
        representative_natural_task=args.representative_natural_task,
        not_high_risk=args.not_high_risk,
        common_execution_contract_available=args.common_execution_contract,
        explicit_enrollment_requested=args.request_explicit_enrollment,
        causal_fix_gate_passed=args.causal_fix_gate if args.causal_fix_gate else None,
        oracle_settled_before_mutation=args.oracle_settled_before_mutation if args.oracle_settled_before_mutation else None,
    )
    print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_eligible and plan["explicit_enrollment_may_proceed"] is not True:
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
