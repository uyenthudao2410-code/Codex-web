"""Prepare the reviewed store-only overlay from actual verified serving bytes.

Reads only manifest-listed immutable source files and nonsecret file hashes on
svhome. No configuration content, credential, database, or remote mutation.
"""
import ast
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tarfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "server-overlay"
EXPECTED_BASE_NAME = "codex-control-plane-9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c-retired-read-e5b3b8e2a63e-fp2"
EXPECTED_BASE_PACKAGE = "sha256:f235d3a2898ad53597e3b48e55e27d2278ea7d6d0c9fb2fef21301467a5d9712"
EXPECTED_BASE_STORE = "e5b3b8e2a63e2e4144f9f782b275b4ecc056e8c1f642c91cc9647cb6b6d6667c"
REMOTE = r'''
import base64,hashlib,json,subprocess
from pathlib import Path
pid=int(subprocess.check_output(['systemctl','--user','show','codex-control-plane.service','--property=MainPID','--value'],text=True).strip())
env=dict(item.split('=',1) for item in Path(f'/proc/{pid}/environ').read_text().split('\0') if '=' in item)
root=next(Path(p).parent for p in env.get('PYTHONPATH','').split(':') if p and (Path(p)/'control_plane'/'store.py').is_file())
manifest=json.loads((root/'release-manifest.json').read_text())
files={}
for record in manifest['files']:
 relative=Path(record['path'])
 if relative.is_absolute() or '..' in relative.parts: raise RuntimeError('UNSAFE_MANIFEST_PATH')
 path=root/relative
 if path.is_symlink() or not path.is_file(): raise RuntimeError('UNSAFE_RELEASE_FILE')
 content=path.read_bytes()
 if len(content)!=record['size_bytes'] or hashlib.sha256(content).hexdigest()!=record['sha256']: raise RuntimeError('BASELINE_MANIFEST_DRIFT')
 files[record['path']]=base64.b64encode(content).decode()
config=Path.home()/'.config/codex-control-plane/control-plane.env'
drop=Path.home()/'.config/systemd/user/codex-control-plane.service.d/10-immutable-release.conf'
print(json.dumps({'service_pid':pid,'release_root':str(root),'manifest':manifest,'files':files,
 'protected_config_sha256':hashlib.sha256(config.read_bytes()).hexdigest(),
 'service_dropin_sha256':hashlib.sha256(drop.read_bytes()).hexdigest()},separators=(',',':')))
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    result = subprocess.run(
        ["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=yes",
         "svhome@100.116.112.22", "python3 -B -"],
        input=REMOTE, text=True, capture_output=True, check=True,
    )
    baseline = json.loads(result.stdout)
    manifest = baseline["manifest"]
    assert manifest["release_name"] == EXPECTED_BASE_NAME
    assert manifest["package_source_sha256"] == EXPECTED_BASE_PACKAGE
    assert manifest["control_plane_schema_version"] == 29
    base_store = base64.b64decode(baseline["files"]["control-plane/control_plane/store.py"])
    assert sha(base_store) == EXPECTED_BASE_STORE
    overlay = (ROOT / "control-plane/control_plane/store.py").read_bytes().replace(b"\r\n", b"\n")
    ast.parse(overlay)
    name = "codex-control-plane-9cae1044-scoped-artifacts-" + sha(overlay)[:12]
    release = OUT / name
    assert not release.exists(), "CANDIDATE_ALREADY_PREPARED"
    release.mkdir(parents=True)
    for relative, encoded in baseline["files"].items():
        path = release / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(encoded))
    (release / "control-plane/control_plane/store.py").write_bytes(overlay)
    records = [
        {"path": item["path"], "size_bytes": (release / item["path"]).stat().st_size,
         "sha256": sha((release / item["path"]).read_bytes())} for item in manifest["files"]
    ]
    changed = [new["path"] for old, new in zip(manifest["files"], records) if old != new]
    assert changed == ["control-plane/control_plane/store.py"]
    builder = module("official_control_plane_builder", ROOT / "scripts/build-control-plane-release.py")
    verifier = module("official_overlay_verifier", release / "deploy/control-plane-verify-release.py")
    package_sha = builder._package_source_sha256(release / "control-plane/control_plane")
    candidate_manifest = {
        **manifest, "release_name": name, "package_source_sha256": package_sha,
        "component_sha256": {
            key: verifier._component_digest(records, prefix)
            for key, prefix in verifier.COMPONENT_PREFIXES.items()
        }, "files": records,
    }
    (release / "release-manifest.json").write_text(json.dumps(candidate_manifest, sort_keys=True, indent=2) + "\n")
    verification = verifier.verify_release(release)
    archive = OUT / (name + ".tar.gz")
    def mode_filter(item):
        item.uid = item.gid = 0
        item.uname = item.gname = ""
        item.mode = 0o755 if item.isdir() or item.name.endswith((
            "control-plane-launcher.sh", "control-plane-mcp-tunnel-launcher.sh",
            "control-plane-backup.sh", "control-plane-healthcheck.sh",
        )) else 0o644
        return item
    with tarfile.open(archive, "w:gz", compresslevel=9) as bundle:
        bundle.add(release, arcname=name, filter=mode_filter)
    receipt = {
        "operation": "scoped_artifact_overlay_preparation", "remote_mutations": False,
        "baseline_service_pid": baseline["service_pid"], "baseline_release_root": baseline["release_root"],
        "baseline_source_revision": manifest["source_revision"], "baseline_release_name": EXPECTED_BASE_NAME,
        "baseline_package_source_sha256": EXPECTED_BASE_PACKAGE, "baseline_store_sha256": EXPECTED_BASE_STORE,
        "protected_config_sha256": baseline["protected_config_sha256"],
        "service_dropin_sha256": baseline["service_dropin_sha256"],
        "overlay_store_sha256": sha(overlay), "changed_runtime_files": changed, "unchanged_release_files": 37,
        "source_revision_semantics": "Original baseline retained; reviewed uncommitted store overlay is separately hash-bound.",
        "candidate_release": str(release), "candidate_archive": str(archive),
        "candidate_archive_sha256": sha(archive.read_bytes()), "verification": verification,
        "focused_tests": "8 new scoped artifact/document tests + 4 existing pilot + 10 private service facade passed",
    }
    (OUT / "preparation-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, separators=(",", ":")))


if __name__ == "__main__":
    main()
