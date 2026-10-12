"""Offline fail-closed checks; no SSH, secrets, live ledger or native effects."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('after_effect_settlement',HERE/'settle-exact-after-effect.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
NATIVE=HERE/'native-correlation-1791759968554973600.json'
QUERY=HERE/'query-receipt-20261011T225840992295Z.json'

class SettlementGuardTests(unittest.TestCase):
    def setUp(self):
        raw=NATIVE.read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),s.NATIVE_OBSERVATION_SHA256)
        self.native=json.loads(raw);self.query=json.loads(QUERY.read_bytes())['public_receipts'][0]
    def rejected(self,call):
        with self.assertRaises(s.Failure):call()
    def census(self):
        return {'kind':'r13_5h_exact_after_effect_root_census','action_id':s.ACTION,'task_id':s.TASK,
          'observed_at_ms':100000,'active_job_count':0,'target_postimage_sha256':s.POST,'checker_sha256':s.CHECK,
          'old_pending_record_sha256':s.OLD_HASHES,'job_row_sha256':self.native['correlation']['job_row_sha256'],
          'proof_input_fingerprint':self.native['correlation']['proof_input_fingerprint'],'proof_status':'passed','proof_exit_code':0,
          'proof_source_binding':self.native['correlation']['proof_source_binding'],'proof_cache_hit':False,
          'idempotency_summary_sha256':self.native['idempotency']['summary_sha256'],'idempotency_status':'completed',
          'idempotency_key':self.native['idempotency']['key'],'idempotency_request_hash':self.native['idempotency']['request_hash'],
          'idempotency_process_instance_id':self.native['native_identity']['process_instance_id'],
          'current_native_identity_observation':{'ok':True,'kind':'r13_5h_root_current_native_identity_read_only',
            'observed_at_ms':100000,'native_identity':self.native['native_identity'],'current_identity':True,
            'mcp_ready':True,'host_owner_pid':11476,'host_process_verified':True,'authenticated_read_only':True,
            'activation_performed':False,'acceptance_performed':False,'mutated_canonical_ledger':False,'secret_values_emitted':False}}
    def test_actual_historical_capsule_and_query_validate(self):
        s.validate_native(self.native);s.validate_query(self.query)
        historical=copy.deepcopy(self.native);historical['observed_at_ms']=0
        s.validate_native(historical) # Immutable capsule is historical; fresh census is independent.
    def test_failure_payload_is_truthful_and_owner_assisted(self):
        p=s.build_payload(self.native,{'native':s.NATIVE_OBSERVATION_SHA256})
        self.assertTrue(p['patch_applied']);self.assertTrue(p['owner_assisted_node_reconciliation'])
        self.assertTrue(p['result_delivery_failed_after_effect']);self.assertEqual(p['local_semantic_acceptance'],'pending')
        self.assertEqual(p['checker_4_of_4'],'not_observed');self.assertEqual(p['initial_verification'],self.native['initial_verification'])
        self.assertNotIn('response_sha256',p);self.assertNotIn('local_handle',p);self.assertNotIn('pre_effect_validation_rejection',p)
    def test_wrong_native_target_effect_and_unknown_fail_closed(self):
        for key,value in [('action_id','wrong'),('task_id','wrong'),('attempt_id','wrong'),('unknown_receipt_id','wrong'),
          ('unknown_payload_sha256','0'*64),('patch_applied',False),('target_postimage_sha256','0'*64),('checker_sha256','0'*64),
          ('central_action_settled',True),('checker_4_of_4','4_of_4'),('native_semantic_acceptance','accepted')]:
            with self.subTest(key=key):
                changed=copy.deepcopy(self.native);changed[key]=value;self.rejected(lambda:s.validate_native(changed))
    def test_wrong_proof_job_old_records_and_idempotency_fail_closed(self):
        for key,value in [('command_id','wrong'),('job_id','wrong'),('proof_ids',[]),('proof_fingerprint','wrong'),('proof_status','failed')]:
            changed=copy.deepcopy(self.native);changed['initial_verification'][key]=value
            self.rejected(lambda:s.validate_native(changed))
        for key,value in [('old_pending_records_unchanged',False),('canary_jobs_quiescent',False),('job_lifecycle','active'),('exit_code',1)]:
            changed=copy.deepcopy(self.native);changed['correlation'][key]=value
            self.rejected(lambda:s.validate_native(changed))
        changed=copy.deepcopy(self.native);changed['idempotency']['status']='prepared'
        self.rejected(lambda:s.validate_native(changed))
    def test_fresh_census_checks_current_effect_without_source_fingerprint(self):
        c=self.census();s.validate_census(c,self.native,100001)
        for key,value in [('active_job_count',1),('active_job_count',False),('target_postimage_sha256','0'*64),
          ('checker_sha256','0'*64),('job_row_sha256','0'*64),('proof_input_fingerprint','0'*64),('observed_at_ms',0),('idempotency_status','prepared'),('idempotency_summary_sha256','0'*64),('proof_cache_hit',True)]:
            changed=copy.deepcopy(c);changed[key]=value
            self.rejected(lambda:s.validate_census(changed,self.native,100001))
        self.assertNotIn('source_worktree_fp',c);self.assertNotIn('zero_vm',c)
    def test_identity_requires_fresh_exact_authenticated_readonly_observation(self):
        c=self.census();good=c['current_native_identity_observation'];s.validate_identity(good,self.native,100001)
        for key,value in [('native_identity',{}),('observed_at_ms',0),('current_identity',False),('mcp_ready',False),
          ('authenticated_read_only',False),('activation_performed',True),('acceptance_performed',True),('secret_values_emitted',True)]:
            changed=copy.deepcopy(good);changed[key]=value;self.rejected(lambda:s.validate_identity(changed,self.native,100001))
    def test_query_binds_exact_unknown_and_one_attempt(self):
        for key,value in [('action_id','wrong'),('task_id','wrong'),('attempts',[]),('reconciliations',[{}]),('dispatch_dispositions',[{}])]:
            changed=copy.deepcopy(self.query);changed[key]=value;self.rejected(lambda:s.validate_query(changed))
        changed=copy.deepcopy(self.query);changed['receipts'][0]['receipt_state']='completed';self.rejected(lambda:s.validate_query(changed))
    def test_terminal_response_requires_one_new_failed_receipt(self):
        good={'receipt_id':'rcpt_new','action_id':s.ACTION,'receipt_state':'failed','delivery_state':'settled','replayed':False}
        s.verify_terminal_response(good)
        for key,value in [('receipt_state','completed'),('receipt_state','rejected'),('replayed',True),('receipt_id',s.UNKNOWN),('delivery_state','reconcile_required')]:
            changed={**good,key:value};self.rejected(lambda:s.verify_terminal_response(changed))
    def family(self):
        p=s.build_payload(self.native,{'native':s.NATIVE_OBSERVATION_SHA256})
        old={'actions':[{'action_id':s.ACTION,'delivery_state':'reconcile_required','settled_at_ms':None,'preserved':'same'}],
         'receipts':[{'receipt_id':s.UNKNOWN,'receipt_state':'unknown','preserved':'same'}],
         'mcp_task_sessions':[{'task_id':s.TASK,'closed_at_ms':None,'close_reason':'','preserved':'same'}],
         'mcp_task_writer_leases':[{'lease_id':'lease_exact','released_at_ms':None,'release_reason':'','preserved':'same'}]}
        final=copy.deepcopy(old);final['actions'][0].update(delivery_state='settled',settled_at_ms=100)
        final['receipts'].append({'receipt_id':'rcpt_new','receipt_state':'failed','action_id':s.ACTION,'device_id':'device_exact','local_handle':'',
         'payload_json':json.dumps(p),'receipt_digest':s.failure_digest(p),'received_at_ms':100})
        final['mcp_task_sessions'][0].update(closed_at_ms=110,close_reason='mcp_task_close')
        final['mcp_task_writer_leases'][0].update(released_at_ms=105,release_reason='owner-assisted')
        return old,final,p
    def test_terminal_and_cleanup_preserve_unknown_and_history(self):
        old,final,p=self.family();s.verify_final(old,final,'rcpt_new',p,'device_exact')
        changed=copy.deepcopy(final);changed['receipts'][0]['preserved']='overwritten'
        self.rejected(lambda:s.verify_final(old,changed,'rcpt_new',p,'device_exact'))
        changed=copy.deepcopy(final);changed['actions'][0]['preserved']='overwritten'
        self.rejected(lambda:s.verify_final(old,changed,'rcpt_new',p,'device_exact'))
        changed=copy.deepcopy(final);changed['receipts'][-1]['receipt_digest']='0'*64
        self.rejected(lambda:s.verify_final(old,changed,'rcpt_new',p,'device_exact'))
        changed=copy.deepcopy(final);changed['mcp_task_writer_leases'][0]['preserved']='overwritten'
        self.rejected(lambda:s.verify_final(old,changed,'rcpt_new',p,'device_exact'))
    def test_already_released_lease_history_is_unchanged(self):
        old,final,p=self.family()
        historical={'lease_id':'lease_old','released_at_ms':1,'release_reason':'historical','preserved':'same'}
        old['mcp_task_writer_leases'].append(historical);final['mcp_task_writer_leases'].append(copy.deepcopy(historical))
        s.verify_final(old,final,'rcpt_new',p,'device_exact')
        final['mcp_task_writer_leases'][1]['released_at_ms']=2
        self.rejected(lambda:s.verify_final(old,final,'rcpt_new',p,'device_exact'))
    def test_initial_family_requires_exact_one_active_owned_lease(self):
        c=SimpleNamespace(BINDING='binding',DEVICE='device',WORKSPACE='workspace',GENERATION='generation',PRINCIPAL='principal')
        payload={'schema_version':1,'operation_kind':'control_plane_approved_patch','code':'CONTROL_PLANE_APPROVED_PATCH_EFFECT_UNKNOWN','diagnostic_code':'CONTROL_PLANE_APPROVED_PATCH_TIMEOUT'}
        target={'actions':[{'delivery_state':'reconcile_required','settled_at_ms':None,'binding_id':c.BINDING,'device_id':c.DEVICE,'workspace_id':c.WORKSPACE,'workspace_generation':c.GENERATION,'context_id':'ctx_b7d6fe51fc7c4aaaaba2947ad8c98e43','request_id':'req_3f80be12f4914928a73f41974980c339'}],
         'receipts':[{'receipt_id':s.UNKNOWN,'receipt_state':'unknown','payload_json':s.canonical(payload).decode()}],
         'mcp_task_sessions':[{'closed_at_ms':None,'binding_id':c.BINDING,'device_id':c.DEVICE,'workspace_id':c.WORKSPACE,'workspace_generation':c.GENERATION,'principal_id':c.PRINCIPAL,'owner_id':'owner'}],
         'mcp_task_writer_leases':[{'task_id':s.TASK,'released_at_ms':None,'binding_id':c.BINDING,'principal_id':c.PRINCIPAL,'owner_id':'owner','lease_generation':1}]}
        s.exact_initial(target,c)
        for key,value in [('binding_id','wrong'),('principal_id','wrong'),('owner_id','wrong'),('lease_generation',False)]:
            changed=copy.deepcopy(target);changed['mcp_task_writer_leases'][0][key]=value
            self.rejected(lambda:s.exact_initial(changed,c))
        changed=copy.deepcopy(target);changed['mcp_task_writer_leases'].append(copy.deepcopy(changed['mcp_task_writer_leases'][0]))
        self.rejected(lambda:s.exact_initial(changed,c))
    def test_snapshot_is_readonly_and_excludes_only_exact_rows(self):
        with tempfile.TemporaryDirectory(prefix='r13-settlement-offline-') as temp:
            dbpath=Path(temp)/'synthetic.sqlite3'
            db=sqlite3.connect(dbpath)
            try:
                for table in s.TABLES:
                    db.execute('CREATE TABLE '+table+' (action_id TEXT,task_id TEXT,preserved TEXT)')
                    db.execute('INSERT INTO '+table+' VALUES(?,?,?)',('action_other','task_other','historical'))
                for table in ('actions','receipts','mcp_task_sessions','mcp_task_writer_leases'):
                    db.execute('INSERT INTO '+table+' VALUES(?,?,?)',(s.ACTION,s.TASK,'exact'))
                db.commit()
            finally:db.close()
            before=hashlib.sha256(dbpath.read_bytes()).hexdigest();unchanged,target=s.snapshot(dbpath)
            self.assertEqual(set(target),{'actions','receipts','mcp_task_sessions','mcp_task_writer_leases'})
            self.assertTrue(all(len(rows)==1 for rows in target.values()))
            self.assertEqual(before,hashlib.sha256(dbpath.read_bytes()).hexdigest())
            self.assertEqual(len(unchanged),len(s.TABLES))
    def test_bad_approval_never_reaches_remote_load(self):
        previous=s.load_remote;s.load_remote=lambda *args:(_ for _ in ()).throw(AssertionError('remote load reached'))
        try:self.rejected(lambda:s.main({'execute':True,'approval_id':'wrong'}))
        finally:s.load_remote=previous

if __name__=='__main__':unittest.main()
