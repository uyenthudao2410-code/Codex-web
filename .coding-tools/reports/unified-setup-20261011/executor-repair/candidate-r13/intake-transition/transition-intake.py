"""One newly approved r13 pilot rotation within the unchanged r12 window; no deployment/restart."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import time

REMOTE=Path('/home/svhome/.local/lib/codex-control-plane/incoming/r11-approved-20261011T194930649730Z')
COMMON_SHA='c55d9d07144654ca0216d55c8de8b20c1a238a9a722ac455d6c83ec0d406e36f'
PRIOR=Path('/home/svhome/.local/state/codex-control-plane/owner-operations/r12-initial-verification-60m/authority-renewal-public.json')
PRIOR_SHA='a3c5c2ee239644a3937fa5f81c7fc14b89544bfde82c4bea56a928ddda408487'
OUT=PRIOR.parent.parent/'r13-same-window-transition'
MARKER=OUT/'transition-public.json'
CANARY=OUT/'canary-r13'
CONTEXT='ctx_d7a539dd85264a62951fddad0ffa2f23'
OLD_PILOT='pilot_98c0b502568a4f888b3106838004c117'
REQUESTED=1791747735200
EXPIRES=1791751335200
OLD_APPROVAL='call_1KzUkF0gMn6uVpHd3QisTzXF'
APPROVAL='r13-same-window-transition'
OPERATION='owner_approved_r13_same_window_pilot_rotation'
REASON='Owner-approved r13 runtime transition: replacement pilot for exact Tools-Codex-web with unchanged context and expiry'
MIN_REMAINING=720000
R12_ACTION='act_6aa1329b96c146f38c807f9926b3e684'
R12_TASK='task_d2c1dd3bff4042d084b045e9bc5a381b'
R12_REJECTION='rcpt_b714c82d5e4a4328b072129f3675b78b'

class Failure(Exception):pass
def need(ok,code):
    if not ok:raise Failure(code)
def now():return int(time.time()*1000)
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def window(observed):
    need(type(observed) is int and REQUESTED<=observed and EXPIRES-observed>=MIN_REMAINING,'UNCHANGED_WINDOW_REQUIRES_12M_NO_EXTENSION')
def load_common():
    p=REMOTE/'r11_common.py';need(sha(p.read_bytes())==COMMON_SHA,'FROZEN_COMMON_CHANGED')
    spec=importlib.util.spec_from_file_location('r13_frozen_common',p)
    c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);return c
def exclusive(path,value):
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:f.write(canonical(value));f.flush();os.fsync(f.fileno())
def save(value):
    fd,tmp=tempfile.mkstemp(prefix='.r13-transition-',dir=OUT)
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'wb') as f:f.write(canonical(value));f.flush();os.fsync(f.fileno())
        os.replace(tmp,MARKER)
    finally:Path(tmp).unlink(missing_ok=True)
def authority(database):
    d=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True,timeout=5)
    try:
        d.row_factory=sqlite3.Row;d.execute('PRAGMA query_only=ON');d.execute('BEGIN')
        return {name:[dict(r) for r in d.execute('SELECT * FROM '+name+' ORDER BY rowid')]
                for name in ('contexts','scoped_pilot_decisions')}
    finally:d.close()
def cleanup(database):
    d=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True,timeout=5)
    try:
        d.row_factory=sqlite3.Row;d.execute('PRAGMA query_only=ON');d.execute('BEGIN')
        a=d.execute('SELECT delivery_state FROM actions WHERE action_id=?',(R12_ACTION,)).fetchall()
        t=d.execute('SELECT closed_at_ms FROM mcp_task_sessions WHERE task_id=?',(R12_TASK,)).fetchall()
        r=d.execute('SELECT receipt_state FROM receipts WHERE receipt_id=? AND action_id=?',(R12_REJECTION,R12_ACTION)).fetchall()
        leases=d.execute('SELECT released_at_ms FROM mcp_task_writer_leases WHERE task_id=?',(R12_TASK,)).fetchall()
        need(len(a)==len(t)==len(r)==1 and a[0][0]=='settled' and type(t[0][0]) is int
             and r[0][0]=='rejected' and all(type(v[0]) is int for v in leases),'EXACT_R12_SETTLEMENT_AND_TASK_CLOSE_REQUIRED')
    finally:d.close()
def target_context(rows,c):
    selected=[r for r in rows['contexts'] if r['context_id']==CONTEXT]
    need(len(selected)==1 and selected[0]['binding_id']==c.BINDING and selected[0]['device_id']==c.DEVICE
         and selected[0]['workspace_id']==c.WORKSPACE and selected[0]['workspace_generation']==c.GENERATION
         and selected[0]['expires_at_ms']==EXPIRES and selected[0]['closed_at_ms'] is None,'EXISTING_CONTEXT_SCOPE_OR_WINDOW_CHANGED')
def prior(c,grant):
    raw=c.protected_file(PRIOR);m=json.loads(raw)
    need(sha(raw)==PRIOR_SHA and m['phase']=='intake_reopened' and m['approval_id']==OLD_APPROVAL
         and m['binding_id']==c.BINDING and m['device_id']==c.DEVICE and m['workspace_id']==c.WORKSPACE
         and m['workspace_generation']==c.GENERATION and m['root']==c.LOCAL_ROOT and m['profile']==c.LOCAL_PROFILE
         and m['context_id']==CONTEXT and m['pilot_id']==OLD_PILOT and m['requested_at_ms']==REQUESTED
         and m['expires_at_ms']==EXPIRES and m['service_grant_sha256']==c.digest(grant),'IMMUTABLE_R12_AUTHORITY_CHANGED')
    return m
def validate_rotation(rows,m,c):
    need(rows['contexts']==m['authority_baseline']['contexts'],'CONTEXT_HISTORY_CHANGED')
    baseline=m['authority_baseline']['scoped_pilot_decisions'];current=rows['scoped_pilot_decisions']
    old_ids={r['decision_id'] for r in baseline}
    for old in baseline:
        matches=[r for r in current if r['decision_id']==old['decision_id']];need(len(matches)==1,'PILOT_HISTORY_MISSING')
        expected=dict(old)
        if old['decision_id']==OLD_PILOT:expected['revoked_at_ms']=m['old_pilot_revoked_at_ms']
        need(matches[0]==expected,'UNRELATED_PILOT_HISTORY_CHANGED')
    added=[r for r in current if r['decision_id'] not in old_ids]
    need(len(added)==1,'ONE_REPLACEMENT_PILOT_REQUIRED')
    row=added[0]
    need(row['decision_id']==m['pilot_id'] and row['decision_id']!=OLD_PILOT
         and re.fullmatch(r'pilot_[a-f0-9]{32}',row['decision_id']) and row['binding_id']==c.BINDING
         and row['principal_id']==c.PRINCIPAL and row['device_id']==c.DEVICE and row['workspace_id']==c.WORKSPACE
         and row['workspace_generation']==c.GENERATION and row['expires_at_ms']==EXPIRES
         and row['revoked_at_ms'] is None and row['reason']==REASON,'EXACT_REPLACEMENT_PILOT_CHANGED')
    need([r['decision_id'] for r in current if r['revoked_at_ms'] is None]==[row['decision_id']],'UNRELATED_UNREVOKED_PILOT')
    return row
def read_marker(c):
    if not MARKER.exists():need(not MARKER.is_symlink(),'MARKER_SYMLINK');return None,None
    raw=c.protected_file(MARKER);return json.loads(raw),sha(raw)
def marker_scope(m,c,grant):
    need(m['operation']==OPERATION and m['approval_id']==APPROVAL and m['context_id']==CONTEXT and m['old_pilot_id']==OLD_PILOT
         and m['requested_at_ms']==REQUESTED and m['expires_at_ms']==EXPIRES
         and m['prior_marker_sha256']==PRIOR_SHA and m['service_grant_sha256']==c.digest(grant)
         and m['binding_id']==c.BINDING and m['device_id']==c.DEVICE and m['workspace_id']==c.WORKSPACE
         and m['workspace_generation']==c.GENERATION and m['root']==c.LOCAL_ROOT and m['profile']==c.LOCAL_PROFILE,
         'R13_MARKER_SCOPE_CHANGED')
def public(c,health,state,overview,grant,m,marker_sha):
    result={'phase':'r13_intake_observation','ok':True,'host':c.HOST,'service':c.SERVICE,
      'device_id':c.DEVICE,'workspace_id':c.WORKSPACE,'workspace_generation':c.GENERATION,
      'root':c.LOCAL_ROOT,'profile':c.LOCAL_PROFILE,'capabilities':{'read':True,'write':True,'exec':True},
      'operation':OPERATION,'next_phase':m['phase'] if m else 'not_started','prior_marker_sha256':PRIOR_SHA,
      'next_marker_sha256':marker_sha or 'absent','context_id':CONTEXT,'requested_at_ms':REQUESTED,'expires_at_ms':EXPIRES,
      'pilot_id':m['pilot_id'] if m and 'pilot_id' in m else OLD_PILOT,'old_pilot_id':OLD_PILOT,
      'approval_id':m.get('approval_id') if m else None,'minimum_canary_remaining_ms':MIN_REMAINING,
      'canary_directory':str(CANARY),'authority_extended':False,'context_preserved':True,'window_preserved':True,
      'policy_assignment':{'binding_id':c.BINDING,'device_id':c.DEVICE,'workspace_id':c.WORKSPACE,
        'workspace_generation':c.GENERATION,'root':c.LOCAL_ROOT,'profile':c.LOCAL_PROFILE,'context_id':CONTEXT,'expires_at_ms':EXPIRES},
      **c.public_observation(health,state,overview,grant)}
    if m and 'pilot_id' in m:
        result.update(old_pilot_revoked_at_ms=m['old_pilot_revoked_at_ms'],replacement_pilot_live=True,
          old_pilot={'decision_id':OLD_PILOT,'revoked_at_ms':m['old_pilot_revoked_at_ms'],'expires_at_ms':EXPIRES},
          replacement_pilot={'decision_id':m['pilot_id'],'revoked_at_ms':None,'expires_at_ms':EXPIRES})
    return result
def main(packet):
    action=packet.get('action');need(action in ('observe','pause-rotate','reopen'),'ACTION_INVALID')
    c=load_common();origin,auth,database,health,state,overview,grant=c.inspect()
    need(health['declared_source_revision']==c.REVISION and health['package_source_sha256']==c.PACKAGE,'NO_SERVER_RELEASE_CHANGE_ALLOWED')
    prior(c,grant);cleanup(database);rows=authority(database);target_context(rows,c);window(now())
    m,marker_sha=read_marker(c)
    if m:
        marker_scope(m,c,grant)
        need(m['service_instance_id']==health['service_instance_id'],'SERVER_INSTANCE_CHANGED_DURING_TRANSITION')
        if m['phase'] in ('authority_rotated_in_recovery','intake_reopened'):
            c.compare_history(m['initial_state'],state);validate_rotation(rows,m,c)
    if action=='observe':
        print(json.dumps(public(c,health,state,overview,grant,m,marker_sha),separators=(',',':')));return
    approval=packet.get('approval_id')
    need(packet.get('execute') is True and packet.get('operator_approved') is True
         and approval==APPROVAL,'NEW_EXPLICIT_R13_APPROVAL_REQUIRED')
    expected=packet.get('server',{});expected=expected.get('public_receipts',[expected]);need(len(expected)==1,'EXACT_SERVER_RECEIPT_REQUIRED');expected=expected[0]
    need(expected.get('ok') is True and expected.get('service_instance_id')==health['service_instance_id']
         and expected.get('state_sha256')==c.digest(state) and expected.get('service_grant_sha256')==c.digest(grant)
         and expected.get('next_marker_sha256')==(marker_sha or 'absent')
         and type(expected.get('observed_at_ms')) is int and 0<=now()-expected['observed_at_ms']<60000,
         'FRESH_EXACT_SERVER_PINS_REQUIRED')
    lock=c.operation_lock()
    try:
        # Re-read after acquiring the owner lock; the earlier observation alone is not a mutation fence.
        locked_state=c.state(database);c.compare_history(state,locked_state)
        need(authority(database)==rows,'AUTHORITY_CHANGED_BEFORE_FIRST_EFFECT')
        locked_health=c.api(origin,auth,'/healthz');locked_overview=c.api(origin,auth,'/v1/ui/overview')
        need(locked_health['service_instance_id']==health['service_instance_id']
             and locked_health['declared_source_revision']==c.REVISION and locked_health['package_source_sha256']==c.PACKAGE
             and locked_overview['admission']['admission_mode']==overview['admission']['admission_mode']
             and c.digest(c.target(locked_overview))==c.digest(grant),'SERVICE_ADMISSION_OR_GRANT_CHANGED_BEFORE_EFFECT')
        need(read_marker(c)[1]==marker_sha and 0<=now()-expected['observed_at_ms']<60000,'MARKER_OR_FRESH_PIN_CHANGED_BEFORE_EFFECT')
        overview=locked_overview
        if action=='pause-rotate':
            need(m is None and not OUT.exists() and not OUT.is_symlink(),'R13_TRANSITION_ALREADY_EXISTS_NO_REPLAY')
            need(overview['admission']['admission_mode']=='scoped_pilot','INITIAL_SCOPED_INTAKE_REQUIRED')
            live=[r for r in rows['scoped_pilot_decisions'] if r['revoked_at_ms'] is None]
            need(len(live)==1 and live[0]['decision_id']==OLD_PILOT and live[0]['expires_at_ms']==EXPIRES
                 and live[0]['binding_id']==c.BINDING and live[0]['principal_id']==c.PRINCIPAL,'ONLY_EXACT_OLD_PILOT_MAY_BE_REVOKED')
            c.private_directory(OUT,create=True)
            m={'operation':OPERATION,'phase':'pause_intended','approval_id':approval,'prior_marker_sha256':PRIOR_SHA,
               'context_id':CONTEXT,'old_pilot_id':OLD_PILOT,'requested_at_ms':REQUESTED,'expires_at_ms':EXPIRES,
               'binding_id':c.BINDING,'device_id':c.DEVICE,'workspace_id':c.WORKSPACE,'workspace_generation':c.GENERATION,
               'root':c.LOCAL_ROOT,'profile':c.LOCAL_PROFILE,'service_instance_id':health['service_instance_id'],
               'service_grant_sha256':c.digest(grant),'initial_state':state,'authority_baseline':rows}
            exclusive(OUT/'pause-rotate-intent.json',{'approval_id':approval,'old_pilot_id':OLD_PILOT,'expires_at_ms':EXPIRES,'no_replay':True});save(m)
            window(now());c.api(origin,auth,'/v1/maintenance/admission',{'mode':'recovery'})
            # Recovery closes future admissions; refuse rotation if any work was admitted during the boundary.
            c.compare_history(state,c.state(database))
            revoked=authority(database);need(revoked['contexts']==rows['contexts'],'CONTEXT_CHANGED_DURING_PAUSE')
            old=next(r for r in revoked['scoped_pilot_decisions'] if r['decision_id']==OLD_PILOT)
            need(type(old['revoked_at_ms']) is int and not any(r['revoked_at_ms'] is None for r in revoked['scoped_pilot_decisions']),
                 'RECOVERY_DID_NOT_REVOKE_EXACT_PILOT')
            need([{**r,'revoked_at_ms':None} if r['decision_id']==OLD_PILOT else r for r in revoked['scoped_pilot_decisions']]
                 ==rows['scoped_pilot_decisions'],'UNRELATED_PILOT_CHANGED_DURING_PAUSE')
            m.update(phase='pilot_create_intended',old_pilot_revoked_at_ms=old['revoked_at_ms']);save(m)
            window(now());created=c.api(origin,auth,'/v1/scoped-pilot-decisions',{'principal_id':c.PRINCIPAL,
               'binding_id':c.BINDING,'expires_at_ms':EXPIRES,'reason':REASON})
            need(isinstance(created.get('decision_id'),str),'PILOT_CREATE_RESPONSE_UNCERTAIN_NO_RETRY')
            m.update(pilot_id=created['decision_id'],phase='authority_rotated_in_recovery')
            validate_rotation(authority(database),m,c)
            CANARY.mkdir(mode=0o700);c.private_directory(CANARY)
            save(m)
        else:
            need(m and m['phase']=='authority_rotated_in_recovery' and m['approval_id']==approval,'EXACT_ROTATED_R13_PHASE_REQUIRED')
            need(overview['admission']['admission_mode']=='recovery','RECOVERY_REQUIRED_BEFORE_REOPEN')
            c.renewed_authority(overview,m);validate_rotation(rows,m,c)
            node=next(r for r in overview['nodes'] if r['device_id']==c.DEVICE)
            ident=packet.get('native_identity',{})
            for key in ('activation_epoch','runtime_instance_id','mcp_server_instance_id','contract_version'):
                need(isinstance(ident.get(key),str) and ident[key] and ident[key]==node.get(key),'EXACT_NEW_R13_NODE_IDENTITY_REQUIRED')
            need(0<=overview['observed_at_ms']-node.get('last_seen_at_ms',0)<60000 and node.get('readiness')=='ready'
                 and node.get('policy_state')=='enabled' and type(node.get('policy_expires_at_ms')) is int
                 and overview['observed_at_ms']<node['policy_expires_at_ms']<=node['last_seen_at_ms']+60000,
                 'FRESH_READY_NODE_POLICY_REQUIRED')
            exclusive(OUT/'reopen-intent.json',{'approval_id':approval,'pilot_id':m['pilot_id'],'native_identity':ident,'no_replay':True})
            window(now());c.api(origin,auth,'/v1/maintenance/admission',{'mode':'scoped_pilot'})
            m.update(phase='intake_reopened',**ident);save(m)
        fresh_state=c.state(database);c.compare_history(m['initial_state'],fresh_state)
        fresh_overview=c.api(origin,auth,'/v1/ui/overview');validate_rotation(authority(database),m,c);prior(c,grant)
        need(fresh_overview['admission']['admission_mode']==('recovery' if action=='pause-rotate' else 'scoped_pilot'),'EXPECTED_ADMISSION_NOT_CONFIRMED')
        window(now());print(json.dumps({**public(c,health,fresh_state,fresh_overview,grant,m,sha(c.protected_file(MARKER))),
           'remote_mutation':True,'no_replay':True,'server_deployed_or_restarted':False,'context_created':False},separators=(',',':')))
    finally:os.close(lock)
