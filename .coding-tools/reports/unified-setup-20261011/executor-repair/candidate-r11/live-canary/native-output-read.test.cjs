'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { canaryObservation, safePage, checkerTap } = require('./native-output-read.cjs');
const command = 'command_one';
const page = content => ({ ok: true, command_id: command, stream: 'stdout',
  output_ref: `command:${command}:stdout`, stream_output_ref: `command:${command}:stdout`,
  offset: 0, requested_offset: 0, next_offset: null, truncated: false, omitted_bytes: 0,
  stream_dropped_bytes: 0, evicted_bytes_total: 0, content, total_stream_bytes: Buffer.byteLength(content) });
test('retained exact command stdout is pinned and secret content is rejected', () => {
  assert.equal(safePage(page('TAP version 13\n'), command, 'stdout').content, 'TAP version 13\n');
  assert.throws(() => safePage(page('Bearer should-not-leak'), command, 'stdout'), { code: 'PRIVATE_OUTPUT_REJECTED' });
  assert.throws(() => safePage(page('valid'), 'different', 'stdout'), { code: 'EXACT_RETAINED_CANARY_OUTPUT_REQUIRED' });
});
test('truncated or evicted output cannot establish four passed tests', () => {
  for (const delta of [{ truncated: true }, { next_offset: 1 }, { omitted_bytes: 2 }, { stream_dropped_bytes: 1 }]) {
    assert.throws(() => safePage({ ...page('valid'), ...delta }, command, 'stdout'), { code: 'EXACT_RETAINED_CANARY_OUTPUT_REQUIRED' });
  }
});
test('TAP requires the exact four checker cases plus 4 pass and zero fail', () => {
  const cases = [
    'passed proof is ready for genuine controller acceptance',
    'failed proof retains the applied patch for replanning',
    'timed-out proof retains the applied patch for replanning',
    'an unapplied patch cannot be ready for acceptance'
  ];
  const text = cases.map((name, index) => `ok ${index + 1} - ${name}`).join('\n') + '\n# tests 4\n# pass 4\n# fail 0\n';
  assert.equal(checkerTap(safePage(page(text), command, 'stdout')).pass, 4);
  assert.throws(() => checkerTap(safePage(page(text.replace('# pass 4', '# pass 3')), command, 'stdout')),
    { code: 'EXACT_CHECKER_TAP_4_OF_4_REQUIRED' });
});
test('only settled passed central service observation selects output command', () => {
  const summary = { run_id: '1'.repeat(32), wave_id: '2'.repeat(32), initial_verification: {
    proof_status: 'passed', plan_sha256: '235ecd2dc1bf8b49b21648ffd24df378088916e65e2420cb383fa79a6439afe7',
    proof_fingerprint: '3'.repeat(64), proof_ids: ['4'.repeat(32)], command_id: command, job_id: 'job_one' } };
  const row = { ok: true, phase: 'observe', provenance: 'central_mcp_service_trial', family: { settled: true, state: 'settled' },
    verified_patch_and_initial_proof_summary: summary };
  assert.equal(canaryObservation({ public_receipts: [row] }).proof.command_id, command);
  assert.throws(() => canaryObservation({ ...row, provenance: 'genuine_chatweb' }), { code: 'EXACT_CANARY_OBSERVATION_REQUIRED' });
  assert.throws(() => canaryObservation({ ...row, family: { settled: false, state: 'accepted' } }), { code: 'CANARY_PROOF_IDENTITY_INVALID' });
});
