const crypto = require('node:crypto');
const { readJson, writeJsonAtomic } = require('./jsonStore');

const STORE_VERSION = 1;
const MAX_ACTIONS = 64;
const MAX_OPERATION_AGE_MS = 24 * 60 * 60 * 1000;
const OPERATION_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/;

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

module.exports = {
  RecoveryActionStore,
  requestFingerprint,
  OPERATION_ID_PATTERN,
  MAX_ACTIONS
};
