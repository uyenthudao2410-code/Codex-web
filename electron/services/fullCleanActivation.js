const crypto = require('node:crypto');
const { ActivationEpochStore } = require('./activationEpoch');
const { readJson } = require('./jsonStore');
const { isAlive: isAlivePid } = require('./nativeService');
const { tunnelFingerprint } = require('./tunnelService');
const { recoveryMcpHealth, recoveryTunnelReady: probeRecoveryTunnelReady } = require('./recoveryPlaneService');
const {
  activationPostflight,
  lifecycleDecisionIsClean,
  normalizeLifecycleDecision,
  verifyActivationPostflight
} = require('./activationPostflight');

const COMPONENTS = Object.freeze(['recovery_host', 'coding_mcp', 'electron_ui']);
const DEFAULT_TTL_MS = 120_000;

function wait(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

function operationId() {
  return `full-clean-${Date.now().toString(36)}-${crypto.randomBytes(12).toString('hex')}`;
}

function epochError(code, message, details = {}) {
  return Object.assign(new Error(message), { code, details });
}

function text(value) { return String(value || '').trim(); }

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
    this.scheduleHandoff = scheduleHandoff;
    this.setActivationEpochCallback = setActivationEpoch;
    this.recoveryHostRunningRevision = text(recoveryHostRunningRevision);
    this.now = now;
    this.wait = waitFn;
    this.store = epochStore || new ActivationEpochStore({ paths, now });
    this.inFlight = null;
  }

  current() { return this.store.current(); }

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
        pid: numeric(ui.pid)
      }
    };
  }

  async preflight({ operationId: requestedOperationId = '', sourceCheckpoint = null, allowAcceptancePending = false } = {}) {
    if (this.orchestrator?.busy || this.orchestrator?.recovering) {
      throw epochError('RUNTIME_BUSY', 'Runtime is busy; full clean activation was not admitted.');
    }
    let runtime = { safe: true, code: 'COMPONENT_STOPPED' };
    if (typeof this.orchestrator?.inspectCodeActivation === 'function') {
      runtime = await this.orchestrator.inspectCodeActivation();
      const allowed = runtime?.code === 'COMPONENT_STOPPED'
        || runtime?.safe === true
        || (runtime?.code === 'ACCEPTANCE_PENDING' && allowAcceptancePending === true);
      if (!allowed) throw epochError(runtime?.code || 'ORCHESTRATION_STATE_UNCERTAIN', 'Canonical runtime lifecycle preflight refused full clean activation.', runtime);
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
        electron_ui: { instance_id: uiPresence.instance_id || null, pid: uiPresence.pid || null },
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
    try {
      return await this.orchestrator.prepareCodeActivation({
        operationId: operationIdValue,
        expiresAtUnixMs,
        allowAcceptancePending: allowAcceptancePending === true,
        ...(sourceCheckpoint ? { sourceCheckpoint } : {})
      });
    } catch (error) {
      if (String(error?.code || '') === 'COMPONENT_STOPPED') return { code: 'COMPONENT_STOPPED', safe: true, fenced: false };
      throw error;
    }
  }

  async _freshLifecycle(record) {
    const sourceCheckpoint = record?.source_checkpoint;
    if (!sourceCheckpoint || typeof this.orchestrator?.verifyCodeActivation !== 'function') return null;
    const raw = await this.orchestrator.verifyCodeActivation(record.operation_id, sourceCheckpoint);
    const lifecycle = raw?.lifecycle && typeof raw.lifecycle === 'object' ? raw.lifecycle : {};
    const snapshot = lifecycle.snapshot && typeof lifecycle.snapshot === 'object' ? lifecycle.snapshot : {};
    const counts = raw?.counts && typeof raw.counts === 'object' ? raw.counts : {};
    const source = raw?.source_checkpoint && typeof raw.source_checkpoint === 'object' ? raw.source_checkpoint : {};
    const sourceMatches = source.ok === true
      && source.code === 'ACTIVATABLE'
      && source.checkpoint_id === sourceCheckpoint.checkpoint_id
      && source.run_id === sourceCheckpoint.run_id
      && source.wave_id === sourceCheckpoint.wave_id
      && source.proof_fingerprint === sourceCheckpoint.proof_fingerprint
      && source.git_head === sourceCheckpoint.git_head;
    const countKeys = [
      'active_tool_calls', 'active_commands', 'starting_commands',
      'active_background_operations', 'active_managed_processes',
      'foreign_heavy_processes', 'active_agent_lanes',
      'threshold_sensitive_stale_candidates', 'owned_codex_sidecar_residues'
    ];
    const normalizedCounts = Object.fromEntries(countKeys.map((key) => [key, Number.isSafeInteger(counts[key]) ? counts[key] : -1]));
    const canonicalSnapshot = snapshot.backup_api_copy === true
      && snapshot.immutable === true
      && snapshot.query_only === true
      && Array.isArray(snapshot.integrity_check)
      && snapshot.integrity_check.length === 1
      && snapshot.integrity_check[0] === 'ok'
      && Number(snapshot.foreign_key_check_rows) === 0
      && /^[a-f0-9]{64}$/.test(String(snapshot.sha256 || ''))
      && /^[a-f0-9]{64}$/.test(String(snapshot.logical_sha256 || ''));
    const decision = {
      schema_version: 1,
      clean: raw?.safe === true
        && raw?.code === 'READY'
        && raw?.operation_id === record.operation_id
        && sourceMatches
        && canonicalSnapshot
        && raw?.fenced === false
        && raw?.fence_operation_id == null
        && countKeys.slice(0, 7).every((key) => normalizedCounts[key] === 0)
        && Number(lifecycle.unexplained_active_runs || 0) === 0
        && Number(lifecycle.unbound_live_resource_residues || 0) === 0,
      code: String(raw?.code || 'ORCHESTRATION_STATE_UNCERTAIN'),
      reason: String(raw?.reason || ''),
      observed_at: new Date(this.now()).toISOString(),
      canonical_lifecycle_observed: canonicalSnapshot,
      source_checkpoint_verified: sourceMatches,
      fence_released: raw?.fenced === false && raw?.fence_operation_id == null,
      fenced: raw?.fenced === true,
      fence_operation_id: raw?.fence_operation_id || null,
      counts: normalizedCounts,
      unexplained_active_runs: Number.isSafeInteger(lifecycle.unexplained_active_runs) ? lifecycle.unexplained_active_runs : -1,
      unbound_live_resource_residues: Number.isSafeInteger(lifecycle.unbound_live_resource_residues) ? lifecycle.unbound_live_resource_residues : -1,
      operation_id: record.operation_id
    };
    const normalized = normalizeLifecycleDecision(decision);
    if (!normalized || !lifecycleDecisionIsClean(normalized)) {
      throw epochError('LIFECYCLE_VERIFICATION_FAILED', 'Full clean activation did not receive a fresh checkpoint-bound unfenced lifecycle proof.', {
        operation_id: record.operation_id,
        source_checkpoint_verified: sourceMatches,
        canonical_lifecycle_observed: canonicalSnapshot,
        fenced: raw?.fenced,
        fence_operation_id: raw?.fence_operation_id || null
      });
    }
    return normalized;
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
    if (this.inFlight) return this.inFlight;
    this.inFlight = this._restart(options).finally(() => { this.inFlight = null; });
    return this.inFlight;
  }

  async _restart(options = {}) {
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
    if (preflight.runtime?.code === 'COMPONENT_STOPPED'
      && !(options.ledgerSnapshot && options.ledgerSnapshot.immutable === true && options.ledgerSnapshot.query_only === true)) {
      throw epochError('ORCHESTRATION_STATE_UNCERTAIN', 'Full clean activation refuses to stop/relaunch while the Coding MCP ledger census is unavailable.');
    }
    // Capture old process identities before any stop/mutation.  The evidence is
    // bound to this epoch and is later used to prove that every replacement is
    // fresh rather than merely reporting a non-empty persisted id.
    const componentEvidence = await this._captureIdentityEvidence();
    const record = this._beginRecord({
      operation_id,
      source_checkpoint: options.sourceCheckpoint || null,
      preflight,
      component_evidence: componentEvidence,
      metadata: {
        reason: options.reason || 'operator_restart',
        requested_at_unix_ms: this.now(),
        expires_at_unix_ms: expiresAtUnixMs
      },
      activation_epoch_id: options.activationEpochId
    });
    const epochId = record.activation_epoch_id;
    try {
      this.setActivationEpoch(epochId);
      this.store.update(epochId, { state: 'ADMISSION_CLOSED', reason: 'new-admission-closed' });
      const fence = await this._prepareFence(operation_id, expiresAtUnixMs, options.sourceCheckpoint || null, options.allowAcceptancePending);
      const runtimeRunning = preflight.runtime?.code !== 'COMPONENT_STOPPED';
      if (runtimeRunning && (!fence || fence.safe !== true || fence.fenced !== true || String(fence.fence_operation_id || '') !== operation_id)) {
        throw epochError('ACTIVATION_PREFLIGHT_UNVERIFIED', 'Full clean activation requires an exact checkpoint-bound runtime fence before stopping processes.', { fence });
      }
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
      await this.orchestrator.start({ automatic: true, fullClean: true, activationEpochId: epochId, activationGate: 'closed', expiresAtUnixMs: effectiveExpiry });
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
        this.store.update(epochId, { state: 'VERIFYING', reason: census.reason || 'waiting-for-connector-or-component' , verification: census });
        this._linkActionPending(this.store.current(), { census, activation_state: 'VERIFYING' });
        return { activation_epoch_id: epochId, state: 'VERIFYING', admission_open: false, fully_ready: false, census };
      }
      return this.finalize(epochId, census);
    } catch (error) {
      this._failEpoch(epochId, error);
      throw error;
    }
  }

  async finalCensus(activationEpochId, { expectedOldInstanceId = '' } = {}) {
    const epochId = text(activationEpochId);
    if (!epochId) throw epochError('ACTIVATION_EPOCH_ID_REQUIRED', 'Activation epoch is required for final census.');
    const record = this.store.current();
    if (!record || String(record.activation_epoch_id || '') !== epochId) {
      throw epochError('ACTIVATION_EPOCH_NOT_CURRENT', 'Final census must target the current durable activation epoch.');
    }
    const settings = this._settings();
    const runtime = await this.orchestrator?.lightweightSnapshot?.() || {};
    const health = await this.orchestrator?.currentMcpHealth?.().catch?.(() => null) || null;
    let tunnelStatusVerified = runtime.tunnelRunning === true;
    if (typeof this.orchestrator?.tunnel?.status === 'function') {
      try {
        tunnelStatusVerified = await this.orchestrator.tunnel.status(settings, { activationEpochId: epochId }) === true;
      } catch { tunnelStatusVerified = false; }
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
    const connectorReady = Boolean(runtime.connectorRefreshRequired === false
      && runtime.connectorRediscovered === true
      && runtime.connectorAcknowledgementPending === false);
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
    if (currentRecoveryMcpPid && currentRecoveryMcpInstanceId && this.secrets?.get && settings.recoveryMcpPort) {
      try {
        const token = this.secrets.get('mcpAuthToken');
        const health = await recoveryMcpHealth(
          settings.recoveryMcpPort,
          token,
          this.deviceIdentity?.device_id || '',
          this._deviceInstanceId() || '',
          epochId,
          currentRecoveryMcpPid,
          currentRecoveryMcpInstanceId
        );
        recoveryMcpHealthVerified = Boolean(health
          && Number(health.pid) === currentRecoveryMcpPid
          && String(health.instance_id || '') === currentRecoveryMcpInstanceId);
      } catch { recoveryMcpHealthVerified = false; }
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
    const pass = Boolean(runtime.mcpRunning === true && tunnelStatusVerified && health?.ready === true
      && processIdentity && epochMatches && workspaceMatches && deviceMatches && revisionMatches
      && tunnelEpochMatches && connectorReady && hostChanged && recoveryHostRevisionMatches
      && recoveryHostEpochMatches
      && uiReady && recoveryMcpReady && recoveryTunnelReady);
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
      connector_acknowledged: connectorReady,
      ui_verified: uiReady,
      recovery_plane_verified: recoveryMcpReady && recoveryTunnelReady,
      reason: pass ? null : 'UPDATE_INCOMPLETE',
      runtime
    };
  }

  async finalize(activationEpochId, census = null) {
    const epochId = text(activationEpochId);
    if (!epochId) throw epochError('ACTIVATION_EPOCH_ID_REQUIRED', 'Activation epoch is required.');
    let initialProof = null;
    let record = null;
    let lifecycleBeforeOpen = null;
    let opened = false;
    try {
      // Never trust a caller-supplied boolean/projection as final proof.  A
      // fresh census is mandatory at this boundary; the optional argument is
      // retained only for backwards-compatible call signatures.  Keep this
      // read inside the transaction catch so a transport/store/census
      // exception is durably terminalized as FAILED rather than leaving an
      // active epoch that merely appears stuck.
      initialProof = await this.finalCensus(epochId);
      if (!initialProof.pass) throw epochError('UPDATE_INCOMPLETE', 'Full clean activation final census is incomplete.', initialProof);
      record = this.store.current();
      lifecycleBeforeOpen = await this._freshLifecycle(record);
      if (typeof this.orchestrator?.completeActivationEpoch === 'function') {
        await this.orchestrator.completeActivationEpoch(epochId);
        opened = true;
      }
      // Re-read every component after MCP admission is completed and before the
      // durable READY transition.  If any identity/revision/epoch changed in
      // that window, close admission again and leave the epoch failed/closed.
      const finalProof = await this.finalCensus(epochId);
      if (!finalProof.pass) throw epochError('UPDATE_INCOMPLETE', 'Full clean activation changed during final commit.', finalProof);
      const lifecycle = record?.source_checkpoint ? await this._freshLifecycle(record) : lifecycleBeforeOpen;
      const postflightByComponent = this._componentPostflights(record, finalProof, lifecycle);
      const censusWithProof = {
        ...finalProof,
        component_postflights: postflightByComponent,
        lifecycle_verified: lifecycle ? lifecycleDecisionIsClean(lifecycle) : null
      };
      const ready = this.store.ready(epochId, { verified: true, activation_epoch_id: epochId, final_census: censusWithProof });
      const result = this._actionResult(ready, {
        state: 'READY',
        admission_open: true,
        fully_ready: true,
        census: censusWithProof,
        postflight_by_component: postflightByComponent
      });
      const linked = this._finishLinkedAction(ready, 'completed', result);
      return linked || result;
    } catch (error) {
      if (opened) {
        let closed = false;
        if (typeof this.orchestrator?.closeActivationEpoch === 'function') {
          try {
            const closeResult = await this.orchestrator.closeActivationEpoch(epochId);
            closed = closeResult?.ok !== false;
          } catch { closed = false; }
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

module.exports = { FullCleanActivation, COMPONENTS, DEFAULT_TTL_MS, operationId };
