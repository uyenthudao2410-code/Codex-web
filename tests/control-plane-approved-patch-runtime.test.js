'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const zlib = require('node:zlib');
const { spawnSync } = require('node:child_process');

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

function assertLocalMcpSchemaAccepts(calls) {
  // Validate the actual emitted packets with the Python runtime contract.
  // A permissive mock MCP server otherwise hides rejected bridge arguments.
  const code = [
    'import json,sys',
    'from coding_tools_mcp.tool_schema import validate_arguments',
    'from coding_tools_mcp.errors import JsonRpcError',
    'calls=json.load(sys.stdin)',
    'for call in calls: validate_arguments(call["params"]["name"],call["params"]["arguments"])',
    'workflow=next(call["params"]["arguments"] for call in calls if call["params"]["name"]=="agent_workflow")',
    'try:',
    ' validate_arguments("agent_workflow",dict(workflow,include_diff=False))',
    'except JsonRpcError as error:',
    ' assert "include_diff is not a recognized argument" in str(error)',
    'else:',
    ' raise AssertionError("Regression fixture must reject the unsupported workflow argument")',
    'print("BRIDGE_SCHEMA_OK")'
  ].join('\n');
  const result = spawnSync(process.execPath, [
    path.join(__dirname, '..', 'scripts', 'run-python.js'), '-B', '-c', code
  ], {
    cwd: path.join(__dirname, '..', 'resources', 'coding-tools-mcp'),
    input: JSON.stringify(calls),
    encoding: 'utf8',
    timeout: 15_000,
    windowsHide: true
  });
  assert.equal(result.error, undefined);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.match(result.stdout, /BRIDGE_SCHEMA_OK/);
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
    task_id: `task_${'a'.repeat(32)}`,
    writer_lease_generation: 1,
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

test('initial verification observes the original background workflow and retains failed proof without another write', async (t) => {
  const item = fixture(t);
  const action = admission(item.registeredRoot);
  action.verification = { argv: ['node', '--test', 'tests/fixture.test.js'], cwd: '', timeout_ms: 60000, max_output_bytes: 32768 };
  action.exec_policy_sha256 = 'e'.repeat(64);
  action.expires_at_ms = Date.now() + 600000;
  const calls = [];
  const requestTimeouts = [];
  const request = http.request;
  let now = Date.now();
  t.mock.method(Date, 'now', () => now);
  t.mock.method(http, 'request', function (options, ...argumentsList) {
    requestTimeouts.push(options.timeout);
    return Reflect.apply(request, this, [options, ...argumentsList]);
  });
  let workflowArguments;
  const operationId = 'background_opaque_operation';
  const proof = { plan_sha256: digest(action.verification), proof_status: 'failed', proof_ids: ['4'.repeat(32)], proof_fingerprint: null,
    command_id: '-original-command', job_id: '_original-job' };
  const server = http.createServer((request, response) => {
    const chunks = [];
    request.on('data', chunk => chunks.push(chunk));
    request.on('end', () => {
      assert.equal(request.headers['x-coding-tools-client-id'], BRIDGE_CLIENT_ID);
      const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      calls.push(body);
      if (calls.length === 1) return send(response, body.id, { workspace: item.registeredRoot });
      if (calls.length === 2) {
        assert.equal(body.params.name, 'agent_workflow');
        workflowArguments = body.params.arguments;
        assert.deepEqual(workflowArguments.initial_verification, action.verification);
        assert.equal(workflowArguments.initial_verification_expires_at_ms, action.expires_at_ms);
        assert.equal(workflowArguments.verification, 'none');
        now += 325_000; // Simulate elapsed handoff/setup without a real wait.
        fs.writeFileSync(item.target, action._after, 'utf8');
        return send(response, body.id, { status: 'running', background_operation: {
          operation_id: operationId, tool: 'agent_workflow', workspace: item.registeredRoot, status: 'running' } });
      }
      assert.equal(calls.length, 3);
      assert.equal(body.params.name, 'task_control');
      assert.equal(body.params.arguments.action, 'operation');
      assert.equal(body.params.arguments.operation_id, operationId);
      assert.equal(body.params.arguments.wait_ms, 5_000);
      assert.equal(body.params.arguments.task_context_id, workflowArguments.task_context_id);
      const completed = approvedPatchWorkflowResult(action, workflowArguments.idempotency_key);
      Object.assign(completed.execution, { ok: false, status: 'failed', initial_verification: proof });
      completed.orchestration.orchestration_state = 'REPLAN';
      Object.assign(completed.idempotency.summary, { execution_ok: false, execution_status: 'failed', orchestration_state: 'REPLAN',
        initial_verification: proof, patch_effect: { applied: true, affected_files: [{ path: action.path, operation: 'update' }] } });
      send(response, body.id, { background_operation: { operation_id: operationId, tool: 'agent_workflow', workspace: item.registeredRoot,
        status: 'completed', result: { structuredContent: completed } } });
    });
  });
  await listen(server);
  t.after(() => server.close());
  const context = createOrchestrator({ port: server.address().port, globalWorkspace: item.unrelatedUiRoot });
  const result = await context.orchestrator.controlPlaneApprovedPatch(action);
  assert.equal(calls.filter(call => call.params.name === 'agent_workflow').length, 1);
  assert.equal(result.patch_applied, true);
  assert.equal(result.local_semantic_acceptance, 'pending');
  assert.equal(result.initial_verification.proof_status, 'failed');
  assert.deepEqual(requestTimeouts, [12_000, 330_000, 15_000]);
  assert.equal(fs.readFileSync(item.target, 'utf8'), action._after);
  assert.equal(result.response_sha256, digest({ file: result.file, initial_verification: proof }));
  assertLocalMcpSchemaAccepts(calls);
});

test('initial verification expires its original observation budget without another write or poll', async (t) => {
  const item = fixture(t);
  const action = admission(item.registeredRoot);
  action.verification = { argv: ['node', '--test'], cwd: '', timeout_ms: 60000, max_output_bytes: 32768 };
  action.exec_policy_sha256 = 'e'.repeat(64);
  action.expires_at_ms = Date.now() + 600000;
  let now = Date.now();
  t.mock.method(Date, 'now', () => now);
  const calls = [];
  const server = http.createServer((request, response) => {
    const chunks = [];
    request.on('data', chunk => chunks.push(chunk));
    request.on('end', () => {
      const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      calls.push(body);
      if (calls.length === 1) return send(response, body.id, { workspace: item.registeredRoot });
      assert.equal(body.params.name, 'agent_workflow');
      assert.equal(calls.length, 2, 'an exhausted budget must not poll or start another workflow');
      fs.writeFileSync(item.target, action._after, 'utf8');
      now += 330_001;
      send(response, body.id, { status: 'running', background_operation: {
        operation_id: 'background_expired_operation', tool: 'agent_workflow', workspace: item.registeredRoot, status: 'running' } });
    });
  });
  await listen(server);
  t.after(() => server.close());
  const context = createOrchestrator({ port: server.address().port, globalWorkspace: item.unrelatedUiRoot });
  await assert.rejects(context.orchestrator.controlPlaneApprovedPatch(action), {
    code: 'CONTROL_PLANE_APPROVED_PATCH_OPERATION_UNCONFIRMED'
  });
  assert.equal(calls.length, 2);
  assert.equal(calls.filter(call => call.params.name === 'agent_workflow').length, 1);
  assert.equal(fs.readFileSync(item.target, 'utf8'), action._after);
});

test('initial verification cannot write before independent local exec admission', async (t) => {
  const item = fixture(t);
  const action = admission(item.registeredRoot);
  action.verification = { argv: ['node', '--test'], cwd: '', timeout_ms: 60000, max_output_bytes: 32768 };
  const context = createOrchestrator({ port: 1, globalWorkspace: item.registeredRoot });
  await assert.rejects(context.orchestrator.controlPlaneApprovedPatch(action), { code: 'CONTROL_PLANE_APPROVED_PATCH_EXEC_POLICY_REQUIRED' });
  assert.equal(fs.readFileSync(item.target, 'utf8'), 'before\n');
});

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
      const workflowArguments = body.params.arguments;
      const { contract_fingerprint: contractFingerprint, ...workflowWithoutFingerprint } = workflowArguments;
      assert.match(contractFingerprint, /^[a-f0-9]{64}$/);
      assert.deepEqual(workflowWithoutFingerprint, {
        task_context_id: calls[0].params.arguments.task_context_id,
        idempotency_key: workflowArguments.idempotency_key,
        workflow: 'custom',
        phase: 'execute',
        execution_mode: 'mcp_only',
        execution_route: 'deterministic',
        objective: 'Apply one owner-approved exact local patch.',
        path: item.registeredRoot,
        patch: action.patch_envelope,
        dry_run: false,
        verification: 'none'
      });
      assert.match(workflowArguments.idempotency_key, /^cpap_[a-f0-9]{56}$/);
      fs.writeFileSync(item.target, action._after, 'utf8');
      send(response, body.id, approvedPatchWorkflowResult(action, workflowArguments.idempotency_key));
    });
  });
  await listen(server);
  t.after(() => server.close());

  const context = createOrchestrator({ port: server.address().port, globalWorkspace: item.unrelatedUiRoot });
  const result = await context.orchestrator.controlPlaneApprovedPatch(action);
  assert.equal(calls.length, 2);
  assertLocalMcpSchemaAccepts(calls);
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
  assert.equal(result.task_id, action.task_id);
  assert.equal(result.writer_lease_generation, action.writer_lease_generation);
  assert.equal(result.run_id, '1'.repeat(32));
  assert.equal(result.wave_id, '2'.repeat(32));
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
