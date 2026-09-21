'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { PassThrough, Readable } = require('node:stream');

const {
  MAX_REQUEST_BYTES,
  readRequest,
  normalisedResult,
  runDevelopmentDocumentWriteBridge
} = require('../control_plane/recovery_document_write_bridge.cjs');
const {
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE,
  digest,
  normaliseDocumentWriteResult
} = require('../../electron/services/controlPlaneDocumentWriteBridge');

const descriptor = Object.freeze({
  installation_id: 'a'.repeat(64),
  runtime_mode: 'development',
  instance_id: 'recovery-host-document-write-0001',
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
  task_id: `task_${'a'.repeat(32)}`,
  writer_lease_generation: 1,
  authority_mode: 'standing',
  tool_name: 'document_workflow',
  operation: 'document_create',
  target: 'docs/result.md',
  source: null,
  title: 'Bridge test',
  content: 'document bridge ok\n',
  content_sha256: 'c'.repeat(64),
  overwrite: false,
  intent_digest: 'b'.repeat(64),
  admission_reference: 'mcp_document_write:' + 'b'.repeat(64),
  expires_at_ms: Date.now() + 60_000,
  policy_sha256: 'd'.repeat(64),
  facade_contract: {
    schema_version: 24,
    profile: 'control-plane-oauth-standing-document-write-v1',
    sha256: 'e'.repeat(64)
  }
});

function safeResult() {
  const result = {
    target: request.target,
    size: Buffer.byteLength(request.content, 'utf8'),
    sha256: 'f'.repeat(64),
    format: 'md'
  };
  return {
    schema_version: 1,
    operation_kind: 'control_plane_document_write',
    local_handle: `cp_doc_${'a'.repeat(48)}`,
    action_id: request.action_id,
    attempt_id: request.attempt_id,
    task_id: request.task_id,
    writer_lease_generation: request.writer_lease_generation,
    operation: request.operation,
    target: request.target,
    source: request.source,
    result,
    actor: { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE },
    policy_sha256: request.policy_sha256,
    facade_contract: { ...request.facade_contract },
    runtime_identity: {
      activation_epoch_id: 'activation-document-write-0001',
      process_instance_id: 'process-document-write-0001',
      server_instance_id: 'server-document-write-0001',
      tool_contract_sha256: '1'.repeat(64)
    },
    response_sha256: digest({
      operation: request.operation,
      target: request.target,
      source: request.source,
      ...result
    })
  };
}

test('document bridge accepts a full 256 KiB JSON content envelope below its bound', async () => {
  const content = 'x'.repeat(256 * 1024);
  const encoded = Buffer.from(JSON.stringify({ content }), 'utf8');
  assert.ok(encoded.length <= MAX_REQUEST_BYTES, `${encoded.length} > ${MAX_REQUEST_BYTES}`);
  const stream = Readable.from([encoded]);
  const parsed = await readRequest(stream);
  assert.equal(parsed.content.length, content.length);
});

test('document bridge rejects input beyond its bounded subprocess request size', async () => {
  const stream = Readable.from([Buffer.alloc(MAX_REQUEST_BYTES + 1, 0x41)]);
  await assert.rejects(readRequest(stream), { code: 'CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_TOO_LARGE' });
});

test('document bridge forwards only the sealed request and strips descriptor secrets', async () => {
  const calls = [];
  const paths = {
    appRoot: () => process.cwd(),
    runtimeIdentity: () => ({ mode: 'development', installation_id: descriptor.installation_id })
  };
  const result = await runDevelopmentDocumentWriteBridge(request, {
    appRoot: process.cwd(),
    dependencies: {
      lifecycle: { createDevelopmentPaths: () => paths },
      loadRecoveryDescriptor: () => descriptor,
      descriptorMatchesInstallation: () => true,
      descriptorRequestOptions: (value) => ({ expectedInstanceId: value.instance_id, token: value.token }),
      clientFactory: () => ({ call: async (...args) => { calls.push(args); return safeResult(); } }),
      documentWriteBridge: { normaliseDocumentWriteResult }
    }
  });
  assert.deepEqual(calls, [[
    'runtime.control_plane_document_write',
    [request],
    { expectedInstanceId: descriptor.instance_id, token: descriptor.token }
  ]]);
  assert.equal(result.operation_kind, 'control_plane_document_write');
  assert.equal(Object.hasOwn(result, 'token'), false);
  assert.equal(JSON.stringify(result).includes('must-not-be-returned'), false);
  assert.equal(JSON.stringify(result).includes('workspace_root'), false);
});

test('document bridge refuses a Recovery installation mismatch before IPC', async () => {
  const calls = [];
  const paths = {
    appRoot: () => process.cwd(),
    runtimeIdentity: () => ({ mode: 'development', installation_id: descriptor.installation_id })
  };
  await assert.rejects(
    runDevelopmentDocumentWriteBridge(request, {
      appRoot: process.cwd(),
      dependencies: {
        lifecycle: { createDevelopmentPaths: () => paths },
        loadRecoveryDescriptor: () => descriptor,
        descriptorMatchesInstallation: () => false,
        descriptorRequestOptions: () => ({}),
        clientFactory: () => ({ call: async (...args) => { calls.push(args); } }),
        documentWriteBridge: { normaliseDocumentWriteResult }
      }
    }),
    { code: 'RECOVERY_HOST_INSTALLATION_MISMATCH' }
  );
  assert.equal(calls.length, 0);
});

test('document bridge normalizer refuses a changed receipt digest', () => {
  const value = safeResult();
  value.result.sha256 = '0'.repeat(64);
  assert.throws(
    () => normalisedResult(descriptor, value, request, { normaliseDocumentWriteResult }),
    { code: 'CONTROL_PLANE_DOCUMENT_WRITE_RESULT_DIGEST_INVALID' }
  );
});
