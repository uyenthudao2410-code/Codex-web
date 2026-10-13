"""Upload reviewed inert artifacts and run read-only rollout preflight; no deployment."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

OUT = Path(__file__).resolve().parent
receipt = json.loads((OUT / 'overlay-preparation-receipt.json').read_text())
name = receipt['verification']['release_name']
remote = '/home/svhome/.local/lib/codex-control-plane/releases/'
suffix = name.rsplit('-', 1)[-1]
files = [
    (Path(receipt['candidate_archive']), remote + name + '.tar.gz'),
    (OUT / 'overlay-preparation-receipt.json', remote + '.review-folder-overlay-' + suffix + '.json'),
    (OUT / 'deploy-reviewed-folder-overlay.py', remote + '.review-folder-overlay-' + suffix + '.py'),
]
options = ['-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', '-o', 'StrictHostKeyChecking=yes']
probe = r'''
import hashlib,json,sys
from pathlib import Path
request=json.load(sys.stdin)
for item in request:
 p=Path(item['path'])
 if p.parent!=Path('/home/svhome/.local/lib/codex-control-plane/releases') or p.is_symlink(): raise RuntimeError('UNSAFE_UPLOAD_TARGET')
 if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']: raise RuntimeError('REMOTE_ARTIFACT_ALREADY_DIFFERS')
print(json.dumps({'operation':'inert_artifact_upload_guard','passed':True,'count':len(request)}))
'''
records = [{'path': target, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()} for source, target in files]
# The Python program receives JSON as a literal argument; source code contains no credentials.
payload = json.dumps(records, separators=(',', ':'))
guard_code = probe.replace('request=json.load(sys.stdin)', 'request=json.loads(' + repr(payload) + ')')
guard = subprocess.run(['ssh.exe', '-T', *options, 'svhome@100.116.112.22', 'python3 -'],
    input=guard_code, text=True, capture_output=True, check=True)
for source, target in files:
    subprocess.run(['scp.exe', *options, str(source), 'svhome@100.116.112.22:' + target],
                   capture_output=True, check=True)
command = 'python3 -B ' + shlex.quote(files[2][1]) + ' --receipt ' + shlex.quote(files[1][1])
preflight = subprocess.run(['ssh.exe', '-T', *options, 'svhome@100.116.112.22', command],
    text=True, capture_output=True, check=True)
proof = {'operation': 'folder_overlay_inert_upload_and_readonly_preflight',
    'runtime_mutations': False, 'uploaded_artifacts': records,
    'upload_guard': json.loads(guard.stdout), 'preflight': json.loads(preflight.stdout),
    'root_rollout_command': command + ' --confirm-deploy-and-restart'}
(OUT / 'upload-and-preflight-receipt.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps(proof, separators=(',', ':')))
