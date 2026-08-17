const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { DEVICE_ID_PATTERN, loadOrCreateDeviceIdentity } = require('../electron/services/deviceIdentity');
const { ComponentRevisionTracker, hashComponentRevision, recoveryHostLegacyV1Revision, RECOVERY_HOST_LEGACY_V1_CONTRACT } = require('../electron/services/componentRevision');
const { RecoveryActionStore } = require('../electron/services/recoveryActionStore');
const { RecoveryActivation } = require('../electron/services/recoveryActivation');
const { RecoveryIpcClient, RecoveryIpcServer } = require('../electron/services/recoveryIpc');
const {
  RecoveryHost,
  acquireRecoveryHostLock,
  releaseRecoveryHostLock
} = require('../electron/services/recoveryHost');
const {
  recoveryHostArguments,
  recoveryLoginItemArguments,
  spawnRecoveryHost,
  spawnElectronUi,
  assertActivationDeadline
} = require('../electron/services/recoveryHostLauncher');
const { replacementArguments } = require('../electron/recoveryHost');

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
    stop: async function stop() { calls.gatewayStop += 1; this.server = null; }
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
  assert.equal(snapshot.status.fullyReady, true);
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
  assert.equal(calls.gatewayStart, 1);
  assert.equal(calls.supervise, 1);

  await host.stop();
  assert.equal(calls.runtimeStop, 0);
  assert.equal(calls.gatewayStop, 1);
  assert.equal(fs.existsSync(paths.recoveryHostLockFile()), false);
  assert.equal(fs.existsSync(paths.recoveryHostDescriptorFile()), false);
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
    prepareCodeActivation: async () => ({ safe: true, code: 'READY', fenced: true }),
    cancelCodeActivation: async () => { calls.cancelFence += 1; return true; },
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
    allow_acceptance_pending: false
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
    prepareCodeActivation: async () => ({ safe: true, code: 'READY', fenced: true }),
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
    allow_acceptance_pending: false
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
  const relative = 'electron/services/deviceIdentity.js';
  const target = path.join(paths.appRoot(), ...relative.split('/'));
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.copyFileSync(path.join(__dirname, '..', ...relative.split('/')), target);
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
    prepareCodeActivation: async () => ({ safe: true, code: 'READY', fenced: true }),
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
    allow_acceptance_pending: false
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
  assert.deepEqual(recoveryLoginItemArguments({ isPackaged: false, getAppPath: () => 'E:\\app path' }), ['"E:\\app path"', '--recovery-host']);
  assert.deepEqual(recoveryHostArguments({ isPackaged: false, getAppPath: () => 'E:\\app' }, {
    expectedOldInstanceId: 'old-instance-0000001',
    operationId: 'operation-000000001'
  }), [
    'E:\\app',
    '--recovery-host',
    '--replace-recovery-host=old-instance-0000001',
    '--activation-operation=operation-000000001'
  ]);
  assert.deepEqual(replacementArguments([
    'electron.exe',
    '--replace-recovery-host=old-instance-0000001',
    '--activation-operation=operation-000000001'
  ]), {
    expectedOldInstanceId: 'old-instance-0000001',
    operationId: 'operation-000000001'
  });
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
});
