"""One read-only correlation after the dispatched action changed context counts."""
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
REMOTE = '/home/svhome/.local/lib/codex-control-plane/incoming/r11-approved-20261011T163335163457Z'
SCRIPT = r'''
import hashlib, importlib.util, json, re, sqlite3, sys
from pathlib import Path
try:
    directory=Path(sys.argv[1])
    helper=directory/'r11_mcp_canary.py'
    if hashlib.sha256(helper.read_bytes()).hexdigest()!='b9be1f2fb50b3831442dbf12aaf15f68a2af5286c8ae5bd14b74f0a375b7918a': raise ValueError('FROZEN_CANARY_CHANGED')
    spec=importlib.util.spec_from_file_location('r11_read_only_canary',helper)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    c=m.load_common();pins=m.pins_input(c)
    marker=m.private_json(m.NEXT_OPERATION_DIR/'canary-dispatch.json')
    if marker['pins_sha256']!=m.digest(pins): raise ValueError('DISPATCH_PINS_CHANGED')
    config=c.environment();database=Path(config['CONTROL_PLANE_DB'])
    family=m.ids(c,database,marker)
    if family.get('action_id')!='act_a0b6b348fd944ea7b9e1eccf0b4c816f' or family.get('task_id')!='task_d06d0dcedee9447ca8dca049137295aa': raise ValueError('EXACT_DISPATCH_FAMILY_REQUIRED')
    verified=m.verified_payload(family,marker,pins) if family.get('settled') else None
    bind=config.get('CONTROL_PLANE_BIND','127.0.0.1')
    if bind not in {'127.0.0.1','0.0.0.0','::',c.HOST}: raise ValueError('SERVICE_BIND_CHANGED')
    origin='http://'+(c.HOST if bind==c.HOST else '127.0.0.1')+':'+config.get('CONTROL_PLANE_PORT','8765')
    overview=c.api(origin,config['CONTROL_PLANE_OPERATOR_TOKEN'],'/v1/ui/overview')
    now=overview['observed_at_ms']
    contexts=[{k:r.get(k) for k in ('context_id','binding_id','device_id','workspace_id','workspace_generation','expires_at_ms','closed_at_ms')}
              for r in overview['contexts'] if r.get('binding_id')==c.BINDING and r.get('closed_at_ms') is None and r['expires_at_ms']>now]
    with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row;db.execute('PRAGMA query_only=ON')
        action=dict(db.execute('SELECT context_id,expires_at_ms FROM actions WHERE action_id=?',(family['action_id'],)).fetchone())
        rejected=[]
        for row in db.execute('SELECT payload_json FROM receipts WHERE action_id=? AND receipt_state=?',(family['action_id'],'rejected')):
            value=json.loads(row['payload_json'])
            codes=[]
            def code_fields(item):
                if isinstance(item,dict):
                    for k,v in item.items():
                        if k in ('code','reason_code','error_code','reason','classification') and isinstance(v,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}',v): codes.append({'field':k,'value':v})
                        elif isinstance(v,(dict,list)): code_fields(v)
                elif isinstance(item,list):
                    for v in item: code_fields(v)
            code_fields(value);rejected.append({'keys':sorted(value) if isinstance(value,dict) else [],'codes':codes})
    m.require(m.sha(m._prior_marker_path.read_bytes())==m._prior_marker_sha256,'PREVIOUS_AUTHORITY_MARKER_CHANGED_DURING_TRIAL')
    print(json.dumps({'ok':True,'phase':'observe','provenance':'central_mcp_service_trial',
        'family':m.public_family(family),'verified_patch_and_initial_proof_summary':verified,
        'native_semantic_acceptance':'pending','acceptance_blocker':'NATIVE_CHATWEB_ACCEPTANCE_TRANSPORT_UNAVAILABLE',
        'replay_forbidden':True,'remote_mutation':False,'read_only_reconciliation':{
            'reason':'post-dispatch authority cardinality diagnosis; no new effect or acceptance',
            'observed_at_ms':now,'active_target_contexts':contexts,'exact_action_context':action,'rejection':rejected}}))
except Exception as e:
    code=getattr(e,'code',None) or (str(e) if isinstance(e,ValueError) else 'READ_ONLY_INSPECTION_FAILED')
    print(json.dumps({'ok':False,'phase':'read_only_inspection_failed','code':code,'exception_type':type(e).__name__,'remote_mutation':False}));sys.exit(2)
'''

try:
    result = subprocess.run(['ssh','-T','-oBatchMode=yes','-oStrictHostKeyChecking=yes','-oConnectTimeout=15',
        'svhome@100.116.112.22','/usr/bin/python3 -B - '+REMOTE], input=SCRIPT.encode(), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=45)
    value=json.loads(result.stdout)
    if not isinstance(value,dict) or not isinstance(value.get('phase'),str): raise ValueError()
    receipt=HERE/('read-only-canary-inspect-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    wrapper={'ok':result.returncode==0 and value.get('ok') is True,'phase':'root_read_only_canary_inspection',
        'ssh_returncode':result.returncode,'remote_dir':REMOTE,'public_receipts':[value],
        'stderr_disclosed':False,'remote_mutation':False,'receipt_path':str(receipt)}
    with receipt.open('x',encoding='utf-8') as handle: json.dump(wrapper,handle,indent=2);handle.write('\n')
    print(json.dumps(wrapper));raise SystemExit(0 if wrapper['ok'] else 2)
except Exception:
    print('{"ok":false,"phase":"root_read_only_inspection_failed","remote_mutation":false,"stderr_disclosed":false}');raise SystemExit(2)
