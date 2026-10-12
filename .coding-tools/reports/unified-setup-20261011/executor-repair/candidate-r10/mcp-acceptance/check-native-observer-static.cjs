'use strict';
// Require exposes only pure validation functions; helper main is not invoked.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { argument, safeIdentity } = require('./observe-r10-native-local.cjs');
const source = path.join(__dirname, 'observe-r10-native-local.cjs');
const expected = { epoch: 'activation-r10-static-check', host: 'a'.repeat(32) };
const fresh = () => ({ observation_schema_version: 1, observation_kind: 'mcp_identity_read_only', observed_at: new Date().toISOString(),
  recovery_host_instance_id: expected.host, mcp_process_instance_id: 'r10-process-static', mcp_server_instance_id: 'r10-server-static',
  activation_epoch_id: expected.epoch, current_activation_epoch_id: expected.epoch, tool_contract_sha256: 'b'.repeat(64),
  mcp_ready: true, identity_current: true, extra_private_metadata: 'STATIC_FIELD_MUST_NOT_BE_EXPORTED' });
const safe = safeIdentity(fresh(), expected);
assert.equal(safe.activation_epoch_id, expected.epoch);
assert.equal(Object.hasOwn(safe, 'extra_private_metadata'), false);
let cases = 1;
for (const change of [
  { observed_at: new Date(Date.now() - 60000).toISOString() },
  { observed_at: new Date(Date.now() + 60000).toISOString() },
  { recovery_host_instance_id: 'c'.repeat(32) },
  { activation_epoch_id: 'activation-other' },
  { current_activation_epoch_id: 'activation-other' },
  { mcp_ready: false }, { identity_current: false },
  { tool_contract_sha256: 'wrong' }, { mcp_process_instance_id: '' },
  { mcp_server_instance_id: '' }, { observation_kind: 'unsupported' }
]) {
  assert.throws(() => safeIdentity({ ...fresh(), ...change }, expected), error => error.code === 'EXACT_CURRENT_R10_IDENTITY_UNPROVEN');
  cases += 1;
}
assert.equal(argument(['--phase=cold'], 'phase', /^(cold|warm|observe)$/), 'cold');
cases += 1;
assert.throws(() => argument(['--phase=cold', '--phase=warm'], 'phase', /^(cold|warm|observe)$/));
cases += 1;
assert.throws(() => argument(['--phase=invalid'], 'phase', /^(cold|warm|observe)$/));
cases += 1;
const text = fs.readFileSync(source, 'utf8');
assert.equal(text.includes('client.identityObservation('), true);
assert.equal(text.includes('client.activateUpdate('), false);
assert.equal(text.includes('client.controlPlaneExec('), false);
assert.equal(text.includes('fs.readFileSync(daemonPath'), false);
assert.equal(text.includes("{ flag: 'wx' }"), true);
process.stdout.write(`${JSON.stringify({ kind: 'r10_native_observer_static_proof', ok: true, pure_validation_cases: cases,
  helper_sha256: crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex'),
  helper_main_invoked: false, runtime_ipc_called: false, host_processes_observed: false, live_operations: false })}\n`);
