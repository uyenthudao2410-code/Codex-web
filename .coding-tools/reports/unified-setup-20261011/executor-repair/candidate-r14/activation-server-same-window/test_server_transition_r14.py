"""Offline checks for actual Windows projection and unchanged-authority admission phases."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r14_server_packet',HERE/'server-transition-r14.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
ROOT=HERE.parents[4]
WINDOWS=HERE.parent/'activation-windows-same-window'

class ProjectionAndPreservation(unittest.TestCase):
    def setUp(self):
        raw=(WINDOWS/'observation-20261011T233915767Z.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'6d7efda04bccc978a1940e310678d49b04b08ec0539a24a98c6b57a7e690be9f')
        self.pre=json.loads(raw);self.previous=s.now;s.now=lambda:self.pre['observed_at_ms']+1
    def tearDown(self):s.now=self.previous
    def test_actual_preclose_with_owned_idle_vm_is_allowed(self):
        s.windows(self.pre,'close')
        self.assertFalse(self.pre['activation_preflight_ready'])
        wrong=copy.deepcopy(self.pre);wrong['target']['binding_id']='wrong'
        with self.assertRaises(s.Failure):s.windows(wrong,'close')
    def test_actual_final_producer_projection_needs_no_invented_target(self):
        p=copy.deepcopy(self.pre)
        for key in ('target','repository_head','current_runtime_tag','authority_expires_at_ms'):p.pop(key,None)
        p.update(phase='r14_final_runtime_proof',ok=True,tag='r14',helper_sha256=s.WINDOWS_TRANSITION,
          live_sandbox_exec_proven=False,semantic_acceptance_performed=False,windows_rebooted=False,ubuntu_deployed_or_restarted=False,
          central_route={'connected':True,'authorityReady':True,'reason':'CENTRAL_ROUTE_READY',
            'evidence':{'serverOrigin':s.TARGET['server_origin'],'deviceId':s.TARGET['device_id'],'endpointId':s.TARGET['endpoint_id']}},
          vm_zero={'host_count':0,'backend_count':0})
        p['descriptor']['installation_id']=s.R14_INSTALLATION;p['ui']['ui_installation_id']=s.R14_INSTALLATION
        p['epoch']['activation_epoch_id']='synthetic_new_r14_epoch'
        p['native_identity'].update(activation_epoch_id='synthetic_new_r14_epoch',current_activation_epoch_id='synthetic_new_r14_epoch',
          recovery_host_instance_id=p['descriptor']['instance_id'],mcp_process_instance_id='synthetic_new_runtime',mcp_server_instance_id='synthetic_new_mcp')
        s.windows(p,'replace');s.windows(p,'reopen')
        changed=copy.deepcopy(p);changed['central_route']['evidence']['deviceId']='wrong'
        with self.assertRaises(s.Failure):s.windows(changed,'replace')
    def test_future_approval_refuses_old_ids_and_window_extension(self):
        a={'approved':True,'source':'human_user_response','approval_id':'call_synthetic_offline_r14',
          'operation':s.OPERATION,'candidate_tag':'workflow-timeout-1012-r14','context_id':s.CONTEXT,'expires_at_ms':s.EXPIRES,
          'target':s.TARGET,'approved_at_ms':s.now(),'pilot_replacement_same_principal_binding_expiry':True,
          'r13_owned_executor_cleanup_refresh':True,'new_approved_patch_verification_canary':True,
          'authority_extension':False,'ubuntu_deploy_or_restart':False,'windows_reboot':False,'semantic_acceptance':False}
        s.approval(a,a['approval_id'])
        for old in (s.WINDOW_APPROVAL,'call_1KzUkF0gMn6uVpHd3QisTzXF'):
            with self.assertRaises(s.Failure):s.approval({**a,'approval_id':old},old)
        with self.assertRaises(s.Failure):s.approval({**a,'expires_at_ms':s.EXPIRES+1},a['approval_id'])
    def test_authority_changes_only_exact_pilot_and_preserves_context_grant(self):
        c=SimpleNamespace(PRINCIPAL='principal_test',BINDING=s.TARGET['binding_id'])
        pilot={'decision_id':s.PRIOR,'principal_id':c.PRINCIPAL,'binding_id':c.BINDING,'expires_at_ms':s.EXPIRES,'revoked_at_ms':None}
        before={'contexts':[{'context_id':s.CONTEXT}],'mcp_service_grants':[{'grant_id':'unchanged'}],
          'scoped_pilot_decisions':[pilot,{'decision_id':'unrelated','revoked_at_ms':1}]}
        closed=copy.deepcopy(before);closed['scoped_pilot_decisions'][0]['revoked_at_ms']=s.now()
        s.preserve(before,closed,'close',c)
        wrong=copy.deepcopy(closed);wrong['scoped_pilot_decisions'][1]['revoked_at_ms']=2
        with self.assertRaises(s.Failure):s.preserve(before,wrong,'close',c)
        replaced=copy.deepcopy(closed);new={'decision_id':'pilot_'+'1'*32,'principal_id':c.PRINCIPAL,'binding_id':c.BINDING,
          'expires_at_ms':s.EXPIRES,'revoked_at_ms':None,**{k:s.TARGET[k] for k in ('device_id','endpoint_id','workspace_id','workspace_generation')}}
        replaced['scoped_pilot_decisions'].append(new);s.preserve(closed,replaced,'replace',c,new['decision_id'])
        changed=copy.deepcopy(replaced);changed['scoped_pilot_decisions'][-1]['expires_at_ms']+=1
        with self.assertRaises(s.Failure):s.preserve(closed,changed,'replace',c,new['decision_id'])
    def test_server_observation_matches_real_windows_consumer(self):
        c=SimpleNamespace(HOST='100.116.112.22',SERVICE='codex-control-plane.service',REVISION='9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c',
          BINDING=s.TARGET['binding_id'],DEVICE=s.TARGET['device_id'],PRINCIPAL='principal_test',digest=lambda v:hashlib.sha256(s.canonical(v)).hexdigest())
        marker={'approval_id':'call_synthetic_offline_r14','phase':'intake_closed','pilot_id':None}
        state={'schema_version':29,**{k:0 for k in ('queued_actions','accepted_actions','open_writers','open_tasks','target_unsettled_actions')}}
        overview={'observed_at_ms':s.now(),'admission':{'admission_mode':'recovery'},
          'scoped_pilot_decisions':[{'decision_id':s.PRIOR,'revoked_at_ms':s.now()}],
          'nodes':[{'device_id':c.DEVICE,'runtime_instance_id':'synthetic','activation_epoch':'synthetic','readiness':'ready'}]}
        public=s.public(c,{'service_instance_id':s.SERVICE},state,overview,{'expires_at_ms':s.EXPIRES},marker,b'{}',False)
        self.assertIn('node',public);self.assertIn('next_marker_sha256',public)
        with tempfile.TemporaryDirectory(prefix='r14-server-offline-') as temp:
            file=Path(temp)/'synthetic-observation.json';file.write_text(json.dumps(public),encoding='utf-8')
            js="const h=require(process.argv[1]);const fs=require('node:fs');h.guardServer(JSON.parse(fs.readFileSync(process.argv[2],'utf8')),{now:Number(process.argv[3])});"
            result=subprocess.run(['node','-e',js,str(WINDOWS/'transition-r14.cjs'),str(file),str(s.now())],cwd=Path(r'E:\Github\Tools-Codex-web'),
              capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,'Actual Windows guard rejected synthetic closed-phase projection')

if __name__=='__main__':unittest.main()
