'use strict';
// Bounded one-off operator for this authorized packaged candidate only.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '../../../..');
const candidate = path.join(root, 'dist/windows-candidate-mxc-wsb-cbe1774-r4-timefix-bfix/win-unpacked');
const executable = path.join(candidate, 'Coding Tools MCP.exe');
const appRoot = path.join(candidate, 'resources/app.asar');
const load = name => require(path.join(root, 'electron/services', name));
const { RuntimePaths } = load('runtimePaths');
const { RecoveryIpcClient, loadRecoveryDescriptor } = load('recoveryIpc');
const { descriptorMatchesInstallation, descriptorRequestOptions, readVerifiedReadyHost } = load('recoveryHostLauncher');
const { canonicalLedgerCensus } = load('fullCleanActivation');
const { processIdentityFrom, observeLifecycleProcessIdentity, sameProcessIdentity } = load('processIdentity');
const { selectTrustedRecoveryHostSource } = load('trustedRecoveryBootstrap');
const paths = new RuntimePaths({ dataRoot: path.join(process.env.APPDATA, 'web-mcp-assistant'), appRoot, resourcesRoot: path.join(candidate, 'resources/resources'), executablePath: executable, runtimeMode: 'packaged' });
const client = new RecoveryIpcClient({ paths });
const read = file => JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const assert = (ok, code) => { if (!ok) throw Object.assign(new Error(code), { code }); };
const pick = (v, keys) => Object.fromEntries(keys.filter(k => v?.[k] !== undefined).map(k => [k, v[k]]));
const identityKeys = ['owner_pid', 'owner_process_start_token', 'instance_id', 'installation_id', 'runtime_mode', 'activation_epoch_id'];
const mode = process.argv[2] || 'status';
const report = { schema_version: 1, operation: `bfix_operator_${mode}`, observed_at: new Date().toISOString(), candidate, mutation_started: false };
const reportPath = path.join(__dirname, `bfix-${mode}-${Date.now()}.json`);
function packageProof() {
  assert(sha(executable) === '94f36ad726297bb2c4451ba9931b1532569f14f9f46526223e39fe75bc08e145' && sha(appRoot) === 'b3607da70af1df36a0aa1eb50f5771ba110069e33d08f256da542faca5f7b922', 'EXACT_BFIX_PACKAGE_REQUIRED');
  const proof = read(path.join(__dirname, '../packaged-bfix-parity-recheck-20261013.json'));
  assert(proof.ok === true && Object.entries(proof.code_sha256).every(([f,h]) => sha(path.join(root,f)) === h), 'SOURCE_CHANGED_AFTER_BFIX_PARITY');
}
async function observe() {
  const verified = await readVerifiedReadyHost(client, paths, loadRecoveryDescriptor, 3, { allowAdmissionBlocked: true });
  assert(verified && descriptorMatchesInstallation(verified.descriptor, paths.runtimeIdentity()), 'EXACT_BFIX_HOST_REQUIRED');
  const descriptor = verified.descriptor;
  assert(sameProcessIdentity(processIdentityFrom(descriptor), await observeLifecycleProcessIdentity(descriptor.owner_pid)), 'BFIX_PROCESS_IDENTITY_CHANGED');
  const opts = descriptorRequestOptions(descriptor);
  const status = await client.status({ ...opts, fresh: true });
  const runtime = await client.call('runtime.lightweight_snapshot', [], opts);
  const epoch = await client.call('runtime.activation_epoch_status', [], opts);
  report.owner = pick(descriptor, identityKeys);
  report.host = pick(status, ['pid','instance_id','process_start_token','state','full_clean_activation','activation_epoch','code_revision','ready_adoption','recovery_bootstrap','activation_closure','loaded_source_receipts','auto_activation','electron_ui_recovery','runtime']);
  const { normalizedRuntimeStatus } = require(path.join(root, 'control-plane/control_plane/recovery_identity_observer.cjs'));
  report.node_runtime_projection = normalizedRuntimeStatus(descriptor, status);
  report.identity_observation = await client.call('runtime.identity_observation', [], opts);
  report.runtime = pick(runtime, ['fullyReady','mcpRunning','nativeAlive','nativePid','centralConnected','authorityReady','componentsReady','updateIncomplete','connectorContractState','codeRevision','activationClosure','activationEpoch','device']);
  report.epoch = epoch;
  return { descriptor, opts, status, runtime, epoch };
}
async function main() {
  assert(['status','refresh','complete','activation-preflight','activate'].includes(mode), 'UNSUPPORTED_BFIX_OPERATION');
  packageProof();
  const current = await observe();
  if (mode === 'status') return;
  const selected = await selectTrustedRecoveryHostSource(root);
  report.source_checkpoint = selected.source_checkpoint;
  if (['refresh','activate'].includes(mode)) {
    const fenceFile = process.argv[3];
    assert(path.isAbsolute(fenceFile || '') && path.dirname(fenceFile).toLowerCase() === path.resolve(__dirname, '..').toLowerCase(), 'EXACT_SERVER_RECEIPT_DIRECTORY_REQUIRED');
    const fence = read(fenceFile); const age = Date.now() - fence.capture_completed_at_ms;
    assert(fence.ok === true && age >= 0 && age < 120000 && fence.service_stable === true && fence.sqlite_integrity_ok === true && fence.source_startup_disk_attestation_matches === true, 'FRESH_SERVER_FENCE_REQUIRED');
    assert(['live_open_tasks','live_writers','queued_actions','active_dispatch_actions'].every(k => fence.whole_device_census?.[k] === 0), 'SERVER_LIVE_WORK_PRESENT');
    const census = await canonicalLedgerCensus({ paths, workspace: root, allowAcceptancePending: true });
    assert(census.safe === true && census.lifecycle.unexplained_active_runs === 0 && census.lifecycle.unbound_live_resource_residues === 0, 'LOCAL_IDLE_CENSUS_REQUIRED');
    assert(['active_tool_calls','active_commands','starting_commands','active_background_operations','active_managed_processes','foreign_heavy_processes','active_agent_lanes','owned_codex_sidecar_residues'].every(k => census.counts[k] === 0), 'LOCAL_LIVE_WORK_PRESENT');
    report.fence = { path: fenceFile, sha256: sha(fenceFile), capture_completed_at_ms: fence.capture_completed_at_ms, preserved_unknowns: fence.historical_unknown_actions_preserved.map(x => pick(x,['action_id','delivery_state','disposition'])) };
    report.census = { safe: census.safe, counts: census.counts };
  }
  if (mode === 'refresh') {
    assert(current.runtime.mcpRunning === false && current.runtime.nativeAlive === false && current.status.electron_ui_recovery?.alive === false && current.status.electron_ui_recovery?.suppressed === true, 'STOPPED_SUPPRESSED_RUNTIME_REQUIRED');
    const intent = path.join(__dirname,'bfix-full-clean-refresh-intent.json');
    assert(!fs.existsSync(intent), 'REFRESH_ALREADY_ATTEMPTED_OBSERVE_ONLY');
    report.operation_id = `bfix-refresh-${Date.now().toString(36)}-${crypto.randomBytes(8).toString('hex')}`;
    fs.writeFileSync(intent, JSON.stringify({ ...report, no_replay: true },null,2)+'\n',{flag:'wx'});
    report.mutation_started = true;
    const result = await client.restart({ refresh: true, mode: 'full_clean_refresh', operationId: report.operation_id, allowAcceptancePending: true, reason: 'operator_bfix_packaged_installation_refresh' }, { ...current.opts, timeout: 55000 });
    report.result = pick(result,['operation_id','activation_epoch_id','accepted','state','activation_state','admission_open','fully_ready','status','activationEpoch']);
    return;
  }
  if (mode === 'complete') {
    assert(!['READY','FAILED'].includes(current.epoch.state), 'ACTIVE_EPOCH_REQUIRED');
    report.mutation_started = true;
    const result = await client.call('runtime.complete_activation_epoch',[current.epoch.activation_epoch_id],{...current.opts,timeout:55000});
    report.result = result;
    return;
  }
  const revision = current.status.code_revision;
  assert(revision?.state === 'current' && revision.running_revision === revision.disk_revision, 'CURRENT_PACKAGED_REVISION_REQUIRED');
  const request = { operation_id: `bfix-source-${Date.now().toString(36)}-${crypto.randomBytes(8).toString('hex')}`, component:'recovery_host', expected_disk_revision:revision.disk_revision, requested_at_unix_ms:Date.now(), expires_at_unix_ms:Date.now()+55000, allow_acceptance_pending:true, source_checkpoint:selected.source_checkpoint, full_clean_required:true, activation_mode:'full_clean_activation' };
  report.request = request;
  const preflight = await client.call('code.activation_preflight',[request],{...current.opts,timeout:55000});
  report.preflight = preflight;
  if (preflight.safe !== true) { const error = new Error(preflight.code || 'SOURCE_ACTIVATION_PREFLIGHT_REFUSED'); error.code = preflight.code || 'SOURCE_ACTIVATION_PREFLIGHT_REFUSED'; error.details = preflight; throw error; }
  if (mode === 'activation-preflight') return;
  const intent = path.join(__dirname,'bfix-source-activation-intent.json');
  assert(!fs.existsSync(intent), 'SOURCE_ACTIVATION_ALREADY_ATTEMPTED_OBSERVE_ONLY');
  fs.writeFileSync(intent,JSON.stringify({...report,no_replay:true},null,2)+'\n',{flag:'wx'});
  report.mutation_started = true;
  report.result = await client.call('code.activate_update',[request],{...current.opts,timeout:55000});
}
main().then(()=>{report.ok=true; fs.writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n',{flag:'wx'}); console.log(JSON.stringify({ok:true,mode,report:reportPath,mutation_started:report.mutation_started,operation_id:report.operation_id,state:report.epoch?.state,fully_ready:report.host?.runtime?.fully_ready,strict_ready:report.node_runtime_projection?.strict_ready,identity_current:report.identity_observation?.identity_current,result_state:report.result?.state}));}).catch(error=>{report.ok=false; report.error={code:error.code||'BFIX_OPERATOR_FAILED',message:String(error.message||error),details:error.details||null}; fs.writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n',{flag:'wx'}); console.error(JSON.stringify({ok:false,mode,report:reportPath,mutation_started:report.mutation_started,...report.error}));process.exitCode=1;});
