const test = require('node:test');
const assert = require('node:assert/strict');
const { RuntimeOrchestrator } = require('../electron/services/runtimeOrchestrator');

function probeOrchestrator(gitStatusRunFn) {
  const warns = [];
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({}) },
    secrets: { get: () => '' },
    environment: {},
    log: {
      info() {},
      warn(message, details) { warns.push({ message, details }); },
      error() {}
    },
    emitProgress() {},
    gitStatusRunFn
  });
  return { orchestrator, warns };
}

const UNAVAILABLE = { available: false, branch: null, head: null, head_short: null, dirty: null };

test('git status probe returns unavailable and logs the spawn cause on ENOENT', async () => {
  let seenOptions = null;
  const { orchestrator, warns } = probeOrchestrator(async (command, args, options) => {
    seenOptions = options;
    throw Object.assign(new Error('spawn git ENOENT'), { code: 'ENOENT' });
  });
  assert.deepEqual(await orchestrator._probeGitStatus('C:\\work\\one'), UNAVAILABLE);
  assert.equal(seenOptions.timeoutMs, 10_000, 'the probe must allow 10 s, not 2 s');
  assert.equal(warns.length, 1, 'a failed probe must log exactly one warning');
  assert.equal(warns[0].message, 'Git status probe failed');
  assert.equal(warns[0].details.cause_code, 'ENOENT');
  assert.equal(warns[0].details.timed_out, false);
  assert.equal(typeof warns[0].details.git_command, 'string');
  assert.ok(warns[0].details.git_command.length > 0);
});

test('git status probe returns unavailable and logs the timeout flag on timeout', async () => {
  const { orchestrator, warns } = probeOrchestrator(async () => {
    throw Object.assign(new Error('Command execution timed out (10000 ms)'), {
      code: 'COMMAND_TIMEOUT',
      stdout: '',
      stderr: 'fatal: timeout tail',
      timedOut: true,
      timeoutMs: 10_000
    });
  });
  assert.deepEqual(await orchestrator._probeGitStatus('C:\\work\\one'), UNAVAILABLE);
  assert.equal(warns.length, 1, 'a failed probe must log exactly one warning');
  assert.equal(warns[0].details.cause_code, 'COMMAND_TIMEOUT');
  assert.equal(warns[0].details.timed_out, true);
  assert.equal(warns[0].details.stderr_tail, 'fatal: timeout tail');
});
