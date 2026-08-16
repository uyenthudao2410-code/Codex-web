const crypto = require('node:crypto');
const fs = require('node:fs');
const { RuntimeOrchestrator } = require('./runtimeOrchestrator');
const { HealthService } = require('./healthService');
const { HubProxyGateway } = require('./hubProxyGateway');
const { RecoveryIpcServer } = require('./recoveryIpc');
const { ensureParent } = require('./jsonStore');
const { ComponentRevisionTracker } = require('./componentRevision');
const { RecoveryActivation } = require('./recoveryActivation');

const SUPERVISION_INTERVAL_MS = 5000;
const REPLACEMENT_WAIT_MS = 15_000;

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
    exitProcess = null, replacement = null
  }) {
    this.paths = paths;
    this.settings = settings;
    this.secrets = secrets;
    this.environment = environment;
    this.log = log;
    this.instanceId = crypto.randomBytes(16).toString('hex');
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
      revisionTracker: this.revisions,
      emitProgress: (payload) => { this.lastProgress = payload; },
      emitStatus: (payload) => { this.lastPublishedStatus = payload; }
    });
    this.healthService = healthService || new HealthService({ settings, secrets, environment, orchestrator: this.orchestrator });
    this.gateway = gateway || new HubProxyGateway({ paths, settings, secrets, log, owner: 'recovery-host' });
    this.ipcServerFactory = ipcServerFactory || ((options) => new RecoveryIpcServer(options));
    this.ipcServer = null;
    this.supervisionTimer = null;
    this.lastSupervisionStatus = null;
    this.ownsLock = false;
    this.running = false;
    this.replacement = replacement;
    this.exitProcess = exitProcess || (() => {});
    this.handoffStarted = false;
    this.replacementWaitMs = REPLACEMENT_WAIT_MS;
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
      started_at: this.startedAt,
      watchdog_interval_ms: SUPERVISION_INTERVAL_MS,
      gateway: this.gateway?.server ? 'healthy' : 'stopped',
      code_revision: codeRevision,
      electron_ui_revision: this.activation.uiRevisionStatus(),
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
    return { ...value, recoveryHost: this.hostStatus() };
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
    try {
      this.lastSupervisionStatus = await this.orchestrator.supervise();
      return this.lastSupervisionStatus;
    } catch (error) {
      this.log.error(error.message, { stage: 'recovery-host-supervise' });
      return null;
    }
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
        startedAt: this.startedAt
      });
      await this.ipcServer.start();
      this.running = true;
      this.supervisionTimer = setInterval(() => { this.superviseOnce(); }, SUPERVISION_INTERVAL_MS);
      this.supervisionTimer.unref();
      this.log.info('Recovery Host đã sở hữu Coding runtime, watchdog và local gateway', {
        hostPid: process.pid,
        hostInstanceId: this.instanceId
      });
      if (this.replacement?.operationId) {
        await this.activation.completeRecoveryReplacement(
          this.replacement.operationId,
          this.replacement.expectedOldInstanceId
        );
      }
      const current = this.settings.load();
      if (current.autoStartServices && !this.orchestrator.isManuallyStopped()) {
        const observed = await this.orchestrator.lightweightSnapshot().catch(() => null);
        this.lastSupervisionStatus = observed;
        if (!observed?.nativeAlive && !observed?.tunnelRunning) {
          this.orchestrator.start({ automatic: true }).catch((error) => {
            this.log.error(error.message, { stage: 'recovery-host-auto-start' });
          });
        }
      }
      return this.hostStatus();
    } catch (error) {
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
  waitForReplacementLockRelease
};
