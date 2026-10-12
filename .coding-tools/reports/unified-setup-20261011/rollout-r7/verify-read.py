"""Verify approved r7 scoped reads over SSH stdin; output hashes only.

Credentials stay in Ubuntu process memory. Outputs contain public identifiers,
fixed diagnostics and hashes, never headers or file content.
"""
import hashlib
import json
import pathlib
import shlex
import stat
import time
import urllib.request

BINDING = 'bind_3e05bf64cb3e4bab93d930ae1692bebb'
EXPECTED_REVISION = 'beaa9d5ade4926ef231e3ec9d0a517fe93830e90'
FIXTURE_SHA = '14c82d572e3416dc67c06046ed33455ccfbaee4af1b1160196d97083def600a2'


def env(path):
    values = {}
    for line in pathlib.Path(path).read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        key, value = line.split('=', 1)
        parts = shlex.split(value, comments=True)
        values[key.strip()] = parts[0] if parts else ''
    return values


def emit(value):
    print(json.dumps(value, separators=(',', ':')), flush=True)


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


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
        return json.load(response)


try:
    inventory_result = call('workspace_context', {'operation': 'inventory'})
    require('error' not in inventory_result, 'INVENTORY_RPC_FAILED')
    inventory = inventory_result['result']['structuredContent']
    require(inventory_result['result'].get('isError') is not True, 'INVENTORY_TOOL_FAILED')
    contract = inventory['tool_contract']
    require(set(contract) == {'schema_version', 'profile', 'sha256'}, 'INVENTORY_CONTRACT_INVALID')
    targets = inventory['targets']
    require(len(targets) == 1 and targets[0]['binding_id'] == BINDING, 'EXACT_BINDING_CHANGED')
    emit({'phase': 'deployed_inventory', 'observed_at_ms': int(time.time() * 1000),
          'contract': contract, 'path_format': inventory['path_format'],
          'target': {key: targets[0].get(key) for key in ('binding_id', 'presence_state', 'readiness',
                                                        'dispatch_state', 'policy_state')},
          'relay_capabilities': inventory['relay_capabilities']})
    arguments = {'operation': 'read_file', 'binding_id': BINDING,
                 'path': 'tests/fixtures/folder-permissions-20261011.txt', 'max_lines': 5,
                 'idempotency_key': 'r7-setup-read-20261011-01',
                 'expected_facade_contract': {'schema_version': 32, 'profile': 'workspace_context',
                   'sha256': 'bc44c044a0b08dfdea80b8ba0dfcc080e180e21a5460dbf9726b49ac1fa769b0'}}
    rejected = call('workspace_context', arguments)
    require('error' not in rejected and rejected['result'].get('isError') is True,
            'MISMATCH_NOT_MODEL_VISIBLE')
    feedback = rejected['result']['structuredContent']
    require(feedback['code'] == 'CONTRACT_MISMATCH' and feedback['execution'] == 'not_started'
            and feedback['expected_facade_contract'] == contract
            and feedback['mismatch_fields'] == ['profile', 'sha256'], 'MISMATCH_FEEDBACK_INVALID')
    emit({'phase': 'contract_self_correction', 'code': feedback['code'],
          'execution': feedback['execution'], 'mismatch_fields': feedback['mismatch_fields'],
          'next_action': feedback['next_action'], 'isError': True, 'json_rpc_error': False})
    historical = call('agent_workflow', {'operation': 'patch_status',
                       'action_id': 'act_16f5443e532942019fa7bb43868b34b0'})
    require('error' not in historical and historical['result'].get('isError') is not True,
            'HISTORICAL_STATUS_FAILED')
    status = historical['result']['structuredContent']
    require(status['execution'] == 'local_patch_rejected'
            and status['local_failure']['code'] == 'CONTROL_PLANE_APPROVED_PATCH_SCHEMA_REJECTED_BEFORE_EFFECT',
            'TERMINAL_DIAGNOSTIC_INVALID')
    emit({'phase': 'historical_terminal_diagnostic', 'execution': status['execution'],
          'local_failure': status['local_failure'], 'action_id': status['action']['action_id'],
          'historical_action_replayed': False})
    arguments['expected_facade_contract'] = contract
    queued = call('workspace_context', arguments)
    require('error' not in queued and queued['result'].get('isError') is not True, 'NEW_READ_REJECTED')
    action_id = queued['result']['structuredContent']['action_id']
    emit({'phase': 'new_read_queued', 'action_id': action_id,
          'replayed': queued['result']['structuredContent'].get('replayed')})
    deadline = time.monotonic() + 55
    while time.monotonic() < deadline:
        response = call('workspace_context', {'operation': 'read_status', 'action_id': action_id})
        require('error' not in response and response['result'].get('isError') is not True,
                'READ_STATUS_FAILED')
        status = response['result']['structuredContent']
        if status.get('file_accessed') is True:
            file = status['file_read']['file']
            require(file['content_sha256'] == FIXTURE_SHA and file['bytes_read'] == 49,
                    'FIXTURE_HASH_CHANGED')
            emit({'phase': 'new_read_verified', 'action_id': action_id, 'file_accessed': True,
                  'bytes_read': file['bytes_read'], 'content_sha256': file['content_sha256'],
                  'execution': status['execution'], 'ok': True})
            break
        if status.get('action', {}).get('central_lifecycle_state') in {'rejected', 'failed', 'stopped'}:
            emit({'phase': 'new_read_terminal_failure', 'action_id': action_id,
                  'execution': status['execution'], 'local_failure': status.get('local_failure')})
            raise RuntimeError('READ_TERMINAL_FAILURE')
        time.sleep(2)
    else:
        raise RuntimeError('READ_PROOF_TIMEOUT')
    source_path = 'control-plane/control_plane/mcp_facade.py'
    source_arguments = {'operation': 'read_file', 'binding_id': BINDING,
                        'path': source_path, 'start_line': 1, 'max_lines': 40, 'max_bytes': 8192,
                        'idempotency_key': 'r7-setup-source-20261011-01',
                        'expected_facade_contract': contract}
    source_queued = call('workspace_context', source_arguments)
    require('error' not in source_queued and source_queued['result'].get('isError') is not True,
            'SOURCE_READ_REJECTED')
    source_action = source_queued['result']['structuredContent']['action_id']
    emit({'phase': 'source_read_queued', 'action_id': source_action, 'path': source_path})
    deadline = time.monotonic() + 55
    while time.monotonic() < deadline:
        source_response = call('workspace_context', {'operation': 'read_status', 'action_id': source_action})
        require('error' not in source_response and source_response['result'].get('isError') is not True,
                'SOURCE_READ_STATUS_FAILED')
        source_status = source_response['result']['structuredContent']
        if source_status.get('file_accessed') is True:
            source_file = source_status['file_read']['file']
            require(source_file['path'] == source_path and 0 < source_file['bytes_read'] <= 8192
                    and hashlib.sha256(source_file['content'].encode()).hexdigest() == source_file['content_sha256'],
                    'SOURCE_READ_INTEGRITY_FAILED')
            emit({'phase': 'source_read_verified', 'action_id': source_action, 'path': source_path,
                  'bytes_read': source_file['bytes_read'], 'content_sha256': source_file['content_sha256'],
                  'execution': source_status['execution'], 'file_accessed': True, 'ok': True})
            break
        if source_status.get('action', {}).get('central_lifecycle_state') in {'rejected', 'failed', 'stopped'}:
            emit({'phase': 'source_read_terminal_failure', 'action_id': source_action,
                  'execution': source_status['execution'], 'local_failure': source_status.get('local_failure')})
            raise RuntimeError('SOURCE_READ_TERMINAL_FAILURE')
        time.sleep(2)
    else:
        raise RuntimeError('SOURCE_READ_PROOF_TIMEOUT')
except Exception as error:
    emit({'phase': 'rollout_verification', 'ok': False,
          'error': str(error) if isinstance(error, RuntimeError) else type(error).__name__})
    raise SystemExit(1)
