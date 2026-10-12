'use strict';
// Guarded r7 -> r9 transition for the approved profile and exact workspace.
// Read phases are freeze/preflight/census/status/proof. Root reviews before mutations.
// No server, task acceptance, feature, release, or standalone Sandbox probe changes.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawn, spawnSync, execFileSync } = require('node:child_process');
const repo = path.resolve(__dirname, '../../../../..');
const services = path.join(repo, 'electron/services');
const { createRuntimePaths } = require(path.join(services, 'runtimePaths'));
const { RecoveryIpcClient, loadRecoveryDescriptor } = require(path.join(services, 'recoveryIpc'));
const { descriptorMatchesInstallation, descriptorRequestOptions } = require(path.join(services, 'recoveryHostLauncher'));
const { observeLifecycleProcessIdentity, sameProcessIdentity, terminateExactProcessTree, waitForExactProcessExit } = require(path.join(services, 'processIdentity'));
const { canonicalLedgerCensus } = require(path.join(services, 'fullCleanActivation'));
const { ControlPlaneEnrollmentService, safeEnrollmentEnvironment } = require(path.join(services, 'controlPlaneEnrollment'));
const { loadExecBridgePolicy, resolveRegisteredWorkspaceRoot } = require(path.join(services, 'controlPlaneExecBridge'));
const dataRoot = 'C:\\Users\\daoth\\AppData\\Roaming\\web-mcp-assistant';
const roots = {
  r7: path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-unified-setup-1011-r7/win-unpacked'),
  r9: path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-executor-lifecycle-1011-r9/win-unpacked')
};
const target = { workspaceId: 'workspace_dda1d78e9a21402aa6213f72af64f788', workspaceGeneration: 'generation_c2f13e8d02344cf6a38a3f42ecfa59b6' };
const bindingId = 'bind_3e05bf64cb3e4bab93d930ae1692bebb';
const deviceId = '72ceec2d-e3f2-472f-8e3c-99fffe053035';
const awaitingAcceptance = ['95e909f0040a448faa9f1f3257e2ee2c'];
const expectedHead = '2c554f59cb7b8ffc86ce5e0e28076c792777642f';
const parityFile = path.join(__dirname, '..', 'candidate-parity-executor-lifecycle-1011-r9-20261011T110727929Z.json');
const paritySha256 = 'c2427d0ff484a94f4437762700ddf144fc41e7f57412491e4421aa22f0e36ec6';
const candidateHashes = {
  r7: { archive: '16151d40c7b1735be9d0502ed14c6885656bfaf41f82a4148e07c03caa123c67', executable: 'e2c20f9e93f43604fdd3d7ee6a366f0feecf8b00b5a4d410a7ca60a08a7bc871' },
  r9: { archive: '3bc75601041ef35b9fd894878b9f1905117512e3fc6f74d6102575b0f1edb226', executable: 'fadc2feb4bb566b3fa22f22ea918c7175f39fa6b74eb7ccb9d2a1d6bab1b6211' }
};
const serviceHashes = {
  runtimePaths: 'a28fe23a10daa10baeb9c437ccee13cff2c1d28585d1c6daa3e5a23844d23474',
  recoveryIpc: '1cb99599553c8e5c9df599141e85dc9a2ce526ef39eeaa1b3b44c876c1357a53',
  recoveryHostLauncher: '92cb2478ae940c737a8e8a007181a9fa410b1eeb1e26a06b5bb07e1043ebf60a',
  processIdentity: 'a0ee2b08cbe4108c352ba14b9532ceaf581497f745a2adda7924c819a972809f',
  fullCleanActivation: '286df402bad9414b8414fb1800dacf7f35cac6795fee0971e9d04ce6839e7c1d',
  controlPlaneEnrollment: 'c72766572150b5f2ce1e7ed7f976eb408ff3a75a7191951fddf0ccb7a28c6405',
  controlPlaneExecBridge: '53c8862d7b23e857f1733762fcf1cfa5b8df01a638c44d0ced0ec1c26bead8a7'
};
const evidence = path.join(__dirname, 'windows-activation.jsonl');
const pinFile = path.join(__dirname, 'r7-identity-pin.json');
const oldEvidence = path.join(__dirname, '..', '..', 'rollout-r7', 'windows-activation.jsonl');
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const fail = code => { throw Object.assign(new Error(), { code }); };
const shaBytes = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const sha = file => shaBytes(fs.readFileSync(file));
const safeText = value => String(value || '').replace(/[^a-zA-Z0-9_.:-]/g, '').slice(0, 128);
const pathKey = value => path.resolve(value).toLowerCase();
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
  if (!Object.hasOwn(roots, tag)) fail('CANDIDATE_TAG_INVALID');
  return createRuntimePaths({ dataRoot, appRoot: path.join(roots[tag], 'resources/app.asar'), resourcesRoot: path.join(roots[tag], 'resources/resources'), runtimeMode: 'packaged', executablePath: path.join(roots[tag], 'Coding Tools MCP.exe') });
}
function verifyFiles() {
  if (pathKey(process.env.APPDATA || '') !== pathKey(path.dirname(dataRoot))) fail('PROFILE_MISMATCH');
  const head = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo, encoding: 'utf8', windowsHide: true }).trim();
  if (head !== expectedHead || sha(parityFile) !== paritySha256) fail('IMMUTABLE_PARITY_RECEIPT_CHANGED');
  const parity = readJson(parityFile, 32 * 1024 * 1024);
  if (parity.ok !== true || parity.repository_head !== expectedHead || parity.candidate_tag !== 'executor-lifecycle-1011-r9'
    || parity.unexpected_payload_differences.length !== 0 || parity.expected_code_changes_not_observed.length !== 0
    || parity.source_parity.length !== 6 || parity.source_parity.some(item => !item.byte_identical)
    || parity.unchanged_r7_ui.length !== 8 || parity.unchanged_r7_ui.some(item => !item.byte_identical)
    || parity.unchanged_mxc_binaries.length !== 3 || parity.unchanged_mxc_binaries.some(item => !item.byte_identical)) fail('R9_PARITY_SCOPE_MISMATCH');
  for (const [name, expected] of Object.entries(serviceHashes)) if (sha(path.join(services, `${name}.js`)) !== expected) fail('ACTIVATION_HELPER_SERVICE_CHANGED');
  for (const source of parity.source_parity) if (sha(path.join(repo, source.source)) !== source.source_sha256) fail('R9_CURRENT_SOURCE_CHANGED');
  for (const tag of ['r7', 'r9']) {
    const manifest = tag === 'r7' ? parity.packages.r7 : parity.packages.candidate;
    if (manifest.candidate !== roots[tag] || sha(path.join(roots[tag], 'resources/app.asar')) !== candidateHashes[tag].archive
      || sha(path.join(roots[tag], 'Coding Tools MCP.exe')) !== candidateHashes[tag].executable) fail('CANDIDATE_HASH_CHANGED');
    // Runtime-generated Python bytecache is separately classified in the immutable parity receipt.
    // Every other recorded physical resource retains its exact bytes; app.asar is verified whole.
    for (const [file, expected] of Object.entries(manifest.entries)) {
      if (file.startsWith('app.asar/') || file.includes('/__pycache__/') || /\.(?:pyc|pyo)$/i.test(file)) continue;
      const physical = path.join(roots[tag], ...file.split('/'));
      const actual = expected.type === 'link' ? shaBytes(Buffer.from(fs.readlinkSync(physical))) : sha(physical);
      if (actual !== expected.sha256) fail('CANDIDATE_RESOURCE_CHANGED');
    }
  }
}
function authorizationGuard() {
  const file = path.join(__dirname, 'authorization.md');
  const raw = fs.readFileSync(file, 'utf8');
  if (!process.argv.includes('--operator-approved') || Buffer.byteLength(raw) > 32768
    || !['r9', 'web-mcp-assistant', repo, '100.116.112.22'].every(marker => raw.includes(marker))) fail('OPERATOR_AUTHORIZATION_REQUIRED');
  return shaBytes(Buffer.from(raw));
}
function closureGuard() {
  const receipt = readJson(path.join(__dirname, 'server-intake-closed.json'), 16384);
  const age = Date.now() - Number(receipt.observed_at_ms);
  if (receipt.phase !== 'intake_closed' || receipt.admission !== 'recovery' || receipt.host !== '100.116.112.22'
    || receipt.service !== 'codex-control-plane.service' || receipt.ok !== true || !Number.isFinite(age) || age < 0 || age >= 600000) fail('FRESH_SERVER_INTAKE_CLOSURE_REQUIRED');
  return receipt;
}
function renewalGuard() {
  const receipt = readJson(path.join(__dirname, 'server-authority-renewal.json'), 32768);
  const assignment = receipt.policy_assignment;
  if (receipt.phase !== 'same_scope_renewal_complete' || receipt.ok !== true || receipt.duration_ms !== 3600000 || receipt.binding_id !== bindingId
    || receipt.expires_at_ms !== receipt.requested_at_ms + 3600000 || receipt.expires_at_ms <= Date.now() || receipt.requested_at_ms > Date.now()
    || assignment?.workspace_id !== target.workspaceId || assignment.workspace_generation !== target.workspaceGeneration
    || assignment.device_id !== deviceId || assignment.expires_at_ms !== receipt.expires_at_ms || assignment.context_id !== receipt.context_id
    || !['recovery', 'scoped_pilot'].includes(receipt.admission) || receipt.service_grant_changed !== false) fail('EXACT_UNEXPIRED_SERVER_RENEWAL_REQUIRED');
  if (['queued_actions', 'accepted_actions', 'open_writers', 'open_tasks'].some(key => receipt.state?.[key] !== 0)) fail('RENEWAL_SERVER_CENSUS_NOT_QUIESCENT');
  return receipt;
}
function mutationGuard(authority = 'closure') {
  const authorization_sha256 = authorizationGuard();
  verifyFiles();
  const receipt = authority === 'renewal' ? renewalGuard() : closureGuard();
  return { ...receipt, authorization_sha256 };
}
function descriptorIdentity(d) {
  return { installation_id: d.installation_id, instance_id: d.instance_id, owner_pid: d.owner_pid, owner_process_start_token: d.owner_process_start_token };
}
async function observedDescriptor() {
  const paths = pathsFor('r7');
  let descriptor;
  try { descriptor = loadRecoveryDescriptor(paths); }
  catch (error) {
    if (error.code !== 'RECOVERY_DESCRIPTOR_STALE') throw error;
    descriptor = readJson(paths.recoveryHostDescriptorFile(), 16384);
    if (descriptor.version !== 1 || descriptor.host !== '127.0.0.1' || descriptor.owner !== 'recovery-host'
      || !/^[a-f0-9]{64}$/.test(descriptor.installation_id || '') || !/^[a-f0-9]{32}$/.test(descriptor.instance_id || '') || !Number.isInteger(descriptor.owner_pid)) fail('RECOVERY_DESCRIPTOR_INVALID');
  }
  const owner = await observeLifecycleProcessIdentity(descriptor.owner_pid);
  if (owner.state === 'unavailable' || (owner.state === 'live' && !sameProcessIdentity({ pid: descriptor.owner_pid, process_start_token: descriptor.owner_process_start_token }, owner))) fail('RECOVERY_OWNER_IDENTITY_CHANGED');
  const tag = ['r7', 'r9'].find(value => descriptorMatchesInstallation(descriptor, pathsFor(value).runtimeIdentity()));
  if (!tag) fail('UNEXPECTED_INSTALLATION');
  return { descriptor, owner, tag, paths: pathsFor(tag) };
}
function authenticated(observed) {
  return { client: new RecoveryIpcClient({ paths: observed.paths }), options: descriptorRequestOptions(observed.descriptor) };
}
function lastReceipt(phase, tag, file = evidence) {
  if (!fs.existsSync(file)) return null;
  return fs.readFileSync(file, 'utf8').trim().split(/\r?\n/).filter(Boolean).map(JSON.parse).findLast(row => row.phase === phase && (!tag || row.tag === tag));
}
function pinFor(tag) {
  if (tag === 'r7') {
    const receipt = lastReceipt('r7_pin_frozen', 'r7');
    const pin = readJson(pinFile, 65536);
    if (receipt?.pin_file !== pinFile || receipt.pin_sha256 !== sha(pinFile) || pin.kind !== 'immutable_r7_identity_pin_for_r9'
      || pin.repository_head !== expectedHead || pin.parity_sha256 !== paritySha256) fail('R7_IDENTITY_PIN_CHANGED');
    return pin;
  }
  const row = lastReceipt('status', tag) || lastReceipt('candidate_started', tag);
  if (!row?.descriptor || !row?.owner || !row?.ui?.identity) fail('R9_IDENTITY_RECEIPT_REQUIRED');
  return { ...row.descriptor, owner: row.owner, ui: { ...row.ui.identity, instance_id: row.ui.instance_id }, native: row.components.native };
}
function assertDescriptorPin(observed, pin) {
  if (observed.descriptor.installation_id !== pin.installation_id || observed.descriptor.instance_id !== pin.instance_id
    || observed.descriptor.owner_pid !== pin.owner.pid || observed.descriptor.owner_process_start_token !== pin.owner.process_start_token) fail('PINNED_RECOVERY_DESCRIPTOR_CHANGED');
}
async function agentObservation(tag) {
  const pin = tag === 'r7' && fs.existsSync(pinFile) ? readJson(pinFile, 65536) : null;
  const receipt = pin?.agent_receipt || lastReceipt('agent_spawned', tag, tag === 'r7' ? oldEvidence : evidence);
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
  const epoch = status.activation_epoch;
  return emit({ phase, tag: observed.tag, descriptor: descriptorIdentity(observed.descriptor), owner: observed.owner,
    ui: { pid: ui?.pid, instance_id: ui?.instance_id, alive: ui?.alive, registered: ui?.registered, ui_installation_id: ui?.ui_installation_id, identity }, components,
    epoch: { activation_epoch_id: epoch?.activation_epoch_id, state: epoch?.state, admission_open: epoch?.admission_open, update_incomplete: epoch?.update_incomplete },
    fully_ready: snapshot.fullyReady, local_ready: snapshot.localReady, central_connected: snapshot.centralConnected, authority_ready: snapshot.authorityReady,
    update_incomplete: snapshot.updateIncomplete, failure_kind: safeText(snapshot.failureKind), agent: { identity: agent.identity, ...agent.summary } });
}
function censusSummary(census) {
  return { safe: census.safe, code: census.code, counts: census.counts, lifecycle: census.lifecycle, reason: census.reason,
    ledger_mutated: census.mutated_canonical_ledger, content_free: census.content_free, census_fingerprint: census.census_fingerprint,
    snapshot: { logical_sha256: census.snapshot.logical_sha256, integrity_check: census.snapshot.integrity_check } };
}
function assertCensus(census, liveAllowed = false) {
  const pending = census.lifecycle.awaiting_acceptance_runs.slice().sort();
  if (pending.join(',') !== awaitingAcceptance.join(',')) fail('PENDING_ACCEPTANCE_SET_CHANGED');
  const integrity = census.snapshot.integrity_check;
  if (census.mutated_canonical_ledger || !census.content_free || !Array.isArray(integrity) || integrity.length !== 1 || integrity[0] !== 'ok') fail('CENSUS_CONTRACT_INVALID');
  if (['active_tool_calls', 'active_commands', 'starting_commands', 'active_background_operations', 'active_managed_processes', 'active_agent_lanes'].some(key => census.counts[key] !== 0)
    || census.lifecycle.live_owned_runs.length !== 0 || census.lifecycle.unexplained_active_runs !== 0 || census.lifecycle.unbound_live_resource_residues !== 0) fail('ACTIVE_JOB_OR_LANE_BLOCKS_ACTIVATION');
  if (liveAllowed && census.code === 'RUNTIME_BUSY' && census.lifecycle.blockers.join(',') === 'live_runtime_state_process') return;
  if (!census.safe) fail(census.code || 'CENSUS_REFUSED');
}
async function censusFor(observed, phase = 'census', holdExclusive = false) {
  const census = await canonicalLedgerCensus({ paths: observed.paths, workspace: repo, allowAcceptancePending: true, holdExclusive,
    pythonStatusFn: async () => ({ installed: true, command: observed.paths.portablePython(), prefixArgs: ['-B'] }) });
  emit({ phase, tag: observed.tag, ...censusSummary(census) });
  return census;
}
function targetPolicyReady(policy) {
  return policy?.state === 'enabled' && policy.enabled === true && policy.workspace_id === target.workspaceId && policy.workspace_generation === target.workspaceGeneration;
}
function policySafe(policy) {
  return { state: safeText(policy?.state), enabled: policy?.enabled === true, workspace_id: policy?.workspace_id, workspace_generation: policy?.workspace_generation,
    policy_sha256: policy?.policy_sha256, allowed_argv_prefix_count: policy?.allowed_argv_prefix_count, allowed_argv_prefixes_sha256: policy?.allowed_argv_prefixes_sha256 };
}
async function inspectPoliciesNoProbe(observed) {
  const service = new ControlPlaneEnrollmentService({ paths: observed.paths });
  const files = await service.inspectStandingWorkspaceFilePolicies();
  const exec = await service.inspectLocalExecPolicy();
  const admitted = loadExecBridgePolicy(observed.paths);
  const workspaceRoot = resolveRegisteredWorkspaceRoot(observed.paths, admitted);
  if (pathKey(workspaceRoot) !== pathKey(fs.realpathSync.native(repo)) || admitted.workspace_id !== target.workspaceId
    || admitted.workspace_generation !== target.workspaceGeneration || admitted.device_id !== deviceId || admitted.authority_mode !== 'standing'
    || admitted.expires_at_ms !== null || admitted.policy_sha256 !== exec.policy_sha256 || !targetPolicyReady(exec)
    || ![files.file_read, files.approved_patch].every(targetPolicyReady)) fail('STANDING_POLICY_TARGET_OR_ALLOWLIST_NOT_READY');
  return { file_read: policySafe(files.file_read), approved_patch: policySafe(files.approved_patch), exec: policySafe(exec),
    sandbox: { state: 'unproven_live_exec_required', standalone_probe_performed: false }, workspace_root_verified: true };
}
function assertStandingPoliciesUnchanged(policies) {
  const pin = pinFor('r7');
  for (const kind of ['file_read', 'approved_patch', 'exec']) if (policies[kind].policy_sha256 !== pin.policies[kind].policy_sha256) fail('STANDING_POLICY_HASH_CHANGED');
  if (policies.exec.allowed_argv_prefixes_sha256 !== pin.policies.exec.allowed_argv_prefixes_sha256) fail('EXISTING_EXEC_ALLOWLIST_CHANGED');
}
async function freeze() {
  verifyFiles();
  const observed = await observedDescriptor();
  if (observed.tag !== 'r7' || observed.owner.state !== 'live') fail('R7_LIVE_SOURCE_REQUIRED');
  const row = await inspectRuntime(observed, 'freeze_observation');
  if (row.ui.identity.state !== 'live' || row.ui.registered !== true || row.ui.alive !== true || row.components.native.state !== 'live'
    || row.ui.ui_installation_id !== observed.descriptor.installation_id) fail('R7_SOURCE_IDENTITIES_NOT_READY');
  const census = await censusFor(observed, 'freeze_census'); assertCensus(census, true);
  const policies = await inspectPoliciesNoProbe(observed);
  const agent = await agentObservation('r7');
  const pin = { kind: 'immutable_r7_identity_pin_for_r9', observed_at: new Date().toISOString(), repository_head: expectedHead, parity_sha256: paritySha256,
    ...row.descriptor, owner: row.owner, ui: { ...row.ui.identity, instance_id: row.ui.instance_id }, native: row.components.native,
    agent: agent.identity, agent_receipt: agent.receipt ? { identity: agent.receipt.identity, node_agent: agent.receipt.node_agent } : null,
    policies, census: censusSummary(census), runtime_mutated: false, server_mutated: false };
  fs.writeFileSync(pinFile, `${JSON.stringify(pin, null, 2)}\n`, { flag: 'wx' });
  emit({ phase: 'r7_pin_frozen', tag: 'r7', pin_file: pinFile, pin_sha256: sha(pinFile), identities: { owner: pin.owner, ui: pin.ui, native: pin.native, agent: pin.agent }, policies, runtime_mutated: false });
}
async function preflight() {
  verifyFiles(); const observed = await observedDescriptor();
  if (observed.tag !== 'r7') fail('R7_SWITCH_SOURCE_REQUIRED');
  const pin = pinFor('r7'); assertDescriptorPin(observed, pin);
  const row = await inspectRuntime(observed, 'preflight');
  if (!sameProcessIdentity(pin.ui, row.ui.identity) || row.ui.instance_id !== pin.ui.instance_id || !sameProcessIdentity(pin.native, row.components.native)) fail('PINNED_R7_COMPONENT_CHANGED');
  const agent = await agentObservation('r7');
  if (agent.identity.state === 'live' && !sameProcessIdentity(pin.agent, agent.identity)) fail('PINNED_R7_AGENT_CHANGED');
  const policies = await inspectPoliciesNoProbe(observed); assertStandingPoliciesUnchanged(policies);
  const census = await censusFor(observed, 'preflight_census'); assertCensus(census, observed.owner.state === 'live');
}
async function activate() {
  mutationGuard(); await preflight();
  const before = await observedDescriptor(); const pin = pinFor('r7'); assertDescriptorPin(before, pin);
  const agent = await agentObservation('r7');
  if (agent.identity.state === 'live') {
    if (agent.summary.last_iteration_state !== 'completed' || !sameProcessIdentity(pin.agent, agent.identity)) fail('CONNECTED_AGENT_NOT_QUIESCENT');
    mutationGuard(); const result = await terminateExactProcessTree(pin.agent, { includeDescendants: false });
    emit({ phase: 'agent_retired', tag: 'r7', identity: pin.agent, result });
  }
  const r = authenticated(before); const status = await r.client.status({ ...r.options, fresh: true }); const ui = status.electron_ui_recovery;
  if (ui?.pid !== pin.ui.pid || ui.instance_id !== pin.ui.instance_id || ui.ui_installation_id !== pin.installation_id) fail('PINNED_UI_IDENTITY_CHANGED');
  const uiIdentity = await observeLifecycleProcessIdentity(ui.pid);
  if (!sameProcessIdentity(pin.ui, uiIdentity)) fail('PINNED_UI_PROCESS_CHANGED');
  mutationGuard(); await r.client.call('client.suppress_ui_recovery', [{ instance_id: ui.instance_id, reason: 'operator_quit' }], r.options);
  const env = { ...process.env }; delete env.ELECTRON_RUN_AS_NODE;
  const signal = spawnSync(before.paths.executablePath(), [`--dev-ui-stop=${ui.instance_id}`], { env, windowsHide: true, timeout: 15000, stdio: 'ignore' });
  if (signal.status !== 0) fail('UI_STOP_SIGNAL_FAILED');
  await waitForExactProcessExit(uiIdentity, { timeoutMs: 15000 });
  mutationGuard(); await r.client.stop({ manual: true }, r.options); emit({ phase: 'runtime_stopped', tag: 'r7', exact_identity_verified: true });
  const census = await censusFor(before, 'stopped_census', true);
  try {
    assertCensus(census); const current = await observedDescriptor(); assertDescriptorPin(current, pin);
    mutationGuard(); if (current.owner.state === 'live') await terminateExactProcessTree(pin.owner, { includeDescendants: false });
    const child = spawn(pathsFor('r9').executablePath(), [], { env, windowsHide: true, detached: true, stdio: 'ignore' });
    await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); }); child.unref();
    emit({ phase: 'candidate_spawned', tag: 'r9', pid: child.pid, candidate: roots.r9, acceptance_pending_preserved: true });
  } finally { await census.release_exclusive_gate(); }
  const deadline = Date.now() + 45000;
  while (Date.now() < deadline) {
    try { const live = await observedDescriptor(); if (live.tag === 'r9' && live.owner.state === 'live') { await inspectRuntime(live, 'candidate_started'); return; } }
    catch (error) { if (!['RECOVERY_DESCRIPTOR_STALE', 'RECOVERY_DESCRIPTOR_MISSING', 'RECOVERY_HOST_UNAVAILABLE', 'RECOVERY_TIMEOUT'].includes(error.code)) throw error; }
    await wait(500);
  }
  fail('R9_START_NOT_OBSERVED');
}
async function policy() {
  const renewal = mutationGuard('renewal'); const observed = await observedDescriptor();
  if (observed.tag !== 'r9' || observed.owner.state !== 'live') fail('R9_HOST_NOT_LIVE');
  const policies = await inspectPoliciesNoProbe(observed); assertStandingPoliciesUnchanged(policies);
  const service = new ControlPlaneEnrollmentService({ paths: observed.paths });
  mutationGuard('renewal'); const metadata = await service.installReadOnlyPolicyAssignment({ ...target, replaceExisting: true });
  if (metadata.expires_at_ms !== renewal.expires_at_ms) fail('METADATA_POLICY_RENEWAL_EXPIRY_MISMATCH');
  emit({ phase: 'metadata_policy_synced', tag: 'r9', policy_sha256: metadata.policy_sha256, expires_at_ms: metadata.expires_at_ms, workspace_id: target.workspaceId, workspace_generation: target.workspaceGeneration });
  const after = await inspectPoliciesNoProbe(observed); assertStandingPoliciesUnchanged(after); renewalGuard();
  emit({ phase: 'policy_complete', tag: 'r9', metadata: { policy_sha256: metadata.policy_sha256, expires_at_ms: metadata.expires_at_ms }, ...after,
    files_installed: false, exec_installed: false, standalone_sandbox_probe_performed: false, binding_id: bindingId, expires_at_ms: renewal.expires_at_ms,
    path_kind: 'guarded_metadata_sync_and_existing_policy_read', renderer_continuation_proven: false });
}
async function refresh() {
  mutationGuard('renewal'); const observed = await observedDescriptor();
  if (observed.tag !== 'r9' || observed.owner.state !== 'live') fail('R9_HOST_NOT_LIVE');
  const policies = await inspectPoliciesNoProbe(observed); assertStandingPoliciesUnchanged(policies);
  const census = await censusFor(observed, 'refresh_preflight_census'); assertCensus(census, true);
  const r = authenticated(observed);
  const result = await r.client.restart({ refresh: true, mode: 'full_clean_refresh', sourceCheckpoint: null, allowAcceptancePending: true,
    reason: 'operator approved r9 executor lifecycle activation preserving pending acceptance' }, { ...r.options, timeout: 120000 });
  emit({ phase: 'refresh', tag: 'r9', state: safeText(result.state), epoch: result.activation_epoch_id });
}
async function startAgent() {
  mutationGuard('renewal'); const observed = await observedDescriptor();
  if (observed.tag !== 'r9' || observed.owner.state !== 'live') fail('R9_HOST_NOT_LIVE');
  if ((await agentObservation('r7')).identity.state !== 'absent') fail('R7_AGENT_STILL_LIVE');
  const prior = await agentObservation('r9');
  if (prior.identity.state === 'live') { emit({ phase: 'agent_already_live', tag: 'r9', identity: prior.identity }); return; }
  const policies = await inspectPoliciesNoProbe(observed); assertStandingPoliciesUnchanged(policies);
  const service = new ControlPlaneEnrollmentService({ paths: observed.paths });
  const output = fs.openSync(path.join(__dirname, 'r9-agent.stdout.jsonl'), 'a'); const errors = fs.openSync(path.join(__dirname, 'r9-agent.stderr.log'), 'a');
  let child;
  try {
    mutationGuard('renewal'); child = spawn(observed.paths.portablePython(), ['-B', '-I', '-u', observed.paths.controlPlaneNodeAgent(), 'run-connected-agent',
      '--config', observed.paths.controlPlaneNodeConfigFile(), '--workspace-registry', observed.paths.controlPlaneWorkspaceRegistryFile(), '--project-root', service.agentProjectRoot,
      '--node', observed.paths.executablePath(), '--runtime-mode', 'packaged', '--interval-seconds', '15', '--max-backoff-seconds', '60', '--max-iterations', '200'],
    { cwd: service.agentProjectRoot, env: safeEnrollmentEnvironment(process.env), windowsHide: true, detached: true, stdio: ['ignore', output, errors] });
    await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); }); child.unref();
  } finally { fs.closeSync(output); fs.closeSync(errors); }
  const identity = await observeLifecycleProcessIdentity(child.pid); if (identity.state !== 'live') fail('R9_AGENT_NOT_LIVE');
  emit({ phase: 'agent_spawned', tag: 'r9', identity, node_agent: observed.paths.controlPlaneNodeAgent(), candidate: roots.r9, interval_seconds: 15, max_iterations: 200 });
}
async function proof() {
  verifyFiles(); const observed = await observedDescriptor();
  if (observed.tag !== 'r9' || observed.owner.state !== 'live') fail('R9_HOST_NOT_LIVE');
  const row = await inspectRuntime(observed); const state = readJson(observed.paths.stateFile());
  if (row.ui.registered !== true || row.ui.alive !== true || row.ui.identity.state !== 'live' || row.ui.ui_installation_id !== observed.descriptor.installation_id || row.components.native.state !== 'live') fail('R9_COMPONENT_IDENTITIES_NOT_READY');
  if (row.epoch.state !== 'READY' || row.epoch.admission_open !== true || row.fully_ready !== true || row.update_incomplete === true || state.nativeActivationEpochId !== row.epoch.activation_epoch_id) fail('R9_READINESS_INCOMPLETE');
  if (row.agent.identity.state !== 'live' || row.agent.last_heartbeat_state !== 'succeeded' || Date.now() - Number(row.agent.last_heartbeat_at_ms) > 90000) fail('R9_AGENT_HEARTBEAT_NOT_FRESH');
  const census = await censusFor(observed, 'final_census'); assertCensus(census, true);
  const policies = await inspectPoliciesNoProbe(observed); assertStandingPoliciesUnchanged(policies); renewalGuard();
  emit({ phase: 'final_proof', tag: 'r9', candidate: roots.r9, profile: 'web-mcp-assistant', identities: { host: observed.owner, ui: row.ui.identity, native: row.components.native, agent: row.agent.identity },
    epoch: row.epoch, fully_ready: row.fully_ready, local_ready: row.local_ready, central_connected: row.central_connected, authority_ready: row.authority_ready,
    awaiting_acceptance_runs: census.lifecycle.awaiting_acceptance_runs, app_asar_sha256: candidateHashes.r9.archive, executable_sha256: candidateHashes.r9.executable,
    parity_sha256: paritySha256, ledger_mutated: false, metadata_policy_synced_by_helper: Boolean(lastReceipt('metadata_policy_synced', 'r9')),
    standing_policies_reinstalled: false, standalone_sandbox_probe_performed: false, live_sandbox_exec_proven: false, windows_restarted: false, pushed: false });
}
(async () => {
  const phase = process.argv[2];
  if (phase === 'freeze') await freeze();
  else if (phase === 'preflight') await preflight();
  else if (phase === 'census') { verifyFiles(); const observed = await observedDescriptor(); assertCensus(await censusFor(observed), observed.owner.state === 'live'); }
  else if (phase === 'status') { verifyFiles(); await inspectRuntime(await observedDescriptor()); }
  else if (phase === 'activate') await activate();
  else if (phase === 'policy') await policy();
  else if (phase === 'refresh') await refresh();
  else if (phase === 'agent') await startAgent();
  else if (phase === 'proof') await proof();
  else fail('PHASE_OUTSIDE_R9_ACTIVATION_SCOPE');
})().catch(error => { emit({ ok: false, code: safeText(error.code || 'R9_ACTIVATION_FAILED'), cause_code: safeText(error.cause?.code) }); process.exitCode = 1; });
