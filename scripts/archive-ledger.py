#!/usr/bin/env python3
"""Automatic size-bounded archival for the canonical orchestration ledger.

Problem: GitHub rejects any single file over 100MB, while the canonical
ledger (``.coding-tools/orchestration/ledger.sqlite3``) grows without bound
and is mandatory repository evidence. Deleting history would destroy the
research/evaluation value of the ledger.

Policy implemented here (fail-closed, per-run archival):
  1. The archive unit is a whole finished run (event hash chains are
     per-run, so moving complete runs never breaks chain verification).
  2. Only finished runs (``finished_at IS NOT NULL``) older than a cutoff
     are eligible. Runs referenced through RESTRICT/NO ACTION foreign keys
     (e.g. ``p5_experiment_epochs.ledger_run_id``) are always kept.
  3. Each archive shard is a full-schema SQLite file under
     ``.coding-tools/orchestration/archives/`` (still version-controlled
     evidence, each shard well below the GitHub limit) plus a manifest
     entry with SHA-256, time range and run list, so any other machine
     gets the full history on clone/pull and can query it with
     ``scripts/query-ledger-history.py``.
  4. Default mode is a read-only dry-run: it simulates on a temp copy and
     prints the projected canonical/archive sizes. Nothing is modified
     without ``--apply`` + ``--runtime-stopped`` + ``--expected-sha256``.

Usage:
  python scripts/archive-ledger.py [--older-than 2026-09-01] [--dry-run]
  python scripts/archive-ledger.py --apply --runtime-stopped \\
      --expected-sha256 <sha256-of-live-ledger>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

CANONICAL_LEDGER = ".coding-tools/orchestration/ledger.sqlite3"
ARCHIVE_DIR = ".coding-tools/orchestration/archives"
MANIFEST = "manifest.json"
GITHUB_HARD_LIMIT = 100 * 1024 * 1024
TARGET_CANONICAL_BYTES = 90 * 1024 * 1024
ARCHIVE_SHARD_TARGET_BYTES = 80 * 1024 * 1024
ARCHIVE_SHARD_HARD_LIMIT = 95 * 1024 * 1024
MANIFEST_SCHEMA = 1


def git_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True, capture_output=True, text=True,
    )
    return Path(result.stdout.strip()).resolve()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def table_columns(connection: sqlite3.Connection) -> dict[str, list[str]]:
    tables = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    ]
    return {
        table: [col[1] for col in connection.execute(f'PRAGMA table_info("{table}")').fetchall()]
        for table in tables
    }


def fk_to_parent(connection: sqlite3.Connection, parent: str) -> list[tuple[str, str, str, str]]:
    """(child_table, child_col, parent_col, on_delete) for FKs targeting parent."""
    found = []
    tables = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    ]
    for table in tables:
        for row in connection.execute(f'PRAGMA foreign_key_list("{table}")').fetchall():
            # (id, seq, table, from, to, on_update, on_delete, match)
            if row[2] == parent:
                found.append((table, row[3], row[4], str(row[6]).upper()))
    return found


def protected_run_ids(connection: sqlite3.Connection) -> set[str]:
    """Runs that must stay: referenced via RESTRICT/NO ACTION FKs."""
    protected: set[str] = set()
    for child, child_col, parent_col, on_delete in fk_to_parent(connection, "runs"):
        if on_delete in ("RESTRICT", "NO ACTION"):
            for (value,) in connection.execute(
                f'SELECT DISTINCT "{child_col}" FROM "{child}"'
                f' WHERE "{child_col}" IS NOT NULL AND "{child_col}" != \'\''
            ).fetchall():
                protected.add(str(value))
    return protected


def loose_tables(connection: sqlite3.Connection) -> tuple[list[str], list[str]]:
    """Tables keyed by run_id/wave_id without a cascading FK (need manual delete)."""
    cols = table_columns(connection)
    fk_runs = {(child, col) for child, col, _, _ in fk_to_parent(connection, "runs")}
    fk_waves = {(child, col) for child, col, _, _ in fk_to_parent(connection, "waves")}
    loose_run = [
        t for t, c in cols.items()
        if "run_id" in c and (t, "run_id") not in fk_runs and t != "runs"
    ]
    loose_wave = [
        t for t, c in cols.items()
        if "wave_id" in c and "run_id" not in c and (t, "wave_id") not in fk_waves
    ]
    return loose_run, loose_wave


def restrict_children(connection: sqlite3.Connection, parent: str) -> list[tuple[str, str]]:
    """(child_table, child_col) with RESTRICT/NO ACTION FKs into parent."""
    return [
        (child, col) for child, col, _, on_delete in fk_to_parent(connection, parent)
        if on_delete in ("RESTRICT", "NO ACTION")
    ]


def prune_restrict_children(connection: sqlite3.Connection,
                            dropped_run_ids: list[str], dropped_wave_ids: list[str]) -> None:
    """Allow a shard to drop runs/waves that RESTRICT-children reference.

    Only used when building an archive shard: the referenced rows stay
    intact in the canonical ledger, so nothing is lost globally. Fails
    closed if a RESTRICT-child row itself has RESTRICT dependents.
    """
    for parent, dropped in (("runs", dropped_run_ids), ("waves", dropped_wave_ids)):
        if not dropped:
            continue
        placeholders = ",".join("?" for _ in dropped)
        for child, child_col in restrict_children(connection, parent):
            incoming = [
                (table, col) for table, col, _, on_delete in fk_to_parent(connection, child)
                if on_delete in ("RESTRICT", "NO ACTION")
            ]
            victims = [
                row[0] for row in connection.execute(
                    f'SELECT DISTINCT "{child_col}" FROM "{child}"'
                    f' WHERE "{child_col}" IN ({placeholders})', dropped
                ).fetchall()
            ]
            if not victims:
                continue
            child_pk = connection.execute(f'PRAGMA table_info("{child}")').fetchall()
            pk_cols = [col[1] for col in child_pk if col[5]]
            for table, col in incoming:
                victim_placeholders = ",".join("?" for _ in victims)
                blocking = connection.execute(
                    f'SELECT COUNT(*) FROM "{table}" WHERE "{col}" IN ({victim_placeholders})',
                    victims,
                ).fetchone()[0]
                if blocking:
                    raise RuntimeError(
                        f"archive shard blocked: {blocking} row(s) in {table} "
                        f"restrict-reference {child} rows of dropped {parent}"
                    )
            connection.execute(
                f'DELETE FROM "{child}" WHERE "{child_col}" IN ({placeholders})', dropped
            )


def delete_runs(connection: sqlite3.Connection, run_ids: list[str]) -> None:
    """Delete whole runs (cascades) plus loosely-linked rows. FKs enforced."""
    if not run_ids:
        return
    loose_run, loose_wave = loose_tables(connection)
    placeholders = ",".join("?" for _ in run_ids)
    wave_ids = [
        row[0]
        for row in connection.execute(
            f"SELECT wave_id FROM waves WHERE run_id IN ({placeholders})", run_ids
        ).fetchall()
    ]
    connection.execute("PRAGMA foreign_keys=ON")
    for table in loose_run:
        connection.execute(
            f'DELETE FROM "{table}" WHERE run_id IN ({placeholders})', run_ids
        )
    if wave_ids:
        wave_placeholders = ",".join("?" for _ in wave_ids)
        for table in loose_wave:
            connection.execute(
                f'DELETE FROM "{table}" WHERE wave_id IN ({wave_placeholders})', wave_ids
            )
    connection.execute(f"DELETE FROM waves WHERE run_id IN ({placeholders})", run_ids)
    connection.execute(f"DELETE FROM runs WHERE run_id IN ({placeholders})", run_ids)


def table_counts(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        row[0]: int(
            connection.execute(f'SELECT COUNT(*) FROM "{row[0]}"').fetchone()[0]
        )
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    }


def check_clean(connection: sqlite3.Connection) -> list[str]:
    blockers: list[str] = []
    if str(connection.execute("PRAGMA integrity_check").fetchone()[0]).lower() != "ok":
        blockers.append("integrity_check_failed")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        blockers.append("foreign_key_check_failed")
    return blockers


def active_blockers(connection: sqlite3.Connection) -> list[str]:
    blockers: list[str] = []
    now = datetime.now(timezone.utc).timestamp()
    queries = {
        "active_controller_leases": (
            "SELECT COUNT(*) FROM controller_leases WHERE status='active' AND expires_at>?",
            (now,),
        ),
        "active_write_fences": (
            "SELECT COUNT(*) FROM write_fences WHERE status='active' AND expires_at>?",
            (now,),
        ),
        "active_managed_jobs": (
            "SELECT COUNT(*) FROM managed_process_jobs WHERE lifecycle_state IN"
            " ('starting','running','terminating','orphaned')",
            (),
        ),
        "active_background_operations": (
            "SELECT COUNT(*) FROM background_operations WHERE status IN ('running')",
            (),
        ),
    }
    for name, (sql, params) in queries.items():
        try:
            if int(connection.execute(sql, params).fetchone()[0]):
                blockers.append(name)
        except sqlite3.OperationalError:
            pass
    return blockers


def select_archivable(
    connection: sqlite3.Connection, cutoff: str
) -> tuple[list[str], list[str], dict[str, str]]:
    protected = protected_run_ids(connection)
    rows = connection.execute(
        "SELECT run_id, status, started_at FROM runs"
        " WHERE started_at < ? AND finished_at IS NOT NULL"
        " ORDER BY started_at",
        (cutoff,),
    ).fetchall()
    archivable = [r[0] for r in rows if r[0] not in protected]
    skipped = [r[0] for r in rows if r[0] in protected]
    active_selected = [r[0] for r in rows if r[1] == "active"]
    meta = {r[0]: r[2] for r in rows if r[0] in archivable}
    return archivable, skipped, {"active_selected": active_selected, "meta": meta}


def simulate(ledger: Path, cutoff: str) -> dict:
    """Read-only dry-run on a temp copy; returns the projected plan."""
    with tempfile.TemporaryDirectory(prefix="ledger-archive-sim-") as temp_dir:
        candidate = Path(temp_dir) / "ledger.sim.sqlite3"
        snapshot_live_ledger(ledger, candidate)
        connection = sqlite3.connect(candidate)
        try:
            blockers = check_clean(connection) + active_blockers(connection)
            archivable, skipped, extra = select_archivable(connection, cutoff)
            if extra["active_selected"]:
                blockers.append("cutoff_selects_active_runs")
            source_counts = table_counts(connection)
            delete_runs(connection, archivable)
            connection.commit()
            fk_violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            connection.execute("VACUUM")
            size_bytes = candidate.stat().st_size
            remaining_counts = table_counts(connection)
        finally:
            connection.close()
    return {
        "cutoff": cutoff,
        "blockers": blockers,
        "archivable_runs": len(archivable),
        "skipped_protected_runs": len(skipped),
        "fk_violations_after_delete": len(fk_violations),
        "source_counts": source_counts,
        "remaining_counts": remaining_counts,
        "projected_canonical_bytes": size_bytes,
        "run_ids": archivable,
        "run_started_at": extra["meta"],
    }


def pick_cutoff(ledger: Path, first_choice: str) -> tuple[str, dict]:
    """Advance the cutoff weekly until the projection fits the target."""
    cutoff = first_choice
    plan = simulate(ledger, cutoff)
    for _ in range(12):
        if plan["projected_canonical_bytes"] <= TARGET_CANONICAL_BYTES or not plan["run_ids"]:
            break
        newest_archived = max(
            plan["source_counts"] and _archived_max_started(ledger, plan["run_ids"]) or cutoff
        )
        cutoff = _add_days(newest_archived, 7)
        plan = simulate(ledger, cutoff)
    return cutoff, plan


def _archived_max_started(ledger: Path, run_ids: list[str]) -> str:
    connection = sqlite3.connect(f"file:{ledger.as_posix()}?mode=ro", uri=True)
    try:
        placeholders = ",".join("?" for _ in run_ids)
        row = connection.execute(
            f"SELECT MAX(started_at) FROM runs WHERE run_id IN ({placeholders})", run_ids
        ).fetchone()
        return str(row[0])
    finally:
        connection.close()


def _add_days(iso: str, days: int) -> str:
    try:
        parsed = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return iso
    shifted = parsed.timestamp() + days * 86400
    return datetime.fromtimestamp(shifted, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def snapshot_live_ledger(source: Path, target: Path) -> None:
    """WAL-safe consistent snapshot via the Online Backup API (never a raw copy)."""
    source_connection = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True, timeout=30.0)
    destination_connection = sqlite3.connect(target, timeout=30.0)
    try:
        source_connection.execute("PRAGMA busy_timeout=30000")
        source_connection.backup(destination_connection, pages=256, sleep=0.01)
        destination_connection.commit()
    finally:
        destination_connection.close()
        source_connection.close()


def build_shard(source: Path, keep_run_ids: list[str] | None,
                 drop_run_ids: list[str] | None, target: Path) -> dict[str, dict[str, int]]:
    """Copy source, keep/drop run sets, vacuum, validate. Returns table counts."""
    shutil.copyfile(source, target)
    connection = sqlite3.connect(target)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        if keep_run_ids is not None:
            complement = [
                row[0]
                for row in connection.execute("SELECT run_id FROM runs").fetchall()
                if row[0] not in set(keep_run_ids)
            ]
            complement_waves = [
                row[0]
                for row in connection.execute(
                    "SELECT wave_id FROM waves WHERE run_id IN (%s)" % ",".join("?" for _ in complement),
                    complement,
                ).fetchall()
            ] if complement else []
            prune_restrict_children(connection, complement, complement_waves)
            delete_runs(connection, complement)
        if drop_run_ids:
            delete_runs(connection, drop_run_ids)
        connection.commit()
        blockers = check_clean(connection)
        if blockers:
            raise RuntimeError(f"shard validation failed: {','.join(blockers)}")
        counts = scoped_counts(connection)
        if keep_run_ids is not None:
            # Archive shards are immutable research artifacts: DELETE mode
            # means no -shm/-wal sidecars can ever appear beside them
            # (only the canonical ledger's sidecars are approved repo state).
            journal_mode = str(connection.execute("PRAGMA journal_mode=DELETE").fetchone()[0]).lower()
            if journal_mode != "delete":
                raise RuntimeError(f"archive shard refused DELETE journal mode: {journal_mode}")
        connection.execute("VACUUM")
        connection.commit()
    finally:
        connection.close()
    for suffix in ("-shm", "-wal"):
        sidecar = Path(f"{target}{suffix}")
        if sidecar.exists():
            raise RuntimeError(f"archive shard retained sidecar: {sidecar.name}")
    return counts


def scoped_counts(connection: sqlite3.Connection) -> dict[str, dict[str, int]]:
    """Per-table totals split into run-linked vs unlinked/global rows.

    Shards are self-contained copies: global tables (no run_id column) and
    unlinked rows (run_id='') exist in every shard by design. Only
    run-linked rows must partition exactly across shards.
    """
    cols = table_columns(connection)
    result: dict[str, dict[str, int]] = {}
    for table, columns in cols.items():
        total = int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
        entry: dict[str, int] = {"total": total}
        if "run_id" in columns:
            linked = int(connection.execute(
                f'SELECT COUNT(*) FROM "{table}" WHERE run_id != \'\''
            ).fetchone()[0]
            )
            entry["linked"] = linked
            entry["unlinked"] = total - linked
        result[table] = entry
    return result


def reconcile(source: dict[str, dict[str, int]], *shards: dict[str, dict[str, int]]) -> list[str]:
    mismatches = []
    for table, src in sorted(source.items()):
        if "linked" in src:
            expected = src["linked"]
            actual = sum(shard.get(table, {}).get("linked", 0) for shard in shards)
            if expected != actual:
                mismatches.append(f"{table}: source_linked={expected} shards_sum={actual}")
        else:
            for index, shard in enumerate(shards):
                have = shard.get(table, {}).get("total", 0)
                if have > src["total"]:
                    mismatches.append(
                        f"{table}: shard[{index}] has {have} rows, source only {src['total']}"
                    )
    return mismatches


def fsync_file(path: Path) -> None:
    fd = os.open(str(path), os.O_RDWR)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def load_manifest(archive_dir: Path) -> dict:
    manifest_path = archive_dir / MANIFEST
    if manifest_path.is_file():
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    return {"schema_version": MANIFEST_SCHEMA, "archives": []}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--older-than", default="",
                        help="ISO cutoff; default: first day of current month (UTC).")
    parser.add_argument("--target-bytes", type=int, default=TARGET_CANONICAL_BYTES)
    parser.add_argument("--apply", action="store_true",
                        help="Execute archival (default is read-only dry-run).")
    parser.add_argument("--runtime-stopped", action="store_true",
                        help="Required for --apply: confirm the ledger owner is stopped.")
    parser.add_argument("--expected-sha256", default="",
                        help="Required for --apply: digest of the live ledger you inspected.")
    args = parser.parse_args()

    root = Path(args.workspace).resolve()
    ledger = root / CANONICAL_LEDGER
    archive_dir = root / ARCHIVE_DIR
    if not ledger.is_file():
        print(f"canonical ledger is missing: {ledger}", file=sys.stderr)
        return 2

    cutoff = args.older_than
    if not cutoff:
        now = datetime.now(timezone.utc)
        cutoff = now.strftime("%Y-%m-01T00:00:00.000Z")

    print(f"cutoff={cutoff} target_canonical_bytes={args.target_bytes}")
    effective_cutoff, plan = pick_cutoff(ledger, cutoff)
    if effective_cutoff != cutoff:
        print(f"cutoff auto-advanced to {effective_cutoff} to fit the target.")
    print(f"archivable_runs={plan['archivable_runs']} "
          f"skipped_protected={plan['skipped_protected_runs']} "
          f"projected_canonical={plan['projected_canonical_bytes']} bytes "
          f"({plan['projected_canonical_bytes']/1048576:.1f} MB)")
    if plan["blockers"]:
        print(f"BLOCKED: {','.join(plan['blockers'])}", file=sys.stderr)
        return 1
    if plan["fk_violations_after_delete"]:
        print("BLOCKED: simulated delete violates foreign keys", file=sys.stderr)
        return 1
    if not plan["run_ids"]:
        print("nothing to archive: canonical already fits policy.")
        return 0

    if not args.apply:
        print("dry-run only: no files modified. Re-run with --apply "
              "--runtime-stopped --expected-sha256 <digest> to execute.")
        print(f"live_sha256={sha256_file(ledger)}")
        return 0

    if not args.runtime_stopped:
        print("refusing: --apply requires --runtime-stopped", file=sys.stderr)
        return 1
    live_digest = sha256_file(ledger)
    if args.expected_sha256.lower() != live_digest.lower():
        print("refusing: --expected-sha256 does not match the live ledger", file=sys.stderr)
        return 1

    archive_dir.mkdir(parents=True, exist_ok=True)
    run_ids: list[str] = plan["run_ids"]
    # Bound every archive shard below the GitHub limit: estimate bytes/run
    # from the dry-run projection, then split oldest-first into chunks.
    est_archive_bytes = max(1, ledger.stat().st_size - plan["projected_canonical_bytes"])
    per_run = est_archive_bytes / max(1, len(run_ids))
    chunk_size = max(1, int(ARCHIVE_SHARD_TARGET_BYTES / max(1, per_run)))
    chunks = [run_ids[i:i + chunk_size] for i in range(0, len(run_ids), chunk_size)]
    print(f"shard_plan={len(chunks)} shard(s), ~{chunk_size} runs/shard "
          f"(est {per_run/1024:.0f} KiB/run)")

    started_at_of = dict(plan.get("run_started_at", {}))
    if not started_at_of:
        connection = sqlite3.connect(f"file:{ledger.as_posix()}?mode=ro", uri=True)
        try:
            placeholders = ",".join("?" for _ in run_ids)
            started_at_of = dict(connection.execute(
                f"SELECT run_id, started_at FROM runs WHERE run_id IN ({placeholders})",
                run_ids,
            ).fetchall())
        finally:
            connection.close()

    with tempfile.TemporaryDirectory(prefix="ledger-archive-", dir=str(ledger.parent)) as temp_dir:
        temp_path = Path(temp_dir)
        live_copy = temp_path / "live.sqlite3"
        snapshot_live_ledger(ledger, live_copy)
        if sha256_file(ledger) != live_digest:
            print("refusing: live ledger changed during snapshot", file=sys.stderr)
            return 1
        source_connection = sqlite3.connect(f"file:{live_copy.as_posix()}?mode=ro", uri=True)
        try:
            source_counts = scoped_counts(source_connection)
        finally:
            source_connection.close()
        canonical_tmp = temp_path / "ledger.canonical.sqlite3"
        canonical_counts = build_shard(live_copy, None, run_ids, canonical_tmp)
        built_shards: list[tuple[str, Path, dict, str, str]] = []
        for index, chunk in enumerate(chunks, start=1):
            chunk_bounds = (min(started_at_of[r] for r in chunk),
                            max(started_at_of[r] for r in chunk))
            stamp_min = str(chunk_bounds[0])[:10].replace("-", "")
            stamp_max = str(chunk_bounds[1])[:10].replace("-", "")
            suffix = f"-p{index}of{len(chunks)}" if len(chunks) > 1 else ""
            shard_name = (f"ledger-archive-{stamp_min}-{stamp_max}-"
                          f"{len(chunk)}runs{suffix}.sqlite3")
            archive_tmp = temp_path / shard_name
            counts = build_shard(live_copy, chunk, None, archive_tmp)
            size_bytes = archive_tmp.stat().st_size
            if size_bytes > ARCHIVE_SHARD_HARD_LIMIT:
                print(f"refusing: shard {shard_name} is {size_bytes} bytes "
                      f"(>{ARCHIVE_SHARD_HARD_LIMIT}); re-run with a smaller "
                      f"--older-than window", file=sys.stderr)
                return 1
            built_shards.append((shard_name, archive_tmp, counts,
                                 chunk_bounds[0], chunk_bounds[1]))
        mismatches = reconcile(source_counts,
                               canonical_counts,
                               *[counts for _, _, counts, _, _ in built_shards])
        if mismatches:
            print("refusing: shard reconciliation failed:", file=sys.stderr)
            for line in mismatches:
                print(f"  {line}", file=sys.stderr)
            return 1
        for shard_name, _, _, _, _ in built_shards:
            if (archive_dir / shard_name).exists():
                print(f"refusing: archive already exists: {shard_name}", file=sys.stderr)
                return 1
        installed: list[Path] = []
        for shard_name, archive_tmp, _, _, _ in built_shards:
            final_archive = archive_dir / shard_name
            shutil.copyfile(archive_tmp, final_archive)
            fsync_file(final_archive)
            installed.append(final_archive)
        pre_backup = Path(tempfile.gettempdir()) / f"ledger-pre-archive-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.sqlite3"
        shutil.copyfile(ledger, pre_backup)
        os.replace(canonical_tmp, ledger)
        fsync_file(ledger)

    manifest = load_manifest(archive_dir)
    for (shard_name, _, _, chunk_min, chunk_max), final_archive in zip(built_shards, installed):
        chunk_ids = chunks[installed.index(final_archive)]
        manifest["archives"].append({
            "file": shard_name,
            "sha256": sha256_file(final_archive),
            "size_bytes": final_archive.stat().st_size,
            "min_started_at": chunk_min,
            "max_started_at": chunk_max,
            "run_count": len(chunk_ids),
            "run_ids": sorted(chunk_ids),
            "archived_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source_sha256": live_digest,
        })
    (archive_dir / MANIFEST).write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    for final_archive in installed:
        print(f"archived -> {final_archive} ({final_archive.stat().st_size/1048576:.1f} MB)")
    print(f"canonical now {ledger.stat().st_size} bytes "
          f"({ledger.stat().st_size/1048576:.1f} MB)")
    print(f"pre-archive backup kept outside repo: {pre_backup}")
    print("next: git add archives + manifest, then "
          "npm run stage:coding-tools-delivery && npm run check:coding-tools-delivery")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
