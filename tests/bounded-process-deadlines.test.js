const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { EventEmitter } = require('node:events');

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

class FakeChild extends EventEmitter {
  constructor(onKill) {
    super();
    this.stdout = new EventEmitter();
    this.stderr = new EventEmitter();
    this.exitCode = null;
    this.signalCode = null;
    this.onKill = onKill;
  }

  kill() {
    return this.onKill?.(this) ?? true;
  }
}

function loadCommandRunner(spawnImpl) {
  const filename = path.join(__dirname, '..', 'electron', 'services', 'commandRunner.js');
  const source = fs.readFileSync(filename, 'utf8');
  const module = { exports: {} };
  const factory = vm.runInThisContext(
    `(function(require, module, exports, __filename, __dirname) {${source}\n})`,
    { filename }
  );
  const localRequire = (id) => id === 'node:child_process' ? { spawn: spawnImpl } : require(id);
  factory(localRequire, module, module.exports, filename, path.dirname(filename));
  return module.exports;
}

test('command timeout waits for owned child termination before rejecting', { timeout: 2_000 }, async () => {
  let child;
  const { run } = loadCommandRunner(() => {
    child = new FakeChild((owned) => {
      setTimeout(() => {
        owned.exitCode = 1;
        owned.signalCode = 'SIGTERM';
        owned.emit('close', 1, 'SIGTERM');
      }, 45);
      return true;
    });
    return child;
  });

  let settled = false;
  const pending = run('fake-owned-child', [], { timeoutMs: 5, timeoutCleanupMs: 200 })
    .finally(() => { settled = true; });

  await delay(20);
  assert.equal(settled, false, 'timeout must remain pending until owned child close/exit is observed');
  assert.equal(child.listenerCount('close') > 0, true);

  await assert.rejects(pending, (error) => {
    assert.equal(error.code, 'COMMAND_TIMEOUT');
    assert.equal(error.timedOut, true);
    assert.equal(error.cleanupConfirmed, true);
    assert.equal(error.cleanupOutcome, 'confirmed');
    return true;
  });
});

test('command timeout fails typed when cleanup cannot confirm owned child termination', { timeout: 2_000 }, async () => {
  const { run } = loadCommandRunner(() => new FakeChild(() => true));

  await assert.rejects(
    run('fake-stuck-child', [], { timeoutMs: 5, timeoutCleanupMs: 15 }),
    (error) => {
      assert.equal(error.code, 'COMMAND_TIMEOUT_CLEANUP_UNCERTAIN');
      assert.equal(error.timedOut, true);
      assert.equal(error.cleanupConfirmed, false);
      assert.equal(error.cleanupOutcome, 'unconfirmed');
      assert.equal(error.cleanupBudgetMs, 15);
      assert.equal(Object.hasOwn(error, 'stdout'), false);
      assert.equal(Object.hasOwn(error, 'stderr'), false);
      return true;
    }
  );
});

test('python discovery consumes one monotonic total budget across all probes', async () => {
  const { pythonStatus } = require('../electron/services/environmentService');
  let now = 0;
  const observedTimeouts = [];
  const calls = [];
  const paths = {
    portablePython: () => path.join(__dirname, 'definitely-missing-portable-python.exe')
  };
  const runFn = async (command, args, options) => {
    calls.push([command, ...args]);
    observedTimeouts.push(options.timeoutMs);
    now += 30;
    return { code: 0, stdout: '', stderr: '' };
  };

  const status = await pythonStatus(paths, {
    budgetMs: 100,
    monotonicNow: () => now,
    runFn,
    platform: 'win32'
  });

  assert.equal(status.installed, false);
  assert.equal(status.code, 'PYTHON_DISCOVERY_TIMEOUT');
  assert.equal(status.timedOut, true);
  assert.equal(status.budgetMs, 100);
  assert.deepEqual(observedTimeouts, [100, 70, 40, 10],
    'remaining timeout must decrease from one shared deadline instead of resetting per probe');
  assert.deepEqual(calls.map((call) => call.slice(0, 2)), [
    ['where.exe', 'py.exe'],
    ['where.exe', 'pyw.exe'],
    ['where.exe', 'python.exe'],
    ['where.exe', 'pythonw.exe']
  ]);
});

test('python discovery maps child cleanup uncertainty to typed bounded discovery timeout', async () => {
  const { pythonStatus } = require('../electron/services/environmentService');
  const paths = {
    portablePython: () => path.join(__dirname, 'definitely-missing-portable-python.exe')
  };
  const runFn = async () => {
    throw Object.assign(new Error('child cleanup not confirmed'), {
      code: 'COMMAND_TIMEOUT_CLEANUP_UNCERTAIN',
      timedOut: true,
      cleanupConfirmed: false
    });
  };

  const status = await pythonStatus(paths, {
    budgetMs: 50,
    monotonicNow: () => 1,
    runFn,
    platform: 'win32'
  });

  assert.equal(status.installed, false);
  assert.equal(status.code, 'PYTHON_DISCOVERY_TIMEOUT');
  assert.equal(status.timedOut, true);
  assert.equal(status.cleanupConfirmed, false);
  assert.equal(status.budgetMs, 50);
});

test('Ubuntu Python discovery avoids Windows-only commands and accepts python3', async () => {
  const { pythonStatus } = require('../electron/services/environmentService');
  const calls = [];
  const status = await pythonStatus({
    portablePython: () => path.join(__dirname, 'definitely-missing-portable-python.exe')
  }, {
    platform: 'linux',
    runFn: async (command, args) => {
      calls.push([command, ...args]);
      return { code: 0, stdout: 'Python 3.12.4', stderr: '' };
    }
  });

  assert.deepEqual(calls, [['python3', '--version']]);
  assert.deepEqual(status, {
    installed: true,
    command: 'python3',
    launchCommand: 'python3',
    prefixArgs: [],
    version: 'Python 3.12.4'
  });
});
