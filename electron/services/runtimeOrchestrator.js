const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { NativeService, isAlive, runtimeFingerprint, P5_A0_SEED_SECRET } = require('./nativeService');
const { TunnelService } = require('./tunnelService');
const { validateRuntimeSettings, mergeRecentWorkspaces, workspaceKey } = require('./config');
const { canConnect } = require('./environmentService');
const { resolveProxy } = require('./proxyService');
const defaultPaths = require('../paths');
const { readJson, updateJsonAtomic } = require('./jsonStore');
const { ComponentRevisionTracker } = require('./componentRevision');
const { run } = require('./commandRunner');
const { runtimeDeviceIdentity, classifyStoredDeviceOwner } = require('./deviceIdentity');

function wait(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

function assertActivationDeadline(expiresAtUnixMs, boundary, processMutated = false) {
  const expiresAt = Number(expiresAtUnixMs || 0);
  if (expiresAt > 0 && Date.now() >= expiresAt) {
    throw Object.assign(new Error('Activation request expired before process mutation.'), {
      code: 'ACTIVATION_REQUEST_EXPIRED',
      details: { boundary, process_mutated: processMutated }
    });
  }
}

const MAX_DEFERRED_RECOVERIES = 6;
const MAX_SUPERVISOR_REQUEST_AGE_MS = 60_000;

function readMcpHealth(port, token, expectedWorkspace = '', expectedDeviceId = '') {
  return new Promise((resolve) => {
    const request = http.request({
      host: '127.0.0.1',
      port,
      path: '/__control/health',
      method: 'GET',
      headers: { Authorization: `Bearer ${token}` },
      timeout: 1200
    }, (response) => {
      let body = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { if (body.length < 65536) body += chunk; });
      response.on('end', () => {
        if (response.statusCode !== 200) { resolve(null); return; }
        try {
          const payload = JSON.parse(body);
          const workspaceMatches = !expectedWorkspace
            || workspaceKey(payload.workspace) === workspaceKey(expectedWorkspace);
          const deviceMatches = !expectedDeviceId || String(payload.device_id || '').toLowerCase() === String(expectedDeviceId).toLowerCase();
          resolve(payload.ready === true && workspaceMatches && deviceMatches ? payload : null);
        } catch {
          resolve(null);
        }
      });
    });
    request.on('timeout', () => { request.destroy(); resolve(null); });
    request.on('error', () => resolve(null));
    request.end();
  });
}

async function probeMcp(port, token, expectedWorkspace = '', expectedDeviceId = '') {
  return Boolean(await readMcpHealth(port, token, expectedWorkspace, expectedDeviceId));
}

function parseGitStatusPorcelainV2(value) {
  const lines = String(value || '').split(/\r?\n/).filter(Boolean);
  let branch = null;
  let head = null;
  let repo = false;
  let dirty = false;
  for (const line of lines) {
    if (line.startsWith('# branch.head ')) { repo = true; const raw = line.slice('# branch.head '.length).trim(); branch = raw && raw !== '(detached)' ? raw : 'detached'; }
    else if (line.startsWith('# branch.oid ')) { repo = true; const raw = line.slice('# branch.oid '.length).trim(); if (/^[0-9a-f]{40,64}$/i.test(raw)) head = raw.toLowerCase(); }
    else if (!line.startsWith('#')) dirty = true;
  }
  return { available: repo, branch, head, head_short: head ? head.slice(0, 8) : null, dirty: repo ? dirty : null };
}

function parseLoopbackListenerPid(value, port) {
  const target = `127.0.0.1:${Number(port)}`;
  const matches = new Set();
  for (const line of String(value || '').split(/\r?\n/)) {
    const fields = line.trim().split(/\s+/);
    if (fields.length < 5 || String(fields[0]).toUpperCase() !== 'TCP') continue;
    if (fields[1] !== target || String(fields[3]).toUpperCase() !== 'LISTENING') continue;
    const pid = Number(fields[4]);
    if (Number.isInteger(pid) && pid > 0) matches.add(pid);
  }
  return matches.size === 1 ? [...matches][0] : null;
}

async function loopbackListenerPid(port) {
  const result = await run('netstat.exe', ['-ano', '-p', 'tcp'], { allowFailure: true, timeoutMs: 3000 });
  if (result.code !== 0) return null;
  return parseLoopbackListenerPid(result.stdout, port);
}

function readMcpActivationPreflight(port, token) {
  return new Promise((resolve, reject) => {
    const request = http.request({
      host: '127.0.0.1',
      port,
      path: '/__control/activation',
      method: 'GET',
      headers: { Authorization: `Bearer ${token}` },
      timeout: 3000
    }, (response) => {
      let body = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { if (body.length < 65536) body += chunk; });
      response.on('end', () => {
        let parsed = {};
        try { parsed = body ? JSON.parse(body) : {}; } catch { /* handled below */ }
        if (response.statusCode !== 200 || typeof parsed.safe !== 'boolean') {
          reject(Object.assign(new Error('Coding MCP activation preflight is unavailable.'), { code: 'ORCHESTRATION_STATE_UNCERTAIN' }));
          return;
        }
        const workspace = String(parsed.workspace || '').trim();
        if (!workspace) {
          reject(Object.assign(new Error('Coding MCP activation preflight omitted workspace identity.'), { code: 'ORCHESTRATION_STATE_UNCERTAIN' }));
          return;
        }
        resolve({ ...parsed, workspace });
      });
    });
    request.on('timeout', () => request.destroy(Object.assign(new Error('Coding MCP activation preflight timed out.'), { code: 'ORCHESTRATION_STATE_UNCERTAIN' })));
    request.on('error', (error) => reject(Object.assign(error, { code: error.code || 'ORCHESTRATION_STATE_UNCERTAIN' })));
    request.end();
  });
}


function switchMcpWorkspace(port, token, workspace) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({ workspace });
    const request = http.request({
      host: '127.0.0.1',
      port,
      path: '/__control/workspace',
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body)
      },
      timeout: 5000
    }, (response) => {
      let payload = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { if (payload.length < 65536) payload += chunk; });
      response.on('end', () => {
        let parsed = {};
        try { parsed = payload ? JSON.parse(payload) : {}; } catch { /* handled below */ }
        if (response.statusCode !== 200 || parsed.ready !== true) {
          reject(new Error(parsed.error || `Chuyển đổi workspace MCP thất bại (HTTP ${response.statusCode})`));
          return;
        }
        resolve(parsed);
      });
    });
    request.on('timeout', () => { request.destroy(new Error('Quá thời gian chuyển đổi workspace MCP')); });
    request.on('error', reject);
    request.end(body);
  });
}

function setMcpAuthorizedRoots(port, token, roots) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({ roots });
    const request = http.request({
      host: '127.0.0.1',
      port,
      path: '/__control/roots',
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body)
      },
      timeout: 5000
    }, (response) => {
      let payload = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { if (payload.length < 65536) payload += chunk; });
      response.on('end', () => {
        let parsed = {};
        try { parsed = payload ? JSON.parse(payload) : {}; } catch { /* handled below */ }
        if (response.statusCode !== 200 || parsed.ready !== true) {
          reject(new Error(parsed.error || `Cập nhật thư mục ủy quyền MCP thất bại (HTTP ${response.statusCode})`));
          return;
        }
        resolve(parsed);
      });
    });
    request.on('timeout', () => { request.destroy(new Error('Quá thời gian cập nhật thư mục ủy quyền MCP')); });
    request.on('error', reject);
    request.end(body);
  });
}

function controlMcpActivation(port, token, payload) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(payload);
    const request = http.request({
      host: '127.0.0.1',
      port,
      path: '/__control/activation',
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body)
      },
      timeout: 5000
    }, (response) => {
      let responseBody = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { if (responseBody.length < 65536) responseBody += chunk; });
      response.on('end', () => {
        let parsed = {};
        try { parsed = responseBody ? JSON.parse(responseBody) : {}; } catch { /* handled below */ }
        if (response.statusCode !== 200) {
          reject(Object.assign(new Error(String(parsed.error || 'Coding MCP activation preflight failed.')), {
            code: String(parsed.code || 'ORCHESTRATION_STATE_UNCERTAIN'),
            details: parsed.details || parsed
          }));
          return;
        }
        resolve(parsed);
      });
    });
    request.on('timeout', () => request.destroy(Object.assign(new Error('Coding MCP activation preflight timed out.'), { code: 'ORCHESTRATION_STATE_UNCERTAIN' })));
    request.on('error', (error) => reject(Object.assign(error, { code: error.code || 'ORCHESTRATION_STATE_UNCERTAIN' })));
    request.end(body);
  });
}

class RuntimeOrchestrator {
  constructor({ settings, secrets, environment, log, emitProgress, emitStatus = () => {}, paths = defaultPaths, revisionTracker = null, deviceIdentity = null, deviceInstanceId = '' }) {
    this.settingsStore = settings;
    this.secrets = secrets;
    this.environment = environment;
    this.log = log;
    this.emitProgress = emitProgress;
    this.emitStatus = emitStatus;
    this.paths = paths;
    this.revisions = revisionTracker || new ComponentRevisionTracker({ paths });
    this.device = (deviceIdentity || deviceInstanceId) ? runtimeDeviceIdentity(deviceIdentity, deviceInstanceId) : null;
    this.native = new NativeService(log, paths, this.revisions, this.device);
    this.tunnel = new TunnelService(log, paths, this.device);
    this.gitStatusCache = null;
    this.gitStatusCacheAt = 0;
    this.gitStatusWorkspace = '';
    this.busy = false;
    this.snapshotCache = null;
    this.snapshotCacheAt = 0;
    this.snapshotInFlight = null;
    this.heartbeatFailures = 0;
    this.heartbeatFailureKind = '';
    this.recovering = false;
    this.recoveryAttempts = 0;
    this.nextRecoveryAt = 0;
    this.autoRecoveryBlocked = false;
    this.lastStartFailure = '';
    this.deferredRecoveryCount = 0;
    this.heartbeatFailureSince = 0;
    this.lastRecoveryAt = 0;
    this.lastHealthyAt = 0;
    this.accumulatedDowntimeMs = 0;
  }

  progress(step, percent, message) {
    this.emitProgress({ step, percent, message, time: new Date().toISOString() });
    this.log.info(message, { step, percent });
  }

  invalidateSnapshot() {
    this.snapshotCacheAt = 0;
  }

  publishSnapshot(snapshot, reason = 'refresh') {
    const signature = (value) => JSON.stringify(value ? { settings: value.settings, secrets: value.secrets, environment: value.environment, status: value.status } : null);
    const previous = signature(this.snapshotCache);
    this.snapshotCache = snapshot;
    this.snapshotCacheAt = Date.now();
    if (previous !== signature(snapshot)) this.emitStatus({ reason, snapshot });
    return snapshot;
  }

  endFailureStreak(now = Date.now()) {
    if (this.heartbeatFailureSince > 0) {
      this.accumulatedDowntimeMs += Math.max(0, now - this.heartbeatFailureSince);
      this.heartbeatFailureSince = 0;
    }
  }

  recoveryStatus() {
    return {
      recovering: this.recovering,
      failures: this.heartbeatFailures,
      failureKind: this.heartbeatFailureKind,
      recoveryAttempts: this.recoveryAttempts,
      nextRecoveryAt: this.nextRecoveryAt,
      recoveryBlocked: this.autoRecoveryBlocked,
      lastStartFailure: this.lastStartFailure,
      deferredRecoveryCount: this.deferredRecoveryCount,
      lastFailureAt: this.heartbeatFailureSince > 0 ? new Date(this.heartbeatFailureSince).toISOString() : null,
      lastRecoveryAt: this.lastRecoveryAt > 0 ? new Date(this.lastRecoveryAt).toISOString() : null,
      lastHealthyAt: this.lastHealthyAt > 0 ? new Date(this.lastHealthyAt).toISOString() : null,
      downtimeMs: this.accumulatedDowntimeMs,
      failureElapsedMs: this.heartbeatFailureSince > 0 ? Math.max(0, Date.now() - this.heartbeatFailureSince) : 0
    };
  }

  async gitStatus(workspace) {
    const target = String(workspace || '').trim();
    if (!target) return { available: false, branch: null, head: null, head_short: null, dirty: null };
    if (this.gitStatusCache && this.gitStatusWorkspace === target && Date.now() - this.gitStatusCacheAt < 10_000) return this.gitStatusCache;
    let status = { available: false, branch: null, head: null, head_short: null, dirty: null };
    try {
      const git = process.platform === 'win32' ? 'git.exe' : 'git';
      const result = await run(git, ['-C', target, 'status', '--porcelain=v2', '--branch', '--untracked-files=normal'], { allowFailure: true, timeoutMs: 2000 });
      if (result.code === 0) status = parseGitStatusPorcelainV2(result.stdout);
    } catch {}
    this.gitStatusCache = status;
    this.gitStatusCacheAt = Date.now();
    this.gitStatusWorkspace = target;
    return status;
  }

  deviceProjection(settings, { mcpHealth = null, nativeAlive = false, tunnelRunning = false, git = null } = {}) {
    if (!this.device) return null;
    return { scope: 'current_device_only', registry: 'local', device_id: this.device.deviceId, device_instance_id: this.device.deviceInstanceId, display_name: this.device.displayName, online: true, workspace: String(settings?.workspace || ''), coding: { mcp_running: Boolean(mcpHealth), native_alive: Boolean(nativeAlive), tunnel_running: Boolean(tunnelRunning), tunnel_id: String(settings?.tunnelId || '') || null, endpoint_device_instance_id: String(mcpHealth?.device_instance_id || '') || null, ownership: 'device_id' }, git: git || { available: false, branch: null, head: null, head_short: null, dirty: null } };
  }

  async preflightLegacyDeviceMigration(probes = {}) {
    if (!this.device) return { required: false, nativePid: null, tunnelPid: null };
    const settings = this.settingsStore.load();
    const state = readJson(this.paths.stateFile(), {});
    const plan = { required: false, nativePid: null, tunnelPid: null };
    const listenerPid = probes.listenerPid || loopbackListenerPid;

    if (isAlive(Number(state.nativePid))) {
      const ownership = classifyStoredDeviceOwner(state.nativeDeviceId, this.device.deviceId);
      if (ownership === 'foreign') {
        throw Object.assign(new Error('Legacy migration refused because Coding MCP belongs to another device.'), { code: 'NATIVE_PROCESS_FOREIGN_DEVICE' });
      }
      if (ownership === 'legacy') {
        const token = await this.ensureToken();
        const healthProbe = probes.mcpHealth || readMcpHealth;
        const [health, ownerPid] = await Promise.all([
          healthProbe(settings.mcpPort, token, settings.workspace, ''),
          listenerPid(settings.mcpPort)
        ]);
        const exactState = state.nativeFingerprint === runtimeFingerprint(settings)
          && workspaceKey(state.nativeWorkspace || '') === workspaceKey(settings.workspace)
          && Number(state.nativePort) === Number(settings.mcpPort);
        const healthDeviceId = String(health?.device_id || '').toLowerCase();
        if (!exactState || Number(ownerPid) !== Number(state.nativePid) || !health
          || (healthDeviceId && healthDeviceId !== this.device.deviceId.toLowerCase())) {
          throw Object.assign(new Error('Legacy Coding MCP ownership could not be proven for this install.'), { code: 'NATIVE_LEGACY_MIGRATION_UNVERIFIED' });
        }
        plan.nativePid = Number(state.nativePid);
        plan.required = true;
      }
    }

    if (isAlive(Number(state.tunnelPid))) {
      const ownership = classifyStoredDeviceOwner(state.tunnelDeviceId, this.device.deviceId);
      if (ownership === 'foreign') {
        throw Object.assign(new Error('Legacy migration refused because Coding Tunnel belongs to another device.'), { code: 'TUNNEL_PROCESS_FOREIGN_DEVICE' });
      }
      if (ownership === 'legacy') {
        const ownerPid = await listenerPid(settings.healthPort);
        let healthy = false;
        if (Number(ownerPid) === Number(state.tunnelPid)) {
          if (probes.tunnelHealth) healthy = await probes.tunnelHealth(settings, Number(state.tunnelPid));
          else {
            const result = await run(this.paths.tunnelExecutable(), [
              'health', '--port', String(settings.healthPort), '--pid', String(state.tunnelPid),
              '--require-control-plane-poll', '--json'
            ], { allowFailure: true, timeoutMs: 3000 });
            healthy = result.code === 0;
          }
        }
        if (!healthy) {
          throw Object.assign(new Error('Legacy Coding Tunnel ownership could not be proven for this install.'), { code: 'TUNNEL_LEGACY_MIGRATION_UNVERIFIED' });
        }
        plan.tunnelPid = Number(state.tunnelPid);
        plan.required = true;
      }
    }

    if (plan.required) {
      if (!this.secrets.get('runtimeApiKey')) throw Object.assign(new Error('Runtime API Key is required before legacy device migration.'), { code: 'LEGACY_MIGRATION_RUNTIME_KEY_MISSING' });
      if (!settings.tunnelId) throw Object.assign(new Error('Tunnel ID is required before legacy device migration.'), { code: 'LEGACY_MIGRATION_TUNNEL_ID_MISSING' });
    }
    return plan;
  }

  async applyLegacyDeviceMigration(plan) {
    if (!plan?.required || !this.device) return false;
    updateJsonAtomic(this.paths.stateFile(), (value) => {
      const next = { ...value };
      if (plan.nativePid) {
        if (Number(value.nativePid) !== Number(plan.nativePid)
          || classifyStoredDeviceOwner(value.nativeDeviceId, this.device.deviceId) !== 'legacy') {
          throw Object.assign(new Error('Coding MCP changed after legacy migration preflight.'), { code: 'LEGACY_MIGRATION_STATE_CHANGED' });
        }
        next.nativeDeviceId = this.device.deviceId;
        next.nativeDeviceInstanceId = this.device.deviceInstanceId;
      }
      if (plan.tunnelPid) {
        if (Number(value.tunnelPid) !== Number(plan.tunnelPid)
          || classifyStoredDeviceOwner(value.tunnelDeviceId, this.device.deviceId) !== 'legacy') {
          throw Object.assign(new Error('Coding Tunnel changed after legacy migration preflight.'), { code: 'LEGACY_MIGRATION_STATE_CHANGED' });
        }
        next.tunnelDeviceId = this.device.deviceId;
        next.tunnelDeviceInstanceId = this.device.deviceInstanceId;
      }
      return next;
    });
    this.log.info('Legacy primary runtime ownership proven; restarting with device identity', {
      nativePid: plan.nativePid || null,
      tunnelPid: plan.tunnelPid || null,
      deviceId: this.device.deviceId
    });
    await this.restart({ automatic: true });
    return true;
  }

  codingMcpRevisionStatus(options = {}) {
    try {
      if (typeof this.native?.revisionStatus === 'function') return this.native.revisionStatus(options);
    } catch { /* revision awareness must never take down lifecycle supervision */ }
    return {
      running_revision: null,
      disk_revision: null,
      update_pending: null,
      state: 'unavailable',
      error_code: 'REVISION_UNAVAILABLE'
    };
  }

  async ensureToken() {
    let token = this.secrets.get('mcpAuthToken');
    if (!token) {
      token = crypto.randomBytes(32).toString('base64url');
      this.secrets.set('mcpAuthToken', token);
    }
    return token;
  }

  p5A0Seed() {
    return String(this.secrets.get(P5_A0_SEED_SECRET) || '');
  }

  async prepareCodeActivation({ operationId, expiresAtUnixMs, allowAcceptancePending = false, sourceCheckpoint = null }) {
    const settings = this.settingsStore.load();
    const token = this.secrets.get('mcpAuthToken');
    if (!token || !(await this.native.status(settings))) {
      throw Object.assign(new Error('Coding Tools MCP is not running under this Recovery Host.'), { code: 'COMPONENT_STOPPED' });
    }
    return controlMcpActivation(settings.mcpPort, token, {
      action: 'prepare',
      operation_id: operationId,
      expires_at_unix_ms: expiresAtUnixMs,
      workspace: settings.workspace,
      allow_acceptance_pending: allowAcceptancePending === true,
      ...(sourceCheckpoint && typeof sourceCheckpoint === 'object' ? { source_checkpoint: sourceCheckpoint } : {})
    });
  }

  async inspectCodeActivation() {
    const settings = this.settingsStore.load();
    const token = this.secrets.get('mcpAuthToken');
    if (!token || !(await this.native.status(settings))) {
      return { safe: true, code: 'COMPONENT_STOPPED', reason: 'coding_mcp_stopped', workspace: settings.workspace };
    }
    const result = await readMcpActivationPreflight(settings.mcpPort, token);
    if (workspaceKey(result.workspace) !== workspaceKey(settings.workspace)) {
      throw Object.assign(new Error('Coding MCP activation preflight returned another workspace.'), { code: 'WORKSPACE_MISMATCH' });
    }
    return result;
  }

  async verifyCodeActivation(operationId, sourceCheckpoint) {
    const settings = this.settingsStore.load();
    const token = this.secrets.get('mcpAuthToken');
    if (!token) throw Object.assign(new Error('Coding Tools MCP is not running under this Recovery Host.'), { code: 'COMPONENT_STOPPED' });
    const result = await controlMcpActivation(settings.mcpPort, token, {
      action: 'verify',
      operation_id: String(operationId || ''),
      workspace: settings.workspace,
      source_checkpoint: sourceCheckpoint && typeof sourceCheckpoint === 'object' ? sourceCheckpoint : null
    });
    if (workspaceKey(result.workspace) !== workspaceKey(settings.workspace)) {
      throw Object.assign(new Error('Coding MCP activation verification returned another workspace.'), { code: 'WORKSPACE_MISMATCH' });
    }
    return result;
  }

  async currentMcpHealth() {
    const settings = this.settingsStore.load();
    const token = this.secrets.get('mcpAuthToken');
    return token ? readMcpHealth(settings.mcpPort, token, settings.workspace, this.device?.deviceId || '') : null;
  }

  async cancelCodeActivation(operationId, { strict = false } = {}) {
    const settings = this.settingsStore.load();
    const token = this.secrets.get('mcpAuthToken');
    if (!token) {
      if (strict) throw Object.assign(new Error('Coding Tools MCP activation fence could not be reached.'), { code: 'ACTIVATION_FENCE_RELEASE_FAILED' });
      return false;
    }
    try {
      const result = await controlMcpActivation(settings.mcpPort, token, { action: 'cancel', operation_id: operationId });
      if (result.cancelled === true) return true;
      if (strict) throw Object.assign(new Error('Coding Tools MCP did not confirm activation fence release.'), { code: 'ACTIVATION_FENCE_RELEASE_FAILED' });
      return false;
    } catch (error) {
      if (strict) throw Object.assign(error, { code: String(error?.code || 'ACTIVATION_FENCE_RELEASE_FAILED') });
      return false;
    }
  }

  async activateCodingMcpUpdate(expectedRevision, options = {}) {
    if (this.busy || this.recovering) {
      throw Object.assign(new Error('Runtime lifecycle is already busy.'), { code: 'RUNTIME_BUSY' });
    }
    this.busy = true;
    let replacementStarted = false;
    try {
      const expiresAtUnixMs = Number(options.expiresAtUnixMs || 0);
      const settings = this.settingsStore.load();
      this.validate(settings);
      const token = await this.ensureToken();
      const diskRevision = this.revisions.disk('coding_mcp', { force: true }).revision;
      if (diskRevision !== expectedRevision) {
        throw Object.assign(new Error('Coding MCP source revision changed before activation.'), { code: 'REVISION_CHANGED' });
      }
      const oldState = readJson(this.paths.stateFile(), {});
      const oldHealth = await this.currentMcpHealth();
      if (!oldHealth) throw Object.assign(new Error('Coding MCP health identity is unavailable.'), { code: 'ORCHESTRATION_STATE_UNCERTAIN' });
      assertActivationDeadline(expiresAtUnixMs, 'before_native_stop', false);
      await this.native.stop();
      assertActivationDeadline(expiresAtUnixMs, 'before_native_start', true);
      const started = await this.native.start(settings, token, this.progress.bind(this), {
        expectedCodeRevision: expectedRevision,
        expiresAtUnixMs,
        activationProcessMutated: true,
        p5Seed: this.p5A0Seed()
      });
      replacementStarted = true;
      let health = null;
      for (let index = 0; index < 35; index += 1) {
        health = await this.currentMcpHealth();
        if (health?.code_revision === expectedRevision) break;
        if (!(await this.native.status(settings))) {
          throw Object.assign(new Error('Coding MCP exited during activation.'), { code: 'ACTIVATION_HEALTH_FAILED' });
        }
        await wait(1000);
      }
      if (!health || health.code_revision !== expectedRevision) {
        throw Object.assign(new Error('Coding MCP did not report the expected code revision after restart.'), { code: 'REVISION_VERIFICATION_FAILED' });
      }
      const oldProcessInstanceId = String(oldHealth.process_instance_id || '');
      const newProcessInstanceId = String(health.process_instance_id || '');
      const oldServerInstanceId = String(oldHealth.instance_id || '');
      const newServerInstanceId = String(health.instance_id || '');
      if (!oldProcessInstanceId || !newProcessInstanceId || oldProcessInstanceId === newProcessInstanceId
        || !oldServerInstanceId || !newServerInstanceId || oldServerInstanceId === newServerInstanceId) {
        throw Object.assign(new Error('Coding MCP restart did not produce a new verified process identity.'), { code: 'ACTIVATION_IDENTITY_UNCHANGED' });
      }
      const verifiedDiskRevision = this.revisions.disk('coding_mcp', { force: true }).revision;
      if (verifiedDiskRevision !== expectedRevision) {
        throw Object.assign(new Error('Coding MCP source revision changed while activation was in progress.'), {
          code: 'REVISION_CHANGED_DURING_ACTIVATION',
          details: { expected_revision: expectedRevision, disk_revision: verifiedDiskRevision }
        });
      }
      this.invalidateSnapshot();
      return {
        old_instance_id: oldProcessInstanceId,
        new_instance_id: newProcessInstanceId,
        old_server_instance_id: oldServerInstanceId,
        new_server_instance_id: newServerInstanceId,
        old_supervisor_instance_id: String(oldState.nativeInstanceId || '') || null,
        new_supervisor_instance_id: String(started.instanceId || '') || null,
        old_revision: String(oldState.nativeCodeRevision || oldHealth.code_revision || '') || null,
        new_revision: health.code_revision,
        health_verified: true,
        disk_revision_verified: true,
        tunnel_preserved: true
      };
    } catch (error) {
      if (replacementStarted) await this.native.stop().catch(() => false);
      throw error;
    } finally {
      this.busy = false;
    }
  }

  isManuallyStopped() {
    return readJson(this.paths.stateFile(), {}).manualStop === true;
  }

  setManualStop(value) {
    updateJsonAtomic(this.paths.stateFile(), (state) => ({
      ...state,
      manualStop: Boolean(value),
      intentChangedAt: new Date().toISOString()
    }));
  }

  connectorContractStatus(toolContract, discovery = null) {
    const currentSha256 = String(toolContract?.sha256 || '').trim();
    const runtimeState = readJson(this.paths.stateFile(), {});
    const acknowledgedSha256 = String(runtimeState.chatgptToolContractSha256 || '').trim();
    const rediscoveredSha256 = String(discovery?.contract_sha256 || '').trim();
    const observedAt = String(discovery?.observed_at || '').trim();
    const observedAtValid = Boolean(observedAt && Number.isFinite(Date.parse(observedAt)));
    const rediscovered = Boolean(
      currentSha256
      && discovery?.current_contract_observed === true
      && rediscoveredSha256 === currentSha256
      && observedAtValid
    );
    const contractChanged = Boolean(currentSha256 && currentSha256 !== acknowledgedSha256);
    let contractState = 'UNAVAILABLE';
    if (currentSha256) {
      if (currentSha256 === acknowledgedSha256) {
        contractState = rediscovered ? 'CURRENT_ACKNOWLEDGED' : 'UNCHANGED_ACKNOWLEDGED';
      } else {
        contractState = rediscovered ? 'CHANGED_DISCOVERED_NEEDS_ACK' : 'CHANGED_NEEDS_DISCOVERY';
      }
    }
    return {
      available: Boolean(currentSha256),
      schemaVersion: Number(toolContract?.schema_version || 0),
      profile: String(toolContract?.profile || ''),
      currentSha256,
      acknowledgedSha256,
      rediscovered,
      rediscoveredSha256,
      rediscoveredAt: rediscovered ? observedAt : null,
      contractState,
      // Tool-contract freshness is a contract boundary, not a process-liveness
      // boundary. ChatGPT may legitimately retain an already acknowledged tool
      // schema across an MCP process restart and call tools/call directly. A new
      // real discovery receipt is therefore required only when the contract SHA
      // changes. Process/runtime freshness is proven independently by health and
      // loaded-revision identity.
      refreshRequired: Boolean(contractChanged && !rediscovered),
      acknowledgementPending: Boolean(contractChanged && rediscovered)
    };
  }

  acknowledgeConnectorContractHash(toolContract, discovery = null) {
    const status = this.connectorContractStatus(toolContract, discovery);
    if (!status.available) throw new Error('Coding Tools MCP chưa cung cấp tool contract fingerprint để xác nhận.');
    if (status.currentSha256 === status.acknowledgedSha256) return status;
    if (!status.rediscovered) {
      throw Object.assign(new Error('ChatGPT chưa đọc lại tools/list cho tool contract hiện tại.'), {
        code: 'CONNECTOR_CONTRACT_NOT_REDISCOVERED'
      });
    }
    updateJsonAtomic(this.paths.stateFile(), (state) => ({
      ...state,
      chatgptToolContractSha256: status.currentSha256,
      chatgptToolContractAcknowledgedAt: new Date().toISOString(),
      chatgptToolContractRediscoveredAt: status.rediscoveredAt || new Date().toISOString()
    }));
    return this.connectorContractStatus(toolContract, discovery);
  }

  synchronizeConnectorContract(toolContract, discovery = null) {
    const status = this.connectorContractStatus(toolContract, discovery);
    if (!status.acknowledgementPending) return status;
    return this.acknowledgeConnectorContractHash(toolContract, discovery);
  }

  async acknowledgeConnectorContract() {
    const settings = this.settingsStore.load();
    const token = this.secrets.get('mcpAuthToken');
    const health = token ? await readMcpHealth(settings.mcpPort, token, settings.workspace, this.device?.deviceId || '') : null;
    if (!health?.tool_contract) throw new Error('Coding Tools MCP chưa chạy hoặc chưa cung cấp tool contract fingerprint.');
    this.acknowledgeConnectorContractHash(health.tool_contract, health.connector_tool_discovery);
    this.invalidateSnapshot();
    return this.snapshot({ force: true, reason: 'connector-contract-acknowledged' });
  }

  pendingSupervisorRestartRequest() {
    if (this.busy || this.recovering) return null;
    const file = this.paths.supervisorRequestFile();
    if (!fs.existsSync(file)) return null;
    let request = null;
    try {
      request = JSON.parse(fs.readFileSync(file, 'utf8'));
    } catch {
      request = null;
    }
    const settings = this.settingsStore.load();
    const now = Date.now();
    const requestedAt = Number(request?.requested_at_unix_ms || 0);
    const notBefore = Number(request?.not_before_unix_ms || requestedAt);
    const expiresAt = Number(request?.expires_at_unix_ms || 0);
    const valid = Boolean(
      request
      && request.version === 1
      && request.action === 'restart'
      && String(request.ticket_id || '').trim()
      && workspaceKey(request.workspace) === workspaceKey(settings.workspace)
      && requestedAt > 0
      && requestedAt <= now + 5000
      && now - requestedAt <= MAX_SUPERVISOR_REQUEST_AGE_MS
      && expiresAt >= now
    );
    if (!valid) {
      fs.rmSync(file, { force: true });
      fs.rmSync(`${file}.bak`, { force: true });
      this.log.warn('Đã loại bỏ yêu cầu restart supervisor không hợp lệ hoặc đã hết hạn', {
        ticketId: request?.ticket_id || '',
        workspace: request?.workspace || ''
      });
      return null;
    }
    if (now < notBefore) return null;
    return { file, request };
  }

  async serviceSupervisorRestartRequest() {
    const pending = this.pendingSupervisorRestartRequest();
    if (!pending) return null;
    fs.rmSync(pending.file, { force: true });
    fs.rmSync(`${pending.file}.bak`, { force: true });
    const ticketId = String(pending.request.ticket_id);
    this.log.info('Recovery Host supervisor đã nhận yêu cầu restart từ Coding Tools MCP', { ticketId });
    try {
      const health = await this.currentMcpHealth();
      if (!health
        || health.process_instance_id !== pending.request.process_instance_id
        || health.instance_id !== pending.request.server_instance_id) {
        throw Object.assign(new Error('Supervisor restart ticket no longer matches the running MCP instance.'), { code: 'STALE_RESTART_TICKET' });
      }
      const expectedRevision = this.revisions.disk('coding_mcp', { force: true }).revision;
      const result = await this.activateCodingMcpUpdate(expectedRevision, {
        expiresAtUnixMs: Number(pending.request.expires_at_unix_ms || 0)
      });
      return { ticketId, status: 'completed', component: 'coding_mcp', result };
    } catch (error) {
      this.log.error(error.message, { stage: 'supervisor-restart-request', ticketId });
      return { ticketId, status: 'failed', error: error.message };
    }
  }

  validate(settings) {
    if (!settings.workspace || !fs.existsSync(settings.workspace)) throw new Error('Vui lòng chọn một thư mục làm việc hợp lệ.');
    validateRuntimeSettings(settings);
  }

  async start(options = {}) {
    if (this.busy) throw new Error('Hiện đã có nhiệm vụ triển khai đang chạy.');
    const automatic = options.automatic === true;
    if (!automatic) {
      this.autoRecoveryBlocked = false;
      this.lastStartFailure = '';
      this.heartbeatFailures = 0;
      this.heartbeatFailureKind = '';
      this.heartbeatFailureSince = 0;
      this.recoveryAttempts = 0;
      this.nextRecoveryAt = 0;
      this.deferredRecoveryCount = 0;
    }
    this.busy = true;
    try {
      const settings = this.settingsStore.load();
      this.validate(settings);
      const runtimeApiKey = this.secrets.get('runtimeApiKey');
      if (!runtimeApiKey) throw new Error('Vui lòng lưu Runtime API Key trong "Cấu hình triển khai" trước.');
      if (!settings.tunnelId) throw new Error('Vui lòng điền OpenAI Tunnel ID trước.');
      const token = await this.ensureToken();

      this.progress('preflight', 8, 'Đang kiểm tra thư mục làm việc, môi trường chạy và cổng');
      const env = await this.environment.inspect(settings, { forceProxy: true });
      if (!env.tunnelClient.installed) throw new Error('Thiếu tệp thực thi OpenAI tunnel-client.');
      if (!env.python.installed) {
        throw new Error('Môi trường runtime portable chưa sẵn sàng, phiên bản phát triển cần Python 3.11+; bản phát hành sẽ tích hợp sẵn Python.');
      }

      this.progress('proxy-detect', 14, 'Đang kiểm tra kết nối trực tiếp, Proxy hệ thống Windows và cổng Proxy cục bộ');
      const proxy = await resolveProxy(settings);
      if (settings.proxyMode === 'manual' && !proxy.reachable) {
        throw new Error(`Proxy thủ công không khả dụng: ${settings.proxyUrl}. Vui lòng khởi động phần mềm proxy, thay đổi cổng hoặc chuyển sang tự động phát hiện.`);
      }
      const proxyLabel = proxy.resolvedUrl || 'Kết nối trực tiếp';
      this.log.info('Hoàn tất kiểm tra tuyến đường mạng', { mode: settings.proxyMode, source: proxy.source, route: proxyLabel, reachable: proxy.reachable });
      this.progress('proxy-ready', 16, proxy.reachable ? `Tuyến đường mạng khả dụng: ${proxyLabel}` : 'Chưa xác minh được tuyến đường mạng khả dụng, sẽ tiếp tục thử kết nối trực tiếp và giữ nhật ký chẩn đoán');

      this.progress('runtime-stop-old', 18, 'Đang dọn dẹp các instance chạy cũ từ lần khởi động trước');
      await this.tunnel.stop();
      await this.native.stop().catch(() => false);
      if (await canConnect('127.0.0.1', settings.mcpPort, 350)) {
        throw new Error(`Cổng cục bộ ${settings.mcpPort} đang bị ứng dụng khác chiếm dụng. Trợ lý sẽ không cưỡng chế chấm dứt tiến trình không xác định, vui lòng thay đổi cổng MCP trong trang "Thư mục làm việc".`);
      }
      if (await canConnect('127.0.0.1', settings.healthPort, 350)) {
        throw new Error(`Cổng cục bộ ${settings.healthPort} đang bị ứng dụng khác chiếm dụng. Trợ lý sẽ không cưỡng chế chấm dứt tiến trình không xác định, vui lòng thay đổi cổng bảng điều khiển Tunnel.`);
      }

      await this.native.start(settings, token, this.progress.bind(this), { p5Seed: this.p5A0Seed() });

      this.progress('mcp-health', 64, 'Đang xác minh Coding Tools MCP');
      let ready = false;
      for (let index = 0; index < 35; index += 1) {
        if (await probeMcp(settings.mcpPort, token, settings.workspace, this.device?.deviceId || '')) { ready = true; break; }
        if (!(await this.native.status(settings))) {
          throw new Error('Tiến trình Coding Tools MCP đã thoát sớm. Vui lòng xem mcp.log trong nhật ký vận hành để biết lỗi khởi động chi tiết.');
        }
        await wait(1000);
      }
      if (!ready) throw new Error('Coding Tools MCP không vượt qua kiểm tra sức khỏe trong thời gian quy định.');

      await this.tunnel.start({ ...settings, effectiveProxyUrl: proxy.resolvedUrl }, runtimeApiKey, token, this.progress.bind(this));
      this.setManualStop(false);
      this.autoRecoveryBlocked = false;
      this.lastStartFailure = '';
      this.heartbeatFailures = 0;
      this.heartbeatFailureKind = '';
      this.heartbeatFailureSince = 0;
      this.recoveryAttempts = 0;
      this.nextRecoveryAt = 0;
      this.lastRecoveryAt = Date.now();
      this.lastHealthyAt = Date.now();
      this.progress('complete', 100, 'Triển khai hoàn tất, cả MCP và OpenAI Tunnel đều đang chạy');
      this.invalidateSnapshot();
      return await this.snapshot({ force: true, reason: 'started' });
    } catch (error) {
      this.autoRecoveryBlocked = true;
      this.lastStartFailure = error.message;
      this.heartbeatFailures = 0;
      this.heartbeatFailureKind = '';
      this.heartbeatFailureSince = Date.now();
      this.recoveryAttempts = 0;
      this.nextRecoveryAt = 0;
      await this.tunnel.stop().catch(() => false);
      await this.native.stop().catch(() => false);
      this.invalidateSnapshot();
      this.log.error(error.message, { stage: 'start' });
      this.emitProgress({ step: 'failed', percent: 100, message: error.message, time: new Date().toISOString() });
      throw error;
    } finally {
      this.busy = false;
    }
  }

  async stop(options = {}) {
    if (this.busy) throw new Error('Hiện đã có nhiệm vụ đang chạy.');
    this.busy = true;
    try {
      if (options.manual !== false) this.setManualStop(true);
      this.progress('stop-tunnel', 25, 'Đang dừng OpenAI Tunnel');
      await this.tunnel.stop();
      this.progress('stop-runtime', 65, 'Đang dừng Coding Tools MCP');
      await this.native.stop().catch(() => false);
      this.progress('stopped', 100, 'Tất cả các dịch vụ do trợ lý khởi động đã dừng');
      this.invalidateSnapshot();
      return await this.snapshot({ force: true, reason: 'stopped' });
    } finally {
      this.busy = false;
    }
  }

  async restart(options = {}) {
    await this.stop({ manual: false });
    return this.start(options);
  }

  async switchWorkspace(nextWorkspace) {
    if (this.busy) throw new Error('Hiện đã có nhiệm vụ đang chạy.');
    const previous = this.settingsStore.load();
    const workspace = path.resolve(String(nextWorkspace || '').trim());
    if (!workspace || !fs.existsSync(workspace) || !fs.statSync(workspace).isDirectory()) {
      throw new Error('Vui lòng chọn một thư mục làm việc hợp lệ.');
    }

    const recentWorkspaces = mergeRecentWorkspaces(previous.recentWorkspaces, workspace);
    if (workspaceKey(previous.workspace) === workspaceKey(workspace)) {
      if (JSON.stringify(recentWorkspaces) !== JSON.stringify(previous.recentWorkspaces || [])) {
        this.settingsStore.save({ recentWorkspaces });
      }
      return this.snapshot({ force: true, reason: 'workspace-reselected' });
    }

    this.busy = true;
    let runtimeWasRunning = false;
    try {
      runtimeWasRunning = await this.native.status();
    } catch {
      runtimeWasRunning = false;
    }

    if (!runtimeWasRunning) {
      this.settingsStore.save({ workspace, recentWorkspaces });
      this.progress('workspace-saved', 100, 'Thư mục làm việc đã lưu, sẽ có hiệu lực ở lần khởi động dịch vụ tiếp theo');
      this.busy = false;
      this.invalidateSnapshot();
      return this.snapshot({ force: true, reason: 'workspace-saved' });
    }

    const token = await this.ensureToken();
    try {
      this.progress('workspace-switch', 20, 'Đang chuyển đổi nóng thư mục làm việc MCP');
      await switchMcpWorkspace(previous.mcpPort, token, workspace);
      const next = this.settingsStore.save({ workspace, recentWorkspaces });
      await this.native.markWorkspace(next);
      this.progress('workspace-health', 80, 'Đang xác minh thư mục làm việc mới');
      const ready = await probeMcp(next.mcpPort, token, workspace, this.device?.deviceId || '');
      if (!ready) throw new Error('Thư mục làm việc mới không khớp với thư mục thực tế của MCP.');
      this.progress('workspace-complete', 100, 'Đã chuyển thư mục làm việc, cả MCP và Tunnel đều không cần khởi động lại');
      this.invalidateSnapshot();
      return this.snapshot({ force: true, reason: 'workspace-switched' });
    } catch (error) {
      this.log.error(error.message, { stage: 'workspace-switch', rollback: previous.workspace });
      try {
        await switchMcpWorkspace(previous.mcpPort, token, previous.workspace);
        this.settingsStore.save(previous);
        await this.native.markWorkspace(previous);
      } catch (rollbackError) {
        this.log.error(rollbackError.message, { stage: 'workspace-rollback' });
      }
      throw new Error(`Chuyển đổi thư mục làm việc thất bại: ${error.message}`);
    } finally {
      this.busy = false;
    }
  }

  async updateAuthorizedRoots(roots) {
    if (this.busy) throw new Error('Hiện đã có nhiệm vụ đang chạy.');
    const previous = this.settingsStore.load();
    const normalized = (Array.isArray(roots) ? roots : [])
      .map((item) => path.resolve(String(item || '').trim()))
      .filter((item) => item && fs.existsSync(item) && fs.statSync(item).isDirectory())
      .filter((item, index, all) => all.findIndex((other) => workspaceKey(other) === workspaceKey(item)) === index)
      .filter((item) => workspaceKey(item) !== workspaceKey(previous.workspace))
      .slice(0, 32);
    this.busy = true;
    try {
      const runtimeWasRunning = await this.native.status().catch(() => false);
      if (runtimeWasRunning) {
        const token = await this.ensureToken();
        await setMcpAuthorizedRoots(previous.mcpPort, token, normalized);
      }
      const saved = this.settingsStore.save({ authorizedRoots: normalized });
      if (runtimeWasRunning) await this.native.markWorkspace(saved);
      this.invalidateSnapshot();
      return this.snapshot({ force: true, reason: 'authorized-roots-updated' });
    } finally {
      this.busy = false;
    }
  }

  async lightweightSnapshot() {
    const settings = this.settingsStore.load();
    const token = this.secrets.get('mcpAuthToken');
    const [mcpHealth, nativeAlive, tunnelRunning, git] = await Promise.all([
      token ? readMcpHealth(settings.mcpPort, token, settings.workspace, this.device?.deviceId || '') : Promise.resolve(null),
      this.native.status().catch(() => false),
      this.tunnel.status(settings).catch(() => false),
      this.gitStatus(settings.workspace)
    ]);
    const mcpRunning = Boolean(mcpHealth);
    return {
      workspace: settings.workspace,
      mcpRunning,
      nativeAlive,
      tunnelRunning,
      fullyReady: mcpRunning && tunnelRunning,
      device: this.deviceProjection(settings, { mcpHealth, nativeAlive, tunnelRunning, git }),
      codeRevision: { codingMcp: this.codingMcpRevisionStatus() },
      ...this.recoveryStatus()
    };
  }

  async recoverTunnelOnly() {
    const settings = this.settingsStore.load();
    const runtimeApiKey = this.secrets.get('runtimeApiKey');
    if (!runtimeApiKey) throw new Error('Vui lòng lưu Runtime API Key trong "Cấu hình triển khai" trước.');
    if (!settings.tunnelId) throw new Error('Vui lòng điền OpenAI Tunnel ID trước.');
    const token = await this.ensureToken();
    const proxy = await resolveProxy(settings);
    if (settings.proxyMode === 'manual' && !proxy.reachable) {
      throw new Error(`Proxy thủ công không khả dụng: ${settings.proxyUrl}.`);
    }
    await this.tunnel.start(
      { ...settings, effectiveProxyUrl: proxy.resolvedUrl },
      runtimeApiKey,
      token,
      this.progress.bind(this)
    );
    this.log.info('OpenAI Tunnel đã được khôi phục mà không khởi động lại Coding Tools MCP');
    this.invalidateSnapshot();
  }

  async recoverMcpOnly() {
    const settings = this.settingsStore.load();
    this.validate(settings);
    const token = await this.ensureToken();
    const before = readJson(this.paths.stateFile(), {});
    const oldNativePid = Number(before.nativePid || 0);
    const tunnelPid = Number(before.tunnelPid || 0);

    if (isAlive(oldNativePid)) {
      throw Object.assign(new Error('Coding MCP process is still alive; refusing dead-process recovery.'), {
        code: 'MCP_PROCESS_STILL_ALIVE'
      });
    }
    if (await canConnect('127.0.0.1', settings.mcpPort, 350)) {
      throw Object.assign(new Error(`Cổng cục bộ ${settings.mcpPort} đang bị tiến trình khác chiếm dụng; từ chối nhận hoặc dừng tiến trình không xác định.`), {
        code: 'MCP_PORT_IN_USE'
      });
    }

    let started = null;
    try {
      started = await this.native.start(settings, token, this.progress.bind(this), { p5Seed: this.p5A0Seed() });
      let health = null;
      let ownedPid = 0;
      for (let index = 0; index < 35; index += 1) {
        const state = readJson(this.paths.stateFile(), {});
        ownedPid = Number(state.nativePid || 0);
        health = await readMcpHealth(settings.mcpPort, token, settings.workspace, this.device?.deviceId || '');
        if (health && ownedPid > 0 && isAlive(ownedPid) && await loopbackListenerPid(settings.mcpPort) === ownedPid) break;
        health = null;
        if (!(await this.native.status(settings))) {
          throw Object.assign(new Error('Coding Tools MCP exited during MCP-only recovery.'), { code: 'MCP_RECOVERY_PROCESS_EXITED' });
        }
        await wait(1000);
      }
      if (!health || ownedPid <= 0) {
        throw Object.assign(new Error('Coding Tools MCP did not pass exact identity and listener ownership checks during MCP-only recovery.'), {
          code: 'MCP_RECOVERY_NOT_READY'
        });
      }
      const after = readJson(this.paths.stateFile(), {});
      this.log.info('Coding Tools MCP đã được khôi phục mà không khởi động lại OpenAI Tunnel', {
        oldPid: oldNativePid || null,
        newPid: ownedPid,
        tunnelPid: tunnelPid || null,
        tunnelStatePreserved: Number(after.tunnelPid || 0) === tunnelPid
      });
      this.invalidateSnapshot();
      return {
        old_pid: oldNativePid || null,
        new_pid: ownedPid,
        tunnel_pid: tunnelPid || null,
        tunnel_preserved: Number(after.tunnelPid || 0) === tunnelPid,
        health_verified: true
      };
    } catch (error) {
      if (started && started.reused !== true) await this.native.stop().catch(() => false);
      this.invalidateSnapshot();
      throw error;
    }
  }

  async supervise() {
    const supervisorRequest = await this.serviceSupervisorRestartRequest();
    if (supervisorRequest) {
      return { ...(await this.lightweightSnapshot()), supervisorRequest };
    }
    const status = await this.lightweightSnapshot();
    if (status.fullyReady) {
      const wasFailing = this.heartbeatFailures > 0 || this.recovering || this.heartbeatFailureSince > 0;
      this.endFailureStreak();
      if (wasFailing) this.lastRecoveryAt = Date.now();
      this.heartbeatFailures = 0;
      this.heartbeatFailureKind = '';
      this.recoveryAttempts = 0;
      this.nextRecoveryAt = 0;
      this.deferredRecoveryCount = 0;
      this.lastHealthyAt = Date.now();
      return { ...status, ...this.recoveryStatus() };
    }
    const runtimeState = readJson(this.paths.stateFile(), {});
    const expectedRunning = runtimeState.manualStop === false
      && Boolean(runtimeState.nativePid || runtimeState.tunnelPid || this.settingsStore.load().autoStartServices);
    if (this.busy || this.recovering || this.isManuallyStopped() || !expectedRunning) return status;
    if (this.autoRecoveryBlocked) {
      return { ...status, recoveryBlocked: true, lastStartFailure: this.lastStartFailure };
    }
    const failureKind = status.mcpRunning
      ? 'tunnel_unavailable'
      : (status.nativeAlive ? 'mcp_health_unavailable' : 'mcp_process_exited');
    if (failureKind !== this.heartbeatFailureKind) {
      this.endFailureStreak();
      this.heartbeatFailureKind = failureKind;
      this.heartbeatFailures = 0;
      this.recoveryAttempts = 0;
      this.nextRecoveryAt = 0;
      this.deferredRecoveryCount = 0;
      this.heartbeatFailureSince = Date.now();
    }
    if (this.heartbeatFailureSince === 0) this.heartbeatFailureSince = Date.now();
    this.heartbeatFailures += 1;
    if (this.heartbeatFailures < 3 || Date.now() < this.nextRecoveryAt) {
      return { ...status, ...this.recoveryStatus() };
    }

    this.recovering = true;
    this.recoveryAttempts += 1;
    const delay = Math.min(60000, 2000 * (2 ** Math.min(this.recoveryAttempts - 1, 5)));
    this.nextRecoveryAt = Date.now() + delay;
    this.log.warn('Kiểm tra sức khỏe giao thức runtime thất bại liên tiếp, bắt đầu tự động khôi phục', {
      failures: this.heartbeatFailures,
      attempt: this.recoveryAttempts,
      mcpRunning: status.mcpRunning,
      nativeAlive: status.nativeAlive,
      tunnelRunning: status.tunnelRunning
    });
    try {
      if (status.mcpRunning) {
        await this.recoverTunnelOnly();
      } else if (status.nativeAlive) {
        this.deferredRecoveryCount += 1;
        if (this.deferredRecoveryCount >= MAX_DEFERRED_RECOVERIES) {
          this.log.warn('Coding Tools MCP không trả lời health check sau nhiều chu kỳ mặc dù process còn sống; buộc khởi động lại để thoát khỏi trạng thái treo', {
            failures: this.heartbeatFailures,
            deferredRecoveryCount: this.deferredRecoveryCount,
            attempt: this.recoveryAttempts
          });
          this.deferredRecoveryCount = 0;
          await this.restart({ automatic: true });
        } else {
          this.log.warn('Coding Tools MCP không trả lời health check nhưng process vẫn còn sống; hoãn restart để không cắt tool call đang chạy', {
            failures: this.heartbeatFailures,
            deferredRecoveryCount: this.deferredRecoveryCount,
            maxDeferredRecoveries: MAX_DEFERRED_RECOVERIES,
            attempt: this.recoveryAttempts
          });
          return {
            ...status,
            ...this.recoveryStatus(),
            recovering: false,
            recoveryDeferred: true,
            deferredRecoveryCount: this.deferredRecoveryCount,
            recoveryReason: 'mcp_process_alive_health_unavailable'
          };
        }
      } else {
        await this.recoverMcpOnly();
      }
      this.endFailureStreak();
      this.lastRecoveryAt = Date.now();
      this.lastHealthyAt = Date.now();
      this.heartbeatFailures = 0;
      this.recoveryAttempts = 0;
      this.nextRecoveryAt = 0;
      this.deferredRecoveryCount = 0;
    } catch (error) {
      this.log.error(error.message, { stage: 'automatic-recovery', retryAfterMs: delay });
    } finally {
      this.recovering = false;
    }
    return this.lightweightSnapshot();
  }

  async snapshot(options = {}) {
    const force = options.force === true;
    if (!force && this.snapshotCache && Date.now() - this.snapshotCacheAt < 15000) return this.snapshotCache;
    if (!force && this.snapshotInFlight) return this.snapshotInFlight;
    this.snapshotInFlight = this._collectSnapshot(options.reason || 'refresh');
    try { return await this.snapshotInFlight; }
    finally { this.snapshotInFlight = null; }
  }

  async _collectSnapshot(reason) {
    const settings = this.settingsStore.load();
    const environment = await this.environment.inspect(settings);
    const token = this.secrets.get('mcpAuthToken');
    const [health, tunnelRunning, git] = await Promise.all([
      token ? readMcpHealth(settings.mcpPort, token, settings.workspace, this.device?.deviceId || '') : Promise.resolve(null),
      this.tunnel.status(settings).catch(() => false),
      this.gitStatus(settings.workspace)
    ]);
    const runtimeRunning = Boolean(health);
    const connectorContract = this.synchronizeConnectorContract(
      health?.tool_contract || null,
      health?.connector_tool_discovery || null
    );
    const nativeAlive = await this.native.status().catch(() => false);
    return this.publishSnapshot({
      settings,
      secrets: this.secrets.status(),
      environment,
      device: this.deviceProjection(settings, { mcpHealth: health, nativeAlive, tunnelRunning, git }),
      status: {
        busy: this.busy,
        runtimeRunning,
        tunnelRunning,
        fullyReady: runtimeRunning && tunnelRunning,
        localMcpUrl: `http://127.0.0.1:${settings.mcpPort}/mcp`,
        tunnelUiUrl: `http://127.0.0.1:${settings.healthPort}/ui`,
        manuallyStopped: this.isManuallyStopped(),
        toolContract: connectorContract.available ? {
          schemaVersion: connectorContract.schemaVersion,
          profile: connectorContract.profile,
          sha256: connectorContract.currentSha256
        } : null,
        connectorContractAcknowledgedSha256: connectorContract.acknowledgedSha256,
        connectorContractState: connectorContract.contractState,
        connectorRefreshRequired: connectorContract.refreshRequired,
        connectorAcknowledgementPending: connectorContract.acknowledgementPending,
        connectorRediscovered: connectorContract.rediscovered,
        connectorRediscoveredAt: connectorContract.rediscoveredAt,
        codeRevision: { codingMcp: this.codingMcpRevisionStatus() },
        ...this.recoveryStatus()
      }
    }, reason);
  }
}

module.exports = { RuntimeOrchestrator, probeMcp, readMcpHealth, readMcpActivationPreflight, parseGitStatusPorcelainV2, parseLoopbackListenerPid, loopbackListenerPid, setMcpAuthorizedRoots };
