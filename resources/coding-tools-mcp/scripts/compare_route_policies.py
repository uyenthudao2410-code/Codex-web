from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare representative paired route policies by accepted-result quality, time and observed economics."
    )
    parser.add_argument("--workspace", default=".", help="Workspace containing .coding-tools/orchestration/ledger.sqlite3")
    parser.add_argument("--baseline-policy", default="chatweb_mcp")
    parser.add_argument(
        "--candidate-policy",
        action="append",
        dest="candidate_policies",
        metavar="POLICY",
        help="Candidate policy identifier; repeat for multiple policies. Defaults to mini and luna when omitted.",
    )
    parser.add_argument("--min-pairs", type=int, default=10)
    parser.add_argument("--min-task-classes", type=int, default=3)
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    ledger = OrchestrationLedger(Path(args.workspace))
    result = ledger.paired_policy_evaluation(
        baseline_policy=args.baseline_policy,
        candidate_policies=tuple(args.candidate_policies or ("mini", "luna")),
        limit=args.limit,
        min_pairs=args.min_pairs,
        min_task_classes=args.min_task_classes,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
