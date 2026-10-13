'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { classify, MAX_BYTES } = require('./discovery-gate-classifier.cjs');

const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'codex-discovery-gate-'));
const run = (name, receipt) => {
  const input = path.join(temp, `${name}-input.json`);
  const output = path.join(temp, `${name}-output.json`);
  fs.writeFileSync(input, JSON.stringify(receipt));
  const result = spawnSync(process.execPath, [
    path.join(__dirname, 'discovery-gate-classifier.cjs'), '--input', input, '--output', output
  ], { encoding: 'utf8' });
  return { result, output: fs.existsSync(output) ? JSON.parse(fs.readFileSync(output, 'utf8')) : null };
};

{
  const { output, result } = run('central', {
    runtime: {
      executionRole: 'central_executor', fullyReady: true, mcpRunning: true, nativeAlive: true,
      authorityReady: true, centralConnected: true, connectorContractState: 'CHANGED_NEEDS_DISCOVERY'
    },
    activation: { state: 'READY', admission_open: true }
  });
  assert.equal(result.status, 0);
  assert.equal(output.connector_applicability, 'not_applicable_central_executor');
  assert.equal(output.strict_discovery_required, false);
  assert.equal(output.central_runtime_ready, true);
  assert.equal(output.live_endpoint_called, false);
  assert.equal(output.runtime_mutated, false);
}

{
  const { output, result } = run('direct-pending', {
    runtime: {
      executionRole: 'direct_legacy', fullyReady: true, mcpRunning: true, nativeAlive: true,
      connectorContractState: 'CHANGED_NEEDS_DISCOVERY'
    },
    activation: { state: 'READY', admission_open: true }
  });
  assert.equal(result.status, 0);
  assert.equal(output.connector_applicability, 'direct_connector');
  assert.equal(output.strict_discovery_required, true);
  assert.match(output.recommendation, /attested current-process/);
}

{
  assert.throws(() => classify({ runtime: {} }), error => error.code === 'EXECUTION_ROLE_MISSING');
}

{
  const oversized = path.join(temp, 'oversized.json');
  fs.writeFileSync(oversized, JSON.stringify({ runtime: { executionRole: 'central_executor' } }) + ' '.repeat(MAX_BYTES));
  const output = path.join(temp, 'oversized-output.json');
  const result = spawnSync(process.execPath, [
    path.join(__dirname, 'discovery-gate-classifier.cjs'), '--input', oversized, '--output', output
  ], { encoding: 'utf8' });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /BOUNDED_RECEIPT_REQUIRED/);
}

process.stdout.write('discovery gate classifier tests: 4 passed\n');
