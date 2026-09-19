const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

test('manager primary navigation is operator-first while advanced tools remain reachable from System', () => {
  const html = read('renderer/index.html');
  const nav = html.match(/<nav class="nav-list"[\s\S]*?<\/nav>/)?.[0] || '';
  for (const page of ['overview', 'task', 'device', 'deploy', 'workspace', 'system']) {
    assert.match(nav, new RegExp(`data-page="${page}"`), `missing primary page ${page}`);
  }
  for (const legacy of ['build', 'health', 'guide', 'logs', 'settings']) {
    assert.doesNotMatch(nav, new RegExp(`data-page="${legacy}"`), `${legacy} should not compete in primary navigation`);
    assert.match(html, new RegExp(`data-nav="${legacy}"`), `${legacy} must remain reachable from System`);
    assert.match(html, new RegExp(`data-page-view="${legacy}"`), `${legacy} page must be preserved`);
  }
  assert.match(html, /control-center\.css/);
  assert.match(html, /control-center\.js/);
  assert.doesNotMatch(html, /data-page-view="routing"/);
  assert.doesNotMatch(html, /data-page-view="traffic"/);
  assert.match(html, /data-page-view="system"/);
});

test('manager exposes truthful current-device identity, Git and existing safe runtime controls', () => {
  const html = read('renderer/index.html');
  const app = read('renderer/app.js');
  for (const id of ['topDeviceButton', 'deviceDisplayName', 'deviceId', 'deviceInstanceId', 'deviceWorkspace', 'deviceGitState', 'deviceCodingState', 'deviceRecoveryState', 'deviceCodingTunnelId', 'deviceRecoveryTunnelId', 'deviceRefresh', 'deviceStart', 'deviceRestart', 'deviceStop', 'deviceRepair']) assert.match(html, new RegExp(`id="${id}"`), `missing device UI id ${id}`);
  assert.match(html, /Local only|local-only/i);
  assert.match(app, /renderDevice\(/);
  assert.match(app, /runRuntime\('restart'\)/);
  assert.match(app, /repairHealth\(\)/);
});

test('central executor UI does not require or erase a Windows OpenAI Tunnel profile', () => {
  const html = read('renderer/index.html');
  const app = read('renderer/app.js');
  const preload = read('electron/preload.js');
  const main = read('electron/main.js');
  assert.match(html, /id="centralExecutorNotice"/);
  assert.match(html, /id="centralExecutorHandoff"/);
  assert.match(html, /id="handoffCentralExecutor"/);
  assert.match(html, /không yêu cầu checkpoint nghiệm thu code/);
  assert.match(html, /id="retryCentralExecutorHandoff"/);
  assert.match(html, /id="centralExecutorGuide"/);
  assert.match(html, /id="controlPlaneServerUrl"/);
  assert.match(html, /id="requestControlPlaneEnrollment"/);
  assert.match(html, /id="controlPlaneEnrollmentStatus"/);
  assert.match(html, /id="centralExecutorWorkspaceRegistration"/);
  assert.match(html, /id="chooseControlPlaneWorkspace"/);
  assert.match(html, /id="controlPlaneWorkspaceCandidate"/);
  assert.match(html, /id="registerControlPlaneWorkspace"/);
  assert.match(html, /id="controlPlaneWorkspaceRegistrationStatus"/);
  assert.match(html, /id="refreshControlPlaneWorkspaces"/);
  assert.match(html, /id="controlPlaneWorkspaceRegistrations"/);
  assert.doesNotMatch(html, /id="controlPlaneContextId"/);
  assert.doesNotMatch(html, /id="replaceControlPlanePolicy"/);
  assert.doesNotMatch(html, /id="installControlPlaneReadOnlyPolicy"/);
  assert.match(html, /Quyền task sẽ đến từ liên kết tài khoản/);
  assert.match(html, /Không dán <code>ctx_…<\/code>/);
  assert.match(html, /data-direct-only/);
  assert.match(app, /function isCentralExecutor\(/);
  assert.match(app, /function centralRoutePresentation\(/);
  assert.match(app, /function renderCentralExecutorMode\(/);
  assert.match(app, /Runtime API Key và OpenAI Tunnel chính chỉ thuộc Ubuntu/);
  assert.match(app, /tunnelId: central \? String\(existing\.tunnelId \|\| ''\)/);
  assert.match(app, /recoveryTunnelId: central \? String\(existing\.recoveryTunnelId \|\| ''\)/);
  assert.match(app, /Không cần Runtime API Key hay Tunnel ID tại Windows/);
  assert.match(app, /status\.centralConnected !== true/);
  assert.match(app, /status\.authorityReady !== true/);
  assert.match(app, /function requestControlPlaneEnrollment\(/);
  assert.match(app, /function chooseControlPlaneWorkspace\(/);
  assert.match(app, /function registerControlPlaneWorkspace\(/);
  assert.match(app, /function refreshControlPlaneWorkspaces\(/);
  assert.match(app, /function retireControlPlaneWorkspace\(/);
  assert.match(app, /function renderCentralWorkspaceRegistrations\(/);
  assert.doesNotMatch(app, /function installControlPlaneReadOnlyPolicy\(/);
  assert.match(app, /async function handoffCentralExecutor\(/);
  assert.match(app, /api\.handoffCentralExecutor\(\)/);
  assert.match(app, /chưa xác nhận kết nối Ubuntu/);
  const pickerStart = app.indexOf('async function chooseControlPlaneWorkspace');
  const registrationStart = app.indexOf('async function registerControlPlaneWorkspace');
  const registrationEnd = app.indexOf('async function refreshControlPlaneWorkspaces', registrationStart);
  assert.ok(pickerStart >= 0 && registrationStart > pickerStart && registrationEnd > registrationStart, 'missing bounded central workspace picker');
  const picker = app.slice(pickerStart, registrationStart);
  const registration = app.slice(registrationStart, registrationEnd);
  assert.match(picker, /api\.chooseWorkspace\(\)/);
  assert.match(picker, /state\.centralWorkspaceCandidate/);
  assert.doesNotMatch(picker, /(?:api\.)?switchWorkspace\s*\(/);
  assert.doesNotMatch(picker, /settings\.workspace\s*=/);
  assert.match(registration, /state\.centralWorkspaceCandidate/);
  assert.match(registration, /api\.registerControlPlaneWorkspace\(\{ workspacePath \}\)/);
  assert.doesNotMatch(registration, /(?:api\.)?switchWorkspace\s*\(|settings\.workspace\s*=|state\.selectedWorkspace/);
  assert.match(app, /api\.listControlPlaneWorkspaces\(\)/);
  assert.match(app, /api\.retireControlPlaneWorkspace\(\{/);
  assert.match(app, /Do not call switchWorkspace,[\s\S]*updateAuthorizedRoots/);
  assert.match(app, /account OAuth chọn target và tạo authority riêng/);
  assert.match(preload, /registerControlPlaneWorkspace:\s*\(request\)\s*=>\s*ipcRenderer\.invoke\('control-plane:register-workspace', request\)/);
  assert.match(preload, /listControlPlaneWorkspaces:\s*\(\)\s*=>\s*ipcRenderer\.invoke\('control-plane:list-workspaces'\)/);
  assert.match(preload, /retireControlPlaneWorkspace:\s*\(request\)\s*=>\s*ipcRenderer\.invoke\('control-plane:retire-workspace', request\)/);
  assert.doesNotMatch(preload, /installControlPlaneReadOnlyPolicy/);
  assert.match(main, /secureHandle\('control-plane:register-workspace'/);
  assert.match(main, /secureHandle\('control-plane:list-workspaces'/);
  assert.match(main, /secureHandle\('control-plane:retire-workspace'/);
  assert.match(preload, /requestControlPlaneEnrollment:\s*\(serverUrl\)\s*=>\s*ipcRenderer\.invoke\('control-plane:enroll', serverUrl\)/);
  assert.match(preload, /handoffCentralExecutor:\s*\(\)\s*=>\s*ipcRenderer\.invoke\('runtime:handoff-central-executor'\)/);
  assert.match(main, /secureHandle\('control-plane:enroll'/);
  assert.doesNotMatch(main, /secureHandle\('control-plane:install-read-only-policy'/);
  const handoffStart = main.indexOf("secureHandle('runtime:handoff-central-executor'");
  const handoffEnd = main.indexOf("secureHandle('runtime:start'", handoffStart);
  assert.ok(handoffStart >= 0 && handoffEnd > handoffStart, 'missing bounded central-executor handoff IPC');
  const handoff = main.slice(handoffStart, handoffEnd);
  assert.match(handoff, /assertManagerIpc\(event\)/);
  assert.doesNotMatch(handoff, /fullCleanRestartOptions|activationSourceCheckpoint/);
  assert.match(handoff, /executionRole:\s*'central_executor'/);
  assert.match(handoff, /mode:\s*'full_clean_execution_role_handoff'/);
  assert.doesNotMatch(handoff, /settings\.save|runtimeApiKey|tunnelId/);
  assert.match(main, /assertManagerIpc\(event\)/);
  assert.match(main, /CONTROL_PLANE_ENROLLMENT_ROLE_REQUIRED/);
  assert.doesNotMatch(main, /CONTROL_PLANE_POLICY_ROLE_REQUIRED/);
});

test('manager Command Center exposes the truthful nine-node topology in the overview fabric', () => {
  const html = read('renderer/index.html');
  for (const suffix of ['ChatWeb', 'Desktop', 'OpenCode', 'Fast', 'Hub', 'DeepSeek', 'Terra', 'Writer', 'Sol']) {
    assert.match(html, new RegExp(`id="ccRouter${suffix}"`), `missing cc router node ${suffix}`);
  }
  for (const suffix of ['ChatWeb', 'Desktop', 'OpenCode', 'Fast', 'DeepSeek', 'Terra', 'Writer', 'Sol']) {
    assert.match(html, new RegExp(`id="ccEdge${suffix}"`), `missing cc router edge ${suffix}`);
  }
  assert.match(html, /id="ccRouterSummary"/);
  for (const id of ['ccKpiRuntime', 'ccKpiClients', 'ccKpiRoute', 'ccKpiProof', 'ccTaskStatus', 'ccTaskObjective', 'ccActivityIndicator', 'ccActivityLabel', 'ccActivityDetail', 'ccMotionMode', 'ccController', 'ccWriter', 'ccContinuity', 'ccTrafficPolicy', 'ccTrafficMeta', 'ccRecoveryState', 'ccRecoveryMeta', 'ccContextPressure', 'ccContextMeta']) {
    assert.match(html, new RegExp(`id="${id}"`), `missing Control Center id ${id}`);
  }
});

test('manager preload reuses the existing read-only orchestration IPC without changing MCP contracts', () => {
  const preload = read('electron/preload.js');
  const main = read('electron/main.js');
  assert.match(preload, /orchestration:\s*\(\)\s*=>\s*ipcRenderer\.invoke\('panel:orchestration'\)/);
  assert.match(preload, /dashboardAnalytics:\s*\(\)\s*=>\s*ipcRenderer\.invoke\('panel:dashboard-analytics'\)/);
  assert.match(main, /secureHandle\('panel:orchestration'/);
  assert.match(main, /path:\s*'\/__control\/orchestration'/);
  assert.match(main, /secureHandle\('panel:dashboard-analytics'/);
  assert.match(main, /path:\s*'\/__control\/orchestration\/analytics'/);
  assert.match(main, /const PANEL_ANALYTICS_TIMEOUT_MS = 10000;/);
  const controlCenter = read('renderer/control-center.js');
  assert.match(controlCenter, /coding-tools:overview-pulse/);
  assert.match(controlCenter, /coding-tools:overview-refresh-request/);
  assert.match(controlCenter, /const snapshotRequest = api\.lightweightSnapshot\(\);/);
  assert.match(controlCenter, /const orchestrationRequest = api\.liveOrchestration\(\);/);
  assert.doesNotMatch(controlCenter, /api\.snapshot\(\)/);
  assert.doesNotMatch(controlCenter, /api\.orchestration\(\)/);
});

test('manager captures a bounded real-renderer performance window without payload or ledger telemetry', () => {
  const preload = read('electron/preload.js');
  const main = read('electron/main.js');
  const controlCenter = read('renderer/control-center.js');
  const metrics = read('electron/services/uiPerformanceMetrics.js');
  assert.match(preload, /recordUiPerformance:\s*\(sample\)\s*=>\s*ipcRenderer\.invoke\('ui-performance:record', sample\)/);
  assert.match(preload, /uiPerformance:\s*\(\)\s*=>\s*ipcRenderer\.invoke\('ui-performance:read'\)/);
  assert.match(main, /secureHandle\('ui-performance:record'/);
  assert.match(main, /assertManagerIpc\(event\)/);
  assert.match(controlCenter, /event_loop_lag_samples_ms/);
  assert.match(controlCenter, /ipc_lightweight_snapshot_ms/);
  assert.match(controlCenter, /ipc_live_orchestration_ms/);
  assert.match(controlCenter, /snapshot_apply_ms/);
  assert.match(controlCenter, /paint_commit_ms/);
  assert.match(controlCenter, /coalesced_updates/);
  assert.match(metrics, /MAX_RENDERER_SAMPLES = 180/);
  assert.match(metrics, /PERSIST_INTERVAL_MS = 30_000/);
  assert.doesNotMatch(metrics, /authorization|prompt|command_text|ledger\.sqlite3/);
});

test('manager router treats OpenCode connectivity and DeepSeek model activity as separate evidence', () => {
  const js = read('renderer/control-center.js');
  assert.match(js, /function delegationLane/);
  assert.match(js, /text\.includes\('deepseek'\)/);
  assert.match(js, /const opencodeState = opencode\?\.online \? 'connected' : 'offline'/);
  assert.match(js, /DeepSeek activity requires explicit delegation evidence/);
  assert.doesNotMatch(js, /opencode\?\.online\s*\?\s*'active'/);
  assert.match(js, /api\.lightweightSnapshot\(\)/);
  assert.match(js, /api\.liveOrchestration\(\)/);
  assert.match(js, /const snapshotRequest = api\.lightweightSnapshot\(\);/);
  assert.match(js, /const orchestrationRequest = api\.liveOrchestration\(\);/);
  assert.match(js, /setTimeout\(pollControlCenter, controlCenterPollDelay\(\)\)/);
  assert.doesNotMatch(js, /setInterval\(\(\) => refresh\(false\), 2500\)/);
  assert.match(js, /\['overview', 'task'\]\.includes\(activePage\(\)\)/);
});

test('Command Center overview keeps bounded provider admission evidence without a dedicated traffic page', () => {
  const html = read('renderer/index.html');
  const js = read('renderer/control-center.js');
  const app = read('renderer/app.js');
  assert.match(html, /id="ccTrafficPolicy"/);
  assert.match(html, /id="ccTrafficMeta"/);
  assert.doesNotMatch(html, /id="trafficActive"|id="trafficRoutes"|id="trafficUsageEvents"/);
  assert.doesNotMatch(app, /traffic:\s*\[/);
  assert.match(js, /function renderProviderTraffic/);
  assert.match(js, /data\?\.provider_traffic/);
  assert.match(js, /setText\('ccTrafficPolicy'/);
  assert.match(js, /setText\('ccTrafficMeta'/);
  assert.match(js, /automatic_routing/);
  assert.match(js, /Provider quota is not configured; observe-only, no limit is invented/);
  assert.match(js, /Limits unknown/);
  assert.doesNotMatch(js, /renderTrafficUsage|normalizedUsageEvent|measurementLabel/);
  assert.doesNotMatch(js, /quota\s*=\s*100|remaining\s*=\s*100/);
});

test('Live Execution Fabric uses semantic SVG paths and injects directional particles only for active execution evidence', () => {
  const html = read('renderer/index.html');
  const js = read('renderer/control-center.js');
  const css = read('renderer/control-center.css');
  assert.match(html, /<path id="ccEdgeFast"/);
  assert.doesNotMatch(html, /id="routingEdgeSol"/);
  assert.doesNotMatch(html, /<line id="(?:cc|routing)Edge/);
  assert.match(html, /ops-router-edge-halo/);
  assert.match(js, /function syncEdgeParticles/);
  assert.match(js, /createElementNS\(SVG_NS, 'animateMotion'\)/);
  assert.match(js, /createElementNS\(SVG_NS, 'mpath'\)/);
  assert.match(js, /\['streaming', 'responding'\]\.includes\(status\) \? 'reverse' : 'forward'/);
  assert.match(js, /view\.activity\.rawState === 'PROVING'/);
  assert.match(js, /Frontend connectivity\/controller ownership does not prove a provider call/);
  assert.match(js, /document\.visibilityState === 'hidden'/);
  assert.match(css, /\.ops-router-particle/);
  assert.match(css, /\.ops-router-edge-group\.is-active \.ops-router-edge-halo/);
  assert.doesNotMatch(css, /@keyframes ccEdgeFlow/);
});

test('Control Center projects durable orchestration phases into visible activity state without fabricating model streaming', () => {
  const js = read('renderer/control-center.js');
  assert.match(js, /function executionActivity/);
  assert.match(js, /resume_packet\?\.orchestration_state/);
  assert.match(js, /PREFLIGHT:\s*\{\s*phase:\s*'thinking'/);
  assert.match(js, /ROUTED:\s*\{\s*phase:\s*'dispatching'/);
  assert.match(js, /EXECUTING:\s*\{\s*phase:\s*'executing'/);
  assert.match(js, /PROVING:\s*\{\s*phase:\s*'proving'/);
  assert.match(js, /ACCEPTING:\s*\{\s*phase:\s*'awaiting_acceptance'.*busy:\s*false/);
  assert.match(js, /REPLAN:\s*\{\s*phase:\s*'replanning'/);
  assert.match(js, /\['streaming', 'responding'\]\.includes\(delegationStatus\)/);
  assert.match(js, /fabric\.dataset\.phase = view\.activity\.phase/);
  assert.match(js, /ccActivityIndicator/);
  assert.match(js, /setAttribute\('aria-busy'/);
  assert.match(js, /matchMedia\?\.\('\(prefers-reduced-motion: reduce\)'\)/);
});

test('Control Center styling is responsive, accessible to reduced-motion users, and avoids hiding legacy functionality', () => {
  const css = read('renderer/control-center.css');
  assert.match(css, /\.cc-workbench/);
  assert.match(css, /\.ops-router/);
  assert.match(css, /\.system-launch-grid/);
  assert.match(css, /\.cc-activity/);
  assert.match(css, /\.ops-router-edge-halo/);
  assert.match(css, /\.ops-router-particle/);
  assert.match(css, /@keyframes ccThinkingDot/);
  assert.match(css, /@keyframes ccActivitySweep/);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(css, /@media \(max-width: 900px\)/);
  assert.match(css, /\.legacy-overview \{ display: none !important; \}/);
});

test('Control Center renders provider admission, bounded flight recorder, history and recovery without inventing quota or context pressure', () => {
  const js = read('renderer/control-center.js');
  assert.match(js, /function renderProviderTraffic/);
  assert.match(js, /provider_traffic/);
  assert.match(js, /automatic_routing/);
  assert.match(js, /Provider quota is not configured; observe-only, no limit is invented/);
  assert.match(js, /function renderRecovery/);
  assert.match(js, /context_pressure/);
  assert.match(js, /host_not_exposed/);
  assert.match(js, /does not expose conversation context pressure; UI does not estimate a percentage/);
  assert.doesNotMatch(js, /contextPercent|context_percentage|estimatedContextPressure/);
});

test('Control Center reports the direct MCP tool contract and measured usage receipts without analytics inference', () => {
  const js = read('renderer/control-center.js');
  assert.match(js, /data\?\.runtime\?\.tools/);
  assert.match(js, /data\?\.direct_usage/);
  assert.match(js, /data\?\.tool_call_metering/);
  assert.match(js, /Tool-card tokens — · client receipt unavailable/);
  assert.match(js, /MCP tools/);
  assert.match(js, /input_total_tokens/);
  assert.match(js, /input_cached_tokens/);
  assert.match(js, /output_total_tokens/);
  assert.match(js, /output_reasoning_tokens/);
  assert.match(js, /unknown_not_zero/);
  assert.match(js, /missing=unknown/);
  assert.doesNotMatch(js, /usage_analytics/);
});


test('Tasks & Proof exposes only the authenticated P5-A0 shadow operator path without treatment controls or raw seed material', () => {
  const html = read('renderer/index.html');
  const preload = read('electron/preload.js');
  const main = read('electron/main.js');
  const p5 = read('renderer/p5-a0.js');

  for (const id of ['p5A0Card', 'p5A0Refresh', 'p5A0Prepare', 'p5A0Open', 'p5A0Analyze', 'p5A0Pause', 'p5A0Resume', 'p5A0Close', 'p5A0HardStop']) {
    assert.match(html, new RegExp('id="' + id + '"'), 'missing P5-A0 operator control ' + id);
  }
  assert.match(html, /p5-a0\.js/);
  assert.match(html, /P5-A0 SHADOW A\/A/);
  assert.match(html, /không có treatment hoặc auto-promotion/i);
  assert.match(preload, /p5A0:\s*\(action\)\s*=>\s*ipcRenderer\.invoke\('p5-a0:control', action\)/);
  assert.match(main, /secureHandle\('p5-a0:control'/);
  assert.match(main, /arguments:\s*\{\s*action:\s*'p5',\s*p5_experiment:\s*p5Experiment\s*\}/);
  assert.match(main, /operation:\s*'prepare_a0'/);
  assert.ok(main.includes("const P5_A0_SEED_HANDLE = 'secret://experiment/p5/a';"));
  assert.match(main, /new Set\(\['status', 'prepare', 'open', 'analyze', 'pause', 'resume', 'close', 'hard_stop'\]\)/);
  assert.doesNotMatch(main, /panelP5A0Control\([^)]*treatment|allowed[^\n]*treatment/i);
  assert.match(p5, /api\?\.p5A0/);
  assert.doesNotMatch(p5, /fixture-seed|raw[_ -]?seed|seed_material/i);
  assert.doesNotMatch(html, /id="[^"]*P5[^"]*Treatment|>\s*P5-A Treatment\s*</i);
});
