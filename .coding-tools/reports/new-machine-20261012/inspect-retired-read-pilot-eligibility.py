"""Compare serving versus proposed pilot predicates in read-only memory."""
import ast
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[3]
source = (root / "control-plane/control_plane/store.py").read_text(encoding="utf-8")
tree = ast.parse(source)
method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
              and node.name == "_quarantined_retired_file_read_unknown_matches_pilot_workspace")
method_source = ast.get_source_segment(source, method)
remote = r'''
import hashlib,json,sqlite3,subprocess,sys,time,types
from pathlib import Path
pid=int(subprocess.check_output(['systemctl','--user','show','codex-control-plane.service','--property=MainPID','--value'],text=True).strip())
env=dict(item.split('=',1) for item in Path(f'/proc/{pid}/environ').read_text().split('\0') if '=' in item)
for folder in env.get('PYTHONPATH','').split(':'):
 if folder: sys.path.insert(0,folder)
from control_plane.store import ControlPlaneStore
store=object.__new__(ControlPlaneStore)
store.clock=lambda:int(time.time()*1000)
db=Path(env['CONTROL_PLANE_DB'])
if not db.is_absolute(): db=Path(f'/proc/{pid}/cwd').resolve()/db
con=sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True)
con.execute('PRAGMA query_only=ON')
con.row_factory=sqlite3.Row
kw={'device_id':'4c4b7a5b-7744-49ae-a490-78a528a00471','owner_id':'owner_default','principal_id':'svcprn_cd98750c7c7e45678d201066dc1b7d7a','binding_id':'bind_71661b1046884174b01c99af5f8546aa','workspace_id':'workspace_f93b5bac9dc74fae9cea66f44c4ebc94','workspace_generation':'generation_a420c8bfcfcb4e42b5bb7fc5e5cec097'}
before=store._blocking_unresolved_action_count_for_pilot(con,**kw)
actions=con.execute("SELECT * FROM actions WHERE device_id=? AND delivery_state IN ('dispatch_unconfirmed','accepted','reconcile_required') ORDER BY created_at_ms,action_id",(kw['device_id'],)).fetchall()
namespace={'sqlite3':sqlite3}
exec(METHOD_SOURCE,namespace)
store._quarantined_retired_file_read_unknown_matches_pilot_workspace=types.MethodType(namespace['_quarantined_retired_file_read_unknown_matches_pilot_workspace'],store)
checks=[]
for action in actions:
 original=store._quarantined_file_read_unknown_matches_pilot_target(con,action=action,owner_id=kw['owner_id'],principal_id=kw['principal_id'],binding_id=kw['binding_id'],workspace_id=kw['workspace_id'],workspace_generation=kw['workspace_generation'])
 proposed=store._quarantined_retired_file_read_unknown_matches_pilot_workspace(con,action=action,**{k:kw[k] for k in ('device_id','owner_id','principal_id','workspace_id','workspace_generation')})
 checks.append({'action_id':action['action_id'],'original_exception':original,'proposed_retired_read_exception':proposed})
print(json.dumps({'observed_at_ms':store.clock(),'operation':'retired_read_proposal_live_read_only','serving_blockers':before,'proposed_blockers':sum(not(c['original_exception'] or c['proposed_retired_read_exception']) for c in checks),'action_checks':checks,'remote_persistent_mutation':False},separators=(',',':')))
con.close()
'''.replace("METHOD_SOURCE", repr(method_source))
result = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "-o",
                         "StrictHostKeyChecking=yes", "svhome@100.116.112.22", "python3 -"],
                        input=remote, text=True, capture_output=True, check=True)
receipt = json.loads(result.stdout)
receipt["overlay_store_sha256"] = __import__("hashlib").sha256(source.replace("\r\n", "\n").encode()).hexdigest()
output = Path(__file__).with_name("retired-read-live-readonly-predicate-receipt.json")
output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, separators=(",", ":")))
