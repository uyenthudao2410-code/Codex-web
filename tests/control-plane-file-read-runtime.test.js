'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');

const { RuntimeOrchestrator } = require('../electron/services/runtimeOrchestrator');
const {
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE,
  digest,
  fileContentDigest
} = require('../electron/services/controlPlaneFileReadBridge');

function listen(server) {
  return new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
}

function fixture(t) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-file-read-runtime-'));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  const registeredRoot = path.join(directory, 'registered-root');
  const unrelatedUiRoot = path.join(directory, 'unrelated-ui-root');
  fs.mkdirSync(registeredRoot);
  fs.mkdirSync(unrelatedUiRoot);
  return { registeredRoot, unrelatedUiRoot };
}

function admission(workspaceRoot) {
  return {
    action_id: 'action-control-plane-0001',
    attempt_id: 'attempt-control-plane-0001',
    policy_sha256: 'a'.repeat(64),
    tool_name: 'workspace_context',
    operation: 'read_file',
    workspace_root: workspaceRoot,
    workspace_id: 'workspace-control-plane-0001',
    workspace_generation: 'generation-control-plane-0001',
    path: 'fixture.txt',
    start_line: 1,
    max_lines: 20,
    max_bytes: 1024,
    facade_contract: {
      schema_version: 8,
      profile: 'control-plane-oauth-bounded-file-read-v1',
      sha256: 'f'.repeat(64)
    }
  };
}

function createOrchestrator({ port, globalWorkspace }) {
  const secret = 'control-plane-file-read-runtime-secret';
  const activationEpochId = 'activation-control-plane-file-read-0001';
  const processInstanceId = 'process-control-plane-file-read-0001';
  const serverInstanceId = 'server-control-plane-file-read-0001';
  const contractSha256 = 'd'.repeat(64);
  const orchestrator = Object.create(RuntimeOrchestrator.prototype);
  orchestrator.settingsStore = { load: () => ({ mcpPort: port, workspace: globalWorkspace }) };
  orchestrator.secrets = { get: (name) => name === 'mcpAuthToken' ? 'mcp-test-token' : null };
  orchestrator.activationEpochId = activationEpochId;
  orchestrator.connectorAttestationSecret = secret;
  orchestrator.connectorAttestationBinding = {
    activationEpochId,
    processInstanceId,
    serverInstanceId,
    contractSha256
  };
  orchestrator.currentMcpHealth = async () => ({
    ready: true,
    activation_epoch_id: activationEpochId,
    process_instance_id: processInstanceId,
    instance_id: serverInstanceId,
    tool_contract: { sha256: contractSha256 }
  });
  return { orchestrator, secret, activationEpochId, processInstanceId, serverInstanceId, contractSha256 };
}

function send(response, id, structuredContent) {
  const payload = JSON.stringify({ jsonrpc: '2.0', id, result: { structuredContent } });
  response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) });
  response.end(payload);
}

test('bounded file-read creates a task-local binding and ignores the global UI workspace', async (t) => {
  const item = fixture(t);
  const calls = [];
  const server = http.createServer((request, response) => {
    const chunks = [];
    request.on('data', (chunk) => chunks.push(chunk));
    request.on('end', () => {
      assert.equal(request.headers.authorization, 'Bearer mcp-test-token');
      assert.equal(request.headers['x-coding-tools-client-id'], BRIDGE_CLIENT_ID);
      assert.equal(request.headers['x-coding-tools-client-type'], BRIDGE_CLIENT_TYPE);
      const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      calls.push(body);
      if (calls.length === 1) {
        assert.equal(body.params.name, 'workspace_context');
        assert.equal(body.params.arguments.path, item.registeredRoot);
        assert.equal(body.params.arguments.detail, 'compact');
        assert.equal(body.params.arguments.max_entries, 1);
        assert.match(body.params.arguments.task_context_id, /^cpfr_[a-f0-9]{56}$/);
        assert.notEqual(body.params.arguments.path, item.unrelatedUiRoot);
        send(response, body.id, { workspace: item.registeredRoot });
        return;
      }
      assert.equal(calls.length, 2, 'the local bridge must use exactly bind then read');
      assert.equal(body.params.name, 'read_file');
      assert.equal(body.params.arguments.task_context_id, calls[0].params.arguments.task_context_id);
      assert.deepEqual(body.params.arguments, {
        task_context_id: calls[0].params.arguments.task_context_id,
        path: 'fixture.txt',
        start_line: 1,
        max_lines: 20,
        max_bytes: 1024,
        encoding: 'utf-8'
      });
      const content = 'line one\nline two\n';
      send(response, body.id, {
        path: 'fixture.txt',
        content,
        encoding: 'utf-8',
        start_line: 1,
        end_line: 2,
        total_lines: 2,
        total_bytes: Buffer.byteLength(content),
        bytes_read: Buffer.byteLength(content),
        truncated: false,
        next_start_line: null
      });
    });
  });
  await listen(server);
  t.after(() => server.close());

  const context = createOrchestrator({ port: server.address().port, globalWorkspace: item.unrelatedUiRoot });
  const result = await context.orchestrator.controlPlaneBoundedFileRead(admission(item.registeredRoot));
  assert.equal(calls.length, 2);
  assert.equal(result.file.content, 'line one\nline two\n');
  assert.equal(result.file.content_sha256, fileContentDigest(result.file.content));
  assert.equal(result.response_sha256, digest(result.file));
  assert.equal(result.runtime_identity.activation_epoch_id, context.activationEpochId);
  assert.equal(result.runtime_identity.process_instance_id, context.processInstanceId);
  assert.equal(result.runtime_identity.server_instance_id, context.serverInstanceId);
  assert.match(result.local_handle, /^cp_fr_[a-f0-9]{48}$/);
});

test('bounded file-read refuses a local context bound to a different workspace before it reads', async (t) => {
  const item = fixture(t);
  let calls = 0;
  const server = http.createServer((request, response) => {
    const chunks = [];
    request.on('data', (chunk) => chunks.push(chunk));
    request.on('end', () => {
      calls += 1;
      const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      assert.equal(body.params.name, 'workspace_context');
      send(response, body.id, { workspace: item.unrelatedUiRoot });
    });
  });
  await listen(server);
  t.after(() => server.close());

  const context = createOrchestrator({ port: server.address().port, globalWorkspace: item.unrelatedUiRoot });
  await assert.rejects(
    context.orchestrator.controlPlaneBoundedFileRead(admission(item.registeredRoot)),
    { code: 'CONTROL_PLANE_FILE_READ_WORKSPACE_MISMATCH' }
  );
  assert.equal(calls, 1);
});
