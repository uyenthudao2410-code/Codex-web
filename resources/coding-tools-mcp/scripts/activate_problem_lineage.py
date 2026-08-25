#!/usr/bin/env python3
"""Read-only preflight or guarded local activation of canonical PRL v9/v10-to-v11."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.problem_lineage_activation import (  # noqa: E402
    ProblemLineageActivationError,
    activate_problem_lineage_schema,
    preflight_problem_lineage_activation,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--activate", action="store_true", help="perform the irreversible additive v9/v10-to-v11 migration")
    parser.add_argument("--runtime-stopped", action="store_true", help="attest that Recovery Host stopped the canonical writer")
    parser.add_argument("--expected-snapshot-sha256", default="")
    parser.add_argument("--expected-logical-sha256", default="")
    args = parser.parse_args(argv)
    try:
        if not args.activate:
            result: object = preflight_problem_lineage_activation(args.workspace, observed_at=time.time())
        else:
            result = activate_problem_lineage_schema(
                args.workspace,
                observed_at=time.time(),
                expected_snapshot_sha256=args.expected_snapshot_sha256,
                expected_logical_sha256=args.expected_logical_sha256,
                runtime_stopped=args.runtime_stopped,
            ).projection()
    except (OSError, RuntimeError, ValueError, ProblemLineageActivationError) as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)[:500]}, sort_keys=True))
        return 2
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
