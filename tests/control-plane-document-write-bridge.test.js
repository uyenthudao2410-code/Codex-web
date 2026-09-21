'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE,
  admitDocumentWriteBridgeRequest,
  digest,
  loadDocumentWriteBridgePolicy,
  normaliseDocumentWriteResult,
  resolveRegisteredDocumentWorkspaceRoot
} = require('../electron/services/controlPlaneDocumentWriteBridge');

const NOW = 1_700_000_000_000;
const CONTRACT = Object.freeze({
  schema_version: 24,
  profile: 'control-plane-oauth-standing-document-write-v1',
  sha256: 'f'.repeat(64)
});

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function fixture(t, { write = true } = {}) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-document-write-'));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  const root = path.join(directory, 'workspace');
  fs.mkdirSync(path.join(root, 'docs'), { recursive: true });
  fs.writeFileSync(path.join(root, 'input.md'), '# source\n', 'utf8');
  const policyFile = path.join(directory, 'approved-patch-policy.json');
  const registryFile = path.join(directory, 'workspace-registry.json');
  const paths = {
    controlPlaneApprovedPatchPolicyFile: () => policyFile,
    controlPlaneWorkspaceRegistryFile: () => registryFile
  };
  const policy = {
    schema_version: 2,
    enabled: true,
    authority_mode: 'standing',
    server_origin: 'https://control.example.test',
    owner_id: 'owner-control-plane-0001',
    device_id: 'device-control-plane-0001',
    endpoint_id: 'endpoint-control-plane-0001',
    workspace_id: 'workspace-control-plane-0001',
    workspace_generation: 'generation-control-plane-0001',
    expires_at_ms: null,
    facade_contract: { ...CONTRACT },
    allowed_relative_paths: ['docs/result.md', 'input.md', 'docs/result.docx'],
    max_patch_bytes: 4096,
    max_file_bytes: 4096,
    validation_profile: 'targeted'
  };
  fs.writeFileSync(policyFile, JSON.stringify(policy), 'utf8');
  fs.writeFileSync(registryFile, JSON.stringify({
    schema_version: 1,
    entries: [{
      workspace_id: policy.workspace_id,
      workspace_generation: policy.workspace_generation,
      canonical_path: root,
      display_name: 'Fixture workspace',
      capabilities: { read: true, write, exec: false },
      created_at_ms: NOW
    }]
  }), 'utf8');
  return { root, policyFile, registryFile, paths };
}

function request(policy, overrides = {}) {
  const content = overrides.content || 'created by bridge\n';
  const operation = overrides.operation || 'document_create';
  const target = overrides.target || (operation === 'document_convert' ? 'docs/result.docx' : 'docs/result.md');
  const source = Object.hasOwn(overrides, 'source')
    ? overrides.source
    : (operation === 'document_convert' ? 'input.md' : null);
  const intentDigest = overrides.intent_digest || 'a'.repeat(64);
  const value = {
    server_origin: policy.server_origin,
    owner_id: policy.owner_id,
    device_id: policy.device_id,
    endpoint_id: policy.endpoint_id,
    workspace_id: policy.workspace_id,
    workspace_generation: policy.workspace_generation,
    context_id: 'context-control-plane-0001',
    binding_id: 'binding-control-plane-0001',
    action_id: 'action-control-plane-0001',
    attempt_id: 'attempt-control-plane-0001',
    task_id: `task_${'a'.repeat(32)}`,
    writer_lease_generation: 1,
    authority_mode: 'standing',
    tool_name: 'document_workflow',
    operation,
    target,
    source,
    title: 'Bridge test',
    content,
    content_sha256: sha256(Buffer.from(content, 'utf8')),
    overwrite: false,
    intent_digest: intentDigest,
    admission_reference: `mcp_document_write:${intentDigest}`,
    expires_at_ms: NOW + 60_000,
    policy_sha256: policy.policy_sha256,
    facade_contract: { ...CONTRACT }
  };
  return { ...value, ...overrides, facade_contract: overrides.facade_contract || value.facade_contract };
}

function loaded(item) {
  return loadDocumentWriteBridgePolicy(item.paths, { now: NOW });
}

test('document write admits create and convert against the exact standing writable root', (t) => {
  const item = fixture(t);
  const policy = loaded(item);
  const create = admitDocumentWriteBridgeRequest(policy, request(policy), { now: NOW });
  assert.equal(create.operation_kind, 'control_plane_document_write');
  assert.deepEqual(create.actor, {
    client_id: 'electron-control-plane-document-bridge',
    client_type: 'electron'
  });
  assert.equal(create.target, 'docs/result.md');
  const convert = admitDocumentWriteBridgeRequest(policy, request(policy, { operation: 'document_convert' }), { now: NOW });
  assert.equal(convert.operation, 'document_convert');
  assert.equal(convert.source, 'input.md');
  assert.equal(resolveRegisteredDocumentWorkspaceRoot(item.paths, policy), fs.realpathSync.native(item.root));
});

test('document write rejects invalid operation/source/target combinations before effect', (t) => {
  const item = fixture(t);
  const policy = loaded(item);
  assert.throws(
    () => admitDocumentWriteBridgeRequest(policy, request(policy, { operation: 'document_create', source: 'input.md' }), { now: NOW }),
    { code: 'CONTROL_PLANE_DOCUMENT_WRITE_SOURCE_INVALID' }
  );
  assert.throws(
    () => admitDocumentWriteBridgeRequest(policy, request(policy, { operation: 'document_convert', target: 'docs/result.md' }), { now: NOW }),
    { code: 'CONTROL_PLANE_DOCUMENT_WRITE_SOURCE_INVALID' }
  );
  assert.throws(
    () => admitDocumentWriteBridgeRequest(policy, request(policy, { target: 'docs/result.json' }), { now: NOW }),
    { code: 'CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID' }
  );
});

test('document write rejects stale target/policy and paths outside the local allowlist', (t) => {
  const item = fixture(t);
  const policy = loaded(item);
  assert.throws(
    () => admitDocumentWriteBridgeRequest(policy, request(policy, { device_id: 'device-other-0001' }), { now: NOW }),
    { code: 'CONTROL_PLANE_DOCUMENT_WRITE_TARGET_MISMATCH' }
  );
  assert.throws(
    () => admitDocumentWriteBridgeRequest(policy, request(policy, { target: 'docs/missing.md' }), { now: NOW }),
    { code: 'CONTROL_PLANE_DOCUMENT_WRITE_PATH_DENIED' }
  );
  const invalidDigest = request(policy);
  invalidDigest.policy_sha256 = '0'.repeat(64);
  assert.throws(
    () => admitDocumentWriteBridgeRequest(policy, invalidDigest, { now: NOW }),
    { code: 'CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID' }
  );
});

test('document write refuses a registry without local write capability', (t) => {
  const item = fixture(t, { write: false });
  const policy = loaded(item);
  assert.throws(
    () => resolveRegisteredDocumentWorkspaceRoot(item.paths, policy),
    { code: 'CONTROL_PLANE_DOCUMENT_WRITE_WORKSPACE_REGISTRY_REQUIRED' }
  );
});

test('document receipt normalization is digest-only and rejects path/identity drift', (t) => {
  const item = fixture(t);
  const policy = loaded(item);
  const admission = admitDocumentWriteBridgeRequest(policy, request(policy), { now: NOW });
  const result = {
    schema_version: 1,
    operation_kind: 'control_plane_document_write',
    local_handle: `cp_doc_${'b'.repeat(48)}`,
    action_id: admission.action_id,
    attempt_id: admission.attempt_id,
    task_id: admission.task_id,
    writer_lease_generation: admission.writer_lease_generation,
    operation: admission.operation,
    target: admission.target,
    source: admission.source,
    result: { target: admission.target, size: 12, sha256: '1'.repeat(64), format: 'md' },
    actor: { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE },
    policy_sha256: admission.policy_sha256,
    facade_contract: { ...admission.facade_contract },
    runtime_identity: {
      activation_epoch_id: 'activation-document-write-0001',
      process_instance_id: 'process-document-write-0001',
      server_instance_id: 'server-document-write-0001',
      tool_contract_sha256: '2'.repeat(64)
    }
  };
  result.response_sha256 = digest({
    operation: admission.operation,
    target: admission.target,
    source: admission.source,
    size: result.result.size,
    sha256: result.result.sha256,
    format: result.result.format
  });
  const normalized = normaliseDocumentWriteResult(result, admission);
  assert.equal(normalized.result.target, 'docs/result.md');
  assert.equal(Object.hasOwn(normalized, 'workspace_root'), false);
  assert.equal(JSON.stringify(normalized).includes(item.root), false);

  const drifted = { ...result, target: '/private/path/result.md' };
  assert.throws(
    () => normaliseDocumentWriteResult(drifted, admission),
    { code: 'CONTROL_PLANE_DOCUMENT_WRITE_RESULT_INVALID' }
  );
});
