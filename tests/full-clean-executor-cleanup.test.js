const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { FullCleanActivation } = require('../electron/services/fullCleanActivation');

function fixture(t, prepare) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-cleanup-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  let now = 1_700_000_000_000;
  const operation = 'operation_cleanup_0001';
  const identity = {
    operation_id: operation, workspace: root,
    process_instance_id: '-native_process_0001', server_instance_id: '_native_server_0001',
    fenced: true, fence_operation_id: operation
  };
  const cleanup = { state: 'pending', started_at_unix_ms: now, deadline_at_unix_ms: now + 430_000, retry_after_ms: 1000 };
  const pending = () => ({ ...identity, safe: false, code: 'SANDBOX_CLEANUP_PENDING', executor_cleanup: { ...cleanup } });
  const completed = () => ({ ...identity, safe: true, code: 'READY', executor_cleanup: { ...cleanup, state: 'completed', confirmed: true } });
  const calls = [];
  const stops = [];
  const coordinator = new FullCleanActivation({
    paths: createRuntimePaths({ dataRoot: path.join(root, 'profile'), appRoot: root, resourcesRoot: root }),
    settings: { load: () => ({ workspace: root }) },
    orchestrator: {
      inspectCodeActivation: async () => ({ safe: true, code: 'READY', workspace: root, executor_cleanup_supported: true }),
      prepareCodeActivation: async (options) => { calls.push(options); return prepare({ calls, pending, completed, now: () => now }); },
      stop: async () => { stops.push('native'); }, currentMcpHealth: async () => null
    },
    getUiPresence: () => ({ alive: true }), terminateUi: async () => { stops.push('ui'); },
    recoveryPlane: { stop: async () => { stops.push('recovery'); } },
    spawnRecoveryReplacement: async () => { stops.push('replacement'); },
    now: () => now, waitFn: async (delay) => { now += delay; }
  });
  return { root, operation, calls, stops, coordinator, pending, completed, now: () => now };
}

test('full-clean observes one cleanup across short fence renewals without extending its deadline', async (t) => {
  const f = fixture(t, ({ calls, pending, completed }) => {
    if (calls.length > 61) return completed();
    const result = pending();
    throw Object.assign(new Error('pending'), { code: result.code, details: result });
  });
  const durable = f.now() + 600_000;
  const result = await f.coordinator._prepareFence(f.operation, durable, null, true);
  assert.equal(result.executor_cleanup.confirmed, true);
  assert.equal(f.calls.length, 62);
  assert.equal(new Set(f.calls.map(row => row.operationId)).size, 1);
  assert.equal(f.calls[0].expiresAtUnixMs, 1_700_000_055_000);
  assert.equal(f.calls[61].expiresAtUnixMs, f.now() + 55_000);
  assert.equal(result.executor_cleanup.deadline_at_unix_ms, 1_700_000_430_000);
  assert.deepEqual(f.stops, []);
});

test('full-clean rejects changed cleanup operation, process or deadline before stopping', async (t) => {
  for (const change of ['operation', 'process', 'deadline']) {
    await t.test(change, async (t) => {
      const f = fixture(t, ({ calls, pending }) => {
        const result = pending();
        if (calls.length > 1) {
          if (change === 'operation') result.operation_id = 'operation_cleanup_other';
          if (change === 'process') result.process_instance_id = 'native_process_other';
          if (change === 'deadline') result.executor_cleanup.deadline_at_unix_ms -= 1;
        }
        return result;
      });
      await assert.rejects(f.coordinator.restart({ operationId: f.operation, refresh: true }), {
        code: 'SANDBOX_CLEANUP_OBSERVATION_INVALID', executorCleanupUnconfirmed: true
      });
      assert.deepEqual(f.stops, []);
      assert.equal(f.coordinator.current().state, 'FAILED');
      assert.equal(f.coordinator.current().admission_state, 'CLOSED');
    });
  }
});

test('failed cleanup and response loss preserve the native owner and terminalize the activation', async (t) => {
  for (const code of ['SANDBOX_TEARDOWN_UNCONFIRMED', 'ORCHESTRATION_STATE_UNCERTAIN']) {
    await t.test(code, async (t) => {
      const f = fixture(t, () => { throw Object.assign(new Error('cleanup could not be confirmed'), { code }); });
      await assert.rejects(f.coordinator.restart({ operationId: f.operation, refresh: true }), { code });
      assert.deepEqual(f.stops, []);
      assert.equal(f.coordinator.current().state, 'FAILED');
    });
  }
});

test('cleanup observation stops at the original fixed deadline', async (t) => {
  const f = fixture(t, ({ pending }) => pending());
  await assert.rejects(f.coordinator._prepareFence(f.operation, f.now() + 600_000, null, false), {
    code: 'SANDBOX_CLEANUP_TIMEOUT', executorCleanupUnconfirmed: true
  });
  assert.equal(f.now(), 1_700_000_430_000);
  assert.deepEqual(f.stops, []);
});

test('native completion must confirm the same cleanup owner', async (t) => {
  const f = fixture(t, ({ calls, pending, completed }) => {
    if (calls.length === 1) return pending();
    const result = completed();
    result.server_instance_id = 'native_server_other';
    return result;
  });
  await assert.rejects(f.coordinator._prepareFence(f.operation, f.now() + 600_000, null, false), {
    code: 'SANDBOX_CLEANUP_OBSERVATION_INVALID'
  });
});

test('a legacy live native is rejected before an epoch or process mutation', async (t) => {
  const f = fixture(t, () => { throw new Error('prepare must not run'); });
  f.coordinator.orchestrator.inspectCodeActivation = async () => ({ safe: true, code: 'READY', workspace: f.root });
  await assert.rejects(f.coordinator.restart({ operationId: f.operation, refresh: true }), { code: 'SANDBOX_CLEANUP_UNSUPPORTED' });
  assert.equal(f.coordinator.current(), null);
  assert.deepEqual(f.calls, []);
  assert.deepEqual(f.stops, []);
});

test('a prepared fence without executor cleanup confirmation cannot authorize stop', async (t) => {
  const f = fixture(t, () => null);
  assert.throws(() => f.coordinator._requireExactPreparedFence({
    safe: true, fenced: true, fence_operation_id: f.operation
  }, f.operation, 'before stopping'), { code: 'SANDBOX_TEARDOWN_UNCONFIRMED' });
});
