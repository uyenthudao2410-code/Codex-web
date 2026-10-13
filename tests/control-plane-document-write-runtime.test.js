const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');

const { RuntimeOrchestrator } = require('../electron/services/runtimeOrchestrator');

async function fixture(t, failure) {
  const workspace = path.join(os.tmpdir(), 'webcodex-document-write-runtime-boundary');
  const calls = [];
  const server = http.createServer((request, response) => {
    const chunks = [];
    request.on('data', (chunk) => chunks.push(chunk));
    request.on('end', () => {
      const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      const tool = body.params.name;
      calls.push(tool);
      if (tool === 'workspace_context' && failure !== 'workflow') {
        if (failure === 'transport') {
          request.socket.destroy();
          return;
        }
        response.writeHead(failure === 'json' ? 200 : 403, { 'Content-Type': 'application/json' });
        response.end(failure === 'json' ? '{invalid-json' : JSON.stringify({
          jsonrpc: '2.0', id: body.id, error: { code: -32602, message: 'Fixture workspace is not authorized.' }
        }));
        return;
      }
      if (tool === 'workspace_context') {
        assert.equal(body.params.arguments.path, workspace);
        response.writeHead(200, { 'Content-Type': 'application/json' });
        response.end(JSON.stringify({ jsonrpc: '2.0', id: body.id,
          result: { structuredContent: { workspace } } }));
        return;
      }
      assert.equal(tool, 'document_workflow');
      response.writeHead(200, { 'Content-Type': 'application/json' });
      response.end(JSON.stringify({ jsonrpc: '2.0', id: body.id,
        result: { isError: true, structuredContent: { error: { message: 'Fixture workflow effect is unverified.' } } } }));
    });
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise((resolve) => server.close(resolve)));
  const activationEpochId = 'activation-document-write-boundary-0001';
  const processInstanceId = 'process-document-write-boundary-0001';
  const serverInstanceId = 'server-document-write-boundary-0001';
  const contractSha256 = 'e'.repeat(64);
  const orchestrator = Object.create(RuntimeOrchestrator.prototype);
  orchestrator.settingsStore = { load: () => ({ mcpPort: server.address().port, workspace }) };
  orchestrator.secrets = { get: () => 'mcp-fixture-token' };
  orchestrator.activationEpochId = activationEpochId;
  orchestrator.connectorAttestationSecret = 'document-write-boundary-fixture-secret';
  orchestrator.connectorAttestationBinding = { activationEpochId, processInstanceId, serverInstanceId, contractSha256 };
  orchestrator.currentMcpHealth = async () => ({ ready: true, activation_epoch_id: activationEpochId,
    process_instance_id: processInstanceId, instance_id: serverInstanceId,
    tool_contract: { sha256: contractSha256 } });
  const content = 'fixture document create';
  const admission = {
    action_id: 'action-document-write-boundary-0001', attempt_id: 'attempt-document-write-boundary-0001',
    operation: 'document_create', policy_sha256: 'a'.repeat(64), authority_mode: 'standing',
    tool_name: 'document_workflow', workspace_root: workspace,
    workspace_id: 'workspace-document-write-boundary-0001', workspace_generation: 'generation-document-write-boundary-0001',
    task_id: `task_${'a'.repeat(32)}`, writer_lease_generation: 1,
    target: 'fixture.txt', source: null, title: '', content,
    content_sha256: crypto.createHash('sha256').update(content, 'utf8').digest('hex'),
    overwrite: false, intent_digest: 'b'.repeat(64), expires_at_ms: Date.now() + 60_000,
    facade_contract: { schema_version: 32, profile: 'control-plane-private-tunnel-service-v1', sha256: 'f'.repeat(64) }
  };
  return { orchestrator, admission, calls };
}

for (const failure of ['rejection', 'json', 'transport']) {
  test(`document workspace bootstrap ${failure} proves no write was dispatched`, async (t) => {
    const { orchestrator, admission, calls } = await fixture(t, failure);
    await assert.rejects(orchestrator.controlPlaneDocumentWrite(admission), {
      code: 'CONTROL_PLANE_DOCUMENT_WRITE_BIND_REJECTED'
    });
    assert.deepEqual(calls, ['workspace_context']);
  });
}

test('document workflow rejection after successful binding retains the unknown-effect diagnostic', async (t) => {
  const { orchestrator, admission, calls } = await fixture(t, 'workflow');
  await assert.rejects(orchestrator.controlPlaneDocumentWrite(admission), {
    code: 'CONTROL_PLANE_DOCUMENT_WRITE_MCP_REJECTED'
  });
  assert.deepEqual(calls, ['workspace_context', 'document_workflow']);
});
