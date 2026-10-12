"""Root-only pinned stream transport; fixed read-only context diagnosis."""
import argparse
import base64
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
FROZEN=HERE.parents[1]/'candidate-r11/activation-server/root-ssh.py'
WRAPPER="import base64,hashlib,json,sys; p=json.loads(sys.stdin.buffer.read(262145)); raw=base64.b64decode(p['source'],validate=True); assert len(raw)<=131072 and hashlib.sha256(raw).hexdigest()==sys.argv[1]; scope={'__name__':'pinned_r14_read_only_context_inspection'}; exec(compile(raw,'<pinned-memory-r14-context-inspection>','exec'),scope); scope['main']()"
def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(ok):
    if not ok:raise ValueError()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--read-only',action='store_true');args=parser.parse_args()
    need(args.read_only and os.name=='nt')
    manifest=json.loads((HERE/'context-inspection-manifest.json').read_bytes())
    source=(HERE/'inspect-context-guard-r14.py').read_bytes();need(sha(source)==manifest['helper_sha256'])
    need(sha(FROZEN.read_bytes())=='d6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba')
    spec=importlib.util.spec_from_file_location('frozen_r14_read_only_safe_receipt',FROZEN)
    transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
    ssh=shutil.which('ssh');need(ssh)
    argv=['/usr/bin/python3','-B','-c',WRAPPER,sha(source)]
    result=subprocess.run([ssh,'-T','-oBatchMode=yes','-oStrictHostKeyChecking=yes','-oConnectTimeout=15',
      '-oServerAliveInterval=15','-oServerAliveCountMax=3','svhome@100.116.112.22',shlex.join(argv)],
      input=json.dumps({'source':base64.b64encode(source).decode()}).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90)
    need(len(result.stdout)<=65536 and b'Bearer ' not in result.stdout and b'PRIVATE KEY' not in result.stdout)
    record={'phase':'root_r14_context_guard_read_only_inspection','public_receipts':transport.safe_receipt(result.stdout),
      'ssh_returncode':result.returncode,'remote_mutation':False,'raw_error_disclosed':False}
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    with (HERE/('context-inspection-receipt-'+stamp+'.json')).open('x',encoding='utf-8') as handle:json.dump(record,handle,sort_keys=True,indent=2)
    print(json.dumps(record,separators=(',',':')));raise SystemExit(result.returncode)
if __name__=='__main__':
    try:main()
    except Exception:
        print('{"phase":"root_r14_context_guard_read_only_inspection_failed","ok":false,"code":"SAFE_READ_ONLY_INSPECTION_TRANSPORT_FAILED","remote_mutation":false,"raw_error_disclosed":false}')
        raise SystemExit(2) from None
