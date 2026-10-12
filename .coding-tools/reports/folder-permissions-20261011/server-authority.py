"""Approved operator actions, executed only on Ubuntu through SSH stdin.

Credentials are read in remote memory. Output is restricted to public state.
"""
import json
import os
import pathlib
import re
import shlex
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

DEVICE = "72ceec2d-e3f2-472f-8e3c-99fffe053035"
WORKSPACE = "workspace_dda1d78e9a21402aa6213f72af64f788"
GENERATION = "generation_c2f13e8d02344cf6a38a3f42ecfa59b6"
PRINCIPAL = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
GRANT = "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"
ENV_FILE = pathlib.Path("/home/svhome/.config/codex-control-plane/control-plane.env")

def emit(value):
    print(json.dumps(value, separators=(",", ":")), flush=True)

def require(condition, code):
    if not condition:
        raise RuntimeError(code)

values = {}
for line in ENV_FILE.read_text().splitlines():
    if not line.strip() or line.lstrip().startswith("#"):
        continue
    key, value = line.split("=", 1)
    parts = shlex.split(value, comments=True)
    values[key.strip()] = parts[0] if parts else ""
host = values["CONTROL_PLANE_BIND"]
if host in ("0.0.0.0", "::"):
    host = "127.0.0.1"
origin = "http://" + host + ":" + values["CONTROL_PLANE_PORT"]
operator = values["CONTROL_PLANE_OPERATOR_TOKEN"]

def api(route, body=None):
    request = urllib.request.Request(
        origin + route,
        data=None if body is None else json.dumps(body, separators=(",", ":")).encode(),
        headers={"Authorization": "Bearer " + operator, "Content-Type": "application/json"},
        method="GET" if body is None else "POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)

def exact_bindings(overview):
    return [row for row in overview["bindings"] if
            row.get("device_id") == DEVICE and row.get("workspace_id") == WORKSPACE
            and row.get("workspace_generation") == GENERATION
            and row.get("revoked_at_ms") is None]

def verify_inventory(overview):
    registrations = [row for row in overview["workspace_registrations"] if
                     row.get("device_id") == DEVICE and row.get("workspace_id") == WORKSPACE
                     and row.get("workspace_generation") == GENERATION
                     and row.get("retired_at_ms") is None]
    require(len(registrations) == 1, "CURRENT_REGISTRATION_NOT_UNIQUE")
    require(all(registrations[0]["capabilities"].get(key) is True for key in ("read", "write", "exec")),
            "CURRENT_CAPABILITIES_CHANGED")
    grants = [row for row in overview["mcp_service_grants"] if row.get("grant_id") == GRANT]
    require(len(grants) == 1, "EXPECTED_GRANT_MISSING")
    grant = grants[0]
    require(grant.get("principal_id") == PRINCIPAL and grant.get("revoked_at_ms") is None,
            "EXPECTED_GRANT_REVOKED")
    require(grant["expires_at_ms"] > overview["observed_at_ms"] + 3600000, "GRANT_WINDOW_TOO_SHORT")
    require(set(grant["scopes"]) == {"control-plane.inventory", "control-plane.read", "control-plane.patch"},
            "EXPECTED_GRANT_SCOPES_CHANGED")

def summary(overview):
    bindings = exact_bindings(overview)
    ids = {row["binding_id"] for row in bindings}
    return {
        "observed_at_ms": overview["observed_at_ms"],
        "admission": overview["admission"],
        "nodes": [{key: row.get(key) for key in (
            "device_id", "endpoint_id", "last_seen_at_ms", "readiness", "policy_state",
            "policy_expires_at_ms", "policy_reason", "activation_epoch")}
                  for row in overview["nodes"] if row.get("device_id") == DEVICE],
        "bindings": [{key: row.get(key) for key in (
            "binding_id", "device_id", "workspace_id", "workspace_generation", "revoked_at_ms")}
                     for row in bindings],
        "contexts": [{key: row.get(key) for key in (
            "context_id", "binding_id", "expires_at_ms", "closed_at_ms")}
                     for row in overview["contexts"] if row.get("binding_id") in ids],
        "pilots": [{key: row.get(key) for key in (
            "decision_id", "principal_id", "binding_id", "expires_at_ms", "revoked_at_ms")}
                   for row in overview["scoped_pilot_decisions"] if row.get("binding_id") in ids],
        "task_count": len(overview.get("task_sessions", [])),
        "current_tasks": [{key: row.get(key) for key in ("task_id", "binding_id", "closed_at_ms")}
                          for row in overview.get("task_sessions", []) if row.get("binding_id") in ids],
        "current_actions": [{key: row.get(key) for key in (
            "action_id", "tool_name", "delivery_state", "latest_receipt_state", "receipt_count")}
            for row in overview.get("actions", []) if row.get("context_id") in {
                context["context_id"] for context in overview["contexts"] if context.get("binding_id") in ids}],
    }

phase = sys.argv[1]
try:
    overview = api("/v1/ui/overview")
    verify_inventory(overview)
    if phase == "prepare":
        require(len(exact_bindings(overview)) == 0, "NEW_BINDING_ALREADY_PRESENT")
        old = ENV_FILE.read_bytes()
        mode = stat.S_IMODE(ENV_FILE.stat().st_mode)
        require(mode == 0o600, "ENV_FILE_MODE_CHANGED")
        pattern = rb"(?m)^CONTROL_PLANE_MCP_SERVICE_EXEC_ENABLED=false(?=\r?$)"
        require(len(re.findall(pattern, old)) == 1, "EXEC_CONFIG_EXPECTATION_CHANGED")
        api("/v1/maintenance/admission", {"mode": "recovery"})
        updated = re.sub(pattern, b"CONTROL_PLANE_MCP_SERVICE_EXEC_ENABLED=true", old)
        fd, temporary = tempfile.mkstemp(prefix=".exec-approved-", dir=str(ENV_FILE.parent))
        try:
            os.fchmod(fd, mode)
            with os.fdopen(fd, "wb") as handle:
                handle.write(updated)
                handle.flush()
                os.fsync(handle.fileno())
            require(ENV_FILE.read_bytes() == old, "ENV_FILE_CONCURRENT_CHANGE")
            os.replace(temporary, ENV_FILE)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        completed = subprocess.run(
            ["systemctl", "--user", "restart", "codex-control-plane.service"],
            capture_output=True, timeout=30,
        )
        require(completed.returncode == 0, "SERVICE_RESTART_FAILED")
        for attempt in range(15):
            try:
                overview = api("/v1/ui/overview")
                break
            except (urllib.error.URLError, TimeoutError):
                if attempt == 14:
                    raise RuntimeError("SERVICE_HEALTH_TIMEOUT") from None
                time.sleep(1)
        verify_inventory(overview)
        binding = api("/v1/bindings", {
            "device_id": DEVICE, "workspace_id": WORKSPACE, "workspace_generation": GENERATION,
            "display_name": "Tools-Codex-web",
        })
        expiry = int(time.time() * 1000) + 3600000
        context = api("/v1/contexts", {"binding_id": binding["binding_id"], "expires_at_ms": expiry})
        pilot = api("/v1/scoped-pilot-decisions", {
            "principal_id": PRINCIPAL, "binding_id": binding["binding_id"], "expires_at_ms": expiry,
            "reason": "Owner-approved Tools-Codex-web read/write/sandboxed exec for 60 minutes",
        })
        emit({"phase": phase, "ok": True, "service_restarted": True, "exec_config_enabled": True,
              "binding_id": binding["binding_id"], "context_id": context["context_id"],
              "pilot_id": pilot.get("decision_id"), "expires_at_ms": expiry,
              "grant_preserved": GRANT, "state": summary(api("/v1/ui/overview"))})
    elif phase == "fence-expired-metadata":
        action_id = "act_1a188ee0d0d7472aa21e6d566ce9793e"
        context_id = "ctx_d77efea247d449c3ab73d1fa370d1374"
        action = api("/v1/actions/" + action_id)
        require(action.get("context_id") == context_id and action.get("tool_name") == "workspace_context"
                and action.get("delivery_state") == "queued" and action.get("expires_at_ms") == 1789835617949
                and action["expires_at_ms"] <= overview["observed_at_ms"]
                and len(action.get("attempts", [])) == 0 and len(action.get("receipts", [])) == 0,
                "EXPIRED_METADATA_ACTION_CHANGED")
        contexts = [row for row in overview["contexts"] if row.get("context_id") == context_id]
        require(len(contexts) == 1 and contexts[0].get("closed_at_ms") is None
                and contexts[0]["expires_at_ms"] == 1789836217932
                and contexts[0]["expires_at_ms"] <= overview["observed_at_ms"], "EXPIRED_CONTEXT_CHANGED")
        api("/v1/contexts/" + context_id + "/close", {})
        result = api("/v1/actions/" + action_id)
        require(result.get("delivery_state") == "settled" and len(result.get("attempts", [])) == 0,
                "EXPIRED_ACTION_NOT_REFUSED")
        emit({"phase": phase, "ok": True, "action_id": action_id, "context_id": context_id,
              "delivery_state": result["delivery_state"], "attempt_count": 0,
              "workspace_effect_performed": False, "reason": "expired_context_closed_before_dispatch"})
    elif phase == "renew-expired":
        bindings = exact_bindings(overview)
        require(len(bindings) == 1 and bindings[0]["binding_id"] == "bind_3e05bf64cb3e4bab93d930ae1692bebb",
                "CURRENT_BINDING_CHANGED")
        binding_id = bindings[0]["binding_id"]
        pilots = [row for row in overview["scoped_pilot_decisions"] if
                  row.get("decision_id") == "pilot_b4069f55f8ab45e497c5287f51ce8ff6"
                  and row.get("binding_id") == binding_id and row.get("principal_id") == PRINCIPAL]
        require(len(pilots) == 1 and pilots[0]["decision_id"] == "pilot_b4069f55f8ab45e497c5287f51ce8ff6"
                and pilots[0]["expires_at_ms"] == 1791699184407
                and pilots[0]["expires_at_ms"] <= overview["observed_at_ms"], "EXPIRED_PILOT_CHANGED")
        require(not any(row.get("binding_id") == binding_id and row.get("revoked_at_ms") is None
                        and row["expires_at_ms"] > overview["observed_at_ms"]
                        for row in overview["scoped_pilot_decisions"]), "UNEXPECTED_CURRENT_PILOT")
        contexts = [row for row in overview["contexts"] if row.get("binding_id") == binding_id
                    and row.get("closed_at_ms") is None]
        require(all(row["expires_at_ms"] <= overview["observed_at_ms"] for row in contexts),
                "UNEXPECTED_CURRENT_CONTEXT")
        target_context_ids = {row["context_id"] for row in overview["contexts"]
                              if row.get("binding_id") == binding_id}
        require(all(row.get("delivery_state") == "settled" for row in overview.get("actions", [])
                    if row.get("context_id") in target_context_ids),
                "UNSETTLED_ACTION_EXISTS")
        api("/v1/maintenance/admission", {"mode": "recovery"})
        for context in contexts:
            api("/v1/contexts/" + context["context_id"] + "/close", {})
        expiry = int(time.time() * 1000) + 3600000
        context = api("/v1/contexts", {"binding_id": binding_id, "expires_at_ms": expiry})
        pilot = api("/v1/scoped-pilot-decisions", {
            "principal_id": PRINCIPAL, "binding_id": binding_id, "expires_at_ms": expiry,
            "reason": "Owner-approved renewal: same Tools-Codex-web read/write/sandboxed exec scope for 60 minutes",
        })
        emit({"phase": phase, "ok": True, "binding_preserved": binding_id,
              "context_id": context["context_id"], "pilot_id": pilot.get("decision_id"),
              "expires_at_ms": expiry, "grant_preserved": GRANT,
              "state": summary(api("/v1/ui/overview"))})
    elif phase == "open":
        bindings = exact_bindings(overview)
        require(len(bindings) == 1, "CURRENT_BINDING_NOT_UNIQUE")
        pilots = [row for row in overview["scoped_pilot_decisions"] if
                  row.get("binding_id") == bindings[0]["binding_id"] and row.get("principal_id") == PRINCIPAL
                  and row.get("revoked_at_ms") is None and row["expires_at_ms"] > overview["observed_at_ms"]]
        require(len(pilots) == 1, "CURRENT_PILOT_NOT_UNIQUE")
        api("/v1/maintenance/admission", {"mode": "scoped_pilot"})
        emit({"phase": phase, "ok": True, "state": summary(api("/v1/ui/overview"))})
    elif phase == "status":
        emit({"phase": phase, "ok": True, "state": summary(overview)})
    elif phase == "reconciliation":
        action = api("/v1/actions/act_16f5443e532942019fa7bb43868b34b0")
        receipts = action["receipts"]
        require(action["delivery_state"] == "settled", "RECONCILIATION_NOT_TERMINAL")
        require(len(action["attempts"]) == 1, "RECONCILIATION_ATTEMPT_CHANGED")
        require([row["receipt_state"] for row in receipts] == ["unknown", "rejected"], "RECONCILIATION_HISTORY_CHANGED")
        emit({"phase": phase, "ok": True, "action_id": action["action_id"],
              "delivery_state": action["delivery_state"], "attempt_count": len(action["attempts"]),
              "receipt_states": [row["receipt_state"] for row in receipts]})
    else:
        raise RuntimeError("UNKNOWN_PHASE")
except urllib.error.HTTPError as error:
    emit({"phase": phase, "ok": False, "error": "OPERATOR_API_HTTP_ERROR", "http_status": error.code})
    sys.exit(1)
except Exception as error:
    code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
    emit({"phase": phase, "ok": False, "error": code})
    sys.exit(1)
