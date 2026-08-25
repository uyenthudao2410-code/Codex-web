#!/usr/bin/env python3
"""Emit the read-only C4 PRL v11 canary readiness receipt for one snapshot."""

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
from coding_tools_mcp.problem_lineage_canary import problem_lineage_canary_report  # noqa: E402
from coding_tools_mcp.problem_resolution_economics import ProblemLineageFacts  # noqa: E402


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    return completed.stdout.strip() if completed.returncode == 0 else ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    root = args.workspace.resolve(strict=False)
    try:
        head = _git(root, "rev-parse", "HEAD").lower() or None
        source_dirty = bool(_git(root, "status", "--porcelain", "--", ".", ":!/.coding-tools"))
        with open_ledger_analysis_snapshot(root) as snapshot:
            problems = ProblemLineageFacts.load(snapshot.reader)
            integrity_rows = snapshot.reader.rows("PRAGMA integrity_check")
            foreign_key_violations = len(snapshot.reader.rows("PRAGMA foreign_key_check"))
            result = problem_lineage_canary_report(
                snapshot.ledger,
                problems,
                integrity_check=";".join(str(row[0]) for row in integrity_rows),
                foreign_key_violations=foreign_key_violations,
            )
            result["snapshot"] = {
                "immutable_backup_api_copy": True,
                "default_ledger_facts_load_statements": 8,
                "total_fact_load_statements": snapshot.statement_count,
                "problem_lineage_fact_load_statements": problems.fact_load_statements,
                "canonical_writer_instantiated": False,
                "live_backup_connections": snapshot.live_backup_connections,
            }
        result["source_identity"] = {
            "disk_head": head,
            "source_worktree_clean": not source_dirty,
            "dirty_source_status_withheld": source_dirty,
        }
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)[:500]}, sort_keys=True))
        return 2
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
