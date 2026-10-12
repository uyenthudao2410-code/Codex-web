"""Root-only once task/writer cleanup. Never post a receipt or replay a patch."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time

SETTLEMENT_SHA='30f0169c0acb39bb888178e1326a220d175d936a39208397f358eb1eb0b0ed0f'
COMMON_SHA='25f2d15359ff49a50e1ded411d40f1f029fb6067390c68aff9b93bda0130d986'
CANARY_SHA='cd91a622d76f19873adc4c7671f6b72d59ba99cac639957c04a1413cb06df104'
INSPECTOR_SHA='5c37fd0c014eae013a30e75a33acfa6a48ff7843627c9257728ccd23fd4bfcb6'
NEW='rcpt_eea61400c4a3408d88bfec9174b75ec7'
PAYLOAD_SHA='b685d64c650b907f9f82d0d1626b0aee7797edea7c83acfdb25a1e56fdb6c8b5'
RECEIPT_DIGEST='1e84662cb62bcd1655f566dcc8f87c4ee19d2ab5bf1747878c9a52377cd3e0ba'
EXPIRY=1791776571067
REASON='after_effect_result_delivery_failed'
PHASE='r13_5h_exact_after_effect_task_only_cleanup'

class Failure(Exception):pass
def need(ok,code):
    if not ok:raise Failure(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def unwrap(value):
    rows=value.get('public_receipts',[value]);need(len(rows)==1,'EXACT_PUBLIC_RECEIPT_REQUIRED');return rows[0]
def forbidden(*args,**kwargs):raise Failure('SETTLEMENT_REPLAY_FORBIDDEN')
def load(packet):
    raw=base64.b64decode(packet['settlement_source_b64'],validate=True)
    need(len(raw)<=262144 and sha(raw)==SETTLEMENT_SHA==packet['settlement_source_sha256'],'FROZEN_SETTLEMENT_CHANGED')
    s={'__name__':'task_only_frozen_functions'};exec(compile(raw,'<task-only-frozen-functions>','exec'),s)
    s['main']=s['exclusive']=s['public']=forbidden
    return s
def exclusive(path,value):
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as handle:handle.write(canonical(value));handle.flush();os.fsync(handle.fileno())

def read_exact(database,s):
    need(database.is_absolute() and database.is_file() and not database.is_symlink(),'DATABASE_TARGET_UNSAFE')
    d=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True,timeout=5)
    try:
        d.row_factory=sqlite3.Row;d.execute('PRAGMA query_only=ON');d.execute('BEGIN')
        rows=lambda sql,value:[dict(r) for r in d.execute(sql,(value,))]
        return {'actions':rows('SELECT * FROM actions WHERE action_id=?',s['ACTION']),
          'receipts':rows('SELECT * FROM receipts WHERE action_id=? ORDER BY received_at_ms,receipt_id',s['ACTION']),
          'mcp_task_sessions':rows('SELECT * FROM mcp_task_sessions WHERE task_id=?',s['TASK']),
          'mcp_task_writer_leases':rows('SELECT * FROM mcp_task_writer_leases WHERE task_id=? ORDER BY lease_id',s['TASK']),
          'delivery_attempts':rows('SELECT * FROM delivery_attempts WHERE action_id=? ORDER BY attempt_number',s['ACTION'])}
    finally:d.close()

def validate_before(rows,inspection,c,s):
    need(len(rows['actions'])==len(rows['mcp_task_sessions'])==1 and len(rows['receipts'])==2,'EXACT_FAMILY_REQUIRED')
    a,t=rows['actions'][0],rows['mcp_task_sessions'][0]
    target={'binding_id':c.BINDING,'device_id':c.DEVICE,'workspace_id':c.WORKSPACE,'workspace_generation':c.GENERATION}
    need(all(a.get(k)==v and t.get(k)==v for k,v in target.items()) and t['principal_id']==c.PRINCIPAL,'EXACT_TARGET_CHANGED')
    need(a['delivery_state']=='settled' and type(a['settled_at_ms']) is int and t['closed_at_ms'] is None,'EXACT_SETTLED_OPEN_TASK_REQUIRED')
    old=[r for r in rows['receipts'] if r['receipt_id']==s['UNKNOWN']]
    new=[r for r in rows['receipts'] if r['receipt_id']==NEW]
    need(len(old)==len(new)==1 and old[0]['receipt_state']=='unknown'
      and sha(old[0]['payload_json'].encode())==s['UNKNOWN_PAYLOAD'],'ORIGINAL_UNKNOWN_CHANGED')
    need(new[0]['receipt_state']=='failed' and sha(new[0]['payload_json'].encode())==PAYLOAD_SHA
      and new[0]['receipt_digest']==RECEIPT_DIGEST and new[0]['received_at_ms']==a['settled_at_ms'],'FAILED_RECEIPT_CHANGED')
    need(inspection['action_row_sha256']==sha(canonical(a)) and inspection['task_row_sha256']==sha(canonical(t))
      and {r['receipt_id']:r['row_sha256'] for r in inspection['receipts']}=={r['receipt_id']:sha(canonical(r)) for r in rows['receipts']}
      and {r['lease_id']:r['row_sha256'] for r in inspection['lease_history']}=={r['lease_id']:sha(canonical(r)) for r in rows['mcp_task_writer_leases']},'FRESH_INSPECTION_ROWS_CHANGED')
    leases=rows['mcp_task_writer_leases'];active=[r for r in leases if r['released_at_ms'] is None]
    need(len(active)<=1 and all(r['binding_id']==c.BINDING and r['principal_id']==c.PRINCIPAL
      and r['owner_id']==t['owner_id'] and r['task_id']==s['TASK'] for r in leases),'EXACT_WRITER_SCOPE_CHANGED')
    need(len(rows['delivery_attempts'])==1 and rows['delivery_attempts'][0]['attempt_id']==s['ATTEMPT'],'EXACT_ATTEMPT_CHANGED')
    return active

def preserve(before,after,s,closed=False):
    need(all(before[k]==after[k] for k in ('actions','receipts','delivery_attempts')),'ACTION_RECEIPT_OR_ATTEMPT_HISTORY_CHANGED')
    need(len(before['mcp_task_sessions'])==len(after['mcp_task_sessions'])==1,'TASK_HISTORY_CHANGED')
    old,new=before['mcp_task_sessions'][0],after['mcp_task_sessions'][0]
    need(s['changed_only'](old,new,{'closed_at_ms','close_reason'}) if closed else old==new,'TASK_HISTORY_CHANGED')
    if closed:need(type(new['closed_at_ms']) is int and new['close_reason']=='mcp_task_close','EXACT_TASK_NOT_CLOSED')
    previous,current=before['mcp_task_writer_leases'],after['mcp_task_writer_leases']
    need(len(previous)==len(current),'LEASE_HISTORY_COUNT_CHANGED')
    for row in previous:
        matches=[r for r in current if r['lease_id']==row['lease_id']];need(len(matches)==1,'LEASE_HISTORY_CHANGED')
        new=matches[0]
        if row['released_at_ms'] is None:
            need(s['changed_only'](row,new,{'released_at_ms','release_reason'}) and type(new['released_at_ms']) is int
              and new['release_reason']==REASON,'EXACT_WRITER_NOT_RELEASED')
        else:need(row==new,'RELEASED_LEASE_HISTORY_CHANGED')

def validate_observation(observation,rows,c,s):
    t=rows['mcp_task_sessions'][0];p=observation.get('task',{})
    need(all(p.get(k)==t[k] for k in ('task_id','owner_id','principal_id','binding_id','device_id','workspace_id','workspace_generation','closed_at_ms')),'MCP_TASK_OBSERVATION_CHANGED')
    actions=observation.get('actions',[])
    need(len(actions)==1 and actions[0].get('action_id')==s['ACTION'] and actions[0].get('delivery_state')=='settled'
      and actions[0].get('settled_at_ms')==rows['actions'][0]['settled_at_ms'],'MCP_ACTION_OBSERVATION_CHANGED')
    active=[r for r in rows['mcp_task_writer_leases'] if r['released_at_ms'] is None]
    if active:
        lease=observation.get('writer_lease',{})
        need(all(lease.get(k)==active[0][k] for k in ('task_id','binding_id','lease_generation','acquired_at_ms',
          'renewed_at_ms','expires_at_ms','released_at_ms')) and lease.get('state') in ('held','expired'),
          'MCP_WRITER_OBSERVATION_CHANGED')
    need(type(observation.get('observed_at_ms')) is int and 0<=int(time.time()*1000)-observation['observed_at_ms']<60000,
      'FRESH_MCP_TASK_OBSERVATION_REQUIRED')

def main(packet):
    stage='input';effect=False;types=(Failure,)
    try:
        need(packet.get('execute') is True and packet.get('approval_id')=='call_a60e931056bd402b997c6c10b0796d81','EXPLICIT_TASK_ONLY_CLEANUP_REQUIRED')
        s=load(packet);types+=(s['Failure'],)
        inspection=unwrap(packet['inspection']);authority=unwrap(packet['authority']);intent=packet['root_intent'];now=int(time.time()*1000)
        need(inspection.get('ok') is True and inspection.get('phase')=='r13_5h_after_effect_settlement_read_only_inspection'
          and inspection.get('remote_mutation') is False and inspection.get('reconstructed_verify_failure',{}).get('status')=='passed'
          and inspection.get('action_id')==s['ACTION'] and inspection.get('task_id')==s['TASK']
          and type(inspection.get('observed_at_ms')) is int and inspection['observed_at_ms']<=now
          and packet['inspection'].get('inspector_sha256')==INSPECTOR_SHA,'EXACT_INSPECTION_REQUIRED')
        need(sha(canonical(intent))==packet['root_intent_sha256'] and re.fullmatch(r'[a-f0-9]{64}',intent.get('helper_sha256','')),
          'ROOT_TASK_CLEANUP_INTENT_CHANGED')
        need(all(intent.get(k)==v for k,v in {'action_id':s['ACTION'],'task_id':s['TASK'],'approval_id':s['APPROVAL'],
          'inspection_sha256':packet['inspection_sha256'],
          'authority_sha256':packet['authority_sha256'],'no_replay':True}.items()),'ROOT_TASK_CLEANUP_INTENT_CHANGED')
        stage='authority_read';c=s['load_remote']('r11_common.py',COMMON_SHA);types+=(c.GuardFailure,)
        c.private_directory(s['REMOTE']);c.private_directory(s['CANARY']);c.service_pid();config=c.environment()
        marker_raw=c.protected_file(s['MARKER']);marker=json.loads(marker_raw)
        need(sha(marker_raw)==authority['next_marker_sha256'] and marker['approval_id']==s['APPROVAL']
          and marker['context_id']==s['CONTEXT'] and marker['pilot_id']==s['PILOT'] and marker['expires_at_ms']==EXPIRY
          and marker['binding_id']==c.BINDING and marker['root']==c.LOCAL_ROOT and marker['profile']==c.LOCAL_PROFILE
          and marker['requested_at_ms']<=now<EXPIRY,'EXACT_EXISTING_AUTHORITY_REQUIRED')
        bind=config.get('CONTROL_PLANE_BIND','127.0.0.1');need(bind in ('127.0.0.1','0.0.0.0','::',c.HOST),'SERVICE_BIND_CHANGED')
        origin='http://'+(c.HOST if bind==c.HOST else '127.0.0.1')+':'+config.get('CONTROL_PLANE_PORT','8765')
        health=c.api(origin,config['CONTROL_PLANE_OPERATOR_TOKEN'],'/healthz')
        need(health['service_instance_id']==inspection['service_instance_id']==authority['service_instance_id']
          and health['declared_source_revision']==c.REVISION and health['package_source_sha256']==c.PACKAGE,'EXACT_SERVER_CHANGED')
        database=Path(config['CONTROL_PLANE_DB']);before=read_exact(database,s);active=validate_before(before,inspection,c,s)
        stage='mcp_read_only_task_preflight';need(sha(c.protected_file(s['REMOTE']/'r13_5h_mcp_canary.py'))==CANARY_SHA,'FROZEN_CANARY_CHANGED')
        canary=s['load_remote']('r13_5h_mcp_canary.py',CANARY_SHA);types+=(canary.Failure,)
        mcp_origin,auth=canary.mcp_credentials(c)
        observation=canary.call(mcp_origin,auth,'task_control',{'operation':'task_observe','task_id':s['TASK']})
        validate_observation(observation,before,c,s)
        need(read_exact(database,s)==before,'ROWS_CHANGED_AFTER_READ_ONLY_PREFLIGHT')
        stage='exclusive_cleanup_intent';exclusive(s['CANARY']/'task-only-cleanup-intent.json',intent)
        need(read_exact(database,s)==before,'ROWS_CHANGED_BEFORE_CLEANUP')
        if active:
            stage='writer_release';need(int(time.time()*1000)<EXPIRY,'AUTHORITY_EXPIRED_BEFORE_CLEANUP');effect=True
            result=canary.call(mcp_origin,auth,'task_control',{'operation':'writer_release','task_id':s['TASK'],'reason':REASON})
            lease=result.get('writer_lease',{})
            need(result.get('execution')=='writer_lease_released'
              and lease.get('lease_generation')==active[0]['lease_generation'] and lease.get('task_id')==s['TASK']
              and lease.get('binding_id')==c.BINDING
              and lease.get('state')=='released' and type(lease.get('released_at_ms')) is int,'WRITER_RELEASE_UNCERTAIN_NO_RETRY')
            released_rows=read_exact(database,s);preserve(before,released_rows,s)
            exact=[r for r in released_rows['mcp_task_writer_leases'] if r['lease_id']==active[0]['lease_id']]
            need(len(exact)==1 and exact[0]['released_at_ms']==lease['released_at_ms'],'WRITER_RELEASE_RESPONSE_ROW_CHANGED')
        stage='task_close';need(int(time.time()*1000)<EXPIRY,'AUTHORITY_EXPIRED_BEFORE_CLEANUP');effect=True
        closed=canary.call(mcp_origin,auth,'workspace_context',{'operation':'task_close','task_id':s['TASK']}).get('task',{})
        need(closed.get('task_id')==s['TASK'] and type(closed.get('closed_at_ms')) is int,'TASK_CLOSE_UNCERTAIN_NO_RETRY')
        stage='final_preservation';after=read_exact(database,s);preserve(before,after,s,closed=True)
        need(after['mcp_task_sessions'][0]['closed_at_ms']==closed['closed_at_ms'],'TASK_CLOSE_RESPONSE_ROW_CHANGED')
        receipt={'phase':PHASE,'ok':True,'action_id':s['ACTION'],'task_id':s['TASK'],'terminal_receipt_id':NEW,
          'writer_released':True,'task_closed':True,'closed_at_ms':closed['closed_at_ms'],
          'action_and_receipt_history_preserved':True,'target_task_and_lease_history_preserved':True,
          'target_before_sha256':sha(canonical(before)),'target_after_sha256':sha(canonical(after)),
          'local_semantic_acceptance':'pending','checker_4_of_4':'not_observed','new_receipt_posted':False,
          'authority_extended':False,'replay_forbidden':True,'remote_mutation':True,'raw_error_disclosed':False}
        exclusive(s['CANARY']/'task-only-cleanup-completed.json',receipt)
        print(json.dumps(receipt,sort_keys=True,separators=(',',':')))
    except Exception as error:
        code=getattr(error,'code',None) if isinstance(error,types) else None
        if code is None and isinstance(error,types) and error.args:code=error.args[0]
        safe=code if isinstance(code,str) and re.fullmatch(r'[A-Z0-9_]{1,128}',code) else 'SAFE_TASK_ONLY_CLEANUP_FAILED'
        print(json.dumps({'phase':PHASE,'ok':False,'stage':stage,'code':safe,'remote_mutation_possible':effect,
          'new_receipt_posted':False,'replay_forbidden':True,'next_action':'read_only_inspect_no_retry','raw_error_disclosed':False},sort_keys=True,separators=(',',':')))
        raise SystemExit(2) from None
