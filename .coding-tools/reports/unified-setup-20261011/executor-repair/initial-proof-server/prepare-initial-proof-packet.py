"""Prepare a local immutable four-file initial-proof release; no deployment."""

from __future__ import annotations

import ast
from datetime import datetime, timezone
import difflib
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import platform
import tarfile


BASE_REVISION = "395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5"
BASE_ARCHIVE_SHA = "bf76625554e32478202191c29ccdea0790448a47971db30af54a7aa5959d9061"
BASE_MANIFEST_SHA = "c608465e22c2a1e4f5801cf93cb416c5bec9c66b412834f0bfed619a1f01ec8d"
BASE_PACKAGE = "sha256:83611914241508ad1f5ca96d017902cb6675fa15ea082f3aa4698f7cffe74419"
SOURCE_PINS = {
    "control-plane/control_plane/mcp_facade.py": "0a1882ab526cd6903c43a05f65892e6b14f660303080c120a430450641bafe7f",
    "control-plane/control_plane/store.py": "f6a1bee23ba44370434e3aa5687718ebe962347b1c6300dd10cb6c7360600d46",
    "control-plane/control_plane/node_agent.py": "8eb81ca3867642877b3ca0a4b1c14f419e19f15b2293bf8a61322c7250eb0f87",
    "control-plane/control_plane/recovery_approved_patch_bridge.cjs": "da9748607ac7cbe036b5bb011d5794e773331591b9d1ce916619d5130c320e70",
}
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
PRIOR = OUT.parent / "store-delta"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def exclusive(path, data):
    with path.open("xb") as handle:
        handle.write(data)


def main():
    assert not (OUT / "packet-manifest.json").exists(), "immutable packet already exists"
    archive_bytes = (PRIOR / f"codex-control-plane-{BASE_REVISION}.tar.gz").read_bytes()
    assert sha(archive_bytes) == BASE_ARCHIVE_SHA, "frozen Store395 archive mismatch"
    payload, modes = {}, {}
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
        for member in archive.getmembers():
            parts = PurePosixPath(member.name).parts
            assert parts and parts[0] == "codex-control-plane-" + BASE_REVISION
            assert not PurePosixPath(member.name).is_absolute() and not any(p in {".", "..", ""} for p in parts)
            assert member.isfile() or member.isdir()
            if member.isfile():
                path = PurePosixPath(*parts[1:]).as_posix()
                assert path not in payload
                payload[path] = archive.extractfile(member).read()
                modes[path] = member.mode
    base_manifest_bytes = payload.pop("release-manifest.json")
    assert sha(base_manifest_bytes) == BASE_MANIFEST_SHA
    base = json.loads(base_manifest_bytes)
    assert base["source_revision"] == BASE_REVISION and base["package_source_sha256"] == BASE_PACKAGE
    records_before = {record["path"]: record for record in base["files"]}
    assert len(payload) == 38 and set(payload) == set(records_before)
    assert sha(canonical(base["files"])) == BASE_REVISION
    for path, data in payload.items():
        assert sha(data) == records_before[path]["sha256"] and len(data) == records_before[path]["size_bytes"]
    diff = ""
    source_hashes = {}
    for path, pin in SOURCE_PINS.items():
        local = (ROOT / path).read_bytes()
        assert sha(local) == pin, "local source changed before freeze: " + path
        before = payload[path]
        after = local.replace(b"\r\n", b"\n")
        source_hashes[path] = {"local_sha256": pin, "base_sha256": sha(before), "payload_sha256": sha(after)}
        if path.endswith(".py"):
            compile(after, path, "exec")
        diff += "".join(difflib.unified_diff(before.decode().splitlines(True), after.decode().splitlines(True),
                                            fromfile="served/" + path, tofile="candidate/" + path))
        payload[path] = after
    tree = ast.parse(payload["control-plane/control_plane/store.py"])
    schema = next(node.value.value for node in tree.body if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == "SCHEMA_VERSION" for target in node.targets))
    assert schema == 29
    records = [{"path": path, "size_bytes": len(data), "sha256": sha(data)} for path, data in sorted(payload.items())]
    changed = [record["path"] for record in records if record != records_before[record["path"]]]
    assert changed == sorted(SOURCE_PINS), "unrelated release payload delta"
    revision = sha(canonical(records))
    name = "codex-control-plane-" + revision
    release = OUT / name
    archive_path = OUT / (name + ".tar.gz")
    assert not release.exists() and not archive_path.exists()
    package = hashlib.sha256()
    for path, data in sorted(payload.items()):
        relative = PurePosixPath(path)
        if relative.parent.as_posix() == "control-plane/control_plane" and relative.suffix == ".py":
            package.update(relative.name.encode() + b"\0" + hashlib.sha256(data).digest() + b"\0")
    def component(prefix):
        digest = hashlib.sha256()
        for record in records:
            if record["path"].startswith(prefix):
                digest.update(record["path"].encode() + b"\0" + record["sha256"].encode() + b"\0")
        return digest.hexdigest()
    manifest = {
        "schema_version": 1, "release_name": name, "source_revision": revision,
        "control_plane_schema_version": schema, "package_source_sha256": "sha256:" + package.hexdigest(),
        "build": {"python": platform.python_version(), "platform": platform.system().lower()},
        "component_sha256": {key: component(prefix) for key, prefix in {
            "control_plane": "control-plane/control_plane/", "deployment": "deploy/", "documentation": "DEPLOYMENT.md"}.items()},
        "files": records,
    }
    for key in ("deployment", "documentation"):
        assert manifest["component_sha256"][key] == base["component_sha256"][key]
    release.mkdir()
    for path, data in payload.items():
        destination = release / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        exclusive(destination, data)
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    exclusive(release / "release-manifest.json", manifest_bytes)
    namespace = {"__name__": "frozen_release_verifier"}
    exec(compile(payload["deploy/control-plane-verify-release.py"], "frozen_release_verifier", "exec"), namespace)
    verification = namespace["verify_release"](release)
    directories = {name}
    for path in payload:
        parts = PurePosixPath(path).parts[:-1]
        for count in range(1, len(parts) + 1):
            directories.add(name + "/" + PurePosixPath(*parts[:count]).as_posix())
    with archive_path.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for directory in sorted(directories):
                    member = tarfile.TarInfo(directory)
                    member.type, member.mode = tarfile.DIRTYPE, 0o700
                    archive.addfile(member)
                for path, data in sorted({**payload, "release-manifest.json": manifest_bytes}.items()):
                    member = tarfile.TarInfo(name + "/" + path)
                    member.size, member.mode = len(data), modes.get(path, 0o600)
                    archive.addfile(member, io.BytesIO(data))
    exclusive(OUT / "initial-proof-server.diff", diff.encode())
    receipt = {
        "operation": "immutable_initial_proof_server_packet_preparation", "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_head_observed": "2c554f59cb7b8ffc86ce5e0e28076c792777642f", "source_revision_is_git_commit": False,
        "base_source_revision": BASE_REVISION, "base_package_source_sha256": BASE_PACKAGE,
        "base_archive_sha256": BASE_ARCHIVE_SHA, "base_manifest_sha256": BASE_MANIFEST_SHA,
        "release_name": name, "source_revision": revision, "package_source_sha256": manifest["package_source_sha256"],
        "archive_name": archive_path.name, "archive_sha256": sha(archive_path.read_bytes()), "manifest_sha256": sha(manifest_bytes),
        "source_hashes": source_hashes, "changed_payload_paths": changed, "unchanged_payload_file_count": 34,
        "payload_file_count": 38, "payload_line_endings": "LF; canonicalizes Windows CRLF while preserving served format",
        "local_verification": verification, "diff_sha256": sha(diff.encode()),
        "schema_migration": {"from": 28, "to": 29, "new_tables": [],
            "add_nullable_columns": {table: ["verification_json TEXT"] for table in
                ("mcp_permission_requests", "mcp_approved_patch_intents", "mcp_standing_patch_intents")},
            "legacy_rows_rewritten": False, "legacy_no_plan_digests_preserved": True},
        "rollback": {"retain_store395_release": True, "retain_preactivation_sqlite_backup": True,
            "restore_database_automatically": False, "old_schema28_binary_supports_schema29": False,
            "strategy": "Preserve all task history; use schema29-compatible rollback or forward fix. Never lower user_version or restore an old snapshot over new task history."},
        "live_identity_expected_only": {"service_instance_id": "cp_6766892f5ada47d1862a0d24334f1116",
            "source_revision": BASE_REVISION, "package_source_sha256": BASE_PACKAGE},
        "target_host": "100.116.112.22", "target_user": "svhome", "target_service": "codex-control-plane.service",
        "deployment_authorized": False, "deployment_performed": False, "service_operation_performed": False,
        "authority_renewal": False, "database_restore_or_replay": False, "git_commit_or_push_performed": False,
    }
    exclusive(OUT / "packet-manifest.json", (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode())
    print(json.dumps({key: receipt[key] for key in ("source_revision", "package_source_sha256", "archive_name", "archive_sha256", "manifest_sha256", "changed_payload_paths", "local_verification")}, sort_keys=True))


if __name__ == "__main__":
    main()
