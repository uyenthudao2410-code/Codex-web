'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');

const { RuntimeOrchestrator } = require('../electron/services/runtimeOrchestrator');
const {
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE
} = require('../electron/services/controlPlaneExecBridge');

function listen(server) {
  return new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
}

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-exec-runtime-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const workspace = path.join(root, 'registered-root');
  fs.mkdirSync(workspace);
  return { workspace };
}

function admission(workspace, overrides = {}) {
  return {
    server_origin: 'https://control.example.test',
    owner_id: 'owner-control-plane-0001',
    device_id: 'device-control-plane-0001',
    endpoint_id: 'endpoint-control-plane-0001',
    workspace_id: 'workspace-control-plane-0001',
    workspace_generation: 'generation-control-plane-0001',
    context_id: 'context-control-plane-0001',
    binding_id: 'binding-control-plane-0001',
    action_id: 'action-control-plane-0001',
    attempt_id: 'attempt-control-plane-0001',
    task_id: `task_${'a'.repeat(32)}`,
    writer_lease_generation: 1,
    tool_name: 'exec_command',
    operation: 'exec_run',
    argv: ['python', '-m', 'pytest', '-q'],
    cwd: 'tests',
    timeout_ms: 30_000,
    max_output_bytes: 16_384,
    expires_at_ms: Date.now() + 30_000,
    facade_contract: {
      schema_version: 14,
      profile: 'control-plane-oauth-bounded-exec-v1',
      sha256: 'f'.repeat(64)
    },
    policy_sha256: 'a'.repeat(64),
    command_id: null,
    job_id: null,
    local_handle: null,
    consumer_id: null,
    yield_time_ms: null,
    signal: null,
    wait_ms: null,
    run_id: null,
    wave_id: null,
    workspace_root: workspace,
    ...overrides
  };
}

function createOrchestrator({ port, workspace }) {
  const orchestrator = Object.create(RuntimeOrchestrator.prototype);
  const activationEpochId = 'activation-control-plane-exec-0001';
  const processInstanceId = 'process-control-plane-exec-0001';
  const serverInstanceId = 'server-control-plane-exec-0001';
  const contractSha256 = 'd'.repeat(64);
  orchestrator.settingsStore = { load: () => ({ mcpPort: port, workspace }) };
  orchestrator.secrets = { get: (name) => name === 'mcpAuthToken' ? 'mcp-test-token' : null };
  orchestrator.activationEpochId = activationEpochId;
  orchestrator.connectorAttestationSecret = 'exec-runtime-attestation-secret';
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
  return { orchestrator, activationEpochId, processInstanceId, serverInstanceId, contractSha256 };
}

function send(response, id, structuredContent) {
  const payload = JSON.stringify({ jsonrpc: '2.0', id, result: { structuredContent } });
  response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) });
  response.end(payload);
}

test('control-plane exec binds the registered workspace and returns managed Job identity', async (t) => {
  const item = fixture(t);
  const action = admission(item.workspace);
  const calls = [];
  const server = http.createServer((request, response) => {
    const chunks = [];
    request.on('data', (chunk) => chunks.push(chunk));
    request.on('end', () => {
      assert.equal(request.headers.authorization, 'Bearer mcp-test-token');
      assert.equal(request.headers['x-coding-tools-client-id'], BRIDGE_CLIENT_ID);
      assert.equal(request.headers['x-coding-tools-client-type'], BRIDGE_CLIENT_TYPE);
      assert.ok(request.headers['x-coding-tools-connector-attestation']);
      const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      calls.push(body);
      if (calls.length === 1) {
        assert.equal(body.params.name, 'workspace_context');
        assert.equal(body.params.arguments.path, item.workspace);
        assert.match(body.params.arguments.task_context_id, /^cpex_[a-f0-9]{56}$/);
        send(response, body.id, { workspace: item.workspace });
        return;
      }
      assert.equal(body.params.name, 'exec_command');
      assert.equal(body.params.arguments.cmd, 'python');
      assert.deepEqual(body.params.arguments.argv, action.argv);
      assert.equal(body.params.arguments.workdir, 'tests');
      assert.equal(body.params.arguments.task_context_id, calls[0].params.arguments.task_context_id);
      assert.match(body.params.arguments.idempotency_key, /^cpex_[a-f0-9]{56}$/);
      send(response, body.id, {
        command_id: 'command-control-plane-exec-0001',
        status: 'exited',
        exit_code: 0,
        stdout: 'exec ok\n',
        stderr: '',
        truncated: false,
        timed_out: false,
        output_refs: null,
        execution_owner: {
          job_id: 'job-control-plane-exec-0001',
          run_id: '',
          wave_id: ''
        }
      });
    });
  });
  await listen(server);
  t.after(() => server.close());
  const context = createOrchestrator({ port: server.address().port, workspace: item.workspace });
  const result = await context.orchestrator.controlPlaneExec(action);
  assert.equal(calls.length, 2);
  assert.equal(result.operation_kind, 'control_plane_exec');
  assert.equal(result.status, 'exited');
  assert.equal(result.exit_code, 0);
  assert.equal(result.command_id, 'command-control-plane-exec-0001');
  assert.equal(result.job_id, 'job-control-plane-exec-0001');
  assert.equal(result.task_id, action.task_id);
  assert.equal(result.writer_lease_generation, 1);
  assert.match(result.local_handle, /^cp_exec_[a-f0-9]{48}$/);
  assert.equal(result.runtime_identity.activation_epoch_id, context.activationEpochId);
  assert.equal(result.runtime_identity.process_instance_id, context.processInstanceId);
  assert.equal(result.runtime_identity.server_instance_id, context.serverInstanceId);
  assert.equal(result.runtime_identity.tool_contract_sha256, context.contractSha256);
});

test('control-plane exec refuses a returned workspace outside the bound root', async (t) => {
  const item = fixture(t);
  const unrelated = path.join(path.dirname(item.workspace), 'unrelated');
  fs.mkdirSync(unrelated);
  const action = admission(item.workspace);
  let calls = 0;
  const server = http.createServer((request, response) => {
    calls += 1;
    const chunks = [];
    request.on('data', (chunk) => chunks.push(chunk));
    request.on('end', () => {
      const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      send(response, body.id, { workspace: unrelated });
    });
  });
  await listen(server);
  t.after(() => server.close());
  const context = createOrchestrator({ port: server.address().port, workspace: item.workspace });
  await assert.rejects(context.orchestrator.controlPlaneExec(action), { code: 'CONTROL_PLANE_EXEC_WORKSPACE_MISMATCH' });
  assert.equal(calls, 1);
});

test('control-plane exec polls an existing Job without calling exec_command', async (t) => {
  const item = fixture(t);
  const action = admission(item.workspace, {
    operation: 'exec_poll',
    command_id: 'command-control-plane-exec-poll-0001',
    job_id: 'job-control-plane-exec-poll-0001',
    local_handle: `cp_exec_${'b'.repeat(48)}`,
    consumer_id: 'control-plane-exec:poll-test',
    yield_time_ms: 1000,
    run_id: '',
    wave_id: ''
  });
  const calls = [];
  const server = http.createServer((request, response) => {
    const chunks = [];
    request.on('data', (chunk) => chunks.push(chunk));
    request.on('end', () => {
      const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      calls.push(body);
      if (calls.length === 1) {
        assert.equal(body.params.name, 'workspace_context');
        send(response, body.id, { workspace: item.workspace });
        return;
      }
      assert.equal(body.params.name, 'command_control');
      assert.equal(body.params.arguments.action, 'poll');
      assert.equal(body.params.arguments.command_id, action.command_id);
      assert.equal(body.params.arguments.consumer_id, action.consumer_id);
      assert.equal(body.params.arguments.yield_time_ms, 1000);
      send(response, body.id, {
        command_id: action.command_id,
        status: 'running',
        exit_code: null,
        stdout: 'still running\n',
        stderr: '',
        truncated: false,
        timed_out: false,
        output_refs: null,
        execution_owner: {
          job_id: action.job_id,
          run_id: '',
          wave_id: ''
        }
      });
    });
  });
  await listen(server);
  t.after(() => server.close());
  const context = createOrchestrator({ port: server.address().port, workspace: item.workspace });
  const result = await context.orchestrator.controlPlaneExec(action);
  assert.equal(calls.length, 2);
  assert.equal(result.status, 'running');
  assert.equal(result.command_id, action.command_id);
  assert.equal(result.job_id, action.job_id);
});

test('control-plane exec stop maps a terminal kill result to stopped', async (t) => {
  const item = fixture(t);
  const action = admission(item.workspace, {
    operation: 'exec_stop',
    command_id: 'command-control-plane-exec-stop-0001',
    job_id: 'job-control-plane-exec-stop-0001',
    local_handle: `cp_exec_${'c'.repeat(48)}`,
    consumer_id: 'control-plane-exec:stop-test',
    yield_time_ms: 500,
    signal: 'TERM',
    wait_ms: 3000,
    run_id: '',
    wave_id: ''
  });
  const calls = [];
  const server = http.createServer((request, response) => {
    const chunks = [];
    request.on('data', (chunk) => chunks.push(chunk));
    request.on('end', () => {
      const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      calls.push(body);
      if (calls.length === 1) {
        assert.equal(body.params.name, 'workspace_context');
        send(response, body.id, { workspace: item.workspace });
        return;
      }
      assert.equal(body.params.name, 'command_control');
      assert.equal(body.params.arguments.action, 'kill');
      assert.equal(body.params.arguments.command_id, action.command_id);
      assert.equal(body.params.arguments.signal, 'TERM');
      assert.equal(body.params.arguments.wait_ms, 3000);
      send(response, body.id, {
        command_id: action.command_id,
        status: 'terminated',
        exit_code: 143,
        stdout: '',
        stderr: 'terminated\n',
        truncated: false,
        timed_out: false,
        output_refs: null,
        execution_owner: {
          job_id: action.job_id,
          run_id: '',
          wave_id: ''
        }
      });
    });
  });
  await listen(server);
  t.after(() => server.close());
  const context = createOrchestrator({ port: server.address().port, workspace: item.workspace });
  const result = await context.orchestrator.controlPlaneExec(action);
  assert.equal(calls.length, 2);
  assert.equal(result.status, 'stopped');
  assert.equal(result.exit_code, 143);
  assert.equal(result.job_id, action.job_id);
});
