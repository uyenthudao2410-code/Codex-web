const CHECKPOINT_ID = /^[A-Za-z0-9][A-Za-z0-9_-]{7,127}$/;
const HEX64 = /^[a-f0-9]{64}$/;
const GIT_OBJECT_ID = /^[a-f0-9]{40,64}$/;
const CLOSURE_INPUT_SCHEMA_VERSION = 1;
const COMPONENTS = Object.freeze(['recovery_host', 'coding_mcp', 'electron_ui']);
// `UNCHANGED_ACKNOWLEDGED` is SHA continuity only.  It deliberately carries no
// current-process discovery timestamp and must not close an accepted-to-live
// activation after a process replacement.  Only the exact rediscovered state
// is current for LIVE_CLOSED.
const CONNECTOR_CURRENT_STATES = new Set(['CURRENT_ACKNOWLEDGED']);
const CONNECTOR_CONTINUITY_STATES = new Set(['UNCHANGED_ACKNOWLEDGED']);
const ACCEPTED_RECEIPT_KINDS = new Set(['explicit_existing_file', 'task_modified_file', 'durable_wave_patch_surface']);
const { componentOwnsPath } = require('./componentRevision');
const {
  OPERATION_ID_PATTERN,
  lifecycleDecisionIsClean,
  normalizeLifecycleDecision,
  postflightRevisionVerified,
  verifyActivationPostflight
} = require('./activationPostflight');

function text(value) { return String(value || '').trim(); }

function normalizedComponents(value) {
  const requested = Array.isArray(value) ? value.slice() : [];
  const unique = [...new Set(requested)];
  return {
    components: COMPONENTS.filter((component) => unique.includes(component)),
    valid: requested.length === unique.length
      && requested.every((component) => typeof component === 'string' && component === text(component))
      && unique.every((component) => COMPONENTS.includes(component))
      && requested.every((component, index) => index === 0
        || COMPONENTS.indexOf(component) > COMPONENTS.indexOf(requested[index - 1]))
  };
}

function normalizedRevision(value) {
  const revision = typeof value === 'string' ? value : '';
  return HEX64.test(revision) ? revision : null;
}

function checkpointIdentity(source, { allowEmptyProof = false } = {}) {
  const value = source && typeof source === 'object' ? source : {};
  const identity = {
    source_checkpoint_id: typeof value.source_checkpoint_id === 'string' ? value.source_checkpoint_id : '',
    run_id: typeof value.run_id === 'string' ? value.run_id : '',
    wave_id: typeof value.wave_id === 'string' ? value.wave_id : '',
    proof_fingerprint: typeof value.proof_fingerprint === 'string' ? value.proof_fingerprint : '',
    accepted_head: typeof value.accepted_head === 'string' ? value.accepted_head : ''
  };
  const valid = CHECKPOINT_ID.test(identity.source_checkpoint_id)
    && CHECKPOINT_ID.test(identity.run_id)
    && CHECKPOINT_ID.test(identity.wave_id)
    && (HEX64.test(identity.proof_fingerprint) || (allowEmptyProof && identity.proof_fingerprint === ''))
    && GIT_OBJECT_ID.test(identity.accepted_head);
  return { ...identity, valid };
}

function activationAuthorityError(code, message, details = {}) {
  return Object.assign(new Error(message), { code, details });
}

function activationSourceCheckpoint(hostStatus, component = '') {
  const requestedComponent = String(component || '');
  if (requestedComponent && !COMPONENTS.includes(requestedComponent)) {
    throw activationAuthorityError('INVALID_COMPONENT', 'Activation component is not allowlisted.');
  }
  const closure = hostStatus?.auto_activation?.closure_input;
  if (!plainObject(closure)) {
    throw activationAuthorityError(
      'ACTIVATION_SOURCE_CHECKPOINT_UNAVAILABLE',
      'Activation requires a fresh durable accepted-code closure checkpoint from Recovery Host.'
    );
  }
  const affectedComponents = Array.isArray(closure.affected_components)
    ? closure.affected_components.slice()
    : [];
  const affectedComponentsValid = affectedComponents.length > 0
    && affectedComponents.length === new Set(affectedComponents).size
    && affectedComponents.every((value) => typeof value === 'string' && value === text(value) && COMPONENTS.includes(value))
    && affectedComponents.every((value, index) => index === 0
      || COMPONENTS.indexOf(value) > COMPONENTS.indexOf(affectedComponents[index - 1]));
  if (closure.schema_version !== CLOSURE_INPUT_SCHEMA_VERSION
    || closure.source_accepted !== true
    || closure.accepted_receipts_complete !== true
    || closure.component_receipts_valid !== true
    || closure.activation_eligible !== true
    || closure.eligibility_code !== 'ACTIVATABLE'
    || closure.affected_components_valid !== true
    || !affectedComponentsValid
    || (requestedComponent && !affectedComponents.includes(requestedComponent))) {
    throw activationAuthorityError(
      'ACTIVATION_SOURCE_CHECKPOINT_NOT_ELIGIBLE',
      'The accepted-code closure checkpoint is not eligible for the requested component.',
      {
        component: requestedComponent || null,
        eligibility_code: typeof closure.eligibility_code === 'string' ? closure.eligibility_code : null,
        affected_components: affectedComponents
      }
    );
  }
  const sourceCheckpoint = {
    checkpoint_id: typeof closure.source_checkpoint_id === 'string' ? closure.source_checkpoint_id : '',
    run_id: typeof closure.run_id === 'string' ? closure.run_id : '',
    wave_id: typeof closure.wave_id === 'string' ? closure.wave_id : '',
    proof_fingerprint: typeof closure.proof_fingerprint === 'string' ? closure.proof_fingerprint : '',
    git_head: typeof closure.accepted_head === 'string' ? closure.accepted_head : ''
  };
  if (!CHECKPOINT_ID.test(sourceCheckpoint.checkpoint_id)
    || !CHECKPOINT_ID.test(sourceCheckpoint.run_id)
    || !CHECKPOINT_ID.test(sourceCheckpoint.wave_id)
    || !HEX64.test(sourceCheckpoint.proof_fingerprint)
    || !GIT_OBJECT_ID.test(sourceCheckpoint.git_head)) {
    throw activationAuthorityError(
      'ACTIVATION_SOURCE_CHECKPOINT_INVALID',
      'The accepted-code closure checkpoint identity is incomplete or noncanonical.'
    );
  }
  return sourceCheckpoint;
}

function receiptBelongsToCheckpoint(receipt, identity, component) {
  return verifyActivationPostflight(receipt, {
    component,
    checkpoint: {
      checkpoint_id: identity.source_checkpoint_id,
      run_id: identity.run_id,
      wave_id: identity.wave_id
    },
    expectedRevision: receipt?.expected_revision
  }).ok;
}

function componentIsCurrent(component, status, receipt, identity) {
  if (!receiptBelongsToCheckpoint(receipt, identity, component)) return false;
  const running = normalizedRevision(status?.running_revision);
  const disk = normalizedRevision(status?.disk_revision);
  const receiptRunning = normalizedRevision(receipt?.running_revision);
  const receiptDisk = normalizedRevision(receipt?.disk_revision);
  return Boolean(postflightRevisionVerified(receipt)
    && running && running === disk
    && running === receiptRunning && disk === receiptDisk
    && status?.update_pending === false);
}

function plainObject(value) {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}

function normalizedAcceptedReceipt(value, identity, component) {
  if (!plainObject(value)) return null;
  const rawPath = typeof value.path === 'string' ? value.path : '';
  const portable = rawPath.replace(/\\/g, '/');
  const protectedPath = portable.toLowerCase();
  const state = text(value.state);
  const sha256 = value.sha256 == null ? null : text(value.sha256).toLowerCase();
  const sizeBytes = value.size_bytes;
  const kind = text(value.receipt_kind);
  if (!portable || rawPath !== text(rawPath) || portable.startsWith('/') || portable.split('/').includes('..')
    || protectedPath === '.coding-tools' || protectedPath.startsWith('.coding-tools/')
    || protectedPath === '.git' || protectedPath.startsWith('.git/')
    || !componentOwnsPath(component, portable)
    || text(value.run_id) !== identity.run_id
    || text(value.wave_id) !== identity.wave_id
    || !ACCEPTED_RECEIPT_KINDS.has(kind)
    || value.restart_safe !== true
    || !Number.isSafeInteger(sizeBytes) || sizeBytes < 0
    || !['file', 'missing'].includes(state)) return null;
  if (state === 'file' && (!HEX64.test(sha256 || '') || value.content_addressed !== true)) return null;
  if (state === 'missing' && (sha256 !== null || sizeBytes !== 0 || value.content_addressed !== false)) return null;
  return {
    path: portable,
    state,
    sha256,
    size_bytes: sizeBytes,
    receipt_kind: kind,
    run_id: identity.run_id,
    wave_id: identity.wave_id,
    restart_safe: true,
    content_addressed: value.content_addressed === true
  };
}

function normalizeComponentReceipts(value, affectedComponents, identity) {
  if (!plainObject(value)) return { valid: false, receipts: {} };
  const keys = Object.keys(value);
  if (keys.length !== affectedComponents.length
    || keys.some((component) => !affectedComponents.includes(component))) {
    return { valid: false, receipts: {} };
  }
  const receipts = {};
  for (const component of affectedComponents) {
    const raw = value[component];
    if (!Array.isArray(raw) || raw.length === 0) return { valid: false, receipts: {} };
    const normalized = raw.map((item) => normalizedAcceptedReceipt(item, identity, component));
    if (normalized.some((item) => !item)
      || new Set(normalized.map((item) => item.path)).size !== normalized.length) {
      return { valid: false, receipts: {} };
    }
    receipts[component] = normalized;
  }
  return { valid: true, receipts };
}

function closureState(projection) {
  if (!projection.source_accepted) return 'NO_ACCEPTED_CHECKPOINT';
  if (!projection.closure_input_schema_supported) return 'CLOSURE_SCHEMA_UNSUPPORTED';
  if (!projection.checkpoint_identity_valid) return 'CHECKPOINT_IDENTITY_INVALID';
  if (!projection.accepted_receipts_complete) return 'RECEIPT_INCOMPLETE';
  if (!projection.activation_eligible) return projection.eligibility_code || 'CHECKPOINT_NOT_ACTIVATABLE';
  if (!projection.affected_components_valid) return 'AFFECTED_COMPONENTS_INVALID';
  if (!projection.component_receipts_valid) return 'ACCEPTED_RECEIPTS_INVALID';
  if (!projection.postflight_receipts_valid) return 'POSTFLIGHT_RECEIPTS_INVALID';
  if (!projection.lifecycle_clean) return projection.lifecycle_code || 'LIFECYCLE_NOT_QUIESCENT';
  if (!projection.components_current) return 'COMPONENTS_NOT_CURRENT';
  if (!projection.connector_contract_current) return 'CONNECTOR_CONTRACT_NOT_CURRENT';
  if (!projection.runtime_fully_ready) return 'RUNTIME_NOT_READY';
  return 'LIVE_CLOSED';
}

function computeActivationClosure({
  acceptedCode = null,
  componentRevisions = {},
  connectorContractState = 'UNAVAILABLE',
  connectorRefreshRequired = null,
  connectorAcknowledgementPending = null,
  connectorRediscoveredAt = null,
  connectorCurrentSha256 = '',
  connectorAcknowledgedSha256 = '',
  runtimeFullyReady = false,
  runtimeRunning = false,
  tunnelRunning = false,
  observedAt = new Date().toISOString()
} = {}) {
  const source = acceptedCode && typeof acceptedCode === 'object' ? acceptedCode : {};
  const normalizedAffectedComponents = normalizedComponents(source.affected_components);
  const affectedComponents = normalizedAffectedComponents.components;
  const identity = checkpointIdentity(source, {
    allowEmptyProof: normalizedAffectedComponents.valid && affectedComponents.length === 0
  });
  const acceptedComponentReceipts = normalizeComponentReceipts(source.component_receipts, affectedComponents, identity);
  const rawPostflightReceipts = source.postflight_receipts;
  const postflightKeysValid = plainObject(rawPostflightReceipts)
    && Object.keys(rawPostflightReceipts).length === affectedComponents.length
    && Object.keys(rawPostflightReceipts).every((component) => affectedComponents.includes(component));
  const postflightReceipts = {};
  const componentCurrent = {};
  let postflightReceiptsValid = postflightKeysValid;
  for (const component of affectedComponents) {
    const rawReceipt = postflightKeysValid ? rawPostflightReceipts[component] || null : null;
    const verification = verifyActivationPostflight(rawReceipt, {
      component,
      checkpoint: {
        checkpoint_id: identity.source_checkpoint_id,
        run_id: identity.run_id,
        wave_id: identity.wave_id
      },
      expectedRevision: rawReceipt?.expected_revision
    });
    if (!verification.ok) postflightReceiptsValid = false;
    const receipt = verification.ok ? verification.postflight : null;
    postflightReceipts[component] = receipt;
    componentCurrent[component] = componentIsCurrent(
      component,
      componentRevisions?.[component] || {},
      receipt,
      identity
    );
  }
  const componentsCurrent = source.components_current === true
    && affectedComponents.every((component) => componentCurrent[component] === true);
  const connectorState = text(connectorContractState) || 'UNAVAILABLE';
  const currentConnectorSha = text(connectorCurrentSha256).toLowerCase();
  const acknowledgedConnectorSha = text(connectorAcknowledgedSha256).toLowerCase();
  const connectorShaCurrent = HEX64.test(currentConnectorSha)
    && currentConnectorSha === acknowledgedConnectorSha;
  const rediscoveredAt = text(connectorRediscoveredAt);
  const connectorFreshnessCurrent = Boolean(connectorState === 'CURRENT_ACKNOWLEDGED'
    && rediscoveredAt && Number.isFinite(Date.parse(rediscoveredAt)));
  const connectorCurrent = Boolean(CONNECTOR_CURRENT_STATES.has(connectorState)
    && connectorRefreshRequired === false
    && connectorAcknowledgementPending === false
    && connectorShaCurrent
    && connectorFreshnessCurrent);
  const normalizedLifecycle = normalizeLifecycleDecision(source.lifecycle_decision);
  const lifecycleOperationBound = affectedComponents.length === 0
    ? OPERATION_ID_PATTERN.test(normalizedLifecycle?.operation_id || '')
    : Object.values(postflightReceipts).some((receipt) => (
      receipt?.lifecycle_decision?.operation_id === normalizedLifecycle?.operation_id
    ));
  const lifecycleClean = source.lifecycle_clean === true
    && lifecycleDecisionIsClean(normalizedLifecycle)
    && lifecycleOperationBound;
  const runtimeReady = runtimeFullyReady === true && runtimeRunning === true && tunnelRunning === true;
  const projection = {
    schema_version: 1,
    ...identity,
    checkpoint_identity_valid: identity.valid,
    closure_input_schema_supported: Number(source.schema_version) === CLOSURE_INPUT_SCHEMA_VERSION,
    source_accepted: source.source_accepted === true,
    accepted_receipts_complete: source.accepted_receipts_complete === true,
    activation_eligible: source.activation_eligible === true,
    eligibility_code: text(source.eligibility_code) || null,
    affected_components: affectedComponents,
    affected_components_valid: normalizedAffectedComponents.valid,
    component_receipts: acceptedComponentReceipts.receipts,
    component_receipts_valid: acceptedComponentReceipts.valid,
    postflight_receipts: postflightReceipts,
    postflight_receipts_valid: postflightReceiptsValid,
    component_current: componentCurrent,
    components_current: componentsCurrent,
    connector_contract_state: connectorState,
    connector_continuity_only: CONNECTOR_CONTINUITY_STATES.has(connectorState),
    connector_refresh_required: connectorRefreshRequired,
    connector_acknowledgement_pending: connectorAcknowledgementPending,
    connector_rediscovered_at: rediscoveredAt || null,
    connector_current_sha256: currentConnectorSha || null,
    connector_acknowledged_sha256: acknowledgedConnectorSha || null,
    connector_contract_current: connectorCurrent,
    lifecycle_decision: normalizedLifecycle,
    lifecycle_clean: lifecycleClean,
    lifecycle_code: text(source.lifecycle_code) || null,
    runtime_running: runtimeRunning === true,
    tunnel_running: tunnelRunning === true,
    runtime_fully_ready: runtimeReady,
    observed_at: text(observedAt) || new Date().toISOString(),
    release_state: 'NOT_RELEASED',
    production_state: 'NOT_CLAIMED'
  };
  projection.closure_state = closureState(projection);
  projection.live_closure = projection.closure_state;
  return projection;
}

module.exports = {
  COMPONENTS,
  CONNECTOR_CURRENT_STATES,
  CONNECTOR_CONTINUITY_STATES,
  CLOSURE_INPUT_SCHEMA_VERSION,
  computeActivationClosure,
  checkpointIdentity,
  activationSourceCheckpoint,
  receiptBelongsToCheckpoint
};
