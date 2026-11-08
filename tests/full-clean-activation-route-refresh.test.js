const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { ActivationEpochStore } = require('../electron/services/activationEpoch');
const {
  FullCleanActivation,
  failingCensusPredicates,
  CENTRAL_ROUTE_REFRESH_TIMEOUT_MS,
  CENTRAL_ROUTE_REFRESH_THROTTLE_MS,
  PENDING_CENSUS_HISTORY_MAX_ENTRIES
} = require('../electron/services/fullCleanActivation');

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-route-refresh-'));
  const paths = createRuntimePaths({
    dataRoot: path.join(root, 'data'),
    resourcesRoot: path.join(root, 'resources'),
    appRoot: path.join(root, 'app')
  });
  fs.mkdirSync(paths.dataRoot(), { recursive: true });
  fs.mkdirSync(paths.resourcesRoot(), { recursive: true });
  fs.mkdirSync(paths.appRoot(), { recursive: true });
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return { root, paths };
}

function id(prefix, suffix = '0001') {
  return `${prefix}-${suffix}-000000000000`;
}

function epochStore(paths) {
  return new ActivationEpochStore({ paths, now: () => 1_700_000_000_000 });
}

const STALE = { connected: false, authorityReady: false, reason: 'CENTRAL_ROUTE_EVIDENCE_STALE', evidence: null };
const FRESH = { connected: true, authorityReady: true, reason: 'CENTRAL_ROUTE_READY', evidence: {} };

function refreshCoordinator(t, { route, nowMs }) {
  const { paths } = fixture(t);
  let now = nowMs;
  const calls = [];
  fs.mkdirSync(path.join(paths.appRoot(), 'control-plane', 'control_plane'), { recursive: true });
  fs.writeFileSync(paths.controlPlaneNodeAgent(), '');
  fs.writeFileSync(paths.controlPlaneNodeConfigFile(), '{}');
  fs.writeFileSync(paths.controlPlaneWorkspaceRegistryFile(), '{}');
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: epochStore(paths),
    orchestrator: { centralRouteEvidence: () => route },
    pythonStatusFn: async () => ({
      installed: true, command: 'python.exe', launchCommand: 'python.exe', prefixArgs: [], version: 'Python 3.12.0'
    }),
    execFileFn: async (command, args, options) => {
      calls.push({ command, args, options });
      route = FRESH;
      return { stdout: '', stderr: '' };
    },
    now: () => now
  });
  return {
    paths, coordinator, calls,
    setRoute: (value) => { route = value; },
    setNow: (value) => { now = value; }
  };
}

test('host refreshes stale central route evidence once through the agent heartbeat', async (t) => {
  const { paths, coordinator, calls } = refreshCoordinator(t, { route: STALE, nowMs: 1_700_000_000_000 });
  const result = await coordinator._refreshStaleCentralRouteEvidence({}, 1_700_000_000_000);

  assert.equal(calls.length, 1, 'stale evidence must trigger exactly one heartbeat refresh');
  assert.deepEqual(result, FRESH);
  assert.equal(calls[0].command, 'python.exe');
  assert.equal(calls[0].options.timeout, CENTRAL_ROUTE_REFRESH_TIMEOUT_MS);
  assert.equal(calls[0].options.timeout, 25_000);
  assert.deepEqual(calls[0].args, [
    '-I', paths.controlPlaneNodeAgent(), 'runtime-heartbeat',
    '--config', paths.controlPlaneNodeConfigFile(),
    '--project-root', paths.appRoot(),
    '--node', paths.executablePath(),
    '--runtime-mode', paths.runtimeMode(),
    '--timeout-seconds', '20',
    '--workspace-registry', paths.controlPlaneWorkspaceRegistryFile()
  ]);
});

test('host does not spawn a refresh for fresh or unrefreshable route evidence', async (t) => {
  const fresh = refreshCoordinator(t, { route: FRESH, nowMs: 1_700_000_000_000 });
  assert.deepEqual(await fresh.coordinator._refreshStaleCentralRouteEvidence({}, 1_700_000_000_000), FRESH);
  assert.equal(fresh.calls.length, 0, 'fresh evidence must not spawn a refresh');

  const missing = refreshCoordinator(t, { route: null, nowMs: 1_700_000_000_000 });
  assert.equal(await missing.coordinator._refreshStaleCentralRouteEvidence({}, 1_700_000_000_000), null);
  assert.equal(missing.calls.length, 0, 'no route result at all must not spawn a refresh');

  for (const reason of ['CENTRAL_ROUTE_EVIDENCE_DEVICE_MISMATCH', 'CENTRAL_LOCAL_DEVICE_IDENTITY_UNAVAILABLE']) {
    const route = { connected: false, authorityReady: false, reason, evidence: null };
    const { coordinator, calls } = refreshCoordinator(t, { route, nowMs: 1_700_000_000_000 });
    assert.deepEqual(await coordinator._refreshStaleCentralRouteEvidence({}, 1_700_000_000_000), route);
    assert.equal(calls.length, 0, `${reason} must not spawn a refresh`);
  }
});

test('host refreshes missing and invalid central route evidence', async (t) => {
  for (const reason of ['CENTRAL_ROUTE_EVIDENCE_MISSING', 'CENTRAL_ROUTE_EVIDENCE_INVALID']) {
    const route = { connected: false, authorityReady: false, reason, evidence: null };
    const { coordinator, calls } = refreshCoordinator(t, { route, nowMs: 1_700_000_000_000 });
    assert.deepEqual(await coordinator._refreshStaleCentralRouteEvidence({}, 1_700_000_000_000), FRESH);
    assert.equal(calls.length, 1, `${reason} must trigger a heartbeat refresh`);
  }
});

test('host refresh is throttled to one attempt per 30 s and fail-closed on spawn failure', async (t) => {
  const { coordinator, calls, setRoute, setNow } = refreshCoordinator(t, { route: STALE, nowMs: 1_700_000_000_000 });
  coordinator.execFileFn = async () => {
    calls.push({ failed: true });
    throw Object.assign(new Error('spawn failed'), { code: 'ENOENT' });
  };

  const failed = await coordinator._refreshStaleCentralRouteEvidence({}, 1_700_000_000_000);
  assert.deepEqual(failed, STALE, 'a failed refresh must keep the stale verdict');
  assert.equal(calls.length, 1);

  const throttled = await coordinator._refreshStaleCentralRouteEvidence({}, 1_700_000_000_000);
  assert.deepEqual(throttled, STALE);
  assert.equal(calls.length, 1, 'a second attempt inside the throttle window must not spawn');

  setNow(1_700_000_000_000 + CENTRAL_ROUTE_REFRESH_THROTTLE_MS + 1_000);
  coordinator.execFileFn = async () => {
    calls.push({ failed: false });
    setRoute(FRESH);
    return { stdout: '', stderr: '' };
  };
  const retried = await coordinator._refreshStaleCentralRouteEvidence({}, 1_700_000_000_000 + 31_000);
  assert.deepEqual(retried, FRESH, 'the next tick after the throttle must retry');
  assert.equal(calls.length, 2);
  assert.equal(CENTRAL_ROUTE_REFRESH_THROTTLE_MS, 30_000);
});

test('host does not spawn a refresh when the agent script or config is missing', async (t) => {
  const { paths, coordinator, calls, setNow } = refreshCoordinator(t, { route: STALE, nowMs: 1_700_000_000_000 });
  fs.rmSync(paths.controlPlaneNodeAgent());
  const noAgent = await coordinator._refreshStaleCentralRouteEvidence({}, 1_700_000_000_000);
  assert.deepEqual(noAgent, STALE);
  assert.equal(calls.length, 0, 'a missing agent script must not spawn');

  // Advance past the throttle so the second sub-case is judged on its own
  // missing path, not on the throttle left by the first attempt.
  setNow(1_700_000_000_000 + 31_000);
  fs.writeFileSync(paths.controlPlaneNodeAgent(), '');
  fs.rmSync(paths.controlPlaneNodeConfigFile());
  const noConfig = await coordinator._refreshStaleCentralRouteEvidence({}, 1_700_000_000_000 + 31_000);
  assert.deepEqual(noConfig, STALE);
  assert.equal(calls.length, 0, 'a missing node config must not spawn');
});

test('failingCensusPredicates lists only the predicates that failed, with their reasons', () => {
  assert.deepEqual(failingCensusPredicates({}), []);
  assert.deepEqual(failingCensusPredicates({ centralExecutor: true }), []);
  assert.deepEqual(failingCensusPredicates({
    centralExecutor: true,
    centralRouteVerified: false,
    centralStatusReason: 'CENTRAL_ROUTE_EVIDENCE_STALE',
    projectionRebuildValid: false,
    projectionRebuildCode: 'PREFLIGHT_RECEIPT_STALE',
    workspaceMatches: false,
    uiVerified: false
  }), [
    { name: 'workspace_matches', reason: null },
    { name: 'ui_verified', reason: null },
    { name: 'projection_rebuild_verified', reason: 'PREFLIGHT_RECEIPT_STALE' },
    { name: 'central_route_verified', reason: 'CENTRAL_ROUTE_EVIDENCE_STALE' }
  ]);
  assert.deepEqual(failingCensusPredicates({
    connectorReady: { valid: false, code: 'UPDATE_INCOMPLETE', reasons: ['CURRENT_CONTRACT_NOT_REDISCOVERED'] }
  }), [
    { name: 'connector_ready', reason: 'CURRENT_CONTRACT_NOT_REDISCOVERED' }
  ]);
});

test('recordPendingCensus keeps a bounded per-tick failing-predicate history', (t) => {
  assert.equal(PENDING_CENSUS_HISTORY_MAX_ENTRIES, 12);
  const { paths } = fixture(t);
  const store = epochStore(paths);
  const activationEpochId = id('activation-pending-history', '0001');
  const operationId = id('operation-pending-history', '0001');
  store.create({
    activation_epoch_id: activationEpochId,
    operation_id: operationId,
    expiresAtUnixMs: 1_700_000_120_000
  });
  store.update(activationEpochId, { state: 'VERIFYING', reason: 'initial-census' });
  const activation = new FullCleanActivation({
    paths,
    settings: { load: () => ({}) },
    secrets: { get: () => '' },
    orchestrator: {},
    recoveryPlane: {},
    revisions: {},
    deviceIdentity: {},
    epochStore: store,
    now: () => 1_700_000_000_000
  });

  for (let i = 0; i < 14; i += 1) {
    const census = {
      pass: false,
      verified: false,
      activation_epoch_id: activationEpochId,
      reason: 'UPDATE_INCOMPLETE',
      failing_predicates: [{ name: `predicate-${i}`, reason: null }]
    };
    const before = structuredClone(census);
    activation.recordPendingCensus(activationEpochId, census);
    assert.deepEqual(census, before, 'recordPendingCensus must not mutate the census it is given');
  }

  const history = store.current().verification.pending_census_history;
  assert.equal(history.length, 12, 'the history is bounded to the last 12 ticks');
  assert.equal(history[0].failing_predicates[0].name, 'predicate-2', 'the oldest entries are dropped first');
  assert.equal(history[11].failing_predicates[0].name, 'predicate-13');
  for (const entry of history) {
    assert.deepEqual(Object.keys(entry).sort(), ['failing_predicates', 'observed_at_ms']);
    assert.equal(entry.observed_at_ms, 1_700_000_000_000);
    assert.deepEqual(Object.keys(entry.failing_predicates[0]).sort(), ['name', 'reason']);
  }
  assert.deepEqual(
    history.map((entry) => entry.failing_predicates[0].name),
    ['predicate-2', 'predicate-3', 'predicate-4', 'predicate-5', 'predicate-6', 'predicate-7',
      'predicate-8', 'predicate-9', 'predicate-10', 'predicate-11', 'predicate-12', 'predicate-13']
  );
});
