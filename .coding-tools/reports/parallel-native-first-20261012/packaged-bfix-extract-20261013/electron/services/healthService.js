const net = require('node:net');

function freePort(start, avoid) {
  return new Promise((resolve, reject) => {
    const tryPort = (port) => {
      if (port > 65535) return reject(new Error('Không tìm thấy cổng cục bộ khả dụng.'));
      if (port === avoid) return tryPort(port + 1);
      const server = net.createServer();
      server.once('error', () => tryPort(port + 1));
      server.listen(port, '127.0.0.1', () => server.close(() => resolve(port)));
    };
    tryPort(Math.max(1024, Number(start) || 18766));
  });
}

class HealthService {
  constructor({ settings, secrets, environment, orchestrator }) {
    Object.assign(this, { settings, secrets, environment, orchestrator });
  }

  async ownership(current) {
    const runtimeOwned = await this.orchestrator.native.status(current).catch(() => false);
    // A central executor deliberately has no Windows OpenAI Tunnel.  Calling
    // the Tunnel ownership probe here made a healthy central node look broken
    // (and could make diagnostics depend on a stale direct profile).
    if (current?.executionRole === 'central_executor') {
      return { runtimeOwned, tunnelOwned: false };
    }
    const tunnelOwned = await this.orchestrator.tunnel.status(current, {
      activationEpochId: this.orchestrator.activationEpochId || ''
    }).catch(() => false);
    return { runtimeOwned, tunnelOwned };
  }

  async centralStatus(current) {
    if (current?.executionRole !== 'central_executor') return null;
    if (typeof this.orchestrator.snapshot === 'function') {
      try {
        const snapshot = await this.orchestrator.snapshot({ force: true, reason: 'health_inspect' });
        return snapshot?.status || snapshot || null;
      } catch {
        // A failed observation is intentionally represented as unknown below;
        // health must never turn a missing route receipt into a green result.
      }
    }
    return null;
  }

  async inspect() {
    const current = this.settings.load();
    const central = current?.executionRole === 'central_executor';
    const env = await this.environment.inspect(current);
    const owned = await this.ownership(current);
    const secretState = this.secrets.status();
    const mcpConflict = env.ports.mcpListening && !owned.runtimeOwned;
    const tunnelConflict = env.ports.tunnelListening && !owned.tunnelOwned;
    const checks = [
      { id: 'workspace', label: 'Thư mục làm việc', ok: env.workspace.exists, repair: 'choose-workspace', detail: current.workspace || 'Chưa chọn' },
      { id: 'runtime', label: 'Python Portable', ok: env.python.installed, repair: 'runtime', detail: env.python.version || 'Python Portable không khả dụng' },
      { id: 'mcp-port', label: 'Cổng cục bộ MCP', ok: !mcpConflict, repair: 'port', detail: mcpConflict ? `${current.mcpPort} bị tiến trình khác chiếm dụng` : `${current.mcpPort} khả dụng hoặc do trợ lý quản lý` },
      { id: 'mcp', label: 'Coding Tools MCP', ok: owned.runtimeOwned, repair: 'restart', detail: owned.runtimeOwned ? 'Trợ lý đang chạy bình thường' : 'Chưa khởi động' }
    ];
    if (central) {
      const centralStatus = await this.centralStatus(current);
      const routeReady = centralStatus?.centralConnected === true
        && centralStatus?.authorityReady === true
        && !centralStatus?.centralStatusReason;
      checks.push({
        id: 'control-plane-route',
        label: 'Kết nối Ubuntu và quyền cục bộ',
        ok: routeReady,
        repair: 'pairing',
        detail: centralStatus
          ? routeReady
            ? 'Ubuntu đã xác minh route và local authority.'
            : `Chưa sẵn sàng${centralStatus.centralStatusReason ? ` (${centralStatus.centralStatusReason})` : ' (chưa có route receipt)'}.`
          : 'Chưa đọc được route receipt từ Ubuntu.'
      });
      return {
        healthy: checks.every((item) => item.ok),
        checks,
        settings: current,
        environment: env,
        ownership: owned,
        executionRole: 'central_executor',
        centralStatus,
        inspectedAt: new Date().toISOString()
      };
    }
    checks.splice(2, 0,
      { id: 'tunnel-client', label: 'Tunnel Client', ok: env.tunnelClient.installed, repair: '', detail: env.tunnelClient.installed ? 'Tệp đầy đủ' : 'Thiếu tệp cài đặt, cần cài đặt lại trợ lý' },
      { id: 'runtime-key', label: 'Runtime API Key', ok: secretState.runtimeApiKey, repair: 'runtime-key', detail: secretState.runtimeApiKey ? 'Đã lưu an toàn' : 'Chưa điền' },
      { id: 'tunnel-id', label: 'Tunnel ID', ok: Boolean(current.tunnelId), repair: 'tunnel-id', detail: current.tunnelId || 'Chưa điền' },
      { id: 'tunnel-port', label: 'Cổng bảng điều khiển Tunnel', ok: !tunnelConflict, repair: 'port', detail: tunnelConflict ? `${current.healthPort} bị tiến trình khác chiếm dụng` : `${current.healthPort} khả dụng hoặc do trợ lý quản lý` }
    );
    checks.push({ id: 'tunnel', label: 'OpenAI Tunnel', ok: owned.tunnelOwned, repair: 'restart', detail: owned.tunnelOwned ? 'Trợ lý đang chạy bình thường' : 'Chưa khởi động' });
    return { healthy: checks.every((item) => item.ok), checks, settings: current, environment: env, ownership: owned, executionRole: 'direct_legacy', inspectedAt: new Date().toISOString() };
  }

  async repair() {
    let current = this.settings.load();
    const central = current?.executionRole === 'central_executor';
    const before = await this.inspect();
    const actions = [];
    const unresolved = [];
    const patch = {};
    if (!before.checks.find((item) => item.id === 'mcp-port')?.ok) {
      patch.mcpPort = await freePort(current.mcpPort + 1, current.healthPort);
      actions.push(`Cổng MCP đã chuyển thành ${patch.mcpPort}`);
    }
    if (!central && !before.checks.find((item) => item.id === 'tunnel-port')?.ok) {
      patch.healthPort = await freePort(current.healthPort + 1, patch.mcpPort || current.mcpPort);
      actions.push(`Cổng bảng điều khiển Tunnel đã chuyển thành ${patch.healthPort}`);
    }
    if (!this.secrets.status().mcpAuthToken) {
      await this.orchestrator.ensureToken();
      actions.push('Đã tạo Token xác thực cục bộ MCP');
    }
    if (Object.keys(patch).length) current = this.settings.save(patch);
    if (!current.workspace) unresolved.push('Chọn thư mục làm việc');
    if (central) {
      if (!before.checks.find((item) => item.id === 'control-plane-route')?.ok) unresolved.push('Hoàn tất pairing và quyền trên Ubuntu');
      if (!before.checks.find((item) => item.id === 'mcp')?.ok) unresolved.push('Chuẩn bị MCP executor cục bộ');
    } else {
      if (!this.secrets.status().runtimeApiKey) unresolved.push('Điền Runtime API Key');
      if (!current.tunnelId) unresolved.push('Điền Tunnel ID');
      if (!before.environment.tunnelClient.installed) unresolved.push('Cài đặt lại trợ lý để khôi phục Tunnel Client');
    }
    if (!before.environment.python.installed) unresolved.push('Sửa chữa Python Portable');
    if (!central && !unresolved.length) {
      await this.orchestrator.restart({
        automatic: true,
        mode: 'soft_recovery',
        reason: 'health_repair'
      });
      actions.push('Đã khởi động lại MCP và Tunnel');
    }
    const after = await this.inspect();
    return { ...after, actions, unresolved };
  }
}

module.exports = { HealthService, freePort };
