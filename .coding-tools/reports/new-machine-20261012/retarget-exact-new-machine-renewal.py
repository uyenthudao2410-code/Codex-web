"""Reviewed exact new-machine renewal configuration repair.

No execution without explicit authorization to extend the original bounded
pilot and retain existing automatic renewal. Uses the maintained renewal
oneshot, never reads/prints bearer values, and preserves all grant rows/scopes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import time

ENV_SHA='397deda57770c66ab40ef2bae19506118b99605549551c3f199859c7cc6c347d'
HELPER_SHA='06ce91b9697e5e3b2b32392142a17c16a3da2571286feec4e24e71feab23b2cb'
RENEWAL_UNIT_SHA='4d8fe28d652248df8f8db7d64a23b40b025e189f6de65c40ef49c23442e63e9c'
TIMER_UNIT_SHA='8e9574508e910a286d46ae54f9b3fc213dae26da068b06a845a1022930ba5a31'
PILOT='pilot_dfb3174078d842299c41c6638830e505'
OLD_CONFIGURED_PILOT='pilot_88e220659e1d43a6b1b2a301f8424f88'
BINDING='bind_71661b1046884174b01c99af5f8546aa'
DEVICE='4c4b7a5b-7744-49ae-a490-78a528a00471'
WORKSPACE='workspace_f93b5bac9dc74fae9cea66f44c4ebc94'
GENERATION='generation_a420c8bfcfcb4e42b5bb7fc5e5cec097'
PRINCIPAL='svcprn_cd98750c7c7e45678d201066dc1b7d7a'
GRANT='mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd'
EXPIRY=1791776571067
HISTORY={'act_048df93488874a70aa97a7ee18ccbd03','act_744496c6bd514d38a746cf8819aae9ad'}
HISTORY_SHA='724cb852c916eb91bb16e8631ef423ce2cdda0b3d0e8e58e1f1c69bdf7d83d2f'
STAGE='preflight'


def require(value,code):
    if not value: raise RuntimeError(code)


def sha(content):
    return hashlib.sha256(content).hexdigest()


def main():
    global STAGE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-activation-epoch',required=True)
    parser.add_argument('--confirm-20h-pilot-and-existing-automatic-renewal',action='store_true',required=True)
    args=parser.parse_args()
    os.umask(0o077)
    env_file=Path.home()/'.config/codex-control-plane/control-plane.env'
    require(not env_file.is_symlink() and env_file.is_file() and env_file.stat().st_uid==os.getuid()
            and env_file.stat().st_mode&0o777==0o600,'PROTECTED_ENV_NOT_OWNER_ONLY')
    original=env_file.read_bytes()
    require(sha(original)==ENV_SHA,'PROTECTED_ENV_DRIFT')
    pid=int(subprocess.check_output(['systemctl','--user','show','codex-control-plane.service','--property=MainPID','--value'],text=True).strip())
    require(pid>0,'SERVICE_NOT_RUNNING')
    serving=dict(item.split('=',1) for item in Path(f'/proc/{pid}/environ').read_text().split('\0') if '=' in item)
    package=next(Path(folder) for folder in serving['PYTHONPATH'].split(':') if (Path(folder)/'control_plane/store.py').is_file())
    helper=package.parent/'deploy/control-plane-authority-renewal.py'
    require(sha(helper.read_bytes())==HELPER_SHA,'MAINTAINED_RENEWAL_HELPER_DRIFT')
    timer='codex-control-plane-authority-renewal.timer';renewal='codex-control-plane-authority-renewal.service'

    def unit_snapshot(unit):
        fields=['Id','LoadState','UnitFileState','FragmentPath','DropInPaths']
        fields+=['ActiveState','Unit','Persistent','RandomizedDelayUSec'] if unit==timer else ['Type']
        output=subprocess.check_output(['systemctl','--user','show',unit,*['--property='+field for field in fields]],text=True)
        values=dict(line.split('=',1) for line in output.splitlines() if '=' in line)
        require(values.get('Id')==unit and values.get('LoadState')=='loaded' and values.get('DropInPaths')=='','RENEWAL_UNIT_IDENTITY_DRIFT')
        fragment=Path.home()/'.config/systemd/user'/unit
        require(values.get('FragmentPath')==str(fragment) and fragment.is_file(),'RENEWAL_UNIT_FRAGMENT_DRIFT')
        digest=sha(fragment.read_bytes())
        require(digest==(TIMER_UNIT_SHA if unit==timer else RENEWAL_UNIT_SHA),'RENEWAL_UNIT_CONFIG_DRIFT')
        values['fragment_sha256']=digest
        if unit==timer:
            require(values.get('ActiveState')=='active' and values.get('UnitFileState')=='enabled'
                    and values.get('Unit')==renewal and values.get('Persistent')=='yes'
                    and values.get('RandomizedDelayUSec')=='1min','EXISTING_RENEWAL_TIMER_DRIFT')
        else:
            require(values.get('Type')=='oneshot','RENEWAL_UNIT_TYPE_DRIFT')
            start=subprocess.check_output(['systemctl','--user','show',unit,'--property=ExecStart','--value'],text=True).strip()
            configured_helper=Path.home()/'.local/lib/codex-control-plane/current/deploy/control-plane-authority-renewal.py'
            require(start.count('path=')==1 and ('path=/usr/bin/python3 ; argv[]=/usr/bin/python3 -B '+str(configured_helper)+' ; ignore_errors=no ;') in start
                    and configured_helper.resolve()==helper.resolve() and sha(configured_helper.read_bytes())==HELPER_SHA,'RENEWAL_EXECSTART_NOT_PINNED_HELPER')
            environment_files=subprocess.check_output(['systemctl','--user','show',unit,'--property=EnvironmentFiles','--value'],text=True).strip()
            require(environment_files==str(env_file)+' (ignore_errors=no)','RENEWAL_ENVIRONMENT_FILE_NOT_EXACT')
            values['exec_start_helper_sha256']=HELPER_SHA
            values['environment_file']=str(env_file)
        return values

    before_timer=unit_snapshot(timer);before_renewal=unit_snapshot(renewal)
    fixed={'CONTROL_PLANE_AUTHORITY_RENEWAL_ENABLED':'true','CONTROL_PLANE_MCP_SERVICE_GRANT_ID':GRANT,
           'CONTROL_PLANE_AUTHORITY_GRANT_TTL_SECONDS':'2419200','CONTROL_PLANE_AUTHORITY_GRANT_WINDOW_SECONDS':'86400',
           'CONTROL_PLANE_AUTHORITY_PILOT_TTL_SECONDS':'72000','CONTROL_PLANE_AUTHORITY_PILOT_WINDOW_SECONDS':'7200'}
    text=original.decode()
    for key,value in fixed.items():
        require(re.findall('^'+re.escape(key)+'=(.*)$',text,re.MULTILINE)==[value],'RENEWAL_SETTING_DRIFT')
    key='CONTROL_PLANE_SCOPED_PILOT_DECISION_ID'
    require(re.findall('^'+key+'=(.*)$',text,re.MULTILINE)==[OLD_CONFIGURED_PILOT],'CONFIGURED_PILOT_CHANGED')
    pattern=re.compile('^'+key+'='+re.escape(OLD_CONFIGURED_PILOT)+'$',re.MULTILINE)
    changed,count=pattern.subn(key+'='+PILOT,text)
    require(count==1,'CONFIGURED_PILOT_REPLACEMENT_NOT_EXACT')
    replacement=changed.encode()
    require(replacement.replace((key+'='+PILOT).encode(),(key+'='+OLD_CONFIGURED_PILOT).encode(),1)==original,'OTHER_ENV_BYTES_CHANGED')
    db=Path(serving['CONTROL_PLANE_DB']);require(db.is_absolute(),'DATABASE_PATH_NOT_ABSOLUTE')
    con=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True);con.execute('PRAGMA query_only=ON');con.row_factory=sqlite3.Row

    def history():
        families=[]
        for action in sorted(HISTORY):
            family={'action_id':action}
            for table in ('actions','action_reconciliations','delivery_attempts','receipts'):
                family[table]=sorted([dict(row) for row in con.execute('SELECT * FROM '+table+' WHERE action_id=?',(action,))],key=lambda row:json.dumps(row,sort_keys=True))
            families.append(family)
        return sha(json.dumps(families,sort_keys=True,separators=(',',':')).encode())

    def grants():
        return [dict(row) for row in con.execute('SELECT * FROM mcp_service_grants ORDER BY grant_id')]

    def pilots():
        return [dict(row) for row in con.execute('SELECT * FROM scoped_pilot_decisions ORDER BY decision_id')]

    def check_target():
        now=int(time.time()*1000)
        target=con.execute('SELECT p.*,b.revoked_at_ms AS binding_revoked,nw.retired_at_ms,n.readiness,n.last_seen_at_ms,n.activation_epoch,n.policy_state,n.policy_expires_at_ms,n.revoked_at_ms AS node_revoked '
                           'FROM scoped_pilot_decisions p JOIN bindings b ON b.binding_id=p.binding_id JOIN node_workspaces nw ON nw.device_id=p.device_id AND nw.workspace_id=p.workspace_id AND nw.workspace_generation=p.workspace_generation JOIN nodes n ON n.device_id=p.device_id WHERE p.decision_id=?',(PILOT,)).fetchone()
        require(target is not None and target['owner_id']=='owner_default' and target['principal_id']==PRINCIPAL
                and target['device_id']==DEVICE and target['binding_id']==BINDING and target['workspace_id']==WORKSPACE
                and target['workspace_generation']==GENERATION and target['revoked_at_ms'] is None
                and target['binding_revoked'] is None and target['retired_at_ms'] is None and target['node_revoked'] is None,'RENEWAL_TARGET_NOT_EXACT_CURRENT')
        require(target['readiness']=='ready' and now-target['last_seen_at_ms']<90000 and target['activation_epoch']==args.expected_activation_epoch
                and target['policy_state']=='enabled' and target['policy_expires_at_ms']>now,'NEW_MACHINE_READY_NOT_CURRENT')
        require(con.execute("SELECT state_value FROM control_plane_state WHERE state_key='admission_mode'").fetchone()[0]=='scoped_pilot','ADMISSION_CHANGED')
        require(con.execute('SELECT COUNT(*) FROM scoped_pilot_decisions WHERE revoked_at_ms IS NULL AND expires_at_ms>?',(now,)).fetchone()[0]==1,'PILOT_COUNT_CHANGED')
        require(history()==HISTORY_SHA,'HISTORICAL_FAMILY_DRIFT')
        return dict(target)

    try:
        before=check_target();now=int(time.time()*1000)
        require(before['expires_at_ms']==EXPIRY and EXPIRY>now,'ORIGINAL_PILOT_EXPIRED_OR_CHANGED')
        before_grants=grants();before_pilots=pilots()
        grant=next((row for row in before_grants if row['grant_id']==GRANT),None)
        require(grant is not None and grant['principal_id']==PRINCIPAL and grant['revoked_at_ms'] is None
                and grant['expires_at_ms']>now+86400*1000 and set(json.loads(grant['scopes_json']))=={'control-plane.inventory','control-plane.read','control-plane.patch'},'PINNED_GRANT_NOT_CURRENT')
        require(subprocess.check_output(['systemctl','--user','show',renewal,'--property=MainPID','--value'],text=True).strip()=='0','RENEWAL_ONESHOT_ALREADY_RUNNING')
        require(unit_snapshot(timer)==before_timer and unit_snapshot(renewal)==before_renewal,'RENEWAL_UNIT_DRIFT_BEFORE_RETARGET')
        require(env_file.read_bytes()==original and grants()==before_grants and pilots()==before_pilots,'STATE_DRIFT_BEFORE_RETARGET')
        STAGE='protected_exact_config_retarget'
        stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());backup=env_file.with_name(env_file.name+'.pre-new-machine-renewal-'+stamp)
        require(not backup.exists(),'CONFIG_BACKUP_ALREADY_EXISTS');backup.write_bytes(original);backup.chmod(0o600)
        descriptor,raw=tempfile.mkstemp(prefix='.new-machine-renewal-',dir=env_file.parent)
        temporary=Path(raw)
        with os.fdopen(descriptor,'wb') as stream:
            os.fchmod(stream.fileno(),0o600);stream.write(replacement);stream.flush();os.fsync(stream.fileno())
        require(env_file.read_bytes()==original,'CONFIG_CHANGED_BEFORE_ATOMIC_REPLACE')
        os.replace(temporary,env_file)
        STAGE='official_existing_renewal_oneshot'
        require(unit_snapshot(timer)==before_timer and unit_snapshot(renewal)==before_renewal,'RENEWAL_UNIT_DRIFT_BEFORE_START')
        started=int(time.time()*1000)
        subprocess.run(['systemctl','--user','start',renewal],check=True,capture_output=True)
        ended=int(time.time()*1000)
        require(subprocess.check_output(['systemctl','--user','show',renewal,'--property=Result','--value'],text=True).strip()=='success'
                and subprocess.check_output(['systemctl','--user','show',renewal,'--property=ExecMainStatus','--value'],text=True).strip()=='0','OFFICIAL_RENEWAL_NOT_SUCCESSFUL')
        STAGE='postflight'
        after=check_target();after_pilots=pilots()
        require(after['expires_at_ms']>EXPIRY and started+72000*1000-1000<=after['expires_at_ms']<=ended+72000*1000
                and after['expires_at_ms']<=ended+86400*1000,'RENEWED_EXPIRY_OUTSIDE_20H_AUTHORIZATION')
        expected=[{**row,'expires_at_ms':after['expires_at_ms']} if row['decision_id']==PILOT else row for row in before_pilots]
        require(after_pilots==expected,'PILOT_TARGET_OR_OTHER_DECISION_CHANGED')
        require(grants()==before_grants and history()==HISTORY_SHA,'GRANTS_OR_HISTORY_CHANGED')
        require(env_file.read_bytes()==replacement and env_file.stat().st_mode&0o777==0o600,'PROTECTED_CONFIG_NOT_EXACT')
        require(unit_snapshot(timer)==before_timer and unit_snapshot(renewal)==before_renewal,'RENEWAL_UNIT_DRIFT_AFTER_START')
        require(int(subprocess.check_output(['systemctl','--user','show','codex-control-plane.service','--property=MainPID','--value'],text=True).strip())==pid,'MAIN_SERVICE_RESTARTED')
        con.close()
        print(json.dumps({'operation':'exact_new_machine_authority_renewal_retarget','ok':True,'pilot_decision_id':PILOT,'binding_id':BINDING,
                          'workspace_generation':GENERATION,'principal_id':PRINCIPAL,'grant_id':GRANT,'previous_expires_at_ms':EXPIRY,
                          'renewed_expires_at_ms':after['expires_at_ms'],'authorized_pilot_ttl_seconds':72000,'api_max_pilot_ttl_seconds':86400,
                          'automatic_timer_unchanged':True,'grants_all_rows_unchanged':True,'pilot_scope_unchanged':True,
                          'timer_preflight_postflight':before_timer,'renewal_unit_preflight_postflight':before_renewal,
                          'historical_family_sha256':HISTORY_SHA,'protected_config_backup_remote_path':str(backup),'main_service_pid_unchanged':pid,
                          'protected_config_sha256':sha(replacement),'completed_at_ms':ended},separators=(',',':')))
    finally:
        try: con.close()
        except Exception: pass


if __name__=='__main__':
    try: main()
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print(json.dumps({'operation':'exact_new_machine_authority_renewal_retarget','ok':False,'stage':STAGE,'error_code':code,
                          'operator_action':'Inspect exact configured pilot and official oneshot state before retry; no automatic expiry or authority rollback.'},separators=(',',':')))
        sys.exit(1)
