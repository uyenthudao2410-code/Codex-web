"""Offline one-poll and exact-runtime guards; never execute adapter/network."""
import argparse
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location("operator_poll", Path(__file__).with_name("operator-scoped-poll-once.py"))
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class SupportedPollTests(unittest.TestCase):
    def fixture(self):
        pins = {"process_instance_id": "process-reviewed", "server_instance_id": "server-reviewed",
                "activation_epoch": "activation-reviewed", "local_tool_contract_sha256": "a" * 64}
        identity = {"runtime_instance_id": pins["process_instance_id"], "mcp_server_instance_id": pins["server_instance_id"],
                    "activation_epoch": pins["activation_epoch"], "contract_version": "sha256:" + "a" * 64}
        def poll(args):
            print(json.dumps({"execution": "file_read_once", "received_action_ids": ["act_" + "b" * 32],
                              "completed_action_ids": ["act_" + "b" * 32], "submitted_receipts": 1}))
            return 0
        agent = SimpleNamespace(observed_runtime_identity=Mock(return_value=identity), recovery_identity_observation=Mock(),
            poll_file_read_once=Mock(side_effect=poll), poll_approved_patch_once=Mock(), poll_exec_once=Mock())
        args = argparse.Namespace(project_root="reviewed-candidate", workspace_id="reviewed-workspace", workspace_generation="reviewed-generation")
        return agent, args, pins

    def test_one_public_poller_receives_exact_namespace_once(self):
        agent, args, pins = self.fixture()
        receipt = helper.invoke(agent, args, pins, "read")
        agent.poll_file_read_once.assert_called_once_with(args)
        agent.poll_approved_patch_once.assert_not_called()
        agent.poll_exec_once.assert_not_called()
        self.assertEqual(receipt["submitted_receipts"], 1)

    def test_changed_runtime_blocks_before_shared_lock_poller(self):
        agent, args, pins = self.fixture()
        pins["activation_epoch"] = "activation-retired"
        with self.assertRaisesRegex(RuntimeError, "EXACT_CURRENT_READY_RUNTIME"):
            helper.invoke(agent, args, pins, "read")
        agent.poll_file_read_once.assert_not_called()

    def test_busy_poller_failure_is_not_retried(self):
        agent, args, pins = self.fixture()
        agent.poll_file_read_once.side_effect = RuntimeError("CONTROL_PLANE_FILE_READ_POLL_ALREADY_RUNNING")
        with self.assertRaisesRegex(RuntimeError, "POLL_ALREADY_RUNNING"):
            helper.invoke(agent, args, pins, "read")
        agent.poll_file_read_once.assert_called_once_with(args)

    def test_terminal_canary_stops_assistance_without_any_poll(self):
        agent, args, pins = self.fixture()
        with patch.object(helper, "active_original", return_value=(None, {"ok": True})):
            result = helper.assist(agent, args, pins, Path("unused"), 160, 900, Mock())
        self.assertEqual(result["stop_reason"], "original_canary_terminal")
        self.assertEqual(result["poll_count"], 0)
        agent.poll_file_read_once.assert_not_called()

    def test_unknown_poll_stops_before_next_admitted_action(self):
        agent, args, pins = self.fixture()
        original = {"lane": "read", "canary_lane": "read_001", "action_id": "act_" + "b" * 32}
        def unknown(args):
            print(json.dumps({"execution": "file_read_once", "received_action_ids": [original["action_id"]],
                              "unknown_action_ids": [original["action_id"]]}))
            return 0
        agent.poll_file_read_once.side_effect = unknown
        with patch.object(helper, "active_original", return_value=(original, None)):
            result = helper.assist(agent, args, pins, Path("unused"), 160, 900, Mock())
        self.assertFalse(result["ok"])
        self.assertEqual(result["stop_reason"], "admitted_action_failure_or_uncertainty")
        agent.poll_file_read_once.assert_called_once_with(args)

    def test_action_budget_is_bounded_and_other_admitted_action_is_reported(self):
        agent, args, pins = self.fixture()
        original = {"lane": "read", "canary_lane": "read_001", "action_id": "act_" + "c" * 32}
        emit = Mock()
        with patch.object(helper, "active_original", return_value=(original, None)):
            result = helper.assist(agent, args, pins, Path("unused"), 1, 900, emit, sleep=lambda _: None)
        self.assertEqual(result["stop_reason"], "action_budget_reached")
        self.assertTrue(emit.call_args.kwargs["other_admitted_action_received"])
        self.assertFalse(emit.call_args.kwargs["original_action_received"])
        with self.assertRaisesRegex(RuntimeError, "BOUNDED_OPERATOR_ASSISTANCE"):
            helper.assist(agent, args, pins, Path("unused"), 161, 900, Mock())


if __name__ == "__main__":
    unittest.main()
