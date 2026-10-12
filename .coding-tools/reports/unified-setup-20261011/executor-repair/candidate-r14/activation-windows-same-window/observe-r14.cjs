'use strict';
// Read-only preparation. No process stop/start, IPC mutation, policy install or server write.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const { spawnSync, execFileSync } = require('node:child_process');
const prior = require('../../candidate-r13/activation-windows-5h/transition-r13.cjs');
const finalPacket = require('./transition-r14.cjs');
const services = 'E:\\Github\\Tools-Codex-web\\electron\\services';
const { RecoveryIpcClient, loadRecoveryDescriptor } = require(path.join(services, 'recoveryIpc'));
const launcher = require(path.join(services, 'recoveryHostLauncher'));
const { observeLifecycleProcessIdentity: identity, sameProcessIdentity: same } = require(path.join(services, 'processIdentity'));
const { canonicalLedgerCensus } = require(path.join(services, 'fullCleanActivation'));
const target = prior.target, paths = prior.pathsFor('r13');
const expected = { head: '2c554f59cb7b8ffc86ce5e0e28076c792777642f', host_pid: 11476, agent_pid: 10396,
  authority_expires_at_ms: 1791776571067, tag: 'source-fingerprint-1012-r13' };
const families = [
  { run_id: '95e909f0040a448faa9f1f3257e2ee2c', wave_id: 'c101beadfc6d4f2fbc13845052c84693' },
  { run_id: 'fbaf4b0700d04794af4062671c1bcd2b', wave_id: 'e712eca9463e465fb1905264c998f50c' }
];
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const sha = file => digest(fs.readFileSync(file));
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const need = (ok, code) => { if (!ok) throw Object.assign(new Error(), { code }); };
const pick = (value, keys) => Object.fromEntries(keys.map(k => [k, value?.[k] ?? null]));
const key = value => path.resolve(value).toLowerCase();
const exactSet = (actual, wanted) => JSON.stringify([...actual].sort()) === JSON.stringify([...wanted].sort());
const ps = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe';
const env = { ...process.env, PSModulePath: path.join(path.dirname(ps), 'Modules') };
function powershell(script) {
  const r = spawnSync(ps, ['-NoProfile', '-NonInteractive', '-Command', script], { env, windowsHide: true,
    shell: false, timeout: 15000, encoding: 'utf8', maxBuffer: 4096 });
  need(!r.error && r.status === 0, 'CONTENT_FREE_PROCESS_QUERY_FAILED');
  return JSON.parse(r.stdout.replace(/^\uFEFF/, '').trim());
}
function zeroVm() {
  const v = powershell("$ErrorActionPreference='Stop'; $n=@('WindowsSandbox','WindowsSandboxClient','WindowsSandboxServer','WindowsSandboxRemoteSession','vmmemWindowsSandbox'); @{host_count=@(Get-Process | Where-Object {$n -contains $_.ProcessName}).Count;backend_count=@(Get-CimInstance Win32_Process -Filter \"Name='wxc-windows-sandbox-daemon.exe' OR Name='wxc-exec.exe' OR Name='wxc-windows-sandbox-guest.exe'\").Count;content_free=$true} | ConvertTo-Json -Compress");
  need(v.content_free === true, 'VM_OBSERVATION_NOT_CONTENT_FREE');
  return v;
}
function pending() {
  const code = `import hashlib,json,sqlite3,sys\nfrom pathlib import Path\nfrom contextlib import closing\nresult=[]\nwith closing(sqlite3.connect(Path(sys.argv[1]).resolve(strict=True).as_uri()+"?mode=ro",uri=True,timeout=10)) as d:\n d.row_factory=sqlite3.Row;d.execute("PRAGMA query_only=ON");d.execute("BEGIN")\n for f in json.loads(sys.argv[2]):\n  record=dict(f)\n  for t,c,field in (("runs","run_id","run_record_sha256"),("waves","wave_id","wave_record_sha256")):\n   rows=d.execute(f"SELECT * FROM {t} WHERE {c}=?",(f[c],)).fetchall()\n   if len(rows)!=1:raise SystemExit(2)\n   record[field]=hashlib.sha256(json.dumps(dict(rows[0]),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()\n  result.append(record)\n d.rollback()\nprint(json.dumps({"families":result,"query_only":True,"mutated":False}))`;
  const r = spawnSync(paths.portablePython(), ['-B', '-I', '-c', code,
    path.join(target.root, '.coding-tools/orchestration/ledger.sqlite3'), JSON.stringify(families)], {
    windowsHide: true, shell: false, timeout: 15000, encoding: 'utf8', maxBuffer: 4096 });
  need(!r.error && r.status === 0, 'QUERY_ONLY_PENDING_FREEZE_FAILED');
  return JSON.parse(r.stdout);
}
function policies() {
  const summaries = {};
  for (const kind of ['ReadOnly', 'FileRead', 'ApprovedPatch', 'Exec']) {
    const file = paths['controlPlane' + kind + 'PolicyFile'](), value = read(file);
    need(value.enabled === true && ['device_id', 'workspace_id', 'workspace_generation', 'owner_id', 'endpoint_id', 'server_origin'].every(k => value[k] === target[k]), 'POLICY_TARGET_CHANGED');
    need(prior.canonical(value.facade_contract) === prior.canonical(prior.facade), 'POLICY_CONTRACT_CHANGED');
    need(kind === 'ReadOnly' ? value.expires_at_ms === expected.authority_expires_at_ms
      : value.authority_mode === 'standing' && value.expires_at_ms === null, 'POLICY_WINDOW_CHANGED');
    summaries[kind] = { file_sha256: sha(file), ...pick(value, ['facade_contract', 'expires_at_ms', 'authority_mode']) };
  }
  return summaries;
}
async function observe() {
  const packageProof = finalPacket.verifyCandidate();
  need(execFileSync('git', ['--no-optional-locks', 'rev-parse', 'HEAD'], { cwd: target.root, encoding: 'utf8', windowsHide: true }).trim() === expected.head, 'HEAD_CHANGED');
  need(key(process.env.APPDATA || '') === key(path.dirname(paths.dataRoot())), 'PROFILE_CHANGED');
  const descriptor = loadRecoveryDescriptor(paths);
  need(launcher.descriptorMatchesInstallation(descriptor, paths.runtimeIdentity()) && descriptor.owner_pid === expected.host_pid
    && descriptor.host === '127.0.0.1' && descriptor.owner === 'recovery-host', 'EXPECTED_R13_HOST_CHANGED');
  const owner = await identity(descriptor.owner_pid);
  need(owner.state === 'live' && same(owner, { pid: descriptor.owner_pid, process_start_token: descriptor.owner_process_start_token }), 'EXACT_R13_HOST_NOT_LIVE');
  const client = new RecoveryIpcClient({ paths }), options = launcher.descriptorRequestOptions(descriptor), ping = await client.ping(options);
  need(ping.pid === owner.pid && ping.instance_id === descriptor.instance_id && ping.process_start_token === owner.process_start_token, 'HOST_PING_IDENTITY_CHANGED');
  const status = await client.status({ ...options, fresh: true });
  const snapshot = await client.call('runtime.lightweight_snapshot', [], options);
  const nativeIdentity = await client.call('runtime.identity_observation', [], options);
  const raw = read(paths.stateFile()), agentRaw = read(path.join(paths.dataRoot(), 'control-plane-connected-agent-status.json'));
  need(agentRaw.agent_pid === expected.agent_pid, 'EXPECTED_AGENT_CHANGED');
  const agent = await identity(agentRaw.agent_pid);
  need(agent.state === 'live', 'EXACT_AGENT_NOT_LIVE');
  const native = raw.nativePid ? await identity(raw.nativePid) : { state: 'absent', pid: null };
  const ui = status.electron_ui_recovery?.pid ? await identity(status.electron_ui_recovery.pid) : { state: 'absent', pid: null };
  need(native.state !== 'unavailable' && ui.state !== 'unavailable' && (native.state !== 'live' || same(native, {
    pid: raw.nativePid, process_start_token: raw.nativeProcessStartToken })), 'COMPONENT_IDENTITY_UNVERIFIED');
  const c = await canonicalLedgerCensus({ paths, workspace: target.root, allowAcceptancePending: true,
    pythonStatusFn: async () => ({ installed: true, command: paths.portablePython(), prefixArgs: ['-B'] }) });
  need(c.mutated_canonical_ledger === false && c.content_free === true && c.snapshot?.query_only === true && c.snapshot?.immutable === true
    && JSON.stringify(c.snapshot.integrity_check) === '["ok"]' && c.snapshot.foreign_key_check_rows === 0
    && exactSet(c.lifecycle.awaiting_acceptance_runs, families.map(f => f.run_id))
    && c.lifecycle.projection_drift === false && c.lifecycle.live_owned_runs.length === 0 && c.lifecycle.unexplained_active_runs === 0
    && c.lifecycle.unbound_live_resource_residues === 0 && ['active_tool_calls', 'active_commands', 'starting_commands', 'active_background_operations',
      'active_managed_processes', 'foreign_heavy_processes', 'active_agent_lanes'].every(k => c.counts[k] === 0)
    && (c.safe === true || c.code === 'RUNTIME_BUSY' && JSON.stringify(c.lifecycle.blockers) === '["live_runtime_state_process"]'), 'CANONICAL_CENSUS_NOT_QUIESCENT');
  const result = { kind: 'r14_read_only_transition_preparation', observed_at_ms: Date.now(), repository_head: expected.head,
    target, package: packageProof, current_runtime_tag: expected.tag, authority_expires_at_ms: expected.authority_expires_at_ms,
    descriptor: pick(descriptor, ['installation_id', 'instance_id', 'owner_pid', 'owner_process_start_token', 'activation_epoch_id']), owner,
    ui: { identity: ui, ...pick(status.electron_ui_recovery, ['instance_id', 'alive', 'registered', 'ui_installation_id']) }, native,
    agent: { identity: agent, ...pick(agentRaw, ['agent_instance_id', 'agent_started_at_ms', 'updated_at_ms', 'last_iteration_state', 'last_heartbeat_state', 'last_heartbeat_at_ms', 'last_error_code']) },
    epoch: pick(status.activation_epoch, ['activation_epoch_id', 'state', 'admission_open', 'update_incomplete']),
    readiness: pick(snapshot, ['fullyReady', 'localReady', 'componentsReady', 'centralConnected', 'authorityReady', 'updateIncomplete', 'failureKind', 'centralStatusReason']),
    native_identity: pick(nativeIdentity, ['observation_schema_version', 'mcp_process_instance_id', 'mcp_server_instance_id', 'activation_epoch_id', 'current_activation_epoch_id', 'tool_contract_sha256', 'mcp_ready', 'identity_current']),
    census: { counts: c.counts, lifecycle: c.lifecycle, safe: c.safe, code: c.code, canonical_mutated: c.mutated_canonical_ledger,
      content_free: c.content_free, snapshot: pick(c.snapshot, ['query_only', 'immutable', 'integrity_check', 'foreign_key_check_rows', 'logical_sha256']) },
    pending_acceptance: pending(), vm_zero: zeroVm(), policies: policies(), runtime_mutated: false, server_mutated: false,
    activation_performed: false, acceptance_performed: false, authority_extended: false };
  result.activation_preflight_ready = result.vm_zero.host_count === 0 && result.vm_zero.backend_count === 0;
  if (process.argv[2] === 'freeze') need(result.activation_preflight_ready, 'SANDBOX_OR_BACKEND_PRESENT');
  const out = path.join(__dirname, (process.argv[2] === 'freeze' ? 'freeze-' : 'observation-') + new Date().toISOString().replace(/[^0-9TZ]/g, '') + '.json');
  fs.writeFileSync(out, JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
  return { ok: true, receipt: out, receipt_sha256: sha(out), owner_pid: owner.pid, agent_pid: agent.pid,
    pending_families: result.pending_acceptance.families, active_managed_jobs: c.counts.active_managed_processes,
    activation_preflight_ready: result.activation_preflight_ready, vm: result.vm_zero, activation_performed: false, server_mutated: false };
}
module.exports = { observe, expected, families };
if (require.main === module) {
  need(['observe', 'freeze'].includes(process.argv[2]), 'EXPLICIT_READ_ONLY_OBSERVE_REQUIRED');
  process.env.PSModulePath = env.PSModulePath;
  observe().then(result => process.stdout.write(JSON.stringify(result) + '\n')).catch(error => {
    process.stderr.write(String(error.code || 'R14_PREPARATION_FAILED').replace(/[^A-Za-z0-9_.:-]/g, '') + '\n'); process.exitCode = 2;
  });
}
