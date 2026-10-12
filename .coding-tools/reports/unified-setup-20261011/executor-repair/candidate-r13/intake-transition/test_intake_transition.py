"""Offline guards and mocked supported-API sequence; no external effects."""
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('intake',HERE/'transition-intake.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

class Fixture:
    def __init__(self,root):
        self.clock=s.REQUESTED+1800000;self.mode='scoped_pilot';self.calls=[]
        self.c=types.SimpleNamespace(BINDING='binding',DEVICE='device',WORKSPACE='workspace',GENERATION='generation',
         PRINCIPAL='principal',LOCAL_ROOT=r'E:\Github\Tools-Codex-web',LOCAL_PROFILE='web-mcp-assistant',
         REVISION='revision',PACKAGE='package',HOST='100.116.112.22',SERVICE='codex-control-plane.service')
        self.rows={'contexts':[{'context_id':s.CONTEXT,'binding_id':'binding','device_id':'device','workspace_id':'workspace',
         'workspace_generation':'generation','expires_at_ms':s.EXPIRES,'closed_at_ms':None}],
         'scoped_pilot_decisions':[{'decision_id':s.OLD_PILOT,'binding_id':'binding','principal_id':'principal','device_id':'device',
          'workspace_id':'workspace','workspace_generation':'generation','expires_at_ms':s.EXPIRES,'revoked_at_ms':None,'reason':'old'}]}
        self.health={'declared_source_revision':'revision','package_source_sha256':'package','service_instance_id':'cp_exact'}
        self.state={'schema_version':29,'all_history_sha256':'unchanged'};self.grant={'grant_id':'preserved'}
        self.ident={'activation_epoch':'new-epoch','runtime_instance_id':'new-runtime','mcp_server_instance_id':'new-mcp','contract_version':'sha256:new'}
        self.c.digest=lambda v:hashlib.sha256(s.canonical(v)).hexdigest()
        self.c.inspect=lambda:('origin','memory-only-auth',Path(root)/'not-live.sqlite3',self.health,self.state,self.overview(),self.grant)
        self.c.state=lambda _:self.state
        self.c.target=lambda _:self.grant
        self.c.compare_history=lambda a,b:self.assert_same(a,b)
        self.c.protected_file=lambda p:p.read_bytes()
        self.c.private_directory=lambda p,create=False:p.mkdir(mode=0o700,parents=True) if create else None
        self.c.operation_lock=lambda:os.open(Path(root)/'lock',os.O_CREAT|os.O_RDWR,0o600)
        self.c.renewed_authority=lambda o,m:None
        self.c.api=self.api
        self.c.public_observation=lambda h,st,o,g:{'observed_at_ms':self.clock,'service_instance_id':'cp_exact',
          'source_revision':'revision','package_source_sha256':'package','state':st,'state_sha256':self.c.digest(st),
          'service_grant_sha256':self.c.digest(g),'admission':self.mode,'binding_id':'binding'}
    @staticmethod
    def assert_same(a,b):
        if a!=b:raise s.Failure('HISTORY_CHANGED')
    def overview(self):return {'observed_at_ms':self.clock,'admission':{'admission_mode':self.mode},
      'nodes':[{'device_id':'device','last_seen_at_ms':self.clock,'readiness':'ready','policy_state':'enabled',
       'policy_expires_at_ms':self.clock+50000,**self.ident}],**copy.deepcopy(self.rows)}
    def api(self,origin,auth,route,body=None):
        self.calls.append((route,copy.deepcopy(body)))
        if route=='/healthz':return self.health
        if route=='/v1/maintenance/admission':
            self.mode=body['mode']
            if self.mode=='recovery':
                for r in self.rows['scoped_pilot_decisions']:
                    if r['revoked_at_ms'] is None:r['revoked_at_ms']=self.clock
            return {'admission_mode':self.mode}
        if route=='/v1/scoped-pilot-decisions':
            r={'decision_id':'pilot_'+'f'*32,'binding_id':'binding','principal_id':'principal','device_id':'device',
               'workspace_id':'workspace','workspace_generation':'generation','expires_at_ms':body['expires_at_ms'],
               'revoked_at_ms':None,'reason':body['reason']}
            self.rows['scoped_pilot_decisions'].append(r);return r
        if route=='/v1/ui/overview':return self.overview()
        raise AssertionError('unexpected API')
    def expected(self,marker_sha='absent'):return {'ok':True,'service_instance_id':'cp_exact',
       'state_sha256':self.c.digest(self.state),'service_grant_sha256':self.c.digest(self.grant),
       'next_marker_sha256':marker_sha,'observed_at_ms':self.clock}

class Tests(unittest.TestCase):
    def test_window_boundary_no_extension(self):
        s.window(s.EXPIRES-s.MIN_REMAINING)
        with self.assertRaises(s.Failure):s.window(s.EXPIRES-s.MIN_REMAINING+1)
        with self.assertRaises(s.Failure):s.window(s.REQUESTED-1)
    def test_mocked_pause_rotation_reopen_and_no_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);out=root/'new-r13';f=Fixture(root);before=copy.deepcopy(f.rows)
            with patch.object(s,'OUT',out),patch.object(s,'MARKER',out/'transition-public.json'),patch.object(s,'CANARY',out/'canary-r13'),\
             patch.object(s,'load_common',return_value=f.c),patch.object(s,'cleanup'),patch.object(s,'prior',return_value={}),\
             patch.object(s,'authority',side_effect=lambda _:copy.deepcopy(f.rows)),patch.object(s,'now',return_value=f.clock),\
             patch.object(s.os,'O_NOFOLLOW',0,create=True),patch.object(s.os,'fchmod',lambda *a:None,create=True):
                packet={'action':'pause-rotate','execute':True,'operator_approved':True,'approval_id':s.APPROVAL,'server':f.expected()}
                with redirect_stdout(io.StringIO()) as output:s.main(packet)
                receipt=json.loads(output.getvalue());m=json.loads((out/'transition-public.json').read_bytes())
                self.assertEqual(receipt['next_phase'],'authority_rotated_in_recovery')
                self.assertEqual(receipt['expires_at_ms'],s.EXPIRES)
                self.assertEqual(f.rows['contexts'],before['contexts'])
                self.assertEqual([v for v in f.calls if v[1] is not None][:2],[('/v1/maintenance/admission',{'mode':'recovery'}),
                 ('/v1/scoped-pilot-decisions',{'principal_id':'principal','binding_id':'binding','expires_at_ms':s.EXPIRES,'reason':s.REASON})])
                self.assertNotEqual(m['pilot_id'],s.OLD_PILOT)
                self.assertTrue((out/'canary-r13').is_dir())
                with self.assertRaises(s.Failure),redirect_stdout(io.StringIO()):s.main(packet)
                reopen={**packet,'action':'reopen','server':f.expected(s.sha((out/'transition-public.json').read_bytes())),
                  'native_identity':f.ident}
                with redirect_stdout(io.StringIO()) as output:s.main(reopen)
                self.assertEqual(json.loads(output.getvalue())['admission'],'scoped_pilot')
                self.assertEqual([body['mode'] for route,body in f.calls if route=='/v1/maintenance/admission'],['recovery','scoped_pilot'])
                self.assertEqual(len(f.rows['scoped_pilot_decisions']),2)
    def test_rotation_denies_scope_or_old_history_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            f=Fixture(temp);baseline=copy.deepcopy(f.rows);f.rows['scoped_pilot_decisions'][0]['revoked_at_ms']=f.clock
            f.api('o','a','/v1/scoped-pilot-decisions',{'expires_at_ms':s.EXPIRES,'reason':s.REASON})
            m={'authority_baseline':baseline,'old_pilot_revoked_at_ms':f.clock,'pilot_id':'pilot_'+'f'*32}
            s.validate_rotation(f.rows,m,f.c)
            for table,index,key,value in [('contexts',0,'expires_at_ms',s.EXPIRES+1),
             ('scoped_pilot_decisions',0,'reason','changed'),('scoped_pilot_decisions',1,'expires_at_ms',s.EXPIRES+1),
             ('scoped_pilot_decisions',1,'binding_id','wrong')]:
                with self.subTest(key=key):
                    rows=copy.deepcopy(f.rows);rows[table][index][key]=value
                    with self.assertRaises(s.Failure):s.validate_rotation(rows,m,f.c)
if __name__=='__main__':unittest.main()
