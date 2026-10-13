'use strict';

// Per-turn token measurement contract.
//
// Finish line: nearly every completed ChatWeb turn produces exactly one
// effective measurement with an explicit kind:
//
//   exact               - provider/ChatGPT reported usage (all four counters)
//   calibrated_estimate - structural estimate corrected by exact samples
//   structural_estimate - bounded estimate from observable evidence only
//   unknown             - insufficient evidence; stays null, never zero
//
// Hard rules enforced here (not in callers):
// - missing is null, never 0; estimates never pose as exact or billing;
// - an estimate without lower<=point<=upper bounds is rejected (no fake
//   precision); confidence without a calibration summary is 'none';
// - selectEffective() returns at most one winner per turn (no double count);
// - no prompt/response/URL/conversation content is accepted or stored:
//   builders only keep counters, bounds, opaque IDs and method versions.

const MEASUREMENT_KINDS = ['exact', 'calibrated_estimate', 'structural_estimate', 'unknown'];

const METHOD_VERSION_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/;

function kindRank(kind) {
  if (kind === 'exact') return 3;
  if (kind === 'calibrated_estimate') return 2;
  if (kind === 'structural_estimate') return 1;
  if (kind === 'unknown') return 0;
  return -1;
}

function exactCount(value) {
  return Number.isSafeInteger(value) && value >= 0 ? value : null;
}

function boundedText(value, maxLength) {
  const text = String(value ?? '').trim();
  if (!text || text.length > maxLength) return null;
  return text;
}

function validRange(range) {
  if (!range || typeof range !== 'object' || Array.isArray(range)) return null;
  const point = exactCount(range.point);
  const lower = exactCount(range.lower);
  const upper = exactCount(range.upper);
  if (point === null || lower === null || upper === null) return null;
  if (!(lower <= point && point <= upper)) return null;
  return { point, lower, upper };
}

function validCalibration(value) {
  if (value === null || value === undefined) return null;
  if (typeof value !== 'object' || Array.isArray(value)) return false;
  if (!Number.isSafeInteger(value.sample_count) || value.sample_count < 1) return false;
  for (const key of ['p50_ape', 'p90_ape']) {
    const number = value[key];
    if (typeof number !== 'number' || !Number.isFinite(number) || number < 0) return false;
  }
  return {
    sample_count: value.sample_count,
    p50_ape: value.p50_ape,
    p90_ape: value.p90_ape
  };
}

function buildExact({ turn_id, trace_id, input_tokens, cached_input_tokens, output_tokens, reasoning_output_tokens, model_id, accounting_profile, source }) {
  const turnId = boundedText(turn_id, 128);
  const traceId = boundedText(trace_id, 128);
  const input = exactCount(input_tokens);
  const cached = exactCount(cached_input_tokens);
  const output = exactCount(output_tokens);
  const reasoning = exactCount(reasoning_output_tokens);
  if (!turnId || !traceId || input === null || cached === null || output === null || reasoning === null) return null;
  if (cached > input || reasoning > output) return null;
  const measured = {
    kind: 'exact',
    turn_id: turnId,
    trace_id: traceId,
    total: { point: input + output, lower: input + output, upper: input + output },
    input: { point: input, lower: input, upper: input },
    output: { point: output, lower: output, upper: output },
    confidence: 'exact',
    method_version: 'exact-receipt-v1',
    calibration: null,
    reason: null
  };
  const model = boundedText(model_id, 200);
  if (model) measured.model_id = model;
  const profile = boundedText(accounting_profile, 32);
  if (profile) measured.accounting_profile = profile;
  const origin = boundedText(source, 32);
  if (origin) measured.source = origin;
  return measured;
}

function buildEstimate({ kind, turn_id, trace_id, total, input, output, confidence, method_version, calibration }) {
  if (kind !== 'calibrated_estimate' && kind !== 'structural_estimate') return null;
  const turnId = boundedText(turn_id, 128);
  const traceId = boundedText(trace_id, 128);
  if (!turnId || !traceId) return null;
  const totalRange = validRange(total);
  if (!totalRange) return null;
  const measured = {
    kind,
    turn_id: turnId,
    trace_id: traceId,
    total: totalRange,
    input: input === undefined || input === null ? null : validRange(input),
    output: output === undefined || output === null ? null : validRange(output),
    confidence: 'none',
    method_version: null,
    calibration: null,
    reason: null
  };
  if ((input !== undefined && input !== null && !measured.input)
    || (output !== undefined && output !== null && !measured.output)) return null;
  const version = boundedText(method_version, 64);
  if (!version || !METHOD_VERSION_PATTERN.test(version)) return null;
  measured.method_version = version;
  if (kind === 'calibrated_estimate') {
    const summary = validCalibration(calibration);
    if (!summary) return null;
    measured.calibration = summary;
  } else if (calibration !== undefined && calibration !== null) {
    return null;
  }
  const stated = String(confidence || 'none').trim().toLowerCase();
  if (!['none', 'low', 'medium', 'high'].includes(stated)) return null;
  if (stated !== 'none' && kind !== 'calibrated_estimate') return null;
  measured.confidence = stated;
  return measured;
}

function buildUnknown({ turn_id, trace_id, reason }) {
  const measurement = {
    kind: 'unknown',
    turn_id: turn_id === undefined || turn_id === null ? null : boundedText(turn_id, 128),
    trace_id: trace_id === undefined || trace_id === null ? null : boundedText(trace_id, 128),
    total: null,
    input: null,
    output: null,
    confidence: 'none',
    method_version: null,
    calibration: null,
    reason: boundedText(reason, 160) || 'insufficient_evidence'
  };
  if ((turn_id !== undefined && turn_id !== null && !measurement.turn_id)
    || (trace_id !== undefined && trace_id !== null && !measurement.trace_id)) return null;
  return measurement;
}

function selectEffective(measurements) {
  const items = Array.isArray(measurements) ? measurements : [];
  let winner = null;
  let winnerRank = -1;
  let winnerSeen = -1;
  for (const item of items) {
    if (!item || typeof item !== 'object') continue;
    const rank = kindRank(item.kind);
    if (rank < 0) continue;
    const seen = Number(item.observed_at_unix_ms);
    const seenMs = Number.isFinite(seen) && seen >= 0 ? seen : -1;
    if (rank > winnerRank || (rank === winnerRank && seenMs > winnerSeen)) {
      winner = item;
      winnerRank = rank;
      winnerSeen = seenMs;
    }
  }
  return winner;
}

module.exports = {
  MEASUREMENT_KINDS,
  kindRank,
  buildExact,
  buildEstimate,
  buildUnknown,
  selectEffective
};
