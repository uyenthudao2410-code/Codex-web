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
  admitExecBridgeRequest,
  digest,
  loadExecBridgePolicy,
  normaliseExecResult,
  resolveRegisteredWorkspaceRoot
} = require('../electron/services/controlPlaneExecBridge');

const NOW = 1_700_000_000_000;
const FACADE_CONTRACT = {
  schema_version: 14,
  profile: 'control-plane-oauth-bounded-exec-v1',
  sha256: 'f'.repeat(64)
};

test('workspace collection selects exact generation and never shares native script approval', (t) => {
  const item = fixture(t);
  const first = { ...policy(), allowed_argv_prefixes: [['node', '--version'], ['node', 'trusted.js']], native_argv_prefixes: [['node', 'trusted.js']] };
  const second = { ...first, workspace_id: 'workspace-control-plane-0002', workspace_generation: 'generation-control-plane-0002', allowed_argv_prefixes: [['node', '--version']], native_argv_prefixes: [] };
  fs.writeFileSync(item.policyFile, JSON.stringify({ schema_version: 1, policies: [first, second] }));
  const loadedFirst = loadExecBridgePolicy(item.paths, { now: NOW, target: first });
  const loadedSecond = loadExecBridgePolicy(item.paths, { now: NOW, target: second });
  assert.deepEqual(loadedFirst.native_argv_prefixes, [['node', 'trusted.js']]);
  assert.deepEqual(loadedSecond.native_argv_prefixes, []);
  assert.throws(() => loadExecBridgePolicy(item.paths, { now: NOW }), { code: 'CONTROL_PLANE_EXEC_POLICY_INVALID' });
  assert.throws(() => loadExecBridgePolicy(item.paths, { now: NOW, target: { ...second, workspace_generation: 'generation-retired-0002' } }), { code: 'CONTROL_PLANE_EXEC_POLICY_INVALID' });
  const action = { ...request(), argv: ['node', 'trusted.js'], cwd: '' };
  assert.deepEqual(admitExecBridgeRequest(loadedFirst, action, { now: NOW }).native_argv_prefixes, [['node', 'trusted.js']]);
  assert.throws(() => admitExecBridgeRequest(loadedSecond, { ...action, workspace_id: second.workspace_id, workspace_generation: second.workspace_generation }, { now: NOW }), { code: 'CONTROL_PLANE_EXEC_ALLOWLIST_DENIED' });
});

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-exec-bridge-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const workspace = path.join(root, 'workspace');
  fs.mkdirSync(workspace);
  const policyFile = path.join(root, 'exec-policy.json');
  const registryFile = path.join(root, 'workspace-registry.json');
  const paths = {
    controlPlaneExecPolicyFile: () => policyFile,
    controlPlaneWorkspaceRegistryFile: () => registryFile
  };
  return { root, workspace, policyFile, registryFile, paths };
}

function policy() {
  return {
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
    facade_contract: { ...FACADE_CONTRACT },
    allowed_argv_prefixes: [['python', '-m', 'pytest'], ['npm', 'test']],
    max_timeout_ms: 60_000,
    max_output_bytes: 32_768,
    max_concurrent: 2
  };
}

function request(expiresAtMs = NOW + 30_000) {
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
    tool_name: 'exec_command',
    operation: 'exec_run',
    argv: ['python', '-m', 'pytest', '-q'],
    cwd: 'tests',
    timeout_ms: 30_000,
    max_output_bytes: 16_384,
    expires_at_ms: expiresAtMs,
    facade_contract: { ...FACADE_CONTRACT },
    command_id: null,
    job_id: null,
    local_handle: null,
    consumer_id: null,
    yield_time_ms: null,
    signal: null,
    wait_ms: null,
    run_id: null,
    wave_id: null
  };
}

function writeRegistry(item, exec = true) {
  fs.writeFileSync(item.registryFile, JSON.stringify({
    schema_version: 1,
    entries: [{
      workspace_id: 'workspace-control-plane-0001',
      workspace_generation: 'generation-control-plane-0001',
      canonical_path: item.workspace,
      display_name: 'Exec fixture',
      capabilities: { read: true, write: true, exec },
      created_at_ms: NOW
    }]
  }), 'utf8');
}

function safeResult(admitted) {
  const output = {
    status: 'exited',
    exit_code: 0,
    stdout: 'ok\n',
    stderr: '',
    truncated: false,
    timed_out: false,
    command_id: 'command-control-plane-0001',
    job_id: 'job-control-plane-0001',
    run_id: '',
    wave_id: '',
    output_refs: null
  };
  return {
    schema_version: 1,
    operation_kind: 'control_plane_exec',
    local_handle: `cp_exec_${'a'.repeat(48)}`,
    action_id: admitted.action_id,
    attempt_id: admitted.attempt_id,
    task_id: admitted.task_id,
    writer_lease_generation: admitted.writer_lease_generation,
    policy_sha256: admitted.policy_sha256,
    actor: { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE },
    facade_contract: { ...admitted.facade_contract },
    runtime_identity: {
      activation_epoch_id: 'activation-control-plane-0001',
      process_instance_id: 'process-control-plane-0001',
      server_instance_id: '_server-control-plane-0001',
      tool_contract_sha256: 'd'.repeat(64)
    },
    ...output,
    response_sha256: digest(output)
  };
}

test('exec policy is default-deny and requires an exact registered executable workspace', (t) => {
  const item = fixture(t);
  assert.throws(() => loadExecBridgePolicy(item.paths, { now: NOW }), { code: 'CONTROL_PLANE_EXEC_POLICY_MISSING' });
  fs.writeFileSync(item.policyFile, JSON.stringify(policy()), 'utf8');
  const loaded = loadExecBridgePolicy(item.paths, { now: NOW });
  assert.equal(loaded.max_concurrent, 2);
  assert.throws(() => resolveRegisteredWorkspaceRoot(item.paths, loaded), { code: 'CONTROL_PLANE_EXEC_WORKSPACE_REGISTRY_REQUIRED' });
  writeRegistry(item);
  assert.equal(resolveRegisteredWorkspaceRoot(item.paths, loaded), fs.realpathSync.native(item.workspace));
  writeRegistry(item, false);
  assert.throws(() => resolveRegisteredWorkspaceRoot(item.paths, loaded), { code: 'CONTROL_PLANE_EXEC_WORKSPACE_REGISTRY_REQUIRED' });
});

test('standing exec policy remains valid after the former TTL window', (t) => {
  const item = fixture(t);
  fs.writeFileSync(item.policyFile, JSON.stringify(policy()), 'utf8');
  const loaded = loadExecBridgePolicy(item.paths, { now: NOW + (10 * 365 * 24 * 60 * 60 * 1000) });
  assert.equal(loaded.authority_mode, 'standing');
  assert.equal(loaded.expires_at_ms, null);
});

test('legacy expiring exec policy remains compatibility-only and still expires', (t) => {
  const item = fixture(t);
  const legacy = policy();
  legacy.schema_version = 1;
  delete legacy.authority_mode;
  legacy.expires_at_ms = NOW + 60_000;
  fs.writeFileSync(item.policyFile, JSON.stringify(legacy), 'utf8');
  const loaded = loadExecBridgePolicy(item.paths, { now: NOW });
  assert.equal(loaded.authority_mode, 'expiring_legacy');
  assert.throws(
    () => loadExecBridgePolicy(item.paths, { now: NOW + 120_000 }),
    { code: 'CONTROL_PLANE_EXEC_POLICY_EXPIRED' }
  );
});

test('exec admission binds account/device/endpoint/workspace, lease and argv allowlist', (t) => {
  const item = fixture(t);
  fs.writeFileSync(item.policyFile, JSON.stringify(policy()), 'utf8');
  writeRegistry(item);
  const loaded = loadExecBridgePolicy(item.paths, { now: NOW });
  const admitted = admitExecBridgeRequest(loaded, request(), { now: NOW });
  assert.equal(admitted.operation_kind, 'control_plane_exec');
  assert.equal(admitted.policy_sha256, loaded.policy_sha256);
  assert.deepEqual(admitted.actor, { client_id: BRIDGE_CLIENT_ID, client_type: BRIDGE_CLIENT_TYPE });
  const wrongDevice = request();
  wrongDevice.device_id = 'device-other-control-plane-0001';
  assert.throws(() => admitExecBridgeRequest(loaded, wrongDevice, { now: NOW }), { code: 'CONTROL_PLANE_EXEC_TARGET_MISMATCH' });
  const disallowed = request();
  disallowed.argv = ['python', '-m', 'pip', 'install', 'x'];
  assert.throws(() => admitExecBridgeRequest(loaded, disallowed, { now: NOW }), { code: 'CONTROL_PLANE_EXEC_ALLOWLIST_DENIED' });
});

test('exec result normalization preserves Job identity and rejects digest drift', (t) => {
  const item = fixture(t);
  fs.writeFileSync(item.policyFile, JSON.stringify(policy()), 'utf8');
  writeRegistry(item);
  const admitted = admitExecBridgeRequest(loadExecBridgePolicy(item.paths, { now: NOW }), request(), { now: NOW });
  const result = normaliseExecResult(safeResult(admitted), admitted);
  assert.equal(result.status, 'exited');
  assert.equal(result.command_id, 'command-control-plane-0001');
  assert.equal(result.job_id, 'job-control-plane-0001');
  assert.equal(result.task_id, admitted.task_id);
  const drift = safeResult(admitted);
  drift.stdout = 'tampered\n';
  assert.throws(() => normaliseExecResult(drift, admitted), { code: 'CONTROL_PLANE_EXEC_RESULT_DIGEST_INVALID' });
});

test('native routing is local policy authority and old policy hashes remain stable', (t) => {
  const item = fixture(t);
  const old = policy();
  fs.writeFileSync(item.policyFile, JSON.stringify(old));
  const loaded = loadExecBridgePolicy(item.paths, { now: NOW });
  const oldProjection = { ...old };
  delete oldProjection.enabled;
  assert.equal(loaded.policy_sha256, digest(oldProjection));
  const admitted = admitExecBridgeRequest(loaded, request(), { now: NOW });
  assert.equal(admitted.execution_mode, 'native_first');
  assert.deepEqual(admitted.native_argv_prefixes, []);
  assert.throws(() => admitExecBridgeRequest(loaded, { ...request(), execution_mode: 'native_only' }, { now: NOW }),
    { code: 'CONTROL_PLANE_EXEC_REQUEST_INVALID' });
  const explicit = { ...old, execution_mode: 'native_only', native_argv_prefixes: [['npm', 'test']] };
  fs.writeFileSync(item.policyFile, JSON.stringify(explicit));
  const approved = loadExecBridgePolicy(item.paths, { now: NOW });
  const approvedRequest = admitExecBridgeRequest(approved, request(), { now: NOW });
  assert.equal(approvedRequest.execution_mode, 'native_only');
  assert.deepEqual(approvedRequest.native_argv_prefixes, [['npm', 'test']]);
  assert.notEqual(approved.policy_sha256, loaded.policy_sha256);
  for (const invalid of [null, [['C:/tools/node.exe']], [['npm', 'test'], ['npm', 'test']], [['npm', 'test;whoami']]]) {
    fs.writeFileSync(item.policyFile, JSON.stringify({ ...explicit, native_argv_prefixes: invalid }));
    assert.throws(() => loadExecBridgePolicy(item.paths, { now: NOW }), { code: 'CONTROL_PLANE_EXEC_POLICY_INVALID' });
  }
});

test('exec metadata is all-or-none, constrained and bound to the result digest', (t) => {
  const item = fixture(t);
  fs.writeFileSync(item.policyFile, JSON.stringify(policy()));
  const admitted = admitExecBridgeRequest(loadExecBridgePolicy(item.paths, { now: NOW }), request(), { now: NOW });
  const original = safeResult(admitted);
  assert.equal(Object.hasOwn(normaliseExecResult(original, admitted), 'execution_backend'), false);
  for (const metadata of [
    { execution_backend: 'native', isolation_level: 'process_container', policy_decision: 'native_safe_command' },
    { execution_backend: 'native', isolation_level: 'process_container', policy_decision: 'native_explicit_approval' },
    { execution_backend: 'isolated', isolation_level: 'hypervisor', policy_decision: 'isolated_unapproved_command' },
    { execution_backend: 'isolated', isolation_level: 'hypervisor', policy_decision: 'isolated_preferred' }
  ]) {
    const output = Object.fromEntries(['status', 'exit_code', 'stdout', 'stderr', 'truncated', 'timed_out',
      'command_id', 'job_id', 'run_id', 'wave_id', 'output_refs'].map((key) => [key, original[key]]));
    const value = { ...original, ...metadata, response_sha256: digest({ ...output, ...metadata }) };
    assert.equal(normaliseExecResult(value, admitted).policy_decision, metadata.policy_decision);
    assert.throws(() => normaliseExecResult({ ...value, response_sha256: original.response_sha256 }, admitted),
      { code: 'CONTROL_PLANE_EXEC_RESULT_DIGEST_INVALID' });
  }
  for (const metadata of [
    { execution_backend: 'native' },
    { execution_backend: 'native', isolation_level: 'hypervisor', policy_decision: 'native_safe_command' },
    { execution_backend: 'isolated', isolation_level: 'hypervisor', policy_decision: 'native_explicit_approval' }
  ]) assert.throws(() => normaliseExecResult({ ...original, ...metadata }, admitted),
    { code: 'CONTROL_PLANE_EXEC_RESULT_METADATA_INVALID' });
});
