const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawn, spawnSync } = require('node:child_process');
const repo = path.resolve(__dirname, '../../..');
const services = path.join(repo, 'electron/services');
const { createRuntimePaths } = require(path.join(services, 'runtimePaths'));
const { RecoveryIpcClient, loadRecoveryDescriptor } = require(path.join(services, 'recoveryIpc'));
const { descriptorMatchesInstallation, descriptorRequestOptions } = require(path.join(services, 'recoveryHostLauncher'));
const { observeLifecycleProcessIdentity, sameProcessIdentity, terminateExactProcessTree, waitForExactProcessExit } = require(path.join(services, 'processIdentity'));
const { canonicalLedgerCensus } = require(path.join(services, 'fullCleanActivation'));
const { ControlPlaneEnrollmentService, safeEnrollmentEnvironment } = require(path.join(services, 'controlPlaneEnrollment'));
const oldRoot = path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-mcp-feedback-1011-r4/win-unpacked');
const newRoot = path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-exec-coldstart-1011-r5/win-unpacked');
const target = { workspaceId: 'workspace_dda1d78e9a21402aa6213f72af64f788', workspaceGeneration: 'generation_c2f13e8d02344cf6a38a3f42ecfa59b6', replaceExisting: true };
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
function pathsFor(root) {
  return createRuntimePaths({ dataRoot: path.join(process.env.APPDATA, 'web-mcp-assistant'), appRoot: path.join(root, 'resources/app.asar'), resourcesRoot: path.join(root, 'resources/resources'), runtimeMode: 'packaged', executablePath: path.join(root, 'Coding Tools MCP.exe') });
}
function emit(value) {
  const receipt = { observed_at: new Date().toISOString(), ...value };
  fs.appendFileSync(path.join(__dirname, 'postreboot-runtime.r5-activation.jsonl'), `${JSON.stringify(receipt)}\n`);
  process.stdout.write(`${JSON.stringify(receipt)}\n`);
}
function hash(file) { return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'); }
function verifyCandidate() {
  const receipt = JSON.parse(fs.readFileSync(path.join(__dirname, 'exec-coldstart-candidate.json'), 'utf8'));
  if (receipt.candidate !== newRoot || receipt.focused_checks_passed !== 13 || receipt.packaged_smoke_exit_code !== 0) throw Object.assign(new Error(), { code: 'R5_CANDIDATE_PROOF_MISMATCH' });
  const files = [
    [path.join(newRoot, 'resources/app.asar'), receipt.app_asar_sha256],
    [path.join(newRoot, 'Coding Tools MCP.exe'), receipt.executable_sha256]
  ];
  for (const entry of receipt.source_parity) {
    if (entry.matched !== true) throw Object.assign(new Error(), { code: 'R5_CANDIDATE_SOURCE_PARITY_MISMATCH' });
    if (!entry.packaged_path.includes(':')) files.push([path.join(newRoot, entry.packaged_path), entry.sha256]);
  }
  for (const [file, expected] of files) if (!expected || hash(file) !== expected) throw Object.assign(new Error(), { code: 'CANDIDATE_HASH_CHANGED' });
  return { node_agent_sha256: receipt.source_parity.find((entry) => entry.source === 'control-plane/control_plane/node_agent.py').sha256, app_asar_sha256: receipt.app_asar_sha256, executable_sha256: receipt.executable_sha256 };
}
async function observedDescriptor(paths) {
  let descriptor;
  try { descriptor = loadRecoveryDescriptor(paths); }
  catch (error) {
    if (error.code !== 'RECOVERY_DESCRIPTOR_STALE') throw error;
    const raw = fs.readFileSync(paths.recoveryHostDescriptorFile(), 'utf8');
    if (Buffer.byteLength(raw, 'utf8') > 64 * 1024) throw Object.assign(new Error(), { code: 'RECOVERY_DESCRIPTOR_INVALID' });
    descriptor = JSON.parse(raw);
    if (descriptor.version !== 1 || descriptor.host !== '127.0.0.1' || descriptor.owner !== 'recovery-host' || !/^[a-f0-9]{64}$/.test(descriptor.installation_id || '') || !/^[a-f0-9]{32}$/.test(descriptor.instance_id || '') || !Number.isInteger(descriptor.owner_pid)) throw Object.assign(new Error(), { code: 'RECOVERY_DESCRIPTOR_INVALID' });
  }
  const owner = await observeLifecycleProcessIdentity(descriptor.owner_pid);
  if (owner.state === 'unavailable') throw Object.assign(new Error(), { code: 'PROCESS_IDENTITY_UNVERIFIED' });
  if (owner.state === 'live' && !sameProcessIdentity({ pid: descriptor.owner_pid, process_start_token: descriptor.owner_process_start_token }, owner)) throw Object.assign(new Error(), { code: 'PROCESS_IDENTITY_CHANGED' });
  return { descriptor, owner };
}
function authenticated(paths, descriptor) {
  if (!descriptorMatchesInstallation(descriptor, paths.runtimeIdentity())) throw Object.assign(new Error(), { code: 'INSTALLATION_MISMATCH' });
  return { client: new RecoveryIpcClient({ paths }), options: descriptorRequestOptions(descriptor) };
}
async function preflight() {
  const paths = pathsFor(newRoot);
  const { descriptor, owner } = await observedDescriptor(paths);
  const oldMatches = descriptorMatchesInstallation(descriptor, pathsFor(oldRoot).runtimeIdentity());
  const newMatches = descriptorMatchesInstallation(descriptor, paths.runtimeIdentity());
  if (!oldMatches && !newMatches) throw Object.assign(new Error(), { code: 'UNEXPECTED_INSTALLATION' });
  const state = JSON.parse(fs.readFileSync(paths.stateFile(), 'utf8'));
  const components = {};
  for (const name of ['native', 'tunnel']) {
    const pid = Number(state[`${name}Pid`] || 0);
    components[name] = pid ? await observeLifecycleProcessIdentity(pid) : { state: 'absent', pid: null };
    if (components[name].state === 'unavailable') throw Object.assign(new Error(), { code: 'PROCESS_IDENTITY_UNVERIFIED' });
    if (components[name].state === 'live' && !sameProcessIdentity({ pid, process_start_token: state[`${name}ProcessStartToken`] }, components[name])) throw Object.assign(new Error(), { code: 'PROCESS_IDENTITY_CHANGED' });
  }
  emit({ phase: 'preflight', candidate: newRoot, hashes: verifyCandidate(), descriptor: { installation_id: descriptor.installation_id, instance_id: descriptor.instance_id, owner_pid: descriptor.owner_pid, owner_process_start_token: descriptor.owner_process_start_token, current_candidate: newMatches }, owner, components, prior_exit_cause: owner.state === 'absent' && oldMatches ? 'unobserved_prior_exit' : null });
  return { paths, descriptor, owner, oldMatches, newMatches };
}
async function switchCandidate() {
  const before = await preflight();
  if (before.newMatches && before.owner.state === 'live') {
    emit({ phase: 'switch_already_applied', owner_pid: before.owner.pid }); return;
  }
  const rows = fs.readFileSync(path.join(__dirname, 'postreboot-runtime.jsonl'), 'utf8').trim().split(/\r?\n/).map((row) => JSON.parse(row));
  const oldAgentReceipt = rows.findLast((row) => row.phase === 'agent_spawned');
  if (!oldAgentReceipt?.identity || oldAgentReceipt.node_agent !== pathsFor(oldRoot).controlPlaneNodeAgent()) throw Object.assign(new Error(), { code: 'R4_AGENT_IDENTITY_MISSING' });
  const oldAgent = await observeLifecycleProcessIdentity(oldAgentReceipt.identity.pid);
  if (oldAgent.state === 'live') {
    if (!sameProcessIdentity(oldAgentReceipt.identity, oldAgent)) throw Object.assign(new Error(), { code: 'R4_AGENT_IDENTITY_CHANGED' });
    const oldAgentState = JSON.parse(fs.readFileSync(path.join(pathsFor(oldRoot).dataRoot(), 'control-plane-connected-agent-status.json'), 'utf8'));
    if (oldAgentState.agent_pid !== oldAgent.pid || oldAgentState.last_iteration_state !== 'completed') throw Object.assign(new Error(), { code: 'R4_CONNECTED_AGENT_NOT_QUIESCENT' });
    const retired = await terminateExactProcessTree(oldAgentReceipt.identity, { includeDescendants: false });
    emit({ phase: 'r4_connected_agent_retired', identity: oldAgentReceipt.identity, result: retired, exact_identity_verified: true });
  } else if (oldAgent.state !== 'absent') throw Object.assign(new Error(), { code: 'R4_AGENT_IDENTITY_UNVERIFIED' });
  const oldPaths = pathsFor(oldRoot);
  if (before.owner.state === 'live') {
    const r = authenticated(oldPaths, before.descriptor);
    const status = await r.client.status({ ...r.options, fresh: true });
    const ui = status.electron_ui_recovery;
    if (ui?.registered !== true || ui.ui_installation_id !== oldPaths.runtimeIdentity().installation_id) throw Object.assign(new Error(), { code: 'UI_IDENTITY_UNVERIFIED' });
    const uiIdentity = await observeLifecycleProcessIdentity(ui.pid);
    if (ui.alive === true && uiIdentity.state === 'live') {
      await r.client.call('client.suppress_ui_recovery', [{ instance_id: ui.instance_id, reason: 'operator_quit' }], r.options);
      const env = { ...process.env }; delete env.ELECTRON_RUN_AS_NODE;
      const signal = spawnSync(oldPaths.executablePath(), [`--dev-ui-stop=${ui.instance_id}`], { env, windowsHide: true, timeout: 15000 });
      if (signal.status !== 0) throw Object.assign(new Error(), { code: 'UI_STOP_SIGNAL_FAILED' });
      await waitForExactProcessExit(uiIdentity, { timeoutMs: 15000 });
    } else if (uiIdentity.state !== 'absent') throw Object.assign(new Error(), { code: 'UI_IDENTITY_UNVERIFIED' });
    await r.client.stop({ manual: true }, r.options);
  }
  const census = await canonicalLedgerCensus({ paths: oldPaths, workspace: repo, allowAcceptancePending: true, holdExclusive: true });
  try {
    emit({ phase: 'stopped_census', safe: census.safe, code: census.code, counts: census.counts, lifecycle: census.lifecycle, ledger_mutated: census.mutated_canonical_ledger });
    if (!census.safe) throw Object.assign(new Error(), { code: census.code || 'CENSUS_REFUSED' });
    const current = await observedDescriptor(oldPaths);
    if (current.descriptor.instance_id !== before.descriptor.instance_id || current.descriptor.owner_pid !== before.descriptor.owner_pid || current.descriptor.owner_process_start_token !== before.descriptor.owner_process_start_token) throw Object.assign(new Error(), { code: 'RECOVERY_DESCRIPTOR_CHANGED' });
    if (current.owner.state === 'live') await terminateExactProcessTree({ pid: current.descriptor.owner_pid, process_start_token: current.descriptor.owner_process_start_token }, { includeDescendants: false });
    const env = { ...process.env }; delete env.ELECTRON_RUN_AS_NODE;
    const child = spawn(pathsFor(newRoot).executablePath(), [], { env, windowsHide: true, detached: true, stdio: 'ignore' });
    await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); });
    child.unref();
    emit({ phase: 'candidate_spawned', pid: child.pid, candidate: newRoot, old_owner_was_absent: before.owner.state === 'absent', acceptance_pending_preserved: true });
  } finally { await census.release_exclusive_gate(); }
}
async function r4() {
  const paths = pathsFor(newRoot);
  const { descriptor, owner } = await observedDescriptor(paths);
  if (owner.state !== 'live') throw Object.assign(new Error(), { code: 'R4_HOST_NOT_LIVE' });
  return { paths, descriptor, ...authenticated(paths, descriptor) };
}
async function resumeAfterReboot() {
  const before = await preflight();
  if (!before.newMatches) throw Object.assign(new Error(), { code: 'POSTREBOOT_INSTALLATION_MISMATCH' });
  if (before.owner.state === 'live') {
    emit({ phase: 'postreboot_already_live', owner_pid: before.owner.pid }); return;
  }
  const census = await canonicalLedgerCensus({ paths: before.paths, workspace: repo, allowAcceptancePending: true, holdExclusive: true });
  try {
    emit({ phase: 'postreboot_stopped_census', safe: census.safe, code: census.code, counts: census.counts, lifecycle: census.lifecycle, ledger_mutated: census.mutated_canonical_ledger });
    if (!census.safe) throw Object.assign(new Error(), { code: census.code || 'CENSUS_REFUSED' });
    const current = await observedDescriptor(before.paths);
    if (current.descriptor.instance_id !== before.descriptor.instance_id || current.owner.state !== 'absent') throw Object.assign(new Error(), { code: 'POSTREBOOT_DESCRIPTOR_CHANGED' });
    const env = { ...process.env }; delete env.ELECTRON_RUN_AS_NODE;
    const child = spawn(before.paths.executablePath(), [], { env, windowsHide: true, detached: true, stdio: 'ignore' });
    await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); });
    child.unref();
    emit({ phase: 'postreboot_candidate_spawned', pid: child.pid, candidate: newRoot, windows_restarted: true, windows_boot_at: '2026-10-11T08:42:38.500Z', acceptance_pending_preserved: true });
  } finally { await census.release_exclusive_gate(); }
}
async function status() {
  const r = await r4();
  const result = await r.client.status({ ...r.options, fresh: true });
  const snapshot = await r.client.call('runtime.lightweight_snapshot', [], r.options);
  emit({ phase: 'status', installation_id: r.descriptor.installation_id, host_pid: r.descriptor.owner_pid, host_instance: r.descriptor.instance_id, host_process_start_token: r.descriptor.owner_process_start_token, ui: result.electron_ui_recovery, epoch: result.activation_epoch, ready: snapshot.fullyReady, local_ready: snapshot.localReady, components_ready: snapshot.componentsReady, central_connected: snapshot.centralConnected, authority_ready: snapshot.authorityReady, central_reason: snapshot.centralStatusReason, update_incomplete: snapshot.updateIncomplete, code_revision: snapshot.codeRevision, failure_kind: snapshot.failureKind, last_start_failure: snapshot.lastStartFailure });
}
(async () => {
  const phase = process.argv[2];
  if (!['preflight', 'switch', 'status', 'refresh', 'agent', 'agent_status', 'proof'].includes(phase)) throw Object.assign(new Error(), { code: 'PHASE_OUTSIDE_R5_ACTIVATION_SCOPE' });
  if (phase === 'preflight') await preflight();
  else if (phase === 'resume') await resumeAfterReboot();
  else if (phase === 'switch') await switchCandidate();
  else if (phase === 'status') await status();
  else if (phase === 'refresh') {
    const r = await r4();
    const result = await r.client.restart({ refresh: true, mode: 'full_clean_refresh', sourceCheckpoint: null, allowAcceptancePending: true, reason: 'operator approved r5 exec cold-start repair activation, preserving pending acceptance' }, { ...r.options, timeout: 120000 });
    emit({ phase: 'refresh', state: result.state, epoch: result.activation_epoch_id });
  } else if (phase === 'policy') {
    const r = await r4();
    const service = new ControlPlaneEnrollmentService({ paths: r.paths, experimentalWindowsSandbox: true });
    const metadata = await service.installReadOnlyPolicyAssignment(target);
    const files = await service.inspectStandingWorkspaceFilePolicies();
    const exec = await service.inspectStandingWorkspaceExecPolicy(target);
    if (![files.file_read, files.approved_patch].every((policy) => policy?.enabled === true && policy.workspace_id === target.workspaceId && policy.workspace_generation === target.workspaceGeneration)) throw Object.assign(new Error(), { code: 'FILE_POLICY_NOT_READY' });
    emit({ phase: 'policy', metadata, files, exec });
  } else if (phase === 'agent') {
    const r = await r4();
    verifyCandidate();
    const agentReceipt = fs.readFileSync(path.join(__dirname, 'postreboot-runtime.r5-activation.jsonl'), 'utf8').trim().split(/\r?\n/).map((row) => JSON.parse(row)).findLast((row) => row.phase === 'agent_spawned');
    if (agentReceipt?.identity) {
      const priorAgent = await observeLifecycleProcessIdentity(agentReceipt.identity.pid);
      if (priorAgent.state === 'live') {
        if (!sameProcessIdentity(agentReceipt.identity, priorAgent)) throw Object.assign(new Error(), { code: 'POSTREBOOT_AGENT_IDENTITY_CHANGED' });
        emit({ phase: 'agent_already_live', identity: priorAgent }); return;
      }
      if (priorAgent.state !== 'absent') throw Object.assign(new Error(), { code: 'POSTREBOOT_AGENT_IDENTITY_UNVERIFIED' });
    }
    const service = new ControlPlaneEnrollmentService({ paths: r.paths });
    const files = await service.inspectStandingWorkspaceFilePolicies();
    if (![files.file_read, files.approved_patch].every((policy) => policy?.enabled === true && policy.workspace_id === target.workspaceId && policy.workspace_generation === target.workspaceGeneration)) throw Object.assign(new Error(), { code: 'FILE_POLICY_NOT_READY' });
    const output = fs.openSync(path.join(__dirname, 'postreboot-runtime.r5-agent.stdout.jsonl'), 'a');
    const errors = fs.openSync(path.join(__dirname, 'postreboot-runtime.r5-agent.stderr.log'), 'a');
    let child;
    try {
      child = spawn(r.paths.portablePython(), ['-I', '-u', r.paths.controlPlaneNodeAgent(), 'run-connected-agent', '--config', r.paths.controlPlaneNodeConfigFile(), '--workspace-registry', r.paths.controlPlaneWorkspaceRegistryFile(), '--project-root', service.agentProjectRoot, '--node', r.paths.executablePath(), '--runtime-mode', 'packaged', '--interval-seconds', '15', '--max-backoff-seconds', '60', '--max-iterations', '200'], { cwd: service.agentProjectRoot, env: safeEnrollmentEnvironment(process.env), windowsHide: true, detached: true, stdio: ['ignore', output, errors] });
      await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); });
      child.unref();
    } finally { fs.closeSync(output); fs.closeSync(errors); }
    const identity = await observeLifecycleProcessIdentity(child.pid);
    if (identity.state !== 'live') throw Object.assign(new Error(), { code: 'CONNECTED_AGENT_NOT_LIVE' });
    emit({ phase: 'agent_spawned', identity, executable: r.paths.portablePython(), node_agent: r.paths.controlPlaneNodeAgent(), candidate: newRoot, max_iterations: 200, interval_seconds: 15, source_node_agent_sha256: hash(r.paths.controlPlaneNodeAgent()) });
  } else if (phase === 'agent_status') {
    const paths = pathsFor(newRoot);
    const state = JSON.parse(fs.readFileSync(path.join(paths.dataRoot(), 'control-plane-connected-agent-status.json'), 'utf8'));
    const identity = await observeLifecycleProcessIdentity(state.agent_pid);
    emit({ phase: 'agent_status', identity, status: state });
  } else if (phase === 'proof') {
    const r = await r4();
    const status = await r.client.status({ ...r.options, fresh: true });
    const snapshot = await r.client.call('runtime.lightweight_snapshot', [], r.options);
    const state = JSON.parse(fs.readFileSync(r.paths.stateFile(), 'utf8'));
    const native = await observeLifecycleProcessIdentity(state.nativePid);
    const ui = await observeLifecycleProcessIdentity(status.electron_ui_recovery.pid);
    if (!sameProcessIdentity({ pid: state.nativePid, process_start_token: state.nativeProcessStartToken }, native) || ui.state !== 'live') throw Object.assign(new Error(), { code: 'FINAL_PROCESS_IDENTITY_UNVERIFIED' });
    const epoch = status.activation_epoch;
    if (epoch?.state !== 'READY' || epoch.admission_open !== true || snapshot.fullyReady !== true || snapshot.updateIncomplete === true || state.nativeActivationEpochId !== epoch.activation_epoch_id) throw Object.assign(new Error(), { code: 'R4_READINESS_INCOMPLETE' });
    const agentStatus = JSON.parse(fs.readFileSync(path.join(r.paths.dataRoot(), 'control-plane-connected-agent-status.json'), 'utf8'));
    const agent = await observeLifecycleProcessIdentity(agentStatus.agent_pid);
    const agentReceipt = fs.readFileSync(path.join(__dirname, 'postreboot-runtime.r5-activation.jsonl'), 'utf8').trim().split(/\r?\n/).map((row) => JSON.parse(row)).findLast((row) => row.phase === 'agent_spawned');
    if (!agentReceipt || !sameProcessIdentity(agentReceipt.identity, agent) || agentStatus.last_heartbeat_state !== 'succeeded' || Date.now() - Number(agentStatus.last_heartbeat_at_ms) > 90000) throw Object.assign(new Error(), { code: 'POSTREBOOT_AGENT_HEARTBEAT_UNVERIFIED' });
    emit({ phase: 'final_proof', installation_id: r.paths.runtimeIdentity().installation_id, hashes: verifyCandidate(), host: { pid: r.descriptor.owner_pid, process_start_token: r.descriptor.owner_process_start_token, instance_id: r.descriptor.instance_id }, ui, native, native_module_root: state.nativeModuleRoot, native_instance_id: state.nativeInstanceId, native_activation_epoch_id: state.nativeActivationEpochId, code_revision: snapshot.codeRevision, epoch, fully_ready: snapshot.fullyReady, local_ready: snapshot.localReady, components_ready: snapshot.componentsReady, central_connected: snapshot.centralConnected, authority_ready: snapshot.authorityReady, update_incomplete: snapshot.updateIncomplete, agent, agent_status: agentStatus, policy_expires_at_ms: 1791710784008, awaiting_acceptance_last_verified_census: ['95e909f0040a448faa9f1f3257e2ee2c'], windows_restarted: true, windows_boot_at: '2026-10-11T08:42:38.500Z', primary_git_committed: false, pushed: false });
  } else if (phase === 'retire_failed_agent') {
    const rows = fs.readFileSync(path.join(__dirname, 'postreboot-runtime.r5-activation.jsonl'), 'utf8').trim().split(/\r?\n/).map((row) => JSON.parse(row));
    const prior = rows.findLast((row) => row.phase === 'agent_spawned');
    if (!prior?.identity || prior.node_agent !== pathsFor(newRoot).controlPlaneNodeAgent()) throw Object.assign(new Error(), { code: 'CONNECTED_AGENT_IDENTITY_MISSING' });
    const result = await terminateExactProcessTree(prior.identity, { includeDescendants: false });
    emit({ phase: 'failed_agent_retired', identity: prior.identity, result, reason: 'CONTROL_PLANE_POLICY_PACKAGED_DATA_ROOT_FORBIDDEN', retry_change: 'removed_forbidden_data_root_override' });
  } else if (phase === 'census') {
    const census = await canonicalLedgerCensus({ paths: pathsFor(newRoot), workspace: repo, allowAcceptancePending: true });
    emit({ phase, safe: census.safe, code: census.code, counts: census.counts, lifecycle: census.lifecycle, reason: census.reason, ledger_mutated: census.mutated_canonical_ledger });
  } else throw Object.assign(new Error(), { code: 'UNKNOWN_PHASE' });
})().catch((error) => { emit({ ok: false, code: String(error.code || 'ACTIVATION_FAILED'), cause_code: String(error.cause?.code || '') }); process.exitCode = 1; });



