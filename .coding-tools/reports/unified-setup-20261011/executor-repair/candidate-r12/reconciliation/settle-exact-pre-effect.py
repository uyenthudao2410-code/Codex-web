"""Root-authorized one-time genuine node rejection and exact task close; no action replay."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
import types
import urllib.request

ACTION='act_6aa1329b96c146f38c807f9926b3e684'
TASK='task_d2c1dd3bff4042d084b045e9bc5a381b'
ATTEMPT='try_4178cd41d2f3424a81dcb3c4cc706ed1'
UNKNOWN='rcpt_9117fdebb06b4e8e8b1b5cd1b65ed2b1'
UNKNOWN_PAYLOAD='09b5eeb50c371e333d23da019ec4d443d8e22d9aaaf2914472c802cbbacb38c2'
APPROVAL='call_1KzUkF0gMn6uVpHd3QisTzXF'
REMOTE=Path('/home/svhome/.local/lib/codex-control-plane/incoming/r11-approved-20261011T194930649730Z')
CANARY=Path('/home/svhome/.local/state/codex-control-plane/owner-operations/r12-initial-verification-60m/canary')
MARKER=CANARY.parent/'authority-renewal-public.json'

class Failure(Exception):
    pass
def need(ok,code):
    if not ok: raise Failure(code)
def digest(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def public(value): print(json.dumps(value,sort_keys=True,separators=(',',':')))
def unwrap(value):
    rows=value.get('public_receipts',[value]);need(len(rows)==1,'EXACT_PUBLIC_RECEIPT_REQUIRED');return rows[0]
def load_remote(name,sha):
    p=REMOTE/name;raw=p.read_bytes();need(digest(raw)==sha,'FROZEN_REMOTE_HELPER_CHANGED')
    spec=importlib.util.spec_from_file_location('frozen_'+name.replace('.','_'),p)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
def exclusive(path,value):
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as handle:handle.write(canonical(value));handle.flush();os.fsync(handle.fileno())

TABLES=('mcp_permission_requests','work_requests','actions','delivery_attempts','receipts','action_reconciliations',
 'action_dispatch_dispositions','mcp_task_sessions','mcp_task_writer_leases','mcp_task_action_links','mcp_patch_acceptances',
 'mcp_file_read_intents','mcp_approved_patch_intents','mcp_standing_patch_intents','mcp_exec_intents','mcp_artifact_intents',
 'mcp_document_write_intents','mcp_read_only_intents','contexts','scoped_pilot_decisions','mcp_service_grants')
def snapshot(database):
    d=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True,timeout=5)
    try:
        d.row_factory=sqlite3.Row;d.execute('PRAGMA query_only=ON');d.execute('BEGIN')
        state={};target={}
        for table in TABLES:
            rows=[dict(row) for row in d.execute('SELECT * FROM '+table)]
            excluded=[];remaining=[]
            for row in rows:
                selected=(table in ('actions','receipts') and row.get('action_id')==ACTION) or (table in ('mcp_task_sessions','mcp_task_writer_leases') and row.get('task_id')==TASK)
                (excluded if selected else remaining).append(row)
            state[table]=digest(canonical(sorted(remaining,key=lambda v:canonical(v))))
            if excluded:target[table]=excluded
        return state,target
    finally:d.close()
def exact_initial(target,c):
    a=target.get('actions',[]);r=target.get('receipts',[]);t=target.get('mcp_task_sessions',[])
    need(len(a)==len(r)==len(t)==1,'EXACT_INITIAL_FAMILY_REQUIRED')
    a=a[0];r=r[0];t=t[0]
    need(a['delivery_state']=='reconcile_required' and a['settled_at_ms'] is None and a['binding_id']==c.BINDING
     and a['device_id']==c.DEVICE and a['workspace_id']==c.WORKSPACE and a['workspace_generation']==c.GENERATION,
     'INITIAL_UNKNOWN_ACTION_CHANGED')
    need(r['receipt_id']==UNKNOWN and r['receipt_state']=='unknown' and digest(r['payload_json'].encode())==UNKNOWN_PAYLOAD,
     'ORIGINAL_UNKNOWN_RECEIPT_CHANGED')
    need(t['closed_at_ms'] is None and t['binding_id']==c.BINDING and t['device_id']==c.DEVICE
     and t['principal_id']==c.PRINCIPAL,'EXACT_OPEN_TASK_CHANGED')
def changed_only(before,after,keys):
    return {k:v for k,v in before.items() if k not in keys}=={k:v for k,v in after.items() if k not in keys}
def verify_terminal_response(result):
    # The exact persisted digest below binds the attempt; a response need not echo it.
    need(isinstance(result.get('receipt_id'),str) and result['receipt_id'] not in ('',UNKNOWN)
     and result.get('action_id')==ACTION and result.get('receipt_state')=='rejected'
     and result.get('delivery_state')=='settled' and result.get('replayed') is False,
     'TERMINAL_REJECTION_RESPONSE_UNCERTAIN_NO_RETRY')
def rejection_digest(payload):
    value={'attempt_id':ATTEMPT,'receipt_state':'rejected','local_handle':'','payload':payload}
    return digest(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8'))
def verify_rejection(initial,final,new_receipt,payload,device):
    need(len(final.get('actions',[]))==1,'FINAL_ACTION_COUNT_CHANGED')
    a=final['actions'][0]
    need(a['delivery_state']=='settled' and type(a['settled_at_ms']) is int
     and changed_only(initial['actions'][0],a,{'delivery_state','settled_at_ms'}),'EXACT_ACTION_NOT_TRUTHFULLY_SETTLED')
    receipts=final.get('receipts',[])
    need(len(receipts)==2 and initial['receipts'][0] in receipts,'ORIGINAL_UNKNOWN_RECEIPT_NOT_PRESERVED')
    added=[r for r in receipts if r['receipt_id']!=UNKNOWN]
    need(len(added)==1 and added[0]['receipt_id']==new_receipt and added[0]['receipt_state']=='rejected'
     and added[0]['action_id']==ACTION and added[0]['device_id']==device and added[0]['local_handle']==''
     and json.loads(added[0]['payload_json'])==payload and added[0]['receipt_digest']==rejection_digest(payload)
     and added[0]['received_at_ms']==a['settled_at_ms'],'NEW_REJECTION_RECEIPT_OR_ATTEMPT_DIGEST_CHANGED')
    return added[0]
def verify_final(initial,final,new_receipt,payload,device):
    verify_rejection(initial,final,new_receipt,payload,device)
    need(len(final.get('mcp_task_sessions',[]))==1,'FINAL_TASK_COUNT_CHANGED')
    t=final['mcp_task_sessions'][0]
    need(type(t['closed_at_ms']) is int and changed_only(initial['mcp_task_sessions'][0],t,{'closed_at_ms','close_reason'}),'EXACT_TASK_CLOSE_CHANGED')
    old=initial.get('mcp_task_writer_leases',[]);new=final.get('mcp_task_writer_leases',[])
    need(len(old)==len(new),'LEASE_HISTORY_COUNT_CHANGED')
    for row in old:
        matching=[v for v in new if v['lease_id']==row['lease_id']];need(len(matching)==1,'LEASE_HISTORY_MISSING')
        need(changed_only(row,matching[0],{'released_at_ms','release_reason'}) and matching[0]['released_at_ms'] is not None,
             'EXACT_LEASE_NOT_RELEASED_OR_HISTORY_CHANGED')

def main(packet):
    need(packet.get('execute') is True and packet.get('approval_id')==APPROVAL,'EXPLICIT_APPROVED_RECONCILIATION_REQUIRED')
    query=unwrap(packet['query']);native=packet['native'];authority=unwrap(packet['authority'])
    now=int(time.time()*1000)
    need(query['action_id']==ACTION and query['task_id']==TASK and query['delivery_state']=='reconcile_required'
     and query['receipts'][0]['receipt_id']==UNKNOWN and query['receipts'][0]['payload_sha256']==UNKNOWN_PAYLOAD,
     'EXACT_QUERY_EVIDENCE_CHANGED')
    need(native.get('ok') is True and native.get('action_id')==ACTION and native.get('task_id')==TASK and native.get('attempt_id')==ATTEMPT
     and native.get('code')=='WORKTREE_STATUS_TOO_LARGE' and native.get('category')=='validation' and native.get('pre_effect') is True
     and type(native.get('observed_at_ms')) is int and 0<=now-native['observed_at_ms']<60000
     and all(native.get(k) is True for k in ('no_new_runs','no_new_jobs','no_new_proof','no_active_work','zero_vm'))
     and native.get('target_preimage_sha256')=='90363c394e12dd67f9003ef96b033e739c7837b34c238238966df623d9e55650'
     and native.get('checker_sha256')=='059c4e83fcbeb07b293312988975b7267d8ab8428872e5ff1211dbf059800230'
     and native.get('old_run_sha256')=='a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590'
     and native.get('old_wave_sha256')=='59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce',
     'FRESH_NATIVE_PRE_EFFECT_PROOF_REQUIRED')
    c=load_remote('r11_common.py','c55d9d07144654ca0216d55c8de8b20c1a238a9a722ac455d6c83ec0d406e36f')
    c.private_directory(REMOTE);c.private_directory(CANARY);c.service_pid()
    config=c.environment();bind=config.get('CONTROL_PLANE_BIND','127.0.0.1')
    need(bind in ('127.0.0.1','0.0.0.0','::',c.HOST),'SERVICE_BIND_CHANGED')
    origin='http://'+(c.HOST if bind==c.HOST else '127.0.0.1')+':'+config.get('CONTROL_PLANE_PORT','8765')
    health=c.api(origin,config['CONTROL_PLANE_OPERATOR_TOKEN'],'/healthz')
    need(health['service_instance_id']==query['service_instance_id']==authority['service_instance_id']
     and health['declared_source_revision']==c.REVISION and health['package_source_sha256']==c.PACKAGE,'SERVER_INSTANCE_OR_RELEASE_CHANGED')
    c.verify_release(c.CURRENT.resolve(strict=True),c.REVISION)
    marker_raw=c.protected_file(MARKER);marker=json.loads(marker_raw)
    need(digest(marker_raw)==authority['next_marker_sha256'] and marker['approval_id']==APPROVAL
     and marker['binding_id']==c.BINDING and marker['root']==c.LOCAL_ROOT and marker['profile']==c.LOCAL_PROFILE
     and marker['phase']=='intake_reopened' and marker['requested_at_ms']<=now<marker['expires_at_ms']==authority['expires_at_ms'],
     'EXACT_UNEXPIRED_AUTHORITY_REQUIRED')
    database=Path(config['CONTROL_PLANE_DB']);need(database.is_absolute() and not database.is_symlink(),'DATABASE_TARGET_UNSAFE')
    before,initial=snapshot(database);exact_initial(initial,c)
    d=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True,timeout=5)
    try:
        d.execute('PRAGMA query_only=ON')
        need(d.execute('SELECT attempt_id FROM delivery_attempts WHERE action_id=?',(ACTION,)).fetchall()==[(ATTEMPT,)]
         and d.execute('SELECT task_id FROM mcp_task_action_links WHERE action_id=?',(ACTION,)).fetchall()==[(TASK,)],'EXACT_ATTEMPT_OR_TASK_LINK_CHANGED')
    finally:d.close()
    identity=native.get('native_identity',{})
    need(identity.get('activation_epoch_id')==marker['activation_epoch']
     and identity.get('process_instance_id')==marker['runtime_instance_id']
     and identity.get('server_instance_id')==marker['mcp_server_instance_id']
     and identity.get('tool_contract_sha256')==marker['contract_version'].removeprefix('sha256:')
     and isinstance(native.get('performance_evidence_sha256'),str) and len(native['performance_evidence_sha256'])==64,
     'EXACT_NATIVE_INSTANCE_AND_PERFORMANCE_PROOF_REQUIRED')
    evidence={k:packet[k+'_sha256'] for k in ('query','native','authority')}
    exclusive(CANARY/'pre-effect-reconciliation-intent.json',{'action_id':ACTION,'task_id':TASK,'attempt_id':ATTEMPT,
     'approval_id':APPROVAL,'evidence':evidence,'historical_rows_sha256':digest(canonical(before)),'no_replay':True})
    payload={'schema_version':1,'operation_kind':'control_plane_approved_patch','code':'WORKTREE_STATUS_TOO_LARGE',
     'patch_applied':False,'local_semantic_acceptance':'not_performed','pre_effect_validation_rejection':True,
     'reconciles_receipt_id':UNKNOWN,'reconciles_payload_sha256':UNKNOWN_PAYLOAD,'evidence_sha256':evidence}
    need(0<=int(time.time()*1000)-native['observed_at_ms']<60000 and int(time.time()*1000)<marker['expires_at_ms'],
     'NATIVE_PROOF_STALE_OR_AUTHORITY_EXPIRED_BEFORE_RECEIPT')
    body={'action_id':ACTION,'attempt_id':ATTEMPT,'receipt_state':'rejected','local_handle':'','payload':payload}
    request=urllib.request.Request(origin+'/v1/nodes/'+c.DEVICE+'/receipts',data=canonical(body),
      headers={'Authorization':'Node '+packet['node_secret'],'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(request,timeout=15) as response:result=json.load(response)
    verify_terminal_response(result)
    recorded,terminal=snapshot(database);need(before==recorded,'UNRELATED_HISTORY_CHANGED_AFTER_RECEIPT')
    verified=verify_rejection(initial,terminal,result['receipt_id'],payload,c.DEVICE)
    need(initial.get('mcp_task_sessions',[])==terminal.get('mcp_task_sessions',[])
     and initial.get('mcp_task_writer_leases',[])==terminal.get('mcp_task_writer_leases',[]),'TASK_OR_LEASE_CHANGED_BEFORE_CLOSE')
    exclusive(CANARY/'pre-effect-terminal-receipt.json',{
     **{k:result[k] for k in ('receipt_id','action_id','receipt_state','delivery_state')},
     'attempt_id':ATTEMPT,'attempt_binding_basis':'persisted_receipt_digest_and_unchanged_delivery_attempt',
     'receipt_digest':verified['receipt_digest']})
    canary=load_remote('r12_mcp_canary.py','ef0928a25dcbc25c3977d9fc74e207dfe29281af2c291b831867a16b8927a43f')
    mcp_origin,auth=canary.mcp_credentials(c)
    exclusive(CANARY/'pre-effect-task-close-intent.json',{'action_id':ACTION,'task_id':TASK,'terminal_receipt_id':result['receipt_id']})
    closed=canary.call(mcp_origin,auth,'workspace_context',{'operation':'task_close','task_id':TASK}).get('task',{})
    need(closed.get('task_id')==TASK and type(closed.get('closed_at_ms')) is int,'TASK_CLOSE_RESPONSE_UNCERTAIN_NO_RETRY')
    after,final=snapshot(database);need(before==after,'UNRELATED_HISTORICAL_ROWS_CHANGED');verify_final(initial,final,result['receipt_id'],payload,c.DEVICE)
    exclusive(CANARY/'pre-effect-task-closed.json',{'task_id':TASK,'closed_at_ms':closed['closed_at_ms'],'unknown_receipt_preserved':UNKNOWN})
    public({'phase':'r12_exact_pre_effect_reconciled','ok':True,'action_id':ACTION,'task_id':TASK,'attempt_id':ATTEMPT,
     'original_unknown_receipt_preserved':UNKNOWN,'terminal_receipt_id':result['receipt_id'],'terminal_code':'WORKTREE_STATUS_TOO_LARGE',
     'action_state':'settled','patch_applied':False,'new_run_job_proof_created':False,'writer_released':True,'task_closed':True,
     'unrelated_history_preserved':True,'local_node_journal_modified':False,'remote_mutation':True,'replay_forbidden':True})

if __name__=='__main__':
    try: main(json.loads(sys.stdin.buffer.read(512*1024+1)))
    except Exception:
        public({'phase':'r12_exact_pre_effect_reconciliation_failed','ok':False,'code':'RECONCILIATION_UNCERTAIN_READ_ONLY_INSPECT_NO_RETRY',
         'raw_error_disclosed':False,'remote_mutation_possible':True,'replay_forbidden':True})
        raise SystemExit(2) from None
