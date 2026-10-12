'use strict';
// Bounded r5 -> r7 switch for the approved DaoChienThang profile only.
// Policy sync requires the separate exact one-hour server renewal receipt.
// No server, task-acceptance, release, or Windows feature mutations.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawn, spawnSync } = require('node:child_process');
const repo = path.resolve(__dirname, '../../../..');
const services = path.join(repo, 'electron/services');
const { createRuntimePaths } = require(path.join(services, 'runtimePaths'));
const { RecoveryIpcClient, loadRecoveryDescriptor } = require(path.join(services, 'recoveryIpc'));
const { descriptorMatchesInstallation, descriptorRequestOptions } = require(path.join(services, 'recoveryHostLauncher'));
const { observeLifecycleProcessIdentity, sameProcessIdentity, terminateExactProcessTree, waitForExactProcessExit } = require(path.join(services, 'processIdentity'));
const { canonicalLedgerCensus } = require(path.join(services, 'fullCleanActivation'));
const { ControlPlaneEnrollmentService, safeEnrollmentEnvironment } = require(path.join(services, 'controlPlaneEnrollment'));
const dataRoot = 'C:\\Users\\daoth\\AppData\\Roaming\\web-mcp-assistant';
const roots = {
  r5: path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-exec-coldstart-1011-r5/win-unpacked'),
  r7: path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-unified-setup-1011-r7/win-unpacked')
};
const target = { workspaceId: 'workspace_dda1d78e9a21402aa6213f72af64f788', workspaceGeneration: 'generation_c2f13e8d02344cf6a38a3f42ecfa59b6' };
const bindingId = 'bind_3e05bf64cb3e4bab93d930ae1692bebb';
const awaitingAcceptance = ['95e909f0040a448faa9f1f3257e2ee2c'];
const initial = {
  installation_id: 'f9558a082121b56759553627fc60ee93cf624a94e8a1082c32e65b92b153bd86',
  instance_id: '7e832a6fa665a671734627676b0fd7cb',
  owner: { pid: 1936, process_start_token: '134361837165089850' },
  ui: { pid: 852, process_start_token: '134361837278635530', instance_id: 'dba7181a98a08ffcc46e48b2d47b1199' },
  native: { pid: 9632, process_start_token: '134361837188077490' },
  agent: { pid: 10336, process_start_token: '134361837362242930' }
};
const sharedHashes = {
  'resources/resources/control-plane/node_agent.py': '7ac20204eb742719db1665651e97d52add481b691ba1cfcca907f35fdfd9ff40',
  'resources/resources/control-plane/recovery_exec_bridge.cjs': '78951d8b0e0be005ce2b526ed4d8f139c304be5e083b8a9821fe6cc805321ba9',
  'resources/resources/native-python/python.exe': '4d6f5f81a4bca11191c4c7c6b43632694d0a4ce74e068619d8fdc161d469859a',
  'resources/resources/coding-tools-mcp/coding_tools_mcp/activation_ledger_census.py': 'a2e9e3b538c33cb22bb707718ef7df2683dac81da07f69ef91ef7ce59dd3b3de'
};
const hashes = {
  r5: { ...sharedHashes, 'resources/app.asar': '4e9c51c4952b5cc491f42a40859d0e78911356453643023ab740ec06343e6f62', 'Coding Tools MCP.exe': '8726f7fc2bbe2b1dc22c87decb8be8c54690c5650bc2d5102f76755b75c53e95' },
  r7: { ...sharedHashes, 'resources/app.asar': '16151d40c7b1735be9d0502ed14c6885656bfaf41f82a4148e07c03caa123c67', 'Coding Tools MCP.exe': 'e2c20f9e93f43604fdd3d7ee6a366f0feecf8b00b5a4d410a7ca60a08a7bc871' }
};
const serviceHashes = {
  runtimePaths: 'a28fe23a10daa10baeb9c437ccee13cff2c1d28585d1c6daa3e5a23844d23474',
  recoveryIpc: 'c9c451c36b764cf4a23cc22f9c435507f0505e65858170560de38cbe2651684b',
  recoveryHostLauncher: '92cb2478ae940c737a8e8a007181a9fa410b1eeb1e26a06b5bb07e1043ebf60a',
  processIdentity: 'a0ee2b08cbe4108c352ba14b9532ceaf581497f745a2adda7924c819a972809f',
  fullCleanActivation: '286df402bad9414b8414fb1800dacf7f35cac6795fee0971e9d04ce6839e7c1d',
  controlPlaneEnrollment: 'c72766572150b5f2ce1e7ed7f976eb408ff3a75a7191951fddf0ccb7a28c6405'
};
const evidence = path.join(__dirname, 'windows-activation.jsonl');
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const fail = code => { throw Object.assign(new Error(), { code }); };
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const safeText = value => String(value || '').replace(/[^a-zA-Z0-9_.:-]/g, '').slice(0, 128);
function readJson(file, limit = 1024 * 1024) {
  const raw = fs.readFileSync(file, 'utf8');
  if (Buffer.byteLength(raw) > limit) fail('EVIDENCE_SIZE_EXCEEDED');
  return JSON.parse(raw);
}
function emit(value) {
  const row = { observed_at: new Date().toISOString(), ...value };
  fs.appendFileSync(evidence, `${JSON.stringify(row)}\n`);
  process.stdout.write(`${JSON.stringify(row)}\n`);
  return row;
}
function pathsFor(tag) {
  return createRuntimePaths({ dataRoot, appRoot: path.join(roots[tag], 'resources/app.asar'), resourcesRoot: path.join(roots[tag], 'resources/resources'), runtimeMode: 'packaged', executablePath: path.join(roots[tag], 'Coding Tools MCP.exe') });
}
function verifyFiles() {
  if (path.resolve(process.env.APPDATA || '', 'web-mcp-assistant').toLowerCase() !== dataRoot.toLowerCase()) fail('PROFILE_MISMATCH');
  for (const tag of ['r5', 'r7']) for (const [file, expected] of Object.entries(hashes[tag])) {
    if (sha(path.join(roots[tag], file)) !== expected) fail('CANDIDATE_HASH_CHANGED');
  }
  for (const [name, expected] of Object.entries(serviceHashes)) if (sha(path.join(services, `${name}.js`)) !== expected) fail('ACTIVATION_HELPER_SERVICE_CHANGED');
  const r7 = readJson(path.join(__dirname, '..', 'windows-candidate.json'));
  if (r7.ok !== true || r7.candidate !== roots.r7 || r7.app_asar_sha256 !== hashes.r7['resources/app.asar'] || r7.executable_sha256 !== hashes.r7['Coding Tools MCP.exe'] || r7.files.some(file => file.matches !== true)) fail('R7_SOURCE_PARITY_RECEIPT_MISMATCH');
}
function renewalGuard() {
  const receipt = readJson(path.join(__dirname, 'server-authority-renewal.json'), 32768);
  const assignment = receipt.policy_assignment;
  if (receipt.phase !== 'same_scope_renewal_complete' || receipt.ok !== true || receipt.duration_ms !== 3600000 || receipt.binding_id !== bindingId || receipt.expires_at_ms !== receipt.requested_at_ms + 3600000 || receipt.expires_at_ms <= Date.now() || receipt.requested_at_ms > Date.now() || assignment?.workspace_id !== target.workspaceId || assignment.workspace_generation !== target.workspaceGeneration || assignment.device_id !== '72ceec2d-e3f2-472f-8e3c-99fffe053035' || assignment.expires_at_ms !== receipt.expires_at_ms || assignment.context_id !== receipt.context_id || receipt.admission !== 'scoped_pilot' || receipt.service_grant_changed !== false) fail('EXACT_UNEXPIRED_SERVER_RENEWAL_REQUIRED');
  if (receipt.state?.queued_actions !== 0 || receipt.state.accepted_actions !== 0 || receipt.state.open_writers !== 0 || receipt.state.open_tasks !== 0) fail('RENEWAL_SERVER_CENSUS_NOT_QUIESCENT');
  return receipt;
}
function mutationGuard(authority = 'closure') {
  if (!process.argv.includes('--operator-approved') || !fs.existsSync(path.join(__dirname, 'authorization.md'))) fail('OPERATOR_AUTHORIZATION_REQUIRED');
  if (authority === 'renewal') { verifyFiles(); return renewalGuard(); }
  const receipt = readJson(path.join(__dirname, 'server-intake-closed.json'), 16384);
  const age = Date.now() - Number(receipt.observed_at_ms);
  if (receipt.phase !== 'intake_closed' || receipt.admission !== 'recovery' || receipt.host !== '100.116.112.22' || receipt.service !== 'codex-control-plane.service' || receipt.ok !== true || !Number.isFinite(age) || age < 0 || age >= 10 * 60 * 1000) fail('FRESH_SERVER_INTAKE_CLOSURE_REQUIRED');
  verifyFiles();
}
function descriptorIdentity(d) {
  return { installation_id: d.installation_id, instance_id: d.instance_id, owner_pid: d.owner_pid, owner_process_start_token: d.owner_process_start_token };
}
async function observedDescriptor() {
  const paths = pathsFor('r5');
  let descriptor;
  try { descriptor = loadRecoveryDescriptor(paths); }
  catch (error) {
    if (error.code !== 'RECOVERY_DESCRIPTOR_STALE') throw error;
    descriptor = readJson(paths.recoveryHostDescriptorFile(), 16384);
    if (descriptor.version !== 1 || descriptor.host !== '127.0.0.1' || descriptor.owner !== 'recovery-host' || !/^[a-f0-9]{64}$/.test(descriptor.installation_id || '') || !/^[a-f0-9]{32}$/.test(descriptor.instance_id || '') || !Number.isInteger(descriptor.owner_pid)) fail('RECOVERY_DESCRIPTOR_INVALID');
  }
  const owner = await observeLifecycleProcessIdentity(descriptor.owner_pid);
  if (owner.state === 'unavailable') fail('PROCESS_IDENTITY_UNVERIFIED');
  if (owner.state === 'live' && !sameProcessIdentity({ pid: descriptor.owner_pid, process_start_token: descriptor.owner_process_start_token }, owner)) fail('RECOVERY_OWNER_IDENTITY_CHANGED');
  const tag = ['r5', 'r7'].find(value => descriptorMatchesInstallation(descriptor, pathsFor(value).runtimeIdentity()));
  if (!tag) fail('UNEXPECTED_INSTALLATION');
  return { descriptor, owner, tag, paths: pathsFor(tag) };
}
function authenticated(observed) {
  return { client: new RecoveryIpcClient({ paths: observed.paths }), options: descriptorRequestOptions(observed.descriptor) };
}
function epochSafe(epoch) {
  return { activation_epoch_id: epoch?.activation_epoch_id, state: epoch?.state, admission_open: epoch?.admission_open, update_incomplete: epoch?.update_incomplete, expires_at_unix_ms: epoch?.expires_at_unix_ms };
}
function lastReceipt(phase, tag) {
  if (!fs.existsSync(evidence)) return null;
  return fs.readFileSync(evidence, 'utf8').trim().split(/\r?\n/).filter(Boolean).map(JSON.parse).findLast(row => row.phase === phase && (!tag || row.tag === tag));
}
function pinFor(tag) {
  const row = lastReceipt('status', tag) || lastReceipt('candidate_started', tag);
  if (tag === 'r5' && !row) return initial;
  if (!row?.descriptor || !row?.owner || !row?.ui?.identity) fail('R7_ROLLBACK_IDENTITY_RECEIPT_REQUIRED');
  return { ...row.descriptor, owner: row.owner, ui: { ...row.ui.identity, instance_id: row.ui.instance_id } };
}
function assertDescriptorPin(observed, pin) {
  if (observed.descriptor.installation_id !== pin.installation_id || observed.descriptor.instance_id !== pin.instance_id || observed.descriptor.owner_pid !== pin.owner.pid || observed.descriptor.owner_process_start_token !== pin.owner.process_start_token) fail('PINNED_RECOVERY_DESCRIPTOR_CHANGED');
}
async function agentObservation(tag) {
  const receipt = lastReceipt('agent_spawned', tag) || (tag === 'r5' ? { identity: initial.agent, node_agent: pathsFor('r5').controlPlaneNodeAgent() } : null);
  if (!receipt?.identity || receipt.node_agent !== pathsFor(tag).controlPlaneNodeAgent()) return { receipt: null, identity: { state: 'absent', pid: null }, summary: null };
  const identity = await observeLifecycleProcessIdentity(receipt.identity.pid);
  if (identity.state === 'unavailable' || (identity.state === 'live' && !sameProcessIdentity(receipt.identity, identity))) fail('CONNECTED_AGENT_IDENTITY_CHANGED');
  const statusFile = path.join(dataRoot, 'control-plane-connected-agent-status.json');
  const raw = fs.existsSync(statusFile) ? readJson(statusFile) : {};
  const summary = { agent_pid: raw.agent_pid, last_iteration_state: safeText(raw.last_iteration_state), last_heartbeat_state: safeText(raw.last_heartbeat_state), last_heartbeat_at_ms: raw.last_heartbeat_at_ms };
  if (identity.state === 'live' && raw.agent_pid !== identity.pid) fail('CONNECTED_AGENT_STATUS_IDENTITY_CHANGED');
  return { receipt, identity, summary };
}
async function inspectRuntime(observed, phase = 'status') {
  if (observed.owner.state !== 'live') return emit({ phase, tag: observed.tag, descriptor: descriptorIdentity(observed.descriptor), owner: observed.owner });
  const r = authenticated(observed);
  const status = await r.client.status({ ...r.options, fresh: true });
  const snapshot = await r.client.call('runtime.lightweight_snapshot', [], r.options);
  const ui = status.electron_ui_recovery;
  const identity = ui?.pid ? await observeLifecycleProcessIdentity(ui.pid) : { state: 'absent', pid: null };
  if (identity.state === 'unavailable') fail('UI_IDENTITY_UNVERIFIED');
  const state = readJson(observed.paths.stateFile());
  const components = {};
  for (const name of ['native', 'tunnel']) {
    const pid = Number(state[`${name}Pid`] || 0);
    const seen = pid ? await observeLifecycleProcessIdentity(pid) : { state: 'absent', pid: null };
    if (seen.state === 'unavailable' || (seen.state === 'live' && !sameProcessIdentity({ pid, process_start_token: state[`${name}ProcessStartToken`] }, seen))) fail('MANAGED_PROCESS_IDENTITY_CHANGED');
    components[name] = seen;
  }
  const agent = await agentObservation(observed.tag);
  return emit({ phase, tag: observed.tag, descriptor: descriptorIdentity(observed.descriptor), owner: observed.owner, ui: { pid: ui?.pid, instance_id: ui?.instance_id, alive: ui?.alive, registered: ui?.registered, ui_installation_id: ui?.ui_installation_id, identity }, components, epoch: epochSafe(status.activation_epoch), fully_ready: snapshot.fullyReady, local_ready: snapshot.localReady, components_ready: snapshot.componentsReady, central_connected: snapshot.centralConnected, authority_ready: snapshot.authorityReady, update_incomplete: snapshot.updateIncomplete, failure_kind: safeText(snapshot.failureKind), agent: { identity: agent.identity, ...agent.summary } });
}
function censusSummary(census) {
  return { safe: census.safe, code: census.code, counts: census.counts, lifecycle: census.lifecycle, reason: census.reason, ledger_mutated: census.mutated_canonical_ledger, content_free: census.content_free, census_fingerprint: census.census_fingerprint, snapshot: { logical_sha256: census.snapshot.logical_sha256, integrity_check: census.snapshot.integrity_check } };
}
function assertCensus(census, liveAllowed = false) {
  const pending = census.lifecycle.awaiting_acceptance_runs.slice().sort();
  if (pending.join(',') !== awaitingAcceptance.slice().sort().join(',')) fail('PENDING_ACCEPTANCE_SET_CHANGED');
  if (census.mutated_canonical_ledger || !census.content_free) fail('CENSUS_CONTRACT_INVALID');
  if (liveAllowed && census.code === 'RUNTIME_BUSY' && census.lifecycle.blockers.join(',') === 'live_runtime_state_process') return;
  if (!census.safe) fail(census.code || 'CENSUS_REFUSED');
}
async function preflight() {
  verifyFiles();
  const observed = await observedDescriptor();
  if (observed.tag === 'r5') assertDescriptorPin(observed, pinFor('r5'));
  await inspectRuntime(observed, 'preflight');
  const census = await canonicalLedgerCensus({ paths: observed.paths, workspace: repo, allowAcceptancePending: true });
  emit({ phase: 'preflight_census', tag: observed.tag, ...censusSummary(census) });
  assertCensus(census, observed.owner.state === 'live');
}
async function retireAgent(tag) {
  const agent = await agentObservation(tag);
  if (agent.identity.state === 'absent') return;
  if (agent.summary.last_iteration_state !== 'completed') fail('CONNECTED_AGENT_NOT_QUIESCENT');
  mutationGuard();
  const result = await terminateExactProcessTree(agent.receipt.identity, { includeDescendants: false });
  emit({ phase: 'agent_retired', tag, identity: agent.receipt.identity, result });
}
async function switchTo(to) {
  mutationGuard();
  const before = await observedDescriptor();
  if (before.tag === to && before.owner.state === 'live') { emit({ phase: 'switch_already_applied', tag: to, owner: before.owner }); return; }
  const from = to === 'r7' ? 'r5' : 'r7';
  if (before.tag !== from) fail('SWITCH_SOURCE_INSTALLATION_MISMATCH');
  const pin = pinFor(from);
  assertDescriptorPin(before, pin);
  // Root has closed server intake. Retire the exact external poller before UI/native.
  await retireAgent(from);
  if (before.owner.state === 'live') {
    const r = authenticated(before);
    const status = await r.client.status({ ...r.options, fresh: true });
    const ui = status.electron_ui_recovery;
    if (ui?.pid !== pin.ui.pid || ui.instance_id !== pin.ui.instance_id || ui.ui_installation_id !== pin.installation_id) fail('PINNED_UI_IDENTITY_CHANGED');
    const identity = await observeLifecycleProcessIdentity(ui.pid);
    if (identity.state === 'live') {
      if (!sameProcessIdentity(pin.ui, identity)) fail('PINNED_UI_PROCESS_CHANGED');
      mutationGuard();
      await r.client.call('client.suppress_ui_recovery', [{ instance_id: ui.instance_id, reason: 'operator_quit' }], r.options);
      const env = { ...process.env }; delete env.ELECTRON_RUN_AS_NODE;
      const signal = spawnSync(before.paths.executablePath(), [`--dev-ui-stop=${ui.instance_id}`], { env, windowsHide: true, timeout: 15000, stdio: 'ignore' });
      if (signal.status !== 0) fail('UI_STOP_SIGNAL_FAILED');
      await waitForExactProcessExit(identity, { timeoutMs: 15000 });
    } else if (identity.state !== 'absent') fail('UI_PROCESS_IDENTITY_UNVERIFIED');
    mutationGuard();
    await r.client.stop({ manual: true }, r.options);
    emit({ phase: 'runtime_stopped', tag: from, exact_identity_verified: true });
  }
  const census = await canonicalLedgerCensus({ paths: before.paths, workspace: repo, allowAcceptancePending: true, holdExclusive: true });
  try {
    emit({ phase: 'stopped_census', tag: from, ...censusSummary(census) });
    assertCensus(census);
    const current = await observedDescriptor(); assertDescriptorPin(current, pin);
    mutationGuard();
    if (current.owner.state === 'live') await terminateExactProcessTree(pin.owner, { includeDescendants: false });
    const env = { ...process.env }; delete env.ELECTRON_RUN_AS_NODE;
    const child = spawn(pathsFor(to).executablePath(), [], { env, windowsHide: true, detached: true, stdio: 'ignore' });
    await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); }); child.unref();
    emit({ phase: 'candidate_spawned', tag: to, pid: child.pid, candidate: roots[to], acceptance_pending_preserved: true });
  } finally { await census.release_exclusive_gate(); }
  const deadline = Date.now() + 45000;
  while (Date.now() < deadline) {
    try {
      const live = await observedDescriptor();
      if (live.tag === to && live.owner.state === 'live') { await inspectRuntime(live, 'candidate_started'); return; }
    } catch (error) { if (!['RECOVERY_DESCRIPTOR_STALE', 'RECOVERY_DESCRIPTOR_MISSING', 'RECOVERY_HOST_UNAVAILABLE', 'RECOVERY_TIMEOUT'].includes(error.code)) throw error; }
    await wait(500);
  }
  fail('NEW_CANDIDATE_START_NOT_OBSERVED');
}
async function refresh(tag = 'r7') {
  mutationGuard(tag === 'r7' ? 'renewal' : 'closure');
  const observed = await observedDescriptor();
  if (observed.tag !== tag || observed.owner.state !== 'live') fail('REFRESH_TARGET_HOST_NOT_LIVE');
  const r = authenticated(observed);
  const result = await r.client.restart({ refresh: true, mode: 'full_clean_refresh', sourceCheckpoint: null, allowAcceptancePending: true, reason: `operator approved ${tag === 'r7' ? 'r7 unified setup activation' : 'r5 rollback'}, preserving pending acceptance` }, { ...r.options, timeout: 120000 });
  emit({ phase: 'refresh', tag, state: safeText(result.state), epoch: result.activation_epoch_id });
}
async function startAgent(tag = 'r7') {
  const authority = tag === 'r7' ? 'renewal' : 'closure';
  mutationGuard(authority);
  const observed = await observedDescriptor();
  if (observed.tag !== tag || observed.owner.state !== 'live') fail('AGENT_TARGET_HOST_NOT_LIVE');
  const oldAgent = await agentObservation(tag === 'r7' ? 'r5' : 'r7');
  if (oldAgent.identity.state !== 'absent') fail('OTHER_CANDIDATE_AGENT_STILL_LIVE');
  const prior = await agentObservation(tag);
  if (prior.identity.state === 'live') { emit({ phase: 'agent_already_live', tag, identity: prior.identity }); return; }
  const service = new ControlPlaneEnrollmentService({ paths: observed.paths });
  const files = await service.inspectStandingWorkspaceFilePolicies();
  if (![files.file_read, files.approved_patch].every(policy => policy?.enabled === true && policy.workspace_id === target.workspaceId && policy.workspace_generation === target.workspaceGeneration)) fail('STANDING_FILE_POLICY_TARGET_MISMATCH');
  const output = fs.openSync(path.join(__dirname, `${tag}-agent.stdout.jsonl`), 'a');
  const errors = fs.openSync(path.join(__dirname, `${tag}-agent.stderr.log`), 'a');
  let child;
  try {
    mutationGuard(authority);
    child = spawn(observed.paths.portablePython(), ['-I', '-u', observed.paths.controlPlaneNodeAgent(), 'run-connected-agent', '--config', observed.paths.controlPlaneNodeConfigFile(), '--workspace-registry', observed.paths.controlPlaneWorkspaceRegistryFile(), '--project-root', service.agentProjectRoot, '--node', observed.paths.executablePath(), '--runtime-mode', 'packaged', '--interval-seconds', '15', '--max-backoff-seconds', '60', '--max-iterations', '200'], { cwd: service.agentProjectRoot, env: safeEnrollmentEnvironment(process.env), windowsHide: true, detached: true, stdio: ['ignore', output, errors] });
    await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); }); child.unref();
  } finally { fs.closeSync(output); fs.closeSync(errors); }
  const identity = await observeLifecycleProcessIdentity(child.pid);
  if (identity.state !== 'live') fail('CONNECTED_AGENT_NOT_LIVE');
  emit({ phase: 'agent_spawned', tag, identity, executable: observed.paths.portablePython(), node_agent: observed.paths.controlPlaneNodeAgent(), candidate: roots[tag], interval_seconds: 15, max_iterations: 200 });
}
function targetPolicyReady(policy) {
  return policy?.state === 'enabled' && policy.enabled === true && policy.workspace_id === target.workspaceId && policy.workspace_generation === target.workspaceGeneration;
}
function policySafe(policy) {
  return { state: safeText(policy?.state), enabled: policy?.enabled === true, workspace_id: policy?.workspace_id, workspace_generation: policy?.workspace_generation, policy_sha256: policy?.policy_sha256, allowed_argv_prefix_count: policy?.allowed_argv_prefix_count, allowed_argv_prefixes_sha256: policy?.allowed_argv_prefixes_sha256 };
}
function sandboxSafe(sandbox) {
  return { state: safeText(sandbox?.state), backend: safeText(sandbox?.backend), reason: safeText(sandbox?.reason), child_process_spawn: sandbox?.child_process_spawn, binary_sha256: sandbox?.binary_sha256, source_commit: sandbox?.source_commit };
}
async function installPolicy() {
  const renewal = mutationGuard('renewal');
  const observed = await observedDescriptor();
  if (observed.tag !== 'r7' || observed.owner.state !== 'live') fail('R7_HOST_NOT_LIVE');
  const service = new ControlPlaneEnrollmentService({ paths: observed.paths, experimentalWindowsSandbox: true });
  const metadata = await service.installReadOnlyPolicyAssignment({ ...target, replaceExisting: true });
  if (metadata.expires_at_ms !== renewal.expires_at_ms) fail('METADATA_POLICY_RENEWAL_EXPIRY_MISMATCH');
  emit({ phase: 'metadata_policy_synced', tag: 'r7', policy_sha256: metadata.policy_sha256, expires_at_ms: metadata.expires_at_ms, workspace_id: target.workspaceId, workspace_generation: target.workspaceGeneration });
  let files = await service.inspectStandingWorkspaceFilePolicies();
  let filesInstalled = false;
  if (![files.file_read, files.approved_patch].every(targetPolicyReady)) {
    mutationGuard('renewal');
    const installed = await service.installStandingWorkspaceFilePolicies({ ...target, allowWrite: true, replaceExisting: true });
    if (installed.state !== 'read_and_patch') fail('FILE_POLICY_INSTALL_PARTIAL');
    filesInstalled = true;
    files = await service.inspectStandingWorkspaceFilePolicies();
  }
  if (![files.file_read, files.approved_patch].every(targetPolicyReady)) fail('FILE_POLICY_NOT_READY');
  emit({ phase: 'file_policy_verified', tag: 'r7', file_read: policySafe(files.file_read), approved_patch: policySafe(files.approved_patch), installed: filesInstalled });
  let exec = await service.inspectStandingWorkspaceExecPolicy(target);
  const beforeAllowlist = exec.policy?.allowed_argv_prefixes_sha256;
  let execInstalled = false;
  if (!targetPolicyReady(exec.policy)) {
    mutationGuard('renewal');
    await service.installStandingWorkspaceExecPolicy({ ...target, replaceExisting: true });
    execInstalled = true;
    exec = await service.inspectStandingWorkspaceExecPolicy(target);
    if (beforeAllowlist && exec.policy.allowed_argv_prefixes_sha256 !== beforeAllowlist) fail('EXISTING_EXEC_ALLOWLIST_CHANGED');
  }
  if (!targetPolicyReady(exec.policy) || exec.sandbox?.state !== 'available') fail('EXEC_POLICY_OR_SANDBOX_NOT_READY');
  renewalGuard();
  emit({ phase: 'policy_complete', tag: 'r7', metadata: { policy_sha256: metadata.policy_sha256, expires_at_ms: metadata.expires_at_ms }, file_read: policySafe(files.file_read), approved_patch: policySafe(files.approved_patch), exec: policySafe(exec.policy), sandbox: sandboxSafe(exec.sandbox), files_installed: filesInstalled, exec_installed: execInstalled, binding_id: bindingId, expires_at_ms: renewal.expires_at_ms, path_kind: 'guarded_api_policy_sync', renderer_continuation_proven: false });
}
async function proof() {
  verifyFiles();
  const observed = await observedDescriptor();
  if (observed.tag !== 'r7' || observed.owner.state !== 'live') fail('R7_HOST_NOT_LIVE');
  const row = await inspectRuntime(observed);
  const state = readJson(observed.paths.stateFile());
  if (row.ui.registered !== true || row.ui.alive !== true || row.ui.identity.state !== 'live' || row.ui.ui_installation_id !== observed.descriptor.installation_id || row.components.native.state !== 'live') fail('R7_COMPONENT_IDENTITIES_NOT_READY');
  if (row.epoch.state !== 'READY' || row.epoch.admission_open !== true || row.fully_ready !== true || row.update_incomplete === true || state.nativeActivationEpochId !== row.epoch.activation_epoch_id) fail('R7_READINESS_INCOMPLETE');
  if (row.agent.identity.state !== 'live' || row.agent.last_heartbeat_state !== 'succeeded' || Date.now() - Number(row.agent.last_heartbeat_at_ms) > 90000) fail('R7_AGENT_HEARTBEAT_NOT_FRESH');
  const census = await canonicalLedgerCensus({ paths: observed.paths, workspace: repo, allowAcceptancePending: true });
  assertCensus(census, true);
  const policy = lastReceipt('policy_complete', 'r7');
  emit({ phase: 'final_proof', tag: 'r7', candidate: roots.r7, profile: 'web-mcp-assistant', identities: { host: observed.owner, ui: row.ui.identity, native: row.components.native, agent: row.agent.identity }, epoch: row.epoch, fully_ready: row.fully_ready, local_ready: row.local_ready, central_connected: row.central_connected, authority_ready: row.authority_ready, awaiting_acceptance_runs: census.lifecycle.awaiting_acceptance_runs, app_asar_sha256: hashes.r7['resources/app.asar'], executable_sha256: hashes.r7['Coding Tools MCP.exe'], ledger_mutated: false, metadata_policy_synced_by_helper: Boolean(lastReceipt('metadata_policy_synced', 'r7')), standing_file_policies_reinstalled: policy?.files_installed === true, standing_exec_policy_reinstalled: policy?.exec_installed === true, windows_restarted: false, pushed: false });
}
(async () => {
  const phase = process.argv[2];
  if (phase === 'preflight') await preflight();
  else if (phase === 'census') { const observed = await observedDescriptor(); const census = await canonicalLedgerCensus({ paths: observed.paths, workspace: repo, allowAcceptancePending: true }); emit({ phase, tag: observed.tag, ...censusSummary(census) }); assertCensus(census, observed.owner.state === 'live'); }
  else if (phase === 'status') { verifyFiles(); await inspectRuntime(await observedDescriptor()); }
  else if (phase === 'activate') await switchTo('r7');
  else if (phase === 'rollback') await switchTo('r5');
  else if (phase === 'rollback_refresh') await refresh('r5');
  else if (phase === 'rollback_agent') await startAgent('r5');
  else if (phase === 'refresh') await refresh();
  else if (phase === 'policy') await installPolicy();
  else if (phase === 'agent') await startAgent();
  else if (phase === 'proof') await proof();
  else fail('PHASE_OUTSIDE_R7_ACTIVATION_SCOPE');
})().catch(error => { emit({ ok: false, code: safeText(error.code || 'R7_ACTIVATION_FAILED'), cause_code: safeText(error.cause?.code) }); process.exitCode = 1; });
