'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE,
  admitFileReadBridgeRequest,
  digest,
  fileContentDigest,
  loadFileReadBridgePolicy,
  normaliseFileReadResult,
  resolveRegisteredWorkspaceRoot
} = require('../electron/services/controlPlaneFileReadBridge');

const NOW = 1_700_000_000_000;
const FACADE_CONTRACT = Object.freeze({
  schema_version: 8,
  profile: 'control-plane-oauth-bounded-file-read-v1',
  sha256: 'f'.repeat(64)
});

function fixture(t) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-file-read-'));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  const root = path.join(directory, 'workspace');
  fs.mkdirSync(root);
  const policyFile = path.join(directory, 'file-read-policy.json');
  const registryFile = path.join(directory, 'workspace-registry.json');
  return {
    root,
    policyFile,
    registryFile,
    paths: {
      controlPlaneFileReadPolicyFile: () => policyFile,
      controlPlaneWorkspaceRegistryFile: () => registryFile
    }
  };
}

function policy(now = NOW) {
  return {
    schema_version: 1,
    enabled: true,
    server_origin: 'https://control.example.test',
    owner_id: 'owner-control-plane-0001',
    device_id: 'device-control-plane-0001',
    endpoint_id: 'endpoint-control-plane-0001',
    workspace_id: 'workspace-control-plane-0001',
    workspace_generation: 'generation-control-plane-0001',
    expires_at_ms: now + 60_000,
    facade_contract: { ...FACADE_CONTRACT },
    allowed_relative_paths: ['fixture.txt'],
    max_bytes: 1024,
    max_lines: 20
  };
}

function request(now = NOW) {
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
    tool_name: 'workspace_context',
    operation: 'read_file',
    path: 'fixture.txt',
    start_line: 1,
    max_lines: 20,
    max_bytes: 1024,
    expires_at_ms: now + 30_000,
    facade_contract: { ...FACADE_CONTRACT }
  };
}

function writeRegistry(paths, root) {
  fs.writeFileSync(paths.controlPlaneWorkspaceRegistryFile(), JSON.stringify({
    schema_version: 1,
    entries: [{
      workspace_id: 'workspace-control-plane-0001',
      workspace_generation: 'generation-control-plane-0001',
      canonical_path: root,
      display_name: 'Fixture root',
      capabilities: { read: true, write: false, exec: false },
      created_at_ms: NOW
    }]
  }), 'utf8');
}

function safeResult(admission, content = 'line one\nline two\n') {
  const bytes = Buffer.byteLength(content, 'utf8');
  const lineCount = content ? 2 : 0;
  const file = {
    path: admission.path,
    content,
    content_sha256: fileContentDigest(content),
    encoding: 'utf-8',
    start_line: admission.start_line,
    end_line: lineCount,
    total_lines: lineCount,
    total_bytes: bytes,
    bytes_read: bytes,
    truncated: false,
    next_start_line: null
  };
  return {
    schema_version: 1,
    operation_kind: 'control_plane_bounded_file_read',
    local_handle: `cp_fr_${'a'.repeat(48)}`,
    action_id: admission.action_id,
    attempt_id: admission.attempt_id,
    file_accessed: true,
    actor: { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE },
    policy_sha256: admission.policy_sha256,
    facade_contract: { ...admission.facade_contract },
    runtime_identity: {
      activation_epoch_id: 'activation-control-plane-0001',
      process_instance_id: 'process-control-plane-0001',
      server_instance_id: 'server-control-plane-0001',
      tool_contract_sha256: 'a'.repeat(64)
    },
    file,
    response_sha256: digest(file)
  };
}

test('bounded file-read policy defaults off and an exact registered root is required', (t) => {
  const item = fixture(t);
  assert.throws(
    () => loadFileReadBridgePolicy(item.paths, { now: NOW }),
    { code: 'CONTROL_PLANE_FILE_READ_POLICY_MISSING' }
  );

  fs.writeFileSync(item.policyFile, JSON.stringify(policy()), 'utf8');
  const loaded = loadFileReadBridgePolicy(item.paths, { now: NOW });
  assert.throws(
    () => resolveRegisteredWorkspaceRoot(item.paths, loaded),
    { code: 'CONTROL_PLANE_FILE_READ_WORKSPACE_REGISTRY_REQUIRED' }
  );
  writeRegistry(item.paths, item.root);
  assert.equal(resolveRegisteredWorkspaceRoot(item.paths, loaded), fs.realpathSync.native(item.root));
});

test('standing file-read policy remains valid after the former TTL window', (t) => {
  const item = fixture(t);
  const standing = policy();
  standing.schema_version = 2;
  standing.authority_mode = 'standing';
  standing.expires_at_ms = null;
  fs.writeFileSync(item.policyFile, JSON.stringify(standing), 'utf8');
  const loaded = loadFileReadBridgePolicy(item.paths, { now: NOW + (10 * 365 * 24 * 60 * 60 * 1000) });
  assert.equal(loaded.schema_version, 2);
  assert.equal(loaded.authority_mode, 'standing');
  assert.equal(loaded.expires_at_ms, null);
});

test('bounded file-read admits only the exact local owner, target, contract, path and limits', (t) => {
  const item = fixture(t);
  fs.writeFileSync(item.policyFile, JSON.stringify(policy()), 'utf8');
  writeRegistry(item.paths, item.root);
  const loaded = loadFileReadBridgePolicy(item.paths, { now: NOW });
  const admitted = admitFileReadBridgeRequest(loaded, request(), { now: NOW });
  assert.equal(admitted.operation_kind, 'control_plane_bounded_file_read');
  assert.equal(admitted.policy_sha256, loaded.policy_sha256);
  assert.equal(admitted.actor.client_id, BRIDGE_CLIENT_ID);
  assert.equal(admitted.actor.client_type, BRIDGE_CLIENT_TYPE);

  const wrongDevice = request();
  wrongDevice.device_id = 'device-other-control-plane-0001';
  assert.throws(
    () => admitFileReadBridgeRequest(loaded, wrongDevice, { now: NOW }),
    { code: 'CONTROL_PLANE_FILE_READ_TARGET_MISMATCH' }
  );

  const wrongPath = request();
  wrongPath.path = '.env';
  assert.throws(
    () => admitFileReadBridgeRequest(loaded, wrongPath, { now: NOW }),
    { code: 'CONTROL_PLANE_FILE_READ_SENSITIVE_PATH' }
  );

  const wrongContract = request();
  wrongContract.facade_contract.sha256 = '0'.repeat(64);
  assert.throws(
    () => admitFileReadBridgeRequest(loaded, wrongContract, { now: NOW }),
    { code: 'CONTROL_PLANE_FILE_READ_CONTRACT_MISMATCH' }
  );
});

test('bounded file-read rejects sensitive content and any receipt policy/digest drift before relay', (t) => {
  const item = fixture(t);
  fs.writeFileSync(item.policyFile, JSON.stringify(policy()), 'utf8');
  const admission = admitFileReadBridgeRequest(loadFileReadBridgePolicy(item.paths, { now: NOW }), request(), { now: NOW });

  const good = normaliseFileReadResult(safeResult(admission), admission);
  assert.equal(good.file.content, 'line one\nline two\n');

  const secret = safeResult(admission, 'token = sk-example-secret-value-123456789\n');
  assert.throws(
    () => normaliseFileReadResult(secret, admission),
    { code: 'CONTROL_PLANE_FILE_READ_SENSITIVE_CONTENT' }
  );

  const policyDrift = safeResult(admission);
  policyDrift.policy_sha256 = '0'.repeat(64);
  assert.throws(
    () => normaliseFileReadResult(policyDrift, admission),
    { code: 'CONTROL_PLANE_FILE_READ_RESULT_ENVELOPE_INVALID' }
  );

  const digestDrift = safeResult(admission);
  digestDrift.response_sha256 = '0'.repeat(64);
  assert.throws(
    () => normaliseFileReadResult(digestDrift, admission),
    { code: 'CONTROL_PLANE_FILE_READ_RESULT_DIGEST_INVALID' }
  );
});
