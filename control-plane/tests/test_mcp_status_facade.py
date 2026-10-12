"""Public action status distinguishes terminal failures and central verdicts."""
from __future__ import annotations

import json
import unittest
from unittest import mock

from control_plane.mcp_facade import ControlPlaneMcpFacade


class McpStatusFacadeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = mock.Mock()
        self.facade = ControlPlaneMcpFacade(
            self.store, auth_kind="private_tunnel_service",
            oauth_scopes=("control-plane.inventory",), oauth_file_read_enabled=True,
            oauth_patch_write_scope="control-plane.patch", oauth_approved_patch_enabled=True,
            oauth_standing_write_enabled=True, oauth_exec_enabled=True,
        )

    def action(self, tool: str, state: str) -> dict:
        return {
            "action_id": "act_" + "a" * 32, "action_digest": "a" * 64,
            "tool_name": tool, "created_at_ms": 1, "expires_at_ms": 100,
            "delivery_state": "reconcile_required" if state == "unknown" else "settled",
            "settled_at_ms": None if state == "unknown" else 50,
            "attempts": [{"attempt_id": "try_001", "attempt_number": 1, "dispatched_at_ms": 2}],
            "receipts": [{"receipt_id": "rcpt_001", "receipt_state": state,
                          "received_at_ms": 50, "receipt_digest": "b" * 64,
                          "payload_json": json.dumps({"code": "CONTROL_PLANE_POLICY_DENIED", "message": "private-value"})}],
        }

    def call_status(self, method: str, observer: str, tool: str, state: str, **extra: str) -> dict:
        action = self.action(tool, state)
        getattr(self.store, observer).return_value = action
        return getattr(self.facade, method)(owner_id="owner", principal_id="principal",
                                            action_id=action["action_id"], **extra)

    def test_terminal_rejection_has_a_reason_in_each_public_status(self) -> None:
        cases = (
            ("_bounded_file_read_status", "mcp_file_read_action_observation", "workspace_context", {}),
            ("_approved_patch_status", "mcp_approved_patch_action_observation", "agent_workflow", {}),
            ("_exec_status", "mcp_exec_action_observation", "exec_command", {}),
            ("_document_write_status", "mcp_document_write_action_observation", "document_workflow", {}),
            ("_artifact_status", "mcp_artifact_action_observation", "view_image", {"kind": "image"}),
        )
        for method, observer, tool, extra in cases:
            with self.subTest(tool=tool):
                result = self.call_status(method, observer, tool, "rejected", **extra)
                self.assertFalse(result["isError"])
                status = result["structuredContent"]
                self.assertTrue(status["execution"].endswith("_rejected"))
                self.assertNotIn("pending", status["execution"])
                self.assertEqual(status["local_admission"], "rejected")
                self.assertEqual(status["action"]["central_lifecycle_state"], "rejected")
                self.assertEqual(status["local_failure"]["code"], "CONTROL_PLANE_POLICY_DENIED")
                self.assertFalse(status["local_failure"]["retryable"])
                self.assertNotIn("private-value", json.dumps(result))

    def test_failed_or_stopped_patch_does_not_claim_that_no_write_occurred(self) -> None:
        for state in ("failed", "stopped"):
            with self.subTest(state=state):
                result = self.call_status("_approved_patch_status", "mcp_approved_patch_action_observation",
                                          "agent_workflow", state)
                status = result["structuredContent"]
                self.assertEqual(status["execution"], "local_patch_" + state)
                self.assertIsNone(status["patch_applied"])
                self.assertEqual(status["patch_effect_state"], "not_verified")
                self.assertEqual(status["action"]["central_lifecycle_state"], state)
                self.assertEqual(status["local_failure"]["next_action"], "do_not_replay_automatically")

    def test_unknown_patch_stays_unknown_and_requires_reconciliation(self) -> None:
        result = self.call_status("_approved_patch_status", "mcp_approved_patch_action_observation", "agent_workflow", "unknown")
        status = result["structuredContent"]
        self.assertIsNone(status["patch_applied"])
        self.assertEqual(status["patch_effect_state"], "unknown")
        self.assertTrue(status["reconciliation_required"])
        self.assertNotIn("local_failure", status["action"])

    def test_central_owner_verdict_does_not_complete_local_run_acceptance(self) -> None:
        action = self.action("agent_workflow", "completed")
        self.store.mcp_approved_patch_action_observation.return_value = action
        relay = {"local_semantic_acceptance": "pending", "postimage_sha256": "c" * 64}
        for decision in ("accepted", "rejected"):
            with self.subTest(decision=decision):
                self.store.get_mcp_patch_acceptance.return_value = {"decision": decision}
                with mock.patch("control_plane.mcp_facade._completed_approved_patch_relay", return_value=relay):
                    result = self.facade._approved_patch_status(owner_id="owner", principal_id="principal", action_id=action["action_id"])
                status = result["structuredContent"]
                self.assertTrue(status["patch_applied"])
                self.assertEqual(status["patch_effect_state"], "verified_applied")
                self.assertEqual(status["central_owner_acceptance"], decision)
                self.assertEqual(status["local_semantic_acceptance"], "pending")
                self.assertEqual(status["execution"], "effect_applied_owner_" + decision + "_local_pending")


if __name__ == "__main__":
    unittest.main()
