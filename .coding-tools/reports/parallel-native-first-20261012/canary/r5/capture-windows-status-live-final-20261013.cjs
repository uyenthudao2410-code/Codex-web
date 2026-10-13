'use strict';

// Read-only status capture through the already running Recovery Host.  The
// credential is read in memory and is never emitted; only bounded, non-secret
// runtime identity and readiness fields are retained as evidence.
const fs = require('node:fs');
const http = require('node:http');
const crypto = require('node:crypto');
const path = require('node:path');

const dataRoot = path.join(process.env.APPDATA, 'web-mcp-assistant');
const descriptorPath = path.join(dataRoot, 'recovery-host.json');
const outputPath = path.join(__dirname, 'windows-status-live-final-20261013.json');
if (fs.existsSync(outputPath)) throw new Error('STATUS_RECEIPT_EXISTS');
const descriptor = JSON.parse(fs.readFileSync(descriptorPath, 'utf8'));
if (!Number.isInteger(descriptor.port) || descriptor.port < 1 || descriptor.port > 65535
  || typeof descriptor.token !== 'string' || descriptor.token.length < 16) {
  throw new Error('RECOVERY_DESCRIPTOR_INVALID');
}

function call(action, args = []) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({ action, args });
    const req = http.request({
      host: '127.0.0.1', port: descriptor.port, path: '/v1/call', method: 'POST',
      headers: { Authorization: `Bearer ${descriptor.token}`, 'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body) }, timeout: 10_000,
    }, res => {
      let raw = '';
      res.setEncoding('utf8');
      res.on('data', chunk => { raw += chunk; if (Buffer.byteLength(raw) > 262144) req.destroy(new Error('RESPONSE_TOO_LARGE')); });
      res.on('end', () => {
        try {
          const value = JSON.parse(raw);
          if (res.statusCode !== 200 || value.ok !== true || !value.data || typeof value.data !== 'object') {
            reject(new Error('RECOVERY_CALL_FAILED'));
          } else resolve(value.data);
        } catch (error) { reject(error); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => req.destroy(new Error('RECOVERY_CALL_TIMEOUT')));
    req.end(body);
  });
}

function pick(value, keys) {
  return Object.fromEntries(keys.filter(key => value && Object.hasOwn(value, key)).map(key => [key, value[key]]));
}

(async () => {
  const ping = await call('recovery.ping');
  const activation = await call('runtime.activation_epoch_status');
  const runtime = await call('runtime.lightweight_snapshot');
  const recovery = await call('recovery.status', [{ fresh: true }]);
  const report = {
    schema_version: 1,
    operation: 'windows_status_live_readonly',
    observed_at_ms: Date.now(),
    candidate: 'E:\\DEV\\Codex-web\\dist\\windows-candidate-mxc-wsb-cbe1774-parallel-r4-timefix\\win-unpacked',
    ok: true,
    mutating: false,
    ping: pick(ping, ['ready', 'state', 'pid', 'process_start_token', 'instance_id', 'device_id', 'started_at']),
    activation: pick(activation, ['activation_epoch_id', 'state', 'epoch_state', 'admission_open', 'update_incomplete', 'ready_commit_digest', 'ready_at']),
    runtime: pick(runtime, ['workspace', 'mcpRunning', 'nativeAlive', 'executionRole', 'localReady', 'directReady', 'centralConnected', 'authorityReady', 'componentsReady', 'fullyReady', 'updateIncomplete', 'centralStatusReason', 'connectorReady', 'connectorContractState', 'connectorRefreshRequired', 'activationEpoch']),
    recovery: pick(recovery, ['state', 'pid', 'process_start_token', 'instance_id', 'device_id', 'telemetry_available', 'signal_stale', 'snapshot_observed_at_unix_ms', 'snapshot_age_ms', 'electron_ui_recovery', 'code_revision']),
    credential_emitted: false,
  };
  fs.writeFileSync(outputPath, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  process.stdout.write(JSON.stringify({ operation: report.operation, output: outputPath, ok: true }) + '\n');
})().catch(error => {
  process.stderr.write(`${error && error.message ? error.message : 'STATUS_CAPTURE_FAILED'}\n`);
  process.exitCode = 1;
});

