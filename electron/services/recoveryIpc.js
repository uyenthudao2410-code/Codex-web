const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const { readJson, writeJsonAtomic } = require('./jsonStore');
const { runtimeDeviceIdentity } = require('./deviceIdentity');
const { INSTALLATION_ID_PATTERN } = require('./runtimeIdentity');

const MAX_DESCRIPTOR_BYTES = 16 * 1024;
const MAX_REQUEST_BYTES = 64 * 1024;
const MAX_RESPONSE_BYTES = 4 * 1024 * 1024;
const DEFAULT_TIMEOUT_MS = 15_000;
const MUTATION_TIMEOUT_MS = 90_000;
const ACTIVATION_EPOCH_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/;

const RPC_ACTIONS = Object.freeze([
  'recovery.ping',
  'recovery.status',
  'code.activation_preflight',
  'code.activate_update',
  'code.activation_status',
  'client.register_ui_revision',
  'client.suppress_ui_recovery',
  'runtime.snapshot',
  'runtime.lightweight_snapshot',
  'runtime.start',
  'runtime.stop',
  'runtime.restart',
  'runtime.activation_epoch_status',
  'runtime.complete_activation_epoch',
  'runtime.switch_workspace',
  'runtime.update_authorized_roots',
  'runtime.acknowledge_connector_contract',
  'health.inspect',
  'health.repair',
  'logs.read',
  'logs.clear'
]);

const MUTATING_ACTIONS = new Set([
  'code.activate_update',
  'client.register_ui_revision',
  'client.suppress_ui_recovery',
  'runtime.start',
  'runtime.stop',
  'runtime.restart',
  'runtime.complete_activation_epoch',
  'runtime.switch_workspace',
  'runtime.update_authorized_roots',
  'runtime.acknowledge_connector_contract',
  'health.repair',
  'logs.clear'
]);

function sameToken(left, right) {
  const a = Buffer.from(String(left || ''), 'utf8');
  const b = Buffer.from(String(right || ''), 'utf8');
  return a.length >= 32 && a.length === b.length && crypto.timingSafeEqual(a, b);
}

function boundedJson(value, maxBytes = MAX_RESPONSE_BYTES) {
  const body = JSON.stringify(value);
  if (Buffer.byteLength(body, 'utf8') <= maxBytes) return body;
  return JSON.stringify({ ok: false, error: { code: 'RESPONSE_TOO_LARGE', message: 'Recovery Host response exceeded the bounded size.' } });
}

function safeError(error) {
  return {
    code: String(error?.code || 'RECOVERY_ACTION_FAILED').slice(0, 80),
    message: String(error?.message || error || 'Recovery action failed.').slice(0, 1000)
  };
}

function isProcessAlive(pid) {
  if (!Number.isInteger(Number(pid)) || Number(pid) <= 0) return false;
  try { process.kill(Number(pid), 0); return true; } catch { return false; }
}

class RecoveryIpcServer {
  constructor({ paths, handlers, log, instanceId, startedAt, deviceIdentity = null, deviceInstanceId = '', activationEpochId = '' }) {
    this.paths = paths;
    this.handlers = handlers;
    this.log = log;
    this.instanceId = instanceId;
    this.startedAt = startedAt;
    this.device = (deviceIdentity || deviceInstanceId)
      ? runtimeDeviceIdentity(deviceIdentity, deviceInstanceId)
      : null;
    this.activationEpochId = String(activationEpochId || '').trim() || null;
    this.server = null;
    this.port = 0;
    this.token = '';
  }

  descriptor() {
    const runtimeIdentity = typeof this.paths.runtimeIdentity === 'function'
      ? this.paths.runtimeIdentity()
      : null;
    return {
      version: 1,
      host: '127.0.0.1',
      port: this.port,
      token: this.token,
      owner: 'recovery-host',
      owner_pid: process.pid,
      instance_id: this.instanceId,
      ...(runtimeIdentity ? {
        installation_id: runtimeIdentity.installation_id,
        runtime_mode: runtimeIdentity.mode
      } : {}),
      ...(this.device ? {
        device_id: this.device.deviceId,
        device_instance_id: this.device.deviceInstanceId,
        device_display_name: this.device.displayName
      } : {}),
      started_at: this.startedAt,
      ...(this.activationEpochId ? { activation_epoch_id: this.activationEpochId } : {})
    };
  }

  updateActivationEpoch(activationEpochId = '') {
    const id = String(activationEpochId || '').trim();
    if (id && !ACTIVATION_EPOCH_ID_PATTERN.test(id)) {
      throw Object.assign(new Error('Recovery Host activation epoch identity is invalid.'), { code: 'RECOVERY_DESCRIPTOR_INVALID' });
    }
    if (!this.server) return null;
    const file = this.paths.recoveryHostDescriptorFile();
    const current = readJson(file, null);
    if (!current || current.instance_id !== this.instanceId || Number(current.owner_pid) !== Number(process.pid)) {
      throw Object.assign(new Error('Recovery Host descriptor owner changed before epoch update.'), { code: 'RECOVERY_DESCRIPTOR_CHANGED' });
    }
    this.activationEpochId = id || null;
    const next = { ...current, ...(this.activationEpochId ? { activation_epoch_id: this.activationEpochId } : {}) };
    if (!this.activationEpochId) delete next.activation_epoch_id;
    writeJsonAtomic(file, next);
    try { fs.chmodSync(file, 0o600); } catch { /* best effort on Windows */ }
    return next;
  }

  async start() {
    if (this.server) return this.descriptor();
    this.token = crypto.randomBytes(32).toString('base64url');
    this.server = http.createServer((request, response) => this.handle(request, response));
    await new Promise((resolve, reject) => {
      const fail = (error) => { this.server = null; reject(error); };
      this.server.once('error', fail);
      this.server.listen(0, '127.0.0.1', () => {
        this.server.removeListener('error', fail);
        resolve();
      });
    });
    this.port = Number(this.server.address()?.port || 0);
    const descriptor = this.descriptor();
    writeJsonAtomic(this.paths.recoveryHostDescriptorFile(), descriptor);
    try { fs.chmodSync(this.paths.recoveryHostDescriptorFile(), 0o600); } catch { /* best effort on Windows */ }
    return descriptor;
  }

  async stop() {
    const server = this.server;
    this.server = null;
    this.port = 0;
    this.token = '';
    const current = readJson(this.paths.recoveryHostDescriptorFile(), null);
    if (current?.instance_id === this.instanceId) {
      fs.rmSync(this.paths.recoveryHostDescriptorFile(), { force: true });
      fs.rmSync(`${this.paths.recoveryHostDescriptorFile()}.bak`, { force: true });
    }
    if (!server) return false;
    await new Promise((resolve) => server.close(() => resolve()));
    return true;
  }

  reject(response, status, code, message) {
    const body = boundedJson({ ok: false, error: { code, message } });
    response.writeHead(status, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) });
    response.end(body);
  }

  handle(request, response) {
    if (request.method !== 'POST' || request.url !== '/v1/call') {
      this.reject(response, 404, 'NOT_FOUND', 'Not found.');
      return;
    }
    const authorization = String(request.headers.authorization || '');
    const supplied = authorization.startsWith('Bearer ') ? authorization.slice(7) : '';
    if (!sameToken(supplied, this.token)) {
      this.reject(response, 401, 'UNAUTHORIZED', 'Unauthorized.');
      return;
    }
    const declaredLength = Number(request.headers['content-length'] || 0);
    if (!Number.isFinite(declaredLength) || declaredLength < 0 || declaredLength > MAX_REQUEST_BYTES) {
      this.reject(response, 413, 'REQUEST_TOO_LARGE', 'Request too large.');
      return;
    }
    const chunks = [];
    let total = 0;
    let finished = false;
    const failOnce = (status, code, message) => {
      if (finished) return;
      finished = true;
      this.reject(response, status, code, message);
    };
    request.on('data', (chunk) => {
      total += chunk.length;
      if (total > MAX_REQUEST_BYTES) {
        request.destroy();
        failOnce(413, 'REQUEST_TOO_LARGE', 'Request too large.');
        return;
      }
      chunks.push(chunk);
    });
    request.on('error', () => failOnce(400, 'INVALID_REQUEST', 'Invalid request.'));
    request.on('end', async () => {
      if (finished) return;
      let payload;
      try { payload = JSON.parse(Buffer.concat(chunks).toString('utf8')); }
      catch { failOnce(400, 'INVALID_JSON', 'Invalid JSON.'); return; }
      const action = String(payload?.action || '');
      const args = Array.isArray(payload?.args) ? payload.args : [];
      if (!RPC_ACTIONS.includes(action) || typeof this.handlers[action] !== 'function') {
        failOnce(400, 'ACTION_NOT_ALLOWED', 'Recovery action is not allowlisted.');
        return;
      }
      try {
        const data = await this.handlers[action](...args);
        if (finished) return;
        finished = true;
        const body = boundedJson({ ok: true, data });
        response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) });
        response.end(body);
      } catch (error) {
        if (finished) return;
        finished = true;
        const safe = safeError(error);
        this.log?.warn?.('Recovery Host IPC action failed', { action, code: safe.code });
        const body = boundedJson({ ok: false, error: safe });
        response.writeHead(409, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) });
        response.end(body);
      }
    });
  }
}

function loadRecoveryDescriptor(paths) {
  const file = paths.recoveryHostDescriptorFile();
  const raw = fs.readFileSync(file, 'utf8');
  if (Buffer.byteLength(raw, 'utf8') > MAX_DESCRIPTOR_BYTES) {
    throw Object.assign(new Error('Recovery Host descriptor exceeds the bounded size.'), { code: 'RECOVERY_DESCRIPTOR_INVALID' });
  }
  let descriptor;
  try { descriptor = JSON.parse(raw); }
  catch { throw Object.assign(new Error('Recovery Host descriptor is invalid JSON.'), { code: 'RECOVERY_DESCRIPTOR_INVALID' }); }
  const port = Number(descriptor?.port || 0);
  const token = String(descriptor?.token || '');
  const ownerPid = Number(descriptor?.owner_pid || 0);
  const installationId = String(descriptor?.installation_id || '').toLowerCase();
  const runtimeMode = String(descriptor?.runtime_mode || '');
  const hasRuntimeIdentity = Boolean(descriptor?.installation_id || descriptor?.runtime_mode);
  if (descriptor?.version !== 1 || descriptor?.host !== '127.0.0.1' || descriptor?.owner !== 'recovery-host') {
    throw Object.assign(new Error('Recovery Host descriptor endpoint is invalid.'), { code: 'RECOVERY_DESCRIPTOR_INVALID' });
  }
  if (!Number.isInteger(port) || port < 1 || port > 65535 || token.length < 32 || !String(descriptor?.instance_id || '')) {
    throw Object.assign(new Error('Recovery Host descriptor is incomplete.'), { code: 'RECOVERY_DESCRIPTOR_INVALID' });
  }
  if (hasRuntimeIdentity
    && (!INSTALLATION_ID_PATTERN.test(installationId) || !['development', 'packaged'].includes(runtimeMode))) {
    throw Object.assign(new Error('Recovery Host installation identity is invalid.'), { code: 'RECOVERY_DESCRIPTOR_INVALID' });
  }
  if (descriptor?.activation_epoch_id !== undefined
    && descriptor.activation_epoch_id !== null
    && !ACTIVATION_EPOCH_ID_PATTERN.test(String(descriptor.activation_epoch_id))) {
    throw Object.assign(new Error('Recovery Host activation epoch identity is invalid.'), { code: 'RECOVERY_DESCRIPTOR_INVALID' });
  }
  if (!Number.isInteger(ownerPid) || !isProcessAlive(ownerPid)) {
    throw Object.assign(new Error('Recovery Host descriptor owner is not alive.'), { code: 'RECOVERY_DESCRIPTOR_STALE' });
  }
  return {
    ...descriptor,
    port,
    token,
    owner_pid: ownerPid,
    installation_id: installationId || null,
    runtime_mode: runtimeMode || null
  };
}

function assertExpectedDescriptor(descriptor, options = {}) {
  const expectedOwnerPid = Number(options.expectedOwnerPid || 0);
  const expectedInstanceId = String(options.expectedInstanceId || '');
  const expectedInstallationId = String(options.expectedInstallationId || '').toLowerCase();
  const ownerMatches = !expectedOwnerPid || Number(descriptor.owner_pid) === expectedOwnerPid;
  const instanceMatches = !expectedInstanceId || String(descriptor.instance_id || '') === expectedInstanceId;
  const installationMatches = !expectedInstallationId || String(descriptor.installation_id || '').toLowerCase() === expectedInstallationId;
  if (ownerMatches && instanceMatches && installationMatches) return descriptor;
  throw Object.assign(new Error('Recovery Host descriptor changed before the authenticated request was sent.'), {
    code: 'RECOVERY_DESCRIPTOR_CHANGED',
    details: {
      expected_owner_pid: expectedOwnerPid || null,
      observed_owner_pid: Number(descriptor.owner_pid || 0) || null,
      expected_instance_id: expectedInstanceId || null,
      observed_instance_id: String(descriptor.instance_id || '') || null,
      expected_installation_id: expectedInstallationId || null,
      observed_installation_id: String(descriptor.installation_id || '') || null
    }
  });
}

class RecoveryIpcClient {
  constructor({ paths }) {
    this.paths = paths;
  }

  call(action, args = [], options = {}) {
    if (!RPC_ACTIONS.includes(action)) {
      return Promise.reject(Object.assign(new Error('Recovery action is not allowlisted.'), { code: 'ACTION_NOT_ALLOWED' }));
    }
    let descriptor;
    try {
      descriptor = loadRecoveryDescriptor(this.paths);
      assertExpectedDescriptor(descriptor, options);
    } catch (error) { return Promise.reject(error); }
    const body = Buffer.from(JSON.stringify({ action, args }));
    const timeout = Math.max(100, Number(options.timeout || (MUTATING_ACTIONS.has(action) ? MUTATION_TIMEOUT_MS : DEFAULT_TIMEOUT_MS)));
    return new Promise((resolve, reject) => {
      const request = http.request({
        host: '127.0.0.1',
        port: descriptor.port,
        path: '/v1/call',
        method: 'POST',
        headers: {
          Authorization: `Bearer ${descriptor.token}`,
          'Content-Type': 'application/json',
          'Content-Length': body.length
        },
        timeout
      }, (response) => {
        const chunks = [];
        let total = 0;
        response.on('data', (chunk) => {
          total += chunk.length;
          if (total <= MAX_RESPONSE_BYTES) chunks.push(chunk);
        });
        response.on('end', () => {
          if (total > MAX_RESPONSE_BYTES) {
            reject(Object.assign(new Error('Recovery Host response exceeded the bounded size.'), { code: 'RESPONSE_TOO_LARGE' }));
            return;
          }
          let payload;
          try { payload = JSON.parse(Buffer.concat(chunks).toString('utf8')); }
          catch { reject(Object.assign(new Error('Recovery Host returned invalid JSON.'), { code: 'RECOVERY_RESPONSE_INVALID' })); return; }
          if (response.statusCode !== 200 || payload?.ok !== true) {
            reject(Object.assign(new Error(String(payload?.error?.message || `Recovery Host request failed (HTTP ${response.statusCode}).`)), {
              code: String(payload?.error?.code || 'RECOVERY_REQUEST_FAILED')
            }));
            return;
          }
          resolve(payload.data);
        });
      });
      request.on('timeout', () => request.destroy(Object.assign(new Error('Recovery Host request timed out.'), { code: 'RECOVERY_REQUEST_TIMEOUT' })));
      request.on('error', (error) => reject(Object.assign(error, { code: error.code || 'RECOVERY_HOST_UNAVAILABLE' })));
      request.end(body);
    });
  }

  ping(options = {}) { return this.call('recovery.ping', [], { timeout: 1500, ...options }); }
  status(options = {}) { return this.call('recovery.status', [], options); }
  activationPreflight(request) { return this.call('code.activation_preflight', [request]); }
  activateUpdate(request) { return this.call('code.activate_update', [request]); }
  activationStatus(operationId) { return this.call('code.activation_status', [operationId]); }
  registerUiRevision(registration) { return this.call('client.register_ui_revision', [registration]); }
  suppressUiRecovery(intent) { return this.call('client.suppress_ui_recovery', [intent]); }
  snapshot(options = {}) { return this.call('runtime.snapshot', [options]); }
  lightweightSnapshot() { return this.call('runtime.lightweight_snapshot'); }
  supervise() { return this.lightweightSnapshot(); }
  start(options = {}, callOptions = {}) { return this.call('runtime.start', [options], callOptions); }
  stop(options = {}, callOptions = {}) { return this.call('runtime.stop', [options], callOptions); }
  restart(options = {}, callOptions = {}) { return this.call('runtime.restart', [options], callOptions); }
  activationEpochStatus() { return this.call('runtime.activation_epoch_status'); }
  completeActivationEpoch(epochId) { return this.call('runtime.complete_activation_epoch', [epochId]); }
  switchWorkspace(workspace) { return this.call('runtime.switch_workspace', [workspace]); }
  updateAuthorizedRoots(roots) { return this.call('runtime.update_authorized_roots', [roots]); }
  acknowledgeConnectorContract() { return this.call('runtime.acknowledge_connector_contract'); }
  healthInspect() { return this.call('health.inspect'); }
  healthRepair() { return this.call('health.repair'); }
  readLogs(limit = 300) { return this.call('logs.read', [limit]); }
  clearLogs() { return this.call('logs.clear'); }
}

module.exports = {
  RecoveryIpcServer,
  RecoveryIpcClient,
  RPC_ACTIONS,
  loadRecoveryDescriptor,
  assertExpectedDescriptor,
  sameToken,
  MAX_DESCRIPTOR_BYTES,
  MAX_REQUEST_BYTES,
  MAX_RESPONSE_BYTES,
  isProcessAlive
};
