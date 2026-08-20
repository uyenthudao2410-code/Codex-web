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

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.p5_measurement import p5_baseline_snapshot
from report_p4_readiness import p4_readiness_report


def p5_baseline_report(workspace: Path) -> dict[str, object]:
    readiness = p4_readiness_report(workspace)
    organic_rework = OrchestrationLedger(workspace).organic_rework_summary()
    return p5_baseline_snapshot(readiness, organic_rework)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report the read-only P5 organic baseline without creating treatment/control samples."
    )
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--require-baseline-observed", action="store_true")
    args = parser.parse_args()

    report = p5_baseline_report(Path(args.workspace).resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_baseline_observed and report.get("baseline_observed") is not True:
        return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
