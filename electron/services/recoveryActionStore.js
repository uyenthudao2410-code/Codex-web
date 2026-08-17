const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { execFile } = require('node:child_process');
const { promisify } = require('node:util');
const { DatabaseSync } = require('node:sqlite');
const { readJson, writeJsonAtomic } = require('./jsonStore');
const { componentOwnsPath } = require('./componentRevision');

const execFileAsync = promisify(execFile);

const STORE_VERSION = 1;
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
const MAX_TRUST_RECEIPTS = 512;
const MAX_TRUST_RECEIPT_FILE_BYTES = 16 * 1024 * 1024;
const MAX_TRUST_RECEIPT_TOTAL_BYTES = 64 * 1024 * 1024;
const COMPONENT_ORDER = Object.freeze(['recovery_host', 'coding_mcp', 'electron_ui']);
const RETRYABLE_REFUSALS = new Set(['RUNTIME_BUSY', 'ORCHESTRATION_STATE_UNCERTAIN', 'ACCEPTANCE_PENDING', 'ACTIVATION_REQUEST_EXPIRED']);
const TERMINAL_INTENT_STATES = new Set(['completed', 'blocked', 'failed', 'superseded']);
const HEX64 = /^[a-f0-9]{64}$/;
const GIT_OBJECT_ID = /^[a-f0-9]{40,64}$/;

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

  begin(request) {
    const replay = this.replay(request);
    if (replay) return { created: false, record: replay };
    const now = this.now();
    const expiresAt = Number(request?.expires_at_unix_ms || 0);
    if (!Number.isSafeInteger(expiresAt) || expiresAt <= now) {
      throw actionError('ACTIVATION_REQUEST_EXPIRED', 'The activation request has expired.');
    }
    const operationId = String(request.operation_id);
    const fingerprint = requestFingerprint(request);
    const store = this.load();
    const record = {
      version: 1,
      operation_id: operationId,
      component: request.component,
      action: 'activate_update',
      request_fingerprint: fingerprint,
      expected_disk_revision: request.expected_disk_revision,
      allow_acceptance_pending: request.allow_acceptance_pending === true,
      state: 'accepted',
      created_at: new Date(now).toISOString(),
      created_at_unix_ms: now,
      expires_at_unix_ms: expiresAt,
      updated_at: new Date(now).toISOString(),
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
  let branch = '';
  const entries = [];
  for (const line of String(output || '').split(/\r?\n/)) {
    if (line.startsWith('## ')) {
      const value = line.slice(3);
      branch = (value.includes('...') ? value.split('...', 1)[0] : value).trim();
      continue;
    }
    if (!line) continue;
    let pathText = line.slice(3);
    if (pathText.includes(' -> ')) pathText = pathText.split(' -> ', 2)[1];
    entries.push({ path: String(pathText || '').replace(/\\/g, '/'), index_status: line[0] || '', worktree_status: line[1] || '' });
    if (entries.length > MAX_DIRTY_ENTRIES) throw actionError('AUTO_ACTIVATION_GIT_TOO_LARGE', 'Git status exceeded the bounded activation limit.');
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

async function gitStatus(workspace, forceUntracked = false) {
  const root = String((await runGit(workspace, ['rev-parse', '--show-toplevel'])).stdout || '').trim();
  if (!root || !samePath(root, workspace)) throw actionError('AUTO_ACTIVATION_WORKSPACE_MISMATCH', 'Automatic activation requires the configured workspace Git root.');
  const args = ['status', '--porcelain=v1', '-b'];
  if (forceUntracked) args.push('--untracked-files=all');
  const parsed = parseGitStatus((await runGit(workspace, args)).stdout);
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
  for (const relative of [...new Set(entries.map((item) => item.path).filter(Boolean))].sort()) {
    digest.update(relative, 'utf8');
    const target = path.resolve(workspace, ...relative.split('/'));
    const outside = path.relative(workspace, target);
    if (outside.startsWith('..') || path.isAbsolute(outside)) { digest.update('<outside>', 'utf8'); continue; }
    try {
      const stat = fs.statSync(target);
      digest.update(stat.isFile() ? fs.readFileSync(target) : Buffer.from('<non-file>'));
    } catch (error) {
      digest.update(error?.code === 'ENOENT' ? '<missing>' : `<error:${String(error?.name || 'Error')}>`, 'utf8');
    }
  }
  digest.update(JSON.stringify(stableValue({ head, branch, entries })), 'utf8');
  return digest.digest('hex');
}

async function workspaceIdentity(workspace) {
  const status = await gitStatus(workspace, false);
  const entries = status.entries.filter((item) => item.path && !item.path.startsWith('.coding-tools/'));
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
    return database.prepare(`SELECT checkpoint_id,run_id,wave_id,git_head,proof_fingerprint,created_at,metadata_json FROM checkpoints WHERE status='accepted' ORDER BY created_at DESC,checkpoint_id DESC LIMIT ?`).all(bounded).reverse().map(parseCheckpointRow);
  } catch (error) {
    throw actionError('AUTO_ACTIVATION_LEDGER_UNAVAILABLE', 'Accepted orchestration checkpoint could not be read safely.', { sqlite_code: String(error?.code || '') });
  } finally {
    try { database?.close(); } catch { /* read-only handle cleanup */ }
  }
}

function readAcceptedCheckpoint(workspace, runId, waveId) {
  return readAcceptedCheckpoints(workspace).slice().reverse().find((item) => String(item.run_id) === String(runId) && String(item.wave_id) === String(waveId)) || null;
}

function normalizeReceipt(item) {
  if (!item || typeof item !== 'object') return null;
  const relative = normalizeRelative(item.path);
  if (!relative || relative.startsWith('.coding-tools/')) return null;
  const state = String(item.state || '');
  if (state === 'missing') return { path: relative, state, sha256: null, size_bytes: 0 };
  const sha256 = String(item.sha256 || '').toLowerCase();
  const sizeBytes = Number(item.size_bytes);
  if (state !== 'file' || !HEX64.test(sha256) || !Number.isSafeInteger(sizeBytes) || sizeBytes < 0 || sizeBytes > MAX_TRUST_RECEIPT_FILE_BYTES) return null;
  return { path: relative, state, sha256, size_bytes: sizeBytes };
}

function acceptedReceipts(checkpoint) {
  const value = checkpoint?.metadata?.accepted_files;
  if (!value || Number(value.schema_version) !== 1 || value.complete !== true || !Array.isArray(value.files) || value.files.length > MAX_TRUST_RECEIPTS) return null;
  const receipts = [];
  const seen = new Set();
  let totalBytes = 0;
  for (const item of value.files) {
    const receipt = normalizeReceipt(item);
    if (!receipt || seen.has(receipt.path)) return null;
    seen.add(receipt.path);
    totalBytes += receipt.size_bytes;
    if (totalBytes > MAX_TRUST_RECEIPT_TOTAL_BYTES) return null;
    receipts.push(receipt);
  }
  if (Number(value.count) !== receipts.length) return null;
  return receipts;
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
    .filter(({ checkpoint, receipts }) => String(checkpoint.git_head || '') === String(head || '')
      && HEX64.test(String(checkpoint.proof_fingerprint || '').toLowerCase()) && receipts !== null);
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
    intents,
    updated_at: String(source.updated_at || new Date().toISOString())
  };
}

function autoOperationId(intent, attempt) {
  const digest = crypto.createHash('sha256').update(`${intent.checkpoint_id}:${intent.component}:${attempt}`).digest('hex');
  return `auto_${digest.slice(0, 48)}`;
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
    return { trust_model: 'running_baseline_accepted_receipts_v2', continuity_mode: 'detached_runtime_children_v1', running: Boolean(this.timer), processing: this.processing, pending: count('pending'), deferred: count('deferred'), awaiting: count('awaiting'), blocked: count('blocked'), failed: count('failed'), completed: count('completed'), baseline_head: state.baseline?.head || null, processed_checkpoints: state.processed_checkpoint_ids.length, last_error: this.lastError };
  }
  start() { if (this.timer) return this.status(); this.timer = setInterval(() => { this.tick().catch(() => {}); }, this.intervalMs); this.timer.unref(); setImmediate(() => { this.tick().catch(() => {}); }); return this.status(); }
  stop() { if (this.timer) clearInterval(this.timer); this.timer = null; return true; }

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

  candidate(checkpoints, state, head) {
    const processed = new Set(state.processed_checkpoint_ids);
    return trustedAcceptedCheckpoints(checkpoints, head).find(({ checkpoint, receipts }) => !processed.has(String(checkpoint.checkpoint_id)) && receipts.length) || null;
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
    const candidate = this.candidate(checkpoints, state, forced.head);
    if (!candidate) return false;
    const checkpointId = String(candidate.checkpoint.checkpoint_id);
    const targets = COMPONENT_ORDER.filter((component) => candidate.receipts.some((receipt) => componentOwnsPath(component, receipt.path)));
    if (!targets.length) {
      state.processed_checkpoint_ids = [...new Set([...state.processed_checkpoint_ids, checkpointId])].slice(-MAX_PROCESSED_CHECKPOINTS);
      this.saveState(state);
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
    const trusted = trustedAcceptedCheckpoints(checkpoints, forced.head);
    const checkpoint = trusted.find((item) => String(item.checkpoint.checkpoint_id) === intent.checkpoint_id)?.checkpoint || null;
    if (!checkpoint || String(checkpoint.proof_fingerprint).toLowerCase() !== intent.proof_fingerprint || String(checkpoint.git_head || '') !== intent.accepted_head) throw actionError('ACCEPTED_CHECKPOINT_CHANGED', 'Accepted checkpoint identity changed before activation.');
    const accepted = acceptedReceiptUnion(checkpoints, forced.head);
    const gate = await this.componentGate(workspace, intent.component, baseline, accepted, forced);
    if (gate.error) throw actionError(gate.error.code, gate.error.message, { files: gate.error.files });
    const diskRevision = String(this.revisions.disk(intent.component, { force: true }).revision || '').toLowerCase();
    if (diskRevision !== intent.expected_revision) throw actionError('REVISION_CHANGED', 'Target component revision changed after final acceptance.');
    return { head: String(forced.head || ''), receipts: gate.receipts };
  }

  updateIntent(state, intent, patch) { Object.assign(intent, patch, { updated_at: new Date(this.now()).toISOString() }); this.saveState(state); }
  advanceBaseline(state, intent) {
    if (!state.baseline || !GIT_OBJECT_ID.test(String(intent.trusted_head || '').toLowerCase()) || !Array.isArray(intent.trusted_receipts)) return false;
    const row = state.baseline.components?.[intent.component];
    if (!row || !HEX64.test(String(intent.expected_revision || '').toLowerCase())) return false;
    row.head = String(intent.trusted_head).toLowerCase();
    row.revision = String(intent.expected_revision).toLowerCase();
    row.receipts = intent.trusted_receipts.map(normalizeReceipt).filter(Boolean);
    const rowHeads = COMPONENT_ORDER.map((component) => String(state.baseline.components?.[component]?.head || ''));
    if (rowHeads.length && rowHeads.every((head) => head === row.head)) state.baseline.head = row.head;
    state.baseline.updated_at = new Date(this.now()).toISOString();
    return true;
  }
  applyRecord(state, intent, record) {
    const recordState = String(record?.state || '');
    if (recordState === 'completed') {
      if (!this.advanceBaseline(state, intent)) {
        this.updateIntent(state, intent, { state: 'failed', current_operation_id: null, error: { code: 'AUTO_ACTIVATION_BASELINE_ADVANCE_FAILED', message: 'Activation completed but its trusted running baseline could not be advanced.' }, result: record.result || null });
        return;
      }
      this.updateIntent(state, intent, { state: 'completed', current_operation_id: null, error: null, result: record.result || null }); return;
    }
    if (recordState === 'accepted') {
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
      this.applyRecord(state, intent, record); return;
    }
    let trusted;
    try { trusted = await this.revalidate(intent); }
    catch (error) { this.updateIntent(state, intent, { state: 'blocked', current_operation_id: null, error: { code: String(error?.code || 'AUTO_ACTIVATION_REVALIDATION_FAILED'), message: String(error?.message || error), files: error?.details?.files || undefined } }); return; }
    this.updateIntent(state, intent, { trusted_head: trusted.head, trusted_receipts: trusted.receipts });
    const attempt = Number(intent.attempt || 0) + 1;
    if (attempt > MAX_AUTO_ATTEMPTS) { this.updateIntent(state, intent, { state: 'blocked', error: { code: 'AUTO_ACTIVATION_RETRY_EXHAUSTED', message: 'Automatic activation exceeded the bounded retry limit.' } }); return; }
    const now = this.now();
    const request = { operation_id: autoOperationId(intent, attempt), component: intent.component, requested_at_unix_ms: now, expires_at_unix_ms: now + ACTIVATION_REQUEST_TTL_MS, expected_disk_revision: intent.expected_revision, allow_acceptance_pending: false };
    const preflight = await this.activation.preflight(request);
    if (preflight.code === 'ALREADY_CURRENT') {
      if (!this.advanceBaseline(state, intent)) { this.updateIntent(state, intent, { state: 'failed', error: { code: 'AUTO_ACTIVATION_BASELINE_ADVANCE_FAILED', message: 'Current component baseline could not be advanced.' } }); return; }
      this.updateIntent(state, intent, { state: 'completed', error: null, result: { activated: false, already_current: true, revision: intent.expected_revision } }); return;
    }
    if (!preflight.safe) {
      this.updateIntent(state, intent, RETRYABLE_REFUSALS.has(String(preflight.code || ''))
        ? { state: 'deferred', error: { code: preflight.code, message: `Activation deferred: ${preflight.runtime?.reason || preflight.code}` } }
        : { state: 'blocked', error: { code: preflight.code || 'AUTO_ACTIVATION_PREFLIGHT_FAILED', message: 'Automatic activation preflight was refused.' } });
      return;
    }
    this.updateIntent(state, intent, { state: 'awaiting', attempt, current_operation_id: request.operation_id, error: null });
    this.applyRecord(state, intent, await this.activation.activate(request));
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
  OPERATION_ID_PATTERN,
  MAX_ACTIONS
};
