'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { RecoveryHost } = require('../electron/services/recoveryHost');

const {
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE,
  admitFileReadBridgeRequest,
  digest,
  fileContentDigest,
  loadFileReadBridgePolicy,
  normaliseFileReadResult,
  resolveDirectRegisteredFile,
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

test('Recovery Host attests a missing target only before bounded read dispatch', async (t) => {
  const item = fixture(t);
  const now = Date.now();
  fs.writeFileSync(item.policyFile, JSON.stringify(policy(now)), 'utf8');
  writeRegistry(item.paths, item.root);
  const host = Object.create(RecoveryHost.prototype);
  host.paths = item.paths;
  host.deviceIdentity = { device_id: 'device-control-plane-0001' };
  let dispatched = false;
  host.orchestrator = {
    lightweightSnapshot: async () => { dispatched = true; throw new Error('runtime must not be reached'); },
    controlPlaneBoundedFileRead: async () => { dispatched = true; throw new Error('read must not be reached'); }
  };
  await assert.rejects(host.controlPlaneBoundedFileRead(request(now)), {
    code: 'CONTROL_PLANE_FILE_READ_TARGET_MISSING_BEFORE_DISPATCH'
  });
  assert.equal(dispatched, false);
  assert.throws(() => resolveDirectRegisteredFile(item.root, 'fixture.txt'), {
    code: 'CONTROL_PLANE_FILE_READ_TARGET_MISSING'
  });
});

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
      server_instance_id: '_server-control-plane-0001',
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

test('workspace prefix file-read policy admits exact nested files and fences unsafe paths', (t) => {
  const item = fixture(t);
  const scoped = policy();
  scoped.schema_version = 3;
  scoped.authority_mode = 'standing';
  scoped.expires_at_ms = null;
  delete scoped.allowed_relative_paths;
  scoped.allowed_relative_prefixes = ['.'];
  fs.writeFileSync(item.policyFile, JSON.stringify(scoped), 'utf8');
  writeRegistry(item.paths, item.root);
  const nested = path.join(item.root, 'src', 'deep');
  fs.mkdirSync(nested, { recursive: true });
  fs.writeFileSync(path.join(nested, 'fixture.txt'), 'safe\n', 'utf8');
  const loaded = loadFileReadBridgePolicy(item.paths, { now: NOW });
  assert.equal(loaded.schema_version, 3);
  const wanted = { ...request(), path: 'src/deep/fixture.txt' };
  assert.equal(admitFileReadBridgeRequest(loaded, wanted, { now: NOW }).path, wanted.path);
  assert.equal(resolveDirectRegisteredFile(item.root, wanted.path), path.join(nested, 'fixture.txt'));
  for (const denied of ['../outside.txt', 'src/.env', 'src/.git/config', '/tmp/outside.txt']) {
    assert.throws(() => admitFileReadBridgeRequest(loaded, { ...wanted, path: denied }, { now: NOW }));
  }
  fs.writeFileSync(item.policyFile, JSON.stringify({
    ...scoped, allowed_relative_paths: ['src/deep/fixture.txt']
  }), 'utf8');
  assert.throws(() => loadFileReadBridgePolicy(item.paths, { now: NOW }),
    { code: 'CONTROL_PLANE_FILE_READ_POLICY_INVALID' });
  fs.writeFileSync(item.policyFile, JSON.stringify({
    ...scoped, allowed_relative_prefixes: ['src']
  }), 'utf8');
  const narrowed = loadFileReadBridgePolicy(item.paths, { now: NOW });
  assert.equal(admitFileReadBridgeRequest(narrowed, wanted, { now: NOW }).path, wanted.path);
  assert.throws(() => admitFileReadBridgeRequest(narrowed,
    { ...wanted, path: 'src2/deep/fixture.txt' }, { now: NOW }),
  { code: 'CONTROL_PLANE_FILE_READ_PATH_DENIED' });
  const exact = { ...scoped, schema_version: 2, allowed_relative_paths: ['fixture.txt'] };
  delete exact.allowed_relative_prefixes;
  fs.writeFileSync(item.policyFile, JSON.stringify(exact), 'utf8');
  assert.throws(() => admitFileReadBridgeRequest(
    loadFileReadBridgePolicy(item.paths, { now: NOW }), wanted, { now: NOW }
  ), { code: 'CONTROL_PLANE_FILE_READ_PATH_DENIED' });
  const outside = path.join(path.dirname(item.root), 'outside');
  fs.mkdirSync(outside);
  fs.writeFileSync(path.join(outside, 'file.txt'), 'outside\n', 'utf8');
  fs.symlinkSync(outside, path.join(item.root, 'linked'), process.platform === 'win32' ? 'junction' : 'dir');
  assert.throws(() => resolveDirectRegisteredFile(item.root, 'linked/file.txt'),
    { code: 'CONTROL_PLANE_FILE_READ_REPARSE_DENIED' });
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
  assert.equal(good.runtime_identity.server_instance_id, '_server-control-plane-0001');

  const invalidIdentity = safeResult(admission);
  invalidIdentity.runtime_identity.server_instance_id = 'invalid identity';
  assert.throws(
    () => normaliseFileReadResult(invalidIdentity, admission),
    { code: 'CONTROL_PLANE_FILE_READ_RESULT_IDENTITY_INVALID' }
  );

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
