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

function tunnelFingerprint(settings, deviceId = '') {
  return crypto.createHash('sha256').update(JSON.stringify({ device_id: String(deviceId || ''), tunnel_id: String(settings.tunnelId || ''), mcp_port: Number(settings.mcpPort), health_port: Number(settings.healthPort) })).digest('hex');
}

class TunnelService {
  constructor(log, paths = defaultPaths, device = null) {
    this.log = log;
    this.paths = paths;
    this.device = device;
  }

  assertOwnedLive(state) {
    if (!this.device || !isAlive(state.tunnelPid)) return;
    const ownership = classifyStoredDeviceOwner(state.tunnelDeviceId, this.device.deviceId);
    if (ownership === 'owned') return;
    const code = ownership === 'foreign' ? 'TUNNEL_PROCESS_FOREIGN_DEVICE' : 'TUNNEL_PROCESS_OWNER_UNVERIFIED';
    throw Object.assign(new Error(ownership === 'foreign' ? 'Coding Tunnel process state belongs to another device; refusing to adopt or terminate it.' : 'Coding Tunnel process state predates device ownership metadata; refusing to adopt or terminate the live process.'), { code, ownerDeviceId: String(state.tunnelDeviceId || '') || null, expectedDeviceId: this.device.deviceId });
  }

  async start(settings, runtimeApiKey, token, progress) {
    if (!fs.existsSync(this.paths.tunnelExecutable())) throw new Error('Gói cài đặt thiếu tệp tunnel-client.exe.');
    if (!runtimeApiKey) throw new Error('Vui lòng lưu OpenAI Runtime API Key trước.');
    if (!settings.tunnelId) throw new Error('Vui lòng điền OpenAI Tunnel ID trước.');
    await this.stop();
    progress('tunnel-start', 72, 'Đang kết nối OpenAI MCP Tunnel');
    ensureParent(this.paths.tunnelLogFile());
    rotateLog(this.paths.tunnelLogFile());
    const output = fs.openSync(this.paths.tunnelLogFile(), 'a');
    const env = {
      ...process.env,
      CONTROL_PLANE_API_KEY: runtimeApiKey,
      MCP_RUNTIME_HEADER_VALUE: `Bearer ${token}`
    };
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
      tunnelFingerprint: tunnelFingerprint(settings, this.device?.deviceId || ''),
      tunnelDeviceId: this.device?.deviceId || '',
      tunnelDeviceInstanceId: this.device?.deviceInstanceId || '',
      tunnelStartedAt: new Date().toISOString()
    }));
    for (let index = 0; index < 30; index += 1) {
      if (await canConnect('127.0.0.1', settings.healthPort, 500)) {
        this.log.info('OpenAI Tunnel đã khởi động', { pid: child.pid, tunnelId: settings.tunnelId });
        return;
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
      updateJsonAtomic(this.paths.stateFile(), (value) => ({ ...value, tunnelPid: null, tunnelId: '', tunnelFingerprint: '', tunnelDeviceId: '', tunnelDeviceInstanceId: '' }));
      return false;
    }
    await run('taskkill.exe', ['/PID', String(state.tunnelPid), '/T', '/F'], { allowFailure: true });
    updateJsonAtomic(this.paths.stateFile(), (value) => ({ ...value, tunnelPid: null, tunnelId: '', tunnelFingerprint: '', tunnelDeviceId: '', tunnelDeviceInstanceId: '' }));
    return true;
  }

  async status(settings) {
    const state = readJson(this.paths.stateFile(), {});
    if (!isAlive(state.tunnelPid)) return false;
    if (this.device && classifyStoredDeviceOwner(state.tunnelDeviceId, this.device.deviceId) !== 'owned') return false;
    if (state.tunnelFingerprint !== tunnelFingerprint(settings, this.device?.deviceId || '')) return false;
    return await canConnect('127.0.0.1', settings.healthPort, 400);
  }
}

module.exports = { TunnelService, tunnelFingerprint };
