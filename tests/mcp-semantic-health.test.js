const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const {
  probeMcpSemanticHealth,
  semanticFailurePolicy,
  SemanticMcpHealthWatchdog
} = require('../electron/services/mcpSemanticHealth');

async function withServer(handler, run) {
  const server = http.createServer(handler);
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  try { return await run(server.address().port); }
  finally { await new Promise((resolve) => server.close(resolve)); }
}

test('semantic probe proves workspace_context can execute, not only HTTP health', async () => {
  await withServer((request, response) => {
    assert.equal(request.url, '/mcp');
    assert.equal(request.headers.authorization, 'Bearer token');
    assert.equal(request.headers['mcp-protocol-version'], '2026-07-28');
    assert.equal(request.headers['mcp-method'], 'tools/call');
    assert.equal(request.headers['mcp-name'], 'workspace_context');
    let body = '';
    request.setEncoding('utf8');
    request.on('data', (chunk) => { body += chunk; });
    request.on('end', () => {
      const parsed = JSON.parse(body);
      assert.equal(parsed.method, 'tools/call');
      assert.equal(parsed.params.name, 'workspace_context');
      assert.deepEqual(parsed.params._meta, {
        'io.modelcontextprotocol/protocolVersion': '2026-07-28',
        'io.modelcontextprotocol/clientCapabilities': {},
        'io.modelcontextprotocol/clientInfo': { name: 'recovery-semantic-watchdog', version: '1' }
      });
      const payload = JSON.stringify({
        jsonrpc: '2.0',
        id: parsed.id,
        result: { structuredContent: { workspace: 'C:\\work\\one' } }
      });
      response.writeHead(200, { 'Content-Type': 'application/json' });
      response.end(payload);
    });
  }, async (port) => {
    const result = await probeMcpSemanticHealth({
      port,
      token: 'token',
      expectedWorkspace: 'C:\\work\\one',
      timeoutMs: 1000
    });
    assert.deepEqual(result, { ok: true, workspace: 'C:\\work\\one' });
  });
});

test('semantic probe rejects a live runtime bound to a different configured workspace', async () => {
  await withServer((_request, response) => {
    const payload = JSON.stringify({
      jsonrpc: '2.0',
      id: 'recovery-semantic-health',
      result: { structuredContent: { workspace: 'C:\\work\\old' } }
    });
    response.writeHead(200, { 'Content-Type': 'application/json' });
    response.end(payload);
  }, async (port) => {
    const result = await probeMcpSemanticHealth({
      port,
      token: 'token',
      expectedWorkspace: 'C:\\work\\current',
      timeoutMs: 1000
    });
    assert.equal(result.ok, false);
    assert.equal(result.reason, 'workspace_mismatch');
    assert.equal(result.workspace, 'C:\\work\\old');
    assert.equal(result.expectedWorkspace, 'C:\\work\\current');
  });
});

test('semantic probe rejects raw TaskGroup JSON-RPC failures even when HTTP is 200', async () => {
  await withServer((_request, response) => {
    const payload = JSON.stringify({
      jsonrpc: '2.0',
      id: 'recovery-semantic-health',
      error: { code: -32603, message: 'ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)' }
    });
    response.writeHead(200, { 'Content-Type': 'application/json' });
    response.end(payload);
  }, async (port) => {
    const result = await probeMcpSemanticHealth({ port, token: 'token', timeoutMs: 1000 });
    assert.equal(result.ok, false);
    assert.equal(result.reason, 'jsonrpc_error');
    assert.equal(result.errorCode, -32603);
    assert.match(result.errorMessage, /TaskGroup/);
  });
});

test('watchdog restarts through the existing orchestrator only after repeated semantic failures', async () => {
  const calls = { restart: 0 };
  const orchestrator = {
    busy: false,
    recovering: false,
    isManuallyStopped: () => false,
    restart: async (options) => {
      assert.deepEqual(options, { automatic: true });
      calls.restart += 1;
    }
  };
  const watchdog = new SemanticMcpHealthWatchdog({
    settings: { load: () => ({ mcpPort: 18766, workspace: 'C:\\work\\current' }) },
    secrets: { get: () => 'token' },
    orchestrator,
    log: { info() {}, warn() {}, error() {} },
    probe: async ({ expectedWorkspace }) => {
      assert.equal(expectedWorkspace, 'C:\\work\\current');
      return { ok: false, reason: 'jsonrpc_error', errorCode: -32603 };
    },
    failureThreshold: 3,
    restartCooldownMs: 1000
  });
  assert.equal((await watchdog.checkOnce()).failures, 1);
  assert.equal((await watchdog.checkOnce()).failures, 2);
  const third = await watchdog.checkOnce();
  assert.equal(third.recovered, true);
  assert.equal(third.failures, 3);
  assert.equal(calls.restart, 1);
  assert.equal(watchdog.failures, 0);
});

test('watchdog fail-closes a deterministic configured-workspace mismatch without restarting', async () => {
  const calls = { restart: 0 };
  const orchestrator = {
    busy: false,
    recovering: false,
    isManuallyStopped: () => false,
    restart: async (options) => {
      assert.deepEqual(options, { automatic: true });
      calls.restart += 1;
    }
  };
  const watchdog = new SemanticMcpHealthWatchdog({
    settings: { load: () => ({ mcpPort: 18766, workspace: 'C:\\work\\current' }) },
    secrets: { get: () => 'token' },
    orchestrator,
    log: { info() {}, warn() {}, error() {} },
    probe: async ({ expectedWorkspace }) => {
      assert.equal(expectedWorkspace, 'C:\\work\\current');
      return {
        ok: false,
        reason: 'workspace_mismatch',
        workspace: 'C:\\work\\old',
        expectedWorkspace
      };
    },
    failureThreshold: 3,
    restartCooldownMs: 1000
  });
  const result = await watchdog.checkOnce();
  assert.equal(result.recovered, undefined);
  assert.equal(result.failures, 1);
  assert.equal(result.recoveryBlocked, true);
  assert.equal(result.deterministicFailure, true);
  assert.equal(calls.restart, 0);
  assert.equal(watchdog.failures, 1);
  const second = await watchdog.checkOnce();
  assert.equal(second.recoveryBlocked, true);
  assert.equal(calls.restart, 0);
});

test('semantic recovery policy distinguishes deterministic protocol failures from transient failures', () => {
  assert.deepEqual(semanticFailurePolicy({ reason: 'workspace_mismatch' }), { deterministic: true, restartable: false });
  assert.deepEqual(semanticFailurePolicy({ reason: 'invalid_json' }), { deterministic: true, restartable: false });
  assert.deepEqual(semanticFailurePolicy({ reason: 'http_status', statusCode: 401 }), { deterministic: true, restartable: false });
  assert.deepEqual(semanticFailurePolicy({ reason: 'jsonrpc_error', errorCode: -32601 }), { deterministic: true, restartable: false });
  assert.deepEqual(semanticFailurePolicy({ reason: 'jsonrpc_error', errorCode: -32603 }), { deterministic: false, restartable: true });
  assert.deepEqual(semanticFailurePolicy({ reason: 'timeout' }), { deterministic: false, restartable: true });
  assert.deepEqual(semanticFailurePolicy({ reason: 'transport_error' }), { deterministic: false, restartable: true });
});

test('watchdog skips semantic probing until a workspace is configured', async () => {
  let probes = 0;
  const watchdog = new SemanticMcpHealthWatchdog({
    settings: { load: () => ({ mcpPort: 18766, workspace: '' }) },
    secrets: { get: () => 'token' },
    orchestrator: {
      busy: false,
      recovering: false,
      isManuallyStopped: () => false,
      restart: async () => {}
    },
    log: { info() {}, warn() {}, error() {} },
    probe: async () => { probes += 1; return { ok: true, workspace: 'C:\\unexpected' }; }
  });
  const result = await watchdog.checkOnce();
  assert.equal(result.skipped, true);
  assert.equal(result.reason, 'not_configured');
  assert.equal(probes, 0);
});

test('watchdog never restarts while the existing lifecycle controller is busy', async () => {
  const calls = { probe: 0, restart: 0 };
  const orchestrator = {
    busy: true,
    recovering: false,
    isManuallyStopped: () => false,
    restart: async () => { calls.restart += 1; }
  };
  const watchdog = new SemanticMcpHealthWatchdog({
    settings: { load: () => ({ mcpPort: 18766 }) },
    secrets: { get: () => 'token' },
    orchestrator,
    log: { info() {}, warn() {}, error() {} },
    probe: async () => { calls.probe += 1; return { ok: false }; },
    failureThreshold: 1
  });
  const result = await watchdog.checkOnce();
  assert.equal(result.skipped, true);
  assert.equal(result.reason, 'suppressed');
  assert.equal(calls.probe, 0);
  assert.equal(calls.restart, 0);
});
