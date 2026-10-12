"""Offline proof of the preserved deployed admission API; no external effects."""
import ast
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3

HERE=Path(__file__).resolve().parent
STORE=HERE.parents[1]/'initial-proof-server/codex-control-plane-9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c/control-plane/control_plane/store.py'
source=STORE.read_bytes()
tree=ast.parse(source)
klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ControlPlaneStore')
method=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='set_admission_mode')
scope={'Any':object,'ValidationError':ValueError,'ConflictError':RuntimeError}
exec(compile(ast.Module(body=[method],type_ignores=[]),str(STORE),'exec'),scope)

class Fixture:
    set_admission_mode=scope['set_admission_mode']
    def __init__(self,mode='scoped_pilot'):
        self.db=sqlite3.connect(':memory:',isolation_level=None)
        self.db.row_factory=sqlite3.Row;self.events=[]
        self.db.executescript('CREATE TABLE control_plane_state(state_key TEXT,state_value TEXT,changed_at_ms INTEGER);'
          'CREATE TABLE scoped_pilot_decisions(decision_id TEXT,revoked_at_ms INTEGER,expires_at_ms INTEGER);')
        self.db.execute('INSERT INTO control_plane_state VALUES (?,?,?)',('admission_mode',mode,1))
        self.db.execute('INSERT INTO scoped_pilot_decisions VALUES (?,?,?)',('pilot_unchanged',None,10000))
    @contextmanager
    def _connection(self):yield self.db
    def _admission_mode(self,c):return c.execute('SELECT state_value FROM control_plane_state').fetchone()[0]
    def clock(self):return 100
    def _event(self,*args):self.events.append(args[3])
    def admission_status(self):return {'admission_mode':self._admission_mode(self.db)}
    def revoked(self):return self.db.execute('SELECT revoked_at_ms FROM scoped_pilot_decisions').fetchone()[0]

checks=[]
for mode in ('scoped_pilot','recovery'):
    f=Fixture(mode);result=f.set_admission_mode(mode='recovery')
    assert result['admission_mode']=='recovery' and f.revoked()==100
    assert 'scoped_pilot_decision_revoked_by_recovery' in f.events
    checks.append({'initial_mode':mode,'recovery_revokes_existing_pilot':True})
f=Fixture();f.set_admission_mode(mode='scoped_pilot')
assert f.revoked() is None and f.admission_status()['admission_mode']=='scoped_pilot'
checks.append({'same_scoped_pilot_mode_pauses_intake':False})
for mode in ('paused','suspended'):
    f=Fixture()
    try:f.set_admission_mode(mode=mode)
    except ValueError:checks.append({'unsupported_mode':mode,'denied':True})
    else:raise AssertionError('unsupported mode was accepted')
print(json.dumps({'phase':'r13_supported_intake_contract_proof','ok':True,'remote_effects':False,
 'source_revision':'9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c',
 'store_sha256':hashlib.sha256(source).hexdigest(),'checks':checks,
 'unchanged_pilot_pause_reopen_supported':False},sort_keys=True))
