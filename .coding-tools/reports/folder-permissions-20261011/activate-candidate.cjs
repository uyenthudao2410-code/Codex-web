const fs = require('node:fs');
const path = require('node:path');
const { spawnSync, spawn } = require('node:child_process');
const repo = path.resolve(__dirname, '../../..');
const { createRuntimePaths } = require(path.join(repo, 'electron/services/runtimePaths'));
const { RecoveryIpcClient, loadRecoveryDescriptor } = require(path.join(repo, 'electron/services/recoveryIpc'));
const { descriptorMatchesInstallation, descriptorRequestOptions } = require(path.join(repo, 'electron/services/recoveryHostLauncher'));
const { observeLifecycleProcessIdentity, terminateExactProcessTree, waitForExactProcessExit } = require(path.join(repo, 'electron/services/processIdentity'));
const { canonicalLedgerCensus } = require(path.join(repo, 'electron/services/fullCleanActivation'));
const patchCandidate = process.argv[3] === 'r3';
const oldRoot = path.join(repo, patchCandidate
  ? 'dist/windows-candidate-mxc-wsb-cbe1774-folders-unified-1011-r2/win-unpacked'
  : 'dist/windows-candidate-mxc-wsb-cbe1774-recovery-rootonly-1011/win-unpacked');
const newRoot = path.join(repo, patchCandidate
  ? 'dist/windows-candidate-mxc-wsb-cbe1774-folders-unified-1011-r3/win-unpacked'
  : 'dist/windows-candidate-mxc-wsb-cbe1774-folders-unified-1011-r2/win-unpacked');
function runtime(root) {
  const paths = createRuntimePaths({dataRoot:path.join(process.env.APPDATA,'web-mcp-assistant'),
    appRoot:path.join(root,'resources/app.asar'),resourcesRoot:path.join(root,'resources/resources'),
    runtimeMode:'packaged',executablePath:path.join(root,'Coding Tools MCP.exe')});
  const descriptor = loadRecoveryDescriptor(paths);
  if (!descriptorMatchesInstallation(descriptor, paths.runtimeIdentity())) throw new Error('Unexpected runtime installation');
  return {paths,descriptor,client:new RecoveryIpcClient({paths}),options:descriptorRequestOptions(descriptor)};
}
function emit(value) { process.stdout.write(JSON.stringify(value)+'\n'); }
(async () => {
  const phase = process.argv[2];
  const r = runtime(phase === 'switch' ? oldRoot : newRoot);
  const status = await r.client.status({...r.options,fresh:true});
  if (phase === 'switch') {
    const ui = status.electron_ui_recovery;
    if (ui?.registered !== true || ui.ui_installation_id !== r.paths.runtimeIdentity().installation_id) throw new Error('UI identity not verified');
    const uiIdentity = await observeLifecycleProcessIdentity(ui.pid);
    const env = {...process.env}; delete env.ELECTRON_RUN_AS_NODE;
    if (ui.alive === true && uiIdentity.state === 'live') {
      await r.client.call('client.suppress_ui_recovery',[{instance_id:ui.instance_id,reason:'operator_quit'}],r.options);
      const signal = spawnSync(path.join(oldRoot,'Coding Tools MCP.exe'),[`--dev-ui-stop=${ui.instance_id}`],{env,windowsHide:true,timeout:15000});
      if (signal.status !== 0) throw new Error('UI stop signal failed');
      await waitForExactProcessExit(uiIdentity,{timeoutMs:15000});
    } else if (uiIdentity.state !== 'absent') throw new Error('Previous UI process identity is uncertain');
    await r.client.stop({manual:true},r.options);
    const census = await canonicalLedgerCensus({paths:r.paths,workspace:repo});
    emit({phase:'stopped',safe:census.safe,counts:census.counts,reason:census.reason});
    if (census.safe !== true) throw new Error('Stopped runtime census refused candidate transition');
    const current = loadRecoveryDescriptor(r.paths);
    if (current.instance_id !== r.descriptor.instance_id || current.owner_pid !== r.descriptor.owner_pid
      || current.owner_process_start_token !== r.descriptor.owner_process_start_token) throw new Error('Host changed during stop');
    await terminateExactProcessTree({pid:current.owner_pid,process_start_token:current.owner_process_start_token},{includeDescendants:false});
    const child = spawn(path.join(newRoot,'Coding Tools MCP.exe'),[],{env,windowsHide:true,detached:true,stdio:'ignore'});
    child.unref();
    emit({phase:'launched',old_host_pid:current.owner_pid,old_ui_pid:ui.pid,new_ui_pid:child.pid,candidate:newRoot});
  } else if (phase === 'refresh') {
    const result = await r.client.restart({refresh:true,mode:'full_clean_refresh',sourceCheckpoint:null,
      reason:'operator approved packaged folder permissions and live patch contract fix'}, {...r.options,timeout:120000});
    emit({phase:'refresh',state:result.state,epoch:result.activation_epoch_id});
  } else if (phase === 'status') {
    const snapshot = await r.client.call('runtime.lightweight_snapshot',[],r.options);
    const result = {phase:'status',host_pid:status.pid,host_instance:status.instance_id,
      ui:status.electron_ui_recovery,epoch:status.activation_epoch,
      ready:snapshot.fullyReady,local_ready:snapshot.localReady,components_ready:snapshot.componentsReady,
      central_connected:snapshot.centralConnected,authority_ready:snapshot.authorityReady,
      central_reason:snapshot.centralStatusReason,update_incomplete:snapshot.updateIncomplete};
    fs.writeFileSync(path.join(__dirname,'runtime-result.json'),JSON.stringify(result,null,2));
    emit(result);
  } else if (phase === 'census') {
    const census = await canonicalLedgerCensus({paths:r.paths,workspace:repo});
    const result = {phase,safe:census.safe,code:census.code,reason:census.reason,
      counts:census.counts,lifecycle:census.lifecycle};
    fs.writeFileSync(path.join(__dirname,'local-job-census.json'),JSON.stringify(result,null,2));
    emit(result);
  } else if (phase === 'diagnose') {
    const snapshot = await r.client.call('runtime.lightweight_snapshot',[],r.options);
    emit({phase,mcpRunning:snapshot.mcpRunning,nativeAlive:snapshot.nativeAlive,
      localReady:snapshot.localReady,fullyReady:snapshot.fullyReady,
      codeRevision:snapshot.codeRevision,connectorReady:snapshot.connectorReady,
      recovering:snapshot.recovering,failures:snapshot.failures,
      failureKind:snapshot.failureKind,lastStartFailure:snapshot.lastStartFailure,
      mcpHealthFailureKind:snapshot.mcpHealthFailureKind,
      snapshotAgeMs:snapshot.snapshotAgeMs});
  } else if (phase === 'show') {
    const child = spawn(path.join(newRoot,'Coding Tools MCP.exe'),[`--dev-ui-control-center=${status.electron_ui_recovery.instance_id}`],{windowsHide:true,stdio:'ignore'});
    child.unref(); emit({phase:'manager_revealed'});
  } else throw new Error('Unknown phase');
})().catch(error=>{emit({ok:false,code:error.code||'ACTIVATION_FAILED',message:error.message});process.exitCode=1;});
