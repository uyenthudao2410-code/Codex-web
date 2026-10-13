'use strict';
// Operator transport for the supported public adoption/proof/accept workflow.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto'), http = require('node:http');
const { app } = require('electron');
const root = path.resolve(__dirname, '../../../..');
const clientId = 'electron-bfix-source-acceptance';
const contextId = 'bfix-source-acceptance-20261013';
const mode = process.argv.includes('--accept') ? 'accept' : process.argv.includes('--observe') ? 'observe' : 'start';
const report = { schema_version: 1, operation: 'bfix_source_checkpoint_rebind', mode, observed_at: new Date().toISOString(), task_context_id: contextId, mutation_started: false };
const pick = (v, keys) => Object.fromEntries(keys.filter(k => v?.[k] !== undefined).map(k => [k, v[k]]));
const need = (v, code) => { if (!v) throw Object.assign(new Error(code), { code }); };
function request(port, token, route, body) {
  return new Promise((resolve, reject) => {
    const data = Buffer.from(JSON.stringify(body));
    const req = http.request({ host: '127.0.0.1', port, path: route, method: 'POST', timeout: 45000, headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', 'Content-Length': data.length, 'MCP-Protocol-Version': '2026-07-28', 'Mcp-Method': body.method || '', 'Mcp-Name': body.params?.name || '', 'X-Coding-Tools-Client-Id': clientId, 'X-Coding-Tools-Client-Type': 'electron' } }, res => {
      let raw = '';
      res.on('data', c => { raw += c; if (raw.length > 1048576) req.destroy(Object.assign(new Error('BOUNDED_RESPONSE_REQUIRED'), { code: 'BOUNDED_RESPONSE_REQUIRED' })); });
      res.on('end', () => { try { const value = JSON.parse(raw); const result = value.result?.structuredContent || value; if (value.error || value.result?.isError || result.ok === false) throw Object.assign(new Error('SUPPORTED_WORKFLOW_REFUSED'), { code: value.error?.code || result.error?.code || 'SUPPORTED_WORKFLOW_REFUSED', details: pick(result.error || result, ['code','message','category','retryable']) }); resolve(result); } catch (e) { reject(e); } });
    });
    req.on('timeout', () => req.destroy(Object.assign(new Error('OBSERVATION_TIMEOUT_NO_REPLAY'), { code: 'OBSERVATION_TIMEOUT_NO_REPLAY' })));
    req.on('error', reject); req.end(data);
  });
}
async function main() {
  const { RuntimePaths } = require(path.join(root, 'electron/services/runtimePaths'));
  const { SecretStore } = require(path.join(root, 'electron/services/secretStore'));
  const paths = new RuntimePaths({ dataRoot: path.join(process.env.APPDATA, 'web-mcp-assistant'), appRoot: root, resourcesRoot: path.join(root, 'resources'), executablePath: process.execPath, runtimeMode: 'development' });
  const settings = JSON.parse(fs.readFileSync(paths.settingsFile(), 'utf8'));
  need(path.resolve(settings.workspace).toLowerCase() === root.toLowerCase(), 'EXACT_CODEX_WEB_WORKSPACE_REQUIRED');
  const token = new SecretStore(paths).get('mcpAuthToken'); need(token, 'LOCAL_MCP_CREDENTIAL_REQUIRED');
  const call = (name, args) => request(settings.mcpPort, token, '/mcp', { jsonrpc: '2.0', id: crypto.randomBytes(8).toString('hex'), method: 'tools/call', params: { name, arguments: { task_context_id: contextId, ...args }, _meta: { 'io.modelcontextprotocol/protocolVersion': '2026-07-28', 'io.modelcontextprotocol/clientInfo': { name: clientId, version: '1' }, 'io.modelcontextprotocol/clientCapabilities': {} } } });
  await request(settings.mcpPort, token, '/__control/hub', { action: 'heartbeat', client_id: clientId, client_type: 'electron' });
  if (mode === 'start') {
    const intent = path.join(__dirname, 'source-rebind-targeted-intent.json'); need(!fs.existsSync(intent), 'REBIND_ALREADY_STARTED_OBSERVE_EXISTING');
    fs.writeFileSync(intent, JSON.stringify({ ...report, no_replay: true }, null, 2) + '\n', { flag: 'wx' });
    report.mutation_started = true;
    const result = await call('agent_workflow', { workflow: 'custom', phase: 'run', execution_route: 'deterministic', objective: 'Bind the unchanged, already proven Recovery Host fix to the current worktree after maintained documentation changed. Verify exact bfix package Git identity without reapplying patches or replaying Jobs.', path: root, paths: ['electron/services/recoveryActionStore.js'], adopt_existing_files: [{ path: 'electron/services/recoveryActionStore.js', sha256: '6f8bfc43491bf7a9019dce176f34078a4572e6e6f09681e95a272e55fca0a646' }], verification: 'tests', test_command: 'node .coding-tools/reports/parallel-native-first-20261012/bfix-transition/verify-bfix-source.cjs', timeout_seconds: 120, max_runtime_seconds: 120, idempotency_key: 'bfix-source-rebind-targeted-20261013' });
    report.result_keys = Object.keys(result);
    report.result = pick(result, ['ok','status','operation_id','orchestration','proof_summary','recommended_next_action','completion_report_id']);
    report.operation = pick(result.operation, ['operation_id','state','status','run_id','wave_id']);
    return;
  }
  const current = await call('task_control', { action: 'get' });
  const state = current.state || current;
  const op = state.orchestration || current.orchestration || {};
  report.result_keys = Object.keys(current);
  report.state = pick(state, ['task_id','status','current_step','next_step','orchestration','completion_report_id','failure']);
  report.completion_report = state.completion_report || current.completion_report || null;
  if (mode === 'observe') return;
  need(op.run_id && op.wave_id && op.orchestration_state === 'ACCEPTING', 'PROVEN_ACCEPTING_WAVE_REQUIRED');
  const transfer = await request(settings.mcpPort, token, '/__control/hub', { action: 'transfer_controller', run_id: op.run_id, target_client_id: clientId });
  need(transfer.ok === true && transfer.transferred === true, 'EXACT_CONTROLLER_TRANSFER_REQUIRED');
  if (state.completion_report_id) await call('task_control', { action: 'ack', run_id: op.run_id, message_id: state.completion_report_id });
  report.mutation_started = true;
  const accepted = await call('task_control', { action: 'accept', run_id: op.run_id, wave_id: op.wave_id, acceptance_files: [{ path: 'electron/services/recoveryActionStore.js', sha256: '6f8bfc43491bf7a9019dce176f34078a4572e6e6f09681e95a272e55fca0a646' }], idempotency_key: 'bfix-source-rebind-accept-20261013' });
  need(accepted.accepted === true, 'SOURCE_ACCEPTANCE_REQUIRED');
  report.acceptance = pick(accepted, ['accepted','checkpoint','source_checkpoint','orchestration','completion_report_id']);
  report.acceptance_keys = Object.keys(accepted);
}
app.setPath('userData', path.join(process.env.APPDATA, 'web-mcp-assistant'));
app.whenReady().then(async () => {
  try { await main(); report.ok = true; } catch (e) { report.ok = false; report.error = { code: e.code || 'SOURCE_REBIND_FAILED', details: e.details || null }; }
  const file = path.join(__dirname, `source-rebind-${mode}-${Date.now()}.json`);
  fs.writeFileSync(file, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ ok: report.ok, mode, report: file, state: report.state?.orchestration?.orchestration_state, error: report.error, result: report.result, operation: report.operation }));
  app.exit(report.ok ? 0 : 1);
});
