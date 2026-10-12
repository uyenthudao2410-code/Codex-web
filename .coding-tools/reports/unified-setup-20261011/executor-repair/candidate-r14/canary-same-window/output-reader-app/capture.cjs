'use strict';
// Root-only credential reader. No native runtime, agent, VM or acceptance is started.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const http = require('node:http');
const HERE = path.resolve(__dirname, "..");
const REPO = path.resolve(HERE, '../../../../../..');
const PROFILE = 'C:\\Users\\daoth\\AppData\\Roaming\\web-mcp-assistant';
const CANDIDATE = path.join(REPO, 'dist/windows-candidate-mxc-wsb-cbe1774-workflow-timeout-1012-r14/win-unpacked');
const NATIVE_SHA = '0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4';
const PLAN_SHA = '235ecd2dc1bf8b49b21648ffd24df378088916e65e2420cb383fa79a6439afe7';
const CLIENT_ID = 'electron-r14_same_window-canary-output-reader';
const hash = raw => crypto.createHash('sha256').update(raw).digest('hex');
const need = (value, code) => { if (!value) throw Object.assign(new Error(), { code }); };
const equalPath = (a, b) => path.resolve(a).toLowerCase() === path.resolve(b).toLowerCase();
const HEX = /^[a-f0-9]{64}$/;

function arg(name) {
  const matches = process.argv.filter(value => value.startsWith(`--${name}=`));
  need(matches.length === 1, 'EXACT_PUBLIC_INPUT_PIN_REQUIRED');
  return matches[0].slice(name.length + 3);
}
function publicJson(file, expected) {
  need(path.isAbsolute(file) && HEX.test(expected), 'PUBLIC_INPUT_PATH_OR_HASH_INVALID');
  const stat = fs.lstatSync(file);
  need(stat.isFile() && !stat.isSymbolicLink() && stat.size <= 1024 * 1024, 'PUBLIC_INPUT_FILE_UNSAFE');
  const raw = fs.readFileSync(file);
  need(hash(raw) === expected, 'PUBLIC_INPUT_FILE_HASH_CHANGED');
  return JSON.parse(raw.toString('utf8'));
}
function canaryObservation(value) {
  const rows = Array.isArray(value.public_receipts) ? value.public_receipts : [value];
  const matches = rows.filter(row => row.ok === true && row.phase === 'observe' && row.provenance === 'central_mcp_service_trial');
  need(matches.length === 1, 'EXACT_CANARY_OBSERVATION_REQUIRED');
  const observed = matches[0], summary = observed.verified_patch_and_initial_proof_summary, proof = summary?.initial_verification;
  need(observed.family?.settled === true && observed.family?.state === 'settled'
    && ['passed', 'failed', 'timed_out'].includes(proof?.proof_status) && proof.plan_sha256 === PLAN_SHA && (proof.proof_status === 'passed' ? HEX.test(proof.proof_fingerprint) : proof.proof_fingerprint === null)
    && Array.isArray(proof.proof_ids) && (proof.proof_status !== 'passed' || proof.proof_ids.length > 0)
    && proof.proof_ids.every(value => /^[a-f0-9]{32}$/.test(value))
    && typeof proof.command_id === 'string' && /^[A-Za-z0-9_-]{1,128}$/.test(proof.command_id)
    && typeof proof.job_id === 'string' && /^[A-Za-z0-9_-]{1,128}$/.test(proof.job_id)
    && /^[a-f0-9]{32}$/.test(summary.run_id) && /^[a-f0-9]{32}$/.test(summary.wave_id)
    && summary.run_id !== '95e909f0040a448faa9f1f3257e2ee2c'
    && summary.wave_id !== 'c101beadfc6d4f2fbc13845052c84693'
    && summary.run_id !== 'fbaf4b0700d04794af4062671c1bcd2b' && summary.wave_id !== 'e712eca9463e465fb1905264c998f50c', 'CANARY_PROOF_IDENTITY_INVALID');
  return { observed, summary, proof };
}
function safePage(value, commandId, stream) {
  need(value && typeof value === 'object' && value.ok === true && value.command_id === commandId
    && value.stream === stream && value.stream_output_ref === `command:${commandId}:${stream}`
    && value.output_ref === `command:${commandId}:${stream}` && value.offset === 0 && value.requested_offset === 0
    && value.next_offset === null && value.truncated === false && value.omitted_bytes === 0
    && value.stream_dropped_bytes === 0 && value.evicted_bytes_total === 0
    && typeof value.content === 'string' && value.total_stream_bytes === Buffer.byteLength(value.content, 'utf8')
    && value.total_stream_bytes <= 32768, 'EXACT_RETAINED_CANARY_OUTPUT_REQUIRED');
  need(!/Bearer\s|PRIVATE KEY|Authorization\s*:/i.test(value.content), 'PRIVATE_OUTPUT_REJECTED');
  return { ok: true, command_id: commandId, session_id: commandId, output_ref: value.output_ref,
    stream_output_ref: value.stream_output_ref, stream, offset: 0, requested_offset: 0,
    content: value.content, content_sha256: hash(Buffer.from(value.content, 'utf8')),
    next_offset: null, total_stream_bytes: value.total_stream_bytes, omitted_bytes: 0,
    stream_dropped_bytes: 0, evicted_bytes_total: 0, truncated: false };
}
function checkerTap(page) {
  const text = page.content;
  const cases = [
    'passed proof is ready for genuine controller acceptance',
    'failed proof retains the applied patch for replanning',
    'timed-out proof retains the applied patch for replanning',
    'an unapplied patch cannot be ready for acceptance'
  ];
  need(/^# tests 4\s*$/m.test(text) && /^# pass 4\s*$/m.test(text) && /^# fail 0\s*$/m.test(text)
    && !/^not ok /m.test(text) && cases.every((name, index) => text.split(/\r?\n/).includes(`ok ${index + 1} - ${name}`)),
  'EXACT_CHECKER_TAP_4_OF_4_REQUIRED');
  return { tests: 4, pass: 4, fail: 0, content_sha256: page.content_sha256 };
}
function requestJson(port, token, method, route, body) {
  return new Promise((resolve, reject) => {
    const fail = code => reject(Object.assign(new Error(), { code }));
    const raw = body === undefined ? null : Buffer.from(JSON.stringify(body));
    const request = http.request({ host: '127.0.0.1', port, path: route, method,
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json',
        ...(raw ? { 'Content-Length': raw.length, 'MCP-Protocol-Version': '2026-07-28', 'Mcp-Method': 'tools/call',
          'Mcp-Name': 'command_control', 'X-Coding-Tools-Client-Id': CLIENT_ID, 'X-Coding-Tools-Client-Type': 'electron' } : {}) },
      timeout: 10000 }, response => {
      const parts = []; let bytes = 0;
      response.on('data', chunk => { bytes += chunk.length; if (bytes <= 262144) parts.push(chunk); });
      response.on('end', () => {
        if (response.statusCode !== 200 || bytes > 262144) return fail('NATIVE_READ_ONLY_RESPONSE_INVALID');
        try { resolve(JSON.parse(Buffer.concat(parts).toString('utf8'))); } catch { fail('NATIVE_READ_ONLY_JSON_INVALID'); }
      });
    });
    request.on('timeout', () => { request.destroy(); fail('NATIVE_READ_ONLY_TIMEOUT'); });
    request.on('error', () => fail('NATIVE_READ_ONLY_TRANSPORT_FAILED'));
    request.end(raw);
  });
}
async function main(app) {
  const isolated = path.join(HERE, 'output-reader-profile');
  const selected = app.commandLine.getSwitchValue('user-data-dir');
  need(selected && equalPath(selected, isolated), 'EXPLICIT_ISOLATED_READER_PROFILE_REQUIRED');
  need(!equalPath(isolated, PROFILE), 'PRODUCT_PROFILE_LOCK_REJECTED');
  app.setPath('userData', isolated); app.setPath('sessionData', path.join(isolated, 'session-data'));
  fs.mkdirSync(path.join(isolated, 'session-data'), { recursive: true });
  await app.whenReady();
  const observationFile = arg('observation'), observationHash = arg('observation-sha256');
  const pins = publicJson(arg('pins'), arg('pins-sha256'));
  const { observed, summary, proof } = canaryObservation(publicJson(observationFile, observationHash));
  const completedAtMs = Number(arg('completed-at-ms'));
  need(Number.isSafeInteger(completedAtMs) && 0 <= Date.now() - completedAtMs && Date.now() - completedAtMs < 300000,
    'NATIVE_OUTPUT_RETENTION_WINDOW_EXPIRED');
  need(pins.native_tool_contract_sha256 === NATIVE_SHA && pins.contract_version === `sha256:${NATIVE_SHA}`,
    'R14_SAME_WINDOW_NATIVE_CONTRACT_PIN_REQUIRED');
  const { createRuntimePaths } = require(path.join(REPO, 'electron/services/runtimePaths'));
  const paths = createRuntimePaths({ dataRoot: PROFILE, appRoot: path.join(CANDIDATE, 'resources/app.asar'),
    resourcesRoot: path.join(CANDIDATE, 'resources/resources'), runtimeMode: 'packaged',
    executablePath: path.join(CANDIDATE, 'Coding Tools MCP.exe') });
  const settings = JSON.parse(fs.readFileSync(paths.settingsFile(), 'utf8'));
  need(equalPath(settings.workspace, REPO) && Number.isSafeInteger(settings.mcpPort)
    && settings.mcpPort >= 1 && settings.mcpPort <= 65535, 'EXACT_NATIVE_SETTINGS_TARGET_REQUIRED');
  const { SecretStore } = require(path.join(REPO, 'electron/services/secretStore'));
  const secrets = new SecretStore(paths), availability = secrets._readResult();
  need(availability.valid && availability.value?.mcpAuthToken, 'NATIVE_AUTH_UNAVAILABLE_IN_CRYPTO_PROFILE');
  const token = secrets.get('mcpAuthToken'); // Memory only: no environment/disk/stdout forwarding.
  const health = await requestJson(settings.mcpPort, token, 'GET', '/__control/health');
  need(health.ready === true && equalPath(health.workspace, REPO) && health.activation_epoch_id === pins.activation_epoch
    && health.process_instance_id === pins.runtime_instance_id
    && (health.instance_id || health.server_instance_id) === pins.mcp_server_instance_id
    && health.tool_contract?.sha256 === NATIVE_SHA, 'EXACT_NATIVE_HEALTH_IDENTITY_REQUIRED');
  const invoke = async (label, arguments_) => {
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
  const receipt = { ok: true, phase: 'native_canary_output_capture', observed_at_ms: Date.now(),
    provenance: 'local_authenticated_read_only', client_id: CLIENT_ID, client_type: 'electron',
    attestation_claimed: false, native_semantic_acceptance: 'pending', tool: 'command_control', action: 'read',
    observation_sha256: observationHash, completed_at_ms: completedAtMs,
    action_id: observed.family.action_id, task_id: observed.family.task_id,
    command_id: proof.command_id, job_id: proof.job_id, run_id: summary.run_id, wave_id: summary.wave_id,
    proof_ids: proof.proof_ids, proof_fingerprint: proof.proof_fingerprint, plan_sha256: PLAN_SHA,
    runtime_identity: { activation_epoch_id: pins.activation_epoch, process_instance_id: pins.runtime_instance_id,
      server_instance_id: pins.mcp_server_instance_id, tool_contract_sha256: NATIVE_SHA },
    proof_status: proof.proof_status, native_command_status: poll.status, native_exit_code: poll.exit_code ?? null,
    stdout: streams.stdout, stderr: streams.stderr, tap, remote_mutation: false };
  const receiptFile = arg('receipt');
  need(path.isAbsolute(receiptFile) && equalPath(path.dirname(receiptFile), HERE)
    && /^native-output-[0-9TZ]+\.json$/.test(path.basename(receiptFile)), 'OUTPUT_RECEIPT_NOT_OWNED');
  const descriptor = fs.openSync(receiptFile, 'wx');
  try { fs.writeFileSync(descriptor, JSON.stringify(receipt)); fs.fsyncSync(descriptor); } finally { fs.closeSync(descriptor); }
  process.stdout.write(JSON.stringify({ ok: true, phase: receipt.phase, receipt_path: receiptFile,
    receipt_sha256: hash(fs.readFileSync(receiptFile)), command_id: proof.command_id, job_id: proof.job_id,
    run_id: summary.run_id, wave_id: summary.wave_id, tap, attestation_claimed: false, secret_values_emitted: false }) + '\n');
}
module.exports = { canaryObservation, safePage, checkerTap };
if (require.main === module) {
  process.noAsar = true;
  const watchdog = setTimeout(() => { process.stdout.write(JSON.stringify({ ok: false, phase: 'native_canary_output_failed', code: 'OUTPUT_READER_26S_DEADLINE', secret_values_emitted: false }) + '\n'); process.exit(2); }, 26000);
  watchdog.unref();
  const { app } = require('electron');
  main(app).then(() => app.exit(0)).catch(error => {
    const code = /^[A-Z0-9_]{1,128}$/.test(error.code || '') ? error.code : 'NATIVE_OUTPUT_CAPTURE_FAILED';
    process.stdout.write(JSON.stringify({ ok: false, phase: 'native_canary_output_failed', code,
      secret_values_emitted: false, acceptance_performed: false }) + '\n');
    app.exit(1);
  });
}
