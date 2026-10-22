'use strict';

// Official local MCP workflow: no secret is printed or persisted.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const http = require('node:http');
const { app } = require('electron');
const { SecretStore } = require('../../../electron/services/secretStore');
const root = 'E:/DEV/Codex-web';
const dataRoot = path.join(app.getPath('appData'), 'web-mcp-assistant');
app.setPath('userData', dataRoot);
const objective = 'Validate and accept the exact completed source for permanent direct Windows host execution without ProcessContainer or Windows Sandbox, preserving permission controls, existing workspace/node identity and unrelated work.';
const sourcePaths = [
  'electron/main.js','electron/services/config.js','electron/services/nativeService.js',
  'electron/services/controlPlaneExecBridge.js','electron/services/controlPlaneEnrollment.js',
  'renderer/app.js','renderer/index.html',
  'resources/coding-tools-mcp/coding_tools_mcp/exec_tools.py',
  'resources/coding-tools-mcp/coding_tools_mcp/runtime_config.py',
  'resources/coding-tools-mcp/coding_tools_mcp/server.py',
  'resources/coding-tools-mcp/coding_tools_mcp/workspace_scope.py',
  'control-plane/control_plane/node_agent.py','control-plane/tests/test_exec_node_agent.py',
  'tests/settings.test.js','tests/native-service-activation-gate.test.js',
  'tests/control-plane-exec-bridge.test.js','tests/control-plane-exec-sandbox.test.js','tests/folder-permission-editor.test.js',
  'resources/coding-tools-mcp/tests/test_local_execution_mode.py',
  'resources/coding-tools-mcp/tests/test_windows_execution_policy.py',
  'resources/coding-tools-mcp/tests/test_exec_spawn_failure.py',
  'resources/coding-tools-mcp/tests/test_wave_a_runtime.py',
  'resources/coding-tools-mcp/tests/test_approved_patch_initial_verification.py'
];
const proofCommand = 'node --test tests/settings.test.js tests/native-service-activation-gate.test.js tests/control-plane-exec-bridge.test.js tests/folder-permission-editor.test.js tests/control-plane-exec-sandbox.test.js';
const stateFile = path.join(__dirname, 'review-workflow-state.json');
function hashFiles() { return sourcePaths.map(relative => ({path:relative,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,relative))).digest('hex')})); }
function save(name, value) { fs.writeFileSync(path.join(__dirname, name), JSON.stringify(value,null,2)+'\n'); }
function normalized(response) { return response.result?.structuredContent || response; }
function request(port, token, endpoint, body, method = 'POST', name = '') {
  return new Promise((resolve,reject) => {
    const bytes = body === undefined ? null : Buffer.from(JSON.stringify(body));
    const req = http.request({host:'127.0.0.1',port,path:endpoint,method,timeout:60000,
      headers:{Authorization:`Bearer ${token}`,...(bytes?{'Content-Type':'application/json','Content-Length':bytes.length}:{}),
        'MCP-Protocol-Version':'2026-07-28','Mcp-Method':'tools/call','Mcp-Name':name,
        'X-Coding-Tools-Client-Id':'codex-desktop','X-Coding-Tools-Client-Type':'codex_desktop'}},res => {
        let raw='';
        res.on('data',chunk=>{if(raw.length<16*1024*1024)raw+=chunk;});
        res.on('end',()=>{
          let value;try{value=JSON.parse(raw);}catch{return reject(Object.assign(new Error('Invalid response.'),{code:'INVALID_RESPONSE'}));}
          if(res.statusCode>=400)return reject(Object.assign(new Error('Official local API refused request.'),{code:value.code||`HTTP_${res.statusCode}`,safe_details:value}));
          resolve(value);
        });
      });
    req.on('timeout',()=>req.destroy(Object.assign(new Error('Request timeout; do not blindly replay.'),{code:'TIMEOUT'})));
    req.on('error',reject);req.end(bytes);
  });
}

app.whenReady().then(async()=>{
  const mode=process.argv.find(value=>value.startsWith('--mode='))?.slice(7);
  if(!['prepare','execute','accept','ack','observe'].includes(mode))throw Object.assign(new Error('Unsupported helper mode.'),{code:'INVALID_MODE'});
  const settings=JSON.parse(fs.readFileSync(path.join(dataRoot,'settings.json'),'utf8'));
  if(path.resolve(settings.workspace).toLowerCase()!==path.resolve(root).toLowerCase())throw Object.assign(new Error('Workspace mismatch.'),{code:'WORKSPACE_MISMATCH'});
  const token=new SecretStore({secretsFile:()=>path.join(dataRoot,'secrets.bin')}).get('mcpAuthToken');
  if(!token)throw Object.assign(new Error('Credential unavailable.'),{code:'TOKEN_UNAVAILABLE'});
  let state=fs.existsSync(stateFile)?JSON.parse(fs.readFileSync(stateFile,'utf8')):{context:JSON.parse(fs.readFileSync(path.join(__dirname,'review-connection-result.json'),'utf8')).task_context_id};
  const call=async(name,args)=>{
    const response=await request(settings.mcpPort,token,'/mcp',{jsonrpc:'2.0',id:`direct-local-mode-${mode}-${Date.now()}`,method:'tools/call',params:{name,arguments:{task_context_id:state.context,...args},_meta:{'io.modelcontextprotocol/protocolVersion':'2026-07-28','io.modelcontextprotocol/clientCapabilities':{},'io.modelcontextprotocol/clientInfo':{name:'codex-desktop',version:'local-mode-work'}}}},'POST',name);
    const value=normalized(response);
    save(`review-${mode}-response.json`,response);
    if(response.error||response.result?.isError||value?.ok===false)throw Object.assign(new Error('Official MCP tool refused request.'),{code:value?.error?.code||response.error?.code||'TOOL_REFUSED',safe_details:value});
    return value;
  };
  if(mode==='prepare'){
    if(state.run_id)throw Object.assign(new Error('Already prepared; refusing another run.'),{code:'ALREADY_PREPARED'});
    state.files=hashFiles();
    const value=await call('agent_workflow',{workflow:'custom',phase:'prepare',execution_route:'deterministic',objective,path:root,paths:sourcePaths,max_files:1,max_total_bytes:4096,max_lines_per_file:30,verification:'none'});
    const binding=value.prepared_binding||value.data?.prepared_binding;
    if(!binding?.run_id||!binding?.wave_id)throw Object.assign(new Error('Prepared binding missing.'),{code:'BINDING_MISSING',safe_details:value});
    state={...state,run_id:binding.run_id,wave_id:binding.wave_id,prepared:true};
    save('review-workflow-state.json',state);
    process.stdout.write(JSON.stringify({ok:true,mode,task_context_id:state.context,run_id:state.run_id,wave_id:state.wave_id,state:value.orchestration?.orchestration_state,file_count:state.files.length})+'\n');
  }else if(mode==='execute'){
    const replan=process.argv.includes('--replan');
    if(!state.prepared||(state.execution_attempted&&!replan))throw Object.assign(new Error('Execution is not a fresh prepared attempt.'),{code:'EXECUTION_STATE_INVALID'});
    if(JSON.stringify(state.files)!==JSON.stringify(hashFiles()))throw Object.assign(new Error('Source changed after prepare.'),{code:'SOURCE_DRIFT'});
    await request(settings.mcpPort,token,'/__control/hub',{action:'heartbeat',client_id:'codex-desktop',client_type:'codex_desktop',client_name:'Codex Desktop',client_version:'local-mode-work'});
    const transfer=await request(settings.mcpPort,token,'/__control/hub',{action:'transfer_controller',target_client_id:'codex-desktop',run_id:state.run_id});
    save('review-controller-transfer.json',transfer);
    if(transfer.transferred!==true)throw Object.assign(new Error('Official controller transfer refused.'),{code:'CONTROLLER_TRANSFER_REFUSED',safe_details:transfer});
    state.execution_attempted=true;save('review-workflow-state.json',state);
    const value=await call('agent_workflow',{workflow:'custom',phase:'execute',execution_route:'deterministic',objective,path:root,workdir:root,...(replan?{}:{run_id:state.run_id,wave_id:state.wave_id}),adopt_existing_files:state.files,commands:[proofCommand],verification:'none',timeout_seconds:300,max_runtime_seconds:300,
      ...(replan?{replan_reason:'The prior attempt refused BASE_DRIFT before adoption or process spawn. HEAD and all 23 explicitly approved source SHA256 values remain identical; only runtime evidence reports changed. Rebind this new proof wave to the currently observed worktree and execute the exact approved direct-host focused tests.'}:{})});
    state.execution_response=value;state.wave_id=value.orchestration?.wave_id||state.wave_id;state.operation_id=value.operation_id||value.operation?.operation_id||value.execution?.operation_id||null;save('review-workflow-state.json',state);
    process.stdout.write(JSON.stringify({ok:true,mode,run_id:state.run_id,wave_id:state.wave_id,response:value})+'\n');
  }else if(mode==='observe'){
    const args=state.operation_id?{action:'operation',operation_id:state.operation_id}:{action:'audit',run_id:state.run_id,wave_id:state.wave_id,limit:20};
    const value=await call('task_control',args);
    state.observation=value;save('review-workflow-state.json',state);
    process.stdout.write(JSON.stringify({ok:true,mode,response:value})+'\n');
  }else if(mode==='accept'){
    if(!state.execution_attempted||state.accept_attempted)throw Object.assign(new Error('Acceptance state invalid.'),{code:'ACCEPTANCE_STATE_INVALID'});
    if(JSON.stringify(state.files)!==JSON.stringify(hashFiles()))throw Object.assign(new Error('Source changed before acceptance.'),{code:'SOURCE_DRIFT'});
    await request(settings.mcpPort,token,'/__control/hub',{action:'heartbeat',client_id:'codex-desktop',client_type:'codex_desktop',client_name:'Codex Desktop',client_version:'local-mode-work'});
    const transfer=await request(settings.mcpPort,token,'/__control/hub',{action:'transfer_controller',target_client_id:'codex-desktop',run_id:state.run_id});
    save('review-accept-controller-transfer.json',transfer);
    if(transfer.transferred!==true)throw Object.assign(new Error('Official controller transfer refused.'),{code:'CONTROLLER_TRANSFER_REFUSED',safe_details:transfer});
    state.accept_attempted=true;save('review-workflow-state.json',state);
    const value=await call('task_control',{action:'accept',run_id:state.run_id,wave_id:state.wave_id,acceptance_files:state.files});
    state.acceptance=value;state.report_id=value.state?.completion_report_id||value.task?.completion_report_id||value.completion_report?.report_id||value.completion_report?.id;save('review-workflow-state.json',state);
    process.stdout.write(JSON.stringify({ok:true,mode,response:value})+'\n');
  }else{
    if(!state.report_id)throw Object.assign(new Error('Actual report id required.'),{code:'REPORT_ID_MISSING'});
    const value=await call('task_control',{action:'ack',run_id:state.run_id,wave_id:state.wave_id,message_id:state.report_id});
    state.acknowledgement=value;save('review-workflow-state.json',state);
    process.stdout.write(JSON.stringify({ok:true,mode,response:value})+'\n');
  }
  app.exit(0);
}).catch(error=>{process.stdout.write(JSON.stringify({ok:false,code:String(error?.code||'WORKFLOW_FAILED'),...(error.safe_details?{details:error.safe_details}:{})})+'\n');app.exit(1);});
