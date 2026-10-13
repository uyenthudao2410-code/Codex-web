'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const Module = require('node:module');
const originalLoad = Module._load;
Module._load = function (request, parent, isMain) {
  return request === 'original-fs' ? fs : originalLoad.apply(this, arguments);
};
const helper = require('./timefix-handoff-final-policy.cjs');
const baselinePath = 'E:/DEV/Codex-web/.coding-tools/reports/native-first-20261012/parallel-r3-transition/canary-policy-baseline-1791809168575-0779bf7e.json';
const baseline = JSON.parse(fs.readFileSync(baselinePath, 'utf8'));
const baselineSha256 = '126534d0440e0497932c96c4dbe6dcc097794c9780e4014f3b7cd0da461a6298';
assert.equal(helper.validateOriginalNativeFirstBaseline(baseline, baselinePath, baselineSha256).receipt.activation_epoch_id,
  'activation-mv58t4he-c162dd8a1c513c77581c5adee2ae6762');
for (const [label, mutate] of [
  ['wrong hash', (_copy) => ({ path: baselinePath, sha256: '0'.repeat(64) })],
  ['wrong candidate', (copy) => { copy.candidate = 'E:/DEV/Codex-web/dist/windows-candidate-mxc-wsb-cbe1774-parallel-r4-timefix/win-unpacked'; return { path: baselinePath, sha256: baselineSha256 }; }],
  ['wrong epoch', (copy) => { copy.receipt.activation_epoch_id = 'activation-mv5gbzeq-7ac98611bf3a96aa444fcf8e14d3ea1c'; return { path: baselinePath, sha256: baselineSha256 }; }],
]) {
  const copy = JSON.parse(JSON.stringify(baseline));
  const args = mutate(copy);
  assert.throws(() => helper.validateOriginalNativeFirstBaseline(copy, args.path, args.sha256), /EXACT_ORIGINAL_CANARY_BASELINE_REQUIRED/, label);
}
console.log(JSON.stringify({ ok: true, authentic_acceptance: 1, mismatch_rejections: 3, live_mutation_performed: false }));
