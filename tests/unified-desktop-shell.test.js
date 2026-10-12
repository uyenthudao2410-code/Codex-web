'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { EventEmitter } = require('node:events');
const { pathToFileURL } = require('node:url');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'electron', 'main.js'), 'utf8');
const rendererPath = path.join(root, 'renderer', 'index.html');
const rendererUrl = pathToFileURL(rendererPath).href;

function sourceSection(start, end) {
  const first = source.indexOf(start);
  const last = source.indexOf(end, first);
  assert.ok(first >= 0 && last > first, `missing shell boundary ${start}`);
  return source.slice(first, last);
}

function shellFixture({ keepRunningOnClose = true } = {}) {
  const windows = [];
  const registrations = [];
  const quits = [];
  const handles = new Map();
  const currentSettings = { theme: 'light', keepRunningOnClose };
  class Contents extends EventEmitter {
    constructor() {
      super();
      this.url = '';
      this.destroyed = false;
      this.loading = true;
      this.messages = [];
      this.mainFrame = { url: '' };
    }
    isDestroyed() { return this.destroyed; }
    getURL() { return this.url; }
    isLoadingMainFrame() { return this.loading; }
    send(channel, payload) { this.messages.push({ channel, payload }); }
    setWindowOpenHandler(handler) { this.openHandler = handler; }
    finishLoad() {
      this.loading = false;
      this.emit('did-finish-load');
    }
  }
  class Window extends EventEmitter {
    constructor(options) {
      super();
      this.options = options;
      this.webContents = new Contents();
      this.destroyed = false;
      this.visible = false;
      this.minimized = false;
      windows.push(this);
    }
    isDestroyed() { return this.destroyed; }
    isMinimized() { return this.minimized; }
    isVisible() { return this.visible; }
    show() { this.visible = true; }
    hide() { this.visible = false; }
    focus() { this.focused = true; }
    restore() { this.minimized = false; }
    removeMenu() {}
    loadFile(file, options) {
      this.loadedFile = file;
      this.loadOptions = options;
      const url = new URL(pathToFileURL(file));
      url.search = new URLSearchParams(options?.query || {}).toString();
      url.hash = options?.hash || '';
      this.webContents.url = url.href;
      this.webContents.mainFrame.url = url.href;
    }
    close() {
      const event = { prevented: false, preventDefault() { this.prevented = true; } };
      this.emit('close', event);
      if (!event.prevented) this.destroy();
    }
    destroy() {
      this.destroyed = true;
      this.webContents.destroyed = true;
      this.emit('closed');
    }
  }
  const context = vm.createContext({
    path, URL, __dirname: path.join(root, 'electron'), BrowserWindow: Window,
    trustedRendererPath: rendererPath, trustedRendererUrl: rendererUrl,
    chatWindow: null, forceQuit: false, uiWindowReady: false, tray: null,
    orchestrator: {}, settings: { load: () => currentSettings },
    registerUiRevision: async () => { registrations.push(true); },
    quitUi: async (reason, options) => { quits.push({ reason, options }); },
    log: { error() {}, warn() {} },
    ipcMain: { handle: (channel, handler) => handles.set(channel, handler) },
    setTimeout: (callback) => callback()
  });
  for (const section of [
    sourceSection('function appIconPath', 'function workspaceStatePaths'),
    sourceSection('function showChatWindow', 'function httpRequestJson'),
    sourceSection('function togglePanel', 'function registerIpc')
  ]) vm.runInContext(section, context);
  return { context, windows, registrations, quits, handles, currentSettings };
}

function ipcEvent(window) {
  return { sender: window.webContents, senderFrame: window.webContents.mainFrame };
}

test('setup and execution navigation reuse one native window with the privileged renderer', async () => {
  const fixture = shellFixture();
  const window = fixture.context.openManagerWindow('workspace');
  assert.equal(fixture.windows.length, 1);
  assert.equal(window.loadedFile, rendererPath);
  assert.equal(window.loadOptions.hash, 'system');
  assert.equal(window.options.webPreferences.preload, path.join(root, 'electron', 'preload.js'));
  assert.equal(window.options.webPreferences.contextIsolation, true);
  assert.equal(window.options.webPreferences.nodeIntegration, false);
  assert.equal(window.options.webPreferences.sandbox, true);
  assert.notEqual(window.options.frame, false, 'use the ordinary OS frame');
  assert.notEqual(window.options.skipTaskbar, true, 'the only window belongs in the taskbar');
  assert.equal(window.webContents.messages.length, 0, 'wait for renderer load before routing');
  window.webContents.finishLoad();
  assert.equal(window.webContents.messages[0].payload.page, 'workspace');
  window.emit('ready-to-show');
  assert.equal(fixture.context.uiWindowReady, true);
  assert.equal(fixture.registrations.length, 1, 'primary identity still registers with Recovery Host');

  window.minimized = true;
  assert.equal(fixture.context.openManagerWindow('overview'), window);
  assert.equal(window.minimized, false);
  assert.equal(fixture.context.openManagerWindow(), window);
  assert.equal(window.webContents.messages.at(-1).payload.page, 'system');
  assert.equal(fixture.windows.length, 1);
  await Promise.resolve();
});

test('manager routes reject URLs and unknown pages before creating a window', () => {
  const fixture = shellFixture();
  for (const page of ['https://example.com', 'file:///tmp/index.html', '../workspace', 'devices', 'unknown', {}, 1]) {
    assert.throws(() => fixture.context.openManagerWindow(page), /không hợp lệ/);
  }
  assert.equal(fixture.windows.length, 0);
  for (const page of ['system', 'workspace', 'deploy', 'overview', 'device', 'settings']) {
    assert.equal(fixture.context.managerNavigationPage(page), page);
  }
});

test('privileged IPC requires the current window, its top-level frame, and the exact renderer file', () => {
  const fixture = shellFixture();
  const window = fixture.context.createChatWindow();
  const event = ipcEvent(window);
  assert.equal(fixture.context.isManagerIpc(event), true);
  assert.doesNotThrow(() => fixture.context.assertManagerIpc(event));
  let calls = 0;
  fixture.context.secureHandle('test:privileged', () => { calls += 1; return true; });
  const handler = fixture.handles.get('test:privileged');
  assert.equal(handler(event), true);

  const oldUrl = window.webContents.url;
  const otherLocalFile = pathToFileURL(path.join(root, 'renderer', 'browser.html')).href;
  for (const url of ['https://chatgpt.com/', otherLocalFile, `${rendererUrl}/extra`, 'file://example.com/index.html']) {
    window.webContents.url = url;
    assert.equal(fixture.context.isManagerIpc(event), false);
    assert.throws(() => handler(event), /không phải Execution Hub/);
  }
  window.webContents.url = oldUrl;
  assert.throws(() => handler({ sender: event.sender }), /không phải Execution Hub/);
  assert.throws(() => handler({ sender: {}, senderFrame: event.senderFrame }), /không phải Execution Hub/);
  assert.throws(() => handler({ sender: event.sender, senderFrame: { url: oldUrl } }), /không phải Execution Hub/);
  window.webContents.mainFrame.url = otherLocalFile;
  assert.throws(() => handler(event), /không phải Execution Hub/);
  assert.equal(calls, 1, 'rejected senders never reach the handler');
});

test('main window blocks browser navigation and popups while keeping in-app routes', () => {
  const fixture = shellFixture();
  const window = fixture.context.createChatWindow();
  assert.equal(window.webContents.openHandler({ url: 'https://chatgpt.com/' }).action, 'deny');
  for (const channel of ['will-navigate', 'will-redirect']) {
    for (const url of ['https://chatgpt.com/', pathToFileURL(path.join(root, 'renderer', 'browser.html')).href]) {
      let blocked = false;
      window.webContents.emit(channel, { preventDefault: () => { blocked = true; } }, url);
      assert.equal(blocked, true);
    }
    let blocked = false;
    window.webContents.emit(channel, { preventDefault: () => { blocked = true; } }, `${rendererUrl}?theme=dark#overview`);
    assert.equal(blocked, false);
  }
});

test('panel controls route into the execution view without creating an overlay or a window', () => {
  const fixture = shellFixture();
  const window = fixture.context.showChatWindow();
  window.webContents.finishLoad();
  assert.equal(fixture.context.togglePanel(), false);
  assert.equal(fixture.windows.length, 1);
  assert.equal(window.webContents.messages[0].channel, 'manager:navigate');
  assert.equal(window.webContents.messages[0].payload.page, 'overview');
  assert.equal(window.webContents.messages[1].payload.visible, false);
});

test('closing the unified window preserves background, explicit stop and Recovery UI identity semantics', () => {
  const fixture = shellFixture();
  const window = fixture.context.showChatWindow();
  window.emit('ready-to-show');
  window.close();
  assert.equal(window.isDestroyed(), false);
  assert.equal(window.visible, false);
  assert.equal(fixture.context.uiWindowReady, true);
  assert.equal(fixture.quits.length, 0);
  assert.equal(fixture.context.showChatWindow(), window);

  fixture.currentSettings.keepRunningOnClose = false;
  window.close();
  assert.equal(fixture.quits.length, 1);
  assert.equal(fixture.quits[0].reason, 'runtime_stop');
  assert.equal(fixture.quits[0].options.stopRuntime, true);
  fixture.context.forceQuit = true;
  window.close();
  assert.equal(fixture.context.chatWindow, null);
  assert.equal(fixture.context.uiWindowReady, false);
  const replacement = fixture.context.createChatWindow();
  assert.notEqual(replacement, window);
  assert.equal(fixture.context.isManagerIpc(ipcEvent(window)), false);
  assert.equal(fixture.context.isManagerIpc(ipcEvent(replacement)), true);
});

test('stale window events cannot clear or navigate a replacement primary window', () => {
  const fixture = shellFixture();
  const oldWindow = fixture.context.openManagerWindow('workspace');
  // Electron may finish emitting lifecycle events after isDestroyed() changes.
  oldWindow.destroyed = true;
  oldWindow.webContents.destroyed = true;
  const replacement = fixture.context.createChatWindow();
  replacement.emit('ready-to-show');
  oldWindow.emit('closed');
  oldWindow.emit('ready-to-show');
  oldWindow.webContents.finishLoad();
  assert.equal(fixture.context.chatWindow, replacement);
  assert.equal(fixture.context.uiWindowReady, true);
  assert.equal(fixture.registrations.length, 1);
  assert.equal(oldWindow.webContents.messages.length, 0);
  assert.equal(replacement.webContents.messages.length, 0);
});

test('runtime heartbeat has one primary delivery and one in-flight observation', async () => {
  const fixture = shellFixture();
  const window = fixture.context.showChatWindow();
  const status = { recoveryHost: { last_progress: { time: '2026-10-11T10:00:00Z' } } };
  let observations = 0;
  fixture.context.orchestrator.lightweightSnapshot = async () => { observations += 1; return status; };
  fixture.context.decorateUiRuntimeSnapshot = (value) => value;
  fixture.context.runtimeHeartbeatInFlight = null;
  fixture.context.lastRecoveryProgressTime = '';
  const publish = sourceSection('const publishRuntimeHeartbeat = () => {', 'setInterval(() => { void publishRuntimeHeartbeat();');
  vm.runInContext(`${publish}\nthis.publishRuntimeHeartbeat = publishRuntimeHeartbeat;`, fixture.context);
  await Promise.all([fixture.context.publishRuntimeHeartbeat(), fixture.context.publishRuntimeHeartbeat()]);
  assert.equal(observations, 1);
  assert.equal(window.webContents.messages.filter((item) => item.channel === 'runtime:heartbeat').length, 1);
  assert.equal(window.webContents.messages.filter((item) => item.channel === 'runtime:progress').length, 1);
  await fixture.context.publishRuntimeHeartbeat();
  assert.equal(observations, 2);
  assert.equal(window.webContents.messages.filter((item) => item.channel === 'runtime:heartbeat').length, 2);
  assert.equal(window.webContents.messages.filter((item) => item.channel === 'runtime:progress').length, 1);
});
