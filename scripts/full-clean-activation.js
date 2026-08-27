#!/usr/bin/env node
'use strict';

/**
 * Explicit operator entry point for a full-system activation restart.
 *
 * This file deliberately does not implement the restart transaction.  It
 * binds a caller-supplied accepted checkpoint to the authenticated Recovery
 * Host IPC contract.  For --execute, the command first persists a bounded
 * post-tool-call intent and exits; a detached worker then performs the
 * authenticated request after this Coding-VP call has released its active
 * MCP slot.  The Recovery Host remains the sole owner of admission fencing,
 * durable epoch creation, process handoff, census, and final readiness.
 *
 * The command is intentionally separate from dev-ui-lifecycle.js: dev:replace
 * is a UI lifecycle helper and cannot preserve ACCEPTING orchestration state.
 * This command is the non-inline surface that ChatGPT's normal Coding-VP
 * connector can invoke through exec_command.  The internal worker mode is
 * intentionally not part of the public command surface.
 */

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');
const {
  RecoveryIpcClient,
  loadRecoveryDescriptor
} = require('../electron/services/recoveryIpc');
const {
  createDevelopmentPaths
} = require('./dev-ui-lifecycle');
const {
  descriptorMatchesInstallation,
  descriptorRequestOptions
} = require('../electron/services/recoveryHostLauncher');
const {
  assessRecoveryHostFreshness,
  bootstrapCurrentRecoveryHost,
  readBootstrapResult
} = require('../electron/services/recoveryBootstrap');
const { hashComponentRevision } = require('../electron/services/componentRevision');
const { readJson, writeJsonAtomic } = require('../electron/services/jsonStore');

const CHECKPOINT_FIELDS = Object.freeze([
  'checkpoint_id',
  'run_id',
  'wave_id',
  'proof_fingerprint',
  'git_head'
]);
const HEX64 = /^[a-f0-9]{64}$/;
const GIT_OBJECT_ID = /^[a-f0-9]{40,64}$/;
const CHECKPOINT_ID = /^[A-Za-z0-9][A-Za-z0-9_-]{7,127}$/;
const DEFAULT_TTL_MS = 55_000;
const DEFAULT_TIMEOUT_MS = 120_000;
const POLL_MS = 500;

// A Coding-VP exec_command is itself accounted as an active MCP tool call.
// Calling the Recovery Host synchronously from that command can therefore
// make the old MCP reject its own activation census with RUNTIME_BUSY.  The
// command layer uses a small, local durable bridge for explicit activation:
// the parent writes an immutable intent, starts a detached worker, and exits;
// the worker only contacts Recovery Host after the parent call has ended.
const DEFERRED_SCHEMA_VERSION = 1;
const DEFERRED_KIND = 'full_clean_activation_deferred';
const DEFERRED_LOCK_KIND = `${DEFERRED_KIND}_worker_lock`;
const DEFERRED_DIRECTORY = 'full-clean-activation';
const DEFERRED_PARENT_POLL_MS = 100;
const DEFERRED_PARENT_GRACE_MS = 300;
// The queue lifetime covers the current full-clean coordinator budget (120s)
// plus bounded ownership/handoff overhead.  It is intentionally separate from
// the authenticated activation request TTL, which is still capped at the
// Recovery Host's current 55s request contract below.
const DEFERRED_DEFAULT_TTL_MS = 180_000;
const DEFERRED_MAX_TTL_MS = 300_000;
const DEFERRED_ACTIVATION_TTL_MS = DEFAULT_TTL_MS;
const DEFERRED_PARENT_WAIT_MAX_MS = 30_000;
const DEFERRED_PREFLIGHT_RETRY_MS = 250;
const DEFERRED_RESULT_MAX_BYTES = 256 * 1024;
const DEFERRED_LOCK_MAX_BYTES = 16 * 1024;
const DEFERRED_OPERATION_ID = /^full-clean-cli-[A-Za-z0-9_-]{15,127}$/;
const ACTIVATION_RESPONSE_LOSS_CODES = new Set([
  'ECONNABORTED', 'ECONNREFUSED', 'ECONNRESET', 'EPIPE', 'ENOENT', 'ETIMEDOUT',
  'RECOVERY_DESCRIPTOR_CHANGED', 'RECOVERY_DESCRIPTOR_STALE', 'RECOVERY_RESPONSE_INVALID',
  'RECOVERY_HOST_UNAVAILABLE', 'RECOVERY_REQUEST_TIMEOUT'
]);
const ACTIVATION_TERMINAL_STATES = new Set(['FAILED']);

function activationCommandError(code, message, details = {}) {
  return Object.assign(new Error(message), { code, details });
}

function parseCheckpoint(raw) {
  if (typeof raw !== 'string' || !raw.trim()) {
    throw activationCommandError(
      'ACTIVATION_SOURCE_CHECKPOINT_REQUIRED',
      'Set FULL_CLEAN_SOURCE_CHECKPOINT_JSON to the exact accepted checkpoint payload.'
    );
  }
  let value;
  try {
    value = JSON.parse(raw);
  } catch {
    throw activationCommandError(
      'ACTIVATION_SOURCE_CHECKPOINT_INVALID',
      'FULL_CLEAN_SOURCE_CHECKPOINT_JSON is not valid JSON.'
    );
  }
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw activationCommandError(
      'ACTIVATION_SOURCE_CHECKPOINT_INVALID',
      'The source checkpoint must be a JSON object.'
    );
  }
  const keys = Object.keys(value).sort();
  if (JSON.stringify(keys) !== JSON.stringify([...CHECKPOINT_FIELDS].sort())) {
    throw activationCommandError(
      'ACTIVATION_SOURCE_CHECKPOINT_INVALID',
      'The source checkpoint must contain exactly the five canonical fields.',
      { fields: CHECKPOINT_FIELDS }
    );
  }
  const checkpoint = Object.fromEntries(CHECKPOINT_FIELDS.map((field) => [field, value[field]]));
  for (const field of ['checkpoint_id', 'run_id', 'wave_id']) {
    if (typeof checkpoint[field] !== 'string' || !CHECKPOINT_ID.test(checkpoint[field])) {
      throw activationCommandError('ACTIVATION_SOURCE_CHECKPOINT_INVALID', `${field} is not canonical.`);
    }
  }
  if (typeof checkpoint.proof_fingerprint !== 'string' || !HEX64.test(checkpoint.proof_fingerprint)) {
    throw activationCommandError('ACTIVATION_SOURCE_CHECKPOINT_INVALID', 'proof_fingerprint is not a SHA-256 identity.');
  }
  if (typeof checkpoint.git_head !== 'string' || !GIT_OBJECT_ID.test(checkpoint.git_head)) {
    throw activationCommandError('ACTIVATION_SOURCE_CHECKPOINT_INVALID', 'git_head is not a Git object identity.');
  }
  return checkpoint;
}

function deferredOperationId(now = Date.now()) {
  const timestamp = Number.isSafeInteger(Number(now)) ? Number(now) : Date.now();
  return `full-clean-cli-${timestamp.toString(36)}-${crypto.randomBytes(12).toString('hex')}`;
}

function assertDeferredOperationId(value) {
  const operationId = String(value || '').trim();
  if (!DEFERRED_OPERATION_ID.test(operationId)) {
    throw activationCommandError(
      'DEFERRED_REQUEST_INVALID',
      'The deferred activation operation_id is invalid.'
    );
  }
  return operationId;
}

function deferredDirectory(paths) {
  const dataRoot = String(paths?.dataRoot?.() || '').trim();
  if (!dataRoot || !path.isAbsolute(dataRoot)) {
    throw activationCommandError(
      'DEFERRED_DATA_ROOT_UNAVAILABLE',
      'The shared runtime data root is unavailable for deferred activation.'
    );
  }
  return path.join(path.resolve(dataRoot), DEFERRED_DIRECTORY);
}

function deferredPath(paths, operationId, suffix = '') {
  const id = assertDeferredOperationId(operationId);
  return path.join(deferredDirectory(paths), `${id}${suffix}.json`);
}

function deferredRequestPath(paths, operationId) {
  return deferredPath(paths, operationId);
}

function deferredResultPath(paths, operationId) {
  return deferredPath(paths, operationId, '.result');
}

function deferredParentMarkerPath(paths, operationId) {
  return deferredPath(paths, operationId, '.parent');
}

function deferredWorkerLockPath(paths, operationId) {
  return deferredPath(paths, operationId, '.worker.lock');
}

function deferredResultLockPath(paths, operationId) {
  return deferredPath(paths, operationId, '.result.lock');
}

function deferredPathInside(paths, candidate, expectedSuffix = '') {
  const root = path.resolve(deferredDirectory(paths));
  const resolved = path.resolve(String(candidate || ''));
  const relative = path.relative(root, resolved);
  if (!relative || relative.startsWith('..') || path.isAbsolute(relative)) {
    throw activationCommandError(
      'DEFERRED_REQUEST_PATH_INVALID',
      'The deferred activation path is outside the runtime data root.'
    );
  }
  const basename = path.basename(resolved);
  if (expectedSuffix && !basename.endsWith(`${expectedSuffix}.json`)) {
    throw activationCommandError(
      'DEFERRED_REQUEST_PATH_INVALID',
      'The deferred activation path has an unexpected file suffix.'
    );
  }
  return resolved;
}

function canonicalDigest(value) {
  return crypto.createHash('sha256').update(JSON.stringify(value), 'utf8').digest('hex');
}

function boundedJsonValue(value, maxBytes = DEFERRED_RESULT_MAX_BYTES) {
  try {
    const encoded = JSON.stringify(value);
    if (Buffer.byteLength(encoded, 'utf8') <= maxBytes) return JSON.parse(encoded);
  } catch { /* handled by the bounded fallback below */ }
  return { truncated: true };
}

function serializeActivationError(error) {
  return {
    code: String(error?.code || 'FULL_CLEAN_ACTIVATION_COMMAND_FAILED').slice(0, 120),
    message: String(error?.message || error || 'Full-clean activation failed.').slice(0, 2000),
    details: boundedJsonValue(error?.details || {})
  };
}

function deferredEnvelopePayload(envelope) {
  const { integrity_sha256: _ignored, ...payload } = envelope || {};
  return payload;
}

function deferredResultPayload(result) {
  const { integrity_sha256: _ignored, ...payload } = result || {};
  return payload;
}

function deferredLockPayload(lock) {
  const { integrity_sha256: _ignored, ...payload } = lock || {};
  return payload;
}

function validateDeferredEnvelope(raw, paths, requestPath) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
    throw activationCommandError('DEFERRED_REQUEST_INVALID', 'Deferred activation envelope is not an object.');
  }
  const allowed = [
    'schema_version', 'kind', 'operation_id', 'requested_at_unix_ms',
    'expires_at_unix_ms', 'parent_pid', 'parent_marker', 'source_checkpoint',
    'installation_id', 'runtime_mode', 'app_root', 'parent_marker_nonce', 'integrity_sha256'
  ].sort();
  const keys = Object.keys(raw).sort();
  if (JSON.stringify(keys) !== JSON.stringify(allowed)) {
    throw activationCommandError('DEFERRED_REQUEST_INVALID', 'Deferred activation envelope fields are not canonical.');
  }
  if (Number(raw.schema_version) !== DEFERRED_SCHEMA_VERSION || raw.kind !== DEFERRED_KIND) {
    throw activationCommandError('DEFERRED_REQUEST_INVALID', 'Deferred activation envelope schema is unsupported.');
  }
  const operationId = assertDeferredOperationId(raw.operation_id);
  const requestedAt = Number(raw.requested_at_unix_ms);
  const expiresAt = Number(raw.expires_at_unix_ms);
  const parentPid = Number(raw.parent_pid);
  if (!Number.isSafeInteger(requestedAt) || !Number.isSafeInteger(expiresAt)
    || expiresAt <= requestedAt || expiresAt - requestedAt > DEFERRED_MAX_TTL_MS
    || !Number.isSafeInteger(parentPid) || parentPid <= 0 || parentPid === process.pid) {
    throw activationCommandError('DEFERRED_REQUEST_INVALID', 'Deferred activation timing or parent identity is invalid.');
  }
  if (typeof raw.source_checkpoint !== 'object' || !raw.source_checkpoint || Array.isArray(raw.source_checkpoint)) {
    throw activationCommandError('DEFERRED_REQUEST_INVALID', 'Deferred activation source checkpoint is invalid.');
  }
  // Reuse the exact canonical checkpoint validator; this also rejects any
  // hidden/extra fields introduced by a hand-edited request file.
  const checkpoint = parseCheckpoint(JSON.stringify(raw.source_checkpoint));
  const identity = typeof paths?.runtimeIdentity === 'function' ? paths.runtimeIdentity() : null;
  if (!identity || String(raw.installation_id || '').toLowerCase() !== String(identity.installation_id || '').toLowerCase()
    || String(raw.runtime_mode || '') !== String(identity.mode || '')) {
    throw activationCommandError(
      'RECOVERY_HOST_INSTALLATION_MISMATCH',
      'Deferred activation belongs to another checkout or runtime installation.'
    );
  }
  const appRoot = typeof paths?.appRoot === 'function' ? path.resolve(paths.appRoot()) : '';
  if (!appRoot || path.resolve(String(raw.app_root || '')) !== appRoot) {
    throw activationCommandError('RECOVERY_HOST_INSTALLATION_MISMATCH', 'Deferred activation app root does not match this checkout.');
  }
  const expectedRequest = deferredRequestPath(paths, operationId);
  const resolvedRequest = deferredPathInside(paths, requestPath);
  if (resolvedRequest !== expectedRequest) {
    throw activationCommandError('DEFERRED_REQUEST_PATH_INVALID', 'Deferred activation request path does not match operation_id.');
  }
  const marker = deferredPathInside(paths, raw.parent_marker, '.parent');
  if (marker !== deferredParentMarkerPath(paths, operationId)) {
    throw activationCommandError('DEFERRED_REQUEST_INVALID', 'Deferred activation parent marker is not canonical.');
  }
  const markerNonce = String(raw.parent_marker_nonce || '').trim();
  if (!/^[a-f0-9]{36}$/.test(markerNonce)) {
    throw activationCommandError('DEFERRED_REQUEST_INVALID', 'Deferred activation parent marker nonce is invalid.');
  }
  if (typeof raw.integrity_sha256 !== 'string' || !HEX64.test(raw.integrity_sha256)
    || raw.integrity_sha256 !== canonicalDigest(deferredEnvelopePayload(raw))) {
    throw activationCommandError('DEFERRED_REQUEST_INTEGRITY_FAILED', 'Deferred activation envelope integrity check failed.');
  }
  return {
    ...raw,
    operation_id: operationId,
    requested_at_unix_ms: requestedAt,
    expires_at_unix_ms: expiresAt,
    parent_pid: parentPid,
    source_checkpoint: checkpoint,
    request_path: resolvedRequest,
    result_path: deferredResultPath(paths, operationId),
    parent_marker: marker,
    parent_marker_nonce: markerNonce
  };
}

function readDeferredEnvelope(paths, requestPath) {
  const resolved = deferredPathInside(paths, requestPath);
  let raw;
  try {
    const stat = fs.statSync(resolved);
    if (!stat.isFile() || stat.size > 64 * 1024) {
      throw activationCommandError('DEFERRED_REQUEST_INVALID', 'Deferred activation request exceeds the bounded size.');
    }
    raw = JSON.parse(fs.readFileSync(resolved, 'utf8'));
  } catch (error) {
    if (error?.code === 'DEFERRED_REQUEST_INVALID') throw error;
    throw activationCommandError('DEFERRED_REQUEST_UNAVAILABLE', 'Deferred activation request could not be read.', {
      message: String(error?.message || error)
    });
  }
  return validateDeferredEnvelope(raw, paths, resolved);
}

function readBoundedJsonFile(target, maxBytes) {
  const stat = fs.statSync(target);
  if (!stat.isFile() || stat.size > maxBytes) {
    throw activationCommandError('DEFERRED_LOCK_INVALID', 'Deferred activation lock exceeds its bounded size.');
  }
  return JSON.parse(fs.readFileSync(target, 'utf8'));
}

function writeExclusiveJsonFile(target, value) {
  fs.mkdirSync(path.dirname(target), { recursive: true });
  let descriptor;
  try {
    descriptor = fs.openSync(target, 'wx', 0o600);
    fs.writeFileSync(descriptor, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
    fs.fsyncSync(descriptor);
  } catch (error) {
    if (descriptor !== undefined) {
      try { fs.closeSync(descriptor); } catch { /* preserve original error */ }
      descriptor = undefined;
    }
    // The creator owns cleanup only when it actually created the file.  An
    // EEXIST path belongs to another process and must never be removed here.
    if (error?.code !== 'EEXIST') {
      try { fs.rmSync(target, { force: true }); } catch { /* preserve original error */ }
    }
    throw error;
  } finally {
    if (descriptor !== undefined) fs.closeSync(descriptor);
  }
}

function validateDeferredWorkerLock(raw, envelope) {
  const allowed = [
    'schema_version', 'kind', 'operation_id', 'worker_pid', 'acquired_at_unix_ms',
    'request_sha256', 'claim_nonce', 'integrity_sha256'
  ].sort();
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)
    || JSON.stringify(Object.keys(raw).sort()) !== JSON.stringify(allowed)
    || Number(raw.schema_version) !== DEFERRED_SCHEMA_VERSION
    || raw.kind !== DEFERRED_LOCK_KIND
    || raw.operation_id !== envelope.operation_id
    || !Number.isSafeInteger(Number(raw.worker_pid)) || Number(raw.worker_pid) <= 0
    || !Number.isSafeInteger(Number(raw.acquired_at_unix_ms))
    || raw.request_sha256 !== envelope.integrity_sha256
    || !/^[a-f0-9]{36}$/.test(String(raw.claim_nonce || ''))
    || typeof raw.integrity_sha256 !== 'string' || !HEX64.test(raw.integrity_sha256)
    || raw.integrity_sha256 !== canonicalDigest(deferredLockPayload(raw))) {
    throw activationCommandError(
      'DEFERRED_WORKER_LOCK_INVALID',
      'Deferred activation worker ownership is malformed or belongs to another request.'
    );
  }
  return { ...raw, worker_pid: Number(raw.worker_pid), acquired_at_unix_ms: Number(raw.acquired_at_unix_ms) };
}

function claimDeferredWorker(paths, envelope, {
  pid = process.pid,
  now = Date.now(),
  isAlive = null
} = {}) {
  const workerPid = Number(pid);
  const acquiredAt = Number(now);
  if (!Number.isSafeInteger(workerPid) || workerPid <= 0 || !Number.isSafeInteger(acquiredAt)) {
    throw activationCommandError('DEFERRED_WORKER_LOCK_INVALID', 'Deferred worker identity or time is invalid.');
  }
  const target = deferredWorkerLockPath(paths, envelope.operation_id);
  const base = {
    schema_version: DEFERRED_SCHEMA_VERSION,
    kind: DEFERRED_LOCK_KIND,
    operation_id: envelope.operation_id,
    worker_pid: workerPid,
    acquired_at_unix_ms: acquiredAt,
    request_sha256: envelope.integrity_sha256,
    claim_nonce: crypto.randomBytes(18).toString('hex')
  };
  const claim = { ...base, integrity_sha256: canonicalDigest(base) };
  try {
    writeExclusiveJsonFile(target, claim);
    return { ...claim, lock_path: target };
  } catch (error) {
    if (error?.code !== 'EEXIST') throw error;
    let existing;
    try {
      existing = validateDeferredWorkerLock(readBoundedJsonFile(target, DEFERRED_LOCK_MAX_BYTES), envelope);
    } catch (lockError) {
      throw lockError?.code
        ? lockError
        : activationCommandError('DEFERRED_WORKER_LOCK_INVALID', 'Deferred worker ownership could not be verified.');
    }
    if (processAlive(existing.worker_pid, isAlive)) {
      throw activationCommandError(
        'DEFERRED_WORKER_ALREADY_RUNNING',
        'Another worker already owns this deferred activation operation.',
        { worker_pid: existing.worker_pid, acquired_at_unix_ms: existing.acquired_at_unix_ms }
      );
    }
    // Never remove or take over an existing operation lock, even when its
    // recorded owner is dead.  A read/remove/create sequence cannot prove the
    // file still belongs to the owner that was inspected and can otherwise
    // delete a concurrently refreshed live claim.  Recovery uses a fresh
    // operation_id and leaves this operation fail-closed for audit.
    throw activationCommandError(
      'DEFERRED_WORKER_ABANDONED',
      'The deferred activation worker owner exited without a terminal result; submit a fresh operation instead of replaying this one.',
      { worker_pid: existing.worker_pid, acquired_at_unix_ms: existing.acquired_at_unix_ms }
    );
  }
}

function releaseDeferredWorkerClaim(claim) {
  const target = String(claim?.lock_path || '');
  if (!target) return false;
  let current;
  try { current = readBoundedJsonFile(target, DEFERRED_LOCK_MAX_BYTES); } catch { return false; }
  if (current?.operation_id !== claim.operation_id || current?.claim_nonce !== claim.claim_nonce
    || current?.integrity_sha256 !== claim.integrity_sha256) return false;
  try { fs.rmSync(target, { force: true }); return true; } catch { return false; }
}

function writeDeferredResult(paths, operationId, result) {
  const id = assertDeferredOperationId(operationId);
  const target = deferredResultPath(paths, id);
  // Terminal results are immutable.  A duplicate worker/retry observes the
  // first verified result instead of replacing success with a late failure (or
  // vice versa).
  if (readDeferredResult(paths, id)) return target;
  const lockPath = deferredResultLockPath(paths, id);
  const lock = {
    schema_version: DEFERRED_SCHEMA_VERSION,
    kind: `${DEFERRED_KIND}_result_lock`,
    operation_id: id,
    writer_pid: process.pid,
    nonce: crypto.randomBytes(18).toString('hex')
  };
  try {
    writeExclusiveJsonFile(lockPath, lock);
  } catch (error) {
    if (error?.code === 'EEXIST' && readDeferredResult(paths, id)) return target;
    throw activationCommandError('DEFERRED_RESULT_WRITE_BUSY', 'Deferred activation result is already being finalized.');
  }
  try {
    if (readDeferredResult(paths, id)) return target;
    const base = {
      schema_version: DEFERRED_SCHEMA_VERSION,
      kind: `${DEFERRED_KIND}_result`,
      operation_id: id,
      completed_at_unix_ms: Date.now(),
      state: String(result?.state || 'failed'),
      ...(result?.result !== undefined ? { result: boundedJsonValue(result.result) } : {}),
      ...(result?.error !== undefined ? { error: boundedJsonValue(result.error) } : {})
    };
    const payload = { ...base, integrity_sha256: canonicalDigest(base) };
    writeJsonAtomic(target, boundedJsonValue(payload));
    if (!readDeferredResult(paths, id)) {
      throw activationCommandError('DEFERRED_RESULT_INTEGRITY_FAILED', 'Deferred activation result did not persist with valid integrity.');
    }
    return target;
  } finally {
    try { fs.rmSync(lockPath, { force: true }); } catch { /* a terminal result remains authoritative */ }
  }
}

function readDeferredResult(paths, operationId) {
  const id = assertDeferredOperationId(operationId);
  const target = deferredResultPath(paths, id);
  if (!fs.existsSync(target)) return null;
  try {
    const stat = fs.statSync(target);
    if (!stat.isFile() || stat.size > DEFERRED_RESULT_MAX_BYTES) return null;
    const raw = JSON.parse(fs.readFileSync(target, 'utf8'));
    if (!raw || raw.schema_version !== DEFERRED_SCHEMA_VERSION
      || raw.kind !== `${DEFERRED_KIND}_result` || raw.operation_id !== id
      || !['completed', 'failed', 'expired'].includes(String(raw.state || ''))
      || typeof raw.integrity_sha256 !== 'string' || !HEX64.test(raw.integrity_sha256)
      || raw.integrity_sha256 !== canonicalDigest(deferredResultPayload(raw))) return null;
    return raw;
  } catch {
    return null;
  }
}

function readDeferredStatus(paths, operationId, now = Date.now()) {
  const id = assertDeferredOperationId(operationId);
  const terminal = readDeferredResult(paths, id);
  if (terminal) return terminal;
  const requestPath = deferredRequestPath(paths, id);
  if (!fs.existsSync(requestPath)) return null;
  const envelope = readDeferredEnvelope(paths, requestPath);
  const marker = readJson(envelope.parent_marker, null);
  if (marker && (marker.operation_id !== id || marker.nonce !== envelope.parent_marker_nonce
    || Number(marker.pid) !== envelope.parent_pid)) {
    throw activationCommandError('DEFERRED_PARENT_MARKER_INVALID', 'Deferred activation parent marker does not match pending status.');
  }
  let worker = null;
  const workerLock = deferredWorkerLockPath(paths, id);
  if (fs.existsSync(workerLock)) {
    try {
      worker = validateDeferredWorkerLock(readBoundedJsonFile(workerLock, DEFERRED_LOCK_MAX_BYTES), envelope);
    } catch (error) {
      throw error?.code
        ? error
        : activationCommandError('DEFERRED_WORKER_LOCK_INVALID', 'Deferred worker ownership could not be verified.');
    }
  }
  const observedAt = Number(now);
  return {
    schema_version: DEFERRED_SCHEMA_VERSION,
    kind: `${DEFERRED_KIND}_status`,
    operation_id: id,
    state: 'pending',
    activation_pending: true,
    fully_ready: false,
    requested_at_unix_ms: envelope.requested_at_unix_ms,
    expires_at_unix_ms: envelope.expires_at_unix_ms,
    expired: Number.isSafeInteger(observedAt) && observedAt >= envelope.expires_at_unix_ms,
    parent_boundary_closed: !marker,
    worker_pid: worker?.worker_pid || null,
    worker_running: worker ? processAlive(worker.worker_pid) : false
  };
}

function processAlive(pid, isAlive = null) {
  if (typeof isAlive === 'function') return Boolean(isAlive(pid));
  try { process.kill(Number(pid), 0); return true; } catch { return false; }
}

async function waitForDeferredParentExit({
  parentPid,
  parentMarker,
  parentMarkerNonce,
  timeoutMs = DEFERRED_PARENT_WAIT_MAX_MS,
  pollMs = DEFERRED_PARENT_POLL_MS,
  graceMs = DEFERRED_PARENT_GRACE_MS,
  waitFn = (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
  isAlive = null,
  readFile = (file) => readJson(file, null)
} = {}) {
  const deadline = Date.now() + Math.min(DEFERRED_PARENT_WAIT_MAX_MS, Math.max(0, Number(timeoutMs) || 0));
  while (Date.now() < deadline) {
    const alive = processAlive(parentPid, isAlive);
    const marker = parentMarker ? readFile(parentMarker) : null;
    const markerPresent = Boolean(marker);
    const markerMatches = !markerPresent || !parentMarkerNonce || marker?.nonce === parentMarkerNonce;
    if (!markerMatches) {
      throw activationCommandError('DEFERRED_PARENT_MARKER_INVALID', 'Deferred activation parent marker changed unexpectedly.');
    }
    if (!alive && !markerPresent) {
      if (graceMs > 0) await waitFn(Math.min(Number(graceMs), 2000));
      return true;
    }
    await waitFn(Math.max(10, Math.min(Number(pollMs) || DEFERRED_PARENT_POLL_MS, 1000)));
  }
  throw activationCommandError(
    'DEFERRED_PARENT_EXIT_TIMEOUT',
    'The originating Coding-VP command did not release its active call before the deferred activation expired.'
  );
}

function parseArgs(argv = []) {
  const values = new Set(argv.map((item) => String(item || '')));
  const execute = values.has('--execute');
  const statusOnly = values.has('--status');
  const preflightOnly = values.has('--preflight') || !execute;
  if (execute && statusOnly) {
    throw activationCommandError('ACTIVATION_COMMAND_ARGUMENT_INVALID', '--execute and --status cannot be combined.');
  }
  if (argv.some((item) => !['--execute', '--preflight', '--status'].includes(String(item || '')))) {
    throw activationCommandError(
      'ACTIVATION_COMMAND_ARGUMENT_INVALID',
      'Usage: node scripts/full-clean-activation.js [--status|--preflight|--execute]'
    );
  }
  return { execute, preflightOnly, statusOnly };
}

function expectedComponentRevision(snapshot, status, component = 'recovery_host') {
  const candidates = [
    snapshot?.recoveryHost?.code_revision,
    snapshot?.recovery_host?.code_revision,
    status?.code_revision,
    status?.codeRevision?.[component],
    snapshot?.codeRevision?.[component]
  ];
  for (const candidate of candidates) {
    const revision = String(candidate?.disk_revision || '').toLowerCase();
    if (HEX64.test(revision)) return revision;
  }
  throw activationCommandError(
    'REVISION_UNAVAILABLE',
    `The ${component} disk revision is unavailable from the authenticated Recovery Host.`
  );
}

function createCommandContext(options = {}) {
  const paths = options.paths || createDevelopmentPaths(options);
  const expectedIdentity = paths.runtimeIdentity();
  const descriptor = loadRecoveryDescriptor(paths);
  if (!descriptorMatchesInstallation(descriptor, expectedIdentity)) {
    throw activationCommandError(
      'RECOVERY_HOST_INSTALLATION_MISMATCH',
      'The authenticated Recovery Host belongs to another checkout or installation.'
    );
  }
  return {
    paths,
    descriptor,
    client: new RecoveryIpcClient({ paths }),
    requestOptions: descriptorRequestOptions(descriptor)
  };
}

async function readAuthority(context, options = {}) {
  const status = await context.client.status(context.requestOptions);
  let snapshot = null;
  try {
    snapshot = await context.client.call(
      'runtime.snapshot',
      [{ force: true, reason: 'full-clean-activation-command-preflight' }],
      context.requestOptions
    );
  } catch (error) {
    // Capability/revision status is sufficient to decide that a stale host
    // must be bootstrapped.  A current host still requires its authenticated
    // runtime snapshot before receiving an activation request.
    snapshot = { snapshot_error_code: String(error?.code || 'RUNTIME_SNAPSHOT_UNAVAILABLE') };
  }
  const workspace = String(snapshot?.workspace || context.paths.appRoot?.() || '').trim();
  const component = 'recovery_host';
  const revisionHasher = options.hashComponentRevisionFn || hashComponentRevision;
  const expectedDiskRevision = String(
    revisionHasher(context.paths.appRoot(), component)?.revision || ''
  ).trim().toLowerCase();
  if (!HEX64.test(expectedDiskRevision)) {
    throw activationCommandError('REVISION_UNAVAILABLE', 'Current-checkout Recovery Host revision could not be computed locally.');
  }
  const freshnessAssessor = options.assessRecoveryHostFreshnessFn || assessRecoveryHostFreshness;
  const freshness = freshnessAssessor({
    paths: context.paths,
    descriptor: context.descriptor,
    status,
    expectedDiskRevision
  });
  if (freshness?.current === true && snapshot?.snapshot_error_code) {
    throw activationCommandError(
      'RUNTIME_SNAPSHOT_UNAVAILABLE',
      'Current Recovery Host did not provide the authenticated runtime snapshot required for activation.',
      { error_code: snapshot.snapshot_error_code }
    );
  }
  return { status, snapshot, workspace, component, expectedDiskRevision, freshness };
}

function buildRequest(authority, checkpoint, now = Date.now(), options = {}) {
  const requestedAt = Number.isSafeInteger(Number(now)) ? Number(now) : Date.now();
  const suppliedOperationId = String(options?.operationId || '').trim();
  const operation_id = suppliedOperationId || `full-clean-cli-${requestedAt.toString(36)}-${crypto.randomBytes(12).toString('hex')}`;
  if (!DEFERRED_OPERATION_ID.test(operation_id)) {
    throw activationCommandError('ACTIVATION_OPERATION_ID_INVALID', 'The activation operation_id is invalid.');
  }
  const suppliedExpiryInput = options?.expiresAtUnixMs;
  const hasSuppliedExpiry = suppliedExpiryInput !== undefined
    && suppliedExpiryInput !== null
    && String(suppliedExpiryInput).trim() !== '';
  const suppliedExpiry = Number(suppliedExpiryInput);
  const defaultExpiry = requestedAt + DEFAULT_TTL_MS;
  if (hasSuppliedExpiry && (!Number.isSafeInteger(suppliedExpiry)
    || suppliedExpiry <= requestedAt || suppliedExpiry > defaultExpiry)) {
    throw activationCommandError(
      'ACTIVATION_REQUEST_INVALID',
      `The authenticated activation request expiry must be within ${DEFAULT_TTL_MS}ms of its request timestamp.`
    );
  }
  const expiresAt = hasSuppliedExpiry ? suppliedExpiry : defaultExpiry;
  return {
    operation_id,
    component: authority.component,
    // These markers are part of the fail-closed command contract.  A stale or
    // legacy Recovery Host must reject the request instead of interpreting it
    // as the historical component-scoped activation path.
    full_clean_required: true,
    activation_mode: 'full_clean_activation',
    requested_at_unix_ms: requestedAt,
    expires_at_unix_ms: expiresAt,
    expected_disk_revision: authority.expectedDiskRevision,
    allow_acceptance_pending: true,
    source_checkpoint: checkpoint
  };
}

function buildDeferredEnvelope({
  paths,
  checkpoint,
  operationId,
  requestedAtUnixMs = Date.now(),
  expiresAtUnixMs,
  parentPid = process.pid,
  parentMarker,
  parentMarkerNonce
} = {}) {
  if (!paths || typeof paths.dataRoot !== 'function' || typeof paths.appRoot !== 'function'
    || typeof paths.runtimeIdentity !== 'function') {
    throw activationCommandError('DEFERRED_DATA_ROOT_UNAVAILABLE', 'Runtime paths are incomplete for deferred activation.');
  }
  const id = assertDeferredOperationId(operationId || deferredOperationId(requestedAtUnixMs));
  const requestedAt = Number(requestedAtUnixMs);
  const expiresAt = Number(expiresAtUnixMs || requestedAt + DEFERRED_DEFAULT_TTL_MS);
  const pid = Number(parentPid);
  if (!Number.isSafeInteger(requestedAt) || !Number.isSafeInteger(expiresAt)
    || expiresAt <= requestedAt || expiresAt - requestedAt > DEFERRED_MAX_TTL_MS
    || !Number.isSafeInteger(pid) || pid <= 0) {
    throw activationCommandError('DEFERRED_REQUEST_INVALID', 'Deferred activation request timing or parent PID is invalid.');
  }
  const canonicalCheckpoint = parseCheckpoint(JSON.stringify(checkpoint));
  const identity = paths.runtimeIdentity();
  const installationId = String(identity?.installation_id || '').toLowerCase();
  const runtimeMode = String(identity?.mode || '').trim();
  if (!HEX64.test(installationId) || !['development', 'packaged'].includes(runtimeMode)) {
    throw activationCommandError('RECOVERY_HOST_INSTALLATION_MISMATCH', 'Runtime installation identity is unavailable for deferred activation.');
  }
  const marker = parentMarker || deferredParentMarkerPath(paths, id);
  const markerNonce = String(parentMarkerNonce || crypto.randomBytes(18).toString('hex'));
  const envelope = {
    schema_version: DEFERRED_SCHEMA_VERSION,
    kind: DEFERRED_KIND,
    operation_id: id,
    requested_at_unix_ms: requestedAt,
    expires_at_unix_ms: expiresAt,
    parent_pid: pid,
    parent_marker: path.resolve(marker),
    source_checkpoint: canonicalCheckpoint,
    installation_id: installationId,
    runtime_mode: runtimeMode,
    app_root: path.resolve(paths.appRoot()),
    parent_marker_nonce: markerNonce
  };
  // Bind the marker nonce to the digest and validate it in the worker.  Older
  // envelopes without this boundary identity are rejected rather than guessed.
  envelope.integrity_sha256 = canonicalDigest(envelope);
  return envelope;
}

function writeDeferredRequest(paths, envelope, { writeJson = writeJsonAtomic } = {}) {
  const id = assertDeferredOperationId(envelope?.operation_id);
  const target = deferredRequestPath(paths, id);
  if (fs.existsSync(target)) {
    throw activationCommandError('DEFERRED_REQUEST_EXISTS', 'A deferred activation request with this operation_id already exists.');
  }
  const marker = deferredParentMarkerPath(paths, id);
  if (path.resolve(String(envelope.parent_marker || '')) !== path.resolve(marker)) {
    throw activationCommandError('DEFERRED_REQUEST_INVALID', 'Deferred activation parent marker is not canonical.');
  }
  // A marker without a request is an incomplete prior handoff.  Do not
  // overwrite it: doing so could let two parent calls claim the same
  // operation boundary.  The caller must use a fresh operation_id or inspect
  // the existing durable evidence.
  if (fs.existsSync(marker)) {
    throw activationCommandError('DEFERRED_REQUEST_EXISTS', 'A deferred activation parent marker with this operation_id already exists.');
  }
  // The marker is written before the request so a worker can never observe a
  // request without a matching parent-boundary sentinel.
  let markerCreated = false;
  try {
    writeJson(marker, {
      schema_version: DEFERRED_SCHEMA_VERSION,
      kind: `${DEFERRED_KIND}_parent`,
      operation_id: id,
      pid: Number(envelope.parent_pid),
      nonce: String(envelope.parent_marker_nonce || '')
    });
    markerCreated = true;
    writeJson(target, envelope);
  } catch (error) {
    // If request persistence fails, remove only the marker created by this
    // attempt.  Leaving a dangling marker would strand a detached worker and
    // make the operation look active forever; removing an older marker would
    // be unsafe, hence the existence check above and the local flag.
    if (markerCreated) {
      try { fs.rmSync(marker, { force: true }); } catch { /* preserve original error */ }
    }
    throw error;
  }
  return { requestPath: target, markerPath: marker };
}

function removeDeferredParentMarker(markerPath) {
  try { fs.rmSync(markerPath, { force: true }); } catch { /* best effort during process exit */ }
}

function deferredWorkerEnvironment(source = process.env) {
  const next = { ...source };
  // The worker authenticates through the Recovery Host descriptor and needs
  // only ordinary process/runtime variables.  Do not carry ambient bearer
  // tokens, provider keys, cookies, or loader injection into the detached
  // process; the checkpoint is passed through its authenticated envelope.
  for (const key of Object.keys(next)) {
    if (/^(OPENAI_API_KEY|ANTHROPIC_API_KEY|AZURE_OPENAI_API_KEY|.*(?:AUTHORIZATION|ACCESS_TOKEN|BEARER_TOKEN|PASSWORD|PASSWD|COOKIE|PRIVATE_KEY|SECRET_KEY|API_KEY|AUTH_TOKEN|MCP_AUTH_TOKEN|P5_A0_SEED).*)$/i.test(key)) {
      delete next[key];
    }
  }
  delete next.NODE_OPTIONS;
  delete next.NODE_EXTRA_CA_CERTS;
  delete next.FULL_CLEAN_SOURCE_CHECKPOINT_JSON;
  next.FULL_CLEAN_DEFERRED_WORKER = '1';
  return next;
}

function spawnDeferredWorker(requestPath, {
  spawnProcess = spawn,
  cwd = process.cwd(),
  env = process.env,
  waitForSpawn = true
} = {}) {
  const workerEnv = deferredWorkerEnvironment(env);
  return new Promise((resolve, reject) => {
    let child;
    try {
      child = spawnProcess(process.execPath, [__filename, '--deferred-worker', requestPath], {
        cwd,
        detached: true,
        windowsHide: true,
        stdio: 'ignore',
        env: workerEnv
      });
    } catch (error) {
      reject(error);
      return;
    }
    const finish = (error = null) => {
      if (error) reject(error);
      else {
        try { child?.unref?.(); } catch { /* no-op */ }
        resolve({ pid: Number(child?.pid || 0) || null });
      }
    };
    if (!child || !Number.isSafeInteger(Number(child.pid)) || Number(child.pid) <= 0) {
      finish(activationCommandError('DEFERRED_WORKER_START_FAILED', 'The detached activation worker did not provide a valid process identity.'));
      return;
    }
    if (!waitForSpawn || typeof child.once !== 'function') {
      finish();
      return;
    }
    let settled = false;
    child.once('error', (error) => {
      if (settled) return;
      settled = true;
      reject(error);
    });
    child.once('spawn', () => {
      if (settled) return;
      settled = true;
      finish();
    });
  });
}

async function deferExecute({
  paths,
  checkpoint,
  env = process.env,
  now = Date.now(),
  // Keep direct callers on the same durable queue budget as the public
  // command. The authenticated wire request is still capped separately by
  // DEFERRED_ACTIVATION_TTL_MS when the worker crosses the post-tool boundary.
  timeoutMs = DEFERRED_DEFAULT_TTL_MS,
  parentPid = process.pid,
  spawnProcess = spawn
} = {}) {
  const context = createCommandContext({ paths });
  const requestedAt = Number.isSafeInteger(Number(now)) ? Number(now) : Date.now();
  const operationId = deferredOperationId(requestedAt);
  const maxTimeout = Math.min(DEFERRED_MAX_TTL_MS, Math.max(1000, Number(timeoutMs) || DEFERRED_DEFAULT_TTL_MS));
  const expiresAt = requestedAt + maxTimeout;
  const envelope = buildDeferredEnvelope({
    paths: context.paths,
    checkpoint,
    operationId,
    requestedAtUnixMs: requestedAt,
    expiresAtUnixMs: expiresAt,
    parentPid
  });
  const files = writeDeferredRequest(context.paths, envelope);
  const cleanupMarker = () => removeDeferredParentMarker(files.markerPath);
  process.once('exit', cleanupMarker);
  let worker;
  try {
    worker = await spawnDeferredWorker(files.requestPath, {
      spawnProcess,
      cwd: context.paths.appRoot(),
      env
    });
  } catch (error) {
    process.removeListener('exit', cleanupMarker);
    cleanupMarker();
    const serialized = serializeActivationError(Object.assign(error, {
      code: error?.code || 'DEFERRED_WORKER_START_FAILED'
    }));
    writeDeferredResult(context.paths, operationId, { state: 'failed', error: serialized });
    throw activationCommandError('DEFERRED_WORKER_START_FAILED', 'The detached activation worker could not be started.', serialized);
  }
  return {
    ok: true,
    mode: 'deferred',
    activation_pending: true,
    fully_ready: false,
    operation_id: operationId,
    requested_at_unix_ms: requestedAt,
    expires_at_unix_ms: expiresAt,
    worker_pid: worker?.pid || null,
    request_path: files.requestPath,
    request_sha256: envelope.integrity_sha256,
    result_path: deferredResultPath(context.paths, operationId),
    handoff: 'post_tool_call'
  };
}

function summarizeAuthority(authority) {
  const status = authority.status || {};
  const epoch = status.activation_epoch || status.activationEpoch || null;
  const observedRevision = authority.freshness?.capability || status.full_clean_activation || status.code_revision || {};
  return {
    workspace: authority.workspace || null,
    component: authority.component,
    revision_source: 'current_checkout_local_hash',
    expected_disk_revision: authority.expectedDiskRevision,
    recovery_host: {
      pid: Number(status.pid || 0) || null,
      instance_id: String(status.instance_id || '') || null,
      device_id: String(status.device_id || '') || null,
      device_instance_id: String(status.device_instance_id || '') || null,
      current_for_full_clean: authority.freshness?.current === true,
      full_clean_capability_available: authority.freshness?.capability?.available === true,
      observed_running_revision: String(observedRevision?.running_revision || '') || null,
      observed_disk_revision: String(observedRevision?.disk_revision || '') || null,
      activation_epoch_id: String(epoch?.activation_epoch_id || '') || null,
      state: String(epoch?.state || '') || null,
      admission_open: epoch?.admission_open === true
    }
  };
}

function activationEpochProjection(value) {
  if (!value || typeof value !== 'object') return {};
  return value.activation_epoch
    || value.activationEpoch
    || value.status?.activation_epoch
    || value.status?.activationEpoch
    || {};
}

function activationEpochState(epoch) {
  return String(epoch?.epoch_state || epoch?.state || '').trim().toUpperCase();
}

function observedActivationOperationId(status) {
  const epoch = activationEpochProjection(status);
  return String(
    epoch?.operation_id
    || epoch?.operationId
    || status?.recovery_bootstrap?.operation_id
    || status?.recoveryBootstrap?.operationId
    || ''
  ).trim() || null;
}

function assertReplacementDescriptor(paths, descriptor, initialDescriptor) {
  if (!descriptor || (String(descriptor.instance_id || '') === String(initialDescriptor?.instance_id || '')
    && Number(descriptor.owner_pid || 0) === Number(initialDescriptor?.owner_pid || 0))) return false;
  const expectedIdentity = typeof paths?.runtimeIdentity === 'function' ? paths.runtimeIdentity() : null;
  if (!expectedIdentity || !descriptorMatchesInstallation(descriptor, expectedIdentity)) {
    throw activationCommandError(
      'RECOVERY_HOST_INSTALLATION_MISMATCH',
      'Replacement Recovery Host belongs to another checkout or runtime installation.'
    );
  }
  return true;
}

function connectorAcknowledgementEligible(snapshot, descriptor, activationEpochId, notBeforeUnixMs = 0) {
  const runtime = snapshot?.status && typeof snapshot.status === 'object' ? snapshot.status : snapshot;
  const epoch = activationEpochProjection(snapshot);
  const expectedEpoch = String(activationEpochId || '').trim();
  const descriptorEpoch = String(descriptor?.activation_epoch_id || '').trim();
  const snapshotEpoch = String(epoch?.activation_epoch_id || epoch?.activationEpochId || '').trim();
  const observedAt = String(runtime?.connectorRediscoveredAt || runtime?.connector_rediscovered_at || '').trim();
  const observedAtUnixMs = Date.parse(observedAt);
  const descriptorStartedAtUnixMs = Date.parse(String(descriptor?.started_at || ''));
  const suppliedBoundary = Number(notBeforeUnixMs || 0);
  const freshnessBoundary = Math.max(
    Number.isSafeInteger(suppliedBoundary) ? suppliedBoundary : 0,
    Number.isFinite(descriptorStartedAtUnixMs) ? descriptorStartedAtUnixMs : Number.POSITIVE_INFINITY
  );
  const currentSha256 = String(runtime?.toolContract?.sha256 || runtime?.tool_contract?.sha256 || '').trim().toLowerCase();
  return Boolean(
    expectedEpoch
    && descriptorEpoch === expectedEpoch
    && snapshotEpoch === expectedEpoch
    && runtime?.connectorRediscovered === true
    && runtime?.connectorRefreshRequired === false
    && runtime?.connectorAcknowledgementPending === true
    && String(runtime?.connectorContractState || '') === 'CHANGED_DISCOVERED_NEEDS_ACK'
    && HEX64.test(currentSha256)
    && Number.isFinite(observedAtUnixMs)
    && observedAtUnixMs >= freshnessBoundary
  );
}

function isActivationResponseLoss(error) {
  const code = String(error?.code || '').trim().toUpperCase();
  return ACTIVATION_RESPONSE_LOSS_CODES.has(code);
}

function terminalReplacementError(error) {
  return new Set([
    'ACTIVATION_OPERATION_MISMATCH',
    'RECOVERY_HOST_INSTALLATION_MISMATCH',
    'UPDATE_INCOMPLETE'
  ]).has(String(error?.code || ''));
}

async function waitForReplacementOperation(paths, initialDescriptor, operationId, timeoutMs = DEFAULT_TIMEOUT_MS, options = {}) {
  const expectedOperationId = String(operationId || '').trim();
  const now = typeof options.now === 'function' ? options.now : () => Date.now();
  const waitFn = typeof options.waitFn === 'function'
    ? options.waitFn : (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const loadDescriptor = options.loadDescriptor || loadRecoveryDescriptor;
  const clientFactory = options.clientFactory || ((runtimePaths) => new RecoveryIpcClient({ paths: runtimePaths }));
  const deadline = Number(now()) + Math.max(1, Number(timeoutMs) || DEFAULT_TIMEOUT_MS);
  let last = null;
  while (Number(now()) < deadline) {
    try {
      const bootstrapResultReader = options.readBootstrapResultFn || readBootstrapResult;
      const bootstrapResult = bootstrapResultReader(paths, expectedOperationId);
      if (bootstrapResult && ['failed', 'expired'].includes(String(bootstrapResult.state || '').toLowerCase())) {
        throw activationCommandError('UPDATE_INCOMPLETE', 'Recovery Host bootstrap reached a terminal failure.', {
          operation_id: expectedOperationId,
          bootstrap_state: bootstrapResult.state,
          error: bootstrapResult.error || null
        });
      }
      const descriptor = loadDescriptor(paths);
      if (!assertReplacementDescriptor(paths, descriptor, initialDescriptor)) {
        await waitFn(POLL_MS);
        continue;
      }
      const client = clientFactory(paths, descriptor);
      const requestOptions = descriptorRequestOptions(descriptor);
      const status = await client.status(requestOptions);
      const statusOperationId = observedActivationOperationId(status);
      if (statusOperationId && statusOperationId !== expectedOperationId) {
        throw activationCommandError(
          'ACTIVATION_OPERATION_MISMATCH',
          'Replacement Recovery Host is serving another activation operation.',
          { expected_operation_id: expectedOperationId, observed_operation_id: statusOperationId }
        );
      }
      const statusEpoch = activationEpochProjection(status);
      if (ACTIVATION_TERMINAL_STATES.has(activationEpochState(statusEpoch))) {
        throw activationCommandError('UPDATE_INCOMPLETE', 'Replacement activation reached a terminal failed epoch.', {
          operation_id: statusOperationId,
          activation_epoch_id: statusEpoch?.activation_epoch_id || null,
          error: statusEpoch?.error || null
        });
      }
      const operation = await client.call('code.activation_status', [expectedOperationId], requestOptions);
      if (String(operation?.operation_id || '') !== expectedOperationId) {
        throw activationCommandError('ACTIVATION_OPERATION_MISMATCH', 'Replacement activation status does not match the requested operation.');
      }
      const operationEpoch = operation?.activation_epoch && typeof operation.activation_epoch === 'object'
        ? operation.activation_epoch : {};
      const epochId = String(
        operation?.activation_epoch_id
        || operation?.result?.activation_epoch_id
        || operationEpoch?.activation_epoch_id
        || ''
      ).trim();
      const descriptorEpoch = String(descriptor?.activation_epoch_id || '').trim();
      const projectedEpoch = String(statusEpoch?.activation_epoch_id || '').trim();
      if ((descriptorEpoch && epochId && descriptorEpoch !== epochId)
        || (projectedEpoch && epochId && projectedEpoch !== epochId)) {
        throw activationCommandError('ACTIVATION_OPERATION_MISMATCH', 'Replacement activation epoch does not match the durable operation.');
      }
      if (['failed', 'refused'].includes(String(operation?.state || '').toLowerCase())
        || ['failed', 'refused'].includes(String(operation?.result?.state || '').toLowerCase())
        || ACTIVATION_TERMINAL_STATES.has(activationEpochState(operationEpoch))) {
        throw activationCommandError(
          'UPDATE_INCOMPLETE',
          'Replacement activation operation reached a terminal failure.',
          {
            operation,
            activation_epoch_id: epochId || null,
            error_code: String(operation?.error?.code || operationEpoch?.error?.code || 'UPDATE_INCOMPLETE')
          }
        );
      }
      last = { descriptor, status, operation };
      if (epochId && descriptorEpoch === epochId && statusOperationId === expectedOperationId) {
        return { ...last, activationEpochId: epochId };
      }
    } catch (error) {
      if (terminalReplacementError(error)) throw error;
      last = { ...(last || {}), error: serializeActivationError(error) };
    }
    await waitFn(POLL_MS);
  }
  throw activationCommandError(
    'ACTIVATION_HANDOFF_RECOVERY_TIMEOUT',
    'The replacement Recovery Host did not expose the exact durable activation operation before timeout.',
    { operation_id: expectedOperationId, last: boundedJsonValue(last) }
  );
}

async function waitForReplacementReady(paths, initialDescriptor, activationEpochId, timeoutMs = DEFAULT_TIMEOUT_MS, options = {}) {
  const now = typeof options.now === 'function' ? options.now : () => Date.now();
  const waitFn = typeof options.waitFn === 'function'
    ? options.waitFn : (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const loadDescriptor = options.loadDescriptor || loadRecoveryDescriptor;
  const clientFactory = options.clientFactory || ((runtimePaths) => new RecoveryIpcClient({ paths: runtimePaths }));
  const deadline = Number(now()) + Math.max(1, Number(timeoutMs) || DEFAULT_TIMEOUT_MS);
  const expectedOperationId = String(options.operationId || '').trim();
  const notBeforeUnixMs = Number(options.notBeforeUnixMs || 0);
  let connectorAckAttempted = false;
  let last = null;
  while (Number(now()) < deadline) {
    try {
      const descriptor = loadDescriptor(paths);
      if (!assertReplacementDescriptor(paths, descriptor, initialDescriptor)) {
        await waitFn(POLL_MS);
        continue;
      }
      const descriptorEpoch = String(descriptor?.activation_epoch_id || '').trim();
      if (descriptorEpoch && descriptorEpoch !== activationEpochId) {
        throw activationCommandError('ACTIVATION_OPERATION_MISMATCH', 'Replacement descriptor belongs to another activation epoch.');
      }
      const client = clientFactory(paths, descriptor);
      const requestOptions = descriptorRequestOptions(descriptor);
      const status = await client.status(requestOptions);
      const epoch = activationEpochProjection(status);
      const statusOperationId = observedActivationOperationId(status);
      if (expectedOperationId && statusOperationId && statusOperationId !== expectedOperationId) {
        throw activationCommandError('ACTIVATION_OPERATION_MISMATCH', 'Replacement status belongs to another activation operation.');
      }
      if (ACTIVATION_TERMINAL_STATES.has(activationEpochState(epoch))) {
        throw activationCommandError('UPDATE_INCOMPLETE', 'Replacement activation reached a terminal failed epoch.', {
          operation_id: statusOperationId,
          activation_epoch_id: epoch?.activation_epoch_id || null,
          error: epoch?.error || null
        });
      }
      let runtime = null;
      if (descriptorEpoch === activationEpochId
        && String(epoch?.activation_epoch_id || '') === activationEpochId
        && (!expectedOperationId || statusOperationId === expectedOperationId)) {
        runtime = await client.call('runtime.lightweight_snapshot', [], requestOptions);
        const runtimeEpoch = activationEpochProjection(runtime);
        if (String(runtimeEpoch?.activation_epoch_id || '') !== activationEpochId) {
          throw activationCommandError('ACTIVATION_OPERATION_MISMATCH', 'Replacement runtime snapshot belongs to another activation epoch.');
        }
        if (!connectorAckAttempted
          && connectorAcknowledgementEligible(runtime, descriptor, activationEpochId, notBeforeUnixMs)) {
          // The fresh discovery projection is produced by the replacement
          // Recovery Host from the current MCP process receipt.  ACK exactly
          // once on this authenticated descriptor, then continue polling so
          // final readiness is still proven independently.
          connectorAckAttempted = true;
          await client.call('runtime.acknowledge_connector_contract', [], requestOptions);
        }
      }
      last = { descriptor, status, runtime, connector_ack_attempted: connectorAckAttempted };
      if (String(epoch?.activation_epoch_id || '') === activationEpochId
        && descriptorEpoch === activationEpochId
        && (!expectedOperationId || statusOperationId === expectedOperationId)
        && String(epoch?.state || '') === 'READY'
        && epoch?.admission_open === true
        && status?.runtime?.fully_ready === true) {
        return { ready: true, descriptor, status, runtime, connectorAckAttempted };
      }
    } catch (error) {
      if (terminalReplacementError(error)) throw error;
      last = { ...(last || {}), error: serializeActivationError(error), connector_ack_attempted: connectorAckAttempted };
      // Handoff is expected to produce a short descriptor gap. Continue polling
      // without ever weakening the identity checks above.
    }
    await waitFn(POLL_MS);
  }
  return { ready: false, last, connectorAckAttempted };
}

async function run(options = {}, env = process.env) {
  const mode = parseArgs(options.argv || []);
  const contextFactory = options.createCommandContextFn || createCommandContext;
  const context = options.context || contextFactory(options);
  const authorityReader = options.readAuthorityFn || readAuthority;
  const authority = await authorityReader(context, options);
  if (mode.statusOnly) {
    return { ok: true, mode: 'status', authority: summarizeAuthority(authority) };
  }
  const checkpoint = parseCheckpoint(env.FULL_CLEAN_SOURCE_CHECKPOINT_JSON);
  const request = buildRequest(authority, checkpoint, Number(options.now || Date.now()), {
    operationId: options.operationId,
    expiresAtUnixMs: options.expiresAtUnixMs
  });
  const timeoutBudget = Math.min(
    DEFAULT_TIMEOUT_MS,
    Math.max(1, Number(options.timeoutMs) || DEFAULT_TIMEOUT_MS)
  );
  const waitForOperation = options.waitForReplacementOperationFn || waitForReplacementOperation;
  const waitForReady = options.waitForReplacementReadyFn || waitForReplacementReady;
  const bootstrapHost = options.bootstrapCurrentRecoveryHostFn || bootstrapCurrentRecoveryHost;
  const currentHost = authority.freshness?.current === true;
  if (!currentHost && mode.preflightOnly) {
    return {
      ok: true,
      mode: 'preflight',
      request,
      preflight: {
        safe: false,
        code: 'RECOVERY_BOOTSTRAP_REQUIRED',
        bootstrap_required: true
      },
      bootstrap_required: true,
      authority: summarizeAuthority(authority)
    };
  }
  let preflight = null;
  let operation = null;
  let operationHandoff = null;
  let bootstrap = null;
  let activationResponseRecovered = false;
  let epochId = null;
  if (!currentHost) {
    const identity = context.paths.runtimeIdentity();
    const requestedAt = Number(request.requested_at_unix_ms);
    bootstrap = await bootstrapHost({
      app: options.app || {
        isPackaged: identity?.mode === 'packaged',
        getAppPath: () => context.paths.appRoot()
      },
      paths: context.paths,
      client: context.client,
      descriptor: context.descriptor,
      status: authority.status,
      operationId: request.operation_id,
      sourceCheckpoint: request.source_checkpoint,
      expectedDiskRevision: authority.expectedDiskRevision,
      requestedAtUnixMs: requestedAt,
      // The bootstrap envelope owns the coordinator/handoff window.  It is
      // intentionally not constrained by the 55s authenticated wire TTL used
      // only when the current host receives code.activate_update directly.
      expiresAtUnixMs: requestedAt + timeoutBudget,
      timeoutMs: Math.min(15_000, timeoutBudget)
    });
    operationHandoff = await waitForOperation(
      context.paths,
      context.descriptor,
      request.operation_id,
      timeoutBudget,
      options.replacementOperationOptions || {}
    );
    operation = operationHandoff.operation || null;
    epochId = String(operationHandoff.activationEpochId || '').trim() || null;
  } else {
    preflight = await context.client.call('code.activation_preflight', [request], context.requestOptions);
    if (preflight?.safe !== true) {
      throw activationCommandError(
        String(preflight?.code || 'ACTIVATION_PREFLIGHT_REFUSED'),
        'Full-clean activation preflight was refused by the Recovery Host.',
        { preflight, authority: summarizeAuthority(authority) }
      );
    }
    if (mode.preflightOnly) {
      return {
        ok: true,
        mode: 'preflight',
        request,
        preflight,
        bootstrap_required: false,
        authority: summarizeAuthority(authority)
      };
    }
    try {
      // This mutation is deliberately attempted once.  A transport failure
      // after handoff is reconciled through the exact durable operation below;
      // retrying activate_update could create a second activation transaction.
      operation = await context.client.call('code.activate_update', [request], context.requestOptions);
    } catch (error) {
      if (!isActivationResponseLoss(error)) throw error;
      activationResponseRecovered = true;
      operationHandoff = await waitForOperation(
        context.paths,
        context.descriptor,
        request.operation_id,
        timeoutBudget,
        options.replacementOperationOptions || {}
      );
      operation = operationHandoff.operation || null;
      epochId = String(operationHandoff.activationEpochId || '').trim() || null;
    }
    epochId = epochId || String(
      operation?.activation_epoch_id
      || operation?.result?.activation_epoch_id
      || operation?.activation_epoch?.activation_epoch_id
      || ''
    ).trim() || null;
    if (!epochId) {
      operationHandoff = await waitForOperation(
        context.paths,
        context.descriptor,
        request.operation_id,
        timeoutBudget,
        options.replacementOperationOptions || {}
      );
      operation = operationHandoff.operation || operation;
      epochId = String(operationHandoff.activationEpochId || '').trim() || null;
    }
  }
  if (!epochId) {
    throw activationCommandError(
      'ACTIVATION_EPOCH_UNAVAILABLE',
      'The exact activation operation did not expose an activation epoch.'
    );
  }
  const handoff = await waitForReady(
    context.paths,
    context.descriptor,
    epochId,
    timeoutBudget,
    {
      ...(options.replacementReadyOptions || {}),
      operationId: request.operation_id,
      notBeforeUnixMs: request.requested_at_unix_ms
    }
  );
  const replacementStatus = handoff.status || handoff.last?.status || null;
  const replacementDescriptor = handoff.descriptor || handoff.last?.descriptor || null;
  const replacementEpoch = replacementStatus?.activation_epoch || {};
  const fullyReady = Boolean(handoff.ready === true
    && String(replacementEpoch.activation_epoch_id || '') === epochId
    && String(replacementEpoch.state || '') === 'READY'
    && replacementEpoch.admission_open === true
    && replacementStatus?.runtime?.fully_ready === true);
  return {
    ok: true,
    mode: 'execute',
    request,
    preflight,
    operation,
    bootstrap_required: !currentHost,
    recovery_host_bootstrapped: bootstrap?.required === true,
    bootstrap: bootstrap ? {
      required: bootstrap.required === true,
      stale: bootstrap.stale === true,
      pid: Number(bootstrap.pid || 0) || null
    } : null,
    activation_response_recovered: activationResponseRecovered,
    activation_epoch_id: epochId,
    fully_ready: fullyReady,
    replacement: {
      ready: fullyReady,
      descriptor_instance_id: replacementDescriptor?.instance_id || null,
      descriptor_owner_pid: Number(replacementDescriptor?.owner_pid || 0) || null,
      state: replacementEpoch.state || null,
      admission_open: replacementEpoch.admission_open === true,
      fully_ready: replacementStatus?.runtime?.fully_ready === true,
      connector_acknowledged: handoff.connectorAckAttempted === true
    }
  };
}

function parseDeferredWorkerArgs(argv = []) {
  if (!Array.isArray(argv) || argv.length !== 2 || String(argv[0] || '') !== '--deferred-worker') return null;
  return { requestPath: String(argv[1] || '') };
}

async function runDeferredWorker(requestPath, {
  env = process.env,
  paths = null,
  waitParent = waitForDeferredParentExit,
  now = () => Date.now(),
  runActivation = run,
  claimWorker = claimDeferredWorker,
  releaseWorker = releaseDeferredWorkerClaim,
  waitRetry = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
} = {}) {
  const runtimePaths = paths || createDevelopmentPaths({});
  let envelope;
  try {
    envelope = readDeferredEnvelope(runtimePaths, requestPath);
  } catch (error) {
    // If the operation id cannot be trusted, there is deliberately no result
    // path to write.  The worker exits without contacting Recovery Host.
    return {
      ok: false,
      code: String(error?.code || 'DEFERRED_REQUEST_INVALID'),
      message: String(error?.message || error),
      details: boundedJsonValue(error?.details || {})
    };
  }
  const existing = readDeferredResult(runtimePaths, envelope.operation_id);
  if (existing && ['completed', 'failed', 'expired'].includes(String(existing.state || ''))) return existing;
  let claim;
  try {
    claim = claimWorker(runtimePaths, envelope, { now: Number(now()) });
  } catch (error) {
    // Single-flight refusal is deliberately not a terminal operation result:
    // the owning worker remains responsible for persisting the outcome.
    return {
      ok: false,
      code: String(error?.code || 'DEFERRED_WORKER_LOCK_FAILED'),
      message: String(error?.message || error),
      details: boundedJsonValue(error?.details || {})
    };
  }
  const claimedExisting = readDeferredResult(runtimePaths, envelope.operation_id);
  if (claimedExisting && ['completed', 'failed', 'expired'].includes(String(claimedExisting.state || ''))) {
    releaseWorker(claim);
    return claimedExisting;
  }
  const finish = (payload) => {
    try {
      writeDeferredResult(runtimePaths, envelope.operation_id, payload);
    } catch {
      // Result persistence is best effort after the activation outcome; never
      // turn a successful/failed activation into an unsafe retry signal.
    }
    return payload;
  };
  try {
    const remaining = Math.max(0, envelope.expires_at_unix_ms - Number(now()));
    if (remaining <= 0) {
      return finish({
        state: 'expired',
        error: { code: 'ACTIVATION_REQUEST_EXPIRED', message: 'Deferred activation request expired before the parent call ended.', details: {} }
      });
    }
    const marker = readJson(envelope.parent_marker, null);
    if (!marker || marker.operation_id !== envelope.operation_id || marker.nonce !== envelope.parent_marker_nonce
      || Number(marker.pid) !== envelope.parent_pid) {
      throw activationCommandError('DEFERRED_PARENT_MARKER_INVALID', 'Deferred activation parent marker is missing or does not match the request.');
    }
    await waitParent({
      parentPid: envelope.parent_pid,
      parentMarker: envelope.parent_marker,
      parentMarkerNonce: envelope.parent_marker_nonce,
      timeoutMs: Math.min(DEFERRED_PARENT_WAIT_MAX_MS, remaining)
    });
    if (readJson(envelope.parent_marker, null)) {
      throw activationCommandError(
        'DEFERRED_PARENT_BOUNDARY_UNCONFIRMED',
        'The originating command boundary is not durably closed; activation remains deferred.'
      );
    }
    if (Number(now()) >= envelope.expires_at_unix_ms) {
      return finish({
        state: 'expired',
        error: { code: 'ACTIVATION_REQUEST_EXPIRED', message: 'Deferred activation request expired before Recovery Host preflight.', details: {} }
      });
    }
    const activationNow = Number(now());
    const activationRemaining = Math.max(0, envelope.expires_at_unix_ms - activationNow);
    const activationTtl = Math.min(DEFERRED_ACTIVATION_TTL_MS, activationRemaining);
    if (activationTtl <= 0) {
      return finish({
        state: 'expired',
        error: { code: 'ACTIVATION_REQUEST_EXPIRED', message: 'Deferred activation request expired before an authenticated activation request could be created.', details: {} }
      });
    }
    const activationEnv = {
      ...env,
      FULL_CLEAN_SOURCE_CHECKPOINT_JSON: JSON.stringify(envelope.source_checkpoint)
    };
    const activationOptions = {
      argv: ['--execute'],
      paths: runtimePaths,
      operationId: envelope.operation_id,
      // Rebase the wire request timestamp at the post-tool boundary.  The
      // Recovery Host rejects requests older than its bounded request window;
      // the outer deferred envelope may wait longer without weakening that
      // authenticated contract.
      now: activationNow,
      expiresAtUnixMs: activationNow + activationTtl,
      timeoutMs: Math.min(DEFAULT_TIMEOUT_MS, activationRemaining)
    };
    let result;
    let preflightAttempts = 0;
    const maxPreflightAttempts = Math.ceil(activationTtl / DEFERRED_PREFLIGHT_RETRY_MS) + 1;
    for (;;) {
      try {
        result = await runActivation(activationOptions, activationEnv);
        break;
      } catch (error) {
        // The node parent/marker barrier closes before Coding-VP necessarily
        // decrements the MCP active-tool counter. Retry only the explicit
        // preflight refusal: it is before durable epoch creation or process
        // mutation. A RUNTIME_BUSY from any later stage remains terminal and
        // must never replay the activation transaction.
        const preflightBusy = String(error?.code || '') === 'RUNTIME_BUSY'
          && error?.details?.preflight?.safe === false
          && String(error?.details?.preflight?.code || '') === 'RUNTIME_BUSY';
        if (!preflightBusy) throw error;
        preflightAttempts += 1;
        const retryNow = Number(now());
        const wireDeadline = activationNow + activationTtl;
        if (preflightAttempts >= maxPreflightAttempts
          || !Number.isSafeInteger(retryNow)
          || retryNow >= wireDeadline
          || retryNow >= envelope.expires_at_unix_ms) {
          throw activationCommandError(
            'ACTIVATION_REQUEST_EXPIRED',
            'Deferred activation remained busy until its authenticated preflight window expired.',
            { operation_id: envelope.operation_id, preflight_attempts: preflightAttempts }
          );
        }
        await waitRetry(Math.min(
          DEFERRED_PREFLIGHT_RETRY_MS,
          wireDeadline - retryNow,
          envelope.expires_at_unix_ms - retryNow
        ));
      }
    }
    const ready = Boolean(result?.ok === true
      && result?.fully_ready === true
      && result?.replacement?.ready === true
      && result?.replacement?.state === 'READY'
      && result?.replacement?.admission_open === true
      && result?.replacement?.fully_ready === true);
    if (!ready) {
      return finish({
        state: 'failed',
        error: {
          code: 'UPDATE_INCOMPLETE',
          message: 'Full-clean activation did not prove READY, open admission, and fully_ready on the replacement runtime.',
          details: boundedJsonValue({
            activation_epoch_id: result?.activation_epoch_id || null,
            replacement: result?.replacement || null,
            operation_state: result?.operation?.state || result?.operation?.result?.state || null
          })
        }
      });
    }
    return finish({ state: 'completed', result });
  } catch (error) {
    return finish({ state: 'failed', error: serializeActivationError(error) });
  } finally {
    try { releaseWorker(claim); } catch { /* terminal result remains authoritative */ }
  }
}

async function readStdinJson(stdin = process.stdin) {
  if (!stdin || stdin.isTTY === true) return '';
  const chunks = [];
  for await (const chunk of stdin) chunks.push(Buffer.from(chunk));
  return Buffer.concat(chunks).toString('utf8').trim();
}

async function main(argv = process.argv.slice(2), env = process.env, stdin = process.stdin) {
  try {
    const workerArgs = parseDeferredWorkerArgs(argv);
    if (workerArgs) {
      const result = await runDeferredWorker(workerArgs.requestPath, { env });
      // Detached workers inherit ignored stdio.  Printing is useful only when
      // an operator invokes the internal worker explicitly for diagnostics.
      if (String(env.FULL_CLEAN_DEFERRED_WORKER || '') !== '1') {
        process.stdout.write(`${JSON.stringify(result)}\n`);
      }
      if (result?.ok === false || result?.state === 'failed' || result?.state === 'expired') process.exitCode = 1;
      return result;
    }
    const parsed = parseArgs(argv);
    let effectiveEnv = env;
    if (!parsed.statusOnly && !String(env.FULL_CLEAN_SOURCE_CHECKPOINT_JSON || '').trim()) {
      const supplied = await readStdinJson(stdin);
      if (supplied) effectiveEnv = { ...env, FULL_CLEAN_SOURCE_CHECKPOINT_JSON: supplied };
    }
    if (parsed.execute) {
      const checkpoint = parseCheckpoint(effectiveEnv.FULL_CLEAN_SOURCE_CHECKPOINT_JSON);
      const result = await deferExecute({
        checkpoint,
        env: effectiveEnv,
        timeoutMs: Number(effectiveEnv.FULL_CLEAN_ACTIVATION_TIMEOUT_MS || DEFERRED_DEFAULT_TTL_MS)
      });
      process.stdout.write(`${JSON.stringify(result)}\n`);
      return result;
    }
    if (parsed.statusOnly && String(effectiveEnv.FULL_CLEAN_ACTIVATION_OPERATION_ID || '').trim()) {
      const paths = createDevelopmentPaths({});
      const operationId = assertDeferredOperationId(effectiveEnv.FULL_CLEAN_ACTIVATION_OPERATION_ID);
      const deferred = readDeferredStatus(paths, operationId);
      if (deferred) {
        const result = { ok: true, mode: 'deferred-status', operation_id: operationId, deferred };
        process.stdout.write(`${JSON.stringify(result)}\n`);
        return result;
      }
      throw activationCommandError(
        'DEFERRED_OPERATION_NOT_FOUND',
        'No deferred full-clean activation request or result exists for this operation_id.'
      );
    }
    const result = await run({ argv, timeoutMs: Number(effectiveEnv.FULL_CLEAN_ACTIVATION_TIMEOUT_MS || DEFAULT_TIMEOUT_MS) }, effectiveEnv);
    process.stdout.write(`${JSON.stringify(result)}\n`);
    return result;
  } catch (error) {
    const result = {
      ok: false,
      code: String(error?.code || 'FULL_CLEAN_ACTIVATION_COMMAND_FAILED'),
      message: String(error?.message || error),
      details: error?.details || {}
    };
    process.stdout.write(`${JSON.stringify(result)}\n`);
    process.exitCode = 1;
    return result;
  }
}

if (require.main === module) void main();

module.exports = {
  CHECKPOINT_FIELDS,
  DEFERRED_SCHEMA_VERSION,
  DEFERRED_KIND,
  DEFERRED_LOCK_KIND,
  DEFERRED_PARENT_POLL_MS,
  DEFERRED_PARENT_GRACE_MS,
  DEFERRED_DEFAULT_TTL_MS,
  DEFERRED_MAX_TTL_MS,
  DEFERRED_ACTIVATION_TTL_MS,
  DEFERRED_PARENT_WAIT_MAX_MS,
  DEFERRED_PREFLIGHT_RETRY_MS,
  parseCheckpoint,
  deferredOperationId,
  assertDeferredOperationId,
  deferredDirectory,
  deferredRequestPath,
  deferredResultPath,
  deferredParentMarkerPath,
  deferredWorkerLockPath,
  deferredResultLockPath,
  canonicalDigest,
  buildDeferredEnvelope,
  validateDeferredEnvelope,
  readDeferredEnvelope,
  writeDeferredRequest,
  writeDeferredResult,
  readDeferredResult,
  readDeferredStatus,
  claimDeferredWorker,
  releaseDeferredWorkerClaim,
  waitForDeferredParentExit,
  deferredWorkerEnvironment,
  spawnDeferredWorker,
  deferExecute,
  parseDeferredWorkerArgs,
  runDeferredWorker,
  parseArgs,
  expectedComponentRevision,
  buildRequest,
  summarizeAuthority,
  createCommandContext,
  readAuthority,
  connectorAcknowledgementEligible,
  isActivationResponseLoss,
  waitForReplacementOperation,
  waitForReplacementReady,
  readStdinJson,
  main,
  run
};
