from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.ledger_maintenance import compact_ledger, inspect_maintenance_readiness, post_restart_append_smoke


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect or explicitly fence canonical ledger maintenance.")
    parser.add_argument("action", choices=("inspect", "compact", "append-smoke"))
    parser.add_argument("--workspace", default=str(PACKAGE_ROOT.parents[1]))
    parser.add_argument("--expected-sha256", default="")
    parser.add_argument("--runtime-stopped", action="store_true")
    parser.add_argument("--allow-append-smoke", action="store_true")
    args = parser.parse_args()
    if args.action == "inspect":
        print(json.dumps(inspect_maintenance_readiness(Path(args.workspace)), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.action == "append-smoke":
        print(json.dumps(post_restart_append_smoke(Path(args.workspace), explicitly_authorized=args.allow_append_smoke), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    result = compact_ledger(Path(args.workspace), expected_sha256=args.expected_sha256, runtime_stopped=args.runtime_stopped)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
