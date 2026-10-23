const path = require('node:path');

const DEFAULTS = Object.freeze({
  configVersion: 7,
  // This is intentionally separate from runtimeIdentity().mode
  // (development/packaged). Existing installations stay on the direct path
  // until a supported full-clean handoff explicitly selects central_executor.
  executionRole: 'direct_legacy',
  workspace: '',
  permissionMode: 'safe',
  // The operator chooses direct host execution or an isolated runner.
  executionMode: 'local',
  toolMode: 'smart',
  mcpPort: 18766,
  healthPort: 18082,
  proxyMode: 'auto',
  proxyUrl: '',
  tunnelId: '',
  tunnelProfile: 'coding-tools',
  // Recovery ports and tunnel identity must remain independent from the primary data plane.
  recoveryMcpPort: 18767,
  recoveryHealthPort: 18083,
  recoveryTunnelId: '',
  recoveryTunnelProfile: 'recovery',
  // Stored only to restore the operator's last Ubuntu origin in the form;
  // enrollment credentials and authority remain owned by node-agent.
  controlPlaneServerUrl: '',
  // CoS companion (W1 read-only pilot): OFF by default. When on, the Electron
  // main process reads the Chat On Steroids Local Control API through
  // electron/services/cosCompanionAdapter.js. cosCompanionUserDataDir may
  // override where the CoS userData folder (control-api/endpoint.json) lives;
  // empty means the standard CoS location / COS_USERDATA_DIR env.
  cosCompanionEnabled: false,
  cosCompanionUserDataDir: '',
  startWithWindows: false,
  autoStartServices: false,
  keepRunningOnClose: true,
  progressReportSeconds: 90,
  theme: 'light',
  firstRunCompleted: false,
  guideProgress: {},
  recentWorkspaces: [],
  authorizedRoots: [],
  costPreset: 'gpt-4o-mini',
  costRateInUsd: 0.15,
  costRateOutUsd: 0.6,
  costCurrency: 'USD',
  costFxRate: 0,
  costBytesPerToken: 4,
  costLaneRates: '{"deepseek":{"in":0.28,"out":0.42},"fast":{"in":0.15,"out":0.6},"terra":{"in":2.5,"out":10},"sol":{"in":10,"out":40}}'
});

function isWindowsAbsolutePath(value) {
  const text = String(value || '').trim();
  return /^[A-Za-z]:[\\/]/.test(text) || /^\\\\[^\\/]+[\\/][^\\/]+(?:[\\/]|$)/.test(text);
}

function normalizeWorkspacePath(value) {
  const text = String(value || '').trim();
  if (!text) return '';
  // Health and activation payloads may carry the executor's Windows path
  // while this check is running in a non-Windows test or control process.
  // Use the path grammar declared by the value, rather than the host OS, so
  // an identity mismatch cannot become a false health success.
  const pathApi = isWindowsAbsolutePath(text) ? path.win32 : path;
  const normalized = pathApi.normalize(text);
  // A drive-relative value such as `E:.` or `C:` depends on the process' per-
  // drive current directory and can therefore bind a different workspace
  // after reboot. Workspace authority must always be a fully-qualified path.
  if (!pathApi.isAbsolute(normalized)) return '';
  const root = pathApi.parse(normalized).root;
  if (normalized === root) return root;
  return normalized.replace(/[\\/]+$/, '') || root;
}

function workspaceKey(value) {
  const normalized = normalizeWorkspacePath(value);
  return process.platform === 'win32' || isWindowsAbsolutePath(normalized)
    ? normalized.toLowerCase()
    : normalized;
}

function mergeRecentWorkspaces(existing, workspace, limit = 50) {
  const candidates = [
    normalizeWorkspacePath(workspace),
    ...(Array.isArray(existing) ? existing : []).map(normalizeWorkspacePath)
  ].filter(Boolean);
  const seen = new Set();
  const result = [];
  for (const item of candidates) {
    const key = workspaceKey(item);
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(item);
    if (result.length >= limit) break;
  }
  return result;
}

function normalize(input = {}) {
  const sourceVersion = Number(input.configVersion) || 0;
  const merged = { ...DEFAULTS };
  for (const key of Object.keys(DEFAULTS)) {
    if (Object.hasOwn(input, key)) merged[key] = input[key];
  }
  merged.configVersion = 7;
  merged.executionRole = ['direct_legacy', 'central_executor'].includes(merged.executionRole)
    ? merged.executionRole
    : 'direct_legacy';
  merged.permissionMode = ['safe', 'trusted'].includes(merged.permissionMode) ? merged.permissionMode : 'safe';
  merged.executionMode = ['local', 'sandboxed'].includes(merged.executionMode) ? merged.executionMode : 'local';
  merged.toolMode = 'smart';
  merged.proxyMode = ['auto', 'system', 'manual', 'direct'].includes(merged.proxyMode) ? merged.proxyMode : 'auto';
  merged.mcpPort = Number.isInteger(Number(merged.mcpPort)) ? Number(merged.mcpPort) : 18766;
  merged.healthPort = Number.isInteger(Number(merged.healthPort)) ? Number(merged.healthPort) : 18082;
  merged.recoveryMcpPort = Number.isInteger(Number(merged.recoveryMcpPort)) ? Number(merged.recoveryMcpPort) : 18767;
  merged.recoveryHealthPort = Number.isInteger(Number(merged.recoveryHealthPort)) ? Number(merged.recoveryHealthPort) : 18083;
  if (sourceVersion < 6 && Number(input.mcpPort) === 18765 && Number(input.healthPort) === 18081) {
    merged.mcpPort = 18766;
    merged.healthPort = 18082;
  }
  merged.proxyUrl = String(merged.proxyUrl || '').trim();
  merged.workspace = normalizeWorkspacePath(merged.workspace);
  merged.tunnelId = String(merged.tunnelId || '').trim();
  merged.recoveryTunnelId = String(merged.recoveryTunnelId || '').trim();
  merged.recoveryTunnelProfile = 'recovery';
  merged.controlPlaneServerUrl = String(merged.controlPlaneServerUrl || '').trim();
  merged.cosCompanionEnabled = Boolean(merged.cosCompanionEnabled);
  merged.cosCompanionUserDataDir = String(merged.cosCompanionUserDataDir || '').trim();
  if (sourceVersion < 5 && merged.theme === 'dark') merged.theme = 'light';
  merged.theme = merged.theme === 'dark' ? 'dark' : 'light';
  merged.progressReportSeconds = [60, 90, 120, 180].includes(Number(merged.progressReportSeconds))
    ? Number(merged.progressReportSeconds)
    : 90;
  merged.firstRunCompleted = Boolean(merged.firstRunCompleted);
  merged.guideProgress = merged.guideProgress && typeof merged.guideProgress === 'object' ? merged.guideProgress : {};
  merged.recentWorkspaces = mergeRecentWorkspaces(merged.recentWorkspaces, merged.workspace, 50);
  merged.authorizedRoots = (Array.isArray(merged.authorizedRoots) ? merged.authorizedRoots : [])
    .map(normalizeWorkspacePath)
    .filter(Boolean)
    .filter((item, index, all) => all.findIndex((other) => workspaceKey(other) === workspaceKey(item)) === index)
    .filter((item) => workspaceKey(item) !== workspaceKey(merged.workspace))
    .slice(0, 32);
  merged.costPreset = String(merged.costPreset || 'gpt-4o-mini');
  merged.costRateInUsd = Number.isFinite(Number(merged.costRateInUsd)) && Number(merged.costRateInUsd) >= 0
    ? Number(merged.costRateInUsd) : 0.15;
  merged.costRateOutUsd = Number.isFinite(Number(merged.costRateOutUsd)) && Number(merged.costRateOutUsd) >= 0
    ? Number(merged.costRateOutUsd) : 0.6;
  merged.costCurrency = merged.costCurrency === 'VND' ? 'VND' : 'USD';
  merged.costFxRate = Number.isFinite(Number(merged.costFxRate)) && Number(merged.costFxRate) > 0
    ? Number(merged.costFxRate) : 0;
  merged.costBytesPerToken = Number.isFinite(Number(merged.costBytesPerToken)) && Number(merged.costBytesPerToken) >= 1
    ? Number(merged.costBytesPerToken) : 4;
  merged.costLaneRates = normalizeLaneRates(merged.costLaneRates);
  return merged;
}

function normalizeLaneRates(value) {
  const fallback = { deepseek: { in: 0.28, out: 0.42 }, fast: { in: 0.15, out: 0.6 }, terra: { in: 2.5, out: 10 }, sol: { in: 10, out: 40 } };
  let parsed = {};
  try { parsed = typeof value === 'string' ? JSON.parse(value) : value; } catch { return JSON.stringify(fallback); }
  const result = {};
  for (const lane of ['deepseek', 'fast', 'terra', 'sol']) {
    const entry = parsed && typeof parsed === 'object' ? parsed[lane] : null;
    const inRate = Number(entry?.in);
    const outRate = Number(entry?.out);
    result[lane] = {
      in: Number.isFinite(inRate) && inRate >= 0 ? inRate : fallback[lane].in,
      out: Number.isFinite(outRate) && outRate >= 0 ? outRate : fallback[lane].out
    };
  }
  return JSON.stringify(result);
}

function validateRuntimeSettings(settings) {
  const ports = [['Cổng MCP', settings.mcpPort], ['Cổng bảng điều khiển Tunnel', settings.healthPort], ['Recovery MCP port', settings.recoveryMcpPort], ['Recovery Tunnel health port', settings.recoveryHealthPort]];
  for (const [label, port] of ports) {
    if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error(`${label} phải nằm trong khoảng 1024-65535.`);
  }
  if (new Set(ports.map(([, port]) => port)).size !== ports.length) throw new Error('Primary và Recovery ports không được giống nhau để giữ failure domain độc lập.');
  const centralExecutor = settings?.executionRole === 'central_executor';
  // A central executor does not use any local OpenAI Tunnel setting.  A stale
  // direct-profile value therefore cannot prevent local bootstrap; the
  // full-clean handoff owns retiring it rather than this validator.
  if (!centralExecutor && settings.tunnelId && !/^tunnel_[A-Za-z0-9_-]{4,}$/.test(settings.tunnelId)) {
    throw new Error('Định dạng Tunnel ID không hợp lệ, phải bắt đầu bằng tunnel_.');
  }
  if (!centralExecutor && settings.recoveryTunnelId && !/^tunnel_[A-Za-z0-9_-]{4,}$/.test(settings.recoveryTunnelId)) throw new Error('Recovery Tunnel ID phải bắt đầu bằng tunnel_.');
  if (!centralExecutor && settings.recoveryTunnelId && settings.recoveryTunnelId === settings.tunnelId) throw new Error('Recovery Tunnel ID phải independent và khác Coding Tunnel ID.');
  if (settings.proxyMode === 'manual' && !settings.proxyUrl) {
    throw new Error('Chế độ proxy thủ công cần điền địa chỉ proxy.');
  }
  if (settings.proxyUrl) {
    let parsed;
    try { parsed = new URL(settings.proxyUrl); } catch { throw new Error('Địa chỉ proxy không phải là URL hợp lệ.'); }
    if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('Địa chỉ proxy chỉ hỗ trợ http:// hoặc https://.');
    if (parsed.username || parsed.password) throw new Error('Vui lòng không lưu tên người dùng hoặc mật khẩu trong địa chỉ proxy.');
  }
  if (settings.controlPlaneServerUrl) {
    let parsed;
    try { parsed = new URL(settings.controlPlaneServerUrl); } catch { throw new Error('Địa chỉ Ubuntu Control Plane không phải là URL hợp lệ.'); }
    if (parsed.protocol !== 'https:' || parsed.username || parsed.password || parsed.pathname !== '/' || parsed.search || parsed.hash) {
      throw new Error('Địa chỉ Ubuntu Control Plane phải là HTTPS origin, không có path hoặc credential.');
    }
  }
}

module.exports = {
  DEFAULTS,
  normalize,
  validateRuntimeSettings,
  normalizeWorkspacePath,
  workspaceKey,
  mergeRecentWorkspaces
};
