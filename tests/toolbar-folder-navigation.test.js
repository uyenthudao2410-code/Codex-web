const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { EventEmitter } = require('node:events');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

function toolbarFixture(executionRole) {
  const source = read('renderer/browser.js');
  const start = source.indexOf("$('#addAuthorizedRootQuick').onclick =");
  const end = source.indexOf("$('#addWorkspace').onclick =", start);
  assert.ok(start >= 0 && end > start);
  const calls = [];
  const elements = new Map();
  const context = vm.createContext({
    switching: false,
    lastRuntimeState: executionRole ? { executionRole } : null,
    $: (selector) => {
      if (!elements.has(selector)) elements.set(selector, { textContent: '' });
      return elements.get(selector);
    },
    unwrap: (result) => {
      if (!result.ok) throw new Error(result.error);
      return result.data;
    },
    baseName: (value) => String(value).split(/[\\/]/).pop(),
    api: {
      openManager: async (page) => {
        calls.push(['manager', page]);
        return { ok: true, data: true };
      },
      chooseAuthorizedRoot: async () => {
        calls.push(['choose']);
        return { ok: true, data: { selected: 'E:\\extra-root' } };
      }
    }
  });
  vm.runInContext(source.slice(start, end), context);
  return {
    calls,
    context,
    click: () => elements.get('#addAuthorizedRootQuick').onclick(),
    message: () => elements.get('#switchState')?.textContent
  };
}

test('Ubuntu toolbar opens the shared folder manager without changing local roots', async () => {
  const fixture = toolbarFixture('central_executor');
  await fixture.click();
  assert.deepEqual(fixture.calls, [['manager', 'workspace']]);
  assert.match(fixture.message(), /Thư mục & quyền/);
  assert.doesNotMatch(fixture.message(), /Đã ủy quyền/);
  assert.equal(fixture.context.switching, false);
});

test('an unobserved execution role opens the folder manager without granting a legacy root', async () => {
  const fixture = toolbarFixture();
  await fixture.click();
  assert.deepEqual(fixture.calls, [['manager', 'workspace']]);
});

test('direct legacy toolbar retains its existing local folder chooser', async () => {
  const fixture = toolbarFixture('direct_legacy');
  await fixture.click();
  assert.deepEqual(fixture.calls, [['choose']]);
  assert.equal(fixture.message(), 'Đã ủy quyền: extra-root');
  assert.equal(fixture.context.switching, false);
});

test('failed manager navigation does not fall back to a local permission change', async () => {
  const fixture = toolbarFixture('central_executor');
  fixture.context.api.openManager = async () => ({ ok: false, error: 'Manager unavailable' });
  await fixture.click();
  assert.deepEqual(fixture.calls, []);
  assert.equal(fixture.message(), 'Manager unavailable');
  assert.equal(fixture.context.switching, false);
});

function managerFixture() {
  const source = read('electron/main.js');
  const start = source.indexOf('function managerNavigationPage(');
  const end = source.indexOf('function registerIpc()', start);
  assert.ok(start >= 0 && end > start);
  const windows = [];
  class PrimaryWindow extends EventEmitter {
    constructor() {
      super();
      this.destroyed = false;
      this.loading = false;
      this.messages = [];
      this.webContents = new EventEmitter();
      this.webContents.isDestroyed = () => this.destroyed;
      this.webContents.getURL = () => 'trusted-index';
      this.webContents.isLoadingMainFrame = () => this.loading;
      this.webContents.send = (channel, payload) => this.messages.push([channel, payload]);
      windows.push(this);
    }
    isDestroyed() { return this.destroyed; }
    show() { this.shown = true; }
    focus() { this.focused = true; }
  }
  const context = vm.createContext({
    chatWindow: null,
    isTrustedRendererUrl: (url) => url === 'trusted-index',
    showChatWindow: () => {
      if (!context.chatWindow || context.chatWindow.isDestroyed()) {
        context.chatWindow = new PrimaryWindow();
      }
      context.chatWindow.show();
      context.chatWindow.focus();
      return context.chatWindow;
    }
  });
  vm.runInContext(source.slice(start, end), context);
  return { context, windows, open: (page) => context.openManagerWindow(page) };
}

test('a folder shortcut opens the primary window and routes to workspace without a second manager', () => {
  const fixture = managerFixture();
  const manager = fixture.open('workspace');
  assert.equal(fixture.windows.length, 1);
  assert.equal(manager, fixture.context.chatWindow);
  assert.equal(manager.shown, true);
  assert.equal(manager.focused, true);
  assert.equal(manager.messages.length, 1);
  assert.equal(manager.messages[0][0], 'manager:navigate');
  assert.equal(manager.messages[0][1].page, 'workspace');
});

test('an existing primary window receives navigation while retaining its renderer state', () => {
  const fixture = managerFixture();
  const manager = fixture.open();
  manager.draft = { folder: 'retained' };
  assert.equal(fixture.open('workspace'), manager);
  assert.equal(manager.draft.folder, 'retained');
  assert.equal(fixture.windows.length, 1);
  assert.equal(manager.shown, true);
  assert.equal(manager.focused, true);
  assert.equal(manager.messages[0][1].page, 'system');
  assert.equal(manager.messages[1][0], 'manager:navigate');
  assert.equal(manager.messages[1][1].page, 'workspace');
});

test('navigation during primary loading waits for its renderer and ignores a closed window', () => {
  const fixture = managerFixture();
  const manager = fixture.open();
  manager.messages.length = 0;
  manager.loading = true;
  fixture.open('workspace');
  assert.equal(manager.messages.length, 0);
  manager.webContents.emit('did-finish-load');
  assert.equal(manager.messages[0][1].page, 'workspace');
  fixture.open('workspace');
  manager.destroyed = true;
  manager.webContents.emit('did-finish-load');
  assert.equal(manager.messages.length, 1);
});

test('queued folder navigation cannot target a replacement primary window or an untrusted page', () => {
  const fixture = managerFixture();
  const previous = fixture.open();
  previous.messages.length = 0;
  previous.loading = true;
  fixture.open('workspace');
  previous.destroyed = true;
  const current = fixture.open();
  previous.webContents.emit('did-finish-load');
  assert.equal(previous.messages.length, 0);
  assert.equal(current.messages.length, 1);
  current.webContents.getURL = () => 'https://chatgpt.com';
  fixture.open('workspace');
  assert.equal(current.messages.length, 1, 'arbitrary pages receive no privileged navigation event');
});

test('manager shortcuts reject unrecognized pages before opening or navigating a window', () => {
  const fixture = managerFixture();
  assert.throws(() => fixture.open('workspace#unexpected'), /không hợp lệ/);
  assert.throws(() => fixture.open({ page: 'workspace' }), /không hợp lệ/);
  assert.equal(fixture.windows.length, 0);
});

test('preload forwards folder navigation and cleans up its manager event subscription', async () => {
  const ipc = new EventEmitter();
  const calls = [];
  ipc.invoke = async (...args) => { calls.push(args); return true; };
  const exposed = {};
  const context = vm.createContext({
    require: (module) => {
      assert.equal(module, 'electron');
      return { ipcRenderer: ipc, contextBridge: { exposeInMainWorld: (name, api) => { exposed[name] = api; } } };
    },
    setTimeout,
    clearTimeout
  });
  vm.runInContext(read('electron/browserPreload.js'), context);
  await exposed.browserAssistant.openManager('workspace');
  assert.deepEqual(calls, [['manager:open', 'workspace']]);
  vm.runInContext(read('electron/preload.js'), vm.createContext({
    require: context.require,
    setTimeout,
    clearTimeout
  }));
  const received = [];
  const dispose = exposed.mcpAssistant.onNavigate((payload) => received.push(payload));
  ipc.emit('manager:navigate', {}, { page: 'workspace' });
  assert.deepEqual(received, [{ page: 'workspace' }]);
  dispose();
  ipc.emit('manager:navigate', {}, { page: 'workspace' });
  assert.equal(received.length, 1);
});
