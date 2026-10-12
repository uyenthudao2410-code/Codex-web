"""Prepare an immutable one-file delta package with a truthful snapshot ID.

No Git repository, branch, index, server, service or authority is mutated.
source_revision is a content-addressed source snapshot, not a claimed commit.
"""
import hashlib
import importlib.util
import io
import json
import platform
import tarfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

root = Path(__file__).resolve().parents[4]
out = Path(__file__).resolve().parent
review = out.parent / 'server-review'
archive_path = root / '.coding-tools/reports/mcp-web-contract-20261011/codex-control-plane-beaa9d5ade4926ef231e3ec9d0a517fe93830e90.tar.gz'
base_revision = 'beaa9d5ade4926ef231e3ec9d0a517fe93830e90'
base_name = 'codex-control-plane-' + base_revision
archive_sha = 'e31132a545da55cad564a373c138bb644917c8cbce73e87b724c88dfee6f3b36'
ui_sha = '03e5279c89bf4b1c04ef0139724e77eb960a3efdca32aa59ec2445e3b35fc64b'
changed_path = 'control-plane/control_plane/web_ui.py'
assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == archive_sha
payload = {}
modes = {}
with tarfile.open(archive_path, 'r:gz') as archive:
    for member in archive.getmembers():
        parts = PurePosixPath(member.name).parts
        assert parts and parts[0] == base_name and not member.name.startswith('/')
        assert all(p not in {'.', '..', ''} for p in parts)
        assert member.isdir() or member.isfile()
        if member.isfile():
            relative = PurePosixPath(*parts[1:]).as_posix()
            assert relative not in payload
            payload[relative] = archive.extractfile(member).read()
            modes[relative] = member.mode
base_manifest = json.loads(payload.pop('release-manifest.json'))
base_records = {record['path']: record for record in base_manifest['files']}
assert len(payload) == 38 and set(payload) == set(base_records)
for path, data in payload.items():
    assert len(data) == base_records[path]['size_bytes']
    assert hashlib.sha256(data).hexdigest() == base_records[path]['sha256']
ui_bytes = (review / ('web_ui.current-' + ui_sha + '.py')).read_bytes()
assert hashlib.sha256(ui_bytes).hexdigest() == ui_sha
compile(ui_bytes, changed_path, 'exec')
payload[changed_path] = ui_bytes
records = [{'path': p, 'size_bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()} for p, data in sorted(payload.items())]
canonical_records = json.dumps(records, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
identity = hashlib.sha256(canonical_records).hexdigest()
release_name = 'codex-control-plane-' + identity
release_dir = out / release_name
archive_output = out / (release_name + '.tar.gz')
assert not release_dir.exists() and not archive_output.exists(), 'Immutable outputs already exist'
package_digest = hashlib.sha256()
for path, data in sorted(payload.items()):
    relative = PurePosixPath(path)
    if relative.parent.as_posix() != 'control-plane/control_plane' or relative.suffix != '.py':
        continue
    package_digest.update(relative.name.encode('utf-8'))
    package_digest.update(b'\0')
    package_digest.update(hashlib.sha256(data).digest())
    package_digest.update(b'\0')
def component(prefix):
    digest = hashlib.sha256()
    for record in records:
        if record['path'].startswith(prefix):
            digest.update(record['path'].encode('utf-8'))
            digest.update(b'\0')
            digest.update(record['sha256'].encode('ascii'))
            digest.update(b'\0')
    return digest.hexdigest()
manifest = {
    'schema_version': 1,
    'release_name': release_name,
    'source_revision': identity,
    'control_plane_schema_version': base_manifest['control_plane_schema_version'],
    'package_source_sha256': 'sha256:' + package_digest.hexdigest(),
    'build': {'python': platform.python_version(), 'platform': platform.system().lower()},
    'component_sha256': {name: component(prefix) for name, prefix in {'control_plane':'control-plane/control_plane/', 'deployment':'deploy/', 'documentation':'DEPLOYMENT.md'}.items()},
    'files': records,
}
release_dir.mkdir()
for path, data in payload.items():
    destination = release_dir / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + '\n').encode('utf-8')
(release_dir / 'release-manifest.json').write_bytes(manifest_bytes)
spec = importlib.util.spec_from_file_location('frozen_release_verifier', release_dir / 'deploy/control-plane-verify-release.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)
verification = verifier.verify_release(release_dir)
directories = {release_name}
for path in payload:
    parts = PurePosixPath(path).parts[:-1]
    for count in range(1, len(parts) + 1):
        directories.add(release_name + '/' + PurePosixPath(*parts[:count]).as_posix())
with tarfile.open(archive_output, 'w:gz', compresslevel=9) as archive:
    for directory in sorted(directories):
        info = tarfile.TarInfo(directory)
        info.type = tarfile.DIRTYPE
        info.mode = 0o700
        archive.addfile(info)
    for path, data in sorted({**payload, 'release-manifest.json': manifest_bytes}.items()):
        info = tarfile.TarInfo(release_name + '/' + path)
        info.size = len(data)
        info.mode = modes.get(path, 0o600)
        archive.addfile(info, io.BytesIO(data))
changed = [record['path'] for record in records if record['sha256'] != base_records[record['path']]['sha256']]
assert changed == [changed_path]
assert manifest['component_sha256']['deployment'] == base_manifest['component_sha256']['deployment']
assert manifest['component_sha256']['documentation'] == base_manifest['component_sha256']['documentation']
receipt = {
    'operation': 'immutable_console_one_file_snapshot_preparation',
    'captured_at_utc': datetime.now(timezone.utc).isoformat(),
    'identity_type': 'source_snapshot_sha256',
    'identity_algorithm': 'SHA256(canonical JSON sorted payload records with path,size_bytes,sha256; excludes derived release-manifest.json)',
    'source_revision_is_git_commit': False,
    'base_git_revision': base_revision,
    'base_archive_sha256': archive_sha,
    'frozen_web_ui_sha256': ui_sha,
    'payload_file_count': len(payload),
    'changed_payload_paths': changed,
    'unchanged_payload_file_count': len(payload) - len(changed),
    'release_name': release_name,
    'source_revision': identity,
    'package_source_sha256': manifest['package_source_sha256'],
    'archive_name': archive_output.name,
    'archive_sha256': hashlib.sha256(archive_output.read_bytes()).hexdigest(),
    'manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(),
    'local_verification': verification,
    'python_syntax': 'pass',
    'deployment_performed': False,
    'git_commit_or_push_performed': False,
}
(out / 'snapshot-provenance.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt, sort_keys=True, indent=2))
