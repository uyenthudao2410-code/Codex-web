const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Exercise the actual renderer closure and registered UI listeners without
// starting the initial analytics request. No production exports are required.
function dashboard() {
  const elements = new Map();
  const frames = new Map();
  const listeners = new Map();
  let nextFrame = 1;
  const createElement = () => ({
    textContent: '', dataset: {}, style: { setProperty(name, value) { this[name] = value; } }, children: [],
    classList: { add() {}, remove() {}, toggle() {} },
    setAttribute() {},
    closest() { return null; },
    append(...nodes) { this.children.push(...nodes); },
    appendChild(node) { this.children.push(node); },
    replaceChildren(...nodes) { this.children = nodes; }
  });
  const context = vm.createContext({
    window: { mcpAssistant: { dashboardAnalytics: async () => ({ ok: false }) } },
    document: {
      getElementById: (id) => elements.get(id) || null,
      querySelector: () => null,
      createElement,
      createElementNS: createElement,
      addEventListener(type, listener) {
        if (!listeners.has(type)) listeners.set(type, []);
        listeners.get(type).push(listener);
      },
      dispatchEvent(event) {
        return Promise.all((listeners.get(event.type) || []).map((listener) => listener(event)));
      }
    },
    performance: { now: () => 0 },
    requestAnimationFrame(callback) { const id = nextFrame++; frames.set(id, callback); return id; },
    cancelAnimationFrame(id) { frames.delete(id); }
  });
  const source = fs.readFileSync(path.join(__dirname, '..', 'renderer', 'dashboard.js'), 'utf8');
  const boundary = source.indexOf('  reducedMotion = window.matchMedia');
  assert.ok(boundary > 0);
  vm.runInContext(`${source.slice(0, boundary)}
    reducedMotion = true;
    globalThis.driver = {
      observedNumber, canonicalMeasuredUsage, canonicalControllerUsageState,
      controllerTokenEstimateState, turnTokenState, renderTokenOverviewTiles,
      renderChatTurnCard, renderLiveTurnCard, renderTurnLog, renderDonut, renderAll,
      toolCallTokenState, renderToolCallTokens,
      snapshotFreshnessLabel, realtimeAgeLabel, rollingProviderUsage, updateRealtimeMetrics, canonicalHourBuckets,
      animateText, compact, setText, applyOverviewPulse,
      setAnalytics(value) { analyticsSnapshot = value; },
      setSnapshot(value) { snapshot = value; },
      setReducedMotion(value) { reducedMotion = value; }
    };
  })();`, context, { filename: 'renderer/dashboard.js' });
  return {
    ...context.driver,
    dispatchOverviewPulse(detail) {
      assert.equal(listeners.get('coding-tools:overview-pulse')?.length, 1);
      return context.document.dispatchEvent({ type: 'coding-tools:overview-pulse', detail });
    },
    element(id) {
      if (!elements.has(id)) elements.set(id, createElement());
      return elements.get(id);
    },
    frames
  };
}

const usageEnvelope = (usage = {}, cost = {}, byModel) => {
  const usageAnalytics = {
    measurement: 'canonical_non_overlapping', missing_measurement_policy: 'unknown_not_zero',
    overall: { event_count: 1, usage: { input_total_tokens: 0, output_total_tokens: 0, total_tokens: 0, ...usage }, cost }
  };
  if (byModel !== undefined) usageAnalytics.by_model = byModel;
  return { usage_analytics: usageAnalytics };
};

const turnSection = (latest = { kind: 'exact', point: 120 }) => ({
  measurement: 'chat_turn_measurements_v1', missing_measurement_policy: 'unknown_not_zero', content_free: true,
  turns_total: 1, turns_exact: 1, latest_turn: latest, session_total: { point: 120 }
});

test('numeric evidence accepts measured zero and rejects coercible non-metrics', () => {
  const d = dashboard();
  for (const value of [null, undefined, true, false, '', ' \t\n', [], [0], {}, { valueOf: () => 2 }, NaN, Infinity, -1, '-2', 'garbage']) {
    assert.equal(d.observedNumber(value), null, `must reject ${String(value)}`);
  }
  for (const value of [0, '0', ' 0 ', 1.5, '12']) assert.equal(d.observedNumber(value), Number(value));
});

test('canonical usage retains measured zero while missing cache, reasoning, and cost stay unknown', () => {
  const d = dashboard();
  d.setAnalytics(usageEnvelope());
  let measured = d.canonicalMeasuredUsage();
  assert.equal(measured.total, 0);
  assert.equal(measured.cached, null);
  assert.equal(measured.reasoning, null);
  assert.equal(measured.cost, null);
  assert.equal(measured.costSource, 'unobserved');
  for (const id of ['daTokensTotal', 'daTokensInTotal', 'daTokensOutTotal', 'daEfficiencyTotal', 'daCostTotal']) d.element(id);
  d.renderTokenOverviewTiles(measured, null, null);
  assert.equal(d.element('daTokensTotal').textContent, '0');
  assert.equal(d.element('daEfficiencyTotal').textContent, '—');
  assert.match(d.element('daCostTotal').textContent, /^[-—]$/);

  d.setAnalytics(usageEnvelope({ input_cached_tokens: 0, output_reasoning_tokens: 0 }, { measured_event_count: 1, measured_usd: 0 }));
  measured = d.canonicalMeasuredUsage();
  d.renderTokenOverviewTiles(measured, null, null);
  assert.equal(measured.costSource, 'provider_reported');
  assert.equal(d.element('daEfficiencyTotal').textContent, '0');
  assert.equal(d.element('daCostTotal').textContent, '$0.000');

  for (const value of [true, ' ', null, 'bad']) {
    d.setAnalytics(usageEnvelope({ total_tokens: value }));
    assert.equal(d.canonicalMeasuredUsage(), null);
  }
});

test('malformed controller and turn projections cannot acquire zero-valued evidence', () => {
  const d = dashboard();
  const data = usageEnvelope();
  data.usage_analytics.controller_usage = { status: 'unobserved', event_count: false, missing_measurement_policy: 'unknown_not_zero' };
  d.setAnalytics(data);
  assert.equal(d.canonicalControllerUsageState(), null);
  data.usage_analytics.controller_usage.event_count = 0;
  assert.equal(d.canonicalControllerUsageState().eventCount, 0);

  const operations = { controller_token_estimate: {
    missing_measurement_policy: 'unknown_not_zero', status: 'context_estimate', measurement: 'CONTEXT_ESTIMATE',
    calibration_samples: false, missing_exact_runs: ' ',
    estimate: { p10_context_tokens: false, p50_context_tokens: ' ', p90_context_tokens: 500 }
  } };
  const estimate = d.controllerTokenEstimateState(operations);
  assert.equal(estimate.p10, null);
  assert.equal(estimate.p50, null);
  assert.equal(estimate.calibrationSamples, null);
  d.element('daControllerTokenStatus');
  d.renderTokenOverviewTiles(null, operations, null);
  assert.doesNotMatch(d.element('daControllerTokenStatus').textContent, /≈0/);

  const section = turnSection({ kind: 'exact', point: ' ' });
  section.session_total.point = false;
  const state = d.turnTokenState({ turn_token_measurements: section });
  assert.equal(state.latestPoint, null);
  assert.equal(state.sessionPoint, null);
  section.turns_total = true;
  assert.equal(d.turnTokenState({ turn_token_measurements: section }), null);
});

test('malformed hourly rows disable the trend instead of becoming zero-valued gaps', () => {
  const d = dashboard();
  const data = usageEnvelope();
  const row = { hour: new Date().toISOString(), event_count: 1, usage: { input_total_tokens: 10, output_total_tokens: 0, total_tokens: 10 } };
  data.usage_analytics.hourly = [row];
  d.setAnalytics(data);
  assert.ok(d.canonicalHourBuckets(d.canonicalMeasuredUsage(), 1));
  row.usage.input_total_tokens = false;
  assert.equal(d.canonicalHourBuckets(d.canonicalMeasuredUsage(), 1), null);
  delete data.usage_analytics.hourly;
  assert.equal(d.canonicalHourBuckets(d.canonicalMeasuredUsage(), 1), null);
});

test('model breakdown preserves known tokens without turning missing coverage into measured zero', () => {
  const d = dashboard();
  for (const id of ['daDonut', 'daLegend', 'daDonutTotal', 'daDonutSub', 'daDonutFoot']) d.element(id);
  const overallTen = { input_total_tokens: 10, output_total_tokens: 0, total_tokens: 10 };
  const render = (data) => {
    d.setAnalytics(data);
    d.renderAll();
    return d.canonicalMeasuredUsage();
  };

  for (const cachedValue of [undefined, false]) {
    const rowUsage = { input_total_tokens: 10, output_total_tokens: 0 };
    if (cachedValue !== undefined) rowUsage.input_cached_tokens = cachedValue;
    const measured = render(usageEnvelope(overallTen, {}, [{
      model: 'gpt-5.6-sol', event_count: 1, usage: rowUsage
    }]));
    assert.equal(measured.byModelStatus, 'complete');
    assert.equal(measured.byModelCachedComplete, false);
    assert.equal(measured.byModel.length, 1);
    assert.equal(measured.byModel[0].inTokens, 10);
    assert.equal(measured.byModel[0].outTokens, 0);
    assert.equal(measured.byModel[0].cachedTokens, null);
    assert.match(measured.byModel[0].usageEvidence, /PARTIAL/);
    assert.equal(d.element('daDonutTotal').textContent, '10');
    assert.match(d.element('daDonutSub').textContent, /CACHED PARTIAL/);
  }

  let measured = render(usageEnvelope(overallTen));
  assert.equal(measured.byModelStatus, 'unavailable');
  assert.equal(measured.byModel.length, 0);
  assert.equal(d.element('daDonutTotal').textContent, '—');
  assert.match(d.element('daDonutSub').textContent, /UNAVAILABLE/);
  assert.match(d.element('daLegend').children[0].textContent, /chưa khả dụng/);

  for (const row of [
    { model: 'gpt-5.6-sol', event_count: 2, usage: { input_total_tokens: 10, output_total_tokens: 0, input_cached_tokens: 0 } },
    { model: 'gpt-5.6-sol', event_count: 1, usage: { input_total_tokens: 5, output_total_tokens: 0, input_cached_tokens: 0 } },
    { model: 'gpt-5.6-sol', event_count: 1, usage: { input_total_tokens: 10, output_total_tokens: 5, input_cached_tokens: 0 } }
  ]) {
    measured = render(usageEnvelope(overallTen, {}, [row]));
    assert.equal(measured.byModelStatus, 'partial');
    assert.equal(measured.byModel.length, 1);
    assert.equal(d.element('daDonutTotal').textContent, '—');
    assert.match(d.element('daDonutSub').textContent, /PARTIAL/);
    assert.doesNotMatch(d.element('daLegend').children[1].children[2].textContent, /%/);
  }

  measured = render(usageEnvelope(overallTen, {}, [
    { model: 'gpt-5.6-sol', event_count: 1, usage: { input_total_tokens: 5, output_total_tokens: 0, input_cached_tokens: 0 } },
    { model: 'gpt-5.6-luna', event_count: 1, usage: { input_total_tokens: false, output_total_tokens: 5, input_cached_tokens: 0 } }
  ]));
  assert.equal(measured.byModelStatus, 'partial');
  assert.equal(measured.byModel.length, 1);
  assert.equal(measured.byModel[0].inTokens, 5);
  assert.equal(d.element('daDonutTotal').textContent, '—');
  assert.match(d.element('daDonutSub').textContent, /PARTIAL/);
  assert.equal(d.element('daLegend').children[1].children[2].textContent, '5 đã quan sát');

  measured = render(usageEnvelope({ input_cached_tokens: 0 }, {}, [{
    model: 'gpt-5.6-sol', event_count: 1,
    usage: { input_total_tokens: 0, output_total_tokens: 0, input_cached_tokens: 0 }
  }]));
  assert.equal(measured.byModelStatus, 'complete');
  assert.equal(measured.byModelCachedComplete, true);
  assert.equal(d.element('daDonutTotal').textContent, '0');
  assert.equal(d.element('daDonutSub').textContent, 'TOKEN MEASURED');
  assert.match(d.element('daLegend').children[0].textContent, /tổng token = 0/);
});

test('missing model breakdown clears an in-flight donut total without animation overwrite', () => {
  const d = dashboard();
  for (const id of ['daDonut', 'daLegend', 'daDonutTotal', 'daDonutSub', 'daDonutFoot']) d.element(id);
  d.setReducedMotion(false);
  d.setAnalytics(usageEnvelope(
    { input_total_tokens: 10, output_total_tokens: 0, total_tokens: 10 }, {},
    [{ model: 'gpt-5.6-sol', event_count: 1, usage: { input_total_tokens: 10, output_total_tokens: 0, input_cached_tokens: 0 } }]
  ));
  d.renderAll();
  assert.equal(d.frames.size, 1);

  d.setAnalytics(usageEnvelope({ input_total_tokens: 10, output_total_tokens: 0, total_tokens: 10 }));
  d.renderAll();
  assert.equal(d.element('daDonutTotal').textContent, '—');
  assert.match(d.element('daDonutSub').textContent, /UNAVAILABLE/);
  assert.equal(d.frames.size, 0);
});

test('unknown latest live reads clear the older analytics card and valid zero restores it', () => {
  const d = dashboard();
  for (const id of ['daChatTurnValue', 'daChatTurnDelta', 'daChatTurnMeta', 'daTurnTokenStatus']) d.element(id);
  for (const live of [undefined, null, {}, turnSection(null), turnSection({ kind: 'exact', point: false }), turnSection({ kind: 'unknown', point: 120 })]) {
    d.renderChatTurnCard({ turn_token_measurements: turnSection() });
    assert.equal(d.element('daChatTurnValue').textContent, '120');
    d.renderLiveTurnCard({ latest_turn_measurement: live });
    assert.equal(d.element('daChatTurnValue').textContent, '—');
    assert.match(d.element('daChatTurnMeta').textContent, /unavailable/);
  }
  d.renderLiveTurnCard({ latest_turn_measurement: turnSection({ kind: 'exact', point: 0 }) });
  assert.equal(d.element('daChatTurnValue').textContent, '0');
  assert.match(d.element('daChatTurnDelta').textContent, /freshness chưa xác nhận/);
});

test('turn log rejects malformed metrics and unsafe measurement envelopes', () => {
  const d = dashboard();
  const log = d.element('daTurnLog');
  const section = turnSection();
  section.recent_turns = [
    { kind: 'exact', point: true, wall_time_ms: true },
    { kind: 'exact', point: 0, wall_time_ms: null },
    { kind: 'structural_estimate', point: 12, lower: ' ', upper: false }
  ];
  d.renderTurnLog({ turn_token_measurements: section });
  assert.equal(log.children[0].children[0].textContent, '—');
  assert.equal(log.children[0].children[2].textContent, '—');
  assert.equal(log.children[1].children[2].textContent, '0');
  assert.equal(log.children[2].children[2].textContent, '≈12');
  section.content_free = false;
  d.renderTurnLog({ turn_token_measurements: section });
  assert.equal(log.children[0].textContent, 'Turn measurements unavailable');
});

test('snapshot and sample freshness are tied to actual receipts', () => {
  const d = dashboard();
  for (const value of [null, {}, { status: { snapshotAgeMs: false, snapshotObservedAtUnixMs: ' ' } }, { status: { snapshotObservedAtUnixMs: 1e99 } }]) {
    d.setSnapshot(value);
    assert.match(d.snapshotFreshnessLabel(), /chưa xác nhận/);
  }
  d.setSnapshot({ status: { signalStale: true, snapshotAgeMs: 0 } });
  assert.match(d.snapshotFreshnessLabel(), /stale/);
  d.setSnapshot({ status: { snapshotAgeMs: 0 } });
  assert.match(d.snapshotFreshnessLabel(), /Snapshot cache 0s/);
  const now = Date.now();
  assert.match(d.realtimeAgeLabel(null, now), /chưa xác nhận/);
  assert.match(d.realtimeAgeLabel(now + 10000, now), /chưa xác nhận/);
  assert.equal(d.rollingProviderUsage({ rolling: { events: 1, tokens: 5, end: new Date(now + 10000).toISOString() } }, now).latestAt, null);
  d.element('daRealtimeTpm');
  d.element('daRealtimeTpmMeta');
  d.updateRealtimeMetrics([], { rolling: { events: 1, tokens: 50, end: new Date(now - 600000).toISOString() } });
  assert.equal(d.element('daRealtimeTpm').textContent, '—');
  assert.match(d.element('daRealtimeTpmMeta').textContent, /đã cũ/);
  d.updateRealtimeMetrics([], { rolling: { events: 1, tokens: 0, end: new Date(now).toISOString() } });
  assert.equal(d.element('daRealtimeTpm').textContent, '0');
});

test('explicit null overview receipts clear previously observed latest-turn and freshness state', async () => {
  const d = dashboard();
  d.element('daChatTurnValue');
  d.element('daLastSync');
  await d.applyOverviewPulse({ detail: {
    snapshot: { status: { snapshotAgeMs: 0 } },
    orchestration: { latest_turn_measurement: turnSection() }
  } });
  assert.equal(d.element('daChatTurnValue').textContent, '120');
  assert.match(d.element('daLastSync').textContent, /Snapshot cache/);
  await d.applyOverviewPulse({ detail: { snapshot: null, orchestration: null } });
  assert.equal(d.element('daChatTurnValue').textContent, '—');
  assert.match(d.element('daLastSync').textContent, /chưa xác nhận/);
});

test('overview performance pulses replace trace objects, preserve omitted fields, and clear explicit null', async () => {
  const d = dashboard();
  const latency = d.element('daRealtimeLatency');
  const meta = d.element('daRealtimeLatencyMeta');
  const trace = (duration) => ({ recent: [{
    started_at: new Date(Date.now() - 1000).toISOString(), tool: 'exec_command',
    ok: true, duration_ms: duration, wait_before_ms: 0
  }] });

  await d.dispatchOverviewPulse({});
  assert.equal(latency.textContent, '—');
  assert.equal(meta.textContent, 'Dữ liệu lệnh chưa khả dụng');

  await d.dispatchOverviewPulse({ performance: trace(500) });
  assert.equal(latency.textContent, '500ms');
  assert.match(meta.textContent, /1 lệnh/);

  await d.dispatchOverviewPulse({ performance: trace(250) });
  assert.equal(latency.textContent, '250ms');
  await d.dispatchOverviewPulse({ snapshot: null });
  assert.equal(latency.textContent, '250ms', 'an omitted field preserves the current trace');
  await d.dispatchOverviewPulse(Object.create({ performance: null }));
  assert.equal(latency.textContent, '250ms', 'inherited properties are not performance receipts');

  await d.dispatchOverviewPulse({ performance: null });
  assert.equal(latency.textContent, '—', 'explicit null removes the old current trace');
  assert.equal(meta.textContent, 'Dữ liệu lệnh chưa khả dụng');
  await d.dispatchOverviewPulse({});
  assert.equal(latency.textContent, '—', 'an omitted field cannot restore a cleared trace');
  assert.equal(meta.textContent, 'Dữ liệu lệnh chưa khả dụng');

  for (const performance of [{}, { recent: [] }, { records: [] }]) {
    await d.dispatchOverviewPulse({ performance });
    assert.equal(latency.textContent, '—');
    assert.equal(meta.textContent, 'Không có lệnh trong 5 phút gần nhất');
  }

  await d.dispatchOverviewPulse({ performance: trace(0) });
  assert.equal(latency.textContent, '0s', 'a measured zero remains an observed latency');
  assert.match(meta.textContent, /1 lệnh/);
  await d.dispatchOverviewPulse({ performance: undefined });
  assert.equal(latency.textContent, '—');
  assert.equal(meta.textContent, 'Dữ liệu lệnh chưa khả dụng');
});

test('unknown replaces an in-flight animation and an observed zero replaces the unknown marker', () => {
  const d = dashboard();
  d.setReducedMotion(false);
  const metric = d.element('metric');
  metric.textContent = '—';
  d.animateText(metric, d.compact, 100);
  assert.equal(d.frames.size, 1);
  d.setText('metric', '—');
  assert.equal(d.frames.size, 0);
  d.animateText(metric, d.compact, 0);
  assert.equal(metric.textContent, '0');
});

test('tool-call turns render estimated bands and never zero-fill missing windows', () => {
  const d = dashboard();
  assert.equal(d.toolCallTokenState(null), null);
  assert.equal(d.toolCallTokenState({}), null);
  const bad = { missing_measurement_policy: 'unknown_not_zero', content_free: true, status: 'context_estimate', measurement: 'CONTEXT_ESTIMATE' };
  assert.equal(d.toolCallTokenState({ tool_call_token_measurements: bad }).calls, null);
  d.element('daToolCallTokenStatus');
  d.renderToolCallTokens(null);
  assert.equal(d.element('daToolCallTokenStatus').textContent, 'Chưa đo lượt nào');
  const section = {
    missing_measurement_policy: 'unknown_not_zero', content_free: true,
    status: 'context_estimate', measurement: 'CONTEXT_ESTIMATE', confidence: 'low',
    tool_calls: 5, model_visible_bytes: 4000, model_visible_chars: 3500,
    estimate: { p10_context_tokens: 667, p50_context_tokens: 1000, p90_context_tokens: 2000, not_controller_total: true }
  };
  const state = d.toolCallTokenState({ tool_call_token_measurements: section });
  assert.equal(state.calls, 5);
  assert.equal(state.p50, 1000);
  assert.equal(state.chars, 3500);
  d.renderToolCallTokens({ tool_call_token_measurements: section });
  assert.match(d.element('daToolCallTokenStatus').textContent, /≈1\.0K · 5 lượt gọi · CONTEXT · 3\.5K ký tự/);
  const calibrated = { ...section, status: 'calibrated_estimate', measurement: 'CALIBRATED_ESTIMATE', confidence: 'low', estimate: { p10_total_tokens: 900, p50_total_tokens: 1000, p90_total_tokens: 1100 } };
  d.renderToolCallTokens({ tool_call_token_measurements: calibrated });
  assert.match(d.element('daToolCallTokenStatus').textContent, /≈1\.0K · 5 lượt gọi · LOW · 3\.5K ký tự/);
  d.renderToolCallTokens({ tool_call_token_measurements: { ...section, tool_calls: 0 } });
  assert.equal(d.element('daToolCallTokenStatus').textContent, 'Chưa đo lượt nào');
});

test('turn log pins a cumulative total preferring backend session totals', () => {
  const d = dashboard();
  const total = d.element('daTurnTotal');
  const log = d.element('daTurnLog');
  const base = {
    measurement: 'chat_turn_measurements_v1', missing_measurement_policy: 'unknown_not_zero', content_free: true,
    turns_total: 3, turns_exact: 1,
    session_total: { point: 1000, lower: 800, upper: 1500 },
    recent_turns: [
      { kind: 'structural_estimate', point: 610, lower: 407, upper: 1200, wall_time_ms: Date.now() },
      { kind: 'exact', point: 200, wall_time_ms: Date.now() },
      { kind: 'structural_estimate', point: 100, lower: 50, upper: 300, wall_time_ms: Date.now() }
    ]
  };
  d.renderTurnLog({ turn_token_measurements: base });
  assert.match(total.textContent, /Tổng phiên/);
  assert.match(total.textContent, /3 lượt/);
  assert.match(total.textContent, /ước lượng/);
  assert.match(total.textContent, /1\.0K/);
  assert.match(total.textContent, /800–1\.5K/);
  assert.equal(log.children.length, 3);
  const noSession = { ...base, session_total: null };
  d.renderTurnLog({ turn_token_measurements: noSession });
  assert.match(total.textContent, /lượt gần nhất/);
  assert.match(total.textContent, /910/);
  assert.match(total.textContent, /657–1\.7K/);
  assert.equal(log.children.length, 3);
  const unmeasured = { ...base, session_total: null, recent_turns: [{ kind: 'unknown', wall_time_ms: Date.now() }] };
  d.renderTurnLog({ turn_token_measurements: unmeasured });
  assert.match(total.textContent, /Chưa có lượt nào để cộng dồn/);
});

test('chat turn card falls back to loaded-turn totals when the session total is missing', () => {
  const d = dashboard();
  for (const id of ['daChatTurnValue', 'daChatTurnDelta', 'daChatTurnMeta']) d.element(id);
  const section = {
    measurement: 'chat_turn_measurements_v1', missing_measurement_policy: 'unknown_not_zero', content_free: true,
    turns_total: 2, turns_exact: 0,
    latest_turn: { kind: 'structural_estimate', point: 610, lower: 407, upper: 1200 },
    recent_turns: [
      { kind: 'structural_estimate', point: 610, lower: 407, upper: 1200 },
      { kind: 'structural_estimate', point: 300, lower: 250, upper: 500 }
    ]
  };
  d.renderChatTurnCard({ turn_token_measurements: section });
  assert.equal(d.element('daChatTurnValue').textContent, '≈910');
  assert.match(d.element('daChatTurnDelta').textContent, /tổng 2 lượt gần nhất/);
  assert.match(d.element('daChatTurnDelta').textContent, /910/);
  assert.match(d.element('daChatTurnDelta').textContent, /Lượt mới nhất \(407–1\.2K\)/);
  const unknownLatest = { ...section, latest_turn: { kind: 'unknown' } };
  d.renderChatTurnCard({ turn_token_measurements: unknownLatest });
  assert.match(d.element('daChatTurnDelta').textContent, /Tổng các lượt gần nhất/);
  assert.match(d.element('daChatTurnDelta').textContent, /lượt mới nhất chưa đo/);
});
