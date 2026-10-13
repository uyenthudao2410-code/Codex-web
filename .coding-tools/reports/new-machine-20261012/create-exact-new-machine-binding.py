"""Reviewed owner binding operation for the exact new-machine workspace.

Run on svhome only after supported Windows replacement has returned its new
generation. This script performs no service, admission, pilot, grant or action
operation. The operator credential stays in process memory.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
import urllib.request

DEVICE = "4c4b7a5b-7744-49ae-a490-78a528a00471"
WORKSPACE = "workspace_f93b5bac9dc74fae9cea66f44c4ebc94"
OLD_GENERATION = "generation_fe5aea8e583749c3bd59986650144bb2"
ORIGIN = "https://svhome.tail0e4032.ts.net"
HISTORICAL_ACTIONS = {
    "act_048df93488874a70aa97a7ee18ccbd03",
    "act_744496c6bd514d38a746cf8819aae9ad",
}
HISTORICAL_FAMILY_SHA256 = "724cb852c916eb91bb16e8631ef423ce2cdda0b3d0e8e58e1f1c69bdf7d83d2f"


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def family_digest(connection):
    families = []
    for action_id in sorted(HISTORICAL_ACTIONS):
        family = {"action_id": action_id}
        for table in ("actions", "action_reconciliations", "delivery_attempts", "receipts"):
            rows = [dict(row) for row in connection.execute(
                "SELECT * FROM " + table + " WHERE action_id=?", (action_id,)
            )]
            family[table] = sorted(rows, key=lambda row: json.dumps(row, sort_keys=True))
        families.append(family)
    return hashlib.sha256(json.dumps(families, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--new-generation", required=True)
    parser.add_argument("--confirm-create-binding", action="store_true", required=True)
    args = parser.parse_args()
    require(re.fullmatch(r"generation_[a-f0-9]{32}", args.new_generation) is not None,
            "NEW_GENERATION_INVALID")
    require(args.new_generation != OLD_GENERATION, "NEW_GENERATION_EQUALS_RETIRED_TARGET")
    pid = int(subprocess.check_output(
        ["systemctl", "--user", "show", "codex-control-plane.service", "--property=MainPID", "--value"],
        text=True,
    ).strip())
    environment = dict(item.split("=", 1) for item in
                       Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in item)
    token = environment.get("CONTROL_PLANE_OPERATOR_TOKEN", "")
    require(bool(token), "OPERATOR_CREDENTIAL_UNAVAILABLE")
    database = Path(environment["CONTROL_PLANE_DB"])
    if not database.is_absolute():
        database = Path(f"/proc/{pid}/cwd").resolve() / database
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    connection.row_factory = sqlite3.Row
    try:
        for query in (
            "SELECT COUNT(*) FROM mcp_task_sessions WHERE device_id=? AND workspace_id=? AND closed_at_ms IS NULL",
            "SELECT COUNT(*) FROM mcp_task_writer_leases l JOIN mcp_task_sessions t ON t.task_id=l.task_id "
            "WHERE t.device_id=? AND t.workspace_id=? AND l.released_at_ms IS NULL",
        ):
            require(connection.execute(query, (DEVICE, WORKSPACE)).fetchone()[0] == 0,
                    "TARGET_TASK_OR_WRITER_NOT_QUIESCENT")
        unsettled = connection.execute(
            "SELECT a.action_id,a.tool_name,a.expires_at_ms,a.delivery_state,r.disposition "
            "FROM actions a LEFT JOIN action_reconciliations r ON r.action_id=a.action_id "
            "WHERE a.device_id=? AND a.workspace_id=? AND a.settled_at_ms IS NULL",
            (DEVICE, WORKSPACE),
        ).fetchall()
        require({row["action_id"] for row in unsettled} == HISTORICAL_ACTIONS,
                "UNSETTLED_ACTION_SET_CHANGED")
        require(all(row["tool_name"] == "workspace_context" and
                    row["delivery_state"] == "reconcile_required" and
                    row["disposition"] == "quarantined_unknown" and
                    row["expires_at_ms"] < int(time.time() * 1000) for row in unsettled),
                "UNSETTLED_ACTION_NOT_HISTORICAL_QUARANTINE")
        old = connection.execute(
            "SELECT retired_at_ms FROM node_workspaces WHERE device_id=? AND workspace_id=? AND workspace_generation=?",
            (DEVICE, WORKSPACE, OLD_GENERATION),
        ).fetchone()
        require(old is not None and old["retired_at_ms"] is not None, "OLD_REGISTRATION_NOT_RETIRED")
        new = connection.execute(
            "SELECT display_name,capabilities_json,retired_at_ms FROM node_workspaces "
            "WHERE device_id=? AND workspace_id=? AND workspace_generation=?",
            (DEVICE, WORKSPACE, args.new_generation),
        ).fetchone()
        require(new is not None and new["retired_at_ms"] is None and new["display_name"] == "Codex-web"
                and json.loads(new["capabilities_json"]) == {"read": True, "write": True, "exec": True},
                "NEW_REGISTRATION_NOT_EXACT_CODING_SCOPE")
        existing = connection.execute(
            "SELECT binding_id,owner_id FROM bindings WHERE device_id=? AND workspace_id=? "
            "AND workspace_generation=? AND revoked_at_ms IS NULL",
            (DEVICE, WORKSPACE, args.new_generation),
        ).fetchall()
        require(len(existing) <= 1, "MULTIPLE_NEW_TARGET_BINDINGS")
        before = family_digest(connection)
        require(before == HISTORICAL_FAMILY_SHA256, "HISTORICAL_ACTION_FAMILIES_CHANGED_SINCE_PREFLIGHT")
        body = {"device_id": DEVICE, "workspace_id": WORKSPACE,
                "workspace_generation": args.new_generation, "display_name": "DESKTOP-63643J4 - Codex-web"}
        if existing:
            require(existing[0]["owner_id"] == "owner_default", "EXISTING_BINDING_OWNER_MISMATCH")
            result = {"binding_id": existing[0]["binding_id"], **body, "replayed": True}
        else:
            request = urllib.request.Request(
                ORIGIN + "/v1/bindings", data=json.dumps(body, separators=(",", ":")).encode(),
                headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                require(response.status == 201, "BINDING_HTTP_RESULT_UNEXPECTED")
                result = json.loads(response.read(16385).decode())
            require(all(result.get(key) == value for key, value in body.items())
                    and result.get("owner_id") == "owner_default", "BINDING_RESULT_TARGET_MISMATCH")
        require(family_digest(connection) == before, "HISTORICAL_ACTION_FAMILIES_CHANGED")
        print(json.dumps({"operation": "exact_new_machine_binding", "body": body,
                          "binding_id": result["binding_id"], "replayed": result.get("replayed", False),
                          "historical_action_family_sha256": before,
                          "service_pid": pid}, separators=(",", ":")))
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Never include response payloads, environment values, request headers,
        # command output or an exception traceback in the operator receipt.
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print(json.dumps({"operation": "exact_new_machine_binding", "ok": False, "error_code": code}))
        sys.exit(1)
