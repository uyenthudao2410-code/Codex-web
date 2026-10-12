'use strict';
// Pure fixtures only: do not run node-agent, IPC, Sandbox, SSH or policy writes.
const assert=require('node:assert/strict'),{test}=require('node:test');
const h=require('./reconcile.cjs');
const before={enabled:true,authority_mode:'standing',expires_at_ms:null,allowed_relative_prefixes:['.'],max_bytes:16384,facade_contract:{...h.facade,sha256:'274af168c29bc7a10eb35e2314632badddabe456c2c645cda7a7767480fc2e32'}};
const after={...before,facade_contract:h.facade};
const now=h.requested+1_500_000;
const server={ok:true,remote_mutation:false,source_revision:h.serverRevision,service_instance_id:'cp_339c7a19bc2443eeab35583addfef543',binding_id:h.target.binding_id,admission:'scoped_pilot',observed_at_ms:now-1000,next_requested_at_ms:h.requested,next_expires_at_ms:h.expiry,next_context_id:h.contextId,next_pilot_id:h.pilotId,state:{queued_actions:0,accepted_actions:0,open_writers:0,open_tasks:0,target_unsettled_actions:0}};
const denied=(fn,code)=>assert.throws(fn,e=>e.code===code);
test('only the fresh facade contract may change',()=>assert.equal(h.guardReplacement(before,after),true));
test('path, lifetime, enabled, limits, extra fields cannot change',()=>{for(const delta of [{allowed_relative_prefixes:['..']},{expires_at_ms:h.expiry},{enabled:false},{max_bytes:999999},{added_field:true}])denied(()=>h.guardReplacement(before,{...after,...delta}),'NONCONTRACT_POLICY_FIELD_CHANGED');});
test('wrong current facade is refused',()=>denied(()=>h.guardReplacement(before,{...after,facade_contract:before.facade_contract}),'POST_FACADE_MISMATCH'));
test('fresh exact same authority and quiescence are accepted',()=>assert.equal(h.guardServer(server,now),true));
test('expired, reanchored and wrong context/pilot authority are refused',()=>{for(const delta of [{next_expires_at_ms:h.expiry+1},{next_requested_at_ms:h.requested+1},{next_context_id:'another'},{next_pilot_id:'another'}])denied(()=>h.guardServer({...server,...delta},now),'EXACT_UNCHANGED_60M_AUTHORITY_REQUIRED');denied(()=>h.guardServer({...server,observed_at_ms:h.expiry},h.expiry),'EXACT_UNCHANGED_60M_AUTHORITY_REQUIRED');});
test('wrong server, recovery admission and stale/future receipt are refused',()=>{for(const delta of [{host:'wrong'},{source_revision:'wrong'},{admission:'recovery'},{observed_at_ms:now-60000},{observed_at_ms:now+1}])denied(()=>h.guardServer({...server,...delta},now),'FRESH_SCOPED_PILOT_RECEIPT_REQUIRED');});
test('any live central work is refused',()=>{for(const k of Object.keys(server.state))denied(()=>h.guardServer({...server,state:{...server.state,[k]:1}},now),'CENTRAL_TASKS_NOT_QUIESCENT');});
test('CLI arguments preserve existing exact bounds without expiry or probe',()=>{const a=h.installArgs('FileRead',before);assert.equal(a[a.indexOf('--max-bytes')+1],'16384');assert.equal(a[a.indexOf('--allowed-relative-prefix')+1],'.');assert.ok(a.includes('--replace'));assert.ok(!a.includes('--expires-at-ms'));const e=h.installArgs('Exec',{allowed_argv_prefixes:[['node']],max_timeout_ms:300000,max_output_bytes:65536});assert.equal(e[e.indexOf('--allowed-argv-prefix')+1],'["node"]');assert.equal(e[e.indexOf('--max-timeout-ms')+1],'300000');assert.ok(!e.includes('--probe'));});
test('admitted receipt digest follows product projection excluding enabled',()=>assert.equal(h.admittedDigest(after),h.admittedDigest({...after,enabled:false})));
