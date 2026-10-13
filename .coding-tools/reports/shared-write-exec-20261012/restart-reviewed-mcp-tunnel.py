"""Restart the exact existing tunnel after the reviewed server is listening.

Adds the supported 30s startup-listener wait to the protected tunnel env file,
preserving all other bytes, identity, profile and credential references. No
schema publication or ChatGPT catalog refresh is claimed by this operation.
"""
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request

UNIT = "codex-control-plane-mcp-tunnel.service"
TUNNEL = "tunnel_6ab62006b6708191b007d1c6e4a136cf"
PROFILE = "ubuntu-root-mcp-2"
PRINCIPAL = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
GRANT = "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"
PILOT = "pilot_dfb3174078d842299c41c6638830e505"
BINDING = "bind_71661b1046884174b01c99af5f8546aa"
PACKAGE = "sha256:5370e6ce030e72514b664b771f400437d337e7c5eb1c39b1ac90748662c3ceb0"
ENV_SHA = "d66b8f7003efca66ecb3df695bc9f220612ae3dd766e44f468fac6ee35cf472a"
UNIT_SHA = "2aed917a856cd9948665f8b5e10710974cd60fecde739794e079d82b5f9d949c"
CLIENT_SHA = "472eb9dd9dd625b4e6023c3b4a5736b3a2e5a1b6dbe9338e001887a64ec992a6"
PROTOCOL = "2026-07-28"
STAGE = "preflight"


def require(value, code):
    if not value:
        raise RuntimeError(code)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def service_pid(unit):
    return int(subprocess.check_output(["systemctl", "--user", "show", unit, "--property=MainPID", "--value"], text=True).strip())


def environment(pid):
    return dict(item.split("=", 1) for item in Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in item)


def child_and_argv(pid):
    found = []
    for child in Path(f"/proc/{pid}/task/{pid}/children").read_text().split():
        argv = Path(f"/proc/{child}/cmdline").read_bytes().decode().split("\0")
        if "--mcp.server-url" in argv:
            found.append((int(child), argv))
    require(len(found) == 1, "SOLE_CANONICAL_TUNNEL_CHILD_NOT_PROVEN")
    return found[0]


def verify_argv(argv, credential_file):
    required = {
        "--profile": PROFILE, "--control-plane.tunnel-id": TUNNEL,
        "--mcp.server-url": "url=http://127.0.0.1:8766/mcp,channel=main",
        "--mcp.extra-headers": "Authorization: file:" + str(credential_file),
        "--mcp.discovery-extra-headers": "Authorization: file:" + str(credential_file),
    }
    for option, value in required.items():
        require(argv.count(option) == 1 and argv[argv.index(option) + 1] == value, "CANONICAL_TUNNEL_ARGUMENT_CHANGED")


def json_get(path):
    with urllib.request.urlopen("http://127.0.0.1:8768" + path, timeout=3) as response:
        return json.loads(response.read(262144))


def tools_list(token):
    payload = {"jsonrpc": "2.0", "id": "guarded-tunnel-discovery", "method": "tools/list", "params": {
        "_meta": {"io.modelcontextprotocol/protocolVersion": PROTOCOL, "io.modelcontextprotocol/clientCapabilities": {}}
    }}
    request = urllib.request.Request("http://127.0.0.1:8766/mcp", data=json.dumps(payload).encode(), headers={
        "Authorization": "Bearer " + token, "Content-Type": "application/json", "Accept": "application/json",
        "MCP-Protocol-Version": PROTOCOL, "Mcp-Method": "tools/list",
    }, method="POST")
    with urllib.request.urlopen(request, timeout=5) as response:
        result = json.loads(response.read(196608))
    require("error" not in result, "LOCAL_MCP_DISCOVERY_FAILED")
    by_name = {tool["name"]: tool for tool in result["result"]["tools"]}
    require({"operation", "argv", "binding_id", "task_id", "expected_facade_contract"}
            <= set(by_name["exec_command"]["inputSchema"]["properties"]), "EXEC_PARAMETER_SCHEMA_MISSING")
    require(by_name["exec_command"]["inputSchema"]["properties"]["operation"]["enum"] == ["exec_run", "exec_status"],
            "EXEC_OPERATIONS_CHANGED")
    require({"doc_create", "doc_convert"} <= set(by_name["document_workflow"]["inputSchema"]["properties"]["operation"]["enum"]),
            "DOCUMENT_WRITE_OPERATIONS_MISSING")
    return {name: list(by_name[name]["inputSchema"]["properties"]) for name in ("exec_command", "document_workflow")}


def authority_snapshot(connection):
    now = int(time.time() * 1000)
    require(connection.execute("SELECT state_value FROM control_plane_state WHERE state_key='admission_mode'").fetchone()[0] == "scoped_pilot", "ADMISSION_MODE_CHANGED")
    pilots = [dict(row) for row in connection.execute("SELECT * FROM scoped_pilot_decisions ORDER BY decision_id")]
    active = [row for row in pilots if row["revoked_at_ms"] is None and row["expires_at_ms"] > now]
    require(len(active) == 1 and active[0]["decision_id"] == PILOT and active[0]["binding_id"] == BINDING
            and active[0]["principal_id"] == PRINCIPAL and active[0]["expires_at_ms"] > now + 120000,
            "CANONICAL_LIVE_PILOT_CHANGED")
    require(connection.execute("SELECT COUNT(*) FROM mcp_task_sessions WHERE binding_id=? AND closed_at_ms IS NULL", (BINDING,)).fetchone()[0] == 0, "CURRENT_TARGET_HAS_OPEN_TASK")
    require(connection.execute("SELECT COUNT(*) FROM actions WHERE workspace_generation='generation_a420c8bfcfcb4e42b5bb7fc5e5cec097' AND settled_at_ms IS NULL").fetchone()[0] == 0, "CURRENT_GENERATION_HAS_UNSETTLED_ACTION")
    return {"pilots": pilots, "grants": [dict(row) for row in connection.execute("SELECT * FROM mcp_service_grants ORDER BY grant_id")]}


def main():
    global STAGE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-restart-exact-tunnel", action="store_true", required=True)
    parser.parse_args()
    os.umask(0o077)
    pid = service_pid(UNIT)
    require(pid == 5383, "REVIEWED_TUNNEL_PROCESS_CHANGED")
    child, argv = child_and_argv(pid)
    require(child == 5503, "REVIEWED_TUNNEL_CHILD_CHANGED")
    env = environment(pid)
    config = Path.home() / ".config/codex-control-plane/mcp-tunnel.env"
    unit_file = Path.home() / ".config/systemd/user" / UNIT
    credential_file = Path.home() / ".config/codex-control-plane/ubuntu-root-mcp-authorization"
    client = Path(env["CONTROL_PLANE_TUNNEL_CLIENT"])
    require(sha(config) == ENV_SHA and sha(unit_file) == UNIT_SHA and sha(client) == CLIENT_SHA, "REVIEWED_TUNNEL_SOURCE_CONFIG_CHANGED")
    verify_argv(argv, credential_file)
    info = credential_file.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_mode & 0o077 == 0, "CREDENTIAL_FILE_NOT_PROTECTED")
    credential_bytes = credential_file.read_bytes()
    token = credential_bytes.decode().strip().removeprefix("Bearer ")
    server_pid = service_pid("codex-control-plane.service")
    server_env = environment(server_pid)
    require(server_env.get("CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256") == PACKAGE
            and server_env.get("CONTROL_PLANE_MCP_AUTH_MODE") == "private_tunnel_service"
            and server_env.get("CONTROL_PLANE_MCP_SERVICE_PRINCIPAL_ID") == PRINCIPAL
            and server_env.get("CONTROL_PLANE_MCP_SERVICE_GRANT_ID") == GRANT, "REVIEWED_SERVER_NOT_READY")
    connection = sqlite3.connect(Path(server_env["CONTROL_PLANE_DB"]).resolve().as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    connection.row_factory = sqlite3.Row
    before = authority_snapshot(connection)
    grant = connection.execute("SELECT token_digest FROM mcp_service_grants WHERE grant_id=?", (GRANT,)).fetchone()
    digest = hashlib.sha256(b"coding-tools-control-plane:mcp-service-grant:v1\0" + token.encode()).hexdigest()
    require(grant is not None and hmac.compare_digest(digest, grant[0]), "TUNNEL_CREDENTIAL_NOT_CANONICAL_GRANT")
    advertised = tools_list(token)
    old_status = json_get("/api/status")
    require(old_status.get("control_plane_tunnel_id") == TUNNEL, "TUNNEL_OPERATOR_IDENTITY_CHANGED")
    original = config.read_bytes()
    require(b"MCP_STARTUP_WAIT_TIMEOUT=" not in original, "STARTUP_WAIT_ALREADY_CHANGED")
    backup = config.with_name(config.name + ".pre-startup-wait-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    require(not backup.exists(), "CONFIG_BACKUP_ALREADY_EXISTS")
    backup.write_bytes(original)
    backup.chmod(0o600)
    STAGE = "install_supported_startup_wait"
    updated = original + (b"" if original.endswith(b"\n") else b"\n") + b"MCP_STARTUP_WAIT_TIMEOUT=30s\n"
    require(config.read_bytes() == original and service_pid(UNIT) == pid, "TUNNEL_CONFIG_CHANGED_BEFORE_WRITE")
    config.write_bytes(updated)
    config.chmod(0o600)
    STAGE = "restart_exact_tunnel"
    subprocess.run(["systemctl", "--user", "restart", UNIT], check=True, capture_output=True)
    STAGE = "ready_and_first_poll_proof"
    deadline = time.monotonic() + 55
    new_pid = new_child = status = None
    while time.monotonic() < deadline:
        try:
            new_pid = service_pid(UNIT)
            new_child, new_argv = child_and_argv(new_pid)
            verify_argv(new_argv, credential_file)
            status = json_get("/api/status")
            probe = subprocess.run([str(client), "health", "--url", "http://127.0.0.1:8768", "--pid", str(new_child),
                                    "--require-control-plane-poll", "--json"], capture_output=True, text=True, timeout=5)
            if probe.returncode == 0 and new_pid != pid and new_child != child:
                health_proof = json.loads(probe.stdout)
                require(health_proof.get("healthz", {}).get("ok") is True
                        and health_proof.get("readyz", {}).get("ok") is True
                        and health_proof.get("control_plane_poll", {}).get("ok") is True,
                        "SUPPORTED_HEALTH_PROOF_INCOMPLETE")
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        raise RuntimeError("NEW_TUNNEL_READY_AND_FIRST_POLL_NOT_PROVEN")
    require(status.get("client_instance_id") != old_status.get("client_instance_id") and status.get("control_plane_tunnel_id") == TUNNEL, "NEW_TUNNEL_INSTANCE_NOT_PROVEN")
    main = next((channel for channel in status.get("channels", []) if channel.get("name") == "main"), {})
    require(main.get("enabled") is True and not main.get("probe_error"), "MAIN_CHANNEL_NOT_ENABLED")
    require(environment(new_child).get("MCP_STARTUP_WAIT_TIMEOUT") == "30s", "STARTUP_WAIT_NOT_LOADED")
    require(config.read_bytes() == updated and sha(unit_file) == UNIT_SHA and credential_file.read_bytes() == credential_bytes,
            "TUNNEL_CREDENTIAL_OR_CONFIG_DRIFT")
    require(service_pid("codex-control-plane.service") == server_pid and authority_snapshot(connection) == before,
            "SERVER_OR_AUTHORITY_CHANGED_DURING_TUNNEL_RESTART")
    require(tools_list(token) == advertised, "LOCAL_TOOL_SCHEMA_CHANGED_DURING_TUNNEL_RESTART")
    connection.close()
    print(json.dumps({"operation": "reviewed_exact_tunnel_restart", "ok": True, "old_pid": pid, "new_pid": new_pid,
                      "old_child_pid": child, "new_child_pid": new_child, "tunnel_id": TUNNEL,
                      "client_instance_id": status["client_instance_id"], "main_channel_enabled": True,
                      "actual_main_probe_status": main.get("probe_status"),
                      "supported_health_proof": {
                          "healthz": {key: health_proof["healthz"].get(key) for key in ("ok", "status")},
                          "readyz": {key: health_proof["readyz"].get(key) for key in ("ok", "status")},
                          "control_plane_poll": {key: health_proof["control_plane_poll"].get(key) for key in ("ok", "value")},
                          "result": health_proof.get("result"),
                      },
                      "ready_and_first_control_plane_poll_verified": True, "supported_startup_wait": "30s",
                      "canonical_credential_and_pilot_grants_unchanged": True, "server_pid_unchanged": server_pid,
                      "local_schema_properties": advertised, "chatgpt_catalog_refresh_performed": False,
                      "protected_config_backup_remote_path": str(backup), "completed_at_ms": int(time.time() * 1000)}, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print(json.dumps({"operation": "reviewed_exact_tunnel_restart", "ok": False, "stage": STAGE, "error_code": code,
                          "operator_action": "Inspect exact tunnel readiness and new process state; no account, profile, credential or authority fallback."}, separators=(",", ":")))
        sys.exit(1)
