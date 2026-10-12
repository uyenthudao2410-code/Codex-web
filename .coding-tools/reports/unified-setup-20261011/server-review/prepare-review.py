"""Freeze the one-file Console delta locally; performs no deployment."""

from __future__ import annotations

from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BASE_REVISION = "beaa9d5ade4926ef231e3ec9d0a517fe93830e90"
ARCHIVE = ROOT / ".coding-tools/reports/mcp-web-contract-20261011" / f"codex-control-plane-{BASE_REVISION}.tar.gz"
ARCHIVE_SHA256 = "e31132a545da55cad564a373c138bb644917c8cbce73e87b724c88dfee6f3b36"
RELEASE_ROOT = f"codex-control-plane-{BASE_REVISION}"
RELATIVE_SOURCE = "control-plane/control_plane/web_ui.py"
SOURCE = ROOT / RELATIVE_SOURCE


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_frozen(name: str, data: bytes) -> None:
    target = OUT / name
    if target.exists():
        if target.read_bytes() != data:
            raise SystemExit(f"Refusing to overwrite frozen artifact: {name}")
        return
    with target.open("xb") as stream:
        stream.write(data)


archive_bytes = ARCHIVE.read_bytes()
assert sha256(archive_bytes) == ARCHIVE_SHA256, "base archive digest mismatch"
with tarfile.open(ARCHIVE, "r:gz") as archive:
    members = archive.getmembers()
    for member in members:
        name = PurePosixPath(member.name)
        assert not name.is_absolute() and ".." not in name.parts and "\\" not in member.name
        assert name.parts and name.parts[0] == RELEASE_ROOT
        assert member.isfile() or member.isdir(), "archive has a non-regular member"
    base_members = [member for member in members if member.name == f"{RELEASE_ROOT}/{RELATIVE_SOURCE}"]
    assert len(base_members) == 1 and base_members[0].isfile()
    base_file = archive.extractfile(base_members[0])
    assert base_file is not None
    base = base_file.read()
    manifest_stream = archive.extractfile(f"{RELEASE_ROOT}/release-manifest.json")
    assert manifest_stream is not None
    manifest = json.load(manifest_stream)

current = SOURCE.read_bytes()
assert SOURCE.read_bytes() == current, "source changed while freezing"
base_hash = sha256(base)
current_hash = sha256(current)
assert manifest.get("source_revision") == BASE_REVISION
base_manifest_entries = [entry for entry in manifest.get("files", []) if entry.get("path") == RELATIVE_SOURCE]
assert len(base_manifest_entries) == 1 and base_manifest_entries[0].get("sha256") == base_hash
base_name = f"web_ui.base-{base_hash}.py"
current_name = f"web_ui.current-{current_hash}.py"
exact_patch = "".join(difflib.unified_diff(
    base.decode("utf-8").splitlines(keepends=True),
    current.decode("utf-8").splitlines(keepends=True),
    fromfile=f"a/{RELATIVE_SOURCE}", tofile=f"b/{RELATIVE_SOURCE}",
)).encode("utf-8")
base_lf = base.replace(b"\r\n", b"\n")
current_lf = current.replace(b"\r\n", b"\n")
review_patch = "".join(difflib.unified_diff(
    base_lf.decode("utf-8").splitlines(keepends=True),
    current_lf.decode("utf-8").splitlines(keepends=True),
    fromfile=f"a/{RELATIVE_SOURCE}", tofile=f"b/{RELATIVE_SOURCE}",
)).encode("utf-8")

# Check and replay in a throwaway directory; never apply to the repository or
# a release checkout. Exact bytes, including the existing Windows newlines,
# must reproduce the frozen source snapshot.
with tempfile.TemporaryDirectory(prefix="console-review-") as temporary:
    temp_root = Path(temporary)
    temp_source = temp_root / RELATIVE_SOURCE
    temp_source.parent.mkdir(parents=True)
    temp_source.write_bytes(base)
    temp_patch = temp_root / "exact.patch"
    temp_patch.write_bytes(exact_patch)
    for arguments in (["--check"], []):
        result = subprocess.run(
            ["git", "-c", "core.autocrlf=false", "apply", "--whitespace=nowarn", *arguments, str(temp_patch)],
            cwd=temp_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        assert result.returncode == 0, "exact patch check/replay failed"
    assert temp_source.read_bytes() == current, "exact patch replay byte mismatch"
    temp_source.write_bytes(base_lf)
    temp_patch.write_bytes(review_patch)
    result = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "apply", "--whitespace=nowarn", str(temp_patch)],
        cwd=temp_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert result.returncode == 0 and temp_source.read_bytes() == current_lf, "LF review patch replay failed"

OUT.mkdir(parents=True, exist_ok=True)
write_frozen(base_name, base)
write_frozen(current_name, current)
write_frozen("web_ui.exact.patch", exact_patch)
write_frozen("web_ui.review-lf.patch", review_patch)
previous_receipt = json.loads((OUT / "receipt.json").read_text("utf-8")) if (OUT / "receipt.json").exists() else None
receipt = {
    "operation": "local_console_one_file_review_preparation",
    "captured_at_utc": previous_receipt["captured_at_utc"] if previous_receipt else datetime.now(timezone.utc).isoformat(),
    "git_head_observed": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "base": {
        "archive": str(ARCHIVE.relative_to(ROOT)).replace("\\", "/"),
        "archive_sha256": ARCHIVE_SHA256,
        "archive_members_safely_inspected": len(members),
        "archive_file_member": f"{RELEASE_ROOT}/{RELATIVE_SOURCE}",
        "source_revision_as_declared_by_base_manifest": BASE_REVISION,
        "package_source_sha256_as_declared_by_base_manifest": manifest.get("package_source_sha256"),
        "frozen_file": base_name, "sha256": base_hash, "bytes": len(base), "crlf_count": base.count(b"\r\n"),
    },
    "candidate_delta": {
        "scope": [RELATIVE_SOURCE], "frozen_file": current_name,
        "sha256": current_hash, "bytes": len(current), "crlf_count": current.count(b"\r\n"),
        "new_git_revision": None, "full_release_built": False,
        "source_current_at_capture": SOURCE.read_bytes() == current,
    },
    "patches": {
        "exact": {"file": "web_ui.exact.patch", "sha256": sha256(exact_patch), "replay_byte_sha256": current_hash, "check_and_replay": "pass"},
        "review_lf": {"file": "web_ui.review-lf.patch", "sha256": sha256(review_patch), "replay_lf_sha256": sha256(current_lf), "replay": "pass", "normalization": "CRLF to LF for compact textual review only"},
    },
    "target_for_next_approved_rollout": {
        "ssh": "svhome@100.116.112.22", "service": "codex-control-plane.service", "service_manager": "systemd user",
        "expected_base_release_to_reverify": RELEASE_ROOT,
        "expected_release_location_to_reverify": f"/home/svhome/.local/lib/codex-control-plane/releases/{RELEASE_ROOT}",
    },
    "deployment_performed": False, "service_operations_performed": False,
    "authority_mutations_performed": False, "commit_or_push_performed": False,
    "remaining_gate": "Owner-approved rollout; fresh target/baseline/quiescence check; a real new immutable release identity and regenerated manifest/package validation before any service switch.",
}
write_frozen("receipt.json", (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
print(json.dumps({"base_sha256": base_hash, "current_sha256": current_hash, "exact_patch_replay": "pass", "review_patch_replay": "pass", "deployment_performed": False}))
