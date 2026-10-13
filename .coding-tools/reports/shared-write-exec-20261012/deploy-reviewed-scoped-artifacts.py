"""Guarded svhome deployment of the reviewed one-file scoped artifact/document overlay.

Run remotely via SSH stdin after artifact upload and explicit review. Uses the
official release verifier, activation-config helper, SQLite Backup API and
systemctl service restart. Keeps DB/env backups protected on svhome only. Pilot,
grant, task, action, receipt and reconciliation authority is never mutated here.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tarfile
import time
import urllib.request

sys.dont_write_bytecode = True
SERVICE = "codex-control-plane.service"
BASE_NAME = 'codex-control-plane-9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c-retired-read-e5b3b8e2a63e-fp2'
NAME = 'codex-control-plane-9cae1044-scoped-artifacts-94b96e1b0fe2'
ARCHIVE_SHA = "daf92ba88eaa01cc0be209077bc827ef0e91e81c306fcf514c981896e3bff206"
PACKAGE_SHA = "sha256:5370e6ce030e72514b664b771f400437d337e7c5eb1c39b1ac90748662c3ceb0"
BASE_PACKAGE_SHA = "sha256:f235d3a2898ad53597e3b48e55e27d2278ea7d6d0c9fb2fef21301467a5d9712"
BASE_STORE_SHA = "e5b3b8e2a63e2e4144f9f782b275b4ecc056e8c1f642c91cc9647cb6b6d6667c"
HISTORY_SHA = "724cb852c916eb91bb16e8631ef423ce2cdda0b3d0e8e58e1f1c69bdf7d83d2f"
HISTORY = {"act_048df93488874a70aa97a7ee18ccbd03","act_744496c6bd514d38a746cf8819aae9ad"}
DEVICES = ("4c4b7a5b-7744-49ae-a490-78a528a00471","72ceec2d-e3f2-472f-8e3c-99fffe053035")
STAGE = "preflight"


def require(value, code):
    if not value:
        raise RuntimeError(code)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def identity():
    pid=int(subprocess.check_output(["systemctl","--user","show",SERVICE,"--property=MainPID","--value"],text=True).strip())
    require(pid>0,"SERVICE_PID_UNAVAILABLE")
    env=dict(item.split("=",1) for item in Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in item)
    return pid,env


def snapshot(con):
    for device in DEVICES:
        require(con.execute("SELECT COUNT(*) FROM mcp_task_sessions WHERE device_id=? AND closed_at_ms IS NULL",(device,)).fetchone()[0]==0,"OPEN_TASK")
        require(con.execute("SELECT COUNT(*) FROM mcp_task_writer_leases l JOIN mcp_task_sessions t ON t.task_id=l.task_id WHERE t.device_id=? AND l.released_at_ms IS NULL",(device,)).fetchone()[0]==0,"UNRELEASED_WRITER")
        rows=con.execute("SELECT a.action_id,a.tool_name,a.expires_at_ms,a.delivery_state,r.disposition FROM actions a LEFT JOIN action_reconciliations r ON r.action_id=a.action_id WHERE a.device_id=? AND a.settled_at_ms IS NULL",(device,)).fetchall()
        require({row['action_id'] for row in rows}==(HISTORY if device==DEVICES[0] else set()),"UNSETTLED_ACTION_SET_CHANGED")
        require(all(row['tool_name']=='workspace_context' and row['expires_at_ms']<int(time.time()*1000) and row['delivery_state']=='reconcile_required' and row['disposition']=='quarantined_unknown' for row in rows),"UNSETTLED_NOT_HISTORICAL_QUARANTINE")
    families=[]
    for action in sorted(HISTORY):
        family={'action_id':action}
        for table in ('actions','action_reconciliations','delivery_attempts','receipts'):
            family[table]=sorted([dict(row) for row in con.execute('SELECT * FROM '+table+' WHERE action_id=?',(action,))],key=lambda row:json.dumps(row,sort_keys=True))
        families.append(family)
    require(hashlib.sha256(json.dumps(families,sort_keys=True,separators=(',',':')).encode()).hexdigest()==HISTORY_SHA,'HISTORICAL_FAMILY_DRIFT')
    admission=con.execute("SELECT state_value FROM control_plane_state WHERE state_key='admission_mode'").fetchone()[0]
    pilots=[dict(row) for row in con.execute('SELECT * FROM scoped_pilot_decisions ORDER BY decision_id')]
    grants=[dict(row) for row in con.execute('SELECT * FROM mcp_service_grants ORDER BY grant_id')]
    require(admission=='scoped_pilot','ADMISSION_MODE_CHANGED')
    active=[row for row in pilots if row['revoked_at_ms'] is None]
    require(len(active)==1 and active[0]['decision_id']=='pilot_dfb3174078d842299c41c6638830e505' and active[0]['binding_id']=='bind_71661b1046884174b01c99af5f8546aa' and active[0]['device_id']==DEVICES[0] and active[0]['workspace_generation']=='generation_a420c8bfcfcb4e42b5bb7fc5e5cec097' and active[0]['principal_id']=='svcprn_cd98750c7c7e45678d201066dc1b7d7a' and active[0]['expires_at_ms']>int(time.time()*1000)+900000,'NEW_PILOT_SCOPE_OR_EXPIRY_CHANGED')
    return {'admission':admission,'pilots':pilots,'grants':grants}


def resume_unchanged_baseline_after_preswitch_failure():
    """Resume only the exact untouched serving release so new work can reconcile."""
    base=Path.home()/'.local/lib/codex-control-plane'
    config=Path.home()/'.config/codex-control-plane/control-plane.env'
    drop=Path.home()/'.config/systemd/user/codex-control-plane.service.d/10-immutable-release.conf'
    require((base/'current').is_symlink() and (base/'current').resolve()==(base/'releases'/BASE_NAME).resolve(),'BASELINE_CHANGED_NO_AUTOMATIC_START')
    require(sha(config)=='3b1d3c8015e7b494f2c0289be270888fd2da2beb64c344e84a7f9fca8858df1e' and sha(drop)=='5aacc340840f94b39956abf243b19e264211e618d53556fdd5cf83c775f12702','BASELINE_CONFIG_CHANGED_NO_AUTOMATIC_START')
    require(sha(base/'current/control-plane/control_plane/store.py')==BASE_STORE_SHA,'BASELINE_SOURCE_CHANGED_NO_AUTOMATIC_START')
    require(int(subprocess.check_output(['systemctl','--user','show',SERVICE,'--property=MainPID','--value'],text=True).strip())==0,'BASELINE_SERVICE_ALREADY_CHANGED_NO_AUTOMATIC_START')
    subprocess.run(['systemctl','--user','start',SERVICE],check=True,capture_output=True)
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        try:
            with urllib.request.urlopen('https://svhome.tail0e4032.ts.net/healthz',timeout=3) as response:
                health=json.loads(response.read(65536))
            if health.get('ok') is True and health.get('package_source_sha256')==BASE_PACKAGE_SHA and health.get('expected_package_source_sha256')==BASE_PACKAGE_SHA:
                return {'unchanged_baseline_resumed':True,'baseline_package_source_sha256':BASE_PACKAGE_SHA,'resumed_service_pid':identity()[0]}
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError('UNCHANGED_BASELINE_HEALTH_NOT_PROVEN')


def main():
    global STAGE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--confirm-deploy-and-restart',action='store_true',required=True)
    args=parser.parse_args()
    os.umask(0o077)
    base=Path.home()/'.local/lib/codex-control-plane'
    releases=base/'releases'
    archive=releases/(NAME+'.tar.gz')
    current=base/'current'
    candidate=releases/NAME
    previous=releases/BASE_NAME
    require(current.is_symlink() and current.resolve()==previous.resolve(),'CURRENT_RELEASE_CHANGED')
    require(sha(archive)==ARCHIVE_SHA,'APPROVED_ARCHIVE_SHA_MISMATCH')
    pid,env=identity()
    require(pid==912047,"REVIEWED_BASE_SERVICE_PID_CHANGED")
    require(env.get('CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256')==BASE_PACKAGE_SHA,'RUNNING_BASE_FINGERPRINT_CHANGED')
    require(sha(previous/'control-plane/control_plane/store.py')==BASE_STORE_SHA,'BASE_STORE_DRIFT')
    db=Path(env['CONTROL_PLANE_DB'])
    require(db.is_absolute(),'DATABASE_PATH_NOT_ABSOLUTE')
    con=sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True)
    con.execute('PRAGMA query_only=ON')
    con.row_factory=sqlite3.Row
    before=snapshot(con)
    require(con.execute('PRAGMA user_version').fetchone()[0]==29,'SCHEMA_CHANGED')
    STAGE='extract_immutable_candidate'
    require(not candidate.exists(),'CANDIDATE_ALREADY_EXISTS')
    with tarfile.open(archive,'r:gz') as bundle:
        members=bundle.getmembers()
        for member in members:
            path=Path(member.name)
            require(not path.is_absolute() and '..' not in path.parts and path.parts[0]==NAME and (member.isdir() or member.isfile()),'UNSAFE_ARCHIVE_MEMBER')
        bundle.extractall(releases, members=members)
    verification=module('reviewed_release_verifier',candidate/'deploy/control-plane-verify-release.py').verify_release(candidate)
    require(verification['package_source_sha256']==PACKAGE_SHA and verification['control_plane_schema_version']==29,'CANDIDATE_MANIFEST_IDENTITY_MISMATCH')
    old_manifest=json.loads((previous/'release-manifest.json').read_text())
    new_manifest=json.loads((candidate/'release-manifest.json').read_text())
    changed=[item['path'] for old,item in zip(old_manifest['files'],new_manifest['files']) if old!=item]
    require(len(old_manifest['files'])==len(new_manifest['files'])==38 and changed==['control-plane/control_plane/store.py'],'UNEXPECTED_RUNTIME_DELTA')
    # Recovery mode revokes the pilot. Stop the sole request-serving service
    # instead, then prove quiescence again with intake closed. If a competing
    # request won before stop, abort here and leave the service stopped.
    STAGE='close_service_intake_and_recheck'
    require(identity()[0]==pid and current.resolve()==previous.resolve(),'SERVICE_CHANGED_BEFORE_STOP')
    subprocess.run(['systemctl','--user','stop',SERVICE],check=True,capture_output=True)
    require(int(subprocess.check_output(['systemctl','--user','show',SERVICE,'--property=MainPID','--value'],text=True).strip())==0,'SERVICE_INTAKE_NOT_CLOSED')
    require(snapshot(con)==before,'AUTHORITY_DRIFT_BEFORE_CLOSED_INTAKE')
    STAGE='consistent_remote_backup'
    for path in env.get('PYTHONPATH','').split(':'):
        if path: sys.path.insert(0,path)
    from control_plane.store import create_verified_backup
    stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())
    backup_dir=Path(env['CONTROL_PLANE_BACKUP_DIR']).resolve()
    require(backup_dir.is_absolute() and backup_dir.is_dir(),'PROTECTED_BACKUP_DIRECTORY_UNAVAILABLE')
    database_backup=backup_dir/('pre-scoped-artifacts-'+stamp+'.sqlite3')
    backup=create_verified_backup(db,database_backup)
    os.chmod(database_backup,0o600)
    env_file=Path.home()/'.config/codex-control-plane/control-plane.env'
    drop_in=Path.home()/'.config/systemd/user/codex-control-plane.service.d/10-immutable-release.conf'
    original_env=env_file.read_bytes()
    original_drop=drop_in.read_bytes()
    require(sha(env_file)=='3b1d3c8015e7b494f2c0289be270888fd2da2beb64c344e84a7f9fca8858df1e' and sha(drop_in)=='5aacc340840f94b39956abf243b19e264211e618d53556fdd5cf83c775f12702','PROTECTED_CONFIG_DRIFT')
    for source,content in ((env_file,original_env),(drop_in,original_drop)):
        saved=source.with_name(source.name+'.pre-scoped-artifacts-'+stamp)
        require(not saved.exists(),'PROTECTED_CONFIG_BACKUP_EXISTS')
        saved.write_bytes(content)
        saved.chmod(0o600)
    require(snapshot(con)==before,'AUTHORITY_DRIFT_BEFORE_SWITCH')
    require(int(subprocess.check_output(['systemctl','--user','show',SERVICE,'--property=MainPID','--value'],text=True).strip())==0 and current.resolve()==previous.resolve(),'CLOSED_INTAKE_CHANGED_BEFORE_SWITCH')
    STAGE='official_activation_config'
    activation=module('reviewed_activation_helper',candidate/'deploy/prepare-control-plane-activation.py')
    config_receipt=activation.prepare_activation_config(release_dir=candidate,env_file=env_file,drop_in=drop_in)
    STAGE='atomic_release_switch_and_start'
    temporary=base/('.current-scoped-artifacts-'+stamp)
    require(not temporary.exists(),'SWITCH_TEMPORARY_EXISTS')
    temporary.symlink_to(candidate)
    os.replace(temporary,current)
    subprocess.run(['systemctl','--user','daemon-reload'],check=True,capture_output=True)
    subprocess.run(['systemctl','--user','start',SERVICE],check=True,capture_output=True)
    STAGE='postflight'
    health=None
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        try:
            with urllib.request.urlopen('https://svhome.tail0e4032.ts.net/healthz',timeout=3) as response:
                observed=json.loads(response.read(65536))
            if observed.get('package_source_sha256')==PACKAGE_SHA:
                health=observed
                break
        except Exception:
            pass
        time.sleep(0.5)
    require(health is not None and health.get('expected_package_source_sha256')==PACKAGE_SHA,'RESTART_HEALTH_FINGERPRINT_NOT_PROVEN')
    new_pid,new_env=identity()
    require(new_pid!=pid and new_env.get('CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256')==PACKAGE_SHA,'NEW_SERVICE_IDENTITY_NOT_PROVEN')
    require(current.resolve()==candidate.resolve(),'CURRENT_CANDIDATE_MISMATCH')
    require(new_env.get('PYTHONPATH')==str(candidate/'control-plane'),'RUNNING_RELEASE_PATH_MISMATCH')
    require(con.execute('PRAGMA user_version').fetchone()[0]==29 and con.execute('PRAGMA integrity_check').fetchone()[0]=='ok','POSTFLIGHT_SQLITE_INTEGRITY_FAILED')
    require(snapshot(con)==before,'AUTHORITY_CHANGED_DURING_DEPLOYMENT')
    receipt={'operation':'reviewed_scoped_artifact_document_deployment','ok':True,'old_service_pid':pid,'new_service_pid':new_pid,
             'release_name':NAME,'archive_sha256':ARCHIVE_SHA,'package_source_sha256':PACKAGE_SHA,
             'schema_version':29,'changed_runtime_files':changed,'unchanged_release_files':37,
             'release_verification':verification,'activation_config':config_receipt,
             'backup_remote_path':str(database_backup),'backup':backup,'sqlite_integrity':'ok',
             'historical_family_sha256':HISTORY_SHA,'pilot_and_all_grants_unchanged':True,
             'admission_mode':'scoped_pilot','pilot_transfer_performed':False,'completed_at_ms':int(time.time()*1000)}
    receipt['intake_closed_by_supported_service_stop']=True
    con.close()
    print(json.dumps(receipt,separators=(',',':')))


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        recovery={}
        if STAGE in {'close_service_intake_and_recheck','consistent_remote_backup'}:
            try:
                recovery=resume_unchanged_baseline_after_preswitch_failure()
            except Exception as resume_error:
                recovery={'baseline_resume_error':str(resume_error) if isinstance(resume_error,RuntimeError) else type(resume_error).__name__}
        print(json.dumps({'operation':'reviewed_scoped_artifact_document_deployment','ok':False,'stage':STAGE,'error_code':code,
                          **recovery,
                          'operator_action':'Inspect current symlink, protected config, service and health before recovery; no automatic authority rollback.'},separators=(',',':')))
        sys.exit(1)
