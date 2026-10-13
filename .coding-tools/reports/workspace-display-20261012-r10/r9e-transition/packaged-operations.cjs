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
requireState(['retire', 'metadata', 'files', 'exec', 'refresh', 'complete', 'status', 'stop', 'stopped-observation', 'confirm-stopped', 'activate'].includes(mode), 'UNSUPPORTED_OPERATION');
const oldMode = ['retire', 'stop', 'stopped-observation', 'confirm-stopped'].includes(mode);
const sourceProofPath = oldMode
  ? path.join(root, '.coding-tools', 'reports', 'folder-access-20261012-r9', 'r9d-candidate-verification.json')
  : path.join(__dirname, '..', 'r9e-candidate-verification.json');
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
const workspaceId = 'workspace_bc86004be2684b958ab7a9a6f9530cd7';
const currentGeneration = 'generation_03f9c04f1b14414fa4bfa7d91cc8ea7a';
function summarize(value) {
  const fields = ['fullyReady','mcpRunning','nativeAlive','nativePid','runtimePhase','executionRole','authorityReady',
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
  const assertOldOwner = async () => {
    const activation = await exactCall('runtime.activation_epoch_status');
    requireState(verified.descriptor.owner_pid === 3476
      && verified.descriptor.instance_id === 'dbf2536afedb8b4e554a29fc9e88cb50'
      && verified.descriptor.installation_id === 'bdf474c17024f7686b83920b289de5422d6129db4bbf8a93659eb744ccaaadba'
      && verified.descriptor.owner_process_start_token === '134362696871111330'
      && activation.activation_epoch_id === 'activation-mv514if9-7a4fabe0ce77708f8be03ff43a6518db'
      && activation.state === 'READY' && activation.admission_open === true, 'EXACT_R9D_OWNER_REQUIRED');
  };
  const readTransitionEvidence = filename => {
    const resolved = path.resolve(filename || '');
    requireState(resolved.toLowerCase().startsWith(path.resolve(__dirname, '..').toLowerCase() + path.sep)
      && fs.statSync(resolved).isFile() && fs.statSync(resolved).size <= 65536, 'BOUNDED_TRANSITION_EVIDENCE_REQUIRED');
    return { path: resolved, value: JSON.parse(fs.readFileSync(resolved, 'utf8')) };
  };
  const requireFreshServerIdle = () => {
    const evidence = readTransitionEvidence(process.argv[4]);
    const value = evidence.value;
    const age = Date.now() - value.observed_at_ms;
    requireState(Number.isSafeInteger(value.observed_at_ms) && age >= 0 && age <= 120000
      && value.database_mutations_performed === false && value.sqlite_integrity_ok === true
      && value.current_generation_idle === true && value.current_device_live_task_writer_idle === true
      && value.selected_target?.binding_id === 'bind_8cd903180f3146099fea128bf55c0b4b'
      && value.selected_target?.device_id === '4c4b7a5b-7744-49ae-a490-78a528a00471'
      && value.selected_target?.workspace_id === workspaceId
      && value.selected_target?.workspace_generation === currentGeneration
      && value.live_pilot?.decision_id === 'pilot_833530c73c72491ba0163037ae80e8f0'
      && value.live_pilot?.workspace_generation === currentGeneration
      && value.live_pilot?.expires_at_ms > Date.now()
      && ['unclosed_tasks', 'unreleased_writers', 'unsettled_actions', 'queued_actions', 'active_dispatch_actions']
        .every(key => value.current_generation_census?.[key] === 0)
      && ['unclosed_tasks', 'unreleased_writers', 'queued_actions', 'active_dispatch_actions']
        .every(key => value.all_current_device_census?.[key] === 0), 'FRESH_SELECTED_CENTRAL_IDLE_RECEIPT_REQUIRED');
    // The all-device historical quarantined UNKNOWN actions remain evidence.
    // They are deliberately not required to be settled or deleted.
    return { path: evidence.path, observed_at_ms: value.observed_at_ms,
      historical_unknown_actions_preserved: true };
  };
  let receipt;
  if (mode === 'retire') {
    await assertOldOwner();
    const serverIdle = requireFreshServerIdle();
    const stopEvidence = readTransitionEvidence(process.argv[5]);
    const stop = stopEvidence.value;
    const stopAge = Date.now() - Date.parse(stop.observed_at);
    if (stop.operation === 'confirm-stopped') {
      const producer = readTransitionEvidence(stop.receipt?.original_operation?.path);
      const failure = readTransitionEvidence(stop.receipt?.original_confirmation_failure?.path);
      requireState(hash(producer.path) === stop.receipt.original_operation.sha256
        && hash(failure.path) === stop.receipt.original_confirmation_failure.sha256
        && producer.value.operation === 'ordinary_stop_operation_result' && producer.value.exact_owner_verified === true
        && failure.value.operation === 'stop' && failure.value.ok === false
        && failure.value.code === 'ORDINARY_STOP_NOT_CONFIRMED'
        && stop.receipt.original_stop_not_replayed === true && stop.receipt.exact_owner_verified === true
        && stop.receipt.runtime.nativeAlive === false && stopAge <= 120000,
      'ORIGINAL_STOP_RECONCILIATION_NOT_VERIFIED');
    }
    requireState(stop.ok === true && ['stop','confirm-stopped'].includes(stop.operation) && stop.candidate.toLowerCase() === candidate.toLowerCase()
      && stop.receipt?.ordinary_stop === true && stop.receipt?.runtime?.mcpRunning === false
      && stop.receipt?.stopped_census?.safe === true && stopAge >= 0 && stopAge <= 900000,
    'FRESH_CONFIRMED_ORDINARY_STOP_REQUIRED');
    const stoppedSnapshot = await exactCall('runtime.lightweight_snapshot');
    requireState(stoppedSnapshot.mcpRunning === false && stoppedSnapshot.nativeAlive === false,
      'EXACT_NATIVE_NOT_STOPPED');
    const { execFileSync } = require('node:child_process');
    const hosts = JSON.parse(execFileSync('powershell.exe', ['-NoProfile','-NonInteractive','-Command',
      "@(Get-Process -Name 'WindowsSandbox*','vmmemWSB','wxc-windows-sandbox-daemon','wxc-exec' -ErrorAction SilentlyContinue | Select-Object Id,ProcessName) | ConvertTo-Json -Compress"],
      { windowsHide:true, encoding:'utf8', timeout:10000 }).trim() || '[]');
    requireState(Array.isArray(hosts) && hosts.length === 0, 'LIVE_SANDBOX_PREVENTS_R9D_RETIREMENT');
    const currentActivation = await exactCall('runtime.activation_epoch_status');
    requireState(verified.descriptor.owner_pid === 3476
      && verified.descriptor.instance_id === 'dbf2536afedb8b4e554a29fc9e88cb50'
      && verified.descriptor.installation_id === 'bdf474c17024f7686b83920b289de5422d6129db4bbf8a93659eb744ccaaadba'
      && currentActivation.activation_epoch_id === 'activation-mv514if9-7a4fabe0ce77708f8be03ff43a6518db'
      && currentActivation.state === 'READY' && currentActivation.admission_open === true,
    'EXACT_R9D_OWNER_REQUIRED');
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
    // The ordinary stop was already confirmed; do not replay its operation.
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
      stopped_census: after, preserved_historical_acceptance: true, durable_state_deleted: false,
      ordinary_stop_receipt: stopEvidence.path, server_idle_receipt: serverIdle, original_stop_not_replayed: true };
  } else if (mode === 'stop') {
    await assertOldOwner();
    const serverIdle = requireFreshServerIdle();
    const { canonicalLedgerCensus } = load('fullCleanActivation');
    const before = await canonicalLedgerCensus({ paths, workspace: root, allowAcceptancePending: true });
    requireState(before.lifecycle?.blockers?.every(reason => reason === 'live_runtime_state_process')
      && before.lifecycle.unexplained_active_runs === 0 && before.lifecycle.unbound_live_resource_residues === 0
      && ['active_tool_calls','active_commands','starting_commands','active_background_operations',
        'active_managed_processes','foreign_heavy_processes','active_agent_lanes','owned_codex_sidecar_residues']
        .every(key => before.counts[key] === 0), 'ACTIVE_WORK_PREVENTS_ORDINARY_STOP');
    const stopped = await client.stop({ manual: true }, expected);
    const operationResultPath = path.join(__dirname, `ordinary-stop-operation-result-${Date.now()}.json`);
    fs.writeFileSync(operationResultPath, JSON.stringify({ operation: 'ordinary_stop_operation_result',
      observed_at: new Date().toISOString(), candidate, runtime: summarize(stopped), before_census: before,
      exact_owner_verified: true, server_idle_receipt: serverIdle }, null, 2), { flag: 'wx' });
    const after = await canonicalLedgerCensus({ paths, workspace: root, allowAcceptancePending: true });
    receipt = { runtime:summarize(stopped), before_census:before, stopped_census:after,
      ordinary_stop:true, historical_acceptance_preserved:true, exact_owner_verified:true,
      operation_result_path:operationResultPath, server_idle_receipt:serverIdle };
    // The real result is preserved above even if a diagnostic confirmation fails.
    requireState(stopped.mcpRunning === false && after.safe === true, 'ORDINARY_STOP_NOT_CONFIRMED');
  } else if (mode === 'confirm-stopped') {
    await assertOldOwner();
    const producer = readTransitionEvidence(process.argv[4]);
    const failure = readTransitionEvidence(process.argv[5]);
    const old = producer.value;
    const resultAge = Date.now() - Date.parse(old.observed_at);
    requireState(old.operation === 'ordinary_stop_operation_result' && old.exact_owner_verified === true
      && old.candidate.toLowerCase() === candidate.toLowerCase()
      && old.runtime?.recoveryHost?.pid === verified.descriptor.owner_pid
      && old.runtime.recoveryHost.instance_id === verified.descriptor.instance_id
      && old.runtime.recoveryHost.last_progress?.step === 'stopped'
      && old.before_census?.lifecycle?.blockers?.every(reason => reason === 'live_runtime_state_process')
      && old.before_census.lifecycle.unexplained_active_runs === 0
      && old.before_census.lifecycle.unbound_live_resource_residues === 0
      && ['active_tool_calls','active_commands','starting_commands','active_background_operations',
        'active_managed_processes','foreign_heavy_processes','active_agent_lanes','owned_codex_sidecar_residues']
        .every(key => old.before_census.counts[key] === 0)
      && resultAge >= 0 && resultAge <= 900000
      && failure.value.operation === 'stop' && failure.value.ok === false
      && failure.value.code === 'ORDINARY_STOP_NOT_CONFIRMED'
      && failure.value.candidate.toLowerCase() === candidate.toLowerCase()
      && Date.parse(failure.value.observed_at) >= Date.parse(old.observed_at), 'ORIGINAL_STOP_PRODUCER_NOT_VERIFIED');
    const runtime = await exactCall('runtime.lightweight_snapshot');
    const { canonicalLedgerCensus } = load('fullCleanActivation');
    const census = await canonicalLedgerCensus({ paths, workspace:root, allowAcceptancePending:true });
    requireState(runtime.mcpRunning === false && runtime.nativeAlive === false && census.safe === true,
      'CURRENT_STOPPED_STATE_NOT_CONFIRMED');
    receipt = { ordinary_stop:true, runtime:summarize(runtime), stopped_census:census,
      exact_owner_verified:true, original_stop_not_replayed:true,
      original_operation:{path:producer.path, sha256:hash(producer.path)},
      original_confirmation_failure:{path:failure.path, sha256:hash(failure.path)},
      diagnosis:'The ordinary stop returned a full snapshot; the evidence harness read lightweight fields at its top level. Original failure preserved; independent current lightweight observation confirms the stopped native process.' };
  } else if (mode === 'stopped-observation') {
    await assertOldOwner();
    const { canonicalLedgerCensus } = load('fullCleanActivation');
    receipt = { runtime:summarize(await exactCall('runtime.lightweight_snapshot')),
      census:await canonicalLedgerCensus({ paths, workspace:root, allowAcceptancePending:true }),
      original_stop_not_replayed:true };
  } else if (mode === 'activate') {
    const { canonicalLedgerCensus } = load('fullCleanActivation');
    const census = await canonicalLedgerCensus({ paths, workspace: root, allowAcceptancePending: true });
    requireState(Array.isArray(census.lifecycle?.blockers) && census.lifecycle.blockers.every(reason => reason === 'live_runtime_state_process')
      && census.lifecycle.unexplained_active_runs === 0 && census.lifecycle.unbound_live_resource_residues === 0
      && ['active_tool_calls','active_commands','starting_commands','active_background_operations','active_managed_processes','foreign_heavy_processes','active_agent_lanes','owned_codex_sidecar_residues']
        .every(key => census.counts[key] === 0), 'ACTIVE_LOCAL_WORK_PREVENTS_FOLDER_ACTIVATION');
    const workspaceRoot = service.registeredWorkspaceRoot({ workspaceId, workspaceGeneration: currentGeneration });
    requireState(workspaceRoot.toLowerCase() === 'e:\\dev\\autocad', 'EXACT_AUTOCAD_ROOT_REQUIRED');
    const { SettingsStore } = load('settingsStore');
    const settings = new SettingsStore(paths);
    const beforeSettings = settings.load();
    const beforeEpoch = await exactCall('runtime.activation_epoch_status');
    const roots = Array.isArray(beforeSettings.authorizedRoots) ? beforeSettings.authorizedRoots : [];
    const key = value => path.normalize(value).toLowerCase();
    let added = false;
    if (key(workspaceRoot) !== key(beforeSettings.workspace) && !roots.some(root => key(root) === key(workspaceRoot))) {
      requireState(roots.length < 32, 'CONTROL_PLANE_WORKSPACE_ROOT_LIMIT');
      await exactCall('runtime.update_authorized_roots', [[...roots, workspaceRoot]]);
      added = true;
    }
    const afterSettings = settings.load();
    const afterEpoch = await exactCall('runtime.activation_epoch_status');
    requireState(key(afterSettings.workspace) === key(beforeSettings.workspace)
      && afterEpoch.activation_epoch_id === beforeEpoch.activation_epoch_id
      && afterEpoch.state === 'READY' && afterEpoch.admission_open === true
      && (key(workspaceRoot) === key(afterSettings.workspace)
        || afterSettings.authorizedRoots.some(root => key(root) === key(workspaceRoot))), 'NATIVE_ROOT_AUTHORIZATION_NOT_VERIFIED');
    const activation = await service.activateWorkspace({ workspaceId, workspaceGeneration: currentGeneration, confirmActivate: true });
    receipt = { ...activation, local_root_authorization: { verified: true, added,
      authorized_root: workspaceRoot, native_default_workspace: afterSettings.workspace,
      activation_epoch_unchanged: true, activation_epoch_id: afterEpoch.activation_epoch_id } };
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
