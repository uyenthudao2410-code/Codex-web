"""Memory-only, read-only diagnosis of the one already-dispatched r12 action."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import pwd
import re
import sqlite3
import time

REMOTE = Path('/home/svhome/.local/lib/codex-control-plane/incoming/r11-approved-20261011T194930649730Z')
COMMON_SHA = 'c55d9d07144654ca0216d55c8de8b20c1a238a9a722ac455d6c83ec0d406e36f'
ACTION = 'act_6aa1329b96c146f38c807f9926b3e684'
TASK = 'task_d2c1dd3bff4042d084b045e9bc5a381b'
CANARY = Path('/home/svhome/.local/state/codex-control-plane/owner-operations/r12-initial-verification-60m/canary')

class Failure(Exception):
    pass

def need(value, code):
    if not value:
        raise Failure(code)

def code(value):
    return value if isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}', value) else None

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def payload_summary(raw):
    need(isinstance(raw, str) and len(raw.encode()) <= 2 * 1024 * 1024, 'RECEIPT_TOO_LARGE')
    value = json.loads(raw)
    need(isinstance(value, dict), 'RECEIPT_NOT_OBJECT')
    result = {key: code(value.get(key)) for key in ('code', 'diagnostic_code', 'operation_kind', 'local_semantic_acceptance')}
    for key in ('patch_applied', 'local_semantic_acceptance_performed'):
        if type(value.get(key)) is bool:
            result[key] = value[key]
    result['payload_sha256'] = digest(raw.encode())
    for key in ('run_id', 'wave_id'):
        if code(value.get(key)):
            result[key] = value[key]
    verification = value.get('initial_verification')
    if isinstance(verification, dict):
        result['initial_verification'] = {key: code(verification.get(key)) for key in ('proof_status', 'plan_sha256', 'run_id', 'wave_id')}
    return result

def query(database, common):
    need(database.is_absolute() and database.is_file() and not database.is_symlink(), 'DATABASE_TARGET_UNSAFE')
    connection = sqlite3.connect(database.as_uri() + '?mode=ro', uri=True, timeout=5)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA query_only=ON'); connection.execute('BEGIN')
        action = connection.execute('SELECT * FROM actions WHERE action_id=?', (ACTION,)).fetchone()
        need(action is not None, 'EXACT_ACTION_MISSING')
        need(all(action[key] == value for key, value in {'binding_id': common.BINDING, 'device_id': common.DEVICE,
          'workspace_id': common.WORKSPACE, 'workspace_generation': common.GENERATION}.items()), 'EXACT_ACTION_TARGET_CHANGED')
        links = connection.execute('SELECT task_id FROM mcp_task_action_links WHERE action_id=?', (ACTION,)).fetchall()
        need(len(links) == 1 and links[0]['task_id'] == TASK, 'EXACT_TASK_LINK_CHANGED')
        task = connection.execute('SELECT * FROM mcp_task_sessions WHERE task_id=?', (TASK,)).fetchone()
        need(task is not None and task['binding_id'] == common.BINDING and task['device_id'] == common.DEVICE, 'EXACT_TASK_TARGET_CHANGED')
        attempts = [dict(row) for row in connection.execute('SELECT attempt_id,attempt_number,dispatched_at_ms FROM delivery_attempts WHERE action_id=? ORDER BY attempt_number', (ACTION,))]
        need(len(attempts) == 1, 'EXACT_ONE_DELIVERY_ATTEMPT_REQUIRED')
        receipts = []
        for row in connection.execute('SELECT receipt_id,receipt_state,received_at_ms,payload_json FROM receipts WHERE action_id=? ORDER BY received_at_ms,receipt_id', (ACTION,)):
            receipts.append({'receipt_id': row['receipt_id'], 'receipt_state': row['receipt_state'], 'received_at_ms': row['received_at_ms'], **payload_summary(row['payload_json'])})
        reconciliations = [dict(row) for row in connection.execute('SELECT disposition,declaration,receipt_id,reconciled_at_ms FROM action_reconciliations WHERE action_id=?', (ACTION,))]
        dispositions = [dict(row) for row in connection.execute('SELECT disposition,declaration,attempt_id,decided_at_ms FROM action_dispatch_dispositions WHERE action_id=?', (ACTION,))]
        flags = [row.get('patch_applied') for row in receipts if type(row.get('patch_applied')) is bool]
        effect = 'patch_applied_claimed_requires_native_file_proof' if True in flags else 'effect_unknown_requires_exact_native_file_and_journal_observation'
        if receipts and all(row['receipt_state'] == 'rejected' for row in receipts):
            effect = 'rejected_receipt_requires_exact_pre_effect_code_review'
        return {'action_id': ACTION, 'task_id': TASK, 'request_id': action['request_id'], 'action_context_id': action['context_id'],
          'delivery_state': action['delivery_state'], 'settled_at_ms': action['settled_at_ms'], 'created_at_ms': action['created_at_ms'],
          'expires_at_ms': action['expires_at_ms'], 'attempts': attempts, 'receipts': receipts,
          'reconciliations': reconciliations, 'dispatch_dispositions': dispositions, 'effect_classification': effect,
          'replay_forbidden': True, 'cleanup_authorized_by_this_query': False}
    finally:
        connection.close()

def main():
    need(os.name == 'posix' and pwd.getpwuid(os.getuid()).pw_name == 'svhome', 'SERVER_USER_MISMATCH')
    common_path = REMOTE / 'r11_common.py'
    need(digest(common_path.read_bytes()) == COMMON_SHA, 'FROZEN_COMMON_CHANGED')
    spec = importlib.util.spec_from_file_location('exact_readonly_common', common_path)
    common = importlib.util.module_from_spec(spec); spec.loader.exec_module(common)
    common.private_directory(REMOTE); common.protected_file(common_path); common.service_pid()
    need(common.HOST in common.run(['tailscale', 'ip', '-4'], code='TAILSCALE_IDENTITY_UNAVAILABLE').decode().split(), 'SERVER_HOST_MISMATCH')
    config = common.environment()  # Operator credential remains in memory; never printed or saved.
    bind = config.get('CONTROL_PLANE_BIND', '127.0.0.1')
    need(bind in {'127.0.0.1', '0.0.0.0', '::', common.HOST}, 'SERVICE_BIND_CHANGED')
    origin = 'http://' + (common.HOST if bind == common.HOST else '127.0.0.1') + ':' + config.get('CONTROL_PLANE_PORT', '8765')
    health = common.api(origin, config['CONTROL_PLANE_OPERATOR_TOKEN'], '/healthz')
    need(health.get('declared_source_revision') == common.REVISION and health.get('package_source_sha256') == common.PACKAGE
         and health.get('schema_version') == 29, 'SERVER_RELEASE_CHANGED')
    response = json.loads(common.protected_file(CANARY / 'canary-dispatch-response.json'))
    need(response.get('action_id') == ACTION and response.get('task_id') == TASK, 'EXACT_DISPATCH_MARKER_CHANGED')
    result = query(Path(config['CONTROL_PLANE_DB']), common)
    result.update(phase='r12_exact_action_read_only_reconciliation', ok=True, observed_at_ms=int(time.time()*1000),
      host=common.HOST, service=common.SERVICE, service_instance_id=health['service_instance_id'],
      remote_mutation=False, database_query_only=True, raw_payload_disclosed=False, raw_error_disclosed=False)
    print(json.dumps(result, sort_keys=True, separators=(',', ':')))

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'phase':'r12_exact_action_read_only_reconciliation', 'ok':False,
          'code':str(error) if isinstance(error, Failure) else 'READ_ONLY_RECONCILIATION_FAILED',
          'remote_mutation':False, 'replay_forbidden':True, 'raw_error_disclosed':False}))
        raise SystemExit(2) from None
