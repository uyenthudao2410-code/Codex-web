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
const pinFile = path.join(__dirname, 'unused'), journal = path.join(__dirname, 'resume.jsonl');
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

const runtimePaths = pathsFor('r11');
const oldProofFile = path.join(__dirname, 'old-r11-proof.json');
const oldProofSha = '4c9795e1e70d9b13c436e48addc2e8191d8bd318ddd91bbb5c484949f884bf32';
const launcherFile = path.join(__dirname, 'breakaway-launch.py');
const launcherSha = '810164f48412ed9c2cedd9d4e5c649bd45aa517696ea6ef2e053c21a789b5fc9';
const { validatePersistedReadyConnectorProof } = require(path.join(services, 'recoveryHost'));
const oldEpoch = 'activation-mv3yg71m-8c2f1e1646c843a8789b4578ad780284';
function approved(requireRenewal = false) {
  verifyCandidate();
  if (!process.argv.includes('--operator-approved-r11-resume') || sha(__filename) !== arg('helper-sha256')) fail('EXACT_RESUME_APPROVAL_REQUIRED');
  const wrapper = pinned('server'), s = wrapper.public_receipts ? wrapper.public_receipts[0] : wrapper;
  const age = Date.now() - s.observed_at_ms;
  if (!s.ok || s.host !== '100.116.112.22' || s.service !== 'codex-control-plane.service' || s.source_revision !== serverRevision || s.binding_id !== target.binding_id || s.admission !== 'recovery' || age < 0 || age >= 60000 || !s.state || ['queued_actions', 'accepted_actions', 'open_writers', 'open_tasks', 'target_unsettled_actions'].some(name => s.state[name] !== 0)) fail('FRESH_QUIESCENT_RECOVERY_REQUIRED');
  if (!requireRenewal) return s;
  const wrapped = pinned('renewal'), n = wrapped.public_receipts ? wrapped.public_receipts[0] : wrapped, a = n.policy_assignment || n;
  if (!n.ok || n.source_revision !== serverRevision || n.admission !== 'recovery' || n.host !== s.host || n.service !== s.service || n.service_instance_id !== s.service_instance_id || n.binding_id !== target.binding_id || !Number.isSafeInteger(n.requested_at_ms) || n.requested_at_ms <= 1791734596302 || n.expires_at_ms !== n.requested_at_ms + 3600000 || n.requested_at_ms > Date.now() || n.expires_at_ms <= Date.now() || a.device_id !== target.device_id || a.workspace_id !== target.workspace_id || a.workspace_generation !== target.workspace_generation || key(n.root || '') !== key(repo) || n.profile !== target.profile) fail('NEW_EXACT_APPROVED_60M_RENEWAL_REQUIRED');
  return n;
}
function launch(request) {
  if (sha(launcherFile) !== launcherSha) fail('BREAKAWAY_HELPER_CHANGED');
  const result = spawnSync(runtimePaths.portablePython(), ['-B', '-I', launcherFile], { input: JSON.stringify(request), windowsHide: true, shell: false, timeout: 10000, encoding: 'utf8', maxBuffer: 16384 });
  let value; try { value = JSON.parse(result.stdout.trim()); } catch { fail('BREAKAWAY_RECEIPT_UNAVAILABLE'); }
  if (result.error || result.status !== 0 || value.ok !== true) { emit({ phase: 'breakaway_refused', ...value }); fail(value.code || 'BREAKAWAY_REFUSED'); }
  return value;
}
function reserve(mode) {
  const file = path.join(__dirname, `${mode}-attempt.json`), fd = fs.openSync(file, 'wx');
  try { fs.writeFileSync(fd, JSON.stringify({ mode, at_ms: Date.now(), helper_sha256: sha(__filename), no_automatic_retry: true }) + '\n'); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
}
async function preflight() {
  const packageProof = verifyCandidate();
  if (sha(oldProofFile) !== oldProofSha) fail('OLD_R11_PROOF_CHANGED');
  const old = read(oldProofFile), gone = [];
  for (const component of [old.owner, old.ui.identity, old.native, old.agent.identity]) {
    const value = await identity(component.pid); if (value.state !== 'absent') fail('OLD_COMPONENT_PID_NOT_ABSENT'); gone.push(value);
  }
  const descriptor = read(runtimePaths.recoveryHostDescriptorFile());
  if (!descriptorMatchesInstallation(descriptor, runtimePaths.runtimeIdentity()) || descriptor.instance_id !== old.descriptor.instance_id || descriptor.owner_pid !== old.owner.pid || descriptor.owner_process_start_token !== old.owner.process_start_token) fail('OLD_DESCRIPTOR_CHANGED_BEFORE_RESUME');
  const c = await census({ paths: runtimePaths }); assertCensus(c, false);
  const durable = read(runtimePaths.activationEpochFile()).current;
  const readyProof = validatePersistedReadyConnectorProof(durable, { expectedExecutionRole: 'central_executor' });
  if (!readyProof.valid || durable.activation_epoch_id !== oldEpoch) fail('PERSISTED_READY_PROOF_INVALID');
  const processes = powershell("$ErrorActionPreference='Stop'; @{candidate_process_count=@(Get-CimInstance Win32_Process -Filter \"Name='Coding Tools MCP.exe'\").Count;content_free=$true}|ConvertTo-Json -Compress");
  if (processes.content_free !== true || processes.candidate_process_count !== 0) fail('OTHER_PACKAGE_PROCESS_PRESENT');
  return { package: packageProof, old_components: gone, census: censusSummary(c), pending_acceptance: pending({ paths: runtimePaths }), vm_zero: zeroVm(), parent_job: launch({ mode: 'observe' }).parent_job, persisted_epoch: oldEpoch, policies: policies({ paths: runtimePaths }), runtime_mutated: false };
}
const descriptorSummary = d => ({ installation_id: d.installation_id, instance_id: d.instance_id, owner_pid: d.owner_pid, owner_process_start_token: d.owner_process_start_token });
async function current() {
  verifyCandidate(); const started = last('resume_runtime_spawned'); if (!started) fail('NEW_RESUME_SPAWN_RECEIPT_REQUIRED');
  const descriptor = loadRecoveryDescriptor(runtimePaths), owner = await identity(descriptor.owner_pid);
  if (!descriptorMatchesInstallation(descriptor, runtimePaths.runtimeIdentity()) || !same(owner, started.identity) || descriptor.owner_pid !== started.pid || descriptor.instance_id === read(oldProofFile).descriptor.instance_id) fail('RESUME_DESCRIPTOR_PROVENANCE_UNPROVEN');
  const client = new RecoveryIpcClient({ paths: runtimePaths }), options = descriptorRequestOptions(descriptor);
  const ping = await client.ping(options);
  if (ping?.instance_id !== descriptor.instance_id || Number(ping?.pid) !== owner.pid || ping?.process_start_token !== owner.process_start_token) fail('RESUME_IPC_PROVENANCE_UNPROVEN');
  return { descriptor, owner, paths: runtimePaths, client, options };
}
async function activate() {
  approved(); const before = await preflight(), held = await census({ paths: runtimePaths }, true); assertCensus(held, false);
  try {
    approved(); zeroVm(); pending({ paths: runtimePaths });
    for (const component of before.old_components) if ((await identity(component.pid)).state !== 'absent') fail('OLD_COMPONENT_REAPPEARED');
    reserve('runtime'); emit({ phase: 'resume_runtime_spawn_attempted', before });
    const result = launch({ mode: 'runtime', operator_approved: true }), seen = await identity(result.pid);
    if (seen.state !== 'live') fail('RESUME_RUNTIME_NOT_LIVE');
    emit({ phase: 'resume_runtime_spawned', ...result, identity: seen, pending_acceptance: pending({ paths: runtimePaths }) });
  } finally { await held.release_exclusive_gate(); }
  const deadline = Date.now() + 45000;
  while (Date.now() < deadline) {
    try { const o = await current(); emit({ phase: 'resume_descriptor_adopted', descriptor: descriptorSummary(o.descriptor), owner: o.owner, pending_acceptance: pending(o), runtime_mutated: true }); return; }
    catch (error) { if (!['RECOVERY_DESCRIPTOR_MISSING', 'RECOVERY_DESCRIPTOR_STALE', 'RECOVERY_HOST_UNAVAILABLE', 'RECOVERY_TIMEOUT'].includes(error.code)) throw error; }
    await wait(500);
  }
  fail('RESUME_DESCRIPTOR_NOT_OBSERVED_NO_RETRY');
}
async function status() {
  const o = await current(), value = await o.client.status({ ...o.options, fresh: true }), snapshot = await o.client.call('runtime.lightweight_snapshot', [], o.options), c = await census(o); assertCensus(c, true);
  const pick = (source, names) => Object.fromEntries(names.map(name => [name, source?.[name] ?? null]));
  emit({ phase: 'resume_status', descriptor: descriptorSummary(o.descriptor), owner: o.owner,
    epoch: pick(value.activation_epoch, ['activation_epoch_id', 'state', 'admission_open', 'update_incomplete']),
    readiness: pick(snapshot, ['fullyReady', 'localReady', 'centralConnected', 'authorityReady', 'updateIncomplete']),
    census: censusSummary(c), pending_acceptance: pending(o), vm_zero: zeroVm(false), runtime_mutated: false });
}
async function policy() {
  const n = approved(true), o = await current(), c = await census(o); assertCensus(c, true); pending(o); zeroVm();
  const service = new ControlPlaneEnrollmentService({ paths: o.paths }); approved(true);
  const result = await service.installReadOnlyPolicyAssignment({ workspaceId: target.workspace_id, workspaceGeneration: target.workspace_generation, replaceExisting: true });
  if (result.expires_at_ms !== n.expires_at_ms) fail('RESUME_POLICY_EXPIRY_MISMATCH');
  emit({ phase: 'resume_metadata_policy_synced', expires_at_ms: result.expires_at_ms, policy_sha256: result.policy_sha256, pending_acceptance: pending(o) });
}
async function agent() {
  const n = approved(true), o = await current(), c = await census(o); assertCensus(c, true); pending(o); zeroVm();
  const raw = read(path.join(dataRoot, 'control-plane-connected-agent-status.json'));
  if (raw.agent_pid && (await identity(raw.agent_pid)).state !== 'absent') fail('EXISTING_AGENT_PID_NOT_ABSENT');
  const synced = last('resume_metadata_policy_synced'); if (!synced || synced.expires_at_ms !== n.expires_at_ms) fail('NEW_POLICY_SYNC_RECEIPT_REQUIRED');
  const iterations = Math.floor((n.expires_at_ms - Date.now()) / 15000); if (iterations < 1 || iterations > 240) fail('AGENT_DURATION_INVALID');
  approved(true); reserve('agent'); emit({ phase: 'resume_agent_spawn_attempted', max_iterations: iterations, authority_expires_at_ms: n.expires_at_ms });
  const result = launch({ mode: 'agent', operator_approved: true, max_iterations: iterations }), seen = await identity(result.pid);
  if (seen.state !== 'live') fail('RESUME_AGENT_NOT_LIVE'); emit({ phase: 'resume_agent_spawned', ...result, identity: seen, max_iterations: iterations, authority_expires_at_ms: n.expires_at_ms, hard_wallclock_expiry: false });
}
async function main() {
  const phase = process.argv[2];
  if (phase === 'preflight') emit({ phase: 'resume_preflight', ...await preflight() });
  else if (phase === 'activate') await activate(); else if (phase === 'status') await status(); else if (phase === 'policy') await policy(); else if (phase === 'agent') await agent(); else fail('PHASE_INVALID');
}
module.exports = { preflight, launch, approved, reserve };
if (require.main === module) main().catch(error => { emit({ ok: false, code: String(error.code || 'RESUME_REFUSED').replace(/[^A-Za-z0-9_.:-]/g, '').slice(0, 128), no_automatic_retry: true, acceptance_performed: false }); process.exitCode = 1; });

