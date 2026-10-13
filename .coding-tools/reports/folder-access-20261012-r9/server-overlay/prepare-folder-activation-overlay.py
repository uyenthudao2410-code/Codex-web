"""Transplant reviewed folder activation onto exact manifest-verified serving source.

No remote mutations. Only store.py/http_api.py/authority-renewal.py change; all other serving files
remain byte-for-byte intact. No config, credential, database or schema copied.
"""
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
ROOT = OUT.parents[3]
BASE = OUT / 'serving-baseline'


def sha(content):
    return hashlib.sha256(content).hexdigest()


def methods(source, class_name):
    tree = ast.parse(source)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    return {node.name: node for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def method(source, class_name, name):
    node = methods(source, class_name)[name]
    return ''.join(source.splitlines(keepends=True)[node.lineno - 1:node.end_lineno]) + '\n'


def replace_method(source, class_name, name, replacement):
    node = methods(source, class_name)[name]
    lines = source.splitlines(keepends=True)
    return ''.join(lines[:node.lineno - 1]) + replacement + ''.join(lines[node.end_lineno:])


def insert_method(source, class_name, before, replacement):
    node = methods(source, class_name)[before]
    lines = source.splitlines(keepends=True)
    return ''.join(lines[:node.lineno - 1]) + replacement + '\n' + ''.join(lines[node.lineno - 1:])


def ast_guard(before, after, class_name, allowed):
    original, changed = ast.parse(before), ast.parse(after)
    for tree in (original, changed):
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
        cls.body = [node for node in cls.body if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name not in allowed]
    if ast.dump(original) != ast.dump(changed):
        raise RuntimeError('NON_ALLOWLISTED_SOURCE_CHANGE')


def bounded(source, start, end):
    left = source.index(start)
    right = source.index(end, left)
    return source[left:right]


def renewal_guard(before, after):
    allowed = {'_identity', '_expiry', '_selected_pilot', '_verify_renewal', 'renew_authority'}
    trees = [ast.parse(before), ast.parse(after)]
    for tree in trees:
        tree.body = [node for index, node in enumerate(tree.body)
            if not (index == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))
            and not (isinstance(node, ast.FunctionDef) and node.name in allowed)
            and not (isinstance(node, ast.Import) and len(node.names) == 1 and node.names[0].name == 're')]
    if ast.dump(trees[0]) != ast.dump(trees[1]):
        raise RuntimeError('NON_ALLOWLISTED_RENEWAL_SOURCE_CHANGE')


def component(records, prefix):
    digest = hashlib.sha256()
    for record in records:
        if record['path'].startswith(prefix):
            digest.update(record['path'].encode() + b'\0' + record['sha256'].encode('ascii') + b'\0')
    return digest.hexdigest()


def main():
    observation = json.loads((OUT / 'serving-baseline-receipt.json').read_text())
    manifest = observation['manifest']
    paths = {'store': 'control-plane/control_plane/store.py', 'http': 'control-plane/control_plane/http_api.py',
             'renewal': 'deploy/control-plane-authority-renewal.py'}
    source = {key: (ROOT / relative).read_text(encoding='utf-8').replace('\r\n', '\n') for key, relative in paths.items()}
    original = {key: (BASE / relative).read_text(encoding='utf-8').replace('\r\n', '\n') for key, relative in paths.items()}
    store = original['store']
    for name in ('_quarantined_retired_file_read_unknown_matches_pilot_workspace', 'node_authority_status'):
        store = replace_method(store, 'ControlPlaneStore', name, method(source['store'], 'ControlPlaneStore', name))
    store = insert_method(store, 'ControlPlaneStore', 'list_enrollment_requests', method(source['store'], 'ControlPlaneStore', 'activate_node_workspace'))
    ast_guard(original['store'], store, 'ControlPlaneStore', {
        '_quarantined_retired_file_read_unknown_matches_pilot_workspace', 'node_authority_status', 'activate_node_workspace'})
    http = replace_method(original['http'], 'ControlPlaneHandler', '_node_policy_authority',
                          method(source['http'], 'ControlPlaneHandler', '_node_policy_authority'))
    http = insert_method(http, 'ControlPlaneHandler', '_session_cookie', method(source['http'], 'ControlPlaneHandler', '_activate_node_workspace'))
    route_start = '            node_workspace_activate_match = '
    route_end = '            node_policy_template_match = '
    route = bounded(source['http'], route_start, route_end)
    if route_start in http or http.count(route_end) != 1:
        raise RuntimeError('ACTIVATION_ROUTE_ANCHOR_DRIFT')
    http = http.replace(route_end, route + route_end, 1)
    status_start = '            node_authority_status_match = '
    status_end = '            node_match = '
    status_before = bounded(http, status_start, status_end)
    status_after = bounded(source['http'], status_start, status_end)
    http = http.replace(status_before, status_after, 1)
    # Entire HTTP POST method may differ only by these two reviewed route edits.
    reversed_http = http.replace(route, '', 1).replace(status_after, status_before, 1)
    ast_guard(original['http'], reversed_http, 'ControlPlaneHandler', {'_node_policy_authority', '_activate_node_workspace'})
    renewal_guard(original['renewal'], source['renewal'])
    if sha((ROOT / paths['renewal']).read_bytes()) != '5a8be1f85dc05795307d8850295808971b615d04e720a28a6d5ca598af3d2d81':
        raise RuntimeError('REVIEWED_RENEWAL_HASH_DRIFT')
    modified = {paths['store']: store.encode(), paths['http']: http.encode(), paths['renewal']: source['renewal'].encode()}
    digest = sha(b''.join(modified[path] for path in sorted(modified)))
    name = 'codex-control-plane-local-folder-activation-1012-r9-' + digest[:12]
    candidate = OUT / name
    candidate.mkdir(parents=True, exist_ok=True)
    records = []
    for record in manifest['files']:
        relative = record['path']
        original_bytes = (BASE / relative).read_bytes()
        if len(original_bytes) != record['size_bytes'] or sha(original_bytes) != record['sha256']:
            raise RuntimeError('LOCAL_BASELINE_MANIFEST_DRIFT')
        content = modified.get(relative, original_bytes)
        target = candidate / relative
        if target.exists() and target.read_bytes() != content:
            raise RuntimeError('CANDIDATE_WOULD_OVERWRITE_DIFFERENT_EVIDENCE')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        records.append({'path': relative, 'size_bytes': len(content), 'sha256': sha(content)})
    changed = [record['path'] for old, record in zip(manifest['files'], records) if old != record]
    if set(changed) != set(modified) or len(records) != len(manifest['files']):
        raise RuntimeError('OVERLAY_FILE_SET_DRIFT')
    package_digest = hashlib.sha256()
    for file in sorted((candidate / 'control-plane/control_plane').glob('*.py')):
        package_digest.update(file.name.encode() + b'\0' + hashlib.sha256(file.read_bytes()).digest() + b'\0')
    candidate_manifest = {**manifest, 'release_name': name, 'package_source_sha256': 'sha256:' + package_digest.hexdigest(),
        'component_sha256': {key: component(records, prefix) for key, prefix in
            {'control_plane': 'control-plane/control_plane/', 'deployment': 'deploy/', 'documentation': 'DEPLOYMENT.md'}.items()},
        'files': records}
    (candidate / 'release-manifest.json').write_text(json.dumps(candidate_manifest, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    spec = importlib.util.spec_from_file_location('folder_overlay_verifier', candidate / 'deploy/control-plane-verify-release.py')
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    verified = verifier.verify_release(candidate)
    for key, relative in paths.items():
        (OUT / (key + '-reviewed-transplant.diff')).write_text(''.join(difflib.unified_diff(
            original[key].splitlines(True), modified[relative].decode().splitlines(True),
            fromfile='serving/' + relative, tofile='candidate/' + relative)), encoding='utf-8')
    archive = OUT / (name + '.tar.gz')
    with tarfile.open(archive, 'w:gz', compresslevel=9) as bundle:
        def modes(item):
            item.uid = item.gid = 0
            item.uname = item.gname = ''
            item.mode = 0o755 if item.isdir() or item.name.endswith('.sh') else 0o644
            return item
        bundle.add(candidate, arcname=name, filter=modes)
    receipt = {'operation': 'folder_activation_overlay_preparation', 'remote_mutations': False,
        'baseline_service_pid': observation['service_pid'], 'baseline_release_root': observation['release_root'],
        'baseline_manifest_sha256': observation['manifest_sha256'], 'baseline_package_source_sha256': manifest['package_source_sha256'],
        'protected_config_hashes': observation['protected_config_hashes'], 'candidate_release': str(candidate),
        'candidate_archive': str(archive), 'candidate_archive_sha256': sha(archive.read_bytes()),
        'candidate_manifest_sha256': sha((candidate / 'release-manifest.json').read_bytes()),
        'changed_runtime_files': changed, 'unchanged_release_files': len(records) - len(changed),
        'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'local_reviewed_source_sha256': {relative: sha((ROOT / relative).read_bytes()) for relative in paths.values()},
        'candidate_runtime_sha256': {relative: sha(content) for relative, content in modified.items()},
        'original_source_revision_semantics': 'Serving baseline revision retained; reviewed uncommitted method overlays bound by explicit hashes.',
        'verification': verified}
    (OUT / 'overlay-preparation-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, separators=(',', ':')))


if __name__ == '__main__':
    main()
