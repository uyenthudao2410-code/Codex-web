'use strict';

// Run with the verified candidate Electron executable and ELECTRON_RUN_AS_NODE=1.
// Arguments: <candidate win-unpacked directory> <exact current activation epoch>.
// This observer never requests activation, policy changes, process stop, or cleanup.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { execFile } = require('node:child_process');
const { promisify } = require('node:util');
const execFileAsync = promisify(execFile);
const originalFs = require('original-fs');

const root = 'E:\\DEV\\Codex-web';
const expectedEpochId = String(process.argv[3] || '');
let candidate = null;
let stage = 'arguments';
const sha256 = (file) => crypto.createHash('sha256').update(originalFs.readFileSync(file)).digest('hex');
function requireState(condition, code) {
  if (!condition) throw Object.assign(new Error(code), { code });
}
function pick(value, names) {
  return Object.fromEntries(names.filter((name) => value?.[name] !== undefined)
    .map((name) => [name, value[name]]));
}

async function main() {
  requireState(/^activation-[A-Za-z0-9_-]+$/.test(expectedEpochId)
    && expectedEpochId !== 'activation-mv4xk8xx-3d9f30b9b0542ef0458f3c3b241d365a', 'NEW_EXACT_R8_ACTIVATION_EPOCH_REQUIRED');
  stage = 'candidate_path';
  candidate = fs.realpathSync(path.resolve(process.argv[2] || ''));
  requireState(candidate.toLowerCase().startsWith(path.join(root, 'dist').toLowerCase() + path.sep),
    'CANDIDATE_OUTSIDE_WORKSPACE');
  const executable = path.join(candidate, 'Coding Tools MCP.exe');
  const appRoot = path.join(candidate, 'resources', 'app.asar');
  stage = 'selected_executable';
  requireState(fs.realpathSync(process.execPath).toLowerCase() === fs.realpathSync(executable).toLowerCase(),
    'SELECTED_ELECTRON_EXECUTABLE_REQUIRED');
  stage = 'package_proof';
  const packagedProof = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'r9-candidate-verification.json'), 'utf8'));
  stage = 'package_hashes';
  requireState(packagedProof.ok === true && packagedProof.candidate.toLowerCase() === candidate.toLowerCase()
    && sha256(appRoot) === packagedProof.app_asar_sha256
    && sha256(executable) === packagedProof.executable_sha256
    && sha256(path.join(candidate, 'resources', 'resources', 'coding-tools-mcp', 'coding_tools_mcp', 'windows_mxc_state_aware.py'))
      === packagedProof.packaged_adapter_sha256, 'EXACT_VERIFIED_R8_PACKAGE_REQUIRED');
  requireState(process.env.APPDATA && path.isAbsolute(process.env.APPDATA), 'APPDATA_REQUIRED');

  stage = 'packaged_service_load';
  const load = (name) => require(path.join(appRoot, 'electron', 'services', name));
  const { RuntimePaths } = load('runtimePaths');
  const { RecoveryIpcClient, loadRecoveryDescriptor } = load('recoveryIpc');
  const { descriptorMatchesInstallation, descriptorRequestOptions, readVerifiedReadyHost } = load('recoveryHostLauncher');
  const { ActivationEpochStore } = load('activationEpoch');
  const { canonicalLedgerCensus, executionProfileForRecord } = load('fullCleanActivation');
  const paths = new RuntimePaths({
    dataRoot: path.join(process.env.APPDATA, 'web-mcp-assistant'), appRoot,
    resourcesRoot: path.join(candidate, 'resources', 'resources'),
    executablePath: executable, runtimeMode: 'packaged'
  });
  const client = new RecoveryIpcClient({ paths });
  stage = 'verified_ready_host';
  const verified = await readVerifiedReadyHost(client, paths, loadRecoveryDescriptor, 2);
  requireState(verified && descriptorMatchesInstallation(verified.descriptor, paths.runtimeIdentity()),
    'SELECTED_PACKAGED_READY_HOST_NOT_VERIFIED');
  const requestOptions = descriptorRequestOptions(verified.descriptor);
  const exactCall = (action, args = []) => client.call(action, args, requestOptions);
  const epochStore = new ActivationEpochStore({ paths });
  const readCurrent = () => {
    const epoch = epochStore.current();
    requireState(epoch?.activation_epoch_id === expectedEpochId
      && epoch.state === 'READY' && epoch.admission_state === 'OPEN', 'CURRENT_READY_EPOCH_CHANGED');
    const profile = executionProfileForRecord(epoch);
    requireState(profile.executionRole === 'central_executor'
      && profile.componentProfile === 'central_executor_v1', 'EXACT_CENTRAL_PROFILE_REQUIRED');
    requireState(epoch.verification?.final_census?.pass === true
      && epoch.verification.final_census.projection_rebuild_verified === true, 'DURABLE_FINAL_CENSUS_NOT_VERIFIED');
    return epoch;
  };
  stage = 'durable_current_epoch';
  const beforeEpoch = readCurrent();
  stage = 'lightweight_runtime';
  const runtime = await exactCall('runtime.lightweight_snapshot');
  requireState(runtime?.fullyReady === true && runtime.mcpRunning === true
    && runtime.executionRole === 'central_executor' && runtime.centralConnected === true
    && runtime.authorityReady === true && runtime.updateIncomplete === false
    && runtime.activationEpoch?.activation_epoch_id === expectedEpochId
    && runtime.activationEpoch.admission_open === true
    && runtime.toolContract?.profile === 'smart-v3', 'CURRENT_RUNTIME_NOT_READY');
  stage = 'fresh_recovery_status';
  const recovery = await exactCall('recovery.status', [{ fresh: true }]);
  requireState(recovery?.pid === verified.descriptor.owner_pid
    && recovery.instance_id === verified.descriptor.instance_id
    && recovery.activation_epoch?.activation_epoch_id === expectedEpochId
    && recovery.activation_epoch.admission_open === true
    && recovery.code_revision?.state === 'current'
    && recovery.code_revision.running_revision === recovery.code_revision.disk_revision,
  'EXACT_CURRENT_HOST_STATUS_REQUIRED');

  // The existing census option allows preserved historical awaiting-acceptance
  // records. It does not settle them or remove live-work/residue blockers.
  stage = 'canonical_ledger_census';
  const census = await canonicalLedgerCensus({ paths, workspace: root, allowAcceptancePending: true });
  requireState(census.content_free === true && census.mutated_canonical_ledger === false
    && census.snapshot?.backup_api_copy === true && census.snapshot.immutable === true
    && census.snapshot.query_only === true
    && JSON.stringify(census.snapshot.integrity_check) === '["ok"]'
    && census.snapshot.foreign_key_check_rows === 0, 'READ_ONLY_CANONICAL_CENSUS_INVALID');
  stage = 'post_census_epoch';
  const afterEpoch = readCurrent();
  requireState(afterEpoch.ready_commit_digest === beforeEpoch.ready_commit_digest,
    'CURRENT_READY_COMMIT_CHANGED');
  const activation = await exactCall('runtime.activation_epoch_status');
  requireState(activation?.activation_epoch_id === expectedEpochId
    && activation.state === 'READY' && activation.admission_open === true, 'CURRENT_IPC_EPOCH_CHANGED');
  await exactCall('recovery.ping');
  const currentDescriptor = loadRecoveryDescriptor(paths);
  requireState(currentDescriptor.owner_pid === verified.descriptor.owner_pid
    && currentDescriptor.instance_id === verified.descriptor.instance_id
    && currentDescriptor.owner_process_start_token === verified.descriptor.owner_process_start_token
    && currentDescriptor.installation_id === verified.descriptor.installation_id,
  'CURRENT_HOST_DESCRIPTOR_CHANGED');
  stage = 'native_os_observation';
  const nativeObservation = await execFileAsync('powershell.exe', [
    '-NoProfile', '-NonInteractive', '-Command',
    "@(Get-Process -Name 'vmmemWSB','WindowsSandboxServer','WindowsSandboxClient','wxc-windows-sandbox-daemon','wxc-exec' -ErrorAction SilentlyContinue | Select-Object Id,ProcessName) | ConvertTo-Json -Compress"
  ], { windowsHide: true, timeout: 10_000, maxBuffer: 64 * 1024 });
  const nativeRaw = JSON.parse(nativeObservation.stdout.trim() || '[]');
  const nativeProcesses = (Array.isArray(nativeRaw) ? nativeRaw : [nativeRaw])
    .map((item) => ({ pid: item.Id, name: item.ProcessName }));
  stage = 'final_epoch_and_owner';
  requireState(readCurrent().ready_commit_digest === beforeEpoch.ready_commit_digest, 'CURRENT_READY_COMMIT_CHANGED');
  await exactCall('recovery.ping');

  const ledgerIdle = Array.isArray(census.lifecycle?.blockers)
    && census.lifecycle.blockers.every((reason) => reason === 'live_runtime_state_process')
    && census.lifecycle.unexplained_active_runs === 0
    && census.lifecycle.unbound_live_resource_residues === 0
    && census.lifecycle.live_owned_runs.length === 0
    && ['active_tool_calls', 'active_commands', 'starting_commands', 'active_background_operations',
      'active_managed_processes', 'foreign_heavy_processes', 'active_agent_lanes', 'owned_codex_sidecar_residues']
      .every((name) => census.counts[name] === 0);
  const report = {
    operation: 'observe_final_machine', observed_at: new Date().toISOString(), candidate,
    ok: ledgerIdle, read_only: true, target_activation_epoch_id: expectedEpochId,
    package: { app_asar_sha256: packagedProof.app_asar_sha256, executable_sha256: packagedProof.executable_sha256 },
    installation_id: paths.runtimeIdentity().installation_id,
    host: pick(recovery, ['pid', 'instance_id', 'state', 'gateway', 'code_revision',
      'full_clean_activation', 'electron_ui_revision', 'electron_ui_recovery', 'recovery_plane_mode', 'runtime']),
    runtime: pick(runtime, ['fullyReady', 'mcpRunning', 'nativeAlive', 'executionRole',
      'authorityReady', 'centralConnected', 'centralStatusReason', 'updateIncomplete', 'toolContract', 'codeRevision']),
    epoch: pick(afterEpoch, ['activation_epoch_id', 'operation_id', 'state', 'admission_state',
      'ready_commit_digest', 'created_at', 'updated_at']),
    final_census_predicates: Object.fromEntries(Object.entries(afterEpoch.verification.final_census)
      .filter(([, value]) => typeof value === 'boolean')),
    canonical_ledger_census: census,
    native_idle_counts: census.counts,
    native_os_observation: {
      observed_at: new Date().toISOString(), ownership_not_inferred: true,
      live_process_count: nativeProcesses.length, live_processes: nativeProcesses
    },
    actual_ui_details: recovery.electron_ui_recovery,
    ledger_idle: ledgerIdle, historical_acceptance_preserved: true,
    descriptor_stable: true, epoch_stable: true
  };
  stage = 'report_write';
  const output = path.join(__dirname, `final-machine-observation-${expectedEpochId}-${Date.now()}.json`);
  fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  process.stdout.write(JSON.stringify({ ...report, report_path: output }) + '\n',
    () => process.exit(report.ok ? 0 : 2));
}

main().catch((error) => {
  process.stderr.write(JSON.stringify({ operation: 'observe_final_machine', observed_at: new Date().toISOString(),
    candidate, ok: false, read_only: true, target_activation_epoch_id: expectedEpochId,
    stage, code: error?.code || 'OBSERVATION_FAILED' }) + '\n', () => process.exit(1));
});
