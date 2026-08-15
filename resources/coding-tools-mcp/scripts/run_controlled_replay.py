from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.evaluation_replay import build_counterbalanced_plan, execute_controlled_replay


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plan or explicitly execute a controlled, counterbalanced AB/BA replay using caller-supplied tasks and commands."
    )
    parser.add_argument("--manifest", required=True, help="JSON manifest describing causal identity and study controls.")
    parser.add_argument("--execute", action="store_true", help="Explicitly run caller-supplied argv in fresh detached worktrees. Default is plan-only.")
    parser.add_argument("--output", help="Optional JSON output path; stdout is always content-free JSON.")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    plan = build_counterbalanced_plan(manifest)
    result = execute_controlled_replay(manifest, plan) if args.execute else {
        "schema_version": 1,
        "mode": "plan_only",
        "plan": plan,
        "executed": False,
    }
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
