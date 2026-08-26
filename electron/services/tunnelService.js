const crypto = require('node:crypto');
const fs = require('node:fs');
const { spawn } = require('node:child_process');
const defaultPaths = require('../paths');
const { readJson, updateJsonAtomic, ensureParent } = require('./jsonStore');
const { rotateLog } = require('./logService');
const { canConnect } = require('./environmentService');
const { run } = require('./commandRunner');
const { isAlive } = require('./nativeService');
const { classifyStoredDeviceOwner } = require('./deviceIdentity');

function tunnelFingerprint(settings, deviceId = '', activationEpochId = '') {
  const payload = {
    device_id: String(deviceId || ''),
    tunnel_id: String(settings.tunnelId || ''),
    mcp_port: Number(settings.mcpPort),
    health_port: Number(settings.healthPort)
  };
  if (String(activationEpochId || '').trim()) payload.activation_epoch_id = String(activationEpochId).trim();
  return crypto.createHash('sha256').update(JSON.stringify(payload)).digest('hex');
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

class TunnelService {
  constructor(log, paths = defaultPaths, device = null) {
    this.log = log;
    this.paths = paths;
    this.device = device;
    this.listenerPidProbe = null;
    this.controlPlaneHealthProbe = null;
  }

  async probeControlPlaneHealth(settings, pid) {
    if (typeof this.controlPlaneHealthProbe === 'function') {
      return this.controlPlaneHealthProbe(settings, pid);
    }
    const executable = this.paths?.tunnelExecutable?.();
    if (!executable || !fs.existsSync(executable)) return false;
    const result = await run(executable, [
      'health', '--port', String(settings.healthPort), '--pid', String(pid),
      '--require-control-plane-poll', '--json'
    ], { allowFailure: true, timeoutMs: 3000 });
    return Number(result?.code) === 0;
  }

  assertOwnedLive(state) {
    if (!this.device || !isAlive(state.tunnelPid)) return;
    const ownership = classifyStoredDeviceOwner(state.tunnelDeviceId, this.device.deviceId);
    if (ownership === 'owned') return;
    const code = ownership === 'foreign' ? 'TUNNEL_PROCESS_FOREIGN_DEVICE' : 'TUNNEL_PROCESS_OWNER_UNVERIFIED';
    throw Object.assign(new Error(ownership === 'foreign' ? 'Coding Tunnel process state belongs to another device; refusing to adopt or terminate it.' : 'Coding Tunnel process state predates device ownership metadata; refusing to adopt or terminate the live process.'), { code, ownerDeviceId: String(state.tunnelDeviceId || '') || null, expectedDeviceId: this.device.deviceId });
  }

  async start(settings, runtimeApiKey, token, progress, options = {}) {
    if (!fs.existsSync(this.paths.tunnelExecutable())) throw new Error('Gói cài đặt thiếu tệp tunnel-client.exe.');
    if (!runtimeApiKey) throw new Error('Vui lòng lưu OpenAI Runtime API Key trước.');
    if (!settings.tunnelId) throw new Error('Vui lòng điền OpenAI Tunnel ID trước.');
    await this.stop();
    const activationEpochId = String(options.activationEpochId || '').trim();
    progress('tunnel-start', 72, 'Đang kết nối OpenAI MCP Tunnel');
    ensureParent(this.paths.tunnelLogFile());
    rotateLog(this.paths.tunnelLogFile());
    const output = fs.openSync(this.paths.tunnelLogFile(), 'a');
    const env = {
      ...process.env,
      CONTROL_PLANE_API_KEY: runtimeApiKey,
      MCP_RUNTIME_HEADER_VALUE: `Bearer ${token}`
    };
    if (activationEpochId) env.CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID = activationEpochId;
    const args = [
      'run',
      '--control-plane.tunnel-id', settings.tunnelId,
      '--control-plane.api-key', 'env:CONTROL_PLANE_API_KEY',
      '--health.listen-addr', `127.0.0.1:${settings.healthPort}`,
      '--mcp.server-url', `url=http://127.0.0.1:${settings.mcpPort}/mcp,channel=main`,
      '--mcp.extra-headers', 'Authorization: env:MCP_RUNTIME_HEADER_VALUE',
      '--mcp.discovery-extra-headers', 'Authorization: env:MCP_RUNTIME_HEADER_VALUE',
      '--log.file', this.paths.tunnelLogFile()
    ];
    const proxyUrl = Object.prototype.hasOwnProperty.call(settings, 'effectiveProxyUrl')
      ? settings.effectiveProxyUrl
      : settings.proxyUrl;
    if (proxyUrl) args.push('--control-plane.http-proxy', proxyUrl);
    const child = spawn(this.paths.tunnelExecutable(), args, {
      detached: true,
      windowsHide: true,
      stdio: ['ignore', output, output],
      env
    });
    child.unref();
    updateJsonAtomic(this.paths.stateFile(), (state) => ({
      ...state,
      tunnelPid: child.pid,
      tunnelId: settings.tunnelId,
      tunnelFingerprint: tunnelFingerprint(settings, this.device?.deviceId || '', activationEpochId),
      tunnelInstanceId: crypto.randomBytes(12).toString('hex'),
      tunnelActivationEpochId: activationEpochId || null,
      tunnelDeviceId: this.device?.deviceId || '',
      tunnelDeviceInstanceId: this.device?.deviceInstanceId || '',
      tunnelStartedAt: new Date().toISOString()
    }));
    for (let index = 0; index < 30; index += 1) {
      const listenerPid = await (this.listenerPidProbe || loopbackListenerPid)(settings.healthPort);
      if (listenerPid === child.pid && await canConnect('127.0.0.1', settings.healthPort, 500)) {
        const state = readJson(this.paths.stateFile(), {});
        this.log.info('OpenAI Tunnel đã khởi động', { pid: child.pid, tunnelId: settings.tunnelId, activationEpochId: activationEpochId || null });
        return { pid: child.pid, instanceId: state.tunnelInstanceId || null, activationEpochId: activationEpochId || null };
      }
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    throw new Error(`Tunnel đã khởi động nhưng cổng ${settings.healthPort} không qua kiểm tra sẵn sàng. Vui lòng xem nhật ký Tunnel.`);
  }

  async stop() {
    const state = readJson(this.paths.stateFile(), {});
    const alive = isAlive(state.tunnelPid);
    this.assertOwnedLive(state);
    if (!alive) {
      updateJsonAtomic(this.paths.stateFile(), (value) => ({ ...value, tunnelPid: null, tunnelId: '', tunnelFingerprint: '', tunnelInstanceId: null, tunnelActivationEpochId: null, tunnelDeviceId: '', tunnelDeviceInstanceId: '' }));
      return false;
    }
    await run('taskkill.exe', ['/PID', String(state.tunnelPid), '/T', '/F'], { allowFailure: true });
    updateJsonAtomic(this.paths.stateFile(), (value) => ({ ...value, tunnelPid: null, tunnelId: '', tunnelFingerprint: '', tunnelInstanceId: null, tunnelActivationEpochId: null, tunnelDeviceId: '', tunnelDeviceInstanceId: '' }));
    return true;
  }

  async status(settings, options = {}) {
    const state = readJson(this.paths.stateFile(), {});
    if (!isAlive(state.tunnelPid)) return false;
    if (this.device && classifyStoredDeviceOwner(state.tunnelDeviceId, this.device.deviceId) !== 'owned') return false;
    if (state.tunnelFingerprint !== tunnelFingerprint(settings, this.device?.deviceId || '', options.activationEpochId || '')) return false;
    const expectedEpoch = String(options.activationEpochId || '').trim();
    if (expectedEpoch && String(state.tunnelActivationEpochId || '').trim() !== expectedEpoch) return false;
    // A persisted fingerprint/epoch is not proof that the current listener is
    // our tunnel: another process may have claimed the same health port.  Bind
    // the health endpoint to the exact PID recorded at launch.
    const listenerPid = await (this.listenerPidProbe || loopbackListenerPid)(settings.healthPort);
    if (listenerPid !== Number(state.tunnelPid)) return false;
    if (!(await canConnect('127.0.0.1', settings.healthPort, 400))) return false;
    return this.probeControlPlaneHealth(settings, Number(state.tunnelPid));
  }
}

module.exports = { TunnelService, tunnelFingerprint, parseLoopbackListenerPid, loopbackListenerPid };
