'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const REPORT = __dirname;
const hash = raw => crypto.createHash('sha256').update(raw).digest('hex');
const need = (condition, code) => { if (!condition) throw Object.assign(new Error(), { code }); };
function arg(name, required = true) {
  const values = process.argv.filter(value => value.startsWith('--' + name + '='));
  need(values.length === (required ? 1 : values.length ? 1 : 0), 'EXACT_INPUT_REQUIRED');
  return values.length ? values[0].slice(name.length + 3) : '';
}
try {
  const mode = arg('operation');
  need(['canary-audit', 'canary-stop'].includes(mode), 'EXACT_CANARY_OPERATION_REQUIRED');
  const manifestRaw = fs.readFileSync(path.join(REPORT, 'canary-controller-manifest.json'));
  need(hash(manifestRaw) === arg('manifest-sha256'), 'EXACT_HELPER_MANIFEST_REQUIRED');
  const manifest = JSON.parse(manifestRaw);
  for (const file of manifest.files) need(hash(fs.readFileSync(path.join(REPORT, file.path))) === file.sha256, 'HELPER_FILE_CHANGED');
  need(hash(fs.readFileSync(manifest.electron.executable)) === manifest.electron.sha256, 'ISOLATED_ELECTRON_BINARY_CHANGED');
  const argv = [path.join(REPORT, 'canary-controller-app'), '--user-data-dir=' + path.join(REPORT, 'canary-controller-profile'), '--operation=' + mode];
  if (mode === 'canary-stop') {
    need(process.argv.includes('--confirm-stop'), 'EXPLICIT_EXACT_STOP_REQUIRED');
    argv.push('--confirm-stop');
    for (const field of ['audit-receipt', 'audit-sha256', 'verification-receipt', 'verification-sha256']) argv.push('--' + field + '=' + arg(field));
  }
  const environment = { ...process.env };
  delete environment.ELECTRON_RUN_AS_NODE;
  const result = spawnSync(manifest.electron.executable, argv, { cwd: REPORT, env: environment, windowsHide: true,
    shell: false, timeout: 60000, encoding: 'utf8', maxBuffer: 16384 });
  const rows = String(result.stdout || '').split(/\r?\n/).map(line => { try { return JSON.parse(line); } catch { return null; } }).filter(Boolean);
  const valid = rows.filter(row => row.ok === true && row.operation === mode && row.secret_values_emitted === false);
  if (result.error || result.status !== 0 || valid.length !== 1) {
    const failure = rows.find(row => row.ok === false && row.secret_values_emitted === false);
    process.stdout.write(JSON.stringify({ ok: false, operation: mode,
      code: /^[A-Z0-9_]{3,96}$/.test(failure?.code || '') ? failure.code : 'ISOLATED_CANARY_CONTROLLER_FAILED',
      child_exit_code: result.status, raw_output_emitted: false, acceptance_performed: false,
      unknown_effect_not_replayed: true, secret_values_emitted: false }) + '\n');
    process.exitCode = 1;
  } else {
    const receipt = valid[0];
    need(path.dirname(receipt.report_path) === REPORT && hash(fs.readFileSync(receipt.report_path)) === receipt.report_sha256, 'EXACT_CONTROLLER_RECEIPT_REQUIRED');
    process.stdout.write(JSON.stringify(receipt) + '\n');
  }
} catch (error) {
  process.stdout.write(JSON.stringify({ ok: false, operation: 'canary_controller_preflight',
    code: /^[A-Z0-9_]{3,96}$/.test(error.code || '') ? error.code : 'CANARY_CONTROLLER_PREFLIGHT_FAILED',
    unknown_effect_not_replayed: true, acceptance_performed: false, secret_values_emitted: false }) + '\n');
  process.exitCode = 1;
}
