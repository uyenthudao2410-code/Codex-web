"""Guarded immutable Native-First prerequisite deployment on confirmed Ubuntu.

Default is read-only. --execute stops the exact service before the final census,
copies the DB through a read-only connection into a protected backup, changes
only official source activation config/current link, then starts the service.
Pre-start failures restore only source/config. Once candidate start is attempted,
leave it for operator review, because it may admit work. DB and authority are
never restored, modified, reconciled or replayed by this helper.
"""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import stat
import subprocess
import sys
import tarfile
import time
import urllib.request

sys.dont_write_bytecode = True
SERVICE = "codex-control-plane.service"
DEVICE = "4c4b7a5b-7744-49ae-a490-78a528a00471"
STAGE = "read_only_preflight"


def require(value, code):
    if not value:
        raise RuntimeError(code)


def sha(content):
    return hashlib.sha256(content).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def systemctl(verb):
    arguments = ["systemctl", "--user", verb]
    if verb != "daemon-reload":
        arguments.append(SERVICE)
    result = subprocess.run(arguments, capture_output=True, timeout=45, check=False)
    require(result.returncode == 0, "EXACT_SERVICE_" + verb.upper().replace("-", "_") + "_FAILED")


def identity():
    result = subprocess.run(["systemctl", "--user", "show", SERVICE, "--property=MainPID", "--property=ActiveState"], capture_output=True, text=True, timeout=10, check=False)
    require(result.returncode == 0, "SYSTEMD_IDENTITY_FAILED")
    fields = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    pid = int(fields.get("MainPID", "0"))
    environment = dict(item.split("=", 1) for item in Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in item) if pid > 1 else None
    return pid, fields.get("ActiveState"), environment


def protected(path, maximum=131072):
    metadata = path.lstat()
    require(stat.S_ISREG(metadata.st_mode) and metadata.st_uid == os.getuid()
            and metadata.st_mode & 0o077 == 0 and metadata.st_size <= maximum, "PROTECTED_FILE_INVALID")
    return path.read_bytes()


def atomic(path, content, mode=0o600):
    temporary = path.with_name("." + path.name + ".native-first-" + str(os.getpid()))
    require(not temporary.exists(), "ATOMIC_TEMP_EXISTS")
    with temporary.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.chmod(mode)
    os.replace(temporary, path)


def current_link(current, target):
    temporary = current.with_name(".current-native-first-" + str(os.getpid()))
    require(not temporary.exists() and not temporary.is_symlink(), "CURRENT_TEMP_EXISTS")
    temporary.symlink_to(target)
    os.replace(temporary, current)


def connect(database):
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    connection.row_factory = sqlite3.Row
    return connection


def digest_rows(rows):
    values = [dict(row) for row in rows]
    values.sort(key=lambda row: json.dumps(row, sort_keys=True))
    return sha(json.dumps(values, sort_keys=True, separators=(",", ":")).encode())


def census(database, approved, allow_live=False):
    now = int(time.time() * 1000)
    connection = connect(database)
    try:
        connection.execute("BEGIN")
        require(connection.execute("PRAGMA user_version").fetchone()[0] == 29, "DATABASE_SCHEMA_CHANGED")
        require(connection.execute("SELECT state_value FROM control_plane_state WHERE state_key='admission_mode'").fetchone()[0] == "scoped_pilot", "ADMISSION_CHANGED")
        live_tasks = connection.execute("SELECT COUNT(*) FROM mcp_task_sessions WHERE closed_at_ms IS NULL AND expires_at_ms>?", (now,)).fetchone()[0]
        live_writers = connection.execute("SELECT COUNT(*) FROM mcp_task_writer_leases WHERE released_at_ms IS NULL AND expires_at_ms>?", (now,)).fetchone()[0]
        active_actions = connection.execute("SELECT COUNT(*) FROM actions WHERE settled_at_ms IS NULL AND delivery_state IN ('queued','dispatch_unconfirmed','accepted')").fetchone()[0]
        if not allow_live:
            require(live_tasks == live_writers == active_actions == 0, "LIVE_WORK_BLOCKS_SERVICE_TRANSITION")
        expected_ids = [row["action_id"] for row in approved["expected_unknown_actions"]]
        placeholders = ",".join("?" for _ in expected_ids)
        unknown = [dict(row) for row in connection.execute("SELECT a.action_id,a.workspace_id,a.workspace_generation,a.delivery_state,a.expires_at_ms,r.disposition FROM actions a LEFT JOIN action_reconciliations r ON r.action_id=a.action_id WHERE a.device_id=? AND a.action_id IN (" + placeholders + ") ORDER BY a.created_at_ms,a.action_id", (DEVICE, *expected_ids))]
        require(unknown == approved["expected_unknown_actions"], "UNRESOLVED_HISTORY_SET_CHANGED")
        if not allow_live:
            require(connection.execute("SELECT COUNT(*) FROM actions WHERE device_id=? AND settled_at_ms IS NULL", (DEVICE,)).fetchone()[0] == len(unknown), "NEW_UNRESOLVED_ACTION_BEFORE_TRANSITION")
        require(all(row["delivery_state"] == "reconcile_required" and row["expires_at_ms"] <= now for row in unknown), "UNRESOLVED_HISTORY_NOT_EXPIRED_UNKNOWN")
        history_ids = expected_ids
        hashes = {}
        for table in ("actions", "action_reconciliations", "delivery_attempts", "receipts"):
            hashes[table] = digest_rows(connection.execute("SELECT * FROM " + table + " WHERE action_id IN (" + placeholders + ")", history_ids))
        # Lease/session/action rows are stable at the stopped-service boundary.
        for table in ("mcp_task_sessions", "mcp_task_writer_leases", "bindings", "node_workspaces"):
            hashes[table] = digest_rows(connection.execute("SELECT * FROM " + table))
        # Renewal may legitimately increase expiration; retain all immutable
        # principal, grant and pilot fields and check live expiry separately.
        hashes["scoped_pilot_decisions"] = digest_rows(connection.execute("SELECT decision_id,owner_id,principal_id,binding_id,device_id,endpoint_id,workspace_id,workspace_generation,created_at_ms,revoked_at_ms FROM scoped_pilot_decisions"))
        grant_columns = [row["name"] for row in connection.execute("PRAGMA table_info(mcp_service_grants)") if row["name"] != "expires_at_ms"]
        require(all(re.fullmatch(r"[a-z][a-z0-9_]{0,80}", key) for key in grant_columns), "GRANT_COLUMN_INVALID")
        hashes["mcp_service_grants"] = digest_rows(connection.execute("SELECT " + ",".join(grant_columns) + " FROM mcp_service_grants"))
        hashes["oauth_principals"] = digest_rows(connection.execute("SELECT * FROM oauth_principals"))
        hashes["control_plane_state"] = digest_rows(connection.execute("SELECT * FROM control_plane_state"))
        require(connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "SQLITE_INTEGRITY_FAILED")
        return {"observed_at_ms": now, "database_schema_version": 29, "live_tasks": live_tasks, "live_writers": live_writers,
                "active_actions": active_actions, "historical_unknown_count": len(unknown),
                "poststart_new_work_present": allow_live and bool(live_tasks or live_writers or active_actions), "immutable_row_hashes": hashes}
    finally:
        connection.close()


def same_state(left, right, after_start=False):
    keys = set(left["immutable_row_hashes"])
    if after_start:
        keys -= {"mcp_task_sessions", "mcp_task_writer_leases"}
    return all(left["immutable_row_hashes"][key] == right["immutable_row_hashes"][key] for key in keys)


def update_pinned_pythonpath(paths, previous, candidate):
    """Replace only exact old-source PYTHONPATH entries in protected configs."""
    old, new = str(previous / "control-plane"), str(candidate / "control-plane")
    changed = 0
    for path, _original in paths.values():
        content = protected(path)
        text = content.decode()
        lines = text.splitlines(keepends=True)
        matches = []
        for index, line in enumerate(lines):
            body = line.rstrip("\r\n")
            match = re.fullmatch(r"(\s*(?:Environment=)?PYTHONPATH=)(.*)", body)
            if match:
                require(match.group(2) == old, "PYTHONPATH_CONFIG_NOT_EXACT_BASELINE")
                matches.append((index, match.group(1)))
        require(len(matches) <= 1, "DUPLICATE_PYTHONPATH_CONFIG")
        for index, prefix in matches:
            newline = "\r\n" if lines[index].endswith("\r\n") else "\n" if lines[index].endswith("\n") else ""
            lines[index] = prefix + new + newline
            changed += 1
        if matches:
            atomic(path, "".join(lines).encode())
    # The launcher may derive the package through the current symlink instead.
    # In that case no explicit pin exists and postflight still requires the
    # actual process PYTHONPATH to resolve to the exact candidate.
    return changed


def health_and_contract(expected_package, expected_contract):
    with urllib.request.urlopen("https://svhome.tail0e4032.ts.net/healthz", timeout=5) as response:
        health = json.loads(response.read(65536))
    require(health.get("ok") is True and health.get("package_source_sha256") == health.get("expected_package_source_sha256") == expected_package and health.get("schema_version") == 29, "HEALTH_PACKAGE_NOT_PROVEN")
    pid, active, environment = identity()
    require(pid > 1 and active == "active" and environment is not None, "SERVICE_NOT_RUNNING")
    credential = Path.home() / ".config/codex-control-plane/ubuntu-root-mcp-authorization"
    token = protected(credential).decode().strip().removeprefix("Bearer ")
    require(bool(re.fullmatch(r"mcpsvc_[A-Za-z0-9_-]{32,128}", token)), "MCP_CREDENTIAL_FORMAT_INVALID")
    port = int(environment.get("CONTROL_PLANE_MCP_PORT", "8766"))
    require(environment.get("CONTROL_PLANE_MCP_BIND", "127.0.0.1") == "127.0.0.1" and 1024 <= port <= 65535, "MCP_LOOPBACK_INVALID")
    params = {"name": "workspace_context", "arguments": {"operation": "inventory"}, "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}}
    request = urllib.request.Request(f"http://127.0.0.1:{port}/mcp", method="POST", headers={"Authorization": "Bearer " + token, "Content-Type": "application/json", "Accept": "application/json", "MCP-Protocol-Version": "2026-07-28", "Mcp-Method": "tools/call", "Mcp-Name": "workspace_context"}, data=json.dumps({"jsonrpc": "2.0", "id": "native-overlay-postflight", "method": "tools/call", "params": params}).encode())
    with urllib.request.urlopen(request, timeout=5) as response:
        rpc = json.loads(response.read(196608))
    require("error" not in rpc and rpc.get("result", {}).get("isError") is not True, "MCP_POSTFLIGHT_FAILED")
    inventory = rpc["result"]["structuredContent"]
    require(inventory["tool_contract"] == expected_contract and inventory.get("workspace_accessed") is False, "SCHEMA32_CONTRACT_DRIFT")
    return {"ok": True, "service_pid": pid, "schema_version": 29, "package_source_sha256": expected_package,
            "facade_contract": inventory["tool_contract"], "inventory_binding_ids": [target["binding_id"] for target in inventory.get("targets", [])],
            "service_instance_id": health.get("service_instance_id")}


def await_health(package, contract, deadline_seconds=25):
    deadline = time.monotonic() + deadline_seconds
    while time.monotonic() < deadline:
        try:
            return health_and_contract(package, contract)
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("POSTFLIGHT_HEALTH_OR_SCHEMA32_NOT_PROVEN")


def inspect_archive(archive, name, approved):
    with tarfile.open(archive, "r:gz") as bundle:
        seen, total = set(), 0
        for member in bundle.getmembers():
            path = PurePosixPath(member.name)
            require(not path.is_absolute() and path.parts and path.parts[0] == name and ".." not in path.parts
                    and member.name not in seen and (member.isdir() or member.isfile()) and member.mode & 0o7000 == 0
                    and member.size <= 16777216, "ARCHIVE_MEMBER_INVALID")
            seen.add(member.name)
            total += member.size
            require(total <= 33554432 and len(seen) <= 500, "ARCHIVE_BOUND_EXCEEDED")
        manifest_bytes = bundle.extractfile(name + "/release-manifest.json").read()
        require(sha(manifest_bytes) == approved["candidate_manifest_sha256"], "CANDIDATE_MANIFEST_CHANGED")
        manifest = json.loads(manifest_bytes)
        expected_files = {name + "/" + record["path"] for record in manifest["files"]} | {name + "/release-manifest.json"}
        actual_files = {member.name for member in bundle.getmembers() if member.isfile()}
        require(actual_files == expected_files, "ARCHIVE_FILE_SET_DRIFT")
        for record in manifest["files"]:
            content = bundle.extractfile(name + "/" + record["path"]).read()
            require(len(content) == record["size_bytes"] and sha(content) == record["sha256"], "ARCHIVE_CONTENT_DRIFT")


def main():
    global STAGE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    receipt_path = Path(args.receipt).resolve()
    approved = json.loads(protected(receipt_path))
    base = Path.home() / ".local/lib/codex-control-plane"
    releases, current = base / "releases", base / "current"
    previous = Path(approved["baseline_release_root"]).resolve()
    name = approved["verification"]["release_name"]
    require(bool(re.fullmatch(r"codex-control-plane-native-first-1012-[a-f0-9]{12}", name)), "CANDIDATE_NAME_INVALID")
    candidate, archive = releases / name, releases / (name + ".tar.gz")
    require(receipt_path.parent == releases and previous.parent == releases and not previous.is_symlink(), "RELEASE_PATH_INVALID")
    require(current.is_symlink() and current.resolve() == previous, "CURRENT_RELEASE_CHANGED")
    require(sha((previous / "release-manifest.json").read_bytes()) == approved["baseline_manifest_sha256"], "BASELINE_MANIFEST_DRIFT")
    require(sha(protected(archive, 33554432)) == approved["candidate_archive_sha256"], "CANDIDATE_ARCHIVE_CHANGED")
    old_config = {}
    for key, item in approved["protected_config_hashes"].items():
        path = Path(item["path"])
        require(path.is_relative_to(Path.home()), "PROTECTED_CONFIG_PATH_INVALID")
        content = protected(path)
        require(sha(content) == item["sha256"], "PROTECTED_CONFIG_CHANGED")
        old_config[key] = (path, content)
    pid, active, environment = identity()
    require(pid == approved["baseline_service_pid"] and active == "active", "BASELINE_SERVICE_CHANGED")
    require(environment.get("PYTHONPATH") == str(previous / "control-plane") and environment.get("CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256") == approved["baseline_package_source_sha256"], "SERVING_SOURCE_CHANGED")
    database = Path(environment["CONTROL_PLANE_DB"])
    if not database.is_absolute():
        database = Path(f"/proc/{pid}/cwd").resolve() / database
    database = database.resolve()
    verified_previous = load("native_baseline_verifier", previous / "deploy/control-plane-verify-release.py").verify_release(previous)
    require(verified_previous["package_source_sha256"] == approved["baseline_package_source_sha256"], "BASELINE_SOURCE_INTEGRITY_FAILED")
    inspect_archive(archive, name, approved)
    before = census(database, approved)
    old_health = health_and_contract(approved["baseline_package_source_sha256"], approved["expected_contract"])
    if not args.execute:
        print(json.dumps({"operation": "native_first_overlay_readonly_preflight", "ok": True, "stage": STAGE,
                          "baseline_service_pid": pid, "candidate_release": str(candidate), "changed_files": approved["changed_runtime_files"],
                          "census": before, "health": old_health, "external_mutations_performed": False}, separators=(",", ":")))
        return
    os.umask(0o077)
    lock_path = base / ".native-first-deployment.lock"
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    service_stopped, switch_attempted, candidate_start_attempted, source_identity_proven, backup_dir = False, False, False, False, None
    try:
        STAGE = "stage_verified_immutable_candidate"
        require(not candidate.exists(), "CANDIDATE_RELEASE_ALREADY_EXISTS")
        with tarfile.open(archive, "r:gz") as bundle:
            for member in bundle.getmembers():
                destination = releases / member.name
                if member.isdir():
                    destination.mkdir(mode=0o700, parents=True, exist_ok=True)
                else:
                    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                    with bundle.extractfile(member) as source, destination.open("xb") as output:
                        output.write(source.read())
                    destination.chmod(0o700 if member.mode & 0o111 else 0o600)
        verified = load("native_candidate_verifier", candidate / "deploy/control-plane-verify-release.py").verify_release(candidate)
        require(verified == approved["verification"], "CANDIDATE_IDENTITY_DRIFT")
        old_manifest = json.loads((previous / "release-manifest.json").read_bytes())
        new_manifest = json.loads((candidate / "release-manifest.json").read_bytes())
        require([record["path"] for record in old_manifest["files"]] == [record["path"] for record in new_manifest["files"]], "CANDIDATE_FILE_SET_DRIFT")
        changed = [new["path"] for old, new in zip(old_manifest["files"], new_manifest["files"]) if old != new]
        require(changed == approved["changed_runtime_files"] == ["control-plane/control_plane/mcp_facade.py", "control-plane/control_plane/node_agent.py"], "UNAPPROVED_SOURCE_DELTA")
        require(identity()[0] == pid and current.resolve() == previous, "SERVICE_CHANGED_BEFORE_STOP")
        require(same_state(before, census(database, approved)), "CAUSAL_STATE_CHANGED_BEFORE_STOP")
        STAGE = "stop_exact_service_then_final_census"
        systemctl("stop")
        service_stopped = True
        require(identity()[0] == 0 and identity()[1] == "inactive", "SERVICE_STOP_NOT_PROVEN")
        stopped = census(database, approved)
        require(same_state(before, stopped), "NEW_WORK_ARRIVED_BEFORE_SERVICE_STOP")
        # With ingress stopped, no new task/action can be admitted by this
        # service between this independent census and source activation.
        STAGE = "protected_snapshot_and_config_backup"
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + str(os.getpid())
        backup_dir = base / "backups" / ("native-first-" + stamp)
        backup_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
        source_db = connect(database)
        snapshot = backup_dir / "control-plane-before.sqlite3"
        target_db = sqlite3.connect(snapshot)
        try:
            source_db.backup(target_db)
            require(target_db.execute("PRAGMA integrity_check").fetchone()[0] == "ok" and target_db.execute("PRAGMA user_version").fetchone()[0] == 29, "READONLY_BACKUP_INTEGRITY_FAILED")
        finally:
            target_db.close()
            source_db.close()
        snapshot.chmod(0o600)
        for key, (path, content) in old_config.items():
            require(protected(path) == content, "CONFIG_CHANGED_AFTER_STOP")
            atomic(backup_dir / (key + ".before"), content)
        rollback = {"previous_release": str(previous), "candidate_release": str(candidate), "previous_package": approved["baseline_package_source_sha256"], "candidate_package": verified["package_source_sha256"], "expected_contract": approved["expected_contract"], "config_hashes_before": approved["protected_config_hashes"], "source_only_rollback": True, "database_restore_allowed": False, "authority_mutation_allowed": False, "stopped_census": stopped}
        atomic(backup_dir / "rollback-manifest.json", json.dumps(rollback, indent=2).encode())
        require(same_state(stopped, census(database, approved)), "CAUSAL_STATE_CHANGED_WHILE_STOPPED")
        STAGE = "official_config_and_source_switch"
        switch_attempted = True
        activation = load("native_source_activation", candidate / "deploy/prepare-control-plane-activation.py")
        activation.prepare_activation_config(release_dir=candidate, env_file=old_config["environment"][0], drop_in=old_config["drop_in"][0])
        explicit_pythonpath_updates = update_pinned_pythonpath(old_config, previous, candidate)
        current_link(current, candidate)
        systemctl("daemon-reload")
        STAGE = "start_candidate_and_verify"
        candidate_start_attempted = True
        systemctl("start")
        service_stopped = False
        new_health = await_health(verified["package_source_sha256"], approved["expected_contract"])
        new_pid, new_active, new_environment = identity()
        require(new_pid != pid and new_active == "active" and new_environment.get("PYTHONPATH") == str(candidate / "control-plane") and current.resolve() == candidate, "NEW_SOURCE_IDENTITY_NOT_PROVEN")
        source_identity_proven = True
        post = census(database, approved, allow_live=True)
        require(same_state(stopped, post, after_start=True), "PRESERVED_AUTHORITY_OR_HISTORY_CHANGED_AFTER_START")
        print(json.dumps({"operation": "native_first_prerequisite_metadata_deployment", "ok": True,
            "old_service_pid": pid, "new_service_pid": new_pid, "release": name, "package_source_sha256": verified["package_source_sha256"],
            "changed_runtime_files": changed, "unchanged_release_files": approved["unchanged_release_files"], "health": new_health,
            "final_census": post, "historical_unknown_receipts_preserved": True, "authority_and_history_unchanged": True,
            "protected_backup_directory": str(backup_dir), "backup_sqlite_sha256": sha(snapshot.read_bytes()),
            "source_only_rollback_prepared": True, "database_restored": False, "authority_mutated": False,
            "explicit_pythonpath_config_updates": explicit_pythonpath_updates,
            "service_operation": "stop then start exact codex-control-plane.service", "external_mutations_performed": True,
            "completed_at_ms": int(time.time() * 1000)}, separators=(",", ":")))
    except Exception as error:
        failure_stage = STAGE
        code = str(error) if isinstance(error, RuntimeError) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,95}", str(error)) else type(error).__name__
        rollback_verified, rollback_blocked_by_work = False, False
        try:
            if candidate_start_attempted:
                # Ordinary work can arrive once the verified service resumes.
                # Any later audit discrepancy needs review, not an automatic
                # second stop that could interrupt the new task or command.
                rollback_blocked_by_work = True
            elif switch_attempted:
                require(identity()[0] == 0 and identity()[1] == "inactive", "SOURCE_ROLLBACK_REQUIRES_STOPPED_SERVICE")
            if switch_attempted and service_stopped and not rollback_blocked_by_work:
                for path, content in old_config.values():
                    atomic(path, content)
                current_link(current, previous)
                systemctl("daemon-reload")
            if service_stopped and not candidate_start_attempted:
                systemctl("start")
                service_stopped = False
            if not rollback_blocked_by_work:
                restored = await_health(approved["baseline_package_source_sha256"], approved["expected_contract"])
                rollback_verified = current.resolve() == previous and restored["ok"] is True
        except Exception:
            rollback_verified = False
        print(json.dumps({"operation": "native_first_prerequisite_metadata_deployment", "ok": False, "stage": failure_stage,
                          "error_code": code, "source_only_rollback_verified": rollback_verified,
                          "source_identity_proven": source_identity_proven, "automatic_rollback_withheld_to_preserve_work": rollback_blocked_by_work,
                          "database_restored": False, "authority_mutated": False, "external_mutations_performed": True,
                          "operator_action": "Inspect source/config/service and preserved causal history; no database restore or action replay."}, separators=(",", ":")))
        sys.exit(2)
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,95}", str(error)) else type(error).__name__
        print(json.dumps({"operation": "native_first_overlay_preflight", "ok": False, "stage": STAGE,
                          "error_code": code, "external_mutations_performed": False}, separators=(",", ":")))
        sys.exit(1)
