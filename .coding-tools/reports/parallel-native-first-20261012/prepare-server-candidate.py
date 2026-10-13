"""Prepare a bounded immutable overlay of the verified operated Ubuntu release."""
import ast
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tarfile

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
BASE = ROOT / '.coding-tools/reports/folder-access-20261012-r9/server-overlay/codex-control-plane-local-folder-activation-1012-r9-626768b49f4b'
ALLOW = (
    'control-plane/control_plane/http_api.py',
    'control-plane/control_plane/mcp_facade.py',
    'control-plane/control_plane/node_agent.py',
    'control-plane/control_plane/recovery_exec_bridge.cjs',
    'control-plane/control_plane/store.py',
    'control-plane/control_plane/workspace_policy_store.py',
    'deploy/control-plane-authority-renewal.py',
)

def sha(value):
    return hashlib.sha256(value).hexdigest()

def require(value, code):
    if not value:
        raise RuntimeError(code)

def component(records, prefix):
    digest = hashlib.sha256()
    for record in records:
        if record['path'].startswith(prefix):
            digest.update(record['path'].encode() + b'\0' + record['sha256'].encode() + b'\0')
    return digest.hexdigest()

def main():
    readiness = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    observed = readiness['serving_source']
    manifest_bytes = (BASE / 'release-manifest.json').read_bytes()
    require(sha(manifest_bytes) == observed['release_manifest_sha256'], 'BASELINE_MANIFEST_DRIFT')
    manifest = json.loads(manifest_bytes)
    require(manifest['files'] == observed['release_manifest_files'], 'BASELINE_FILE_SET_DRIFT')
    modified = {name: (ROOT / name).read_bytes().replace(b'\r\n', b'\n') for name in ALLOW}
    name = 'codex-control-plane-parallel-native-1012-' + sha(b''.join(modified[n] for n in sorted(modified)))[:12]
    candidate = OUT / name
    require(not candidate.exists(), 'CANDIDATE_ALREADY_EXISTS')
    candidate.mkdir()
    records, changed = [], []
    source_hashes = {}
    for old in manifest['files']:
        path = old['path']
        before = (BASE / path).read_bytes()
        require(len(before) == old['size_bytes'] and sha(before) == old['sha256'], 'BASELINE_CONTENT_DRIFT')
        content = modified.get(path, before)
        target = candidate / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        record = {'path': path, 'sha256': sha(content), 'size_bytes': len(content)}
        records.append(record)
        if record != old:
            changed.append(path)
            (OUT / (Path(path).stem + '-production-overlay.diff')).write_text(''.join(difflib.unified_diff(
                before.decode().splitlines(True), content.decode().splitlines(True),
                fromfile='serving/' + path, tofile='candidate/' + path)), encoding='utf-8')
        if path in modified:
            source_hashes[path] = sha((ROOT / path).read_bytes())
    baseline_paths = {record['path'] for record in manifest['files']}
    for path in sorted(set(ALLOW) - baseline_paths):
        require(path == 'control-plane/control_plane/workspace_policy_store.py', 'UNAPPROVED_NEW_RELEASE_FILE')
        content = modified[path]
        target = candidate / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        records.append({'path': path, 'sha256': sha(content), 'size_bytes': len(content)})
        changed.append(path)
        source_hashes[path] = sha((ROOT / path).read_bytes())
        (OUT / (Path(path).stem + '-production-overlay.diff')).write_text(''.join(difflib.unified_diff([], content.decode().splitlines(True), fromfile='/dev/null', tofile='candidate/' + path)), encoding='utf-8')
    records.sort(key=lambda record: record['path'])
    changed.sort()
    require(set(changed) <= set(ALLOW), 'UNAPPROVED_OVERLAY_DELTA')
    aggregate = hashlib.sha256()
    for target in sorted((candidate / 'control-plane/control_plane').glob('*.py')):
        aggregate.update(target.name.encode() + b'\0' + hashlib.sha256(target.read_bytes()).digest() + b'\0')
    new_manifest = {**manifest, 'release_name': name, 'package_source_sha256': 'sha256:' + aggregate.hexdigest(),
        'component_sha256': {key: component(records, prefix) for key, prefix in {
            'control_plane': 'control-plane/control_plane/', 'deployment': 'deploy/', 'documentation': 'DEPLOYMENT.md'}.items()},
        'files': records}
    (candidate / 'release-manifest.json').write_text(json.dumps(new_manifest, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    spec = importlib.util.spec_from_file_location('parallel_release_verifier', candidate / 'deploy/control-plane-verify-release.py')
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    verification = verifier.verify_release(candidate)
    for path in changed:
        if path.endswith('.py'):
            ast.parse((candidate / path).read_bytes(), filename=path)
    import_code = "import control_plane.http_api, control_plane.node_agent; import importlib.util; from pathlib import Path; p=Path('../deploy/control-plane-authority-renewal.py').resolve(); s=importlib.util.spec_from_file_location('candidate_authority_renewal',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print('candidate imports passed')"
    subprocess.run([sys.executable, '-B', '-c', import_code], cwd=candidate / 'control-plane', capture_output=True, check=True)
    contract_code = "from control_plane.mcp_facade import tool_contract; import json; c=tool_contract(auth_kind='private_tunnel_service',oauth_scopes=('control-plane.inventory',),oauth_file_read_enabled=True,oauth_patch_write_scope='control-plane.patch',oauth_approved_patch_enabled=True,oauth_standing_write_enabled=True,oauth_exec_enabled=True); print(json.dumps(c))"
    result = subprocess.run([sys.executable, '-B', '-c', contract_code], cwd=candidate / 'control-plane', capture_output=True, check=True)
    contract = json.loads(result.stdout)
    require({key: contract[key] for key in ('schema_version', 'profile', 'sha256')} == readiness['tool_contract'], 'PUBLIC_CONTRACT_DRIFT')
    archive = OUT / (name + '.tar.gz')
    with tarfile.open(archive, 'w:gz', compresslevel=9) as bundle:
        def modes(member):
            member.uid = member.gid = 0
            member.uname = member.gname = ''
            member.mode = 0o755 if member.isdir() or member.name.endswith('.sh') else 0o644
            return member
        bundle.add(candidate, arcname=name, filter=modes)
    receipt = {'operation': 'parallel_native_production_candidate_preparation', 'ok': True,
        'candidate_release': str(candidate), 'candidate_archive': str(archive), 'candidate_archive_sha256': sha(archive.read_bytes()),
        'candidate_manifest_sha256': sha((candidate / 'release-manifest.json').read_bytes()), 'verification': verification,
        'changed_runtime_files': changed, 'allowed_runtime_files': list(ALLOW), 'allowed_new_files': ['control-plane/control_plane/workspace_policy_store.py'], 'unchanged_release_files': len(records) - len(changed),
        'baseline_service_pid': readiness['service_pid'], 'baseline_release_root': observed['serving_release_root'],
        'baseline_manifest_sha256': observed['release_manifest_sha256'], 'baseline_package_source_sha256': observed['package_source_sha256'],
        'protected_config_hashes': readiness['protected_activation_config_hashes'], 'expected_contract': readiness['tool_contract'],
        'expected_unknown_actions': [{key: action[key] for key in ('action_id', 'workspace_id', 'workspace_generation', 'delivery_state', 'expires_at_ms', 'disposition')} for action in readiness['historical_unknown_actions_preserved']],
        'source_raw_sha256': source_hashes, 'base_revision': manifest.get('source_revision'),
        'uncommitted_overlay': True, 'remote_mutations_performed': False, 'database_restore_allowed': False}
    with (OUT / 'server-candidate-preparation.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(receipt, handle, indent=2)
        handle.write('\n')
    print(json.dumps({'ok': True, 'release': name, 'changed_files': changed, 'package': verification['package_source_sha256'], 'contract': readiness['tool_contract']}))

if __name__ == '__main__':
    main()
