"""Offline receipt-loss and routing-negative boundaries; no live integrations."""
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("isolated_idle_under_test", HERE / "run-isolated-idle-canary-timefix.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class Row:
    def __init__(self, values):
        self.values = values

    def fetchone(self):
        return self.values[0] if self.values else None

    def fetchall(self):
        return self.values


class Connection:
    def execute(self, sql, _args):
        if "lease_generation FROM" in sql:
            return Row([("lease",)])
        if "closed_at_ms FROM" in sql:
            return Row([(1,)])
        return Row([(0,)])

    def close(self):
        pass


class BoundaryTests(unittest.TestCase):
    def reviewed_main(self, pins):
        raw = json.dumps(pins).encode()
        targets = [SimpleNamespace(workspace_label="Codex-web")]
        argv = ["run-isolated-idle-canary-timefix.py", "--attempt-id", "c" * 32,
                "--reviewed-pins-sha256", runner.base.sha(raw), "--credential-file", "not-read",
                "--execute-confirmed-isolated-idle-canary"]
        with patch.object(sys, "argv", argv), patch.dict(runner.__dict__, {"_REVIEWED_PINS_BYTES": raw}), \
                patch.object(runner.overlap, "reviewed_targets", return_value=targets) as reviewed, \
                patch.object(runner, "run", return_value=0):
            result = runner.main()
        return result, reviewed

    def test_native_pins_cannot_be_reused_for_idle_dispatch(self):
        with self.assertRaisesRegex(RuntimeError, "REVIEWED_ISOLATED_IDLE_APPROVAL_REQUIRED"):
            self.reviewed_main({"isolated_idle_approved": True, "purpose": "native-overlap"})

    def test_idle_pins_use_exact_isolated_target_reader(self):
        pins = {"isolated_idle_approved": True, "purpose": "isolated-idle"}
        result, reviewed = self.reviewed_main(pins)
        self.assertEqual(result, 0)
        reviewed.assert_called_once_with(pins, "not-read", require_native_fixture=False)

    def exercise(self, *, lose_response=False, unknown=False, metadata=None, empty_lineage=False):
        calls = []
        recovered = {"task": None, "action": None}
        task, action = "task_" + "a" * 32, "act_" + "b" * 32
        args = SimpleNamespace(principal_id="principal", binding_id="binding", workspace_label="Codex-web",
                               workspace_id="workspace", workspace_generation="generation", retained_unknown_actions=[])
        proof = {"receipt_id": "receipt", "action_id": action, "attempt_number": 1}
        payload = {**(metadata or runner.METADATA), "status": "exited", "timed_out": False, "truncated": False,
                   "stderr": "", "stdout": "v22.1.0\n", "local_handle": "handle", "job_id": "job",
                   "command_id": "command", "run_id": "run", "wave_id": "wave"}
        if empty_lineage:
            payload.update(run_id="", wave_id="")
        result = {"execution": "completed_exec_relay", "process_state": "completed", "exit_code": 0,
                  "exec": {**payload}, "action": {"action_id": action, "settled_at_ms": None if unknown else 1}}

        class Client:
            def call(self, name, value):
                calls.append((name, value))
                if value["operation"] == "task_open":
                    recovered["task"] = task
                    return {"task": {"task_id": task}}
                if value["operation"] == "writer_claim":
                    return {"writer_lease": {"state": "held", "task_id": task, "binding_id": "binding", "lease_generation": "lease"}}
                if value["operation"] == "exec_run":
                    recovered["action"] = action
                    if lose_response:
                        raise RuntimeError("TRANSPORT_RESPONSE_LOST")
                    return {"action_id": action, "replayed": False}
                if value["operation"] == "exec_output":
                    return {"has_output": True, "exit_code": 0, "truncated": False, **(metadata or runner.METADATA)}
                return {}

        def recover(*_):
            return recovered["task"], {runner.LANE: recovered["action"]} if recovered["action"] else {}

        emitted = []
        with patch.object(runner.base, "service_state", return_value=(1, Connection())), \
                patch.object(runner.base, "credential", return_value="never-output-test-token"), \
                patch.object(runner.base, "Mcp", return_value=Client()), \
                patch.object(runner.base, "recover", side_effect=recover), \
                patch.object(runner.base, "check_target", return_value={"sha256": "contract"}), \
                patch.object(runner.overlap, "verify_existing_unsettled"), \
                patch.object(runner.base, "observe", return_value=result), \
                patch.object(runner.base, "unknown", return_value=unknown), \
                patch.object(runner.base, "receipt", return_value=(payload, proof)), \
                patch.object(runner, "emit", side_effect=lambda phase, **values: emitted.append((phase, values))):
            status = runner.run(SimpleNamespace(attempt_id="c" * 32), args)
        return status, calls, emitted[-1][1]

    def test_only_one_trusted_action_and_settled_cleanup(self):
        status, calls, report = self.exercise()
        self.assertEqual(status, 0)
        dispatched = [value for _, value in calls if value["operation"] == "exec_run"]
        self.assertEqual(len(dispatched), 1)
        self.assertEqual(dispatched[0]["argv"], ["node", "--version"])
        self.assertTrue(report["task_closed_verified"])
        self.assertFalse(any(value["operation"] == "exec_stop" for _, value in calls))

    def test_lost_response_recovers_original_without_redispatch(self):
        status, calls, report = self.exercise(lose_response=True)
        self.assertEqual(status, 1)
        self.assertEqual(sum(value["operation"] == "exec_run" for _, value in calls), 1)
        self.assertEqual(report["action_id"], "act_" + "b" * 32)
        self.assertTrue(report["task_closed_verified"])
        self.assertFalse(report["requires_reconciliation"])

    def test_unknown_original_defers_cleanup_and_never_stops(self):
        status, calls, report = self.exercise(lose_response=True, unknown=True)
        self.assertEqual(status, 1)
        self.assertTrue(report["cleanup_deferred_pending_effect"])
        self.assertFalse(any(value["operation"] in {"writer_release", "task_close", "exec_stop"} for _, value in calls))

    def test_native_receipt_cannot_pass_isolated_acceptance(self):
        status, calls, report = self.exercise(metadata={"execution_backend": "native", "isolation_level": "process_container",
                                                      "policy_decision": "native_safe_command"})
        self.assertEqual(status, 1)
        self.assertEqual(report["error_code"], "ISOLATED_ROUTING_NOT_EXACT")
        self.assertEqual(sum(value["operation"] == "exec_run" for _, value in calls), 1)

    def test_isolated_hypervisor_allows_empty_workflow_lineage_ids(self):
        status, calls, report = self.exercise(
            metadata={"execution_backend": "isolated", "isolation_level": "hypervisor",
                      "policy_decision": "isolated_preferred"}, empty_lineage=True)
        self.assertEqual(status, 0)
        self.assertEqual(sum(value["operation"] == "exec_run" for _, value in calls), 1)
        self.assertEqual(report["proof"]["run_id"], "")
        self.assertEqual(report["proof"]["wave_id"], "")


if __name__ == "__main__":
    unittest.main()
