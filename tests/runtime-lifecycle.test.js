const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { runtimeFingerprint, currentRuntimeState } = require('../electron/services/nativeService');
const { normalizeProxyValue } = require('../electron/services/proxyService');
const runtimePaths = require('../electron/paths');
const runtimeStatePath = path.join(os.tmpdir(), `webcodex-runtime-lifecycle-${process.pid}.json`);
runtimePaths.stateFile = () => runtimeStatePath;
fs.writeFileSync(runtimeStatePath, JSON.stringify({ manualStop: false }), 'utf8');
test.after(() => fs.rmSync(runtimeStatePath, { force: true }));
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
  const base = { workspace: 'C:\\work\\one', mcpPort: 18765, permissionMode: 'safe' };
  assert.equal(runtimeFingerprint(base), runtimeFingerprint({ ...base }));
  assert.notEqual(runtimeFingerprint(base), runtimeFingerprint({ ...base, workspace: 'C:\\work\\two' }));
  assert.notEqual(runtimeFingerprint(base), runtimeFingerprint({ ...base, mcpPort: 18766 }));
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
