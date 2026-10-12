"""Exact read-only observation of consumed settlement; no replay or cleanup."""
import base64
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time

PIN='30f0169c0acb39bb888178e1326a220d175d936a39208397f358eb1eb0b0ed0f'
COMMON='25f2d15359ff49a50e1ded411d40f1f029fb6067390c68aff9b93bda0130d986'
NEW='rcpt_eea61400c4a3408d88bfec9174b75ec7'
PAYLOAD='b685d64c650b907f9f82d0d1626b0aee7797edea7c83acfdb25a1e56fdb6c8b5'
MARKERS=('after-effect-reconciliation-intent.json','after-effect-terminal-receipt.json',
 'after-effect-task-close-intent.json','after-effect-task-closed.json')
PHASE='r13_5h_after_effect_settlement_read_only_inspection'

class Failure(Exception):pass
def need(ok,code):
    if not ok:raise Failure(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def forbidden(*args,**kwargs):raise Failure('MUTATION_FORBIDDEN_IN_INSPECTION')

def load(packet):
    raw=base64.b64decode(packet['settlement_source_b64'],validate=True)
    need(len(raw)<=262144 and sha(raw)==PIN==packet['settlement_source_sha256'],'IMMUTABLE_HELPER_CHANGED')
    s={'__name__':'read_only_settlement_functions'}
    exec(compile(raw,'<immutable-readonly-settlement-functions>','exec'),s)
    s['main']=s['exclusive']=s['public']=forbidden
    return s

def markers(c,s,evidence):
    rows={}
    for name in MARKERS:
        p=s['CANARY']/name
        if not p.exists() and not p.is_symlink():rows[name]={'exists':False};continue
        raw=c.protected_file(p);need(len(raw)<=262144,'EXACT_MARKER_TOO_LARGE')
        value=json.loads(raw);need(isinstance(value,dict),'EXACT_MARKER_NOT_OBJECT')
        need(value.get('action_id',s['ACTION'])==s['ACTION'] and value.get('task_id',s['TASK'])==s['TASK'],'EXACT_MARKER_TARGET_CHANGED')
        if name==MARKERS[0]:need(value.get('evidence')==evidence,'REMOTE_INTENT_EVIDENCE_CHANGED')
        if name==MARKERS[1]:need(value.get('receipt_id')==NEW,'TERMINAL_MARKER_RECEIPT_CHANGED')
        rows[name]={'exists':True,'sha256':sha(raw),'size_bytes':len(raw)}
    return rows

def read_family(database,c,s,expected):
    need(database.is_absolute() and database.is_file() and not database.is_symlink(),'DATABASE_TARGET_UNSAFE')
    d=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True,timeout=5)
    try:
        d.row_factory=sqlite3.Row;d.execute('PRAGMA query_only=ON');d.execute('BEGIN')
        rows=lambda sql,key:[dict(r) for r in d.execute(sql,(key,))]
        actions=rows('SELECT * FROM actions WHERE action_id=?',s['ACTION'])
        receipts=rows('SELECT * FROM receipts WHERE action_id=? ORDER BY received_at_ms,receipt_id',s['ACTION'])
        tasks=rows('SELECT * FROM mcp_task_sessions WHERE task_id=?',s['TASK'])
        leases=rows('SELECT * FROM mcp_task_writer_leases WHERE task_id=? ORDER BY lease_id',s['TASK'])
        attempts=rows('SELECT attempt_id,attempt_number,dispatched_at_ms FROM delivery_attempts WHERE action_id=?',s['ACTION'])
        links=rows('SELECT task_id FROM mcp_task_action_links WHERE action_id=?',s['ACTION'])
    finally:d.close()
    need(len(actions)==len(tasks)==1 and len(receipts)==2 and len(leases)<=32,'EXACT_FAMILY_COUNTS_CHANGED')
    a,t=actions[0],tasks[0]
    target={'binding_id':c.BINDING,'device_id':c.DEVICE,'workspace_id':c.WORKSPACE,'workspace_generation':c.GENERATION}
    need(all(a.get(k)==v and t.get(k)==v for k,v in target.items()) and t.get('principal_id')==c.PRINCIPAL,'EXACT_FAMILY_TARGET_CHANGED')
    need(a.get('context_id')=='ctx_b7d6fe51fc7c4aaaaba2947ad8c98e43' and a.get('request_id')=='req_3f80be12f4914928a73f41974980c339','EXACT_ACTION_CONTEXT_CHANGED')
    need(attempts==[{'attempt_id':s['ATTEMPT'],'attempt_number':1,'dispatched_at_ms':1791759246011}] and links==[{'task_id':s['TASK']}],'EXACT_ATTEMPT_OR_LINK_CHANGED')
    old=[r for r in receipts if r['receipt_id']==s['UNKNOWN']];new=[r for r in receipts if r['receipt_id']==NEW]
    need(len(old)==len(new)==1 and old[0]['receipt_state']=='unknown' and sha(old[0]['payload_json'].encode())==s['UNKNOWN_PAYLOAD'],'ORIGINAL_UNKNOWN_CHANGED')
    need(new[0]['receipt_state']=='failed' and sha(new[0]['payload_json'].encode())==PAYLOAD and json.loads(new[0]['payload_json'])==expected,'EXACT_FAILED_RECEIPT_CHANGED')
    initial={'actions':[{**a,'delivery_state':'reconcile_required','settled_at_ms':None}],'receipts':old}
    final={'actions':actions,'receipts':receipts}
    try:
        s['verify_failure'](initial,final,NEW,expected,c.DEVICE);guard={'status':'passed'}
    except s['Failure'] as error:
        code=str(error);need(re.fullmatch(r'[A-Z0-9_]{1,128}',code),'UNSAFE_GUARD_CODE')
        guard={'status':'failed','code':code}
    active=[r for r in leases if r['released_at_ms'] is None]
    need(all(r.get('binding_id')==c.BINDING and r.get('principal_id')==c.PRINCIPAL and r.get('owner_id')==t['owner_id'] for r in leases),'EXACT_LEASE_TARGET_CHANGED')
    return {'action_id':s['ACTION'],'task_id':s['TASK'],'delivery_state':a['delivery_state'],'settled_at_ms':a['settled_at_ms'],
      'action_row_sha256':sha(canonical(a)),'receipts':[{'receipt_id':r['receipt_id'],'receipt_state':r['receipt_state'],
        'received_at_ms':r['received_at_ms'],'payload_sha256':sha(r['payload_json'].encode()),'receipt_digest':r['receipt_digest'],
        'row_sha256':sha(canonical(r))} for r in receipts],
      'original_unknown_hash_preserved':True,'exact_failed_receipt_payload_preserved':True,'task_closed':t['closed_at_ms'] is not None,
      'task_closed_at_ms':t['closed_at_ms'],'task_row_sha256':sha(canonical(t)),
      'active_writer_count':len(active),'lease_history':[{'lease_id':r['lease_id'],'lease_generation':r['lease_generation'],
        'released_at_ms':r['released_at_ms'],'row_sha256':sha(canonical(r))} for r in leases],
      'reconstructed_verify_failure':guard,'original_full_row_baseline_available':False,
      'reconstruction_is_original_history_proof':False,'query_only':True}

def main(packet):
    stage='input';types=(Failure,)
    try:
        need(packet.get('read_only') is True and packet.get('approval_id')=='call_a60e931056bd402b997c6c10b0796d81','EXPLICIT_READ_ONLY_REQUIRED')
        s=load(packet);types+=(s['Failure'],);native=packet['native'];root=packet['root_intent'];evidence=root['evidence_sha256']
        need(root.get('helper_sha256')==PIN and root.get('action_id')==s['ACTION'] and root.get('task_id')==s['TASK'],'EXACT_ROOT_INTENT_CHANGED')
        need(all(evidence.get(k)==packet.get(k+'_sha256') for k in ('query','native','authority')) and sha(canonical(root['root_census']))==evidence['root_census'],'EXACT_ROOT_EVIDENCE_CHANGED')
        s['validate_native'](native);s['validate_query'](s['unwrap'](packet['query']))
        stage='frozen_common';c=s['load_remote']('r11_common.py',COMMON);types+=(c.GuardFailure,)
        c.private_directory(s['REMOTE']);c.private_directory(s['CANARY']);c.service_pid()
        stage='service_health';config=c.environment();bind=config.get('CONTROL_PLANE_BIND','127.0.0.1')
        need(bind in ('127.0.0.1','0.0.0.0','::',c.HOST),'SERVICE_BIND_CHANGED')
        origin='http://'+(c.HOST if bind==c.HOST else '127.0.0.1')+':'+config.get('CONTROL_PLANE_PORT','8765')
        health=c.api(origin,config['CONTROL_PLANE_OPERATOR_TOKEN'],'/healthz')
        need(health['service_instance_id']==s['unwrap'](packet['query'])['service_instance_id'] and health['declared_source_revision']==c.REVISION and health['package_source_sha256']==c.PACKAGE,'EXACT_SERVER_CHANGED')
        stage='marker_chain';chain=markers(c,s,evidence)
        stage='exact_family';result=read_family(Path(config['CONTROL_PLANE_DB']),c,s,s['build_payload'](native,evidence))
        stage='canary_hash';canary_sha=None;canary_state='missing_or_unsafe'
        try:
            canary_raw=c.protected_file(s['REMOTE']/'r13_5h_mcp_canary.py');canary_sha=sha(canary_raw);canary_state='observed'
        except Exception:pass
        expected='cd91a622d76f19873adc4c7671f6b72d59ba99cac639957c04a1413cb06df104'
        interval='post_POST_helper_boundary_unproven'
        if chain[MARKERS[1]]['exists'] and not chain[MARKERS[2]]['exists']:interval='after_terminal_marker_before_task_close_intent'
        elif chain[MARKERS[2]]['exists'] and not chain[MARKERS[3]]['exists']:interval='after_task_close_intent_before_task_closed_marker'
        elif chain[MARKERS[3]]['exists']:interval='after_task_closed_marker'
        result.update(phase=PHASE,ok=True,observed_at_ms=int(time.time()*1000),service_instance_id=health['service_instance_id'],
          marker_chain=chain,stop_boundary=interval,frozen_canary_state=canary_state,frozen_canary_sha256=canary_sha,frozen_canary_pin_matches=canary_sha==expected,
          remote_mutation=False,database_query_only=True,raw_rows_disclosed=False,raw_error_disclosed=False,replay_forbidden=True,
          mcp_calls=0,mutation_api_calls=0,patch_no_effect_claimed=False)
        print(json.dumps(result,sort_keys=True,separators=(',',':')))
    except Exception as error:
        value=str(error) if isinstance(error,types) else ''
        code=value if re.fullmatch(r'[A-Z0-9_]{1,128}',value) else 'SAFE_READ_ONLY_INSPECTION_FAILED'
        print(json.dumps({'phase':PHASE,'ok':False,'failed_stage':stage,'code':code,'remote_mutation':False,
          'raw_error_disclosed':False,'replay_forbidden':True},sort_keys=True,separators=(',',':')))
        raise SystemExit(2) from None
