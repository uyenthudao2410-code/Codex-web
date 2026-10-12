'use strict';
// Final query-only observation. No execution, refresh, policy, cleanup or acceptance action.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const HERE = __dirname;
const PACKET_FILE = path.resolve(HERE, '../activation-windows-same-window/transition-r14.cjs');
const PACKET_SHA = 'b875e90526322528ae4406492b7915ed9ce049a28943d9c5f661e26fd07e0d74';
const PINS_FILE = path.join(HERE, 'pins-live-1791764723953.json');
const PINS_SHA = '55afe6b1f0ed5466d9f67fb2ed6ed1b3fe0245433283d784e93b0c854070d7bd';
const sha = raw => crypto.createHash('sha256').update(raw).digest('hex');
const need = (ok, code) => { if (!ok) throw Object.assign(new Error(), { code }); };
const select = (value, keys) => Object.fromEntries(keys.map(key => [key, value?.[key] ?? null]));
const safeAtom = value => value === null || typeof value === 'boolean' || Number.isSafeInteger(value)
  ? value : typeof value === 'string' && /^[A-Za-z0-9_.:\/-]{0,256}$/.test(value) ? value : 'UNPROJECTED';
const revision = value => Object.fromEntries(['state', 'running_revision', 'disk_revision', 'update_pending', 'pending_revision']
  .map(key => [key, safeAtom(value?.[key] ?? null)]));

async function main() {
  need(process.argv.includes('--read-only'), 'EXPLICIT_READ_ONLY_OBSERVATION_REQUIRED');
  need(sha(fs.readFileSync(PACKET_FILE)) === PACKET_SHA && sha(fs.readFileSync(PINS_FILE)) === PINS_SHA, 'FROZEN_OBSERVATION_INPUT_CHANGED');
  const packet = require(PACKET_FILE), pins = JSON.parse(fs.readFileSync(PINS_FILE, 'utf8'));
  const repo = packet.target.root, services = path.join(repo, 'electron/services'), paths = packet.pathsFor('r14');
  const { RecoveryIpcClient, loadRecoveryDescriptor } = require(path.join(services, 'recoveryIpc'));
  const { descriptorRequestOptions, descriptorMatchesInstallation } = require(path.join(services, 'recoveryHostLauncher'));
  const { observeLifecycleProcessIdentity: identity, sameProcessIdentity: same } = require(path.join(services, 'processIdentity'));
  const { canonicalLedgerCensus } = require(path.join(services, 'fullCleanActivation'));
  const descriptor = loadRecoveryDescriptor(paths);
  need(descriptorMatchesInstallation(descriptor, paths.runtimeIdentity()), 'EXACT_R14_INSTALLATION_REQUIRED');
  const owner = await identity(descriptor.owner_pid);
  need(owner.state === 'live' && same(owner, { pid: descriptor.owner_pid, process_start_token: descriptor.owner_process_start_token }), 'EXACT_R14_OWNER_REQUIRED');
  const client = new RecoveryIpcClient({ paths }), options = descriptorRequestOptions(descriptor);
  const native = await client.call('runtime.identity_observation', [], options);
  const matchesPins = value => value?.identity_current === true && value.mcp_ready === true
    && value.activation_epoch_id === value.current_activation_epoch_id
    && value.activation_epoch_id === pins.activation_epoch && value.mcp_process_instance_id === pins.runtime_instance_id
    && value.mcp_server_instance_id === pins.mcp_server_instance_id && value.tool_contract_sha256 === pins.native_tool_contract_sha256
    && value.recovery_host_instance_id === descriptor.instance_id;
  need(matchesPins(native), 'EXACT_CURRENT_NATIVE_IDENTITY_REQUIRED');
  const status = await client.status({ ...options, fresh: true });
  const lightweight = await client.call('runtime.lightweight_snapshot', [], options);
  const census = await canonicalLedgerCensus({ paths, workspace: repo, allowAcceptancePending: true, holdExclusive: false,
    pythonStatusFn: async () => ({ installed: true, command: paths.portablePython(), prefixArgs: ['-B'] }) });
  need(census.content_free === true && census.mutated_canonical_ledger === false
    && census.snapshot?.query_only === true && census.snapshot?.immutable === true, 'QUERY_ONLY_CONTENT_FREE_CENSUS_REQUIRED');
  const ps = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe';
  const query = "$ErrorActionPreference='Stop'; $n=@('WindowsSandbox','WindowsSandboxClient','WindowsSandboxServer','WindowsSandboxRemoteSession','vmmemWindowsSandbox'); @{content_free=$true;host_count=@(Get-Process | Where-Object {$n -contains $_.ProcessName}).Count;backend_count=@(Get-CimInstance Win32_Process -Filter \"Name='wxc-windows-sandbox-daemon.exe' OR Name='wxc-exec.exe' OR Name='wxc-windows-sandbox-guest.exe'\").Count} | ConvertTo-Json -Compress";
  const probe = spawnSync(ps, ['-NoProfile', '-NonInteractive', '-Command', query],
    { shell: false, windowsHide: true, timeout: 15000, encoding: 'utf8', maxBuffer: 1024,
      env: { ...process.env, PSModulePath: path.join(path.dirname(ps), 'Modules') } });
  need(!probe.error && probe.status === 0, 'READ_ONLY_VM_OBSERVATION_FAILED');
  const vm = JSON.parse(probe.stdout.replace(/^\uFEFF/, ''));
  need(vm.content_free === true && Number.isSafeInteger(vm.host_count) && vm.host_count >= 0
    && Number.isSafeInteger(vm.backend_count) && vm.backend_count >= 0, 'READ_ONLY_VM_COUNTS_INVALID');
  const after = await client.call('runtime.identity_observation', [], options);
  const afterOwner = await identity(descriptor.owner_pid);
  need(matchesPins(after) && same(owner, afterOwner), 'RUNTIME_CHANGED_DURING_FINAL_OBSERVATION');
  const result = {
    schema_version: 1, phase: 'r14_final_query_only_runtime_and_canonical_census', ok: true, observed_at_ms: Date.now(),
    helper_sha256: sha(fs.readFileSync(__filename)), packet_sha256: PACKET_SHA, pins_sha256: PINS_SHA,
    target: { binding_id: packet.target.binding_id, device_id: packet.target.device_id,
      workspace_id: packet.target.workspace_id, workspace_generation: packet.target.workspace_generation,
      root: repo, profile: packet.target.profile },
    descriptor: select(descriptor, ['installation_id', 'instance_id', 'owner_pid', 'owner_process_start_token']),
    owner: select(owner, ['state', 'pid', 'process_start_token']),
    native_identity: select(native, ['observation_schema_version', 'observation_kind', 'observed_at', 'recovery_host_instance_id',
      'mcp_process_instance_id', 'mcp_server_instance_id', 'activation_epoch_id', 'current_activation_epoch_id',
      'tool_contract_sha256', 'mcp_ready', 'identity_current']),
    readiness: select(lightweight, ['fullyReady', 'localReady', 'componentsReady', 'centralConnected', 'authorityReady', 'updateIncomplete']),
    readiness_codes: { failureKind: safeAtom(lightweight.failureKind ?? null), centralStatusReason: safeAtom(lightweight.centralStatusReason ?? null) },
    epoch: select(status.activation_epoch, ['activation_epoch_id', 'state', 'admission_open', 'update_incomplete']),
    revisions: { code: revision(status.code_revision), ui: revision(status.electron_ui_revision), native: revision(lightweight.codeRevision?.codingMcp) },
    census: { safe: census.safe, code: census.code, reason: census.reason, counts: census.counts, lifecycle: census.lifecycle,
      observed_at_unix_seconds: census.observed_at_unix_seconds, content_free: census.content_free,
      mutated_canonical_ledger: census.mutated_canonical_ledger,
      snapshot: select(census.snapshot, ['query_only', 'immutable', 'integrity_check', 'foreign_key_check_rows', 'logical_sha256']) },
    vm_counts: vm, preactivation_assertions_applied: false, zero_vm_assertion_applied: false,
    secret_values_emitted: false, runtime_mutated: false, server_mutated: false, policy_mutated: false,
    executor_or_job_started: false, acceptance_performed: false, command_executed_or_replayed: false
  };
  const file = path.join(HERE, 'final-observation-' + result.observed_at_ms + '.json');
  fs.writeFileSync(file, JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
  process.stdout.write(JSON.stringify({ ...result, receipt_path: file, receipt_sha256: sha(fs.readFileSync(file)) }) + '\n');
}
if (require.main === module) main().catch(error => {
  process.stdout.write(JSON.stringify({ phase: 'r14_final_query_only_observation_failed', ok: false,
    code: /^[A-Z0-9_]{1,128}$/.test(error.code || '') ? error.code : 'SAFE_READ_ONLY_FINAL_OBSERVATION_FAILED',
    raw_error_disclosed: false, secret_values_emitted: false, runtime_mutated: false, server_mutated: false, acceptance_performed: false }) + '\n');
  process.exitCode = 2;
});
