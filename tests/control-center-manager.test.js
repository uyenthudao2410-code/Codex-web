const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

test('manager primary navigation is operator-first while advanced tools remain reachable from System', () => {
  const html = read('renderer/index.html');
  const nav = html.match(/<nav class="nav-list"[\s\S]*?<\/nav>/)?.[0] || '';
  for (const page of ['overview', 'routing', 'task', 'deploy', 'workspace', 'system']) {
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
  assert.match(html, /data-page-view="system"/);
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
  for (const id of ['ccKpiRuntime', 'ccKpiClients', 'ccKpiRoute', 'ccKpiProof', 'ccTaskStatus', 'ccTaskObjective', 'ccController', 'ccWriter', 'ccContinuity', 'routingDelegations', 'routingEvents', 'routingProofs']) {
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
  assert.match(js, /\['overview', 'routing', 'task'\]\.includes\(activePage\(\)\)/);
});

test('Control Center styling is responsive, accessible to reduced-motion users, and avoids hiding legacy functionality', () => {
  const css = read('renderer/control-center.css');
  assert.match(css, /\.cc-workbench/);
  assert.match(css, /\.ops-router/);
  assert.match(css, /\.system-launch-grid/);
  assert.match(css, /@keyframes ccEdgeFlow/);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(css, /@media \(max-width: 900px\)/);
  assert.match(css, /\.legacy-overview \{ display: none !important; \}/);
});
