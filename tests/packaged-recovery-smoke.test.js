const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { waitForRecoveryHostReady } = require('../scripts/packaged-recovery-smoke');

test('packaged recovery smoke retries descriptor-visible host startup until recovery.ping is ready', async () => {
  let calls = 0;
  let now = 0;
  const ping = await waitForRecoveryHostReady({}, {
    timeoutMs: 100,
    retryDelayMs: 10,
    nowFn: () => now,
    waitFn: async (delay) => { now += delay; },
    pingFn: async () => {
      calls += 1;
      if (calls < 3) throw new Error('temporary startup race');
      return { ok: true, data: { ready: true } };
    }
  });

  assert.equal(calls, 3);
  assert.deepEqual(ping, { ok: true, data: { ready: true } });
});

test('packaged contract probe runs Python without creating bytecode in the inspected package', () => {
  const source = fs.readFileSync(path.join(__dirname, '..', 'scripts', 'packaged-recovery-smoke.js'), 'utf8');
  assert.match(source, /spawnSync\(packagedPython, \['-I', '-B', '-c', probe, packagedMcpRoot\]/);
});
