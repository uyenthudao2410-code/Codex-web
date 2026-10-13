"""Close only the original task after its exact rejected-result reconciliation."""
import json
from types import SimpleNamespace

base = _BASE_CANARY
pins = json.loads(_REVIEWED_PINS_BYTES.decode("utf-8-sig"))
args = SimpleNamespace(**pins)
args.credential_file = "/home/svhome/.config/codex-control-plane/ubuntu-root-mcp-authorization"
TASK = "task_cd3ea31140794fbcb5c598eb29cb9c90"
ACTION = "act_1de2cef3dc304d6e8b3f90237d7c136a"
ATTEMPT = "try_8d31c7cfb661441aadb9e620e47508a3"
UNKNOWN = "rcpt_03cb8c766afb4a0ab6d5f9c53c75f317"
REJECTED = "rcpt_c1fc74bc54894262995bad367d76b214"
phase = "preflight"
try:
    port, connection = base.service_state(args)
    client = base.Mcp(port, base.credential(args, connection))
    contract = base.check_target(args, connection, client)
    task = connection.execute("SELECT * FROM mcp_task_sessions WHERE task_id=?", (TASK,)).fetchone()
    base.require(task is not None and task["closed_at_ms"] is None and task["binding_id"] == args.binding_id
                 and task["principal_id"] == args.principal_id and task["workspace_generation"] == args.workspace_generation,
                 "EXACT_ORIGINAL_OPEN_TASK_REQUIRED")
    action = connection.execute("SELECT a.*, l.task_id FROM actions a JOIN mcp_task_action_links l ON l.action_id=a.action_id WHERE a.action_id=?", (ACTION,)).fetchone()
    base.require(action is not None and action["task_id"] == TASK and action["delivery_state"] == "settled"
                 and action["settled_at_ms"] is not None, "EXACT_ORIGINAL_SETTLED_ACTION_REQUIRED")
    attempts = connection.execute("SELECT attempt_id FROM delivery_attempts WHERE action_id=?", (ACTION,)).fetchall()
    base.require(len(attempts) == 1 and attempts[0][0] == ATTEMPT, "ORIGINAL_ATTEMPT_CHANGED")
    receipts = [dict(row) for row in connection.execute("SELECT * FROM receipts WHERE action_id=? ORDER BY receipt_id", (ACTION,))]
    base.require(len(receipts) == 2 and {(r["receipt_id"], r["receipt_state"]) for r in receipts}
                 == {(UNKNOWN, "unknown"), (REJECTED, "rejected")}, "ORIGINAL_UNKNOWN_AND_REJECTION_REQUIRED")
    base.require(connection.execute("SELECT COUNT(*) FROM actions a JOIN mcp_task_action_links l ON l.action_id=a.action_id WHERE l.task_id=? AND a.settled_at_ms IS NULL", (TASK,)).fetchone()[0] == 0,
                 "ORIGINAL_TASK_HAS_UNSETTLED_ACTIONS")
    phase = "writer_release"
    client.call("task_control", {"operation": "writer_release", "task_id": TASK, "reason": "original_read067_result_rejected_no_success_claim"})
    phase = "task_close"
    client.call("workspace_context", {"operation": "task_close", "task_id": TASK})
    base.require(connection.execute("SELECT closed_at_ms FROM mcp_task_sessions WHERE task_id=?", (TASK,)).fetchone()[0] is not None
                 and connection.execute("SELECT COUNT(*) FROM mcp_task_writer_leases WHERE task_id=? AND released_at_ms IS NULL", (TASK,)).fetchone()[0] == 0,
                 "EXACT_ORIGINAL_TASK_CLEANUP_NOT_CONFIRMED")
    base.require([dict(row) for row in connection.execute("SELECT * FROM receipts WHERE action_id=? ORDER BY receipt_id", (ACTION,))] == receipts,
                 "ORIGINAL_RECEIPTS_CHANGED_DURING_TASK_CLEANUP")
    base.require(base.check_target(args, connection, client) == contract, "CURRENT_RUNTIME_CHANGED_DURING_CLEANUP")
    print(json.dumps({"operation": "close_exact_read067_task", "ok": True, "task_id": TASK, "action_id": ACTION,
                      "task_closed_verified": True, "writer_released_verified": True, "unknown_receipt_preserved": True,
                      "action_redispatched": False, "read_success_claimed": False}))
except Exception as error:
    print(json.dumps({"operation": "close_exact_read067_task", "ok": False, "phase": phase, "error_code": base.error_code(error),
                      "automatic_retry_forbidden": True, "next_action": "Observe exact original task and writer before retry."}))
    raise SystemExit(1)
