'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { Readable } = require('node:stream');

const {
  normalisedResult,
  readRequest,
  runDevelopmentFileReadBridge
} = require('../control_plane/recovery_file_read_bridge.cjs');
const {
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE,
  admitFileReadBridgeRequest,
  digest,
  fileContentDigest,
  normaliseFileReadResult
} = require('../../electron/services/controlPlaneFileReadBridge');
const { RPC_ACTIONS, RecoveryIpcServer, RecoveryIpcClient, loadRecoveryDescriptor } = require('../../electron/services/recoveryIpc');
const { createRuntimePaths } = require('../../electron/services/runtimePaths');

const descriptor = Object.freeze({
  installation_id: 'a'.repeat(64),
  runtime_mode: 'development',
  instance_id: 'recovery-host-file-read-0001',
  token: 'must-not-be-returned',
  owner_process_start_token: 'must-not-be-returned'
});

const request = Object.freeze({
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
  tool_name: 'workspace_context',
  operation: 'read_file',
  path: 'fixture.txt',
  start_line: 1,
  max_lines: 20,
  max_bytes: 1024,
  expires_at_ms: Date.now() + 60_000,
  facade_contract: {
    schema_version: 8,
    profile: 'control-plane-oauth-bounded-file-read-v1',
    sha256: 'f'.repeat(64)
  }
});

function safeResult() {
  const content = 'line one\nline two\n';
  const bytes = Buffer.byteLength(content, 'utf8');
  const file = {
    path: request.path,
    content,
    content_sha256: fileContentDigest(content),
    encoding: 'utf-8',
    start_line: 1,
    end_line: 2,
    total_lines: 2,
    total_bytes: bytes,
    bytes_read: bytes,
    truncated: false,
    next_start_line: null
  };
  return {
    schema_version: 1,
    operation_kind: 'control_plane_bounded_file_read',
    action_id: request.action_id,
    attempt_id: request.attempt_id,
    local_handle: `cp_fr_${'b'.repeat(48)}`,
    file_accessed: true,
    policy_sha256: 'c'.repeat(64),
    actor: { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE },
    runtime_identity: {
      activation_epoch_id: 'activation-file-read-0001',
      process_instance_id: 'process-file-read-0001',
      server_instance_id: 'server-file-read-0001',
      tool_contract_sha256: 'd'.repeat(64)
    },
    facade_contract: { ...request.facade_contract },
    file,
    response_sha256: digest(file)
  };
}

test('file-read bridge forwards only the sealed request and strips descriptor secrets', async () => {
  const calls = [];
  const result = await runDevelopmentFileReadBridge(request, {
    appRoot: process.cwd(),
    dependencies: {
      createDevelopmentPaths: () => ({ runtimeIdentity: () => ({ mode: 'development', installation_id: 'a'.repeat(64) }) }),
      loadRecoveryDescriptor: () => descriptor,
      descriptorMatchesInstallation: () => true,
      descriptorRequestOptions: (value) => ({ expectedInstanceId: value.instance_id }),
      clientFactory: () => ({ call: async (...args) => { calls.push(args); return safeResult(); } }),
      fileReadBridge: { normaliseFileReadResult }
    }
  });
  assert.deepEqual(calls, [[
    'runtime.control_plane_bounded_file_read',
    [request],
    { expectedInstanceId: descriptor.instance_id }
  ]]);
  assert.equal(result.file_accessed, true);
  assert.equal(result.actor.client_id, BRIDGE_CLIENT_ID);
  assert.equal(result.file.path, 'fixture.txt');
  assert.equal(JSON.stringify(result).includes('must-not-be-returned'), false);
  assert.equal(RPC_ACTIONS.includes('runtime.control_plane_bounded_file_read'), true);
});

test('file-read bridge allowlists its response and rejects sensitive content before it returns to Python', () => {
  const result = normalisedResult(descriptor, { ...safeResult(), workspace_root: 'E:\\private-workspace' }, request, { normaliseFileReadResult });
  assert.equal(Object.hasOwn(result, 'workspace_root'), false);
  assert.equal(JSON.stringify(result).includes('private-workspace'), false);

  const unsafe = safeResult();
  unsafe.file.content = 'secret = sk-example-secret-value-123456789\n';
  unsafe.file.content_sha256 = fileContentDigest(unsafe.file.content);
  unsafe.file.bytes_read = Buffer.byteLength(unsafe.file.content, 'utf8');
  unsafe.file.total_bytes = unsafe.file.bytes_read;
  unsafe.file.total_lines = 1;
  unsafe.file.end_line = 1;
  unsafe.response_sha256 = digest(unsafe.file);
  assert.throws(
    () => normalisedResult(descriptor, unsafe, request, { normaliseFileReadResult }),
    { code: 'CONTROL_PLANE_FILE_READ_SENSITIVE_CONTENT' }
  );
});

test('file-read bridge refuses installation mismatch before it opens Recovery IPC', async () => {
  let called = false;
  await assert.rejects(
    runDevelopmentFileReadBridge(request, {
      appRoot: process.cwd(),
      dependencies: {
        createDevelopmentPaths: () => ({ runtimeIdentity: () => ({ mode: 'development', installation_id: 'a'.repeat(64) }) }),
        loadRecoveryDescriptor: () => descriptor,
        descriptorMatchesInstallation: () => false,
        descriptorRequestOptions: () => ({}),
        clientFactory: () => ({ call: async () => { called = true; } }),
        fileReadBridge: { normaliseFileReadResult }
      }
    }),
    { code: 'RECOVERY_HOST_INSTALLATION_MISMATCH' }
  );
  assert.equal(called, false);
});

test('file-read request survives stdin JSON and real Recovery IPC without shape drift', async (t) => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'cp-file-read-ipc-'));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  const appRoot = path.resolve(__dirname, '../..');
  const paths = createRuntimePaths({ dataRoot: directory, appRoot, resourcesRoot: path.join(appRoot, 'resources'), runtimeMode: 'development' });
  const observed = [];
  let effects = 0;
  const policy = {
    ...request,
    schema_version: 1,
    enabled: true,
    allowed_relative_paths: ['fixture.txt'],
    policy_sha256: 'c'.repeat(64)
  };
  const server = new RecoveryIpcServer({
    paths,
    instanceId: 'file-read-real-ipc-test',
    startedAt: new Date().toISOString(),
    log: { warn() {} },
    handlers: {
      'runtime.control_plane_bounded_file_read': async (value) => {
        observed.push(value);
        admitFileReadBridgeRequest(policy, value);
        effects += 1;
        return safeResult();
      }
    }
  });
  const liveDescriptor = await server.start();
  t.after(() => server.stop());
  const dependencies = {
    createDevelopmentPaths: () => paths,
    RecoveryIpcClient,
    loadRecoveryDescriptor,
    fileReadBridge: { normaliseFileReadResult }
  };
  const parsed = await readRequest(Readable.from([Buffer.from(JSON.stringify(request), 'utf8')]));
  const result = await runDevelopmentFileReadBridge(parsed, { appRoot, dependencies });
  assert.deepEqual(observed, [request]);
  assert.equal(result.file_accessed, true);
  assert.equal(result.installation_id, liveDescriptor.installation_id);
  assert.equal(effects, 1);
  for (const invalid of [{ ...request, max_lines: '20' }, { ...request, extra: 'untrusted' }, [request]]) {
    await assert.rejects(runDevelopmentFileReadBridge(invalid, { appRoot, dependencies }), {
      code: 'CONTROL_PLANE_FILE_READ_REQUEST_INVALID'
    });
  }
  assert.equal(effects, 1, 'malformed requests must fail before any local effect');
});
