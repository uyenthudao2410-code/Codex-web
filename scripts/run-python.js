#!/usr/bin/env node
"use strict";

// Delivery tooling must work on both supported host conventions: Ubuntu often
// exposes only `python3`, while the Windows package/test hosts expose `python`.
// Fall back only when an interpreter is missing; a real script failure remains
// the script's own exit status and is never retried under another interpreter.

const { spawnSync } = require('node:child_process');

const invocation = process.argv.slice(2);
let pythonArguments;

if (invocation[0] === '--module') {
  const moduleName = invocation[1];
  if (!moduleName || moduleName.startsWith('-')) {
    process.stderr.write('run-python --module requires a module name\n');
    process.exit(2);
  }
  pythonArguments = ['-m', moduleName, ...invocation.slice(2)];
} else {
  const [script, ...argumentsList] = invocation;
  if (!script) {
    process.stderr.write('run-python requires a script path or --module name\n');
    process.exit(2);
  }
  pythonArguments = [script, ...argumentsList];
}

const candidates = process.platform === 'win32'
  ? ['python', 'py']
  : ['python3', 'python'];

for (const interpreter of candidates) {
  const result = spawnSync(interpreter, pythonArguments, {
    env: process.env,
    stdio: 'inherit'
  });
  if (result.error?.code === 'ENOENT') continue;
  if (result.error) {
    process.stderr.write(`unable to start ${interpreter}: ${result.error.code || 'unknown'}\n`);
    process.exit(1);
  }
  if (result.signal) {
    process.kill(process.pid, result.signal);
    process.exit(1);
  }
  process.exit(typeof result.status === 'number' ? result.status : 1);
}

process.stderr.write('Python 3 interpreter is unavailable\n');
process.exit(127);
