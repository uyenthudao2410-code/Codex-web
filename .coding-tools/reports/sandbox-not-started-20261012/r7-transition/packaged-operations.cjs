'use strict';
// Run with the selected Electron executable in ELECTRON_RUN_AS_NODE mode so
// every service is loaded from that candidate's actual app.asar.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const originalFs = require('original-fs');
const { spawn } = require('node:child_process');
const root = 'E:\\DEV\\Codex-web';
const mode = process.argv[2];
const candidate = fs.realpathSync(path.resolve(process.argv[3] || ''));
function requireState(condition, code) {
  if (!condition) throw Object.assign(new Error(code), { code });
}
requireState(candidate.toLowerCase().startsWith(path.join(root, 'dist').toLowerCase() + path.sep), 'CANDIDATE_OUTSIDE_WORKSPACE');
const appRoot = path.join(candidate, 'resources', 'app.asar');
const executable = path.join(candidate, 'Coding Tools MCP.exe');
requireState(process.execPath.toLowerCase() === executable.toLowerCase(), 'SELECTED_ELECTRON_EXECUTABLE_REQUIRED');
requireState(['retire', 'metadata', 'files', 'exec', 'refresh', 'complete', 'status'].includes(mode), 'UNSUPPORTED_OPERATION');
const sourceProofPath = path.join(__dirname, '..', mode === 'retire' ? 'r6-candidate-verification.json' : 'r7-candidate-verification.json');
const sourceProof = JSON.parse(fs.readFileSync(sourceProofPath, 'utf8'));
const hash = file => crypto.createHash('sha256').update(originalFs.readFileSync(file)).digest('hex');
requireState(sourceProof.ok === true && sourceProof.candidate.toLowerCase() === candidate.toLowerCase()
  && hash(executable) === sourceProof.executable_sha256 && hash(appRoot) === sourceProof.app_asar_sha256
  && hash(path.join(candidate, 'resources', 'resources', 'coding-tools-mcp', 'coding_tools_mcp', 'windows_mxc_state_aware.py'))
    === sourceProof.packaged_adapter_sha256, 'EXACT_SELECTED_PACKAGE_REQUIRED');
const load = name => require(path.join(appRoot, 'electron', 'services', name));
const { RuntimePaths } = load('runtimePaths');
const { RecoveryIpcClient, loadRecoveryDescriptor } = load('recoveryIpc');
const { descriptorMatchesInstallation, descriptorRequestOptions, readVerifiedReadyHost } = load('recoveryHostLauncher');
const { ControlPlaneEnrollmentService } = load('controlPlaneEnrollment');
const paths = new RuntimePaths({ dataRoot: path.join(process.env.APPDATA, 'web-mcp-assistant'),
  appRoot, resourcesRoot: path.join(candidate, 'resources', 'resources'),
  executablePath: executable, runtimeMode: 'packaged' });
const client = new RecoveryIpcClient({ paths });
const service = new ControlPlaneEnrollmentService({ paths, experimentalWindowsSandbox: true });
const workspaceId = 'workspace_f93b5bac9dc74fae9cea66f44c4ebc94';
const currentGeneration = 'generation_a420c8bfcfcb4e42b5bb7fc5e5cec097';
function summarize(value) {
  const fields = ['fullyReady','mcpRunning','nativePid','runtimePhase','executionRole','authorityReady',
    'centralConnected','centralStatusReason','activationEpochId','activationState','updateIncomplete',
    'connectorContractState','loadedSourceReceipts','sourceUpdate','workspace','deviceId','recoveryHost',
    'fullCleanActivation','activeCommands','activeToolCalls'];
  return Object.fromEntries(fields.filter(key => value?.[key] !== undefined).map(key => [key, value[key]]));
}
async function main() {
  const verified = await readVerifiedReadyHost(client, paths, loadRecoveryDescriptor, 2, { allowAdmissionBlocked: true });
  requireState(verified && descriptorMatchesInstallation(verified.descriptor, paths.runtimeIdentity()), 'SELECTED_PACKAGED_HOST_NOT_VERIFIED');
  const expected = descriptorRequestOptions(verified.descriptor);
  const exactCall = (action, args = []) => client.call(action, args, expected);
  await exactCall('recovery.ping');
  let receipt;
  if (mode === 'retire') {
    const currentActivation = await exactCall('runtime.activation_epoch_status');
    requireState(verified.descriptor.owner_pid === 25028
      && verified.descriptor.instance_id === '8b8992a71407cd61f37317ae0b438cb4'
      && verified.descriptor.installation_id === '4eedacadb4c7d463a2c00d7790db84198f7b31a22abf683163d55b1503c935f5'
      && currentActivation.activation_epoch_id === 'activation-mv4u5k6v-cfeabc74ae10012ae61eab8d4c87e8b4'
      && currentActivation.state === 'READY' && currentActivation.admission_open === true,
    'EXACT_READY_R6_OWNER_REQUIRED');
    const { canonicalLedgerCensus } = load('fullCleanActivation');
    const { processIdentityFrom, observeLifecycleProcessIdentity, sameProcessIdentity,
      terminateExactProcessTree, waitForExactProcessExit } = load('processIdentity');
    const before = await canonicalLedgerCensus({ paths, workspace: root, allowAcceptancePending: true });
    requireState(Array.isArray(before.lifecycle?.blockers)
      && before.lifecycle.blockers.every(reason => reason === 'live_runtime_state_process')
      && (before.safe === true || before.reason === 'live_runtime_state_process')
      && before.lifecycle.unexplained_active_runs === 0
      && before.lifecycle.unbound_live_resource_residues === 0
      && ['active_tool_calls','active_commands','starting_commands','active_background_operations',
        'active_managed_processes','foreign_heavy_processes','active_agent_lanes','owned_codex_sidecar_residues']
        .every(key => before.counts[key] === 0), 'ACTIVE_WORK_PREVENTS_PACKAGED_RETIREMENT');
    const hostIdentity = processIdentityFrom(verified.descriptor);
    requireState(sameProcessIdentity(hostIdentity, await observeLifecycleProcessIdentity(hostIdentity.pid)), 'HOST_PROCESS_IDENTITY_CHANGED');
    const supervisorRoot = path.join(paths.dataRoot(), 'recovery-supervisor');
    const manifestFile = path.join(supervisorRoot, 'manifest.json');
    const manifestStat = fs.statSync(manifestFile);
    requireState(manifestStat.isFile() && manifestStat.size <= 65536, 'SUPERVISOR_MANIFEST_INVALID');
    const manifestRaw = fs.readFileSync(manifestFile, 'utf8');
    const manifest = JSON.parse(manifestRaw);
    requireState(manifest.schema_version === 1 && manifest.mode === 'packaged'
      && typeof manifest.app_root === 'string' && path.isAbsolute(manifest.app_root)
      && typeof manifest.executable === 'string' && path.isAbsolute(manifest.executable)
      && fs.realpathSync(manifest.app_root).toLowerCase() === candidate.toLowerCase()
      && fs.realpathSync(manifest.executable).toLowerCase() === fs.realpathSync(executable).toLowerCase(),
    'SUPERVISOR_INSTALLATION_MISMATCH');
    const status = await exactCall('recovery.status', [{ fresh: true }]);
    const ui = status.electron_ui_recovery;
    const installationId = paths.runtimeIdentity().installation_id;
    const sameUi = current => current?.registered === true && current.ui_runtime_mode === 'packaged'
      && current.pid === ui.pid && current.instance_id === ui.instance_id
      && current.ui_installation_id === installationId;
    const noPendingUiLaunch = async current => {
      requireState(Number(current?.pending_registration_until_unix_ms || 0) <= Date.now(),
        'UI_RECOVERY_LAUNCH_STILL_PENDING');
      if (current?.last_launch_pid) {
        const launched = await observeLifecycleProcessIdentity(current.last_launch_pid);
        requireState(launched.state === 'absent', 'UI_RECOVERY_LAUNCH_PROCESS_UNVERIFIED');
      }
    };
    let uiIdentity = null;
    if (ui?.alive === false) {
      requireState(ui.suppressed === true, 'MISSING_UI_RECOVERY_NOT_SUPPRESSED');
      await noPendingUiLaunch(ui);
    } else {
      requireState(sameUi(ui) && ui.alive === true
        && /^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/.test(ui.instance_id || '')
        && Number.isSafeInteger(ui.pid) && ui.pid > 0, 'CURRENT_PACKAGED_UI_UNVERIFIED');
      uiIdentity = processIdentityFrom(await observeLifecycleProcessIdentity(ui.pid));
    }
    requireState(fs.readFileSync(manifestFile, 'utf8') === manifestRaw, 'SUPERVISOR_MANIFEST_CHANGED');
    fs.writeFileSync(path.join(supervisorRoot, 'stop.request'), new Date().toISOString(), { encoding: 'ascii', mode: 0o600 });
    if (uiIdentity) {
      await exactCall('client.suppress_ui_recovery', [{ instance_id: ui.instance_id, reason: 'operator_quit' }]);
      const suppressed = (await exactCall('recovery.status', [{ fresh: true }])).electron_ui_recovery;
      requireState(sameUi(suppressed) && suppressed.alive === true && suppressed.suppressed === true
        && sameProcessIdentity(uiIdentity, await observeLifecycleProcessIdentity(ui.pid)), 'UI_PROCESS_IDENTITY_CHANGED');
      const uiEnvironment = { ...process.env }; delete uiEnvironment.ELECTRON_RUN_AS_NODE;
      const signal = spawn(executable, [`--dev-ui-stop=${ui.instance_id}`], { cwd: candidate,
        env: uiEnvironment, stdio: 'ignore', detached: true, windowsHide: true });
      await new Promise((resolve, reject) => { signal.once('spawn', resolve); signal.once('error', reject); });
      signal.unref();
      await waitForExactProcessExit(uiIdentity, { observeProcessIdentity: observeLifecycleProcessIdentity, timeoutMs: 20000 });
    }
    const stoppedUi = (await exactCall('recovery.status', [{ fresh: true }])).electron_ui_recovery;
    requireState(stoppedUi?.alive === false && stoppedUi.suppressed === true
      && (uiIdentity === null || sameUi(stoppedUi)), 'PACKAGED_UI_NOT_VERIFIED_STOPPED');
    await noPendingUiLaunch(stoppedUi);
    await client.stop({ manual: true }, expected);
    const after = await canonicalLedgerCensus({ paths, workspace: root, allowAcceptancePending: true });
    requireState(after.safe === true, 'STOPPED_CANONICAL_CENSUS_NOT_QUIESCENT');
    const finalUi = (await exactCall('recovery.status', [{ fresh: true }])).electron_ui_recovery;
    requireState(finalUi?.alive === false && finalUi.suppressed === true
      && (uiIdentity === null || sameUi(finalUi)), 'PACKAGED_UI_RECOVERY_STATE_CHANGED');
    await noPendingUiLaunch(finalUi);
    const currentDescriptor = loadRecoveryDescriptor(paths);
    requireState(currentDescriptor.owner_pid === verified.descriptor.owner_pid
      && currentDescriptor.instance_id === verified.descriptor.instance_id
      && currentDescriptor.installation_id === verified.descriptor.installation_id
      && sameProcessIdentity(hostIdentity, processIdentityFrom(currentDescriptor)), 'RECOVERY_OWNER_CHANGED');
    await exactCall('recovery.ping');
    const retirement = await terminateExactProcessTree(hostIdentity, { observeProcessIdentity: observeLifecycleProcessIdentity });
    receipt = { retirement, ui_pid: ui?.pid || null, ui_was_missing: uiIdentity === null,
      ui_stopped: finalUi, host_pid: hostIdentity.pid, before_census: before,
      stopped_census: after, preserved_historical_acceptance: true, durable_state_deleted: false };
  } else if (mode === 'metadata' || mode === 'files' || mode === 'exec') {
    const generation = process.argv[4];
    requireState(generation === currentGeneration, 'EXACT_CURRENT_GENERATION_REQUIRED');
    receipt = mode === 'metadata'
      ? await service.installReadOnlyPolicyAssignment({ workspaceId, workspaceGeneration: generation, replaceExisting: true })
      : mode === 'files'
      ? await service.installStandingWorkspaceFilePolicies({ workspaceId, workspaceGeneration: generation, allowWrite: true, replaceExisting: true })
      : await service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration: generation, replaceExisting: true });
  } else if (mode === 'refresh') {
    const result = await client.restart({ refresh: true, mode: 'full_clean_refresh',
      allowAcceptancePending: true, reason: 'operator_new_machine_repair_preserve_historical_acceptance' }, expected);
    receipt = { runtime: summarize(result), activation: await exactCall('runtime.activation_epoch_status') };
  } else if (mode === 'complete') {
    const epochId = process.argv[4];
    requireState(/^activation-[A-Za-z0-9_-]+$/.test(epochId || ''), 'EXACT_ACTIVATION_EPOCH_REQUIRED');
    receipt = { result: await exactCall('runtime.complete_activation_epoch', [epochId]), runtime: summarize(await exactCall('runtime.lightweight_snapshot')), activation: await exactCall('runtime.activation_epoch_status') };
  } else if (mode === 'status') {
    receipt = { installation_id: paths.runtimeIdentity().installation_id, host_pid: verified.descriptor.owner_pid,
      runtime: summarize(await exactCall('runtime.lightweight_snapshot')), activation: await exactCall('runtime.activation_epoch_status'),
      workspaces: await service.listWorkspaces(), file_policies: await service.inspectStandingWorkspaceFilePolicies(), exec_policy: await service.inspectLocalExecPolicy() };
  } else throw Object.assign(new Error('UNSUPPORTED_OPERATION'), { code: 'UNSUPPORTED_OPERATION' });
  const report = { operation: mode, observed_at: new Date().toISOString(), candidate, ok: true, receipt };
  report.report_path = path.join(__dirname, `packaged-${mode}-receipt-${Date.now()}.json`);
  fs.writeFileSync(report.report_path, JSON.stringify(report, null, 2), { flag: 'wx' });
  console.log(JSON.stringify(report));
}
main().then(() => process.exit(0), error => {
  const report = { operation: mode, observed_at: new Date().toISOString(), candidate, ok: false, code: error?.code || error?.name || 'ERROR' };
  report.report_path = path.join(__dirname, `packaged-${mode}-failure-${Date.now()}.json`);
  fs.writeFileSync(report.report_path, JSON.stringify(report, null, 2), { flag: 'wx' });
  console.error(JSON.stringify(report)); process.exit(1);
});
