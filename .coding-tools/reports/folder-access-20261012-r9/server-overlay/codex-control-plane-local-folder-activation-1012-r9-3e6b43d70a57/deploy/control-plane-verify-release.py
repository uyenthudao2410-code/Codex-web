#!/usr/bin/env python3
"""Verify one extracted, versioned control-plane release before activation.

This command reads only the selected release directory and its manifest. It
does not read a service environment, SQLite database, credentials or network;
alter a `current` symlink; or start/stop a process. A pass proves artifact
integrity at this directory boundary, not service ownership, loaded code, TLS,
node admission or a task effect.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Sequence


MANIFEST_NAME = "release-manifest.json"
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
REVISION_PATTERN = re.compile(r"^[0-9a-f]{40,64}$")
FINGERPRINT_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
COMPONENT_PREFIXES = {
    "control_plane": "control-plane/control_plane/",
    "deployment": "deploy/",
    "documentation": "DEPLOYMENT.md",
}


class ReleaseVerificationError(RuntimeError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ReleaseVerificationError("invalid release file path")
    candidate = Path(value)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise ReleaseVerificationError("invalid release file path")
    return candidate.as_posix()


def _regular_files(root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise ReleaseVerificationError("release contains a symlink")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ReleaseVerificationError("release contains an unsupported entry")
        files[relative] = path
    return files


def _read_manifest(root: Path) -> dict[str, Any]:
    manifest_path = root / MANIFEST_NAME
    if manifest_path.is_symlink() or not manifest_path.is_file() or manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ReleaseVerificationError("release manifest is unavailable")
    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseVerificationError("release manifest is invalid") from error
    if not isinstance(value, dict):
        raise ReleaseVerificationError("release manifest is invalid")
    return value


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
        raise ReleaseVerificationError("release component is empty")
    return digest.hexdigest()


def verify_release(release_dir: str | Path) -> dict[str, Any]:
    root = Path(release_dir).expanduser().resolve()
    if not root.is_dir() or root.is_symlink():
        raise ReleaseVerificationError("release directory is invalid")
    manifest = _read_manifest(root)
    if set(manifest) != {
        "schema_version",
        "release_name",
        "source_revision",
        "control_plane_schema_version",
        "package_source_sha256",
        "build",
        "component_sha256",
        "files",
    }:
        raise ReleaseVerificationError("release manifest has an unexpected schema")
    if manifest["schema_version"] != 1 or manifest["release_name"] != root.name:
        raise ReleaseVerificationError("release manifest identity is invalid")
    if not isinstance(manifest["source_revision"], str) or REVISION_PATTERN.fullmatch(manifest["source_revision"]) is None:
        raise ReleaseVerificationError("release source revision is invalid")
    if not isinstance(manifest["control_plane_schema_version"], int) or manifest["control_plane_schema_version"] < 1:
        raise ReleaseVerificationError("release control-plane schema is invalid")
    if not isinstance(manifest["package_source_sha256"], str) or FINGERPRINT_PATTERN.fullmatch(manifest["package_source_sha256"]) is None:
        raise ReleaseVerificationError("release package fingerprint is invalid")
    if not isinstance(manifest["build"], dict) or set(manifest["build"]) != {"python", "platform"}:
        raise ReleaseVerificationError("release build metadata is invalid")
    component_hashes = manifest["component_sha256"]
    if not isinstance(component_hashes, dict) or set(component_hashes) != set(COMPONENT_PREFIXES):
        raise ReleaseVerificationError("release component metadata is invalid")
    if any(not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None for value in component_hashes.values()):
        raise ReleaseVerificationError("release component metadata is invalid")
    records = manifest["files"]
    if not isinstance(records, list) or not records:
        raise ReleaseVerificationError("release file manifest is invalid")

    expected: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != {"path", "size_bytes", "sha256"}:
            raise ReleaseVerificationError("release file manifest is invalid")
        relative = _safe_relative(record["path"])
        size = record["size_bytes"]
        sha256 = record["sha256"]
        if relative == MANIFEST_NAME or relative in expected:
            raise ReleaseVerificationError("release file manifest is invalid")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise ReleaseVerificationError("release file manifest is invalid")
        if not isinstance(sha256, str) or SHA256_PATTERN.fullmatch(sha256) is None:
            raise ReleaseVerificationError("release file manifest is invalid")
        expected[relative] = {"path": relative, "size_bytes": size, "sha256": sha256}

    actual = _regular_files(root)
    actual.pop(MANIFEST_NAME, None)
    if set(actual) != set(expected):
        raise ReleaseVerificationError("release file set does not match manifest")
    for relative, record in expected.items():
        path = actual[relative]
        if path.stat().st_size != record["size_bytes"] or _sha256_file(path) != record["sha256"]:
            raise ReleaseVerificationError("release file hash does not match manifest")
    for component, prefix in COMPONENT_PREFIXES.items():
        if _component_digest(expected.values(), prefix) != component_hashes[component]:
            raise ReleaseVerificationError("release component hash does not match manifest")

    return {
        "operation": "control_plane_release_verification",
        "release_name": manifest["release_name"],
        "source_revision": manifest["source_revision"],
        "control_plane_schema_version": manifest["control_plane_schema_version"],
        "package_source_sha256": manifest["package_source_sha256"],
        "file_count": len(expected),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-dir", required=True, help="extracted versioned release directory")
    args = parser.parse_args(argv)
    try:
        receipt = verify_release(args.release_dir)
    except (OSError, ReleaseVerificationError):
        print(json.dumps({"error": {"code": "CONTROL_PLANE_RELEASE_VERIFICATION_FAILED"}}, separators=(",", ":")), file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
