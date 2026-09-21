const test = require('node:test');
const assert = require('node:assert/strict');
const { resolvePythonExecutable } = require('./helpers/python-executable');

test('uses an explicit Python interpreter without trying another command', () => {
  const calls = [];
  const resolved = resolvePythonExecutable({
    environment: { PYTHON: 'chosen-python' },
    platform: 'linux',
    probe: (executable, argumentsList) => {
      calls.push([executable, argumentsList]);
      return { status: 0 };
    }
  });

  assert.equal(resolved, 'chosen-python');
  assert.deepEqual(calls, [['chosen-python', ['--version']]]);
});

test('falls back from a missing Ubuntu python3 command to python', () => {
  const calls = [];
  const resolved = resolvePythonExecutable({
    environment: {},
    platform: 'linux',
    probe: (executable) => {
      calls.push(executable);
      return executable === 'python3'
        ? { error: { code: 'ENOENT' } }
        : { status: 0 };
    }
  });

  assert.equal(resolved, 'python');
  assert.deepEqual(calls, ['python3', 'python']);
});

test('does not hide a non-missing Python probe failure behind a fallback', () => {
  assert.throws(() => resolvePythonExecutable({
    environment: {},
    platform: 'linux',
    probe: () => ({ status: 1 })
  }), /Python interpreter probe failed: python3/);
});

test('reports clearly when no supported Python command exists', () => {
  assert.throws(() => resolvePythonExecutable({
    environment: {},
    platform: 'win32',
    probe: () => ({ error: { code: 'ENOENT' } })
  }), /Python 3 interpreter is unavailable/);
});
