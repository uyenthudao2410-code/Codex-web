from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.evaluation_report import current_ledger_baseline_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Report the current canonical ledger/evaluation baseline without generating workload.'
    )
    parser.add_argument('--workspace', default='.')
    args = parser.parse_args()
    result = current_ledger_baseline_report(Path(args.workspace))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
