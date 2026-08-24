#!/usr/bin/env python3
"""Emit the A2 stage-latency coverage report from one immutable ledger snapshot."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.ledger_analysis import open_ledger_analysis_snapshot  # noqa: E402
from coding_tools_mcp.stage_latency_attribution import stage_latency_attribution_report  # noqa: E402


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _source_identity(root: Path) -> dict[str, object]:
    head = _git(root, "rev-parse", "HEAD").lower()
    status = _git(root, "status", "--porcelain", "--", ".", ":!/.coding-tools")
    clean = bool(head) and not bool(status)
    return {
        "head": head or None,
        "source_worktree_clean": clean,
        "source_head_used_for_current_cohort": head if clean else None,
        "dirty_source_status_withheld": bool(status),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--source-head", default="", help="Explicit exact source head; bypasses only the CLI source-identity selection, never the reporter's exact-wave check.")
    parser.add_argument("--minimum-decision-cohort", type=int, default=50)
    parser.add_argument("--coverage-threshold", type=float, default=0.90)
    args = parser.parse_args(argv)
    root = args.workspace.resolve(strict=False)
    try:
        identity = _source_identity(root)
        supplied_head = str(args.source_head or "").strip().lower()
        source_head = supplied_head or str(identity["source_head_used_for_current_cohort"] or "")
        with open_ledger_analysis_snapshot(root) as snapshot:
            result = stage_latency_attribution_report(
                snapshot.ledger,
                source_head=source_head,
                min_decision_cohort=args.minimum_decision_cohort,
                coverage_threshold=args.coverage_threshold,
            )
            result["snapshot"] = {
                "immutable_backup_api_copy": True,
                "ledger_facts_load_statements": snapshot.statement_count,
                "canonical_writer_instantiated": False,
                "live_backup_connections": snapshot.live_backup_connections,
            }
        result["source_identity"] = {**result["source_identity"], **identity, "source_head_explicit_override": bool(supplied_head)}
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)[:500]}, sort_keys=True))
        return 2
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
