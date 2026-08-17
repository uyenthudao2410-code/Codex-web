const fs = require('node:fs');
const path = require('node:path');
const { RecoveryActionStore, OPERATION_ID_PATTERN } = require('./recoveryActionStore');
const { isProcessAlive } = require('./recoveryIpc');
const { recoveryHostLegacyV1Revision } = require('./componentRevision');
const { readJson, writeJsonAtomic } = require('./jsonStore');

const COMPONENTS = new Set(['coding_mcp', 'electron_ui', 'recovery_host']);
const REVISION_PATTERN = /^[a-f0-9]{64}$/;
const INSTANCE_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/;
const MAX_REQUEST_TTL_MS = 60_000;
const CLOCK_SKEW_MS = 5_000;
const UI_RECOVERY_STATE_VERSION = 1;
const UI_RECOVERY_EXIT_REASONS = new Set(['operator_quit', 'runtime_stop']);

function activationError(code, message, details = {}) {
  return Object.assign(new Error(message), { code, details });
}

function ensureActivationFresh(request, now) {
  if (Number(request?.expires_at_unix_ms || 0) <= now) {
    throw activationError('ACTIVATION_REQUEST_EXPIRED', 'Activation request expired before process mutation.');
  }
}

function exactObject(value, allowed, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw activationError('INVALID_ARGUMENT', `${label} must be an object.`);
  }
  const unexpected = Object.keys(value).filter((key) => !allowed.has(key));
  if (unexpected.length) throw activationError('INVALID_ARGUMENT', `${label} contains unsupported fields.`);
  return value;
}

function normalizeActivationRequest(input, now = Date.now(), { allowExpiredReplay = false } = {}) {
  const value = exactObject(input, new Set([
    'operation_id', 'component', 'requested_at_unix_ms', 'expires_at_unix_ms',
    'expected_disk_revision', 'allow_acceptance_pending'
  ]), 'activation request');
  const request = {
    operation_id: String(value.operation_id || ''),
    component: String(value.component || ''),
    requested_at_unix_ms: Number(value.requested_at_unix_ms || 0),
    expires_at_unix_ms: Number(value.expires_at_unix_ms || 0),
    expected_disk_revision: String(value.expected_disk_revision || '').toLowerCase(),
    allow_acceptance_pending: value.allow_acceptance_pending === true
  };
  if (!OPERATION_ID_PATTERN.test(request.operation_id)) throw activationError('INVALID_OPERATION_ID', 'Invalid activation operation_id.');
  if (!COMPONENTS.has(request.component)) throw activationError('INVALID_COMPONENT', 'Activation component is not allowlisted.');
  if (!REVISION_PATTERN.test(request.expected_disk_revision)) throw activationError('INVALID_REVISION', 'expected_disk_revision must be a SHA-256 component revision.');
  if (!Number.isSafeInteger(request.requested_at_unix_ms) || !Number.isSafeInteger(request.expires_at_unix_ms)) {
    throw activationError('INVALID_ARGUMENT', 'Activation timestamps must be integer milliseconds.');
  }
  if (request.expires_at_unix_ms <= request.requested_at_unix_ms
    || request.expires_at_unix_ms > request.requested_at_unix_ms + MAX_REQUEST_TTL_MS) {
    throw activationError('ACTIVATION_REQUEST_EXPIRED', 'Activation request expiry is outside the allowed window.');
  }
  if (!allowExpiredReplay
    && (request.requested_at_unix_ms > now + CLOCK_SKEW_MS
      || request.requested_at_unix_ms < now - MAX_REQUEST_TTL_MS
      || request.expires_at_unix_ms <= now)) {
    throw activationError('ACTIVATION_REQUEST_EXPIRED', 'Activation request timestamp is outside the allowed window.');
  }
  return request;
}

class RecoveryActivation {
  constructor({
    paths,
    revisions,
    orchestrator,
    log,
    recoveryInstanceId,
    recoveryRunningRevision,
    actionStore = null,
    spawnRecoveryReplacement = null,
    spawnElectronUi = null,
    beginRecoveryHandoff = null,
    now = () => Date.now()
  }) {
    this.paths = paths;
    this.revisions = revisions;
    this.orchestrator = orchestrator;
    this.log = log;
    this.recoveryInstanceId = recoveryInstanceId;
    this.recoveryRunningRevision = recoveryRunningRevision;
    this.actions = actionStore || new RecoveryActionStore({ paths, now });
    this.spawnRecoveryReplacement = spawnRecoveryReplacement;
    this.spawnElectronUi = spawnElectronUi;
    this.beginRecoveryHandoff = beginRecoveryHandoff;
    this.now = now;
    this.uiRegistration = null;
    this.uiRecoveryStateFile = path.join(paths.dataRoot(), 'electron-ui-recovery.json');
    this.uiRecoveryPreference = this.loadUiRecoveryPreference();
  }

  loadUiRecoveryPreference() {
    if (!fs.existsSync(this.uiRecoveryStateFile)) {
      return { version: UI_RECOVERY_STATE_VERSION, suppressed: false, reason: '', updated_at_unix_ms: 0 };
    }
    const value = readJson(this.uiRecoveryStateFile, null);
    const updatedAt = Number(value?.updated_at_unix_ms || 0);
    if (value?.version !== UI_RECOVERY_STATE_VERSION || typeof value?.suppressed !== 'boolean'
      || !Number.isSafeInteger(updatedAt) || updatedAt < 0) {
      return {
        version: UI_RECOVERY_STATE_VERSION,
        suppressed: true,
        reason: 'state_invalid',
        updated_at_unix_ms: this.now(),
        error_code: 'UI_RECOVERY_STATE_INVALID'
      };
    }
    return {
      version: UI_RECOVERY_STATE_VERSION,
      suppressed: value.suppressed,
      reason: String(value.reason || '').slice(0, 80),
      updated_at_unix_ms: updatedAt
    };
  }

  writeUiRecoveryPreference(suppressed, reason = '') {
    const next = {
      version: UI_RECOVERY_STATE_VERSION,
      suppressed: suppressed === true,
      reason: suppressed === true ? String(reason || '').slice(0, 80) : '',
      updated_at_unix_ms: this.now()
    };
    writeJsonAtomic(this.uiRecoveryStateFile, next);
    try { fs.chmodSync(this.uiRecoveryStateFile, 0o600); } catch { /* best effort on Windows */ }
    this.uiRecoveryPreference = next;
    return this.uiRecoveryPreferenceStatus();
  }

  uiRecoveryPreferenceStatus() {
    return {
      ...this.uiRecoveryPreference,
      state: this.uiRecoveryPreference?.suppressed ? 'suppressed' : 'enabled'
    };
  }

  uiPresence() {
    const registration = this.uiRegistration;
    return {
      tracked: Boolean(registration),
      alive: Boolean(registration && isProcessAlive(registration.pid)),
      instance_id: registration?.instance_id || null,
      pid: registration?.pid || null,
      registered_at_unix_ms: registration?.registered_at_unix_ms || null
    };
  }

  hasPendingUiActivation() {
    return Boolean(this.actions.load().actions.find((item) => (
      item.component === 'electron_ui'
      && item.state === 'accepted'
      && Number(item.expires_at_unix_ms || 0) > this.now()
    )));
  }

  suppressUiRecovery(input) {
    const value = exactObject(input, new Set(['instance_id', 'reason']), 'UI recovery suppression');
    const intent = { instance_id: String(value.instance_id || ''), reason: String(value.reason || '') };
    const presence = this.uiPresence();
    if (!INSTANCE_ID_PATTERN.test(intent.instance_id) || !UI_RECOVERY_EXIT_REASONS.has(intent.reason)) {
      throw activationError('INVALID_UI_RECOVERY_INTENT', 'Electron UI recovery suppression intent is invalid.');
    }
    if (!presence.tracked || !presence.alive || presence.instance_id !== intent.instance_id) {
      throw activationError('UI_RECOVERY_INSTANCE_MISMATCH', 'Electron UI recovery suppression must match the live registered UI instance.');
    }
    return this.writeUiRecoveryPreference(true, intent.reason);
  }

  recoveryRevisionStatus() {
    return this.revisions.status('recovery_host', this.recoveryRunningRevision);
  }

  uiRevisionStatus() {
    const presence = this.uiPresence();
    try {
      return this.revisions.status('electron_ui', presence.alive ? this.uiRegistration?.revision || null : null);
    } catch (error) {
      return {
        running_revision: presence.alive ? this.uiRegistration?.revision || null : null,
        disk_revision: null,
        update_pending: null,
        state: 'unavailable',
        error_code: String(error?.code || 'REVISION_UNAVAILABLE')
      };
    }
  }

  componentRevisionStatus(component) {
    if (component === 'recovery_host') return this.recoveryRevisionStatus();
    if (component === 'electron_ui') return this.uiRevisionStatus();
    return this.orchestrator.codingMcpRevisionStatus();
  }

  validateExpectedRevision(request) {
    const status = this.componentRevisionStatus(request.component);
    if (!status.disk_revision) throw activationError('REVISION_UNAVAILABLE', 'The component disk revision is unavailable.');
    if (status.disk_revision !== request.expected_disk_revision) {
      throw activationError('REVISION_CHANGED', 'The component changed after this activation request was created.', {
        expected_disk_revision: request.expected_disk_revision,
        disk_revision: status.disk_revision
      });
    }
    return status;
  }

  async preflight(input) {
    const request = normalizeActivationRequest(input, this.now());
    const revision = this.validateExpectedRevision(request);
    if (revision.running_revision === revision.disk_revision) {
      return { safe: true, code: 'ALREADY_CURRENT', component: request.component, revision };
    }
    if (request.component === 'electron_ui') {
      return { safe: true, code: 'READY', component: request.component, revision };
    }
    const runtime = await this.orchestrator.inspectCodeActivation();
    if (!runtime.safe) {
      if (runtime.code === 'ACCEPTANCE_PENDING' && request.allow_acceptance_pending) {
        return { safe: true, code: 'READY', component: request.component, revision, runtime: { ...runtime, acceptance_preserved: true } };
      }
      return { safe: false, code: runtime.code || 'ORCHESTRATION_STATE_UNCERTAIN', component: request.component, revision, runtime };
    }
    return { safe: true, code: 'READY', component: request.component, revision, runtime };
  }

  async activate(input) {
    const now = this.now();
    const replayRequest = normalizeActivationRequest(input, now, { allowExpiredReplay: true });
    const replay = this.actions.replay(replayRequest);
    if (replay) return { ...replay, deduplicated: true };
    const request = normalizeActivationRequest(input, now);
    const claim = this.actions.begin(request);
    if (!claim.created) return { ...claim.record, deduplicated: true };
    let revision;
    try {
      revision = this.validateExpectedRevision(request);
      if (revision.running_revision === revision.disk_revision) {
        return this.actions.finish(request.operation_id, 'completed', {
          activated: false,
          already_current: true,
          revision: revision.disk_revision
        });
      }
      if (request.component === 'electron_ui') {
        ensureActivationFresh(request, this.now());
        if (!this.uiRegistration && typeof this.spawnElectronUi === 'function') {
          await this.spawnElectronUi({ expiresAtUnixMs: request.expires_at_unix_ms });
        }
        return this.actions.get(request.operation_id);
      }

      const inspection = await this.orchestrator.inspectCodeActivation();
      if (inspection.code === 'COMPONENT_STOPPED' && request.component === 'coding_mcp') {
        return this.actions.finish(request.operation_id, 'completed', {
          activated: false,
          component_stopped: true,
          next_start_revision: request.expected_disk_revision
        });
      }
      if (!inspection.safe && !(inspection.code === 'ACCEPTANCE_PENDING' && request.allow_acceptance_pending)) {
        return this.actions.finish(request.operation_id, 'refused', null, {
          code: inspection.code || 'ORCHESTRATION_STATE_UNCERTAIN',
          message: `Activation refused: ${inspection.reason || 'runtime preflight failed'}`
        });
      }
      if (inspection.code !== 'COMPONENT_STOPPED') {
        const preflight = await this.orchestrator.prepareCodeActivation({
          operationId: request.operation_id,
          expiresAtUnixMs: Math.min(request.expires_at_unix_ms, this.now() + 55_000),
          allowAcceptancePending: request.allow_acceptance_pending
        });
        if (!preflight.safe) {
          return this.actions.finish(request.operation_id, 'refused', null, {
            code: preflight.code || 'ORCHESTRATION_STATE_UNCERTAIN',
            message: `Activation refused: ${preflight.reason || 'runtime preflight failed'}`
          });
        }
      }
      if (request.component === 'coding_mcp') {
        ensureActivationFresh(request, this.now());
        const result = await this.orchestrator.activateCodingMcpUpdate(request.expected_disk_revision, {
          expiresAtUnixMs: request.expires_at_unix_ms
        });
        return this.actions.finish(request.operation_id, 'completed', { activated: true, ...result });
      }
      ensureActivationFresh(request, this.now());
      if (typeof this.spawnRecoveryReplacement !== 'function' || typeof this.beginRecoveryHandoff !== 'function') {
        await this.orchestrator.cancelCodeActivation(request.operation_id);
        return this.actions.finish(request.operation_id, 'failed', null, {
          code: 'RECOVERY_REPLACEMENT_UNAVAILABLE',
          message: 'Recovery Host replacement launcher is unavailable.'
        });
      }
      await this.spawnRecoveryReplacement({
        operationId: request.operation_id,
        expectedOldInstanceId: this.recoveryInstanceId,
        expiresAtUnixMs: request.expires_at_unix_ms
      });
      this.beginRecoveryHandoff(request.operation_id);
      return this.actions.get(request.operation_id);
    } catch (error) {
      if (request.component !== 'electron_ui') await this.orchestrator.cancelCodeActivation(request.operation_id).catch(() => false);
      const code = String(error?.code || '');
      const expiredAfterMutation = code === 'ACTIVATION_REQUEST_EXPIRED' && error?.details?.process_mutated === true;
      const state = ['RUNTIME_BUSY', 'ORCHESTRATION_STATE_UNCERTAIN', 'ACCEPTANCE_PENDING', 'WORKSPACE_MISMATCH', 'COMPONENT_STOPPED', 'REVISION_CHANGED', 'ACTIVATION_REQUEST_EXPIRED'].includes(code)
        && !expiredAfterMutation ? 'refused' : 'failed';
      return this.actions.finish(request.operation_id, state, null, error);
    }
  }

  status(operationId) {
    if (!OPERATION_ID_PATTERN.test(String(operationId || ''))) throw activationError('INVALID_OPERATION_ID', 'Invalid activation operation_id.');
    const record = this.actions.get(operationId);
    if (!record) throw activationError('ACTIVATION_OPERATION_NOT_FOUND', 'Activation operation was not found.');
    return record;
  }

  registerUi(input) {
    const value = exactObject(input, new Set(['instance_id', 'pid', 'revision', 'started_at_unix_ms']), 'UI registration');
    const registration = {
      instance_id: String(value.instance_id || ''),
      pid: Number(value.pid || 0),
      revision: String(value.revision || '').toLowerCase(),
      started_at_unix_ms: Number(value.started_at_unix_ms || 0),
      registered_at_unix_ms: this.now()
    };
    if (!INSTANCE_ID_PATTERN.test(registration.instance_id) || !Number.isSafeInteger(registration.pid) || registration.pid <= 0
      || !REVISION_PATTERN.test(registration.revision) || !Number.isSafeInteger(registration.started_at_unix_ms)
      || registration.started_at_unix_ms > this.now() + CLOCK_SKEW_MS || !isProcessAlive(registration.pid)) {
      throw activationError('INVALID_UI_REGISTRATION', 'Electron UI registration is invalid or the process is not alive.');
    }
    this.uiRegistration = registration;
    if (this.uiRecoveryPreference?.suppressed || this.uiRecoveryPreference?.error_code) {
      this.writeUiRecoveryPreference(false, '');
    }
    const pending = this.actions.load().actions.find((item) => (
      item.component === 'electron_ui'
      && item.state === 'accepted'
      && Number(item.expires_at_unix_ms || 0) > this.now()
    )) || null;
    if (!pending) return { registered: true, restart_required: false, code_revision: this.uiRevisionStatus() };
    if (pending.expected_disk_revision === registration.revision) {
      const completed = this.actions.finish(pending.operation_id, 'completed', {
        activated: true,
        new_instance_id: registration.instance_id,
        new_revision: registration.revision,
        health_verified: true
      });
      return { registered: true, restart_required: false, activation: completed, code_revision: this.uiRevisionStatus() };
    }
    return {
      registered: true,
      restart_required: true,
      operation_id: pending.operation_id,
      expires_at_unix_ms: Number(pending.expires_at_unix_ms || 0),
      expected_revision: pending.expected_disk_revision,
      code_revision: this.uiRevisionStatus()
    };
  }

  verifyRecoveryReplacement(operationId) {
    const record = this.actions.get(operationId);
    if (!record || record.component !== 'recovery_host' || record.state !== 'accepted') {
      throw activationError('ACTIVATION_OPERATION_MISMATCH', 'Recovery replacement operation is not pending.');
    }
    const revision = this.recoveryRevisionStatus();
    if (!revision.running_revision || revision.running_revision !== revision.disk_revision || revision.update_pending) {
      throw activationError('REVISION_VERIFICATION_FAILED', 'Replacement Recovery Host did not load the expected revision.');
    }
    let revisionContract = 'current';
    let legacyBridge = null;
    if (revision.running_revision !== record.expected_disk_revision) {
      try {
        legacyBridge = recoveryHostLegacyV1Revision(this.paths.appRoot());
      } catch (error) {
        throw activationError('REVISION_VERIFICATION_FAILED', 'Replacement Recovery Host legacy revision bridge verification failed.', {
          bridge_error_code: String(error?.code || 'REVISION_BRIDGE_FAILED')
        });
      }
      if (legacyBridge.revision !== record.expected_disk_revision) {
        throw activationError('REVISION_VERIFICATION_FAILED', 'Replacement Recovery Host did not load source authorized by the legacy revision contract.', {
          expected_legacy_revision: record.expected_disk_revision,
          observed_legacy_revision: legacyBridge.revision,
          current_revision: revision.running_revision
        });
      }
      revisionContract = legacyBridge.contract;
    }
    return { record, revision, revisionContract, legacyBridge };
  }

  async completeRecoveryReplacement(operationId, oldInstanceId, options = {}) {
    const { revision, revisionContract } = this.verifyRecoveryReplacement(operationId);
    await this.orchestrator.cancelCodeActivation(operationId).catch(() => false);
    return this.actions.finish(operationId, 'completed', {
      activated: true,
      old_instance_id: oldInstanceId,
      new_instance_id: this.recoveryInstanceId,
      old_revision: null,
      new_revision: revision.running_revision,
      revision_contract: revisionContract,
      health_verified: true,
      coding_mcp_preserved: options.primaryLegacyMigrationRequired !== true,
      tunnel_preserved: options.primaryLegacyMigrationRequired !== true,
      legacy_device_migration: {
        primary_required: options.primaryLegacyMigrationRequired === true,
        recovery_required: options.recoveryLegacyMigrationRequired === true
      }
    });
  }
}

module.exports = {
  RecoveryActivation,
  normalizeActivationRequest,
  COMPONENTS,
  REVISION_PATTERN,
  MAX_REQUEST_TTL_MS,
  UI_RECOVERY_EXIT_REASONS
};
