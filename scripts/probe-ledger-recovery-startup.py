"""Probe existing startup guards in a NEW isolated workspace; never apply a DB."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / 'resources' / 'coding-tools-mcp'
sys.path.insert(0, str(PACKAGE))
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


def file_hash(file: Path) -> str:
    with file.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def probe(source: Path, expected_sha256: str) -> dict:
    source = source.resolve(strict=True)
    if file_hash(source) != expected_sha256:
        raise RuntimeError('REHEARSAL_INPUT_HASH_MISMATCH')
    root = Path(tempfile.mkdtemp(prefix='codex-ledger-startup-probe-'))
    target = root / '.coding-tools' / 'orchestration' / 'ledger.sqlite3'
    target.parent.mkdir(parents=True)
    src = sqlite3.connect(source.as_uri() + '?mode=ro&immutable=1', uri=True)
    dst = sqlite3.connect(target)
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()
    ledger = OrchestrationLedger(root)  # scoped only to the new temp workspace
    with ledger._connect() as c:
        event_count = c.execute('SELECT count(*) FROM events').fetchone()[0]
        pending = [dict(r) for r in c.execute("SELECT idempotency_key,operation,request_hash FROM idempotency_records WHERE status IN ('unknown','in_progress')")]
    orphaned = ledger.mark_orphaned_background_operations(current_server_instance_id='isolated-rehearsal-server')
    unknown = ledger.mark_orphaned_idempotency(current_process_instance_id='isolated-rehearsal-process')
    expired = ledger.expire_controller_leases()
    rejected = 0
    for row in pending:
        result = ledger.claim_idempotency(**row, process_instance_id='isolated-rehearsal-process')
        if result.get('claimed') is not False or result.get('reason') != 'unknown':
            raise RuntimeError('REHEARSAL_UNKNOWN_EFFECT_REPLAY_NOT_FENCED')
        rejected += 1
    with ledger._connect() as c:
        integrity = c.execute('PRAGMA integrity_check').fetchone()[0]
        fk = len(list(c.execute('PRAGMA foreign_key_check')))
        events_unchanged = event_count == c.execute('SELECT count(*) FROM events').fetchone()[0]
        running = c.execute("SELECT count(*) FROM background_operations WHERE status='running'").fetchone()[0]
        progress = c.execute("SELECT count(*) FROM idempotency_records WHERE status='in_progress'").fetchone()[0]
    if integrity != 'ok' or fk or not events_unchanged or running or progress or file_hash(source) != expected_sha256:
        raise RuntimeError('REHEARSAL_POSTFLIGHT_FAILED')
    result = {'status': 'ISOLATED_STARTUP_GUARDS_PROVED', 'activation_eligible': False,
        'source_unchanged': True, 'source_sha256': expected_sha256, 'workspace': str(root),
        'probe_sha256': file_hash(target), 'background_marked_orphaned': orphaned,
        'idempotency_marked_unknown': unknown, 'unknown_replay_claims_rejected': rejected,
        'controller_leases_expired': len(expired), 'events_count_unchanged': events_unchanged,
        'integrity': integrity, 'foreign_key_rows': fk, 'real_runtime_started': False,
        'still_required': ['PROBLEM_PROJECTION_RECONCILIATION', 'AUTHORITY_HIGH_WATER_MARK_REVIEW', 'OPERATOR_REVIEW']}
    (root / 'startup-probe-report.json').write_text(json.dumps(result, indent=2, sort_keys=True), encoding='utf-8')
    target.chmod(0o400)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(probe(args.candidate, args.expected_sha256), sort_keys=True))
