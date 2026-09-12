const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'renderer/control-center.js'), 'utf8');

function makeElement() {
  const classes = new Set();
  const element = {
    textContent: '',
    className: '',
    dataset: {},
    style: {},
    disabled: false,
    classList: {
      add(...names) { names.forEach((name) => classes.add(name)); },
      remove(...names) { names.forEach((name) => classes.delete(name)); },
      toggle(name, enabled) {
        if (enabled) classes.add(name);
        else classes.delete(name);
      }
    },
    append() {},
    appendChild() {},
    addEventListener() {},
    closest() { return null; },
    querySelector() { return null; },
    querySelectorAll() { return []; },
    setAttribute() {},
    remove() {}
  };
  return element;
}

function makeEventTarget() {
  const handlers = new Map();
  return {
    addEventListener(type, listener) {
      if (!handlers.has(type)) handlers.set(type, new Set());
      handlers.get(type).add(listener);
    },
    removeEventListener(type, listener) {
      handlers.get(type)?.delete(listener);
    },
    dispatchEvent(event) {
      for (const listener of handlers.get(event?.type) || []) listener(event);
      return true;
    }
  };
}

class HarnessCustomEvent {
  constructor(type, init = {}) { this.type = type; this.detail = init.detail; }
}

function loadEmbeddedBridge() {
  const parentDocument = makeEventTarget();
  const childDocument = makeEventTarget();
  const apiCalls = { lightweightSnapshot: 0, liveOrchestration: 0 };
  const api = {
    lightweightSnapshot() { apiCalls.lightweightSnapshot += 1; return Promise.resolve({ ok: true, data: {} }); },
    liveOrchestration() { apiCalls.liveOrchestration += 1; return Promise.resolve({ ok: true, data: {} }); }
  };
  const parentWindow = { document: parentDocument, CustomEvent: HarnessCustomEvent };
  const windowObject = {
    mcpAssistant: api,
    location: { search: '?embedded=1' },
    parent: parentWindow,
    addEventListener() {}
  };
  vm.runInNewContext(source, {
    window: windowObject,
    document: childDocument,
    CustomEvent: HarnessCustomEvent,
    Promise,
    console
  }, { filename: 'renderer/control-center.js' });
  return { apiCalls, parentDocument, childDocument };
}

function loadControlCenter(status, {
  snapshotResponses = [{ ok: true, data: status }],
  orchestrationResponses = [{ ok: true, data: {} }],
  locationSearch = '',
  parentWindow = null
} = {}) {
  const elements = new Map();
  const eventHandlers = new Map();
  const pulses = [];
  let heartbeat = null;
  let snapshotIndex = 0;
  let orchestrationIndex = 0;
  const apiCalls = { lightweightSnapshot: 0, liveOrchestration: 0 };
  const nextResponse = async (responses, index) => {
    const response = responses[Math.min(index, responses.length - 1)];
    if (response instanceof Error) throw response;
    return response;
  };
  const document = {
    visibilityState: 'visible',
    querySelector(selector) {
      return selector === '.page.active' ? { dataset: { pageView: 'overview' } } : null;
    },
    querySelectorAll() { return []; },
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, makeElement());
      return elements.get(id);
    },
    createElement() { return makeElement(); },
    createElementNS() { return makeElement(); },
    addEventListener(type, listener) { eventHandlers.set(type, listener); },
    dispatchEvent(event) {
      if (event?.type === 'coding-tools:overview-pulse') pulses.push(event.detail);
    }
  };
  const api = {
    lightweightSnapshot: () => {
      apiCalls.lightweightSnapshot += 1;
      return nextResponse(snapshotResponses, snapshotIndex++);
    },
    liveOrchestration: () => {
      apiCalls.liveOrchestration += 1;
      return nextResponse(orchestrationResponses, orchestrationIndex++);
    },
    performanceTrace: async () => ({ ok: true, data: {} }),
    recordUiPerformance: async () => ({ ok: true }),
    onHeartbeat(listener) { heartbeat = listener; }
  };
  const noTimer = () => 0;
  const windowObject = {
    mcpAssistant: api,
    location: { search: locationSearch },
    performance: { now: () => 0 },
    matchMedia: () => ({ matches: false, addEventListener() {} }),
    setTimeout: noTimer,
    addEventListener() {}
  };
  windowObject.parent = parentWindow || windowObject;
  const context = {
    window: windowObject,
    document,
    CustomEvent: class CustomEvent {
      constructor(type, init = {}) { this.type = type; this.detail = init.detail; }
    },
    Date,
    Promise,
    console,
    setTimeout: noTimer
  };
  vm.runInNewContext(source, context, { filename: 'renderer/control-center.js' });
  return {
    elements,
    heartbeat: () => heartbeat,
    pulses,
    apiCalls,
    requestRefresh: () => eventHandlers.get('coding-tools:overview-refresh-request')?.()
  };
}

async function flushRenderer() {
  await new Promise((resolve) => setImmediate(resolve));
  await new Promise((resolve) => setImmediate(resolve));
}

function currentStatus(overrides = {}) {
  return {
    mcpRunning: true,
    tunnelRunning: true,
    fullyReady: true,
    recovering: false,
    recoveryBlocked: false,
    failures: 0,
    recoveryAttempts: 0,
    deferredRecoveryCount: 0,
    telemetryAvailable: true,
    signalStale: false,
    snapshotObservedAtUnixMs: Date.now() - 25,
    snapshotAgeMs: 25,
    staleAfterMs: 15_000,
    ...overrides
  };
}

test('embedded Control Center is a passive pulse bridge instead of a second snapshot/orchestration poller', () => {
  const harness = loadEmbeddedBridge();
  assert.deepEqual(harness.apiCalls, { lightweightSnapshot: 0, liveOrchestration: 0 });

  const observedPulses = [];
  harness.childDocument.addEventListener('coding-tools:overview-pulse', (event) => observedPulses.push(event.detail));
  const pulse = { snapshot: { status: { fullyReady: true } }, orchestration: { task: { status: 'active' } } };
  harness.parentDocument.dispatchEvent(new HarnessCustomEvent('coding-tools:overview-pulse', { detail: pulse }));
  assert.equal(observedPulses.length, 1);
  assert.equal(observedPulses[0], pulse);

  let parentRefreshes = 0;
  harness.parentDocument.addEventListener('coding-tools:overview-refresh-request', () => { parentRefreshes += 1; });
  harness.childDocument.dispatchEvent(new HarnessCustomEvent('coding-tools:overview-refresh-request'));
  assert.equal(parentRefreshes, 1);
  assert.deepEqual(harness.apiCalls, { lightweightSnapshot: 0, liveOrchestration: 0 });
});

test('embedded Control Center falls back to normal polling when parent document access is unavailable', async () => {
  const inaccessibleParent = {};
  Object.defineProperty(inaccessibleParent, 'document', {
    get() { throw new Error('cross-origin parent'); }
  });
  const harness = loadControlCenter(currentStatus(), {
    locationSearch: '?embedded=1',
    parentWindow: inaccessibleParent
  });
  await flushRenderer();
  assert.equal(harness.apiCalls.lightweightSnapshot, 1);
  assert.equal(harness.apiCalls.liveOrchestration, 1);
  assert.equal(harness.elements.get('ccHealthBadge').textContent, 'Operational');
});

test('Control Center uses a receipt timestamp and preserves unknown/stale heartbeat state instead of coercing it offline', async () => {
  const harness = loadControlCenter(currentStatus());
  await flushRenderer();

  assert.equal(harness.elements.get('ccHealthBadge').textContent, 'Operational');
  assert.equal(harness.elements.get('ccKpiRuntime').textContent, 'Online');
  assert.match(harness.elements.get('ccLastSync').textContent, /^Last receipt /);
  assert.match(harness.elements.get('ccLastSync').textContent, / · age /);

  const heartbeat = harness.heartbeat();
  assert.equal(typeof heartbeat, 'function');
  heartbeat({
    mcpRunning: null,
    tunnelRunning: null,
    fullyReady: false,
    telemetryAvailable: false,
    signalStale: true,
    staleAfterMs: 15_000
  });

  assert.equal(harness.elements.get('ccHealthBadge').textContent, 'UNKNOWN');
  assert.equal(harness.elements.get('ccKpiRuntime').textContent, 'UNKNOWN');
  assert.equal(harness.elements.get('ccKpiRuntimeMeta').textContent, 'Telemetry UNKNOWN · MCP UNKNOWN · Tunnel UNKNOWN');
  assert.equal(harness.elements.get('ccRecoveryState').textContent, 'UNKNOWN');
  assert.match(harness.elements.get('ccLastSync').textContent, /^Snapshot UNKNOWN · telemetry_unavailable$/);
  assert.doesNotMatch(harness.elements.get('ccKpiRuntimeMeta').textContent, /MCP OFF|Tunnel OFF/);

  heartbeat(currentStatus({ signalStale: true }));
  assert.equal(harness.elements.get('ccHealthBadge').textContent, 'UNKNOWN');
  assert.equal(harness.elements.get('ccKpiRuntime').textContent, 'UNKNOWN');
  assert.match(harness.elements.get('ccKpiRuntimeMeta').textContent, /^Telemetry STALE/);
  assert.match(harness.elements.get('ccLastSync').textContent, /^Snapshot STALE · signal_stale$/);

  heartbeat(currentStatus({ snapshotAgeMs: 15_001, staleAfterMs: 15_000 }));
  assert.equal(harness.elements.get('ccHealthBadge').textContent, 'UNKNOWN');
  assert.match(harness.elements.get('ccLastSync').textContent, /^Snapshot STALE · snapshot_age_expired$/);
});

test('Control Center emits stopped/MCP OFF/Tunnel OFF only from a fresh explicit false receipt', async () => {
  const harness = loadControlCenter(currentStatus({
    mcpRunning: false,
    tunnelRunning: false,
    fullyReady: false
  }));
  await flushRenderer();

  assert.equal(harness.elements.get('ccHealthBadge').textContent, 'Offline');
  assert.equal(harness.elements.get('ccKpiRuntime').textContent, 'Stopped');
  assert.equal(harness.elements.get('ccKpiRuntimeMeta').textContent, 'MCP OFF · Tunnel OFF');
  assert.match(harness.elements.get('ccLastSync').textContent, /^Last receipt /);
});

test('Control Center rejects malformed receipt numerics and recovery counters instead of Number-coercing them', async () => {
  const invalidTimestamp = loadControlCenter(currentStatus({ snapshotObservedAtUnixMs: [Date.now()] }));
  await flushRenderer();
  assert.equal(invalidTimestamp.elements.get('ccHealthBadge').textContent, 'UNKNOWN');
  assert.match(invalidTimestamp.elements.get('ccLastSync').textContent, /^Snapshot UNKNOWN · snapshot_receipt_missing$/);

  const invalidAge = loadControlCenter(currentStatus({ snapshotAgeMs: { value: 25 } }));
  await flushRenderer();
  assert.equal(invalidAge.elements.get('ccHealthBadge').textContent, 'UNKNOWN');
  assert.match(invalidAge.elements.get('ccLastSync').textContent, /^Snapshot UNKNOWN · snapshot_age_missing$/);

  const recovery = loadControlCenter(currentStatus());
  await flushRenderer();
  recovery.heartbeat()(currentStatus({
    failures: [],
    recoveryAttempts: { count: 1 },
    deferredRecoveryCount: [0]
  }));
  assert.equal(recovery.elements.get('ccRecoveryState').textContent, 'UNKNOWN');
  assert.equal(recovery.elements.get('ccRecoveryMeta').textContent, 'Recovery telemetry is incomplete.');
});

test('Control Center uses the documented 30-second supervision bound when a stale threshold is missing or invalid', async () => {
  const oldReceipt = currentStatus({
    snapshotObservedAtUnixMs: Date.now() - 31_000,
    snapshotAgeMs: 0
  });
  delete oldReceipt.signalStale;
  delete oldReceipt.staleAfterMs;
  const missingThreshold = loadControlCenter(oldReceipt);
  await flushRenderer();
  assert.equal(missingThreshold.elements.get('ccHealthBadge').textContent, 'UNKNOWN');
  assert.match(missingThreshold.elements.get('ccLastSync').textContent, /^Snapshot STALE · snapshot_age_expired$/);

  const invalidThreshold = loadControlCenter(currentStatus({
    snapshotObservedAtUnixMs: Date.now() - 31_000,
    snapshotAgeMs: 0,
    staleAfterMs: { ms: 60_000 }
  }));
  await flushRenderer();
  assert.equal(invalidThreshold.elements.get('ccHealthBadge').textContent, 'UNKNOWN');
  assert.match(invalidThreshold.elements.get('ccLastSync').textContent, /^Snapshot STALE · snapshot_age_expired$/);

  const unboundedThreshold = loadControlCenter(currentStatus({
    snapshotObservedAtUnixMs: Date.now() - 31_000,
    snapshotAgeMs: 0,
    staleAfterMs: 86_400_000
  }));
  await flushRenderer();
  assert.equal(unboundedThreshold.elements.get('ccHealthBadge').textContent, 'UNKNOWN');
  assert.match(unboundedThreshold.elements.get('ccLastSync').textContent, /^Snapshot STALE · snapshot_age_expired$/);
});

test('Control Center clears a failed live projection before publishing the next overview pulse', async () => {
  const status = currentStatus();
  const harness = loadControlCenter(status, {
    snapshotResponses: [{ ok: true, data: status }],
    orchestrationResponses: [
      { ok: true, data: { task: { status: 'active' } } },
      new Error('live control unavailable')
    ]
  });
  await flushRenderer();
  assert.deepEqual(harness.pulses.at(-1).orchestration, { task: { status: 'active' } });

  harness.requestRefresh();
  await flushRenderer();
  assert.equal(harness.pulses.at(-1).orchestration, null);
});

test('Control Center clears a failed runtime snapshot before publishing the next overview pulse', async () => {
  const status = currentStatus();
  const harness = loadControlCenter(status, {
    snapshotResponses: [
      { ok: true, data: status },
      new Error('runtime snapshot unavailable')
    ],
    orchestrationResponses: [{ ok: true, data: {} }]
  });
  await flushRenderer();
  assert.ok(harness.pulses.at(-1).snapshot);

  harness.requestRefresh();
  await flushRenderer();
  assert.equal(harness.pulses.at(-1).snapshot, null);
});

test('Control Center source never converts an absent heartbeat field into a false runtime claim', () => {
  assert.match(source, /function snapshotObservation\(payload\)/);
  assert.match(source, /payload\.telemetryAvailable !== true/);
  assert.match(source, /payload\.signalStale === true/);
  assert.match(source, /const SUPERVISION_STATUS_STALE_MS = 30000;/);
  assert.match(source, /typeof value !== 'number' && typeof value !== 'string'/);
  assert.match(source, /function snapshotSyncText\(payload\)/);
  assert.match(source, /Last receipt \$\{formatTime\(observation\.observedAtUnixMs\)\} · age/);
  assert.match(source, /snapshot\.status\.mcpRunning = exactBoolean\(health\?\.mcpRunning\)/);
  assert.match(source, /\} else orchestration = null;/);
  assert.doesNotMatch(source, /snapshot\.status\.runtimeRunning = Boolean\(health\?\.mcpRunning\)/);
  assert.doesNotMatch(source, /Last sync \$\{new Date\(\)\.toLocaleTimeString/);
});
