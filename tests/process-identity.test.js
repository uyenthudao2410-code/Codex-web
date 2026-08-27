'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
  POWERSHELL_OBSERVE_SCRIPT,
  normalizeProcessStartToken,
  observeProcessIdentity,
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
