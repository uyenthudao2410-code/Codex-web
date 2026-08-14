const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { HubProxyGateway } = require('../electron/services/hubProxyGateway');

function listen(server) {
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => resolve(server.address().port));
  });
}

function post(port, token, body, headers = {}, requestPath = '/mcp') {
  return new Promise((resolve, reject) => {
    const data = Buffer.from(JSON.stringify(body));
    const request = http.request({ host: '127.0.0.1', port, path: requestPath, method: 'POST', headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Content-Length': data.length,
      ...headers
    } }, (response) => {
      const chunks = [];
      response.on('data', (chunk) => chunks.push(chunk));
      response.on('end', () => resolve({ status: response.statusCode, headers: response.headers, body: Buffer.concat(chunks).toString('utf8') }));
    });
    request.on('error', reject);
    request.end(data);
  });
}

test('gateway keeps real MCP bearer in Electron and tags Desktop requests', async (t) => {
  const observed = [];
  const actualBearer = 'actual-mcp-secret-never-in-descriptor';
  const upstream = http.createServer((request, response) => {
    const chunks = [];
    request.on('data', (chunk) => chunks.push(chunk));
    request.on('end', () => {
      observed.push({ path: request.url, headers: request.headers, body: Buffer.concat(chunks).toString('utf8') });
      const body = JSON.stringify({ jsonrpc: '2.0', id: 1, result: { ok: true } });
      response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body), 'Mcp-Session-Id': 'upstream-session' });
      response.end(body);
    });
  });
  const upstreamPort = await listen(upstream);
  t.after(() => new Promise((resolve) => upstream.close(resolve)));

  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'hub-proxy-gateway-'));
  const descriptorPath = path.join(directory, 'hub-proxy.json');
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  const gateway = new HubProxyGateway({
    settings: { load: () => ({ mcpPort: upstreamPort }) },
    secrets: { get: (key) => key === 'mcpAuthToken' ? actualBearer : '' },
    log: { info() {} },
    descriptorPath
  });
  t.after(() => gateway.stop());
  const descriptor = await gateway.start();
  const descriptorText = fs.readFileSync(descriptorPath, 'utf8');
  assert.equal(descriptorText.includes(actualBearer), false);
  assert.notEqual(descriptor.token, actualBearer);

  const payload = { jsonrpc: '2.0', id: 1, method: 'tools/list', params: {} };
  const result = await post(descriptor.port, descriptor.token, payload, {
    'MCP-Protocol-Version': '2026-07-28',
    'Mcp-Method': 'tools/list',
    'Mcp-Session-Id': 'desktop-session'
  });
  assert.equal(result.status, 200);
  assert.equal(result.headers['mcp-session-id'], 'upstream-session');
  assert.equal(observed.length, 1);
  assert.equal(observed[0].headers.authorization, `Bearer ${actualBearer}`);
  assert.equal(observed[0].headers['x-coding-tools-client-id'], 'codex-desktop');
  assert.equal(observed[0].headers['x-coding-tools-client-type'], 'codex_desktop');
  assert.equal(observed[0].headers['mcp-session-id'], 'desktop-session');
  assert.equal(observed[0].headers['mcp-protocol-version'], '2026-07-28');

  const heartbeat = await post(descriptor.port, descriptor.token, {}, {}, '/__hub_proxy/heartbeat');
  assert.equal(heartbeat.status, 200);
  assert.equal(observed.length, 2);
  assert.equal(observed[1].path, '/__control/hub');
  assert.equal(observed[1].headers.authorization, `Bearer ${actualBearer}`);
  const heartbeatBody = JSON.parse(observed[1].body);
  assert.equal(heartbeatBody.action, 'heartbeat');
  assert.equal(heartbeatBody.client_id, 'codex-desktop');
  assert.equal(heartbeatBody.client_type, 'codex_desktop');

  const openCode = await post(descriptor.port, descriptor.token, payload, {
    'X-Coding-Tools-Proxy-Client-Id': 'opencode',
    'X-Coding-Tools-Proxy-Client-Type': 'opencode'
  });
  assert.equal(openCode.status, 200);
  assert.equal(observed.length, 3);
  assert.equal(observed[2].headers['x-coding-tools-client-id'], 'opencode');
  assert.equal(observed[2].headers['x-coding-tools-client-type'], 'opencode');

  const openCodeHeartbeat = await post(descriptor.port, descriptor.token, {}, {
    'X-Coding-Tools-Proxy-Client-Id': 'opencode',
    'X-Coding-Tools-Proxy-Client-Type': 'opencode'
  }, '/__hub_proxy/heartbeat');
  assert.equal(openCodeHeartbeat.status, 200);
  assert.equal(observed.length, 4);
  const openCodeHeartbeatBody = JSON.parse(observed[3].body);
  assert.equal(openCodeHeartbeatBody.client_id, 'opencode');
  assert.equal(openCodeHeartbeatBody.client_type, 'opencode');

  const invalidIdentity = await post(descriptor.port, descriptor.token, payload, {
    'X-Coding-Tools-Proxy-Client-Id': 'chatweb',
    'X-Coding-Tools-Proxy-Client-Type': 'chatweb'
  });
  assert.equal(invalidIdentity.status, 403);
  assert.equal(observed.length, 4);

  const canonicalSpoof = await post(descriptor.port, descriptor.token, payload, {
    'X-Coding-Tools-Client-Id': 'chatweb',
    'X-Coding-Tools-Client-Type': 'chatweb'
  });
  assert.equal(canonicalSpoof.status, 200);
  assert.equal(observed.length, 5);
  assert.equal(observed[4].headers['x-coding-tools-client-id'], 'codex-desktop');
  assert.equal(observed[4].headers['x-coding-tools-client-type'], 'codex_desktop');

  const telemetryPayload = {
    schema_version: 1,
    event_type: 'message.updated',
    session_id: 'ses_test',
    message_id: 'msg_test',
    provider_dispatch_id: 'dispatch_test',
    provider_delegation_id: 'delegation_test',
    provider_id: 'opencode-go',
    model_id: 'deepseek-v4-flash',
    status: 'completed',
    started_at_ms: 1000,
    completed_at_ms: 1600,
    duration_ms: 600,
    finish: 'stop',
    provider_cost: 0.004,
    input_tokens: 100,
    output_tokens: 20,
    reasoning_output_tokens: 4,
    cache_read_tokens: 40,
    cache_write_tokens: 2
  };
  const telemetry = await post(descriptor.port, descriptor.token, telemetryPayload, {
    'X-Coding-Tools-Proxy-Client-Id': 'opencode',
    'X-Coding-Tools-Proxy-Client-Type': 'opencode'
  }, '/__hub_proxy/telemetry');
  assert.equal(telemetry.status, 200);
  assert.equal(observed.length, 6);
  assert.equal(observed[5].path, '/__control/hub');
  assert.equal(observed[5].headers.authorization, `Bearer ${actualBearer}`);
  const forwardedTelemetry = JSON.parse(observed[5].body);
  assert.equal(forwardedTelemetry.action, 'provider_telemetry');
  assert.equal(forwardedTelemetry.client_id, 'opencode');
  assert.deepEqual(forwardedTelemetry.telemetry, telemetryPayload);
  const desktopTelemetry = await post(descriptor.port, descriptor.token, telemetryPayload, {}, '/__hub_proxy/telemetry');
  assert.equal(desktopTelemetry.status, 403);
  assert.equal(observed.length, 6);
  const contentLeak = await post(descriptor.port, descriptor.token, { ...telemetryPayload, prompt: 'must not pass' }, {
    'X-Coding-Tools-Proxy-Client-Id': 'opencode',
    'X-Coding-Tools-Proxy-Client-Type': 'opencode'
  }, '/__hub_proxy/telemetry');
  assert.equal(contentLeak.status, 400);
  assert.equal(observed.length, 6);

  const denied = await post(descriptor.port, 'wrong-token', payload);
  assert.equal(denied.status, 401);
  await gateway.stop();
  assert.equal(fs.existsSync(descriptorPath), false);
});
