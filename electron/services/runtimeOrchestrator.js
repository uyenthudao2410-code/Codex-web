const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { NativeService } = require('./nativeService');
const { TunnelService } = require('./tunnelService');
const { validateRuntimeSettings, mergeRecentWorkspaces, workspaceKey } = require('./config');
const { canConnect } = require('./environmentService');
const { resolveProxy } = require('./proxyService');
const { stateFile } = require('../paths');
const { readJson, updateJsonAtomic } = require('./jsonStore');

function wait(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

const MAX_DEFERRED_RECOVERIES = 6;

function probeMcp(port, token, expectedWorkspace = '') {
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
        if (response.statusCode !== 200) { resolve(false); return; }
        try {
          const payload = JSON.parse(body);
          const workspaceMatches = !expectedWorkspace
            || workspaceKey(payload.workspace) === workspaceKey(expectedWorkspace);
          resolve(payload.ready === true && workspaceMatches);
        } catch {
          resolve(false);
        }
      });
    });
    request.on('timeout', () => { request.destroy(); resolve(false); });
    request.on('error', () => resolve(false));
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

class RuntimeOrchestrator {
  constructor({ settings, secrets, environment, log, emitProgress, emitStatus = () => {} }) {
    this.settingsStore = settings;
    this.secrets = secrets;
    this.environment = environment;
    this.log = log;
    this.emitProgress = emitProgress;
    this.emitStatus = emitStatus;
    this.native = new NativeService(log);
    this.tunnel = new TunnelService(log);
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

  async ensureToken() {
    let token = this.secrets.get('mcpAuthToken');
    if (!token) {
      token = crypto.randomBytes(32).toString('base64url');
      this.secrets.set('mcpAuthToken', token);
    }
    return token;
  }

  isManuallyStopped() {
    return readJson(stateFile(), {}).manualStop === true;
  }

  setManualStop(value) {
    updateJsonAtomic(stateFile(), (state) => ({
      ...state,
      manualStop: Boolean(value),
      intentChangedAt: new Date().toISOString()
    }));
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

      await this.native.start(settings, token, this.progress.bind(this));

      this.progress('mcp-health', 64, 'Đang xác minh Coding Tools MCP');
      let ready = false;
      for (let index = 0; index < 35; index += 1) {
        if (await probeMcp(settings.mcpPort, token, settings.workspace)) { ready = true; break; }
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
      this.recoveryAttempts = 0;
      this.nextRecoveryAt = 0;
      this.progress('complete', 100, 'Triển khai hoàn tất, cả MCP và OpenAI Tunnel đều đang chạy');
      this.invalidateSnapshot();
      return await this.snapshot({ force: true, reason: 'started' });
    } catch (error) {
      this.autoRecoveryBlocked = true;
      this.lastStartFailure = error.message;
      this.heartbeatFailures = 0;
      this.heartbeatFailureKind = '';
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
      const ready = await probeMcp(next.mcpPort, token, workspace);
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
    const [mcpRunning, nativeAlive, tunnelRunning] = await Promise.all([
      token ? probeMcp(settings.mcpPort, token, settings.workspace) : Promise.resolve(false),
      this.native.status().catch(() => false),
      this.tunnel.status(settings).catch(() => false)
    ]);
    return {
      workspace: settings.workspace,
      mcpRunning,
      nativeAlive,
      tunnelRunning,
      fullyReady: mcpRunning && tunnelRunning,
      recovering: this.recovering,
      failures: this.heartbeatFailures,
      recoveryBlocked: this.autoRecoveryBlocked,
      lastStartFailure: this.lastStartFailure
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

  async supervise() {
    const status = await this.lightweightSnapshot();
    if (status.fullyReady) {
      this.heartbeatFailures = 0;
      this.heartbeatFailureKind = '';
      this.recoveryAttempts = 0;
      this.nextRecoveryAt = 0;
      this.deferredRecoveryCount = 0;
      return status;
    }
    const runtimeState = readJson(stateFile(), {});
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
      this.heartbeatFailureKind = failureKind;
      this.heartbeatFailures = 0;
      this.recoveryAttempts = 0;
      this.nextRecoveryAt = 0;
      this.deferredRecoveryCount = 0;
    }
    this.heartbeatFailures += 1;
    if (this.heartbeatFailures < 3 || Date.now() < this.nextRecoveryAt) {
      return { ...status, failures: this.heartbeatFailures };
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
            recovering: false,
            recoveryDeferred: true,
            deferredRecoveryCount: this.deferredRecoveryCount,
            recoveryReason: 'mcp_process_alive_health_unavailable'
          };
        }
      } else {
        await this.restart({ automatic: true });
      }
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
    const runtimeRunning = token
      ? await probeMcp(settings.mcpPort, token, settings.workspace)
      : false;
    const tunnelRunning = await this.tunnel.status(settings).catch(() => false);
    return this.publishSnapshot({
      settings,
      secrets: this.secrets.status(),
      environment,
      status: {
        busy: this.busy,
        runtimeRunning,
        tunnelRunning,
        fullyReady: runtimeRunning && tunnelRunning,
        localMcpUrl: `http://127.0.0.1:${settings.mcpPort}/mcp`,
        tunnelUiUrl: `http://127.0.0.1:${settings.healthPort}/ui`,
        manuallyStopped: this.isManuallyStopped()
      }
    }, reason);
  }
}

module.exports = { RuntimeOrchestrator, probeMcp, setMcpAuthorizedRoots };
