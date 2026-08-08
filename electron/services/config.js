const path = require('node:path');

const DEFAULTS = Object.freeze({
  configVersion: 5,
  workspace: '',
  permissionMode: 'safe',
  toolMode: 'smart',
  mcpPort: 18765,
  healthPort: 18081,
  proxyMode: 'auto',
  proxyUrl: '',
  tunnelId: '',
  tunnelProfile: 'coding-tools',
  startWithWindows: false,
  autoStartServices: false,
  keepRunningOnClose: true,
  progressReportSeconds: 90,
  theme: 'light',
  firstRunCompleted: false,
  guideProgress: {},
  recentWorkspaces: [],
  authorizedRoots: []
});

function normalizeWorkspacePath(value) {
  const text = String(value || '').trim();
  if (!text) return '';
  const normalized = path.normalize(text).replace(/[\\/]+$/, '');
  return normalized || path.parse(text).root || text;
}

function workspaceKey(value) {
  const normalized = normalizeWorkspacePath(value);
  return process.platform === 'win32' ? normalized.toLowerCase() : normalized;
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
  merged.configVersion = 5;
  merged.permissionMode = ['safe', 'trusted'].includes(merged.permissionMode) ? merged.permissionMode : 'safe';
  merged.toolMode = 'smart';
  merged.proxyMode = ['auto', 'system', 'manual', 'direct'].includes(merged.proxyMode) ? merged.proxyMode : 'auto';
  merged.mcpPort = Number.isInteger(Number(merged.mcpPort)) ? Number(merged.mcpPort) : 18765;
  merged.healthPort = Number.isInteger(Number(merged.healthPort)) ? Number(merged.healthPort) : 18081;
  merged.proxyUrl = String(merged.proxyUrl || '').trim();
  merged.workspace = normalizeWorkspacePath(merged.workspace);
  merged.tunnelId = String(merged.tunnelId || '').trim();
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
  return merged;
}

function validateRuntimeSettings(settings) {
  for (const [label, port] of [['Cổng MCP', settings.mcpPort], ['Cổng bảng điều khiển Tunnel', settings.healthPort]]) {
    if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error(`${label} phải nằm trong khoảng 1024-65535.`);
  }
  if (settings.mcpPort === settings.healthPort) throw new Error('Cổng MCP và cổng bảng điều khiển Tunnel không được giống nhau.');
  if (settings.tunnelId && !/^tunnel_[A-Za-z0-9_-]{4,}$/.test(settings.tunnelId)) {
    throw new Error('Định dạng Tunnel ID không hợp lệ, phải bắt đầu bằng tunnel_.');
  }
  if (settings.proxyMode === 'manual' && !settings.proxyUrl) {
    throw new Error('Chế độ proxy thủ công cần điền địa chỉ proxy.');
  }
  if (settings.proxyUrl) {
    let parsed;
    try { parsed = new URL(settings.proxyUrl); } catch { throw new Error('Địa chỉ proxy không phải là URL hợp lệ.'); }
    if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('Địa chỉ proxy chỉ hỗ trợ http:// hoặc https://.');
    if (parsed.username || parsed.password) throw new Error('Vui lòng không lưu tên người dùng hoặc mật khẩu trong địa chỉ proxy.');
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
