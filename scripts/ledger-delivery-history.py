"""Read-only semantic retention check for Git delivery, including merge parents.

This is not a database repair/merge utility. Immutable events must remain exact;
mutable projections need to retain identities. Valid staged archive shards may
hold history removed by the supported whole-run archival operation.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
from pathlib import Path

LEDGER = '.coding-tools/orchestration/ledger.sqlite3'
ARCHIVES = '.coding-tools/orchestration/archives'
TABLE_KEYS = {'events': 'event_id', 'problem_events': 'event_id', 'runs': 'run_id',
              'waves': 'wave_id', 'checkpoints': 'checkpoint_id', 'proofs': 'proof_id'}


def git(root: Path, *args: str, optional: bool = False) -> bytes:
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True)
    if result.returncode:
        if optional:
            return b''
        raise RuntimeError('LEDGER_HISTORY_GIT_READ_FAILED')
    return result.stdout


def read_blob(root: Path, ref: str, relative: str, *, optional: bool = False) -> bytes:
    if optional:
        entry = (git(root, 'ls-tree', ref, '--', relative) if ref
                 else git(root, 'ls-files', '--stage', '--', relative))
        if not entry.strip():
            return b''
    # An absent optional path is allowed; an unreadable existing blob is not.
    return git(root, 'show', f'{ref}:{relative}')


def facts(raw: bytes) -> dict:
    if not raw.startswith(b'SQLite format 3\x00'):
        raise RuntimeError('LEDGER_HISTORY_DATABASE_INVALID')
    # Git blobs are completed Backup API snapshots, not live WAL databases.
    # Deserialize only in memory; normalize journal header there, never on disk.
    view = bytearray(raw)
    view[18] = view[19] = 1
    connection = sqlite3.connect(':memory:')
    try:
        connection.deserialize(bytes(view))
        connection.execute('PRAGMA query_only=ON')
        if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('LEDGER_HISTORY_DATABASE_INVALID')
        result = {}
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table, key in TABLE_KEYS.items():
            if table not in tables:
                continue
            columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')]
            # Supports the original small delivery-test/legacy event fixture.
            if key not in columns and table == 'events' and 'seq' in columns:
                key = 'seq'
            if key not in columns:
                raise RuntimeError('LEDGER_HISTORY_IDENTITY_SCHEMA_UNSUPPORTED')
            rows = {}
            for values in connection.execute(f'SELECT * FROM "{table}"'):
                row = dict(zip(columns, values))
                identity = row[key]
                if identity is None or identity == '' or identity in rows:
                    raise RuntimeError('LEDGER_HISTORY_DUPLICATE_OR_MISSING_IDENTITY')
                rows[identity] = row if table in {'events', 'problem_events'} else None
            result[table] = rows
        if 'events' not in result:
            raise RuntimeError('LEDGER_HISTORY_EVENTS_MISSING')
        return result
    finally:
        connection.close()


def union(target: dict, other: dict) -> None:
    for table, rows in other.items():
        current = target.setdefault(table, {})
        for identity, row in rows.items():
            if identity in current and current[identity] != row:
                raise RuntimeError(f'LEDGER_HISTORY_EVENT_CONFLICT table={table}')
            current[identity] = row


def tree_facts(root: Path, ref: str, *, required: bool) -> dict:
    canonical = read_blob(root, ref, LEDGER, optional=not required)
    result = facts(canonical) if canonical else {}
    raw_manifest = read_blob(root, ref, f'{ARCHIVES}/manifest.json', optional=True)
    if not raw_manifest:
        return result
    manifest = json.loads(raw_manifest)
    if manifest.get('schema_version') != 1 or not isinstance(manifest.get('archives'), list):
        raise RuntimeError('LEDGER_HISTORY_ARCHIVE_MANIFEST_INVALID')
    seen = set()
    for entry in manifest['archives']:
        name = entry.get('file')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*\.sqlite3', name) or name in seen:
            raise RuntimeError('LEDGER_HISTORY_ARCHIVE_PATH_INVALID')
        seen.add(name)
        raw = read_blob(root, ref, f'{ARCHIVES}/{name}')
        if hashlib.sha256(raw).hexdigest() != entry.get('sha256') or len(raw) != entry.get('size_bytes'):
            raise RuntimeError('LEDGER_HISTORY_ARCHIVE_HASH_MISMATCH')
        archived = facts(raw)
        run_ids = entry.get('run_ids')
        if not isinstance(run_ids, list) or len(set(run_ids)) != len(run_ids) or len(run_ids) != entry.get('run_count'):
            raise RuntimeError('LEDGER_HISTORY_ARCHIVE_RUN_MANIFEST_INVALID')
        if not set(run_ids).issubset(archived.get('runs', {})):
            raise RuntimeError('LEDGER_HISTORY_ARCHIVE_RUN_MISSING')
        union(result, archived)
    return result


def baseline_refs(root: Path) -> list[str]:
    head = git(root, 'rev-parse', '--verify', 'HEAD', optional=True).decode().strip()
    refs = [head] if head else []
    if head:
        parents = git(root, 'show', '-s', '--format=%P', head).decode().split()
        if len(parents) > 1:
            refs.extend(parents)
    merge_path = Path(git(root, 'rev-parse', '--git-path', 'MERGE_HEAD').decode().strip())
    if not merge_path.is_absolute():
        merge_path = root / merge_path
    if merge_path.exists():
        for ref in merge_path.read_text(encoding='ascii').split():
            if not re.fullmatch(r'[a-f0-9]{40,64}', ref):
                raise RuntimeError('LEDGER_HISTORY_MERGE_ID_INVALID')
            refs.append(ref)
    return list(dict.fromkeys(refs))


def verify_history(root: Path, extra_refs: tuple[str, ...] = ()) -> dict:
    candidate = tree_facts(root, '', required=True)  # empty ref means index
    refs = baseline_refs(root)
    for requested in extra_refs:
        resolved = git(root, 'rev-parse', '--verify', '--end-of-options', f'{requested}^{{commit}}').decode().strip()
        if resolved not in refs:
            refs.append(resolved)
    for ref in refs:
        prior = tree_facts(root, ref, required=False)
        for table, rows in prior.items():
            delivered = candidate.get(table, {})
            missing = sum(identity not in delivered for identity in rows)
            changed = sum(identity in delivered and row != delivered[identity] for identity, row in rows.items())
            if missing or changed:
                raise RuntimeError(f'LEDGER_HISTORY_NOT_PRESERVED baseline={ref} table={table} missing={missing} changed={changed}')
    return {'checked_baselines': len(refs), 'scope': 'head_and_merge_parents_plus_explicit_baselines',
            'canonical_mutated': False, 'index_mutated': False}
