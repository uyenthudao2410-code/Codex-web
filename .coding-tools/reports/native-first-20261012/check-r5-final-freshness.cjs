'use strict';
// Hash-only final evidence freshness; no test, process launch, or runtime call.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../../..');
const { assertExactPackagedResources, assertExactControlPlaneAdapter } = require(path.join(root, 'scripts/verify-packaged-resources'));
const parityPath = path.join(__dirname, 'r5-candidate-parity.json');
const smokePath = path.join(__dirname, 'r5-packaged-smoke.json');
const productionPath = path.join(__dirname, 'production-transition-preflight-1791804360927.json');
const output = path.join(__dirname, 'r5-final-freshness-checkpoint.json');
if (fs.existsSync(output)) throw new Error('Preserve existing receipt');
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const parity = read(parityPath);
const smoke = read(smokePath);
const production = read(productionPath);
const resources = path.join(parity.candidate, 'resources/resources');
const codeDrift = Object.entries(parity.code_sha256).filter(([file, sha]) => hash(path.join(root, file)) !== sha).map(([file]) => file);
const resource = assertExactPackagedResources(path.join(root, 'resources'), resources, { separatelyVerifiedTopLevelDirectories: ['control-plane'] });
const adapter = assertExactControlPlaneAdapter(path.join(root, 'control-plane/control_plane'), path.join(resources, 'control-plane'));
const data = path.join(process.env.APPDATA, 'web-mcp-assistant');
const descriptor = read(path.join(data, 'recovery-host.json'));
const owner = Object.fromEntries(Object.keys(production.production_identity).map(name => [name, descriptor[name]]));
const policyDrift = Object.entries(production.preserved_policy_fingerprints).filter(([name, expected]) => {
  const file = path.join(data, name);
  return expected.present ? !fs.existsSync(file) || hash(file) !== expected.sha256 : fs.existsSync(file);
}).map(([name]) => name);
const executable = path.join(parity.candidate, 'Coding Tools MCP.exe');
const packageStable = hash(executable) === parity.executable_sha256
  && hash(path.join(parity.candidate, 'resources/app.asar')) === parity.app_asar_sha256;
const ownerStable = JSON.stringify(owner) === JSON.stringify(production.production_identity);
const report = {
  schema_version: 1, operation: 'final_r5_freshness_checkpoint', observed_at: new Date().toISOString(),
  observed_git_head_reference: parity.git_head,
  no_additional_tests_run: true, verification_kind: 'read-only source/package and preserved local state hashes',
  candidate: parity.candidate, application_code_files: Object.keys(parity.code_sha256).length,
  application_source_drift: codeDrift, resource_proof: resource, adapter_proof: adapter,
  executable_sha256: parity.executable_sha256, app_asar_sha256: parity.app_asar_sha256, package_stable: packageStable,
  parity_receipt: { path: parityPath, sha256: hash(parityPath) },
  smoke_receipt: { path: smokePath, sha256: hash(smokePath), ok: smoke.ok, exit_code: smoke.exit_code,
    observed_at: smoke.capture_finished_utc, fixture_generations_alive_after: smoke.fixture_generations_alive_after },
  production_identity: owner, production_identity_stable: ownerStable, policy_file_drift: policyDrift,
  production_runtime_census_reference: { path: productionPath, sha256: hash(productionPath), observed_at: production.observed_at,
    activation: production.activation, local_live_work_idle: production.local_live_work_idle, counts: production.canonical_ledger_census.counts },
  current_decision: 'Keep Codex-web as first canary and wait for historical UNKNOWN authority gate; preserve production r9e',
  local_activation_performed: false, service_operations_performed: false, task_or_policy_changes_performed: false,
  remaining_gate: 'Three historical AutoCAD file-read actions remain UNKNOWN; generic TARGET_MISSING has ambiguous pre/post-read origin',
  next_action: 'Wait for legitimate phase evidence or supported authority resolution; do not launch local transition',
  limitations: ['Hash freshness is separate from behavior tests; prior successful tests/smoke are reused', 'Live job state is the cited fresh final census, not inferred from file hashes']
};
report.ok = codeDrift.length === 0 && resource.exact_source && adapter.exact_source && packageStable && ownerStable && policyDrift.length === 0 && smoke.ok;
fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ ok: report.ok, report_path: output, code_drift: codeDrift, resource_files: resource.file_count,
  adapter_files: adapter.file_count, owner_stable: ownerStable, policy_drift: policyDrift }));
process.exitCode = report.ok ? 0 : 1;
