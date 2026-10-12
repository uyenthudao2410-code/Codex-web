'use strict';
// New read-only evidence helper. No activation, exec, policy, probe or stop API.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const { spawnSync, execFileSync } = require('node:child_process');
const repo = path.resolve(__dirname, '../../../../../..');
const candidate = path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-setup-exec-contract-1011-r10/win-unpacked');
const archive = path.join(candidate, 'resources/app.asar');
const executable = path.join(candidate, 'Coding Tools MCP.exe');
const dataRoot = 'C:\\Users\\daoth\\AppData\\Roaming\\web-mcp-assistant';
const parityFile = path.join(__dirname, '../candidate-parity-20261011T115907669Z.json');
const pins = {
  head: '2c554f59cb7b8ffc86ce5e0e28076c792777642f',
  archive: 'c39a614d40f551f0ddef4e579bcd8ef5d8d3ad365bbd43e22693df8c1f9672e9',
  executable: '6e34a6705a647aaddda0d24f2152904006a504ab7a29ba516b686c6de29ef09f',
  parity: 'c9f6fe1313b6004519a61bebf3f8f173a74cfd1d563bef48fce87908ed72f57c',
  modules: {
    runtimePaths: 'a28fe23a10daa10baeb9c437ccee13cff2c1d28585d1c6daa3e5a23844d23474',
    recoveryIpc: '57e0154c4d9f80bcfc5fa95ec5c4643de436d8fe945e9b3ab884afd9b8faebc2',
    recoveryHostLauncher: '92cb2478ae940c737a8e8a007181a9fa410b1eeb1e26a06b5bb07e1043ebf60a',
    processIdentity: 'a0ee2b08cbe4108c352ba14b9532ceaf581497f745a2adda7924c819a972809f'
  }
};
const shaBytes = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const sha = file => shaBytes(fs.readFileSync(file));
const pathKey = value => path.resolve(value).toLowerCase();
const fail = code => { throw Object.assign(new Error(), { code }); };
const requireThat = (condition, code) => { if (!condition) fail(code); };
const safeCode = value => /^[A-Z0-9_]{2,96}$/.test(String(value || '')) ? value : 'READ_OBSERVATION_FAILED';
const select = (value, fields) => Object.fromEntries(fields.map(key => [key, value?.[key] ?? null]));

function argument(argv, name, pattern) {
  const prefix = `--${name}=`, matches = argv.filter(value => value.startsWith(prefix));
  requireThat(matches.length === 1 && pattern.test(matches[0].slice(prefix.length)), 'EXACT_REVIEWED_ARGUMENT_REQUIRED');
  return matches[0].slice(prefix.length);
}
function readJson(file, maximum) {
  const value = fs.readFileSync(file);
  requireThat(value.length <= maximum, 'READ_EVIDENCE_SIZE_EXCEEDED');
  return JSON.parse(value.toString('utf8'));
}
function safeIdentity(raw, expected) {
  const age = Date.now() - Date.parse(raw?.observed_at);
  requireThat(raw?.observation_schema_version === 1 && raw.observation_kind === 'mcp_identity_read_only'
    && raw.recovery_host_instance_id === expected.host && raw.activation_epoch_id === expected.epoch
    && raw.current_activation_epoch_id === expected.epoch && raw.mcp_ready === true && raw.identity_current === true
    && Number.isFinite(age) && age >= 0 && age < 30000
    && /^[A-Za-z0-9_-]{8,128}$/.test(raw.mcp_process_instance_id || '')
    && /^[A-Za-z0-9_-]{8,128}$/.test(raw.mcp_server_instance_id || '')
    && /^[a-f0-9]{64}$/.test(raw.tool_contract_sha256 || ''), 'EXACT_CURRENT_R10_IDENTITY_UNPROVEN');
  return select(raw, ['observation_schema_version', 'observation_kind', 'observed_at', 'recovery_host_instance_id',
    'mcp_process_instance_id', 'mcp_server_instance_id', 'activation_epoch_id', 'current_activation_epoch_id',
    'tool_contract_sha256', 'mcp_ready', 'identity_current']);
}
function backendFiles(parity) {
  const root = path.join(candidate, 'resources/resources/tools/mxc-windows-sandbox');
  const names = ['wxc-exec.exe', 'wxc-windows-sandbox-daemon.exe', 'wxc-windows-sandbox-guest.exe', 'mxc-windows-sandbox.provenance.json'];
  const files = {};
  for (const name of names) {
    const file = path.join(root, name), key = path.relative(candidate, file).replaceAll('\\', '/');
    const expected = parity.packages?.candidate?.entries?.[key];
    requireThat(expected?.type === 'file' && sha(file) === expected.sha256, 'PINNED_STATE_AWARE_BACKEND_CHANGED');
    files[name] = expected.sha256;
  }
  return { kind: 'Microsoft MXC Windows Sandbox state-aware candidate', root, verified_files_sha256: files,
    probe_performed: false, active_manager_ownership_proven: false };
}
const hostScript = String.raw`
$ErrorActionPreference='Stop'
$wanted=@(Get-Process | Where-Object {
  $_.ProcessName -match '^WindowsSandbox' -or $_.ProcessName -eq 'vmmemWindowsSandbox' -or
  $_.ProcessName -eq 'wxc-windows-sandbox-daemon'
})
$items=@($wanted | ForEach-Object {
  $created=$null
  try { $created=[string]$_.StartTime.ToUniversalTime().ToFileTimeUtc() } catch {}
  @{ name=$_.ProcessName; pid=$_.Id; process_start_token=$created }
})
@{processes=$items; observed_at=[DateTime]::UtcNow.ToString('o'); temp_root=[System.IO.Path]::GetTempPath()} |
  ConvertTo-Json -Compress -Depth 4
`;
function hostObservation() {
  const shell = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe';
  const result = spawnSync(shell, ['-NoProfile', '-NonInteractive', '-Command', hostScript],
    { encoding: 'utf8', windowsHide: true, timeout: 15000, maxBuffer: 65536 });
  requireThat(result.status === 0 && !result.error, 'HOST_VM_READ_OBSERVATION_UNAVAILABLE');
  const raw = JSON.parse(result.stdout), age = Date.now() - Date.parse(raw.observed_at);
  requireThat(Array.isArray(raw.processes) && raw.processes.length <= 64 && Number.isFinite(age) && age >= 0 && age < 30000
    && pathKey(raw.temp_root) === pathKey(os.tmpdir()), 'HOST_VM_READ_OBSERVATION_INVALID');
  const processes = raw.processes.map(item => {
    requireThat(/^(WindowsSandbox[A-Za-z0-9_.-]*|vmmemWindowsSandbox|wxc-windows-sandbox-daemon)$/.test(item.name || '')
      && Number.isInteger(item.pid) && item.pid > 0 && (item.process_start_token === null || /^[0-9]{1,32}$/.test(item.process_start_token)),
      'HOST_VM_PROCESS_METADATA_INVALID');
    return select(item, ['name', 'pid', 'process_start_token']);
  });
  const daemonPath = path.join(raw.temp_root, 'wxc-wsb', 'state-aware', 'daemon.json');
  let record = null;
  try { record = fs.lstatSync(daemonPath); } catch (error) { if (error.code !== 'ENOENT') fail('DAEMON_RECORD_EXISTENCE_UNAVAILABLE'); }
  // Do not open/read/hash the record: it contains a private IPC nonce.
  const sandbox = processes.filter(item => /^WindowsSandbox/.test(item.name) || item.name === 'vmmemWindowsSandbox');
  const daemon = processes.filter(item => item.name === 'wxc-windows-sandbox-daemon');
  const recordPresent = record !== null;
  return { observed_at: raw.observed_at, temp_root: raw.temp_root, processes,
    sandbox_process_count: sandbox.length, daemon_process_count: daemon.length,
    daemon_record_exists: recordPresent, daemon_record_regular_file: recordPresent && record.isFile() && !record.isSymbolicLink(),
    daemon_record_read: false, daemon_record_hashed: false,
    cold_candidate_observed: sandbox.length === 0 && daemon.length === 0 && !recordPresent,
    warm_candidate_observed: sandbox.length > 0 && daemon.length === 1 && recordPresent && record.isFile() && !record.isSymbolicLink(),
    daemon_or_vm_ownership_proven: false, manager_lease_proven: false };
}
function writeObservation(row) {
  const name = `native-local-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(4).toString('hex')}.json`;
  const file = path.join(__dirname, name);
  fs.writeFileSync(file, `${JSON.stringify(row, null, 2)}\n`, { flag: 'wx' });
  return { evidence_file: file, evidence_sha256: sha(file) };
}
async function main(argv = process.argv.slice(2)) {
  const allowed = ['expected-epoch', 'expected-host-instance', 'expected-installation-id', 'phase'];
  requireThat(argv.length === allowed.length && argv.every(value => allowed.some(name => value.startsWith(`--${name}=`))), 'READ_ARGUMENTS_INVALID');
  const expected = {
    epoch: argument(argv, 'expected-epoch', /^activation-[A-Za-z0-9_-]{8,128}$/),
    host: argument(argv, 'expected-host-instance', /^[a-f0-9]{32}$/),
    installation: argument(argv, 'expected-installation-id', /^[a-f0-9]{64}$/),
    phase: argument(argv, 'phase', /^(cold|warm|observe)$/)
  };
  requireThat(expected.epoch !== 'activation-mv3qe36p-991f11f44f47d32ea2e217b1db882ff7', 'FRESH_R10_EPOCH_REQUIRED');
  requireThat(process.platform === 'win32' && process.env.ELECTRON_RUN_AS_NODE === '1' && pathKey(process.execPath) === pathKey(executable)
    && pathKey(process.env.APPDATA || '') === pathKey(path.dirname(dataRoot)), 'EXACT_PACKAGED_R10_OBSERVER_REQUIRED');
  requireThat(execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo, encoding: 'utf8', windowsHide: true }).trim() === pins.head
    && sha(archive) === pins.archive && sha(executable) === pins.executable && sha(parityFile) === pins.parity, 'IMMUTABLE_R10_PACKAGE_CHANGED');
  const parity = readJson(parityFile, 32 * 1024 * 1024);
  requireThat(parity.ok === true && parity.candidate_tag === 'setup-exec-contract-1011-r10' && pathKey(parity.packages?.candidate?.candidate || '') === pathKey(candidate),
    'IMMUTABLE_R10_PARITY_CHANGED');
  const modules = path.join(archive, 'electron/services');
  for (const [name, hash] of Object.entries(pins.modules)) requireThat(sha(path.join(modules, `${name}.js`)) === hash, 'PACKAGED_READ_MODULE_CHANGED');
  const { createRuntimePaths } = require(path.join(modules, 'runtimePaths'));
  const { RecoveryIpcClient, loadRecoveryDescriptor } = require(path.join(modules, 'recoveryIpc'));
  const { descriptorMatchesInstallation, descriptorRequestOptions } = require(path.join(modules, 'recoveryHostLauncher'));
  const { observeLifecycleProcessIdentity, sameProcessIdentity } = require(path.join(modules, 'processIdentity'));
  const paths = createRuntimePaths({ dataRoot, appRoot: archive, resourcesRoot: path.join(candidate, 'resources/resources'),
    runtimeMode: 'packaged', executablePath: executable });
  const descriptor = loadRecoveryDescriptor(paths);
  requireThat(descriptorMatchesInstallation(descriptor, paths.runtimeIdentity()) && descriptor.installation_id === expected.installation
    && descriptor.instance_id === expected.host, 'EXACT_LIVE_R10_DESCRIPTOR_REQUIRED');
  const ownerPin = select(descriptor, ['owner_pid', 'owner_process_start_token']);
  const owner = await observeLifecycleProcessIdentity(descriptor.owner_pid);
  requireThat(owner.state === 'live' && sameProcessIdentity({ pid: ownerPin.owner_pid, process_start_token: ownerPin.owner_process_start_token }, owner),
    'EXACT_R10_OWNER_PROCESS_REQUIRED');
  const client = new RecoveryIpcClient({ paths }), options = descriptorRequestOptions(descriptor);
  const identity = safeIdentity(await client.identityObservation({ ...options, timeout: 15000 }), expected);
  const backend = backendFiles(parity), host = hostObservation();
  const after = loadRecoveryDescriptor(paths), ownerAfter = await observeLifecycleProcessIdentity(descriptor.owner_pid);
  requireThat(after.instance_id === descriptor.instance_id && after.installation_id === descriptor.installation_id
    && after.owner_pid === descriptor.owner_pid && after.owner_process_start_token === descriptor.owner_process_start_token
    && ownerAfter.state === 'live' && sameProcessIdentity(owner, ownerAfter), 'R10_OWNER_CHANGED_DURING_OBSERVATION');
  const row = { kind: 'r10_native_local_read_only', observed_at: new Date().toISOString(), ok: true, phase: expected.phase,
    repository: { root: repo, head: pins.head, worktree: 'dirty_preserved' }, candidate, profile: 'web-mcp-assistant',
    package: { app_asar_sha256: pins.archive, executable_sha256: pins.executable, parity_sha256: pins.parity },
    descriptor: { installation_id: descriptor.installation_id, instance_id: descriptor.instance_id, runtime_mode: descriptor.runtime_mode },
    owner: select(owner, ['state', 'pid', 'process_start_token']), identity, backend, host,
    requested_phase_observed: expected.phase === 'observe' || (expected.phase === 'cold' ? host.cold_candidate_observed : host.warm_candidate_observed),
    pin_fields: { process_instance_id: identity.mcp_process_instance_id, server_instance_id: identity.mcp_server_instance_id,
      activation_epoch_id: identity.activation_epoch_id, native_contract_sha256: identity.tool_contract_sha256 },
    helper_sha256: sha(__filename), canary_accepted: false, cleanup_confirmed: false,
    mutations: { runtime: false, authority: false, command: false, probe: false, service: false, ledger: false } };
  const receipt = writeObservation(row);
  process.stdout.write(`${JSON.stringify({ ok: true, ...receipt, observed_at: row.observed_at, phase: expected.phase,
    identity, pin_fields: row.pin_fields, requested_phase_observed: row.requested_phase_observed,
    host: select(host, ['observed_at', 'sandbox_process_count', 'daemon_process_count', 'daemon_record_exists',
      'daemon_record_read', 'cold_candidate_observed', 'warm_candidate_observed']), mutations: row.mutations })}\n`);
}
if (require.main === module) main().catch(error => {
  const row = { kind: 'r10_native_local_read_only_failed', observed_at: new Date().toISOString(), ok: false,
    code: safeCode(error.code), live_command_invoked: false, mutations_requested: false };
  const receipt = writeObservation(row);
  process.stdout.write(`${JSON.stringify({ ...row, ...receipt })}\n`);
  process.exitCode = 1;
});
module.exports = { argument, safeIdentity, safeCode, select };
