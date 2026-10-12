"""Root-only approved exact pre-effect reconciliation; credentials never leave memory except encrypted SSH stdin."""
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
import sys

HERE=Path(__file__).resolve().parent
APPROVAL='call_1KzUkF0gMn6uVpHd3QisTzXF'
CONFIG=Path(r'C:\Users\daoth\AppData\Roaming\web-mcp-assistant\control-plane-node.json')
AGENT=Path(r'E:\Github\Tools-Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-policy-contract-1012-r12\win-unpacked\resources\resources\control-plane\node_agent.py')
AGENT_SHA='bc28e81636d4d1edb35fcfd4b05e905241f4f63ba18ceac38e8c9043cce56840'
FROZEN=HERE.parents[1]/'candidate-r11/activation-server/root-ssh.py'
WRAPPER="import base64,hashlib,json,sys; p=json.loads(sys.stdin.buffer.read(1048577)); raw=base64.b64decode(p['source'],validate=True); assert len(raw)<=262144 and hashlib.sha256(raw).hexdigest()==sys.argv[1]; scope={'__name__':'pinned_settlement'}; exec(compile(raw,'<pinned-memory-settlement>','exec'),scope);\ntry: scope['main'](p['packet'])\nexcept Exception: print(json.dumps({'phase':'r12_exact_pre_effect_reconciliation_failed','ok':False,'code':'RECONCILIATION_UNCERTAIN_READ_ONLY_INSPECT_NO_RETRY','remote_mutation_possible':True,'replay_forbidden':True,'raw_error_disclosed':False}));sys.exit(2)"
def need(ok):
    if not ok:raise ValueError()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def receipt(file,digest):
    p=Path(file);need(p.is_absolute() and p.is_file() and not p.is_symlink());raw=p.read_bytes();need(sha(raw)==digest);return json.loads(raw)
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true');parser.add_argument('--operator-approved',action='store_true');parser.add_argument('--approval-id',required=True)
    for kind in ('query','native','authority'):
        parser.add_argument('--'+kind,required=True);parser.add_argument('--'+kind+'-sha256',required=True)
    args=parser.parse_args();need(args.execute and args.operator_approved and args.approval_id==APPROVAL and os.name=='nt')
    manifest=json.loads((HERE/'settlement-manifest.json').read_bytes())
    source=(HERE/'settle-exact-pre-effect.py').read_bytes();need(sha(source)==manifest['helper_sha256'])
    need(sha(FROZEN.read_bytes())=='d6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba')
    spec=importlib.util.spec_from_file_location('frozen_settle_transport',FROZEN);transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
    packet={'execute':True,'approval_id':APPROVAL}
    for kind in ('query','native','authority'):
        packet[kind]=receipt(getattr(args,kind),getattr(args,kind+'_sha256'));packet[kind+'_sha256']=getattr(args,kind+'_sha256')
    need(CONFIG.is_file() and not CONFIG.is_symlink() and AGENT.is_file() and not AGENT.is_symlink() and sha(AGENT.read_bytes())==AGENT_SHA)
    raw_config=CONFIG.read_bytes();need(len(raw_config)<=65536);config=json.loads(raw_config)
    need(config.get('device_id')=='72ceec2d-e3f2-472f-8e3c-99fffe053035' and config.get('endpoint_id')=='executor-72ceec2d-e3f2-472f-8e3c-99fffe053035'
     and config.get('server_url','').rstrip('/')=='https://svhome.tail0e4032.ts.net')
    spec=importlib.util.spec_from_file_location('pinned_dpapi_reader',AGENT);agent=importlib.util.module_from_spec(spec);sys.modules[spec.name]=agent;spec.loader.exec_module(agent)
    # Use only the existing memory-only DPAPI decoder, never _config (which may migrate a legacy file).
    protected=config.get('node_secret_dpapi');need(protected and config.get('node_secret') in (None,''))
    packet['node_secret']=agent._unprotect_node_secret(protected)
    need(CONFIG.read_bytes()==raw_config)
    intent=HERE/'root-terminal-reconciliation-intent.json'
    with intent.open('x',encoding='utf-8') as handle:
        json.dump({'approval_id':APPROVAL,'action_id':'act_6aa1329b96c146f38c807f9926b3e684','task_id':'task_d2c1dd3bff4042d084b045e9bc5a381b',
          'helper_sha256':sha(source),'evidence_sha256':{k:packet[k+'_sha256'] for k in ('query','native','authority')},'no_replay':True},handle,sort_keys=True)
        handle.flush();os.fsync(handle.fileno())
    stdin=json.dumps({'source':base64.b64encode(source).decode(),'packet':packet},separators=(',',':')).encode()
    ssh=shutil.which('ssh');need(ssh)
    argv=['/usr/bin/python3','-B','-c',WRAPPER,sha(source)]
    result=subprocess.run([ssh,'-T','-oBatchMode=yes','-oStrictHostKeyChecking=yes','-oConnectTimeout=15','-oServerAliveInterval=15',
       '-oServerAliveCountMax=3','svhome@100.116.112.22',shlex.join(argv)],input=stdin,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90)
    need(len(result.stdout)<=65536 and b'Bearer ' not in result.stdout and b'PRIVATE KEY' not in result.stdout and packet['node_secret'].encode() not in result.stdout)
    record={'phase':'root_r12_exact_terminal_reconciliation','public_receipts':transport.safe_receipt(result.stdout),
      'ssh_returncode':result.returncode,'remote_mutation_possible':True,'raw_error_disclosed':False,'credentials_saved':False,'no_replay':True}
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    with (HERE/('terminal-reconciliation-receipt-'+stamp+'.json')).open('x',encoding='utf-8') as handle:json.dump(record,handle,sort_keys=True,indent=2)
    print(json.dumps(record,separators=(',',':')));raise SystemExit(result.returncode)
if __name__=='__main__':
    try:main()
    except Exception:
        print('{"phase":"root_r12_terminal_reconciliation_failed","ok":false,"code":"UNKNOWN_OUTCOME_READ_ONLY_INSPECT_NO_RETRY","remote_mutation_possible":true,"credentials_saved":false,"no_replay":true,"raw_error_disclosed":false}')
        raise SystemExit(2) from None
