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

test('main process exposes panel IPC for orchestration, handoff and toggle', () => {
  const main = read('electron/main.js');
  assert.match(main, /secureHandle\('panel:toggle'/);
  assert.match(main, /secureHandle\('panel:orchestration'/);
  assert.match(main, /secureHandle\('panel:handoff'/);
  assert.match(main, /__control\/orchestration/);
  assert.match(main, /handoff_action: 'record'/);
  assert.match(main, /panel:visibility/);
});

test('MCP exposes an authorized orchestration snapshot endpoint', () => {
  const server = read('resources/coding-tools-mcp/coding_tools_mcp/server.py');
  assert.match(server, /__control\/orchestration/);
  assert.match(server, /def control_orchestration_snapshot/);
  assert.match(server, /current_active_run/);
  assert.match(server, /latest_handoff_capsule/);
});

test('control panel renders task, orchestration, events, proofs and handoff controls', () => {
  const html = read('renderer/panel.html');
  for (const id of ['taskStatus', 'taskObjective', 'taskBar', 'runStatus', 'waveLine', 'eventList', 'eventCount', 'proofList', 'handoffButton', 'pauseTask', 'resumeTask', 'stopTask', 'refreshButton', 'closeButton', 'syncState']) {
    assert.match(html, new RegExp(`id="${id}"`), `panel.html thiếu id ${id}`);
  }
  const js = read('renderer/panel.js');
  assert.match(js, /refreshOrchestration/);
  assert.match(js, /setInterval\(refreshOrchestration, 2000\)/);
  assert.match(js, /recordHandoff/);
  assert.match(js, /renderEvents/);
  assert.match(js, /renderProofs/);
  const preload = read('electron/panelPreload.js');
  assert.match(preload, /exposeInMainWorld\('panelAssistant'/);
  for (const method of ['orchestration', 'health', 'pauseTask', 'resumeTask', 'stopTask', 'handoff', 'close']) {
    assert.match(preload, new RegExp(`${method}:`));
  }
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
