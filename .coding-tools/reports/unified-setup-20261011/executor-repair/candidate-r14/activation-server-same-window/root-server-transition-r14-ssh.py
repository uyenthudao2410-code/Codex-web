"""Root stream transport for exact r14 admission phases; protected values stay on server."""
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
FROZEN=HERE.parents[1]/'candidate-r11/activation-server/root-ssh.py'
AUTHORITY=HERE.parents[1]/'candidate-r13/authority-5h/remote-receipts/reopen-20261011T225252535254Z.json'
AUTHORITY_SHA='25bc940304dcede5896099db40f09f9449615834c2f3d82644de2e9b1d2335b0'
WRAPPER="import base64,hashlib,json,sys; p=json.loads(sys.stdin.buffer.read(1048577)); raw=base64.b64decode(p['source'],validate=True); assert len(raw)<=262144 and hashlib.sha256(raw).hexdigest()==sys.argv[1]; scope={'__name__':'pinned_r14_server_transition'}; exec(compile(raw,'<pinned-memory-r14-transition>','exec'),scope);\ntry: scope['main'](p['packet'])\nexcept Exception: print(json.dumps({'phase':'r14_same_window_transition_failed','ok':False,'code':'R14_PHASE_UNCERTAIN_READ_ONLY_INSPECT_NO_REPLAY','remote_mutation_possible':p['packet'].get('execute',False),'raw_error_disclosed':False,'replay_forbidden':True}));sys.exit(2)"
def need(ok):
    if not ok:raise ValueError()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pinned(path,digest):
    p=Path(path);need(p.is_absolute() and p.is_file() and not p.is_symlink());raw=p.read_bytes()
    need(len(raw)<=262144 and sha(raw)==digest);return raw
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=('observe','close','replace','reopen'))
    p.add_argument('--execute',action='store_true');p.add_argument('--read-only',action='store_true')
    p.add_argument('--approval-id')
    for kind in ('approval','windows','server'):
        p.add_argument('--'+kind);p.add_argument('--'+kind+'-sha256')
    args=p.parse_args();need(os.name=='nt')
    mutation=args.phase!='observe';need(args.execute and not args.read_only if mutation else args.read_only and not args.execute)
    manifest=json.loads((HERE/'helper-manifest.json').read_bytes())
    need(manifest.get('ready_for_execution') is True)
    source=pinned(HERE/'server-transition-r14.py',manifest['helper_sha256'])
    packet={'phase':args.phase,'execute':mutation,'authority':json.loads(pinned(AUTHORITY,AUTHORITY_SHA)),
      'authority_sha256':AUTHORITY_SHA}
    if mutation:
        need(args.approval_id);packet['approval_id']=args.approval_id
        for kind in ('approval','windows'):
            value=getattr(args,kind);digest=getattr(args,kind+'_sha256');need(value and digest)
            packet[kind]=json.loads(pinned(value,digest));packet[kind+'_sha256']=digest
        if args.phase!='close':
            need(args.server and args.server_sha256);packet['server']=json.loads(pinned(args.server,args.server_sha256));packet['server_sha256']=args.server_sha256
    pinned(FROZEN,'d6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba')
    spec=importlib.util.spec_from_file_location('frozen_r14_server_stream_transport',FROZEN)
    transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
    if mutation:
        intent={'phase':args.phase,'approval_id':args.approval_id,'helper_sha256':sha(source),
          'input_sha256':{k:packet[k+'_sha256'] for k in ('approval','windows','authority')},'no_replay':True}
        if args.phase!='close':intent['input_sha256']['server']=args.server_sha256
        with (HERE/('root-'+args.phase+'-intent.json')).open('x',encoding='utf-8') as handle:
            json.dump(intent,handle,sort_keys=True);handle.flush();os.fsync(handle.fileno())
    stdin=json.dumps({'source':base64.b64encode(source).decode(),'packet':packet},separators=(',',':')).encode();need(len(stdin)<=1048576)
    ssh=shutil.which('ssh');need(ssh)
    argv=['/usr/bin/python3','-B','-c',WRAPPER,sha(source)]
    result=subprocess.run([ssh,'-T','-oBatchMode=yes','-oStrictHostKeyChecking=yes','-oConnectTimeout=15',
      '-oServerAliveInterval=15','-oServerAliveCountMax=3','svhome@100.116.112.22',shlex.join(argv)],
      input=stdin,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90)
    need(len(result.stdout)<=65536 and b'Bearer ' not in result.stdout and b'PRIVATE KEY' not in result.stdout)
    record={'phase':'root_r14_same_window_server_'+args.phase,'public_receipts':transport.safe_receipt(result.stdout),
      'ssh_returncode':result.returncode,'remote_mutation_possible':mutation,'raw_error_disclosed':False,'replay_forbidden':True}
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    with (HERE/(args.phase+'-receipt-'+stamp+'.json')).open('x',encoding='utf-8') as handle:json.dump(record,handle,sort_keys=True,indent=2)
    print(json.dumps(record,separators=(',',':')));raise SystemExit(result.returncode)
if __name__=='__main__':
    try:main()
    except Exception:
        print('{"phase":"root_r14_same_window_server_transport_failed","ok":false,"code":"SAFE_ROOT_TRANSPORT_FAILED_READ_ONLY_INSPECT_NO_REPLAY","remote_mutation_possible":true,"raw_error_disclosed":false,"replay_forbidden":true}')
        raise SystemExit(2) from None
