const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { RecoveryActionStore } = require('../electron/services/recoveryActionStore');
const { RecoveryActivation, normalizeActivationRequest } = require('../electron/services/recoveryActivation');

const OLD = 'a'.repeat(64);
const NEXT = 'b'.repeat(64);

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-activation-'));
  const paths = createRuntimePaths({
    dataRoot: path.join(root, 'data'),
    resourcesRoot: path.join(root, 'resources'),
    appRoot: path.join(root, 'app')
  });
  fs.mkdirSync(paths.dataRoot(), { recursive: true });
  fs.mkdirSync(paths.resourcesRoot(), { recursive: true });
  fs.mkdirSync(paths.appRoot(), { recursive: true });
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return paths;
}

function request(component, now = Date.now(), operationId = 'operation-00000001') {
  return {
    operation_id: operationId,
    component,
    requested_at_unix_ms: now,
    expires_at_unix_ms: now + 60_000,
    expected_disk_revision: NEXT,
    allow_acceptance_pending: false
  };
}

function revisions(running = OLD) {
  return {
    status: (_component, supplied) => ({
      running_revision: supplied || running || null,
      disk_revision: NEXT,
      update_pending: Boolean((supplied || running) && (supplied || running) !== NEXT),
      state: (supplied || running) === NEXT ? 'current' : 'update_pending'
    })
  };
}

function orchestrator(overrides = {}) {
  return {
    codingMcpRevisionStatus: () => ({ running_revision: OLD, disk_revision: NEXT, update_pending: true, state: 'update_pending' }),
    inspectCodeActivation: async () => ({ safe: true, code: 'READY', workspace: 'C:\work' }),
    prepareCodeActivation: async () => ({ safe: true, code: 'READY', fenced: true }),
    cancelCodeActivation: async () => true,
    activateCodingMcpUpdate: async () => ({ old_instance_id: 'old-mcp', new_instance_id: 'new-mcp', old_revision: OLD, new_revision: NEXT, health_verified: true, tunnel_preserved: true }),
    ...overrides
  };
}

test('activation requests are strict, bounded, and expire', () => {
  const now = Date.now();
  assert.equal(normalizeActivationRequest(request('coding_mcp', now), now).component, 'coding_mcp');
  assert.throws(() => normalizeActivationRequest({ ...request('coding_mcp', now), executable: 'cmd.exe' }, now), { code: 'INVALID_ARGUMENT' });
  assert.throws(() => normalizeActivationRequest(request('all', now), now), { code: 'INVALID_COMPONENT' });
  assert.throws(() => normalizeActivationRequest({ ...request('coding_mcp', now), expires_at_unix_ms: now - 1 }, now), { code: 'ACTIVATION_REQUEST_EXPIRED' });
});

test('durable action store replays the same operation and rejects payload conflicts', (t) => {
  const paths = fixture(t);
  let now = Date.now();
  const store = new RecoveryActionStore({ paths, now: () => now });
  const firstRequest = request('coding_mcp', now);
  assert.equal(store.begin(firstRequest).created, true);
  assert.equal(store.begin(firstRequest).created, false);
  assert.throws(() => store.begin({ ...firstRequest, component: 'electron_ui' }), { code: 'IDEMPOTENCY_CONFLICT' });
  const completed = store.finish(firstRequest.operation_id, 'completed', { activated: true });
  assert.equal(completed.state, 'completed');
  assert.equal(new RecoveryActionStore({ paths, now: () => now }).get(firstRequest.operation_id).result.activated, true);
  now += 60_001;
  const completedReplay = store.begin(firstRequest);
  assert.equal(completedReplay.created, false);
  assert.equal(completedReplay.record.state, 'completed');

  const expiring = request('coding_mcp', now, 'operation-00000002');
  store.begin(expiring);
  now += 60_001;
  assert.equal(store.begin(expiring).record.error.code, 'ACTIVATION_REQUEST_EXPIRED');
});

test('completed activation replays its durable result after request expiry', async (t) => {
  const paths = fixture(t);
  let now = Date.now();
  let activations = 0;
  const manager = new RecoveryActivation({
    paths,
    revisions: revisions(),
    orchestrator: orchestrator({
      activateCodingMcpUpdate: async () => {
        activations += 1;
        return { old_instance_id: 'old', new_instance_id: 'new', old_revision: OLD, new_revision: NEXT, health_verified: true, tunnel_preserved: true };
      }
    }),
    log: {},
    recoveryInstanceId: 'recovery-instance-0001',
    recoveryRunningRevision: OLD,
    now: () => now
  });
  const activation = request('coding_mcp', now, 'operation-durable-0001');
  assert.equal((await manager.activate(activation)).state, 'completed');
  now += 60_001;
  const replay = await manager.activate(activation);
  assert.equal(replay.state, 'completed');
  assert.equal(replay.deduplicated, true);
  assert.equal(activations, 1);
});

test('Coding MCP activation is fenced, component-scoped, verified, and idempotent', async (t) => {
  const paths = fixture(t);
  const calls = { prepare: 0, activate: 0 };
  let activationOptions = null;
  const manager = new RecoveryActivation({
    paths,
    revisions: revisions(),
    orchestrator: orchestrator({
      prepareCodeActivation: async () => { calls.prepare += 1; return { safe: true, code: 'READY', fenced: true }; },
      activateCodingMcpUpdate: async (_revision, options) => {
        calls.activate += 1;
        activationOptions = options;
        return { old_instance_id: 'old', new_instance_id: 'new', old_revision: OLD, new_revision: NEXT, health_verified: true, tunnel_preserved: true };
      }
    }),
    log: {},
    recoveryInstanceId: 'recovery-instance-0001',
    recoveryRunningRevision: OLD
  });
  const activation = request('coding_mcp');
  const first = await manager.activate(activation);
  const replay = await manager.activate(activation);
  assert.equal(first.state, 'completed');
  assert.equal(first.result.new_revision, NEXT);
  assert.equal(first.result.tunnel_preserved, true);
  assert.equal(replay.deduplicated, true);
  assert.equal(activationOptions.expiresAtUnixMs, activation.expires_at_unix_ms);
  assert.deepEqual(calls, { prepare: 1, activate: 1 });
});

test('Electron UI activation propagates its deadline to the launch boundary', async (t) => {
  const paths = fixture(t);
  let launchOptions = null;
  const manager = new RecoveryActivation({
    paths,
    revisions: revisions(),
    orchestrator: orchestrator(),
    log: {},
    recoveryInstanceId: 'recovery-instance-0001',
    recoveryRunningRevision: OLD,
    spawnElectronUi: async (options) => { launchOptions = options; }
  });
  const activation = request('electron_ui');
  const result = await manager.activate(activation);
  assert.equal(result.state, 'accepted');
  assert.equal(launchOptions.expiresAtUnixMs, activation.expires_at_unix_ms);
});

test('canonical runtime refusal is persisted without restarting Coding MCP', async (t) => {
  const paths = fixture(t);
  let activated = false;
  const manager = new RecoveryActivation({
    paths,
    revisions: revisions(),
    orchestrator: orchestrator({
      prepareCodeActivation: async () => { throw Object.assign(new Error('busy'), { code: 'RUNTIME_BUSY' }); },
      activateCodingMcpUpdate: async () => { activated = true; }
    }),
    log: {},
    recoveryInstanceId: 'recovery-instance-0001',
    recoveryRunningRevision: OLD
  });
  const result = await manager.activate(request('coding_mcp'));
  assert.equal(result.state, 'refused');
  assert.equal(result.error.code, 'RUNTIME_BUSY');
  assert.equal(activated, false);
});

test('Coding MCP activation failure releases the admission fence before persisting failure', async (t) => {
  const paths = fixture(t);
  const events = [];
  const manager = new RecoveryActivation({
    paths,
    revisions: revisions(),
    orchestrator: orchestrator({
      prepareCodeActivation: async () => { events.push('prepare'); return { safe: true, code: 'READY', fenced: true }; },
      activateCodingMcpUpdate: async () => {
        events.push('activate');
        throw Object.assign(new Error('restart failed'), { code: 'ACTIVATION_HEALTH_FAILED' });
      },
      cancelCodeActivation: async () => { events.push('cancel'); return true; }
    }),
    log: {},
    recoveryInstanceId: 'recovery-instance-0001',
    recoveryRunningRevision: OLD
  });

  const result = await manager.activate(request('coding_mcp'));

  assert.equal(result.state, 'failed');
  assert.equal(result.error.code, 'ACTIVATION_HEALTH_FAILED');
  assert.deepEqual(events, ['prepare', 'activate', 'cancel']);
});

test('Electron UI registration completes only after the expected revision is running', async (t) => {
  const paths = fixture(t);
  const manager = new RecoveryActivation({
    paths,
    revisions: revisions(),
    orchestrator: orchestrator(),
    log: {},
    recoveryInstanceId: 'recovery-instance-0001',
    recoveryRunningRevision: OLD
  });
  const activation = request('electron_ui');
  assert.equal((await manager.activate(activation)).state, 'accepted');
  const oldRegistration = manager.registerUi({
    instance_id: 'electron-ui-old-0001', pid: process.pid, revision: OLD, started_at_unix_ms: Date.now()
  });
  assert.equal(oldRegistration.restart_required, true);
  assert.equal(oldRegistration.expires_at_unix_ms, activation.expires_at_unix_ms);
  const newRegistration = manager.registerUi({
    instance_id: 'electron-ui-new-0001', pid: process.pid, revision: NEXT, started_at_unix_ms: Date.now()
  });
  assert.equal(newRegistration.restart_required, false);
  assert.equal(newRegistration.activation.state, 'completed');
  assert.equal(manager.status(activation.operation_id).result.health_verified, true);
});

test('Recovery Host activation prepares MCP continuity before scheduling a fixed handoff', async (t) => {
  const paths = fixture(t);
  const events = [];
  let replacementOptions = null;
  const manager = new RecoveryActivation({
    paths,
    revisions: revisions(),
    orchestrator: orchestrator({ prepareCodeActivation: async () => { events.push('preflight'); return { safe: true }; } }),
    log: {},
    recoveryInstanceId: 'recovery-instance-0001',
    recoveryRunningRevision: OLD,
    spawnRecoveryReplacement: async (options) => {
      replacementOptions = options;
      events.push(`spawn:${options.expectedOldInstanceId}`);
    },
    beginRecoveryHandoff: () => { events.push('handoff'); }
  });
  const activation = request('recovery_host');
  const result = await manager.activate(activation);
  assert.equal(result.state, 'accepted');
  assert.deepEqual(events, ['preflight', 'spawn:recovery-instance-0001', 'handoff']);
  assert.equal(replacementOptions.expiresAtUnixMs, activation.expires_at_unix_ms);
});

test('expiry after a process mutation is persisted as failed rather than refused', async (t) => {
  const paths = fixture(t);
  const manager = new RecoveryActivation({
    paths,
    revisions: revisions(),
    orchestrator: orchestrator({
      activateCodingMcpUpdate: async () => {
        throw Object.assign(new Error('deadline after stop'), {
          code: 'ACTIVATION_REQUEST_EXPIRED',
          details: { process_mutated: true, boundary: 'before_native_start' }
        });
      }
    }),
    log: {},
    recoveryInstanceId: 'recovery-instance-0001',
    recoveryRunningRevision: OLD
  });
  const result = await manager.activate(request('coding_mcp'));
  assert.equal(result.state, 'failed');
  assert.equal(result.error.code, 'ACTIVATION_REQUEST_EXPIRED');
});

test('request expiring during preflight cannot mutate a stopped component', async (t) => {
  const paths = fixture(t);
  let now = Date.now();
  let spawned = false;
  const activation = request('recovery_host', now, 'operation-expiring-0001');
  activation.expires_at_unix_ms = now + 1;
  const manager = new RecoveryActivation({
    paths,
    revisions: revisions(),
    orchestrator: orchestrator({
      inspectCodeActivation: async () => {
        now += 2;
        return { safe: true, code: 'COMPONENT_STOPPED' };
      }
    }),
    log: {},
    recoveryInstanceId: 'recovery-instance-0001',
    recoveryRunningRevision: OLD,
    spawnRecoveryReplacement: async () => { spawned = true; },
    beginRecoveryHandoff: () => {},
    now: () => now
  });

  const result = await manager.activate(activation);

  assert.equal(result.state, 'refused');
  assert.equal(result.error.code, 'ACTIVATION_REQUEST_EXPIRED');
  assert.equal(spawned, false);
});
