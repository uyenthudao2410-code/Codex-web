"""Observe or explicitly close only the two exact r9 canary action contexts.

Send through SSH stdin to svhome@100.116.112.22. Default is read-only.
Never closes tasks, releases writers, settles actions, deploys or restarts.
UNKNOWN or live action/task/writer evidence refuses execution. The standing
owner context, receipts and historical action families are preserved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shlex
import sqlite3
import stat
import time
import urllib.error
import urllib.request

BINDING = "bind_3e05bf64cb3e4bab93d930ae1692bebb"
DEVICE = "72ceec2d-e3f2-472f-8e3c-99fffe053035"
WORKSPACE = "workspace_dda1d78e9a21402aa6213f72af64f788"
GENERATION = "generation_c2f13e8d02344cf6a38a3f42ecfa59b6"
PRINCIPAL = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
STANDING = "ctx_655e717e5c634cc1922d0f0d2e9d33c6"
INSTANCE = "cp_d203277517b747e4b056ec0184d09709"
REVISION = "5ce5c51fc97584501d5d091e8c21df88250f55eb42e6e756384b234da8837b1f"
PACKAGE = "sha256:bb529f710342bf064fb5d2259ab1ad49e3733a6ca6db0c60b60ed67f119a7566"
CANARIES = {
    "cold": ("task_6c770b0958074bdbad47d95391f2bff5", "act_4193cf69c84542e7b13a91e492916ccd"),
    "warm": ("task_3b1889c84dbd4e54a2ac9729a8a4da1f", "act_fc024ff0b54c4a8ba4c7c7b0228a7e76"),
}
COLD_CONTEXT = "ctx_9b930390ceb94596a49513ad94ebcb97"
ARGV = {"argv": ["node", "--test", "tests/control-plane-approved-patch-runtime.test.js"]}
TERMINAL = {"completed", "failed", "rejected", "stopped"}
ENV_FILE = Path("/home/svhome/.config/codex-control-plane/control-plane.env")


class GuardFailure(Exception):
    pass


def require(condition, code):
    if not condition:
        raise GuardFailure(code)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def emit(phase, **fields):
    print(json.dumps({"phase": phase, "observed_at_ms": int(time.time() * 1000),
                      **fields}, separators=(",", ":")), flush=True)


def environment():
    require(pwd.getpwuid(os.getuid()).pw_name == "svhome", "SERVER_USER_MISMATCH")
    require(ENV_FILE.is_file() and not ENV_FILE.is_symlink(), "CONFIG_TARGET_UNSAFE")
    info = ENV_FILE.stat()
    require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o600,
            "CONFIG_ACL_INVALID")
    values = {}
    for line in ENV_FILE.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        require(key.strip() not in values, "CONFIG_DUPLICATE_KEY")
        parts = shlex.split(value, comments=True)
        require(len(parts) <= 1, "CONFIG_VALUE_INVALID")
        values[key.strip()] = parts[0] if parts else ""
    bind = values.get("CONTROL_PLANE_BIND", "127.0.0.1")
    require(bind in {"127.0.0.1", "0.0.0.0", "::", "100.116.112.22"}, "SERVER_BIND_CHANGED")
    port = values.get("CONTROL_PLANE_PORT", "8765")
    require(port.isdigit() and 1 <= int(port) <= 65535, "SERVER_PORT_INVALID")
    address = "100.116.112.22" if bind == "100.116.112.22" else "127.0.0.1"
    database = Path(values["CONTROL_PLANE_DB"])
    require(database.is_absolute() and database.is_file() and not database.is_symlink(),
            "DATABASE_TARGET_UNSAFE")
    require(database.resolve().is_relative_to(Path("/home/svhome")), "DATABASE_SCOPE_CHANGED")
    return "http://" + address + ":" + port, values["CONTROL_PLANE_OPERATOR_TOKEN"], database


def api(origin, token, route, body=None):
    request = urllib.request.Request(origin + route,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        method="GET" if body is None else "POST")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.load(response)
    except (OSError, ValueError, urllib.error.URLError):
        raise GuardFailure("CONTROL_PLANE_API_FAILED") from None
    require(isinstance(result, dict), "CONTROL_PLANE_RESPONSE_INVALID")
    return result


def health_guard(health):
    require(health.get("ok") is True and health.get("schema_version") == 28,
            "SERVER_HEALTH_CHANGED")
    require(health.get("service_instance_id") == INSTANCE, "SERVER_INSTANCE_CHANGED")
    require(health.get("declared_source_revision") == REVISION
            and health.get("package_source_sha256") == PACKAGE, "SERVER_SOURCE_CHANGED")


def rows(connection, query, parameters=()):
    return [dict(row) for row in connection.execute(query, parameters)]


def snapshot(database, selected):
    families = []
    blockers = []
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        require(int(connection.execute("PRAGMA user_version").fetchone()[0]) == 28,
                "DATABASE_SCHEMA_CHANGED")
        standing = rows(connection, "SELECT * FROM contexts WHERE context_id=?", (STANDING,))
        require(len(standing) == 1 and standing[0]["binding_id"] == BINDING
                and standing[0]["closed_at_ms"] is None, "STANDING_CONTEXT_CHANGED")
        for name in selected:
            task_id, action_id = CANARIES[name]
            tasks = rows(connection, "SELECT * FROM mcp_task_sessions WHERE task_id=?", (task_id,))
            actions = rows(connection, "SELECT * FROM actions WHERE action_id=?", (action_id,))
            intents = rows(connection, "SELECT * FROM mcp_exec_intents WHERE action_id=?", (action_id,))
            links = rows(connection, "SELECT * FROM mcp_task_action_links WHERE task_id=?", (task_id,))
            require(len(tasks) == len(actions) == len(intents) == len(links) == 1,
                    "CANARY_FAMILY_MISSING_OR_SHARED")
            task, action, intent = tasks[0], actions[0], intents[0]
            require(links[0]["action_id"] == action_id and intent["task_id"] == task_id
                    and intent["principal_id"] == PRINCIPAL and task["principal_id"] == PRINCIPAL,
                    "CANARY_TASK_INTENT_LINK_CHANGED")
            require(intent["binding_id"] == BINDING and action["request_id"] == intent["request_id"]
                    and action["admission_reference"] == "mcp_exec:" + intent["intent_digest"],
                    "CANARY_EXEC_ADMISSION_CHANGED")
            require(json.loads(intent["argv_json"]) == ARGV and intent["cwd"] == ""
                    and intent["timeout_ms"] == 300000 and intent["max_output_bytes"] == 32768,
                    "CANARY_COMMAND_CHANGED")
            for record in (task, action):
                require(record["binding_id"] == BINDING and record["device_id"] == DEVICE
                        and record["workspace_id"] == WORKSPACE
                        and record["workspace_generation"] == GENERATION,
                        "CANARY_TARGET_CHANGED")
            context_id = action["context_id"]
            require(re.fullmatch(r"ctx_[a-f0-9]{32}", context_id) and context_id != STANDING,
                    "CANARY_CONTEXT_SCOPE_INVALID")
            if name == "cold":
                require(context_id == COLD_CONTEXT, "COLD_CONTEXT_CHANGED")
            contexts = rows(connection, "SELECT * FROM contexts WHERE context_id=?", (context_id,))
            require(len(contexts) == 1, "CANARY_CONTEXT_MISSING")
            context = contexts[0]
            require(context["owner_id"] == task["owner_id"] == action["owner_id"] == intent["owner_id"]
                    == standing[0]["owner_id"] and context["binding_id"] == BINDING
                    and context["device_id"] == DEVICE and context["workspace_id"] == WORKSPACE
                    and context["workspace_generation"] == GENERATION,
                    "CANARY_CONTEXT_AUTHORITY_CHANGED")
            require(context["endpoint_id"] == action["endpoint_id"] == task["endpoint_id"]
                    and context["created_at_ms"] == action["created_at_ms"] == intent["created_at_ms"]
                    and context["expires_at_ms"] == action["expires_at_ms"],
                    "CANARY_GENERATED_CONTEXT_IDENTITY_CHANGED")
            requests = rows(connection, "SELECT * FROM work_requests WHERE request_id=?", (action["request_id"],))
            require(len(requests) == 1 and requests[0]["context_id"] == context_id
                    and requests[0]["owner_id"] == context["owner_id"],
                    "CANARY_WORK_REQUEST_CONTEXT_CHANGED")
            require(rows(connection, "SELECT action_id FROM actions WHERE context_id=?", (context_id,))
                    == [{"action_id": action_id}], "CANARY_CONTEXT_SHARED")
            require(not rows(connection, "SELECT grant_id FROM mcp_access_grants WHERE context_id=?", (context_id,)),
                    "CANARY_CONTEXT_HAS_SHARED_GRANT")
            require(not rows(connection, "SELECT action_id FROM mcp_patch_acceptances WHERE action_id=?", (action_id,)),
                    "CANARY_HAS_PATCH_ACCEPTANCE")
            family = {"task": task, "action": action, "intent": intent, "links": links}
            for table, order in (("receipts", "received_at_ms, receipt_id"),
                                 ("delivery_attempts", "attempt_number, attempt_id"),
                                 ("action_reconciliations", "action_id"),
                                 ("action_dispatch_dispositions", "action_id")):
                family[table] = rows(connection,
                    f"SELECT * FROM {table} WHERE action_id=? ORDER BY {order}", (action_id,))
            family["writers"] = rows(connection,
                "SELECT * FROM mcp_task_writer_leases WHERE task_id=? ORDER BY lease_id", (task_id,))
            if task["closed_at_ms"] is None:
                blockers.append(name + ":TASK_NOT_CLOSED")
            if any(writer["released_at_ms"] is None for writer in family["writers"]):
                blockers.append(name + ":WRITER_NOT_RELEASED")
            receipts = family["receipts"]
            if action["delivery_state"] != "settled" or action["settled_at_ms"] is None:
                blockers.append(name + ":ACTION_NOT_SETTLED")
            if not receipts or receipts[-1]["receipt_state"] not in TERMINAL:
                blockers.append(name + ":TERMINAL_RECEIPT_UNPROVEN")
            families.append({"name": name, "task_id": task_id, "action_id": action_id,
                             "context": context, "immutable_family_sha256": digest(family)})
        preserved = {
            "standing_context_sha256": digest(standing),
            "patch_acceptances_sha256": digest(rows(connection,
                "SELECT * FROM mcp_patch_acceptances ORDER BY action_id")),
            "service_grants_sha256": digest(rows(connection,
                "SELECT * FROM mcp_service_grants ORDER BY grant_id")),
            "scoped_pilots_sha256": digest(rows(connection,
                "SELECT * FROM scoped_pilot_decisions ORDER BY decision_id")),
            "action_history_sha256": digest({table: rows(connection,
                f"SELECT * FROM {table} ORDER BY {order}")
                for table, order in (("actions", "action_id"),
                                     ("work_requests", "request_id"),
                                     ("receipts", "receipt_id"),
                                     ("delivery_attempts", "attempt_id"),
                                     ("action_reconciliations", "action_id"),
                                     ("action_dispatch_dispositions", "action_id"),
                                     ("mcp_exec_intents", "action_id"),
                                     ("mcp_task_sessions", "task_id"),
                                     ("mcp_task_action_links", "action_id"),
                                     ("mcp_task_writer_leases", "lease_id"))}),
        }
    return {"families": families, "preserved": preserved, "blockers": blockers}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--which", choices=("cold", "warm", "both"), default="both")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--operator-approved", action="store_true")
    parser.add_argument("--expected-state-sha256")
    parser.add_argument("--expected-contexts")
    arguments = parser.parse_args()
    selected = tuple(CANARIES) if arguments.which == "both" else (arguments.which,)
    origin, token, database = environment()
    health_guard(api(origin, token, "/healthz"))
    before = snapshot(database, selected)
    contexts = sorted(family["context"]["context_id"] for family in before["families"])
    summary = [{key: family[key] for key in ("name", "task_id", "action_id", "immutable_family_sha256")}
               | {"context_id": family["context"]["context_id"],
                  "context_closed_at_ms": family["context"]["closed_at_ms"]}
               for family in before["families"]]
    emit("r9_context_cleanup_observed", ok=True, remote_mutation=False,
         service_instance_id=INSTANCE, ready=not before["blockers"], blockers=before["blockers"],
         families=summary, state_sha256=digest(before), expected_contexts=",".join(contexts))
    if not arguments.execute:
        return
    require(arguments.operator_approved, "EXPLICIT_EXECUTION_AUTHORIZATION_REQUIRED")
    require(not before["blockers"], "CANARY_NOT_TERMINAL_FOR_CONTEXT_CLEANUP")
    require(arguments.expected_state_sha256 == digest(before), "OBSERVED_STATE_PIN_CHANGED")
    require(arguments.expected_contexts == ",".join(contexts), "EXACT_CONTEXT_PIN_CHANGED")
    require(snapshot(database, selected) == before, "CANARY_CHANGED_BEFORE_CLEANUP")
    health_guard(api(origin, token, "/healthz"))
    for context_id in contexts:
        response = api(origin, token, "/v1/contexts/" + context_id + "/close", {})
        require(response.get("context_id") == context_id
                and response.get("closed_at_ms") is not None, "CONTEXT_CLOSE_ACK_UNPROVEN")
    after = snapshot(database, selected)
    require(not after["blockers"] and after["preserved"] == before["preserved"],
            "PRESERVED_AUTHORITY_OR_ACCEPTANCE_CHANGED")
    for previous, current in zip(before["families"], after["families"]):
        require(previous["immutable_family_sha256"] == current["immutable_family_sha256"],
                "ACTION_TASK_WRITER_OR_RECEIPT_MUTATED")
        expected = previous["context"] | {"closed_at_ms": current["context"]["closed_at_ms"]}
        require(current["context"]["closed_at_ms"] is not None and current["context"] == expected,
                "CONTEXT_CLOSE_EFFECT_UNPROVEN")
    health_guard(api(origin, token, "/healthz"))
    emit("r9_context_cleanup_complete", ok=True, remote_mutation=True,
         contexts_closed=contexts, standing_context_preserved=STANDING,
         tasks_actions_writers_receipts_preserved=True, service_restart=False,
         command_replayed=False, state_sha256=digest(after))


if __name__ == "__main__":
    try:
        main()
    except GuardFailure as error:
        emit("r9_context_cleanup_refused", ok=False, code=str(error))
        raise SystemExit(1) from None
    except Exception:
        emit("r9_context_cleanup_refused", ok=False, code="CLEANUP_UNEXPECTED_FAILURE")
        raise SystemExit(1) from None
