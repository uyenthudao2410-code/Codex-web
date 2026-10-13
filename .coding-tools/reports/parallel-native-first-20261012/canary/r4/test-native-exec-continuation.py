import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("continuation", HERE / "run-native-exec-continuation.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def final(error="ORIGINAL_JOB_IDENTITY_NOT_VERIFIED"):
    return {
        "phase": "final", "ok": False, "error_code": error, "attempt_id": "a" * 32,
        "task_id": "task_" + "b" * 32, "unresolved_original_actions": [],
        "binding_id": "bind_" + "c" * 32, "workspace_id": "workspace_" + "d" * 32,
        "workspace_generation": "generation_" + "e" * 32,
        "requires_reconciliation": False, "task_closed_verified": True,
        "writer_released_verified": True,
        "proof_counts": {"reads": 100, "patches": 20, "readbacks": 20, "node_jobs": 0, "git_jobs": 0},
        "final_action_status": {"node_01": {"state": "completed", "process_state": "completed",
                                               "reconciliation_required": False}},
    }


class ContinuationTests(unittest.TestCase):
    def test_partial_receipt_requires_exact_failure_and_closure(self):
        rows = [final()]
        raw = (json.dumps(rows[0]) + "\n").encode()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "failed.ndjson"
            path.write_bytes(raw)
            observed = MOD.validate_failed_receipt(path, MOD.sha(raw))
        self.assertEqual(observed["final"]["proof_counts"]["reads"], 100)

    def test_partial_receipt_rejects_different_error(self):
        raw = (json.dumps(final("OTHER_FAILURE")) + "\n").encode()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "failed.ndjson"
            path.write_bytes(raw)
            with self.assertRaisesRegex(RuntimeError, "FAILED_RECEIPT_WRONG_TERMINAL_FAILURE"):
                MOD.validate_failed_receipt(path, MOD.sha(raw))

    def test_exec_identity_allows_empty_run_and_wave(self):
        metadata = {"execution_backend": "native", "isolation_level": "process_container",
                    "policy_decision": "native_safe_command"}
        payload = {**metadata, "job_id": "job_1", "command_id": "command_1", "local_handle": "cp_exec_1",
                   "run_id": "", "wave_id": "", "status": "exited", "timed_out": False,
                   "truncated": False, "stderr": ""}
        result = {"exec": payload}
        MOD.validate_exec_result(result, payload, metadata)

    def test_exec_identity_requires_local_handle(self):
        metadata = {"execution_backend": "native", "isolation_level": "process_container",
                    "policy_decision": "native_safe_command"}
        payload = {**metadata, "job_id": "job_1", "command_id": "command_1", "local_handle": "",
                   "status": "exited", "timed_out": False, "truncated": False, "stderr": ""}
        with self.assertRaisesRegex(RuntimeError, "ORIGINAL_JOB_IDENTITY_NOT_VERIFIED"):
            MOD.validate_exec_result({"exec": payload}, payload, metadata)


if __name__ == "__main__":
    unittest.main()
