'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const {
  TRUSTED_COMPONENT,
  trustedAttestation,
  normalizeTrustedAttestation,
  selectTrustedRecoveryHostSource,
  revalidateTrustedRecoveryHostSource
} = require('../electron/services/trustedRecoveryBootstrap');
const { run: runTrustedCommand, parseArgs } = require('../scripts/trusted-recovery-bootstrap');
const { run: runFullClean } = require('../scripts/full-clean-activation');

const HEAD = 'a'.repeat(40);

function checkpoint(id, createdAt = '2026-09-08T00:00:00.000Z') {
  return {
    checkpoint_id: id,
    run_id: `run-${id}`,
    wave_id: `wave-${id}`,
    proof_fingerprint: 'b'.repeat(64),
    git_head: HEAD,
    status: 'accepted',
    created_at: createdAt
  };
}

function evaluationFor(value, components = [TRUSTED_COMPONENT], receiptSha = 'c'.repeat(64)) {
  return {
    eligible: true,
    code: 'ACTIVATABLE',
    source_checkpoint_id: value.checkpoint_id,
    run_id: value.run_id,
    wave_id: value.wave_id,
    proof_fingerprint: value.proof_fingerprint,
    accepted_head: value.git_head,
    affected_components: components,
    receipts: [{
      path: 'electron/services/recoveryActionStore.js',
      state: 'file',
      sha256: receiptSha,
      size_bytes: 100,
      receipt_kind: 'durable_wave_patch_surface',
      run_id: value.run_id,
      wave_id: value.wave_id,
      restart_safe: true,
      content_addressed: true
    }]
  };
}

function selectionOptions(evaluations) {
  return {
    gitStatusFn: async () => ({ head: HEAD }),
    readAcceptedCheckpointsFn: () => [...evaluations.keys()],
    evaluateEligibilityFn: (value) => evaluations.get(value)
  };
}

test('trusted bootstrap chooses only the newest byte-exact recovery_host source at current HEAD', async () => {
  const coding = checkpoint('checkpoint-coding-mcp-0001', '2026-09-08T00:00:01.000Z');
  const recovery = checkpoint('checkpoint-recovery-host-0002', '2026-09-08T00:00:02.000Z');
  const newerRecovery = checkpoint('checkpoint-recovery-host-0003', '2026-09-08T00:00:03.000Z');
  const evaluations = new Map([
    [coding, evaluationFor(coding, ['coding_mcp'])],
    [recovery, evaluationFor(recovery)],
    [newerRecovery, evaluationFor(newerRecovery, [TRUSTED_COMPONENT], 'd'.repeat(64))]
  ]);

  const selected = await selectTrustedRecoveryHostSource('E:\\DEV\\Codex-web', selectionOptions(evaluations));

  assert.equal(selected.source_checkpoint.checkpoint_id, newerRecovery.checkpoint_id);
  assert.equal(selected.attestation.component, TRUSTED_COMPONENT);
  assert.match(selected.attestation.receipt_sha256, /^[a-f0-9]{64}$/);
  assert.equal(selected.receipt_count, 1);
});

test('trusted bootstrap rejects a zero-target or cross-component accepted checkpoint', async () => {
  const zero = checkpoint('checkpoint-zero-target-0001');
  const mixed = checkpoint('checkpoint-mixed-target-0002');
  const evaluations = new Map([
    [zero, evaluationFor(zero, [])],
    [mixed, evaluationFor(mixed, ['recovery_host', 'coding_mcp'])]
  ]);

  await assert.rejects(
    selectTrustedRecoveryHostSource('E:\\DEV\\Codex-web', selectionOptions(evaluations)),
    { code: 'TRUSTED_BOOTSTRAP_SOURCE_UNAVAILABLE' }
  );
});

test('trusted bootstrap revalidation rejects receipt drift and attestation substitution', async () => {
  const source = checkpoint('checkpoint-recovery-host-0004');
  const initial = evaluationFor(source);
  const attestation = trustedAttestation(initial);
  const options = selectionOptions(new Map([[source, evaluationFor(source, [TRUSTED_COMPONENT], 'e'.repeat(64))]]));

  await assert.rejects(
    revalidateTrustedRecoveryHostSource('E:\\DEV\\Codex-web', attestation.source_checkpoint, attestation, options),
    { code: 'TRUSTED_BOOTSTRAP_SOURCE_DRIFT' }
  );
  assert.throws(
    () => normalizeTrustedAttestation({ ...attestation, unexpected: true }, attestation.source_checkpoint),
    { code: 'TRUSTED_BOOTSTRAP_ATTESTATION_INVALID' }
  );
});

test('fixed trusted-bootstrap command derives authority itself and forwards no caller checkpoint', async () => {
  const workspace = path.resolve(__dirname, '..');
  const source = checkpoint('checkpoint-recovery-host-0005');
  const attestation = trustedAttestation(evaluationFor(source));
  const calls = [];
  const result = await runTrustedCommand({
    paths: { appRoot: () => workspace },
    selectTrustedRecoveryHostSourceFn: async (actualWorkspace) => {
      assert.equal(actualWorkspace, workspace);
      return { source_checkpoint: attestation.source_checkpoint, attestation, receipt_count: 1 };
    },
    assessDeferredHandoffFn: () => ({ ready: true, mode: 'recovery_supervisor', supervisor_pid: 777 }),
    deferExecuteFn: async (options) => {
      calls.push(options);
      return { ok: true, mode: 'deferred', operation_id: 'full-clean-cli-trusted-bootstrap-0001' };
    }
  });

  assert.equal(calls.length, 1);
  assert.deepEqual(calls[0].checkpoint, attestation.source_checkpoint);
  assert.deepEqual(calls[0].trustedRecoveryBootstrap, attestation);
  assert.equal(result.trusted_recovery_bootstrap.component, TRUSTED_COMPONENT);
  assert.equal(Object.hasOwn(calls[0], 'path'), false);
  assert.equal(Object.hasOwn(calls[0], 'pid'), false);
  assert.deepEqual(parseArgs([]), { preflight: false });
  assert.deepEqual(parseArgs(['--preflight']), { preflight: true });
  assert.throws(() => parseArgs(['--execute']), { code: 'TRUSTED_BOOTSTRAP_ARGUMENT_INVALID' });
});

test('fixed trusted-bootstrap preflight performs no durable operation', async () => {
  const workspace = path.resolve(__dirname, '..');
  const source = checkpoint('checkpoint-recovery-host-0006');
  const attestation = trustedAttestation(evaluationFor(source));
  let deferred = false;
  const result = await runTrustedCommand({
    argv: ['--preflight'],
    paths: { appRoot: () => workspace },
    selectTrustedRecoveryHostSourceFn: async () => ({ source_checkpoint: attestation.source_checkpoint, attestation, receipt_count: 1 }),
    assessDeferredHandoffFn: () => ({ ready: true, mode: 'recovery_supervisor', supervisor_pid: 778 }),
    deferExecuteFn: async () => { deferred = true; }
  });
  assert.equal(result.mutable_operation_started, false);
  assert.equal(result.deferred_handoff.ready, true);
  assert.equal(result.deferred_handoff.supervisor_pid, 778);
  assert.equal(deferred, false);
});

test('fixed trusted-bootstrap preflight fails closed without a current durable handoff owner', async () => {
  const workspace = path.resolve(__dirname, '..');
  const source = checkpoint('checkpoint-recovery-host-0008');
  const attestation = trustedAttestation(evaluationFor(source));
  await assert.rejects(
    runTrustedCommand({
      argv: ['--preflight'],
      paths: { appRoot: () => workspace },
      selectTrustedRecoveryHostSourceFn: async () => ({ source_checkpoint: attestation.source_checkpoint, attestation, receipt_count: 1 }),
      assessDeferredHandoffFn: () => ({
        ready: false,
        mode: 'recovery_supervisor',
        code: 'DEFERRED_SUPERVISOR_CAPABILITY_UNAVAILABLE'
      })
    }),
    { code: 'DEFERRED_SUPERVISOR_CAPABILITY_UNAVAILABLE' }
  );
});

test('trusted attestation forces exactly one recovery-host bootstrap even when the old host reports current', async () => {
  const workspace = path.resolve(__dirname, '..');
  const source = checkpoint('checkpoint-recovery-host-0007');
  const attestation = trustedAttestation(evaluationFor(source));
  const calls = [];
  const context = {
    paths: { appRoot: () => workspace, runtimeIdentity: () => ({ mode: 'development' }) },
    descriptor: { owner_pid: 111, instance_id: 'old-host-instance-0007' },
    client: { call: async () => { throw new Error('current host must not receive trusted activation directly'); } },
    requestOptions: {}
  };
  const result = await runFullClean({
    argv: ['--execute'],
    context,
    operationId: 'full-clean-cli-trusted-bootstrap-0007',
    now: 1_700_000_000_000,
    timeoutMs: 1_000,
    trustedRecoveryBootstrap: attestation,
    forceRecoveryHostBootstrap: true,
    revalidateTrustedSourceFn: async (actualWorkspace, actualCheckpoint, actualAttestation) => {
      assert.equal(actualWorkspace, workspace);
      assert.deepEqual(actualCheckpoint, attestation.source_checkpoint);
      assert.deepEqual(actualAttestation, attestation);
      return { source_checkpoint: actualCheckpoint, attestation: actualAttestation };
    },
    readAuthorityFn: async () => ({
      status: {},
      workspace,
      component: TRUSTED_COMPONENT,
      expectedDiskRevision: 'f'.repeat(64),
      freshness: { current: true }
    }),
    bootstrapCurrentRecoveryHostFn: async (options) => {
      calls.push(options);
      return { required: true, stale: true, pid: 222 };
    },
    waitForReplacementOperationFn: async () => ({
      operation: { operation_id: 'full-clean-cli-trusted-bootstrap-0007' },
      activationEpochId: 'trusted-epoch-0007'
    }),
    waitForReplacementReadyFn: async () => ({
      ready: true,
      status: {
        activation_epoch: { activation_epoch_id: 'trusted-epoch-0007', state: 'READY', admission_open: true },
        runtime: { fully_ready: true }
      }
    })
  }, { FULL_CLEAN_SOURCE_CHECKPOINT_JSON: JSON.stringify(attestation.source_checkpoint) });

  assert.equal(calls.length, 1);
  assert.equal(calls[0].forceRefresh, true);
  assert.deepEqual(calls[0].trustedRecoveryBootstrap, attestation);
  assert.equal(result.ok, true);
  assert.equal(result.fully_ready, true);
});
