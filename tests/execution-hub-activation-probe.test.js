const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { HubProxyGateway } = require('../electron/services/hubProxyGateway');
const { probeActivation } = require('../scripts/execution-hub-activation-probe');

function listen(server) {
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => resolve(server.address().port));
  });
}

test('activation probe proves the telemetry route without forwarding or exposing tokens', async (t) => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'hub-activation-probe-'));
  const descriptorPath = path.join(directory, 'execution-hub-proxy.json');
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  const gateway = new HubProxyGateway({
    settings: { load: () => { throw new Error('probe must not forward to MCP'); } },
    secrets: { get: () => { throw new Error('probe must not read MCP bearer'); } },
    log: { info() {} },
    descriptorPath,
  });
  t.after(() => gateway.stop());
  const descriptor = await gateway.start();

  const result = await probeActivation({ descriptorFile: descriptorPath, timeoutMs: 500 });
  assert.equal(result.ok, true);
  assert.equal(result.route_loaded, true);
  assert.equal(result.status, 403);
  assert.equal(result.owner, 'recovery-host');
  assert.equal(result.owner_pid, process.pid);
  const serialized = JSON.stringify(result);
  assert.equal(serialized.includes(descriptor.token), false);
  assert.equal(serialized.toLowerCase().includes('token'), false);
});

test('activation probe distinguishes a legacy Electron gateway that does not expose telemetry route', async (t) => {
  const token = 'x'.repeat(43);
  const legacy = http.createServer((_request, response) => {
    response.writeHead(404, { 'Content-Length': 0 });
    response.end();
  });
  const port = await listen(legacy);
  t.after(() => new Promise((resolve) => legacy.close(resolve)));
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'hub-activation-legacy-'));
  const descriptorPath = path.join(directory, 'execution-hub-proxy.json');
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  fs.writeFileSync(descriptorPath, JSON.stringify({ version: 1, host: '127.0.0.1', port, token, electron_pid: 1234 }));

  const result = await probeActivation({ descriptorFile: descriptorPath, timeoutMs: 500 });
  assert.equal(result.ok, false);
  assert.equal(result.route_loaded, false);
  assert.equal(result.code, 'ELECTRON_RESTART_REQUIRED');
  assert.equal(result.owner, 'electron');
  assert.equal(result.owner_pid, 1234);
  assert.equal(JSON.stringify(result).includes(token), false);
});
