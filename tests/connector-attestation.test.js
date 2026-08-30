const test = require('node:test');
const assert = require('node:assert/strict');
const childProcess = require('node:child_process');
const { EventEmitter } = require('node:events');
const fs = require('node:fs');
const net = require('node:net');
const os = require('node:os');
const path = require('node:path');
const {
  CONNECTOR_ATTESTATION_HEADER,
  connectorAttestationHeader
} = require('../electron/services/connectorAttestation');

test('connector attestation binds the managed tunnel tuple and never emits the secret', () => {
  const secret = 'connector-attestation-test-secret';
  const value = connectorAttestationHeader({
    secret,
    clientId: 'chatweb',
    clientType: 'chatweb',
    activationEpochId: 'activation-test-001',
    processInstanceId: 'mcp-process-test',
    serverInstanceId: 'mcp-server-test',
    contractSha256: 'a'.repeat(64),
    issuedAtUnixMs: 1700000000000,
    nonce: '0123456789abcdef0123456789abcdef'
  });
  assert.equal(value.split('|').length, 10);
  assert.equal(value.includes(secret), false);
  assert.match(value, /^v1\|chatweb\|chatweb\|activation-test-001\|mcp-process-test\|mcp-server-test\|a{64}\|1700000000000\|[0-9a-f]{32}\|[0-9a-f]{64}$/);
  // This fixed vector is also verified by the Python implementation.
  assert.equal(value, 'v1|chatweb|chatweb|activation-test-001|mcp-process-test|mcp-server-test|aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa|1700000000000|0123456789abcdef0123456789abcdef|42b5c6d9bded1b39327a98c500d87cf9ff9c97a338a539c4c3ff67bceb36fff6');
});

test('managed Tunnel attestation is forwarded externally but excluded from local discovery probes', async (t) => {
  let launch = null;
  t.mock.method(childProcess, 'spawn', (command, args, options) => {
    launch = { command, args: [...args], options };
    const child = new EventEmitter();
    child.pid = process.pid;
    child.unref = () => {};
    queueMicrotask(() => child.emit('spawn'));
    return child;
  });

  const modulePath = require.resolve('../electron/services/tunnelService');
  delete require.cache[modulePath];
  t.after(() => { delete require.cache[modulePath]; });
  const { TunnelService } = require(modulePath);

  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'coding-tools-tunnel-attestation-'));
  t.after(() => fs.rmSync(temp, { recursive: true, force: true }));
  const server = net.createServer((socket) => socket.end());
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  t.after(() => new Promise((resolve) => {
    if (!server.listening) return resolve();
    server.close(resolve);
  }));

  const processStartToken = '10000000000000099';
  const service = new TunnelService(
    { info() {} },
    {
      stateFile: () => path.join(temp, 'runtime-state.json'),
      tunnelExecutable: () => process.execPath,
      tunnelLogFile: () => path.join(temp, 'tunnel.log')
    },
    null,
    {
      processIdentityObserver: (pid) => ({ state: 'live', pid, process_start_token: processStartToken }),
      identitySleep: async () => {}
    }
  );
  service.listenerPidProbe = async () => process.pid;

  const secret = 'managed-tunnel-static-attestation-secret';
  const activationEpochId = 'activation-tunnel-attestation-0001';
  await service.start({
    tunnelId: 'tunnel-attestation-test',
    healthPort: server.address().port,
    mcpPort: 18765
  }, 'runtime-api-key', 'mcp-auth-token', () => {}, {
    activationEpochId,
    connectorAttestation: {
      secret,
      clientId: 'chatweb',
      clientType: 'chatweb',
      activationEpochId,
      processInstanceId: 'mcp-process-attestation-test',
      serverInstanceId: 'mcp-server-attestation-test',
      contractSha256: 'b'.repeat(64)
    }
  });

  assert.ok(launch);
  assert.equal(launch.command, process.execPath);
  const valuesFor = (flag) => launch.args.flatMap((value, index) => (
    value === flag && index + 1 < launch.args.length ? [launch.args[index + 1]] : []
  ));
  const forwardedHeaders = valuesFor('--mcp.extra-headers');
  const discoveryHeaders = valuesFor('--mcp.discovery-extra-headers');
  const attestationReference = `${CONNECTOR_ATTESTATION_HEADER}: env:MCP_DISCOVERY_ATTESTATION_VALUE`;
  assert.equal(forwardedHeaders.filter((value) => value === attestationReference).length, 1);
  assert.equal(discoveryHeaders.some((value) => (
    value.includes(CONNECTOR_ATTESTATION_HEADER)
    || value.includes('MCP_DISCOVERY_ATTESTATION_VALUE')
  )), false);

  const attestationValue = launch.options.env.MCP_DISCOVERY_ATTESTATION_VALUE;
  assert.equal(typeof attestationValue, 'string');
  assert.ok(attestationValue.length > 0);
  assert.equal(attestationValue.includes(secret), false);
  assert.equal(launch.args.join(' ').includes(attestationValue), false);
  assert.equal(launch.args.join(' ').includes(secret), false);
});
