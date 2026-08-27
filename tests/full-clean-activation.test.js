const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { ActivationEpochStore } = require('../electron/services/activationEpoch');
const {
  FullCleanActivation,
  canonicalProjectionRebuildSha256,
  validateProjectionRebuildGate,
  validateConnectorReadyGate
} = require('../electron/services/fullCleanActivation');
const { RecoveryHost } = require('../electron/services/recoveryHost');
const { RuntimeOrchestrator } = require('../electron/services/runtimeOrchestrator');
const { observeProcessIdentity } = require('../electron/services/processIdentity');
const { tunnelFingerprint } = require('../electron/services/tunnelService');

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
  coordinator.finalCensus = async (epochIdValue) => {
    calls.push(['finalCensus', epochIdValue]);
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
  const processInstanceId = id('mcp-process-connector', '1001');
  const serverInstanceId = id('mcp-server-connector', '1001');
  const observedAt = new Date(nowUnixMs - 1000).toISOString();
  const health = {
    process_instance_id: processInstanceId,
    instance_id: serverInstanceId,
    tool_contract: { sha256: contractSha256 },
    connector_tool_discovery: {
      current_contract_observed: true,
      contract_sha256: contractSha256,
      observed_at: observedAt,
      process_instance_id: processInstanceId,
      server_instance_id: serverInstanceId
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

  const staleAcknowledgement = validateConnectorReadyGate({
    health,
    contractStatus: { ...contractStatus, acknowledgedSha256: 'd'.repeat(64) },
    nowUnixMs
  });
  assert.equal(staleAcknowledgement.valid, false);
  assert.ok(staleAcknowledgement.reasons.includes('ACKNOWLEDGED_SHA256_MISMATCH'));
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
  const nowUnixMs = 1_700_000_000_000;
  const contractSha256 = 'c'.repeat(64);
  const connectorRediscoveredAt = new Date(nowUnixMs - 1000).toISOString();
  const receipt = projectionReceipt(root, {
    projection_classification: 'NO_ACTIVE_PROJECTION',
    projection: { run_id: '', wave_id: '', orchestration_state: '', mode: 'global' }
  });
  const wrapper = projectionWrapper(receipt);
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
        connector_tool_discovery: {
          current_contract_observed: true,
          contract_sha256: contractSha256,
          observed_at: connectorRediscoveredAt,
          process_instance_id: processInstanceId,
          server_instance_id: serverInstanceId
        },
        projection_rebuild: wrapper
      };
    },
    connectorContractStatus(toolContract, discovery) {
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
      if (health.connector_tool_discovery?.process_instance_id !== processInstanceId
        || health.connector_tool_discovery?.server_instance_id !== serverInstanceId) {
        throw codedError('CONNECTOR_CONTRACT_NOT_REDISCOVERED');
      }
      connectorAcknowledged = true;
      return this.connectorContractStatus(health.tool_contract, health.connector_tool_discovery);
    },
    tunnel: { status: async () => true }
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
    now: () => nowUnixMs
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

  connectorAcknowledged = false;
  wrapper.current = false;
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
  wrapper.current = true;
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

test('full-clean failure after epoch creation stops owned old components before terminalizing', async (t) => {
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
      inspectCodeActivation: async () => ({ safe: true, code: 'READY' }),
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
  assert.deepEqual(calls.map(([name]) => name), ['ui.stop', 'runtime.stop', 'recovery-plane.stop']);
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

  await assert.rejects(coordinator.restart({ operationId: id('operation-epoch', '0012'), sourceCheckpoint: acceptedSourceCheckpoint() }), { code: 'ACCEPTANCE_PENDING' });
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
