const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const {
  RecoveryHost,
  acquireRecoveryHostLock,
  releaseRecoveryHostLock,
  waitForReplacementLockRelease
} = require('../electron/services/recoveryHost');

// Same dead-pid sentinel the existing recovery-host tests use: no live
// process ever holds it, on Windows or Linux.
const DEAD_PID = 99999999;

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-replacement-lock-'));
  const dataRoot = path.join(root, 'data');
  const resourcesRoot = path.join(root, 'resources');
  const appRoot = path.join(root, 'app');
  fs.mkdirSync(dataRoot, { recursive: true });
  fs.mkdirSync(resourcesRoot, { recursive: true });
  fs.mkdirSync(appRoot, { recursive: true });
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return createRuntimePaths({ dataRoot, resourcesRoot, appRoot });
}

function writeLock(paths, { pid, instance_id }) {
  fs.writeFileSync(paths.recoveryHostLockFile(), JSON.stringify({ pid, instance_id }), 'utf8');
}

function replacementHost(t, paths) {
  const revision = 'a'.repeat(64);
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ autoStartServices: false }) },
    secrets: {},
    environment: {},
    log: { info() {}, warn() {}, error() {}, read: () => [], clear() {} },
    orchestrator: {
      setFullCleanActivation() {},
      setActivationEpoch() {},
      codingMcpRevisionStatus: () => ({
        running_revision: revision,
        disk_revision: revision,
        update_pending: false,
        state: 'current'
      }),
      isManuallyStopped: () => false
    },
    healthService: {},
    gateway: { start: async () => {}, stop: async () => {} },
    revisionTracker: {
      captureRunning: () => revision,
      status: () => ({
        running_revision: revision,
        disk_revision: revision,
        update_pending: false,
        state: 'current'
      })
    },
    recoveryPlaneService: { setActivationEpoch() {} },
    ipcServerFactory: () => ({ start: async () => ({}), stop: async () => true }),
    processIdentityObserver: async (pid) => ({
      state: 'live',
      pid,
      process_start_token: '123456789'
    })
  });
  return host;
}

function seedVerifyingEpoch(host) {
  const created = host.activationEpochStore.create({
    operation_id: 'resume-after-handoff-operation-0001',
    expires_at_unix_ms: Date.now() + 600_000,
    component_evidence: {
      recovery_host: { instance_id: 'old-owner-27344', pid: 27344 }
    }
  });
  host.activationEpochStore.update(created.activation_epoch_id, {
    state: 'VERIFYING',
    reason: 'replacement-census'
  });
  return created;
}

test('waitForReplacementLockRelease treats a dead lock holder as released', async (t) => {
  const paths = fixture(t);
  writeLock(paths, { pid: DEAD_PID, instance_id: 'dead-owner-22656' });
  assert.equal(await waitForReplacementLockRelease(paths, 'expected-owner-27344', 1000), true);
  assert.equal(fs.existsSync(paths.recoveryHostLockFile()), false, 'the stale lock must be removed');
});

test('waitForReplacementLockRelease still rejects a live lock holder from another instance', async (t) => {
  const paths = fixture(t);
  writeLock(paths, { pid: process.pid, instance_id: 'live-other-owner' });
  await assert.rejects(
    waitForReplacementLockRelease(paths, 'expected-owner', 1000),
    { code: 'RECOVERY_REPLACEMENT_TARGET_CHANGED' }
  );
  assert.equal(fs.existsSync(paths.recoveryHostLockFile()), true, 'a live lock must not be removed');
});

test('waitForReplacementLockRelease returns when the expected holder releases the lock', async (t) => {
  const paths = fixture(t);
  writeLock(paths, { pid: process.pid, instance_id: 'expected-owner' });
  // The expected holder is waited on, not rejected: it releases the lock
  // mid-wait and the waiter proceeds.
  setTimeout(() => fs.rmSync(paths.recoveryHostLockFile(), { force: true }), 100);
  assert.equal(await waitForReplacementLockRelease(paths, 'expected-owner', 1000), true);
});

test('waitForReplacementLockRelease waits on the expected holder instead of failing it', async (t) => {
  const paths = fixture(t);
  writeLock(paths, { pid: process.pid, instance_id: 'expected-owner' });
  await assert.rejects(
    waitForReplacementLockRelease(paths, 'expected-owner', 1000),
    { code: 'RECOVERY_REPLACEMENT_TIMEOUT' }
  );
});

test('rebindCurrentRecoveryHost records the live host identity in epoch metadata', (t) => {
  const paths = fixture(t);
  const host = replacementHost(t, paths);
  const created = seedVerifyingEpoch(host);

  assert.equal(host.rebindCurrentRecoveryHost(), true);
  const current = host.activationEpochStore.current();
  assert.equal(current.activation_epoch_id, created.activation_epoch_id);
  assert.equal(current.metadata.current_recovery_host_instance_id, host.instanceId);
  assert.equal(current.metadata.current_recovery_host_pid, process.pid);
  assert.equal(
    current.component_evidence.recovery_host.instance_id,
    'old-owner-27344',
    'creation-time evidence must stay immutable'
  );
  assert.equal(host.rebindCurrentRecoveryHost(), false, 'a second rebind is a no-op');
});

test('Recovery Host resumes a VERIFYING epoch when the old lock holder is dead', async (t) => {
  const paths = fixture(t);
  const host = replacementHost(t, paths);
  const created = seedVerifyingEpoch(host);
  // 09/11 shape: the epoch still names the host that created it (27344)
  // while the lock is held by the host that died mid-VERIFYING (22656).
  writeLock(paths, { pid: DEAD_PID, instance_id: 'dead-owner-22656' });
  // The resume must reach ownership, not re-run the activation census.
  host.fullCleanActivation.continueReplacement = async () => ({ census: {} });
  t.after(() => host.stop());

  await host.start();

  const current = host.activationEpochStore.current();
  assert.equal(current.activation_epoch_id, created.activation_epoch_id);
  assert.equal(current.state, 'VERIFYING', 'the epoch must keep VERIFYING instead of FAILED');
  assert.equal(current.error, null);
  assert.equal(host.ownsLock, true);
  assert.equal(host.running, true);
  assert.equal(current.metadata.current_recovery_host_instance_id, host.instanceId);
  assert.equal(current.metadata.current_recovery_host_pid, process.pid);
  assert.equal(releaseRecoveryHostLock(paths, host.instanceId), true);
});
