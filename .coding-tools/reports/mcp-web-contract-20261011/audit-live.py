"""Run an approved bounded MCP read; credentials stay in remote memory."""
import json
import pathlib
import shlex
import stat
import time
import urllib.request

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

config = env('/home/svhome/.config/codex-control-plane/control-plane.env')
tunnel = env('/home/svhome/.config/codex-control-plane/mcp-tunnel.env')
header = pathlib.Path(tunnel['CONTROL_PLANE_MCP_AUTH_HEADER_FILE'])
assert header.is_file() and not header.is_symlink() and stat.S_IMODE(header.stat().st_mode) in (0o400, 0o600)
authorization = header.read_text().strip()
assert authorization.startswith('Bearer ')
origin = 'http://127.0.0.1:' + config.get('CONTROL_PLANE_MCP_PORT', '8766')
number = 0

def rpc(method, params):
    global number
    number += 1
    request = urllib.request.Request(origin + '/mcp', data=json.dumps({
        'jsonrpc': '2.0', 'id': number, 'method': method, 'params': params,
    }).encode(), headers={'Authorization': authorization, 'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)

def call(arguments):
    return rpc('tools/call', {'name': 'workspace_context', 'arguments': arguments})

try:
    listing = rpc('tools/list', {})['result']
    contract = listing['_meta']['control_plane']['tool_contract']
    emit({'phase': 'discovery', 'contract': contract, 'relays': {
        row['name']: row['_meta']['control_plane'] for row in listing['tools']
    }})
    inventory = call({'operation': 'inventory'})['result']['structuredContent']
    emit({'phase': 'inventory', 'observed_at_ms': int(time.time() * 1000), 'targets': [
        {key: row.get(key) for key in ('binding_id', 'workspace_id', 'workspace_generation',
          'capabilities', 'presence_state', 'readiness', 'dispatch_state', 'policy_state')}
        for row in inventory['targets']
    ], 'contract_present_in_inventory': 'tool_contract' in inventory})
    expected_binding = 'bind_3e05bf64cb3e4bab93d930ae1692bebb'
    assert len(inventory['targets']) == 1 and inventory['targets'][0]['binding_id'] == expected_binding
    request = {'operation': 'read_file', 'binding_id': expected_binding,
               'path': 'tests/fixtures/folder-permissions-20261011.txt', 'max_lines': 5,
               'idempotency_key': 'mcp-web-contract-read-20261011-01',
               'expected_facade_contract': {'schema_version': 32, 'profile': 'workspace_context',
                 'sha256': 'bc44c044a0b08dfdea80b8ba0dfcc080e180e21a5460dbf9726b49ac1fa769b0'}}
    bad = call(request)
    emit({'phase': 'exact_user_contract_reproduction', 'rpc_error': bad.get('error'),
          'tool_error': bad.get('result', {}).get('isError')})
    request['expected_facade_contract'] = contract
    queued = call(request)
    assert 'error' not in queued and queued['result'].get('isError') is not True
    action_id = queued['result']['structuredContent']['action_id']
    deadline = time.monotonic() + 55
    while time.monotonic() < deadline:
        status = call({'operation': 'read_status', 'action_id': action_id})['result']['structuredContent']
        if status.get('file_accessed') is True:
            file = status['file_read']['file']
            emit({'phase': 'correct_contract_read_verified', 'action_id': action_id,
                  'content_sha256': file['content_sha256'], 'bytes_read': file['bytes_read'],
                  'file_accessed': True, 'execution': status['execution']})
            break
        if status.get('action', {}).get('central_lifecycle_state') in {'rejected', 'failed', 'stopped'}:
            raise RuntimeError('READ_TERMINAL_FAILURE')
        time.sleep(2)
    else:
        raise RuntimeError('READ_PROOF_TIMEOUT')
except Exception as error:
    emit({'phase': 'audit', 'ok': False, 'error': str(error) if isinstance(error, RuntimeError) else type(error).__name__})
    raise SystemExit(1)
