import importlib.util, json, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("observer", HERE / "run-native-exec-readback-observer.py"); MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

def value():
    return {"operation":"native_exec_readback_finalizer","phase":"final","ok":False,"error_code":"KeyError","task_id":"task_"+"b"*32,"action_ids":{"build_readback":"act_"+"a"*32},"proofs":{},"task_closed_verified":True,"writer_released_verified":True}
class ObserverTests(unittest.TestCase):
    def test_prior_requires_existing_action_and_hash(self):
        raw=(json.dumps(value())+"\n").encode()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"prior.ndjson"; p.write_bytes(raw); got=MOD.prior(p,MOD.sha(raw)); self.assertTrue(got["final"]["action_ids"]["build_readback"].startswith("act_"))
    def test_prior_rejects_missing_action(self):
        v=value(); del v["action_ids"]; raw=(json.dumps(v)+"\n").encode()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"prior.ndjson"; p.write_bytes(raw)
            with self.assertRaises(RuntimeError): MOD.prior(p,MOD.sha(raw))
if __name__=="__main__": unittest.main()
