#!/usr/bin/env python3
"""Report one fixed TG9 natural Problem cohort from an immutable ledger copy."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.cross_session_continuity_report import (  # noqa: E402
    CrossSessionContinuityFacts,
)
from coding_tools_mcp.ledger_analysis import open_ledger_analysis_snapshot  # noqa: E402
from coding_tools_mcp.natural_problem_cohort import (  # noqa: E402
    natural_problem_cohort_report,
)
from coding_tools_mcp.problem_resolution_economics import (  # noqa: E402
    ProblemLineageFacts,
)


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--start-problem-id", required=True)
    parser.add_argument("--start-problem-revision", required=True, type=int)
    parser.add_argument("--target-n", choices=(5, 10), default=10, type=int)
    args = parser.parse_args(argv)
    root = args.workspace.resolve(strict=False)
    try:
        head = _git(root, "rev-parse", "HEAD").lower() or None
        source_dirty = bool(
            _git(root, "status", "--porcelain", "--", ".", ":!/.coding-tools")
        )
        with open_ledger_analysis_snapshot(root) as snapshot:
            problems = ProblemLineageFacts.load(snapshot.reader)
            continuity = CrossSessionContinuityFacts.load(snapshot.reader)
            result = natural_problem_cohort_report(
                snapshot.ledger,
                problems,
                continuity,
                start_problem_id=args.start_problem_id,
                start_problem_revision=args.start_problem_revision,
                target_n=args.target_n,
            )
            result["snapshot"] = {
                "immutable_backup_api_copy": True,
                "total_fact_load_statements": snapshot.statement_count,
                "problem_lineage_fact_load_statements": problems.fact_load_statements,
                "cross_session_fact_load_statements": continuity.fact_load_statements,
                "canonical_writer_instantiated": False,
                "live_backup_connections": snapshot.live_backup_connections,
            }
        result["source_identity"] = {
            "disk_head": head,
            "source_worktree_clean": not source_dirty,
            "dirty_source_status_withheld": source_dirty,
        }
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": type(exc).__name__,
                    "message": str(exc)[:500],
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
