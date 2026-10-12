"""Root-only approved exact after-effect reconciliation; credentials never leave memory except encrypted SSH stdin."""
from pathlib import Path
import argparse
import base64
import datetime
import hashlib
import importlib.util
import json
import os
import sqlite3
from contextlib import closing
import time
import zlib
import shlex
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
APPROVAL='call_a60e931056bd402b997c6c10b0796d81'
CONFIG=Path(r'C:\Users\daoth\AppData\Roaming\web-mcp-assistant\control-plane-node.json')
AGENT=Path(r'E:\Github\Tools-Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-source-fingerprint-1012-r13\win-unpacked\resources\resources\control-plane\node_agent.py')
AGENT_SHA='bc28e81636d4d1edb35fcfd4b05e905241f4f63ba18ceac38e8c9043cce56840'
FROZEN=HERE.parents[1]/'candidate-r11/activation-server/root-ssh.py'
WRAPPER="import base64,hashlib,json,sys; p=json.loads(sys.stdin.buffer.read(1048577)); raw=base64.b64decode(p['source'],validate=True); assert len(raw)<=262144 and hashlib.sha256(raw).hexdigest()==sys.argv[1]; scope={'__name__':'pinned_settlement'}; exec(compile(raw,'<pinned-memory-settlement>','exec'),scope);\ntry: scope['main'](p['packet'])\nexcept Exception: print(json.dumps({'phase':'r13_5h_exact_after_effect_reconciliation_failed','ok':False,'code':'RECONCILIATION_UNCERTAIN_READ_ONLY_INSPECT_NO_RETRY','remote_mutation_possible':True,'replay_forbidden':True,'raw_error_disclosed':False}));sys.exit(2)"
def need(ok):
    if not ok:raise ValueError()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def receipt(file,digest):
    p=Path(file);need(p.is_absolute() and p.is_file() and not p.is_symlink());raw=p.read_bytes();need(sha(raw)==digest);return json.loads(raw)
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def current_native_identity(native):
    script=HERE/'root-native-identity-read.cjs';node=Path(r'C:\Program Files\nodejs\node.exe')
    need(script.is_file() and not script.is_symlink() and sha(script.read_bytes())=='af83560e2b6bac7784dbe9125459aefcc7a8f1579111715b7cd234c98ad90f17')
    need(node.is_absolute() and node.is_file() and not node.is_symlink() and node.resolve(strict=True)==node)
    result=subprocess.run([str(node),str(script)],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
      timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),shell=False)
    need(result.returncode==0 and 0<len(result.stdout)<=8192 and b'Bearer ' not in result.stdout and b'PRIVATE KEY' not in result.stdout)
    value=json.loads(result.stdout)
    need(set(value)=={'ok','kind','observed_at_ms','native_identity','current_identity','mcp_ready','host_owner_pid',
      'host_process_verified','authenticated_read_only','activation_performed','acceptance_performed','mutated_canonical_ledger','secret_values_emitted'})
    need(value['ok'] is True and value['kind']=='r13_5h_root_current_native_identity_read_only'
     and value['native_identity']==native['native_identity'] and type(value['observed_at_ms']) is int
     and 0<=int(time.time()*1000)-value['observed_at_ms']<60000
     and all(value[key] is True for key in ('current_identity','mcp_ready','host_process_verified','authenticated_read_only'))
     and all(value[key] is False for key in ('activation_performed','acceptance_performed','mutated_canonical_ledger','secret_values_emitted')))
    return value

def local_census(native):
    repository=Path(r'E:\Github\Tools-Codex-web');ledger=repository/'.coding-tools/orchestration/ledger.sqlite3'
    need(ledger.is_file() and not ledger.is_symlink())
    with closing(sqlite3.connect(ledger.resolve(strict=True).as_uri()+'?mode=ro',uri=True,timeout=5)) as db:
        db.row_factory=sqlite3.Row;db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
        active=db.execute("SELECT COUNT(*) FROM managed_process_jobs WHERE lifecycle_state IN ('starting','active','waiting','idle','running','orphaned')").fetchone()[0]
        need(active==0)
        old={}
        for table,column,key in [('runs','run_id','95e909f0040a448faa9f1f3257e2ee2c'),('waves','wave_id','c101beadfc6d4f2fbc13845052c84693')]:
            rows=db.execute('SELECT * FROM '+table+' WHERE '+column+'=?',(key,)).fetchall();need(len(rows)==1)
            old[table]=sha(canonical(dict(rows[0])))
        jobs=db.execute('SELECT * FROM managed_process_jobs WHERE job_id=? AND command_id=?',('e0d55c2194fa404eae7f3f4dcaf383bf','mSj-X1p4ZcQ97Q_TX-xnzzUD')).fetchall();need(len(jobs)==1)
        proofs=db.execute('SELECT * FROM proofs WHERE proof_id=? AND run_id=? AND wave_id=?',('796459e8115c431e993f577c27992750','fbaf4b0700d04794af4062671c1bcd2b','e712eca9463e465fb1905264c998f50c')).fetchall();need(len(proofs)==1)
        job=dict(jobs[0]);proof=dict(proofs[0]);need(job['lifecycle_state']=='exited' and proof['status']=='passed' and proof['exit_code']==0)
        records=db.execute("SELECT * FROM idempotency_records WHERE idempotency_key=? AND operation='agent_workflow' AND run_id=? AND wave_id=?",
         ('cpap_36e1306a273cfffb7594fdc1ee64889d01f6439e7223c9506a432414','fbaf4b0700d04794af4062671c1bcd2b','e712eca9463e465fb1905264c998f50c')).fetchall()
        need(len(records)==1);record=dict(records[0])
        need(record['status']=='completed' and record['request_hash']=='efe791944feb94101e060b86d95edeef140d7a94c4bc2fc699a68178735e0023'
         and record['process_instance_id']==native['native_identity']['process_instance_id'] and record['error_code']=='')
        if record['summary_codec']=='plain_json':
            summary_raw=record['summary_json'].encode();need(len(summary_raw)<=1048576)
        else:
            need(record['summary_codec']=='zlib_json' and isinstance(record['summary_blob'],bytes))
            decoder=zlib.decompressobj();summary_raw=decoder.decompress(record['summary_blob'],1048577)
            need(decoder.eof and len(summary_raw)<=1048576 and not decoder.unused_data)
        need(sha(summary_raw)==native['idempotency']['summary_sha256'])
        proof_meta=json.loads(proof['metadata_json'])
        need(proof['cache_hit']==0 and proof_meta['proof_source_binding']==native['correlation']['proof_source_binding'])

        db.rollback()
    value={'kind':'r13_5h_exact_after_effect_root_census','action_id':'act_b2335c57472b4d68931d10dda1572ff9','task_id':'task_3b2a2a860ca54ef7889d2efce6923dc7',
     'observed_at_ms':int(time.time()*1000),'active_job_count':active,'old_pending_record_sha256':old,
     'target_postimage_sha256':sha((repository/'tests/fixtures/initial-proof-canary-target.cjs').read_bytes()),
     'checker_sha256':sha((repository/'tests/fixtures/initial-proof-canary-check.cjs').read_bytes()),
     'job_row_sha256':sha(json.dumps(job,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()),
     'proof_input_fingerprint':proof['input_fingerprint'],'proof_status':proof['status'],'proof_exit_code':proof['exit_code'],
     'proof_source_binding':proof_meta['proof_source_binding'],'proof_cache_hit':False,
     'idempotency_summary_sha256':sha(summary_raw),'idempotency_status':record['status'],
     'idempotency_key':record['idempotency_key'],'idempotency_request_hash':record['request_hash'],
     'idempotency_process_instance_id':record['process_instance_id']}
    return value

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true');parser.add_argument('--operator-approved',action='store_true');parser.add_argument('--approval-id',required=True)
    for kind in ('query','native','authority'):
        parser.add_argument('--'+kind,required=True);parser.add_argument('--'+kind+'-sha256',required=True)
    args=parser.parse_args();need(args.execute and args.operator_approved and args.approval_id==APPROVAL and os.name=='nt')
    manifest=json.loads((HERE/'settlement-manifest.json').read_bytes())
    need(manifest.get('ready_for_execution') is True)
    source=(HERE/'settle-exact-after-effect.py').read_bytes();need(sha(source)==manifest['helper_sha256'])
    need(sha(FROZEN.read_bytes())=='d6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba')
    spec=importlib.util.spec_from_file_location('frozen_settle_transport',FROZEN);transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
    packet={'execute':True,'approval_id':APPROVAL}
    for kind in ('query','native','authority'):
        packet[kind]=receipt(getattr(args,kind),getattr(args,kind+'_sha256'));packet[kind+'_sha256']=getattr(args,kind+'_sha256')
    identity=current_native_identity(packet['native'])
    packet['root_census']=local_census(packet['native']);packet['root_census']['current_native_identity_observation']=identity
    packet['root_census_sha256']=sha(canonical(packet['root_census']))
    need(CONFIG.is_file() and not CONFIG.is_symlink() and AGENT.is_file() and not AGENT.is_symlink() and sha(AGENT.read_bytes())==AGENT_SHA)
    raw_config=CONFIG.read_bytes();need(len(raw_config)<=65536);config=json.loads(raw_config)
    need(config.get('device_id')=='72ceec2d-e3f2-472f-8e3c-99fffe053035' and config.get('endpoint_id')=='executor-72ceec2d-e3f2-472f-8e3c-99fffe053035'
     and config.get('server_url','').rstrip('/')=='https://svhome.tail0e4032.ts.net')
    spec=importlib.util.spec_from_file_location('pinned_dpapi_reader',AGENT);agent=importlib.util.module_from_spec(spec);sys.modules[spec.name]=agent;spec.loader.exec_module(agent)
    # Use only the existing memory-only DPAPI decoder, never _config (which may migrate a legacy file).
    protected=config.get('node_secret_dpapi');need(protected and config.get('node_secret') in (None,''))
    packet['node_secret']=agent._unprotect_node_secret(protected)
    need(CONFIG.read_bytes()==raw_config)
    intent=HERE/'root-after-effect-terminal-reconciliation-intent.json'
    with intent.open('x',encoding='utf-8') as handle:
        json.dump({'approval_id':APPROVAL,'action_id':'act_b2335c57472b4d68931d10dda1572ff9','task_id':'task_3b2a2a860ca54ef7889d2efce6923dc7',
          'helper_sha256':sha(source),'evidence_sha256':{k:packet[k+'_sha256'] for k in ('query','native','authority','root_census')},'root_census':packet['root_census'],'no_replay':True},handle,sort_keys=True)
        handle.flush();os.fsync(handle.fileno())
    stdin=json.dumps({'source':base64.b64encode(source).decode(),'packet':packet},separators=(',',':')).encode()
    ssh=shutil.which('ssh');need(ssh)
    argv=['/usr/bin/python3','-B','-c',WRAPPER,sha(source)]
    result=subprocess.run([ssh,'-T','-oBatchMode=yes','-oStrictHostKeyChecking=yes','-oConnectTimeout=15','-oServerAliveInterval=15',
       '-oServerAliveCountMax=3','svhome@100.116.112.22',shlex.join(argv)],input=stdin,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90)
    need(len(result.stdout)<=65536 and b'Bearer ' not in result.stdout and b'PRIVATE KEY' not in result.stdout and packet['node_secret'].encode() not in result.stdout)
    record={'phase':'root_r13_5h_exact_terminal_reconciliation','public_receipts':transport.safe_receipt(result.stdout),
      'ssh_returncode':result.returncode,'remote_mutation_possible':True,'raw_error_disclosed':False,'credentials_saved':False,'no_replay':True}
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    with (HERE/('terminal-reconciliation-receipt-'+stamp+'.json')).open('x',encoding='utf-8') as handle:json.dump(record,handle,sort_keys=True,indent=2)
    print(json.dumps(record,separators=(',',':')));raise SystemExit(result.returncode)
if __name__=='__main__':
    try:main()
    except Exception:
        print('{"phase":"root_r13_5h_terminal_reconciliation_failed","ok":false,"code":"UNKNOWN_OUTCOME_READ_ONLY_INSPECT_NO_RETRY","remote_mutation_possible":true,"credentials_saved":false,"no_replay":true,"raw_error_disclosed":false}')
        raise SystemExit(2) from None
