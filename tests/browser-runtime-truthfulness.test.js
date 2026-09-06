'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const read = (relative) => fs.readFileSync(path.join(__dirname, '..', relative), 'utf8');

function createDom(selectors) {
  const elements = new Map();
  for (const selector of selectors) {
    const element = { classes: new Set(), className: '', dataset: {}, disabled: false,
      style: {}, textContent: '', title: '', setAttribute() {} };
    element.classList = {
      add(...names) { names.forEach((name) => element.classes.add(name)); },
      remove(...names) { names.forEach((name) => element.classes.delete(name)); },
      toggle(name, enabled) {
        if (enabled) element.classes.add(name);
        else element.classes.delete(name);
      }
    };
    elements.set(selector, element);
  }
  return { elements, $: (selector) => elements.get(selector) || null };
}

function fragment(relative, startMarker, endMarker, globals) {
  const source = read(relative);
  const start = source.indexOf(startMarker);
  const end = source.indexOf(endMarker, start);
  assert.ok(start >= 0 && end > start, relative + ' fragment bounds');
  const context = vm.createContext(globals);
  vm.runInContext(source.slice(start, end), context, { filename: relative });
  return context;
}

const panelSelectors = [
  '#routerChatWeb', '#routerDesktop', '#routerOpenCode', '#routerHub', '#routerWriter',
  '#routerFast', '#routerDeepSeek', '#routerTerra', '#routerSol',
  '#routerEdgeChatWeb', '#routerEdgeDesktop', '#routerEdgeOpenCode', '#routerEdgeWriter',
  '#routerEdgeFast', '#routerEdgeDeepSeek', '#routerEdgeTerra', '#routerEdgeSol',
  '#routingEvidenceKpi', '#runStatus', '#runObjective', '#waveLine', '#orchCounts',
  '#capsuleLine', '#handoffButton', '#copyCodexConfigButton'
];

test('panel routing requires active delegation evidence, not automatic configuration', () => {
  const { elements, $ } = createDom(panelSelectors);
  const context = fragment('renderer/panel.js', 'function clientActivity(client)',
    'function renderRuntimeActivity', { $, controlPlaneState: 'available' });
  const base = { clients: [], runtime: { process_instance_id: 'proc-1' },
    runtime_activity: { state: 'IDLE' }, authority: { write: { status: 'idle' } },
    provider_traffic: { automatic_routing: { enabled: true } } };
  context.data = { ...base, delegations: [
    { model: 'mini', status: 'active' }, { model: 'luna', status: 'running' },
    { model: 'deepseek', status: 'executing' }, { model: 'terra', status: 'completed' },
    { model: 'sol', status: 'queued' }, { model: 'sol', status: 'blocked' }
  ] };
  vm.runInContext('renderRouting(data)', context);
  for (const key of ['Fast', 'DeepSeek']) assert.equal(elements.get('#router' + key).classes.has('active'), true);
  assert.equal(elements.get('#routerTerra').classes.has('connected'), true);
  assert.equal(elements.get('#routerSol').classes.has('waiting'), true);
  assert.equal(elements.get('#routingEvidenceKpi').textContent, '0/3 active · 0 recent · 3 tuyến chạy');
  for (const status of ['queued', 'blocked', 'unknown', '', 'waiting', 'idle']) {
    context.data = { ...base, delegations: ['mini', 'deepseek', 'terra', 'sol'].map((model) => ({ model, status })) };
    vm.runInContext('renderRouting(data)', context);
    for (const key of ['Fast', 'DeepSeek', 'Terra', 'Sol']) {
      assert.deepEqual([...elements.get('#router' + key).classes], ['waiting']);
    }
    assert.equal(elements.get('#routingEvidenceKpi').textContent, '0/3 active · 0 recent · 0 tuyến chạy');
  }
  context.data = { ...base, delegations: [] };
  vm.runInContext('renderRouting(data)', context);
  for (const key of ['Fast', 'DeepSeek', 'Terra', 'Sol']) assert.deepEqual([...elements.get('#router' + key).classes], ['waiting']);
});

test('panel RUN tone distinguishes active, terminal, failed, and unknown', () => {
  const { elements, $ } = createDom(panelSelectors);
  const context = fragment('renderer/panel.js', 'function renderRun(data)',
    'function clientFor(data, type, id)', { $, controlPlaneState: 'available', renderTruthConsole() {}, shortTime: () => '' });
  const cases = { active: 'active', running: 'active', executing: 'active', accepted: 'neutral',
    completed: 'neutral', failed: 'hold', rejected: 'hold', aborted: 'hold', unknown: 'waiting', idle: 'waiting' };
  for (const [status, tone] of Object.entries(cases)) {
    context.data = { run: { status }, waves: [] };
    vm.runInContext('renderRun(data)', context);
    assert.equal(elements.get('#runStatus').className, 'badge kpi-mini-badge status-' + tone);
  }
});

function actionHarness() {
  const dom = createDom(panelSelectors);
  const state = { alerts: [], transfers: [], clipboardWrites: 0, refreshes: 0,
    confirmed: true, receipt: { copied: true }, handoff: {}, handoffCalls: [] };
  const context = fragment('renderer/panel.js', 'async function recordHandoff', 'function updateClock', {
    $: dom.$, controlPlaneState: 'available', lastOrchestration: { run: { run_id: 'run-123' } },
    window: { confirm: () => state.confirmed },
    navigator: { clipboard: { writeText: () => { state.clipboardWrites += 1; } } },
    unwrap: (result) => { if (!result?.ok) throw new Error('IPC failed'); return result.data; },
    api: {
      handoff: async (payload) => { state.handoffCalls.push(payload); return { ok: true, data: state.handoff }; },
      transferController: async (payload) => { state.transfers.push(payload); return { ok: true, data: {} }; },
      copyCodexConfig: async () => ({ ok: true, data: state.receipt })
    },
    refreshOrchestration: async () => { state.refreshes += 1; },
    renderControlPlaneUnavailable() {}, alert: (message) => state.alerts.push(message)
  });
  return { ...dom, state, context };
}

test('panel transfer sends the IPC object and preserves confirmation/unavailable guards', async () => {
  const { state, context } = actionHarness();
  await vm.runInContext('transferController("codex-desktop")', context);
  assert.deepEqual(JSON.parse(JSON.stringify(state.transfers)), [{ targetClientId: 'codex-desktop', runId: 'run-123' }]);
  assert.equal(state.refreshes, 1);
  state.confirmed = false;
  await vm.runInContext('transferController("chatweb")', context);
  context.controlPlaneState = 'unavailable';
  state.confirmed = true;
  await vm.runInContext('transferController("chatweb")', context);
  assert.equal(state.transfers.length, 1);
});

test('panel config trusts copied receipt without overwriting the actual TOML clipboard', async () => {
  const { state, context } = actionHarness();
  await vm.runInContext('copyCodexConfig()', context);
  assert.match(state.alerts.at(-1), /^Đã sao chép cấu hình MCP/);
  state.receipt = { copied: false };
  await vm.runInContext('copyCodexConfig()', context);
  assert.match(state.alerts.at(-1), /^Lỗi sao chép cấu hình:/);
  assert.equal(state.clipboardWrites, 0);
});

test('panel handoff requires a matching structured capsule and reports its real version', async () => {
  const { state, context, elements } = actionHarness();
  const capsule = { capsule_id: 'cap-1', run_id: 'run-123', version: 7 };
  state.handoff = { structuredContent: { recorded: true, capsule } };
  await vm.runInContext('recordHandoff()', context);
  assert.deepEqual(state.alerts, ['Đã ghi Capsule thành công (v7).']);
  assert.deepEqual(JSON.parse(JSON.stringify(state.handoffCalls)), [{ runId: 'run-123' }]);
  assert.equal(state.refreshes, 1);
  const bad = [ {}, { isError: true, structuredContent: { recorded: true, capsule } },
    { structuredContent: { ok: false, recorded: true, capsule } },
    { structuredContent: { recorded: false, capsule } }, { structuredContent: { recorded: true } },
    ...[{ capsule_id: '  ' }, { run_id: '' }, { run_id: 'run-other' }, { version: 0 }, { version: 7.5 }, { version: '7' }]
      .map((delta) => ({ structuredContent: { recorded: true, capsule: { ...capsule, ...delta } } })) ];
  for (const receipt of bad) {
    state.handoff = receipt;
    state.alerts.length = 0;
    await vm.runInContext('recordHandoff()', context);
    assert.equal(state.refreshes, 1);
    assert.equal(state.alerts.length, 1);
    assert.match(state.alerts[0], /^Lỗi ghi capsule:/);
  }
  assert.equal(elements.get('#handoffButton').disabled, false);
});

test('panel handoff with no selected RUN makes no IPC request', async () => {
  const { state, context, elements } = actionHarness();
  context.lastOrchestration = { run: null };
  await vm.runInContext('recordHandoff()', context);
  assert.equal(state.handoffCalls.length, 0);
  assert.match(state.alerts.at(-1), /^Lỗi ghi capsule:/);
  assert.equal(elements.get('#handoffButton').disabled, true);
});

test('main handoff forwards the selected RUN with Electron identity and rejects missing binding', async () => {
  let handler;
  const calls = [];
  const responseResult = { structuredContent: { recorded: true } };
  fragment('electron/main.js', "  secureHandle('panel:handoff'", "  secureHandle('chat:clear-session'", {
    secureHandle: (_name, callback) => { handler = callback; },
    invokeSafely: async (callback) => {
      try { return { ok: true, data: await callback() }; }
      catch (error) { return { ok: false, error: error.message }; }
    },
    settings: { load: () => ({ mcpPort: 18766 }) },
    secrets: { get: () => 'fixture-only-token' },
    app: { getVersion: () => '1.0.0' },
    httpRequestJson: async (request) => { calls.push(request); return { result: responseResult }; }
  });
  for (const payload of [undefined, {}, { runId: '' }, { runId: ' ' }, { runId: 1 }]) {
    const result = await handler({}, payload);
    assert.equal(result.ok, false);
  }
  assert.equal(calls.length, 0);
  const result = await handler({}, { runId: ' run-123 ', summary: 'continue test' });
  assert.equal(result.ok, true);
  assert.equal(result.data, responseResult);
  assert.equal(calls.length, 1);
  assert.deepEqual(JSON.parse(JSON.stringify(calls[0].body.params.arguments)), {
    action: 'handoff', handoff_action: 'record', run_id: 'run-123',
    payload: { panel_summary: 'continue test' }
  });
  assert.equal(calls[0].headers['X-Coding-Tools-Client-Type'], 'electron');
  assert.equal(calls[0].headers['X-Coding-Tools-Client-Id'], 'electron-panel');
  assert.equal(Object.hasOwn(calls[0].body.params.arguments, 'task_context_id'), false);
});

test('browser health moves fresh to uncertain and back without false green or stopped claims', () => {
  const health = ['#mcpState', '#tunnelState', '#recoveryTunnelState', '#deviceState', '#gitState', '#workspaceHealthButton'];
  const { elements, $ } = createDom([...health, '#deviceStateName', '#gitStateText', '#workspaceHealthName',
    '#workspaceHealthPath', '#workspaceHealthState', '#workspaceHealthTime']);
  const context = fragment('renderer/browser.js', 'function renderServiceState(state)', 'async function refreshStatus', {
    $, activeWorkspace: 'E:\\DEV\\Codex-web', lastRuntimeState: null, lastRuntimeCheckAt: 0,
    baseName: (value) => String(value || '').split(/[\\/]/).pop()
  });
  const fresh = { mcpRunning: true, nativeAlive: true, tunnelRunning: true, telemetryAvailable: true,
    recoveryHost: { recovery_plane: { tunnel: { state: 'healthy' } } },
    device: { display_name: 'Desktop device', device_id: 'device-1', online: true,
      git: { available: true, dirty: false, branch: 'main', head_short: 'abc1234' } } };
  const render = (data) => { context.data = data; vm.runInContext('renderServiceState(data)', context); };
  const expectTone = (tone) => {
    for (const selector of health) assert.deepEqual([...elements.get(selector).classes], [tone], selector);
  };
  const uncertain = [null, { signalStale: true }, { telemetryAvailable: false },
    { ...fresh, recovering: true }, { ...fresh, recoveryDeferred: true }];
  for (const state of uncertain) {
    render(fresh);
    expectTone('ready');
    render(state);
    expectTone('warn');
    assert.equal(elements.get('#workspaceHealthState').textContent, 'Chưa xác nhận telemetry');
    assert.equal(elements.get('#deviceStateName').textContent, 'Desktop device');
    assert.equal(elements.get('#gitStateText').textContent, 'main @ abc1234');
    render({ ...fresh, device: { ...fresh.device, device_id: 'device-2' } });
    expectTone('ready');
    assert.equal(elements.get('#workspaceHealthState').textContent, '✓ Đã đồng bộ');
  }
  for (const mcpRunning of [undefined, null, 'true']) {
    render({ ...fresh, mcpRunning });
    assert.deepEqual([...elements.get('#workspaceHealthButton').classes], ['warn']);
  }
  render({ ...fresh, mcpRunning: false });
  assert.deepEqual([...elements.get('#workspaceHealthButton').classes], ['error']);
  assert.equal(elements.get('#workspaceHealthState').textContent, 'Chờ đồng bộ');
});
