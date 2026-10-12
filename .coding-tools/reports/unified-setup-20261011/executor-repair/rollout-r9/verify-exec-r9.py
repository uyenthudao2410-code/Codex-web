"""One authorized, bounded live MCP test; emit only fixed diagnostics/hashes.

Run over SSH stdin. Credentials remain in Ubuntu process memory.
"""
import hashlib
import json
import pathlib
import re
import shlex
import stat
import sys
import time
import urllib.request

BINDING = 'bind_3e05bf64cb3e4bab93d930ae1692bebb'
EXPIRY = int(sys.argv[1])
ARGV = ['node', '--test', 'tests/control-plane-approved-patch-runtime.test.js']


def emit(value):
    print(json.dumps({'observed_at_ms': int(time.time() * 1000), **value}, separators=(',', ':')), flush=True)


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def env(path):
    result = {}
    for line in pathlib.Path(path).read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        key, value = line.split('=', 1)
        parts = shlex.split(value, comments=True)
        result[key.strip()] = parts[0] if parts else ''
    return result


config = env('/home/svhome/.config/codex-control-plane/control-plane.env')
tunnel = env('/home/svhome/.config/codex-control-plane/mcp-tunnel.env')
header = pathlib.Path(tunnel['CONTROL_PLANE_MCP_AUTH_HEADER_FILE'])
require(header.is_file() and not header.is_symlink()
        and stat.S_IMODE(header.stat().st_mode) in (0o400, 0o600), 'HEADER_FILE_ACL_INVALID')
authorization = header.read_text().strip()
require(authorization.startswith('Bearer '), 'HEADER_FORMAT_INVALID')
origin = 'http://127.0.0.1:' + config.get('CONTROL_PLANE_MCP_PORT', '8766')
number = 0


def call(name, arguments):
    global number
    number += 1
    request = urllib.request.Request(origin + '/mcp', data=json.dumps({
        'jsonrpc': '2.0', 'id': number, 'method': 'tools/call',
        'params': {'name': name, 'arguments': arguments},
    }).encode(), headers={'Authorization': authorization, 'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.load(response)
    require('error' not in result, 'MCP_PROTOCOL_ERROR')
    if result['result'].get('isError') is True:
        feedback = result['result'].get('structuredContent', {})
        code = feedback.get('code')
        emit({'phase': 'tool_rejected', 'tool': name,
              'code': code if isinstance(code, str) and re.fullmatch(r'[A-Z0-9_]{2,96}', code) else 'MCP_TOOL_ERROR',
              'execution': feedback.get('execution')})
        raise RuntimeError('MCP_TOOL_ERROR')
    return result['result']['structuredContent']


task_id = None
action_id = None
terminal = False
try:
    require(int(time.time() * 1000) + 600_000 < EXPIRY, 'INSUFFICIENT_APPROVED_AUTHORITY_WINDOW')
    inventory = call('workspace_context', {'operation': 'inventory'})
    target = next((item for item in inventory['targets'] if item['binding_id'] == BINDING), None)
    require(target is not None and target['presence_state'] == 'online'
            and target['readiness'] == 'ready' and target['policy_state'] == 'enabled', 'TARGET_NOT_READY')
    contract = inventory['tool_contract']
    emit({'phase': 'exec_preflight', 'contract': contract,
          'target': {key: target.get(key) for key in ('binding_id', 'presence_state', 'readiness', 'policy_state')},
          'argv': ARGV, 'timeout_ms': 300_000, 'max_output_bytes': 32768})
    task = call('workspace_context', {'operation': 'task_open', 'binding_id': BINDING,
        'label': 'Unified r9 MCP exec verification', 'idempotency_key': 'r9-lifecycle-exec-task-20261011-01'})
    task_id = task['task']['task_id']
    call('task_control', {'operation': 'writer_claim', 'task_id': task_id})
    emit({'phase': 'exec_task_opened', 'task_id': task_id})
    queued = call('exec_command', {'operation': 'exec_run', 'binding_id': BINDING,
        'task_id': task_id, 'argv': ARGV, 'cwd': '', 'timeout_ms': 300_000, 'max_output_bytes': 32768,
        'idempotency_key': 'r9-lifecycle-exec-proof-20261011-01', 'expected_facade_contract': contract})
    action_id = queued['action_id']
    emit({'phase': 'exec_queued', 'action_id': action_id, 'task_id': task_id, 'replayed': queued.get('replayed')})
    deadline = time.monotonic() + 540
    last_renewal = time.monotonic()
    last_state = None
    while time.monotonic() < deadline:
        status = call('exec_command', {'operation': 'exec_status', 'action_id': action_id})
        state = (status['execution'], status['action']['delivery_state'], status['action']['central_lifecycle_state'])
        if state != last_state:
            emit({'phase': 'exec_observation', 'action_id': action_id, 'execution': state[0],
                  'delivery_state': state[1], 'central_lifecycle_state': state[2],
                  'process_state': status['process_state'], 'exit_code': status['exit_code'],
                  'attempt_count': len(status['action']['attempts']), 'local_failure': status.get('local_failure')})
            last_state = state
        if status['execution'] == 'completed_exec_relay':
            terminal = True
            require(status['exit_code'] == 0 and status['process_state'] == 'completed'
                    and status['action']['delivery_state'] == 'settled', 'LIVE_TEST_FAILED')
            output = ''
            cursor = 0
            while True:
                page = call('command_control', {'operation': 'exec_output', 'action_id': action_id,
                                                'cursor': cursor, 'max_bytes': 32768})
                require(page['has_output'] is True and page['exit_code'] == 0, 'EXEC_OUTPUT_UNVERIFIED')
                output += page['output']
                require(len(output.encode()) <= 65536, 'EXEC_OUTPUT_BOUND_EXCEEDED')
                if not page['truncated']:
                    break
                require(page['next_cursor'] > cursor, 'EXEC_OUTPUT_CURSOR_STALLED')
                cursor = page['next_cursor']
            passes = re.search(r'^# pass (\d+)\s*$', output, re.MULTILINE)
            failures = re.search(r'^# fail (\d+)\s*$', output, re.MULTILINE)
            require(passes is not None and failures is not None
                    and int(passes[1]) == 4 and int(failures[1]) == 0, 'LIVE_TEST_TAP_PROOF_INVALID')
            emit({'phase': 'live_test_verified', 'action_id': action_id, 'argv': ARGV,
                  'exit_code': 0, 'tests_passed': 4, 'tests_failed': 0,
                  'output_bytes': len(output.encode()), 'output_sha256': hashlib.sha256(output.encode()).hexdigest(),
                  'attempt_count': len(status['action']['attempts']),
                  'exec_receipt_sha256': status['exec']['response_sha256'], 'ok': True})
            break
        if state[1] == 'reconcile_required':
            raise RuntimeError('EXEC_UNKNOWN_RECONCILIATION_REQUIRED')
        if state[2] in {'rejected', 'failed', 'stopped'}:
            terminal = state[1] == 'settled'
            raise RuntimeError('EXEC_TERMINAL_REJECTION')
        if time.monotonic() - last_renewal > 25:
            call('task_control', {'operation': 'writer_claim', 'task_id': task_id})
            last_renewal = time.monotonic()
        time.sleep(5)
    else:
        stop = call('command_control', {'operation': 'exec_stop', 'action_id': action_id})
        emit({'phase': 'exec_proof_deadline_stop_requested', 'action_id': action_id,
              'stop_state': stop['stop_state'], 'execution': stop['execution']})
        raise RuntimeError('EXEC_PROOF_DEADLINE_PENDING_RECONCILIATION')
except Exception as error:
    emit({'phase': 'r9_exec_verification', 'ok': False, 'task_id': task_id, 'action_id': action_id,
          'code': str(error) if isinstance(error, RuntimeError) else type(error).__name__})
    raise SystemExit(1) from None
finally:
    if task_id is not None and (terminal or action_id is None):
        try:
            call('task_control', {'operation': 'writer_release', 'task_id': task_id, 'reason': 'r9_exec_terminal'})
            closed = call('workspace_context', {'operation': 'task_close', 'task_id': task_id})
            emit({'phase': 'exec_task_closed', 'task_id': task_id, 'terminal_action': terminal})
        except Exception:
            emit({'phase': 'exec_task_cleanup_unverified', 'task_id': task_id, 'action_id': action_id})
