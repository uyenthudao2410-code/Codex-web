"""Controlled evidence-only recovery rehearsal. No apply/switch/restart command.

Writes only newly created isolated artifacts. Historical authority is withheld;
current rows and unknown effects stay intact. Output is NOT activation eligible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

LEDGER = '.coding-tools/orchestration/ledger.sqlite3'
AUTHORITY_TABLES = frozenset({'controller_goal_attachments', 'controller_leases', 'write_fences',
    'hub_clients', 'controller_reattach_receipts', 'checkout_resource_claims', 'agent_lanes',
    'run_continuations', 'goal_continuations', 'hub_client_cursors'})
IMMUTABLE_TABLES = frozenset({'events', 'problem_events', 'checkpoints', 'proofs', 'problem_revisions'})


def sha(file: Path) -> str:
    with file.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def ro(file: Path) -> sqlite3.Connection:
    c = sqlite3.connect(file.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    c.execute('PRAGMA query_only=ON')
    return c


def schema(c: sqlite3.Connection) -> dict:
    return dict(c.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))


def records(c: sqlite3.Connection, table: str) -> tuple[list[str], dict]:
    # Names come from the snapshot's schema, never command-line SQL.
    quoted = '"' + table.replace('"', '""') + '"'
    info = list(c.execute(f'PRAGMA table_info({quoted})'))
    columns = [r[1] for r in info]
    keys = [r[1] for r in sorted(info, key=lambda r: r[5]) if r[5]]
    if not keys:
        raise RuntimeError('RECOVERY_TABLE_WITHOUT_PRIMARY_KEY')
    key_indices = [columns.index(k) for k in keys]
    result = {}
    for values in c.execute(f'SELECT * FROM {quoted}'):
        key = tuple(values[i] for i in key_indices)
        if key in result:
            raise RuntimeError('RECOVERY_DUPLICATE_IDENTITY')
        result[key] = values
    return columns, result


def rehearse(current: Path, historical: Path, candidate: Path, expected_runs: set[str]) -> dict:
    if candidate.exists() or candidate.resolve() in {current.resolve(), historical.resolve()}:
        raise RuntimeError('RECOVERY_TARGET_MUST_BE_NEW_ISOLATED_FILE')
    before = sha(current)
    base, old = ro(current), ro(historical)
    out = None
    try:
        tables = schema(base)
        if tables != schema(old):
            raise RuntimeError('RECOVERY_SCHEMA_MISMATCH')
        _, current_runs = records(base, 'runs')
        _, old_runs = records(old, 'runs')
        additions = {str(key[0]) for key in old_runs.keys() - current_runs.keys()}
        if additions != expected_runs or not expected_runs:
            raise RuntimeError('RECOVERY_RUN_ALLOWLIST_MISMATCH')
        # Exclusive creation guards against accidentally overwriting a backup.
        with candidate.open('xb'):
            pass
        out = sqlite3.connect(candidate)
        base.backup(out)
        out.execute('PRAGMA foreign_keys=ON')
        out.execute('BEGIN')
        out.execute('PRAGMA defer_foreign_keys=ON')
        inserted, withheld, conflicts, effects = {}, {}, {}, {}
        for table in sorted(tables):
            cols, a = records(base, table)
            _, b = records(old, table)
            different = [key for key in a.keys() & b.keys() if a[key] != b[key]]
            if different:
                conflicts[table] = len(different)
                if table in IMMUTABLE_TABLES:
                    raise RuntimeError(f'RECOVERY_IMMUTABLE_CONFLICT table={table}')
            new = [b[key] for key in b.keys() - a.keys()]
            if table in AUTHORITY_TABLES:
                if new:
                    withheld[table] = len(new)
                continue
            if new:
                quoted = '"' + table.replace('"', '""') + '"'
                placeholders = ','.join('?' for _ in cols)
                out.executemany(f'INSERT INTO {quoted} VALUES({placeholders})', new)
                inserted[table] = len(new)
                if table in {'background_operations', 'idempotency_records', 'managed_process_jobs'}:
                    status = next((name for name in ['status', 'state', 'lifecycle_state'] if name in cols), None)
                    effects[table] = dict(Counter(row[cols.index(status)] for row in new)) if status else {'unknown': len(new)}
        if list(out.execute('PRAGMA foreign_key_check')):
            raise RuntimeError('RECOVERY_FOREIGN_KEY_CONFLICT')
        out.commit()
        if out.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('RECOVERY_INTEGRITY_FAILED')
        # Verify all existing values, including hub observations and fences,
        # were preserved. No conflict is resolved by choosing newest timestamp.
        for table in tables:
            _, original = records(base, table)
            _, merged = records(out, table)
            if any(merged.get(k) != v for k, v in original.items()):
                raise RuntimeError('RECOVERY_CURRENT_STATE_CHANGED')
        out.close()
        out = None
        if sha(current) != before:
            raise RuntimeError('RECOVERY_BACKUP_CHANGED')
        return {'schema_version': 1, 'status': 'QUARANTINED_REHEARSAL', 'activation_eligible': False,
            'canonical_mutated': False, 'existing_rows_preserved': True, 'integrity': 'ok', 'foreign_key_rows': 0,
            'inserted_rows': inserted, 'withheld_historical_authority_rows': withheld,
            'preserved_current_conflicts': conflicts, 'historical_effect_statuses': effects,
            'required_gates': ['PROBLEM_PROJECTION_RECONCILIATION', 'AUTHORITY_GENERATION_REVIEW',
                'UNKNOWN_EFFECT_RECONCILIATION', 'OPERATOR_REVIEW_BEFORE_CANONICAL_SWITCH'],
            'current_backup_sha256': before, 'historical_sha256': sha(historical), 'candidate_sha256': sha(candidate)}
    finally:
        if out is not None:
            out.rollback()
            out.close()
        base.close()
        old.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--historical-blob', required=True)
    parser.add_argument('--expected-historical-sha256', required=True)
    parser.add_argument('--expected-snapshot-sha256', required=True)
    parser.add_argument('--run-id', action='append', required=True)
    args = parser.parse_args()
    root = args.workspace.resolve()
    live = root / LEDGER
    raw = subprocess.check_output(['git', '-C', str(root), 'cat-file', 'blob', args.historical_blob])
    if hashlib.sha256(raw).hexdigest() != args.expected_historical_sha256:
        raise RuntimeError('RECOVERY_HISTORICAL_HASH_MISMATCH')
    destination = Path(tempfile.mkdtemp(prefix='codex-ledger-recovery-rehearsal-'))
    backup = destination / 'current-backup.sqlite3'
    # Online Backup API only, never filesystem copy of the live DB.
    source = sqlite3.connect(live.as_uri() + '?mode=ro', uri=True, timeout=10)
    saved = sqlite3.connect(backup)
    try:
        source.backup(saved, pages=256, sleep=0.01)
    finally:
        saved.close()
        source.close()
    historical = destination / 'historical-original.sqlite3'
    historical.write_bytes(raw)
    if sha(backup) != args.expected_snapshot_sha256:
        raise RuntimeError(f'RECOVERY_BASELINE_DRIFT backup={backup}')
    # Git's original bytes remain intact; a read-only immutable connection can
    # read its completed WAL-safe snapshot without touching source sidecars.
    report = rehearse(backup, historical, destination / 'QUARANTINED-candidate.sqlite3', set(args.run_id))
    for artifact in [backup, historical, destination / 'QUARANTINED-candidate.sqlite3']:
        artifact.chmod(0o400)
    report['artifacts_write_protected'] = True
    report.update({'captured_at_utc': datetime.now(timezone.utc).isoformat(),
                   'historical_git_blob': args.historical_blob, 'artifact_directory': str(destination)})
    (destination / 'rehearsal-report.json').write_text(json.dumps(report, sort_keys=True, indent=2), encoding='utf-8')
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
