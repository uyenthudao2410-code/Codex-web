"""Bounded CP projections for a completed patch with its initial proof."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from control_plane.mcp_facade import ControlPlaneMcpFacade, _completed_approved_patch_relay
from control_plane.store import ControlPlaneStore


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


class InitialVerificationFacadeTests(unittest.TestCase):
    def test_status_keeps_completed_effect_separate_from_failed_or_timed_out_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ControlPlaneStore(Path(directory) / "test.sqlite3")
            facade = ControlPlaneMcpFacade(store)
            contract = {key: facade.contract[key] for key in ("schema_version", "profile", "sha256")}
            plan = {"argv": ["node", "--test", "tests/fixture.test.js"], "cwd": "", "timeout_ms": 60000, "max_output_bytes": 32768}
            file = {"path": "src/fixture.txt", "preimage_sha256": "a" * 64, "postimage_sha256": "b" * 64, "bytes_written": 10}
            expected = {**file, "patch_sha256": "c" * 64, "facade_contract": contract, "authority_mode": "owner_review", "verification_sha256": digest(plan)}
            for status in ("passed", "failed", "timed_out"):
                with self.subTest(status=status):
                    proof = {"plan_sha256": digest(plan), "proof_status": status, "proof_ids": ["1" * 32] if status == "passed" else [],
                             "proof_fingerprint": "d" * 64 if status == "passed" else None}
                    payload = {
                        "schema_version": 1, "operation_kind": "control_plane_approved_patch", "patch_applied": True,
                        "local_handle": "cp_ap_" + "1" * 48, "policy_sha256": "2" * 64,
                        "local_semantic_acceptance": "pending", "task_id": "task_" + "3" * 32, "writer_lease_generation": 1,
                        "run_id": "4" * 32, "wave_id": "5" * 32,
                        "actor": {"client_id": "electron-control-plane-approved-patch-bridge", "client_type": "electron"},
                        "runtime_identity": {"activation_epoch_id": "epoch-proof-0001", "process_instance_id": "process-proof-0001",
                                             "server_instance_id": "server-proof-0001", "tool_contract_sha256": "6" * 64},
                        "facade_contract": contract, "file": file, "initial_verification": proof,
                        "response_sha256": digest({"file": file, "initial_verification": proof}),
                    }
                    action = {
                        "action_id": "act_" + "7" * 32, "tool_name": "agent_workflow", "delivery_state": "settled",
                        "action_digest": "8" * 64, "created_at_ms": 1, "expires_at_ms": 1000, "settled_at_ms": 2, "attempts": [],
                        "task_id": payload["task_id"], "writer_lease_generation": 1,
                        "arguments_json": json.dumps({"operation": "apply_patch", "permission_request_id": "permreq-proof-0001",
                                                      "path": file["path"], "preimage_sha256": file["preimage_sha256"],
                                                      "patch_sha256": expected["patch_sha256"], "validation_profile": "targeted", "verification_sha256": digest(plan)}),
                        "receipts": [{"receipt_id": "receipt-proof-0001", "receipt_state": "completed", "received_at_ms": 1, "receipt_digest": "9" * 64, "payload_json": json.dumps(payload)}],
                    }
                    relay = _completed_approved_patch_relay(action, contract, expected)
                    self.assertEqual(relay["initial_verification"], proof)
                    with mock.patch.object(store, "mcp_approved_patch_action_observation", return_value=action), \
                         mock.patch.object(store, "mcp_approved_patch_expected_file", return_value=expected), \
                         mock.patch.object(store, "get_mcp_patch_acceptance", return_value=None):
                        observation = facade._approved_patch_status(owner_id="owner-test-0001", principal_id="principal-test-0001", action_id=action["action_id"])["structuredContent"]
                    self.assertTrue(observation["patch_applied"])
                    self.assertEqual(observation["proof_status"], status)
                    self.assertEqual(observation["local_semantic_acceptance"], "pending")
                    self.assertEqual(observation["patch"]["run_id"], payload["run_id"])
                    self.assertIn(status, observation["execution"])
                    payload["response_sha256"] = digest(file)
                    action["receipts"][0]["payload_json"] = json.dumps(payload)
                    self.assertIsNone(_completed_approved_patch_relay(action, contract, expected))


if __name__ == "__main__":
    unittest.main()
