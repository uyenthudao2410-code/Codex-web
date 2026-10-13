'use strict';
// Root-only exact canary audit/stop. Existing MCP bearer stays in memory.
// This uses ordinary native controller authority; no managed transport
// attestation, proof injection, acceptance, replay, or file rollback is claimed.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const http = require('node:http');
const originalFs = require('original-fs');
const { app } = require('electron');
const REPORT = path.resolve(__dirname, '..');
const ROOT = 'E:\\DEV\\Codex-web';
const AUTOCAD = 'E:\\DEV\\Autocad';
const PROFILE = path.join(process.env.APPDATA, 'web-mcp-assistant');
const CANDIDATE = path.join(ROOT, 'dist', 'windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9d', 'win-unpacked');
const RUN = 'a123ac6f4c484f15a21033e0059d63d9';
const WAVE = '8aaccbc6dea74f9c96ffe6deb4844d82';
const EPOCH = 'activation-mv514if9-7a4fabe0ce77708f8be03ff43a6518db';
const PROCESS = '_H5DKjZjiw52F4s2';
const SERVER = 'mynei0XQyArSjjoB';
const CLIENT = 'chatweb-autocad-r9d-smoke-controller';
const TARGET = 'mcp-access-smoke-20261012-r9d.txt';
const POSTIMAGE = '3a42ea5c3e68101db07001a265b9fb4fcbbc0021ed965139dcf10ea99ba73023';
const SHA = '0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4';
const HEX = /^[a-f0-9]{64}$/;
const need = (condition, code) => { if (!condition) throw Object.assign(new Error(), { code }); };
const hash = raw => crypto.createHash('sha256').update(raw).digest('hex');
const fileHash = file => hash(originalFs.readFileSync(file));
const samePath = (a, b) => path.resolve(a).toLowerCase() === path.resolve(b).toLowerCase();
const pick = (value, keys) => Object.fromEntries(keys.filter(key => value?.[key] !== undefined).map(key => [key, value[key]]));
function arg(name, required = true) {
  const values = process.argv.filter(value => value.startsWith('--' + name + '='));
  need(values.length === (required ? 1 : values.length ? 1 : 0), 'EXACT_INPUT_REQUIRED');
  return values.length ? values[0].slice(name.length + 3) : '';
}
function ownedFile(file, digest) {
  need(path.isAbsolute(file) && HEX.test(digest), 'REVIEWED_EVIDENCE_PIN_REQUIRED');
  const resolved = fs.realpathSync(file);
  need(resolved.toLowerCase().startsWith(path.resolve(REPORT, '..').toLowerCase() + path.sep), 'EVIDENCE_OUTSIDE_REPORT');
  const info = fs.lstatSync(file);
  need(info.isFile() && !info.isSymbolicLink() && info.size <= 2 * 1024 * 1024, 'EVIDENCE_UNSAFE');
  const raw = fs.readFileSync(file);
  need(hash(raw) === digest, 'REVIEWED_EVIDENCE_CHANGED');
  return raw;
}
function request(port, token, method, route, body) {
  return new Promise((resolve, reject) => {
    const fail = code => reject(Object.assign(new Error(), { code }));
    const raw = body === undefined ? null : Buffer.from(JSON.stringify(body));
    const req = http.request({ host: '127.0.0.1', port, path: route, method,
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json',
        ...(raw ? { 'Content-Length': raw.length, 'MCP-Protocol-Version': '2026-07-28',
          'Mcp-Method': 'tools/call', 'Mcp-Name': 'task_control',
          'X-Coding-Tools-Client-Id': CLIENT, 'X-Coding-Tools-Client-Type': 'chatweb' } : {}) },
      timeout: 15000 }, res => {
      const chunks = []; let bytes = 0;
      res.on('data', chunk => { bytes += chunk.length; if (bytes <= 2 * 1024 * 1024) chunks.push(chunk); });
      res.on('end', () => {
        if (res.statusCode !== 200 || bytes > 2 * 1024 * 1024) return fail('NATIVE_RESPONSE_REJECTED');
        try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))); } catch { fail('NATIVE_RESPONSE_INVALID'); }
      });
    });
    req.on('timeout', () => { req.destroy(); fail('NATIVE_REQUEST_TIMEOUT_UNKNOWN_DO_NOT_REPLAY'); });
    req.on('error', () => fail('NATIVE_TRANSPORT_FAILED_UNKNOWN_DO_NOT_REPLAY'));
    req.end(raw);
  });
}
function summary(value) {
  const orchestration = value.orchestration || {};
  need(orchestration.run_id === RUN && orchestration.wave_id === WAVE, 'EXACT_NATIVE_RUN_WAVE_REQUIRED');
  return { orchestration: pick(orchestration, ['run_id', 'wave_id', 'orchestration_state', 'execution_mode',
    'base_head', 'contract_fp', 'write_lease_id', 'write_owner']),
    run: pick(value.audit?.run, ['run_id', 'task_id', 'status', 'started_at', 'finished_at']),
    proofs: (value.audit?.proofs || []).map(proof => pick(proof, ['proof_id', 'run_id', 'wave_id', 'status', 'input_fingerprint'])),
    integrity: value.audit?.integrity,
    completion_report: pick(value.completion_report, ['report_id', 'run_id', 'wave_id', 'state', 'outcome']),
    stopped: value.stopped === true, target_run_id: value.target_run_id || null };
}
async function main() {
  const operation = arg('operation');
  need(['canary-audit', 'canary-stop'].includes(operation), 'EXACT_CANARY_OPERATION_REQUIRED');
  const isolated = path.join(REPORT, 'canary-controller-profile');
  need(samePath(app.commandLine.getSwitchValue('user-data-dir'), isolated) && !samePath(isolated, PROFILE), 'ISOLATED_CONTROLLER_PROFILE_REQUIRED');
  app.setPath('userData', isolated);
  app.setPath('sessionData', path.join(isolated, 'session-data'));
  await app.whenReady();
  const proof = JSON.parse(fs.readFileSync(path.join(REPORT, '..', 'r9d-candidate-verification.json')));
  const appRoot = path.join(CANDIDATE, 'resources', 'app.asar');
  need(proof.ok === true && samePath(proof.candidate, CANDIDATE)
    && proof.executable_sha256 === '337f3669f7702156fe725c61dfc530d1938eee35f463fe3f1261ddba53b14c74'
    && proof.app_asar_sha256 === '2fba385f52d679dc005b8a55d8d05a971bb0312e0bcbc9a3acabd69885ed7589'
    && fileHash(path.join(CANDIDATE, 'Coding Tools MCP.exe')) === proof.executable_sha256
    && fileHash(appRoot) === proof.app_asar_sha256, 'EXACT_R9D_PACKAGE_REQUIRED');
  const load = name => require(path.join(appRoot, 'electron', 'services', name));
  const { RuntimePaths } = load('runtimePaths');
  const { SettingsStore } = load('settingsStore');
  const { SecretStore } = load('secretStore');
  const { RecoveryIpcClient, loadRecoveryDescriptor } = load('recoveryIpc');
  const { readVerifiedReadyHost, descriptorRequestOptions, descriptorMatchesInstallation } = load('recoveryHostLauncher');
  const { ControlPlaneEnrollmentService } = load('controlPlaneEnrollment');
  const paths = new RuntimePaths({ dataRoot: PROFILE, appRoot, resourcesRoot: path.join(CANDIDATE, 'resources', 'resources'),
    executablePath: path.join(CANDIDATE, 'Coding Tools MCP.exe'), runtimeMode: 'packaged' });
  const settings = new SettingsStore(paths).load();
  need(samePath(settings.workspace, ROOT) && settings.authorizedRoots.some(root => samePath(root, AUTOCAD)), 'EXACT_AUTHORIZED_ROOT_REQUIRED');
  const service = new ControlPlaneEnrollmentService({ paths });
  need(samePath(service.registeredWorkspaceRoot({ workspaceId: 'workspace_bc86004be2684b958ab7a9a6f9530cd7',
    workspaceGeneration: 'generation_03f9c04f1b14414fa4bfa7d91cc8ea7a' }), AUTOCAD), 'EXACT_REGISTRY_ROOT_REQUIRED');
  const recovery = new RecoveryIpcClient({ paths });
  const verified = await readVerifiedReadyHost(recovery, paths, loadRecoveryDescriptor, 2);
  need(verified && descriptorMatchesInstallation(verified.descriptor, paths.runtimeIdentity())
    && verified.descriptor.owner_pid === 3476 && verified.descriptor.instance_id === 'dbf2536afedb8b4e554a29fc9e88cb50'
    && verified.descriptor.installation_id === 'bdf474c17024f7686b83920b289de5422d6129db4bbf8a93659eb744ccaaadba'
    && verified.descriptor.owner_process_start_token === '134362696871111330', 'EXACT_R9D_OWNER_REQUIRED');
  const exact = (action, args = []) => recovery.call(action, args, descriptorRequestOptions(verified.descriptor));
  const epoch = await exact('runtime.activation_epoch_status');
  need(epoch.activation_epoch_id === EPOCH && epoch.state === 'READY' && epoch.admission_open === true, 'EXACT_READY_EPOCH_REQUIRED');
  const target = path.join(AUTOCAD, TARGET);
  need(fileHash(target) === POSTIMAGE && fs.realpathSync(target).toLowerCase() === target.toLowerCase(), 'CANARY_POSTIMAGE_CHANGED');
  const secrets = new SecretStore(paths);
  const available = secrets._readResult();
  need(available.valid === true && available.value?.mcpAuthToken, 'EXISTING_NATIVE_AUTH_UNAVAILABLE');
  const token = secrets.get('mcpAuthToken');
  const health = () => request(settings.mcpPort, token, 'GET', '/__control/health');
  function requireHealth(value) {
    need(value.ready === true && samePath(value.workspace, ROOT) && value.activation_epoch_id === EPOCH
      && value.process_instance_id === PROCESS && (value.instance_id || value.server_instance_id) === SERVER
      && value.tool_contract?.sha256 === SHA, 'EXACT_NATIVE_HEALTH_REQUIRED');
  }
  requireHealth(await health());
  const invoke = async action => {
    const id = 'autocad-r9d-' + action + '-' + Date.now();
    const body = { jsonrpc: '2.0', id, method: 'tools/call', params: { name: 'task_control', arguments: {
      action, run_id: RUN, wave_id: WAVE, limit: 20,
      ...(action === 'stop' ? { reason: 'Controlled smoke ended without admitted same-wave semantic proof; preserve exact patched bytes and independent access evidence.' } : {})
    }, _meta: { 'io.modelcontextprotocol/protocolVersion': '2026-07-28', 'io.modelcontextprotocol/clientCapabilities': {},
      'io.modelcontextprotocol/clientInfo': { name: CLIENT, version: '1' } } } };
    const result = await request(settings.mcpPort, token, 'POST', '/mcp', body);
    if (result.id !== id || result.error || result.result?.isError === true) {
      const code = result.result?.structuredContent?.error?.code || result.result?.structuredContent?.code;
      throw Object.assign(new Error(), { code: /^[A-Z0-9_]{3,96}$/.test(code || '') ? code : 'NATIVE_TASK_CONTROL_REJECTED' });
    }
    need(result.result?.structuredContent, 'NATIVE_TASK_CONTROL_RESULT_MISSING');
    return result.result.structuredContent;
  };
  const before = summary(await invoke('audit'));
  need(before.orchestration.orchestration_state === 'ACCEPTING', 'EXACT_CANARY_NOT_ACCEPTING');
  const receipt = { operation, observed_at: new Date().toISOString(), ok: true, root: AUTOCAD, run_id: RUN, wave_id: WAVE,
    activation_epoch_id: EPOCH, package_sha256: proof.app_asar_sha256, canary_postimage_sha256: POSTIMAGE,
    actor: { client_id: CLIENT, client_type: 'chatweb', attestation_claimed: false }, before, acceptance_performed: false,
    proof_injected: false, file_reverted: false, canary_replayed: false, secret_values_emitted: false };
  if (operation === 'canary-stop') {
    need(process.argv.includes('--confirm-stop'), 'EXPLICIT_EXACT_STOP_REQUIRED');
    const auditRaw = ownedFile(arg('audit-receipt'), arg('audit-sha256'));
    const audit = JSON.parse(auditRaw.toString('utf8'));
    const age = Date.now() - Date.parse(audit.observed_at);
    need(audit.ok === true && audit.operation === 'canary-audit' && audit.run_id === RUN && audit.wave_id === WAVE
      && audit.activation_epoch_id === EPOCH && audit.before.orchestration.orchestration_state === 'ACCEPTING'
      && age >= 0 && age < 300000, 'FRESH_EXACT_AUDIT_REQUIRED');
    const evidenceDigest = arg('verification-sha256');
    ownedFile(arg('verification-receipt'), evidenceDigest);
    receipt.independent_verification_reviewed_sha256 = evidenceDigest;
    requireHealth(await health());
    need(fileHash(target) === POSTIMAGE, 'CANARY_POSTIMAGE_CHANGED');
    const stopped = summary(await invoke('stop'));
    need(stopped.stopped === true && stopped.target_run_id === RUN
      && stopped.orchestration.orchestration_state === 'ABORTED', 'EXACT_CANARY_STOP_NOT_CONFIRMED');
    receipt.after = stopped;
    receipt.final_audit = summary(await invoke('audit'));
    need(receipt.final_audit.orchestration.orchestration_state === 'ABORTED' && fileHash(target) === POSTIMAGE, 'STOPPED_RUN_OR_POSTIMAGE_CHANGED');
  }
  const finalEpoch = await exact('runtime.activation_epoch_status');
  need(finalEpoch.activation_epoch_id === EPOCH && finalEpoch.state === 'READY' && finalEpoch.admission_open === true, 'READY_EPOCH_CHANGED');
  await exact('recovery.ping');
  const receiptPath = path.join(REPORT, operation + '-receipt-' + Date.now() + '.json');
  fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
  process.stdout.write(JSON.stringify({ operation, ok: true, report_path: receiptPath, report_sha256: fileHash(receiptPath),
    run_id: RUN, wave_id: WAVE, state: receipt.after?.orchestration.orchestration_state || before.orchestration.orchestration_state,
    acceptance_performed: false, secret_values_emitted: false }) + '\n');
}
const watchdog = setTimeout(() => app.exit(2), 55000);
watchdog.unref();
main().then(() => app.exit(0)).catch(error => {
  const code = /^[A-Z0-9_]{3,96}$/.test(error.code || '') ? error.code : 'CANARY_CONTROLLER_FAILED';
  process.stdout.write(JSON.stringify({ ok: false, operation: 'canary_controller', code, acceptance_performed: false,
    unknown_effect_not_replayed: true, secret_values_emitted: false }) + '\n');
  app.exit(1);
});
