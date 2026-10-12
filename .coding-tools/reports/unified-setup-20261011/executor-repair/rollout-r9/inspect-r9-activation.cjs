'use strict';
// Read-only, content-free diagnosis; no restart, probe, permission or intake mutation.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const repo = path.resolve(__dirname, '../../../../..');
const { createRuntimePaths } = require(path.join(repo, 'electron/services/runtimePaths'));
const { RecoveryIpcClient, loadRecoveryDescriptor } = require(path.join(repo, 'electron/services/recoveryIpc'));
const { descriptorMatchesInstallation, descriptorRequestOptions } = require(path.join(repo, 'electron/services/recoveryHostLauncher'));
const candidate = path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-executor-lifecycle-1011-r9/win-unpacked');
const paths = createRuntimePaths({ dataRoot: 'C:\\Users\\daoth\\AppData\\Roaming\\web-mcp-assistant', appRoot: path.join(candidate, 'resources/app.asar'), resourcesRoot: path.join(candidate, 'resources/resources'), runtimeMode: 'packaged', executablePath: path.join(candidate, 'Coding Tools MCP.exe') });
const expectedEpoch = 'activation-mv3qe36p-991f11f44f47d32ea2e217b1db882ff7';
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const fail = code => { throw Object.assign(new Error(), { code }); };
const stringKeys = new Set(['activation_epoch_id', 'operation_id', 'state', 'epoch_state', 'admission_state', 'phase', 'stage', 'code', 'error_code', 'kind', 'reason', 'reason_code', 'failure_kind', 'source', 'mode', 'integrity_check', 'projection_classification', 'classification', 'handoff_state', 'bootstrap_state', 'ready_commit_digest', 'expected_revision', 'actual_revision', 'running_revision', 'disk_revision']);
const boolKeys = new Set(['pass', 'ready', 'admission_open', 'update_incomplete', 'fullyReady', 'localReady', 'componentsReady', 'centralConnected', 'authorityReady', 'nativeAlive', 'mcpRunning', 'tunnelRunning', 'connectorReady', 'connectorRefreshRequired', 'registered', 'alive', 'started', 'completed', 'failed', 'pending', 'source_checkpoint_verified', 'content_free', 'mutated_canonical_ledger', 'exclusive_gate_held']);
const numberKeys = new Set(['pid', 'owner_pid', 'expires_at_unix_ms', 'observed_at_ms', 'checked_at_ms', 'last_heartbeat_at_ms', 'ready_at_unix_ms']);
const containerKeys = new Set(['error', 'details', 'activation_epoch', 'activation', 'bootstrap_activation', 'bootstrap', 'full_clean_activation', 'recovery_plane', 'last_error', 'result', 'final_proof', 'final_census', 'proof', 'census', 'counts', 'lifecycle', 'postflight', 'components', 'runtime', 'mcp', 'coding_mcp', 'electron_ui', 'recovery_host', 'reasons', 'blockers', 'failures', 'codeRevision', 'codingMcp', 'checks', 'metadata', 'timeline']);
function sanitized(value, depth = 0, context = '') {
  if (depth > 8 || !value || typeof value !== 'object') return {};
  if (Array.isArray(value)) return value.slice(0, 64).flatMap(item => {
    if (typeof item === 'string' && /^[A-Za-z][A-Za-z0-9_.:-]{0,127}$/.test(item)) return [item];
    if (item && typeof item === 'object') return [sanitized(item, depth + 1, context)];
    return [];
  });
  const out = { observed_keys: Object.keys(value).sort().slice(0, 128) };
  for (const [key, item] of Object.entries(value)) {
    if (stringKeys.has(key) && (item === null || (typeof item === 'string' && /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/.test(item)))) out[key] = item;
    else if (boolKeys.has(key) && typeof item === 'boolean') out[key] = item;
    else if ((numberKeys.has(key) || context === 'counts') && Number.isSafeInteger(item) && item >= 0) out[key] = item;
    else if (containerKeys.has(key) && item && typeof item === 'object') out[key] = sanitized(item, depth + 1, key);
  }
  return out;
}
(async () => {
  if (sha(path.join(candidate, 'resources/app.asar')) !== '3bc75601041ef35b9fd894878b9f1905117512e3fc6f74d6102575b0f1edb226') fail('R9_ARCHIVE_CHANGED');
  const descriptor = loadRecoveryDescriptor(paths);
  if (!descriptorMatchesInstallation(descriptor, paths.runtimeIdentity())) fail('R9_DESCRIPTOR_MISMATCH');
  const client = new RecoveryIpcClient({ paths });
  const options = descriptorRequestOptions(descriptor);
  const responses = await Promise.allSettled([
    client.status({ ...options, fresh: true }),
    client.call('runtime.activation_epoch_status', [], options)
  ]);
  const results = responses.map(response => response.status === 'fulfilled' ? response.value : { error: { code: /^[A-Z0-9_]{1,96}$/.test(response.reason?.code || '') ? response.reason.code : 'READ_ONLY_IPC_FAILED' } });
  const epochStore = JSON.parse(fs.readFileSync(paths.activationEpochFile(), 'utf8'));
  const rawEpoch = epochStore.current;
  if (rawEpoch.activation_epoch_id !== expectedEpoch) fail('EPOCH_CHANGED_DURING_DIAGNOSIS');
  let activation = null;
  if (typeof rawEpoch.operation_id === 'string' && /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(rawEpoch.operation_id)) {
    try { activation = await client.call('code.activation_status', [rawEpoch.operation_id], options); }
    catch (error) { activation = { error: { code: /^[A-Z0-9_]{1,96}$/.test(error.code || '') ? error.code : 'ACTIVATION_STATUS_UNAVAILABLE' } }; }
  }
  const report = { kind: 'read_only_r9_activation_diagnosis', observed_at: new Date().toISOString(), helper_sha256: sha(__filename),
    expected_epoch: expectedEpoch, recovery_status: sanitized(results[0]), epoch_status: sanitized(results[1]), durable_epoch: sanitized(rawEpoch),
    code_activation_status: sanitized(activation), runtime_mutated: false, sandbox_probe_performed: false, server_mutated: false };
  const reportFile = path.join(__dirname, `activation-diagnosis-${report.observed_at.replace(/[^0-9TZ]/g, '')}.json`);
  fs.writeFileSync(reportFile, `${JSON.stringify(report, null, 2)}\n`, { flag: 'wx' });
  process.stdout.write(`${JSON.stringify({ report: reportFile, report_sha256: sha(reportFile), ...report })}\n`);
})().catch(error => { process.stdout.write(`${JSON.stringify({ ok: false, code: /^[A-Z0-9_]{1,96}$/.test(error.code || '') ? error.code : 'READ_ONLY_DIAGNOSIS_FAILED' })}\n`); process.exitCode = 1; });
