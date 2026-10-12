'use strict';
// Query-only observation; whitelist public identity fields, never descriptor secrets.
const fs = require('node:fs'), path = require('node:path');
const repo = path.resolve(__dirname, '../../../../..');
const services = path.join(repo, 'electron/services');
const {createRuntimePaths} = require(path.join(services, 'runtimePaths'));
const {RecoveryIpcClient} = require(path.join(services, 'recoveryIpc'));
const {descriptorRequestOptions, descriptorMatchesInstallation} = require(path.join(services, 'recoveryHostLauncher'));
const {observeLifecycleProcessIdentity, sameProcessIdentity} = require(path.join(services, 'processIdentity'));
const {canonicalLedgerCensus} = require(path.join(services, 'fullCleanActivation'));
const dataRoot = 'C:\\Users\\daoth\\AppData\\Roaming\\web-mcp-assistant';
const pick = (v, keys) => Object.fromEntries(keys.map(k => [k, v?.[k] ?? null]));
async function main() {
  const descriptor = JSON.parse(fs.readFileSync(path.join(dataRoot,'recovery-host.json')));
  const candidates = ['setup-exec-contract-1011-r10', 'initial-proof-1011-r11'].map(tag => {
    const root = path.join(repo, `dist/windows-candidate-mxc-wsb-cbe1774-${tag}/win-unpacked`);
    return {tag, paths:createRuntimePaths({dataRoot, appRoot:path.join(root,'resources/app.asar'), resourcesRoot:path.join(root,'resources/resources'), runtimeMode:'packaged', executablePath:path.join(root,'Coding Tools MCP.exe')})};
  });
  const found = candidates.find(x => descriptorMatchesInstallation(descriptor,x.paths.runtimeIdentity()));
  if(!found) throw Object.assign(new Error(),{code:'UNEXPECTED_INSTALLATION'});
  const owner = await observeLifecycleProcessIdentity(descriptor.owner_pid);
  if(owner.state==='unavailable' || owner.state==='live' && !sameProcessIdentity({pid:descriptor.owner_pid,process_start_token:descriptor.owner_process_start_token},owner)) throw Object.assign(new Error(),{code:'OWNER_CHANGED'});
  const state = JSON.parse(fs.readFileSync(found.paths.stateFile()));
  const agent = JSON.parse(fs.readFileSync(path.join(dataRoot,'control-plane-connected-agent-status.json')));
  const identities = {host:owner};
  for(const name of ['native','tunnel']) identities[name] = state[name+'Pid'] ? await observeLifecycleProcessIdentity(state[name+'Pid']) : {state:'absent'};
  identities.agent = agent.agent_pid ? await observeLifecycleProcessIdentity(agent.agent_pid) : {state:'absent'};
  let publicStatus=null;
  if(owner.state==='live') {
    const client = new RecoveryIpcClient({paths:found.paths}), options=descriptorRequestOptions(descriptor);
    const status=await client.status({...options,fresh:true}), snap=await client.call('runtime.lightweight_snapshot',[],options);
    identities.ui = status.electron_ui_recovery?.pid ? await observeLifecycleProcessIdentity(status.electron_ui_recovery.pid) : {state:'absent'};
    publicStatus={epoch:pick(status.activation_epoch,['activation_epoch_id','state','admission_open','update_incomplete']),projection:pick(snap,['fullyReady','localReady','centralConnected','authorityReady','updateIncomplete','failureKind','centralStatusReason'])};
  }
  const census=await canonicalLedgerCensus({paths:found.paths,workspace:repo,allowAcceptancePending:true,pythonStatusFn:async()=>({installed:true,command:found.paths.portablePython(),prefixArgs:['-B']})});
  const row={observed_at_ms:Date.now(),tag:found.tag,descriptor:pick(descriptor,['installation_id','instance_id','owner_pid','owner_process_start_token']),identities,status:publicStatus,agent:pick(agent,['last_iteration_state','last_heartbeat_state','last_heartbeat_at_ms']),census:pick(census,['safe','code','counts','lifecycle','snapshot','mutated_canonical_ledger'])};
  const file=path.join(__dirname,`root-preflight-${row.observed_at_ms}.json`); fs.writeFileSync(file,JSON.stringify(row,null,2)+'\n',{flag:'wx'});
  process.stdout.write(JSON.stringify({...row,receipt:path.basename(file)})+'\n');
}
main().catch(e=>{process.stdout.write(JSON.stringify({ok:false,code:e.code||'OBSERVATION_FAILED'})+'\n');process.exitCode=1;});
