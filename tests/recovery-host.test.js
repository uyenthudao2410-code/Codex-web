const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { DEVICE_ID_PATTERN, loadOrCreateDeviceIdentity } = require('../electron/services/deviceIdentity');
const {
  ComponentRevisionTracker,
  hashComponentRevision,
  recoveryHostLegacyV1Revision,
  RECOVERY_HOST_LEGACY_V1_CONTRACT,
  RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS
} = require('../electron/services/componentRevision');
const { RecoveryActionStore } = require('../electron/services/recoveryActionStore');
const { RecoveryActivation } = require('../electron/services/recoveryActivation');
const { RecoveryIpcClient, RecoveryIpcServer, RPC_ACTIONS } = require('../electron/services/recoveryIpc');
const {
  RecoveryHost,
  acquireRecoveryHostLock,
  releaseRecoveryHostLock
} = require('../electron/services/recoveryHost');
const {
  recoveryHostArguments,
  recoveryLoginItemArguments,
  electronUiArguments,
  spawnRecoveryHost,
  spawnElectronUi,
  assertActivationDeadline
} = require('../electron/services/recoveryHostLauncher');
const { replacementArguments, bootstrapArguments } = require('../electron/recoveryHost');

const SOURCE_CHECKPOINT = Object.freeze({
  checkpoint_id: 'checkpoint-recovery-host-0001',
  run_id: 'run-recovery-host-0001',
  wave_id: 'wave-recovery-host-0001',
  proof_fingerprint: 'c'.repeat(64),
  git_head: 'd'.repeat(40)
});

function activationLifecycle(operationId, sourceCheckpoint, fenced) {
  return {
    safe: true,
    code: 'READY',
    reason: 'idle',
    operation_id: operationId,
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
      snapshot: {
        backup_api_copy: true,
        immutable: true,
        query_only: true,
        integrity_check: ['ok'],
        foreign_key_check_rows: 0,
        sha256: 'e'.repeat(64),
        logical_sha256: 'f'.repeat(64)
      },
      unexplained_active_runs: 0,
      unbound_live_resource_residues: 0
    },
    source_checkpoint: { ok: true, code: 'ACTIVATABLE', ...sourceCheckpoint },
    fenced: fenced === true,
    fence_operation_id: fenced === true ? operationId : null
  };
}

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-recovery-host-'));
  const dataRoot = path.join(root, 'data');
  const resourcesRoot = path.join(root, 'resources');
  const appRoot = path.join(root, 'app');
  fs.mkdirSync(dataRoot, { recursive: true });
  fs.mkdirSync(resourcesRoot, { recursive: true });
  fs.mkdirSync(appRoot, { recursive: true });
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return createRuntimePaths({ dataRoot, resourcesRoot, appRoot });
}

function uiRecoveryFixture(t, { paths = fixture(t), revision = 'a'.repeat(64), spawnElectronUi = async () => 0 } = {}) {
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ autoStartServices: false }) },
    secrets: {},
    environment: {},
    log: { info() {}, warn() {}, error() {}, read: () => [], clear() {} },
    orchestrator: {
      codingMcpRevisionStatus: () => ({
        running_revision: revision,
        disk_revision: revision,
        update_pending: false,
        state: 'current'
      })
    },
    healthService: {},
    gateway: {},
    revisionTracker: {
      captureRunning: () => revision,
      status: (_component, running) => ({
        running_revision: running || null,
        disk_revision: revision,
        update_pending: false,
        state: running ? 'current' : 'unknown'
      })
    },
    spawnElectronUi
  });
  return { host, paths, revision };
}

function unauthorizedCall(descriptor) {
  return new Promise((resolve, reject) => {
    const body = Buffer.from(JSON.stringify({ action: 'recovery.ping', args: [] }));
    const request = http.request({
      host: '127.0.0.1',
      port: descriptor.port,
      path: '/v1/call',
      method: 'POST',
      headers: {
        Authorization: `Bearer ${'x'.repeat(43)}`,
        'Content-Type': 'application/json',
        'Content-Length': body.length
      }
    }, (response) => {
      response.resume();
      response.on('end', () => resolve(response.statusCode));
    });
    request.on('error', reject);
    request.end(body);
  });
}

test('RuntimePaths resolves backend state without importing Electron APIs', (t) => {
  const paths = fixture(t);
  assert.equal(paths.deviceFile(), path.join(paths.dataRoot(), 'device.json'));
  assert.equal(paths.settingsFile(), path.join(paths.dataRoot(), 'settings.json'));
  assert.equal(path.basename(paths.appRoot()), 'app');
  assert.equal(paths.recoveryHostDescriptorFile(), path.join(paths.dataRoot(), 'recovery-host.json'));
  assert.equal(paths.recoveryHostBootstrapFile('bootstrap-operation-0001'), path.join(paths.dataRoot(), 'recovery-host-bootstrap.bootstrap-operation-0001.json'));
  assert.equal(paths.recoveryHostBootstrapResultFile('bootstrap-operation-0001'), path.join(paths.dataRoot(), 'recovery-host-bootstrap.bootstrap-operation-0001.result.json'));
  assert.equal(paths.recoveryActionsFile(), path.join(paths.dataRoot(), 'recovery-actions.json'));
  assert.equal(paths.tunnelExecutable(), path.join(paths.resourcesRoot(), 'tools', 'tunnel-client.exe'));
});

test('device identity is stable per install, unique across installs, and corruption fails closed', (t) => {
  const firstPaths = fixture(t);
  const secondPaths = fixture(t);
  const first = loadOrCreateDeviceIdentity(firstPaths);
  const repeated = loadOrCreateDeviceIdentity(firstPaths);
  const second = loadOrCreateDeviceIdentity(secondPaths);

  assert.match(first.device_id, DEVICE_ID_PATTERN);
  assert.equal(repeated.device_id, first.device_id);
  assert.notEqual(second.device_id, first.device_id);
  assert.ok(first.display_name);

  fs.writeFileSync(firstPaths.deviceFile(), '{not-json', 'utf8');
  assert.throws(() => loadOrCreateDeviceIdentity(firstPaths), { code: 'DEVICE_IDENTITY_INVALID' });
});

test('Recovery IPC is loopback-only, authenticated, bounded, and allowlisted', async (t) => {
  const paths = fixture(t);
  let mutations = 0;
  const deviceIdentity = {
    version: 1,
    device_id: '12345678-1234-4123-8123-123456789abc',
    display_name: 'Recovery IPC test device',
    created_at: '2026-08-17T00:00:00.000Z'
  };
  const server = new RecoveryIpcServer({
    paths,
    instanceId: 'instance-one',
    startedAt: new Date().toISOString(),
    deviceIdentity,
    deviceInstanceId: 'device-instance-test-0001',
    log: { warn() {} },
    handlers: {
      'recovery.ping': async () => ({ ready: true }),
      'runtime.restart': async () => { mutations += 1; return { restarted: true }; }
    }
  });
  t.after(() => server.stop());
  const descriptor = await server.start();
  const client = new RecoveryIpcClient({ paths });
  assert.deepEqual(await client.ping(), { ready: true });
  assert.deepEqual(await client.restart(), { restarted: true });
  assert.equal(mutations, 1);
  assert.equal(await unauthorizedCall(descriptor), 401);
  await assert.rejects(client.call('shell.run', ['whoami']), { code: 'ACTION_NOT_ALLOWED' });
  assert.equal(descriptor.host, '127.0.0.1');
  assert.equal(descriptor.owner, 'recovery-host');
  assert.equal(descriptor.device_id, deviceIdentity.device_id);
  assert.equal(descriptor.device_instance_id, 'device-instance-test-0001');
});

test('Recovery Host lock rejects a second live owner and replaces a dead owner', (t) => {
  const paths = fixture(t);
  acquireRecoveryHostLock(paths, 'first-owner');
  assert.throws(() => acquireRecoveryHostLock(paths, 'second-owner'), { code: 'RECOVERY_HOST_ALREADY_RUNNING' });
  assert.equal(releaseRecoveryHostLock(paths, 'wrong-owner'), false);
  assert.equal(releaseRecoveryHostLock(paths, 'first-owner'), true);

  fs.writeFileSync(paths.recoveryHostLockFile(), JSON.stringify({ pid: 99999999, instance_id: 'dead-owner' }), 'utf8');
  const replacement = acquireRecoveryHostLock(paths, 'replacement');
  assert.equal(replacement.instance_id, 'replacement');
  assert.equal(releaseRecoveryHostLock(paths, 'replacement'), true);
});

test('Recovery Host owns supervision and IPC without stopping the runtime when UI exits', async (t) => {
  const paths = fixture(t);
  const calls = { supervise: 0, runtimeStop: 0, gatewayStart: 0, gatewayStop: 0 };
  const orchestrator = {
    isManuallyStopped: () => false,
    supervise: async () => {
      calls.supervise += 1;
      return { mcpRunning: true, tunnelRunning: true, fullyReady: true };
    },
    snapshot: async () => ({ status: { fullyReady: true } }),
    lightweightSnapshot: async () => ({ mcpRunning: true, tunnelRunning: true, fullyReady: true }),
    start: async () => ({ started: true }),
    stop: async () => { calls.runtimeStop += 1; return { stopped: true }; },
    restart: async () => ({ restarted: true }),
    switchWorkspace: async () => ({}),
    updateAuthorizedRoots: async () => ({}),
    acknowledgeConnectorContract: async () => ({})
  };
  const gateway = {
    server: null,
    start: async function start() { calls.gatewayStart += 1; this.server = {}; },
    stop: async function stop() { calls.gatewayStop += 1; this.server = null; },
    metrics() {
      return {
        measurement: 'resident_gateway_upstream_round_trip',
        by_kind: { mcp: { n: 3, p50_ms: 1, p90_ms: 2, p99_ms: 3, failures: 0, status_classes: { '2xx': 3 } } }
      };
    }
  };
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ autoStartServices: false }) },
    secrets: {},
    environment: {},
    log: { info() {}, warn() {}, error() {}, read: () => [], clear() {} },
    orchestrator,
    healthService: { inspect: async () => ({}), repair: async () => ({}) },
    gateway
  });
  t.after(() => host.stop());
  await host.start();
  await host.superviseOnce();
  const client = new RecoveryIpcClient({ paths });
  const snapshot = await client.snapshot();
  const persistedDevice = loadOrCreateDeviceIdentity(paths);
  const descriptor = JSON.parse(fs.readFileSync(paths.recoveryHostDescriptorFile(), 'utf8'));
  assert.equal(snapshot.status.fullyReady, false);
  assert.equal(snapshot.updateIncomplete, true);
  assert.equal(snapshot.recoveryHost.runtime.fully_ready, false);
  assert.equal(snapshot.recoveryHost.runtime.connector_ready, false);
  assert.equal(snapshot.recoveryHost.state, 'healthy');
  assert.equal(snapshot.recoveryHost.device_id, persistedDevice.device_id);
  assert.equal(snapshot.recoveryHost.device_instance_id, host.instanceId);
  assert.equal(snapshot.device.scope, 'current_device_only');
  assert.equal(snapshot.device.device_id, persistedDevice.device_id);
  assert.equal(snapshot.device.device_instance_id, host.instanceId);
  assert.equal(descriptor.device_id, persistedDevice.device_id);
  assert.equal(descriptor.device_instance_id, host.instanceId);
  assert.equal(snapshot.recoveryHost.code_revision.state, 'current');
  assert.equal(snapshot.recoveryHost.code_revision.update_pending, false);
  assert.equal(snapshot.recoveryHost.gateway_metrics.measurement, 'resident_gateway_upstream_round_trip');
  assert.equal(snapshot.recoveryHost.gateway_metrics.by_kind.mcp.p90_ms, 2);
  assert.equal(calls.gatewayStart, 1);
  assert.equal(calls.supervise, 1);

  await host.stop();
  assert.equal(calls.runtimeStop, 0);
  assert.equal(calls.gatewayStop, 1);
  assert.equal(fs.existsSync(paths.recoveryHostLockFile()), false);
  assert.equal(fs.existsSync(paths.recoveryHostDescriptorFile()), false);
});

test('new unsuppressed Recovery Host relaunches UI after initial registration grace expires', async (t) => {
  let launches = 0;
  const { host } = uiRecoveryFixture(t, {
    spawnElectronUi: async () => { launches += 1; return 42000 + launches; }
  });

  assert.equal(host.uiRecoveryStatus().state, 'awaiting_initial_registration');
  assert.ok(host.uiRecoveryStatus().initial_registration_grace_until_unix_ms > Date.now());
  await host.superviseElectronUi();
  assert.equal(launches, 0, 'initial grace must allow an already-running UI to re-register after host replacement');

  host.uiRecoveryInitialGraceUntil = 0;
  await Promise.all([host.superviseElectronUi(), host.superviseElectronUi()]);
  assert.equal(launches, 1, 'missing UI must be relaunched by Recovery Host itself after grace');
  assert.equal(host.uiRecoveryStatus().state, 'waiting_for_registration');
  await host.superviseElectronUi();
  assert.equal(launches, 1, 'registration grace/cooldown must prevent duplicate UI launches');
});

test('Recovery Host relaunches a previously registered UI when its process dies unexpectedly', async (t) => {
  let launches = 0;
  const { host, revision } = uiRecoveryFixture(t, {
    revision: 'b'.repeat(64),
    spawnElectronUi: async () => { launches += 1; return 42500 + launches; }
  });
  host.activation.uiRegistration = {
    instance_id: 'lost-electron-ui-0001',
    pid: 99999999,
    revision,
    started_at_unix_ms: Date.now() - 1000,
    registered_at_unix_ms: Date.now() - 900
  };
  host.uiRecoveryInitialGraceUntil = 0;

  await Promise.all([host.superviseElectronUi(), host.superviseElectronUi()]);
  assert.equal(launches, 1);
  assert.equal(host.uiRecoveryStatus().registered, true);
  assert.equal(host.uiRecoveryStatus().alive, false);
  assert.equal(host.uiRecoveryStatus().state, 'waiting_for_registration');
});

test('explicit operator quit suppression survives Recovery Host replacement and blocks default-armed recovery', async (t) => {
  const paths = fixture(t);
  let launches = 0;
  const options = {
    paths,
    revision: 'c'.repeat(64),
    spawnElectronUi: async () => { launches += 1; return 43000 + launches; }
  };
  const { host, revision } = uiRecoveryFixture(t, options);
  const first = {
    instance_id: 'electron-ui-live-0001',
    pid: process.pid,
    revision,
    started_at_unix_ms: Date.now()
  };
  await host.handlers()['client.register_ui_revision'](first);
  await assert.rejects(
    Promise.resolve().then(() => host.handlers()['client.suppress_ui_recovery']({
      instance_id: 'wrong-electron-ui-0001',
      reason: 'operator_quit'
    })),
    { code: 'UI_RECOVERY_INSTANCE_MISMATCH' }
  );
  const suppression = await host.handlers()['client.suppress_ui_recovery']({
    instance_id: first.instance_id,
    reason: 'operator_quit'
  });
  assert.equal(suppression.suppressed, true);

  const { host: replacementHost } = uiRecoveryFixture(t, options);
  assert.equal(replacementHost.activation.uiRecoveryPreferenceStatus().suppressed, true);
  assert.equal(replacementHost.uiRecoveryStatus().state, 'suppressed');
  replacementHost.uiRecoveryInitialGraceUntil = 0;
  await replacementHost.superviseElectronUi();
  assert.equal(launches, 0, 'explicit operator quit must remain off across Recovery Host replacement');

  await replacementHost.handlers()['client.register_ui_revision']({
    instance_id: 'electron-ui-live-0002',
    pid: process.pid,
    revision,
    started_at_unix_ms: Date.now()
  });
  assert.equal(replacementHost.activation.uiRecoveryPreferenceStatus().suppressed, false);
  assert.equal(replacementHost.uiRecoveryStatus().state, 'healthy');
});

test('UI watchdog defers to a pending controlled electron activation', async (t) => {
  let launches = 0;
  const { host, revision } = uiRecoveryFixture(t, {
    revision: 'd'.repeat(64),
    spawnElectronUi: async () => { launches += 1; return 44000; }
  });
  host.uiRecoveryInitialGraceUntil = 0;
  const now = Date.now();
  host.activation.actions.begin({
    operation_id: 'operation-ui-pending-0001',
    component: 'electron_ui',
    requested_at_unix_ms: now,
    expires_at_unix_ms: now + 30_000,
    expected_disk_revision: revision,
    allow_acceptance_pending: false
  });
  await host.superviseElectronUi();
  assert.equal(launches, 0);
  assert.equal(host.uiRecoveryStatus().state, 'activation_pending');
});

test('Recovery Host reports a source change as pending without restarting itself', (t) => {
  const paths = fixture(t);
  const source = path.join(paths.appRoot(), 'electron', 'services', 'recoveryHost.js');
  fs.mkdirSync(path.dirname(source), { recursive: true });
  fs.writeFileSync(source, 'module.exports = { version: 1 };\n');
  const revisionTracker = new ComponentRevisionTracker({ paths, refreshIntervalMs: 0 });
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ autoStartServices: false }) },
    secrets: {},
    environment: {},
    log: { info() {}, warn() {}, error() {}, read: () => [], clear() {} },
    orchestrator: {},
    healthService: {},
    gateway: {},
    revisionTracker
  });
  const before = host.hostStatus().code_revision;
  fs.writeFileSync(source, 'module.exports = { version: 2 };\n');
  const after = host.hostStatus().code_revision;
  assert.equal(before.state, 'current');
  assert.equal(after.running_revision, before.running_revision);
  assert.notEqual(after.disk_revision, before.disk_revision);
  assert.equal(after.update_pending, true);
  assert.equal(after.state, 'update_pending');
  assert.equal(host.running, false);
});

test('Recovery Host replacement hands off ownership without stopping Coding MCP or tunnel', async (t) => {
  const paths = fixture(t);
  const oldRevision = 'a'.repeat(64);
  const newRevision = 'b'.repeat(64);
  const calls = { runtimeStop: 0, oldExit: 0, cancelFence: 0 };
  const makeOrchestrator = () => ({
    isManuallyStopped: () => false,
    supervise: async () => ({ mcpRunning: true, nativeAlive: true, tunnelRunning: true, fullyReady: true }),
    lightweightSnapshot: async () => ({ mcpRunning: true, nativeAlive: true, tunnelRunning: true, fullyReady: true }),
    codingMcpRevisionStatus: () => ({ running_revision: oldRevision, disk_revision: oldRevision, update_pending: false, state: 'current' }),
    inspectCodeActivation: async () => ({ safe: true, code: 'READY' }),
    prepareCodeActivation: async ({ operationId, sourceCheckpoint }) => (
      activationLifecycle(operationId, sourceCheckpoint, true)
    ),
    cancelCodeActivation: async () => { calls.cancelFence += 1; return true; },
    verifyCodeActivation: async (operationId, sourceCheckpoint) => (
      activationLifecycle(operationId, sourceCheckpoint, false)
    ),
    start: async () => ({}),
    stop: async () => { calls.runtimeStop += 1; },
    restart: async () => ({}),
    snapshot: async () => ({}),
    switchWorkspace: async () => ({}),
    updateAuthorizedRoots: async () => ({}),
    acknowledgeConnectorContract: async () => ({})
  });
  const makeGateway = () => ({
    server: null,
    start: async function start() { this.server = {}; },
    stop: async function stop() { this.server = null; }
  });
  const makeIpc = () => ({ start: async () => ({}), stop: async () => true });
  const tracker = (runningRevision) => ({
    captureRunning: () => runningRevision,
    status: (_component, supplied) => ({
      running_revision: supplied || null,
      disk_revision: newRevision,
      update_pending: Boolean(supplied && supplied !== newRevision),
      state: supplied === newRevision ? 'current' : 'update_pending'
    })
  });
  const settings = { load: () => ({ autoStartServices: true }) };
  const common = {
    paths,
    settings,
    secrets: {},
    environment: {},
    log: { info() {}, warn() {}, error() {}, read: () => [], clear() {} },
    healthService: { inspect: async () => ({}), repair: async () => ({}) },
    ipcServerFactory: makeIpc
  };
  let replacementHost;
  let replacementStarted;
  const oldHost = new RecoveryHost({
    ...common,
    orchestrator: makeOrchestrator(),
    gateway: makeGateway(),
    revisionTracker: tracker(oldRevision),
    exitProcess: () => { calls.oldExit += 1; },
    spawnRecoveryReplacement: async (replacement) => {
      replacementHost = new RecoveryHost({
        ...common,
        orchestrator: makeOrchestrator(),
        gateway: makeGateway(),
        revisionTracker: tracker(newRevision),
        actionStore: new RecoveryActionStore({ paths }),
        replacement
      });
      replacementStarted = replacementHost.start();
      return process.pid;
    }
  });
  await oldHost.start();
  const now = Date.now();
  const activation = await oldHost.activation.activate({
    operation_id: 'replacement-operation-0001',
    component: 'recovery_host',
    requested_at_unix_ms: now,
    expires_at_unix_ms: now + 60_000,
    expected_disk_revision: newRevision,
    allow_acceptance_pending: false,
    source_checkpoint: {
      checkpoint_id: 'checkpoint-replacement-0001',
      run_id: 'run-replacement-0001',
      wave_id: 'wave-replacement-0001',
      proof_fingerprint: 'c'.repeat(64),
      git_head: 'd'.repeat(40)
    }
  });
  assert.equal(activation.state, 'accepted');
  await replacementStarted;
  for (let index = 0; index < 50 && calls.oldExit === 0; index += 1) {
    await new Promise((resolve) => setTimeout(resolve, 20));
  }
  assert.equal(oldHost.activation.status('replacement-operation-0001').state, 'completed');
  assert.equal(replacementHost.running, true);
  assert.equal(replacementHost.deviceIdentity.device_id, oldHost.deviceIdentity.device_id);
  assert.notEqual(replacementHost.deviceInstanceId, oldHost.deviceInstanceId);
  assert.equal(calls.runtimeStop, 0);
  assert.equal(calls.oldExit, 1);
  assert.equal(calls.cancelFence, 1);
  await replacementHost.stop();
});

test('Recovery Host handoff drains in-flight supervision before releasing ownership', async (t) => {
  const paths = fixture(t);
  const oldRevision = 'a'.repeat(64);
  const newRevision = 'b'.repeat(64);
  let releaseRecoveryEnsure;
  let recoveryEnsureCalls = 0;
  let recoveryEnsureStarted;
  const recoveryEnsureStartedPromise = new Promise((resolve) => { recoveryEnsureStarted = resolve; });
  const recoveryPlaneService = {
    preflightLegacyOwnershipMigration: async () => ({ required: false }),
    applyLegacyOwnershipMigration: async () => false,
    ensure: async () => {
      recoveryEnsureCalls += 1;
      if (recoveryEnsureCalls === 1) return { state: 'healthy' };
      if (recoveryEnsureCalls === 2) {
        recoveryEnsureStarted();
        await new Promise((resolve) => { releaseRecoveryEnsure = resolve; });
      }
      return { state: 'healthy' };
    }
  };
  const orchestrator = {
    isManuallyStopped: () => false,
    supervise: async () => ({ mcpRunning: true, nativeAlive: true, tunnelRunning: true, fullyReady: true }),
    lightweightSnapshot: async () => ({ mcpRunning: true, nativeAlive: true, tunnelRunning: true, fullyReady: true }),
    codingMcpRevisionStatus: () => ({ running_revision: oldRevision, disk_revision: oldRevision, update_pending: false, state: 'current' }),
    inspectCodeActivation: async () => ({ safe: true, code: 'READY' }),
    prepareCodeActivation: async ({ operationId, sourceCheckpoint }) => (
      activationLifecycle(operationId, sourceCheckpoint, true)
    ),
    cancelCodeActivation: async () => true,
    ensureToken: async () => 'x'.repeat(32),
    preflightLegacyDeviceMigration: async () => ({ required: false }),
    start: async () => ({}),
    snapshot: async () => ({}),
    switchWorkspace: async () => ({}),
    updateAuthorizedRoots: async () => ({}),
    acknowledgeConnectorContract: async () => ({})
  };
  const revisionTracker = {
    captureRunning: () => oldRevision,
    status: (_component, supplied) => ({
      running_revision: supplied || null,
      disk_revision: newRevision,
      update_pending: supplied !== newRevision,
      state: supplied === newRevision ? 'current' : 'update_pending'
    })
  };
  const gateway = {
    server: null,
    start: async function start() { this.server = {}; },
    stop: async function stop() { this.server = null; }
  };
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ autoStartServices: false }) },
    secrets: { get: () => 'runtime-key' },
    environment: {},
    log: { info() {}, warn() {}, error() {}, read: () => [], clear() {} },
    orchestrator,
    healthService: { inspect: async () => ({}), repair: async () => ({}) },
    gateway,
    ipcServerFactory: () => ({ start: async () => ({}), stop: async () => true }),
    revisionTracker,
    recoveryPlaneService,
    spawnRecoveryReplacement: async () => process.pid,
    exitProcess: () => {}
  });
  host.replacementWaitMs = 50;
  host.handoffSupervisionDrainMs = 1000;
  t.after(async () => {
    releaseRecoveryEnsure?.();
    await host.stop();
  });
  await host.start();

  const supervision = host.superviseOnce();
  await recoveryEnsureStartedPromise;
  const now = Date.now();
  const operationId = 'replacement-supervision-drain-0001';
  assert.equal((await host.activation.activate({
    operation_id: operationId,
    component: 'recovery_host',
    requested_at_unix_ms: now,
    expires_at_unix_ms: now + 60_000,
    expected_disk_revision: newRevision,
    allow_acceptance_pending: false,
    source_checkpoint: { ...SOURCE_CHECKPOINT }
  })).state, 'accepted');

  await new Promise((resolve) => setTimeout(resolve, 150));
  assert.equal(fs.existsSync(paths.recoveryHostLockFile()), true, 'handoff must keep ownership while old supervision is still mutating Recovery Plane');
  const callsBefore = recoveryEnsureCalls;
  await host.superviseOnce();
  assert.equal(recoveryEnsureCalls, callsBefore, 'handoff fence must suppress new supervision work');

  releaseRecoveryEnsure();
  await supervision;
  let status = host.activation.status(operationId);
  for (let index = 0; index < 100 && status.state === 'accepted'; index += 1) {
    await new Promise((resolve) => setTimeout(resolve, 10));
    status = host.activation.status(operationId);
  }
  assert.equal(status.state, 'failed');
  assert.equal(status.error.code, 'RECOVERY_REPLACEMENT_FAILED');
  assert.equal(host.running, true, 'old host must resume when no replacement takes ownership');
  assert.equal(host.ownsLock, true);
});

test('Recovery Host verifies replacement revision before any legacy device migration', () => {
  const source = fs.readFileSync(path.join(__dirname, '..', 'electron', 'services', 'recoveryHost.js'), 'utf8');
  const verify = source.indexOf('verifyRecoveryReplacement(this.replacement.operationId)');
  const primaryPreflight = source.indexOf('preflightLegacyDeviceMigration()');
  const recoveryPreflight = source.indexOf('preflightLegacyOwnershipMigration(current, authToken)');
  const complete = source.indexOf('completeRecoveryReplacement(');
  const primaryApply = source.indexOf('applyLegacyDeviceMigration(primaryLegacyMigration)');
  assert.ok(verify >= 0 && primaryPreflight > verify && recoveryPreflight > verify);
  assert.ok(complete > verify && primaryApply > complete);
});

test('Recovery replacement accepts the pinned legacy revision contract and rejects added-file tampering', (t) => {
  const paths = fixture(t);
  for (const relative of Object.keys(RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS)) {
    const target = path.join(paths.appRoot(), ...relative.split('/'));
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(path.join(__dirname, '..', ...relative.split('/')), target);
  }
  const relative = 'electron/services/deviceIdentity.js';
  const target = path.join(paths.appRoot(), ...relative.split('/'));
  const currentRevision = hashComponentRevision(paths.appRoot(), 'recovery_host').revision;
  const legacyRevision = recoveryHostLegacyV1Revision(paths.appRoot()).revision;
  const now = Date.now();
  const operationId = 'legacy-revision-bridge-0001';
  const actions = new RecoveryActionStore({ paths, now: () => now });
  actions.begin({
    operation_id: operationId,
    component: 'recovery_host',
    requested_at_unix_ms: now,
    expires_at_unix_ms: now + 60_000,
    expected_disk_revision: legacyRevision,
    allow_acceptance_pending: true
  });
  const activation = new RecoveryActivation({
    paths,
    revisions: { status: () => ({ running_revision: currentRevision, disk_revision: currentRevision, update_pending: false, state: 'current' }) },
    orchestrator: {},
    log: {},
    recoveryInstanceId: 'legacy-bridge-instance-0001',
    recoveryRunningRevision: currentRevision,
    actionStore: actions,
    now: () => now
  });
  const verified = activation.verifyRecoveryReplacement(operationId);
  assert.equal(verified.revisionContract, RECOVERY_HOST_LEGACY_V1_CONTRACT);
  assert.equal(verified.legacyBridge.revision, legacyRevision);
  fs.appendFileSync(target, '\n// tampered after activation request\n');
  assert.throws(() => activation.verifyRecoveryReplacement(operationId), { code: 'REVISION_VERIFICATION_FAILED' });
});

test('Recovery Host resumes ownership and releases the fence when replacement does not start', async (t) => {
  const paths = fixture(t);
  const oldRevision = 'a'.repeat(64);
  const newRevision = 'b'.repeat(64);
  const calls = { runtimeStop: 0, cancelFence: 0, exit: 0 };
  const orchestrator = {
    isManuallyStopped: () => false,
    supervise: async () => ({ mcpRunning: true, nativeAlive: true, tunnelRunning: true, fullyReady: true }),
    lightweightSnapshot: async () => ({ mcpRunning: true, nativeAlive: true, tunnelRunning: true, fullyReady: true }),
    codingMcpRevisionStatus: () => ({ running_revision: oldRevision, disk_revision: oldRevision, update_pending: false, state: 'current' }),
    inspectCodeActivation: async () => ({ safe: true, code: 'READY' }),
    prepareCodeActivation: async ({ operationId, sourceCheckpoint }) => (
      activationLifecycle(operationId, sourceCheckpoint, true)
    ),
    cancelCodeActivation: async () => { calls.cancelFence += 1; return true; },
    start: async () => ({}),
    stop: async () => { calls.runtimeStop += 1; },
    restart: async () => ({}),
    snapshot: async () => ({}),
    switchWorkspace: async () => ({}),
    updateAuthorizedRoots: async () => ({}),
    acknowledgeConnectorContract: async () => ({})
  };
  const revisionTracker = {
    captureRunning: () => oldRevision,
    status: (_component, supplied) => ({
      running_revision: supplied || null,
      disk_revision: newRevision,
      update_pending: supplied !== newRevision,
      state: supplied === newRevision ? 'current' : 'update_pending'
    })
  };
  const gateway = {
    server: null,
    start: async function start() { this.server = {}; },
    stop: async function stop() { this.server = null; }
  };
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ autoStartServices: false }) },
    secrets: {},
    environment: {},
    log: { info() {}, warn() {}, error() {}, read: () => [], clear() {} },
    orchestrator,
    healthService: { inspect: async () => ({}), repair: async () => ({}) },
    gateway,
    ipcServerFactory: () => ({ start: async () => ({}), stop: async () => true }),
    revisionTracker,
    spawnRecoveryReplacement: async () => process.pid,
    exitProcess: () => { calls.exit += 1; }
  });
  host.replacementWaitMs = 50;
  t.after(() => host.stop());
  await host.start();
  const now = Date.now();
  const operationId = 'replacement-operation-failure-0001';
  assert.equal((await host.activation.activate({
    operation_id: operationId,
    component: 'recovery_host',
    requested_at_unix_ms: now,
    expires_at_unix_ms: now + 60_000,
    expected_disk_revision: newRevision,
    allow_acceptance_pending: false,
    source_checkpoint: { ...SOURCE_CHECKPOINT }
  })).state, 'accepted');

  let status = host.activation.status(operationId);
  for (let index = 0; index < 100 && status.state === 'accepted'; index += 1) {
    await new Promise((resolve) => setTimeout(resolve, 10));
    status = host.activation.status(operationId);
  }

  assert.equal(status.state, 'failed');
  assert.equal(status.error.code, 'RECOVERY_REPLACEMENT_FAILED');
  assert.equal(host.running, true);
  assert.equal(host.ownsLock, true);
  assert.ok(gateway.server);
  assert.equal(calls.cancelFence, 1);
  assert.equal(calls.runtimeStop, 0);
  assert.equal(calls.exit, 0);
});

test('Recovery Host launch arguments preserve the app root in development', () => {
  assert.deepEqual(recoveryHostArguments({ isPackaged: true, getAppPath: () => 'ignored' }), ['--recovery-host']);
  assert.deepEqual(recoveryHostArguments({ isPackaged: false, getAppPath: () => 'E:\\app' }), ['E:\\app', '--recovery-host']);
  assert.deepEqual(electronUiArguments({ isPackaged: true, getAppPath: () => 'ignored' }), []);
  assert.deepEqual(electronUiArguments({ isPackaged: false, getAppPath: () => 'E:\\app' }), ['E:\\app']);
  assert.deepEqual(recoveryLoginItemArguments({ isPackaged: false, getAppPath: () => 'E:\\app path' }), ['"E:\\app path"', '--recovery-host']);
  assert.deepEqual(recoveryHostArguments({ isPackaged: false, getAppPath: () => 'E:\\app' }, {
    expectedOldInstanceId: 'old-instance-0000001',
    operationId: 'operation-000000001',
    activationEpochId: 'epoch-activation-0001'
  }), [
    'E:\\app',
    '--recovery-host',
    '--replace-recovery-host=old-instance-0000001',
    '--activation-operation=operation-000000001',
    '--activation-epoch-id=epoch-activation-0001'
  ]);
  assert.deepEqual(electronUiArguments({ isPackaged: false, getAppPath: () => 'E:\\app' }, {
    activationEpochId: 'epoch-activation-0001'
  }), ['E:\\app', '--activation-epoch-id=epoch-activation-0001']);
  assert.deepEqual(recoveryHostArguments({ isPackaged: true, getAppPath: () => 'ignored' }, {
    bootstrapId: 'bootstrap-operation-0001'
  }), ['--recovery-host', '--recovery-bootstrap=bootstrap-operation-0001']);
  assert.deepEqual(bootstrapArguments(['electron.exe', '--recovery-bootstrap=bootstrap-operation-0001']), {
    operationId: 'bootstrap-operation-0001'
  });
  assert.deepEqual(replacementArguments([
    'electron.exe',
    '--replace-recovery-host=old-instance-0000001',
    '--activation-operation=operation-000000001',
    '--activation-epoch-id=epoch-activation-0001'
  ]), {
    expectedOldInstanceId: 'old-instance-0000001',
    operationId: 'operation-000000001',
    activationEpochId: 'epoch-activation-0001'
  });
  assert.deepEqual(replacementArguments(['electron.exe', '--activation-epoch-id=epoch-activation-0001']), {
    activationEpochId: 'epoch-activation-0001'
  });
  assert.throws(() => recoveryHostArguments({ isPackaged: true }, { activationEpochId: 'bad epoch' }), {
    code: 'INVALID_ACTIVATION_EPOCH_ID'
  });
  assert.throws(() => replacementArguments(['electron.exe', '--activation-epoch-id=bad epoch']), {
    code: 'RECOVERY_REPLACEMENT_ARGUMENTS_INVALID'
  });
});

test('activation launchers propagate the epoch through argv and child environment', async () => {
  const app = { isPackaged: true, getAppPath: () => 'ignored' };
  const launches = [];
  const spawnProcess = (command, args, options) => {
    const child = {
      pid: 42001 + launches.length,
      once(event, listener) { if (event === 'spawn') queueMicrotask(listener); return this; },
      unref() {}
    };
    launches.push({ command, args, options });
    return child;
  };
  const options = { activationEpochId: 'epoch-activation-0001' };
  await spawnRecoveryHost(app, spawnProcess, options);
  await spawnElectronUi(app, spawnProcess, options);
  await spawnRecoveryHost(app, spawnProcess, { bootstrapId: 'bootstrap-operation-0001' });
  assert.deepEqual(launches.map((item) => item.args), [
    ['--recovery-host', '--activation-epoch-id=epoch-activation-0001'],
    ['--activation-epoch-id=epoch-activation-0001'],
    ['--recovery-host', '--recovery-bootstrap=bootstrap-operation-0001']
  ]);
  assert.equal(launches[0].options.env.CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID, 'epoch-activation-0001');
  assert.equal(launches[1].options.env.CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID, 'epoch-activation-0001');
  assert.equal(launches[0].options.env.WEBCODEX_PROCESS_ROLE, 'recovery-host');
  assert.equal(launches[1].options.env.WEBCODEX_PROCESS_ROLE, 'electron-ui');
  assert.equal(launches[2].options.env.WEBCODEX_RECOVERY_BOOTSTRAP_ID, 'bootstrap-operation-0001');
});

test('activation launchers reject expired requests before invoking the process spawn boundary', async () => {
  const app = { isPackaged: true, getAppPath: () => 'ignored' };
  let spawnCalls = 0;
  const spawnProcess = () => {
    spawnCalls += 1;
    throw new Error('spawn must not be reached');
  };
  const expired = { expiresAtUnixMs: Date.now() - 1 };
  await assert.rejects(spawnRecoveryHost(app, spawnProcess, expired), { code: 'ACTIVATION_REQUEST_EXPIRED' });
  await assert.rejects(spawnElectronUi(app, spawnProcess, expired), { code: 'ACTIVATION_REQUEST_EXPIRED' });
  assert.throws(() => assertActivationDeadline(expired, 'before_ui_relaunch'), {
    code: 'ACTIVATION_REQUEST_EXPIRED'
  });
  assert.equal(spawnCalls, 0);
});

test('Electron main delegates runtime ownership to Recovery Host', () => {
  const root = path.resolve(__dirname, '..');
  const main = fs.readFileSync(path.join(root, 'electron', 'main.js'), 'utf8');
  const host = fs.readFileSync(path.join(root, 'electron', 'services', 'recoveryHost.js'), 'utf8');
  assert.doesNotMatch(main, /new RuntimeOrchestrator/);
  assert.doesNotMatch(main, /new HubProxyGateway/);
  assert.match(main, /ensureRecoveryHost/);
  assert.match(host, /new RuntimeOrchestrator/);
  assert.match(host, /new HubProxyGateway/);
  assert.match(host, /orchestrator\.supervise\(\)/);
  assert.match(main, /assertActivationDeadline\(\{ expiresAtUnixMs: result\.expires_at_unix_ms \}, 'before_ui_relaunch'\)/);
  assert.match(main, /orchestrator\.activationStatus\(result\.operation_id\)/);
  assert.match(main, /suppressUiRecovery\(reason\)/);
  assert.match(main, /quitUi\('operator_quit'\)/);
  assert.equal(RPC_ACTIONS.includes('client.suppress_ui_recovery'), true);
});

test('Recovery Host restart resolves the current accepted checkpoint and rejects caller drift', async (t) => {
  const paths = fixture(t);
  const calls = [];
  const closureInput = {
    schema_version: 1,
    source_accepted: true,
    accepted_receipts_complete: true,
    component_receipts_valid: true,
    activation_eligible: true,
    eligibility_code: 'ACTIVATABLE',
    affected_components: ['recovery_host'],
    affected_components_valid: true,
    source_checkpoint_id: SOURCE_CHECKPOINT.checkpoint_id,
    run_id: SOURCE_CHECKPOINT.run_id,
    wave_id: SOURCE_CHECKPOINT.wave_id,
    proof_fingerprint: SOURCE_CHECKPOINT.proof_fingerprint,
    accepted_head: SOURCE_CHECKPOINT.git_head
  };
  const orchestrator = {
    setFullCleanActivation() {},
    setFullCleanSourceCheckpointResolver(resolver) { this.checkpointResolver = resolver; },
    completeActivationEpoch: async () => ({}),
    activationEpochStatus: () => ({ state: 'NONE', admission_open: true, update_incomplete: false }),
    codingMcpRevisionStatus: () => ({
      running_revision: 'a'.repeat(64),
      disk_revision: 'a'.repeat(64),
      update_pending: false,
      state: 'current'
    })
  };
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ autoStartServices: false, workspace: 'C:\\work\\one' }) },
    secrets: {},
    environment: {},
    log: { info() {}, warn() {}, error() {}, read: () => [], clear() {} },
    orchestrator,
    healthService: {},
    gateway: {},
    autoActivationController: { status: () => ({ closure_input: closureInput }) },
    revisionTracker: {
      captureRunning: () => 'a'.repeat(64),
      status: () => ({
        running_revision: 'a'.repeat(64),
        disk_revision: 'a'.repeat(64),
        update_pending: false,
        state: 'current'
      })
    }
  });
  host.assertBootstrapMutationAllowed = () => true;
  host.fullCleanActivation.restart = async (options) => {
    calls.push(options);
    return { full_clean_activation: true, state: 'HANDOFF', admission_open: false, fully_ready: false };
  };

  const handler = host.handlers()['runtime.restart'];
  await handler({ reason: 'operator_restart' });
  assert.deepEqual(calls[0].sourceCheckpoint, SOURCE_CHECKPOINT);
  assert.deepEqual(orchestrator.checkpointResolver(), SOURCE_CHECKPOINT);

  await assert.rejects(handler({
    sourceCheckpoint: { ...SOURCE_CHECKPOINT, wave_id: 'wave-recovery-host-other' }
  }), { code: 'ACTIVATION_SOURCE_CHECKPOINT_MISMATCH' });
  assert.equal(calls.length, 1);
});
