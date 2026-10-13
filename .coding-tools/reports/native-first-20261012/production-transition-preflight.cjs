'use strict';
// Exact current r9e installation observer. No stop, activation, policy, task,
// shortcut, supervisor, or service mutation is exposed by this helper.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const originalFs = require('original-fs');
const { execFile } = require('node:child_process');
const { promisify } = require('node:util');
const execFileAsync = promisify(execFile);

const root = 'E:\\DEV\\Codex-web';
const candidate = path.join(root, 'dist', 'windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9e', 'win-unpacked');
const executable = path.join(candidate, 'Coding Tools MCP.exe');
const appRoot = path.join(candidate, 'resources', 'app.asar');
const dataRoot = path.join(process.env.APPDATA || '', 'web-mcp-assistant');
const oldProofPath = path.join(root, '.coding-tools', 'reports', 'workspace-display-20261012-r10', 'r9e-candidate-verification.json');
const expectedOwner = {
  owner_pid: 38436,
  owner_process_start_token: '134362736855547600',
  instance_id: 'b81bbad41b65c71f1bb4f21b0bdb8d10',
  installation_id: '2e511714fe3f1f64484f11778e1fe2a5c46bb5d5873f02047144b417f7996d0a'
};
const preservedWorkspace = {
  workspace_id: 'workspace_bc86004be2684b958ab7a9a6f9530cd7',
  workspace_generation: 'generation_03f9c04f1b14414fa4bfa7d91cc8ea7a',
  workspace_path: 'E:\\DEV\\Autocad'
};
const pick = (value, names) => Object.fromEntries(names.filter(name => value?.[name] !== undefined).map(name => [name, value[name]]));
const requireState = (condition, code) => { if (!condition) throw Object.assign(new Error(code), { code }); };
const hash = file => crypto.createHash('sha256').update(originalFs.readFileSync(file)).digest('hex');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const fileObservation = file => {
  if (!fs.existsSync(file)) return { present: false };
  requireState(fs.statSync(file).isFile() && fs.statSync(file).size <= 256 * 1024, 'BOUNDED_PRESERVED_STATE_REQUIRED');
  return { present: true, sha256: hash(file), bytes: fs.statSync(file).size };
};
const preservedFiles = ['control-plane-workspaces.json', 'control-plane-node.json',
  'control-plane-read-only-policy.json', 'control-plane-file-read-policy.json',
  'control-plane-approved-patch-policy.json', 'control-plane-document-write-policy.json',
  'control-plane-exec-policy.json'];
const observePreserved = () => Object.fromEntries(preservedFiles.map(name => [name, fileObservation(path.join(dataRoot, name))]));
let stage = 'package';

async function main() {
  requireState(path.isAbsolute(dataRoot) && process.env.APPDATA, 'APPDATA_REQUIRED');
  requireState(fs.realpathSync(process.execPath).toLowerCase() === fs.realpathSync(executable).toLowerCase(), 'EXACT_R9E_EXECUTABLE_REQUIRED');
  const proof = read(oldProofPath);
  requireState(proof.ok === true && proof.candidate.toLowerCase() === candidate.toLowerCase()
    && hash(executable) === proof.executable_sha256 && hash(appRoot) === proof.app_asar_sha256
    && hash(path.join(candidate, 'resources/resources/coding-tools-mcp/coding_tools_mcp/windows_mxc_state_aware.py')) === proof.packaged_adapter_sha256,
  'EXACT_R9E_PACKAGE_PROOF_REQUIRED');
  const load = name => require(path.join(appRoot, 'electron/services', name));
  const { RuntimePaths } = load('runtimePaths');
  const { RecoveryIpcClient, loadRecoveryDescriptor } = load('recoveryIpc');
  const { descriptorMatchesInstallation, descriptorRequestOptions, readVerifiedReadyHost } = load('recoveryHostLauncher');
  const { canonicalLedgerCensus } = load('fullCleanActivation');
  const paths = new RuntimePaths({ dataRoot, appRoot, resourcesRoot: path.join(candidate, 'resources/resources'), executablePath: executable, runtimeMode: 'packaged' });
  const client = new RecoveryIpcClient({ paths });
  stage = 'exact_host';
  const verified = await readVerifiedReadyHost(client, paths, loadRecoveryDescriptor, 2, { allowAdmissionBlocked: true });
  requireState(verified && descriptorMatchesInstallation(verified.descriptor, paths.runtimeIdentity())
    && Object.entries(expectedOwner).every(([name, value]) => verified.descriptor[name] === value), 'EXPECTED_CURRENT_R9E_HOST_CHANGED');
  const exact = (action, args = []) => client.call(action, args, descriptorRequestOptions(verified.descriptor));
  const beforePreserved = observePreserved();
  const settings = read(paths.settingsFile());
  stage = 'current_runtime';
  const observedGitHead = (await execFileAsync('git', ['-C', root, 'rev-parse', 'HEAD'], { windowsHide: true, timeout: 10000 })).stdout.trim();
  const runtime = await exact('runtime.lightweight_snapshot');
  const activation = await exact('runtime.activation_epoch_status');
  const recovery = await exact('recovery.status', [{ fresh: true }]);
  requireState(recovery.pid === expectedOwner.owner_pid && recovery.instance_id === expectedOwner.instance_id, 'CURRENT_RECOVERY_STATUS_IDENTITY_MISMATCH');
  stage = 'canonical_ledger_census';
  const census = await canonicalLedgerCensus({ paths, workspace: root, allowAcceptancePending: true });
  requireState(census.content_free === true && census.mutated_canonical_ledger === false
    && census.snapshot?.backup_api_copy === true && census.snapshot.immutable === true
    && census.snapshot.query_only === true && JSON.stringify(census.snapshot.integrity_check) === '["ok"]'
    && census.snapshot.foreign_key_check_rows === 0, 'READ_ONLY_CANONICAL_CENSUS_REQUIRED');
  const zeroCounts = ['active_tool_calls', 'active_commands', 'starting_commands', 'active_background_operations',
    'active_managed_processes', 'foreign_heavy_processes', 'active_agent_lanes', 'owned_codex_sidecar_residues'];
  const idle = Array.isArray(census.lifecycle?.blockers)
    && census.lifecycle.blockers.every(reason => reason === 'live_runtime_state_process')
    && census.lifecycle.unexplained_active_runs === 0 && census.lifecycle.unbound_live_resource_residues === 0
    && zeroCounts.every(name => census.counts[name] === 0);
  stage = 'os_process_observation';
  const native = await execFileAsync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command',
    "@(Get-Process -Name 'WindowsSandbox*','vmmemWSB','wxc-windows-sandbox-daemon','wxc-exec' -ErrorAction SilentlyContinue | Select-Object Id,ProcessName) | ConvertTo-Json -Compress"],
  { windowsHide: true, timeout: 10000, maxBuffer: 65536 });
  const nativeRaw = JSON.parse(native.stdout.trim() || '[]');
  const nativeProcesses = (Array.isArray(nativeRaw) ? nativeRaw : [nativeRaw]).map(value => ({ pid: value.Id, name: value.ProcessName }));
  stage = 'final_identity';
  await exact('recovery.ping');
  const afterDescriptor = loadRecoveryDescriptor(paths);
  const afterEpoch = await exact('runtime.activation_epoch_status');
  const afterPreserved = observePreserved();
  const descriptorStable = Object.entries(expectedOwner).every(([name, value]) => afterDescriptor[name] === value);
  const epochStable = afterEpoch.activation_epoch_id === activation.activation_epoch_id
    && afterEpoch.state === activation.state && afterEpoch.admission_open === activation.admission_open;
  const preservedStable = JSON.stringify(beforePreserved) === JSON.stringify(afterPreserved);
  requireState(descriptorStable && epochStable && preservedStable, 'PRODUCTION_IDENTITY_OR_POLICY_CHANGED_DURING_OBSERVATION');
  const registry = read(paths.controlPlaneWorkspaceRegistryFile());
  const entries = Array.isArray(registry.entries) ? registry.entries : [];
  const preservedEntries = entries.filter(entry => entry.workspace_id === preservedWorkspace.workspace_id
    && entry.workspace_generation === preservedWorkspace.workspace_generation);
  requireState(preservedEntries.length === 1
    && path.resolve(preservedEntries[0].canonical_path || '').toLowerCase() === path.resolve(preservedWorkspace.workspace_path).toLowerCase(),
  'PRESERVED_AUTOCAD_REGISTRATION_CHANGED');
  const report = {
    schema_version: 1, operation: 'production_transition_preflight', read_only: true,
    observed_git_head: observedGitHead,
    observed_at: new Date().toISOString(), observed_at_ms: Date.now(),
    current_candidate: candidate, current_package_sha256: { executable: proof.executable_sha256, app_asar: proof.app_asar_sha256 },
    production_identity: expectedOwner,
    runtime: pick(runtime, ['fullyReady', 'mcpRunning', 'nativeAlive', 'nativePid', 'executionRole', 'centralConnected',
      'authorityReady', 'centralStatusReason', 'updateIncomplete', 'toolContract', 'codeRevision']),
    activation: pick(afterEpoch, ['activation_epoch_id', 'state', 'admission_open', 'admission_state', 'operation_id']),
    recovery: pick(recovery, ['pid', 'instance_id', 'code_revision', 'electron_ui_revision', 'electron_ui_recovery', 'recovery_plane_mode']),
    canonical_ledger_census: census,
    local_live_work_idle: idle,
    windows_sandbox_os_observation: { ownership_not_inferred: true, processes: nativeProcesses },
    preserved_workspace_expectation: preservedWorkspace,
    preserved_workspace_registry_entries: preservedEntries.map(value => pick(value, ['workspace_id', 'workspace_generation', 'canonical_path', 'capabilities'])),
    settings_scope: pick(settings, ['workspace', 'authorizedRoots', 'executionRole']),
    preserved_policy_fingerprints: beforePreserved,
    preserved_policy_files_stable: preservedStable, descriptor_stable: descriptorStable, epoch_stable: epochStable,
    central_server_census: 'required freshly from authenticated read-only server before any stop; not inferred from local authorityReady',
    activation_eligibility: 'pending final candidate exact source parity, packaged smoke and fresh authenticated device/server idle receipt with supported UNKNOWN action reconciliation',
    mutating_actions_performed: [], task_or_policy_changes: false,
    ok: true
  };
  report.report_path = path.join(__dirname, `production-transition-preflight-${Date.now()}.json`);
  fs.writeFileSync(report.report_path, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  process.stdout.write(JSON.stringify(pick(report, ['ok', 'operation', 'report_path', 'production_identity', 'activation',
    'local_live_work_idle', 'descriptor_stable', 'epoch_stable', 'preserved_policy_files_stable', 'activation_eligibility'])) + '\n', () => process.exit(0));
}

main().catch(error => {
  const report = { schema_version: 1, operation: 'production_transition_preflight', observed_at: new Date().toISOString(),
    ok: false, read_only: true, stage, code: error?.code || 'PREFLIGHT_OBSERVATION_FAILED', mutating_actions_performed: [] };
  report.report_path = path.join(__dirname, `production-transition-preflight-failure-${Date.now()}.json`);
  fs.writeFileSync(report.report_path, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  process.stderr.write(JSON.stringify(report) + '\n', () => process.exit(1));
});
