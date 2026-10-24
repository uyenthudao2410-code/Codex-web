const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { RecoveryHost } = require('../electron/services/recoveryHost');
const {
  buildBootstrapEnvelope,
  readBootstrapEnvelope,
  writeBootstrapEnvelope,
  writeBootstrapResult,
  readBootstrapResult,
  removeBootstrapEnvelope,
  proveIdlePackagedHandoff,
  bootstrapCurrentRecoveryHost
} = require('../electron/services/recoveryBootstrap');
const { trustedAttestation } = require('../electron/services/trustedRecoveryBootstrap');

const OPERATION_ONE = 'bootstrap-operation-000001';
const OPERATION_TWO = 'bootstrap-operation-000002';
const REVISION = 'a'.repeat(64);
const OLD_PROCESS_START_TOKEN = '133801234567890123';
const CURRENT_PROCESS_START_TOKEN = '133801234567890999';
const SOURCE_CHECKPOINT = Object.freeze({
  checkpoint_id: 'checkpoint-bootstrap-0001',
  run_id: 'run-bootstrap-0001',
  wave_id: 'wave-bootstrap-0001',
  proof_fingerprint: 'b'.repeat(64),
  git_head: 'c'.repeat(40)
});

function trustedSourceAttestation() {
  return trustedAttestation({
    eligible: true,
    code: 'ACTIVATABLE',
    source_checkpoint_id: SOURCE_CHECKPOINT.checkpoint_id,
    run_id: SOURCE_CHECKPOINT.run_id,
    wave_id: SOURCE_CHECKPOINT.wave_id,
    proof_fingerprint: SOURCE_CHECKPOINT.proof_fingerprint,
    accepted_head: SOURCE_CHECKPOINT.git_head,
    affected_components: ['recovery_host'],
    receipts: [{
      path: 'electron/services/recoveryActionStore.js',
      state: 'file',
      sha256: 'd'.repeat(64),
      size_bytes: 1,
      receipt_kind: 'durable_wave_patch_surface',
      run_id: SOURCE_CHECKPOINT.run_id,
      wave_id: SOURCE_CHECKPOINT.wave_id,
      restart_safe: true,
      content_addressed: true
    }]
  });
}

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-recovery-bootstrap-'));
  const dataRoot = path.join(root, 'data');
  const resourcesRoot = path.join(root, 'resources');
  const appRoot = path.join(root, 'app');
  fs.mkdirSync(dataRoot, { recursive: true });
  fs.mkdirSync(resourcesRoot, { recursive: true });
  fs.mkdirSync(appRoot, { recursive: true });
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return createRuntimePaths({
    dataRoot,
    resourcesRoot,
    appRoot,
    executablePath: process.execPath
  });
}

function descriptor(paths, overrides = {}) {
  const identity = paths.runtimeIdentity();
  return {
    version: 1,
    host: '127.0.0.1',
    port: 32123,
    owner: 'recovery-host',
    owner_pid: process.pid,
    owner_process_start_token: OLD_PROCESS_START_TOKEN,
    instance_id: 'stale-recovery-host-0001',
    token: 't'.repeat(48),
    installation_id: identity.installation_id,
    runtime_mode: identity.mode,
    ...overrides
  };
}

function envelope(paths, operationId = OPERATION_ONE, overrides = {}) {
  const requestedAt = Date.now();
  const { descriptor: descriptorOverrides = {}, ...requestOverrides } = overrides;
  return buildBootstrapEnvelope({
    paths,
    descriptor: descriptor(paths, descriptorOverrides),
    operationId,
    sourceCheckpoint: SOURCE_CHECKPOINT,
    expectedDiskRevision: REVISION,
    requestedAtUnixMs: requestedAt,
    expiresAtUnixMs: requestedAt + 90_000,
    ...requestOverrides
  });
}

function logStub() {
  return { info() {}, warn() {}, error() {}, read: () => [], clear() {} };
}

test('refresh bootstrap is checkpoint-free but keeps durable acceptance preservation explicit', (t) => {
  const paths = fixture(t);
  const requestedAt = Date.now();
  const refresh = buildBootstrapEnvelope({
    paths,
    descriptor: descriptor(paths),
    operationId: OPERATION_ONE,
    sourceCheckpoint: null,
    expectedDiskRevision: REVISION,
    refresh: true,
    requestedAtUnixMs: requestedAt,
    expiresAtUnixMs: requestedAt + 90_000
  });
  writeBootstrapEnvelope(paths, refresh);
  const loaded = readBootstrapEnvelope(paths, { bootstrapId: OPERATION_ONE });
  assert.equal(loaded.refresh, true);
  assert.equal(loaded.source_checkpoint, null);
  assert.equal(loaded.allow_acceptance_pending, true);
  assert.throws(() => buildBootstrapEnvelope({
    paths,
    descriptor: descriptor(paths),
    operationId: OPERATION_TWO,
    sourceCheckpoint: SOURCE_CHECKPOINT,
    expectedDiskRevision: REVISION,
    refresh: true,
    requestedAtUnixMs: requestedAt,
    expiresAtUnixMs: requestedAt + 90_000
  }), { code: 'RECOVERY_BOOTSTRAP_INVALID' });
});

test('bootstrap artifacts are operation-scoped and exact-envelope removal cannot delete another operation', (t) => {
  const paths = fixture(t);
  const first = envelope(paths, OPERATION_ONE);
  const second = envelope(paths, OPERATION_TWO);
  const firstPath = writeBootstrapEnvelope(paths, first);
  const secondPath = writeBootstrapEnvelope(paths, second);

  assert.notEqual(firstPath, secondPath);
  assert.equal(readBootstrapEnvelope(paths, { bootstrapId: OPERATION_ONE }).operation_id, OPERATION_ONE);
  assert.equal(readBootstrapEnvelope(paths, { bootstrapId: OPERATION_TWO }).operation_id, OPERATION_TWO);
  assert.throws(() => removeBootstrapEnvelope(paths, OPERATION_ONE, second.integrity_sha256), {
    code: 'RECOVERY_BOOTSTRAP_INTEGRITY_FAILED'
  });
  assert.equal(removeBootstrapEnvelope(paths, OPERATION_ONE, first.integrity_sha256), true);
  assert.equal(fs.existsSync(firstPath), false);
  assert.equal(fs.existsSync(secondPath), true);
});

test('bootstrap failure receipt retains only bounded termination diagnostics', (t) => {
  const paths = fixture(t);
  writeBootstrapResult(paths, {
    operation_id: OPERATION_ONE,
    state: 'failed',
    error: {
      code: 'RECOVERY_BOOTSTRAP_TERMINATION_FAILED',
      message: 'Exact termination failed',
      details: {
        cause_code: 'PROCESS_TERMINATION_FAILED',
        termination_cause_code: 'PROCESS_TERMINATION_TIMEOUT',
        pid: 42424, exit_code: 128,
        stdout: 'must not persist process output', token: 'must not persist secrets'
      }
    }
  });
  assert.deepEqual(readBootstrapResult(paths, OPERATION_ONE).error.details, {
    cause_code: 'PROCESS_TERMINATION_FAILED',
    termination_cause_code: 'PROCESS_TERMINATION_TIMEOUT',
    pid: 42424, exit_code: 128
  });
});

test('bootstrap results move monotonically and terminal receipts are immutable per operation', (t) => {
  const paths = fixture(t);
  writeBootstrapResult(paths, { operation_id: OPERATION_ONE, state: 'pending', completed_at_unix_ms: 1000 });
  writeBootstrapResult(paths, { operation_id: OPERATION_ONE, state: 'started', completed_at_unix_ms: 1001 });
  writeBootstrapResult(paths, {
    operation_id: OPERATION_ONE,
    state: 'completed',
    completed_at_unix_ms: 1002,
    result: { activation_epoch_id: 'epoch-bootstrap-0001', fully_ready: true }
  });

  assert.equal(readBootstrapResult(paths, OPERATION_ONE).state, 'completed');
  assert.throws(() => writeBootstrapResult(paths, {
    operation_id: OPERATION_ONE,
    state: 'failed',
    completed_at_unix_ms: 1003
  }), { code: 'RECOVERY_BOOTSTRAP_RESULT_TERMINAL' });
  assert.equal(readBootstrapResult(paths, OPERATION_ONE).state, 'completed');

  writeBootstrapResult(paths, { operation_id: OPERATION_TWO, state: 'pending', completed_at_unix_ms: 1000 });
  assert.equal(readBootstrapResult(paths, OPERATION_TWO).state, 'pending');
});

test('a crashed result lock fail-closes only its exact operation and is never reclaimed by unlink', (t) => {
  const paths = fixture(t);
  const staleLock = `${paths.recoveryHostBootstrapResultFile(OPERATION_ONE)}.lock`;
  fs.writeFileSync(staleLock, JSON.stringify({
    version: 1,
    operation_id: OPERATION_ONE,
    pid: 99999999,
    token: 'stale-lock-token',
    created_at_unix_ms: 1
  }), 'utf8');

  assert.throws(() => writeBootstrapResult(paths, {
    operation_id: OPERATION_ONE,
    state: 'pending'
  }, { timeoutMs: 30 }), { code: 'RECOVERY_BOOTSTRAP_RESULT_BUSY' });
  assert.equal(fs.existsSync(staleLock), true);

  writeBootstrapResult(paths, { operation_id: OPERATION_TWO, state: 'pending' });
  assert.equal(readBootstrapResult(paths, OPERATION_TWO).state, 'pending');
  assert.equal(fs.existsSync(`${paths.recoveryHostBootstrapResultFile(OPERATION_TWO)}.lock`), false);
});

function rollbackSnapshot(paths, running, overrides = {}) {
  return {
    settings: { workspace: paths.appRoot(), executionRole: 'direct_legacy' },
    device: { coding: { native_alive: running } },
    status: {
      runtimeRunning: running, tunnelRunning: running, busy: false, recovering: false,
      manuallyStopped: false, activationEpoch: { activation_epoch_id: 'epoch-before-stop' },
      ...overrides
    }
  };
}

test('bootstrap semantic stop refusal never terminates, spawns or restores', async (t) => {
  for (const code of ['RECOVERY_REQUEST_FAILED', 'RUNTIME_BUSY', 'AUTHORITY_DENIED', 'ECONNRESET']) {
    await t.test(code, async (t) => {
      const paths = fixture(t);
      const target = descriptor(paths);
      fs.writeFileSync(paths.recoveryHostDescriptorFile(), JSON.stringify(target));
      let effects = 0;
      const refusal = Object.assign(new Error('refused'), { code, recoveryResponseReceived: true });
      await assert.rejects(bootstrapCurrentRecoveryHost({
        app: { isPackaged: true, getAppPath: () => paths.appRoot() }, paths,
        descriptor: target, status: { full_clean_activation: { available: false } },
        client: {
          call: async () => rollbackSnapshot(paths, true),
          stop: async () => { throw refusal; }, start: async () => { effects++; }
        },
        operationId: OPERATION_ONE, sourceCheckpoint: SOURCE_CHECKPOINT, expectedDiskRevision: REVISION,
        processIdentityObserver: async (pid) => ({ state: 'live', pid, process_start_token: OLD_PROCESS_START_TOKEN }),
        terminateProcess: async () => { effects++; throw new Error('unsafe termination'); },
        spawnProcess: () => { effects++; throw new Error('unsafe spawn'); }
      }), (error) => error === refusal);
      assert.equal(effects, 0);
      assert.equal(readBootstrapResult(paths, OPERATION_ONE).error.code, code);
    });
  }
});

test('bootstrap failed handoff preserves off, unknown, partial and manual-stop state', async (t) => {
  for (const mode of ['off', 'unknown', 'partial', 'manual-stop', 'epoch-changed', 'recovering', 'recovery-unknown']) {
    await t.test(mode, async (t) => {
      const paths = fixture(t);
      const target = descriptor(paths);
      fs.writeFileSync(paths.recoveryHostDescriptorFile(), JSON.stringify(target));
      let starts = 0;
      let stopped = false;
      await assert.rejects(bootstrapCurrentRecoveryHost({
        app: { isPackaged: true, getAppPath: () => paths.appRoot() }, paths,
        descriptor: target, status: { full_clean_activation: { available: false } },
        client: {
          call: async () => mode === 'unknown' ? {} : rollbackSnapshot(paths,
            !stopped && mode !== 'off', {
              ...(mode === 'partial' ? { tunnelRunning: false } : {}),
              ...(stopped && mode === 'manual-stop' ? { manuallyStopped: true } : {}),
              ...(stopped && mode === 'recovering' ? { recovering: true } : {}),
              ...(stopped && mode === 'recovery-unknown' ? { recovering: undefined } : {}),
              ...(stopped && mode === 'epoch-changed' ? { activationEpoch: { activation_epoch_id: 'other-epoch' } } : {})
            }),
          stop: async () => { stopped = true; }, start: async () => { starts++; }
        },
        operationId: OPERATION_ONE, sourceCheckpoint: SOURCE_CHECKPOINT, expectedDiskRevision: REVISION,
        processIdentityObserver: async (pid) => ({ state: 'live', pid, process_start_token: OLD_PROCESS_START_TOKEN }),
        terminateProcess: async () => { throw Object.assign(new Error('probe unavailable'), { code: 'PROCESS_IDENTITY_UNVERIFIED' }); }
      }), { code: 'RECOVERY_BOOTSTRAP_PROCESS_IDENTITY_UNVERIFIED' });
      assert.equal(starts, 0);
    });
  }
});

test('stale-host bootstrap reconciles a lost stop response through exact descriptor and PID proof', async (t) => {
  const paths = fixture(t);
  const staleDescriptor = descriptor(paths);
  fs.writeFileSync(paths.recoveryHostDescriptorFile(), JSON.stringify(staleDescriptor), 'utf8');
  let alive = true;
  let terminateCalls = 0;
  const launches = [];
  const spawnProcess = (command, args, options) => {
    const child = {
      pid: 45001,
      once(event, listener) { if (event === 'spawn') queueMicrotask(listener); return this; },
      unref() {}
    };
    launches.push({ command, args, options });
    return child;
  };

  const result = await bootstrapCurrentRecoveryHost({
    app: { isPackaged: true, getAppPath: () => paths.appRoot() },
    paths,
    client: {
      call: async () => rollbackSnapshot(paths, false),
      stop: async () => { throw Object.assign(new Error('response lost'), { code: 'ECONNRESET' }); }
    },
    descriptor: staleDescriptor,
    status: { full_clean_activation: { available: false } },
    operationId: OPERATION_ONE,
    sourceCheckpoint: SOURCE_CHECKPOINT,
    expectedDiskRevision: REVISION,
    spawnProcess,
    processIdentityObserver: async (pid) => alive
      ? { state: 'live', pid, process_start_token: OLD_PROCESS_START_TOKEN }
      : { state: 'absent', pid, process_start_token: null },
    terminateProcess: (identity) => {
      assert.deepEqual(identity, {
        pid: staleDescriptor.owner_pid,
        process_start_token: OLD_PROCESS_START_TOKEN
      });
      terminateCalls += 1;
      alive = false;
    },
    sleep: async () => {}
  });

  assert.equal(result.required, true);
  assert.equal(terminateCalls, 1);
  assert.equal(launches.length, 1);
  assert.deepEqual(launches[0].args, ['--recovery-host', `--recovery-bootstrap=${OPERATION_ONE}`]);
  assert.equal(readBootstrapResult(paths, OPERATION_ONE).state, 'started');
  assert.equal(readBootstrapEnvelope(paths, { bootstrapId: OPERATION_ONE }).old_host_instance_id, staleDescriptor.instance_id);
});

test('bootstrap transport loss cannot terminate an unconfirmed runtime', async (t) => {
  for (const state of ['running', 'unknown', 'native-alive']) {
    await t.test(state, async (t) => {
      const paths = fixture(t);
      const target = descriptor(paths);
      fs.writeFileSync(paths.recoveryHostDescriptorFile(), JSON.stringify(target));
      let effects = 0;
      await assert.rejects(bootstrapCurrentRecoveryHost({
        app: { isPackaged: true, getAppPath: () => paths.appRoot() }, paths,
        descriptor: target, status: { full_clean_activation: { available: false } },
        client: {
          call: async () => {
            if (state === 'unknown') return {};
            const snapshot = rollbackSnapshot(paths, state === 'running');
            if (state === 'native-alive') snapshot.device.coding.native_alive = true;
            return snapshot;
          },
          stop: async () => { throw Object.assign(new Error('lost response'), { code: 'ECONNRESET' }); },
          start: async () => { effects++; }
        },
        operationId: OPERATION_ONE, sourceCheckpoint: SOURCE_CHECKPOINT, expectedDiskRevision: REVISION,
        processIdentityObserver: async (pid) => ({ state: 'live', pid, process_start_token: OLD_PROCESS_START_TOKEN }),
        terminateProcess: async () => { effects++; throw new Error('unsafe terminate'); },
        spawnProcess: () => { effects++; throw new Error('unsafe spawn'); }
      }), { code: 'RECOVERY_BOOTSTRAP_STOP_UNCONFIRMED' });
      assert.equal(effects, 0);
    });
  }
});

test('explicit refresh may hand off an exact idle packaged host to development', async (t) => {
  const paths = fixture(t);
  const staleDescriptor = descriptor(paths, {
    installation_id: 'f'.repeat(64),
    runtime_mode: 'packaged'
  });
  fs.writeFileSync(paths.recoveryHostDescriptorFile(), JSON.stringify(staleDescriptor), 'utf8');
  let alive = true;
  let stopCalls = 0;
  const client = {
    status: async () => ({
      pid: staleDescriptor.owner_pid,
      instance_id: staleDescriptor.instance_id,
      process_start_token: OLD_PROCESS_START_TOKEN,
      electron_ui_recovery: { alive: false, state: 'missing' }
    }),
    call: async (action) => {
      assert.equal(action, 'runtime.lightweight_snapshot');
      return {
        telemetryAvailable: true,
        signalStale: false,
        snapshotBusy: false,
        recovering: false,
        mcpRunning: false,
        nativeAlive: false,
        tunnelRunning: false,
        activationEpoch: { state: 'READY', admission_open: true },
        device: { workspace: paths.appRoot() }
      };
    },
    stop: async () => { stopCalls += 1; }
  };
  const result = await bootstrapCurrentRecoveryHost({
    app: { isPackaged: false, getAppPath: () => paths.appRoot() },
    paths,
    client,
    descriptor: staleDescriptor,
    status: { full_clean_activation: { available: false } },
    operationId: OPERATION_ONE,
    sourceCheckpoint: null,
    expectedDiskRevision: REVISION,
    refresh: true,
    forceRefresh: true,
    allowIdlePackagedHandoff: true,
    spawnProcess: () => ({ pid: 45003, once(event, listener) { if (event === 'spawn') queueMicrotask(listener); return this; }, unref() {} }),
    processIdentityObserver: async (pid) => alive
      ? { state: 'live', pid, process_start_token: OLD_PROCESS_START_TOKEN }
      : { state: 'absent', pid, process_start_token: null },
    terminateProcess: async () => { alive = false; },
    sleep: async () => {}
  });
  assert.equal(stopCalls, 1);
  assert.equal(result.idle_packaged_handoff.exact_host, true);
  assert.equal(result.idle_packaged_handoff.workspace, paths.appRoot());
});

test('idle handoff accepts an explicitly suppressed dead UI after operator quit', async (t) => {
  const paths = fixture(t);
  const staleDescriptor = descriptor(paths, {
    installation_id: 'f'.repeat(64),
    runtime_mode: 'packaged'
  });
  const proof = await proveIdlePackagedHandoff({
    paths,
    descriptor: staleDescriptor,
    client: {
      status: async () => ({
        pid: staleDescriptor.owner_pid,
        instance_id: staleDescriptor.instance_id,
        process_start_token: OLD_PROCESS_START_TOKEN,
        electron_ui_recovery: {
          registered: true,
          alive: false,
          state: 'suppressed',
          suppressed: true,
          suppression_reason: 'operator_quit'
        }
      }),
      call: async (action) => {
        assert.equal(action, 'runtime.lightweight_snapshot');
        return {
          telemetryAvailable: true,
          signalStale: false,
          snapshotBusy: false,
          busy: false,
          recovering: false,
          mcpRunning: false,
          nativeAlive: false,
          tunnelRunning: false,
          activationEpoch: { state: 'FAILED', admission_open: false },
          device: { workspace: paths.appRoot() }
        };
      }
    }
  });
  assert.equal(proof.exact_host, true);
  assert.equal(proof.workspace, paths.appRoot());
  assert.equal(proof.activation_epoch_state, 'FAILED');
});

test('explicit refresh refuses a cached UI absence while replacement registration is pending', async (t) => {
  const paths = fixture(t);
  const staleDescriptor = descriptor(paths, {
    installation_id: 'f'.repeat(64),
    runtime_mode: 'packaged'
  });
  let stopCalls = 0;
  await assert.rejects(bootstrapCurrentRecoveryHost({
    app: { isPackaged: false, getAppPath: () => paths.appRoot() },
    paths,
    client: {
      status: async () => ({
        pid: staleDescriptor.owner_pid,
        instance_id: staleDescriptor.instance_id,
        process_start_token: OLD_PROCESS_START_TOKEN,
        electron_ui_recovery: {
          alive: false,
          state: 'waiting_for_registration',
          pending_registration_until_unix_ms: Date.now() + 30_000
        }
      }),
      call: async () => ({
        telemetryAvailable: true,
        signalStale: false,
        snapshotBusy: false,
        busy: false,
        recovering: false,
        mcpRunning: false,
        nativeAlive: false,
        tunnelRunning: false,
        activationEpoch: { state: 'READY', admission_open: true },
        device: { workspace: paths.appRoot() }
      }),
      stop: async () => { stopCalls += 1; }
    },
    descriptor: staleDescriptor,
    status: { full_clean_activation: { available: false } },
    operationId: OPERATION_ONE,
    sourceCheckpoint: null,
    expectedDiskRevision: REVISION,
    refresh: true,
    forceRefresh: true,
    allowIdlePackagedHandoff: true
  }), { code: 'RECOVERY_HOST_IDLE_HANDOFF_REFUSED' });
  assert.equal(stopCalls, 0, 'a pending replacement UI must block the handoff before child stop');
});

test('idle handoff shares its deadline with a slow status IPC call', async (t) => {
  const paths = fixture(t);
  const staleDescriptor = descriptor(paths, {
    installation_id: 'f'.repeat(64),
    runtime_mode: 'packaged'
  });
  const requestedTimeouts = [];
  const startedAt = Date.now();
  await assert.rejects(proveIdlePackagedHandoff({
    paths,
    descriptor: staleDescriptor,
    timeoutMs: 25,
    client: {
      status: async (options) => {
        requestedTimeouts.push(options.timeout);
        await new Promise((resolve) => setTimeout(resolve, 300));
        return {};
      },
      call: async () => assert.fail('a status call beyond the deadline must not start the snapshot call')
    }
  }), { code: 'RECOVERY_HOST_IDLE_HANDOFF_UNVERIFIED' });
  assert.ok(Date.now() - startedAt < 250, 'the shared deadline must bound an uncooperative status client');
  assert.equal(requestedTimeouts.length, 1);
  assert.ok(requestedTimeouts[0] > 0 && requestedTimeouts[0] <= 25);
});

test('idle handoff shares its deadline with a slow snapshot IPC call', async (t) => {
  const paths = fixture(t);
  const staleDescriptor = descriptor(paths, {
    installation_id: 'f'.repeat(64),
    runtime_mode: 'packaged'
  });
  const requestedTimeouts = [];
  const startedAt = Date.now();
  await assert.rejects(proveIdlePackagedHandoff({
    paths,
    descriptor: staleDescriptor,
    timeoutMs: 25,
    client: {
      status: async (options) => {
        requestedTimeouts.push(options.timeout);
        return {
          pid: staleDescriptor.owner_pid,
          instance_id: staleDescriptor.instance_id,
          process_start_token: OLD_PROCESS_START_TOKEN,
          electron_ui_recovery: { alive: false, state: 'missing' }
        };
      },
      call: async (_action, _arguments, options) => {
        requestedTimeouts.push(options.timeout);
        await new Promise((resolve) => setTimeout(resolve, 300));
        return {};
      }
    }
  }), { code: 'RECOVERY_HOST_IDLE_HANDOFF_UNVERIFIED' });
  assert.ok(Date.now() - startedAt < 250, 'the shared deadline must bound an uncooperative snapshot client');
  assert.equal(requestedTimeouts.length, 2);
  assert.ok(requestedTimeouts.every((value) => value > 0 && value <= 25));
});

test('explicit refresh waits through a bounded in-flight supervision snapshot before idle handoff', async (t) => {
  const paths = fixture(t);
  const staleDescriptor = descriptor(paths, {
    installation_id: 'f'.repeat(64),
    runtime_mode: 'packaged'
  });
  fs.writeFileSync(paths.recoveryHostDescriptorFile(), JSON.stringify(staleDescriptor), 'utf8');
  let snapshotCalls = 0;
  let sleepCalls = 0;
  let stopCalls = 0;
  const client = {
    status: async () => ({
      pid: staleDescriptor.owner_pid,
      instance_id: staleDescriptor.instance_id,
      process_start_token: OLD_PROCESS_START_TOKEN,
      electron_ui_recovery: { alive: false, state: 'missing' }
    }),
    call: async () => ({
      telemetryAvailable: true,
      signalStale: false,
      snapshotBusy: snapshotCalls++ === 0,
      busy: false,
      recovering: false,
      mcpRunning: false,
      nativeAlive: false,
      tunnelRunning: false,
      activationEpoch: { state: 'READY', admission_open: true },
      device: { workspace: paths.appRoot() }
    }),
    stop: async () => { stopCalls += 1; }
  };
  let alive = true;
  const result = await bootstrapCurrentRecoveryHost({
    app: { isPackaged: false, getAppPath: () => paths.appRoot() },
    paths,
    client,
    descriptor: staleDescriptor,
    status: { full_clean_activation: { available: false } },
    operationId: OPERATION_ONE,
    sourceCheckpoint: null,
    expectedDiskRevision: REVISION,
    refresh: true,
    forceRefresh: true,
    allowIdlePackagedHandoff: true,
    spawnProcess: () => ({ pid: 45003, once(event, listener) { if (event === 'spawn') queueMicrotask(listener); return this; }, unref() {} }),
    processIdentityObserver: async (pid) => alive
      ? { state: 'live', pid, process_start_token: OLD_PROCESS_START_TOKEN }
      : { state: 'absent', pid, process_start_token: null },
    terminateProcess: async () => { alive = false; },
    sleep: async (ms) => {
      assert.equal(ms, 250);
      sleepCalls += 1;
    }
  });
  assert.equal(snapshotCalls, 3,
    'the idle proof must be revalidated at the child-stop boundary');
  assert.equal(sleepCalls, 1);
  assert.equal(stopCalls, 1);
  assert.equal(result.idle_packaged_handoff.exact_host, true);
});

test('explicit refresh still refuses a persistently busy supervision snapshot', async (t) => {
  const paths = fixture(t);
  const staleDescriptor = descriptor(paths, {
    installation_id: 'f'.repeat(64),
    runtime_mode: 'packaged'
  });
  let snapshotCalls = 0;
  let sleepCalls = 0;
  let stopCalls = 0;
  await assert.rejects(bootstrapCurrentRecoveryHost({
    app: { isPackaged: false, getAppPath: () => paths.appRoot() },
    paths,
    client: {
      status: async () => ({
        pid: staleDescriptor.owner_pid,
        instance_id: staleDescriptor.instance_id,
        process_start_token: OLD_PROCESS_START_TOKEN,
        electron_ui_recovery: { alive: false, state: 'missing' }
      }),
      call: async () => {
        snapshotCalls += 1;
        return {
          telemetryAvailable: true,
          signalStale: false,
          snapshotBusy: true,
          busy: false,
          recovering: false,
          mcpRunning: false,
          nativeAlive: false,
          tunnelRunning: false,
          activationEpoch: { state: 'READY', admission_open: true },
          device: { workspace: paths.appRoot() }
        };
      },
      stop: async () => { stopCalls += 1; }
    },
    descriptor: staleDescriptor,
    status: { full_clean_activation: { available: false } },
    operationId: OPERATION_ONE,
    sourceCheckpoint: null,
    expectedDiskRevision: REVISION,
    timeoutMs: 1_000,
    refresh: true,
    forceRefresh: true,
    allowIdlePackagedHandoff: true,
    sleep: async (ms) => {
      assert.equal(ms, 250);
      sleepCalls += 1;
    }
  }), { code: 'RECOVERY_HOST_IDLE_HANDOFF_REFUSED' });
  assert.equal(snapshotCalls, 4);
  assert.equal(sleepCalls, 3);
  assert.equal(stopCalls, 0);
});

test('packaged handoff remains fail closed when any runtime component is live', async (t) => {
  const paths = fixture(t);
  const staleDescriptor = descriptor(paths, {
    installation_id: 'f'.repeat(64),
    runtime_mode: 'packaged'
  });
  let stopCalls = 0;
  await assert.rejects(bootstrapCurrentRecoveryHost({
    app: { isPackaged: false, getAppPath: () => paths.appRoot() },
    paths,
    client: {
      status: async () => ({
        pid: staleDescriptor.owner_pid,
        instance_id: staleDescriptor.instance_id,
        process_start_token: OLD_PROCESS_START_TOKEN,
        electron_ui_recovery: { alive: false, state: 'missing' }
      }),
      call: async () => ({
        telemetryAvailable: true,
        signalStale: false,
        snapshotBusy: false,
        recovering: false,
        mcpRunning: true,
        nativeAlive: true,
        tunnelRunning: false,
        activationEpoch: { state: 'READY', admission_open: true },
        device: { workspace: paths.appRoot() }
      }),
      stop: async () => { stopCalls += 1; }
    },
    descriptor: staleDescriptor,
    status: { full_clean_activation: { available: false } },
    operationId: OPERATION_ONE,
    sourceCheckpoint: null,
    expectedDiskRevision: REVISION,
    refresh: true,
    forceRefresh: true,
    allowIdlePackagedHandoff: true
  }), { code: 'RECOVERY_HOST_IDLE_HANDOFF_REFUSED' });
  assert.equal(stopCalls, 0);
});

test('refused handoff restores children only through the still-exact old Recovery Host', async (t) => {
  const paths = fixture(t);
  const staleDescriptor = descriptor(paths);
  fs.writeFileSync(paths.recoveryHostDescriptorFile(), JSON.stringify(staleDescriptor), 'utf8');
  let stopCalls = 0;
  let startCalls = 0;

  await assert.rejects(bootstrapCurrentRecoveryHost({
    app: { isPackaged: true, getAppPath: () => paths.appRoot() },
    paths,
    client: {
      call: async () => rollbackSnapshot(paths, stopCalls === 0),
      stop: async () => { stopCalls += 1; },
      start: async (options, callOptions) => {
        startCalls += 1;
        assert.deepEqual(options, { reason: 'bootstrap_handoff_rollback' });
        assert.equal(callOptions.expectedOwnerPid, staleDescriptor.owner_pid);
        assert.equal(callOptions.expectedInstanceId, staleDescriptor.instance_id);
        assert.equal(callOptions.expectedOwnerProcessStartToken, OLD_PROCESS_START_TOKEN);
      }
    },
    descriptor: staleDescriptor,
    status: { full_clean_activation: { available: false } },
    operationId: OPERATION_ONE,
    sourceCheckpoint: SOURCE_CHECKPOINT,
    expectedDiskRevision: REVISION,
    processIdentityObserver: async (pid) => ({
      state: 'live',
      pid,
      process_start_token: OLD_PROCESS_START_TOKEN
    }),
    terminateProcess: async () => {
      throw Object.assign(new Error('transient probe unavailable'), { code: 'PROCESS_IDENTITY_UNVERIFIED' });
    },
    sleep: async () => {}
  }), { code: 'RECOVERY_BOOTSTRAP_PROCESS_IDENTITY_UNVERIFIED' });

  assert.equal(stopCalls, 1);
  assert.equal(startCalls, 1);
  const receipt = readBootstrapResult(paths, OPERATION_ONE);
  assert.equal(receipt.state, 'failed');
  assert.equal(receipt.error.code, 'RECOVERY_BOOTSTRAP_PROCESS_IDENTITY_UNVERIFIED');
});

test('failed handoff never restores through a changed Recovery Host descriptor', async (t) => {
  const paths = fixture(t);
  const staleDescriptor = descriptor(paths);
  fs.writeFileSync(paths.recoveryHostDescriptorFile(), JSON.stringify(staleDescriptor), 'utf8');
  let descriptorReads = 0;
  let startCalls = 0;

  await assert.rejects(bootstrapCurrentRecoveryHost({
    app: { isPackaged: true, getAppPath: () => paths.appRoot() },
    paths,
    client: {
      call: async () => rollbackSnapshot(paths, true),
      stop: async () => {},
      start: async () => { startCalls += 1; }
    },
    descriptor: staleDescriptor,
    status: { full_clean_activation: { available: false } },
    operationId: OPERATION_ONE,
    sourceCheckpoint: SOURCE_CHECKPOINT,
    expectedDiskRevision: REVISION,
    processIdentityObserver: async (pid) => ({
      state: 'live',
      pid,
      process_start_token: OLD_PROCESS_START_TOKEN
    }),
    readDescriptor: () => {
      descriptorReads += 1;
      return { ...staleDescriptor, instance_id: 'replacement-host-instance-0001' };
    },
    sleep: async () => {}
  }), { code: 'RECOVERY_BOOTSTRAP_TARGET_CHANGED' });

  assert.equal(descriptorReads, 2);
  assert.equal(startCalls, 0);
});

test('central rollback restores a previously running executor without enabling a direct Tunnel', async (t) => {
  const paths = fixture(t);
  const target = descriptor(paths);
  fs.writeFileSync(paths.recoveryHostDescriptorFile(), JSON.stringify(target));
  let stopped = false;
  let starts = 0;
  await assert.rejects(bootstrapCurrentRecoveryHost({
    app: { isPackaged: true, getAppPath: () => paths.appRoot() }, paths,
    descriptor: target, status: { full_clean_activation: { available: false } },
    client: {
      call: async (action, args, options) => {
        assert.equal(action, 'runtime.snapshot');
        assert.equal(args[0].force, true);
        assert.equal(options.expectedInstanceId, target.instance_id);
        const snapshot = rollbackSnapshot(paths, !stopped, { tunnelRunning: false });
        snapshot.settings.executionRole = 'central_executor';
        return snapshot;
      },
      stop: async () => { stopped = true; }, start: async () => { starts++; }
    },
    operationId: OPERATION_ONE, sourceCheckpoint: SOURCE_CHECKPOINT, expectedDiskRevision: REVISION,
    processIdentityObserver: async (pid) => ({ state: 'live', pid, process_start_token: OLD_PROCESS_START_TOKEN }),
    terminateProcess: async () => { throw Object.assign(new Error('probe unavailable'), { code: 'PROCESS_IDENTITY_UNVERIFIED' }); }
  }), { code: 'RECOVERY_BOOTSTRAP_PROCESS_IDENTITY_UNVERIFIED' });
  assert.equal(starts, 1);
  assert.equal(readBootstrapResult(paths, OPERATION_ONE).state, 'failed');
});

test('failed exact termination carries cause and exit code into the durable bootstrap receipt', async (t) => {
  const paths = fixture(t);
  const staleDescriptor = descriptor(paths);
  fs.writeFileSync(paths.recoveryHostDescriptorFile(), JSON.stringify(staleDescriptor), 'utf8');
  await assert.rejects(bootstrapCurrentRecoveryHost({
    app: { isPackaged: true, getAppPath: () => paths.appRoot() },
    paths, descriptor: staleDescriptor,
    client: { stop: async () => {} },
    status: { full_clean_activation: { available: false } },
    operationId: OPERATION_ONE, sourceCheckpoint: SOURCE_CHECKPOINT, expectedDiskRevision: REVISION,
    processIdentityObserver: async (pid) => ({ state: 'live', pid, process_start_token: OLD_PROCESS_START_TOKEN }),
    terminateProcess: async () => {
      throw Object.assign(new Error('failed kill'), {
        code: 'PROCESS_TERMINATION_FAILED',
        details: { cause_code: 'PROCESS_TERMINATION_TIMEOUT', exit_code: 128, stdout: 'not evidence' }
      });
    },
    spawnProcess: () => assert.fail('a live root must prevent replacement')
  }), { code: 'RECOVERY_BOOTSTRAP_TERMINATION_FAILED' });
  assert.deepEqual(readBootstrapResult(paths, OPERATION_ONE).error.details, {
    cause_code: 'PROCESS_TERMINATION_FAILED', termination_cause_code: 'PROCESS_TERMINATION_TIMEOUT',
    pid: staleDescriptor.owner_pid, exit_code: 128
  });
});

test('trusted bootstrap revalidates its recovery_host receipt before it can stop the old host', async (t) => {
  const paths = fixture(t);
  const staleDescriptor = descriptor(paths);
  fs.writeFileSync(paths.recoveryHostDescriptorFile(), JSON.stringify(staleDescriptor), 'utf8');
  const attestation = trustedSourceAttestation();
  let validationCalls = 0;
  let stopCalls = 0;
  let alive = true;
  const result = await bootstrapCurrentRecoveryHost({
    app: { isPackaged: true, getAppPath: () => paths.appRoot() },
    paths,
    client: { stop: async () => { stopCalls += 1; } },
    descriptor: staleDescriptor,
    status: { full_clean_activation: { available: false } },
    operationId: OPERATION_ONE,
    sourceCheckpoint: SOURCE_CHECKPOINT,
    expectedDiskRevision: REVISION,
    trustedRecoveryBootstrap: attestation,
    revalidateTrustedSourceFn: async (workspace, sourceCheckpoint, receivedAttestation) => {
      validationCalls += 1;
      assert.equal(workspace, paths.appRoot());
      assert.deepEqual(sourceCheckpoint, SOURCE_CHECKPOINT);
      assert.deepEqual(receivedAttestation, attestation);
      return { source_checkpoint: sourceCheckpoint, attestation: receivedAttestation };
    },
    spawnProcess: () => ({ pid: 45002, once(event, listener) { if (event === 'spawn') queueMicrotask(listener); return this; }, unref() {} }),
    processIdentityObserver: async (pid) => alive
      ? { state: 'live', pid, process_start_token: OLD_PROCESS_START_TOKEN }
      : { state: 'absent', pid, process_start_token: null },
    terminateProcess: async () => { alive = false; },
    sleep: async () => {}
  });

  assert.equal(validationCalls, 1);
  assert.equal(stopCalls, 1);
  assert.equal(result.required, true);
  assert.deepEqual(readBootstrapEnvelope(paths, { bootstrapId: OPERATION_ONE }).trusted_recovery_bootstrap, attestation);

  let rejectedStopCalls = 0;
  await assert.rejects(bootstrapCurrentRecoveryHost({
    app: { isPackaged: true, getAppPath: () => paths.appRoot() },
    paths,
    client: { stop: async () => { rejectedStopCalls += 1; } },
    descriptor: staleDescriptor,
    status: { full_clean_activation: { available: false } },
    operationId: OPERATION_TWO,
    sourceCheckpoint: SOURCE_CHECKPOINT,
    expectedDiskRevision: REVISION,
    trustedRecoveryBootstrap: attestation,
    revalidateTrustedSourceFn: async () => { throw Object.assign(new Error('receipt changed'), { code: 'TRUSTED_BOOTSTRAP_SOURCE_DRIFT' }); }
  }), { code: 'TRUSTED_BOOTSTRAP_SOURCE_DRIFT' });
  assert.equal(rejectedStopCalls, 0);
});

test('bootstrap host revalidates trusted source before creating a durable same-operation epoch', async (t) => {
  const paths = fixture(t);
  const request = envelope(paths, OPERATION_ONE, {
    descriptor: { owner_pid: 78001, instance_id: 'old-stale-host-0001' },
    trustedRecoveryBootstrap: trustedSourceAttestation()
  });
  writeBootstrapEnvelope(paths, request);
  writeBootstrapResult(paths, { operation_id: OPERATION_ONE, state: 'started' });
  let recoveryPlaneEnsures = 0;
  let ordinaryStarts = 0;
  let trustedValidationCalls = 0;
  const orchestrator = {
    setFullCleanActivation() {},
    setActivationEpoch() {},
    activationEpochStatus: () => null,
    codingMcpRevisionStatus: () => ({
      running_revision: REVISION,
      disk_revision: REVISION,
      update_pending: false,
      state: 'current'
    }),
    start: async () => { ordinaryStarts += 1; },
    lightweightSnapshot: async () => ({ fullyReady: false }),
    isManuallyStopped: () => false
  };
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ workspace: paths.appRoot(), autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: logStub(),
    orchestrator,
    healthService: { inspect: async () => ({}), repair: async () => ({}) },
    gateway: { start: async () => {}, stop: async () => {}, metrics: () => ({}) },
    ipcServerFactory: () => ({ start: async () => ({}), stop: async () => true }),
    revisionTracker: {
      captureRunning: () => REVISION,
      status: () => ({ running_revision: REVISION, disk_revision: REVISION, update_pending: false, state: 'current' })
    },
    recoveryPlaneService: {
      setActivationEpoch() {},
      stop: async () => {},
      ensure: async () => { recoveryPlaneEnsures += 1; return { state: 'healthy' }; }
    },
    bootstrap: request,
    trustedRecoverySourceValidator: async (workspace, sourceCheckpoint, attestation) => {
      trustedValidationCalls += 1;
      assert.equal(workspace, paths.appRoot());
      assert.deepEqual(sourceCheckpoint, SOURCE_CHECKPOINT);
      assert.deepEqual(attestation, request.trusted_recovery_bootstrap);
      return { source_checkpoint: sourceCheckpoint, attestation };
    },
    processIdentityObserver: async (pid) => pid === process.pid
      ? { state: 'live', pid, process_start_token: CURRENT_PROCESS_START_TOKEN }
      : { state: 'absent', pid, process_start_token: null },
    exitProcess: () => {}
  });
  host.fullCleanActivation.restart = async (options) => {
    const created = host.activationEpochStore.create({
      operation_id: options.operationId,
      source_checkpoint: options.sourceCheckpoint,
      expires_at_unix_ms: options.expiresAtUnixMs,
      metadata: { reason: options.reason },
      component_evidence: { recovery_host: { instance_id: host.instanceId, pid: process.pid } }
    });
    host.activationEpochStore.update(created.activation_epoch_id, { state: 'ADMISSION_CLOSED', reason: 'test-bootstrap' });
    return { state: 'HANDOFF', activation_epoch_id: created.activation_epoch_id };
  };

  t.after(() => host.stop());
  const status = await host.start();
  const current = host.activationEpochStore.current();
  assert.equal(current.operation_id, OPERATION_ONE);
  assert.equal(current.metadata.reason, 'recovery_host_bootstrap');
  assert.equal(status.activation_epoch.operation_id, OPERATION_ONE);
  assert.equal(status.activation_epoch.admission_open, false);
  assert.equal(status.state, 'bootstrapping');
  assert.equal(trustedValidationCalls, 1);
  assert.equal(host.supervisionTimer, null);
  assert.equal(recoveryPlaneEnsures, 0);
  assert.equal(ordinaryStarts, 0);
  assert.equal(fs.existsSync(paths.recoveryHostBootstrapFile(OPERATION_ONE)), false);
  assert.equal(readBootstrapResult(paths, OPERATION_ONE).state, 'started');
  assert.equal((await host.handlers()['recovery.ping']()).ready, false);
  await assert.rejects(host.handlers()['runtime.restart']({}), { code: 'RECOVERY_BOOTSTRAP_IN_PROGRESS' });
});

test('bootstrap replay before durable HANDOFF terminalizes fail-closed instead of skipping to replacement startup', async (t) => {
  const paths = fixture(t);
  const request = envelope(paths, OPERATION_ONE, {
    descriptor: { owner_pid: 78002, instance_id: 'old-stale-host-0002' }
  });
  writeBootstrapEnvelope(paths, request);
  writeBootstrapResult(paths, { operation_id: OPERATION_ONE, state: 'started' });
  let gatewayStarts = 0;
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ workspace: paths.appRoot(), autoStartServices: false }) },
    secrets: {},
    environment: {},
    log: logStub(),
    orchestrator: {
      setFullCleanActivation() {},
      setActivationEpoch() {},
      codingMcpRevisionStatus: () => ({ running_revision: REVISION, disk_revision: REVISION, update_pending: false, state: 'current' })
    },
    healthService: {},
    gateway: { start: async () => { gatewayStarts += 1; }, stop: async () => {} },
    ipcServerFactory: () => ({ start: async () => ({}), stop: async () => true }),
    revisionTracker: {
      captureRunning: () => REVISION,
      status: () => ({ running_revision: REVISION, disk_revision: REVISION, update_pending: false, state: 'current' })
    },
    recoveryPlaneService: { setActivationEpoch() {} },
    bootstrap: request,
    processIdentityObserver: async (pid) => pid === process.pid
      ? { state: 'live', pid, process_start_token: CURRENT_PROCESS_START_TOKEN }
      : { state: 'absent', pid, process_start_token: null }
  });
  const created = host.activationEpochStore.create({
    operation_id: OPERATION_ONE,
    source_checkpoint: SOURCE_CHECKPOINT,
    expires_at_unix_ms: request.expires_at_unix_ms,
    metadata: { reason: 'recovery_host_bootstrap' },
    component_evidence: { recovery_host: { instance_id: 'previous-bootstrap-host-0001', pid: 77001 } }
  });
  host.activationEpochStore.update(created.activation_epoch_id, { state: 'ADMISSION_CLOSED', reason: 'crash-before-fence' });

  await assert.rejects(host.start(), { code: 'ACTIVATION_EPOCH_RESUME_UNSAFE' });
  const terminal = host.activationEpochStore.current();
  assert.equal(terminal.state, 'FAILED');
  assert.equal(terminal.admission_state, 'CLOSED');
  assert.equal(terminal.error.code, 'ACTIVATION_EPOCH_RESUME_UNSAFE');
  assert.equal(readBootstrapResult(paths, OPERATION_ONE).state, 'failed');
  assert.equal(fs.existsSync(paths.recoveryHostBootstrapFile(OPERATION_ONE)), false);
  assert.equal(gatewayStarts, 0);
  assert.equal(fs.existsSync(paths.recoveryHostLockFile()), false);
});

test('new bootstrap terminalizes an expired prior epoch and can create a fresh operation', async (t) => {
  const paths = fixture(t);
  const request = envelope(paths, OPERATION_TWO, {
    descriptor: { owner_pid: 78003, instance_id: 'expired-prior-host-0001' }
  });
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ workspace: paths.appRoot(), autoStartServices: false }) },
    secrets: {},
    environment: {},
    log: logStub(),
    orchestrator: {
      setFullCleanActivation() {},
      setActivationEpoch() {},
      codingMcpRevisionStatus: () => ({
        running_revision: REVISION,
        disk_revision: REVISION,
        update_pending: false,
        state: 'current'
      })
    },
    healthService: {},
    gateway: {},
    revisionTracker: {
      captureRunning: () => REVISION,
      status: () => ({
        running_revision: REVISION,
        disk_revision: REVISION,
        update_pending: false,
        state: 'current'
      })
    },
    recoveryPlaneService: { setActivationEpoch() {} },
    bootstrap: request,
    processIdentityObserver: async (pid) => ({ state: 'absent', pid, process_start_token: null })
  });
  const originalNow = Date.now;
  let now = originalNow();
  Date.now = () => now;
  try {
    const created = host.activationEpochStore.create({
      operation_id: OPERATION_ONE,
      expires_at_unix_ms: now + 30,
      component_evidence: {
        recovery_host: { instance_id: 'expired-epoch-owner-0001', pid: 78002 }
      }
    });
    host.activationEpochStore.update(created.activation_epoch_id, { state: 'VERIFYING' });
    now += 40;

    const plan = await host.prepareBootstrapStart(host.activationEpochStore.current());
    assert.equal(plan.operationId, OPERATION_TWO);
    assert.equal(plan.requiresNewEpoch, true);
    assert.equal(plan.durableEpoch.state, 'FAILED');
    assert.equal(plan.durableEpoch.error.code, 'ACTIVATION_REQUEST_EXPIRED');
    assert.equal(host.activationEpochStore.current().state, 'FAILED');
  } finally {
    Date.now = originalNow;
  }
});

test('receipt-conflict reconciliation preserves a failed bootstrap receipt and releases admission only after epoch, identity, and census proof', async (t) => {
  const paths = fixture(t);
  const request = envelope(paths, OPERATION_ONE, {
    sourceCheckpoint: null,
    refresh: true,
    descriptor: { owner_pid: 78004, instance_id: 'old-recovery-host-reconcile-0001' }
  });
  writeBootstrapEnvelope(paths, request);
  writeBootstrapResult(paths, {
    operation_id: OPERATION_ONE,
    state: 'failed',
    error: { code: 'ORCHESTRATION_STATE_UNCERTAIN', message: 'The prior stopped-runtime census was not quiescent.' }
  });
  const before = readBootstrapResult(paths, OPERATION_ONE);
  const readyEpoch = {
    activation_epoch_id: 'activation-reconciled-ready-0001',
    operation_id: OPERATION_TWO,
    state: 'READY',
    admission_state: 'OPEN'
  };
  const censusCalls = [];
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ workspace: paths.appRoot(), autoStartServices: false }) },
    secrets: {},
    environment: {},
    log: logStub(),
    orchestrator: {
      setFullCleanActivation() {},
      setActivationEpoch() {},
      codingMcpRevisionStatus: () => ({ running_revision: REVISION, disk_revision: REVISION, update_pending: false, state: 'current' })
    },
    healthService: {},
    gateway: {},
    revisionTracker: {
      captureRunning: () => REVISION,
      status: () => ({ running_revision: REVISION, disk_revision: REVISION, update_pending: false, state: 'current' })
    },
    recoveryPlaneService: { setActivationEpoch() {} },
    bootstrap: request,
    processIdentityObserver: async (pid) => ({ state: 'live', pid, process_start_token: CURRENT_PROCESS_START_TOKEN }),
    canonicalLedgerCensusFn: async (options) => {
      censusCalls.push(options);
      return {
        safe: true,
        code: 'READY',
        reason: 'canonical_ledger_quiescent',
        content_free: true,
        mutated_canonical_ledger: false,
        census_fingerprint: 'f'.repeat(64),
        snapshot: { immutable: true, query_only: true },
        lifecycle: {
          projection_drift: false,
          unexplained_active_runs: 0,
          unbound_live_resource_residues: 0
        }
      };
    }
  });
  host.activationEpochStore.current = () => ({ ...readyEpoch });
  host.running = true;
  host.ownsLock = true;
  host.processIdentity = { pid: process.pid, process_start_token: CURRENT_PROCESS_START_TOKEN };
  host.lastSupervisionStatus = {};
  host.bootstrapActivation = {
    state: 'receipt_conflict',
    operation_id: OPERATION_TWO,
    activation_epoch_id: readyEpoch.activation_epoch_id,
    error_code: 'ORCHESTRATION_STATE_UNCERTAIN'
  };
  fs.writeFileSync(paths.recoveryHostLockFile(), JSON.stringify({ pid: process.pid, instance_id: host.instanceId }), 'utf8');

  const reconciliation = await host.reconcileTerminalBootstrapReceipt(readyEpoch);

  assert.equal(reconciliation.state, 'reconciled_terminal_receipt');
  assert.equal(reconciliation.attempted_operation_id, OPERATION_ONE);
  assert.equal(reconciliation.operation_id, OPERATION_TWO);
  assert.equal(reconciliation.activation_epoch_id, readyEpoch.activation_epoch_id);
  assert.equal(reconciliation.terminal_result_state, 'failed');
  assert.equal(reconciliation.error_code, 'ORCHESTRATION_STATE_UNCERTAIN');
  assert.equal(fs.existsSync(paths.recoveryHostBootstrapFile(OPERATION_ONE)), false);
  assert.deepEqual(readBootstrapResult(paths, OPERATION_ONE), before, 'terminal failed receipt must remain immutable evidence');
  assert.equal(censusCalls.length, 1);
  assert.equal(censusCalls[0].workspace, paths.appRoot());
  assert.equal(censusCalls[0].allowAcceptancePending, true, 'only the validated checkpoint-free refresh may preserve pending acceptance records');
  assert.equal(host.bootstrapBlocksAdmission(), false);
  assert.equal((await host.handlers()['recovery.ping']()).ready, true);
  const snapshot = host.cachedRuntimeSnapshot();
  assert.notEqual(snapshot.mcpRunning, true, 'reconciliation must not fabricate MCP readiness');
  assert.notEqual(snapshot.tunnelRunning, true, 'reconciliation must not fabricate tunnel readiness');
});

test('receipt-conflict reconciliation remains admission-closed when the terminal bootstrap receipt is missing', async (t) => {
  const paths = fixture(t);
  const request = envelope(paths, OPERATION_ONE, {
    sourceCheckpoint: null,
    refresh: true,
    descriptor: { owner_pid: 78005, instance_id: 'old-recovery-host-reconcile-0002' }
  });
  writeBootstrapEnvelope(paths, request);
  const readyEpoch = {
    activation_epoch_id: 'activation-reconciled-ready-0002',
    operation_id: OPERATION_TWO,
    state: 'READY',
    admission_state: 'OPEN'
  };
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ workspace: paths.appRoot(), autoStartServices: false }) },
    secrets: {},
    environment: {},
    log: logStub(),
    orchestrator: {
      setFullCleanActivation() {},
      setActivationEpoch() {},
      codingMcpRevisionStatus: () => ({ running_revision: REVISION, disk_revision: REVISION, update_pending: false, state: 'current' })
    },
    healthService: {},
    gateway: {},
    revisionTracker: {
      captureRunning: () => REVISION,
      status: () => ({ running_revision: REVISION, disk_revision: REVISION, update_pending: false, state: 'current' })
    },
    recoveryPlaneService: { setActivationEpoch() {} },
    bootstrap: request,
    processIdentityObserver: async (pid) => ({ state: 'live', pid, process_start_token: CURRENT_PROCESS_START_TOKEN }),
    canonicalLedgerCensusFn: async () => { throw new Error('census must not run before terminal receipt validation'); }
  });
  host.activationEpochStore.current = () => ({ ...readyEpoch });
  host.running = true;
  host.ownsLock = true;
  host.processIdentity = { pid: process.pid, process_start_token: CURRENT_PROCESS_START_TOKEN };
  host.bootstrapActivation = {
    state: 'receipt_conflict',
    operation_id: OPERATION_TWO,
    activation_epoch_id: readyEpoch.activation_epoch_id
  };
  fs.writeFileSync(paths.recoveryHostLockFile(), JSON.stringify({ pid: process.pid, instance_id: host.instanceId }), 'utf8');

  await assert.rejects(host.reconcileTerminalBootstrapReceipt(readyEpoch), {
    code: 'RECOVERY_BOOTSTRAP_RECONCILIATION_RECEIPT_UNVERIFIED'
  });
  assert.equal(fs.existsSync(paths.recoveryHostBootstrapFile(OPERATION_ONE)), true);
  assert.equal(host.bootstrapBlocksAdmission(), true);
});

test('host status exposes durable operation binding and fails closed on incomplete connector evidence', async (t) => {
  const paths = fixture(t);
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ workspace: paths.appRoot(), autoStartServices: false }) },
    secrets: {},
    environment: {},
    log: logStub(),
    orchestrator: {
      setFullCleanActivation() {},
      codingMcpRevisionStatus: () => ({ running_revision: REVISION, disk_revision: REVISION, update_pending: false, state: 'current' }),
      activationEpochStatus: () => ({ activation_epoch_id: 'epoch-bootstrap-0002', state: 'PREPARING', admission_open: false, update_incomplete: true })
    },
    healthService: {},
    gateway: {},
    revisionTracker: {
      captureRunning: () => REVISION,
      status: () => ({ running_revision: REVISION, disk_revision: REVISION, update_pending: false, state: 'current' })
    },
    recoveryPlaneService: { setActivationEpoch() {} }
  });
  host.activationEpochStore.create({
    activation_epoch_id: 'epoch-bootstrap-0002',
    operation_id: OPERATION_TWO
  });
  host.lastSupervisionStatus = {
    fullyReady: true,
    connectorRefreshRequired: false,
    connectorRediscovered: true,
    connectorAcknowledgementPending: false,
    connectorContractState: 'CURRENT_ACKNOWLEDGED',
    toolContract: { sha256: 'd'.repeat(64) },
    connectorContractAcknowledgedSha256: null
  };
  let status = host.hostStatus();
  assert.equal(status.activation_epoch.operation_id, OPERATION_TWO);
  assert.equal((await host.handlers()['runtime.activation_epoch_status']()).operation_id, OPERATION_TWO);
  assert.equal(status.runtime.connector_ready, false);
  assert.equal(status.runtime.connector_ack_sha_matches, false);
  assert.equal(status.runtime.fully_ready, false);

  host.lastSupervisionStatus.connectorContractAcknowledgedSha256 = 'd'.repeat(64);
  status = host.hostStatus();
  // An acknowledgement hash alone is not a current connector receipt.  The
  // freshness mode and a bounded, process-bound rediscovery timestamp are
  // required before Recovery Host can project connector readiness.
  assert.equal(status.runtime.connector_ready, false);
  assert.equal(status.runtime.connector_ack_sha_matches, true);
  assert.equal(status.runtime.fully_ready, false, 'closed activation admission remains authoritative');

  host.lastSupervisionStatus.connectorFreshnessMode = 'current_process_discovery';
  host.lastSupervisionStatus.connectorRediscoveredAt = '2026-01-01T00:00:00.000Z';
  status = host.hostStatus();
  assert.equal(status.runtime.connector_ready, true);
  assert.equal(status.runtime.connector_ack_sha_matches, true);
  assert.equal(status.runtime.fully_ready, false, 'closed activation admission remains authoritative');
});
