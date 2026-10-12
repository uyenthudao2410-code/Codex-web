'use strict';
// Prepare a tiny Electron app; do not launch it or read credentials.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const repo = 'E:\\Github\\Tools-Codex-web', hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const appDir = path.join(__dirname, 'output-reader-app'); fs.mkdirSync(appDir, { recursive: true });
let s = fs.readFileSync(path.join(__dirname, '../../candidate-r13/canary-5h/native-output-read.cjs'), 'utf8')
  .replaceAll('\r\n', '\n').replaceAll('r13_5h', 'r14_same_window').replaceAll('R13_5H', 'R14_SAME_WINDOW')
  .replace('const HERE = __dirname;', 'const HERE = path.resolve(__dirname, "..");')
  .replace('source-fingerprint-1012-r13', 'workflow-timeout-1012-r14');
s = s.replace("proof?.proof_status === 'passed' && proof.plan_sha256", "['passed', 'failed', 'timed_out'].includes(proof?.proof_status) && proof.plan_sha256")
  .replace('HEX.test(proof.proof_fingerprint)', "(proof.proof_status === 'passed' ? HEX.test(proof.proof_fingerprint) : proof.proof_fingerprint === null)")
  .replace('proof.proof_ids.length > 0', "(proof.proof_status !== 'passed' || proof.proof_ids.length > 0)")
  .replace("&& summary.wave_id !== 'c101beadfc6d4f2fbc13845052c84693'", "&& summary.wave_id !== 'c101beadfc6d4f2fbc13845052c84693'\n    && summary.run_id !== 'fbaf4b0700d04794af4062671c1bcd2b' && summary.wave_id !== 'e712eca9463e465fb1905264c998f50c'");
const profileStart = s.indexOf("  const selected = app.commandLine.getSwitchValue('user-data-dir');"), profileEnd = s.indexOf("  const observationFile =", profileStart);
if (profileStart < 0 || profileEnd < 0) throw new Error('ISOLATED_APP_PROFILE_ANCHOR_MISSING');
s = s.slice(0, profileStart) + `  const isolated = path.join(HERE, 'output-reader-profile');
  const selected = app.commandLine.getSwitchValue('user-data-dir');
  need(selected && equalPath(selected, isolated), 'EXPLICIT_ISOLATED_READER_PROFILE_REQUIRED');
  need(!equalPath(isolated, PROFILE), 'PRODUCT_PROFILE_LOCK_REJECTED');
  app.setPath('userData', isolated); app.setPath('sessionData', path.join(isolated, 'session-data'));
  fs.mkdirSync(path.join(isolated, 'session-data'), { recursive: true });
  await app.whenReady();
` + s.slice(profileEnd);
const streamsStart = s.indexOf('  const streams = {};'), streamsEnd = s.indexOf('  const receipt =', streamsStart);
if (streamsStart < 0 || streamsEnd < 0) throw new Error('OUTPUT_CAPTURE_ANCHOR_MISSING');
s = s.slice(0, streamsStart) + `  const invoke = async (label, arguments_) => {
    const id = 'r14-output-' + label + '-' + Date.now();
    const response = await requestJson(settings.mcpPort, token, 'POST', '/mcp', {
      jsonrpc: '2.0', id, method: 'tools/call', params: { name: 'command_control', arguments: arguments_,
        _meta: { 'io.modelcontextprotocol/protocolVersion': '2026-07-28', 'io.modelcontextprotocol/clientCapabilities': {},
          'io.modelcontextprotocol/clientInfo': { name: CLIENT_ID, version: '1' } } } });
    need(response.id === id && !response.error && response.result?.isError !== true, 'NATIVE_COMMAND_READ_REJECTED');
    return response.result?.structuredContent;
  };
  need(Date.now() - completedAtMs < 300000, 'NATIVE_OUTPUT_RETENTION_WINDOW_EXPIRED');
  const [poll, stdout, stderr] = await Promise.all([
    invoke('poll', { action: 'poll', command_id: proof.command_id, consumer_id: CLIENT_ID, yield_time_ms: 0,
      max_output_bytes: 1, verbosity: 'summary' }),
    invoke('stdout', { action: 'read', output_ref: 'command:' + proof.command_id + ':stdout', stream: 'stdout', offset: 0, limit: 32768 }),
    invoke('stderr', { action: 'read', output_ref: 'command:' + proof.command_id + ':stderr', stream: 'stderr', offset: 0, limit: 32768 })
  ]);
  need((poll?.command_id || poll?.session_id) === proof.command_id
    && (poll?.execution_owner?.job_id || poll?.managed_job?.job_id || poll?.job_id) === proof.job_id
    && ['exited', 'timeout', 'terminated', 'reconciled_terminal'].includes(poll?.status), 'EXACT_NATIVE_COMMAND_JOB_TERMINAL_REQUIRED');
  const streams = { stdout: safePage(stdout, proof.command_id, 'stdout'), stderr: safePage(stderr, proof.command_id, 'stderr') };
  need(streams.stdout.total_stream_bytes + streams.stderr.total_stream_bytes <= 32768
    && !streams.stdout.content.includes(token) && !streams.stderr.content.includes(token), 'PRIVATE_OR_OVERSIZED_OUTPUT_REJECTED');
  let tap = null;
  if (proof.proof_status === 'passed') { need(poll.exit_code === 0 && streams.stderr.content === '', 'PASSED_PROOF_EXIT_OR_STDERR_CONFLICT'); tap = checkerTap(streams.stdout); }
` + s.slice(streamsEnd);
s = s.replace("stdout: streams.stdout, stderr: streams.stderr, tap, remote_mutation: false", "proof_status: proof.proof_status, native_command_status: poll.status, native_exit_code: poll.exit_code ?? null,\n    stdout: streams.stdout, stderr: streams.stderr, tap, remote_mutation: false")
  .replace("  process.noAsar = true;", "  process.noAsar = true;\n  const watchdog = setTimeout(() => { process.stdout.write(JSON.stringify({ ok: false, phase: 'native_canary_output_failed', code: 'OUTPUT_READER_26S_DEADLINE', secret_values_emitted: false }) + '\\n'); process.exit(2); }, 26000);\n  watchdog.unref();");
fs.writeFileSync(path.join(appDir, 'capture.cjs'), s, { flag: 'wx' });
fs.writeFileSync(path.join(appDir, 'package.json'), JSON.stringify({ name: 'r14-canary-output-reader', version: '1.0.0', main: 'capture.cjs', private: true }, null, 2) + '\n', { flag: 'wx' });
const binary = path.join(repo, 'node_modules/electron/dist/electron.exe');
fs.writeFileSync(path.join(__dirname, 'output-reader-binary-pin.json'), JSON.stringify({ executable: binary, sha256: hash(fs.readFileSync(binary)),
  product_bootstrap: false, windows_opened: false, binary_executed: false, credentials_read: false }, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify({ prepared: 'output-reader-app', executed: false, credentials_read: false }) + '\n');
