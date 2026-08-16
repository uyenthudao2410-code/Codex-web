const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { NativeService, runtimeFingerprint, currentRuntimeState } = require('../electron/services/nativeService');
const { normalizeProxyValue } = require('../electron/services/proxyService');
const runtimePaths = require('../electron/paths');
const runtimeStatePath = path.join(os.tmpdir(), `webcodex-runtime-lifecycle-${process.pid}.json`);
const supervisorRequestPath = path.join(os.tmpdir(), `webcodex-supervisor-request-${process.pid}.json`);
runtimePaths.stateFile = () => runtimeStatePath;
runtimePaths.supervisorRequestFile = () => supervisorRequestPath;
fs.writeFileSync(runtimeStatePath, JSON.stringify({ manualStop: false }), 'utf8');
test.after(() => {
  fs.rmSync(runtimeStatePath, { force: true });
  fs.rmSync(supervisorRequestPath, { force: true });
  fs.rmSync(`${supervisorRequestPath}.bak`, { force: true });
});
test.beforeEach(() => {
  fs.rmSync(supervisorRequestPath, { force: true });
  fs.rmSync(`${supervisorRequestPath}.bak`, { force: true });
});
const { RuntimeOrchestrator } = require('../electron/services/runtimeOrchestrator');

function recoveryHarness(status) {
  const calls = { restart: 0, tunnel: 0 };
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.lightweightSnapshot = async () => ({ ...status });
  orchestrator.restart = async () => { calls.restart += 1; };
  orchestrator.recoverTunnelOnly = async () => { calls.tunnel += 1; };
  orchestrator.isManuallyStopped = () => false;
  orchestrator.heartbeatFailures = 2;
  orchestrator.heartbeatFailureKind = status.mcpRunning
    ? 'tunnel_unavailable'
    : (status.nativeAlive ? 'mcp_health_unavailable' : 'mcp_process_exited');
  return { orchestrator, calls };
}

test('native runtime identity changes with workspace and port while tool mode stays smart', () => {
  const base = { workspace: 'C:\\work\\one', mcpPort: 18766, permissionMode: 'safe' };
  assert.equal(runtimeFingerprint(base), runtimeFingerprint({ ...base }));
  assert.notEqual(runtimeFingerprint(base), runtimeFingerprint({ ...base, workspace: 'C:\\work\\two' }));
  assert.notEqual(runtimeFingerprint(base), runtimeFingerprint({ ...base, mcpPort: 18767 }));
  assert.notEqual(runtimeFingerprint(base), runtimeFingerprint({ ...base, authorizedRoots: ['D:\\shared'] }));
  assert.equal(runtimeFingerprint(base), runtimeFingerprint({ ...base, toolMode: 'readonly' }));
});

test('proxy values from Windows settings are normalized', () => {
  assert.equal(normalizeProxyValue('127.0.0.1:7890'), 'http://127.0.0.1:7890');
  assert.equal(normalizeProxyValue('http=127.0.0.1:8080;https=127.0.0.1:7890'), 'http://127.0.0.1:7890');
  assert.equal(normalizeProxyValue('http://user:pass@127.0.0.1:7890'), '');
});

test('background runtime processes are hidden and never detached on Windows', () => {
  const fs = require('node:fs');
  const path = require('node:path');
  const root = path.resolve(__dirname, '..');
  for (const relative of ['electron/services/nativeService.js', 'electron/services/tunnelService.js']) {
    const source = fs.readFileSync(path.join(root, relative), 'utf8');
    assert.match(source, /windowsHide:\s*true/);
    assert.match(source, /detached:\s*false/);
    assert.doesNotMatch(source, /detached:\s*true/);
  }
  const runner = fs.readFileSync(path.join(root, 'electron/services/commandRunner.js'), 'utf8');
  assert.doesNotMatch(runner, /spawnDetached/);
  // Process launch policy is shared by the extracted process helper rather
  // than duplicated in server.py.
  const processPolicy = fs.readFileSync(path.join(root, 'resources/coding-tools-mcp/coding_tools_mcp/processes.py'), 'utf8');
  assert.match(processPolicy, /def hidden_process_popen_kwargs/);
  assert.match(processPolicy, /CREATE_NO_WINDOW/);
  const execTools = fs.readFileSync(path.join(root, 'resources/coding-tools-mcp/coding_tools_mcp/exec_tools.py'), 'utf8');
  assert.match(execTools, /encoding="utf-8"/);
});

test('runtime state migration keeps only current native and tunnel fields', () => {
  assert.deepEqual(
    currentRuntimeState({ nativePid: 1, tunnelPid: 2, nativeCodeRevision: 'abc', obsoletePid: 3 }),
    { nativePid: 1, tunnelPid: 2, nativeCodeRevision: 'abc' }
  );
});

test('native revision status is pending only when the live process has a captured revision', () => {
  const paths = {
    stateFile: () => runtimeStatePath,
    appRoot: () => path.resolve(__dirname, '..'),
    resourcesRoot: () => path.resolve(__dirname, '..', 'resources')
  };
  const revisions = {
    status: (_component, runningRevision) => ({
      running_revision: runningRevision || null,
      disk_revision: 'disk-revision',
      update_pending: runningRevision ? runningRevision !== 'disk-revision' : null,
      state: runningRevision ? (runningRevision === 'disk-revision' ? 'current' : 'update_pending') : 'unknown'
    })
  };
  const native = new NativeService({ info() {} }, paths, revisions);
  try {
    fs.writeFileSync(runtimeStatePath, JSON.stringify({ nativePid: process.pid, nativeCodeRevision: 'running-revision' }));
    const pending = native.revisionStatus();
    assert.equal(pending.update_pending, true);
    assert.equal(pending.state, 'update_pending');

    fs.writeFileSync(runtimeStatePath, JSON.stringify({ nativePid: process.pid }));
    const legacy = native.revisionStatus();
    assert.equal(legacy.running_revision, null);
    assert.equal(legacy.update_pending, null);
    assert.equal(legacy.state, 'unknown');
  } finally {
    fs.writeFileSync(runtimeStatePath, JSON.stringify({ manualStop: false }));
  }
});

test('runtime recovery projection exposes only local typed supervisor evidence', () => {
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({}) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.recovering = true;
  orchestrator.heartbeatFailures = 3;
  orchestrator.heartbeatFailureKind = 'tunnel_unavailable';
  orchestrator.recoveryAttempts = 2;
  orchestrator.nextRecoveryAt = 123456;
  orchestrator.autoRecoveryBlocked = true;
  orchestrator.lastStartFailure = 'typed local failure';
  orchestrator.deferredRecoveryCount = 1;
  assert.deepEqual(orchestrator.recoveryStatus(), {
    recovering: true,
    failures: 3,
    failureKind: 'tunnel_unavailable',
    recoveryAttempts: 2,
    nextRecoveryAt: 123456,
    recoveryBlocked: true,
    lastStartFailure: 'typed local failure',
    deferredRecoveryCount: 1
  });
});

test('revision observation failure cannot break runtime supervision', () => {
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({}) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.native = { revisionStatus: () => { throw new Error('observer failed'); } };
  assert.deepEqual(orchestrator.codingMcpRevisionStatus(), {
    running_revision: null,
    disk_revision: null,
    update_pending: null,
    state: 'unavailable',
    error_code: 'REVISION_UNAVAILABLE'
  });
});

test('connector contract stays pending until operator acknowledges the current hash', () => {
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: 'C:\\work\\one' }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  const contract = { schema_version: 1, profile: 'smart-v3', sha256: 'a'.repeat(64) };
  assert.equal(orchestrator.connectorContractStatus(contract).refreshRequired, true);
  orchestrator.acknowledgeConnectorContractHash(contract);
  const acknowledged = orchestrator.connectorContractStatus(contract);
  assert.equal(acknowledged.refreshRequired, false);
  assert.equal(acknowledged.acknowledgedSha256, contract.sha256);
});

test('supervisor consumes a fresh workspace-bound restart ticket exactly once', async () => {
  const workspace = 'C:\\work\\one';
  const calls = { activate: 0 };
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace, autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.lightweightSnapshot = async () => ({ fullyReady: true, mcpRunning: true, nativeAlive: true, tunnelRunning: true });
  orchestrator.currentMcpHealth = async () => ({ process_instance_id: 'process-one', instance_id: 'server-one' });
  orchestrator.revisions.disk = () => ({ revision: 'a'.repeat(64) });
  orchestrator.activateCodingMcpUpdate = async (revision) => { calls.activate += 1; return { new_revision: revision }; };
  const now = Date.now();
  fs.writeFileSync(supervisorRequestPath, JSON.stringify({
    version: 1,
    action: 'restart',
    ticket_id: 'ticket-1',
    process_instance_id: 'process-one',
    server_instance_id: 'server-one',
    workspace,
    requested_at_unix_ms: now - 1000,
    not_before_unix_ms: now - 1,
    expires_at_unix_ms: now + 30000
  }), 'utf8');
  const result = await orchestrator.supervise();
  assert.equal(calls.activate, 1);
  assert.equal(fs.existsSync(supervisorRequestPath), false);
  assert.equal(result.supervisorRequest.ticketId, 'ticket-1');
  assert.equal(result.supervisorRequest.status, 'completed');
  assert.equal(result.supervisorRequest.component, 'coding_mcp');
});

test('Coding MCP activation verifies revision and a new process identity without touching the tunnel', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-mcp-activation-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const stateFile = path.join(root, 'runtime-state.json');
  fs.writeFileSync(stateFile, JSON.stringify({ nativeInstanceId: 'old-supervisor', nativeCodeRevision: 'a'.repeat(64) }));
  const expectedRevision = 'b'.repeat(64);
  const paths = { stateFile: () => stateFile };
  const orchestrator = new RuntimeOrchestrator({
    paths,
    settings: { load: () => ({ workspace: root, mcpPort: 32123 }) },
    secrets: { get: () => 'token' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    revisionTracker: { disk: () => ({ revision: expectedRevision }) }
  });
  orchestrator.validate = () => {};
  orchestrator.ensureToken = async () => 'token';
  let health = {
    ready: true,
    workspace: root,
    process_instance_id: 'old-process',
    instance_id: 'old-server',
    code_revision: 'a'.repeat(64)
  };
  orchestrator.currentMcpHealth = async () => health;
  const calls = { stop: 0, start: 0, tunnel: 0 };
  orchestrator.native = {
    stop: async () => { calls.stop += 1; return true; },
    start: async (_settings, _token, _progress, options) => {
      calls.start += 1;
      assert.equal(options.expectedCodeRevision, expectedRevision);
      health = {
        ready: true,
        workspace: root,
        process_instance_id: 'new-process',
        instance_id: 'new-server',
        code_revision: expectedRevision
      };
      return { instanceId: 'new-supervisor', codeRevision: expectedRevision };
    },
    status: async () => true
  };
  orchestrator.tunnel = { stop: async () => { calls.tunnel += 1; } };

  const result = await orchestrator.activateCodingMcpUpdate(expectedRevision);

  assert.equal(result.old_instance_id, 'old-process');
  assert.equal(result.new_instance_id, 'new-process');
  assert.equal(result.old_server_instance_id, 'old-server');
  assert.equal(result.new_server_instance_id, 'new-server');
  assert.equal(result.new_revision, expectedRevision);
  assert.equal(result.tunnel_preserved, true);
  assert.deepEqual(calls, { stop: 1, start: 1, tunnel: 0 });
});

test('Coding MCP activation fails before stop when the requested revision changed', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-mcp-activation-stale-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const paths = { stateFile: () => path.join(root, 'runtime-state.json') };
  const orchestrator = new RuntimeOrchestrator({
    paths,
    settings: { load: () => ({ workspace: root, mcpPort: 32123 }) },
    secrets: { get: () => 'token' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    revisionTracker: { disk: () => ({ revision: 'c'.repeat(64) }) }
  });
  orchestrator.validate = () => {};
  orchestrator.ensureToken = async () => 'token';
  let stopped = false;
  orchestrator.native = { stop: async () => { stopped = true; } };

  await assert.rejects(orchestrator.activateCodingMcpUpdate('b'.repeat(64)), { code: 'REVISION_CHANGED' });
  assert.equal(stopped, false);
});

test('supervisor rejects stale or wrong-workspace restart tickets without restarting', async () => {
  const workspace = 'C:\\work\\one';
  const calls = { restart: 0 };
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace, autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.lightweightSnapshot = async () => ({ fullyReady: true, mcpRunning: true, nativeAlive: true, tunnelRunning: true });
  orchestrator.restart = async () => { calls.restart += 1; };
  const now = Date.now();
  fs.writeFileSync(supervisorRequestPath, JSON.stringify({
    version: 1,
    action: 'restart',
    ticket_id: 'ticket-stale',
    workspace: 'C:\\work\\other',
    requested_at_unix_ms: now - 120000,
    not_before_unix_ms: now - 119000,
    expires_at_unix_ms: now - 60000
  }), 'utf8');
  await orchestrator.supervise();
  assert.equal(calls.restart, 0);
  assert.equal(fs.existsSync(supervisorRequestPath), false);
});

test('supervisor never recovers a restart ticket from json backup', async () => {
  const workspace = 'C:\\work\\one';
  const calls = { restart: 0 };
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace, autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.lightweightSnapshot = async () => ({ fullyReady: true, mcpRunning: true, nativeAlive: true, tunnelRunning: true });
  orchestrator.restart = async () => { calls.restart += 1; };
  const now = Date.now();
  fs.writeFileSync(supervisorRequestPath, '{invalid-json', 'utf8');
  fs.writeFileSync(`${supervisorRequestPath}.bak`, JSON.stringify({
    version: 1,
    action: 'restart',
    ticket_id: 'ticket-from-backup',
    workspace,
    requested_at_unix_ms: now - 1000,
    not_before_unix_ms: now - 1,
    expires_at_unix_ms: now + 30000
  }), 'utf8');
  await orchestrator.supervise();
  assert.equal(calls.restart, 0);
  assert.equal(fs.existsSync(supervisorRequestPath), false);
  assert.equal(fs.existsSync(`${supervisorRequestPath}.bak`), false);
});

test('supervisor recovers only the tunnel when MCP remains healthy', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: true,
    nativeAlive: true,
    tunnelRunning: false
  });
  await orchestrator.supervise();
  assert.equal(calls.tunnel, 1);
  assert.equal(calls.restart, 0);
});

test('supervisor trusts MCP health over a stale owned-process record', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: true,
    nativeAlive: false,
    tunnelRunning: false
  });
  await orchestrator.supervise();
  assert.equal(calls.tunnel, 1);
  assert.equal(calls.restart, 0);
});

test('supervisor does not kill a live MCP process after transient health failures', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: false,
    nativeAlive: true,
    tunnelRunning: true
  });
  const result = await orchestrator.supervise();
  assert.equal(calls.tunnel, 0);
  assert.equal(calls.restart, 0);
  assert.equal(result.recoveryDeferred, true);
  assert.equal(result.recoveryReason, 'mcp_process_alive_health_unavailable');
});

test('supervisor defers recovery when both health checks fail but MCP process remains alive', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: false,
    nativeAlive: true,
    tunnelRunning: false
  });
  const result = await orchestrator.supervise();
  assert.equal(calls.tunnel, 0);
  assert.equal(calls.restart, 0);
  assert.equal(result.recoveryDeferred, true);
});

test('supervisor performs a full restart only after the owned MCP process exits', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: false,
    nativeAlive: false,
    tunnelRunning: true
  });
  await orchestrator.supervise();
  assert.equal(calls.tunnel, 0);
  assert.equal(calls.restart, 1);
});

test('supervisor requires three consecutive failures of the same kind', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: false,
    nativeAlive: true,
    tunnelRunning: true
  });
  orchestrator.heartbeatFailureKind = 'tunnel_unavailable';
  const result = await orchestrator.supervise();
  assert.equal(result.failures, 1);
  assert.equal(calls.tunnel, 0);
  assert.equal(calls.restart, 0);
});

test('supervisor escalates to a full restart after repeated deferrals of a hung live MCP', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: false,
    nativeAlive: true,
    tunnelRunning: false
  });
  const maxDeferred = 6;
  for (let attempt = 1; attempt < maxDeferred; attempt += 1) {
    orchestrator.nextRecoveryAt = 0;
    const result = await orchestrator.supervise();
    assert.equal(result.recoveryDeferred, true);
    assert.equal(calls.restart, 0);
  }
  orchestrator.nextRecoveryAt = 0;
  await orchestrator.supervise();
  assert.equal(calls.restart, 1);
  assert.equal(calls.tunnel, 0);
  assert.equal(orchestrator.deferredRecoveryCount, 0);
});

test('supervisor resets the deferral counter once the runtime becomes healthy', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: false,
    nativeAlive: true,
    tunnelRunning: false
  });
  orchestrator.nextRecoveryAt = 0;
  const deferred = await orchestrator.supervise();
  assert.equal(deferred.recoveryDeferred, true);
  assert.equal(orchestrator.deferredRecoveryCount, 1);
  orchestrator.lightweightSnapshot = async () => ({
    fullyReady: true,
    mcpRunning: true,
    nativeAlive: true,
    tunnelRunning: true
  });
  await orchestrator.supervise();
  assert.equal(orchestrator.deferredRecoveryCount, 0);
  assert.equal(calls.restart, 0);
});

test('native and tunnel stop paths own the whole process tree on Windows', () => {
  const fs = require('node:fs');
  const path = require('node:path');
  const root = path.resolve(__dirname, '..');
  for (const relative of ['electron/services/nativeService.js', 'electron/services/tunnelService.js']) {
    const source = fs.readFileSync(path.join(root, relative), 'utf8');
    assert.match(source, /taskkill\.exe/);
    assert.match(source, /\/T/);
    assert.match(source, /\/F/);
  }
});
