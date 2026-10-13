const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const zlib = require('node:zlib');
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
const { RecoveryIpcClient, RecoveryIpcServer, RPC_ACTIONS, sanitizeControlPlaneExecErrorDetails } = require('../electron/services/recoveryIpc');
const { compactWorkspaceSummary, workspaceSummaryDigest } = require('../electron/services/controlPlaneReadOnlyBridge');
const { digest: approvedPatchDigest } = require('../electron/services/controlPlaneApprovedPatchBridge');
const { loadExecBridgePolicy } = require('../electron/services/controlPlaneExecBridge');
const {
  RecoveryHost,
  acquireRecoveryHostLock,
  releaseRecoveryHostLock,
  validatePersistedReadyConnectorProof,
  strictControlPlaneBridgeRuntime
} = require('../electron/services/recoveryHost');
const {
  recoveryHostArguments,
  recoveryLoginItemArguments,
  electronUiArguments,
  spawnRecoveryHost,
  spawnElectronUi,
  processEnvironment,
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
    executor_cleanup: { state: 'not_required', confirmed: true },
    fence_operation_id: fenced === true ? operationId : null
  };
}

function controlPlaneWorkspaceSummary() {
  return compactWorkspaceSummary({
    workspace: 'E:\\private-workspace',
    project: { type: 'node', name: 'office-fixture', version: '1.0.0' },
    entries: [{
      name: 'office-marker.txt', path: 'office-marker.txt', type: 'file',
      size_bytes: 17, modified: '2026-09-16T00:00:00Z', is_hidden: false, is_ignored: false
    }],
    entries_truncated: false,
    git: { is_repo: true, branch: 'main', changed_count: 0, truncated: false }
  });
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

test('central bridge admission requires a fresh route and local policy rather than a Windows Tunnel connector', () => {
  const base = {
    executionRole: 'central_executor',
    componentsReady: true,
    fullyReady: true,
    updateIncomplete: false,
    connectorReady: false,
    connectorContractState: 'UNAVAILABLE',
    connectorFreshnessMode: null,
    connectorRediscovered: false,
    connectorRefreshRequired: false,
    connectorAcknowledgementPending: false
  };
  assert.equal(strictControlPlaneBridgeRuntime({
    ...base,
    centralConnected: true,
    authorityReady: true,
    centralStatusReason: null
  }), true);
  assert.equal(strictControlPlaneBridgeRuntime({
    ...base,
    centralConnected: true,
    authorityReady: false,
    centralStatusReason: 'CENTRAL_LOCAL_POLICY_NOT_READY'
  }), false);
});

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

function seedCentralReadyEpoch(host) {
  const store = host.activationEpochStore;
  const activationEpochId = 'activation-ready-adoption-0001';
  const revision = 'a'.repeat(64);
  store.create({
    activation_epoch_id: activationEpochId,
    operation_id: 'ready-adoption-operation-0001',
    components: ['recovery_host', 'coding_mcp', 'electron_ui'],
    metadata: { execution_role: 'central_executor', component_profile: 'central_executor_v1' },
    component_revisions: {
      recovery_host: { disk_revision: revision },
      coding_mcp: { disk_revision: revision },
      electron_ui: { disk_revision: revision }
    }
  });
  store.update(activationEpochId, { state: 'STOPPING' });
  store.update(activationEpochId, { state: 'VERIFYING' });
  const finalCensus = {
    verified: true,
    pass: true,
    activation_epoch_id: activationEpochId,
    execution_role: 'central_executor',
    component_profile: 'central_executor_v1',
    host_instance_id: 'central-recovery-host-ready-0001',
    host_pid: process.pid,
    process_instance_id: 'central-coding-mcp-process-ready-0001',
    server_instance_id: 'central-coding-mcp-server-ready-0001',
    supervisor_instance_id: 'central-supervisor-ready-0001',
    ui_instance_id: 'central-ui-ready-0001',
    recovery_mcp_instance_id: 'central-recovery-mcp-ready-0001',
    recovery_mcp_pid: process.pid,
    running_revision: revision,
    disk_revision: revision,
    ui_running_revision: revision,
    recovery_host_running_revision: revision,
    all_components_same_epoch: true,
    process_identity_verified: true,
    process_identity_changed: true,
    recovery_host_revision_matches: true,
    recovery_host_epoch_matches: true,
    ui_verified: true,
    recovery_mcp_health_verified: true,
    recovery_plane_identity_changed: true,
    recovery_plane_epoch_matches: true,
    recovery_plane_verified: true,
    projection_rebuild_verified: true,
    workspace_matches: true,
    device_matches: true,
    revision_matches: true,
    epoch_matches: true,
    central_connected: true,
    authority_ready: true,
    central_route_verified: true,
    central_status_reason: null,
    tunnel_required: false,
    tunnel_identity_changed: null,
    runtime: {
      executionRole: 'central_executor',
      activationEpoch: { activation_epoch_id: activationEpochId },
      tunnelRunning: false,
      // The census occurs before commit/open, and must not itself authorize a
      // later action after a restart or turn historical route proof into live proof.
      fullyReady: false
    }
  };
  const committed = store.commitReady(activationEpochId, {
    verified: true,
    activation_epoch_id: activationEpochId,
    final_census: finalCensus
  });
  store.ready(activationEpochId, committed.ready_commit_digest);
  return store.current();
}

function readyAdoptionHost(t, { executionRole = 'direct_legacy' } = {}) {
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
    settings: { load: () => ({ autoStartServices: false, workspace: paths.appRoot(), executionRole }) },
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

function approvedPatchVerificationHost(t, { execDenied = false, differentExecWorkspace = false } = {}) {
  const { host } = readyAdoptionHost(t);
  const root = fs.realpathSync.native(host.paths.appRoot());
  const before = 'before\n';
  const after = 'after\n';
  const sha256 = value => crypto.createHash('sha256').update(value).digest('hex');
  const preimage = sha256(before);
  const postimage = sha256(after);
  const envelope = [
    '*** Begin Patch',
    '*** Write Exact File: fixture.txt',
    `@@ encoding=zlib-base64 preimage_sha256=${preimage} postimage_sha256=${postimage}`,
    `+${zlib.deflateSync(Buffer.from(after)).toString('base64')}`,
    '*** End Patch'
  ].join('\n');
  fs.writeFileSync(path.join(root, 'fixture.txt'), before, 'utf8');
  const expiresAtMs = Date.now() + 60_000;
  const authority = {
    server_origin: 'https://control.example.test',
    owner_id: 'owner-approved-patch-host-0001',
    device_id: host.deviceIdentity.device_id,
    endpoint_id: 'endpoint-approved-patch-host-0001',
    workspace_id: 'workspace-approved-patch-host-0001',
    workspace_generation: 'generation-approved-patch-host-0001',
    expires_at_ms: expiresAtMs,
    facade_contract: { schema_version: 32, profile: 'control-plane-private-tunnel-service-v1', sha256: 'f'.repeat(64) }
  };
  const patchPolicy = { schema_version: 1, enabled: true, ...authority,
    allowed_relative_paths: ['fixture.txt'], max_patch_bytes: 4096, max_file_bytes: 4096,
    validation_profile: 'targeted' };
  const execAuthority = differentExecWorkspace ? { ...authority,
    workspace_id: 'workspace-other-approved-patch-host-0001',
    workspace_generation: 'generation-other-approved-patch-host-0001' } : authority;
  const execPolicy = { schema_version: 1, enabled: true, ...execAuthority,
    allowed_argv_prefixes: execDenied ? [['npm']] : [['node', '--test']],
    max_timeout_ms: 60_000, max_output_bytes: 32768, max_concurrent: 1 };
  const registration = (authorityValue, canonicalPath) => ({
    workspace_id: authorityValue.workspace_id,
    workspace_generation: authorityValue.workspace_generation,
    canonical_path: canonicalPath,
    display_name: 'Isolated approved-patch host fixture',
    capabilities: { read: true, write: true, exec: true },
    created_at_ms: Date.now()
  });
  const entries = [registration(authority, root)];
  if (differentExecWorkspace) {
    const otherRoot = path.join(root, 'other-workspace');
    fs.mkdirSync(otherRoot);
    entries.push(registration(execAuthority, fs.realpathSync.native(otherRoot)));
  }
  fs.writeFileSync(host.paths.controlPlaneApprovedPatchPolicyFile(), JSON.stringify(patchPolicy), 'utf8');
  fs.writeFileSync(host.paths.controlPlaneExecPolicyFile(), JSON.stringify(execPolicy), 'utf8');
  fs.writeFileSync(host.paths.controlPlaneWorkspaceRegistryFile(), JSON.stringify({ schema_version: 1, entries }), 'utf8');
  const verification = { argv: ['node', '--test', 'tests/fixture.test.js'], cwd: '', timeout_ms: 60_000, max_output_bytes: 32768 };
  const request = { ...authority, expires_at_ms: expiresAtMs - 1,
    context_id: 'context-approved-patch-host-0001', binding_id: 'binding-approved-patch-host-0001',
    action_id: 'action-approved-patch-host-0001', attempt_id: 'attempt-approved-patch-host-0001',
    task_id: `task_${'a'.repeat(32)}`, writer_lease_generation: 1,
    tool_name: 'agent_workflow', operation: 'apply_patch',
    permission_request_id: 'permission-approved-patch-host-0001', permission_digest: 'a'.repeat(64), intent_digest: 'b'.repeat(64),
    path: 'fixture.txt', preimage_sha256: preimage, patch_sha256: sha256(envelope), patch_envelope: envelope,
    validation_profile: 'targeted', verification };
  const identity = { activation_epoch_id: 'activation-approved-patch-host-0001',
    mcp_process_instance_id: 'process-approved-patch-host-0001', mcp_server_instance_id: 'server-approved-patch-host-0001',
    tool_contract_sha256: 'd'.repeat(64), mcp_ready: true, identity_current: true };
  const calls = { snapshot: 0, patch: 0, admission: null };
  host.orchestrator.lightweightSnapshot = async () => {
    calls.snapshot += 1;
    return { executionRole: 'central_executor', componentsReady: true, fullyReady: true, updateIncomplete: false,
      centralConnected: true, authorityReady: true, centralStatusReason: null };
  };
  host.mcpIdentityObservation = async () => identity;
  host.orchestrator.controlPlaneApprovedPatch = async admission => {
    calls.patch += 1;
    calls.admission = admission;
    fs.writeFileSync(path.join(admission.workspace_root, admission.path), after, 'utf8');
    const file = { path: admission.path, preimage_sha256: admission.preimage_sha256,
      postimage_sha256: admission.postimage_sha256, bytes_written: admission.postimage_bytes };
    const initialVerification = { plan_sha256: approvedPatchDigest(verification), proof_status: 'passed',
      proof_ids: ['4'.repeat(32)], proof_fingerprint: '5'.repeat(64), command_id: '-original-command', job_id: '_original-job' };
    return { schema_version: 1, operation_kind: 'control_plane_approved_patch', local_handle: `cp_ap_${'c'.repeat(48)}`,
      action_id: admission.action_id, attempt_id: admission.attempt_id, task_id: admission.task_id,
      writer_lease_generation: admission.writer_lease_generation, run_id: '1'.repeat(32), wave_id: '2'.repeat(32),
      patch_applied: true, local_semantic_acceptance: 'pending', actor: admission.actor, policy_sha256: admission.policy_sha256,
      facade_contract: admission.facade_contract, runtime_identity: { activation_epoch_id: identity.activation_epoch_id,
        process_instance_id: identity.mcp_process_instance_id, server_instance_id: identity.mcp_server_instance_id,
        tool_contract_sha256: identity.tool_contract_sha256 }, file, initial_verification: initialVerification,
      response_sha256: approvedPatchDigest({ file, initial_verification: initialVerification }) };
  };
  return { host, root, request, calls, before, after };
}

test('Recovery Host initial verification denies exec authority before the patch orchestrator', async t => {
  for (const scenario of [
    { name: 'argv outside independent exec policy', options: { execDenied: true }, code: 'CONTROL_PLANE_EXEC_ALLOWLIST_DENIED' },
    { name: 'exec registration resolves another workspace', options: { differentExecWorkspace: true }, code: 'CONTROL_PLANE_EXEC_POLICY_INVALID' }
  ]) {
    await t.test(scenario.name, async child => {
      const item = approvedPatchVerificationHost(child, scenario.options);
      await assert.rejects(item.host.controlPlaneApprovedPatch(item.request), { code: scenario.code });
      assert.equal(item.calls.patch, 0);
      assert.equal(item.calls.snapshot, 0, 'independent exec admission must precede asynchronous runtime work');
      assert.equal(fs.readFileSync(path.join(item.root, 'fixture.txt'), 'utf8'), item.before);
    });
  }
});

test('Recovery Host initial verification forwards the exact independent exec admission for the same root', async t => {
  const item = approvedPatchVerificationHost(t);
  const expectedExecPolicy = loadExecBridgePolicy(item.host.paths);
  const result = await item.host.controlPlaneApprovedPatch(item.request);
  assert.equal(item.calls.patch, 1);
  assert.equal(item.calls.admission.workspace_root, item.root);
  assert.equal(item.calls.admission.exec_policy_sha256, expectedExecPolicy.policy_sha256);
  assert.deepEqual(item.calls.admission.verification, item.request.verification);
  assert.equal(item.calls.admission.expires_at_ms, item.request.expires_at_ms);
  assert.equal(item.calls.admission.actor.client_id, 'electron-control-plane-approved-patch-bridge');
  assert.equal(Object.isFrozen(item.calls.admission), true);
  assert.equal(result.patch_applied, true);
  assert.equal(result.initial_verification.proof_status, 'passed');
  assert.equal(fs.readFileSync(path.join(item.root, 'fixture.txt'), 'utf8'), item.after);
});

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

test('full-clean UI termination keeps a detached Recovery Host descendant alive', async (t) => {
  const paths = fixture(t);
  const terminations = [];
  const uiPid = process.pid + 1;
  const uiToken = '133801234567890123';
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ autoStartServices: false, workspace: paths.appRoot() }) },
    secrets: {},
    environment: {},
    log: { info() {}, warn() {}, error() {}, read: () => [], clear() {} },
    orchestrator: {},
    healthService: {},
    gateway: { stop: async () => {} },
    revisionTracker: {
      captureRunning: () => 'a'.repeat(64),
      status: () => ({ running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64), state: 'current' })
    },
    processIdentityObserver: (pid) => ({ state: 'live', pid, process_start_token: uiToken }),
    lifecycleProcessIdentityObserver: async (pid) => ({ state: 'live', pid, process_start_token: uiToken }),
    exactProcessTerminator: async (identity, options) => { terminations.push({ identity, options }); }
  });
  t.after(() => host.stop());
  host.activation.uiRegistration = {
    instance_id: 'detached-ui-child-host-test-0001',
    pid: uiPid,
    process_start_token: uiToken,
    revision: 'a'.repeat(64),
    registered_at_unix_ms: Date.now()
  };

  const presence = host.activation.uiPresence();
  assert.equal(presence.alive, true);
  await host.fullCleanActivation.terminateUi(presence);

  assert.deepEqual(terminations, [{
    identity: { pid: uiPid, process_start_token: uiToken },
    options: {
      observeProcessIdentity: host.lifecycleProcessIdentityObserver,
      timeoutMs: 5000,
      includeDescendants: false
    }
  }]);
});

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
      'runtime.restart': async () => { mutations += 1; return { restarted: true }; },
      'runtime.stop': async () => { throw Object.assign(new Error('semantic refusal'), { code: 'ECONNRESET' }); }
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
  await assert.rejects(client.stop(), { code: 'ECONNRESET', recoveryResponseReceived: true });
  assert.equal(descriptor.host, '127.0.0.1');
  assert.equal(descriptor.owner, 'recovery-host');
  assert.equal(descriptor.device_id, deviceIdentity.device_id);
  assert.equal(descriptor.device_instance_id, 'device-instance-test-0001');
});

test('Recovery IPC client keeps fresh status as a read argument, not transport authority', async () => {
  const client = new RecoveryIpcClient({ paths: {} });
  let observed = null;
  client.call = async (...args) => {
    observed = args;
    return { ok: true };
  };

  await client.status({ fresh: true, timeout: 321, expectedOwnerPid: 42 });
  assert.deepEqual(observed, [
    'recovery.status',
    [{ fresh: true }],
    { timeout: 321, expectedOwnerPid: 42 }
  ]);
});

test('Recovery IPC preserves only typed execution diagnostics on the exact error action', async (t) => {
  const paths = fixture(t);
  const details = {
    native_error_code: 'SANDBOX_STATE_PHASE_FAILED', phase: 'start', backend_error_code: 'backend_error',
    command_id: '-4hBa9tkNAYi4ngWamUIO4Ba', job_id: 'a'.repeat(32), job_lifecycle: 'spawn_failed',
    root_pid: 0, execution_started: false, job_finished_at: '2026-10-11T10:27:08.489123Z'
  };
  const privateFields = { token: 'do-not-forward-token', descriptor: { token: 'private' }, stdout: 'private stdout' };
  const server = new RecoveryIpcServer({
    paths, instanceId: 'instance-exec-diagnostics', startedAt: new Date().toISOString(), log: { warn() {} },
    handlers: {
      'runtime.control_plane_exec': async (request) => {
        throw Object.assign(new Error('private native message'), {
          code: request?.otherCode ? 'OTHER_EXEC_ERROR' : 'CONTROL_PLANE_EXEC_MCP_REJECTED',
          details: { ...details, ...privateFields }
        });
      },
      'runtime.stop': async () => { throw Object.assign(new Error('other action'), {
        code: 'CONTROL_PLANE_EXEC_MCP_REJECTED', details
      }); }
    }
  });
  t.after(() => server.stop());
  await server.start();
  const client = new RecoveryIpcClient({ paths });
  await assert.rejects(client.call('runtime.control_plane_exec', [{}]), (error) => {
    assert.equal(error.code, 'CONTROL_PLANE_EXEC_MCP_REJECTED');
    assert.equal(error.recoveryResponseReceived, true);
    assert.deepEqual(error.details, details);
    assert.equal(error.message.includes('private'), false);
    assert.equal(JSON.stringify(error).includes('do-not-forward'), false);
    return true;
  });
  for (const [action, args] of [['runtime.stop', []], ['runtime.control_plane_exec', [{ otherCode: true }]]]) {
    await assert.rejects(client.call(action, args), (error) => {
      assert.equal(Object.hasOwn(error, 'details'), false);
      assert.equal(error.recoveryResponseReceived, true);
      return true;
    });
  }
});

test('Recovery IPC execution diagnostics reject coercion and impossible UTC completion dates', () => {
  assert.deepEqual(sanitizeControlPlaneExecErrorDetails({
    native_error_code: 'SANDBOX_STATE_PHASE_FAILED', phase: 'shell', backend_error_code: 'private\nmessage',
    command_id: 'x'.repeat(161), job_id: 'job\nsecret', job_lifecycle: 'completed',
    root_pid: '0', execution_started: 0, job_finished_at: '2026-02-31T10:27:08Z',
    token: 'private'
  }), { native_error_code: 'SANDBOX_STATE_PHASE_FAILED' });
  assert.equal(sanitizeControlPlaneExecErrorDetails([]), null);
  assert.equal(sanitizeControlPlaneExecErrorDetails({ root_pid: true, job_finished_at: Date.now() }), null);
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

test('persisted central READY proof uses the immutable profile and complete census, never a Windows connector receipt', (t) => {
  const { host } = readyAdoptionHost(t, { executionRole: 'central_executor' });
  const ready = seedCentralReadyEpoch(host);
  const result = validatePersistedReadyConnectorProof(ready, { expectedExecutionRole: 'central_executor' });
  assert.equal(result.valid, true);
  assert.equal(result.execution_role, 'central_executor');
  assert.equal(result.component_profile, 'central_executor_v1');
  assert.equal(result.freshness_mode, null, 'central mode must not fabricate direct connector discovery');
  assert.equal(result.current_sha256, null);
  assert.equal(strictControlPlaneBridgeRuntime(ready.verification.final_census.runtime), false,
    'persisted READY proof never substitutes for fresh per-action route/policy evidence');

  const cases = [
    ['metadata absent', (r) => { r.metadata = {}; }, 'CONNECTOR_VALIDATION_MISSING'],
    ['profile missing', (r) => { delete r.metadata.component_profile; }, 'ACTIVATION_EXECUTION_PROFILE_INVALID'],
    ['profile mismatch', (r) => { r.metadata.component_profile = 'direct_legacy_v1'; }, 'ACTIVATION_EXECUTION_PROFILE_INVALID'],
    ['metadata role mismatch', (r) => { r.metadata.execution_role = 'direct_legacy'; }, 'ACTIVATION_EXECUTION_PROFILE_INVALID'],
    ['census role mismatch', (r) => { r.verification.final_census.execution_role = 'direct_legacy'; }, 'FINAL_CENSUS_EXECUTION_ROLE_MISMATCH'],
    ['census profile mismatch', (r) => { r.verification.final_census.component_profile = 'direct_legacy_v1'; }, 'FINAL_CENSUS_COMPONENT_PROFILE_MISMATCH'],
    ['census epoch mismatch', (r) => { r.verification.final_census.activation_epoch_id = 'different-epoch'; }, 'FINAL_CENSUS_ACTIVATION_EPOCH_ID_MISMATCH'],
    ['no same-epoch proof', (r) => { delete r.verification.final_census.all_components_same_epoch; }, 'CENTRAL_ALL_COMPONENTS_SAME_EPOCH_INVALID'],
    ['local process identity unverified', (r) => { r.verification.final_census.process_identity_verified = false; }, 'CENTRAL_PROCESS_IDENTITY_VERIFIED_INVALID'],
    ['route missing', (r) => { delete r.verification.final_census.central_route_verified; }, 'CENTRAL_CENTRAL_ROUTE_VERIFIED_INVALID'],
    ['authority not ready', (r) => { r.verification.final_census.authority_ready = false; }, 'CENTRAL_AUTHORITY_READY_INVALID'],
    ['central reason missing', (r) => { delete r.verification.final_census.central_status_reason; }, 'CENTRAL_STATUS_REASON_INVALID'],
    ['connector receipt present', (r) => { r.verification.final_census.connector_validation = { valid: true }; }, 'CENTRAL_DIRECT_CONNECTOR_PROOF_PRESENT'],
    ['tunnel required', (r) => { r.verification.final_census.tunnel_required = true; }, 'CENTRAL_TUNNEL_PROFILE_INVALID'],
    ['MCP identity missing', (r) => { r.verification.final_census.process_instance_id = ''; }, 'CENTRAL_PROCESS_INSTANCE_ID_MISSING'],
    ['recovery process missing', (r) => { r.verification.final_census.recovery_mcp_pid = 0; }, 'CENTRAL_RECOVERY_MCP_PID_INVALID'],
    ['revision mismatch', (r) => { r.verification.final_census.running_revision = 'b'.repeat(64); }, 'CENTRAL_CODING_MCP_REVISION_MISMATCH'],
    ['runtime role mismatch', (r) => { r.verification.final_census.runtime.executionRole = 'direct_legacy'; }, 'CENTRAL_RUNTIME_EXECUTION_ROLE_INVALID'],
    ['runtime tunnel running', (r) => { r.verification.final_census.runtime.tunnelRunning = true; }, 'CENTRAL_RUNTIME_TUNNEL_STATE_INVALID'],
    ['runtime epoch mismatch', (r) => { r.verification.final_census.runtime.activationEpoch.activation_epoch_id = 'other'; }, 'RUNTIME_ACTIVATION_EPOCH_ID_MISMATCH']
  ];
  for (const [label, mutate, expected] of cases) {
    const candidate = structuredClone(ready);
    mutate(candidate);
    const invalid = validatePersistedReadyConnectorProof(candidate, { expectedExecutionRole: 'central_executor' });
    assert.equal(invalid.valid, false, label);
    assert.ok(invalid.reasons.includes(expected), `${label}: ${invalid.reasons.join(', ')}`);
  }

  const { host: directHost } = readyAdoptionHost(t);
  const direct = seedReadyEpoch(directHost);
  const mixed = validatePersistedReadyConnectorProof(direct, { expectedExecutionRole: 'central_executor' });
  assert.equal(mixed.valid, false);
  assert.ok(mixed.reasons.includes('READY_EXECUTION_ROLE_MISMATCH'),
    'legacy direct receipts never authorize adoption under central settings');
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
  await host.handlers()['runtime.restart']({
    mode: 'full_clean_execution_role_handoff', executionRole: 'central_executor'
  });
  assert.equal(refreshCalls.length, 2, 'explicit role migration must remain callable under a blocked READY receipt');
  assert.equal(refreshCalls[1].mode, 'full_clean_execution_role_handoff');
  assert.equal(refreshCalls[1].executionRole, 'central_executor');
  assert.equal(refreshCalls[1].sourceCheckpoint, undefined);
  assert.equal(refreshCalls[1].refresh, undefined, 'only the coordinator normalizes the validated migration');
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

test('healthy READY supervision services the explicit supervisor restart ticket', async (t) => {
  const { host } = readyAdoptionHost(t);
  seedReadyEpoch(host);
  let ticketCalls = 0;
  let superviseCalls = 0;
  let lightweightCalls = 0;
  host.orchestrator.serviceSupervisorRestartRequest = async () => {
    ticketCalls += 1;
    return { ticket_id: 'restart-healthy-ready-test', expected_disconnect: true };
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
  assert.equal(host.readyAdoptionBlocksAdmission(), false);
  const ready = await host.superviseOnce();
  assert.equal(ticketCalls, 1, 'healthy READY supervision must service an explicit restart ticket');
  assert.equal(superviseCalls, 1, 'ordinary supervision may continue after the explicit restart request is serviced');
  assert.equal(lightweightCalls, 0, 'healthy READY supervision must not fall back to the blocked lightweight snapshot path');
  assert.equal(ready.supervisorRequest.ticket_id, 'restart-healthy-ready-test');
});

test('healthy READY supervision yields immediately after a supervisor restart enters HANDOFF', async (t) => {
  const { host } = readyAdoptionHost(t);
  seedReadyEpoch(host);
  let superviseCalls = 0;
  let lightweightCalls = 0;
  let recoveryPlaneCalls = 0;
  let uiCalls = 0;
  host.orchestrator.serviceSupervisorRestartRequest = async () => ({
    ticketId: 'restart-handoff-drain-test',
    operationId: 'restart-handoff-drain-test',
    status: 'accepted',
    activation_mode: 'full_clean_refresh',
    result: { state: 'HANDOFF', admission_open: false, fully_ready: false }
  });
  host.orchestrator.supervise = async () => {
    superviseCalls += 1;
    return { mcpRunning: true, tunnelRunning: true, fullyReady: true };
  };
  host.orchestrator.lightweightSnapshot = async () => {
    lightweightCalls += 1;
    return { mcpRunning: true, tunnelRunning: true, fullyReady: false };
  };

  await host.start();
  host.ensureRecoveryPlane = async () => { recoveryPlaneCalls += 1; };
  host.superviseElectronUi = async () => { uiCalls += 1; };
  const pending = await host.superviseOnce();

  assert.equal(superviseCalls, 0, 'ordinary runtime supervision must not run after accepted full-clean HANDOFF');
  assert.equal(lightweightCalls, 0, 'handoff must not start another live runtime observation before supervision drains');
  assert.equal(recoveryPlaneCalls, 0, 'Recovery Plane supervision must yield to the full-clean handoff owner');
  assert.equal(uiCalls, 0, 'UI recovery must yield to the full-clean handoff owner');
  assert.equal(pending.supervisorRequest.status, 'accepted');
  assert.equal(pending.supervisorRequest.result.state, 'HANDOFF');
  assert.equal(pending.fullyReady, false);
  assert.equal(pending.updateIncomplete, true);
});

test('healthy READY supervision defers a retained supervisor restart until the next watchdog tick', async (t) => {
  const { host } = readyAdoptionHost(t);
  seedReadyEpoch(host);
  let ticketCalls = 0;
  let superviseCalls = 0;
  let lightweightCalls = 0;
  let recoveryPlaneCalls = 0;
  let uiCalls = 0;
  host.orchestrator.serviceSupervisorRestartRequest = async () => {
    ticketCalls += 1;
    if (ticketCalls === 1) {
      return {
        ticketId: 'restart-deferred-retry-test',
        operationId: 'restart-deferred-retry-test',
        status: 'deferred',
        request_retained: true,
        activation_mode: 'full_clean_activation',
        error: { code: 'RUNTIME_BUSY', message: 'initiating tool call is still leaving admission' }
      };
    }
    return {
      ticketId: 'restart-deferred-retry-test',
      operationId: 'restart-deferred-retry-test',
      status: 'accepted',
      activation_mode: 'full_clean_refresh',
      result: { state: 'HANDOFF', admission_open: false, fully_ready: false }
    };
  };
  host.orchestrator.supervise = async () => {
    superviseCalls += 1;
    const nestedRequest = await host.orchestrator.serviceSupervisorRestartRequest();
    return {
      mcpRunning: true,
      nativeAlive: true,
      tunnelRunning: true,
      fullyReady: true,
      supervisorRequest: nestedRequest
    };
  };
  host.orchestrator.lightweightSnapshot = async () => {
    lightweightCalls += 1;
    return { mcpRunning: true, nativeAlive: true, tunnelRunning: true, fullyReady: true };
  };

  await host.start();
  host.recordSupervisionStatus({
    mcpRunning: true,
    nativeAlive: true,
    tunnelRunning: true,
    componentsReady: true,
    connectorReady: true,
    fullyReady: true
  });
  host.ensureRecoveryPlane = async () => { recoveryPlaneCalls += 1; };
  host.superviseElectronUi = async () => { uiCalls += 1; };

  const deferred = await host.superviseOnce();
  assert.equal(ticketCalls, 1,
    'a retained deferred ticket must not be consumed again through ordinary supervision in the same tick');
  assert.equal(superviseCalls, 0, 'ordinary runtime supervision must yield to the deferred restart owner');
  assert.equal(lightweightCalls, 0, 'the deferred tick must not start a second runtime observation');
  assert.equal(recoveryPlaneCalls, 0, 'Recovery Plane mutation must yield while the restart journal owns the tick');
  assert.equal(uiCalls, 0, 'UI recovery must yield while the restart journal owns the tick');
  assert.equal(deferred.supervisorRequest.status, 'deferred');
  assert.equal(deferred.supervisorRequest.request_retained, true);
  assert.equal(deferred.mcpRunning, true, 'deferred is not evidence that the primary runtime already stopped');
  assert.equal(deferred.tunnelRunning, true, 'deferred preserves the last observed live Tunnel state');
  assert.equal(deferred.fullyReady, false);
  assert.equal(deferred.updateIncomplete, true);

  const accepted = await host.superviseOnce();
  assert.equal(ticketCalls, 2, 'the retained ticket is retried exactly once on the next watchdog tick');
  assert.equal(superviseCalls, 0, 'accepted HANDOFF must still bypass ordinary runtime supervision');
  assert.equal(lightweightCalls, 0);
  assert.equal(recoveryPlaneCalls, 0);
  assert.equal(uiCalls, 0);
  assert.equal(accepted.supervisorRequest.status, 'accepted');
  assert.equal(accepted.supervisorRequest.result.state, 'HANDOFF');
  assert.equal(accepted.mcpRunning, false);
  assert.equal(accepted.tunnelRunning, false);
  assert.equal(accepted.fullyReady, false);
  assert.equal(accepted.updateIncomplete, true);
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

test('Recovery Host adopts a complete central READY census after an ordinary host restart', async (t) => {
  const { host, calls } = readyAdoptionHost(t, { executionRole: 'central_executor' });
  const ready = seedCentralReadyEpoch(host);

  await host.start();
  assert.equal(host.readyAdoptionBlocksAdmission(), false);
  assert.deepEqual(calls.orchestratorEpochs, [ready.activation_epoch_id]);
  assert.deepEqual(calls.recoveryPlaneEpochs, [ready.activation_epoch_id]);
  assert.equal(calls.gatewayStart, 1);
  assert.equal(calls.ipcStart, 1);
  assert.deepEqual(host.activationEpochStore.current(), ready, 'adoption preserves immutable history');
});

test('Recovery Host rejects central settings with only a legacy direct READY receipt', async (t) => {
  const { host, calls } = readyAdoptionHost(t, { executionRole: 'central_executor' });
  const ready = seedReadyEpoch(host);

  const status = await host.start();
  assert.equal(host.readyAdoptionBlocksAdmission(), true);
  assert.ok(status.ready_adoption.reasons.includes('READY_EXECUTION_ROLE_MISMATCH'));
  assert.equal(status.activation_epoch.admission_open, false);
  assert.deepEqual(calls.orchestratorEpochs, []);
  assert.equal(calls.gatewayStart, 0);
  assert.equal(calls.ipcStart, 1);
  assert.deepEqual(host.activationEpochStore.current(), ready);
});

test('ordinary central recovery supervision never reads a cloud key or restarts retained direct Tunnel settings', async (t) => {
  const { host } = readyAdoptionHost(t, { executionRole: 'central_executor' });
  const current = {
    executionRole: 'central_executor',
    tunnelId: 'retained-primary-tunnel',
    recoveryTunnelId: 'retained-recovery-tunnel',
    workspace: host.paths.appRoot()
  };
  const calls = [];
  host.settings.load = () => current;
  host.secrets.get = () => { throw new Error('Central supervision must not access cloud credentials'); };
  host.orchestrator.ensureToken = async () => 'local-auth-fixture';
  host.orchestrator.activationEpochId = 'activation-central-ready-fixture';
  host.recoveryPlane.ensure = async (settings, options) => {
    calls.push({ settings, options });
    return { state: 'healthy', tunnel: { state: 'not_configured' } };
  };

  const status = await host.ensureRecoveryPlane();
  assert.equal(status.state, 'healthy');
  assert.equal(calls.length, 1);
  assert.equal(calls[0].settings.tunnelId, '');
  assert.equal(calls[0].settings.recoveryTunnelId, '');
  assert.equal(calls[0].settings.executionRole, 'central_executor');
  assert.deepEqual(calls[0].options, {
    authToken: 'local-auth-fixture', runtimeApiKey: '', activationEpochId: 'activation-central-ready-fixture'
  });
  assert.equal(current.tunnelId, 'retained-primary-tunnel', 'legacy rollback configuration stays intact');
  assert.equal(current.recoveryTunnelId, 'retained-recovery-tunnel');
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

test('runtime projection closes stale READY admission when the current primary runtime is incomplete', (t) => {
  const { host } = readyAdoptionHost(t);
  const ready = seedReadyEpoch(host);
  host.lastSupervisionStatus = {
    executionRole: 'direct_legacy',
    mcpRunning: false,
    nativeAlive: false,
    tunnelRunning: false,
    fullyReady: false,
    connectorRefreshRequired: false,
    connectorAcknowledgementPending: false,
    connectorContractState: 'UNAVAILABLE'
  };

  const projected = host.decorate({
    mcpRunning: false,
    nativeAlive: false,
    tunnelRunning: false,
    fullyReady: false,
    updateIncomplete: false,
    activationEpoch: {
      activation_epoch_id: ready.activation_epoch_id,
      operation_id: ready.operation_id,
      state: 'READY',
      admission_open: true,
      update_incomplete: false
    },
    status: {
      fullyReady: false,
      activationEpoch: {
        activation_epoch_id: ready.activation_epoch_id,
        operation_id: ready.operation_id,
        state: 'READY',
        admission_open: true,
        update_incomplete: false
      }
    }
  }, { preferCachedRuntime: true });

  assert.equal(projected.updateIncomplete, true);
  assert.equal(projected.activationEpoch.admission_open, false);
  assert.equal(projected.activationEpoch.update_incomplete, true);
  assert.equal(projected.activationEpoch.state, 'READY', 'durable state remains visible as history');
  assert.equal(projected.status.activationEpoch.admission_open, false);
  assert.equal(projected.recoveryHost.activation_epoch.admission_open, false);
  assert.equal(host.activationEpochStore.current().state, 'READY');
  assert.equal(host.activationEpochStore.current().admission_state, 'OPEN');
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

test('Recovery Host publishes the completed UI observation into its cached IPC projection', async (t) => {
  const { host } = uiRecoveryFixture(t);
  host.running = true;
  host.orchestrator.supervise = async () => ({
    mcpRunning: false,
    nativeAlive: false,
    tunnelRunning: false,
    componentsReady: false,
    connectorReady: false,
    fullyReady: false
  });
  host.ensureRecoveryPlane = async () => null;
  host.activation.observeUiPresence = async () => ({
    tracked: false,
    alive: false,
    pid: null,
    instance_id: null
  });
  host.activation.uiPresence = ({ preferCached = false } = {}) => ({
    tracked: false,
    alive: preferCached ? null : false,
    pid: null,
    instance_id: null
  });
  host.uiRecoveryInitialGraceUntil = 0;

  await host.superviseOnce();

  const status = await host.handlers()['recovery.status']();
  const snapshot = await host.handlers()['runtime.lightweight_snapshot']();
  assert.equal(status.electron_ui_recovery.alive, false,
    'status must retain the exact completed UI absence observation');
  assert.equal(snapshot.recoveryHost.electron_ui_recovery.alive, false,
    'the lightweight cached projection must carry the same exact observation');
});

test('fresh Recovery Host status proves an unregistered UI is missing for idle handoff', async (t) => {
  const { host } = uiRecoveryFixture(t);
  host.uiRecoveryInitialGraceUntil = 0;

  const observed = await host.handlers()['recovery.status']({ fresh: true });
  assert.equal(observed.electron_ui_recovery.registered, false);
  assert.equal(observed.electron_ui_recovery.alive, false);
  assert.equal(observed.electron_ui_recovery.state, 'missing');
});

test('fresh Recovery Host status keeps a registered but unverified UI fail closed', async (t) => {
  const { host, revision } = uiRecoveryFixture(t);
  host.activation.uiRegistration = {
    instance_id: 'fresh-status-uncertain-ui-0001',
    pid: 42001,
    process_start_token: '123456789',
    revision,
    registered_at_unix_ms: Date.now()
  };
  host.activation.asyncProcessIdentityObserver = async (pid) => ({ state: 'unavailable', pid });

  const observed = await host.handlers()['recovery.status']({ fresh: true });
  assert.equal(observed.electron_ui_recovery.registered, true);
  assert.equal(observed.electron_ui_recovery.alive, null);
  assert.equal(observed.electron_ui_recovery.state, 'unknown');
});

test('Recovery Host identity observation is a read-only exact MCP projection', async (t) => {
  const { host } = readyAdoptionHost(t);
  host.orchestrator.currentMcpHealth = async () => ({
    ready: true,
    process_instance_id: 'coding-mcp-process-observed-0001',
    instance_id: 'coding-mcp-server-observed-0001',
    activation_epoch_id: 'activation-ready-adoption-0001',
    tool_contract: { sha256: 'f'.repeat(64) }
  });

  const observation = await host.handlers()['runtime.identity_observation']();
  assert.equal(observation.observation_kind, 'mcp_identity_read_only');
  assert.equal(observation.recovery_host_instance_id, host.instanceId);
  assert.equal(observation.mcp_process_instance_id, 'coding-mcp-process-observed-0001');
  assert.equal(observation.mcp_server_instance_id, 'coding-mcp-server-observed-0001');
  assert.equal(observation.activation_epoch_id, 'activation-ready-adoption-0001');
  assert.equal(observation.current_activation_epoch_id, 'activation-ready-adoption-0001');
  assert.equal(observation.tool_contract_sha256, 'f'.repeat(64));
  assert.equal(observation.identity_current, true);
});

test('Recovery Host admits a control-plane read-only context only from explicit local policy and strict runtime evidence', async (t) => {
  const { host } = readyAdoptionHost(t);
  const expiresAtMs = Date.now() + 60_000;
  const policy = {
    schema_version: 2,
    enabled: true,
    server_origin: 'https://control.example.test',
    owner_id: 'owner-control-plane-0001',
    device_id: host.deviceIdentity.device_id,
    endpoint_id: 'endpoint-control-plane-0001',
    workspace_id: 'workspace-control-plane-0001',
    workspace_generation: 'generation-control-plane-0001',
    expires_at_ms: expiresAtMs,
    facade_contract: {
      schema_version: 3,
      profile: 'control-plane-read-only-queue-v2',
      sha256: 'f'.repeat(64)
    }
  };
  fs.writeFileSync(host.paths.controlPlaneReadOnlyPolicyFile(), `${JSON.stringify(policy)}\n`, 'utf8');
  const request = {
    server_origin: policy.server_origin,
    owner_id: policy.owner_id,
    device_id: policy.device_id,
    endpoint_id: policy.endpoint_id,
    workspace_id: policy.workspace_id,
    workspace_generation: policy.workspace_generation,
    context_id: 'context-control-plane-0001',
    binding_id: 'binding-control-plane-0001',
    action_id: 'action-control-plane-0001',
    attempt_id: 'attempt-control-plane-0001',
    tool_name: 'workspace_context',
    arguments: { detail: 'compact', max_entries: 1 },
    expires_at_ms: expiresAtMs - 1,
    facade_contract: { ...policy.facade_contract }
  };
  host.orchestrator.lightweightSnapshot = async () => ({
    componentsReady: true,
    connectorReady: true,
    fullyReady: true,
    updateIncomplete: false,
    connectorContractState: 'CURRENT_ACKNOWLEDGED',
    connectorFreshnessMode: 'current_process_discovery',
    connectorRediscovered: true,
    connectorRediscoveredAt: new Date().toISOString(),
    connectorRefreshRequired: false,
    connectorAcknowledgementPending: false
  });
  host.orchestrator.currentMcpHealth = async () => ({
    ready: true,
    process_instance_id: 'mcp-process-control-plane-0001',
    instance_id: 'mcp-server-control-plane-0001',
    activation_epoch_id: 'activation-ready-adoption-0001',
    tool_contract: { sha256: 'a'.repeat(64) }
  });
  let calls = 0;
  host.orchestrator.controlPlaneReadOnlyWorkspaceContext = async (admission) => {
    calls += 1;
    assert.equal(admission.tool_name, 'workspace_context');
    assert.deepEqual(admission.arguments, { detail: 'compact', max_entries: 1 });
    assert.equal(admission.actor.client_id, 'electron-control-plane-bridge');
    assert.deepEqual(admission.facade_contract, policy.facade_contract);
    return {
      schema_version: 1,
      operation_kind: 'control_plane_read_only_workspace_context',
      action_id: admission.action_id,
      attempt_id: admission.attempt_id,
      local_handle: `cp_ro_${'b'.repeat(48)}`,
      workspace_accessed: true,
      policy_sha256: admission.policy_sha256,
      actor: admission.actor,
      runtime_identity: {
        activation_epoch_id: 'activation-ready-adoption-0001',
        process_instance_id: 'mcp-process-control-plane-0001',
        server_instance_id: 'mcp-server-control-plane-0001',
        tool_contract_sha256: 'a'.repeat(64)
      },
      facade_contract: { ...admission.facade_contract },
      workspace_summary: controlPlaneWorkspaceSummary(),
      workspace_summary_sha256: workspaceSummaryDigest(controlPlaneWorkspaceSummary()),
      response_sha256: 'c'.repeat(64)
    };
  };

  const result = await host.handlers()['runtime.control_plane_read_only_workspace_context'](request);
  assert.equal(result.workspace_accessed, true);
  assert.equal(calls, 1);

  host.orchestrator.controlPlaneReadOnlyWorkspaceContext = async (admission) => ({
    schema_version: 1,
    operation_kind: 'control_plane_read_only_workspace_context',
    action_id: admission.action_id,
    attempt_id: admission.attempt_id,
    local_handle: `cp_ro_${'b'.repeat(48)}`,
    workspace_accessed: true,
    policy_sha256: admission.policy_sha256,
    actor: admission.actor,
    runtime_identity: {
      activation_epoch_id: 'activation-ready-adoption-0001',
      process_instance_id: 'mcp-process-control-plane-0001',
      server_instance_id: 'mcp-server-control-plane-0001',
      tool_contract_sha256: 'a'.repeat(64)
    },
    facade_contract: { ...admission.facade_contract, sha256: 'e'.repeat(64) },
    workspace_summary: controlPlaneWorkspaceSummary(),
    workspace_summary_sha256: workspaceSummaryDigest(controlPlaneWorkspaceSummary()),
    response_sha256: 'c'.repeat(64)
  });
  await assert.rejects(
    host.handlers()['runtime.control_plane_read_only_workspace_context']({ ...request, attempt_id: 'attempt-control-plane-contract-drift-0001' }),
    { code: 'CONTROL_PLANE_BRIDGE_CONTRACT_CHANGED' }
  );

  const validReadOnlyResult = (admission, overrides = {}) => ({
    schema_version: 1,
    operation_kind: 'control_plane_read_only_workspace_context',
    action_id: admission.action_id,
    attempt_id: admission.attempt_id,
    local_handle: `cp_ro_${'b'.repeat(48)}`,
    workspace_accessed: true,
    policy_sha256: admission.policy_sha256,
    actor: admission.actor,
    runtime_identity: {
      activation_epoch_id: 'activation-ready-adoption-0001',
      process_instance_id: 'mcp-process-control-plane-0001',
      server_instance_id: 'mcp-server-control-plane-0001',
      tool_contract_sha256: 'a'.repeat(64)
    },
    facade_contract: { ...admission.facade_contract },
    workspace_summary: controlPlaneWorkspaceSummary(),
    workspace_summary_sha256: workspaceSummaryDigest(controlPlaneWorkspaceSummary()),
    response_sha256: 'c'.repeat(64),
    ...overrides
  });
  host.orchestrator.controlPlaneReadOnlyWorkspaceContext = async (admission) => validReadOnlyResult(admission, {
    workspace_summary: {}
  });
  await assert.rejects(
    host.handlers()['runtime.control_plane_read_only_workspace_context']({ ...request, attempt_id: 'attempt-control-plane-summary-invalid-0001' }),
    { code: 'CONTROL_PLANE_BRIDGE_WORKSPACE_SUMMARY_INVALID' }
  );

  host.orchestrator.controlPlaneReadOnlyWorkspaceContext = async (admission) => validReadOnlyResult(admission, {
    workspace_summary_sha256: 'd'.repeat(64)
  });
  await assert.rejects(
    host.handlers()['runtime.control_plane_read_only_workspace_context']({ ...request, attempt_id: 'attempt-control-plane-summary-digest-0001' }),
    { code: 'CONTROL_PLANE_BRIDGE_WORKSPACE_SUMMARY_DIGEST_INVALID' }
  );

  const foreignPolicy = { ...policy, device_id: 'device-control-plane-foreign-0001' };
  fs.writeFileSync(host.paths.controlPlaneReadOnlyPolicyFile(), `${JSON.stringify(foreignPolicy)}\n`, 'utf8');
  await assert.rejects(
    host.handlers()['runtime.control_plane_read_only_workspace_context']({ ...request, device_id: foreignPolicy.device_id, attempt_id: 'attempt-control-plane-foreign-0001' }),
    { code: 'CONTROL_PLANE_BRIDGE_DEVICE_MISMATCH' }
  );
  assert.equal(calls, 1, 'a policy copied to another device must block before local MCP admission');
  fs.writeFileSync(host.paths.controlPlaneReadOnlyPolicyFile(), `${JSON.stringify(policy)}\n`, 'utf8');

  host.orchestrator.lightweightSnapshot = async () => ({
    componentsReady: true,
    connectorReady: true,
    fullyReady: true,
    updateIncomplete: false,
    connectorContractState: 'CURRENT_COMPATIBLE_ACKNOWLEDGED',
    connectorFreshnessMode: 'compatible_activation_bootstrap',
    connectorRediscovered: false,
    connectorRefreshRequired: false,
    connectorAcknowledgementPending: false
  });
  await assert.rejects(
    host.handlers()['runtime.control_plane_read_only_workspace_context']({ ...request, attempt_id: 'attempt-control-plane-0002' }),
    { code: 'CONTROL_PLANE_BRIDGE_RUNTIME_UNREADY' }
  );
  assert.equal(calls, 1, 'compatible bootstrap must block before the local MCP action');
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

test('Recovery Host rejects UI registration from another installation', async (t) => {
  const paths = fixture(t);
  const { host, revision } = uiRecoveryFixture(t, { paths, revision: 'e'.repeat(64) });
  const expected = paths.runtimeIdentity();
  await assert.rejects(
    host.handlers()['client.register_ui_revision']({
      instance_id: 'foreign-electron-ui-0001',
      pid: process.pid,
      revision,
      started_at_unix_ms: Date.now(),
      runtime_mode: 'packaged',
      installation_id: 'f'.repeat(64)
    }),
    {
      code: 'RECOVERY_HOST_INSTALLATION_MISMATCH',
      details: {
        expected_installation_id: expected.installation_id,
        observed_installation_id: 'f'.repeat(64),
        expected_runtime_mode: expected.mode,
        observed_runtime_mode: 'packaged'
      }
    }
  );
  assert.equal(host.activation.uiRegistration, null);
});

test('Recovery Host exposes host and UI runtime identities separately', async (t) => {
  const paths = fixture(t);
  const { host, revision } = uiRecoveryFixture(t, { paths, revision: 'f'.repeat(64) });
  const identity = paths.runtimeIdentity();
  await host.handlers()['client.register_ui_revision']({
    instance_id: 'matching-electron-ui-0001',
    pid: process.pid,
    revision,
    started_at_unix_ms: Date.now(),
    runtime_mode: identity.mode,
    installation_id: identity.installation_id
  });
  const status = host.uiRecoveryStatus();
  assert.equal(status.recovery_host_runtime_mode, identity.mode);
  assert.equal(status.recovery_host_installation_id, identity.installation_id);
  assert.equal(status.ui_runtime_mode, identity.mode);
  assert.equal(status.ui_installation_id, identity.installation_id);
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
    inspectCodeActivation: async () => ({ executor_cleanup_supported: true, safe: true, code: 'READY' }),
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
    inspectCodeActivation: async () => ({ executor_cleanup_supported: true, safe: true, code: 'READY' }),
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
    inspectCodeActivation: async () => ({ executor_cleanup_supported: true, safe: true, code: 'READY' }),
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

test('real Electron children strip deferred worker-only environment contracts', () => {
  const inherited = {
    ELECTRON_RUN_AS_NODE: '1',
    FULL_CLEAN_DEFERRED_WORKER: '1',
    FULL_CLEAN_SOURCE_CHECKPOINT_JSON: '{"checkpoint_id":"must-not-cross"}',
    SAFE_PARENT_VALUE: 'preserved'
  };
  const env = processEnvironment('recovery-host', {
    bootstrapId: 'bootstrap-operation-0001'
  }, inherited);
  assert.equal(Object.hasOwn(env, 'ELECTRON_RUN_AS_NODE'), false);
  assert.equal(Object.hasOwn(env, 'FULL_CLEAN_DEFERRED_WORKER'), false);
  assert.equal(Object.hasOwn(env, 'FULL_CLEAN_SOURCE_CHECKPOINT_JSON'), false);
  assert.equal(env.SAFE_PARENT_VALUE, 'preserved');
  assert.equal(env.WEBCODEX_PROCESS_ROLE, 'recovery-host');
  assert.equal(env.WEBCODEX_RECOVERY_BOOTSTRAP_ID, 'bootstrap-operation-0001');
  assert.equal(inherited.ELECTRON_RUN_AS_NODE, '1');
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
  const managerStart = main.indexOf('function openManagerWindow(');
  const startupStart = main.indexOf('app.whenReady().then(async () => {');
  const startupEnd = main.indexOf("log.info('Coding Tools MCP UI đã kết nối Recovery Host');", startupStart);
  assert.ok(createStart >= 0 && managerStart > createStart);
  assert.ok(startupStart >= 0 && startupEnd > startupStart);

  const createSource = main.slice(createStart, managerStart);
  const revealFunction = createSource.indexOf('const revealOpeningWindow =');
  const readyListener = createSource.indexOf("openingWindow.once('ready-to-show'");
  const loadFile = createSource.indexOf('openingWindow.loadFile(');
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
  assert.match(managerSource, /const targetWindow = showChatWindow\(\)/,
    'manager navigation must use the already guarded primary window');
  assert.doesNotMatch(managerSource, /new BrowserWindow|\.loadFile\(/,
    'manager navigation must not create or load a second window');
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
  const coordinateRestart = host.fullCleanActivation.restart.bind(host.fullCleanActivation);
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

  closureInput.affected_components = [];
  await assert.rejects(handler({ reason: 'operator_restart' }), {
    code: 'ACTIVATION_SOURCE_CHECKPOINT_NOT_ELIGIBLE'
  });
  await handler({ mode: 'full_clean_execution_role_handoff', executionRole: 'central_executor' });
  assert.equal(calls.length, 3, 'operator role migration does not require an accepted code component change');
  assert.equal(calls[2].mode, 'full_clean_execution_role_handoff');
  assert.equal(calls[2].sourceCheckpoint, undefined);
  assert.equal(calls[2].refresh, undefined);
  assert.equal(calls[2].reason, 'operator_central_executor_handoff');

  host.autoActivation.status = () => ({});
  await assert.rejects(handler({ reason: 'operator_restart' }), {
    code: 'ACTIVATION_SOURCE_CHECKPOINT_UNAVAILABLE'
  });
  await handler({ mode: 'full_clean_execution_role_handoff', executionRole: 'central_executor' });
  assert.equal(calls.length, 4, 'role migration also supports installations with no accepted-code closure');

  // Use the real coordinator admission for ambiguous requests: the Recovery
  // Host must neither hide supplied source authority nor route automatic=true
  // around the handoff validator through a soft restart.
  host.fullCleanActivation.restart = coordinateRestart;
  for (const mixed of [
    { sourceCheckpoint: SOURCE_CHECKPOINT },
    { source_checkpoint: SOURCE_CHECKPOINT },
    { component: 'recovery_host' },
    { expectedDiskRevision: 'a'.repeat(64) },
    { automatic: true },
    { soft: true },
    { allowAcceptancePending: true }
  ]) {
    await assert.rejects(handler({
      mode: 'full_clean_execution_role_handoff', executionRole: 'central_executor', ...mixed
    }), { code: 'ACTIVATION_EXECUTION_ROLE_HANDOFF_INVALID' });
  }
  assert.equal(host.activationEpochStore.current(), null, 'invalid mixed handoff must not create a durable transaction');
});
