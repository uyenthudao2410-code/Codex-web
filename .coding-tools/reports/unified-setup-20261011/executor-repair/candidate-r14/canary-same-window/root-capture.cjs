'use strict';
// Root invokes this only after the NEW canary settles; preparation never launches it.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const hash = raw => crypto.createHash('sha256').update(raw).digest('hex');
const need = (ok, code) => { if (!ok) throw Object.assign(new Error(), { code }); };
function arg(name) { const values = process.argv.filter(v => v.startsWith('--' + name + '=')); need(values.length === 1, 'EXACT_PUBLIC_PIN_REQUIRED'); return values[0].slice(name.length + 3); }
function main() {
  need(process.argv.includes('--capture-new-canary-output'), 'EXPLICIT_OUTPUT_CAPTURE_REQUIRED');
  const manifestRaw = fs.readFileSync(path.join(__dirname, 'helper-manifest.json'));
  need(hash(manifestRaw) === arg('manifest-sha256'), 'CANARY_HELPER_MANIFEST_CHANGED');
  const manifest = JSON.parse(manifestRaw);
  for (const row of manifest.files) need(hash(fs.readFileSync(path.join(__dirname, row.path))) === row.sha256, 'CANARY_HELPER_FILE_CHANGED');
  const pin = JSON.parse(fs.readFileSync(path.join(__dirname, 'output-reader-binary-pin.json')));
  need(hash(fs.readFileSync(pin.executable)) === pin.sha256, 'ISOLATED_ELECTRON_BINARY_CHANGED');
  const completedAt = Number(arg('completed-at-ms'));
  need(Number.isSafeInteger(completedAt) && completedAt <= Date.now() && Date.now() - completedAt < 300000, 'OUTPUT_RETENTION_WINDOW_EXPIRED_NO_RERUN');
  const receipt = path.join(__dirname, 'native-output-' + new Date().toISOString().replace(/[^0-9TZ]/g, '') + '.json');
  need(!fs.existsSync(receipt), 'NEW_EXCLUSIVE_OUTPUT_RECEIPT_REQUIRED');
  const env = { ...process.env }; delete env.ELECTRON_RUN_AS_NODE;
  const argv = [path.join(__dirname, 'output-reader-app'), '--user-data-dir=' + path.join(__dirname, 'output-reader-profile'),
    '--observation=' + arg('observation'), '--observation-sha256=' + arg('observation-sha256'),
    '--pins=' + arg('pins'), '--pins-sha256=' + arg('pins-sha256'), '--completed-at-ms=' + completedAt, '--receipt=' + receipt];
  const result = spawnSync(pin.executable, argv, { env, cwd: __dirname, windowsHide: true, shell: false,
    timeout: 30000, encoding: 'utf8', maxBuffer: 16384 });
  // Never echo diagnostic stderr, arbitrary stdout or raw errors from Electron.
  const lines = String(result.stdout || '').trim().split(/\r?\n/).filter(Boolean);
  const values = lines.map(line => { try { return JSON.parse(line); } catch { return null; } }).filter(Boolean);
  const rows = values.filter(v => v.phase === 'native_canary_output_capture' && v.ok === true && v.secret_values_emitted === false);
  if (result.error || result.status !== 0 || rows.length !== 1 || !fs.existsSync(receipt)) {
    process.stdout.write(JSON.stringify({ ok: false, phase: 'root_output_capture_failed', code: result.error?.code === 'ETIMEDOUT' ? 'ISOLATED_READER_30S_TIMEOUT' : 'ISOLATED_READER_FAILED',
      output_receipt_exists: fs.existsSync(receipt), raw_stderr_emitted: false, raw_stdout_emitted: false,
      canary_replayed: false, checker_rerun: false, acceptance_performed: false }) + '\n'); process.exitCode = 2; return;
  }
  const row = rows[0]; need(row.receipt_path === receipt && row.receipt_sha256 === hash(fs.readFileSync(receipt)), 'OUTPUT_RECEIPT_IDENTITY_CHANGED');
  process.stdout.write(JSON.stringify({ ok: true, phase: 'root_output_capture_complete', receipt_path: receipt,
    receipt_sha256: row.receipt_sha256, command_id: row.command_id, job_id: row.job_id, run_id: row.run_id, wave_id: row.wave_id,
    tap: row.tap, raw_stderr_emitted: false, credentials_emitted: false, product_bootstrap: false, child_exit_code: result.status }) + '\n');
}
if (require.main === module) { try { main(); } catch (error) { process.stdout.write(JSON.stringify({ ok: false, phase: 'root_output_capture_refused',
  code: String(error.code || 'OUTPUT_CAPTURE_REFUSED').replace(/[^A-Z0-9_]/g, ''), credentials_emitted: false, canary_replayed: false }) + '\n'); process.exitCode = 2; } }
