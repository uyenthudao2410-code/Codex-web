'use strict';
// Attribute actual root validation and bind it to the current applied source.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const repo = path.resolve(__dirname, '../../../../..');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const reconciliation = path.join(__dirname, '../candidate-r13/reconciliation-5h');
const patch = fs.readFileSync(path.join(reconciliation, 'approved-patch-initial-proof-timeout-r2.patch'));
const manifestBytes = fs.readFileSync(path.join(reconciliation, 'approved-patch-initial-proof-timeout-r2.json'));
const manifest = JSON.parse(manifestBytes);
if (sha(patch) !== '5614539fdda1a5fd22a880a65a26d06f46c2741c649e3a1a68e0b045d643cf88' || manifest.patch_sha256 !== sha(patch)) throw new Error('APPLIED_PATCH_ARTIFACT_CHANGED');
const files = manifest.changes.map(item => {
  const bytes = fs.readFileSync(path.join(repo, item.file));
  const normalized = sha(bytes.toString('utf8').replace(/\r\n/g, '\n'));
  if (normalized !== item.candidate_normalized_sha256) throw new Error('APPLIED_SOURCE_NOT_EXACT_PREPARED_PATCH');
  return { file: item.file, applied_sha256: sha(bytes), applied_normalized_sha256: normalized };
});
const freezeBytes = fs.readFileSync(path.join(__dirname, 'source-freeze.json'));
const receipt = { schema_version: 1, observed_at: new Date().toISOString(), repository_root: repo,
  repository_head: JSON.parse(freezeBytes).repository_head, candidate_tag: 'workflow-timeout-1012-r14',
  source_freeze_sha256: sha(freezeBytes), applied_patch_sha256: sha(patch), applied_manifest_sha256: sha(manifestBytes),
  applied_source_files: files,
  actual_source_validation: {
    provenance: 'root controller reported successful actual-source tool execution; this lane did not rerun it',
    tool_chunk_id: '87110f',
    command: "node --test '--test-name-pattern=initial verification' tests/control-plane-approved-patch-runtime.test.js",
    tests: 3, pass: 3, fail: 0, skipped: 0, duration_ms: 458.3366,
    subtest_duration_ms: [322.7551, 13.1968, 3.251],
    stdout_artifact_available: false,
    scoped_git_diff_check: 'root reported passed in the same execution wave'
  },
  prior_in_memory_preparation_validation: { tests: 2, pass: 2, fail: 0,
    proof_path: '.coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r13/reconciliation-5h/approved-patch-initial-proof-timeout-r2.proof.json' },
  claim: 'source applied and focused checks passed; packaged parity and activation require separate evidence',
  runtime_activated: false, server_mutated: false };
fs.writeFileSync(path.join(__dirname, 'source-proof.json'), JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify({ ok: true, source_files: files.length, actual_source_tests: 3,
  source_freeze_sha256: receipt.source_freeze_sha256, source_proof_sha256: sha(JSON.stringify(receipt, null, 2) + '\n') }) + '\n');
