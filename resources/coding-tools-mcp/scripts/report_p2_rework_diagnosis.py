from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.ledger_access import open_existing_ledger
from coding_tools_mcp.rework_diagnosis import stratified_rework_diagnosis


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Report P2 stratified accepted-result rework diagnosis from the canonical ledger.'
    )
    parser.add_argument('--workspace', default=str(REPOSITORY_ROOT))
    parser.add_argument('--limit', type=int, default=5000)
    args = parser.parse_args()
    root = Path(args.workspace).resolve()
    result = stratified_rework_diagnosis(open_existing_ledger(root), limit=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
