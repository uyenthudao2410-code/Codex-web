#!/usr/bin/env python3
"""Research helper: query the canonical ledger plus all archive shards.

After :mod:`archive-ledger` moves old finished runs into
``.coding-tools/orchestration/archives/ledger-archive-*.sqlite3``, any
machine that clones/pulls the repo has the full history locally. This tool
queries across every shard without modifying anything (read-only).

Usage:
  python scripts/query-ledger-history.py list
  python scripts/query-ledger-history.py counts
  python scripts/query-ledger-history.py locate <run_id>
  python scripts/query-ledger-history.py sql --table events --where "run_id='...'" --limit 20
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

CANONICAL_LEDGER = ".coding-tools/orchestration/ledger.sqlite3"
ARCHIVE_DIR = ".coding-tools/orchestration/archives"
MANIFEST = "manifest.json"

QUERYABLE_TABLES = (
    "runs", "waves", "events", "proofs", "checkpoints", "delegations",
    "idempotency_records", "managed_process_jobs", "background_operations",
    "controller_leases", "handoff_capsules", "coordination_messages",
)


def shards(workspace: Path) -> list[Path]:
    files = [workspace / CANONICAL_LEDGER]
    archive_dir = workspace / ARCHIVE_DIR
    if archive_dir.is_dir():
        files += sorted(archive_dir.glob("ledger-archive-*.sqlite3"))
    return [path for path in files if path.is_file()]


def shard_summary(path: Path) -> dict:
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        runs = connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        events = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        bounds = connection.execute(
            "SELECT MIN(started_at), MAX(started_at) FROM runs"
        ).fetchone()
    finally:
        connection.close()
    return {
        "file": path.name,
        "size_mb": round(path.stat().st_size / 1048576, 1),
        "runs": runs,
        "events": events,
        "min_started_at": bounds[0],
        "max_started_at": bounds[1],
    }


def cmd_list(workspace: Path) -> int:
    manifest_path = workspace / ARCHIVE_DIR / MANIFEST
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        print(f"manifest archives: {len(manifest.get('archives', []))}")
    for path in shards(workspace):
        info = shard_summary(path)
        print(f"{info['file']}: {info['size_mb']} MB, runs={info['runs']}, "
              f"events={info['events']}, {info['min_started_at']} -> {info['max_started_at']}")
    return 0


def cmd_counts(workspace: Path) -> int:
    for path in shards(workspace):
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        try:
            tables = [
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                ).fetchall()
            ]
            counts = {
                table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                for table in tables
            }
        finally:
            connection.close()
        interesting = {key: counts.get(key, 0) for key in
                       ("runs", "waves", "events", "proofs", "idempotency_records",
                        "managed_process_jobs")}
        print(f"{path.name}: {interesting}")
    return 0


def cmd_locate(workspace: Path, run_id: str) -> int:
    for path in shards(workspace):
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        try:
            hit = connection.execute(
                "SELECT run_id, status, started_at FROM runs WHERE run_id=?", (run_id,)
            ).fetchone()
        finally:
            connection.close()
        if hit:
            print(f"run {run_id} found in {path.name}: status={hit[1]} started_at={hit[2]}")
            return 0
    print(f"run {run_id} not found in any local shard", file=sys.stderr)
    return 1


def cmd_sql(workspace: Path, table: str, where: str, limit: int) -> int:
    if table not in QUERYABLE_TABLES:
        print(f"refusing: table must be one of {','.join(QUERYABLE_TABLES)}", file=sys.stderr)
        return 2
    limit = max(1, min(limit, 5000))
    rows: list[dict] = []
    for path in shards(workspace):
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            cols = [col[1] for col in
                    connection.execute(f'PRAGMA table_info("{table}")').fetchall()]
            if not cols:
                continue
            sql = f'SELECT * FROM "{table}"'
            if where:
                sql += f" WHERE {where}"
            sql += " LIMIT ?"
            for row in connection.execute(sql, (limit,)).fetchall():
                record = dict(row)
                record["_source_file"] = path.name
                rows.append(record)
                if len(rows) >= limit:
                    break
        except sqlite3.Error as exc:
            print(f"warning: {path.name}: {exc}", file=sys.stderr)
        finally:
            connection.close()
        if len(rows) >= limit:
            break
    print(json.dumps(rows[:limit], ensure_ascii=False, indent=2, default=str))
    print(f"-- {len(rows[:limit])} row(s) from {len(shards(workspace))} shard(s), table={table} --",
          file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List local shards with time ranges.")
    sub.add_parser("counts", help="Per-shard row counts for main tables.")
    locate = sub.add_parser("locate", help="Find which shard holds a run.")
    locate.add_argument("run_id")
    query = sub.add_parser("sql", help="SELECT across all shards (read-only).")
    query.add_argument("--table", required=True)
    query.add_argument("--where", default="")
    query.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    if args.command == "list":
        return cmd_list(workspace)
    if args.command == "counts":
        return cmd_counts(workspace)
    if args.command == "locate":
        return cmd_locate(workspace, args.run_id)
    return cmd_sql(workspace, args.table, args.where, args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
