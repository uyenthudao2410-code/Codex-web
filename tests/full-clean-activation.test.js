const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { ActivationEpochStore } = require('../electron/services/activationEpoch');
const { FullCleanActivation } = require('../electron/services/fullCleanActivation');
const { RecoveryHost } = require('../electron/services/recoveryHost');
const { RuntimeOrchestrator } = require('../electron/services/runtimeOrchestrator');

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-full-clean-'));
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

test('replacement startup failure terminalizes the activation epoch and keeps admission closed', async (t) => {
  const { root, paths } = fixture(t);
  const store = epochStore(paths);
  const created = store.create({
    activation_epoch_id: id('activation-epoch'),
    operation_id: id('operation-epoch'),
    components: ['recovery_host', 'coding_mcp', 'electron_ui']
  });
  const failure = Object.assign(new Error('replacement MCP failed to start'), { code: 'MCP_START_FAILED' });
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: store,
    settings: { load: () => ({ workspace: root }) },
    orchestrator: {
      setActivationEpoch() {},
      start: async () => { throw failure; }
    },
    now: () => 1_700_000_000_001
  });

  await assert.rejects(
    coordinator.continueReplacement({ activationEpochId: created.activation_epoch_id }),
    { code: 'MCP_START_FAILED' }
  );
  const terminal = store.current();
  assert.equal(terminal.state, 'FAILED');
  assert.equal(terminal.admission_state, 'CLOSED');
  assert.equal(terminal.error.code, 'MCP_START_FAILED');
});

test('full-clean failure after epoch creation stops owned old components before terminalizing', async (t) => {
  const { root, paths } = fixture(t);
  const store = epochStore(paths);
  const failure = Object.assign(new Error('activation fence raced with another lifecycle mutation'), { code: 'ACTIVATION_PREFLIGHT_UNVERIFIED' });
  const calls = [];
  const revisions = {
    status: () => ({ running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64), update_pending: false, state: 'current' })
  };
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: store,
    settings: { load: () => ({ workspace: root }) },
    revisions,
    recoveryInstanceId: 'old-recovery-host-0006',
    deviceIdentity: { device_id: 'device-0006', device_instance_id: 'old-recovery-host-0006' },
    orchestrator: {
      busy: false,
      recovering: false,
      inspectCodeActivation: async () => ({ safe: true, code: 'READY' }),
      prepareCodeActivation: async () => { throw failure; },
      currentMcpHealth: async () => null,
      codingMcpRevisionStatus: () => revisions.status(),
      setActivationEpoch() {},
      stop: async (options) => { calls.push(['runtime.stop', options]); return true; }
    },
    recoveryPlane: { stop: async () => { calls.push(['recovery-plane.stop']); } },
    getUiPresence: () => ({ alive: true, pid: process.pid + 1, instance_id: 'old-ui-000000000006' }),
    terminateUi: async () => { calls.push(['ui.stop']); },
    now: () => 1_700_000_000_020
  });

  await assert.rejects(
    coordinator.restart({
      operationId: id('operation-epoch', '0006'),
      expectedDiskRevision: 'a'.repeat(64)
    }),
    { code: 'ACTIVATION_PREFLIGHT_UNVERIFIED' }
  );
  assert.deepEqual(calls.map(([name]) => name), ['ui.stop', 'runtime.stop', 'recovery-plane.stop']);
  assert.equal(store.current().state, 'FAILED');
  assert.equal(store.current().admission_state, 'CLOSED');
});

test('Recovery Host replacement-start exceptions persist FAILED before ownership is released', async (t) => {
  const { root, paths } = fixture(t);
  const store = epochStore(paths);
  const created = store.create({
    activation_epoch_id: id('activation-epoch', '0002'),
    operation_id: id('operation-epoch', '0002'),
    components: ['recovery_host', 'coding_mcp', 'electron_ui'],
    component_evidence: {
      recovery_host: {
        instance_id: 'old-recovery-host-0001',
        pid: process.pid
      }
    }
  });
  const failure = Object.assign(new Error('replacement runtime unavailable'), { code: 'RUNTIME_START_FAILED' });
  const gateway = {
    start: async () => {},
    stop: async () => {}
  };
  const ipc = {
    start: async () => {},
    stop: async () => {}
  };
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ workspace: root, autoStartServices: false }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    gateway,
    ipcServerFactory: () => ipc,
    healthService: {},
    revisionTracker: {
      captureRunning: () => 'a'.repeat(64),
      status: () => ({ running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64), update_pending: false, state: 'current' })
    },
    orchestrator: {
      activationEpochId: created.activation_epoch_id,
      setActivationEpoch() {},
      start: async () => { throw failure; },
      codingMcpRevisionStatus: () => ({ running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64), update_pending: false, state: 'current' }),
      lightweightSnapshot: async () => ({ mcpRunning: false, tunnelRunning: false, fullyReady: false }),
      isManuallyStopped: () => false
    },
    recoveryPlaneService: {
      setActivationEpoch() {},
      stop: async () => {},
      ensure: async () => ({ state: 'healthy' })
    },
    replacement: { activationEpochId: created.activation_epoch_id },
    exitProcess: () => {}
  });

  await assert.rejects(host.start(), { code: 'RUNTIME_START_FAILED' });
  const terminal = store.current();
  assert.equal(terminal.state, 'FAILED');
  assert.equal(terminal.admission_state, 'CLOSED');
  assert.equal(terminal.error.code, 'RUNTIME_START_FAILED');
  assert.equal(fs.existsSync(paths.recoveryHostLockFile()), false);
});

test('Recovery Host remains available for an explicit retry after a FAILED epoch', async (t) => {
  const { root, paths } = fixture(t);
  const store = epochStore(paths);
  const created = store.create({
    activation_epoch_id: id('activation-epoch', '0007'),
    operation_id: id('operation-epoch', '0007')
  });
  store.fail(created.activation_epoch_id, { code: 'MCP_START_FAILED', message: 'previous replacement failed' });
  let recoveryEnsureCalls = 0;
  const gateway = { start: async () => {}, stop: async () => {} };
  const ipc = { start: async () => {}, stop: async () => {} };
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ workspace: root, autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    gateway,
    ipcServerFactory: () => ipc,
    healthService: {},
    revisionTracker: {
      captureRunning: () => 'a'.repeat(64),
      status: () => ({ running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64), update_pending: false, state: 'current' })
    },
    orchestrator: {
      activationEpochId: created.activation_epoch_id,
      setActivationEpoch() {},
      codingMcpRevisionStatus: () => ({ running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64), update_pending: false, state: 'current' }),
      lightweightSnapshot: async () => ({ mcpRunning: false, tunnelRunning: false, fullyReady: false }),
      isManuallyStopped: () => false
    },
    recoveryPlaneService: {
      setActivationEpoch() {},
      stop: async () => {},
      ensure: async () => { recoveryEnsureCalls += 1; return { state: 'healthy' }; }
    },
    exitProcess: () => {}
  });

  const status = await host.start();
  assert.equal(host.running, true);
  assert.equal(status.activation_epoch.state, 'FAILED');
  assert.equal(status.activation_epoch.admission_open, false);
  assert.equal(status.runtime, null);
  assert.equal(recoveryEnsureCalls, 0);
  await host.stop();
});

test('stopped-runtime retry requires and binds an unchanged independent ledger census', async (t) => {
  const { root, paths } = fixture(t);
  const store = epochStore(paths);
  const previous = store.create({
    activation_epoch_id: id('activation-epoch', '0008'),
    operation_id: id('operation-epoch', '0008'),
    components: ['recovery_host', 'coding_mcp', 'electron_ui']
  });
  store.fail(previous.activation_epoch_id, { code: 'MCP_START_FAILED', message: 'previous replacement failed' });
  const snapshot = {
    backup_api_copy: true,
    immutable: true,
    query_only: true,
    integrity_check: ['ok'],
    foreign_key_check_rows: 0,
    sha256: '1'.repeat(64),
    logical_sha256: '2'.repeat(64)
  };
  const census = {
    safe: true,
    code: 'READY',
    workspace: root,
    snapshot,
    counts: { active_commands: 0, active_background_operations: 0, active_managed_processes: 0, active_agent_lanes: 0 },
    lifecycle: { unexplained_active_runs: 0, unbound_live_resource_residues: 0, projection_drift: false, blockers: [] },
    census_fingerprint: '3'.repeat(64),
    content_free: true,
    mutated_canonical_ledger: false
  };
  let censusCalls = 0;
  let releaseCalls = 0;
  const spawnCalls = [];
  const revisions = {
    status: () => ({ running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64), update_pending: false, state: 'current' })
  };
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: store,
    settings: { load: () => ({ workspace: root }) },
    revisions,
    recoveryInstanceId: 'old-recovery-host-0008',
    deviceIdentity: { device_id: 'device-0008', device_instance_id: 'old-recovery-host-0008' },
    orchestrator: {
      busy: false,
      recovering: false,
      inspectCodeActivation: async () => ({ safe: true, code: 'COMPONENT_STOPPED', workspace: root }),
      currentMcpHealth: async () => null,
      codingMcpRevisionStatus: () => revisions.status(),
      setActivationEpoch() {},
      stop: async () => true
    },
    canonicalLedgerCensus: async (options) => {
      censusCalls += 1;
      return { ...structuredClone(census), ...(options.holdExclusive ? { release_exclusive_gate: async () => { releaseCalls += 1; return true; } } : {}) };
    },
    spawnRecoveryReplacement: async (options) => { spawnCalls.push(options); },
    now: () => 1_700_000_000_030
  });

  const result = await coordinator.restart({ operationId: id('operation-epoch', '0009') });
  assert.equal(result.state, 'HANDOFF');
  assert.equal(censusCalls, 2);
  assert.equal(releaseCalls, 1);
  assert.equal(spawnCalls.length, 1);
  const active = store.current();
  assert.notEqual(active.activation_epoch_id, previous.activation_epoch_id);
  assert.deepEqual(active.ledger_snapshot, snapshot);
  assert.equal(active.metadata.ledger_census_fingerprint, census.census_fingerprint);
  assert.equal(active.admission_state, 'CLOSED');
});

test('stopped-runtime retry refuses when the independent ledger changes before admission', async (t) => {
  const { root, paths } = fixture(t);
  const store = epochStore(paths);
  const previous = store.create({
    activation_epoch_id: id('activation-epoch', '0009'),
    operation_id: id('operation-epoch', '0009'),
    components: ['recovery_host', 'coding_mcp', 'electron_ui']
  });
  store.fail(previous.activation_epoch_id, { code: 'MCP_START_FAILED', message: 'previous replacement failed' });
  const makeCensus = (sha, fingerprint) => ({
    safe: true,
    code: 'READY',
    workspace: root,
    snapshot: {
      backup_api_copy: true,
      immutable: true,
      query_only: true,
      integrity_check: ['ok'],
      foreign_key_check_rows: 0,
      sha256: sha,
      logical_sha256: '2'.repeat(64)
    },
    lifecycle: { unexplained_active_runs: 0, unbound_live_resource_residues: 0, projection_drift: false, blockers: [] },
    census_fingerprint: fingerprint,
    content_free: true,
    mutated_canonical_ledger: false
  });
  let call = 0;
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: store,
    settings: { load: () => ({ workspace: root }) },
    revisions: { status: () => ({ running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64), update_pending: false }) },
    orchestrator: {
      inspectCodeActivation: async () => ({ safe: true, code: 'COMPONENT_STOPPED', workspace: root }),
      currentMcpHealth: async () => null,
      codingMcpRevisionStatus: () => ({ running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64), update_pending: false }),
      setActivationEpoch() {}
    },
    canonicalLedgerCensus: async () => {
      call += 1;
      return call === 1
        ? makeCensus('1'.repeat(64), '3'.repeat(64))
        : { ...makeCensus('4'.repeat(64), '5'.repeat(64)), release_exclusive_gate: async () => true };
    },
    now: () => 1_700_000_000_031
  });

  await assert.rejects(coordinator.restart({ operationId: id('operation-epoch', '0010') }), { code: 'ORCHESTRATION_STATE_UNCERTAIN' });
  assert.equal(call, 2);
  assert.equal(store.current().activation_epoch_id, previous.activation_epoch_id);
  assert.equal(store.current().state, 'FAILED');
});

test('stopped-runtime retry refuses dangerous unresolved acceptance from the canonical ledger census', async (t) => {
  const { root, paths } = fixture(t);
  const store = epochStore(paths);
  const previous = store.create({
    activation_epoch_id: id('activation-epoch', '0011'),
    operation_id: id('operation-epoch', '0011'),
    components: ['recovery_host', 'coding_mcp', 'electron_ui']
  });
  store.fail(previous.activation_epoch_id, { code: 'MCP_START_FAILED', message: 'previous replacement failed' });
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: store,
    settings: { load: () => ({ workspace: root }) },
    orchestrator: {
      inspectCodeActivation: async () => ({ safe: true, code: 'COMPONENT_STOPPED', workspace: root }),
      currentMcpHealth: async () => null,
      codingMcpRevisionStatus: () => ({ running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64), update_pending: false })
    },
    canonicalLedgerCensus: async () => ({
      safe: false,
      code: 'ACCEPTANCE_PENDING',
      reason: 'acceptance_pending',
      snapshot: { backup_api_copy: true, immutable: true, query_only: true },
      lifecycle: { blockers: ['acceptance_pending'] }
    }),
    now: () => 1_700_000_000_032
  });

  await assert.rejects(coordinator.restart({ operationId: id('operation-epoch', '0012') }), { code: 'ACCEPTANCE_PENDING' });
  assert.equal(store.current().activation_epoch_id, previous.activation_epoch_id);
  assert.equal(store.current().state, 'FAILED');
});

test('final census exceptions are durably terminalized instead of leaving an active epoch', async (t) => {
  const { root, paths } = fixture(t);
  const store = epochStore(paths);
  const created = store.create({
    activation_epoch_id: id('activation-epoch', '0003'),
    operation_id: id('operation-epoch', '0003'),
    components: ['recovery_host', 'coding_mcp', 'electron_ui']
  });
  store.update(created.activation_epoch_id, { state: 'STOPPING', reason: 'test-stop-boundary' });
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: store,
    settings: { load: () => ({ workspace: root }) },
    orchestrator: {},
    now: () => 1_700_000_000_010
  });
  coordinator.finalCensus = async () => {
    throw Object.assign(new Error('census transport failed'), { code: 'CENSUS_TRANSPORT_FAILED' });
  };

  await assert.rejects(coordinator.finalize(created.activation_epoch_id), { code: 'CENSUS_TRANSPORT_FAILED' });
  const terminal = store.current();
  assert.equal(terminal.state, 'FAILED');
  assert.equal(terminal.admission_state, 'CLOSED');
  assert.equal(terminal.error.code, 'CENSUS_TRANSPORT_FAILED');
});

test('replacement without a required Electron UI launcher fails durably and stays closed', async (t) => {
  const { root, paths } = fixture(t);
  const store = epochStore(paths);
  const created = store.create({
    activation_epoch_id: id('activation-epoch', '0004'),
    operation_id: id('operation-epoch', '0004'),
    components: ['recovery_host', 'coding_mcp', 'electron_ui'],
    component_evidence: { recovery_host: { instance_id: 'old-recovery-host-0004' } }
  });
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: store,
    settings: { load: () => ({ workspace: root }) },
    secrets: { get: () => '' },
    orchestrator: {
      setActivationEpoch() {},
      start: async () => {},
      ensureToken: async () => 'x'.repeat(32)
    },
    recoveryPlane: {
      setActivationEpoch() {},
      ensure: async () => ({ state: 'healthy' })
    },
    recoveryInstanceId: 'new-recovery-host-0004',
    getUiRegistration: () => null,
    getUiPresence: () => ({ alive: false }),
    now: () => 1_700_000_000_011
  });

  await assert.rejects(
    coordinator.continueReplacement({
      activationEpochId: created.activation_epoch_id,
      expectedOldInstanceId: 'old-recovery-host-0004'
    }),
    { code: 'UI_REPLACEMENT_UNAVAILABLE' }
  );
  const terminal = store.current();
  assert.equal(terminal.state, 'FAILED');
  assert.equal(terminal.admission_state, 'CLOSED');
  assert.equal(terminal.error.code, 'UI_REPLACEMENT_UNAVAILABLE');
});

test('manual restart delegates to full clean while automatic recovery remains component-scoped', async (t) => {
  const { paths } = fixture(t);
  const calls = [];
  const orchestrator = new RuntimeOrchestrator({
    paths,
    settings: { load: () => ({}) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.setFullCleanActivation({
    restart: async (options) => { calls.push(['full', options]); return { mode: 'full_clean_activation' }; }
  });
  orchestrator.stop = async (options) => { calls.push(['stop', options]); return true; };
  orchestrator.start = async (options) => { calls.push(['start', options]); return { mode: options.mode }; };

  assert.deepEqual(await orchestrator.restart({ reason: 'operator' }), { mode: 'full_clean_activation' });
  assert.equal(calls[0][0], 'full');
  const automatic = await orchestrator.restart({ automatic: true });
  assert.equal(automatic.mode, 'soft_recovery');
  assert.deepEqual(calls.slice(1).map(([name]) => name), ['stop', 'start']);
});

test('ordinary runtime start is refused while a durable activation epoch is incomplete', async (t) => {
  const { paths } = fixture(t);
  const store = epochStore(paths);
  const created = store.create({
    activation_epoch_id: id('activation-epoch', '0005'),
    operation_id: id('operation-epoch', '0005')
  });
  const orchestrator = new RuntimeOrchestrator({
    paths,
    settings: { load: () => ({}) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });

  await assert.rejects(orchestrator.start(), { code: 'UPDATE_INCOMPLETE' });
  assert.equal(store.current().activation_epoch_id, created.activation_epoch_id);
  assert.equal(store.current().admission_state, 'CLOSED');
});
