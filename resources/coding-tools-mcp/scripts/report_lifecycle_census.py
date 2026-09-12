#!/usr/bin/env python3
"""Emit one content-free, immutable Gate 0 lifecycle census."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.lifecycle_census import (  # noqa: E402
    lifecycle_census,
    open_lifecycle_census_snapshot,
    read_task_projection,
)


SUMMARY_FIELDS = (
    "summary",
    "projection",
    "snapshot",
    "read_contract",
    "content_free",
    "mutated_canonical_ledger",
    "observed_at_unix_seconds",
    "schema_version",
)


def _observed_at(value: str) -> float:
    text = str(value or "").strip()
    if not text:
        return time.time()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("--observed-at must include an explicit UTC offset or Z")
    return parsed.timestamp()


def report(
    workspace: Path,
    *,
    observed_at: float,
    grace_seconds: float,
    stale_after_seconds: float,
) -> dict[str, object]:
    root = Path(workspace).resolve(strict=False)
    with open_lifecycle_census_snapshot(root) as snapshot:
        return lifecycle_census(
            snapshot,
            workspace=root,
            observed_at=observed_at,
            grace_seconds=grace_seconds,
            stale_after_seconds=stale_after_seconds,
            projection=read_task_projection(root),
        )


def _summary_payload(payload: dict[str, object]) -> dict[str, object]:
    return {field: payload[field] for field in SUMMARY_FIELDS if field in payload}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--observed-at", default="", help="UTC ISO-8601 timestamp; defaults to the current clock.")
    parser.add_argument("--grace-seconds", type=float, default=15 * 60)
    parser.add_argument("--stale-after-seconds", type=float, default=24 * 60 * 60)
    parser.add_argument("--summary", action="store_true", help="Emit only bounded lifecycle summary fields from the same census result.")
    args = parser.parse_args(argv)
    try:
        payload = report(
            args.workspace,
            observed_at=_observed_at(args.observed_at),
            grace_seconds=args.grace_seconds,
            stale_after_seconds=args.stale_after_seconds,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__}, sort_keys=True))
        return 2
    if args.summary:
        payload = _summary_payload(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
