'use strict';

// Project existing receipts. This helper never dispatches work or edits runtime state.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = __dirname;
const load = (name) => JSON.parse(fs.readFileSync(path.join(root, name), 'utf8'));
const lines = (name) => fs.readFileSync(path.join(root, name), 'utf8').trim()
  .split(/\r?\n/).filter(Boolean).map(JSON.parse);
const digest = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');
const fileEvidence = 'canary/autocad-folder-access-receipt-r9d-379870e54349464ca9bf8c1d03dd92e0.ndjson';
const execEvidence = 'canary/autocad-exec-remaining-receipt-r9d-912d867d0dff4ce98aa3b3220a096319.ndjson';
const serverEvidence = 'final-server-surface-r9d-1791797626010.json';
const localEvidence = 'r9d-transition/final-machine-observation-activation-mv514if9-7a4fabe0ce77708f8be03ff43a6518db-1791797633598.json';
const shortcutEvidence = 'r9d-transition/coding-tools-shortcuts-after-r9d.json';
const fileRows = lines(fileEvidence);
const fileFinal = fileRows.find((row) => row.phase === 'final');
const execFinal = lines(execEvidence).find((row) => row.phase === 'final');
const server = load(serverEvidence);
const local = load(localEvidence);
const shortcuts = load(shortcutEvidence);
const target = 'E:\\DEV\\Autocad\\mcp-access-smoke-20261012-r9d.txt';
const targetBytes = fs.readFileSync(target);
const expectedHash = '3a42ea5c3e68101db07001a265b9fb4fcbbc0021ed965139dcf10ea99ba73023';
assert.equal(targetBytes.length, 63);
assert.equal(digest(targetBytes), expectedHash);
assert.equal(fileFinal.task_closed_verified, true);
assert.equal(fileFinal.writer_released_verified, true);
assert.equal(fileFinal.unresolved_original_actions.length, 0);
const fileProofs = fileRows.filter((row) => ['create_verified', 'patch_verified', 'readback_verified'].includes(row.phase));
assert.equal(fileProofs.length, 4);
for (const row of fileProofs) assert.equal(row.attempt_number, 1);
assert.equal(execFinal.ok, true);
assert.equal(execFinal.task_closed_verified, true);
assert.equal(execFinal.writer_released_verified, true);
assert.equal(execFinal.unresolved_original_actions.length, 0);
assert.equal(execFinal.proofs.node_version.stdout, 'v24.19.0');
assert.equal(execFinal.proofs.node_version.reused_original_job, true);
assert.equal(execFinal.proofs.node_cwd.receipt.stdout, 'C:\\CodexWorkspace\\share-0');
assert.equal(execFinal.proofs.node_hash.receipt.stdout, expectedHash);
assert.equal(execFinal.proofs.dotnet.receipt.stdout, '10.0.102');
for (const proof of Object.values(execFinal.proofs)) {
  assert.equal(proof.status.exit_code, 0);
  assert.equal(proof.status.action.central_lifecycle_state, 'completed');
}
assert.equal(server.current_generation_idle, true);
assert.equal(server.current_device_live_task_writer_idle, true);
assert.equal(server.tunnel_ready.status, 200);
assert.equal(server.sqlite_integrity_ok, true);
assert.equal(server.last_safe_renewal_receipt.selected_scope_matches_live_pilot, true);
assert.deepEqual(server.selected_target.capabilities, { exec: true, read: true, write: true });
assert.equal(local.ok, true);
assert.equal(local.epoch.state, 'READY');
assert.equal(local.epoch.admission_state, 'OPEN');
assert.equal(local.runtime.fullyReady, true);
assert.equal(local.ledger_idle, true);
assert.equal(local.descriptor_stable, true);
assert.equal(shortcuts.length, 2);
for (const shortcut of shortcuts) {
  assert.equal(shortcut.target, path.join(local.candidate, 'Coding Tools MCP.exe'));
  assert.equal(shortcut.target_exists, true);
}
const evidenceFiles = [fileEvidence, execEvidence, serverEvidence, localEvidence, shortcutEvidence,
  'server-deployment-receipt.json', 'r9d-parity.txt', 'r9d-smoke.txt',
  'r9d-transition/isolated-crypto-profile-remediation.json'];
const report = {
  schema_version: 1,
  operation: 'r9d_autocad_operational_completion_projection',
  observed_at: new Date().toISOString(),
  operational_access_pass: true,
  semantic_acceptance_complete: false,
  read_only_projection: true,
  repository: { root: 'E:\\DEV\\Codex-web', branch: 'main', head: '7999c4151cb501db86f2e4d0a2275d33fc248324', worktree: 'dirty_preserved', commit: false, push: false, published_release: false },
  workflow: 'Thêm thư mục → chọn đúng thư mục → xác nhận một lần quyền đọc/sửa/chạy; chuyển binding và chính sách theo đúng path/generation.',
  target_workspace: 'E:\\DEV\\Autocad',
  target_source_modified: false,
  runtime: { candidate: local.candidate, activation_epoch_id: local.target_activation_epoch_id,
    state: local.epoch.state, admission_state: local.epoch.admission_state,
    host_pid: local.host.pid, package: local.package, shortcuts_updated: 2 },
  server: { destination: 'svhome@100.116.112.22', deployed_and_restarted: true,
    service_pid: server.service_pid, package_source_sha256: server.health.package_source_sha256,
    selected_target: server.selected_target, census: server.current_generation_census,
    tunnel_status: server.tunnel_ready.status, selected_pilot_renewal_confirmed: true },
  file: { path: target, bytes: targetBytes.length, sha256: expectedHash,
    proofs: fileProofs, task_closed: true, writer_released: true },
  commands: Object.fromEntries(Object.entries(execFinal.proofs).map(([name, proof]) => [name, {
    action_id: proof.status.action.action_id, receipt_id: proof.receipt.receipt_id,
    exit_code: proof.status.exit_code, stdout: proof.stdout || proof.receipt.stdout,
    reused_original_job: proof.reused_original_job === true,
  }])),
  live_execution_jobs_settled: true,
  native_resource_counts: local.native_idle_counts,
  preserved_pending_canary: { run_id: 'a123ac6f4c484f15a21033e0059d63d9',
    wave_id: '8aaccbc6dea74f9c96ffe6deb4844d82', last_observed_state: 'ACCEPTING',
    same_wave_semantic_verification: false, accepted_or_terminalized: false },
  preserved_history: { server_unknown_actions: server.historical_unknown_actions_preserved.length,
    historical_acceptance_preserved: local.historical_acceptance_preserved },
  deviations: [
    'The original combined file harness stopped at an oversized exec argv before an exec action was admitted; file create/read/PATCH/read remained completed.',
    'The original Node version Job completed; a harness compared the labeled output envelope as raw version text. The final helper re-observed that same Job without replay.',
    'Additional short Node cwd/hash and dotnet version Jobs completed with exit 0.',
    'The patch canary has no same-wave semantic proof and remains pending. Operational access PASS does not mark it ACCEPTED.',
    'An isolated helper could not decrypt existing authorization. No production key was copied; its generated profile key was moved out of repository evidence with a retained remediation receipt.',
  ],
  evidence: evidenceFiles.map((name) => ({ path: path.join(root, name), sha256: digest(fs.readFileSync(path.join(root, name))) })),
};
const output = path.join(root, 'completion-r9d.json');
fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { encoding: 'utf8', flag: 'wx' });
console.log(JSON.stringify({ ok: true, report: output, operational_access_pass: true, semantic_acceptance_complete: false }));
