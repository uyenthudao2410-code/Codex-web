"""Capture the existing sanitized observer, including new untracked source leaves."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OBSERVER = HERE.parent / 'native-first-20261012/inspect-server-readiness.py'
output = HERE / sys.argv[1]
if output.parent != HERE or output.exists():
    raise RuntimeError('NEW_REPORT_PATH_REQUIRED')
source = OBSERVER.read_bytes()
ast.parse(source)
result = subprocess.run(['ssh.exe', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=yes', 'svhome@100.116.112.22', 'python3', '-B', '-'], input=source, capture_output=True, timeout=55)
if len(result.stdout) > 262144:
    raise RuntimeError('OBSERVER_RESPONSE_TOO_LARGE')
report = json.loads(result.stdout)
if report.get('operation') != 'native_first_ubuntu_readonly_readiness':
    raise RuntimeError('SANITIZED_OBSERVER_RESPONSE_REQUIRED')
report['local_observation'] = {'ssh_exit_code': result.returncode,
    'captured_utc': datetime.now(timezone.utc).isoformat(), 'observer_sha256': hashlib.sha256(source).hexdigest(),
    'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'current_python_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((ROOT / 'control-plane/control_plane').glob('*.py'))}}
with output.open('x', encoding='utf-8', newline='\n') as handle:
    json.dump(report, handle, indent=2)
    handle.write('\n')
print(json.dumps({'ok': report.get('ok'), 'report': str(output), 'service_pid': report.get('service_pid'), 'error_code': report.get('error_code')}))
sys.exit(0 if result.returncode == 0 and report.get('ok') else 1)
