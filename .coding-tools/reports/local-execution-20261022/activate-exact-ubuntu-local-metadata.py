#!/usr/bin/env python3
"""One exact Ubuntu metadata update. Default: read-only; add --execute to apply.

Run as svhome. No admission API, pilot renewal/revocation, database restore,
tunnel configuration or credential changes. No network download is required.
"""
import argparse
import ast
from contextlib import closing
import fcntl
import hashlib
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import platform
import pwd
import re
import shutil
import socket
import sqlite3
import stat
import subprocess
import sys
import time
import urllib.request

sys.dont_write_bytecode = True
HOME = Path('/home/svhome')
INSTALL = HOME / '.local/lib/codex-control-plane'
RELEASES, CURRENT = INSTALL / 'releases', INSTALL / 'current'
BASELINE = RELEASES / 'codex-control-plane-parallel-native-1012-f7acd9ec4ba1'
SERVICE = 'codex-control-plane.service'
EXPECTED_PID = 970133
BASE_MANIFEST = 'c65439e1de52b741483debfd0600b52e7d969a8641818c554071990d4b3b1a3d'
BASE_PACKAGE = 'sha256:eb8c83abf44aca6c73ae5760813cda91d76187605cc53bbf1ae92cf6bb85f22d'
BASE_NODE = 'e368fd239446c8313c871dd41e4b35356e40bef83fff0bff80debff528f92f96'
NEW_NODE = '5af9fe034347c35ce77bfe5742546e3656daaa1cbf3cc17bc35bb111bcee27c7'
NEW_PACKAGE = 'sha256:a96208eb770ef62cc58566bf7ebd7202b56a7c0f2713521d943fb0cfc49e1734'
NODE = 'control-plane/control_plane/node_agent.py'
CONFIRMED_GENERATED_CACHES = frozenset({
    'control-plane/control_plane/__pycache__/__init__.cpython-314.pyc',
    'control-plane/control_plane/__pycache__/store.cpython-314.pyc',
})
ENV = HOME / '.config/codex-control-plane/control-plane.env'
DROP = HOME / '.config/systemd/user/codex-control-plane.service.d/10-immutable-release.conf'
CONTRACT = {'schema_version': 32, 'profile': 'control-plane-private-tunnel-service-v1',
            'sha256': '3664b70740d8d7359a3605b5ce42d7cbf3329e27dcfeec27d22b23ec9c631f66'}
HISTORICAL = {'action_id': 'act_0f0a49c6424d42d3bc7bc49ad46e4ffa',
              'device_id': '3c7378b3-ecc4-4466-9a87-25d4d53ffdcf',
              'workspace_id': 'workspace_4b0a57021f324dfc8cc3d2aca229d7cf',
              'workspace_generation': 'generation_990bc5104fd24f3ab2c021a3257132ab',
              'tool_name': 'workspace_context', 'delivery_state': 'dispatch_unconfirmed',
              'expires_at_ms': 1789835463391, 'settled_at_ms': None}
AUX = ['codex-control-plane-' + name for name in ('backup', 'healthcheck', 'authority-renewal')]
STAGE = 'preflight'
RELEASE_FAILURE_MESSAGES = {
    'invalid release file path', 'release contains a symlink',
    'release contains an unsupported entry', 'release manifest is unavailable',
    'release manifest is invalid', 'release component is empty',
    'release directory is invalid', 'release manifest has an unexpected schema',
    'release manifest identity is invalid', 'release source revision is invalid',
    'release control-plane schema is invalid', 'release package fingerprint is invalid',
    'release build metadata is invalid', 'release component metadata is invalid',
    'release file manifest is invalid', 'release file set does not match manifest',
    'release file hash does not match manifest', 'release component hash does not match manifest',
}


class ReleaseCheckFailure(RuntimeError):
    def __init__(self, code, issues):
        super().__init__(code)
        self.issues = issues


def require(value, code):
    if not value:
        raise RuntimeError(code)


def sha(content):
    return hashlib.sha256(content).hexdigest()


def run(*arguments):
    result = subprocess.run(['systemctl', '--user', *arguments], capture_output=True, timeout=45)
    require(result.returncode == 0, 'SYSTEMD_COMMAND_FAILED')
    return result.stdout.decode()


def properties(unit):
    raw = run('show', unit, '--property=LoadState,ActiveState,MainPID,ControlGroup,ExecStart')
    return dict(line.split('=', 1) for line in raw.splitlines() if '=' in line)


def private(path):
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
            and info.st_mode & 0o077 == 0, 'PROTECTED_FILE_INVALID')
    return path.read_bytes(), stat.S_IMODE(info.st_mode)


def atomic(path, content, mode):
    temporary = path.with_name('.' + path.name + '.local-metadata-' + str(os.getpid()))
    with temporary.open('xb') as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.chmod(mode)
    os.replace(temporary, path)


def switch(target):
    temporary = CURRENT.with_name('.current-local-metadata-' + str(os.getpid()))
    require(not temporary.exists() and not temporary.is_symlink(), 'CURRENT_TEMP_EXISTS')
    temporary.symlink_to(target)
    os.replace(temporary, CURRENT)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_release(verifier, root):
    try:
        return verifier.verify_release(root)
    except verifier.ReleaseVerificationError as error:
        message = str(error)
        code = 'RELEASE_VERIFY_' + re.sub('[^A-Z0-9]+', '_', message.upper()).strip('_') if message in RELEASE_FAILURE_MESSAGES else 'RELEASE_VERIFICATION_FAILED'
        issues = []
        try:
            manifest = json.loads((root / 'release-manifest.json').read_bytes())
            expected = {record['path']: record for record in manifest['files']}
            actual = {}
            for path in root.rglob('*'):
                relative = path.relative_to(root).as_posix()
                mode = path.lstat().st_mode
                if stat.S_ISLNK(mode):
                    issues.append({'issue': 'SYMLINK', 'path': relative})
                elif stat.S_ISREG(mode):
                    actual[relative] = path
                elif not stat.S_ISDIR(mode):
                    issues.append({'issue': 'UNSUPPORTED_ENTRY', 'path': relative})
            issues.extend({'issue': 'EXTRA_FILE', 'path': relative} for relative in sorted(set(actual) - set(expected) - {'release-manifest.json'}))
            for relative, record in expected.items():
                if relative not in actual:
                    issues.append({'issue': 'MISSING_REGULAR_FILE', 'path': relative})
                elif len(actual[relative].read_bytes()) != record['size_bytes'] or sha(actual[relative].read_bytes()) != record['sha256']:
                    issues.append({'issue': 'FILE_BYTES_CHANGED', 'path': relative})
        except Exception:
            pass
        raise ReleaseCheckFailure(code, issues[:100]) from None


def check_baseline(verifier):
    try:
        return check_release(verifier, BASELINE), []
    except ReleaseCheckFailure as error:
        if str(error) != 'RELEASE_VERIFY_RELEASE_FILE_SET_DOES_NOT_MATCH_MANIFEST':
            raise
        # This exact observed cache pair is retained in the live baseline.
        # Every manifested file and all other file-set checks remain strict.
        manifest = json.loads((BASELINE / 'release-manifest.json').read_bytes())
        expected = {record['path']: record for record in manifest['files']}
        actual = verifier._regular_files(BASELINE)
        actual.pop('release-manifest.json')
        extras = set(actual) - set(expected)
        if extras != CONFIRMED_GENERATED_CACHES or set(expected) - set(actual):
            raise error
        for relative, record in expected.items():
            content = actual[relative].read_bytes()
            require(len(content) == record['size_bytes'] and sha(content) == record['sha256'],
                    'BASELINE_MANIFESTED_FILE_CHANGED')
        for component, prefix in verifier.COMPONENT_PREFIXES.items():
            require(verifier._component_digest(manifest['files'], prefix) == manifest['component_sha256'][component],
                    'BASELINE_COMPONENT_CHANGED')
        return {'package_source_sha256': manifest['package_source_sha256']}, sorted(extras)


def database_state(database, idle=True):
    now = int(time.time() * 1000)
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True, timeout=5)) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA query_only=ON')
        connection.execute('BEGIN')
        require(connection.execute('PRAGMA user_version').fetchone()[0] == 29, 'DATABASE_SCHEMA_CHANGED')
        tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        records = {}
        for table in tables:
            require(re.fullmatch('[a-z][a-z0-9_]*', table), 'DATABASE_TABLE_INVALID')
            query = 'SELECT * FROM ' + table
            if table == 'nodes':
                query = 'SELECT device_id,endpoint_id,owner_id,display_name,credential_hash,credential_created_at_ms,credential_generation,revoked_at_ms FROM nodes'
            elif table == 'events':
                query += " WHERE event_type != 'node_heartbeat'"
            records[table] = {json.dumps(dict(row), sort_keys=True, separators=(',', ':'))
                              for row in connection.execute(query)}
        actions = [dict(row) for row in connection.execute("SELECT action_id,device_id,workspace_id,workspace_generation,tool_name,delivery_state,expires_at_ms,settled_at_ms FROM actions WHERE settled_at_ms IS NULL AND delivery_state IN ('queued','dispatch_unconfirmed','accepted')")]
        exception = [row for row in actions if row['action_id'] == HISTORICAL['action_id']]
        if exception:
            require(exception == [HISTORICAL] and HISTORICAL['expires_at_ms'] < now, 'HISTORICAL_DISPATCH_CHANGED')
            require(connection.execute('SELECT COUNT(*) FROM mcp_read_only_intents WHERE action_id=?', (HISTORICAL['action_id'],)).fetchone()[0] == 1,
                    'HISTORICAL_READ_INTENT_CHANGED')
            for table in ('mcp_file_read_intents', 'mcp_approved_patch_intents', 'mcp_standing_patch_intents',
                          'mcp_exec_intents', 'mcp_artifact_intents', 'mcp_document_write_intents', 'receipts'):
                require(connection.execute('SELECT COUNT(*) FROM ' + table + ' WHERE action_id=?', (HISTORICAL['action_id'],)).fetchone()[0] == 0, 'HISTORICAL_ACTION_HAS_EFFECTFUL_INTENT')
        active = len(actions) - len(exception)
        unknown = connection.execute("SELECT a.action_id,a.expires_at_ms,r.disposition FROM actions a LEFT JOIN action_reconciliations r ON r.action_id=a.action_id WHERE a.settled_at_ms IS NULL AND a.delivery_state='reconcile_required'").fetchall()
        require(not idle or all(row['expires_at_ms'] <= now and row['disposition'] == 'quarantined_unknown'
                and connection.execute('SELECT COUNT(*) FROM mcp_exec_intents WHERE action_id=?', (row['action_id'],)).fetchone()[0] == 0
                for row in unknown), 'UNRESOLVED_WORK_BLOCKS_UPDATE')
        tasks = connection.execute('SELECT COUNT(*) FROM mcp_task_sessions WHERE closed_at_ms IS NULL AND expires_at_ms>?', (now,)).fetchone()[0]
        writers = connection.execute('SELECT COUNT(*) FROM mcp_task_writer_leases WHERE released_at_ms IS NULL AND expires_at_ms>?', (now,)).fetchone()[0]
        require(not idle or tasks == writers == active == 0, 'LIVE_WORK_BLOCKS_UPDATE')
        admission = connection.execute("SELECT state_value FROM control_plane_state WHERE state_key='admission_mode'").fetchone()[0]
        return records, {'active_actions': active, 'live_tasks': tasks, 'live_writers': writers,
                         'admission_mode': admission}


def json_http(url, body=None, token=None):
    headers = {} if token is None else {'Authorization': 'Bearer ' + token,
               'Content-Type': 'application/json', 'Accept': 'application/json',
               'MCP-Protocol-Version': '2026-07-28', 'Mcp-Method': 'tools/call',
               'Mcp-Name': 'workspace_context'}
    request = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(), headers=headers)
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    with urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect()).open(request, timeout=4) as response:
        return json.loads(response.read(1048576))


def prove_listener_ownership(pid, addresses):
    owned = set()
    for descriptor in Path('/proc/' + str(pid) + '/fd').iterdir():
        try:
            match = re.fullmatch(r'socket:\[(\d+)\]', os.readlink(descriptor))
        except FileNotFoundError:
            continue
        if match:
            owned.add(match.group(1))
    listeners = []
    for line in Path('/proc/net/tcp').read_text().splitlines()[1:]:
        fields = line.split()
        if len(fields) > 9 and fields[3] == '0A':
            address, port = fields[1].split(':')
            host = socket.inet_ntoa(bytes.fromhex(address)[::-1])
            listeners.append(((host, int(port, 16)), fields[9]))
    for address in addresses:
        matches = [inode for endpoint, inode in listeners if endpoint == address]
        require(matches and all(inode in owned for inode in matches), 'SYSTEMD_PID_DOES_NOT_OWN_LISTENER')


def observe(environment, package, authorization):
    bind_host = str(ipaddress.ip_address(environment.get('CONTROL_PLANE_BIND', '127.0.0.1')))
    host = bind_host
    host = '127.0.0.1' if host == '0.0.0.0' else host
    require(':' not in host, 'IPV4_BIND_REQUIRED')
    port = int(environment.get('CONTROL_PLANE_PORT', '8765'))
    mcp_port = int(environment.get('CONTROL_PLANE_MCP_PORT', '8766'))
    require(environment.get('CONTROL_PLANE_MCP_BIND', '127.0.0.1') == '127.0.0.1'
            and 1024 <= port <= 65535 and 1024 <= mcp_port <= 65535, 'LISTENER_CONFIG_INVALID')
    health = json_http('http://' + host + ':' + str(port) + '/healthz')
    require(health.get('ok') is True and health.get('schema_version') == 29
            and health.get('package_source_sha256') == health.get('expected_package_source_sha256') == package,
            'SERVICE_PACKAGE_NOT_PROVEN')
    token = authorization.decode().strip().removeprefix('Bearer ')
    require(re.fullmatch(r'mcpsvc_[A-Za-z0-9_-]{32,128}', token), 'MCP_CREDENTIAL_INVALID')
    body = {'jsonrpc': '2.0', 'id': 'local-metadata-observation', 'method': 'tools/call',
            'params': {'name': 'workspace_context', 'arguments': {'operation': 'inventory'},
                       '_meta': {'io.modelcontextprotocol/protocolVersion': '2026-07-28',
                                 'io.modelcontextprotocol/clientCapabilities': {}}}}
    rpc = json_http('http://127.0.0.1:' + str(mcp_port) + '/mcp', body, token)
    result = rpc.get('result', {})
    require('error' not in rpc and result.get('isError') is not True, 'MCP_INVENTORY_FAILED')
    inventory = result['structuredContent']
    require(inventory['tool_contract'] == CONTRACT and inventory.get('workspace_accessed') is False,
            'FACADE_CONTRACT_CHANGED')
    # This baseline's health contract has no PID field. Bind both listeners to
    # the systemd process through actual Linux listening socket inodes instead.
    pid = int(properties(SERVICE)['MainPID'])
    require(pid > 1, 'SYSTEMD_PROCESS_NOT_RUNNING')
    prove_listener_ownership(pid, [(bind_host, port), ('127.0.0.1', mcp_port)])
    require(int(properties(SERVICE)['MainPID']) == pid, 'SYSTEMD_PROCESS_CHANGED_DURING_OBSERVATION')
    return {'service_instance_id': health['service_instance_id'],
            'binding_ids': sorted(target['binding_id'] for target in inventory.get('targets', []))}, [(host, port), ('127.0.0.1', mcp_port)]


def stopped(cgroup, listeners):
    state = properties(SERVICE)
    require(state['ActiveState'] == 'inactive' and int(state['MainPID']) == 0, 'SERVICE_NOT_STOPPED')
    require(cgroup.startswith('/') and '..' not in Path(cgroup).parts, 'CGROUP_PATH_INVALID')
    process_file = Path('/sys/fs/cgroup') / cgroup.lstrip('/') / 'cgroup.procs'
    require(not process_file.exists() or not process_file.read_text().strip(), 'SERVICE_CGROUP_NOT_EMPTY')
    for address in listeners:
        with socket.socket() as probe:
            probe.settimeout(0.3)
            require(probe.connect_ex(address) != 0, 'SERVICE_LISTENER_STILL_OPEN')


def main():
    global STAGE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    execute = parser.parse_args().execute
    require(Path.home() == HOME and pwd.getpwuid(os.getuid()).pw_name == 'svhome', 'RUN_AS_SVHOME_WITHOUT_SUDO')
    require(CURRENT.is_symlink() and CURRENT.resolve() == BASELINE and not BASELINE.is_symlink(), 'BASELINE_RELEASE_CHANGED')
    require(sha((BASELINE / 'release-manifest.json').read_bytes()) == BASE_MANIFEST
            and sha((BASELINE / NODE).read_bytes()) == BASE_NODE, 'BASELINE_SOURCE_CHANGED')
    pinned_manifest = json.loads((BASELINE / 'release-manifest.json').read_bytes())
    verifier_record = next(record for record in pinned_manifest['files'] if record['path'] == 'deploy/control-plane-verify-release.py')
    require(sha((BASELINE / verifier_record['path']).read_bytes()) == verifier_record['sha256'], 'BASELINE_VERIFIER_CHANGED')
    verifier = load('exact_baseline_verifier', BASELINE / 'deploy/control-plane-verify-release.py')
    verified_baseline, generated_caches = check_baseline(verifier)
    require(verified_baseline['package_source_sha256'] == BASE_PACKAGE, 'BASELINE_INTEGRITY_FAILED')
    service = properties(SERVICE)
    require(service['ActiveState'] == 'active' and int(service['MainPID']) == EXPECTED_PID, 'BASELINE_SERVICE_CHANGED')
    require(str(CURRENT / 'deploy/control-plane-launcher.sh') in service['ExecStart'], 'SERVICE_LAUNCHER_CHANGED')
    environment = dict(item.split('=', 1) for item in Path('/proc/' + str(EXPECTED_PID) + '/environ').read_text().split('\0') if '=' in item)
    require(environment.get('PYTHONPATH') == str(BASELINE / 'control-plane')
            and environment.get('CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256') == BASE_PACKAGE,
            'SERVING_SOURCE_CHANGED')
    database = Path(environment['CONTROL_PLANE_DB'])
    if not database.is_absolute():
        database = Path('/proc/' + str(EXPECTED_PID) + '/cwd').resolve() / database
    database = database.resolve()
    require(database.is_file() and not database.is_relative_to(INSTALL), 'DATABASE_PATH_INVALID')
    configs = {path: private(path) for path in (ENV, DROP)}
    authorization, _ = private(HOME / '.config/codex-control-plane/ubuntu-root-mcp-authorization')
    old_observation, listeners = observe(environment, BASE_PACKAGE, authorization)
    before, counts = database_state(database)
    timers = [name + '.timer' for name in AUX if properties(name + '.timer').get('ActiveState') == 'active']
    require(all(properties(name + '.service').get('ActiveState') in ('inactive', 'failed') for name in AUX), 'AUXILIARY_JOB_BUSY')
    if not execute:
        print(json.dumps({'ok': True, 'stage': STAGE, 'service_pid': EXPECTED_PID,
                          'baseline_node_sha256': BASE_NODE, 'candidate_node_sha256': NEW_NODE,
                          'candidate_package_sha256': NEW_PACKAGE, 'counts': counts,
                          'confirmed_baseline_caches_preserved_and_excluded_from_candidate': generated_caches,
                          'binding_ids': old_observation['binding_ids'], 'external_mutations_performed': False}))
        return
    os.umask(0o077)
    descriptor = os.open(INSTALL / '.local-metadata-update.lock', os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    candidate = RELEASES / 'codex-control-plane-local-metadata-20261022-5af9fe034347'
    paused, service_stopped, changed, start_attempted = [], False, False, False
    stop_attempted = False
    expected_configs = {}
    old_link = os.readlink(CURRENT)
    backup = None
    try:
        STAGE = 'prepare_exact_two_line_overlay'
        require(not candidate.exists(), 'CANDIDATE_ALREADY_EXISTS')
        def omit_confirmed_cache_pair(directory, names):
            relative = Path(directory).relative_to(BASELINE)
            return [name for name in names if (relative / name).as_posix() in CONFIRMED_GENERATED_CACHES]
        shutil.copytree(BASELINE, candidate, copy_function=shutil.copy2, ignore=omit_confirmed_cache_pair)
        original = (candidate / NODE).read_bytes()
        anchor = b'        and value["policy_decision"] in ("isolated_unapproved_command", "isolated_preferred")\n'
        addition = b'        or value["execution_backend"] == "local" and value["isolation_level"] == "host_user"\n        and value["policy_decision"] == "operator_local"\n'
        require(original.count(anchor) == 1, 'METADATA_ANCHOR_CHANGED')
        replacement = original.replace(anchor, anchor + addition)
        require(sha(replacement) == NEW_NODE and replacement.replace(addition, b'', 1) == original, 'OVERLAY_NOT_EXACT')
        ast.parse(replacement)
        (candidate / NODE).write_bytes(replacement)
        manifest = json.loads((candidate / 'release-manifest.json').read_bytes())
        manifest['release_name'] = candidate.name
        manifest['source_revision'] = sha(b'local-execution-two-line-overlay-v1\0' + bytes.fromhex(BASE_MANIFEST) + bytes.fromhex(NEW_NODE))
        manifest['build'] = {'python': platform.python_version(), 'platform': platform.system().lower()}
        manifest['package_source_sha256'] = NEW_PACKAGE
        for record in manifest['files']:
            if record['path'] == NODE:
                record['sha256'], record['size_bytes'] = NEW_NODE, len(replacement)
            else:
                require((candidate / record['path']).read_bytes() == (BASELINE / record['path']).read_bytes(), 'UNRELATED_RELEASE_CHANGE')
        manifest['component_sha256']['control_plane'] = verifier._component_digest(manifest['files'], 'control-plane/control_plane/')
        (candidate / 'release-manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
        require(check_release(verifier, candidate)['package_source_sha256'] == NEW_PACKAGE, 'CANDIDATE_VERIFICATION_FAILED')
        # Execute only the installed maintained pure fingerprint function.
        http_tree = ast.parse((candidate / 'control-plane/control_plane/http_api.py').read_bytes())
        fingerprint = next(node for node in http_tree.body if isinstance(node, ast.FunctionDef) and node.name == '_package_source_sha256')
        scope = {'Path': Path, 'hashlib': hashlib}
        exec(compile(ast.Module(body=[fingerprint], type_ignores=[]), 'maintained_package_fingerprint', 'exec'), scope)
        require(scope['_package_source_sha256'](candidate / 'control-plane/control_plane') == NEW_PACKAGE, 'CANDIDATE_PACKAGE_HASH_CHANGED')
        STAGE = 'pause_competing_timers'
        for timer in timers:
            paused.append(timer)
            run('stop', timer)
        require(all(properties(name + '.service').get('ActiveState') in ('inactive', 'failed') for name in AUX), 'AUXILIARY_JOB_BUSY')
        require(properties(SERVICE)['MainPID'] == str(EXPECTED_PID) and CURRENT.resolve() == BASELINE, 'SERVICE_CHANGED_BEFORE_STOP')
        before, counts = database_state(database)
        STAGE = 'stop_exact_service_and_confirm_idle'
        stop_attempted = True
        run('stop', SERVICE)
        service_stopped = True
        stopped(service['ControlGroup'], listeners)
        final, final_counts = database_state(database)
        require(final == before and final_counts['admission_mode'] == counts['admission_mode'], 'CAUSAL_STATE_CHANGED_DURING_STOP')
        STAGE = 'backup_stopped_database_and_config'
        backup = INSTALL / 'backups' / ('local-metadata-' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '-' + str(os.getpid()))
        backup.mkdir(mode=0o700, parents=True, exist_ok=False)
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as source, closing(sqlite3.connect(backup / 'control-plane-before.sqlite3')) as target:
            source.backup(target)
            require(target.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'BACKUP_INTEGRITY_FAILED')
        for path, (content, mode) in configs.items():
            require(private(path) == (content, mode), 'CONFIGURATION_CHANGED')
            atomic(backup / (path.name + '.before'), content, mode)
        atomic(backup / 'previous-current-link.txt', old_link.encode(), 0o600)
        stopped(service['ControlGroup'], listeners)
        require(database_state(database)[0] == final, 'CAUSAL_STATE_CHANGED_WHILE_STOPPED')
        STAGE = 'activate_immutable_source_identity'
        activation = load('exact_activation_helper', candidate / 'deploy/prepare-control-plane-activation.py')
        require(all(private(path) == value for path, value in configs.items()), 'CONFIGURATION_CHANGED_BEFORE_ACTIVATION')
        for path, (content, mode) in configs.items():
            text = activation._replace_key(content.decode(), activation.REVISION_KEY, manifest['source_revision'], environment=path == ENV)
            text = activation._replace_key(text, activation.FINGERPRINT_KEY, NEW_PACKAGE, environment=path == ENV)
            expected_configs[path] = (text.encode(), mode)
        changed = True
        activation.prepare_activation_config(release_dir=candidate, env_file=ENV, drop_in=DROP)
        require(all(private(path) == value for path, value in expected_configs.items()), 'ACTIVATION_CONFIG_NOT_EXACT')
        stopped(service['ControlGroup'], listeners)
        require(CURRENT.resolve() == BASELINE, 'CURRENT_CHANGED')
        switch(candidate)
        run('daemon-reload')
        stopped(service['ControlGroup'], listeners)
        STAGE = 'start_once_and_verify'
        start_attempted = True
        run('start', SERVICE)
        service_stopped = False
        deadline = time.monotonic() + 25
        while True:
            try:
                observed, _ = observe(environment, NEW_PACKAGE, authorization)
                break
            except Exception:
                if time.monotonic() >= deadline:
                    raise RuntimeError('POSTSTART_SOURCE_OR_MCP_NOT_PROVEN') from None
                time.sleep(0.5)
        active = properties(SERVICE)
        require(active['ActiveState'] == 'active' and int(active['MainPID']) > 1
                and int(active['MainPID']) != EXPECTED_PID and CURRENT.resolve() == candidate
                and observed['service_instance_id'] != old_observation['service_instance_id'], 'NEW_INSTANCE_NOT_PROVEN')
        new_environment = dict(item.split('=', 1) for item in Path('/proc/' + active['MainPID'] + '/environ').read_text().split('\0') if '=' in item)
        require(new_environment.get('PYTHONPATH') == str(candidate / 'control-plane')
                and new_environment.get('CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256') == NEW_PACKAGE
                and new_environment.get('CONTROL_PLANE_DECLARED_SOURCE_REVISION') == manifest['source_revision']
                and new_environment.get('CONTROL_PLANE_DB') == environment['CONTROL_PLANE_DB']
                and str(CURRENT / 'deploy/control-plane-launcher.sh') in active['ExecStart'], 'NEW_PROCESS_SOURCE_NOT_PROVEN')
        ignored = {'CONTROL_PLANE_DECLARED_SOURCE_REVISION', 'CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256'}
        require({key: value for key, value in new_environment.items() if key.startswith('CONTROL_PLANE_') and key not in ignored}
                == {key: value for key, value in environment.items() if key.startswith('CONTROL_PLANE_') and key not in ignored},
                'UNRELATED_SERVICE_SETTINGS_CHANGED')
        after, after_counts = database_state(database, idle=False)
        authority = ('scoped_pilot_decisions', 'mcp_service_grants', 'mcp_access_grants', 'oauth_principals', 'bindings', 'node_workspaces', 'control_plane_state')
        require(all(after[key] == final[key] for key in authority), 'AUTHORITY_CHANGED_CONCURRENTLY')
        historical_preserved = all(final[key] <= after[key] for key in final)
        require(historical_preserved, 'CAUSAL_HISTORY_CHANGED_AFTER_START')
        for timer in list(paused):
            run('start', timer)
            paused.remove(timer)
        require(all(properties(timer)['ActiveState'] == 'active' for timer in timers), 'TIMER_RESTORE_NOT_PROVEN')
        receipt = {'ok': True, 'stage': 'complete', 'new_service_pid': int(active['MainPID']),
                   'candidate_release': str(candidate), 'candidate_node_sha256': NEW_NODE,
                   'package_source_sha256': NEW_PACKAGE, 'source_kind': 'exact_two_line_baseline_overlay',
                   'source_revision_kind': 'content_derived_not_git_commit',
                   'pilots_and_admission_unchanged': True, 'admission_mode': after_counts['admission_mode'],
                   'existing_causal_rows_preserved': historical_preserved, 'counts': after_counts,
                   'confirmed_baseline_caches_preserved_and_excluded_from_candidate': generated_caches,
                   'binding_ids_before': old_observation['binding_ids'], 'binding_ids_after': observed['binding_ids'],
                   'backup_directory': str(backup), 'database_restored': False,
                   'temporarily_paused_timers_restored': timers,
                   'tunnel_credentials_or_service_changed': False, 'service_operation': 'stop then start exact user facade service'}
        atomic(backup / 'activation-receipt.json', json.dumps(receipt, indent=2).encode(), 0o600)
        print(json.dumps(receipt))
    except Exception:
        # A started candidate may have admitted real work. Never stop it again
        # automatically or roll back authority/database after that boundary.
        if stop_attempted and not start_attempted:
            actual = properties(SERVICE)
            service_stopped = actual['ActiveState'] == 'inactive' and int(actual['MainPID']) == 0
        if service_stopped and not start_attempted:
            stopped(service['ControlGroup'], listeners)
            if changed:
                require(CURRENT.resolve() in (BASELINE, candidate), 'ROLLBACK_CURRENT_CHANGED')
                for path, (content, mode) in configs.items():
                    require(private(path) in ((content, mode), expected_configs[path]), 'ROLLBACK_CONFIG_CHANGED_CONCURRENTLY')
                    atomic(path, content, mode)
                switch(old_link)
                run('daemon-reload')
            run('start', SERVICE)
        raise
    finally:
        failures = []
        try:
            for timer in paused:
                try:
                    run('start', timer)
                except Exception:
                    failures.append(timer)
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)
        require(not failures, 'TIMER_RESTORATION_FAILED')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) and re.fullmatch('[A-Z][A-Z0-9_]{2,95}', str(error)) else type(error).__name__
        print(json.dumps({'ok': False, 'stage': STAGE, 'error_code': code,
                          'integrity_issues': error.issues if isinstance(error, ReleaseCheckFailure) else [],
                          'next_action': 'Inspect exact service and retained backup; do not rerun after any start attempt without new identity evidence.'}))
        raise SystemExit(2) from None
