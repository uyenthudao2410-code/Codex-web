from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.evaluation_report import evaluation_plane_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Report host-visible latency and explicit critical-path evidence without inferring model latency or cross-clock correlation.'
    )
    parser.add_argument('--workspace', default='.')
    parser.add_argument('--run-id', default='')
    args = parser.parse_args()
    result = evaluation_plane_report(Path(args.workspace), run_id=args.run_id)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
