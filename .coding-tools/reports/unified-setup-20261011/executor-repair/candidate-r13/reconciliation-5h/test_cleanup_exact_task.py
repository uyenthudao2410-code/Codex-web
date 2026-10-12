"""Two focused offline checks for public lease shape and receipt preservation."""
import copy
import importlib.util
from pathlib import Path
import time
import types
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('task_only_cleanup',HERE/'cleanup-exact-after-effect-task.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
s={'TASK':'task_exact','ACTION':'act_exact','changed_only':lambda a,b,keys:
  {k:v for k,v in a.items() if k not in keys}=={k:v for k,v in b.items() if k not in keys}}

def before_rows():
    return {'actions':[{'action_id':'act_exact','delivery_state':'settled','settled_at_ms':10}],
      'receipts':[{'receipt_id':'unknown','payload':'original'},{'receipt_id':'failed','payload':'fixed'}],
      'delivery_attempts':[{'attempt_id':'try_exact'}],
      'mcp_task_sessions':[{'task_id':'task_exact','owner_id':'owner','principal_id':'principal',
        'binding_id':'bind','device_id':'device','workspace_id':'workspace','workspace_generation':'generation',
        'closed_at_ms':None,'close_reason':None}],
      'mcp_task_writer_leases':[{'lease_id':'lease_exact','task_id':'task_exact','binding_id':'bind',
        'lease_generation':1,'acquired_at_ms':1,'renewed_at_ms':2,'expires_at_ms':3,
        'released_at_ms':None,'release_reason':None}]}

class CleanupChecks(unittest.TestCase):
    def test_expired_public_lease_then_release_and_close_preserves_exact_rows(self):
        before=before_rows();lease=before['mcp_task_writer_leases'][0]
        public={k:lease[k] for k in ('task_id','binding_id','lease_generation','acquired_at_ms',
          'renewed_at_ms','expires_at_ms','released_at_ms')};public['state']='expired'
        observed={'task':before['mcp_task_sessions'][0],'writer_lease':public,
          'actions':before['actions'],'observed_at_ms':int(time.time()*1000)}
        h.validate_observation(observed,before,types.SimpleNamespace(),s)
        released=copy.deepcopy(before);released['mcp_task_writer_leases'][0].update(
          released_at_ms=20,release_reason=h.REASON)
        h.preserve(before,released,s)
        closed=copy.deepcopy(released);closed['mcp_task_sessions'][0].update(closed_at_ms=30,close_reason='mcp_task_close')
        h.preserve(before,closed,s,closed=True)
        self.assertLessEqual(len(h.REASON),64)
        self.assertNotIn('lease_id',public)
        self.assertNotIn('released',public)

    def test_changed_receipt_or_wrong_public_task_is_refused(self):
        before=before_rows();changed=copy.deepcopy(before);changed['receipts'][0]['payload']='changed'
        with self.assertRaisesRegex(h.Failure,'ACTION_RECEIPT_OR_ATTEMPT_HISTORY_CHANGED'):
            h.preserve(before,changed,s)
        observation={'task':{**before['mcp_task_sessions'][0],'task_id':'task_other'}}
        with self.assertRaisesRegex(h.Failure,'MCP_TASK_OBSERVATION_CHANGED'):
            h.validate_observation(observation,before,types.SimpleNamespace(),s)

if __name__=='__main__':unittest.main()
