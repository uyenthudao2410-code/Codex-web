const fs = require('node:fs');
const path = require('node:path');

const HOST_OBSERVATION_SCHEMA_VERSION = 5;
const HOST_OBSERVATION_MAX_BUFFER = 256;
const HOST_OBSERVATION_MAX_JOURNAL_BYTES = 2 * 1024 * 1024;
const HOST_CORRELATION_SCHEMA_VERSION = 1;
const HOST_CORRELATION_BINDING_TTL_MS = 60 * 60 * 1000;
const EVENT_TYPES = new Set(['user_turn_visible', 'assistant_response_first_visible', 'host_turn_span']);

function boundedText(value, maxLength, required = false) {
  const text = String(value ?? '').trim();
  if ((required && !text) || text.length > maxLength || /[\u0000-\u001f]/.test(text)) return null;
  return text;
}

function finiteNonNegative(value) {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : null;
}

function normalizeHostObservation(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const allowed = new Set([
    'schema_version', 'event_type', 'observation_id', 'span_id', 'navigation_epoch', 'clock_domain',
    'monotonic_ms', 'wall_time_ms', 'start_ms', 'end_ms', 'duration_ms', 'user_observation_id',
    'assistant_observation_id', 'observer_plane', 'measurement', 'trace_id', 'turn_id', 'run_id', 'wave_id'
  ]);
  if (Object.keys(value).some((key) => !allowed.has(key))) return null;
  if (value.schema_version !== HOST_OBSERVATION_SCHEMA_VERSION || !EVENT_TYPES.has(value.event_type)) return null;

  const navigationEpoch = value.navigation_epoch;
  const clockDomain = boundedText(value.clock_domain, 160, true);
  const observerPlane = boundedText(value.observer_plane, 100, true);
  const measurement = boundedText(value.measurement, 100, true);
  const traceId = boundedText(value.trace_id, 128, true);
  const turnId = boundedText(value.turn_id, 128, true);
  const runId = boundedText(value.run_id, 128, false);
  const waveId = boundedText(value.wave_id, 128, false);
  if (!Number.isInteger(navigationEpoch) || navigationEpoch < 0 || !clockDomain || !observerPlane || !measurement || !traceId || !turnId) return null;
  if (Boolean(runId) !== Boolean(waveId)) return null;

  const common = {
    schema_version: HOST_OBSERVATION_SCHEMA_VERSION,
    event_type: value.event_type,
    navigation_epoch: navigationEpoch,
    clock_domain: clockDomain,
    observer_plane: observerPlane,
    measurement: measurement,
    trace_id: traceId,
    turn_id: turnId,
    ...(runId && waveId ? { run_id: runId, wave_id: waveId } : {})
  };

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
    if (!event || event.event_type !== 'host_turn_span') {
      return { pending_cleared: false, binding_consumed: false };
    }
    return {
      pending_cleared: this.clearPendingTurn(workspace, event),
      binding_consumed: Boolean(event.run_id && event.wave_id) && this.consumeBinding(workspace, event)
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
      buffer: [],
      sequence: 0,
      pendingUser: null,
      pendingIntentIdentity: null,
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
      if (!state.awaitingUserVisible && !state.pendingUser) return;
      const turns = visibleTurns();
      if (!turns.length) return;
      const latest = turns[turns.length - 1];
      for (const item of turns.slice(0, -1)) markSeen(item.node);
      if (state.awaitingUserVisible && performance.now() > state.intentDeadlineMs) {
        state.awaitingUserVisible = false;
        state.pendingUser = null;
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
        state.pendingUser = null;
        return;
      }
      if (!state.awaitingUserVisible && !state.pendingUser) markSeen(latest.node);
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
      if (state.awaitingUserVisible || state.pendingUser) scheduleScan();
    });
    if (target) state.observer.observe(target, { childList: true, subtree: true });
    document.addEventListener('submit', onSubmit, true);
    document.addEventListener('click', onClick, true);
    document.addEventListener('keydown', onKeyDown, true);
    state.dispose = () => {
      try { state.observer?.disconnect(); } catch {}
      if (state.primeQuietTimer) clearTimeout(state.primeQuietTimer);
      if (state.primeDeadlineTimer) clearTimeout(state.primeDeadlineTimer);
      document.removeEventListener('submit', onSubmit, true);
      document.removeEventListener('click', onClick, true);
      document.removeEventListener('keydown', onKeyDown, true);
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

module.exports = {
  ChatEvaluationJournal,
  normalizeHostObservation,
  buildChatEvaluationObserverScript,
  chatEvaluationDrainScript,
  journalPath,
  pendingTurnPath,
  bindingTurnPath,
  HOST_OBSERVATION_MAX_BUFFER,
  HOST_OBSERVATION_MAX_JOURNAL_BYTES,
  HOST_OBSERVATION_SCHEMA_VERSION,
  HOST_CORRELATION_SCHEMA_VERSION
};
