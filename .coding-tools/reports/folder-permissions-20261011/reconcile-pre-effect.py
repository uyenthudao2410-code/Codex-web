"""Submit one independently proven pre-effect rejection without journal edits."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[3]
REPORTS = Path(__file__).resolve().parent
AGENT = ROOT / "dist/windows-candidate-mxc-wsb-cbe1774-folders-unified-1011-r2/win-unpacked/resources/resources/control-plane/node_agent.py"
ACTION = "act_16f5443e532942019fa7bb43868b34b0"
ATTEMPT = "try_5239ead2bf2b459e8e175c623362b8cc"
EXPECTED = "742976da6d38a49f35c48b5824eea2badc1e98258dd74d8c34720f08f09a14cb"
connection = sqlite3.connect((ROOT / ".coding-tools/orchestration/ledger.sqlite3").as_uri() + "?mode=ro", uri=True)
connection.row_factory = sqlite3.Row
row = connection.execute("SELECT * FROM background_operations WHERE operation_id=?", ("HAt4M_RQNok1GYYb",)).fetchone()
summary = json.loads(row["summary_json"])
assert row["status"] == "failed" and not row["run_id"] and not row["wave_id"]
assert summary["worker_terminalized"] is True
assert summary["request_id"] == "control-plane-approved-patch-workflow-46f19dc2e6ddfea9549cb93b"
assert summary["error"]["message"] == "arguments.include_diff is not a recognized argument."
assert hashlib.sha256((REPORTS / "read-write-fixture.txt").read_bytes()).hexdigest() == EXPECTED
profile = Path(os.environ["APPDATA"]) / "web-mcp-assistant"
journal_path = profile / "control-plane-node.json.approved-patch-bridge-journal.json"
journal_before = journal_path.read_bytes()
original = json.loads(journal_before)["entries"][ACTION + "|" + ATTEMPT]
assert original["state"] == "unknown" and original["receipt"]["receipt_submitted"] is True
assert original["receipt"]["payload"]["diagnostic_code"] == "CONTROL_PLANE_APPROVED_PATCH_MCP_REJECTED"
spec = importlib.util.spec_from_file_location("approved_node_agent", AGENT)
agent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = agent
spec.loader.exec_module(agent)
config = agent._config(profile / "control-plane-node.json")
assert config["device_id"] == "72ceec2d-e3f2-472f-8e3c-99fffe053035"
receipt = agent._approved_patch_journal_receipt(ACTION, ATTEMPT, "rejected", "", {
    "schema_version": 1, "operation_kind": "control_plane_approved_patch",
    "code": "CONTROL_PLANE_APPROVED_PATCH_SCHEMA_REJECTED_BEFORE_EFFECT",
    "reconciliation": {
        "operation_id": row["operation_id"], "request_id": summary["request_id"],
        "worker_terminalized": True, "run_created": False, "wave_created": False,
        "preimage_sha256": EXPECTED, "local_evidence": "pre-effect-rejection.json",
        "reason": "Schema validation rejected include_diff before workflow mutation; exact preimage remains unchanged",
    },
})
entry = {"receipt": receipt}
# Preserve a separate evidence record before the network mutation. The original
# UNKNOWN journal is immutable evidence and is never overwritten here.
evidence = REPORTS / "terminal-reconciliation-receipt.json"
evidence.write_text(json.dumps(entry, indent=2) + "\n")
try:
    response = agent._submit_receipt(config, entry)
    assert response["delivery_state"] == "settled" and response["receipt_state"] == "rejected"
    assert journal_path.read_bytes() == journal_before
    evidence.write_text(json.dumps({**entry, "server_receipt": response, "original_journal_preserved": True}, indent=2) + "\n")
    print(json.dumps({"ok": True, "action_id": ACTION, "state": "settled", "receipt_state": "rejected",
                      "original_journal_preserved": True}))
except Exception as error:
    print(json.dumps({"ok": False, "error": type(error).__name__}))
    sys.exit(1)
