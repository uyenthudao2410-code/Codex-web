'use strict';
const assert = require('node:assert/strict');
const test = require('node:test');
const helper = require('./local-semantic-acceptance.cjs');
const run = 'a'.repeat(32), wave = 'b'.repeat(32);
test('audit keeps only proofs from the original exact RUN/WAVE', () => {
  const value = helper.projectAudit({ orchestration: { run_id: run, wave_id: wave, orchestration_state: 'ACCEPTING' },
    audit: { run: { run_id: run, status: 'active' }, proofs: [
      { run_id: run, wave_id: wave, proof_id: '1'.repeat(32), status: 'passed', input_fingerprint: '2'.repeat(64) },
      { run_id: 'c'.repeat(32), wave_id: wave, proof_id: '3'.repeat(32), status: 'passed' },
      { run_id: run, wave_id: 'd'.repeat(32), proof_id: '4'.repeat(32), status: 'passed' }
    ] } }, { run_id: run, wave_id: wave });
  assert.equal(value.proofs.length, 1);
  assert.equal(value.state, 'ACCEPTING');
  assert.equal(value.proofs[0].proof_id, '1'.repeat(32));
});
test('audit rejects a projection from a different original wave', () => {
  assert.throws(() => helper.projectAudit({ orchestration: { run_id: run, wave_id: 'c'.repeat(32) } },
    { run_id: run, wave_id: wave }), error => error.code === 'AUDIT_ORIGINAL_RUN_WAVE_MISMATCH');
});
test('final canary selection rejects duplicate final outcomes', () => {
  const row = { phase: 'final', operation: 'native_first_shared_mcp_canary',
    workspace_id: 'workspace_f93b5bac9dc74fae9cea66f44c4ebc94',
    workspace_generation: 'generation_a420c8bfcfcb4e42b5bb7fc5e5cec097', attempt_id: 'a'.repeat(32), proofs: {} };
  assert.equal(helper.finalCanary([row]), row);
  assert.throws(() => helper.finalCanary([row, row]), error => error.code === 'EXACT_FINAL_CANARY_REQUIRED');
});
test('tool payload reads the supported structured result and refuses MCP errors', () => {
  assert.deepEqual(helper.toolPayload({ id: 'rpc', result: { structuredContent: { accepted: true } } }, 'rpc'),
    { accepted: true });
  assert.throws(() => helper.toolPayload({ id: 'rpc', result: { isError: true, structuredContent: {} } }, 'rpc'),
    error => error.code === 'LOCAL_MCP_GUARD_REJECTED');
  assert.throws(() => helper.toolPayload({ id: 'different', result: { structuredContent: {} } }, 'rpc'),
    error => error.code === 'LOCAL_MCP_GUARD_REJECTED');
});
test('post-reject audit uses the current persisted report latch', () => {
  const result = helper.projectAudit({ orchestration: { run_id: run, wave_id: wave, orchestration_state: 'REPLAN' },
    state: { completion_report_id: 'report-current' }, completion_report: { state: 'REPLAN' },
    audit: { run: { run_id: run }, proofs: [] } }, { run_id: run, wave_id: wave });
  assert.equal(result.completion_report_id, 'report-current');
  assert.equal(result.state, 'REPLAN');
});
test('real verifier proof rejects cache reuse, wrong command and wrong source scope', () => {
  const crypto = require('node:crypto');
  const command = 'node tests/fixtures/native-first-canary/verify-postimages.cjs';
  const hash = crypto.createHash('sha256').update(command).digest('hex');
  const target = { acceptance_files: [{ path: 'tests/fixtures/native-first-canary/file-001.txt' }] };
  const proof = { status: 'passed', input_fingerprint: '2'.repeat(64), stage_id: 'check:' + hash.slice(0, 16),
    command_hash: hash, exit_code: 0, cache_hit: false, proof_reuse: null,
    result_status: 'passed', cancelled: false, timed_out: false,
    proof_source_binding: { paths: target.acceptance_files.map(value => value.path) } };
  assert.equal(helper.realVerifierProof(proof, target, command), true);
  assert.equal(helper.realVerifierProof({ ...proof, cache_hit: true, proof_reuse: { executed: false } }, target, command), false);
  assert.equal(helper.realVerifierProof({ ...proof, command_hash: 'f'.repeat(64) }, target, command), false);
  assert.equal(helper.realVerifierProof({ ...proof, proof_source_binding: { paths: [] } }, target, command), false);
});
