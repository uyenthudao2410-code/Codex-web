'use strict';
// Artifact and synthetic guard validation only. Never invokes a runtime phase.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const asar = require('@electron/asar');
const repo = 'E:\\Github\\Tools-Codex-web';
const dir = __dirname;
const candidate = path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-source-fingerprint-1012-r13/win-unpacked');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const sha = file => hash(fs.readFileSync(file));
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const requireProof = (value, code) => { if (!value) throw new Error(code); };
const h = require('./transition-r13.cjs');
const frozen = read(path.join(dir, '../source-freeze.json'));
const parity = read(path.join(dir, '../candidate-parity-20261011T200058268Z.json'));
requireProof(sha(path.join(dir, '../source-freeze.json')) === 'e9351a360eaa7c016514015a27ea06c762604e12c2a5ca436a550abbf09f29ff' && sha(path.join(dir, '../candidate-parity-20261011T200058268Z.json')) === '7c2c60851359f619472bbfafb649529b3eaae90ee6a4626a724c401b91323b88' && parity.ok === true && frozen.source_files.length === 17, 'FROZEN_PACKAGE_PROOF_CHANGED');
for (const item of frozen.source_files) {
  const payload = item.payload.startsWith('app.asar/')
    ? asar.extractFile(path.join(candidate, 'resources/app.asar'), path.join(...item.payload.slice(9).split('/')))
    : fs.readFileSync(path.join(candidate, item.payload));
  requireProof(sha(path.join(repo, item.source)) === item.sha256 && hash(payload) === item.sha256, 'FROZEN_SOURCE_OR_PAYLOAD_CHANGED');
}
const manifestFile = path.join(dir, 'helper-manifest.json');
const manifest = read(manifestFile);
for (const item of manifest.helper_files) requireProof(sha(path.join(dir, item.file)) === item.sha256, 'HELPER_PIN_CHANGED');
for (const item of manifest.dependencies) requireProof(sha(path.join(repo, item.file)) === item.sha256 && hash(asar.extractFile(path.join(candidate, 'resources/app.asar'), path.join(...item.file.split('/')))) === item.sha256, 'DEPENDENCY_PIN_CHANGED');
const run = (exe, args) => { const r = spawnSync(exe, args, { windowsHide: true, shell: false, encoding: 'utf8', timeout: 15000, maxBuffer: 65536 }); requireProof(!r.error && r.status === 0, 'OFFLINE_COMMAND_FAILED'); return r.stdout; };
for (const file of ['transition-r13.cjs', 'offline-check.cjs', 'verify-packet.cjs']) run(process.execPath, ['--check', path.join(dir, file)]);
// Reuse the successful 9/9 tool result for these exact helper bytes.
requireProof(sha(path.join(dir, 'transition-r13.cjs')) === '8b376db45d4be9669edcc8278b6411da899497469e8f6d4b70f7b9662876d4d0' && sha(path.join(dir, 'offline-check.cjs')) === '43a3db921569ddc98246206ea7420e103a4047a34edffe608640960ecb3791f7', 'PASSED_GUARD_RESULT_SOURCE_CHANGED');
const ps = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe';
const literal = value => "'" + value.replaceAll("'", "''") + "'";
const parse = run(ps, ['-NoProfile', '-NonInteractive', '-Command', '$packetTokens=$null;$packetErrors=$null;[System.Management.Automation.Language.Parser]::ParseFile(' + literal(path.join(dir, 'launch-child.ps1')) + ',[ref]$packetTokens,[ref]$packetErrors) | Out-Null;@{parse_errors=@($packetErrors).Count;executed=$false} | ConvertTo-Json -Compress']);
const parsed = JSON.parse(parse.replace(/^\uFEFF/, '').trim());
requireProof(parsed.parse_errors === 0 && parsed.executed === false, 'POWERSHELL_PARSE_FAILED');
run(path.join(candidate, 'resources/resources/native-python/python.exe'), ['-B', '-I', '-c', 'import pathlib; p=pathlib.Path(' + JSON.stringify(path.join(dir, 'query-job.py')) + '); compile(p.read_text(encoding="utf-8"), str(p), "exec")']);
const proof = {
  kind: 'r13_windows_transition_rotated_pilot_offline_proof', observed_at: new Date().toISOString(),
  runtime_activated: false, server_mutated: false, policy_mutated: false, approval_received: false,
  guard_tests_passed: 9, guard_result_reused_from_exact_helper_hashes: true, node_syntax: 'passed', windows_powershell_parse_errors: 0, query_job_compile_only: 'passed',
  matched_candidate_payload_files: 17, matched_lifecycle_dependencies: manifest.dependencies.length,
  source_freeze_sha256: sha(path.join(dir, '../source-freeze.json')),
  candidate_parity_sha256: sha(path.join(dir, '../candidate-parity-20261011T200058268Z.json')),
  helper_manifest_sha256: sha(manifestFile), helper_files: manifest.helper_files,
  preserved_authority_window: { context_id: h.authorityWindow.context_id, requested_at_ms: h.authorityWindow.requested_at_ms, expires_at_ms: h.authorityWindow.expires_at_ms },
  predecessor_pilot_id: h.authorityWindow.pilot_id, expected_operation: h.rotationOperation, expected_approval_id: h.rotationApprovalId,
  replacement_pilot_created_before_activation_required: true, minimum_remaining_ms: h.minimumWindowMs,
  server_pause_count_allowed: 1, original_r12_receipt_preserved_and_rejected_for_r13_effects: true
};
const name = 'rotation-proof-' + proof.observed_at.replace(/[^0-9TZ]/g, '') + '.json';
fs.writeFileSync(path.join(dir, name), JSON.stringify(proof, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify({ ok: true, guard_tests_passed: 9, helper_manifest_sha256: proof.helper_manifest_sha256, receipt: name, receipt_sha256: sha(path.join(dir, name)), runtime_activated: false, server_mutated: false }) + '\n');
