'use strict';
// Root-executed, phase-separated transition. Observe/freeze are query-only.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const { spawn, spawnSync, execFileSync } = require('node:child_process');
const asar = require('@electron/asar');
const repo = path.resolve(__dirname, '../../../../../..'), services = path.join(repo, 'electron/services');
const { createRuntimePaths } = require(path.join(services, 'runtimePaths'));
const { RecoveryIpcClient, loadRecoveryDescriptor } = require(path.join(services, 'recoveryIpc'));
const { descriptorMatchesInstallation, descriptorRequestOptions } = require(path.join(services, 'recoveryHostLauncher'));
const { observeLifecycleProcessIdentity: identity, sameProcessIdentity: same, terminateExactProcessTree, waitForExactProcessExit } = require(path.join(services, 'processIdentity'));
const { canonicalLedgerCensus } = require(path.join(services, 'fullCleanActivation'));
const { ControlPlaneEnrollmentService, safeEnrollmentEnvironment } = require(path.join(services, 'controlPlaneEnrollment'));
const { loadExecBridgePolicy, resolveRegisteredWorkspaceRoot } = require(path.join(services, 'controlPlaneExecBridge'));
const dataRoot = 'C:\\Users\\daoth\\AppData\\Roaming\\web-mcp-assistant';
const roots = Object.fromEntries(Object.entries({ r10: 'setup-exec-contract-1011-r10', r11: 'initial-proof-1011-r11' }).map(([key, tag]) => [key, path.join(repo, `dist/windows-candidate-mxc-wsb-cbe1774-${tag}/win-unpacked`)]));
const head = '2c554f59cb7b8ffc86ce5e0e28076c792777642f';
const target = { binding_id: 'bind_3e05bf64cb3e4bab93d930ae1692bebb', device_id: '72ceec2d-e3f2-472f-8e3c-99fffe053035', workspace_id: 'workspace_dda1d78e9a21402aa6213f72af64f788', workspace_generation: 'generation_c2f13e8d02344cf6a38a3f42ecfa59b6', root: repo, profile: 'web-mcp-assistant' };
const serverRevision = '9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c';
const canaryArgv = ['node', '--test', 'tests/fixtures/initial-proof-canary-check.cjs'];
const expectedPending = { run_id: '95e909f0040a448faa9f1f3257e2ee2c', wave_id: 'c101beadfc6d4f2fbc13845052c84693', run_record_sha256: 'a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590', wave_record_sha256: '59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce' };
const pinFile = path.join(__dirname, 'r10-observation-pin.json'), journal = path.join(__dirname, 'transition.jsonl');
const sha = file => digest(fs.readFileSync(file));
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const key = file => path.resolve(file).toLowerCase();
const fail = code => { throw Object.assign(new Error(), { code }); };
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const rows = () => fs.existsSync(journal) ? fs.readFileSync(journal, 'utf8').trim().split(/\r?\n/).filter(Boolean).map(JSON.parse) : [];
const last = phase => rows().findLast(row => row.phase === phase);
function emit(value) { const row = { observed_at: new Date().toISOString(), helper_sha256: sha(__filename), ...value }; fs.appendFileSync(journal, JSON.stringify(row) + '\n'); process.stdout.write(JSON.stringify(row) + '\n'); return row; }
function arg(name) { const values = process.argv.filter(value => value.startsWith(`--${name}=`)); if (values.length !== 1) fail('EXPLICIT_PIN_ARGUMENT_REQUIRED'); return values[0].slice(name.length + 3); }
function pinned(name) { const file = arg(name); if (!path.isAbsolute(file) || !/^[a-f0-9]{64}$/.test(arg(`${name}-sha256`)) || sha(file) !== arg(`${name}-sha256`)) fail('PINNED_RECEIPT_CHANGED'); return read(file); }
function pathsFor(tag) { return createRuntimePaths({ dataRoot, appRoot: path.join(roots[tag], 'resources/app.asar'), resourcesRoot: path.join(roots[tag], 'resources/resources'), runtimeMode: 'packaged', executablePath: path.join(roots[tag], 'Coding Tools MCP.exe') }); }
function verifyCandidate() {
  if (key(process.env.APPDATA || '') !== key(path.dirname(dataRoot)) || execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo, encoding: 'utf8', windowsHide: true }).trim() !== head) fail('REPOSITORY_OR_PROFILE_CHANGED');
  const parityFile = path.join(__dirname, '../candidate-parity-20261011T142316263Z.json'), parity = read(parityFile), freezeFile = path.join(__dirname, '../source-freeze.json');
  if (sha(parityFile) !== 'cefbb4daaeda869629594ed311e685de10049ef07445766b73ae4a5113bc0666' || sha(freezeFile) !== '3bd561909abf56126ae2a15cc65932181251a48a1a9d47779b506e1b6c359c63' || !parity.ok || parity.candidate_tag !== 'initial-proof-1011-r11' || parity.source_files.length !== 12 || parity.source_freeze_sha256 !== sha(freezeFile) || sha(path.join(roots.r11, 'resources/app.asar')) !== '2071c0c242bc4b24ebfc22ea21b5c4d066e018505061ebe299cd666c6d2e8a91' || sha(pathsFor('r11').executablePath()) !== parity.executable_sha256) fail('R11_PACKAGE_PIN_CHANGED');
  for (const item of parity.source_files) {
    const payload = item.payload.startsWith('app.asar/') ? asar.extractFile(path.join(roots.r11, 'resources/app.asar'), path.join(...item.payload.slice(9).split('/'))) : fs.readFileSync(path.join(roots.r11, item.payload));
    if (sha(path.join(repo, item.source)) !== item.sha256 || digest(payload) !== item.sha256) fail('R11_SOURCE_OR_PAYLOAD_DRIFT');
  }
  return { app_asar_sha256: parity.app_asar_sha256, executable_sha256: parity.executable_sha256, matched_files: 12, parity_sha256: sha(parityFile), source_freeze_sha256: sha(freezeFile) };
}
const ps = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe';
function powershell(script) {
  const result = spawnSync(ps, ['-NoProfile', '-NonInteractive', '-Command', script], { windowsHide: true, shell: false, timeout: 10000, encoding: 'utf8', maxBuffer: 16384 });
  if (result.error || result.status !== 0) fail('QUERY_OBSERVER_UNAVAILABLE');
  try { return JSON.parse(result.stdout.replace(/^\uFEFF/, '').trim()); } catch { fail('QUERY_OBSERVER_MALFORMED'); }
}
function zeroVm(required = true) {
  const value = powershell("$ErrorActionPreference='Stop'; $names=@('WindowsSandbox','WindowsSandboxClient','WindowsSandboxServer','WindowsSandboxRemoteSession','vmmemWindowsSandbox'); $hostCount=@(Get-Process | Where-Object { $names -contains $_.ProcessName }).Count; $backendCount=@(Get-CimInstance Win32_Process -Filter \"Name='wxc-windows-sandbox-daemon.exe' OR Name='wxc-exec.exe' OR Name='wxc-windows-sandbox-guest.exe'\").Count; @{host_count=$hostCount;backend_count=$backendCount;content_free=$true} | ConvertTo-Json -Compress");
  if (!Number.isSafeInteger(value.host_count) || !Number.isSafeInteger(value.backend_count) || value.content_free !== true) fail('VM_OBSERVATION_INVALID');
  value.ok = value.host_count === 0 && value.backend_count === 0; value.observed_at_ms = Date.now();
  if (required && !value.ok) fail('VM_OR_BACKEND_STILL_PRESENT'); return value;
}
async function observed() {
  let descriptor;
  try { descriptor = loadRecoveryDescriptor(pathsFor('r10')); } catch (error) { if (error.code !== 'RECOVERY_DESCRIPTOR_STALE') throw error; descriptor = read(pathsFor('r10').recoveryHostDescriptorFile()); }
  const tag = Object.keys(roots).find(value => descriptorMatchesInstallation(descriptor, pathsFor(value).runtimeIdentity()));
  if (!tag || descriptor.version !== 1 || descriptor.host !== '127.0.0.1' || descriptor.owner !== 'recovery-host' || !/^[a-f0-9]{32}$/.test(descriptor.instance_id || '')) fail('UNEXPECTED_RECOVERY_INSTALLATION');
  const owner = await identity(descriptor.owner_pid);
  if (owner.state === 'unavailable' || owner.state === 'live' && !same(owner, { pid: descriptor.owner_pid, process_start_token: descriptor.owner_process_start_token })) fail('HOST_IDENTITY_UNVERIFIED');
  return { descriptor, tag, owner, paths: pathsFor(tag) };
}
const descriptorSummary = d => ({ installation_id: d.installation_id, instance_id: d.instance_id, owner_pid: d.owner_pid, owner_process_start_token: d.owner_process_start_token });
const ipc = o => ({ client: new RecoveryIpcClient({ paths: o.paths }), options: descriptorRequestOptions(o.descriptor) });
async function agentObservation(o) {
  const file = path.join(dataRoot, 'control-plane-connected-agent-status.json'), raw = fs.existsSync(file) ? read(file) : {};
  const seen = raw.agent_pid ? await identity(raw.agent_pid) : { state: 'absent', pid: null };
  if (seen.state === 'unavailable') fail('AGENT_IDENTITY_UNVERIFIED');
  if (seen.state === 'live') {
    const literal = value => "'" + value.replaceAll("'", "''") + "'";
    const result = powershell(`$ErrorActionPreference='Stop'; $p=Get-CimInstance Win32_Process -Filter 'ProcessId=${seen.pid}'; $c=[string]$p.CommandLine; @{matches=($c.Contains(${literal(o.paths.controlPlaneNodeAgent())}) -and $c.Contains('run-connected-agent') -and $c.Contains(${literal(o.paths.controlPlaneNodeConfigFile())}));content_free=$true} | ConvertTo-Json -Compress`);
    if (!result.matches || result.content_free !== true) fail('AGENT_COMMAND_TARGET_UNVERIFIED');
  }
  const pick = names => Object.fromEntries(names.map(name => [name, raw[name] ?? null]));
  const config = read(o.paths.controlPlaneNodeConfigFile());
  if (config.device_id !== target.device_id) fail('NODE_CONFIG_TARGET_CHANGED');
  return { identity: seen, ...pick(['last_iteration_state', 'last_heartbeat_state', 'last_heartbeat_at_ms', 'completed_iterations', 'device_id', 'workspace_id', 'workspace_generation']), node_config: { device_id: config.device_id, endpoint_id: config.endpoint_id, server_origin: new URL(config.server_url).origin } };
}
async function runtimeObservation(o) {
  if (o.owner.state !== 'live') return { tag: o.tag, descriptor: descriptorSummary(o.descriptor), owner: o.owner };
  const r = ipc(o), status = await r.client.status({ ...r.options, fresh: true }), snapshot = await r.client.call('runtime.lightweight_snapshot', [], r.options), raw = read(o.paths.stateFile());
  const uiRaw = status.electron_ui_recovery, ui = uiRaw?.pid ? await identity(uiRaw.pid) : { state: 'absent', pid: null }, native = raw.nativePid ? await identity(raw.nativePid) : { state: 'absent', pid: null }, tunnel = raw.tunnelPid ? await identity(raw.tunnelPid) : { state: 'absent', pid: null };
  if ([ui, native, tunnel].some(x => x.state === 'unavailable') || native.state === 'live' && !same(native, { pid: raw.nativePid, process_start_token: raw.nativeProcessStartToken }) || tunnel.state === 'live' && !same(tunnel, { pid: raw.tunnelPid, process_start_token: raw.tunnelProcessStartToken })) fail('COMPONENT_IDENTITY_UNVERIFIED');
  const pick = (value, names) => Object.fromEntries(names.map(name => [name, value?.[name] ?? null]));
  return { tag: o.tag, descriptor: descriptorSummary(o.descriptor), owner: o.owner, ui: { identity: ui, ...pick(uiRaw, ['instance_id', 'alive', 'registered', 'ui_installation_id']) }, native, tunnel, agent: await agentObservation(o), epoch: pick(status.activation_epoch, ['activation_epoch_id', 'operation_id', 'state', 'admission_open', 'update_incomplete']), readiness: pick(snapshot, ['fullyReady', 'localReady', 'componentsReady', 'centralConnected', 'authorityReady', 'updateIncomplete', 'failureKind', 'centralStatusReason']), native_epoch: raw.nativeActivationEpochId ?? null, revisions: [status.code_revision, status.electron_ui_revision, snapshot.codeRevision?.codingMcp].map(value => pick(value, ['state', 'running_revision', 'disk_revision', 'update_pending', 'pending_revision'])) };
}
const pendingCode = `import hashlib,json,sqlite3,sys\nfrom pathlib import Path\ns=sqlite3.connect(Path(sys.argv[1]).resolve(strict=True).as_uri()+"?mode=ro",uri=True);s.execute("PRAGMA query_only=ON");d=sqlite3.connect(":memory:");s.backup(d);s.close();d.row_factory=sqlite3.Row\nr={}\nfor table,column,value in (("runs","run_id",sys.argv[2]),("waves","wave_id",sys.argv[3])):\n rows=d.execute(f"SELECT * FROM {table} WHERE {column}=?",(value,)).fetchall()\n if len(rows)!=1:raise SystemExit(2)\n r[table]=hashlib.sha256(json.dumps(dict(rows[0]),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()\nprint(json.dumps(r));d.close()`;
function pending(o) {
  const result = spawnSync(o.paths.portablePython(), ['-B', '-I', '-c', pendingCode, path.join(repo, '.coding-tools/orchestration/ledger.sqlite3'), expectedPending.run_id, expectedPending.wave_id], { windowsHide: true, shell: false, timeout: 10000, encoding: 'utf8', maxBuffer: 16384 });
  if (result.error || result.status !== 0) fail('PENDING_RECORD_READ_FAILED');
  const hashes = JSON.parse(result.stdout.trim()); if (hashes.runs !== expectedPending.run_record_sha256 || hashes.waves !== expectedPending.wave_record_sha256) fail('PENDING_ACCEPTANCE_RECORD_CHANGED'); return { ...expectedPending, unchanged: true };
}
function assertCensus(value, liveAllowed = false) {
  if (value.mutated_canonical_ledger || !value.content_free || value.snapshot.integrity_check.join(',') !== 'ok' || value.lifecycle.awaiting_acceptance_runs.join(',') !== expectedPending.run_id || value.lifecycle.projection_drift || value.lifecycle.live_owned_runs.length || value.lifecycle.unexplained_active_runs || value.lifecycle.unbound_live_resource_residues || ['active_tool_calls', 'active_commands', 'starting_commands', 'active_background_operations', 'active_managed_processes', 'foreign_heavy_processes', 'active_agent_lanes'].some(name => value.counts[name] !== 0)) fail('CANONICAL_CENSUS_NOT_QUIESCENT');
  if (!value.safe && !(liveAllowed && value.code === 'RUNTIME_BUSY' && value.lifecycle.blockers.join(',') === 'live_runtime_state_process')) fail(value.code || 'CENSUS_REFUSED');
}
async function census(o, holdExclusive = false) { return canonicalLedgerCensus({ paths: o.paths, workspace: repo, allowAcceptancePending: true, holdExclusive, pythonStatusFn: async () => ({ installed: true, command: o.paths.portablePython(), prefixArgs: ['-B'] }) }); }
function censusSummary(value) { return { counts: value.counts, lifecycle: value.lifecycle, safe: value.safe, code: value.code, content_free: value.content_free, ledger_mutated: value.mutated_canonical_ledger, snapshot: { integrity_check: value.snapshot.integrity_check, logical_sha256: value.snapshot.logical_sha256 } }; }
function policies(o) {
  const exec = loadExecBridgePolicy(o.paths, { allowExpired: true });
  if (exec.workspace_id !== target.workspace_id || exec.workspace_generation !== target.workspace_generation || exec.device_id !== target.device_id || key(resolveRegisteredWorkspaceRoot(o.paths, exec)) !== key(repo)) fail('POLICY_REGISTERED_ROOT_MISMATCH');
  const files = Object.fromEntries(['controlPlaneFileReadPolicyFile', 'controlPlaneApprovedPatchPolicyFile', 'controlPlaneExecPolicyFile'].map(name => [name, sha(o.paths[name]())]));
  return { file_hashes: files, exec_policy_sha256: exec.policy_sha256, authority_mode: exec.authority_mode, expires_at_ms: exec.expires_at_ms, allowed_argv_prefixes: exec.allowed_argv_prefixes, canary_allowed: exec.allowed_argv_prefixes.some(prefix => prefix.every((word, i) => canaryArgv[i] === word)), standalone_sandbox_probe_performed: false };
}
async function observe(freeze = false) {
  const packageProof = verifyCandidate(), o = await observed(), row = await runtimeObservation(o), c = await census(o); assertCensus(c, o.owner.state === 'live');
  const receipt = { kind: 'r11_local_transition_observation', repository_head: head, target, ...row, package: packageProof, census: censusSummary(c), pending_acceptance: pending(o), vm_zero: zeroVm(false), policies: policies(o), runtime_mutated: false, server_mutated: false };
  receipt.activation_blocker = receipt.vm_zero.ok ? null : 'VM_OR_BACKEND_STILL_PRESENT_REQUIRES_SUPPORTED_OWNED_CLEANUP';
  if (o.tag === 'r10' && (sha(path.join(roots.r10, 'resources/app.asar')) !== 'c39a614d40f551f0ddef4e579bcd8ef5d8d3ad365bbd43e22693df8c1f9672e9' || sha(o.paths.executablePath()) !== '6e34a6705a647aaddda0d24f2152904006a504ab7a29ba516b686c6de29ef09f')) fail('CURRENT_R10_PACKAGE_CHANGED');
  if (freeze) { if (o.tag !== 'r10') fail('R10_PIN_REQUIRES_R10'); fs.writeFileSync(pinFile, JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' }); }
  emit({ phase: freeze ? 'r10_pin_frozen' : 'observation', ...receipt, ...(freeze ? { pin_sha256: sha(pinFile), pin_file: pinFile } : {}) });
}
function pin() { if (sha(pinFile) !== arg('pin-sha256')) fail('R10_OBSERVATION_PIN_CHANGED'); const p = read(pinFile); if (p.kind !== 'r11_local_transition_observation' || p.tag !== 'r10' || p.owner.state !== 'live' || JSON.stringify(p.target) !== JSON.stringify(target) || p.repository_head !== head || p.pending_acceptance.run_record_sha256 !== expectedPending.run_record_sha256 || p.pending_acceptance.wave_record_sha256 !== expectedPending.wave_record_sha256 || p.runtime_mutated !== false || p.server_mutated !== false) fail('R10_PIN_INVALID'); return p; }
function mutationGuard(requireRenewal = false, allowOldServerForCleanup = false) {
  verifyCandidate(); if (!process.argv.includes('--operator-approved-r11')) fail('R11_OPERATOR_APPROVAL_REQUIRED');
  const s = pinned('server'), age = Date.now() - s.observed_at_ms;
  const sourceAllowed = s.source_revision === serverRevision || allowOldServerForCleanup && s.source_revision === '395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5';
  if (!s.ok || s.host !== '100.116.112.22' || s.service !== 'codex-control-plane.service' || !sourceAllowed || s.binding_id !== target.binding_id || s.admission !== 'recovery' || age < 0 || age >= 600000 || !s.state || ['queued_actions', 'accepted_actions', 'open_writers', 'open_tasks', 'target_unsettled_actions'].some(name => s.state[name] !== 0)) fail('FRESH_QUIESCENT_R11_RECOVERY_RECEIPT_REQUIRED');
  if (!requireRenewal) return s;
  const n = pinned('renewal'), assignment = n.policy_assignment || n;
  if (!n.ok || n.source_revision !== serverRevision || n.binding_id !== target.binding_id || n.admission !== 'recovery' || n.host !== s.host || n.service !== s.service || n.service_instance_id !== s.service_instance_id || n.expires_at_ms !== n.requested_at_ms + 3600000 || n.expires_at_ms <= Date.now() || n.requested_at_ms > Date.now() || assignment.device_id !== target.device_id || assignment.workspace_id !== target.workspace_id || assignment.workspace_generation !== target.workspace_generation || key(n.root || '') !== key(repo) || n.profile !== target.profile) fail('EXACT_BOUND_60M_RENEWAL_REQUIRED');
  return n;
}
async function ownedCleanup(secretStore) {
  mutationGuard(false, true); const p = pin(), o = await exactOld(p), before = await runtimeObservation(o), c = await census(o); assertCensus(c, true); pending(o);
  if (before.agent.identity.state !== 'absent' || before.native.state !== 'live' || !same(before.native, p.native)) fail('QUIESCENT_EXACT_NATIVE_WITH_NO_AGENT_REQUIRED');
  const settings = read(o.paths.settingsFile()); if (key(settings.workspace || '') !== key(repo) || !Number.isSafeInteger(settings.mcpPort)) fail('NATIVE_CLEANUP_SETTINGS_TARGET_CHANGED');
  const { RuntimeOrchestrator, loopbackListenerPid } = require(path.join(services, 'runtimeOrchestrator'));
  const { FullCleanActivation } = require(path.join(services, 'fullCleanActivation'));
  const prior = last('r10_owned_cleanup_started');
  const operation = prior?.operation_id || `r11-transition-cleanup-${crypto.randomBytes(16).toString('hex')}`;
  const expires = prior?.expires_at_ms || Date.now() + 480000;
  if (expires <= Date.now() || prior && prior.old_native?.pid !== before.native.pid) fail('OWNED_CLEANUP_OPERATION_EXPIRED_OR_CHANGED');
  if (!prior) emit({ phase: 'r10_owned_cleanup_started', operation_id: operation, expires_at_ms: expires, old_native: before.native, vm_before: zeroVm(false) });
  const orchestrator = { settingsStore: { load: () => settings }, secrets: secretStore, native: { status: async () => {
    mutationGuard(false, true); await exactOld(p); const seen = await identity(before.native.pid); pending(o);
    if (seen.state !== 'live' || !same(seen, before.native) || Number(await loopbackListenerPid(settings.mcpPort)) !== before.native.pid) fail('EXACT_NATIVE_CLEANUP_LISTENER_CHANGED'); return true;
  } } };
  const coordinator = { now: Date.now, wait, _settings: () => settings, orchestrator: { prepareCodeActivation: options => RuntimeOrchestrator.prototype.prepareCodeActivation.call(orchestrator, options) } };
  const result = await FullCleanActivation.prototype._prepareFence.call(coordinator, operation, expires, null, true);
  const cleanup = result?.executor_cleanup;
  const safeCleanup = cleanup && typeof cleanup === 'object' ? Object.fromEntries(['state', 'confirmed', 'started_at_unix_ms', 'deadline_at_unix_ms', 'retry_after_ms'].filter(name => Object.hasOwn(cleanup, name)).map(name => [name, cleanup[name]])) : null;
  emit({ phase: 'r10_owned_cleanup_prepare_result', operation_id: operation, expires_at_ms: expires,
    result: { code: String(result?.code || '').replace(/[^A-Za-z0-9_.:-]/g, '').slice(0, 128), safe: result?.safe === true, fenced: result?.fenced === true,
      operation_id: typeof result?.operation_id === 'string' ? result.operation_id.replace(/[^A-Za-z0-9_.:-]/g, '').slice(0, 128) : null,
      fence_operation_id: typeof result?.fence_operation_id === 'string' ? result.fence_operation_id.replace(/[^A-Za-z0-9_.:-]/g, '').slice(0, 128) : null,
      workspace: result?.workspace && key(result.workspace) === key(repo) ? repo : null, workspace_matches: Boolean(result?.workspace && key(result.workspace) === key(repo)), executor_cleanup: safeCleanup } });
  FullCleanActivation.prototype._requireExactPreparedFence.call(coordinator, result, operation, 'before approved r11 retirement');
  const vm = zeroVm(), afterCensus = await census(o); assertCensus(afterCensus, true);
  emit({ phase: 'r10_owned_cleanup_confirmed', operation_id: operation, old_native: before.native, executor_cleanup: result.executor_cleanup, process_instance_id: result.process_instance_id, server_instance_id: result.server_instance_id, safe: result.safe, fenced: result.fenced, vm_zero: vm, pending_acceptance: pending(o), census: censusSummary(afterCensus), arbitrary_vm_termination: false });
}
async function exactOld(p) { const o = await observed(); if (o.tag !== 'r10' || JSON.stringify(descriptorSummary(o.descriptor)) !== JSON.stringify(p.descriptor) || !same(o.owner, p.owner)) fail('PINNED_R10_HOST_CHANGED'); return o; }
async function boundary(p, stopped = false, held = null) {
  mutationGuard(); const o = await exactOld(p);
  for (const component of [p.ui.identity, p.native, p.agent.identity]) { if (!component.pid) continue; const seen = await identity(component.pid); if (seen.state === 'unavailable' || seen.state === 'live' && !same(seen, component)) fail('EFFECT_BOUNDARY_OLD_COMPONENT_CHANGED'); }
  const currentAgent = await agentObservation(o); if (currentAgent.identity.state === 'live' && !same(currentAgent.identity, p.agent.identity)) fail('UNEXPECTED_AGENT_AT_EFFECT_BOUNDARY');
  const c = held || await census(o); assertCensus(c, !stopped); pending(o); zeroVm(); return o;
}
async function activate() {
  mutationGuard(); const p = pin(), o = await exactOld(p), before = await runtimeObservation(o);
  if (JSON.stringify(before.ui) !== JSON.stringify(p.ui) || !same(before.native, p.native) || before.tunnel.state !== 'absent') fail('PINNED_R10_COMPONENTS_CHANGED');
  if (before.agent.identity.state === 'live') {
    if (!same(before.agent.identity, p.agent.identity) || before.agent.last_iteration_state !== 'completed') fail('AGENT_NOT_EXACT_AND_QUIESCENT');
    await boundary(p); emit({ phase: 'old_agent_retirement_started', identity: before.agent.identity });
    const result = await terminateExactProcessTree(before.agent.identity, { includeDescendants: false }); emit({ phase: 'old_agent_retired', result });
  }
  const r = ipc(o), env = { ...process.env }; delete env.ELECTRON_RUN_AS_NODE;
  if (before.ui.identity.state === 'live') {
    await boundary(p); await r.client.call('client.suppress_ui_recovery', [{ instance_id: before.ui.instance_id, reason: 'operator_quit' }], r.options);
    await boundary(p); emit({ phase: 'old_ui_stop_started', identity: before.ui.identity });
    const result = spawnSync(o.paths.executablePath(), [`--dev-ui-stop=${before.ui.instance_id}`], { env, windowsHide: true, shell: false, timeout: 15000, stdio: 'ignore' });
    if (result.status !== 0) fail('EXACT_UI_STOP_SIGNAL_FAILED'); if (!await waitForExactProcessExit(before.ui.identity, { timeoutMs: 15000 })) fail('EXACT_UI_STOP_NOT_OBSERVED'); emit({ phase: 'old_ui_stopped' });
  }
  await boundary(p); emit({ phase: 'old_runtime_stop_started' }); await r.client.stop({ manual: true }, r.options);
  if (before.native.state === 'live' && !await waitForExactProcessExit(before.native, { timeoutMs: 15000 })) fail('EXACT_NATIVE_STOP_NOT_OBSERVED'); emit({ phase: 'old_runtime_stopped' });
  const c = await census(o, true);
  try {
    await boundary(p, true, c);
    for (const component of [before.ui.identity, before.native, before.agent.identity]) if (component.pid && (await identity(component.pid)).state !== 'absent') fail('OLD_COMPONENT_NOT_RETIRED');
    emit({ phase: 'old_host_retirement_started', identity: before.owner }); const result = await terminateExactProcessTree(before.owner, { includeDescendants: false }); emit({ phase: 'old_host_retired', result });
    mutationGuard(); zeroVm(); pending(o); if ((await identity(before.owner.pid)).state !== 'absent') fail('OLD_HOST_NOT_RETIRED');
    if (last('r11_spawn_attempted')) fail('R11_SPAWN_ALREADY_ATTEMPTED'); emit({ phase: 'r11_spawn_attempted' });
    const child = spawn(pathsFor('r11').executablePath(), [], { env, windowsHide: true, detached: true, stdio: 'ignore' }); await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); }); child.unref(); emit({ phase: 'r11_spawned', pid: child.pid });
  } finally { await c.release_exclusive_gate(); }
  const deadline = Date.now() + 45000;
  while (Date.now() < deadline) { try { const live = await observed(); if (live.tag === 'r11' && live.owner.state === 'live') { const row = await runtimeObservation(live); emit({ phase: 'r11_started', ...row }); return; } } catch (error) { if (!['RECOVERY_DESCRIPTOR_STALE', 'RECOVERY_DESCRIPTOR_MISSING', 'RECOVERY_HOST_UNAVAILABLE', 'RECOVERY_TIMEOUT'].includes(error.code)) throw error; } await wait(500); }
  fail('R11_START_NOT_OBSERVED');
}
async function currentR11() {
  const o = await observed(), started = last('r11_started'); if (o.tag !== 'r11' || o.owner.state !== 'live' || !started) fail('R11_STARTED_RECEIPT_REQUIRED');
  if (same(o.owner, started.owner) && o.descriptor.instance_id === started.descriptor.instance_id) return o;
  const refresh = last('r11_refresh'), durable = read(o.paths.activationEpochFile()).current, proof = durable?.state === 'READY' ? durable.verification?.final_census : durable?.verification;
  if (!refresh || refresh.state !== 'HANDOFF' || refresh.epoch !== durable?.activation_epoch_id || !['VERIFYING', 'READY'].includes(durable.state) || durable.error || !proof || proof.host_pid !== o.owner.pid || proof.host_instance_id !== o.descriptor.instance_id || proof.expected_old_host_pid !== started.owner.pid || proof.expected_old_host_instance_id !== started.descriptor.instance_id || ['workspace_matches', 'device_matches', 'revision_matches', 'process_identity_verified', 'epoch_matches'].some(name => proof[name] !== true)) fail('EXACT_R11_HANDOFF_PROOF_REQUIRED');
  return o;
}
async function policySync() {
  const n = mutationGuard(true), o = await currentR11(), c = await census(o); assertCensus(c, true); pending(o); zeroVm();
  const service = new ControlPlaneEnrollmentService({ paths: o.paths }); mutationGuard(true);
  const result = await service.installReadOnlyPolicyAssignment({ workspaceId: target.workspace_id, workspaceGeneration: target.workspace_generation, replaceExisting: true });
  if (result.expires_at_ms !== n.expires_at_ms) fail('SYNCED_METADATA_EXPIRY_MISMATCH'); emit({ phase: 'r11_metadata_policy_synced', expires_at_ms: result.expires_at_ms, policy_sha256: result.policy_sha256, pending_acceptance: pending(o), standing_policy_installed: false });
}
async function refresh() {
  mutationGuard(true); const o = await currentR11(), c = await census(o); assertCensus(c, true); pending(o); zeroVm();
  if (last('r11_refresh_attempted')) fail('R11_REFRESH_ALREADY_ATTEMPTED'); const r = ipc(o); emit({ phase: 'r11_refresh_attempted', old_host: o.owner, old_instance_id: o.descriptor.instance_id });
  const result = await r.client.restart({ refresh: true, mode: 'full_clean_refresh', sourceCheckpoint: null, allowAcceptancePending: true, reason: 'operator approved r11 initial proof activation preserving pending acceptance' }, { ...r.options, timeout: 120000 });
  emit({ phase: 'r11_refresh', state: result.state, epoch: result.activation_epoch_id, pending_acceptance: pending(o) });
}
async function startAgent() {
  const n = mutationGuard(true), o = await currentR11(); if (last('r11_agent_spawn_attempted')) fail('R11_AGENT_SPAWN_ALREADY_ATTEMPTED');
  if ((await agentObservation(o)).identity.state === 'live') fail('AGENT_ALREADY_LIVE'); const c = await census(o); assertCensus(c, true); pending(o); zeroVm();
  const service = new ControlPlaneEnrollmentService({ paths: o.paths }), maxIterations = Math.max(1, Math.floor((n.expires_at_ms - Date.now()) / 15000));
  if (maxIterations > 240) fail('BOUNDED_AGENT_DURATION_INVALID');
  const stdout = fs.openSync(path.join(__dirname, 'r11-agent.stdout.jsonl'), 'a'), stderr = fs.openSync(path.join(__dirname, 'r11-agent.stderr.log'), 'a'); let child;
  try {
    mutationGuard(true); emit({ phase: 'r11_agent_spawn_attempted', max_iterations: maxIterations });
    child = spawn(o.paths.portablePython(), ['-B', '-I', '-u', o.paths.controlPlaneNodeAgent(), 'run-connected-agent', '--config', o.paths.controlPlaneNodeConfigFile(), '--workspace-registry', o.paths.controlPlaneWorkspaceRegistryFile(), '--project-root', service.agentProjectRoot, '--node', o.paths.executablePath(), '--runtime-mode', 'packaged', '--interval-seconds', '15', '--max-backoff-seconds', '60', '--max-iterations', String(maxIterations)], { cwd: service.agentProjectRoot, env: safeEnrollmentEnvironment(process.env), windowsHide: true, detached: true, stdio: ['ignore', stdout, stderr] });
    await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); }); child.unref();
  } finally { fs.closeSync(stdout); fs.closeSync(stderr); }
  const seen = await identity(child.pid); if (seen.state !== 'live') fail('R11_AGENT_NOT_LIVE'); emit({ phase: 'r11_agent_spawned', identity: seen, interval_seconds: 15, max_iterations: maxIterations, authority_expires_at_ms: n.expires_at_ms });
}
async function proof() {
  verifyCandidate(); const o = await currentR11(), row = await runtimeObservation(o), c = await census(o); assertCensus(c, true); const localPolicies = policies(o);
  if (row.ui.identity.state !== 'live' || row.ui.registered !== true || row.ui.alive !== true || row.ui.ui_installation_id !== o.descriptor.installation_id || row.native.state !== 'live' || row.epoch.state !== 'READY' || row.epoch.admission_open !== true || row.native_epoch !== row.epoch.activation_epoch_id || row.readiness.fullyReady !== true || row.readiness.updateIncomplete !== false || row.agent.identity.state !== 'live' || row.agent.last_heartbeat_state !== 'succeeded' || Date.now() - row.agent.last_heartbeat_at_ms > 90000 || row.revisions.some(value => value.state !== 'current' || value.running_revision !== value.disk_revision || value.update_pending || value.pending_revision)) fail('R11_RUNTIME_PROOF_INCOMPLETE');
  emit({ phase: 'r11_final_runtime_proof', ok: true, ...row, package: verifyCandidate(), census: censusSummary(c), pending_acceptance: pending(o), policies: localPolicies, vm_zero: zeroVm(), acceptance_performed: false, live_sandbox_exec_proven: false, windows_rebooted: false, runtime_activated: true });
}
async function main() { const phase = process.argv[2]; if (phase === 'observe' || phase === 'preflight') await observe(); else if (phase === 'freeze') await observe(true); else if (phase === 'activate') await activate(); else if (phase === 'policy') await policySync(); else if (phase === 'refresh') await refresh(); else if (phase === 'agent') await startAgent(); else if (phase === 'status') { verifyCandidate(); emit({ phase: 'r11_status', ...await runtimeObservation(await currentR11()), pending_acceptance: pending(await currentR11()) }); } else if (phase === 'proof') await proof(); else fail('PHASE_INVALID'); }
function reportError(error) {
  const clean = value => String(value || '').replace(/[^A-Za-z0-9_.:-]/g, '').slice(0, 128);
  // Do not emit Error.message, child stdout/stderr, arguments or first stack
  // line: any of these may include credentials from a failed private request.
  const frames = String(error.stack || '').split(/\r?\n/).slice(1).map(line => {
    const matched = /\(?([^()]+?):(\d+):(\d+)\)?$/.exec(line.trim());
    if (!matched) return null;
    const file = path.basename(matched[1].replace(/^at\s+/, '').trim());
    return { file: clean(file), line: Number(matched[2]), column: Number(matched[3]) };
  }).filter(Boolean).slice(0, 8);
  emit({ ok: false, code: clean(error.code || 'R11_TRANSITION_REFUSED'), diagnostics: { syscall: clean(error.syscall), errno: Number.isSafeInteger(error.errno) ? error.errno : null, basename: clean(error.path ? path.basename(String(error.path)) : ''), stack_locations: frames }, no_automatic_retry: true });
}
function secretStoreObservation(value) {
  const names = ['found', 'valid', 'unavailable', 'recovered', 'mcpAuthToken', 'user_data_matches', 'session_data_matches', 'cli_profile_matches'];
  emit({ phase: 'native_secret_store_boolean_observation', ...Object.fromEntries(names.map(name => [name, value?.[name] === true])), secret_values_emitted: false });
}
module.exports = { ownedCleanup, pathsFor, reportError, secretStoreObservation };
if (require.main === module) main().catch(error => { reportError(error); process.exitCode = 1; });
