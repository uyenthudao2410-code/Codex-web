const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');

const { RuntimeOrchestrator } = require('../electron/services/runtimeOrchestrator');
const { BRIDGE_CLIENT_ID, BRIDGE_CLIENT_TYPE, READ_ONLY_ARGUMENTS } = require('../electron/services/controlPlaneReadOnlyBridge');

function listen(server) { return new Promise((resolve) => server.listen(0, '127.0.0.1', resolve)); }

test('control-plane read-only bridge owns an attested actor and never accepts central tool arguments', async (t) => {
  const secret = 'control-plane-bridge-test-secret';
  const activationEpochId = 'activation-control-plane-bridge-0001';
  const processInstanceId = 'process-control-plane-bridge-0001';
  const serverInstanceId = 'server-control-plane-bridge-0001';
  const contractSha256 = 'd'.repeat(64);
  const facadeContract = { schema_version: 3, profile: 'control-plane-read-only-queue-v2', sha256: 'f'.repeat(64) };
  const workspace = path.join(os.tmpdir(), 'webcodex-control-plane-bridge-workspace');
  let requests = 0;
  const server = http.createServer((request, response) => {
    const chunks = [];
    request.on('data', (chunk) => chunks.push(chunk));
    request.on('end', () => {
      requests += 1;
      assert.equal(request.headers.authorization, 'Bearer mcp-test-token');
      assert.equal(request.headers['x-coding-tools-client-id'], BRIDGE_CLIENT_ID);
      assert.equal(request.headers['x-coding-tools-client-type'], BRIDGE_CLIENT_TYPE);
      const attestation = String(request.headers['x-coding-tools-connector-attestation'] || '');
      const parts = attestation.split('|');
      const signature = parts.pop();
      assert.equal(parts[0], 'v1');
      assert.equal(parts[1], BRIDGE_CLIENT_ID);
      assert.equal(parts[2], BRIDGE_CLIENT_TYPE);
      assert.equal(parts[3], activationEpochId);
      assert.equal(parts[4], processInstanceId);
      assert.equal(parts[5], serverInstanceId);
      assert.equal(parts[6], contractSha256);
      assert.equal(signature, crypto.createHmac('sha256', secret).update(parts.join('|'), 'utf8').digest('hex'));
      const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      assert.equal(body.method, 'tools/call');
      assert.equal(body.params.name, 'workspace_context');
      assert.deepEqual(body.params.arguments, READ_ONLY_ARGUMENTS);
      assert.equal(body.params.arguments.path, undefined);
      const payload = JSON.stringify({
        jsonrpc: '2.0', id: body.id,
        result: { structuredContent: { workspace } }
      });
      response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) });
      response.end(payload);
    });
  });
  await listen(server);
  t.after(() => server.close());

  const orchestrator = Object.create(RuntimeOrchestrator.prototype);
  orchestrator.settingsStore = { load: () => ({ mcpPort: server.address().port, workspace }) };
  orchestrator.secrets = { get: (name) => name === 'mcpAuthToken' ? 'mcp-test-token' : null };
  orchestrator.activationEpochId = activationEpochId;
  orchestrator.connectorAttestationSecret = secret;
  orchestrator.connectorAttestationBinding = { activationEpochId, processInstanceId, serverInstanceId, contractSha256 };
  orchestrator.currentMcpHealth = async () => ({
    ready: true,
    activation_epoch_id: activationEpochId,
    process_instance_id: processInstanceId,
    instance_id: serverInstanceId,
    tool_contract: { sha256: contractSha256 }
  });

  const result = await orchestrator.controlPlaneReadOnlyWorkspaceContext({
    action_id: 'action-control-plane-bridge-0001',
    attempt_id: 'attempt-control-plane-bridge-0001',
    policy_sha256: 'a'.repeat(64),
    tool_name: 'workspace_context',
    facade_contract: { ...facadeContract }
  });
  assert.equal(result.workspace_accessed, true);
  assert.equal(result.actor.client_id, BRIDGE_CLIENT_ID);
  assert.equal(result.runtime_identity.activation_epoch_id, activationEpochId);
  assert.match(result.local_handle, /^cp_ro_[a-f0-9]{48}$/);
  assert.match(result.response_sha256, /^[a-f0-9]{64}$/);
  assert.deepEqual(result.facade_contract, facadeContract);
  assert.equal(requests, 1);

  orchestrator.connectorAttestationBinding = { ...orchestrator.connectorAttestationBinding, processInstanceId: 'other-process' };
  await assert.rejects(
    orchestrator.controlPlaneReadOnlyWorkspaceContext({
      action_id: 'action-control-plane-bridge-0001',
      attempt_id: 'attempt-control-plane-bridge-0002',
      policy_sha256: 'a'.repeat(64),
      tool_name: 'workspace_context',
      facade_contract: { ...facadeContract }
    }),
    { code: 'CONNECTOR_ATTESTATION_BINDING_UNAVAILABLE' }
  );
  assert.equal(requests, 1, 'identity drift must block before an MCP request');
});

test('control-plane read-only bridge refuses a workspace response outside the current local workspace', async (t) => {
  const workspace = path.join(os.tmpdir(), 'webcodex-control-plane-bridge-expected');
  const facadeContract = { schema_version: 3, profile: 'control-plane-read-only-queue-v2', sha256: 'f'.repeat(64) };
  const server = http.createServer((_request, response) => {
    const payload = JSON.stringify({ jsonrpc: '2.0', id: 'ignored', result: { structuredContent: { workspace: path.join(os.tmpdir(), 'outside') } } });
    response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) });
    response.end(payload);
  });
  await listen(server);
  t.after(() => server.close());
  const orchestrator = Object.create(RuntimeOrchestrator.prototype);
  orchestrator.settingsStore = { load: () => ({ mcpPort: server.address().port, workspace }) };
  orchestrator.secrets = { get: () => 'mcp-test-token' };
  orchestrator.activationEpochId = 'activation-control-plane-bridge-0002';
  orchestrator.connectorAttestationSecret = 'control-plane-bridge-mismatch-secret';
  orchestrator.connectorAttestationBinding = {
    activationEpochId: 'activation-control-plane-bridge-0002',
    processInstanceId: 'process-control-plane-bridge-0002',
    serverInstanceId: 'server-control-plane-bridge-0002',
    contractSha256: 'e'.repeat(64)
  };
  orchestrator.currentMcpHealth = async () => ({
    ready: true,
    activation_epoch_id: 'activation-control-plane-bridge-0002',
    process_instance_id: 'process-control-plane-bridge-0002',
    instance_id: 'server-control-plane-bridge-0002',
    tool_contract: { sha256: 'e'.repeat(64) }
  });
  await assert.rejects(
    orchestrator.controlPlaneReadOnlyWorkspaceContext({
      action_id: 'action-control-plane-bridge-0002',
      attempt_id: 'attempt-control-plane-bridge-0002',
      policy_sha256: 'b'.repeat(64),
      tool_name: 'workspace_context',
      facade_contract: { ...facadeContract }
    }),
    { code: 'CONTROL_PLANE_BRIDGE_WORKSPACE_MISMATCH' }
  );
});
