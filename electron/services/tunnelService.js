const fs = require('node:fs');
const { spawn } = require('node:child_process');
const defaultPaths = require('../paths');
const { readJson, updateJsonAtomic, ensureParent } = require('./jsonStore');
const { rotateLog } = require('./logService');
const { canConnect } = require('./environmentService');
const { run } = require('./commandRunner');
const { isAlive } = require('./nativeService');

class TunnelService {
  constructor(log, paths = defaultPaths) {
    this.log = log;
    this.paths = paths;
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
    if (!isAlive(state.tunnelPid)) return false;
    await run('taskkill.exe', ['/PID', String(state.tunnelPid), '/T', '/F'], { allowFailure: true });
    updateJsonAtomic(this.paths.stateFile(), (value) => ({ ...value, tunnelPid: null }));
    return true;
  }

  async status(settings) {
    const state = readJson(this.paths.stateFile(), {});
    return isAlive(state.tunnelPid) && await canConnect('127.0.0.1', settings.healthPort, 400);
  }
}

module.exports = { TunnelService };
