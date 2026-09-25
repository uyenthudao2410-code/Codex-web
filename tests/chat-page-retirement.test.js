const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

test('desktop runtime contains no embedded ChatGPT session, page observer, or page consent bridge', () => {
  const desktopSources = [
    'electron/main.js', 'electron/browserPreload.js', 'renderer/browser.html', 'renderer/browser.js',
    'renderer/index.html', 'renderer/app.js', 'renderer/theme-bootstrap.js'
  ].map(read).join('\n');
  for (const forbidden of [
    'persist:chatgpt-session', 'ChatViewController', 'ChatEvaluationJournal', 'chatConversationAccess',
    'clearChatSession', 'chat:clear-session', 'chat:navigate', 'chat:status', 'chat:state', 'chat:download',
    'Page.addScriptToEvaluateOnNewDocument', 'window.fetch =', 'JSON.parse =',
    'MutationObserver', 'data-message-author-role', 'coding-tools-continue-consent',
    'electron_chatgpt_dom', 'chatgpt.com/backend-api'
  ]) {
    assert.equal(desktopSources.includes(forbidden), false, forbidden);
  }
  assert.equal(fs.existsSync(path.join(root, 'electron/chatViewController.js')), false);
  assert.equal(fs.existsSync(path.join(root, 'electron/services/chatEvaluationJournal.js')), false);
  assert.equal(fs.existsSync(path.join(root, 'electron/services/chatConversationAccess.js')), false);
  const localShell = [
    read('renderer/browser.html'), read('renderer/browser.css'), read('renderer/browser.js'),
    read('electron/browserPreload.js'), read('electron/main.js'), read('electron/paths.js')
  ].join('\n');
  for (const obsolete of [
    'agentSidebar', 'agent-sidebar', 'railToggle', 'conversationIndex',
    'syncVisibleConversations', 'setConversationWorkspace', 'setLeftInset',
    'discoverVisibleConversations', 'collapseNativeSidebar', 'conversation:index-changed'
  ]) {
    assert.equal(localShell.includes(obsolete), false, obsolete);
  }
});

test('official ChatGPT handoff is a fixed user click and local task controls remain available', () => {
  const html = read('renderer/browser.html');
  const renderer = read('renderer/browser.js');
  const preload = read('electron/browserPreload.js');
  const main = read('electron/main.js');

  assert.match(html, /id="openChatGPTButton"/);
  assert.match(renderer, /\$\('#openChatGPTButton'\)\.onclick/);
  assert.match(preload, /openChatGPT: \(\) => ipcRenderer\.invoke\('shell:open', 'chatgpt-connectors'\)/);
  assert.match(main, /const allowed = new Set\(\['chatgpt-connectors'/);
  assert.match(main, /'chatgpt-connectors': 'https:\/\/chatgpt\.com\/\#settings\/Connectors'/);
  assert.match(main, /shell\.openExternal\(urls\[target\]\)/);

  for (const control of ['workspace:choose-and-switch', 'task-state:pause', 'task-state:resume', 'task-state:stop']) {
    assert.ok(main.includes(control), `local executor control remains: ${control}`);
  }
  assert.match(html, /id="addWorkspace"/);
  assert.match(html, /id="addAuthorizedRootQuick"/);
  assert.match(renderer, /refreshTask\(true\)/);
});

test('executor overview keeps telemetry unknown and separates route status from action rights', () => {
  const source = read('renderer/browser.js');
  const start = source.indexOf('function renderExecutorSummary() {');
  const end = source.indexOf('\nasync function refreshStatus()', start);
  assert.ok(start >= 0 && end > start);
  const text = new Map([
    ['#executorRuntimeState', ''],
    ['#executorPolicyState', ''],
    ['#executorWorkspaceState', '']
  ]);
  const state = { current: { signalStale: true, telemetryAvailable: false } };
  const context = {
    lastRuntimeState: state.current,
    activeWorkspace: 'C:/workspace',
    $: (selector) => ({ set textContent(value) { text.set(selector, value); } })
  };
  vm.runInNewContext(source.slice(start, end), context);
  vm.runInNewContext('renderExecutorSummary()', context);
  assert.equal(text.get('#executorRuntimeState'), 'Chưa xác minh telemetry runtime');
  assert.equal(text.get('#executorPolicyState'), 'Chưa xác minh quyền theo từng thao tác');

  context.lastRuntimeState = {
    signalStale: false, telemetryAvailable: true, componentsReady: true,
    executionRole: 'central_executor', centralConnected: true, authorityReady: true,
    fullyReady: true
  };
  vm.runInNewContext('renderExecutorSummary()', context);
  assert.equal(text.get('#executorRuntimeState'), 'Các process cục bộ sẵn sàng');
  assert.equal(text.get('#executorPolicyState'), 'Đã kết nối route; quyền và receipt vẫn kiểm tra riêng');
});
