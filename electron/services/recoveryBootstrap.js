'use strict';

/**
 * Recovery Host bootstrap bridge.
 *
 * A full-clean activation must never be sent to a Recovery Host that was
 * loaded from an older checkout.  This module provides the small, durable
 * handoff used to retire that host and start the current checkout first.  It
 * deliberately contains no durable business/task state: the envelope binds
 * only the authenticated old process identity, current installation identity,
 * expected source revision and activation request.  The activation epoch and
 * orchestration ledger remain the authoritative durable records.
 */

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');
const {
  RecoveryIpcClient,
  loadRecoveryDescriptor
} = require('./recoveryIpc');
const {
  descriptorRequestOptions,
  descriptorMatchesInstallation,
  spawnRecoveryHost
} = require('./recoveryHostLauncher');
const {
  normalizeProcessStartToken,
  observeLifecycleProcessIdentity,
  processIdentityFrom,
  sameProcessIdentity,
  terminateExactProcessTree,
  waitForExactProcessExit
} = require('./processIdentity');
const { writeJsonAtomic, ensureParent } = require('./jsonStore');
const {
  normalizeTrustedAttestation,
  revalidateTrustedRecoveryHostSource
} = require('./trustedRecoveryBootstrap');

const BOOTSTRAP_SCHEMA_VERSION = 1;
const BOOTSTRAP_KIND = 'recovery_host_bootstrap';
const BOOTSTRAP_RESULT_KIND = `${BOOTSTRAP_KIND}_result`;
const BOOTSTRAP_OPERATION_ID = /^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/;
const INSTALLATION_ID = /^[a-f0-9]{64}$/;
const REVISION = /^[a-f0-9]{64}$/;
const EPOCH_ID = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/;
const MAX_ENVELOPE_BYTES = 128 * 1024;
const MAX_RESULT_BYTES = 256 * 1024;
// A bootstrap envelope spans a real Electron cold start plus the subsequent
// full-clean MCP/Tunnel/UI replacement.  The former 120-second cap was
// shorter than the observed Windows startup path, so a valid replacement
// could expire after its children had already been stopped.  Keep the bound
// finite (and separately bounded from the connector discovery gate), while
// allowing enough time for the authenticated handoff to complete.
// The bootstrap envelope carries the same bounded transaction deadline as the
// full-clean epoch. It must cover the five-minute cold-start/operator poll plus
// a real external connector round trip after exact process replacement.
const DEFAULT_TTL_MS = 600_000;
const RESULT_STATE_ORDER = Object.freeze({ pending: 0, started: 1, completed: 2, failed: 2, expired: 2 });
const TERMINAL_RESULT_STATES = new Set(['completed', 'failed', 'expired']);
const RESULT_LOCK_TIMEOUT_MS = 2_000;

function bootstrapError(code, message, details = {}) {
  return Object.assign(new Error(message), { code, details });
}

function text(value) { return String(value ?? '').trim(); }

// Persist only bounded machine diagnostics, never process output or argv.
function bootstrapFailureDetails(value = {}) {
  const result = {};
  for (const key of ['cause_code', 'termination_cause_code']) {
    if (/^[A-Z][A-Z0-9_]{0,119}$/.test(String(value?.[key] || ''))) result[key] = value[key];
  }
  for (const key of ['pid', 'exit_code']) {
    if (Number.isSafeInteger(value?.[key])) result[key] = value[key];
  }
  return result;
}

function canonicalDigest(value) {
  return crypto.createHash('sha256').update(JSON.stringify(value), 'utf8').digest('hex');
}

function withoutIntegrity(value) {
  const { integrity_sha256: _ignored, ...payload } = value || {};
  return payload;
}

function boundedArtifactPath(paths, candidate) {
  const resolved = path.resolve(candidate);
  if (typeof paths?.dataRoot === 'function') {
    const root = path.resolve(paths.dataRoot());
    if (resolved !== root && !resolved.startsWith(`${root}${path.sep}`)) {
      throw bootstrapError('RECOVERY_BOOTSTRAP_PATH_INVALID', 'Recovery Host bootstrap artifact escaped the runtime data root.');
    }
  }
  return resolved;
}

function bootstrapFile(paths, operationId = '') {
  if (typeof paths?.recoveryHostBootstrapFile !== 'function') {
    throw bootstrapError('RECOVERY_BOOTSTRAP_PATH_UNAVAILABLE', 'Runtime paths do not expose a Recovery Host bootstrap file.');
  }
  const id = operationId ? validateOperationId(operationId) : '';
  return boundedArtifactPath(paths, paths.recoveryHostBootstrapFile(id));
}

function bootstrapResultFile(paths, operationId = '') {
  const id = operationId ? validateOperationId(operationId) : '';
  if (typeof paths?.recoveryHostBootstrapResultFile === 'function') {
    return boundedArtifactPath(paths, paths.recoveryHostBootstrapResultFile(id));
  }
  return `${bootstrapFile(paths, id)}.result`;
}

function bootstrapResultLockFile(paths, operationId) {
  return boundedArtifactPath(paths, `${bootstrapResultFile(paths, operationId)}.lock`);
}

function sleepSync(ms) {
  const buffer = new Int32Array(new SharedArrayBuffer(4));
  Atomics.wait(buffer, 0, 0, Math.max(1, Number(ms) || 1));
}

function acquireBootstrapResultLock(paths, operationId, { timeoutMs = RESULT_LOCK_TIMEOUT_MS } = {}) {
  const id = validateOperationId(operationId);
  const file = bootstrapResultLockFile(paths, id);
  const boundedTimeout = Math.max(20, Math.min(RESULT_LOCK_TIMEOUT_MS, Number(timeoutMs) || RESULT_LOCK_TIMEOUT_MS));
  const deadline = Date.now() + boundedTimeout;
  const token = crypto.randomBytes(16).toString('hex');
  ensureParent(file);
  while (Date.now() < deadline) {
    let handle;
    try {
      handle = fs.openSync(file, 'wx', 0o600);
      fs.writeFileSync(handle, JSON.stringify({ version: 1, operation_id: id, pid: process.pid, token, created_at_unix_ms: Date.now() }), 'utf8');
      fs.fsyncSync(handle);
      fs.closeSync(handle);
      return { file, token };
    } catch (error) {
      if (handle !== undefined) {
        try { fs.closeSync(handle); } catch {}
      }
      if (error?.code !== 'EEXIST') throw error;
      try {
        const stat = fs.lstatSync(file);
        if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 4096) {
          throw bootstrapError('RECOVERY_BOOTSTRAP_RESULT_LOCK_INVALID', 'Recovery Host bootstrap result lock is invalid.');
        }
      } catch (readError) {
        if (readError?.code && readError.code !== 'ENOENT') throw readError;
      }
      // Never reclaim by unlinking a path observed as stale: another process
      // could acquire a new lock between observation and unlink. A crashed lock
      // therefore fail-closes only this operation; a new operation uses a new
      // artifact and lock.
      sleepSync(20);
    }
  }
  throw bootstrapError('RECOVERY_BOOTSTRAP_RESULT_BUSY', 'Recovery Host bootstrap result is being updated by another process.');
}

function releaseBootstrapResultLock(lock) {
  if (!lock?.file || !lock?.token) return false;
  try {
    const current = JSON.parse(fs.readFileSync(lock.file, 'utf8'));
    if (current?.token !== lock.token || Number(current?.pid) !== process.pid) return false;
    fs.unlinkSync(lock.file);
    return true;
  } catch (error) {
    if (error?.code === 'ENOENT') return false;
    throw error;
  }
}

function validateOperationId(value) {
  const operationId = text(value);
  if (!BOOTSTRAP_OPERATION_ID.test(operationId)) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap operation_id is invalid.');
  }
  return operationId;
}

function validateCheckpoint(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap source checkpoint is invalid.');
  }
  const allowed = ['checkpoint_id', 'run_id', 'wave_id', 'proof_fingerprint', 'git_head'];
  const keys = Object.keys(value).sort();
  if (JSON.stringify(keys) !== JSON.stringify([...allowed].sort())) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap source checkpoint fields are not canonical.');
  }
  for (const key of ['checkpoint_id', 'run_id', 'wave_id']) {
    if (!/^[A-Za-z0-9][A-Za-z0-9_-]{7,127}$/.test(String(value[key] || ''))) {
      throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', `Recovery Host bootstrap source checkpoint ${key} is invalid.`);
    }
  }
  if (!REVISION.test(text(value.proof_fingerprint).toLowerCase())
    || !/^[a-f0-9]{40,64}$/.test(text(value.git_head).toLowerCase())) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap source checkpoint proof is invalid.');
  }
  return {
    checkpoint_id: String(value.checkpoint_id),
    run_id: String(value.run_id),
    wave_id: String(value.wave_id),
    proof_fingerprint: text(value.proof_fingerprint).toLowerCase(),
    git_head: text(value.git_head).toLowerCase()
  };
}

function validateOptionalRefreshCheckpoint(value, refresh) {
  if (refresh === true) {
    if (value !== null && value !== undefined) {
      throw bootstrapError(
        'RECOVERY_BOOTSTRAP_INVALID',
        'A process-refresh bootstrap cannot carry source checkpoint authority.'
      );
    }
    return null;
  }
  return validateCheckpoint(value);
}

function validateTrustedRecoveryBootstrap(value, sourceCheckpoint, refresh) {
  if (value === undefined || value === null) return null;
  if (refresh === true) {
    throw bootstrapError(
      'RECOVERY_BOOTSTRAP_INVALID',
      'A trusted Recovery Supervisor bootstrap cannot be a checkpoint-free refresh.'
    );
  }
  try {
    return normalizeTrustedAttestation(value, sourceCheckpoint);
  } catch (error) {
    throw bootstrapError(
      String(error?.code || 'RECOVERY_BOOTSTRAP_INVALID'),
      'Trusted Recovery Supervisor bootstrap attestation is invalid.',
      { cause_code: String(error?.code || '') || null }
    );
  }
}

function expectedIdentity(paths) {
  const identity = paths?.runtimeIdentity?.();
  if (!identity || !INSTALLATION_ID.test(text(identity.installation_id).toLowerCase())
    || !['development', 'packaged'].includes(text(identity.mode))) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_INSTALLATION_INVALID', 'Current Recovery Host installation identity is unavailable.');
  }
  return {
    version: Number(identity.version || 1),
    mode: text(identity.mode),
    installation_id: text(identity.installation_id).toLowerCase()
  };
}

function normalizeDescriptorIdentity(descriptor) {
  return {
    installation_id: text(descriptor?.installation_id).toLowerCase(),
    runtime_mode: text(descriptor?.runtime_mode)
  };
}

function bootstrapCapability(status = {}) {
  const capability = status?.full_clean_activation && typeof status.full_clean_activation === 'object'
    ? status.full_clean_activation : null;
  const codeRevision = status?.code_revision && typeof status.code_revision === 'object'
    ? status.code_revision : {};
  const runningRevision = text(capability?.running_revision || codeRevision.running_revision).toLowerCase() || null;
  const diskRevision = text(capability?.disk_revision || codeRevision.disk_revision).toLowerCase() || null;
  const available = capability?.available === true
    && Number(capability?.contract_version || 0) === 1
    && capability?.state === 'current'
    && REVISION.test(runningRevision || '')
    && REVISION.test(diskRevision || '')
    && runningRevision === diskRevision;
  return {
    available,
    contract_version: Number(capability?.contract_version || 0) || null,
    state: text(capability?.state) || 'unavailable',
    running_revision: runningRevision,
    disk_revision: diskRevision
  };
}

/**
 * Return a fail-closed decision about whether an authenticated host may accept
 * a full-clean request.  Missing capability is stale/unsupported, never
 * "healthy enough" by inference.
 */
function assessRecoveryHostFreshness({ paths, descriptor, status, expectedDiskRevision = '' } = {}) {
  const identity = expectedIdentity(paths);
  const descriptorIdentity = normalizeDescriptorIdentity(descriptor);
  const installationMatches = descriptorMatchesInstallation(descriptor, identity);
  const capability = bootstrapCapability(status);
  const expectedRevision = text(expectedDiskRevision).toLowerCase();
  const revisionMatches = Boolean(expectedRevision && capability.disk_revision === expectedRevision
    && capability.running_revision === expectedRevision);
  const current = Boolean(installationMatches && descriptorIdentity.runtime_mode === identity.mode
    && capability.available && (!expectedRevision || revisionMatches));
  return {
    current,
    stale: !current,
    installation_matches: installationMatches,
    expected_installation_id: identity.installation_id,
    observed_installation_id: descriptorIdentity.installation_id || null,
    expected_runtime_mode: identity.mode,
    observed_runtime_mode: descriptorIdentity.runtime_mode || null,
    expected_disk_revision: expectedRevision || null,
    revision_matches: revisionMatches,
    capability
  };
}

function sameWorkspace(left, right) {
  const first = text(left);
  const second = text(right);
  if (!first || !second) return false;
  try {
    return path.resolve(first).toLowerCase() === path.resolve(second).toLowerCase();
  } catch {
    return false;
  }
}

async function proveIdlePackagedHandoff({ client, paths, descriptor, timeoutMs = 15_000 } = {}) {
  const expected = expectedIdentity(paths);
  const observed = normalizeDescriptorIdentity(descriptor);
  if (expected.mode !== 'development' || observed.runtime_mode !== 'packaged') {
    throw bootstrapError(
      'RECOVERY_HOST_INSTALLATION_MISMATCH',
      'Cross-installation handoff is supported only from an idle packaged host to the selected development checkout.'
    );
  }
  if (!client || typeof client.status !== 'function' || typeof client.call !== 'function') {
    throw bootstrapError(
      'RECOVERY_HOST_IDLE_HANDOFF_UNVERIFIED',
      'The packaged Recovery Host cannot provide an authenticated idle-handoff proof.'
    );
  }
  const request = {
    ...descriptorRequestOptions(descriptor),
    timeout: Math.min(8_000, Math.max(1_500, Number(timeoutMs) || 8_000))
  };
  let status;
  let runtime;
  try {
    status = await client.status(request);
    runtime = await client.call('runtime.lightweight_snapshot', [], request);
  } catch (error) {
    throw bootstrapError(
      'RECOVERY_HOST_IDLE_HANDOFF_UNVERIFIED',
      'The packaged Recovery Host idle state could not be verified.',
      { cause_code: String(error?.code || '') || null }
    );
  }
  const descriptorToken = normalizeProcessStartToken(descriptor?.owner_process_start_token);
  const statusToken = normalizeProcessStartToken(status?.process_start_token);
  const exactHost = Number(status?.pid || 0) === Number(descriptor?.owner_pid || 0)
    && text(status?.instance_id) === text(descriptor?.instance_id)
    && Boolean(descriptorToken && statusToken === descriptorToken);
  const workspace = text(runtime?.device?.workspace || runtime?.workspace);
  const epochState = text(runtime?.activationEpoch?.epoch_state || runtime?.activationEpoch?.state).toUpperCase();
  const terminalEpoch = ['NONE', 'READY', 'FAILED'].includes(epochState);
  const workspaceMatches = sameWorkspace(workspace, paths.appRoot());
  const safe = exactHost
    && status?.electron_ui_recovery?.alive === false
    && runtime?.telemetryAvailable === true
    && runtime?.signalStale === false
    && runtime?.snapshotBusy === false
    && runtime?.busy !== true
    && runtime?.recovering !== true
    && runtime?.mcpRunning === false
    && runtime?.nativeAlive === false
    && runtime?.tunnelRunning === false
    && terminalEpoch
    && workspaceMatches;
  if (!safe) {
    throw bootstrapError(
      'RECOVERY_HOST_IDLE_HANDOFF_REFUSED',
      'The packaged Recovery Host is not provably idle for a development-checkout handoff.',
      {
        exact_host: exactHost,
        ui_alive: status?.electron_ui_recovery?.alive === true,
        telemetry_available: runtime?.telemetryAvailable === true,
        signal_stale: runtime?.signalStale !== false,
        snapshot_busy: runtime?.snapshotBusy !== false,
        recovering: runtime?.recovering === true,
        mcp_running: runtime?.mcpRunning === true,
        native_alive: runtime?.nativeAlive === true,
        tunnel_running: runtime?.tunnelRunning === true,
        activation_epoch_state: epochState || null,
        workspace_matches: workspaceMatches
      }
    );
  }
  return {
    exact_host: true,
    workspace,
    activation_epoch_state: epochState,
    observed_at_unix_ms: Date.now()
  };
}

function buildBootstrapEnvelope({
  paths,
  descriptor,
  operationId,
  sourceCheckpoint,
  expectedDiskRevision,
  requestedAtUnixMs = Date.now(),
  expiresAtUnixMs = Number(requestedAtUnixMs) + DEFAULT_TTL_MS,
  activationEpochId = '',
  refresh = false,
  trustedRecoveryBootstrap = null,
  oldHostProcessStartToken = descriptor?.owner_process_start_token
} = {}) {
  const identity = expectedIdentity(paths);
  const id = validateOperationId(operationId);
  const requestedAt = Number(requestedAtUnixMs);
  const expiresAt = Number(expiresAtUnixMs);
  const oldPid = Number(descriptor?.owner_pid || 0);
  const oldInstanceId = text(descriptor?.instance_id);
  const oldProcessStartToken = normalizeProcessStartToken(oldHostProcessStartToken);
  const revision = text(expectedDiskRevision).toLowerCase();
  if (!Number.isSafeInteger(requestedAt) || !Number.isSafeInteger(expiresAt)
    || expiresAt <= requestedAt || expiresAt - requestedAt > DEFAULT_TTL_MS
    || !Number.isInteger(oldPid) || oldPid <= 0 || !oldInstanceId || !oldProcessStartToken
    || !REVISION.test(revision)) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap timing, old identity, or revision is invalid.');
  }
  const epoch = text(activationEpochId);
  if (epoch && !EPOCH_ID.test(epoch)) throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap activation epoch is invalid.');
  const processRefresh = refresh === true;
  const canonicalSourceCheckpoint = validateOptionalRefreshCheckpoint(sourceCheckpoint, processRefresh);
  const trusted = validateTrustedRecoveryBootstrap(trustedRecoveryBootstrap, canonicalSourceCheckpoint, processRefresh);
  const envelope = {
    schema_version: BOOTSTRAP_SCHEMA_VERSION,
    kind: BOOTSTRAP_KIND,
    operation_id: id,
    requested_at_unix_ms: requestedAt,
    expires_at_unix_ms: expiresAt,
    old_host_pid: oldPid,
    old_host_process_start_token: oldProcessStartToken,
    old_host_instance_id: oldInstanceId,
    expected_installation_id: identity.installation_id,
    runtime_mode: identity.mode,
    app_root: path.resolve(paths.appRoot()),
    expected_disk_revision: revision,
    // A refresh preserves durable AWAITING_ACCEPTANCE rows but never treats
    // them as live mutation authority. Active tools, commands, agent lanes,
    // managed jobs, P5 epochs and unexplained ownership remain hard blockers
    // in the independent canonical census.
    allow_acceptance_pending: true,
    source_checkpoint: canonicalSourceCheckpoint,
    ...(processRefresh ? { refresh: true } : {}),
    ...(trusted ? { trusted_recovery_bootstrap: trusted } : {}),
    ...(epoch ? { activation_epoch_id: epoch } : {})
  };
  return { ...envelope, integrity_sha256: canonicalDigest(envelope) };
}

function validateBootstrapEnvelope(raw, paths, { bootstrapId = '', now = Date.now(), allowExpired = false } = {}) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap envelope is not an object.');
  const required = [
    'schema_version', 'kind', 'operation_id', 'requested_at_unix_ms',
    'expires_at_unix_ms', 'old_host_pid', 'old_host_process_start_token', 'old_host_instance_id',
    'expected_installation_id', 'runtime_mode', 'app_root',
    'expected_disk_revision', 'allow_acceptance_pending', 'source_checkpoint', 'integrity_sha256'
  ];
  const optional = ['activation_epoch_id', 'refresh', 'trusted_recovery_bootstrap'];
  const keys = Object.keys(raw).sort();
  const allowed = new Set([...required, ...optional]);
  if (required.some((key) => !keys.includes(key)) || keys.some((key) => !allowed.has(key))) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap envelope fields are not canonical.');
  }
  if (Number(raw.schema_version) !== BOOTSTRAP_SCHEMA_VERSION || raw.kind !== BOOTSTRAP_KIND) throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap envelope schema is unsupported.');
  const operationId = validateOperationId(raw.operation_id);
  if (bootstrapId && operationId !== validateOperationId(bootstrapId)) throw bootstrapError('RECOVERY_BOOTSTRAP_ID_MISMATCH', 'Recovery Host bootstrap argument does not match the durable envelope.');
  const requestedAt = Number(raw.requested_at_unix_ms);
  const expiresAt = Number(raw.expires_at_unix_ms);
  if (!Number.isSafeInteger(requestedAt) || !Number.isSafeInteger(expiresAt)
    || expiresAt <= requestedAt || expiresAt - requestedAt > DEFAULT_TTL_MS) throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap timing is invalid.');
  if (!allowExpired && Number(now) >= expiresAt) throw bootstrapError('RECOVERY_BOOTSTRAP_EXPIRED', 'Recovery Host bootstrap envelope has expired.');
  const oldProcessStartToken = normalizeProcessStartToken(raw.old_host_process_start_token);
  if (!Number.isInteger(Number(raw.old_host_pid)) || Number(raw.old_host_pid) <= 0
    || !oldProcessStartToken || !text(raw.old_host_instance_id)) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap old process identity is invalid.');
  }
  const identity = expectedIdentity(paths);
  if (text(raw.expected_installation_id).toLowerCase() !== identity.installation_id
    || text(raw.runtime_mode) !== identity.mode
    || path.resolve(String(raw.app_root || '')) !== path.resolve(paths.appRoot())) throw bootstrapError('RECOVERY_BOOTSTRAP_INSTALLATION_MISMATCH', 'Recovery Host bootstrap belongs to another checkout or runtime installation.');
  if (!REVISION.test(text(raw.expected_disk_revision).toLowerCase())) throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap expected revision is invalid.');
  if (typeof raw.allow_acceptance_pending !== 'boolean') throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap acceptance policy is invalid.');
  if (raw.activation_epoch_id !== undefined && raw.activation_epoch_id !== null && !EPOCH_ID.test(text(raw.activation_epoch_id))) throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap activation epoch is invalid.');
  if (raw.refresh !== undefined && typeof raw.refresh !== 'boolean') {
    throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap refresh flag is invalid.');
  }
  const refresh = raw.refresh === true;
  const checkpoint = validateOptionalRefreshCheckpoint(raw.source_checkpoint, refresh);
  const trusted = validateTrustedRecoveryBootstrap(raw.trusted_recovery_bootstrap, checkpoint, refresh);
  if (typeof raw.integrity_sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(raw.integrity_sha256)
    || raw.integrity_sha256 !== canonicalDigest(withoutIntegrity(raw))) throw bootstrapError('RECOVERY_BOOTSTRAP_INTEGRITY_FAILED', 'Recovery Host bootstrap envelope integrity check failed.');
  return {
    ...raw,
    operation_id: operationId,
    requested_at_unix_ms: requestedAt,
    expires_at_unix_ms: expiresAt,
    old_host_pid: Number(raw.old_host_pid),
    old_host_process_start_token: oldProcessStartToken,
    old_host_instance_id: text(raw.old_host_instance_id),
    expected_installation_id: identity.installation_id,
    runtime_mode: identity.mode,
    app_root: path.resolve(paths.appRoot()),
    expected_disk_revision: text(raw.expected_disk_revision).toLowerCase(),
    refresh,
    source_checkpoint: checkpoint,
    trusted_recovery_bootstrap: trusted,
    bootstrap_path: bootstrapFile(paths, operationId),
    result_path: bootstrapResultFile(paths, operationId)
  };
}

function readBootstrapEnvelope(paths, options = {}) {
  const operationId = validateOperationId(options.bootstrapId);
  const file = bootstrapFile(paths, operationId);
  let stat;
  try { stat = fs.lstatSync(file); } catch (error) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_UNAVAILABLE', 'Recovery Host bootstrap envelope is unavailable.', { cause_code: error?.code || '' });
  }
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size > MAX_ENVELOPE_BYTES) throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap envelope is not a bounded regular file.');
  let raw;
  try { raw = JSON.parse(fs.readFileSync(file, 'utf8')); } catch (error) { throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap envelope is invalid JSON.', { cause_code: error?.code || '' }); }
  return validateBootstrapEnvelope(raw, paths, { ...options, bootstrapId: operationId });
}

function writeBootstrapEnvelope(paths, envelope) {
  validateBootstrapEnvelope(envelope, paths, { bootstrapId: envelope?.operation_id, now: Number(envelope?.requested_at_unix_ms || Date.now()) - 1 });
  const operationId = validateOperationId(envelope?.operation_id);
  const file = bootstrapFile(paths, operationId);
  ensureParent(file);
  const encoded = JSON.stringify(envelope);
  if (Buffer.byteLength(encoded, 'utf8') > MAX_ENVELOPE_BYTES) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap envelope exceeds the bounded size.');
  }
  let handle;
  try {
    handle = fs.openSync(file, 'wx', 0o600);
    fs.writeFileSync(handle, encoded, 'utf8');
    fs.fsyncSync(handle);
  } catch (error) {
    if (error?.code === 'EEXIST') {
      throw bootstrapError('RECOVERY_BOOTSTRAP_EXISTS', 'This Recovery Host bootstrap operation is already pending.');
    }
    throw error;
  } finally {
    if (handle !== undefined) fs.closeSync(handle);
  }
  try { fs.chmodSync(file, 0o600); } catch { /* best effort on Windows */ }
  return file;
}

function validateBootstrapResult(raw, operationId = '') {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_RESULT_INVALID', 'Recovery Host bootstrap result is not an object.');
  }
  const expectedOperationId = validateOperationId(operationId || raw.operation_id);
  const state = text(raw.state);
  const recordedAt = Number(raw.completed_at_unix_ms);
  if (Number(raw.schema_version) !== BOOTSTRAP_SCHEMA_VERSION || raw.kind !== BOOTSTRAP_RESULT_KIND
    || raw.operation_id !== expectedOperationId
    || !Object.prototype.hasOwnProperty.call(RESULT_STATE_ORDER, state)
    || !Number.isSafeInteger(recordedAt) || recordedAt <= 0
    || !/^[a-f0-9]{64}$/.test(String(raw.integrity_sha256 || ''))
    || raw.integrity_sha256 !== canonicalDigest(withoutIntegrity(raw))) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_RESULT_INVALID', 'Recovery Host bootstrap result failed validation.');
  }
  return raw;
}

function writeBootstrapResult(paths, result = {}, options = {}) {
  const operationId = validateOperationId(result.operation_id);
  const state = Object.prototype.hasOwnProperty.call(RESULT_STATE_ORDER, text(result.state))
    ? text(result.state) : 'failed';
  const recordedAt = Number(result.completed_at_unix_ms || Date.now());
  if (!Number.isSafeInteger(recordedAt) || recordedAt <= 0) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_RESULT_INVALID', 'Recovery Host bootstrap result timestamp is invalid.');
  }
  const base = {
    schema_version: BOOTSTRAP_SCHEMA_VERSION,
    kind: BOOTSTRAP_RESULT_KIND,
    operation_id: operationId,
    state,
    completed_at_unix_ms: recordedAt,
    ...(result.error ? { error: {
      code: text(result.error.code || 'RECOVERY_BOOTSTRAP_FAILED').slice(0, 120),
      message: text(result.error.message || result.error).slice(0, 2000),
      ...(Object.keys(bootstrapFailureDetails(result.error.details)).length
        ? { details: bootstrapFailureDetails(result.error.details) } : {})
    } } : {}),
    ...(result.result !== undefined ? { result: result.result } : {})
  };
  const payload = { ...base, integrity_sha256: canonicalDigest(base) };
  const file = bootstrapResultFile(paths, operationId);
  ensureParent(file);
  const encoded = JSON.stringify(payload);
  if (Buffer.byteLength(encoded, 'utf8') > MAX_RESULT_BYTES) throw bootstrapError('RECOVERY_BOOTSTRAP_RESULT_TOO_LARGE', 'Recovery Host bootstrap result exceeds the bounded size.');
  const lock = acquireBootstrapResultLock(paths, operationId, options);
  try {
    if (fs.existsSync(file)) {
      let existing;
      try {
        const stat = fs.lstatSync(file);
        if (!stat.isFile() || stat.isSymbolicLink() || stat.size > MAX_RESULT_BYTES) throw new Error('not a bounded regular file');
        existing = validateBootstrapResult(JSON.parse(fs.readFileSync(file, 'utf8')), operationId);
      } catch (error) {
        throw bootstrapError('RECOVERY_BOOTSTRAP_RESULT_INVALID', 'Existing Recovery Host bootstrap result is invalid and was not overwritten.', { cause_code: error?.code || '' });
      }
      if (TERMINAL_RESULT_STATES.has(existing.state)) {
        if (existing.state === state) {
          const existingTerminal = { state: existing.state, error: existing.error || null, result: existing.result ?? null };
          const requestedTerminal = { state, error: payload.error || null, result: payload.result ?? null };
          if (canonicalDigest(existingTerminal) === canonicalDigest(requestedTerminal)) return file;
          throw bootstrapError('RECOVERY_BOOTSTRAP_RESULT_CONFLICT', 'Terminal Recovery Host bootstrap result payload is immutable.', { state: existing.state });
        }
        throw bootstrapError('RECOVERY_BOOTSTRAP_RESULT_TERMINAL', 'Terminal Recovery Host bootstrap result is immutable.', { state: existing.state });
      }
      if (RESULT_STATE_ORDER[state] < RESULT_STATE_ORDER[existing.state]) {
        throw bootstrapError('RECOVERY_BOOTSTRAP_RESULT_REGRESSION', 'Recovery Host bootstrap result cannot move backwards.', {
          state: existing.state,
          requested_state: state
        });
      }
      if (recordedAt < Number(existing.completed_at_unix_ms)) {
        throw bootstrapError('RECOVERY_BOOTSTRAP_RESULT_CLOCK_REGRESSION', 'Recovery Host bootstrap result timestamp cannot move backwards.');
      }
    }
    writeJsonAtomic(file, payload);
    try { fs.chmodSync(file, 0o600); } catch { /* best effort on Windows */ }
    return file;
  } finally {
    releaseBootstrapResultLock(lock);
  }
}

function readBootstrapResult(paths, operationId = '') {
  const id = validateOperationId(operationId);
  const file = bootstrapResultFile(paths, id);
  try {
    const stat = fs.lstatSync(file);
    if (!stat.isFile() || stat.isSymbolicLink() || stat.size > MAX_RESULT_BYTES) return null;
    const raw = JSON.parse(fs.readFileSync(file, 'utf8'));
    return validateBootstrapResult(raw, id);
  } catch { return null; }
}

function removeBootstrapEnvelope(paths, operationId, expectedIntegrity = '') {
  const id = validateOperationId(operationId);
  const file = bootstrapFile(paths, id);
  let stat;
  try { stat = fs.lstatSync(file); } catch (error) {
    if (error?.code === 'ENOENT') return false;
    throw error;
  }
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size > MAX_ENVELOPE_BYTES) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap envelope is not a bounded regular file.');
  }
  let raw;
  try { raw = JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch (error) { throw bootstrapError('RECOVERY_BOOTSTRAP_INVALID', 'Recovery Host bootstrap envelope is invalid JSON.', { cause_code: error?.code || '' }); }
  const envelope = validateBootstrapEnvelope(raw, paths, { bootstrapId: id, allowExpired: true });
  const expected = text(expectedIntegrity).toLowerCase();
  if (expected && envelope.integrity_sha256 !== expected) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_INTEGRITY_FAILED', 'Recovery Host bootstrap envelope changed before guarded removal.');
  }
  fs.unlinkSync(file);
  return true;
}

async function defaultTerminateProcess(identity, options = {}) {
  return terminateExactProcessTree(identity, options);
}

/**
 * Retire an authenticated stale host and spawn the current checkout.  The
 * function never sends `code.activate_update` to the stale process.  The new
 * process receives only the bootstrap operation id; it reads and validates the
 * durable envelope itself before invoking FullCleanActivation.
 */
async function bootstrapCurrentRecoveryHost({
  app,
  paths,
  client = new RecoveryIpcClient({ paths }),
  descriptor = loadRecoveryDescriptor(paths),
  status = null,
  operationId,
  sourceCheckpoint,
  expectedDiskRevision,
  activationEpochId = '',
  refresh = false,
  trustedRecoveryBootstrap = null,
  forceRefresh = false,
  allowIdlePackagedHandoff = false,
  requestedAtUnixMs = Date.now(),
  expiresAtUnixMs = Number(requestedAtUnixMs) + DEFAULT_TTL_MS,
  timeoutMs = 15_000,
  spawnProcess = spawn,
  terminateProcess = defaultTerminateProcess,
  processIdentityObserver = observeLifecycleProcessIdentity,
  waitForExactExit = waitForExactProcessExit,
  readDescriptor = loadRecoveryDescriptor,
  revalidateTrustedSourceFn = revalidateTrustedRecoveryHostSource,
  sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
  log = null
} = {}) {
  const freshness = assessRecoveryHostFreshness({ paths, descriptor, status, expectedDiskRevision });
  let idlePackagedHandoff = null;
  if (!freshness.installation_matches) {
    const eligible = allowIdlePackagedHandoff === true
      && refresh === true
      && forceRefresh === true
      && (sourceCheckpoint === null || sourceCheckpoint === undefined || sourceCheckpoint === '')
      && !trustedRecoveryBootstrap
      && !text(activationEpochId)
      && freshness.expected_runtime_mode === 'development'
      && freshness.observed_runtime_mode === 'packaged';
    if (!eligible) {
      throw bootstrapError('RECOVERY_HOST_INSTALLATION_MISMATCH', 'Refused to terminate a Recovery Host from another installation.', freshness);
    }
    idlePackagedHandoff = await proveIdlePackagedHandoff({ client, paths, descriptor, timeoutMs });
  }
  if (freshness.current && forceRefresh !== true) {
    return { required: false, stale: false, descriptor, status, freshness };
  }
  const canonicalSourceCheckpoint = validateOptionalRefreshCheckpoint(sourceCheckpoint, refresh === true);
  const trusted = validateTrustedRecoveryBootstrap(
    trustedRecoveryBootstrap,
    canonicalSourceCheckpoint,
    refresh === true
  );
  if (trusted) {
    let verified;
    try {
      verified = await revalidateTrustedSourceFn(paths.appRoot(), canonicalSourceCheckpoint, trusted);
    } catch (error) {
      throw bootstrapError(
        String(error?.code || 'TRUSTED_BOOTSTRAP_SOURCE_UNAVAILABLE'),
        'Trusted Recovery Supervisor bootstrap source could not be revalidated before handoff.',
        { cause_code: String(error?.code || '') || null }
      );
    }
    if (verified?.attestation?.receipt_sha256 !== trusted.receipt_sha256) {
      throw bootstrapError('TRUSTED_BOOTSTRAP_SOURCE_DRIFT', 'Trusted Recovery Supervisor bootstrap source receipt changed before handoff.');
    }
  }
  const ownerPid = Number(descriptor?.owner_pid || 0);
  const ownerInstanceId = text(descriptor?.instance_id);
  if (!Number.isInteger(ownerPid) || ownerPid <= 0 || !ownerInstanceId) throw bootstrapError('RECOVERY_BOOTSTRAP_TARGET_INVALID', 'Stale Recovery Host descriptor has no authenticated process identity.');
  let baselineObservation;
  try { baselineObservation = await processIdentityObserver(ownerPid); }
  catch (error) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_PROCESS_IDENTITY_UNVERIFIED', 'Stale Recovery Host process identity could not be observed.', {
      cause_code: error?.code || ''
    });
  }
  if (baselineObservation?.state === 'absent') {
    throw bootstrapError('RECOVERY_BOOTSTRAP_TARGET_EXITED', 'Stale Recovery Host exited before bootstrap handoff.');
  }
  if (baselineObservation?.state !== 'live') {
    throw bootstrapError('RECOVERY_BOOTSTRAP_PROCESS_IDENTITY_UNVERIFIED', 'Stale Recovery Host process identity could not be observed.');
  }
  let ownerIdentity;
  try {
    ownerIdentity = processIdentityFrom({
      pid: ownerPid,
      process_start_token: baselineObservation.process_start_token
    });
  } catch (error) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_PROCESS_IDENTITY_UNVERIFIED', 'Stale Recovery Host process identity could not be observed.', {
      cause_code: error?.code || ''
    });
  }
  const descriptorToken = normalizeProcessStartToken(descriptor?.owner_process_start_token);
  const descriptorTokenSupplied = descriptor?.owner_process_start_token !== undefined
    && descriptor?.owner_process_start_token !== null
    && String(descriptor.owner_process_start_token).trim() !== '';
  if (descriptorTokenSupplied && !descriptorToken) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_PROCESS_IDENTITY_UNVERIFIED', 'Stale Recovery Host descriptor process identity is invalid.');
  }
  if (descriptorToken && descriptorToken !== ownerIdentity.process_start_token) {
    throw bootstrapError('RECOVERY_BOOTSTRAP_TARGET_CHANGED', 'Recovery Host owner changed before bootstrap handoff.');
  }
  const envelope = buildBootstrapEnvelope({
    paths,
    descriptor,
    operationId,
    sourceCheckpoint: canonicalSourceCheckpoint,
    expectedDiskRevision,
    requestedAtUnixMs,
    expiresAtUnixMs,
    activationEpochId,
    refresh: refresh === true,
    trustedRecoveryBootstrap: trusted,
    oldHostProcessStartToken: ownerIdentity.process_start_token
  });
  const file = writeBootstrapEnvelope(paths, envelope);
  writeBootstrapResult(paths, { operation_id: envelope.operation_id, state: 'pending' });
  const descriptorOptions = descriptorRequestOptions(descriptor);
  let childStopMayHaveOccurred = false;
  try {
    // Ask the authenticated host to stop only its children first.  Transport
    // response loss is not proof that the stop did not happen; the exact
    // descriptor/PID checks below remain the mutation authority.
    childStopMayHaveOccurred = true;
    try {
      await client.stop(
        { manual: false },
        {
          ...descriptorOptions,
          timeout: Math.min(15_000, Math.max(1_000, Number(timeoutMs) || 15_000))
        }
      );
    }
    catch (error) {
      log?.warn?.('Stale Recovery Host stop response was unavailable; reconciling exact process identity before handoff.', {
        operationId: envelope.operation_id,
        code: error?.code || ''
      });
    }
    let verified;
    try { verified = readDescriptor(paths); }
    catch (error) {
      if (error?.code === 'RECOVERY_DESCRIPTOR_STALE' || error?.code === 'ENOENT') verified = null;
      else throw error;
    }
    if (verified && (Number(verified.owner_pid) !== ownerPid || text(verified.instance_id) !== ownerInstanceId)) {
      throw bootstrapError('RECOVERY_BOOTSTRAP_TARGET_CHANGED', 'Recovery Host owner changed during bootstrap handoff.');
    }
    const verifiedToken = normalizeProcessStartToken(verified?.owner_process_start_token);
    if (verifiedToken && verifiedToken !== ownerIdentity.process_start_token) {
      throw bootstrapError('RECOVERY_BOOTSTRAP_TARGET_CHANGED', 'Recovery Host owner changed during bootstrap handoff.');
    }
    let afterStop;
    try { afterStop = await processIdentityObserver(ownerPid); }
    catch (error) {
      throw bootstrapError('RECOVERY_BOOTSTRAP_PROCESS_IDENTITY_UNVERIFIED', 'Recovery Host process identity became unavailable during bootstrap handoff.', {
        cause_code: error?.code || ''
      });
    }
    if (afterStop?.state !== 'absent' && afterStop?.state !== 'live') {
      throw bootstrapError('RECOVERY_BOOTSTRAP_PROCESS_IDENTITY_UNVERIFIED', 'Recovery Host process identity became unavailable during bootstrap handoff.');
    }
    const oldIdentityStillLive = afterStop?.state === 'live' && sameProcessIdentity(ownerIdentity, afterStop);
    if (!verified && oldIdentityStillLive) {
      throw bootstrapError('RECOVERY_BOOTSTRAP_TARGET_UNVERIFIED', 'Recovery Host descriptor disappeared while the exact previous owner was still alive.');
    }
    if (oldIdentityStillLive) {
      try {
        await terminateProcess(ownerIdentity, {
          observeProcessIdentity: processIdentityObserver,
          sleep,
          timeoutMs: Math.min(10_000, Math.max(500, Number(timeoutMs) || 15_000))
        });
      } catch (error) {
        if (error?.code === 'PROCESS_IDENTITY_CHANGED') {
          throw bootstrapError('RECOVERY_BOOTSTRAP_TARGET_CHANGED', 'Recovery Host owner changed before exact termination.');
        }
        if (error?.code === 'PROCESS_IDENTITY_UNVERIFIED') {
          throw bootstrapError('RECOVERY_BOOTSTRAP_PROCESS_IDENTITY_UNVERIFIED', 'Recovery Host process identity could not be verified for termination.');
        }
        throw bootstrapError('RECOVERY_BOOTSTRAP_TERMINATION_FAILED', 'Stale Recovery Host exact termination failed.', {
          cause_code: error?.code || '',
          termination_cause_code: error?.details?.cause_code || '',
          pid: ownerPid,
          exit_code: error?.details?.exit_code
        });
      }
    }
    try {
      await waitForExactExit(ownerIdentity, {
        observeProcessIdentity: processIdentityObserver,
        sleep,
        timeoutMs: Math.min(10_000, Math.max(500, Number(timeoutMs) || 15_000))
      });
    } catch (error) {
      if (error?.code === 'PROCESS_IDENTITY_UNVERIFIED') {
        throw bootstrapError('RECOVERY_BOOTSTRAP_PROCESS_IDENTITY_UNVERIFIED', 'Recovery Host process identity became unavailable while waiting for exit.');
      }
      if (error?.code === 'PROCESS_TERMINATION_TIMEOUT') {
        throw bootstrapError('RECOVERY_BOOTSTRAP_TERMINATION_TIMEOUT', 'Stale Recovery Host did not exit before bootstrap launch.');
      }
      throw error;
    }
    // Record STARTED before the spawn boundary.  The spawned host may finish
    // very quickly; writing this state afterwards could otherwise overwrite a
    // terminal receipt from the replacement.
    writeBootstrapResult(paths, {
      operation_id: envelope.operation_id,
      state: 'started',
      result: { launch_pending: true, expected_disk_revision: envelope.expected_disk_revision }
    });
    const launchOptions = {
      executablePath: typeof paths.executablePath === 'function' ? paths.executablePath() : undefined,
      bootstrapId: envelope.operation_id
    };
    const pid = await spawnRecoveryHost(app, spawnProcess, launchOptions);
    log?.info?.('Started current-checkout Recovery Host through stale-host bootstrap', { operationId: envelope.operation_id, oldPid: ownerPid, pid });
    return {
      required: true,
      stale: true,
      bootstrap: envelope,
      bootstrap_path: file,
      pid,
      freshness,
      ...(idlePackagedHandoff ? { idle_packaged_handoff: idlePackagedHandoff } : {})
    };
  } catch (error) {
    const state = String(error?.code || '') === 'RECOVERY_BOOTSTRAP_EXPIRED' || Date.now() >= envelope.expires_at_unix_ms
      ? 'expired' : 'failed';
    try {
      writeBootstrapResult(paths, {
        operation_id: envelope.operation_id,
        state,
        error: { code: error?.code || 'RECOVERY_BOOTSTRAP_FAILED', message: error?.message || String(error), details: error?.details }
      });
    } catch { /* preserve the original handoff failure */ }
    // runtime.stop happens before exact Recovery Host termination.  If a
    // later fail-closed identity check refuses the handoff, restore the old
    // runtime only when both the authenticated descriptor and OS start-token
    // still prove the exact old owner.  This compensation cannot touch a
    // replacement/recycled PID and never changes the terminal failure receipt.
    if (childStopMayHaveOccurred && typeof client.start === 'function') {
      try {
        const currentDescriptor = readDescriptor(paths);
        const descriptorStillExact = Number(currentDescriptor?.owner_pid || 0) === ownerPid
          && text(currentDescriptor?.instance_id) === ownerInstanceId
          && normalizeProcessStartToken(currentDescriptor?.owner_process_start_token)
            === ownerIdentity.process_start_token;
        if (descriptorStillExact) {
          const observed = await processIdentityObserver(ownerPid);
          if (observed?.state === 'live' && sameProcessIdentity(ownerIdentity, observed)) {
            await client.start(
              { reason: 'bootstrap_handoff_rollback' },
              {
                ...descriptorOptions,
                timeout: Math.min(45_000, Math.max(5_000, Number(timeoutMs) || 15_000))
              }
            );
            log?.warn?.('Restored the exact previous Recovery Host runtime after a refused bootstrap handoff.', {
              operationId: envelope.operation_id,
              code: error?.code || 'RECOVERY_BOOTSTRAP_FAILED'
            });
          }
        }
      } catch (rollbackError) {
        log?.error?.('Could not restore the previous Recovery Host runtime after bootstrap failure.', {
          operationId: envelope.operation_id,
          code: rollbackError?.code || 'RECOVERY_BOOTSTRAP_ROLLBACK_FAILED'
        });
      }
    }
    throw error;
  }
}

module.exports = {
  BOOTSTRAP_SCHEMA_VERSION,
  BOOTSTRAP_KIND,
  BOOTSTRAP_RESULT_KIND,
  DEFAULT_TTL_MS,
  canonicalDigest,
  bootstrapCapability,
  assessRecoveryHostFreshness,
  proveIdlePackagedHandoff,
  buildBootstrapEnvelope,
  validateBootstrapEnvelope,
  readBootstrapEnvelope,
  writeBootstrapEnvelope,
  writeBootstrapResult,
  readBootstrapResult,
  removeBootstrapEnvelope,
  bootstrapCurrentRecoveryHost,
  defaultTerminateProcess,
  bootstrapFile,
  bootstrapResultFile
};
