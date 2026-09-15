const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { createRuntimePaths } = require('../electron/services/runtimePaths');
const {
  BRIDGE_CLIENT_ID,
  BRIDGE_CLIENT_TYPE,
  READ_ONLY_ARGUMENTS,
  POLICY_SCHEMA_VERSION,
  loadReadOnlyBridgePolicy,
  admitReadOnlyBridgeRequest
} = require('../electron/services/controlPlaneReadOnlyBridge');

const FACADE_CONTRACT = Object.freeze({
  schema_version: 3,
  profile: 'control-plane-read-only-queue-v2',
  sha256: 'f'.repeat(64)
});

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-control-plane-bridge-'));
  const dataRoot = path.join(root, 'data');
  const resourcesRoot = path.join(root, 'resources');
  const appRoot = path.join(root, 'app');
  fs.mkdirSync(dataRoot, { recursive: true });
  fs.mkdirSync(resourcesRoot, { recursive: true });
  fs.mkdirSync(appRoot, { recursive: true });
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return createRuntimePaths({ dataRoot, resourcesRoot, appRoot });
}

function policy(now = 1_700_000_000_000) {
  return {
    schema_version: POLICY_SCHEMA_VERSION,
    enabled: true,
    server_origin: 'http://100.116.112.22:8765',
    owner_id: 'owner-default',
    device_id: 'device-control-plane-0001',
    endpoint_id: 'endpoint-control-plane-0001',
    workspace_id: 'workspace-control-plane-0001',
    workspace_generation: 'generation-control-plane-0001',
    expires_at_ms: now + 60_000,
    facade_contract: { ...FACADE_CONTRACT }
  };
}

function request(now = 1_700_000_000_000) {
  return {
    server_origin: 'http://100.116.112.22:8765',
    owner_id: 'owner-default',
    device_id: 'device-control-plane-0001',
    endpoint_id: 'endpoint-control-plane-0001',
    workspace_id: 'workspace-control-plane-0001',
    workspace_generation: 'generation-control-plane-0001',
    context_id: 'context-control-plane-0001',
    binding_id: 'binding-control-plane-0001',
    action_id: 'action-control-plane-0001',
    attempt_id: 'attempt-control-plane-0001',
    tool_name: 'workspace_context',
    arguments: { ...READ_ONLY_ARGUMENTS },
    expires_at_ms: now + 30_000,
    facade_contract: { ...FACADE_CONTRACT }
  };
}

test('read-only control-plane bridge defaults off without an installed local policy', (t) => {
  const paths = fixture(t);
  assert.throws(
    () => loadReadOnlyBridgePolicy(paths, { now: 1_700_000_000_000 }),
    { code: 'CONTROL_PLANE_BRIDGE_POLICY_MISSING' }
  );
});

test('read-only control-plane bridge binds an exact target and compact workspace request', (t) => {
  const paths = fixture(t);
  const now = 1_700_000_000_000;
  fs.writeFileSync(paths.controlPlaneReadOnlyPolicyFile(), JSON.stringify(policy(now)), 'utf8');
  const loaded = loadReadOnlyBridgePolicy(paths, { now });
  const admitted = admitReadOnlyBridgeRequest(loaded, request(now), { now });

  assert.equal(admitted.policy_sha256, loaded.policy_sha256);
  assert.equal(admitted.actor.client_id, BRIDGE_CLIENT_ID);
  assert.equal(admitted.actor.client_type, BRIDGE_CLIENT_TYPE);
  assert.deepEqual(admitted.arguments, READ_ONLY_ARGUMENTS);
  assert.deepEqual(admitted.facade_contract, FACADE_CONTRACT);
  assert.equal(admitted.operation_kind, 'control_plane_read_only_workspace_context');
});

test('read-only control-plane bridge rejects expired authority, target drift, and generic arguments', (t) => {
  const paths = fixture(t);
  const now = 1_700_000_000_000;
  fs.writeFileSync(paths.controlPlaneReadOnlyPolicyFile(), JSON.stringify(policy(now)), 'utf8');
  const loaded = loadReadOnlyBridgePolicy(paths, { now });

  const wrongTarget = request(now);
  wrongTarget.workspace_generation = 'generation-other-target-0001';
  assert.throws(
    () => admitReadOnlyBridgeRequest(loaded, wrongTarget, { now }),
    { code: 'CONTROL_PLANE_BRIDGE_TARGET_MISMATCH' }
  );

  const genericArguments = request(now);
  genericArguments.arguments = { detail: 'compact', max_entries: 1, path: 'E:/outside-scope' };
  assert.throws(
    () => admitReadOnlyBridgeRequest(loaded, genericArguments, { now }),
    { code: 'CONTROL_PLANE_BRIDGE_TOOL_DENIED' }
  );

  const expired = request(now);
  expired.expires_at_ms = now;
  assert.throws(
    () => admitReadOnlyBridgeRequest(loaded, expired, { now }),
    { code: 'CONTROL_PLANE_BRIDGE_REQUEST_EXPIRED' }
  );

  const contractMismatch = request(now);
  contractMismatch.facade_contract.sha256 = 'e'.repeat(64);
  assert.throws(
    () => admitReadOnlyBridgeRequest(loaded, contractMismatch, { now }),
    { code: 'CONTROL_PLANE_BRIDGE_CONTRACT_MISMATCH' }
  );
});
