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
PREVIOUS=HERE.parent/'activation-server-same-window'
FAILED_RECEIPT=PREVIOUS/'close-receipt-20261011T235132676605Z.json'
FAILED_RECEIPT_SHA='2b2017be367f07294bc851fd134116f2b6a8983c236ab813665cf2e3da873af7'
FAILED_INTENT=PREVIOUS/'root-close-intent.json'
FAILED_INTENT_SHA='5fba40ab07066770aafc9b612c0a07490c1aa5e65d14e7a34d1f280afa32ea9d'
INSPECTION=PREVIOUS/'context-inspection-receipt-20261011T235529216835Z.json'
INSPECTION_SHA='0e7c8f027fac258ef34a68f1f850ff07acca51328dcbbf59fd50fc06eea18cf9'
WRAPPER="import base64,hashlib,json,sys; p=json.loads(sys.stdin.buffer.read(1048577)); raw=base64.b64decode(p['source'],validate=True); assert len(raw)<=262144 and hashlib.sha256(raw).hexdigest()==sys.argv[1]; scope={'__name__':'pinned_r14_server_transition'}; exec(compile(raw,'<pinned-memory-r14-transition>','exec'),scope);\ntry: scope['main'](p['packet'])\nexcept Exception: print(json.dumps({'phase':'r14_same_window_transition_failed','ok':False,'code':'R14_PHASE_UNCERTAIN_READ_ONLY_INSPECT_NO_REPLAY','remote_mutation_possible':p['packet'].get('execute',False),'raw_error_disclosed':False,'replay_forbidden':True}));sys.exit(2)"
def need(ok):
    if not ok:raise ValueError()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pinned(path,digest):
    p=Path(path);need(p.is_absolute() and p.is_file() and not p.is_symlink());raw=p.read_bytes()
    need(len(raw)<=262144 and sha(raw)==digest);return raw
def prior_failure_reconciled(approval_id):
    failed=json.loads(pinned(FAILED_RECEIPT,FAILED_RECEIPT_SHA))
    need(failed.get('ssh_returncode')==2 and len(failed.get('public_receipts',[]))==1)
    row=failed['public_receipts'][0]
    need(row.get('ok') is False and row.get('operation')=='close' and row.get('stage')=='input'
      and row.get('code')=='UNCHANGED_EXACT_CONTEXT_REQUIRED')
    intent=json.loads(pinned(FAILED_INTENT,FAILED_INTENT_SHA));need(intent.get('phase')=='close' and intent.get('approval_id')==approval_id)
    inspected=json.loads(pinned(INSPECTION,INSPECTION_SHA))
    need(inspected.get('ssh_returncode')==0 and inspected.get('remote_mutation') is False and len(inspected.get('public_receipts',[]))==1)
    observation=inspected['public_receipts'][0]
    need(observation.get('ok') is True and observation.get('remote_mutation') is False
      and observation.get('server_rows_preserved') is True and observation.get('no_mutation_or_replay_performed') is True
      and observation.get('admission')=='scoped_pilot' and observation.get('context_id')=='ctx_1e7e2fec6f0e43018db7a51c6980e5c2'
      and observation.get('expected_expires_at_ms')==1791776571067 and observation.get('live_unclosed_target_context_count')==1
      and observation.get('expired_unclosed_target_context_count')==1)
    need(set(observation.get('remote_phase_files',{}))=={'close-intent.json','replace-intent.json','reopen-intent.json','authority-transition-public.json'}
      and all(r.get('exists') is False for r in observation['remote_phase_files'].values()))
    pilots=observation.get('all_unrevoked_pilots',[])
    need(len(pilots)==1 and pilots[0].get('decision_id')=='pilot_b1cb26c319fb489aae24d3b746318447')
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
        if args.phase=='close':prior_failure_reconciled(args.approval_id)
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
        if args.phase=='close':intent['prior_failure_reconciliation_sha256']={'failed_receipt':FAILED_RECEIPT_SHA,'failed_intent':FAILED_INTENT_SHA,'read_only_inspection':INSPECTION_SHA}
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
