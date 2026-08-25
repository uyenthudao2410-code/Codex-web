const { RECOVERY_HOST_LEGACY_V1_CONTRACT } = require('./componentRevision');

const POSTFLIGHT_SCHEMA_VERSION = 2;
const COMPONENTS = Object.freeze(['recovery_host', 'coding_mcp', 'electron_ui']);
const OLD_INSTANCE_STATES = Object.freeze(['ABSENT', 'RUNNING']);
const OPERATION_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/;
const HEX64 = /^[a-f0-9]{64}$/;
const POSTFLIGHT_FIELDS = new Set([
  'schema_version', 'operation_id', 'source_checkpoint_id', 'run_id', 'wave_id',
  'component', 'old_instance_state', 'old_instance_id', 'new_instance_id',
  'already_current', 'expected_revision', 'running_revision', 'disk_revision',
  'revision_contract', 'started_at', 'completed_at', 'postflight_verified',
  'health_verified', 'lifecycle_decision'
]);
const LIFECYCLE_FIELDS = new Set([
  'schema_version', 'operation_id', 'clean', 'code', 'reason', 'observed_at',
  'canonical_lifecycle_observed', 'source_checkpoint_verified',
  'fence_released', 'fenced', 'fence_operation_id', 'counts',
  'unexplained_active_runs', 'unbound_live_resource_residues'
]);
const LIFECYCLE_COUNT_FIELDS = new Set([
  'active_tool_calls', 'active_commands', 'starting_commands',
  'active_background_operations', 'active_managed_processes',
  'foreign_heavy_processes', 'active_agent_lanes',
  'threshold_sensitive_stale_candidates', 'owned_codex_sidecar_residues'
]);

function text(value) { return String(value || '').trim(); }

function timestamp(value) {
  const normalized = text(value);
  return normalized && Number.isFinite(Date.parse(normalized)) ? normalized : null;
}

function stableValue(value) {
  if (Array.isArray(value)) return value.map(stableValue);
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stableValue(value[key])]));
}

function exactFields(value, allowed) {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value)
    && Object.keys(value).length === allowed.size
    && Object.keys(value).every((key) => allowed.has(key)));
}

function checkpointIdentity(value) {
  const source = value && typeof value === 'object' ? value : {};
  return {
    checkpoint_id: text(source.checkpoint_id || source.source_checkpoint_id),
    run_id: text(source.run_id),
    wave_id: text(source.wave_id)
  };
}

function normalizeLifecycleDecision(value) {
  if (!exactFields(value, LIFECYCLE_FIELDS) || Number(value.schema_version) !== 1) return null;
  if (!value.counts || typeof value.counts !== 'object' || Array.isArray(value.counts)
    || Object.keys(value.counts).some((key) => !LIFECYCLE_COUNT_FIELDS.has(key))
    || Object.values(value.counts).some((count) => !Number.isSafeInteger(count) || count < 0)
    || !Number.isSafeInteger(value.unexplained_active_runs) || value.unexplained_active_runs < 0
    || !Number.isSafeInteger(value.unbound_live_resource_residues) || value.unbound_live_resource_residues < 0
    || typeof value.clean !== 'boolean'
    || typeof value.canonical_lifecycle_observed !== 'boolean'
    || typeof value.source_checkpoint_verified !== 'boolean'
    || typeof value.fence_released !== 'boolean'
    || typeof value.fenced !== 'boolean') return null;
  const counts = Object.fromEntries(Object.entries(value.counts));
  return {
    schema_version: 1,
    operation_id: text(value.operation_id) || null,
    clean: value.clean === true,
    code: text(value.code) || null,
    reason: text(value.reason) || null,
    observed_at: timestamp(value.observed_at),
    canonical_lifecycle_observed: value.canonical_lifecycle_observed === true,
    source_checkpoint_verified: value.source_checkpoint_verified === true,
    fence_released: value.fence_released === true,
    fenced: typeof value.fenced === 'boolean' ? value.fenced : null,
    fence_operation_id: text(value.fence_operation_id) || null,
    counts,
    unexplained_active_runs: value.unexplained_active_runs,
    unbound_live_resource_residues: value.unbound_live_resource_residues
  };
}

function normalizeActivationPostflight(value) {
  if (!exactFields(value, POSTFLIGHT_FIELDS) || Number(value.schema_version) !== POSTFLIGHT_SCHEMA_VERSION) return null;
  const component = text(value.component);
  const expectedRevision = text(value.expected_revision).toLowerCase();
  const runningRevision = text(value.running_revision).toLowerCase();
  const diskRevision = text(value.disk_revision).toLowerCase();
  if (!COMPONENTS.includes(component) || !HEX64.test(expectedRevision)
    || typeof value.already_current !== 'boolean'
    || typeof value.postflight_verified !== 'boolean'
    || typeof value.health_verified !== 'boolean'
    || (runningRevision && !HEX64.test(runningRevision)) || (diskRevision && !HEX64.test(diskRevision))) return null;
  return {
    schema_version: POSTFLIGHT_SCHEMA_VERSION,
    operation_id: text(value.operation_id) || null,
    source_checkpoint_id: text(value.source_checkpoint_id) || null,
    run_id: text(value.run_id) || null,
    wave_id: text(value.wave_id) || null,
    component,
    old_instance_state: text(value.old_instance_state) || null,
    old_instance_id: text(value.old_instance_id) || null,
    new_instance_id: text(value.new_instance_id) || null,
    already_current: value.already_current === true,
    expected_revision: expectedRevision,
    running_revision: runningRevision || null,
    disk_revision: diskRevision || null,
    revision_contract: text(value.revision_contract) || null,
    started_at: timestamp(value.started_at),
    completed_at: timestamp(value.completed_at),
    postflight_verified: value.postflight_verified === true,
    health_verified: value.health_verified === true,
    lifecycle_decision: normalizeLifecycleDecision(value.lifecycle_decision)
  };
}

function postflightRevisionVerified(postflight) {
  if (!postflight || postflight.running_revision !== postflight.disk_revision) return false;
  if (postflight.running_revision === postflight.expected_revision) return true;
  return postflight.component === 'recovery_host'
    && postflight.revision_contract === RECOVERY_HOST_LEGACY_V1_CONTRACT;
}

function postflightIdentityVerified(postflight) {
  if (!postflight || !OLD_INSTANCE_STATES.includes(postflight.old_instance_state)
    || !postflight.new_instance_id) return false;
  if (postflight.already_current) {
    return postflight.old_instance_state === 'RUNNING'
      && Boolean(postflight.old_instance_id)
      && postflight.old_instance_id === postflight.new_instance_id;
  }
  if (postflight.old_instance_state === 'RUNNING') {
    return Boolean(postflight.old_instance_id)
      && postflight.old_instance_id !== postflight.new_instance_id;
  }
  return postflight.component === 'electron_ui'
    && (!postflight.old_instance_id || postflight.old_instance_id !== postflight.new_instance_id);
}

function lifecycleMatchesPostflight(postflight) {
  const lifecycle = postflight?.lifecycle_decision;
  return Boolean(lifecycle
    && lifecycle.clean === true
    && lifecycle.canonical_lifecycle_observed === true
    && lifecycle.source_checkpoint_verified === true
    && lifecycle.fence_released === true
    && lifecycle.fenced === false
    && lifecycle.fence_operation_id === null
    && lifecycle.operation_id === postflight.operation_id
    && lifecycle.observed_at);
}

function verifyActivationPostflight(value, {
  operationId = '',
  component = '',
  checkpoint = null,
  expectedRevision = ''
} = {}) {
  const postflight = normalizeActivationPostflight(value);
  if (!postflight) return { ok: false, code: 'POSTFLIGHT_SCHEMA_INVALID', postflight: null };
  const expectedOperationId = text(operationId);
  const expectedComponent = text(component);
  const identity = checkpointIdentity(checkpoint);
  const expected = text(expectedRevision).toLowerCase();
  if (!OPERATION_ID_PATTERN.test(postflight.operation_id || '')) {
    return { ok: false, code: 'POSTFLIGHT_OPERATION_INVALID', postflight };
  }
  if (expectedOperationId && postflight.operation_id !== expectedOperationId) {
    return { ok: false, code: 'POSTFLIGHT_OPERATION_MISMATCH', postflight };
  }
  if (expectedComponent && postflight.component !== expectedComponent) {
    return { ok: false, code: 'POSTFLIGHT_COMPONENT_MISMATCH', postflight };
  }
  if (identity.checkpoint_id && (postflight.source_checkpoint_id !== identity.checkpoint_id
    || postflight.run_id !== identity.run_id || postflight.wave_id !== identity.wave_id)) {
    return { ok: false, code: 'POSTFLIGHT_CHECKPOINT_MISMATCH', postflight };
  }
  if (expected && postflight.expected_revision !== expected) {
    return { ok: false, code: 'POSTFLIGHT_REVISION_MISMATCH', postflight };
  }
  if (postflight.postflight_verified !== true || postflight.health_verified !== true) {
    return { ok: false, code: 'POSTFLIGHT_UNVERIFIED', postflight };
  }
  if (!postflightRevisionVerified(postflight)) {
    return { ok: false, code: 'POSTFLIGHT_REVISION_UNVERIFIED', postflight };
  }
  if (!postflightIdentityVerified(postflight)) {
    return { ok: false, code: 'POSTFLIGHT_IDENTITY_UNVERIFIED', postflight };
  }
  if (!postflight.started_at || !postflight.completed_at
    || Date.parse(postflight.completed_at) < Date.parse(postflight.started_at)) {
    return { ok: false, code: 'POSTFLIGHT_TIME_INVALID', postflight };
  }
  if (!lifecycleMatchesPostflight(postflight)) {
    return { ok: false, code: 'POSTFLIGHT_LIFECYCLE_UNVERIFIED', postflight };
  }
  return { ok: true, code: 'POSTFLIGHT_VERIFIED', postflight };
}

function postflightMatchesIntent(value, intent, { operationId = '' } = {}) {
  if (!intent || typeof intent !== 'object') return false;
  const expectedOperationId = text(operationId || intent.current_operation_id);
  if (!expectedOperationId) return false;
  return verifyActivationPostflight(value, {
    operationId: expectedOperationId,
    component: intent.component,
    checkpoint: {
      checkpoint_id: intent.checkpoint_id,
      run_id: intent.run_id,
      wave_id: intent.wave_id
    },
    expectedRevision: intent.expected_revision
  }).ok;
}

function activationPostflight(request, {
  oldInstanceState = null,
  oldInstanceId = null,
  newInstanceId = null,
  runningRevision = null,
  diskRevision = null,
  startedAt = null,
  completedAt = null,
  healthVerified = false,
  lifecycle = null,
  alreadyCurrent = false,
  revisionContract = 'current'
} = {}) {
  const source = request?.source_checkpoint || {};
  const candidate = {
    schema_version: POSTFLIGHT_SCHEMA_VERSION,
    operation_id: text(request?.operation_id) || null,
    source_checkpoint_id: text(source.checkpoint_id) || null,
    run_id: text(source.run_id) || null,
    wave_id: text(source.wave_id) || null,
    component: text(request?.component),
    old_instance_state: text(oldInstanceState) || null,
    old_instance_id: text(oldInstanceId) || null,
    new_instance_id: text(newInstanceId) || null,
    already_current: alreadyCurrent === true,
    expected_revision: text(request?.expected_disk_revision).toLowerCase(),
    running_revision: text(runningRevision).toLowerCase() || null,
    disk_revision: text(diskRevision).toLowerCase() || null,
    started_at: text(startedAt) || null,
    completed_at: text(completedAt) || null,
    health_verified: healthVerified === true,
    postflight_verified: true,
    lifecycle_decision: lifecycle && typeof lifecycle === 'object' ? stableValue(lifecycle) : null,
    revision_contract: text(revisionContract || 'current')
  };
  const verification = verifyActivationPostflight(candidate, {
    operationId: request?.operation_id,
    component: request?.component,
    checkpoint: request?.source_checkpoint,
    expectedRevision: request?.expected_disk_revision
  });
  return { ...(verification.postflight || normalizeActivationPostflight(candidate) || candidate), postflight_verified: verification.ok };
}

module.exports = {
  POSTFLIGHT_SCHEMA_VERSION,
  COMPONENTS,
  OLD_INSTANCE_STATES,
  OPERATION_ID_PATTERN,
  normalizeActivationPostflight,
  normalizeLifecycleDecision,
  postflightRevisionVerified,
  postflightIdentityVerified,
  lifecycleMatchesPostflight,
  verifyActivationPostflight,
  postflightMatchesIntent,
  activationPostflight
};
