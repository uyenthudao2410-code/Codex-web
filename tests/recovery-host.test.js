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
  releaseRecoveryHostLock,
  validatePersistedReadyConnectorProof
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

function seedReadyEpoch(host, {
  freshnessMode = 'current_process_discovery',
  processInstanceId = 'coding-mcp-process-ready-0001',
  serverInstanceId = 'coding-mcp-server-ready-0001',
  contractSha256 = 'f'.repeat(64),
  connectorProcessInstanceId = processInstanceId,
  connectorServerInstanceId = serverInstanceId,
  runtimeContractSha256 = null,
  rediscoveredAt = new Date(Date.now() - 1000).toISOString(),
  compatibilityAcknowledgedAt = null,
  connectorAcknowledged = true
} = {}) {
  const store = host.activationEpochStore;
  const activationEpochId = 'activation-ready-adoption-0001';
  const created = store.create({
    activation_epoch_id: activationEpochId,
    operation_id: 'ready-adoption-operation-0001',
    components: ['coding_mcp']
  });
  store.update(activationEpochId, { state: 'STOPPING' });
  store.update(activationEpochId, { state: 'VERIFYING' });
  const finalCensus = {
    pass: true,
    activation_epoch_id: activationEpochId,
    process_instance_id: processInstanceId,
    server_instance_id: serverInstanceId,
    connector_acknowledged: connectorAcknowledged,
    connector_validation: {
      valid: true,
      code: 'READY',
      reasons: [],
      current_sha256: contractSha256,
      acknowledged_sha256: contractSha256,
      freshness_mode: freshnessMode,
      rediscovered_at: rediscoveredAt,
      compatibility_acknowledged_at: compatibilityAcknowledgedAt,
      activation_epoch_id: activationEpochId,
      process_instance_id: connectorProcessInstanceId,
      server_instance_id: connectorServerInstanceId
    },
    ...(runtimeContractSha256 ? {
      runtime: { toolContract: { sha256: runtimeContractSha256 } }
    } : {})
  };
  const committed = store.commitReady(activationEpochId, {
    verified: true,
    activation_epoch_id: activationEpochId,
    final_census: finalCensus
  });
  store.ready(activationEpochId, committed.ready_commit_digest);
  assert.equal(created.activation_epoch_id, activationEpochId);
  return store.current();
}

function readyAdoptionHost(t) {
  const paths = fixture(t);
  const calls = { orchestratorEpochs: [], recoveryPlaneEpochs: [], gatewayStart: 0, ipcStart: 0 };
  const revision = 'a'.repeat(64);
  const orchestrator = {
    setActivationEpoch: (epochId) => calls.orchestratorEpochs.push(epochId),
    activationEpochStatus: () => ({
      activation_epoch_id: 'activation-ready-adoption-0001',
      operation_id: 'ready-adoption-operation-0001',
      state: 'READY',
      epoch_state: 'READY',
      admission_open: true,
      update_incomplete: false
    }),
    completeActivationEpoch: async () => ({}),
    codingMcpRevisionStatus: () => ({
      running_revision: revision,
      disk_revision: revision,
      update_pending: false,
      state: 'current'
    }),
    isManuallyStopped: () => true
  };
  const gateway = {
    server: null,
    start: async function start() { calls.gatewayStart += 1; this.server = {}; },
    stop: async function stop() { this.server = null; }
  };
  const recoveryPlaneService = {
    setActivationEpoch: (epochId) => calls.recoveryPlaneEpochs.push(epochId),
    ensure: async () => ({ state: 'healthy' }),
    stop: async () => true
  };
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ autoStartServices: false, workspace: paths.appRoot() }) },
    secrets: { get: () => 'runtime-key' },
    environment: {},
    log: { info() {}, warn() {}, error() {}, read: () => [], clear() {} },
    orchestrator,
    healthService: {},
    gateway,
    recoveryPlaneService,
    ipcServerFactory: () => ({
      start: async () => { calls.ipcStart += 1; },
      stop: async () => true
    }),
    revisionTracker: {
      captureRunning: () => revision,
      status: (_component, running) => ({
        running_revision: running || revision,
        disk_revision: revision,
        update_pending: false,
        state: 'current'
      })
    }
  });
  t.after(() => host.stop());
  return { host, calls };
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

test('duplicate replacement contender cannot fail the epoch owned by the live Recovery Host', async (t) => {
  const paths = fixture(t);
  const finalOwner = 'final-recovery-host-owner-0001';
  const oldOwner = 'old-recovery-host-owner-00001';
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
    processIdentityObserver: async (pid) => ({
      state: 'live',
      pid,
      process_start_token: '123456789'
    })
  });
  const created = host.activationEpochStore.create({
    operation_id: 'duplicate-replacement-operation-0001',
    expires_at_unix_ms: Date.now() + 60_000,
    component_evidence: {
      recovery_host: { instance_id: oldOwner, pid: 48001 }
    }
  });
  host.activationEpochStore.update(created.activation_epoch_id, {
    state: 'HANDOFF',
    reason: 'replacement-owner-already-live'
  });
  acquireRecoveryHostLock(paths, finalOwner);
  t.after(() => releaseRecoveryHostLock(paths, finalOwner));

  await assert.rejects(host.start(), { code: 'RECOVERY_HOST_ALREADY_RUNNING' });
  const current = host.activationEpochStore.current();
  assert.equal(current.activation_epoch_id, created.activation_epoch_id);
  assert.equal(current.state, 'HANDOFF');
  assert.equal(current.admission_state, 'CLOSED');
  assert.equal(current.error, null);
  assert.equal(host.ownsLock, false);
  assert.equal(host.running, false);
});

test('persisted READY connector proof accepts either exact freshness mode and rejects malformed identities or timestamps', (t) => {
  const { host } = readyAdoptionHost(t);
  const strict = validatePersistedReadyConnectorProof(seedReadyEpoch(host));
  assert.equal(strict.valid, true);
  assert.deepEqual(strict.reasons, []);

  const { host: compatibilityHost } = readyAdoptionHost(t);
  const compatibilityAt = new Date(Date.now() - 1000).toISOString();
  const compatible = validatePersistedReadyConnectorProof(seedReadyEpoch(compatibilityHost, {
    freshnessMode: 'compatible_activation_bootstrap',
    rediscoveredAt: null,
    compatibilityAcknowledgedAt: compatibilityAt
  }));
  assert.equal(compatible.valid, true);
  assert.deepEqual(compatible.reasons, []);
  assert.equal(compatible.rediscovered_at, null);
  assert.equal(compatible.compatibility_acknowledged_at, compatibilityAt);

  const cases = [
    ['unknown freshness mode', { freshnessMode: 'unknown_mode' }, 'CONNECTOR_FRESHNESS_MODE_INVALID'],
    ['missing rediscovery timestamp', { rediscoveredAt: '' }, 'REDISCOVERY_TIMESTAMP_INVALID'],
    ['strict mode carries compatibility receipt', { compatibilityAcknowledgedAt: compatibilityAt }, 'COMPATIBILITY_RECEIPT_PRESENT'],
    ['compatibility timestamp missing', {
      freshnessMode: 'compatible_activation_bootstrap', rediscoveredAt: null, compatibilityAcknowledgedAt: null
    }, 'COMPATIBILITY_TIMESTAMP_INVALID'],
    ['compatibility timestamp from future', {
      freshnessMode: 'compatible_activation_bootstrap',
      rediscoveredAt: null,
      compatibilityAcknowledgedAt: new Date(Date.now() + 60_000).toISOString()
    }, 'COMPATIBILITY_TIMESTAMP_FROM_FUTURE'],
    ['compatibility mode carries rediscovery', {
      freshnessMode: 'compatible_activation_bootstrap', compatibilityAcknowledgedAt: compatibilityAt
    }, 'COMPATIBILITY_MODE_REDISCOVERY_PRESENT'],
    ['process identity mismatch', { connectorProcessInstanceId: 'coding-mcp-process-other-0001' }, 'CONNECTOR_PROCESS_INSTANCE_ID_MISMATCH'],
    ['server identity mismatch', { connectorServerInstanceId: 'coding-mcp-server-other-0001' }, 'CONNECTOR_SERVER_INSTANCE_ID_MISMATCH'],
    ['contract hash mismatch', { runtimeContractSha256: 'e'.repeat(64) }, 'RUNTIME_CONTRACT_SHA256_MISMATCH']
  ];
  for (const [label, options, reason] of cases) {
    const { host: candidateHost } = readyAdoptionHost(t);
    const candidate = seedReadyEpoch(candidateHost, options);
    const result = validatePersistedReadyConnectorProof(candidate);
    assert.equal(result.valid, false, label);
    assert.ok(result.reasons.includes(reason), `${label}: ${result.reasons.join(', ')}`);
  }
});

test('Recovery Host keeps control-plane IPC alive for an invalid READY epoch without rewriting history', async (t) => {
  const { host, calls } = readyAdoptionHost(t);
  const before = seedReadyEpoch(host, {
    freshnessMode: 'compatible_activation_bootstrap',
    rediscoveredAt: null,
    compatibilityAcknowledgedAt: null
  });

  const status = await host.start();
  assert.equal(host.running, true);
  assert.equal(status.state, 'update_incomplete');
  assert.equal(status.activation_epoch.admission_open, false);
  assert.equal(status.activation_epoch.update_incomplete, true);
  assert.equal(status.ready_adoption.state, 'blocked');
  assert.ok(status.ready_adoption.reasons.includes('COMPATIBILITY_TIMESTAMP_INVALID'));
  assert.deepEqual(calls.orchestratorEpochs, []);
  assert.deepEqual(calls.recoveryPlaneEpochs, []);
  assert.equal(calls.gatewayStart, 0);
  assert.equal(calls.ipcStart, 1, 'authenticated Recovery IPC remains available for explicit refresh');
  await assert.rejects(host.handlers()['runtime.start']({}), { code: 'UPDATE_INCOMPLETE' });

  const refreshCalls = [];
  host.fullCleanActivation.restart = async (options) => {
    refreshCalls.push(options);
    return { state: 'HANDOFF', admission_open: false, fully_ready: false };
  };
  await host.handlers()['runtime.restart']({ refresh: true, mode: 'full_clean_refresh', reason: 'invalid-ready-recovery' });
  assert.equal(refreshCalls.length, 1, 'explicit full-clean refresh must remain callable');
  assert.equal(refreshCalls[0].refresh, true);
  assert.equal(refreshCalls[0].mode, 'full_clean_refresh');
  const after = host.activationEpochStore.current();
  assert.deepEqual(after, before, 'startup guard must not rewrite immutable READY history');
});

test('invalid READY adoption supervision services only the explicit supervisor restart ticket', async (t) => {
  const { host } = readyAdoptionHost(t);
  seedReadyEpoch(host, {
    freshnessMode: 'compatible_activation_bootstrap',
    rediscoveredAt: null,
    compatibilityAcknowledgedAt: null
  });
  let ticketCalls = 0;
  let superviseCalls = 0;
  let lightweightCalls = 0;
  host.orchestrator.serviceSupervisorRestartRequest = async () => {
    ticketCalls += 1;
    return { ticket_id: 'restart-ready-adoption-test', expected_disconnect: true };
  };
  host.orchestrator.supervise = async () => {
    superviseCalls += 1;
    return { mcpRunning: true, tunnelRunning: true, fullyReady: true };
  };
  host.orchestrator.lightweightSnapshot = async () => {
    lightweightCalls += 1;
    return { mcpRunning: true, tunnelRunning: true, fullyReady: false };
  };
  host.recordSupervisionStatus = (value) => {
    host.lastSupervisionStatus = value;
    return value;
  };

  await host.start();
  assert.equal(host.readyAdoptionBlocksAdmission(), true);
  const blockedReady = await host.superviseOnce();
  assert.equal(ticketCalls, 1, 'the explicit restart ticket must remain serviceable under the blocked READY adoption guard');
  assert.equal(superviseCalls, 0, 'ordinary watchdog supervision must remain blocked');
  assert.equal(lightweightCalls, 1);
  assert.equal(blockedReady.supervisorRequest.ticket_id, 'restart-ready-adoption-test');

  const replacement = host.activationEpochStore.create({
    activation_epoch_id: 'activation-ready-adoption-0002',
    operation_id: 'ready-adoption-operation-0002',
    components: ['coding_mcp']
  });
  await host.superviseOnce();
  assert.equal(replacement.state, 'PREPARING');
  assert.equal(host.readyAdoptionBlocksAdmission(), false,
    'a different durable epoch retires the old READY-adoption diagnostic');
  assert.equal(ticketCalls, 1, 'a non-READY replacement epoch must block restart-ticket consumption');
  assert.equal(superviseCalls, 0, 'ordinary watchdog supervision stays blocked while the replacement epoch owns activation');
  assert.equal(lightweightCalls, 2);
});

test('invalid READY adoption guard retires only after a different durable epoch becomes current', async (t) => {
  const { host } = readyAdoptionHost(t);
  const blocked = seedReadyEpoch(host, {
    freshnessMode: 'compatible_activation_bootstrap',
    rediscoveredAt: null,
    compatibilityAcknowledgedAt: null
  });
  await host.start();
  assert.equal(host.readyAdoptionBlocksAdmission(), true);
  assert.equal(host.refreshReadyAdoptionGuard(), false,
    'the same malformed READY epoch must not clear its process-local guard');

  const originalCurrent = host.activationEpochStore.current.bind(host.activationEpochStore);
  try {
    host.activationEpochStore.current = () => null;
    assert.equal(host.refreshReadyAdoptionGuard(), false,
      'a missing durable current record is not evidence that the blocked epoch was replaced');
    assert.equal(host.readyAdoptionBlocksAdmission(), true);

    host.activationEpochStore.current = () => {
      throw Object.assign(new Error('unreadable activation store'), { code: 'ACTIVATION_EPOCH_STORE_INVALID' });
    };
    assert.equal(host.refreshReadyAdoptionGuard(), false,
      'an unreadable durable store must retain the fail-closed guard');
    assert.equal(host.readyAdoptionBlocksAdmission(), true);
  } finally {
    host.activationEpochStore.current = originalCurrent;
  }

  const replacement = host.activationEpochStore.create({
    activation_epoch_id: 'activation-ready-adoption-0002',
    operation_id: 'ready-adoption-operation-0002',
    components: ['coding_mcp']
  });
  host.orchestrator.activationEpochStatus = () => {
    const current = host.activationEpochStore.current();
    return {
      activation_epoch_id: current?.activation_epoch_id || null,
      operation_id: current?.operation_id || null,
      state: current?.state || 'NONE',
      epoch_state: current?.state || 'NONE',
      admission_open: Boolean(current?.state === 'READY' && current?.admission_state === 'OPEN'),
      update_incomplete: Boolean(current && (current.state !== 'READY' || current.admission_state !== 'OPEN'))
    };
  };

  const status = host.hostStatus();
  assert.equal(host.readyAdoptionBlocksAdmission(), false,
    'a different durable current epoch must retire only the old process-local guard');
  assert.equal(status.ready_adoption.state, 'adopted');
  assert.equal(status.activation_epoch.activation_epoch_id, replacement.activation_epoch_id);
  assert.equal(status.activation_epoch.state, 'PREPARING');
  assert.equal(status.activation_epoch.admission_open, false,
    'the replacement epoch keeps admission closed under its own durable state');
  assert.equal(status.activation_epoch.update_incomplete, true,
    'retiring the old guard must not project an in-progress replacement as ready');
  assert.equal(host.activationEpochStore.get(blocked.activation_epoch_id).state, 'READY',
    'the retired malformed READY record remains immutable history');
});

test('Recovery Host adopts a durable READY epoch only after strict proof validation', async (t) => {
  const { host, calls } = readyAdoptionHost(t);
  const ready = seedReadyEpoch(host);

  await host.start();
  assert.equal(host.running, true);
  assert.deepEqual(calls.orchestratorEpochs, [ready.activation_epoch_id]);
  assert.deepEqual(calls.recoveryPlaneEpochs, [ready.activation_epoch_id]);
  assert.equal(calls.gatewayStart, 1);
  assert.equal(calls.ipcStart, 1);
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

test('connector-pending supervision wakes final census for an exact compatible bootstrap', async (t) => {
  const paths = fixture(t);
  const revision = 'a'.repeat(64);
  const epochId = 'activation-connector-pending-0001';
  const processInstanceId = 'coding-process-instance-0001';
  const serverInstanceId = 'coding-server-instance-00001';
  let bootstrapObserved = false;
  let discoveryObserved = false;
  let lightweightCalls = 0;
  let censusCalls = 0;
  let persistedCensusCalls = 0;
  let finalizeCalls = 0;
  const activationOrder = [];
  let tunnelStatusCalls = 0;
  let exactRevisionCalls = 0;
  const health = () => ({
    ready: true,
    activation_epoch_id: epochId,
    process_instance_id: processInstanceId,
    instance_id: serverInstanceId,
    workspace: 'E:\\DEV\\Codex-web',
    device_id: '12345678-1234-4123-8123-123456789abc',
    device_instance_id: 'device-instance-connector-0001',
    code_revision: revision,
    tool_contract: {
      schema_version: 1,
      profile: 'smart-v3',
      sha256: 'f'.repeat(64),
      compatible_predecessor_sha256: ['e'.repeat(64)]
    },
    connector_tool_discovery: discoveryObserved ? {
      current_contract_observed: true,
      identity_source: 'attested_transport',
      attestation_verified: true,
      client_id: 'chatweb-recovery-host-test',
      contract_sha256: 'f'.repeat(64),
      activation_epoch_id: epochId,
      process_instance_id: processInstanceId,
      server_instance_id: serverInstanceId,
      observed_at: '2026-08-27T06:01:00.000Z'
    } : null,
    connector_activation_bootstrap: bootstrapObserved ? {
      current_contract_contact: true,
      identity_source: 'attested_transport',
      attestation_verified: true,
      client_id: 'chatweb-recovery-host-test',
      client_type: 'chatweb',
      method: 'tools/call',
      tool_name: 'workspace_context',
      workspace_accessed: false,
      contract_sha256: 'f'.repeat(64),
      activation_epoch_id: epochId,
      process_instance_id: processInstanceId,
      server_instance_id: serverInstanceId,
      observed_at: '2026-08-27T06:00:00.000Z'
    } : null
  });
  const orchestrator = {
    setFullCleanActivation() {},
    setFullCleanSourceCheckpointResolver() {},
    currentMcpHealth: async () => health(),
    connectorContractStatus: (_contract, discovery, _contact, bootstrap) => ({
      currentSha256: 'f'.repeat(64),
      acknowledgedSha256: 'e'.repeat(64),
      contractState: discovery
        ? 'CHANGED_DISCOVERED_NEEDS_ACK'
        : bootstrap ? 'CHANGED_COMPATIBLE_NEEDS_ACK' : 'CHANGED_NEEDS_DISCOVERY',
      refreshRequired: !discovery && !bootstrap,
      acknowledgementPending: Boolean(discovery || bootstrap),
      rediscovered: Boolean(discovery),
      rediscoveredAt: discovery?.observed_at || null,
      bootstrapCurrent: Boolean(bootstrap)
    }),
    activationEpochStatus: () => ({
      activation_epoch_id: epochId,
      state: 'UPDATE_INCOMPLETE',
      epoch_state: 'VERIFYING',
      admission_open: false,
      update_incomplete: true
    }),
    codingMcpRevisionStatus: () => {
      exactRevisionCalls += 1;
      return {
        running_revision: revision,
        disk_revision: revision,
        update_pending: false,
        state: 'current'
      };
    },
    lightweightSnapshot: async () => {
      lightweightCalls += 1;
      throw new Error('connector-pending supervision must not run blocking identity probes');
    },
    tunnel: {
      status: async () => {
        tunnelStatusCalls += 1;
        return true;
      }
    },
    supervise: async () => ({})
  };
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ workspace: 'E:\\DEV\\Codex-web', autoStartServices: false }) },
    secrets: {},
    environment: {},
    log: { info() {}, warn() {}, error() {}, read: () => [], clear() {} },
    orchestrator,
    healthService: {},
    gateway: {},
    processAlive: () => true,
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
  const epoch = {
    operation_id: 'full-clean-refresh-connector-pending-0001',
    activation_epoch_id: epochId,
    state: 'VERIFYING',
    admission_state: 'CLOSED',
    verification: {
      activation_epoch_id: epochId,
      process_instance_id: processInstanceId,
      server_instance_id: serverInstanceId,
      supervisor_instance_id: 'coding-supervisor-instance-0001',
      tunnel_instance_id: 'coding-tunnel-instance-000001',
      tunnel_pid: 45002,
      running_revision: revision,
      process_identity_verified: true,
      process_identity_changed: true,
      tunnel_identity_changed: true,
      tunnel_health_verified: false,
      recovery_host_revision_matches: true,
      recovery_host_epoch_matches: true,
      ui_verified: true,
      recovery_plane_identity_changed: true,
      recovery_plane_epoch_matches: true,
      recovery_plane_verified: true,
      projection_rebuild_verified: true,
      workspace_matches: true,
      device_matches: true,
      revision_matches: true,
      epoch_matches: true,
      connector_validation: { valid: false, reasons: ['CURRENT_CONTRACT_NOT_REDISCOVERED'] },
      runtime: {
        workspace: 'E:\\DEV\\Codex-web',
        mcpRunning: true,
        nativeAlive: true,
        tunnelRunning: false,
        fullyReady: false,
        connectorContractState: 'CHANGED_NEEDS_DISCOVERY',
        device: {
          device_id: '12345678-1234-4123-8123-123456789abc',
          device_instance_id: 'device-instance-connector-0001'
        },
        codeRevision: { codingMcp: { running_revision: revision, disk_revision: revision } }
      }
    }
  };
  fs.writeFileSync(paths.stateFile(), JSON.stringify({
    nativePid: 45001,
    nativeInstanceId: 'coding-supervisor-instance-0001',
    nativeActivationEpochId: epochId,
    nativeCodeRevision: revision,
    tunnelPid: 45002,
    tunnelInstanceId: 'coding-tunnel-instance-000001',
    tunnelActivationEpochId: epochId
  }), 'utf8');
  host.fullCleanActivation = {
    current: () => epoch,
    finalCensus: async (_epochId, options = {}) => {
      censusCalls += 1;
      assert.equal(_epochId, epochId);
      assert.equal(options.reusePendingProjection, true,
        'connector-pending watchdog census must reuse the exact durable projection receipt');
      epoch.verification.tunnel_health_verified = true;
      const connectorObserved = bootstrapObserved || discoveryObserved;
      return {
        pass: connectorObserved,
        verified: connectorObserved,
        activation_epoch_id: epochId,
        reason: connectorObserved ? null : 'UPDATE_INCOMPLETE'
      };
    },
    recordPendingCensus: (_epochId, census) => {
      persistedCensusCalls += 1;
      activationOrder.push(`persist:${census.pass}`);
      assert.equal(_epochId, epochId);
      assert.equal(census.activation_epoch_id, epochId);
      epoch.verification = { ...epoch.verification, ...census };
      return epoch;
    },
    finalize: async (_epochId) => {
      finalizeCalls += 1;
      activationOrder.push('finalize');
      assert.equal(_epochId, epochId);
      assert.equal(epoch.verification.pass, true,
        'the exact passing census must be durable before independent finalize begins');
      assert.equal(epoch.admission_state, 'CLOSED');
      return { state: 'READY', admission_open: true, fully_ready: true };
    }
  };
  host.running = true;

  const pending = await host.superviseOnce();
  assert.equal(lightweightCalls, 0);
  assert.equal(tunnelStatusCalls, 1, 'a transient negative census must be upgraded by one exact live Tunnel probe');
  assert.equal(censusCalls, 1, 'a recovered Tunnel probe must refresh the authoritative durable census once');
  assert.equal(persistedCensusCalls, 1, 'the refreshed non-terminal census must replace stale durable evidence');
  assert.equal(pending.mcpRunning, true);
  assert.equal(pending.tunnelRunning, true, 'exact prior tunnel receipt plus unchanged live PID is retained while admission stays closed');
  assert.equal(pending.connectorContractState, 'CHANGED_NEEDS_DISCOVERY');

  await host.superviseOnce();
  assert.equal(tunnelStatusCalls, 1, 'a verified pending Tunnel must not be re-probed on every supervision tick');
  assert.equal(censusCalls, 1, 'connector-pending supervision must defer further census work until real discovery');
  assert.equal(persistedCensusCalls, 1);
  const cached = host.cachedActivationSnapshot();
  assert.equal(cached.snapshotSource, 'activation_connector_pending_cache');
  assert.equal(cached.snapshotBusy, false);
  assert.equal(cached.telemetryAvailable, true);
  assert.equal(cached.signalStale, false);
  assert.ok(Number(cached.snapshotObservedAtUnixMs) > 0);
  assert.ok(Number(cached.snapshotAgeMs) >= 0);
  assert.equal(cached.fullyReady, false);
  assert.equal(exactRevisionCalls, 0, 'cached read-only snapshots must not start blocking OS identity probes');

  bootstrapObserved = true;
  await host.superviseOnce();
  assert.equal(censusCalls, 2, 'an exact compatible bootstrap must trigger the authoritative final census and guarded ACK path');
  assert.equal(persistedCensusCalls, 2, 'the passing compatibility census must replace the older durable receipt before finalize');
  assert.equal(finalizeCalls, 1);
  assert.deepEqual(activationOrder.slice(-2), ['persist:true', 'finalize']);
  assert.equal(lightweightCalls, 0);

  epoch.state = 'STOPPING';
  const beforeStopping = structuredClone(epoch);
  await host.superviseOnce();
  assert.equal(censusCalls, 2, 'STOPPING must not enter the replacement watchdog final census');
  assert.equal(persistedCensusCalls, 2, 'STOPPING must not persist VERIFYING evidence');
  assert.equal(finalizeCalls, 1, 'STOPPING must not be finalized by the watchdog');
  assert.deepEqual(epoch, beforeStopping, 'coordinator-owned STOPPING epoch must remain byte-for-byte unchanged');
});

test('Recovery Host supervision arms accepted-code activation only after the durable epoch becomes READY and OPEN', async (t) => {
  const paths = fixture(t);
  const revision = 'a'.repeat(64);
  let epoch = {
    operation_id: 'full-clean-auto-activation-arm-0001',
    activation_epoch_id: 'activation-auto-activation-arm-0001',
    state: 'VERIFYING',
    admission_state: 'CLOSED',
    verification: null
  };
  let censusPass = false;
  let controllerRunning = false;
  const calls = { start: 0, stop: 0, supervise: 0 };
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ workspace: paths.appRoot(), autoStartServices: false }) },
    secrets: {},
    environment: {},
    log: { info() {}, warn() {}, error() {}, read: () => [], clear() {} },
    orchestrator: {
      lightweightSnapshot: async () => ({ mcpRunning: true, tunnelRunning: true, fullyReady: false }),
      supervise: async () => {
        calls.supervise += 1;
        return { mcpRunning: true, tunnelRunning: true, fullyReady: true };
      },
      codingMcpRevisionStatus: () => ({
        running_revision: revision,
        disk_revision: revision,
        update_pending: false,
        state: 'current'
      })
    },
    healthService: {},
    gateway: { stop: async () => true },
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
    autoActivationController: {
      status: () => ({ running: controllerRunning, closure_input: null }),
      start: () => {
        calls.start += 1;
        controllerRunning = true;
        return { running: true };
      },
      stop: () => {
        calls.stop += 1;
        controllerRunning = false;
        return true;
      }
    }
  });
  host.fullCleanActivation = {
    current: () => epoch,
    enforceCurrentExpiry: () => epoch,
    finalCensus: async () => ({
      pass: censusPass,
      verified: censusPass,
      activation_epoch_id: epoch.activation_epoch_id
    }),
    recordPendingCensus: () => epoch,
    finalize: async () => {
      epoch = { ...epoch, state: 'READY', admission_state: 'OPEN' };
      return { state: 'READY', admission_open: true, fully_ready: true };
    }
  };
  host.activationEpochStore.current = () => epoch;
  host.recordSupervisionStatus = (value) => {
    host.lastSupervisionStatus = value;
    return value;
  };
  host.ensureRecoveryPlane = async () => null;
  host.superviseElectronUi = async () => null;
  host.running = true;

  await host.superviseOnce();
  assert.equal(epoch.state, 'VERIFYING');
  assert.equal(calls.start, 0, 'VERIFYING must not arm accepted-code activation early');

  censusPass = true;
  await host.superviseOnce();
  assert.equal(epoch.state, 'READY');
  assert.equal(epoch.admission_state, 'OPEN');
  assert.equal(calls.start, 1, 'the supervised READY/OPEN transition must arm the controller once');
  assert.equal(controllerRunning, true);

  await host.superviseOnce();
  assert.equal(calls.start, 1, 'later READY supervision ticks must not call start again');
  assert.equal(calls.supervise, 1, 'ordinary runtime supervision resumes only after READY/OPEN');

  await host.stop();
  assert.equal(calls.stop, 1, 'Recovery Host stop must continue stopping accepted-code activation');
  assert.equal(controllerRunning, false);
});

test('Recovery Host lightweight IPC serves one fresh supervision projection without duplicate live probes', async (t) => {
  const { host, revision } = uiRecoveryFixture(t);
  let directProbeCalls = 0;
  let uiIdentityCalls = 0;
  let durableEpochReads = 0;
  let componentRevisionReads = 0;
  const uiProcessStartToken = '123456789';
  host.activation.processIdentityObserver = (pid) => {
    uiIdentityCalls += 1;
    return { state: 'live', pid, process_start_token: uiProcessStartToken };
  };
  host.activation.uiRegistration = {
    instance_id: 'electron-ui-cache-test-0001',
    pid: 42001,
    process_start_token: uiProcessStartToken,
    revision,
    registered_at_unix_ms: Date.now()
  };
  assert.equal(host.activation.uiPresence().alive, true, 'supervision must establish one exact UI presence receipt');
  uiIdentityCalls = 0;
  const originalEpochCurrent = host.fullCleanActivation.current.bind(host.fullCleanActivation);
  host.fullCleanActivation.current = (...args) => {
    durableEpochReads += 1;
    return originalEpochCurrent(...args);
  };
  const originalRevisionStatus = host.revisions.status.bind(host.revisions);
  host.revisions.status = (...args) => {
    componentRevisionReads += 1;
    return originalRevisionStatus(...args);
  };
  host.orchestrator.lightweightSnapshot = async () => {
    directProbeCalls += 1;
    throw new Error('UI heartbeat must not launch a second live probe');
  };
  host.lastRecoveryPlaneStatus = {
    state: 'healthy',
    mcp: { state: 'healthy' },
    tunnel: { state: 'healthy' }
  };
  host.recordSupervisionStatus({
    mcpRunning: true,
    nativeAlive: true,
    tunnelRunning: true,
    componentsReady: true,
    connectorReady: true,
    fullyReady: true,
    failures: 0,
    codeRevision: { codingMcp: { running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64) } }
  });
  const projectionEpochReads = durableEpochReads;
  const projectionRevisionReads = componentRevisionReads;
  const ping = await host.handlers()['recovery.ping']();
  assert.equal(ping.pid, process.pid);
  assert.equal(ping.instance_id, host.instanceId);
  assert.equal(ping.ready, false);
  assert.equal(ping.recovery_plane_mode, undefined, 'liveness ping must remain independent of rich recovery-plane status');
  assert.equal(uiIdentityCalls, 0, 'liveness ping must not start a blocking UI identity probe');
  assert.equal(durableEpochReads, projectionEpochReads,
    'liveness ping must not re-read the durable activation epoch');
  assert.equal(componentRevisionReads, projectionRevisionReads,
    'liveness ping must not recalculate component revisions');

  const cachedStatus = await host.handlers()['recovery.status']();
  assert.equal(cachedStatus.recovery_plane_mode, 'independent_mcp_tunnel_v1');
  assert.equal(cachedStatus.electron_ui_revision.state, 'current');
  assert.equal(cachedStatus.telemetry_available, true);
  assert.equal(cachedStatus.signal_stale, false);
  assert.equal(uiIdentityCalls, 0, 'cached status must not repeat the blocking UI identity probe');
  assert.equal(durableEpochReads, projectionEpochReads,
    'cached status must not re-read the durable activation epoch');
  assert.equal(componentRevisionReads, projectionRevisionReads,
    'cached status must not recalculate component revisions');

  const handler = host.handlers()['runtime.lightweight_snapshot'];
  host.supervisionInFlight = Promise.resolve();
  const first = await handler();
  assert.equal(directProbeCalls, 0);
  assert.equal(first.mcpRunning, true);
  assert.equal(first.tunnelRunning, true);
  assert.equal(first.snapshotBusy, true);
  assert.equal(first.snapshotSource, 'recovery_host_supervision_cache');
  assert.equal(first.signalStale, false);
  assert.equal(first.recoveryHost.electron_ui_revision.state, 'current');
  assert.equal(first.recoveryHost.electron_ui_recovery.alive, true);
  assert.equal(uiIdentityCalls, 0, 'cached lightweight IPC must not repeat the blocking UI process identity probe');
  assert.ok(Number(first.snapshotAgeMs) >= 0);
  assert.equal(first.recoveryHost.recovery_plane.tunnel.state, 'healthy');
  assert.equal(durableEpochReads, projectionEpochReads,
    'lightweight IPC must not re-read the durable activation epoch');
  assert.equal(componentRevisionReads, projectionRevisionReads,
    'lightweight IPC must not recalculate component revisions');

  host.supervisionInFlight = null;
  host.lastSupervisionObservedAtUnixMs = Date.now() - 31_000;
  const stale = await handler();
  assert.equal(directProbeCalls, 0);
  assert.equal(durableEpochReads, projectionEpochReads);
  assert.equal(componentRevisionReads, projectionRevisionReads);
  assert.equal(stale.signalStale, true);
  assert.ok(stale.snapshotAgeMs >= 30_000);

  host.lastSupervisionStatus = null;
  host.lastSupervisionObservedAtUnixMs = 0;
  const unavailable = await handler();
  assert.equal(directProbeCalls, 0);
  assert.equal(durableEpochReads, projectionEpochReads);
  assert.equal(componentRevisionReads, projectionRevisionReads);
  assert.equal(unavailable.telemetryAvailable, false);
  assert.equal(unavailable.signalStale, true);
  assert.equal(unavailable.mcpRunning, null);
  assert.equal(unavailable.tunnelRunning, null);
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

test('UI watchdog does not relaunch a registered UI when async process identity is unavailable', async (t) => {
  let launches = 0;
  const { host, revision } = uiRecoveryFixture(t, {
    spawnElectronUi: async () => { launches += 1; return 42600 + launches; }
  });
  host.activation.uiRegistration = {
    instance_id: 'uncertain-electron-ui-0001',
    pid: process.pid,
    process_start_token: '123456789',
    revision,
    registered_at_unix_ms: Date.now()
  };
  host.activation.processIdentityObserver = () => {
    throw new Error('UI watchdog must not call the synchronous observer');
  };
  host.activation.asyncProcessIdentityObserver = async (pid) => ({ state: 'unavailable', pid });
  host.uiRecoveryInitialGraceUntil = 0;

  const status = await host.superviseElectronUi();
  assert.equal(launches, 0);
  assert.equal(status.state, 'unknown');
  assert.equal(status.alive, null);
  assert.equal(status.last_error_code, 'UI_PROCESS_IDENTITY_UNVERIFIED');
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
  assert.equal(launches[0].options.windowsHide, true, 'Recovery Host must remain a background process');
  assert.equal(launches[1].options.windowsHide, false, 'Electron UI must be allowed to create a visible Windows window');
  assert.equal(launches[2].options.windowsHide, true, 'bootstrap Recovery Host must remain a background process');
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

test('Electron UI registers with Recovery Host only after its window is visible', () => {
  const root = path.resolve(__dirname, '..');
  const main = fs.readFileSync(path.join(root, 'electron', 'main.js'), 'utf8');
  const createStart = main.indexOf('function createChatWindow()');
  const managerStart = main.indexOf('function openManagerWindow()');
  const startupStart = main.indexOf('app.whenReady().then(async () => {');
  const startupEnd = main.indexOf("log.info('Coding Tools MCP UI đã kết nối Recovery Host');", startupStart);
  assert.ok(createStart >= 0 && managerStart > createStart);
  assert.ok(startupStart >= 0 && startupEnd > startupStart);

  const createSource = main.slice(createStart, managerStart);
  const revealFunction = createSource.indexOf('const revealOpeningWindow =');
  const readyListener = createSource.indexOf("openingWindow.once('ready-to-show'");
  const loadFile = createSource.indexOf('chatWindow.loadFile(');
  const showWindow = createSource.indexOf('openingWindow.show()', revealFunction);
  const visibleGuard = createSource.indexOf('openingWindow.isVisible()', showWindow);
  const markReady = createSource.indexOf('uiWindowReady = true', visibleGuard);
  const register = createSource.indexOf('registerUiRevision()', markReady);
  const revealOnReady = createSource.indexOf('() => revealOpeningWindow()', readyListener);
  assert.ok(revealFunction >= 0 && readyListener > revealFunction && readyListener < loadFile,
    'ready-to-show must be subscribed before local HTML can load');
  assert.ok(showWindow > revealFunction && visibleGuard > showWindow && markReady > visibleGuard && register > markReady,
    'the window must be shown, verified visible, and marked ready before UI registration');
  assert.ok(revealOnReady > readyListener && revealOnReady < loadFile,
    'ready-to-show must trigger the bounded visible-window reveal path');

  const registerStart = main.indexOf('async function registerUiRevision()');
  const registerEnd = main.indexOf('async function suppressUiRecovery', registerStart);
  const registerSource = main.slice(registerStart, registerEnd);
  assert.match(registerSource, /!uiWindowReady/);
  assert.match(registerSource, /chatWindow\.isDestroyed\(\)/);
  assert.match(registerSource, /chatWindow\.webContents\.isDestroyed\(\)/);

  const startupSource = main.slice(startupStart, startupEnd);
  const createAtStartup = startupSource.indexOf('createChatWindow()');
  assert.ok(createAtStartup >= 0);
  assert.doesNotMatch(startupSource.slice(0, createAtStartup), /registerUiRevision\(\)/,
    'startup must not publish UI readiness before creating and showing the window');

  const managerSource = main.slice(managerStart, main.indexOf('function registerIpc()', managerStart));
  assert.ok(managerSource.indexOf("managerWindow.once('ready-to-show'") < managerSource.indexOf('managerWindow.loadFile('),
    'the manager window must subscribe before loading local HTML');
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

  await handler({ refresh: true, mode: 'full_clean_refresh', reason: 'npm_start_refresh' });
  assert.equal(calls.length, 2);
  assert.equal(calls[1].refresh, true);
  assert.equal(calls[1].mode, 'full_clean_refresh');
  assert.equal(calls[1].sourceCheckpoint, null);
});
