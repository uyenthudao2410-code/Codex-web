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
  'READY_COMMITTED',
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
const READY_COMMIT_DIGEST_PATTERN = /^[0-9a-f]{64}$/;

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

function sha256Bytes(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function writeBytesAtomic(file, bytes) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temporary = `${file}.${process.pid}.${Date.now()}.${crypto.randomBytes(6).toString('hex')}.tmp`;
  let descriptor;
  try {
    descriptor = fs.openSync(temporary, 'wx', 0o600);
    fs.writeFileSync(descriptor, bytes);
    fs.fsyncSync(descriptor);
  } finally {
    if (descriptor !== undefined) fs.closeSync(descriptor);
  }
  try {
    fs.renameSync(temporary, file);
  } catch (error) {
    try { fs.rmSync(temporary, { force: true }); } catch { /* preserve the original failure */ }
    throw error;
  }
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

function readyCommitDigestFor(epochId, expiresAtUnixMs, verification) {
  return crypto.createHash('sha256').update(canonicalJson({
    activation_epoch_id: epochId,
    expires_at_unix_ms: expiresAtUnixMs,
    verification
  })).digest('hex');
}

function normalizeReadyCommitDigest(value) {
  if (typeof value !== 'string' || !READY_COMMIT_DIGEST_PATTERN.test(value)) {
    throw epochError(
      'ACTIVATION_EPOCH_READY_COMMIT_DIGEST_INVALID',
      'ready() requires the canonical lowercase 64-hex ready commit digest.'
    );
  }
  return value;
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
  const centralExecutor = record?.metadata?.execution_role === 'central_executor'
    && record?.metadata?.component_profile === 'central_executor_v1';
  const legacyPass = census.all_components_same_epoch === true
    && (centralExecutor
      ? census.central_route_verified === true
      : census.connector_acknowledged === true);
  if (!pass && !legacyPass) {
    throw epochError('ACTIVATION_EPOCH_READY_PROOF_REQUIRED', centralExecutor
      ? 'Final census did not prove all components and the central route are ready.'
      : 'Final census did not prove all components and connector admission are ready.');
  }
  if (census.pass === false || census.verified === false) {
    throw epochError('ACTIVATION_EPOCH_READY_PROOF_REQUIRED', 'Final census explicitly reports an incomplete activation.');
  }
  const negativeFlags = [
    'all_components_same_epoch', 'epoch_matches', 'workspace_matches', 'device_matches',
    'revision_matches', 'process_identity_verified',
    'ui_verified', 'recovery_plane_verified'
  ];
  if (centralExecutor) {
    negativeFlags.push('central_route_verified', 'central_connected', 'authority_ready');
  } else {
    negativeFlags.push('connector_acknowledged');
  }
  for (const flag of negativeFlags) {
    if (Object.prototype.hasOwnProperty.call(census, flag) && census[flag] !== true) {
      throw epochError('ACTIVATION_EPOCH_READY_PROOF_REQUIRED', `Final census flag ${flag} is not true.`);
    }
  }
  if (centralExecutor) {
    // Central activation replaces the connector acknowledgement with a
    // credential-free, authenticated route observation.  Unlike legacy
    // records, every component/identity proof is mandatory here so a partial
    // client activation cannot open authority merely because its route is up.
    for (const flag of [
      'all_components_same_epoch', 'epoch_matches', 'workspace_matches',
      'device_matches', 'revision_matches', 'process_identity_verified',
      'ui_verified', 'recovery_plane_verified', 'central_route_verified',
      'central_connected', 'authority_ready'
    ]) {
      if (census[flag] !== true) {
        throw epochError('ACTIVATION_EPOCH_READY_PROOF_REQUIRED', `Central final census requires ${flag}=true.`);
      }
    }
  }
  // A final census may carry a richer runtime snapshot than its legacy
  // top-level flags.  Never allow an explicitly unhealthy snapshot to
  // contradict a READY proof: the route can be authenticated while the
  // primary MCP/native components are stopped or an update is incomplete.
  // `commitReady()` is the first phase of a two-phase activation and keeps
  // admission CLOSED.  In central mode, componentsReady/fullyReady include
  // the admission bit itself, so they are allowed to remain false until the
  // independent pre-admission revalidation opens the epoch.  The final
  // census producer remains responsible for proving those fields before it
  // returns pass=true.  Direct legacy execution additionally requires its
  // Tunnel when that runtime field is present.
  if (isPlainObject(census.runtime)) {
    const runtimeAliases = {
      mcpRunning: 'mcp_running',
      nativeAlive: 'native_alive'
    };
    for (const flag of ['mcpRunning', 'nativeAlive']) {
      const value = census.runtime[flag] ?? census.runtime[runtimeAliases[flag]];
      if (value === false) {
        throw epochError('ACTIVATION_EPOCH_READY_PROOF_REQUIRED', `Final runtime census reports ${flag}=false.`);
      }
    }
    if (census.runtime.updateIncomplete === true || census.runtime.update_incomplete === true) {
      throw epochError('ACTIVATION_EPOCH_READY_PROOF_REQUIRED', 'Final runtime census reports UPDATE_INCOMPLETE.');
    }
    if (!centralExecutor) {
      const tunnelRunning = census.runtime.tunnelRunning ?? census.runtime.tunnel_running;
      if (tunnelRunning === false) {
        throw epochError('ACTIVATION_EPOCH_READY_PROOF_REQUIRED', 'Direct runtime census reports tunnelRunning=false.');
      }
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

function normalizeRecord(value, { allowLegacy = false, allowStaleReadyProof = false } = {}) {
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
  const readyCommitDigest = value.ready_commit_digest === undefined || value.ready_commit_digest === null || value.ready_commit_digest === ''
    ? null : String(value.ready_commit_digest);
  if (readyCommitDigest !== null && !READY_COMMIT_DIGEST_PATTERN.test(readyCommitDigest)) throw storeError('Activation epoch ready_commit_digest is invalid.');
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
  if (!allowLegacy && (state === 'READY_COMMITTED' || state === 'READY')
    && !transitions.some((transition) => transition.state === 'STOPPING')) {
    throw storeError(`${state} activation epoch requires an explicit STOPPING transition.`);
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
  const allowStaleProof = allowStaleReadyProof && (state === 'READY_COMMITTED' || state === 'READY');
  if (!allowLegacy && !allowStaleProof && (state === 'READY_COMMITTED' || state === 'READY')) {
    validateReadyVerification(verification, id, { components, metadata });
  }
  if (readyCommitDigest) {
    if (state !== 'READY_COMMITTED' && state !== 'READY' && state !== 'FAILED') {
      throw storeError('Activation epoch ready_commit_digest is only valid after verification commit.');
    }
    if (!verification) throw storeError('Activation epoch ready_commit_digest requires verification proof.');
    if (!allowStaleProof) validateReadyVerification(verification, id, { components, metadata });
    if (readyCommitDigest !== readyCommitDigestFor(id, expires.unixMs, verification)) {
      throw storeError('Activation epoch ready_commit_digest does not bind the canonical verification proof.');
    }
    if (state === 'READY' && !transitions.some((transition) => transition.state === 'READY_COMMITTED')) {
      throw storeError('READY activation epoch with ready_commit_digest requires READY_COMMITTED transition evidence.');
    }
  }
  if (!allowLegacy && state === 'READY_COMMITTED' && !readyCommitDigest) throw storeError('READY_COMMITTED activation epoch requires ready_commit_digest.');
  if (!allowLegacy && state === 'READY' && transitions.some((transition) => transition.state === 'READY_COMMITTED') && !readyCommitDigest) throw storeError('READY activation epoch reached through READY_COMMITTED requires ready_commit_digest.');
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
    ready_commit_digest: readyCommitDigest,
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
function normalizeSnapshot(value, label = 'store', { allowStaleReadyProof = false } = {}) {
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
    current = value.current === null ? null : normalizeRecord(value.current, { allowStaleReadyProof });
    history = value.history.map((item) => normalizeRecord(item, { allowStaleReadyProof }));
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

function isStaleReadyProofError(error) {
  return error?.code === 'ACTIVATION_EPOCH_READY_PROOF_REQUIRED'
    || error?.details?.code === 'ACTIVATION_EPOCH_READY_PROOF_REQUIRED';
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

  _projectStaleReady(current) {
    if (!current || !['READY_COMMITTED', 'READY'].includes(current.state)) return current;
    const failedAtUnixMs = Number.isSafeInteger(current.updated_at_unix_ms)
      ? current.updated_at_unix_ms
      : current.created_at_unix_ms;
    const failedAt = isoAt(failedAtUnixMs);
    const transitions = [...current.transitions, {
      state: 'FAILED',
      at: failedAt,
      reason: 'legacy-ready-proof-invalid-under-current-readiness-contract'
    }].slice(-MAX_TRANSITIONS);
    return normalizeRecord({
      ...current,
      state: 'FAILED',
      admission_state: 'CLOSED',
      ready_commit_digest: null,
      ready_at: null,
      ready_at_unix_ms: null,
      failed_at: failedAt,
      failed_at_unix_ms: failedAtUnixMs,
      error: {
        code: 'ACTIVATION_EPOCH_STALE_READY_PROOF',
        message: 'Persisted READY proof is no longer admissible under the current runtime readiness contract.',
        details: {
          source_state: current.state,
          source_admission_state: current.admission_state,
          projection: 'read_only_fail_closed',
          recovery_action: 'controlled_full_clean_activation_required'
        }
      },
      transitions
    });
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
    let store;
    let primaryUsedStaleReadyProjection = false;
    try {
      store = normalizeSnapshot(primary.value, 'primary store');
    } catch (error) {
      // A stricter readiness contract may invalidate an older persisted READY
      // proof (for example, a central route that was recorded while the local
      // executor was already UPDATE_INCOMPLETE).  Do not resurrect that proof
      // or fall back to the backup.  Read it as a terminal, CLOSED projection
      // so Recovery Host can remain available for an explicit full-clean
      // activation.  Other corruption still fails closed exactly as before.
      if (!isStaleReadyProofError(error)) throw error;
      store = normalizeSnapshot(primary.value, 'primary store', { allowStaleReadyProof: true });
      primaryUsedStaleReadyProjection = true;
    }
    // A syntactically valid but semantically malformed backup is evidence of a
    // potentially torn or tampered write.  Do not silently ignore it while
    // reporting the primary as a coherent durable state.
    if (backup.exists) {
      try {
        normalizeSnapshot(backup.value, 'backup store');
      } catch (error) {
        if (!isStaleReadyProofError(error)) throw error;
        normalizeSnapshot(backup.value, 'backup store', { allowStaleReadyProof: true });
      }
    }
    const current = primaryUsedStaleReadyProjection
      ? this._projectStaleReady(store.current)
      : store.current;
    return { version: STORE_VERSION, current, history: store.history.slice(0, this.maxHistory) };
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

  // An invalid activation snapshot is a recovery incident, not a reason to
  // weaken the normal reader or silently fall back to the backup.  This
  // explicitly operator-confirmed path preserves the exact primary/backup
  // bytes under a content-addressed quarantine receipt, then installs an
  // empty valid store so Recovery Host can serve authenticated control-plane
  // IPC and an operator can create a fresh full-clean epoch.  It is never
  // called automatically during startup.
  quarantineInvalidSnapshot({
    confirm = false,
    expectedPrimarySha256 = '',
    reason = 'operator-confirmed-invalid-activation-epoch'
  } = {}) {
    if (confirm !== true) {
      throw epochError(
        'ACTIVATION_EPOCH_QUARANTINE_CONFIRM_REQUIRED',
        'Invalid activation-epoch quarantine requires explicit operator confirmation.'
      );
    }
    const expected = String(expectedPrimarySha256 || '').trim().toLowerCase();
    if (expected && !/^[a-f0-9]{64}$/.test(expected)) {
      throw epochError(
        'ACTIVATION_EPOCH_QUARANTINE_HASH_INVALID',
        'expectedPrimarySha256 must be a lowercase 64-hex SHA-256 digest.'
      );
    }
    const boundedReason = String(reason || '').trim().slice(0, 240) || 'operator-confirmed-invalid-activation-epoch';
    return this._withLock(() => {
      const backupFile = `${this.file}.bak`;
      const primary = this._parseFile(this.file);
      const backup = this._parseFile(backupFile);
      const failures = [];
      const inspect = (entry, label) => {
        if (!entry.exists) {
          failures.push({ label, code: 'MISSING', message: `${label} is missing.` });
          return;
        }
        if (!entry.readable) {
          failures.push({ label, code: 'UNREADABLE', message: `${label} is unreadable.` });
          return;
        }
        try {
          normalizeSnapshot(entry.value, label);
        } catch (error) {
          failures.push({
            label,
            code: String(error?.code || 'ACTIVATION_EPOCH_STORE_INVALID'),
            message: String(error?.message || 'Invalid activation snapshot.')
          });
        }
      };
      inspect(primary, 'primary store');
      // A missing backup is valid for a freshly-created store.  Only inspect
      // it when it exists; a missing primary remains an explicit failure.
      if (backup.exists) inspect(backup, 'backup store');
      if (failures.length === 0) {
        throw epochError(
          'ACTIVATION_EPOCH_QUARANTINE_NOT_REQUIRED',
          'Activation epoch primary and backup snapshots are valid; no quarantine was performed.'
        );
      }

      const readBytes = (file, label, exists) => {
        if (!exists) return null;
        try {
          return fs.readFileSync(file);
        } catch (error) {
          throw epochError('ACTIVATION_EPOCH_QUARANTINE_READ_FAILED', `${label} could not be read for quarantine.`, {
            code: String(error?.code || 'READ_FAILED')
          });
        }
      };
      const primaryBytes = readBytes(this.file, 'Primary activation snapshot', primary.exists);
      const backupBytes = readBytes(backupFile, 'Backup activation snapshot', backup.exists);
      const primarySha256 = primaryBytes ? sha256Bytes(primaryBytes) : null;
      const backupSha256 = backupBytes ? sha256Bytes(backupBytes) : null;
      if (expected && primarySha256 !== expected) {
        throw epochError('ACTIVATION_EPOCH_QUARANTINE_HASH_MISMATCH', 'Primary activation snapshot changed or is not the expected target.', {
          expected_primary_sha256: expected,
          observed_primary_sha256: primarySha256
        });
      }

      const quarantineId = `activation-epoch-quarantine-${Date.now().toString(36)}-${crypto.randomBytes(8).toString('hex')}`;
      const primaryQuarantine = `${this.file}.${quarantineId}.primary.json`;
      const backupQuarantine = `${this.file}.${quarantineId}.backup.json`;
      const receiptFile = `${this.file}.${quarantineId}.receipt.json`;
      if (primaryBytes) writeBytesAtomic(primaryQuarantine, primaryBytes);
      if (backupBytes) writeBytesAtomic(backupQuarantine, backupBytes);
      const verifyQuarantine = (file, bytes, label) => {
        if (!bytes) return;
        let observed;
        try { observed = fs.readFileSync(file); } catch (error) {
          throw epochError('ACTIVATION_EPOCH_QUARANTINE_VERIFY_FAILED', `${label} quarantine copy could not be read.`, {
            code: String(error?.code || 'READ_FAILED')
          });
        }
        if (sha256Bytes(observed) !== sha256Bytes(bytes)) {
          throw epochError('ACTIVATION_EPOCH_QUARANTINE_VERIFY_FAILED', `${label} quarantine copy failed its SHA-256 check.`);
        }
      };
      verifyQuarantine(primaryQuarantine, primaryBytes, 'Primary activation snapshot');
      verifyQuarantine(backupQuarantine, backupBytes, 'Backup activation snapshot');
      const unchanged = (file, bytes, label) => {
        if (!bytes) return;
        let observed;
        try { observed = fs.readFileSync(file); } catch (error) {
          throw epochError('ACTIVATION_EPOCH_QUARANTINE_SOURCE_CHANGED', `${label} changed while preparing quarantine.`, {
            code: String(error?.code || 'READ_FAILED')
          });
        }
        if (sha256Bytes(observed) !== sha256Bytes(bytes)) {
          throw epochError('ACTIVATION_EPOCH_QUARANTINE_SOURCE_CHANGED', `${label} changed while preparing quarantine.`);
        }
      };
      unchanged(this.file, primaryBytes, 'Primary activation snapshot');
      unchanged(backupFile, backupBytes, 'Backup activation snapshot');

      const empty = emptyStore();
      // writeJsonAtomic deliberately keeps an unreadable backup.  A second
      // identical write copies the now-valid primary over that old backup,
      // giving the new reader two independently valid snapshots.
      writeJsonAtomic(this.file, empty);
      writeJsonAtomic(this.file, empty);
      const replaced = this._read();
      const receipt = {
        version: 1,
        kind: 'activation_epoch_invalid_snapshot_quarantine',
        quarantine_id: quarantineId,
        recorded_at: new Date().toISOString(),
        reason: boundedReason,
        failures,
        primary: primaryBytes ? {
          bytes: primaryBytes.length,
          sha256: primarySha256,
          path: primaryQuarantine
        } : null,
        backup: backupBytes ? {
          bytes: backupBytes.length,
          sha256: backupSha256,
          path: backupQuarantine
        } : null,
        replacement: {
          primary_path: this.file,
          backup_path: backupFile,
          current: null,
          ready_authority: false,
          requires_explicit_new_activation: true
        }
      };
      writeJsonAtomic(receiptFile, receipt);
      return {
        quarantined: true,
        quarantine_id: quarantineId,
        receipt_path: receiptFile,
        primary_path: primaryQuarantine,
        backup_path: backupBytes ? backupQuarantine : null,
        primary_sha256: primarySha256,
        backup_sha256: backupSha256,
        failure_codes: failures.map((item) => item.code),
        replacement: replaced
      };
    });
  }

  enforceCurrentExpiry(boundary = 'observe') {
    return this._withLock(() => {
      const store = this._read();
      const record = store.current;
      if (!record || !ACTIVE_STATES.has(record.state)) return clone(record);
      this._assertNotExpiredLocked(store, record, boundary);
      return clone(record);
    });
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
      throw epochError('ACTIVATION_REQUEST_EXPIRED', 'Activation epoch expiry must be in the future.');
    }
    const requestedId = input.activation_epoch_id || input.epoch_id;
    const id = requestedId ? normalizeId(requestedId) : generatedEpochId(now);
    return this._withLock(() => {
      const lockedNow = this.now();
      if (!Number.isSafeInteger(lockedNow) || lockedNow < 0) throw epochError('ACTIVATION_EPOCH_CLOCK_INVALID', 'Activation epoch clock is invalid.');
      if (intent.expires_at_unix_ms !== null && intent.expires_at_unix_ms <= lockedNow) {
        throw epochError('ACTIVATION_REQUEST_EXPIRED', 'Activation epoch expiry must be in the future.');
      }
      const store = this._read();
      if (store.current) {
        if (ACTIVE_STATES.has(store.current.state)) this._assertNotExpiredLocked(store, store.current, 'create');
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
        ready_commit_digest: null,
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

  _assertNotExpiredLocked(store, record, boundary) {
    const now = this.now();
    if (!Number.isSafeInteger(now) || now < 0) {
      throw epochError('ACTIVATION_EPOCH_CLOCK_INVALID', 'Activation epoch clock is invalid.');
    }
    if (now < record.updated_at_unix_ms) {
      throw epochError('ACTIVATION_EPOCH_CLOCK_REGRESSION', 'Activation epoch clock moved backwards.');
    }
    if (!ACTIVE_STATES.has(record.state) || record.expires_at_unix_ms === null || now < record.expires_at_unix_ms) return now;
    if (!store.current || store.current.activation_epoch_id !== record.activation_epoch_id
      || store.current.revision !== record.revision) {
      throw epochError('ACTIVATION_EPOCH_CONFLICT', 'Activation epoch changed while checking expiry.');
    }
    const details = {
      activation_epoch_id: record.activation_epoch_id,
      boundary: String(boundary || 'mutation').slice(0, 96),
      expires_at_unix_ms: record.expires_at_unix_ms
    };
    const next = {
      ...record,
      state: 'FAILED',
      revision: record.revision + 1,
      admission_state: 'CLOSED',
      updated_at: isoAt(now),
      updated_at_unix_ms: now,
      started_at: record.started_at || isoAt(now),
      started_at_unix_ms: record.started_at_unix_ms ?? now,
      failed_at: isoAt(now),
      failed_at_unix_ms: now,
      error: {
        code: 'ACTIVATION_REQUEST_EXPIRED',
        message: 'Activation request expired before the activation boundary completed.',
        details
      },
      transitions: compactTransitions([...record.transitions, {
        state: 'FAILED', at: isoAt(now), reason: `expired:${details.boundary}`
      }])
    };
    store.current = next;
    this._write(store);
    throw epochError(
      'ACTIVATION_REQUEST_EXPIRED',
      'Activation request expired before the activation boundary completed.',
      details
    );
  }

  update(epochId, patch = {}) {
    if (isPlainObject(epochId) && (patch === undefined || patch === null || Object.keys(patch).length === 0)) {
      patch = epochId;
      epochId = patch.activation_epoch_id;
    }
    if (!isPlainObject(patch)) throw epochError('ACTIVATION_EPOCH_ARGUMENT_INVALID', 'Activation epoch update must be an object.');
    return this._withLock(() => {
      const { store, id, record } = this._requireCurrent(epochId);
      // Terminal records are immutable.  Do not consult the injected clock for
      // a terminal no-op/replay: a later clock regression must not mask the
      // durable terminal result with an unrelated clock error.  Active records
      // still run the expiry fence before any mutation or CAS decision.
      const now = ACTIVE_STATES.has(record.state)
        ? this._assertNotExpiredLocked(store, record, 'update')
        : null;
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
      const nextState = patch.state === undefined && patch.phase === undefined
        ? record.state
        : normalizeState(patch.state || patch.phase);
      if (nextState === 'READY_COMMITTED') {
        throw epochError('ACTIVATION_EPOCH_READY_COMMIT_REQUIRED', 'Use commitReady() to enter READY_COMMITTED.');
      }
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
      const now = this._assertNotExpiredLocked(store, record, 'fail');
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

  commitReady(epochId, verification) {
    return this._withLock(() => {
      const { store, id, record } = this._requireCurrent(epochId);
      if (record.state === 'FAILED' || record.state === 'READY') {
        throw epochError('ACTIVATION_EPOCH_TERMINAL', 'A terminal activation epoch cannot commit ready verification.');
      }
      const now = this._assertNotExpiredLocked(store, record, 'commitReady');
      if (record.state === 'READY_COMMITTED') {
        const replayProof = boundedClone(verification, 'verification');
        validateReadyVerification(replayProof, id, record);
        if (replayProof.verified_at === undefined || replayProof.verified_at === null || replayProof.verified_at === '') {
          replayProof.verified_at = record.verification?.verified_at;
        }
        const replayDigest = readyCommitDigestFor(id, record.expires_at_unix_ms, replayProof);
        if (replayDigest === record.ready_commit_digest && sameCanonical(replayProof, record.verification)) return clone(record);
        throw epochError('ACTIVATION_EPOCH_READY_COMMIT_CONFLICT', 'READY_COMMITTED replay proof does not match the durable commit.');
      }
      if (record.state !== 'VERIFYING') {
        throw epochError('ACTIVATION_EPOCH_READY_COMMIT_STATE_INVALID', 'commitReady() requires exact VERIFYING state.');
      }
      if (!record.transitions.some((transition) => transition.state === 'STOPPING')) {
        throw epochError('ACTIVATION_EPOCH_READY_COMMIT_STATE_INVALID', 'commitReady() requires durable STOPPING transition evidence.');
      }
      const proof = boundedClone(verification, 'verification');
      validateReadyVerification(proof, id, record);
      if (proof.verified_at === undefined || proof.verified_at === null || proof.verified_at === '') proof.verified_at = isoAt(now);
      const startedAt = record.started_at || isoAt(now);
      const startedAtUnixMs = record.started_at_unix_ms ?? (record.started_at ? Date.parse(record.started_at) : now);
      const readyCommitDigest = readyCommitDigestFor(id, record.expires_at_unix_ms, proof);
      const next = {
        ...record,
        state: 'READY_COMMITTED',
        revision: record.revision + 1,
        admission_state: 'CLOSED',
        updated_at: isoAt(now),
        updated_at_unix_ms: now,
        started_at: startedAt,
        started_at_unix_ms: startedAtUnixMs,
        ready_commit_digest: readyCommitDigest,
        verification: proof,
        error: null,
        transitions: compactTransitions([...record.transitions, { state: 'READY_COMMITTED', at: isoAt(now), reason: 'verification-committed' }])
      };
      store.current = next;
      this._write(store);
      return clone(normalizeRecord(next));
    });
  }

  ready(epochId, readyCommitDigest) {
    return this._withLock(() => {
      const { store, record } = this._requireCurrent(epochId);
      const now = ACTIVE_STATES.has(record.state)
        ? this._assertNotExpiredLocked(store, record, 'ready')
        : null;
      if (record.state === 'FAILED') throw epochError('ACTIVATION_EPOCH_TERMINAL', 'A failed activation epoch cannot become ready.');
      const digest = normalizeReadyCommitDigest(readyCommitDigest);
      if (record.state === 'READY') {
        if (record.ready_commit_digest === digest) return clone(record);
        throw epochError('ACTIVATION_EPOCH_READY_COMMIT_CONFLICT', 'READY replay digest does not match the durable commit.');
      }
      if (record.state !== 'READY_COMMITTED') {
        throw epochError('ACTIVATION_EPOCH_READY_STATE_INVALID', 'ready() requires READY_COMMITTED state.');
      }
      if (record.ready_commit_digest !== digest) {
        throw epochError('ACTIVATION_EPOCH_READY_COMMIT_CONFLICT', 'ready() digest does not match the durable verification commit.');
      }
      const next = {
        ...record,
        state: 'READY',
        revision: record.revision + 1,
        admission_state: 'OPEN',
        updated_at: isoAt(now),
        updated_at_unix_ms: now,
        ready_at: isoAt(now),
        ready_at_unix_ms: now,
        error: null,
        transitions: compactTransitions([...record.transitions, { state: 'READY', at: isoAt(now), reason: 'ready-commit-opened' }])
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
