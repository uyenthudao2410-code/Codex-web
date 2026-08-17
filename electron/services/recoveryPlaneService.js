const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const { spawn } = require('node:child_process');
const { readJson, updateJsonAtomic, ensureParent } = require('./jsonStore');
const { rotateLog } = require('./logService');
const { canConnect } = require('./environmentService');
const { run } = require('./commandRunner');
const { isAlive } = require('./nativeService');
const { runtimeDeviceIdentity, classifyStoredDeviceOwner } = require('./deviceIdentity');

const RECOVERY_MCP_START_ATTEMPTS = 30;
// tunnel-client defaults to a 30s control-plane long poll plus a 5s deadline guardrail.
// Keep startup bounded, but allow the first successful poll to complete before declaring failure.
const RECOVERY_TUNNEL_START_ATTEMPTS = 90;

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex'); }
function fileSha256(file) { return sha256(fs.readFileSync(file)); }
function recoveryFingerprint(settings, scriptRevision, authToken, deviceId = '', deviceInstanceId = '') {
  return sha256(JSON.stringify({ script_revision: scriptRevision, port: Number(settings.recoveryMcpPort), auth_token_hash: sha256(String(authToken || '')), device_id: String(deviceId || ''), device_instance_id: String(deviceInstanceId || '') }));
}
function recoveryTunnelFingerprint(settings, authToken, deviceId = '') {
  return sha256(JSON.stringify({ tunnel_id: String(settings.recoveryTunnelId || ''), mcp_port: Number(settings.recoveryMcpPort), health_port: Number(settings.recoveryHealthPort), proxy_url: String(settings.effectiveProxyUrl || settings.proxyUrl || ''), auth_token_hash: sha256(String(authToken || '')), device_id: String(deviceId || '') }));
}

function recoveryMcpHealth(port, authToken, expectedDeviceId = '', expectedDeviceInstanceId = '') {
  return new Promise((resolve) => {
    const request = http.request({ host: '127.0.0.1', port: Number(port), path: '/healthz', method: 'GET', headers: { Authorization: `Bearer ${authToken}` }, timeout: 800 }, (response) => {
      let body = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { if (body.length < 16 * 1024) body += chunk; });
      response.on('end', () => { if (response.statusCode !== 200) { resolve(null); return; } try { const payload = JSON.parse(body); const deviceMatches = !expectedDeviceId || String(payload.device_id || '').toLowerCase() === String(expectedDeviceId).toLowerCase(); const instanceMatches = !expectedDeviceInstanceId || String(payload.device_instance_id || '') === String(expectedDeviceInstanceId); resolve(payload.ok === true && payload.service === 'recovery-mcp' && deviceMatches && instanceMatches ? payload : null); } catch { resolve(null); } });
    });
    request.on('timeout', () => { request.destroy(); resolve(null); });
    request.on('error', () => resolve(null));
    request.end();
  });
}
async function stopExactTree(pid) {
  if (!isAlive(pid)) return false;
  await run('taskkill.exe', ['/PID', String(pid), '/T', '/F'], { allowFailure: true });
  return true;
}

async function recoveryTunnelListenerPid(port) {
  const result = await run('netstat.exe', ['-ano', '-p', 'tcp'], { allowFailure: true, timeoutMs: 3000 });
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
  ], { allowFailure: true, timeoutMs: 3000 });
  return result.code === 0;
}

class RecoveryPlaneService {
  constructor({ paths, log, deviceIdentity = null, deviceInstanceId = '' }) { this.paths = paths; this.log = log; this.device = (deviceIdentity || deviceInstanceId) ? runtimeDeviceIdentity(deviceIdentity, deviceInstanceId) : null; this.lastStatus = null; this.ensureInFlight = null; }
  readState() { return readJson(this.paths.recoveryPlaneStateFile(), {}); }
  updateState(patch) { updateJsonAtomic(this.paths.recoveryPlaneStateFile(), (value) => ({ ...value, version: 1, ...patch, updatedAt: new Date().toISOString() })); }
  assertOwnedLive(pid, storedDeviceId, kind) { if (!this.device || !isAlive(pid)) return; const ownership = classifyStoredDeviceOwner(storedDeviceId, this.device.deviceId); if (ownership === 'owned') return; const code = ownership === 'foreign' ? `${kind}_FOREIGN_DEVICE` : `${kind}_OWNER_UNVERIFIED`; throw Object.assign(new Error(ownership === 'foreign' ? `${kind} process state belongs to another device; refusing to adopt or terminate it.` : `${kind} process state predates device ownership metadata; refusing to adopt or terminate the live process.`), { code, ownerDeviceId: String(storedDeviceId || '') || null, expectedDeviceId: this.device.deviceId }); }

  async deactivateOwnedTunnel(state, { configured, tunnelState, errorCode = null }) {
    this.assertOwnedLive(state.recoveryTunnelPid, state.recoveryTunnelDeviceId, 'RECOVERY_TUNNEL');
    this.assertOwnedLive(state.recoveryTunnelCandidatePid, state.recoveryTunnelCandidateDeviceId, 'RECOVERY_TUNNEL');
    if (isAlive(state.recoveryTunnelPid)) await stopExactTree(state.recoveryTunnelPid);
    if (state.recoveryTunnelCandidatePid !== state.recoveryTunnelPid && isAlive(state.recoveryTunnelCandidatePid)) await stopExactTree(state.recoveryTunnelCandidatePid);
    this.updateState({
      recoveryTunnelPid: null,
      recoveryTunnelFingerprint: null,
      recoveryTunnelCandidatePid: null,
      recoveryTunnelCandidateFingerprint: null,
      recoveryTunnelCandidateStartedAt: null,
      recoveryTunnelDeviceId: null,
      recoveryTunnelDeviceInstanceId: null,
      recoveryTunnelCandidateDeviceId: null,
      recoveryTunnelCandidateDeviceInstanceId: null,
      recoveryTunnelConfigured: configured,
      recoveryTunnelState: tunnelState,
      recoveryTunnelLastErrorCode: errorCode
    });
    return { state: tunnelState, configured, pid: null, ...(errorCode ? { error_code: errorCode } : {}) };
  }

  async ensureMcp(settings, authToken) {
    if (String(authToken || '').length < 32) throw Object.assign(new Error('Recovery MCP auth token is unavailable.'), { code: 'RECOVERY_MCP_AUTH_UNAVAILABLE' });
    const python = this.paths.portablePython();
    const script = this.paths.recoveryMcpScript();
    if (!fs.existsSync(python) || !fs.existsSync(script)) throw Object.assign(new Error('Recovery MCP runtime files are missing.'), { code: 'RECOVERY_MCP_FILES_MISSING' });
    const scriptRevision = fileSha256(script);
    const fingerprint = recoveryFingerprint(settings, scriptRevision, authToken, this.device?.deviceId || '', this.device?.deviceInstanceId || '');
    const state = this.readState();
    this.assertOwnedLive(state.recoveryMcpPid, state.recoveryMcpDeviceId, 'RECOVERY_MCP');
    const current = isAlive(state.recoveryMcpPid) && state.recoveryMcpFingerprint === fingerprint && Number(state.recoveryMcpPort) === Number(settings.recoveryMcpPort) && (!this.device || state.recoveryMcpDeviceInstanceId === this.device.deviceInstanceId) && await recoveryMcpHealth(settings.recoveryMcpPort, authToken, this.device?.deviceId || '', this.device?.deviceInstanceId || '');
    if (current) return { state: 'healthy', pid: state.recoveryMcpPid, port: settings.recoveryMcpPort, revision: scriptRevision, replaced: false, device_id: this.device?.deviceId || null, device_instance_id: this.device?.deviceInstanceId || null };
    if (isAlive(state.recoveryMcpPid)) await stopExactTree(state.recoveryMcpPid);
    ensureParent(this.paths.recoveryMcpLogFile());
    rotateLog(this.paths.recoveryMcpLogFile());
    const output = fs.openSync(this.paths.recoveryMcpLogFile(), 'a');
    let child;
    try {
      const env = { ...process.env, WEBCODEX_RECOVERY_AUTH_TOKEN: authToken };
      if (this.device) { env.WEBCODEX_RECOVERY_DEVICE_ID = this.device.deviceId; env.WEBCODEX_RECOVERY_DEVICE_INSTANCE_ID = this.device.deviceInstanceId; env.WEBCODEX_RECOVERY_DEVICE_DISPLAY_NAME = this.device.displayName; }
      child = spawn(python, ['-u', script, '--host', '127.0.0.1', '--port', String(settings.recoveryMcpPort), '--data-root', this.paths.dataRoot()], { detached: true, windowsHide: true, stdio: ['ignore', output, output], env });
      await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); });
      child.unref();
    } finally { fs.closeSync(output); }
    this.updateState({ recoveryMcpPid: child.pid, recoveryMcpPort: Number(settings.recoveryMcpPort), recoveryMcpFingerprint: fingerprint, recoveryMcpRevision: scriptRevision, recoveryMcpStartedAt: new Date().toISOString(), recoveryMcpDeviceId: this.device?.deviceId || null, recoveryMcpDeviceInstanceId: this.device?.deviceInstanceId || null });
    for (let index = 0; index < RECOVERY_MCP_START_ATTEMPTS; index += 1) {
      if (!isAlive(child.pid)) break;
      if (await recoveryMcpHealth(settings.recoveryMcpPort, authToken, this.device?.deviceId || '', this.device?.deviceInstanceId || '')) return { state: 'healthy', pid: child.pid, port: settings.recoveryMcpPort, revision: scriptRevision, replaced: true, device_id: this.device?.deviceId || null, device_instance_id: this.device?.deviceInstanceId || null };
      await new Promise((resolve) => setTimeout(resolve, 200));
    }
    await stopExactTree(child.pid);
    this.updateState({ recoveryMcpPid: null, recoveryMcpDeviceId: null, recoveryMcpDeviceInstanceId: null });
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
    const fingerprint = recoveryTunnelFingerprint(settings, authToken, this.device?.deviceId || '');
    this.assertOwnedLive(state.recoveryTunnelPid, state.recoveryTunnelDeviceId, 'RECOVERY_TUNNEL');
    const current = state.recoveryTunnelFingerprint === fingerprint && await recoveryTunnelReady(this.paths, settings.recoveryHealthPort, state.recoveryTunnelPid);
    if (current) return { state: 'healthy', configured: true, pid: state.recoveryTunnelPid, health_port: settings.recoveryHealthPort, replaced: false };

    const listenerPid = await recoveryTunnelListenerPid(settings.recoveryHealthPort);
    const candidatePid = Number(state.recoveryTunnelCandidatePid || 0);
    this.assertOwnedLive(candidatePid, state.recoveryTunnelCandidateDeviceId, 'RECOVERY_TUNNEL');
    const matchingCandidate = candidatePid > 0 && state.recoveryTunnelCandidateFingerprint === fingerprint && isAlive(candidatePid);
    if (matchingCandidate) {
      for (let index = 0; index < RECOVERY_TUNNEL_START_ATTEMPTS; index += 1) {
        if (await recoveryTunnelReady(this.paths, settings.recoveryHealthPort, candidatePid)) {
          const startedAt = state.recoveryTunnelCandidateStartedAt || new Date().toISOString();
          this.updateState({ recoveryTunnelPid: candidatePid, recoveryTunnelFingerprint: fingerprint, recoveryTunnelDeviceId: this.device?.deviceId || null, recoveryTunnelDeviceInstanceId: state.recoveryTunnelCandidateDeviceInstanceId || this.device?.deviceInstanceId || null, recoveryTunnelCandidatePid: null, recoveryTunnelCandidateFingerprint: null, recoveryTunnelCandidateStartedAt: null, recoveryTunnelCandidateDeviceId: null, recoveryTunnelCandidateDeviceInstanceId: null, recoveryTunnelConfigured: true, recoveryTunnelState: 'healthy', recoveryTunnelLastErrorCode: null, recoveryTunnelStartedAt: startedAt });
          return { state: 'healthy', configured: true, pid: candidatePid, health_port: settings.recoveryHealthPort, replaced: false, adopted_candidate: true, device_id: this.device?.deviceId || null };
        }
        if (!isAlive(candidatePid)) break;
        await new Promise((resolve) => setTimeout(resolve, 500));
      }
      if (isAlive(candidatePid)) await stopExactTree(candidatePid);
      this.updateState({ recoveryTunnelCandidatePid: null, recoveryTunnelCandidateFingerprint: null, recoveryTunnelCandidateStartedAt: null, recoveryTunnelCandidateDeviceId: null, recoveryTunnelCandidateDeviceInstanceId: null });
    }

    const refreshedListenerPid = await recoveryTunnelListenerPid(settings.recoveryHealthPort);
    if (refreshedListenerPid) {
      const errorCode = 'RECOVERY_TUNNEL_HEALTH_PORT_IN_USE';
      this.updateState({ recoveryTunnelConfigured: true, recoveryTunnelState: 'blocked_health_port_in_use', recoveryTunnelLastErrorCode: errorCode });
      throw Object.assign(new Error('Recovery Tunnel health port is owned by an unrecognized process; refusing to replace or adopt it.'), { code: errorCode });
    }

    if (isAlive(state.recoveryTunnelPid)) await stopExactTree(state.recoveryTunnelPid);
    this.updateState({ recoveryTunnelPid: null, recoveryTunnelFingerprint: null, recoveryTunnelDeviceId: null, recoveryTunnelDeviceInstanceId: null });
    ensureParent(this.paths.recoveryTunnelLogFile());
    rotateLog(this.paths.recoveryTunnelLogFile());
    const output = fs.openSync(this.paths.recoveryTunnelLogFile(), 'a');
    const env = { ...process.env, CONTROL_PLANE_API_KEY: runtimeApiKey, MCP_RUNTIME_HEADER_VALUE: `Bearer ${authToken}` };
    const args = ['run', '--control-plane.tunnel-id', tunnelId, '--control-plane.api-key', 'env:CONTROL_PLANE_API_KEY', '--health.listen-addr', `127.0.0.1:${settings.recoveryHealthPort}`, '--mcp.server-url', `url=http://127.0.0.1:${settings.recoveryMcpPort}/mcp,channel=main`, '--mcp.extra-headers', 'Authorization: env:MCP_RUNTIME_HEADER_VALUE', '--mcp.discovery-extra-headers', 'Authorization: env:MCP_RUNTIME_HEADER_VALUE', '--log.file', this.paths.recoveryTunnelLogFile()];
    const proxyUrl = Object.prototype.hasOwnProperty.call(settings, 'effectiveProxyUrl') ? settings.effectiveProxyUrl : settings.proxyUrl;
    if (proxyUrl) args.push('--control-plane.http-proxy', proxyUrl);
    let child;
    try {
      child = spawn(this.paths.tunnelExecutable(), args, { detached: true, windowsHide: true, stdio: ['ignore', output, output], env });
      await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); });
      child.unref();
    } finally { fs.closeSync(output); }
    const candidateStartedAt = new Date().toISOString();
    this.updateState({ recoveryTunnelCandidatePid: child.pid, recoveryTunnelCandidateFingerprint: fingerprint, recoveryTunnelCandidateStartedAt: candidateStartedAt, recoveryTunnelCandidateDeviceId: this.device?.deviceId || null, recoveryTunnelCandidateDeviceInstanceId: this.device?.deviceInstanceId || null, recoveryTunnelConfigured: true, recoveryTunnelState: 'starting', recoveryTunnelLastErrorCode: null });
    for (let index = 0; index < RECOVERY_TUNNEL_START_ATTEMPTS; index += 1) {
      if (await recoveryTunnelReady(this.paths, settings.recoveryHealthPort, child.pid)) { this.updateState({ recoveryTunnelPid: child.pid, recoveryTunnelFingerprint: fingerprint, recoveryTunnelDeviceId: this.device?.deviceId || null, recoveryTunnelDeviceInstanceId: this.device?.deviceInstanceId || null, recoveryTunnelCandidatePid: null, recoveryTunnelCandidateFingerprint: null, recoveryTunnelCandidateStartedAt: null, recoveryTunnelCandidateDeviceId: null, recoveryTunnelCandidateDeviceInstanceId: null, recoveryTunnelState: 'healthy', recoveryTunnelLastErrorCode: null, recoveryTunnelStartedAt: candidateStartedAt }); return { state: 'healthy', configured: true, pid: child.pid, health_port: settings.recoveryHealthPort, replaced: true, device_id: this.device?.deviceId || null }; }
      if (!isAlive(child.pid)) break;
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    const exitedEarly = !isAlive(child.pid);
    if (!exitedEarly) await stopExactTree(child.pid);
    const errorCode = exitedEarly ? 'RECOVERY_TUNNEL_PROCESS_EXITED' : 'RECOVERY_TUNNEL_NOT_READY';
    this.updateState({ recoveryTunnelCandidatePid: null, recoveryTunnelCandidateFingerprint: null, recoveryTunnelCandidateStartedAt: null, recoveryTunnelCandidateDeviceId: null, recoveryTunnelCandidateDeviceInstanceId: null, recoveryTunnelState: 'failed', recoveryTunnelLastErrorCode: errorCode });
    throw Object.assign(new Error(exitedEarly ? 'Recovery Tunnel process exited before readiness.' : 'Recovery Tunnel did not complete a successful control-plane poll.'), { code: errorCode });
  }

  async ensure(settings, { authToken, runtimeApiKey }) {
    if (this.ensureInFlight) return this.ensureInFlight;
    const operation = this.ensureOnce(settings, { authToken, runtimeApiKey });
    this.ensureInFlight = operation;
    try { return await operation; }
    finally { if (this.ensureInFlight === operation) this.ensureInFlight = null; }
  }

  async ensureOnce(settings, { authToken, runtimeApiKey }) {
    const mcp = await this.ensureMcp(settings, authToken);
    let tunnel;
    try { tunnel = await this.ensureTunnel(settings, runtimeApiKey, authToken); }
    catch (error) { tunnel = { state: 'failed', configured: Boolean(settings.recoveryTunnelId), pid: null, error_code: String(error?.code || 'RECOVERY_TUNNEL_FAILED') }; this.log?.error?.(error.message, { stage: 'recovery-plane-tunnel', code: tunnel.error_code }); }
    this.lastStatus = { mode: 'independent_mcp_tunnel_v1', state: mcp.state === 'healthy' ? 'healthy' : 'degraded', device_id: this.device?.deviceId || null, device_instance_id: this.device?.deviceInstanceId || null, mcp, tunnel, checked_at: new Date().toISOString() };
    return this.lastStatus;
  }

  async stop() {
    const state = this.readState();
    this.assertOwnedLive(state.recoveryTunnelPid, state.recoveryTunnelDeviceId, 'RECOVERY_TUNNEL');
    this.assertOwnedLive(state.recoveryTunnelCandidatePid, state.recoveryTunnelCandidateDeviceId, 'RECOVERY_TUNNEL');
    this.assertOwnedLive(state.recoveryMcpPid, state.recoveryMcpDeviceId, 'RECOVERY_MCP');
    await stopExactTree(state.recoveryTunnelPid);
    if (state.recoveryTunnelCandidatePid !== state.recoveryTunnelPid) await stopExactTree(state.recoveryTunnelCandidatePid);
    await stopExactTree(state.recoveryMcpPid);
    this.updateState({ recoveryTunnelPid: null, recoveryTunnelFingerprint: null, recoveryTunnelDeviceId: null, recoveryTunnelDeviceInstanceId: null, recoveryTunnelCandidatePid: null, recoveryTunnelCandidateFingerprint: null, recoveryTunnelCandidateStartedAt: null, recoveryTunnelCandidateDeviceId: null, recoveryTunnelCandidateDeviceInstanceId: null, recoveryMcpPid: null, recoveryMcpDeviceId: null, recoveryMcpDeviceInstanceId: null, recoveryTunnelState: 'stopped' });
    return true;
  }
}

module.exports = { RecoveryPlaneService, recoveryFingerprint, recoveryTunnelFingerprint, recoveryMcpHealth, recoveryTunnelListenerPid, recoveryTunnelReady, stopExactTree };
