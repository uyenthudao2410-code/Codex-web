const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');
const { panelInset, panelBounds, chatBounds, PANEL_WIDTH, MIN_CHAT_WIDTH } = require('../electron/services/panelLayout');

test('panel layout keeps chat usable and shrinks gracefully on narrow windows', () => {
  assert.equal(panelInset(1360, false), 0);
  assert.equal(panelInset(1360, true), PANEL_WIDTH);
  assert.equal(panelInset(900, true), 900 - MIN_CHAT_WIDTH);
  assert.equal(panelInset(400, true), 0);
  assert.equal(panelInset(1200, true, { panelWidth: 500, minChatWidth: 600 }), 500);

  const bounds = panelBounds(1360, 900, 112, true);
  assert.deepEqual(bounds, { x: 1360 - PANEL_WIDTH, y: 112, width: PANEL_WIDTH, height: 900 - 112 });
  assert.equal(panelBounds(1360, 900, 112, false), null);

  const chat = chatBounds(1360, 900, 112, true);
  assert.deepEqual(chat, { x: 0, y: 112, width: 1360 - PANEL_WIDTH, height: 900 - 112 });
  const chatClosed = chatBounds(1360, 900, 112, false);
  assert.deepEqual(chatClosed, { x: 0, y: 112, width: 1360, height: 900 - 112 });
});

test('chat view can be inset by the control panel without changing the toolbar height', () => {
  const controller = read('electron/chatViewController.js');
  assert.match(controller, /setRightInset/);
  assert.match(controller, /this\.rightInset = 0/);
  assert.match(controller, /width: Math\.max\(0, width - this\.rightInset\)/);
  const main = read('electron/main.js');
  assert.match(main, /toolbarHeight: 112/);
  assert.match(main, /panelInset\(width, panelVisible\)/);
  assert.match(main, /panelBounds\(width, height, TOOLBAR_HEIGHT, panelVisible\)/);
});

test('main process exposes Execution Control Center IPC through MCP control plane', () => {
  const main = read('electron/main.js');
  assert.match(main, /secureHandle\('panel:toggle'/);
  assert.match(main, /secureHandle\('panel:orchestration'/);
  assert.match(main, /secureHandle\('panel:handoff'/);
  assert.match(main, /secureHandle\('panel:task-control'/);
  assert.match(main, /secureHandle\('panel:transfer-controller'/);
  assert.match(main, /secureHandle\('panel:copy-codex-config'/);
  assert.match(main, /__control\/orchestration/);
  assert.match(main, /__control\/hub/);
  assert.match(main, /handoff_action: 'record'/);
  assert.match(main, /X-Coding-Tools-Client-Id': 'electron-panel'/);
  assert.ok((main.match(/X-Coding-Tools-Client-Id': 'electron-panel'/g) || []).length >= 2, 'panel task controls and handoff must both carry electron-panel identity');
  assert.match(main, /panel:visibility/);
});

test('MCP exposes an authorized orchestration snapshot endpoint', () => {
  const server = read('resources/coding-tools-mcp/coding_tools_mcp/server.py');
  assert.match(server, /__control\/orchestration/);
  assert.match(server, /def control_orchestration_snapshot/);
  assert.match(server, /current_active_run/);
  assert.match(server, /latest_handoff_capsule/);
});

test('control panel renders task plus multi-client authority and continuity controls', () => {
  const html = read('renderer/panel.html');
  for (const id of ['taskStatus', 'taskObjective', 'taskBar', 'runStatus', 'waveLine', 'eventList', 'eventCount', 'proofList', 'handoffButton', 'pauseTask', 'resumeTask', 'stopTask', 'refreshButton', 'closeButton', 'syncState', 'chatwebClientStatus', 'desktopClientStatus', 'opencodeClientStatus', 'opencodeCursor', 'controllerLine', 'writeAuthorityLine', 'continuityStatus', 'rotationLine', 'continuityReasons', 'contextPressureLine', 'resumeLine', 'toChatWebButton', 'toDesktopButton', 'copyCodexConfigButton', 'routerFabric', 'routerSummary', 'routerChatWeb', 'routerDesktop', 'routerOpenCode', 'routerHub', 'routerWriter', 'routerFast', 'routerTerra', 'routerSol', 'routerDeepSeek']) {
    assert.match(html, new RegExp(`id="${id}"`), `panel.html thiếu id ${id}`);
  }
  assert.match(html, /Operator Control Panel/);
  assert.match(html, /Executive Summary/);
  assert.match(html, /Alerts &amp; Decisions/);
  assert.match(html, /Capacity &amp; Authority/);
  assert.match(html, /Quick Controls/);
  assert.match(html, /Provider quota \/ billing:[\s\S]*UNKNOWN/);
  assert.match(html, /id="advancedOperations"/);
  const js = read('renderer/panel.js');
  assert.match(js, /refreshOrchestration/);
  assert.match(js, /setInterval\(refreshOrchestration, 2000\)/);
  assert.match(js, /recordHandoff/);
  assert.match(js, /renderEvents/);
  assert.match(js, /renderProofs/);
  assert.match(js, /renderHub/);
  assert.match(js, /renderRouterFabric/);
  assert.match(js, /delegationRouterLane/);
  assert.match(js, /clientFor\(data, 'opencode', 'opencode'\)/);
  assert.match(js, /SAFE TO ROTATE CHATWEB: YES/);
  assert.match(js, /host không expose mức sử dụng/);
  assert.match(js, /window\.confirm/);
  assert.match(js, /transferController\('codex-desktop'\)/);
  assert.doesNotMatch(js, /transferController\('opencode'\)/);
  assert.match(js, /copyCodexConfig/);
  assert.match(js, /document\.hidden/);
  assert.match(js, /visibilitychange/);
  const preload = read('electron/panelPreload.js');
  assert.match(preload, /exposeInMainWorld\('panelAssistant'/);
  for (const method of ['orchestration', 'health', 'pauseTask', 'resumeTask', 'stopTask', 'handoff', 'transferController', 'copyCodexConfig', 'close']) {
    assert.match(preload, new RegExp(`${method}:`));
  }
  assert.match(preload, /panel:task-control/);
  assert.doesNotMatch(preload, /task-state:pause/);
  assert.doesNotMatch(preload, /task-state:stop/);
  const css = read('renderer/panel.css');
  assert.match(css, /\.client-grid/);
  assert.match(css, /\.continuity-callout\.safe/);
  assert.match(css, /\.continuity-callout\.unsafe/);
  assert.match(css, /\.router-fabric/);
  assert.match(css, /\.operator-dashboard/);
  assert.match(css, /\.executive-grid/);
  assert.match(css, /\.quick-control-grid/);
  assert.match(css, /\.advanced-ops/);
  assert.match(css, /body\.is-hidden \.router-edge\.active/);
  assert.match(css, /@keyframes routerFlow/);
  assert.match(css, /prefers-reduced-motion: reduce/);
});

test('browser toolbar offers the control panel toggle', () => {
  const html = read('renderer/browser.html');
  assert.match(html, /panelToggleButton/);
  const browser = read('renderer/browser.js');
  assert.match(browser, /togglePanel/);
  assert.match(browser, /renderPanelVisibility/);
  const preload = read('electron/browserPreload.js');
  assert.match(preload, /togglePanel/);
  assert.match(preload, /onPanelVisibility/);
  const css = read('renderer/browser.css');
  assert.match(css, /manager-button\.active/);
});
