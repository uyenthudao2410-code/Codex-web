#!/usr/bin/env python3
"""Read-only preflight or guarded exact completed-agent lane reconciliation."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.completed_agent_lane_reconciliation import (  # noqa: E402
    ExactCompletedAgentLaneReconciliationError,
    _safe_projection,
    preflight_exact_completed_agent_lane_reconciliation,
    reconcile_exact_completed_agent_lane,
)
from coding_tools_mcp.lifecycle_reconciliation import LifecycleReconciliationError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--lane-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--wave-id", required=True)
    parser.add_argument("--semantic-key", required=True)
    parser.add_argument("--thread-id", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--expected-lane-last-turn-id", required=True)
    parser.add_argument("--external-completed-turn-id", required=True)
    parser.add_argument("--external-thread-status", required=True, choices=("idle", "completed"))
    parser.add_argument("--externally-observed-at", required=True)
    parser.add_argument("--reconcile", action="store_true", help="apply the exact-ID official reconciliation")
    parser.add_argument("--runtime-stopped", action="store_true", help="attest that Recovery Host stopped the canonical writer")
    parser.add_argument("--expected-snapshot-sha256", default="")
    parser.add_argument("--expected-logical-sha256", default="")
    parser.add_argument(
        "--authority",
        default="codex_user_authorized_exact_completed_agent_lane_reconciliation",
    )
    args = parser.parse_args(argv)
    common = {
        "workspace": args.workspace,
        "lane_id": args.lane_id,
        "run_id": args.run_id,
        "wave_id": args.wave_id,
        "semantic_key": args.semantic_key,
        "thread_id": args.thread_id,
        "session_id": args.session_id,
        "expected_lane_last_turn_id": args.expected_lane_last_turn_id,
        "external_completed_turn_id": args.external_completed_turn_id,
        "external_thread_status": args.external_thread_status,
        "externally_observed_at": args.externally_observed_at,
        "observed_at": time.time(),
    }
    try:
        if not args.reconcile:
            output: object = _safe_projection(
                preflight_exact_completed_agent_lane_reconciliation(**common)
            )
        else:
            output = reconcile_exact_completed_agent_lane(
                **common,
                expected_snapshot_sha256=args.expected_snapshot_sha256,
                expected_logical_sha256=args.expected_logical_sha256,
                runtime_stopped=args.runtime_stopped,
                authority=args.authority,
            ).projection()
    except (
        OSError,
        RuntimeError,
        ValueError,
        LifecycleReconciliationError,
        ExactCompletedAgentLaneReconciliationError,
    ) as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)[:500]}, sort_keys=True))
        return 2
    print(json.dumps({"ok": True, "result": output}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
