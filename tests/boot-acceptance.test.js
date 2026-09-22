const test = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { verifyBootAcceptance } = require('../scripts/verify-boot-acceptance');

const NOW = 1_790_000_000_000;
const SHA = 'a'.repeat(64);
function fixture(role = 'direct_legacy') {
  const target = { device_id: 'device-a', endpoint_id: 'endpoint-a', workspace_id: 'workspace-a', workspace_generation: 1 };
  const problem = { problem_id: 'prl-22e670302757c9b7663170e226ed7c26', problem_revision: 1, criteria_fingerprint: SHA };
  const expected = {
    schema_version: 2, ...problem, ...target, execution_role: role,
    package_sha256: SHA, executable_sha256: SHA, supervisor_script_sha256: SHA, contract_sha256: SHA,
    revisions: { recovery_host: SHA, coding_mcp: SHA }, startup_intent: 'enabled',
    connector_policy: 'strict', binding_id: 'binding-a', principal_id: 'principal-a'
  };
  const receipt = {
    schema_version: 2, ...problem, manual_repair_count: 0,
    attempts: [{ operation_id: 'op-a', outcome: 'succeeded' }],
    before: { boot_time_ms: NOW - 100_000, observed_at_ms: NOW - 90_000,
      host: { instance_id: 'old-host', process_start_token: '134345300000000001' } },
    after: {
      ...target, execution_role: role, observed_at_ms: NOW, boot_time_ms: NOW - 60_000, boot_mode: 'restart',
      package_sha256: SHA, startup_intent: 'enabled',
      host: { runtime_mode: 'packaged', pid: 101, instance_id: 'new-host', process_start_token: '134345400000000001',
        executable_sha256: SHA, started_at_ms: NOW - 50_000, activation_epoch_id: 'epoch-a' },
      supervisor: { installed: true, state: 'healthy', pid: 102, observed_at_ms: NOW, last_host_pid: 101, script_sha256: SHA },
      revisions: Object.fromEntries(['recovery_host', 'coding_mcp'].map((key) => [key, { running_revision: SHA, disk_revision: SHA, update_pending: false }])),
      runtime: {
        executionRole: role, activationEpoch: { activation_epoch_id: 'epoch-a', operation_id: 'op-a', state: 'READY', admission_open: true },
        updateIncomplete: false, mcpRunning: true, nativeAlive: true, componentsReady: true, fullyReady: true,
        process_instance_id: 'process-a', server_instance_id: 'server-a', toolContract: { sha256: SHA },
        tunnelRunning: role === 'direct_legacy', localReady: true, centralConnected: true, authorityReady: true,
        connectorRediscovered: true, connector_observed_at_ms: NOW - 1_000, connectorRefreshRequired: false,
        connectorContractState: 'CURRENT_ACKNOWLEDGED', connectorContractAcknowledgedSha256: SHA
      },
      central_route: { ...target, binding_id: 'binding-a', principal_id: 'principal-a', observed_at_ms: NOW,
        authority_ready: true, admission_open: true, policy_expires_at_ms: NOW + 60_000 }
    },
    client: { ...target, observed_at_ms: NOW - 500, process_instance_id: 'process-a', server_instance_id: 'server-a',
      activation_epoch_id: 'epoch-a', contract_sha256: SHA, tool: 'workspace_context', ok: true,
      completed: true, workspace_accessed: true, request_id: 'request-a', binding_id: 'binding-a', principal_id: 'principal-a',
      connector_rediscovered: true, connector_observed_at_ms: NOW - 1_000 }
  };
  return { expected, receipt };
}
const verify = ({ expected, receipt }) => verifyBootAcceptance(expected, receipt, { nowMs: NOW });

test('role-specific boot evidence can be consistent without becoming live acceptance', () => {
  for (const role of ['direct_legacy', 'central_executor']) {
    const result = verify(fixture(role));
    assert.equal(result.status, 'EVIDENCE_CONSISTENT', result.failures.join(','));
    assert.equal(result.authority_granted, false);
    assert.equal(result.live_accepted, false);
    assert.equal(result.receipt_authenticity_verified, false);
  }
});

test('PID/hash/healthy legacy receipt alone is never boot acceptance', () => {
  const packet = fixture();
  packet.receipt = { schema_version: 1, supervisor: { state: 'healthy' }, recovery: { pid: 99 }, expected_post_reboot: {} };
  assert.equal(verify(packet).status, 'NOT_PROVEN');
  assert.ok(verify(packet).failures.includes('SCHEMA_V2_REQUIRED'));
});

test('false-green and mismatched observations fail closed', async (t) => {
  const cases = {
    pending: (p) => { p.receipt.client.completed = false; p.receipt.client.workspace_accessed = false; },
    wrongWorkspace: (p) => { p.receipt.client.workspace_id = 'other'; },
    wrongGeneration: (p) => { p.receipt.client.workspace_generation++; },
    oldProcess: (p) => { p.receipt.client.process_instance_id = 'old'; },
    oldEpoch: (p) => { p.receipt.client.activation_epoch_id = 'old'; },
    oldContract: (p) => { p.receipt.client.contract_sha256 = 'b'.repeat(64); },
    wrongProblem: (p) => { p.receipt.problem_revision++; },
    staleClient: (p) => { p.receipt.client.observed_at_ms = NOW - 40_000; },
    futureObservation: (p) => { p.receipt.after.observed_at_ms = NOW + 1; },
    noReboot: (p) => { p.receipt.after.boot_time_ms = p.receipt.before.boot_time_ms; },
    reusedHost: (p) => { p.receipt.after.host.instance_id = 'old-host'; },
    sameStartToken: (p) => { p.receipt.after.host.process_start_token = p.receipt.before.host.process_start_token; },
    sourceDrift: (p) => { p.receipt.after.revisions.recovery_host.running_revision = 'b'.repeat(64); },
    stalePackage: (p) => { p.receipt.after.package_sha256 = 'b'.repeat(64); },
    failedEpoch: (p) => { p.receipt.after.runtime.activationEpoch.state = 'FAILED'; },
    closedAdmission: (p) => { p.receipt.after.runtime.activationEpoch.admission_open = false; },
    mcpDead: (p) => { p.receipt.after.runtime.mcpRunning = false; },
    falseString: (p) => { p.receipt.after.runtime.fullyReady = 'true'; },
    tunnelDead: (p) => { p.receipt.after.runtime.tunnelRunning = false; },
    noSupervisor: (p) => { p.receipt.after.supervisor.installed = false; },
    offIntent: (p) => { p.expected.startup_intent = 'disabled'; },
    manualRepair: (p) => { p.receipt.manual_repair_count = 1; },
    noHistory: (p) => { p.receipt.attempts = []; },
    noExpectedIdentity: (p) => { delete p.expected.workspace_id; delete p.receipt.after.workspace_id; delete p.receipt.client.workspace_id; }
  };
  for (const [name, change] of Object.entries(cases)) await t.test(name, () => {
    const p = fixture(); change(p); assert.equal(verify(p).status, 'NOT_PROVEN');
  });
});

test('post-boot host, supervisor and final attempt must belong to the measured activation', async (t) => {
  for (const mutate of [
    (p) => { p.receipt.after.host.started_at_ms = p.receipt.before.boot_time_ms; },
    (p) => { p.receipt.after.host.activation_epoch_id = 'other-epoch'; },
    (p) => { p.receipt.after.supervisor.last_host_pid = 999; },
    (p) => { p.receipt.after.supervisor.script_sha256 = 'b'.repeat(64); },
    (p) => { p.receipt.attempts[0].outcome = 'failed'; },
    (p) => { p.receipt.attempts[0].operation_id = 'other-operation'; }
  ]) await t.test(String(mutate), () => {
    const p = fixture(); mutate(p); assert.equal(verify(p).status, 'NOT_PROVEN');
  });
  const p = fixture('central_executor'); p.receipt.after.central_route.policy_expires_at_ms = NOW - 1;
  assert.equal(verify(p).status, 'NOT_PROVEN');
});

test('central requires real route, principal/binding and client discovery, not a local Tunnel', async (t) => {
  for (const field of ['binding_id', 'principal_id', 'device_id', 'workspace_generation']) await t.test(field, () => {
    const p = fixture('central_executor'); p.receipt.after.central_route[field] = 'wrong';
    assert.ok(verify(p).failures.includes('CENTRAL_BINDING_MISMATCH'));
  });
  const p = fixture('central_executor'); p.receipt.after.runtime.centralConnected = false;
  assert.ok(verify(p).failures.includes('CENTRAL_ROUTE_NOT_READY'));
  const q = fixture('central_executor'); q.receipt.client.connector_rediscovered = false;
  assert.ok(verify(q).failures.includes('CENTRAL_CLIENT_DISCOVERY_UNPROVEN'));
});

test('compatible continuity cannot impersonate strict rediscovery', () => {
  const p = fixture(); const r = p.receipt.after.runtime;
  r.connectorRediscovered = false; r.connectorContractState = 'CURRENT_COMPATIBLE_ACKNOWLEDGED';
  r.connectorCompatibilityAcknowledged = true;
  assert.equal(verify(p).status, 'NOT_PROVEN');
  p.expected.connector_policy = 'exact_or_reviewed_compatible'; p.expected.reviewed_ack_sha256 = SHA;
  assert.equal(verify(p).status, 'EVIDENCE_CONSISTENT');
  r.connectorRefreshRequired = true;
  assert.equal(verify(p).status, 'NOT_PROVEN');
});

test('fresh but pre-reboot discovery cannot certify the post-reboot client', () => {
  for (const role of ['direct_legacy', 'central_executor']) {
    const p = fixture(role);
    p.receipt.after.boot_time_ms = NOW - 100;
    p.receipt.after.host.started_at_ms = NOW - 50;
    p.receipt.client.observed_at_ms = NOW - 25;
    assert.equal(verify(p).status, 'NOT_PROVEN');
  }
});

test('CLI fails safely without echoing invalid inputs or paths', () => {
  const result = spawnSync(process.execPath, ['scripts/verify-boot-acceptance.js', 'secret-marker'], { encoding: 'utf8' });
  assert.equal(result.status, 2);
  assert.equal(JSON.parse(result.stdout).status, 'INVALID_INPUT');
  assert.doesNotMatch(result.stdout + result.stderr, /secret-marker/);
});

test('CLI reads bounded packets, reports hashes and redacts malformed or oversized JSON', (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'boot-oracle-test-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const expected = path.join(root, 'expected.json');
  const receipt = path.join(root, 'receipt.json');
  fs.writeFileSync(expected, '{}');
  fs.writeFileSync(receipt, '{}');
  const run = () => spawnSync(process.execPath, ['scripts/verify-boot-acceptance.js', expected, receipt], { encoding: 'utf8' });
  const consistentRead = run();
  assert.equal(consistentRead.status, 1);
  assert.match(JSON.parse(consistentRead.stdout).receipt_sha256, /^[a-f0-9]{64}$/);
  for (const content of ['{"secret-marker":', 'x'.repeat(256 * 1024 + 1)]) {
    fs.writeFileSync(receipt, content);
    const invalid = run();
    assert.equal(invalid.status, 2);
    assert.equal(JSON.parse(invalid.stdout).status, 'INVALID_INPUT');
    assert.doesNotMatch(invalid.stdout + invalid.stderr, /secret-marker|boot-oracle-test-/);
  }
});
