const test = require('node:test');
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const http = require('node:http');
const runtimePaths = require('../electron/paths');
const runtimeStatePath = path.join(os.tmpdir(), `webcodex-live-supervisor-${process.pid}.json`);
runtimePaths.stateFile = () => runtimeStatePath;
fs.writeFileSync(runtimeStatePath, JSON.stringify({ manualStop: false }), 'utf8');
test.after(() => fs.rmSync(runtimeStatePath, { force: true }));
const { RuntimeOrchestrator } = require('../electron/services/runtimeOrchestrator');

const MCP_ROOT = path.resolve(__dirname, '..', 'resources', 'coding-tools-mcp');
const PYTHON = process.env.PYTHON || 'python';

function removeTempTree(target) {
  fs.rmSync(target, {
    recursive: true,
    force: true,
    // Windows can keep a just-exited child process directory briefly locked.
    // Node retries EBUSY/EPERM/ENOTEMPTY only for recursive removal, so keep
    // cleanup deterministic with a small bounded retry window instead of an
    // unbounded sleep or masking the failure.
    maxRetries: process.platform === 'win32' ? 10 : 0,
    retryDelay: process.platform === 'win32' ? 100 : 0
  });
}

function waitForHealth(port, timeoutMs = 30000) {
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + timeoutMs;
    const attempt = () => {
      const request = http.get({ host: '127.0.0.1', port, path: '/__control/health', timeout: 1500 }, (response) => {
        response.resume();
        if (response.statusCode === 200) { resolve(true); return; }
        retry();
      });
      request.on('error', retry);
      request.on('timeout', () => { request.destroy(); retry(); });
    };
    const retry = () => {
      if (Date.now() > deadline) { reject(new Error('MCP health timeout')); return; }
      setTimeout(attempt, 150);
    };
    attempt();
  });
}

function spawnMcp(workspace, port) {
  const env = { ...process.env, PYTHONIOENCODING: 'utf-8', CODING_TOOLS_MCP_TOOL_MODE: 'smart' };
  const child = spawn(PYTHON, ['-m', 'coding_tools_mcp', '--port', String(port), '--workspace', workspace], {
    cwd: MCP_ROOT,
    env,
    windowsHide: true,
    stdio: ['ignore', 'ignore', 'pipe']
  });
  let stderr = '';
  child.stderr.on('data', (chunk) => { stderr += chunk.toString().slice(-4000); });
  child._stderrTail = () => stderr;
  return child;
}

function makeHarness(mcpProcess, mcpPortSetting, tunnelStatus, failureKind) {
  const calls = { restart: 0, tunnelStarts: 0 };
  const orchestrator = new RuntimeOrchestrator({
    settings: {
      load: () => ({
        workspace: '',
        mcpPort: mcpPortSetting,
        tunnelId: 'test-tunnel',
        autoStartServices: true,
        proxyMode: 'auto',
        proxyUrl: '',
        healthPort: 18090
      })
    },
    secrets: {
      get: (key) => ({ runtimeApiKey: 'test-runtime-key', mcpAuthToken: 'test-mcp-token' }[key] || ''),
      set() {}
    },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    emitStatus() {}
  });
  orchestrator.heartbeatFailures = 2;
  orchestrator.heartbeatFailureKind = failureKind;
  orchestrator.native = {
    status: async () => mcpProcess.exitCode === null && mcpProcess.signalCode === null
  };
  orchestrator.tunnel = {
    status: async () => tunnelStatus,
    start: async () => { calls.tunnelStarts += 1; }
  };
  orchestrator.restart = async () => {
    calls.restart += 1;
    if (mcpProcess.exitCode === null && mcpProcess.signalCode === null) {
      mcpProcess.kill();
      await new Promise((resolve) => mcpProcess.once('exit', resolve));
    }
  };
  orchestrator.isManuallyStopped = () => false;
  return { orchestrator, calls };
}

test('live supervisor recovers only the tunnel and never kills a healthy MCP', async () => {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-sup-'));
  const port = 19121;
  const mcp = spawnMcp(workspace, port);
  try {
    await waitForHealth(port);
    const { orchestrator, calls } = makeHarness(mcp, port, false, 'tunnel_unavailable');
    await orchestrator.supervise();
    assert.equal(calls.tunnelStarts, 1);
    assert.equal(calls.restart, 0);
    assert.equal(mcp.exitCode, null, 'MCP must still be running after tunnel recovery'); assert.equal(mcp.signalCode, null);
  } finally {
    if (mcp.exitCode === null && mcp.signalCode === null) {
      mcp.kill();
      await new Promise((resolve) => mcp.once('exit', resolve));
    }
    removeTempTree(workspace);
  }
});

test('live supervisor escalates and force-restarts a hung live MCP after repeated deferrals', async () => {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-sup-'));
  const port = 19122;
  const mcp = spawnMcp(workspace, port);
  try {
    await waitForHealth(port);
    const { orchestrator, calls } = makeHarness(mcp, port + 1, false, 'mcp_health_unavailable');
    orchestrator.heartbeatFailures = 2;
    orchestrator.heartbeatFailureKind = 'mcp_health_unavailable';
    const maxDeferred = 6;
    for (let attempt = 1; attempt < maxDeferred; attempt += 1) {
      orchestrator.nextRecoveryAt = 0;
      const result = await orchestrator.supervise();
      assert.equal(result.recoveryDeferred, true);
      assert.equal(mcp.exitCode, null, 'MCP must survive the deferral phase'); assert.equal(mcp.signalCode, null);
    }
    orchestrator.nextRecoveryAt = 0;
    await orchestrator.supervise();
    assert.equal(calls.restart, 1);
    assert.equal(mcp.exitCode === null && mcp.signalCode === null, false, 'MCP must be force-killed by escalation restart');
  } finally {
    if (mcp.exitCode === null && mcp.signalCode === null) {
      mcp.kill();
      await new Promise((resolve) => mcp.once('exit', resolve));
    }
    removeTempTree(workspace);
  }
});

test('live supervisor full-restarts when the owned MCP process has exited', async () => {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-sup-'));
  const port = 19123;
  const mcp = spawnMcp(workspace, port);
  try {
    await waitForHealth(port);
    mcp.kill();
    await new Promise((resolve) => mcp.once('exit', resolve));
    const { orchestrator, calls } = makeHarness(mcp, port, false, 'mcp_process_exited');
    orchestrator.heartbeatFailures = 2;
    orchestrator.heartbeatFailureKind = 'mcp_process_exited';
    await orchestrator.supervise();
    assert.equal(calls.restart, 1);
    assert.equal(calls.tunnelStarts, 0);
  } finally {
    if (mcp.exitCode === null && mcp.signalCode === null) {
      mcp.kill();
      await new Promise((resolve) => mcp.once('exit', resolve));
    }
    removeTempTree(workspace);
  }
});
