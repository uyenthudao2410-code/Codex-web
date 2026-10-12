'use strict';
// Require exposes only pure validation functions; helper main is not invoked.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { argument, safeIdentity } = require('./observe-r10-native-local-v3.cjs');
const source = path.join(__dirname, 'observe-r10-native-local-v3.cjs');
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
assert.equal(text.includes("require('original-fs').readFileSync(archive)"), true);
assert.equal(text.includes('sha(archive)'), false);
assert.equal(text.includes("pathKey(process.execPath) === pathKey(executable)"), true);
assert.equal(text.includes("const modules = path.join(repo, 'electron/services');"), true);
assert.equal(text.includes("const modules = path.join(archive, 'electron/services');"), false);
assert.equal(text.includes("entry.sha256 === hash && sha(path.join(modules, `${name}.js`)) === hash"), true);
assert.equal(text.includes("runtimeMode: 'packaged', executablePath: executable"), true);
assert.equal(text.includes("boundary: safeCode(boundary)"), true);
const repo = path.resolve(__dirname, '../../../../../..');
const parity = JSON.parse(fs.readFileSync(path.join(__dirname, '../candidate-parity-20261011T115907669Z.json'), 'utf8'));
assert.equal(crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname, '../candidate-parity-20261011T115907669Z.json'))).digest('hex'), 'c9f6fe1313b6004519a61bebf3f8f173a74cfd1d563bef48fce87908ed72f57c');
const moduleNames = ['commandRunner','deviceIdentity','jsonStore','pathSemantics','runtimeIdentity','runtimePaths','recoveryIpc','recoveryHostLauncher','processIdentity'];
for (const name of moduleNames) {
  const hash = crypto.createHash('sha256').update(fs.readFileSync(path.join(repo, 'electron/services', name + '.js'))).digest('hex');
  assert.equal(parity.packages.candidate.entries['app.asar/electron/services/' + name + '.js'].sha256, hash);
  assert.equal(text.includes(name + ": '" + hash + "'"), true);
}

assert.equal(text.includes('client.identityObservation('), true);
assert.equal(text.includes('client.activateUpdate('), false);
assert.equal(text.includes('client.controlPlaneExec('), false);
assert.equal(text.includes('fs.readFileSync(daemonPath'), false);
assert.equal(text.includes("{ flag: 'wx' }"), true);
process.stdout.write(`${JSON.stringify({ kind: 'r10_native_observer_static_proof_v3', ok: true, pure_validation_cases: cases, packaged_equivalent_modules: 9, actual_module_hash_matches: true, raw_archive_reader: 'electron_original_fs',
  helper_sha256: crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex'),
  helper_main_invoked: false, runtime_ipc_called: false, host_processes_observed: false, live_operations: false })}\n`);
