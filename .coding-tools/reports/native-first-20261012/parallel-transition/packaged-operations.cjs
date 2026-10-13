'use strict';
// Additive evidence for the authorized r9e -> parallel native-first handoff.
// Mutation is gated by --apply, immutable package proofs and exact process IDs.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const originalFs = require('original-fs');
const { spawn, execFileSync } = require('node:child_process');
const root = 'E:\\DEV\\Codex-web';
const oldCandidate = path.join(root, 'dist/windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9e/win-unpacked');
const newCandidate = path.join(root, 'dist/windows-candidate-mxc-wsb-cbe1774-parallel-native-1012-r1/win-unpacked');
const expectedOwner = Object.freeze({ owner_pid: 38436, owner_process_start_token: '134362736855547600',
  instance_id: 'b81bbad41b65c71f1bb4f21b0bdb8d10',
  installation_id: '2e511714fe3f1f64484f11778e1fe2a5c46bb5d5873f02047144b417f7996d0a' });
const oldEpoch = 'activation-mv53i8gp-f06eeb5b46a11d2cf7ebdc9445606937';
const targets = Object.freeze([
  { workspace_id: 'workspace_f93b5bac9dc74fae9cea66f44c4ebc94', workspace_generation: 'generation_a420c8bfcfcb4e42b5bb7fc5e5cec097', workspace_path: 'E:\\DEV\\Codex-web' },
  { workspace_id: 'workspace_bc86004be2684b958ab7a9a6f9530cd7', workspace_generation: 'generation_03f9c04f1b14414fa4bfa7d91cc8ea7a', workspace_path: 'E:\\DEV\\Autocad' }
]);
const mode = process.argv[2];
const apply = process.argv.includes('--apply');
const option = name => { const index = process.argv.indexOf(name); return index >= 0 ? process.argv[index + 1] : undefined; };
const requireState = (condition, code) => { if (!condition) throw Object.assign(new Error(code), { code }); };
const pick = (value, keys) => Object.fromEntries(keys.filter(key => value?.[key] !== undefined).map(key => [key, value[key]]));
const digest = file => crypto.createHash('sha256').update(originalFs.readFileSync(file)).digest('hex');
const read = file => {
  requireState(path.isAbsolute(file) && fs.statSync(file).isFile() && fs.statSync(file).size <= 2 * 1024 * 1024, 'BOUNDED_ABSOLUTE_RECEIPT_REQUIRED');
  return JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
};
const receiptFile = (operation, receipt, extra = {}) => {
  const report = { schema_version: 1, operation, observed_at: new Date().toISOString(), observed_at_ms: Date.now(),
    candidate, ok: true, receipt, ...extra };
  report.report_path = path.join(__dirname, `${operation}-${Date.now()}-${crypto.randomBytes(4).toString('hex')}.json`);
  fs.writeFileSync(report.report_path, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  return report;
};
const summarize = value => pick(value?.status && typeof value.status === 'object' ? { ...value.status, ...value,
  workspace: value.settings?.workspace, deviceId: value.device?.device_id } : value,
  ['fullyReady', 'mcpRunning', 'nativeAlive', 'nativePid', 'runtimePhase', 'executionRole',
  'authorityReady', 'centralConnected', 'centralStatusReason', 'activationEpochId', 'activationState', 'updateIncomplete',
  'connectorContractState', 'loadedSourceReceipts', 'sourceUpdate', 'workspace', 'deviceId', 'fullCleanActivation']);
const oldMode = ['stop', 'stopped-observation', 'retire'].includes(mode);
const candidate = oldMode ? oldCandidate : newCandidate;
const executable = path.join(candidate, 'Coding Tools MCP.exe');
const appRoot = path.join(candidate, 'resources/app.asar');
let stage = 'package_proof';
let mutationStarted = false;
let stopIntentReceipt = null;

async function main() {
  requireState(['stop', 'stopped-observation', 'retire', 'refresh', 'complete', 'status', 'policies'].includes(mode), 'UNSUPPORTED_OPERATION');
  requireState(fs.realpathSync(process.execPath).toLowerCase() === fs.realpathSync(executable).toLowerCase(), 'EXACT_SELECTED_ELECTRON_REQUIRED');
  const oldProof = read(path.join(root, '.coding-tools/reports/workspace-display-20261012-r10/r9e-candidate-verification.json'));
  const parityPath = option('--parity-proof');
  const smokePath = option('--smoke-proof');
  const parity = read(parityPath);
  const smoke = read(smokePath);
  requireState(parity.ok === true && parity.proof_kind === 'exact_source_package_parity'
    && parity.candidate.toLowerCase() === newCandidate.toLowerCase()
    && digest(path.join(newCandidate, 'Coding Tools MCP.exe')) === parity.executable_sha256
    && digest(path.join(newCandidate, 'resources/app.asar')) === parity.app_asar_sha256
    && smoke.ok === true && smoke.candidate.toLowerCase() === newCandidate.toLowerCase()
    && smoke.sha256?.executable === parity.executable_sha256 && smoke.sha256?.app_asar === parity.app_asar_sha256
    && smoke.sha256?.source_package_parity_receipt === digest(parityPath)
    && smoke.production_descriptor_stable === true && smoke.fixture_generations_alive_after?.length === 0
    && smoke.candidate_process_census_after?.length === 0 && smoke.profiles_remaining_after?.length === 0, 'FINAL_PARITY_AND_ISOLATED_SMOKE_REQUIRED');
  if (oldMode) requireState(oldProof.ok === true && oldProof.candidate.toLowerCase() === oldCandidate.toLowerCase()
    && digest(executable) === oldProof.executable_sha256 && digest(appRoot) === oldProof.app_asar_sha256, 'EXACT_OLD_PACKAGE_REQUIRED');
  for (const [relative, hash] of Object.entries(parity.code_sha256 || {})) {
    requireState(digest(path.join(root, relative)) === hash, 'SOURCE_CHANGED_AFTER_FINAL_PACKAGE_PROOF');
  }
  const { assertExactPackagedResources, assertExactControlPlaneAdapter } = require(path.join(root, 'scripts/verify-packaged-resources'));
  assertExactPackagedResources(path.join(root, 'resources'), path.join(newCandidate, 'resources/resources'),
    { separatelyVerifiedTopLevelDirectories: ['control-plane'] });
  assertExactControlPlaneAdapter(path.join(root, 'control-plane/control_plane'), path.join(newCandidate, 'resources/resources/control-plane'));
  const load = name => require(path.join(appRoot, 'electron/services', name));
  const { RuntimePaths } = load('runtimePaths');
  const { RecoveryIpcClient, loadRecoveryDescriptor } = load('recoveryIpc');
  const { descriptorMatchesInstallation, descriptorRequestOptions, readVerifiedReadyHost } = load('recoveryHostLauncher');
  const { canonicalLedgerCensus } = load('fullCleanActivation');
  const { processIdentityFrom, observeLifecycleProcessIdentity, sameProcessIdentity, terminateExactProcessTree, waitForExactProcessExit } = load('processIdentity');
  const paths = new RuntimePaths({ dataRoot: path.join(process.env.APPDATA, 'web-mcp-assistant'), appRoot,
    resourcesRoot: path.join(candidate, 'resources/resources'), executablePath: executable, runtimeMode: 'packaged' });
  const client = new RecoveryIpcClient({ paths });
  stage = 'exact_host';
  const verified = await readVerifiedReadyHost(client, paths, loadRecoveryDescriptor, 2, { allowAdmissionBlocked: true });
  requireState(verified && descriptorMatchesInstallation(verified.descriptor, paths.runtimeIdentity()), 'SELECTED_HOST_NOT_VERIFIED');
  if (oldMode) requireState(Object.entries(expectedOwner).every(([key, value]) => verified.descriptor[key] === value), 'EXACT_R9E_OWNER_CHANGED');
  const expected = descriptorRequestOptions(verified.descriptor);
  const exact = (action, args = []) => client.call(action, args, expected);
  const hostIdentity = processIdentityFrom(verified.descriptor);
  requireState(sameProcessIdentity(hostIdentity, await observeLifecycleProcessIdentity(hostIdentity.pid)), 'HOST_START_IDENTITY_CHANGED');
  const registry = read(paths.controlPlaneWorkspaceRegistryFile());
  for (const target of targets) {
    const matches = registry.entries?.filter(entry => entry.workspace_id === target.workspace_id && entry.workspace_generation === target.workspace_generation) || [];
    requireState(matches.length === 1 && path.resolve(matches[0].canonical_path).toLowerCase() === target.workspace_path.toLowerCase(), 'EXACT_WORKSPACE_REGISTRATION_CHANGED');
  }
  const policyNames = ['control-plane-workspaces.json', 'control-plane-node.json', 'control-plane-read-only-policy.json',
    'control-plane-file-read-policy.json', 'control-plane-approved-patch-policy.json', 'control-plane-document-write-policy.json', 'control-plane-exec-policy.json'];
  const fingerprints = () => Object.fromEntries(policyNames.map(name => {
    const file = path.join(paths.dataRoot(), name);
    return [name, fs.existsSync(file) ? { present: true, sha256: digest(file) } : { present: false }];
  }));
  const beforeFiles = fingerprints();
  const idle = census => Array.isArray(census.lifecycle?.blockers)
    && census.lifecycle.blockers.every(reason => reason === 'live_runtime_state_process')
    && census.lifecycle.unexplained_active_runs === 0 && census.lifecycle.unbound_live_resource_residues === 0
    && ['active_tool_calls', 'active_commands', 'starting_commands', 'active_background_operations', 'active_managed_processes',
      'foreign_heavy_processes', 'active_agent_lanes', 'owned_codex_sidecar_residues'].every(key => census.counts?.[key] === 0);
  const census = () => canonicalLedgerCensus({ paths, workspace: root, allowAcceptancePending: true });
  const noSandboxProcess = () => {
    const text = execFileSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command',
      "@(Get-Process -Name 'WindowsSandbox*','vmmemWSB','wxc-windows-sandbox-daemon','wxc-exec' -ErrorAction SilentlyContinue | Select-Object Id,ProcessName) | ConvertTo-Json -Compress"],
    { windowsHide: true, encoding: 'utf8', timeout: 10_000, maxBuffer: 65536 }).trim();
    const found = JSON.parse(text || '[]');
    requireState(Array.isArray(found) && found.length === 0, 'LIVE_SANDBOX_PROCESS_REQUIRES_OWNERSHIP_REVIEW');
    return { observed_at_ms: Date.now(), processes: [], ownership_not_inferred: true };
  };
  const serverFence = () => {
    const file = option('--server-fence');
    const fence = read(file);
    const age = Date.now() - fence.observed_at_ms;
    requireState(fence.ok === true && fence.fenced === true && fence.live_work_idle === true
      && fence.historical_unknown_preserved === true && age >= 0 && age <= 120_000
      && targets.every(target => fence.targets?.some(item => item.workspace_id === target.workspace_id
        && item.workspace_generation === target.workspace_generation)), 'FRESH_EXACT_SERVER_FENCE_REQUIRED');
    return { receipt_path: file, sha256: digest(file), observed_at_ms: fence.observed_at_ms };
  };
  let result;
  if (mode === 'status' || mode === 'stopped-observation') {
    result = { runtime: summarize(await exact('runtime.lightweight_snapshot')), activation: await exact('runtime.activation_epoch_status'),
      census: await census(), owner: pick(verified.descriptor, ['owner_pid', 'owner_process_start_token', 'instance_id', 'installation_id']),
      preserved_fingerprints: beforeFiles, original_stop_not_replayed: mode === 'stopped-observation' };
  } else {
    requireState(apply, 'EXPLICIT_APPLY_REQUIRED');
    if (mode === 'stop') {
      const fence = serverFence();
      const before = await census();
      requireState(idle(before), 'ACTIVE_LOCAL_WORK_PREVENTS_ORDINARY_STOP');
      const sandbox = noSandboxProcess();
      const epoch = await exact('runtime.activation_epoch_status');
      requireState(epoch.activation_epoch_id === oldEpoch && epoch.state === 'READY' && epoch.admission_open === true, 'OLD_EPOCH_CHANGED');
      serverFence();
      stopIntentReceipt = receiptFile('ordinary-stop-intent', { owner: expectedOwner, epoch, before_census: before,
        server_fence: fence, preserved_fingerprints: beforeFiles, sandbox, request: { action: 'runtime.stop', options: { manual: true } },
        effect_observed: false }).report_path;
      stage = 'ordinary_stop'; mutationStarted = true;
      const stopped = await client.stop({ manual: true }, expected);
      const stop = receiptFile('ordinary-stop-result', { runtime: summarize(stopped), owner: expectedOwner, epoch, before_census: before,
        server_fence: fence, preserved_fingerprints: beforeFiles, historical_acceptance_preserved: true, sandbox,
        stop_intent_receipt: stopIntentReceipt });
      requireState(summarize(stopped).mcpRunning === false, 'ORDINARY_STOP_NOT_CONFIRMED_OBSERVE_WITHOUT_REPLAY');
      result = { stop_result_receipt: stop.report_path, runtime: summarize(stopped), stopped_census: await census(), owner: expectedOwner };
    } else if (mode === 'retire') {
      const stopped = read(option('--stop-receipt'));
      requireState(stopped.ok === true && stopped.operation === 'ordinary-stop-result'
        && stopped.candidate.toLowerCase() === oldCandidate.toLowerCase()
        && Object.entries(expectedOwner).every(([key, value]) => stopped.receipt.owner[key] === value)
        && Date.now() - stopped.observed_at_ms >= 0 && Date.now() - stopped.observed_at_ms <= 900_000
        && JSON.stringify(stopped.receipt.preserved_fingerprints) === JSON.stringify(beforeFiles), 'FRESH_EXACT_STOP_RECEIPT_REQUIRED');
      let stopReconciliation = null;
      if (stopped.receipt.runtime.mcpRunning !== false) {
        const observationPath = option('--stopped-observation');
        const observation = read(observationPath);
        requireState(observation.ok === true && observation.operation === 'stopped-observation'
          && observation.candidate.toLowerCase() === oldCandidate.toLowerCase()
          && Object.entries(expectedOwner).every(([key, value]) => observation.receipt.owner[key] === value)
          && observation.observed_at_ms >= stopped.observed_at_ms && Date.now() - observation.observed_at_ms >= 0
          && Date.now() - observation.observed_at_ms <= 120_000
          && observation.receipt.original_stop_not_replayed === true
          && observation.receipt.runtime.mcpRunning === false && observation.receipt.runtime.nativeAlive === false
          && observation.receipt.census.safe === true && idle(observation.receipt.census)
          && JSON.stringify(observation.receipt.preserved_fingerprints) === JSON.stringify(beforeFiles), 'FRESH_LINKED_STOPPED_OBSERVATION_REQUIRED');
        stopReconciliation = receiptFile('ordinary-stop-reconciliation', {
          original_stop_receipt: option('--stop-receipt'), original_stop_sha256: digest(option('--stop-receipt')),
          stopped_observation: observationPath, stopped_observation_sha256: digest(observationPath), owner: expectedOwner,
          runtime: observation.receipt.runtime, stopped_census: observation.receipt.census,
          original_result_preserved: true, original_stop_not_replayed: true, method: 'fresh exact owner observation after original returned stop result'
        }).report_path;
      }
      const stoppedCensus = await census();
      requireState(stoppedCensus.safe === true && idle(stoppedCensus), 'STOPPED_CANONICAL_CENSUS_NOT_QUIESCENT');
      requireState((await exact('runtime.lightweight_snapshot')).mcpRunning === false, 'RUNTIME_RESTARTED_AFTER_STOP');
      const supervisorRoot = path.join(paths.dataRoot(), 'recovery-supervisor');
      const manifestFile = path.join(supervisorRoot, 'manifest.json');
      const manifestHash = digest(manifestFile);
      const manifest = read(manifestFile);
      requireState(manifest.schema_version === 1 && manifest.mode === 'packaged'
        && fs.realpathSync(manifest.app_root).toLowerCase() === oldCandidate.toLowerCase()
        && fs.realpathSync(manifest.executable).toLowerCase() === executable.toLowerCase(), 'EXACT_OLD_SUPERVISOR_REQUIRED');
      const status = await exact('recovery.status', [{ fresh: true }]);
      const ui = status.electron_ui_recovery;
      const sameUi = current => current?.registered === true && current.ui_runtime_mode === 'packaged'
        && current.pid === ui.pid && current.instance_id === ui.instance_id && current.ui_installation_id === expectedOwner.installation_id;
      const noPendingUi = async current => {
        requireState(Number(current?.pending_registration_until_unix_ms || 0) <= Date.now(), 'UI_LAUNCH_PENDING');
        if (current?.last_launch_pid) requireState((await observeLifecycleProcessIdentity(current.last_launch_pid)).state === 'absent', 'UI_LAUNCH_IDENTITY_UNVERIFIED');
      };
      let uiIdentity = null;
      if (ui?.alive === false) { requireState(ui.suppressed === true, 'MISSING_UI_NOT_SUPPRESSED'); await noPendingUi(ui); }
      else { requireState(sameUi(ui) && ui.alive === true, 'EXACT_UI_REQUIRED'); uiIdentity = processIdentityFrom(await observeLifecycleProcessIdentity(ui.pid)); }
      requireState(digest(manifestFile) === manifestHash, 'SUPERVISOR_CHANGED');
      stage = 'supervisor_suppression'; mutationStarted = true;
      fs.writeFileSync(path.join(supervisorRoot, 'stop.request'), new Date().toISOString(), { encoding: 'ascii', mode: 0o600 });
      if (uiIdentity) {
        await exact('client.suppress_ui_recovery', [{ instance_id: ui.instance_id, reason: 'operator_quit' }]);
        const suppressed = (await exact('recovery.status', [{ fresh: true }])).electron_ui_recovery;
        requireState(sameUi(suppressed) && suppressed.alive === true && suppressed.suppressed === true
          && sameProcessIdentity(uiIdentity, await observeLifecycleProcessIdentity(ui.pid)), 'UI_IDENTITY_CHANGED');
        const env = { ...process.env }; delete env.ELECTRON_RUN_AS_NODE;
        const signal = spawn(executable, [`--dev-ui-stop=${ui.instance_id}`], { cwd: candidate, env, stdio: 'ignore', detached: true, windowsHide: true });
        await new Promise((resolve, reject) => { signal.once('spawn', resolve); signal.once('error', reject); }); signal.unref();
        await waitForExactProcessExit(uiIdentity, { observeProcessIdentity: observeLifecycleProcessIdentity, timeoutMs: 20_000 });
      }
      const finalUi = (await exact('recovery.status', [{ fresh: true }])).electron_ui_recovery;
      requireState(finalUi?.alive === false && finalUi.suppressed === true && (uiIdentity === null || sameUi(finalUi)), 'UI_NOT_TERMINAL');
      await noPendingUi(finalUi);
      const finalCensus = await census();
      requireState(finalCensus.safe === true && idle(finalCensus), 'WORK_APPEARED_DURING_RETIREMENT');
      const finalSandbox = noSandboxProcess();
      const descriptor = loadRecoveryDescriptor(paths);
      requireState(Object.entries(expectedOwner).every(([key, value]) => descriptor[key] === value)
        && sameProcessIdentity(hostIdentity, processIdentityFrom(descriptor)), 'OWNER_CHANGED_BEFORE_RETIREMENT');
      await exact('recovery.ping');
      stage = 'exact_host_retirement';
      const retirement = await terminateExactProcessTree(hostIdentity, { observeProcessIdentity: observeLifecycleProcessIdentity });
      requireState(JSON.stringify(beforeFiles) === JSON.stringify(fingerprints()), 'POLICY_CHANGED_DURING_HANDOFF');
      result = { retirement, owner: expectedOwner, ui_stopped: finalUi, stopped_census: finalCensus, stop_reconciliation: stopReconciliation,
        manifest_sha256: manifestHash, preserved_fingerprints: beforeFiles, durable_state_deleted: false,
        sandbox_observation: finalSandbox, final_candidate: newCandidate,
        final_package: { executable_sha256: parity.executable_sha256, app_asar_sha256: parity.app_asar_sha256 } };
    } else if (mode === 'refresh') {
      requireState(idle(await census()), 'ACTIVE_LOCAL_WORK_PREVENTS_REFRESH');
      stage = 'full_clean_refresh'; mutationStarted = true;
      const refreshed = await client.restart({ refresh: true, mode: 'full_clean_refresh', allowAcceptancePending: true,
        reason: 'operator_parallel_native_first_preserve_history' }, expected);
      result = { runtime: summarize(refreshed), activation: await exact('runtime.activation_epoch_status') };
    } else if (mode === 'complete') {
      const epoch = option('--epoch');
      requireState(/^activation-[A-Za-z0-9_-]+$/.test(epoch || '') && (await exact('runtime.activation_epoch_status')).activation_epoch_id === epoch, 'EXACT_NEW_EPOCH_REQUIRED');
      stage = 'activation_completion'; mutationStarted = true;
      result = { result: await exact('runtime.complete_activation_epoch', [epoch]), runtime: summarize(await exact('runtime.lightweight_snapshot')),
        activation: await exact('runtime.activation_epoch_status'), census: await census() };
    } else if (mode === 'policies') {
      const { ControlPlaneEnrollmentService } = load('controlPlaneEnrollment');
      const enrollment = new ControlPlaneEnrollmentService({ paths, experimentalWindowsSandbox: true });
      result = [];
      for (const target of targets) {
        stage = `exact_policies_${target.workspace_id}`;
        const request = { workspaceId: target.workspace_id, workspaceGeneration: target.workspace_generation };
        const existing = await enrollment.inspectLocalExecPolicy(request);
        mutationStarted = true;
        const activation = await enrollment.activateWorkspace({ ...request, confirmActivate: true });
        const files = await enrollment.installStandingWorkspaceFilePolicies({ ...request, allowWrite: true, replaceExisting: true });
        const exec = await enrollment.installStandingWorkspaceExecPolicy({ ...request, executionMode: 'native_first',
          nativeArgvPrefixes: existing.workspace_id === target.workspace_id && existing.workspace_generation === target.workspace_generation
            ? existing.native_argv_prefixes || [] : [], probeSandbox: false, replaceExisting: true });
        result.push({ target, activation, files, exec, observed_files: await enrollment.inspectStandingWorkspaceFilePolicies(request),
          observed_exec: await enrollment.inspectStandingWorkspaceExecPolicy(request) });
        receiptFile('workspace-policy-result', result[result.length - 1]);
      }
    }
  }
  const report = receiptFile(mode, result, { mutating: mutationStarted, historical_unknown_preserved: true,
    parity_proof_sha256: digest(parityPath), smoke_proof_sha256: digest(smokePath) });
  process.stdout.write(JSON.stringify(pick(report, ['ok', 'operation', 'report_path', 'candidate', 'mutating'])) + '\n', () => process.exit(0));
}
main().catch(error => {
  const report = { schema_version: 1, operation: mode, candidate, observed_at: new Date().toISOString(), observed_at_ms: Date.now(),
    ok: false, stage, code: error?.code || 'TRANSITION_FAILED', mutating_action_started: mutationStarted,
    ...(stopIntentReceipt ? { stop_intent_receipt: stopIntentReceipt } : {}),
    retry_instruction: mutationStarted ? 'Observe exact current state and original operation receipt; do not replay uncertain mutations.' : 'Resolve the read-only gate before applying.' };
  report.report_path = path.join(__dirname, `${mode}-failure-${Date.now()}.json`);
  fs.writeFileSync(report.report_path, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  process.stderr.write(JSON.stringify(report) + '\n', () => process.exit(1));
});
