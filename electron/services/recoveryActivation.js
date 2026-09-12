const fs = require('node:fs');
const path = require('node:path');
const { RecoveryActionStore, OPERATION_ID_PATTERN } = require('./recoveryActionStore');
const {
  normalizeProcessStartToken,
  observeProcessIdentity,
  observeProcessIdentityAsync,
  processIdentityFrom,
  sameProcessIdentity
} = require('./processIdentity');
const { recoveryHostLegacyV1Revision, RECOVERY_HOST_LEGACY_V1_CONTRACT } = require('./componentRevision');
const { readJson, writeJsonAtomic } = require('./jsonStore');
const {
  activationPostflight,
  BLOCKING_LIFECYCLE_COUNT_KEYS,
  LIFECYCLE_COUNT_KEYS,
  lifecycleDecisionIsClean,
  OLD_INSTANCE_STATES,
  normalizeActivationPostflight,
  verifyActivationPostflight
} = require('./activationPostflight');

const COMPONENTS = new Set(['coding_mcp', 'electron_ui', 'recovery_host']);
const REVISION_PATTERN = /^[a-f0-9]{64}$/;
const INSTANCE_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/;
const MAX_REQUEST_TTL_MS = 60_000;
const CLOCK_SKEW_MS = 5_000;
const UI_RECOVERY_STATE_VERSION = 1;
const UI_RECOVERY_EXIT_REASONS = new Set(['operator_quit', 'runtime_stop']);
const SOURCE_CHECKPOINT_FIELDS = new Set(['checkpoint_id', 'run_id', 'wave_id', 'proof_fingerprint', 'git_head']);
const SOURCE_ID_MAX_LENGTH = 256;
const GIT_OBJECT_ID_PATTERN = /^[a-f0-9]{40,64}$/;
const CHECKPOINT_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{7,127}$/;

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

function normalizeSourceCheckpoint(input, { allowEmptyProof = false } = {}) {
  if (input === undefined || input === null) {
    throw activationError('ACTIVATION_SOURCE_CHECKPOINT_REQUIRED', 'Activation requires an exact accepted source_checkpoint.');
  }
  const value = exactObject(input, SOURCE_CHECKPOINT_FIELDS, 'source_checkpoint');
  const checkpoint = {
    checkpoint_id: typeof value.checkpoint_id === 'string' ? value.checkpoint_id : '',
    run_id: typeof value.run_id === 'string' ? value.run_id : '',
    wave_id: typeof value.wave_id === 'string' ? value.wave_id : '',
    proof_fingerprint: typeof value.proof_fingerprint === 'string' ? value.proof_fingerprint : '',
    git_head: typeof value.git_head === 'string' ? value.git_head : ''
  };
  for (const field of ['checkpoint_id', 'run_id', 'wave_id']) {
    if (!CHECKPOINT_ID_PATTERN.test(checkpoint[field]) || checkpoint[field].length > SOURCE_ID_MAX_LENGTH) {
      throw activationError('INVALID_SOURCE_CHECKPOINT', `source_checkpoint.${field} is invalid.`);
    }
  }
  if ((!REVISION_PATTERN.test(checkpoint.proof_fingerprint)
      && !(allowEmptyProof && checkpoint.proof_fingerprint === ''))
    || !GIT_OBJECT_ID_PATTERN.test(checkpoint.git_head)) {
    throw activationError('INVALID_SOURCE_CHECKPOINT', 'source_checkpoint proof or Git identity is invalid.');
  }
  return checkpoint;
}

function normalizeActivationRequest(input, now = Date.now(), { allowExpiredReplay = false } = {}) {
  const value = exactObject(input, new Set([
    'operation_id', 'component', 'requested_at_unix_ms', 'expires_at_unix_ms',
    'expected_disk_revision', 'allow_acceptance_pending', 'source_checkpoint',
    // Explicit marker for callers that require the system transaction.  A
    // stale/legacy Recovery Host must reject this request rather than silently
    // falling back to component-scoped activation.
    'full_clean_required', 'activation_mode'
  ]), 'activation request');
  const request = {
    operation_id: String(value.operation_id || ''),
    component: String(value.component || ''),
    requested_at_unix_ms: Number(value.requested_at_unix_ms || 0),
    expires_at_unix_ms: Number(value.expires_at_unix_ms || 0),
    expected_disk_revision: String(value.expected_disk_revision || '').toLowerCase(),
    allow_acceptance_pending: value.allow_acceptance_pending === true,
    source_checkpoint: normalizeSourceCheckpoint(value.source_checkpoint),
    full_clean_required: value.full_clean_required === true,
    activation_mode: String(value.activation_mode || '').trim() || null
  };
  if (!OPERATION_ID_PATTERN.test(request.operation_id)) throw activationError('INVALID_OPERATION_ID', 'Invalid activation operation_id.');
  if (!COMPONENTS.has(request.component)) throw activationError('INVALID_COMPONENT', 'Activation component is not allowlisted.');
  if (request.full_clean_required && request.activation_mode !== 'full_clean_activation') {
    throw activationError('INVALID_ACTIVATION_MODE', 'A full-clean activation request must declare activation_mode=full_clean_activation.');
  }
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

function nonnegativeInteger(value) {
  return Number.isSafeInteger(value) && value >= 0;
}

function canonicalLifecycleSnapshot(lifecycle) {
  const snapshot = lifecycle && typeof lifecycle === 'object' && !Array.isArray(lifecycle)
    ? lifecycle.snapshot
    : null;
  return Boolean(snapshot && typeof snapshot === 'object' && !Array.isArray(snapshot)
    && snapshot.backup_api_copy === true
    && snapshot.immutable === true
    && snapshot.query_only === true
    && Array.isArray(snapshot.integrity_check)
    && snapshot.integrity_check.length === 1
    && snapshot.integrity_check[0] === 'ok'
    && nonnegativeInteger(snapshot.foreign_key_check_rows)
    && snapshot.foreign_key_check_rows === 0
    && REVISION_PATTERN.test(String(snapshot.sha256 || ''))
    && REVISION_PATTERN.test(String(snapshot.logical_sha256 || '')));
}

function sourceCheckpointMatches(value, expected) {
  if (!value || typeof value !== 'object' || Array.isArray(value)
    || !expected || typeof expected !== 'object') return false;
  return value.ok === true
    && value.code === 'ACTIVATABLE'
    && value.checkpoint_id === expected.checkpoint_id
    && value.run_id === expected.run_id
    && value.wave_id === expected.wave_id
    && value.proof_fingerprint === expected.proof_fingerprint
    && value.git_head === expected.git_head;
}

function lifecycleEvidence(source, request) {
  const runtime = source && typeof source === 'object' && !Array.isArray(source) ? source : {};
  const lifecycle = runtime.lifecycle && typeof runtime.lifecycle === 'object' && !Array.isArray(runtime.lifecycle)
    ? runtime.lifecycle
    : null;
  const rawCounts = runtime.counts && typeof runtime.counts === 'object' && !Array.isArray(runtime.counts)
    ? runtime.counts
    : null;
  const countsValid = Boolean(rawCounts
    && Object.keys(rawCounts).length === LIFECYCLE_COUNT_KEYS.length
    && LIFECYCLE_COUNT_KEYS.every((key) => Object.hasOwn(rawCounts, key) && nonnegativeInteger(rawCounts[key])));
  const counts = countsValid
    ? Object.fromEntries(LIFECYCLE_COUNT_KEYS.map((key) => [key, rawCounts[key]]))
    : {};
  const unexplained = lifecycle?.unexplained_active_runs;
  const residues = lifecycle?.unbound_live_resource_residues;
  return {
    lifecycle,
    counts,
    countsValid,
    canonicalLifecycleObserved: canonicalLifecycleSnapshot(lifecycle),
    sourceCheckpointVerified: sourceCheckpointMatches(runtime.source_checkpoint, request?.source_checkpoint),
    operationBound: runtime.operation_id === request?.operation_id,
    blockersClear: countsValid
      && BLOCKING_LIFECYCLE_COUNT_KEYS.every((key) => counts[key] === 0)
      && unexplained === 0
      && residues === 0,
    unexplainedActiveRuns: nonnegativeInteger(unexplained) ? unexplained : null,
    unboundLiveResourceResidues: nonnegativeInteger(residues) ? residues : null
  };
}

function verifiedLifecycleResponse(source, request, { fenced }) {
  const evidence = lifecycleEvidence(source, request);
  const expectedFence = fenced === true;
  return Boolean(source && typeof source === 'object' && !Array.isArray(source)
    && source.safe === true
    && source.code === 'READY'
    && evidence.operationBound
    && evidence.sourceCheckpointVerified
    && evidence.canonicalLifecycleObserved
    && evidence.blockersClear
    && source.fenced === expectedFence
    && (expectedFence
      ? source.fence_operation_id === request.operation_id
      : source.fence_operation_id === null));
}

function lifecycleDecision(runtime, request, observedAt) {
  const source = runtime && typeof runtime === 'object' ? runtime : {};
  const evidence = lifecycleEvidence(source, request);
  return {
    schema_version: 1,
    clean: source.safe === true
      && source.code === 'READY'
      && evidence.operationBound
      && evidence.canonicalLifecycleObserved
      && evidence.sourceCheckpointVerified
      && evidence.blockersClear
      && source.fenced === false
      && source.fence_operation_id == null,
    code: String(source.code || 'ORCHESTRATION_STATE_UNCERTAIN').slice(0, 80),
    reason: String(source.reason || '').slice(0, 120),
    observed_at: String(observedAt || new Date().toISOString()),
    canonical_lifecycle_observed: evidence.canonicalLifecycleObserved,
    source_checkpoint_verified: evidence.sourceCheckpointVerified,
    fence_released: source.fenced === false && source.fence_operation_id == null,
    fenced: typeof source.fenced === 'boolean' ? source.fenced : null,
    fence_operation_id: String(source.fence_operation_id || '') || null,
    operation_id: typeof source.operation_id === 'string' ? source.operation_id : null,
    counts: evidence.counts,
    unexplained_active_runs: evidence.unexplainedActiveRuns,
    unbound_live_resource_residues: evidence.unboundLiveResourceResidues
  };
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
    fullCleanActivation = null,
    processIdentityObserver = observeProcessIdentity,
    asyncProcessIdentityObserver = null,
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
    this.fullCleanActivation = fullCleanActivation;
    this.processIdentityObserver = typeof processIdentityObserver === 'function'
      ? processIdentityObserver
      : observeProcessIdentity;
    this.asyncProcessIdentityObserver = typeof asyncProcessIdentityObserver === 'function'
      ? asyncProcessIdentityObserver
      : this.processIdentityObserver === observeProcessIdentity
        ? observeProcessIdentityAsync
        : this.processIdentityObserver;
    this.now = now;
    this.uiRegistration = null;
    this.lastUiPresence = null;
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

  uiPresence({ preferCached = false } = {}) {
    const registration = this.uiRegistration;
    const cached = this.lastUiPresence;
    const cacheMatches = Boolean(
      cached
      && registration
      && cached.instance_id === registration.instance_id
      && Number(cached.pid || 0) === Number(registration.pid || 0)
      && normalizeProcessStartToken(cached.process_start_token)
        === normalizeProcessStartToken(registration.process_start_token)
    );
    if (preferCached) {
      if (cacheMatches) return { ...cached };
      return {
        tracked: Boolean(registration),
        alive: null,
        instance_id: registration?.instance_id || null,
        activation_epoch_id: registration?.activation_epoch_id || null,
        pid: registration?.pid || null,
        process_start_token: registration?.process_start_token || null,
        registered_at_unix_ms: registration?.registered_at_unix_ms || null,
        observed_at_unix_ms: null
      };
    }
    let identityMatches = false;
    if (registration) {
      try {
        const observed = this.processIdentityObserver(registration.pid);
        // Presence is a synchronous status/activation projection. A thenable
        // or unavailable observation cannot authorize the registered owner.
        identityMatches = !observed?.then && sameProcessIdentity(registration, observed);
      } catch { identityMatches = false; }
    }
    const presence = {
      tracked: Boolean(registration),
      alive: Boolean(registration && identityMatches),
      instance_id: registration?.instance_id || null,
      activation_epoch_id: registration?.activation_epoch_id || null,
      pid: registration?.pid || null,
      process_start_token: registration?.process_start_token || null,
      registered_at_unix_ms: registration?.registered_at_unix_ms || null,
      observed_at_unix_ms: this.now()
    };
    this.lastUiPresence = presence;
    return { ...presence };
  }

  async observeUiPresence() {
    const registration = this.uiRegistration;
    if (!registration) {
      const presence = {
        tracked: false,
        alive: false,
        instance_id: null,
        activation_epoch_id: null,
        pid: null,
        process_start_token: null,
        registered_at_unix_ms: null,
        observed_at_unix_ms: this.now()
      };
      this.lastUiPresence = presence;
      return { ...presence };
    }

    let observed;
    try { observed = await this.asyncProcessIdentityObserver(registration.pid); }
    catch (error) {
      observed = { state: 'unavailable', code: error?.code || 'PROCESS_IDENTITY_UNVERIFIED' };
    }

    const current = this.uiRegistration;
    const registrationStillCurrent = Boolean(
      current
      && current.instance_id === registration.instance_id
      && Number(current.pid || 0) === Number(registration.pid || 0)
      && normalizeProcessStartToken(current.process_start_token)
        === normalizeProcessStartToken(registration.process_start_token)
    );
    if (!registrationStillCurrent) {
      return {
        tracked: Boolean(current),
        alive: null,
        instance_id: current?.instance_id || null,
        activation_epoch_id: current?.activation_epoch_id || null,
        pid: current?.pid || null,
        process_start_token: current?.process_start_token || null,
        registered_at_unix_ms: current?.registered_at_unix_ms || null,
        observed_at_unix_ms: null
      };
    }

    let alive = null;
    if (observed?.state === 'absent') alive = false;
    else if (observed?.state === 'live') alive = sameProcessIdentity(registration, observed);
    const presence = {
      tracked: true,
      alive,
      instance_id: registration.instance_id,
      activation_epoch_id: registration.activation_epoch_id || null,
      pid: registration.pid,
      process_start_token: registration.process_start_token,
      registered_at_unix_ms: registration.registered_at_unix_ms || null,
      observed_at_unix_ms: this.now()
    };
    this.lastUiPresence = presence;
    return { ...presence };
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

  recoveryRevisionStatus(options = {}) {
    return this.revisions.status('recovery_host', this.recoveryRunningRevision, options);
  }

  uiRevisionStatus(options = {}) {
    const presence = options.presence && typeof options.presence === 'object'
      ? options.presence
      : this.uiPresence({ preferCached: options.preferCachedPresence === true });
    try {
      return this.revisions.status('electron_ui', presence.alive ? this.uiRegistration?.revision || null : null, options);
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

  componentRevisionStatus(component, options = {}) {
    if (component === 'recovery_host') return this.recoveryRevisionStatus(options);
    if (component === 'electron_ui') return this.uiRevisionStatus(options);
    return this.orchestrator.codingMcpRevisionStatus(options);
  }

  async componentInstanceId(component) {
    if (component === 'recovery_host') return String(this.recoveryInstanceId || '') || null;
    if (component === 'electron_ui') return String(this.uiPresence().instance_id || '') || null;
    try {
      const health = await this.orchestrator.currentMcpHealth();
      return String(health?.process_instance_id || '') || null;
    } catch { return null; }
  }

  validateExpectedRevision(request) {
    const status = this.componentRevisionStatus(request.component, { force: true });
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
    if (request.full_clean_required && !this.hasFullCleanCoordinator()) {
      return {
        safe: false,
        code: 'RECOVERY_HOST_UPGRADE_REQUIRED',
        component: request.component,
        activation_mode: request.activation_mode,
        full_clean_required: true,
        revision,
        reason: 'The authenticated Recovery Host does not expose the current full-clean activation coordinator.'
      };
    }
    const conflict = this.actions.active(request.operation_id);
    if (conflict) {
      return {
        safe: false,
        code: 'ACTIVATION_CONFLICT',
        component: request.component,
        revision,
        conflicting_operation_id: conflict.operation_id,
        lifecycle_decision: lifecycleDecision(null, request, new Date(this.now()).toISOString())
      };
    }
    const inspected = await this.orchestrator.inspectCodeActivation();
    const runtime = inspected.code === 'COMPONENT_STOPPED'
      ? inspected
      : await this.orchestrator.verifyCodeActivation(
        request.operation_id,
        request.source_checkpoint,
        request.allow_acceptance_pending
      );
    if (runtime.code === 'COMPONENT_STOPPED' && request.component !== 'coding_mcp') {
      return {
        safe: false,
        code: 'ORCHESTRATION_STATE_UNCERTAIN',
        component: request.component,
        revision,
        runtime,
        lifecycle_decision: lifecycleDecision(runtime, request, new Date(this.now()).toISOString())
      };
    }
    if (!runtime.safe) {
      if (runtime.code === 'ACCEPTANCE_PENDING' && request.allow_acceptance_pending) {
        const preserved = { ...runtime, safe: true, acceptance_preserved: true };
        return {
          safe: true,
          code: revision.running_revision === revision.disk_revision ? 'ALREADY_CURRENT' : 'READY',
          component: request.component,
          revision,
          runtime: preserved,
          lifecycle_decision: lifecycleDecision(preserved, request, new Date(this.now()).toISOString())
        };
      }
      return {
        safe: false,
        code: runtime.code || 'ORCHESTRATION_STATE_UNCERTAIN',
        component: request.component,
        revision,
        runtime,
        lifecycle_decision: lifecycleDecision(runtime, request, new Date(this.now()).toISOString())
      };
    }
    return {
      safe: true,
      code: runtime.code === 'COMPONENT_STOPPED'
        ? 'COMPONENT_STOPPED'
        : revision.running_revision === revision.disk_revision ? 'ALREADY_CURRENT' : 'READY',
      component: request.component,
      revision,
      runtime,
      lifecycle_decision: lifecycleDecision(runtime, request, new Date(this.now()).toISOString())
    };
  }

  async componentInstanceEvidence(component) {
    if (component === 'recovery_host') {
      const instanceId = String(this.recoveryInstanceId || '') || null;
      return { instanceId, state: instanceId ? 'RUNNING' : null, proven: Boolean(instanceId) };
    }
    if (component === 'electron_ui') {
      const presence = this.uiPresence();
      if (presence.alive && presence.instance_id) {
        return { instanceId: String(presence.instance_id), state: 'RUNNING', proven: true };
      }
      // A local presence census is authoritative for the tracked UI process:
      // either no UI is registered or the exact tracked PID is dead.
      if (!presence.alive && (presence.tracked === false || presence.instance_id)) {
        return { instanceId: String(presence.instance_id || '') || null, state: 'ABSENT', proven: true };
      }
      return { instanceId: null, state: null, proven: false };
    }
    try {
      const health = await this.orchestrator.currentMcpHealth();
      const instanceId = String(health?.process_instance_id || '') || null;
      if (instanceId) return { instanceId, state: 'RUNNING', proven: true };
    } catch { /* the inspection below distinguishes stopped from unavailable */ }
    return { instanceId: null, state: null, proven: false };
  }

  async verifyFreshLifecycle(request) {
    if (typeof this.orchestrator.verifyCodeActivation !== 'function') {
      throw activationError('LIFECYCLE_VERIFICATION_UNAVAILABLE', 'The official post-cancel lifecycle verifier is unavailable.');
    }
    let verification;
    try {
      verification = await this.orchestrator.verifyCodeActivation(
        request.operation_id,
        request.source_checkpoint,
        request.allow_acceptance_pending
      );
    } catch (error) {
      throw activationError(String(error?.code || 'LIFECYCLE_VERIFICATION_FAILED'), String(error?.message || 'Fresh lifecycle verification failed.'));
    }
    const decision = lifecycleDecision(verification, request, new Date(this.now()).toISOString());
    if (!verifiedLifecycleResponse(verification, request, { fenced: false })
      || !lifecycleDecisionIsClean(decision)) {
      throw activationError('LIFECYCLE_VERIFICATION_FAILED', 'Fresh lifecycle evidence is not checkpoint-bound and unfenced.', {
        safe: verification?.safe,
        operation_id_matches: verification?.operation_id === request.operation_id,
        fenced: verification?.fenced,
        fence_operation_id: verification?.fence_operation_id || null,
        source_checkpoint_verified: decision.source_checkpoint_verified,
        canonical_lifecycle_observed: decision.canonical_lifecycle_observed,
        lifecycle_clean: decision.clean
      });
    }
    return decision;
  }

  async releaseFenceAndBuildPostflight(request, values = {}) {
    // Replacing Coding MCP destroys the old in-memory fence along with the old
    // process, so cancel may legitimately report "already absent".  The
    // authoritative condition is the fresh, authenticated verify call below:
    // it must observe this exact operation unfenced and revalidate the exact
    // source checkpoint against a new immutable lifecycle census.
    await this.orchestrator.cancelCodeActivation(request.operation_id).catch(() => false);
    const lifecycle = await this.verifyFreshLifecycle(request);
    return activationPostflight(request, {
      ...values,
      startedAt: values.startedAt || new Date(this.now()).toISOString(),
      completedAt: values.completedAt || new Date(this.now()).toISOString(),
      lifecycle
    });
  }

  async verifyCheckpointLifecycle({ operationId, sourceCheckpoint }) {
    const request = {
      operation_id: String(operationId || ''),
      source_checkpoint: normalizeSourceCheckpoint(sourceCheckpoint, { allowEmptyProof: true })
    };
    return this.verifyFreshLifecycle(request);
  }

  hasFullCleanCoordinator() {
    return Boolean(this.fullCleanActivation?.restart
      && typeof this.orchestrator?.completeActivationEpoch === 'function');
  }

  coordinatorFailureState(operationId, error) {
    const linked = this.actions.get(operationId);
    const linkedEpoch = String(linked?.activation_epoch_id || linked?.result?.activation_epoch_id || '').trim();
    const retryable = new Set([
      'RUNTIME_BUSY', 'ORCHESTRATION_STATE_UNCERTAIN', 'ACCEPTANCE_PENDING',
      'ACTIVATION_CONFLICT', 'ACTIVATION_REQUEST_EXPIRED'
    ]).has(String(error?.code || ''));
    // Once an epoch exists, the coordinator may already have stopped or
    // fenced the old runtime.  That boundary is a failed activation, never a
    // retryable refusal, and admission must remain closed until a new request.
    return linkedEpoch && !['READY'].includes(String(linked?.activation_state || ''))
      ? 'failed'
      : (retryable ? 'refused' : 'failed');
  }

  finishCoordinatorFailure(operationId, error) {
    const current = this.actions.get(operationId);
    if (!current || ['completed', 'failed', 'refused'].includes(current.state)) return current;
    const linkedEpoch = String(current.activation_epoch_id || current.result?.activation_epoch_id || '').trim() || null;
    const state = this.coordinatorFailureState(operationId, error);
    return this.actions.finish(operationId, state, linkedEpoch ? {
      full_clean_activation: true,
      activation_epoch_id: linkedEpoch,
      state: 'FAILED',
      admission_open: false,
      fully_ready: false
    } : null, error);
  }

  bindFullCleanEpoch(operationId, result) {
    if (typeof this.actions?.bindDurableEpoch !== 'function'
      || typeof this.fullCleanActivation?.current !== 'function') {
      throw activationError('ACTIVATION_EPOCH_BINDING_UNAVAILABLE', 'Durable Full Clean epoch binding is unavailable.');
    }
    const returnedOperationId = typeof result?.operation_id === 'string' ? result.operation_id : '';
    const returnedEpochId = typeof result?.activation_epoch_id === 'string'
      ? result.activation_epoch_id
      : (typeof result?.result?.activation_epoch_id === 'string' ? result.result.activation_epoch_id : '');
    if (returnedOperationId !== operationId || !returnedEpochId) {
      throw activationError('ACTIVATION_EPOCH_BINDING_MISMATCH', 'Full Clean result is not bound to the exact activation operation and epoch.');
    }
    const epoch = this.fullCleanActivation.current();
    const epochOperationId = typeof epoch?.operation_id === 'string' ? epoch.operation_id : '';
    const epochId = typeof epoch?.activation_epoch_id === 'string' ? epoch.activation_epoch_id : '';
    const expiresAtUnixMs = Number(epoch?.expires_at_unix_ms || epoch?.metadata?.expires_at_unix_ms || 0);
    if (epochOperationId !== operationId || epochId !== returnedEpochId) {
      throw activationError('ACTIVATION_EPOCH_BINDING_MISMATCH', 'Full Clean durable epoch identity does not match the returned activation result.');
    }
    return this.actions.bindDurableEpoch(operationId, {
      operation_id: epochOperationId,
      activation_epoch_id: epochId,
      expires_at_unix_ms: expiresAtUnixMs
    });
  }

  async activateFullClean(request, { replay = false } = {}) {
    const operationId = request.operation_id;
    try {
      // The authenticated request remains a short-lived admission credential.
      // Once it has admitted an exact Full Clean transaction, the durable epoch
      // owns the longer bounded replacement lifetime.  Do not collapse those
      // two clocks by forwarding the request deadline into the epoch creator.
      if (!replay) ensureActivationFresh(request, this.now());
      const result = await this.fullCleanActivation.restart({
        operationId,
        component: request.component,
        expectedDiskRevision: request.expected_disk_revision,
        sourceCheckpoint: request.source_checkpoint,
        allowAcceptancePending: request.allow_acceptance_pending,
        // A replay carries the already-linked epoch; the coordinator must
        // reconcile it instead of creating a second activation transaction.
        ...(replay ? {
          activationEpochId: String(this.actions.get(operationId)?.activation_epoch_id
            || this.actions.get(operationId)?.result?.activation_epoch_id || '').trim() || undefined
        } : {}),
        reason: `component_revision:${request.component}`
      });
      if (!['completed', 'failed', 'refused'].includes(String(result?.state || ''))) {
        this.bindFullCleanEpoch(operationId, result);
      }
      const record = this.actions.get(operationId);
      if (record) return { ...record, ...(replay ? { deduplicated: true } : {}) };
      return result;
    } catch (error) {
      const record = this.finishCoordinatorFailure(operationId, error);
      if (record) return record;
      throw error;
    }
  }

  async activate(input) {
    const now = this.now();
    const replayRequest = normalizeActivationRequest(input, now, { allowExpiredReplay: true });
    const replay = this.actions.replay(replayRequest);
    const resumableStopped = replay?.state === 'accepted'
      && replay?.component === 'coding_mcp'
      && replay?.result?.component_stopped === true;
    if (replay && !resumableStopped) {
      if (this.hasFullCleanCoordinator() && replay.state === 'accepted') {
        return this.activateFullClean(replayRequest, { replay: true });
      }
      return { ...replay, deduplicated: true };
    }
    const request = normalizeActivationRequest(input, now);
    if (request.full_clean_required && !this.hasFullCleanCoordinator()) {
      // Preserve a durable refusal record for status polling, but never invoke
      // the legacy component-scoped branch on a request that explicitly asks
      // for a full-system transaction.
      const claim = this.actions.begin(request);
      if (!claim.created) return { ...claim.record, deduplicated: true };
      return this.actions.finish(request.operation_id, 'refused', null, {
        code: 'RECOVERY_HOST_UPGRADE_REQUIRED',
        message: 'The authenticated Recovery Host is stale or lacks the full-clean coordinator; bootstrap a current replacement before activation.'
      });
    }
    // A revision activation is a system transaction when the Recovery Host
    // has the full-clean coordinator.  Keep the component-scoped path as a
    // compatibility fallback for isolated/unit hosts and legacy callers.
    // Production RecoveryHost instances expose the epoch completion control
    // method on RuntimeOrchestrator.  Keep isolated/unit hosts that provide a
    // deliberately minimal orchestrator on the historical component-scoped
    // path; otherwise merely constructing a coordinator would silently change
    // their activation contract and make a replacement handoff impossible to
    // exercise without the full runtime authority surface.
    let claim;
    if (resumableStopped) {
      this.actions.resume(request.operation_id);
      claim = { created: true, record: this.actions.get(request.operation_id) };
    } else {
      claim = this.actions.begin(request);
      if (!claim.created) return { ...claim.record, deduplicated: true };
    }
    if (this.hasFullCleanCoordinator()) {
      return this.activateFullClean(request);
    }
    let revision;
    let lifecycle = null;
    const startedAt = new Date(this.now()).toISOString();
    let fencePrepared = false;
    try {
      revision = this.validateExpectedRevision(request);
      const oldEvidence = await this.componentInstanceEvidence(request.component);
      const oldInstanceId = oldEvidence.instanceId;
      const oldInstanceState = oldEvidence.state;
      this.actions.annotate(request.operation_id, {
        started_at: startedAt,
        old_instance_id: oldInstanceId,
        old_instance_state: oldInstanceState
      });
      const inspection = await this.orchestrator.inspectCodeActivation();
      ensureActivationFresh(request, this.now());
      if (inspection.code === 'COMPONENT_STOPPED' && request.component === 'coding_mcp') {
        lifecycle = lifecycleDecision(inspection, request, new Date(this.now()).toISOString());
        this.actions.annotate(request.operation_id, { lifecycle_decision: lifecycle });
        const stoppedStatus = this.componentRevisionStatus('coding_mcp', { force: true });
        const completedAt = new Date(this.now()).toISOString();
        const postflight = activationPostflight(request, {
          oldInstanceId,
          oldInstanceState: oldInstanceState || 'ABSENT',
          newInstanceId: null,
          runningRevision: stoppedStatus.running_revision,
          diskRevision: stoppedStatus.disk_revision || request.expected_disk_revision,
          startedAt,
          completedAt,
          healthVerified: false,
          lifecycle
        });
        return this.actions.defer(request.operation_id, {
          activated: false,
          component_stopped: true,
          next_start_revision: request.expected_disk_revision,
          postflight
        }, {
          code: 'COMPONENT_AWAITING_START',
          message: 'Coding MCP is stopped; activation remains resumable until a fresh instance starts.'
        });
      }
      if (inspection.code === 'COMPONENT_STOPPED') {
        return this.actions.finish(request.operation_id, 'refused', null, {
          code: 'ORCHESTRATION_STATE_UNCERTAIN',
          message: 'Canonical lifecycle evidence is unavailable while Coding MCP is stopped.'
        });
      }
      if (!inspection.safe && !(inspection.code === 'ACCEPTANCE_PENDING' && request.allow_acceptance_pending)) {
        return this.actions.finish(request.operation_id, 'refused', null, {
          code: inspection.code || 'ORCHESTRATION_STATE_UNCERTAIN',
          message: `Activation refused: ${inspection.reason || 'runtime preflight failed'}`
        });
      }
      const preflight = await this.orchestrator.prepareCodeActivation({
        operationId: request.operation_id,
        expiresAtUnixMs: Math.min(request.expires_at_unix_ms, this.now() + 55_000),
        allowAcceptancePending: request.allow_acceptance_pending,
        sourceCheckpoint: request.source_checkpoint
      });
      fencePrepared = preflight?.fenced === true;
      lifecycle = lifecycleDecision(preflight, request, new Date(this.now()).toISOString());
      const preflightBound = verifiedLifecycleResponse(preflight, request, { fenced: true })
        && fencePrepared
        && preflight.fence_operation_id === request.operation_id
        && lifecycle.source_checkpoint_verified === true;
      if (!preflightBound) {
        if (fencePrepared) await this.orchestrator.cancelCodeActivation(request.operation_id).catch(() => false);
        return this.actions.finish(request.operation_id, 'refused', null, {
          code: preflight?.safe === false
            ? preflight.code || 'ORCHESTRATION_STATE_UNCERTAIN'
            : 'ACTIVATION_PREFLIGHT_UNVERIFIED',
          message: `Activation refused: ${preflight?.reason || 'checkpoint-bound activation fence was not verified'}`
        });
      }
      this.actions.annotate(request.operation_id, { lifecycle_decision: lifecycle });

      if (revision.running_revision === revision.disk_revision) {
        const current = this.validateExpectedRevision(request);
        const currentEvidence = await this.componentInstanceEvidence(request.component);
        const currentInstanceId = currentEvidence.instanceId || oldInstanceId;
        const completedAt = new Date(this.now()).toISOString();
        const postflight = await this.releaseFenceAndBuildPostflight(request, {
          oldInstanceId: currentInstanceId,
          oldInstanceState: currentEvidence.state || oldInstanceState,
          newInstanceId: currentInstanceId,
          runningRevision: current.running_revision,
          diskRevision: current.disk_revision,
          startedAt,
          completedAt,
          healthVerified: Boolean(currentInstanceId && current.running_revision === current.disk_revision),
          alreadyCurrent: true
        });
        return this.actions.finish(request.operation_id, 'completed', {
          activated: false,
          already_current: true,
          revision: current.disk_revision,
          postflight
        });
      }

      if (request.component === 'electron_ui') {
        ensureActivationFresh(request, this.now());
        if (!this.uiPresence().alive) {
          if (typeof this.spawnElectronUi !== 'function') {
            await this.orchestrator.cancelCodeActivation(request.operation_id).catch(() => false);
            return this.actions.finish(request.operation_id, 'failed', null, {
              code: 'UI_REPLACEMENT_UNAVAILABLE',
              message: 'Electron UI replacement launcher is unavailable.'
            });
          }
          await this.spawnElectronUi({ expiresAtUnixMs: request.expires_at_unix_ms });
        }
        return this.actions.get(request.operation_id);
      }

      if (request.component === 'coding_mcp') {
        ensureActivationFresh(request, this.now());
        const result = await this.orchestrator.activateCodingMcpUpdate(request.expected_disk_revision, {
          expiresAtUnixMs: request.expires_at_unix_ms
        });
        const current = this.componentRevisionStatus('coding_mcp', { force: true });
        const completedAt = new Date(this.now()).toISOString();
        const postflight = await this.releaseFenceAndBuildPostflight(request, {
          oldInstanceState: OLD_INSTANCE_STATES[1],
          oldInstanceId: result.old_instance_id || oldInstanceId,
          newInstanceId: result.new_instance_id,
          runningRevision: current.running_revision || result.new_revision,
          diskRevision: current.disk_revision,
          startedAt,
          completedAt,
          healthVerified: result.health_verified === true
        });
        const payload = { activated: true, ...result, postflight };
        return postflight.postflight_verified
          ? this.actions.finish(request.operation_id, 'completed', payload)
          : this.actions.finish(request.operation_id, 'failed', payload, {
            code: 'POSTFLIGHT_UNVERIFIED',
            message: 'Coding MCP replacement did not satisfy the checkpoint-bound postflight contract.'
          });
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
      await this.orchestrator.cancelCodeActivation(request.operation_id).catch(() => false);
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
    const epochId = String(record.activation_epoch_id || record.result?.activation_epoch_id || '').trim();
    if (!epochId || !this.fullCleanActivation?.current) return record;
    try {
      const epoch = this.fullCleanActivation.current();
      if (!epoch || epoch.activation_epoch_id !== epochId) return record;
      return { ...record, activation_epoch: epoch };
    } catch (error) {
      return {
        ...record,
        activation_epoch: {
          activation_epoch_id: epochId,
          state: 'UPDATE_INCOMPLETE',
          admission_state: 'CLOSED',
          error: { code: String(error?.code || 'ACTIVATION_EPOCH_STORE_INVALID'), message: String(error?.message || error) }
        }
      };
    }
  }

  async registerUi(input) {
    const value = exactObject(input, new Set(['instance_id', 'pid', 'revision', 'started_at_unix_ms', 'activation_epoch_id']), 'UI registration');
    const registration = {
      instance_id: String(value.instance_id || ''),
      pid: Number(value.pid || 0),
      revision: String(value.revision || '').toLowerCase(),
      started_at_unix_ms: Number(value.started_at_unix_ms || 0),
      activation_epoch_id: String(value.activation_epoch_id || '').trim() || null,
      registered_at_unix_ms: this.now()
    };
    if (!INSTANCE_ID_PATTERN.test(registration.instance_id) || !Number.isSafeInteger(registration.pid) || registration.pid <= 0
      || !REVISION_PATTERN.test(registration.revision) || !Number.isSafeInteger(registration.started_at_unix_ms)
      || registration.started_at_unix_ms > this.now() + CLOCK_SKEW_MS) {
      throw activationError('INVALID_UI_REGISTRATION', 'Electron UI registration is invalid.');
    }
    let observed;
    try { observed = await this.asyncProcessIdentityObserver(registration.pid); }
    catch (error) {
      throw activationError('UI_PROCESS_IDENTITY_UNVERIFIED', 'Electron UI process creation identity is unavailable.', {
        pid: registration.pid,
        cause_code: error?.code || ''
      });
    }
    if (observed?.state !== 'live') {
      throw activationError('UI_PROCESS_IDENTITY_UNVERIFIED', 'Electron UI process creation identity is unavailable.', {
        pid: registration.pid,
        observed_state: observed?.state || null
      });
    }
    try {
      const identity = processIdentityFrom({
        pid: registration.pid,
        process_start_token: observed.process_start_token
      });
      registration.process_start_token = identity.process_start_token;
    } catch (error) {
      throw activationError('UI_PROCESS_IDENTITY_UNVERIFIED', 'Electron UI process creation identity is unavailable.', {
        pid: registration.pid,
        cause_code: error?.code || ''
      });
    }
    this.uiRegistration = registration;
    const verifiedPresence = {
      tracked: true,
      alive: true,
      instance_id: registration.instance_id,
      activation_epoch_id: registration.activation_epoch_id,
      pid: registration.pid,
      process_start_token: registration.process_start_token,
      registered_at_unix_ms: registration.registered_at_unix_ms,
      observed_at_unix_ms: this.now()
    };
    this.lastUiPresence = verifiedPresence;
    const verifiedRevision = (options = {}) => this.uiRevisionStatus({
      ...options,
      presence: verifiedPresence,
      preferCachedPresence: true
    });
    const epoch = this.fullCleanActivation?.current?.();
    if (epoch) {
      const epochMatches = registration.activation_epoch_id && registration.activation_epoch_id === epoch.activation_epoch_id;
      if (!epochMatches) {
        return {
          registered: true,
          restart_required: true,
          activation_epoch_id: epoch.activation_epoch_id,
          expected_activation_epoch_id: epoch.activation_epoch_id,
          code: 'UPDATE_INCOMPLETE',
          code_revision: verifiedRevision()
        };
      }
      this.fullCleanActivation.uiRegistration = registration;
      if (epoch.state !== 'READY') {
        return {
          registered: true,
          restart_required: false,
          activation_epoch_id: epoch.activation_epoch_id,
          code_revision: verifiedRevision()
        };
      }
    }
    if (this.uiRecoveryPreference?.suppressed || this.uiRecoveryPreference?.error_code) {
      this.writeUiRecoveryPreference(false, '');
    }
    const pending = this.actions.load().actions.find((item) => (
      item.component === 'electron_ui'
      && item.state === 'accepted'
      && Number(item.expires_at_unix_ms || 0) > this.now()
    )) || null;
    if (!pending) return { registered: true, restart_required: false, code_revision: verifiedRevision() };
    if (pending.expected_disk_revision !== registration.revision) {
      if (!pending.old_instance_id) this.actions.annotate(pending.operation_id, { old_instance_id: registration.instance_id });
      return {
        registered: true,
        restart_required: true,
        operation_id: pending.operation_id,
        expires_at_unix_ms: Number(pending.expires_at_unix_ms || 0),
        expected_revision: pending.expected_disk_revision,
        code_revision: verifiedRevision()
      };
    }
    const refreshed = this.actions.get(pending.operation_id) || pending;
    const request = {
      operation_id: pending.operation_id,
      component: 'electron_ui',
      expected_disk_revision: refreshed.expected_disk_revision,
      source_checkpoint: refreshed.source_checkpoint || null
    };
    const revision = verifiedRevision({ force: true });
    const completedAt = new Date(this.now()).toISOString();
    let postflight;
    try {
      postflight = await this.releaseFenceAndBuildPostflight(request, {
        oldInstanceState: refreshed.old_instance_state,
        oldInstanceId: refreshed.old_instance_id,
        newInstanceId: registration.instance_id,
        runningRevision: revision.running_revision,
        diskRevision: revision.disk_revision,
        startedAt: refreshed.started_at,
        completedAt,
        healthVerified: verifiedPresence.alive
      });
    } catch (error) {
      const failed = this.actions.finish(pending.operation_id, 'failed', null, {
        code: String(error?.code || 'POSTFLIGHT_LIFECYCLE_UNVERIFIED'),
        message: String(error?.message || 'Electron UI postflight lifecycle verification failed.')
      });
      return { registered: true, restart_required: true, activation: failed, code_revision: revision };
    }
    const result = {
      activated: true,
      old_instance_id: refreshed.old_instance_id,
      new_instance_id: registration.instance_id,
      new_revision: registration.revision,
      health_verified: postflight.health_verified,
      postflight
    };
    const completed = postflight.postflight_verified
      ? this.actions.finish(pending.operation_id, 'completed', result)
      : this.actions.finish(pending.operation_id, 'failed', result, {
        code: revision.disk_revision !== pending.expected_disk_revision
          ? 'REVISION_CHANGED_DURING_ACTIVATION'
          : (!refreshed.old_instance_id || refreshed.old_instance_id === registration.instance_id)
            ? 'ACTIVATION_IDENTITY_UNCHANGED'
            : 'POSTFLIGHT_UNVERIFIED',
        message: 'Electron UI registration did not satisfy the checkpoint-bound postflight contract.'
      });
    return {
      registered: true,
      restart_required: completed.state !== 'completed',
      activation: completed,
      code_revision: revision
    };
  }

  verifyRecoveryReplacement(operationId) {
    const record = this.actions.get(operationId);
    if (!record || record.component !== 'recovery_host' || record.state !== 'accepted') {
      throw activationError('ACTIVATION_OPERATION_MISMATCH', 'Recovery replacement operation is not pending.');
    }
    const revision = this.recoveryRevisionStatus({ force: true });
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
    const { record, revision, revisionContract } = this.verifyRecoveryReplacement(operationId);
    if (!record.old_instance_id || String(record.old_instance_id) === String(this.recoveryInstanceId || '')) {
      throw activationError('ACTIVATION_IDENTITY_UNCHANGED', 'Recovery Host replacement did not produce a new verified instance identity.');
    }
    if (String(oldInstanceId || '') !== String(record.old_instance_id || '')) {
      throw activationError('ACTIVATION_OPERATION_MISMATCH', 'Recovery Host replacement old instance does not match the durable activation record.');
    }
    const request = {
      operation_id: operationId,
      component: 'recovery_host',
      expected_disk_revision: record.expected_disk_revision,
      source_checkpoint: record.source_checkpoint || null
    };
    const completedAt = new Date(this.now()).toISOString();
    const postflight = await this.releaseFenceAndBuildPostflight(request, {
      oldInstanceState: record.old_instance_state,
      oldInstanceId: record.old_instance_id,
      newInstanceId: this.recoveryInstanceId,
      runningRevision: revision.running_revision,
      diskRevision: revision.disk_revision,
      startedAt: record.started_at,
      completedAt,
      healthVerified: true,
      revisionContract
    });
    const result = {
      activated: true,
      old_instance_id: record.old_instance_id,
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
      },
      postflight
    };
    return postflight.postflight_verified
      ? this.actions.finish(operationId, 'completed', result)
      : this.actions.finish(operationId, 'failed', result, {
        code: 'POSTFLIGHT_UNVERIFIED',
        message: 'Recovery Host replacement did not satisfy the checkpoint-bound postflight contract.'
      });
  }
}

module.exports = {
  RecoveryActivation,
  normalizeActivationRequest,
  normalizeSourceCheckpoint,
  activationPostflight,
  lifecycleDecision,
  COMPONENTS,
  REVISION_PATTERN,
  MAX_REQUEST_TTL_MS,
  UI_RECOVERY_EXIT_REASONS
};
