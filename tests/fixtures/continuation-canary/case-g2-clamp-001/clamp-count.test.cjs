'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { clampCount } = require('./clamp-count.cjs');

test('returns an integer already inside the range', () => {
  assert.equal(clampCount(4, 0, 10), 4);
  assert.equal(clampCount(-4, -10, -1), -4);
});

test('clamps values below and above the range', () => {
  assert.equal(clampCount(-2, 0, 10), 0);
  assert.equal(clampCount(12, 0, 10), 10);
});

test('supports exact boundaries and a single-value range', () => {
  assert.equal(clampCount(0, 0, 10), 0);
  assert.equal(clampCount(10, 0, 10), 10);
  assert.equal(clampCount(4, 3, 3), 3);
});

test('rejects non-finite, non-integer, and non-number arguments', () => {
  const invalidCases = [
    [NaN, 0, 10],
    [Infinity, 0, 10],
    [-Infinity, 0, 10],
    [4.5, 0, 10],
    ['4', 0, 10],
    [null, 0, 10],
    [4, NaN, 10],
    [4, 0.5, 10],
    [4, '0', 10],
    [4, 0, Infinity],
    [4, 0, 10.5],
    [4, 0, null]
  ];

  for (const args of invalidCases) {
    assert.throws(
      () => clampCount(...args),
      TypeError,
      `expected TypeError for ${JSON.stringify(args)}`
    );
  }
});

test('rejects a reversed range', () => {
  assert.throws(
    () => clampCount(4, 10, 0),
    RangeError
  );
});
