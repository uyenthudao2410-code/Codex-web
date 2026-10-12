'use strict';
// Root alone executes supported read-only IPC/census. No dispatch or acceptance.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const {spawnSync} = require('node:child_process');
const repo = 'E:\\Github\\Tools-Codex-web';
const services = path.join(repo, 'electron/services');
const {createRuntimePaths} = require(path.join(services, 'runtimePaths'));
const {RecoveryIpcClient} = require(path.join(services, 'recoveryIpc'));
const {descriptorRequestOptions, descriptorMatchesInstallation} = require(path.join(services, 'recoveryHostLauncher'));
const {observeLifecycleProcessIdentity, sameProcessIdentity} = require(path.join(services, 'processIdentity'));
const {canonicalLedgerCensus} = require(path.join(services, 'fullCleanActivation'));
const candidate = path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-policy-contract-1012-r12/win-unpacked');
const dataRoot = 'C:\\Users\\daoth\\AppData\\Roaming\\web-mcp-assistant';
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const need = (ok, code) => {if (!ok) throw Object.assign(new Error(), {code});};
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
function sandboxProcessCensus() {
  const ps = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe';
  const script = "$ErrorActionPreference='Stop'; $n=@('WindowsSandbox','WindowsSandboxClient','WindowsSandboxServer','WindowsSandboxRemoteSession','vmmemWindowsSandbox'); @{host_count=@(Get-Process | Where-Object {$n -contains $_.ProcessName}).Count;backend_count=@(Get-CimInstance Win32_Process -Filter \"Name='wxc-windows-sandbox-daemon.exe' OR Name='wxc-exec.exe' OR Name='wxc-windows-sandbox-guest.exe'\").Count;content_free=$true} | ConvertTo-Json -Compress";
  const result = spawnSync(ps,['-NoProfile','-NonInteractive','-Command',script],{env:{...process.env,PSModulePath:path.join(path.dirname(ps),'Modules')},windowsHide:true,shell:false,timeout:15000,encoding:'utf8',maxBuffer:16384});
  need(!result.error && result.status === 0, 'SANDBOX_PROCESS_CENSUS_UNAVAILABLE');
  const value = JSON.parse(result.stdout.replace(/^\uFEFF/,'').trim());
  need(value.content_free === true && value.host_count === 0 && value.backend_count === 0, 'SANDBOX_OR_BACKEND_PROCESS_PRESENT');
  return {...value,observed_at_ms:Date.now(),basis:'windows_sandbox_host_and_wxc_backend_process_census',physical_hcs_inventory_claimed:false};
}
function localRead(paths) {
  const result = spawnSync(paths.portablePython(), ['-B','-I',path.join(__dirname,'native-no-effect-local.py')], {shell:false,windowsHide:true,encoding:'utf8',timeout:15000,maxBuffer:65536});
  need(!result.error && result.status === 0, 'LOCAL_NO_EFFECT_COLLECTOR_REFUSED');
  const receipt = JSON.parse(result.stdout);
  need(receipt.ok === true && receipt.kind === 'r12_query_only_native_no_effect_local' && receipt.external_mutation === false
    && receipt.mutated_canonical_ledger === false && receipt.replay_forbidden === true, 'LOCAL_NO_EFFECT_RECEIPT_INVALID');
  return receipt;
}
function samePinnedIdentity(identity, pins) {
  return identity.observation_kind === 'mcp_identity_read_only' && identity.observation_schema_version === 1
    && identity.identity_current === true && identity.activation_epoch_id === pins.activation_epoch
    && identity.current_activation_epoch_id === pins.activation_epoch
    && identity.mcp_process_instance_id === pins.runtime_instance_id
    && identity.mcp_server_instance_id === pins.mcp_server_instance_id
    && identity.tool_contract_sha256 === pins.native_tool_contract_sha256;
}
async function main() {
  need(process.argv.includes('--execute-read-only'), 'EXPLICIT_ROOT_READ_ONLY_EXECUTION_REQUIRED');
  const paths = createRuntimePaths({dataRoot,appRoot:path.join(candidate,'resources/app.asar'),resourcesRoot:path.join(candidate,'resources/resources'),runtimeMode:'packaged',executablePath:path.join(candidate,'Coding Tools MCP.exe')});
  const descriptor = read(paths.recoveryHostDescriptorFile());
  need(descriptorMatchesInstallation(descriptor, paths.runtimeIdentity()), 'R12_INSTALLATION_REQUIRED');
  const owner = await observeLifecycleProcessIdentity(descriptor.owner_pid);
  need(owner.state === 'live' && sameProcessIdentity({pid:descriptor.owner_pid,process_start_token:descriptor.owner_process_start_token},owner), 'HOST_IDENTITY_CHANGED');
  const before = localRead(paths), pins = before.native_identity_pins;
  const vmBefore = sandboxProcessCensus();
  const client = new RecoveryIpcClient({paths}), options = descriptorRequestOptions(descriptor);
  const identity = await client.call('runtime.identity_observation', [], options);
  need(samePinnedIdentity(identity,pins), 'EXACT_R12_NATIVE_IDENTITY_CHANGED');
  const census = await canonicalLedgerCensus({paths,workspace:repo,allowAcceptancePending:true,pythonStatusFn:async()=>({installed:true,command:paths.portablePython(),prefixArgs:['-B']})});
  const keys = ['active_tool_calls','active_commands','starting_commands','active_background_operations','active_managed_processes','foreign_heavy_processes','active_agent_lanes'];
  need(census.mutated_canonical_ledger === false && keys.every(key=>census.counts[key]===0)
    && census.snapshot?.query_only === true && census.snapshot?.immutable === true
    && census.snapshot?.integrity_check?.length === 1 && census.snapshot.integrity_check[0] === 'ok'
    && census.snapshot?.foreign_key_check_rows === 0 && census.lifecycle?.unexplained_active_runs === 0
    && census.lifecycle?.unbound_live_resource_residues === 0 && census.lifecycle?.projection_drift === false
    && (census.lifecycle?.blockers || []).every(code=>code==='live_runtime_state_process'), 'CANONICAL_CENSUS_NOT_QUIESCENT');
  const afterIdentity = await client.call('runtime.identity_observation', [], options);
  need(samePinnedIdentity(afterIdentity,pins), 'NATIVE_IDENTITY_CHANGED_DURING_RECONCILIATION');
  const after = localRead(paths);
  const vmAfter = sandboxProcessCensus();
  need(after.pins_sha256 === before.pins_sha256 && after.journal.sha256 === before.journal.sha256
    && after.native_failure.row_sha256 === before.native_failure.row_sha256
    && JSON.stringify(after.ledger.protected_records) === JSON.stringify(before.ledger.protected_records)
    && after.ledger.snapshot.events_max_seq === before.ledger.snapshot.events_max_seq, 'EVIDENCE_CHANGED_DURING_RECONCILIATION');
  const observed = Date.now();
  const receipt = {...after,kind:'r12_query_only_native_no_effect_reconciliation',observed_at_ms:observed,
    observed_at_utc:new Date(observed).toISOString(),active_census_required:false,
    authenticated_identity_observation:true,attestation_claimed:false,
    census:{counts:Object.fromEntries(keys.map(key=>[key,census.counts[key]])),snapshot:census.snapshot,
      blockers:census.lifecycle.blockers,unexplained_active_runs:0,unbound_live_resource_residues:0,projection_drift:false,mutated_canonical_ledger:false},
    active_work_quiescent:true,
    code:'WORKTREE_STATUS_TOO_LARGE',category:'validation',pre_effect:true,
    pre_effect_basis:['unique_exact_native_validation_failure_before_RUN_creation','target_and_checker_exact_preimage','zero_RUN_WAVE_Job_proof_and_events_since_dispatch_window','canonical_work_census_quiescent'],
    target_preimage_sha256:after.files['tests/fixtures/initial-proof-canary-target.cjs'],
    checker_sha256:after.files['tests/fixtures/initial-proof-canary-check.cjs'],
    no_new_runs:true,no_new_jobs:true,no_new_proof:true,no_active_work:true,
    zero_vm:true,zero_vm_basis:'no_matching_windows_sandbox_host_or_wxc_backend_processes',
    vm_process_census:{before:vmBefore,after:vmAfter},hcs_inventory_status:'not_observed_by_this_helper',physical_hcs_inventory_claimed:false,
    old_run_sha256:after.ledger.protected_records.runs.sha256,old_wave_sha256:after.ledger.protected_records.waves.sha256,
    native_identity:{activation_epoch_id:identity.activation_epoch_id,process_instance_id:identity.mcp_process_instance_id,
      server_instance_id:identity.mcp_server_instance_id,tool_contract_sha256:identity.tool_contract_sha256},
    performance_evidence_sha256:after.native_failure.row_sha256,performance_snapshot_sha256:after.native_failure.performance_sha256,
    helper_sha256:sha(fs.readFileSync(__filename)),local_helper_sha256:sha(fs.readFileSync(path.join(__dirname,'native-no-effect-local.py')))};
  const file = path.join(__dirname,'native-no-effect-'+observed+'.json');
  fs.writeFileSync(file,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
  process.stdout.write(JSON.stringify({ok:true,kind:receipt.kind,action_id:receipt.action_id,attempt_id:receipt.attempt_id,
    no_native_patch_effect_observed:true,active_work_quiescent:true,receipt_path:file,receipt_sha256:sha(fs.readFileSync(file)),
    attestation_claimed:false,acceptance_performed:false,receipt_terminalized:false,replay_forbidden:true,external_mutation:false,secret_values_emitted:false})+'\n');
}
if (require.main === module) main().catch(error=>{process.stdout.write(JSON.stringify({ok:false,code:error.code||'ROOT_NATIVE_NO_EFFECT_CENSUS_REFUSED',replay_forbidden:true,external_mutation:false,secret_values_emitted:false})+'\n');process.exitCode=2;});
