"""Build the exact acceptance fix in an isolated, guarded Git checkout."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[4]
OUTPUT = Path(__file__).resolve().parent
SOURCE_FILES = (
    "control-plane/control_plane/store.py",
    "control-plane/tests/test_mcp_task_sessions.py",
)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def run(arguments: list[str], *, cwd: Path, log: str, timeout: int = 240) -> bytes:
    result = subprocess.run(arguments, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    (OUTPUT / log).write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"preparation step failed: {log}, exit={result.returncode}")
    return result.stdout


def git(*arguments: str, cwd: Path = ROOT) -> bytes:
    return subprocess.check_output(["git", "-C", str(cwd), *arguments])


def main() -> None:
    preflight = json.loads((OUTPUT / "preflight.json").read_text(encoding="utf-8"))
    base_revision = preflight["repository_head"]
    if git("rev-parse", "HEAD").decode().strip() != base_revision:
        raise RuntimeError("main HEAD changed since preflight")
    if not preflight["deployed_store_matches_head"] or not preflight["all_deployed_files_match_manifest"]:
        raise RuntimeError("deployed baseline does not match verified preflight")
    if not all(record["matches_deployed_manifest"] for record in preflight["head_to_deployed_manifest_comparison"]):
        raise RuntimeError("HEAD would change other deployed release inputs")
    main_index_hash = sha256(git("diff", "--cached", "--binary"))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    isolated_parent = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "dist" / f"control-plane-owner-standing-acceptance-{stamp}"
    if not isolated_parent.is_relative_to((ROOT / "dist").resolve()):
        raise RuntimeError("isolated preparation must stay under repository dist")
    isolated_parent.mkdir(parents=True, exist_ok=len(sys.argv) > 1)
    isolated = isolated_parent / "source"
    release_output = isolated_parent / "release"
    release_output.mkdir(exist_ok=len(sys.argv) > 1)
    if not isolated.exists():
        run(["git", "clone", "--shared", "--no-checkout", "--no-tags", "--single-branch", "--branch", "main", str(ROOT), str(isolated)],
            cwd=ROOT, log="isolated-clone.log")
    current_revision = git("rev-parse", "HEAD", cwd=isolated).decode().strip()
    if current_revision == base_revision:
        run(["git", "config", "core.longpaths", "true"], cwd=isolated, log="isolated-longpaths.log")
        run(["git", "checkout", "-b", "codex/owner-standing-acceptance", base_revision], cwd=isolated, log="isolated-checkout.log")
        for relative in SOURCE_FILES:
            selected = (ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            if relative.endswith("store.py") and sha256(selected) != preflight["fixed_store_sha256"]:
                raise RuntimeError("fixed store source drifted")
            (isolated / relative).write_bytes(selected)
        run(["git", "add", "--", *SOURCE_FILES], cwd=isolated, log="isolated-source-stage.log")
        run(["npm.cmd", "run", "stage:coding-tools-delivery"], cwd=isolated, log="isolated-delivery-stage.log")
        run(["npm.cmd", "run", "check:coding-tools-delivery"], cwd=isolated, log="isolated-delivery-check.log")
        staged_files = git("diff", "--cached", "--name-only", cwd=isolated).decode("utf-8").splitlines()
        if any(relative not in SOURCE_FILES and not relative.startswith(".coding-tools/") for relative in staged_files):
            raise RuntimeError("isolated commit contains an unrelated source change")
        run(["git", "-c", "user.name=Codex", "-c", "user.email=codex@local.invalid", "-c", "commit.gpgsign=false",
             "commit", "-m", "fix(control-plane): accept standing patch from owner console"], cwd=isolated, log="isolated-commit.log")
    else:
        if git("rev-parse", "HEAD^", cwd=isolated).decode().strip() != base_revision:
            raise RuntimeError("resumed isolated commit is not a child of the verified baseline")
        staged_files = git("diff", "--name-only", "HEAD^", "HEAD", cwd=isolated).decode("utf-8").splitlines()
        if "coding-tools delivery check: PASS" not in (OUTPUT / "isolated-delivery-check.log").read_text():
            raise RuntimeError("resumed isolated commit is missing its delivery guard proof")
    for relative in SOURCE_FILES:
        if git("show", f"HEAD:{relative}", cwd=isolated) != (ROOT / relative).read_bytes().replace(b"\r\n", b"\n"):
            raise RuntimeError("isolated source differs from the passed focused-test source")
    new_revision = git("rev-parse", "HEAD", cwd=isolated).decode("ascii").strip()
    if git("rev-parse", "HEAD^", cwd=isolated).decode("ascii").strip() != base_revision:
        raise RuntimeError("isolated commit lost exact base provenance")
    isolated_status = git("status", "--porcelain=v1", "--untracked-files=all", cwd=isolated).decode("utf-8").splitlines()
    if any(not record[3:].startswith(".coding-tools/") for record in isolated_status):
        raise RuntimeError("isolated release source is not clean after commit")
    receipt = json.loads(run(
        [sys.executable, "-B", str(ROOT / "scripts/build-control-plane-release.py"), "--source-root", str(isolated),
         "--source-revision", new_revision, "--output-dir", str(release_output)],
        cwd=isolated, log="build-receipt.json",
    ))
    release = Path(receipt["release_directory"])
    verifier = json.loads(run([sys.executable, "-B", str(release / "deploy/control-plane-verify-release.py"),
                               "--release-dir", str(release)], cwd=isolated, log="artifact-verification.json"))
    new_manifest = json.loads((release / "release-manifest.json").read_text(encoding="utf-8"))
    deployed_manifest = json.loads((OUTPUT / "deployed-release-manifest.json").read_text(encoding="utf-8"))
    deployed_files = {entry["path"]: entry for entry in deployed_manifest["files"]}
    candidate_files = {entry["path"]: entry for entry in new_manifest["files"]}
    changed = []
    for relative in sorted(set(deployed_files) | set(candidate_files)):
        old, new = deployed_files.get(relative), candidate_files.get(relative)
        if old != new:
            changed.append({"path": relative, "deployed": old, "candidate": new})
    runtime_changes = [record for record in changed if record["path"] != "DEPLOYMENT.md"]
    if [record["path"] for record in runtime_changes] != [SOURCE_FILES[0]]:
        raise RuntimeError("candidate would replace unrelated runtime/deploy files")
    if sha256(git("diff", "--cached", "--binary")) != main_index_hash or git("rev-parse", "HEAD").decode().strip() != base_revision:
        raise RuntimeError("main state changed during isolated preparation")
    result = {
        "operation": "isolated_owner_standing_acceptance_release_preparation",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_revision": base_revision,
        "source_revision": new_revision,
        "isolated_source_directory": str(isolated),
        "isolated_branch": "codex/owner-standing-acceptance",
        "isolated_release_source_clean": True,
        "isolated_runtime_evidence_status": isolated_status,
        "main_head_and_index_preserved": True,
        "commit_changed_files": staged_files,
        "source_changes": list(SOURCE_FILES),
        "full_release_file_changes": changed,
        "runtime_and_deploy_file_changes": runtime_changes,
        "unchanged_release_file_count": len(candidate_files) - len(changed),
        "archive": receipt["archive"],
        "archive_sha256": receipt["archive_sha256"],
        "release_directory": receipt["release_directory"],
        "package_source_sha256": receipt["package_source_sha256"],
        "artifact_verification": verifier,
        "focused_test_proof": {
            "command": "python -W error -B -m unittest discover -s tests -p test_mcp_task_sessions.py -k acceptance -v",
            "result": "4 passed before isolated packaging; unchanged source behavior reused",
        },
        "remote_mutations": False,
        "deploy_ready_for_operator_review": True,
    }
    (OUTPUT / "artifact-receipt.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "source_revision", "archive", "archive_sha256", "package_source_sha256", "runtime_and_deploy_file_changes",
        "unchanged_release_file_count", "main_head_and_index_preserved",
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
