const test = require('node:test');
const assert = require('node:assert/strict');
const { connectorAttestationHeader } = require('../electron/services/connectorAttestation');

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
