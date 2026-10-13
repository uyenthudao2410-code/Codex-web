'use strict';
// Additive evidence for the authorized old-r4 -> r4 immutable-resource handoff.
// Mutation is gated by --apply, immutable package proofs and exact process IDs.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const originalFs = require('original-fs');
const { spawn, execFileSync, spawnSync } = require('node:child_process');
const root = 'E:\\DEV\\Codex-web';
const oldCandidate = path.join(root, 'dist/windows-candidate-mxc-wsb-cbe1774-parallel-native-1012-r4/win-unpacked');
const newCandidate = path.join(root, 'dist/windows-candidate-mxc-wsb-cbe1774-parallel-r4-timefix/win-unpacked');
const expectedOwner = Object.freeze({ owner_pid: 28800, owner_process_start_token: '134362894309253220',
  instance_id: '121b28e1a1d93d1d5a03775fc6c9a5e6',
  installation_id: '491e1d67970775eb93c7085942ad76fb233707c40672f9b37e8c8e13e5c20b96' });
// old-r4 is the exact READY owner; one supported stop precedes fresh stopped observation.
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
const oldMode = ['stop', 'timefix-old-stopped-observation', 'retire'].includes(mode);
const candidate = oldMode ? oldCandidate : newCandidate;
const executable = path.join(candidate, 'Coding Tools MCP.exe');
const appRoot = path.join(candidate, 'resources/app.asar');
let stage = 'package_proof';
let mutationStarted = false;
let stopIntentReceipt = null;
let canaryPolicyBaselineReceipt = null;
let canaryPolicyProgressReceipts = [];
let scopedPollIntentReceipt = null;
let readReconciliationIntentReceipt = null;


async function main() {
  requireState(['stop', 'timefix-old-stopped-observation', 'retire', 'refresh', 'complete', 'status', 'policies', 'canary-build', 'canary-overlap', 'final-policy'].includes(mode), 'UNSUPPORTED_OPERATION');
  requireState(fs.realpathSync(process.execPath).toLowerCase() === fs.realpathSync(executable).toLowerCase(), 'EXACT_SELECTED_ELECTRON_REQUIRED');
  requireState(process.env.PYTHONDONTWRITEBYTECODE === '1', 'BYTECODE_WRITES_MUST_BE_DISABLED');
  const oldProof = read(path.join(root, '.coding-tools/reports/native-first-20261012/parallel-r4-candidate-parity.json'));
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
  if (oldMode) requireState(Object.entries(expectedOwner).every(([key, value]) => verified.descriptor[key] === value), 'EXACT_OLD_R4_OWNER_CHANGED');
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
  const oldResourceSnapshotPath = path.join(root, '.coding-tools/reports/parallel-native-first-20261012/timefix-old-resource-snapshot.json');
  requireState(digest(oldResourceSnapshotPath) === '23504a0f0b469c1b9d30346e049b26e93dc71921a3bb8a3255e988e31ba27db2', 'RETIRING_RESOURCE_SNAPSHOT_CHANGED');
  const oldResourceSnapshot = read(oldResourceSnapshotPath);
  const verifySelectedResources = () => {
    const selectedResources = path.join(candidate, 'resources/resources');
    if (oldMode) {
      requireState(oldResourceSnapshot.ok === true && oldResourceSnapshot.retirement_only === true
        && oldResourceSnapshot.candidate.toLowerCase() === oldCandidate.toLowerCase()
        && oldResourceSnapshot.executable_sha256 === digest(executable)
        && oldResourceSnapshot.app_asar_sha256 === digest(appRoot)
        && oldResourceSnapshot.old_parity_proof_sha256 === digest(path.join(root, '.coding-tools/reports/native-first-20261012/parallel-r4-candidate-parity.json'))
        && oldResourceSnapshot.old_smoke_proof_sha256 === digest(path.join(root, '.coding-tools/reports/native-first-20261012/parallel-r4-packaged-smoke.json')),
        'RETIRING_EXACT_RESOURCE_AUTHORITY_REQUIRED');
      const files = {};
      const stack = [selectedResources];
      while (stack.length) {
        const folder = stack.pop();
        for (const entry of fs.readdirSync(folder, { withFileTypes: true })) {
          const absolute = path.join(folder, entry.name);
          const relative = path.relative(selectedResources, absolute).split(path.sep).join('/');
          requireState(!entry.isSymbolicLink(), 'RETIRING_PACKAGE_LINK_UNSUPPORTED');
          if (entry.isDirectory()) {
            requireState(!['__pycache__', '.pytest_cache', '.coding-tools'].includes(entry.name), 'RETIRING_PACKAGE_CACHE_DETECTED');
            stack.push(absolute);
          } else {
            requireState(entry.isFile() && !/\.py[co]$/i.test(entry.name), 'RETIRING_PACKAGE_ENTRY_UNSUPPORTED');
            files[relative] = { size_bytes: fs.statSync(absolute).size, sha256: digest(absolute) };
          }
        }
      }
      requireState(Object.keys(files).length === oldResourceSnapshot.file_count
        && Object.entries(oldResourceSnapshot.resources).every(([relative, expected]) => files[relative]?.size_bytes === expected.size_bytes
          && files[relative]?.sha256 === expected.sha256), 'RETIRING_PACKAGE_RESOURCES_CHANGED');
      return { immutable_old_package: true, file_count: Object.keys(files).length, current_source_claim: false };
    }
    const resources = assertExactPackagedResources(path.join(root, 'resources'), selectedResources,
      { separatelyVerifiedTopLevelDirectories: ['control-plane'] });
    const adapter = assertExactControlPlaneAdapter(path.join(root, 'control-plane/control_plane'), path.join(selectedResources, 'control-plane'));
    return { resources, adapter };
  };
  const census = async () => {
    verifySelectedResources();
    const observed = await canonicalLedgerCensus({ paths, workspace: root, allowAcceptancePending: true });
    verifySelectedResources();
    return observed;
  };
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
    const age = Date.now() - fence.capture_completed_at_ms;
    const work = fence.whole_device_census || {};
    const global = fence.global_live_work_by_scope || {};
    const historic = fence.historical_unknown_actions_preserved || [];
    const targetScopes = new Set(targets.map(target => `${target.workspace_id}:${target.workspace_generation}`));
    const blockerByAction = new Map((global.blocking_action_identities || []).map(item => [item.action_id, item]));
    const foreignExpiredBlockers = (global.blocking_action_identities || []).filter(item =>
      item.device_id !== fence.node?.device_id
      && !targetScopes.has(`${item.workspace_id}:${item.workspace_generation}`)
      && item.expired === true
      && item.delivery_state === 'dispatch_unconfirmed');
    const autocad = historic.filter(item => item.workspace_id === targets[1].workspace_id
      && item.workspace_generation === targets[1].workspace_generation);
    const expectedQuarantines = ['act_9db9b985a3d648b5b941f2e13a30ee47',
      'act_52409c69f1b84e08bb3fdd86747f79c3', 'act_3849e259d55546639794cec40f63fea8'].sort();
    requireState(fence.ok === true && fence.service_stable === true && fence.sqlite_integrity_ok === true
      && fence.source_startup_disk_attestation_matches === true && Number.isFinite(age) && age >= 0 && age <= 120_000
      && ['live_open_tasks', 'live_writers', 'queued_actions', 'active_dispatch_actions'].every(key => work[key] === 0)
      && (global.active_actions || []).every(item => foreignExpiredBlockers.some(candidate =>
        candidate.device_id === item.device_id && candidate.workspace_id === item.workspace_id
        && candidate.workspace_generation === item.workspace_generation && candidate.delivery_state === item.delivery_state))
      && (global.blocking_action_identities || []).every(item => foreignExpiredBlockers.some(candidate => candidate.action_id === item.action_id))
      && fence.node?.device_id === '4c4b7a5b-7744-49ae-a490-78a528a00471'
      && targets.every(target => Object.values(fence.expected_current_scopes || {}).some(item => item.expected_workspace_id === target.workspace_id
        && item.expected_generation === target.workspace_generation && item.active_bindings?.length === 1
        && item.active_registrations?.length === 1 && item.active_bindings[0].workspace_id === target.workspace_id
        && item.active_bindings[0].workspace_generation === target.workspace_generation
        && item.active_registrations[0].workspace_id === target.workspace_id
        && item.active_registrations[0].workspace_generation === target.workspace_generation))
      && autocad.length === 3 && JSON.stringify(autocad.map(item => item.action_id).sort()) === JSON.stringify(expectedQuarantines)
      && historic.every(item => item.delivery_state === 'reconcile_required' && item.disposition === 'quarantined_unknown'
        && item.expired === true && Number.isInteger(item.reconciled_at_ms) && item.reconciled_at_ms > 0)
      && work.unsettled_actions === historic.length && work.reconciliation_required_actions === historic.length,
      'FRESH_EXACT_IDLE_SERVER_CENSUS_REQUIRED');
    return { receipt_path: file, sha256: digest(file), capture_completed_at_ms: fence.capture_completed_at_ms,
      admission_fence_claimed: false, preserved_autocad_quarantines: expectedQuarantines,
      foreign_expired_blockers: foreignExpiredBlockers.map(item => item.action_id).sort() };
  };
  let result;
  if (mode === 'status' || mode === 'timefix-old-stopped-observation') {
    if (mode === 'timefix-old-stopped-observation') requireState(fs.existsSync(path.join(__dirname, 'timefix-old-stop-intent.json')), 'ORIGINAL_STOP_INTENT_REQUIRED');
    result = { runtime: summarize(await exact('runtime.lightweight_snapshot')), activation: await exact('runtime.activation_epoch_status'),
      census: await census(), owner: pick(verified.descriptor, ['owner_pid', 'owner_process_start_token', 'instance_id', 'installation_id']),
      preserved_fingerprints: beforeFiles, original_stop_not_replayed: mode === 'timefix-old-stopped-observation' };
  } else {
    requireState(apply, 'EXPLICIT_APPLY_REQUIRED');
    const server = serverFence();
    if (mode === 'stop') {
      const before = await census();
      requireState(idle(before), 'ACTIVE_LOCAL_WORK_PREVENTS_ORDINARY_STOP');
      const beforeRuntime = summarize(await exact('runtime.lightweight_snapshot'));
      const epoch = await exact('runtime.activation_epoch_status');
      requireState(epoch.activation_epoch_id === 'activation-mv5cvpnu-2ddc4f6edfe0487ec46a1594cb87218d'
        && epoch.state === 'READY' && epoch.admission_open === true && beforeRuntime.mcpRunning === true
        && beforeRuntime.nativeAlive === true, 'EXACT_READY_R3_EPOCH_REQUIRED');
      const sandbox = noSandboxProcess();
      const intentPath = path.join(__dirname, 'timefix-old-stop-intent.json');
      requireState(!fs.existsSync(intentPath), 'ORIGINAL_R3_STOP_ALREADY_ATTEMPTED_DO_NOT_REPLAY');
      stopIntentReceipt = intentPath;
      fs.writeFileSync(intentPath, JSON.stringify({ schema_version: 1, operation: 'ordinary-stop-intent', candidate,
        observed_at_ms: Date.now(), owner: expectedOwner, epoch, server, before_census: before,
        preserved_fingerprints: beforeFiles, sandbox, request: { action: 'runtime.stop', options: { manual: true } },
        effect_observed: false, no_replay: true }, null, 2) + '\n', { flag: 'wx' });
      stage = 'ordinary_stop'; mutationStarted = true;
      serverFence();
      const stopped = await client.stop({ manual: true }, expected);
      const stop = receiptFile('timefix-old-stop-result', { runtime: summarize(stopped), owner: expectedOwner, epoch,
        before_census: before, preserved_fingerprints: beforeFiles, historical_acceptance_preserved: true,
        stop_intent_receipt: intentPath, original_stop_not_replayed: true });
      requireState(summarize(stopped).mcpRunning === false, 'ORDINARY_STOP_NOT_CONFIRMED_OBSERVE_WITHOUT_REPLAY');
      result = { stop_result_receipt: stop.report_path, runtime: summarize(stopped), stopped_census: await census(), owner: expectedOwner };
    } else if (mode === 'retire') {
      const observationPath = option('--timefix-old-stopped-observation');
      const observation = read(observationPath);
      requireState(observation.ok === true && observation.operation === 'timefix-old-stopped-observation'
        && observation.candidate.toLowerCase() === oldCandidate.toLowerCase()
        && Object.entries(expectedOwner).every(([key, value]) => observation.receipt.owner[key] === value)
        && Date.now() - observation.observed_at_ms >= 0 && Date.now() - observation.observed_at_ms <= 120_000
        && observation.receipt.original_stop_not_replayed === true
        && observation.receipt.runtime.mcpRunning === false && observation.receipt.runtime.nativeAlive === false
        && observation.receipt.census.safe === true && idle(observation.receipt.census)
        && JSON.stringify(observation.receipt.preserved_fingerprints) === JSON.stringify(beforeFiles), 'FRESH_EXACT_STOPPED_OBSERVATION_REQUIRED');
      const stopReconciliation = receiptFile('timefix-old-retirement-authority', {
        stopped_observation: observationPath, stopped_observation_sha256: digest(observationPath), owner: expectedOwner,
        runtime: observation.receipt.runtime, stopped_census: observation.receipt.census,
        no_stop_dispatched: true, original_stop_not_replayed: true,
        method: 'fresh exact stopped old-r4 owner and quiescent canonical census before r4 handoff'
      }).report_path;
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
      const retirementIntentPath = path.join(__dirname, 'timefix-old-retirement-intent.json');
      const existingRetirementIntent = fs.existsSync(retirementIntentPath) ? read(retirementIntentPath) : null;
      if (existingRetirementIntent) {
        requireState(existingRetirementIntent.operation === 'exact-retirement-intent'
          && JSON.stringify(existingRetirementIntent.owner) === JSON.stringify(expectedOwner)
          && typeof existingRetirementIntent.stopped_observation === 'string'
          && fs.existsSync(existingRetirementIntent.stopped_observation)
          && existingRetirementIntent.no_replay === true, 'ORIGINAL_R3_RETIREMENT_INTENT_MISMATCH');
      }
      serverFence();
      if (!existingRetirementIntent) {
        fs.writeFileSync(retirementIntentPath, JSON.stringify({ schema_version: 1, operation: 'exact-retirement-intent',
          observed_at_ms: Date.now(), owner: expectedOwner, stopped_observation: observationPath, server, no_replay: true }, null, 2) + '\n', { flag: 'wx' });
      }
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
      serverFence();
      stage = 'exact_host_retirement';
      const retirement = await terminateExactProcessTree(hostIdentity, { observeProcessIdentity: observeLifecycleProcessIdentity });
      requireState(JSON.stringify(beforeFiles) === JSON.stringify(fingerprints()), 'POLICY_CHANGED_DURING_HANDOFF');
      result = { retirement, owner: expectedOwner, ui_stopped: finalUi, stopped_census: finalCensus, stop_reconciliation: stopReconciliation,
        manifest_sha256: manifestHash, preserved_fingerprints: beforeFiles, durable_state_deleted: false, server_census: server, retirement_intent_receipt: retirementIntentPath,
        sandbox_observation: finalSandbox, final_candidate: newCandidate,
        final_package: { executable_sha256: parity.executable_sha256, app_asar_sha256: parity.app_asar_sha256 } };
    } else if (mode === 'refresh') {
      requireState(idle(await census()), 'ACTIVE_LOCAL_WORK_PREVENTS_REFRESH');
      const refreshIntent = path.join(__dirname, 'ordinary-r4-refresh-intent.json');
      requireState(!fs.existsSync(refreshIntent), 'ORIGINAL_R4_REFRESH_ALREADY_ATTEMPTED_OBSERVE_ONLY');
      fs.writeFileSync(refreshIntent, JSON.stringify({ schema_version: 1, operation: 'full-clean-refresh-intent',
        observed_at_ms: Date.now(), owner: pick(verified.descriptor, ['owner_pid','owner_process_start_token','instance_id','installation_id']),
        server, no_replay: true }, null, 2) + '\n', { flag: 'wx' });
      stage = 'full_clean_refresh'; mutationStarted = true;
      const refreshed = await client.restart({ refresh: true, mode: 'full_clean_refresh', allowAcceptancePending: true,
        reason: 'operator_parallel_native_first_r4_preserve_history' }, expected);
      result = { runtime: summarize(refreshed), activation: await exact('runtime.activation_epoch_status') };
    } else if (mode === 'complete') {
      const epoch = option('--epoch');
      requireState(/^activation-[A-Za-z0-9_-]+$/.test(epoch || '') && (await exact('runtime.activation_epoch_status')).activation_epoch_id === epoch, 'EXACT_NEW_EPOCH_REQUIRED');
      stage = 'activation_completion'; mutationStarted = true;
      result = { result: await exact('runtime.complete_activation_epoch', [epoch]), runtime: summarize(await exact('runtime.lightweight_snapshot')),
        activation: await exact('runtime.activation_epoch_status'), census: await census() };
    } else if (['canary-build', 'canary-overlap', 'final-policy'].includes(mode)) {
      const epoch = option('--epoch');
      requireState(/^activation-[A-Za-z0-9_-]+$/.test(epoch || ''), 'EXACT_READY_EPOCH_REQUIRED');
      const verifyReady = async () => {
        requireState(sameProcessIdentity(hostIdentity, await observeLifecycleProcessIdentity(hostIdentity.pid)), 'HOST_START_IDENTITY_CHANGED');
        const activation = await exact('runtime.activation_epoch_status');
        requireState(activation.activation_epoch_id === epoch && activation.state === 'READY'
          && activation.admission_open === true, 'EXACT_READY_ACTIVATION_REQUIRED');
        return activation;
      };
      await verifyReady();
      serverFence();
      requireState(idle(await census()), 'ACTIVE_LOCAL_WORK_PREVENTS_CANARY_POLICY_CHANGE');
      const { ControlPlaneEnrollmentService } = load('controlPlaneEnrollment');
      const enrollment = new ControlPlaneEnrollmentService({ paths, experimentalWindowsSandbox: true });
      const scopeOf = target => ({ workspaceId: target.workspace_id, workspaceGeneration: target.workspace_generation });
      const baseline = [];
      for (const target of targets) {
        const observed = await enrollment.inspectLocalExecPolicy(scopeOf(target));
        requireState(observed.state === 'enabled' && observed.workspace_id === target.workspace_id
          && observed.workspace_generation === target.workspace_generation && Array.isArray(observed.native_argv_prefixes),
        'EXACT_EXISTING_EXEC_POLICY_REQUIRED');
        baseline.push({ workspace_label: path.basename(target.workspace_path), workspace_id: target.workspace_id,
          workspace_generation: target.workspace_generation, policy: observed });
      }
      if (mode === 'final-policy') {
        stage = 'reviewed_final_policy_baseline';
        const baselinePath = option('--baseline-receipt');
        const original = read(baselinePath);
        requireState(path.resolve(baselinePath).toLowerCase() === path.join(root,
          '.coding-tools/reports/native-first-20261012/parallel-old-r4-transition/canary-policy-baseline-1791809168575-0779bf7e.json').toLowerCase()
          && digest(baselinePath) === '126534d0440e0497932c96c4dbe6dcc097794c9780e4014f3b7cd0da461a6298'
          && original.ok === true && original.operation === 'canary-policy-baseline'
          && original.candidate.toLowerCase() === oldCandidate.toLowerCase()
          && original.receipt.approval_set === 'codex-build'
          && original.receipt.activation_epoch_id === 'activation-mv5cvpnu-2ddc4f6edfe0487ec46a1594cb87218d'
          && original.parity_proof_sha256 === oldResourceSnapshot.old_parity_proof_sha256 && original.smoke_proof_sha256 === oldResourceSnapshot.old_smoke_proof_sha256
          && original.receipt.targets?.length === 2, 'EXACT_ORIGINAL_CANARY_BASELINE_REQUIRED');
        const canaryPrefixes = [['node', 'trusted-build.js'], ['node', 'tests/fixtures/parallel-native-overlap-20261012/hold.cjs']];
        const reviewed = baseline.map(current => {
          const matches = original.receipt.targets.filter(item => item.workspace_id === current.workspace_id
            && item.workspace_generation === current.workspace_generation && item.workspace_label === current.workspace_label);
          requireState(matches.length === 1 && matches[0].policy.state === 'enabled'
            && matches[0].policy.workspace_id === current.workspace_id
            && matches[0].policy.workspace_generation === current.workspace_generation
            && matches[0].policy.execution_mode === 'native_first' && Array.isArray(matches[0].policy.native_argv_prefixes),
          'EXACT_ORIGINAL_NATIVE_FIRST_POLICY_REQUIRED');
          const prefixes = matches[0].policy.native_argv_prefixes;
          const encode = prefix => JSON.stringify(prefix);
          const removed = current.policy.native_argv_prefixes.filter(prefix => !prefixes.some(item => encode(item) === encode(prefix)));
          requireState(removed.every(prefix => canaryPrefixes.some(item => encode(item) === encode(prefix)))
            && JSON.stringify(current.policy.native_argv_prefixes.filter(prefix => !removed.some(item => encode(item) === encode(prefix))))
              === JSON.stringify(prefixes), 'UNRELATED_NATIVE_APPROVAL_CHANGE_PREVENTS_RESTORE');
          return { ...current, prefixes, removed };
        });
        canaryPolicyBaselineReceipt = baselinePath;
        result = { activation_epoch_id: epoch, baseline_activation_epoch_id: original.receipt.activation_epoch_id,
          baseline_receipt: baselinePath, baseline_sha256: digest(baselinePath), targets: [], cross_package_restoration: true,
          old_package_parity_sha256: oldResourceSnapshot.old_parity_proof_sha256, new_package_parity_sha256: digest(parityPath) };
        for (const target of targets) {
          const reviewedTarget = reviewed.find(item => item.workspace_id === target.workspace_id);
          await verifyReady();
          stage = `restore_native_first_${target.workspace_id}`; mutationStarted = true;
          await enrollment.installStandingWorkspaceExecPolicy({ ...scopeOf(target), executionMode: 'native_first',
            nativeArgvPrefixes: reviewedTarget.prefixes, probeSandbox: false, replaceExisting: true });
          const observed = await enrollment.inspectLocalExecPolicy(scopeOf(target));
          requireState(observed.state === 'enabled' && observed.workspace_id === target.workspace_id
            && observed.workspace_generation === target.workspace_generation && observed.execution_mode === 'native_first'
            && JSON.stringify(observed.native_argv_prefixes) === JSON.stringify(reviewedTarget.prefixes), 'FINAL_NATIVE_FIRST_RECEIPT_NOT_EXACT');
          const record = { workspace_label: reviewedTarget.workspace_label, workspace_id: target.workspace_id,
            workspace_generation: target.workspace_generation, removed_canary_argv: reviewedTarget.removed, policy: observed };
          result.targets.push(record);
          canaryPolicyProgressReceipts.push(receiptFile('final-policy-target', record).report_path);
        }
        result.only_canary_additions_removed = true;
      } else {
        const approvalSet = mode === 'canary-build' ? 'codex-build' : 'overlap';
        const fixtureManifestPath = option('--fixture-manifest');
        read(fixtureManifestPath);
        stage = 'canary_policy_baseline';
        canaryPolicyBaselineReceipt = receiptFile('canary-policy-baseline', { activation_epoch_id: epoch,
          approval_set: approvalSet, fixture_manifest_path: fixtureManifestPath, fixture_manifest_sha256: digest(fixtureManifestPath),
          targets: baseline }, { mutating: false, parity_proof_sha256: digest(parityPath), smoke_proof_sha256: digest(smokePath) }).report_path;
        const { installCanaryApprovals } = require(path.join(root,
          '.coding-tools/reports/parallel-native-first-20261012/canary/canary-policy-approvals.cjs'));
        stage = `install_${approvalSet}_native_approvals`; mutationStarted = true;
        result = await installCanaryApprovals({ enrollment, targets, expectedEpoch: epoch, observeActivation: verifyReady,
          approvalSet, fixtureManifestPath, onVerifiedTarget: record => {
            canaryPolicyProgressReceipts.push(receiptFile('canary-policy-target', record).report_path);
          } });
        result.baseline_receipt = canaryPolicyBaselineReceipt;
        result.baseline_sha256 = digest(canaryPolicyBaselineReceipt);
      }
    } else if (mode === 'policies') {
      const currentEpoch = await exact('runtime.activation_epoch_status');
      requireState(currentEpoch.state === 'READY' && currentEpoch.admission_open === true && currentEpoch.activation_epoch_id === option('--epoch'), 'EXACT_READY_R4_EPOCH_REQUIRED');
      requireState(idle(await census()), 'ACTIVE_LOCAL_WORK_PREVENTS_POLICY_UPDATE');
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
    ...(canaryPolicyBaselineReceipt ? { canary_policy_baseline_receipt: canaryPolicyBaselineReceipt } : {}),
    ...(canaryPolicyProgressReceipts.length ? { verified_policy_target_receipts: canaryPolicyProgressReceipts } : {}),
    ...(scopedPollIntentReceipt ? { original_scoped_poll_intent_receipt: scopedPollIntentReceipt } : {}),
    ...(readReconciliationIntentReceipt ? { original_read_reconciliation_intent_receipt: readReconciliationIntentReceipt } : {}),

    retry_instruction: mutationStarted ? 'Observe exact current state and original operation receipt; do not replay uncertain mutations.' : 'Resolve the read-only gate before applying.' };
  report.report_path = path.join(__dirname, `${mode}-failure-${Date.now()}.json`);
  fs.writeFileSync(report.report_path, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  process.stderr.write(JSON.stringify(report) + '\n', () => process.exit(1));
});
