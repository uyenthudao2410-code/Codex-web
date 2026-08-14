const assert = require('node:assert/strict');
const http = require('node:http');
const test = require('node:test');

const {
  FLASH_MODEL,
  CanaryError,
  configureElectronAppContext,
  deriveRequestId,
  isElectronEntrypoint,
  preflightFlashCanary,
  runFlashCanary,
  sanitizedSummary,
  validateContext,
  validateHealth
} = require('../scripts/execution-hub-provider-canary');

function startServer(handler) {
  return new Promise((resolve) => {
    const server = http.createServer(handler);
    server.listen(0, '127.0.0.1', () => resolve(server));
  });
}

function json(response, status, body) {
  const encoded = Buffer.from(JSON.stringify(body));
  response.writeHead(status, { 'Content-Type': 'application/json', 'Content-Length': encoded.length });
  response.end(encoded);
}

test('request id is deterministic per run and wave', () => {
  const first = deriveRequestId('run-a', 'wave-a');
  assert.equal(first, deriveRequestId('run-a', 'wave-a'));
  assert.notEqual(first, deriveRequestId('run-a', 'wave-b'));
});

test('Electron entry detection is explicit and independent of require.main', () => {
  const filename = require.resolve('../scripts/execution-hub-provider-canary');
  assert.equal(isElectronEntrypoint({ versions: { electron: '43.2.0' }, argv: ['electron.exe', filename], filename }), true);
  assert.equal(isElectronEntrypoint({ versions: { electron: '43.2.0' }, argv: ['electron.exe', `${filename}.other`], filename }), false);
  assert.equal(isElectronEntrypoint({ versions: { node: process.versions.node }, argv: ['node.exe', filename], filename }), false);
});

test('standalone Electron context is aligned to the managed app userData before readiness', () => {
  const calls = [];
  const fakeApp = {
    setName(value) { calls.push(['name', value]); },
    setPath(key, value) { calls.push(['path', key, value]); }
  };
  const root = configureElectronAppContext(fakeApp, 'C:\\Users\\tester\\AppData\\Roaming');
  assert.equal(root, 'C:\\Users\\tester\\AppData\\Roaming\\web-mcp-assistant');
  assert.deepEqual(calls, [
    ['name', 'web-mcp-assistant'],
    ['path', 'userData', root]
  ]);
});

test('context validation fails closed on workspace mismatch', () => {
  const snapshot = {
    run: { status: 'active' },
    resume_packet: { run_id: 'run-a', wave_id: 'wave-a', orchestration_state: 'EXECUTING' },
    runtime: { workspace: 'C:\\other' }
  };
  assert.throws(() => validateContext(snapshot, 'C:\\workspace'), (error) => error instanceof CanaryError && error.code === 'PROVIDER_CANARY_WORKSPACE_MISMATCH');
});

test('live health validation fails closed on workspace and tool-contract mismatch', () => {
  const workspace = process.cwd();
  const valid = { ready: true, workspace, tool_profile: 'smart-v3', tool_count: 8, instance_id: 'runtime-a' };
  assert.equal(validateHealth(valid, workspace).toolCount, 8);
  assert.throws(
    () => validateHealth({ ...valid, workspace: `${workspace}-other` }, workspace),
    (error) => error instanceof CanaryError && error.code === 'PROVIDER_CANARY_WORKSPACE_MISMATCH'
  );
  assert.throws(
    () => validateHealth({ ...valid, tool_profile: 'smart-v2' }, workspace),
    (error) => error instanceof CanaryError && error.code === 'PROVIDER_CANARY_CONTRACT_MISMATCH'
  );
  assert.throws(
    () => validateHealth({ ...valid, tool_count: 9 }, workspace),
    (error) => error instanceof CanaryError && error.code === 'PROVIDER_CANARY_CONTRACT_MISMATCH'
  );
});

test('sanitized summary excludes prompt, bearer and raw provider output', () => {
  const summary = sanitizedSummary({
    context: { runId: 'run-a', waveId: 'wave-a' },
    dispatch: { dispatch_id: 'dispatch-a', delegation_id: 'delegation-a', model: FLASH_MODEL, status: 'completed', result: 'SECRET_PROVIDER_TEXT', prompt: 'SECRET_PROMPT' },
    usage: {
      model: FLASH_MODEL,
      status: 'completed',
      usage: { input_tokens: 10, cached_input_tokens: 2, uncached_input_tokens: 8, output_tokens: 3, reasoning_output_tokens: 1, cache_read_tokens: 2, cache_write_tokens: 0 },
      cost: { provider_cost: 0.001, kind: 'provider_reported' },
      timing: { provider_ms: 100 },
      measurement: { usage: 'measured', cost: 'measured', provider_timing: 'measured' }
    }
  });
  const text = JSON.stringify(summary);
  assert.equal(summary.model, FLASH_MODEL);
  assert.equal(summary.read_only_enforced, true);
  assert.equal(text.includes('SECRET_PROVIDER_TEXT'), false);
  assert.equal(text.includes('SECRET_PROMPT'), false);
  assert.equal(text.toLowerCase().includes('authorization'), false);
});

test('flash canary dispatches once, polls terminal state and correlates measured usage', async (t) => {
  const token = 'test-bearer-not-for-output';
  const workspace = process.cwd();
  let observeCount = 0;
  let dispatchCount = 0;
  let sawAuthorization = false;
  let dispatchedBody = null;
  const server = await startServer((request, response) => {
    sawAuthorization ||= request.headers.authorization === `Bearer ${token}`;
    if (request.method === 'GET' && request.url === '/__control/health') {
      json(response, 200, { ready: true, workspace, tool_profile: 'smart-v3', tool_count: 8, instance_id: 'runtime-a' });
      return;
    }
    if (request.method === 'GET' && request.url === '/__control/orchestration') {
      const usage = observeCount >= 2 ? [{
        delegation_id: 'delegation-a', model: FLASH_MODEL, status: 'completed',
        usage: { input_tokens: 12, cached_input_tokens: 4, uncached_input_tokens: 8, output_tokens: 2, reasoning_output_tokens: 0, cache_read_tokens: 4, cache_write_tokens: 0 },
        cost: { provider_cost: 0.0025, kind: 'provider_reported' },
        timing: { provider_ms: 250 },
        measurement: { usage: 'measured', cost: 'measured', provider_timing: 'measured' }
      }] : [];
      json(response, 200, {
        run: { status: 'active' },
        resume_packet: { run_id: 'run-a', wave_id: 'wave-a', orchestration_state: 'EXECUTING' },
        runtime: { workspace },
        usage_events: usage
      });
      return;
    }
    if (request.method === 'POST' && request.url === '/__control/hub') {
      const chunks = [];
      request.on('data', (chunk) => chunks.push(chunk));
      request.on('end', () => {
        const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
        if (body.action === 'provider_dispatch') {
          dispatchCount += 1;
          dispatchedBody = body;
          json(response, 200, { dispatch: { dispatch_id: 'dispatch-a', delegation_id: 'delegation-a', model: FLASH_MODEL, status: 'running' } });
          return;
        }
        if (body.action === 'provider_observe') {
          observeCount += 1;
          json(response, 200, { dispatch: { dispatch_id: 'dispatch-a', delegation_id: 'delegation-a', model: FLASH_MODEL, status: observeCount >= 2 ? 'completed' : 'running' } });
          return;
        }
        json(response, 400, { code: 'UNEXPECTED_ACTION', message: 'unexpected' });
      });
      return;
    }
    json(response, 404, { error: 'not found' });
  });
  t.after(() => server.close());
  const port = server.address().port;
  const summary = await runFlashCanary({ port, token, workspace, sleepFn: async () => {}, pollMs: 1, telemetryWaitMs: 100 });
  assert.equal(sawAuthorization, true);
  assert.equal(dispatchCount, 1);
  assert.equal(dispatchedBody.client_id, 'electron-panel');
  assert.equal(dispatchedBody.client_type, 'electron');
  assert.equal(dispatchedBody.model, FLASH_MODEL);
  assert.equal(dispatchedBody.request_id, deriveRequestId('run-a', 'wave-a'));
  assert.equal(summary.status, 'completed');
  assert.equal(summary.cost.provider_cost, 0.0025);
  assert.equal(summary.measurement.usage, 'measured');
  assert.equal(summary.measurement.cost, 'measured');
  assert.equal(JSON.stringify(summary).includes(token), false);
});

test('preflight validates live target and performs zero hub posts', async (t) => {
  const token = 'test-bearer-not-for-output';
  const workspace = process.cwd();
  let hubPostCount = 0;
  let sawAuthorization = false;
  const server = await startServer((request, response) => {
    sawAuthorization ||= request.headers.authorization === `Bearer ${token}`;
    if (request.method === 'GET' && request.url === '/__control/health') {
      json(response, 200, { ready: true, workspace, tool_profile: 'smart-v3', tool_count: 8, instance_id: 'runtime-preflight' });
      return;
    }
    if (request.method === 'GET' && request.url === '/__control/orchestration') {
      json(response, 200, {
        run: { status: 'active' },
        resume_packet: { run_id: 'run-preflight', wave_id: 'wave-preflight', orchestration_state: 'PROVING' },
        runtime: { workspace }
      });
      return;
    }
    if (request.method === 'POST' && request.url === '/__control/hub') {
      hubPostCount += 1;
      json(response, 500, { code: 'UNEXPECTED_DISPATCH', message: 'preflight must not dispatch' });
      return;
    }
    json(response, 404, { error: 'not found' });
  });
  t.after(() => server.close());
  const port = server.address().port;
  const result = await preflightFlashCanary({ port, token, workspace });
  assert.equal(sawAuthorization, true);
  assert.equal(hubPostCount, 0);
  assert.equal(result.summary.preflight, true);
  assert.equal(result.summary.provider_dispatches, 0);
  assert.equal(result.summary.runtime_instance_id, 'runtime-preflight');
  assert.equal(result.summary.tool_profile, 'smart-v3');
  assert.equal(result.summary.tool_count, 8);
  assert.equal(JSON.stringify(result.summary).includes(token), false);
});
