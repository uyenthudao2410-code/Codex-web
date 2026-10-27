'use strict';

// P3-C1: read-only probe+poll channel for REGISTERED folders only.
// Main side: new IPC handlers accept only roots from settings.workspace,
// settings.authorizedRoots, settings.recentWorkspaces, or the control-plane
// workspace registry (well-formed entries only); anything else rejects with
// the same wrong-target error shape, before any service call.
// Renderer side: one poller per folder, keyed by canonical workspace; view
// switches never kill another folder's poller or discard its turn status.

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const mainSource = fs.readFileSync(path.join(__dirname, '..', 'electron/main.js'), 'utf8');
const preloadSource = fs.readFileSync(path.join(__dirname, '..', 'electron/preload.js'), 'utf8');
const rendererSource = fs.readFileSync(path.join(__dirname, '..', 'renderer/work-hub.js'), 'utf8');
const { canonicalPathKey } = require('../electron/services/pathSemantics');

function fragment(source, start, end) {
  const from = source.indexOf(start);
  const to = end ? source.indexOf(end, from) : source.length;
  assert.ok(from >= 0 && to > from, `Missing source boundary: ${start}`);
  return source.slice(from, to);
}

// ---------------------------------------------------------------- main ---
const REGISTRY = {
  schema_version: 1,
  entries: [
    { workspace_id: 'workspace_reg', workspace_generation: 'generation_reg', canonical_path: 'E:\\Registry' },
  ],
};

function mainFixture({ registryMode = 'ok' } = {}) {
  const handlers = new Map();
  const calls = [];
  const settingsValue = {
    workspace: 'E:\\Active',
    authorizedRoots: ['E:\\Auth'],
    recentWorkspaces: ['E:\\Recent'],
  };
  const fsSync = {
    readFileSync(file) {
      assert.equal(file, '/data/control-plane-workspaces.json');
      if (registryMode === 'ok') return Buffer.from(JSON.stringify(REGISTRY), 'utf8');
      if (registryMode === 'noid') {
        return Buffer.from(JSON.stringify({
          schema_version: 1,
          entries: [{ canonical_path: 'E:\\NoId' }],
        }), 'utf8');
      }
      if (registryMode === 'malformed') return Buffer.from('{not json', 'utf8');
      throw new Error('ENOENT: no registry file');
    },
  };
  const codexChat = {
    probe: async (root) => { calls.push(['probe', root]); return { ok: true, state: 'READY', data: { state: 'READY', threadId: null } }; },
    poll: async (root) => { calls.push(['poll', root]); return { ok: true, state: 'RUNNING', data: { state: 'RUNNING', threadId: 'thread-x' } }; },
  };
  vm.runInNewContext(fragment(mainSource, '  // P3-C1: read-only registered-folder chat status.', '  // W5 git range review'), {
    settings: { load: () => settingsValue },
    fsSync,
    runtimePaths: { controlPlaneWorkspaceRegistryFile: () => '/data/control-plane-workspaces.json' },
    canonicalPathKey,
    codexChat,
    secureHandle: (channel, handler) => { handlers.set(channel, handler); },
    invokeSafely: async (action) => {
      try { return { ok: true, data: await action() }; }
      catch (error) { return { ok: false, error: error.message }; }
    },
  });
  return {
    calls,
    invoke: (channel, payload) => handlers.get(channel)({}, payload),
  };
}

test('main: probe-registered accepts the settings workspace, authorized roots, recent workspaces, and registry roots', async () => {
  const f = mainFixture();
  for (const root of ['E:\\Active', 'E:\\Auth', 'E:\\Recent', 'E:\\Registry']) {
    const result = await f.invoke('workhub:codex-chat-probe-registered', { expectedWorkspace: root });
    assert.equal(result.ok, true, `${root}: ${result.error || ''}`);
    assert.equal(result.data.state, 'READY');
  }
  assert.deepEqual(f.calls.map((call) => call[1]), ['E:\\Active', 'E:\\Auth', 'E:\\Recent', 'E:\\Registry']);
});

test('main: poll-registered accepts a registered root and reaches only poll', async () => {
  const f = mainFixture();
  const result = await f.invoke('workhub:codex-chat-poll-registered', { expectedWorkspace: 'E:\\Auth' });
  assert.equal(result.ok, true);
  assert.equal(result.data.state, 'RUNNING');
  assert.deepEqual(f.calls, [['poll', 'E:\\Auth']]);
});

test('main: an existing-but-unregistered directory rejects before any service call', async () => {
  const f = mainFixture();
  const result = await f.invoke('workhub:codex-chat-probe-registered', { expectedWorkspace: 'E:\\Unregistered' });
  assert.equal(result.ok, false);
  assert.match(result.error, /Dự án đã thay đổi/);
  assert.equal(f.calls.length, 0);
});

test('main: an alias spelling that canonical-matches a registered root succeeds and reaches the service with the registered spelling', async () => {
  const f = mainFixture();
  const result = await f.invoke('workhub:codex-chat-probe-registered', { expectedWorkspace: 'e:/active' });
  assert.equal(result.ok, true, result.error || '');
  assert.deepEqual(f.calls, [['probe', 'E:\\Active']]);
});

test('main: empty expected workspace rejects before any service call', async () => {
  const f = mainFixture();
  for (const payload of [{}, { expectedWorkspace: '' }, { expectedWorkspace: '   ' }]) {
    const result = await f.invoke('workhub:codex-chat-probe-registered', payload);
    assert.equal(result.ok, false);
    assert.match(result.error, /Dự án đã thay đổi/);
  }
  assert.equal(f.calls.length, 0);
});

test('main: registry failures fail closed for registry-only roots but keep settings roots', async () => {
  for (const registryMode of ['missing', 'malformed', 'noid']) {
    const f = mainFixture({ registryMode });
    const registryRoot = registryMode === 'noid' ? 'E:\\NoId' : 'E:\\Registry';
    const denied = await f.invoke('workhub:codex-chat-probe-registered', { expectedWorkspace: registryRoot });
    assert.equal(denied.ok, false, registryMode);
    assert.match(denied.error, /Dự án đã thay đổi/, registryMode);
    const allowed = await f.invoke('workhub:codex-chat-probe-registered', { expectedWorkspace: 'E:\\Active' });
    assert.equal(allowed.ok, true, registryMode);
    assert.deepEqual(f.calls, [['probe', 'E:\\Active']]);
  }
});

test('preload: the registered surface exposes probe+poll and NOTHING else', () => {
  const exposed = [...preloadSource.matchAll(/workhubCodexChat(\w*)Registered/g)].map((m) => m[1]);
  assert.deepEqual(exposed.sort(), ['Poll', 'Probe']);
  for (const forbidden of ['Send', 'Interrupt', 'Reset', 'Fork', 'Resume', 'Handoff', 'Models', 'History']) {
    assert.ok(!preloadSource.includes(`workhubCodexChat${forbidden}Registered`), forbidden);
    assert.ok(!preloadSource.includes(`codex-chat-${forbidden.toLowerCase()}-registered`), forbidden);
  }
  assert.ok(preloadSource.includes("ipcRenderer.invoke('workhub:codex-chat-probe-registered'"));
  assert.ok(preloadSource.includes("ipcRenderer.invoke('workhub:codex-chat-poll-registered'"));
});

// ------------------------------------------------------------- renderer ---
function domNode(text = '') {
  return {
    text, children: [], id: '', className: '', parentNode: null, nextSibling: null,
    appendChild(child) { this.children.push(child); child.parentNode = this; return child; },
    replaceChildren(...children) { this.children = children; for (const child of children) child.parentNode = this; },
    get textContent() { return this.text + this.children.map((child) => child.textContent).join(''); },
    set textContent(value) { this.text = String(value); this.children = []; },
  };
}

function rendererFixture({ withStateBox = true } = {}) {
  let workspace = 'E:\\Alpha';
  let stripBox = null;
  const stateBox = domNode();
  stateBox.parentNode = { insertBefore(node) { stripBox = node; } };
  const boxes = new Map(withStateBox ? [['#whCodexChatState', stateBox]] : []);
  const views = {
    'E:\\Alpha': { state: 'RUNNING', threadId: 'thread-alpha' },
    'E:\\Beta': { state: 'RUNNING', threadId: 'thread-beta' },
  };
  const pollCalls = [];
  const paintCalls = [];
  const intervals = new Map();
  let nextTimer = 0;
  const context = vm.createContext({
    ui: { requests: {}, gen: 0 },
    currentProject: () => workspace,
    $: (selector) => (selector === '#whCodexChatFolders' ? stripBox : boxes.get(selector)),
    el: (tag, className, text) => {
      const node = domNode(text === undefined ? '' : text);
      node.className = className;
      return node;
    },
    S: { workspaceKeyOf: (value) => String(value || '').toLowerCase().replace(/\//g, '\\') },
    store: { projectLabel: (value) => value },
    unwrap: (value) => value,
    paintCodexChat: (view) => { paintCalls.push(view); },
    setInterval: (callback) => { const id = ++nextTimer; intervals.set(id, callback); return id; },
    clearInterval: (id) => { intervals.delete(id); },
    window: {
      mcpAssistant: {
        workhubCodexChatPoll: async ({ expectedWorkspace }) => {
          pollCalls.push(['poll', expectedWorkspace]);
          const view = views[expectedWorkspace] || { state: 'READY', threadId: null };
          return { ok: true, state: view.state, data: view };
        },
        workhubCodexChatPollRegistered: async ({ expectedWorkspace }) => {
          pollCalls.push(['poll-registered', expectedWorkspace]);
          const view = views[expectedWorkspace] || { state: 'READY', threadId: null };
          return { ok: true, state: view.state, data: view };
        },
      },
    },
  });
  vm.runInContext(fragment(rendererSource, '  const CODEX_CHAT_STATE_LABELS = {', '  function paintCodexChat('), context);
  vm.runInContext(fragment(rendererSource, '  async function pollCodexChatTurn(', '  async function renderCodexChat('), context);
  vm.runInContext(fragment(rendererSource, '  function requestScope(', '  function saveCurrentDraft('), context);
  return {
    context, views, pollCalls, paintCalls, intervals,
    stripText: () => (stripBox ? stripBox.textContent : ''),
    switchProject(next) { workspace = next; context.ui.gen += 1; },
  };
}

test('renderer: a turn in folder A keeps its status row while viewing B and shows its final state on return, with no duplicate poller', async () => {
  const f = rendererFixture();
  const scopeA = f.context.requestScope('codex-chat');
  f.context.startCodexChatPolling(scopeA);
  assert.equal(f.intervals.size, 1);

  await f.context.pollCodexChatTurn(scopeA);
  assert.deepEqual(f.pollCalls, [['poll', 'E:\\Alpha']]);
  assert.match(f.stripText(), /E:\\Alpha/);
  assert.match(f.stripText(), /Đang chạy/);

  f.switchProject('E:\\Beta');
  await f.context.pollCodexChatTurn(scopeA);
  assert.deepEqual(f.pollCalls.at(-1), ['poll-registered', 'E:\\Alpha']);
  assert.match(f.stripText(), /E:\\Alpha/);
  assert.match(f.stripText(), /Đang chạy/);
  assert.equal(f.intervals.size, 1, 'switching views must not kill folder A poller');

  const scopeB = f.context.requestScope('codex-chat');
  f.context.startCodexChatPolling(scopeB);
  assert.equal(f.intervals.size, 2, 'poller map keeps 2 keys after a view switch');
  await f.context.pollCodexChatTurn(scopeB);
  assert.deepEqual(f.pollCalls.at(-1), ['poll', 'E:\\Beta']);
  assert.match(f.stripText(), /E:\\Beta/);
  assert.match(f.stripText(), /Đang chạy/);

  f.views['E:\\Alpha'] = { state: 'COMPLETED', threadId: 'thread-alpha' };
  f.switchProject('E:\\Alpha');
  await f.context.pollCodexChatTurn(scopeA);
  assert.deepEqual(f.pollCalls.at(-1), ['poll', 'E:\\Alpha']);
  assert.match(f.stripText(), /E:\\Alpha/);
  assert.match(f.stripText(), /Lượt chat hoàn tất/);
  assert.match(f.stripText(), /E:\\Beta/);
  assert.match(f.stripText(), /Đang chạy/);
  assert.equal(f.intervals.size, 1, 'only the completed folder poller stops; folder B keeps polling');
  assert.ok(f.pollCalls.every(([channel]) => channel === 'poll' || channel === 'poll-registered'), 'polling never sends');
  assert.equal(f.paintCalls.length, 2, 'only current-view ticks paint the full view; stale-scope ticks update the strip only');
});

test('renderer: starting twice for the same folder creates no duplicate poller', () => {
  const f = rendererFixture();
  const scopeA = f.context.requestScope('codex-chat');
  f.context.startCodexChatPolling(scopeA);
  f.context.startCodexChatPolling(scopeA);
  assert.equal(f.intervals.size, 1);
});

test('renderer: stopping one folder stops only that folder; stopping with no argument stops all', () => {
  const f = rendererFixture();
  const scopeA = f.context.requestScope('codex-chat');
  f.context.startCodexChatPolling(scopeA);
  f.switchProject('E:\\Beta');
  const scopeB = f.context.requestScope('codex-chat');
  f.context.startCodexChatPolling(scopeB);
  assert.equal(f.intervals.size, 2);
  f.context.stopCodexChatPolling('E:\\Alpha');
  assert.equal(f.intervals.size, 1);
  f.context.startCodexChatPolling(scopeA);
  assert.equal(f.intervals.size, 2);
  f.context.stopCodexChatPolling();
  assert.equal(f.intervals.size, 0);
});

test('renderer: remembering a folder state without a chat state box never throws', () => {
  const f = rendererFixture({ withStateBox: false });
  assert.doesNotThrow(() => {
    f.context.rememberCodexChatFolderState('E:\\Alpha', { state: 'RUNNING', threadId: 'thread-alpha' });
  });
  assert.equal(f.stripText(), '');
});
