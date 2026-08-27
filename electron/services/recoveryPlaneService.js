const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const { spawn } = require('node:child_process');
const { readJson, updateJsonAtomic, ensureParent } = require('./jsonStore');
const { rotateLog } = require('./logService');
const { canConnect } = require('./environmentService');
const { run } = require('./commandRunner');
const {
  isAlive,
  captureSpawnedProcessIdentity,
  requireExactStoredProcessIdentity
} = require('./nativeService');
const { runtimeDeviceIdentity, classifyStoredDeviceOwner } = require('./deviceIdentity');
const {
  normalizeProcessStartToken,
  observeProcessIdentity,
  sameProcessIdentity,
  terminateExactProcessTree
} = require('./processIdentity');

const RECOVERY_MCP_START_ATTEMPTS = 30;
// tunnel-client defaults to a 30s control-plane long poll plus a 5s deadline guardrail.
// Keep startup bounded, but allow the first successful poll to complete before declaring failure.
const RECOVERY_TUNNEL_START_ATTEMPTS = 90;
const LEGACY_CANDIDATE_STABILIZATION_ATTEMPTS = 4;
const LEGACY_CANDIDATE_STABILIZATION_DELAY_MS = 250;
const RECOVERY_MCP_HEALTH_TIMEOUT_MS = 3_000;
const RECOVERY_MCP_ACTIVATION_HEALTH_TIMEOUT_MS = 10_000;
const RECOVERY_TUNNEL_PROBE_TIMEOUT_MS = 10_000;

function wait(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex'); }
function instanceId() { return crypto.randomBytes(16).toString('hex'); }
function fileSha256(file) { return sha256(fs.readFileSync(file)); }
function recoveryFingerprint(settings, scriptRevision, authToken, deviceId = '', deviceInstanceId = '', activationEpochId = '') {
  const value = { script_revision: scriptRevision, port: Number(settings.recoveryMcpPort), auth_token_hash: sha256(String(authToken || '')), device_id: String(deviceId || ''), device_instance_id: String(deviceInstanceId || '') };
  if (String(activationEpochId || '').trim()) value.activation_epoch_id = String(activationEpochId).trim();
  return sha256(JSON.stringify(value));
}
function recoveryTunnelFingerprint(settings, authToken, deviceId = '', activationEpochId = '') {
  const value = { tunnel_id: String(settings.recoveryTunnelId || ''), mcp_port: Number(settings.recoveryMcpPort), health_port: Number(settings.recoveryHealthPort), proxy_url: String(settings.effectiveProxyUrl || settings.proxyUrl || ''), auth_token_hash: sha256(String(authToken || '')), device_id: String(deviceId || '') };
  if (String(activationEpochId || '').trim()) value.activation_epoch_id = String(activationEpochId).trim();
  return sha256(JSON.stringify(value));
}

function recoveryMcpHealthObservation(port, authToken, expectedDeviceId = '', expectedDeviceInstanceId = '', expectedActivationEpochId = '', expectedPid = 0, expectedInstanceId = '', options = {}) {
  return new Promise((resolve) => {
    let settled = false;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      resolve(value);
    };
    const timeoutMs = Number.isSafeInteger(Number(options.timeoutMs)) && Number(options.timeoutMs) > 0
      ? Math.min(Number(options.timeoutMs), RECOVERY_MCP_ACTIVATION_HEALTH_TIMEOUT_MS)
      : RECOVERY_MCP_HEALTH_TIMEOUT_MS;
    const request = http.request({ host: '127.0.0.1', port: Number(port), path: '/healthz', method: 'GET', headers: { Authorization: `Bearer ${authToken}`, Connection: 'close' }, timeout: timeoutMs }, (response) => {
      let body = '';
      let bodyTruncated = false;
      response.setEncoding('utf8');
      response.on('data', (chunk) => {
        if (body.length + chunk.length <= 16 * 1024) body += chunk;
        else bodyTruncated = true;
      });
      response.on('end', () => {
        if (bodyTruncated) { finish({ ok: false, failure_kind: 'response_too_large', payload: null }); return; }
        if (response.statusCode !== 200) { finish({ ok: false, failure_kind: 'http_status', status_code: Number(response.statusCode || 0), payload: null }); return; }
        let payload;
        try { payload = JSON.parse(body); }
        catch { finish({ ok: false, failure_kind: 'invalid_json', payload: null }); return; }
        const checks = [
          ['not_ready', payload.ok === true],
          ['service_mismatch', payload.service === 'recovery-mcp'],
          ['device_id_mismatch', !expectedDeviceId || String(payload.device_id || '').toLowerCase() === String(expectedDeviceId).toLowerCase()],
          ['device_instance_id_mismatch', !expectedDeviceInstanceId || String(payload.device_instance_id || '') === String(expectedDeviceInstanceId)],
          ['activation_epoch_mismatch', !expectedActivationEpochId || String(payload.activation_epoch_id || '') === String(expectedActivationEpochId)],
          ['pid_mismatch', !expectedPid || Number(payload.pid) === Number(expectedPid)],
          ['instance_id_mismatch', !expectedInstanceId || String(payload.instance_id || '') === String(expectedInstanceId)]
        ];
        const failure = checks.find(([, matches]) => !matches);
        finish({ ok: !failure, failure_kind: failure?.[0] || null, payload: failure ? null : payload });
      });
    });
    request.on('timeout', () => { request.destroy(); finish({ ok: false, failure_kind: 'timeout', payload: null }); });
    request.on('error', (error) => finish({ ok: false, failure_kind: 'request_error', error_code: String(error?.code || '') || null, payload: null }));
    request.end();
  });
}

async function recoveryMcpHealth(port, authToken, expectedDeviceId = '', expectedDeviceInstanceId = '', expectedActivationEpochId = '', expectedPid = 0, expectedInstanceId = '', options = {}) {
  const observation = await recoveryMcpHealthObservation(
    port,
    authToken,
    expectedDeviceId,
    expectedDeviceInstanceId,
    expectedActivationEpochId,
    expectedPid,
    expectedInstanceId,
    options
  );
  return observation.ok ? observation.payload : null;
}
async function stopExactTree(identity, options = {}) {
  if (!identity) return false;
  await terminateExactProcessTree(identity, options);
  return true;
}

function storedProcessReceipt(state, prefix) {
  const pid = Number(state?.[`${prefix}Pid`]);
  return {
    pid: Number.isSafeInteger(pid) && pid > 0 ? pid : null,
    process_start_token: normalizeProcessStartToken(state?.[`${prefix}ProcessStartToken`])
  };
}

function sameStoredProcessReceipt(state, prefix, expected) {
  const actual = storedProcessReceipt(state, prefix);
  return actual.pid === (expected?.pid ?? null)
    && actual.process_start_token === (expected?.process_start_token ?? null);
}

function stateFieldsMatch(state, expected = {}) {
  return Object.entries(expected).every(([key, value]) => {
    if (key.endsWith('ProcessStartToken')) {
      return normalizeProcessStartToken(state?.[key]) === normalizeProcessStartToken(value);
    }
    if (key.endsWith('Pid')) {
      const actualPid = Number(state?.[key]);
      const expectedPid = Number(value);
      return (Number.isSafeInteger(actualPid) && actualPid > 0 ? actualPid : null)
        === (Number.isSafeInteger(expectedPid) && expectedPid > 0 ? expectedPid : null);
    }
    return state?.[key] === value;
  });
}

function persistenceCleanupFailure(kind, persistenceError, cleanupError) {
  cleanupError.persistenceError = persistenceError;
  cleanupError.details = {
    ...(cleanupError.details || {}),
    persistence_error_code: persistenceError?.code || '',
    persistence_error_message: persistenceError?.message || ''
  };
  if (!cleanupError.code) cleanupError.code = `${kind}_PROCESS_PERSISTENCE_CLEANUP_FAILED`;
  return cleanupError;
}

async function recoveryTunnelListenerPid(port) {
  const result = await run('netstat.exe', ['-ano', '-p', 'tcp'], { allowFailure: true, timeoutMs: RECOVERY_TUNNEL_PROBE_TIMEOUT_MS });
  if (result.code !== 0) return null;
  const target = `127.0.0.1:${Number(port)}`;
  for (const line of String(result.stdout || '').split(/\r?\n/)) {
    const fields = line.trim().split(/\s+/);
    if (fields.length < 5 || String(fields[0]).toUpperCase() !== 'TCP') continue;
    if (fields[1] !== target || String(fields[3]).toUpperCase() !== 'LISTENING') continue;
    const pid = Number(fields[4]);
    return Number.isInteger(pid) && pid > 0 ? pid : null;
  }
  return null;
}

async function recoveryTunnelReady(paths, port, pid) {
  if (!isAlive(pid)) return false;
  if (await recoveryTunnelListenerPid(port) !== Number(pid)) return false;
  const result = await run(paths.tunnelExecutable(), [
    'health', '--port', String(port), '--pid', String(pid),
    '--require-control-plane-poll', '--json'
  ], { allowFailure: true, timeoutMs: RECOVERY_TUNNEL_PROBE_TIMEOUT_MS });
  return result.code === 0;
}

class RecoveryPlaneService {
  constructor({
    paths,
    log,
    deviceIdentity = null,
    deviceInstanceId = '',
    activationEpochId = '',
    processIdentityObserver = observeProcessIdentity,
    exactProcessTerminator = terminateExactProcessTree,
    identitySleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
  }) {
    this.paths = paths;
    this.log = log;
    this.device = (deviceIdentity || deviceInstanceId) ? runtimeDeviceIdentity(deviceIdentity, deviceInstanceId) : null;
    this.activationEpochId = String(activationEpochId || '').trim();
    this.lastStatus = null;
    this.ensureInFlight = null;
    this.legacyCandidateStabilizationAttempts = LEGACY_CANDIDATE_STABILIZATION_ATTEMPTS;
    this.legacyCandidateStabilizationDelayMs = LEGACY_CANDIDATE_STABILIZATION_DELAY_MS;
    this.processIdentityObserver = typeof processIdentityObserver === 'function'
      ? processIdentityObserver
      : observeProcessIdentity;
    this.exactProcessTerminator = typeof exactProcessTerminator === 'function'
      ? exactProcessTerminator
      : terminateExactProcessTree;
    this.identitySleep = typeof identitySleep === 'function'
      ? identitySleep
      : (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  }
  setActivationEpoch(activationEpochId = '') { this.activationEpochId = String(activationEpochId || '').trim(); return this.activationEpochId || null; }
  readState() { return readJson(this.paths.recoveryPlaneStateFile(), {}); }
  updateState(patch, guard = null, errorCode = 'RECOVERY_PROCESS_STATE_CHANGED') {
    updateJsonAtomic(this.paths.recoveryPlaneStateFile(), (value) => {
      if (typeof guard === 'function' && !guard(value)) {
        throw Object.assign(new Error('Recovery Plane process state changed before the guarded update.'), {
          code: errorCode
        });
      }
      return { ...value, version: 1, ...patch, updatedAt: new Date().toISOString() };
    });
  }
  assertOwnedLive(pid, storedDeviceId, kind) { if (!this.device || !isAlive(pid)) return; const ownership = classifyStoredDeviceOwner(storedDeviceId, this.device.deviceId); if (ownership === 'owned') return; const code = ownership === 'foreign' ? `${kind}_FOREIGN_DEVICE` : `${kind}_OWNER_UNVERIFIED`; throw Object.assign(new Error(ownership === 'foreign' ? `${kind} process state belongs to another device; refusing to adopt or terminate it.` : `${kind} process state predates device ownership metadata; refusing to adopt or terminate the live process.`), { code, ownerDeviceId: String(storedDeviceId || '') || null, expectedDeviceId: this.device.deviceId }); }

  async ownedIdentity(state, prefix, kind) {
    // Exact OS identity is the first gate.  This preserves the typed
    // *_PROCESS_IDENTITY_UNVERIFIED contract for live legacy records that
    // have no start token, before device ownership classification runs.
    const identity = await this.exactIdentity(state, prefix, kind);
    const pid = state?.[`${prefix}Pid`];
    this.assertOwnedLive(pid, state?.[`${prefix}DeviceId`], kind);
    return identity;
  }

  exactIdentity(state, prefix, kind) {
    return requireExactStoredProcessIdentity({
      pid: state?.[`${prefix}Pid`],
      processStartToken: state?.[`${prefix}ProcessStartToken`]
    }, {
      processIdentityObserver: this.processIdentityObserver,
      kind
    });
  }

  async terminateOwnedIdentity(identity, prefix, kind = 'RECOVERY_PROCESS') {
    if (!identity) return false;
    if (!prefix) {
      throw Object.assign(new Error('Recovery Plane exact termination requires a stored receipt prefix.'), {
        code: `${kind}_PROCESS_STATE_UNVERIFIED`
      });
    }
    const state = this.readState();
    if (!sameStoredProcessReceipt(state, prefix, identity)) {
      throw Object.assign(new Error('Recovery Plane process state changed before exact termination.'), {
        code: `${kind}_PROCESS_STATE_CHANGED`
      });
    }
    const current = await this.exactIdentity(state, prefix, kind);
    if (!current) return false;
    if (!sameProcessIdentity(identity, current)) {
      throw Object.assign(new Error('Recovery Plane process identity changed before exact termination.'), {
        code: `${kind}_PROCESS_IDENTITY_CHANGED`
      });
    }
    await this.exactProcessTerminator(identity, {
      observeProcessIdentity: this.processIdentityObserver
    });
    return true;
  }

  captureSpawnedIdentity(pid, kind) {
    return captureSpawnedProcessIdentity(pid, {
      processIdentityObserver: this.processIdentityObserver,
      sleep: this.identitySleep,
      kind
    });
  }

  legacyCandidateMigrationError(message = 'Legacy Recovery Tunnel candidate ownership could not be proven for this install.') {
    return Object.assign(new Error(message), { code: 'RECOVERY_TUNNEL_CANDIDATE_LEGACY_MIGRATION_UNVERIFIED' });
  }

  async stabilizeLegacyTunnelCandidate(settings, authToken, initialState, probes = {}) {
    const initialPid = Number(initialState.recoveryTunnelCandidatePid || 0);
    if (!initialPid || !isAlive(initialPid)) return initialState;
    const initialIdentity = await this.exactIdentity(initialState, 'recoveryTunnelCandidate', 'RECOVERY_TUNNEL');
    if (!initialIdentity) return initialState;
    const legacyFingerprint = recoveryTunnelFingerprint(settings, authToken, '');
    const initialOwnership = classifyStoredDeviceOwner(initialState.recoveryTunnelCandidateDeviceId, this.device.deviceId);
    if (initialOwnership === 'foreign') {
      throw Object.assign(new Error('Recovery Tunnel candidate belongs to another device.'), { code: 'RECOVERY_TUNNEL_FOREIGN_DEVICE' });
    }
    if (initialOwnership !== 'legacy') return initialState;
    if (String(initialState.recoveryTunnelCandidateFingerprint || '') !== legacyFingerprint) {
      throw this.legacyCandidateMigrationError();
    }

    const ready = probes.tunnelReady || recoveryTunnelReady;
    const sleep = probes.wait || wait;
    const attempts = Math.max(1, Number(this.legacyCandidateStabilizationAttempts) || LEGACY_CANDIDATE_STABILIZATION_ATTEMPTS);
    const delayMs = Math.max(0, Number(this.legacyCandidateStabilizationDelayMs) || 0);
    let state = initialState;
    for (let attempt = 0; attempt < attempts; attempt += 1) {
      if (attempt > 0) state = this.readState();
      const candidatePid = Number(state.recoveryTunnelCandidatePid || 0);
      if (!candidatePid) return state;
      if (candidatePid !== initialPid) {
        throw this.legacyCandidateMigrationError('Recovery Tunnel candidate changed during legacy ownership proof.');
      }
      if (normalizeProcessStartToken(state.recoveryTunnelCandidateProcessStartToken)
        !== initialIdentity.process_start_token) {
        throw this.legacyCandidateMigrationError('Recovery Tunnel candidate OS identity changed during legacy ownership proof.');
      }
      await this.exactIdentity(state, 'recoveryTunnelCandidate', 'RECOVERY_TUNNEL');
      const ownership = classifyStoredDeviceOwner(state.recoveryTunnelCandidateDeviceId, this.device.deviceId);
      if (ownership === 'foreign') {
        throw Object.assign(new Error('Recovery Tunnel candidate belongs to another device.'), { code: 'RECOVERY_TUNNEL_FOREIGN_DEVICE' });
      }
      if (ownership === 'owned') return state;
      if (ownership !== 'legacy' || String(state.recoveryTunnelCandidateFingerprint || '') !== legacyFingerprint) {
        throw this.legacyCandidateMigrationError();
      }
      if (!isAlive(candidatePid)) return state;
      if (await ready(this.paths, settings.recoveryHealthPort, candidatePid)) return state;
      if (attempt + 1 < attempts && delayMs > 0) await sleep(delayMs);
    }
    throw this.legacyCandidateMigrationError();
  }

  async preflightLegacyOwnershipMigration(settings, authToken, probes = {}) {
    if (!this.device) return { required: false, recoveryMcpPid: null, recoveryTunnelPid: null, recoveryTunnelCandidatePid: null };
    let state = this.readState();
    let candidatePid = Number(state.recoveryTunnelCandidatePid || 0);
    if (candidatePid > 0 && isAlive(candidatePid)) {
      const candidateOwnership = classifyStoredDeviceOwner(state.recoveryTunnelCandidateDeviceId, this.device.deviceId);
      if (candidateOwnership === 'legacy') {
        state = await this.stabilizeLegacyTunnelCandidate(settings, authToken, state, probes);
      }
    }
    const plan = {
      required: false,
      recoveryMcpPid: null,
      recoveryMcpProcessStartToken: null,
      recoveryTunnelPid: null,
      recoveryTunnelProcessStartToken: null,
      recoveryTunnelCandidatePid: null,
      recoveryTunnelCandidateProcessStartToken: null
    };
    const recoveryMcpPid = Number(state.recoveryMcpPid || 0);
    if (recoveryMcpPid > 0 && isAlive(recoveryMcpPid)) {
      const ownership = classifyStoredDeviceOwner(state.recoveryMcpDeviceId, this.device.deviceId);
      if (ownership === 'foreign') throw Object.assign(new Error('Recovery MCP belongs to another device.'), { code: 'RECOVERY_MCP_FOREIGN_DEVICE' });
      if (ownership === 'legacy') {
        const identity = await this.exactIdentity(state, 'recoveryMcp', 'RECOVERY_MCP');
        if (identity) {
          const health = await (probes.mcpHealth || recoveryMcpHealth)(settings.recoveryMcpPort, authToken);
          if (!health || Number(health.pid) !== recoveryMcpPid || Number(state.recoveryMcpPort) !== Number(settings.recoveryMcpPort)) {
            throw Object.assign(new Error('Legacy Recovery MCP ownership could not be proven for this install.'), { code: 'RECOVERY_MCP_LEGACY_MIGRATION_UNVERIFIED' });
          }
          plan.recoveryMcpPid = recoveryMcpPid;
          plan.recoveryMcpProcessStartToken = identity.process_start_token;
          plan.required = true;
        }
      }
    }
    const recoveryTunnelPid = Number(state.recoveryTunnelPid || 0);
    if (recoveryTunnelPid > 0 && isAlive(recoveryTunnelPid)) {
      const ownership = classifyStoredDeviceOwner(state.recoveryTunnelDeviceId, this.device.deviceId);
      if (ownership === 'foreign') throw Object.assign(new Error('Recovery Tunnel belongs to another device.'), { code: 'RECOVERY_TUNNEL_FOREIGN_DEVICE' });
      if (ownership === 'legacy') {
        const identity = await this.exactIdentity(state, 'recoveryTunnel', 'RECOVERY_TUNNEL');
        if (identity) {
          const ready = await (probes.tunnelReady || recoveryTunnelReady)(this.paths, settings.recoveryHealthPort, recoveryTunnelPid);
          if (!ready) throw Object.assign(new Error('Legacy Recovery Tunnel ownership could not be proven for this install.'), { code: 'RECOVERY_TUNNEL_LEGACY_MIGRATION_UNVERIFIED' });
          plan.recoveryTunnelPid = recoveryTunnelPid;
          plan.recoveryTunnelProcessStartToken = identity.process_start_token;
          plan.required = true;
        }
      }
    }
    candidatePid = Number(state.recoveryTunnelCandidatePid || 0);
    if (candidatePid > 0 && isAlive(candidatePid)) {
      const candidateOwnership = classifyStoredDeviceOwner(state.recoveryTunnelCandidateDeviceId, this.device.deviceId);
      if (candidateOwnership === 'foreign') {
        throw Object.assign(new Error('Recovery Tunnel candidate belongs to another device.'), { code: 'RECOVERY_TUNNEL_FOREIGN_DEVICE' });
      }
      if (candidateOwnership === 'legacy') {
        const identity = await this.exactIdentity(state, 'recoveryTunnelCandidate', 'RECOVERY_TUNNEL');
        if (identity) {
          const legacyFingerprint = recoveryTunnelFingerprint(settings, authToken, '');
          const ready = state.recoveryTunnelCandidateFingerprint === legacyFingerprint
            && await (probes.tunnelReady || recoveryTunnelReady)(this.paths, settings.recoveryHealthPort, candidatePid);
          if (!ready) {
            throw this.legacyCandidateMigrationError();
          }
          plan.recoveryTunnelCandidatePid = candidatePid;
          plan.recoveryTunnelCandidateProcessStartToken = identity.process_start_token;
          plan.required = true;
        }
      }
    }
    return plan;
  }

  async applyLegacyOwnershipMigration(plan) {
    if (!plan?.required || !this.device) return false;
    const state = this.readState();
    const patch = {};
    const expectedReceipts = [];
    const expectedFields = {};
    if (plan.recoveryMcpPid) {
      if (Number(state.recoveryMcpPid) !== Number(plan.recoveryMcpPid)
        || normalizeProcessStartToken(state.recoveryMcpProcessStartToken) !== plan.recoveryMcpProcessStartToken
        || classifyStoredDeviceOwner(state.recoveryMcpDeviceId, this.device.deviceId) !== 'legacy') {
        throw Object.assign(new Error('Recovery MCP changed after legacy migration preflight.'), { code: 'RECOVERY_LEGACY_MIGRATION_STATE_CHANGED' });
      }
      const identity = await this.exactIdentity(state, 'recoveryMcp', 'RECOVERY_MCP');
      if (!identity || identity.process_start_token !== plan.recoveryMcpProcessStartToken) {
        throw Object.assign(new Error('Recovery MCP exited or changed after legacy migration preflight.'), { code: 'RECOVERY_LEGACY_MIGRATION_STATE_CHANGED' });
      }
      expectedReceipts.push(['recoveryMcp', storedProcessReceipt(state, 'recoveryMcp')]);
      expectedFields.recoveryMcpDeviceId = state.recoveryMcpDeviceId;
      expectedFields.recoveryMcpDeviceInstanceId = state.recoveryMcpDeviceInstanceId;
      patch.recoveryMcpDeviceId = this.device.deviceId;
      patch.recoveryMcpDeviceInstanceId = this.device.deviceInstanceId;
    }
    if (plan.recoveryTunnelPid) {
      if (Number(state.recoveryTunnelPid) !== Number(plan.recoveryTunnelPid)
        || normalizeProcessStartToken(state.recoveryTunnelProcessStartToken) !== plan.recoveryTunnelProcessStartToken
        || classifyStoredDeviceOwner(state.recoveryTunnelDeviceId, this.device.deviceId) !== 'legacy') {
        throw Object.assign(new Error('Recovery Tunnel changed after legacy migration preflight.'), { code: 'RECOVERY_LEGACY_MIGRATION_STATE_CHANGED' });
      }
      const identity = await this.exactIdentity(state, 'recoveryTunnel', 'RECOVERY_TUNNEL');
      if (!identity || identity.process_start_token !== plan.recoveryTunnelProcessStartToken) {
        throw Object.assign(new Error('Recovery Tunnel exited or changed after legacy migration preflight.'), { code: 'RECOVERY_LEGACY_MIGRATION_STATE_CHANGED' });
      }
      expectedReceipts.push(['recoveryTunnel', storedProcessReceipt(state, 'recoveryTunnel')]);
      expectedFields.recoveryTunnelDeviceId = state.recoveryTunnelDeviceId;
      expectedFields.recoveryTunnelDeviceInstanceId = state.recoveryTunnelDeviceInstanceId;
      patch.recoveryTunnelDeviceId = this.device.deviceId;
      patch.recoveryTunnelDeviceInstanceId = this.device.deviceInstanceId;
    }
    if (plan.recoveryTunnelCandidatePid) {
      if (Number(state.recoveryTunnelCandidatePid) !== Number(plan.recoveryTunnelCandidatePid)
        || normalizeProcessStartToken(state.recoveryTunnelCandidateProcessStartToken) !== plan.recoveryTunnelCandidateProcessStartToken
        || classifyStoredDeviceOwner(state.recoveryTunnelCandidateDeviceId, this.device.deviceId) !== 'legacy') {
        throw Object.assign(new Error('Recovery Tunnel candidate changed after legacy migration preflight.'), { code: 'RECOVERY_LEGACY_MIGRATION_STATE_CHANGED' });
      }
      const identity = await this.exactIdentity(state, 'recoveryTunnelCandidate', 'RECOVERY_TUNNEL');
      if (!identity || identity.process_start_token !== plan.recoveryTunnelCandidateProcessStartToken) {
        throw Object.assign(new Error('Recovery Tunnel candidate exited or changed after legacy migration preflight.'), { code: 'RECOVERY_LEGACY_MIGRATION_STATE_CHANGED' });
      }
      expectedReceipts.push(['recoveryTunnelCandidate', storedProcessReceipt(state, 'recoveryTunnelCandidate')]);
      expectedFields.recoveryTunnelCandidateDeviceId = state.recoveryTunnelCandidateDeviceId;
      expectedFields.recoveryTunnelCandidateDeviceInstanceId = state.recoveryTunnelCandidateDeviceInstanceId;
      patch.recoveryTunnelCandidateDeviceId = this.device.deviceId;
      patch.recoveryTunnelCandidateDeviceInstanceId = this.device.deviceInstanceId;
    }
    this.updateState(patch, (value) => expectedReceipts.every(([prefix, receipt]) => sameStoredProcessReceipt(value, prefix, receipt))
      && stateFieldsMatch(value, expectedFields), 'RECOVERY_LEGACY_MIGRATION_STATE_CHANGED');
    this.log?.info?.('Legacy Recovery Plane ownership proven; rotating services into device-aware mode', {
      recoveryMcpPid: plan.recoveryMcpPid || null,
      recoveryTunnelPid: plan.recoveryTunnelPid || null,
      deviceId: this.device.deviceId
    });
    return true;
  }

  async deactivateOwnedTunnel(state, { configured, tunnelState, errorCode = null }) {
    const tunnelIdentity = await this.ownedIdentity(state, 'recoveryTunnel', 'RECOVERY_TUNNEL');
    // Validate the candidate receipt independently even when its numeric PID
    // equals the primary.  PID equality alone is not an identity proof.
    const candidateIdentity = await this.ownedIdentity(state, 'recoveryTunnelCandidate', 'RECOVERY_TUNNEL');
    const identities = [
      ['recoveryTunnel', tunnelIdentity],
      ['recoveryTunnelCandidate', candidateIdentity]
    ];
    const terminated = [];
    for (const [prefix, identity] of identities) {
      if (!identity || terminated.some((value) => sameProcessIdentity(value, identity))) continue;
      await this.terminateOwnedIdentity(identity, prefix, 'RECOVERY_TUNNEL');
      terminated.push(identity);
    }
    const tunnelReceipt = storedProcessReceipt(state, 'recoveryTunnel');
    const candidateReceipt = storedProcessReceipt(state, 'recoveryTunnelCandidate');
    this.updateState({
      recoveryTunnelPid: null,
      recoveryTunnelProcessStartToken: null,
      recoveryTunnelInstanceId: null,
      recoveryTunnelFingerprint: null,
      recoveryTunnelActivationEpochId: null,
      recoveryTunnelCandidatePid: null,
      recoveryTunnelCandidateProcessStartToken: null,
      recoveryTunnelCandidateInstanceId: null,
      recoveryTunnelCandidateFingerprint: null,
      recoveryTunnelCandidateActivationEpochId: null,
      recoveryTunnelCandidateStartedAt: null,
      recoveryTunnelDeviceId: null,
      recoveryTunnelDeviceInstanceId: null,
      recoveryTunnelCandidateDeviceId: null,
      recoveryTunnelCandidateDeviceInstanceId: null,
      recoveryTunnelConfigured: configured,
      recoveryTunnelState: tunnelState,
      recoveryTunnelLastErrorCode: errorCode
    }, (value) => sameStoredProcessReceipt(value, 'recoveryTunnel', tunnelReceipt)
      && sameStoredProcessReceipt(value, 'recoveryTunnelCandidate', candidateReceipt), 'RECOVERY_TUNNEL_PROCESS_STATE_CHANGED');
    return { state: tunnelState, configured, pid: null, instance_id: null, ...(errorCode ? { error_code: errorCode } : {}) };
  }

  async ensureMcp(settings, authToken) {
    if (String(authToken || '').length < 32) throw Object.assign(new Error('Recovery MCP auth token is unavailable.'), { code: 'RECOVERY_MCP_AUTH_UNAVAILABLE' });
    const python = this.paths.portablePython();
    const script = this.paths.recoveryMcpScript();
    if (!fs.existsSync(python) || !fs.existsSync(script)) throw Object.assign(new Error('Recovery MCP runtime files are missing.'), { code: 'RECOVERY_MCP_FILES_MISSING' });
    const scriptRevision = fileSha256(script);
    const fingerprint = recoveryFingerprint(settings, scriptRevision, authToken, this.device?.deviceId || '', this.device?.deviceInstanceId || '', this.activationEpochId);
    const state = this.readState();
    const existingReceipt = storedProcessReceipt(state, 'recoveryMcp');
    const existingIdentity = await this.ownedIdentity(state, 'recoveryMcp', 'RECOVERY_MCP');
    const currentChecks = {
      instance_id_present: Boolean(state.recoveryMcpInstanceId),
      exact_process_identity: Boolean(existingIdentity),
      fingerprint_matches: state.recoveryMcpFingerprint === fingerprint,
      port_matches: Number(state.recoveryMcpPort) === Number(settings.recoveryMcpPort),
      device_instance_matches: !this.device || state.recoveryMcpDeviceInstanceId === this.device.deviceInstanceId,
      activation_epoch_matches: String(state.recoveryMcpActivationEpochId || '') === String(this.activationEpochId || '')
    };
    const prerequisitesMatch = Object.values(currentChecks).every(Boolean);
    const currentHealth = prerequisitesMatch
      ? await recoveryMcpHealthObservation(
        settings.recoveryMcpPort,
        authToken,
        this.device?.deviceId || '',
        this.device?.deviceInstanceId || '',
        this.activationEpochId,
        state.recoveryMcpPid,
        state.recoveryMcpInstanceId,
        { timeoutMs: RECOVERY_MCP_ACTIVATION_HEALTH_TIMEOUT_MS }
      )
      : { ok: false, failure_kind: 'prerequisite_mismatch', payload: null };
    currentChecks.health_verified = currentHealth.ok === true;
    let replacementReason = Object.entries(currentChecks).find(([, matches]) => !matches)?.[0]
      || currentHealth.failure_kind
      || null;
    this.lastMcpCurrentObservation = {
      current: Object.values(currentChecks).every(Boolean),
      failure_kind: replacementReason,
      checks: currentChecks,
      health_failure_kind: currentHealth.failure_kind || null
    };
    const current = this.lastMcpCurrentObservation.current;
    if (current) {
      const latestState = this.readState();
      const latestIdentity = await this.ownedIdentity(latestState, 'recoveryMcp', 'RECOVERY_MCP');
      if (latestIdentity && sameProcessIdentity(existingIdentity, latestIdentity)
        && latestState.recoveryMcpFingerprint === fingerprint
        && latestState.recoveryMcpInstanceId === state.recoveryMcpInstanceId) {
        return {
          state: 'healthy',
          pid: latestState.recoveryMcpPid,
          process_start_token: latestIdentity.process_start_token,
          instance_id: latestState.recoveryMcpInstanceId,
          port: settings.recoveryMcpPort,
          revision: scriptRevision,
          replaced: false,
          device_id: this.device?.deviceId || null,
          device_instance_id: this.device?.deviceInstanceId || null,
          activation_epoch_id: this.activationEpochId || null
        };
      }
      replacementReason = 'confirmation_state_changed';
      this.lastMcpCurrentObservation = {
        ...this.lastMcpCurrentObservation,
        current: false,
        failure_kind: replacementReason
      };
    }
    if (existingIdentity) await this.terminateOwnedIdentity(existingIdentity, 'recoveryMcp', 'RECOVERY_MCP');
    if (existingIdentity || existingReceipt.pid || existingReceipt.process_start_token) {
      this.updateState({ recoveryMcpPid: null, recoveryMcpProcessStartToken: null, recoveryMcpInstanceId: null, recoveryMcpPort: null, recoveryMcpFingerprint: null, recoveryMcpRevision: null, recoveryMcpStartedAt: null, recoveryMcpDeviceId: null, recoveryMcpDeviceInstanceId: null, recoveryMcpActivationEpochId: null }, (value) => sameStoredProcessReceipt(value, 'recoveryMcp', existingReceipt), 'RECOVERY_MCP_PROCESS_STATE_CHANGED');
    }
    ensureParent(this.paths.recoveryMcpLogFile());
    rotateLog(this.paths.recoveryMcpLogFile());
    const output = fs.openSync(this.paths.recoveryMcpLogFile(), 'a');
    let child;
    let spawnedIdentity;
    const recoveryMcpInstanceId = instanceId();
    try {
      const env = { ...process.env, WEBCODEX_RECOVERY_AUTH_TOKEN: authToken };
      if (this.device) { env.WEBCODEX_RECOVERY_DEVICE_ID = this.device.deviceId; env.WEBCODEX_RECOVERY_DEVICE_INSTANCE_ID = this.device.deviceInstanceId; env.WEBCODEX_RECOVERY_DEVICE_DISPLAY_NAME = this.device.displayName; }
      if (this.activationEpochId) env.WEBCODEX_ACTIVATION_EPOCH_ID = this.activationEpochId;
      env.WEBCODEX_RECOVERY_MCP_INSTANCE_ID = recoveryMcpInstanceId;
      child = spawn(python, ['-u', script, '--host', '127.0.0.1', '--port', String(settings.recoveryMcpPort), '--data-root', this.paths.dataRoot()], { detached: true, windowsHide: true, stdio: ['ignore', output, output], env });
      await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); });
      child.unref();
      spawnedIdentity = await this.captureSpawnedIdentity(child.pid, 'RECOVERY_MCP');
    } finally { fs.closeSync(output); }
    try {
      this.updateState({ recoveryMcpPid: child.pid, recoveryMcpProcessStartToken: spawnedIdentity.process_start_token, recoveryMcpInstanceId, recoveryMcpPort: Number(settings.recoveryMcpPort), recoveryMcpFingerprint: fingerprint, recoveryMcpRevision: scriptRevision, recoveryMcpStartedAt: new Date().toISOString(), recoveryMcpDeviceId: this.device?.deviceId || null, recoveryMcpDeviceInstanceId: this.device?.deviceInstanceId || null, recoveryMcpActivationEpochId: this.activationEpochId || null }, (value) => sameStoredProcessReceipt(value, 'recoveryMcp', { pid: null, process_start_token: null }), 'RECOVERY_MCP_PROCESS_STATE_CHANGED');
    } catch (error) {
      try {
        await this.exactProcessTerminator(spawnedIdentity, { observeProcessIdentity: this.processIdentityObserver });
      } catch (cleanupError) {
        throw persistenceCleanupFailure('RECOVERY_MCP', error, cleanupError);
      }
      throw error;
    }
    for (let index = 0; index < RECOVERY_MCP_START_ATTEMPTS; index += 1) {
      if (!isAlive(child.pid)) break;
      if (await recoveryMcpHealth(settings.recoveryMcpPort, authToken, this.device?.deviceId || '', this.device?.deviceInstanceId || '', this.activationEpochId, child.pid, recoveryMcpInstanceId, { timeoutMs: RECOVERY_MCP_ACTIVATION_HEALTH_TIMEOUT_MS })) {
        const latestState = this.readState();
        const latestIdentity = await this.ownedIdentity(latestState, 'recoveryMcp', 'RECOVERY_MCP');
        if (latestIdentity && sameProcessIdentity(spawnedIdentity, latestIdentity)
          && latestState.recoveryMcpInstanceId === recoveryMcpInstanceId
          && latestState.recoveryMcpFingerprint === fingerprint) {
          return { state: 'healthy', pid: child.pid, process_start_token: latestIdentity.process_start_token, instance_id: recoveryMcpInstanceId, port: settings.recoveryMcpPort, revision: scriptRevision, replaced: true, replacement_reason: replacementReason, device_id: this.device?.deviceId || null, device_instance_id: this.device?.deviceInstanceId || null, activation_epoch_id: this.activationEpochId || null };
        }
      }
      await new Promise((resolve) => setTimeout(resolve, 200));
    }
    await this.terminateOwnedIdentity(spawnedIdentity, 'recoveryMcp', 'RECOVERY_MCP');
    this.updateState({ recoveryMcpPid: null, recoveryMcpProcessStartToken: null, recoveryMcpInstanceId: null, recoveryMcpDeviceId: null, recoveryMcpDeviceInstanceId: null, recoveryMcpActivationEpochId: null }, (value) => sameStoredProcessReceipt(value, 'recoveryMcp', spawnedIdentity), 'RECOVERY_MCP_PROCESS_STATE_CHANGED');
    throw Object.assign(new Error('Recovery MCP failed its local readiness check.'), { code: 'RECOVERY_MCP_NOT_READY' });
  }

  async ensureTunnel(settings, runtimeApiKey, authToken) {
    const state = this.readState();
    const tunnelId = String(settings.recoveryTunnelId || '').trim();
    if (!tunnelId) {
      return this.deactivateOwnedTunnel(state, { configured: false, tunnelState: 'not_configured' });
    }
    if (tunnelId === String(settings.tunnelId || '').trim()) {
      return this.deactivateOwnedTunnel(state, { configured: true, tunnelState: 'blocked_shared_tunnel_id', errorCode: 'RECOVERY_TUNNEL_ID_NOT_INDEPENDENT' });
    }
    if (!runtimeApiKey) {
      return this.deactivateOwnedTunnel(state, { configured: true, tunnelState: 'blocked_missing_runtime_key', errorCode: 'RECOVERY_TUNNEL_RUNTIME_KEY_MISSING' });
    }
    if (!fs.existsSync(this.paths.tunnelExecutable())) throw Object.assign(new Error('Recovery Tunnel executable is missing.'), { code: 'RECOVERY_TUNNEL_EXECUTABLE_MISSING' });
    const fingerprint = recoveryTunnelFingerprint(settings, authToken, this.device?.deviceId || '', this.activationEpochId);
    const primaryReceipt = storedProcessReceipt(state, 'recoveryTunnel');
    const candidateReceipt = storedProcessReceipt(state, 'recoveryTunnelCandidate');
    const primaryIdentity = await this.ownedIdentity(state, 'recoveryTunnel', 'RECOVERY_TUNNEL');
    const candidateIdentity = await this.ownedIdentity(state, 'recoveryTunnelCandidate', 'RECOVERY_TUNNEL');
    const current = Boolean(state.recoveryTunnelInstanceId)
      && Boolean(primaryIdentity)
      && state.recoveryTunnelFingerprint === fingerprint
      && String(state.recoveryTunnelActivationEpochId || '') === String(this.activationEpochId || '')
      && await recoveryTunnelReady(this.paths, settings.recoveryHealthPort, state.recoveryTunnelPid);
    if (current) {
      const latestState = this.readState();
      const latestIdentity = await this.ownedIdentity(latestState, 'recoveryTunnel', 'RECOVERY_TUNNEL');
      const latestReady = latestIdentity
        && sameProcessIdentity(primaryIdentity, latestIdentity)
        && latestState.recoveryTunnelFingerprint === fingerprint
        && latestState.recoveryTunnelInstanceId === state.recoveryTunnelInstanceId
        && latestState.recoveryTunnelActivationEpochId === state.recoveryTunnelActivationEpochId
        && await recoveryTunnelReady(this.paths, settings.recoveryHealthPort, latestState.recoveryTunnelPid);
      const finalState = latestReady ? this.readState() : null;
      const finalIdentity = finalState && await this.ownedIdentity(finalState, 'recoveryTunnel', 'RECOVERY_TUNNEL');
      if (finalIdentity
        && sameProcessIdentity(latestIdentity, finalIdentity)
        && finalState.recoveryTunnelFingerprint === fingerprint
        && finalState.recoveryTunnelInstanceId === state.recoveryTunnelInstanceId
        && finalState.recoveryTunnelActivationEpochId === state.recoveryTunnelActivationEpochId) {
        return {
          state: 'healthy',
          configured: true,
          pid: finalState.recoveryTunnelPid,
          process_start_token: finalIdentity.process_start_token,
          instance_id: finalState.recoveryTunnelInstanceId,
          health_port: settings.recoveryHealthPort,
          replaced: false,
          device_id: this.device?.deviceId || null,
          activation_epoch_id: this.activationEpochId || null
        };
      }
    }

    const candidatePid = Number(state.recoveryTunnelCandidatePid || 0);
    const matchingCandidate = Boolean(candidateIdentity)
      && state.recoveryTunnelCandidateFingerprint === fingerprint
      && Boolean(String(state.recoveryTunnelCandidateInstanceId || '').trim());
    const terminated = [];
    const terminateOnce = async (identity, prefix) => {
      if (!identity || terminated.some((value) => sameProcessIdentity(value, identity))) return;
      await this.terminateOwnedIdentity(identity, prefix, 'RECOVERY_TUNNEL');
      terminated.push(identity);
    };
    if (matchingCandidate) {
      for (let index = 0; index < RECOVERY_TUNNEL_START_ATTEMPTS; index += 1) {
        if (await recoveryTunnelReady(this.paths, settings.recoveryHealthPort, candidatePid)) {
          const latestState = this.readState();
          const latestCandidate = await this.ownedIdentity(latestState, 'recoveryTunnelCandidate', 'RECOVERY_TUNNEL');
          const latestPrimary = await this.ownedIdentity(latestState, 'recoveryTunnel', 'RECOVERY_TUNNEL');
          const candidateInstanceId = String(latestState.recoveryTunnelCandidateInstanceId || '').trim();
          if (!latestCandidate || !sameProcessIdentity(candidateIdentity, latestCandidate)
            || latestState.recoveryTunnelCandidateFingerprint !== fingerprint
            || !candidateInstanceId
            || (latestPrimary && !sameStoredProcessReceipt(latestState, 'recoveryTunnel', primaryReceipt))) {
            throw Object.assign(new Error('Recovery Tunnel state changed before candidate promotion.'), { code: 'RECOVERY_TUNNEL_PROCESS_STATE_CHANGED' });
          }
          const startedAt = latestState.recoveryTunnelCandidateStartedAt || new Date().toISOString();
          this.updateState({ recoveryTunnelPid: candidatePid, recoveryTunnelProcessStartToken: latestCandidate.process_start_token, recoveryTunnelInstanceId: candidateInstanceId, recoveryTunnelFingerprint: fingerprint, recoveryTunnelActivationEpochId: this.activationEpochId || null, recoveryTunnelDeviceId: this.device?.deviceId || null, recoveryTunnelDeviceInstanceId: latestState.recoveryTunnelCandidateDeviceInstanceId || this.device?.deviceInstanceId || null, recoveryTunnelCandidatePid: null, recoveryTunnelCandidateProcessStartToken: null, recoveryTunnelCandidateInstanceId: null, recoveryTunnelCandidateFingerprint: null, recoveryTunnelCandidateActivationEpochId: null, recoveryTunnelCandidateStartedAt: null, recoveryTunnelCandidateDeviceId: null, recoveryTunnelCandidateDeviceInstanceId: null, recoveryTunnelConfigured: true, recoveryTunnelState: 'healthy', recoveryTunnelLastErrorCode: null, recoveryTunnelStartedAt: startedAt }, (value) => sameStoredProcessReceipt(value, 'recoveryTunnelCandidate', candidateReceipt)
            && sameStoredProcessReceipt(value, 'recoveryTunnel', primaryReceipt)
            && stateFieldsMatch(value, { recoveryTunnelCandidateFingerprint: fingerprint, recoveryTunnelCandidateInstanceId: candidateInstanceId }), 'RECOVERY_TUNNEL_PROCESS_STATE_CHANGED');
          return { state: 'healthy', configured: true, pid: candidatePid, process_start_token: latestCandidate.process_start_token, instance_id: candidateInstanceId, health_port: settings.recoveryHealthPort, replaced: false, adopted_candidate: true, device_id: this.device?.deviceId || null, activation_epoch_id: this.activationEpochId || null };
        }
        if (!isAlive(candidatePid)) break;
        await new Promise((resolve) => setTimeout(resolve, 500));
      }
      if (candidateIdentity) await terminateOnce(candidateIdentity, 'recoveryTunnelCandidate');
      this.updateState({ recoveryTunnelCandidatePid: null, recoveryTunnelCandidateProcessStartToken: null, recoveryTunnelCandidateInstanceId: null, recoveryTunnelCandidateFingerprint: null, recoveryTunnelCandidateActivationEpochId: null, recoveryTunnelCandidateStartedAt: null, recoveryTunnelCandidateDeviceId: null, recoveryTunnelCandidateDeviceInstanceId: null }, (value) => sameStoredProcessReceipt(value, 'recoveryTunnelCandidate', candidateReceipt), 'RECOVERY_TUNNEL_PROCESS_STATE_CHANGED');
    }

    if (candidateIdentity && !matchingCandidate) {
      await terminateOnce(candidateIdentity, 'recoveryTunnelCandidate');
      this.updateState({ recoveryTunnelCandidatePid: null, recoveryTunnelCandidateProcessStartToken: null, recoveryTunnelCandidateInstanceId: null, recoveryTunnelCandidateFingerprint: null, recoveryTunnelCandidateActivationEpochId: null, recoveryTunnelCandidateStartedAt: null, recoveryTunnelCandidateDeviceId: null, recoveryTunnelCandidateDeviceInstanceId: null }, (value) => sameStoredProcessReceipt(value, 'recoveryTunnelCandidate', candidateReceipt), 'RECOVERY_TUNNEL_PROCESS_STATE_CHANGED');
    } else if (!candidateIdentity && (candidateReceipt.pid || candidateReceipt.process_start_token)) {
      this.updateState({ recoveryTunnelCandidatePid: null, recoveryTunnelCandidateProcessStartToken: null, recoveryTunnelCandidateInstanceId: null, recoveryTunnelCandidateFingerprint: null, recoveryTunnelCandidateActivationEpochId: null, recoveryTunnelCandidateStartedAt: null, recoveryTunnelCandidateDeviceId: null, recoveryTunnelCandidateDeviceInstanceId: null }, (value) => sameStoredProcessReceipt(value, 'recoveryTunnelCandidate', candidateReceipt), 'RECOVERY_TUNNEL_PROCESS_STATE_CHANGED');
    }
    if (primaryIdentity) {
      await terminateOnce(primaryIdentity, 'recoveryTunnel');
      this.updateState({ recoveryTunnelPid: null, recoveryTunnelProcessStartToken: null, recoveryTunnelInstanceId: null, recoveryTunnelFingerprint: null, recoveryTunnelActivationEpochId: null, recoveryTunnelDeviceId: null, recoveryTunnelDeviceInstanceId: null }, (value) => sameStoredProcessReceipt(value, 'recoveryTunnel', primaryReceipt), 'RECOVERY_TUNNEL_PROCESS_STATE_CHANGED');
    } else if (primaryReceipt.pid || primaryReceipt.process_start_token) {
      this.updateState({ recoveryTunnelPid: null, recoveryTunnelProcessStartToken: null, recoveryTunnelInstanceId: null, recoveryTunnelFingerprint: null, recoveryTunnelActivationEpochId: null, recoveryTunnelDeviceId: null, recoveryTunnelDeviceInstanceId: null }, (value) => sameStoredProcessReceipt(value, 'recoveryTunnel', primaryReceipt), 'RECOVERY_TUNNEL_PROCESS_STATE_CHANGED');
    }

    const refreshedListenerPid = await recoveryTunnelListenerPid(settings.recoveryHealthPort);
    if (refreshedListenerPid) {
      const errorCode = 'RECOVERY_TUNNEL_HEALTH_PORT_IN_USE';
      this.updateState({ recoveryTunnelConfigured: true, recoveryTunnelState: 'blocked_health_port_in_use', recoveryTunnelLastErrorCode: errorCode }, (value) => sameStoredProcessReceipt(value, 'recoveryTunnel', { pid: null, process_start_token: null })
        && sameStoredProcessReceipt(value, 'recoveryTunnelCandidate', { pid: null, process_start_token: null }), 'RECOVERY_TUNNEL_PROCESS_STATE_CHANGED');
      throw Object.assign(new Error('Recovery Tunnel health port is owned by an unrecognized process; refusing to replace or adopt it.'), { code: errorCode });
    }

    ensureParent(this.paths.recoveryTunnelLogFile());
    rotateLog(this.paths.recoveryTunnelLogFile());
    const output = fs.openSync(this.paths.recoveryTunnelLogFile(), 'a');
    const env = { ...process.env, CONTROL_PLANE_API_KEY: runtimeApiKey, MCP_RUNTIME_HEADER_VALUE: `Bearer ${authToken}` };
    if (this.activationEpochId) env.WEBCODEX_ACTIVATION_EPOCH_ID = this.activationEpochId;
    const args = ['run', '--control-plane.tunnel-id', tunnelId, '--control-plane.api-key', 'env:CONTROL_PLANE_API_KEY', '--health.listen-addr', `127.0.0.1:${settings.recoveryHealthPort}`, '--mcp.server-url', `url=http://127.0.0.1:${settings.recoveryMcpPort}/mcp,channel=main`, '--mcp.extra-headers', 'Authorization: env:MCP_RUNTIME_HEADER_VALUE', '--mcp.discovery-extra-headers', 'Authorization: env:MCP_RUNTIME_HEADER_VALUE', '--log.file', this.paths.recoveryTunnelLogFile()];
    const proxyUrl = Object.prototype.hasOwnProperty.call(settings, 'effectiveProxyUrl') ? settings.effectiveProxyUrl : settings.proxyUrl;
    if (proxyUrl) args.push('--control-plane.http-proxy', proxyUrl);
    let child;
    let spawnedIdentity;
    try {
      child = spawn(this.paths.tunnelExecutable(), args, { detached: true, windowsHide: true, stdio: ['ignore', output, output], env });
      await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); });
      child.unref();
      spawnedIdentity = await this.captureSpawnedIdentity(child.pid, 'RECOVERY_TUNNEL');
    } finally { fs.closeSync(output); }
    const candidateStartedAt = new Date().toISOString();
    const recoveryTunnelInstanceId = instanceId();
    try {
      this.updateState({ recoveryTunnelCandidatePid: child.pid, recoveryTunnelCandidateProcessStartToken: spawnedIdentity.process_start_token, recoveryTunnelCandidateInstanceId: recoveryTunnelInstanceId, recoveryTunnelCandidateFingerprint: fingerprint, recoveryTunnelCandidateActivationEpochId: this.activationEpochId || null, recoveryTunnelCandidateStartedAt: candidateStartedAt, recoveryTunnelCandidateDeviceId: this.device?.deviceId || null, recoveryTunnelCandidateDeviceInstanceId: this.device?.deviceInstanceId || null, recoveryTunnelConfigured: true, recoveryTunnelState: 'starting', recoveryTunnelLastErrorCode: null }, (value) => sameStoredProcessReceipt(value, 'recoveryTunnelCandidate', { pid: null, process_start_token: null })
        && sameStoredProcessReceipt(value, 'recoveryTunnel', { pid: null, process_start_token: null }), 'RECOVERY_TUNNEL_PROCESS_STATE_CHANGED');
    } catch (error) {
      try {
        await this.exactProcessTerminator(spawnedIdentity, { observeProcessIdentity: this.processIdentityObserver });
      } catch (cleanupError) {
        throw persistenceCleanupFailure('RECOVERY_TUNNEL', error, cleanupError);
      }
      throw error;
    }
    for (let index = 0; index < RECOVERY_TUNNEL_START_ATTEMPTS; index += 1) {
      if (await recoveryTunnelReady(this.paths, settings.recoveryHealthPort, child.pid)) {
        const latestState = this.readState();
        const latestCandidate = await this.ownedIdentity(latestState, 'recoveryTunnelCandidate', 'RECOVERY_TUNNEL');
        if (!latestCandidate || !sameProcessIdentity(spawnedIdentity, latestCandidate)
          || latestState.recoveryTunnelCandidateInstanceId !== recoveryTunnelInstanceId
          || latestState.recoveryTunnelCandidateFingerprint !== fingerprint) {
          throw Object.assign(new Error('Recovery Tunnel identity changed before promotion.'), { code: 'RECOVERY_TUNNEL_PROCESS_IDENTITY_CHANGED' });
        }
        this.updateState({ recoveryTunnelPid: child.pid, recoveryTunnelProcessStartToken: latestCandidate.process_start_token, recoveryTunnelInstanceId: recoveryTunnelInstanceId, recoveryTunnelFingerprint: fingerprint, recoveryTunnelActivationEpochId: this.activationEpochId || null, recoveryTunnelDeviceId: this.device?.deviceId || null, recoveryTunnelDeviceInstanceId: this.device?.deviceInstanceId || null, recoveryTunnelCandidatePid: null, recoveryTunnelCandidateProcessStartToken: null, recoveryTunnelCandidateInstanceId: null, recoveryTunnelCandidateFingerprint: null, recoveryTunnelCandidateActivationEpochId: null, recoveryTunnelCandidateStartedAt: null, recoveryTunnelCandidateDeviceId: null, recoveryTunnelCandidateDeviceInstanceId: null, recoveryTunnelState: 'healthy', recoveryTunnelLastErrorCode: null, recoveryTunnelStartedAt: candidateStartedAt }, (value) => sameStoredProcessReceipt(value, 'recoveryTunnelCandidate', { pid: child.pid, process_start_token: spawnedIdentity.process_start_token })
          && sameStoredProcessReceipt(value, 'recoveryTunnel', { pid: null, process_start_token: null }), 'RECOVERY_TUNNEL_PROCESS_STATE_CHANGED');
        return { state: 'healthy', configured: true, pid: child.pid, process_start_token: latestCandidate.process_start_token, instance_id: recoveryTunnelInstanceId, health_port: settings.recoveryHealthPort, replaced: true, device_id: this.device?.deviceId || null, activation_epoch_id: this.activationEpochId || null };
      }
      if (!isAlive(child.pid)) break;
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    const exitedEarly = !isAlive(child.pid);
    await this.terminateOwnedIdentity(spawnedIdentity, 'recoveryTunnelCandidate', 'RECOVERY_TUNNEL');
    const errorCode = exitedEarly ? 'RECOVERY_TUNNEL_PROCESS_EXITED' : 'RECOVERY_TUNNEL_NOT_READY';
    this.updateState({ recoveryTunnelCandidatePid: null, recoveryTunnelCandidateProcessStartToken: null, recoveryTunnelCandidateInstanceId: null, recoveryTunnelCandidateFingerprint: null, recoveryTunnelCandidateActivationEpochId: null, recoveryTunnelCandidateStartedAt: null, recoveryTunnelCandidateDeviceId: null, recoveryTunnelCandidateDeviceInstanceId: null, recoveryTunnelState: 'failed', recoveryTunnelLastErrorCode: errorCode }, (value) => sameStoredProcessReceipt(value, 'recoveryTunnelCandidate', spawnedIdentity), 'RECOVERY_TUNNEL_PROCESS_STATE_CHANGED');
    throw Object.assign(new Error(exitedEarly ? 'Recovery Tunnel process exited before readiness.' : 'Recovery Tunnel did not complete a successful control-plane poll.'), { code: errorCode });
  }

  async ensure(settings, { authToken, runtimeApiKey, activationEpochId = undefined }) {
    if (this.ensureInFlight) return this.ensureInFlight;
    if (activationEpochId !== undefined) this.setActivationEpoch(activationEpochId);
    const operation = this.ensureOnce(settings, { authToken, runtimeApiKey });
    this.ensureInFlight = operation;
    try { return await operation; }
    finally { if (this.ensureInFlight === operation) this.ensureInFlight = null; }
  }

  async ensureOnce(settings, { authToken, runtimeApiKey }) {
    const mcp = await this.ensureMcp(settings, authToken);
    let tunnel;
    try { tunnel = await this.ensureTunnel(settings, runtimeApiKey, authToken); }
    catch (error) { tunnel = { state: 'failed', configured: Boolean(settings.recoveryTunnelId), pid: null, instance_id: null, activation_epoch_id: this.activationEpochId || null, error_code: String(error?.code || 'RECOVERY_TUNNEL_FAILED') }; this.log?.error?.(error.message, { stage: 'recovery-plane-tunnel', code: tunnel.error_code }); }
    this.lastStatus = { mode: 'independent_mcp_tunnel_v1', state: mcp.state === 'healthy' ? 'healthy' : 'degraded', activation_epoch_id: this.activationEpochId || null, device_id: this.device?.deviceId || null, device_instance_id: this.device?.deviceInstanceId || null, mcp, tunnel, checked_at: new Date().toISOString() };
    return this.lastStatus;
  }

  async stop() {
    const state = this.readState();
    const tunnelIdentity = await this.ownedIdentity(state, 'recoveryTunnel', 'RECOVERY_TUNNEL');
    const candidateIdentity = await this.ownedIdentity(state, 'recoveryTunnelCandidate', 'RECOVERY_TUNNEL');
    const mcpIdentity = await this.ownedIdentity(state, 'recoveryMcp', 'RECOVERY_MCP');
    const receipts = {
      recoveryTunnel: storedProcessReceipt(state, 'recoveryTunnel'),
      recoveryTunnelCandidate: storedProcessReceipt(state, 'recoveryTunnelCandidate'),
      recoveryMcp: storedProcessReceipt(state, 'recoveryMcp')
    };
    const terminated = [];
    for (const [prefix, identity, kind] of [
      ['recoveryTunnel', tunnelIdentity, 'RECOVERY_TUNNEL'],
      ['recoveryTunnelCandidate', candidateIdentity, 'RECOVERY_TUNNEL'],
      ['recoveryMcp', mcpIdentity, 'RECOVERY_MCP']
    ]) {
      if (!identity || terminated.some((value) => sameProcessIdentity(value, identity))) continue;
      await this.terminateOwnedIdentity(identity, prefix, kind);
      terminated.push(identity);
    }
    this.updateState({ recoveryTunnelPid: null, recoveryTunnelProcessStartToken: null, recoveryTunnelInstanceId: null, recoveryTunnelFingerprint: null, recoveryTunnelActivationEpochId: null, recoveryTunnelDeviceId: null, recoveryTunnelDeviceInstanceId: null, recoveryTunnelCandidatePid: null, recoveryTunnelCandidateProcessStartToken: null, recoveryTunnelCandidateInstanceId: null, recoveryTunnelCandidateFingerprint: null, recoveryTunnelCandidateActivationEpochId: null, recoveryTunnelCandidateStartedAt: null, recoveryTunnelCandidateDeviceId: null, recoveryTunnelCandidateDeviceInstanceId: null, recoveryMcpPid: null, recoveryMcpProcessStartToken: null, recoveryMcpInstanceId: null, recoveryMcpDeviceId: null, recoveryMcpDeviceInstanceId: null, recoveryMcpActivationEpochId: null, recoveryTunnelState: 'stopped' }, (value) => sameStoredProcessReceipt(value, 'recoveryTunnel', receipts.recoveryTunnel)
      && sameStoredProcessReceipt(value, 'recoveryTunnelCandidate', receipts.recoveryTunnelCandidate)
      && sameStoredProcessReceipt(value, 'recoveryMcp', receipts.recoveryMcp), 'RECOVERY_PROCESS_STATE_CHANGED');
    return true;
  }
}

module.exports = { RecoveryPlaneService, recoveryFingerprint, recoveryTunnelFingerprint, recoveryMcpHealth, recoveryMcpHealthObservation, recoveryTunnelListenerPid, recoveryTunnelReady, stopExactTree };
