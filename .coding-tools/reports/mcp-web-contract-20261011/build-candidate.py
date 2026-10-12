"""Prepare one immutable Control Plane candidate after the parent freezes source.

Without --source-frozen, only verify the previously deployed artifact and print
the preparation plan. No remote connection, installation, authority mutation,
primary commit, service operation or publication is performed by this script.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent
PREVIOUS = ROOT / ".coding-tools/reports/folder-permissions-20261011/server-acceptance-fix"
BASE = "70de202d93c9a759befe5d38491ce54e9ef4b3cd"
BASE_PACKAGE = "sha256:fd5132676f1a68e875348fe790c6803c591f65a73311d793194c20a4e70b7d81"
PRIMARY_HEAD = "2c554f59cb7b8ffc86ce5e0e28076c792777642f"
BRANCH = "codex/mcp-web-client-feedback"
SOURCE_FILES = (
    "control-plane/control_plane/mcp_facade.py",
    "control-plane/control_plane/node_agent.py",
    "control-plane/control_plane/mcp_status.py",
    "control-plane/tests/test_mcp_client_feedback.py",
    "control-plane/tests/test_mcp_status.py",
    "control-plane/tests/test_artifact_node_agent.py",
    "control-plane/tests/test_mcp_status_facade.py",
    "control-plane/tests/test_mcp_artifact_relay.py",
    "control-plane/tests/test_mcp_file_read_facade.py",
    "control-plane/tests/test_file_read_node_agent.py",
    "control-plane/tests/test_mcp_exec.py",
    "control-plane/tests/test_mcp_permission_requests.py",
    "control-plane/tests/test_mcp_task_sessions.py",
    "control-plane/tests/test_mcp_private_tunnel_service_facade.py",
    "control-plane/tests/test_mcp_oauth.py",
    "control-plane/tests/test_mcp_exec_http_node_e2e.py",
)
ALLOWED_RELEASE_CHANGES = frozenset({
    "DEPLOYMENT.md", *SOURCE_FILES[:3],
})
UNCHANGED_TOOLS = (
    "scripts/build-control-plane-release.py",
    "deploy/control-plane-verify-release.py",
)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(target: Path) -> str:
    if target.is_symlink() or not target.is_file():
        raise RuntimeError("expected a regular artifact input")
    digest = hashlib.sha256()
    with target.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_bytes(target: Path) -> bytes:
    if target.is_symlink() or not target.is_file():
        raise RuntimeError("expected a regular source input")
    return target.read_bytes().replace(b"\r\n", b"\n")


def git(*arguments: str, cwd: Path = ROOT) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(cwd), *arguments], check=False,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise RuntimeError("local Git inspection failed")
    return result.stdout


def primary_identity() -> dict:
    return {
        "head": git("rev-parse", "HEAD").decode("ascii").strip(),
        "branch": git("branch", "--show-current").decode("utf-8").strip(),
        "index_entries_sha256": sha256(git("ls-files", "--stage", "-z")),
        "staged_diff_sha256": sha256(git("diff", "--cached", "--binary")),
    }


def write_new(target: Path, content: bytes) -> None:
    with target.open("xb") as stream:
        stream.write(content)


def write_json(target: Path, value: dict) -> None:
    write_new(target, (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8"))


def run(arguments: list[str], *, cwd: Path, log: str, timeout: int = 300) -> bytes:
    """Run only known local tooling; keep command arguments and secrets out of logs."""
    result = subprocess.run(
        arguments, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=timeout, check=False,
    )
    write_new(OUTPUT / log, result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"local preparation step failed: {log}; exit={result.returncode}")
    return result.stdout


def inspect_baseline() -> tuple[Path, dict, dict]:
    receipt = json.loads((PREVIOUS / "artifact-receipt.json").read_text(encoding="utf-8"))
    source = Path(receipt["isolated_source_directory"]).resolve(strict=True)
    dist = (ROOT / "dist").resolve(strict=True)
    if not dist.is_relative_to(ROOT.resolve()) or not source.is_relative_to(dist) or source.is_symlink():
        raise RuntimeError("previous source checkout is outside dist")
    if receipt["source_revision"] != BASE or receipt["package_source_sha256"] != BASE_PACKAGE:
        raise RuntimeError("previous artifact receipt is not the deployed baseline")
    if git("rev-parse", "HEAD", cwd=source).decode("ascii").strip() != BASE:
        raise RuntimeError("previous source checkout no longer has the exact baseline HEAD")
    if git("branch", "--show-current", cwd=source).decode("utf-8").strip() != receipt["isolated_branch"]:
        raise RuntimeError("previous source branch changed")
    manifest_path = PREVIOUS / "candidate-release-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    archive = Path(receipt["review_archive"]).resolve(strict=True)
    if not archive.is_relative_to(PREVIOUS.resolve()) or file_sha256(archive) != receipt["review_archive_sha256"]:
        raise RuntimeError("previous review archive does not match its immutable receipt")
    if manifest["source_revision"] != BASE or manifest["package_source_sha256"] != BASE_PACKAGE:
        raise RuntimeError("previous manifest has a different identity")
    with tarfile.open(archive, "r:gz") as package:
        stream = package.extractfile(f"codex-control-plane-{BASE}/release-manifest.json")
        if stream is None or json.loads(stream.read()) != manifest:
            raise RuntimeError("previous manifest differs from the verified archive")
    for record in manifest["files"]:
        relative = record["path"]
        if relative == "DEPLOYMENT.md":
            continue
        selected = git("show", f"{BASE}:{relative}", cwd=source)
        if relative.endswith(".sh"):
            selected = selected.replace(b"\r\n", b"\n")
        if sha256(selected) != record["sha256"] or len(selected) != record["size_bytes"]:
            raise RuntimeError("baseline Git source differs from the deployed manifest")
    for relative in UNCHANGED_TOOLS:
        if canonical_bytes(ROOT / relative) != git("show", f"{BASE}:{relative}", cwd=source):
            raise RuntimeError("strict builder or verifier changed")
    return source, receipt, manifest


def build_candidate() -> dict:
    before = primary_identity()
    if before["head"] != PRIMARY_HEAD or before["branch"] != "main":
        raise RuntimeError("primary repository identity differs from the authorized checkout")
    previous_source, previous_receipt, previous_manifest = inspect_baseline()
    if (OUTPUT / "artifact-receipt.json").exists():
        raise RuntimeError("candidate receipt already exists; do not overwrite or repeat the build")
    source_bytes = {relative: canonical_bytes(ROOT / relative) for relative in SOURCE_FILES}
    input_records = [
        {"path": relative, "sha256": sha256(content), "size_bytes": len(content)}
        for relative, content in source_bytes.items()
    ]
    input_sha = sha256(json.dumps(input_records, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    write_json(OUTPUT / "frozen-source-inputs.json", {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": input_records,
        "source_inputs_sha256": input_sha,
        "primary_identity": before,
        "baseline_revision": BASE,
    })
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    isolated_parent = (ROOT / "dist" / f"control-plane-mcp-web-client-feedback-{stamp}").resolve()
    if not isolated_parent.is_relative_to((ROOT / "dist").resolve()) or isolated_parent.exists():
        raise RuntimeError("new isolated source destination is unsafe or already exists")
    isolated_parent.mkdir()
    isolated = isolated_parent / "source"
    release_output = isolated_parent / "release"
    release_output.mkdir()
    run([
        "git", "clone", "--no-checkout", "--no-hardlinks", "--dissociate",
        "--no-tags", "--single-branch", "--branch", previous_receipt["isolated_branch"],
        "--config", "core.longpaths=true", str(previous_source), str(isolated),
    ], cwd=ROOT, log="isolated-clone.log", timeout=600)
    alternates = isolated / ".git/objects/info/alternates"
    if alternates.is_file() and alternates.read_bytes().strip():
        raise RuntimeError("new clone still borrows mutable object storage")
    if git("rev-parse", "HEAD", cwd=isolated).decode("ascii").strip() != BASE:
        raise RuntimeError("new clone lost exact deployed base provenance")
    run(["git", "checkout", "-b", BRANCH, BASE], cwd=isolated, log="isolated-checkout.log")
    for relative, selected in source_bytes.items():
        target = isolated / relative
        if target.is_symlink():
            raise RuntimeError("isolated source target is a symlink")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(selected)
    for relative, selected in source_bytes.items():
        if canonical_bytes(ROOT / relative) != selected:
            raise RuntimeError("primary frozen source changed during isolated copy")
    run(["git", "add", "--", *SOURCE_FILES], cwd=isolated, log="isolated-source-stage.log")
    npm = "npm.cmd" if os.name == "nt" else "npm"
    run([npm, "run", "stage:coding-tools-delivery"], cwd=isolated, log="isolated-delivery-stage.log")
    run([npm, "run", "check:coding-tools-delivery"], cwd=isolated, log="isolated-delivery-check.log")
    staged_files = git("diff", "--cached", "--name-only", cwd=isolated).decode("utf-8").splitlines()
    if any(relative not in SOURCE_FILES and not relative.startswith(".coding-tools/") for relative in staged_files):
        raise RuntimeError("isolated commit contains an unrelated source change")
    run([
        "git", "-c", "user.name=Codex", "-c", "user.email=codex@local.invalid",
        "-c", "commit.gpgsign=false", "commit", "-m",
        "fix(control-plane): clarify MCP client errors and operation readiness",
    ], cwd=isolated, log="isolated-commit.log")
    revision = git("rev-parse", "HEAD", cwd=isolated).decode("ascii").strip()
    if git("rev-parse", "HEAD^", cwd=isolated).decode("ascii").strip() != BASE:
        raise RuntimeError("isolated commit is not an exact child of the deployed revision")
    for relative, selected in source_bytes.items():
        if git("show", f"HEAD:{relative}", cwd=isolated) != selected:
            raise RuntimeError("isolated committed source differs from the frozen tested source")
    isolated_status = git("status", "--porcelain=v1", "--untracked-files=all", cwd=isolated).decode("utf-8").splitlines()
    if any(not record[3:].startswith(".coding-tools/") for record in isolated_status):
        raise RuntimeError("isolated source is not clean after commit")
    build = json.loads(run([
        sys.executable, "-B", str(isolated / UNCHANGED_TOOLS[0]),
        "--source-root", str(isolated), "--source-revision", revision,
        "--output-dir", str(release_output),
    ], cwd=isolated, log="build-receipt.json"))
    release = Path(build["release_directory"])
    verification = json.loads(run([
        sys.executable, "-B", str(release / UNCHANGED_TOOLS[1]),
        "--release-dir", str(release),
    ], cwd=isolated, log="artifact-verification.json"))
    manifest_bytes = (release / "release-manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    old_files = {record["path"]: record for record in previous_manifest["files"]}
    new_files = {record["path"]: record for record in manifest["files"]}
    changes = [
        {"path": relative, "deployed": old_files.get(relative), "candidate": new_files.get(relative)}
        for relative in sorted(old_files.keys() | new_files.keys())
        if old_files.get(relative) != new_files.get(relative)
    ]
    if not {record["path"] for record in changes}.issubset(ALLOWED_RELEASE_CHANGES):
        raise RuntimeError("candidate contains an unrelated runtime or deployment delta")
    if not set(SOURCE_FILES[:3]).issubset({record["path"] for record in changes}):
        raise RuntimeError("candidate is missing an expected runtime delta")
    if set(old_files) - set(new_files) or set(new_files) - set(old_files) != {SOURCE_FILES[2]}:
        raise RuntimeError("candidate changed the release file set beyond the new status module")
    if manifest["control_plane_schema_version"] != previous_manifest["control_plane_schema_version"]:
        raise RuntimeError("candidate unexpectedly changes the database schema")
    for relative, selected in source_bytes.items():
        if canonical_bytes(ROOT / relative) != selected:
            raise RuntimeError("primary frozen source changed after candidate build")
    if primary_identity() != before:
        raise RuntimeError("primary HEAD, branch or index changed during isolated preparation")
    review_archive = OUTPUT / Path(build["archive"]).name
    with Path(build["archive"]).open("rb") as source, review_archive.open("xb") as destination:
        shutil.copyfileobj(source, destination)
    if file_sha256(review_archive) != build["archive_sha256"]:
        raise RuntimeError("review archive differs from the strict builder output")
    write_new(OUTPUT / "candidate-release-manifest.json", manifest_bytes)
    result = {
        "operation": "isolated_mcp_web_client_feedback_release_preparation",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_revision": BASE,
        "base_package_source_sha256": BASE_PACKAGE,
        "source_revision": revision,
        "source_inputs_sha256": input_sha,
        "source_inputs": input_records,
        "source_snapshot_matches_primary_after_build": True,
        "isolated_source_directory": str(isolated),
        "isolated_branch": BRANCH,
        "isolated_release_source_clean": True,
        "isolated_runtime_evidence_status": isolated_status,
        "primary_identity": before,
        "main_head_and_index_preserved": True,
        "commit_changed_files": staged_files,
        "source_changes": list(SOURCE_FILES),
        "full_release_file_changes": changes,
        "runtime_and_deploy_file_changes": [record for record in changes if record["path"] != "DEPLOYMENT.md"],
        "unchanged_release_file_count": sum(old_files.get(relative) == record for relative, record in new_files.items()),
        "archive": build["archive"],
        "archive_sha256": build["archive_sha256"],
        "review_archive": str(review_archive),
        "review_archive_sha256": file_sha256(review_archive),
        "release_directory": str(release),
        "review_manifest": str(OUTPUT / "candidate-release-manifest.json"),
        "package_source_sha256": build["package_source_sha256"],
        "artifact_verification": verification,
        "validation_scope": "unchanged strict clean-source builder and release verifier; focused behavioral proofs owned by parent",
        "remote_mutations": False,
        "deployment_performed": False,
        "service_operations": False,
        "push_or_public_release": False,
        "deploy_ready_for_operator_review": True,
    }
    write_json(OUTPUT / "artifact-receipt.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-frozen", action="store_true", help="parent has frozen the exact passed source; permits isolated copy/commit/build only")
    arguments = parser.parse_args()
    if not arguments.source_frozen:
        source, _receipt, manifest = inspect_baseline()
        print(json.dumps({
            "operation": "mcp_web_candidate_preparation_plan",
            "baseline_revision": BASE,
            "baseline_package_source_sha256": BASE_PACKAGE,
            "baseline_source_directory": str(source),
            "baseline_file_count": len(manifest["files"]),
            "allowed_source_inputs": list(SOURCE_FILES),
            "missing_source_inputs": [relative for relative in SOURCE_FILES if not (ROOT / relative).is_file()],
            "awaiting_parent_source_frozen": True,
            "remote_mutations": False,
        }, sort_keys=True))
        return 0
    result = build_candidate()
    print(json.dumps({key: result[key] for key in (
        "source_revision", "base_revision", "archive_sha256", "package_source_sha256",
        "review_archive", "runtime_and_deploy_file_changes", "unchanged_release_file_count",
        "main_head_and_index_preserved", "deployment_performed",
    )}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(json.dumps({"error": {"code": "MCP_WEB_CANDIDATE_PREPARATION_FAILED", "message": str(error)}}), file=sys.stderr)
        raise SystemExit(2)
    except (OSError, subprocess.SubprocessError, ValueError, tarfile.TarError):
        print(json.dumps({"error": {"code": "MCP_WEB_CANDIDATE_PREPARATION_FAILED"}}), file=sys.stderr)
        raise SystemExit(2)
