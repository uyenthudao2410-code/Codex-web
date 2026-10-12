'use strict';
// Root-run read-only r14 preflight. Never constructs an executor or runs the checker.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const packet = require('../activation-windows-same-window/transition-r14.cjs');
const repo = packet.target.root, services = path.join(repo, 'electron/services'), paths = packet.pathsFor('r14');
const { RecoveryIpcClient, loadRecoveryDescriptor } = require(path.join(services, 'recoveryIpc'));
const { descriptorRequestOptions, descriptorMatchesInstallation } = require(path.join(services, 'recoveryHostLauncher'));
const { observeLifecycleProcessIdentity: identity, sameProcessIdentity: same } = require(path.join(services, 'processIdentity'));
const { canonicalLedgerCensus } = require(path.join(services, 'fullCleanActivation'));
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const read = file => JSON.parse(fs.readFileSync(file));
const need = (ok, code) => { if (!ok) throw Object.assign(new Error(), { code }); };
async function main() {
  const prepared = read(path.join(__dirname, 'static-preparation.json')), packaged = packet.verifyCandidate();
  const descriptor = loadRecoveryDescriptor(paths);
  need(descriptorMatchesInstallation(descriptor, paths.runtimeIdentity()), 'EXACT_R14_INSTALLATION_REQUIRED');
  const owner = await identity(descriptor.owner_pid);
  need(owner.state === 'live' && same(owner, { pid: descriptor.owner_pid, process_start_token: descriptor.owner_process_start_token }), 'EXACT_R14_OWNER_CHANGED');
  const client = new RecoveryIpcClient({ paths }), options = descriptorRequestOptions(descriptor);
  const native = await client.call('runtime.identity_observation', [], options), status = await client.status({ ...options, fresh: true });
  const snapshot = await client.call('runtime.lightweight_snapshot', [], options);
  need(native.identity_current === true && native.mcp_ready === true && native.activation_epoch_id === native.current_activation_epoch_id
    && native.tool_contract_sha256 === '0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4'
    && status.activation_epoch?.activation_epoch_id === native.activation_epoch_id && status.activation_epoch?.state === 'READY'
    && status.activation_epoch?.admission_open === true && snapshot.fullyReady === true && snapshot.centralConnected === true
    && snapshot.authorityReady === true && snapshot.updateIncomplete === false, 'EXACT_CURRENT_R14_READY_REQUIRED');
  const targetHash = sha(fs.readFileSync(path.join(repo, prepared.target))), checkerHash = sha(fs.readFileSync(path.join(repo, prepared.checker)));
  need(targetHash === prepared.existing_preimage_sha256 && checkerHash === prepared.checker_sha256, 'CANARY_FIXTURE_DRIFT_NO_RESET');
  const code = `import hashlib,json,sqlite3,sys\nfrom pathlib import Path\nresult=[]\nwith sqlite3.connect(Path(sys.argv[1]).resolve(strict=True).as_uri()+"?mode=ro",uri=True,timeout=10) as d:\n d.row_factory=sqlite3.Row;d.execute("PRAGMA query_only=ON");d.execute("BEGIN")\n for f in json.loads(sys.argv[2]):\n  row=dict(f)\n  for t,c,field in (("runs","run_id","run_record_sha256"),("waves","wave_id","wave_record_sha256")):\n   found=d.execute(f"SELECT * FROM {t} WHERE {c}=?",(f[c],)).fetchall()\n   if len(found)!=1:raise SystemExit(2)\n   row[field]=hashlib.sha256(json.dumps(dict(found[0]),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()\n  result.append(row)\n d.rollback()\nprint(json.dumps(result))`;
  const p = spawnSync(paths.portablePython(), ['-B', '-I', '-c', code, path.join(repo, '.coding-tools/orchestration/ledger.sqlite3'), JSON.stringify(packet.oldPending)],
    { windowsHide: true, shell: false, timeout: 15000, encoding: 'utf8', maxBuffer: 8192 });
  need(!p.error && p.status === 0 && packet.canonical(JSON.parse(p.stdout)) === packet.canonical(packet.oldPending), 'BOTH_PENDING_FAMILIES_CHANGED');
  const census = await canonicalLedgerCensus({ paths, workspace: repo, allowAcceptancePending: true,
    pythonStatusFn: async () => ({ installed: true, command: paths.portablePython(), prefixArgs: ['-B'] }) });
  packet.assertCensus(census);
  const ps = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe';
  const v = spawnSync(ps, ['-NoProfile', '-NonInteractive', '-Command', "$n=@('WindowsSandbox','WindowsSandboxClient','WindowsSandboxServer','WindowsSandboxRemoteSession','vmmemWindowsSandbox'); @{host_count=@(Get-Process | Where-Object {$n -contains $_.ProcessName}).Count;backend_count=@(Get-CimInstance Win32_Process -Filter \"Name='wxc-windows-sandbox-daemon.exe' OR Name='wxc-exec.exe' OR Name='wxc-windows-sandbox-guest.exe'\").Count} | ConvertTo-Json -Compress"],
    { windowsHide: true, shell: false, timeout: 15000, encoding: 'utf8', maxBuffer: 1024,
      env: { ...process.env, PSModulePath: path.join(path.dirname(ps), 'Modules') } });
  need(!v.error && v.status === 0, 'SANDBOX_OBSERVATION_FAILED'); const vm = JSON.parse(v.stdout.replace(/^\uFEFF/, ''));
  need(vm.host_count === 0 && vm.backend_count === 0, 'COLD_SANDBOX_PREFLIGHT_REQUIRED');
  const observed = Date.now(), first = packet.oldPending[0], second = packet.oldPending[1];
  const result = { ok: true, kind: 'r14_same_window_query_only_native_preflight', observed_at_ms: observed, package: packaged,
    native_preflight: { observed_at_ms: observed, source_head: '2c554f59cb7b8ffc86ce5e0e28076c792777642f',
      preimage_sha256: targetHash, checker_sha256: checkerHash, old_run_sha256: first.run_record_sha256, old_wave_sha256: first.wave_record_sha256,
      second_old_run_sha256: second.run_record_sha256, second_old_wave_sha256: second.wave_record_sha256, cold_sandbox: true, no_active_jobs: true },
    activation_epoch: native.activation_epoch_id, runtime_instance_id: native.mcp_process_instance_id,
    mcp_server_instance_id: native.mcp_server_instance_id, native_tool_contract_sha256: native.tool_contract_sha256,
    contract_version: 'sha256:' + native.tool_contract_sha256, census: { counts: census.counts, lifecycle: census.lifecycle }, vm_zero: vm,
    authenticated_identity_observation: true, fixture_mutated: false, checker_executed: false, external_mutation: false, attestation_claimed: false };
  const after = await client.call('runtime.identity_observation', [], options);
  need(after.identity_current === true && ['mcp_process_instance_id', 'mcp_server_instance_id', 'activation_epoch_id', 'tool_contract_sha256'].every(k => after[k] === native[k])
    && sha(fs.readFileSync(path.join(repo, prepared.target))) === targetHash, 'NATIVE_OR_FIXTURE_CHANGED_DURING_PREFLIGHT');
  const file = path.join(__dirname, 'native-preflight-' + observed + '.json');
  fs.writeFileSync(file, JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
  process.stdout.write(JSON.stringify({ ...result, receipt_path: file, receipt_sha256: sha(fs.readFileSync(file)) }) + '\n');
}
if (require.main === module) {
  process.env.PSModulePath = packet.psEnvironment().PSModulePath;
  main().catch(error => { process.stdout.write(JSON.stringify({ ok: false, code: String(error.code || 'R14_NATIVE_PREFLIGHT_FAILED').replace(/[^A-Z0-9_]/g, ''), external_mutation: false }) + '\n'); process.exitCode = 2; });
}
