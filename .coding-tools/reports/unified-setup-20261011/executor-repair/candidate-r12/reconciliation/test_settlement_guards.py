"""Offline regressions for exact node receipt reconciliation; no SSH or live API."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('settlement',HERE/'settle-exact-pre-effect.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
DEVICE='72ceec2d-e3f2-472f-8e3c-99fffe053035'
NEW='rcpt_test_exact_rejection'

def fixture():
    payload={'code':'WORKTREE_STATUS_TOO_LARGE','patch_applied':False,'pre_effect_validation_rejection':True}
    initial={'actions':[{'action_id':s.ACTION,'delivery_state':'reconcile_required','settled_at_ms':None,'args_json':'original'}],
     'receipts':[{'receipt_id':s.UNKNOWN,'receipt_state':'unknown','payload_json':'preserved'}],
     'mcp_task_sessions':[{'task_id':s.TASK,'closed_at_ms':None,'close_reason':'','principal_id':'preserved'}],
     'mcp_task_writer_leases':[{'lease_id':'exact','released_at_ms':None,'release_reason':'','lease_generation':1}]}
    terminal=copy.deepcopy(initial);terminal['actions'][0].update(delivery_state='settled',settled_at_ms=123)
    terminal['receipts'].append({'receipt_id':NEW,'action_id':s.ACTION,'device_id':DEVICE,'receipt_state':'rejected',
     'local_handle':'','payload_json':json.dumps(payload),'receipt_digest':s.rejection_digest(payload),'received_at_ms':123})
    result={'receipt_id':NEW,'action_id':s.ACTION,'receipt_state':'rejected','delivery_state':'settled','replayed':False}
    return initial,terminal,payload,result

class SettlementGuards(unittest.TestCase):
    def test_response_without_echoed_attempt_still_verifies_real_digest(self):
        initial,terminal,payload,result=fixture()
        self.assertNotIn('attempt_id',result)
        s.verify_terminal_response(result)
        self.assertEqual(s.verify_rejection(initial,terminal,NEW,payload,DEVICE)['receipt_id'],NEW)

    def test_deployed_response_echo_is_optional(self):
        _,_,_,result=fixture();result['attempt_id']=s.ATTEMPT
        s.verify_terminal_response(result)

    def test_replayed_response_is_denied(self):
        _,_,_,result=fixture();result['replayed']=True
        with self.assertRaises(s.Failure):s.verify_terminal_response(result)

    def test_wrong_attempt_digest_is_denied(self):
        initial,terminal,payload,_=fixture()
        wrong={'attempt_id':'other-attempt','receipt_state':'rejected','local_handle':'','payload':payload}
        terminal['receipts'][1]['receipt_digest']=s.digest(s.canonical(wrong))
        with self.assertRaises(s.Failure):s.verify_rejection(initial,terminal,NEW,payload,DEVICE)

    def test_wrong_receipt_fields_are_denied(self):
        for key,value in [('device_id','other'),('action_id','other'),('local_handle','invented'),('received_at_ms',124)]:
            with self.subTest(key=key):
                initial,terminal,payload,_=fixture();terminal['receipts'][1][key]=value
                with self.assertRaises(s.Failure):s.verify_rejection(initial,terminal,NEW,payload,DEVICE)

    def test_wrong_payload_is_denied(self):
        initial,terminal,payload,_=fixture();terminal['receipts'][1]['payload_json']='{"patch_applied":true}'
        with self.assertRaises(s.Failure):s.verify_rejection(initial,terminal,NEW,payload,DEVICE)

    def test_old_receipt_and_action_args_remain_protected(self):
        for table,key in [('receipts','payload_json'),('actions','args_json')]:
            with self.subTest(table=table):
                initial,terminal,payload,_=fixture();terminal[table][0][key]='changed'
                with self.assertRaises(s.Failure):s.verify_rejection(initial,terminal,NEW,payload,DEVICE)

    def test_truthful_task_close_preserves_other_task_and_lease_fields(self):
        initial,final,payload,_=fixture()
        final['mcp_task_sessions'][0].update(closed_at_ms=124,close_reason='closed')
        final['mcp_task_writer_leases'][0].update(released_at_ms=124,release_reason='closed')
        s.verify_final(initial,final,NEW,payload,DEVICE)
        final['mcp_task_writer_leases'][0]['lease_generation']=2
        with self.assertRaises(s.Failure):s.verify_final(initial,final,NEW,payload,DEVICE)

if __name__=='__main__':unittest.main()
