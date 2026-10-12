'use strict';

// Opt-in acceptance fixture. The starting version intentionally misclassifies
// failed proof; the approved one-file patch must correct that behavior.
function proofDisposition({ patchApplied, proofStatus } = {}) {
  if (patchApplied !== true) return 'not-applied';
  if (proofStatus === 'passed') return 'ready-for-acceptance';
  return 'replan';
}

module.exports = { proofDisposition };
