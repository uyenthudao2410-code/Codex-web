'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
  normalisedResult,
  runDevelopmentApprovedPatchBridge
} = require('../control_plane/recovery_approved_patch_bridge.cjs');
const {
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE,
  digest,
  normaliseApprovedPatchResult
} = require('../../electron/services/controlPlaneApprovedPatchBridge');
const { RPC_ACTIONS } = require('../../electron/services/recoveryIpc');

const descriptor = Object.freeze({
  installation_id: 'a'.repeat(64),
  runtime_mode: 'development',
  instance_id: 'recovery-host-approved-patch-0001',
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
  tool_name: 'agent_workflow',
  operation: 'apply_patch',
  permission_request_id: 'permission-control-plane-0001',
  permission_digest: 'a'.repeat(64),
  intent_digest: 'b'.repeat(64),
  path: 'fixture.txt',
  preimage_sha256: 'c'.repeat(64),
  patch_sha256: 'd'.repeat(64),
  patch_envelope: 'raw patch must not return',
  validation_profile: 'targeted',
  expires_at_ms: Date.now() + 60_000,
  max_file_bytes: 4096,
  postimage_sha256: 'e'.repeat(64),
  postimage_bytes: 6,
  facade_contract: {
    schema_version: 10,
    profile: 'control-plane-oauth-approved-patch-v1',
    sha256: 'f'.repeat(64)
  }
});

function safeResult() {
  const file = {
    path: request.path,
    preimage_sha256: request.preimage_sha256,
    postimage_sha256: request.postimage_sha256,
    bytes_written: request.postimage_bytes
  };
  return {
    schema_version: 1,
    operation_kind: 'control_plane_approved_patch',
    action_id: request.action_id,
    attempt_id: request.attempt_id,
    task_id: request.task_id,
    writer_lease_generation: request.writer_lease_generation,
    run_id: '1'.repeat(32),
    wave_id: '2'.repeat(32),
    local_handle: `cp_ap_${'b'.repeat(48)}`,
    patch_applied: true,
    local_semantic_acceptance: 'pending',
    policy_sha256: 'c'.repeat(64),
    actor: { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE },
    runtime_identity: {
      activation_epoch_id: 'activation-approved-patch-0001',
      process_instance_id: 'process-approved-patch-0001',
      server_instance_id: 'server-approved-patch-0001',
      tool_contract_sha256: 'd'.repeat(64)
    },
    facade_contract: { ...request.facade_contract },
    file,
    response_sha256: digest(file)
  };
}

test('approved-patch bridge forwards only the sealed request and strips descriptor and patch secrets', async () => {
  const calls = [];
  const result = await runDevelopmentApprovedPatchBridge(request, {
    appRoot: process.cwd(),
    dependencies: {
      createDevelopmentPaths: () => ({ runtimeIdentity: () => ({ mode: 'development', installation_id: 'a'.repeat(64) }) }),
      loadRecoveryDescriptor: () => descriptor,
      descriptorMatchesInstallation: () => true,
      descriptorRequestOptions: (value) => ({ expectedInstanceId: value.instance_id }),
      clientFactory: () => ({ call: async (...args) => { calls.push(args); return safeResult(); } }),
      approvedPatchBridge: { normaliseApprovedPatchResult }
    }
  });
  assert.deepEqual(calls, [[
    'runtime.control_plane_approved_patch',
    [request],
    { expectedInstanceId: descriptor.instance_id }
  ]]);
  assert.equal(result.patch_applied, true);
  assert.equal(result.local_semantic_acceptance, 'pending');
  assert.equal(result.file.path, 'fixture.txt');
  assert.equal(Object.hasOwn(result, 'patch_envelope'), false);
  assert.equal(JSON.stringify(result).includes('must-not-be-returned'), false);
  assert.equal(JSON.stringify(result).includes(request.patch_envelope), false);
  assert.equal(RPC_ACTIONS.includes('runtime.control_plane_approved_patch'), true);
});

test('approved-patch bridge allowlists its result and refuses a descriptor mismatch before Recovery IPC', async () => {
  const result = normalisedResult(descriptor, { ...safeResult(), workspace_root: 'E:\\private-workspace' }, request, { normaliseApprovedPatchResult });
  assert.equal(Object.hasOwn(result, 'workspace_root'), false);
  assert.equal(JSON.stringify(result).includes('private-workspace'), false);

  let called = false;
  await assert.rejects(
    runDevelopmentApprovedPatchBridge(request, {
      appRoot: process.cwd(),
      dependencies: {
        createDevelopmentPaths: () => ({ runtimeIdentity: () => ({ mode: 'development', installation_id: 'a'.repeat(64) }) }),
        loadRecoveryDescriptor: () => descriptor,
        descriptorMatchesInstallation: () => false,
        descriptorRequestOptions: () => ({}),
        clientFactory: () => ({ call: async () => { called = true; } }),
        approvedPatchBridge: { normaliseApprovedPatchResult }
      }
    }),
    { code: 'RECOVERY_HOST_INSTALLATION_MISMATCH' }
  );
  assert.equal(called, false);
});
