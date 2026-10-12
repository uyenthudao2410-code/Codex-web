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


TASK='task_3b1889c84dbd4e54a2ac9729a8a4da1f'
ACTION='act_fc024ff0b54c4a8ba4c7c7b0228a7e76'
try:
    state=call('exec_command', {'operation':'exec_status','action_id':ACTION})
    require(state['action']['delivery_state']=='settled','EXEC_NOT_SETTLED_FOR_TASK_CLEANUP')
    emit({'phase':'failed_exec_observed_terminal','action_id':ACTION,'delivery_state':state['action']['delivery_state'],'execution':state['execution'],'process_state':state['process_state'],'exit_code':state['exit_code'],'attempt_count':len(state['action']['attempts'])})
    call('task_control', {'operation':'writer_release','task_id':TASK,'reason':'r9_exec_relay_terminal_reconciled'})
    call('workspace_context', {'operation':'task_close','task_id':TASK})
    emit({'phase':'failed_exec_task_closed','ok':True,'task_id':TASK,'action_id':ACTION,'command_replayed':False})
except Exception as error:
    emit({'phase':'failed_exec_task_cleanup_failed','ok':False,'code':str(error) if isinstance(error,RuntimeError) else type(error).__name__})
    raise SystemExit(1) from None
