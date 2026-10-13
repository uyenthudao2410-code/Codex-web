"""Offline regression checks for proof rejection and observation safety only."""
import importlib.util
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PATH = Path(__file__).with_name("run-r6-three-stage-exec-canary.py")
spec = importlib.util.spec_from_file_location("prepared_r6_canary", PATH)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class CanaryProofTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript("""
            CREATE TABLE receipts(receipt_id TEXT, action_id TEXT, receipt_state TEXT, payload_json TEXT);
            CREATE TABLE delivery_attempts(attempt_id TEXT, action_id TEXT, attempt_number INTEGER);
            CREATE TABLE mcp_exec_intents(action_id TEXT, argv_json TEXT, task_id TEXT, writer_lease_generation INTEGER);
        """)
        self.args = SimpleNamespace(activation_epoch="epoch-r6", process_instance_id="process-r6",
                                    server_instance_id="server-r6", local_tool_contract_sha256="a" * 64,
                                    service_pid=123, observe_only=True)
        self.contract = {"schema_version": 32, "profile": "control-plane-private-tunnel-service-v1", "sha256": "b" * 64}
        self.runtime = {"activation_epoch_id": self.args.activation_epoch,
                        "process_instance_id": self.args.process_instance_id,
                        "server_instance_id": self.args.server_instance_id,
                        "tool_contract_sha256": self.args.local_tool_contract_sha256}
        self.payload = {"schema_version": 1, "operation_kind": "control_plane_exec",
                        "action_id": "act-original", "attempt_id": "try-original",
                        "task_id": "task-original", "writer_lease_generation": 1,
                        "runtime_identity": self.runtime, "facade_contract": self.contract,
                        "actor": {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron"},
                        "response_sha256": "c" * 64, "stdout": "v24.14.0\n", "stderr": "",
                        "exit_code": 0, "timed_out": False, "truncated": False,
                        "job_id": "job-original", "command_id": "command-original"}
        self.result = {"execution": "completed_exec_relay", "process_state": "completed", "exit_code": 0,
                       "action": {"action_id": "act-original", "settled_at_ms": 1234},
                       "exec": {"receipt_id": "rcpt-original", "response_sha256": "c" * 64}}
        self.connection.execute("INSERT INTO receipts VALUES(?,?,?,?)", ("rcpt-original", "act-original", "completed", json.dumps(self.payload)))
        self.connection.execute("INSERT INTO delivery_attempts VALUES(?,?,?)", ("try-original", "act-original", 1))
        self.connection.execute("INSERT INTO mcp_exec_intents VALUES(?,?,?,?)", ("act-original", json.dumps({"argv": ["node", "--version"]}), "task-original", 1))
        self.calls = []

        def call(name, arguments):
            self.calls.append((name, arguments))
            self.assertEqual(name, "exec_command")
            self.assertEqual(arguments, {"operation": "exec_status", "action_id": "act-original"})
            return self.result

        self.client = SimpleNamespace(call=call)

    def tearDown(self):
        self.connection.close()

    def update_payload(self):
        self.connection.execute("UPDATE receipts SET payload_json=?", (json.dumps(self.payload),))

    def proof(self):
        return helper.verified_version(self.connection, self.client, self.args, self.contract,
                                       "task-original", 1, "cold", "act-original")

    def test_exact_version_original_lineage_passes(self):
        proof = self.proof()
        self.assertEqual(proof["version"], "v24.14.0")
        self.assertEqual(proof["job_id"], "job-original")
        self.assertEqual(proof["attempt_number"], 1)

    def test_version_trailing_text_is_rejected_without_printing_output(self):
        self.payload["stdout"] += "unexpected token\n"
        self.update_payload()
        with self.assertRaisesRegex(RuntimeError, "EXACT_NODE_VERSION_OUTPUT_NOT_VERIFIED"):
            self.proof()

    def test_second_delivery_attempt_cannot_be_proof(self):
        self.connection.execute("INSERT INTO delivery_attempts VALUES(?,?,?)", ("try-second", "act-original", 2))
        with self.assertRaisesRegex(RuntimeError, "ORIGINAL_ACTION_HAS_UNEXPECTED_DELIVERY_ATTEMPTS"):
            self.proof()

    def test_wrong_runtime_identity_cannot_be_proof(self):
        self.payload["runtime_identity"] = {**self.runtime, "activation_epoch_id": "old-epoch"}
        self.update_payload()
        with self.assertRaisesRegex(RuntimeError, "RECEIPT_IDENTITY_NOT_EXACT"):
            self.proof()

    def test_changed_structured_argv_cannot_be_proof(self):
        self.connection.execute("UPDATE mcp_exec_intents SET argv_json=?", (json.dumps({"argv": ["node", "--version", "extra"]}),))
        with self.assertRaisesRegex(RuntimeError, "ORIGINAL_STRUCTURED_NODE_VERSION_INTENT_CHANGED"):
            self.proof()

    def test_failed_terminal_receipt_cannot_be_success(self):
        self.connection.execute("UPDATE receipts SET receipt_state='failed'")
        with self.assertRaisesRegex(RuntimeError, "VERIFIED_RECEIPT_NOT_FOUND"):
            self.proof()

    def test_observe_only_does_not_renew_or_dispatch(self):
        with patch.object(helper, "service_state_pid", return_value=123), \
             patch.object(helper, "renew", side_effect=AssertionError("mutation forbidden")), \
             patch.object(helper, "check_target", side_effect=AssertionError("no admission call needed")):
            result = helper.observe(self.client, self.connection, self.args, self.contract,
                                    "task-original", 1, "cold", "act-original")
        self.assertIs(result, self.result)
        self.assertEqual(len(self.calls), 1)

    def test_unknown_observation_returns_original_without_replacement(self):
        self.result = {"action": {"action_id": "act-original", "settled_at_ms": None}, "reconciliation_required": True}
        with patch.object(helper, "service_state_pid", return_value=123), \
             patch.object(helper, "renew", side_effect=AssertionError("mutation forbidden")):
            result = helper.observe(self.client, self.connection, self.args, self.contract,
                                    "task-original", 1, "cold", "act-original")
        self.assertTrue(result["reconciliation_required"])
        self.assertEqual(len(self.calls), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
