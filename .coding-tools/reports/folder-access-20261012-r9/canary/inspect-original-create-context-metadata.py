"""Read-only original action metadata; no content or credentials are output."""
import json
from pathlib import Path
import sqlite3
import subprocess
import time

PID = 946413
ACTION = "act_ed8982433bf347ef8c32aebc17b23d43"
current = int(subprocess.check_output(["systemctl", "--user", "show", "codex-control-plane.service", "--property=MainPID", "--value"], text=True).strip())
if current != PID:
    raise SystemExit("EXACT_ORIGINAL_SERVICE_CHANGED")
environment = dict(item.split("=", 1) for item in Path(f"/proc/{PID}/environ").read_text().split("\0") if "=" in item)
database = Path(environment["CONTROL_PLANE_DB"])
if not database.is_absolute():
    database = Path(f"/proc/{PID}/cwd").resolve() / database
connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
connection.execute("PRAGMA query_only=ON")
connection.row_factory = sqlite3.Row
row = connection.execute("SELECT arguments_json FROM actions WHERE action_id=?", (ACTION,)).fetchone()
if row is None:
    raise SystemExit("EXACT_ORIGINAL_ACTION_MISSING")
arguments = json.loads(row["arguments_json"])
metadata = {key: arguments[key] for key in ("task_id", "writer_lease_generation", "workspace_id", "workspace_generation", "operation", "target", "source", "facade_contract") if key in arguments}
intent = connection.execute("SELECT task_id,writer_lease_generation,facade_schema_version,facade_profile,facade_contract_sha256 FROM mcp_document_write_intents WHERE action_id=?", (ACTION,)).fetchone()
if intent is None:
    raise SystemExit("EXACT_ORIGINAL_DOCUMENT_INTENT_MISSING")
metadata.update({"task_id": intent["task_id"], "writer_lease_generation": intent["writer_lease_generation"], "facade_contract": {"schema_version": intent["facade_schema_version"], "profile": intent["facade_profile"], "sha256": intent["facade_contract_sha256"]}})
connection.close()
print(json.dumps({"operation": "inspect_original_create_context_metadata", "read_only": True, "observed_at_ms": int(time.time() * 1000), "action_id": ACTION, "metadata": metadata}, separators=(",", ":")))
