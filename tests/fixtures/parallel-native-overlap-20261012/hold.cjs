'use strict';
const assert = require('node:assert/strict');
assert.equal(process.platform, 'win32');
const workspace = "Codex-web";
const started_at_ms = Date.now();
const clock = process.hrtime.bigint();
setTimeout(() => {
  const duration_ms = Number(process.hrtime.bigint() - clock) / 1e6;
  console.log(JSON.stringify({marker:'PARALLEL_NATIVE_OVERLAP_V1',workspace,pid:process.pid,started_at_ms,finished_at_ms:Date.now(),duration_ms}));
}, 5000);
