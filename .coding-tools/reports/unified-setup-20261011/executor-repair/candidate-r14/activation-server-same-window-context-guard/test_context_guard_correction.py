"""One focused check: expired history is preserved; exact sole live context remains mandatory."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r14_corrected_context_guard',HERE/'server-transition-r14.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
spec=importlib.util.spec_from_file_location('r14_corrected_context_driver',HERE/'root-server-transition-r14-ssh.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)

class ExactLiveContext(unittest.TestCase):
    def test_expired_history_and_exact_scope_preservation(self):
        raw=d.INSPECTION.read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),d.INSPECTION_SHA)
        actual=json.loads(raw)['public_receipts'][0]
        c=SimpleNamespace(BINDING=s.TARGET['binding_id'],PRINCIPAL=actual['prior_pilot_rows'][0]['principal_id'])
        rows={'contexts':actual['unclosed_target_contexts'],'scoped_pilot_decisions':actual['prior_pilot_rows']}
        before=copy.deepcopy(rows);previous=s.now;s.now=lambda:actual['observed_at_ms']
        try:
            self.assertEqual(s.window(rows,c),actual['prior_pilot_rows'][0]);self.assertEqual(rows,before)
            live=next(r for r in rows['contexts'] if r['context_id']==s.CONTEXT)
            wrong=copy.deepcopy(rows);wrong['contexts'][0]['device_id']='wrong'
            with self.assertRaises(s.Failure):s.window(wrong,c)
            extra=copy.deepcopy(rows);extra['contexts'].append({**live,'context_id':'ctx_synthetic_second_live'})
            with self.assertRaises(s.Failure):s.window(extra,c)
            closed=copy.deepcopy(rows);closed['contexts'][0]['closed_at_ms']=actual['observed_at_ms']
            with self.assertRaises(s.Failure):s.window(closed,c)
            expired=copy.deepcopy(rows);expired['contexts'][0]['expires_at_ms']=actual['observed_at_ms']
            with self.assertRaises(s.Failure):s.window(expired,c)
            d.prior_failure_reconciled('call_VVCZ5vN5tTi8XytTvFyQyHY0')
            with self.assertRaises(ValueError):d.prior_failure_reconciled('call_wrong_approval')
        finally:s.now=previous

if __name__=='__main__':unittest.main()
