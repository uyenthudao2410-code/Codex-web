const crypto = require('node:crypto');
const fs = require('node:fs');
const { RuntimeOrchestrator } = require('./runtimeOrchestrator');
const { RecoveryPlaneService } = require('./recoveryPlaneService');
const { HealthService } = require('./healthService');
const { HubProxyGateway } = require('./hubProxyGateway');
const { RecoveryIpcServer } = require('./recoveryIpc');
const { ensureParent } = require('./jsonStore');
const { loadOrCreateDeviceIdentity, normalizeDeviceIdentity } = require('./deviceIdentity');
const { ComponentRevisionTracker } = require('./componentRevision');
const { RecoveryActivation } = require('./recoveryActivation');
const { AcceptedCodeActivationController } = require('./recoveryActionStore');
const { computeActivationClosure } = require('./activationClosure');
const { FullCleanActivation } = require('./fullCleanActivation');
const { ActivationEpochStore, ACTIVE_STATES } = require('./activationEpoch');
const { run } = require('./commandRunner');

const SUPERVISION_INTERVAL_MS = 5000;
const REPLACEMENT_WAIT_MS = 15_000;
const HANDOFF_SUPERVISION_DRAIN_MS = 10_000;
const UI_RECOVERY_REGISTRATION_TIMEOUT_MS = 15_000;
const UI_RECOVERY_COOLDOWN_MS = 20_000;
const UI_RECOVERY_WINDOW_MS = 10 * 60_000;
const UI_RECOVERY_ATTEMPT_LIMIT = 4;
const UI_RECOVERY_CIRCUIT_BREAK_MS = 5 * 60_000;

function wait(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

function isProcessAlive(pid) {
  if (!Number.isInteger(Number(pid)) || Number(pid) <= 0) return false;
  try { process.kill(Number(pid), 0); return true; } catch { return false; }
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
    connectorRediscoveredAt: status?.connectorRediscoveredAt,
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
    deviceIdentity = null
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
    this.lastRecoveryPlaneStatus = null;
    this.ownsLock = false;
    this.running = false;
    this.replacement = replacement;
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
        if (!pid || pid === process.pid) throw Object.assign(new Error('Refused to terminate an unverified Electron UI owner.'), { code: 'UI_RECOVERY_INSTANCE_MISMATCH' });
        if (process.platform === 'win32') {
          const result = await run('taskkill.exe', ['/PID', String(pid), '/T', '/F'], { allowFailure: true });
          if (Number(result?.code) !== 0) {
            throw Object.assign(new Error('Electron UI termination command failed.'), {
              code: 'UI_TERMINATION_FAILED',
              details: { pid, exit_code: result?.code ?? null }
            });
          }
        } else {
          try { process.kill(pid, 'SIGTERM'); } catch (error) {
            if (error?.code !== 'ESRCH') throw Object.assign(error, { code: 'UI_TERMINATION_FAILED' });
          }
        }
        const deadline = Date.now() + 5000;
        while (isProcessAlive(pid) && Date.now() < deadline) await wait(50);
        if (isProcessAlive(pid)) {
          throw Object.assign(new Error('Electron UI process remained alive after termination request.'), {
            code: 'UI_TERMINATION_FAILED',
            details: { pid }
          });
        }
        return true;
      },
      scheduleHandoff: (epochId, details) => this.scheduleFullCleanHandoff(epochId, details),
      epochStore: this.activationEpochStore
    });
    this.activation.fullCleanActivation = this.fullCleanActivation;
    this.orchestrator.setFullCleanActivation?.(this.fullCleanActivation);
    if (replacement?.activationEpochId) this.orchestrator.setActivationEpoch?.(replacement.activationEpochId);
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

  uiRecoveryStatus() {
    const now = Date.now();
    const preference = this.activation.uiRecoveryPreferenceStatus();
    const presence = this.activation.uiPresence();
    this.uiRecoveryAttempts = this.uiRecoveryAttempts.filter((time) => time >= now - UI_RECOVERY_WINDOW_MS);
    let state = this.uiRecoveryLastState;
    if (preference.suppressed) state = 'suppressed';
    else if (presence.alive) state = 'healthy';
    else if (this.activation.hasPendingUiActivation()) state = 'activation_pending';
    else if (!presence.tracked && this.uiRecoveryInitialGraceUntil > now) state = 'awaiting_initial_registration';
    else if (this.uiRecoveryCircuitUntil > now) state = 'circuit_suppressed';
    else if (this.uiRecoveryPendingUntil > now) state = 'waiting_for_registration';
    else if (this.uiRecoveryNextAttemptAt > now) state = 'cooldown';
    else if (!presence.alive) state = 'missing';
    return {
      state,
      registered: presence.tracked,
      alive: presence.alive,
      pid: presence.pid || null,
      instance_id: presence.instance_id || null,
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
      const presence = this.activation.uiPresence();
      this.uiRecoveryAttempts = this.uiRecoveryAttempts.filter((time) => time >= now - UI_RECOVERY_WINDOW_MS);
      if (preference.suppressed) {
        this.uiRecoveryLastState = 'suppressed';
        return this.uiRecoveryStatus();
      }
      if (presence.alive) {
        this.resetUiRecoveryTracking('healthy');
        return this.uiRecoveryStatus();
      }
      if (this.activation.hasPendingUiActivation()) {
        this.uiRecoveryLastState = 'activation_pending';
        return this.uiRecoveryStatus();
      }
      if (!presence.tracked && this.uiRecoveryInitialGraceUntil > now) {
        this.uiRecoveryLastState = 'awaiting_initial_registration';
        return this.uiRecoveryStatus();
      }
      if (typeof this.spawnElectronUi !== 'function') {
        this.uiRecoveryLastState = 'unavailable';
        this.uiRecoveryLastErrorCode = 'UI_RECOVERY_LAUNCHER_UNAVAILABLE';
        return this.uiRecoveryStatus();
      }
      if (this.uiRecoveryCircuitUntil > now) {
        this.uiRecoveryLastState = 'circuit_suppressed';
        return this.uiRecoveryStatus();
      }
      if (this.uiRecoveryPendingUntil > now) {
        this.uiRecoveryLastState = 'waiting_for_registration';
        return this.uiRecoveryStatus();
      }
      if (this.uiRecoveryNextAttemptAt > now) {
        this.uiRecoveryLastState = 'cooldown';
        return this.uiRecoveryStatus();
      }
      if (this.uiRecoveryAttempts.length >= UI_RECOVERY_ATTEMPT_LIMIT) {
        this.uiRecoveryCircuitUntil = now + UI_RECOVERY_CIRCUIT_BREAK_MS;
        this.uiRecoveryLastState = 'circuit_suppressed';
        return this.uiRecoveryStatus();
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
      return this.uiRecoveryStatus();
    })();
    this.uiRecoveryLaunchInFlight = operation;
    try {
      return await operation;
    } finally {
      if (this.uiRecoveryLaunchInFlight === operation) this.uiRecoveryLaunchInFlight = null;
    }
  }

  hostStatus() {
    let codeRevision;
    try {
      codeRevision = this.revisions.status('recovery_host', this.recoveryHostRunningRevision, { force: true });
    } catch (error) {
      codeRevision = {
        running_revision: this.recoveryHostRunningRevision || null,
        disk_revision: null,
        update_pending: null,
        state: 'unavailable',
        error_code: String(error?.code || 'REVISION_UNAVAILABLE')
      };
    }
    const electronUiRevision = this.activation.uiRevisionStatus({ force: true });
    const autoActivation = this.autoActivation?.status?.() || null;
    let codingMcpRevision = {};
    try { codingMcpRevision = this.orchestrator.codingMcpRevisionStatus?.({ force: true }) || {}; } catch {}
    let activationEpoch = null;
    try { activationEpoch = this.fullCleanActivation?.current?.() || null; } catch (error) {
      activationEpoch = { state: 'UPDATE_INCOMPLETE', admission_state: 'CLOSED', error: { code: String(error?.code || 'ACTIVATION_EPOCH_STORE_INVALID'), message: String(error?.message || error) } };
    }
    const epochStatus = this.orchestrator.activationEpochStatus?.() || {
      activation_epoch_id: activationEpoch?.activation_epoch_id || null,
      state: activationEpoch?.state || 'NONE',
      admission_open: !activationEpoch || activationEpoch.state === 'READY',
      update_incomplete: Boolean(activationEpoch && activationEpoch.state !== 'READY')
    };
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
      state: this.running ? 'healthy' : 'starting',
      pid: process.pid,
      instance_id: this.instanceId,
      device_id: this.deviceIdentity.device_id,
      device_instance_id: this.deviceInstanceId,
      device_display_name: this.deviceIdentity.display_name,
      started_at: this.startedAt,
      watchdog_interval_ms: SUPERVISION_INTERVAL_MS,
      gateway: this.gateway?.server ? 'healthy' : 'stopped',
      gateway_metrics: this.gateway?.metrics?.() || null,
      code_revision: codeRevision,
      electron_ui_revision: electronUiRevision,
      electron_ui_recovery: this.uiRecoveryStatus(),
      auto_activation: autoActivation,
      activation_closure: activationClosure,
      activation_epoch: epochStatus,
      recovery_plane_mode: 'independent_mcp_tunnel_v1',
      recovery_plane: this.lastRecoveryPlaneStatus,
      last_progress: this.lastProgress,
      runtime: this.lastSupervisionStatus ? {
        mcp: Boolean(this.lastSupervisionStatus.mcpRunning),
        tunnel: Boolean(this.lastSupervisionStatus.tunnelRunning),
        fully_ready: Boolean(this.lastSupervisionStatus.fullyReady && epochStatus.admission_open !== false),
        update_incomplete: Boolean(epochStatus.update_incomplete),
        activation_epoch_id: epochStatus.activation_epoch_id || null,
        recovering: Boolean(this.lastSupervisionStatus.recovering),
        recovery_blocked: Boolean(this.lastSupervisionStatus.recoveryBlocked)
      } : null
    };
  }

  decorate(value) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return value;
    const recoveryHost = this.hostStatus();
    const activationClosure = activationClosureProjection({
      autoActivation: recoveryHost.auto_activation,
      recoveryHostRevision: recoveryHost.code_revision,
      electronUiRevision: recoveryHost.electron_ui_revision,
      codingMcpRevision: (() => {
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
      epochStatus = this.orchestrator.activationEpochStatus?.() || this.fullCleanActivation?.current?.() || null;
    } catch (error) {
      epochStatus = { state: 'UPDATE_INCOMPLETE', admission_open: false, update_incomplete: true, error_code: String(error?.code || 'ACTIVATION_EPOCH_STORE_INVALID') };
    }
    const incomplete = Boolean(epochStatus && (epochStatus.update_incomplete === true || (epochStatus.state && epochStatus.state !== 'READY')));
    if (status && incomplete) status.fullyReady = false;
    if (value && incomplete) value.fullyReady = false;
    return { ...value, ...(status ? { status } : {}), activationClosure, activationEpoch: epochStatus, updateIncomplete: incomplete, device: { ...device, scope: 'current_device_only', registry: 'local', device_id: this.deviceIdentity.device_id, device_instance_id: this.deviceInstanceId, display_name: this.deviceIdentity.display_name, online: this.running, workspace: String(device.workspace || value.workspace || currentSettings.workspace || ''), coding, recovery: { host_running: this.running, mcp_running: plane.mcp?.state === 'healthy', tunnel_running: plane.tunnel?.state === 'healthy', tunnel_state: String(plane.tunnel?.state || 'unknown'), tunnel_id: String(currentSettings.recoveryTunnelId || '') || null }, git: device.git || { available: false, branch: null, head: null, head_short: null, dirty: null } }, recoveryHost };
  }

  handlers() {
    return {
      'recovery.ping': async () => ({ ready: this.running, ...this.hostStatus() }),
      'recovery.status': async () => this.hostStatus(),
      'code.activation_preflight': async (request) => this.activation.preflight(request),
      'code.activate_update': async (request) => this.activation.activate(request),
      'code.activation_status': async (operationId) => this.activation.status(operationId),
      'client.register_ui_revision': async (registration) => {
        const result = await this.activation.registerUi(registration);
        this.resetUiRecoveryTracking('healthy');
        return result;
      },
      'client.suppress_ui_recovery': async (intent) => {
        const result = this.activation.suppressUiRecovery(intent);
        this.resetUiRecoveryTracking('suppressed');
        return result;
      },
      'runtime.snapshot': async (options = {}) => this.decorate(await this.orchestrator.snapshot(options)),
      'runtime.lightweight_snapshot': async () => this.decorate(await this.orchestrator.lightweightSnapshot()),
      'runtime.activation_epoch_status': async () => this.orchestrator.activationEpochStatus?.() || { state: 'NONE', admission_open: true, update_incomplete: false },
      'runtime.complete_activation_epoch': async (activationEpochId) => {
        if (!this.fullCleanActivation || typeof this.orchestrator?.completeActivationEpoch !== 'function') {
          throw Object.assign(new Error('Full clean activation is unavailable for this runtime owner.'), { code: 'FULL_CLEAN_ACTIVATION_UNAVAILABLE' });
        }
        const id = String(activationEpochId || '');
        return this.decorate(await this.fullCleanActivation.finalize(id, await this.fullCleanActivation.finalCensus(id)));
      },
      'runtime.start': async (options = {}) => this.decorate(await this.orchestrator.start(options)),
      'runtime.stop': async (options = {}) => this.decorate(await this.orchestrator.stop(options)),
      'runtime.restart': async (options = {}) => {
        const result = options?.automatic === true || options?.mode === 'soft_recovery'
          ? await this.orchestrator.restart({ ...options, automatic: true, mode: 'soft_recovery' })
          : (this.fullCleanActivation?.restart && typeof this.orchestrator?.completeActivationEpoch === 'function'
            ? await this.fullCleanActivation.restart({ ...options, reason: options.reason || 'operator_restart' })
            : await this.orchestrator.restart(options));
        return this.decorate(result);
      },
      'runtime.switch_workspace': async (workspace) => this.decorate(await this.orchestrator.switchWorkspace(workspace)),
      'runtime.update_authorized_roots': async (roots) => this.decorate(await this.orchestrator.updateAuthorizedRoots(roots)),
      'runtime.acknowledge_connector_contract': async () => this.decorate(await this.orchestrator.acknowledgeConnectorContract()),
      'health.inspect': async () => this.healthService.inspect(),
      'health.repair': async () => this.healthService.repair(),
      'logs.read': async (limit = 300) => this.log.read(Math.max(1, Math.min(500, Number(limit) || 300))),
      'logs.clear': async () => { this.log.clear(); return true; }
    };
  }

  async superviseOnce() {
    if (!this.running || this.handoffStarted) return this.lastSupervisionStatus;
    if (this.supervisionInFlight) return this.supervisionInFlight;
    const operation = (async () => {
      let runtime = null;
      let epoch = null;
      try {
        epoch = this.fullCleanActivation.current?.();
      } catch (error) {
        this.log.error(error.message, { stage: 'recovery-host-activation-epoch-read', code: error?.code || '' });
        return this.lastSupervisionStatus;
      }
      const admissionBlocked = Boolean(epoch && epoch.state !== 'READY');
      try {
        // During a full-clean transaction the coordinator is the sole owner of
        // component mutation.  The normal watchdog must not restart MCP/Tunnel
        // (or consume a supervisor ticket) while the epoch is assembling.
        // Any non-READY durable epoch (including FAILED/expired epochs) keeps
        // admission closed.  The ordinary watchdog must not mutate MCP,
        // Tunnel, Recovery Plane, or consume restart tickets in that state;
        // only the explicit activation coordinator may advance it.
        runtime = admissionBlocked
          ? await this.orchestrator.lightweightSnapshot()
          : await this.orchestrator.supervise();
        this.lastSupervisionStatus = runtime;
      } catch (error) {
        this.log.error(error.message, { stage: 'recovery-host-supervise' });
      }
      if (epoch && ['STARTING', 'VERIFYING', 'HANDOFF', 'FROZEN', 'STOPPING', 'ADMISSION_CLOSED', 'PREPARING'].includes(epoch.state)) {
        try {
          const census = await this.fullCleanActivation.finalCensus(epoch.activation_epoch_id, {
            expectedOldInstanceId: this.replacement?.expectedOldInstanceId || ''
          });
          if (census.pass) {
            const completed = await this.fullCleanActivation.finalize(epoch.activation_epoch_id, census);
            this.lastSupervisionStatus = { ...(this.lastSupervisionStatus || {}), fullCleanActivation: completed };
          }
        } catch (error) {
          this.log.warn(error.message, { stage: 'full-clean-activation-census', code: error?.code || '' });
        }
      }
      // Recovery plane and UI repair are also component mutations.  They are
      // intentionally suppressed while admission is blocked; the replacement
      // coordinator performs the one required start/observation sequence.
      if (!admissionBlocked) {
        await this.ensureRecoveryPlane();
        await this.superviseElectronUi();
      }
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
    let replacementEpochId = String(this.replacement?.activationEpochId || '').trim();
    let fullCleanReplacement = Boolean(replacementEpochId);
    let recoveredFromDurableEpoch = false;
    // A FAILED epoch is terminal and keeps admission closed, but it must not
    // brick the Recovery Host itself.  Keep the control plane alive so the
    // operator can submit a new explicit full-clean activation.  Component
    // startup/recovery remains suppressed below until that new epoch reaches
    // READY; a failed transaction must never be auto-healed by the watchdog.
    const failedEpochBlocked = Boolean(!fullCleanReplacement && durableEpoch && durableEpoch.state === 'FAILED');
    if (failedEpochBlocked) {
      this.log?.warn?.('Recovery Host is serving control-plane IPC with a failed activation epoch; explicit full-clean activation is required.', {
        activationEpochId: durableEpoch.activation_epoch_id
      });
    }
    if (!fullCleanReplacement && durableEpoch && ACTIVE_STATES.has(durableEpoch.state)) {
      const durableExpiry = Number(durableEpoch.expires_at_unix_ms || durableEpoch.metadata?.expires_at_unix_ms || 0);
      if (durableExpiry > 0 && Date.now() >= durableExpiry) {
        const error = Object.assign(new Error('Activation request expired before Recovery Host recovery.'), {
          code: 'ACTIVATION_REQUEST_EXPIRED',
          details: { activation_epoch_id: durableEpoch.activation_epoch_id, expires_at_unix_ms: durableExpiry, process_mutated: false }
        });
        try { this.activationEpochStore.fail(durableEpoch.activation_epoch_id, error); } catch (persistError) {
          this.log?.error?.(persistError.message, { stage: 'recovery-host-expired-epoch-persist', code: persistError?.code || '' });
        }
        throw error;
      }
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
    } else if (!fullCleanReplacement && durableEpoch && durableEpoch.state === 'READY') {
      // A READY epoch remains the current activation identity across an
      // ordinary host process restart; child services must use that epoch.
      this.orchestrator.setActivationEpoch?.(durableEpoch.activation_epoch_id);
      this.recoveryPlane?.setActivationEpoch?.(durableEpoch.activation_epoch_id);
    }
    const persistReplacementFailure = (error) => {
      if (!replacementEpochId) return;
      try {
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
      if (this.replacement?.expectedOldInstanceId) {
        await waitForReplacementLockRelease(this.paths, this.replacement.expectedOldInstanceId);
      }
      acquireRecoveryHostLock(this.paths, this.instanceId);
    } catch (error) {
      persistReplacementFailure(error);
      throw error;
    }
    this.ownsLock = true;
    try {
      await this.gateway.start();
      this.ipcServer = this.ipcServerFactory({
        paths: this.paths,
        handlers: this.handlers(),
        log: this.log,
        instanceId: this.instanceId,
        startedAt: this.startedAt,
        deviceIdentity: this.deviceIdentity,
        deviceInstanceId: this.deviceInstanceId,
        activationEpochId: this.orchestrator.activationEpochId || this.fullCleanActivation.current?.()?.activation_epoch_id || ''
      });
      await this.ipcServer.start();
      this.running = true;
      if (fullCleanReplacement) {
        await this.fullCleanActivation.continueReplacement({
          activationEpochId: this.replacement.activationEpochId,
          expectedOldInstanceId: this.replacement.expectedOldInstanceId,
          expiresAtUnixMs: this.replacement.expiresAtUnixMs
        });
        this.lastRecoveryPlaneStatus = this.recoveryPlane?.lastStatus || this.lastRecoveryPlaneStatus;
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
      if (!fullCleanReplacement && !failedEpochBlocked) {
        await this.ensureRecoveryPlane({ legacyMigrationPlan: recoveryLegacyMigration });
      }
      this.supervisionTimer = setInterval(() => { this.superviseOnce(); }, SUPERVISION_INTERVAL_MS);
      this.supervisionTimer.unref();
      this.log.info('Recovery Host đã sở hữu Coding runtime, watchdog và local gateway', {
        hostPid: process.pid,
        hostInstanceId: this.instanceId
      });
      const current = this.settings.load();
      if (!fullCleanReplacement && !failedEpochBlocked && !recoveredFromDurableEpoch && !primaryMigrationFailed && current.autoStartServices && !this.orchestrator.isManuallyStopped()) {
        const observed = await this.orchestrator.lightweightSnapshot().catch(() => null);
        this.lastSupervisionStatus = observed;
        if (!observed?.nativeAlive && !observed?.tunnelRunning) {
          this.orchestrator.start({ automatic: true }).catch((error) => {
            this.log.error(error.message, { stage: 'recovery-host-auto-start' });
          });
        }
      }
      const postStartEpoch = this.fullCleanActivation.current?.();
      if (!postStartEpoch || postStartEpoch.state === 'READY') this.autoActivation?.start?.();
      return this.hostStatus();
    } catch (error) {
      this.autoActivation?.stop?.();
      await this.ipcServer?.stop().catch(() => false);
      await this.gateway?.stop().catch(() => false);
      if (this.ownsLock) releaseRecoveryHostLock(this.paths, this.instanceId);
      this.ownsLock = false;
      persistReplacementFailure(error);
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
  HANDOFF_SUPERVISION_DRAIN_MS,
  UI_RECOVERY_REGISTRATION_TIMEOUT_MS,
  UI_RECOVERY_COOLDOWN_MS,
  UI_RECOVERY_ATTEMPT_LIMIT,
  waitForReplacementLockRelease,
  activationClosureProjection
};
