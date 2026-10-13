"""Append one rejected result for the original read; never replay or edit journal."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import sys
import time

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parents[3]
base = root / 'dist/windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9c/win-unpacked/resources'
profile = Path(os.environ['APPDATA']) / 'web-mcp-assistant'
action = 'act_5e96e41f520d44d99a2b36bf749e658b'
attempt = 'try_df0e7870613c4eee8d1e9ff90b3a4d5b'
device = '4c4b7a5b-7744-49ae-a490-78a528a00471'
server = 'https://svhome.tail0e4032.ts.net'
journal = profile / 'control-plane-node.json.file-read-bridge-journal.json'
def require(value, code):
    if not value:
        raise RuntimeError(code)
def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()
def load(file):
    return json.loads(file.read_text(encoding='utf-8-sig'))
def validate():
    require(sha(base / 'app.asar') == '45903d28f4c7e0415ca30857992e5b34c66e1f7f597822c35036874df7dd78cd', 'READ_RECONCILE_PACKAGE_CHANGED')
    state = load(profile / 'runtime-state.json')
    require(state['nativeActivationEpochId'] == 'activation-mv50m446-6a132615d256208450967af03c450d00', 'READ_RECONCILE_RUNTIME_CHANGED')
    entry = load(journal)['entries'][action+'|'+attempt]
    receipt = entry['receipt']
    require(entry['state'] == 'unknown' and entry['action_id'] == action and entry['attempt_id'] == attempt and receipt['receipt_state'] == 'unknown' and receipt['receipt_submitted'] is True and receipt['local_handle'] == '' and receipt['payload']['diagnostic_code'] == 'CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID' and receipt['payload']['operation_kind'] == 'control_plane_bounded_file_read', 'READ_RECONCILE_JOURNAL_CHANGED')
    require(sha(Path('E:/DEV/Autocad/mcp-access-smoke-20261012-r9c.txt')) == '9e49f61b0725d9463f3cea5a04a26ae5794123a4f2bf8fa61af36bd29e439d89', 'READ_RECONCILE_TARGET_CHANGED')
    config = load(profile / 'control-plane-node.json')
    require(config['device_id'] == device and config['server_url'] == server and config['node_secret_dpapi'].startswith('dpapi-v1:'), 'READ_RECONCILE_CONFIG_CHANGED')
    return config
try:
    config = validate()
    before = sha(journal)
    payload = {'schema_version':1,'operation_kind':'control_plane_bounded_file_read','code':'FILE_READ_RESULT_REJECTED_OPERATOR_RECONCILIATION','diagnostic_code':'CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID','original_unknown_receipt_preserved':True,'original_local_journal_sha256':before,'read_may_have_occurred':True,'valid_bounded_read_receipt_retained':False,'action_redispatched':False,'reconciliation_required':False}
    result = {'operation':'r9c_original_read_result_reconciliation','observed_at_ms':int(time.time()*1000),'action_id':action,'attempt_id':attempt,'payload':payload,'node_journal_modified':False}
    if '--confirm-reconcile' in sys.argv:
        spec = importlib.util.spec_from_file_location('exact_node_agent', base / 'resources/control-plane/node_agent.py')
        agent = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent)
        secret = agent._unprotect_node_secret(config['node_secret_dpapi'])
        validate()
        response = agent._request(server, f'/v1/nodes/{device}/receipts', {'action_id':action,'attempt_id':attempt,'receipt_state':'rejected','local_handle':'','payload':payload}, f'Node {secret}')
        secret = None
        require(response['action_id'] == action and response['attempt_id'] == attempt and response['receipt_state'] == 'rejected' and response['delivery_state'] == 'settled', 'READ_RECONCILE_RESPONSE_INVALID')
        require(sha(journal) == before, 'READ_RECONCILE_JOURNAL_MUTATED')
        result['server_receipt'] = response
    else:
        result['mode'] = 'preflight_only'
    output = Path(__file__).with_name(f"r9c-read-reconciliation-{result['observed_at_ms']}.json")
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'report_path':str(output),**result}))
except Exception as error:
    import re
    code = str(error) if re.fullmatch(r'[A-Z_]{3,100}',str(error)) else 'READ_RECONCILE_FAILED'
    print(json.dumps({'ok':False,'code':code}))
    sys.exit(1)
