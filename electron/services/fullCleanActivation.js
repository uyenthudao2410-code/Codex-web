const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { execFile, spawn } = require('node:child_process');
const { promisify } = require('node:util');
const { ActivationEpochStore } = require('./activationEpoch');
const { readJson } = require('./jsonStore');
const { pythonStatus } = require('./environmentService');
const { isAlive: isAlivePid } = require('./nativeService');
const { tunnelFingerprint } = require('./tunnelService');
const { recoveryMcpHealthObservation, recoveryTunnelReady: probeRecoveryTunnelReady } = require('./recoveryPlaneService');
const {
  activationPostflight,
  lifecycleDecisionIsClean,
  normalizeLifecycleDecision,
  verifyActivationPostflight
} = require('./activationPostflight');
const { normalizeSourceCheckpoint } = require('./recoveryActivation');

const COMPONENTS = Object.freeze(['recovery_host', 'coding_mcp', 'electron_ui']);
// Full-clean activation includes Recovery Host handoff, cold Electron
// startup, MCP/Tunnel readiness and an exact postflight census.  This deadline
// is intentionally bounded but must exceed the cold-start path; otherwise the
// coordinator tears down the fresh runtime solely because the host took a
// while to become ready.
// Keep the durable transaction alive beyond the five-minute operator poll.
// A cold replacement plus canonical projection census can consume several
// minutes before the external ChatGPT connector gets its first opportunity to
// contact the new MCP process. The store still rejects every mutation at or
// after this bounded expiry; this only gives the connector phase its intended
// post-start window instead of racing the startup deadline.
const DEFAULT_TTL_MS = 600_000;
// Coding MCP accepts an activation-preparation fence only inside its own
// 60-second validation window. Keep a small transport/clock margin while the
// durable full-clean epoch retains the longer end-to-end deadline above.
const MCP_PREPARE_FENCE_TTL_MS = 55_000;
const execFileAsync = promisify(execFile);
const HEX64 = /^[a-f0-9]{64}$/;
const TERMINAL_P5_LIFECYCLES = new Set(['EPOCH_CLOSED', 'EPOCH_HARD_STOPPED']);
const PROJECTION_REBUILD_KIND = 'coding_tools_mcp_projection_rebuild';
const PROJECTION_REBUILD_MAX_AGE_MS = 5 * 60 * 1000;
const PROJECTION_REBUILD_FUTURE_SKEW_MS = 1000;
const PROJECTION_REBUILD_STALE_GATE_REASONS = new Set([
  'PREFLIGHT_RECEIPT_STALE',
  'HEALTH_RECEIPT_STALE'
]);
const PROJECTION_REBUILD_ALLOWED_CLASSIFICATIONS = new Set([
  'NO_ACTIVE_PROJECTION', 'CONTEXTUAL_PROJECTIONS', 'PROJECTION_CONSISTENT', 'CHECKPOINTED', 'BLOCKED', 'ABORTED'
]);
const PROJECTION_REBUILD_RECEIPT_FIELDS = new Set([
  'schema_version', 'kind', 'activation_epoch_id', 'process_instance_id',
  'server_instance_id', 'workspace', 'ledger_snapshot_sha256',
  'ledger_logical_sha256', 'ledger_integrity', 'projection_classification',
  'projection', 'completed_at', 'completed_at_unix_ms', 'reconciled',
  'integrity_sha256'
]);
const PROJECTION_REBUILD_LEDGER_FIELDS = new Set([
  'backup_api_copy', 'immutable', 'query_only', 'integrity_check', 'foreign_key_check_rows'
]);
const PROJECTION_REBUILD_PROJECTION_FIELDS = new Set([
  'run_id', 'wave_id', 'orchestration_state', 'mode', 'context_count', 'contextual_sha256'
]);
const CONNECTOR_DISCOVERY_FUTURE_SKEW_MS = 1000;
const ACTIVATION_RESPONSE_LOSS_CODES = new Set([
  'ECONNABORTED', 'ECONNREFUSED', 'ECONNRESET', 'EPIPE', 'ETIMEDOUT',
  'MCP_ACTIVATION_RESPONSE_INVALID', 'ORCHESTRATION_STATE_UNCERTAIN'
]);

function wait(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

function operationId() {
  return `full-clean-${Date.now().toString(36)}-${crypto.randomBytes(12).toString('hex')}`;
}

function epochError(code, message, details = {}) {
  return Object.assign(new Error(message), { code, details });
}

function text(value) { return String(value || '').trim(); }

function isActivationResponseLoss(error) {
  return ACTIVATION_RESPONSE_LOSS_CODES.has(String(error?.code || '').trim().toUpperCase());
}

function exactActivationAdmission(value, epochId, readyCommitDigest, expiresAtUnixMs, admissionOpen) {
  return Boolean(value
    && String(value.activation_epoch_id || '') === String(epochId || '')
    && String(value.ready_commit_digest || '') === String(readyCommitDigest || '')
    && Number(value.expires_at_unix_ms || 0) === Number(expiresAtUnixMs || 0)
    && value.admission_open === admissionOpen);
}

function canonicalWorkspace(value) {
  const resolved = path.resolve(String(value || ''));
  return process.platform === 'win32' ? resolved.toLowerCase() : resolved;
}

function exactObjectFields(value, fields) {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value)
    && Object.keys(value).length === fields.size
    && Object.keys(value).every((key) => fields.has(key)));
}

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map((item) => canonicalJson(item)).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function canonicalProjectionRebuildSha256(receipt) {
  const payload = Object.fromEntries(Object.entries(receipt || {}).filter(([key]) => key !== 'integrity_sha256'));
  return crypto.createHash('sha256').update(canonicalJson(payload), 'utf8').digest('hex');
}

function projectionIdentity(value) {
  const outer = value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  const source = outer.orchestration && typeof outer.orchestration === 'object' && !Array.isArray(outer.orchestration)
    ? outer.orchestration : outer;
  return {
    run_id: text(source.run_id),
    wave_id: text(source.wave_id),
    orchestration_state: text(source.orchestration_state).toUpperCase(),
    mode: text(source.mode).toLowerCase(),
    context_count: source.context_count ?? 0,
    contextual_sha256: text(source.contextual_sha256).toLowerCase()
  };
}

function validateProjectionRebuildReceipt(receipt, {
  activationEpochId,
  processInstanceId,
  serverInstanceId,
  workspace,
  ledgerSnapshot,
  nowUnixMs
} = {}) {
  const reasons = [];
  const add = (reason) => { if (!reasons.includes(reason)) reasons.push(reason); };
  if (!exactObjectFields(receipt, PROJECTION_REBUILD_RECEIPT_FIELDS)) {
    add(receipt && typeof receipt === 'object' ? 'RECEIPT_FIELDS_INVALID' : 'RECEIPT_MISSING');
    return { valid: false, code: 'UPDATE_INCOMPLETE', reasons, receipt: null };
  }
  if (receipt.schema_version !== 2 || receipt.kind !== PROJECTION_REBUILD_KIND) add('RECEIPT_SCHEMA_INVALID');
  for (const field of ['activation_epoch_id', 'process_instance_id', 'server_instance_id']) {
    if (typeof receipt[field] !== 'string' || !receipt[field].trim() || receipt[field].length > 256) {
      add(`${field.toUpperCase()}_INVALID`);
    }
  }
  if (typeof receipt.workspace !== 'string' || !receipt.workspace.trim() || receipt.workspace.length > 4096) add('WORKSPACE_INVALID');
  if (!HEX64.test(receipt.ledger_snapshot_sha256) || !HEX64.test(receipt.ledger_logical_sha256)) add('LEDGER_HASH_INVALID');
  const integrity = receipt.ledger_integrity;
  if (!exactObjectFields(integrity, PROJECTION_REBUILD_LEDGER_FIELDS)
    || integrity.backup_api_copy !== true
    || integrity.immutable !== true
    || integrity.query_only !== true
    || !Array.isArray(integrity.integrity_check)
    || integrity.integrity_check.length !== 1
    || integrity.integrity_check[0] !== 'ok'
    || integrity.foreign_key_check_rows !== 0) add('LEDGER_INTEGRITY_INVALID');
  const classification = receipt.projection_classification;
  const projection = receipt.projection;
  const projectionFieldsValid = exactObjectFields(projection, PROJECTION_REBUILD_PROJECTION_FIELDS)
    && ['run_id', 'wave_id', 'orchestration_state', 'mode', 'contextual_sha256']
      .every((field) => typeof projection?.[field] === 'string' && projection[field].length <= 256)
    && Number.isSafeInteger(projection?.context_count)
    && projection.context_count >= 0;
  const emptyProjection = projectionFieldsValid
    && !projection.run_id && !projection.wave_id && !projection.orchestration_state;
  const completeProjection = projectionFieldsValid
    && Boolean(projection.run_id && projection.wave_id && projection.orchestration_state);
  const noActiveProjection = emptyProjection
    && ['none', 'global'].includes(projection?.mode)
    && projection.context_count === 0
    && !projection.contextual_sha256;
  const contextualProjection = emptyProjection
    && projection?.mode === 'contextual'
    && projection.context_count > 0
    && HEX64.test(projection.contextual_sha256);
  const globalProjection = completeProjection
    && projection?.mode === 'global'
    && projection.context_count === 0
    && !projection.contextual_sha256;
  const terminalState = { CHECKPOINTED: 'CHECKPOINTED', BLOCKED: 'BLOCKED', ABORTED: 'ABORTED' }[classification];
  if (!PROJECTION_REBUILD_ALLOWED_CLASSIFICATIONS.has(classification)
    || !projectionFieldsValid
    || (classification === 'NO_ACTIVE_PROJECTION' && !noActiveProjection)
    || (classification === 'CONTEXTUAL_PROJECTIONS' && !contextualProjection)
    || (!['NO_ACTIVE_PROJECTION', 'CONTEXTUAL_PROJECTIONS'].includes(classification) && !globalProjection)
    || (terminalState && projection.orchestration_state !== terminalState)) add('PROJECTION_CLASSIFICATION_INVALID');
  if (receipt.reconciled !== true) add('RECONCILIATION_FLAG_INVALID');
  const completedMs = receipt.completed_at_unix_ms;
  const timestampValid = Number.isSafeInteger(completedMs) && completedMs > 0;
  if (!timestampValid) add('RECEIPT_TIMESTAMP_INVALID');
  let canonicalCompletedAt = null;
  if (timestampValid) {
    try { canonicalCompletedAt = new Date(completedMs).toISOString(); } catch { canonicalCompletedAt = null; }
  }
  if (!canonicalCompletedAt || receipt.completed_at !== canonicalCompletedAt || Date.parse(receipt.completed_at) !== completedMs) {
    add('RECEIPT_TIMESTAMP_MISMATCH');
  }
  if (!Number.isSafeInteger(nowUnixMs) || nowUnixMs <= 0) add('VALIDATION_TIMESTAMP_INVALID');
  else if (timestampValid) {
    if (completedMs > nowUnixMs + PROJECTION_REBUILD_FUTURE_SKEW_MS) add('RECEIPT_FROM_FUTURE');
    if (nowUnixMs - completedMs > PROJECTION_REBUILD_MAX_AGE_MS) add('RECEIPT_STALE');
  }
  if (text(receipt.activation_epoch_id) !== text(activationEpochId)) add('ACTIVATION_EPOCH_ID_MISMATCH');
  if (text(receipt.process_instance_id) !== text(processInstanceId)) add('PROCESS_INSTANCE_ID_MISMATCH');
  if (text(receipt.server_instance_id) !== text(serverInstanceId)) add('SERVER_INSTANCE_ID_MISMATCH');
  if (!workspace || canonicalWorkspace(receipt.workspace) !== canonicalWorkspace(workspace)) add('WORKSPACE_MISMATCH');
  if (!canonicalSnapshot(ledgerSnapshot)) add('CURRENT_LEDGER_INTEGRITY_INVALID');
  else {
    if (receipt.ledger_snapshot_sha256 !== text(ledgerSnapshot.sha256).toLowerCase()) add('LEDGER_SNAPSHOT_SHA256_MISMATCH');
    if (receipt.ledger_logical_sha256 !== text(ledgerSnapshot.logical_sha256).toLowerCase()) add('LEDGER_LOGICAL_SHA256_MISMATCH');
  }
  if (!HEX64.test(receipt.integrity_sha256)
    || receipt.integrity_sha256 !== canonicalProjectionRebuildSha256(receipt)) add('RECEIPT_INTEGRITY_INVALID');
  return {
    valid: reasons.length === 0,
    code: reasons.length === 0 ? 'READY' : 'UPDATE_INCOMPLETE',
    reasons,
    receipt
  };
}

function validateProjectionRebuildGate({ preflight, health, expected, nowUnixMs } = {}) {
  const reasons = [];
  const add = (prefix, values) => {
    for (const value of values) {
      const reason = `${prefix}_${value}`;
      if (!reasons.includes(reason)) reasons.push(reason);
    }
  };
  const validateWrapper = (wrapper, prefix) => {
    if (!wrapper || typeof wrapper !== 'object' || Array.isArray(wrapper)) {
      add(prefix, ['WRAPPER_MISSING']);
      return { valid: false, receipt: null };
    }
    if (wrapper.current !== true) add(prefix, ['WRAPPER_NOT_CURRENT']);
    const validation = wrapper.validation;
    if (!validation || typeof validation !== 'object' || Array.isArray(validation)
      || validation.valid !== true || validation.code !== 'READY'
      || !Array.isArray(validation.reasons) || validation.reasons.length !== 0) {
      add(prefix, ['WRAPPER_VALIDATION_INVALID']);
    }
    const result = validateProjectionRebuildReceipt(wrapper.receipt, { ...expected, nowUnixMs });
    add(prefix, result.reasons);
    if (validation?.projection_classification !== wrapper.receipt?.projection_classification) {
      add(prefix, ['WRAPPER_CLASSIFICATION_MISMATCH']);
    }
    return result;
  };
  const preflightResult = validateWrapper(preflight?.projection_rebuild, 'PREFLIGHT');
  const healthResult = validateWrapper(health?.projection_rebuild, 'HEALTH');
  const preflightReceipt = preflightResult.receipt;
  const healthReceipt = healthResult.receipt;
  if (!preflight?.projection_rebuild_receipt
    || canonicalJson(preflight.projection_rebuild_receipt) !== canonicalJson(preflightReceipt)) {
    add('PREFLIGHT', ['DUPLICATE_RECEIPT_MISMATCH']);
  }
  if (preflightReceipt) {
    if (text(preflight?.projection_classification).toUpperCase() !== preflightReceipt.projection_classification) {
      add('PREFLIGHT', ['PROJECTION_CLASSIFICATION_MISMATCH']);
    }
    if (canonicalJson(projectionIdentity(preflight?.projection)) !== canonicalJson(preflightReceipt.projection)) {
      add('PREFLIGHT', ['PROJECTION_IDENTITY_MISMATCH']);
    }
  }
  if (!preflightReceipt || !healthReceipt
    || preflightReceipt.integrity_sha256 !== healthReceipt.integrity_sha256
    || canonicalJson(preflightReceipt) !== canonicalJson(healthReceipt)) {
    add('CROSS_OBSERVATION', ['RECEIPT_MISMATCH']);
  }
  return {
    valid: reasons.length === 0,
    code: reasons.length === 0 ? 'READY' : 'UPDATE_INCOMPLETE',
    reasons,
    projection_classification: healthReceipt?.projection_classification || preflightReceipt?.projection_classification || null,
    receipt: healthReceipt || preflightReceipt || null
  };
}

function projectionRebuildFailedOnlyForStaleness(validation) {
  const reasons = Array.isArray(validation?.reasons) ? validation.reasons : [];
  return reasons.length > 0
    && reasons.every((reason) => PROJECTION_REBUILD_STALE_GATE_REASONS.has(String(reason || '')));
}

function validateConnectorReadyGate({ health, contractStatus, nowUnixMs } = {}) {
  const reasons = [];
  const add = (reason) => { if (!reasons.includes(reason)) reasons.push(reason); };
  const processInstanceId = text(health?.process_instance_id);
  const serverInstanceId = text(health?.instance_id || health?.server_instance_id);
  const activationEpochId = text(health?.activation_epoch_id);
  const currentSha256 = text(health?.tool_contract?.sha256);
  const discovery = health?.connector_tool_discovery;
  const discoveryObservedAt = text(discovery?.observed_at);
  const discoveryObservedAtUnixMs = Date.parse(discoveryObservedAt);
  const activationBootstrap = health?.connector_activation_bootstrap;
  const bootstrapObservedAt = text(activationBootstrap?.observed_at);
  const bootstrapObservedAtUnixMs = Date.parse(bootstrapObservedAt);
  const contractState = text(contractStatus?.contractState);
  const discoveryMode = contractState === 'CURRENT_ACKNOWLEDGED';
  const compatibilityMode = contractState === 'CURRENT_COMPATIBLE_ACKNOWLEDGED';
  const validateDiscoveryReceipt = discoveryMode || contractState === 'CHANGED_DISCOVERED_NEEDS_ACK';
  const validateCompatibilityReceipt = compatibilityMode
    || ['CHANGED_COMPATIBLE_NEEDS_ACK', 'UNCHANGED_COMPATIBLE_NEEDS_ACK'].includes(contractState);

  if (!HEX64.test(currentSha256)) add('CURRENT_CONTRACT_SHA256_INVALID');
  if (!processInstanceId) add('PROCESS_INSTANCE_ID_MISSING');
  if (!serverInstanceId) add('SERVER_INSTANCE_ID_MISSING');
  if (!activationEpochId) add('ACTIVATION_EPOCH_ID_MISSING');
  if (!Number.isSafeInteger(nowUnixMs) || nowUnixMs <= 0) add('VALIDATION_TIMESTAMP_INVALID');

  if (!contractStatus || typeof contractStatus !== 'object' || Array.isArray(contractStatus)) {
    add('CONNECTOR_CONTRACT_STATUS_UNAVAILABLE');
  } else {
    if (contractStatus.available !== true) add('CONNECTOR_CONTRACT_UNAVAILABLE');
    if (text(contractStatus.currentSha256) !== currentSha256) add('STATUS_CURRENT_SHA256_MISMATCH');
    if (text(contractStatus.acknowledgedSha256) !== currentSha256) add('ACKNOWLEDGED_SHA256_MISMATCH');
    if (contractStatus.refreshRequired !== false) add('CONNECTOR_REFRESH_REQUIRED');
    if (contractStatus.acknowledgementPending !== false) add('CONNECTOR_ACKNOWLEDGEMENT_PENDING');
    if (contractStatus.contractChanged !== false) add('CONNECTOR_CONTRACT_CHANGED');
    if (!discoveryMode && !compatibilityMode) add('CONNECTOR_CONTRACT_STATE_INVALID');
  }

  if (validateDiscoveryReceipt) {
    if (!discovery || typeof discovery !== 'object' || Array.isArray(discovery)) {
      add('DISCOVERY_RECEIPT_MISSING');
    } else {
      if (discovery.current_contract_observed !== true) add('CURRENT_CONTRACT_NOT_REDISCOVERED');
      if (text(discovery.identity_source) !== 'attested_transport') add('DISCOVERY_IDENTITY_SOURCE_INVALID');
      if (discovery.attestation_verified !== true) add('DISCOVERY_ATTESTATION_INVALID');
      if (text(discovery.contract_sha256) !== currentSha256) add('DISCOVERY_CONTRACT_SHA256_MISMATCH');
      if (text(discovery.process_instance_id) !== processInstanceId) add('DISCOVERY_PROCESS_INSTANCE_ID_MISMATCH');
      if (text(discovery.server_instance_id) !== serverInstanceId) add('DISCOVERY_SERVER_INSTANCE_ID_MISMATCH');
      if (text(discovery.activation_epoch_id) !== activationEpochId) add('DISCOVERY_ACTIVATION_EPOCH_ID_MISMATCH');
      if (!discoveryObservedAt || !Number.isFinite(discoveryObservedAtUnixMs)) add('DISCOVERY_TIMESTAMP_INVALID');
      else if (Number.isSafeInteger(nowUnixMs)
        && discoveryObservedAtUnixMs > nowUnixMs + CONNECTOR_DISCOVERY_FUTURE_SKEW_MS) add('DISCOVERY_FROM_FUTURE');
    }
    if (contractStatus?.rediscovered !== true) add('STATUS_NOT_REDISCOVERED');
    if (text(contractStatus?.rediscoveredSha256) !== currentSha256) add('STATUS_REDISCOVERED_SHA256_MISMATCH');
    if (text(contractStatus?.rediscoveredAt) !== discoveryObservedAt) add('STATUS_REDISCOVERY_TIMESTAMP_MISMATCH');
  }

  if (validateCompatibilityReceipt) {
    // A compatibility bootstrap may close only after the orchestrator has
    // guarded and persisted the exact attested ChatWeb receipt for this
    // process/server/epoch. Pending and malformed compatibility states still
    // fail through the status and receipt checks below.
    if (!activationBootstrap || typeof activationBootstrap !== 'object' || Array.isArray(activationBootstrap)) {
      add('COMPATIBILITY_BOOTSTRAP_RECEIPT_MISSING');
    } else {
      if (activationBootstrap.current_contract_contact !== true) add('COMPATIBILITY_BOOTSTRAP_NOT_CURRENT');
      if (text(activationBootstrap.identity_source) !== 'attested_transport') add('COMPATIBILITY_BOOTSTRAP_IDENTITY_SOURCE_INVALID');
      if (activationBootstrap.attestation_verified !== true) add('COMPATIBILITY_BOOTSTRAP_ATTESTATION_INVALID');
      if (text(activationBootstrap.client_type) !== 'chatweb') add('COMPATIBILITY_BOOTSTRAP_CLIENT_TYPE_INVALID');
      if (!text(activationBootstrap.client_id)) add('COMPATIBILITY_BOOTSTRAP_CLIENT_ID_MISSING');
      if (text(activationBootstrap.method) !== 'tools/call') add('COMPATIBILITY_BOOTSTRAP_METHOD_INVALID');
      if (text(activationBootstrap.tool_name) !== 'workspace_context') add('COMPATIBILITY_BOOTSTRAP_TOOL_INVALID');
      if (activationBootstrap.workspace_accessed !== false) add('COMPATIBILITY_BOOTSTRAP_WORKSPACE_ACCESSED');
      if (text(activationBootstrap.contract_sha256) !== currentSha256) add('COMPATIBILITY_BOOTSTRAP_CONTRACT_SHA256_MISMATCH');
      if (text(activationBootstrap.process_instance_id) !== processInstanceId) add('COMPATIBILITY_BOOTSTRAP_PROCESS_INSTANCE_ID_MISMATCH');
      if (text(activationBootstrap.server_instance_id) !== serverInstanceId) add('COMPATIBILITY_BOOTSTRAP_SERVER_INSTANCE_ID_MISMATCH');
      if (text(activationBootstrap.activation_epoch_id) !== activationEpochId) add('COMPATIBILITY_BOOTSTRAP_ACTIVATION_EPOCH_ID_MISMATCH');
      if (!bootstrapObservedAt || !Number.isFinite(bootstrapObservedAtUnixMs)) add('COMPATIBILITY_BOOTSTRAP_TIMESTAMP_INVALID');
      else if (Number.isSafeInteger(nowUnixMs)
        && bootstrapObservedAtUnixMs > nowUnixMs + CONNECTOR_DISCOVERY_FUTURE_SKEW_MS) add('COMPATIBILITY_BOOTSTRAP_FROM_FUTURE');
    }
    if (contractStatus?.rediscovered === true) add('COMPATIBILITY_MODE_MUST_NOT_CLAIM_REDISCOVERY');
    if (compatibilityMode && contractStatus?.compatibilityAcknowledged !== true) add('STATUS_COMPATIBILITY_NOT_ACKNOWLEDGED');
    if (contractStatus?.bootstrapCurrent !== true) add('STATUS_COMPATIBILITY_BOOTSTRAP_NOT_CURRENT');
    if (!['declared_exact_predecessor_activation_bootstrap', 'exact_current_contract_activation_bootstrap']
      .includes(text(contractStatus?.compatibilitySource))) add('STATUS_COMPATIBILITY_SOURCE_INVALID');
    if (compatibilityMode && text(contractStatus?.compatibilityAcknowledgedAt) !== bootstrapObservedAt) {
      add('STATUS_COMPATIBILITY_TIMESTAMP_MISMATCH');
    }
  }

  return {
    valid: reasons.length === 0,
    code: reasons.length === 0 ? 'READY' : 'UPDATE_INCOMPLETE',
    reasons,
    current_sha256: HEX64.test(currentSha256) ? currentSha256 : null,
    acknowledged_sha256: HEX64.test(text(contractStatus?.acknowledgedSha256))
      ? text(contractStatus.acknowledgedSha256) : null,
    freshness_mode: discoveryMode ? 'current_process_discovery'
      : compatibilityMode ? 'compatible_activation_bootstrap' : null,
    rediscovered_at: discoveryMode && Number.isFinite(discoveryObservedAtUnixMs) ? discoveryObservedAt : null,
    compatibility_acknowledged_at: compatibilityMode && Number.isFinite(bootstrapObservedAtUnixMs)
      ? bootstrapObservedAt : null,
    activation_epoch_id: activationEpochId || null,
    process_instance_id: processInstanceId || null,
    server_instance_id: serverInstanceId || null
  };
}

function reusablePendingProjectionObservation(record, { allowCommitted = false } = {}) {
  // A pending VERIFYING census can be reused by the watchdog/finalize path
  // while admission is closed.  The same immutable projection is also useful
  // for the narrow post-commit identity fence immediately before
  // `complete_epoch`; in that case the store is READY_COMMITTED but admission
  // is still CLOSED and the proof has moved under `verification.final_census`.
  // Keep the default strict (READY_COMMITTED is not reusable) so callers must
  // opt into this bounded revalidation explicitly.
  const verificationContainer = record?.verification;
  const verification = verificationContainer?.final_census
    && typeof verificationContainer.final_census === 'object'
    && !Array.isArray(verificationContainer.final_census)
    ? verificationContainer.final_census
    : verificationContainer;
  const receipt = verification?.projection_rebuild_receipt;
  const connectorValidation = verification?.connector_validation;
  const currentConnectorReceipt = Boolean(
    connectorValidation
    && typeof connectorValidation === 'object'
    && !Array.isArray(connectorValidation)
    && connectorValidation.valid === true
    && (
      (connectorValidation.freshness_mode === 'current_process_discovery'
        && text(connectorValidation.rediscovered_at)
        && !text(connectorValidation.compatibility_acknowledged_at))
      || (connectorValidation.freshness_mode === 'compatible_activation_bootstrap'
        && text(connectorValidation.compatibility_acknowledged_at)
        && !text(connectorValidation.rediscovered_at))
    )
  );
  const reusable = Boolean(
    record
    && (record.state === 'VERIFYING' || (allowCommitted && record.state === 'READY_COMMITTED'))
    && record.admission_state === 'CLOSED'
    && verification && typeof verification === 'object' && !Array.isArray(verification)
    && verification.projection_rebuild_verified === true
    && connectorValidation
    && typeof connectorValidation === 'object'
    && !Array.isArray(connectorValidation)
    // A negative connector gate is the normal waiting state. A passing
    // candidate is reusable only when it already contains one of the two
    // exact current-process receipt modes accepted by the connector validator.
    && (connectorValidation.valid !== true || currentConnectorReceipt)
    && verification.process_identity_verified === true
    && verification.workspace_matches === true
    && verification.device_matches === true
    && verification.revision_matches === true
    && verification.recovery_host_revision_matches === true
    && verification.recovery_host_epoch_matches === true
    && verification.ui_verified === true
    && verification.recovery_plane_verified === true
    && verification.epoch_matches === true
    && receipt && typeof receipt === 'object' && !Array.isArray(receipt)
    && text(receipt.activation_epoch_id) === text(record.activation_epoch_id)
  );
  if (!reusable) return null;
  const integrity = receipt.ledger_integrity;
  const snapshot = {
    backup_api_copy: integrity?.backup_api_copy,
    immutable: integrity?.immutable,
    query_only: integrity?.query_only,
    integrity_check: integrity?.integrity_check,
    foreign_key_check_rows: integrity?.foreign_key_check_rows,
    sha256: receipt.ledger_snapshot_sha256,
    logical_sha256: receipt.ledger_logical_sha256
  };
  if (!canonicalSnapshot(snapshot)) return null;
  const wrapper = {
    current: true,
    validation: {
      valid: true,
      code: 'READY',
      reasons: [],
      projection_classification: receipt.projection_classification
    },
    receipt
  };
  return {
    projection_rebuild: wrapper,
    projection_rebuild_receipt: receipt,
    projection_classification: receipt.projection_classification,
    projection: receipt.projection,
    snapshot,
    lifecycle_decision: verification.lifecycle_decision || null,
    reused_pending_projection: true
  };
}

function requireCanonicalSourceCheckpoint(value) {
  try {
    return normalizeSourceCheckpoint(value);
  } catch (error) {
    if (error?.code === 'ACTIVATION_SOURCE_CHECKPOINT_REQUIRED'
      || error?.code === 'INVALID_SOURCE_CHECKPOINT'
      || error?.code === 'INVALID_ARGUMENT') {
      throw error;
    }
    throw epochError('ACTIVATION_SOURCE_CHECKPOINT_REQUIRED', 'Full clean activation requires an exact accepted source checkpoint.', {
      cause_code: text(error?.code) || null
    });
  }
}

function canonicalSnapshot(snapshot) {
  return Boolean(snapshot
    && snapshot.backup_api_copy === true
    && snapshot.immutable === true
    && snapshot.query_only === true
    && Array.isArray(snapshot.integrity_check)
    && snapshot.integrity_check.length === 1
    && snapshot.integrity_check[0] === 'ok'
    && Number(snapshot.foreign_key_check_rows) === 0
    && HEX64.test(text(snapshot.sha256).toLowerCase())
    && HEX64.test(text(snapshot.logical_sha256).toLowerCase()));
}

function summarizeCensus(raw, { workspace, allowAcceptancePending = false } = {}) {
  const snapshot = raw?.snapshot && typeof raw.snapshot === 'object' ? raw.snapshot : {};
  const runs = Array.isArray(raw?.runs) ? raw.runs.filter((item) => item && typeof item === 'object') : [];
  const managedJobs = Array.isArray(raw?.managed_jobs)
    ? raw.managed_jobs.filter((item) => item && typeof item === 'object')
    : [];
  const summary = raw?.summary && typeof raw.summary === 'object' ? raw.summary : {};
  const classifications = (name) => runs.filter((item) => String(item.classification || '') === name);
  const liveOwned = classifications('LIVE_OWNED');
  const accepting = classifications('AWAITING_ACCEPTANCE');
  const unexplained = classifications('UNEXPLAINED_ACTIVE');
  const terminalContradictions = classifications('TERMINAL_PARENT_CONTRADICTION');
  const activeP5 = runs.filter((item) => String(item.classification || '') === 'P5_EXPERIMENT_ANCHOR'
    && !TERMINAL_P5_LIFECYCLES.has(String(item.p5_epoch_lifecycle || '')));
  const liveManagedJobs = managedJobs.filter((item) => String(item.classification || '') === 'LIVE_OWNED');
  const orphanedManagedJobs = managedJobs.filter((item) => String(item.classification || '') === 'ORPHANED_OR_FOREIGN_MANAGED_JOB');
  const unbound = Array.isArray(raw?.unbound_live_resources) ? raw.unbound_live_resources : [];
  const projectionDrift = summary.projection_drift === true
    || String(raw?.projection?.classification || '') === 'PROJECTION_DRIFT';
  const snapshotOk = canonicalSnapshot(snapshot);
  const workspaceMatches = canonicalWorkspace(raw?.workspace || workspace) === canonicalWorkspace(workspace);
  const sourceCheckpointVerified = raw?.source_checkpoint_verified !== false;
  const dangerousAcceptance = accepting.length > 0 && allowAcceptancePending !== true;
  const counts = {
    active_tool_calls: 0,
    active_commands: 0,
    starting_commands: 0,
    active_background_operations: runs.reduce((sum, item) => sum + Number(item.ownership?.running_background_operations || 0), 0),
    active_managed_processes: liveManagedJobs.length,
    foreign_heavy_processes: 0,
    active_agent_lanes: runs.reduce((sum, item) => sum + Number(item.ownership?.live_agent_lanes || 0), 0),
    threshold_sensitive_stale_candidates: Number(summary.run_classification_counts?.THRESHOLD_SENSITIVE_STALE_CANDIDATE || 0),
    owned_codex_sidecar_residues: 0
  };
  const blockers = [];
  if (!snapshotOk) blockers.push('ledger_snapshot_integrity_failed');
  if (!workspaceMatches) blockers.push('workspace_mismatch');
  if (!sourceCheckpointVerified) blockers.push('source_checkpoint_mismatch');
  if (counts.active_background_operations || counts.active_managed_processes || counts.active_agent_lanes) blockers.push('active_runtime_work');
  if (liveOwned.length) blockers.push('lifecycle_live_owned');
  if (orphanedManagedJobs.length) blockers.push('managed_process_residue');
  if (unexplained.length || unbound.length) blockers.push('lifecycle_unexplained_or_unbound');
  if (terminalContradictions.length) blockers.push('terminal_parent_contradiction');
  if (projectionDrift) blockers.push('projection_drift');
  if (activeP5.length) blockers.push('p5_epoch_not_terminal');
  if (dangerousAcceptance) blockers.push('acceptance_pending');
  const safe = blockers.length === 0;
  return {
    schema_version: 1,
    safe,
    code: safe ? 'READY' : (dangerousAcceptance ? 'ACCEPTANCE_PENDING' : 'ORCHESTRATION_STATE_UNCERTAIN'),
    reason: safe ? 'canonical_ledger_quiescent' : blockers[0],
    workspace: text(raw?.workspace || workspace),
    ledger_path: text(raw?.ledger_path || path.join(workspace, '.coding-tools', 'orchestration', 'ledger.sqlite3')),
    snapshot,
    counts,
    lifecycle: {
      unexplained_active_runs: Number(summary.unexplained_active_runs || 0),
      unbound_live_resource_residues: Number(summary.unbound_live_resource_residues || unbound.length),
      projection_drift: projectionDrift,
      ordinary_active_runs: Number(summary.ordinary_active_runs || 0),
      awaiting_acceptance_runs: accepting.map((item) => text(item.run_id)).filter(Boolean),
      live_owned_runs: liveOwned.map((item) => text(item.run_id)).filter(Boolean),
      active_p5_runs: activeP5.map((item) => text(item.run_id)).filter(Boolean),
      blockers
    },
    source_checkpoint_verified: sourceCheckpointVerified,
    content_free: raw?.content_free === true,
    mutated_canonical_ledger: raw?.mutated_canonical_ledger === true,
    observed_at_unix_seconds: raw?.observed_at_unix_seconds ?? null
  };
}

function runtimeStateHasLiveManagedProcess(paths) {
  let state;
  try { state = readJson(paths.stateFile(), {}); } catch { state = {}; }
  const pids = [Number(state.nativePid || 0), Number(state.tunnelPid || 0)].filter((pid) => Number.isSafeInteger(pid) && pid > 0);
  for (const pid of pids) {
    try { process.kill(pid, 0); return true; } catch { /* stale PID */ }
  }
  return false;
}

function heldCensus(command, args, options) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd,
      env: options.env,
      windowsHide: true,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    let stdout = '';
    let stderr = '';
    let settled = false;
    const timeout = setTimeout(() => {
      child.kill();
      reject(Object.assign(new Error('Canonical ledger census exclusive gate timed out.'), { code: 'ORCHESTRATION_STATE_UNCERTAIN' }));
    }, 15_000);
    timeout.unref?.();
    child.stderr.setEncoding('utf8');
    child.stderr.on('data', (chunk) => { if (stderr.length < 64 * 1024) stderr += chunk; });
    child.stdout.setEncoding('utf8');
    child.stdout.on('data', (chunk) => {
      if (settled) return;
      stdout += chunk;
      if (stdout.length > 8 * 1024 * 1024) {
        settled = true;
        clearTimeout(timeout);
        child.kill();
        reject(Object.assign(new Error('Canonical ledger census exceeded its output bound.'), { code: 'ORCHESTRATION_STATE_UNCERTAIN' }));
        return;
      }
      const newline = stdout.indexOf('\n');
      if (newline < 0) return;
      settled = true;
      clearTimeout(timeout);
      const line = stdout.slice(0, newline).trim();
      let raw;
      try { raw = JSON.parse(line); }
      catch (error) {
        child.kill();
        reject(Object.assign(new Error('Canonical ledger census returned invalid held evidence.'), {
          code: 'ORCHESTRATION_STATE_UNCERTAIN', cause: error
        }));
        return;
      }
      let released = false;
      const release = () => new Promise((releaseResolve, releaseReject) => {
        if (released) { releaseResolve(true); return; }
        released = true;
        const releaseTimeout = setTimeout(() => {
          child.kill();
          releaseReject(Object.assign(new Error('Canonical ledger census gate release timed out.'), { code: 'ORCHESTRATION_STATE_UNCERTAIN' }));
        }, 5000);
        releaseTimeout.unref?.();
        child.once('error', (error) => { clearTimeout(releaseTimeout); releaseReject(error); });
        child.once('exit', (code) => {
          clearTimeout(releaseTimeout);
          if (code === 0) releaseResolve(true);
          else releaseReject(Object.assign(new Error('Canonical ledger census gate holder exited abnormally.'), {
            code: 'ORCHESTRATION_STATE_UNCERTAIN', details: { exit_code: code, stderr: stderr.slice(0, 1000) }
          }));
        });
        child.stdin.end('release\n');
      });
      resolve({ raw, release });
    });
    child.once('error', (error) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      reject(error);
    });
    child.once('exit', (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      reject(Object.assign(new Error('Canonical ledger census gate holder exited before publishing evidence.'), {
        code: 'ORCHESTRATION_STATE_UNCERTAIN', details: { exit_code: code, stderr: stderr.slice(0, 1000) }
      }));
    });
  });
}

async function canonicalLedgerCensus({ paths, workspace, allowAcceptancePending = false, sourceCheckpoint = null, holdExclusive = false } = {}) {
  const rawWorkspace = text(workspace);
  if (!rawWorkspace || !path.isAbsolute(rawWorkspace)) {
    throw Object.assign(new Error('Canonical ledger census requires an absolute workspace.'), {
      code: 'WORKSPACE_MISMATCH'
    });
  }
  const root = path.resolve(rawWorkspace);
  const ledgerPath = path.join(root, '.coding-tools', 'orchestration', 'ledger.sqlite3');
  if (!paths || !root || !fs.existsSync(ledgerPath)) {
    throw Object.assign(new Error('Canonical orchestration ledger is unavailable for stopped-runtime preflight.'), {
      code: 'ORCHESTRATION_STATE_UNCERTAIN'
    });
  }
  const moduleRoot = path.join(paths.resourcesRoot(), 'coding-tools-mcp');
  const helper = path.join(moduleRoot, 'coding_tools_mcp', 'activation_ledger_census.py');
  if (!fs.existsSync(helper)) {
    throw Object.assign(new Error('Canonical ledger census helper is unavailable.'), { code: 'ORCHESTRATION_STATE_UNCERTAIN' });
  }
  const python = await pythonStatus(paths);
  if (!python.installed) {
    throw Object.assign(new Error('Python runtime is unavailable for canonical ledger census.'), { code: 'ORCHESTRATION_STATE_UNCERTAIN' });
  }
  const env = {
    ...process.env,
    PYTHONPATH: [moduleRoot, path.join(moduleRoot, 'python_vendor'), process.env.PYTHONPATH || '']
      .filter(Boolean).join(path.delimiter)
  };
  const args = [
    ...(python.prefixArgs || []),
    '-u', '-m', 'coding_tools_mcp.activation_ledger_census',
    '--workspace', root
  ];
  if (sourceCheckpoint && typeof sourceCheckpoint === 'object') {
    args.push('--source-checkpoint-json', JSON.stringify(sourceCheckpoint));
  }
  if (holdExclusive) args.push('--hold-exclusive');
  let raw;
  let releaseExclusive = null;
  try {
    if (holdExclusive) {
      const held = await heldCensus(python.command, args, { cwd: root, env });
      raw = held.raw;
      releaseExclusive = held.release;
    } else {
      const output = await execFileAsync(python.command, args, {
        cwd: root,
        env,
        windowsHide: true,
        maxBuffer: 8 * 1024 * 1024,
        timeout: 15_000
      });
      raw = JSON.parse(String(output.stdout || '').trim());
    }
  } catch (error) {
    if (releaseExclusive) await releaseExclusive().catch(() => false);
    throw Object.assign(new Error('Canonical ledger census could not be completed.'), {
      code: 'ORCHESTRATION_STATE_UNCERTAIN',
      cause: error
    });
  }
  const result = summarizeCensus({ ...raw, workspace: root, ledger_path: ledgerPath }, {
    workspace: root,
    allowAcceptancePending
  });
  if (sourceCheckpoint && typeof sourceCheckpoint === 'object' && text(sourceCheckpoint.git_head)) {
    try {
      const git = await execFileAsync('git', ['-C', root, 'rev-parse', 'HEAD'], {
        cwd: root,
        env,
        windowsHide: true,
        maxBuffer: 64 * 1024,
        timeout: 5000
      });
      const currentHead = text(git.stdout).toLowerCase();
      if (currentHead !== text(sourceCheckpoint.git_head).toLowerCase()) {
        result.safe = false;
        result.code = 'REVISION_CHANGED';
        result.reason = 'source_checkpoint_git_head_mismatch';
        result.lifecycle.blockers = [...new Set([...result.lifecycle.blockers, 'source_checkpoint_git_head_mismatch'])];
      }
    } catch {
      result.safe = false;
      result.code = 'ORCHESTRATION_STATE_UNCERTAIN';
      result.reason = 'source_git_identity_unavailable';
      result.lifecycle.blockers = [...new Set([...result.lifecycle.blockers, 'source_git_identity_unavailable'])];
    }
  }
  if (runtimeStateHasLiveManagedProcess(paths)) {
    result.safe = false;
    result.code = 'RUNTIME_BUSY';
    result.reason = 'live_runtime_state_process';
    result.lifecycle.blockers = [...new Set([...result.lifecycle.blockers, 'live_runtime_state_process'])];
  }
  if (result.mutated_canonical_ledger === true || result.content_free !== true) {
    result.safe = false;
    result.code = 'ORCHESTRATION_STATE_UNCERTAIN';
    result.reason = 'canonical_census_contract_invalid';
  }
  result.census_fingerprint = crypto.createHash('sha256').update(JSON.stringify({
    snapshot: {
      sha256: result.snapshot.sha256,
      logical_sha256: result.snapshot.logical_sha256,
      size_bytes: result.snapshot.size_bytes,
      schema_version: result.snapshot.schema_version,
      integrity_check: result.snapshot.integrity_check,
      foreign_key_check_rows: result.snapshot.foreign_key_check_rows,
      backup_api_copy: result.snapshot.backup_api_copy,
      immutable: result.snapshot.immutable,
      query_only: result.snapshot.query_only
    },
    counts: result.counts,
    lifecycle: result.lifecycle,
    workspace: result.workspace,
    ledger_path: result.ledger_path
  })).digest('hex');
  if (holdExclusive) {
    if (raw?.exclusive_gate_held !== true || typeof releaseExclusive !== 'function') {
      if (releaseExclusive) await releaseExclusive().catch(() => false);
      throw Object.assign(new Error('Canonical ledger census did not prove its exclusive gate.'), { code: 'ORCHESTRATION_STATE_UNCERTAIN' });
    }
    Object.defineProperty(result, 'release_exclusive_gate', {
      value: releaseExclusive,
      configurable: false,
      enumerable: false,
      writable: false
    });
  }
  return result;
}

/**
 * Recovery Host-owned transaction for an operator/revision restart.
 *
 * The coordinator deliberately owns only the control-plane transaction.  It
 * never deletes the workspace ledger, task history, acceptance receipts,
 * settings, secrets, or device identity.  Child services receive the epoch via
 * their launch options/environment and remain admission-closed until the
 * final current-process census is explicitly verified.
 */
class FullCleanActivation {
  constructor({
    paths,
    settings,
    secrets,
    orchestrator,
    recoveryPlane = null,
    revisions = null,
    deviceIdentity = null,
    recoveryInstanceId = '',
    actionStore = null,
    log = null,
    spawnRecoveryReplacement = null,
    spawnElectronUi = null,
    getUiRegistration = null,
    getUiPresence = null,
    getUiRevision = null,
    terminateUi = null,
    getRecoveryPlaneStatus = null,
    canonicalLedgerCensus = null,
    scheduleHandoff = null,
    setActivationEpoch = null,
    recoveryHostRunningRevision = '',
    now = () => Date.now(),
    waitFn = wait,
    epochStore = null
  } = {}) {
    if (!paths) throw new Error('Full clean activation requires runtime paths.');
    this.paths = paths;
    this.settings = settings;
    this.secrets = secrets;
    this.orchestrator = orchestrator;
    this.recoveryPlane = recoveryPlane;
    this.revisions = revisions;
    this.deviceIdentity = deviceIdentity;
    this.recoveryInstanceId = text(recoveryInstanceId);
    this.actionStore = actionStore;
    this.log = log;
    this.spawnRecoveryReplacement = spawnRecoveryReplacement;
    this.spawnElectronUi = spawnElectronUi;
    this.getUiRegistration = getUiRegistration;
    this.getUiPresence = getUiPresence;
    this.getUiRevision = getUiRevision;
    this.terminateUi = terminateUi;
    this.getRecoveryPlaneStatus = getRecoveryPlaneStatus;
    this.canonicalLedgerCensus = canonicalLedgerCensus;
    this.scheduleHandoff = scheduleHandoff;
    this.setActivationEpochCallback = setActivationEpoch;
    this.recoveryHostRunningRevision = text(recoveryHostRunningRevision);
    this.now = now;
    this.wait = waitFn;
    this.store = epochStore || new ActivationEpochStore({ paths, now });
    this.inFlight = null;
    this.inFlightRequestKey = null;
  }

  current() { return this.store.current(); }
  enforceCurrentExpiry(boundary = 'observe') { return this.store.enforceCurrentExpiry(boundary); }

  /**
   * Persist the latest non-terminal census while a replacement activation is
   * waiting for one of its external gates (normally connector discovery).
   *
   * A replacement host can observe a better Tunnel/Recovery-Plane result than
   * the one captured during its first cold-start census.  Keeping that result
   * only in memory leaves the durable epoch stale forever and makes every
   * status reader report the old blocker.  This method deliberately records
   * evidence only; it never opens admission or changes a terminal epoch.
   */
  recordPendingCensus(activationEpochId, census) {
    const epochId = text(activationEpochId);
    if (!epochId || !census || typeof census !== 'object' || Array.isArray(census)) {
      throw epochError('ACTIVATION_CENSUS_INVALID', 'A pending activation census is required.');
    }
    const current = this.store.current();
    if (!current || String(current.activation_epoch_id || '') !== epochId) {
      throw epochError('ACTIVATION_EPOCH_NOT_CURRENT', 'Pending activation census must target the current durable epoch.');
    }
    // Evidence refresh is legal only after handoff begins replacement assembly.
    // In particular, never regress coordinator-owned STOPPING back to VERIFYING.
    if (!['STARTING', 'VERIFYING'].includes(String(current.state || ''))) {
      throw epochError('ACTIVATION_EPOCH_STATE_INVALID', 'Pending activation census requires a post-handoff assembly state.', {
        activation_epoch_id: epochId,
        state: current.state || null
      });
    }
    if (String(census.activation_epoch_id || '') !== epochId) {
      throw epochError('ACTIVATION_EPOCH_ID_MISMATCH', 'Pending activation census belongs to another activation epoch.', {
        activation_epoch_id: epochId,
        census_activation_epoch_id: String(census.activation_epoch_id || '') || null
      });
    }
    const next = this.store.update(epochId, {
      state: 'VERIFYING',
      reason: String(census.reason || 'waiting-for-connector-or-component'),
      verification: census
    });
    this._linkActionPending(next, { census, activation_state: 'VERIFYING' });
    return next;
  }

  // Device identity is durable at the install level, while
  // device_instance_id is the current Recovery Host lifecycle identity.  The
  // latter is deliberately fresh for every replacement process and is the
  // value propagated to MCP and the Recovery Plane.
  _deviceInstanceId() {
    return text(this.deviceIdentity?.device_instance_id) || this.recoveryInstanceId || null;
  }

  _linkedAction(operationId) {
    try { return this.actionStore?.get?.(operationId) || null; } catch { return null; }
  }

  _actionResult(epoch, overrides = {}) {
    return {
      full_clean_activation: true,
      activation_mode: 'full_clean_activation',
      activation_epoch_id: epoch?.activation_epoch_id || null,
      operation_id: epoch?.operation_id || null,
      state: epoch?.state || 'UPDATE_INCOMPLETE',
      admission_open: epoch?.admission_state === 'OPEN',
      fully_ready: epoch?.state === 'READY' && epoch?.admission_state === 'OPEN',
      ...overrides
    };
  }

  _linkActionPending(epoch, details = {}) {
    const operationId = String(epoch?.operation_id || '').trim();
    if (!operationId || !this.actionStore?.defer) return null;
    const action = this._linkedAction(operationId);
    if (!action || ['completed', 'failed', 'refused'].includes(action.state)) return action;
    return this.actionStore.defer(operationId, this._actionResult(epoch, {
      state: epoch.state,
      admission_open: false,
      fully_ready: false,
      ...details
    }), null);
  }

  _finishLinkedAction(epoch, state, result = null, error = null) {
    const operationId = String(epoch?.operation_id || '').trim();
    if (!operationId || !this.actionStore?.finish) return null;
    const action = this._linkedAction(operationId);
    if (!action || ['completed', 'failed', 'refused'].includes(action.state)) return action;
    return this.actionStore.finish(operationId, state, result, error);
  }

  setActivationEpoch(epochId) {
    const id = text(epochId);
    this.orchestrator?.setActivationEpoch?.(id);
    this.recoveryPlane?.setActivationEpoch?.(id);
    this.setActivationEpochCallback?.(id);
    return id;
  }

  /**
   * Persist a terminal failure without allowing cleanup/reporting to mask the
   * original activation error.  The durable store is intentionally fail
   * closed: a failed epoch keeps admission CLOSED and can only be replaced by
   * a later, explicitly requested activation.  This helper is used on every
   * replacement-start failure boundary, including failures that happen before
   * the normal transaction body has reached its first state transition.
   */
  _failEpoch(epochId, failure) {
    const id = text(epochId);
    if (!id) return null;
    try {
      const failed = this.store.fail(id, failure);
      this._finishLinkedAction(failed, 'failed', this._actionResult(failed, {
        state: 'FAILED',
        admission_open: false,
        fully_ready: false
      }), failure);
      return failed;
    } catch (error) {
      // A concurrent terminal transition (normally finalize() or another
      // supervisor turn) is safe and idempotent.  Any other persistence error
      // must not replace the original failure, but is recorded for operators.
      if (String(error?.code || '') !== 'ACTIVATION_EPOCH_TERMINAL') {
        this.log?.error?.(error.message, {
          stage: 'full-clean-activation-failure-persist',
          activationEpochId: id,
          code: error?.code || ''
        });
      }
      return null;
    }
  }

  /**
   * Once a durable full-clean epoch exists, the previous component set is no
   * longer an admissible runtime.  If the transaction fails before the normal
   * STOPPING boundary (for example a fence race or replacement-launch error),
   * stop only the components owned by this Recovery Host before publishing a
   * terminal FAILED epoch.  This prevents a healthy-looking old MCP/Tunnel/UI
   * from continuing under the retired activation epoch while the durable
   * supervisor projection says admission is closed.  Never terminate the
   * Recovery Host itself here; it must remain available to accept the next
   * explicit operator activation.
   */
  async _failClosedOwnedRuntime(epochId) {
    const ui = this.getUiPresence?.() || {};
    if (ui.alive && typeof this.terminateUi === 'function') {
      try { await this.terminateUi(ui); }
      catch (error) {
        this.log?.error?.(error.message, {
          stage: 'full-clean-failure-ui-stop',
          activationEpochId: text(epochId),
          code: error?.code || ''
        });
      }
    }
    if (typeof this.orchestrator?.stop === 'function') {
      try {
        await this.orchestrator.stop({
          manual: false,
          fullClean: true,
          activationEpochId: text(epochId)
        });
      } catch (error) {
        this.log?.error?.(error.message, {
          stage: 'full-clean-failure-runtime-stop',
          activationEpochId: text(epochId),
          code: error?.code || ''
        });
      }
    }
    if (typeof this.recoveryPlane?.stop === 'function') {
      try { await this.recoveryPlane.stop(); }
      catch (error) {
        this.log?.error?.(error.message, {
          stage: 'full-clean-failure-recovery-plane-stop',
          activationEpochId: text(epochId),
          code: error?.code || ''
        });
      }
    }
  }

  _settings() {
    const value = this.settings?.load?.() || {};
    if (!value || typeof value !== 'object') throw epochError('FULL_CLEAN_SETTINGS_UNAVAILABLE', 'Runtime settings could not be loaded.');
    return value;
  }

  _componentRevisions() {
    const result = {};
    for (const component of COMPONENTS) {
      try {
        const status = component === 'coding_mcp' && this.orchestrator?.codingMcpRevisionStatus
          ? this.orchestrator.codingMcpRevisionStatus({ force: true })
          : this.revisions?.status?.(component, null, { force: true });
        result[component] = {
          disk_revision: text(status?.disk_revision) || null,
          running_revision: text(status?.running_revision) || null,
          update_pending: status?.update_pending ?? null
        };
      } catch (error) {
        result[component] = { state: 'unavailable', error_code: String(error?.code || 'REVISION_UNAVAILABLE') };
      }
    }
    return result;
  }

  /**
   * Capture the identities that existed before the old runtime is stopped.
   * These values are immutable evidence on the epoch record; the final census
   * must prove that every replacement is a genuinely new process/runtime.
   */
  async _captureIdentityEvidence() {
    const state = readJson(this.paths.stateFile?.() || '', {});
    let health = null;
    try {
      health = await this.orchestrator?.currentMcpHealth?.();
    } catch { /* stopped/unreachable MCP is represented by null evidence */ }
    const plane = this.getRecoveryPlaneStatus?.() || this.recoveryPlane?.lastStatus || {};
    const planeState = this.recoveryPlane?.readState?.() || {};
    const ui = this.getUiPresence?.() || {};
    const numeric = (value) => Number.isSafeInteger(Number(value)) && Number(value) > 0 ? Number(value) : null;
    return {
      device_id: this.deviceIdentity?.device_id || null,
      device_instance_id: this._deviceInstanceId(),
      recovery_host: {
        instance_id: this.recoveryInstanceId || null,
        pid: numeric(process.pid)
      },
      coding_mcp: {
        process_instance_id: text(health?.process_instance_id) || null,
        server_instance_id: text(health?.instance_id || health?.server_instance_id) || null,
        supervisor_instance_id: text(state.nativeInstanceId) || null,
        pid: numeric(state.nativePid)
      },
      coding_tunnel: {
        instance_id: text(state.tunnelInstanceId) || null,
        pid: numeric(state.tunnelPid)
      },
      recovery_mcp: {
        instance_id: text(plane.mcp?.instance_id || plane.mcp?.process_instance_id || planeState.recoveryMcpInstanceId) || null,
        pid: numeric(plane.mcp?.pid || planeState.recoveryMcpPid)
      },
      recovery_tunnel: {
        instance_id: text(plane.tunnel?.instance_id || plane.tunnel?.process_instance_id || planeState.recoveryTunnelInstanceId) || null,
        pid: numeric(plane.tunnel?.pid || planeState.recoveryTunnelPid)
      },
      electron_ui: {
        instance_id: text(ui.instance_id) || null,
        pid: numeric(ui.pid),
        process_start_token: text(ui.process_start_token) || null
      }
    };
  }

  async preflight({ operationId: requestedOperationId = '', sourceCheckpoint = null, allowAcceptancePending = false } = {}) {
    if (this.orchestrator?.busy || this.orchestrator?.recovering) {
      throw epochError('RUNTIME_BUSY', 'Runtime is busy; full clean activation was not admitted.');
    }
    let runtime = { safe: true, code: 'COMPONENT_STOPPED' };
    if (typeof this.orchestrator?.inspectCodeActivation === 'function') {
      runtime = await this.orchestrator.inspectCodeActivation({ operationId: text(requestedOperationId) });
      const allowed = runtime?.code === 'COMPONENT_STOPPED'
        || runtime?.safe === true
        || (runtime?.code === 'ACCEPTANCE_PENDING' && allowAcceptancePending === true);
      if (!allowed) throw epochError(runtime?.code || 'ORCHESTRATION_STATE_UNCERTAIN', 'Canonical runtime lifecycle preflight refused full clean activation.', runtime);
    }
    // When Coding MCP is stopped there is no process left to answer the
    // normal activation preflight endpoint.  Read the canonical ledger through
    // the independent Backup-API/query-only census helper before admitting a
    // replacement.  The resulting receipt is carried in the immutable epoch
    // request and is rechecked immediately before any stop/spawn mutation.
    if (runtime?.code === 'COMPONENT_STOPPED') {
      if (typeof this.canonicalLedgerCensus !== 'function') {
        throw epochError('ORCHESTRATION_STATE_UNCERTAIN', 'Full clean activation cannot admit a stopped runtime without an independent canonical ledger census.');
      }
      let census;
      try {
        census = await this.canonicalLedgerCensus({
          workspace: this._settings().workspace,
          sourceCheckpoint,
          allowAcceptancePending: allowAcceptancePending === true
        });
      } catch (error) {
        throw epochError(String(error?.code || 'ORCHESTRATION_STATE_UNCERTAIN'), 'Canonical ledger census was unavailable for stopped-runtime activation.', {
          message: String(error?.message || ''),
          cause_code: String(error?.cause?.code || '') || null
        });
      }
      if (!census || census.safe !== true) {
        throw epochError(census?.code || 'ORCHESTRATION_STATE_UNCERTAIN', 'Canonical ledger census refused stopped-runtime activation.', census || {});
      }
      runtime = {
        ...runtime,
        lifecycle: census,
        canonical_ledger_census: census
      };
    }
    return {
      safe: true,
      code: runtime?.code || 'READY',
      operation_id: text(requestedOperationId) || null,
      source_checkpoint: sourceCheckpoint || null,
      runtime,
      component_revisions: this._componentRevisions(),
      settings: {
        workspace: text(this._settings().workspace),
        device_id: text(this.deviceIdentity?.device_id) || null,
        device_instance_id: this._deviceInstanceId()
      },
      observed_at: new Date(this.now()).toISOString()
    };
  }

  _beginRecord({ operation_id, source_checkpoint, preflight, metadata = {}, activation_epoch_id = undefined, component_evidence = null } = {}) {
    const uiPresence = this.getUiPresence?.() || {};
    return this.store.create({
      ...(activation_epoch_id ? { activation_epoch_id } : {}),
      operation_id,
      mode: 'full_clean_activation',
      components: COMPONENTS,
      source_checkpoint,
      ledger_snapshot: preflight?.runtime?.lifecycle?.snapshot || preflight?.runtime?.lifecycle || null,
      component_revisions: preflight?.component_revisions || this._componentRevisions(),
      component_evidence: component_evidence || {
        recovery_host: { instance_id: this.recoveryInstanceId || null },
        electron_ui: {
          instance_id: uiPresence.instance_id || null,
          pid: uiPresence.pid || null,
          process_start_token: uiPresence.process_start_token || null
        },
        device_id: this.deviceIdentity?.device_id || null,
      device_instance_id: this._deviceInstanceId()
      },
      owner_instance_id: this.recoveryInstanceId || null,
      owner_pid: process.pid,
      expires_at_unix_ms: Number(metadata.expires_at_unix_ms || 0) || null,
      metadata: { ...metadata, reason: metadata.reason || 'operator_restart' }
    });
  }

  async _prepareFence(operationIdValue, expiresAtUnixMs, sourceCheckpoint, allowAcceptancePending) {
    if (typeof this.orchestrator?.prepareCodeActivation !== 'function') return null;
    const nowUnixMs = this.now();
    const prepareExpiresAtUnixMs = Math.min(
      Number(expiresAtUnixMs || 0),
      nowUnixMs + MCP_PREPARE_FENCE_TTL_MS
    );
    if (!Number.isSafeInteger(prepareExpiresAtUnixMs) || prepareExpiresAtUnixMs <= nowUnixMs) {
      throw epochError('ACTIVATION_REQUEST_EXPIRED', 'Full clean activation request expired before Coding MCP preparation.');
    }
    try {
      return await this.orchestrator.prepareCodeActivation({
        operationId: operationIdValue,
        expiresAtUnixMs: prepareExpiresAtUnixMs,
        allowAcceptancePending: allowAcceptancePending === true,
        ...(sourceCheckpoint ? { sourceCheckpoint } : {})
      });
    } catch (error) {
      if (String(error?.code || '') === 'COMPONENT_STOPPED') return { code: 'COMPONENT_STOPPED', safe: true, fenced: false };
      throw error;
    }
  }

  _requireExactPreparedFence(fence, operationIdValue, stage) {
    const expectedOperationId = text(operationIdValue);
    if (!fence
      || fence.safe !== true
      || fence.fenced !== true
      || text(fence.fence_operation_id) !== expectedOperationId) {
      throw epochError(
        'ACTIVATION_PREFLIGHT_UNVERIFIED',
        `Full clean activation requires an exact checkpoint-bound runtime fence ${stage}.`,
        { fence, operation_id: expectedOperationId, stage }
      );
    }
    return fence;
  }

  async _freshActivationObservation(record) {
    const sourceCheckpoint = record?.source_checkpoint;
    let raw;
    if (sourceCheckpoint && typeof this.orchestrator?.verifyCodeActivation === 'function') {
      raw = await this.orchestrator.verifyCodeActivation(record.operation_id, sourceCheckpoint);
    } else if (!sourceCheckpoint && typeof this.orchestrator?.inspectCodeActivation === 'function') {
      // Operator/UI restarts do not necessarily originate from an accepted
      // RUN/WAVE checkpoint.  The authenticated GET preflight is still
      // mandatory: it reconciles the runtime projection and builds the
      // process-local receipt that complete_activation_epoch later consumes.
      raw = await this.orchestrator.inspectCodeActivation({ operationId: record.operation_id });
    } else {
      throw epochError('LIFECYCLE_VERIFICATION_FAILED', 'Full clean activation cannot obtain a fresh runtime lifecycle observation.');
    }
    const lifecycle = raw?.lifecycle && typeof raw.lifecycle === 'object' ? raw.lifecycle : {};
    const snapshot = lifecycle.snapshot && typeof lifecycle.snapshot === 'object' ? lifecycle.snapshot : {};
    const counts = raw?.counts && typeof raw.counts === 'object' ? raw.counts : {};
    const source = raw?.source_checkpoint && typeof raw.source_checkpoint === 'object' ? raw.source_checkpoint : {};
    const sourceMatches = !sourceCheckpoint || (source.ok === true
      && source.code === 'ACTIVATABLE'
      && source.checkpoint_id === sourceCheckpoint.checkpoint_id
      && source.run_id === sourceCheckpoint.run_id
      && source.wave_id === sourceCheckpoint.wave_id
      && source.proof_fingerprint === sourceCheckpoint.proof_fingerprint
      && source.git_head === sourceCheckpoint.git_head);
    const countKeys = [
      'active_tool_calls', 'active_commands', 'starting_commands',
      'active_background_operations', 'active_managed_processes',
      'foreign_heavy_processes', 'active_agent_lanes',
      'threshold_sensitive_stale_candidates', 'owned_codex_sidecar_residues'
    ];
    const normalizedCounts = Object.fromEntries(countKeys.map((key) => [key, Number.isSafeInteger(counts[key]) ? counts[key] : -1]));
    const canonicalLifecycleSnapshot = canonicalSnapshot(snapshot);
    const workspaceMatches = canonicalWorkspace(raw?.workspace) === canonicalWorkspace(this._settings().workspace);
    const clean = raw?.safe === true
      && raw?.code === 'READY'
      && sourceMatches
      && canonicalLifecycleSnapshot
      && workspaceMatches
      && raw?.fenced === false
      && raw?.fence_operation_id == null
      && countKeys.slice(0, 7).every((key) => normalizedCounts[key] === 0)
      && Number(lifecycle.unexplained_active_runs || 0) === 0
      && Number(lifecycle.unbound_live_resource_residues || 0) === 0;
    const decision = {
      schema_version: 1,
      clean: clean && Boolean(sourceCheckpoint) && raw?.operation_id === record.operation_id,
      code: String(raw?.code || 'ORCHESTRATION_STATE_UNCERTAIN'),
      reason: String(raw?.reason || ''),
      observed_at: new Date(this.now()).toISOString(),
      canonical_lifecycle_observed: canonicalLifecycleSnapshot,
      source_checkpoint_verified: Boolean(sourceCheckpoint) && sourceMatches,
      fence_released: raw?.fenced === false && raw?.fence_operation_id == null,
      fenced: raw?.fenced === true,
      fence_operation_id: raw?.fence_operation_id || null,
      counts: normalizedCounts,
      unexplained_active_runs: Number.isSafeInteger(lifecycle.unexplained_active_runs) ? lifecycle.unexplained_active_runs : -1,
      unbound_live_resource_residues: Number.isSafeInteger(lifecycle.unbound_live_resource_residues) ? lifecycle.unbound_live_resource_residues : -1,
      operation_id: record.operation_id
    };
    const normalized = sourceCheckpoint ? normalizeLifecycleDecision(decision) : null;
    if (!clean || (sourceCheckpoint && (!normalized || !lifecycleDecisionIsClean(normalized)))) {
      throw epochError('LIFECYCLE_VERIFICATION_FAILED', 'Full clean activation did not receive a fresh checkpoint-bound unfenced lifecycle proof.', {
        operation_id: record.operation_id,
        observation: {
          safe: raw?.safe === true,
          code: text(raw?.code) || null,
          reason: text(raw?.reason) || null,
          observed_operation_id: text(raw?.operation_id) || null,
          workspace: text(raw?.workspace) || null,
          fenced: raw?.fenced === true,
          fence_operation_id: text(raw?.fence_operation_id) || null,
          counts: raw?.counts && typeof raw.counts === 'object' ? raw.counts : null,
          lifecycle: lifecycle && typeof lifecycle === 'object' ? {
            projection_classification: text(lifecycle.projection_classification || lifecycle.projection?.classification) || null,
            unexplained_active_runs: lifecycle.unexplained_active_runs ?? null,
            unbound_live_resource_residues: lifecycle.unbound_live_resource_residues ?? null,
            projection_rebuild: lifecycle.projection_rebuild && typeof lifecycle.projection_rebuild === 'object'
              ? { current: lifecycle.projection_rebuild.current === true, validation: lifecycle.projection_rebuild.validation || null }
              : null
          } : null
        },
        source_checkpoint_verified: sourceMatches,
        canonical_lifecycle_observed: canonicalLifecycleSnapshot,
        workspace_matches: workspaceMatches,
        fenced: raw?.fenced,
        fence_operation_id: raw?.fence_operation_id || null
      });
    }
    return {
      lifecycle_decision: normalized,
      checkpoint_bound: Boolean(sourceCheckpoint),
      snapshot,
      projection: lifecycle.projection && typeof lifecycle.projection === 'object' ? lifecycle.projection : {},
      projection_classification: text(lifecycle.projection_classification || lifecycle.projection?.classification).toUpperCase(),
      projection_rebuild: lifecycle.projection_rebuild && typeof lifecycle.projection_rebuild === 'object'
        ? lifecycle.projection_rebuild : null,
      projection_rebuild_receipt: lifecycle.projection_rebuild_receipt
        && typeof lifecycle.projection_rebuild_receipt === 'object'
        ? lifecycle.projection_rebuild_receipt : null
    };
  }

  async _freshLifecycle(record) {
    const observation = await this._freshActivationObservation(record);
    return observation.lifecycle_decision;
  }

  _componentPostflights(record, census, lifecycle) {
    if (!record?.source_checkpoint || !lifecycle || !lifecycleDecisionIsClean(lifecycle)) return {};
    const evidence = record.component_evidence || {};
    const current = {
      recovery_host: {
        instance_id: text(census.host_instance_id),
        running_revision: text(census.recovery_host_running_revision)
      },
      coding_mcp: {
        instance_id: text(census.process_instance_id),
        running_revision: text(census.running_revision || census.runtime?.codeRevision?.codingMcp?.running_revision)
      },
      electron_ui: {
        instance_id: text(census.ui_instance_id),
        running_revision: text(census.ui_running_revision)
      }
    };
    const result = {};
    for (const component of COMPONENTS) {
      const expectedRevision = text(record.component_revisions?.[component]?.disk_revision);
      const old = evidence[component] && typeof evidence[component] === 'object' ? evidence[component] : {};
      const oldId = text(old.instance_id || old.process_instance_id);
      const newId = current[component].instance_id;
      const runningRevision = current[component].running_revision;
      if (!expectedRevision || !newId || !runningRevision) continue;
      const request = {
        operation_id: record.operation_id,
        component,
        expected_disk_revision: expectedRevision,
        source_checkpoint: record.source_checkpoint
      };
      const candidate = activationPostflight(request, {
        oldInstanceState: oldId ? 'RUNNING' : 'ABSENT',
        oldInstanceId: oldId || null,
        newInstanceId: newId,
        runningRevision,
        diskRevision: runningRevision,
        startedAt: record.started_at || record.created_at,
        completedAt: new Date(this.now()).toISOString(),
        healthVerified: true,
        lifecycle,
        revisionContract: 'current'
      });
      const verified = verifyActivationPostflight(candidate, {
        operationId: record.operation_id,
        component,
        checkpoint: record.source_checkpoint,
        expectedRevision
      });
      if (verified.ok) result[component] = verified.postflight;
    }
    return result;
  }

  async restart(options = {}) {
    if (options.automatic === true || options.mode === 'soft_recovery' || options.soft === true) {
      if (typeof this.orchestrator?.restart !== 'function') throw epochError('SOFT_RESTART_UNAVAILABLE', 'Soft restart is unavailable.');
      return this.orchestrator.restart({ ...options, automatic: true, mode: 'soft_recovery' });
    }
    // Code/revision activation remains an accepted-checkpoint transaction.
    // `refresh` is the explicit operator process-refresh surface used by
    // `npm start`: it still gets the same durable epoch, census, handoff and
    // final admission gates, but it is not allowed to invent a RUN/WAVE
    // checkpoint for an operation that is only refreshing the installation.
    const refresh = options?.refresh === true || options?.mode === 'full_clean_refresh';
    const sourceCheckpoint = refresh ? null : requireCanonicalSourceCheckpoint(options?.sourceCheckpoint);
    const requestedOperationId = text(options.operationId) || operationId();
    const requestKey = canonicalJson({
      operation_id: requestedOperationId,
      source_checkpoint: sourceCheckpoint,
      refresh,
      component: text(options.component) || 'coding_mcp',
      expected_disk_revision: text(options.expectedDiskRevision) || null,
      activation_epoch_id: text(options.activationEpochId) || null,
      expires_at_unix_ms: options.expiresAtUnixMs == null ? null : Number(options.expiresAtUnixMs),
      allow_acceptance_pending: options.allowAcceptancePending === true
    });
    if (this.inFlight) {
      if (this.inFlightRequestKey === requestKey) return this.inFlight;
      throw epochError('RUNTIME_BUSY', 'Another full-clean activation operation is already in flight.', {
        requested_operation_id: requestedOperationId
      });
    }
    this.inFlightRequestKey = requestKey;
    const tracked = this._restart({ ...options, refresh, operationId: requestedOperationId, sourceCheckpoint }).finally(() => {
      if (this.inFlight === tracked) {
        this.inFlight = null;
        this.inFlightRequestKey = null;
      }
    });
    this.inFlight = tracked;
    return tracked;
  }

  async _restart(options = {}) {
    const refresh = options?.refresh === true || options?.mode === 'full_clean_refresh';
    const sourceCheckpoint = refresh ? null : requireCanonicalSourceCheckpoint(options?.sourceCheckpoint);
    options = { ...options, refresh, sourceCheckpoint };
    const operation_id = text(options.operationId) || operationId();
    const expiresAtUnixMs = Number(options.expiresAtUnixMs || (this.now() + DEFAULT_TTL_MS));
    if (!Number.isSafeInteger(expiresAtUnixMs) || expiresAtUnixMs <= this.now()) throw epochError('ACTIVATION_REQUEST_EXPIRED', 'Full clean activation request is expired.');
    // Idempotent replay is bound to the durable epoch, not merely to a caller
    // supplied operation id. A retry after Recovery Host handoff must resume
    // the existing transaction and never create a second epoch.
    const existing = this.store.current();
    if (existing && existing.operation_id === operation_id) {
      const suppliedEpochId = text(options.activationEpochId);
      if (suppliedEpochId && existing.activation_epoch_id !== suppliedEpochId) {
        throw epochError('ACTIVATION_EPOCH_ID_MISMATCH', 'The replay activation epoch does not match the current durable operation.', {
          activation_epoch_id: suppliedEpochId,
          current_activation_epoch_id: existing.activation_epoch_id,
          operation_id
        });
      }
      if (existing.state === 'FAILED') throw epochError('UPDATE_INCOMPLETE', 'The requested activation epoch has failed and remains admission-closed.', { activation_epoch_id: existing.activation_epoch_id });
      this.setActivationEpoch(existing.activation_epoch_id);
      const linked = this._linkedAction(operation_id);
      if (existing.state === 'READY') return linked || this._actionResult(existing, { census: existing.verification?.final_census || null });
      this._linkActionPending(existing, { activation_epoch_id: existing.activation_epoch_id });
      return this._linkedAction(operation_id) || this._actionResult(existing);
    }
    // A caller-supplied epoch is only valid for an idempotent replay that is
    // still represented by the current durable record.  Never recreate an old
    // epoch ID from an action record after the epoch store has been lost,
    // compacted, or replaced; that would make a stale handoff look like a new
    // activation transaction.
    const requestedEpochId = text(options.activationEpochId);
    if (requestedEpochId) {
      const suppliedRecord = this.store.load(requestedEpochId);
      if (!existing
        || existing.activation_epoch_id !== requestedEpochId
        || !suppliedRecord
        || suppliedRecord.operation_id !== operation_id
        || suppliedRecord.activation_epoch_id !== requestedEpochId) {
        throw epochError('ACTIVATION_EPOCH_NOT_CURRENT', 'The supplied activation epoch is not the current durable replay target.', {
          activation_epoch_id: requestedEpochId,
          operation_id
        });
      }
    }
    // Terminalize an expired active epoch before a new explicit request is
    // considered, so a stale transaction cannot block the system forever.
    if (existing && this.store.isStale(existing.activation_epoch_id, this.now())) {
      this._failEpoch(existing.activation_epoch_id, epochError('ACTIVATION_REQUEST_EXPIRED', 'The previous activation epoch expired before completion.'));
    }
    const preflight = await this.preflight({
      operationId: operation_id,
      sourceCheckpoint: options.sourceCheckpoint || null,
      allowAcceptancePending: options.allowAcceptancePending === true
    });
    // Revision activation requests are immutable contracts.  Do not silently
    // activate whatever happens to be on disk if the requested component moved
    // again while the request was waiting for preflight; require a fresh
    // explicit request instead.
    const expectedDiskRevision = text(options.expectedDiskRevision);
    if (expectedDiskRevision) {
      const component = text(options.component) || 'coding_mcp';
      const observedRevision = text(preflight.component_revisions?.[component]?.disk_revision);
      if (!observedRevision || observedRevision !== expectedDiskRevision) {
        throw epochError('REVISION_CHANGED', 'Requested component revision changed before full-clean activation.', {
          component,
          expected_revision: expectedDiskRevision,
          observed_revision: observedRevision || null
        });
      }
    }
    if (preflight.runtime?.code === 'COMPONENT_STOPPED') {
      const census = preflight.runtime?.canonical_ledger_census;
      const snapshot = census?.snapshot;
      if (!census || census.safe !== true || !snapshot || snapshot.immutable !== true || snapshot.query_only !== true) {
        throw epochError('ORCHESTRATION_STATE_UNCERTAIN', 'Full clean activation refuses to stop/relaunch without a verified canonical ledger census.');
      }
      // A second independent read closes the race between the first census and
      // epoch creation.  If the canonical ledger moved, the operation is
      // refused before any owned process is stopped.
      if (typeof this.canonicalLedgerCensus !== 'function') {
        throw epochError('ORCHESTRATION_STATE_UNCERTAIN', 'Canonical ledger census cannot be refreshed before stopped-runtime activation.');
      }
      let refreshed;
      try {
        refreshed = await this.canonicalLedgerCensus({
          workspace: this._settings().workspace,
          sourceCheckpoint: options.sourceCheckpoint || null,
          allowAcceptancePending: options.allowAcceptancePending === true,
          holdExclusive: true
        });
      } catch (error) {
        throw epochError(String(error?.code || 'ORCHESTRATION_STATE_UNCERTAIN'), 'Canonical ledger census could not be refreshed before stopped-runtime activation.', {
          message: String(error?.message || ''),
          cause_code: String(error?.cause?.code || '') || null
        });
      }
      const sameSnapshot = refreshed?.safe === true
        && typeof refreshed.release_exclusive_gate === 'function'
        && refreshed.workspace === census.workspace
        && refreshed.ledger_path === census.ledger_path
        && refreshed.snapshot?.sha256 === snapshot.sha256
        && refreshed.snapshot?.logical_sha256 === snapshot.logical_sha256
        && refreshed.census_fingerprint === census.census_fingerprint;
      if (!sameSnapshot) {
        if (typeof refreshed?.release_exclusive_gate === 'function') {
          await refreshed.release_exclusive_gate().catch(() => false);
        }
        throw epochError('ORCHESTRATION_STATE_UNCERTAIN', 'Canonical ledger changed between stopped-runtime census and activation admission.', {
          initial_census_fingerprint: census.census_fingerprint || null,
          refreshed_census_fingerprint: refreshed?.census_fingerprint || null,
          initial_sha256: snapshot.sha256 || null,
          refreshed_sha256: refreshed?.snapshot?.sha256 || null
        });
      }
      preflight.runtime.canonical_ledger_census = refreshed;
      preflight.runtime.lifecycle = refreshed;
    }
    // Capture old process identities before any stop/mutation.  The evidence is
    // bound to this epoch and is later used to prove that every replacement is
    // fresh rather than merely reporting a non-empty persisted id.
    const heldCensus = preflight?.runtime?.canonical_ledger_census;
    const releaseExclusiveGate = typeof heldCensus?.release_exclusive_gate === 'function'
      ? heldCensus.release_exclusive_gate : null;
    let record = null;
    try {
      const componentEvidence = await this._captureIdentityEvidence();
      record = this._beginRecord({
        operation_id,
        source_checkpoint: options.sourceCheckpoint || null,
        preflight,
        component_evidence: componentEvidence,
        metadata: {
          reason: options.reason || 'operator_restart',
          allow_acceptance_pending: options.allowAcceptancePending === true,
          refresh: options.refresh === true,
          requested_at_unix_ms: this.now(),
          expires_at_unix_ms: expiresAtUnixMs,
          ...(text(heldCensus?.census_fingerprint)
            ? { ledger_census_fingerprint: text(heldCensus.census_fingerprint) }
            : {})
        },
        activation_epoch_id: options.activationEpochId
      });
    } catch (error) {
      if (releaseExclusiveGate) await releaseExclusiveGate().catch(() => false);
      throw error;
    }
    const epochId = record.activation_epoch_id;
    try {
      // The exclusive application ledger gate spans the second census and the
      // durable epoch create. Releasing it is the commit boundary: supported
      // writers cannot append between the verified snapshot and epoch binding.
      if (releaseExclusiveGate) await releaseExclusiveGate();
      this.setActivationEpoch(epochId);
      this.store.update(epochId, { state: 'ADMISSION_CLOSED', reason: 'new-admission-closed' });
      const fence = await this._prepareFence(operation_id, expiresAtUnixMs, options.sourceCheckpoint || null, options.allowAcceptancePending);
      const runtimeRunning = preflight.runtime?.code !== 'COMPONENT_STOPPED';
      if (runtimeRunning) this._requireExactPreparedFence(fence, operation_id, 'before stopping processes');
      if (!runtimeRunning && preflight.safe !== true) {
        throw epochError('ORCHESTRATION_STATE_UNCERTAIN', 'Stopped runtime did not provide a safe canonical preflight receipt.');
      }
      this.store.update(epochId, { state: 'FROZEN', reason: 'durable-state-checkpointed', verification: { preflight, fence } });
      this.store.update(epochId, { state: 'STOPPING', reason: 'stopping-old-runtime' });
      const uiPresence = this.getUiPresence?.() || {};
      if (uiPresence.alive && typeof this.terminateUi === 'function') {
        await this.terminateUi(uiPresence);
      }
      if (typeof this.orchestrator?.stop === 'function') {
        // UI termination may take longer than Coding MCP's bounded admission
        // fence. Renew the same operation immediately before the runtime stop
        // so no process mutation relies on an expired preparation receipt.
        if (runtimeRunning) {
          const stopFence = await this._prepareFence(
            operation_id,
            expiresAtUnixMs,
            options.sourceCheckpoint || null,
            options.allowAcceptancePending
          );
          this._requireExactPreparedFence(stopFence, operation_id, 'immediately before Coding MCP stop');
        }
        await this.orchestrator.stop({ manual: false, fullClean: true, activationEpochId: epochId });
      }
      if (typeof this.recoveryPlane?.stop === 'function') await this.recoveryPlane.stop();
      this.store.update(epochId, { state: 'HANDOFF', reason: 'replacement-recovery-host-requested' });
      if (typeof this.spawnRecoveryReplacement !== 'function') throw epochError('RECOVERY_REPLACEMENT_UNAVAILABLE', 'Full clean activation requires a Recovery Host replacement launcher.');
      await this.spawnRecoveryReplacement({
        operationId: operation_id,
        expectedOldInstanceId: this.recoveryInstanceId,
        activationEpochId: epochId,
        expiresAtUnixMs
      });
      this.scheduleHandoff?.(epochId, { operationId: operation_id, expiresAtUnixMs });
      const pending = this._linkActionPending(this.store.current(), {
        accepted: true,
        activation_epoch_id: epochId,
        activation_state: 'HANDOFF',
        census: null
      });
      return pending || { accepted: true, state: 'HANDOFF', activation_epoch_id: epochId, operation_id, admission_open: false, fully_ready: false };
    } catch (error) {
      await this._failClosedOwnedRuntime(epochId);
      this._failEpoch(epochId, error);
      this.log?.error?.(error.message, { stage: 'full-clean-activation', activationEpochId: epochId, code: error?.code || '' });
      throw error;
    }
  }

  async continueReplacement({ activationEpochId, expectedOldInstanceId = '', expiresAtUnixMs = 0 } = {}) {
    const epochId = text(activationEpochId);
    if (!epochId) return null;
    const record = this.store.current();
    if (!record || record.activation_epoch_id !== epochId) throw epochError('ACTIVATION_EPOCH_NOT_CURRENT', 'Replacement epoch is not the current durable activation.');
    try {
      if (record.state === 'FAILED') throw epochError('UPDATE_INCOMPLETE', 'Replacement epoch is failed and remains admission-closed.');
      // The durable record is authoritative for expiry.  Replacement argv is
      // intentionally only a routing hint and does not carry the deadline;
      // never let a missing/stale argv value resurrect an expired transaction.
      const durableExpiry = Number(record.expires_at_unix_ms || record.metadata?.expires_at_unix_ms || 0);
      const suppliedExpiry = Number(expiresAtUnixMs || 0);
      if (durableExpiry > 0 && suppliedExpiry > 0 && durableExpiry !== suppliedExpiry) {
        throw epochError('ACTIVATION_EPOCH_EXPIRY_MISMATCH', 'Replacement expiry does not match the durable activation request.', {
          durable_expires_at_unix_ms: durableExpiry,
          supplied_expires_at_unix_ms: suppliedExpiry
        });
      }
      const effectiveExpiry = durableExpiry || suppliedExpiry;
      if (effectiveExpiry > 0 && this.now() >= effectiveExpiry) throw epochError('ACTIVATION_REQUEST_EXPIRED', 'Replacement activation request expired.');
      if (record.state === 'READY') {
        // A duplicate/late replacement process must not trust a terminal READY
        // bit by itself.  Re-census the live identities and epoch before
        // allowing this process to advertise readiness.
        const proof = await this.finalCensus(epochId, { expectedOldInstanceId });
        if (!proof.pass) throw epochError('UPDATE_INCOMPLETE', 'Durable READY activation lacks current-process proof.', proof);
        return { activation_epoch_id: epochId, state: 'READY', admission_open: true, fully_ready: true, census: proof };
      }
      this.setActivationEpoch(epochId);
      this.store.update(epochId, { state: 'STARTING', reason: 'replacement-loading-durable-runtime' });
      const settings = this._settings();
      if (typeof this.orchestrator?.start !== 'function') {
        throw epochError('RUNTIME_START_UNAVAILABLE', 'Full clean activation requires a Coding MCP runtime launcher.');
      }
      await this.orchestrator.start({
        automatic: true,
        fullClean: true,
        activationEpochId: epochId,
        activationGate: 'closed',
        activationAllowAcceptancePending: record.metadata?.allow_acceptance_pending === true,
        expiresAtUnixMs: effectiveExpiry
      });
      if (typeof this.recoveryPlane?.ensure !== 'function') {
        throw epochError('RECOVERY_PLANE_UNAVAILABLE', 'Full clean activation requires the Recovery MCP/Tunnel plane launcher.');
      }
      const token = await this.orchestrator?.ensureToken?.();
      const runtimeApiKey = this.secrets?.get?.('runtimeApiKey');
      await this.recoveryPlane.ensure(settings, { authToken: token, runtimeApiKey, activationEpochId: epochId });
      const registration = this.getUiRegistration?.();
      const uiPresent = this.getUiPresence?.() || {};
      if (!registration || registration.activation_epoch_id !== epochId || !uiPresent.alive) {
        if (typeof this.spawnElectronUi !== 'function') {
          throw epochError('UI_REPLACEMENT_UNAVAILABLE', 'Full clean activation requires an Electron UI replacement launcher.');
        }
        await this.spawnElectronUi({ activationEpochId: epochId, expiresAtUnixMs: effectiveExpiry });
      }
      this.store.update(epochId, { state: 'VERIFYING', reason: 'replacement-census' });
      const census = await this.finalCensus(epochId, { expectedOldInstanceId });
      if (!census.pass) {
        this.recordPendingCensus(epochId, census);
        return { activation_epoch_id: epochId, state: 'VERIFYING', admission_open: false, fully_ready: false, census };
      }
      return this.finalize(epochId, census);
    } catch (error) {
      await this._failClosedOwnedRuntime(epochId);
      this._failEpoch(epochId, error);
      throw error;
    }
  }

  async finalCensus(activationEpochId, {
    expectedOldInstanceId = '',
    reusePendingProjection = false,
    revalidateCommitted = false
  } = {}) {
    const epochId = text(activationEpochId);
    if (!epochId) throw epochError('ACTIVATION_EPOCH_ID_REQUIRED', 'Activation epoch is required for final census.');
    const record = this.store.current();
    if (!record || String(record.activation_epoch_id || '') !== epochId) {
      throw epochError('ACTIVATION_EPOCH_NOT_CURRENT', 'Final census must target the current durable activation epoch.');
    }
    const settings = this._settings();
    let activationObservation = null;
    let activationObservationFailure = null;
    let projectionObservationReused = false;
    if (reusePendingProjection === true) {
      activationObservation = reusablePendingProjectionObservation(record, {
        allowCommitted: revalidateCommitted === true
      });
      projectionObservationReused = Boolean(activationObservation);
    }
    if (!activationObservation) {
      try {
        // This call must precede health.  The MCP preflight reconciles the compact
        // projection and binds its receipt to one immutable ledger snapshot;
        // health must then expose that exact same process-local receipt.
        activationObservation = await this._freshActivationObservation(record);
      } catch (error) {
        activationObservationFailure = {
          code: text(error?.code) || 'LIFECYCLE_VERIFICATION_FAILED',
          message: text(error?.message) || 'Fresh activation observation failed.'
        };
      }
    }
    // The projection receipt is created by the preflight above. Capture one
    // bounded post-preflight health observation and reuse it for the runtime
    // snapshot so final census cannot contradict itself through a second short
    // liveness probe while the freshly launched UI is polling control state.
    let health = await this.orchestrator?.currentMcpHealth?.({
      timeoutMs: 15_000
    }).catch?.(() => null) || null;
    let censusNowUnixMs = this.now();
    const validateProjection = () => validateProjectionRebuildGate({
      preflight: activationObservation,
      health,
      expected: {
        activationEpochId: epochId,
        processInstanceId: text(health?.process_instance_id),
        serverInstanceId: text(health?.instance_id || health?.server_instance_id),
        workspace: settings.workspace,
        ledgerSnapshot: activationObservation?.snapshot
      },
      nowUnixMs: censusNowUnixMs
    });
    let projectionRebuild = validateProjection();
    let projectionObservationRefreshedAfterStaleReuse = false;
    if (projectionObservationReused && projectionRebuildFailedOnlyForStaleness(projectionRebuild)) {
      // A connector may arrive near the five-minute projection-receipt TTL.
      // Reusing that exact durable receipt is safe until it expires, but a
      // second independent finalize census can cross the TTL boundary. Refresh
      // only this time-based evidence. Any workspace/ledger/process/epoch or
      // receipt-integrity mismatch remains fail-closed and never reaches this
      // fallback.
      projectionObservationRefreshedAfterStaleReuse = true;
      projectionObservationReused = false;
      try {
        activationObservation = await this._freshActivationObservation(record);
        activationObservationFailure = null;
      } catch (error) {
        activationObservation = null;
        activationObservationFailure = {
          code: text(error?.code) || 'LIFECYCLE_VERIFICATION_FAILED',
          message: text(error?.message) || 'Fresh activation observation failed.'
        };
      }
      // The fresh preflight must precede the authoritative health receipt. The
      // first health read above only diagnosed the stale cached pair.
      health = await this.orchestrator?.currentMcpHealth?.({
        timeoutMs: 15_000
      }).catch?.(() => null) || null;
      censusNowUnixMs = this.now();
      projectionRebuild = validateProjection();
    }
    const runtime = await this.orchestrator?.lightweightSnapshot?.({ mcpHealth: health }) || {};
    let tunnelStatusVerified = runtime.tunnelRunning === true;
    if (typeof this.orchestrator?.tunnel?.status === 'function') {
      for (let attempt = 0; attempt < 3; attempt += 1) {
        try {
          tunnelStatusVerified = await this.orchestrator.tunnel.status(settings, { activationEpochId: epochId }) === true;
        } catch { tunnelStatusVerified = false; }
        if (tunnelStatusVerified) break;
        if (attempt < 2) await this.wait(250);
      }
    }
    const state = readJson(this.paths.stateFile?.() || '', {});
    const evidence = record.component_evidence && typeof record.component_evidence === 'object'
      ? record.component_evidence : {};
    const oldMcp = evidence.coding_mcp && typeof evidence.coding_mcp === 'object' ? evidence.coding_mcp : {};
    const oldTunnel = evidence.coding_tunnel && typeof evidence.coding_tunnel === 'object' ? evidence.coding_tunnel : {};
    const oldUi = evidence.electron_ui && typeof evidence.electron_ui === 'object' ? evidence.electron_ui : {};
    const oldRecoveryHost = evidence.recovery_host && typeof evidence.recovery_host === 'object' ? evidence.recovery_host : {};
    const numeric = (value) => Number.isSafeInteger(Number(value)) && Number(value) > 0 ? Number(value) : null;
    const currentMcpProcessId = text(health?.process_instance_id);
    const currentMcpServerId = text(health?.instance_id || health?.server_instance_id);
    const currentSupervisorId = text(state.nativeInstanceId);
    const currentMcpPid = numeric(state.nativePid);
    const currentTunnelId = text(state.tunnelInstanceId);
    const currentTunnelPid = numeric(state.tunnelPid);
    const expectedDeviceInstanceId = this._deviceInstanceId();
    let connectorContractStatus = null;
    try {
      connectorContractStatus = this.orchestrator?.connectorContractStatus?.(
        health?.tool_contract || null,
        health?.connector_tool_discovery || null,
        health?.connector_client_contact || null,
        health?.connector_activation_bootstrap || null,
        health
      ) || null;
    } catch { connectorContractStatus = null; }
    const identityChanged = (current, previous) => Boolean(current && (!text(previous) || current !== text(previous)));
    const epochMatches = Boolean(health && String(health.activation_epoch_id || '') === epochId
      && String(state.nativeActivationEpochId || '') === epochId
      && String(state.tunnelActivationEpochId || '') === epochId);
    const workspaceMatches = Boolean(settings.workspace && health && String(health.workspace || '').toLowerCase() === String(settings.workspace).toLowerCase());
    const deviceMatches = Boolean(!this.deviceIdentity?.device_id || (health
      && String(health.device_id || '').toLowerCase() === String(this.deviceIdentity.device_id).toLowerCase()
      && (!expectedDeviceInstanceId
        || String(health.device_instance_id || '') === String(expectedDeviceInstanceId))
      && (!state.nativeDeviceId || String(state.nativeDeviceId || '').toLowerCase() === String(this.deviceIdentity.device_id).toLowerCase())
      && (!state.nativeDeviceInstanceId
        || String(state.nativeDeviceInstanceId || '') === String(this._deviceInstanceId() || ''))));
    const revision = runtime?.codeRevision?.codingMcp || {};
    const expectedMcpRevision = text(record.component_revisions?.coding_mcp?.disk_revision);
    const stateMcpRevision = text(state.nativeCodeRevision);
    const revisionMatches = Boolean(revision.disk_revision && revision.running_revision
      && revision.disk_revision === revision.running_revision
      && (!stateMcpRevision || stateMcpRevision === revision.running_revision)
      && (!health?.code_revision || String(health.code_revision) === String(revision.running_revision))
      && (!expectedMcpRevision || revision.disk_revision === expectedMcpRevision));
    const tunnelEpochMatches = Boolean(currentTunnelPid && currentTunnelId
      && String(state.tunnelActivationEpochId || '') === epochId
      && state.tunnelFingerprint === tunnelFingerprint(settings, this.deviceIdentity?.device_id || '', epochId)
      && identityChanged(currentTunnelId, oldTunnel.instance_id)
      && (!oldTunnel.pid || currentTunnelPid !== numeric(oldTunnel.pid)));
    const boundOldHostId = text(oldRecoveryHost.instance_id);
    const oldHostPid = numeric(oldRecoveryHost.pid);
    const expectedHostId = text(expectedOldInstanceId) || boundOldHostId;
    const hostEvidenceBound = !boundOldHostId || !expectedOldInstanceId || boundOldHostId === text(expectedOldInstanceId);
    const hostChanged = Boolean(expectedHostId && this.recoveryInstanceId
      && String(this.recoveryInstanceId) !== expectedHostId
      && (!oldHostPid || Number(process.pid) !== oldHostPid)
      && hostEvidenceBound);
    const processIdentity = Boolean(currentMcpProcessId && currentMcpServerId && currentSupervisorId && currentMcpPid
      && isAlivePid(currentMcpPid)
      && identityChanged(currentMcpProcessId, oldMcp.process_instance_id)
      && identityChanged(currentMcpServerId, oldMcp.server_instance_id)
      && identityChanged(currentSupervisorId, oldMcp.supervisor_instance_id)
      && (!oldMcp.pid || currentMcpPid !== numeric(oldMcp.pid)));
    const recoveryHostRevision = (() => {
      try {
        return this.revisions?.status?.('recovery_host', this.recoveryHostRunningRevision || null, { force: true }) || {};
      } catch { return {}; }
    })();
    const expectedRecoveryRevision = text(record.component_revisions?.recovery_host?.disk_revision);
    const recoveryHostRevisionMatches = Boolean(recoveryHostRevision.disk_revision
      && recoveryHostRevision.running_revision
      && recoveryHostRevision.disk_revision === recoveryHostRevision.running_revision
      && (!expectedRecoveryRevision || recoveryHostRevision.disk_revision === expectedRecoveryRevision));
    // The Recovery Host is part of the activation epoch, not merely the
    // process that happens to own the lock.  Bind the durable descriptor to
    // this replacement's instance/PID and epoch so a stale descriptor cannot
    // make an otherwise healthy child set look fully ready.
    const recoveryHostDescriptor = (() => {
      try {
        return typeof this.paths?.recoveryHostDescriptorFile === 'function'
          ? readJson(this.paths.recoveryHostDescriptorFile(), {})
          : null;
      } catch { return null; }
    })();
    const recoveryHostEpochMatches = typeof this.paths?.recoveryHostDescriptorFile === 'function'
      ? Boolean(recoveryHostDescriptor
        && String(recoveryHostDescriptor.instance_id || '') === String(this.recoveryInstanceId || '')
        && Number(recoveryHostDescriptor.owner_pid) === Number(process.pid)
        && String(recoveryHostDescriptor.activation_epoch_id || '') === epochId
        && (!expectedDeviceInstanceId
          || String(recoveryHostDescriptor.device_instance_id || '') === String(expectedDeviceInstanceId))
      )
      : Boolean(this.recoveryInstanceId);
    const ui = this.getUiRegistration?.() || {};
    const uiPresence = this.getUiPresence?.() || {};
    const oldUiId = text(oldUi.instance_id);
    const uiRevision = this.getUiRevision?.({ force: true }) || runtime?.codeRevision?.electronUi || {};
    const expectedUiRevision = text(record.component_revisions?.electron_ui?.disk_revision);
    const uiReady = Boolean(uiPresence.alive && ui.instance_id && ui.activation_epoch_id === activationEpochId
      && identityChanged(String(ui.instance_id), oldUiId)
      && uiRevision.disk_revision && uiRevision.running_revision
      && uiRevision.disk_revision === uiRevision.running_revision
      && (!expectedUiRevision || uiRevision.disk_revision === expectedUiRevision));
    const plane = this.getRecoveryPlaneStatus?.() || this.recoveryPlane?.lastStatus || {};
    const planeState = this.recoveryPlane?.readState?.() || {};
    const oldRecoveryMcp = evidence.recovery_mcp && typeof evidence.recovery_mcp === 'object' ? evidence.recovery_mcp : {};
    const oldRecoveryTunnel = evidence.recovery_tunnel && typeof evidence.recovery_tunnel === 'object' ? evidence.recovery_tunnel : {};
    const currentRecoveryMcpPid = numeric(plane.mcp?.pid || planeState.recoveryMcpPid);
    const currentRecoveryMcpInstanceId = text(plane.mcp?.instance_id || planeState.recoveryMcpInstanceId);
    const currentRecoveryTunnelPid = numeric(plane.tunnel?.pid || planeState.recoveryTunnelPid);
    const currentRecoveryTunnelInstanceId = text(plane.tunnel?.instance_id || planeState.recoveryTunnelInstanceId);
    const recoveryMcpIdentityChanged = Boolean(currentRecoveryMcpPid && currentRecoveryMcpInstanceId
      && (!oldRecoveryMcp.pid || currentRecoveryMcpPid !== numeric(oldRecoveryMcp.pid))
      && identityChanged(currentRecoveryMcpInstanceId, oldRecoveryMcp.instance_id));
    const recoveryTunnelIdentityChanged = Boolean(currentRecoveryTunnelPid && currentRecoveryTunnelInstanceId
      && (!oldRecoveryTunnel.pid || currentRecoveryTunnelPid !== numeric(oldRecoveryTunnel.pid))
      && identityChanged(currentRecoveryTunnelInstanceId, oldRecoveryTunnel.instance_id));
    const recoveryMcpEpochMatches = Boolean(String(plane.activation_epoch_id || '') === epochId
      && String(plane.mcp?.activation_epoch_id || planeState.recoveryMcpActivationEpochId || '') === epochId);
    let recoveryMcpHealthVerified = false;
    let recoveryMcpHealthFailureKind = 'not_observed';
    if (currentRecoveryMcpPid && currentRecoveryMcpInstanceId && this.secrets?.get && settings.recoveryMcpPort) {
      try {
        const token = this.secrets.get('mcpAuthToken');
        const observation = await recoveryMcpHealthObservation(
          settings.recoveryMcpPort,
          token,
          this.deviceIdentity?.device_id || '',
          this._deviceInstanceId() || '',
          epochId,
          currentRecoveryMcpPid,
          currentRecoveryMcpInstanceId,
          { timeoutMs: 10_000 }
        );
        const health = observation.payload;
        recoveryMcpHealthFailureKind = observation.failure_kind;
        recoveryMcpHealthVerified = Boolean(health
          && Number(health.pid) === currentRecoveryMcpPid
          && String(health.instance_id || '') === currentRecoveryMcpInstanceId);
      } catch {
        recoveryMcpHealthVerified = false;
        recoveryMcpHealthFailureKind = 'observation_exception';
      }
    }
    const recoveryMcpReady = Boolean(plane.mcp?.state === 'healthy'
      && recoveryMcpEpochMatches
      && currentRecoveryMcpPid && isAlivePid(currentRecoveryMcpPid)
      && recoveryMcpIdentityChanged
      && recoveryMcpHealthVerified);
    // Configuration is derived from current settings.  A configured Recovery
    // Tunnel with a missing/inconsistent status is incomplete, never silently
    // treated as "not configured".
    const recoveryTunnelConfigured = Boolean(String(settings.recoveryTunnelId || '').trim());
    const recoveryTunnelEpochMatches = Boolean(String(plane.activation_epoch_id || '') === epochId
      && String(plane.tunnel?.activation_epoch_id || planeState.recoveryTunnelActivationEpochId || '') === epochId);
    let recoveryTunnelHealthVerified = false;
    if (recoveryTunnelConfigured && currentRecoveryTunnelPid && this.paths?.tunnelExecutable) {
      try {
        recoveryTunnelHealthVerified = await probeRecoveryTunnelReady(this.paths, settings.recoveryHealthPort, currentRecoveryTunnelPid);
      } catch { recoveryTunnelHealthVerified = false; }
    }
    const recoveryTunnelReady = recoveryTunnelConfigured
      ? Boolean(plane.tunnel
        && plane.tunnel.configured === true
        && plane.tunnel.state === 'healthy'
        && recoveryTunnelEpochMatches
        && currentRecoveryTunnelPid && isAlivePid(currentRecoveryTunnelPid)
        && recoveryTunnelIdentityChanged
        && recoveryTunnelHealthVerified)
      : Boolean(!plane.tunnel || plane.tunnel.state === 'not_configured' || plane.tunnel.configured !== true);
    const componentsReadyForConnector = Boolean(runtime.mcpRunning === true && tunnelStatusVerified && health?.ready === true
      && processIdentity && epochMatches && workspaceMatches && deviceMatches && revisionMatches
      && tunnelEpochMatches && hostChanged && recoveryHostRevisionMatches
      && recoveryHostEpochMatches
      && uiReady && recoveryMcpReady && recoveryTunnelReady && projectionRebuild.valid);
    let connectorAcknowledgement = { attempted: false, completed: false, error: null };
    if (componentsReadyForConnector
      && [
        'CHANGED_DISCOVERED_NEEDS_ACK',
        'CHANGED_COMPATIBLE_NEEDS_ACK',
        'UNCHANGED_COMPATIBLE_NEEDS_ACK'
      ].includes(connectorContractStatus?.contractState)) {
      connectorAcknowledgement = { attempted: true, completed: false, error: null };
      try {
        if (typeof this.orchestrator?.acknowledgeExactConnectorDiscovery !== 'function') {
          throw epochError('CONNECTOR_ACKNOWLEDGEMENT_UNAVAILABLE', 'Exact current-process connector discovery/bootstrap acknowledgement is unavailable.');
        }
        connectorContractStatus = await this.orchestrator.acknowledgeExactConnectorDiscovery(health, {
          activationEpochId: epochId,
          nowUnixMs: censusNowUnixMs
        });
        connectorAcknowledgement.completed = true;
      } catch (error) {
        connectorAcknowledgement.error = {
          code: text(error?.code) || 'CONNECTOR_ACKNOWLEDGEMENT_FAILED',
          message: text(error?.message) || 'Connector acknowledgement failed.'
        };
      }
    }
    const connectorReady = validateConnectorReadyGate({
      health,
      contractStatus: connectorContractStatus,
      nowUnixMs: censusNowUnixMs
    });
    const pass = Boolean(componentsReadyForConnector && connectorReady.valid);
    return {
      verified: pass,
      pass,
      activation_epoch_id: epochId,
      host_instance_id: this.recoveryInstanceId || null,
      host_pid: Number(process.pid) || null,
      expected_old_host_instance_id: expectedHostId || null,
      expected_old_host_pid: oldHostPid,
      process_instance_id: currentMcpProcessId || null,
      server_instance_id: currentMcpServerId || null,
      supervisor_instance_id: currentSupervisorId || null,
      tunnel_instance_id: currentTunnelId || null,
      tunnel_pid: currentTunnelPid,
      tunnel_health_verified: tunnelStatusVerified,
      recovery_mcp_pid: currentRecoveryMcpPid,
      recovery_mcp_instance_id: currentRecoveryMcpInstanceId || null,
      recovery_tunnel_pid: currentRecoveryTunnelPid,
      recovery_tunnel_instance_id: currentRecoveryTunnelInstanceId || null,
      recovery_mcp_health_verified: recoveryMcpHealthVerified,
      recovery_mcp_health_failure_kind: recoveryMcpHealthFailureKind,
      recovery_tunnel_health_verified: recoveryTunnelHealthVerified,
      running_revision: text(revision.running_revision),
      disk_revision: text(revision.disk_revision),
      ui_instance_id: text(ui.instance_id) || null,
      ui_running_revision: text(uiRevision.running_revision),
      recovery_host_running_revision: text(recoveryHostRevision.running_revision),
      workspace_matches: workspaceMatches,
      device_matches: deviceMatches,
      revision_matches: revisionMatches,
      recovery_host_revision_matches: recoveryHostRevisionMatches,
      recovery_host_epoch_matches: recoveryHostEpochMatches,
      process_identity_verified: processIdentity,
      process_identity_changed: Boolean(identityChanged(currentMcpProcessId, oldMcp.process_instance_id)
        && identityChanged(currentMcpServerId, oldMcp.server_instance_id)
        && identityChanged(currentSupervisorId, oldMcp.supervisor_instance_id)),
      tunnel_identity_changed: tunnelEpochMatches,
      recovery_plane_identity_changed: recoveryMcpIdentityChanged && (!recoveryTunnelConfigured || recoveryTunnelIdentityChanged),
      recovery_plane_epoch_matches: recoveryMcpEpochMatches && (!recoveryTunnelConfigured || recoveryTunnelEpochMatches),
      epoch_matches: epochMatches && tunnelEpochMatches && recoveryHostEpochMatches && recoveryMcpEpochMatches
        && (!recoveryTunnelConfigured || recoveryTunnelEpochMatches),
      connector_acknowledged: connectorReady.valid,
      connector_validation: connectorReady,
      connector_acknowledgement: connectorAcknowledgement,
      ui_verified: uiReady,
      recovery_plane_verified: recoveryMcpReady && recoveryTunnelReady,
      projection_rebuild_verified: projectionRebuild.valid,
      projection_rebuild_reused: projectionObservationReused,
      projection_rebuild_refreshed_after_stale_reuse: projectionObservationRefreshedAfterStaleReuse,
      projection_rebuild_validation: {
        code: projectionRebuild.code,
        reasons: projectionRebuild.reasons,
        projection_classification: projectionRebuild.projection_classification,
        ...(activationObservationFailure ? { observation_failure: activationObservationFailure } : {})
      },
      projection_rebuild_receipt: projectionRebuild.receipt,
      lifecycle_decision: activationObservation?.lifecycle_decision || null,
      reason: pass ? null : 'UPDATE_INCOMPLETE',
      runtime
    };
  }

  /**
   * Revalidate the committed component identities at the last safe point
   * before Coding MCP admission is opened.  `finalize()` first commits the
   * immutable READY proof while admission is CLOSED; this method is then
   * called by RuntimeOrchestrator immediately before it sends `complete_epoch`.
   * A process, Tunnel, UI, or Recovery-Plane replacement between those two
   * observations must therefore fail closed instead of opening MCP under a
   * proof for a different runtime.
   *
   * The recheck deliberately reuses only the exact projection receipt already
   * committed for this epoch.  It still performs fresh live identity/health
   * reads through `finalCensus`; no ledger mutation or synthetic connector
   * receipt is created here.
   */
  async revalidateBeforeAdmission({
    activationEpochId,
    readyCommitDigest = '',
    expiresAtUnixMs = 0
  } = {}) {
    const epochId = text(activationEpochId);
    const digest = text(readyCommitDigest);
    if (!epochId) throw epochError('ACTIVATION_EPOCH_ID_REQUIRED', 'Activation epoch is required for admission revalidation.');
    const record = this.store.current();
    if (!record || text(record.activation_epoch_id) !== epochId) {
      throw epochError('ACTIVATION_EPOCH_NOT_CURRENT', 'Admission revalidation must target the current durable activation epoch.');
    }
    if (record.state !== 'READY_COMMITTED' || record.admission_state !== 'CLOSED') {
      throw epochError('UPDATE_INCOMPLETE', 'Admission revalidation requires the exact closed READY_COMMITTED proof.', {
        activation_epoch_id: epochId,
        state: record.state || null,
        admission_state: record.admission_state || null
      });
    }
    if (!digest || text(record.ready_commit_digest) !== digest) {
      throw epochError('ACTIVATION_EPOCH_READY_COMMIT_CONFLICT', 'Admission revalidation digest does not match the durable READY proof.', {
        activation_epoch_id: epochId,
        expected_ready_commit_digest: text(record.ready_commit_digest) || null,
        supplied_ready_commit_digest: digest || null
      });
    }
    const durableExpiry = Number(record.expires_at_unix_ms || 0);
    const suppliedExpiry = Number(expiresAtUnixMs || 0);
    if (suppliedExpiry > 0 && durableExpiry !== suppliedExpiry) {
      throw epochError('ACTIVATION_EPOCH_EXPIRY_MISMATCH', 'Admission revalidation expiry does not match the durable activation.', {
        activation_epoch_id: epochId,
        durable_expires_at_unix_ms: durableExpiry || null,
        supplied_expires_at_unix_ms: suppliedExpiry
      });
    }

    const committed = record.verification?.final_census;
    if (!committed || typeof committed !== 'object' || Array.isArray(committed)) {
      throw epochError('UPDATE_INCOMPLETE', 'The durable READY proof has no committed final census for admission revalidation.', {
        activation_epoch_id: epochId
      });
    }

    const expectedOldInstanceId = text(record.component_evidence?.recovery_host?.instance_id);
    let fresh;
    try {
      fresh = await this.finalCensus(epochId, {
        expectedOldInstanceId,
        reusePendingProjection: true,
        revalidateCommitted: true
      });
    } catch (error) {
      if (error?.code) throw error;
      throw epochError('UPDATE_INCOMPLETE', 'The final live identity revalidation failed before MCP admission.', {
        activation_epoch_id: epochId,
        cause_code: text(error?.code) || null,
        message: text(error?.message) || null
      });
    }
    if (!fresh || fresh.pass !== true) {
      throw epochError('UPDATE_INCOMPLETE', 'A live component identity changed before MCP admission.', {
        activation_epoch_id: epochId,
        revalidation: fresh || null
      });
    }

    // Compare every identity captured in the committed census.  Optional
    // Recovery-Tunnel fields may legitimately be null when that plane is not
    // configured; a one-sided value is still a mismatch.  Connector receipt
    // timestamps are intentionally not compared byte-for-byte because a
    // second valid discovery on the same process is allowed to refresh it.
    const identityFields = [
      'activation_epoch_id', 'host_instance_id', 'host_pid',
      'process_instance_id', 'server_instance_id', 'supervisor_instance_id',
      'tunnel_instance_id', 'tunnel_pid',
      'recovery_mcp_instance_id', 'recovery_mcp_pid',
      'recovery_tunnel_instance_id', 'recovery_tunnel_pid',
      'ui_instance_id', 'ui_running_revision', 'recovery_host_running_revision',
      'running_revision', 'disk_revision'
    ];
    const normalizeIdentity = (field, value) => {
      if (field.endsWith('_pid')) {
        const number = Number(value);
        return Number.isSafeInteger(number) && number > 0 ? number : null;
      }
      return text(value) || null;
    };
    const mismatches = [];
    for (const field of identityFields) {
      const expected = normalizeIdentity(field, committed[field]);
      const observed = normalizeIdentity(field, fresh[field]);
      if (expected !== observed) mismatches.push({ field, expected, observed });
    }
    if (mismatches.length > 0) {
      throw epochError('UPDATE_INCOMPLETE', 'A committed activation identity no longer matches the live process set.', {
        activation_epoch_id: epochId,
        mismatches
      });
    }

    // Ensure the durable record did not change while the asynchronous census
    // was running.  This closes a second CAS window before the orchestrator
    // sends the external MCP mutation.
    const after = this.store.current();
    if (!after || text(after.activation_epoch_id) !== epochId
      || after.state !== 'READY_COMMITTED'
      || after.admission_state !== 'CLOSED'
      || text(after.ready_commit_digest) !== digest) {
      throw epochError('ACTIVATION_EPOCH_CONFLICT', 'The durable READY proof changed during admission revalidation.', {
        activation_epoch_id: epochId
      });
    }
    return {
      valid: true,
      activation_epoch_id: epochId,
      ready_commit_digest: digest,
      census: fresh
    };
  }

  async finalize(activationEpochId, census = null) {
    const epochId = text(activationEpochId);
    if (!epochId) throw epochError('ACTIVATION_EPOCH_ID_REQUIRED', 'Activation epoch is required.');
    let record = null;
    let committed = null;
    let opened = false;
    try {
      // Never trust a caller-supplied boolean/projection as final proof. A
      // fresh live census is mandatory at this boundary; the optional argument
      // is retained only for backwards-compatible call signatures. When the
      // durable epoch still contains a strict admission-closed pending census,
      // finalCensus may reuse only its exact immutable projection receipt while
      // revalidating every live process/component/connector identity. This
      // avoids a second multi-minute ledger rebuild between the watchdog census
      // and the READY commit without weakening the transaction boundary. Keep
      // this read inside the transaction catch so a transport/store/census
      // exception is durably terminalized as FAILED rather than leaving an
      // active epoch that merely appears stuck.
      const finalProof = await this.finalCensus(epochId, { reusePendingProjection: true });
      if (!finalProof.pass) throw epochError('UPDATE_INCOMPLETE', 'Full clean activation final census is incomplete.', finalProof);
      record = this.store.current();
      if (!record || record.activation_epoch_id !== epochId) {
        throw epochError('ACTIVATION_EPOCH_NOT_CURRENT', 'Final activation proof no longer belongs to the current durable epoch.');
      }
      // finalCensus already captured the checkpoint/lifecycle decision before
      // the matching MCP health receipt.  Re-running preflight here would
      // create a different receipt observation and break the atomic binding.
      const lifecycle = finalProof.lifecycle_decision || null;
      if (record.source_checkpoint && !lifecycleDecisionIsClean(lifecycle)) {
        throw epochError('LIFECYCLE_VERIFICATION_FAILED', 'Final activation census omitted its checkpoint-bound lifecycle proof.');
      }
      const postflightByComponent = this._componentPostflights(record, finalProof, lifecycle);
      const censusWithProof = {
        ...finalProof,
        component_postflights: postflightByComponent,
        lifecycle_verified: lifecycle ? lifecycleDecisionIsClean(lifecycle) : null
      };
      // Commit the exact census durably while admission is still CLOSED.  If
      // this write fails, completeActivationEpoch is never called.
      committed = this.store.commitReady(epochId, {
        verified: true,
        activation_epoch_id: epochId,
        final_census: censusWithProof
      });
      const readyCommitDigest = text(committed.ready_commit_digest);
      const expiresAtUnixMs = Number(committed.expires_at_unix_ms || 0);
      if (!HEX64.test(readyCommitDigest) || !Number.isSafeInteger(expiresAtUnixMs) || expiresAtUnixMs <= 0) {
        throw epochError('UPDATE_INCOMPLETE', 'Durable activation commit is missing its bound digest or expiry.');
      }
      if (typeof this.orchestrator?.completeActivationEpoch !== 'function') {
        throw epochError('MCP_ACTIVATION_CONTROL_UNAVAILABLE', 'Coding MCP activation admission control is unavailable.');
      }
      let admission = null;
      try {
        admission = await this.orchestrator.completeActivationEpoch(epochId, readyCommitDigest);
        opened = admission?.admission_open === true;
        if (!exactActivationAdmission(admission, epochId, readyCommitDigest, expiresAtUnixMs, true)) {
          throw epochError('UPDATE_INCOMPLETE', 'Coding MCP did not acknowledge the exact durable activation commit.', {
            activation_epoch_id: epochId,
            ready_commit_digest: readyCommitDigest,
            observed: admission || null
          });
        }
        opened = true;
      } catch (error) {
        if (!isActivationResponseLoss(error)) throw error;
        // A response can be lost after the MCP opened admission.  Never retry
        // the mutation blindly: reconcile the exact process health once.
        opened = true;
        let health = null;
        try { health = await this.orchestrator?.currentMcpHealth?.(); }
        catch { health = null; }
        if (!exactActivationAdmission(health, epochId, readyCommitDigest, expiresAtUnixMs, true)) {
          throw epochError('MCP_ACTIVATION_COMMIT_UNCERTAIN', 'Coding MCP activation response was lost and exact admission could not be reconciled.', {
            activation_epoch_id: epochId,
            ready_commit_digest: readyCommitDigest,
            cause_code: String(error?.code || '') || null,
            health: health || null
          });
        }
        admission = health;
      }
      // No fallible component census is permitted after effective admission
      // opens.  The final local transition consumes only the exact digest that
      // was already acknowledged by the MCP process.
      const ready = this.store.ready(epochId, readyCommitDigest);
      const result = this._actionResult(ready, {
        state: 'READY',
        admission_open: true,
        fully_ready: true,
        census: censusWithProof,
        postflight_by_component: postflightByComponent,
        ready_commit_digest: readyCommitDigest,
        mcp_admission: admission
      });
      // Runtime readiness is already terminal and authoritative.  A secondary
      // action-store/reporting failure must not close a successfully committed
      // runtime or turn READY into a contradictory FAILED projection.
      try {
        const linked = this._finishLinkedAction(ready, 'completed', result);
        return linked || result;
      } catch (error) {
        this.log?.error?.(error.message, {
          stage: 'full-clean-activation-reporting',
          activationEpochId: epochId,
          code: error?.code || ''
        });
        return result;
      }
    } catch (error) {
      if (opened) {
        let closed = false;
        if (typeof this.orchestrator?.closeActivationEpoch === 'function') {
          try {
            const digest = text(committed?.ready_commit_digest);
            const closeResult = await this.orchestrator.closeActivationEpoch(epochId, digest);
            closed = Boolean(closeResult?.ok === true
              && closeResult?.admission_open === false
              && String(closeResult?.activation_epoch_id || '') === epochId
              && (!digest || String(closeResult?.ready_commit_digest || '') === digest));
          } catch (closeError) {
            if (isActivationResponseLoss(closeError)) {
              try {
                const digest = text(committed?.ready_commit_digest);
                const health = await this.orchestrator?.currentMcpHealth?.();
                closed = exactActivationAdmission(
                  health,
                  epochId,
                  digest,
                  Number(committed?.expires_at_unix_ms || 0),
                  false
                );
              } catch { closed = false; }
            }
          }
        }
        // If the exact MCP close could not be confirmed, stop the owned
        // primary runtime as a second fail-closed boundary.  A FAILED durable
        // epoch must never leave an admitted MCP process behind.
        if (!closed && typeof this.orchestrator?.stop === 'function') {
          await this.orchestrator.stop({ manual: false, fullClean: true, activationEpochId: epochId }).catch(() => false);
        }
      }
      const failed = this._failEpoch(epochId, error);
      if (failed) this._finishLinkedAction(failed, 'failed', this._actionResult(failed, { state: 'FAILED', admission_open: false, fully_ready: false }), error);
      throw error;
    }
  }
}

module.exports = {
  FullCleanActivation,
  COMPONENTS,
  DEFAULT_TTL_MS,
  operationId,
  canonicalLedgerCensus,
  canonicalSnapshot,
  summarizeCensus,
  canonicalProjectionRebuildSha256,
  validateProjectionRebuildGate,
  validateConnectorReadyGate,
  reusablePendingProjectionObservation
};
