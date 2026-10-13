'use strict';

// One-off guarded operator transition for the already-authorized r4-timefix ->
// bfix packaged handoff.  This is intentionally evidence-local and has no
// general replacement API.  Every destructive step is preceded by the exact
// identity and cross-machine fence checks below.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '../../../..');
const oldCandidate = path.join(root, 'dist/windows-candidate-mxc-wsb-cbe1774-parallel-r4-timefix/win-unpacked');
const newCandidate = path.join(root, 'dist/windows-candidate-mxc-wsb-cbe1774-r4-timefix-bfix/win-unpacked');
const oldExe = path.join(oldCandidate, 'Coding Tools MCP.exe');
const newExe = path.join(newCandidate, 'Coding Tools MCP.exe');
const oldAppRoot = path.join(oldCandidate, 'resources/app.asar');
const newAppRoot = path.join(newCandidate, 'resources/app.asar');
const dataRoot = path.join(process.env.APPDATA, 'web-mcp-assistant');
const transitionRoot = __dirname;
const parityPath = path.join(root, '.coding-tools/reports/parallel-native-first-20261012/packaged-bfix-parity-recheck-20261013.json');
const smokePath = path.join(root, '.coding-tools/reports/parallel-native-first-20261012/packaged-bfix-smoke-20261013.json');
const serverFencePath = path.join(root, '.coding-tools/reports/parallel-native-first-20261012/server-readiness-bfix-handoff-20261013-2.json');
const outputPath = path.join(transitionRoot, `bfix-handoff-${Date.now()}.json`);
const digest = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
const fail = (code, message, details = {}) => { const e = new Error(message || code); e.code = code; e.details = details; throw e; };
const samePath = (a, b) => path.resolve(String(a)).toLowerCase() === path.resolve(String(b)).toLowerCase();
const now = () => Date.now();
const check = (condition, code, details) => { if (!condition) fail(code, code, details); };

const { RuntimePaths } = require(path.join(root, 'electron/services/runtimePaths'));
const { RecoveryIpcClient, loadRecoveryDescriptor } = require(path.join(root, 'electron/services/recoveryIpc'));
const { descriptorMatchesInstallation, descriptorRequestOptions, readVerifiedReadyHost } = require(path.join(root, 'electron/services/recoveryHostLauncher'));
const { processIdentityFrom, observeLifecycleProcessIdentity, sameProcessIdentity, terminateExactProcessTree } = require(path.join(root, 'electron/services/processIdentity'));
const { canonicalLedgerCensus } = require(path.join(root, 'electron/services/fullCleanActivation'));
const { assertExactPackagedResources, assertExactControlPlaneAdapter } = require(path.join(root, 'scripts/verify-packaged-resources'));

function pathsFor(candidate) {
  const executable = path.join(candidate, 'Coding Tools MCP.exe');
  return new RuntimePaths({ dataRoot, appRoot: path.join(candidate, 'resources/app.asar'), resourcesRoot: path.join(candidate, 'resources/resources'), executablePath: executable, runtimeMode: 'packaged' });
}

function noSandbox() {
  const result = spawnSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', "@(Get-Process -Name 'WindowsSandbox*','vmmemWSB','wxc-windows-sandbox-daemon','wxc-exec' -ErrorAction SilentlyContinue | Select-Object Id,ProcessName) | ConvertTo-Json -Compress"], { windowsHide: true, encoding: 'utf8', timeout: 10000, maxBuffer: 65536 });
  check(result.status === 0, 'SANDBOX_CENSUS_UNAVAILABLE');
  const found = JSON.parse(String(result.stdout || '').trim() || '[]');
  check(Array.isArray(found) && found.length === 0, 'LIVE_SANDBOX_PROCESS_REQUIRES_OWNERSHIP_REVIEW', { found });
  return { processes: [], observed_at_ms: now() };
}

function serverFence() {
  const fence = read(serverFencePath);
  const age = now() - Number(fence.capture_completed_at_ms);
  const work = fence.whole_device_census || {};
  const global = fence.global_live_work_by_scope || {};
  const historic = fence.historical_unknown_actions_preserved || [];
  const expectedQuarantines = ['act_9db9b985a3d648b5b941f2e13a30ee47', 'act_52409c69f1b84e08bb3fdd86747f79c3', 'act_3849e259d55546639794cec40f63fea8'].sort();
  const targetScopes = new Set(['workspace_f93b5bac9dc74fae9cea66f44c4ebc94:generation_a420c8bfcfcb4e42b5bb7fc5e5cec097', 'workspace_bc86004be2684b958ab7a9a6f9530cd7:generation_03f9c04f1b14414fa4bfa7d91cc8ea7a']);
  check(fence.ok === true && fence.service_stable === true && fence.sqlite_integrity_ok === true && fence.source_startup_disk_attestation_matches === true, 'FRESH_UBUNTU_FENCE_INVALID');
  check(Number.isFinite(age) && age >= 0 && age <= 120000, 'FRESH_UBUNTU_FENCE_EXPIRED', { age });
  check(['live_open_tasks', 'live_writers', 'queued_actions', 'active_dispatch_actions'].every(k => work[k] === 0), 'UBUNTU_LIVE_WORK_PRESENT', { work });
  check(expectedQuarantines.every(id => historic.some(x => x.action_id === id)), 'HISTORICAL_UNKNOWN_SET_CHANGED');
  check(historic.every(x => x.delivery_state === 'reconcile_required' && x.disposition === 'quarantined_unknown' && x.expired === true && Number.isInteger(x.reconciled_at_ms) && x.reconciled_at_ms > 0), 'HISTORICAL_UNKNOWN_NOT_QUARANTINED');
  const foreignExpired = (global.blocking_action_identities || []).filter(x => x.expired === true && x.delivery_state === 'dispatch_unconfirmed' && !targetScopes.has(`${x.workspace_id}:${x.workspace_generation}`));
  check((global.active_actions || []).every(x => foreignExpired.some(y => y.device_id === x.device_id && y.workspace_id === x.workspace_id && y.workspace_generation === x.workspace_generation && y.delivery_state === x.delivery_state)), 'UBUNTU_ACTIVE_ACTION_PRESENT');
  check((global.blocking_action_identities || []).every(x => foreignExpired.some(y => y.action_id === x.action_id)), 'UBUNTU_BLOCKING_ACTION_PRESENT');
  return { path: serverFencePath, sha256: digest(serverFencePath), capture_completed_at_ms: fence.capture_completed_at_ms, age_ms: age, preserved_unknown_actions: expectedQuarantines };
}

async function observeCurrent() {
  const paths = pathsFor(oldCandidate);
  const client = new RecoveryIpcClient({ paths });
  const verified = await readVerifiedReadyHost(client, paths, loadRecoveryDescriptor, 2, { allowAdmissionBlocked: true });
  check(verified && descriptorMatchesInstallation(verified.descriptor, paths.runtimeIdentity()), 'CURRENT_OWNER_INSTALLATION_MISMATCH');
  const opts = descriptorRequestOptions(verified.descriptor);
  const [runtime, epoch, status] = await Promise.all([
    client.call('runtime.lightweight_snapshot', [], opts), client.call('runtime.activation_epoch_status', [], opts), client.call('recovery.status', [{ fresh: true }], opts)
  ]);
  const census = await canonicalLedgerCensus({ paths, workspace: root, allowAcceptancePending: true });
  check(census.safe === true && census.lifecycle?.unexplained_active_runs === 0 && census.lifecycle?.unbound_live_resource_residues === 0, 'LOCAL_CANONICAL_CENSUS_NOT_IDLE', { census: { safe: census.safe, lifecycle: census.lifecycle, counts: census.counts } });
  check(['active_tool_calls', 'active_commands', 'starting_commands', 'active_background_operations', 'active_managed_processes', 'foreign_heavy_processes', 'active_agent_lanes', 'owned_codex_sidecar_residues'].every(k => census.counts?.[k] === 0), 'LOCAL_ACTIVE_WORK_PRESENT', { counts: census.counts });
  const identity = processIdentityFrom(verified.descriptor);
  const observed = await observeLifecycleProcessIdentity(identity.pid);
  check(sameProcessIdentity(identity, observed), 'CURRENT_OWNER_PROCESS_IDENTITY_CHANGED', { expected: identity, observed });
  check(runtime?.mcpRunning === false && runtime?.nativeAlive === false, 'CURRENT_RUNTIME_NOT_STOPPED', { runtime });
  check(status?.electron_ui_recovery?.suppressed === true && status?.electron_ui_recovery?.alive === false, 'UI_NOT_SUPPRESSED', { ui: status?.electron_ui_recovery });
  const manifestPath = path.join(dataRoot, 'recovery-supervisor/manifest.json');
  const manifest = read(manifestPath);
  check(manifest.mode === 'packaged' && samePath(manifest.app_root, oldCandidate) && samePath(manifest.executable, oldExe), 'CURRENT_SUPERVISOR_MANIFEST_MISMATCH', { manifest });
  return { paths, client, verified, opts, runtime, epoch, status, census, identity, observed, manifest, manifest_sha256: digest(manifestPath) };
}

function packageProof() {
  const parity = read(parityPath); const smoke = read(smokePath);
  check(parity.ok === true && parity.proof_kind === 'exact_source_package_parity' && samePath(parity.candidate, newCandidate), 'BFIX_PARITY_RECEIPT_INVALID');
  check(digest(newExe) === parity.executable_sha256 && digest(newAppRoot) === parity.app_asar_sha256, 'BFIX_PACKAGE_HASH_CHANGED');
  check(smoke.ok === true && smoke.package?.executable === true && smoke.package?.app_asar === true && smoke.isolation?.production_descriptor_stable === true && smoke.recovery?.host_ready === true && smoke.recovery?.mcp_alive === true && smoke.supervisor?.healthy === true && smoke.supervisor?.live_owner_fail_closed === true, 'BFIX_SMOKE_RECEIPT_INVALID');
  const resources = assertExactPackagedResources(path.join(root, 'resources'), path.join(newCandidate, 'resources/resources'), { separatelyVerifiedTopLevelDirectories: ['control-plane'] });
  const adapter = assertExactControlPlaneAdapter(path.join(root, 'control-plane/control_plane'), path.join(newCandidate, 'resources/resources/control-plane'));
  return { parity_sha256: digest(parityPath), smoke_sha256: digest(smokePath), executable_sha256: parity.executable_sha256, app_asar_sha256: parity.app_asar_sha256, resources, adapter };
}

async function main() {
  const apply = process.argv.includes('--apply');
  const fence = serverFence();
  const proof = packageProof();
  const current = await observeCurrent();
  const sandbox = noSandbox();
  const base = { schema_version: 1, operation: 'bfix_packaged_handoff', observed_at: new Date().toISOString(), git_head: require('node:child_process').execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(), old_candidate: oldCandidate, new_candidate: newCandidate, current_owner: { owner_pid: current.verified.descriptor.owner_pid, owner_process_start_token: current.verified.descriptor.owner_process_start_token, instance_id: current.verified.descriptor.instance_id, installation_id: current.verified.descriptor.installation_id }, current_runtime: { mcpRunning: current.runtime.mcpRunning, nativeAlive: current.runtime.nativeAlive, activation_epoch_id: current.epoch.activation_epoch_id, activation_state: current.epoch.state, admission_open: current.epoch.admission_open }, current_census: { safe: current.census.safe, counts: current.census.counts }, current_manifest_sha256: current.manifest_sha256, fence, proof, sandbox, mutation_started: false };
  if (!apply) { base.ok = true; base.mode = 'preflight'; base.decision = 'READY_TO_APPLY'; fs.writeFileSync(outputPath, JSON.stringify(base, null, 2) + '\n', { flag: 'wx' }); console.log(JSON.stringify({ ok: true, mode: 'preflight', report: outputPath, owner_pid: current.identity.pid, bfix_executable_sha256: proof.executable_sha256 })); return; }
  const intentPath = path.join(transitionRoot, 'bfix-handoff-intent.json');
  check(!fs.existsSync(intentPath), 'BFIX_HANDOFF_ALREADY_STARTED');
  fs.writeFileSync(intentPath, JSON.stringify({ schema_version: 1, operation: 'bfix-packaged-handoff-intent', observed_at: new Date().toISOString(), old_owner: base.current_owner, old_manifest_sha256: current.manifest_sha256, new_candidate: newCandidate, fence, proof, no_replay: true }, null, 2) + '\n', { flag: 'wx' });
  base.mutation_started = true; base.intent = intentPath;
  const termination = await terminateExactProcessTree(current.identity, { observeProcessIdentity: observeLifecycleProcessIdentity, timeoutMs: 15000 });
  base.termination = termination;
  const supervisor = path.join(root, 'resources/recovery-supervisor/recovery-supervisor.ps1');
  const install = spawnSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', supervisor, '-Action', 'Install', '-Packaged', '-AppRoot', newCandidate, '-Executable', newExe], { cwd: root, windowsHide: true, encoding: 'utf8', timeout: 60000, maxBuffer: 131072 });
  check(install.status === 0, 'BFIX_SUPERVISOR_INSTALL_FAILED', { exit_code: install.status, output: String(install.stdout || install.stderr || '').slice(0, 1000) });
  base.install_output = String(install.stdout || '').slice(0, 1000);
  const manifestPath = path.join(dataRoot, 'recovery-supervisor/manifest.json');
  const installed = read(manifestPath);
  check(installed.mode === 'packaged' && samePath(installed.app_root, newCandidate) && samePath(installed.executable, newExe) && installed.executable_sha256 === proof.executable_sha256, 'BFIX_SUPERVISOR_MANIFEST_NOT_INSTALLED');
  base.installed_manifest = { app_root: installed.app_root, executable: installed.executable, executable_sha256: installed.executable_sha256, sha256: digest(manifestPath) };
  base.ok = true; base.mode = 'apply'; base.decision = 'BFIX_INSTALLED_AWAITING_ACTIVATION';
  fs.writeFileSync(outputPath, JSON.stringify(base, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ ok: true, mode: 'apply', report: outputPath, installed_manifest_sha256: base.installed_manifest.sha256 }));
}

main().catch(error => { const report = { schema_version: 1, operation: 'bfix_packaged_handoff', observed_at: new Date().toISOString(), ok: false, code: error.code || 'BFIX_HANDOFF_FAILED', message: String(error.message || error), details: error.details || {}, mutation_started: false }; try { fs.writeFileSync(outputPath, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' }); report.report = outputPath; } catch {} console.error(JSON.stringify(report)); process.exitCode = 1; });
