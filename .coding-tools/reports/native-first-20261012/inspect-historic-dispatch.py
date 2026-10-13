"""Exact read-only dispatch observer; raw environment and receipt data stay in memory."""
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import time

action_id = "act_0f0a49c6424d42d3bc7bc49ad46e4ffa"
service = subprocess.run(["systemctl", "--user", "show", "codex-control-plane.service", "--property=MainPID", "--value"], capture_output=True, text=True, check=True)
pid = int(service.stdout.strip())
environment = dict(item.split("=", 1) for item in Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in item)
database = Path(environment["CONTROL_PLANE_DB"])
if not database.is_absolute():
    database = Path(f"/proc/{pid}/cwd").resolve() / database
connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
connection.row_factory = sqlite3.Row
connection.execute("PRAGMA query_only=ON")
connection.execute("BEGIN")
now = int(time.time() * 1000)
action = dict(connection.execute("SELECT action_id,device_id,workspace_id,workspace_generation,tool_name,delivery_state,created_at_ms,expires_at_ms,settled_at_ms,action_digest FROM actions WHERE action_id=?", (action_id,)).fetchone())
attempts = [dict(row) for row in connection.execute("SELECT attempt_id,attempt_number,dispatched_at_ms FROM delivery_attempts WHERE action_id=? ORDER BY attempt_number", (action_id,))]
intents = {name: bool(connection.execute("SELECT 1 FROM " + name + " WHERE action_id=?", (action_id,)).fetchone()) for name in ("mcp_read_only_intents", "mcp_file_read_intents", "mcp_approved_patch_intents", "mcp_standing_patch_intents", "mcp_exec_intents", "mcp_artifact_intents", "mcp_document_write_intents")}
receipts = [{"receipt_id": row["receipt_id"], "receipt_state": row["receipt_state"], "received_at_ms": row["received_at_ms"], "receipt_digest": row["receipt_digest"], "local_handle_present": bool(row["local_handle"]), "payload_sha256": hashlib.sha256(row["payload_json"].encode()).hexdigest()} for row in connection.execute("SELECT * FROM receipts WHERE action_id=? ORDER BY received_at_ms,receipt_id", (action_id,))]
node = dict(connection.execute("SELECT device_id,revoked_at_ms,last_seen_at_ms,readiness FROM nodes WHERE device_id=?", (action["device_id"],)).fetchone())
tasks = connection.execute("SELECT COUNT(*) FROM mcp_task_sessions WHERE device_id=? AND closed_at_ms IS NULL AND expires_at_ms>?", (action["device_id"], now)).fetchone()[0]
writers = connection.execute("SELECT COUNT(*) FROM mcp_task_writer_leases l JOIN bindings b ON b.binding_id=l.binding_id WHERE b.device_id=? AND l.released_at_ms IS NULL AND l.expires_at_ms>?", (action["device_id"], now)).fetchone()[0]
digest = hashlib.sha256(json.dumps({"action": action, "attempts": attempts, "intents": intents, "receipts": receipts}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
connection.execute("ROLLBACK")
print(json.dumps({"ok": True, "captured_at_ms": now, "action": action, "action_expired": action["expires_at_ms"] <= now, "delivery_attempts": attempts, "attempt_expiry_note": "Attempts have no separate expiry; immutable action expiry is shown", "intent_kinds": intents, "receipts": receipts, "node": node, "live_tasks": tasks, "live_writers": writers, "historical_state_sha256": digest, "database_mutations_performed": False}, separators=(",", ":")))
