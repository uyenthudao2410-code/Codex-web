const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { execFile } = require('node:child_process');
const { promisify, TextDecoder } = require('node:util');
const { DatabaseSync } = require('node:sqlite');
const { readJson, writeJsonAtomic } = require('./jsonStore');
const {
  COMPONENT_ORDER,
  RECOVERY_HOST_LEGACY_V1_CONTRACT,
  componentOwnsPath,
  componentOwners
} = require('./componentRevision');
const {
  lifecycleDecisionIsClean,
  normalizeActivationPostflight,
  normalizeLifecycleDecision,
  postflightRevisionVerified: importedPostflightRevisionVerified,
  postflightMatchesIntent: verifyPostflightMatchesIntent,
  verifyActivationPostflight
} = require('./activationPostflight');

const execFileAsync = promisify(execFile);

const STORE_VERSION = 2;
const MAX_ACTIONS = 64;
const MAX_OPERATION_AGE_MS = 24 * 60 * 60 * 1000;
const OPERATION_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/;
const AUTO_ACTIVATION_INTERVAL_MS = 3000;
const ACTIVATION_REQUEST_TTL_MS = 45000;
const MAX_GIT_OUTPUT_BYTES = 1024 * 1024;
const MAX_DIRTY_ENTRIES = 2000;
const MAX_AUTO_INTENTS = 96;
const MAX_AUTO_ATTEMPTS = 5;
const MAX_ACCEPTED_CHECKPOINTS = 256;
const MAX_PROCESSED_CHECKPOINTS = 512;
const MAX_TRUST_RECEIPTS = 256;
const MAX_TRUST_RECEIPT_FILE_BYTES = 16 * 1024 * 1024;
const MAX_TRUST_RECEIPT_TOTAL_BYTES = 64 * 1024 * 1024;
const RETRYABLE_REFUSALS = new Set(['RUNTIME_BUSY', 'ORCHESTRATION_STATE_UNCERTAIN', 'ACCEPTANCE_PENDING', 'ACTIVATION_REQUEST_EXPIRED', 'ACTIVATION_CONFLICT']);
const TERMINAL_INTENT_STATES = new Set(['completed', 'blocked', 'failed', 'superseded']);
const HEX64 = /^[a-f0-9]{64}$/;
const GIT_OBJECT_ID = /^[a-f0-9]{40,64}$/;
const CHECKPOINT_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{7,127}$/;
const ACCEPTED_FILE_SCHEMA_VERSION = 2;
const CLOSURE_INPUT_SCHEMA_VERSION = 1;
const ACCEPTED_RECEIPT_KINDS = new Set(['explicit_existing_file', 'task_modified_file', 'durable_wave_patch_surface']);
const ACCEPTED_RECEIPT_SOURCES = new Set(['explicit_acceptance_attestations', 'task_modified_files', 'durable_wave_patch_surface']);
const ALLOWED_MULTI_OWNER_PATHS = new Set(['package.json']);
const RUNTIME_SENSITIVE_PREFIXES = Object.freeze([
  'electron/',
  'renderer/',
  'resources/coding-tools-mcp/coding_tools_mcp/'
]);

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function requestFingerprint(request) {
  return crypto.createHash('sha256').update(canonicalJson(request)).digest('hex');
}

function actionError(code, message, details = {}) {
  return Object.assign(new Error(message), { code, details });
}

class RecoveryActionStore {
  constructor({ paths, now = () => Date.now(), maxActions = MAX_ACTIONS }) {
    this.file = paths.recoveryActionsFile();
    this.now = now;
    this.maxActions = Math.max(8, Math.min(MAX_ACTIONS, Number(maxActions) || MAX_ACTIONS));
  }

  load() {
    const value = readJson(this.file, { version: STORE_VERSION, actions: [] });
    const actions = Array.isArray(value?.actions) ? value.actions.filter((item) => item && typeof item === 'object') : [];
    return { version: STORE_VERSION, actions };
  }

  save(actions) {
    const now = this.now();
    const retained = actions
      .filter((item) => Number(item?.created_at_unix_ms || 0) >= now - MAX_OPERATION_AGE_MS)
      .sort((left, right) => Number(right.created_at_unix_ms || 0) - Number(left.created_at_unix_ms || 0))
      .slice(0, this.maxActions);
    writeJsonAtomic(this.file, { version: STORE_VERSION, actions: retained });
  }

  replay(request) {
    const operationId = String(request?.operation_id || '');
    if (!OPERATION_ID_PATTERN.test(operationId)) {
      throw actionError('INVALID_OPERATION_ID', 'operation_id must contain 16-128 allowlisted characters.');
    }
    const fingerprint = requestFingerprint(request);
    const store = this.load();
    const existing = store.actions.find((item) => item.operation_id === operationId);
    if (!existing) return null;
    if (existing.request_fingerprint !== fingerprint) {
      throw actionError('IDEMPOTENCY_CONFLICT', 'operation_id was already used for a different activation request.');
    }
    if (existing.state === 'accepted' && Number(existing.expires_at_unix_ms || 0) <= this.now()) {
      return this.finish(existing.operation_id, 'failed', null, {
        code: 'ACTIVATION_REQUEST_EXPIRED',
        message: 'The activation request expired before completion.'
      });
    }
    return existing;
  }

  active(excludeOperationId = '') {
    const now = this.now();
    return this.load().actions.find((item) => (
      item.state === 'accepted'
      && Number(item.expires_at_unix_ms || 0) > now
      && String(item.operation_id || '') !== String(excludeOperationId || '')
    )) || null;
  }

  begin(request) {
    const replay = this.replay(request);
    if (replay) return { created: false, record: replay };
    const conflict = this.active(request?.operation_id);
    if (conflict) {
      throw actionError('ACTIVATION_CONFLICT', 'Another activation operation is already in flight.', {
        operation_id: conflict.operation_id,
        component: conflict.component
      });
    }
    const now = this.now();
    const expiresAt = Number(request?.expires_at_unix_ms || 0);
    if (!Number.isSafeInteger(expiresAt) || expiresAt <= now) {
      throw actionError('ACTIVATION_REQUEST_EXPIRED', 'The activation request has expired.');
    }
    const operationId = String(request.operation_id);
    const fingerprint = requestFingerprint(request);
    const store = this.load();
    const record = {
      version: STORE_VERSION,
      operation_id: operationId,
      component: request.component,
      action: 'activate_update',
      request_fingerprint: fingerprint,
      expected_disk_revision: request.expected_disk_revision,
      source_checkpoint: request.source_checkpoint && typeof request.source_checkpoint === 'object'
        ? stableValue(request.source_checkpoint)
        : null,
      allow_acceptance_pending: request.allow_acceptance_pending === true,
      requested_at_unix_ms: Number(request.requested_at_unix_ms || now),
      state: 'accepted',
      created_at: new Date(now).toISOString(),
      created_at_unix_ms: now,
      expires_at_unix_ms: expiresAt,
      updated_at: new Date(now).toISOString(),
      started_at: null,
      old_instance_state: null,
      old_instance_id: null,
      new_instance_id: null,
      lifecycle_decision: null,
      postflight: null,
      result: null,
      error: null
    };
    this.save([record, ...store.actions]);
    return { created: true, record };
  }

  get(operationId) {
    const record = this.load().actions.find((item) => item.operation_id === String(operationId || '')) || null;
    if (!record) return null;
    if (record.state === 'accepted' && Number(record.expires_at_unix_ms || 0) <= this.now()) {
      return this.finish(record.operation_id, 'failed', null, {
        code: 'ACTIVATION_REQUEST_EXPIRED',
        message: 'The activation request expired before completion.'
      });
    }
    return record;
  }

  annotate(operationId, patch = {}) {
    const store = this.load();
    const index = store.actions.findIndex((item) => item.operation_id === String(operationId || ''));
    if (index < 0) throw actionError('ACTIVATION_OPERATION_NOT_FOUND', 'Activation operation was not found.');
    const current = store.actions[index];
    if (['completed', 'failed', 'refused'].includes(current.state)) return current;
    const now = this.now();
    const next = {
      ...current,
      ...(Object.prototype.hasOwnProperty.call(patch, 'started_at') && !current.started_at
        ? { started_at: String(patch.started_at || '') || new Date(now).toISOString() }
        : {}),
      ...(Object.prototype.hasOwnProperty.call(patch, 'old_instance_id') && !current.old_instance_id
        ? { old_instance_id: String(patch.old_instance_id || '') || null }
        : {}),
      ...(Object.prototype.hasOwnProperty.call(patch, 'old_instance_state') && !current.old_instance_state
        ? { old_instance_state: ['ABSENT', 'RUNNING'].includes(String(patch.old_instance_state || '')) ? String(patch.old_instance_state) : null }
        : {}),
      ...(Object.prototype.hasOwnProperty.call(patch, 'lifecycle_decision') && patch.lifecycle_decision && typeof patch.lifecycle_decision === 'object'
        ? { lifecycle_decision: stableValue(patch.lifecycle_decision) }
        : {}),
      updated_at: new Date(now).toISOString()
    };
    store.actions[index] = next;
    this.save(store.actions);
    return next;
  }

  finish(operationId, state, result = null, error = null) {
    if (!['completed', 'failed', 'refused'].includes(state)) {
      throw actionError('INVALID_ACTION_STATE', 'Recovery action terminal state is invalid.');
    }
    const store = this.load();
    const index = store.actions.findIndex((item) => item.operation_id === String(operationId || ''));
    if (index < 0) throw actionError('ACTIVATION_OPERATION_NOT_FOUND', 'Activation operation was not found.');
    const current = store.actions[index];
    if (['completed', 'failed', 'refused'].includes(current.state)) return current;
    const now = this.now();
    const next = {
      ...current,
      state,
      updated_at: new Date(now).toISOString(),
      finished_at: new Date(now).toISOString(),
      old_instance_state: String(result?.postflight?.old_instance_state || current.old_instance_state || '') || null,
      new_instance_id: String(result?.postflight?.new_instance_id || current.new_instance_id || '') || null,
      postflight: result?.postflight && typeof result.postflight === 'object' ? stableValue(result.postflight) : null,
      result: result && typeof result === 'object' ? result : null,
      error: error && typeof error === 'object' ? {
        code: String(error.code || 'ACTIVATION_FAILED').slice(0, 80),
        message: String(error.message || 'Activation failed.').slice(0, 1000)
      } : null
    };
    store.actions[index] = next;
    this.save(store.actions);
    return next;
  }

  defer(operationId, result = null, error = null) {
    const store = this.load();
    const index = store.actions.findIndex((item) => item.operation_id === String(operationId || ''));
    if (index < 0) throw actionError('ACTIVATION_OPERATION_NOT_FOUND', 'Activation operation was not found.');
    const current = store.actions[index];
    if (['completed', 'failed', 'refused'].includes(current.state)) return current;
    const now = this.now();
    const next = {
      ...current,
      state: 'accepted',
      updated_at: new Date(now).toISOString(),
      result: result && typeof result === 'object' ? result : null,
      postflight: result?.postflight && typeof result.postflight === 'object' ? stableValue(result.postflight) : null,
      error: error && typeof error === 'object' ? {
        code: String(error.code || 'ACTIVATION_DEFERRED').slice(0, 80),
        message: String(error.message || 'Activation is waiting for a runtime condition.').slice(0, 1000)
      } : null
    };
    store.actions[index] = next;
    this.save(store.actions);
    return next;
  }

  resume(operationId) {
    const store = this.load();
    const index = store.actions.findIndex((item) => item.operation_id === String(operationId || ''));
    if (index < 0) throw actionError('ACTIVATION_OPERATION_NOT_FOUND', 'Activation operation was not found.');
    const current = store.actions[index];
    if (current.state !== 'accepted' || current.result?.component_stopped !== true) return current;
    const now = this.now();
    const next = {
      ...current,
      result: null,
      postflight: null,
      error: null,
      updated_at: new Date(now).toISOString()
    };
    store.actions[index] = next;
    this.save(store.actions);
    return next;
  }
}

function normalizeRelative(value) {
  const raw = String(value || '').trim().replace(/\\/g, '/').replace(/^\.\//, '');
  if (!raw || raw.startsWith('/') || /^[A-Za-z]:\//.test(raw) || raw.split('/').includes('..')) return '';
  return raw;
}

function stableValue(value) {
  if (Array.isArray(value)) return value.map(stableValue);
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stableValue(value[key])]));
}

function samePath(left, right) {
  const a = path.resolve(String(left || ''));
  const b = path.resolve(String(right || ''));
  return process.platform === 'win32' ? a.toLowerCase() === b.toLowerCase() : a === b;
}

function parseGitStatus(output) {
  if (!Buffer.isBuffer(output) && !(output instanceof Uint8Array)) {
    throw actionError('AUTO_ACTIVATION_GIT_MALFORMED', 'Git status identity must be parsed from raw bytes.');
  }
  let decoded;
  try {
    decoded = new TextDecoder('utf-8', { fatal: true }).decode(output);
  } catch {
    throw actionError('AUTO_ACTIVATION_GIT_MALFORMED', 'Git status contained non-UTF-8 path bytes.');
  }
  if (!decoded.endsWith('\0')) {
    throw actionError('AUTO_ACTIVATION_GIT_MALFORMED', 'Git status did not use complete NUL-delimited records.');
  }
  const records = decoded.slice(0, -1).split('\0');
  let branch = '';
  const entries = [];
  let index = 0;
  if (records[0]?.startsWith('## ')) {
    const value = records[0].slice(3);
    branch = (value.includes('...') ? value.split('...', 1)[0] : value).trim();
    index = 1;
  }
  while (index < records.length) {
    const record = records[index];
    if (!record || record.length < 4 || record[2] !== ' ' || record.startsWith('## ')) {
      throw actionError('AUTO_ACTIVATION_GIT_MALFORMED', 'Git status contained a malformed porcelain record.');
    }
    const indexStatus = record[0] || '';
    const worktreeStatus = record[1] || '';
    const pathText = record.slice(3);
    if (!pathText) {
      throw actionError('AUTO_ACTIVATION_GIT_MALFORMED', 'Git status contained an empty path.');
    }
    let originalPath = null;
    if ('RC'.includes(indexStatus) || 'RC'.includes(worktreeStatus)) {
      index += 1;
      originalPath = records[index];
      if (!originalPath) {
        throw actionError('AUTO_ACTIVATION_GIT_MALFORMED', 'Git rename/copy status omitted its original path.');
      }
    }
    entries.push({
      path: pathText,
      original_path: originalPath,
      index_status: indexStatus,
      worktree_status: worktreeStatus
    });
    index += 1;
  }
  if (entries.length > MAX_DIRTY_ENTRIES) {
    throw actionError('AUTO_ACTIVATION_GIT_TOO_LARGE', 'Git status exceeded the bounded activation limit.');
  }
  return { branch, entries };
}

async function runGit(workspace, args) {
  try {
    return await execFileAsync('git', ['-C', workspace, ...args], {
      cwd: workspace, windowsHide: true, encoding: 'utf8', timeout: 5000, maxBuffer: MAX_GIT_OUTPUT_BYTES
    });
  } catch (error) {
    throw actionError('AUTO_ACTIVATION_GIT_UNAVAILABLE', 'Git identity required for automatic activation is unavailable.', {
      exit_code: Number.isInteger(error?.code) ? error.code : null
    });
  }
}

async function runGitBytes(workspace, args) {
  try {
    return await execFileAsync('git', ['-C', workspace, ...args], {
      cwd: workspace, windowsHide: true, encoding: 'buffer', timeout: 5000, maxBuffer: MAX_GIT_OUTPUT_BYTES
    });
  } catch (error) {
    throw actionError('AUTO_ACTIVATION_GIT_UNAVAILABLE', 'Git identity required for automatic activation is unavailable.', {
      exit_code: Number.isInteger(error?.code) ? error.code : null
    });
  }
}

async function gitStatus(workspace, forceUntracked = false) {
  const root = String((await runGit(workspace, ['rev-parse', '--show-toplevel'])).stdout || '').trim();
  if (!root || !samePath(root, workspace)) throw actionError('AUTO_ACTIVATION_WORKSPACE_MISMATCH', 'Automatic activation requires the configured workspace Git root.');
  const args = ['status', '--porcelain=v1', '-z', '-b', forceUntracked ? '--untracked-files=all' : '--untracked-files=no'];
  const parsed = parseGitStatus((await runGitBytes(workspace, args)).stdout);
  const head = String((await runGit(workspace, ['rev-parse', 'HEAD'])).stdout || '').trim();
  return { ...parsed, head };
}

async function gitChangedPaths(workspace, fromHead, toHead) {
  const from = String(fromHead || '').toLowerCase();
  const to = String(toHead || '').toLowerCase();
  if (!GIT_OBJECT_ID.test(from) || !GIT_OBJECT_ID.test(to)) {
    throw actionError('BASE_HEAD_CHANGED', 'Component baseline Git identity is invalid.');
  }
  if (from === to) return [];
  let stdout;
  try {
    stdout = String((await runGit(workspace, ['diff', '--name-only', '--no-renames', `${from}..${to}`, '--'])).stdout || '');
  } catch {
    throw actionError('BASE_HEAD_CHANGED', 'Component baseline Git identity is no longer available.');
  }
  const files = [...new Set(stdout.split(/\r?\n/).map(normalizeRelative).filter(Boolean))];
  if (files.length > MAX_DIRTY_ENTRIES) {
    throw actionError('AUTO_ACTIVATION_GIT_TOO_LARGE', 'Committed Git delta exceeded the bounded activation limit.');
  }
  return files;
}

function fingerprintPaths(workspace, entries, head, branch) {
  const digest = crypto.createHash('sha256');
  const root = fs.realpathSync.native(path.resolve(workspace));
  for (const relative of [...new Set(entries.map((item) => item.path).filter(Boolean))].sort()) {
    digest.update(relative, 'utf8');
    const target = path.resolve(root, ...relative.split('/'));
    const outside = path.relative(root, target);
    if (outside.startsWith('..') || path.isAbsolute(outside)) { digest.update('<outside>', 'utf8'); continue; }
    try {
      const realTarget = fs.realpathSync.native(target);
      const realOutside = path.relative(root, realTarget);
      if (realOutside.startsWith('..') || path.isAbsolute(realOutside)) {
        digest.update('<outside>', 'utf8');
        continue;
      }
      const stat = fs.statSync(realTarget);
      digest.update(stat.isFile() ? fs.readFileSync(realTarget) : Buffer.from('<non-file>'));
    } catch (error) {
      digest.update(error?.code === 'ENOENT' ? '<missing>' : `<error:${String(error?.name || 'Error')}>`, 'utf8');
    }
  }
  digest.update(JSON.stringify(stableValue({ head, branch, entries })), 'utf8');
  return digest.digest('hex');
}

async function workspaceIdentity(workspace) {
  const status = await gitStatus(workspace, true);
  const entries = status.entries.filter((item) => {
    if (!item.path) return false;
    const protectedPath = process.platform === 'win32' ? item.path.toLowerCase() : item.path;
    return protectedPath !== '.coding-tools' && !protectedPath.startsWith('.coding-tools/');
  }).map((item) => ({
    path: item.path,
    index_status: item.index_status,
    worktree_status: item.worktree_status
  }));
  return { head: status.head, branch: status.branch, entries, worktree_fp: fingerprintPaths(workspace, entries, status.head, status.branch) };
}

function readJsonDirect(file, fallback) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return fallback; }
}

function parseCheckpointRow(row) {
  if (!row) return null;
  let metadata = {};
  try { metadata = JSON.parse(String(row.metadata_json || '{}')); } catch { metadata = {}; }
  return { ...row, metadata };
}

function readAcceptedCheckpoints(workspace, limit = MAX_ACCEPTED_CHECKPOINTS) {
  const ledger = path.join(workspace, '.coding-tools', 'orchestration', 'ledger.sqlite3');
  if (!fs.existsSync(ledger)) return [];
  let database;
  try {
    database = new DatabaseSync(ledger, { readOnly: true, timeout: 1000 });
    const bounded = Math.max(1, Math.min(MAX_ACCEPTED_CHECKPOINTS, Number(limit) || MAX_ACCEPTED_CHECKPOINTS));
    return database.prepare(`SELECT checkpoint_id,run_id,wave_id,git_head,proof_fingerprint,status,created_at,metadata_json FROM checkpoints WHERE status='accepted' ORDER BY created_at DESC,checkpoint_id DESC LIMIT ?`).all(bounded).reverse().map(parseCheckpointRow);
  } catch (error) {
    throw actionError('AUTO_ACTIVATION_LEDGER_UNAVAILABLE', 'Accepted orchestration checkpoint could not be read safely.', { sqlite_code: String(error?.code || '') });
  } finally {
    try { database?.close(); } catch { /* read-only handle cleanup */ }
  }
}

function readAcceptedCheckpoint(workspace, runId, waveId) {
  return readAcceptedCheckpoints(workspace).slice().reverse().find((item) => String(item.run_id) === String(runId) && String(item.wave_id) === String(waveId)) || null;
}

function normalizeReceipt(item, provenance = null) {
  if (!item || typeof item !== 'object') return null;
  const relative = normalizeRelative(item.path);
  if (!relative || relative.startsWith('.coding-tools/')) return null;
  const state = String(item.state || '');
  let receipt;
  if (state === 'missing') {
    if (item.sha256 !== null || Number(item.size_bytes) !== 0) return null;
    receipt = { path: relative, state, sha256: null, size_bytes: 0 };
  } else {
    const sha256 = String(item.sha256 || '').toLowerCase();
    const sizeBytes = Number(item.size_bytes);
    if (state !== 'file' || !HEX64.test(sha256) || !Number.isSafeInteger(sizeBytes) || sizeBytes < 0 || sizeBytes > MAX_TRUST_RECEIPT_FILE_BYTES) return null;
    receipt = { path: relative, state, sha256, size_bytes: sizeBytes };
  }
  if (!provenance) return receipt;
  const receiptKind = String(item.receipt_kind || '');
  const runId = String(item.run_id || '');
  const waveId = String(item.wave_id || '');
  const source = String(provenance.source || '');
  const allowedKinds = source === 'explicit_acceptance_attestations'
    ? new Set(['explicit_existing_file'])
    : source === 'durable_wave_patch_surface'
      ? new Set(['durable_wave_patch_surface', 'task_modified_file'])
      : new Set(['task_modified_file']);
  if (!ACCEPTED_RECEIPT_KINDS.has(receiptKind)
    || !allowedKinds.has(receiptKind)
    || runId !== String(provenance.runId || '')
    || waveId !== String(provenance.waveId || '')
    || item.restart_safe !== true
    || item.content_addressed !== (state === 'file')) return null;
  const normalized = {
    ...receipt,
    receipt_kind: receiptKind,
    run_id: runId,
    wave_id: waveId,
    restart_safe: true,
    content_addressed: state === 'file'
  };
  if (receiptKind === 'explicit_existing_file') {
    const expectedSha256 = String(item.expected_sha256 || '').toLowerCase();
    if (state !== 'file' || !HEX64.test(expectedSha256) || expectedSha256 !== receipt.sha256) return null;
    normalized.expected_sha256 = expectedSha256;
  }
  return normalized;
}

function parseAcceptedReceiptEnvelope(checkpoint) {
  const value = checkpoint?.metadata?.accepted_files;
  const runId = String(checkpoint?.run_id || '');
  const waveId = String(checkpoint?.wave_id || '');
  if (!value || value.schema_version !== ACCEPTED_FILE_SCHEMA_VERSION) {
    return { ok: false, code: 'RECEIPT_SCHEMA_UNSUPPORTED', message: 'Accepted checkpoint does not use the activation-safe receipt schema.' };
  }
  if (value.complete !== true || !Array.isArray(value.incomplete_reasons) || value.incomplete_reasons.length
    || !Array.isArray(value.files) || value.files.length > MAX_TRUST_RECEIPTS) {
    return { ok: false, code: 'RECEIPT_INCOMPLETE', message: 'Accepted checkpoint file receipts are incomplete.' };
  }
  const source = String(value.source || '');
  if (!runId || !waveId || String(value.run_id || '') !== runId || String(value.wave_id || '') !== waveId
    || !ACCEPTED_RECEIPT_SOURCES.has(source)) {
    return { ok: false, code: 'RECEIPT_PROVENANCE_INVALID', message: 'Accepted checkpoint receipt provenance is invalid.' };
  }
  const receipts = [];
  const seen = new Set();
  let totalBytes = 0;
  for (const item of value.files) {
    const receipt = normalizeReceipt(item, { runId, waveId, source });
    if (!receipt || seen.has(receipt.path)) {
      return { ok: false, code: 'RECEIPT_PROVENANCE_INVALID', message: 'Accepted checkpoint contains an invalid or duplicate file receipt.' };
    }
    seen.add(receipt.path);
    totalBytes += receipt.size_bytes;
    if (totalBytes > MAX_TRUST_RECEIPT_TOTAL_BYTES) {
      return { ok: false, code: 'RECEIPT_INCOMPLETE', message: 'Accepted checkpoint receipt bytes exceed the bounded activation budget.' };
    }
    receipts.push(receipt);
  }
  if (!Number.isSafeInteger(value.count) || value.count !== receipts.length
    || !Number.isSafeInteger(value.total_bytes) || value.total_bytes !== totalBytes) {
    return { ok: false, code: 'RECEIPT_INCOMPLETE', message: 'Accepted checkpoint receipt counts do not reconcile.' };
  }
  return {
    ok: true,
    envelope: {
      schema_version: ACCEPTED_FILE_SCHEMA_VERSION,
      source,
      run_id: runId,
      wave_id: waveId,
      complete: true,
      count: receipts.length,
      total_bytes: totalBytes,
      files: receipts,
      incomplete_reasons: []
    }
  };
}

function acceptedReceipts(checkpoint) {
  const parsed = parseAcceptedReceiptEnvelope(checkpoint);
  return parsed.ok ? parsed.envelope.files : null;
}

function eligibilityResult(checkpoint, patch = {}) {
  return {
    eligible: false,
    code: 'CHECKPOINT_NOT_ACTIVATABLE',
    message: 'Accepted checkpoint is not eligible for activation.',
    source_checkpoint_id: typeof checkpoint?.checkpoint_id === 'string' ? checkpoint.checkpoint_id : '',
    run_id: typeof checkpoint?.run_id === 'string' ? checkpoint.run_id : '',
    wave_id: typeof checkpoint?.wave_id === 'string' ? checkpoint.wave_id : '',
    proof_fingerprint: typeof checkpoint?.proof_fingerprint === 'string' ? checkpoint.proof_fingerprint : '',
    accepted_head: typeof checkpoint?.git_head === 'string' ? checkpoint.git_head : '',
    source_accepted: checkpoint?.status === 'accepted',
    accepted_receipts_complete: false,
    affected_components: [],
    component_receipts: {},
    receipts: [],
    ...patch
  };
}

function evaluateActivationEligibility(checkpoint, {
  workspace,
  currentHead,
  currentReceiptProvider = currentFileReceipt,
  componentOwnersProvider = componentOwners
} = {}) {
  const base = eligibilityResult(checkpoint);
  const proofIsEmpty = base.proof_fingerprint === '';
  if (!CHECKPOINT_ID_PATTERN.test(base.source_checkpoint_id)
    || !CHECKPOINT_ID_PATTERN.test(base.run_id)
    || !CHECKPOINT_ID_PATTERN.test(base.wave_id)
    || (!proofIsEmpty && !HEX64.test(base.proof_fingerprint))
    || !GIT_OBJECT_ID.test(base.accepted_head)) {
    return { ...base, code: 'CHECKPOINT_IDENTITY_INVALID', message: 'Accepted checkpoint identity is incomplete or invalid.' };
  }
  if (!base.source_accepted) {
    return { ...base, code: 'CHECKPOINT_NOT_ACCEPTED', message: 'Checkpoint status is not accepted.' };
  }
  const head = typeof currentHead === 'string' ? currentHead : '';
  if (!GIT_OBJECT_ID.test(head) || head !== base.accepted_head) {
    return { ...base, code: 'SOURCE_HEAD_DRIFT', message: 'Git HEAD no longer matches the accepted checkpoint.' };
  }
  const parsed = parseAcceptedReceiptEnvelope(checkpoint);
  if (!parsed.ok) return { ...base, code: parsed.code, message: parsed.message };
  const receipts = parsed.envelope.files;
  if (proofIsEmpty && receipts.length !== 0) {
    return { ...base, code: 'CHECKPOINT_IDENTITY_INVALID', message: 'Empty proof identity is reserved for an authoritative zero-file checkpoint.' };
  }
  const componentReceipts = Object.fromEntries(COMPONENT_ORDER.map((component) => [component, []]));
  const affected = new Set();
  for (const trusted of receipts) {
    let current;
    try { current = currentReceiptProvider(workspace, trusted.path); }
    catch (error) {
      return { ...base, code: 'SOURCE_DRIFT', message: 'Accepted source receipt could not be re-read.', details: { path: trusted.path, error_code: String(error?.code || '') } };
    }
    if (!receiptMatches(current, trusted)) {
      return { ...base, code: 'SOURCE_DRIFT', message: 'Accepted source bytes changed before activation.', details: { path: trusted.path } };
    }
    const owners = componentOwnersProvider(trusted.path);
    if (!Array.isArray(owners) || owners.some((component, index) => !COMPONENT_ORDER.includes(component) || owners.indexOf(component) !== index)) {
      return { ...base, code: 'COMPONENT_MAPPING_AMBIGUOUS', message: 'Component ownership mapping is not deterministic.', details: { path: trusted.path } };
    }
    if (owners.length > 1 && !ALLOWED_MULTI_OWNER_PATHS.has(trusted.path)) {
      return { ...base, code: 'COMPONENT_MAPPING_AMBIGUOUS', message: 'Accepted source maps to an undeclared multi-component owner set.', details: { path: trusted.path, owners } };
    }
    if (!owners.length && RUNTIME_SENSITIVE_PREFIXES.some((prefix) => trusted.path.startsWith(prefix))) {
      return { ...base, code: 'COMPONENT_MAPPING_UNMAPPED', message: 'Runtime-owned accepted source has no component mapping.', details: { path: trusted.path } };
    }
    for (const component of owners) {
      affected.add(component);
      componentReceipts[component].push(trusted);
    }
  }
  const affectedComponents = COMPONENT_ORDER.filter((component) => affected.has(component));
  return eligibilityResult(checkpoint, {
    eligible: true,
    code: 'ACTIVATABLE',
    message: 'Accepted checkpoint is eligible for component activation.',
    source_accepted: true,
    accepted_receipts_complete: true,
    affected_components: affectedComponents,
    component_receipts: Object.fromEntries(affectedComponents.map((component) => [component, componentReceipts[component]])),
    receipts
  });
}

function currentFileReceipt(workspace, relative) {
  const portable = normalizeRelative(relative);
  if (!portable || portable.startsWith('.coding-tools/')) throw actionError('AUTO_ACTIVATION_PATH_INVALID', 'Automatic activation receipt path is invalid.');
  const target = path.resolve(workspace, ...portable.split('/'));
  const escaped = path.relative(workspace, target);
  if (escaped.startsWith('..') || path.isAbsolute(escaped)) throw actionError('AUTO_ACTIVATION_PATH_INVALID', 'Automatic activation receipt escaped the workspace.');
  let stat;
  try { stat = fs.lstatSync(target); }
  catch (error) {
    if (error?.code === 'ENOENT') return { path: portable, state: 'missing', sha256: null, size_bytes: 0 };
    throw actionError('AUTO_ACTIVATION_RECEIPT_UNAVAILABLE', 'Automatic activation could not inspect a source receipt.');
  }
  if (stat.isSymbolicLink() || !stat.isFile()) throw actionError('AUTO_ACTIVATION_RECEIPT_UNSUPPORTED', 'Automatic activation receipts require regular files.');
  const sizeBytes = Number(stat.size);
  if (!Number.isSafeInteger(sizeBytes) || sizeBytes < 0 || sizeBytes > MAX_TRUST_RECEIPT_FILE_BYTES) throw actionError('AUTO_ACTIVATION_RECEIPT_TOO_LARGE', 'Automatic activation source receipt exceeded the bounded file size.');
  const content = fs.readFileSync(target);
  return { path: portable, state: 'file', sha256: crypto.createHash('sha256').update(content).digest('hex'), size_bytes: content.length };
}

function receiptMap(receipts) {
  return new Map((Array.isArray(receipts) ? receipts : []).map((item) => [item.path, item]));
}

function receiptMatches(current, trusted) {
  return Boolean(current && trusted && current.path === trusted.path && current.state === trusted.state
    && (current.state === 'missing' || (current.sha256 === trusted.sha256 && current.size_bytes === trusted.size_bytes)));
}

function trustedAcceptedCheckpoints(checkpoints, head) {
  return (Array.isArray(checkpoints) ? checkpoints : []).map((checkpoint) => ({ checkpoint, receipts: acceptedReceipts(checkpoint) }))
    .filter(({ checkpoint, receipts }) => checkpoint?.status === 'accepted'
      && typeof checkpoint.git_head === 'string' && checkpoint.git_head === head
      && HEX64.test(typeof checkpoint.proof_fingerprint === 'string' ? checkpoint.proof_fingerprint : '')
      && receipts !== null);
}

function acceptedReceiptUnion(checkpoints, head) {
  const union = new Map();
  for (const { receipts } of trustedAcceptedCheckpoints(checkpoints, head)) {
    for (const receipt of receipts) union.set(receipt.path, receipt);
  }
  return union;
}

function normalizeBaseline(value) {
  if (!value || typeof value !== 'object' || !String(value.head || '')) return null;
  const components = {};
  for (const component of COMPONENT_ORDER) {
    const source = value.components?.[component] && typeof value.components[component] === 'object' ? value.components[component] : {};
    const revision = String(source.revision || '').toLowerCase();
    const receipts = [];
    let totalBytes = 0;
    for (const item of (Array.isArray(source.receipts) ? source.receipts : []).slice(0, MAX_TRUST_RECEIPTS)) {
      const receipt = normalizeReceipt(item);
      if (!receipt || receipts.some((current) => current.path === receipt.path)) continue;
      if (totalBytes + receipt.size_bytes > MAX_TRUST_RECEIPT_TOTAL_BYTES) break;
      totalBytes += receipt.size_bytes;
      receipts.push(receipt);
    }
    components[component] = { head: String(source.head || value.head || ''), revision: HEX64.test(revision) ? revision : null, receipts };
  }
  return { head: String(value.head), components, captured_at: String(value.captured_at || ''), updated_at: String(value.updated_at || '') };
}

function normalizePostflightReceipt(value) {
  return normalizeActivationPostflight(value);
}

function postflightRevisionVerified(postflight) {
  return importedPostflightRevisionVerified(postflight);
}

function postflightMatchesIntent(postflight, intent, operationId = '') {
  const expectedOperationId = String(operationId || intent?.current_operation_id || intent?.activation_operation_id || '').trim();
  return verifyPostflightMatchesIntent(postflight, intent, { operationId: expectedOperationId });
}

function normalizeClosureInput(value) {
  if (!value || typeof value !== 'object' || Number(value.schema_version) !== CLOSURE_INPUT_SCHEMA_VERSION) return null;
  const runId = typeof value.run_id === 'string' ? value.run_id : '';
  const waveId = typeof value.wave_id === 'string' ? value.wave_id : '';
  const checkpointId = typeof value.source_checkpoint_id === 'string' ? value.source_checkpoint_id : '';
  const proofFingerprint = typeof value.proof_fingerprint === 'string' ? value.proof_fingerprint : '';
  const acceptedHead = typeof value.accepted_head === 'string' ? value.accepted_head : '';
  if (!CHECKPOINT_ID_PATTERN.test(runId) || !CHECKPOINT_ID_PATTERN.test(waveId)
    || !CHECKPOINT_ID_PATTERN.test(checkpointId) || !GIT_OBJECT_ID.test(acceptedHead)
    || (proofFingerprint !== '' && !HEX64.test(proofFingerprint))) return null;
  const rawAffectedComponents = Array.isArray(value.affected_components)
    ? value.affected_components.slice(0, 16).map((component) => String(component || ''))
    : [];
  const affectedComponentsValid = Array.isArray(value.affected_components)
    && value.affected_components.length <= COMPONENT_ORDER.length
    && rawAffectedComponents.every((component, index) => COMPONENT_ORDER.includes(component)
      && rawAffectedComponents.indexOf(component) === index)
    && rawAffectedComponents.every((component, index) => COMPONENT_ORDER.indexOf(component)
      > (index === 0 ? -1 : COMPONENT_ORDER.indexOf(rawAffectedComponents[index - 1])));
  const knownAffectedComponents = COMPONENT_ORDER.filter((component) => rawAffectedComponents.includes(component));
  const componentReceipts = {};
  const postflightReceipts = {};
  const rawComponentReceipts = value.component_receipts;
  let componentReceiptsValid = Boolean(rawComponentReceipts
    && typeof rawComponentReceipts === 'object'
    && !Array.isArray(rawComponentReceipts)
    && Object.keys(rawComponentReceipts).length === knownAffectedComponents.length
    && Object.keys(rawComponentReceipts).every((component) => knownAffectedComponents.includes(component)));
  for (const component of knownAffectedComponents) {
    const rawReceipts = Array.isArray(rawComponentReceipts?.[component]) ? rawComponentReceipts[component] : [];
    const normalizedReceipts = rawReceipts.map((item) => normalizeReceipt(item, { runId, waveId, source: String(item?.receipt_kind || '') === 'explicit_existing_file' ? 'explicit_acceptance_attestations' : String(item?.receipt_kind || '') === 'durable_wave_patch_surface' ? 'durable_wave_patch_surface' : 'task_modified_files' }));
    if (!rawReceipts.length || normalizedReceipts.some((item) => !item)
      || new Set(normalizedReceipts.map((item) => item?.path)).size !== normalizedReceipts.length) {
      componentReceiptsValid = false;
      componentReceipts[component] = [];
    } else {
      componentReceipts[component] = normalizedReceipts;
    }
    const postflight = normalizePostflightReceipt(value.postflight_receipts?.[component]);
    if (postflight) postflightReceipts[component] = postflight;
  }
  const sourceAccepted = value.source_accepted === true;
  const acceptedReceiptsComplete = value.accepted_receipts_complete === true;
  const activationEligible = sourceAccepted && acceptedReceiptsComplete && affectedComponentsValid
    && componentReceiptsValid && value.activation_eligible === true;
  const lifecycleDecision = normalizeLifecycleDecision(value.lifecycle_decision);
  const zeroTargetVerified = knownAffectedComponents.length === 0
    && lifecycleDecisionIsClean(lifecycleDecision);
  const emptyProofAuthorized = proofFingerprint === ''
    && knownAffectedComponents.length === 0
    && affectedComponentsValid
    && componentReceiptsValid
    && activationEligible;
  if (proofFingerprint === '' && !emptyProofAuthorized) return null;
  const componentsCurrent = activationEligible && (knownAffectedComponents.length === 0 ? zeroTargetVerified : knownAffectedComponents.every((component) => {
    const postflight = postflightReceipts[component];
    return Boolean(postflight
      && postflight.source_checkpoint_id === checkpointId
      && postflight.run_id === runId
      && postflight.wave_id === waveId
      && postflight.health_verified === true
      && postflight.postflight_verified === true
      && postflightRevisionVerified(postflight)
      && postflight.started_at
      && postflight.completed_at);
  }));
  return {
    schema_version: CLOSURE_INPUT_SCHEMA_VERSION,
    source_checkpoint_id: checkpointId,
    run_id: runId,
    wave_id: waveId,
    proof_fingerprint: proofFingerprint,
    accepted_head: acceptedHead,
    source_accepted: sourceAccepted,
    accepted_receipts_complete: acceptedReceiptsComplete,
    activation_eligible: activationEligible,
    eligibility_code: String(value.eligibility_code || ''),
    affected_components: rawAffectedComponents,
    affected_components_valid: affectedComponentsValid,
    component_receipts_valid: componentReceiptsValid,
    component_receipts: componentReceipts,
    postflight_receipts: postflightReceipts,
    components_current: componentsCurrent,
    lifecycle_decision: lifecycleDecision,
    lifecycle_clean: lifecycleDecisionIsClean(lifecycleDecision),
    observed_at: String(value.observed_at || '') || null
  };
}

function autoState(value) {
  const source = value && typeof value === 'object' ? value : {};
  const compatible = Number(source.version) === 2;
  const intents = compatible && Array.isArray(source.intents) ? source.intents.filter((item) => item && typeof item === 'object').slice(-MAX_AUTO_INTENTS) : [];
  const processed = compatible && Array.isArray(source.processed_checkpoint_ids)
    ? [...new Set(source.processed_checkpoint_ids.map(String).filter(Boolean))].slice(-MAX_PROCESSED_CHECKPOINTS) : [];
  return {
    version: 2,
    active_checkpoint_id: compatible ? (String(source.active_checkpoint_id || '') || null) : null,
    processed_checkpoint_ids: processed,
    baseline: compatible ? normalizeBaseline(source.baseline) : null,
    closure_input: compatible ? normalizeClosureInput(source.closure_input) : null,
    intents,
    updated_at: String(source.updated_at || new Date().toISOString())
  };
}

function autoOperationId(intent, attempt) {
  const digest = crypto.createHash('sha256').update(`${intent.checkpoint_id}:${intent.component}:${attempt}`).digest('hex');
  return `auto_${digest.slice(0, 48)}`;
}

function zeroTargetVerificationOperationId(checkpoint) {
  const digest = crypto.createHash('sha256').update(canonicalJson({
    checkpoint_id: checkpoint?.checkpoint_id,
    run_id: checkpoint?.run_id,
    wave_id: checkpoint?.wave_id,
    proof_fingerprint: checkpoint?.proof_fingerprint,
    git_head: checkpoint?.git_head
  })).digest('hex');
  return `auto_zero_${digest.slice(0, 48)}`;
}

class AcceptedCodeActivationController {
  constructor({ paths, settings, revisions, activation, log, now = () => Date.now(), intervalMs = AUTO_ACTIVATION_INTERVAL_MS,
    identityProvider = workspaceIdentity, forcedStatusProvider = (workspace) => gitStatus(workspace, true),
    acceptedCheckpointProvider = readAcceptedCheckpoints, runningRevisionProvider = null }) {
    this.paths = paths; this.settings = settings; this.revisions = revisions; this.activation = activation; this.log = log;
    this.now = now; this.intervalMs = Math.max(500, Number(intervalMs) || AUTO_ACTIVATION_INTERVAL_MS);
    this.identityProvider = identityProvider; this.forcedStatusProvider = forcedStatusProvider;
    this.acceptedCheckpointProvider = acceptedCheckpointProvider; this.runningRevisionProvider = runningRevisionProvider;
    this.timer = null; this.processing = false; this.lastError = null;
  }

  loadState() { return autoState(readJson(this.paths.acceptedCodeActivationFile(), {})); }
  saveState(state) { const next = autoState({ ...state, updated_at: new Date(this.now()).toISOString() }); writeJsonAtomic(this.paths.acceptedCodeActivationFile(), next); return next; }
  status() {
    const state = this.loadState();
    const count = (name) => state.intents.filter((item) => item.state === name).length;
    return { trust_model: 'running_baseline_accepted_receipts_v2', continuity_mode: 'detached_runtime_children_v1', running: Boolean(this.timer), processing: this.processing, pending: count('pending'), deferred: count('deferred'), awaiting: count('awaiting'), blocked: count('blocked'), failed: count('failed'), completed: count('completed'), baseline_head: state.baseline?.head || null, processed_checkpoints: state.processed_checkpoint_ids.length, closure_input: state.closure_input, last_error: this.lastError };
  }
  start() { if (this.timer) return this.status(); this.timer = setInterval(() => { this.tick().catch(() => {}); }, this.intervalMs); this.timer.unref(); setImmediate(() => { this.tick().catch(() => {}); }); return this.status(); }
  stop() { if (this.timer) clearInterval(this.timer); this.timer = null; return true; }

  newClosureInput(evaluation) {
    return normalizeClosureInput({
      schema_version: CLOSURE_INPUT_SCHEMA_VERSION,
      source_checkpoint_id: evaluation.source_checkpoint_id,
      run_id: evaluation.run_id,
      wave_id: evaluation.wave_id,
      proof_fingerprint: evaluation.proof_fingerprint,
      accepted_head: evaluation.accepted_head,
      source_accepted: evaluation.source_accepted,
      accepted_receipts_complete: evaluation.accepted_receipts_complete,
      activation_eligible: evaluation.eligible,
      eligibility_code: evaluation.code,
      affected_components: evaluation.affected_components,
      component_receipts: evaluation.component_receipts,
      postflight_receipts: {},
      components_current: false,
      lifecycle_decision: null,
      lifecycle_clean: false,
      observed_at: new Date(this.now()).toISOString()
    });
  }

  refreshClosureInput(state) {
    const closure = state.closure_input;
    if (!closure) return null;
    const intents = state.intents.filter((item) => item.checkpoint_id === closure.source_checkpoint_id);
    const postflightReceipts = {};
    let lifecycleDecision = closure.lifecycle_decision;
    for (const intent of intents) {
      const postflight = normalizePostflightReceipt(intent.result?.postflight);
      if (postflight) {
        postflightReceipts[intent.component] = postflight;
        if (postflight.lifecycle_decision) lifecycleDecision = postflight.lifecycle_decision;
      }
      if (intent.lifecycle_decision && typeof intent.lifecycle_decision === 'object') lifecycleDecision = intent.lifecycle_decision;
    }
    const allCurrent = closure.affected_components.length === 0
      ? lifecycleDecisionIsClean(lifecycleDecision)
      : closure.affected_components.every((component) => {
      const intent = intents.find((item) => item.component === component);
      const postflight = postflightReceipts[component];
      return Boolean(intent?.state === 'completed' && postflightMatchesIntent(postflight, intent));
    });
    const activationEligible = closure.activation_eligible
      && !intents.some((item) => ['blocked', 'failed', 'superseded'].includes(String(item.state || '')));
    state.closure_input = normalizeClosureInput({
      ...closure,
      activation_eligible: activationEligible,
      postflight_receipts: postflightReceipts,
      components_current: allCurrent,
      lifecycle_decision: lifecycleDecision,
      lifecycle_clean: lifecycleDecisionIsClean(lifecycleDecision),
      observed_at: new Date(this.now()).toISOString()
    });
    return state.closure_input;
  }

  runtimeRevisionStatus(component) {
    try {
      if (typeof this.runningRevisionProvider === 'function') return this.runningRevisionProvider(component) || {};
      if (component === 'recovery_host' && typeof this.activation?.recoveryRevisionStatus === 'function') return this.activation.recoveryRevisionStatus() || {};
      if (component === 'coding_mcp' && typeof this.activation?.orchestrator?.codingMcpRevisionStatus === 'function') return this.activation.orchestrator.codingMcpRevisionStatus() || {};
      if (component === 'electron_ui' && typeof this.activation?.uiRevisionStatus === 'function') return this.activation.uiRevisionStatus() || {};
      return this.revisions.status?.(component) || {};
    } catch { return {}; }
  }

  captureComponentReceipts(workspace, component, forcedEntries) {
    const files = [...new Set((forcedEntries || []).map((item) => normalizeRelative(typeof item === 'string' ? item : item?.path)).filter((relative) => componentOwnsPath(component, relative)))];
    if (files.length > MAX_TRUST_RECEIPTS) throw actionError('AUTO_ACTIVATION_RECEIPT_TOO_LARGE', 'Target component has too many dirty source receipts.');
    const receipts = [];
    let totalBytes = 0;
    for (const relative of files) {
      const receipt = currentFileReceipt(workspace, relative);
      totalBytes += receipt.size_bytes;
      if (totalBytes > MAX_TRUST_RECEIPT_TOTAL_BYTES) throw actionError('AUTO_ACTIVATION_RECEIPT_TOO_LARGE', 'Target component dirty receipts exceeded the bounded byte budget.');
      receipts.push(receipt);
    }
    return receipts;
  }

  captureBaseline(workspace, forced) {
    const components = {};
    for (const component of COMPONENT_ORDER) {
      const diskRevision = String(this.revisions.disk(component, { force: true }).revision || '').toLowerCase();
      const runningRevision = String(this.runtimeRevisionStatus(component).running_revision || '').toLowerCase();
      const current = HEX64.test(runningRevision) && runningRevision === diskRevision;
      components[component] = {
        head: String(forced.head || ''),
        revision: HEX64.test(runningRevision) ? runningRevision : null,
        receipts: current ? this.captureComponentReceipts(workspace, component, forced.entries) : []
      };
    }
    const now = new Date(this.now()).toISOString();
    return { head: String(forced.head || ''), components, captured_at: now, updated_at: now };
  }

  async ensureBaseline(workspace, state, forced) {
    if (!state.baseline) {
      state.baseline = this.captureBaseline(workspace, forced);
      this.saveState(state);
      return state.baseline;
    }
    const currentHead = String(forced.head || '');
    const active = state.intents.filter((item) => item.checkpoint_id === state.active_checkpoint_id && !TERMINAL_INTENT_STATES.has(String(item.state || '')));
    if (active.some((item) => String(item.accepted_head || '') !== currentHead)) {
      throw actionError('BASE_HEAD_CHANGED', 'Git HEAD changed while an automatic activation was still active.');
    }
    let changed = false;
    for (const component of COMPONENT_ORDER) {
      const row = state.baseline.components?.[component];
      if (!row) continue;
      const rowHead = String(row.head || state.baseline.head || '');
      if (!row.head && rowHead) { row.head = rowHead; changed = true; }
      const baselineRevision = String(row.revision || '').toLowerCase();
      const diskRevision = String(this.revisions.disk(component, { force: true }).revision || '').toLowerCase();
      const runningRevision = String(this.runtimeRevisionStatus(component).running_revision || '').toLowerCase();
      if (rowHead === currentHead) {
        if (!HEX64.test(baselineRevision) && HEX64.test(runningRevision) && runningRevision === diskRevision) {
          row.revision = runningRevision;
          row.receipts = this.captureComponentReceipts(workspace, component, forced.entries);
          changed = true;
        }
        continue;
      }
      let committed;
      try { committed = (await gitChangedPaths(workspace, rowHead, currentHead)).filter((relative) => componentOwnsPath(component, relative)); }
      catch { continue; }
      const currentReceipts = this.captureComponentReceipts(workspace, component, [...forced.entries, ...committed]);
      const baselineMap = receiptMap(row.receipts || []);
      const bytesUnchanged = currentReceipts.every((current) => receiptMatches(current, baselineMap.get(current.path)));
      if (HEX64.test(baselineRevision) && runningRevision === baselineRevision && diskRevision === baselineRevision && bytesUnchanged) {
        row.head = currentHead;
        row.receipts = currentReceipts;
        changed = true;
      }
    }
    const rowHeads = COMPONENT_ORDER.map((component) => String(state.baseline.components?.[component]?.head || ''));
    if (rowHeads.length && rowHeads.every((head) => head === currentHead) && state.baseline.head !== currentHead) {
      state.baseline.head = currentHead;
      changed = true;
    }
    if (changed) { state.baseline.updated_at = new Date(this.now()).toISOString(); this.saveState(state); }
    return state.baseline;
  }

  async componentGate(workspace, component, baseline, accepted, forced) {
    const row = baseline?.components?.[component] || {};
    const baselineHead = String(row.head || baseline?.head || '');
    const currentHead = String(forced?.head || '');
    const committed = baselineHead === currentHead ? [] : (await gitChangedPaths(workspace, baselineHead, currentHead)).filter((relative) => componentOwnsPath(component, relative));
    const currentReceipts = this.captureComponentReceipts(workspace, component, [...(forced?.entries || []), ...committed]);
    const baselineMap = receiptMap(row.receipts || []);
    const untrusted = currentReceipts.filter((current) => !receiptMatches(current, baselineMap.get(current.path)) && !receiptMatches(current, accepted.get(current.path)));
    if (untrusted.length) {
      return {
        error: { code: 'UNACCEPTED_COMPONENT_DIRTY', message: 'Target component contains dirty bytes that are neither running-baseline nor finally accepted.', files: untrusted.slice(0, 20).map((item) => item.path) },
        receipts: currentReceipts,
        committed_paths: committed
      };
    }
    return { error: null, receipts: currentReceipts, committed_paths: committed };
  }

  candidate(checkpoints, state, workspace, head) {
    const processed = new Set(state.processed_checkpoint_ids);
    for (const checkpoint of (Array.isArray(checkpoints) ? checkpoints : [])) {
      if (processed.has(String(checkpoint?.checkpoint_id || ''))
        || typeof checkpoint?.git_head !== 'string'
        || checkpoint.git_head !== head) continue;
      const evaluation = evaluateActivationEligibility(checkpoint, { workspace, currentHead: head });
      return { checkpoint, evaluation, receipts: evaluation.receipts };
    }
    return null;
  }

  markActiveProcessed(state) {
    if (!state.active_checkpoint_id) return false;
    const active = state.intents.filter((item) => item.checkpoint_id === state.active_checkpoint_id);
    if (!active.length || active.some((item) => !TERMINAL_INTENT_STATES.has(String(item.state || '')))) return false;
    state.processed_checkpoint_ids = [...new Set([...state.processed_checkpoint_ids, state.active_checkpoint_id])].slice(-MAX_PROCESSED_CHECKPOINTS);
    state.active_checkpoint_id = null;
    this.saveState(state);
    return true;
  }

  supersedeStaleActiveIntents(state, currentHead) {
    if (!state.active_checkpoint_id) return { changed: false, awaiting_operation: false };
    const stale = state.intents.filter((item) => item.checkpoint_id === state.active_checkpoint_id
      && !TERMINAL_INTENT_STATES.has(String(item.state || ''))
      && String(item.accepted_head || '') !== String(currentHead || ''));
    if (!stale.length) return { changed: false, awaiting_operation: false };
    if (stale.some((item) => String(item.current_operation_id || ''))) {
      return { changed: false, awaiting_operation: true };
    }
    const updatedAt = new Date(this.now()).toISOString();
    for (const intent of stale) {
      Object.assign(intent, {
        state: 'superseded',
        current_operation_id: null,
        error: {
          code: 'BASE_HEAD_CHANGED',
          message: 'Git HEAD changed before automatic activation; the stale intent was superseded.'
        },
        updated_at: updatedAt
      });
    }
    this.refreshClosureInput(state);
    this.saveState(state);
    return { changed: true, awaiting_operation: false };
  }

  async discover() {
    const rawWorkspace = String(this.settings.load()?.workspace || '').trim();
    if (!rawWorkspace) return false;
    const workspace = path.resolve(rawWorkspace);
    if (!fs.existsSync(workspace)) return false;
    const state = this.loadState();
    const forced = await this.forcedStatusProvider(workspace);
    const headDrift = this.supersedeStaleActiveIntents(state, forced.head);
    if (headDrift.awaiting_operation) return false;
    if (headDrift.changed && state.active_checkpoint_id && !this.markActiveProcessed(state)) return false;
    await this.ensureBaseline(workspace, state, forced);
    if (state.active_checkpoint_id) {
      if (!this.markActiveProcessed(state)) return false;
    }
    const checkpoints = this.acceptedCheckpointProvider(workspace, MAX_ACCEPTED_CHECKPOINTS);
    const candidate = this.candidate(checkpoints, state, workspace, forced.head);
    if (!candidate) return false;
    const checkpointId = String(candidate.checkpoint.checkpoint_id);
    state.closure_input = this.newClosureInput(candidate.evaluation);
    if (!candidate.evaluation.eligible) {
      state.processed_checkpoint_ids = [...new Set([...state.processed_checkpoint_ids, checkpointId])].slice(-MAX_PROCESSED_CHECKPOINTS);
      this.saveState(state);
      return false;
    }
    const targets = candidate.evaluation.affected_components;
    if (!targets.length) {
      try {
        const lifecycle = await this.activation.verifyCheckpointLifecycle({
          operationId: zeroTargetVerificationOperationId(candidate.checkpoint),
          sourceCheckpoint: {
            checkpoint_id: candidate.checkpoint.checkpoint_id,
            run_id: candidate.checkpoint.run_id,
            wave_id: candidate.checkpoint.wave_id,
            proof_fingerprint: candidate.checkpoint.proof_fingerprint,
            git_head: candidate.checkpoint.git_head
          }
        });
        state.closure_input.lifecycle_decision = lifecycle;
        state.closure_input.lifecycle_clean = lifecycle.clean === true;
        state.closure_input.components_current = lifecycle.clean === true;
        state.closure_input.observed_at = new Date(this.now()).toISOString();
        state.processed_checkpoint_ids = [...new Set([...state.processed_checkpoint_ids, checkpointId])].slice(-MAX_PROCESSED_CHECKPOINTS);
        state.closure_input = normalizeClosureInput(state.closure_input);
        this.saveState(state);
      } catch (error) {
        state.closure_input.lifecycle_decision = {
          schema_version: 1,
          clean: false,
          code: String(error?.code || 'LIFECYCLE_VERIFICATION_FAILED'),
          reason: String(error?.message || 'Zero-target lifecycle verification failed.'),
          observed_at: new Date(this.now()).toISOString(),
          canonical_lifecycle_observed: false,
          source_checkpoint_verified: false,
          fence_released: false,
          fenced: null,
          fence_operation_id: null,
          operation_id: zeroTargetVerificationOperationId(candidate.checkpoint),
          counts: {},
          unexplained_active_runs: 0,
          unbound_live_resource_residues: 0
        };
        state.closure_input.lifecycle_clean = false;
        state.closure_input.components_current = false;
        this.saveState(state);
      }
      return false;
    }
    const accepted = acceptedReceiptUnion(checkpoints, forced.head);
    state.active_checkpoint_id = checkpointId;
    for (const component of targets) {
      const gate = await this.componentGate(workspace, component, state.baseline, accepted, forced);
      state.intents.push({
        checkpoint_id: checkpointId,
        run_id: String(candidate.checkpoint.run_id || ''),
        wave_id: String(candidate.checkpoint.wave_id || ''),
        proof_fingerprint: String(candidate.checkpoint.proof_fingerprint).toLowerCase(),
        accepted_head: String(candidate.checkpoint.git_head || ''),
        accepted_files: candidate.receipts.map((receipt) => receipt.path),
        component,
        expected_revision: String(this.revisions.disk(component, { force: true }).revision || '').toLowerCase(),
        trusted_head: null,
        trusted_receipts: [],
        state: gate.error ? 'blocked' : 'pending',
        attempt: 0,
        current_operation_id: null,
        error: gate.error,
        created_at: new Date(this.now()).toISOString(),
        updated_at: new Date(this.now()).toISOString()
      });
    }
    state.intents = state.intents.slice(-MAX_AUTO_INTENTS);
    if (state.intents.some((item) => item.checkpoint_id === checkpointId && item.state === 'blocked')) {
      state.closure_input.activation_eligible = false;
    }
    this.refreshClosureInput(state);
    this.saveState(state); return true;
  }

  async revalidate(intent) {
    const rawWorkspace = String(this.settings.load()?.workspace || '').trim();
    if (!rawWorkspace) throw actionError('AUTO_ACTIVATION_WORKSPACE_MISMATCH', 'Configured workspace is unavailable.');
    const workspace = path.resolve(rawWorkspace);
    const forced = await this.forcedStatusProvider(workspace);
    const state = this.loadState();
    const baseline = await this.ensureBaseline(workspace, state, forced);
    const checkpoints = this.acceptedCheckpointProvider(workspace, MAX_ACCEPTED_CHECKPOINTS);
    const checkpoint = checkpoints.find((item) => String(item?.checkpoint_id || '') === intent.checkpoint_id) || null;
    if (!checkpoint || String(checkpoint.proof_fingerprint).toLowerCase() !== intent.proof_fingerprint || String(checkpoint.git_head || '') !== intent.accepted_head) throw actionError('ACCEPTED_CHECKPOINT_CHANGED', 'Accepted checkpoint identity changed before activation.');
    const eligibility = evaluateActivationEligibility(checkpoint, { workspace, currentHead: forced.head });
    if (!eligibility.eligible) throw actionError(eligibility.code, eligibility.message, eligibility.details || {});
    const accepted = acceptedReceiptUnion(checkpoints, forced.head);
    const gate = await this.componentGate(workspace, intent.component, baseline, accepted, forced);
    if (gate.error) throw actionError(gate.error.code, gate.error.message, { files: gate.error.files });
    const diskRevision = String(this.revisions.disk(intent.component, { force: true }).revision || '').toLowerCase();
    if (diskRevision !== intent.expected_revision) throw actionError('REVISION_CHANGED', 'Target component revision changed after final acceptance.');
    return { head: String(forced.head || ''), receipts: gate.receipts };
  }

  updateIntent(state, intent, patch) {
    Object.assign(intent, patch, { updated_at: new Date(this.now()).toISOString() });
    this.refreshClosureInput(state);
    this.saveState(state);
  }
  advanceBaseline(state, intent, postflight) {
    if (!state.baseline || !GIT_OBJECT_ID.test(String(intent.trusted_head || '').toLowerCase()) || !Array.isArray(intent.trusted_receipts)) return false;
    const row = state.baseline.components?.[intent.component];
    const runningRevision = String(postflight?.running_revision || '').toLowerCase();
    if (!row || !postflightMatchesIntent(postflight, intent) || !HEX64.test(runningRevision)) return false;
    row.head = String(intent.trusted_head).toLowerCase();
    row.revision = runningRevision;
    row.receipts = intent.trusted_receipts.map((item) => normalizeReceipt(item)).filter(Boolean);
    const rowHeads = COMPONENT_ORDER.map((component) => String(state.baseline.components?.[component]?.head || ''));
    if (rowHeads.length && rowHeads.every((head) => head === row.head)) state.baseline.head = row.head;
    state.baseline.updated_at = new Date(this.now()).toISOString();
    return true;
  }
  applyRecord(state, intent, record) {
    const recordState = String(record?.state || '');
    if (recordState === 'completed') {
      const postflight = normalizePostflightReceipt(record?.result?.postflight || record?.postflight);
      const operationMatches = String(record?.operation_id || '') === String(intent?.current_operation_id || intent?.activation_operation_id || '');
      if (!operationMatches || !postflightMatchesIntent(postflight, intent, record?.operation_id)) {
        this.updateIntent(state, intent, {
          state: 'failed',
          current_operation_id: null,
          lifecycle_decision: postflight?.lifecycle_decision || intent.lifecycle_decision || null,
          error: {
            code: operationMatches ? 'POSTFLIGHT_UNVERIFIED' : 'POSTFLIGHT_OPERATION_MISMATCH',
            message: 'Activation completed without a checkpoint-bound verified component postflight receipt.'
          },
          result: record?.result || null
        });
        return;
      }
      if (!this.advanceBaseline(state, intent, postflight)) {
        this.updateIntent(state, intent, { state: 'failed', current_operation_id: null, lifecycle_decision: postflight.lifecycle_decision, error: { code: 'AUTO_ACTIVATION_BASELINE_ADVANCE_FAILED', message: 'Activation completed but its trusted running baseline could not be advanced.' }, result: record.result || null });
        return;
      }
      this.updateIntent(state, intent, { state: 'completed', current_operation_id: null, lifecycle_decision: postflight.lifecycle_decision, error: null, result: { ...(record.result || {}), postflight } }); return;
    }
    if (recordState === 'accepted') {
      if (record?.result?.component_stopped === true) {
        this.updateIntent(state, intent, Number(record.expires_at_unix_ms || 0) > this.now()
          ? { state: 'awaiting', error: { code: 'COMPONENT_AWAITING_START', message: 'Coding MCP is stopped; activation remains resumable until a fresh instance starts.' } }
          : { state: 'deferred', current_operation_id: null, error: { code: 'ACTIVATION_REQUEST_EXPIRED', message: 'Activation attempt expired before Coding MCP restarted.' } });
        return;
      }
      this.updateIntent(state, intent, Number(record.expires_at_unix_ms || 0) > this.now()
        ? { state: 'awaiting', error: null }
        : { state: 'deferred', current_operation_id: null, error: { code: 'ACTIVATION_REQUEST_EXPIRED', message: 'Activation attempt expired before completion.' } });
      return;
    }
    const error = record?.error || { code: 'AUTO_ACTIVATION_FAILED', message: 'Activation did not complete.' };
    if (recordState === 'refused' && RETRYABLE_REFUSALS.has(String(error.code || '')) && intent.attempt < MAX_AUTO_ATTEMPTS) this.updateIntent(state, intent, { state: 'deferred', current_operation_id: null, error });
    else this.updateIntent(state, intent, { state: recordState === 'refused' ? 'blocked' : 'failed', current_operation_id: null, error });
  }

  async processIntent(state, intent) {
    if (['blocked', 'failed', 'superseded'].includes(intent.state)) return;
    if (intent.state === 'awaiting' && intent.current_operation_id) {
      const record = this.activation.status(intent.current_operation_id);
      if (record?.state === 'accepted' && record?.result?.component_stopped === true) {
        try {
          const now = this.now();
          const resumed = await this.activation.activate({
            operation_id: intent.current_operation_id,
            component: intent.component,
            requested_at_unix_ms: Number(record.requested_at_unix_ms || now),
            expires_at_unix_ms: Number(record.expires_at_unix_ms || now + ACTIVATION_REQUEST_TTL_MS),
            expected_disk_revision: intent.expected_revision,
            allow_acceptance_pending: false,
            source_checkpoint: {
              checkpoint_id: intent.checkpoint_id,
              run_id: intent.run_id,
              wave_id: intent.wave_id,
              proof_fingerprint: intent.proof_fingerprint,
              git_head: intent.accepted_head
            }
          });
          this.applyRecord(state, intent, resumed);
        } catch (error) {
          const code = String(error?.code || 'AUTO_ACTIVATION_RESUME_FAILED');
          this.updateIntent(state, intent, RETRYABLE_REFUSALS.has(code)
            ? { state: 'deferred', current_operation_id: null, error: { code, message: String(error?.message || error) } }
            : { state: 'failed', current_operation_id: null, error: { code, message: String(error?.message || error) } });
        }
        return;
      }
      this.applyRecord(state, intent, record); return;
    }
    let trusted;
    try { trusted = await this.revalidate(intent); }
    catch (error) { this.updateIntent(state, intent, { state: 'blocked', current_operation_id: null, error: { code: String(error?.code || 'AUTO_ACTIVATION_REVALIDATION_FAILED'), message: String(error?.message || error), files: error?.details?.files || undefined } }); return; }
    this.updateIntent(state, intent, { trusted_head: trusted.head, trusted_receipts: trusted.receipts });
    const attempt = Number(intent.attempt || 0) + 1;
    if (attempt > MAX_AUTO_ATTEMPTS) { this.updateIntent(state, intent, { state: 'blocked', error: { code: 'AUTO_ACTIVATION_RETRY_EXHAUSTED', message: 'Automatic activation exceeded the bounded retry limit.' } }); return; }
    const now = this.now();
    const request = {
      operation_id: autoOperationId(intent, attempt),
      component: intent.component,
      requested_at_unix_ms: now,
      expires_at_unix_ms: now + ACTIVATION_REQUEST_TTL_MS,
      expected_disk_revision: intent.expected_revision,
      allow_acceptance_pending: false,
      source_checkpoint: {
        checkpoint_id: intent.checkpoint_id,
        run_id: intent.run_id,
        wave_id: intent.wave_id,
        proof_fingerprint: intent.proof_fingerprint,
        git_head: intent.accepted_head
      }
    };
    let preflight;
    try { preflight = await this.activation.preflight(request); }
    catch (error) {
      const code = String(error?.code || 'AUTO_ACTIVATION_PREFLIGHT_FAILED');
      this.updateIntent(state, intent, RETRYABLE_REFUSALS.has(code)
        ? { state: 'deferred', attempt, current_operation_id: null, error: { code, message: String(error?.message || 'Automatic activation preflight was deferred.') } }
        : { state: 'blocked', attempt, current_operation_id: null, error: { code, message: String(error?.message || 'Automatic activation preflight failed.') } });
      return;
    }
    const lifecycleDecision = preflight?.lifecycle_decision || preflight?.runtime?.lifecycle_decision || null;
    if (lifecycleDecision) this.updateIntent(state, intent, { lifecycle_decision: lifecycleDecision });
    if (!preflight.safe) {
      this.updateIntent(state, intent, RETRYABLE_REFUSALS.has(String(preflight.code || ''))
        ? { state: 'deferred', attempt, current_operation_id: null, error: { code: preflight.code, message: `Activation deferred: ${preflight.runtime?.reason || preflight.code}` } }
        : { state: 'blocked', attempt, current_operation_id: null, error: { code: preflight.code || 'AUTO_ACTIVATION_PREFLIGHT_FAILED', message: 'Automatic activation preflight was refused.' } });
      return;
    }
    this.updateIntent(state, intent, {
      state: 'awaiting',
      attempt,
      activation_operation_id: request.operation_id,
      current_operation_id: request.operation_id,
      error: null
    });
    try { this.applyRecord(state, intent, await this.activation.activate(request)); }
    catch (error) {
      const code = String(error?.code || 'AUTO_ACTIVATION_FAILED');
      this.updateIntent(state, intent, RETRYABLE_REFUSALS.has(code)
        ? { state: 'deferred', current_operation_id: null, error: { code, message: String(error?.message || 'Automatic activation was deferred.') } }
        : { state: 'failed', current_operation_id: null, error: { code, message: String(error?.message || 'Automatic activation failed.') } });
    }
  }

  async tick() {
    if (this.processing) return false;
    this.processing = true;
    try {
      await this.discover();
      const state = this.loadState();
      const active = state.intents.filter((item) => item.checkpoint_id === state.active_checkpoint_id);
      const intent = active.find((item) => !TERMINAL_INTENT_STATES.has(String(item.state || '')));
      if (intent) await this.processIntent(state, intent);
      this.lastError = null; return true;
    } catch (error) {
      this.lastError = { code: String(error?.code || 'AUTO_ACTIVATION_FAILED').slice(0, 80), message: String(error?.message || error).slice(0, 500) };
      this.log?.warn?.(this.lastError.message, { stage: 'accepted-code-auto-activation', code: this.lastError.code });
      return false;
    } finally { this.processing = false; }
  }
}

module.exports = {
  RecoveryActionStore,
  AcceptedCodeActivationController,
  requestFingerprint,
  workspaceIdentity,
  gitStatus,
  parseGitStatus,
  fingerprintPaths,
  readAcceptedCheckpoint,
  readAcceptedCheckpoints,
  acceptedReceipts,
  evaluateActivationEligibility,
  OPERATION_ID_PATTERN,
  MAX_ACTIONS
};
