"""Freeze a local, closed-intake schema29 Store395 recovery artifact."""
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

OUT = Path(__file__).resolve().parent
BASE = OUT.parents[1] / "store-delta"
BASE_REVISION = "395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5"
BASE_ARCHIVE_SHA = "bf76625554e32478202191c29ccdea0790448a47971db30af54a7aa5959d9061"
BASE_MANIFEST_SHA = "c608465e22c2a1e4f5801cf93cb416c5bec9c66b412834f0bfed619a1f01ec8d"
STORE_PATH = "control-plane/control_plane/store.py"
DENIED_METHODS = (
    "set_admission_mode", "create_scoped_pilot_decision", "renew_scoped_pilot_decision",
    "create_context", "create_work_request", "create_mcp_access_grant",
    "create_mcp_service_grant", "renew_mcp_service_grant",
    "record_mcp_patch_acceptance", "record_owner_mcp_patch_acceptance", "_admission_decision",
)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def exclusive(path, data):
    with path.open("xb") as handle:
        handle.write(data)

def recovery_store(before):
    text = before.decode()
    assert text.count("SCHEMA_VERSION = 28\n") == 1
    text = text.replace("SCHEMA_VERSION = 28\n", "SCHEMA_VERSION = 29\n", 1)
    tree = ast.parse(text)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ControlPlaneStore")
    methods = {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
    inserts = {}
    for name in DENIED_METHODS:
        method = methods[name]
        first = method.body[0]
        line = first.end_lineno if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str) else first.lineno - 1
        inserts[line] = '        raise ConflictError("schema29 recovery artifact prohibits new authority, intake, and semantic acceptance.")\n'
    inserts[methods["poll_actions"].body[0].end_lineno] = (
        "        # Recovery is observation/receipt only; never allocate another attempt.\n"
        "        return []\n"
    )
    inserts[methods["_initialize"].body[0].lineno - 1] = '''        # Emergency recovery supports only an existing, closed schema29 database.
        # Do not run the legacy initializer, migrate, downgrade, or rewrite history.
        if not self.path.is_file():
            raise RuntimeError("schema29 recovery requires an existing database.")
        with self._connection() as connection:
            if int(connection.execute("PRAGMA user_version").fetchone()[0]) != 29:
                raise RuntimeError("schema29 recovery requires exact database schema29.")
            state = connection.execute("SELECT state_value FROM control_plane_state WHERE state_key = 'admission_mode'").fetchone()
            if state is None or state["state_value"] != "recovery":
                raise RuntimeError("schema29 recovery requires persisted closed admission.")
            for table in ("mcp_permission_requests", "mcp_approved_patch_intents", "mcp_standing_patch_intents"):
                columns = {row["name"]: row for row in connection.execute(f"PRAGMA table_info({table})")}
                column = columns.get("verification_json")
                if column is None or column["type"].upper() != "TEXT" or column["notnull"]:
                    raise RuntimeError("schema29 recovery requires nullable verification_json columns.")
        return
'''
    # Other old entry points inspect the same persisted admission helper.
    method = methods["_admission_mode"]
    ret = next(n for n in method.body if isinstance(n, ast.Return))
    inserts[ret.lineno - 1] = '''        if row is None or row["state_value"] != "recovery":
            raise ConflictError("schema29 recovery cannot operate after admission drift.")
'''
    lines = text.splitlines(True)
    for line, addition in sorted(inserts.items(), reverse=True):
        lines[line:line] = [addition]
    after = "".join(lines).encode()
    compile(after, STORE_PATH, "exec")
    return after

def main():
    assert not (OUT / "packet-manifest.json").exists(), "immutable recovery packet already exists"
    archive_bytes = (BASE / f"codex-control-plane-{BASE_REVISION}.tar.gz").read_bytes()
    assert sha(archive_bytes) == BASE_ARCHIVE_SHA
    payload, modes = {}, {}
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
        for member in archive.getmembers():
            parts = PurePosixPath(member.name).parts
            assert parts[0] == "codex-control-plane-" + BASE_REVISION
            assert not PurePosixPath(member.name).is_absolute() and not any(p in {".", "..", ""} for p in parts)
            assert member.isfile() or member.isdir()
            if member.isfile():
                path = PurePosixPath(*parts[1:]).as_posix()
                assert path not in payload
                payload[path] = archive.extractfile(member).read()
                modes[path] = member.mode
    manifest_before = payload.pop("release-manifest.json")
    assert sha(manifest_before) == BASE_MANIFEST_SHA
    base = json.loads(manifest_before)
    records_before = {r["path"]: r for r in base["files"]}
    assert len(payload) == 38 and sha(canonical(base["files"])) == BASE_REVISION
    for path, data in payload.items():
        assert sha(data) == records_before[path]["sha256"] and len(data) == records_before[path]["size_bytes"]
    before = payload[STORE_PATH]
    payload[STORE_PATH] = recovery_store(before)
    diff = "".join(difflib.unified_diff(before.decode().splitlines(True), payload[STORE_PATH].decode().splitlines(True), fromfile="Store395/" + STORE_PATH, tofile="schema29-recovery/" + STORE_PATH)).encode()
    records = [{"path": p, "size_bytes": len(d), "sha256": sha(d)} for p, d in sorted(payload.items())]
    assert [r["path"] for r in records if r != records_before[r["path"]]] == [STORE_PATH]
    revision = sha(canonical(records))
    name = "codex-control-plane-" + revision
    release = OUT / name
    release.mkdir()
    package = hashlib.sha256()
    for path, data in sorted(payload.items()):
        p = PurePosixPath(path)
        if p.parent.as_posix() == "control-plane/control_plane" and p.suffix == ".py":
            package.update(p.name.encode() + b"\0" + hashlib.sha256(data).digest() + b"\0")
        dest = release / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        exclusive(dest, data)
    def component(prefix):
        digest = hashlib.sha256()
        for r in records:
            if r["path"].startswith(prefix):
                digest.update(r["path"].encode() + b"\0" + r["sha256"].encode() + b"\0")
        return digest.hexdigest()
    manifest = {"schema_version": 1, "release_name": name, "source_revision": revision, "control_plane_schema_version": 29,
                "package_source_sha256": "sha256:" + package.hexdigest(),
                "build": {"python": platform.python_version(), "platform": platform.system().lower()},
                "component_sha256": {k: component(p) for k, p in {"control_plane": "control-plane/control_plane/", "deployment": "deploy/", "documentation": "DEPLOYMENT.md"}.items()}, "files": records}
    for key in ("deployment", "documentation"):
        assert manifest["component_sha256"][key] == base["component_sha256"][key]
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    exclusive(release / "release-manifest.json", manifest_bytes)
    namespace = {"__name__": "frozen_release_verifier"}
    exec(compile(payload["deploy/control-plane-verify-release.py"], "frozen_release_verifier", "exec"), namespace)
    verification = namespace["verify_release"](release)
    archive_path = OUT / (name + ".tar.gz")
    with archive_path.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for path, data in sorted({**payload, "release-manifest.json": manifest_bytes}.items()):
                    member = tarfile.TarInfo(name + "/" + path)
                    member.size, member.mode = len(data), modes.get(path, 0o600)
                    archive.addfile(member, io.BytesIO(data))
    exclusive(OUT / "schema29-recovery.diff", diff)
    receipt = {"operation": "offline_closed_schema29_recovery_preparation", "captured_at_utc": datetime.now(timezone.utc).isoformat(),
               "git_head_observed": "2c554f59cb7b8ffc86ce5e0e28076c792777642f", "base_source_revision": BASE_REVISION,
               "base_archive_sha256": BASE_ARCHIVE_SHA, "base_manifest_sha256": BASE_MANIFEST_SHA,
               "source_revision": revision, "source_revision_is_git_commit": False, "release_name": name,
               "package_source_sha256": manifest["package_source_sha256"], "archive_name": archive_path.name,
               "archive_sha256": sha(archive_path.read_bytes()), "manifest_sha256": sha(manifest_bytes), "diff_sha256": sha(diff),
               "changed_payload_paths": [STORE_PATH], "unchanged_payload_file_count": 37, "local_release_verification": verification,
               "supported_state": "existing schema29 database with persisted admission_mode=recovery and nullable verification_json columns",
               "new_intake_or_dispatch_enabled": False, "new_grants_or_authority_enabled": False,
               "semantic_acceptance_enabled": False, "migration_or_database_restore": False,
               "deployment_performed": False, "service_operation_performed": False, "authority_renewal_performed": False,
               "git_commit_or_push_performed": False, "denied_store_entry_points": list(DENIED_METHODS)}
    exclusive(OUT / "packet-manifest.json", (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode())
    print(json.dumps({k: receipt[k] for k in ("source_revision", "package_source_sha256", "archive_sha256", "manifest_sha256", "local_release_verification")}, sort_keys=True))

if __name__ == "__main__":
    main()
