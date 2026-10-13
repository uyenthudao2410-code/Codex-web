'use strict';
// Exact read-only native audit through the already running Recovery Host gateway.
// No crypto profile, credential copy, controller takeover, stop or acceptance.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const originalFs = require('original-fs');
const { DatabaseSync } = require('node:sqlite');
const ROOT = 'E:\\DEV\\Codex-web';
const AUTOCAD = 'E:\\DEV\\Autocad';
const CANDIDATE = path.join(ROOT, 'dist', 'windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9d', 'win-unpacked');
const CONTEXT = 'cpap_ced36a9e27d7ccbbf19ebca90c3d0393772f98ce3a1910982450c850';
const RUN = 'a123ac6f4c484f15a21033e0059d63d9';
const WAVE = '8aaccbc6dea74f9c96ffe6deb4844d82';
const EPOCH = 'activation-mv514if9-7a4fabe0ce77708f8be03ff43a6518db';
const POSTIMAGE = '3a42ea5c3e68101db07001a265b9fb4fcbbc0021ed965139dcf10ea99ba73023';
const need = (condition, code) => { if (!condition) throw Object.assign(new Error(), { code }); };
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const same = (a, b) => path.resolve(a).toLowerCase() === path.resolve(b).toLowerCase();
const pick = (value, keys) => Object.fromEntries(keys.filter(key => value?.[key] !== undefined).map(key => [key, value[key]]));
async function main() {
  const executable = path.join(CANDIDATE, 'Coding Tools MCP.exe');
  const appRoot = path.join(CANDIDATE, 'resources', 'app.asar');
  need(same(process.execPath, executable), 'EXACT_R9D_EXECUTABLE_REQUIRED');
  need(hash(originalFs.readFileSync(executable)) === '337f3669f7702156fe725c61dfc530d1938eee35f463fe3f1261ddba53b14c74'
    && hash(originalFs.readFileSync(appRoot)) === '2fba385f52d679dc005b8a55d8d05a971bb0312e0bcbc9a3acabd69885ed7589', 'EXACT_R9D_PACKAGE_REQUIRED');
  const load = name => require(path.join(appRoot, 'electron', 'services', name));
  const { RuntimePaths } = load('runtimePaths');
  const { RecoveryIpcClient, loadRecoveryDescriptor } = load('recoveryIpc');
  const { readVerifiedReadyHost, descriptorRequestOptions, descriptorMatchesInstallation } = load('recoveryHostLauncher');
  const paths = new RuntimePaths({ dataRoot: path.join(process.env.APPDATA, 'web-mcp-assistant'), appRoot,
    resourcesRoot: path.join(CANDIDATE, 'resources', 'resources'), executablePath: executable, runtimeMode: 'packaged' });
  const client = new RecoveryIpcClient({ paths });
  const verified = await readVerifiedReadyHost(client, paths, loadRecoveryDescriptor, 2);
  const host = verified?.descriptor;
  need(host && descriptorMatchesInstallation(host, paths.runtimeIdentity()) && host.owner_pid === 3476
    && host.instance_id === 'dbf2536afedb8b4e554a29fc9e88cb50' && host.owner_process_start_token === '134362696871111330', 'EXACT_R9D_OWNER_REQUIRED');
  const exact = (action, args = []) => client.call(action, args, descriptorRequestOptions(host));
  const requireEpoch = epoch => need(epoch?.activation_epoch_id === EPOCH && epoch.state === 'READY' && epoch.admission_open === true, 'EXACT_READY_EPOCH_REQUIRED');
  requireEpoch(await exact('runtime.activation_epoch_status'));
  const identity = await exact('runtime.identity_observation');
  need(identity.mcp_ready === true && identity.identity_current === true
    && identity.mcp_process_instance_id === '_H5DKjZjiw52F4s2' && identity.mcp_server_instance_id === 'mynei0XQyArSjjoB'
    && identity.tool_contract_sha256 === '0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4', 'EXACT_NATIVE_IDENTITY_REQUIRED');
  const registry = JSON.parse(fs.readFileSync(path.join(ROOT, '.coding-tools', 'orchestration', 'task-context-workspaces.json'), 'utf8'));
  need(same(registry.contexts?.[CONTEXT]?.canonical_root || '', AUTOCAD), 'EXACT_CANARY_CONTEXT_ROOT_REQUIRED');
  const scopeHash = hash(Buffer.from('mcp2026:' + CONTEXT)).slice(0, 24);
  const state = JSON.parse(fs.readFileSync(path.join(AUTOCAD, '.coding-tools', 'task-contexts', scopeHash + '.json'), 'utf8'));
  need(state.orchestration?.run_id === RUN && state.orchestration?.wave_id === WAVE, 'EXACT_CANARY_CONTEXT_RUN_REQUIRED');
  const target = path.join(AUTOCAD, 'mcp-access-smoke-20261012-r9d.txt');
  need(hash(originalFs.readFileSync(target)) === POSTIMAGE, 'EXACT_CANARY_POSTIMAGE_REQUIRED');
  const gatewayFile = paths.hubProxyDescriptorFile();
  need(fs.lstatSync(gatewayFile).isFile() && fs.statSync(gatewayFile).size <= 16384, 'BOUNDED_EXISTING_GATEWAY_DESCRIPTOR_REQUIRED');
  const gateway = JSON.parse(fs.readFileSync(gatewayFile, 'utf8'));
  need(gateway.version === 1 && gateway.host === '127.0.0.1' && gateway.owner === 'recovery-host'
    && gateway.owner_pid === host.owner_pid && gateway.device_id === host.device_id
    && gateway.device_instance_id === host.device_instance_id && gateway.instance_id === host.device_instance_id
    && Number.isSafeInteger(gateway.port) && gateway.port > 0 && gateway.port <= 65535
    && typeof gateway.token === 'string' && gateway.token.length >= 32, 'EXACT_EXISTING_GATEWAY_REQUIRED');
  const peekLease = () => {
    const db = new DatabaseSync(path.join(AUTOCAD, '.coding-tools', 'orchestration', 'ledger.sqlite3'), { readOnly: true });
    try {
      db.exec('PRAGMA query_only=ON');
      return db.prepare('SELECT run_id,owner_client_id,status,expires_at,fencing_token FROM controller_leases WHERE run_id=?').get(RUN) || null;
    } finally { db.close(); }
  };
  const beforeLease = peekLease();
  const id = 'r9d-exact-canary-audit-' + Date.now();
  const body = Buffer.from(JSON.stringify({ jsonrpc: '2.0', id, method: 'tools/call', params: {
    name: 'task_control', arguments: { action: 'audit', task_context_id: CONTEXT, run_id: RUN, wave_id: WAVE, limit: 20 },
    _meta: { 'io.modelcontextprotocol/protocolVersion': '2026-07-28', 'io.modelcontextprotocol/clientCapabilities': {},
      'io.modelcontextprotocol/clientInfo': { name: 'codex-desktop-proxy', version: '1' } } } }));
  const result = await new Promise((resolve, reject) => {
    const fail = code => reject(Object.assign(new Error(), { code }));
    const request = http.request({ host: gateway.host, port: gateway.port, path: '/mcp', method: 'POST',
      headers: { Authorization: 'Bearer ' + gateway.token, 'Content-Type': 'application/json', 'Content-Length': body.length,
        'MCP-Protocol-Version': '2026-07-28', 'Mcp-Method': 'tools/call', 'Mcp-Name': 'task_control' }, timeout: 15000 }, response => {
      const chunks = []; let bytes = 0;
      response.on('data', chunk => { bytes += chunk.length; if (bytes <= 4 * 1024 * 1024) chunks.push(chunk); });
      response.on('end', () => {
        if (response.statusCode !== 200 || bytes > 4 * 1024 * 1024) return fail('EXISTING_GATEWAY_AUDIT_REJECTED');
        try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))); } catch { fail('EXISTING_GATEWAY_AUDIT_INVALID'); }
      });
    });
    request.on('timeout', () => { request.destroy(); fail('EXISTING_GATEWAY_AUDIT_TIMEOUT_DO_NOT_REPLAY'); });
    request.on('error', () => fail('EXISTING_GATEWAY_AUDIT_TRANSPORT_FAILED_DO_NOT_REPLAY'));
    request.end(body);
  });
  if (result.id !== id || result.error || result.result?.isError === true) {
    const code = result.result?.structuredContent?.error?.code || result.result?.structuredContent?.code;
    throw Object.assign(new Error(), { code: /^[A-Z0-9_]{3,96}$/.test(code || '') ? code : 'EXACT_NATIVE_AUDIT_REJECTED' });
  }
  const value = result.result?.structuredContent;
  need(value?.orchestration?.run_id === RUN && value.orchestration.wave_id === WAVE, 'EXACT_NATIVE_AUDIT_RUN_REQUIRED');
  const afterLease = peekLease();
  requireEpoch(await exact('runtime.activation_epoch_status'));
  await exact('recovery.ping');
  need(hash(originalFs.readFileSync(target)) === POSTIMAGE, 'CANARY_POSTIMAGE_CHANGED');
  const currentHost = loadRecoveryDescriptor(paths);
  need(currentHost.owner_pid === host.owner_pid && currentHost.instance_id === host.instance_id
    && currentHost.owner_process_start_token === host.owner_process_start_token, 'HOST_CHANGED_DURING_AUDIT');
  const receipt = { ok: true, operation: 'exact_canary_audit_via_existing_gateway', observed_at: new Date().toISOString(),
    root: AUTOCAD, task_context_id: CONTEXT, run_id: RUN, wave_id: WAVE, activation_epoch_id: EPOCH,
    postimage_sha256: POSTIMAGE, actor: { client_id: 'codex-desktop', client_type: 'codex_desktop', identity_spoofed: false },
    orchestration: pick(value.orchestration, ['run_id', 'wave_id', 'orchestration_state', 'execution_mode']),
    run: pick(value.audit?.run, ['run_id', 'task_id', 'status', 'started_at', 'finished_at']),
    proofs: (value.audit?.proofs || []).map(item => pick(item, ['proof_id', 'wave_id', 'status', 'exit_code'])),
    integrity: value.audit?.integrity, controller_lease_before: beforeLease, controller_lease_after: afterLease,
    controller_lease_same: JSON.stringify(beforeLease) === JSON.stringify(afterLease),
    lifecycle_read_only: true, native_report_export_performed: true, acceptance_performed: false,
    stop_performed: false, credential_copied: false, crypto_profile_started: false, secret_values_emitted: false };
  const report = path.join(__dirname, 'existing-gateway-canary-audit-' + Date.now() + '.json');
  fs.writeFileSync(report, JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
  process.stdout.write(JSON.stringify({ ok: true, report_path: report, report_sha256: hash(fs.readFileSync(report)),
    state: receipt.orchestration.orchestration_state, controller_lease: afterLease, secret_values_emitted: false }) + '\n');
}
main().then(() => process.exit(0)).catch(error => {
  process.stdout.write(JSON.stringify({ ok: false, code: /^[A-Z0-9_]{3,96}$/.test(error.code || '') ? error.code : 'EXISTING_GATEWAY_CANARY_AUDIT_FAILED',
    stop_performed: false, acceptance_performed: false, secret_values_emitted: false }) + '\n');
  process.exit(1);
});
