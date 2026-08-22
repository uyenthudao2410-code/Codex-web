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

from coding_tools_mcp.accepted_result_economics_report import accepted_result_economics_report
from coding_tools_mcp.ledger_access import open_existing_ledger
from coding_tools_mcp.p5_measurement import p5_baseline_snapshot
from report_p4_readiness import p4_readiness_report


def p5_baseline_report(workspace: Path) -> dict[str, object]:
    readiness = p4_readiness_report(workspace)
    ledger = None if readiness.get("state") == "LEDGER_MISSING" else open_existing_ledger(workspace)
    organic_rework = (
        {}
        if ledger is None
        else ledger.organic_rework_summary()
    )
    git_baseline = readiness.get("git_baseline") if isinstance(readiness.get("git_baseline"), dict) else {}
    resource_economics = {} if ledger is None else accepted_result_economics_report(
        workspace,
        ledger,
        source_head=str(git_baseline.get("head") or ""),
        source_worktree_clean=git_baseline.get("source_worktree_clean") is True,
    )
    return p5_baseline_snapshot(readiness, organic_rework, resource_economics)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report the read-only P5 organic baseline without creating treatment/control samples."
    )
    parser.add_argument("--workspace", default=str(REPOSITORY_ROOT))
    parser.add_argument("--require-baseline-observed", action="store_true")
    args = parser.parse_args()

    report = p5_baseline_report(Path(args.workspace).resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_baseline_observed and report.get("baseline_observed") is not True:
        return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
