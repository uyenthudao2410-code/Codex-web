"""Fetch only manifest-verified source files from svhome; never copy config or DB."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
REMOTE = r'''
import base64,hashlib,json,subprocess
from pathlib import Path
pid=int(subprocess.check_output(['systemctl','--user','show','codex-control-plane.service','--property=MainPID','--value'],text=True).strip())
if pid<=0: raise RuntimeError('SERVING_PID_UNAVAILABLE')
env=dict(item.split('=',1) for item in Path(f'/proc/{pid}/environ').read_text().split('\0') if '=' in item)
root=next(Path(p).parent for p in env.get('PYTHONPATH','').split(':') if p and (Path(p)/'control_plane'/'store.py').is_file())
raw=(root/'release-manifest.json').read_bytes()
manifest=json.loads(raw)
files={}
for record in manifest['files']:
 relative=Path(record['path'])
 if relative.is_absolute() or '..' in relative.parts: raise RuntimeError('UNSAFE_MANIFEST_PATH')
 path=root/relative
 if path.is_symlink() or not path.is_file(): raise RuntimeError('UNSAFE_RELEASE_FILE')
 content=path.read_bytes()
 if len(content)!=record['size_bytes'] or hashlib.sha256(content).hexdigest()!=record['sha256']: raise RuntimeError('BASELINE_MANIFEST_DRIFT')
 files[record['path']]=base64.b64encode(content).decode()
protected={}
for name,path in [('environment',Path.home()/'.config/codex-control-plane/control-plane.env'),('drop_in',Path.home()/'.config/systemd/user/codex-control-plane.service.d/10-immutable-release.conf')]:
 protected[name]={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
print(json.dumps({'service_pid':pid,'release_root':str(root),'manifest':manifest,'manifest_sha256':hashlib.sha256(raw).hexdigest(),'expected_package_source_sha256':env.get('CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256'),'protected_config_hashes':protected,'files':files},separators=(',',':')))
'''


def main():
    result = subprocess.run(['ssh.exe', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5',
        '-o', 'StrictHostKeyChecking=yes', 'svhome@100.116.112.22', 'python3 -'],
        input=REMOTE, text=True, capture_output=True, check=True)
    observed = json.loads(result.stdout)
    baseline = OUT / 'serving-baseline'
    baseline.mkdir(parents=True, exist_ok=True)
    for relative, encoded in observed.pop('files').items():
        path = baseline / relative
        content = base64.b64decode(encoded)
        if path.exists() and path.read_bytes() != content:
            raise RuntimeError('BASELINE_FETCH_WOULD_OVERWRITE_DIFFERENT_EVIDENCE')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    receipt = {**observed, 'operation': 'folder_activation_serving_source_read',
        'remote_mutations': False, 'baseline_directory': str(baseline)}
    (OUT / 'serving-baseline-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    (baseline / 'release-manifest.json').write_text(json.dumps(observed['manifest'], indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in receipt.items() if key != 'manifest'}, separators=(',', ':')))


if __name__ == '__main__':
    main()
