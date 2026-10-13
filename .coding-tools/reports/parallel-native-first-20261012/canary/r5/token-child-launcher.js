'use strict';

// Intended top-level command: `node token-child-launcher.js`.
// The approved Node native process starts the static WinAPI probe with argv,
// no shell, and emits bounded non-identifying facts only.
const cp = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const probe = path.join(__dirname, 'token-child-probe.exe');
if (!fs.existsSync(probe) || !fs.statSync(probe).isFile()) {
  process.stderr.write('TOKEN_PROBE_BINARY_MISSING\n');
  process.exitCode = 2;
} else {
  const child = cp.spawnSync(probe, [], { encoding: 'utf8', windowsHide: true, timeout: 10000, shell: false });
  const rawStdout = String(child.stdout || '');
  if (Buffer.byteLength(rawStdout, 'utf8') > 4096) {
    process.stderr.write('TOKEN_PROBE_OUTPUT_TOO_LARGE\n');
    process.exitCode = 3;
    return;
  }
  const stdout = rawStdout.trim();
  const stderr = String(child.stderr || '').slice(0, 512);
  let facts = null;
  try { facts = JSON.parse(stdout); } catch (_) {}
  const report = {
    schema_version: 1,
    operation: 'native_child_token_winapi_probe',
    top_level_execution: 'node_native_approved',
    child_argv: [probe],
    shell: false,
    timeout_ms: 10000,
    child_status: child.status,
    child_signal: child.signal || null,
    child_error: child.error ? String(child.error.code || 'spawn_error') : null,
    child_facts: facts,
    stderr_empty: stderr.length === 0,
    stderr_sha256: crypto.createHash('sha256').update(stderr).digest('hex'),
  };
  process.stdout.write(`${JSON.stringify(report)}\n`);
  process.exitCode = Number.isInteger(child.status) ? child.status : 1;
}
