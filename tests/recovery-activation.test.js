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
const SOURCE_CHECKPOINT = Object.freeze({
  checkpoint_id: 'checkpoint-activation-0001',
  run_id: 'run-activation-0001',
  wave_id: 'wave-activation-0001',
  proof_fingerprint: 'c'.repeat(64),
  git_head: 'd'.repeat(40)
});

function lifecycleCounts(overrides = {}) {
  return {
    active_tool_calls: 0,
    active_commands: 0,
    starting_commands: 0,
    active_background_operations: 0,
    active_managed_processes: 0,
    foreign_heavy_processes: 0,
    active_agent_lanes: 0,
    threshold_sensitive_stale_candidates: 0,
    owned_codex_sidecar_residues: 0,
    ...overrides
  };
}

function lifecycleSnapshot(overrides = {}) {
  return {
    backup_api_copy: true,
    immutable: true,
    query_only: true,
    integrity_check: ['ok'],
    foreign_key_check_rows: 0,
    sha256: 'e'.repeat(64),
    logical_sha256: 'f'.repeat(64),
    ...overrides
  };
}

function safeLifecycle({
  sourceVerified = true,
  operationId = 'operation-00000001',
  sourceCheckpoint = SOURCE_CHECKPOINT,
  countOverrides = {},
  lifecycleOverrides = {}
} = {}) {
  return {
    safe: true,
    code: 'READY',
    reason: 'idle',
    operation_id: operationId,
    counts: lifecycleCounts(countOverrides),
    lifecycle: {
      snapshot: lifecycleSnapshot(),
      unexplained_active_runs: 0,
      unbound_live_resource_residues: 0,
      ...lifecycleOverrides
    },
    ...(sourceVerified ? { source_checkpoint: {
      ok: true,
      code: 'ACTIVATABLE',
      ...sourceCheckpoint
    } } : {})
  };
}

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
    allow_acceptance_pending: false,
    source_checkpoint: { ...SOURCE_CHECKPOINT }
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
  const {
    activateCodingMcpUpdate: customActivate,
    codingMcpRevisionStatus: customRevisionStatus,
    currentMcpHealth: customHealth,
    ...rest
  } = overrides;
  let runningRevision = OLD;
  let processInstanceId = 'mcp-process-old-0001';
  return {
    codingMcpRevisionStatus: customRevisionStatus || (() => ({ running_revision: runningRevision, disk_revision: NEXT, update_pending: runningRevision !== NEXT, state: runningRevision === NEXT ? 'current' : 'update_pending' })),
    currentMcpHealth: customHealth || (async () => ({ process_instance_id: processInstanceId, code_revision: runningRevision })),
    inspectCodeActivation: async () => ({ ...safeLifecycle({ sourceVerified: false }), workspace: 'C:\\work' }),
    prepareCodeActivation: async ({ operationId, sourceCheckpoint }) => ({
      ...safeLifecycle({ operationId, sourceCheckpoint }),
      fenced: true,
      fence_operation_id: operationId
    }),
    cancelCodeActivation: async () => true,
    verifyCodeActivation: async (operationId, sourceCheckpoint) => ({
      ...safeLifecycle({ operationId, sourceCheckpoint }),
      operation_id: operationId,
      fenced: false,
      fence_operation_id: null
    }),
    activateCodingMcpUpdate: async (...args) => {
      const result = customActivate
        ? await customActivate(...args)
        : { old_instance_id: processInstanceId, new_instance_id: 'mcp-process-new-0001', old_revision: OLD, new_revision: NEXT, health_verified: true, tunnel_preserved: true };
      if (result?.health_verified === true && result?.new_revision) {
        runningRevision = result.new_revision;
        processInstanceId = result.new_instance_id || processInstanceId;
      }
      return result;
    },
    ...rest
  };
}

test('activation requests are strict, bounded, and expire', () => {
  const now = Date.now();
  const normalized = normalizeActivationRequest(request('coding_mcp', now), now);
  assert.equal(normalized.component, 'coding_mcp');
  assert.deepEqual(normalized.source_checkpoint, SOURCE_CHECKPOINT);
  assert.throws(() => normalizeActivationRequest({
    ...request('coding_mcp', now),
    source_checkpoint: undefined
  }, now), { code: 'ACTIVATION_SOURCE_CHECKPOINT_REQUIRED' });
  assert.throws(() => normalizeActivationRequest({ ...request('coding_mcp', now), executable: 'cmd.exe' }, now), { code: 'INVALID_ARGUMENT' });
  assert.throws(() => normalizeActivationRequest({
    ...request('coding_mcp', now),
    source_checkpoint: { ...SOURCE_CHECKPOINT, unexpected: true }
  }, now), { code: 'INVALID_ARGUMENT' });
  assert.throws(() => normalizeActivationRequest({
    ...request('coding_mcp', now),
    source_checkpoint: { ...SOURCE_CHECKPOINT, proof_fingerprint: 'bad' }
  }, now), { code: 'INVALID_SOURCE_CHECKPOINT' });
  assert.throws(() => normalizeActivationRequest({
    ...request('coding_mcp', now),
    source_checkpoint: { ...SOURCE_CHECKPOINT, proof_fingerprint: '' }
  }, now), { code: 'INVALID_SOURCE_CHECKPOINT' });
  assert.throws(() => normalizeActivationRequest({
    ...request('coding_mcp', now),
    source_checkpoint: { ...SOURCE_CHECKPOINT, checkpoint_id: ` ${SOURCE_CHECKPOINT.checkpoint_id}` }
  }, now), { code: 'INVALID_SOURCE_CHECKPOINT' });
  assert.throws(() => normalizeActivationRequest({
    ...request('coding_mcp', now),
    source_checkpoint: { ...SOURCE_CHECKPOINT, proof_fingerprint: SOURCE_CHECKPOINT.proof_fingerprint.toUpperCase() }
  }, now), { code: 'INVALID_SOURCE_CHECKPOINT' });
  assert.throws(() => normalizeActivationRequest(request('all', now), now), { code: 'INVALID_COMPONENT' });
  assert.throws(() => normalizeActivationRequest({ ...request('coding_mcp', now), expires_at_unix_ms: now - 1 }, now), { code: 'ACTIVATION_REQUEST_EXPIRED' });
});

test('direct activation without source authority is rejected before an action claim', async (t) => {
  const paths = fixture(t);
  const manager = new RecoveryActivation({
    paths,
    revisions: revisions(),
    orchestrator: orchestrator(),
    log: {},
    recoveryInstanceId: 'recovery-instance-0001',
    recoveryRunningRevision: OLD
  });
  const input = request('coding_mcp');
  delete input.source_checkpoint;
  await assert.rejects(manager.activate(input), { code: 'ACTIVATION_SOURCE_CHECKPOINT_REQUIRED' });
  assert.equal(manager.actions.load().actions.length, 0);
});

test('noncanonical or identity-mismatched prepare receipt releases the fence before mutation', async (t) => {
  for (const [label, prepareResult] of [
    ['unverified-source', ({ operationId }) => ({
      ...safeLifecycle({ sourceVerified: false, operationId }),
      fenced: true,
      fence_operation_id: operationId
    })],
    ['wrong-operation', () => ({
      ...safeLifecycle({ operationId: 'operation-other-0001' }),
      fenced: true,
      fence_operation_id: 'operation-other-0001'
    })],
    ['wrong-response-operation', ({ operationId }) => ({
      ...safeLifecycle({ operationId: 'operation-other-0001' }),
      fenced: true,
      fence_operation_id: operationId
    })],
    ['wrong-checkpoint', ({ operationId }) => ({
      ...safeLifecycle({
        operationId,
        sourceCheckpoint: { ...SOURCE_CHECKPOINT, wave_id: 'wave-activation-other' }
      }),
      fenced: true,
      fence_operation_id: operationId
    })],
    ['active-runtime-count', ({ operationId }) => ({
      ...safeLifecycle({ operationId, countOverrides: { active_commands: 1 } }),
      fenced: true,
      fence_operation_id: operationId
    })],
    ['invalid-lifecycle-snapshot', ({ operationId }) => ({
      ...safeLifecycle({
        operationId,
        lifecycleOverrides: { snapshot: lifecycleSnapshot({ immutable: false }) }
      }),
      fenced: true,
      fence_operation_id: operationId
    })]
  ]) {
    await t.test(label, async (t) => {
      const paths = fixture(t);
      let activated = false;
      let cancelled = 0;
      const manager = new RecoveryActivation({
        paths,
        revisions: revisions(),
        orchestrator: orchestrator({
          prepareCodeActivation: async (options) => prepareResult(options),
          activateCodingMcpUpdate: async () => { activated = true; },
          cancelCodeActivation: async () => { cancelled += 1; return true; }
        }),
        log: {},
        recoveryInstanceId: 'recovery-instance-0001',
        recoveryRunningRevision: OLD
      });
      const result = await manager.activate(request('coding_mcp'));
      assert.equal(result.state, 'refused');
      assert.equal(result.error.code, 'ACTIVATION_PREFLIGHT_UNVERIFIED');
      assert.equal(activated, false);
      assert.equal(cancelled, 1);
    });
  }
});

test('fresh post-cancel verification requires exact operation, checkpoint, zero blockers, and canonical snapshot', async (t) => {
  const cases = [
    ['wrong-operation', (operationId, sourceCheckpoint) => safeLifecycle({
      operationId: 'operation-other-0001', sourceCheckpoint
    })],
    ['wrong-checkpoint', (operationId) => safeLifecycle({
      operationId,
      sourceCheckpoint: { ...SOURCE_CHECKPOINT, checkpoint_id: 'checkpoint-activation-other' }
    })],
    ['active-runtime-count', (operationId, sourceCheckpoint) => safeLifecycle({
      operationId, sourceCheckpoint, countOverrides: { active_agent_lanes: 1 }
    })],
    ['unexplained-run', (operationId, sourceCheckpoint) => safeLifecycle({
      operationId, sourceCheckpoint, lifecycleOverrides: { unexplained_active_runs: 1 }
    })],
    ['invalid-snapshot', (operationId, sourceCheckpoint) => safeLifecycle({
      operationId,
      sourceCheckpoint,
      lifecycleOverrides: { snapshot: lifecycleSnapshot({ integrity_check: ['corrupt'] }) }
    })]
  ];
  for (const [label, verification] of cases) {
    await t.test(label, async (t) => {
      const paths = fixture(t);
      const manager = new RecoveryActivation({
        paths,
        revisions: revisions(),
        orchestrator: orchestrator({
          verifyCodeActivation: async (operationId, sourceCheckpoint) => ({
            ...verification(operationId, sourceCheckpoint),
            fenced: false,
            fence_operation_id: null
          })
        }),
        log: {},
        recoveryInstanceId: 'recovery-instance-0001',
        recoveryRunningRevision: OLD
      });
      await assert.rejects(
        manager.verifyCheckpointLifecycle({
          operationId: 'operation-verify-0001',
          sourceCheckpoint: SOURCE_CHECKPOINT
        }),
        { code: 'LIFECYCLE_VERIFICATION_FAILED' }
      );
    });
  }
});

test('zero-target lifecycle verification accepts canonical empty proof without weakening component activation requests', async (t) => {
  const paths = fixture(t);
  const manager = new RecoveryActivation({
    paths,
    revisions: revisions(),
    orchestrator: orchestrator(),
    log: {},
    recoveryInstanceId: 'recovery-instance-0001',
    recoveryRunningRevision: OLD
  });
  const sourceCheckpoint = { ...SOURCE_CHECKPOINT, proof_fingerprint: '' };
  const verified = await manager.verifyCheckpointLifecycle({
    operationId: 'operation-zero-target-0001',
    sourceCheckpoint
  });
  assert.equal(verified.clean, true);
  assert.equal(verified.source_checkpoint_verified, true);
  assert.throws(
    () => normalizeActivationRequest({
      ...request('coding_mcp'),
      source_checkpoint: sourceCheckpoint
    }),
    { code: 'INVALID_SOURCE_CHECKPOINT' }
  );
});

test('durable action store replays the same operation and rejects payload conflicts', (t) => {
  const paths = fixture(t);
  let now = Date.now();
  const store = new RecoveryActionStore({ paths, now: () => now });
  const firstRequest = request('coding_mcp', now);
  assert.equal(store.begin(firstRequest).created, true);
  assert.equal(store.begin(firstRequest).created, false);
  assert.throws(() => store.begin({ ...firstRequest, component: 'electron_ui' }), { code: 'IDEMPOTENCY_CONFLICT' });
  assert.throws(() => store.begin(request('electron_ui', now, 'operation-conflict-0001')), { code: 'ACTIVATION_CONFLICT' });
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
  let prepareOptions = null;
  const manager = new RecoveryActivation({
    paths,
    revisions: revisions(),
    orchestrator: orchestrator({
      prepareCodeActivation: async (options) => {
        calls.prepare += 1;
        prepareOptions = options;
        return { ...safeLifecycle({ operationId: options.operationId, sourceCheckpoint: options.sourceCheckpoint }), fenced: true, fence_operation_id: options.operationId };
      },
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
  assert.equal(first.result.postflight.schema_version, 2);
  assert.equal(first.result.postflight.postflight_verified, true);
  assert.equal(first.result.postflight.source_checkpoint_id, SOURCE_CHECKPOINT.checkpoint_id);
  assert.equal(first.postflight.postflight_verified, true);
  assert.equal(replay.deduplicated, true);
  assert.equal(activationOptions.expiresAtUnixMs, activation.expires_at_unix_ms);
  assert.deepEqual(prepareOptions.sourceCheckpoint, SOURCE_CHECKPOINT);
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
      prepareCodeActivation: async ({ operationId }) => {
        events.push('prepare');
        return { ...safeLifecycle({ operationId }), fenced: true, fence_operation_id: operationId };
      },
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
    recoveryRunningRevision: OLD,
    spawnElectronUi: async () => {}
  });
  const activation = request('electron_ui');
  assert.equal((await manager.activate(activation)).state, 'accepted');
  const oldRegistration = await manager.registerUi({
    instance_id: 'electron-ui-old-0001', pid: process.pid, revision: OLD, started_at_unix_ms: Date.now()
  });
  assert.equal(oldRegistration.restart_required, true);
  assert.equal(oldRegistration.expires_at_unix_ms, activation.expires_at_unix_ms);
  const newRegistration = await manager.registerUi({
    instance_id: 'electron-ui-new-0001', pid: process.pid, revision: NEXT, started_at_unix_ms: Date.now()
  });
  assert.equal(newRegistration.restart_required, false);
  assert.equal(newRegistration.activation.state, 'completed');
  assert.equal(manager.status(activation.operation_id).result.health_verified, true);
  assert.equal(manager.status(activation.operation_id).result.postflight.postflight_verified, true);
  assert.equal(manager.status(activation.operation_id).postflight.source_checkpoint_id, SOURCE_CHECKPOINT.checkpoint_id);
});

test('Recovery Host activation prepares MCP continuity before scheduling a fixed handoff', async (t) => {
  const paths = fixture(t);
  const events = [];
  let replacementOptions = null;
  const manager = new RecoveryActivation({
    paths,
    revisions: revisions(),
    orchestrator: orchestrator({
      prepareCodeActivation: async ({ operationId }) => {
        events.push('preflight');
        return { ...safeLifecycle({ operationId }), fenced: true, fence_operation_id: operationId };
      }
    }),
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
