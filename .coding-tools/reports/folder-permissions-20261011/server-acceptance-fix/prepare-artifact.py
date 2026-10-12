"""Prepare code-only acceptance-fix evidence; never mutate a remote service."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[4]
OUTPUT = Path(__file__).resolve().parent
STORE = "control-plane/control_plane/store.py"


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_bytes(*arguments: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *arguments])


def capture_deployed_code() -> dict:
    remote_program = r'''
import base64, hashlib, json
from pathlib import Path
current = Path("/home/svhome/.local/lib/codex-control-plane/current")
release = current.resolve(strict=True)
release_parent = Path("/home/svhome/.local/lib/codex-control-plane/releases").resolve()
if not release.is_dir() or not release.is_relative_to(release_parent):
    raise RuntimeError("current target is outside release directory")
manifest_path = release / "release-manifest.json"
manifest_bytes = manifest_path.read_bytes()
manifest = json.loads(manifest_bytes)
store_path = release / "control-plane/control_plane/store.py"
if store_path.is_symlink() or not store_path.is_file():
    raise RuntimeError("deployed store source is unsafe")
store_bytes = store_path.read_bytes()
observed = []
for record in manifest["files"]:
    relative = Path(record["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError("release manifest path is unsafe")
    target = release / relative
    if target.is_symlink() or not target.is_file() or not target.resolve().is_relative_to(release):
        raise RuntimeError("release manifest target is unsafe")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    observed.append({"path": relative.as_posix(), "sha256": digest,
                     "size_bytes": target.stat().st_size,
                     "matches_manifest": digest == record["sha256"] and target.stat().st_size == record["size_bytes"]})
print(json.dumps({"release_directory": str(release),
                  "manifest_base64": base64.b64encode(manifest_bytes).decode("ascii"),
                  "store_base64": base64.b64encode(store_bytes).decode("ascii"),
                  "observed_files": observed}, separators=(",", ":")))
'''
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "svhome@100.116.112.22", "python3", "-"],
        input=remote_program.encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True,
    )
    response = json.loads(result.stdout)
    manifest_bytes = base64.b64decode(response.pop("manifest_base64"), validate=True)
    store_bytes = base64.b64decode(response.pop("store_base64"), validate=True)
    manifest = json.loads(manifest_bytes)
    (OUTPUT / "deployed-release-manifest.json").write_bytes(manifest_bytes)
    (OUTPUT / "deployed-store.py").write_bytes(store_bytes)
    head = git_bytes("rev-parse", "HEAD").decode("ascii").strip()
    base = git_bytes("show", f"{head}:{STORE}")
    fixed = (ROOT / STORE).read_bytes().replace(b"\r\n", b"\n")
    (OUTPUT / "base-store.py").write_bytes(base)
    (OUTPUT / "fixed-store.py").write_bytes(fixed)
    patch = git_bytes("diff", "--no-ext-diff", "--binary", "--", STORE)
    (OUTPUT / "owner-standing-acceptance.patch").write_bytes(patch)
    release_source_comparison = []
    for record in manifest["files"]:
        relative = record["path"]
        if relative == "DEPLOYMENT.md":
            continue
        source_bytes = git_bytes("show", f"{head}:{relative}")
        if relative.endswith(".sh"):
            source_bytes = source_bytes.replace(b"\r\n", b"\n")
        release_source_comparison.append({"path": relative, "head_sha256": sha256(source_bytes),
                                          "matches_deployed_manifest": sha256(source_bytes) == record["sha256"]})
    receipt = {
        "operation": "owner_standing_patch_acceptance_artifact_preflight",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository_root": str(ROOT),
        "repository_head": head,
        "repository_branch": git_bytes("branch", "--show-current").decode("utf-8").strip(),
        "fix_patch_sha256": sha256(patch),
        "base_store_sha256": sha256(base),
        "fixed_store_sha256": sha256(fixed),
        "deployed_store_sha256": sha256(store_bytes),
        "deployed_store_matches_head": store_bytes == base,
        "deployed_manifest_sha256": sha256(manifest_bytes),
        "deployed_source_revision": manifest["source_revision"],
        "deployed_package_source_sha256": manifest["package_source_sha256"],
        "deployed_release_directory": response["release_directory"],
        "all_deployed_files_match_manifest": all(record["matches_manifest"] for record in response["observed_files"]),
        "deployed_file_observations": response["observed_files"],
        "head_to_deployed_manifest_comparison": release_source_comparison,
        "remote_mutations": False,
    }
    (OUTPUT / "preflight.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    receipt = capture_deployed_code()
    print(json.dumps({key: receipt[key] for key in (
        "repository_head", "deployed_source_revision", "deployed_store_matches_head", "all_deployed_files_match_manifest",
        "base_store_sha256", "fixed_store_sha256", "deployed_store_sha256",
    )}, sort_keys=True))
