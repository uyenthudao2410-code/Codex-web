const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { collectBootRuntimeObservation, parseArguments, main } = require('../scripts/collect-boot-runtime-observation');
const { buildMcpIdentityObservation } = require('../electron/services/recoveryHost');
const NOW = 1_790_000_000_000;
const workspace = path.resolve('fixture-workspace');
function fixture() {
  const descriptor = { owner_pid: 100, instance_id: 'host-a', owner_process_start_token: '134345400000000001',
    runtime_mode: 'packaged', token: 'secret-marker' };
  const epoch = { activation_epoch_id: 'epoch-a', operation_id: 'op-a', state: 'READY', admission_open: true };
  const status = { pid: 100, instance_id: 'host-a', process_start_token: descriptor.owner_process_start_token,
    snapshot_observed_at_unix_ms: NOW - 100, activation_epoch: epoch, secret: 'secret-marker' };
  const runtime = { device: { workspace, device_id: 'device-a' }, activationEpoch: epoch, executionRole: 'central_executor',
    snapshotObservedAtUnixMs: NOW - 100, telemetryAvailable: true, signalStale: false, snapshotBusy: false, fullyReady: false,
    secret: 'secret-marker' };
  const identity = { observation_schema_version: 1, observation_kind: 'mcp_identity_read_only', observed_at: new Date(NOW).toISOString(),
    recovery_host_instance_id: 'host-a', current_activation_epoch_id: 'epoch-a', activation_epoch_id: 'epoch-a',
    mcp_process_instance_id: 'process-a', mcp_server_instance_id: 'server-a', identity_current: true };
  const calls = [];
  const client = { call: async (action, args, options) => {
    calls.push(action); assert.deepEqual(args, []); assert.equal(options.expectedOwnerPid, 100);
    assert.equal(options.expectedInstanceId, 'host-a'); assert.equal(options.expectedOwnerProcessStartToken, descriptor.owner_process_start_token);
    if (action === 'recovery.status') return status;
    if (action === 'runtime.lightweight_snapshot') return runtime;
    if (action === 'runtime.identity_observation') return identity;
    throw new Error('mutation/unexpected action');
  } };
  return { descriptor, status, runtime, identity, calls, args: { expectedWorkspace: workspace, paths: {}, client,
    readDescriptor: () => descriptor, now: () => NOW } };
}
test('collector uses only exact-bound reads and never invents client proof or readiness', async () => {
  const f = fixture(); const result = await collectBootRuntimeObservation(f.args);
  assert.equal(result.status, 'OBSERVED'); assert.equal(result.runtime.fullyReady, false);
  assert.equal(result.runtime.mcpRunning, null); assert.equal(result.client, null);
  assert.equal(result.live_accepted, false); assert.equal(result.observed_at_ms, NOW - 100);
  assert.deepEqual(f.calls, ['recovery.status', 'runtime.lightweight_snapshot', 'runtime.identity_observation']);
  assert.doesNotMatch(JSON.stringify(result), /secret-marker|fixture-workspace/);
});
test('stale cache is not refreshed by the collector clock', async () => {
  const f = fixture(); f.runtime.snapshotObservedAtUnixMs = NOW - 60_000;
  const r = await collectBootRuntimeObservation(f.args);
  assert.equal(r.status, 'STALE_OR_INCOMPLETE'); assert.equal(r.observed_at_ms, NOW - 60_000);
});
test('missing timestamps and future identity observations fail freshness', async () => {
  const f = fixture(); delete f.status.snapshot_observed_at_unix_ms;
  f.identity.observed_at = new Date(NOW + 1).toISOString();
  assert.equal((await collectBootRuntimeObservation(f.args)).status, 'STALE_OR_INCOMPLETE');
});
test('wrong workspace stops before an identity query and never exposes its path', async () => {
  const f = fixture(); f.runtime.device.workspace = path.resolve('private-other-workspace');
  const r = await collectBootRuntimeObservation(f.args);
  assert.equal(r.failure_code, 'WORKSPACE_TARGET_MISMATCH'); assert.equal(f.calls.length, 2);
  assert.doesNotMatch(JSON.stringify(r), /private-other/);
});
test('descriptor replacement and epoch drift cannot mix snapshots', async () => {
  const f = fixture(); let reads = 0;
  f.args.readDescriptor = () => ++reads === 1 ? f.descriptor : { ...f.descriptor, instance_id: 'new-host' };
  assert.equal((await collectBootRuntimeObservation(f.args)).failure_code, 'HOST_IDENTITY_CHANGED');
  const g = fixture(); g.identity.current_activation_epoch_id = 'new-epoch';
  assert.equal((await collectBootRuntimeObservation(g.args)).failure_code, 'EPOCH_CHANGED_DURING_READ');
});
test('bad target and read failures do not echo secret exception content', async () => {
  assert.equal((await collectBootRuntimeObservation({})).failure_code, 'EXPLICIT_WORKSPACE_REQUIRED');
  const f = fixture(); f.args.client.call = async () => { throw new Error('secret-marker'); };
  const r = await collectBootRuntimeObservation(f.args);
  assert.equal(r.failure_code, 'RECOVERY_READ_FAILED'); assert.doesNotMatch(JSON.stringify(r), /secret-marker/);
});

test('Host sanitizes attested completed contact and collector requires exact target/request', async () => {
  const f = fixture();
  const read = { schema_version: 1, kind: 'workspace_read_completed', tool: 'workspace_context',
    completed: true, workspace_accessed: true, request_id: `rpc-${'a'.repeat(64)}`,
    device_id: 'device-a', endpoint_id: 'endpoint-a', workspace_id: 'workspace-a', workspace_generation: 1,
    process_instance_id: 'process-a', server_instance_id: 'server-a', activation_epoch_id: 'epoch-a',
    contract_sha256: 'b'.repeat(64), observed_at: new Date(NOW - 10).toISOString(), secret: 'secret-marker' };
  const health = { ready: true, process_instance_id: 'process-a', instance_id: 'server-a', activation_epoch_id: 'epoch-a',
    tool_contract: { sha256: 'b'.repeat(64) }, connector_client_contact: {
      current_contract_contact: true, identity_source: 'attested_transport', attestation_verified: true, workspace_read: read } };
  const build = () => buildMcpIdentityObservation({ recoveryHostInstanceId: 'host-a', health,
    activationEpoch: { activation_epoch_id: 'epoch-a', admission_open: true }, observedAt: new Date(NOW).toISOString() });
  Object.assign(f.identity, build());
  assert.doesNotMatch(JSON.stringify(f.identity), /secret-marker/);
  assert.equal((await collectBootRuntimeObservation(f.args)).client, null);
  f.args.expectedClient = { device_id: 'device-a', endpoint_id: 'endpoint-a', workspace_id: 'workspace-a',
    workspace_generation: 1, request_id: read.request_id };
  const result = await collectBootRuntimeObservation(f.args);
  assert.equal(result.client.workspace_accessed, true);
  assert.equal(result.client.delivery_confirmed, false);
  f.args.expectedClient.request_id = `rpc-${'c'.repeat(64)}`;
  assert.equal((await collectBootRuntimeObservation(f.args)).client, null);
  for (const [key, bad] of [['completed', false], ['activation_epoch_id', 'other'],
    ['observed_at', new Date(NOW - 31_000).toISOString()], ['workspace_generation', true]]) {
    const saved = read[key]; read[key] = bad;
    assert.equal(build().workspace_read, null, key); read[key] = saved;
  }
  health.connector_client_contact.attestation_verified = false;
  assert.equal(build().workspace_read, null);
});

test('CLI requires all correlation fields, validates before IPC, and never invents a read', async () => {
  const args = ['--workspace', workspace, '--device-id', 'device-a', '--endpoint-id', 'endpoint-a',
    '--workspace-id', 'workspace-a', '--workspace-generation', '1', '--request-hash', 'a'.repeat(64)];
  assert.equal(parseArguments(args).expectedClient.request_id, `rpc-${'a'.repeat(64)}`);
  assert.equal(parseArguments(['--workspace', workspace]).expectedClient, undefined);
  let calls = 0;
  const deps = { collect: async (parsed) => {
    calls++; assert.equal(parsed.expectedClient.workspace_generation, 1);
    return { status: 'OBSERVED', client: null };
  }, output: () => {} };
  assert.equal(await main(args, deps), 1, 'runtime observation cannot satisfy missing client correlation');
  for (const bad of [args.slice(0, -2), [...args, '--device-id', 'other'], ['--workspace', workspace, '--force', 'true'],
    args.map((x) => x === '1' ? '1.5' : x), args.map((x) => x === '1' ? '9007199254740992' : x)]) {
    const before = calls;
    assert.equal(await main(bad, deps), 2);
    assert.equal(calls, before);
  }
});
