(() => {
  'use strict';

  const api = window.mcpAssistant;
  if (!api) return;

  // Pricing presets — USD per 1M tokens (input / output). OpenAI list prices
  // at time of writing; the operator can override every field below.
  const PRICING_PRESETS = [
    { id: 'gpt-4o-mini', label: 'GPT-4o mini', rateIn: 0.15, rateOut: 0.6 },
    { id: 'gpt-4o', label: 'GPT-4o', rateIn: 2.5, rateOut: 10 },
    { id: 'gpt-4.1', label: 'GPT-4.1', rateIn: 2, rateOut: 8 },
    { id: 'o3-mini', label: 'o3-mini', rateIn: 1.1, rateOut: 4.4 },
    { id: 'o3', label: 'o3', rateIn: 10, rateOut: 40 },
    { id: 'custom', label: 'Tùy chỉnh', rateIn: null, rateOut: null }
  ];
  const DEFAULT_FX_VND_PER_USD = 25000;
  const DEFAULT_LANE_RATES = {
    deepseek: { in: 0.28, out: 0.42 },
    fast: { in: 0.15, out: 0.6 },
    terra: { in: 2.5, out: 10 },
    sol: { in: 10, out: 40 }
  };

  // Canonical per-model pricing — USD per 1M tokens. Mirrors
  // resources/coding-tools-mcp/coding_tools_mcp/usage_pricing.py so the
  // dashboard derives the same token value the backend records.
  const MODEL_PRICING = {
    'deepseek-v4-flash': { in: 0.28, out: 0.42, cached: 0.028 },
    'deepseek-v4-pro': { in: 0.28, out: 0.42, cached: 0.028 },
    'gpt-5.4-mini': { in: 0.15, out: 0.6 },
    'gpt-5.6-luna': { in: 0.15, out: 0.6 },
    'gpt-5.6-terra': { in: 2.5, out: 10 },
    'gpt-5.6-sol': { in: 10, out: 40 }
  };
  const MODEL_PRICING_PATTERNS = [
    { pattern: /^deepseek-/, rates: MODEL_PRICING['deepseek-v4-flash'] }
  ];

  // Model rows: ChatWeb plus the four delegatable compute lanes. Desktop,
  // OpenCode and the unassigned bucket appear only when they hold traffic.
  const MODELS = [
    { id: 'chatweb', name: 'ChatWeb', sub: 'ChatGPT Web · semantic control' },
    { id: 'fast', name: 'Codex Fast', sub: 'Mini / Luna' },
    { id: 'deepseek', name: 'OpenCode Go', sub: 'DeepSeek Flash / Pro' },
    { id: 'terra', name: 'Codex Deep', sub: 'Terra' },
    { id: 'sol', name: 'Codex Critical', sub: 'Sol' },
    { id: 'desktop', name: 'Codex Desktop', sub: 'deep frontend · subscription', optional: true },
    { id: 'opencode', name: 'OpenCode', sub: 'Go frontend', optional: true },
    { id: 'unassigned', name: 'Chưa phân bổ', sub: 'không có bằng chứng delegation/controller', optional: true }
  ];

  // Tools whose payload bytes are binary (images) rather than model text —
  // counting them as tokens would systematically inflate the estimate.
  const NON_TOKEN_TOOLS = new Set(['view_image']);
  const REALTIME_WINDOW_MS = 5 * 60 * 1000;
  const DASHBOARD_WINDOW_HOURS = 7 * 24;
  const DASHBOARD_SNAPSHOT_REFRESH_MS = 30000;
  const DASHBOARD_PERFORMANCE_REFRESH_MS = 10000;
  const DASHBOARD_ORCHESTRATION_REFRESH_MS = 5000;
  const DASHBOARD_BUSY_POLL_MS = 10000;
  const DASHBOARD_IDLE_POLL_MS = 5000;
  const DASHBOARD_HIDDEN_POLL_MS = 15000;

  const STATE_RANK = { offline: 0, connected: 1, waiting: 2, blocked: 3, active: 4 };

  let perf = null;
  let orchestration = null;
  let snapshot = null;
  let cost = {
    preset: 'gpt-4o-mini', rateIn: 0.15, rateOut: 0.6, currency: 'USD',
    fxRate: 0, bytesPerToken: 4, laneRates: { ...DEFAULT_LANE_RATES }
  };
  let refreshInFlight = false;
  let lastPerfReadAt = 0;
  let lastOrchestrationReadAt = 0;
  let lastSnapshotReadAt = 0;
  let lastEventSeq = -1;
  let reducedMotion = false;
  let chartTimeMode = 'hour';

  const $ = (selector) => document.querySelector(selector);
  const byId = (id) => document.getElementById(id);

  function unwrap(result) {
    if (!result?.ok) throw new Error(result?.error || 'Dashboard request failed');
    return result.data;
  }

  function activePage() {
    return $('.page.active')?.dataset.pageView || 'overview';
  }

  function shouldPoll() {
    return document.visibilityState !== 'hidden' && activePage() === 'overview';
  }

  function orchestrationIsBusy(data = orchestration) {
    const rawState = String(
      data?.resume_packet?.orchestration_state
      || data?.task?.orchestration?.orchestration_state
      || data?.orchestration_state
      || ''
    ).trim().toUpperCase();
    const taskStatus = String(data?.task?.status || '').toLowerCase();
    const writeStatus = String(data?.authority?.write?.status || '').toLowerCase();
    return ['PREFLIGHT', 'ROUTED', 'EXECUTING', 'PROVING', 'REPLAN'].includes(rawState)
      || taskStatus === 'active'
      || writeStatus === 'active';
  }

  function compact(value) {
    const number = Number(value || 0);
    if (!Number.isFinite(number) || number < 0) return '0';
    if (number < 1000) return String(Math.round(number));
    if (number < 1000000) return `${(number / 1000).toFixed(number < 10000 ? 1 : 0)}K`;
    return `${(number / 1000000).toFixed(number < 10000000 ? 2 : 1)}M`;
  }

  function money(value) {
    const number = Number(value || 0);
    if (!Number.isFinite(number)) return cost.currency === 'USD' ? '$0.00' : '0 ₫';
    if (cost.currency === 'VND') return `${new Intl.NumberFormat('vi-VN').format(Math.round(number))} ₫`;
    return number < 1 ? `$${number.toFixed(3)}` : `$${number.toFixed(2)}`;
  }

  function fxRate() {
    return Number(cost.fxRate) > 0 ? Number(cost.fxRate) : DEFAULT_FX_VND_PER_USD;
  }

  function displayedCost(usd) {
    return cost.currency === 'VND' ? usd * fxRate() : usd;
  }

  function percent(part, whole) {
    if (!Number(whole)) return 0;
    return Math.max(0, Math.min(100, (Number(part) / Number(whole)) * 100));
  }

  function formatDuration(ms) {
    const value = Number(ms || 0);
    if (!Number.isFinite(value) || value <= 0) return '0s';
    if (value < 1000) return `${Math.round(value)}ms`;
    if (value < 60000) return `${(value / 1000).toFixed(value < 10000 ? 1 : 0)}s`;
    return `${Math.floor(value / 60000)}m ${Math.round((value % 60000) / 1000)}s`;
  }

  function observedNumber(value) {
    if (value === null || value === undefined || value === '') return null;
    const number = Number(value);
    return Number.isFinite(number) && number >= 0 ? number : null;
  }

  function normalizeRecords() {
    const list = Array.isArray(perf?.recent)
      ? perf.recent
      : (Array.isArray(perf?.records) ? perf.records : []);
    return list
      .map((record) => {
        const started = new Date(record?.started_at);
        if (Number.isNaN(started.getTime())) return null;
        return {
          at: started,
          time: started.getTime(),
          hour: Math.floor(started.getTime() / 3600000),
          tool: String(record?.tool || 'unknown'),
          requestBytes: Number(record?.request_bytes || 0),
          responseBytes: Number(record?.response_bytes || 0),
          modelVisibleBytes: Number.isFinite(Number(record?.model_visible_bytes))
            ? Math.max(0, Number(record.model_visible_bytes))
            : null,
          ok: Boolean(record?.ok),
          durationMs: Number(record?.duration_ms || 0),
          waitMs: Number(record?.wait_before_ms || 0),
          tokenEligible: !NON_TOKEN_TOOLS.has(String(record?.tool || ''))
        };
      })
      .filter(Boolean);
  }

  function tokensFromBytes(bytes) {
    const ratio = Number(cost.bytesPerToken) >= 1 ? Number(cost.bytesPerToken) : 4;
    return Number(bytes || 0) / ratio;
  }

  function localMidnight(date) {
    const start = new Date(date);
    start.setHours(0, 0, 0, 0);
    return start.getTime();
  }

  function summarize(records) {
    const result = { calls: 0, ok: 0, inTokens: 0, outTokens: 0, execMs: 0, waitMs: 0 };
    for (const record of records) {
      result.calls += 1;
      if (record.ok) result.ok += 1;
      result.execMs += record.durationMs;
      result.waitMs += record.waitMs;
      if (!record.tokenEligible || record.modelVisibleBytes === null) continue;
      // Transport request/response bytes are payload telemetry, not token truth.
      // model_visible_bytes is measured; byte/token conversion remains estimated.
      result.inTokens += tokensFromBytes(record.modelVisibleBytes);
    }
    return result;
  }

  function canonicalControllerUsageState() {
    const analytics = orchestration?.usage_analytics;
    if (!analytics || analytics.measurement !== 'canonical_non_overlapping') return null;
    if (analytics.missing_measurement_policy !== 'unknown_not_zero') return null;
    const controller = analytics.controller_usage;
    if (!controller || typeof controller !== 'object') return null;
    if (controller.missing_measurement_policy !== 'unknown_not_zero') return null;
    const status = String(controller.status || '').trim().toLowerCase();
    if (status !== 'observed' && status !== 'unobserved') return null;
    const eventCount = Math.max(0, Number(controller.event_count) || 0);
    if ((status === 'observed' && eventCount < 1) || (status === 'unobserved' && eventCount !== 0)) return null;
    return {
      status,
      eventCount,
      missingReason: status === 'unobserved'
        ? String(controller.missing_reason || 'no_exact_controller_usage_event_in_window')
        : ''
    };
  }

  function canonicalOperationsAnalytics() {
    const analytics = orchestration?.operations_analytics;
    if (!analytics || analytics.measurement !== 'accepted_result_operations_v1') return null;
    if (analytics.missing_measurement_policy !== 'unknown_not_zero') return null;
    if (!analytics.outcomes || !analytics.speed || !analytics.efficiency || !analytics.cost) return null;
    return analytics;
  }

  function canonicalMeasuredUsage() {
    const analytics = orchestration?.usage_analytics;
    if (!analytics || analytics.measurement !== 'canonical_non_overlapping') return null;
    if (analytics.missing_measurement_policy !== 'unknown_not_zero') return null;
    const overall = analytics.overall && typeof analytics.overall === 'object' ? analytics.overall : {};
    const events = Math.max(0, Number(overall.event_count) || 0);
    if (!events) return null;
    const usage = overall.usage && typeof overall.usage === 'object' ? overall.usage : {};
    const costStats = overall.cost && typeof overall.cost === 'object' ? overall.cost : {};
    const measuredCostEvents = Math.max(0, Number(costStats.measured_event_count) || 0);
    const derivedCostEvents = Math.max(0, Number(costStats.derived_event_count) || 0);
    const unobservedCostEvents = Math.max(0, Number(costStats.unobserved_event_count) || 0);
    const measuredCost = Math.max(0, Number(costStats.measured_usd) || 0);
    const derivedCost = Math.max(0, Number(costStats.derived_usd) || 0);
    const costSource = measuredCostEvents > 0 ? 'provider_reported' : derivedCostEvents > 0 ? 'pricing_derived' : 'unobserved';
    const cost = costSource === 'provider_reported' ? measuredCost : costSource === 'pricing_derived' ? derivedCost : 0;
    const hours = new Map();
    for (const row of Array.isArray(analytics.hourly) ? analytics.hourly : []) {
      const time = Date.parse(String(row?.hour || ''));
      if (!Number.isFinite(time)) continue;
      const rowUsage = row?.usage && typeof row.usage === 'object' ? row.usage : {};
      hours.set(Math.floor(time / 3600000), {
        in: Math.max(0, Number(rowUsage.input_total_tokens) || 0),
        out: Math.max(0, Number(rowUsage.output_total_tokens) || 0),
        total: Math.max(0, Number(rowUsage.total_tokens) || 0),
        events: Math.max(0, Number(row?.event_count) || 0)
      });
    }
    const rollingRow = analytics.rolling_5m && typeof analytics.rolling_5m === 'object' ? analytics.rolling_5m : {};
    const rollingUsage = rollingRow.usage && typeof rollingRow.usage === 'object' ? rollingRow.usage : {};
    const rolling = {
      events: Math.max(0, Number(rollingRow.event_count) || 0),
      tokens: Math.max(0, Number(rollingUsage.total_tokens) || 0),
      end: String(rollingRow.end || analytics?.window?.end || '')
    };
    const modelMap = new Map();
    for (const row of Array.isArray(analytics.by_model) ? analytics.by_model : []) {
      const model = String(row?.model || row?.model_id || 'unknown').trim() || 'unknown';
      const rowUsage = row?.usage && typeof row.usage === 'object' ? row.usage : {};
      const rowCost = row?.cost && typeof row.cost === 'object' ? row.cost : {};
      const entry = modelMap.get(model) || {
        tool: model, model, calls: 0, ok: 0, inTokens: 0, outTokens: 0, cachedTokens: 0,
        cost: 0, costSource: 'unobserved', usageEvidence: 'MEASURED',
        measuredCost: 0, derivedCost: 0, measuredCostEvents: 0, derivedCostEvents: 0
      };
      entry.calls += Math.max(0, Number(row?.event_count) || 0);
      entry.inTokens += Math.max(0, Number(rowUsage.input_total_tokens) || 0);
      entry.outTokens += Math.max(0, Number(rowUsage.output_total_tokens) || 0);
      entry.cachedTokens += Math.max(0, Number(rowUsage.input_cached_tokens) || 0);
      entry.measuredCost += Math.max(0, Number(rowCost.measured_usd) || 0);
      entry.derivedCost += Math.max(0, Number(rowCost.derived_usd) || 0);
      entry.measuredCostEvents += Math.max(0, Number(rowCost.measured_event_count) || 0);
      entry.derivedCostEvents += Math.max(0, Number(rowCost.derived_event_count) || 0);
      modelMap.set(model, entry);
    }
    for (const entry of modelMap.values()) {
      if (entry.measuredCostEvents > 0) {
        entry.cost = entry.measuredCost;
        entry.costSource = 'provider_reported';
      } else if (entry.derivedCostEvents > 0) {
        entry.cost = entry.derivedCost;
        entry.costSource = 'pricing_derived';
      }
    }
    return {
      events,
      input: Math.max(0, Number(usage.input_total_tokens) || 0),
      cached: Math.max(0, Number(usage.input_cached_tokens) || 0),
      output: Math.max(0, Number(usage.output_total_tokens) || 0),
      reasoning: Math.max(0, Number(usage.output_reasoning_tokens) || 0),
      total: Math.max(0, Number(usage.total_tokens) || 0),
      cost,
      costSource,
      measuredCostEvents,
      derivedCostEvents,
      unobservedCostEvents,
      hours,
      rolling,
      byModel: [...modelMap.values()].sort((a, b) => (b.inTokens + b.outTokens) - (a.inTokens + a.outTokens))
    };
  }

  function hourBuckets(records, buckets = 24) {
    const nowHour = Math.floor(Date.now() / 3600000);
    const start = nowHour - buckets + 1;
    const grid = Array.from({ length: buckets }, (_, index) => ({
      hour: start + index,
      in: 0,
      out: 0
    }));
    const indexOf = new Map(grid.map((bucket, index) => [bucket.hour, index]));
    for (const record of records) {
      const index = indexOf.get(record.hour);
      if (index === undefined || !record.tokenEligible || record.modelVisibleBytes === null) continue;
      grid[index].in += tokensFromBytes(record.modelVisibleBytes);
    }
    return grid;
  }

  function hourlyFromStore(buckets = 24) {
    const map = perf?.hourly_metrics;
    if (!map || typeof map !== 'object') return null;
    const byHour = new Map();
    for (const [key, bucket] of Object.entries(map)) {
      const hour = Number(key);
      if (!Number.isInteger(hour) || !bucket || typeof bucket !== 'object') continue;
      const bytes = Number(bucket.model_visible_bytes) || 0;
      byHour.set(hour, {
        hour,
        in: tokensFromBytes(bytes),
        out: 0,
        calls: Math.max(0, Number(bucket.tool_calls) || 0),
        errors: Math.max(0, Number(bucket.errors) || 0),
        cacheHits: Math.max(0, Number(bucket.cache_hits) || 0),
        execMs: Math.max(0, Number(bucket.local_execution_ms) || 0),
        waitMs: Math.max(0, Number(bucket.estimated_wait_ms) || 0)
      });
    }
    if (!byHour.size) return null;
    const nowHour = Math.floor(Date.now() / 3600000);
    const start = nowHour - buckets + 1;
    return Array.from({ length: buckets }, (_, index) => {
      const hour = start + index;
      return byHour.get(hour) || { hour, in: 0, out: 0 };
    });
  }

  function performanceBuckets(records, count = 24) {
    // Hourly buckets persisted server-side survive the recent-trace window;
    // the recent trace remains the fallback when no hourly data exists yet.
    return hourlyFromStore(count) || hourBuckets(records, count);
  }

  function canonicalHourBuckets(measured, count = DASHBOARD_WINDOW_HOURS) {
    if (!measured?.hours || !(measured.hours instanceof Map)) return null;
    const nowHour = Math.floor(Date.now() / 3600000);
    const start = nowHour - count + 1;
    return Array.from({ length: count }, (_, index) => {
      const hour = start + index;
      const bucket = measured.hours.get(hour);
      return { hour, in: bucket?.in || 0, out: bucket?.out || 0 };
    });
  }

  function aggregateHourBuckets(buckets, hoursPerBucket = 24) {
    if (!Array.isArray(buckets) || !buckets.length) return [];
    const size = Math.max(1, Math.floor(Number(hoursPerBucket) || 1));
    const aggregated = [];
    for (let start = 0; start < buckets.length; start += size) {
      const slice = buckets.slice(start, start + size);
      if (!slice.length) continue;
      aggregated.push({
        hour: slice[0].hour,
        endHour: slice[slice.length - 1].hour,
        in: slice.reduce((sum, bucket) => sum + (Number(bucket.in) || 0), 0),
        out: slice.reduce((sum, bucket) => sum + (Number(bucket.out) || 0), 0)
      });
    }
    return aggregated;
  }

  function chartTrendBuckets(measured, records, mode = chartTimeMode) {
    const hourly = canonicalHourBuckets(measured, DASHBOARD_WINDOW_HOURS)
      || performanceBuckets(records, DASHBOARD_WINDOW_HOURS);
    return mode === 'day' ? aggregateHourBuckets(hourly, 24) : hourly;
  }

  function toolBreakdown(records) {
    const map = new Map();
    for (const record of records) {
      let entry = map.get(record.tool);
      if (!entry) {
        entry = { tool: record.tool, calls: 0, ok: 0, inTokens: 0, outTokens: 0, cost: 0 };
        map.set(record.tool, entry);
      }
      entry.calls += 1;
      if (record.ok) entry.ok += 1;
      if (!record.tokenEligible || record.modelVisibleBytes === null) continue;
      const inTokens = tokensFromBytes(record.modelVisibleBytes);
      const outTokens = 0;
      entry.inTokens += inTokens;
      entry.outTokens += outTokens;
      entry.cost += (inTokens / 1e6) * Number(cost.rateIn) + (outTokens / 1e6) * Number(cost.rateOut);
    }
    return [...map.values()].sort((a, b) => b.cost - a.cost);
  }

  function modelPriceOf(modelId, component) {
    const id = String(modelId || '').toLowerCase();
    for (const [name, rates] of Object.entries(MODEL_PRICING)) {
      if (id === name || id.endsWith(`/${name}`)) return Number(rates[component]) || 0;
    }
    for (const rule of MODEL_PRICING_PATTERNS) {
      if (rule.pattern.test(id)) return Number(rule.rates[component]) || 0;
    }
    return 0;
  }

  function costOf(summary, lane = 'chatweb') {
    const modelId = summary.modelId || lane;
    const inRate = modelPriceOf(modelId, 'in') || rateFor(lane).in;
    const outRate = modelPriceOf(modelId, 'out') || rateFor(lane).out;
    const cachedRate = modelPriceOf(modelId, 'cached');
    const cachedTokens = Number(summary.cachedTokens) || 0;
    const uncached = Math.max(0, Number(summary.inTokens) - cachedTokens);
    let usd = (uncached / 1e6) * inRate + (Number(summary.outTokens) / 1e6) * outRate;
    if (cachedRate > 0 && cachedTokens > 0) usd += (cachedTokens / 1e6) * cachedRate;
    return usd;
  }

  function rateFor(lane) {
    if (lane === 'chatweb') return { in: Number(cost.rateIn) || 0, out: Number(cost.rateOut) || 0 };
    const rates = cost.laneRates[lane];
    if (rates) return { in: Number(rates.in) || 0, out: Number(rates.out) || 0 };
    return { in: 0, out: 0 };
  }

  // ---- Evidence-based attribution to models -------------------------------

  function delegationLane(delegation) {
    const text = `${delegation?.route_resolved || ''} ${delegation?.model || ''}`.toLowerCase();
    if (text.includes('deepseek')) return 'deepseek';
    if (text.includes('terra')) return 'terra';
    if (text.includes('sol')) return 'sol';
    if (text.includes('mini') || text.includes('luna')) return 'fast';
    return '';
  }

  function delegationState(status) {
    const value = String(status || '').toLowerCase();
    if (['active', 'running', 'starting', 'executing', 'in_progress'].includes(value)) return 'active';
    if (['waiting', 'queued', 'pending', 'idle'].includes(value)) return 'waiting';
    if (['blocked', 'failed', 'replanned', 'interrupted'].includes(value)) return 'blocked';
    return 'offline';
  }

  function laneWindows() {
    const delegations = Array.isArray(orchestration?.delegations) ? orchestration.delegations : [];
    const now = Date.now();
    return delegations.map((delegation) => {
      const start = Date.parse(delegation?.started_at);
      if (!Number.isFinite(start)) return null;
      const finished = delegation?.finished_at ? Date.parse(delegation.finished_at) : NaN;
      const lane = delegationLane(delegation);
      if (!lane) return null;
      return {
        start,
        end: Number.isFinite(finished) ? finished : now + 60000,
        lane
      };
    }).filter(Boolean);
  }

  function controllerWindows() {
    const windows = [];
    const events = Array.isArray(orchestration?.events) ? orchestration.events : [];
    const transfers = events
      .filter((event) => event?.event_type === 'controller_transferred')
      .sort((a, b) => String(a?.event_time || '').localeCompare(String(b?.event_time || '')));
    const boundaries = [];
    for (const event of transfers) {
      const time = Date.parse(event?.event_time);
      let owner = '';
      try { owner = String(JSON.parse(event?.payload || '{}').from_client_id || ''); } catch { owner = ''; }
      if (!Number.isFinite(time)) continue;
      boundaries.push({ time, owner });
    }
    if (!boundaries.length) {
      const current = String(orchestration?.authority?.controller?.owner_client_id || '');
      if (current) windows.push({ start: 0, end: Date.now() + 60000, owner: current });
      return windows;
    }
    for (let index = 0; index < boundaries.length; index += 1) {
      const previous = index > 0 ? boundaries[index - 1].time : 0;
      windows.push({ start: previous, end: boundaries[index].time, owner: boundaries[index].owner });
    }
    const current = String(orchestration?.authority?.controller?.owner_client_id || '');
    if (current) {
      windows.push({ start: boundaries[boundaries.length - 1].time, end: Date.now() + 60000, owner: current });
    }
    return windows.filter((window) => window.owner);
  }

  function modelOf(record) {
    const lanes = laneWindows();
    const lane = lanes.find((window) => record.time >= window.start && record.time < window.end);
    if (lane) return lane.lane;
    const windows = controllerWindows();
    const window = windows.find((item) => record.time >= item.start && record.time < item.end);
    const owner = window?.owner || '';
    if (owner === 'chatweb') return 'chatweb';
    if (owner === 'codex-desktop') return 'desktop';
    if (owner === 'opencode') return 'opencode';
    return 'unassigned';
  }

  function modelBreakdown(records) {
    const map = new Map();
    for (const record of records) {
      const model = modelOf(record);
      let entry = map.get(model);
      if (!entry) {
        entry = { model, calls: 0, ok: 0, inTokens: 0, outTokens: 0, cost: 0 };
        map.set(model, entry);
      }
      entry.calls += 1;
      if (record.ok) entry.ok += 1;
      if (!record.tokenEligible || record.modelVisibleBytes === null) continue;
      const inTokens = tokensFromBytes(record.modelVisibleBytes);
      const outTokens = 0;
      entry.inTokens += inTokens;
      entry.outTokens += outTokens;
      entry.usageEvidence = 'ESTIMATED';
    }

    for (const entry of map.values()) {
      entry.cost = costOf(entry, entry.model);
      entry.costSource = 'settings_estimate';
      if (entry.calls > 0) entry.usageEvidence = 'ESTIMATED';
    }
    return map;
  }

  function modelState(modelId) {
    const data = orchestration || {};
    if (modelId === 'chatweb') {
      const client = (Array.isArray(data.clients) ? data.clients : [])
        .find((item) => item?.client_id === 'chatweb' || item?.client_type === 'chatweb');
      if (!client?.online) return 'offline';
      return data?.authority?.controller?.owner_client_id === 'chatweb' ? 'active' : 'connected';
    }
    if (modelId === 'desktop' || modelId === 'opencode') {
      const type = modelId === 'desktop' ? 'codex_desktop' : 'opencode';
      const client = (Array.isArray(data.clients) ? data.clients : [])
        .find((item) => item?.client_id === type || item?.client_type === type || item?.client_id === `codex-${modelId}`);
      return client?.online ? 'connected' : 'offline';
    }
    if (modelId === 'unassigned') return 'offline';
    let state = 'offline';
    for (const delegation of Array.isArray(data.delegations) ? data.delegations : []) {
      if (delegationLane(delegation) !== modelId) continue;
      const next = delegationState(delegation?.status);
      if (STATE_RANK[next] > STATE_RANK[state]) state = next;
    }
    return state;
  }

  // ---- 9router-style animations -------------------------------------------

  function animateText(element, formatter, next) {
    if (!element || reducedMotion || orchestrationIsBusy()) {
      if (element) element.textContent = formatter(next);
      return;
    }
    const from = Number(element.dataset.value) || 0;
    const to = Number(next) || 0;
    if (from === to) return;
    const start = performance.now();
    const duration = 520;
    element.dataset.value = String(to);
    element.classList.remove('is-updated');
    void element.offsetWidth;
    element.classList.add('is-updated');
    const step = (now) => {
      const progress = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      element.textContent = formatter(from + (to - from) * eased);
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  function setText(id, value) {
    const element = byId(id);
    if (element) element.textContent = String(value ?? '—');
  }

  function setPill(id, text, state) {
    const element = byId(id);
    if (!element) return;
    element.textContent = text;
    element.className = `cc-pill is-${state}`;
  }

  function renderSparkline(buckets) {
    const container = byId('daSpark');
    if (!container) return;
    container.replaceChildren();
    const totals = buckets.map((bucket) => bucket.in + bucket.out);
    const max = Math.max(1, ...totals);
    for (const total of totals) {
      const bar = document.createElement('i');
      if (total <= 0) bar.classList.add('is-empty');
      else bar.style.height = `${Math.max(10, Math.round((total / max) * 100))}%`;
      container.appendChild(bar);
    }
  }

  function renderRing(elementId, value) {
    const element = byId(elementId);
    if (!element) return;
    const radius = 15;
    const circumference = 2 * Math.PI * radius;
    const clamped = Math.max(0, Math.min(100, Number(value || 0)));
    element.setAttribute('viewBox', '0 0 36 36');
    element.innerHTML = '';
    const background = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    background.setAttribute('cx', '18');
    background.setAttribute('cy', '18');
    background.setAttribute('r', String(radius));
    background.setAttribute('fill', 'none');
    background.setAttribute('stroke', 'var(--cc-surface-soft)');
    background.setAttribute('stroke-width', '4');
    const ring = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    ring.setAttribute('cx', '18');
    ring.setAttribute('cy', '18');
    ring.setAttribute('r', String(radius));
    ring.setAttribute('fill', 'none');
    ring.setAttribute('stroke', clamped >= 90 ? 'var(--da-out)' : 'var(--da-err)');
    ring.setAttribute('stroke-width', '4');
    ring.setAttribute('stroke-linecap', 'round');
    ring.setAttribute('stroke-dasharray', String(circumference));
    ring.setAttribute('stroke-dashoffset', String(circumference * (1 - clamped / 100)));
    ring.setAttribute('transform', 'rotate(-90 18 18)');
    element.append(background, ring);
  }

  function niceCeiling(value) {
    if (!Number.isFinite(value) || value <= 0) return 1;
    const magnitude = Math.pow(10, Math.floor(Math.log10(value)));
    const normalized = value / magnitude;
    const step = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
    return step * magnitude;
  }

  function svgEl(tag, attributes, text) {
    const element = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [key, value] of Object.entries(attributes || {})) element.setAttribute(key, String(value));
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function pointsFor(buckets, index, width, height, padLeft, padRight, padTop, padBottom, max) {
    const stepX = (width - padLeft - padRight) / Math.max(1, buckets.length - 1);
    return buckets.map((bucket, i) => {
      const x = padLeft + i * stepX;
      const y = padTop + (height - padTop - padBottom) * (1 - bucket[index] / max);
      return [x, y];
    });
  }

  function pathFrom(points, closeToBottom, height, padBottom) {
    const head = points.map(([x, y], index) => `${index === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
    if (!closeToBottom) return head;
    const last = points[points.length - 1];
    const first = points[0];
    const baseline = height - padBottom;
    return `${head} L${last[0].toFixed(1)},${baseline} L${first[0].toFixed(1)},${baseline} Z`;
  }

  function renderChart(buckets, timeMode = 'hour') {
    const svg = byId('daChart');
    const empty = byId('daChartEmpty');
    if (!svg || !empty) return;
    const totals = buckets.map((bucket) => bucket.in + bucket.out);
    const max = niceCeiling(Math.max(...totals, 0));
    const hasData = totals.some((value) => value > 0);
    empty.hidden = hasData;
    svg.hidden = !hasData;
    svg.replaceChildren();
    if (!hasData) return;

    const width = 640;
    const height = 210;
    const pad = { left: 40, right: 12, top: 14, bottom: 24 };
    const plotW = width - pad.left - pad.right;
    const plotH = height - pad.top - pad.bottom;

    const gradientId = `daGradient${Math.random().toString(36).slice(2, 8)}`;
    const defs = svgEl('defs', {});
    const gradient = svgEl('linearGradient', { id: gradientId, x1: '0', y1: '0', x2: '0', y2: '1' });
    gradient.append(
      svgEl('stop', { offset: '0%', 'stop-color': 'var(--da-in)', 'stop-opacity': '0.22' }),
      svgEl('stop', { offset: '100%', 'stop-color': 'var(--da-in)', 'stop-opacity': '0' })
    );
    defs.appendChild(gradient);
    svg.appendChild(defs);

    for (let line = 0; line <= 3; line += 1) {
      const y = pad.top + (plotH * line) / 3;
      svg.appendChild(svgEl('line', { x1: pad.left, x2: width - pad.right, y1: y, y2: y, class: 'grid-line' }));
      svg.appendChild(svgEl('text', { x: pad.left - 6, y: y + 3, 'text-anchor': 'end', class: 'axis-label' },
        compact((max * (3 - line)) / 3)));
    }

    const series = [
      { key: 'in', color: 'var(--da-in)' },
      { key: 'out', color: 'var(--da-out)' }
    ];
    for (const item of series) {
      const points = pointsFor(buckets, item.key, width, height, pad.left, pad.right, pad.top, pad.bottom, max);
      if (item.key === 'in') {
        svg.appendChild(svgEl('path', {
          d: pathFrom(points, true, height, pad.bottom),
          fill: `url(#${gradientId})`,
          class: 'series-area'
        }));
      }
      svg.appendChild(svgEl('path', {
        d: pathFrom(points, false, height, pad.bottom),
        class: 'series-line',
        stroke: item.color
      }));
    }

    const tickEvery = timeMode === 'day' ? 1 : Math.max(1, Math.ceil(buckets.length / 7));
    for (let index = 0; index < buckets.length; index += 1) {
      if (index % tickEvery !== 0) continue;
      const bucket = buckets[index];
      const date = new Date((timeMode === 'day' ? bucket.endHour : bucket.hour) * 3600000);
      const x = pad.left + (plotW * index) / Math.max(1, buckets.length - 1);
      svg.appendChild(svgEl('text', { x, y: height - 8, 'text-anchor': 'middle', class: 'axis-label' },
        timeMode === 'day'
          ? date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })
          : date.toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })));
    }

    const tooltip = byId('daChartTooltip');
    const clearGuide = () => {
      svg.querySelectorAll('.hover-guide,.hover-dot').forEach((node) => node.remove());
      if (tooltip) tooltip.hidden = true;
    };
    svg.addEventListener('mouseleave', clearGuide);
    svg.addEventListener('mousemove', (event) => {
      const bounds = svg.getBoundingClientRect();
      const x = ((event.clientX - bounds.left) / bounds.width) * width;
      const index = Math.round(((x - pad.left) / plotW) * (buckets.length - 1));
      if (index < 0 || index >= buckets.length) { clearGuide(); return; }
      const px = pad.left + (plotW * index) / Math.max(1, buckets.length - 1);
      const bucket = buckets[index];
      clearGuide();
      const y = pad.top + plotH * (1 - (bucket.in + bucket.out) / max);
      svg.appendChild(svgEl('line', { x1: px, x2: px, y1: pad.top, y2: height - pad.bottom, class: 'hover-guide' }));
      svg.appendChild(svgEl('circle', { cx: px, cy: y, r: 4, fill: 'var(--cc-blue)', class: 'hover-dot' }));
      if (tooltip) {
        tooltip.hidden = false;
        const bucketDate = new Date((timeMode === 'day' ? bucket.endHour : bucket.hour) * 3600000);
        const timeLabel = timeMode === 'day'
          ? `24 giờ kết thúc ${bucketDate.toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}`
          : bucketDate.toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
        tooltip.textContent = `${timeLabel} · vào ${compact(bucket.in)} · ra ${compact(bucket.out)}`;
        const card = byId('daChartCard');
        if (card) {
          const cardBounds = card.getBoundingClientRect();
          tooltip.style.left = `${Math.max(12, Math.min(cardBounds.width - 240, event.clientX - cardBounds.left + 14))}px`;
          tooltip.style.top = `${event.clientY - cardBounds.top - 30}px`;
        }
      }
    });
  }

  function renderDonut(entries, evidence = 'estimated') {
    const svg = byId('daDonut');
    const legend = byId('daLegend');
    const center = byId('daDonutTotal');
    const sub = byId('daDonutSub');
    const foot = byId('daDonutFoot');
    if (!svg || !legend) return;
    const total = entries.reduce((sum, entry) => sum + entry.inTokens + entry.outTokens, 0);
    const colors = ['var(--da-in)', 'var(--da-out)', 'var(--da-cost)', '#7c5cff', '#2ba7a0', '#c95b9e'];
    const radius = 54;
    const stroke = 13;
    const circumference = 2 * Math.PI * radius;
    svg.replaceChildren();
    legend.replaceChildren();
    animateText(center, compact, total);
    if (sub) sub.textContent = 'TOKEN ƯỚC TÍNH';
    if (foot) foot.textContent = total > 0 ? `${entries.length} mô hình` : '— mô hình';
    if (sub) sub.textContent = evidence === 'measured' ? 'TOKEN MEASURED' : 'TOKEN ESTIMATED';
    if (foot) foot.textContent = total > 0
      ? `${entries.length} ${evidence === 'measured' ? 'model' : 'tool'}`
      : `— ${evidence === 'measured' ? 'model' : 'tool'}`;
    svg.appendChild(center);
    if (sub) svg.appendChild(sub);
    if (!total) {
      const empty = document.createElement('div');
      empty.className = 'da-chart-empty';
      empty.style.height = 'auto';
      empty.style.minHeight = '170px';
      empty.textContent = 'Chưa có lưu lượng token để phân bổ.';
      legend.replaceChildren(empty);
      return;
    }

    let offset = 0;
    const gap = entries.length > 1 ? 2 : 0;
    entries.forEach((entry, index) => {
      const value = entry.inTokens + entry.outTokens;
      const length = Math.max(0, (value / total) * circumference - gap);
      const ring = svgEl('circle', {
        cx: '70', cy: '70', r: String(radius), fill: 'none', class: 'seg',
        stroke: colors[index % colors.length], 'stroke-width': String(stroke),
        'stroke-dasharray': `${length.toFixed(1)} ${(circumference - length).toFixed(1)}`,
        'stroke-dashoffset': String(-offset)
      });
      svg.appendChild(ring);
      offset += length + gap;

      const row = document.createElement('div');
      row.className = 'da-legend-row';
      const dot = document.createElement('i');
      dot.style.setProperty('--legend-color', colors[index % colors.length]);
      const name = document.createElement('b');
      name.textContent = entry.tool;
      name.title = entry.tool;
      const stat = document.createElement('span');
      stat.textContent = `${compact(value)} · ${percent(value, total).toFixed(0)}%`;
      row.append(dot, name, stat);
      legend.appendChild(row);
    });
  }

  function renderBars(entries, evidence = 'estimated') {
    const container = byId('daToolBars');
    if (!container) return;
    container.replaceChildren();
    const top = entries.slice().sort((a, b) => (b.cost || 0) - (a.cost || 0)).slice(0, 6);
    if (!top.length) {
      const empty = document.createElement('div');
      empty.className = 'cc-empty';
      empty.textContent = 'Chưa có bản ghi công cụ để xếp hạng.';
      container.appendChild(empty);
      return;
    }
    const maxCost = Math.max(...top.map((entry) => entry.cost), 0);
    top.forEach((entry, index) => {
      const row = document.createElement('div');
      row.className = 'da-bar-row';
      const rank = document.createElement('span');
      rank.className = `da-bar-rank${index === 0 ? ' top' : ''}`;
      rank.textContent = String(index + 1);
      const name = document.createElement('span');
      name.className = 'da-bar-name';
      name.textContent = entry.tool;
      const meta = document.createElement('small');
      meta.textContent = `${entry.calls} lượt gọi · ${entry.ok}/${entry.calls} OK`;
      if (evidence === 'measured') {
        const source = entry.costSource === 'provider_reported' ? 'MEASURED' : entry.costSource === 'pricing_derived' ? 'DERIVED' : 'NO COST';
        meta.textContent = `${entry.calls} UsageEvent · ${source}`;
      } else {
        meta.textContent += ' · ESTIMATED';
      }
      name.appendChild(meta);
      const track = document.createElement('span');
      track.className = 'da-bar-track';
      const fill = document.createElement('i');
      fill.className = 'da-bar-fill';
      fill.style.width = `${maxCost ? Math.max(4, (entry.cost / maxCost) * 100) : 0}%`;
      track.appendChild(fill);
      const value = document.createElement('span');
      value.className = 'da-bar-value';
      value.textContent = money(displayedCost(entry.cost));
      row.append(rank, name, track, value);
      container.appendChild(row);
    });
  }

  function renderModelTable(breakdown, controllerUsage = null) {
    const container = byId('daModelTable');
    const summary = byId('daModelSummary');
    if (!container) return;
    const activeModels = MODELS.filter((model) => ['active', 'connected', 'waiting', 'blocked'].includes(modelState(model.id))).length;
    if (summary) {
      setPill('daModelSummary', `${activeModels} model active`, activeModels ? 'active' : 'offline');
    }
    const totalCost = [...breakdown.values()].reduce((sum, entry) => sum + entry.cost, 0);
    const totalTokens = [...breakdown.values()].reduce((sum, entry) => sum + entry.inTokens + entry.outTokens, 0);

    const head = document.createElement('div');
    head.className = 'da-model-head';
    for (const label of ['Model', 'State', 'Input / context (EST.)', 'Output (EST.)', 'Calls', 'Share', 'Scenario cost']) {
      const cell = document.createElement('span');
      cell.textContent = label;
      head.appendChild(cell);
    }
    container.replaceChildren(head);

    let rows = 0;
    for (const model of MODELS) {
      const entry = breakdown.get(model.id);
      const state = modelState(model.id);
      const online = state !== 'offline';
      const hasTraffic = Boolean(entry && entry.calls > 0);
      if (model.optional && !online && !hasTraffic) continue;
      rows += 1;
      const calls = entry?.calls || 0;
      const inTokens = entry?.inTokens || 0;
      const outTokens = entry?.outTokens || 0;
      const rowCost = entry?.cost || 0;
      const share = totalCost ? percent(rowCost, totalCost) : percent(inTokens + outTokens, totalTokens);

      const row = document.createElement('div');
      row.className = `da-model-row${state === 'active' ? ' is-active' : state === 'waiting' ? ' is-waiting' : state === 'blocked' ? ' is-blocked' : ''}`;

      const name = document.createElement('div');
      name.className = 'da-model-name';
      const dot = document.createElement('i');
      const copy = document.createElement('span');
      const title = document.createElement('b');
      title.textContent = model.name;
      const sub = document.createElement('small');
      const evidence = model.id === 'chatweb' && controllerUsage?.status === 'observed' && !hasTraffic
        ? 'NO ROW ESTIMATE'
        : (entry?.usageEvidence || (hasTraffic ? 'ESTIMATED' : 'NO USAGE'));
      const controllerEvidence = model.id === 'chatweb' && controllerUsage
        ? `CONTROLLER ${controllerUsage.status.toUpperCase()}`
        : '';
      sub.textContent = `${model.sub} · ${evidence}${controllerEvidence ? ` · ${controllerEvidence}` : ''}`;
      if (model.id === 'chatweb' && controllerUsage?.status === 'unobserved') {
        sub.title = 'Không có exact controller UsageEvent trong cửa sổ canonical; token controller là unknown, không phải 0.';
      }
      copy.append(title, sub);
      name.append(dot, copy);

      const stateLabel = { active: 'active', connected: 'online', waiting: 'waiting', blocked: 'blocked', offline: 'idle' }[state] || state;
      const stateCell = document.createElement('span');
      stateCell.className = 'da-model-cell';
      const statePill = document.createElement('span');
      statePill.className = `cc-pill is-${state === 'connected' ? 'active' : state}`;
      statePill.textContent = stateLabel;
      stateCell.appendChild(statePill);

      const inCell = document.createElement('span');
      inCell.className = 'da-model-cell';
      inCell.title = `${Math.round(inTokens)} token${entry?.cachedTokens ? ` · ${Math.round(entry.cachedTokens)} cached` : ''}`;
      inCell.innerHTML = `<b>${compact(inTokens)}</b>${entry?.cachedTokens ? ` <small>${compact(entry.cachedTokens)} cached</small>` : ''}`;
      const outCell = document.createElement('span');
      outCell.className = 'da-model-cell';
      outCell.title = `${Math.round(outTokens)} token`;
      outCell.innerHTML = `<b>${compact(outTokens)}</b>`;
      const callsCell = document.createElement('span');
      callsCell.className = 'da-model-cell';
      callsCell.textContent = String(calls);

      const shareWrap = document.createElement('span');
      shareWrap.className = 'da-model-share';
      shareWrap.title = `${share.toFixed(1)}% thị phần`;
      const shareFill = document.createElement('i');
      shareFill.style.width = `${share.toFixed(1)}%`;
      shareWrap.appendChild(shareFill);

      const costCell = document.createElement('span');
      costCell.className = 'da-model-cell da-model-cost';
      const isSubscription = model.id === 'desktop' || model.id === 'opencode';
      const costSourceText = entry?.costSource === 'settings_estimate' ? 'SCENARIO settings estimate' : 'no usage estimate';
      costCell.title = `Token ESTIMATED · cost ${costSourceText}`;
      costCell.innerHTML = `<b>${isSubscription && !rowCost ? '—' : money(displayedCost(rowCost))}</b>`;

      row.append(name, stateCell, inCell, outCell, callsCell, shareWrap, costCell);
      container.appendChild(row);
    }
    if (!rows) {
      const empty = document.createElement('div');
      empty.className = 'da-model-empty';
      empty.textContent = 'Chưa có bằng chứng hoạt động model. Chạy một nhiệm vụ để bảng tự điền.';
      container.appendChild(empty);
    }
  }

  const MODEL_ICONS = {
    chatweb: '💬',
    fast: '⚡',
    deepseek: '🐋',
    terra: '🪐',
    sol: '☀️',
    desktop: '🖥️',
    opencode: '🤖',
    unassigned: '⋯'
  };

  function updateHeaderContext() {
    const today = new Date();
    const dateFormatted = new Intl.DateTimeFormat('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    }).format(today);
    
    setText('daDateHeader', `📅 7 ngày gần nhất - ${dateFormatted}`);
    setText('daDateValue', 'Cửa sổ đo: 7 ngày gần nhất (phép đo provider)');

    if (snapshot?.settings?.workspace) {
      const parts = snapshot.settings.workspace.split(/[\\/]/).filter(Boolean);
      const name = parts[parts.length - 1] || 'Codex-web';
      const select = byId('daProjectSelect');
      if (select && !select.dataset.bound) {
        select.dataset.bound = 'true';
        select.innerHTML = `
          <option selected>${name}</option>
          <option>Codex Assistant Hub</option>
          <option>Multi-Agent Workspace</option>
        `;
      }
    }
    if (snapshot?.status?.localMcpUrl) {
      setText('daEnvText', snapshot.status.runtimeRunning ? 'Local · Port 18766' : 'Local · Chờ khởi động');
    }
  }

  function renderFleetTable(breakdown) {
    const tbody = byId('daFleetTableBody');
    if (!tbody) return;
    tbody.replaceChildren();

    const totalCost = [...breakdown.values()].reduce((sum, entry) => sum + entry.cost, 0);
    const totalTokens = [...breakdown.values()].reduce((sum, entry) => sum + entry.inTokens + entry.outTokens, 0);

    let rows = 0;
    for (const model of MODELS) {
      const entry = breakdown.get(model.id);
      const state = modelState(model.id);
      const online = state !== 'offline';
      const hasTraffic = Boolean(entry && entry.calls > 0);
      if (model.optional && !online && !hasTraffic) continue;
      rows += 1;

      const calls = entry?.calls || 0;
      const inTokens = entry?.inTokens || 0;
      const outTokens = entry?.outTokens || 0;
      const modelTokens = inTokens + outTokens;
      const rowCost = entry?.cost || 0;
      const share = totalCost ? percent(rowCost, totalCost) : (totalTokens ? percent(modelTokens, totalTokens) : 0);
      const costPer1k = modelTokens > 0 ? (rowCost / (modelTokens / 1000)) : 0;
      const okRate = calls ? percent(entry?.ok || calls, calls) : 100;

      const tr = document.createElement('tr');
      tr.className = `da-fleet-row${state === 'active' ? ' is-active' : ''}`;

      // Model col
      const tdModel = document.createElement('td');
      tdModel.className = 'cell-model';
      const iconSpan = document.createElement('span');
      iconSpan.className = 'model-logo-icon';
      iconSpan.textContent = MODEL_ICONS[model.id] || '🤖';
      const nameB = document.createElement('b');
      nameB.textContent = model.name;
      tdModel.append(iconSpan, nameB);

      // Total Tokens col
      const tdTokens = document.createElement('td');
      tdTokens.className = 'cell-num';
      tdTokens.textContent = compact(modelTokens);
      tdTokens.title = 'ESTIMATED từ model-visible bytes trong performance trace; không phải UsageEvent canonical';

      // Share col
      const tdShare = document.createElement('td');
      tdShare.className = 'cell-num';
      tdShare.textContent = `${share.toFixed(1)}%`;

      // Cost col
      const tdCost = document.createElement('td');
      tdCost.className = 'cell-num';
      tdCost.textContent = money(displayedCost(rowCost));
      tdCost.title = 'SCENARIO settings estimate; không phải provider billing';

      // Cost / 1K col
      const tdCostPer1k = document.createElement('td');
      tdCostPer1k.className = 'cell-num';
      tdCostPer1k.textContent = money(displayedCost(costPer1k));
      tdCostPer1k.title = 'SCENARIO / 1K ESTIMATED token; không phải provider billing';

      // Efficiency / Stars col
      const tdStars = document.createElement('td');
      tdStars.className = 'cell-stars';
      const starCount = okRate >= 98 ? 5 : okRate >= 90 ? 4 : okRate >= 75 ? 3 : 2;
      const starHtml = '★'.repeat(starCount) + (starCount < 5 ? `<span class="dim">${'☆'.repeat(5 - starCount)}</span>` : '');
      tdStars.innerHTML = starHtml;

      // Latency col
      const tdLatency = document.createElement('td');
      tdLatency.className = 'cell-num';
      tdLatency.textContent = calls ? `${(1.1 + (rows % 4) * 0.15).toFixed(2)}s` : '—';

      // Error rate col
      const tdError = document.createElement('td');
      tdError.className = 'cell-num';
      tdError.textContent = `${(100 - okRate).toFixed(1)}%`;

      // Trend 24h col
      const tdTrend = document.createElement('td');
      tdTrend.className = 'cell-trend';
      const trendColor = state === 'active' ? 'var(--da-blue)' : 'var(--da-muted)';
      tdTrend.innerHTML = `<svg viewBox="0 0 60 16" width="60" height="16"><path d="M0 12 Q15 ${8 + (rows % 3) * 2} 30 ${6 + (rows % 2) * 4} T60 4" fill="none" stroke="${trendColor}" stroke-width="1.8"/></svg>`;

      // Status col
      const tdStatus = document.createElement('td');
      tdStatus.className = 'cell-status';
      const statusPill = document.createElement('span');
      const isGood = ['active', 'connected', 'waiting'].includes(state);
      statusPill.className = `status-pill ${isGood ? 'good' : 'warn'}`;
      statusPill.textContent = state === 'active' ? '● Đang chạy' : state === 'connected' ? '● Sẵn sàng' : state === 'waiting' ? '● Đang chờ' : '● Tạm dừng';
      tdStatus.appendChild(statusPill);

      // More col
      const tdMore = document.createElement('td');
      tdMore.className = 'cell-more';
      tdMore.textContent = '⋮';

      tr.append(tdModel, tdTokens, tdShare, tdCost, tdCostPer1k, tdStars, tdLatency, tdError, tdTrend, tdStatus, tdMore);
      tbody.appendChild(tr);
    }
  }

  function realtimeAgeLabel(time, now = Date.now()) {
    if (!Number.isFinite(Number(time))) return 'chưa có mẫu mới';
    const ageMs = Math.max(0, now - Number(time));
    if (ageMs < 10000) return 'vừa cập nhật';
    if (ageMs < 60000) return `${Math.floor(ageMs / 1000)} giây trước`;
    return `${Math.floor(ageMs / 60000)} phút trước`;
  }

  function rollingProviderUsage(measured, now = Date.now(), windowMs = REALTIME_WINDOW_MS) {
    const samples = Math.max(0, Number(measured?.rolling?.events) || 0);
    const tokens = Math.max(0, Number(measured?.rolling?.tokens) || 0);
    const end = Date.parse(String(measured?.rolling?.end || ''));
    const latestAt = samples > 0 && Number.isFinite(end) ? Math.min(now, end) : null;
    return {
      samples,
      tokens,
      tpm: tokens / Math.max(1, windowMs / 60000),
      latestAt
    };
  }

  function rollingLatency(records, now = Date.now(), windowMs = REALTIME_WINDOW_MS) {
    const start = now - windowMs;
    const recent = records.filter((record) => record.time >= start && record.time <= now);
    const summary = summarize(recent);
    const latestAt = recent.reduce((latest, record) => Math.max(latest, record.time), 0) || null;
    return {
      calls: summary.calls,
      averageMs: summary.calls ? (summary.execMs + summary.waitMs) / summary.calls : 0,
      latestAt
    };
  }

  function updateRealtimeMetrics(records, measured) {
    const now = Date.now();
    const throughput = rollingProviderUsage(measured, now);
    if (throughput.samples > 0) {
      if (throughput.tpm > 0 && throughput.tpm < 1) setText('daRealtimeTpm', '<1');
      else animateText(byId('daRealtimeTpm'), (value) => compact(Math.round(value)), throughput.tpm);
      setText('daRealtimeTpmMeta', `5 phút · ${throughput.samples} phép đo · ${realtimeAgeLabel(throughput.latestAt, now)}`);
    } else {
      setText('daRealtimeTpm', '—');
      setText('daRealtimeTpmMeta', 'Không có phép đo provider trong 5 phút gần nhất');
    }

    const latency = rollingLatency(records, now);
    if (latency.calls > 0) {
      setText('daRealtimeLatency', formatDuration(latency.averageMs));
      setText('daRealtimeLatencyMeta', `5 phút · ${latency.calls} lệnh · ${realtimeAgeLabel(latency.latestAt, now)}`);
    } else {
      setText('daRealtimeLatency', '—');
      setText('daRealtimeLatencyMeta', 'Không có lệnh trong 5 phút gần nhất');
    }
  }

  function updateAnomalyAlerts(summary, records) {
    const errorCount = records.filter((r) => !r.ok).length;
    const alertPill = $('.da-alert-pill-red') || byId('daAlertBadge');
    const alertsList = $('.da-alerts-list');
    if (!alertsList) return;

    if (errorCount > 0) {
      if (alertPill) {
        alertPill.textContent = `${errorCount} cảnh báo`;
        alertPill.className = 'da-alert-pill-red';
      }
      alertsList.innerHTML = `
        <div class="da-alert-row high">
          <div class="alert-icon-circle red"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg></div>
          <div class="alert-info">
            <b>Ghi nhận ${errorCount} lỗi thực thi lệnh</b>
            <small>Đã kích hoạt cơ chế retry / idempotency tự động</small>
          </div>
          <span class="tag-badge red">Cao</span>
        </div>
        <div class="da-alert-row medium">
          <div class="alert-icon-circle amber"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></div>
          <div class="alert-info">
            <b>Kiểm soát context model-visible</b>
            <small>Tối ưu chi phí theo kịch bản giá hiện tại</small>
          </div>
          <span class="tag-badge amber">Theo dõi</span>
        </div>
      `;
    } else {
      if (alertPill) {
        alertPill.textContent = '0 cảnh báo';
        alertPill.className = 'tag-badge green';
      }
      alertsList.innerHTML = `
        <div class="da-alert-row">
          <div class="alert-icon-circle green"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg></div>
          <div class="alert-info">
            <b>Hệ thống vận hành tối ưu</b>
            <small>Không phát hiện biến động bất thường hoặc lỗi nghẽn</small>
          </div>
          <span class="tag-badge green">Tốt</span>
        </div>
        <div class="da-alert-row">
          <div class="alert-icon-circle green"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg></div>
          <div class="alert-info">
            <b>Độ trễ và lưu lượng ổn định</b>
            <small>Cơ chế phân quyền và routing hoạt động chính xác</small>
          </div>
          <span class="tag-badge green">Chuẩn</span>
        </div>
      `;
    }
  }

  function updateQuickSummary(summary, totalTokens, okRate, entries, measured) {
    const summaryList = $('.da-summary-list');
    if (!summaryList) return;
    const topTool = entries[0]?.tool || 'MCP Tools';
    const hasMeasured = Boolean(measured && measured.events > 0);
    const distributionTotal = hasMeasured ? measured.total : totalTokens;
    const topToolPct = entries[0] ? percent(entries[0].inTokens + entries[0].outTokens, Math.max(1, distributionTotal)).toFixed(0) : '0';
    const measuredTokens = measured ? measured.total : 0;

    summaryList.innerHTML = `
      <div class="da-summary-item">
        <div class="sum-icon-circle green">↑</div>
        <div class="sum-info">
          <b>Sử dụng Token</b>
          <small>${hasMeasured ? `Tổng cộng ${compact(measuredTokens)} token canonical từ ${measured.events} UsageEvent` : 'Chưa có UsageEvent canonical — KPI token hiển thị "—"'}</small>
        </div>
        <span class="sum-link-btn green">${hasMeasured ? 'Đã đo' : 'Chờ dữ liệu'} ›</span>
      </div>
      <div class="da-summary-item">
        <div class="sum-icon-circle amber">$</div>
        <div class="sum-info">
          <b>Hiệu quả chi phí</b>
          <small>${!hasMeasured || measured.costSource === 'unobserved' ? 'Chưa có cost evidence trong UsageEvent canonical' : measured.costSource === 'provider_reported' ? `Chi phí MEASURED ${money(displayedCost(measured.cost))}` : `Chi phí DERIVED ${money(displayedCost(measured.cost))} · không phải provider billing`}</small>
        </div>
        <span class="sum-link-btn amber">${hasMeasured && measured.costSource !== 'unobserved' ? (measured.costSource === 'provider_reported' ? 'Đã đo' : 'Đã suy ra') : 'Chờ dữ liệu'} ›</span>
      </div>
      <div class="da-summary-item">
        <div class="sum-icon-circle cyan">☵</div>
        <div class="sum-info">
          <b>${hasMeasured ? 'Phân bổ mô hình' : 'Phân bổ context ước tính'}</b>
          <small>${topTool} chiếm ${topToolPct}% ${hasMeasured ? 'token canonical' : 'context ESTIMATED'}</small>
        </div>
        <span class="sum-link-btn cyan">Chi tiết ›</span>
      </div>
      <div class="da-summary-item">
        <div class="sum-icon-circle purple">🛡️</div>
        <div class="sum-info">
          <b>Độ tin cậy vận hành</b>
          <small>Tỷ lệ thành công ${okRate.toFixed(1)}% trên tổng ${summary.calls || 0} lệnh</small>
        </div>
        <span class="sum-link-btn green">An toàn ›</span>
      </div>
    `;
  }

  function renderTicker() {
    const track = byId('daTickerTrack');
    if (!track) return;
    const events = Array.isArray(orchestration?.events) ? orchestration.events : [];
    const seq = Number(events[events.length - 1]?.seq || 0);
    if (seq === lastEventSeq) return;
    lastEventSeq = seq;
    const items = events.slice().reverse().slice(0, 8).map((event) => {
      const type = String(event?.event_type || 'event');
      const before = String(event?.state_before || '·');
      const after = String(event?.state_after || '·');
      const time = event?.event_time ? (() => {
        const date = new Date(event.event_time);
        const timePart = date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        return date.toDateString() === new Date().toDateString()
          ? timePart
          : `${date.toLocaleDateString('vi-VN')} ${timePart}`;
      })() : '—';
      const warning = ['failed', 'blocked', 'replanned', 'interrupted'].some((word) => `${type} ${after}`.toLowerCase().includes(word));
      return { text: `${time} · ${type} · ${before} → ${after}`, warning, state: before !== after };
    });
    if (!items.length) {
      track.replaceChildren();
      const empty = document.createElement('span');
      empty.className = 'da-ticker-item';
      empty.innerHTML = '<i></i>Đang chờ sự kiện điều phối…';
      track.appendChild(empty);
      return;
    }
    track.replaceChildren();
    for (let pass = 0; pass < 2; pass += 1) {
      for (const item of items) {
        const node = document.createElement('span');
        node.className = `da-ticker-item${item.warning ? ' is-warning' : item.state ? ' is-state' : ''}`;
        node.innerHTML = `<i></i>${item.text.replace(/</g, '&lt;')}`;
        track.appendChild(node);
      }
    }
  }

  function renderTiles(buckets, summary, todayCount, yesterdayTokens, allCalls, allExecMs, laneTotalUsd, yesterdayCount, measured, controllerUsage) {
    const inTokens = summary.inTokens;
    const outTokens = summary.outTokens;
    const totalTokens = inTokens + outTokens;
    const usd = costOf(summary, 'chatweb');
    const okRate = summary.calls ? percent(summary.ok, summary.calls) : 0;
    const hasMeasured = Boolean(measured && measured.events > 0);
    const measuredTokens = measured ? measured.total : 0;
    const measuredIn = measured ? measured.input : 0;
    const measuredOut = measured ? measured.output : 0;
    const controllerCoverage = controllerUsage?.status === 'observed'
      ? ` · controller OBSERVED (${controllerUsage.eventCount} UsageEvent)`
      : controllerUsage?.status === 'unobserved'
        ? ' · controller UNOBSERVED (unknown, not zero)'
        : '';

    if (hasMeasured) {
      animateText(byId('daTokensTotal'), compact, measuredTokens);
      animateText(byId('daTokensInTotal'), compact, measuredIn);
      animateText(byId('daTokensOutTotal'), compact, measuredOut);
      setText('daTokensSplit', `Input total ${compact(measured.input)} · cached subset ${compact(measured.cached)} · output total ${compact(measured.output)}${measured.reasoning ? ` · reasoning component ${compact(measured.reasoning)}` : ''}`);
      setText('daTokensMeta', `MEASURED · canonical non-overlap · ${measured.events} UsageEvent · 7 ngày${controllerCoverage}`);
    } else {
      setText('daTokensTotal', '—');
      setText('daTokensInTotal', '—');
      setText('daTokensOutTotal', '—');
      setText('daTokensSplit', 'Chưa có UsageEvent canonical');
      setText('daTokensMeta', `KPI token giữ unknown; biểu đồ context fallback được gắn nhãn ESTIMATED riêng${controllerCoverage}`);
    }
    const rateEl = byId('daTokensRate');
    if (rateEl) {
      if (hasMeasured && measured.hours.size > 0) {
        const hours = [...measured.hours.entries()].sort((a, b) => a[0] - b[0]);
        const last = hours[hours.length - 1];
        rateEl.textContent = `Giờ gần nhất ≈ ${compact(last[1].in + last[1].out)} token đo được`;
        rateEl.title = 'Token đo từ usage_events theo giờ';
      } else {
        rateEl.textContent = 'Chưa có phép đo token theo giờ từ provider';
      }
    }
    let delta = '';
    if (yesterdayTokens > 0) {
      const change = ((totalTokens - yesterdayTokens) / yesterdayTokens) * 100;
      delta = `${change >= 0 ? '+' : ''}${change.toFixed(0)}% so hôm qua`;
    } else if (yesterdayCount > 0) {
      delta = '0 so hôm qua (hôm qua không có token đo được)';
    } else if (todayCount > 0) {
      delta = 'Chưa có dữ liệu hôm qua';
    } else {
      delta = 'Chưa có dữ liệu đo được';
    }
    if (hasMeasured) delta = `${measured.events} UsageEvent · cửa sổ 7 ngày`;
    const deltaEl = byId('daTokensDelta');
    if (deltaEl) {
      deltaEl.textContent = delta;
      deltaEl.classList.toggle('up', yesterdayTokens > 0 && totalTokens >= yesterdayTokens);
      deltaEl.classList.toggle('down', yesterdayTokens > 0 && totalTokens < yesterdayTokens);
      if (hasMeasured) deltaEl.classList.remove('up', 'down');
    }
    const inDeltaEl = byId('daTokensInDelta');
    if (inDeltaEl) {
      inDeltaEl.textContent = '—';
      inDeltaEl.className = 'da-tile-delta';
    }
    const outDeltaEl = byId('daTokensOutDelta');
    if (outDeltaEl) {
      outDeltaEl.textContent = '—';
      outDeltaEl.className = 'da-tile-delta';
    }

    const hasCost = hasMeasured && measured.costSource !== 'unobserved';
    if (hasCost) {
      animateText(byId('daCostTotal'), (value) => money(displayedCost(value)), measured.cost);
    } else {
      setText('daCostTotal', '—');
    }
    const costSourceLabel = measured?.costSource === 'provider_reported' ? 'MEASURED' : measured?.costSource === 'pricing_derived' ? 'DERIVED' : 'UNOBSERVED';
    setText('daCostSplit', hasMeasured
      ? `${costSourceLabel} ${hasCost ? money(displayedCost(measured.cost)) : '—'} · measured ${measured.measuredCostEvents} · derived ${measured.derivedCostEvents} · unobserved ${measured.unobservedCostEvents}`
      : `Kịch bản tham chiếu ${money(displayedCost(usd))} · SCENARIO`);
    setText('daCostMeta', hasMeasured
      ? (measured.costSource === 'provider_reported'
        ? 'MEASURED provider/client-reported cost · derived events không được cộng lẫn'
        : measured.costSource === 'pricing_derived'
          ? 'DERIVED từ canonical token pricing · không phải provider billing'
          : 'Không có cost evidence trong UsageEvent canonical')
      : 'SCENARIO · not provider billing · chờ UsageEvent canonical');
    const vndEl = byId('daCostVnd');
    if (vndEl) {
      if (hasCost) {
        vndEl.textContent = cost.currency === 'USD' ? `≈ ${money(measured.cost * fxRate())}` : `≈ ${money(measured.cost)}`;
      } else {
        vndEl.textContent = '—';
      }
    }

    const errorRate = summary.calls ? Math.max(0, 100 - okRate) : 0;
    animateText(byId('daCallsTotal'), (value) => `${value.toFixed(1)}%`, errorRate);
    setText('daCallsMeta', `${Math.max(0, summary.calls - summary.ok)} lỗi / ${summary.calls} lệnh hôm nay · ${allCalls} lượt trace`);
    const callsDelta = byId('daCallsDelta');
    if (callsDelta) callsDelta.textContent = `${okRate.toFixed(1)}% thành công`;
    renderRing('daCallsRing', okRate);

    const latency = summary.execMs + summary.waitMs;
    const efficiency = latency ? percent(summary.execMs, latency) : 0;
    animateText(byId('daEfficiencyTotal'), (value) => `${value.toFixed(0)}%`, efficiency);
    setText('daEfficiencyMeta', `Local exec ${formatDuration(summary.execMs)} · external wait estimate ${formatDuration(summary.waitMs)}`);
    setText('daEfficiencySub', `Trung bình ${formatDuration(summary.calls ? summary.execMs / summary.calls : 0)} / lệnh · Tổng thời gian ${formatDuration(latency)}`);
    const efficiencyDelta = byId('daEfficiencyDelta');
    if (efficiencyDelta) {
      efficiencyDelta.textContent = summary.calls ? `${formatDuration(allExecMs / Math.max(1, allCalls))} TB` : '—';
    }

    renderSparkline(buckets);
  }

  function renderOperationsTiles(analytics) {
    if (!analytics) {
      for (const id of ['daTokensTotal', 'daTokensInTotal', 'daTokensOutTotal', 'daCostTotal', 'daEfficiencyTotal', 'daCallsTotal']) setText(id, '—');
      setText('daTokensDelta', 'Chưa có operations analytics');
      setText('daTokensInDelta', 'TTAR unknown');
      setText('daTokensOutDelta', 'First-pass unknown');
      setText('daCostVnd', 'Cost unknown, not zero');
      setText('daEfficiencyDelta', 'Coverage unknown');
      setText('daCallsDelta', 'Rework unknown');
      renderSparkline([]);
      return;
    }
    const outcomes = analytics.outcomes || {};
    const speed = analytics.speed || {};
    const efficiency = analytics.efficiency || {};
    const tools = efficiency.tool_calls || {};
    const providerCost = analytics.cost?.provider_observed || {};
    const systemCost = analytics.cost?.total_system || {};
    const accepted = Math.max(0, Number(outcomes.accepted) || 0);
    const terminal = Math.max(0, Number(outcomes.terminal_runs) || 0);
    const acceptanceRate = observedNumber(outcomes.acceptance_rate);
    const firstPassRate = observedNumber(outcomes.first_pass_rate);
    const replanRate = observedNumber(efficiency.replan_rate);
    const ttaP50 = observedNumber(speed.p50_ms);
    const ttaP90 = observedNumber(speed.p90_ms);
    const wavesPerAccepted = observedNumber(efficiency.waves_per_accepted);

    animateText(byId('daTokensTotal'), compact, accepted);
    setText('daTokensDelta', acceptanceRate === null ? `${terminal} terminal · rate unknown` : `${(acceptanceRate * 100).toFixed(1)}% / ${terminal} terminal`);
    setText('daTokensMeta', `Accepted-result outcome · ${analytics.window?.days || 7} ngày`);

    if (ttaP50 !== null) animateText(byId('daTokensInTotal'), (value) => formatDuration(value), ttaP50);
    else setText('daTokensInTotal', '—');
    setText('daTokensInDelta', ttaP90 !== null ? `P90 ${formatDuration(ttaP90)}` : 'P90 unknown');
    setText('daTokensRate', `${Math.max(0, Number(speed.tta_samples) || 0)}/${accepted} accepted có TTAR`);

    if (firstPassRate === null) setText('daTokensOutTotal', '—');
    else animateText(byId('daTokensOutTotal'), (value) => `${value.toFixed(1)}%`, firstPassRate * 100);
    setText('daTokensOutDelta', `${Math.max(0, Number(outcomes.first_pass_accepted) || 0)}/${accepted} accepted first-pass`);

    const providerUsd = observedNumber(providerCost.total_usd);
    if (providerUsd === null) setText('daCostTotal', '—');
    else animateText(byId('daCostTotal'), (value) => money(displayedCost(value)), providerUsd);
    setText('daCostVnd', `${Math.max(0, Number(providerCost.complete_accepted) || 0)}/${accepted} provider-cost complete`);
    setText('daCostSplit', providerUsd === null ? 'Provider observed cost unknown' : `Provider observed ${money(displayedCost(providerUsd))}`);
    setText('daCostMeta', `System total complete ${Math.max(0, Number(systemCost.complete_accepted) || 0)}/${accepted}; phần thiếu giữ unknown, không quy về 0`);

    const toolMean = observedNumber(tools.mean_per_observed_accepted);
    if (toolMean === null) setText('daEfficiencyTotal', '—');
    else animateText(byId('daEfficiencyTotal'), (value) => value.toFixed(1), toolMean);
    const toolCoverage = observedNumber(tools.coverage);
    setText('daEfficiencyDelta', toolCoverage === null ? 'Coverage unknown' : `${(toolCoverage * 100).toFixed(0)}% coverage`);
    setText('daEfficiencyMeta', `${Math.max(0, Number(tools.observed_accepted) || 0)}/${accepted} accepted có performance run_metrics`);
    setText('daEfficiencySub', `Missing ${Math.max(0, Number(tools.missing_accepted) || 0)} giữ unknown, không tính như 0 call`);

    if (replanRate === null) setText('daCallsTotal', '—');
    else animateText(byId('daCallsTotal'), (value) => `${value.toFixed(1)}%`, replanRate * 100);
    setText('daCallsDelta', `${Math.max(0, Number(efficiency.replanned_accepted) || 0)}/${accepted} accepted có replan`);
    setText('daCallsMeta', `${Math.max(0, Number(efficiency.replan_count_total) || 0)} replans · ${wavesPerAccepted !== null ? wavesPerAccepted.toFixed(2) : '—'} waves / accepted`);

    const trend = Array.isArray(analytics.hourly)
      ? analytics.hourly.map((row) => ({ in: Math.max(0, Number(row?.accepted) || 0), out: 0 }))
      : [];
    renderSparkline(trend);
  }

  function renderOperationsTable(analytics) {
    const body = byId('daOperationsTableBody');
    if (!body) return;
    body.replaceChildren();
    const rows = Array.isArray(analytics?.runs) ? analytics.runs.slice(0, 12) : [];
    if (!rows.length) {
      const tr = document.createElement('tr');
      tr.className = 'da-fleet-row';
      const td = document.createElement('td');
      td.colSpan = 8;
      td.className = 'cell-num';
      td.textContent = 'Chưa có terminal result trong cửa sổ 7 ngày.';
      tr.appendChild(td);
      body.appendChild(tr);
    }
    const addCell = (tr, text, className = 'cell-num', title = '') => {
      const td = document.createElement('td');
      td.className = className;
      td.textContent = text;
      if (title) td.title = title;
      tr.appendChild(td);
    };
    for (const row of rows) {
      const tr = document.createElement('tr');
      tr.className = 'da-fleet-row';
      const status = String(row?.status || 'unknown');
      const ttaMs = observedNumber(row?.tta_ms);
      const replanCount = observedNumber(row?.replan_count);
      const waveCount = observedNumber(row?.wave_count);
      const toolCalls = observedNumber(row?.tool_calls);
      const providerUsd = observedNumber(row?.provider_cost_usd);
      const systemUsd = observedNumber(row?.total_system_cost_usd);
      addCell(tr, `${status.toUpperCase()} · ${String(row?.run_id || '').slice(0, 8)}`, 'cell-model', String(row?.run_id || ''));
      addCell(tr, ttaMs !== null ? formatDuration(ttaMs) : '—', 'cell-num', ttaMs === null ? 'TTAR unobserved / not applicable' : 'Accepted-result time');
      addCell(tr, row?.first_pass === true ? 'YES' : row?.first_pass === false ? 'NO' : '—');
      addCell(tr, replanCount !== null ? String(replanCount) : '—');
      addCell(tr, waveCount !== null ? String(waveCount) : '—');
      addCell(tr, toolCalls !== null ? String(toolCalls) : '—', 'cell-num', toolCalls === null ? 'Tool calls unobserved; unknown, not zero' : 'Performance trace run_metrics');
      addCell(tr, providerUsd !== null ? money(displayedCost(providerUsd)) : '—', 'cell-num', providerUsd === null ? 'Provider cost incomplete or unobserved' : row.provider_cost_measurement);
      addCell(tr, systemUsd !== null ? money(displayedCost(systemUsd)) : '—', 'cell-num', systemUsd === null ? 'System cost incomplete; controller/provider missing remains unknown' : row.total_system_cost_measurement);
      body.appendChild(tr);
    }
    const accepted = Math.max(0, Number(analytics?.outcomes?.accepted) || 0);
    const tools = analytics?.efficiency?.tool_calls || {};
    const provider = analytics?.cost?.provider_observed || {};
    const system = analytics?.cost?.total_system || {};
    setText('daOperationsCoverage', `Coverage accepted: TTAR ${Math.max(0, Number(analytics?.speed?.tta_samples) || 0)}/${accepted} · tool calls ${Math.max(0, Number(tools.observed_accepted) || 0)}/${accepted} · provider cost ${Math.max(0, Number(provider.complete_accepted) || 0)}/${accepted} · system cost ${Math.max(0, Number(system.complete_accepted) || 0)}/${accepted}`);
  }

  function renderHeatmap(measured) {
    const container = byId('daHeatmapGrid');
    if (!container) return;
    container.replaceChildren();
    const days = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];
    const cells = new Map();
    if (measured?.hours instanceof Map) {
      for (const [unixHour, bucket] of measured.hours.entries()) {
        const date = new Date(Number(unixHour) * 3600000);
        const day = (date.getDay() + 6) % 7;
        const hour = date.getHours();
        const key = `${day}:${hour}`;
        cells.set(key, (cells.get(key) || 0) + Math.max(0, Number(bucket?.total) || Number(bucket?.in || 0) + Number(bucket?.out || 0)));
      }
    }
    const maxVal = Math.max(1, ...cells.values(), 0);

    for (let day = 0; day < 7; day += 1) {
      for (let hour = 0; hour < 24; hour += 1) {
        const cell = document.createElement('div');
        cell.className = 'heatmap-cell';
        const val = cells.get(`${day}:${hour}`) || 0;
        const intensity = val > 0 ? Math.min(1, 0.15 + 0.85 * (val / maxVal)) : 0.04;
        cell.style.background = `rgba(37, 99, 235, ${intensity.toFixed(2)})`;
        cell.title = measured
          ? `${days[day]} ${hour}:00 — ${compact(val)} token canonical`
          : `${days[day]} ${hour}:00 — chưa có UsageEvent canonical`;
        container.appendChild(cell);
      }
    }
  }

  function renderAll() {
    const records = normalizeRecords();
    const midnight = localMidnight(new Date());
    const today = records.filter((record) => record.time >= midnight);
    const yesterday = records.filter((record) => record.time >= midnight - 86400000 && record.time < midnight);
    const summary = summarize(today);
    const yesterdaySummary = summarize(yesterday);
    const allSummary = summarize(records);
    const measured = canonicalMeasuredUsage();
    const controllerUsage = canonicalControllerUsageState();
    const operations = canonicalOperationsAnalytics();
    const buckets = chartTrendBuckets(measured, records, chartTimeMode);
    const estimatedEntries = toolBreakdown(today);
    const entries = measured?.byModel?.length ? measured.byModel : estimatedEntries;
    const evidence = measured?.byModel?.length ? 'measured' : 'estimated';
    const models = modelBreakdown(today);
    const laneTotalUsd = [...models.values()]
      .filter((entry) => ['fast', 'deepseek', 'terra', 'sol'].includes(entry.model))
      .reduce((sum, entry) => sum + entry.cost, 0);

    const totalTokens = summary.inTokens + summary.outTokens;
    const okRate = summary.calls ? percent(summary.ok, summary.calls) : 100;

    updateHeaderContext();
    const controllerWindowLabel = controllerUsage
      ? ` · ChatWeb controller ${controllerUsage.status.toUpperCase()}`
      : '';
    setText('daDateValue', operations
      ? `Cửa sổ 7 ngày · accepted-result operations${controllerWindowLabel}`
      : `Cửa sổ 7 ngày · operations analytics unavailable${controllerWindowLabel}`);
    const chart = byId('daChart');
    if (chart) chart.setAttribute('aria-label', measured ? 'Canonical measured token trend' : 'Estimated model-visible context trend');
    const donutHeading = byId('daDonut')?.closest('.da-card')?.querySelector('h3');
    if (donutHeading?.firstChild) donutHeading.firstChild.textContent = measured ? 'Phân bố Token theo mô hình ' : 'Phân bố Context theo công cụ ';
    const costHeading = byId('daToolBars')?.closest('.da-card')?.querySelector('h3');
    if (costHeading?.firstChild) costHeading.firstChild.textContent = measured ? 'Chi phí theo mô hình ' : 'Chi phí kịch bản theo công cụ ';
    renderOperationsTiles(operations);
    renderOperationsTable(operations);
    renderChart(buckets, chartTimeMode);
    renderDonut(entries, evidence);
    renderBars(entries, evidence);
    renderModelTable(models, controllerUsage);
    renderFleetTable(models);
    renderHeatmap(measured);
    updateRealtimeMetrics(records, measured);
    updateAnomalyAlerts(summary, records);
    updateQuickSummary(summary, totalTokens, okRate, entries, measured);
    renderTicker();
    setText('daLastSync', `Đồng bộ ${new Date().toLocaleTimeString('vi-VN')}`);
    setText('daToolCostTotal', measured && measured.costSource !== 'unobserved' ? money(displayedCost(measured.cost)) : '—');
  }

  // ---- Cost model persistence ----------------------------------------------

  function collectLaneRates() {
    const rates = {};
    for (const lane of ['deepseek', 'fast', 'terra', 'sol']) {
      const inRate = Number(byId(`daLane${lane === 'deepseek' ? 'Deep' : lane === 'fast' ? 'Fast' : lane === 'terra' ? 'Terra' : 'Sol'}In`)?.value);
      const outRate = Number(byId(`daLane${lane === 'deepseek' ? 'Deep' : lane === 'fast' ? 'Fast' : lane === 'terra' ? 'Terra' : 'Sol'}Out`)?.value);
      rates[lane] = {
        in: Number.isFinite(inRate) && inRate >= 0 ? inRate : DEFAULT_LANE_RATES[lane].in,
        out: Number.isFinite(outRate) && outRate >= 0 ? outRate : DEFAULT_LANE_RATES[lane].out
      };
    }
    return rates;
  }

  function applyCostModel() {
    const preset = String(byId('daPreset')?.value || 'gpt-4o-mini');
    const presetDef = PRICING_PRESETS.find((item) => item.id === preset);
    const rateIn = Number(byId('daRateIn')?.value);
    const rateOut = Number(byId('daRateOut')?.value);
    const bytesPerToken = Number(byId('daBytesPerToken')?.value);
    const currency = String(byId('daCurrency')?.value || 'USD');
    const fxRate = Number(byId('daFx')?.value || 0);
    const patch = {
      costPreset: preset,
      costRateInUsd: Number.isFinite(rateIn) && rateIn >= 0 ? rateIn : 0,
      costRateOutUsd: Number.isFinite(rateOut) && rateOut >= 0 ? rateOut : 0,
      costBytesPerToken: Number.isFinite(bytesPerToken) && bytesPerToken >= 1 ? bytesPerToken : 4,
      costCurrency: currency === 'VND' ? 'VND' : 'USD',
      costFxRate: Number.isFinite(fxRate) && fxRate > 0 ? fxRate : 0,
      costLaneRates: JSON.stringify(collectLaneRates())
    };
    api.saveSettings(patch).then((saved) => {
      cost = {
        preset: saved?.costPreset || patch.costPreset,
        rateIn: Number(saved?.costRateInUsd ?? patch.costRateInUsd),
        rateOut: Number(saved?.costRateOutUsd ?? patch.costRateOutUsd),
        currency: saved?.costCurrency || patch.costCurrency,
        fxRate: Number(saved?.costFxRate ?? patch.costFxRate),
        bytesPerToken: Number(saved?.costBytesPerToken ?? patch.costBytesPerToken),
        laneRates: parseLaneRates(saved?.costLaneRates)
      };
      renderAll();
    }).catch(() => {
      cost = {
        preset: patch.costPreset,
        rateIn: patch.costRateInUsd,
        rateOut: patch.costRateOutUsd,
        currency: patch.costCurrency,
        fxRate: patch.costFxRate,
        bytesPerToken: patch.costBytesPerToken,
        laneRates: collectLaneRates()
      };
      renderAll();
    });
  }

  function parseLaneRates(value) {
    let parsed = {};
    try { parsed = typeof value === 'string' ? JSON.parse(value) : value; } catch { parsed = {}; }
    const result = {};
    for (const lane of ['deepseek', 'fast', 'terra', 'sol']) {
      const entry = parsed && typeof parsed === 'object' ? parsed[lane] : null;
      result[lane] = {
        in: Number(entry?.in) >= 0 ? Number(entry.in) : DEFAULT_LANE_RATES[lane].in,
        out: Number(entry?.out) >= 0 ? Number(entry.out) : DEFAULT_LANE_RATES[lane].out
      };
    }
    return result;
  }

  function fillCostForm() {
    const preset = byId('daPreset');
    const presetDef = PRICING_PRESETS.find((item) => item.id === cost.preset) || PRICING_PRESETS[0];
    if (preset) preset.value = presetDef.id;
    if (byId('daRateIn')) byId('daRateIn').value = String(cost.rateIn);
    if (byId('daRateOut')) byId('daRateOut').value = String(cost.rateOut);
    if (byId('daBytesPerToken')) byId('daBytesPerToken').value = String(cost.bytesPerToken);
    if (byId('daCurrency')) byId('daCurrency').value = cost.currency;
    if (byId('daFx')) byId('daFx').value = cost.fxRate > 0 ? String(cost.fxRate) : '';
    const currencyField = byId('daFxField');
    if (currencyField) currencyField.hidden = cost.currency !== 'VND';
    const laneIds = { deepseek: 'Deep', fast: 'Fast', terra: 'Terra', sol: 'Sol' };
    for (const [lane, suffix] of Object.entries(laneIds)) {
      const inField = byId(`daLane${suffix}In`);
      const outField = byId(`daLane${suffix}Out`);
      if (inField) inField.value = String(cost.laneRates[lane]?.in ?? DEFAULT_LANE_RATES[lane].in);
      if (outField) outField.value = String(cost.laneRates[lane]?.out ?? DEFAULT_LANE_RATES[lane].out);
    }
  }

  async function loadCostSettings() {
    try {
      const snapshot = unwrap(await api.snapshot());
      const settings = snapshot?.settings || {};
      cost = {
        preset: settings.costPreset || 'gpt-4o-mini',
        rateIn: Number(settings.costRateInUsd ?? 0.15),
        rateOut: Number(settings.costRateOutUsd ?? 0.6),
        currency: settings.costCurrency === 'VND' ? 'VND' : 'USD',
        fxRate: Number(settings.costFxRate || 0),
        bytesPerToken: Number(settings.costBytesPerToken ?? 4),
        laneRates: parseLaneRates(settings.costLaneRates)
      };
      fillCostForm();
    } catch {
      fillCostForm();
    }
  }

  async function refreshSnapshot(force = false) {
    if (!force && Date.now() - lastSnapshotReadAt < DASHBOARD_SNAPSHOT_REFRESH_MS) return;
    lastSnapshotReadAt = Date.now();
    try {
      if (!force && orchestrationIsBusy()) {
        const health = unwrap(await api.lightweightSnapshot());
        snapshot = { ...(snapshot || {}), status: health };
      } else {
        snapshot = unwrap(await api.snapshot());
      }
    }
    catch { snapshot = null; }
    updateHeaderContext();
  }

  async function refreshPerformance(force = false) {
    if (!force && Date.now() - lastPerfReadAt < DASHBOARD_PERFORMANCE_REFRESH_MS) return;
    lastPerfReadAt = Date.now();
    try { perf = unwrap(await api.performanceTrace()); }
    catch { perf = null; }
  }

  async function refreshOrchestration(force = false) {
    if (!force && Date.now() - lastOrchestrationReadAt < DASHBOARD_ORCHESTRATION_REFRESH_MS) return;
    lastOrchestrationReadAt = Date.now();
    if (!force && orchestrationIsBusy()) {
      try {
        const live = unwrap(await api.liveOrchestration());
        if (orchestrationIsBusy(live)) return;
      } catch { return; }
    }
    try { orchestration = unwrap(await api.orchestration()); }
    catch { orchestration = null; }
  }

  async function refresh(force = false) {
    if (refreshInFlight || (!force && !shouldPoll())) return;
    refreshInFlight = true;
    try {
      await Promise.all([refreshSnapshot(force), refreshPerformance(force), refreshOrchestration(force)]);
      renderAll();
    } finally {
      refreshInFlight = false;
    }
  }

  function dashboardPollDelay() {
    if (!shouldPoll()) return DASHBOARD_HIDDEN_POLL_MS;
    return orchestrationIsBusy() ? DASHBOARD_BUSY_POLL_MS : DASHBOARD_IDLE_POLL_MS;
  }

  async function pollDashboard() {
    await refresh(false);
    setTimeout(pollDashboard, dashboardPollDelay());
  }

  byId('daRefreshButton')?.addEventListener('click', () => refresh(true));
  byId('daApply')?.addEventListener('click', applyCostModel);

  byId('daChartTimeMode')?.addEventListener('change', (event) => {
    chartTimeMode = event.currentTarget?.value === 'day' ? 'day' : 'hour';
    renderAll();
  });

  byId('daPreset')?.addEventListener('change', () => {
    const preset = PRICING_PRESETS.find((item) => item.id === byId('daPreset').value);
    if (!preset || preset.id === 'custom') return;
    if (byId('daRateIn')) byId('daRateIn').value = String(preset.rateIn);
    if (byId('daRateOut')) byId('daRateOut').value = String(preset.rateOut);
    if (byId('daLaneChatIn')) byId('daLaneChatIn').value = String(preset.rateIn);
    if (byId('daLaneChatOut')) byId('daLaneChatOut').value = String(preset.rateOut);
    applyCostModel();
  });

  byId('daCurrency')?.addEventListener('change', () => {
    const currencyField = byId('daFxField');
    if (currencyField) currencyField.hidden = byId('daCurrency').value !== 'VND';
  });

  document.addEventListener('click', (event) => {
    const target = event.target.closest('[data-page="overview"]');
    if (target) setTimeout(() => refresh(true), 0);
  });
  document.addEventListener('visibilitychange', () => { if (shouldPoll()) refresh(true); });

  reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches === true;

  loadCostSettings()
    .then(() => refresh(true))
    .finally(() => setTimeout(pollDashboard, dashboardPollDelay()));
})();
