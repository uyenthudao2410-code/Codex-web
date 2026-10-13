import importlib.util, json, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("finalizer", HERE / "run-native-exec-readback-finalizer.py"); MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)
def value():
    proofs={k:{"job_id":k,"command_id":k,"local_handle":k} for k in ("git_diff","git_log","build")}
    return {"operation":"native_exec_continuation_resume","phase":"final","ok":False,"error_code":"KeyError","proof_counts":{"git_jobs":2,"approved_build":1,"build_readback":0},"proofs":proofs,"action_ids":{"build_readback":"act_"+"a"*32},"task_closed_verified":True,"writer_released_verified":True}
class FinalizerTests(unittest.TestCase):
    def test_prior_is_bound_and_readback_missing(self):
        raw=(json.dumps(value())+"\n").encode()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"resume.ndjson"; p.write_bytes(raw); got=MOD.prior_value(p,MOD.sha(raw)); self.assertEqual(got["final"]["proof_counts"]["build_readback"],0)
    def test_prior_cannot_repeat_existing_readback_proof(self):
        v=value(); v["proofs"]["build_readback"]={"job_id":"x"}; raw=(json.dumps(v)+"\n").encode()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"resume.ndjson"; p.write_bytes(raw)
            with self.assertRaises(RuntimeError) as caught: MOD.prior_value(p,MOD.sha(raw))
            self.assertEqual(caught.exception.args,("PRIOR_READBACK_PROOF_ALREADY_PRESENT",))
if __name__=="__main__": unittest.main()
