const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

test('manager primary navigation is operator-first while advanced tools remain reachable from System', () => {
  const html = read('renderer/index.html');
  const nav = html.match(/<nav class="nav-list"[\s\S]*?<\/nav>/)?.[0] || '';
  for (const page of ['overview', 'routing', 'traffic', 'task', 'device', 'deploy', 'workspace', 'system']) {
    assert.match(nav, new RegExp(`data-page="${page}"`), `missing primary page ${page}`);
  }
  for (const legacy of ['build', 'health', 'guide', 'logs', 'settings']) {
    assert.doesNotMatch(nav, new RegExp(`data-page="${legacy}"`), `${legacy} should not compete in primary navigation`);
    assert.match(html, new RegExp(`data-nav="${legacy}"`), `${legacy} must remain reachable from System`);
    assert.match(html, new RegExp(`data-page-view="${legacy}"`), `${legacy} page must be preserved`);
  }
  assert.match(html, /control-center\.css/);
  assert.match(html, /control-center\.js/);
  assert.match(html, /data-page-view="routing"/);
  assert.match(html, /data-page-view="traffic"/);
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

test('manager Command Center and Live Routing expose the truthful nine-node topology', () => {
  const html = read('renderer/index.html');
  for (const prefix of ['cc', 'routing']) {
    for (const suffix of ['ChatWeb', 'Desktop', 'OpenCode', 'Fast', 'Hub', 'DeepSeek', 'Terra', 'Writer', 'Sol']) {
      assert.match(html, new RegExp(`id="${prefix}Router${suffix}"`), `missing ${prefix} router node ${suffix}`);
    }
    for (const suffix of ['ChatWeb', 'Desktop', 'OpenCode', 'Fast', 'DeepSeek', 'Terra', 'Writer', 'Sol']) {
      assert.match(html, new RegExp(`id="${prefix}Edge${suffix}"`), `missing ${prefix} router edge ${suffix}`);
    }
    assert.match(html, new RegExp(`id="${prefix}RouterSummary"`));
  }
  for (const id of ['ccKpiRuntime', 'ccKpiClients', 'ccKpiRoute', 'ccKpiProof', 'ccTaskStatus', 'ccTaskObjective', 'ccActivityIndicator', 'ccActivityLabel', 'ccActivityDetail', 'ccMotionMode', 'ccController', 'ccWriter', 'ccContinuity', 'ccTrafficPolicy', 'ccTrafficMeta', 'ccRecoveryState', 'ccRecoveryMeta', 'ccContextPressure', 'ccContextMeta', 'routingDelegations', 'routingEvents', 'routingProofs', 'routingProviderTraffic', 'routingPhaseTiming', 'routingRunHistory', 'routingRecoveryState', 'routingRecoveryMeta', 'routingContextPressure']) {
    assert.match(html, new RegExp(`id="${id}"`), `missing Control Center id ${id}`);
  }
});

test('manager preload reuses the existing read-only orchestration IPC without changing MCP contracts', () => {
  const preload = read('electron/preload.js');
  const main = read('electron/main.js');
  assert.match(preload, /orchestration:\s*\(\)\s*=>\s*ipcRenderer\.invoke\('panel:orchestration'\)/);
  assert.match(main, /secureHandle\('panel:orchestration'/);
  assert.match(main, /path:\s*'\/__control\/orchestration'/);
});

test('manager router treats OpenCode connectivity and DeepSeek model activity as separate evidence', () => {
  const js = read('renderer/control-center.js');
  assert.match(js, /function delegationLane/);
  assert.match(js, /text\.includes\('deepseek'\)/);
  assert.match(js, /const opencodeState = opencode\?\.online \? 'connected' : 'offline'/);
  assert.match(js, /DeepSeek activity requires explicit delegation evidence/);
  assert.doesNotMatch(js, /opencode\?\.online\s*\?\s*'active'/);
  assert.match(js, /setInterval\(\(\) => refresh\(false\), 2500\)/);
  assert.match(js, /\['overview', 'routing', 'traffic', 'task'\]\.includes\(activePage\(\)\)/);
});

test('Traffic & Usage reuses bounded Execution Hub read models and keeps unknown quota explicit', () => {
  const html = read('renderer/index.html');
  const js = read('renderer/control-center.js');
  const app = read('renderer/app.js');
  for (const id of ['trafficLastSync', 'trafficRefreshButton', 'trafficActive', 'trafficQueued', 'trafficUsage', 'trafficLimits', 'trafficRoutes', 'trafficUsageEvents', 'trafficCapacity', 'trafficEvidence']) {
    assert.match(html, new RegExp(`id="${id}"`), `missing Traffic & Usage id ${id}`);
  }
  assert.match(app, /traffic:\s*\['TRAFFIC & USAGE'/);
  assert.match(js, /function renderTrafficUsage/);
  assert.match(js, /data\?\.provider_traffic/);
  assert.match(js, /data\?\.usage_events/);
  assert.match(js, /function measurementLabel/);
  assert.match(js, /Provider tokens and MCP model-visible bytes are never added together/);
  assert.match(js, /quota UNKNOWN/);
  assert.match(js, /zero is not assumed/);
  assert.doesNotMatch(js, /quota\s*=\s*100|remaining\s*=\s*100/);
});

test('Live Execution Fabric uses semantic SVG paths and injects directional particles only for active execution evidence', () => {
  const html = read('renderer/index.html');
  const js = read('renderer/control-center.js');
  const css = read('renderer/control-center.css');
  assert.match(html, /<path id="ccEdgeFast"/);
  assert.match(html, /<path id="routingEdgeSol"/);
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
  assert.match(js, /flight_recorder\?\.phase_timing/);
  assert.match(js, /history\?\.runs/);
  assert.match(js, /transcript excluded/);
  assert.match(js, /function renderRecovery/);
  assert.match(js, /context_pressure/);
  assert.match(js, /host_not_exposed/);
  assert.match(js, /does not expose conversation context pressure; UI does not estimate a percentage/);
  assert.doesNotMatch(js, /contextPercent|context_percentage|estimatedContextPressure/);
});
