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
  const REALTIME_WINDOW_MS = 5 * 60 * 1000;
  const DASHBOARD_WINDOW_HOURS = 7 * 24;
  const DASHBOARD_ANALYTICS_REFRESH_MS = 30000;

  const STATE_RANK = { offline: 0, connected: 1, waiting: 2, blocked: 3, active: 4 };

  let perf = null;
  let orchestration = null;
  let snapshot = null;
  let analyticsSnapshot = null;
  let cost = {
    preset: 'gpt-4o-mini', rateIn: 0.15, rateOut: 0.6, currency: 'USD',
    fxRate: 0, laneRates: { ...DEFAULT_LANE_RATES }
  };
  let analyticsInFlight = null;
  let lastAnalyticsReadAt = 0;
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
    if (typeof value !== 'number' && typeof value !== 'string') return null;
    if (typeof value === 'string' && value.trim() === '') return null;
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
          waitMs: Number(record?.wait_before_ms || 0)
        };
      })
      .filter(Boolean);
  }

  function localMidnight(date) {
    const start = new Date(date);
    start.setHours(0, 0, 0, 0);
    return start.getTime();
  }

  function summarize(records) {
    const result = { calls: 0, ok: 0, requestBytes: 0, responseBytes: 0, modelVisibleBytes: 0, execMs: 0, waitMs: 0 };
    for (const record of records) {
      result.calls += 1;
      if (record.ok) result.ok += 1;
      result.execMs += record.durationMs;
      result.waitMs += record.waitMs;
      // Transport request/response/model-visible bytes are payload telemetry, not token truth.
      result.requestBytes += Math.max(0, Number(record.requestBytes) || 0);
      result.responseBytes += Math.max(0, Number(record.responseBytes) || 0);
      result.modelVisibleBytes += Math.max(0, Number(record.modelVisibleBytes) || 0);
    }
    return result;
  }

  function canonicalControllerUsageState() {
    const analytics = analyticsSnapshot?.usage_analytics;
    if (!analytics || analytics.measurement !== 'canonical_non_overlapping') return null;
    if (analytics.missing_measurement_policy !== 'unknown_not_zero') return null;
    const controller = analytics.controller_usage;
    if (!controller || typeof controller !== 'object') return null;
    if (controller.missing_measurement_policy !== 'unknown_not_zero') return null;
    const status = String(controller.status || '').trim().toLowerCase();
    if (status !== 'observed' && status !== 'unobserved') return null;
    const eventCount = observedNumber(controller.event_count);
    if (eventCount === null) return null;
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
    const analytics = analyticsSnapshot?.operations_analytics;
    if (!analytics || analytics.measurement !== 'accepted_result_operations_v1') return null;
    if (analytics.missing_measurement_policy !== 'unknown_not_zero') return null;
    if (!analytics.outcomes || !analytics.speed || !analytics.efficiency || !analytics.cost) return null;
    return analytics;
  }

  function controllerTokenEstimateState(operations) {
    const projection = operations?.controller_token_estimate;
    if (!projection || typeof projection !== 'object') return null;
    if (projection.missing_measurement_policy !== 'unknown_not_zero') return null;
    const status = String(projection.status || '').trim().toLowerCase();
    const measurement = String(projection.measurement || '').trim().toUpperCase();
    if (!['exact', 'calibrated_estimate', 'context_estimate', 'unknown'].includes(status)) return null;
    if (status === 'calibrated_estimate' && measurement !== 'CALIBRATED_ESTIMATE') return null;
    if (status === 'context_estimate' && measurement !== 'CONTEXT_ESTIMATE') return null;
    const estimate = projection.estimate && typeof projection.estimate === 'object' ? projection.estimate : {};
    return {
      status,
      measurement,
      confidence: String(projection.confidence || 'unknown').trim().toLowerCase(),
      calibrationSamples: observedNumber(projection.calibration_samples),
      exactRuns: observedNumber(projection.exact_runs),
      missingExactRuns: observedNumber(projection.missing_exact_runs),
      p10: observedNumber(estimate.p10_total_tokens ?? estimate.p10_context_tokens),
      p50: observedNumber(estimate.p50_total_tokens ?? estimate.p50_context_tokens),
      p90: observedNumber(estimate.p90_total_tokens ?? estimate.p90_context_tokens),
      notControllerTotal: estimate.not_controller_total === true
    };
  }

  function canonicalMeasuredUsage() {
    const analytics = analyticsSnapshot?.usage_analytics;
    if (!analytics || analytics.measurement !== 'canonical_non_overlapping') return null;
    if (analytics.missing_measurement_policy !== 'unknown_not_zero') return null;
    const overall = analytics.overall && typeof analytics.overall === 'object' ? analytics.overall : {};
    const events = observedNumber(overall.event_count);
    if (events === null || events < 1) return null;
    const usage = overall.usage && typeof overall.usage === 'object' ? overall.usage : {};
    const costStats = overall.cost && typeof overall.cost === 'object' ? overall.cost : {};
    const input = observedNumber(usage.input_total_tokens);
    const cached = observedNumber(usage.input_cached_tokens);
    const output = observedNumber(usage.output_total_tokens);
    const reasoning = observedNumber(usage.output_reasoning_tokens);
    const total = observedNumber(usage.total_tokens);
    if (input === null || output === null || total === null) return null;
    const measuredCostEvents = observedNumber(costStats.measured_event_count);
    const derivedCostEvents = observedNumber(costStats.derived_event_count);
    const unobservedCostEvents = observedNumber(costStats.unobserved_event_count);
    const measuredCost = observedNumber(costStats.measured_usd);
    const derivedCost = observedNumber(costStats.derived_usd);
    const costSource = measuredCostEvents !== null && measuredCost !== null && measuredCostEvents > 0
      ? 'provider_reported'
      : derivedCostEvents !== null && derivedCost !== null && derivedCostEvents > 0
        ? 'pricing_derived'
        : 'unobserved';
    const cost = costSource === 'provider_reported' ? measuredCost : costSource === 'pricing_derived' ? derivedCost : null;
    const hours = new Map();
    let hoursAvailable = Array.isArray(analytics.hourly);
    for (const row of Array.isArray(analytics.hourly) ? analytics.hourly : []) {
      const time = Date.parse(String(row?.hour || ''));
      if (!Number.isFinite(time)) { hoursAvailable = false; continue; }
      const rowUsage = row?.usage && typeof row.usage === 'object' ? row.usage : {};
      const input = observedNumber(rowUsage.input_total_tokens);
      const output = observedNumber(rowUsage.output_total_tokens);
      const total = observedNumber(rowUsage.total_tokens);
      const events = observedNumber(row?.event_count);
      if (input === null || output === null || total === null || events === null) { hoursAvailable = false; continue; }
      hours.set(Math.floor(time / 3600000), { in: input, out: output, total, events });
    }
    const rollingRow = analytics.rolling_5m && typeof analytics.rolling_5m === 'object' ? analytics.rolling_5m : {};
    const rollingUsage = rollingRow.usage && typeof rollingRow.usage === 'object' ? rollingRow.usage : {};
    const rolling = {
      events: observedNumber(rollingRow.event_count),
      tokens: observedNumber(rollingUsage.total_tokens),
      end: String(rollingRow.end || analytics?.window?.end || '')
    };
    const modelRows = Array.isArray(analytics.by_model) ? analytics.by_model : null;
    const modelMap = new Map();
    let byModelStatus = modelRows && modelRows.length ? 'complete' : 'unavailable';
    let byModelCachedComplete = Boolean(modelRows && modelRows.length);
    for (const row of modelRows || []) {
      const model = String(row?.model || row?.model_id || 'unknown').trim() || 'unknown';
      const rowUsage = row?.usage && typeof row.usage === 'object' ? row.usage : {};
      const rowCost = row?.cost && typeof row.cost === 'object' ? row.cost : {};
      const entry = modelMap.get(model) || {
        tool: model, model, calls: 0, ok: 0, inTokens: 0, outTokens: 0, cachedTokens: 0,
        cachedComplete: true, cost: null, costSource: 'unobserved', usageEvidence: 'MEASURED',
        measuredCost: 0, derivedCost: 0, measuredCostEvents: 0, derivedCostEvents: 0
      };
      const calls = observedNumber(row?.event_count);
      const input = observedNumber(rowUsage.input_total_tokens);
      const output = observedNumber(rowUsage.output_total_tokens);
      const cached = observedNumber(rowUsage.input_cached_tokens);
      if (calls === null || input === null || output === null) {
        byModelStatus = 'partial';
        continue;
      }
      entry.calls += calls;
      entry.inTokens += input;
      entry.outTokens += output;
      if (cached === null) {
        entry.cachedComplete = false;
        byModelCachedComplete = false;
      } else if (entry.cachedComplete) {
        entry.cachedTokens += cached;
      }
      const measuredCost = observedNumber(rowCost.measured_usd);
      const derivedCost = observedNumber(rowCost.derived_usd);
      const measuredCostEvents = observedNumber(rowCost.measured_event_count);
      const derivedCostEvents = observedNumber(rowCost.derived_event_count);
      if (measuredCost !== null && measuredCostEvents !== null) {
        entry.measuredCost += measuredCost;
        entry.measuredCostEvents += measuredCostEvents;
      }
      if (derivedCost !== null && derivedCostEvents !== null) {
        entry.derivedCost += derivedCost;
        entry.derivedCostEvents += derivedCostEvents;
      }
      modelMap.set(model, entry);
    }
    for (const entry of modelMap.values()) {
      if (!entry.cachedComplete) {
        entry.cachedTokens = null;
        entry.usageEvidence = 'MEASURED PARTIAL';
      }
      delete entry.cachedComplete;
      if (entry.measuredCostEvents > 0) {
        entry.cost = entry.measuredCost;
        entry.costSource = 'provider_reported';
      } else if (entry.derivedCostEvents > 0) {
        entry.cost = entry.derivedCost;
        entry.costSource = 'pricing_derived';
      }
    }
    if (byModelStatus === 'complete') {
      const coverage = [...modelMap.values()].reduce((summary, entry) => {
        summary.calls += entry.calls;
        summary.input += entry.inTokens;
        summary.output += entry.outTokens;
        return summary;
      }, { calls: 0, input: 0, output: 0 });
      if (coverage.calls !== events || coverage.input !== input || coverage.output !== output) {
        byModelStatus = 'partial';
      }
    }
    return {
      events,
      input,
      cached,
      output,
      reasoning,
      total,
      cost,
      costSource,
      measuredCostEvents,
      derivedCostEvents,
      unobservedCostEvents,
      hours: hoursAvailable ? hours : null,
      rolling,
      byModelStatus,
      byModelCachedComplete,
      byModel: [...modelMap.values()].sort((a, b) => (b.inTokens + b.outTokens) - (a.inTokens + a.outTokens))
    };
  }

  function hourBuckets(records, buckets = 24) {
    void records;
    void buckets;
    return [];
  }

  function hourlyFromStore(buckets = 24) {
    void buckets;
    return null;
  }

  function performanceBuckets(records, count = 24) {
    void records;
    void count;
    return [];
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

  function chartTrendBuckets(measured, mode = chartTimeMode) {
    const hourly = canonicalHourBuckets(measured, DASHBOARD_WINDOW_HOURS) || [];
    return mode === 'day' ? aggregateHourBuckets(hourly, 24) : hourly;
  }

  function toolBreakdown(records) {
    void records;
    return [];
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

  function modelOf(record, lanes = laneWindows(), windows = controllerWindows()) {
    const lane = lanes.find((window) => record.time >= window.start && record.time < window.end);
    if (lane) return lane.lane;
    const window = windows.find((item) => record.time >= item.start && record.time < item.end);
    const owner = window?.owner || '';
    if (owner === 'chatweb' || owner.startsWith('chatweb:')) return 'chatweb';
    if (owner === 'codex-desktop') return 'desktop';
    if (owner === 'opencode') return 'opencode';
    return 'unassigned';
  }

  function modelBreakdown(records) {
    void records;
    return new Map();
  }

  function modelState(modelId) {
    const data = orchestration || {};
    if (modelId === 'chatweb') {
      const client = (Array.isArray(data.clients) ? data.clients : [])
        .find((item) => item?.client_id === 'chatweb' || item?.client_type === 'chatweb');
      if (!client?.online) return 'offline';
      const owner = String(data?.authority?.controller?.owner_client_id || '');
      return owner === 'chatweb' || owner.startsWith('chatweb:') ? 'active' : 'connected';
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
    if (element?.__dashboardAnimationFrame && typeof cancelAnimationFrame === 'function') {
      cancelAnimationFrame(element.__dashboardAnimationFrame);
      element.__dashboardAnimationFrame = null;
    }
    if (!element || reducedMotion || orchestrationIsBusy()) {
      if (element) element.textContent = formatter(next);
      return;
    }
    const from = Number(element.dataset.value) || 0;
    const to = Number(next) || 0;
    if (from === to) {
      element.textContent = formatter(to);
      return;
    }
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
      if (progress < 1) {
        element.__dashboardAnimationFrame = requestAnimationFrame(step);
      } else {
        element.__dashboardAnimationFrame = null;
      }
    };
    element.__dashboardAnimationFrame = requestAnimationFrame(step);
  }

  function setText(id, value) {
    const element = byId(id);
    if (!element) return;
    if (element.__dashboardAnimationFrame && typeof cancelAnimationFrame === 'function') {
      cancelAnimationFrame(element.__dashboardAnimationFrame);
      element.__dashboardAnimationFrame = null;
    }
    delete element.dataset.value;
    element.textContent = String(value ?? '—');
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
    if (!hasData) {
      svg.onmouseleave = null;
      svg.onmousemove = null;
      return;
    }

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
    svg.onmouseleave = clearGuide;
    svg.onmousemove = (event) => {
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
    };
  }

  function renderDonut(entries, breakdownStatus = 'unavailable', cachedComplete = false) {
    const svg = byId('daDonut');
    const legend = byId('daLegend');
    const center = byId('daDonutTotal');
    const sub = byId('daDonutSub');
    const foot = byId('daDonutFoot');
    if (!svg || !legend) return;
    const rows = Array.isArray(entries) ? entries : [];
    const status = breakdownStatus === 'complete' || breakdownStatus === 'partial'
      ? breakdownStatus
      : 'unavailable';
    const total = rows.reduce((sum, entry) => sum + entry.inTokens + entry.outTokens, 0);
    const colors = ['var(--da-in)', 'var(--da-out)', 'var(--da-cost)', '#7c5cff', '#2ba7a0', '#c95b9e'];
    const radius = 54;
    const stroke = 13;
    const circumference = 2 * Math.PI * radius;
    svg.replaceChildren();
    legend.replaceChildren();
    if (status === 'complete') animateText(center, compact, total);
    else setText('daDonutTotal', '—');
    if (sub) {
      sub.textContent = status === 'complete'
        ? (cachedComplete ? 'TOKEN MEASURED' : 'TOKEN MEASURED · CACHED PARTIAL')
        : status === 'partial'
          ? 'TOKEN BREAKDOWN PARTIAL'
          : 'TOKEN BREAKDOWN UNAVAILABLE';
    }
    if (foot) foot.textContent = status === 'complete'
      ? `${rows.length} model`
      : status === 'partial'
        ? `${rows.length} model observed`
        : '— model';
    svg.appendChild(center);
    if (sub) svg.appendChild(sub);
    if (status === 'unavailable') {
      const empty = document.createElement('div');
      empty.className = 'da-chart-empty';
      empty.style.height = 'auto';
      empty.style.minHeight = '170px';
      empty.textContent = 'Phân bổ token theo model chưa khả dụng; dữ liệu thiếu không được tính là 0.';
      legend.replaceChildren(empty);
      return;
    }
    if (status === 'partial') {
      const note = document.createElement('div');
      note.className = 'da-chart-empty';
      note.style.height = 'auto';
      note.textContent = 'Breakdown theo model chỉ có một phần; tổng và tỷ trọng chưa khả dụng.';
      legend.appendChild(note);
      rows.forEach((entry, index) => {
        const value = entry.inTokens + entry.outTokens;
        const row = document.createElement('div');
        row.className = 'da-legend-row';
        const dot = document.createElement('i');
        dot.style.setProperty('--legend-color', colors[index % colors.length]);
        const name = document.createElement('b');
        name.textContent = entry.tool;
        name.title = entry.tool;
        const stat = document.createElement('span');
        stat.textContent = `${compact(value)} đã quan sát`;
        row.append(dot, name, stat);
        legend.appendChild(row);
      });
      return;
    }
    if (!total) {
      const empty = document.createElement('div');
      empty.className = 'da-chart-empty';
      empty.style.height = 'auto';
      empty.style.minHeight = '170px';
      empty.textContent = 'UsageEvent theo model hợp lệ có tổng token = 0.';
      legend.replaceChildren(empty);
      return;
    }

    let offset = 0;
    const gap = entries.length > 1 ? 2 : 0;
    rows.forEach((entry, index) => {
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

  function renderBars(entries) {
    const container = byId('daToolBars');
    if (!container) return;
    container.replaceChildren();
    const top = entries
      .filter((entry) => observedNumber(entry?.cost) !== null)
      .slice()
      .sort((a, b) => (b.cost || 0) - (a.cost || 0))
      .slice(0, 6);
    if (!top.length) {
      const empty = document.createElement('div');
      empty.className = 'cc-empty';
      empty.textContent = 'Chưa có chi phí UsageEvent canonical để xếp hạng.';
      container.appendChild(empty);
      return;
    }
    const maxCost = Math.max(...top.map((entry) => observedNumber(entry.cost) || 0), 0);
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
      const source = entry.costSource === 'provider_reported' ? 'MEASURED' : entry.costSource === 'pricing_derived' ? 'DERIVED' : 'NO COST';
      meta.textContent = `${entry.calls} UsageEvent · ${source}`;
      name.appendChild(meta);
      const track = document.createElement('span');
      track.className = 'da-bar-track';
      const fill = document.createElement('i');
      fill.className = 'da-bar-fill';
      fill.style.width = `${maxCost ? Math.max(4, ((observedNumber(entry.cost) || 0) / maxCost) * 100) : 0}%`;
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
    if (!(breakdown instanceof Map) || breakdown.size === 0) {
      if (summary) setPill('daModelSummary', 'usage unknown', 'waiting');
      const empty = document.createElement('div');
      empty.className = 'da-model-empty';
      empty.textContent = 'Chưa có UsageEvent canonical đủ để gán token/chi phí theo lane; không suy diễn từ bytes.';
      container.replaceChildren(empty);
      return;
    }
    const activeModels = MODELS.filter((model) => ['active', 'connected', 'waiting', 'blocked'].includes(modelState(model.id))).length;
    if (summary) {
      setPill('daModelSummary', `${activeModels} model active`, activeModels ? 'active' : 'offline');
    }
    const totalCost = [...breakdown.values()].reduce((sum, entry) => sum + (observedNumber(entry.cost) || 0), 0);
    const totalTokens = [...breakdown.values()].reduce((sum, entry) => sum + entry.inTokens + entry.outTokens, 0);

    const head = document.createElement('div');
    head.className = 'da-model-head';
    for (const label of ['Model', 'State', 'Input token', 'Output token', 'Calls', 'Share', 'Usage cost']) {
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
      const rowCost = observedNumber(entry?.cost);
      const share = rowCost !== null && totalCost > 0 ? percent(rowCost, totalCost) : percent(inTokens + outTokens, totalTokens);

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
        ? 'NO CANONICAL LANE ROW'
        : (entry?.usageEvidence || (hasTraffic ? 'MEASURED' : 'NO USAGE'));
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
      const costSourceText = entry?.costSource === 'provider_reported'
        ? 'MEASURED provider-reported'
        : entry?.costSource === 'pricing_derived'
          ? 'DERIVED from canonical UsageEvent pricing'
          : 'UNOBSERVED';
      costCell.title = `Canonical UsageEvent token · cost ${costSourceText}`;
      costCell.innerHTML = `<b>${rowCost === null ? '—' : money(displayedCost(rowCost))}</b>`;

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
    if (!snapshot || typeof snapshot !== 'object') return;
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
      setText('daProjectText', name);
    }
    if (snapshot?.status?.localMcpUrl) {
      const running = snapshot.status.runtimeRunning;
      setText('daEnvText', typeof running === 'boolean'
        ? running ? 'Local · Port 18766' : 'Local · Chờ khởi động'
        : 'Local · trạng thái chưa xác nhận');
    }
  }

  function snapshotFreshnessLabel() {
    const status = snapshot?.status;
    if (!status || typeof status !== 'object') return 'Freshness snapshot chưa xác nhận';
    if (status.signalStale === true) return 'Snapshot stale; cần kiểm tra lại';
    const ageMs = observedNumber(status.snapshotAgeMs);
    const observedAt = observedNumber(status.snapshotObservedAtUnixMs);
    if (observedAt !== null && observedAt > 0 && Number.isFinite(new Date(observedAt).getTime())) {
      return `Snapshot receipt ${new Date(observedAt).toLocaleTimeString('vi-VN')}`;
    }
    if (ageMs !== null) return `Snapshot cache ${formatDuration(ageMs)} trước`;
    return 'Freshness snapshot chưa xác nhận';
  }

  function renderFleetTable(breakdown) {
    const tbody = byId('daFleetTableBody');
    if (!tbody) return;
    tbody.replaceChildren();
    if (!(breakdown instanceof Map) || breakdown.size === 0) {
      const tr = document.createElement('tr');
      tr.className = 'da-fleet-row';
      const td = document.createElement('td');
      td.colSpan = 11;
      td.className = 'cell-num';
      td.textContent = 'Token/chi phí theo model chưa có mapping UsageEvent canonical; giữ unknown, không quy đổi từ bytes.';
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }

    const totalCost = [...breakdown.values()].reduce((sum, entry) => sum + (observedNumber(entry.cost) || 0), 0);
    const totalTokens = [...breakdown.values()].reduce((sum, entry) => sum + entry.inTokens + entry.outTokens, 0);

    for (const model of MODELS) {
      const entry = breakdown.get(model.id);
      const state = modelState(model.id);
      const online = state !== 'offline';
      const hasTraffic = Boolean(entry && entry.calls > 0);
      if (model.optional && !online && !hasTraffic) continue;

      const calls = entry?.calls || 0;
      const inTokens = entry?.inTokens || 0;
      const outTokens = entry?.outTokens || 0;
      const modelTokens = inTokens + outTokens;
      const rowCost = observedNumber(entry?.cost);
      const share = rowCost !== null && totalCost > 0 ? percent(rowCost, totalCost) : (totalTokens ? percent(modelTokens, totalTokens) : 0);
      const costPer1k = rowCost !== null && modelTokens > 0 ? (rowCost / (modelTokens / 1000)) : null;
      const okRate = calls ? percent(Math.max(0, Number(entry?.ok) || 0), calls) : null;
      const latencyMs = calls
        ? (Math.max(0, Number(entry?.execMs) || 0) + Math.max(0, Number(entry?.waitMs) || 0)) / calls
        : null;

      const tr = document.createElement('tr');
      tr.className = `da-fleet-row${state === 'active' ? ' is-active' : ''}`;

      const tdModel = document.createElement('td');
      tdModel.className = 'cell-model';
      const iconSpan = document.createElement('span');
      iconSpan.className = 'model-logo-icon';
      iconSpan.textContent = MODEL_ICONS[model.id] || '🤖';
      const nameB = document.createElement('b');
      nameB.textContent = model.name;
      tdModel.append(iconSpan, nameB);

      const tdTokens = document.createElement('td');
      tdTokens.className = 'cell-num';
      tdTokens.textContent = compact(modelTokens);
      tdTokens.title = 'Canonical UsageEvent token total';

      const tdShare = document.createElement('td');
      tdShare.className = 'cell-num';
      tdShare.textContent = `${share.toFixed(1)}%`;

      const tdCost = document.createElement('td');
      tdCost.className = 'cell-num';
      tdCost.textContent = rowCost === null ? '—' : money(displayedCost(rowCost));
      tdCost.title = entry?.costSource === 'provider_reported'
        ? 'MEASURED provider-reported cost'
        : entry?.costSource === 'pricing_derived'
          ? 'DERIVED from canonical UsageEvent token pricing; not provider billing'
          : 'Cost unobserved';

      const tdCostPer1k = document.createElement('td');
      tdCostPer1k.className = 'cell-num';
      tdCostPer1k.textContent = costPer1k === null ? '—' : money(displayedCost(costPer1k));
      tdCostPer1k.title = 'Derived only from canonical UsageEvent token/cost fields; unavailable when canonical evidence is missing';

      const tdStars = document.createElement('td');
      tdStars.className = 'cell-stars';
      tdStars.textContent = okRate === null ? '—' : `${okRate.toFixed(1)}%`;
      tdStars.title = okRate === null ? 'Không có lệnh quan sát được' : 'Tỷ lệ lệnh thành công quan sát được trong performance trace';

      const tdLatency = document.createElement('td');
      tdLatency.className = 'cell-num';
      tdLatency.textContent = latencyMs === null ? '—' : formatDuration(latencyMs);
      tdLatency.title = latencyMs === null ? 'Latency unknown' : 'Observed execution + estimated wait per attributed trace call';

      const tdError = document.createElement('td');
      tdError.className = 'cell-num';
      tdError.textContent = okRate === null ? '—' : `${(100 - okRate).toFixed(1)}%`;

      const tdTrend = document.createElement('td');
      tdTrend.className = 'cell-trend';
      tdTrend.textContent = '—';
      tdTrend.title = 'Chưa có per-model time-series evidence; không nội suy trend 24h.';

      const tdStatus = document.createElement('td');
      tdStatus.className = 'cell-status';
      const statusPill = document.createElement('span');
      const isGood = ['active', 'connected', 'waiting'].includes(state);
      statusPill.className = `status-pill ${isGood ? 'good' : 'warn'}`;
      statusPill.textContent = state === 'active' ? '● Đang chạy' : state === 'connected' ? '● Sẵn sàng' : state === 'waiting' ? '● Đang chờ' : '● Tạm dừng';
      tdStatus.appendChild(statusPill);

      const tdMore = document.createElement('td');
      tdMore.className = 'cell-more';
      tdMore.textContent = '⋮';

      tr.append(tdModel, tdTokens, tdShare, tdCost, tdCostPer1k, tdStars, tdLatency, tdError, tdTrend, tdStatus, tdMore);
      tbody.appendChild(tr);
    }
  }

  function realtimeAgeLabel(time, now = Date.now()) {
    const observedAt = observedNumber(time);
    if (observedAt === null || observedAt > now) return 'freshness chưa xác nhận';
    const ageMs = now - observedAt;
    if (ageMs < 10000) return 'vừa cập nhật';
    if (ageMs < 60000) return `${Math.floor(ageMs / 1000)} giây trước`;
    return `${Math.floor(ageMs / 60000)} phút trước`;
  }

  function rollingProviderUsage(measured, now = Date.now(), windowMs = REALTIME_WINDOW_MS) {
    const samples = observedNumber(measured?.rolling?.events);
    const tokens = observedNumber(measured?.rolling?.tokens);
    const end = Date.parse(String(measured?.rolling?.end || ''));
    const latestAt = samples !== null && tokens !== null && samples > 0 && Number.isFinite(end) && end <= now ? end : null;
    return {
      samples,
      tokens,
      tpm: tokens === null ? null : tokens / Math.max(1, windowMs / 60000),
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
    if (throughput.samples !== null && throughput.tokens !== null && throughput.samples > 0 && throughput.tpm !== null
        && throughput.latestAt !== null && now - throughput.latestAt <= REALTIME_WINDOW_MS) {
      if (throughput.tpm > 0 && throughput.tpm < 1) setText('daRealtimeTpm', '<1');
      else animateText(byId('daRealtimeTpm'), (value) => compact(Math.round(value)), throughput.tpm);
      setText('daRealtimeTpmMeta', `5 phút · ${throughput.samples} phép đo · ${realtimeAgeLabel(throughput.latestAt, now)}`);
    } else {
      setText('daRealtimeTpm', '—');
      setText('daRealtimeTpmMeta', throughput.latestAt !== null && now - throughput.latestAt > REALTIME_WINDOW_MS
        ? 'Phép đo provider đã cũ; chờ cửa sổ 5 phút mới'
        : throughput.samples === 0
          ? 'Không có phép đo provider trong 5 phút gần nhất'
          : 'Phép đo provider hoặc freshness chưa xác nhận');
    }

    const latency = rollingLatency(records, now);
    if (latency.calls > 0) {
      setText('daRealtimeLatency', formatDuration(latency.averageMs));
      setText('daRealtimeLatencyMeta', `5 phút · ${latency.calls} lệnh · ${realtimeAgeLabel(latency.latestAt, now)}`);
    } else {
      setText('daRealtimeLatency', '—');
      setText('daRealtimeLatencyMeta', perf === null || perf === undefined
        ? 'Dữ liệu lệnh chưa khả dụng'
        : 'Không có lệnh trong 5 phút gần nhất');
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
            <small>Theo performance trace hiện có; kiểm tra causal event trước khi kết luận nguyên nhân</small>
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
            <b>Chưa ghi nhận lỗi trong trace hiện tại</b>
            <small>Đây là bằng chứng quan sát được, không phải claim toàn hệ thống đã tối ưu</small>
          </div>
          <span class="tag-badge green">Tốt</span>
        </div>
        <div class="da-alert-row">
          <div class="alert-icon-circle green"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg></div>
          <div class="alert-info">
            <b>Độ trễ và lưu lượng dùng số liệu quan sát</b>
            <small>Trường thiếu evidence giữ unknown thay vì nội suy trạng thái tốt</small>
          </div>
          <span class="tag-badge green">Chuẩn</span>
        </div>
      `;
    }
  }

  function updateQuickSummary(summary, okRate, entries, measured) {
    const summaryList = $('.da-summary-list');
    if (!summaryList) return;
    const topTool = entries[0]?.tool || 'MCP Tools';
    const hasMeasured = Boolean(measured && measured.events > 0);
    const distributionStatus = measured?.byModelStatus || 'unavailable';
    const completeDistribution = hasMeasured && distributionStatus === 'complete' && entries.length > 0;
    const partialDistribution = hasMeasured && distributionStatus === 'partial';
    const distributionTotal = hasMeasured ? measured.total : 0;
    const topToolPct = completeDistribution && entries[0]
      ? percent(entries[0].inTokens + entries[0].outTokens, Math.max(1, distributionTotal)).toFixed(0)
      : null;
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
          <b>${!hasMeasured ? 'Token chưa có phép đo' : completeDistribution ? 'Phân bổ mô hình' : 'Phân bổ mô hình chưa đầy đủ'}</b>
          <small>${!hasMeasured
            ? 'Không suy diễn token từ model-visible bytes'
            : completeDistribution
              ? `${topTool} chiếm ${topToolPct}% token canonical`
              : partialDistribution
                ? 'Breakdown theo model chỉ có một phần; không phát hành tổng/tỷ trọng đầy đủ'
                : 'Breakdown theo model chưa khả dụng; dữ liệu thiếu không được tính là 0'}</small>
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

  function coverageLabel(value) {
    const measured = observedNumber(value);
    return measured === null ? '—' : `${(measured * 100).toFixed(0)}%`;
  }

  function renderCoverageMetric(valueId, metaId, metric) {
    setText(valueId, coverageLabel(metric?.coverage));
    if (!metric || typeof metric !== 'object') {
      setText(metaId, 'UNOBSERVED · coverage projection unavailable');
      return;
    }
    const measurement = String(metric.measurement || 'unobserved').toUpperCase();
    const observed = observedNumber(metric.observed);
    const exact = observedNumber(metric.exact);
    const expected = observedNumber(metric.expected);
    const details = [measurement];
    if (observed !== null && exact !== null) details.push(`${Math.round(exact)}/${Math.round(observed)} exact`);
    else if (observed !== null && expected !== null) details.push(`${Math.round(observed)}/${Math.round(expected)} observed`);
    if (metric.missing_reason) details.push(String(metric.missing_reason));
    if (metric.provenance) details.push(String(metric.provenance));
    setText(metaId, details.join(' · '));
  }

  function turnTokenState(operations) {
    const section = operations?.turn_token_measurements;
    if (!section || typeof section !== 'object') return null;
    if (section.measurement !== 'chat_turn_measurements_v1') return null;
    if (section.missing_measurement_policy !== 'unknown_not_zero') return null;
    if (section.content_free !== true) return null;
    const turnsTotal = observedNumber(section.turns_total);
    const exactTurns = observedNumber(section.turns_exact);
    if (turnsTotal === null || exactTurns === null) return null;
    const session = section.session_total && typeof section.session_total === 'object' ? section.session_total : {};
    const sessionPoint = observedNumber(session.point);
    const latest = section.latest_turn && typeof section.latest_turn === 'object' ? section.latest_turn : null;
    const latestKind = latest ? String(latest.kind || 'unknown') : 'unknown';
    const numOrNull = (value) => observedNumber(value);
    return {
      turnsTotal,
      exactTurns,
      sessionPoint,
      sessionLower: numOrNull(session.lower),
      sessionUpper: numOrNull(session.upper),
      latestKind: ['exact', 'structural_estimate', 'unknown'].includes(latestKind) ? latestKind : 'unknown',
      latestPoint: latest ? numOrNull(latest.point) : null,
      latestLower: latest ? numOrNull(latest.lower) : null,
      latestUpper: latest ? numOrNull(latest.upper) : null
    };
  }

  function sumTurnEstimates(list) {
    // Client-side cumulative total over loaded turns. Estimates stay
    // estimates: exact rows contribute their point to both range bounds.
    let count = 0, exact = 0, point = 0, lower = 0, upper = 0;
    for (const row of Array.isArray(list) ? list : []) {
      const turnPoint = observedNumber(row?.point);
      if (turnPoint === null) continue;
      const kind = String(row?.kind || '');
      count += 1;
      if (kind === 'exact') exact += 1;
      point += turnPoint;
      const turnLower = observedNumber(row?.lower);
      const turnUpper = observedNumber(row?.upper);
      if (kind === 'structural_estimate' && turnLower !== null && turnUpper !== null) {
        lower += turnLower;
        upper += turnUpper;
      } else {
        lower += turnPoint;
        upper += turnPoint;
      }
    }
    return count > 0 ? { count, exact, point, lower, upper } : null;
  }

  function formatCumulativeTotal(scope, count, exact, point, lower, upper) {
    const ranged = lower !== null && upper !== null;
    const amount = exact === count
      ? `Exact ${compact(point)}`
      : (ranged ? `ước lượng ≈${compact(point)} (${compact(lower)}–${compact(upper)})` : `ước lượng ≈${compact(point)}`);
    return `Tổng ${scope} · ${count} lượt · ${amount}`;
  }

  // Cumulative hero total shared by the analytics and live-pulse paths.
  // Backend session_total first, otherwise the sum of loaded turns.
  let cachedTurnTotal = null;
  function resolveTurnTotal(operations, state) {
    const section = operations?.turn_token_measurements;
    const session = section?.session_total && typeof section.session_total === 'object'
      ? section.session_total
      : null;
    const sessionPoint = session ? observedNumber(session.point) : null;
    if (sessionPoint !== null && state && state.turnsTotal > 0) {
      return {
        point: sessionPoint,
        lower: observedNumber(session.lower),
        upper: observedNumber(session.upper),
        exact: state.exactTurns === state.turnsTotal,
        scope: 'phiên',
        count: state.turnsTotal
      };
    }
    const loaded = sumTurnEstimates(section?.recent_turns);
    if (loaded) {
      return {
        point: loaded.point,
        lower: loaded.lower,
        upper: loaded.upper,
        exact: loaded.exact === loaded.count,
        scope: `${loaded.count} lượt gần nhất`,
        count: loaded.count
      };
    }
    return null;
  }

  function formatTurnTotalValue(total) {
    if (!total) return '—';
    return total.exact ? compact(total.point) : `≈${compact(total.point)}`;
  }

  function renderTurnTokens(operations) {
    const state = turnTokenState(operations);
    if (!state || state.turnsTotal < 1) {
      setText('daTurnTokenStatus', 'Chưa đo lượt nào');
      return;
    }
    if (state.latestKind === 'exact' && state.latestPoint !== null) {
      setText('daTurnTokenStatus', `${compact(state.latestPoint)} Exact · ${state.turnsTotal} lượt`);
      return;
    }
    if (state.latestKind === 'structural_estimate' && state.latestPoint !== null) {
      const range = state.latestLower !== null && state.latestUpper !== null
        ? ` (${compact(state.latestLower)}–${compact(state.latestUpper)})`
        : '';
      const session = state.sessionPoint !== null && state.turnsTotal > 1
        ? ` · phiên ≈${compact(state.sessionPoint)}`
        : '';
      setText('daTurnTokenStatus', `≈${compact(state.latestPoint)}${range} · ${state.turnsTotal} lượt${session}`);
      return;
    }
    if (state.sessionPoint !== null) {
      setText('daTurnTokenStatus', `phiên ≈${compact(state.sessionPoint)} · lượt mới nhất chưa đo`);
      return;
    }
    setText('daTurnTokenStatus', 'Lượt mới nhất chưa đo');
  }

  function toolCallTokenState(operations) {
    const section = operations?.tool_call_token_measurements;
    if (!section || typeof section !== 'object') return null;
    if (section.missing_measurement_policy !== 'unknown_not_zero') return null;
    if (section.content_free !== true) return null;
    const status = String(section.status || '').trim().toLowerCase();
    const measurement = String(section.measurement || '').trim().toUpperCase();
    if (!['calibrated_estimate', 'context_estimate', 'unknown'].includes(status)) return null;
    if (status === 'calibrated_estimate' && measurement !== 'CALIBRATED_ESTIMATE') return null;
    if (status === 'context_estimate' && measurement !== 'CONTEXT_ESTIMATE') return null;
    const estimate = section.estimate && typeof section.estimate === 'object' ? section.estimate : {};
    return {
      status,
      measurement,
      confidence: String(section.confidence || 'unknown').trim().toLowerCase(),
      calls: observedNumber(section.tool_calls),
      bytes: observedNumber(section.model_visible_bytes),
      chars: observedNumber(section.model_visible_chars),
      p10: observedNumber(estimate.p10_total_tokens ?? estimate.p10_context_tokens),
      p50: observedNumber(estimate.p50_total_tokens ?? estimate.p50_context_tokens),
      p90: observedNumber(estimate.p90_total_tokens ?? estimate.p90_context_tokens)
    };
  }

  function renderToolCallTokens(operations) {
    const state = toolCallTokenState(operations);
    if (!state || state.calls === null || state.calls < 1) {
      setText('daToolCallTokenStatus', 'Chưa đo lượt nào');
      return;
    }
    const chars = state.chars !== null ? ` · ${compact(state.chars)} ký tự` : '';
    if ((state.status === 'calibrated_estimate' || state.status === 'context_estimate') && state.p50 !== null) {
      const tag = state.status === 'calibrated_estimate' ? ` · ${state.confidence.toUpperCase()}` : ' · CONTEXT';
      setText('daToolCallTokenStatus', `≈${compact(state.p50)} · ${state.calls} lượt gọi${tag}${chars}`);
      return;
    }
    setText('daToolCallTokenStatus', `${state.calls} lượt gọi · chưa đủ dữ liệu ước lượng${chars}`);
  }

  function renderTurnLog(operations) {
    const container = byId('daTurnLog');
    if (!container) return;
    const section = operations?.turn_token_measurements;
    const state = turnTokenState(operations);
    const allTurns = state && Array.isArray(section.recent_turns) ? section.recent_turns : null;
    const rows = allTurns ? allTurns.slice(0, 20) : null;
    // Pinned cumulative total above the per-turn rows: backend session_total
    // first, otherwise the sum of loaded turns. Estimates stay labeled.
    if (state && allTurns) {
      const sessionTotal = section.session_total && typeof section.session_total === 'object'
        ? section.session_total
        : {};
      const sessionPoint = observedNumber(sessionTotal.point);
      if (sessionPoint !== null) {
        setText('daTurnTotal', formatCumulativeTotal(
          'phiên', state.turnsTotal, state.exactTurns, sessionPoint,
          observedNumber(sessionTotal.lower), observedNumber(sessionTotal.upper)));
      } else {
        const loaded = sumTurnEstimates(allTurns);
        setText('daTurnTotal', loaded
          ? formatCumulativeTotal('các lượt gần nhất', loaded.count, loaded.exact, loaded.point, loaded.lower, loaded.upper)
          : 'Chưa có lượt nào để cộng dồn');
      }
    } else {
      setText('daTurnTotal', 'Tổng số chưa có số liệu');
    }
    container.replaceChildren();
    if (!rows) {
      const empty = document.createElement('div');
      empty.className = 'da-turn-empty';
      empty.textContent = 'Turn measurements unavailable';
      container.append(empty);
      return;
    }
    if (!rows.length) {
      const empty = document.createElement('div');
      empty.className = 'da-turn-empty';
      empty.textContent = 'Chưa có lượt chat nào được đo';
      container.append(empty);
      return;
    }
    for (const row of rows) {
      const item = document.createElement('div');
      item.className = 'da-turn-row';
      item.setAttribute('role', 'row');
      const time = document.createElement('span');
      time.className = 'da-turn-time';
      const wallMs = observedNumber(row?.wall_time_ms);
      time.textContent = wallMs !== null && wallMs > 0 && Number.isFinite(new Date(wallMs).getTime())
        ? new Date(wallMs).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
        : '—';
      const kind = document.createElement('span');
      const rawKind = String(row?.kind || 'unknown');
      const kindName = rawKind === 'exact' || rawKind === 'structural_estimate' ? rawKind : 'unknown';
      kind.className = `da-turn-kind ${kindName === 'exact' ? 'is-exact' : kindName === 'structural_estimate' ? 'is-estimated' : 'is-unknown'}`;
      kind.textContent = kindName === 'exact' ? 'Exact' : kindName === 'structural_estimate' ? '≈ Ước lượng' : 'Chưa đo';
      const tokens = document.createElement('span');
      tokens.className = 'da-turn-tokens';
      const point = observedNumber(row?.point);
      if (point === null || kindName === 'unknown') {
        tokens.textContent = '—';
      } else if (kindName === 'exact') {
        tokens.textContent = compact(point);
      } else {
        const lower = observedNumber(row?.lower);
        const upper = observedNumber(row?.upper);
        tokens.textContent = lower !== null && upper !== null
          ? `≈${compact(point)} (${compact(lower)}–${compact(upper)})`
          : `≈${compact(point)}`;
      }
      item.append(time, kind, tokens);
      container.append(item);
    }
  }

  // Pulse fast path (4-6s): the newest turn rides every overview pulse via
  // live_control, bypassing the 30s analytics throttle. Session totals and
  // history stay on the analytics path. An unavailable live read must clear
  // the latest-turn card so an older analytics result cannot appear current.
  function renderLiveTurnCard(orchestration) {
    const live = orchestration?.latest_turn_measurement;
    const valid = live && typeof live === 'object'
      && live.measurement === 'chat_turn_measurements_v1'
      && live.missing_measurement_policy === 'unknown_not_zero'
      && live.content_free === true;
    const latest = valid && live.latest_turn && typeof live.latest_turn === 'object' ? live.latest_turn : null;
    const kind = String(latest?.kind || 'unknown');
    const point = observedNumber(latest?.point);
    if (point === null || (kind !== 'exact' && kind !== 'structural_estimate')) {
      setText('daChatTurnValue', '—');
      setText('daChatTurnDelta', 'Lượt mới nhất chưa có phép đo hợp lệ');
      setText('daChatTurnMeta', 'Live measurement unavailable · lịch sử nằm trong nhật ký lượt chat');
      setText('daTurnTokenStatus', 'Lượt mới nhất chưa đo');
      return;
    }
    if (kind === 'exact') {
      setText('daChatTurnValue', compact(point));
      setText('daChatTurnDelta', 'Exact · live pulse · freshness chưa xác nhận');
      setText('daChatTurnMeta', 'EXACT receipt · live pulse · timestamp chưa được transport expose');
    } else {
      const lower = observedNumber(latest.lower);
      const upper = observedNumber(latest.upper);
      const range = lower !== null && upper !== null ? ` (${compact(lower)}–${compact(upper)})` : '';
      // Hero value stays the cumulative total; without one yet, show this turn.
      setText('daChatTurnValue', cachedTurnTotal ? formatTurnTotalValue(cachedTurnTotal) : `≈${compact(point)}`);
      setText('daChatTurnDelta', `Lượt mới nhất${range} · live pulse · freshness chưa xác nhận`);
      setText('daChatTurnMeta', 'STRUCTURAL ESTIMATE · live pulse · timestamp chưa được transport expose');
    }
    setText('daTurnTokenStatus', kind === 'exact' ? `${compact(point)} Exact · trực tiếp` : `≈${compact(point)} · trực tiếp`);
  }

  function renderChatTurnCard(operations) {
    const state = turnTokenState(operations);
    if (!state || state.turnsTotal < 1) {
      cachedTurnTotal = null;
      setText('daChatTurnValue', '—');
      setText('daChatTurnDelta', 'Chưa đo lượt chat nào');
      setText('daChatTurnMeta', 'ChatWeb structural measurement · chờ turn FINAL đầu tiên');
      return;
    }
    // Hero value is always the cumulative total, never just the latest turn.
    cachedTurnTotal = resolveTurnTotal(operations, state);
    setText('daChatTurnValue', formatTurnTotalValue(cachedTurnTotal));
    if (state.latestKind === 'exact' && state.latestPoint !== null) {
      setText('daChatTurnDelta', `Exact · lượt mới nhất · ${state.turnsTotal} lượt`);
      setText('daChatTurnMeta', 'EXACT receipt · provider/ChatGPT báo · không ước lượng');
      return;
    }
    if (state.latestKind === 'structural_estimate' && state.latestPoint !== null) {
      const range = state.latestLower !== null && state.latestUpper !== null
        ? ` (${compact(state.latestLower)}–${compact(state.latestUpper)})`
        : '';
      let session = state.sessionPoint !== null && state.turnsTotal > 1
        ? ` · phiên ≈${compact(state.sessionPoint)}`
        : '';
      if (!session) {
        const loaded = sumTurnEstimates(operations?.turn_token_measurements?.recent_turns);
        if (loaded && loaded.count > 1) {
          session = ` · tổng ${loaded.count} lượt gần nhất ≈${compact(loaded.point)} (${compact(loaded.lower)}–${compact(loaded.upper)})`;
        }
      }
      setText('daChatTurnDelta', `Lượt mới nhất${range} · ${state.turnsTotal} lượt${session}`);
      setText('daChatTurnMeta', 'STRUCTURAL ESTIMATE · confidence none · exact chưa expose · không phải billing');
      return;
    }
    if (state.sessionPoint !== null) {
      setText('daChatTurnDelta', `Phiên · lượt mới nhất chưa đo · ${state.turnsTotal} lượt`);
      setText('daChatTurnMeta', 'STRUCTURAL ESTIMATE · session total các lượt đã đo');
      return;
    }
    {
      const loaded = sumTurnEstimates(operations?.turn_token_measurements?.recent_turns);
      if (loaded && loaded.count > 0) {
        setText('daChatTurnDelta', `${formatCumulativeTotal('các lượt gần nhất', loaded.count, loaded.exact, loaded.point, loaded.lower, loaded.upper)} · lượt mới nhất chưa đo`);
        setText('daChatTurnMeta', 'Cộng dồn các lượt đã tải · ước lượng giữ nhãn · không phải billing');
        return;
      }
    }
    setText('daChatTurnValue', '—');
    setText('daChatTurnDelta', 'Lượt mới nhất chưa đo');
    setText('daChatTurnMeta', 'Thiếu phép đo giữ unknown, không suy diễn từ 0');
  }

  function renderTokenOverviewTiles(measured, operations, controllerUsage) {
    const hasMeasured = Boolean(measured && measured.events > 0);
    const accepted = observedNumber(operations?.outcomes?.accepted);
    const windowDays = Math.max(1, Number(operations?.window?.days) || 7);
    const controllerObserved = controllerUsage?.status === 'observed';
    const controllerUnobserved = controllerUsage?.status === 'unobserved';
    const controllerEstimate = controllerTokenEstimateState(operations);
    const estimateStatus = controllerEstimate?.status || 'unknown';
    const estimatePrefix = controllerObserved && controllerUsage?.eventCount !== null
      ? `${controllerUsage.eventCount} exact · `
      : '';
    const estimateRangeAvailable = controllerEstimate
      && controllerEstimate.p10 !== null
      && controllerEstimate.p50 !== null
      && controllerEstimate.p90 !== null;
    const calibrationSamples = controllerEstimate?.calibrationSamples;
    const calibrationLabel = calibrationSamples === null || calibrationSamples === undefined
      ? 'mẫu chưa xác nhận'
      : `${calibrationSamples} mẫu`;

    setText('daProviderTokenStatus', hasMeasured ? 'Đã đo' : 'Chưa có dữ liệu');
    if (estimateStatus === 'calibrated_estimate' && estimateRangeAvailable) {
      setText('daControllerTokenStatus', `${estimatePrefix}≈${compact(controllerEstimate.p50)} token bổ sung`);
      setText('daEstimateConfidence', `${controllerEstimate.confidence.toUpperCase()} · ${calibrationLabel} · ${compact(controllerEstimate.p10)}–${compact(controllerEstimate.p90)}`);
    } else if (estimateStatus === 'context_estimate' && estimateRangeAvailable) {
      setText('daControllerTokenStatus', `${estimatePrefix}Context ≈${compact(controllerEstimate.p50)} token`);
      setText('daEstimateConfidence', `LOW · ${compact(controllerEstimate.p10)}–${compact(controllerEstimate.p90)} · không phải controller total`);
    } else if (estimateStatus === 'exact' || (controllerObserved && controllerEstimate?.missingExactRuns === 0)) {
      setText('daControllerTokenStatus', controllerObserved && controllerUsage?.eventCount !== null
        ? `${controllerUsage.eventCount} exact receipt`
        : 'Exact receipt đã khai báo; coverage chưa xác nhận');
      setText('daEstimateConfidence', 'Không cần ước lượng');
    } else {
      setText('daControllerTokenStatus', controllerUnobserved ? 'Chưa đủ dữ liệu để ước lượng' : 'Chưa đủ dữ liệu');
      setText('daEstimateConfidence', 'Chưa phát hành số ước lượng');
    }

    if (!hasMeasured) {
      for (const id of ['daTokensTotal', 'daTokensInTotal', 'daTokensOutTotal', 'daCostTotal', 'daEfficiencyTotal', 'daCallsTotal']) setText(id, '-');
      setText('daTokensDelta', 'Chưa có UsageEvent canonical');
      setText('daTokensInDelta', 'Input token unknown');
      setText('daTokensOutDelta', 'Output token unknown');
      setText('daCostVnd', 'Chi phí unknown, không phải 0');
      setText('daEfficiencyDelta', 'Cached token unknown');
      setText('daCallsDelta', accepted !== null && accepted > 0 ? `${accepted} kết quả; token chưa đo` : 'Chưa có kết quả hoàn tất');
      return;
    }

    animateText(byId('daTokensTotal'), compact, measured.total);
    animateText(byId('daTokensInTotal'), compact, measured.input);
    animateText(byId('daTokensOutTotal'), compact, measured.output);
    if (measured.cached === null) setText('daEfficiencyTotal', '—');
    else animateText(byId('daEfficiencyTotal'), compact, measured.cached);

    setText('daTokensDelta', `${measured.events} UsageEvent · ${windowDays} ngày`);
    setText('daTokensInDelta', measured.cached === null ? 'Cached token unknown' : `${compact(measured.cached)} cached`);
    setText('daTokensOutDelta', measured.reasoning === null
      ? 'Reasoning token unknown'
      : measured.reasoning > 0 ? `${compact(measured.reasoning)} reasoning` : 'Output đã đo');
    const cacheRatio = measured.cached !== null && measured.input > 0 ? (measured.cached / measured.input) * 100 : null;
    setText('daEfficiencyDelta', cacheRatio === null ? 'Cache ratio unknown' : `${cacheRatio.toFixed(1)}% input cached`);

    if (measured.costSource !== 'unobserved' && measured.cost !== null) {
      animateText(byId('daCostTotal'), (value) => money(displayedCost(value)), measured.cost);
      setText(
        'daCostVnd',
        measured.costSource === 'provider_reported'
          ? 'Provider reported'
          : 'Quy đổi bảng giá · không phải ChatGPT billing'
      );
    } else {
      setText('daCostTotal', '-');
      setText('daCostVnd', 'Chi phí unknown, không phải 0');
    }

    if (accepted !== null && accepted > 0) {
      animateText(byId('daCallsTotal'), compact, Math.round(measured.total / accepted));
      setText('daCallsDelta', `${accepted} kết quả · tỷ lệ tổng hợp ${windowDays} ngày`);
    } else {
      setText('daCallsTotal', '-');
      setText('daCallsDelta', 'Chưa có kết quả accepted trong cửa sổ');
    }

    setText('daTokensMeta', `MEASURED · canonical non-overlap · ${measured.events} UsageEvent`);
    setText('daCostMeta', measured.costSource === 'pricing_derived' ? 'API-equivalent pricing estimate; not ChatGPT billing' : measured.costSource);
    setText('daCallsMeta', accepted !== null && accepted > 0 ? 'Aggregate token/accepted ratio; không phải causal per-run join' : 'Token/accepted unavailable');
  }

  function renderMeasurementCoverage(analytics) {
    const coverage = analytics?.measurement_coverage;
    const valid = coverage && coverage.missing_measurement_policy === 'unknown_not_zero';
    setPill('daCoveragePolicy', valid ? 'unknown_not_zero' : 'coverage unavailable', valid ? 'active' : 'waiting');
    renderCoverageMetric('daCoverageController', 'daCoverageControllerMeta', valid ? coverage.controller_usage : null);
    renderCoverageMetric('daCoverageProvider', 'daCoverageProviderMeta', valid ? coverage.provider_usage : null);
    renderCoverageMetric('daCoverageInvocation', 'daCoverageInvocationMeta', valid ? coverage.tool_invocation : null);
    renderCoverageMetric('daCoverageToolCard', 'daCoverageToolCardMeta', valid ? coverage.tool_card_tokens : null);
    renderCoverageMetric('daCoverageCost', 'daCoverageCostMeta', valid ? coverage.cost : null);
    renderCoverageMetric('daCoverageRunAttribution', 'daCoverageRunAttributionMeta', valid ? coverage.exact_run_attribution : null);
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
        cell.title = measured?.hours instanceof Map
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
    const buckets = chartTrendBuckets(measured, chartTimeMode);
    const entries = measured?.byModel?.length ? measured.byModel : [];
    const models = new Map();
    const okRate = summary.calls ? percent(summary.ok, summary.calls) : 100;

    updateHeaderContext();
    const controllerWindowLabel = controllerUsage
      ? ` · ChatWeb controller ${controllerUsage.status.toUpperCase()}`
      : '';
    setText('daDateValue', operations
      ? `Cửa sổ 7 ngày · accepted-result operations${controllerWindowLabel}`
      : `Cửa sổ 7 ngày · operations analytics unavailable${controllerWindowLabel}`);
    const chart = byId('daChart');
    if (chart) chart.setAttribute('aria-label', measured ? 'Canonical measured token trend' : 'Canonical token trend unavailable');
    const donutHeading = byId('daDonut')?.closest('.da-card')?.querySelector('h3');
    if (donutHeading?.firstChild) donutHeading.firstChild.textContent = 'Phân bố Token theo mô hình · measured ';
    const costHeading = byId('daToolBars')?.closest('.da-card')?.querySelector('h3');
    if (costHeading?.firstChild) costHeading.firstChild.textContent = 'Chi phí theo mô hình · measured/provider ';
    renderTokenOverviewTiles(measured, operations, controllerUsage);
    renderTurnTokens(operations);
    renderToolCallTokens(operations);
    renderChatTurnCard(operations);
    renderLiveTurnCard(orchestration);
    renderTurnLog(operations);
    renderSparkline(buckets);
    renderOperationsTable(operations);
    renderMeasurementCoverage(operations);
    renderChart(buckets, chartTimeMode);
    renderDonut(entries, measured?.byModelStatus, measured?.byModelCachedComplete);
    renderBars(entries);
    renderModelTable(models, controllerUsage);
    renderFleetTable(models);
    renderHeatmap(measured);
    updateRealtimeMetrics(records, measured);
    updateAnomalyAlerts(summary, records);
    updateQuickSummary(summary, okRate, entries, measured);
    renderTicker();
    setText('daLastSync', snapshotFreshnessLabel());
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
    const currency = String(byId('daCurrency')?.value || 'USD');
    const fxRate = Number(byId('daFx')?.value || 0);
    const patch = {
      costPreset: preset,
      costRateInUsd: Number.isFinite(rateIn) && rateIn >= 0 ? rateIn : 0,
      costRateOutUsd: Number.isFinite(rateOut) && rateOut >= 0 ? rateOut : 0,
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

  function loadCostSettings() {
    const settings = snapshot?.settings || {};
    cost = {
      preset: settings.costPreset || 'gpt-4o-mini',
      rateIn: Number(settings.costRateInUsd ?? 0.15),
      rateOut: Number(settings.costRateOutUsd ?? 0.6),
      currency: settings.costCurrency === 'VND' ? 'VND' : 'USD',
      fxRate: Number(settings.costFxRate || 0),
      laneRates: parseLaneRates(settings.costLaneRates)
    };
    fillCostForm();
  }

  async function refreshAnalytics(force = false) {
    if (analyticsInFlight) return analyticsInFlight;
    if (!force && analyticsSnapshot && Date.now() - lastAnalyticsReadAt < DASHBOARD_ANALYTICS_REFRESH_MS) {
      return analyticsSnapshot;
    }
    lastAnalyticsReadAt = Date.now();
    analyticsInFlight = api.dashboardAnalytics()
      .then(unwrap)
      .then((data) => {
        analyticsSnapshot = data;
        return analyticsSnapshot;
      })
      .catch(() => analyticsSnapshot)
      .finally(() => { analyticsInFlight = null; });
    return analyticsInFlight;
  }

  async function applyOverviewPulse(event) {
    const detail = event?.detail && typeof event.detail === 'object' ? event.detail : {};
    if (Object.prototype.hasOwnProperty.call(detail, 'snapshot')) {
      snapshot = detail.snapshot;
      loadCostSettings();
    }
    if (Object.prototype.hasOwnProperty.call(detail, 'orchestration')) orchestration = detail.orchestration;
    if (Object.prototype.hasOwnProperty.call(detail, 'performance')) perf = detail.performance;
    // Render the live pulse immediately. Analytics is an independent,
    // window-bounded read and must never hold the live Overview render behind
    // its IPC timeout or an in-flight request.
    renderAll();
    void refreshAnalytics(detail.force === true).then(() => renderAll());
  }

  function requestOverviewRefresh() {
    document.dispatchEvent(new CustomEvent('coding-tools:overview-refresh-request'));
  }

  // Dashboard markup is hosted directly in the Control Center overview, so
  // refresh/theme sync stays in this document. No embedded frame to mirror.
  byId('daRefreshButton')?.addEventListener('click', () => {
    lastAnalyticsReadAt = 0;
    requestOverviewRefresh();
  });
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
    if (target) setTimeout(requestOverviewRefresh, 0);
  });
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState !== 'hidden' && activePage() === 'overview') requestOverviewRefresh();
  });
  document.addEventListener('coding-tools:overview-pulse', applyOverviewPulse);

  reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches === true;

  Promise.all([Promise.resolve(loadCostSettings()), refreshAnalytics(true)])
    .then(() => renderAll())
    .finally(requestOverviewRefresh);
})();
