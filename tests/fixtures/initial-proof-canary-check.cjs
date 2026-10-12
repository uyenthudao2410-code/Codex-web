'use strict';

// Run only through the explicit initial-verification argv in the acceptance
// packet. This filename is excluded from the ordinary npm test glob.
const test = require('node:test');
const assert = require('node:assert/strict');
const { proofDisposition } = require('./initial-proof-canary-target.cjs');

test('passed proof is ready for genuine controller acceptance', () => {
  assert.equal(proofDisposition({ patchApplied: true, proofStatus: 'passed' }), 'ready-for-acceptance');
});

test('failed proof retains the applied patch for replanning', () => {
  assert.equal(proofDisposition({ patchApplied: true, proofStatus: 'failed' }), 'replan');
});

test('timed-out proof retains the applied patch for replanning', () => {
  assert.equal(proofDisposition({ patchApplied: true, proofStatus: 'timed_out' }), 'replan');
});

test('an unapplied patch cannot be ready for acceptance', () => {
  assert.equal(proofDisposition({ patchApplied: false, proofStatus: 'passed' }), 'not-applied');
});
