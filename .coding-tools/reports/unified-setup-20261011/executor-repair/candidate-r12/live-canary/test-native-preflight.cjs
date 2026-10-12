'use strict';
const test = require('node:test'), assert = require('node:assert/strict');
const {packageProof,readyIdentity,readySnapshot} = require('./native-preflight.cjs');
const identity = {observation_schema_version:1,observation_kind:'mcp_identity_read_only',mcp_ready:true,identity_current:true,
  activation_epoch_id:'epoch_new',current_activation_epoch_id:'epoch_new',mcp_process_instance_id:'process_new',
  mcp_server_instance_id:'server_new',tool_contract_sha256:'0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4'};
const revision = {state:'current',running_revision:'r12',disk_revision:'r12',update_pending:false,pending_revision:null};
const status = {activation_epoch:{activation_epoch_id:'epoch_new',state:'READY',admission_open:true},
  code_revision:revision,electron_ui_revision:revision};
const snapshot = {fullyReady:true,localReady:true,componentsReady:true,centralConnected:true,authorityReady:true,
  updateIncomplete:false,codeRevision:{codingMcp:revision}};
test('r12 archive and all fifteen relevant payloads match frozen source',()=>{
  assert.equal(packageProof().matched_files,15);
});
test('final ready identity rejects provisional, stale or wrong native contract',()=>{
  readyIdentity(identity);
  for (const delta of [{identity_current:false},{mcp_ready:false},{observation_schema_version:2},
    {current_activation_epoch_id:'wrong'},{tool_contract_sha256:'a'.repeat(64)}]) {
    assert.throws(()=>readyIdentity({...identity,...delta}));
  }
});
test('final readiness remains strict about admission, route and source',()=>{
  readySnapshot(status,snapshot,identity);
  assert.throws(()=>readySnapshot({...status,activation_epoch:{...status.activation_epoch,admission_open:false}},snapshot,identity));
  assert.throws(()=>readySnapshot(status,{...snapshot,centralConnected:false},identity));
  assert.throws(()=>readySnapshot(status,{...snapshot,codeRevision:{codingMcp:{...revision,update_pending:true}}},identity));
});
