"""Root-only owner-assisted node failure reconciliation after proven effect; no replay or native acceptance."""
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import sqlite3
import sys
import time
import types
import urllib.request

ACTION='act_b2335c57472b4d68931d10dda1572ff9'
TASK='task_3b2a2a860ca54ef7889d2efce6923dc7'
ATTEMPT='try_3631a21448cd4a3798de3a284ba3e9e0'
UNKNOWN='rcpt_9da35cd224ce47a2843d0a556a059589'
UNKNOWN_PAYLOAD='302976a0f322a2633fc72f296e87b4149d67cedc3680894f056b66237339f333'
APPROVAL='call_a60e931056bd402b997c6c10b0796d81'
REMOTE=Path('/home/svhome/.local/lib/codex-control-plane/incoming/r11-approved-20261011T225341342686Z')
CANARY=Path('/home/svhome/.local/state/codex-control-plane/owner-operations/r13-initial-verification-5h/canary')
MARKER=CANARY.parent/'authority-renewal-public.json'
NATIVE_OBSERVATION_SHA256='8c081b83dfcb075e3b8f7588cb15d9dbc4274d472d5551c0e60985b4a1beaa6c'
CONTEXT='ctx_1e7e2fec6f0e43018db7a51c6980e5c2'
PILOT='pilot_b1cb26c319fb489aae24d3b746318447'
RUN='fbaf4b0700d04794af4062671c1bcd2b'
WAVE='e712eca9463e465fb1905264c998f50c'
COMMAND='mSj-X1p4ZcQ97Q_TX-xnzzUD'
JOB='e0d55c2194fa404eae7f3f4dcaf383bf'
PROOF='796459e8115c431e993f577c27992750'
POST='d1edd529d09c7d4f71dfbb9e9b9e53010cc43a616cf1247594ddf4d705b84a1e'
CHECK='059c4e83fcbeb07b293312988975b7267d8ab8428872e5ff1211dbf059800230'
PLAN='235ecd2dc1bf8b49b21648ffd24df378088916e65e2420cb383fa79a6439afe7'
OLD_HASHES={'runs':'a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590','waves':'59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce'}


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
    need(a['context_id']=='ctx_b7d6fe51fc7c4aaaaba2947ad8c98e43' and a['request_id']=='req_3f80be12f4914928a73f41974980c339','EXACT_ACTION_CONTEXT_REQUEST_CHANGED')
    need(r['receipt_id']==UNKNOWN and r['receipt_state']=='unknown' and digest(r['payload_json'].encode())==UNKNOWN_PAYLOAD,
     'ORIGINAL_UNKNOWN_RECEIPT_CHANGED')
    need(t['closed_at_ms'] is None and t['binding_id']==c.BINDING and t['device_id']==c.DEVICE
     and t['principal_id']==c.PRINCIPAL and t['workspace_id']==c.WORKSPACE
     and t['workspace_generation']==c.GENERATION,'EXACT_OPEN_TASK_CHANGED')
    leases=target.get('mcp_task_writer_leases',[])
    active=[row for row in leases if row['released_at_ms'] is None]
    need(len(active)==1 and active[0]['task_id']==TASK and active[0]['binding_id']==c.BINDING
     and active[0]['principal_id']==c.PRINCIPAL and active[0]['owner_id']==t['owner_id']
     and type(active[0]['lease_generation']) is int and active[0]['lease_generation']>=1,
     'EXACT_ONE_ACTIVE_TASK_WRITER_LEASE_REQUIRED')

def changed_only(before,after,keys):
    return {k:v for k,v in before.items() if k not in keys}=={k:v for k,v in after.items() if k not in keys}
def verify_terminal_response(result):
    # The exact persisted digest below binds the attempt; a response need not echo it.
    need(isinstance(result.get('receipt_id'),str) and result['receipt_id'] not in ('',UNKNOWN)
     and result.get('action_id')==ACTION and result.get('receipt_state')=='failed'
     and result.get('delivery_state')=='settled' and result.get('replayed') is False,
     'TERMINAL_FAILURE_RESPONSE_UNCERTAIN_NO_RETRY')
def failure_digest(payload):
    value={'attempt_id':ATTEMPT,'receipt_state':'failed','local_handle':'','payload':payload}
    return digest(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8'))
def verify_failure(initial,final,new_receipt,payload,device):
    need(len(final.get('actions',[]))==1,'FINAL_ACTION_COUNT_CHANGED')
    a=final['actions'][0]
    need(a['delivery_state']=='settled' and type(a['settled_at_ms']) is int
     and changed_only(initial['actions'][0],a,{'delivery_state','settled_at_ms'}),'EXACT_ACTION_NOT_TRUTHFULLY_SETTLED')
    receipts=final.get('receipts',[])
    need(len(receipts)==2 and initial['receipts'][0] in receipts,'ORIGINAL_UNKNOWN_RECEIPT_NOT_PRESERVED')
    added=[r for r in receipts if r['receipt_id']!=UNKNOWN]
    need(len(added)==1 and added[0]['receipt_id']==new_receipt and added[0]['receipt_state']=='failed'
     and added[0]['action_id']==ACTION and added[0]['device_id']==device and added[0]['local_handle']==''
     and json.loads(added[0]['payload_json'])==payload and added[0]['receipt_digest']==failure_digest(payload)
     and added[0]['received_at_ms']==a['settled_at_ms'],'NEW_FAILURE_RECEIPT_OR_ATTEMPT_DIGEST_CHANGED')
    return added[0]
def verify_final(initial,final,new_receipt,payload,device):
    verify_failure(initial,final,new_receipt,payload,device)
    need(len(final.get('mcp_task_sessions',[]))==1,'FINAL_TASK_COUNT_CHANGED')
    t=final['mcp_task_sessions'][0]
    need(type(t['closed_at_ms']) is int and changed_only(initial['mcp_task_sessions'][0],t,{'closed_at_ms','close_reason'}),'EXACT_TASK_CLOSE_CHANGED')
    old=initial.get('mcp_task_writer_leases',[]);new=final.get('mcp_task_writer_leases',[])
    need(len(old)==len(new),'LEASE_HISTORY_COUNT_CHANGED')
    for row in old:
        matching=[v for v in new if v['lease_id']==row['lease_id']];need(len(matching)==1,'LEASE_HISTORY_MISSING')
        if row['released_at_ms'] is None:
            need(changed_only(row,matching[0],{'released_at_ms','release_reason'}) and matching[0]['released_at_ms'] is not None,
             'EXACT_LEASE_NOT_RELEASED_OR_HISTORY_CHANGED')
        else:
            need(row==matching[0],'ALREADY_RELEASED_LEASE_HISTORY_CHANGED')

def validate_query(query):
    need(query.get('action_id')==ACTION and query.get('task_id')==TASK and query.get('delivery_state')=='reconcile_required'
     and query.get('settled_at_ms') is None and len(query.get('receipts',[]))==1
     and query['receipts'][0].get('receipt_id')==UNKNOWN and query['receipts'][0].get('payload_sha256')==UNKNOWN_PAYLOAD
     and query['receipts'][0].get('receipt_state')=='unknown'
     and query['receipts'][0].get('diagnostic_code')=='CONTROL_PLANE_APPROVED_PATCH_TIMEOUT'
     and query.get('attempts')==[{'attempt_id':ATTEMPT,'attempt_number':1,'dispatched_at_ms':1791759246011}]
     and query.get('reconciliations')==[] and query.get('dispatch_dispositions')==[], 'EXACT_QUERY_EVIDENCE_CHANGED')

def validate_native(native):
    need(isinstance(native,dict) and native.get('ok') is True
     and native.get('kind')=='r13_5h_after_effect_diagnostic_correlation'
     and native.get('action_id')==ACTION and native.get('task_id')==TASK and native.get('attempt_id')==ATTEMPT
     and native.get('unknown_receipt_id')==UNKNOWN and native.get('unknown_payload_sha256')==UNKNOWN_PAYLOAD
     and native.get('central_delivery_state')=='reconcile_required' and native.get('central_action_settled') is False,
     'EXACT_NATIVE_CORRELATION_REQUIRED')
    need(native.get('patch_applied') is True and native.get('target_postimage_sha256')==POST and native.get('checker_sha256')==CHECK
     and native.get('source_identity_current_matches_proof') is True and native.get('native_semantic_acceptance')=='pending'
     and native.get('checker_4_of_4')=='not_observed' and native.get('attestation_claimed') is False,
     'EXACT_EFFECT_WITHOUT_ACCEPTANCE_OR_TAP_CLAIM_REQUIRED')
    proof=native.get('initial_verification',{});correlation=native.get('correlation',{});idempotency=native.get('idempotency',{})
    need(proof.get('plan_sha256')==PLAN and proof.get('proof_status')=='passed' and proof.get('proof_ids')==[PROOF]
     and proof.get('command_id')==COMMAND and proof.get('job_id')==JOB
     and isinstance(proof.get('proof_fingerprint'),str) and re.fullmatch(r'[a-f0-9]{64}',proof['proof_fingerprint'])
     and native.get('proof_status')=='passed' and type(native.get('proof_exit_code')) is int and native['proof_exit_code']==0,
     'GENUINE_EXACT_INITIAL_PROOF_REQUIRED')
    need(all(correlation.get(k)==v for k,v in {'run_id':RUN,'wave_id':WAVE,'command_id':COMMAND,'job_id':JOB,
      'proof_ids':[PROOF],'proof_fingerprint':proof['proof_fingerprint'],'job_lifecycle':'exited','exit_code':0,
      'old_pending_record_sha256':OLD_HASHES,'old_pending_records_unchanged':True,'canary_jobs_quiescent':True}.items())
     and correlation.get('run_status')!='accepted' and correlation.get('wave_status')!='ACCEPTED',
     'EXACT_JOB_PROOF_AND_OLD_PENDING_HISTORY_REQUIRED')
    need(idempotency.get('status')=='completed' and idempotency.get('orchestration_state')=='ACCEPTING'
     and isinstance(idempotency.get('summary_sha256'),str) and re.fullmatch(r'[a-f0-9]{64}',idempotency['summary_sha256']),
     'GENUINE_COMPLETED_IDEMPOTENCY_REQUIRED')

def validate_identity(value,native,now):
    need(isinstance(value,dict) and value.get('ok') is True
     and value.get('kind')=='r13_5h_root_current_native_identity_read_only'
     and type(value.get('observed_at_ms')) is int and 0<=now-value['observed_at_ms']<60000
     and value.get('native_identity')==native['native_identity']
     and all(value.get(key) is True for key in ('current_identity','mcp_ready','host_process_verified','authenticated_read_only'))
     and all(value.get(key) is False for key in ('activation_performed','acceptance_performed','mutated_canonical_ledger','secret_values_emitted')),
     'FRESH_AUTHENTICATED_EXACT_NATIVE_IDENTITY_REQUIRED')

def validate_census(census,native,now):
    validate_identity(census.get('current_native_identity_observation'),native,now)
    need(census.get('kind')=='r13_5h_exact_after_effect_root_census' and census.get('action_id')==ACTION
     and census.get('task_id')==TASK and type(census.get('observed_at_ms')) is int
     and 0<=now-census['observed_at_ms']<60000 and census.get('active_job_count')==0
     and type(census.get('active_job_count')) is int and census.get('target_postimage_sha256')==POST
     and census.get('checker_sha256')==CHECK and census.get('old_pending_record_sha256')==OLD_HASHES
     and census.get('job_row_sha256')==native['correlation']['job_row_sha256']
     and census.get('proof_input_fingerprint')==native['correlation']['proof_input_fingerprint']
     and census.get('proof_status')=='passed' and census.get('proof_exit_code')==0
     and census.get('proof_source_binding')==native['correlation']['proof_source_binding'] and census.get('proof_cache_hit') is False
     and census.get('idempotency_status')=='completed' and census.get('idempotency_key')==native['idempotency']['key']
     and census.get('idempotency_summary_sha256')==native['idempotency']['summary_sha256']
     and census.get('idempotency_request_hash')==native['idempotency']['request_hash']
     and census.get('idempotency_process_instance_id')==native['native_identity']['process_instance_id'],
     'FRESH_QUIESCENT_EFFECT_AND_PROOF_PRESERVATION_REQUIRED')

def build_payload(native,evidence):
    validate_native(native)
    return {'schema_version':1,'operation_kind':'control_plane_approved_patch',
     'code':'CONTROL_PLANE_APPROVED_PATCH_RESULT_DELIVERY_FAILED_AFTER_EFFECT',
     'diagnostic_code':'CONTROL_PLANE_APPROVED_PATCH_TIMEOUT','patch_applied':True,
     'owner_assisted_node_reconciliation':True,'result_delivery_failed_after_effect':True,
     'local_semantic_acceptance':'pending','checker_4_of_4':'not_observed','run_id':RUN,'wave_id':WAVE,
     'initial_verification':native['initial_verification'],
     'file':{'path':'tests/fixtures/initial-proof-canary-target.cjs','postimage_sha256':POST},
     'reconciles_receipt_id':UNKNOWN,'reconciles_payload_sha256':UNKNOWN_PAYLOAD,'evidence_sha256':evidence}

def main(packet):
    need(packet.get('execute') is True and packet.get('approval_id')==APPROVAL,'EXPLICIT_APPROVED_RECONCILIATION_REQUIRED')
    query=unwrap(packet['query']);native=packet['native'];authority=unwrap(packet['authority'])
    now=int(time.time()*1000)
    validate_query(query)
    need(packet.get('native_sha256')==NATIVE_OBSERVATION_SHA256,'EXACT_GENUINE_NATIVE_CAPSULE_PIN_REQUIRED')
    validate_native(native)
    validate_census(packet['root_census'],native,now)
    need(digest(canonical(packet['root_census']))==packet['root_census_sha256'],'ROOT_CENSUS_DIGEST_CHANGED')
    c=load_remote('r11_common.py','25f2d15359ff49a50e1ded411d40f1f029fb6067390c68aff9b93bda0130d986')
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
     and marker['phase']=='intake_reopened' and marker['requested_at_ms']<=now<marker['expires_at_ms']==authority['expires_at_ms']
     and marker['context_id']==authority['context_id']==CONTEXT and marker['pilot_id']==authority['pilot_id']==PILOT
     and marker['expires_at_ms']-marker['requested_at_ms']==18000000 and authority['duration_ms']==18000000,
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
     and identity.get('tool_contract_sha256')==marker['contract_version'].removeprefix('sha256:'),
     'EXACT_NATIVE_INSTANCE_REQUIRED')
    evidence={k:packet[k+'_sha256'] for k in ('query','native','authority','root_census')}
    exclusive(CANARY/'after-effect-reconciliation-intent.json',{'action_id':ACTION,'task_id':TASK,'attempt_id':ATTEMPT,
     'approval_id':APPROVAL,'evidence':evidence,'historical_rows_sha256':digest(canonical(before)),'no_replay':True})
    payload=build_payload(native,evidence)
    validate_census(packet['root_census'],native,int(time.time()*1000))
    need(int(time.time()*1000)<marker['expires_at_ms'],'AUTHORITY_EXPIRED_BEFORE_RECEIPT')
    body={'action_id':ACTION,'attempt_id':ATTEMPT,'receipt_state':'failed','local_handle':'','payload':payload}
    request=urllib.request.Request(origin+'/v1/nodes/'+c.DEVICE+'/receipts',data=canonical(body),
      headers={'Authorization':'Node '+packet['node_secret'],'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(request,timeout=15) as response:result=json.load(response)
    verify_terminal_response(result)
    recorded,terminal=snapshot(database);need(before==recorded,'UNRELATED_HISTORY_CHANGED_AFTER_RECEIPT')
    verified=verify_failure(initial,terminal,result['receipt_id'],payload,c.DEVICE)
    need(initial.get('mcp_task_sessions',[])==terminal.get('mcp_task_sessions',[])
     and initial.get('mcp_task_writer_leases',[])==terminal.get('mcp_task_writer_leases',[]),'TASK_OR_LEASE_CHANGED_BEFORE_CLOSE')
    exclusive(CANARY/'after-effect-terminal-receipt.json',{
     **{k:result[k] for k in ('receipt_id','action_id','receipt_state','delivery_state')},
     'attempt_id':ATTEMPT,'attempt_binding_basis':'persisted_receipt_digest_and_unchanged_delivery_attempt',
     'receipt_digest':verified['receipt_digest']})
    canary=load_remote('r13_5h_mcp_canary.py','cd91a622d76f19873adc4c7671f6b72d59ba99cac639957c04a1413cb06df104')
    mcp_origin,auth=canary.mcp_credentials(c)
    exclusive(CANARY/'after-effect-task-close-intent.json',{'action_id':ACTION,'task_id':TASK,'terminal_receipt_id':result['receipt_id']})
    released=canary.call(mcp_origin,auth,'task_control',{'operation':'writer_release','task_id':TASK,
      'reason':'owner-assisted failed result delivery after applied patch; native acceptance pending'})
    need(released.get('execution')=='writer_lease_released','WRITER_RELEASE_RESPONSE_UNCERTAIN_NO_RETRY')
    closed=canary.call(mcp_origin,auth,'workspace_context',{'operation':'task_close','task_id':TASK}).get('task',{})
    need(closed.get('task_id')==TASK and type(closed.get('closed_at_ms')) is int,'TASK_CLOSE_RESPONSE_UNCERTAIN_NO_RETRY')
    after,final=snapshot(database);need(before==after,'UNRELATED_HISTORICAL_ROWS_CHANGED');verify_final(initial,final,result['receipt_id'],payload,c.DEVICE)
    exclusive(CANARY/'after-effect-task-closed.json',{'task_id':TASK,'closed_at_ms':closed['closed_at_ms'],'unknown_receipt_preserved':UNKNOWN})
    public({'phase':'r13_5h_exact_after_effect_reconciled','ok':True,'action_id':ACTION,'task_id':TASK,'attempt_id':ATTEMPT,
     'original_unknown_receipt_preserved':UNKNOWN,'terminal_receipt_id':result['receipt_id'],'terminal_code':payload['code'],
     'action_state':'settled','patch_applied':True,'checker_4_of_4':'not_observed','local_semantic_acceptance':'pending','new_run_job_proof_created':False,'writer_released':True,'task_closed':True,
     'unrelated_history_preserved':True,'local_node_journal_modified':False,'remote_mutation':True,'replay_forbidden':True})

if __name__=='__main__':
    try: main(json.loads(sys.stdin.buffer.read(512*1024+1)))
    except Exception:
        public({'phase':'r13_5h_exact_after_effect_reconciliation_failed','ok':False,'code':'RECONCILIATION_UNCERTAIN_READ_ONLY_INSPECT_NO_RETRY',
         'raw_error_disclosed':False,'remote_mutation_possible':True,'replay_forbidden':True})
        raise SystemExit(2) from None
