"""Offline tests for the r5 evidence joiner."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("joiner", HERE / "aggregate-native-first-continuation.py")
JOINER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(JOINER)


class JoinerTests(unittest.TestCase):
    def test_production_receipts_join_to_complete_native_lanes(self):
        root = HERE.parent
        r4 = root / "r4"
        args = type("Args", (), {
            "original": str(r4 / "shared-mcp-receipt-e343984bfcee4e8fb5f9de04038596a7.ndjson"),
            "continuation": str(r4 / "continuation-receipt-0fe3b0d6d1e44d8284760356bea309fc.ndjson"),
            "resume": str(r4 / "continuation-resume-receipt-9509199d0c7b49bba496c971676a4882.ndjson"),
            "readback": str(r4 / "readback-finalizer-receipt-698fcc64e0b5431081e8a4e90fb7569f.ndjson"),
        })()
        report = JOINER.validate(args)
        self.assertEqual(report["status"], "lanes_complete_semantic_gate_separate")
        self.assertEqual(report["combined_proof_counts"], {
            "reads": 100, "patches": 20, "readbacks": 20, "node_jobs": 10,
            "git_jobs": 3, "approved_build": 1, "build_readback": 1,
        })
        self.assertFalse(report["replayed_original_actions"])
        self.assertEqual(len(report["native_jobs"]), 14)

    def test_changed_chain_hash_is_rejected(self):
        r4 = HERE.parent / "r4"
        args = type("Args", (), {
            "original": str(r4 / "shared-mcp-receipt-e343984bfcee4e8fb5f9de04038596a7.ndjson"),
            "continuation": str(r4 / "continuation-receipt-0fe3b0d6d1e44d8284760356bea309fc.ndjson"),
            "resume": str(r4 / "continuation-resume-receipt-9509199d0c7b49bba496c971676a4882.ndjson"),
            "readback": str(r4 / "readback-finalizer-receipt-698fcc64e0b5431081e8a4e90fb7569f.ndjson"),
        })()
        with tempfile.TemporaryDirectory() as temporary:
            changed = Path(temporary) / "changed.ndjson"
            changed.write_bytes((r4 / "shared-mcp-receipt-e343984bfcee4e8fb5f9de04038596a7.ndjson").read_bytes() + b"\n")
            args.original = str(changed)
            with self.assertRaises(RuntimeError):
                JOINER.validate(args)

    def test_action_handle_cannot_be_substituted(self):
        proof = {"receipt_id": "rcpt_original", "action_id": "act_original", "attempt_id": "try_original",
                 "attempt_number": 1, "response_sha256": "a" * 64}
        final = {"proofs": {"node_01": proof}, "action_ids": {"node_01": "act_substitute"}}
        with self.assertRaisesRegex(RuntimeError, "ORIGINAL_ACTION_HANDLE_MISMATCH"):
            JOINER.count_required_proofs(final, ["node_01"], "TEST")

    def test_isolated_job_cannot_count_as_native(self):
        proof = {"job_id": "original_job", "command_id": "original_command", "local_handle": "original_handle",
                 "execution_backend": "isolated", "isolation_level": "hypervisor"}
        with self.assertRaisesRegex(RuntimeError, "NOT_NATIVE"):
            JOINER.check_native_jobs({"node_01": proof}, ["node_01"], "TEST")

    def test_same_scope_with_another_runtime_is_rejected(self):
        expected = {"activation_epoch_id": "expected", "process_instance_id": "process", "server_instance_id": "server",
                    "tool_contract_sha256": "a" * 64}
        changed = {**expected, "activation_epoch_id": "different"}
        final = {"workspace_id": "same", "workspace_generation": "same", "binding_id": "same",
                 "proofs": {"node_01": {"runtime_identity": changed}}}
        with self.assertRaisesRegex(RuntimeError, "RUNTIME_IDENTITY_CHANGED"):
            JOINER.check_scope_and_identity(final, JOINER.scope(final), expected)


if __name__ == "__main__":
    unittest.main()
