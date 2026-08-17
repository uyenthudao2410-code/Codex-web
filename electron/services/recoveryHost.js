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

const SUPERVISION_INTERVAL_MS = 5000;
const REPLACEMENT_WAIT_MS = 15_000;
const HANDOFF_SUPERVISION_DRAIN_MS = 10_000;

function wait(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

function isProcessAlive(pid) {
  if (!Number.isInteger(Number(pid)) || Number(pid) <= 0) return false;
  try { process.kill(Number(pid), 0); return true; } catch { return false; }
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
    this.autoActivation = autoActivationController || new AcceptedCodeActivationController({ paths, settings, revisions: this.revisions, activation: this.activation, log });
    this.recoveryPlane = recoveryPlaneService || new RecoveryPlaneService({
      paths,
      log,
      deviceIdentity: this.deviceIdentity,
      deviceInstanceId: this.deviceInstanceId
    });
  }

  hostStatus() {
    let codeRevision;
    try {
      codeRevision = this.revisions.status('recovery_host', this.recoveryHostRunningRevision);
    } catch (error) {
      codeRevision = {
        running_revision: this.recoveryHostRunningRevision || null,
        disk_revision: null,
        update_pending: null,
        state: 'unavailable',
        error_code: String(error?.code || 'REVISION_UNAVAILABLE')
      };
    }
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
      code_revision: codeRevision,
      electron_ui_revision: this.activation.uiRevisionStatus(),
      auto_activation: this.autoActivation?.status?.() || null,
      recovery_plane_mode: 'independent_mcp_tunnel_v1',
      recovery_plane: this.lastRecoveryPlaneStatus,
      last_progress: this.lastProgress,
      runtime: this.lastSupervisionStatus ? {
        mcp: Boolean(this.lastSupervisionStatus.mcpRunning),
        tunnel: Boolean(this.lastSupervisionStatus.tunnelRunning),
        fully_ready: Boolean(this.lastSupervisionStatus.fullyReady),
        recovering: Boolean(this.lastSupervisionStatus.recovering),
        recovery_blocked: Boolean(this.lastSupervisionStatus.recoveryBlocked)
      } : null
    };
  }

  decorate(value) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return value;
    const recoveryHost = this.hostStatus();
    let currentSettings = {};
    try { currentSettings = this.settings.load() || {}; } catch {}
    const device = value.device && typeof value.device === 'object' ? value.device : {};
    const coding = device.coding && typeof device.coding === 'object' ? device.coding : { mcp_running: Boolean(value.mcpRunning ?? value.status?.runtimeRunning), native_alive: Boolean(value.nativeAlive ?? value.status?.runtimeRunning), tunnel_running: Boolean(value.tunnelRunning ?? value.status?.tunnelRunning), tunnel_id: String(currentSettings.tunnelId || '') || null, ownership: 'device_id' };
    const plane = recoveryHost.recovery_plane || {};
    return { ...value, device: { ...device, scope: 'current_device_only', registry: 'local', device_id: this.deviceIdentity.device_id, device_instance_id: this.deviceInstanceId, display_name: this.deviceIdentity.display_name, online: this.running, workspace: String(device.workspace || value.workspace || currentSettings.workspace || ''), coding, recovery: { host_running: this.running, mcp_running: plane.mcp?.state === 'healthy', tunnel_running: plane.tunnel?.state === 'healthy', tunnel_state: String(plane.tunnel?.state || 'unknown'), tunnel_id: String(currentSettings.recoveryTunnelId || '') || null }, git: device.git || { available: false, branch: null, head: null, head_short: null, dirty: null } }, recoveryHost };
  }

  handlers() {
    return {
      'recovery.ping': async () => ({ ready: this.running, ...this.hostStatus() }),
      'recovery.status': async () => this.hostStatus(),
      'code.activation_preflight': async (request) => this.activation.preflight(request),
      'code.activate_update': async (request) => this.activation.activate(request),
      'code.activation_status': async (operationId) => this.activation.status(operationId),
      'client.register_ui_revision': async (registration) => this.activation.registerUi(registration),
      'runtime.snapshot': async (options = {}) => this.decorate(await this.orchestrator.snapshot(options)),
      'runtime.lightweight_snapshot': async () => this.decorate(await this.orchestrator.lightweightSnapshot()),
      'runtime.start': async (options = {}) => this.decorate(await this.orchestrator.start(options)),
      'runtime.stop': async (options = {}) => this.decorate(await this.orchestrator.stop(options)),
      'runtime.restart': async (options = {}) => this.decorate(await this.orchestrator.restart(options)),
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
      try {
        runtime = await this.orchestrator.supervise();
        this.lastSupervisionStatus = runtime;
      } catch (error) {
        this.log.error(error.message, { stage: 'recovery-host-supervise' });
      }
      await this.ensureRecoveryPlane();
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
      this.lastRecoveryPlaneStatus = await this.recoveryPlane.ensure(current, { authToken, runtimeApiKey });
    } catch (error) {
      this.lastRecoveryPlaneStatus = { state: 'unavailable', error_code: String(error?.code || 'RECOVERY_PLANE_UNAVAILABLE'), checked_at: new Date().toISOString() };
      this.log.error(error.message, { stage: 'recovery-plane-supervise', code: this.lastRecoveryPlaneStatus.error_code });
    }
    return this.lastRecoveryPlaneStatus;
  }

  async start() {
    if (this.running) return this.hostStatus();
    if (this.replacement?.expectedOldInstanceId) {
      await waitForReplacementLockRelease(this.paths, this.replacement.expectedOldInstanceId);
    }
    acquireRecoveryHostLock(this.paths, this.instanceId);
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
        deviceInstanceId: this.deviceInstanceId
      });
      await this.ipcServer.start();
      this.running = true;
      let primaryLegacyMigration = { required: false };
      let recoveryLegacyMigration = { required: false };
      if (this.replacement?.operationId) {
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
      await this.ensureRecoveryPlane({ legacyMigrationPlan: recoveryLegacyMigration });
      this.supervisionTimer = setInterval(() => { this.superviseOnce(); }, SUPERVISION_INTERVAL_MS);
      this.supervisionTimer.unref();
      this.log.info('Recovery Host đã sở hữu Coding runtime, watchdog và local gateway', {
        hostPid: process.pid,
        hostInstanceId: this.instanceId
      });
      const current = this.settings.load();
      if (!primaryMigrationFailed && current.autoStartServices && !this.orchestrator.isManuallyStopped()) {
        const observed = await this.orchestrator.lightweightSnapshot().catch(() => null);
        this.lastSupervisionStatus = observed;
        if (!observed?.nativeAlive && !observed?.tunnelRunning) {
          this.orchestrator.start({ automatic: true }).catch((error) => {
            this.log.error(error.message, { stage: 'recovery-host-auto-start' });
          });
        }
      }
      this.autoActivation?.start?.();
      return this.hostStatus();
    } catch (error) {
      this.autoActivation?.stop?.();
      await this.ipcServer?.stop().catch(() => false);
      await this.gateway?.stop().catch(() => false);
      if (this.ownsLock) releaseRecoveryHostLock(this.paths, this.instanceId);
      this.ownsLock = false;
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
  waitForReplacementLockRelease
};
