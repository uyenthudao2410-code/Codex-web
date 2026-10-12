"""Read-only diagnosis of the exact r14 context guard; no server writes or owner lock."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3

COMMON=Path('/home/svhome/.local/lib/codex-control-plane/incoming/r11-approved-20261011T225341342686Z/r11_common.py')
COMMON_SHA='25f2d15359ff49a50e1ded411d40f1f029fb6067390c68aff9b93bda0130d986'
DIRECTORY=Path('/home/svhome/.local/state/codex-control-plane/owner-operations/r14-same-window-activation')
CONTEXT='ctx_1e7e2fec6f0e43018db7a51c6980e5c2'
PRIOR='pilot_b1cb26c319fb489aae24d3b746318447'
EXPIRES=1791776571067
SERVICE='cp_339c7a19bc2443eeab35583addfef543'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def project(row,keys):return {key:row.get(key) for key in keys}
def rows(database):
    with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True,timeout=5) as d:
        d.row_factory=sqlite3.Row;d.execute('PRAGMA query_only=ON');d.execute('BEGIN')
        return {table:[dict(r) for r in d.execute('SELECT * FROM '+table+' ORDER BY rowid')]
          for table in ('contexts','scoped_pilot_decisions','mcp_service_grants')}

def main():
    c=None
    try:
        if sha(COMMON.read_bytes())!=COMMON_SHA:raise ValueError()
        spec=importlib.util.spec_from_file_location('r14_context_guard_read_only_common',COMMON)
        c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
        origin,auth,database,health,before,overview,grant=c.inspect()
        c.require(health['service_instance_id']==SERVICE and health['declared_source_revision']==c.REVISION,'EXACT_SERVER_CHANGED')
        before_rows=rows(database);stamp=overview['observed_at_ms']
        target=[r for r in before_rows['contexts'] if r['binding_id']==c.BINDING]
        open_rows=[r for r in target if r['closed_at_ms'] is None]
        exact=[r for r in target if r['context_id']==CONTEXT]
        pilots=before_rows['scoped_pilot_decisions'];unrevoked=[r for r in pilots if r['revoked_at_ms'] is None]
        files={}
        for name in ('close-intent.json','replace-intent.json','reopen-intent.json','authority-transition-public.json'):
            path=DIRECTORY/name
            if path.exists() or path.is_symlink():
                raw=c.protected_file(path);value=json.loads(raw)
                files[name]={'exists':True,'sha256':sha(raw),**project(value,('phase','operation','approval_id','context_id','expires_at_ms','prior_pilot_id','pilot_id'))}
            else:files[name]={'exists':False}
        after=c.state(database);c.compare_history(before,after)
        c.require(before_rows==rows(database),'AUTHORITY_ROWS_CHANGED_DURING_READ_ONLY_INSPECTION')
        keys=('context_id','binding_id','device_id','workspace_id','workspace_generation','expires_at_ms','closed_at_ms')
        pkeys=('decision_id','principal_id','binding_id','device_id','endpoint_id','workspace_id','workspace_generation','expires_at_ms','revoked_at_ms')
        result={'phase':'r14_context_guard_read_only_inspection','ok':True,'observed_at_ms':stamp,
          'service_instance_id':health['service_instance_id'],'source_revision':c.REVISION,'binding_id':c.BINDING,
          'context_id':CONTEXT,'expected_expires_at_ms':EXPIRES,'admission':overview['admission']['admission_mode'],
          'exact_context_rows':[project(r,keys) for r in exact],
          'unclosed_target_contexts':[project(r,keys) for r in open_rows],
          'unclosed_target_context_count':len(open_rows),
          'live_unclosed_target_context_count':sum(r['expires_at_ms']>stamp for r in open_rows),
          'expired_unclosed_target_context_count':sum(r['expires_at_ms']<=stamp for r in open_rows),
          'all_context_rows_sha256':c.digest(before_rows['contexts']),
          'all_unrevoked_pilots':[project(r,pkeys) for r in unrevoked],
          'prior_pilot_rows':[project(r,pkeys) for r in pilots if r['decision_id']==PRIOR],
          'grant':project(grant,('grant_id','principal_id','expires_at_ms','revoked_at_ms','scopes')),
          'service_grant_sha256':c.digest(grant),'state':before,'state_sha256':c.digest(before),
          'remote_phase_files':files,'server_rows_preserved':True,'remote_mutation':False,
          'raw_error_disclosed':False,'no_mutation_or_replay_performed':True}
        print(json.dumps(result,sort_keys=True,separators=(',',':')))
    except Exception as error:
        code=error.code if c is not None and isinstance(error,c.GuardFailure) else 'READ_ONLY_CONTEXT_INSPECTION_FAILED'
        if not re.fullmatch(r'[A-Z0-9_]{1,128}',str(code)):code='READ_ONLY_CONTEXT_INSPECTION_FAILED'
        print(json.dumps({'phase':'r14_context_guard_read_only_inspection_failed','ok':False,'code':code,
          'remote_mutation':False,'raw_error_disclosed':False}));raise SystemExit(2) from None
