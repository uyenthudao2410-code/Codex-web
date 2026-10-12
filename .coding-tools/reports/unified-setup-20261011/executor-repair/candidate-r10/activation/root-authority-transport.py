"""Exact-byte SSH transport for the reviewed, approved r10 authority packet."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[5]
HELPER = BASE.parent.parent / 'store-delta/ubuntu-r10-store-authority-v3-local-proof.py'
HELPER_SHA = 'a312575854fee785158fa21624a096d7b09ae3701ded38f449a7330ba089ebec'
LOCAL = BASE / 'activate-r10-v2.cjs'
LOCAL_SHA = '4b689f8533f1de77130257543b408aec43b3f91e79579015a7a10a054db06b05'
REMOTE = '/home/svhome/.local/lib/codex-control-plane/incoming/r10-approved-20261011T123342Z/ubuntu-r10-store-authority-v3-local-proof.py'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10', 'svhome@100.116.112.22']
OLD_EPOCH = 'activation-mv3qe36p-991f11f44f47d32ea2e217b1db882ff7'
SERVICE = 'cp_6766892f5ada47d1862a0d24334f1116'

def require(value, code):
    if not value:
        raise RuntimeError(code)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def remote(argv, raw=b''):
    result = subprocess.run(SSH + [shlex.join(argv)], input=raw, capture_output=True, timeout=150)
    require(len(result.stdout) <= 131072, 'REMOTE_OUTPUT_TOO_LARGE')
    rows = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    require(rows, 'NO_PUBLIC_REMOTE_RECEIPT')
    # Reviewed helper emits only public receipts; never emit stderr.
    return result, rows

def save(name, raw):
    with (BASE / name).open('xb') as handle:
        handle.write(raw)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['stage', 'observe', 'close', 'renew', 'reopen'])
    parser.add_argument('--epoch')
    args = parser.parse_args()
    require(sha(HELPER.read_bytes()) == HELPER_SHA, 'SERVER_HELPER_CHANGED')
    require(sha(LOCAL.read_bytes()) == LOCAL_SHA, 'LOCAL_HELPER_CHANGED')
    if args.action == 'stage':
        code = """from pathlib import Path
import os,sys,hashlib,json,stat
p=Path(sys.argv[1]); expected=sys.argv[2]; raw=sys.stdin.buffer.read(131073)
assert len(raw)<=131072 and hashlib.sha256(raw).hexdigest()==expected
s=p.parent.lstat(); assert stat.S_ISDIR(s.st_mode) and not p.parent.is_symlink() and s.st_uid==os.getuid() and s.st_mode & 0o077 == 0
if p.exists():
 assert not p.is_symlink() and p.stat().st_uid==os.getuid() and p.stat().st_mode & 0o077 == 0 and p.read_bytes()==raw
else:
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as h: h.write(raw)
assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
print(json.dumps({'phase':'r10_authority_helper_staged','ok':True,'sha256':expected}))
"""
        result, rows = remote(['python3', '-B', '-c', code, REMOTE, HELPER_SHA], HELPER.read_bytes())
        require(result.returncode == 0 and rows[-1].get('ok') is True, 'STAGING_FAILED')
        print(json.dumps(rows[-1]))
        return
    command = ['python3', '-B', REMOTE, args.action]
    raw = b''
    proof_name = None
    if args.action != 'observe':
        preflight = json.loads((BASE / 'server-preflight.json').read_bytes())
        require(preflight['service_instance_id'] == SERVICE and preflight['ok'] is True, 'PREFLIGHT_SERVICE_CHANGED')
        state_sha = preflight['state_sha256']
        require(re.fullmatch('[a-f0-9]{64}', state_sha), 'STATE_HASH_INVALID')
        epoch = OLD_EPOCH
        if args.action in {'close', 'renew'}:
            generated = subprocess.run(['node', str(LOCAL), 'server-preparation-proof'], cwd=REPO, capture_output=True, timeout=180)
            receipts = [json.loads(line) for line in generated.stdout.splitlines() if line.strip()]
            require(generated.returncode == 0 and receipts[-1].get('phase') == 'server_preparation_proof_saved', 'LOCAL_PREPARATION_FAILED')
            proof = Path(receipts[-1]['file'])
            require(proof.parent == BASE and re.fullmatch('server-preparation-proof-[0-9TZ]+\\.json', proof.name), 'LOCAL_PROOF_PATH_INVALID')
            raw = proof.read_bytes()
            require(sha(raw) == receipts[-1]['proof_sha256'], 'LOCAL_PROOF_HASH_CHANGED')
            proof_name = proof.name
            command += ['--local-preparation-stdin', '--expected-local-preparation-sha256', sha(raw)]
        else:
            require(args.epoch and re.fullmatch('activation-[a-zA-Z0-9-]+', args.epoch) and args.epoch != OLD_EPOCH, 'NEW_EPOCH_REQUIRED')
            epoch = args.epoch
        command += ['--execute', '--operator-approved', '--expected-service-instance', SERVICE,
                    '--expected-state-sha256', state_sha, '--expected-activation-epoch', epoch]
    result, rows = remote(command, raw)
    name = {'observe':'server-preflight.json', 'close':'server-intake-closed.json',
            'renew':'server-authority-renewal.json', 'reopen':'server-intake-reopened.json'}[args.action]
    # Preserve exact emitted bytes for pins; failed receipts use distinct immutable names.
    if result.returncode != 0 or rows[-1].get('ok') is not True:
        from datetime import datetime, timezone
        name = 'server-' + args.action + '-failed-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.jsonl'
        save(name, result.stdout)
        print(json.dumps({'ok':False,'code':rows[-1].get('code','REMOTE_REFUSED'),'receipt':name,'local_proof':proof_name}))
        raise SystemExit(2)
    save(name, result.stdout)
    print(json.dumps({'ok':True,'phase':rows[-1]['phase'],'receipt':name,'sha256':sha(result.stdout),
                      'local_proof':proof_name,'public_receipt':rows[-1]}))

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'ok':False,'code':str(error) if isinstance(error,RuntimeError) else 'TRANSPORT_FAILED','no_automatic_retry':True}))
        raise SystemExit(2) from None
