from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.ledger_access import open_existing_ledger_analysis
from coding_tools_mcp.ledger_analysis import organic_rework_summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report organic ChatWeb+MCP first-pass/rework/TTA evidence without generating workload."
    )
    parser.add_argument("--workspace", default=str(REPOSITORY_ROOT), help="Workspace containing .coding-tools/orchestration/ledger.sqlite3")
    parser.add_argument("--since", default="", help="Inclusive run_started_at lower bound (ISO-8601).")
    parser.add_argument("--until", default="", help="Inclusive run_started_at upper bound (ISO-8601).")
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    with open_existing_ledger_analysis(Path(args.workspace)) as snapshot:
        result = organic_rework_summary(snapshot.ledger, since=args.since, until=args.until, limit=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
