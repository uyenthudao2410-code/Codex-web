const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const HOST_OBSERVATION_SCHEMA_VERSION = 6;
const HOST_OBSERVATION_MAX_BUFFER = 256;
const HOST_OBSERVATION_MAX_JOURNAL_BYTES = 2 * 1024 * 1024;
const HOST_CORRELATION_SCHEMA_VERSION = 1;
const HOST_CORRELATION_BINDING_TTL_MS = 60 * 60 * 1000;
const PRODUCT_SESSION_RECEIPT_PREFIX = 'chatweb-product-session:';
const EVENT_TYPES = new Set(['user_turn_visible', 'assistant_response_first_visible', 'host_turn_span', 'controller_usage', 'turn_features']);

// Bounds for the in-page SSE usage observer. The hook is read-only: it tees
// event-stream bodies, scans a bounded prefix for response.completed frames,
// and never alters page traffic. Anything unexpected falls back to the
// untouched original response.
const SSE_OBSERVATION_MAX_STREAM_BYTES = 262144;
const SSE_OBSERVATION_MAX_EVENTS_PER_STREAM = 400;
const SSE_OBSERVATION_MAX_KEY_SAMPLES = 8;

function initialUsageSeamDebug() {
  return {
    sseStreams: 0,
    sseEvents: 0,
    sseCompleted: 0,
    sseUsageHits: 0,
    sseUsageRejected: 0,
    usageKeySamples: []
  };
}

// Shared in-page fetch/SSE observer. Both the early bootstrap script and the
// DOM observer fallback interpolate this snippet; it relies only on the
// enclosing scope names `state` (with `state.debug`), `structuredResponseUsage`
// and `inspectStructuredUsage`, which both templates define. No message
// content is read: only response.completed envelopes are inspected, and only
// token counters plus usage-object key names are retained.
function sseFetchObservationSnippet() {
  return `
  const installFetchSseObservation = () => {
    if (window.__mcpUsageSseHookInstalled) return true;
    const nativeFetch = window.fetch;
    if (typeof nativeFetch !== 'function') return false;
    window.__mcpUsageSseOriginalFetch = nativeFetch;
    window.__mcpUsageSseHookInstalled = true;
    const NL = String.fromCharCode(10);
    const FRAME_SEP = NL + NL;
    // Bounded event-vocabulary sampling (P1): records distinct SSE type
    // names only, never payloads. Settles whether ChatGPT web sends
    // response.completed shapes at all.
    const noteSseEventType = (obj) => {
      const typeName = obj && typeof obj.type === 'string' ? obj.type.slice(0, 64) : '';
      if (!typeName) return;
      if (state.debug.sseTypeSamples.length < 16 && state.debug.sseTypeSamples.indexOf(typeName) === -1) {
        state.debug.sseTypeSamples.push(typeName);
      }
      // Usage-shape survey: if ANY envelope carries a usage object, record
      // its key names (never values). Closes the "usage hiding under another
      // event type" doubt without reading content.
      const usage = obj && obj.usage;
      if (usage && typeof usage === 'object' && !Array.isArray(usage)) {
        const keys = 'usage:{' + Object.keys(usage).slice(0, 8).join(',') + '}';
        if (state.debug.usageKeySamples.length < 8 && state.debug.usageKeySamples.indexOf(keys) === -1) {
          state.debug.usageKeySamples.push(keys);
        }
      }
    };
    const noteSseObject = (obj) => {
      if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return;
      if (obj.type !== 'response.completed' && obj.object !== 'response') return;
      state.debug.sseCompleted += 1;
      const usage = obj.usage || (obj.response && obj.response.usage) || null;
      if (usage && typeof usage === 'object' && !Array.isArray(usage)) {
        const keys = Object.keys(usage).slice(0, 8).join(',');
        if (state.debug.usageKeySamples.length < 8 && state.debug.usageKeySamples.indexOf(keys) === -1) {
          state.debug.usageKeySamples.push(keys);
        }
      }
      try { inspectStructuredUsage(obj); } catch (ignoredInspect) {}
      if (structuredResponseUsage(obj)) state.debug.sseUsageHits += 1;
      else state.debug.sseUsageRejected += 1;
    };
    const scanSseBranch = (branch) => {
      try {
        const reader = branch.getReader();
        const decoder = new TextDecoder();
        let text = '';
        let events = 0;
        const pump = () => reader.read().then((chunk) => {
          if (chunk && chunk.value) {
            try { text += decoder.decode(chunk.value, { stream: !chunk.done }); } catch (ignoredDecode) {}
          }
          if (text.length > 262144) { try { reader.cancel(); } catch (ignoredCancel) {} return; }
          let cut = text.indexOf(FRAME_SEP);
          while (cut !== -1 && events < 400) {
            const frame = text.slice(0, cut);
            text = text.slice(cut + 2);
            const lines = frame.split(NL);
            for (let i = 0; i < lines.length; i += 1) {
              const line = lines[i].trim();
              if (line.indexOf('data:') !== 0) continue;
              const payload = line.slice(5).trim();
              if (!payload || payload === '[DONE]') continue;
              events += 1;
              state.debug.sseEvents += 1;
              try { const eventObject = JSON.parse(payload); noteSseEventType(eventObject); noteSseObject(eventObject); } catch (ignoredFrame) {}
            }
            cut = text.indexOf(FRAME_SEP);
          }
          if (!chunk.done && events < 400) pump();
        }, () => {});
        pump();
      } catch (ignoredBranch) {}
    };
    window.fetch = async function mcpUsageObservedFetch() {
      const response = await nativeFetch.apply(this, arguments);
      try {
        const headers = response && response.headers;
        const contentType = String(headers && headers.get ? headers.get('content-type') : '').toLowerCase();
        if (contentType.indexOf('text/event-stream') === -1 || !response.body || response.body.locked) return response;
        const tee = response.body.tee();
        if (!tee || tee.length < 2) return response;
        state.debug.sseStreams += 1;
        scanSseBranch(tee[1]);
        return new Response(tee[0], { status: response.status, statusText: response.statusText, headers: response.headers });
      } catch (ignoredWrap) {
        return response;
      }
    };
    return true;
  };
  restoreFetchSseObservation = () => {
    try {
      if (window.__mcpUsageSseHookInstalled && window.__mcpUsageSseOriginalFetch) {
        window.fetch = window.__mcpUsageSseOriginalFetch;
      }
    } catch (ignoredRestore) {}
    window.__mcpUsageSseHookInstalled = false;
    window.__mcpUsageSseOriginalFetch = null;
  };`.trim();
}

// Outer-scope binding for the snippet above. The snippet is interpolated
// inside a branch in the observer fallback, while dispose() lives in the
// outer IIFE scope, so the restore handle must be declared outside and
// assigned by the snippet rather than block-scoped.
function sseFetchObservationScopeSnippet() {
  return 'let restoreFetchSseObservation = null;';
}

function buildChatEvaluationBootstrapScript() {
  return `(() => {
    const KEY = '__mcpStructuredUsageBootstrap';
    const existing = window[KEY];
    if (existing && existing.schemaVersion === 1 && typeof existing.subscribe === 'function') return true;
    const state = {
      schemaVersion: 1,
      queue: [],
      listeners: new Set(),
      debug: { sseStreams: 0, sseEvents: 0, sseCompleted: 0, sseUsageHits: 0, sseUsageRejected: 0, usageKeySamples: [], sseTypeSamples: [], featuresFinalized: 0, featuresInterim: 0 },
      dispose: null
    };
    const exactInteger = (value) => Number.isSafeInteger(value) && value >= 0 ? value : null;
    const structuredResponseUsage = (node) => {
      if (!node || typeof node !== 'object' || Array.isArray(node)) return null;
      let response = null;
      if (node.type === 'response.completed' && node.response && typeof node.response === 'object' && !Array.isArray(node.response)) {
        response = node.response;
      } else if (node.object === 'response' && node.status === 'completed') {
        response = node;
      } else if (node.status === 'completed' && /^resp[_-]/.test(String(node.id || '')) && node.usage) {
        response = node;
      }
      const usage = response?.usage;
      if (!usage || typeof usage !== 'object' || Array.isArray(usage)) return null;
      const inputTokens = exactInteger(usage.input_tokens);
      const cachedInputTokens = exactInteger(usage.input_tokens_details?.cached_tokens);
      const outputTokens = exactInteger(usage.output_tokens);
      const reasoningOutputTokens = exactInteger(usage.output_tokens_details?.reasoning_tokens);
      if (inputTokens === null || cachedInputTokens === null || outputTokens === null || reasoningOutputTokens === null
        || cachedInputTokens > inputTokens || reasoningOutputTokens > outputTokens) return null;
      const modelId = typeof response.model === 'string' && response.model.length <= 200 ? response.model : '';
      return { inputTokens, cachedInputTokens, outputTokens, reasoningOutputTokens, modelId };
    };
    const structuredUsageEnvelopeChildren = (node) => {
      if (!node || typeof node !== 'object' || Array.isArray(node)) return [];
      const children = [];
      for (const key of ['data', 'event']) {
        const child = node[key];
        if (child && typeof child === 'object' && !Array.isArray(child)) children.push(child);
      }
      return children;
    };
    const publish = (usage) => {
      if (!usage) return;
      const exact = {
        inputTokens: usage.inputTokens,
        cachedInputTokens: usage.cachedInputTokens,
        outputTokens: usage.outputTokens,
        reasoningOutputTokens: usage.reasoningOutputTokens,
        modelId: usage.modelId || ''
      };
      if (state.listeners.size) {
        for (const listener of Array.from(state.listeners)) {
          try { listener(exact); } catch {}
        }
        return;
      }
      state.queue.push(exact);
      if (state.queue.length > 16) state.queue.splice(0, state.queue.length - 16);
    };
    const inspectStructuredUsage = (value) => {
      if (!value || typeof value !== 'object' || Array.isArray(value)) return;
      const queue = [{ value, depth: 0 }];
      let inspected = 0;
      while (queue.length && inspected < 8) {
        const item = queue.shift();
        const current = item?.value;
        if (!current || typeof current !== 'object' || Array.isArray(current)) continue;
        inspected += 1;
        const usage = structuredResponseUsage(current);
        if (usage) {
          publish(usage);
          return;
        }
        if (item.depth >= 2) continue;
        for (const child of structuredUsageEnvelopeChildren(current)) queue.push({ value: child, depth: item.depth + 1 });
      }
    };
    const originalJsonParse = JSON.parse;
    const parseWithUsageObservation = function (...args) {
      const parsed = originalJsonParse.apply(this, args);
      try { inspectStructuredUsage(parsed); } catch {}
      return parsed;
    };
    JSON.parse = parseWithUsageObservation;
    ${sseFetchObservationScopeSnippet()}
    ${sseFetchObservationSnippet()}
    try { installFetchSseObservation(); } catch {}
    const originalResponseJson = globalThis.Response?.prototype?.json;
    let responseJsonWithUsageObservation = null;
    if (typeof originalResponseJson === 'function') {
      responseJsonWithUsageObservation = async function (...args) {
        const parsed = await originalResponseJson.apply(this, args);
        try { inspectStructuredUsage(parsed); } catch {}
        return parsed;
      };
      globalThis.Response.prototype.json = responseJsonWithUsageObservation;
    }
    state.subscribe = (listener) => {
      if (typeof listener !== 'function') return () => {};
      state.listeners.add(listener);
      const pending = state.queue.splice(0);
      for (const usage of pending) {
        try { listener(usage); } catch {}
      }
      return () => state.listeners.delete(listener);
    };
    state.dispose = () => {
      state.listeners.clear();
      state.queue.length = 0;
      try { restoreFetchSseObservation(); } catch {}
      if (JSON.parse === parseWithUsageObservation) JSON.parse = originalJsonParse;
      if (responseJsonWithUsageObservation && globalThis.Response?.prototype?.json === responseJsonWithUsageObservation) {
        globalThis.Response.prototype.json = originalResponseJson;
      }
      if (window[KEY] === state) {
        try { delete window[KEY]; } catch { window[KEY] = null; }
      }
    };
    window[KEY] = state;
    return true;
  })()`;
}

function boundedText(value, maxLength, required = false) {
  const text = String(value ?? '').trim();
  if ((required && !text) || text.length > maxLength || /[\u0000-\u001f]/.test(text)) return null;
  return text;
}

function finiteNonNegative(value) {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : null;
}

function exactNonNegativeInteger(value) {
  return Number.isSafeInteger(value) && value >= 0 ? value : null;
}

function productSessionReceipt(url) {
  let parsed;
  try { parsed = new URL(String(url || '')); } catch { return null; }
  const host = parsed.hostname.toLowerCase();
  if (host !== 'chatgpt.com' && host !== 'www.chatgpt.com') return null;
  const match = parsed.pathname.match(/^\/c\/([A-Za-z0-9_-]{8,200})\/?$/);
  if (!match) return null;
  const digest = crypto.createHash('sha256')
    .update(`${host === 'www.chatgpt.com' ? 'chatgpt.com' : host}\0${match[1]}`, 'utf8')
    .digest('hex');
  return `${PRODUCT_SESSION_RECEIPT_PREFIX}${digest}`;
}

function normalizedProductSessionReceiptId(value) {
  const receipt = boundedText(value, PRODUCT_SESSION_RECEIPT_PREFIX.length + 64, false);
  if (!receipt || !receipt.startsWith(PRODUCT_SESSION_RECEIPT_PREFIX)) return null;
  const digest = receipt.slice(PRODUCT_SESSION_RECEIPT_PREFIX.length);
  return /^[0-9a-f]{64}$/.test(digest) ? receipt : null;
}

function normalizeHostObservation(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const allowed = new Set([
    'schema_version', 'event_type', 'observation_id', 'span_id', 'navigation_epoch', 'clock_domain',
    'monotonic_ms', 'wall_time_ms', 'start_ms', 'end_ms', 'duration_ms', 'user_observation_id',
    'assistant_observation_id', 'observer_plane', 'measurement', 'trace_id', 'turn_id', 'run_id', 'wave_id',
    'accounting_profile', 'provider_id', 'model_id', 'source', 'input_tokens', 'cached_input_tokens',
    'output_tokens', 'reasoning_output_tokens', 'product_session_receipt_id',
    'prior_product_session_receipt_id', 'product_session_transition',
    'turn_ordinal', 'tool_card_count', 'user_chars', 'user_code_blocks',
    'asst_chars', 'asst_code_blocks'
  ]);
  if (Object.keys(value).some((key) => !allowed.has(key))) return null;
  if (value.schema_version !== HOST_OBSERVATION_SCHEMA_VERSION || !EVENT_TYPES.has(value.event_type)) return null;

  const controllerOnlyKeys = [
    'accounting_profile', 'provider_id', 'model_id', 'source', 'input_tokens', 'cached_input_tokens',
    'output_tokens', 'reasoning_output_tokens'
  ];
  if (value.event_type !== 'controller_usage' && controllerOnlyKeys.some((key) => Object.hasOwn(value, key))) return null;

  const featureOnlyKeys = ['turn_ordinal', 'tool_card_count', 'user_chars', 'user_code_blocks', 'asst_chars', 'asst_code_blocks'];
  if (value.event_type !== 'turn_features' && featureOnlyKeys.some((key) => Object.hasOwn(value, key))) return null;

  const navigationEpoch = value.navigation_epoch;
  const clockDomain = boundedText(value.clock_domain, 160, true);
  const observerPlane = boundedText(value.observer_plane, 100, true);
  const measurement = boundedText(value.measurement, 100, true);
  const traceId = boundedText(value.trace_id, 128, true);
  const turnId = boundedText(value.turn_id, 128, true);
  const runId = boundedText(value.run_id, 128, false);
  const waveId = boundedText(value.wave_id, 128, false);
  const productSessionReceiptId = normalizedProductSessionReceiptId(value.product_session_receipt_id);
  const priorProductSessionReceiptId = normalizedProductSessionReceiptId(value.prior_product_session_receipt_id);
  const productSessionTransition = boundedText(value.product_session_transition, 16, false);
  if (!Number.isInteger(navigationEpoch) || navigationEpoch < 0 || !clockDomain || !observerPlane || !measurement || !traceId || !turnId) return null;
  if (Boolean(runId) !== Boolean(waveId)) return null;
  if (Object.hasOwn(value, 'product_session_receipt_id') && !productSessionReceiptId) return null;
  if (Object.hasOwn(value, 'prior_product_session_receipt_id') && !priorProductSessionReceiptId) return null;
  if (productSessionTransition && !['observed', 'same', 'rotated'].includes(productSessionTransition)) return null;
  if ((priorProductSessionReceiptId || productSessionTransition) && !productSessionReceiptId) return null;
  if (productSessionTransition === 'rotated' && (!priorProductSessionReceiptId || priorProductSessionReceiptId === productSessionReceiptId)) return null;

  const common = {
    schema_version: HOST_OBSERVATION_SCHEMA_VERSION,
    event_type: value.event_type,
    navigation_epoch: navigationEpoch,
    clock_domain: clockDomain,
    observer_plane: observerPlane,
    measurement: measurement,
    trace_id: traceId,
    turn_id: turnId,
    ...(runId && waveId ? { run_id: runId, wave_id: waveId } : {}),
    ...(productSessionReceiptId ? { product_session_receipt_id: productSessionReceiptId } : {}),
    ...(priorProductSessionReceiptId ? { prior_product_session_receipt_id: priorProductSessionReceiptId } : {}),
    ...(productSessionTransition ? { product_session_transition: productSessionTransition } : {})
  };

  if (value.event_type === 'controller_usage') {
    const observationId = boundedText(value.observation_id, 128, true);
    const monotonicMs = finiteNonNegative(value.monotonic_ms);
    const wallTimeMs = finiteNonNegative(value.wall_time_ms);
    const accountingProfile = boundedText(value.accounting_profile, 32, true);
    const source = boundedText(value.source, 32, true);
    const providerId = boundedText(value.provider_id, 160, false);
    const modelId = boundedText(value.model_id, 200, false);
    const inputTokens = exactNonNegativeInteger(value.input_tokens);
    const cachedInputTokens = exactNonNegativeInteger(value.cached_input_tokens);
    const outputTokens = exactNonNegativeInteger(value.output_tokens);
    const reasoningOutputTokens = exactNonNegativeInteger(value.reasoning_output_tokens);
    if (!observationId || monotonicMs === null || wallTimeMs === null || !accountingProfile || !source
      || inputTokens === null || cachedInputTokens === null || outputTokens === null || reasoningOutputTokens === null
      || cachedInputTokens > inputTokens || reasoningOutputTokens > outputTokens) return null;
    return {
      ...common,
      observation_id: observationId,
      monotonic_ms: monotonicMs,
      wall_time_ms: wallTimeMs,
      accounting_profile: accountingProfile,
      source,
      ...(providerId ? { provider_id: providerId } : {}),
      ...(modelId ? { model_id: modelId } : {}),
      input_tokens: inputTokens,
      cached_input_tokens: cachedInputTokens,
      output_tokens: outputTokens,
      reasoning_output_tokens: reasoningOutputTokens
    };
  }

  if (value.event_type === 'turn_features') {
    const turnFeaturesId = boundedText(value.observation_id, 128, true);
    const turnFeaturesMonotonic = finiteNonNegative(value.monotonic_ms);
    const turnFeaturesWall = finiteNonNegative(value.wall_time_ms);
    // Ordinal is best-effort: real ChatGPT DOM often lacks
    // conversation-turn-N keys while role-based detection still works.
    // A null ordinal must never drop the whole feature record.
    let turnOrdinal = null;
    if (value.turn_ordinal !== undefined && value.turn_ordinal !== null) {
      turnOrdinal = exactNonNegativeInteger(value.turn_ordinal);
      if (turnOrdinal === null) return null;
    }
    const durationMs = finiteNonNegative(value.duration_ms);
    const toolCards = exactNonNegativeInteger(value.tool_card_count);
    const userChars = exactNonNegativeInteger(value.user_chars);
    const userCode = exactNonNegativeInteger(value.user_code_blocks);
    const asstChars = exactNonNegativeInteger(value.asst_chars);
    const asstCode = exactNonNegativeInteger(value.asst_code_blocks);
    if (!turnFeaturesId || turnFeaturesMonotonic === null || turnFeaturesWall === null
      || durationMs === null || toolCards === null
      || userChars === null || userCode === null || asstChars === null || asstCode === null) return null;
    return {
      ...common,
      observation_id: turnFeaturesId,
      monotonic_ms: turnFeaturesMonotonic,
      wall_time_ms: turnFeaturesWall,
      turn_ordinal: turnOrdinal,
      duration_ms: durationMs,
      tool_card_count: toolCards,
      user_chars: userChars,
      user_code_blocks: userCode,
      asst_chars: asstChars,
      asst_code_blocks: asstCode
    };
  }

  if (value.event_type === 'host_turn_span') {
    const spanId = boundedText(value.span_id, 128, true);
    const userObservationId = boundedText(value.user_observation_id, 128, true);
    const assistantObservationId = boundedText(value.assistant_observation_id, 128, true);
    const startMs = finiteNonNegative(value.start_ms);
    const endMs = finiteNonNegative(value.end_ms);
    if (!spanId || !userObservationId || !assistantObservationId || startMs === null || endMs === null || endMs < startMs) return null;
    return {
      ...common,
      span_id: spanId,
      user_observation_id: userObservationId,
      assistant_observation_id: assistantObservationId,
      start_ms: startMs,
      end_ms: endMs,
      duration_ms: Math.round((endMs - startMs) * 1000) / 1000
    };
  }

  const observationId = boundedText(value.observation_id, 128, true);
  const monotonicMs = finiteNonNegative(value.monotonic_ms);
  const wallTimeMs = finiteNonNegative(value.wall_time_ms);
  if (!observationId || monotonicMs === null || wallTimeMs === null) return null;
  return { ...common, observation_id: observationId, monotonic_ms: monotonicMs, wall_time_ms: wallTimeMs };
}

function journalPath(workspace) {
  return path.join(path.resolve(workspace), '.coding-tools', 'evaluation', 'chatweb-host-observations.jsonl');
}

function pendingTurnPath(workspace) {
  return path.join(path.resolve(workspace), '.coding-tools', 'evaluation', 'chatweb-host-turn-pending.json');
}

function bindingTurnPath(workspace) {
  return path.join(path.resolve(workspace), '.coding-tools', 'evaluation', 'chatweb-host-turn-binding.json');
}

function writeOneShotJson(target, value) {
  fs.mkdirSync(path.dirname(target), { recursive: true });
  const temporary = path.join(path.dirname(target), `.${path.basename(target)}.${process.pid}.${Date.now()}.tmp`);
  let descriptor;
  try {
    descriptor = fs.openSync(temporary, 'w', 0o600);
    fs.writeFileSync(descriptor, `${JSON.stringify(value)}\n`, 'utf8');
    fs.fsyncSync(descriptor);
  } finally {
    if (descriptor !== undefined) fs.closeSync(descriptor);
  }
  try {
    fs.renameSync(temporary, target);
  } catch (error) {
    try { fs.rmSync(temporary, { force: true }); } catch { /* best effort */ }
    throw error;
  }
}

function readOneShotJson(target) {
  try {
    const value = JSON.parse(fs.readFileSync(target, 'utf8'));
    return value && typeof value === 'object' && !Array.isArray(value) ? value : null;
  } catch {
    return null;
  }
}

function normalizedBinding(workspace) {
  const target = bindingTurnPath(workspace);
  const value = readOneShotJson(target);
  const allowed = new Set(['schema_version', 'turn_id', 'trace_id', 'run_id', 'wave_id', 'bound_at_unix_ms']);
  const validKeys = value && !Object.keys(value).some((key) => !allowed.has(key));
  const turnId = validKeys ? boundedText(value.turn_id, 128, true) : null;
  const traceId = validKeys ? boundedText(value.trace_id, 128, true) : null;
  const runId = validKeys ? boundedText(value.run_id, 128, true) : null;
  const waveId = validKeys ? boundedText(value.wave_id, 128, true) : null;
  const boundAt = validKeys ? finiteNonNegative(value.bound_at_unix_ms) : null;
  const now = Date.now();
  if (!validKeys || value.schema_version !== HOST_CORRELATION_SCHEMA_VERSION || !turnId || !traceId || !runId || !waveId || boundAt === null || boundAt > now + 5000 || now - boundAt > HOST_CORRELATION_BINDING_TTL_MS) {
    if (value) {
      try { fs.rmSync(target, { force: true }); } catch { /* best effort */ }
    }
    return null;
  }
  return { turn_id: turnId, trace_id: traceId, run_id: runId, wave_id: waveId, bound_at_unix_ms: boundAt };
}

class ChatEvaluationJournal {
  constructor({ maxBytes = HOST_OBSERVATION_MAX_JOURNAL_BYTES } = {}) {
    this.maxBytes = Math.max(4096, Number(maxBytes) || HOST_OBSERVATION_MAX_JOURNAL_BYTES);
    this.correlationCompletion = new Map();
    this.productSessions = new Map();
  }

  lastProductSessionReceipt(workspace) {
    const key = path.resolve(workspace);
    if (this.productSessions.has(key)) return this.productSessions.get(key);
    let previous = null;
    try {
      const lines = fs.readFileSync(journalPath(workspace), 'utf8').trim().split(/\r?\n/).slice(-256).reverse();
      for (const line of lines) {
        let value;
        try { value = JSON.parse(line); } catch { continue; }
        const receipt = normalizedProductSessionReceiptId(value?.product_session_receipt_id);
        if (receipt) { previous = receipt; break; }
      }
    } catch { previous = null; }
    this.productSessions.set(key, previous);
    return previous;
  }

  attachProductSession(workspace, observations, url) {
    const current = productSessionReceipt(url);
    if (!current) return Array.isArray(observations) ? observations : [];
    const key = path.resolve(workspace);
    const previous = this.lastProductSessionReceipt(workspace);
    const transition = !previous ? 'observed' : previous === current ? 'same' : 'rotated';
    this.productSessions.set(key, current);
    return (Array.isArray(observations) ? observations : []).map((value) => ({
      ...value,
      product_session_receipt_id: current,
      product_session_transition: transition,
      ...(transition === 'rotated' ? { prior_product_session_receipt_id: previous } : {})
    }));
  }

  append(workspace, observations) {
    const normalized = (Array.isArray(observations) ? observations : [])
      .slice(0, HOST_OBSERVATION_MAX_BUFFER)
      .map(normalizeHostObservation)
      .filter(Boolean);
    if (!normalized.length) return { appended: 0, path: journalPath(workspace) };

    const target = journalPath(workspace);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    const payload = normalized.map((item) => JSON.stringify(item)).join('\n') + '\n';
    let currentBytes = 0;
    try { currentBytes = fs.statSync(target).size; } catch { currentBytes = 0; }
    if (currentBytes > 0 && currentBytes + Buffer.byteLength(payload) > this.maxBytes) {
      const backup = `${target}.1`;
      try { fs.rmSync(backup, { force: true }); } catch { /* best effort */ }
      fs.renameSync(target, backup);
    }
    fs.appendFileSync(target, payload, { encoding: 'utf8', mode: 0o600 });
    return { appended: normalized.length, path: target };
  }

  stagePendingTurns(workspace, observations) {
    let staged = 0;
    for (const value of Array.isArray(observations) ? observations : []) {
      const event = normalizeHostObservation(value);
      if (!event || event.event_type !== 'user_turn_visible') continue;
      writeOneShotJson(pendingTurnPath(workspace), {
        schema_version: HOST_CORRELATION_SCHEMA_VERSION,
        turn_id: event.turn_id,
        trace_id: event.trace_id,
        ...(event.product_session_receipt_id ? { product_session_receipt_id: event.product_session_receipt_id } : {}),
        ...(event.prior_product_session_receipt_id ? { prior_product_session_receipt_id: event.prior_product_session_receipt_id } : {}),
        ...(event.product_session_transition ? { product_session_transition: event.product_session_transition } : {}),
        staged_at_unix_ms: Date.now()
      });
      staged += 1;
    }
    return staged;
  }

  attachExplicitBindings(workspace, observations) {
    const binding = normalizedBinding(workspace);
    return (Array.isArray(observations) ? observations : []).map((value) => {
      const event = normalizeHostObservation(value);
      if (!event || !binding || event.turn_id !== binding.turn_id || event.trace_id !== binding.trace_id) return event;
      return normalizeHostObservation({ ...event, run_id: binding.run_id, wave_id: binding.wave_id });
    }).filter(Boolean);
  }

  clearPendingTurn(workspace, observation) {
    const event = normalizeHostObservation(observation);
    if (!event) return false;
    const target = pendingTurnPath(workspace);
    const value = readOneShotJson(target);
    if (!value || value.schema_version !== HOST_CORRELATION_SCHEMA_VERSION || value.turn_id !== event.turn_id || value.trace_id !== event.trace_id) return false;
    try { fs.rmSync(target, { force: true }); return true; } catch { return false; }
  }

  consumeBinding(workspace, observation) {
    const event = normalizeHostObservation(observation);
    const binding = normalizedBinding(workspace);
    if (!event || !binding || event.turn_id !== binding.turn_id || event.trace_id !== binding.trace_id) return false;
    try { fs.rmSync(bindingTurnPath(workspace), { force: true }); return true; } catch { return false; }
  }

  finalizeCorrelation(workspace, observation) {
    const event = normalizeHostObservation(observation);
    if (!event || !['host_turn_span', 'controller_usage'].includes(event.event_type)) {
      return { pending_cleared: false, binding_consumed: false };
    }
    const key = `${path.resolve(workspace)}\u0000${event.turn_id}\u0000${event.trace_id}`;
    const phases = this.correlationCompletion.get(key) || { host_span: false, controller_usage: false };
    if (event.event_type === 'host_turn_span') phases.host_span = true;
    if (event.event_type === 'controller_usage' && event.run_id && event.wave_id) phases.controller_usage = true;
    this.correlationCompletion.set(key, phases);
    if (this.correlationCompletion.size > 64) {
      const oldest = this.correlationCompletion.keys().next().value;
      if (oldest) this.correlationCompletion.delete(oldest);
    }
    const pendingCleared = event.event_type === 'host_turn_span' ? this.clearPendingTurn(workspace, event) : false;
    const bindingConsumed = phases.host_span && phases.controller_usage && event.run_id && event.wave_id
      ? this.consumeBinding(workspace, event)
      : false;
    if (bindingConsumed) this.correlationCompletion.delete(key);
    return {
      pending_cleared: pendingCleared,
      binding_consumed: Boolean(bindingConsumed)
    };
  }
}

function buildChatEvaluationObserverScript({ navigationEpoch, clockDomain }) {
  const epoch = Math.max(0, Number(navigationEpoch) || 0);
  const domain = String(clockDomain || '').slice(0, 160);
  return `(() => {
    const KEY = '__mcpHostEvaluationTelemetry';
    const epoch = ${JSON.stringify(epoch)};
    const clockDomain = ${JSON.stringify(domain)};
    const existing = window[KEY];
    if (existing && existing.navigationEpoch === epoch && existing.clockDomain === clockDomain) return true;
    try { existing?.dispose?.(); } catch {}
    try { existing?.observer?.disconnect(); } catch {}
    const state = {
      navigationEpoch: epoch,
      clockDomain,
      observer: null,
      seenKeys: new Set(),
      seenNodes: new WeakSet(),
      controllerUsageSeen: new Set(),
      buffer: [],
      sequence: 0,
      debug: { sseStreams: 0, sseEvents: 0, sseCompleted: 0, sseUsageHits: 0, sseUsageRejected: 0, usageKeySamples: [], sseTypeSamples: [], featuresFinalized: 0, featuresInterim: 0 },
      pendingUser: null,
      pendingUserMetrics: null,
      finalizing: null,
      pendingIntentIdentity: null,
      lastTurn: null,
      armed: false,
      primeQuietTimer: null,
      primeDeadlineTimer: null,
      awaitingUserVisible: false,
      intentDeadlineMs: 0,
      intentBaselineOrdinal: -1,
      dispose: null
    };
    const sample = () => {
      const monotonic = performance.now();
      return { monotonic_ms: monotonic, wall_time_ms: performance.timeOrigin + monotonic };
    };
    // Text metrics, counts only. Authorized operator policy change: the
    // observer measures visible message length and code-block counts
    // in-memory to support per-turn token quantification. Only the numbers
    // leave this function; text is never stored, buffered, logged or
    // emitted, and no other content reader exists in the measurement path.
    const textMetrics = (node) => {
      try {
        const text = node && typeof node.textContent === 'string' ? node.textContent : '';
        const codeBlocks = node && node.querySelectorAll ? node.querySelectorAll('pre,code').length : 0;
        return { chars: text.length, codeBlocks };
      } catch {
        return { chars: 0, codeBlocks: 0 };
      }
    };
    const describeTurn = (node) => {
      const direct = node.getAttribute?.('data-message-author-role');
      if (direct === 'user' || direct === 'assistant') return { role: direct, roleNode: node };
      const roleNode = node.querySelector?.('[data-message-author-role="user"],[data-message-author-role="assistant"]');
      const role = roleNode?.getAttribute?.('data-message-author-role') || '';
      return role === 'user' || role === 'assistant' ? { role, roleNode } : { role: '', roleNode: null };
    };
    const turnNodes = () => {
      const turns = Array.from(document.querySelectorAll('[data-testid^="conversation-turn-"]'));
      return turns.length ? turns : Array.from(document.querySelectorAll('[data-message-author-role="user"],[data-message-author-role="assistant"]'));
    };
    const stableTurnKey = (node) => {
      const direct = node.getAttribute?.('data-testid') || '';
      if (direct.startsWith('conversation-turn-')) return direct;
      const owner = node.closest?.('[data-testid^="conversation-turn-"]');
      return owner?.getAttribute?.('data-testid') || '';
    };
    const turnOrdinal = (node) => {
      const match = stableTurnKey(node).match(/conversation-turn-(\d+)$/);
      return match ? Number(match[1]) : null;
    };
    const alreadySeen = (node) => {
      const key = stableTurnKey(node);
      return key ? state.seenKeys.has(key) : state.seenNodes.has(node);
    };
    const markSeen = (node) => {
      const key = stableTurnKey(node);
      if (key) state.seenKeys.add(key);
      else state.seenNodes.add(node);
    };
    const isStructurallyVisible = (node, role) => {
      if (!node?.isConnected) return false;
      try {
        if (typeof node.checkVisibility === 'function' && !node.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) return false;
      } catch {}
      const rects = node.getClientRects?.();
      if (!rects || !Array.from(rects).some((rect) => rect.width > 0 && rect.height > 0)) return false;
      if (role === 'assistant' && !node.querySelector?.('.markdown,p,pre,code,table,ul,ol,blockquote,img')) return false;
      return true;
    };
    const push = (event) => {
      state.buffer.push(event);
      if (state.buffer.length > ${HOST_OBSERVATION_MAX_BUFFER}) state.buffer.splice(0, state.buffer.length - ${HOST_OBSERVATION_MAX_BUFFER});
    };
    const exactInteger = (value) => Number.isSafeInteger(value) && value >= 0 ? value : null;
    const structuredResponseUsage = (node) => {
      if (!node || typeof node !== 'object' || Array.isArray(node)) return null;
      let response = null;
      if (node.type === 'response.completed' && node.response && typeof node.response === 'object' && !Array.isArray(node.response)) {
        response = node.response;
      } else if (node.object === 'response' && node.status === 'completed') {
        response = node;
      } else if (node.status === 'completed' && /^resp[_-]/.test(String(node.id || '')) && node.usage) {
        response = node;
      }
      const usage = response?.usage;
      if (!usage || typeof usage !== 'object' || Array.isArray(usage)) return null;
      const inputTokens = exactInteger(usage.input_tokens);
      const cachedInputTokens = exactInteger(usage.input_tokens_details?.cached_tokens);
      const outputTokens = exactInteger(usage.output_tokens);
      const reasoningOutputTokens = exactInteger(usage.output_tokens_details?.reasoning_tokens);
      if (inputTokens === null || cachedInputTokens === null || outputTokens === null || reasoningOutputTokens === null
        || cachedInputTokens > inputTokens || reasoningOutputTokens > outputTokens) return null;
      const modelId = typeof response.model === 'string' && response.model.length <= 200 ? response.model : '';
      return { inputTokens, cachedInputTokens, outputTokens, reasoningOutputTokens, modelId };
    };
    const currentUsageIdentity = () => {
      if (state.pendingUser) return { turnId: state.pendingUser.turnId, traceId: state.pendingUser.traceId };
      if (state.pendingIntentIdentity && (state.awaitingUserVisible || performance.now() <= state.intentDeadlineMs)) {
        return state.pendingIntentIdentity;
      }
      if (state.lastTurn && performance.now() - state.lastTurn.completedAtMs <= 120000) {
        return { turnId: state.lastTurn.turnId, traceId: state.lastTurn.traceId };
      }
      return null;
    };
    const emitControllerUsage = (usage) => {
      const identity = currentUsageIdentity();
      if (!identity) return;
      const fingerprint = [identity.turnId, usage.inputTokens, usage.cachedInputTokens, usage.outputTokens, usage.reasoningOutputTokens].join(':');
      if (state.controllerUsageSeen.has(fingerprint)) return;
      state.controllerUsageSeen.add(fingerprint);
      const at = sample();
      push({
        schema_version: ${HOST_OBSERVATION_SCHEMA_VERSION},
        event_type: 'controller_usage',
        observation_id: epoch + ':controller_usage:' + (++state.sequence),
        navigation_epoch: epoch,
        clock_domain: clockDomain,
        monotonic_ms: at.monotonic_ms,
        wall_time_ms: at.wall_time_ms,
        turn_id: identity.turnId,
        trace_id: identity.traceId,
        observer_plane: 'electron_chatgpt_structured_response',
        measurement: 'structured_response_usage_exact',
        accounting_profile: 'openai_compatible',
        provider_id: 'openai',
        ...(usage.modelId ? { model_id: usage.modelId } : {}),
        source: 'client_reported',
        input_tokens: usage.inputTokens,
        cached_input_tokens: usage.cachedInputTokens,
        output_tokens: usage.outputTokens,
        reasoning_output_tokens: usage.reasoningOutputTokens
      });
    };
    const usageBootstrap = window.__mcpStructuredUsageBootstrap;
    let unsubscribeUsageBootstrap = null;
    const structuredUsageEnvelopeChildren = (node) => {
      if (!node || typeof node !== 'object' || Array.isArray(node)) return [];
      const children = [];
      for (const key of ['data', 'event']) {
        const child = node[key];
        if (child && typeof child === 'object' && !Array.isArray(child)) children.push(child);
      }
      return children;
    };
    const inspectStructuredUsage = (value) => {
      if (!value || typeof value !== 'object' || Array.isArray(value)) return;
      const queue = [{ value, depth: 0 }];
      let inspected = 0;
      while (queue.length && inspected < 8) {
        const item = queue.shift();
        const current = item?.value;
        if (!current || typeof current !== 'object' || Array.isArray(current)) continue;
        inspected += 1;
        const usage = structuredResponseUsage(current);
        if (usage) {
          emitControllerUsage(usage);
          return;
        }
        if (item.depth >= 2) continue;
        for (const child of structuredUsageEnvelopeChildren(current)) {
          queue.push({ value: child, depth: item.depth + 1 });
        }
      }
    };
    let originalJsonParse = null;
    let parseWithUsageObservation = null;
    let originalResponseJson = null;
    let responseJsonWithUsageObservation = null;
    ${sseFetchObservationScopeSnippet()}
    if (usageBootstrap && usageBootstrap.schemaVersion === 1 && typeof usageBootstrap.subscribe === 'function') {
      unsubscribeUsageBootstrap = usageBootstrap.subscribe((usage) => emitControllerUsage(usage));
    } else {
      originalJsonParse = JSON.parse;
      parseWithUsageObservation = function (...args) {
        const parsed = originalJsonParse.apply(this, args);
        try { inspectStructuredUsage(parsed); } catch {}
        return parsed;
      };
      JSON.parse = parseWithUsageObservation;
      ${sseFetchObservationSnippet()}
      try { installFetchSseObservation(); } catch {}
      originalResponseJson = globalThis.Response?.prototype?.json;
      if (typeof originalResponseJson === 'function') {
        responseJsonWithUsageObservation = async function (...args) {
          const parsed = await originalResponseJson.apply(this, args);
          try { inspectStructuredUsage(parsed); } catch {}
          return parsed;
        };
        globalThis.Response.prototype.json = responseJsonWithUsageObservation;
      }
    }
    const visibleTurns = () => turnNodes().map((node) => {
      const described = describeTurn(node);
      return { node, role: described.role, roleNode: described.roleNode, ordinal: turnOrdinal(node) };
    }).filter((item) => item.role && isStructurallyVisible(item.roleNode, item.role));
    const createTurnIdentity = () => {
      const raw = globalThis.crypto?.randomUUID?.() || (Date.now().toString(36) + '-' + Math.random().toString(36).slice(2));
      const bytes = new Uint8Array(16);
      if (globalThis.crypto?.getRandomValues) globalThis.crypto.getRandomValues(bytes);
      else for (let index = 0; index < bytes.length; index += 1) bytes[index] = Math.floor(Math.random() * 256);
      let traceId = Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('');
      if (/^0{32}$/.test(traceId)) traceId = traceId.slice(0, -1) + '1';
      return { turnId: 'chatweb-turn:' + raw, traceId };
    };
    const emitVisible = (item, at, identity) => {
      const observationId = epoch + ':' + item.role + ':' + (++state.sequence);
      push({
        schema_version: ${HOST_OBSERVATION_SCHEMA_VERSION},
        event_type: item.role === 'user' ? 'user_turn_visible' : 'assistant_response_first_visible',
        observation_id: observationId,
        navigation_epoch: epoch,
        clock_domain: clockDomain,
        monotonic_ms: at.monotonic_ms,
        wall_time_ms: at.wall_time_ms,
        turn_id: identity.turnId,
        trace_id: identity.traceId,
        observer_plane: 'electron_chatgpt_dom',
        measurement: 'observed_host_visible'
      });
      return observationId;
    };
    const scan = () => {
      if (!state.awaitingUserVisible && !state.pendingUser && !state.finalizing) return;
      const turns = visibleTurns();
      if (!turns.length) {
        if (state.finalizing) finalizeTurnFeatures(true);
        return;
      }
      const latest = turns[turns.length - 1];
      for (const item of turns.slice(0, -1)) markSeen(item.node);
      if (state.awaitingUserVisible && performance.now() > state.intentDeadlineMs) {
        state.awaitingUserVisible = false;
        state.pendingUser = null;
        state.pendingUserMetrics = null;
        state.pendingIntentIdentity = null;
      }
      if (latest.role === 'user' && state.awaitingUserVisible && !alreadySeen(latest.node)) {
        if (latest.ordinal !== null && latest.ordinal <= state.intentBaselineOrdinal) {
          markSeen(latest.node);
          return;
        }
        const at = sample();
        const identity = state.pendingIntentIdentity || createTurnIdentity();
        const observationId = emitVisible(latest, at, identity);
        markSeen(latest.node);
        state.awaitingUserVisible = false;
        state.pendingIntentIdentity = null;
        state.pendingUser = { observationId, monotonicMs: at.monotonic_ms, ordinal: latest.ordinal, ...identity };
        state.pendingUserMetrics = textMetrics(latest.roleNode);
        return;
      }
      if (latest.role === 'assistant' && state.pendingUser && !alreadySeen(latest.node)) {
        if (latest.ordinal !== null && state.pendingUser.ordinal !== null && latest.ordinal <= state.pendingUser.ordinal) {
          markSeen(latest.node);
          return;
        }
        const at = sample();
        const identity = { turnId: state.pendingUser.turnId, traceId: state.pendingUser.traceId };
        const observationId = emitVisible(latest, at, identity);
        markSeen(latest.node);
        push({
          schema_version: ${HOST_OBSERVATION_SCHEMA_VERSION},
          event_type: 'host_turn_span',
          span_id: state.pendingUser.observationId + '->' + observationId,
          user_observation_id: state.pendingUser.observationId,
          assistant_observation_id: observationId,
          navigation_epoch: epoch,
          clock_domain: clockDomain,
          start_ms: state.pendingUser.monotonicMs,
          end_ms: at.monotonic_ms,
          duration_ms: Math.max(0, at.monotonic_ms - state.pendingUser.monotonicMs),
          turn_id: identity.turnId,
          trace_id: identity.traceId,
          observer_plane: 'electron_chatgpt_dom',
          measurement: 'observed_user_visible_to_first_assistant_visible'
        });
        // Finalized structural features (P0): the span above marks
        // first-visible TIMING, but counts are only meaningful at turn end.
        // Sampling at first-visible undercounts streaming answers, so start
        // the finalizing phase instead: exactly one turn_features is
        // emitted when the assistant DOM goes quiet, on timeout, or when a
        // new turn starts. Numeric only, no message content.
        state.finalizing = {
          identity,
          userObservationId: state.pendingUser.observationId,
          assistantObservationId: observationId,
          monotonicStart: state.pendingUser.monotonicMs,
          userMetrics: state.pendingUserMetrics || { chars: 0, codeBlocks: 0 },
          lastAsstChars: textMetrics(latest.roleNode).chars,
          lastAsstCode: textMetrics(latest.roleNode).codeBlocks,
          lastOrdinal: latest.ordinal,
          lastInterimEmitMs: at.monotonic_ms,
          lastChangeMs: at.monotonic_ms,
          startMs: at.monotonic_ms
        };
        state.lastTurn = { ...identity, completedAtMs: at.monotonic_ms };
        state.pendingUser = null;
        state.pendingUserMetrics = null;
        return;
      }
      if (!state.awaitingUserVisible && !state.pendingUser && !state.finalizing) markSeen(latest.node);
      if (state.finalizing && !state.pendingUser) updateFinalizing();
    };
    // Turn-end finalization: re-measure the latest visible assistant turn on
    // every scan; emit once after QUIET_MS without text growth, on timeout,
    // or when forced (new turn / empty page). Abandoned turns (navigation
    // dispose) keep span timing but no features: unknown, never zero.
    const finalizeTurnFeatures = (force) => {
      const fin = state.finalizing;
      if (!fin) return;
      const at = sample();
      if (force !== true && at.monotonic_ms - fin.lastChangeMs < 1000) return;
      pushFeaturesSnapshot(fin, at);
      state.debug.featuresFinalized += 1;
      state.finalizing = null;
    };
    // Shared snapshot builder: interim progress and the final measurement
    // share one shape. Downstream keeps the latest snapshot per turn, so
    // interim numbers tick live during streaming without double-counting.
    const pushFeaturesSnapshot = (fin, at) => {
      let toolCards = 0;
      try {
        const turns = visibleTurns();
        let node = null;
        for (let i = turns.length - 1; i >= 0; i -= 1) {
          if (turns[i].role === 'assistant') { node = turns[i].node; break; }
        }
        toolCards = node && node.querySelectorAll
          ? node.querySelectorAll('[data-mcp-tool-summary="1"]').length
          : 0;
      } catch {}
      push({
        schema_version: ${HOST_OBSERVATION_SCHEMA_VERSION},
        event_type: 'turn_features',
        observation_id: fin.assistantObservationId + ':features',
        navigation_epoch: epoch,
        clock_domain: clockDomain,
        monotonic_ms: at.monotonic_ms,
        wall_time_ms: at.wall_time_ms,
        turn_id: fin.identity.turnId,
        trace_id: fin.identity.traceId,
        observer_plane: 'electron_chatgpt_dom',
        measurement: 'structural_turn_features',
        turn_ordinal: fin.lastOrdinal,
        duration_ms: Math.max(0, at.monotonic_ms - fin.monotonicStart),
        tool_card_count: toolCards,
        user_chars: fin.userMetrics.chars,
        user_code_blocks: fin.userMetrics.codeBlocks,
        asst_chars: fin.lastAsstChars,
        asst_code_blocks: fin.lastAsstCode
      });
    };
    const updateFinalizing = () => {
      const fin = state.finalizing;
      if (!fin || state.pendingUser) return;
      const turns = visibleTurns();
      if (!turns.length) {
        finalizeTurnFeatures(true);
        return;
      }
      let current = null;
      for (let i = turns.length - 1; i >= 0; i -= 1) {
        if (turns[i].role === 'assistant') { current = turns[i]; break; }
      }
      if (!current) {
        finalizeTurnFeatures(true);
        return;
      }
      const metrics = textMetrics(current.roleNode);
      if (metrics.chars !== fin.lastAsstChars || metrics.codeBlocks !== fin.lastAsstCode) {
        fin.lastAsstChars = metrics.chars;
        fin.lastAsstCode = metrics.codeBlocks;
        fin.lastChangeMs = performance.now();
        // Streaming interim: emit progress at most every 3s while the answer
        // grows. Same shape as the final event; downstream keeps the latest
        // snapshot per turn, so live numbers never double-count.
        if (fin.lastChangeMs - (fin.lastInterimEmitMs || 0) >= 3000) {
          fin.lastInterimEmitMs = fin.lastChangeMs;
          pushFeaturesSnapshot(fin, sample());
          state.debug.featuresInterim += 1;
        }
      }
      if (current.ordinal !== null) fin.lastOrdinal = current.ordinal;
      if (performance.now() - fin.startMs >= 600000) finalizeTurnFeatures(true);
      else finalizeTurnFeatures(false);
    };
    let scanScheduled = false;
    const scheduleScan = () => {
      if (scanScheduled) return;
      scanScheduled = true;
      requestAnimationFrame(() => {
        scanScheduled = false;
        scan();
      });
    };
    const finishPriming = () => {
      if (state.armed) return;
      if (state.primeQuietTimer) clearTimeout(state.primeQuietTimer);
      if (state.primeDeadlineTimer) clearTimeout(state.primeDeadlineTimer);
      state.primeQuietTimer = null;
      state.primeDeadlineTimer = null;
      turnNodes().forEach(markSeen);
      state.pendingUser = null;
      state.pendingUserMetrics = null;
      state.pendingIntentIdentity = null;
      state.armed = true;
    };
    const schedulePriming = () => {
      if (state.armed) return;
      if (state.primeQuietTimer) clearTimeout(state.primeQuietTimer);
      state.primeQuietTimer = setTimeout(finishPriming, 750);
      if (!state.primeDeadlineTimer) state.primeDeadlineTimer = setTimeout(finishPriming, 5000);
    };
    const noteUserIntent = () => {
      if (!state.armed) return;
      // A new turn while the previous one is still finalizing: flush the old
      // turn first so every turn keeps exactly one canonical measurement.
      if (state.finalizing) finalizeTurnFeatures(true);
      const ordinals = turnNodes().map(turnOrdinal).filter((value) => value !== null);
      state.intentBaselineOrdinal = ordinals.length ? Math.max(...ordinals) : -1;
      state.intentDeadlineMs = performance.now() + 15000;
      state.awaitingUserVisible = true;
      state.pendingUser = null;
      state.pendingIntentIdentity = createTurnIdentity();
      scheduleScan();
    };
    const onSubmit = (event) => {
      if (event.target?.querySelector?.('textarea,[contenteditable="true"]')) noteUserIntent();
    };
    const onClick = (event) => {
      if (event.target?.closest?.('button[data-testid="send-button"]')) noteUserIntent();
    };
    const onKeyDown = (event) => {
      if (event.key !== 'Enter' || event.shiftKey || event.altKey || event.ctrlKey || event.metaKey || event.isComposing) return;
      if (event.target?.closest?.('textarea,[contenteditable="true"]')) noteUserIntent();
    };
    const target = document.querySelector('main') || document.body;
    state.observer = new MutationObserver(() => {
      if (!state.armed) {
        schedulePriming();
        return;
      }
      if (state.awaitingUserVisible || state.pendingUser || state.finalizing) scheduleScan();
    });
    if (target) state.observer.observe(target, { childList: true, subtree: true });
    document.addEventListener('submit', onSubmit, true);
    document.addEventListener('click', onClick, true);
    document.addEventListener('keydown', onKeyDown, true);
    state.dispose = () => {
      try { state.observer?.disconnect(); } catch {}
      if (state.primeQuietTimer) clearTimeout(state.primeQuietTimer);
      if (state.primeDeadlineTimer) clearTimeout(state.primeDeadlineTimer);
      try { unsubscribeUsageBootstrap?.(); } catch {}
      try { restoreFetchSseObservation(); } catch {}
      if (parseWithUsageObservation && JSON.parse === parseWithUsageObservation) JSON.parse = originalJsonParse;
      if (responseJsonWithUsageObservation && globalThis.Response?.prototype?.json === responseJsonWithUsageObservation) {
        globalThis.Response.prototype.json = originalResponseJson;
      }
      document.removeEventListener('submit', onSubmit, true);
      document.removeEventListener('click', onClick, true);
      document.removeEventListener('keydown', onKeyDown, true);
      if (window[KEY] === state) {
        try { delete window[KEY]; } catch { window[KEY] = null; }
      }
    };
    schedulePriming();
    window[KEY] = state;
    return true;
  })()`;
}

function chatEvaluationDrainScript() {
  return `(() => {
    const state = window.__mcpHostEvaluationTelemetry;
    if (!state || !Array.isArray(state.buffer) || state.buffer.length === 0) return [];
    return state.buffer.splice(0, ${HOST_OBSERVATION_MAX_BUFFER});
  })()`;
}

// Read-only seam telemetry for the token canary. Returns bounded in-page
// counters only (no content); used by the operator to classify a silent seam:
// no streams vs no completed frames vs completed without exact usage fields
// vs usage seen but not emitted downstream.
function chatEvaluationDebugScript() {
  return `(() => {
    const out = { fetchHook: Boolean(window.__mcpUsageSseHookInstalled) };
    try {
      const bootstrap = window.__mcpStructuredUsageBootstrap;
      if (bootstrap && bootstrap.debug) {
        out.bootstrap = {
          sseStreams: bootstrap.debug.sseStreams || 0,
          sseEvents: bootstrap.debug.sseEvents || 0,
          sseCompleted: bootstrap.debug.sseCompleted || 0,
          sseUsageHits: bootstrap.debug.sseUsageHits || 0,
          sseUsageRejected: bootstrap.debug.sseUsageRejected || 0,
          usageKeySamples: (bootstrap.debug.usageKeySamples || []).slice(0, 8),
          sseTypeSamples: (bootstrap.debug.sseTypeSamples || []).slice(0, 16),
          featuresFinalized: bootstrap.debug.featuresFinalized || 0,
          featuresInterim: bootstrap.debug.featuresInterim || 0
        };
      }
    } catch (ignoredBootstrapDebug) {}
    try {
      const telemetry = window.__mcpHostEvaluationTelemetry;
      if (telemetry && telemetry.debug) {
        out.observer = {
          sseStreams: telemetry.debug.sseStreams || 0,
          sseEvents: telemetry.debug.sseEvents || 0,
          sseCompleted: telemetry.debug.sseCompleted || 0,
          sseUsageHits: telemetry.debug.sseUsageHits || 0,
          sseUsageRejected: telemetry.debug.sseUsageRejected || 0,
          usageKeySamples: (telemetry.debug.usageKeySamples || []).slice(0, 8),
          sseTypeSamples: (telemetry.debug.sseTypeSamples || []).slice(0, 16),
          featuresFinalized: telemetry.debug.featuresFinalized || 0,
          featuresInterim: telemetry.debug.featuresInterim || 0
        };
      }
    } catch (ignoredObserverDebug) {}
    return out;
  })()`;
}

module.exports = {
  ChatEvaluationJournal,
  normalizeHostObservation,
  productSessionReceipt,
  buildChatEvaluationBootstrapScript,
  buildChatEvaluationObserverScript,
  chatEvaluationDrainScript,
  chatEvaluationDebugScript,
  journalPath,
  pendingTurnPath,
  bindingTurnPath,
  HOST_OBSERVATION_MAX_BUFFER,
  HOST_OBSERVATION_MAX_JOURNAL_BYTES,
  HOST_OBSERVATION_SCHEMA_VERSION,
  HOST_CORRELATION_SCHEMA_VERSION
};
