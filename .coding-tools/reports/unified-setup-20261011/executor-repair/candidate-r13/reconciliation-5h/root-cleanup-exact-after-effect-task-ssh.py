"""Root-only exact task/writer cleanup after observed failed settlement; never post a receipt."""
from pathlib import Path
import argparse
import base64
import datetime
import hashlib
import importlib.util
import json
import os
import shlex
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
APPROVAL='call_a60e931056bd402b997c6c10b0796d81'
FROZEN=HERE.parents[1]/'candidate-r11/activation-server/root-ssh.py'
SETTLEMENT='30f0169c0acb39bb888178e1326a220d175d936a39208397f358eb1eb0b0ed0f'
CANARY='cd91a622d76f19873adc4c7671f6b72d59ba99cac639957c04a1413cb06df104'
AUTHORITY=HERE.parent/'authority-5h/remote-receipts/reopen-20261011T225252535254Z.json'
AUTHORITY_SHA='25bc940304dcede5896099db40f09f9449615834c2f3d82644de2e9b1d2335b0'
WRAPPER="import base64,hashlib,json,sys; p=json.loads(sys.stdin.buffer.read(1048577)); raw=base64.b64decode(p['source'],validate=True); assert len(raw)<=262144 and hashlib.sha256(raw).hexdigest()==sys.argv[1]; scope={'__name__':'pinned_exact_task_cleanup'}; exec(compile(raw,'<pinned-memory-exact-task-cleanup>','exec'),scope);\ntry: scope['main'](p['packet'])\nexcept Exception: print(json.dumps({'phase':'r13_5h_exact_task_only_cleanup','ok':False,'code':'TASK_CLEANUP_UNCERTAIN_READ_ONLY_INSPECT_NO_RETRY','remote_mutation_possible':True,'replay_forbidden':True,'raw_error_disclosed':False}));sys.exit(2)"
def need(ok):
    if not ok:raise ValueError()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pinned(path,digest):
    need(path.is_file() and not path.is_symlink());raw=path.read_bytes()
    need(len(raw)<=262144 and sha(raw)==digest);return raw

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true')
    p.add_argument('--approval-id',required=True);p.add_argument('--inspection',required=True);p.add_argument('--inspection-sha256',required=True)
    args=p.parse_args();need(args.execute and args.approval_id==APPROVAL and os.name=='nt')
    manifest=json.loads((HERE/'task-cleanup-manifest.json').read_bytes());need(manifest.get('ready_for_execution') is True)
    source=pinned(HERE/'cleanup-exact-after-effect-task.py',manifest['helper_sha256'])
    inspection_path=Path(args.inspection);need(inspection_path.is_absolute())
    packet={'execute':True,'approval_id':APPROVAL,'inspection':json.loads(pinned(inspection_path,args.inspection_sha256)),
      'inspection_sha256':args.inspection_sha256,'authority':json.loads(pinned(AUTHORITY,AUTHORITY_SHA)),
      'authority_sha256':AUTHORITY_SHA,'settlement_source_b64':base64.b64encode(pinned(HERE/'settle-exact-after-effect.py',SETTLEMENT)).decode(),
      'settlement_source_sha256':SETTLEMENT,'canary_source_b64':base64.b64encode(pinned(HERE.parent/'canary-5h/r13_5h_mcp_canary.py',CANARY)).decode(),
      'canary_source_sha256':CANARY}
    pinned(FROZEN,'d6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba')
    spec=importlib.util.spec_from_file_location('frozen_exact_task_cleanup_transport',FROZEN)
    transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
    intent={'approval_id':APPROVAL,'action_id':'act_b2335c57472b4d68931d10dda1572ff9','task_id':'task_3b2a2a860ca54ef7889d2efce6923dc7',
      'helper_sha256':sha(source),'inspection_sha256':args.inspection_sha256,'authority_sha256':AUTHORITY_SHA,'no_replay':True}
    raw=json.dumps(intent,sort_keys=True,separators=(',',':')).encode()
    with (HERE/'root-exact-task-cleanup-intent.json').open('xb') as handle:
        handle.write(raw);handle.flush();os.fsync(handle.fileno())
    packet['root_intent']=intent;packet['root_intent_sha256']=sha(raw)
    stdin=json.dumps({'source':base64.b64encode(source).decode(),'packet':packet},separators=(',',':')).encode();need(len(stdin)<=1048576)
    ssh=shutil.which('ssh');need(ssh)
    argv=['/usr/bin/python3','-B','-c',WRAPPER,sha(source)]
    result=subprocess.run([ssh,'-T','-oBatchMode=yes','-oStrictHostKeyChecking=yes','-oConnectTimeout=15',
      '-oServerAliveInterval=15','-oServerAliveCountMax=3','svhome@100.116.112.22',shlex.join(argv)],
      input=stdin,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90)
    need(len(result.stdout)<=65536 and b'Bearer ' not in result.stdout and b'PRIVATE KEY' not in result.stdout)
    record={'phase':'root_r13_5h_exact_task_only_cleanup','public_receipts':transport.safe_receipt(result.stdout),
      'ssh_returncode':result.returncode,'remote_mutation_possible':True,'receipt_posted':False,'raw_error_disclosed':False,'replay_forbidden':True}
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    with (HERE/('task-cleanup-receipt-'+stamp+'.json')).open('x',encoding='utf-8') as handle:json.dump(record,handle,sort_keys=True,indent=2)
    print(json.dumps(record,separators=(',',':')));raise SystemExit(result.returncode)
if __name__=='__main__':
    try:main()
    except Exception:
        print('{"phase":"root_r13_5h_exact_task_only_cleanup","ok":false,"code":"TASK_CLEANUP_UNCERTAIN_READ_ONLY_INSPECT_NO_RETRY","remote_mutation_possible":true,"receipt_posted":false,"raw_error_disclosed":false,"replay_forbidden":true}')
        raise SystemExit(2) from None
