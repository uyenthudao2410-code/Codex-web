const crypto = require('node:crypto');
const fs = require('node:fs');
const { RuntimeOrchestrator } = require('./runtimeOrchestrator');
const { RecoveryPlaneService } = require('./recoveryPlaneService');
const { HealthService } = require('./healthService');
const { HubProxyGateway } = require('./hubProxyGateway');
const { RecoveryIpcServer } = require('./recoveryIpc');
const { ensureParent, readJson } = require('./jsonStore');
const { loadOrCreateDeviceIdentity, normalizeDeviceIdentity } = require('./deviceIdentity');
const { ComponentRevisionTracker } = require('./componentRevision');
const { RecoveryActivation } = require('./recoveryActivation');
const { AcceptedCodeActivationController } = require('./recoveryActionStore');
const { computeActivationClosure, activationSourceCheckpoint } = require('./activationClosure');
const { FullCleanActivation, canonicalLedgerCensus } = require('./fullCleanActivation');
const { ActivationEpochStore, ACTIVE_STATES } = require('./activationEpoch');
const { writeBootstrapResult, readBootstrapResult, removeBootstrapEnvelope } = require('./recoveryBootstrap');
const {
  normalizeProcessStartToken,
  observeProcessIdentity,
  observeProcessIdentityAsync,
  processIdentityFrom,
  sameProcessIdentity,
  terminateExactProcessTree
} = require('./processIdentity');

const SUPERVISION_INTERVAL_MS = 5000;
// UI clients poll every five seconds. Their read path must consume the latest
// completed supervisor projection instead of launching another MCP/Tunnel/Git
// probe in parallel with the supervisor. Keep an explicit freshness window so
// a stalled supervisor becomes UNKNOWN/WARN telemetry rather than stale green.
const SUPERVISION_STATUS_STALE_MS = 30_000;
const REPLACEMENT_WAIT_MS = 15_000;
const HANDOFF_SUPERVISION_DRAIN_MS = 10_000;
const UI_RECOVERY_REGISTRATION_TIMEOUT_MS = 15_000;
const UI_RECOVERY_COOLDOWN_MS = 20_000;
const UI_RECOVERY_WINDOW_MS = 10 * 60_000;
const UI_RECOVERY_ATTEMPT_LIMIT = 4;
const UI_RECOVERY_CIRCUIT_BREAK_MS = 5 * 60_000;
const TERMINAL_BOOTSTRAP_STATES = new Set(['completed', 'failed', 'expired', 'reconciled_terminal_receipt']);
const READY_CONNECTOR_SHA_PATTERN = /^[a-f0-9]{64}$/;
// A durable connector receipt may be old (the attestation capability is
// lifecycle-bound rather than a per-request signature), but a timestamp from
// the future is never credible evidence. Keep this aligned with the bounded
// skew accepted by the runtime connector gate.
const READY_CONNECTOR_FUTURE_SKEW_MS = 5_000;

function wait(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

function isProcessAlive(pid) {
  if (!Number.isInteger(Number(pid)) || Number(pid) <= 0) return false;
  try { process.kill(Number(pid), 0); return true; } catch { return false; }
}

function connectorTimestampValid(value, nowUnixMs = Date.now()) {
  const timestamp = String(value || '').trim();
  const timestampUnixMs = Date.parse(timestamp);
  return Boolean(timestamp
    && Number.isFinite(timestampUnixMs)
    && (!Number.isFinite(Number(nowUnixMs))
      || timestampUnixMs <= Number(nowUnixMs) + READY_CONNECTOR_FUTURE_SKEW_MS));
}

function activationCensus(record) {
  const verification = record?.verification;
  if (!verification || typeof verification !== 'object' || Array.isArray(verification)) return null;
  if (verification.final_census && typeof verification.final_census === 'object') {
    return verification.final_census;
  }
  return String(verification.activation_epoch_id || '') === String(record?.activation_epoch_id || '')
    ? verification : null;
}

function activationPendingCensus(record) {
  if (String(record?.state || '') !== 'VERIFYING') return false;
  const census = activationCensus(record);
  return census
    && census.process_identity_verified === true
    && census.process_identity_changed === true
    && census.tunnel_identity_changed === true
    && census.recovery_host_revision_matches === true
    && census.recovery_host_epoch_matches === true
    && census.ui_verified === true
    && census.recovery_plane_identity_changed === true
    && census.recovery_plane_epoch_matches === true
    && census.recovery_plane_verified === true
    && census.projection_rebuild_verified === true
    && census.workspace_matches === true
    && census.device_matches === true
    && census.revision_matches === true
    && census.epoch_matches === true
    && census.connector_validation
    && census.connector_validation.valid === false
    ? census : null;
}

function activationAwaitsConnector(record) {
  const census = activationPendingCensus(record);
  return Boolean(census && census.tunnel_health_verified === true);
}

function activationAwaitsTunnelOrConnector(record) {
  return Boolean(activationPendingCensus(record));
}

function exactConnectorEvidenceObserved(health, census) {
  const discovery = health?.connector_tool_discovery;
  const bootstrap = health?.connector_activation_bootstrap;
  const currentSha256 = String(health?.tool_contract?.sha256 || '').trim();
  const processInstanceId = String(health?.process_instance_id || '').trim();
  const serverInstanceId = String(health?.instance_id || health?.server_instance_id || '').trim();
  const activationEpochId = String(health?.activation_epoch_id || '').trim();
  const discoveryObservedAt = String(discovery?.observed_at || '').trim();
  const exactDiscovery = Boolean(discovery
    && discovery.current_contract_observed === true
    && String(discovery.identity_source || '').trim() === 'attested_transport'
    && discovery.attestation_verified === true
    && currentSha256
    && String(discovery.contract_sha256 || '').trim() === currentSha256
    && processInstanceId === String(census?.process_instance_id || '').trim()
    && serverInstanceId === String(census?.server_instance_id || '').trim()
    && String(discovery.process_instance_id || '').trim() === processInstanceId
    && String(discovery.server_instance_id || '').trim() === serverInstanceId
    && activationEpochId === String(census?.activation_epoch_id || '').trim()
    && String(discovery.activation_epoch_id || '').trim() === activationEpochId
    && connectorTimestampValid(discoveryObservedAt));
  const bootstrapObservedAt = String(bootstrap?.observed_at || '').trim();
  const exactCompatibilityBootstrap = Boolean(bootstrap
    && bootstrap.current_contract_contact === true
    && String(bootstrap.identity_source || '').trim() === 'attested_transport'
    && bootstrap.attestation_verified === true
    && String(bootstrap.client_type || '').trim() === 'chatweb'
    && String(bootstrap.client_id || '').trim()
    && String(bootstrap.method || '').trim() === 'tools/call'
    && String(bootstrap.tool_name || '').trim() === 'workspace_context'
    && bootstrap.workspace_accessed === false
    && currentSha256
    && String(bootstrap.contract_sha256 || '').trim() === currentSha256
    && processInstanceId === String(census?.process_instance_id || '').trim()
    && serverInstanceId === String(census?.server_instance_id || '').trim()
    && String(bootstrap.process_instance_id || '').trim() === processInstanceId
    && String(bootstrap.server_instance_id || '').trim() === serverInstanceId
    && activationEpochId === String(census?.activation_epoch_id || '').trim()
    && String(bootstrap.activation_epoch_id || '').trim() === activationEpochId
    && connectorTimestampValid(bootstrapObservedAt));
  return exactDiscovery || exactCompatibilityBootstrap;
}

/**
 * Validate the connector portion of a persisted terminal READY census before
 * an ordinary Recovery Host restart adopts that epoch.  ActivationEpochStore
 * intentionally validates only the generic two-phase READY proof so it can be
 * shared by components; this boundary adds the product-specific invariant
 * that READY is admissible only after one of the exact attested current-process
 * receipt modes accepted by the full-clean connector validator.
 *
 * This is deliberately read-only.  A malformed/legacy READY record is not
 * rewritten or silently downgraded here because terminal history is immutable;
 * the caller must keep startup fail-closed and require an explicit new
 * full-clean activation to establish a replacement proof.
 */
function validatePersistedReadyConnectorProof(record, { nowUnixMs = Date.now() } = {}) {
  const reasons = [];
  const add = (reason) => { if (!reasons.includes(reason)) reasons.push(reason); };
  const epochId = String(record?.activation_epoch_id || '').trim();
  const verification = record?.verification;
  const census = verification?.final_census;
  const connector = census?.connector_validation;

  if (!record || record.state !== 'READY' || record.admission_state !== 'OPEN') {
    add('READY_ADMISSION_STATE_INVALID');
  }
  if (!epochId) add('ACTIVATION_EPOCH_ID_MISSING');
  if (!verification || typeof verification !== 'object' || Array.isArray(verification)
    || verification.verified !== true) {
    add('READY_VERIFICATION_INVALID');
  } else if (String(verification.activation_epoch_id || '').trim() !== epochId) {
    add('VERIFICATION_ACTIVATION_EPOCH_ID_MISMATCH');
  }
  if (!census || typeof census !== 'object' || Array.isArray(census)) {
    add('FINAL_CENSUS_MISSING');
  } else {
    if (census.pass !== true) add('FINAL_CENSUS_NOT_PASSING');
    if (String(census.activation_epoch_id || '').trim() !== epochId) {
      add('FINAL_CENSUS_ACTIVATION_EPOCH_ID_MISMATCH');
    }
  }
  if (!connector || typeof connector !== 'object' || Array.isArray(connector)) {
    add('CONNECTOR_VALIDATION_MISSING');
  } else {
    if (connector.valid !== true) add('CONNECTOR_VALIDATION_NOT_VALID');
    if (connector.code !== 'READY') add('CONNECTOR_VALIDATION_CODE_INVALID');
    if (!Array.isArray(connector.reasons) || connector.reasons.length !== 0) {
      add('CONNECTOR_VALIDATION_REASONS_NON_EMPTY');
    }
    const freshnessMode = String(connector.freshness_mode || '').trim();
    if (!['current_process_discovery', 'compatible_activation_bootstrap'].includes(freshnessMode)) {
      add('CONNECTOR_FRESHNESS_MODE_INVALID');
    }

    const currentSha = String(connector.current_sha256 || '').trim();
    const acknowledgedSha = String(connector.acknowledged_sha256 || '').trim();
    if (!READY_CONNECTOR_SHA_PATTERN.test(currentSha)) add('CURRENT_CONTRACT_SHA256_INVALID');
    if (!READY_CONNECTOR_SHA_PATTERN.test(acknowledgedSha)) add('ACKNOWLEDGED_CONTRACT_SHA256_INVALID');
    if (currentSha && acknowledgedSha && currentSha !== acknowledgedSha) {
      add('ACKNOWLEDGED_CONTRACT_SHA256_MISMATCH');
    }

    const processInstanceId = String(census?.process_instance_id || '').trim();
    const serverInstanceId = String(census?.server_instance_id || '').trim();
    if (!processInstanceId) add('PROCESS_INSTANCE_ID_MISSING');
    if (!serverInstanceId) add('SERVER_INSTANCE_ID_MISSING');
    if (String(connector.activation_epoch_id || '').trim() !== epochId) {
      add('CONNECTOR_ACTIVATION_EPOCH_ID_MISMATCH');
    }
    if (String(connector.process_instance_id || '').trim() !== processInstanceId) {
      add('CONNECTOR_PROCESS_INSTANCE_ID_MISMATCH');
    }
    if (String(connector.server_instance_id || '').trim() !== serverInstanceId) {
      add('CONNECTOR_SERVER_INSTANCE_ID_MISMATCH');
    }

    const rediscoveredAt = String(connector.rediscovered_at || '').trim();
    const compatibilityAcknowledgedAt = String(connector.compatibility_acknowledged_at || '').trim();
    if (freshnessMode === 'current_process_discovery') {
      if (!rediscoveredAt || !Number.isFinite(Date.parse(rediscoveredAt))) {
        add('REDISCOVERY_TIMESTAMP_INVALID');
      } else if (!connectorTimestampValid(rediscoveredAt, nowUnixMs)) {
        add('REDISCOVERY_TIMESTAMP_FROM_FUTURE');
      }
      if (compatibilityAcknowledgedAt) add('COMPATIBILITY_RECEIPT_PRESENT');
    } else if (freshnessMode === 'compatible_activation_bootstrap') {
      if (!compatibilityAcknowledgedAt || !Number.isFinite(Date.parse(compatibilityAcknowledgedAt))) {
        add('COMPATIBILITY_TIMESTAMP_INVALID');
      } else if (!connectorTimestampValid(compatibilityAcknowledgedAt, nowUnixMs)) {
        add('COMPATIBILITY_TIMESTAMP_FROM_FUTURE');
      }
      if (rediscoveredAt) add('COMPATIBILITY_MODE_REDISCOVERY_PRESENT');
    }
    if (census.connector_acknowledged !== true) add('CONNECTOR_ACKNOWLEDGEMENT_INVALID');

    // Keep the contract hash bound to any duplicated runtime projection when
    // that optional projection is present. Missing legacy duplicates are not
    // treated as proof, but are tolerated because connector_validation is the
    // canonical persisted receipt field.
    const runtimeContractSha = String(
      census?.runtime?.toolContract?.sha256
      || census?.runtime?.tool_contract?.sha256
      || ''
    ).trim();
    if (runtimeContractSha && runtimeContractSha !== currentSha) {
      add('RUNTIME_CONTRACT_SHA256_MISMATCH');
    }
    const runtimeEpoch = String(
      census?.runtime?.activationEpoch?.activation_epoch_id
      || census?.runtime?.activation_epoch_id
      || ''
    ).trim();
    if (runtimeEpoch && runtimeEpoch !== epochId) add('RUNTIME_ACTIVATION_EPOCH_ID_MISMATCH');
  }

  return {
    valid: reasons.length === 0,
    code: reasons.length === 0 ? 'READY' : 'UPDATE_INCOMPLETE',
    reasons,
    activation_epoch_id: epochId || null,
    process_instance_id: String(census?.process_instance_id || '').trim() || null,
    server_instance_id: String(census?.server_instance_id || '').trim() || null,
    current_sha256: String(connector?.current_sha256 || '').trim() || null,
    freshness_mode: String(connector?.freshness_mode || '').trim() || null,
    rediscovered_at: String(connector?.rediscovered_at || '').trim() || null,
    compatibility_acknowledged_at: String(connector?.compatibility_acknowledged_at || '').trim() || null
  };
}

function activationClosureProjection({
  autoActivation = null,
  recoveryHostRevision = {},
  electronUiRevision = {},
  codingMcpRevision = {},
  runtime = {}
} = {}) {
  const status = runtime?.status && typeof runtime.status === 'object' ? runtime.status : runtime;
  const connectorContractState = String(
    status?.connectorContractState
    || status?.connector_contract_state
    || runtime?.status?.connectorContractState
    || runtime?.activationClosure?.connector_contract_state
    || 'UNAVAILABLE'
  );
  const runtimeFullyReady = Object.prototype.hasOwnProperty.call(status || {}, 'fullyReady')
    ? status.fullyReady === true
    : status?.fully_ready === true;
  const runtimeRunning = Object.prototype.hasOwnProperty.call(status || {}, 'runtimeRunning')
    ? status.runtimeRunning === true
    : status?.mcpRunning === true;
  const tunnelRunning = status?.tunnelRunning === true;
  const freshCodingMcpRevision = codingMcpRevision && typeof codingMcpRevision === 'object'
    && Object.keys(codingMcpRevision).length
    ? codingMcpRevision
    : status?.codeRevision?.codingMcp || {};
  return computeActivationClosure({
    acceptedCode: autoActivation?.closure_input || null,
    componentRevisions: {
      recovery_host: recoveryHostRevision || {},
      electron_ui: electronUiRevision || {},
      coding_mcp: freshCodingMcpRevision
    },
    connectorContractState,
    connectorRefreshRequired: status?.connectorRefreshRequired,
    connectorAcknowledgementPending: status?.connectorAcknowledgementPending,
    connectorRediscoveredAt: status?.connectorRediscoveredAt,
    connectorCompatibilityAcknowledgedAt: status?.connectorCompatibilityAcknowledgedAt,
    connectorCurrentSha256: status?.toolContract?.sha256,
    connectorAcknowledgedSha256: status?.connectorContractAcknowledgedSha256,
    runtimeFullyReady,
    runtimeRunning,
    tunnelRunning
  });
}

function readLock(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return null; }
}

function acquireRecoveryHostLock(paths, instanceId, pid = process.pid) {
  const file = paths.recoveryHostLockFile();
  ensureParent(file);
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const descriptor = { version: 1, pid, instance_id: instanceId, created_at: new Date().toISOString() };
      const handle = fs.openSync(file, 'wx', 0o600);
      try { fs.writeFileSync(handle, JSON.stringify(descriptor), 'utf8'); }
      finally { fs.closeSync(handle); }
      return descriptor;
    } catch (error) {
      if (error?.code !== 'EEXIST') throw error;
      const current = readLock(file);
      if (current && isProcessAlive(current.pid)) {
        throw Object.assign(new Error('A Recovery Host already owns the runtime.'), {
          code: 'RECOVERY_HOST_ALREADY_RUNNING',
          ownerPid: Number(current.pid),
          ownerInstanceId: String(current.instance_id || '')
        });
      }
      fs.rmSync(file, { force: true });
    }
  }
  throw Object.assign(new Error('Recovery Host ownership could not be acquired.'), { code: 'RECOVERY_HOST_LOCK_FAILED' });
}

function releaseRecoveryHostLock(paths, instanceId) {
  const file = paths.recoveryHostLockFile();
  const current = readLock(file);
  if (current?.instance_id !== instanceId) return false;
  fs.rmSync(file, { force: true });
  return true;
}

async function waitForReplacementLockRelease(paths, expectedInstanceId, timeoutMs = REPLACEMENT_WAIT_MS) {
  const deadline = Date.now() + Math.max(1000, Number(timeoutMs) || REPLACEMENT_WAIT_MS);
  while (Date.now() < deadline) {
    const current = readLock(paths.recoveryHostLockFile());
    if (!current) return true;
    if (String(current.instance_id || '') !== String(expectedInstanceId || '')) {
      throw Object.assign(new Error('Recovery Host replacement target changed.'), { code: 'RECOVERY_REPLACEMENT_TARGET_CHANGED' });
    }
    await wait(50);
  }
  throw Object.assign(new Error('Timed out waiting for the previous Recovery Host to release ownership.'), { code: 'RECOVERY_REPLACEMENT_TIMEOUT' });
}

class RecoveryHost {
  constructor({
    paths, settings, secrets, environment, log, orchestrator, healthService, gateway, ipcServerFactory,
    revisionTracker = null, actionStore = null, spawnRecoveryReplacement = null, spawnElectronUi = null,
    exitProcess = null, replacement = null, autoActivationController = null, recoveryPlaneService = null,
    deviceIdentity = null, bootstrap = null, processAlive = isProcessAlive,
    processIdentityObserver = observeProcessIdentity,
    asyncProcessIdentityObserver = null,
    exactProcessTerminator = terminateExactProcessTree,
    canonicalLedgerCensusFn = canonicalLedgerCensus
  }) {
    this.paths = paths;
    this.settings = settings;
    this.secrets = secrets;
    this.environment = environment;
    this.log = log;
    this.instanceId = crypto.randomBytes(16).toString('hex');
    this.deviceInstanceId = this.instanceId;
    this.deviceIdentity = deviceIdentity
      ? normalizeDeviceIdentity(deviceIdentity)
      : loadOrCreateDeviceIdentity(paths);
    this.startedAt = new Date().toISOString();
    this.lastProgress = null;
    this.lastPublishedStatus = null;
    this.revisions = revisionTracker || new ComponentRevisionTracker({ paths });
    this.recoveryHostRunningRevision = this.revisions.captureRunning('recovery_host');
    this.orchestrator = orchestrator || new RuntimeOrchestrator({
      paths,
      settings,
      secrets,
      environment,
      log,
      deviceIdentity: this.deviceIdentity,
      deviceInstanceId: this.deviceInstanceId,
      activationEpochId: replacement?.activationEpochId || '',
      revisionTracker: this.revisions,
      emitProgress: (payload) => { this.lastProgress = payload; },
      emitStatus: (payload) => { this.lastPublishedStatus = payload; }
    });
    this.healthService = healthService || new HealthService({ settings, secrets, environment, orchestrator: this.orchestrator });
    this.gateway = gateway || new HubProxyGateway({ paths, settings, secrets, log, owner: 'recovery-host', deviceIdentity: this.deviceIdentity, deviceInstanceId: this.deviceInstanceId });
    this.ipcServerFactory = ipcServerFactory || ((options) => new RecoveryIpcServer(options));
    this.ipcServer = null;
    this.supervisionTimer = null;
    this.supervisionInFlight = null;
    this.lastSupervisionStatus = null;
    this.lastSupervisionObservedAtUnixMs = 0;
    // The supervisor owns the potentially expensive runtime observation path.
    // Lightweight UI heartbeats consume this completed projection instead of
    // re-reading durable activation state or probing process identities.
    this.lastSupervisionProjection = null;
    this.lastSupervisionProjectionSource = 'recovery_host_supervision_cache';
    this.lastRecoveryPlaneStatus = null;
    this.ownsLock = false;
    this.running = false;
    // A terminal READY record is not sufficient to resume ownership: the
    // persisted connector receipt must prove an attested, current-process
    // discovery.  Keep a read-only diagnostic when that proof is absent so
    // the authenticated control plane can remain available for an explicit
    // full-clean refresh without admitting the stale runtime.
    this.readyAdoptionBlocked = null;
    this.replacement = replacement;
    // A bootstrap envelope is present only when a current-checkout process was
    // launched to replace a stale Recovery Host.  It is consumed before normal
    // watchdog/startup recovery so the stale process can never execute a
    // component-scoped activation request.
    this.bootstrap = bootstrap;
    this.bootstrapActivation = bootstrap ? { state: 'pending', operation_id: bootstrap.operation_id || null } : null;
    this.bootstrapEnvelopeConsumed = false;
    this.processAlive = typeof processAlive === 'function' ? processAlive : isProcessAlive;
    this.processIdentityObserver = typeof processIdentityObserver === 'function'
      ? processIdentityObserver
      : observeProcessIdentity;
    this.asyncProcessIdentityObserver = typeof asyncProcessIdentityObserver === 'function'
      ? asyncProcessIdentityObserver
      : this.processIdentityObserver === observeProcessIdentity
        ? observeProcessIdentityAsync
        : this.processIdentityObserver;
    this.exactProcessTerminator = typeof exactProcessTerminator === 'function'
      ? exactProcessTerminator
      : terminateExactProcessTree;
    this.canonicalLedgerCensus = typeof canonicalLedgerCensusFn === 'function'
      ? canonicalLedgerCensusFn
      : null;
    this.processIdentity = null;
    this.exitProcess = exitProcess || (() => {});
    this.handoffStarted = false;
    this.replacementWaitMs = REPLACEMENT_WAIT_MS;
    this.handoffSupervisionDrainMs = HANDOFF_SUPERVISION_DRAIN_MS;
    this.spawnElectronUi = spawnElectronUi;
    this.uiRecoveryAttempts = [];
    this.uiRecoveryPendingUntil = 0;
    this.uiRecoveryNextAttemptAt = 0;
    this.uiRecoveryCircuitUntil = 0;
    this.uiRecoveryLastLaunchPid = 0;
    this.uiRecoveryLastErrorCode = '';
    this.uiRecoveryLastState = 'untracked';
    this.uiRecoveryLaunchInFlight = null;
    this.uiRecoveryInitialGraceUntil = 0;
    this.activation = new RecoveryActivation({
      paths,
      revisions: this.revisions,
      orchestrator: this.orchestrator,
      log,
      recoveryInstanceId: this.instanceId,
      recoveryRunningRevision: this.recoveryHostRunningRevision,
      actionStore,
      spawnRecoveryReplacement,
      spawnElectronUi,
      processIdentityObserver: this.processIdentityObserver,
      asyncProcessIdentityObserver: this.asyncProcessIdentityObserver,
      beginRecoveryHandoff: (operationId) => this.scheduleRecoveryHandoff(operationId)
    });
    if (this.activation.uiRecoveryPreferenceStatus().suppressed) {
      this.uiRecoveryLastState = 'suppressed';
    } else {
      this.uiRecoveryInitialGraceUntil = Date.now() + UI_RECOVERY_REGISTRATION_TIMEOUT_MS;
      this.uiRecoveryLastState = 'awaiting_initial_registration';
    }
    this.autoActivation = autoActivationController || new AcceptedCodeActivationController({ paths, settings, revisions: this.revisions, activation: this.activation, log });
    this.recoveryPlane = recoveryPlaneService || new RecoveryPlaneService({
      paths,
      log,
      deviceIdentity: this.deviceIdentity,
      deviceInstanceId: this.deviceInstanceId,
      activationEpochId: replacement?.activationEpochId || ''
    });
    // Bind the interprocess epoch-store lock descriptor to this Recovery Host
    // lifecycle identity so lock evidence and the durable epoch owner cannot
    // silently refer to unrelated random identities in the same process.
    this.activationEpochStore = new ActivationEpochStore({ paths, ownerInstanceId: this.instanceId });
    this.fullCleanActivation = new FullCleanActivation({
      paths,
      settings,
      secrets,
      orchestrator: this.orchestrator,
      recoveryPlane: this.recoveryPlane,
      revisions: this.revisions,
      deviceIdentity: this.deviceIdentity,
      recoveryInstanceId: this.instanceId,
      actionStore: this.activation.actions,
      log,
      spawnRecoveryReplacement,
      spawnElectronUi,
      getUiRegistration: () => this.activation.uiRegistration,
      getUiPresence: () => this.activation.uiPresence(),
      getUiRevision: (options) => this.activation.uiRevisionStatus(options),
      getRecoveryPlaneStatus: () => this.lastRecoveryPlaneStatus,
      canonicalLedgerCensus: (options) => this.canonicalLedgerCensus({ paths: this.paths, ...options }),
      recoveryHostRunningRevision: this.recoveryHostRunningRevision,
      setActivationEpoch: (epochId) => {
        if (this.ipcServer && typeof this.ipcServer.updateActivationEpoch === 'function') {
          this.ipcServer.updateActivationEpoch(epochId);
        } else if (this.ipcServer) {
          this.ipcServer.activationEpochId = String(epochId || '').trim() || null;
        }
      },
      terminateUi: async (presence) => {
        const pid = Number(presence?.pid || 0);
        const instanceId = String(presence?.instance_id || '').trim();
        const token = normalizeProcessStartToken(presence?.process_start_token);
        if (!pid || pid === process.pid || !instanceId || !token) {
          throw Object.assign(new Error('Refused to terminate an unverified Electron UI owner.'), {
            code: 'UI_RECOVERY_INSTANCE_MISMATCH'
          });
        }
        const currentPresence = this.activation.uiPresence();
        if (!currentPresence.alive
          || Number(currentPresence.pid) !== pid
          || String(currentPresence.instance_id || '') !== instanceId
          || normalizeProcessStartToken(currentPresence.process_start_token) !== token) {
          throw Object.assign(new Error('Electron UI owner changed before exact termination.'), {
            code: 'UI_RECOVERY_INSTANCE_MISMATCH',
            details: { pid, instance_id: instanceId }
          });
        }
        let identity;
        try { identity = processIdentityFrom({ pid, process_start_token: token }); }
        catch (error) {
          throw Object.assign(new Error('Electron UI process identity is unavailable for termination.'), {
            code: 'UI_PROCESS_IDENTITY_UNVERIFIED',
            cause: error
          });
        }
        try {
          await this.exactProcessTerminator(identity, {
            observeProcessIdentity: this.processIdentityObserver,
            timeoutMs: 5000
          });
        } catch (error) {
          throw Object.assign(new Error('Electron UI exact process termination failed.'), {
            code: error?.code === 'PROCESS_IDENTITY_UNVERIFIED'
              ? 'UI_PROCESS_IDENTITY_UNVERIFIED'
              : error?.code === 'PROCESS_IDENTITY_CHANGED'
                ? 'UI_RECOVERY_INSTANCE_MISMATCH'
                : 'UI_TERMINATION_FAILED',
            cause: error,
            details: { pid, instance_id: instanceId }
          });
        }
        return true;
      },
      scheduleHandoff: (epochId, details) => this.scheduleFullCleanHandoff(epochId, details),
      epochStore: this.activationEpochStore
    });
    this.activation.fullCleanActivation = this.fullCleanActivation;
    this.orchestrator.setFullCleanActivation?.(this.fullCleanActivation);
    // All non-soft restart callers (including deferred task_control tickets)
    // must obtain their source authority from this Recovery Host's current
    // accepted-code closure.  Never infer a checkpoint from a ticket or a
    // stale component projection.
    this.orchestrator.setFullCleanSourceCheckpointResolver?.(
      () => this.resolveFullCleanSourceCheckpoint()
    );
    if (replacement?.activationEpochId) this.orchestrator.setActivationEpoch?.(replacement.activationEpochId);
  }

  resolveFullCleanSourceCheckpoint() {
    return activationSourceCheckpoint(this.hostStatus());
  }

  _resolveRequestedFullCleanCheckpoint(requested) {
    const authoritative = this.resolveFullCleanSourceCheckpoint();
    if (requested === undefined || requested === null) return authoritative;
    const fields = ['checkpoint_id', 'run_id', 'wave_id', 'proof_fingerprint', 'git_head'];
    const matches = requested && typeof requested === 'object' && !Array.isArray(requested)
      && Object.keys(requested).length === fields.length
      && fields.every((field) => requested[field] === authoritative[field]);
    if (!matches) {
      throw Object.assign(new Error('The requested full-clean source checkpoint does not match the current Recovery Host accepted-code closure.'), {
        code: 'ACTIVATION_SOURCE_CHECKPOINT_MISMATCH',
        details: { source_checkpoint: authoritative }
      });
    }
    return authoritative;
  }

  resetUiRecoveryTracking(state = 'healthy') {
    this.uiRecoveryAttempts = [];
    this.uiRecoveryPendingUntil = 0;
    this.uiRecoveryNextAttemptAt = 0;
    this.uiRecoveryCircuitUntil = 0;
    this.uiRecoveryInitialGraceUntil = 0;
    this.uiRecoveryLastErrorCode = '';
    this.uiRecoveryLastState = state;
  }

  uiRecoveryStatus({ presence = null, preferCachedPresence = false } = {}) {
    const now = Date.now();
    const preference = this.activation.uiRecoveryPreferenceStatus();
    const observedPresence = presence && typeof presence === 'object'
      ? presence
      : this.activation.uiPresence({ preferCached: preferCachedPresence });
    this.uiRecoveryAttempts = this.uiRecoveryAttempts.filter((time) => time >= now - UI_RECOVERY_WINDOW_MS);
    let state = this.uiRecoveryLastState;
    if (preference.suppressed) state = 'suppressed';
    else if (observedPresence.alive === true) state = 'healthy';
    else if (observedPresence.alive === null) state = 'unknown';
    else if (this.activation.hasPendingUiActivation()) state = 'activation_pending';
    else if (!observedPresence.tracked && this.uiRecoveryInitialGraceUntil > now) state = 'awaiting_initial_registration';
    else if (this.uiRecoveryCircuitUntil > now) state = 'circuit_suppressed';
    else if (this.uiRecoveryPendingUntil > now) state = 'waiting_for_registration';
    else if (this.uiRecoveryNextAttemptAt > now) state = 'cooldown';
    else if (observedPresence.alive === false) state = 'missing';
    return {
      state,
      registered: observedPresence.tracked,
      alive: observedPresence.alive,
      pid: observedPresence.pid || null,
      instance_id: observedPresence.instance_id || null,
      started_at_unix_ms: Number(this.activation.uiRegistration?.started_at_unix_ms || 0) || null,
      runtime_mode: typeof this.paths.runtimeMode === 'function' ? this.paths.runtimeMode() : null,
      suppressed: preference.suppressed,
      suppression_reason: preference.reason || '',
      attempts_in_window: this.uiRecoveryAttempts.length,
      last_launch_pid: this.uiRecoveryLastLaunchPid || null,
      initial_registration_grace_until_unix_ms: this.uiRecoveryInitialGraceUntil || null,
      pending_registration_until_unix_ms: this.uiRecoveryPendingUntil || null,
      next_attempt_at_unix_ms: this.uiRecoveryNextAttemptAt || null,
      circuit_suppressed_until_unix_ms: this.uiRecoveryCircuitUntil || null,
      last_error_code: this.uiRecoveryLastErrorCode || null
    };
  }

  async superviseElectronUi() {
    if (this.uiRecoveryLaunchInFlight) return this.uiRecoveryLaunchInFlight;
    const operation = (async () => {
      const now = Date.now();
      const preference = this.activation.uiRecoveryPreferenceStatus();
      const presence = await this.activation.observeUiPresence();
      this.uiRecoveryAttempts = this.uiRecoveryAttempts.filter((time) => time >= now - UI_RECOVERY_WINDOW_MS);
      if (preference.suppressed) {
        this.uiRecoveryLastState = 'suppressed';
        return this.uiRecoveryStatus({ presence });
      }
      if (presence.alive) {
        this.resetUiRecoveryTracking('healthy');
        return this.uiRecoveryStatus({ presence });
      }
      if (presence.alive === null) {
        this.uiRecoveryLastState = 'unknown';
        this.uiRecoveryLastErrorCode = 'UI_PROCESS_IDENTITY_UNVERIFIED';
        return this.uiRecoveryStatus({ presence });
      }
      if (this.activation.hasPendingUiActivation()) {
        this.uiRecoveryLastState = 'activation_pending';
        return this.uiRecoveryStatus({ presence });
      }
      if (!presence.tracked && this.uiRecoveryInitialGraceUntil > now) {
        this.uiRecoveryLastState = 'awaiting_initial_registration';
        return this.uiRecoveryStatus({ presence });
      }
      if (typeof this.spawnElectronUi !== 'function') {
        this.uiRecoveryLastState = 'unavailable';
        this.uiRecoveryLastErrorCode = 'UI_RECOVERY_LAUNCHER_UNAVAILABLE';
        return this.uiRecoveryStatus({ presence });
      }
      if (this.uiRecoveryCircuitUntil > now) {
        this.uiRecoveryLastState = 'circuit_suppressed';
        return this.uiRecoveryStatus({ presence });
      }
      if (this.uiRecoveryPendingUntil > now) {
        this.uiRecoveryLastState = 'waiting_for_registration';
        return this.uiRecoveryStatus({ presence });
      }
      if (this.uiRecoveryNextAttemptAt > now) {
        this.uiRecoveryLastState = 'cooldown';
        return this.uiRecoveryStatus({ presence });
      }
      if (this.uiRecoveryAttempts.length >= UI_RECOVERY_ATTEMPT_LIMIT) {
        this.uiRecoveryCircuitUntil = now + UI_RECOVERY_CIRCUIT_BREAK_MS;
        this.uiRecoveryLastState = 'circuit_suppressed';
        return this.uiRecoveryStatus({ presence });
      }
      this.uiRecoveryAttempts.push(now);
      try {
        const pid = await this.spawnElectronUi({});
        this.uiRecoveryLastLaunchPid = Number(pid || 0);
        this.uiRecoveryPendingUntil = now + UI_RECOVERY_REGISTRATION_TIMEOUT_MS;
        this.uiRecoveryNextAttemptAt = now + UI_RECOVERY_COOLDOWN_MS;
        this.uiRecoveryLastErrorCode = '';
        this.uiRecoveryLastState = 'launch_started';
        this.log.info('Recovery Host started a replacement Electron UI after unexpected UI loss', {
          launchPid: this.uiRecoveryLastLaunchPid || null,
          attemptsInWindow: this.uiRecoveryAttempts.length
        });
      } catch (error) {
        this.uiRecoveryPendingUntil = 0;
        this.uiRecoveryNextAttemptAt = now + UI_RECOVERY_COOLDOWN_MS;
        this.uiRecoveryLastErrorCode = String(error?.code || 'UI_RECOVERY_LAUNCH_FAILED');
        this.uiRecoveryLastState = 'launch_failed';
        this.log.error(error.message, { stage: 'electron-ui-recovery', code: this.uiRecoveryLastErrorCode });
      }
      return this.uiRecoveryStatus({ presence });
    })();
    this.uiRecoveryLaunchInFlight = operation;
    try {
      return await operation;
    } finally {
      if (this.uiRecoveryLaunchInFlight === operation) this.uiRecoveryLaunchInFlight = null;
    }
  }

  bootstrapBlocksAdmission() {
    const state = String(this.bootstrapActivation?.state || 'pending');
    // A failed bootstrap receipt is immutable evidence of a failed attempt,
    // not an enduring ownership lease.  It may release admission only through
    // reconcileTerminalBootstrapReceipt(), which validates the independent
    // durable epoch, current Recovery Host identity, and a fresh ledger census.
    return Boolean(this.bootstrap && !TERMINAL_BOOTSTRAP_STATES.has(state));
  }

  readyAdoptionBlocksAdmission() {
    return Boolean(this.readyAdoptionBlocked);
  }

  refreshReadyAdoptionGuard() {
    const blockedEpochId = String(this.readyAdoptionBlocked?.activation_epoch_id || '').trim();
    if (!blockedEpochId) return false;
    let current = null;
    try { current = this.activationEpochStore.current(); }
    catch {
      // An unreadable store is never evidence that the guard can be cleared.
      return false;
    }
    const currentEpochId = String(current?.activation_epoch_id || '').trim();
    if (!currentEpochId || currentEpochId === blockedEpochId) return false;
    // A replacement/full-clean operation owns the new epoch.  Drop only the
    // process-local diagnostic for the retired READY record; the new epoch's
    // own state/admission gates remain authoritative and are revalidated by
    // the coordinator before any READY/open projection.
    this.readyAdoptionBlocked = null;
    return true;
  }

  readyAdoptionBlockDetails() {
    if (!this.readyAdoptionBlocked) return null;
    return {
      ...this.readyAdoptionBlocked,
      code: 'UPDATE_INCOMPLETE',
      message: 'Durable READY activation lacks strict current-process connector discovery proof.'
    };
  }

  assertReadyAdoptionMutationAllowed({ allowFullCleanRefresh = false } = {}) {
    // The guard is process-local because the durable READY record is immutable.
    // Reconcile it immediately before every guarded mutation so a replacement
    // epoch created by an explicit full-clean refresh can become authoritative
    // without requiring a Recovery Host process restart.  A failed/read-error
    // read leaves the guard intact (refreshReadyAdoptionGuard is fail-closed).
    this.refreshReadyAdoptionGuard();
    if (!this.readyAdoptionBlocksAdmission() || allowFullCleanRefresh) return true;
    const details = this.readyAdoptionBlockDetails();
    throw Object.assign(new Error(details.message), {
      code: 'UPDATE_INCOMPLETE',
      details
    });
  }

  assertBootstrapMutationAllowed() {
    if (!this.bootstrapBlocksAdmission()) return true;
    throw Object.assign(new Error('Recovery Host bootstrap owns activation; external runtime mutation is closed.'), {
      code: 'RECOVERY_BOOTSTRAP_IN_PROGRESS',
      details: {
        operation_id: this.bootstrap?.operation_id || null,
        state: this.bootstrapActivation?.state || 'pending'
      }
    });
  }

  async reconcileTerminalBootstrapReceipt(durableEpoch = null) {
    const bootstrap = this.bootstrap;
    const activation = this.bootstrapActivation;
    const attemptedOperationId = String(bootstrap?.operation_id || '').trim();
    if (!bootstrap || !attemptedOperationId || String(activation?.state || '') !== 'receipt_conflict') {
      throw Object.assign(new Error('Recovery Host has no terminal bootstrap receipt conflict to reconcile.'), {
        code: 'RECOVERY_BOOTSTRAP_RECONCILIATION_UNAVAILABLE'
      });
    }
    if (!this.running || !this.ownsLock || !this.processIdentity) {
      throw Object.assign(new Error('Recovery Host ownership is unavailable for terminal bootstrap reconciliation.'), {
        code: 'RECOVERY_BOOTSTRAP_RECONCILIATION_UNVERIFIED'
      });
    }

    const verifyReadyEpoch = (record) => {
      const operationId = String(record?.operation_id || '').trim();
      const activationEpochId = String(record?.activation_epoch_id || '').trim();
      const admission = String(record?.admission_state || '').trim().toUpperCase();
      if (!record || record.state !== 'READY' || admission !== 'OPEN'
        || !operationId || !activationEpochId || operationId === attemptedOperationId) {
        throw Object.assign(new Error('The durable activation epoch cannot prove that this terminal bootstrap attempt is superseded.'), {
          code: 'RECOVERY_BOOTSTRAP_RECONCILIATION_EPOCH_UNVERIFIED',
          details: {
            attempted_operation_id: attemptedOperationId,
            durable_operation_id: operationId || null,
            activation_epoch_id: activationEpochId || null,
            state: String(record?.state || '') || null,
            admission_state: admission || null
          }
        });
      }
      const conflictOperationId = String(activation?.operation_id || '').trim();
      const conflictEpochId = String(activation?.activation_epoch_id || '').trim();
      if ((conflictOperationId && conflictOperationId !== operationId)
        || (conflictEpochId && conflictEpochId !== activationEpochId)) {
        throw Object.assign(new Error('The receipt-conflict projection does not match the current durable activation epoch.'), {
          code: 'RECOVERY_BOOTSTRAP_RECONCILIATION_EPOCH_CHANGED',
          details: {
            attempted_operation_id: attemptedOperationId,
            conflict_operation_id: conflictOperationId || null,
            durable_operation_id: operationId,
            conflict_activation_epoch_id: conflictEpochId || null,
            durable_activation_epoch_id: activationEpochId
          }
        });
      }
      return { operationId, activationEpochId };
    };

    const initialEpoch = durableEpoch || this.activationEpochStore.current();
    const readyEpoch = verifyReadyEpoch(initialEpoch);
    const terminalResult = readBootstrapResult(this.paths, attemptedOperationId);
    const terminalState = String(terminalResult?.state || '');
    const terminalErrorCode = String(terminalResult?.error?.code || '').trim();
    const terminalErrorMessage = String(terminalResult?.error?.message || '').trim();
    if (!terminalResult || terminalResult.operation_id !== attemptedOperationId
      || !['failed', 'expired'].includes(terminalState)
      || !terminalErrorCode || !terminalErrorMessage) {
      throw Object.assign(new Error('The conflicting bootstrap result is not a valid terminal failed/expired receipt.'), {
        code: 'RECOVERY_BOOTSTRAP_RECONCILIATION_RECEIPT_UNVERIFIED',
        details: {
          attempted_operation_id: attemptedOperationId,
          result_state: terminalState || null,
          error_code: terminalErrorCode || null
        }
      });
    }

    const observedSelf = await this.processIdentityObserver(process.pid);
    if (observedSelf?.state !== 'live' || !sameProcessIdentity(this.processIdentity, observedSelf)) {
      throw Object.assign(new Error('Recovery Host process identity changed before terminal bootstrap reconciliation.'), {
        code: 'RECOVERY_BOOTSTRAP_RECONCILIATION_IDENTITY_CHANGED',
        details: { pid: process.pid, instance_id: this.instanceId }
      });
    }
    const lock = readLock(this.paths.recoveryHostLockFile());
    if (Number(lock?.pid) !== Number(process.pid) || String(lock?.instance_id || '') !== this.instanceId) {
      throw Object.assign(new Error('Recovery Host lock ownership changed before terminal bootstrap reconciliation.'), {
        code: 'RECOVERY_BOOTSTRAP_RECONCILIATION_OWNERSHIP_CHANGED',
        details: { pid: process.pid, instance_id: this.instanceId }
      });
    }
    if (typeof this.canonicalLedgerCensus !== 'function') {
      throw Object.assign(new Error('Canonical ledger census is unavailable for terminal bootstrap reconciliation.'), {
        code: 'ORCHESTRATION_STATE_UNCERTAIN'
      });
    }
    // An explicit npm-start process refresh is intentionally checkpoint-free
    // and preserves pre-existing accepted-work state.  It may observe durable
    // AWAITING_ACCEPTANCE records without gaining authority to accept them;
    // this is the same narrow allowance used by FullCleanActivation for a
    // validated refresh envelope, never for a source-checkpoint activation.
    const allowAcceptancePending = bootstrap.refresh === true
      && bootstrap.source_checkpoint === null
      && bootstrap.allow_acceptance_pending === true;
    const workspace = String(this.settings?.load?.()?.workspace || '').trim();
    const census = await this.canonicalLedgerCensus({
      paths: this.paths,
      workspace,
      allowAcceptancePending
    });
    const validCensus = census?.safe === true
      && census?.code === 'READY'
      && census?.content_free === true
      && census?.mutated_canonical_ledger === false
      && census?.snapshot?.immutable === true
      && census?.snapshot?.query_only === true
      && census?.lifecycle?.projection_drift === false
      && Number(census?.lifecycle?.unexplained_active_runs || 0) === 0
      && Number(census?.lifecycle?.unbound_live_resource_residues || 0) === 0;
    if (!validCensus) {
      throw Object.assign(new Error('Canonical ledger census refused terminal bootstrap reconciliation.'), {
        code: census?.code || 'ORCHESTRATION_STATE_UNCERTAIN',
        details: {
          attempted_operation_id: attemptedOperationId,
          census_code: census?.code || null,
          census_reason: census?.reason || null,
          census_fingerprint: census?.census_fingerprint || null
        }
      });
    }
    const finalEpoch = this.activationEpochStore.current();
    const finalReadyEpoch = verifyReadyEpoch(finalEpoch);
    if (finalReadyEpoch.operationId !== readyEpoch.operationId
      || finalReadyEpoch.activationEpochId !== readyEpoch.activationEpochId) {
      throw Object.assign(new Error('The durable activation epoch changed during terminal bootstrap reconciliation.'), {
        code: 'RECOVERY_BOOTSTRAP_RECONCILIATION_EPOCH_CHANGED',
        details: {
          attempted_operation_id: attemptedOperationId,
          initial_operation_id: readyEpoch.operationId,
          final_operation_id: finalReadyEpoch.operationId,
          initial_activation_epoch_id: readyEpoch.activationEpochId,
          final_activation_epoch_id: finalReadyEpoch.activationEpochId
        }
      });
    }
    const consumed = removeBootstrapEnvelope(this.paths, attemptedOperationId, bootstrap.integrity_sha256 || '');
    if (consumed !== true) {
      throw Object.assign(new Error('The exact bootstrap envelope was unavailable for guarded reconciliation consumption.'), {
        code: 'RECOVERY_BOOTSTRAP_RECONCILIATION_ENVELOPE_UNVERIFIED',
        details: { attempted_operation_id: attemptedOperationId }
      });
    }
    this.bootstrapEnvelopeConsumed = true;
    this.bootstrapActivation = {
      state: 'reconciled_terminal_receipt',
      operation_id: finalReadyEpoch.operationId,
      activation_epoch_id: finalReadyEpoch.activationEpochId,
      attempted_operation_id: attemptedOperationId,
      terminal_result_state: terminalState,
      error_code: terminalErrorCode,
      reconciled_at_unix_ms: Date.now(),
      census_fingerprint: String(census.census_fingerprint || '') || null
    };
    return this.bootstrapActivation;
  }

  async prepareBootstrapStart(durableEpoch) {
    if (!this.bootstrap) return null;
    const operationId = String(this.bootstrap.operation_id || '').trim();
    const expiresAtUnixMs = Number(this.bootstrap.expires_at_unix_ms || 0);
    if (!operationId || !Number.isSafeInteger(expiresAtUnixMs) || Date.now() >= expiresAtUnixMs) {
      throw Object.assign(new Error('Recovery Host bootstrap request expired before startup.'), {
        code: 'RECOVERY_BOOTSTRAP_EXPIRED',
        details: { operation_id: operationId || null, expires_at_unix_ms: expiresAtUnixMs || null }
      });
    }
    const oldPid = Number(this.bootstrap.old_host_pid || 0);
    const oldInstanceId = String(this.bootstrap.old_host_instance_id || '').trim();
    const oldProcessStartToken = normalizeProcessStartToken(this.bootstrap.old_host_process_start_token);
    if (!Number.isInteger(oldPid) || oldPid <= 0 || !oldInstanceId || !oldProcessStartToken
      || oldPid === process.pid || oldInstanceId === this.instanceId) {
      throw Object.assign(new Error('Previous Recovery Host identity is still active or was not replaced.'), {
        code: 'RECOVERY_BOOTSTRAP_OLD_HOST_ACTIVE',
        details: {
          operation_id: operationId,
          old_host_pid: oldPid,
          old_host_process_start_token: oldProcessStartToken || null,
          old_host_instance_id: oldInstanceId
        }
      });
    }
    let observedOldHost;
    try { observedOldHost = await this.processIdentityObserver(oldPid); }
    catch (error) {
      throw Object.assign(new Error('Previous Recovery Host process identity could not be observed.'), {
        code: 'RECOVERY_BOOTSTRAP_PROCESS_IDENTITY_UNVERIFIED',
        cause: error
      });
    }
    if (observedOldHost?.state === 'unavailable' || !['absent', 'live'].includes(String(observedOldHost?.state || ''))) {
      throw Object.assign(new Error('Previous Recovery Host process identity could not be observed.'), {
        code: 'RECOVERY_BOOTSTRAP_PROCESS_IDENTITY_UNVERIFIED'
      });
    }
    if (observedOldHost?.state === 'live' && sameProcessIdentity({
      pid: oldPid,
      process_start_token: oldProcessStartToken
    }, observedOldHost)) {
      throw Object.assign(new Error('Previous Recovery Host identity is still active or was not replaced.'), {
        code: 'RECOVERY_BOOTSTRAP_OLD_HOST_ACTIVE',
        details: {
          operation_id: operationId,
          old_host_pid: oldPid,
          old_host_process_start_token: oldProcessStartToken,
          old_host_instance_id: oldInstanceId
        }
      });
    }
    const revision = this.revisions.status('recovery_host', this.recoveryHostRunningRevision, { force: true });
    const expectedRevision = String(this.bootstrap.expected_disk_revision || '').trim().toLowerCase();
    if (!expectedRevision || revision.state !== 'current'
      || String(revision.running_revision || '').toLowerCase() !== expectedRevision
      || String(revision.disk_revision || '').toLowerCase() !== expectedRevision) {
      throw Object.assign(new Error('Bootstrap Recovery Host is not running the requested current checkout revision.'), {
        code: 'RECOVERY_BOOTSTRAP_REVISION_MISMATCH',
        details: {
          operation_id: operationId,
          expected_disk_revision: expectedRevision || null,
          running_revision: revision.running_revision || null,
          disk_revision: revision.disk_revision || null,
          revision_state: revision.state || null
        }
      });
    }
    const suppliedEpochId = String(this.bootstrap.activation_epoch_id || '').trim();
    if (durableEpoch && String(durableEpoch.operation_id || '') === operationId) {
      if (suppliedEpochId && String(durableEpoch.activation_epoch_id || '') !== suppliedEpochId) {
        throw Object.assign(new Error('Bootstrap activation epoch does not match the durable operation.'), {
          code: 'ACTIVATION_EPOCH_ID_MISMATCH'
        });
      }
      if (durableEpoch.state === 'FAILED' || durableEpoch.state === 'READY') {
        throw Object.assign(new Error('Bootstrap activation epoch is already terminal.'), {
          code: durableEpoch.state === 'FAILED' ? 'UPDATE_INCOMPLETE' : 'RECOVERY_BOOTSTRAP_TERMINAL',
          details: {
            operation_id: operationId,
            activation_epoch_id: durableEpoch.activation_epoch_id,
            state: durableEpoch.state
          }
        });
      }
      return { operationId, expectedRevision, expiresAtUnixMs, replayEpoch: durableEpoch, requiresNewEpoch: false };
    }
    const priorResult = readBootstrapResult(this.paths, operationId);
    if (priorResult && ['completed', 'failed', 'expired'].includes(String(priorResult.state || ''))) {
      throw Object.assign(new Error('Recovery Host bootstrap operation is already terminal without a matching durable epoch.'), {
        code: 'RECOVERY_BOOTSTRAP_TERMINAL',
        details: { operation_id: operationId, state: priorResult.state }
      });
    }
    if (suppliedEpochId) {
      throw Object.assign(new Error('Bootstrap supplied an activation epoch that is not the current durable operation.'), {
        code: 'ACTIVATION_EPOCH_NOT_CURRENT'
      });
    }
    if (durableEpoch && ACTIVE_STATES.has(durableEpoch.state)) {
      const durableExpiry = Number(
        durableEpoch.expires_at_unix_ms || durableEpoch.metadata?.expires_at_unix_ms || 0
      );
      if (durableExpiry > 0 && Date.now() >= durableExpiry) {
        const expiredEpochId = durableEpoch.activation_epoch_id;
        try {
          durableEpoch = this.activationEpochStore.fail(expiredEpochId, {
            code: 'ACTIVATION_REQUEST_EXPIRED',
            message: 'The prior activation epoch expired before a new bootstrap refresh.',
            details: {
              activation_epoch_id: expiredEpochId,
              operation_id: durableEpoch.operation_id || null,
              expires_at_unix_ms: durableExpiry,
              process_mutated: false
            }
          });
        } catch (error) {
          // The store atomically terminalizes an epoch detected exactly at an
          // expiry boundary and then throws the typed expiry to its caller.
          // Re-read and accept only that exact durable FAILED result.
          const terminal = this.activationEpochStore.current();
          if (String(error?.code || '') !== 'ACTIVATION_REQUEST_EXPIRED'
            || terminal?.activation_epoch_id !== expiredEpochId
            || terminal?.state !== 'FAILED'
            || terminal?.error?.code !== 'ACTIVATION_REQUEST_EXPIRED') {
            throw error;
          }
          durableEpoch = terminal;
        }
      } else {
        throw Object.assign(new Error('Another durable activation epoch is already active.'), {
          code: 'ACTIVATION_EPOCH_ACTIVE',
          details: { activation_epoch_id: durableEpoch.activation_epoch_id, operation_id: durableEpoch.operation_id || null }
        });
      }
    }
    return {
      operationId,
      expectedRevision,
      expiresAtUnixMs,
      replayEpoch: null,
      requiresNewEpoch: true,
      durableEpoch
    };
  }

  recordBootstrapEpoch(epoch, extra = {}) {
    if (!epoch || typeof epoch !== 'object') return null;
    const operationId = String(epoch.operation_id || '').trim();
    const isBootstrapOperation = Boolean(
      operationId
      && (operationId === String(this.bootstrap?.operation_id || '')
        || String(epoch.metadata?.reason || '') === 'recovery_host_bootstrap')
    );
    if (!isBootstrapOperation) return null;
    const state = epoch.state === 'READY' ? 'completed' : epoch.state === 'FAILED' ? 'failed' : 'started';
    const receipt = {
      operation_id: operationId,
      state,
      ...(epoch.state === 'FAILED' ? { error: epoch.error || { code: 'UPDATE_INCOMPLETE', message: 'Full-clean bootstrap activation failed.' } } : {}),
      result: {
        activation_epoch_id: epoch.activation_epoch_id || null,
        activation_state: epoch.state || null,
        admission_open: epoch.admission_state === 'OPEN',
        fully_ready: epoch.state === 'READY' && epoch.admission_state === 'OPEN',
        ...extra
      }
    };
    try { writeBootstrapResult(this.paths, receipt); }
    catch (error) {
      this.log?.error?.(error.message, { stage: 'recovery-bootstrap-result', operationId, code: error?.code || '' });
    }
    if (this.bootstrap && operationId === String(this.bootstrap.operation_id || '')) {
      this.bootstrapActivation = { state, operation_id: operationId, activation_epoch_id: epoch.activation_epoch_id || null };
      if (!this.bootstrapEnvelopeConsumed) {
        try {
          removeBootstrapEnvelope(this.paths, operationId, this.bootstrap.integrity_sha256 || '');
          this.bootstrapEnvelopeConsumed = true;
        } catch (error) {
          this.log?.error?.(error.message, { stage: 'recovery-bootstrap-consume', operationId, code: error?.code || '' });
        }
      }
    }
    return receipt;
  }

  recordBootstrapFailure(error, durableEpoch = null) {
    if (!this.bootstrap) return null;
    if (durableEpoch && String(durableEpoch.operation_id || '') === String(this.bootstrap.operation_id || '')) {
      return this.recordBootstrapEpoch(durableEpoch);
    }
    const state = String(error?.code || '') === 'RECOVERY_BOOTSTRAP_EXPIRED' ? 'expired' : 'failed';
    this.bootstrapActivation = { state, operation_id: this.bootstrap.operation_id || null };
    try {
      writeBootstrapResult(this.paths, {
        operation_id: this.bootstrap.operation_id,
        state,
        error: { code: error?.code || 'RECOVERY_BOOTSTRAP_FAILED', message: error?.message || String(error) },
        result: { activation_epoch_id: null, admission_open: false, fully_ready: false }
      });
    } catch (persistError) {
      this.log?.error?.(persistError.message, { stage: 'recovery-bootstrap-failure-result', code: persistError?.code || '' });
    }
    return this.bootstrapActivation;
  }

  recoveryPingStatus() {
    const bootstrapAdmissionBlocked = this.bootstrapBlocksAdmission();
    const readyAdoptionBlocked = this.readyAdoptionBlocksAdmission();
    return {
      ready: this.running && !bootstrapAdmissionBlocked && !readyAdoptionBlocked,
      state: bootstrapAdmissionBlocked
        ? 'bootstrapping'
        : readyAdoptionBlocked
          ? 'update_incomplete'
          : this.running ? 'healthy' : 'starting',
      pid: process.pid,
      process_start_token: this.processIdentity?.process_start_token || null,
      instance_id: this.instanceId,
      device_id: this.deviceIdentity.device_id,
      device_instance_id: this.deviceInstanceId,
      started_at: this.startedAt,
      ...(readyAdoptionBlocked ? { ready_adoption: this.readyAdoptionBlockDetails() } : {})
    };
  }

  cachedHostStatus() {
    const projected = this.lastSupervisionProjection?.recoveryHost;
    if (projected && typeof projected === 'object' && !Array.isArray(projected)) {
      const observedAtUnixMs = Number(this.lastSupervisionObservedAtUnixMs || 0);
      const ageMs = observedAtUnixMs > 0 ? Math.max(0, Date.now() - observedAtUnixMs) : null;
      return {
        ...projected,
        telemetry_available: true,
        signal_stale: ageMs === null || ageMs > SUPERVISION_STATUS_STALE_MS,
        snapshot_observed_at_unix_ms: observedAtUnixMs || null,
        snapshot_age_ms: ageMs
      };
    }
    // Before the first supervision projection, retain fail-closed status
    // semantics but prohibit fresh OS process-identity and forced revision
    // probes on the IPC event loop.
    return this.hostStatus({ preferCachedRuntime: true });
  }

  hostStatus({ preferCachedRuntime = false } = {}) {
    // Cached IPC projections must remain a pure read model: invoking the
    // durable store here would turn a lightweight heartbeat into a blocking
    // disk/lock read.  Fresh operator/status reads, however, are an
    // authoritative opportunity to retire a guard for a genuinely new epoch.
    if (!preferCachedRuntime) this.refreshReadyAdoptionGuard();
    let codeRevision;
    try {
      codeRevision = this.revisions.status('recovery_host', this.recoveryHostRunningRevision, { force: !preferCachedRuntime });
    } catch (error) {
      codeRevision = {
        running_revision: this.recoveryHostRunningRevision || null,
        disk_revision: null,
        update_pending: null,
        state: 'unavailable',
        error_code: String(error?.code || 'REVISION_UNAVAILABLE')
      };
    }
    const electronUiPresence = this.activation.uiPresence({ preferCached: preferCachedRuntime });
    const electronUiRevision = this.activation.uiRevisionStatus({
      force: !preferCachedRuntime,
      presence: electronUiPresence
    });
    const autoActivation = this.autoActivation?.status?.() || null;
    let codingMcpRevision = {};
    if (preferCachedRuntime) {
      codingMcpRevision = this.lastSupervisionStatus?.codeRevision?.codingMcp || {};
    } else {
      try { codingMcpRevision = this.orchestrator.codingMcpRevisionStatus?.({ force: true }) || {}; } catch {}
    }
    let activationEpoch = null;
    try { activationEpoch = this.fullCleanActivation?.current?.() || null; } catch (error) {
      activationEpoch = { state: 'UPDATE_INCOMPLETE', admission_state: 'CLOSED', error: { code: String(error?.code || 'ACTIVATION_EPOCH_STORE_INVALID'), message: String(error?.message || error) } };
    }
    let epochStatus = this.orchestrator.activationEpochStatus?.() || {
      activation_epoch_id: activationEpoch?.activation_epoch_id || null,
      operation_id: activationEpoch?.operation_id || null,
      state: activationEpoch?.state || 'NONE',
      // A READY state without an explicit OPEN admission bit is not an open
      // runtime.  This fallback is used by legacy/test orchestrators and must
      // fail closed instead of projecting a stale green status.
      admission_open: !activationEpoch
        || (activationEpoch.state === 'READY' && activationEpoch.admission_state === 'OPEN'),
      update_incomplete: Boolean(activationEpoch && (activationEpoch.state !== 'READY' || activationEpoch.admission_state !== 'OPEN'))
    };
    const durableOperationId = String(activationEpoch?.operation_id || '').trim() || null;
    const projectedOperationId = String(epochStatus?.operation_id || '').trim() || null;
    epochStatus = { ...epochStatus, operation_id: durableOperationId };
    if (projectedOperationId && projectedOperationId !== durableOperationId) {
      epochStatus = {
        ...epochStatus,
        admission_open: false,
        update_incomplete: true,
        error_code: 'ACTIVATION_OPERATION_MISMATCH'
      };
    }
    const bootstrapAdmissionBlocked = this.bootstrapBlocksAdmission();
    if (bootstrapAdmissionBlocked) {
      epochStatus = {
        ...epochStatus,
        state: epochStatus?.state && epochStatus.state !== 'NONE' ? epochStatus.state : 'UPDATE_INCOMPLETE',
        admission_open: false,
        update_incomplete: true
      };
    }
    const readyAdoptionBlocked = this.readyAdoptionBlocksAdmission();
    if (readyAdoptionBlocked) {
      const block = this.readyAdoptionBlockDetails();
      epochStatus = {
        ...epochStatus,
        // Preserve the durable READY state as `epoch_state` while exposing the
        // host's effective admission state as incomplete.  This prevents a
        // malformed terminal record from being projected as a usable runtime.
        state: 'UPDATE_INCOMPLETE',
        admission_open: false,
        update_incomplete: true,
        error_code: 'UPDATE_INCOMPLETE',
        error: block
      };
    }
    const fullCleanAvailable = Boolean(
      this.fullCleanActivation
      && typeof this.fullCleanActivation.restart === 'function'
      && typeof this.fullCleanActivation.finalCensus === 'function'
      && codeRevision.state === 'current'
      && codeRevision.running_revision
      && codeRevision.disk_revision
      && codeRevision.running_revision === codeRevision.disk_revision
    );
    const fullCleanState = !this.fullCleanActivation
      ? 'unavailable'
      : fullCleanAvailable ? 'current' : 'stale';
    const connectorCurrentSha256 = String(this.lastSupervisionStatus?.toolContract?.sha256 || '').trim().toLowerCase();
    const connectorAcknowledgedSha256 = String(this.lastSupervisionStatus?.connectorContractAcknowledgedSha256 || '').trim().toLowerCase();
    const connectorAckShaMatches = Boolean(
      /^[a-f0-9]{64}$/.test(connectorCurrentSha256)
      && connectorCurrentSha256 === connectorAcknowledgedSha256
    );
    const connectorContractState = String(this.lastSupervisionStatus?.connectorContractState || 'UNAVAILABLE');
    const connectorFreshnessMode = String(this.lastSupervisionStatus?.connectorFreshnessMode || '');
    const connectorEvidenceCurrent = Boolean(
      (connectorContractState === 'CURRENT_ACKNOWLEDGED'
        && connectorFreshnessMode === 'current_process_discovery'
        && this.lastSupervisionStatus?.connectorRediscovered === true
        && connectorTimestampValid(this.lastSupervisionStatus?.connectorRediscoveredAt))
      || (connectorContractState === 'CURRENT_COMPATIBLE_ACKNOWLEDGED'
        && connectorFreshnessMode === 'compatible_activation_bootstrap'
        && this.lastSupervisionStatus?.connectorRediscovered !== true
        && this.lastSupervisionStatus?.connectorCompatibilityAcknowledged === true
        && connectorTimestampValid(this.lastSupervisionStatus?.connectorCompatibilityAcknowledgedAt))
    );
    const connectorReady = Boolean(
      this.lastSupervisionStatus?.connectorRefreshRequired === false
      && connectorEvidenceCurrent
      && this.lastSupervisionStatus?.connectorAcknowledgementPending === false
      && connectorAckShaMatches
    );
    const activationClosure = activationClosureProjection({
      autoActivation,
      recoveryHostRevision: codeRevision,
      electronUiRevision,
      codingMcpRevision,
      runtime: {
        ...(this.lastSupervisionStatus || {}),
        connectorContractState: 'UNAVAILABLE'
      }
    });
    return {
      state: bootstrapAdmissionBlocked
        ? 'bootstrapping'
        : readyAdoptionBlocked
          ? 'update_incomplete'
          : this.running ? 'healthy' : 'starting',
      pid: process.pid,
      process_start_token: this.processIdentity?.process_start_token || null,
      instance_id: this.instanceId,
      device_id: this.deviceIdentity.device_id,
      device_instance_id: this.deviceInstanceId,
      device_display_name: this.deviceIdentity.display_name,
      started_at: this.startedAt,
      watchdog_interval_ms: SUPERVISION_INTERVAL_MS,
      gateway: this.gateway?.server ? 'healthy' : 'stopped',
      gateway_metrics: this.gateway?.metrics?.() || null,
      code_revision: codeRevision,
      full_clean_activation: {
        available: fullCleanAvailable,
        contract_version: 1,
        running_revision: codeRevision.running_revision || null,
        disk_revision: codeRevision.disk_revision || null,
        state: fullCleanState,
        activation_epoch_id: epochStatus.activation_epoch_id || null
      },
      recovery_bootstrap: this.bootstrap ? {
        operation_id: this.bootstrap.operation_id || null,
        expected_disk_revision: this.bootstrap.expected_disk_revision || null,
        old_host_pid: Number(this.bootstrap.old_host_pid || 0) || null,
        old_host_process_start_token: this.bootstrap.old_host_process_start_token || null,
        old_host_instance_id: this.bootstrap.old_host_instance_id || null,
        state: this.bootstrapActivation?.state || 'pending',
        attempted_operation_id: this.bootstrapActivation?.attempted_operation_id || null,
        terminal_result_state: this.bootstrapActivation?.terminal_result_state || null,
        error_code: this.bootstrapActivation?.error_code || null,
        reconciled_at_unix_ms: this.bootstrapActivation?.reconciled_at_unix_ms || null,
        census_fingerprint: this.bootstrapActivation?.census_fingerprint || null
      } : null,
      capabilities: {
        full_clean_activation: fullCleanAvailable,
        activation_epoch: true
      },
      electron_ui_revision: electronUiRevision,
      electron_ui_recovery: this.uiRecoveryStatus({
        presence: electronUiPresence,
        preferCachedPresence: preferCachedRuntime
      }),
      auto_activation: autoActivation,
      activation_closure: activationClosure,
      activation_epoch: epochStatus,
      ready_adoption: readyAdoptionBlocked ? {
        state: 'blocked',
        ...this.readyAdoptionBlockDetails()
      } : { state: 'adopted' },
      recovery_plane_mode: 'independent_mcp_tunnel_v1',
      recovery_plane: this.lastRecoveryPlaneStatus,
      last_progress: this.lastProgress,
      runtime: this.lastSupervisionStatus ? {
        mcp: Boolean(this.lastSupervisionStatus.mcpRunning),
        tunnel: Boolean(this.lastSupervisionStatus.tunnelRunning),
        fully_ready: Boolean(this.lastSupervisionStatus.fullyReady
          && epochStatus.admission_open === true
          && fullCleanAvailable
          && connectorReady
          && connectorAckShaMatches),
        update_incomplete: Boolean(epochStatus.update_incomplete
          || !fullCleanAvailable
          || !connectorReady
          || !connectorAckShaMatches),
        connector_ready: connectorReady,
        connector_ack_sha_matches: connectorAckShaMatches,
        connector_current_sha256: connectorCurrentSha256 || null,
        connector_acknowledged_sha256: connectorAcknowledgedSha256 || null,
        activation_epoch_id: epochStatus.activation_epoch_id || null,
        recovering: Boolean(this.lastSupervisionStatus.recovering),
        recovery_blocked: Boolean(this.lastSupervisionStatus.recoveryBlocked)
      } : null
    };
  }

  decorate(value, { preferCachedRuntime = false } = {}) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return value;
    const recoveryHost = this.hostStatus({ preferCachedRuntime });
    const activationClosure = activationClosureProjection({
      autoActivation: recoveryHost.auto_activation,
      recoveryHostRevision: recoveryHost.code_revision,
      electronUiRevision: recoveryHost.electron_ui_revision,
      codingMcpRevision: preferCachedRuntime
        ? (value?.codeRevision?.codingMcp || this.lastSupervisionStatus?.codeRevision?.codingMcp || {})
        : (() => {
          try { return this.orchestrator.codingMcpRevisionStatus?.({ force: true }) || {}; } catch { return {}; }
        })(),
      runtime: value
    });
    recoveryHost.activation_closure = activationClosure;
    let currentSettings = {};
    try { currentSettings = this.settings.load() || {}; } catch {}
    const device = value.device && typeof value.device === 'object' ? value.device : {};
    const coding = device.coding && typeof device.coding === 'object' ? device.coding : { mcp_running: Boolean(value.mcpRunning ?? value.status?.runtimeRunning), native_alive: Boolean(value.nativeAlive ?? value.status?.runtimeRunning), tunnel_running: Boolean(value.tunnelRunning ?? value.status?.tunnelRunning), tunnel_id: String(currentSettings.tunnelId || '') || null, ownership: 'device_id' };
    const plane = recoveryHost.recovery_plane || {};
    const status = value.status && typeof value.status === 'object'
      ? { ...value.status, activationClosure }
      : value.status;
    let epochStatus = null;
    try {
      const durableEpoch = this.fullCleanActivation?.current?.() || null;
      epochStatus = this.orchestrator.activationEpochStatus?.() || durableEpoch;
      if (epochStatus) {
        const durableOperationId = String(durableEpoch?.operation_id || '').trim() || null;
        const projectedOperationId = String(epochStatus?.operation_id || '').trim() || null;
        epochStatus = { ...epochStatus, operation_id: durableOperationId };
        if (projectedOperationId && projectedOperationId !== durableOperationId) {
          epochStatus = { ...epochStatus, admission_open: false, update_incomplete: true, error_code: 'ACTIVATION_OPERATION_MISMATCH' };
        }
      }
    } catch (error) {
      epochStatus = { state: 'UPDATE_INCOMPLETE', admission_open: false, update_incomplete: true, error_code: String(error?.code || 'ACTIVATION_EPOCH_STORE_INVALID') };
    }
    if (this.readyAdoptionBlocksAdmission()) {
      epochStatus = {
        ...epochStatus,
        state: 'UPDATE_INCOMPLETE',
        admission_open: false,
        update_incomplete: true,
        error_code: 'UPDATE_INCOMPLETE',
        error: this.readyAdoptionBlockDetails()
      };
    }
    const epochIncomplete = Boolean(epochStatus && (
      epochStatus.update_incomplete === true
      || (epochStatus.state && epochStatus.state !== 'READY')
      || (epochStatus.state === 'READY' && epochStatus.admission_open !== true)
    )) || this.bootstrapBlocksAdmission();
    // The aggregate runtime readiness contract is stricter than a durable
    // READY epoch: the current Recovery Host capability and exact connector
    // freshness/ACK receipt must also be current. Project that same truth onto every
    // IPC snapshot so callers cannot observe a green top-level fullyReady next
    // to recoveryHost.runtime.update_incomplete=true.
    const aggregateReady = recoveryHost.runtime?.fully_ready === true;
    const incomplete = epochIncomplete || !aggregateReady;
    if (status && (incomplete || status.fullyReady !== true)) status.fullyReady = false;
    if (Object.prototype.hasOwnProperty.call(value, 'fullyReady')
      && (incomplete || value.fullyReady !== true)) value.fullyReady = false;
    return { ...value, ...(status ? { status } : {}), activationClosure, activationEpoch: epochStatus, updateIncomplete: incomplete, device: { ...device, scope: 'current_device_only', registry: 'local', device_id: this.deviceIdentity.device_id, device_instance_id: this.deviceInstanceId, display_name: this.deviceIdentity.display_name, online: this.running, workspace: String(device.workspace || value.workspace || currentSettings.workspace || ''), coding, recovery: { host_running: this.running, mcp_running: plane.mcp?.state === 'healthy', tunnel_running: plane.tunnel?.state === 'healthy', tunnel_state: String(plane.tunnel?.state || 'unknown'), tunnel_id: String(currentSettings.recoveryTunnelId || '') || null }, git: device.git || { available: false, branch: null, head: null, head_short: null, dirty: null } }, recoveryHost };
  }

  async connectorPendingObservation(record) {
    const census = activationCensus(record) || {};
    const prior = census.runtime && typeof census.runtime === 'object' ? census.runtime : {};
    const state = readJson(this.paths.stateFile(), {});
    const health = await this.orchestrator.currentMcpHealth?.({ timeoutMs: 3_000 }).catch?.(() => null) || null;
    const priorDevice = prior.device && typeof prior.device === 'object' ? prior.device : {};
    const processCurrent = Boolean(health
      && health.ready === true
      && String(health.activation_epoch_id || '') === String(record.activation_epoch_id || '')
      && String(health.process_instance_id || '') === String(census.process_instance_id || '')
      && String(health.instance_id || health.server_instance_id || '') === String(census.server_instance_id || '')
      && String(health.workspace || '').toLowerCase() === String(prior.workspace || '').toLowerCase()
      && String(health.device_id || '').toLowerCase() === String(priorDevice.device_id || '').toLowerCase()
      && String(health.device_instance_id || '') === String(priorDevice.device_instance_id || '')
      && String(health.code_revision || '') === String(census.running_revision || '')
      && String(state.nativeInstanceId || '') === String(census.supervisor_instance_id || '')
      && String(state.nativeActivationEpochId || '') === String(record.activation_epoch_id || '')
      && String(state.nativeCodeRevision || '') === String(census.running_revision || '')
      && Number(state.nativePid || 0) > 0
      && this.processAlive(Number(state.nativePid)));
    const tunnelReceiptCurrent = Boolean(
      Number(state.tunnelPid || 0) === Number(census.tunnel_pid || 0)
      && String(state.tunnelInstanceId || '') === String(census.tunnel_instance_id || '')
      && String(state.tunnelActivationEpochId || '') === String(record.activation_epoch_id || '')
      && Number(state.tunnelPid || 0) > 0
      && this.processAlive(Number(state.tunnelPid)));
    let tunnelCurrent = Boolean(census.tunnel_health_verified === true && tunnelReceiptCurrent);
    let censusRefreshRequired = false;
    if (!tunnelCurrent
      && census.tunnel_health_verified !== true
      && tunnelReceiptCurrent
      && typeof this.orchestrator?.tunnel?.status === 'function') {
      try {
        tunnelCurrent = await this.orchestrator.tunnel.status(this.settings.load(), {
          activationEpochId: String(record.activation_epoch_id || '')
        }) === true;
        censusRefreshRequired = tunnelCurrent;
      } catch {
        tunnelCurrent = false;
      }
    }
    const contract = health && typeof this.orchestrator.connectorContractStatus === 'function'
      ? this.orchestrator.connectorContractStatus(
        health.tool_contract || null,
        health.connector_tool_discovery || null,
        health.connector_client_contact || null,
        health.connector_activation_bootstrap || null,
        health
      )
      : null;
    const runtime = {
      ...prior,
      mcpRunning: processCurrent,
      nativeAlive: processCurrent,
      tunnelRunning: tunnelCurrent,
      componentsReady: false,
      connectorReady: false,
      fullyReady: false,
      updateIncomplete: true,
      activationEpoch: this.orchestrator.activationEpochStatus?.() || prior.activationEpoch || null,
      ...(health?.tool_contract ? {
        toolContract: {
          schemaVersion: Number(health.tool_contract.schema_version || 0),
          profile: String(health.tool_contract.profile || ''),
          sha256: String(health.tool_contract.sha256 || '')
        }
      } : {}),
      ...(contract ? {
        connectorContractAcknowledgedSha256: contract.acknowledgedSha256 || null,
        connectorContractState: contract.contractState || 'UNAVAILABLE',
        connectorRefreshRequired: contract.refreshRequired === true,
        connectorAcknowledgementPending: contract.acknowledgementPending === true,
        connectorRediscovered: contract.rediscovered === true,
        connectorRediscoveredAt: contract.rediscoveredAt || null,
        connectorBootstrapObservedAt: contract.bootstrapObservedAt || null,
        connectorCompatibilityAcknowledged: contract.compatibilityAcknowledged === true,
        connectorCompatibilityAcknowledgedAt: contract.compatibilityAcknowledgedAt || null,
        connectorFreshnessMode: contract.contractState === 'CURRENT_COMPATIBLE_ACKNOWLEDGED'
          ? 'compatible_activation_bootstrap'
          : contract.contractState === 'CURRENT_ACKNOWLEDGED' ? 'current_process_discovery' : null
      } : {})
    };
    return {
      runtime,
      componentCurrent: processCurrent && tunnelCurrent,
      mcpCurrent: processCurrent,
      tunnelCurrent,
      censusRefreshRequired,
      componentRegression: Boolean(census.tunnel_health_verified === true && !tunnelCurrent),
      connectorEvidenceObserved: processCurrent
        && exactConnectorEvidenceObserved(health, census)
        && [
          'CHANGED_DISCOVERED_NEEDS_ACK',
          'CURRENT_ACKNOWLEDGED',
          'CHANGED_COMPATIBLE_NEEDS_ACK',
          'UNCHANGED_COMPATIBLE_NEEDS_ACK',
          'CURRENT_COMPATIBLE_ACKNOWLEDGED'
        ].includes(String(contract?.contractState || ''))
    };
  }

  cachedActivationSnapshot() {
    if (this.lastSupervisionProjectionSource !== 'activation_connector_pending_cache'
      || !this.lastSupervisionStatus
      || !this.lastSupervisionProjection) return null;
    const observedAtUnixMs = Number(this.lastSupervisionObservedAtUnixMs || 0);
    const ageMs = observedAtUnixMs > 0 ? Math.max(0, Date.now() - observedAtUnixMs) : null;
    return {
      ...this.lastSupervisionProjection,
      telemetryAvailable: true,
      signalStale: ageMs === null || ageMs > SUPERVISION_STATUS_STALE_MS,
      snapshotBusy: Boolean(this.supervisionInFlight),
      snapshotSource: 'activation_connector_pending_cache',
      snapshotObservedAtUnixMs: observedAtUnixMs || null,
      snapshotAgeMs: ageMs
    };
  }

  recordSupervisionStatus(value, { activationConnectorPending = false } = {}) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return this.lastSupervisionStatus;
    this.lastSupervisionStatus = value;
    this.lastSupervisionObservedAtUnixMs = Date.now();
    this.lastSupervisionProjectionSource = activationConnectorPending
      ? 'activation_connector_pending_cache'
      : 'recovery_host_supervision_cache';
    try {
      // Build the decorated read model once, on the supervisor's observation
      // path.  The IPC handler below only copies this object and updates
      // bounded telemetry fields; it never calls decorate/hostStatus again.
      this.lastSupervisionProjection = this.decorate({
        ...value,
        telemetryAvailable: true,
        signalStale: false,
        snapshotBusy: Boolean(this.supervisionInFlight),
        snapshotSource: this.lastSupervisionProjectionSource,
        snapshotObservedAtUnixMs: this.lastSupervisionObservedAtUnixMs,
        snapshotAgeMs: 0
      }, { preferCachedRuntime: true });
    } catch (error) {
      // Projection failure is an explicit unavailable read model, never a
      // reason to project stale raw runtime data as healthy/ready.
      this.lastSupervisionProjection = null;
      this.log?.warn?.(error.message, { stage: 'recovery-host-supervision-projection' });
    }
    return value;
  }

  cachedRuntimeSnapshot() {
    const observedAtUnixMs = Number(this.lastSupervisionObservedAtUnixMs || 0);
    const ageMs = observedAtUnixMs > 0 ? Math.max(0, Date.now() - observedAtUnixMs) : null;
    if (!this.lastSupervisionStatus || !this.lastSupervisionProjection) {
      return {
        mcpRunning: null,
        nativeAlive: null,
        tunnelRunning: null,
        componentsReady: false,
        connectorReady: false,
        fullyReady: false,
        telemetryAvailable: false,
        signalStale: true,
        snapshotBusy: Boolean(this.supervisionInFlight),
        snapshotSource: 'recovery_host_supervision_unavailable',
        snapshotObservedAtUnixMs: null,
        snapshotAgeMs: null,
        recoveryHost: null,
        updateIncomplete: true
      };
    }
    return {
      ...this.lastSupervisionProjection,
      telemetryAvailable: true,
      signalStale: ageMs === null || ageMs > SUPERVISION_STATUS_STALE_MS,
      snapshotBusy: Boolean(this.supervisionInFlight),
      snapshotSource: this.lastSupervisionProjectionSource,
      snapshotObservedAtUnixMs: observedAtUnixMs || null,
      snapshotAgeMs: ageMs
    };
  }

  handlers() {
    return {
      // Liveness must stay responsive while an unrelated authenticated read is
      // in flight.  Exact PID/instance/start-token identity is already bound
      // by the descriptor and is sufficient for the independent supervisor;
      // never run PowerShell identity or revision probes in this handler.
      'recovery.ping': async () => this.recoveryPingStatus(),
      // Operator status consumes the latest completed supervision read model.
      // Activation/mutation paths retain their own exact preflight and fresh
      // runtime snapshot authority; cached presentation is never mutation
      // authority.
      'recovery.status': async () => this.cachedHostStatus(),
      'code.activation_preflight': async (request) => this.activation.preflight(request),
      'code.activate_update': async (request) => {
        this.assertBootstrapMutationAllowed();
        // The production path intentionally delegates to FullCleanActivation
        // (and therefore may not call the ordinary mutation assertion), but it
        // still needs to retire a stale process-local READY-adoption guard when
        // a replacement epoch already exists.
        this.refreshReadyAdoptionGuard();
        // Production hosts route this action through FullCleanActivation,
        // which is the supported way to replace an invalid terminal READY
        // epoch.  Minimal legacy/unit hosts may lack that coordinator; keep
        // their component-scoped fallback fail-closed instead of mutating
        // runtime state under an unverified READY record.
        if (!(this.fullCleanActivation?.restart
          && typeof this.orchestrator?.completeActivationEpoch === 'function')) {
          this.assertReadyAdoptionMutationAllowed();
        }
        return this.activation.activate(request);
      },
      'code.activation_status': async (operationId) => this.activation.status(operationId),
      'client.register_ui_revision': async (registration) => {
        const result = await this.activation.registerUi(registration);
        this.resetUiRecoveryTracking('healthy');
        return result;
      },
      'client.suppress_ui_recovery': async (intent) => {
        this.assertBootstrapMutationAllowed();
        const result = this.activation.suppressUiRecovery(intent);
        this.resetUiRecoveryTracking('suppressed');
        return result;
      },
      'runtime.snapshot': async (options = {}) => this.decorate(await this.orchestrator.snapshot(options)),
      'runtime.lightweight_snapshot': async () => this.cachedRuntimeSnapshot(),
      'runtime.activation_epoch_status': async () => this.hostStatus().activation_epoch,
      'runtime.complete_activation_epoch': async (activationEpochId) => {
        this.assertBootstrapMutationAllowed();
        this.assertReadyAdoptionMutationAllowed();
        if (!this.fullCleanActivation || typeof this.orchestrator?.completeActivationEpoch !== 'function') {
          throw Object.assign(new Error('Full clean activation is unavailable for this runtime owner.'), { code: 'FULL_CLEAN_ACTIVATION_UNAVAILABLE' });
        }
        const id = String(activationEpochId || '');
        return this.decorate(await this.fullCleanActivation.finalize(id, await this.fullCleanActivation.finalCensus(id)));
      },
      'runtime.start': async (options = {}) => {
        this.assertBootstrapMutationAllowed();
        this.assertReadyAdoptionMutationAllowed();
        return this.decorate(await this.orchestrator.start(options));
      },
      'runtime.stop': async (options = {}) => {
        this.assertBootstrapMutationAllowed();
        // Stop is deliberately available while an invalid READY record is
        // blocked so the authenticated bootstrap/refresh handoff can quiesce
        // the old runtime.  Reconcile a retired guard when a replacement epoch
        // is already durable, without opening admission for the old epoch.
        this.refreshReadyAdoptionGuard();
        return this.decorate(await this.orchestrator.stop(options));
      },
      'runtime.restart': async (options = {}) => {
        this.assertBootstrapMutationAllowed();
        const soft = options?.automatic === true || options?.mode === 'soft_recovery';
        const refresh = options?.refresh === true || options?.mode === 'full_clean_refresh';
        this.assertReadyAdoptionMutationAllowed({ allowFullCleanRefresh: refresh });
        const result = soft
          ? await this.orchestrator.restart({ ...options, automatic: true, mode: 'soft_recovery' })
          : (this.fullCleanActivation?.restart && typeof this.orchestrator?.completeActivationEpoch === 'function'
            ? await this.fullCleanActivation.restart({
              ...options,
              // Code/revision activation is bound to the live accepted
              // closure.  The explicit npm-start process refresh is the only
              // exception: it carries no source authority and therefore must
              // be marked as a refresh all the way through the durable epoch.
              ...(refresh
                ? { refresh: true, mode: 'full_clean_refresh', sourceCheckpoint: null }
                : {
                  // Resolve and validate against the live closure even when a
                  // client omitted sourceCheckpoint.  A supplied value is not
                  // trusted unless it is byte-for-byte the current authority.
                  sourceCheckpoint: this._resolveRequestedFullCleanCheckpoint(options?.sourceCheckpoint)
                }),
              reason: options.reason || (refresh ? 'npm_start_refresh' : 'operator_restart')
            })
            : (() => {
              throw Object.assign(new Error('Operator restart requires the Recovery Host full-clean activation coordinator.'), {
                code: 'FULL_CLEAN_ACTIVATION_UNAVAILABLE'
              });
            })());
        return this.decorate(result);
      },
      'runtime.switch_workspace': async (workspace) => {
        this.assertBootstrapMutationAllowed();
        this.assertReadyAdoptionMutationAllowed();
        return this.decorate(await this.orchestrator.switchWorkspace(workspace));
      },
      'runtime.update_authorized_roots': async (roots) => {
        this.assertBootstrapMutationAllowed();
        this.assertReadyAdoptionMutationAllowed();
        return this.decorate(await this.orchestrator.updateAuthorizedRoots(roots));
      },
      'runtime.acknowledge_connector_contract': async () => {
        this.assertBootstrapMutationAllowed();
        this.assertReadyAdoptionMutationAllowed();
        return this.decorate(await this.orchestrator.acknowledgeConnectorContract());
      },
      'health.inspect': async () => this.healthService.inspect(),
      'health.repair': async () => {
        this.assertBootstrapMutationAllowed();
        this.assertReadyAdoptionMutationAllowed();
        return this.healthService.repair();
      },
      'logs.read': async (limit = 300) => this.log.read(Math.max(1, Math.min(500, Number(limit) || 300))),
      'logs.clear': async () => { this.assertBootstrapMutationAllowed(); this.assertReadyAdoptionMutationAllowed(); this.log.clear(); return true; }
    };
  }

  ensureAutoActivationStarted(epoch = null) {
    if (!this.running || this.bootstrapBlocksAdmission() || this.readyAdoptionBlocksAdmission()) return false;
    if (epoch && (epoch.state !== 'READY' || epoch.admission_state !== 'OPEN')) return false;
    let alreadyRunning = false;
    try { alreadyRunning = this.autoActivation?.status?.()?.running === true; } catch {}
    if (alreadyRunning) return true;
    if (typeof this.autoActivation?.start !== 'function') return false;
    this.autoActivation.start();
    return true;
  }

  async superviseOnce() {
    if (!this.running || this.handoffStarted) return this.lastSupervisionStatus;
    if (this.supervisionInFlight) return this.supervisionInFlight;
    const operation = (async () => {
      // A full-clean coordinator can create a replacement epoch while this
      // Recovery Host process remains alive.  Retire only the old process-local
      // diagnostic before deriving admissionBlocked; the durable new epoch's
      // own state and census still control all subsequent supervision.
      this.refreshReadyAdoptionGuard();
      let runtime = null;
      let epoch = null;
      try {
        epoch = typeof this.fullCleanActivation.enforceCurrentExpiry === 'function'
          ? this.fullCleanActivation.enforceCurrentExpiry('recovery_host_supervise')
          : this.fullCleanActivation.current?.();
      } catch (error) {
        if (String(error?.code || '') === 'ACTIVATION_REQUEST_EXPIRED') {
          try { epoch = this.fullCleanActivation.current?.(); }
          catch (readError) {
            this.log.error(readError.message, { stage: 'recovery-host-activation-epoch-expiry-read', code: readError?.code || '' });
            return this.lastSupervisionStatus;
          }
          this.log.warn('Recovery Host terminalized an expired activation epoch during supervision; explicit refresh remains available.', {
            activationEpochId: epoch?.activation_epoch_id || null
          });
        } else {
          this.log.error(error.message, { stage: 'recovery-host-activation-epoch-read', code: error?.code || '' });
          return this.lastSupervisionStatus;
        }
      }
      const admissionBlocked = this.readyAdoptionBlocksAdmission()
        || Boolean(epoch && epoch.state !== 'READY');
      const connectorPending = activationAwaitsTunnelOrConnector(epoch);
      let pendingObservation = null;
      try {
        // During a full-clean transaction the coordinator is the sole owner of
        // component mutation.  The normal watchdog must not restart MCP/Tunnel
        // (or consume a supervisor ticket) while the epoch is assembling.
        // Any non-READY durable epoch (including FAILED/expired epochs) keeps
        // admission closed.  The ordinary watchdog must not mutate MCP,
        // Tunnel, Recovery Plane, or consume restart tickets in that state;
        // only the explicit activation coordinator may advance it.
        pendingObservation = connectorPending
          ? await this.connectorPendingObservation(epoch)
          : null;
        runtime = admissionBlocked
          ? (pendingObservation?.runtime || await this.orchestrator.lightweightSnapshot())
          : await this.orchestrator.supervise();
        this.recordSupervisionStatus(runtime, {
          activationConnectorPending: connectorPending
        });
      } catch (error) {
        this.log.error(error.message, { stage: 'recovery-host-supervise' });
      }
      const shouldRunFinalCensus = !connectorPending
        || pendingObservation?.mcpCurrent !== true
        || pendingObservation?.componentRegression === true
        || pendingObservation?.censusRefreshRequired === true
        || pendingObservation?.connectorEvidenceObserved === true;
      if (shouldRunFinalCensus
        && epoch
        && ['STARTING', 'VERIFYING', 'HANDOFF', 'FROZEN', 'STOPPING', 'ADMISSION_CLOSED', 'PREPARING'].includes(epoch.state)) {
        try {
          const census = await this.fullCleanActivation.finalCensus(epoch.activation_epoch_id, {
            expectedOldInstanceId: this.replacement?.expectedOldInstanceId || '',
            // Admission is still CLOSED, so no ordinary tool can mutate the
            // canonical ledger between a verified pending census and this
            // watchdog recheck. The coordinator still revalidates every live
            // process/component/connector identity; it only reuses the exact
            // durable projection receipt to avoid a second multi-minute ledger
            // rebuild inside the same bounded activation epoch.
            reusePendingProjection: connectorPending === true
          });
          if (census.pass) {
            // finalize() deliberately performs its own independent live census
            // and may reuse only the exact durable admission-closed projection
            // receipt. Persist this passing candidate before crossing that
            // boundary; otherwise finalize() can read the previous connector-
            // pending receipt and terminalize an otherwise healthy epoch as
            // stale/incomplete. recordPendingCensus never opens admission.
            this.fullCleanActivation.recordPendingCensus(epoch.activation_epoch_id, census);
            const completed = await this.fullCleanActivation.finalize(epoch.activation_epoch_id, census);
            this.recordSupervisionStatus({ ...(this.lastSupervisionStatus || {}), fullCleanActivation: completed }, {
              activationConnectorPending: connectorPending
            });
            const finalizedEpoch = this.activationEpochStore.current();
            this.recordBootstrapEpoch(finalizedEpoch, {
              replacement_host_instance_id: this.instanceId,
              replacement_host_pid: process.pid
            });
            epoch = finalizedEpoch;
          } else if (typeof this.fullCleanActivation.recordPendingCensus === 'function') {
            // A transient cold-start probe can be negative even though the
            // exact Tunnel/Recovery processes become healthy a few seconds
            // later.  Persist the refreshed evidence so subsequent watchdog
            // ticks and status readers no longer inherit the first stale
            // census. Admission remains closed until the full census passes.
            this.fullCleanActivation.recordPendingCensus(epoch.activation_epoch_id, census);
            if (census.runtime && typeof census.runtime === 'object') {
              this.recordSupervisionStatus({
                ...census.runtime,
                tunnelRunning: census.tunnel_health_verified === true
              }, { activationConnectorPending: connectorPending });
            }
            this.lastRecoveryPlaneStatus = this.recoveryPlane?.lastStatus || this.lastRecoveryPlaneStatus;
            this.recordBootstrapEpoch(this.activationEpochStore.current(), {
              replacement_host_instance_id: this.instanceId,
              replacement_host_pid: process.pid
            });
          }
        } catch (error) {
          this.log.warn(error.message, { stage: 'full-clean-activation-census', code: error?.code || '' });
          this.recordBootstrapEpoch(this.activationEpochStore.current(), {
            replacement_host_instance_id: this.instanceId,
            replacement_host_pid: process.pid
          });
        }
      }
      // Recovery plane and UI repair are also component mutations.  They are
      // intentionally suppressed while admission is blocked; the replacement
      // coordinator performs the one required start/observation sequence.
      if (!admissionBlocked) {
        await this.ensureRecoveryPlane();
        await this.superviseElectronUi();
      }
      this.ensureAutoActivationStarted(epoch);
      return runtime;
    })();
    this.supervisionInFlight = operation;
    try {
      return await operation;
    } finally {
      if (this.supervisionInFlight === operation) this.supervisionInFlight = null;
    }
  }

  async drainSupervisionForHandoff() {
    const operation = this.supervisionInFlight;
    if (!operation) return true;
    let timer = null;
    const timeout = new Promise((_, reject) => {
      timer = setTimeout(() => reject(Object.assign(
        new Error('Recovery Host supervision did not quiesce before replacement handoff.'),
        { code: 'RECOVERY_SUPERVISION_BUSY' }
      )), Math.max(100, Number(this.handoffSupervisionDrainMs) || HANDOFF_SUPERVISION_DRAIN_MS));
      timer.unref?.();
    });
    try {
      await Promise.race([operation, timeout]);
      return true;
    } finally {
      if (timer) clearTimeout(timer);
    }
  }

  async ensureRecoveryPlane(options = {}) {
    try {
      const current = this.settings.load();
      const authToken = await this.orchestrator.ensureToken();
      const runtimeApiKey = this.secrets.get('runtimeApiKey');
      if (options.legacyMigrationPlan?.required && typeof this.recoveryPlane.applyLegacyOwnershipMigration === 'function') {
        await this.recoveryPlane.applyLegacyOwnershipMigration(options.legacyMigrationPlan);
      }
      this.lastRecoveryPlaneStatus = await this.recoveryPlane.ensure(current, {
        authToken,
        runtimeApiKey,
        activationEpochId: this.orchestrator.activationEpochId || undefined
      });
    } catch (error) {
      this.lastRecoveryPlaneStatus = { state: 'unavailable', error_code: String(error?.code || 'RECOVERY_PLANE_UNAVAILABLE'), checked_at: new Date().toISOString() };
      this.log.error(error.message, { stage: 'recovery-plane-supervise', code: this.lastRecoveryPlaneStatus.error_code });
    }
    return this.lastRecoveryPlaneStatus;
  }

  async start() {
    if (this.running) return this.hostStatus();
    // A durable non-terminal activation is authoritative even when a process
    // replacement was launched without argv (crash, login/startup, or manual
    // service restart).  Never silently enter normal runtime ownership while
    // such an epoch is active: resume that exact epoch or fail closed.
    let durableEpoch = null;
    try { durableEpoch = this.activationEpochStore.current(); }
    catch (error) {
      this.log?.error?.(error.message, { stage: 'recovery-host-activation-epoch-load', code: error?.code || '' });
      throw error;
    }
    // Recompute this process-local admission guard from the current durable
    // record on every start.  It is intentionally not persisted or inferred
    // from a previous host instance.
    this.readyAdoptionBlocked = null;
    let bootstrapPlan = null;
    try { bootstrapPlan = await this.prepareBootstrapStart(durableEpoch); }
    catch (error) {
      this.recordBootstrapFailure(error, durableEpoch);
      throw error;
    }
    if (bootstrapPlan && Object.prototype.hasOwnProperty.call(bootstrapPlan, 'durableEpoch')) {
      durableEpoch = bootstrapPlan.durableEpoch;
    }
    let replacementEpochId = String(this.replacement?.activationEpochId || '').trim();
    let fullCleanReplacement = Boolean(replacementEpochId);
    let recoveredFromDurableEpoch = false;
    // A FAILED epoch is terminal and keeps admission closed, but it must not
    // brick the Recovery Host itself.  Keep the control plane alive so the
    // operator can submit a new explicit full-clean activation.  Component
    // startup/recovery remains suppressed below until that new epoch reaches
    // READY; a failed transaction must never be auto-healed by the watchdog.
    let failedEpochBlocked = Boolean(!bootstrapPlan && !fullCleanReplacement && durableEpoch && durableEpoch.state === 'FAILED');
    let readyEpochBlocked = false;
    if (failedEpochBlocked) {
      this.log?.warn?.('Recovery Host is serving control-plane IPC with a failed activation epoch; explicit full-clean activation is required.', {
        activationEpochId: durableEpoch.activation_epoch_id
      });
    }
    if (!fullCleanReplacement && durableEpoch && ACTIVE_STATES.has(durableEpoch.state)) {
      const resumableReplacementStates = new Set(['HANDOFF', 'STARTING', 'VERIFYING']);
      if (!resumableReplacementStates.has(String(durableEpoch.state || ''))) {
        const error = Object.assign(new Error('Activation crashed before a durable Recovery Host handoff and cannot skip directly to replacement startup.'), {
          code: 'ACTIVATION_EPOCH_RESUME_UNSAFE',
          details: {
            activation_epoch_id: durableEpoch.activation_epoch_id,
            operation_id: durableEpoch.operation_id || null,
            state: durableEpoch.state,
            process_mutated: durableEpoch.state === 'FROZEN' || durableEpoch.state === 'STOPPING'
          }
        });
        try { durableEpoch = this.activationEpochStore.fail(durableEpoch.activation_epoch_id, error); }
        catch (persistError) {
          this.log?.error?.(persistError.message, { stage: 'recovery-host-unsafe-resume-failure-persist', code: persistError?.code || '' });
        }
        this.recordBootstrapFailure(error, durableEpoch);
        throw error;
      }
      const durableExpiry = Number(durableEpoch.expires_at_unix_ms || durableEpoch.metadata?.expires_at_unix_ms || 0);
      if (durableExpiry > 0 && Date.now() >= durableExpiry) {
        const error = Object.assign(new Error('Activation request expired before Recovery Host recovery.'), {
          code: 'ACTIVATION_REQUEST_EXPIRED',
          details: { activation_epoch_id: durableEpoch.activation_epoch_id, expires_at_unix_ms: durableExpiry, process_mutated: false }
        });
        const expiredEpochId = durableEpoch.activation_epoch_id;
        try { durableEpoch = this.activationEpochStore.fail(expiredEpochId, error); } catch (persistError) {
          const terminal = this.activationEpochStore.current();
          if (String(persistError?.code || '') === 'ACTIVATION_REQUEST_EXPIRED'
            && terminal?.activation_epoch_id === expiredEpochId
            && terminal?.state === 'FAILED'
            && terminal?.error?.code === 'ACTIVATION_REQUEST_EXPIRED') {
            durableEpoch = terminal;
          } else {
            this.log?.error?.(persistError.message, { stage: 'recovery-host-expired-epoch-persist', code: persistError?.code || '' });
            throw persistError;
          }
        }
        failedEpochBlocked = true;
        this.log?.warn?.('Recovery Host terminalized an expired activation epoch and kept control-plane IPC available for an explicit refresh.', {
          activationEpochId: expiredEpochId
        });
      } else {
        const boundOldHostId = String(durableEpoch.component_evidence?.recovery_host?.instance_id || '').trim();
        if (!boundOldHostId) {
          throw Object.assign(new Error('Active activation epoch has no bound old Recovery Host identity.'), {
            code: 'ACTIVATION_EPOCH_OLD_INSTANCE_REQUIRED',
            details: { activation_epoch_id: durableEpoch.activation_epoch_id }
          });
        }
        this.replacement = {
          ...(this.replacement || {}),
          activationEpochId: durableEpoch.activation_epoch_id,
          expectedOldInstanceId: boundOldHostId,
          operationId: durableEpoch.operation_id || undefined,
          expiresAtUnixMs: Number(durableEpoch.expires_at_unix_ms || durableEpoch.metadata?.expires_at_unix_ms || 0) || 0
        };
        replacementEpochId = durableEpoch.activation_epoch_id;
        fullCleanReplacement = true;
        recoveredFromDurableEpoch = true;
        this.orchestrator.setActivationEpoch?.(replacementEpochId);
        this.recoveryPlane?.setActivationEpoch?.(replacementEpochId);
        this.log?.warn?.('Resuming an active full-clean activation from the durable epoch store.', {
          activationEpochId: replacementEpochId,
          previousHostInstanceId: boundOldHostId
        });
      }
    } else if (!fullCleanReplacement && durableEpoch && durableEpoch.state === 'READY') {
      // A READY epoch remains the current activation identity across an
      // ordinary host process restart only when its persisted census contains
      // a valid exact current-process discovery or guarded compatibility
      // bootstrap receipt. Keep malformed terminal records untouched, but
      // retain the authenticated Recovery control plane so an explicit
      // full-clean refresh can replace them. No component/gateway admission is
      // opened while this process-local guard is active.
      const readyConnectorProof = validatePersistedReadyConnectorProof(durableEpoch);
      if (!readyConnectorProof.valid) {
        readyEpochBlocked = true;
        this.readyAdoptionBlocked = readyConnectorProof;
        this.log?.warn?.('Durable READY activation lacks strict current-process connector discovery proof; keeping only the authenticated control plane available for an explicit full-clean refresh.', {
          stage: 'recovery-host-ready-epoch-adoption',
          activationEpochId: durableEpoch.activation_epoch_id,
          reasons: readyConnectorProof.reasons
        });
      } else {
        this.readyAdoptionBlocked = null;
        this.orchestrator.setActivationEpoch?.(durableEpoch.activation_epoch_id);
        this.recoveryPlane?.setActivationEpoch?.(durableEpoch.activation_epoch_id);
      }
    }
    const persistReplacementFailure = (error) => {
      if (!replacementEpochId) return;
      // A duplicate launcher that never acquired Recovery Host ownership must
      // not terminalize the epoch owned by the already-running replacement.
      // RECOVERY_HOST_ALREADY_RUNNING is an ownership refusal for the
      // contender, not a failure of the durable activation transaction.
      if (String(error?.code || '') === 'RECOVERY_HOST_ALREADY_RUNNING') return;
      try {
        const current = this.activationEpochStore.current();
        if (!current || current.activation_epoch_id !== replacementEpochId || current.state === 'READY') return;
        // Keep the durable activation gate closed whenever replacement startup
        // cannot complete.  The operation may already have been terminalized
        // by FullCleanActivation; store.fail() is idempotent for that case.
        this.activationEpochStore.fail(replacementEpochId, error);
      } catch (persistError) {
        if (String(persistError?.code || '') !== 'ACTIVATION_EPOCH_TERMINAL') {
          this.log?.error?.(persistError.message, {
            stage: 'recovery-host-replacement-failure-persist',
            activationEpochId: replacementEpochId,
            code: persistError?.code || ''
          });
        }
      }
    };
    if (fullCleanReplacement) {
      // Replacement argv is untrusted routing metadata.  Bind it to the
      // current durable record before acquiring ownership or starting any
      // child process, and recover the authoritative expiry from disk (the
      // launcher intentionally does not put secrets/deadlines in argv).
      if (!durableEpoch || String(durableEpoch.activation_epoch_id || '') !== replacementEpochId) {
        const error = Object.assign(new Error('Replacement activation epoch is not the current durable activation.'), {
          code: 'ACTIVATION_EPOCH_NOT_CURRENT',
          details: { activation_epoch_id: replacementEpochId, durable_activation_epoch_id: durableEpoch?.activation_epoch_id || null }
        });
        persistReplacementFailure(error);
        throw error;
      }
      if (durableEpoch.state === 'FAILED') {
        const error = Object.assign(new Error('Replacement activation epoch is failed and remains admission-closed.'), {
          code: 'UPDATE_INCOMPLETE',
          details: { activation_epoch_id: replacementEpochId, state: durableEpoch.state, error_code: durableEpoch.error?.code || null }
        });
        persistReplacementFailure(error);
        throw error;
      }
      const durableOperationId = String(durableEpoch.operation_id || '').trim();
      const suppliedOperationId = String(this.replacement?.operationId || '').trim();
      if (suppliedOperationId && durableOperationId && suppliedOperationId !== durableOperationId) {
        const error = Object.assign(new Error('Replacement operation does not match the durable activation.'), {
          code: 'ACTIVATION_OPERATION_MISMATCH',
          details: { activation_epoch_id: replacementEpochId, supplied_operation_id: suppliedOperationId, durable_operation_id: durableOperationId }
        });
        persistReplacementFailure(error);
        throw error;
      }
      const boundOldHostId = String(durableEpoch.component_evidence?.recovery_host?.instance_id || '').trim();
      const suppliedOldHostId = String(this.replacement?.expectedOldInstanceId || '').trim();
      if (boundOldHostId && suppliedOldHostId && boundOldHostId !== suppliedOldHostId) {
        const error = Object.assign(new Error('Replacement target does not match the durable old Recovery Host identity.'), {
          code: 'RECOVERY_REPLACEMENT_TARGET_CHANGED',
          details: { activation_epoch_id: replacementEpochId, supplied_old_instance_id: suppliedOldHostId, durable_old_instance_id: boundOldHostId }
        });
        persistReplacementFailure(error);
        throw error;
      }
      const hasBoundEvidence = durableEpoch.component_evidence && typeof durableEpoch.component_evidence === 'object';
      if (ACTIVE_STATES.has(durableEpoch.state) && hasBoundEvidence && !boundOldHostId && !suppliedOldHostId) {
        const error = Object.assign(new Error('Active replacement has no bound old Recovery Host identity.'), {
          code: 'ACTIVATION_EPOCH_OLD_INSTANCE_REQUIRED',
          details: { activation_epoch_id: replacementEpochId }
        });
        persistReplacementFailure(error);
        throw error;
      }
      this.replacement = {
        ...(this.replacement || {}),
        activationEpochId: replacementEpochId,
        operationId: suppliedOperationId || durableOperationId || undefined,
        expectedOldInstanceId: suppliedOldHostId || boundOldHostId || undefined,
        expiresAtUnixMs: Number(durableEpoch.expires_at_unix_ms || durableEpoch.metadata?.expires_at_unix_ms || 0) || 0
      };
      const replacementExpiry = Number(this.replacement.expiresAtUnixMs || 0);
      if (ACTIVE_STATES.has(durableEpoch.state) && replacementExpiry > 0 && Date.now() >= replacementExpiry) {
        const error = Object.assign(new Error('Replacement activation request expired before Recovery Host ownership handoff.'), {
          code: 'ACTIVATION_REQUEST_EXPIRED',
          details: { activation_epoch_id: replacementEpochId, expires_at_unix_ms: replacementExpiry, process_mutated: false }
        });
        persistReplacementFailure(error);
        throw error;
      }
    }
    try {
      let observedSelf;
      try { observedSelf = await this.processIdentityObserver(process.pid); }
      catch (error) {
        throw Object.assign(new Error('Recovery Host process identity is unavailable before runtime ownership.'), {
          code: 'RECOVERY_PROCESS_IDENTITY_UNVERIFIED',
          cause: error
        });
      }
      if (observedSelf?.state !== 'live') {
        throw Object.assign(new Error('Recovery Host process identity is unavailable before runtime ownership.'), {
          code: 'RECOVERY_PROCESS_IDENTITY_UNVERIFIED'
        });
      }
      try {
        this.processIdentity = processIdentityFrom({
          pid: process.pid,
          process_start_token: observedSelf.process_start_token
        });
      } catch (error) {
        throw Object.assign(new Error('Recovery Host process identity is unavailable before runtime ownership.'), {
          code: 'RECOVERY_PROCESS_IDENTITY_UNVERIFIED',
          cause: error
        });
      }
      if (this.replacement?.expectedOldInstanceId) {
        const currentOwner = readLock(this.paths.recoveryHostLockFile());
        if (currentOwner
          && isProcessAlive(currentOwner.pid)
          && String(currentOwner.instance_id || '') !== String(this.replacement.expectedOldInstanceId)) {
          throw Object.assign(new Error('A Recovery Host already owns the active replacement epoch.'), {
            code: 'RECOVERY_HOST_ALREADY_RUNNING',
            ownerPid: Number(currentOwner.pid),
            ownerInstanceId: String(currentOwner.instance_id || '')
          });
        }
        await waitForReplacementLockRelease(this.paths, this.replacement.expectedOldInstanceId);
      }
      acquireRecoveryHostLock(this.paths, this.instanceId);
    } catch (error) {
      persistReplacementFailure(error);
      throw error;
    }
    this.ownsLock = true;
    try {
      // A malformed/legacy READY epoch must not expose the execution gateway
      // while its strict connector proof is absent.  The Recovery IPC server
      // below remains available so an operator can submit an explicit
      // full-clean refresh that creates a replacement epoch.
      if (!readyEpochBlocked) await this.gateway.start();
      this.ipcServer = this.ipcServerFactory({
        paths: this.paths,
        handlers: this.handlers(),
        log: this.log,
        instanceId: this.instanceId,
        startedAt: this.startedAt,
        deviceIdentity: this.deviceIdentity,
        deviceInstanceId: this.deviceInstanceId,
        activationEpochId: readyEpochBlocked
          ? ''
          : this.orchestrator.activationEpochId || this.fullCleanActivation.current?.()?.activation_epoch_id || '',
        processIdentityObserver: async (pid) => {
          if (Number(pid) === Number(process.pid) && this.processIdentity) {
            return { state: 'live', ...this.processIdentity };
          }
          return this.processIdentityObserver(pid);
        }
      });
      await this.ipcServer.start();
      this.running = true;
      if (bootstrapPlan?.requiresNewEpoch) {
        this.bootstrapActivation = { state: 'started', operation_id: bootstrapPlan.operationId };
        writeBootstrapResult(this.paths, {
          operation_id: bootstrapPlan.operationId,
          state: 'started',
          result: {
            bootstrap_host_pid: process.pid,
            bootstrap_host_instance_id: this.instanceId,
            admission_open: false,
            fully_ready: false
          }
        });
        let activationResult;
        try {
          activationResult = await this.fullCleanActivation.restart({
            operationId: bootstrapPlan.operationId,
            component: 'recovery_host',
            expectedDiskRevision: bootstrapPlan.expectedRevision,
            ...(this.bootstrap.refresh === true
              ? { refresh: true, mode: 'full_clean_refresh', sourceCheckpoint: null }
              : { sourceCheckpoint: this.bootstrap.source_checkpoint }),
            allowAcceptancePending: this.bootstrap.allow_acceptance_pending === true,
            expiresAtUnixMs: bootstrapPlan.expiresAtUnixMs,
            reason: this.bootstrap.refresh === true
              ? 'npm_start_refresh_bootstrap'
              : 'recovery_host_bootstrap'
          });
        } catch (error) {
          this.recordBootstrapFailure(error, this.activationEpochStore.current());
          throw error;
        }
        const createdEpoch = this.activationEpochStore.current();
        if (!createdEpoch || String(createdEpoch.operation_id || '') !== bootstrapPlan.operationId) {
          const error = Object.assign(new Error('Bootstrap activation did not create the requested durable epoch.'), {
            code: 'RECOVERY_BOOTSTRAP_EPOCH_UNAVAILABLE'
          });
          this.recordBootstrapFailure(error, createdEpoch);
          throw error;
        }
        this.recordBootstrapEpoch(createdEpoch, {
          bootstrap_host_instance_id: this.instanceId,
          coordinator_result_state: activationResult?.state || activationResult?.activation_state || null
        });
        // FullCleanActivation scheduled this transitional host to hand off to a
        // final Recovery Host. Do not start ordinary watchdog/auto-start paths.
        return this.hostStatus();
      }
      if (fullCleanReplacement) {
        const continued = await this.fullCleanActivation.continueReplacement({
          activationEpochId: this.replacement.activationEpochId,
          expectedOldInstanceId: this.replacement.expectedOldInstanceId,
          expiresAtUnixMs: this.replacement.expiresAtUnixMs
        });
        if (continued?.census?.runtime) {
          this.recordSupervisionStatus({
            ...continued.census.runtime,
            tunnelRunning: continued.census.tunnel_health_verified === true
          });
        }
        this.lastRecoveryPlaneStatus = this.recoveryPlane?.lastStatus || this.lastRecoveryPlaneStatus;
        this.recordBootstrapEpoch(this.activationEpochStore.current(), {
          replacement_host_instance_id: this.instanceId,
          replacement_host_pid: process.pid
        });
      }
      let primaryLegacyMigration = { required: false };
      let recoveryLegacyMigration = { required: false };
      if (!fullCleanReplacement && this.replacement?.operationId) {
        this.activation.verifyRecoveryReplacement(this.replacement.operationId);
        const current = this.settings.load();
        const recoveryMigrationSupported = typeof this.recoveryPlane.preflightLegacyOwnershipMigration === 'function'
          && typeof this.orchestrator.ensureToken === 'function';
        const authToken = recoveryMigrationSupported ? await this.orchestrator.ensureToken() : '';
        [primaryLegacyMigration, recoveryLegacyMigration] = await Promise.all([
          typeof this.orchestrator.preflightLegacyDeviceMigration === 'function'
            ? this.orchestrator.preflightLegacyDeviceMigration()
            : Promise.resolve({ required: false }),
          recoveryMigrationSupported
            ? this.recoveryPlane.preflightLegacyOwnershipMigration(current, authToken)
            : Promise.resolve({ required: false })
        ]);
        await this.activation.completeRecoveryReplacement(
          this.replacement.operationId,
          this.replacement.expectedOldInstanceId,
          {
            primaryLegacyMigrationRequired: primaryLegacyMigration.required === true,
            recoveryLegacyMigrationRequired: recoveryLegacyMigration.required === true
          }
        );
      }

      let primaryMigrationFailed = false;
      if (primaryLegacyMigration.required && typeof this.orchestrator.applyLegacyDeviceMigration === 'function') {
        try {
          await this.orchestrator.applyLegacyDeviceMigration(primaryLegacyMigration);
        } catch (error) {
          primaryMigrationFailed = true;
          this.log.error(error.message, { stage: 'legacy-primary-device-migration', code: error?.code || '' });
        }
      }
      if (!fullCleanReplacement && !failedEpochBlocked && !readyEpochBlocked) {
        await this.ensureRecoveryPlane({ legacyMigrationPlan: recoveryLegacyMigration });
      }
      this.supervisionTimer = setInterval(() => { this.superviseOnce(); }, SUPERVISION_INTERVAL_MS);
      this.supervisionTimer.unref();
      this.log.info('Recovery Host đã sở hữu Coding runtime, watchdog và local gateway', {
        hostPid: process.pid,
        hostInstanceId: this.instanceId
      });
      const current = this.settings.load();
      if (!fullCleanReplacement && !failedEpochBlocked && !readyEpochBlocked && !recoveredFromDurableEpoch && !primaryMigrationFailed && current.autoStartServices && !this.orchestrator.isManuallyStopped()) {
        const observed = await this.orchestrator.lightweightSnapshot().catch(() => null);
        this.recordSupervisionStatus(observed);
        if (!observed?.nativeAlive && !observed?.tunnelRunning) {
          this.orchestrator.start({ automatic: true }).catch((error) => {
            this.log.error(error.message, { stage: 'recovery-host-auto-start' });
          });
        }
      }
      const postStartEpoch = this.fullCleanActivation.current?.();
      this.ensureAutoActivationStarted(postStartEpoch);
      return this.hostStatus();
    } catch (error) {
      const beforeCleanupEpoch = this.activationEpochStore.current();
      const terminalReady = beforeCleanupEpoch?.state === 'READY';
      this.autoActivation?.stop?.();
      if (!terminalReady) {
        await this.ipcServer?.stop().catch(() => false);
        await this.gateway?.stop().catch(() => false);
        if (this.ownsLock) releaseRecoveryHostLock(this.paths, this.instanceId);
        this.ownsLock = false;
      }
      persistReplacementFailure(error);
      const terminalEpoch = this.activationEpochStore.current();
      if (terminalReady || terminalEpoch?.state === 'READY') {
        // A READY epoch from an older operation must not overwrite a failed
        // bootstrap receipt as `completed`: that terminal receipt is immutable
        // evidence for the attempted operation.  Preserve it and retain the
        // envelope until the guarded reconciliation below proves the current
        // host/epoch/ledger relationship.
        this.bootstrapActivation = {
          state: 'receipt_conflict',
          operation_id: terminalEpoch.operation_id || null,
          activation_epoch_id: terminalEpoch.activation_epoch_id || null,
          error_code: error?.code || 'RECOVERY_BOOTSTRAP_RESULT_FAILED'
        };
        try {
          const reconciliation = await this.reconcileTerminalBootstrapReceipt(terminalEpoch);
          this.log?.warn?.('Reconciled a terminal failed bootstrap receipt against the current durable activation epoch.', {
            attemptedOperationId: reconciliation.attempted_operation_id,
            activationEpochId: reconciliation.activation_epoch_id,
            censusFingerprint: reconciliation.census_fingerprint || null
          });
        } catch (reconciliationError) {
          // Keep the host alive for read-only status, but preserve admission
          // closure.  A failed/missing receipt, identity drift, or non-quiescent
          // ledger must never be converted into a permissive runtime owner.
          this.log?.error?.(reconciliationError.message, {
            stage: 'recovery-bootstrap-terminal-reconciliation',
            code: reconciliationError?.code || 'RECOVERY_BOOTSTRAP_RECONCILIATION_FAILED'
          });
        }
        return this.hostStatus();
      }
      this.recordBootstrapFailure(error, terminalEpoch);
      this.recordBootstrapEpoch(terminalEpoch, {
        replacement_host_instance_id: this.instanceId,
        replacement_host_pid: process.pid
      });
      throw error;
    }
  }

  scheduleRecoveryHandoff(operationId) {
    if (this.handoffStarted) return;
    this.handoffStarted = true;
    const timer = setTimeout(() => {
      this.performRecoveryHandoff(operationId).catch((error) => {
        this.log.error(error.message, { stage: 'recovery-host-handoff-unhandled', operationId });
        this.exitProcess(1);
      });
    }, 100);
    timer.unref();
  }

  scheduleFullCleanHandoff(activationEpochId, details = {}) {
    if (this.handoffStarted) return;
    this.handoffStarted = true;
    const timer = setTimeout(() => {
      this.performFullCleanHandoff(activationEpochId, details).catch((error) => {
        this.log.error(error.message, { stage: 'full-clean-handoff-unhandled', activationEpochId, code: error?.code || '' });
        try { this.activationEpochStore.fail(activationEpochId, error); } catch {}
        this.exitProcess(1);
      });
    }, 100);
    timer.unref?.();
  }

  async performFullCleanHandoff(activationEpochId, details = {}) {
    try {
      await this.drainSupervisionForHandoff();
      // The coordinator already fenced and stopped primary/recovery children;
      // stop again defensively (idempotently) before releasing host ownership.
      await this.orchestrator.stop({ manual: false, fullClean: true, activationEpochId }).catch(() => false);
      if (typeof this.recoveryPlane?.stop === 'function') await this.recoveryPlane.stop().catch(() => false);
      await this.stop();
      this.log.info('Recovery Host released ownership for a full clean activation replacement', {
        activationEpochId,
        operationId: details.operationId || null
      });
      this.exitProcess(0);
    } catch (error) {
      try { this.activationEpochStore.fail(activationEpochId, error); } catch {}
      this.log.error(error.message, { stage: 'full-clean-handoff', activationEpochId, code: error?.code || '' });
      this.exitProcess(1);
    }
  }

  async performRecoveryHandoff(operationId) {
    try {
      await this.drainSupervisionForHandoff();
    } catch (error) {
      await this.orchestrator.cancelCodeActivation(operationId).catch(() => false);
      this.activation.actions.finish(operationId, 'failed', null, {
        code: String(error?.code || 'RECOVERY_SUPERVISION_BUSY'),
        message: 'Recovery Host supervision was still mutating runtime state; replacement handoff was not allowed to release ownership.'
      });
      this.handoffStarted = false;
      this.log.error(error.message, { stage: 'recovery-host-handoff-quiesce', operationId, code: error?.code || '' });
      return;
    }
    await this.stop();
    const deadline = Date.now() + this.replacementWaitMs;
    while (Date.now() < deadline) {
      const record = this.activation.actions.get(operationId);
      if (record?.state === 'completed') {
        this.exitProcess(0);
        return;
      }
      if (record && ['failed', 'refused'].includes(record.state)) break;
      await wait(100);
    }
    try {
      await this.start();
      await this.orchestrator.cancelCodeActivation(operationId).catch(() => false);
      this.activation.actions.finish(operationId, 'failed', null, {
        code: 'RECOVERY_REPLACEMENT_FAILED',
        message: 'Replacement Recovery Host did not become healthy; the previous host resumed ownership.'
      });
      this.handoffStarted = false;
      this.log.error('Recovery Host replacement failed; previous host resumed ownership', { operationId });
    } catch (error) {
      this.log.error(error.message, { stage: 'recovery-host-handoff-rollback', operationId });
      this.exitProcess(1);
    }
  }

  async stop() {
    this.autoActivation?.stop?.();
    if (this.supervisionTimer) clearInterval(this.supervisionTimer);
    this.supervisionTimer = null;
    this.running = false;
    await this.ipcServer?.stop().catch(() => false);
    await this.gateway?.stop().catch(() => false);
    if (this.ownsLock) releaseRecoveryHostLock(this.paths, this.instanceId);
    this.ownsLock = false;
    return true;
  }
}

module.exports = {
  RecoveryHost,
  acquireRecoveryHostLock,
  releaseRecoveryHostLock,
  isProcessAlive,
  SUPERVISION_INTERVAL_MS,
  SUPERVISION_STATUS_STALE_MS,
  HANDOFF_SUPERVISION_DRAIN_MS,
  UI_RECOVERY_REGISTRATION_TIMEOUT_MS,
  UI_RECOVERY_COOLDOWN_MS,
  UI_RECOVERY_ATTEMPT_LIMIT,
  waitForReplacementLockRelease,
  activationClosureProjection,
  validatePersistedReadyConnectorProof
};
