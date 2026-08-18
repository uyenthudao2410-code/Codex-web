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

  const STATE_RANK = { offline: 0, connected: 1, waiting: 2, blocked: 3, active: 4 };

  let perf = null;
  let orchestration = null;
  let cost = {
    preset: 'gpt-4o-mini', rateIn: 0.15, rateOut: 0.6, currency: 'USD',
    fxRate: 0, bytesPerToken: 4, laneRates: { ...DEFAULT_LANE_RATES }
  };
  let refreshInFlight = false;
  let lastPerfReadAt = 0;
  let lastOrchestrationReadAt = 0;
  let lastEventSeq = -1;
  let reducedMotion = false;

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

    const measuredByLane = new Map();
    for (const delegation of Array.isArray(orchestration?.delegations) ? orchestration.delegations : []) {
      const lane = delegationLane(delegation);
      const economics = delegation?.metadata?.economics;
      if (!lane || !economics || typeof economics !== 'object') continue;
      const input = Number(economics.input_tokens);
      const output = Number(economics.output_tokens);
      if (!Number.isFinite(input) || input < 0 || !Number.isFinite(output) || output < 0) continue;
      const usage = measuredByLane.get(lane) || { inTokens: 0, outTokens: 0, cachedTokens: 0, calls: 0 };
      usage.inTokens += input;
      usage.outTokens += output;
      if (Number.isFinite(Number(economics.cached_input_tokens))) {
        usage.cachedTokens += Math.max(0, Number(economics.cached_input_tokens));
      }
      usage.calls += 1;
      measuredByLane.set(lane, usage);
    }

    for (const [lane, usage] of measuredByLane) {
      let entry = map.get(lane);
      if (!entry) {
        entry = { model: lane, calls: 0, ok: 0, inTokens: 0, outTokens: 0, cost: 0 };
        map.set(lane, entry);
      }
      entry.inTokens = usage.inTokens;
      entry.outTokens = usage.outTokens;
      entry.cachedTokens = usage.cachedTokens;
      entry.calls = Math.max(entry.calls, usage.calls);
      entry.usageEvidence = 'MEASURED';
      entry.modelId = String(delegation?.model || '');
      const providerCost = Number(economics.provider_cost);
      if (Number.isFinite(providerCost) && providerCost >= 0) {
        entry.providerCost = providerCost;
      }
    }
    for (const entry of map.values()) {
      if (Number.isFinite(Number(entry.providerCost)) && Number(entry.providerCost) >= 0) {
        entry.cost = Number(entry.providerCost);
        entry.costSource = 'provider_reported';
      } else {
        entry.cost = costOf(entry, entry.model);
        entry.costSource = entry.usageEvidence === 'MEASURED' ? 'pricing_derived' : 'settings_estimate';
      }
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
    if (!element || reducedMotion) {
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

  function renderChart(buckets) {
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

    for (let index = 0; index < buckets.length; index += 1) {
      if (index % 4 !== 0) continue;
      const date = new Date(buckets[index].hour * 3600000);
      const x = pad.left + (plotW * index) / Math.max(1, buckets.length - 1);
      svg.appendChild(svgEl('text', { x, y: height - 8, 'text-anchor': 'middle', class: 'axis-label' },
        date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })));
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
        tooltip.textContent = `${new Date(bucket.hour * 3600000).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })} · vào ${compact(bucket.in)} · ra ${compact(bucket.out)}`;
        const card = byId('daChartCard');
        if (card) {
          const cardBounds = card.getBoundingClientRect();
          tooltip.style.left = `${Math.max(12, Math.min(cardBounds.width - 240, event.clientX - cardBounds.left + 14))}px`;
          tooltip.style.top = `${event.clientY - cardBounds.top - 30}px`;
        }
      }
    });
  }

  function renderDonut(entries) {
    const svg = byId('daDonut');
    const legend = byId('daLegend');
    const center = byId('daDonutTotal');
    const sub = byId('daDonutSub');
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

  function renderBars(entries) {
    const container = byId('daToolBars');
    if (!container) return;
    container.replaceChildren();
    const top = entries.slice(0, 6);
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

  function renderModelTable(breakdown) {
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
    for (const label of ['Model', 'State', 'Input / context', 'Output', 'Calls', 'Share', 'Scenario cost']) {
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
      const evidence = entry?.usageEvidence || (hasTraffic ? 'ESTIMATED' : 'NO USAGE');
      sub.textContent = `${model.sub} · ${evidence}`;
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
      const costSourceText = { provider_reported: 'provider reported', pricing_derived: 'derived from $/1M pricing', settings_estimate: 'settings estimate' }[entry?.costSource] || 'estimate';
      costCell.title = `Nguồn giá trị token: ${costSourceText}`;
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

  function renderTiles(buckets, summary, todayCount, yesterdayTokens, allCalls, allExecMs, laneTotalUsd, yesterdayCount) {
    const inTokens = summary.inTokens;
    const outTokens = summary.outTokens;
    const totalTokens = inTokens + outTokens;
    const usd = costOf(summary, 'chatweb');
    const okRate = summary.calls ? percent(summary.ok, summary.calls) : 0;

    animateText(byId('daTokensTotal'), compact, totalTokens);
    setText('daTokensSplit', `Tool → model ${compact(inTokens)} context-token eq.`);
    setText('daTokensMeta', `MEASURED model-visible bytes · ESTIMATED at ${cost.bytesPerToken} byte/token · images excluded`);
    const rateEl = byId('daTokensRate');
    if (rateEl) {
      const lastHour = buckets[buckets.length - 1];
      const activeHours = buckets.filter((bucket) => bucket.in + bucket.out > 0).length;
      const hourAverage = buckets.reduce((sum, bucket) => sum + bucket.in + bucket.out, 0) / Math.max(1, buckets.length);
      const current = lastHour && lastHour.in + lastHour.out > 0 ? lastHour.in + lastHour.out : 0;
      rateEl.textContent = current > 0
        ? `Giờ gần nhất ≈ ${compact(current)} token · trung bình ≈ ${compact(hourAverage)}/giờ`
        : activeHours > 0
          ? `Trung bình ≈ ${compact(hourAverage)} token/giờ (24h)`
          : 'Chưa có mẫu theo giờ';
      rateEl.title = 'Lưu lượng token theo giờ · từ hourly metrics của runtime, không phải báo phí';
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
    const deltaEl = byId('daTokensDelta');
    if (deltaEl) {
      deltaEl.textContent = delta;
      deltaEl.classList.toggle('up', yesterdayTokens > 0 && totalTokens >= yesterdayTokens);
      deltaEl.classList.toggle('down', yesterdayTokens > 0 && totalTokens < yesterdayTokens);
    }

    animateText(byId('daCostTotal'), (value) => money(displayedCost(value)), usd);
    setText('daCostSplit', `Context scenario ${money(usd)} · current lanes ${money(displayedCost(laneTotalUsd))}`);
    setText('daCostMeta', cost.preset && cost.preset !== 'custom'
      ? `SCENARIO · ${(PRICING_PRESETS.find((preset) => preset.id === cost.preset) || {}).label || cost.preset} · not provider billing`
      : 'SCENARIO · custom rates · not provider billing');
    const vndEl = byId('daCostVnd');
    if (vndEl) {
      vndEl.textContent = cost.currency === 'USD' ? `≈ ${money(usd * fxRate())}` : `≈ ${money(usd)}`;
    }

    animateText(byId('daCallsTotal'), (value) => String(Math.round(value)), todayCount);
    setText('daCallsMeta', `${summary.ok}/${summary.calls} lệnh OK · ${allCalls} lượt tổng`);
    const callsDelta = byId('daCallsDelta');
    if (callsDelta) callsDelta.textContent = `${okRate.toFixed(0)}% thành công`;
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

  function renderAll() {
    const records = normalizeRecords();
    const midnight = localMidnight(new Date());
    const today = records.filter((record) => record.time >= midnight);
    const yesterday = records.filter((record) => record.time >= midnight - 86400000 && record.time < midnight);
    const summary = summarize(today);
    const yesterdaySummary = summarize(yesterday);
    const allSummary = summarize(records);
    const buckets = performanceBuckets(records, 24);
    const entries = toolBreakdown(today);
    const models = modelBreakdown(today);
    const laneTotalUsd = [...models.values()]
      .filter((entry) => ['fast', 'deepseek', 'terra', 'sol'].includes(entry.model))
      .reduce((sum, entry) => sum + entry.cost, 0);

    renderTiles(buckets, summary, today.length, yesterdaySummary.inTokens + yesterdaySummary.outTokens, records.length, allSummary.execMs, laneTotalUsd, yesterday.length);
    renderChart(buckets);
    renderDonut(entries);
    renderBars(entries);
    renderModelTable(models);
    renderTicker();
    setText('daLastSync', `Đồng bộ ${new Date().toLocaleTimeString('vi-VN')}`);
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

  // ---- Polling ---------------------------------------------------------------

  async function refreshPerformance(force = false) {
    if (!force && Date.now() - lastPerfReadAt < 10000) return;
    lastPerfReadAt = Date.now();
    try { perf = unwrap(await api.performanceTrace()); }
    catch { perf = null; }
    renderAll();
  }

  async function refreshOrchestration(force = false) {
    if (!force && Date.now() - lastOrchestrationReadAt < 4000) return;
    lastOrchestrationReadAt = Date.now();
    try { orchestration = unwrap(await api.orchestration()); }
    catch { orchestration = null; }
    renderAll();
  }

  async function refresh(force = false) {
    if (refreshInFlight || (!force && !shouldPoll())) return;
    refreshInFlight = true;
    try {
      await Promise.all([refreshPerformance(force), refreshOrchestration(force)]);
    } finally {
      refreshInFlight = false;
    }
  }

  byId('daRefreshButton')?.addEventListener('click', () => refresh(true));
  byId('daApply')?.addEventListener('click', applyCostModel);

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

  loadCostSettings().then(() => refresh(true));
  setInterval(() => refresh(false), 3000);
})();
