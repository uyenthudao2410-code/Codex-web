'use strict';
// Read-only production observation; no runtime dispatch or authority mutation.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const repo = path.resolve(__dirname, '../../../../..');
const services = path.join(repo, 'electron/services');
const { pathsFor } = require('../candidate-r11/activation-windows/transition-r11.cjs');
const { RecoveryIpcClient, loadRecoveryDescriptor } = require(path.join(services, 'recoveryIpc'));
const { descriptorMatchesInstallation, descriptorRequestOptions } = require(path.join(services, 'recoveryHostLauncher'));
const { observeLifecycleProcessIdentity, sameProcessIdentity } = require(path.join(services, 'processIdentity'));
const { canonicalLedgerCensus } = require(path.join(services, 'fullCleanActivation'));
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
async function run() {
  const paths = pathsFor('r11'), descriptor = loadRecoveryDescriptor(paths);
  const host = await observeLifecycleProcessIdentity(descriptor.owner_pid);
  if (!descriptorMatchesInstallation(descriptor, paths.runtimeIdentity()) || host.state !== 'live'
    || !sameProcessIdentity(host, {pid: descriptor.owner_pid, process_start_token: descriptor.owner_process_start_token})) {
    throw Object.assign(new Error(), {code: 'EXACT_R11_HOST_UNPROVEN'});
  }
  const options = descriptorRequestOptions(descriptor), client = new RecoveryIpcClient({paths});
  const status = await client.status({...options, fresh: true});
  const light = await client.call('runtime.lightweight_snapshot', [], options);
  const native = await client.call('runtime.identity_observation', [], options);
  const census = await canonicalLedgerCensus({paths, workspace: repo, allowAcceptancePending: true,
    pythonStatusFn: async () => ({installed: true, command: paths.portablePython(), prefixArgs: ['-B']})});
  const pendingCode = 'import hashlib,json,sqlite3,sys\nfrom pathlib import Path\ns=sqlite3.connect(Path(sys.argv[1]).resolve(strict=True).as_uri()+"?mode=ro",uri=True);s.execute("PRAGMA query_only=ON");d=sqlite3.connect(":memory:");s.backup(d);s.close();d.row_factory=sqlite3.Row\nr={}\nfor table,column,value in (("runs","run_id",sys.argv[2]),("waves","wave_id",sys.argv[3])):\n rows=d.execute(f"SELECT * FROM {table} WHERE {column}=?",(value,)).fetchall()\n if len(rows)!=1:raise SystemExit(2)\n r[table]=hashlib.sha256(json.dumps(dict(rows[0]),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()\nprint(json.dumps(r));d.close()';
  const hashes = spawnSync(paths.portablePython(), ['-B', '-I', '-c', pendingCode,
    path.join(repo, '.coding-tools/orchestration/ledger.sqlite3'), '95e909f0040a448faa9f1f3257e2ee2c',
    'c101beadfc6d4f2fbc13845052c84693'], {windowsHide: true, encoding: 'utf8', timeout: 10000});
  if (hashes.error || hashes.status !== 0) throw Object.assign(new Error(), {code: 'PENDING_READ_UNAVAILABLE'});
  const pending = JSON.parse(hashes.stdout);
  pending.unchanged = pending.runs === 'a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590'
    && pending.waves === '59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce';
  const agentFile = path.join(path.dirname(paths.recoveryHostDescriptorFile()), 'control-plane-connected-agent-status.json');
  const agent = fs.existsSync(agentFile) ? read(agentFile) : {};
  const agentIdentity = agent.agent_pid ? await observeLifecycleProcessIdentity(agent.agent_pid) : {state: 'absent'};
  const row = {kind: 'read_only_r11_before_r12', observed_at_ms: Date.now(), ok: pending.unchanged,
    host: {pid: host.pid, process_start_token: host.process_start_token, instance_id: descriptor.instance_id},
    epoch: Object.fromEntries(['activation_epoch_id', 'state', 'admission_open', 'update_incomplete'].map(k => [k, status.activation_epoch?.[k] ?? null])),
    readiness: Object.fromEntries(['fullyReady', 'localReady', 'centralConnected', 'authorityReady', 'updateIncomplete'].map(k => [k, light[k] ?? null])),
    native, agent: {identity: agentIdentity, last_heartbeat_state: agent.last_heartbeat_state ?? null,
      last_heartbeat_at_ms: agent.last_heartbeat_at_ms ?? null},
    census: {counts: census.counts, safe: census.safe, code: census.code, content_free: census.content_free,
      canonical_mutated: census.mutated_canonical_ledger, lifecycle: census.lifecycle,
      integrity_check: census.snapshot.integrity_check}, pending,
    fixture_sha256: sha(fs.readFileSync(path.join(repo, 'tests/fixtures/initial-proof-canary-target.cjs'))),
    runtime_mutated: false, authority_mutated: false};
  const name = `current-observation-${row.observed_at_ms}.json`;
  fs.writeFileSync(path.join(__dirname, name), JSON.stringify(row, null, 2) + '\n', {flag: 'wx'});
  process.stdout.write(JSON.stringify({ok: row.ok, receipt: name, ...row}) + '\n');
  if (!row.ok) process.exitCode = 1;
}
run().catch(error => {
  process.stdout.write(JSON.stringify({ok: false, code: error.code || 'CURRENT_OBSERVATION_UNAVAILABLE',
    runtime_mutated: false, authority_mutated: false}) + '\n'); process.exitCode = 2;
});
