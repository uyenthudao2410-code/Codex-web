const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { EventEmitter } = require('node:events');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { ActivationEpochStore } = require('../electron/services/activationEpoch');
const {
  FullCleanActivation,
  CANONICAL_LEDGER_CENSUS_TIMEOUT_MS,
  CANONICAL_LEDGER_CENSUS_DISCOVERY_TIMEOUT_MS,
  CANONICAL_LEDGER_CENSUS_CLEANUP_TIMEOUT_MS,
  canonicalLedgerCensus,
  canonicalLedgerCensusFailure,
  summarizeCensus,
  oneShotCensus,
  heldCensus,
  canonicalProjectionRebuildSha256,
  validateProjectionRebuildGate,
  validateConnectorReadyGate,
  reusablePendingProjectionObservation
} = require('../electron/services/fullCleanActivation');
const { RecoveryHost } = require('../electron/services/recoveryHost');
const { RuntimeOrchestrator } = require('../electron/services/runtimeOrchestrator');
const { observeProcessIdentity } = require('../electron/services/processIdentity');
const { tunnelFingerprint } = require('../electron/services/tunnelService');
const { readControlPlaneRouteEvidence } = require('../electron/services/controlPlaneRouteEvidence');

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

function acceptedSourceCheckpoint() {
  return {
    checkpoint_id: id('checkpoint', '0001'),
    run_id: id('run', '0001'),
    wave_id: id('wave', '0001'),
    proof_fingerprint: 'a'.repeat(64),
    git_head: 'b'.repeat(40)
  };
}

function epochStore(paths) {
  return new ActivationEpochStore({ paths, now: () => 1_700_000_000_000 });
}

function codedError(code, message = code) {
  return Object.assign(new Error(message), { code });
}

test('canonical ledger census keeps a bounded cold-snapshot budget and classifies timeout causes', () => {
  assert.equal(CANONICAL_LEDGER_CENSUS_TIMEOUT_MS, 30_000);
  assert.equal(CANONICAL_LEDGER_CENSUS_DISCOVERY_TIMEOUT_MS, 5_000);
  assert.equal(CANONICAL_LEDGER_CENSUS_CLEANUP_TIMEOUT_MS, 5_000);
  const nativeTimeout = Object.assign(new Error('Command failed'), { killed: true, signal: 'SIGTERM' });
  const classified = canonicalLedgerCensusFailure(nativeTimeout);
  assert.equal(classified.code, 'CANONICAL_LEDGER_CENSUS_TIMEOUT');
  assert.equal(classified.timedOut, true);
  assert.equal(Object.hasOwn(classified, 'cause'), false);

  const lockFailure = canonicalLedgerCensusFailure(Object.assign(new Error('helper failed'), {
    stderr: 'activation ledger census failed: RuntimeError: ACTIVATION_LEDGER_CENSUS_LOCK_TIMEOUT secret-output'
  }));
  assert.equal(lockFailure.code, 'ACTIVATION_LEDGER_CENSUS_LOCK_TIMEOUT');
  assert.equal(JSON.stringify(lockFailure).includes('secret-output'), false);

  const ordinaryFailure = codedError('ENOENT');
  const sanitized = canonicalLedgerCensusFailure(ordinaryFailure);
  assert.notEqual(sanitized, ordinaryFailure);
  assert.equal(sanitized.code, 'ENOENT');
  assert.equal(Object.hasOwn(sanitized, 'stdout'), false);
  assert.equal(Object.hasOwn(sanitized, 'stderr'), false);
});

test('canonical ledger census gives Python discovery one five-second budget and preserves its typed timeout', async (t) => {
  const { root, paths } = fixture(t);
  const ledgerPath = path.join(root, '.coding-tools', 'orchestration', 'ledger.sqlite3');
  const helperPath = path.join(
    paths.resourcesRoot(),
    'coding-tools-mcp',
    'coding_tools_mcp',
    'activation_ledger_census.py'
  );
  fs.mkdirSync(path.dirname(ledgerPath), { recursive: true });
  fs.mkdirSync(path.dirname(helperPath), { recursive: true });
  fs.writeFileSync(ledgerPath, 'fixture', 'utf8');
  fs.writeFileSync(helperPath, '# fixture\n', 'utf8');
  let observedOptions = null;

  await assert.rejects(
    canonicalLedgerCensus({
      paths,
      workspace: root,
      pythonStatusFn: async (_paths, options) => {
        observedOptions = options;
        throw Object.assign(new Error('discovery deadline reached'), {
          code: 'PYTHON_DISCOVERY_TIMEOUT',
          stderr: 'must-not-leak'
        });
      }
    }),
    (error) => {
      assert.equal(error.code, 'PYTHON_DISCOVERY_TIMEOUT');
      assert.equal(Object.hasOwn(error, 'stderr'), false);
      assert.equal(JSON.stringify(error).includes('must-not-leak'), false);
      return true;
    }
  );
  assert.deepEqual(observedOptions, { budgetMs: 5_000 });
});

class FakeCensusChild extends EventEmitter {
  constructor(onKill = null) {
    super();
    this.stdout = new EventEmitter();
    this.stderr = new EventEmitter();
    this.stdout.setEncoding = () => {};
    this.stderr.setEncoding = () => {};
    this.stdin = { end() {} };
    this.exitCode = null;
    this.signalCode = null;
    this.onKill = onKill;
  }
  kill() {
    return this.onKill?.(this) ?? true;
  }
}

test('one-shot canonical census timeout waits for owned child exit before settling', { timeout: 2000 }, async () => {
  let settled = false;
  const pending = oneShotCensus('fake-census', [], {
    cwd: process.cwd(),
    env: {},
    timeoutMs: 5,
    cleanupTimeoutMs: 200,
    spawnFn: () => new FakeCensusChild((owned) => {
      setTimeout(() => {
        owned.exitCode = 1;
        owned.signalCode = 'SIGTERM';
        owned.emit('close', 1, 'SIGTERM');
      }, 45);
      return true;
    })
  }).finally(() => { settled = true; });

  await new Promise((resolve) => setTimeout(resolve, 20));
  assert.equal(settled, false, 'one-shot census timeout must await owned child close/exit');
  await assert.rejects(pending, (error) => {
    assert.equal(error.code, 'CANONICAL_LEDGER_CENSUS_TIMEOUT');
    assert.equal(error.timedOut, true);
    assert.equal(error.cleanupConfirmed, true);
    assert.equal(error.cleanupOutcome, 'confirmed');
    assert.equal(error.cleanupBudgetMs, 200);
    return true;
  });
});

test('one-shot canonical census fails closed when owned child cleanup is unconfirmed', { timeout: 2000 }, async () => {
  await assert.rejects(
    oneShotCensus('fake-stuck-census', [], {
      cwd: process.cwd(),
      env: {},
      timeoutMs: 5,
      cleanupTimeoutMs: 15,
      spawnFn: () => new FakeCensusChild(() => true)
    }),
    (error) => {
      assert.equal(error.code, 'CANONICAL_LEDGER_CENSUS_CLEANUP_UNCERTAIN');
      assert.equal(error.cleanupConfirmed, false);
      assert.equal(error.cleanupOutcome, 'unconfirmed');
      assert.equal(error.cleanupBudgetMs, 15);
      return true;
    }
  );
});

test('one-shot canonical census keeps lock timeout distinct and does not leak stderr', async () => {
  const secret = 'SECRET-ONE-SHOT-CENSUS-OUTPUT';
  await assert.rejects(
    oneShotCensus('fake-lock-timeout', [], {
      cwd: process.cwd(),
      env: {},
      timeoutMs: 200,
      cleanupTimeoutMs: 15,
      spawnFn: () => {
        const child = new FakeCensusChild();
        queueMicrotask(() => {
          child.stderr.emit('data', `ACTIVATION_LEDGER_CENSUS_LOCK_TIMEOUT ${secret}`);
          child.exitCode = 1;
          child.emit('close', 1, null);
        });
        return child;
      }
    }),
    (error) => {
      assert.equal(error.code, 'ACTIVATION_LEDGER_CENSUS_LOCK_TIMEOUT');
      assert.equal(error.exit_code, 1);
      assert.equal(JSON.stringify(error).includes(secret), false);
      return true;
    }
  );
});

test('held canonical census timeout waits for owned child exit before settling', { timeout: 2000 }, async () => {
  let settled = false;
  const pending = heldCensus('fake-census', [], {
    cwd: process.cwd(),
    env: {},
    timeoutMs: 5,
    cleanupTimeoutMs: 200,
    spawnFn: () => new FakeCensusChild((owned) => {
      setTimeout(() => {
        owned.exitCode = 1;
        owned.signalCode = 'SIGTERM';
        owned.emit('close', 1, 'SIGTERM');
      }, 45);
      return true;
    })
  }).finally(() => { settled = true; });

  await new Promise((resolve) => setTimeout(resolve, 20));
  assert.equal(settled, false, 'held census timeout must await owned child close/exit');
  await assert.rejects(pending, (error) => {
    assert.equal(error.code, 'CANONICAL_LEDGER_CENSUS_TIMEOUT');
    assert.equal(error.timedOut, true);
    assert.equal(error.cleanupConfirmed, true);
    assert.equal(error.cleanupOutcome, 'confirmed');
    assert.equal(error.cleanupBudgetMs, 200);
    return true;
  });
});

test('held canonical census fails closed when owned child cleanup is unconfirmed', { timeout: 2000 }, async () => {
  await assert.rejects(
    heldCensus('fake-stuck-census', [], {
      cwd: process.cwd(),
      env: {},
      timeoutMs: 5,
      cleanupTimeoutMs: 15,
      spawnFn: () => new FakeCensusChild(() => true)
    }),
    (error) => {
      assert.equal(error.code, 'CANONICAL_LEDGER_CENSUS_CLEANUP_UNCERTAIN');
      assert.equal(error.cleanupConfirmed, false);
      assert.equal(error.cleanupOutcome, 'unconfirmed');
      assert.equal(error.cleanupBudgetMs, 15);
      return true;
    }
  );
});

test('held canonical census keeps lock timeout distinct and does not leak stderr', async () => {
  const secret = 'SECRET-CENSUS-PROCESS-OUTPUT';
  await assert.rejects(
    heldCensus('fake-lock-timeout', [], {
      cwd: process.cwd(),
      env: {},
      timeoutMs: 200,
      cleanupTimeoutMs: 15,
      spawnFn: () => {
        const child = new FakeCensusChild();
        queueMicrotask(() => {
          child.stderr.emit('data', `activation ledger census failed: ACTIVATION_LEDGER_CENSUS_LOCK_TIMEOUT ${secret}`);
          child.exitCode = 1;
          child.emit('exit', 1, null);
        });
        return child;
      }
    }),
    (error) => {
      assert.equal(error.code, 'ACTIVATION_LEDGER_CENSUS_LOCK_TIMEOUT');
      assert.equal(error.exit_code, 1);
      assert.equal(JSON.stringify(error).includes(secret), false);
      assert.equal(Object.hasOwn(error, 'stderr'), false);
      return true;
    }
  );
});

test('Recovery Host bootstrap failure receipt retains a typed census cause without process output', (t) => {
  const { paths } = fixture(t);
  const operationId = id('bootstrap-census-timeout', '0001');
  const host = Object.create(RecoveryHost.prototype);
  host.paths = paths;
  host.bootstrap = { operation_id: operationId };
  host.bootstrapActivation = null;
  host.recordBootstrapFailure(Object.assign(new Error('Canonical ledger census was unavailable.'), {
    code: 'ORCHESTRATION_STATE_UNCERTAIN',
    details: {
      cause_code: 'CANONICAL_LEDGER_CENSUS_TIMEOUT',
      stderr: 'must not persist process output'
    }
  }));

  const receipt = JSON.parse(fs.readFileSync(paths.recoveryHostBootstrapResultFile(operationId), 'utf8'));
  assert.deepEqual(receipt.error.details, { cause_code: 'CANONICAL_LEDGER_CENSUS_TIMEOUT' });
  assert.equal(JSON.stringify(receipt).includes('must not persist process output'), false);
});

test('pending activation census replaces stale durable component evidence without opening admission', (t) => {
  const { paths } = fixture(t);
  const store = epochStore(paths);
  const activationEpochId = id('activation-pending-census', '0001');
  const operationId = id('operation-pending-census', '0001');
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
    epochStore: store
  });
  const census = {
    pass: false,
    verified: false,
    activation_epoch_id: activationEpochId,
    tunnel_health_verified: true,
    recovery_plane_verified: true,
    connector_validation: { valid: false, reasons: ['CURRENT_CONTRACT_NOT_REDISCOVERED'] },
    reason: 'UPDATE_INCOMPLETE'
  };

  const pending = activation.recordPendingCensus(activationEpochId, census);

  assert.equal(pending.state, 'VERIFYING');
  assert.equal(pending.admission_state, 'CLOSED');
  assert.equal(pending.ready_commit_digest, null);
  assert.deepEqual(pending.verification, census);

  const passingCandidate = activation.recordPendingCensus(activationEpochId, {
    ...census,
    pass: true,
    verified: true,
    connector_validation: { valid: true, reasons: [] },
    reason: null
  });
  assert.equal(passingCandidate.state, 'VERIFYING');
  assert.equal(passingCandidate.admission_state, 'CLOSED');
  assert.equal(passingCandidate.ready_commit_digest, null);
  assert.equal(passingCandidate.verification.pass, true,
    'a passing candidate remains evidence-only until finalize independently commits it');
});

test('pending census advances only STARTING and refreshes VERIFYING without mutating coordinator-owned states', (t) => {
  const { paths } = fixture(t);
  const activationEpochId = id('activation-pending-state-gate', '0001');
  const census = {
    pass: false,
    activation_epoch_id: activationEpochId,
    reason: 'UPDATE_INCOMPLETE'
  };

  for (const state of ['STARTING', 'VERIFYING']) {
    let updateCalls = 0;
    const current = {
      activation_epoch_id: activationEpochId,
      state,
      admission_state: 'CLOSED',
      verification: { previous: true }
    };
    const activation = new FullCleanActivation({
      paths,
      settings: { load: () => ({}) },
      orchestrator: {},
      epochStore: {
        current: () => current,
        update: (_epochId, next) => {
          updateCalls += 1;
          Object.assign(current, next);
          return current;
        }
      }
    });

    const next = activation.recordPendingCensus(activationEpochId, census);
    assert.equal(updateCalls, 1, `${state} must persist exactly one census refresh`);
    assert.equal(next.state, 'VERIFYING');
    assert.deepEqual(next.verification, census);
    assert.equal(next.admission_state, 'CLOSED');
  }

  for (const state of ['PREPARING', 'ADMISSION_CLOSED', 'FROZEN', 'STOPPING', 'HANDOFF']) {
    let updateCalls = 0;
    const current = {
      activation_epoch_id: activationEpochId,
      state,
      admission_state: 'CLOSED',
      reason: 'preserve-me',
      verification: { previous: true }
    };
    const before = structuredClone(current);
    const activation = new FullCleanActivation({
      paths,
      settings: { load: () => ({}) },
      orchestrator: {},
      epochStore: {
        current: () => current,
        update: () => {
          updateCalls += 1;
          throw new Error('forbidden state must not reach the durable update');
        }
      }
    });

    assert.throws(
      () => activation.recordPendingCensus(activationEpochId, census),
      (error) => error?.code === 'ACTIVATION_EPOCH_STATE_INVALID'
        && error?.details?.state === state
    );
    assert.equal(updateCalls, 0, `${state} must fail before durable mutation`);
    assert.deepEqual(current, before);
  }
});

function projectionSnapshot() {
  return {
    backup_api_copy: true,
    immutable: true,
    query_only: true,
    integrity_check: ['ok'],
    foreign_key_check_rows: 0,
    sha256: '1'.repeat(64),
    logical_sha256: '2'.repeat(64)
  };
}

test('checkpoint-bound fresh activation observation forwards only explicit durable acceptance-pending policy', async (t) => {
  const { root, paths } = fixture(t);
  const sourceCheckpoint = acceptedSourceCheckpoint();
  const operationId = id('operation-policy-propagation', '1001');
  const calls = [];
  const coordinator = new FullCleanActivation({
    paths,
    settings: { load: () => ({ workspace: root }) },
    orchestrator: {
      async verifyCodeActivation(...args) {
        calls.push(args);
        return {
          safe: true,
          code: 'READY',
          reason: 'idle',
          operation_id: operationId,
          workspace: root,
          fenced: false,
          fence_operation_id: null,
          counts: {
            active_tool_calls: 0,
            active_commands: 0,
            starting_commands: 0,
            active_background_operations: 0,
            active_managed_processes: 0,
            foreign_heavy_processes: 0,
            active_agent_lanes: 0,
            threshold_sensitive_stale_candidates: 0,
            owned_codex_sidecar_residues: 0
          },
          source_checkpoint: { ok: true, code: 'ACTIVATABLE', ...sourceCheckpoint },
          lifecycle: {
            snapshot: projectionSnapshot(),
            projection: {},
            projection_classification: 'CHECKPOINTED',
            unexplained_active_runs: 0,
            unbound_live_resource_residues: 0
          }
        };
      }
    },
    now: () => 1_700_000_000_000
  });

  for (const metadata of [
    { allow_acceptance_pending: true },
    { allow_acceptance_pending: false },
    undefined
  ]) {
    const observation = await coordinator._freshActivationObservation({
      operation_id: operationId,
      source_checkpoint: sourceCheckpoint,
      ...(metadata ? { metadata } : {})
    });
    assert.equal(observation.lifecycle_decision.clean, true);
  }

  assert.deepEqual(calls.map((args) => args.slice(0, 2)), [
    [operationId, sourceCheckpoint],
    [operationId, sourceCheckpoint],
    [operationId, sourceCheckpoint]
  ]);
  assert.deepEqual(calls.map((args) => args[2]), [true, false, false]);
});

function projectionReceipt(root, overrides = {}) {
  const completedAtUnixMs = Object.hasOwn(overrides, 'completed_at_unix_ms')
    ? overrides.completed_at_unix_ms : 1_700_000_000_000;
  const receipt = {
    schema_version: 2,
    kind: 'coding_tools_mcp_projection_rebuild',
    activation_epoch_id: id('activation-projection', '1001'),
    process_instance_id: id('mcp-process', '1001'),
    server_instance_id: id('mcp-server', '1001'),
    workspace: root,
    ledger_snapshot_sha256: '1'.repeat(64),
    ledger_logical_sha256: '2'.repeat(64),
    ledger_integrity: {
      backup_api_copy: true,
      immutable: true,
      query_only: true,
      integrity_check: ['ok'],
      foreign_key_check_rows: 0
    },
    projection_classification: 'CHECKPOINTED',
    projection: {
      run_id: id('run-projection', '1001'),
      wave_id: id('wave-projection', '1001'),
      orchestration_state: 'CHECKPOINTED',
      mode: 'global',
      context_count: 0,
      contextual_sha256: ''
    },
    completed_at: new Date(completedAtUnixMs).toISOString(),
    completed_at_unix_ms: completedAtUnixMs,
    reconciled: true,
    ...overrides
  };
  receipt.projection = {
    run_id: id('run-projection', '1001'),
    wave_id: id('wave-projection', '1001'),
    orchestration_state: 'CHECKPOINTED',
    mode: 'global',
    context_count: 0,
    contextual_sha256: '',
    ...(overrides.projection || {})
  };
  delete receipt.integrity_sha256;
  receipt.integrity_sha256 = canonicalProjectionRebuildSha256(receipt);
  return receipt;
}

function projectionWrapper(receipt, overrides = {}) {
  return {
    current: true,
    receipt,
    validation: {
      valid: true,
      code: 'READY',
      reasons: [],
      projection_classification: receipt?.projection_classification || null
    },
    ...overrides
  };
}

test('pending projection reuse requires every admission-closed identity and immutable-ledger gate', () => {
  const root = path.resolve('pending-projection-reuse-workspace');
  const receipt = projectionReceipt(root);
  const record = {
    activation_epoch_id: receipt.activation_epoch_id,
    state: 'VERIFYING',
    admission_state: 'CLOSED',
    verification: {
      projection_rebuild_verified: true,
      projection_rebuild_receipt: receipt,
      connector_validation: { valid: false, reasons: ['CURRENT_CONTRACT_NOT_REDISCOVERED'] },
      process_identity_verified: true,
      workspace_matches: true,
      device_matches: true,
      revision_matches: true,
      recovery_host_revision_matches: true,
      recovery_host_epoch_matches: true,
      ui_verified: true,
      recovery_plane_verified: true,
      epoch_matches: true,
      lifecycle_decision: { safe: true, code: 'READY' }
    }
  };

  const reusable = reusablePendingProjectionObservation(record);
  assert.ok(reusable);
  assert.equal(reusable.reused_pending_projection, true);
  assert.equal(reusable.projection_rebuild_receipt, receipt);
  assert.equal(reusable.snapshot.sha256, receipt.ledger_snapshot_sha256);
  assert.equal(reusable.snapshot.logical_sha256, receipt.ledger_logical_sha256);

  const rejected = [
    ['admission is open', (value) => { value.admission_state = 'OPEN'; }],
    ['epoch is not verifying', (value) => { value.state = 'READY_COMMITTED'; }],
    ['projection was not verified', (value) => { value.verification.projection_rebuild_verified = false; }],
    ['connector is already valid', (value) => { value.verification.connector_validation.valid = true; }],
    ['MCP identity changed', (value) => { value.verification.process_identity_verified = false; }],
    ['workspace changed', (value) => { value.verification.workspace_matches = false; }],
    ['device changed', (value) => { value.verification.device_matches = false; }],
    ['revision changed', (value) => { value.verification.revision_matches = false; }],
    ['Recovery Host revision changed', (value) => { value.verification.recovery_host_revision_matches = false; }],
    ['Recovery Host epoch changed', (value) => { value.verification.recovery_host_epoch_matches = false; }],
    ['UI is not verified', (value) => { value.verification.ui_verified = false; }],
    ['Recovery Plane is not verified', (value) => { value.verification.recovery_plane_verified = false; }],
    ['component epoch changed', (value) => { value.verification.epoch_matches = false; }],
    ['receipt belongs to another epoch', (value) => {
      value.verification.projection_rebuild_receipt.activation_epoch_id = id('activation-projection-retired', '1001');
    }],
    ['ledger snapshot is not immutable', (value) => {
      value.verification.projection_rebuild_receipt.ledger_integrity.immutable = false;
    }],
    ['ledger snapshot hash is invalid', (value) => {
      value.verification.projection_rebuild_receipt.ledger_snapshot_sha256 = 'not-a-sha256';
    }]
  ];
  for (const [name, mutate] of rejected) {
    const candidate = structuredClone(record);
    mutate(candidate);
    assert.equal(reusablePendingProjectionObservation(candidate), null, name);
  }
});

test('pending projection reuse permits a strict discovered candidate for finalize without a second preflight', () => {
  const root = path.resolve('pending-projection-strict-workspace');
  const receipt = projectionReceipt(root);
  const record = {
    activation_epoch_id: receipt.activation_epoch_id,
    state: 'VERIFYING',
    admission_state: 'CLOSED',
    verification: {
      projection_rebuild_verified: true,
      projection_rebuild_receipt: receipt,
      connector_validation: {
        valid: true,
        freshness_mode: 'current_process_discovery',
        rediscovered_at: '2026-08-29T00:00:00.000Z'
      },
      process_identity_verified: true,
      workspace_matches: true,
      device_matches: true,
      revision_matches: true,
      recovery_host_revision_matches: true,
      recovery_host_epoch_matches: true,
      ui_verified: true,
      recovery_plane_verified: true,
      epoch_matches: true,
      lifecycle_decision: { safe: true, code: 'READY' }
    }
  };

  const reusable = reusablePendingProjectionObservation(record);

  assert.ok(reusable);
  assert.equal(reusable.reused_pending_projection, true);
  assert.equal(reusable.projection_rebuild_receipt, receipt);
});

test('pending projection reuse permits an exact compatible bootstrap candidate for finalize', () => {
  const root = path.resolve('pending-projection-compatible-workspace');
  const receipt = projectionReceipt(root);
  const record = {
    activation_epoch_id: receipt.activation_epoch_id,
    state: 'VERIFYING',
    admission_state: 'CLOSED',
    verification: {
      projection_rebuild_verified: true,
      projection_rebuild_receipt: receipt,
      connector_validation: {
        valid: true,
        freshness_mode: 'compatible_activation_bootstrap',
        rediscovered_at: null,
        compatibility_acknowledged_at: '2026-08-29T00:00:00.000Z'
      },
      process_identity_verified: true,
      workspace_matches: true,
      device_matches: true,
      revision_matches: true,
      recovery_host_revision_matches: true,
      recovery_host_epoch_matches: true,
      ui_verified: true,
      recovery_plane_verified: true,
      epoch_matches: true,
      lifecycle_decision: { safe: true, code: 'READY' }
    }
  };

  const reusable = reusablePendingProjectionObservation(record);

  assert.ok(reusable);
  assert.equal(reusable.reused_pending_projection, true);
  assert.equal(reusable.projection_rebuild_receipt, receipt);
});

test('committed projection reuse is explicit and remains admission-closed', () => {
  const root = path.resolve('committed-projection-reuse-workspace');
  const receipt = projectionReceipt(root);
  const finalCensus = {
    pass: true,
    activation_epoch_id: receipt.activation_epoch_id,
    projection_rebuild_verified: true,
    projection_rebuild_receipt: receipt,
    connector_validation: {
      valid: true,
      freshness_mode: 'current_process_discovery',
      rediscovered_at: '2026-08-29T00:00:00.000Z'
    },
    process_identity_verified: true,
    workspace_matches: true,
    device_matches: true,
    revision_matches: true,
    recovery_host_revision_matches: true,
    recovery_host_epoch_matches: true,
    ui_verified: true,
    recovery_plane_verified: true,
    epoch_matches: true,
    lifecycle_decision: { safe: true, code: 'READY' }
  };
  const record = {
    activation_epoch_id: receipt.activation_epoch_id,
    state: 'READY_COMMITTED',
    admission_state: 'CLOSED',
    verification: { final_census: finalCensus }
  };

  assert.equal(reusablePendingProjectionObservation(record), null,
    'ordinary callers cannot reuse terminal-commit evidence');
  const reusable = reusablePendingProjectionObservation(record, { allowCommitted: true });
  assert.ok(reusable);
  assert.equal(reusable.reused_pending_projection, true);
  assert.equal(reusable.projection_rebuild_receipt, receipt);
});

function projectionGateInput(root, {
  preflightReceipt = projectionReceipt(root),
  healthReceipt = preflightReceipt,
  preflightWrapper = null,
  healthWrapper = null,
  nowUnixMs = 1_700_000_000_000
} = {}) {
  return {
    preflight: {
      snapshot: projectionSnapshot(),
      projection_classification: preflightReceipt?.projection_classification || null,
      projection: preflightReceipt ? {
        classification: preflightReceipt.projection_classification,
        ...preflightReceipt.projection
      } : {},
      projection_rebuild: preflightWrapper || projectionWrapper(preflightReceipt),
      projection_rebuild_receipt: preflightReceipt
    },
    health: {
      projection_rebuild: healthWrapper || projectionWrapper(healthReceipt)
    },
    expected: {
      activationEpochId: id('activation-projection', '1001'),
      processInstanceId: id('mcp-process', '1001'),
      serverInstanceId: id('mcp-server', '1001'),
      workspace: root,
      ledgerSnapshot: projectionSnapshot()
    },
    nowUnixMs
  };
}

function finalizeTransactionFixture(t, {
  commitReadyError = null,
  complete = null,
  health = null,
  readyError = null,
  close = null,
  actionFinish = null
} = {}) {
  const { root, paths } = fixture(t);
  const activationEpochId = id('activation-transaction', '1001');
  const operationId = id('activation-operation', '1001');
  const readyCommitDigest = 'd'.repeat(64);
  const expiresAtUnixMs = 1_700_000_120_000;
  const calls = [];
  let healthCallCount = 0;
  let record = {
    activation_epoch_id: activationEpochId,
    operation_id: operationId,
    state: 'VERIFYING',
    admission_state: 'CLOSED',
    expires_at_unix_ms: expiresAtUnixMs,
    source_checkpoint: null,
    component_revisions: null,
    component_evidence: null,
    verification: null
  };
  const receipt = (admissionOpen, overrides = {}) => ({
    ok: true,
    activation_epoch_id: activationEpochId,
    ready_commit_digest: readyCommitDigest,
    expires_at_unix_ms: expiresAtUnixMs,
    admission_open: admissionOpen,
    ...overrides
  });
  const store = {
    current() { return record; },
    commitReady(epochIdValue, verification) {
      calls.push(['commitReady', epochIdValue]);
      if (commitReadyError) throw commitReadyError;
      record = {
        ...record,
        state: 'READY_COMMITTED',
        admission_state: 'CLOSED',
        ready_commit_digest: readyCommitDigest,
        verification
      };
      return record;
    },
    ready(epochIdValue, digest) {
      calls.push(['ready', epochIdValue, digest]);
      if (readyError) throw readyError;
      record = {
        ...record,
        state: 'READY',
        admission_state: 'OPEN',
        ready_commit_digest: digest
      };
      return record;
    },
    fail(epochIdValue, failure) {
      calls.push(['fail', epochIdValue, failure?.code || null]);
      record = {
        ...record,
        state: 'FAILED',
        admission_state: 'CLOSED',
        error: { code: failure?.code || 'ACTIVATION_EPOCH_FAILED' }
      };
      return record;
    }
  };
  const orchestrator = {
    async completeActivationEpoch(epochIdValue, digest) {
      calls.push(['completeActivationEpoch', epochIdValue, digest]);
      if (complete) return complete({ epochId: epochIdValue, digest, receipt });
      return receipt(true);
    },
    async currentMcpHealth() {
      healthCallCount += 1;
      calls.push(['currentMcpHealth', healthCallCount]);
      return health ? health({ call: healthCallCount, receipt }) : null;
    },
    async closeActivationEpoch(epochIdValue, digest) {
      calls.push(['closeActivationEpoch', epochIdValue, digest]);
      if (close) return close({ epochId: epochIdValue, digest, receipt });
      return receipt(false);
    },
    async stop(options) {
      calls.push(['runtime.stop', options]);
      return true;
    }
  };
  const actionStore = actionFinish
    ? {
        get: () => ({ state: 'pending' }),
        finish(...args) {
          calls.push(['finishLinkedAction']);
          return actionFinish(...args);
        }
      }
    : null;
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: store,
    settings: { load: () => ({ workspace: root }) },
    orchestrator,
    actionStore,
    log: { error() {} },
    now: () => 1_700_000_000_000
  });
  coordinator.finalCensus = async (epochIdValue, options = {}) => {
    calls.push(['finalCensus', epochIdValue, options]);
    return { pass: true, activation_epoch_id: epochIdValue };
  };
  return {
    activationEpochId,
    calls,
    coordinator,
    current: () => record,
    expiresAtUnixMs,
    readyCommitDigest,
    receipt
  };
}

test('projection rebuild gate accepts only one exact current preflight and health receipt', () => {
  const root = path.resolve('projection-gate-workspace');
  const result = validateProjectionRebuildGate(projectionGateInput(root));

  assert.equal(result.valid, true);
  assert.equal(result.code, 'READY');
  assert.deepEqual(result.reasons, []);
  assert.equal(result.projection_classification, 'CHECKPOINTED');
});

test('projection rebuild gate accepts a ledger-bound contextual projection set without selecting a global run', () => {
  const root = path.resolve('projection-gate-contextual-workspace');
  const receipt = projectionReceipt(root, {
    projection_classification: 'CONTEXTUAL_PROJECTIONS',
    projection: {
      run_id: '',
      wave_id: '',
      orchestration_state: '',
      mode: 'contextual',
      context_count: 6,
      contextual_sha256: '9'.repeat(64)
    }
  });
  const result = validateProjectionRebuildGate(projectionGateInput(root, {
    preflightReceipt: receipt,
    healthReceipt: receipt
  }));

  assert.equal(result.valid, true);
  assert.equal(result.projection_classification, 'CONTEXTUAL_PROJECTIONS');
});

test('projection rebuild gate fails closed for identity, ledger, projection, timestamp, and wrapper drift', () => {
  const root = path.resolve('projection-gate-workspace');
  const base = projectionReceipt(root);
  const mutate = (changes) => projectionReceipt(root, changes);
  const tampered = structuredClone(base);
  tampered.process_instance_id = id('tampered-process', '1001');
  const crossObservation = projectionReceipt(root, {
    completed_at_unix_ms: base.completed_at_unix_ms + 1,
    completed_at: new Date(base.completed_at_unix_ms + 1).toISOString()
  });
  const cases = [
    {
      name: 'missing wrapper',
      input: { ...projectionGateInput(root), health: {} },
      reason: 'HEALTH_WRAPPER_MISSING'
    },
    {
      name: 'missing receipt',
      input: projectionGateInput(root, { healthWrapper: projectionWrapper(null) }),
      reason: 'HEALTH_RECEIPT_MISSING'
    },
    {
      name: 'wrong epoch',
      receipt: mutate({ activation_epoch_id: id('other-activation', '1001') }),
      reason: 'HEALTH_ACTIVATION_EPOCH_ID_MISMATCH'
    },
    {
      name: 'wrong process',
      receipt: mutate({ process_instance_id: id('other-process', '1001') }),
      reason: 'HEALTH_PROCESS_INSTANCE_ID_MISMATCH'
    },
    {
      name: 'wrong server',
      receipt: mutate({ server_instance_id: id('other-server', '1001') }),
      reason: 'HEALTH_SERVER_INSTANCE_ID_MISMATCH'
    },
    {
      name: 'wrong workspace',
      receipt: mutate({ workspace: path.join(root, 'other') }),
      reason: 'HEALTH_WORKSPACE_MISMATCH'
    },
    {
      name: 'physical ledger drift',
      receipt: mutate({ ledger_snapshot_sha256: '3'.repeat(64) }),
      reason: 'HEALTH_LEDGER_SNAPSHOT_SHA256_MISMATCH'
    },
    {
      name: 'logical ledger drift',
      receipt: mutate({ ledger_logical_sha256: '4'.repeat(64) }),
      reason: 'HEALTH_LEDGER_LOGICAL_SHA256_MISMATCH'
    },
    {
      name: 'invalid SQLite integrity',
      receipt: mutate({ ledger_integrity: { ...base.ledger_integrity, foreign_key_check_rows: 1 } }),
      reason: 'HEALTH_LEDGER_INTEGRITY_INVALID'
    },
    {
      name: 'projection drift',
      receipt: mutate({ projection_classification: 'PROJECTION_DRIFT' }),
      reason: 'HEALTH_PROJECTION_CLASSIFICATION_INVALID'
    },
    {
      name: 'not reconciled',
      receipt: mutate({ reconciled: false }),
      reason: 'HEALTH_RECONCILIATION_FLAG_INVALID'
    },
    {
      name: 'stale timestamp',
      receipt: mutate({
        completed_at_unix_ms: base.completed_at_unix_ms - (5 * 60 * 1000) - 1,
        completed_at: new Date(base.completed_at_unix_ms - (5 * 60 * 1000) - 1).toISOString()
      }),
      reason: 'HEALTH_RECEIPT_STALE'
    },
    {
      name: 'future timestamp',
      receipt: mutate({
        completed_at_unix_ms: base.completed_at_unix_ms + 1001,
        completed_at: new Date(base.completed_at_unix_ms + 1001).toISOString()
      }),
      reason: 'HEALTH_RECEIPT_FROM_FUTURE'
    },
    {
      name: 'tampered digest',
      receipt: tampered,
      reason: 'HEALTH_RECEIPT_INTEGRITY_INVALID'
    },
    {
      name: 'preflight and health observations differ',
      input: projectionGateInput(root, { preflightReceipt: base, healthReceipt: crossObservation }),
      reason: 'CROSS_OBSERVATION_RECEIPT_MISMATCH'
    }
  ];

  for (const item of cases) {
    const input = item.input || projectionGateInput(root, {
      preflightReceipt: item.receipt,
      healthReceipt: item.receipt
    });
    const result = validateProjectionRebuildGate(input);
    assert.equal(result.valid, false, item.name);
    assert.equal(result.code, 'UPDATE_INCOMPLETE', item.name);
    assert.ok(result.reasons.includes(item.reason), `${item.name}: ${result.reasons.join(', ')}`);
  }
});

test('connector gate binds ACK and rediscovery to the exact post-preflight health observation', () => {
  const nowUnixMs = 1_700_000_000_000;
  const contractSha256 = 'c'.repeat(64);
  const activationEpochId = id('activation-connector-gate', '1001');
  const processInstanceId = id('mcp-process-connector', '1001');
  const serverInstanceId = id('mcp-server-connector', '1001');
  const observedAt = new Date(nowUnixMs - 1000).toISOString();
  const health = {
    activation_epoch_id: activationEpochId,
    process_instance_id: processInstanceId,
    instance_id: serverInstanceId,
    tool_contract: { sha256: contractSha256 },
    connector_tool_discovery: {
      current_contract_observed: true,
      identity_source: 'attested_transport',
      attestation_verified: true,
      contract_sha256: contractSha256,
      observed_at: observedAt,
      process_instance_id: processInstanceId,
      server_instance_id: serverInstanceId,
      activation_epoch_id: activationEpochId
    }
  };
  const contractStatus = {
    available: true,
    currentSha256: contractSha256,
    acknowledgedSha256: contractSha256,
    rediscovered: true,
    rediscoveredSha256: contractSha256,
    rediscoveredAt: observedAt,
    refreshRequired: false,
    acknowledgementPending: false,
    contractChanged: false,
    contractState: 'CURRENT_ACKNOWLEDGED'
  };

  const ready = validateConnectorReadyGate({ health, contractStatus, nowUnixMs });
  assert.equal(ready.valid, true);
  assert.deepEqual(ready.reasons, []);

  const mixedProcessObservation = structuredClone(health);
  mixedProcessObservation.connector_tool_discovery.process_instance_id = id('retired-mcp-process', '1001');
  const mixedProcess = validateConnectorReadyGate({
    health: mixedProcessObservation,
    contractStatus,
    nowUnixMs
  });
  assert.equal(mixedProcess.valid, false);
  assert.ok(mixedProcess.reasons.includes('DISCOVERY_PROCESS_INSTANCE_ID_MISMATCH'));

  const mixedEpochObservation = structuredClone(health);
  mixedEpochObservation.connector_tool_discovery.activation_epoch_id = id('retired-activation-epoch', '1001');
  const mixedEpoch = validateConnectorReadyGate({ health: mixedEpochObservation, contractStatus, nowUnixMs });
  assert.equal(mixedEpoch.valid, false);
  assert.ok(mixedEpoch.reasons.includes('DISCOVERY_ACTIVATION_EPOCH_ID_MISMATCH'));

  const untrustedIdentityObservation = structuredClone(health);
  untrustedIdentityObservation.connector_tool_discovery.identity_source = 'explicit_headers';
  const untrustedIdentity = validateConnectorReadyGate({ health: untrustedIdentityObservation, contractStatus, nowUnixMs });
  assert.equal(untrustedIdentity.valid, false);
  assert.ok(untrustedIdentity.reasons.includes('DISCOVERY_IDENTITY_SOURCE_INVALID'));

  const staleAcknowledgement = validateConnectorReadyGate({
    health,
    contractStatus: { ...contractStatus, acknowledgedSha256: 'd'.repeat(64) },
    nowUnixMs
  });
  assert.equal(staleAcknowledgement.valid, false);
  assert.ok(staleAcknowledgement.reasons.includes('ACKNOWLEDGED_SHA256_MISMATCH'));
});

test('connector gate accepts only an acknowledged exact no-workspace compatibility bootstrap', () => {
  const nowUnixMs = 1_700_000_000_000;
  const activationEpochId = id('activation-compatible-gate', '1001');
  const contractSha256 = 'e'.repeat(64);
  const processInstanceId = id('mcp-process-compatible', '1001');
  const serverInstanceId = id('mcp-server-compatible', '1001');
  const observedAt = new Date(nowUnixMs - 1000).toISOString();
  const bootstrap = {
    observed: true,
    current_contract_contact: true,
    identity_source: 'attested_transport',
    attestation_verified: true,
    client_id: 'chatweb-compatible-client',
    client_type: 'chatweb',
    method: 'tools/call',
    tool_name: 'workspace_context',
    workspace_accessed: false,
    contract_sha256: contractSha256,
    activation_epoch_id: activationEpochId,
    process_instance_id: processInstanceId,
    server_instance_id: serverInstanceId,
    observed_at: observedAt
  };
  const health = {
    activation_epoch_id: activationEpochId,
    process_instance_id: processInstanceId,
    instance_id: serverInstanceId,
    tool_contract: { sha256: contractSha256 },
    connector_tool_discovery: null,
    connector_activation_bootstrap: bootstrap
  };
  const contractStatus = {
    available: true,
    currentSha256: contractSha256,
    acknowledgedSha256: contractSha256,
    rediscovered: false,
    rediscoveredSha256: '',
    rediscoveredAt: null,
    compatibilityAcknowledged: true,
    compatibilityAcknowledgedAt: observedAt,
    compatibilitySource: 'declared_exact_predecessor_activation_bootstrap',
    bootstrapCurrent: true,
    refreshRequired: false,
    acknowledgementPending: false,
    contractChanged: false,
    contractState: 'CURRENT_COMPATIBLE_ACKNOWLEDGED'
  };

  const ready = validateConnectorReadyGate({ health, contractStatus, nowUnixMs });
  assert.equal(ready.valid, true);
  assert.equal(ready.code, 'READY');
  assert.deepEqual(ready.reasons, []);
  assert.equal(ready.freshness_mode, 'compatible_activation_bootstrap');
  assert.equal(ready.rediscovered_at, null);
  assert.equal(ready.compatibility_acknowledged_at, observedAt);

  for (const [field, value, reason] of [
    ['identity_source', 'explicit_headers', 'COMPATIBILITY_BOOTSTRAP_IDENTITY_SOURCE_INVALID'],
    ['process_instance_id', id('retired-compatible-process', '1001'), 'COMPATIBILITY_BOOTSTRAP_PROCESS_INSTANCE_ID_MISMATCH'],
    ['server_instance_id', id('retired-compatible-server', '1001'), 'COMPATIBILITY_BOOTSTRAP_SERVER_INSTANCE_ID_MISMATCH'],
    ['activation_epoch_id', id('activation-compatible-retired', '1001'), 'COMPATIBILITY_BOOTSTRAP_ACTIVATION_EPOCH_ID_MISMATCH'],
    ['workspace_accessed', true, 'COMPATIBILITY_BOOTSTRAP_WORKSPACE_ACCESSED'],
    ['contract_sha256', 'f'.repeat(64), 'COMPATIBILITY_BOOTSTRAP_CONTRACT_SHA256_MISMATCH']
  ]) {
    const invalid = validateConnectorReadyGate({
      health: { ...health, connector_activation_bootstrap: { ...bootstrap, [field]: value } },
      contractStatus,
      nowUnixMs
    });
    assert.equal(invalid.valid, false, field);
    assert.ok(invalid.reasons.includes(reason), `${field}: ${invalid.reasons.join(', ')}`);
  }
});

test('final census rebuilds an ordinary no-checkpoint projection before health and gates READY on the exact receipt', async (t) => {
  const { root, paths } = fixture(t);
  const activationEpochId = id('activation-projection', '1001');
  const operationId = id('operation-projection', '1001');
  const processInstanceId = id('mcp-process', '1001');
  const serverInstanceId = id('mcp-server', '1001');
  const supervisorInstanceId = id('mcp-supervisor', '1001');
  const tunnelInstanceId = id('coding-tunnel', '1001');
  const recoveryHostInstanceId = id('recovery-host', '1001');
  const recoveryMcpInstanceId = id('recovery-mcp', '1001');
  const uiInstanceId = id('electron-ui', '1001');
  const deviceId = id('device', '1001');
  const revision = 'a'.repeat(64);
  let nowUnixMs = 1_700_000_000_000;
  const contractSha256 = 'c'.repeat(64);
  let connectorRediscoveredAt = new Date(nowUnixMs - 1000).toISOString();
  let connectorBootstrapObservedAt = new Date(nowUnixMs - 500).toISOString();
  let connectorEvidenceMode = 'discovery';
  let receipt = projectionReceipt(root, {
    projection_classification: 'NO_ACTIVE_PROJECTION',
    projection: { run_id: '', wave_id: '', orchestration_state: '', mode: 'global' }
  });
  let preflightWrapperCurrent = true;
  let wrapper = projectionWrapper(receipt, { current: preflightWrapperCurrent });
  const processStartToken = observeProcessIdentity(process.pid).process_start_token || '1';
  const recoveryServer = http.createServer((request, response) => {
    response.writeHead(200, { 'Content-Type': 'application/json' });
    response.end(JSON.stringify({
      ok: true,
      service: 'recovery-mcp',
      device_id: deviceId,
      device_instance_id: recoveryHostInstanceId,
      activation_epoch_id: activationEpochId,
      pid: process.pid,
      instance_id: recoveryMcpInstanceId
    }));
  });
  await new Promise((resolve) => recoveryServer.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise((resolve) => recoveryServer.close(resolve)));
  const recoveryMcpPort = recoveryServer.address().port;
  const settings = {
    workspace: root,
    mcpPort: 41001,
    healthPort: 41002,
    tunnelId: 'coding-tunnel-id',
    recoveryMcpPort,
    recoveryHealthPort: 41003,
    recoveryTunnelId: ''
  };
  fs.mkdirSync(path.dirname(paths.stateFile()), { recursive: true });
  fs.writeFileSync(paths.stateFile(), JSON.stringify({
    nativeInstanceId: supervisorInstanceId,
    nativePid: process.pid,
    nativeActivationEpochId: activationEpochId,
    nativeDeviceId: deviceId,
    nativeDeviceInstanceId: recoveryHostInstanceId,
    nativeCodeRevision: revision,
    tunnelInstanceId,
    tunnelPid: process.pid,
    tunnelActivationEpochId: activationEpochId,
    tunnelFingerprint: tunnelFingerprint(settings, deviceId, activationEpochId)
  }));
  fs.mkdirSync(path.dirname(paths.recoveryHostDescriptorFile()), { recursive: true });
  fs.writeFileSync(paths.recoveryHostDescriptorFile(), JSON.stringify({
    instance_id: recoveryHostInstanceId,
    owner_pid: process.pid,
    activation_epoch_id: activationEpochId,
    device_instance_id: recoveryHostInstanceId
  }));
  const store = epochStore(paths);
  store.create({
    activation_epoch_id: activationEpochId,
    operation_id: operationId,
    components: ['recovery_host', 'coding_mcp', 'electron_ui'],
    component_revisions: {
      recovery_host: { disk_revision: revision },
      coding_mcp: { disk_revision: revision },
      electron_ui: { disk_revision: revision }
    },
    component_evidence: {
      recovery_host: { instance_id: id('old-recovery-host', '1001'), pid: process.pid + 1 },
      coding_mcp: {
        process_instance_id: id('old-mcp-process', '1001'),
        server_instance_id: id('old-mcp-server', '1001'),
        supervisor_instance_id: id('old-mcp-supervisor', '1001'),
        pid: process.pid + 2
      },
      coding_tunnel: { instance_id: id('old-coding-tunnel', '1001'), pid: process.pid + 3 },
      recovery_mcp: { instance_id: id('old-recovery-mcp', '1001'), pid: process.pid + 4 },
      electron_ui: {
        instance_id: id('old-electron-ui', '1001'),
        pid: process.pid + 5,
        process_start_token: '1'
      }
    }
  });
  const calls = [];
  let connectorAcknowledged = false;
  let tunnelStatusCalls = 0;
  const tunnelWaits = [];
  const orchestrator = {
    async lightweightSnapshot() {
      return {
        mcpRunning: true,
        tunnelRunning: true,
        connectorRefreshRequired: false,
        connectorRediscovered: true,
        connectorAcknowledgementPending: false,
        codeRevision: {
          codingMcp: { disk_revision: revision, running_revision: revision },
          electronUi: { disk_revision: revision, running_revision: revision }
        }
      };
    },
    async inspectCodeActivation() {
      calls.push('preflight');
      receipt = projectionReceipt(root, {
        projection_classification: 'NO_ACTIVE_PROJECTION',
        projection: { run_id: '', wave_id: '', orchestration_state: '', mode: 'global' },
        completed_at_unix_ms: nowUnixMs
      });
      wrapper = projectionWrapper(receipt, { current: preflightWrapperCurrent });
      return {
        safe: true,
        code: 'READY',
        reason: 'idle',
        workspace: root,
        fenced: false,
        fence_operation_id: null,
        counts: {
          active_tool_calls: 0,
          active_commands: 0,
          starting_commands: 0,
          active_background_operations: 0,
          active_managed_processes: 0,
          foreign_heavy_processes: 0,
          active_agent_lanes: 0,
          threshold_sensitive_stale_candidates: 0,
          owned_codex_sidecar_residues: 0
        },
        lifecycle: {
          snapshot: projectionSnapshot(),
          projection: {
            available: true,
            classification: 'NO_ACTIVE_PROJECTION',
            run_id: '',
            wave_id: '',
            orchestration_state: '',
            mode: 'global',
            context_count: 0,
            contextual_sha256: ''
          },
          projection_classification: 'NO_ACTIVE_PROJECTION',
          projection_rebuild: wrapper,
          projection_rebuild_receipt: receipt,
          unexplained_active_runs: 0,
          unbound_live_resource_residues: 0
        }
      };
    },
    async currentMcpHealth() {
      calls.push('health');
      return {
        ready: true,
        activation_epoch_id: activationEpochId,
        process_instance_id: processInstanceId,
        instance_id: serverInstanceId,
        workspace: root,
        device_id: deviceId,
        device_instance_id: recoveryHostInstanceId,
        code_revision: revision,
        tool_contract: { sha256: contractSha256 },
        connector_tool_discovery: connectorEvidenceMode === 'discovery' ? {
          current_contract_observed: true,
          identity_source: 'attested_transport',
          attestation_verified: true,
          contract_sha256: contractSha256,
          observed_at: connectorRediscoveredAt,
          process_instance_id: processInstanceId,
          server_instance_id: serverInstanceId,
          activation_epoch_id: activationEpochId
        } : null,
        connector_activation_bootstrap: connectorEvidenceMode === 'compatibility' ? {
          current_contract_contact: true,
          identity_source: 'attested_transport',
          attestation_verified: true,
          client_id: 'chatweb-full-clean-compatible',
          client_type: 'chatweb',
          method: 'tools/call',
          tool_name: 'workspace_context',
          workspace_accessed: false,
          contract_sha256: contractSha256,
          observed_at: connectorBootstrapObservedAt,
          process_instance_id: processInstanceId,
          server_instance_id: serverInstanceId,
          activation_epoch_id: activationEpochId
        } : null,
        projection_rebuild: wrapper
      };
    },
    connectorContractStatus(toolContract, discovery, _contact, bootstrap) {
      if (connectorEvidenceMode === 'compatibility') {
        return {
          available: true,
          currentSha256: toolContract?.sha256 || '',
          acknowledgedSha256: connectorAcknowledged ? contractSha256 : 'd'.repeat(64),
          rediscovered: false,
          rediscoveredSha256: '',
          rediscoveredAt: null,
          bootstrapCurrent: Boolean(bootstrap),
          bootstrapObservedAt: bootstrap?.observed_at || null,
          compatibilityAcknowledged: connectorAcknowledged,
          compatibilityAcknowledgedAt: connectorAcknowledged ? bootstrap?.observed_at || null : null,
          compatibilitySource: 'declared_exact_predecessor_activation_bootstrap',
          refreshRequired: false,
          acknowledgementPending: !connectorAcknowledged,
          contractChanged: !connectorAcknowledged,
          contractState: connectorAcknowledged
            ? 'CURRENT_COMPATIBLE_ACKNOWLEDGED'
            : 'CHANGED_COMPATIBLE_NEEDS_ACK'
        };
      }
      return {
        available: true,
        currentSha256: toolContract?.sha256 || '',
        acknowledgedSha256: connectorAcknowledged ? contractSha256 : 'd'.repeat(64),
        rediscovered: discovery?.current_contract_observed === true,
        rediscoveredSha256: discovery?.contract_sha256 || '',
        rediscoveredAt: discovery?.observed_at || null,
        refreshRequired: false,
        acknowledgementPending: !connectorAcknowledged,
        contractChanged: !connectorAcknowledged,
        contractState: connectorAcknowledged ? 'CURRENT_ACKNOWLEDGED' : 'CHANGED_DISCOVERED_NEEDS_ACK'
      };
    },
    async acknowledgeExactConnectorDiscovery(health, options) {
      calls.push('connector-ack');
      assert.equal(health.process_instance_id, processInstanceId);
      assert.equal(health.instance_id, serverInstanceId);
      assert.equal(options.activationEpochId, activationEpochId);
      const evidence = connectorEvidenceMode === 'compatibility'
        ? health.connector_activation_bootstrap
        : health.connector_tool_discovery;
      if (evidence?.process_instance_id !== processInstanceId
        || evidence?.server_instance_id !== serverInstanceId) {
        throw codedError('CONNECTOR_CONTRACT_NOT_REDISCOVERED');
      }
      connectorAcknowledged = true;
      return this.connectorContractStatus(
        health.tool_contract,
        health.connector_tool_discovery,
        null,
        health.connector_activation_bootstrap
      );
    },
    tunnel: {
      status: async () => {
        tunnelStatusCalls += 1;
        return tunnelStatusCalls >= 3;
      }
    }
  };
  const recoveryPlaneStatus = {
    activation_epoch_id: activationEpochId,
    mcp: {
      state: 'healthy',
      activation_epoch_id: activationEpochId,
      pid: process.pid,
      instance_id: recoveryMcpInstanceId
    },
    tunnel: { state: 'not_configured', configured: false }
  };
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: store,
    settings: { load: () => settings },
    secrets: { get: () => 'test-auth-token' },
    orchestrator,
    revisions: { status: () => ({ disk_revision: revision, running_revision: revision }) },
    recoveryPlane: {
      lastStatus: recoveryPlaneStatus,
      readState: () => ({
        recoveryMcpPid: process.pid,
        recoveryMcpInstanceId,
        recoveryMcpActivationEpochId: activationEpochId
      })
    },
    deviceIdentity: { device_id: deviceId, device_instance_id: recoveryHostInstanceId },
    recoveryInstanceId: recoveryHostInstanceId,
    getUiRegistration: () => ({
      instance_id: uiInstanceId,
      pid: process.pid,
      process_start_token: processStartToken,
      activation_epoch_id: activationEpochId
    }),
    getUiPresence: () => ({
      alive: true,
      instance_id: uiInstanceId,
      pid: process.pid,
      process_start_token: processStartToken
    }),
    getUiRevision: () => ({ disk_revision: revision, running_revision: revision }),
    getRecoveryPlaneStatus: () => recoveryPlaneStatus,
    recoveryHostRunningRevision: revision,
    now: () => nowUnixMs,
    waitFn: async (delayMs) => { tunnelWaits.push(delayMs); }
  });

  const census = await coordinator.finalCensus(activationEpochId);

  assert.deepEqual(calls, ['preflight', 'health', 'connector-ack']);
  assert.equal(census.connector_acknowledgement.attempted, true);
  assert.equal(census.connector_acknowledgement.completed, true);
  assert.equal(census.projection_rebuild_verified, true);
  assert.equal(census.connector_acknowledged, true);
  assert.equal(census.connector_validation.valid, true);
  assert.equal(census.pass, true);
  assert.equal(census.verified, true);
  assert.equal(census.reason, null);
  assert.equal(tunnelStatusCalls, 3, 'one transient Tunnel observation is retried within the same bounded census');
  assert.deepEqual(tunnelWaits, [250, 250]);

  connectorEvidenceMode = 'compatibility';
  connectorAcknowledged = false;
  connectorBootstrapObservedAt = new Date(nowUnixMs - 250).toISOString();
  const callsBeforeCompatibility = calls.length;
  const compatible = await coordinator.finalCensus(activationEpochId);
  assert.deepEqual(calls.slice(callsBeforeCompatibility), ['preflight', 'health', 'connector-ack']);
  assert.equal(compatible.connector_acknowledgement.attempted, true);
  assert.equal(compatible.connector_acknowledgement.completed, true);
  assert.equal(compatible.connector_validation.freshness_mode, 'compatible_activation_bootstrap');
  assert.equal(compatible.connector_validation.rediscovered_at, null);
  assert.equal(compatible.connector_validation.compatibility_acknowledged_at, connectorBootstrapObservedAt);
  assert.equal(compatible.pass, true);

  connectorEvidenceMode = 'discovery';

  connectorAcknowledged = false;
  store.update(activationEpochId, {
    state: 'STARTING',
    reason: 'replacement-assembly-started'
  });
  coordinator.recordPendingCensus(activationEpochId, {
    ...census,
    verified: false,
    pass: false,
    connector_acknowledged: false,
    connector_validation: {
      valid: false,
      code: 'UPDATE_INCOMPLETE',
      reasons: ['CONNECTOR_ACKNOWLEDGEMENT_PENDING']
    },
    reason: 'UPDATE_INCOMPLETE'
  });
  const callsBeforeReuse = calls.length;
  const reused = await coordinator.finalCensus(activationEpochId, { reusePendingProjection: true });
  assert.deepEqual(calls.slice(callsBeforeReuse), ['health', 'connector-ack'],
    'projection reuse must skip only the expensive preflight while keeping live health and connector ACK');
  assert.equal(reused.projection_rebuild_reused, true);
  assert.equal(reused.projection_rebuild_verified, true);
  assert.equal(reused.connector_acknowledged, true);
  assert.equal(reused.pass, true);

  connectorAcknowledged = false;
  nowUnixMs += (5 * 60 * 1000) + 1;
  connectorRediscoveredAt = new Date(nowUnixMs - 1000).toISOString();
  const callsBeforeStaleRefresh = calls.length;
  const refreshed = await coordinator.finalCensus(activationEpochId, { reusePendingProjection: true });
  assert.deepEqual(calls.slice(callsBeforeStaleRefresh), ['health', 'preflight', 'health', 'connector-ack'],
    'a cached receipt that expires at finalize time must be rebuilt before the authoritative health read');
  assert.equal(refreshed.projection_rebuild_reused, false);
  assert.equal(refreshed.projection_rebuild_refreshed_after_stale_reuse, true);
  assert.equal(refreshed.projection_rebuild_verified, true);
  assert.equal(refreshed.pass, true);

  const wrongWorkspaceReceipt = projectionReceipt(path.join(root, 'other-workspace'), {
    projection_classification: 'NO_ACTIVE_PROJECTION',
    projection: { run_id: '', wave_id: '', orchestration_state: '', mode: 'global' },
    completed_at_unix_ms: nowUnixMs
  });
  wrapper = projectionWrapper(wrongWorkspaceReceipt);
  coordinator.recordPendingCensus(activationEpochId, {
    ...refreshed,
    verified: false,
    pass: false,
    connector_acknowledged: false,
    connector_validation: {
      valid: false,
      code: 'UPDATE_INCOMPLETE',
      reasons: ['CONNECTOR_ACKNOWLEDGEMENT_PENDING']
    },
    projection_rebuild_verified: true,
    projection_rebuild_receipt: wrongWorkspaceReceipt,
    reason: 'UPDATE_INCOMPLETE'
  });
  connectorAcknowledged = false;
  const callsBeforeWorkspaceMismatch = calls.length;
  const workspaceMismatch = await coordinator.finalCensus(activationEpochId, { reusePendingProjection: true });
  assert.deepEqual(calls.slice(callsBeforeWorkspaceMismatch), ['health'],
    'workspace mismatch must fail closed instead of triggering the staleness-only rebuild fallback');
  assert.equal(workspaceMismatch.projection_rebuild_refreshed_after_stale_reuse, false);
  assert.equal(workspaceMismatch.pass, false);
  assert.ok(workspaceMismatch.projection_rebuild_validation.reasons.includes('PREFLIGHT_WORKSPACE_MISMATCH'));
  assert.ok(workspaceMismatch.projection_rebuild_validation.reasons.includes('HEALTH_WORKSPACE_MISMATCH'));

  connectorAcknowledged = false;
  preflightWrapperCurrent = false;
  const incomplete = await coordinator.finalCensus(activationEpochId);
  assert.deepEqual(calls.slice(-2), ['preflight', 'health']);
  assert.equal(incomplete.connector_acknowledgement.attempted, false);
  assert.equal(incomplete.projection_rebuild_verified, false);
  assert.equal(incomplete.pass, false);
  assert.equal(incomplete.verified, false);
  assert.equal(incomplete.reason, 'UPDATE_INCOMPLETE');

  // A green connector projection from lightweightSnapshot must not be mixed
  // with a later MCP health observation whose discovery receipt belongs to a
  // retired process.  The exact post-preflight health receipt is authoritative.
  preflightWrapperCurrent = true;
  const originalHealth = orchestrator.currentMcpHealth;
  orchestrator.currentMcpHealth = async () => {
    const value = await originalHealth();
    value.connector_tool_discovery.process_instance_id = id('retired-mcp-process', '1001');
    return value;
  };
  const mixedObservation = await coordinator.finalCensus(activationEpochId);
  assert.equal(mixedObservation.connector_acknowledged, false);
  assert.ok(mixedObservation.connector_validation.reasons.includes('DISCOVERY_PROCESS_INSTANCE_ID_MISMATCH'));
  assert.equal(mixedObservation.pass, false);

  await t.test('central activation requires fresh route and policy while its epoch remains closed, then finalizes without a connector', async () => {
    // Reuse the exact live-process/projection fixture, but give the central
    // profile its own durable store. A mocked passing census would miss both
    // the pre-READY circular gate and the store's mandatory epoch proof.
    const directRecord = store.current();
    const centralStore = new ActivationEpochStore({
      file: path.join(root, 'central-activation-epoch.json'),
      now: () => nowUnixMs
    });
    centralStore.create({
      activation_epoch_id: activationEpochId,
      operation_id: operationId,
      components: directRecord.components,
      component_revisions: directRecord.component_revisions,
      component_evidence: directRecord.component_evidence,
      expires_at_unix_ms: nowUnixMs + 600_000,
      metadata: {
        refresh: true,
        activation_mode: 'full_clean_execution_role_handoff',
        execution_role: 'central_executor',
        component_profile: 'central_executor_v1'
      }
    });
    for (const state of ['ADMISSION_CLOSED', 'FROZEN', 'STOPPING', 'HANDOFF', 'STARTING']) {
      centralStore.update(activationEpochId, { state });
    }
    coordinator.store = centralStore;
    settings.executionRole = 'central_executor';
    settings.tunnelId = '';
    orchestrator.currentMcpHealth = originalHealth;
    connectorEvidenceMode = 'none';
    let primaryTunnelRunning = false;
    orchestrator.lightweightSnapshot = async () => ({
      executionRole: 'central_executor',
      mcpRunning: true,
      nativeAlive: true,
      tunnelRunning: primaryTunnelRunning,
      localReady: false,
      fullyReady: false,
      centralConnected: false,
      authorityReady: false,
      centralStatusReason: 'LOCAL_EXECUTOR_NOT_READY',
      updateIncomplete: true,
      activationEpoch: { activation_epoch_id: activationEpochId, admission_open: false },
      codeRevision: { codingMcp: { disk_revision: revision, running_revision: revision } }
    });
    orchestrator.centralRouteEvidence = (_settings, now) => readControlPlaneRouteEvidence(paths, {
      expectedDeviceId: deviceId,
      now
    });
    let admissionCalls = 0;
    orchestrator.completeActivationEpoch = async (epochId, digest) => {
      admissionCalls += 1;
      const committed = centralStore.current();
      assert.equal(committed.state, 'READY_COMMITTED');
      assert.equal(committed.admission_state, 'CLOSED');
      await coordinator.revalidateBeforeAdmission({
        activationEpochId: epochId,
        readyCommitDigest: digest,
        expiresAtUnixMs: committed.expires_at_unix_ms
      });
      return {
        activation_epoch_id: epochId,
        ready_commit_digest: digest,
        expires_at_unix_ms: committed.expires_at_unix_ms,
        admission_open: true
      };
    };
    const missingRoute = await coordinator.finalCensus(activationEpochId);
    assert.equal(missingRoute.pass, false);
    assert.equal(missingRoute.central_route_verified, false);
    assert.equal(missingRoute.central_status_reason, 'CENTRAL_ROUTE_EVIDENCE_MISSING');
    coordinator.recordPendingCensus(activationEpochId, missingRoute);
    assert.equal(centralStore.current().state, 'VERIFYING');
    assert.equal(centralStore.current().admission_state, 'CLOSED');
    assert.equal(admissionCalls, 0);

    const route = {
      schema_version: 1,
      kind: 'control_plane_authenticated_heartbeat',
      server_origin: 'https://central.example',
      device_id: deviceId,
      endpoint_id: id('endpoint', '1001'),
      credential_generation: 1,
      server_last_seen_at_ms: nowUnixMs,
      observed_at_ms: nowUnixMs,
      runtime_readiness: 'degraded',
      policy_state: 'enabled',
      policy_expires_at_ms: nowUnixMs + 600_000,
      policy_sha256: 'e'.repeat(64)
    };
    const writeRoute = (patch = {}) => {
      fs.mkdirSync(path.dirname(paths.controlPlaneRouteEvidenceFile()), { recursive: true });
      fs.writeFileSync(paths.controlPlaneRouteEvidenceFile(), JSON.stringify({ ...route, ...patch }));
    };
    for (const [patch, expectedReason] of [
      [{ observed_at_ms: nowUnixMs - 60_001 }, 'CENTRAL_ROUTE_EVIDENCE_STALE'],
      [{ device_id: id('other-device', '1001') }, 'CENTRAL_ROUTE_EVIDENCE_DEVICE_MISMATCH'],
      [{ policy_state: 'expired_or_disabled', policy_expires_at_ms: nowUnixMs - 1 }, 'CENTRAL_LOCAL_POLICY_NOT_READY']
    ]) {
      writeRoute(patch);
      const invalid = await coordinator.finalCensus(activationEpochId);
      assert.equal(invalid.pass, false);
      assert.equal(invalid.central_route_verified, false);
      assert.equal(invalid.central_status_reason, expectedReason);
      assert.equal(centralStore.current().admission_state, 'CLOSED');
      assert.equal(admissionCalls, 0);
    }
    writeRoute();
    primaryTunnelRunning = true;
    assert.equal((await coordinator.finalCensus(activationEpochId)).pass, false,
      'a still-running direct Windows Tunnel cannot be accepted as central executor');
    primaryTunnelRunning = false;
    const centralReady = await coordinator.finalCensus(activationEpochId);
    assert.equal(centralReady.pass, true);
    assert.equal(centralReady.all_components_same_epoch, true);
    assert.equal(centralReady.central_route_verified, true);
    assert.equal(centralReady.central_status_reason, null);
    assert.equal(centralReady.runtime.fullyReady, false,
      'admission is closed while the independent central route is proven');
    assert.equal(centralReady.runtime.updateIncomplete, false,
      'expected pre-admission epoch state must not invalidate a complete READY proof');
    assert.equal(centralReady.runtime.admissionPending, true);
    assert.equal(Object.hasOwn(centralReady, 'connector_validation'), false);
    coordinator.recordPendingCensus(activationEpochId, centralReady);
    const completed = await coordinator.finalize(activationEpochId);
    assert.equal(completed.state, 'READY');
    assert.equal(completed.activation_mode, 'full_clean_execution_role_handoff');
    assert.equal(admissionCalls, 1);
    assert.equal(centralStore.current().admission_state, 'OPEN');
    const { validatePersistedReadyConnectorProof } = require('../electron/services/recoveryHost');
    const adoption = validatePersistedReadyConnectorProof(centralStore.current(), {
      nowUnixMs,
      expectedExecutionRole: 'central_executor'
    });
    assert.equal(adoption.valid, true, adoption.reasons.join(', '));
    assert.deepEqual(adoption.reasons, []);
  });
});

test('central full-clean replacement persists its epoch role and never supplies node Tunnel credentials', async (t) => {
  const { root, paths } = fixture(t);
  const activationEpochId = id('activation-central-handoff', '0001');
  const operationId = id('operation-central-handoff', '0001');
  const nowUnixMs = 1_700_000_000_000;
  const store = new ActivationEpochStore({ paths, now: () => nowUnixMs });
  store.create({
    activation_epoch_id: activationEpochId,
    operation_id: operationId,
    components: ['recovery_host', 'coding_mcp', 'electron_ui'],
    expires_at_unix_ms: nowUnixMs + 120_000,
    metadata: {
      reason: 'central-handoff-test',
      execution_role: 'central_executor',
      component_profile: 'central_executor_v1'
    }
  });
  let settings = {
    workspace: root,
    executionRole: 'direct_legacy',
    tunnelId: 'tunnel_legacy_primary',
    recoveryTunnelId: 'tunnel_legacy_recovery',
    recoveryMcpPort: 18767,
    recoveryHealthPort: 18083
  };
  const observed = { saves: [], starts: [], ensure: [], secretNames: [] };
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: store,
    now: () => nowUnixMs,
    settings: {
      load: () => settings,
      save: (patch) => {
        observed.saves.push(patch);
        settings = { ...settings, ...patch };
        return settings;
      }
    },
    secrets: { get: (name) => { observed.secretNames.push(name); return name === 'mcpAuthToken' ? 'loopback-only-token' : 'must-not-be-read'; } },
    orchestrator: {
      setActivationEpoch() {},
      ensureToken: async () => 'loopback-only-token',
      start: async (options) => { observed.starts.push(options); return {}; },
      stop: async () => {}
    },
    recoveryPlane: {
      setActivationEpoch() {},
      ensure: async (recoverySettings, options) => { observed.ensure.push({ recoverySettings, options }); return {}; },
      stop: async () => {}
    },
    getUiRegistration: () => ({ instance_id: 'ui-central-handoff-0001', activation_epoch_id: activationEpochId }),
    getUiPresence: () => ({ alive: true, instance_id: 'ui-central-handoff-0001' })
  });
  coordinator.finalCensus = async () => ({
    activation_epoch_id: activationEpochId,
    pass: false,
    verified: false,
    reason: 'CENTRAL_ROUTE_EVIDENCE_MISSING'
  });

  const result = await coordinator.continueReplacement({ activationEpochId });
  assert.equal(result.state, 'VERIFYING');
  assert.deepEqual(observed.saves, [{ executionRole: 'central_executor' }]);
  assert.equal(observed.starts.length, 1);
  assert.equal(observed.ensure.length, 1);
  assert.equal(observed.ensure[0].recoverySettings.tunnelId, '');
  assert.equal(observed.ensure[0].recoverySettings.recoveryTunnelId, '');
  assert.equal(observed.ensure[0].options.runtimeApiKey, '');
  assert.equal(observed.secretNames.includes('runtimeApiKey'), false);
  assert.equal(store.current().metadata.execution_role, 'central_executor');
  assert.equal(store.current().metadata.component_profile, 'central_executor_v1');
});

test('execution role changes are refused outside an explicit full-clean handoff', async (t) => {
  const { root, paths } = fixture(t);
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: epochStore(paths),
    settings: { load: () => ({ workspace: root, executionRole: 'direct_legacy' }) }
  });
  await assert.rejects(
    coordinator.restart({ executionRole: 'central_executor' }),
    { code: 'ACTIVATION_EXECUTION_ROLE_HANDOFF_REQUIRED' }
  );
});

test('operator central handoff is checkpoint-free and preserves its distinct mode for direct migration or central retry', async (t) => {
  for (const executionRole of ['direct_legacy', 'central_executor']) {
    const { root, paths } = fixture(t);
    const coordinator = new FullCleanActivation({
      paths,
      epochStore: epochStore(paths),
      settings: { load: () => ({ workspace: root, executionRole }) }
    });
    let observed = null;
    coordinator._restart = async (options) => {
      observed = options;
      return { state: 'HANDOFF' };
    };
    await coordinator.restart({
      mode: 'full_clean_execution_role_handoff',
      executionRole: 'central_executor',
      reason: 'operator_central_executor_handoff'
    });
    assert.equal(observed.mode, 'full_clean_execution_role_handoff');
    assert.equal(observed.refresh, true);
    assert.equal(observed.sourceCheckpoint, null);
    assert.equal(observed.executionRole, 'central_executor');
    assert.equal(observed.componentProfile, 'central_executor_v1');
  }
});

test('operator central handoff refuses source, revision, soft-restart and acceptance authority before mutation', async (t) => {
  const { root, paths } = fixture(t);
  const store = epochStore(paths);
  const calls = [];
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: store,
    settings: { load: () => ({ workspace: root, executionRole: 'direct_legacy' }) },
    orchestrator: { restart: async () => { calls.push('soft'); } }
  });
  coordinator._restart = async () => { calls.push('restart'); };
  for (const patch of [
    { sourceCheckpoint: acceptedSourceCheckpoint() },
    { source_checkpoint: acceptedSourceCheckpoint() },
    { sourceCheckpoint: '' },
    { component: 'coding_mcp' },
    { expectedDiskRevision: 'a'.repeat(64) },
    { expected_disk_revision: 'a'.repeat(64) },
    { automatic: true },
    { soft: true },
    { allowAcceptancePending: true },
    { maintenanceWorkspace: root },
    { reason: `exact_stale_runs:${'a'.repeat(32)}` },
    { executionRole: 'direct_legacy' },
    { executionRole: undefined }
  ]) {
    await assert.rejects(coordinator.restart({
      mode: 'full_clean_execution_role_handoff',
      executionRole: 'central_executor',
      ...patch
    }), { code: 'ACTIVATION_EXECUTION_ROLE_HANDOFF_INVALID' });
  }
  assert.equal(store.current(), null);
  assert.deepEqual(calls, []);
});

test('operator central handoff preserves live-runtime fences and binds checkpointless migration mode durably', async (t) => {
  const { root, paths } = fixture(t);
  const store = epochStore(paths);
  const calls = [];
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: store,
    settings: {
      load: () => ({ workspace: root, executionRole: 'direct_legacy' }),
      save: () => { calls.push('settings.save'); }
    },
    orchestrator: {
      inspectCodeActivation: async () => ({ executor_cleanup_supported: true, safe: true, code: 'READY', workspace: root }),
      prepareCodeActivation: async (options) => {
        calls.push('fence');
        assert.equal(Object.hasOwn(options, 'sourceCheckpoint'), false);
        assert.equal(options.allowAcceptancePending, false);
        return {
          safe: true,
          fenced: true,
          executor_cleanup: { state: 'not_required', confirmed: true },
          fence_operation_id: options.operationId,
          expires_at_unix_ms: options.expiresAtUnixMs
        };
      },
      currentMcpHealth: async () => null,
      stop: async () => { calls.push('runtime.stop'); }
    },
    recoveryPlane: { stop: async () => { calls.push('recovery.stop'); } },
    spawnRecoveryReplacement: async () => { calls.push('replacement.spawn'); },
    now: () => 1_700_000_000_030
  });
  const request = {
    operationId: id('operation-role-handoff', '1002'),
    mode: 'full_clean_execution_role_handoff',
    executionRole: 'central_executor',
    reason: 'operator_central_executor_handoff'
  };
  const result = await coordinator.restart(request);
  assert.equal(result.state, 'HANDOFF');
  assert.deepEqual(calls, ['fence', 'fence', 'runtime.stop', 'recovery.stop', 'replacement.spawn']);
  assert.equal(store.current().source_checkpoint, null);
  assert.equal(store.current().metadata.activation_mode, request.mode);
  assert.equal(store.current().metadata.refresh, true);
  assert.equal(store.current().metadata.execution_role, 'central_executor');
  assert.equal(store.current().metadata.component_profile, 'central_executor_v1');
  assert.equal(store.current().admission_state, 'CLOSED');
  assert.equal((await coordinator.restart(request)).state, 'HANDOFF');
  assert.equal(calls.length, 5, 'idempotent retry must not stop or spawn another replacement');
  await assert.rejects(coordinator.restart({
    operationId: request.operationId,
    refresh: true,
    mode: 'full_clean_refresh'
  }), { code: 'ACTIVATION_EXECUTION_ROLE_HANDOFF_MISMATCH' });
  assert.equal(calls.length, 5);
});

test('operator central handoff cannot override busy runtime or stopped canonical-ledger acceptance blockers', async (t) => {
  for (const stopped of [false, true]) {
    const { root, paths } = fixture(t);
    const store = epochStore(paths);
    const calls = [];
    const coordinator = new FullCleanActivation({
      paths,
      epochStore: store,
      settings: { load: () => ({ workspace: root, executionRole: 'direct_legacy' }) },
      orchestrator: {
        inspectCodeActivation: async () => stopped
          ? { safe: true, code: 'COMPONENT_STOPPED' }
          : { safe: false, code: 'RUNTIME_BUSY' },
        stop: async () => { calls.push('stop'); }
      },
      canonicalLedgerCensus: async (options) => {
        calls.push('census');
        assert.equal(options.sourceCheckpoint, null);
        assert.equal(options.allowAcceptancePending, false);
        return { safe: false, code: 'ACCEPTANCE_PENDING', reason: 'acceptance_pending' };
      },
      spawnRecoveryReplacement: async () => { calls.push('spawn'); }
    });
    await assert.rejects(coordinator.restart({
      mode: 'full_clean_execution_role_handoff',
      executionRole: 'central_executor'
    }), { code: stopped ? 'ACCEPTANCE_PENDING' : 'RUNTIME_BUSY' });
    assert.equal(store.current(), null);
    assert.deepEqual(calls, stopped ? ['census'] : []);
  }
});

test('full-clean restart refuses a missing accepted source checkpoint before any epoch or process mutation', async (t) => {
  const { root, paths } = fixture(t);
  const store = epochStore(paths);
  const calls = [];
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: store,
    settings: { load: () => ({ workspace: root }) },
    orchestrator: {
      stop: async () => { calls.push('stop'); },
      start: async () => { calls.push('start'); }
    },
    recoveryPlane: { stop: async () => { calls.push('recovery-stop'); } }
  });

  await assert.rejects(
    coordinator.restart({ operationId: id('operation-missing-checkpoint', '1001') }),
    { code: 'ACTIVATION_SOURCE_CHECKPOINT_REQUIRED' }
  );
  assert.equal(coordinator.current(), null);
  assert.deepEqual(calls, []);
});

test('explicit process refresh starts a full-clean epoch without inventing a source checkpoint', async (t) => {
  const { root, paths } = fixture(t);
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: epochStore(paths),
    settings: { load: () => ({ workspace: root }) }
  });
  let observed = null;
  coordinator._restart = async (options) => {
    observed = options;
    return { activation_epoch_id: id('activation-refresh', '1001'), state: 'HANDOFF' };
  };

  const result = await coordinator.restart({
    operationId: id('operation-refresh', '1001'),
    refresh: true,
    mode: 'full_clean_refresh',
    reason: 'npm_start_refresh'
  });
  assert.equal(result.state, 'HANDOFF');
  assert.equal(observed.refresh, true);
  assert.equal(observed.mode, 'full_clean_refresh');
  assert.equal(observed.sourceCheckpoint, null);
});

test('full-clean bounds the Coding MCP preparation fence without shortening the durable epoch', async (t) => {
  const { root, paths } = fixture(t);
  const nowUnixMs = 1_700_000_000_000;
  const calls = [];
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: epochStore(paths),
    settings: { load: () => ({ workspace: root }) },
    orchestrator: {
      prepareCodeActivation: async (options) => {
        calls.push(options);
        return {
          safe: true,
          fenced: true,
          executor_cleanup: { state: 'not_required', confirmed: true },
          fence_operation_id: options.operationId,
          expires_at_unix_ms: options.expiresAtUnixMs
        };
      }
    },
    now: () => nowUnixMs
  });
  const operationId = id('operation-bounded-fence', '1001');
  const durableExpiresAtUnixMs = nowUnixMs + 600_000;

  const bounded = await coordinator._prepareFence(operationId, durableExpiresAtUnixMs, null, false);
  const shortDeadline = await coordinator._prepareFence(operationId, nowUnixMs + 30_000, null, false);

  assert.equal(calls[0].expiresAtUnixMs, nowUnixMs + 55_000);
  assert.equal(bounded.expires_at_unix_ms, nowUnixMs + 55_000);
  assert.equal(calls[1].expiresAtUnixMs, nowUnixMs + 30_000);
  assert.equal(shortDeadline.expires_at_unix_ms, nowUnixMs + 30_000);
  assert.equal(durableExpiresAtUnixMs, nowUnixMs + 600_000,
    'the end-to-end activation epoch keeps its independent ten-minute deadline');
});

test('public full-clean refresh renews the Coding MCP fence after slow UI termination without shortening handoff expiry', async (t) => {
  const { root, paths } = fixture(t);
  let nowUnixMs = 1_700_000_000_000;
  const durableExpiresAtUnixMs = nowUnixMs + 600_000;
  const operationId = id('operation-renewed-fence', '1001');
  const prepareCalls = [];
  const events = [];
  const spawnCalls = [];
  const store = new ActivationEpochStore({ paths, now: () => nowUnixMs });
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: store,
    settings: { load: () => ({ workspace: root }) },
    orchestrator: {
      inspectCodeActivation: async () => ({ executor_cleanup_supported: true, safe: true, code: 'READY', workspace: root }),
      prepareCodeActivation: async (options) => {
        prepareCalls.push({ preparedAtUnixMs: nowUnixMs, ...options });
        events.push('prepare');
        return {
          safe: true,
          fenced: true,
          executor_cleanup: { state: 'not_required', confirmed: true },
          fence_operation_id: options.operationId,
          expires_at_unix_ms: options.expiresAtUnixMs
        };
      },
      currentMcpHealth: async () => null,
      stop: async () => { events.push('runtime.stop'); return true; }
    },
    recoveryPlane: { stop: async () => { events.push('recovery-plane.stop'); } },
    getUiPresence: () => ({ alive: true, pid: process.pid + 1, instance_id: id('old-electron-ui', '1001') }),
    terminateUi: async () => {
      events.push('ui.stop');
      nowUnixMs += 56_000;
    },
    spawnRecoveryReplacement: async (options) => {
      events.push('recovery.spawn');
      spawnCalls.push(options);
    },
    now: () => nowUnixMs
  });

  const result = await coordinator.restart({
    operationId,
    refresh: true,
    mode: 'full_clean_refresh',
    expiresAtUnixMs: durableExpiresAtUnixMs
  });

  assert.equal(result.state, 'HANDOFF');
  assert.deepEqual(events, [
    'prepare',
    'ui.stop',
    'prepare',
    'runtime.stop',
    'recovery-plane.stop',
    'recovery.spawn'
  ]);
  assert.equal(prepareCalls.length, 2);
  for (const call of prepareCalls) {
    assert.equal(call.operationId, operationId);
    assert.ok(call.expiresAtUnixMs > call.preparedAtUnixMs);
    assert.ok(call.expiresAtUnixMs <= call.preparedAtUnixMs + 55_000);
  }
  assert.equal(prepareCalls[0].expiresAtUnixMs, 1_700_000_055_000);
  assert.equal(prepareCalls[1].preparedAtUnixMs, 1_700_000_056_000,
    'UI termination advances beyond the first short-lived preparation fence');
  assert.equal(prepareCalls[1].expiresAtUnixMs, 1_700_000_111_000);
  assert.equal(spawnCalls.length, 1);
  assert.equal(spawnCalls[0].operationId, operationId);
  assert.equal(spawnCalls[0].expiresAtUnixMs, durableExpiresAtUnixMs);
  assert.equal(store.current().expires_at_unix_ms, durableExpiresAtUnixMs);
  assert.equal(store.current().source_checkpoint, null,
    'the public refresh path must not invent an accepted source checkpoint');
});

test('full-clean restart forwards service ports as recovery-plane idle proof', async (t) => {
  const { root, paths } = fixture(t);
  let nowUnixMs = 1_700_000_000_000;
  const durableExpiresAtUnixMs = nowUnixMs + 600_000;
  const operationId = id('operation-idle-proof', '1001');
  const stopArgs = [];
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: new ActivationEpochStore({ paths, now: () => nowUnixMs }),
    settings: { load: () => ({ workspace: root, recoveryHealthPort: 18083, recoveryMcpPort: 18767 }) },
    orchestrator: {
      inspectCodeActivation: async () => ({ executor_cleanup_supported: true, safe: true, code: 'READY', workspace: root }),
      prepareCodeActivation: async (options) => ({
        safe: true,
        fenced: true,
        executor_cleanup: { state: 'not_required', confirmed: true },
          fence_operation_id: options.operationId,
        expires_at_unix_ms: options.expiresAtUnixMs
      }),
      currentMcpHealth: async () => null,
      stop: async () => true
    },
    recoveryPlane: { stop: async (idleProof) => { stopArgs.push(idleProof); } },
    getUiPresence: () => ({}),
    spawnRecoveryReplacement: async () => {},
    now: () => nowUnixMs
  });

  const result = await coordinator.restart({
    operationId,
    refresh: true,
    mode: 'full_clean_refresh',
    expiresAtUnixMs: durableExpiresAtUnixMs
  });

  assert.equal(result.state, 'HANDOFF');
  assert.deepEqual(stopArgs, [{ recoveryHealthPort: 18083, recoveryMcpPort: 18767 }],
    'the STOPPING boundary must let the plane prove stale receipts idle without terminating them');
});

test('full-clean single-flight reuses only the exact operation and source authority', async (t) => {
  const { root, paths } = fixture(t);
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: epochStore(paths),
    settings: { load: () => ({ workspace: root }) }
  });
  const checkpoint = acceptedSourceCheckpoint();
  const operationId = id('operation-single-flight', '1001');
  let release;
  let calls = 0;
  coordinator._restart = async (options) => {
    calls += 1;
    await new Promise((resolve) => { release = resolve; });
    return { operation_id: options.operationId };
  };

  const first = coordinator.restart({ operationId, sourceCheckpoint: checkpoint });
  const exactReplay = coordinator.restart({ operationId, sourceCheckpoint: checkpoint });
  await assert.rejects(
    coordinator.restart({ operationId: id('operation-single-flight', '1002'), sourceCheckpoint: checkpoint }),
    { code: 'RUNTIME_BUSY' }
  );
  await assert.rejects(
    coordinator.restart({
      operationId,
      sourceCheckpoint: { ...checkpoint, proof_fingerprint: 'c'.repeat(64) }
    }),
    { code: 'RUNTIME_BUSY' }
  );
  assert.equal(calls, 1);
  release();
  assert.deepEqual(await first, { operation_id: operationId });
  assert.deepEqual(await exactReplay, { operation_id: operationId });
  assert.equal(coordinator.inFlight, null);
  assert.equal(coordinator.inFlightRequestKey, null);
});

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

test('replacement reconciles exact stale runs in one atomic helper invocation before Coding MCP start', async (t) => {
  const { root, paths } = fixture(t);
  const store = epochStore(paths);
  const firstRun = 'a'.repeat(32);
  const secondRun = 'b'.repeat(32);
  const created = store.create({
    activation_epoch_id: id('activation-exact-stale', '0001'),
    operation_id: id('operation-exact-stale', '0001'),
    expiresAtUnixMs: 1_700_000_120_000,
    components: ['recovery_host', 'coding_mcp', 'electron_ui'],
    metadata: { reason: `exact_stale_runs:${firstRun},${secondRun}` }
  });
  const calls = [];
  const failure = Object.assign(new Error('stop after maintenance proof'), { code: 'MCP_START_FAILED' });
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: store,
    settings: { load: () => ({ workspace: root }) },
    orchestrator: {
      setActivationEpoch() {},
      start: async () => { calls.push('start'); throw failure; }
    },
    now: () => 1_700_000_000_001
  });
  coordinator._execExactStaleRunCli = async ({ runIds, reconcile, snapshotSha256, logicalSha256 }) => {
    calls.push(`batch:${reconcile ? 'reconcile' : 'preflight'}:${runIds.length}`);
    assert.deepEqual(runIds, [firstRun, secondRun]);
    assert.equal(reconcile, true);
    assert.equal(snapshotSha256, undefined);
    assert.equal(logicalSha256, undefined);
    return {
      schema_version: 1,
      reconciliation: {
        changed: true,
        idempotent: false,
        chain_ok: true,
        results: [
          { run_id: firstRun, changed: true, idempotent: false, chain_ok: true },
          { run_id: secondRun, changed: true, idempotent: false, chain_ok: true }
        ]
      },
      postflight: {
        targets: [
          { run_id: firstRun, status: 'stale', classification: 'RECONCILED_STALE', already_reconciled: true },
          { run_id: secondRun, status: 'stale', classification: 'RECONCILED_STALE', already_reconciled: true }
        ]
      }
    };
  };

  await assert.rejects(
    coordinator.continueReplacement({ activationEpochId: created.activation_epoch_id }),
    { code: 'MCP_START_FAILED' }
  );
  assert.deepEqual(calls, [
    'batch:reconcile:2',
    'start'
  ]);
  assert.equal(store.current().state, 'FAILED');
});

test('exact stale-run maintenance accepts 64 exact IDs and rejects 65', async (t) => {
  const { paths } = fixture(t);
  const coordinator = new FullCleanActivation({ paths, settings: { load: () => ({}) } });
  const sixtyFour = Array.from({ length: 64 }, (_value, index) => index.toString(16).padStart(32, '0'));
  assert.deepEqual(
    coordinator._exactStaleRunIds({ metadata: { reason: `exact_stale_runs:${sixtyFour.join(',')}` } }),
    sixtyFour
  );
  const sixtyFive = [...sixtyFour, 'f'.repeat(32)];
  assert.throws(
    () => coordinator._exactStaleRunIds({ metadata: { reason: `exact_stale_runs:${sixtyFive.join(',')}` } }),
    { code: 'EXACT_STALE_RUN_REQUEST_INVALID' }
  );
});

test('replacement refuses malformed exact stale-run maintenance before Coding MCP start', async (t) => {
  const { root, paths } = fixture(t);
  const store = epochStore(paths);
  const created = store.create({
    activation_epoch_id: id('activation-exact-stale', '0002'),
    operation_id: id('operation-exact-stale', '0002'),
    expiresAtUnixMs: 1_700_000_120_000,
    components: ['recovery_host', 'coding_mcp', 'electron_ui'],
    metadata: { reason: 'exact_stale_runs:not-a-run-id' }
  });
  let startCalls = 0;
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: store,
    settings: { load: () => ({ workspace: root }) },
    orchestrator: {
      setActivationEpoch() {},
      start: async () => { startCalls += 1; }
    },
    now: () => 1_700_000_000_001
  });

  await assert.rejects(
    coordinator.continueReplacement({ activationEpochId: created.activation_epoch_id }),
    { code: 'EXACT_STALE_RUN_REQUEST_INVALID' }
  );
  assert.equal(startCalls, 0);
  assert.equal(store.current().state, 'FAILED');
  assert.equal(store.current().admission_state, 'CLOSED');
});

test('full-clean unverified prepare preserves owned old components and terminalizes the epoch', async (t) => {
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
      inspectCodeActivation: async () => ({ executor_cleanup_supported: true, safe: true, code: 'READY' }),
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
      expectedDiskRevision: 'a'.repeat(64),
      sourceCheckpoint: acceptedSourceCheckpoint()
    }),
    { code: 'ACTIVATION_PREFLIGHT_UNVERIFIED' }
  );
  assert.deepEqual(calls.map(([name]) => name), [], 'an unverified prepare must preserve the owned executor');
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

test('Recovery Host terminalizes an expired resumable epoch and publishes control-plane readiness', async (t) => {
  const { root, paths } = fixture(t);
  const store = epochStore(paths);
  const created = store.create({
    activation_epoch_id: id('activation-expired', '0007'),
    operation_id: id('operation-expired', '0007'),
    expiresAtUnixMs: 1_700_000_001_000
  });
  store.update(created.activation_epoch_id, { state: 'HANDOFF', reason: 'replacement-requested' });
  let recoveryEnsureCalls = 0;
  let ipcStartCalls = 0;
  const gateway = { start: async () => {}, stop: async () => {} };
  const ipc = {
    start: async () => { ipcStartCalls += 1; },
    stop: async () => {}
  };
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
      activationEpochId: '',
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
  const terminal = new ActivationEpochStore({ paths }).current();
  assert.equal(host.running, true);
  assert.equal(ipcStartCalls, 1, 'the authenticated Recovery control plane must become ready during cold start');
  assert.equal(terminal.state, 'FAILED');
  assert.equal(terminal.admission_state, 'CLOSED');
  assert.equal(terminal.error.code, 'ACTIVATION_REQUEST_EXPIRED');
  assert.equal(status.activation_epoch.state, 'FAILED');
  assert.equal(status.activation_epoch.admission_open, false);
  assert.equal(status.runtime, null);
  assert.equal(recoveryEnsureCalls, 0, 'an expired transaction must not recover child runtimes outside an explicit refresh');
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

  const result = await coordinator.restart({ operationId: id('operation-epoch', '0009'), sourceCheckpoint: acceptedSourceCheckpoint() });
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

  await assert.rejects(coordinator.restart({ operationId: id('operation-epoch', '0010'), sourceCheckpoint: acceptedSourceCheckpoint() }), { code: 'ORCHESTRATION_STATE_UNCERTAIN' });
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

  await assert.rejects(coordinator.restart({ operationId: id('operation-epoch', '0012'), sourceCheckpoint: acceptedSourceCheckpoint() }), {
    code: 'ACCEPTANCE_PENDING',
    message: /reason=acceptance_pending/
  });
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

test('manual restart never falls back to stop-start when full-clean coordination is unavailable', async (t) => {
  const { paths } = fixture(t);
  let stopped = 0;
  let started = 0;
  const orchestrator = new RuntimeOrchestrator({
    paths,
    settings: { load: () => ({}) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.stop = async () => { stopped += 1; };
  orchestrator.start = async () => { started += 1; };

  await assert.rejects(orchestrator.restart({ reason: 'operator' }), {
    code: 'FULL_CLEAN_ACTIVATION_UNAVAILABLE'
  });
  assert.equal(stopped, 0);
  assert.equal(started, 0);
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

test('pre-admission revalidation rejects process drift against the committed census', async (t) => {
  const { root, paths } = fixture(t);
  const activationEpochId = id('activation-pre-open-drift', '1001');
  const readyCommitDigest = 'd'.repeat(64);
  const expiresAtUnixMs = 1_700_000_120_000;
  const committedCensus = {
    pass: true,
    activation_epoch_id: activationEpochId,
    host_instance_id: id('recovery-host-current', '1001'),
    host_pid: 101,
    process_instance_id: id('mcp-process-current', '1001'),
    server_instance_id: id('mcp-server-current', '1001'),
    supervisor_instance_id: id('native-supervisor-current', '1001'),
    tunnel_instance_id: id('coding-tunnel-current', '1001'),
    tunnel_pid: 102,
    recovery_mcp_instance_id: id('recovery-mcp-current', '1001'),
    recovery_mcp_pid: 103,
    recovery_tunnel_instance_id: null,
    recovery_tunnel_pid: null,
    ui_instance_id: id('electron-ui-current', '1001'),
    ui_running_revision: '1'.repeat(64),
    recovery_host_running_revision: '2'.repeat(64),
    running_revision: '3'.repeat(64),
    disk_revision: '3'.repeat(64)
  };
  const record = {
    activation_epoch_id: activationEpochId,
    state: 'READY_COMMITTED',
    admission_state: 'CLOSED',
    ready_commit_digest: readyCommitDigest,
    expires_at_unix_ms: expiresAtUnixMs,
    component_evidence: {
      recovery_host: { instance_id: id('recovery-host-retired', '1001') }
    },
    verification: { final_census: committedCensus }
  };
  const coordinator = new FullCleanActivation({
    paths,
    epochStore: { current: () => record },
    settings: { load: () => ({ workspace: root }) },
    orchestrator: {},
    now: () => 1_700_000_000_000
  });
  coordinator.finalCensus = async (epochIdValue, options) => {
    assert.equal(epochIdValue, activationEpochId);
    assert.deepEqual(options, {
      expectedOldInstanceId: id('recovery-host-retired', '1001'),
      reusePendingProjection: true,
      revalidateCommitted: true
    });
    return {
      ...committedCensus,
      process_instance_id: id('mcp-process-replaced-again', '1001')
    };
  };

  await assert.rejects(
    coordinator.revalidateBeforeAdmission({
      activationEpochId,
      readyCommitDigest,
      expiresAtUnixMs
    }),
    (error) => error?.code === 'UPDATE_INCOMPLETE'
      && error?.details?.mismatches?.some((item) => item.field === 'process_instance_id')
  );
  assert.equal(record.state, 'READY_COMMITTED');
  assert.equal(record.admission_state, 'CLOSED');
});

test('finalize never opens MCP admission when the durable ready commit fails', async (t) => {
  const harness = finalizeTransactionFixture(t, {
    commitReadyError: codedError('ACTIVATION_EPOCH_STORE_INVALID', 'durable commit failed')
  });

  await assert.rejects(
    harness.coordinator.finalize(harness.activationEpochId),
    { code: 'ACTIVATION_EPOCH_STORE_INVALID' }
  );

  assert.equal(harness.calls.filter(([name]) => name === 'completeActivationEpoch').length, 0);
  assert.deepEqual(harness.calls.map(([name]) => name), ['finalCensus', 'commitReady', 'fail']);
  assert.equal(harness.current().state, 'FAILED');
  assert.equal(harness.current().admission_state, 'CLOSED');
});

test('finalize commits proof before opening admission and performs no post-open census', async (t) => {
  const harness = finalizeTransactionFixture(t);

  const result = await harness.coordinator.finalize(harness.activationEpochId, { pass: false });

  assert.deepEqual(harness.calls.map(([name]) => name), [
    'finalCensus',
    'commitReady',
    'completeActivationEpoch',
    'ready'
  ]);
  assert.equal(harness.calls.filter(([name]) => name === 'finalCensus').length, 1);
  assert.deepEqual(harness.calls.find(([name]) => name === 'finalCensus')[2], {
    reusePendingProjection: true
  });
  assert.deepEqual(harness.calls.find(([name]) => name === 'completeActivationEpoch').slice(1), [
    harness.activationEpochId,
    harness.readyCommitDigest
  ]);
  assert.deepEqual(harness.calls.find(([name]) => name === 'ready').slice(1), [
    harness.activationEpochId,
    harness.readyCommitDigest
  ]);
  assert.equal(result.state, 'READY');
  assert.equal(result.admission_open, true);
  assert.equal(result.fully_ready, true);
  assert.equal(harness.current().state, 'READY');
  assert.equal(harness.current().admission_state, 'OPEN');
});

test('lost complete response reconciles exact MCP health once without retrying the mutation', async (t) => {
  const harness = finalizeTransactionFixture(t, {
    complete: async () => { throw codedError('ETIMEDOUT', 'completion response was lost'); },
    health: ({ receipt }) => receipt(true)
  });

  const result = await harness.coordinator.finalize(harness.activationEpochId);

  assert.equal(harness.calls.filter(([name]) => name === 'completeActivationEpoch').length, 1);
  assert.equal(harness.calls.filter(([name]) => name === 'currentMcpHealth').length, 1);
  assert.equal(harness.calls.filter(([name]) => name === 'closeActivationEpoch').length, 0);
  assert.equal(result.mcp_admission.admission_open, true);
  assert.equal(harness.current().state, 'READY');
  assert.equal(harness.current().admission_state, 'OPEN');
});

test('mismatched health after response loss closes the exact epoch and digest', async (t) => {
  const harness = finalizeTransactionFixture(t, {
    complete: async () => { throw codedError('ECONNRESET', 'completion response was lost'); },
    health: ({ receipt }) => receipt(true, { ready_commit_digest: 'e'.repeat(64) })
  });

  await assert.rejects(
    harness.coordinator.finalize(harness.activationEpochId),
    { code: 'MCP_ACTIVATION_COMMIT_UNCERTAIN' }
  );

  const closeCall = harness.calls.find(([name]) => name === 'closeActivationEpoch');
  assert.deepEqual(closeCall.slice(1), [harness.activationEpochId, harness.readyCommitDigest]);
  assert.equal(harness.calls.filter(([name]) => name === 'runtime.stop').length, 0);
  assert.equal(harness.current().state, 'FAILED');
  assert.equal(harness.current().admission_state, 'CLOSED');
});

test('unavailable reconciliation stops the owned runtime when exact close is unconfirmed', async (t) => {
  const harness = finalizeTransactionFixture(t, {
    complete: async () => { throw codedError('ETIMEDOUT', 'completion response was lost'); },
    health: () => null,
    close: async () => { throw codedError('ETIMEDOUT', 'close response was lost'); }
  });

  await assert.rejects(
    harness.coordinator.finalize(harness.activationEpochId),
    { code: 'MCP_ACTIVATION_COMMIT_UNCERTAIN' }
  );

  const closeCall = harness.calls.find(([name]) => name === 'closeActivationEpoch');
  assert.deepEqual(closeCall.slice(1), [harness.activationEpochId, harness.readyCommitDigest]);
  assert.equal(harness.calls.filter(([name]) => name === 'currentMcpHealth').length, 2);
  assert.equal(harness.calls.filter(([name]) => name === 'runtime.stop').length, 1);
  assert.equal(harness.current().state, 'FAILED');
  assert.equal(harness.current().admission_state, 'CLOSED');
});

test('durable READY failure after MCP admission rolls back the exact epoch', async (t) => {
  const harness = finalizeTransactionFixture(t, {
    readyError: codedError('ACTIVATION_EPOCH_STORE_INVALID', 'READY persistence failed')
  });

  await assert.rejects(
    harness.coordinator.finalize(harness.activationEpochId),
    { code: 'ACTIVATION_EPOCH_STORE_INVALID' }
  );

  const closeCall = harness.calls.find(([name]) => name === 'closeActivationEpoch');
  assert.deepEqual(closeCall.slice(1), [harness.activationEpochId, harness.readyCommitDigest]);
  assert.equal(harness.calls.filter(([name]) => name === 'runtime.stop').length, 0);
  assert.equal(harness.current().state, 'FAILED');
  assert.equal(harness.current().admission_state, 'CLOSED');
});

test('post-READY linked-action reporting failure does not roll back a ready runtime', async (t) => {
  const harness = finalizeTransactionFixture(t, {
    actionFinish: () => { throw codedError('ACTION_STORE_WRITE_FAILED', 'secondary reporting failed'); }
  });

  const result = await harness.coordinator.finalize(harness.activationEpochId);

  assert.equal(result.state, 'READY');
  assert.equal(result.admission_open, true);
  assert.equal(result.fully_ready, true);
  assert.equal(harness.calls.filter(([name]) => name === 'finishLinkedAction').length, 1);
  assert.equal(harness.calls.filter(([name]) => name === 'closeActivationEpoch').length, 0);
  assert.equal(harness.calls.filter(([name]) => name === 'runtime.stop').length, 0);
  assert.equal(harness.calls.filter(([name]) => name === 'fail').length, 0);
  assert.equal(harness.current().state, 'READY');
  assert.equal(harness.current().admission_state, 'OPEN');
});

test('expiry at commit, open, or durable READY boundary leaves admission closed', async (t) => {
  const cases = [
    {
      name: 'commitReady',
      options: { commitReadyError: codedError('ACTIVATION_REQUEST_EXPIRED') },
      completeCalls: 0,
      closeCalls: 0
    },
    {
      name: 'MCP open',
      options: { complete: async () => { throw codedError('ACTIVATION_REQUEST_EXPIRED'); } },
      completeCalls: 1,
      closeCalls: 0
    },
    {
      name: 'durable READY',
      options: { readyError: codedError('ACTIVATION_REQUEST_EXPIRED') },
      completeCalls: 1,
      closeCalls: 1
    }
  ];

  for (const item of cases) {
    await t.test(item.name, async (subtest) => {
      const harness = finalizeTransactionFixture(subtest, item.options);
      await assert.rejects(
        harness.coordinator.finalize(harness.activationEpochId),
        { code: 'ACTIVATION_REQUEST_EXPIRED' }
      );
      assert.equal(harness.calls.filter(([name]) => name === 'completeActivationEpoch').length, item.completeCalls);
      assert.equal(harness.calls.filter(([name]) => name === 'closeActivationEpoch').length, item.closeCalls);
      if (item.closeCalls === 1) {
        const closeCall = harness.calls.find(([name]) => name === 'closeActivationEpoch');
        assert.deepEqual(closeCall.slice(1), [harness.activationEpochId, harness.readyCommitDigest]);
      }
      assert.equal(harness.current().state, 'FAILED');
      assert.equal(harness.current().admission_state, 'CLOSED');
    });
  }
});

const censusSummaryWorkspace = 'E:\\workspace';
const censusSummarySnapshot = () => ({
  backup_api_copy: true,
  immutable: true,
  query_only: true,
  integrity_check: ['ok'],
  foreign_key_check_rows: 0,
  sha256: 'a'.repeat(64),
  logical_sha256: 'b'.repeat(64)
});
function censusSummaryRaw(overrides = {}) {
  return {
    snapshot: censusSummarySnapshot(),
    workspace: censusSummaryWorkspace,
    runs: [],
    managed_jobs: [],
    unbound_live_resources: [],
    summary: {},
    ...overrides
  };
}
const censusSummaryServiceJob = {
  job_id: '4d77511e155a49b985bc8794ae7913a1',
  classification: 'LIVE_OWNED',
  owner: 'codex-app-server',
  command_id: 'codex-app-server-1',
  resource_class: 'MEDIUM',
  lifecycle_state: 'running',
  root_pid: 29400,
  run_id: '',
  wave_id: '',
  job_updated_at: '2026-10-27T06:33:42.850Z'
};
const censusSummaryServiceEntry = {
  job_id: '4d77511e155a49b985bc8794ae7913a1',
  owner: 'codex-app-server',
  command_id: 'codex-app-server-1',
  resource_class: 'MEDIUM',
  lifecycle_state: 'running',
  root_pid: 29400,
  job_updated_at: '2026-10-27T06:33:42.850Z'
};
const censusSummaryTaskJob = {
  job_id: 'task-job-1',
  classification: 'LIVE_OWNED',
  lifecycle_state: 'running',
  root_pid: 12345,
  run_id: 'run-1',
  wave_id: 'wave-1',
  job_updated_at: '2026-10-27T06:33:42.850Z'
};

test('census summary discounts a live provider service job from managed work', () => {
  const result = summarizeCensus(censusSummaryRaw({
    managed_jobs: [censusSummaryServiceJob],
    live_service_jobs: [censusSummaryServiceEntry]
  }), { workspace: censusSummaryWorkspace });
  assert.equal(result.counts.active_managed_processes, 0);
  assert.equal(result.counts.owned_codex_sidecar_residues, 1);
  assert.equal(result.lifecycle.blockers.includes('active_runtime_work'), false);
  assert.equal(result.safe, true);
  assert.equal(result.code, 'READY');
  assert.deepEqual(result.live_service_jobs, [censusSummaryServiceEntry]);
});

test('census summary still counts a live task-work job as managed work', () => {
  const result = summarizeCensus(censusSummaryRaw({
    managed_jobs: [censusSummaryTaskJob]
  }), { workspace: censusSummaryWorkspace });
  assert.equal(result.counts.active_managed_processes, 1);
  assert.equal(result.counts.owned_codex_sidecar_residues, 0);
  assert.equal(result.lifecycle.blockers.includes('active_runtime_work'), true);
  assert.equal(result.safe, false);
});

test('census summary counts only task-work jobs when service and task jobs are mixed', () => {
  const result = summarizeCensus(censusSummaryRaw({
    managed_jobs: [censusSummaryServiceJob, censusSummaryTaskJob],
    live_service_jobs: [censusSummaryServiceEntry]
  }), { workspace: censusSummaryWorkspace });
  assert.equal(result.counts.active_managed_processes, 1);
  assert.equal(result.counts.owned_codex_sidecar_residues, 1);
  assert.equal(result.lifecycle.blockers.includes('active_runtime_work'), true);
  assert.equal(result.safe, false);
});

test('census summary without live_service_jobs behaves as before', () => {
  const result = summarizeCensus(censusSummaryRaw({
    managed_jobs: [censusSummaryServiceJob]
  }), { workspace: censusSummaryWorkspace });
  assert.equal(result.counts.active_managed_processes, 1);
  assert.equal(result.counts.owned_codex_sidecar_residues, 0);
  assert.equal(result.lifecycle.blockers.includes('active_runtime_work'), true);
  assert.equal(result.safe, false);
});

