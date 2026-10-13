"""Guarded immutable svhome folder overlay rollout. Default is read-only preflight.

Root controller alone runs --confirm-deploy-and-restart after artifact review.
Backups containing credentials remain protected on svhome; authority is not edited.
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
SERVICE = 'codex-control-plane.service'
STAGE = 'preflight'
DEVICE = '4c4b7a5b-7744-49ae-a490-78a528a00471'
HISTORY = {'act_048df93488874a70aa97a7ee18ccbd03', 'act_744496c6bd514d38a746cf8819aae9ad'}


def require(value, code):
    if not value:
        raise RuntimeError(code)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity():
    pid = int(subprocess.check_output(['systemctl', '--user', 'show', SERVICE, '-p', 'MainPID', '--value'], text=True).strip())
    require(pid > 0, 'SERVICE_PID_UNAVAILABLE')
    env = dict(item.split('=', 1) for item in Path(f'/proc/{pid}/environ').read_text().split('\0') if '=' in item)
    return pid, env


def authority_snapshot(connection):
    now = int(time.time() * 1000)
    require(connection.execute('PRAGMA user_version').fetchone()[0] == 29, 'SCHEMA_CHANGED')
    require(connection.execute("SELECT state_value FROM control_plane_state WHERE state_key='admission_mode'").fetchone()[0] == 'scoped_pilot', 'ADMISSION_CHANGED')
    require(connection.execute('SELECT COUNT(*) FROM mcp_task_sessions WHERE device_id=? AND closed_at_ms IS NULL AND expires_at_ms>?', (DEVICE, now)).fetchone()[0] == 0, 'LIVE_TASK')
    require(connection.execute('SELECT COUNT(*) FROM mcp_task_writer_leases l JOIN bindings b ON b.binding_id=l.binding_id WHERE b.device_id=? AND l.released_at_ms IS NULL AND l.expires_at_ms>?', (DEVICE, now)).fetchone()[0] == 0, 'LIVE_WRITER')
    unresolved = connection.execute('SELECT a.action_id,a.delivery_state,a.expires_at_ms,a.tool_name,r.disposition FROM actions a LEFT JOIN action_reconciliations r ON r.action_id=a.action_id WHERE a.device_id=? AND a.settled_at_ms IS NULL', (DEVICE,)).fetchall()
    require({row['action_id'] for row in unresolved} == HISTORY, 'UNSETTLED_ACTION_SET_CHANGED')
    require(all(row['delivery_state'] == 'reconcile_required' and row['tool_name'] == 'workspace_context' and row['expires_at_ms'] < now and row['disposition'] == 'quarantined_unknown' for row in unresolved), 'UNSETTLED_ACTION_NOT_AUDITED_HISTORY')
    digest = hashlib.sha256()
    counts = {}
    for table in ('control_plane_state', 'bindings', 'scoped_pilot_decisions', 'mcp_service_grants'):
        rows = [dict(row) for row in connection.execute('SELECT * FROM ' + table)]
        rows.sort(key=lambda row: json.dumps(row, sort_keys=True))
        counts[table] = len(rows)
        digest.update(table.encode() + b'\0' + json.dumps(rows, sort_keys=True, separators=(',', ':')).encode() + b'\0')
    for table in ('actions', 'action_reconciliations', 'delivery_attempts', 'receipts'):
        rows = [dict(row) for row in connection.execute('SELECT * FROM ' + table + ' WHERE action_id IN (?,?)', tuple(sorted(HISTORY)))]
        rows.sort(key=lambda row: json.dumps(row, sort_keys=True))
        digest.update(table.encode() + b'\0' + json.dumps(rows, sort_keys=True, separators=(',', ':')).encode() + b'\0')
    return {'authority_and_history_sha256': digest.hexdigest(), 'table_counts': counts, 'historical_unknown_count': len(unresolved)}


def main():
    global STAGE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', required=True)
    parser.add_argument('--confirm-deploy-and-restart', action='store_true')
    args = parser.parse_args()
    approved = json.loads(Path(args.receipt).read_text())
    name = approved['verification']['release_name']
    require(name.startswith('codex-control-plane-local-folder-activation-1012-r9-') and '/' not in name, 'RELEASE_NAME_INVALID')
    base = Path.home() / '.local/lib/codex-control-plane'
    releases, current = base / 'releases', base / 'current'
    previous = Path(approved['baseline_release_root'])
    candidate, archive = releases / name, releases / (name + '.tar.gz')
    require(current.is_symlink() and current.resolve() == previous.resolve(), 'CURRENT_RELEASE_CHANGED')
    require(sha(previous / 'release-manifest.json') == approved['baseline_manifest_sha256'], 'BASELINE_MANIFEST_CHANGED')
    pid, env = identity()
    require(pid == approved['baseline_service_pid'], 'BASELINE_PID_CHANGED')
    require(env.get('PYTHONPATH') == str(previous / 'control-plane'), 'SERVING_ROOT_CHANGED')
    require(env.get('CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256') == approved['baseline_package_source_sha256'], 'SERVING_FINGERPRINT_CHANGED')
    require(sha(archive) == approved['candidate_archive_sha256'], 'APPROVED_ARCHIVE_HASH_MISMATCH')
    for item in approved['protected_config_hashes'].values():
        require(sha(Path(item['path'])) == item['sha256'], 'PROTECTED_CONFIG_CHANGED')
    verification = load('serving_release_verifier', previous / 'deploy/control-plane-verify-release.py').verify_release(previous)
    require(verification['package_source_sha256'] == approved['baseline_package_source_sha256'], 'BASELINE_INTEGRITY_FAILED')
    db = Path(env['CONTROL_PLANE_DB']).resolve()
    connection = sqlite3.connect(db.as_uri() + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA query_only=ON')
    before = authority_snapshot(connection)
    with tarfile.open(archive, 'r:gz') as bundle:
        for member in bundle.getmembers():
            path = Path(member.name)
            require(not path.is_absolute() and '..' not in path.parts and path.parts[0] == name and (member.isdir() or member.isfile()), 'UNSAFE_ARCHIVE_MEMBER')
        manifest_member = bundle.extractfile(name + '/release-manifest.json').read()
        require(hashlib.sha256(manifest_member).hexdigest() == approved['candidate_manifest_sha256'], 'ARCHIVE_MANIFEST_HASH_MISMATCH')
    if not args.confirm_deploy_and_restart:
        print(json.dumps({'operation': 'folder_overlay_readonly_preflight', 'passed': True,
            'service_pid': pid, 'release_name': name, 'authority': before,
            'remote_mutations': False}, separators=(',', ':')))
        return
    os.umask(0o077)
    STAGE = 'extract_verified_candidate'
    require(not candidate.exists(), 'CANDIDATE_ALREADY_EXISTS')
    with tarfile.open(archive, 'r:gz') as bundle:
        bundle.extractall(releases)
    verified = load('candidate_release_verifier', candidate / 'deploy/control-plane-verify-release.py').verify_release(candidate)
    require(verified == approved['verification'], 'CANDIDATE_IDENTITY_MISMATCH')
    old_manifest = json.loads((previous / 'release-manifest.json').read_text())
    new_manifest = json.loads((candidate / 'release-manifest.json').read_text())
    require([item['path'] for item in old_manifest['files']] == [item['path'] for item in new_manifest['files']], 'FILE_SET_CHANGED')
    changed = [item['path'] for old, item in zip(old_manifest['files'], new_manifest['files']) if old != item]
    require(changed == approved['changed_runtime_files'], 'UNAPPROVED_RUNTIME_DELTA')
    STAGE = 'protected_backups'
    sys.path.insert(0, str(previous / 'control-plane'))
    from control_plane.store import create_verified_backup
    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    backup_dir = Path(env['CONTROL_PLANE_BACKUP_DIR']).resolve()
    require(backup_dir.is_dir(), 'BACKUP_DIRECTORY_UNAVAILABLE')
    database_backup = backup_dir / ('pre-folder-activation-' + stamp + '.sqlite3')
    require(not database_backup.exists(), 'DATABASE_BACKUP_EXISTS')
    backup = create_verified_backup(db, database_backup)
    database_backup.chmod(0o600)
    for item in approved['protected_config_hashes'].values():
        original = Path(item['path'])
        target = original.with_name(original.name + '.pre-folder-activation-' + stamp)
        require(not target.exists(), 'CONFIG_BACKUP_EXISTS')
        target.write_bytes(original.read_bytes())
        target.chmod(0o600)
    require(authority_snapshot(connection) == before, 'AUTHORITY_CHANGED_BEFORE_SWITCH')
    require(identity()[0] == pid and current.resolve() == previous.resolve(), 'SERVICE_CHANGED_BEFORE_SWITCH')
    STAGE = 'official_activation_config'
    activation = load('folder_activation_config', candidate / 'deploy/prepare-control-plane-activation.py')
    config_receipt = activation.prepare_activation_config(release_dir=candidate,
        env_file=Path(approved['protected_config_hashes']['environment']['path']),
        drop_in=Path(approved['protected_config_hashes']['drop_in']['path']))
    STAGE = 'atomic_switch_and_restart'
    temporary = base / ('.current-folder-activation-' + stamp)
    require(not temporary.exists(), 'SWITCH_TEMP_EXISTS')
    temporary.symlink_to(candidate)
    os.replace(temporary, current)
    subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True, capture_output=True)
    subprocess.run(['systemctl', '--user', 'restart', SERVICE], check=True, capture_output=True)
    STAGE = 'postflight'
    package_sha = approved['verification']['package_source_sha256']
    deadline = time.monotonic() + 20
    health = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen('https://svhome.tail0e4032.ts.net/healthz', timeout=3) as response:
                observed = json.loads(response.read(65536))
            if observed.get('package_source_sha256') == package_sha:
                health = observed
                break
        except Exception:
            pass
        time.sleep(0.5)
    require(health is not None and health.get('expected_package_source_sha256') == package_sha, 'NEW_HEALTH_FINGERPRINT_NOT_PROVEN')
    new_pid, new_env = identity()
    require(new_pid != pid and new_env.get('PYTHONPATH') == str(candidate / 'control-plane') and new_env.get('CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256') == package_sha, 'NEW_SERVICE_IDENTITY_NOT_PROVEN')
    require(current.resolve() == candidate.resolve(), 'CURRENT_CANDIDATE_MISMATCH')
    require(authority_snapshot(connection) == before, 'AUTHORITY_CHANGED_DURING_DEPLOYMENT')
    require(connection.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'POSTFLIGHT_SQLITE_INTEGRITY_FAILED')
    print(json.dumps({'operation': 'reviewed_folder_activation_overlay_deployment', 'ok': True,
        'old_service_pid': pid, 'new_service_pid': new_pid, 'release_name': name,
        'package_source_sha256': package_sha, 'archive_sha256': approved['candidate_archive_sha256'],
        'changed_runtime_files': changed, 'unchanged_release_files': approved['unchanged_release_files'],
        'release_verification': verified, 'activation_config': config_receipt,
        'backup_remote_path': str(database_backup), 'backup': backup,
        'authority_and_history_unchanged': True, 'schema_version': 29,
        'completed_at_ms': int(time.time() * 1000)}, separators=(',', ':')))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'operation': 'reviewed_folder_activation_overlay_deployment', 'ok': False,
            'stage': STAGE, 'error_code': str(error) if isinstance(error, RuntimeError) else type(error).__name__,
            'operator_action': 'Inspect immutable release, protected config and service; no automatic authority rollback.'}, separators=(',', ':')))
        sys.exit(1)
