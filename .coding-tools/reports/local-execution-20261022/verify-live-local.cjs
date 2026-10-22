'use strict';
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { app } = require('electron');
const { SecretStore } = require('../../../electron/services/secretStore');
const root = 'E:/DEV/Codex-web';
const dataRoot = path.join(app.getPath('appData'), 'web-mcp-assistant');
app.setPath('userData', dataRoot);
const assert = (condition, code) => { if (!condition) throw Object.assign(new Error(code), {code}); };
function payload(response) {
  const result = response.result;
  let value = result?.structuredContent;
  if (!value) try { value = JSON.parse(result?.content?.find(item => item.type === 'text')?.text || '{}'); } catch { value = {}; }
  assert(!response.error && !result?.isError && value?.ok !== false, value?.error?.code || response.error?.code || 'TOOL_REFUSED');
  return value?.data || value;
}
function request(port, token, tool, args) {
  return new Promise((resolve, reject) => {
    const body = Buffer.from(JSON.stringify({jsonrpc:'2.0',id:`live-local-${tool}-${Date.now()}`,method:'tools/call',params:{name:tool,arguments:args,
      _meta:{'io.modelcontextprotocol/protocolVersion':'2026-07-28','io.modelcontextprotocol/clientCapabilities':{},
        'io.modelcontextprotocol/clientInfo':{name:'codex-desktop',version:'local-mode-live-proof'}}}}));
    const req = http.request({host:'127.0.0.1',port,path:'/mcp',method:'POST',timeout:60000,headers:{Authorization:`Bearer ${token}`,
      'Content-Type':'application/json','Content-Length':body.length,'MCP-Protocol-Version':'2026-07-28','Mcp-Method':'tools/call','Mcp-Name':tool,
      'X-Coding-Tools-Client-Id':'codex-desktop','X-Coding-Tools-Client-Type':'codex_desktop'}}, response => {
      let raw = '';
      response.on('data', data => { if (raw.length < 4*1024*1024) raw += data; });
      response.on('end', () => {
        if (response.statusCode !== 200) return reject(Object.assign(new Error('HTTP_REFUSED'), {code:`HTTP_${response.statusCode}`}));
        try { resolve(JSON.parse(raw)); } catch { reject(Object.assign(new Error('INVALID_RESPONSE'), {code:'INVALID_RESPONSE'})); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => req.destroy(Object.assign(new Error('TIMEOUT_DO_NOT_REPLAY'), {code:'TIMEOUT_DO_NOT_REPLAY'})));
    req.end(body);
  });
}
app.whenReady().then(async () => {
  const settings = JSON.parse(fs.readFileSync(path.join(dataRoot, 'settings.json'), 'utf8'));
  assert(settings.executionMode === 'local' && path.resolve(settings.workspace) === path.resolve(root), 'LOCAL_MODE_REQUIRED');
  const token = new SecretStore({secretsFile:() => path.join(dataRoot, 'secrets.bin')}).get('mcpAuthToken');
  assert(token, 'CREDENTIAL_UNAVAILABLE');
  const contextResponse = await request(settings.mcpPort, token, 'workspace_context', {path:root,detail:'compact',max_entries:1});
  const context = payload(contextResponse);
  const contextId = context.task_context_id || contextResponse.result?._meta?.['io.coding-tools/taskContextId'];
  assert(contextId, 'CONTEXT_MISSING');
  const call = async (tool, args) => payload(await request(settings.mcpPort, token, tool, {task_context_id:contextId,...args}));
  let result = await call('exec_command', {cmd:'node --version',workdir:root,yield_time_ms:1000,timeout_ms:10000,verbosity:'full'});
  const commandId = result.command_id;
  const deadline = Date.now() + 15000;
  while ((result.status === 'running' || result.exit_code == null) && commandId && Date.now() < deadline) {
    await new Promise(resolve => setTimeout(resolve, 200));
    result = await call('command_control', {action:'poll',command_id:commandId,yield_time_ms:1000,verbosity:'full'});
  }
  const receipt = {observed_at:new Date().toISOString(),task_context_id:contextId,command:'node --version',command_id:commandId,
    execution_mode:settings.executionMode,status:result.status,exit_code:result.exit_code,
    execution_backend:result.execution_backend,isolation_level:result.isolation_level,policy_decision:result.policy_decision,
    execution_owner:result.execution_owner,stdout:result.stdout,stderr:result.stderr,timed_out:result.timed_out || false};
  receipt.ok = result.status === 'exited' && result.exit_code === 0 && !receipt.timed_out
    && receipt.execution_backend === 'local' && receipt.isolation_level === 'host_user' && receipt.policy_decision === 'operator_local'
    && !!receipt.execution_owner?.job_id;
  fs.writeFileSync(path.join(__dirname, 'live-local-command.json'), JSON.stringify(receipt, null, 2) + '\n');
  console.log(JSON.stringify(receipt));
  app.exit(receipt.ok ? 0 : 1);
}).catch(error => { console.log(JSON.stringify({ok:false,error_code:error.code || 'LIVE_PROOF_FAILED'})); app.exit(1); });
