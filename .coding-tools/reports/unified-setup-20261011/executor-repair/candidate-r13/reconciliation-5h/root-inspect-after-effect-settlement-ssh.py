"""Root-only bounded read-only inspection after uncertain exact settlement; no replay."""
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
PINS={
 'query':('query-receipt-20261011T225840992295Z.json','9cab482e03bc6bd7e7d679eff7cb496bda243be0be5533409aca9e6453b64384'),
 'native':('native-correlation-1791759968554973600.json','8c081b83dfcb075e3b8f7588cb15d9dbc4274d472d5551c0e60985b4a1beaa6c'),
 'root_intent':('root-after-effect-terminal-reconciliation-intent.json','58dd54ddf1bc7c368ea7ac7270b3c43921b0afc88fb34a0cf20910072d382bd8'),
 'authority':('../authority-5h/remote-receipts/reopen-20261011T225252535254Z.json','25bc940304dcede5896099db40f09f9449615834c2f3d82644de2e9b1d2335b0')
}
SETTLEMENT_SHA='30f0169c0acb39bb888178e1326a220d175d936a39208397f358eb1eb0b0ed0f'
WRAPPER="import base64,hashlib,json,sys; p=json.loads(sys.stdin.buffer.read(1048577)); raw=base64.b64decode(p['source'],validate=True); assert len(raw)<=262144 and hashlib.sha256(raw).hexdigest()==sys.argv[1]; scope={'__name__':'pinned_readonly_inspector'}; exec(compile(raw,'<pinned-memory-readonly-inspection>','exec'),scope);\ntry: scope['main'](p['packet'])\nexcept Exception: print(json.dumps({'phase':'r13_5h_after_effect_settlement_read_only_inspection','ok':False,'code':'SAFE_READ_ONLY_INSPECTION_FAILED','remote_mutation':False,'replay_forbidden':True,'raw_error_disclosed':False}));sys.exit(2)"

def need(ok):
    if not ok:raise ValueError()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pinned(path,digest):
    need(path.is_file() and not path.is_symlink())
    raw=path.read_bytes();need(len(raw)<=262144 and sha(raw)==digest);return raw

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--read-only',action='store_true');parser.add_argument('--approval-id',required=True)
    args=parser.parse_args();need(args.read_only and args.approval_id==APPROVAL and os.name=='nt')
    manifest=json.loads((HERE/'inspection-manifest.json').read_bytes());need(manifest.get('ready_for_read_only') is True)
    source=pinned(HERE/'inspect-after-effect-settlement.py',manifest['inspector_sha256'])
    settlement=pinned(HERE/'settle-exact-after-effect.py',SETTLEMENT_SHA)
    packet={'approval_id':APPROVAL,'read_only':True,'settlement_source_b64':base64.b64encode(settlement).decode(),
      'settlement_source_sha256':SETTLEMENT_SHA}
    for kind,(name,digest) in PINS.items():
        packet[kind]=json.loads(pinned(HERE/name,digest));packet[kind+'_sha256']=digest
    pinned(FROZEN,'d6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba')
    spec=importlib.util.spec_from_file_location('frozen_readonly_inspection_transport',FROZEN)
    transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
    stdin=json.dumps({'source':base64.b64encode(source).decode(),'packet':packet},separators=(',',':')).encode()
    need(len(stdin)<=1048576)
    ssh=shutil.which('ssh');need(ssh)
    argv=['/usr/bin/python3','-B','-c',WRAPPER,sha(source)]
    result=subprocess.run([ssh,'-T','-oBatchMode=yes','-oStrictHostKeyChecking=yes','-oConnectTimeout=15',
      '-oServerAliveInterval=15','-oServerAliveCountMax=2','svhome@100.116.112.22',shlex.join(argv)],
      input=stdin,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
    need(len(result.stdout)<=65536 and b'Bearer ' not in result.stdout and b'PRIVATE KEY' not in result.stdout)
    record={'phase':'root_r13_5h_after_effect_settlement_read_only_inspection',
      'public_receipts':transport.safe_receipt(result.stdout),'ssh_returncode':result.returncode,
      'remote_mutation':False,'staged_files':False,'stderr_disclosed':False,'replay_forbidden':True,
      'inspector_sha256':sha(source),'immutable_root_intent_sha256':PINS['root_intent'][1]}
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    with (HERE/('inspection-receipt-'+stamp+'.json')).open('x',encoding='utf-8') as handle:
        json.dump(record,handle,sort_keys=True,indent=2)
    print(json.dumps(record,separators=(',',':')));raise SystemExit(result.returncode)

if __name__=='__main__':
    try:main()
    except Exception:
        print('{"phase":"root_r13_5h_after_effect_settlement_read_only_inspection","ok":false,"code":"SAFE_READ_ONLY_INSPECTION_FAILED","remote_mutation":false,"stderr_disclosed":false,"replay_forbidden":true}')
        raise SystemExit(2) from None
