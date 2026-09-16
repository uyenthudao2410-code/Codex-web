#!/usr/bin/env python3
"""Build a versioned, secret-free Ubuntu control-plane release archive.

The builder is intentionally an artifact-preparation command only. It does not
read a service environment, SQLite database, or credentials; alter a current
symlink; install a systemd unit; or start/restart a process. It copies a small
allowlist into an immutable release directory and emits a manifest that binds
the selected Git revision, package fingerprint, component hashes and build
runtime. Deployment remains an explicit operator procedure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
RELEASE_SCHEMA_VERSION = 1
REVISION_PATTERN = re.compile(r"^[0-9a-f]{40,64}$")
CONTROL_PLANE_FILES = (
    "README.md",
)
DEPLOY_FILES = (
    "codex-control-plane.service.example",
    "codex-control-plane-mcp-tunnel.service.example",
    "codex-control-plane-backup.service.example",
    "codex-control-plane-backup.timer.example",
    "codex-control-plane-healthcheck.service.example",
    "codex-control-plane-healthcheck.timer.example",
    "control-plane-launcher.sh",
    "control-plane-mcp-tunnel-launcher.sh",
    "control-plane-backup.sh",
    "control-plane-healthcheck.sh",
    "control-plane-verify-release.py",
    "control-plane.env.example",
)
CONTROL_PLANE_RUNTIME_SUFFIXES = frozenset({".py", ".cjs", ".cmd"})
REQUIRED_RELEASE_FILES = frozenset(
    {
        "control-plane/README.md",
        "control-plane/control_plane/__main__.py",
        "control-plane/control_plane/http_api.py",
        "control-plane/control_plane/maintenance.py",
        "control-plane/control_plane/store.py",
        "deploy/codex-control-plane.service.example",
        "deploy/codex-control-plane-mcp-tunnel.service.example",
        "deploy/codex-control-plane-backup.service.example",
        "deploy/codex-control-plane-backup.timer.example",
        "deploy/codex-control-plane-healthcheck.service.example",
        "deploy/codex-control-plane-healthcheck.timer.example",
        "deploy/control-plane-launcher.sh",
        "deploy/control-plane-mcp-tunnel-launcher.sh",
        "deploy/control-plane-backup.sh",
        "deploy/control-plane-healthcheck.sh",
        "deploy/control-plane-verify-release.py",
        "deploy/control-plane.env.example",
        "DEPLOYMENT.md",
    }
)

class ReleaseBuildError(RuntimeError):
    """A non-destructive release preparation failure."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _regular_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ReleaseBuildError(f"release input contains a symlink: {path.relative_to(root)}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ReleaseBuildError(f"release input is not a regular file: {path.relative_to(root)}")
        files.append(path)
    return files


def _copy_tree(source: Path, destination: Path, *, allowed_suffixes: frozenset[str] | None = None) -> None:
    for path in _regular_files(source):
        relative = path.relative_to(source)
        if allowed_suffixes is not None and path.suffix.lower() not in allowed_suffixes:
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def _copy_file(source: Path, destination: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise ReleaseBuildError(f"required release input is missing or unsafe: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _git_text(source_root: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(source_root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise ReleaseBuildError("selected source is not a readable Git checkout") from error
    return completed.stdout.strip()


def _source_revision(source_root: Path) -> str:
    revision = _git_text(source_root, "rev-parse", "HEAD").lower()
    if REVISION_PATTERN.fullmatch(revision) is None:
        raise ReleaseBuildError("selected source revision is invalid")
    return revision


def _assert_source_clean(source_root: Path) -> None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(source_root), "status", "--porcelain=v1", "--untracked-files=all", "-z"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise ReleaseBuildError("selected source cannot be checked for release drift") from error
    for raw_record in completed.stdout.split(b"\0"):
        if not raw_record:
            continue
        if len(raw_record) < 4:
            raise ReleaseBuildError("selected source has an unreadable Git status record")
        relative = raw_record[3:].decode("utf-8", "surrogateescape")
        # Runtime evidence is deliberately versioned independently of source
        # content. It is not copied into this artifact and cannot alter its
        # file manifest, so its allowed live drift does not invalidate source
        # release preparation.
        if relative == ".coding-tools" or relative.startswith(".coding-tools/"):
            continue
        raise ReleaseBuildError("selected source has tracked or untracked release drift")


def _control_plane_metadata(source_root: Path) -> tuple[int, str]:
    package_root = source_root / "control-plane"
    if not (package_root / "control_plane" / "http_api.py").is_file():
        raise ReleaseBuildError("control-plane package source is missing")
    original_path = list(sys.path)
    try:
        sys.path.insert(0, str(package_root))
        from control_plane.http_api import _package_source_sha256
        from control_plane.store import SCHEMA_VERSION

        fingerprint = _package_source_sha256()
    finally:
        sys.path[:] = original_path
    if not isinstance(SCHEMA_VERSION, int) or SCHEMA_VERSION < 1:
        raise ReleaseBuildError("control-plane schema version is invalid")
    if not isinstance(fingerprint, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", fingerprint):
        raise ReleaseBuildError("control-plane package fingerprint is invalid")
    return SCHEMA_VERSION, fingerprint


def _manifest_files(release_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in _regular_files(release_root):
        relative = path.relative_to(release_root).as_posix()
        if relative == "release-manifest.json":
            continue
        records.append({"path": relative, "size_bytes": path.stat().st_size, "sha256": _sha256_file(path)})
    return records


def _component_digest(records: Iterable[dict[str, Any]], prefix: str) -> str:
    digest = hashlib.sha256()
    count = 0
    for record in records:
        path = str(record["path"])
        if not path.startswith(prefix):
            continue
        count += 1
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(record["sha256"]).encode("ascii"))
        digest.update(b"\0")
    if count == 0:
        raise ReleaseBuildError(f"release component is empty: {prefix}")
    return digest.hexdigest()


def _deployment_guide(release_name: str) -> str:
    return f"""# Control-plane release deployment

This archive contains **{release_name}**. It is a source artifact, not an
activated service. It contains no SQLite database, operator token, node
credential, session, backup, or private environment file.

## Prepare outside the release tree

1. Inspect `release-manifest.json`; verify the selected Git revision, package
   fingerprint and each file digest before extracting it under a versioned path
   such as `~/.local/lib/codex-control-plane/releases/<revision>`.
2. Copy `deploy/control-plane.env.example` to
   `~/.config/codex-control-plane/control-plane.env`, replace every placeholder,
   and set mode `0600`. Keep the database and backups in an owner-only state
   directory outside `releases/`.
3. Run `python3 deploy/control-plane-verify-release.py --release-dir <release>`
   and compare its content-free receipt to this manifest. Install the six
   unit/timer examples from `deploy/` as user units. They only
   execute `~/.local/lib/codex-control-plane/current/deploy/...`; `current` must
   be an operator-controlled symlink to exactly one verified release directory.

## Controlled activation

Before changing `current`, close admission through the existing authenticated
control-plane procedure, inspect active/inflight work, and make a verified
backup. A schema migration is allowed only after that verified snapshot and is
part of starting the selected service; never rewrite a live database from the
archive or use an application rollback as a database rollback. Point `current`
at the selected release, refresh units, then start or
restart only the named control-plane service through the supported systemd
procedure. Verify `/healthz` with the package fingerprint in this manifest
before reopening admission. Do not infer a live deployment from archive creation
or a matching source checkout.

## Rollback

Close admission, fence/reconcile any in-flight work, point `current` at the
previous compatible verified release, and obtain new process/health identity
evidence before an explicit reopen. Database restore is a separate recovery
decision: never copy a database into a release directory or restore it merely
because an application binary was rolled back.
"""


def build_release(
    source_root: Path,
    output_dir: Path,
    source_revision: str,
    *,
    require_clean_source: bool,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    output_dir = output_dir.resolve()
    revision = source_revision.lower()
    if REVISION_PATTERN.fullmatch(revision) is None:
        raise ReleaseBuildError("source revision must be a 40-64 character lowercase Git revision")
    if require_clean_source:
        _assert_source_clean(source_root)
        if revision != _source_revision(source_root):
            raise ReleaseBuildError("requested source revision does not match the clean checkout")
    if not output_dir.exists() or not output_dir.is_dir():
        raise ReleaseBuildError("output directory must already exist")

    release_name = f"codex-control-plane-{revision}"
    final_release = output_dir / release_name
    final_archive = output_dir / f"{release_name}.tar.gz"
    if final_release.exists() or final_archive.exists():
        raise ReleaseBuildError("release output already exists; choose a new output directory")

    schema_version, package_fingerprint = _control_plane_metadata(source_root)
    staging_root = Path(tempfile.mkdtemp(prefix=".control-plane-release-", dir=output_dir))
    staging_release = staging_root / release_name
    temporary_archive = staging_root / f"{release_name}.tar.gz"
    try:
        _copy_tree(
            source_root / "control-plane" / "control_plane",
            staging_release / "control-plane" / "control_plane",
            allowed_suffixes=CONTROL_PLANE_RUNTIME_SUFFIXES,
        )
        for relative in CONTROL_PLANE_FILES:
            _copy_file(source_root / "control-plane" / relative, staging_release / "control-plane" / relative)
        for relative in DEPLOY_FILES:
            _copy_file(source_root / "deploy" / relative, staging_release / "deploy" / relative)
        (staging_release / "DEPLOYMENT.md").write_text(_deployment_guide(release_name), encoding="utf-8")

        records = _manifest_files(staging_release)
        released_paths = {str(record["path"]) for record in records}
        if not REQUIRED_RELEASE_FILES.issubset(released_paths):
            raise ReleaseBuildError("release manifest is missing a required runtime or deployment file")
        manifest = {
            "schema_version": RELEASE_SCHEMA_VERSION,
            "release_name": release_name,
            "source_revision": revision,
            "control_plane_schema_version": schema_version,
            "package_source_sha256": package_fingerprint,
            "build": {
                "python": platform.python_version(),
                "platform": platform.system().lower(),
            },
            "component_sha256": {
                "control_plane": _component_digest(records, "control-plane/control_plane/"),
                "deployment": _component_digest(records, "deploy/"),
                "documentation": _component_digest(records, "DEPLOYMENT.md"),
            },
            "files": records,
        }
        (staging_release / "release-manifest.json").write_text(
            json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        with tarfile.open(temporary_archive, "w:gz", compresslevel=9) as archive:
            archive.add(staging_release, arcname=release_name, recursive=True)
        os.replace(staging_release, final_release)
        os.replace(temporary_archive, final_archive)
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)

    return {
        "operation": "control_plane_versioned_release_build",
        "release_name": release_name,
        "source_revision": revision,
        "package_source_sha256": package_fingerprint,
        "control_plane_schema_version": schema_version,
        "release_directory": str(final_release),
        "archive": str(final_archive),
        "archive_sha256": _sha256_file(final_archive),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, help="existing empty-or-new directory for release outputs")
    parser.add_argument("--source-root", default=str(ROOT), help="Git checkout containing this repository")
    parser.add_argument("--source-revision", default=None, help="optional exact revision; must equal clean checkout HEAD")
    args = parser.parse_args(argv)
    source_root = Path(args.source_root).expanduser()
    try:
        revision = str(args.source_revision or _source_revision(source_root)).lower()
        receipt = build_release(source_root, Path(args.output_dir).expanduser(), revision, require_clean_source=True)
    except ReleaseBuildError as error:
        print(json.dumps({"error": {"code": "CONTROL_PLANE_RELEASE_BUILD_FAILED"}}, separators=(",", ":")), file=sys.stderr)
        return 2
    except (OSError, tarfile.TarError):
        print(json.dumps({"error": {"code": "CONTROL_PLANE_RELEASE_BUILD_FAILED"}}, separators=(",", ":")), file=sys.stderr)
        return 1
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
