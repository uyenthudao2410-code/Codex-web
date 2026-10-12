"""Freeze the one Store lookup delta against the last served source snapshot.

Local-only preparation. Never opens server configuration, SQLite, SSH, or a
service. Existing outputs are immutable and a second invocation fails closed.
"""

from __future__ import annotations

import ast
from datetime import datetime, timezone
import difflib
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path, PurePosixPath
import platform
import tarfile


BASE_REVISION = "5ce5c51fc97584501d5d091e8c21df88250f55eb42e6e756384b234da8837b1f"
BASE_ARCHIVE_SHA = "ba38f233d2369835bc3d60f4d9af3e0b65f0ed71565303628f7a25ef42120b90"
BASE_MANIFEST_SHA = "f79cba83bdb9843cb95ab4bb7b3f0d1f0e59f26c895c841bf434bbbc2e9fecc6"
BASE_PACKAGE = "sha256:bb529f710342bf064fb5d2259ab1ad49e3733a6ca6db0c60b60ed67f119a7566"
BASE_STORE_SHA = "99d3eba656a269886a842bc357a14222eb811bbb7dea8d0538c210d5f3edcf40"
LOCAL_STORE_SHA = "19f8447286e8ffeab1de854f378e31656206e9c177d3a514beb2ad442dccc537"
POST_STORE_SHA = "1d45615fff15e19dc50d4a7cead04b7566ed0acd87489f2ab5cd69adbc24a9e0"
DRIVER_BASE_SHA = "0a7f8a058765112ae6bf125521dc16661dbf9dd42a9775921ab2516701f85fa5"
CHANGED_PATH = "control-plane/control_plane/store.py"
METHOD = "assigned_read_only_policy_context"
SERVICE_INSTANCE = "cp_d203277517b747e4b056ec0184d09709"
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
PRIOR = ROOT / ".coding-tools/reports/unified-setup-20261011/rollout-r7"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(data: object) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def exclusive(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)


def replace_once(text: str, before: str, after: str) -> str:
    assert text.count(before) == 1, "guarded helper substitution does not match frozen base"
    return text.replace(before, after, 1)


def method_without(tree: ast.Module) -> str:
    owner = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "ControlPlaneStore")
    methods = [node for node in owner.body if isinstance(node, ast.FunctionDef) and node.name == METHOD]
    assert len(methods) == 1
    owner.body.remove(methods[0])
    return ast.dump(tree, include_attributes=False)


def main() -> None:
    archive_path = PRIOR / f"codex-control-plane-{BASE_REVISION}.tar.gz"
    archive_bytes = archive_path.read_bytes()
    assert sha(archive_bytes) == BASE_ARCHIVE_SHA, "served base archive drift"
    payload: dict[str, bytes] = {}
    modes: dict[str, int] = {}
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
        for member in archive.getmembers():
            parts = PurePosixPath(member.name).parts
            assert parts and parts[0] == f"codex-control-plane-{BASE_REVISION}"
            assert not PurePosixPath(member.name).is_absolute() and not any(p in {".", "..", ""} for p in parts)
            assert member.isdir() or member.isfile()
            if member.isfile():
                path = PurePosixPath(*parts[1:]).as_posix()
                assert path not in payload
                source = archive.extractfile(member)
                assert source is not None
                payload[path] = source.read()
                modes[path] = member.mode
    base_manifest_bytes = payload.pop("release-manifest.json")
    assert sha(base_manifest_bytes) == BASE_MANIFEST_SHA
    base_manifest = json.loads(base_manifest_bytes)
    assert base_manifest["source_revision"] == BASE_REVISION
    assert base_manifest["package_source_sha256"] == BASE_PACKAGE
    base_records = {record["path"]: record for record in base_manifest["files"]}
    assert len(payload) == 38 and set(payload) == set(base_records)
    assert sha(canonical(base_manifest["files"])) == BASE_REVISION
    for path, data in payload.items():
        assert len(data) == base_records[path]["size_bytes"] and sha(data) == base_records[path]["sha256"]
        assert (PRIOR / f"codex-control-plane-{BASE_REVISION}" / path).read_bytes() == data
    before = payload[CHANGED_PATH]
    local_source = (ROOT / CHANGED_PATH).read_bytes()
    assert sha(local_source) == LOCAL_STORE_SHA, "Store local source freeze mismatch"
    # Preserve the served file's LF format rather than delivering a whole-file
    # CRLF formatting change from the Windows checkout.
    assert b"\r\n" not in before
    after = local_source.replace(b"\r\n", b"\n")
    assert sha(before) == BASE_STORE_SHA and sha(after) == POST_STORE_SHA, "Store payload freeze mismatch"
    assert method_without(ast.parse(before)) == method_without(ast.parse(after)), "unapproved Store change outside lookup method"
    compile(after, CHANGED_PATH, "exec")
    diff = "".join(difflib.unified_diff(before.decode().splitlines(True), after.decode().splitlines(True),
                                       fromfile="served/" + CHANGED_PATH, tofile="candidate/" + CHANGED_PATH))
    assert diff.count("@@ -") == 2, "unexpected lookup method change"
    payload[CHANGED_PATH] = after
    records = [{"path": p, "size_bytes": len(data), "sha256": sha(data)} for p, data in sorted(payload.items())]
    identity = sha(canonical(records))
    release_name = "codex-control-plane-" + identity
    release_dir = OUT / release_name
    archive_out = OUT / (release_name + ".tar.gz")
    assert not release_dir.exists() and not archive_out.exists() and not (OUT / "packet-manifest.json").exists()
    changed = [record["path"] for record in records if record != base_records[record["path"]]]
    assert changed == [CHANGED_PATH]
    package = hashlib.sha256()
    for path, data in sorted(payload.items()):
        relative = PurePosixPath(path)
        if relative.parent.as_posix() == "control-plane/control_plane" and relative.suffix == ".py":
            package.update(relative.name.encode() + b"\0" + hashlib.sha256(data).digest() + b"\0")

    def component(prefix: str) -> str:
        digest = hashlib.sha256()
        for record in records:
            if record["path"].startswith(prefix):
                digest.update(record["path"].encode() + b"\0" + record["sha256"].encode() + b"\0")
        return digest.hexdigest()

    manifest = {"schema_version": 1, "release_name": release_name, "source_revision": identity,
                "control_plane_schema_version": base_manifest["control_plane_schema_version"],
                "package_source_sha256": "sha256:" + package.hexdigest(),
                "build": {"python": platform.python_version(), "platform": platform.system().lower()},
                "component_sha256": {name: component(prefix) for name, prefix in {
                    "control_plane": "control-plane/control_plane/", "deployment": "deploy/", "documentation": "DEPLOYMENT.md"}.items()},
                "files": records}
    assert manifest["component_sha256"]["deployment"] == base_manifest["component_sha256"]["deployment"]
    assert manifest["component_sha256"]["documentation"] == base_manifest["component_sha256"]["documentation"]
    release_dir.mkdir()
    for path, data in payload.items():
        destination = release_dir / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        exclusive(destination, data)
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    exclusive(release_dir / "release-manifest.json", manifest_bytes)
    spec = importlib.util.spec_from_file_location("frozen_release_verifier", release_dir / "deploy/control-plane-verify-release.py")
    assert spec is not None and spec.loader is not None
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    verification = verifier.verify_release(release_dir)
    directories = {release_name}
    for path in payload:
        parts = PurePosixPath(path).parts[:-1]
        for count in range(1, len(parts) + 1):
            directories.add(release_name + "/" + PurePosixPath(*parts[:count]).as_posix())
    with archive_out.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for directory in sorted(directories):
                    info = tarfile.TarInfo(directory)
                    info.type, info.mode = tarfile.DIRTYPE, 0o700
                    archive.addfile(info)
                for path, data in sorted({**payload, "release-manifest.json": manifest_bytes}.items()):
                    info = tarfile.TarInfo(release_name + "/" + path)
                    info.size, info.mode = len(data), modes.get(path, 0o600)
                    archive.addfile(info, io.BytesIO(data))
    archive_sha = sha(archive_out.read_bytes())
    driver_bytes = (PRIOR / "ubuntu-console-rollout.py").read_bytes()
    assert sha(driver_bytes) == DRIVER_BASE_SHA, "reviewed rollout helper drift"
    driver = driver_bytes.decode()
    substitutions = {
        'BASE_REVISION = "beaa9d5ade4926ef231e3ec9d0a517fe93830e90"': 'BASE_REVISION = "' + BASE_REVISION + '"',
        'BASE_PACKAGE = "sha256:acb5ae4713844015e32ee5005001583ae4c04e650c68fb599b22309c65dd2835"': 'BASE_PACKAGE = "' + BASE_PACKAGE + '"',
        'REVISION = "' + BASE_REVISION + '"': 'REVISION = "' + identity + '"',
        'PACKAGE = "' + BASE_PACKAGE + '"': 'PACKAGE = "' + manifest["package_source_sha256"] + '"',
        'ARCHIVE_SHA256 = "' + BASE_ARCHIVE_SHA + '"': 'ARCHIVE_SHA256 = "' + archive_sha + '"',
        'backup_directory = BACKUP_ROOT / "unified-setup-r7-5ce5c51fc9758450"': 'backup_directory = BACKUP_ROOT / "store-lookup-' + identity[:16] + '"',
        'require(delta == ["control-plane/control_plane/web_ui.py"], "UNRELATED_RELEASE_DELTA")': 'require(delta == ["' + CHANGED_PATH + '"], "UNRELATED_RELEASE_DELTA")',
        'require(file_hash(candidate / delta[0]) == "03e5279c89bf4b1c04ef0139724e77eb960a3efdca32aa59ec2445e3b35fc64b", "FROZEN_CONSOLE_DELTA_MISMATCH")': 'require(file_hash(baseline / delta[0]) == "' + BASE_STORE_SHA + '" and file_hash(candidate / delta[0]) == "' + POST_STORE_SHA + '", "FROZEN_STORE_DELTA_MISMATCH")',
        'require(result["open_writers"] == 0, "OPEN_WRITER_LEASES_BLOCK_DEPLOYMENT")': 'require(result["open_writers"] == 0, "OPEN_WRITER_LEASES_BLOCK_DEPLOYMENT")\n    require(result["open_tasks"] == 0, "OPEN_TASKS_BLOCK_DEPLOYMENT")',
        'old_health = verify_health(origin, token, BASE_REVISION, BASE_PACKAGE)': 'old_health = verify_health(origin, token, BASE_REVISION, BASE_PACKAGE)\n    require(old_health["service_instance_id"] == "' + SERVICE_INSTANCE + '", "BASE_SERVICE_INSTANCE_CHANGED")',
    }
    # Apply identity substitutions independently so the newly assigned base
    # identity cannot accidentally be consumed by the candidate substitution.
    original_driver = driver
    for before_text in substitutions:
        assert original_driver.count(before_text) == 1
    for index, (before_text, after_text) in enumerate(substitutions.items()):
        driver = replace_once(driver, before_text, "__STORE_DELTA_SUBSTITUTION_" + str(index) + "__")
    for index, after_text in enumerate(substitutions.values()):
        driver = replace_once(driver, "__STORE_DELTA_SUBSTITUTION_" + str(index) + "__", after_text)
    start = driver.index('        ui_environment = dict(os.environ, PYTHONPATH=str(candidate / "control-plane"), PYTHONDONTWRITEBYTECODE="1")')
    stop = driver.index('        emit("deployment_complete"', start)
    driver = driver[:start] + driver[stop:]
    driver = driver.replace("Guarded approved MCP web Ubuntu rollout driver", "Guarded pending-approval Store lookup Ubuntu rollout driver", 1)
    family_tables = ("work_requests", "actions", "delivery_attempts", "receipts", "action_reconciliations",
                     "action_dispatch_dispositions", "contexts", "mcp_task_sessions", "mcp_task_writer_leases",
                     "mcp_patch_acceptances", "mcp_file_read_intents", "mcp_approved_patch_intents",
                     "mcp_standing_patch_intents", "mcp_exec_intents", "mcp_artifact_intents",
                     "mcp_document_write_intents", "mcp_read_only_intents")
    fingerprint_code = '        preserved_tables = ' + repr(family_tables) + '\n'
    fingerprint_code += '        preserved_rows = {table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()] for table in preserved_tables}\n'
    fingerprint_code += '        result["preserved_action_task_context_families_sha256"] = canonical_digest(preserved_rows)\n'
    driver = replace_once(driver, '        result["historical_action_families_sha256"] = canonical_digest(families)\n',
                          '        result["historical_action_families_sha256"] = canonical_digest(families)\n' + fingerprint_code)
    compile(driver, "ubuntu-store-rollout.py", "exec")
    exclusive(OUT / "ubuntu-store-rollout.py", driver.encode())
    exclusive(OUT / "store-lookup.diff", diff.encode())
    packet = {"operation": "immutable_store_lookup_packet_preparation", "captured_at_utc": datetime.now(timezone.utc).isoformat(),
              "git_head_observed": "2c554f59cb7b8ffc86ce5e0e28076c792777642f", "source_revision_is_git_commit": False,
              "base_source_revision": BASE_REVISION, "base_package_source_sha256": BASE_PACKAGE,
              "base_archive_sha256": BASE_ARCHIVE_SHA, "base_manifest_sha256": BASE_MANIFEST_SHA,
              "base_store_sha256": BASE_STORE_SHA, "post_store_sha256": POST_STORE_SHA,
              "local_store_source_sha256": LOCAL_STORE_SHA, "payload_line_endings": "LF; preserves served base format",
              "release_name": release_name, "source_revision": identity, "package_source_sha256": manifest["package_source_sha256"],
              "archive_name": archive_out.name, "archive_sha256": archive_sha, "manifest_sha256": sha(manifest_bytes),
              "payload_file_count": len(payload), "changed_payload_paths": changed, "unchanged_payload_file_count": 37,
              "affected_function": "ControlPlaneStore." + METHOD, "diff_sha256": sha(diff.encode()), "unapproved_extra_source_delta": [],
              "local_verification": verification, "python_syntax": "pass", "driver_base_sha256": DRIVER_BASE_SHA,
              "deployment_helper_sha256": sha(driver.encode()), "expected_service_instance_id_before_deployment": SERVICE_INSTANCE,
              "target_host": "100.116.112.22", "target_user": "svhome", "target_service": "codex-control-plane.service",
              "database_schema_version": 28, "database_restore_or_replay": False, "authority_renewal": False,
              "deployment_authorized": False, "deployment_performed": False, "git_commit_or_push_performed": False}
    exclusive(OUT / "packet-manifest.json", (json.dumps(packet, sort_keys=True, indent=2) + "\n").encode())
    print(json.dumps(packet, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
