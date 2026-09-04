const test = require('node:test');
const assert = require('node:assert/strict');

const {
  MEASUREMENT_KINDS,
  kindRank,
  buildExact,
  buildEstimate,
  buildUnknown,
  selectEffective
} = require('../electron/services/tokenMeasurement');

test('measurement kinds follow exact-first precedence', () => {
  assert.deepEqual(MEASUREMENT_KINDS, ['exact', 'calibrated_estimate', 'structural_estimate', 'unknown']);
  assert.ok(kindRank('exact') > kindRank('calibrated_estimate'));
  assert.ok(kindRank('calibrated_estimate') > kindRank('structural_estimate'));
  assert.ok(kindRank('structural_estimate') > kindRank('unknown'));
  assert.equal(kindRank('billing'), -1);
});

test('exact requires all four counters and keeps point bounds', () => {
  const exact = buildExact({
    turn_id: 'turn-1', trace_id: 'trace-1',
    input_tokens: 100, cached_input_tokens: 40,
    output_tokens: 20, reasoning_output_tokens: 5,
    model_id: 'gpt-x', accounting_profile: 'openai_compatible', source: 'client_reported'
  });
  assert.equal(exact.kind, 'exact');
  assert.deepEqual(exact.total, { point: 120, lower: 120, upper: 120 });
  assert.equal(exact.confidence, 'exact');
  assert.equal(buildExact({
    turn_id: 'turn-1', trace_id: 'trace-1',
    input_tokens: 100, cached_input_tokens: null,
    output_tokens: 20, reasoning_output_tokens: 5
  }), null);
  assert.equal(buildExact({
    turn_id: 'turn-1', trace_id: 'trace-1',
    input_tokens: 100, cached_input_tokens: 101,
    output_tokens: 20, reasoning_output_tokens: 5
  }), null);
});

test('estimates require explicit bounds and never pose as exact', () => {
  const structural = buildEstimate({
    kind: 'structural_estimate', turn_id: 'turn-2', trace_id: 'trace-2',
    total: { point: 42000, lower: 30000, upper: 60000 },
    method_version: 'structural-v1'
  });
  assert.equal(structural.kind, 'structural_estimate');
  assert.equal(structural.confidence, 'none');
  assert.equal(structural.input, null);
  // No bounds, no estimate.
  assert.equal(buildEstimate({
    kind: 'structural_estimate', turn_id: 'turn-2', trace_id: 'trace-2',
    total: { point: 42000, lower: null, upper: null },
    method_version: 'structural-v1'
  }), null);
  // Inverted bounds rejected.
  assert.equal(buildEstimate({
    kind: 'structural_estimate', turn_id: 'turn-2', trace_id: 'trace-2',
    total: { point: 42000, lower: 60000, upper: 30000 },
    method_version: 'structural-v1'
  }), null);
  // Structural must not claim calibrated confidence.
  assert.equal(buildEstimate({
    kind: 'structural_estimate', turn_id: 'turn-2', trace_id: 'trace-2',
    total: { point: 42000, lower: 30000, upper: 60000 },
    confidence: 'high', method_version: 'structural-v1'
  }), null);
  // Calibrated requires a calibration summary.
  assert.equal(buildEstimate({
    kind: 'calibrated_estimate', turn_id: 'turn-2', trace_id: 'trace-2',
    total: { point: 42000, lower: 38000, upper: 47000 },
    method_version: 'calibrated-v1'
  }), null);
  const calibrated = buildEstimate({
    kind: 'calibrated_estimate', turn_id: 'turn-2', trace_id: 'trace-2',
    total: { point: 42000, lower: 38000, upper: 47000 },
    confidence: 'medium', method_version: 'calibrated-v1',
    calibration: { sample_count: 40, p50_ape: 0.07, p90_ape: 0.16 }
  });
  assert.equal(calibrated.kind, 'calibrated_estimate');
  assert.equal(calibrated.confidence, 'medium');
});

test('unknown keeps nulls and never zero', () => {
  const unknown = buildUnknown({ turn_id: 'turn-3', trace_id: 'trace-3', reason: 'no_exact_no_calibration' });
  assert.equal(unknown.kind, 'unknown');
  assert.equal(unknown.total, null);
  assert.equal(unknown.input, null);
  assert.equal(unknown.output, null);
  assert.ok(!('point' in unknown) || unknown.point === undefined);
  assert.equal(JSON.stringify(unknown).includes('0 tokens'), false);
});

test('builders keep only counters and opaque IDs, never content', () => {
  const exact = buildExact({
    turn_id: 'turn-4', trace_id: 'trace-4',
    input_tokens: 10, cached_input_tokens: 0, output_tokens: 5, reasoning_output_tokens: 0,
    model_id: 'gpt-x', accounting_profile: 'openai_compatible', source: 'client_reported',
    prompt: 'must be ignored', response: 'must be ignored', url: 'https://x', conversation_id: 'c-1'
  });
  assert.deepEqual(Object.keys(exact).sort(), [
    'accounting_profile', 'calibration', 'confidence', 'input', 'kind', 'method_version',
    'model_id', 'output', 'reason', 'source', 'total', 'trace_id', 'turn_id'
  ]);
});

test('selectEffective returns at most one winner with exact precedence', () => {
  const unknown = buildUnknown({ turn_id: 't', trace_id: 'r', reason: 'x' });
  const structural = buildEstimate({
    kind: 'structural_estimate', turn_id: 't', trace_id: 'r',
    total: { point: 9, lower: 5, upper: 15 }, method_version: 'structural-v1'
  });
  const exact = buildExact({
    turn_id: 't', trace_id: 'r',
    input_tokens: 8, cached_input_tokens: 0, output_tokens: 4, reasoning_output_tokens: 0
  });
  assert.equal(selectEffective([unknown, structural]), structural);
  assert.equal(selectEffective([structural, unknown, exact]), exact);
  assert.equal(selectEffective([unknown]), unknown);
  assert.equal(selectEffective([]), null);
  assert.equal(selectEffective(null), null);
  assert.equal(selectEffective([{ kind: 'billing' }]), null);
});
