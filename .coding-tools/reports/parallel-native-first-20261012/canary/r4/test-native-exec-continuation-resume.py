import importlib.util, json, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("resume", HERE / "run-native-exec-continuation-resume.py")
MOD = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

def prior():
    proofs = {f"node_{i:02}": {"job_id": f"job{i}", "command_id": f"cmd{i}", "local_handle": f"handle{i}", "execution_backend": "native", "isolation_level": "process_container"} for i in range(1, 11)}
    proofs["git_status"] = {"job_id": "gitjob", "command_id": "gitcmd", "local_handle": "githandle", "execution_backend": "native", "isolation_level": "process_container"}
    return {"operation": "native_exec_continuation", "phase": "final", "ok": False,
            "error_code": "EXEC_TERMINAL_PAYLOAD_INVALID", "proof_counts": {"node_jobs": 10, "git_jobs": 1, "approved_build": 0, "build_readback": 0},
            "proofs": proofs, "action_ids": {"git_diff": "act_" + "a" * 32},
            "task_closed_verified": True, "writer_released_verified": True}

class ResumeTests(unittest.TestCase):
    def test_prior_requires_exact_partial_and_hash(self):
        raw = (json.dumps(prior()) + "\n").encode()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "prior.ndjson"; p.write_bytes(raw)
            got = MOD.load_prior(p, MOD.sha(raw)); self.assertEqual(got["final"]["proof_counts"]["node_jobs"], 10)
    def test_prior_rejects_any_existing_unproved_lane(self):
        value = prior(); value["proofs"]["git_diff"] = value["proofs"]["git_status"]
        raw = (json.dumps(value) + "\n").encode()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "prior.ndjson"; p.write_bytes(raw)
            with self.assertRaises(RuntimeError) as caught:
                MOD.load_prior(p, MOD.sha(raw))
            self.assertEqual(caught.exception.args, ("PRIOR_UNPROVED_LANE_ALREADY_PROVED",))

if __name__ == "__main__": unittest.main()
