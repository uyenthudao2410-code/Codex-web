'use strict';

// Same-user read-only reachability and fresh isolated context discovery.
// Credential is decrypted only in memory and is never written or printed.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { app } = require('electron');
const { SecretStore } = require('../../../electron/services/secretStore');
app.setPath('userData', path.join(app.getPath('appData'), 'web-mcp-assistant'));

function request(port, token, body) {
  return new Promise((resolve, reject) => {
    const bytes = Buffer.from(JSON.stringify(body));
    const request = http.request({host: '127.0.0.1', port, path: '/mcp', method: 'POST', timeout: 15000,
      headers: {Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', 'Content-Length': bytes.length,
        'MCP-Protocol-Version': '2026-07-28', 'Mcp-Method': 'tools/call', 'Mcp-Name': 'workspace_context',
        'X-Coding-Tools-Client-Id': 'codex-desktop', 'X-Coding-Tools-Client-Type': 'codex_desktop'}}, response => {
      let raw = '';
      response.on('data', chunk => { if (raw.length < 4 * 1024 * 1024) raw += chunk; });
      response.on('end', () => {
        if (response.statusCode !== 200) return reject(Object.assign(new Error('Local MCP request refused.'), {code: `HTTP_${response.statusCode}`}));
        try { resolve(JSON.parse(raw)); } catch { reject(Object.assign(new Error('Invalid MCP response.'), {code:'INVALID_RESPONSE'})); }
      });
    });
    request.on('timeout', () => request.destroy(Object.assign(new Error('MCP connection timed out.'), {code:'TIMEOUT'})));
    request.on('error', reject);
    request.end(bytes);
  });
}

app.whenReady().then(async () => {
  const dataRoot = path.join(app.getPath('appData'), 'web-mcp-assistant');
  const settings = JSON.parse(fs.readFileSync(path.join(dataRoot, 'settings.json'), 'utf8'));
  const expectedRoot = path.resolve('E:/DEV/Codex-web');
  if (path.resolve(String(settings.workspace || '')).toLowerCase() !== expectedRoot.toLowerCase()) {
    throw Object.assign(new Error('Workspace mismatch.'), {code:'WORKSPACE_MISMATCH'});
  }
  const store = new SecretStore({secretsFile:()=>path.join(dataRoot, 'secrets.bin')});
  const token = store.get('mcpAuthToken');
  if (!token) {
    const status = store._readResult();
    process.stdout.write(JSON.stringify({diagnostic:'credential-read',data_root:dataRoot,found:status.found,valid:status.valid,unavailable:status.unavailable,error_code:String(status.error?.code || ''),error_type:String(status.error?.name || ''),entry_names:Object.keys(status.value || {})})+'\n');
    throw Object.assign(new Error('Local credential unavailable.'), {code:'TOKEN_UNAVAILABLE'});
  }
  const response = await request(Number(settings.mcpPort), token, {
    jsonrpc:'2.0', id:'direct-local-mode-context-20261022', method:'tools/call', params:{name:'workspace_context', arguments:{path:expectedRoot,detail:'full',max_entries:1},
      _meta:{'io.modelcontextprotocol/protocolVersion':'2026-07-28','io.modelcontextprotocol/clientCapabilities':{},'io.modelcontextprotocol/clientInfo':{name:'codex-desktop',version:'local-mode-work'}}}
  });
  const result = response.result;
  const structured = result?.structuredContent;
  const payload = structured?.data || structured;
  let textPayload;
  if (!payload) {
    try { textPayload = JSON.parse(result?.content?.find(item=>item.type==='text')?.text || '{}'); } catch { textPayload = {}; }
  }
  const value = payload || textPayload;
  if (response.error || result?.isError || value?.ok === false) throw Object.assign(new Error('Workspace context refused.'), {code:value?.error?.code || response.error?.code || 'CONTEXT_REFUSED'});
  const context = value?.task_context_id || result?._meta?.['io.coding-tools/taskContextId'] || structured?._meta?.['io.coding-tools/taskContextId'];
  const safe = {ok:true,local_mcp_reachable:true,client_id:'codex-desktop',client_type:'codex_desktop',task_context_id:context || null,
    workspace:value?.workspace || null,endpoint:value?.endpoint || null,task_status:value?.task?.status || null,
    result_keys:Object.keys(value || {}),meta_keys:Object.keys(result?._meta || {})};
  fs.writeFileSync(path.join(__dirname,'review-connection-result.json'), JSON.stringify(safe,null,2)+'\n');
  process.stdout.write(JSON.stringify(safe)+'\n');
  app.exit(0);
}).catch(error => {
  process.stdout.write(JSON.stringify({ok:false,code:String(error?.code || 'CONNECTION_FAILED')})+'\n');
  app.exit(1);
});
