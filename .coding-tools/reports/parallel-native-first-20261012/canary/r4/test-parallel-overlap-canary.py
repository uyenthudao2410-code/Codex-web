"""Offline safety and overlap boundaries; no credentials, SSH or real fixtures."""

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
import time

SPEC = importlib.util.spec_from_file_location("parallel_overlap_canary", Path(__file__).with_name("run-parallel-overlap-canary.py"))
CANARY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CANARY)


class ReviewedPinTests(unittest.TestCase):
    def pins(self):
        pins = {"schema_version": 1, "service_pid": 123, "facade_schema_version": 34,
                **{key: "reviewed_" + key for key in CANARY.COMMON_IDENTITIES},
                **{key: "a" * 64 for key in CANARY.COMMON_DIGESTS}}
        pins["targets"] = [{"workspace_label": label,
            **{key: "reviewed_" + key + str(index) for key in CANARY.TARGET_IDENTITIES},
            "activation_verified": True, "native_fixture_explicitly_approved": True,
            "native_argv": ["node", CANARY.FIXTURE + "/hold.cjs"], "native_cwd": "",
            "native_source_sha256": CANARY.base.sha(CANARY.hold_source(label).encode()),
            "exec_policy_sha256": str(index + 1) * 64} for index, label in enumerate(CANARY.LABELS)]
        return pins

    def test_both_exact_scopes_and_native_source_approvals_are_required(self):
        pins = self.pins()
        targets = CANARY.reviewed_targets(pins, "/protected/credential")
        self.assertEqual([target.workspace_label for target in targets], list(CANARY.LABELS))
        pins["targets"][1]["native_fixture_explicitly_approved"] = False
        with self.assertRaisesRegex(RuntimeError, "APPROVAL_REQUIRED"):
            CANARY.reviewed_targets(pins, "/protected/credential")
        pins = self.pins()
        pins["targets"][1]["binding_id"] = pins["targets"][0]["binding_id"]
        with self.assertRaisesRegex(RuntimeError, "NOT_DISTINCT"):
            CANARY.reviewed_targets(pins, "/protected/credential")
        pins = self.pins()
        pins["targets"][1]["native_source_sha256"] = pins["targets"][0]["native_source_sha256"]
        with self.assertRaisesRegex(RuntimeError, "FIXTURE_PIN_REQUIRED"):
            CANARY.reviewed_targets(pins, "/protected/credential")
        pins = self.pins()
        pins["targets"][0]["retained_unknown_actions"] = ["act_" + str(index) * 32 for index in range(3)]
        with self.assertRaisesRegex(RuntimeError, "ALLOWLIST_REQUIRED"):
            CANARY.reviewed_targets(pins, "/protected/credential")

    def test_timestamps_prove_intersection_and_reject_sequential_or_same_jobs(self):
        first = {"job_id": "job1", "command_id": "command1", "pid": 11, "started_at_ms": 100, "finished_at_ms": 5100}
        second = {"job_id": "job2", "command_id": "command2", "pid": 12, "started_at_ms": 1200, "finished_at_ms": 6200}
        self.assertEqual(CANARY.verify_overlap([first, second])["overlap_duration_ms"], 3900)
        with self.assertRaisesRegex(RuntimeError, "DO_NOT_OVERLAP"):
            CANARY.verify_overlap([first, {**second, "started_at_ms": 5100}])
        with self.assertRaisesRegex(RuntimeError, "NOT_DISTINCT"):
            CANARY.verify_overlap([first, {**second, "job_id": "job1"}])

    def test_only_exact_expired_canonical_quarantine_allowlist_can_pass_without_writes(self):
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        connection.row_factory = sqlite3.Row
        connection.execute("CREATE TABLE actions(action_id,device_id,workspace_id,workspace_generation,expires_at_ms,settled_at_ms)")
        ids = ["act_" + str(index) * 32 for index in range(3)]
        args = SimpleNamespace(workspace_label="Autocad", device_id="device", workspace_id="workspace",
                               workspace_generation="generation", principal_id="principal", binding_id="binding",
                               retained_unknown_actions=ids)
        expired = int(time.time() * 1000) - 1000
        for action_id in ids:
            connection.execute("INSERT INTO actions VALUES(?,?,?,?,?,NULL)", (action_id, args.device_id,
                               args.workspace_id, args.workspace_generation, expired))
        changes = connection.total_changes
        with patch.object(CANARY, "canonical_quarantine_verifier") as load, contextlib.redirect_stdout(io.StringIO()):
            predicate = load.return_value
            predicate.return_value = True
            CANARY.verify_existing_unsettled(args, connection)
            self.assertEqual(predicate.call_count, 3)
            self.assertEqual(predicate.call_args.kwargs["binding_id"], args.binding_id)
            self.assertEqual(predicate.call_args.kwargs["principal_id"], args.principal_id)
            self.assertEqual(predicate.call_args.kwargs["workspace_generation"], args.workspace_generation)
            self.assertEqual(connection.total_changes, changes, "quarantine verification must be read-only")
            predicate.return_value = False
            with self.assertRaisesRegex(RuntimeError, "QUARANTINE_NOT_EXACT"):
                CANARY.verify_existing_unsettled(args, connection)
            predicate.return_value = True
            connection.execute("UPDATE actions SET expires_at_ms=? WHERE action_id=?", (expired + 60000, ids[0]))
            with self.assertRaisesRegex(RuntimeError, "QUARANTINE_NOT_EXACT"):
                CANARY.verify_existing_unsettled(args, connection)
            connection.execute("UPDATE actions SET expires_at_ms=?", (expired,))
            connection.execute("INSERT INTO actions VALUES(?,?,?,?,?,NULL)", ("act_" + "e" * 32, args.device_id,
                               args.workspace_id, args.workspace_generation, expired))
            with self.assertRaisesRegex(RuntimeError, "UNREVIEWED_UNSETTLED_ACTION"):
                CANARY.verify_existing_unsettled(args, connection)


class OriginalHandleRecoveryTests(unittest.TestCase):
    def lost_response(self, effect_unknown):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.executescript("""
            CREATE TABLE mcp_task_open_idempotency(principal_id,idempotency_key,task_id);
            CREATE TABLE mcp_task_sessions(task_id,binding_id,closed_at_ms);
            CREATE TABLE mcp_task_writer_leases(task_id,lease_generation,released_at_ms);
            CREATE TABLE actions(action_id,device_id,workspace_id,workspace_generation,settled_at_ms);
        """)
        for table in {lane[0] for lane in CANARY.base.LANES.values()}:
            connection.execute(f"CREATE TABLE {table}(principal_id,idempotency_key,action_id)")
        pins = ReviewedPinTests().pins()
        targets = CANARY.reviewed_targets(pins, "/protected/credential")
        args = SimpleNamespace(attempt_id="c" * 32, reviewed_pins_sha256="d" * 64)
        action_id, calls, task_bindings = "act_" + "e" * 32, [], {}

        class Client:
            def __init__(self, _port, _credential):
                pass

            def call(self, tool, arguments):
                operation = arguments["operation"]
                calls.append((tool, operation, arguments.copy()))
                if operation == "task_open":
                    index = next(index for index, target in enumerate(targets) if target.binding_id == arguments["binding_id"])
                    task_id = "task_" + str(index + 1) * 32
                    task_bindings[task_id] = arguments["binding_id"]
                    connection.execute("INSERT INTO mcp_task_sessions VALUES(?,?,NULL)", (task_id, arguments["binding_id"]))
                    connection.execute("INSERT INTO mcp_task_open_idempotency VALUES(?,?,?)",
                                       (targets[index].principal_id, arguments["idempotency_key"], task_id))
                    return {"task": {"task_id": task_id}}
                if operation == "writer_claim":
                    task_id = arguments["task_id"]
                    if not connection.execute("SELECT 1 FROM mcp_task_writer_leases WHERE task_id=?", (task_id,)).fetchone():
                        connection.execute("INSERT INTO mcp_task_writer_leases VALUES(?,7,NULL)", (task_id,))
                    return {"writer_lease": {"state": "held", "task_id": task_id,
                            "binding_id": task_bindings[task_id], "lease_generation": 7}}
                if operation == "read_file":
                    held = connection.execute("SELECT COUNT(*) FROM mcp_task_writer_leases WHERE released_at_ms IS NULL").fetchone()[0]
                    if held != 2:
                        raise AssertionError("BOTH_WRITER_LEASES_MUST_BE_HELD")
                    target = targets[0]
                    connection.execute("INSERT INTO mcp_file_read_intents VALUES(?,?,?)",
                                       (target.principal_id, arguments["idempotency_key"], action_id))
                    connection.execute("INSERT INTO actions VALUES(?,?,?,?,?)", (action_id, target.device_id,
                                       target.workspace_id, target.workspace_generation, None if effect_unknown else 1))
                    raise urllib.error.URLError("PRIVATE_ERROR_MUST_NOT_BE_EMITTED")
                if operation == "read_status":
                    return {"action": {"action_id": action_id, "settled_at_ms": None if effect_unknown else 1,
                            "central_lifecycle_state": "reconcile_required" if effect_unknown else "failed"},
                            "reconciliation_required": effect_unknown}
                if operation == "writer_release":
                    connection.execute("UPDATE mcp_task_writer_leases SET released_at_ms=1 WHERE task_id=?", (arguments["task_id"],))
                    return {}
                if operation == "task_close":
                    connection.execute("UPDATE mcp_task_sessions SET closed_at_ms=1 WHERE task_id=?", (arguments["task_id"],))
                    return {}
                raise AssertionError("UNEXPECTED_CALL")

        output = io.StringIO()
        with patch.object(CANARY.base, "service_state", return_value=(8766, connection)), \
                patch.object(CANARY.base, "credential", return_value="private-memory-only-credential"), \
                patch.object(CANARY.base, "check_target", return_value={}), \
                patch.object(CANARY.base, "Mcp", Client), contextlib.redirect_stdout(output):
            exit_code = CANARY.run(args, targets)
        text = output.getvalue()
        self.assertNotIn("PRIVATE_ERROR", text)
        self.assertNotIn("private-memory-only-credential", text)
        final = json.loads(text.splitlines()[-1])
        self.assertEqual(exit_code, 1)
        self.assertEqual(sum(operation == "task_open" for _, operation, _ in calls), 2)
        self.assertEqual(sum(operation == "read_file" for _, operation, _ in calls), 1)
        self.assertFalse(any(operation in ("exec_run", "exec_stop") for _, operation, _ in calls))
        self.assertEqual(final["targets"][0]["action_ids"], {"read_probe": action_id})
        self.assertTrue(final["targets"][1]["task_closed_verified"])
        self.assertTrue(final["targets"][1]["writer_released_verified"])
        return calls, final

    def test_lost_unknown_keeps_original_root_open_and_closes_other_root_independently(self):
        calls, final = self.lost_response(True)
        first = final["targets"][0]
        self.assertTrue(first["requires_reconciliation"])
        self.assertTrue(first["cleanup_deferred_pending_effect"])
        self.assertEqual(first["unresolved_original_actions"], ["read_probe"])
        self.assertFalse(any(operation in ("writer_release", "task_close") and arguments["task_id"] == first["task_id"]
                             for _, operation, arguments in calls))

    def test_lost_settled_failure_recovers_original_action_and_closes_both_original_tasks(self):
        calls, final = self.lost_response(False)
        for target in final["targets"]:
            self.assertFalse(target["requires_reconciliation"])
            self.assertTrue(target["task_closed_verified"])
            self.assertTrue(target["writer_released_verified"])
        self.assertEqual(sum(operation == "writer_release" for _, operation, _ in calls), 2)
        self.assertEqual(sum(operation == "task_close" for _, operation, _ in calls), 2)


class ClientReconnectTests(unittest.TestCase):
    def reconnect(self, duplicate_intent=False):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute("CREATE TABLE mcp_exec_intents(principal_id,idempotency_key,action_id)")
        targets = CANARY.reviewed_targets(ReviewedPinTests().pins(), "/protected/credential")
        clients, sessions, queued = [], [], []

        class Client:
            def __init__(self, port, credential):
                clients.append(self)

        class Session:
            def __init__(self, args, database, client, attempt):
                self.args, self.client = args, client
                self.attempt = "parallel-overlap-20261012:" + attempt + ":" + args.workspace_label
                self.task_id = "task-original-" + str(len(sessions))
                self.contract, self.generation, self.actions = {}, 7, {}
                sessions.append(self)

            def open(self):
                pass

            def read(self, *args, **kwargs):
                pass

            def patch(self):
                pass

            def queue(self, lane, arguments):
                action = "action-original-" + str(sessions.index(self))
                self.actions[lane] = action
                queued.append((self.client, action))
                connection.execute("INSERT INTO mcp_exec_intents VALUES(?,?,?)",
                                   (self.args.principal_id, self.attempt + ":" + lane, action))

            def running_receipt(self):
                index = sessions.index(self)
                return {"job_id": "job-original-" + str(index), "command_id": "command-original-" + str(index),
                        "local_handle": "handle-original-" + str(index)}

            def native_completion(self, running):
                index = sessions.index(self)
                if self.client is not clients[1] or running != self.running_receipt():
                    raise AssertionError("RECONNECT_MUST_PRESERVE_ORIGINAL_HANDLES")
                if duplicate_intent and index == 0:
                    connection.execute("INSERT INTO mcp_exec_intents VALUES(?,?,?)",
                                       (self.args.principal_id, self.attempt + ":second-exec", "action-forbidden-second"))
                return {**running, "pid": index + 11, "started_at_ms": 1000 + index * 1000,
                        "finished_at_ms": 6000 + index * 1000}

            def cleanup(self):
                return {"ok": True, "task_id": self.task_id, "action_ids": self.actions.copy()}

        output = io.StringIO()
        with patch.object(CANARY, "Session", Session), patch.object(CANARY.base, "service_state", return_value=(8766, connection)), \
                patch.object(CANARY.base, "credential", return_value="PRIVATE_CREDENTIAL"), \
                patch.object(CANARY.base, "check_target", return_value={}), patch.object(CANARY.base, "Mcp", Client), \
                contextlib.redirect_stdout(output):
            code = CANARY.run(SimpleNamespace(attempt_id="c" * 32, reviewed_pins_sha256="d" * 64), targets)
        self.assertEqual(len(clients), 2)
        self.assertEqual(len(queued), 2)
        self.assertTrue(all(client is clients[0] for client, _ in queued))
        self.assertNotIn("PRIVATE_CREDENTIAL", output.getvalue())
        final = json.loads(output.getvalue().splitlines()[-1])
        self.assertEqual([target["action_ids"]["node_overlap"] for target in final["targets"]],
                         [action for _, action in queued])
        return code, final

    def test_client_recreated_original_handles_observed_without_second_exec(self):
        code, final = self.reconnect()
        self.assertEqual(code, 0)
        self.assertTrue(final["observation_client_recreated"])
        self.assertEqual(final["reconnect_scope"], "client_transport_only")
        self.assertTrue(final["no_second_exec_verified"])
        self.assertEqual(final["overlap"]["overlap_duration_ms"], 4000)

    def test_second_exec_intent_after_reconnect_fails_even_with_overlap(self):
        code, final = self.reconnect(duplicate_intent=True)
        self.assertEqual(code, 1)
        self.assertEqual(final["error_code"], "SECOND_EXEC_INTENT_DETECTED_AFTER_RECONNECT")


if __name__ == "__main__":
    unittest.main()
