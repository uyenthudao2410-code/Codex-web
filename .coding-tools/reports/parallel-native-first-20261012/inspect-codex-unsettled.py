"""Read-only exact Codex action provenance; no bodies, credentials or mutation."""
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time

EXPECTED_PID = 970133
DEVICE = "4c4b7a5b-7744-49ae-a490-78a528a00471"
WORKSPACE = "workspace_f93b5bac9dc74fae9cea66f44c4ebc94"
GENERATION = "generation_a420c8bfcfcb4e42b5bb7fc5e5cec097"
HISTORICAL_IDS = ["act_d4e6ce3ca8064311bf0a8601e5ec1711", "act_ac60e7c1abf14e97a208f907801c571a",
                  "act_cdd2e63ad9cc427f9372462e9fca51b6", "act_97f01939475c46fca95aa1428d2441be",
                  "act_0eb81c71305e472ca6a91b9107362e17"]
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,255}$")


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def main():
    if sys.platform == "win32":
        output = Path(__file__).with_name(sys.argv[1])
        require(output.parent == Path(__file__).parent and not output.exists(), "NEW_REPORT_PATH_REQUIRED")
        source = Path(__file__).read_bytes()
        result = subprocess.run(["ssh.exe", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
            "-o", "StrictHostKeyChecking=yes", "svhome@100.116.112.22", "python3", "-B", "-"],
            input=source, capture_output=True, timeout=45)
        require(len(result.stdout) <= 262144, "BOUNDED_OBSERVER_RESPONSE_REQUIRED")
        report = json.loads(result.stdout)
        require(report.get("operation") == "codex_unsettled_readonly_provenance", "EXACT_OBSERVER_RESPONSE_REQUIRED")
        report["observer_sha256"] = hashlib.sha256(source).hexdigest()
        report["ssh_exit_code"] = result.returncode
        with output.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, indent=2)
            handle.write("\n")
        print(json.dumps({"ok": report.get("ok"), "report": str(output), "action_count": len(report.get("actions", [])),
                          "all_exact_current_principal_read_only": report.get("all_exact_current_principal_read_only")}))
        return 0 if report.get("ok") and result.returncode == 0 else 1
    service = subprocess.run(["systemctl", "--user", "show", "codex-control-plane.service", "--property=MainPID"],
                             capture_output=True, text=True, timeout=10)
    require(service.returncode == 0 and service.stdout.strip() == "MainPID=" + str(EXPECTED_PID), "EXACT_SERVING_PID_REQUIRED")
    environment = dict(item.split("=", 1) for item in Path(f"/proc/{EXPECTED_PID}/environ").read_text().split("\0") if "=" in item)
    principal = environment["CONTROL_PLANE_MCP_SERVICE_PRINCIPAL_ID"]
    require(IDENTIFIER.fullmatch(principal), "PRINCIPAL_ID_INVALID")
    database = Path(environment["CONTROL_PLANE_DB"]).resolve()
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    now = int(time.time() * 1000)
    rows = connection.execute("SELECT action_id,owner_id,request_id,context_id,binding_id,device_id,workspace_id,workspace_generation,"
        "tool_name,arguments_json,action_digest,idempotency_key,created_at_ms,expires_at_ms,delivery_state,settled_at_ms "
        "FROM actions WHERE device_id=? AND workspace_id=? AND workspace_generation=? "
        "AND (settled_at_ms IS NULL OR action_id IN (?,?,?,?,?)) "
        "ORDER BY created_at_ms,action_id LIMIT 129", (DEVICE, WORKSPACE, GENERATION, *HISTORICAL_IDS)).fetchall()
    require(len(rows) <= 128, "BOUNDED_ACTION_CENSUS_REQUIRED")
    tables = ["mcp_read_only_intents", "mcp_file_read_intents", "mcp_approved_patch_intents", "mcp_standing_patch_intents",
              "mcp_exec_intents", "mcp_artifact_intents", "mcp_document_write_intents"]
    actions = []
    for row in rows:
        args = json.loads(row["arguments_json"])
        exact_arguments = args == {"detail": "compact", "max_entries": 1}
        intents = []
        for table in tables:
            intent_rows = connection.execute(f"SELECT principal_id,intent_digest,created_at_ms FROM {table} WHERE action_id=?", (row["action_id"],)).fetchall()
            for intent in intent_rows:
                require(IDENTIFIER.fullmatch(intent["principal_id"]), "INTENT_PRINCIPAL_ID_INVALID")
                intents.append({"intent_kind": table, **dict(intent), "matches_serving_principal": intent["principal_id"] == principal})
        receipts = [{"receipt_state": item["receipt_state"], "received_at_ms": item["received_at_ms"],
                     "has_local_handle": item["local_handle"] is not None}
                    for item in connection.execute("SELECT receipt_state,received_at_ms,local_handle FROM receipts WHERE action_id=? ORDER BY received_at_ms", (row["action_id"],))]
        events = [dict(item) for item in connection.execute("SELECT event_type,created_at_ms FROM events WHERE subject_id=? ORDER BY created_at_ms", (row["action_id"],))]
        record = {key: row[key] for key in ("action_id", "owner_id", "request_id", "context_id", "binding_id", "device_id", "workspace_id",
            "workspace_generation", "tool_name", "action_digest", "created_at_ms", "expires_at_ms", "delivery_state", "settled_at_ms")}
        record.update(exact_compact_metadata_arguments=exact_arguments,
            arguments_sha256=hashlib.sha256(row["arguments_json"].encode()).hexdigest(),
            idempotency_key_sha256=hashlib.sha256(row["idempotency_key"].encode()).hexdigest(),
            known_canary_idempotency_prefix=row["idempotency_key"].startswith(("parallel-native-first-20261012:", "parallel-overlap-20261012:")),
            expired=row["expires_at_ms"] <= now, intents=intents, receipts=receipts, events=events,
            delivery_attempt_count=connection.execute("SELECT COUNT(*) FROM delivery_attempts WHERE action_id=?", (row["action_id"],)).fetchone()[0])
        actions.append(record)
    report = {"operation": "codex_unsettled_readonly_provenance", "ok": True, "observed_at_ms": now,
        "service_pid": EXPECTED_PID, "serving_principal_id": principal, "actions": actions, "read_only_database": True,
        "unsettled_action_count": sum(item["settled_at_ms"] is None for item in actions),
        "all_exact_current_principal_read_only": bool(actions) and all(item["tool_name"] == "workspace_context"
            and item["exact_compact_metadata_arguments"] and len(item["intents"]) == 1
            and item["intents"][0]["intent_kind"] == "mcp_read_only_intents"
            and item["intents"][0]["matches_serving_principal"] for item in actions)}
    connection.close()
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(json.dumps({"operation": "codex_unsettled_readonly_provenance", "ok": False,
                          "error_code": str(error) if isinstance(error, RuntimeError) else type(error).__name__}))
        sys.exit(1)
