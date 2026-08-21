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
  assert.equal(PANEL_WIDTH, 420);
  assert.equal(PANEL_WIDTH_RATIO, 0.35);
  assert.equal(PANEL_MIN_WIDTH, 360);
  assert.equal(PANEL_MAX_WIDTH, 750);
  assert.equal(panelInset(1360, false), 0);
  assert.equal(panelInset(1360, true), 476);
  assert.equal(panelInset(1920, true), 672);
  assert.equal(panelInset(2560, true), PANEL_MAX_WIDTH);
  assert.equal(panelInset(900, true), 900 - MIN_CHAT_WIDTH);
  assert.equal(panelInset(400, true), 0);
  assert.equal(panelInset(1200, true, { panelWidth: 500, minChatWidth: 600 }), 500);

  const bounds = panelBounds(1360, 900, 112, true);
  assert.deepEqual(bounds, { x: 884, y: 112, width: 476, height: 900 - 112 });
  assert.equal(panelBounds(1360, 900, 112, false), null);

  const chat = chatBounds(1360, 900, 112, true);
  assert.deepEqual(chat, { x: 0, y: 112, width: 884, height: 900 - 112 });
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
  assert.match(main, /secureHandle\('panel:live-control'/);
  assert.match(main, /secureHandle\('panel:orchestration'/);
  assert.match(main, /secureHandle\('panel:handoff'/);
  assert.match(main, /secureHandle\('panel:task-control'/);
  assert.match(main, /secureHandle\('panel:transfer-controller'/);
  assert.match(main, /secureHandle\('panel:copy-codex-config'/);
  assert.match(main, /path: '\/__control\/orchestration\/live'/);
  assert.match(main, /path: '\/__control\/orchestration'/);
  assert.match(main, /const PANEL_ORCHESTRATION_TIMEOUT_MS = 10000;/);
  assert.match(main, /const PANEL_LIVE_CONTROL_TIMEOUT_MS = 2500;/);
  assert.match(main, /timeout: PANEL_ORCHESTRATION_TIMEOUT_MS/);
  assert.match(main, /timeout: PANEL_LIVE_CONTROL_TIMEOUT_MS/);
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
  assert.match(httpHandler, /__control\/orchestration\/live/);
  assert.match(httpHandler, /def control_orchestration_snapshot/);
  assert.match(httpHandler, /live_control_snapshot\(self\.runtime/);
  assert.match(httpHandler, /current_active_run/);
  assert.match(httpHandler, /latest_handoff_capsule/);
  const liveControl = read('resources/coding-tools-mcp/coding_tools_mcp/live_control.py');
  assert.match(liveControl, /def live_control_snapshot/);
  assert.match(liveControl, /"snapshot_scope": "live_control"/);
  assert.match(liveControl, /runtime_activity_snapshot/);
  assert.match(liveControl, /activity_state/);
  assert.doesNotMatch(liveControl, /usage_analytics|operations_analytics|routing_evidence|flight_recorder|export_summary/);
});

test('control panel renders task plus multi-client authority and continuity controls', () => {
  const html = read('renderer/panel.html');
  const tagById = (id) => {
    const match = html.match(new RegExp(`<[^>]+id="${id}"[^>]*>`));
    assert.ok(match, `panel.html thiếu opening tag ${id}`);
    return match[0];
  };
  for (const id of ['taskStatus', 'taskObjective', 'taskBar', 'runStatus', 'waveLine', 'eventList', 'eventCount', 'proofList', 'handoffButton', 'pauseTask', 'resumeTask', 'stopTask', 'refreshButton', 'closeButton', 'syncState', 'continuityStatus', 'toChatWebButton', 'toDesktopButton', 'copyCodexConfigButton', 'runtimeActivitySection', 'runtimeActivitySummary', 'runtimeActivityList']) {
    assert.match(html, new RegExp(`id="${id}"`), `panel.html thiếu id ${id}`);
  }
  assert.doesNotMatch(tagById('mcpDot'), /\bready\b/);
  assert.doesNotMatch(tagById('tunnelDot'), /\bready\b/);
  assert.match(html, /id="taskStatus"[^>]*>Chưa đồng bộ</);
  assert.match(html, /id="taskPercent"[^>]*>—</);
  assert.match(html, /id="runStatus"[^>]*>Chưa đồng bộ</);
  assert.match(html, /id="eventCount"[^>]*>—</);
  assert.match(html, /id="routingEvidenceKpi"[^>]*>Chưa đồng bộ</);
  assert.match(html, /id="continuityStatus"[^>]*>Chưa đồng bộ</);
  assert.match(html, /id="hubStatus"[^>]*>Chưa đồng bộ</);
  assert.match(html, /id="runtimeActivitySummary"[^>]*>Chưa đồng bộ</);
  assert.match(html, /id="syncState"[^>]*>Chưa đồng bộ với control plane</);
  assert.equal((html.match(/● CHƯA ĐỒNG BỘ/g) || []).length, 9, 'mọi router node phải bắt đầu ở trạng thái chưa đồng bộ');
  assert.match(tagById('routerChatWeb'), /class="router-node waiting"/);
  assert.match(tagById('routerDesktop'), /class="router-node waiting"/);
  assert.match(tagById('routerOpenCode'), /class="router-node waiting"/);
  assert.match(tagById('routerHub'), /class="router-node hub waiting"/);
  assert.match(tagById('routerWriter'), /class="router-node writer-authority waiting"/);
  for (const id of ['pauseTask', 'resumeTask', 'stopTask', 'handoffButton', 'toChatWebButton', 'toDesktopButton', 'copyCodexConfigButton']) {
    assert.match(tagById(id), /\bdisabled\b/, `${id} phải fail-closed trước lần sync đầu tiên`);
  }
  assert.doesNotMatch(tagById('refreshButton'), /\bdisabled\b/);
  assert.doesNotMatch(tagById('closeButton'), /\bdisabled\b/);
  assert.match(html, /Operator Control Panel/);
  assert.match(html, /Executive Summary/);
  assert.match(html, /id="truthConsole"/);
  assert.match(html, /id="truthRuntimeMatch"[^>]*data-state="UNKNOWN"/);
  assert.match(html, /id="truthWaveWorktreeMatch"[^>]*data-state="UNKNOWN"/);
  assert.match(html, /class="dashboard-card executive-card hero-summary"/);
  assert.match(html, /class="hero-kpi-grid"/);
  assert.equal((html.match(/class="summary-kpi-card /g) || []).length, 3, 'Executive Summary phải có đúng ba KPI hero cards');
  assert.match(html, /id="taskPercent"/);
  assert.match(html, /id="eventCount"/);
  assert.match(html, /id="hubStatus"/);
  assert.match(html, /Quick Controls/);
  assert.match(html, /<details class="dashboard-card recent-card panel-section secondary-disclosure" id="eventsSection">/);
  assert.match(html, /id="advancedOperations"/);
  const js = read('renderer/panel.js');
  assert.match(js, /refreshOrchestration/);
  assert.match(js, /setInterval\(refreshOrchestration, 2000\)/);
  assert.match(js, /let orchestrationInFlight = null;/);
  assert.match(js, /let orchestrationError = '';/);
  assert.match(js, /let controlPlaneState = 'unknown';/);
  assert.match(js, /const CONTROL_PLANE_ACTION_IDS = \[/);
  assert.match(js, /function renderSyncState\(\)/);
  assert.match(js, /if \(controlPlaneState === 'unavailable'\)/);
  assert.match(js, /CONTROL PLANE UNAVAILABLE/);
  assert.match(js, /Chưa đồng bộ với control plane/);
  assert.match(js, /if \(orchestrationInFlight\) return orchestrationInFlight;/);
  assert.match(js, /orchestrationError = error\?\.message \|\| String\(error\)/);
  assert.match(js, /finally \{[\s\S]*?orchestrationInFlight = null;/);
  assert.match(js, /if \(!orchestrationError && lastSyncAt && Date\.now\(\) - lastSyncAt > 8000\)/);
  const unavailableBlock = js.slice(js.indexOf('function renderControlPlaneUnavailable(error)'), js.indexOf('function renderHealth(health)'));
  assert.ok(unavailableBlock.length > 0, 'panel.js phải có fail-visible invalidation path');
  assert.match(unavailableBlock, /controlPlaneState = 'unavailable';/);
  assert.match(unavailableBlock, /lastOrchestration = null;/);
  assert.match(unavailableBlock, /lastSyncAt = 0;/);
  assert.match(unavailableBlock, /setControlPlaneActionsEnabled\(false\)/);
  assert.match(unavailableBlock, /#eventList/);
  assert.match(unavailableBlock, /#proofList/);
  assert.match(unavailableBlock, /#runtimeActivityList/);
  assert.match(unavailableBlock, /#delegationList/);
  assert.match(unavailableBlock, /● CHƯA ĐỒNG BỘ/);
  const refreshBlock = js.slice(js.indexOf('async function refreshOrchestration'), js.indexOf('async function refreshHealth'));
  assert.match(refreshBlock, /controlPlaneState = 'available';/);
  assert.match(refreshBlock, /lastSyncAt = Date\.now\(\);/);
  assert.match(refreshBlock, /renderControlPlaneUnavailable\(error\);/);
  assert.ok(refreshBlock.indexOf("controlPlaneState = 'available';") < refreshBlock.indexOf('renderTask(data?.task);'), 'authoritative state phải được đánh dấu trước khi render action controls');
  const renderHealthBlock = js.slice(js.indexOf('function renderHealth(health)'), js.indexOf('function renderTask(task)'));
  assert.match(renderHealthBlock, /renderSyncState\(\);/);
  assert.doesNotMatch(renderHealthBlock, /#syncState/);
  const refreshHealthBlock = js.slice(js.indexOf('async function refreshHealth'), js.indexOf('async function taskAction'));
  assert.match(refreshHealthBlock, /lastHealth = null;/);
  assert.match(refreshHealthBlock, /classList\.remove\('ready'\)/);
  assert.ok((js.match(/if \(controlPlaneState !== 'available'\) return;/g) || []).length >= 4, 'mọi action handler phải fail closed khi control plane chưa authoritative');
  assert.match(js, /controllerOwner\.startsWith\('chatweb:'\)/);
  assert.match(js, /recordHandoff/);
  assert.match(js, /renderEvents/);
  assert.match(js, /renderProofs/);
  assert.match(js, /renderHub/);
  assert.match(js, /renderRuntimeActivity/);
  assert.match(js, /renderTruthConsole\(data\?\.truth_snapshot \|\| \{\}\)/);
  assert.match(js, /normalized === 'MATCHED'\) return 'badge status-active'/);
  assert.match(js, /normalized === 'MISMATCHED'\) return 'badge status-hold'/);
  assert.match(js, /normalized === 'NOT_APPLICABLE'\) return 'badge status-neutral'/);
  assert.match(js, /return 'badge status-waiting'/);
  assert.match(js, /runtime_activity/);
  assert.match(js, /activity_state/);
  assert.match(js, /NO_SIGNAL/);
  assert.doesNotMatch(js, /const hubUp = Boolean/);
  assert.match(js, /clientFor\(data, 'opencode', 'opencode'\)/);
  assert.doesNotMatch(js, /renderRouterFabric|routerGeometry|getBoundingClientRect|updateRouterGeometry|scheduleRouterGeometry|requestAnimationFrame|ResizeObserver|routerNodeIds|routerEdgeIds/);
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
  assert.match(preload, /orchestration: \(\) => ipcRenderer\.invoke\('panel:live-control'\)/);
  assert.doesNotMatch(preload, /panel:orchestration/);
  assert.match(preload, /panel:task-control/);
  assert.doesNotMatch(preload, /task-state:pause/);
  assert.doesNotMatch(preload, /task-state:stop/);
  const managerPreload = read('electron/preload.js');
  assert.match(managerPreload, /orchestration: \(\) => ipcRenderer\.invoke\('panel:orchestration'\)/);
  assert.doesNotMatch(managerPreload, /panel:live-control/);
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
