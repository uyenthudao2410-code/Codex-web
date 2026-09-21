const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { safeRemoveScratch } = require('../scripts/installed-recovery-smoke');

test('installed recovery smoke retries a transient Windows scratch-directory lock', (t) => {
  const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'webmcp-installed-recovery-test-'));
  const originalRmSync = fs.rmSync;
  let calls = 0;
  t.after(() => {
    fs.rmSync = originalRmSync;
    originalRmSync(scratch, { recursive: true, force: true, maxRetries: 3, retryDelay: 100 });
  });

  fs.rmSync = (target, options) => {
    calls += 1;
    if (calls < 3) {
      const error = new Error('transient Windows lock');
      error.code = 'EBUSY';
      throw error;
    }
    return originalRmSync(target, options);
  };

  safeRemoveScratch(scratch);

  assert.equal(calls, 3);
  assert.equal(fs.existsSync(scratch), false);
});
