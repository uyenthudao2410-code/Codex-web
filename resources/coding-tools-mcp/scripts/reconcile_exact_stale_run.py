#!/usr/bin/env python3
"""Read-only preflight or exact-ID guarded stale-run reconciliation."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.stale_run_reconciliation import (  # noqa: E402
    ExactStaleRunReconciliationError,
    preflight_exact_stale_run_reconciliation,
    reconcile_exact_stale_runs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--run-id", action="append", required=True, help="opaque exact canonical run ID; repeat for one atomic batch")
    parser.add_argument("--reconcile", action="store_true", help="apply the exact-ID official atomic reconciliation")
    parser.add_argument("--runtime-stopped", action="store_true", help="attest that Recovery Host stopped the canonical writer")
    parser.add_argument("--expected-snapshot-sha256", default="")
    parser.add_argument("--expected-logical-sha256", default="")
    parser.add_argument("--authority", default="codex_user_authorized_exact_stale_reconciliation")
    args = parser.parse_args(argv)
    try:
        if not args.reconcile:
            if len(args.run_id) != 1:
                raise ExactStaleRunReconciliationError("read-only CLI preflight accepts exactly one run; batch reconcile owns its own immutable preflight")
            result = preflight_exact_stale_run_reconciliation(args.workspace, run_id=args.run_id[0], observed_at=time.time())
            from coding_tools_mcp.stale_run_reconciliation import _safe_projection  # noqa: PLC0415
            output: object = _safe_projection(result)
        else:
            receipt = reconcile_exact_stale_runs(
                args.workspace,
                run_ids=args.run_id,
                observed_at=time.time(),
                expected_snapshot_sha256=args.expected_snapshot_sha256,
                expected_logical_sha256=args.expected_logical_sha256,
                runtime_stopped=args.runtime_stopped,
                authority=args.authority,
            )
            output = receipt.projection()
    except (OSError, RuntimeError, ValueError, ExactStaleRunReconciliationError) as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)[:500]}, sort_keys=True))
        return 2
    print(json.dumps({"ok": True, "result": output}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
