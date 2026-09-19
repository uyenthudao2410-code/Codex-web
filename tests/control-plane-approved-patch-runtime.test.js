'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const zlib = require('node:zlib');

const { RuntimeOrchestrator } = require('../electron/services/runtimeOrchestrator');
const {
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE,
  digest
} = require('../electron/services/controlPlaneApprovedPatchBridge');

function listen(server) {
  return new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
}

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function fixture(t) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-approved-patch-runtime-'));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  const registeredRoot = path.join(directory, 'registered-root');
  const unrelatedUiRoot = path.join(directory, 'unrelated-ui-root');
  fs.mkdirSync(registeredRoot);
  fs.mkdirSync(unrelatedUiRoot);
  const target = path.join(registeredRoot, 'fixture.txt');
  fs.writeFileSync(target, 'before\n', 'utf8');
  return { registeredRoot, unrelatedUiRoot, target };
}

function exactPatch(pathValue, before, after) {
  const preimage = sha256(Buffer.from(before, 'utf8'));
  const postimage = sha256(Buffer.from(after, 'utf8'));
  const encoded = zlib.deflateSync(Buffer.from(after, 'utf8')).toString('base64');
  const envelope = [
    '*** Begin Patch',
    `*** Write Exact File: ${pathValue}`,
    `@@ encoding=zlib-base64 preimage_sha256=${preimage} postimage_sha256=${postimage}`,
    `+${encoded}`,
    '*** End Patch'
  ].join('\n');
  return { envelope, preimage, postimage, patchSha256: sha256(Buffer.from(envelope, 'utf8')), bytes: Buffer.byteLength(after, 'utf8') };
}

function admission(workspaceRoot, before = 'before\n', after = 'after\n') {
  const patch = exactPatch('fixture.txt', before, after);
  return {
    action_id: 'action-control-plane-0001',
    attempt_id: 'attempt-control-plane-0001',
    policy_sha256: 'a'.repeat(64),
    tool_name: 'agent_workflow',
    operation: 'apply_patch',
    validation_profile: 'targeted',
    workspace_root: workspaceRoot,
    workspace_id: 'workspace-control-plane-0001',
    workspace_generation: 'generation-control-plane-0001',
    permission_request_id: 'permission-control-plane-0001',
    permission_digest: 'b'.repeat(64),
    intent_digest: 'c'.repeat(64),
    path: 'fixture.txt',
    preimage_sha256: patch.preimage,
    patch_sha256: patch.patchSha256,
    patch_envelope: patch.envelope,
    postimage_sha256: patch.postimage,
    postimage_bytes: patch.bytes,
    max_file_bytes: 4096,
    facade_contract: {
      schema_version: 10,
      profile: 'control-plane-oauth-approved-patch-v1',
      sha256: 'f'.repeat(64)
    },
    _after: after
  };
}

function createOrchestrator({ port, globalWorkspace }) {
  const secret = 'control-plane-approved-patch-runtime-secret';
  const activationEpochId = 'activation-control-plane-approved-patch-0001';
  const processInstanceId = 'process-control-plane-approved-patch-0001';
  const serverInstanceId = 'server-control-plane-approved-patch-0001';
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
  return { orchestrator, activationEpochId, processInstanceId, serverInstanceId, contractSha256 };
}

function send(response, id, structuredContent) {
  const payload = JSON.stringify({ jsonrpc: '2.0', id, result: { structuredContent } });
  response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) });
  response.end(payload);
}

function approvedPatchWorkflowResult(action, idempotencyKey, {
  runId = '1'.repeat(32),
  waveId = '2'.repeat(32),
  requestHash = '3'.repeat(64)
} = {}) {
  const affectedFiles = [{ path: action.path, operation: 'update' }];
  return {
    workflow: 'custom',
    phase: 'execute',
    durable_idempotency: true,
    execution: {
      ok: true,
      status: 'passed',
      affected_files: affectedFiles,
      patch_results: [{ dry_run: false, clean: true, affected_files: affectedFiles }]
    },
    orchestration: {
      run_id: runId,
      wave_id: waveId,
      orchestration_state: 'ACCEPTING'
    },
    idempotency: {
      operation: 'agent_workflow',
      status: 'completed',
      idempotency_key: idempotencyKey,
      request_hash: requestHash,
      run_id: runId,
      wave_id: waveId,
      summary: {
        execution_ok: true,
        execution_status: 'passed',
        run_id: runId,
        wave_id: waveId,
        orchestration_state: 'ACCEPTING'
      }
    }
  };
}

test('approved patch binds the registered root, creates a local RUN/WAVE, and returns only a receipt', async (t) => {
  const item = fixture(t);
  const action = admission(item.registeredRoot);
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
        assert.notEqual(body.params.arguments.path, item.unrelatedUiRoot);
        assert.match(body.params.arguments.task_context_id, /^cpap_[a-f0-9]{56}$/);
        send(response, body.id, { workspace: item.registeredRoot });
        return;
      }
      assert.equal(calls.length, 2, 'the bridge must only bind then run one exact local workflow');
      assert.equal(body.params.name, 'agent_workflow');
      assert.deepEqual(body.params.arguments, {
        task_context_id: calls[0].params.arguments.task_context_id,
        idempotency_key: body.params.arguments.idempotency_key,
        workflow: 'custom',
        phase: 'execute',
        execution_mode: 'mcp_only',
        execution_route: 'deterministic',
        objective: 'Apply one owner-approved exact local patch.',
        path: item.registeredRoot,
        patch: action.patch_envelope,
        dry_run: false,
        verification: 'none',
        include_diff: false
      });
      assert.match(body.params.arguments.idempotency_key, /^cpap_[a-f0-9]{56}$/);
      fs.writeFileSync(item.target, action._after, 'utf8');
      send(response, body.id, approvedPatchWorkflowResult(action, body.params.arguments.idempotency_key));
    });
  });
  await listen(server);
  t.after(() => server.close());

  const context = createOrchestrator({ port: server.address().port, globalWorkspace: item.unrelatedUiRoot });
  const result = await context.orchestrator.controlPlaneApprovedPatch(action);
  assert.equal(calls.length, 2);
  assert.equal(fs.readFileSync(item.target, 'utf8'), action._after);
  assert.equal(result.patch_applied, true);
  assert.equal(result.local_semantic_acceptance, 'pending');
  assert.deepEqual(result.file, {
    path: 'fixture.txt',
    preimage_sha256: action.preimage_sha256,
    postimage_sha256: action.postimage_sha256,
    bytes_written: Buffer.byteLength(action._after, 'utf8')
  });
  assert.equal(result.response_sha256, digest(result.file));
  assert.equal(Object.hasOwn(result, 'patch_envelope'), false);
  assert.equal(JSON.stringify(result).includes(action.patch_envelope), false);
  assert.match(result.local_handle, /^cp_ap_[a-f0-9]{48}$/);
  assert.equal(Object.hasOwn(result, 'run_id'), false);
  assert.equal(JSON.stringify(result).includes('1'.repeat(32)), false);
  assert.equal(JSON.stringify(result).includes('2'.repeat(32)), false);
  assert.equal(result.runtime_identity.activation_epoch_id, context.activationEpochId);
  assert.equal(result.runtime_identity.process_instance_id, context.processInstanceId);
  assert.equal(result.runtime_identity.server_instance_id, context.serverInstanceId);
});

test('approved patch refuses a malformed local workflow result after a possible effect', async (t) => {
  const item = fixture(t);
  const action = admission(item.registeredRoot);
  let calls = 0;
  const server = http.createServer((request, response) => {
    const chunks = [];
    request.on('data', (chunk) => chunks.push(chunk));
    request.on('end', () => {
      calls += 1;
      const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      if (calls === 1) {
        send(response, body.id, { workspace: item.registeredRoot });
        return;
      }
      assert.equal(body.params.name, 'agent_workflow');
      fs.writeFileSync(item.target, action._after, 'utf8');
      const malformed = approvedPatchWorkflowResult(action, body.params.arguments.idempotency_key);
      delete malformed.orchestration.wave_id;
      send(response, body.id, malformed);
    });
  });
  await listen(server);
  t.after(() => server.close());
  const context = createOrchestrator({ port: server.address().port, globalWorkspace: item.unrelatedUiRoot });
  await assert.rejects(
    context.orchestrator.controlPlaneApprovedPatch(action),
    { code: 'CONTROL_PLANE_APPROVED_PATCH_MCP_RESULT_INVALID' }
  );
  assert.equal(calls, 2);
  assert.equal(fs.readFileSync(item.target, 'utf8'), action._after);
});

test('approved patch rejects a stale preimage before it binds or calls the local MCP', async (t) => {
  const item = fixture(t);
  const action = admission(item.registeredRoot);
  fs.writeFileSync(item.target, 'user changed this\n', 'utf8');
  let calls = 0;
  const server = http.createServer(() => { calls += 1; });
  await listen(server);
  t.after(() => server.close());
  const context = createOrchestrator({ port: server.address().port, globalWorkspace: item.unrelatedUiRoot });
  await assert.rejects(
    context.orchestrator.controlPlaneApprovedPatch(action),
    { code: 'CONTROL_PLANE_APPROVED_PATCH_PREIMAGE_MISMATCH' }
  );
  assert.equal(calls, 0);
});

test('approved patch refuses a local context bound to another workspace before it applies', async (t) => {
  const item = fixture(t);
  const action = admission(item.registeredRoot);
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
    context.orchestrator.controlPlaneApprovedPatch(action),
    { code: 'CONTROL_PLANE_APPROVED_PATCH_WORKSPACE_MISMATCH' }
  );
  assert.equal(calls, 1);
  assert.equal(fs.readFileSync(item.target, 'utf8'), 'before\n');
});
