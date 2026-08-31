'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const { PassThrough } = require('node:stream');

const {
  POWERSHELL_BROKER_SCRIPT,
  POWERSHELL_OBSERVE_SCRIPT,
  createWindowsIdentityBroker,
  normalizeProcessStartToken,
  observeProcessIdentity,
  observeProcessIdentityAsync,
  terminateExactProcessTree,
  waitForExactProcessExit
} = require('../electron/services/processIdentity');

const WINDOWS_ONLY = { skip: process.platform !== 'win32' };
const PID = 42_424;
const START_TOKEN = '133801234567890123';
const REPLACEMENT_TOKEN = '133801234567890999';

function live(processStartToken = START_TOKEN) {
  return { state: 'live', pid: PID, process_start_token: processStartToken };
}

function brokerHarness({ responseFor, writeError = null } = {}) {
  const calls = [];
  const writes = [];
  const children = [];
  const spawn = (command, args, options) => {
    calls.push({ command, args, options });
    const child = new EventEmitter();
    child.killed = false;
    child.killCalls = 0;
    child.refCalls = 0;
    child.unrefCalls = 0;
    child.stdout = new PassThrough();
    child.stdout.refCalls = 0;
    child.stdout.unrefCalls = 0;
    child.stdout.ref = () => { child.stdout.refCalls += 1; };
    child.stdout.unref = () => { child.stdout.unrefCalls += 1; };
    child.stdin = new EventEmitter();
    child.stdin.destroyed = false;
    child.stdin.refCalls = 0;
    child.stdin.unrefCalls = 0;
    child.stdin.ref = () => { child.stdin.refCalls += 1; };
    child.stdin.unref = () => { child.stdin.unrefCalls += 1; };
    child.stdin.end = () => { child.stdin.destroyed = true; };
    child.stdin.write = (chunk, callback) => {
      if (writeError) throw writeError;
      const text = Buffer.isBuffer(chunk) ? chunk.toString('utf8') : String(chunk);
      writes.push(text.trim());
      const request = JSON.parse(text);
      queueMicrotask(() => {
        const response = responseFor?.(request);
        if (response === null || response === undefined) return;
        const output = typeof response === 'string' ? response : JSON.stringify(response);
        child.stdout.write(`${output}\n`);
      });
      callback?.(null);
      return true;
    };
    child.ref = () => { child.refCalls += 1; };
    child.unref = () => { child.unrefCalls += 1; };
    child.kill = () => {
      child.killCalls += 1;
      child.killed = true;
      return true;
    };
    children.push(child);
    return child;
  };
  return { calls, writes, children, spawn };
}

test('process start tokens wider than Number.MAX_SAFE_INTEGER remain canonical strings', () => {
  const token = (BigInt(Number.MAX_SAFE_INTEGER) + 12_345_678_901_234n).toString(10);
  assert.equal(normalizeProcessStartToken(token), token);
  assert.equal(normalizeProcessStartToken(BigInt(token)), token);

  const observed = observeProcessIdentity(PID, { observe: () => token });
  assert.deepEqual(observed, { state: 'live', pid: PID, process_start_token: token });
  assert.equal(typeof observed.process_start_token, 'string');
});

test('observation with an explicit different PID is unavailable', () => {
  const observed = observeProcessIdentity(PID, {
    observe: () => ({ ...live(), pid: PID + 1 })
  });

  assert.equal(observed.state, 'unavailable');
  assert.equal(observed.code, 'PROCESS_IDENTITY_UNVERIFIED');
  assert.equal(observed.pid, PID);
  assert.equal(observed.process_start_token, null);
});

test('Windows probe treats empty, malformed, multiline, and oversized output as unavailable', WINDOWS_ONLY, async (t) => {
  const cases = [
    { name: 'empty', stdout: '' },
    { name: 'malformed', stdout: 'not-a-filetime' },
    { name: 'multiline', stdout: '133801234567890123\n133801234567890124' },
    { name: 'oversized', stdout: '9'.repeat(513), reason: 'probe_output_too_large' }
  ];

  for (const item of cases) {
    await t.test(item.name, () => {
      const observed = observeProcessIdentity(PID, {
        noCache: true,
        spawnSync: () => ({ status: 0, stdout: item.stdout })
      });
      assert.equal(observed.state, 'unavailable');
      assert.equal(observed.code, 'PROCESS_IDENTITY_UNVERIFIED');
      assert.equal(observed.pid, PID);
      assert.equal(observed.process_start_token, null);
      if (item.reason) assert.equal(observed.details.reason, item.reason);
    });
  }
});

test('exact Windows identity reaches one structured taskkill invocation', WINDOWS_ONLY, async () => {
  const calls = [];
  let observations = 0;
  const result = await terminateExactProcessTree(
    { pid: PID, process_start_token: START_TOKEN },
    {
      observeProcessIdentity: async () => {
        observations += 1;
        return observations === 1 ? live() : { state: 'absent', pid: PID };
      },
      runProcess: async (command, args, options) => {
        calls.push({ command, args, options });
        return { code: 0 };
      },
      sleep: async () => {
        throw new Error('sleep must not run after the exact process is already absent');
      }
    }
  );

  assert.equal(calls.length, 1);
  assert.equal(calls[0].command, 'taskkill.exe');
  assert.deepEqual(calls[0].args, ['/PID', String(PID), '/T', '/F']);
  assert.deepEqual(calls[0].options, { allowFailure: true });
  assert.equal(result.state, 'terminated');
  assert.equal(result.exit_state, 'exited');
  assert.equal(observations, 2);
});

test('same PID with a different start token never reaches taskkill', WINDOWS_ONLY, async () => {
  let taskkillCalls = 0;
  await assert.rejects(
    terminateExactProcessTree(
      { pid: PID, process_start_token: START_TOKEN },
      {
        observeProcessIdentity: async () => live(REPLACEMENT_TOKEN),
        runProcess: async () => {
          taskkillCalls += 1;
          return { code: 0 };
        }
      }
    ),
    { code: 'PROCESS_IDENTITY_CHANGED' }
  );
  assert.equal(taskkillCalls, 0);
});

test('unavailable identity observation never reaches taskkill', WINDOWS_ONLY, async () => {
  let taskkillCalls = 0;
  await assert.rejects(
    terminateExactProcessTree(
      { pid: PID, process_start_token: START_TOKEN },
      {
        observeProcessIdentity: async () => ({
          state: 'unavailable',
          pid: PID,
          code: 'PROCESS_IDENTITY_UNVERIFIED'
        }),
        runProcess: async () => {
          taskkillCalls += 1;
          return { code: 0 };
        }
      }
    ),
    { code: 'PROCESS_IDENTITY_UNVERIFIED' }
  );
  assert.equal(taskkillCalls, 0);
});

test('post-taskkill replacement token proves the original exited without a second kill', WINDOWS_ONLY, async () => {
  let observations = 0;
  let taskkillCalls = 0;
  const result = await terminateExactProcessTree(
    { pid: PID, process_start_token: START_TOKEN },
    {
      observeProcessIdentity: async () => {
        observations += 1;
        return observations === 1 ? live() : live(REPLACEMENT_TOKEN);
      },
      runProcess: async () => {
        taskkillCalls += 1;
        return { code: 128 };
      },
      sleep: async () => {
        throw new Error('a recycled PID must not enter the exit wait');
      }
    }
  );

  assert.equal(result.state, 'already_exited');
  assert.equal(result.observed.process_start_token, REPLACEMENT_TOKEN);
  assert.equal(taskkillCalls, 1);
  assert.equal(observations, 2);
});

test('exact exit wait returns immediately when the PID has been recycled', async () => {
  let observations = 0;
  let sleeps = 0;
  const result = await waitForExactProcessExit(
    { pid: PID, process_start_token: START_TOKEN },
    {
      observeProcessIdentity: async () => {
        observations += 1;
        return live(REPLACEMENT_TOKEN);
      },
      sleep: async () => {
        sleeps += 1;
      },
      timeoutMs: 1_000
    }
  );

  assert.equal(result.state, 'replaced');
  assert.equal(result.observed.process_start_token, REPLACEMENT_TOKEN);
  assert.equal(observations, 1);
  assert.equal(sleeps, 0);
});

test('Windows observation uses fixed PowerShell command, structured argv, and bounded launch options', WINDOWS_ONLY, () => {
  const calls = [];
  const observed = observeProcessIdentity(PID, {
    noCache: true,
    timeoutMs: 1_234,
    spawnSync: (command, args, options) => {
      calls.push({ command, args, options });
      return { status: 0, stdout: START_TOKEN };
    }
  });

  assert.deepEqual(observed, live());
  assert.equal(calls.length, 1);
  const [{ command, args, options }] = calls;
  assert.equal(command, 'powershell.exe');
  assert.equal(Array.isArray(args), true);
  assert.deepEqual(args.slice(0, 6), [
    '-NoLogo',
    '-NoProfile',
    '-NonInteractive',
    '-ExecutionPolicy',
    'Bypass',
    '-Command'
  ]);
  assert.equal(args[6], POWERSHELL_OBSERVE_SCRIPT);
  assert.match(POWERSHELL_OBSERVE_SCRIPT, /Get-Process -Id \$processId/);
  assert.match(POWERSHELL_OBSERVE_SCRIPT, /\$creation % 10/);
  assert.doesNotMatch(POWERSHELL_OBSERVE_SCRIPT, /Get-CimInstance|Win32_Process/);
  assert.equal(args[7], String(PID));
  assert.equal(args.length, 8);
  assert.equal(options.shell, false);
  assert.equal(options.windowsHide, true);
  assert.equal(options.timeout, 1_234);
  assert.equal(options.maxBuffer, 512);
  assert.deepEqual(options.stdio, ['ignore', 'pipe', 'ignore']);
});

test('asynchronous Windows observation uses a fixed hidden broker command and structured PID frame', async () => {
  const harness = brokerHarness({
    responseFor: (request) => ({
      id: request.id,
      pid: request.pid,
      state: 'live',
      process_start_token: START_TOKEN
    })
  });
  const observed = await observeProcessIdentityAsync(PID, {
    platform: 'win32',
    noCache: true,
    timeoutMs: 1_234,
    spawn: harness.spawn
  });

  assert.deepEqual(observed, live());
  assert.equal(harness.calls.length, 1);
  const [{ command, args, options }] = harness.calls;
  assert.equal(command, 'powershell.exe');
  assert.deepEqual(args.slice(0, 6), [
    '-NoLogo',
    '-NoProfile',
    '-NonInteractive',
    '-ExecutionPolicy',
    'Bypass',
    '-Command'
  ]);
  assert.equal(args[6], POWERSHELL_BROKER_SCRIPT);
  assert.equal(args.length, 7);
  assert.doesNotMatch(args.join(' '), new RegExp(String(PID)));
  assert.match(POWERSHELL_BROKER_SCRIPT, /ReadLine/);
  assert.match(POWERSHELL_BROKER_SCRIPT, /ConvertFrom-Json/);
  assert.equal(options.shell, false);
  assert.equal(options.windowsHide, true);
  assert.deepEqual(options.stdio, ['pipe', 'pipe', 'ignore']);
  assert.deepEqual(JSON.parse(harness.writes[0]), { id: 1, pid: PID });
});

test('persistent Windows identity broker reuses one child and unreferences idle handles', async () => {
  const harness = brokerHarness({
    responseFor: (request) => ({
      id: request.id,
      pid: request.pid,
      state: 'live',
      process_start_token: START_TOKEN
    })
  });
  const broker = createWindowsIdentityBroker({ spawnProcess: harness.spawn });
  try {
    const first = await observeProcessIdentityAsync(PID, { platform: 'win32', noCache: true, broker });
    const second = await observeProcessIdentityAsync(PID, { platform: 'win32', noCache: true, broker });
    assert.deepEqual(first, live());
    assert.deepEqual(second, live());
    assert.equal(harness.calls.length, 1);
    assert.deepEqual(harness.writes.map((item) => JSON.parse(item)), [
      { id: 1, pid: PID },
      { id: 2, pid: PID }
    ]);
    const child = harness.children[0];
    assert.ok(child.unrefCalls > 0);
    assert.ok(child.stdin.unrefCalls > 0);
    assert.ok(child.stdout.unrefCalls > 0);
  } finally {
    broker.close();
  }
});

test('persistent Windows identity broker fails closed on spawn, pipe, output, and timeout failures', async (t) => {
  await t.test('spawn failure', async () => {
    const broker = createWindowsIdentityBroker({
      spawnProcess: () => { throw Object.assign(new Error('missing broker'), { code: 'ENOENT' }); }
    });
    const observed = await broker.observe(PID, { timeoutMs: 100 });
    assert.equal(observed.state, 'unavailable');
    assert.equal(observed.details.reason, 'broker_spawn_failed');
    assert.equal(observed.details.cause_code, 'ENOENT');
  });

  await t.test('pipe failure', async () => {
    const harness = brokerHarness({
      responseFor: () => null,
      writeError: Object.assign(new Error('broken pipe'), { code: 'EPIPE' })
    });
    const broker = createWindowsIdentityBroker({ spawnProcess: harness.spawn });
    try {
      const observed = await broker.observe(PID, { timeoutMs: 100 });
      assert.equal(observed.state, 'unavailable');
      assert.equal(observed.details.reason, 'broker_pipe_write_failed');
      assert.equal(observed.details.cause_code, 'EPIPE');
      assert.equal(harness.children[0].killCalls, 1);
    } finally {
      broker.close();
    }
  });

  await t.test('malformed output', async () => {
    const harness = brokerHarness({ responseFor: () => 'not-json' });
    const broker = createWindowsIdentityBroker({ spawnProcess: harness.spawn });
    try {
      const observed = await broker.observe(PID, { timeoutMs: 100 });
      assert.equal(observed.state, 'unavailable');
      assert.equal(observed.details.reason, 'probe_protocol_invalid');
      assert.equal(harness.children[0].killCalls, 1);
    } finally {
      broker.close();
    }
  });

  await t.test('oversized output', async () => {
    const harness = brokerHarness({ responseFor: () => '9'.repeat(5_000) });
    const broker = createWindowsIdentityBroker({ spawnProcess: harness.spawn });
    try {
      const observed = await broker.observe(PID, { timeoutMs: 100 });
      assert.equal(observed.state, 'unavailable');
      assert.equal(observed.details.reason, 'probe_output_too_large');
      assert.equal(harness.children[0].killCalls, 1);
    } finally {
      broker.close();
    }
  });

  await t.test('timeout', async () => {
    const harness = brokerHarness({ responseFor: () => null });
    const broker = createWindowsIdentityBroker({ spawnProcess: harness.spawn });
    try {
      const observed = await broker.observe(PID, { timeoutMs: 100 });
      assert.equal(observed.state, 'unavailable');
      assert.equal(observed.details.reason, 'probe_timeout');
      assert.equal(harness.children[0].killCalls, 1);
    } finally {
      broker.close();
    }
  });
});
