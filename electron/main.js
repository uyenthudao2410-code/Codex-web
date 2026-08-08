const path = require('node:path');
const fs = require('node:fs/promises');
const crypto = require('node:crypto');
const { app, BrowserWindow, dialog, ipcMain, shell, Tray, Menu, nativeImage, session } = require('electron');
const { SettingsStore } = require('./services/settingsStore');
const { SecretStore } = require('./services/secretStore');
const { LogService } = require('./services/logService');
const { EnvironmentService } = require('./services/environmentService');
const { RuntimeOrchestrator } = require('./services/runtimeOrchestrator');
const { ChatViewController } = require('./chatViewController');
const { run } = require('./services/commandRunner');
const { resolveProxy, clearProxyCache } = require('./services/proxyService');
const { BuildVerificationService } = require('./services/buildVerificationService');
const { HealthService } = require('./services/healthService');
const { readJson, writeJsonAtomic } = require('./services/jsonStore');

let chatWindow;
let managerWindow;
let chatController;
let orchestrator;
let forceQuit = false;
let tray = null;
let buildVerification;
let healthService;
const settings = new SettingsStore();
const secrets = new SecretStore();
const log = new LogService();
const environment = new EnvironmentService();

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
    }
  });
  chatController.mount();

  chatWindow.once('ready-to-show', () => chatWindow.show());
  chatWindow.on('closed', () => {
    if (chatController) chatController.dispose();
    chatController = null;
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
  secureHandle('health:inspect', () => invokeSafely(() => healthService.inspect()));
  secureHandle('health:repair', () => invokeSafely(() => healthService.repair()));
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
    const allowed = ['permissionMode', 'toolMode', 'mcpPort', 'healthPort', 'proxyMode', 'proxyUrl', 'tunnelId', 'tunnelProfile', 'startWithWindows', 'autoStartServices', 'keepRunningOnClose', 'progressReportSeconds', 'theme', 'guideProgress', 'firstRunCompleted'];
    const clean = Object.fromEntries(Object.entries(patch || {}).filter(([key]) => allowed.includes(key)));
    const saved = settings.save(clean);
    if (Object.hasOwn(clean, 'startWithWindows')) {
      app.setLoginItemSettings({ openAtLogin: Boolean(saved.startWithWindows), path: process.execPath });
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
  secureHandle('logs:read', () => invokeSafely(async () => log.read()));
  secureHandle('logs:clear', () => invokeSafely(async () => { log.clear(); return true; }));
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

const hasSingleInstanceLock = app.requestSingleInstanceLock();
if (!hasSingleInstanceLock) app.quit();
app.on('second-instance', () => showChatWindow());

app.whenReady().then(async () => {
  app.setLoginItemSettings({ openAtLogin: Boolean(settings.load().startWithWindows), path: process.execPath });
  session.defaultSession.setPermissionRequestHandler((_webContents, _permission, callback) => callback(false));
  session.defaultSession.setPermissionCheckHandler(() => false);
  app.on('web-contents-created', (_event, contents) => {
    contents.on('will-attach-webview', (event) => event.preventDefault());
  });
  createTray();
  orchestrator = new RuntimeOrchestrator({
    settings,
    secrets,
    environment,
    log,
    emitProgress: (payload) => sendManager('runtime:progress', payload),
    emitStatus: (payload) => sendManager('runtime:status-changed', payload)
  });
  buildVerification = new BuildVerificationService(log, (payload) => sendManager('build:progress', payload));
  healthService = new HealthService({ settings, secrets, environment, orchestrator });
  log.on('entry', (payload) => sendManager('logs:entry', payload));
  registerIpc();
  createChatWindow();
  setInterval(() => orchestrator.supervise().then((status) => {
    sendManager('runtime:heartbeat', status);
    if (chatWindow && !chatWindow.isDestroyed()) chatWindow.webContents.send('runtime:heartbeat', status);
  }).catch(() => {}), 5000).unref();
  log.info('Trợ lý Web MCP đã khởi động');
  if (settings.load().autoStartServices && !orchestrator.isManuallyStopped()) {
    orchestrator.start({ automatic: true }).catch((error) => log.error(error.message, { stage: 'auto-start' }));
  }
});

app.on('before-quit', () => { forceQuit = true; });
app.on('window-all-closed', () => {
  if (!forceQuit && settings.load().keepRunningOnClose) return;
  if (!forceQuit) app.quit();
});
app.on('activate', () => showChatWindow());
