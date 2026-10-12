"""Root-operated r13 intake packet streamed to memory; no stage/deploy/restart path."""
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
import sys

HERE=Path(__file__).resolve().parent
FROZEN=HERE.parents[1]/'candidate-r11/activation-server/root-ssh.py'
FROZEN_SHA='d6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba'
APPROVAL='r13-same-window-transition'
WRAPPER="import base64,hashlib,json,sys;p=json.loads(sys.stdin.buffer.read(1048577));raw=base64.b64decode(p['source'],validate=True);assert len(raw)<=262144 and hashlib.sha256(raw).hexdigest()==sys.argv[1];scope={'__name__':'pinned_r13_intake'};exec(compile(raw,'<pinned-memory-r13-intake>','exec'),scope);\ntry:scope['main'](p['packet'])\nexcept Exception:print(json.dumps({'phase':'r13_intake_failed','ok':False,'code':'INTAKE_TRANSITION_UNCERTAIN_READ_ONLY_INSPECT_NO_REPLAY','remote_mutation_possible':p['packet']['action']!='observe','raw_error_disclosed':False,'no_replay':True}));sys.exit(2)"
def need(ok):
    if not ok:raise ValueError()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def evidence(path,digest):
    p=Path(path);need(p.is_absolute() and p.is_file() and not p.is_symlink());raw=p.read_bytes();need(sha(raw)==digest);return json.loads(raw)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('observe','pause-rotate','reopen'))
    p.add_argument('--execute',action='store_true');p.add_argument('--operator-approved',action='store_true')
    p.add_argument('--approval-id');p.add_argument('--server');p.add_argument('--server-sha256')
    for name in ('activation-epoch','runtime-instance-id','mcp-server-instance-id','contract-version'):p.add_argument('--'+name)
    args=p.parse_args();mutate=args.action!='observe'
    if mutate:need(args.execute and args.operator_approved and args.approval_id==APPROVAL and args.server and args.server_sha256)
    else:need(not args.execute)
    m=json.loads((HERE/'helper-manifest.json').read_bytes());raw=(HERE/'transition-intake.py').read_bytes()
    need(sha(raw)==m['files']['transition-intake.py']['sha256'] and len(raw)==m['files']['transition-intake.py']['size_bytes'])
    need(sha(FROZEN.read_bytes())==FROZEN_SHA)
    spec=importlib.util.spec_from_file_location('r13_frozen_transport',FROZEN)
    t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
    packet={'action':args.action,'execute':args.execute,'operator_approved':args.operator_approved,'approval_id':args.approval_id}
    if mutate:packet.update(server=evidence(args.server,args.server_sha256),server_sha256=args.server_sha256)
    if args.action=='reopen':
        ident={key:getattr(args,key) for key in ('activation_epoch','runtime_instance_id','mcp_server_instance_id','contract_version')}
        need(all(isinstance(v,str) and v for v in ident.values()));packet['native_identity']=ident
    if mutate:
        with (HERE/('root-'+args.action+'-intent.json')).open('x',encoding='utf-8') as f:
            json.dump({'action':args.action,'approval_id':APPROVAL,'helper_sha256':sha(raw),'server_sha256':args.server_sha256,'no_replay':True},f,sort_keys=True)
            f.flush();os.fsync(f.fileno())
    payload=json.dumps({'source':base64.b64encode(raw).decode(),'packet':packet},separators=(',',':')).encode()
    ssh=shutil.which('ssh');need(ssh and isinstance(ssh,str))
    argv=['/usr/bin/python3','-B','-c',WRAPPER,sha(raw)]
    r=subprocess.run([ssh,'-T','-oBatchMode=yes','-oStrictHostKeyChecking=yes','-oConnectTimeout=15','-oServerAliveInterval=15',
        '-oServerAliveCountMax=3','svhome@100.116.112.22',shlex.join(argv)],input=payload,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90)
    need(len(r.stdout)<=65536 and b'Bearer ' not in r.stdout and b'PRIVATE KEY' not in r.stdout)
    record={'action':args.action,'public_receipts':t.safe_receipt(r.stdout),'ssh_returncode':r.returncode,
       'remote_mutation_possible':mutate,'stderr_disclosed':False,'stage_deploy_restart_requested':False,'no_replay':True}
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');directory=HERE/'remote-receipts';directory.mkdir(exist_ok=True)
    path=directory/(args.action+'-'+stamp+'.json')
    with path.open('x',encoding='utf-8') as f:json.dump(record,f,indent=2,sort_keys=True)
    print(json.dumps({'receipt_path':str(path),**record},separators=(',',':')));raise SystemExit(r.returncode)
if __name__=='__main__':
    try:main()
    except Exception:
        print('{"phase":"r13_intake_transport_failed","ok":false,"code":"UNKNOWN_OUTCOME_READ_ONLY_INSPECT_NO_REPLAY","raw_error_disclosed":false,"no_replay":true}')
        raise SystemExit(2) from None
