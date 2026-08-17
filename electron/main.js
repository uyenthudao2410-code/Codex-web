const path = require('node:path');
const fs = require('node:fs/promises');
const crypto = require('node:crypto');
const http = require('node:http');
const { app, BrowserWindow, dialog, ipcMain, shell, Tray, Menu, nativeImage, session, WebContentsView, clipboard } = require('electron');
const { SettingsStore } = require('./services/settingsStore');
const { SecretStore } = require('./services/secretStore');
const { LogService } = require('./services/logService');
const { EnvironmentService, pythonStatus } = require('./services/environmentService');
const { ChatViewController } = require('./chatViewController');
const { ChatEvaluationJournal } = require('./services/chatEvaluationJournal');
const { run } = require('./services/commandRunner');
const { resolveProxy, clearProxyCache } = require('./services/proxyService');
const { BuildVerificationService } = require('./services/buildVerificationService');
const { buildCodexDesktopMcpConfig } = require('./services/codexDesktopConfig');
const { readJson, writeJsonAtomic } = require('./services/jsonStore');
const { panelInset, panelBounds } = require('./services/panelLayout');
const runtimePathApi = require('./paths');
const { resourcesRoot, hubProxyDescriptorFile } = runtimePathApi;
const { createElectronRuntimePaths } = require('./services/runtimePaths');
const { RecoveryIpcClient } = require('./services/recoveryIpc');
const {
  ensureRecoveryHost,
  recoveryLoginItemArguments,
  electronUiArguments,
  assertActivationDeadline
} = require('./services/recoveryHostLauncher');
const { ComponentRevisionTracker } = require('./services/componentRevision');
const { startRecoveryHostApplication } = require('./recoveryHost');

let chatWindow;
let managerWindow;
let chatController;
let orchestrator;
let forceQuit = false;
let tray = null;
let buildVerification;
let panelView = null;
let panelVisible = false;
let lastRecoveryProgressTime = '';
const TOOLBAR_HEIGHT = 112;
const PANEL_ORCHESTRATION_TIMEOUT_MS = 10000;
const recoveryHostMode = process.argv.includes('--recovery-host') || process.env.WEBCODEX_PROCESS_ROLE === 'recovery-host';
const runtimePaths = createElectronRuntimePaths(app);
runtimePathApi.configureRuntimePaths(runtimePaths);
const settings = new SettingsStore(runtimePaths);
const secrets = new SecretStore(runtimePaths);
const log = new LogService(runtimePaths);
const environment = new EnvironmentService(runtimePaths);
const chatEvaluationJournal = new ChatEvaluationJournal();
const uiRevisionTracker = new ComponentRevisionTracker({ paths: runtimePaths });
const uiInstanceId = crypto.randomBytes(16).toString('hex');
const uiStartedAtUnixMs = Date.now();
const uiRunningRevision = recoveryHostMode ? null : uiRevisionTracker.captureRunning('electron_ui');
let uiRestartScheduled = false;

function codeActivationRequest(component, allowAcceptancePending = false) {
  const allowed = new Set(['coding_mcp', 'electron_ui', 'recovery_host']);
  if (!allowed.has(component)) throw Object.assign(new Error('Component kích hoạt không hợp lệ.'), { code: 'INVALID_COMPONENT' });
  const now = Date.now();
  return {
    operation_id: crypto.randomBytes(18).toString('base64url'),
    component,
    requested_at_unix_ms: now,
    expires_at_unix_ms: now + 60_000,
    expected_disk_revision: uiRevisionTracker.disk(component, { force: true }).revision,
    allow_acceptance_pending: allowAcceptancePending === true
  };
}

async function registerUiRevision() {
  if (recoveryHostMode || uiRestartScheduled || !orchestrator || !uiRunningRevision) return null;
  const result = await orchestrator.registerUiRevision({
    instance_id: uiInstanceId,
    pid: process.pid,
    revision: uiRunningRevision,
    started_at_unix_ms: uiStartedAtUnixMs
  });
  if (result?.restart_required) {
    try {
      assertActivationDeadline({ expiresAtUnixMs: result.expires_at_unix_ms }, 'before_ui_relaunch');
    } catch (error) {
      if (error?.code !== 'ACTIVATION_REQUEST_EXPIRED') throw error;
      await orchestrator.activationStatus(result.operation_id).catch(() => null);
      return { ...result, restart_required: false, expired: true };
    }
    uiRestartScheduled = true;
    forceQuit = true;
    app.relaunch({ execPath: process.execPath, args: electronUiArguments(app) });
    app.exit(0);
  }
  return result;
}

function appIconPath() {
  return path.join(__dirname, 'app-icon.png');
}

function sendManager(channel, payload) {
  if (managerWindow && !managerWindow.isDestroyed()) managerWindow.webContents.send(channel, payload);
}

function safeMessage(error) {
  return error instanceof Error ? error.message : String(error);
}

function assertTrustedIpc(event) {
  const url = event.senderFrame?.url || event.sender?.getURL?.() || '';
  if (!url.startsWith('file://')) throw new Error('Đã chặn cuộc gọi IPC từ trang không phải cục bộ.');
}

function secureHandle(channel, handler) {
  ipcMain.handle(channel, (event, ...args) => {
    assertTrustedIpc(event);
    return handler(event, ...args);
  });
}

function workspaceStatePaths() {
  const workspace = String(settings.load().workspace || '').trim();
  if (!workspace) throw new Error('Vui lòng chọn thư mục làm việc trước.');
  const root = path.resolve(workspace);
  return {
    root,
    statePath: path.join(root, '.coding-tools', 'task-state.json'),
    historyPath: path.join(root, '.coding-tools', 'task-history.json'),
    performancePath: path.join(root, '.coding-tools', 'performance.json')
  };
}

function archiveTask(state, historyPath, reason) {
  if (!state || typeof state !== 'object' || (!state.task_id && !state.objective)) return;
  const history = readJson(historyPath, []);
  const items = Array.isArray(history) ? history : [];
  items.push({ ...state, archived_at: new Date().toISOString(), archive_reason: reason });
  writeJsonAtomic(historyPath, items.slice(-100));
}

async function invokeSafely(action) {
  try { return { ok: true, data: await action() }; }
  catch (error) { return { ok: false, error: safeMessage(error) }; }
}

function showChatWindow() {
  const target = createChatWindow();
  if (target.isMinimized()) target.restore();
  target.show();
  target.focus();
  return target;
}

function httpRequestJson({ port, path: requestPath, method, token, body, headers = {}, timeout }) {
  return new Promise((resolve, reject) => {
    const payload = body === undefined ? null : JSON.stringify(body);
    const request = http.request({
      host: '127.0.0.1',
      port,
      path: requestPath,
      method,
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(payload ? { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) } : {}),
        ...headers
      },
      timeout
    }, (response) => {
      let data = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { if (data.length < 4 * 1024 * 1024) data += chunk; });
      response.on('end', () => {
        if (response.statusCode >= 400) {
          reject(new Error(`MCP trả về HTTP ${response.statusCode}: ${String(data).slice(0, 200)}`));
          return;
        }
        try { resolve(data ? JSON.parse(data) : null); } catch { resolve(data); }
      });
    });
    request.on('timeout', () => { request.destroy(new Error('Quá thời gian kết nối MCP.')); });
    request.on('error', reject);
    if (payload) request.write(payload);
    request.end();
  });
}

async function panelTaskControl(action) {
  const allowed = new Set(['pause', 'resume', 'stop']);
  if (!allowed.has(action)) throw new Error('Thao tác nhiệm vụ từ bảng điều khiển không hợp lệ.');
  const current = settings.load();
  const token = secrets.get('mcpAuthToken');
  if (!token) throw new Error('MCP chưa sẵn sàng để điều khiển nhiệm vụ.');
  const request = {
    jsonrpc: '2.0',
    id: `panel-task-${action}-${Date.now()}`,
    method: 'tools/call',
    params: {
      name: 'task_control',
      arguments: { action },
      _meta: {
        'io.modelcontextprotocol/protocolVersion': '2026-07-28',
        'io.modelcontextprotocol/clientCapabilities': {},
        'io.modelcontextprotocol/clientInfo': { name: 'web-mcp-assistant-panel', version: app.getVersion() }
      }
    }
  };
  const response = await httpRequestJson({
    port: current.mcpPort,
    path: '/mcp',
    method: 'POST',
    token,
    body: request,
    headers: {
      'MCP-Protocol-Version': '2026-07-28',
      'Mcp-Method': 'tools/call',
      'Mcp-Name': 'task_control',
      'X-Coding-Tools-Client-Id': 'electron-panel',
      'X-Coding-Tools-Client-Type': 'electron'
    },
    timeout: 10000
  });
  if (response && response.error) throw new Error(response.error.message || 'MCP từ chối thao tác nhiệm vụ.');
  if (response?.result?.isError) {
    const message = response.result?.structuredContent?.error?.message || response.result?.content?.[0]?.text || 'MCP từ chối thao tác nhiệm vụ.';
    throw new Error(String(message).slice(0, 400));
  }
  return (response && response.result) || null;
}

async function recordHostObservationSpan(event) {
  if (!event || event.event_type !== 'host_turn_span' || !event.run_id || !event.wave_id || !event.trace_id || !event.turn_id) return false;
  const current = settings.load();
  const token = secrets.get('mcpAuthToken');
  if (!token) return false;
  const request = {
    jsonrpc: '2.0',
    id: `host-observation-${Date.now()}`,
    method: 'tools/call',
    params: {
      name: 'task_control',
      arguments: {
        action: 'observation',
        run_id: event.run_id,
        wave_id: event.wave_id,
        observation_span: {
          span_id: event.span_id,
          stage: 'host_turn_span',
          source: 'electron_chatgpt_dom',
          measurement: event.measurement,
          clock_domain: event.clock_domain,
          start_ms: event.start_ms,
          end_ms: event.end_ms,
          observer_plane: 'electron_chatgpt_dom',
          trace_id: event.trace_id,
          turn_id: event.turn_id
        }
      },
      _meta: {
        'io.modelcontextprotocol/protocolVersion': '2026-07-28',
        'io.modelcontextprotocol/clientCapabilities': {},
        'io.modelcontextprotocol/clientInfo': { name: 'web-mcp-assistant-host-observer', version: app.getVersion() }
      }
    }
  };
  const response = await httpRequestJson({
    port: current.mcpPort,
    path: '/mcp',
    method: 'POST',
    token,
    body: request,
    headers: {
      'MCP-Protocol-Version': '2026-07-28',
      'Mcp-Method': 'tools/call',
      'Mcp-Name': 'task_control',
      'X-Coding-Tools-Client-Id': 'electron-host-observer',
      'X-Coding-Tools-Client-Type': 'electron'
    },
    timeout: 5000
  });
  if (response?.error || response?.result?.isError) throw new Error(response?.error?.message || response?.result?.structuredContent?.error?.message || 'MCP rejected host observation.');
  return true;
}

function layoutViews() {
  if (!chatWindow || chatWindow.isDestroyed()) return;
  const [width, height] = chatWindow.getContentSize();
  if (chatController) chatController.setRightInset(panelInset(width, panelVisible));
  if (panelView && !panelView.webContents.isDestroyed()) {
    const bounds = panelBounds(width, height, TOOLBAR_HEIGHT, panelVisible);
    panelView.setBounds(bounds || { x: width, y: TOOLBAR_HEIGHT, width: 0, height: Math.max(0, height - TOOLBAR_HEIGHT) });
  }
}

function broadcastPanelVisibility() {
  if (chatWindow && !chatWindow.isDestroyed()) chatWindow.webContents.send('panel:visibility', { visible: panelVisible });
}

function createPanelView() {
  if (panelView && !panelView.webContents.isDestroyed()) return panelView;
  panelView = new WebContentsView({
    webPreferences: {
      preload: path.join(__dirname, 'panelPreload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });
  panelView.setBackgroundColor('#ffffff');
  chatWindow.contentView.addChildView(panelView);
  panelView.webContents.loadFile(path.join(__dirname, '..', 'renderer', 'panel.html'));
  return panelView;
}

function destroyPanelView() {
  if (!panelView) return;
  try { chatWindow?.contentView?.removeChildView(panelView); } catch { /* already detached */ }
  if (panelView.webContents && !panelView.webContents.isDestroyed()) panelView.webContents.close();
  panelView = null;
}

function togglePanel() {
  panelVisible = !panelVisible;
  if (panelVisible) createPanelView();
  else destroyPanelView();
  layoutViews();
  broadcastPanelVisibility();
  return panelVisible;
}

function createTray() {
  if (tray && !tray.isDestroyed()) return tray;
  const icon = nativeImage.createFromPath(appIconPath()).resize({ width: 16, height: 16 });
  tray = new Tray(icon);
  tray.setToolTip('Trợ lý Web MCP · Đang chạy ngầm');
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Mở Trợ lý Web MCP', click: () => showChatWindow() },
    { label: 'Mở Cấu hình Quản lý', click: () => { showChatWindow(); openManagerWindow(); } },
    { type: 'separator' },
    { label: 'Thoát Trợ lý (Giữ dịch vụ MCP)', click: () => { forceQuit = true; app.quit(); } }
  ]));
  tray.on('click', () => showChatWindow());
  tray.on('double-click', () => showChatWindow());
  return tray;
}

function createChatWindow() {
  if (chatWindow && !chatWindow.isDestroyed()) {
    chatWindow.show();
    chatWindow.focus();
    return chatWindow;
  }

  chatWindow = new BrowserWindow({
    width: 1360,
    height: 900,
    minWidth: 960,
    minHeight: 640,
    show: false,
    backgroundColor: '#f7f7f8',
    title: 'Trợ lý Web MCP',
    icon: appIconPath(),
    webPreferences: {
      preload: path.join(__dirname, 'browserPreload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });
  chatWindow.removeMenu();
  chatWindow.loadFile(path.join(__dirname, '..', 'renderer', 'browser.html'));

  chatController = new ChatViewController({
    window: chatWindow,
    log,
    settings,
    toolbarHeight: 112,
    onState: (payload) => {
      if (chatWindow && !chatWindow.isDestroyed()) chatWindow.webContents.send('chat:state', payload);
    },
    onDownload: (payload) => {
      if (chatWindow && !chatWindow.isDestroyed()) chatWindow.webContents.send('chat:download', payload);
    },
    onEvaluation: async (events) => {
      const workspace = String(settings.load().workspace || '').trim();
      if (!workspace) return;
      let correlated = [];
      try {
        chatEvaluationJournal.stagePendingTurns(workspace, events);
        correlated = chatEvaluationJournal.attachExplicitBindings(workspace, events);
        chatEvaluationJournal.append(workspace, correlated);
      } catch (error) {
        log.warn('Không thể ghi host-visible evaluation telemetry', { error: safeMessage(error) });
        return;
      }
      for (const event of correlated.filter((item) => item?.event_type === 'host_turn_span')) {
        try {
          if (event.run_id && event.wave_id) await recordHostObservationSpan(event);
        } catch (error) {
          log.warn('Không thể ghi explicit host observation vào EOCL ledger', { error: safeMessage(error) });
        } finally {
          chatEvaluationJournal.finalizeCorrelation(workspace, event);
        }
      }
    }
  });
  chatController.mount();
  chatWindow.on('resize', () => layoutViews());

  chatWindow.once('ready-to-show', () => chatWindow.show());
  chatWindow.on('closed', () => {
    if (chatController) chatController.dispose();
    chatController = null;
    destroyPanelView();
    panelVisible = false;
    chatWindow = null;
    if (managerWindow && !managerWindow.isDestroyed()) managerWindow.destroy();
  });
  chatWindow.on('close', (event) => {
    if (forceQuit) return;
    event.preventDefault();
    if (settings.load().keepRunningOnClose) {
      if (managerWindow && !managerWindow.isDestroyed()) managerWindow.hide();
      chatWindow.hide();
      return;
    }
    if (!orchestrator) {
      forceQuit = true;
      app.quit();
      return;
    }
    orchestrator.stop().catch((error) => log.error(error.message, { stage: 'close' })).finally(() => {
      forceQuit = true;
      app.quit();
    });
  });
  return chatWindow;
}

function openManagerWindow() {
  if (managerWindow && !managerWindow.isDestroyed()) {
    managerWindow.show();
    managerWindow.focus();
    return managerWindow;
  }

  const chatBounds = chatWindow && !chatWindow.isDestroyed() ? chatWindow.getBounds() : null;
  const width = 980;
  const height = 720;
  const x = chatBounds ? Math.round(chatBounds.x + Math.max(0, (chatBounds.width - width) / 2)) : undefined;
  const y = chatBounds ? Math.round(chatBounds.y + Math.max(0, (chatBounds.height - height) / 2)) : undefined;

  managerWindow = new BrowserWindow({
    width,
    height,
    x,
    y,
    minWidth: 820,
    minHeight: 580,
    show: false,
    skipTaskbar: true,
    frame: false,
    transparent: false,
    backgroundColor: '#f7f7f8',
    title: 'Trợ lý Web MCP · Trung tâm Quản lý',
    icon: appIconPath(),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });
  managerWindow.removeMenu();
  const initialTheme = settings.load().theme === 'light' ? 'light' : 'dark';
  managerWindow.loadFile(path.join(__dirname, '..', 'renderer', 'index.html'), { query: { theme: initialTheme } });
  managerWindow.once('ready-to-show', () => managerWindow.show());
  managerWindow.on('close', (event) => {
    if (forceQuit) return;
    event.preventDefault();
    managerWindow.hide();
    if (chatWindow && !chatWindow.isDestroyed()) {
      chatWindow.show();
      chatWindow.focus();
    }
  });
  managerWindow.on('closed', () => { managerWindow = null; });
  return managerWindow;
}

function registerIpc() {
  secureHandle('app:snapshot', (_event, options) => invokeSafely(() => orchestrator.snapshot(options || {})));
  secureHandle('app:lightweight-snapshot', () => invokeSafely(() => orchestrator.lightweightSnapshot()));
  secureHandle('workspace:hub', () => invokeSafely(async () => { const current = settings.load(); return { activeWorkspace: current.workspace, recentWorkspaces: current.recentWorkspaces || [] }; }));
  secureHandle('workspace:switch', (_event, workspace) => invokeSafely(() => orchestrator.switchWorkspace(workspace)));
  secureHandle('workspace:authorized-roots', (_event, roots) => invokeSafely(() => orchestrator.updateAuthorizedRoots(roots)));
  secureHandle('workspace:choose-authorized-root', () => invokeSafely(async () => {
    const result = await dialog.showOpenDialog(chatWindow, { properties: ['openDirectory', 'createDirectory'] });
    if (result.canceled || !result.filePaths[0]) return null;
    const selected = path.resolve(result.filePaths[0]);
    const current = settings.load();
    const roots = Array.isArray(current.authorizedRoots) ? current.authorizedRoots : [];
    const key = selected.toLowerCase();
    const merged = roots.some((item) => String(item).toLowerCase() === key) ? roots : [...roots, selected];
    const snapshot = await orchestrator.updateAuthorizedRoots(merged);
    return { selected, snapshot };
  }));
  secureHandle('task-state:read', () => invokeSafely(async () => {
    let statePath;
    try { ({ statePath } = workspaceStatePaths()); } catch { return { exists: false, state: null }; }
    try {
      const state = JSON.parse(await fs.readFile(statePath, 'utf8'));
      return { exists: true, statePath, state };
    } catch (error) {
      if (error?.code === 'ENOENT') return { exists: false, statePath, state: null };
      throw new Error(`Đọc trạng thái nhiệm vụ thất bại: ${safeMessage(error)}`);
    }
  }));
  secureHandle('task-state:clear', () => invokeSafely(async () => {
    let paths;
    try { paths = workspaceStatePaths(); } catch { return false; }
    const { statePath, historyPath } = paths;
    archiveTask(readJson(statePath, null), historyPath, 'cleared-from-assistant');
    await fs.unlink(statePath).catch((error) => { if (error?.code !== 'ENOENT') throw error; });
    return true;
  }));
  secureHandle('task-state:pause', () => invokeSafely(async () => {
    const { statePath } = workspaceStatePaths();
    const state = readJson(statePath, null); if (!state) throw new Error('Hiện không có nhiệm vụ nào có thể tạm dừng.');
    state.status = 'paused'; state.pause_reason = 'Người dùng tạm dừng từ trợ lý'; state.updated_at = new Date().toISOString();
    writeJsonAtomic(statePath, state); return state;
  }));
  secureHandle('task-state:resume', () => invokeSafely(async () => {
    const { statePath } = workspaceStatePaths();
    const state = readJson(statePath, null); if (!state) throw new Error('Hiện không có nhiệm vụ nào có thể tiếp tục.');
    state.status = 'active'; state.pause_reason = ''; state.updated_at = new Date().toISOString();
    writeJsonAtomic(statePath, state); return state;
  }));
  secureHandle('task-state:stop', () => invokeSafely(async () => {
    const { statePath } = workspaceStatePaths();
    const state = readJson(statePath, null); if (!state) throw new Error('Hiện không có nhiệm vụ nào có thể dừng.');
    state.status = 'stopped'; state.failure = 'Người dùng dừng nhiệm vụ từ trợ lý';
    state.next_step = state.next_step || 'Tiếp tục nhiệm vụ hiện tại sau khi xác nhận, hoặc bắt đầu nhiệm vụ mới.';
    state.updated_at = new Date().toISOString();
    writeJsonAtomic(statePath, state); return state;
  }));
  secureHandle('task-state:history', () => invokeSafely(async () => {
    let historyPath;
    try { ({ historyPath } = workspaceStatePaths()); } catch { return []; }
    try { const value = JSON.parse(await fs.readFile(historyPath, 'utf8')); return Array.isArray(value) ? value.slice(-50).reverse() : []; }
    catch (error) { if (error?.code === 'ENOENT') return []; throw error; }
  }));
  secureHandle('performance:read', () => invokeSafely(async () => {
    let performancePath;
    try { ({ performancePath } = workspaceStatePaths()); } catch { return null; }
    try { return JSON.parse(await fs.readFile(performancePath, 'utf8')); }
    catch (error) { if (error?.code === 'ENOENT') return null; throw error; }
  }));
  secureHandle('performance:clear', () => invokeSafely(async () => {
    const { performancePath } = workspaceStatePaths();
    await fs.rm(performancePath, { force: true });
    return true;
  }));
  secureHandle('build:inspect', () => invokeSafely(() => buildVerification.inspect(settings.load().workspace)));
  secureHandle('build:run', (_event, options) => invokeSafely(() => buildVerification.execute(settings.load().workspace, options || {})));
  secureHandle('health:inspect', () => invokeSafely(() => orchestrator.healthInspect()));
  secureHandle('health:repair', () => invokeSafely(() => orchestrator.healthRepair()));
  secureHandle('workspace:choose-and-switch', () => invokeSafely(async () => { const result = await dialog.showOpenDialog(chatWindow, { properties: ['openDirectory', 'createDirectory'] }); if (result.canceled) return null; return orchestrator.switchWorkspace(result.filePaths[0]); }));
  secureHandle('manager:close', () => invokeSafely(async () => {
    if (managerWindow && !managerWindow.isDestroyed()) managerWindow.hide();
    if (chatWindow && !chatWindow.isDestroyed()) {
      chatWindow.show();
      chatWindow.focus();
    }
    return true;
  }));
  secureHandle('manager:open', () => invokeSafely(async () => { openManagerWindow(); return true; }));
  secureHandle('chat:navigate', (_event, action) => invokeSafely(async () => chatController?.navigate(action)));
  secureHandle('chat:status', () => invokeSafely(async () => chatController?.getState() || null));
  secureHandle('panel:toggle', () => invokeSafely(async () => ({ visible: togglePanel() })));
  secureHandle('panel:visibility', () => invokeSafely(async () => ({ visible: panelVisible })));
  secureHandle('panel:orchestration', () => invokeSafely(async () => {
    const current = settings.load();
    const token = secrets.get('mcpAuthToken');
    if (!token) throw new Error('MCP chưa sẵn sàng để đọc trạng thái điều phối.');
    return httpRequestJson({
      port: current.mcpPort,
      path: '/__control/orchestration',
      method: 'GET',
      token,
      timeout: PANEL_ORCHESTRATION_TIMEOUT_MS
    });
  }));
  secureHandle('panel:task-control', (_event, action) => invokeSafely(() => panelTaskControl(String(action || ''))));
  secureHandle('panel:transfer-controller', (_event, payload) => invokeSafely(async () => {
    const current = settings.load();
    const token = secrets.get('mcpAuthToken');
    if (!token) throw new Error('MCP chưa sẵn sàng để chuyển controller.');
    const targetClientId = String(payload?.targetClientId || '').trim();
    if (!['chatweb', 'codex-desktop'].includes(targetClientId)) throw new Error('Controller target không hợp lệ.');
    const runId = String(payload?.runId || '').trim();
    return httpRequestJson({
      port: current.mcpPort,
      path: '/__control/hub',
      method: 'POST',
      token,
      body: { action: 'transfer_controller', target_client_id: targetClientId, ...(runId ? { run_id: runId } : {}) },
      timeout: 5000
    });
  }));
  secureHandle('panel:copy-codex-config', () => invokeSafely(async () => {
    const python = await pythonStatus();
    if (!python.installed) throw new Error('Không tìm thấy Python 3.11+ để tạo cấu hình Codex Desktop.');
    const moduleRoot = path.join(resourcesRoot(), 'coding-tools-mcp');
    const pythonPath = [path.join(moduleRoot, 'python_vendor'), moduleRoot].join(path.delimiter);
    const config = buildCodexDesktopMcpConfig({
      pythonCommand: python.command,
      prefixArgs: python.prefixArgs || [],
      pythonPath,
      descriptorPath: hubProxyDescriptorFile()
    });
    clipboard.writeText(config.toml);
    return { copied: true, mode: config.mode, descriptorPath: config.descriptorPath, containsBearer: false };
  }));
  secureHandle('panel:handoff', (_event, payload) => invokeSafely(async () => {
    const current = settings.load();
    const token = secrets.get('mcpAuthToken');
    if (!token) throw new Error('MCP chưa sẵn sàng để ghi capsule handoff.');
    const summaryText = String((payload && payload.summary) || '').slice(0, 600);
    const request = {
      jsonrpc: '2.0',
      id: `panel-handoff-${Date.now()}`,
      method: 'tools/call',
      params: {
        name: 'task_control',
        arguments: { action: 'handoff', handoff_action: 'record', payload: { panel_summary: summaryText } },
        _meta: {
          'io.modelcontextprotocol/protocolVersion': '2026-07-28',
          'io.modelcontextprotocol/clientCapabilities': {},
          'io.modelcontextprotocol/clientInfo': { name: 'web-mcp-assistant-panel', version: app.getVersion() }
        }
      }
    };
    const response = await httpRequestJson({
      port: current.mcpPort,
      path: '/mcp',
      method: 'POST',
      token,
      body: request,
      headers: {
        'MCP-Protocol-Version': '2026-07-28',
        'Mcp-Method': 'tools/call',
        'Mcp-Name': 'task_control',
        'X-Coding-Tools-Client-Id': 'electron-panel',
        'X-Coding-Tools-Client-Type': 'electron'
      },
      timeout: 10000
    });
    if (response && response.error) throw new Error(response.error.message || 'MCP từ chối thao tác handoff.');
    return (response && response.result) || null;
  }));
  secureHandle('chat:clear-session', () => invokeSafely(async () => {
    if (!chatController) throw new Error('Trang ChatGPT chưa được khởi tạo.');
    await chatController.clearSession();
    return true;
  }));
  secureHandle('dialog:workspace', () => invokeSafely(async () => {
    const result = await dialog.showOpenDialog(managerWindow || chatWindow, { properties: ['openDirectory', 'createDirectory'] });
    return result.canceled ? '' : result.filePaths[0];
  }));
  secureHandle('settings:save', (_event, patch) => invokeSafely(async () => {
    // Recovery settings stay explicitly operator-controlled and separate from the primary runtime failure domain.
    const allowed = ['permissionMode', 'toolMode', 'mcpPort', 'healthPort', 'recoveryMcpPort', 'recoveryHealthPort', 'proxyMode', 'proxyUrl', 'tunnelId', 'tunnelProfile', 'recoveryTunnelId', 'recoveryTunnelProfile', 'startWithWindows', 'autoStartServices', 'keepRunningOnClose', 'progressReportSeconds', 'theme', 'guideProgress', 'firstRunCompleted', 'costPreset', 'costRateInUsd', 'costRateOutUsd', 'costCurrency', 'costFxRate', 'costBytesPerToken', 'costLaneRates'];
    const clean = Object.fromEntries(Object.entries(patch || {}).filter(([key]) => allowed.includes(key)));
    const saved = settings.save(clean);
    if (Object.hasOwn(clean, 'startWithWindows')) {
      app.setLoginItemSettings({
        openAtLogin: Boolean(saved.startWithWindows),
        path: process.execPath,
        args: recoveryLoginItemArguments(app)
      });
    }
    clearProxyCache();
    return saved;
  }));
  secureHandle('environment:detect-proxy', () => invokeSafely(async () => resolveProxy(settings.load(), { force: true })));
  secureHandle('secrets:runtime-key', (_event, value) => invokeSafely(async () => {
    if (String(value || '').trim().length < 12) throw new Error('Độ dài Runtime API Key không hợp lệ.');
    secrets.set('runtimeApiKey', value);
    return secrets.status();
  }));
  secureHandle('secrets:runtime-key-remove', () => invokeSafely(async () => {
    secrets.remove('runtimeApiKey');
    return secrets.status();
  }));
  secureHandle('secrets:mcp-token-regenerate', () => invokeSafely(async () => {
    secrets.set('mcpAuthToken', crypto.randomBytes(32).toString('base64url'));
    return secrets.status();
  }));
  secureHandle('runtime:start', () => invokeSafely(() => orchestrator.start()));
  secureHandle('runtime:stop', () => invokeSafely(() => orchestrator.stop()));
  secureHandle('runtime:restart', () => invokeSafely(() => orchestrator.restart()));
  secureHandle('code:activation-preflight', (_event, component, allowAcceptancePending) => invokeSafely(async () => {
    const request = codeActivationRequest(component, allowAcceptancePending);
    return { request, preflight: await orchestrator.activationPreflight(request) };
  }));
  secureHandle('code:activate-update', (_event, component, allowAcceptancePending) => invokeSafely(async () => {
    const request = codeActivationRequest(component, allowAcceptancePending);
    const result = await orchestrator.activateUpdate(request);
    if (component === 'electron_ui') setImmediate(() => registerUiRevision().catch(() => {}));
    return result;
  }));
  secureHandle('code:activation-status', (_event, operationId) => invokeSafely(() => orchestrator.activationStatus(operationId)));
  secureHandle('connector:ack-contract', () => invokeSafely(() => orchestrator.acknowledgeConnectorContract()));
  secureHandle('logs:read', () => invokeSafely(() => orchestrator.readLogs()));
  secureHandle('logs:clear', () => invokeSafely(() => orchestrator.clearLogs()));
  secureHandle('environment:install-python', () => invokeSafely(async () => {
    const result = await run('winget.exe', ['install', '--id', 'Python.Python.3.12', '-e', '--accept-source-agreements', '--accept-package-agreements']);
    return result.stdout;
  }));
  secureHandle('shell:open', (_event, target) => invokeSafely(async () => {
    const allowed = new Set(['chatgpt-connectors', 'openai-tunnels', 'openai-runtime-keys', 'tunnel-ui', 'coding-tools-source']);
    if (!allowed.has(target)) throw new Error('Không được phép mở địa chỉ này.');
    if (target === 'chatgpt-connectors' && chatController) {
      await chatController.openUrl('https://chatgpt.com/#settings/Connectors');
      if (chatWindow && !chatWindow.isDestroyed()) {
        chatWindow.show();
        chatWindow.focus();
      }
      return true;
    }
    const current = settings.load();
    const urls = {
      'chatgpt-connectors': 'https://chatgpt.com/#settings/Connectors',
      'openai-tunnels': 'https://platform.openai.com/settings/organization/tunnels',
      'openai-runtime-keys': 'https://platform.openai.com/settings/organization/api-keys',
      'tunnel-ui': `http://127.0.0.1:${current.healthPort}/ui`,
      'coding-tools-source': 'https://github.com/xyTom/coding-tools-mcp'
    };
    await shell.openExternal(urls[target]);
    return true;
  }));
}

if (recoveryHostMode) {
  app.whenReady().then(() => startRecoveryHostApplication(app));
} else {
  const hasSingleInstanceLock = app.requestSingleInstanceLock();
  if (!hasSingleInstanceLock) app.quit();
  app.on('second-instance', () => showChatWindow());

  app.whenReady().then(async () => {
    app.setLoginItemSettings({
      openAtLogin: Boolean(settings.load().startWithWindows),
      path: process.execPath,
      args: recoveryLoginItemArguments(app)
    });
    session.defaultSession.setPermissionRequestHandler((_webContents, _permission, callback) => callback(false));
    session.defaultSession.setPermissionCheckHandler(() => false);
    app.on('web-contents-created', (_event, contents) => {
      contents.on('will-attach-webview', (event) => event.preventDefault());
    });
    createTray();
    try {
      orchestrator = await ensureRecoveryHost({ app, paths: runtimePaths, log });
    } catch (error) {
      orchestrator = new RecoveryIpcClient({ paths: runtimePaths });
      log.error(error.message, { stage: 'recovery-host-connect', code: error?.code || '' });
    }
    await registerUiRevision().catch((error) => log.warn(error.message, { stage: 'ui-revision-registration', code: error?.code || '' }));
    buildVerification = new BuildVerificationService(log, (payload) => sendManager('build:progress', payload));
    log.on('entry', (payload) => sendManager('logs:entry', payload));
    registerIpc();
    createChatWindow();
    setInterval(() => orchestrator.lightweightSnapshot().then((status) => {
      const progress = status?.recoveryHost?.last_progress;
      if (progress?.time && progress.time !== lastRecoveryProgressTime) {
        lastRecoveryProgressTime = progress.time;
        sendManager('runtime:progress', progress);
      }
      sendManager('runtime:heartbeat', status);
      if (chatWindow && !chatWindow.isDestroyed()) chatWindow.webContents.send('runtime:heartbeat', status);
    }).then(() => registerUiRevision()).catch(() => {}), 5000).unref();
    log.info('Trợ lý Web MCP UI đã kết nối Recovery Host');
  });

  app.on('before-quit', () => { forceQuit = true; });
  app.on('window-all-closed', () => {
    if (!forceQuit && settings.load().keepRunningOnClose) return;
    if (!forceQuit) app.quit();
  });
  app.on('activate', () => showChatWindow());
}
