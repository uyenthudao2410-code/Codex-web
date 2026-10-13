"""Additive read-only Ubuntu Native-First readiness observer.

Run over SSH stdin with python3 -B -. Credentials and process environment stay
in memory. Only allowlisted projections and content digests leave the server.
No dispatch, authority changes, renewal, service mutation or DB writes.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import subprocess
import sys
import time
import urllib.request

DEVICE = "4c4b7a5b-7744-49ae-a490-78a528a00471"
SCOPES = {
    "Codex-web": ("workspace_f93b5bac9dc74fae9cea66f44c4ebc94", "generation_a420c8bfcfcb4e42b5bb7fc5e5cec097"),
    "Autocad": ("workspace_bc86004be2684b958ab7a9a6f9530cd7", "generation_03f9c04f1b14414fa4bfa7d91cc8ea7a"),
}
EXPECTED_CONTRACT_SHA256 = "3664b70740d8d7359a3605b5ce42d7cbf3329e27dcfeec27d22b23ec9c631f66"
ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
SHA = re.compile(r"^[a-f0-9]{64}$")
SERVICE = "codex-control-plane.service"


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def show(unit, fields):
    result = subprocess.run(["systemctl", "--user", "show", unit,
                             *("--property=" + field for field in fields)],
                            capture_output=True, text=True, timeout=10, check=False)
    require(result.returncode == 0, "SYSTEMD_SHOW_FAILED")
    require(len(result.stdout.encode()) <= 16384, "SYSTEMD_SHOW_TOO_LARGE")
    return {key: value for line in result.stdout.splitlines() if "=" in line
            for key, value in [line.split("=", 1)] if key in fields}


def identifier(value):
    require(isinstance(value, str) and ID.fullmatch(value), "IDENTIFIER_INVALID")
    return value


def projection(row):
    """SQL callers explicitly select identifiers, enum states and timestamps."""
    result = dict(row)
    for key, value in result.items():
        if key.endswith("_id") or key.endswith("_generation"):
            if value is not None and not isinstance(value, int):
                identifier(value)
        elif isinstance(value, str):
            require(bool(re.fullmatch(r"[A-Za-z0-9_./:-]{0,160}", value)), "PROJECTION_VALUE_INVALID")
    return result


def json_response(request, maximum=196608):
    with urllib.request.urlopen(request, timeout=10) as response:
        raw = response.read(maximum + 1)
    require(len(raw) <= maximum, "READONLY_RESPONSE_TOO_LARGE")
    result = json.loads(raw)
    require(isinstance(result, dict), "READONLY_RESPONSE_NOT_OBJECT")
    return result


def rpc(port, method, params, token, name=None):
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json",
               "Accept": "application/json", "MCP-Protocol-Version": "2026-07-28", "Mcp-Method": method}
    if name:
        headers["Mcp-Name"] = name
    params = {**params, "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
                                 "io.modelcontextprotocol/clientCapabilities": {}}}
    request = urllib.request.Request(f"http://127.0.0.1:{port}/mcp", method="POST", headers=headers,
        data=json.dumps({"jsonrpc": "2.0", "id": "native-first-readiness", "method": method,
                         "params": params}, separators=(",", ":")).encode())
    response = json_response(request)
    require("error" not in response and response.get("id") == "native-first-readiness", "READONLY_MCP_RPC_FAILED")
    result = response.get("result")
    require(isinstance(result, dict) and result.get("isError") is not True, "READONLY_MCP_RESULT_INVALID")
    return result


def census(connection, now, workspace=None, generation=None):
    terms, values = ["device_id=?"], [DEVICE]
    if workspace is not None:
        terms.extend(["workspace_id=?", "workspace_generation=?"])
        values.extend([workspace, generation])
    predicate = " AND ".join(terms)
    def count(sql, extra=()):
        return connection.execute(sql, (*values, *extra)).fetchone()[0]
    tasks = count(f"SELECT COUNT(*) FROM mcp_task_sessions WHERE {predicate} AND closed_at_ms IS NULL")
    live_tasks = count(f"SELECT COUNT(*) FROM mcp_task_sessions WHERE {predicate} AND closed_at_ms IS NULL AND expires_at_ms>?", (now,))
    writer_predicate = " AND ".join("t." + term for term in terms)
    writer_query = "SELECT COUNT(*) FROM mcp_task_writer_leases l JOIN mcp_task_sessions t ON t.task_id=l.task_id "
    writers = count(writer_query + f"WHERE {writer_predicate} AND l.released_at_ms IS NULL")
    live_writers = count(writer_query + f"WHERE {writer_predicate} AND l.released_at_ms IS NULL AND l.expires_at_ms>?", (now,))
    states = {row["delivery_state"]: row["n"] for row in connection.execute(
        f"SELECT delivery_state,COUNT(*) n FROM actions WHERE {predicate} AND settled_at_ms IS NULL GROUP BY delivery_state", values)}
    require(all(ID.fullmatch(key) for key in states), "ACTION_STATE_INVALID")
    return {"unclosed_tasks": tasks, "live_open_tasks": live_tasks, "expired_unclosed_tasks": tasks - live_tasks,
            "unreleased_writers": writers, "live_writers": live_writers, "expired_unreleased_writers": writers - live_writers,
            "unsettled_actions": sum(states.values()), "unsettled_by_delivery_state": states,
            "queued_actions": states.get("queued", 0),
            "active_dispatch_actions": sum(states.get(key, 0) for key in ("dispatch_unconfirmed", "accepted")),
            "reconciliation_required_actions": states.get("reconcile_required", 0)}


def source_manifest(root, environment):
    # systemd may keep cwd=$HOME and choose the immutable package via PYTHONPATH.
    candidates = [root / "control_plane", root / "control-plane/control_plane"]
    for value in environment.get("PYTHONPATH", "").split(":"):
        if value:
            path = Path(value).resolve()
            require(path.is_relative_to(Path.home().resolve()), "PYTHONPATH_OUTSIDE_HOME")
            candidates.append(path / "control_plane")
    packages = {path.resolve() for path in candidates if (path / "http_api.py").is_file()}
    require(len(packages) == 1, "SERVING_PACKAGE_NOT_UNIQUE")
    package = packages.pop()
    files, aggregate = {}, hashlib.sha256()
    for path in sorted(package.glob("*.py")):
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).digest()
            files[path.name] = digest.hex()
            aggregate.update(path.name.encode() + b"\0" + digest + b"\0")
    auxiliary = {}
    for name in ("recovery_exec_bridge.cjs", "recovery_file_bridge.cjs", "recovery_patch_bridge.cjs"):
        path = package / name
        if path.is_file():
            auxiliary[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    release = package.parent.parent
    manifest_path = release / "release-manifest.json"
    require(manifest_path.is_file() and manifest_path.stat().st_size <= 131072, "RELEASE_MANIFEST_UNAVAILABLE")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    records = manifest.get("files")
    require(isinstance(records, list) and 1 <= len(records) <= 200, "RELEASE_MANIFEST_FILES_INVALID")
    safe_records, seen = [], set()
    for record in records:
        relative, expected, size = record.get("path"), record.get("sha256"), record.get("size_bytes")
        require(isinstance(relative, str) and re.fullmatch(r"[A-Za-z0-9_./-]{1,200}", relative)
                and not relative.startswith("/") and ".." not in Path(relative).parts
                and relative not in seen and SHA.fullmatch(expected or "")
                and isinstance(size, int) and 0 <= size <= 16777216, "RELEASE_MANIFEST_RECORD_INVALID")
        path = release / relative
        require(path.is_file() and not path.is_symlink() and path.stat().st_size == size
                and hashlib.sha256(path.read_bytes()).hexdigest() == expected, "SERVING_RELEASE_FILE_DRIFT")
        seen.add(relative)
        safe_records.append({"path": relative, "sha256": expected, "size_bytes": size})
    return {"process_working_directory": str(root), "package_root": str(package),
            "serving_release_root": str(package.parent.parent), "python_files_sha256": files,
            "package_source_sha256": "sha256:" + aggregate.hexdigest(), "auxiliary_files_sha256": auxiliary,
            "release_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "release_manifest_files": safe_records, "release_file_integrity_verified": True}


def main():
    capture_started = int(time.time() * 1000)
    service = show(SERVICE, ["MainPID", "ActiveState", "SubState", "FragmentPath", "DropInPaths"])
    pid = int(service["MainPID"])
    require(pid > 1 and service["ActiveState"] == "active", "CONTROL_PLANE_NOT_RUNNING")
    environment = dict(item.split("=", 1) for item in Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in item)
    root = Path(f"/proc/{pid}/cwd").resolve()
    require(root.is_relative_to(Path.home().resolve()), "SERVING_ROOT_OUTSIDE_HOME")
    source = source_manifest(root, environment)
    module = None
    cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
    if b"-m" in cmdline:
        module = cmdline[cmdline.index(b"-m") + 1].decode()
        require(bool(re.fullmatch(r"control_plane(?:\.[A-Za-z_][A-Za-z0-9_]*)?", module)), "SERVING_MODULE_UNEXPECTED")
    source["process_module"] = module
    source["cmdline_sha256"] = hashlib.sha256(Path(f"/proc/{pid}/cmdline").read_bytes()).hexdigest()
    source["unit_files_sha256"] = {}
    for value in [service.get("FragmentPath", ""), *service.get("DropInPaths", "").split()]:
        if value:
            path = Path(value).resolve()
            require(path.is_relative_to(Path.home().resolve()) and path.is_file(), "UNIT_PATH_UNEXPECTED")
            source["unit_files_sha256"][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    protected_config_hashes = {}
    env_file = Path.home() / ".config/codex-control-plane/control-plane.env"
    drop_in = Path.home() / ".config/systemd/user/codex-control-plane.service.d/10-immutable-release.conf"
    for name, path in (("environment", env_file), ("drop_in", drop_in)):
        metadata = path.lstat()
        require(stat.S_ISREG(metadata.st_mode) and metadata.st_uid == os.getuid()
                and metadata.st_mode & 0o077 == 0 and metadata.st_size <= 131072, "ACTIVATION_CONFIGURATION_NOT_PROTECTED")
        protected_config_hashes[name] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    current = Path.home() / ".local/lib/codex-control-plane/current"
    require(current.is_symlink() and current.resolve() == Path(source["serving_release_root"]), "CURRENT_RELEASE_LINK_DISAGREES")
    source["current_release_link"] = str(current)
    principal = identifier(environment.get("CONTROL_PLANE_MCP_SERVICE_PRINCIPAL_ID"))
    grant_id = identifier(environment.get("CONTROL_PLANE_MCP_SERVICE_GRANT_ID"))
    require(environment.get("CONTROL_PLANE_MCP_AUTH_MODE") == "private_tunnel_service", "MCP_AUTH_MODE_UNEXPECTED")
    require(environment.get("CONTROL_PLANE_MCP_BIND", "127.0.0.1") == "127.0.0.1", "MCP_NOT_LOOPBACK")
    port = int(environment.get("CONTROL_PLANE_MCP_PORT", "8766"))
    require(1024 <= port <= 65535, "MCP_PORT_INVALID")
    credential = Path.home() / ".config/codex-control-plane/ubuntu-root-mcp-authorization"
    metadata = credential.lstat()
    require(stat.S_ISREG(metadata.st_mode) and metadata.st_uid == os.getuid()
            and metadata.st_mode & 0o077 == 0 and metadata.st_size <= 65536, "CREDENTIAL_NOT_PROTECTED")
    token = credential.read_text().strip().removeprefix("Bearer ")
    require(bool(re.fullmatch(r"mcpsvc_[A-Za-z0-9_-]{32,128}", token)), "CREDENTIAL_FORMAT_INVALID")
    inventory = rpc(port, "tools/call", {"name": "workspace_context", "arguments": {"operation": "inventory"}}, token, "workspace_context")["structuredContent"]
    tools = rpc(port, "tools/list", {}, token)["tools"]
    require(inventory.get("principal_id") == principal and inventory.get("workspace_accessed") is False, "INVENTORY_AUTHORITY_DISAGREES")
    contract = inventory["tool_contract"]
    require(isinstance(contract.get("schema_version"), int) and SHA.fullmatch(contract.get("sha256", "")), "CONTRACT_FORMAT_INVALID")
    targets = []
    for target in inventory.get("targets", []):
        keys = ("binding_id", "device_id", "endpoint_id", "workspace_id", "workspace_generation",
                "binding_state", "workspace_state", "node_state", "readiness", "presence_state", "dispatch_state")
        targets.append(projection({key: target.get(key) for key in keys}))
    database = Path(environment["CONTROL_PLANE_DB"])
    if not database.is_absolute():
        database = root / database
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    connection.row_factory = sqlite3.Row
    now = int(time.time() * 1000)
    connection.execute("BEGIN")
    database_schema_version = connection.execute("PRAGMA user_version").fetchone()[0]
    global_active_scope_census = {}
    for label, sql in (
        ("live_open_tasks", "SELECT device_id,workspace_id,workspace_generation,COUNT(*) n FROM mcp_task_sessions WHERE closed_at_ms IS NULL AND expires_at_ms>? GROUP BY device_id,workspace_id,workspace_generation"),
        ("live_writers", "SELECT t.device_id,t.workspace_id,t.workspace_generation,COUNT(*) n FROM mcp_task_writer_leases l JOIN mcp_task_sessions t ON t.task_id=l.task_id WHERE l.released_at_ms IS NULL AND l.expires_at_ms>? GROUP BY t.device_id,t.workspace_id,t.workspace_generation"),
    ):
        global_active_scope_census[label] = [projection(row) for row in connection.execute(sql, (now,))]
    global_active_scope_census["active_actions"] = [projection(row) for row in connection.execute("SELECT device_id,workspace_id,workspace_generation,delivery_state,COUNT(*) n FROM actions WHERE settled_at_ms IS NULL AND delivery_state IN ('queued','dispatch_unconfirmed','accepted') GROUP BY device_id,workspace_id,workspace_generation,delivery_state")]
    global_active_scope_census["blocking_action_identities"] = [projection(row) for row in connection.execute("SELECT action_id,device_id,workspace_id,workspace_generation,tool_name,delivery_state,created_at_ms,expires_at_ms FROM actions WHERE settled_at_ms IS NULL AND delivery_state IN ('queued','dispatch_unconfirmed','accepted') ORDER BY created_at_ms,action_id LIMIT 50")]
    for action in global_active_scope_census["blocking_action_identities"]:
        action["expired"] = action["expires_at_ms"] <= now
    node_row = connection.execute("SELECT device_id,owner_id,endpoint_id,readiness,runtime_instance_id,mcp_server_instance_id,activation_epoch,contract_version,last_seen_at_ms,revoked_at_ms,policy_state,policy_expires_at_ms,policy_sha256,policy_observed_at_ms FROM nodes WHERE device_id=?", (DEVICE,)).fetchone()
    require(node_row is not None, "EXPECTED_NODE_NOT_REGISTERED")
    node = projection(node_row)
    node["heartbeat_age_ms"] = now - node["last_seen_at_ms"] if isinstance(node["last_seen_at_ms"], int) else None
    node["heartbeat_fresh_60000_ms"] = node["heartbeat_age_ms"] is not None and 0 <= node["heartbeat_age_ms"] <= 60000
    grant_row = connection.execute("SELECT grant_id,owner_id,principal_id,scopes_json,created_at_ms,expires_at_ms,revoked_at_ms FROM mcp_service_grants WHERE grant_id=?", (grant_id,)).fetchone()
    require(grant_row is not None, "SERVICE_GRANT_NOT_FOUND")
    grant_data = dict(grant_row)
    scopes = json.loads(grant_data.pop("scopes_json"))
    require(isinstance(scopes, list) and all(isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9_:.-]{1,80}", item) for item in scopes), "GRANT_SCOPES_INVALID")
    grant = projection(grant_data)
    grant["scopes"] = scopes
    grant["live"] = grant["revoked_at_ms"] is None and grant["expires_at_ms"] > now
    owner = identifier(node["owner_id"])
    require(grant["owner_id"] == owner and grant["principal_id"] == principal, "SERVICE_GRANT_NODE_DISAGREES")
    bindings = [projection(row) for row in connection.execute("SELECT binding_id,owner_id,device_id,endpoint_id,workspace_id,workspace_generation,created_at_ms,revoked_at_ms FROM bindings WHERE owner_id=? AND device_id=? ORDER BY created_at_ms,binding_id", (owner, DEVICE))]
    registrations = [projection(row) for row in connection.execute("SELECT device_id,workspace_id,workspace_generation,registered_at_ms,retired_at_ms FROM node_workspaces WHERE device_id=? ORDER BY registered_at_ms,workspace_id", (DEVICE,))]
    pilots = [projection(row) for row in connection.execute("SELECT decision_id,owner_id,principal_id,binding_id,device_id,endpoint_id,workspace_id,workspace_generation,created_at_ms,expires_at_ms,revoked_at_ms FROM scoped_pilot_decisions WHERE owner_id=? AND revoked_at_ms IS NULL AND expires_at_ms>? ORDER BY created_at_ms", (owner, now))]
    whole_device = census(connection, now)
    scoped = {}
    # Invoke only the actual serving store's pure SQL continuity predicate on
    # our read-only snapshot. Bypass its constructor, which owns migrations.
    sys.path.insert(0, str(Path(source["package_root"]).parent))
    from control_plane.store import ControlPlaneStore
    continuity = object.__new__(ControlPlaneStore)
    continuity.clock = lambda: now
    for name, (workspace, generation) in SCOPES.items():
        counts = census(connection, now, workspace, generation)
        current_bindings = [item for item in bindings if item["workspace_id"] == workspace and item["workspace_generation"] == generation and item["revoked_at_ms"] is None]
        current_registrations = [item for item in registrations if item["workspace_id"] == workspace and item["workspace_generation"] == generation and item["retired_at_ms"] is None]
        current_targets = [item for item in targets if item["workspace_id"] == workspace and item["workspace_generation"] == generation]
        blocking_count = continuity._blocking_unresolved_action_count_for_pilot(
            connection, device_id=DEVICE, owner_id=owner, principal_id=principal,
            binding_id=current_bindings[0]["binding_id"] if len(current_bindings) == 1 else "bind_unavailable",
            workspace_id=workspace, workspace_generation=generation,
        )
        scoped[name] = {"expected_workspace_id": workspace, "expected_generation": generation,
                        "active_bindings": current_bindings, "active_registrations": current_registrations,
                        "delegated_inventory_targets": current_targets, "census": counts,
                        "exact_scope_idle": counts["unclosed_tasks"] == counts["unreleased_writers"] == counts["unsettled_actions"] == 0,
                        "serving_activation_unresolved_action_blockers": blocking_count}
    unknown = [projection(row) for row in connection.execute("SELECT a.action_id,a.binding_id,a.workspace_id,a.workspace_generation,a.tool_name,a.delivery_state,a.created_at_ms,a.expires_at_ms,a.settled_at_ms,r.disposition,r.reconciled_at_ms,l.task_id FROM actions a LEFT JOIN action_reconciliations r ON r.action_id=a.action_id LEFT JOIN mcp_task_action_links l ON l.action_id=a.action_id WHERE a.device_id=? AND a.settled_at_ms IS NULL AND a.delivery_state='reconcile_required' ORDER BY a.created_at_ms,a.action_id LIMIT 100", (DEVICE,))]
    for action in unknown:
        action["expected_current_scope"] = next((name for name, values in SCOPES.items() if values == (action["workspace_id"], action["workspace_generation"])), None)
        action["expired"] = action["expires_at_ms"] <= now
        action["delivery_attempts"] = [projection(row) for row in connection.execute("SELECT attempt_id,attempt_number,dispatched_at_ms FROM delivery_attempts WHERE action_id=? ORDER BY attempt_number", (action["action_id"],))]
        action["receipts"] = []
        for row in connection.execute("SELECT receipt_id,receipt_state,receipt_digest,received_at_ms,local_handle,payload_json FROM receipts WHERE action_id=? ORDER BY received_at_ms,receipt_id", (action["action_id"],)):
            data = dict(row)
            raw, handle = data.pop("payload_json"), data.pop("local_handle")
            receipt = projection(data)
            receipt["local_handle_sha256"] = hashlib.sha256(handle.encode()).hexdigest() if handle else None
            payload = json.loads(raw)
            require(isinstance(payload, dict), "HISTORICAL_RECEIPT_NOT_OBJECT")
            receipt["payload_sha256"] = hashlib.sha256(raw.encode()).hexdigest()
            receipt["payload_keys"] = [identifier(key) for key in payload]
            receipt["safe_diagnostics"] = {}
            for key in ("code", "diagnostic_code"):
                value = payload.get(key)
                if isinstance(value, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,95}", value):
                    receipt["safe_diagnostics"][key] = value
            kind = payload.get("operation_kind")
            if isinstance(kind, str) and re.fullmatch(r"[a-z][a-z0-9_]{2,95}", kind):
                receipt["safe_diagnostics"]["operation_kind"] = kind
            action["receipts"].append(receipt)
    admission_row = connection.execute("SELECT state_value AS admission_mode,changed_at_ms FROM control_plane_state WHERE state_key='admission_mode'").fetchone()
    admission = projection(admission_row) if admission_row is not None else {"admission_mode": "unconfigured"}
    integrity = connection.execute("PRAGMA integrity_check").fetchall()
    integrity_ok = len(integrity) == 1 and integrity[0][0] == "ok"
    connection.close()
    health = json_response("https://svhome.tail0e4032.ts.net/healthz", 65536)
    safe_health = {key: health.get(key) for key in ("ok", "schema_version", "declared_source_revision", "package_source_sha256", "expected_package_source_sha256", "service_instance_id")}
    for key, value in safe_health.items():
        if isinstance(value, str):
            require(bool(re.fullmatch(r"[A-Za-z0-9_:-]{1,160}", value)), "HEALTH_PROJECTION_INVALID")
    try:
        with urllib.request.urlopen("http://127.0.0.1:8768/readyz", timeout=5) as response:
            tunnel = {"ready": response.status == 200, "status": response.status}
    except Exception as error:
        tunnel = {"ready": False, "status": getattr(error, "code", None), "error_class": type(error).__name__}
    renewal = {"service": show("codex-control-plane-authority-renewal.service", ["ActiveState", "SubState", "Result", "ExecMainStatus", "InvocationID"]),
               "timer": show("codex-control-plane-authority-renewal.timer", ["ActiveState", "SubState", "UnitFileState", "NextElapseUSecRealtime", "LastTriggerUSec"])}
    contract_ready = contract["schema_version"] == 32 and contract["sha256"] == EXPECTED_CONTRACT_SHA256
    source_ready = safe_health.get("ok") is True and safe_health.get("package_source_sha256") == source["package_source_sha256"] == safe_health.get("expected_package_source_sha256")
    service_after = show(SERVICE, ["MainPID", "ActiveState", "SubState"])
    service_stable = all(service_after.get(key) == service.get(key) for key in service_after)
    blockers = []
    codex = scoped["Codex-web"]
    if not contract_ready: blockers.append("FACADE_SCHEMA32_CONTRACT_MISMATCH")
    if not source_ready: blockers.append("SERVING_PACKAGE_STARTUP_DISK_ATTESTATION_MISMATCH")
    if not service_stable: blockers.append("SERVICE_CHANGED_DURING_OBSERVATION")
    if not grant["live"]: blockers.append("SERVICE_GRANT_NOT_LIVE")
    if not node["heartbeat_fresh_60000_ms"] or node["readiness"] != "ready": blockers.append("WINDOWS_NODE_NOT_FRESH_READY")
    if not codex["active_bindings"] or not codex["active_registrations"]: blockers.append("CODEX_WEB_CURRENT_SCOPE_NOT_REGISTERED_AND_BOUND")
    if not codex["delegated_inventory_targets"]: blockers.append("CODEX_WEB_NOT_DELEGATED_TO_CURRENT_SERVICE_PRINCIPAL")
    if codex["serving_activation_unresolved_action_blockers"]: blockers.append("CURRENT_AUTOCAD_UNKNOWN_READ_ACTIONS_BLOCK_WORKSPACE_ACTIVATION")
    if not codex["exact_scope_idle"]: blockers.append("CODEX_WEB_CURRENT_SCOPE_NOT_IDLE")
    if whole_device["live_open_tasks"] or whole_device["live_writers"] or whole_device["active_dispatch_actions"] or whole_device["queued_actions"]: blockers.append("DEVICE_HAS_LIVE_OR_DISPATCH_WORK")
    result = {"operation": "native_first_ubuntu_readonly_readiness", "ok": True,
              "capture_started_at_ms": capture_started, "snapshot_at_ms": now, "capture_completed_at_ms": int(time.time() * 1000),
              "service_pid": pid, "service": service, "service_after": service_after, "service_stable": service_stable,
              "serving_source": source, "health": safe_health, "source_startup_disk_attestation_matches": source_ready,
              "protected_activation_config_hashes": protected_config_hashes, "database_schema_version": database_schema_version,
              "tool_contract": contract, "expected_contract_matches": contract_ready,
              "tool_names": [identifier(tool["name"]) for tool in tools],
              "tool_input_properties": {identifier(tool["name"]): [identifier(key) for key in tool["inputSchema"].get("properties", {})] for tool in tools},
              "principal_id": principal, "service_grant": grant, "admission": admission,
              "node": node, "owner_bindings": bindings, "node_workspace_registrations": registrations,
              "live_pilots": pilots, "delegated_inventory_targets": targets, "expected_current_scopes": scoped,
              "whole_device_census": whole_device, "historical_unknown_actions_preserved": unknown,
              "global_live_work_by_scope": global_active_scope_census,
              "unknown_projection_limit": 100, "unknown_projection_truncated": whole_device["reconciliation_required_actions"] > len(unknown),
              "history_note": "UNKNOWN actions remain unresolved evidence; no cleanup, settlement or replay was performed.",
              "renewal": renewal, "tunnel_ready": tunnel, "sqlite_integrity_ok": integrity_ok,
              "codex_web_canary_blockers": blockers, "codex_web_canary_eligible_under_current_authority": not blockers,
              "external_mutations_performed": False, "database_mutations_performed": False,
              "read_only_mcp_methods": ["tools/list", "workspace_context inventory"]}
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,95}", str(error)) else type(error).__name__
        print(json.dumps({"operation": "native_first_ubuntu_readonly_readiness", "ok": False,
                          "error_code": code, "external_mutations_performed": False}, separators=(",", ":")))
        sys.exit(1)
