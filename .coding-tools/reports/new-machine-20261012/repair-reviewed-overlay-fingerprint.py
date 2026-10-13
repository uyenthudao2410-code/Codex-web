"""Repair only the package identity metadata of the approved runtime overlay.

The corrected immutable artifact contains exactly the same 38 release files.
Its manifest now agrees with the official runtime fingerprint helper. Protected
backups remain remote; pilot/grants/history stay unchanged. No blind restart.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tarfile
import time
import urllib.request

sys.dont_write_bytecode=True
SERVICE='codex-control-plane.service'
BASE_NAME='codex-control-plane-9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c'
PREVIOUS_NAME=BASE_NAME+'-retired-read-e5b3b8e2a63e'
NAME=PREVIOUS_NAME+'-fp2'
ARCHIVE_SHA='819c917e290029c1512b88bf85f60f875a1adc42e496a24490a8aee61ea4fd4e'
PACKAGE_SHA='sha256:f235d3a2898ad53597e3b48e55e27d2278ea7d6d0c9fb2fef21301467a5d9712'
WRONG_SHA='sha256:41c3bdb38a0b642f650d08d89382bc07b594d330289cf7fa82a624c17147a8a3'
HISTORY_SHA='724cb852c916eb91bb16e8631ef423ce2cdda0b3d0e8e58e1f1c69bdf7d83d2f'
HISTORY={'act_048df93488874a70aa97a7ee18ccbd03','act_744496c6bd514d38a746cf8819aae9ad'}
DEVICES=('4c4b7a5b-7744-49ae-a490-78a528a00471','72ceec2d-e3f2-472f-8e3c-99fffe053035')
STAGE='preflight'


def require(value,code):
    if not value: raise RuntimeError(code)


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def fingerprint(release):
    content=(release/'control-plane/control_plane/http_api.py').read_text()
    method=next(node for node in ast.walk(ast.parse(content)) if isinstance(node,ast.FunctionDef) and node.name=='_package_source_sha256')
    namespace={'hashlib':hashlib,'Path':Path}
    exec(ast.get_source_segment(content,method),namespace)
    return namespace['_package_source_sha256'](release/'control-plane/control_plane')


def snapshot(con):
    for device in DEVICES:
        require(con.execute('SELECT COUNT(*) FROM mcp_task_sessions WHERE device_id=? AND closed_at_ms IS NULL',(device,)).fetchone()[0]==0,'OPEN_TASK')
        require(con.execute('SELECT COUNT(*) FROM mcp_task_writer_leases l JOIN mcp_task_sessions t ON t.task_id=l.task_id WHERE t.device_id=? AND l.released_at_ms IS NULL',(device,)).fetchone()[0]==0,'UNRELEASED_WRITER')
        rows=con.execute('SELECT a.action_id,a.tool_name,a.expires_at_ms,a.delivery_state,r.disposition FROM actions a LEFT JOIN action_reconciliations r ON r.action_id=a.action_id WHERE a.device_id=? AND a.settled_at_ms IS NULL',(device,)).fetchall()
        require({row['action_id'] for row in rows}==(HISTORY if device==DEVICES[0] else set()),'UNSETTLED_ACTION_SET_CHANGED')
        require(all(row['tool_name']=='workspace_context' and row['expires_at_ms']<int(time.time()*1000) and row['delivery_state']=='reconcile_required' and row['disposition']=='quarantined_unknown' for row in rows),'UNSETTLED_NOT_HISTORICAL_QUARANTINE')
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
    active=[row for row in pilots if row['revoked_at_ms'] is None]
    require(admission=='scoped_pilot' and len(active)==1 and active[0]['decision_id']=='pilot_7177a7cd197c4944ae77ebc1c4d433a3' and active[0]['expires_at_ms']==1791776571067,'OLD_PILOT_CHANGED')
    return {'admission':admission,'pilots':pilots,'grants':grants}


def main():
    global STAGE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--confirm-fingerprint-repair-and-restart',action='store_true',required=True)
    parser.parse_args()
    os.umask(0o077)
    base=Path.home()/'.local/lib/codex-control-plane';releases=base/'releases'
    current=base/'current';previous=releases/PREVIOUS_NAME;candidate=releases/NAME
    archive=releases/(NAME+'.tar.gz')
    require(current.is_symlink() and current.resolve()==previous.resolve(),'CURRENT_OVERLAY_CHANGED')
    require(hashlib.sha256(archive.read_bytes()).hexdigest()==ARCHIVE_SHA,'CORRECTED_ARCHIVE_SHA_MISMATCH')
    require(fingerprint(previous)==PACKAGE_SHA,'APPROVED_RUNTIME_SOURCE_DRIFT')
    env_file=Path.home()/'.config/codex-control-plane/control-plane.env'
    drop_in=Path.home()/'.config/systemd/user/codex-control-plane.service.d/10-immutable-release.conf'
    text=env_file.read_text()
    def configured(key):
        values=re.findall('^'+re.escape(key)+'=(.*)$',text,re.MULTILINE)
        require(len(values)==1,'PROTECTED_CONFIG_KEY_AMBIGUOUS')
        return values[0].strip().strip('"').strip("'")
    require(configured('CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256')==WRONG_SHA,'EXPECTED_FAILURE_CONFIG_CHANGED')
    db=Path(configured('CONTROL_PLANE_DB'));backup_dir=Path(configured('CONTROL_PLANE_BACKUP_DIR'))
    require(db.is_absolute() and backup_dir.is_absolute() and backup_dir.is_dir(),'PROTECTED_PATH_NOT_ABSOLUTE')
    con=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True);con.execute('PRAGMA query_only=ON');con.row_factory=sqlite3.Row
    before=snapshot(con)
    require(con.execute('PRAGMA user_version').fetchone()[0]==29,'SCHEMA_CHANGED')
    STAGE='extract_corrected_immutable_candidate'
    require(not candidate.exists(),'CORRECTED_CANDIDATE_ALREADY_EXISTS')
    with tarfile.open(archive,'r:gz') as bundle:
        for member in bundle.getmembers():
            path=Path(member.name)
            require(not path.is_absolute() and '..' not in path.parts and path.parts[0]==NAME and (member.isdir() or member.isfile()),'UNSAFE_ARCHIVE_MEMBER')
        bundle.extractall(releases)
    verification=module('corrected_official_verifier',candidate/'deploy/control-plane-verify-release.py').verify_release(candidate)
    require(verification['package_source_sha256']==PACKAGE_SHA and fingerprint(candidate)==PACKAGE_SHA,'ACTUAL_MANIFEST_PACKAGE_MISMATCH')
    previous_manifest=json.loads((previous/'release-manifest.json').read_text());candidate_manifest=json.loads((candidate/'release-manifest.json').read_text())
    require(previous_manifest['files']==candidate_manifest['files'] and len(candidate_manifest['files'])==38,'REPAIR_RUNTIME_BYTES_CHANGED')
    require(candidate_manifest['control_plane_schema_version']==29,'REPAIR_SCHEMA_CHANGED')
    STAGE='protected_remote_backup'
    sys.path.insert(0,str(previous/'control-plane'))
    from control_plane.store import create_verified_backup
    stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())
    db_backup=backup_dir/('pre-fingerprint-repair-'+stamp+'.sqlite3')
    backup=create_verified_backup(db,db_backup);db_backup.chmod(0o600)
    for source in (env_file,drop_in):
        saved=source.with_name(source.name+'.pre-fingerprint-repair-'+stamp)
        require(not saved.exists(),'PROTECTED_BACKUP_ALREADY_EXISTS')
        saved.write_bytes(source.read_bytes());saved.chmod(0o600)
    require(snapshot(con)==before,'AUTHORITY_DRIFT_BEFORE_REPAIR')
    STAGE='official_metadata_repair'
    helper=module('corrected_official_activation',candidate/'deploy/prepare-control-plane-activation.py')
    config=helper.prepare_activation_config(release_dir=candidate,env_file=env_file,drop_in=drop_in)
    check=helper.prepare_activation_config(release_dir=candidate,env_file=env_file,drop_in=drop_in,check_only=True)
    require(check['environment_matches'] and check['drop_in_matches'] and fingerprint(candidate)==check['package_source_sha256']==PACKAGE_SHA,'ACTUAL_MANIFEST_EXPECTED_PACKAGE_MISMATCH')
    STAGE='atomic_switch_and_official_restart'
    temporary=base/('.current-fingerprint-repair-'+stamp);require(not temporary.exists(),'SWITCH_TEMPORARY_EXISTS')
    temporary.symlink_to(candidate);os.replace(temporary,current)
    subprocess.run(['systemctl','--user','daemon-reload'],check=True,capture_output=True)
    subprocess.run(['systemctl','--user','restart',SERVICE],check=True,capture_output=True)
    STAGE='postflight'
    health=None;deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        try:
            with urllib.request.urlopen('https://svhome.tail0e4032.ts.net/healthz',timeout=3) as response: observed=json.loads(response.read(65536))
            if observed.get('package_source_sha256')==PACKAGE_SHA and observed.get('expected_package_source_sha256')==PACKAGE_SHA:
                health=observed;break
        except Exception: pass
        time.sleep(0.5)
    require(health is not None,'CORRECTED_RESTART_HEALTH_NOT_PROVEN')
    pid=int(subprocess.check_output(['systemctl','--user','show',SERVICE,'--property=MainPID','--value'],text=True).strip())
    require(pid>0,'CORRECTED_SERVICE_PID_UNAVAILABLE')
    running=dict(item.split('=',1) for item in Path(f'/proc/{pid}/environ').read_text().split('\0') if '=' in item)
    require(running.get('PYTHONPATH')==str(candidate/'control-plane') and running.get('CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256')==PACKAGE_SHA,'CORRECTED_RUNNING_SOURCE_UNPROVEN')
    require(snapshot(con)==before,'AUTHORITY_CHANGED_DURING_REPAIR')
    require(con.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and con.execute('PRAGMA user_version').fetchone()[0]==29,'SQLITE_INTEGRITY_FAILED')
    con.close()
    print(json.dumps({'operation':'approved_overlay_fingerprint_repair','ok':True,'service_pid':pid,'release_name':NAME,'archive_sha256':ARCHIVE_SHA,
                      'package_source_sha256':PACKAGE_SHA,'actual_manifest_expected_agree':True,'runtime_files_unchanged_from_reviewed_overlay':38,
                      'official_release_verification':verification,'activation_config':config,'backup_remote_path':str(db_backup),'backup':backup,
                      'schema_version':29,'sqlite_integrity':'ok','historical_family_sha256':HISTORY_SHA,'old_pilot_all_grants_unchanged':True,
                      'pilot_transfer_performed':False,'completed_at_ms':int(time.time()*1000)},separators=(',',':')))


if __name__=='__main__':
    try: main()
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print(json.dumps({'operation':'approved_overlay_fingerprint_repair','ok':False,'stage':STAGE,'error_code':code},separators=(',',':')))
        sys.exit(1)
