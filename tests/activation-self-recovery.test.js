const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { RecoveryHost } = require('../electron/services/recoveryHost');

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'activation-self-recovery-'));
  const dataRoot = path.join(root, 'data');
  const resourcesRoot = path.join(root, 'resources');
  const appRoot = path.join(root, 'app');
  fs.mkdirSync(dataRoot, { recursive: true });
  fs.mkdirSync(resourcesRoot, { recursive: true });
  fs.mkdirSync(appRoot, { recursive: true });
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return createRuntimePaths({ dataRoot, resourcesRoot, appRoot });
}

test('Recovery Host supervision atomically fails an expired active epoch through FullCleanActivation and keeps component mutation suppressed', async (t) => {
  const paths = fixture(t);
  const revision = 'a'.repeat(64);
  const calls = { lightweight: 0, supervise: 0 };
  const orchestrator = {
    setFullCleanActivation() {},
    setFullCleanSourceCheckpointResolver() {},
    setActivationEpoch() {},
    codingMcpRevisionStatus: () => ({
      running_revision: revision,
      disk_revision: revision,
      update_pending: false,
      state: 'current'
    }),
    lightweightSnapshot: async () => {
      calls.lightweight += 1;
      return {
        mcpRunning: true,
        nativeAlive: true,
        tunnelRunning: true,
        componentsReady: false,
        connectorReady: false,
        fullyReady: false,
        updateIncomplete: true
      };
    },
    supervise: async () => {
      calls.supervise += 1;
      return { fullyReady: true };
    }
  };
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ workspace: path.dirname(paths.dataRoot()), autoStartServices: false }) },
    secrets: {},
    environment: {},
    log: { info() {}, warn() {}, error() {}, read: () => [], clear() {} },
    orchestrator,
    healthService: {},
    gateway: {},
    revisionTracker: {
      captureRunning: () => revision,
      status: (_component, running) => ({
        running_revision: running || revision,
        disk_revision: revision,
        update_pending: false,
        state: 'current'
      })
    },
    recoveryPlaneService: { setActivationEpoch() {} }
  });

  const createdAt = Date.now();
  const expiresAt = createdAt + 1000;
  const created = host.activationEpochStore.create({
    operation_id: 'activation-watchdog-expiry-0001',
    expires_at_unix_ms: expiresAt,
    component_evidence: {
      recovery_host: { instance_id: host.instanceId, pid: process.pid }
    }
  });
  host.activationEpochStore.update(created.activation_epoch_id, {
    state: 'VERIFYING',
    reason: 'connector-awaiting-proof'
  });
  host.activationEpochStore.now = () => expiresAt;
  host.fullCleanActivation.store.now = () => expiresAt;
  host.running = true;

  const snapshot = await host.superviseOnce();
  const current = host.activationEpochStore.current();

  assert.equal(current.activation_epoch_id, created.activation_epoch_id);
  assert.equal(current.state, 'FAILED');
  assert.equal(current.admission_state, 'CLOSED');
  assert.equal(current.error.code, 'ACTIVATION_REQUEST_EXPIRED');
  assert.equal(current.error.details.boundary, 'recovery_host_supervise');
  assert.equal(current.failed_at_unix_ms, expiresAt);
  assert.equal(calls.lightweight, 1, 'failed activation keeps the control-plane observation path alive');
  assert.equal(calls.supervise, 0, 'ordinary component supervision must remain suppressed after expiry');
  assert.equal(snapshot.fullyReady, false);
});
