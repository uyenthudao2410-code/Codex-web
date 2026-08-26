const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { writeJsonAtomic } = require('./jsonStore');

// This file is deliberately separate from the orchestration ledger.  It is a
// small recovery-supervisor projection: the ledger remains the durable source
// of execution truth, while this store records which runtime activation is
// currently being assembled and whether its final admission gate is open.
const STORE_VERSION = 1;
const DEFAULT_MAX_HISTORY = 32;
const MAX_HISTORY = 256;
const MAX_TRANSITIONS = 64;
const MAX_COMPONENTS = 32;
const MAX_DETAIL_BYTES = 128 * 1024;
const MAX_ID_LENGTH = 128;
const DEFAULT_LOCK_TIMEOUT_MS = 5_000;
const DEFAULT_LOCK_STALE_MS = 60_000;
const LOCK_RETRY_MS = 20;
const MAX_OWNER_PID = 0x7fffffff;

const EPOCH_STATES = Object.freeze([
  'PREPARING',
  'ADMISSION_CLOSED',
  'FROZEN',
  'STOPPING',
  'HANDOFF',
  'STARTING',
  'VERIFYING',
  'READY',
  'FAILED'
]);
const ACTIVE_STATES = new Set(EPOCH_STATES.slice(0, -2));
const TERMINAL_STATES = new Set(['READY', 'FAILED']);
const STATE_ORDER = new Map(EPOCH_STATES.map((state, index) => [state, index]));
const MODE_VALUES = new Set(['full_clean_activation', 'soft_recovery']);
// Keep this aligned with the process/argv contract: the store accepts any
// non-empty allowlisted identity, while generated identities remain much
// stronger (timestamp plus 128 bits of randomness).
const ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/;
const OPERATION_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/;

function sleepSync(milliseconds) {
  const view = new Int32Array(new SharedArrayBuffer(4));
  Atomics.wait(view, 0, 0, Math.max(1, Number(milliseconds) || 1));
}

function processIsAlive(pid) {
  const value = Number(pid);
  if (!Number.isSafeInteger(value) || value <= 0) return false;
  try {
    process.kill(value, 0);
    return true;
  } catch (error) {
    // EPERM means the process exists but is not signalable.  Treat it as live
    // so a stale-lock cleanup can never remove a live owner's lock.
    return error?.code === 'EPERM';
  }
}

function epochError(code, message, details = {}) {
  return Object.assign(new Error(message), { code, details });
}

function clone(value) {
  if (value === undefined) return undefined;
  return JSON.parse(JSON.stringify(value));
}

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function isPlainObject(value) {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}

function boundedClone(value, label, maxBytes = MAX_DETAIL_BYTES) {
  if (value === undefined || value === null) return null;
  let encoded;
  try {
    encoded = JSON.stringify(value);
  } catch {
    throw epochError('ACTIVATION_EPOCH_VALUE_INVALID', `${label} must be JSON serializable.`);
  }
  if (typeof encoded !== 'string' || Buffer.byteLength(encoded, 'utf8') > maxBytes) {
    throw epochError('ACTIVATION_EPOCH_VALUE_TOO_LARGE', `${label} exceeds the bounded activation-epoch limit.`);
  }
  return JSON.parse(encoded);
}

function text(value, label = 'value', maxLength = MAX_ID_LENGTH) {
  const normalized = String(value ?? '').trim();
  if (!normalized || normalized.length > maxLength) {
    throw epochError('ACTIVATION_EPOCH_VALUE_INVALID', `${label} is invalid.`);
  }
  return normalized;
}

function optionalText(value, label, maxLength = MAX_ID_LENGTH) {
  if (value === undefined || value === null || value === '') return null;
  return text(value, label, maxLength);
}

function integerOr(value, fallback, label) {
  const result = value === undefined || value === null ? fallback : Number(value);
  if (!Number.isSafeInteger(result) || result < 0) {
    throw epochError('ACTIVATION_EPOCH_VALUE_INVALID', `${label} must be a non-negative safe integer.`);
  }
  return result;
}

function optionalInteger(value, label) {
  if (value === undefined || value === null || value === '') return null;
  return integerOr(value, null, label);
}

function timestampPair(unixValue, isoValue, label, { required = false } = {}) {
  const hasUnix = !(unixValue === undefined || unixValue === null || unixValue === '');
  const hasIso = !(isoValue === undefined || isoValue === null || isoValue === '');
  if (!hasUnix && !hasIso) {
    if (required) throw epochError('ACTIVATION_EPOCH_VALUE_INVALID', `${label} is required.`);
    return { unixMs: null, iso: null };
  }
  const unixMs = hasUnix ? integerOr(unixValue, null, `${label}_unix_ms`) : null;
  const parsedIso = hasIso ? Date.parse(String(isoValue)) : null;
  if (hasIso && (!Number.isFinite(parsedIso) || parsedIso < 0)) {
    throw epochError('ACTIVATION_EPOCH_VALUE_INVALID', `${label} is invalid.`);
  }
  if (unixMs !== null && parsedIso !== null && unixMs !== parsedIso) {
    throw epochError('ACTIVATION_EPOCH_VALUE_INVALID', `${label} timestamp fields disagree.`);
  }
  const resolved = unixMs === null ? parsedIso : unixMs;
  return { unixMs: resolved, iso: hasIso ? String(isoValue) : isoAt(resolved) };
}

function optionalOwner(value, label = 'owner_instance_id') {
  if (value === undefined || value === null || value === '') return null;
  const normalized = text(value, label);
  if (!ID_PATTERN.test(normalized)) {
    throw epochError('ACTIVATION_EPOCH_OWNER_INVALID', `${label} has an invalid format.`);
  }
  return normalized;
}

function optionalPid(value, label = 'owner_pid') {
  if (value === undefined || value === null || value === '') return null;
  const pid = Number(value);
  if (!Number.isSafeInteger(pid) || pid <= 0 || pid > MAX_OWNER_PID) {
    throw epochError('ACTIVATION_EPOCH_OWNER_INVALID', `${label} must be a valid process id.`);
  }
  return pid;
}

function isoAt(unixMs) {
  return new Date(unixMs).toISOString();
}

function resolveStoreFile(paths, explicitFile) {
  if (explicitFile) return path.resolve(String(explicitFile));
  if (paths && typeof paths.activationEpochFile === 'function') {
    return path.resolve(String(paths.activationEpochFile()));
  }
  if (paths && typeof paths.dataRoot === 'function') {
    return path.resolve(path.join(String(paths.dataRoot()), 'activation-epoch.json'));
  }
  throw epochError('ACTIVATION_EPOCH_PATH_REQUIRED', 'Activation epoch store requires paths.dataRoot() or an explicit file.');
}

function generatedEpochId(now) {
  // The timestamp is useful when inspecting a crash/recovery directory; the
  // random suffix is the authority-bearing identity and prevents collisions.
  return `activation-${now.toString(36)}-${crypto.randomBytes(16).toString('hex')}`;
}

function normalizeState(value, { allowNull = false } = {}) {
  if (value === undefined || value === null || value === '') {
    if (allowNull) return null;
    throw epochError('ACTIVATION_EPOCH_STATE_INVALID', 'Activation epoch state is required.');
  }
  const state = String(value).trim().toUpperCase().replace(/[ -]+/g, '_');
  if (!EPOCH_STATES.includes(state)) {
    throw epochError('ACTIVATION_EPOCH_STATE_INVALID', `Unknown activation epoch state: ${state}.`);
  }
  return state;
}

function normalizeMode(value) {
  const mode = String(value || 'full_clean_activation').trim().toLowerCase();
  if (!MODE_VALUES.has(mode)) {
    throw epochError('ACTIVATION_EPOCH_MODE_INVALID', 'Activation epoch mode is not supported.');
  }
  return mode;
}

function normalizeId(value, label = 'activation_epoch_id') {
  const normalized = text(value, label);
  if (!ID_PATTERN.test(normalized)) {
    throw epochError('ACTIVATION_EPOCH_ID_INVALID', `${label} has an invalid format.`);
  }
  return normalized;
}

function normalizeOperationId(value) {
  const normalized = optionalText(value, 'operation_id');
  if (normalized && !OPERATION_ID_PATTERN.test(normalized)) {
    throw epochError('ACTIVATION_EPOCH_OPERATION_ID_INVALID', 'operation_id has an invalid format.');
  }
  return normalized;
}

function normalizeComponents(value) {
  if (value === undefined || value === null) return [];
  if (!Array.isArray(value) || value.length > MAX_COMPONENTS) {
    throw epochError('ACTIVATION_EPOCH_COMPONENTS_INVALID', 'components must be a bounded array.');
  }
  const result = [];
  const seen = new Set();
  for (const item of value) {
    const component = text(item, 'component', 96);
    if (!/^[A-Za-z][A-Za-z0-9_-]{0,95}$/.test(component)) {
      throw epochError('ACTIVATION_EPOCH_COMPONENTS_INVALID', 'components contains an invalid name.');
    }
    if (!seen.has(component)) {
      seen.add(component);
      result.push(component);
    }
  }
  return result;
}

function normalizeError(value) {
  if (value === undefined || value === null) return null;
  if (value instanceof Error) {
    return {
      code: String(value.code || 'ACTIVATION_EPOCH_FAILED').slice(0, 96),
      message: String(value.message || 'Activation epoch failed.').slice(0, 2000),
      details: boundedClone(value.details || null, 'error.details')
    };
  }
  if (typeof value === 'string') {
    return { code: 'ACTIVATION_EPOCH_FAILED', message: value.slice(0, 2000), details: null };
  }
  if (!isPlainObject(value)) {
    throw epochError('ACTIVATION_EPOCH_ERROR_INVALID', 'Activation epoch error must be an Error, string, or object.');
  }
  return {
    code: String(value.code || 'ACTIVATION_EPOCH_FAILED').slice(0, 96),
    message: String(value.message || 'Activation epoch failed.').slice(0, 2000),
    details: boundedClone(value.details || null, 'error.details')
  };
}

function canonicalIntent(input) {
  const value = isPlainObject(input) ? input : {};
  const metadata = boundedClone(value.metadata || null, 'metadata');
  const componentEvidence = boundedClone(value.component_evidence || null, 'component_evidence');
  const ownerFromEvidence = componentEvidence?.recovery_host?.instance_id;
  const ownerFromMetadata = metadata?.owner_instance_id || metadata?.ownerInstanceId;
  const expiresFromMetadata = metadata?.expires_at_unix_ms ?? metadata?.expiresAtUnixMs;
  return {
    operation_id: normalizeOperationId(value.operation_id),
    mode: normalizeMode(value.mode),
    components: normalizeComponents(value.components || value.expected_components),
    source_checkpoint: boundedClone(value.source_checkpoint || null, 'source_checkpoint'),
    ledger_snapshot: boundedClone(value.ledger_snapshot || null, 'ledger_snapshot'),
    // These fields are part of the creation request.  Keeping them in the
    // fingerprint prevents an idempotent retry from silently reusing an epoch
    // with a different revision/identity baseline.
    component_revisions: boundedClone(value.component_revisions || null, 'component_revisions'),
    component_evidence: componentEvidence,
    owner_instance_id: optionalOwner(value.owner_instance_id ?? value.ownerInstanceId ?? ownerFromMetadata ?? ownerFromEvidence),
    owner_pid: optionalPid(value.owner_pid ?? value.ownerPid ?? metadata?.owner_pid ?? metadata?.ownerPid),
    expires_at_unix_ms: optionalInteger(value.expires_at_unix_ms ?? value.expiresAtUnixMs ?? expiresFromMetadata, 'expires_at_unix_ms'),
    metadata
  };
}

function requestFingerprint(intent) {
  return crypto.createHash('sha256').update(canonicalJson(intent)).digest('hex');
}

function normalizeTransition(value) {
  const source = isPlainObject(value) ? value : {};
  const state = normalizeState(source.state || source.phase);
  const at = source.at || source.at_iso || source.timestamp;
  const observedAt = at ? String(at) : null;
  if (observedAt && !Number.isFinite(Date.parse(observedAt))) {
    throw epochError('ACTIVATION_EPOCH_VALUE_INVALID', 'Transition timestamp is invalid.');
  }
  return {
    state,
    at: observedAt,
    reason: source.reason === undefined || source.reason === null ? null : String(source.reason).slice(0, 500)
  };
}

function compactTransitions(transitions) {
  if (!Array.isArray(transitions) || transitions.length <= MAX_TRANSITIONS) return transitions;
  // Preserve the creation and stop boundaries while retaining the newest
  // bounded tail.  READY is only legal after an explicit STOPPING transition;
  // dropping that transition during compaction would make a valid long-lived
  // epoch impossible to complete (or would force the reader to trust a state
  // bit without its durable transition evidence).
  const keep = new Set([0]);
  const stoppingIndex = transitions.findIndex((item) => {
    try { return normalizeState(item?.state || item?.phase) === 'STOPPING'; } catch { return false; }
  });
  if (stoppingIndex > 0) keep.add(stoppingIndex);
  for (let index = transitions.length - 1; index >= 0 && keep.size < MAX_TRANSITIONS; index -= 1) {
    keep.add(index);
  }
  return [...keep].sort((left, right) => left - right).map((index) => transitions[index]);
}

function storeError(message, details = {}) {
  return epochError('ACTIVATION_EPOCH_STORE_INVALID', message, details);
}

function sameCanonical(left, right) {
  return canonicalJson(left) === canonicalJson(right);
}

// A READY transition is the durable admission boundary.  Keep this validator
// generic enough for the store to remain independent of component code, while
// requiring the pieces that prove a full-clean census actually happened.
function validateReadyVerification(verification, epochId, record = null) {
  if (!isPlainObject(verification) || verification.verified !== true) {
    throw epochError('ACTIVATION_EPOCH_READY_PROOF_REQUIRED', 'ready() requires an explicit verified=true final census.');
  }
  if (verification.activation_epoch_id === undefined || verification.activation_epoch_id === null || verification.activation_epoch_id === '') {
    throw epochError('ACTIVATION_EPOCH_READY_PROOF_REQUIRED', 'Final verification must identify its activation epoch.');
  }
  if (normalizeId(verification.activation_epoch_id) !== epochId) {
    throw epochError('ACTIVATION_EPOCH_ID_MISMATCH', 'Final verification belongs to another activation epoch.');
  }
  const census = verification.final_census;
  if (!isPlainObject(census)) {
    throw epochError('ACTIVATION_EPOCH_READY_PROOF_REQUIRED', 'Final verification must include a final_census object.');
  }
  const censusEpoch = census.activation_epoch_id ?? census.activationEpochId;
  if (censusEpoch !== undefined && censusEpoch !== null && censusEpoch !== '') {
    if (normalizeId(censusEpoch) !== epochId) {
      throw epochError('ACTIVATION_EPOCH_ID_MISMATCH', 'Final census belongs to another activation epoch.');
    }
  }
  const pass = census.pass === true || census.verified === true;
  const legacyPass = census.all_components_same_epoch === true
    && census.connector_acknowledged === true;
  if (!pass && !legacyPass) {
    throw epochError('ACTIVATION_EPOCH_READY_PROOF_REQUIRED', 'Final census did not prove all components and connector admission are ready.');
  }
  if (census.pass === false || census.verified === false) {
    throw epochError('ACTIVATION_EPOCH_READY_PROOF_REQUIRED', 'Final census explicitly reports an incomplete activation.');
  }
  const negativeFlags = [
    'all_components_same_epoch', 'epoch_matches', 'workspace_matches', 'device_matches',
    'revision_matches', 'process_identity_verified', 'connector_acknowledged',
    'ui_verified', 'recovery_plane_verified'
  ];
  for (const flag of negativeFlags) {
    if (Object.prototype.hasOwnProperty.call(census, flag) && census[flag] !== true) {
      throw epochError('ACTIVATION_EPOCH_READY_PROOF_REQUIRED', `Final census flag ${flag} is not true.`);
    }
  }
  if (record && Array.isArray(record.components) && record.components.length > 0 && census.components && isPlainObject(census.components)) {
    for (const component of record.components) {
      const evidence = census.components[component];
      if (!isPlainObject(evidence)) {
        throw epochError('ACTIVATION_EPOCH_READY_PROOF_REQUIRED', `Final census is missing component evidence for ${component}.`);
      }
      const componentEpoch = evidence.activation_epoch_id ?? evidence.activationEpochId;
      if (componentEpoch !== undefined && componentEpoch !== null && componentEpoch !== ''
        && normalizeId(componentEpoch) !== epochId) {
        throw epochError('ACTIVATION_EPOCH_ID_MISMATCH', `Component ${component} belongs to another activation epoch.`);
      }
      if (evidence.ready === false || evidence.healthy === false || evidence.pass === false) {
        throw epochError('ACTIVATION_EPOCH_READY_PROOF_REQUIRED', `Component ${component} is not ready.`);
      }
    }
  }
  return census;
}

function normalizeRecord(value, { allowLegacy = false } = {}) {
  if (!isPlainObject(value)) throw storeError('Activation epoch record must be an object.');
  const version = Number(value.version ?? value.schema_version ?? STORE_VERSION);
  if (version !== STORE_VERSION && !(allowLegacy && version === 0)) {
    throw storeError('Activation epoch record version is unsupported.');
  }
  const id = normalizeId(value.activation_epoch_id || value.epoch_id);
  const state = normalizeState(value.state || value.phase);
  const mode = normalizeMode(value.mode);
  const created = timestampPair(value.created_at_unix_ms, value.created_at, 'created_at', { required: !allowLegacy });
  const updated = timestampPair(value.updated_at_unix_ms, value.updated_at, 'updated_at', { required: !allowLegacy });
  const createdAtUnixMs = created.unixMs === null ? 0 : created.unixMs;
  const updatedAtUnixMs = updated.unixMs === null ? createdAtUnixMs : updated.unixMs;
  if (updatedAtUnixMs < createdAtUnixMs) throw storeError('Activation epoch timestamps are not monotonic.');
  const expires = timestampPair(value.expires_at_unix_ms, value.expires_at, 'expires_at');
  const ownerInstanceId = optionalOwner(value.owner_instance_id ?? value.ownerInstanceId);
  const ownerPid = optionalPid(value.owner_pid ?? value.ownerPid);
  const revision = integerOr(value.revision ?? value.record_revision, 1, 'revision');
  if (revision < 1) throw storeError('Activation epoch revision is invalid.');
  const components = normalizeComponents(value.components || value.expected_components);
  const componentRevisions = boundedClone(value.component_revisions || null, 'component_revisions');
  const componentEvidence = boundedClone(value.component_evidence || null, 'component_evidence');
  const metadata = boundedClone(value.metadata || null, 'metadata');
  const verification = boundedClone(value.verification || null, 'verification');
  const transitionsInput = value.transitions;
  if (!Array.isArray(transitionsInput) || transitionsInput.length === 0) {
    if (!allowLegacy) throw storeError('Activation epoch transitions are required.');
  }
  if (Array.isArray(transitionsInput) && transitionsInput.length > MAX_TRANSITIONS && !allowLegacy) {
    throw storeError('Activation epoch transition history exceeds the bounded limit.');
  }
  const transitions = Array.isArray(transitionsInput)
    ? transitionsInput.slice(-MAX_TRANSITIONS).map(normalizeTransition)
    : [];
  let previousOrder = -1;
  let previousAt = -Infinity;
  for (const transition of transitions) {
    const order = STATE_ORDER.get(transition.state);
    if (order < previousOrder) throw storeError('Activation epoch transitions regress state.');
    previousOrder = order;
    if (!transition.at) {
      if (!allowLegacy) throw storeError('Activation epoch transition timestamp is required.');
    } else {
      const at = Date.parse(transition.at);
      if (!Number.isFinite(at) || at < previousAt || at > updatedAtUnixMs) {
        throw storeError('Activation epoch transition timestamps are not monotonic.');
      }
      previousAt = at;
    }
  }
  if (!allowLegacy && transitions[0]?.state !== 'PREPARING') {
    throw storeError('Activation epoch transition history must begin at PREPARING.');
  }
  if (!allowLegacy && transitions.at(-1)?.state !== state) {
    throw storeError('Activation epoch transition history does not match the current state.');
  }
  if (!allowLegacy && state === 'READY'
    && !transitions.some((transition) => transition.state === 'STOPPING')) {
    throw storeError('READY activation epoch requires an explicit STOPPING transition.');
  }
  const admissionState = value.admission_state === undefined || value.admission_state === null
    ? (allowLegacy ? (state === 'READY' ? 'OPEN' : 'CLOSED') : null)
    : String(value.admission_state).trim().toUpperCase();
  if (admissionState !== null && !['OPEN', 'CLOSED'].includes(admissionState)) {
    throw storeError('Activation epoch admission_state is invalid.');
  }
  if ((state === 'READY' && admissionState !== 'OPEN')
    || (state !== 'READY' && admissionState === 'OPEN')) {
    throw storeError('Activation epoch state and admission_state disagree.');
  }
  const started = timestampPair(value.started_at_unix_ms, value.started_at, 'started_at');
  const readyAt = timestampPair(value.ready_at_unix_ms, value.ready_at, 'ready_at');
  const failedAt = timestampPair(value.failed_at_unix_ms, value.failed_at, 'failed_at');
  if (!allowLegacy && state !== 'PREPARING' && started.unixMs === null) {
    throw storeError('Activation epoch started_at is required after PREPARING.');
  }
  if (!allowLegacy && state === 'READY' && readyAt.unixMs === null) {
    throw storeError('READY activation epoch requires ready_at.');
  }
  if (!allowLegacy && state === 'FAILED' && failedAt.unixMs === null) {
    throw storeError('FAILED activation epoch requires failed_at.');
  }
  const error = normalizeError(value.error);
  if (!allowLegacy && state === 'FAILED' && !error) throw storeError('FAILED activation epoch requires an error.');
  if (!allowLegacy && state !== 'FAILED' && error) throw storeError('Non-failed activation epoch cannot carry an error.');

  const requestIntent = isPlainObject(value.request_intent)
    ? canonicalIntent(value.request_intent)
    : (allowLegacy ? canonicalIntent({
      operation_id: value.operation_id,
      mode,
      components,
      source_checkpoint: value.source_checkpoint,
      ledger_snapshot: value.ledger_snapshot,
      component_revisions: componentRevisions,
      component_evidence: componentEvidence,
      owner_instance_id: ownerInstanceId,
      owner_pid: ownerPid,
      expires_at_unix_ms: expires.unixMs,
      metadata
    }) : null);
  if (!requestIntent) throw storeError('Activation epoch request_intent is required.');
  const requestFp = String(value.request_fingerprint || '').trim().toLowerCase() || null;
  if (!requestFp || !/^[a-f0-9]{64}$/.test(requestFp)) {
    if (!allowLegacy) throw storeError('Activation epoch request_fingerprint is required and invalid.');
  }
  const recordIntent = canonicalIntent({
    operation_id: value.operation_id,
    mode,
    components,
    source_checkpoint: value.source_checkpoint,
    ledger_snapshot: value.ledger_snapshot,
    component_revisions: componentRevisions,
    component_evidence: componentEvidence,
    owner_instance_id: ownerInstanceId,
    owner_pid: ownerPid,
    expires_at_unix_ms: expires.unixMs,
    metadata: requestIntent.metadata
  });
  if (!sameCanonical(recordIntent, requestIntent)) {
    throw storeError('Activation epoch immutable request fields do not match request_intent.');
  }
  if (requestFp && requestFp !== requestFingerprint(requestIntent)) {
    throw storeError('Activation epoch request_fingerprint does not match request_intent.');
  }
  if (!allowLegacy && state === 'READY') {
    validateReadyVerification(verification, id, { components });
  }
  if (!allowLegacy && expires.unixMs !== null && expires.unixMs < createdAtUnixMs) {
    throw storeError('Activation epoch expiry precedes creation.');
  }
  return {
    version: STORE_VERSION,
    activation_epoch_id: id,
    operation_id: normalizeOperationId(value.operation_id),
    mode,
    state,
    admission_state: admissionState || (state === 'READY' ? 'OPEN' : 'CLOSED'),
    components,
    source_checkpoint: boundedClone(value.source_checkpoint || null, 'source_checkpoint'),
    ledger_snapshot: boundedClone(value.ledger_snapshot || null, 'ledger_snapshot'),
    component_revisions: componentRevisions,
    component_evidence: componentEvidence,
    owner_instance_id: ownerInstanceId,
    owner_pid: ownerPid,
    expires_at: expires.iso,
    expires_at_unix_ms: expires.unixMs,
    verification,
    metadata,
    request_intent: requestIntent,
    request_fingerprint: requestFp || requestFingerprint(requestIntent),
    revision,
    created_at: created.iso || isoAt(createdAtUnixMs),
    created_at_unix_ms: createdAtUnixMs,
    updated_at: updated.iso || isoAt(updatedAtUnixMs),
    updated_at_unix_ms: updatedAtUnixMs,
    started_at: started.iso,
    started_at_unix_ms: started.unixMs,
    ready_at: readyAt.iso,
    ready_at_unix_ms: readyAt.unixMs,
    failed_at: failedAt.iso,
    failed_at_unix_ms: failedAt.unixMs,
    error,
    transitions
  };
}

function emptyStore() {
  return { version: STORE_VERSION, current: null, history: [] };
}

// Validate a complete snapshot independently of which file supplied it.  The
// primary file is the only authority; the backup is nevertheless evidence that
// must be structurally valid before we trust the snapshot as a coherent
// recovery projection.  We intentionally do not compare primary and backup
// contents because a valid backup is expected to lag by one atomic write.
function normalizeSnapshot(value, label = 'store') {
  if (!isPlainObject(value) || Number(value.version || 0) !== STORE_VERSION
    || (value.current !== null && !isPlainObject(value.current))
    || !Array.isArray(value.history)) {
    throw storeError(`Activation epoch ${label} schema is invalid.`);
  }
  if (value.history.length > MAX_HISTORY) {
    throw storeError(`Activation epoch ${label} history exceeds the bounded limit.`);
  }
  let current;
  let history;
  try {
    current = value.current === null ? null : normalizeRecord(value.current);
    history = value.history.map((item) => normalizeRecord(item));
  } catch (error) {
    if (error?.code === 'ACTIVATION_EPOCH_STORE_INVALID') throw error;
    throw storeError(`Activation epoch ${label} contains an invalid record.`, {
      code: error?.code || 'INVALID_RECORD'
    });
  }
  const ids = new Set();
  for (const item of [current, ...history]) {
    if (!item) continue;
    if (ids.has(item.activation_epoch_id)) {
      throw storeError(`Activation epoch ${label} contains duplicate identities.`);
    }
    ids.add(item.activation_epoch_id);
    if (item !== current && !TERMINAL_STATES.has(item.state)) {
      throw storeError(`Activation epoch ${label} history contains a non-terminal record.`);
    }
  }
  if (current === null && history.some((item) => ACTIVE_STATES.has(item.state))) {
    throw storeError(`Activation epoch ${label} has an active historical record without a current owner.`);
  }
  return { version: STORE_VERSION, current, history };
}

class ActivationEpochStore {
  constructor({
    paths = null,
    file = null,
    now = () => Date.now(),
    maxHistory = DEFAULT_MAX_HISTORY,
    lockTimeoutMs = DEFAULT_LOCK_TIMEOUT_MS,
    lockStaleMs = DEFAULT_LOCK_STALE_MS,
    ownerInstanceId = ''
  } = {}) {
    this.file = resolveStoreFile(paths, file);
    this.lockFile = `${this.file}.lock`;
    this.now = now;
    this.maxHistory = Math.max(1, Math.min(MAX_HISTORY, Number(maxHistory) || DEFAULT_MAX_HISTORY));
    this.lockTimeoutMs = Math.max(0, Number(lockTimeoutMs) || DEFAULT_LOCK_TIMEOUT_MS);
    this.lockStaleMs = Math.max(1_000, Number(lockStaleMs) || DEFAULT_LOCK_STALE_MS);
    this.ownerInstanceId = String(ownerInstanceId || '').trim() || `${process.pid}-${crypto.randomBytes(8).toString('hex')}`;
  }

  _acquireLock() {
    const startedAt = Date.now();
    const token = crypto.randomBytes(16).toString('hex');
    const descriptor = {
      version: 1,
      pid: process.pid,
      owner_instance_id: this.ownerInstanceId,
      token,
      acquired_at_unix_ms: startedAt
    };
    fs.mkdirSync(path.dirname(this.lockFile), { recursive: true });
    for (;;) {
      try {
        const handle = fs.openSync(this.lockFile, 'wx', 0o600);
        try {
          fs.writeFileSync(handle, `${JSON.stringify(descriptor)}\n`, 'utf8');
          fs.fsyncSync(handle);
        } finally {
          fs.closeSync(handle);
        }
        return descriptor;
      } catch (error) {
        if (error?.code !== 'EEXIST') throw error;
        let existing = null;
        let stat = null;
        try { existing = JSON.parse(fs.readFileSync(this.lockFile, 'utf8')); } catch { /* another owner is writing */ }
        try { stat = fs.statSync(this.lockFile); } catch { continue; }
        const acquiredAt = Number(existing?.acquired_at_unix_ms);
        const nowMs = Date.now();
        const age = Math.max(
          Number.isFinite(acquiredAt) ? Math.max(0, nowMs - acquiredAt) : 0,
          Math.max(0, nowMs - Number(stat.mtimeMs || nowMs))
        );
        const ownerPid = Number(existing?.pid);
        // Only reap a lock when the descriptor identifies a definitely dead
        // process and the lock has exceeded the bounded stale interval.  A
        // malformed or live descriptor is never deleted by a contender.
        if (age >= this.lockStaleMs && Number.isSafeInteger(ownerPid) && ownerPid > 0 && !processIsAlive(ownerPid)) {
          // Quarantine with an atomic rename instead of rmSync: two contenders
          // may both observe the same stale descriptor, and an unconditional
          // delete could otherwise remove a freshly acquired replacement lock.
          const staleFile = `${this.lockFile}.${process.pid}.${token}.stale`;
          try {
            fs.renameSync(this.lockFile, staleFile);
            fs.rmSync(staleFile, { force: true });
            continue;
          } catch { /* retain the lock and continue waiting */ }
        }
        if (Date.now() - startedAt >= this.lockTimeoutMs) {
          throw epochError('ACTIVATION_EPOCH_LOCK_TIMEOUT', 'Activation epoch store is locked by another owner.', {
            lock_file: this.lockFile,
            owner_pid: Number.isSafeInteger(ownerPid) ? ownerPid : null,
            owner_instance_id: String(existing?.owner_instance_id || '') || null
          });
        }
        sleepSync(LOCK_RETRY_MS);
      }
    }
  }

  _releaseLock(descriptor) {
    if (!descriptor) return;
    try {
      const current = JSON.parse(fs.readFileSync(this.lockFile, 'utf8'));
      if (current?.token !== descriptor.token || Number(current?.pid) !== Number(descriptor.pid)) return;
      fs.rmSync(this.lockFile, { force: true });
    } catch {
      // Never remove an unreadable lock: another process may have replaced it.
    }
  }

  _withLock(action) {
    const lock = this._acquireLock();
    try { return action(); }
    finally { this._releaseLock(lock); }
  }

  _parseFile(file) {
    try {
      return { exists: true, readable: true, value: JSON.parse(fs.readFileSync(file, 'utf8')) };
    } catch (error) {
      return { exists: fs.existsSync(file), readable: false, error };
    }
  }

  _read() {
    const primary = this._parseFile(this.file);
    const backup = this._parseFile(`${this.file}.bak`);
    if (!primary.exists && !backup.exists) return emptyStore();
    // A backup is evidence for recovery, never an alternate authority.  If
    // the primary is missing/unreadable, fail closed instead of silently
    // resurrecting a possibly stale READY epoch from .bak.
    if (!primary.readable) {
      throw epochError('ACTIVATION_EPOCH_STORE_INVALID', 'Activation epoch primary store is unreadable; refusing backup fallback.', {
        primary_exists: primary.exists,
        backup_exists: backup.exists,
        primary_error: String(primary.error?.code || primary.error?.message || 'UNREADABLE')
      });
    }
    if (backup.exists && !backup.readable) {
      throw epochError('ACTIVATION_EPOCH_STORE_INVALID', 'Activation epoch backup store is unreadable.', {
        primary_exists: true,
        backup_exists: true,
        backup_error: String(backup.error?.code || backup.error?.message || 'UNREADABLE')
      });
    }
    const store = normalizeSnapshot(primary.value, 'primary store');
    // A syntactically valid but semantically malformed backup is evidence of a
    // potentially torn or tampered write.  Do not silently ignore it while
    // reporting the primary as a coherent durable state.
    if (backup.exists) normalizeSnapshot(backup.value, 'backup store');
    return { version: STORE_VERSION, current: store.current, history: store.history.slice(0, this.maxHistory) };
  }

  _write(store) {
    const current = store.current ? normalizeRecord(store.current) : null;
    const history = [];
    const seen = new Set(current ? [current.activation_epoch_id] : []);
    for (const item of Array.isArray(store.history) ? store.history : []) {
      const normalized = normalizeRecord(item);
      if (seen.has(normalized.activation_epoch_id)) continue;
      seen.add(normalized.activation_epoch_id);
      history.push(normalized);
      if (history.length >= this.maxHistory) break;
    }
    writeJsonAtomic(this.file, { version: STORE_VERSION, current, history });
  }

  // With no argument this returns the complete normalized store.  Supplying an
  // epoch id is a convenience for callers recovering a specific transaction.
  load(epochId = null) {
    const store = this._read();
    if (epochId === null || epochId === undefined || epochId === '') return clone(store);
    const id = normalizeId(epochId);
    if (store.current?.activation_epoch_id === id) return clone(store.current);
    return clone(store.history.find((item) => item.activation_epoch_id === id) || null);
  }

  current() {
    return clone(this._read().current);
  }

  history() {
    return clone(this._read().history);
  }

  get(epochId) {
    return this.load(epochId);
  }

  create(input = {}) {
    if (!isPlainObject(input)) throw epochError('ACTIVATION_EPOCH_ARGUMENT_INVALID', 'Activation epoch creation input must be an object.');
    const now = this.now();
    if (!Number.isSafeInteger(now) || now < 0) throw epochError('ACTIVATION_EPOCH_CLOCK_INVALID', 'Activation epoch clock is invalid.');
    const intent = canonicalIntent(input);
    if (intent.expires_at_unix_ms !== null && intent.expires_at_unix_ms <= now) {
      throw epochError('ACTIVATION_EPOCH_EXPIRED', 'Activation epoch expiry must be in the future.');
    }
    const requestedId = input.activation_epoch_id || input.epoch_id;
    const id = requestedId ? normalizeId(requestedId) : generatedEpochId(now);
    return this._withLock(() => {
      const lockedNow = this.now();
      if (!Number.isSafeInteger(lockedNow) || lockedNow < 0) throw epochError('ACTIVATION_EPOCH_CLOCK_INVALID', 'Activation epoch clock is invalid.');
      if (intent.expires_at_unix_ms !== null && intent.expires_at_unix_ms <= lockedNow) {
        throw epochError('ACTIVATION_EPOCH_EXPIRED', 'Activation epoch expiry must be in the future.');
      }
      const store = this._read();
      if (store.current) {
        if (store.current.activation_epoch_id === id
          && store.current.request_fingerprint === requestFingerprint(intent)) return clone(store.current);
        if (store.current.activation_epoch_id === id) {
          throw epochError('ACTIVATION_EPOCH_ID_CONFLICT', 'activation_epoch_id already identifies another activation request.');
        }
        if (ACTIVE_STATES.has(store.current.state)) {
          const stale = store.current.expires_at_unix_ms !== null && lockedNow >= store.current.expires_at_unix_ms;
          throw epochError('ACTIVATION_EPOCH_ACTIVE', 'Another activation epoch is still active.', {
            activation_epoch_id: store.current.activation_epoch_id,
            state: store.current.state,
            stale,
            expires_at_unix_ms: store.current.expires_at_unix_ms
          });
        }
      }
      if (store.history.some((item) => item.activation_epoch_id === id)) {
        throw epochError('ACTIVATION_EPOCH_ID_CONFLICT', 'activation_epoch_id already exists in history.');
      }
      const record = {
        version: STORE_VERSION,
        activation_epoch_id: id,
        operation_id: intent.operation_id,
        mode: intent.mode,
        state: 'PREPARING',
        // Creation is the durable admission boundary.  A caller must explicitly
        // finish with ready() before this value can return to OPEN.
        admission_state: 'CLOSED',
        components: intent.components,
        source_checkpoint: intent.source_checkpoint,
        ledger_snapshot: intent.ledger_snapshot,
        component_revisions: intent.component_revisions,
        component_evidence: intent.component_evidence,
        owner_instance_id: intent.owner_instance_id,
        owner_pid: intent.owner_pid,
        expires_at: intent.expires_at_unix_ms === null ? null : isoAt(intent.expires_at_unix_ms),
        expires_at_unix_ms: intent.expires_at_unix_ms,
        verification: null,
        metadata: intent.metadata,
        request_intent: intent,
        request_fingerprint: requestFingerprint(intent),
        revision: 1,
        created_at: isoAt(lockedNow),
        created_at_unix_ms: lockedNow,
        updated_at: isoAt(lockedNow),
        updated_at_unix_ms: lockedNow,
        started_at: null,
        started_at_unix_ms: null,
        ready_at: null,
        ready_at_unix_ms: null,
        failed_at: null,
        failed_at_unix_ms: null,
        error: null,
        transitions: [{ state: 'PREPARING', at: isoAt(lockedNow), reason: 'created' }]
      };
      const nextHistory = store.current ? [store.current, ...store.history] : store.history;
      this._write({ version: STORE_VERSION, current: record, history: nextHistory });
      return clone(normalizeRecord(record));
    });
  }

  _requireCurrent(epochId) {
    const id = normalizeId(epochId);
    const store = this._read();
    if (!store.current || store.current.activation_epoch_id !== id) {
      const historical = store.history.some((item) => item.activation_epoch_id === id);
      throw epochError(historical ? 'ACTIVATION_EPOCH_NOT_CURRENT' : 'ACTIVATION_EPOCH_NOT_FOUND', historical
        ? 'Only the current activation epoch may be updated.'
        : 'Activation epoch was not found.', { activation_epoch_id: id });
    }
    return { store, id, record: store.current };
  }

  update(epochId, patch = {}) {
    if (isPlainObject(epochId) && (patch === undefined || patch === null || Object.keys(patch).length === 0)) {
      patch = epochId;
      epochId = patch.activation_epoch_id;
    }
    if (!isPlainObject(patch)) throw epochError('ACTIVATION_EPOCH_ARGUMENT_INVALID', 'Activation epoch update must be an object.');
    return this._withLock(() => {
      const { store, id, record } = this._requireCurrent(epochId);
      if (patch.expected_revision !== undefined && Number(patch.expected_revision) !== record.revision) {
        throw epochError('ACTIVATION_EPOCH_CONFLICT', 'Activation epoch revision is stale.', {
          expected_revision: Number(patch.expected_revision),
          current_revision: record.revision
        });
      }
      if (patch.expected_state !== undefined && normalizeState(patch.expected_state) !== record.state) {
        throw epochError('ACTIVATION_EPOCH_CONFLICT', 'Activation epoch state is stale.', {
          expected_state: normalizeState(patch.expected_state),
          current_state: record.state
        });
      }
      if (TERMINAL_STATES.has(record.state)) {
        if (!patch.state || normalizeState(patch.state) === record.state) return clone(record);
        throw epochError('ACTIVATION_EPOCH_TERMINAL', 'A terminal activation epoch cannot be updated.', { state: record.state });
      }
      const now = this.now();
      if (!Number.isSafeInteger(now) || now < record.updated_at_unix_ms) {
        throw epochError('ACTIVATION_EPOCH_CLOCK_REGRESSION', 'Activation epoch clock moved backwards.');
      }
      const nextState = patch.state === undefined && patch.phase === undefined
        ? record.state
        : normalizeState(patch.state || patch.phase);
      if (TERMINAL_STATES.has(nextState)) {
        throw epochError('ACTIVATION_EPOCH_TERMINAL_TRANSITION', 'Use ready() or fail() to terminalize an activation epoch.');
      }
      const currentOrder = STATE_ORDER.get(record.state);
      const nextOrder = STATE_ORDER.get(nextState);
      if (nextState !== record.state && nextOrder < currentOrder) {
        throw epochError('ACTIVATION_EPOCH_STATE_REGRESSION', 'Activation epoch state cannot move backwards.', {
          state: record.state,
          requested_state: nextState
        });
      }
      const next = {
        ...record,
        state: nextState,
        revision: record.revision + 1,
        updated_at: isoAt(now),
        updated_at_unix_ms: now,
        verification: patch.verification === undefined ? record.verification : boundedClone(patch.verification, 'verification'),
        metadata: patch.metadata === undefined ? record.metadata : boundedClone(patch.metadata, 'metadata')
      };
      if (patch.component_revisions !== undefined
        && !sameCanonical(boundedClone(patch.component_revisions, 'component_revisions'), record.component_revisions)) {
        throw epochError('ACTIVATION_EPOCH_IMMUTABLE', 'component_revisions cannot change after epoch creation.');
      }
      if (patch.component_evidence !== undefined
        && !sameCanonical(boundedClone(patch.component_evidence, 'component_evidence'), record.component_evidence)) {
        throw epochError('ACTIVATION_EPOCH_IMMUTABLE', 'component_evidence cannot change after epoch creation.');
      }
      if (patch.owner_instance_id !== undefined
        && optionalOwner(patch.owner_instance_id) !== record.owner_instance_id) {
        throw epochError('ACTIVATION_EPOCH_IMMUTABLE', 'owner_instance_id cannot change after epoch creation.');
      }
      if (patch.owner_pid !== undefined && optionalPid(patch.owner_pid) !== record.owner_pid) {
        throw epochError('ACTIVATION_EPOCH_IMMUTABLE', 'owner_pid cannot change after epoch creation.');
      }
      if (patch.expires_at_unix_ms !== undefined
        && optionalInteger(patch.expires_at_unix_ms, 'expires_at_unix_ms') !== record.expires_at_unix_ms) {
        throw epochError('ACTIVATION_EPOCH_IMMUTABLE', 'expires_at_unix_ms cannot change after epoch creation.');
      }
      if (patch.components !== undefined) {
        const components = normalizeComponents(patch.components);
        if (canonicalJson(components) !== canonicalJson(record.components)) {
          throw epochError('ACTIVATION_EPOCH_IMMUTABLE', 'components cannot change after epoch creation.');
        }
        next.components = components;
      }
      if (patch.source_checkpoint !== undefined) {
        const sourceCheckpoint = boundedClone(patch.source_checkpoint, 'source_checkpoint');
        if (!sameCanonical(sourceCheckpoint, record.source_checkpoint)) {
          throw epochError('ACTIVATION_EPOCH_IMMUTABLE', 'source_checkpoint cannot change after it is bound.');
        }
        next.source_checkpoint = sourceCheckpoint;
      }
      if (patch.ledger_snapshot !== undefined) {
        const ledgerSnapshot = boundedClone(patch.ledger_snapshot, 'ledger_snapshot');
        if (!sameCanonical(ledgerSnapshot, record.ledger_snapshot)) {
          throw epochError('ACTIVATION_EPOCH_IMMUTABLE', 'ledger_snapshot cannot change after it is bound.');
        }
        next.ledger_snapshot = ledgerSnapshot;
      }
      if (patch.operation_id !== undefined && normalizeOperationId(patch.operation_id) !== record.operation_id) {
        throw epochError('ACTIVATION_EPOCH_IMMUTABLE', 'operation_id cannot change after epoch creation.');
      }
      if (patch.activation_epoch_id !== undefined && normalizeId(patch.activation_epoch_id) !== id) {
        throw epochError('ACTIVATION_EPOCH_IMMUTABLE', 'activation_epoch_id cannot change after epoch creation.');
      }
      if (patch.request_intent !== undefined || patch.request_fingerprint !== undefined) {
        throw epochError('ACTIVATION_EPOCH_IMMUTABLE', 'request intent cannot change after epoch creation.');
      }
      if (nextState !== record.state || patch.reason !== undefined) {
        next.transitions = compactTransitions([...record.transitions, {
          state: nextState,
          at: isoAt(now),
          reason: patch.reason === undefined || patch.reason === null ? null : String(patch.reason).slice(0, 500)
        }]);
      }
      if (!next.started_at && nextState !== 'PREPARING') {
        next.started_at = isoAt(now);
        next.started_at_unix_ms = now;
      }
      next.admission_state = 'CLOSED';
      store.current = next;
      this._write(store);
      return clone(normalizeRecord(next));
    });
  }

  fail(epochId, failure = null) {
    return this._withLock(() => {
      const { store, record } = this._requireCurrent(epochId);
      if (record.state === 'FAILED') return clone(record);
      if (record.state === 'READY') throw epochError('ACTIVATION_EPOCH_TERMINAL', 'A ready activation epoch cannot be failed.');
      const now = this.now();
      if (!Number.isSafeInteger(now) || now < record.updated_at_unix_ms) {
        throw epochError('ACTIVATION_EPOCH_CLOCK_REGRESSION', 'Activation epoch clock moved backwards.');
      }
      const normalizedFailure = normalizeError(failure) || {
        code: 'ACTIVATION_EPOCH_FAILED',
        message: 'Activation epoch failed.',
        details: null
      };
      const next = {
        ...record,
        state: 'FAILED',
        revision: record.revision + 1,
        admission_state: 'CLOSED',
        updated_at: isoAt(now),
        updated_at_unix_ms: now,
        started_at: record.started_at || isoAt(now),
        started_at_unix_ms: record.started_at_unix_ms ?? (record.started_at ? Date.parse(record.started_at) : now),
        failed_at: isoAt(now),
        failed_at_unix_ms: now,
        error: normalizedFailure,
        transitions: compactTransitions([...record.transitions, { state: 'FAILED', at: isoAt(now), reason: 'failed' }])
      };
      store.current = next;
      this._write(store);
      return clone(normalizeRecord(next));
    });
  }

  ready(epochId, verification = null) {
    return this._withLock(() => {
      const { store, id, record } = this._requireCurrent(epochId);
      if (record.state === 'READY') {
        // READY is terminal and idempotent.  Still reject an explicitly
        // mismatched epoch id so a stale caller cannot mistake another epoch
        // for its own completion.
        if (isPlainObject(verification) && verification.activation_epoch_id !== undefined
          && normalizeId(verification.activation_epoch_id) !== id) {
          throw epochError('ACTIVATION_EPOCH_ID_MISMATCH', 'Final verification belongs to another activation epoch.');
        }
        return clone(record);
      }
      if (record.state === 'FAILED') throw epochError('ACTIVATION_EPOCH_TERMINAL', 'A failed activation epoch cannot become ready.');
      if (STATE_ORDER.get(record.state) < STATE_ORDER.get('STOPPING')) {
        throw epochError('ACTIVATION_EPOCH_READY_STATE_INVALID', 'READY requires the activation to have reached STOPPING/VERIFYING.');
      }
      if (!record.transitions.some((transition) => transition.state === 'STOPPING')) {
        throw epochError('ACTIVATION_EPOCH_READY_STATE_INVALID', 'READY requires an explicit STOPPING transition.');
      }
      validateReadyVerification(verification, id, record);
      const now = this.now();
      if (!Number.isSafeInteger(now) || now < record.updated_at_unix_ms) {
        throw epochError('ACTIVATION_EPOCH_CLOCK_REGRESSION', 'Activation epoch clock moved backwards.');
      }
      const proof = boundedClone(verification, 'verification');
      if (proof.verified_at === undefined || proof.verified_at === null || proof.verified_at === '') proof.verified_at = isoAt(now);
      const startedAt = record.started_at || isoAt(now);
      const startedAtUnixMs = record.started_at_unix_ms ?? (record.started_at ? Date.parse(record.started_at) : now);
      const next = {
        ...record,
        state: 'READY',
        revision: record.revision + 1,
        admission_state: 'OPEN',
        updated_at: isoAt(now),
        updated_at_unix_ms: now,
        started_at: startedAt,
        started_at_unix_ms: startedAtUnixMs,
        ready_at: isoAt(now),
        ready_at_unix_ms: now,
        verification: proof,
        error: null,
        transitions: compactTransitions([...record.transitions, { state: 'READY', at: isoAt(now), reason: 'verified' }])
      };
      store.current = next;
      this._write(store);
      return clone(normalizeRecord(next));
    });
  }

  admissionState() {
    return this._read().current?.admission_state || 'OPEN';
  }

  admissionClosed() {
    return this.admissionState() === 'CLOSED';
  }

  isStale(epochId = null, at = this.now()) {
    const record = epochId === null || epochId === undefined || epochId === ''
      ? this._read().current
      : this.load(epochId);
    if (!record || !ACTIVE_STATES.has(record.state) || record.expires_at_unix_ms === null) return false;
    const now = Number(at);
    if (!Number.isSafeInteger(now) || now < 0) throw epochError('ACTIVATION_EPOCH_CLOCK_INVALID', 'Activation epoch clock is invalid.');
    return now >= record.expires_at_unix_ms;
  }

  currentStatus() {
    const current = this._read().current;
    if (!current) return { activation_epoch_id: null, state: 'NONE', admission_open: true, stale: false };
    return {
      activation_epoch_id: current.activation_epoch_id,
      state: current.state,
      admission_open: current.admission_state === 'OPEN',
      stale: this.isStale(current.activation_epoch_id),
      expires_at_unix_ms: current.expires_at_unix_ms,
      owner_instance_id: current.owner_instance_id,
      owner_pid: current.owner_pid,
      revision: current.revision
    };
  }

  active() {
    const current = this._read().current;
    return current && ACTIVE_STATES.has(current.state) ? clone(current) : null;
  }
}

module.exports = {
  ActivationEpochStore,
  STORE_VERSION,
  DEFAULT_MAX_HISTORY,
  MAX_HISTORY,
  MAX_TRANSITIONS,
  DEFAULT_LOCK_TIMEOUT_MS,
  DEFAULT_LOCK_STALE_MS,
  EPOCH_STATES,
  ACTIVE_STATES,
  TERMINAL_STATES,
  normalizeState,
  normalizeMode,
  normalizeId,
  requestFingerprint
};
