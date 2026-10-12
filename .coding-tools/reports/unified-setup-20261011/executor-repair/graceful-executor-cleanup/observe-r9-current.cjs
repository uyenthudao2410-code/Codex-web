'use strict';
// Read-only final observation. No runtime switch, command replay, authority change,
// service operation, exclusive ledger gate, or Sandbox probe is exposed here.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync, execFileSync } = require('node:child_process');
const repo = path.resolve(__dirname, '../../../../..');
const services = path.join(repo, 'electron/services');
const candidate = path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-executor-lifecycle-1011-r9/win-unpacked');
const dataRoot = 'C:\\Users\\daoth\\AppData\\Roaming\\web-mcp-assistant';
const pins = {
  head: '2c554f59cb7b8ffc86ce5e0e28076c792777642f',
  archive: '3bc75601041ef35b9fd894878b9f1905117512e3fc6f74d6102575b0f1edb226',
  executable: 'fadc2feb4bb566b3fa22f22ea918c7175f39fa6b74eb7ccb9d2a1d6bab1b6211',
  installation: 'e65d60602938af2f1c6e8cd9e8c59352ff2a5e24a268a45a98114726cdd8210d',
  instance: '6006092b7a061f47b20a0b27c1f34f1d',
  epoch: 'activation-mv3qe36p-991f11f44f47d32ea2e217b1db882ff7',
  host: { pid: 1128, process_start_token: '134361911908524600' },
  ui: { pid: 25296, process_start_token: '134361911886531150' },
  uiInstance: '2d80b88288e54bcc40f86f6ad45adcf6',
  native: { pid: 9212, process_start_token: '134361911931895600' },
  agent: { pid: 7108, process_start_token: '134361912150770020' },
  run: '95e909f0040a448faa9f1f3257e2ee2c',
  wave: 'c101beadfc6d4f2fbc13845052c84693',
  serverHelper: 'c86ff98e315651225a9f125132ce4ac4c84fe64a537d3021971d5333c9abf869',
  serviceInstance: 'cp_d203277517b747e4b056ec0184d09709',
  revision: '5ce5c51fc97584501d5d091e8c21df88250f55eb42e6e756384b234da8837b1f',
  authorityExpiry: 1791721156518,
  context: 'ctx_655e717e5c634cc1922d0f0d2e9d33c6',
  pilot: 'pilot_6c6dd3a9b03e4221af64068ff5ea0afd',
  historicalFamilyDigest: '825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed',
  services: {
    runtimePaths: 'a28fe23a10daa10baeb9c437ccee13cff2c1d28585d1c6daa3e5a23844d23474',
    recoveryIpc: '57e0154c4d9f80bcfc5fa95ec5c4643de436d8fe945e9b3ab884afd9b8faebc2',
    recoveryHostLauncher: '92cb2478ae940c737a8e8a007181a9fa410b1eeb1e26a06b5bb07e1043ebf60a',
    processIdentity: 'a0ee2b08cbe4108c352ba14b9532ceaf581497f745a2adda7924c819a972809f',
    fullCleanActivation: '881ffbdc57d4332ec1d6316199d2876d58821447b30cc861eade4c2c3d31baf1'
  }
};
const shaBytes = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const sha = file => shaBytes(fs.readFileSync(file));
const fail = code => { throw Object.assign(new Error(), { code }); };
const requireThat = (condition, code) => { if (!condition) fail(code); };
const safeText = value => String(value || '').replace(/[^a-zA-Z0-9_.:-]/g, '').slice(0, 128);
const select = (row, fields) => Object.fromEntries(fields.map(field => [field, row?.[field] ?? null]));
const readJson = file => {
  const bytes = fs.readFileSync(file);
  requireThat(bytes.length <= 1024 * 1024, 'OBSERVATION_INPUT_TOO_LARGE');
  return JSON.parse(bytes.toString('utf8'));
};
const pendingReadCode = String.raw`
import hashlib,json,sqlite3,sys
from pathlib import Path
database=Path(sys.argv[1]).resolve(strict=True)
run_id=sys.argv[2]; wave_id=sys.argv[3]
source=sqlite3.connect(database.as_uri()+"?mode=ro",uri=True,timeout=5)
source.execute("PRAGMA query_only=ON")
snapshot=sqlite3.connect(":memory:")
source.backup(snapshot); source.close()
snapshot.row_factory=sqlite3.Row
snapshot.execute("PRAGMA query_only=ON")
result={}
for table,key,value in (("runs","run_id",run_id),("waves","wave_id",wave_id)):
 rows=snapshot.execute(f"SELECT * FROM {table} WHERE {key}=?",(value,)).fetchall()
 if len(rows)!=1: raise SystemExit(2)
 row=dict(rows[0]); encoded=json.dumps(row,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
 result[table]={field:row.get(field) for field in ("run_id","wave_id","status","finished_at") if field in row}
 result[table]["record_sha256"]=hashlib.sha256(encoded).hexdigest()
snapshot.close()
print(json.dumps(result,separators=(",",":")))
`;
async function main() {
  requireThat(process.argv.slice(2).length === 0 || (process.argv.length === 3 && process.argv[2] === '--after-canary'), 'READ_MODE_INVALID');
  const addedCanary = process.argv[2] === '--after-canary' ? 1 : 0;
  requireThat(path.resolve(process.env.APPDATA || '').toLowerCase() === path.dirname(dataRoot).toLowerCase(), 'PROFILE_MISMATCH');
  requireThat(execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo, encoding: 'utf8', windowsHide: true }).trim() === pins.head, 'REPOSITORY_HEAD_CHANGED');
  for (const [name, expected] of Object.entries(pins.services)) requireThat(sha(path.join(services, `${name}.js`)) === expected, 'READ_HELPER_SERVICE_CHANGED');
  requireThat(sha(path.join(candidate, 'resources/app.asar')) === pins.archive && sha(path.join(candidate, 'Coding Tools MCP.exe')) === pins.executable, 'ACTIVE_R9_PACKAGE_CHANGED');
  const serverHelper = path.join(__dirname, '..', 'rollout-r9', 'ubuntu-r9-authority.py');
  requireThat(sha(serverHelper) === pins.serverHelper, 'SERVER_READ_HELPER_CHANGED');
  const { createRuntimePaths } = require(path.join(services, 'runtimePaths'));
  const { RecoveryIpcClient, loadRecoveryDescriptor } = require(path.join(services, 'recoveryIpc'));
  const { descriptorMatchesInstallation, descriptorRequestOptions } = require(path.join(services, 'recoveryHostLauncher'));
  const { observeLifecycleProcessIdentity, sameProcessIdentity } = require(path.join(services, 'processIdentity'));
  const { canonicalLedgerCensus } = require(path.join(services, 'fullCleanActivation'));
  const paths = createRuntimePaths({ dataRoot, appRoot: path.join(candidate, 'resources/app.asar'), resourcesRoot: path.join(candidate, 'resources/resources'), runtimeMode: 'packaged', executablePath: path.join(candidate, 'Coding Tools MCP.exe') });
  const descriptor = loadRecoveryDescriptor(paths);
  requireThat(descriptorMatchesInstallation(descriptor, paths.runtimeIdentity()) && descriptor.installation_id === pins.installation && descriptor.instance_id === pins.instance
    && descriptor.owner_pid === pins.host.pid && descriptor.owner_process_start_token === pins.host.process_start_token, 'ACTIVE_R9_DESCRIPTOR_CHANGED');
  const owner = await observeLifecycleProcessIdentity(descriptor.owner_pid);
  requireThat(owner.state === 'live' && sameProcessIdentity(pins.host, owner), 'ACTIVE_R9_HOST_CHANGED');
  const pendingRead = () => {
    const result = spawnSync(paths.portablePython(), ['-B', '-I', '-c', pendingReadCode, path.join(repo, '.coding-tools/orchestration/ledger.sqlite3'), pins.run, pins.wave], { encoding: 'utf8', windowsHide: true, timeout: 15000, maxBuffer: 65536 });
    requireThat(result.status === 0 && !result.error, 'PENDING_ACCEPTANCE_READ_FAILED');
    const value = JSON.parse(result.stdout);
    requireThat(value.runs?.run_id === pins.run && value.waves?.run_id === pins.run && value.waves?.wave_id === pins.wave, 'PENDING_ACCEPTANCE_IDENTITY_CHANGED');
    return value;
  };
  const pendingBefore = pendingRead();
  const client = new RecoveryIpcClient({ paths });
  const options = descriptorRequestOptions(descriptor);
  const status = await client.status({ ...options, fresh: true });
  const snapshot = await client.call('runtime.lightweight_snapshot', [], options);
  const state = readJson(paths.stateFile());
  const identities = { host: owner };
  identities.ui = await observeLifecycleProcessIdentity(status.electron_ui_recovery?.pid || 0);
  identities.native = await observeLifecycleProcessIdentity(Number(state.nativePid || 0));
  identities.agent = await observeLifecycleProcessIdentity(pins.agent.pid);
  const blockers = [];
  for (const name of ['ui', 'native', 'agent']) if (identities[name].state !== 'live' || !sameProcessIdentity(pins[name], identities[name])) blockers.push(`${name}_identity_changed`);
  const ui = status.electron_ui_recovery;
  if (ui?.instance_id !== pins.uiInstance || ui?.ui_installation_id !== pins.installation || ui?.alive !== true || ui?.registered !== true) blockers.push('ui_registration_changed');
  const epoch = select(status.activation_epoch, ['activation_epoch_id', 'state', 'admission_open', 'update_incomplete']);
  if (epoch.activation_epoch_id !== pins.epoch || state.nativeActivationEpochId !== pins.epoch) blockers.push('epoch_identity_changed');
  if (epoch.state !== 'READY' || epoch.admission_open !== true || epoch.update_incomplete !== false) blockers.push('epoch_readiness_changed');
  const readiness = { fully_ready: snapshot.fullyReady, local_ready: snapshot.localReady, central_connected: snapshot.centralConnected, authority_ready: snapshot.authorityReady, update_incomplete: snapshot.updateIncomplete, failure_kind: safeText(snapshot.failureKind) };
  if (Object.values(select(readiness, ['fully_ready', 'local_ready', 'central_connected', 'authority_ready'])).some(value => value !== true) || readiness.update_incomplete === true) blockers.push('live_readiness_incomplete');
  const census = await canonicalLedgerCensus({ paths, workspace: repo, allowAcceptancePending: true, holdExclusive: false,
    pythonStatusFn: async () => ({ installed: true, command: paths.portablePython(), prefixArgs: ['-B'] }) });
  requireThat(census.mutated_canonical_ledger === false && census.content_free === true && JSON.stringify(census.snapshot.integrity_check) === '["ok"]', 'CENSUS_READ_CONTRACT_INVALID');
  if (census.lifecycle.awaiting_acceptance_runs.slice().sort().join(',') !== pins.run) blockers.push('pending_acceptance_set_changed');
  for (const key of ['active_tool_calls', 'active_commands', 'starting_commands', 'active_background_operations', 'active_managed_processes', 'active_agent_lanes']) if (census.counts[key] !== 0) blockers.push(`nonzero_${key}`);
  if (census.lifecycle.live_owned_runs.length !== 0 || census.lifecycle.unexplained_active_runs !== 0 || census.lifecycle.unbound_live_resource_residues !== 0) blockers.push('live_ledger_resource_residue');
  if (!census.safe && !(census.code === 'RUNTIME_BUSY' && census.lifecycle.blockers.join(',') === 'live_runtime_state_process')) blockers.push('canonical_census_refused');
  const pendingAfter = pendingRead();
  if (JSON.stringify(pendingBefore) !== JSON.stringify(pendingAfter)) blockers.push('pending_acceptance_records_changed_during_observation');
  const agentStatusFile = path.join(dataRoot, 'control-plane-connected-agent-status.json');
  const agentStatus = readJson(agentStatusFile);
  const agent = select(agentStatus, ['agent_pid', 'last_iteration_state', 'last_heartbeat_state', 'last_heartbeat_at_ms']);
  if (agent.agent_pid !== pins.agent.pid || agent.last_heartbeat_state !== 'succeeded' || !Number.isFinite(agent.last_heartbeat_at_ms) || Date.now() - agent.last_heartbeat_at_ms >= 60000) blockers.push('connected_agent_heartbeat_not_fresh');
  const remote = spawnSync('ssh', ['-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10', 'svhome@100.116.112.22', 'python3 -B - observe'], { input: fs.readFileSync(serverHelper), encoding: 'utf8', windowsHide: true, timeout: 45000, maxBuffer: 1024 * 1024 });
  requireThat(remote.status === 0 && !remote.error, 'SERVER_READ_OBSERVATION_FAILED');
  const remoteRows = remote.stdout.trim().split(/\r?\n/).filter(Boolean).map(JSON.parse);
  requireThat(remoteRows.length === 1 && remoteRows[0].phase === 'r9_read_only_preflight' && remoteRows[0].ok === true && remoteRows[0].remote_mutation === false, 'SERVER_READ_CONTRACT_INVALID');
  const server = remoteRows[0];
  if (server.service_instance_id !== pins.serviceInstance || server.source_revision !== pins.revision) blockers.push('server_identity_changed');
  if (server.admission !== 'scoped_pilot') blockers.push('server_intake_changed');
  if (server.state.actions !== 37 + addedCanary || server.state.tasks !== 9 + addedCanary || server.state.acceptances !== 1 || server.state.unsettled_actions !== 13 || server.state.historical_action_families_sha256 !== pins.historicalFamilyDigest) blockers.push('server_expected_census_changed');
  for (const key of ['queued_actions', 'accepted_actions', 'open_writers', 'open_tasks', 'target_unsettled_actions', 'unsettled_acceptances']) if (server.state[key] !== 0) blockers.push(`server_nonzero_${key}`);
  const node = server.node;
  if (node.activation_epoch !== pins.epoch || node.readiness !== 'ready' || node.policy_state !== 'enabled' || server.observed_at_ms - node.last_seen_at_ms >= 60000) blockers.push('server_node_readiness_changed');
  const liveContexts = server.target_contexts.filter(row => row.closed_at_ms === null && row.expires_at_ms > server.observed_at_ms);
  const livePilots = server.target_pilots.filter(row => row.revoked_at_ms === null && row.expires_at_ms > server.observed_at_ms);
  if (liveContexts.length !== 1 || liveContexts[0].context_id !== pins.context || liveContexts[0].expires_at_ms !== pins.authorityExpiry
    || livePilots.length !== 1 || livePilots[0].decision_id !== pins.pilot || livePilots[0].expires_at_ms !== pins.authorityExpiry) blockers.push('standing_authority_changed');
  for (const contextId of ['ctx_9b930390ceb94596a49513ad94ebcb97', 'ctx_5b576164bfce43c1b8bc6016cbfc118a']) if (!server.target_contexts.some(row => row.context_id === contextId && Number.isInteger(row.closed_at_ms))) blockers.push('canary_context_cleanup_missing');
  const result = {
    kind: 'r9_final_read_only_census', observed_at: new Date().toISOString(), ok: blockers.length === 0, blockers,
    repository: { root: repo, branch: 'main', head: pins.head, worktree: 'dirty_preserved' }, candidate, profile: 'web-mcp-assistant',
    helper_sha256: sha(__filename), read_helper_service_sha256: pins.services, active_package: { app_asar_sha256: pins.archive, executable_sha256: pins.executable, installation_id: pins.installation, instance_id: pins.instance },
    identities, epoch, readiness, agent,
    ledger: { safe_for_stopped_activation: census.safe, code: census.code, counts: census.counts, lifecycle: census.lifecycle, reason: census.reason, ledger_mutated: census.mutated_canonical_ledger, content_free: census.content_free, census_fingerprint: census.census_fingerprint, snapshot: select(census.snapshot, ['logical_sha256', 'integrity_check', 'query_only', 'immutable']), hold_exclusive: false },
    pending_acceptance: { before: pendingBefore, after: pendingAfter, records_unchanged: JSON.stringify(pendingBefore) === JSON.stringify(pendingAfter) },
    server: { observed_at_ms: server.observed_at_ms, service_instance_id: server.service_instance_id, source_revision: server.source_revision, package_source_sha256: server.package_source_sha256, admission: server.admission, state: server.state, state_sha256: server.state_sha256, binding_id: server.binding_id, node,
      authority: { context: liveContexts[0] || null, pilot: livePilots[0] || null, expected_expires_at_ms: pins.authorityExpiry }, canary_contexts: server.target_contexts.filter(row => ['ctx_9b930390ceb94596a49513ad94ebcb97', 'ctx_5b576164bfce43c1b8bc6016cbfc118a'].includes(row.context_id)), server_read_helper_sha256: pins.serverHelper },
    mutations: { runtime: false, service: false, policy: false, task: false, acceptance: false, command_replay: false, sandbox_probe: false, windows_restart: false }
  };
  const output = path.join(__dirname, `census-${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
  fs.writeFileSync(output, `${JSON.stringify(result, null, 2)}\n`, { flag: 'wx' });
  process.stdout.write(`${JSON.stringify({ ok: result.ok, blockers, evidence_file: output, evidence_sha256: sha(output), observed_at: result.observed_at, identities, epoch, readiness, server_state: server.state, pending_acceptance_records_unchanged: result.pending_acceptance.records_unchanged, authority_expires_at_ms: pins.authorityExpiry, mutations: result.mutations })}\n`);
  if (!result.ok) process.exitCode = 2;
}
main().catch(error => {
  const row = { kind: 'r9_final_read_only_census_failed', observed_at: new Date().toISOString(), ok: false, code: safeText(error.code || 'READ_CENSUS_FAILED'), mutations_requested: false };
  const output = path.join(__dirname, `failure-${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
  fs.writeFileSync(output, `${JSON.stringify(row, null, 2)}\n`, { flag: 'wx' });
  process.stdout.write(`${JSON.stringify({ ...row, evidence_file: output })}\n`);
  process.exitCode = 2;
});
