"""Root-only creation of the missing receipt directory; no task or authority effects."""
import hashlib
import json
import pathlib
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone

REMOTE = r'''
import hashlib,json,os,pathlib,pwd,stat,time
parent=pathlib.Path('/home/svhome/.local/state/codex-control-plane/owner-operations/r11-initial-verification-next-60m')
child=parent/'canary-after-contract-sync'
marker=parent/'authority-renewal-public.json'
def need(ok,code):
 if not ok: raise RuntimeError(code)
try:
 need(pwd.getpwuid(os.getuid()).pw_name=='svhome','SSH_USER_CHANGED')
 for p in [*reversed(parent.parents),parent]:
  need(p.is_dir() and not p.is_symlink(),'PARENT_SYMLINK_OR_MISSING')
 need(parent.stat().st_uid==os.getuid() and stat.S_IMODE(parent.stat().st_mode)==0o700,'PARENT_PRIVATE_MODE_CHANGED')
 need(marker.is_file() and not marker.is_symlink() and marker.stat().st_uid==os.getuid() and stat.S_IMODE(marker.stat().st_mode) in (0o400,0o600),'AUTHORITY_MARKER_UNSAFE')
 raw=marker.read_bytes()
 need(hashlib.sha256(raw).hexdigest()=='e3d29f73b0395dd47ff46dd9bbb62831afce0a14183d23c2cd0ca88c5ceaf34c','AUTHORITY_MARKER_CHANGED')
 value=json.loads(raw)
 need(value['phase']=='intake_reopened' and value['approval_id']=='call_flEpmLChKJPZsbnlAAXR5byS' and value['expires_at_ms']==1791739329910 and int(time.time()*1000)<1791739329910-120000,'APPROVED_WINDOW_CHANGED_OR_TOO_SHORT')
 need(not child.exists() and not child.is_symlink(),'CHILD_ALREADY_EXISTS_NO_RETRY')
 child.mkdir(mode=0o700)
 need(child.stat().st_uid==os.getuid() and stat.S_IMODE(child.stat().st_mode)==0o700 and not child.is_symlink() and not any(child.iterdir()),'CHILD_POSTCONDITION_FAILED')
 need(marker.read_bytes()==raw,'AUTHORITY_MARKER_CHANGED_DURING_BOOTSTRAP')
 descriptor=os.open(parent,os.O_RDONLY|os.O_DIRECTORY)
 try: os.fsync(descriptor)
 finally: os.close(descriptor)
 print(json.dumps({'ok':True,'phase':'canary_receipt_directory_created','path':str(child),'mode':'0700','authority_marker_unchanged':True,'task_or_action_created':False,'remote_mutation':True}))
except Exception as error:
 print(json.dumps({'ok':False,'phase':'canary_directory_bootstrap_refused','code':str(error) if isinstance(error,RuntimeError) else 'BOOTSTRAP_FAILED','no_automatic_retry':True}))
 raise SystemExit(2)
'''

def main():
    if sys.argv[1:] != ['--execute-approved-r11']:
        raise SystemExit('EXPLICIT_ROOT_EXECUTION_REQUIRED')
    out = pathlib.Path(__file__).resolve().parent / 'canary-directory-bootstrap'
    out.mkdir(exist_ok=True)
    intent = out / 'intent.json'
    with intent.open('x', encoding='utf-8') as handle:
        json.dump({'operation':'create_missing_canary_receipt_directory','helper_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'no_automatic_retry':True},handle)
    result = subprocess.run([shutil.which('ssh'),'-T','-oBatchMode=yes','-oStrictHostKeyChecking=yes','-oConnectTimeout=15','svhome@100.116.112.22',shlex.join(['/usr/bin/python3','-B','-c',REMOTE])],capture_output=True,timeout=30)
    rows = [json.loads(line) for line in result.stdout.decode().splitlines() if line.strip().startswith('{')]
    if len(rows) != 1:
        raise SystemExit('BOOTSTRAP_UNCERTAIN_NO_RETRY')
    row = {'observed_at_utc':datetime.now(timezone.utc).isoformat(),'ssh_returncode':result.returncode,'stderr_disclosed':False,'public_receipt':rows[0]}
    with (out / 'receipt.json').open('x',encoding='utf-8') as handle:
        json.dump(row,handle,indent=2)
    print(json.dumps(row))
    return 0 if result.returncode == 0 and rows[0].get('ok') is True else 2

if __name__ == '__main__':
    sys.exit(main())
