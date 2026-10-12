"""Pure selected guard checks; no inspect/API/main/SQL call."""
import ast
import copy
import hashlib,json
from pathlib import Path
import re
from types import SimpleNamespace
BASE=Path(__file__).resolve().parent
HELPER=BASE/'ubuntu-r10-same-expiry-recovery-intake.py'
raw=HELPER.read_bytes();compile(raw,str(HELPER),'exec');tree=ast.parse(raw)
names={'SERVICE_INSTANCE','CONTEXT','PILOT','REQUESTED','EXPIRY','FAILED_EPOCH','NATIVE_CONTRACT'}
selected=[row for row in tree.body if isinstance(row,ast.ClassDef) and row.name=='Refused'
    or isinstance(row,ast.FunctionDef) and row.name in {'need','exact_pilot','reopen_identity'}
    or isinstance(row,ast.Assign) and isinstance(row.targets[0],ast.Name) and row.targets[0].id in names]
ns={'re':re};exec(compile(ast.Module(body=selected,type_ignores=[]),str(HELPER),'exec'),ns)
g={'BINDING':'bind_3e05bf64cb3e4bab93d930ae1692bebb','PRINCIPAL':'svcprn_cd98750c7c7e45678d201066dc1b7d7a',
    'DEVICE':'72ceec2d-e3f2-472f-8e3c-99fffe053035','WORKSPACE':'workspace_dda1d78e9a21402aa6213f72af64f788',
    'GENERATION':'generation_c2f13e8d02344cf6a38a3f42ecfa59b6','PREDECESSOR_EPOCH':'activation-mv3qe36p-991f11f44f47d32ea2e217b1db882ff7'}
pilot={'binding_id':g['BINDING'],'principal_id':g['PRINCIPAL'],'device_id':g['DEVICE'],
    'workspace_id':g['WORKSPACE'],'workspace_generation':g['GENERATION'],'expires_at_ms':ns['EXPIRY']}
ns['exact_pilot'](g,pilot)
args=SimpleNamespace(expected_activation_epoch='activation-fixture-newrecovered',expected_process_instance='recovered-process',
    expected_server_instance='recovered-server',expected_native_contract=ns['NATIVE_CONTRACT'])
node={'device_id':g['DEVICE'],'activation_epoch':args.expected_activation_epoch,'runtime_instance_id':args.expected_process_instance,
    'mcp_server_instance_id':args.expected_server_instance,'contract_version':'sha256:'+ns['NATIVE_CONTRACT'],
    'readiness':'ready','policy_state':'enabled','last_seen_at_ms':100000,'policy_expires_at_ms':160000}
overview={'observed_at_ms':100001,'nodes':[node]}
ns['reopen_identity'](g,overview,args)
cases=[]
for name,mutate in [('different_scope',lambda row:row.update(binding_id='wrong')),('extended_expiry',lambda row:row.update(expires_at_ms=ns['EXPIRY']+1))]:
    sample=copy.deepcopy(pilot);mutate(sample)
    try:ns['exact_pilot'](g,sample)
    except ns['Refused'] as e:cases.append({'case':name,'rejected':e.code})
    else:raise AssertionError(name)
for name,mutate in [('offline',lambda row:row.update(readiness='blocked')),('wrong_native',lambda row:row.update(runtime_instance_id='wrong-process')),
    ('stale_heartbeat',lambda row:row.update(last_seen_at_ms=40000)),('expired_policy',lambda row:row.update(policy_expires_at_ms=100001)),
    ('wrong_epoch',lambda row:row.update(activation_epoch=ns['FAILED_EPOCH']))]:
    sample=copy.deepcopy(overview);mutate(sample['nodes'][0])
    try:ns['reopen_identity'](g,sample,args)
    except ns['Refused'] as e:cases.append({'case':name,'rejected':e.code})
    else:raise AssertionError(name)
assert hashlib.sha256((BASE/'ubuntu-r10-store-authority-v3-local-proof.py').read_bytes()).hexdigest()=='a312575854fee785158fa21624a096d7b09ae3701ded38f449a7330ba089ebec'
assert '/renew' not in raw.decode() and 'save_recovery' in raw.decode() and 'newpilot_id' in raw.decode()
result={'kind':'pure_same_expiry_recovery_guard_proof','helper_sha256':hashlib.sha256(raw).hexdigest(),
    'syntax_passed':True,'positive_cases':2,'negative_cases':cases,'v3_unchanged':True,'main_invoked':False,'live_operations':False}
with (BASE/'r10-same-expiry-recovery-static-proof.json').open('x',encoding='utf-8') as handle:json.dump(result,handle,indent=2);handle.write('\n')
print(json.dumps(result,separators=(',',':')))
