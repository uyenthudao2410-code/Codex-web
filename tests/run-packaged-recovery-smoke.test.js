const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const { runPackagedRecoverySmoke } = require('../scripts/run-packaged-recovery-smoke');

test('packaged recovery wrapper tests the exact fresh candidate after the icon and build gates', () => {
  const calls = [];
  const root = path.resolve(__dirname, '..');
  const environment = { CODEX_PACKAGED_APP_ROOT: path.join(root, 'dist', 'win-unpacked'), TEST_MARKER: 'preserved' };
  const status = runPackagedRecoverySmoke({
    root,
    candidateTag: 'recovery-fixture',
    nodeExecutable: 'test-node',
    environment,
    spawnSyncFn: (...args) => { calls.push(args); return { status: 0 }; }
  });

  assert.equal(status, 0);
  assert.deepEqual(calls.map(([executable, args]) => [executable, args]), [
    ['test-node', [path.join(root, 'scripts', 'generate-icon.js')]],
    ['test-node', [path.join(root, 'scripts', 'build-dev-candidate.js'), 'recovery-fixture']],
    ['test-node', [path.join(root, 'scripts', 'packaged-recovery-smoke.js')]]
  ]);
  assert.equal(calls[2][2].env.CODEX_PACKAGED_APP_ROOT,
    path.join(root, 'dist', 'windows-candidate-mxc-wsb-cbe1774-recovery-fixture', 'win-unpacked'));
  assert.equal(calls[2][2].env.TEST_MARKER, 'preserved');
  assert.equal(environment.CODEX_PACKAGED_APP_ROOT, path.join(root, 'dist', 'win-unpacked'));
  assert(calls.every(([, , options]) => options.cwd === root && options.windowsHide === true && !options.shell));
});

test('packaged recovery wrapper stops at a failed icon or build gate', () => {
  for (const failedStage of [0, 1]) {
    const calls = [];
    const status = runPackagedRecoverySmoke({
      candidateTag: 'recovery-fixture',
      spawnSyncFn: (_executable, args) => {
        calls.push(args);
        return { status: calls.length - 1 === failedStage ? 7 : 0 };
      }
    });
    assert.equal(status, 7);
    assert.equal(calls.length, failedStage + 1);
    assert(!calls.some(([script]) => path.basename(script) === 'packaged-recovery-smoke.js'));
  }
});

test('packaged recovery wrapper propagates smoke failure and treats a failed spawn as failure', () => {
  const result = (lastResult) => {
    let calls = 0;
    return runPackagedRecoverySmoke({
      spawnSyncFn: () => ++calls === 3 ? lastResult : { status: 0 }
    });
  };
  assert.equal(result({ status: 9 }), 9);
  assert.equal(result({ status: null, error: { code: 'ENOENT' } }), 1);
  assert.equal(result({ status: null, signal: 'SIGTERM' }), 1);
});

test('packaged recovery wrapper selects a new valid candidate tag for each run', () => {
  const tags = [];
  for (let run = 0; run < 2; run += 1) {
    assert.equal(runPackagedRecoverySmoke({
      spawnSyncFn: (_executable, args) => {
        if (path.basename(args[0]) === 'build-dev-candidate.js') tags.push(args[1]);
        return { status: 0 };
      }
    }), 0);
  }
  assert(tags.every(tag => /^recovery-[a-f0-9]{20}$/.test(tag)));
  assert.notEqual(tags[0], tags[1]);
});
