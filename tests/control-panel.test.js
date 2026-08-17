const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');
const {
  panelInset,
  panelBounds,
  chatBounds,
  PANEL_WIDTH,
  PANEL_WIDTH_RATIO,
  PANEL_MIN_WIDTH,
  PANEL_MAX_WIDTH,
  MIN_CHAT_WIDTH
} = require('../electron/services/panelLayout');

test('panel layout keeps chat usable and shrinks gracefully on narrow windows', () => {
  assert.equal(PANEL_WIDTH, 510);
  assert.equal(PANEL_WIDTH_RATIO, 0.45);
  assert.equal(PANEL_MIN_WIDTH, PANEL_WIDTH);
  assert.equal(PANEL_MAX_WIDTH, 880);
  assert.equal(panelInset(1360, false), 0);
  assert.equal(panelInset(1360, true), 612);
  assert.equal(panelInset(1920, true), 864);
  assert.equal(panelInset(2560, true), PANEL_MAX_WIDTH);
  assert.equal(panelInset(900, true), 900 - MIN_CHAT_WIDTH);
  assert.equal(panelInset(400, true), 0);
  assert.equal(panelInset(1200, true, { panelWidth: 500, minChatWidth: 600 }), 500);

  const bounds = panelBounds(1360, 900, 112, true);
  assert.deepEqual(bounds, { x: 748, y: 112, width: 612, height: 900 - 112 });
  assert.equal(panelBounds(1360, 900, 112, false), null);

  const chat = chatBounds(1360, 900, 112, true);
  assert.deepEqual(chat, { x: 0, y: 112, width: 748, height: 900 - 112 });
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
  assert.match(main, /const PANEL_ORCHESTRATION_TIMEOUT_MS = 10000;/);
  assert.match(main, /timeout: PANEL_ORCHESTRATION_TIMEOUT_MS/);
  assert.match(main, /__control\/hub/);
  assert.match(main, /handoff_action: 'record'/);
  assert.match(main, /X-Coding-Tools-Client-Id': 'electron-panel'/);
  assert.ok((main.match(/X-Coding-Tools-Client-Id': 'electron-panel'/g) || []).length >= 2, 'panel task controls and handoff must both carry electron-panel identity');
  assert.match(main, /panel:visibility/);
});

test('MCP exposes an authorized orchestration snapshot endpoint', () => {
  // HTTP routing was extracted from server.py into the focused handler module;
  // keep the source assertion on the module that owns the endpoint.
  const httpHandler = read('resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py');
  assert.match(httpHandler, /__control\/orchestration/);
  assert.match(httpHandler, /def control_orchestration_snapshot/);
  assert.match(httpHandler, /current_active_run/);
  assert.match(httpHandler, /latest_handoff_capsule/);
});

test('control panel renders task plus multi-client authority and continuity controls', () => {
  const html = read('renderer/panel.html');
  for (const id of ['taskStatus', 'taskObjective', 'taskBar', 'runStatus', 'waveLine', 'eventList', 'eventCount', 'proofList', 'handoffButton', 'pauseTask', 'resumeTask', 'stopTask', 'refreshButton', 'closeButton', 'syncState', 'continuityStatus', 'toChatWebButton', 'toDesktopButton', 'copyCodexConfigButton', 'routerFabric', 'routerSummary', 'routerChatWeb', 'routerDesktop', 'routerOpenCode', 'routerHub', 'routerWriter', 'routerFast', 'routerTerra', 'routerSol', 'routerDeepSeek']) {
    assert.match(html, new RegExp(`id="${id}"`), `panel.html thiếu id ${id}`);
  }
  assert.match(html, /Operator Control Panel/);
  assert.match(html, /Executive Summary/);
  assert.match(html, /class="dashboard-card executive-card hero-summary"/);
  assert.match(html, /class="hero-kpi-grid"/);
  assert.equal((html.match(/class="summary-kpi-card /g) || []).length, 4, 'Executive Summary phải có đúng bốn KPI hero cards');
  assert.match(html, /id="taskPercent"/);
  assert.match(html, /id="eventCount"/);
  assert.match(html, /id="routerSummary"/);
  assert.match(html, /id="hubStatus"/);
  assert.doesNotMatch(html, /Alerts &amp; Decisions/);
  assert.doesNotMatch(html, /Capacity &amp; Authority/);
  assert.doesNotMatch(html, /id="continuitySection"/);
  assert.doesNotMatch(html, /id="hubSection"/);
  assert.match(html, /Quick Controls/);
  const routingIndex = html.indexOf('id="routerSection"');
  assert.ok(routingIndex > html.indexOf('Executive Summary'), 'Live Routing phải nằm sau phần tóm tắt đầu trang');
  assert.ok(routingIndex < html.indexOf('Quick Controls'), 'Live Routing không được nằm gần cuối panel');
  assert.match(html, /class="dashboard-card router-card panel-section hero-routing"/);
  assert.match(html, /class="router-fabric routing-stage"/);
  assert.match(html, /class="routing-column routing-frontends"/);
  assert.match(html, /class="routing-hub-column"/);
  assert.match(html, /class="routing-column routing-lanes"/);
  assert.match(html, />FRONTENDS</);
  assert.match(html, />EXECUTION HUB</);
  assert.match(html, />COMPUTE LANES</);
  assert.match(html, /Delegated model work/);
  assert.match(html, /MCP Write &amp; Proof/);
  assert.match(html, /single writer · fence/);
  const hubColumn = html.slice(html.indexOf('class="routing-hub-column"'), html.indexOf('class="routing-column routing-lanes"'));
  const laneColumn = html.slice(html.indexOf('class="routing-column routing-lanes"'), html.indexOf('class="router-legend"'));
  assert.match(hubColumn, /id="routerWriter"/, 'MCP writer/proof authority phải nằm cùng control-plane column với Execution Hub');
  assert.doesNotMatch(laneColumn, /id="routerWriter"/, 'MCP writer không được trình bày như một compute/model lane');
  assert.match(html, /id="routingOverlay" class="router-links"/);
  assert.match(html, /<path id="routerEdgeChatWeb"/);
  assert.doesNotMatch(html, /<line id="routerEdge/);
  assert.doesNotMatch(html, /viewBox="0 0 1000 380"/);
  assert.doesNotMatch(html, /d="M245 75/);
  assert.match(html, /class="hub-role">RUNTIME AUTHORITY/);
  assert.match(html, /<details class="dashboard-card recent-card panel-section secondary-disclosure" id="eventsSection">/);
  assert.match(html, /id="advancedOperations"/);
  const js = read('renderer/panel.js');
  assert.match(js, /refreshOrchestration/);
  assert.match(js, /setInterval\(refreshOrchestration, 2000\)/);
  assert.match(js, /let orchestrationInFlight = null;/);
  assert.match(js, /let orchestrationError = '';/);
  assert.match(js, /function renderSyncState\(\)/);
  assert.match(js, /if \(orchestrationError\)/);
  assert.match(js, /if \(orchestrationInFlight\) return orchestrationInFlight;/);
  assert.match(js, /orchestrationError = error\?\.message \|\| String\(error\)/);
  assert.match(js, /finally \{[\s\S]*?orchestrationInFlight = null;/);
  assert.match(js, /if \(!orchestrationError && lastSyncAt && Date\.now\(\) - lastSyncAt > 8000\)/);
  const renderHealthBlock = js.slice(js.indexOf('function renderHealth(health)'), js.indexOf('function renderTask(task)'));
  assert.match(renderHealthBlock, /renderSyncState\(\);/);
  assert.doesNotMatch(renderHealthBlock, /#syncState/);
  assert.match(js, /recordHandoff/);
  assert.match(js, /renderEvents/);
  assert.match(js, /renderProofs/);
  assert.match(js, /renderHub/);
  assert.match(js, /renderRouterFabric/);
  assert.match(js, /const routerGeometry = \{/);
  assert.match(js, /getBoundingClientRect\(\)/);
  assert.match(js, /function updateRouterGeometry\(\)/);
  assert.match(js, /function scheduleRouterGeometry\(\)/);
  assert.match(js, /requestAnimationFrame/);
  assert.match(js, /new ResizeObserver\(scheduleRouterGeometry\)/);
  assert.match(js, /\['routerFabric', \.\.\.Object\.values\(routerNodeIds\)\]\.forEach\(\(id\) => \{/);
  assert.match(js, /routerResizeObserver\.observe\(element\)/);
  assert.match(js, /overlay\.setAttribute\('viewBox'/);
  assert.match(js, /edge\.setAttribute\('d', routerCurve/);
  assert.match(js, /delegationRouterLane/);
  assert.match(js, /className = `router-kpi badge \$\{hubState === 'active'/);
  assert.match(js, /clientFor\(data, 'opencode', 'opencode'\)/);
  assert.doesNotMatch(js, /renderClient\(/);
  assert.doesNotMatch(js, /#controllerLine/);
  assert.doesNotMatch(js, /#rotationLine/);
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
  assert.match(css, /\.hero-summary/);
  assert.match(css, /\.hero-kpi-grid/);
  assert.match(css, /\.summary-kpi-card/);
  assert.match(css, /\.hero-routing/);
  assert.match(css, /\.routing-stage\.router-fabric/);
  assert.match(css, /grid-template-columns:repeat\(4,minmax\(0,1fr\)\)/);
  assert.match(css, /@media \(max-width: 430px\)/);
  assert.match(css, /\.quick-control-grid/);
  assert.match(css, /\.advanced-ops/);
  assert.match(css, /\.advisory-card/);
  assert.match(css, /@keyframes hubBreath/);
  assert.match(css, /@keyframes dashboardEnter/);
  assert.match(css, /@keyframes liveBeacon/);
  assert.match(css, /body\.is-hidden \.router-edge\.active/);
  assert.match(css, /@keyframes routerFlow/);
  assert.match(css, /prefers-reduced-motion: reduce/);
  assert.match(css, /Operator Control Panel v4: readability fix/);
  assert.match(css, /Operator Control Panel v5: balanced type scale and explicit authority topology/);
  assert.match(css, /\.lane-stack \{[\s\S]*?grid-template-rows: repeat\(4, minmax\(0, 1fr\)\);/);
  assert.match(css, /\.routing-stage \.router-node\.writer-authority/);
  assert.match(css, /html, body \{[\s\S]*?font-size: 13px;/);
  assert.match(css, /\.hero-heading h2 \{[\s\S]*?font-size: 16px;/);
  assert.match(css, /\.routing-stage \.router-node\.hub \{[\s\S]*?flex-direction: column;/);
  assert.match(css, /\.routing-stage \.router-node\.hub b \{[\s\S]*?font-size: 14px;[\s\S]*?white-space: nowrap;/);
  const v6 = css.slice(css.indexOf('Operator Control Panel v6:'));
  assert.ok(v6.length > 0, 'panel.css phải có compact/dynamic routing v6 overrides');
  assert.match(v6, /\.hero-summary \{[\s\S]*?min-height: 0;[\s\S]*?padding: 12px 14px !important;/);
  assert.match(v6, /\.summary-kpi-card \{[\s\S]*?min-height: 82px;/);
  assert.match(v6, /\.hero-routing \{ min-height: 500px;/);
  assert.match(v6, /\.routing-stage \.router-links \{[\s\S]*?inset: 0;[\s\S]*?width: 100%;[\s\S]*?height: 100%;/);
  assert.match(v6, /\.routing-hub-column \{[\s\S]*?grid-template-rows: 32px minmax\(0, 1fr\) auto auto 64px;/);
  const v7 = css.slice(css.indexOf('Operator Control Panel v7:'));
  assert.ok(v7.length > 0, 'panel.css phải có final screenshot-fit v7 overrides');
  assert.match(v7, /@media \(min-width: 500px\) \{[\s\S]*?\.hero-kpi-grid \{[\s\S]*?grid-template-columns: repeat\(4, minmax\(0, 1fr\)\);/);
  assert.match(v7, /\.summary-kpi-card \.kpi-copy > span \{[\s\S]*?white-space: nowrap;[\s\S]*?text-overflow: ellipsis;/);
  assert.match(v7, /@media \(max-width: 499px\) \{[\s\S]*?grid-template-columns: repeat\(2, minmax\(0, 1fr\)\);/);
  assert.match(v7, /@media \(max-width: 350px\) \{[\s\S]*?grid-template-columns: 1fr;/);
  const v8 = css.slice(css.indexOf('Operator Control Panel v8:'));
  assert.ok(v8.length > 0, 'panel.css phải có stable source-flow v8 overrides');
  assert.match(v8, /\.operator-dashboard \{[\s\S]*?grid-template-columns: minmax\(0, 1fr\);[\s\S]*?grid-auto-rows: max-content;/);
  assert.match(v8, /\.operator-dashboard > \.hero-summary \{[\s\S]*?height: auto !important;[\s\S]*?overflow: visible;/);
  assert.match(v8, /\.operator-dashboard > \.hero-routing \{[\s\S]*?width: 100%;[\s\S]*?margin: 0;/);
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
