'use strict';

function clampCount(value, min, max) {
  if (![value, min, max].every(Number.isInteger)) {
    throw new TypeError('value, min, and max must be finite integers');
  }

  if (min > max) {
    throw new RangeError('min must be less than or equal to max');
  }

  return Math.min(max, Math.max(min, value));
}

module.exports = { clampCount };
