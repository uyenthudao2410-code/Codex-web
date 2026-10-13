"""Offline boundary tests; no SSH, credentials, real task, lease or fixture writes."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.error

PATH = Path(__file__).with_name("run-native-first-canary.py")
SPEC = importlib.util.spec_from_file_location("native_first_canary", PATH)
CANARY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CANARY)


class CanaryRecoveryTests(unittest.TestCase):
    def run_lost_response(self, effect_unknown):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.executescript("""
            CREATE TABLE mcp_task_open_idempotency(principal_id,idempotency_key,task_id);
            CREATE TABLE mcp_task_sessions(task_id,binding_id,closed_at_ms);
            CREATE TABLE mcp_task_writer_leases(task_id,lease_generation,released_at_ms);
            CREATE TABLE actions(action_id,device_id,workspace_id,workspace_generation,settled_at_ms);
        """)
        for table in {lane[0] for lane in CANARY.LANES.values()}:
            connection.execute(f"CREATE TABLE {table}(principal_id,idempotency_key,action_id)")
        task_id, action_id, calls = "task_" + "a" * 32, "act_" + "b" * 32, []
        args = SimpleNamespace(principal_id="principal", attempt_id="c" * 32, binding_id="binding",
                               device_id="device", workspace_id="workspace", workspace_generation="generation",
                               service_pid=123, include_approved_build=False)

        class Client:
            def __init__(self, _port, _credential):
                pass

            def call(self, tool, arguments):
                operation = arguments["operation"]
                calls.append((tool, operation))
                if operation == "task_open":
                    connection.execute("INSERT INTO mcp_task_sessions VALUES(?,?,NULL)", (task_id, args.binding_id))
                    connection.execute("INSERT INTO mcp_task_open_idempotency VALUES(?,?,?)", (args.principal_id, arguments["idempotency_key"], task_id))
                    return {"task": {"task_id": task_id}}
                if operation == "writer_claim":
                    if not connection.execute("SELECT 1 FROM mcp_task_writer_leases").fetchone():
                        connection.execute("INSERT INTO mcp_task_writer_leases VALUES(?,7,NULL)", (task_id,))
                    return {"writer_lease": {"state": "held", "task_id": task_id, "binding_id": args.binding_id, "lease_generation": 7}}
                if operation == "read_file":
                    connection.execute("INSERT INTO mcp_file_read_intents VALUES(?,?,?)", (args.principal_id, arguments["idempotency_key"], action_id))
                    connection.execute("INSERT INTO actions VALUES(?,?,?,?,?)", (action_id, args.device_id, args.workspace_id, args.workspace_generation, None if effect_unknown else 1))
                    raise urllib.error.URLError("SECRET_TEST_ERROR_MUST_NOT_BE_EMITTED")
                if operation == "read_status":
                    return {"action": {"action_id": action_id, "settled_at_ms": None if effect_unknown else 1,
                                       "central_lifecycle_state": "reconcile_required" if effect_unknown else "failed"},
                            "reconciliation_required": effect_unknown}
                if operation == "writer_release":
                    connection.execute("UPDATE mcp_task_writer_leases SET released_at_ms=1 WHERE task_id=?", (task_id,))
                    return {}
                if operation == "task_close":
                    connection.execute("UPDATE mcp_task_sessions SET closed_at_ms=1 WHERE task_id=?", (task_id,))
                    return {}
                raise AssertionError("UNEXPECTED_CALL")

        output = io.StringIO()
        with patch.object(CANARY, "service_state", return_value=(8766, connection)), \
                patch.object(CANARY, "credential", return_value="memory-only-test-credential"), \
                patch.object(CANARY, "check_target", return_value={}), \
                patch.object(CANARY, "Mcp", Client), contextlib.redirect_stdout(output):
            exit_code = CANARY.run(args)
        text = output.getvalue()
        self.assertNotIn("SECRET_TEST_ERROR", text)
        self.assertNotIn("memory-only-test-credential", text)
        final = json.loads(text.splitlines()[-1])
        self.assertEqual(exit_code, 1)
        self.assertEqual(final["action_ids"], {"read_001": action_id})
        self.assertEqual(final["task_id"], task_id)
        self.assertEqual(calls.count(("workspace_context", "read_file")), 1)
        self.assertEqual(calls.count(("workspace_context", "task_open")), 1)
        return calls, final

    def test_lost_response_recovers_original_unknown_without_cleanup_or_replacement(self):
        calls, final = self.run_lost_response(True)
        self.assertNotIn(("task_control", "writer_release"), calls)
        self.assertNotIn(("workspace_context", "task_close"), calls)
        self.assertNotIn(("command_control", "exec_stop"), calls)
        self.assertEqual(final["unresolved_original_actions"], ["read_001"])
        self.assertTrue(final["requires_reconciliation"])
        self.assertTrue(final["cleanup_deferred_pending_effect"])

    def test_lost_response_settled_failure_closes_original_task_and_lease(self):
        calls, final = self.run_lost_response(False)
        self.assertEqual(calls.count(("task_control", "writer_release")), 1)
        self.assertEqual(calls.count(("workspace_context", "task_close")), 1)
        self.assertEqual(final["unresolved_original_actions"], [])
        self.assertTrue(final["task_closed_verified"])
        self.assertTrue(final["writer_released_verified"])
        self.assertFalse(final["ok"])


if __name__ == "__main__":
    unittest.main()
