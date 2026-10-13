"""Prepare a secret-free artifact from the exact serving immutable release.

Only manifest-listed verified release files are fetched. No configuration,
credentials or database is copied and no remote mutation is performed.
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

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "server-pilot-continuity"
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
print(json.dumps({'service_pid':pid,'release_root':str(root),'manifest':manifest,'files':files},separators=(',',':')))
'''


def sha(content):
    return hashlib.sha256(content).hexdigest()


def component(records, prefix):
    digest = hashlib.sha256()
    for record in records:
        if record["path"].startswith(prefix):
            digest.update(record["path"].encode())
            digest.update(b"\0")
            digest.update(record["sha256"].encode("ascii"))
            digest.update(b"\0")
    return digest.hexdigest()


def main():
    result = subprocess.run([
        "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=yes",
        "svhome@100.116.112.22", "python3 -",
    ], input=REMOTE, text=True, capture_output=True, check=True)
    baseline = json.loads(result.stdout)
    manifest = baseline["manifest"]
    base_store = base64.b64decode(baseline["files"]["control-plane/control_plane/store.py"])
    head_store = subprocess.check_output(["git", "show", "HEAD:control-plane/control_plane/store.py"], cwd=ROOT)
    if base_store != head_store:
        raise RuntimeError("SERVING_STORE_NOT_EXACT_HEAD_BASELINE")
    overlay = (ROOT / "control-plane/control_plane/store.py").read_bytes().replace(b"\r\n", b"\n")
    ast.parse(overlay)
    overlay_sha = sha(overlay)
    name = manifest["release_name"] + "-retired-read-" + overlay_sha[:12]
    release = OUT / name
    if release.exists():
        expected = set(baseline["files"]) | {"release-manifest.json"}
        if {path.relative_to(release).as_posix() for path in release.rglob("*") if path.is_file()} != expected:
            raise RuntimeError("CANDIDATE_EXISTING_FILE_SET_DRIFT")
    release.mkdir(parents=True, exist_ok=True)
    for relative, encoded in baseline["files"].items():
        path = release / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(encoded))
    (release / "control-plane/control_plane/store.py").write_bytes(overlay)
    records = []
    for record in manifest["files"]:
        content = (release / record["path"]).read_bytes()
        records.append({"path": record["path"], "size_bytes": len(content), "sha256": sha(content)})
    changed = [record["path"] for before, record in zip(manifest["files"], records) if before != record]
    if changed != ["control-plane/control_plane/store.py"]:
        raise RuntimeError("OVERLAY_CHANGED_UNEXPECTED_FILE")
    package = release / "control-plane/control_plane"
    digest = hashlib.sha256()
    for path in sorted(package.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        digest.update(b"\0")
    candidate_manifest = {
        **manifest, "release_name": name, "package_source_sha256": "sha256:" + digest.hexdigest(),
        "component_sha256": {"control_plane": component(records, "control-plane/control_plane/"),
                             "deployment": component(records, "deploy/"),
                             "documentation": component(records, "DEPLOYMENT.md")},
        "files": records,
    }
    (release / "release-manifest.json").write_text(json.dumps(candidate_manifest, sort_keys=True, indent=2) + "\n")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("overlay_release_verifier", release / "deploy/control-plane-verify-release.py")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    verification = verifier.verify_release(release)
    archive = OUT / (name + ".tar.gz")
    with tarfile.open(archive, "w:gz", compresslevel=9) as bundle:
        def mode_filter(item):
            item.uid = item.gid = 0
            item.uname = item.gname = ""
            item.mode = 0o755 if item.isdir() or item.name.endswith(("control-plane-launcher.sh", "control-plane-mcp-tunnel-launcher.sh", "control-plane-backup.sh", "control-plane-healthcheck.sh")) else 0o644
            return item
        bundle.add(release, arcname=name, filter=mode_filter)
    receipt = {
        "operation": "retired_read_pilot_overlay_preparation", "remote_mutations": False,
        "baseline_service_pid": baseline["service_pid"], "baseline_release_root": baseline["release_root"],
        "baseline_source_revision": manifest["source_revision"],
        "baseline_package_source_sha256": manifest["package_source_sha256"],
        "baseline_store_sha256": sha(base_store), "overlay_store_sha256": overlay_sha,
        "overlay_git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "changed_runtime_files": changed, "unchanged_release_files": len(records) - len(changed),
        "manifest_source_revision_semantics": "Original serving baseline; reviewed uncommitted store overlay is bound separately by overlay_store_sha256, not claimed as a Git release.",
        "candidate_release": str(release), "candidate_archive": str(archive),
        "candidate_archive_sha256": sha(archive.read_bytes()), "verification": verification,
    }
    (OUT / "overlay-preparation-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, separators=(",", ":")))


if __name__ == "__main__":
    main()
