'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const zlib = require('node:zlib');

const {
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE,
  admitApprovedPatchBridgeRequest,
  digest,
  loadApprovedPatchBridgePolicy,
  normaliseApprovedPatchWorkflowResult,
  normaliseApprovedPatchResult,
  resolveExactRegisteredPatchTarget,
  resolveRegisteredWorkspaceRoot
} = require('../electron/services/controlPlaneApprovedPatchBridge');

const NOW = 1_700_000_000_000;
const FACADE_CONTRACT = Object.freeze({
  schema_version: 10,
  profile: 'control-plane-oauth-approved-patch-v1',
  sha256: 'f'.repeat(64)
});

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function fixture(t) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-approved-patch-'));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  const root = path.join(directory, 'workspace');
  fs.mkdirSync(root);
  const policyFile = path.join(directory, 'approved-patch-policy.json');
  const registryFile = path.join(directory, 'workspace-registry.json');
  return {
    root,
    policyFile,
    registryFile,
    paths: {
      controlPlaneApprovedPatchPolicyFile: () => policyFile,
      controlPlaneWorkspaceRegistryFile: () => registryFile
    }
  };
}

function patch(pathValue, before, after) {
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
  return { envelope, preimage, postimage, patch_sha256: sha256(Buffer.from(envelope, 'utf8')), bytes: Buffer.byteLength(after, 'utf8') };
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
    max_patch_bytes: 4096,
    max_file_bytes: 4096,
    validation_profile: 'targeted'
  };
}

function request(now = NOW, source = 'before\n', output = 'after\n') {
  const exact = patch('fixture.txt', source, output);
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
    tool_name: 'agent_workflow',
    operation: 'apply_patch',
    permission_request_id: 'permission-control-plane-0001',
    permission_digest: 'a'.repeat(64),
    intent_digest: 'b'.repeat(64),
    path: 'fixture.txt',
    preimage_sha256: exact.preimage,
    patch_sha256: exact.patch_sha256,
    patch_envelope: exact.envelope,
    validation_profile: 'targeted',
    expires_at_ms: now + 30_000,
    facade_contract: { ...FACADE_CONTRACT },
    _fixture: exact
  };
}

function transportRequest(value) {
  const { _fixture, ...requestValue } = value;
  return requestValue;
}

function writeRegistry(paths, root) {
  fs.writeFileSync(paths.controlPlaneWorkspaceRegistryFile(), JSON.stringify({
    schema_version: 1,
    entries: [{
      workspace_id: 'workspace-control-plane-0001',
      workspace_generation: 'generation-control-plane-0001',
      canonical_path: root,
      display_name: 'Fixture root',
      capabilities: { read: true, write: true, exec: false },
      created_at_ms: NOW
    }]
  }), 'utf8');
}

function safeResult(admission) {
  const file = {
    path: admission.path,
    preimage_sha256: admission.preimage_sha256,
    postimage_sha256: admission.postimage_sha256,
    bytes_written: admission.postimage_bytes
  };
  return {
    schema_version: 1,
    operation_kind: 'control_plane_approved_patch',
    local_handle: `cp_ap_${'a'.repeat(48)}`,
    action_id: admission.action_id,
    attempt_id: admission.attempt_id,
    task_id: admission.task_id,
    writer_lease_generation: admission.writer_lease_generation,
    run_id: '1'.repeat(32),
    wave_id: '2'.repeat(32),
    patch_applied: true,
    local_semantic_acceptance: 'pending',
    actor: { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE },
    policy_sha256: admission.policy_sha256,
    facade_contract: { ...admission.facade_contract },
    runtime_identity: {
      activation_epoch_id: 'activation-control-plane-0001',
      process_instance_id: 'process-control-plane-0001',
      server_instance_id: 'server-control-plane-0001',
      tool_contract_sha256: 'd'.repeat(64)
    },
    file,
    response_sha256: digest(file)
  };
}

function workflowResult(pathValue, idempotencyKey, {
  runId = '1'.repeat(32),
  waveId = '2'.repeat(32),
  requestHash = '3'.repeat(64)
} = {}) {
  const affectedFiles = [{ path: pathValue, operation: 'update' }];
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
    orchestration: { run_id: runId, wave_id: waveId, orchestration_state: 'ACCEPTING' },
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

test('approved-patch policy defaults closed and requires an exact writable registered root', (t) => {
  const item = fixture(t);
  assert.throws(
    () => loadApprovedPatchBridgePolicy(item.paths, { now: NOW }),
    { code: 'CONTROL_PLANE_APPROVED_PATCH_POLICY_MISSING' }
  );

  fs.writeFileSync(item.policyFile, JSON.stringify(policy()), 'utf8');
  const loaded = loadApprovedPatchBridgePolicy(item.paths, { now: NOW });
  assert.throws(
    () => resolveRegisteredWorkspaceRoot(item.paths, loaded),
    { code: 'CONTROL_PLANE_APPROVED_PATCH_WORKSPACE_REGISTRY_REQUIRED' }
  );
  writeRegistry(item.paths, item.root);
  assert.equal(resolveRegisteredWorkspaceRoot(item.paths, loaded), fs.realpathSync.native(item.root));
});

test('standing approved-patch policy remains valid after the former TTL window', (t) => {
  const item = fixture(t);
  const standing = policy();
  standing.schema_version = 2;
  standing.authority_mode = 'standing';
  standing.expires_at_ms = null;
  fs.writeFileSync(item.policyFile, JSON.stringify(standing), 'utf8');
  const loaded = loadApprovedPatchBridgePolicy(item.paths, { now: NOW + (10 * 365 * 24 * 60 * 60 * 1000) });
  assert.equal(loaded.schema_version, 2);
  assert.equal(loaded.authority_mode, 'standing');
  assert.equal(loaded.expires_at_ms, null);
});

test('approved-patch admits only an exact approved envelope, local target and contract', (t) => {
  const item = fixture(t);
  fs.writeFileSync(item.policyFile, JSON.stringify(policy()), 'utf8');
  writeRegistry(item.paths, item.root);
  const loaded = loadApprovedPatchBridgePolicy(item.paths, { now: NOW });
  const source = request();
  const admitted = admitApprovedPatchBridgeRequest(loaded, transportRequest(source), { now: NOW });
  assert.equal(admitted.operation_kind, 'control_plane_approved_patch');
  assert.equal(admitted.postimage_sha256, source._fixture.postimage);
  assert.equal(admitted.postimage_bytes, source._fixture.bytes);
  assert.equal(admitted.policy_sha256, loaded.policy_sha256);
  assert.equal(admitted.actor.client_id, BRIDGE_CLIENT_ID);
  assert.equal(admitted.actor.client_type, BRIDGE_CLIENT_TYPE);

  const wrongDevice = transportRequest(request());
  wrongDevice.device_id = 'device-other-control-plane-0001';
  assert.throws(
    () => admitApprovedPatchBridgeRequest(loaded, wrongDevice, { now: NOW }),
    { code: 'CONTROL_PLANE_APPROVED_PATCH_TARGET_MISMATCH' }
  );

  const wrongContract = transportRequest(request());
  wrongContract.facade_contract.sha256 = '0'.repeat(64);
  assert.throws(
    () => admitApprovedPatchBridgeRequest(loaded, wrongContract, { now: NOW }),
    { code: 'CONTROL_PLANE_APPROVED_PATCH_CONTRACT_MISMATCH' }
  );

  const multiFile = transportRequest(request());
  multiFile.patch_envelope = `${multiFile.patch_envelope.replace('*** End Patch', '*** Add File: second.txt\n+x\n*** End Patch')}`;
  multiFile.patch_sha256 = sha256(Buffer.from(multiFile.patch_envelope, 'utf8'));
  assert.throws(
    () => admitApprovedPatchBridgeRequest(loaded, multiFile, { now: NOW }),
    { code: 'CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID' }
  );
});

test('approved-patch rechecks a direct registered file and rejects stale or reparse targets before local MCP', (t) => {
  const item = fixture(t);
  fs.writeFileSync(item.policyFile, JSON.stringify(policy()), 'utf8');
  writeRegistry(item.paths, item.root);
  const target = path.join(item.root, 'fixture.txt');
  fs.writeFileSync(target, 'before\n', 'utf8');
  const loaded = loadApprovedPatchBridgePolicy(item.paths, { now: NOW });
  const admitted = admitApprovedPatchBridgeRequest(loaded, transportRequest(request()), { now: NOW });
  const resolved = resolveExactRegisteredPatchTarget(resolveRegisteredWorkspaceRoot(item.paths, loaded), admitted);
  assert.equal(resolved.preimage_sha256, admitted.preimage_sha256);
  assert.equal(resolved.postimage_sha256, admitted.postimage_sha256);

  fs.writeFileSync(target, 'changed by user\n', 'utf8');
  assert.throws(
    () => resolveExactRegisteredPatchTarget(resolveRegisteredWorkspaceRoot(item.paths, loaded), admitted),
    { code: 'CONTROL_PLANE_APPROVED_PATCH_PREIMAGE_MISMATCH' }
  );

  if (process.platform !== 'win32') {
    const outside = path.join(path.dirname(item.root), 'outside.txt');
    fs.writeFileSync(outside, 'before\n', 'utf8');
    fs.rmSync(target);
    fs.symlinkSync(outside, target);
    assert.throws(
      () => resolveExactRegisteredPatchTarget(resolveRegisteredWorkspaceRoot(item.paths, loaded), admitted),
      { code: 'CONTROL_PLANE_APPROVED_PATCH_REPARSE_DENIED' }
    );
  }
});

test('approved-patch allowlists the completed receipt and never returns patch bytes', (t) => {
  const item = fixture(t);
  fs.writeFileSync(item.policyFile, JSON.stringify(policy()), 'utf8');
  const loaded = loadApprovedPatchBridgePolicy(item.paths, { now: NOW });
  const source = request();
  const admitted = admitApprovedPatchBridgeRequest(loaded, transportRequest(source), { now: NOW });
  const good = normaliseApprovedPatchResult(safeResult(admitted), admitted);
  assert.equal(good.file.path, 'fixture.txt');
  assert.equal(Object.hasOwn(good, 'patch_envelope'), false);
  assert.equal(JSON.stringify(good).includes(source._fixture.envelope), false);

  const digestDrift = safeResult(admitted);
  digestDrift.response_sha256 = '0'.repeat(64);
  assert.throws(
    () => normaliseApprovedPatchResult(digestDrift, admitted),
    { code: 'CONTROL_PLANE_APPROVED_PATCH_RESULT_DIGEST_INVALID' }
  );

  const postimageDrift = safeResult(admitted);
  postimageDrift.file.postimage_sha256 = '0'.repeat(64);
  postimageDrift.response_sha256 = digest(postimageDrift.file);
  assert.throws(
    () => normaliseApprovedPatchResult(postimageDrift, admitted),
    { code: 'CONTROL_PLANE_APPROVED_PATCH_RESULT_FILE_INVALID' }
  );

  const selfAccepted = safeResult(admitted);
  selfAccepted.local_semantic_acceptance = 'accepted';
  assert.throws(
    () => normaliseApprovedPatchResult(selfAccepted, admitted),
    { code: 'CONTROL_PLANE_APPROVED_PATCH_RESULT_ENVELOPE_INVALID' }
  );
});

test('approved-patch binds its opaque receipt to canonical agent-workflow RUN/WAVE correlation', () => {
  const idempotencyKey = `cpap_${'a'.repeat(56)}`;
  const localWorkflow = workflowResult('fixture.txt', idempotencyKey);
  const correlation = normaliseApprovedPatchWorkflowResult(localWorkflow, {
    path: 'fixture.txt',
    idempotency_key: idempotencyKey
  });
  assert.deepEqual(correlation, {
    run_id: '1'.repeat(32),
    wave_id: '2'.repeat(32),
    idempotency_request_hash: '3'.repeat(64),
    local_semantic_acceptance: 'pending',
    deduplicated: false
  });

  const replay = workflowResult('fixture.txt', idempotencyKey);
  replay.deduplicated = true;
  delete replay.execution;
  delete replay.orchestration;
  assert.deepEqual(normaliseApprovedPatchWorkflowResult(replay, {
    path: 'fixture.txt',
    idempotency_key: idempotencyKey
  }), {
    run_id: '1'.repeat(32),
    wave_id: '2'.repeat(32),
    idempotency_request_hash: '3'.repeat(64),
    local_semantic_acceptance: 'pending',
    deduplicated: true
  });

  const mismatchedRun = workflowResult('fixture.txt', idempotencyKey);
  mismatchedRun.orchestration.run_id = '4'.repeat(32);
  assert.throws(
    () => normaliseApprovedPatchWorkflowResult(mismatchedRun, {
      path: 'fixture.txt',
      idempotency_key: idempotencyKey
    }),
    { code: 'CONTROL_PLANE_APPROVED_PATCH_MCP_RESULT_INVALID' }
  );
});
