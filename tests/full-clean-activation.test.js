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
