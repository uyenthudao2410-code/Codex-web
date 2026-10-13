"""Upload hash-verified inert artifacts and run the read-only deployment preflight."""
import ast
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REMOTE = '/home/svhome/.local/lib/codex-control-plane/releases'
OPTIONS = ['-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=yes', 'svhome@100.116.112.22']
receipt = json.loads((HERE / 'server-candidate-preparation.json').read_text(encoding='utf-8'))
validation = json.loads((HERE / 'server-candidate-validation.json').read_text(encoding='utf-8'))
if validation.get('passed') is not True or validation.get('package_source_sha256') != receipt['verification']['package_source_sha256']:
    raise RuntimeError('EXACT_CANDIDATE_VALIDATION_REQUIRED')
history = json.loads((HERE.parent / 'native-first-20261012/historic-dispatch-proof.json').read_text(encoding='utf-8'))
if history.get('ok') is not True or history.get('action_expired') is not True or history['receipts'] or history['live_tasks'] or history['live_writers'] or history['intent_kinds'] != {name: name == 'mcp_read_only_intents' for name in history['intent_kinds']}:
    raise RuntimeError('EXACT_HISTORICAL_METADATA_PROOF_REQUIRED')
receipt['expected_historical_dispatch_actions'] = [{key: history['action'][key] for key in ('action_id', 'device_id', 'workspace_id', 'workspace_generation', 'tool_name', 'delivery_state', 'expires_at_ms', 'settled_at_ms')}]
receipt['targets'] = [
    {'workspace_id': 'workspace_f93b5bac9dc74fae9cea66f44c4ebc94', 'workspace_generation': 'generation_a420c8bfcfcb4e42b5bb7fc5e5cec097'},
    {'workspace_id': 'workspace_bc86004be2684b958ab7a9a6f9530cd7', 'workspace_generation': 'generation_03f9c04f1b14414fa4bfa7d91cc8ea7a'}]
pins_path = HERE / 'server-deployment-pins.json'
with pins_path.open('x', encoding='utf-8', newline='\n') as target:
    json.dump(receipt, target, indent=2)
    target.write('\n')
helper = HERE / 'deploy-server-candidate.py'
ast.parse(helper.read_bytes())
helper_hash = hashlib.sha256(helper.read_bytes()).hexdigest()
name = receipt['verification']['release_name']
suffix = name.rsplit('-', 1)[-1] + '-' + helper_hash[:12]
files = [(Path(receipt['candidate_archive']), REMOTE + '/' + name + '.tar.gz'),
         (pins_path, REMOTE + '/.parallel-native-' + suffix + '.json'),
         (helper, REMOTE + '/.parallel-native-' + suffix + '.py')]
uploader = '''import hashlib,json,os,sys
from pathlib import Path
item=json.loads(sys.argv[1]); p=Path(item['path'])
if p.parent!=Path('/home/svhome/.local/lib/codex-control-plane/releases') or p.is_symlink():raise RuntimeError('UPLOAD_TARGET_INVALID')
data=sys.stdin.buffer.read(33554433)
if len(data)>33554432 or hashlib.sha256(data).hexdigest()!=item['sha256']:raise RuntimeError('UPLOAD_CONTENT_INVALID')
if p.exists():
 if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise RuntimeError('EXISTING_ARTIFACT_DIFFERS')
else:
 os.umask(0o077)
 with p.open('xb') as target:target.write(data)
 p.chmod(0o600)
print(json.dumps({'ok':True,'path':str(p),'sha256':item['sha256']}))
'''
uploads = []
for local, remote in files:
    record = {'path': remote, 'sha256': hashlib.sha256(local.read_bytes()).hexdigest()}
    command = 'python3 -B -c ' + shlex.quote(uploader) + ' ' + shlex.quote(json.dumps(record))
    result = subprocess.run(['ssh.exe', *OPTIONS, command], input=local.read_bytes(), capture_output=True, timeout=30)
    response = json.loads(result.stdout)
    if result.returncode or response != {'ok': True, **record}:
        raise RuntimeError('INERT_UPLOAD_NOT_VERIFIED')
    uploads.append(response)
command = 'python3 -B ' + shlex.quote(files[2][1]) + ' --receipt ' + shlex.quote(files[1][1])
result = subprocess.run(['ssh.exe', *OPTIONS, command], capture_output=True, timeout=55)
preflight = json.loads(result.stdout)
report = {'operation': 'parallel_native_inert_upload_preflight', 'ok': result.returncode == 0 and preflight.get('ok') is True,
    'deployment_helper_sha256': helper_hash, 'uploads': uploads, 'preflight': preflight,
    'root_execute_command': command + ' --execute', 'runtime_mutations': False}
with (HERE / 'server-upload-preflight.json').open('x', encoding='utf-8') as target:
    json.dump(report, target, indent=2)
    target.write('\n')
print(json.dumps(report))
sys.exit(0 if report['ok'] else 1)
