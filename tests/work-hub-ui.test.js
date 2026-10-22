'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const Store = require('../renderer/work-hub-store');

const root = path.resolve(__dirname, '..');
const markup = fs.readFileSync(path.join(root, 'renderer/index.html'), 'utf8');
const script = fs.readFileSync(path.join(root, 'renderer/work-hub.js'), 'utf8');
const PROJECT_A = 'E:/Projects/alpha';
const PROJECT_B = 'E:/Projects/beta';

// A small DOM fixture keeps these interaction tests independent of Electron.
// The production script, markup and store are used together; only browser/IPC
// boundaries are replaced. This is not a layout or native-window test.
class Element {
  constructor(tag, document) {
    this.tagName = tag.toUpperCase();
    this.ownerDocument = document;
    this.attributes = {};
    this.dataset = {};
    this.childNodes = [];
    this.listeners = new Map();
    this.hidden = false;
    this.disabled = false;
    this.value = '';
    this.checked = false;
    this.classList = {
      contains: (name) => this.className.split(/\s+/).includes(name),
      add: (...names) => { this.className = [...new Set([...this.className.split(/\s+/).filter(Boolean), ...names])].join(' '); },
      remove: (...names) => { this.className = this.className.split(/\s+/).filter((name) => !names.includes(name)).join(' '); },
      toggle: (name, force) => {
        const enabled = force === undefined ? !this.classList.contains(name) : Boolean(force);
        if (enabled) this.classList.add(name); else this.classList.remove(name);
        return enabled;
      },
    };
  }
  get id() { return this.attributes.id || ''; }
  set id(value) { this.setAttribute('id', value); }
  get className() { return this.attributes.class || ''; }
  set className(value) { this.setAttribute('class', value); }
  get children() { return this.childNodes.filter((node) => node instanceof Element); }
  get textContent() { return this.childNodes.map((node) => typeof node === 'string' ? node : node.textContent).join(''); }
  set textContent(value) { this.replaceChildren(String(value ?? '')); }
  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === 'id') this.ownerDocument.ids.set(String(value), this);
    if (name.startsWith('data-')) this.dataset[name.slice(5).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())] = String(value);
    if (name === 'hidden') this.hidden = true;
    if (name === 'disabled') this.disabled = true;
    if (name === 'value') this.value = String(value);
  }
  getAttribute(name) { return this.attributes[name] ?? null; }
  hasAttribute(name) { return name in this.attributes; }
  removeAttribute(name) { delete this.attributes[name]; if (name === 'hidden') this.hidden = false; }
  toggleAttribute(name, force) {
    const enabled = force === undefined ? !this.hasAttribute(name) : Boolean(force);
    if (enabled) this.setAttribute(name, ''); else this.removeAttribute(name);
    return enabled;
  }
  append(...nodes) { for (const node of nodes.flat()) { if (node instanceof Element) node.parentElement = this; this.childNodes.push(node); } }
  appendChild(node) { this.append(node); return node; }
  replaceChildren(...nodes) { this.childNodes = []; this.append(...nodes); }
  remove() { if (this.parentElement) this.parentElement.childNodes = this.parentElement.childNodes.filter((node) => node !== this); }
  addEventListener(name, callback) { const list = this.listeners.get(name) || []; list.push(callback); this.listeners.set(name, list); }
  async emit(name, extra = {}) {
    const event = { target: this, currentTarget: this, preventDefault() {}, stopPropagation() { this.stopped = true; }, ...extra };
    for (const callback of this.listeners.get(name) || []) await callback(event);
    if (extra.bubbles && !event.stopped) {
      if (this.parentElement) await this.parentElement.emit(name, { ...event, currentTarget: this.parentElement });
      else if (this.ownerDocument) await this.ownerDocument.emit(name, { ...event, currentTarget: this.ownerDocument });
    }
    return event;
  }
  querySelectorAll(selector) { return descendants(this).filter((node) => matches(node, selector)); }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
  closest(selector) { let node = this; while (node) { if (matches(node, selector)) return node; node = node.parentElement; } return null; }
  focus() { this.ownerDocument.activeElement = this; }
  select() {}
  scrollIntoView() {}
  setSelectionRange() {}
}

function descendants(element) { return element.children.flatMap((child) => [child, ...descendants(child)]); }
function matches(element, selector) {
  return selector.split(',').some((part) => {
    const token = part.trim();
    const tag = token.match(/^[a-z][\w-]*/i)?.[0];
    if (tag && element.tagName !== tag.toUpperCase()) return false;
    const id = token.match(/#([\w-]+)/)?.[1];
    if (id && element.id !== id) return false;
    for (const name of token.matchAll(/\.([\w-]+)/g)) if (!element.classList.contains(name[1])) return false;
    for (const attribute of token.matchAll(/\[([\w-]+)(?:=["']?([^\]"']*)["']?)?\]/g)) {
      if (!element.hasAttribute(attribute[1])) return false;
      if (attribute[2] !== undefined && element.getAttribute(attribute[1]) !== attribute[2]) return false;
    }
    return true;
  });
}

function createDocument() {
  const document = { ids: new Map(), listeners: new Map(), visibilityState: 'visible', hidden: false };
  document.body = new Element('body', document);
  document.createElement = (tag) => new Element(tag, document);
  document.createTextNode = (text) => String(text);
  document.querySelectorAll = (selector) => document.body.querySelectorAll(selector);
  document.querySelector = (selector) => /^#[\w-]+$/.test(selector) ? document.ids.get(selector.slice(1)) || null : document.querySelectorAll(selector)[0] || null;
  document.addEventListener = Element.prototype.addEventListener;
  document.emit = Element.prototype.emit;
  document.execCommand = () => true;
  const stack = [document.body];
  const voidTags = new Set(['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr']);
  for (const token of markup.matchAll(/<\/?([a-z][\w-]*)\b([^>]*?)>|([^<]+)/gi)) {
    if (token[3]) { stack.at(-1).append(token[3]); continue; }
    const tag = token[1].toLowerCase();
    if (token[0].startsWith('</')) {
      const index = stack.findLastIndex((element) => element.tagName === tag.toUpperCase());
      if (index > 0) stack.length = index;
      continue;
    }
    const element = document.createElement(tag);
    for (const attribute of token[2].matchAll(/([^\s=/'">]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g)) element.setAttribute(attribute[1], attribute[2] ?? attribute[3] ?? attribute[4] ?? '');
    stack.at(-1).append(element);
    if (!voidTags.has(tag) && !token[0].endsWith('/>')) stack.push(element);
  }
  return document;
}

function deferred() {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
}
const ok = (data) => ({ ok: true, data });
const settle = () => new Promise((resolve) => setImmediate(resolve));

async function fixture({ storage = new Map(), read, write, drafts = [] } = {}) {
  const document = createDocument();
  let workspace = PROJECT_A;
  const readCalls = [];
  const writeCalls = [];
  const shellCalls = [];
  const shellState = { workspace: PROJECT_A };
  const fileContents = new Map();
  const storageKey = 'coding-tools-work-hub-v1';
  const initialStore = Store.createStore({
    load: () => storage.has(storageKey) ? JSON.parse(storage.get(storageKey)) : null,
    save: (data) => storage.set(storageKey, JSON.stringify(data)),
  });
  for (const [project, draft] of drafts) initialStore.saveDraft(project, draft);
  const api = {
    snapshot: async () => {
      shellCalls.push(['snapshot', workspace]);
      return ok({ settings: { workspace, recentWorkspaces: [PROJECT_A, PROJECT_B] }, status: {} });
    },
    switchWorkspace: async (project) => {
      shellCalls.push(['switchWorkspace', project]);
      workspace = project;
      return ok({ settings: { workspace } });
    },
    taskState: async () => ok({ exists: false, state: null }),
    taskHistory: async () => ok([]),
    orchestration: async () => ok({ clients: [], delegations: [] }),
    listControlPlaneWorkspaces: async () => ok([]),
    workhubList: async () => ok({ root: workspace, rel: '', entries: [{ name: 'one.js', rel: 'one.js', type: 'file', size: 12 }, { name: 'two.js', rel: 'two.js', type: 'file', size: 12 }], truncated: false }),
    workhubRead: (rel, expectedWorkspace) => {
      readCalls.push({ rel, expectedWorkspace });
      const saved = fileContents.get(`${workspace}\n${rel}`);
      return read ? read(rel, workspace, expectedWorkspace) : Promise.resolve(ok({ rel, size: 12, content: saved ?? `${workspace}/${rel}`, hash: saved === undefined ? 'abc' : 'saved-hash', binary: false, truncated: false }));
    },
    workhubWrite: (rel, content, expectedHash, expectedWorkspace) => {
      writeCalls.push({ rel, content, expectedHash, expectedWorkspace });
      if (write) return write(rel, content, expectedHash, expectedWorkspace);
      fileContents.set(`${expectedWorkspace}\n${rel}`, content);
      return Promise.resolve(ok({ rel, hash: 'saved-hash' }));
    },
    workhubSearch: async (query) => ok({ query, results: [{ rel: 'one.js', line: 2, text: 'return 1;' }], scannedFiles: 2, truncated: false }),
    workhubGitStatus: async () => ok([]),
    workhubGitLog: async () => ok([]),
    workhubKeepAwake: async () => ok(true),
  };
  const window = {
    WorkHubStore: Store, mcpAssistant: api, alert() {}, prompt: () => null, confirm: () => true, focus() {}, addEventListener() {},
    navigate(page) { shellCalls.push(['navigate', page]); document.body.dataset.page = page; },
  };
  vm.runInNewContext(script, {
    window, document,
    refreshSnapshot: async () => { shellCalls.push(['refreshSnapshot', workspace]); shellState.workspace = workspace; },
    localStorage: { getItem: (key) => storage.get(key) || null, setItem: (key, value) => storage.set(key, value) },
    navigator: { clipboard: { writeText: async () => {} } },
    setInterval: () => 1, clearInterval() {}, setTimeout: () => 1, clearTimeout() {},
    console, URL, Date,
  }, { filename: 'renderer/work-hub.js' });
  await document.emit('DOMContentLoaded');
  await settle();
  return {
    document, storage, readCalls, writeCalls, shellCalls, shellState, hub: window.WorkHubUI,
    setWorkspace: (value) => { workspace = value; },
    refresh: async () => { await window.WorkHubUI.refresh(); await settle(); },
    get: (id) => document.querySelector(`#${id}`),
    openFile: (index = 0) => document.querySelector('#whFileList').children[index].querySelector('button').emit('click'),
  };
}

test('Work Hub tabs expose one panel and support keyboard navigation', async () => {
  const f = await fixture();
  const tabs = f.document.querySelectorAll('[data-wh-tab]');
  const panels = f.document.querySelectorAll('[data-wh-panel]');
  assert.deepEqual(tabs.map((tab) => tab.dataset.whTab), ['context', 'progress', 'changes', 'verify', 'results']);
  assert.equal(panels.length, 5);
  assert.equal(tabs.filter((tab) => tab.getAttribute('aria-selected') === 'true').length, 1);
  assert.equal(tabs.find((tab) => tab.getAttribute('aria-selected') === 'true').dataset.whTab, 'context');
  assert.equal(panels.filter((panel) => !panel.hidden).length, 1);
  const changes = tabs.find((tab) => tab.dataset.whTab === 'changes');
  await changes.emit('click');
  for (const tab of tabs) assert.equal(tab.getAttribute('aria-selected'), String(tab === changes));
  for (const panel of panels) assert.equal(panel.hidden, panel.dataset.whPanel !== 'changes');
  await changes.emit('keydown', { key: 'ArrowRight' });
  const selected = tabs.find((tab) => tab.getAttribute('aria-selected') === 'true');
  assert.equal(selected.dataset.whTab, 'verify');
  assert.equal(f.document.activeElement, selected);
  assert.equal(f.get(selected.getAttribute('aria-controls')).hidden, false);
  await selected.emit('keydown', { key: 'Home' });
  assert.equal(tabs.find((tab) => tab.getAttribute('aria-selected') === 'true').dataset.whTab, 'context');
  await tabs[0].emit('keydown', { key: 'ArrowRight' });
  assert.equal(f.document.activeElement.dataset.whTab, 'progress');
  assert.equal(f.get('whPanelProgress').hidden, false);
  await f.document.activeElement.emit('keydown', { key: 'End' });
  assert.equal(f.document.activeElement.dataset.whTab, 'results');
  await f.document.activeElement.emit('keydown', { key: 'ArrowRight' });
  assert.equal(f.document.activeElement.dataset.whTab, 'context');
});

test('global project switch refreshes app scope before returning from History to Work Hub', async () => {
  const f = await fixture();
  f.document.body.dataset.page = 'task';
  f.shellCalls.length = 0;
  const beta = f.get('whProjects').children.find((row) => row.textContent.includes(PROJECT_B));
  const switchButton = beta.querySelectorAll('button').find((button) => button.textContent === 'Chuyển đến');
  const pending = switchButton.emit('click');
  assert.equal(f.document.querySelector('.main-area').inert, true);
  assert.equal(f.document.body.dataset.page, 'task');
  await pending;
  await settle();
  assert.deepEqual(f.shellCalls.slice(0, 4), [
    ['switchWorkspace', PROJECT_B], ['refreshSnapshot', PROJECT_B], ['navigate', 'workhub'], ['snapshot', PROJECT_B],
  ]);
  assert.equal(f.shellState.workspace, PROJECT_B);
  assert.equal(f.document.body.dataset.page, 'workhub');
  assert.equal(f.get('whWorkspacePath').textContent, PROJECT_B);
  assert.equal(f.get('whWorkspaceName').textContent, 'beta');
  assert.equal(f.document.querySelector('.main-area').inert, false);
});

test('workspace change from Settings refreshes the global header and Work Hub draft', async () => {
  const f = await fixture({ drafts: [[PROJECT_B, { text: 'beta saved request', type: 'feature', fields: { goal: 'beta goal' } }]] });
  f.document.body.dataset.page = 'system';
  f.setWorkspace(PROJECT_B);
  f.shellCalls.length = 0;
  await f.document.emit('coding-tools:workspace-changed', { detail: { workspace: PROJECT_B } });
  await settle();
  assert.deepEqual(f.shellCalls, [['snapshot', PROJECT_B]]);
  assert.equal(f.document.body.dataset.page, 'system');
  assert.equal(f.get('whWorkspacePath').textContent, PROJECT_B);
  assert.equal(f.get('whWorkspaceName').textContent, 'beta');
  assert.equal(f.get('whPreview').value, 'beta saved request');
  assert.equal(f.get('whField-goal').value, 'beta goal');
});

test('changing projects clears file selection and ignores an old read response', async () => {
  const oldRead = deferred();
  const f = await fixture({ read: (rel, project) => project === PROJECT_A ? oldRead.promise : Promise.resolve(ok({ rel, content: 'beta content', size: 12, hash: 'beta' })) });
  await f.refresh();
  const pendingOpen = f.openFile();
  f.setWorkspace(PROJECT_B);
  await f.refresh();
  assert.equal(f.get('whViewerAddBasket').disabled, true);
  assert.equal(f.get('whEditFile').disabled, true);
  oldRead.resolve(ok({ rel: 'one.js', content: 'alpha stale content', size: 12, hash: 'alpha' }));
  await pendingOpen;
  await settle();
  assert.doesNotMatch(f.get('whViewer').textContent, /alpha stale content/);
  await f.openFile();
  await settle();
  assert.match(f.get('whViewer').textContent, /beta content/);
});

test('a slower file read cannot replace a newer selection in the same project', async () => {
  const first = deferred();
  const second = deferred();
  const f = await fixture({ read: (rel) => rel === 'one.js' ? first.promise : second.promise });
  await f.refresh();
  const firstOpen = f.openFile(0);
  const secondOpen = f.openFile(1);
  second.resolve(ok({ rel: 'two.js', content: 'second selection', size: 12, hash: 'second' }));
  await secondOpen;
  await settle();
  first.resolve(ok({ rel: 'one.js', content: 'first stale selection', size: 12, hash: 'first' }));
  await firstOpen;
  await settle();
  assert.match(f.get('whViewer').textContent, /second selection/);
  assert.doesNotMatch(f.get('whViewer').textContent, /first stale selection/);
  assert.match(f.get('whViewerTitle').textContent, /two\.js/);
});

test('request drafts restore type, fields, prompt and preview per project', async () => {
  const f = await fixture({ drafts: [
    [PROJECT_A, { text: 'alpha preview', type: 'feature', fields: { goal: 'alpha goal', behavior: 'alpha behavior' }, promptId: 'seed-docs' }],
    [PROJECT_B, { text: 'beta preview', type: 'docs', fields: { topic: 'beta topic' }, promptId: 'seed-review' }],
  ] });
  await f.refresh();
  assert.equal(f.get('whTaskType').value, 'feature');
  assert.equal(f.get('whField-goal').value, 'alpha goal');
  assert.equal(f.get('whPromptSelect').value, 'seed-docs');
  assert.equal(f.get('whPreview').value, 'alpha preview');
  f.get('whField-goal').value = 'alpha edited goal';
  await f.get('whField-goal').emit('input', { bubbles: true });
  f.get('whPreview').value = 'alpha edited preview';
  await f.get('whPreview').emit('input', { bubbles: true });
  await f.refresh();
  assert.equal(f.get('whField-goal').value, 'alpha edited goal');
  f.setWorkspace(PROJECT_B);
  await f.refresh();
  assert.equal(f.get('whTaskType').value, 'docs');
  assert.equal(f.get('whField-topic').value, 'beta topic');
  assert.equal(f.get('whPromptSelect').value, 'seed-review');
  assert.equal(f.get('whPreview').value, 'beta preview');
  f.setWorkspace(PROJECT_A);
  await f.refresh();
  assert.equal(f.get('whTaskType').value, 'feature');
  assert.equal(f.get('whField-goal').value, 'alpha edited goal');
  assert.equal(f.get('whPreview').value, 'alpha edited preview');
});

test('editing a search result uses raw source rather than numbered viewer text', async () => {
  const source = 'function demo() {\n  return 1;\n}\n';
  const f = await fixture({ read: (rel) => Promise.resolve(ok({ rel, content: source, size: source.length, hash: 'source-hash', binary: false, truncated: false })) });
  await f.refresh();
  f.get('whCodeQuery').value = 'return';
  await f.get('whCodeSearch').emit('click');
  await f.get('whCodeResults').querySelector('button').emit('click');
  await settle();
  assert.match(f.get('whViewer').querySelector('.wh-line-hit').textContent, /return 1;/);
  assert.equal(f.get('whEditFile').disabled, false);
  await f.get('whEditFile').emit('click');
  assert.equal(f.get('whEditor').hidden, false);
  assert.equal(f.get('whEditor').value, source);
});

test('truncated and binary previews cannot enable the text editor', async () => {
  const f = await fixture({ read: (rel) => Promise.resolve(ok(rel === 'one.js'
    ? { rel, content: 'partial text', size: 500000, hash: 'partial-hash', binary: false, truncated: true }
    : { rel, content: '', size: 200, hash: 'binary-hash', binary: true, truncated: false })) });
  await f.refresh();
  await f.openFile(0);
  await settle();
  assert.equal(f.get('whEditFile').disabled, true);
  assert.equal(f.get('whSaveFile').disabled, true);
  assert.equal(f.get('whEditor').hidden, true);
  await f.openFile(1);
  await settle();
  assert.equal(f.get('whEditFile').disabled, true);
  assert.equal(f.get('whSaveFile').disabled, true);
  assert.equal(f.get('whEditor').hidden, true);
});

async function editFile(f, content, index = 0) {
  await f.openFile(index);
  await settle();
  await f.get('whEditFile').emit('click');
  f.get('whEditor').value = content;
}

test('Save submits raw content, preimage hash and workspace once while pending', async () => {
  const saving = deferred();
  const f = await fixture({ write: () => saving.promise });
  await f.refresh();
  const content = 'function updated() {\n  return 2;\n}\n';
  await editFile(f, content);
  const firstSave = f.get('whSaveFile').emit('click');
  await f.get('whSaveFile').emit('click');
  assert.equal(f.writeCalls.length, 1);
  assert.deepEqual(f.writeCalls[0], { rel: 'one.js', content, expectedHash: 'abc', expectedWorkspace: PROJECT_A });
  assert.equal(f.get('whSaveFile').disabled, true);
  saving.resolve(ok({ rel: 'one.js', hash: 'written-hash' }));
  await firstSave;
  await settle();
  assert.equal(f.writeCalls.length, 1);
  assert.equal(f.get('whEditor').hidden, true);
});

test('a failed Save preserves the edited content and offers retry', async () => {
  const f = await fixture({ write: async () => { throw new Error('preimage changed'); } });
  await f.refresh();
  await editFile(f, 'unsaved code');
  await f.get('whSaveFile').emit('click');
  assert.equal(f.get('whEditor').hidden, false);
  assert.equal(f.get('whEditor').value, 'unsaved code');
  assert.equal(f.get('whSaveFile').disabled, false);
  assert.equal(f.get('whStatus').dataset.kind, 'error');
  assert.match(f.get('whStatus').textContent, /preimage changed/);
});

test('an old Save reply cannot change the viewer after an external workspace switch', async () => {
  const saving = deferred();
  const f = await fixture({ write: () => saving.promise });
  await f.refresh();
  await editFile(f, 'alpha pending save');
  const pendingSave = f.get('whSaveFile').emit('click');
  f.setWorkspace(PROJECT_B);
  await f.refresh();
  const betaView = f.get('whViewer').textContent;
  const betaTitle = f.get('whViewerTitle').textContent;
  saving.resolve(ok({ rel: 'one.js', hash: 'alpha-written-hash' }));
  await pendingSave;
  await settle();
  assert.equal(f.writeCalls[0].expectedWorkspace, PROJECT_A);
  assert.equal(f.get('whWorkspacePath').textContent, PROJECT_B);
  assert.equal(f.get('whViewer').textContent, betaView);
  assert.equal(f.get('whViewerTitle').textContent, betaTitle);
  assert.equal(f.get('whEditor').hidden, true);
  await f.openFile();
  await settle();
  assert.match(f.get('whViewer').textContent, /beta/);
  assert.doesNotMatch(f.get('whViewer').textContent, /alpha pending save/);
});

test('unsaved edits block file navigation and survive an external A to B to A switch', async () => {
  const f = await fixture();
  await f.refresh();
  await editFile(f, 'alpha local edit');
  const readsBeforeNavigation = f.readCalls.length;
  await f.openFile(1);
  await settle();
  assert.equal(f.readCalls.length, readsBeforeNavigation);
  assert.match(f.get('whViewerTitle').textContent, /one\.js/);
  assert.equal(f.get('whEditor').value, 'alpha local edit');
  assert.equal(f.document.activeElement, f.get('whEditor'));
  f.setWorkspace(PROJECT_B);
  await f.refresh();
  assert.equal(f.get('whEditor').hidden, true);
  f.setWorkspace(PROJECT_A);
  await f.refresh();
  await f.openFile();
  await settle();
  assert.equal(f.get('whEditor').hidden, false);
  assert.equal(f.get('whEditor').value, 'alpha local edit');
  assert.equal(f.get('whSaveFile').disabled, false);
});

test('building context retains the existing request and respects the text budget', async () => {
  const f = await fixture({ read: (rel) => Promise.resolve(ok({ rel, content: 'x'.repeat(50000), size: 50000, hash: 'context-source-hash', binary: false, truncated: false })) });
  await f.refresh();
  const request = 'Fix login while preserving the public API.';
  f.get('whPreview').value = request;
  await f.get('whPreview').emit('input', { bubbles: true });
  f.hub.store.addToBasket(PROJECT_A, { path: 'one.js', size: 50000 });
  await f.get('whBuildContextBtn').emit('click');
  const combined = f.get('whPreview').value;
  assert.ok(combined.startsWith(request));
  assert.ok(combined.length <= 20000, `context exceeded budget: ${combined.length}`);
  assert.match(combined, /one\.js/);
  assert.ok(combined.length > request.length);
  assert.equal(f.hub.store.getDraft(PROJECT_A).text, combined);
  assert.equal(f.readCalls.at(-1).expectedWorkspace, PROJECT_A);
});

test('context from an old workspace cannot replace the new workspace request', async () => {
  const reading = deferred();
  const f = await fixture({ read: () => reading.promise });
  await f.refresh();
  f.get('whPreview').value = 'alpha request';
  await f.get('whPreview').emit('input', { bubbles: true });
  f.hub.store.addToBasket(PROJECT_A, { path: 'one.js' });
  const building = f.get('whBuildContextBtn').emit('click');
  f.setWorkspace(PROJECT_B);
  await f.refresh();
  f.get('whPreview').value = 'beta request';
  await f.get('whPreview').emit('input', { bubbles: true });
  reading.resolve(ok({ rel: 'one.js', content: 'alpha stale context', size: 100, hash: 'alpha-context' }));
  await building;
  assert.equal(f.get('whPreview').value, 'beta request');
  assert.equal(f.hub.store.getDraft(PROJECT_B).text, 'beta request');
});

test('context generation preserves a request edited while files were loading', async () => {
  const reading = deferred();
  const f = await fixture({ read: () => reading.promise });
  await f.refresh();
  f.get('whPreview').value = 'initial request';
  f.hub.store.addToBasket(PROJECT_A, { path: 'one.js' });
  const building = f.get('whBuildContextBtn').emit('click');
  f.get('whPreview').value = 'newer user request';
  await f.get('whPreview').emit('input', { bubbles: true });
  reading.resolve(ok({ rel: 'one.js', content: 'file context', size: 100, hash: 'context' }));
  await building;
  assert.equal(f.get('whPreview').value, 'newer user request');
  assert.equal(f.hub.store.getDraft(PROJECT_A).text, 'newer user request');
});
