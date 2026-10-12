"""Focused offline r13 authority receipt guards; no SSH or live IPC."""
import copy
import importlib.util
from pathlib import Path
import types
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('canary',HERE/'r13_mcp_canary.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
C=types.SimpleNamespace(HOST='100.116.112.22',SERVICE='codex-control-plane.service',REVISION='revision',
 BINDING='binding',DEVICE='device',WORKSPACE='workspace',GENERATION='generation',LOCAL_ROOT=r'E:\Github\Tools-Codex-web',LOCAL_PROFILE='web-mcp-assistant')
def fixture():
    pins={'approval_id':'r13-same-window-transition','context_id':'ctx_d7a539dd85264a62951fddad0ffa2f23',
     'requested_at_ms':1791747735200,'expires_at_ms':1791751335200,'pilot_id':'pilot_'+'f'*32,
     'authority_marker_sha256':'a'*64,'service_instance_id':'cp_exact',
     'activation_epoch':'epoch','runtime_instance_id':'runtime','mcp_server_instance_id':'mcp','contract_version':'contract'}
    old='pilot_98c0b502568a4f888b3106838004c117';revoked=1791749000000
    r={'host':C.HOST,'service':C.SERVICE,'admission':'scoped_pilot','source_revision':C.REVISION,
     'binding_id':C.BINDING,'device_id':C.DEVICE,'workspace_id':C.WORKSPACE,'workspace_generation':C.GENERATION,
     'root':C.LOCAL_ROOT,'profile':C.LOCAL_PROFILE,'operation':s.NEXT_OPERATION,'next_phase':'intake_reopened',
     'context_preserved':True,'window_preserved':True,'authority_extended':False,'replacement_pilot_live':True,
     'prior_marker_sha256':s.PRIOR_AUTHORITY_SHA256,'next_marker_sha256':pins['authority_marker_sha256'],
     'observed_at_ms':1791749100000,'old_pilot_id':old,'old_pilot_revoked_at_ms':revoked,
     'old_pilot':{'decision_id':old,'expires_at_ms':pins['expires_at_ms'],'revoked_at_ms':revoked},
     'replacement_pilot':{'decision_id':pins['pilot_id'],'expires_at_ms':pins['expires_at_ms'],'revoked_at_ms':None},
     'node':{k:pins[k] for k in ('activation_epoch','runtime_instance_id','mcp_server_instance_id','contract_version')},
     **{k:pins[k] for k in ('approval_id','context_id','requested_at_ms','expires_at_ms','pilot_id','service_instance_id')}}
    return pins,r
class Tests(unittest.TestCase):
    def test_exact_rotated_reopened_receipt(self):
        p,r=fixture();s.receipt_guard(p,r,C)
        self.assertEqual(s.CANARY_OPERATION_DIR.name,'canary-r13')
        self.assertEqual(s.PRIOR_AUTHORITY_MARKER.parent.name,'r12-initial-verification-60m')
    def test_wrong_scope_window_or_lineage_denied(self):
        for k,v in [('expires_at_ms',1791751335201),('context_id','new-context'),('pilot_id','pilot_98c0b502568a4f888b3106838004c117'),
         ('approval_id','call_1KzUkF0gMn6uVpHd3QisTzXF'),('next_phase','authority_rotated_in_recovery'),('replacement_pilot_live',False),('prior_marker_sha256','b'*64)]:
            with self.subTest(key=k):
                p,r=fixture();r[k]=v
                with self.assertRaises(s.Failure):s.receipt_guard(p,r,C)
    def test_wrong_native_or_revocation_denied(self):
        for native in (True,False):
            p,r=fixture()
            if native:r['node']['runtime_instance_id']='other'
            else:r['old_pilot']['revoked_at_ms']=None
            with self.assertRaises(s.Failure):s.receipt_guard(p,r,C)
if __name__=='__main__':unittest.main()
