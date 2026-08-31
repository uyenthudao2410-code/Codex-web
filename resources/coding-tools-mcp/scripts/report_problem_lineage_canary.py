#!/usr/bin/env python3
"""Emit the read-only C4 PRL v12 canary readiness receipt for one snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.ledger_analysis import open_ledger_analysis_snapshot  # noqa: E402
from coding_tools_mcp.lifecycle_reconciliation import logical_ledger_sha256  # noqa: E402
from coding_tools_mcp.problem_lineage_canary import problem_lineage_canary_report  # noqa: E402
from coding_tools_mcp.problem_resolution_economics import ProblemLineageFacts  # noqa: E402


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError("required git source-identity probe failed")
    return completed.stdout.strip()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _digest(value: str, name: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise RuntimeError(f"immutable snapshot {name} is not a canonical SHA-256 digest")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    root = args.workspace.resolve(strict=False)
    try:
        head = _git(root, "rev-parse", "HEAD").lower() or None
        source_dirty = bool(_git(root, "status", "--porcelain", "--", ".", ":!/.coding-tools"))
        with open_ledger_analysis_snapshot(root) as snapshot:
            reader = snapshot.reader
            if reader.connection is None:
                raise RuntimeError("immutable snapshot reader is not open")
            if snapshot.live_backup_connections != 1:
                raise RuntimeError("immutable snapshot did not use exactly one live Backup-API connection")
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
                "snapshot_at": _utc_now(),
                "immutable_backup_api_copy": True,
                "sha256": _digest(_sha256_file(reader.path), "physical"),
                "logical_sha256": _digest(logical_ledger_sha256(reader.connection), "logical"),
                "size_bytes": reader.path.stat().st_size,
                "immutable": True,
                "query_only": True,
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
    except (OSError, sqlite3.Error, RuntimeError, TypeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)[:500]}, sort_keys=True))
        return 2
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
