"""Root-only three direct r14 admission phases under the unchanged five-hour authority."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import time

REMOTE=Path('/home/svhome/.local/lib/codex-control-plane/incoming/r11-approved-20261011T225341342686Z')
COMMON_SHA='25f2d15359ff49a50e1ded411d40f1f029fb6067390c68aff9b93bda0130d986'
DIRECTORY=Path('/home/svhome/.local/state/codex-control-plane/owner-operations/r14-same-window-activation')
MARKER=DIRECTORY/'authority-transition-public.json'
R13_MARKER=DIRECTORY.parent/'r13-initial-verification-5h/authority-renewal-public.json'
OPERATION='owner_approved_r14_same_window_activation'
CONTEXT='ctx_1e7e2fec6f0e43018db7a51c6980e5c2'
PRIOR='pilot_b1cb26c319fb489aae24d3b746318447'
REQUESTED=1791758571067
EXPIRES=1791776571067
SERVICE='cp_339c7a19bc2443eeab35583addfef543'
WINDOW_APPROVAL='call_a60e931056bd402b997c6c10b0796d81'
HEAD='2c554f59cb7b8ffc86ce5e0e28076c792777642f'
WINDOWS_MANIFEST='77ab6e95eef25874c309d6233cf0f3f855f7b8f39ed14ffe03455e55de76b389'
WINDOWS_TRANSITION='b875e90526322528ae4406492b7915ed9ce049a28943d9c5f661e26fd07e0d74'
R14_INSTALLATION='779594f2a05ae6bcf0a5a23d7c9d451330aab3636f4f3774b4b1251a2353dc96'
CONTRACT='0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4'
TARGET={'binding_id':'bind_3e05bf64cb3e4bab93d930ae1692bebb','device_id':'72ceec2d-e3f2-472f-8e3c-99fffe053035',
 'workspace_id':'workspace_dda1d78e9a21402aa6213f72af64f788','workspace_generation':'generation_c2f13e8d02344cf6a38a3f42ecfa59b6',
 'owner_id':'owner_default','endpoint_id':'executor-72ceec2d-e3f2-472f-8e3c-99fffe053035',
 'server_origin':'https://svhome.tail0e4032.ts.net','root':r'E:\Github\Tools-Codex-web','profile':'web-mcp-assistant'}

class Failure(Exception):pass
def need(ok,code):
    if not ok:raise Failure(code)
def now():return int(time.time()*1000)
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def unwrap(value):
    rows=value.get('public_receipts',[value]);need(len(rows)==1,'ONE_PUBLIC_RECEIPT_REQUIRED');return rows[0]
def exclusive(path,value):
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:f.write(canonical(value));f.flush();os.fsync(f.fileno())
def common():
    p=REMOTE/'r11_common.py';need(sha(p.read_bytes())==COMMON_SHA,'FROZEN_COMMON_CHANGED')
    spec=importlib.util.spec_from_file_location('frozen_r14_same_window_common',p)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

def approval(value,approval_id):
    need(value.get('approved') is True and value.get('source')=='human_user_response' and value.get('approval_id')==approval_id
      and re.fullmatch(r'call_[A-Za-z0-9_-]+',approval_id) and approval_id not in (WINDOW_APPROVAL,'call_1KzUkF0gMn6uVpHd3QisTzXF')
      and value.get('operation')==OPERATION and value.get('candidate_tag')=='workflow-timeout-1012-r14'
      and value.get('context_id')==CONTEXT and value.get('expires_at_ms')==EXPIRES and value.get('target')==TARGET
      and type(value.get('approved_at_ms')) is int and value['approved_at_ms']<=now()<EXPIRES,
      'EXPLICIT_FUTURE_R14_APPROVAL_REQUIRED')
    need(all(value.get(k) is True for k in ('pilot_replacement_same_principal_binding_expiry','r13_owned_executor_cleanup_refresh','new_approved_patch_verification_canary'))
      and all(value.get(k) is False for k in ('authority_extension','ubuntu_deploy_or_restart','windows_reboot','semantic_acceptance')),
      'EXACT_R14_OPERATION_SCOPE_REQUIRED')

def windows(value,phase):
    need(type(value.get('observed_at_ms')) is int and 0<=now()-value['observed_at_ms']<60000,'FRESH_WINDOWS_RECEIPT_REQUIRED')
    if phase=='close':need(value.get('target')==TARGET and value.get('repository_head')==HEAD,'EXACT_WINDOWS_TARGET_REQUIRED')
    package=value.get('package',{})
    need(package.get('candidate_tag')=='workflow-timeout-1012-r14' and package.get('matched_files')==17
      and package.get('helper_manifest_sha256')==WINDOWS_MANIFEST
      and package.get('app_asar_sha256')=='f2a1e77b08f7109ccbd4072055da8d281a339dd5f32f154285d3696ad11f6324'
      and package.get('executable_sha256')=='8270535a8149b54527172f9b774ea1fd6ed975fde44e4bb91022bdde31dea154'
      and package.get('source_freeze_sha256')=='a618711528b418db77a901a5b83537bde2d511618ef630ab22670a2e6579625d'
      and package.get('parity_sha256')=='59e4a0af303424a42db59831f83e8205420f6143a446f530bd9a9a272d4ae51a',
      'EXACT_FROZEN_R14_PACKAGE_PROOF_REQUIRED')
    counts=value.get('census',{}).get('counts',{})
    need(all(type(counts.get(k)) is int and counts[k]==0 for k in ('active_tool_calls','active_commands','starting_commands','active_background_operations','active_managed_processes','foreign_heavy_processes','active_agent_lanes','owned_codex_sidecar_residues')),
      'WINDOWS_NOT_QUIESCENT')
    identity=value.get('native_identity',{})
    need(identity.get('mcp_ready') is True and identity.get('identity_current') is True
      and identity.get('tool_contract_sha256')==CONTRACT and identity.get('activation_epoch_id')==identity.get('current_activation_epoch_id'),
      'FRESH_NATIVE_IDENTITY_REQUIRED')
    if phase=='close':
        need(value.get('kind')=='r14_read_only_transition_preparation' and value.get('current_runtime_tag')=='source-fingerprint-1012-r13'
          and value.get('authority_expires_at_ms')==EXPIRES and identity.get('mcp_process_instance_id')=='6UTUCFZxzWswLzYo'
          and identity.get('mcp_server_instance_id')=='N-RYdpKzr66ftnM5','EXACT_R13_PRECLOSE_OBSERVATION_REQUIRED')
    else:
        need(value.get('phase')=='r14_final_runtime_proof' and value.get('ok') is True and value.get('epoch',{}).get('state')=='READY'
          and value.get('semantic_acceptance_performed') is False and value.get('live_sandbox_exec_proven') is False,
          'REAL_R14_FINAL_RUNTIME_PROOF_REQUIRED')
        need(value.get('tag')=='r14' and value.get('helper_sha256')==WINDOWS_TRANSITION
          and value.get('owner',{}).get('state')=='live' and value.get('native',{}).get('state')=='live'
          and value.get('readiness',{}).get('fullyReady') is True and value.get('epoch',{}).get('update_incomplete') is False
          and value.get('ubuntu_deployed_or_restarted') is False and value.get('windows_rebooted') is False,
          'EXACT_FROZEN_R14_OWNER_READY_PROOF_REQUIRED')
        descriptor=value.get('descriptor',{});ui=value.get('ui',{})
        need(descriptor.get('installation_id')==R14_INSTALLATION and descriptor.get('owner_pid')==value['owner'].get('pid')
          and ui.get('alive') is True and ui.get('registered') is True and ui.get('ui_installation_id')==R14_INSTALLATION
          and identity.get('recovery_host_instance_id')==descriptor.get('instance_id')
          and identity['activation_epoch_id']==value['epoch'].get('activation_epoch_id')
          and identity['activation_epoch_id']!='activation-mv4f0vbd-d6ff8f434f6de1929cedd4266c042dcd'
          and identity.get('mcp_process_instance_id') not in (None,'','6UTUCFZxzWswLzYo')
          and identity.get('mcp_server_instance_id') not in (None,'','N-RYdpKzr66ftnM5'),'EXACT_NEW_R14_INSTALLATION_IDENTITY_REQUIRED')
        route=value.get('central_route',{});evidence=route.get('evidence',{})
        need(route.get('connected') is True and route.get('authorityReady') is True and route.get('reason')=='CENTRAL_ROUTE_READY'
          and evidence.get('serverOrigin')==TARGET['server_origin'] and evidence.get('deviceId')==TARGET['device_id']
          and evidence.get('endpointId')==TARGET['endpoint_id'],'EXACT_R14_ROUTE_SCOPE_REQUIRED')
        vm=value.get('vm_zero',{});need(vm.get('host_count')==0 and vm.get('backend_count')==0,'R14_EXECUTOR_NOT_ZERO')
    return identity

def authority_rows(database):
    with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True,timeout=5) as d:
        d.row_factory=sqlite3.Row;d.execute('PRAGMA query_only=ON');d.execute('BEGIN')
        return {table:[dict(r) for r in d.execute('SELECT * FROM '+table+' ORDER BY rowid')]
          for table in ('contexts','scoped_pilot_decisions','mcp_service_grants')}

def window(rows,c):
    contexts=[r for r in rows['contexts'] if r['binding_id']==c.BINDING and r['closed_at_ms'] is None]
    need(len(contexts)==1 and contexts[0]['context_id']==CONTEXT and contexts[0]['expires_at_ms']==EXPIRES,'UNCHANGED_EXACT_CONTEXT_REQUIRED')
    prior=[r for r in rows['scoped_pilot_decisions'] if r['decision_id']==PRIOR]
    need(len(prior)==1 and prior[0]['principal_id']==c.PRINCIPAL and prior[0]['binding_id']==c.BINDING and prior[0]['expires_at_ms']==EXPIRES,'EXACT_PRIOR_PILOT_REQUIRED')
    return prior[0]

def preserve(before,after,phase,c,new_id=None):
    need(before['contexts']==after['contexts'] and before['mcp_service_grants']==after['mcp_service_grants'],'CONTEXT_OR_GRANT_CHANGED')
    old={r['decision_id']:r for r in before['scoped_pilot_decisions']};new={r['decision_id']:r for r in after['scoped_pilot_decisions']}
    if phase=='close':
        need(old.keys()==new.keys(),'PILOT_HISTORY_COUNT_CHANGED')
        for key,row in old.items():
            if key==PRIOR:
                need(row['revoked_at_ms'] is None and type(new[key]['revoked_at_ms']) is int
                  and {k:v for k,v in row.items() if k!='revoked_at_ms'}=={k:v for k,v in new[key].items() if k!='revoked_at_ms'},'EXACT_PRIOR_REVOKE_REQUIRED')
            else:need(row==new[key],'UNRELATED_PILOT_CHANGED')
    elif phase=='replace':
        need(set(new)-set(old)=={new_id} and all(new.get(k)==v for k,v in old.items()),'PILOT_REPLACEMENT_HISTORY_CHANGED')
        row=new[new_id]
        need(row['principal_id']==c.PRINCIPAL and row['binding_id']==c.BINDING and row['expires_at_ms']==EXPIRES and row['revoked_at_ms'] is None
          and all(row.get(k)==TARGET[k] for k in ('device_id','endpoint_id','workspace_id','workspace_generation')),'REPLACEMENT_SCOPE_CHANGED')
    else:need(old==new,'PILOT_CHANGED_DURING_REOPEN')

def marker_read(c,packet,phase):
    if phase=='close':need(not MARKER.exists() and not MARKER.is_symlink(),'R14_MARKER_ALREADY_EXISTS_NO_REPLAY');return None
    raw=c.protected_file(MARKER)
    previous=unwrap(packet['server'])
    need(sha(raw)==previous['next_marker_sha256'],'OBSERVED_PREVIOUS_MARKER_CHANGED')
    value=json.loads(raw)
    need(value.get('approval_id')==packet['approval_id'] and value.get('context_id')==CONTEXT and value.get('expires_at_ms')==EXPIRES
      and value.get('requested_at_ms')==REQUESTED and value.get('prior_pilot_id')==PRIOR and all(value.get(k)==v for k,v in TARGET.items())
      and value.get('operation')==OPERATION and value.get('phase')==('intake_closed' if phase=='replace' else 'pilot_replaced'),
      'EXACT_PREVIOUS_PHASE_REQUIRED')
    return value

def node_echo(overview,native,c):
    rows=[r for r in overview['nodes'] if r['device_id']==c.DEVICE];need(len(rows)==1,'EXACT_NODE_NOT_UNIQUE');node=rows[0]
    need(0<=overview['observed_at_ms']-node['last_seen_at_ms']<60000 and node['readiness']=='ready' and node['policy_state']=='enabled'
      and all(node[k]==v for k,v in {'activation_epoch':native['activation_epoch_id'],'runtime_instance_id':native['mcp_process_instance_id'],
        'mcp_server_instance_id':native['mcp_server_instance_id'],'contract_version':'sha256:'+CONTRACT}.items()),'FRESH_R14_NODE_ECHO_REQUIRED')
    return node

def public(c,health,snapshot,overview,grant,marker,raw_marker,mutation):
    previous=next(r for r in overview['scoped_pilot_decisions'] if r['decision_id']==PRIOR)
    nodes=[r for r in overview['nodes'] if r['device_id']==c.DEVICE];need(len(nodes)==1,'EXACT_NODE_NOT_UNIQUE')
    return {'phase':'r14_same_window_read_only_observation','ok':True,'host':c.HOST,'service':c.SERVICE,
      'source_revision':c.REVISION,'service_instance_id':health['service_instance_id'],'binding_id':c.BINDING,
      'approval_id':marker['approval_id'],'principal_id':c.PRINCIPAL,
      'node':{k:nodes[0].get(k) for k in ('device_id','readiness','policy_state','policy_reason','policy_expires_at_ms',
        'last_seen_at_ms','activation_epoch','runtime_instance_id','mcp_server_instance_id','contract_version')},
      **{k:TARGET[k] for k in ('device_id','workspace_id','workspace_generation','root','profile')},
      'admission':overview['admission']['admission_mode'],'state':snapshot,'state_sha256':c.digest(snapshot),
      'observed_at_ms':overview['observed_at_ms'],'context_id':CONTEXT,'requested_at_ms':REQUESTED,'expires_at_ms':EXPIRES,
      'pilot_id':marker.get('pilot_id'),'prior_pilot_id':PRIOR,'prior_pilot_revoked':previous['revoked_at_ms'] is not None,
      'replacement_pilot_same_principal':marker.get('pilot_id') not in (None,PRIOR),
      'replacement_pilot_same_binding':marker.get('pilot_id') not in (None,PRIOR),'replacement_pilot_expires_at_ms':EXPIRES,
      'grant_expires_at_ms':grant['expires_at_ms'],'approved_window_covered':EXPIRES<=grant['expires_at_ms'],
      'capabilities':{'read':True,'write':True,'exec':True},'next_operation':OPERATION,'next_phase':marker['phase'],
      'next_marker_sha256':sha(raw_marker),'service_grant_sha256':c.digest(grant),'authority_extended':False,
      **{k:marker.get(k) for k in ('activation_epoch','runtime_instance_id','mcp_server_instance_id','contract_version')},
      'service_deployed_or_restarted':False,'remote_mutation':mutation,'replay_forbidden':True}

def main(packet):
    phase=packet.get('phase');stage='input';c=None
    try:
        if phase=='observe':
            need(packet.get('execute') is False,'READ_ONLY_OBSERVATION_REQUIRED')
            c=common();origin,auth,database,health,snapshot,overview,grant=c.inspect()
            need(health['service_instance_id']==SERVICE,'EXACT_SERVER_CHANGED')
            raw=c.protected_file(MARKER);marker=json.loads(raw);rows=authority_rows(database);prior=window(rows,c)
            need(marker.get('operation')==OPERATION and marker.get('context_id')==CONTEXT and marker.get('requested_at_ms')==REQUESTED
              and all(marker.get(k)==v for k,v in TARGET.items())
              and marker.get('expires_at_ms')==EXPIRES and now()<EXPIRES and prior['revoked_at_ms'] is not None,'EXACT_CURRENT_R14_MARKER_REQUIRED')
            active=[r for r in rows['scoped_pilot_decisions'] if r['revoked_at_ms'] is None]
            if marker['phase']=='intake_closed':need(not active and marker['pilot_id'] is None,'EXACT_CLOSED_PHASE_REQUIRED')
            else:need(marker['phase'] in ('pilot_replaced','intake_reopened') and len(active)==1 and active[0]['decision_id']==marker['pilot_id']
              and active[0]['principal_id']==c.PRINCIPAL and active[0]['binding_id']==c.BINDING and active[0]['expires_at_ms']==EXPIRES,'EXACT_REPLACED_PHASE_REQUIRED')
            need(overview['admission']['admission_mode']==('scoped_pilot' if marker['phase']=='intake_reopened' else 'recovery'),'MARKER_ADMISSION_CHANGED')
            print(json.dumps(public(c,health,snapshot,overview,grant,marker,raw,False),sort_keys=True,separators=(',',':')));return
        need(phase in ('close','replace','reopen') and packet.get('execute') is True,'EXPLICIT_R14_PHASE_REQUIRED')
        approval(packet['approval'],packet['approval_id']);native=windows(packet['windows'],phase)
        c=common();origin,auth,database,health,before_state,overview,grant=c.inspect()
        need(health['service_instance_id']==SERVICE and health['declared_source_revision']==c.REVISION
          and now()+720000<EXPIRES<=grant['expires_at_ms'],'UNCHANGED_SERVER_AND_WINDOW_REQUIRED')
        authority=unwrap(packet['authority']);r13=c.protected_file(R13_MARKER)
        need(sha(r13)==authority['next_marker_sha256'],'ORIGINAL_AUTHORITY_MARKER_CHANGED')
        original=json.loads(r13)
        need(original['context_id']==CONTEXT and original['pilot_id']==PRIOR and original['requested_at_ms']==REQUESTED and original['expires_at_ms']==EXPIRES,'ORIGINAL_AUTHORITY_WINDOW_CHANGED')
        before=authority_rows(database);prior=window(before,c);marker=marker_read(c,packet,phase)
        active=[r for r in before['scoped_pilot_decisions'] if r['revoked_at_ms'] is None]
        if phase=='close':
            need(overview['admission']['admission_mode']=='scoped_pilot' and len(active)==1 and active[0]['decision_id']==PRIOR,'EXACT_SINGLE_CURRENT_PILOT_REQUIRED')
            c.private_directory(DIRECTORY,create=True)
            marker={'operation':OPERATION,'phase':'close_prepared','approval_id':packet['approval_id'],'authority_approval_id':WINDOW_APPROVAL,
              'context_id':CONTEXT,'requested_at_ms':REQUESTED,'expires_at_ms':EXPIRES,'prior_pilot_id':PRIOR,'pilot_id':None,
              **TARGET,'principal_id':c.PRINCIPAL}
        else:
            need(overview['admission']['admission_mode']=='recovery' and prior['revoked_at_ms'] is not None,'RECOVERY_AND_REVOKED_PRIOR_REQUIRED')
            c.private_directory(DIRECTORY)
            if phase=='replace':need(not active,'UNRELATED_ACTIVE_PILOT_BEFORE_REPLACEMENT')
            else:need(len(active)==1 and active[0]['decision_id']==marker['pilot_id'],'EXACT_REPLACEMENT_PILOT_REQUIRED')
            node_echo(overview,native,c)
        descriptor=c.operation_lock()
        try:
            need(c.state(database)==before_state and authority_rows(database)==before,'STATE_CHANGED_BEFORE_PHASE')
            marker_read(c,packet,phase)
            windows(packet['windows'],phase);approval(packet['approval'],packet['approval_id'])
            exclusive(DIRECTORY/(phase+'-intent.json'),{'approval_id':packet['approval_id'],'phase':phase,
              'windows_sha256':packet['windows_sha256'],'authority_sha256':packet['authority_sha256'],
              'previous_marker_sha256':None if phase=='close' else unwrap(packet['server'])['next_marker_sha256'],
              'state_sha256':c.digest(before_state),'authority_rows_sha256':sha(canonical(before)),'no_replay':True})
            stage='supported_'+phase+'_api'
            if phase=='close':c.api(origin,auth,'/v1/maintenance/admission',{'mode':'recovery'});marker['phase']='intake_closed'
            elif phase=='replace':
                result=c.api(origin,auth,'/v1/scoped-pilot-decisions',{'principal_id':c.PRINCIPAL,'binding_id':c.BINDING,'expires_at_ms':EXPIRES,'reason':'Owner-approved r14 activation in unchanged authority window'})
                need(re.fullmatch(r'pilot_[a-f0-9]{32}',str(result.get('decision_id',''))),'REPLACEMENT_RESPONSE_UNCERTAIN_NO_REPLAY')
                marker.update(pilot_id=result['decision_id'],phase='pilot_replaced')
            else:c.api(origin,auth,'/v1/maintenance/admission',{'mode':'scoped_pilot'});marker['phase']='intake_reopened'
            stage='phase_preservation'
            after=authority_rows(database);preserve(before,after,phase,c,marker.get('pilot_id'));c.compare_history(before_state,c.state(database))
            fresh=c.api(origin,auth,'/v1/ui/overview');fresh_health=c.api(origin,auth,'/healthz')
            need(fresh_health['service_instance_id']==SERVICE and fresh['admission']['admission_mode']==('scoped_pilot' if phase=='reopen' else 'recovery'),'PHASE_ADMISSION_NOT_OBSERVED')
            if phase!='close':
                node=node_echo(fresh,native,c)
                marker.update(activation_epoch=node['activation_epoch'],runtime_instance_id=node['runtime_instance_id'],mcp_server_instance_id=node['mcp_server_instance_id'],contract_version=node['contract_version'])
            marker.update(service_instance_id=SERVICE,source_revision=c.REVISION,windows_receipt_sha256=packet['windows_sha256'],
              prior_pilot_revoked=True,replacement_pilot_same_principal=phase!='close',replacement_pilot_same_binding=phase!='close',replacement_pilot_expires_at_ms=EXPIRES)
            raw=canonical(marker);c.atomic_bytes(MARKER,raw)
            print(json.dumps(public(c,fresh_health,c.state(database),fresh,grant,marker,raw,True),sort_keys=True,separators=(',',':')))
        finally:os.close(descriptor)
    except Exception as error:
        value=str(error) if isinstance(error,(Failure,)) or (c is not None and isinstance(error,c.GuardFailure)) else ''
        code=value if re.fullmatch(r'[A-Z0-9_]{1,128}',value) else 'R14_PHASE_UNCERTAIN_READ_ONLY_INSPECT_NO_REPLAY'
        print(json.dumps({'phase':'r14_same_window_transition_failed','ok':False,'stage':stage,'operation':phase,'code':code,
          'remote_mutation_possible':True,'raw_error_disclosed':False,'replay_forbidden':True},sort_keys=True,separators=(',',':')))
        raise SystemExit(2) from None
