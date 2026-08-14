const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { runtimeFingerprint, currentRuntimeState } = require('../electron/services/nativeService');
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
  const mcpServer = fs.readFileSync(path.join(root, 'resources/coding-tools-mcp/coding_tools_mcp/server.py'), 'utf8');
  assert.match(mcpServer, /CREATE_NO_WINDOW/);
  assert.match(mcpServer, /encoding="utf-8"/);
});

test('runtime state migration keeps only current native and tunnel fields', () => {
  assert.deepEqual(currentRuntimeState({ nativePid: 1, tunnelPid: 2, obsoletePid: 3 }), { nativePid: 1, tunnelPid: 2 });
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
    ticket_id: 'ticket-1',
    workspace,
    requested_at_unix_ms: now - 1000,
    not_before_unix_ms: now - 1,
    expires_at_unix_ms: now + 30000
  }), 'utf8');
  const result = await orchestrator.supervise();
  assert.equal(calls.restart, 1);
  assert.equal(fs.existsSync(supervisorRequestPath), false);
  assert.equal(result.supervisorRequest.ticketId, 'ticket-1');
  assert.equal(result.supervisorRequest.status, 'completed');
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
