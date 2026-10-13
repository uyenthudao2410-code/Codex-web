const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const net = require('node:net');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { normalize, validateRuntimeSettings } = require('../electron/services/config');
const { componentOwnsPath } = require('../electron/services/componentRevision');
const {
  RecoveryPlaneService,
  recoveryMcpHealthObservation,
  recoveryTunnelFingerprint,
  recoveryTunnelListenerPid,
  parseLoopbackListenerPid,
  stopExactTree: terminateExactTree
} = require('../electron/services/recoveryPlaneService');
const { observeProcessIdentity } = require('../electron/services/processIdentity');
const { installTunnelProcessFixture, withWorkingDirectory } = require('./helpers/tunnel-process-fixture');

const root = path.resolve(__dirname, '..');
const python = path.join(root, 'resources', 'native-python', 'python.exe');
const script = path.join(root, 'resources', 'recovery-mcp', 'recovery_mcp.py');
function freePort() { return new Promise((resolve,reject)=>{const server=net.createServer();server.once('error',reject);server.listen(0,'127.0.0.1',()=>{const port=server.address().port;server.close((error)=>error?reject(error):resolve(port));});}); }
function processAlive(pid) { try { process.kill(pid,0);return true; } catch { return false; } }
async function waitForPidExit(pid,timeoutMs=5000){const deadline=Date.now()+timeoutMs;while(Date.now()<deadline&&processAlive(pid)){await new Promise((resolve)=>setTimeout(resolve,50));}assert.equal(processAlive(pid),false,`PID ${pid} remained alive`);}
async function waitConnect(port,timeoutMs=5000){const deadline=Date.now()+timeoutMs;while(Date.now()<deadline){const ok=await new Promise((resolve)=>{const socket=net.connect({host:'127.0.0.1',port});let done=false;const finish=(value)=>{if(done)return;done=true;socket.destroy();resolve(value);};socket.once('connect',()=>finish(true));socket.once('error',()=>finish(false));setTimeout(()=>finish(false),150);});if(ok)return;await new Promise((r)=>setTimeout(r,50));}throw new Error(`port ${port} not ready`);}
async function httpRequest(port,options={}){return new Promise((resolve,reject)=>{const body=options.body?Buffer.from(options.body):null;const req=http.request({host:'127.0.0.1',port,path:options.path||'/',method:options.method||'GET',headers:options.headers||{}},(res)=>{const chunks=[];res.on('data',(c)=>chunks.push(c));res.on('end',()=>{const joined=Buffer.concat(chunks);const raw=joined.toString('utf8');let parsed=null;try{parsed=raw?JSON.parse(raw):null;}catch{}resolve({status:res.statusCode,headers:res.headers,body:parsed,raw});});});req.once('error',reject);if(body)req.end(body);else req.end();});}
async function request(port,token,payload){const body=JSON.stringify(payload);return httpRequest(port,{path:'/mcp',method:'POST',headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json','Content-Length':Buffer.byteLength(body)},body});}
async function stopProcess(child){if(!child)return;if(processAlive(child.pid))await stopExactTree(child.pid);await new Promise((resolve)=>{if(!processAlive(child.pid))return resolve();const timer=setTimeout(resolve,1500);child.once('exit',()=>{clearTimeout(timer);resolve();});});}
async function stopExactTree(pid){const observed=observeProcessIdentity(pid,{noCache:true});assert.equal(observed.state,'live',`PID ${pid} identity unavailable before test cleanup`);return terminateExactTree({pid,process_start_token:observed.process_start_token});}
function currentProcessStartToken(){const observed=observeProcessIdentity(process.pid,{noCache:true});assert.equal(observed.state,'live');return observed.process_start_token;}

if(process.platform!=='win32') test('Recovery plane process tests require Windows',{skip:true},()=>{});
else {
  test('Recovery settings use separate ports and reject a shared tunnel identity',()=>{const value=normalize({});assert.equal(value.recoveryMcpPort,18767);assert.equal(value.recoveryHealthPort,18083);assert.equal(value.recoveryTunnelId,'');assert.doesNotThrow(()=>validateRuntimeSettings(value));assert.throws(()=>validateRuntimeSettings({...value,recoveryTunnelId:'tunnel_same1',tunnelId:'tunnel_same1'}),/independent|khác|same|Recovery/i);assert.throws(()=>validateRuntimeSettings({...value,recoveryMcpPort:value.mcpPort}),/port|cổng/i);});
  test('Recovery Host component owns independent recovery plane source',()=>{assert.equal(componentOwnsPath('recovery_host','electron/services/recoveryPlaneService.js'),true);assert.equal(componentOwnsPath('recovery_host','resources/recovery-mcp/recovery_mcp.py'),true);});
  test('Recovery Plane periodic identity gates use the async observer without weakening exact matching', async () => {
    const token = '10000000000000901';
    const deviceId = '12345678-1234-4123-8123-123456789abc';
    let syncCalls = 0;
    let asyncCalls = 0;
    const service = new RecoveryPlaneService({
      paths: {},
      log: null,
      deviceIdentity: {
        version: 1,
        device_id: deviceId,
        display_name: 'Async identity test',
        created_at: '2026-08-17T00:00:00.000Z'
      },
      deviceInstanceId: 'async-identity-instance-0001',
      processIdentityObserver: () => {
        syncCalls += 1;
        throw new Error('periodic exact identity must not use the blocking observer');
      },
      asyncProcessIdentityObserver: async (pid) => {
        asyncCalls += 1;
        return { state: 'live', pid, process_start_token: token };
      }
    });
    const identity = await service.ownedIdentity({
      recoveryMcpPid: process.pid,
      recoveryMcpProcessStartToken: token,
      recoveryMcpDeviceId: deviceId
    }, 'recoveryMcp', 'RECOVERY_MCP');
    assert.deepEqual(identity, { pid: process.pid, process_start_token: token });
    assert.equal(asyncCalls, 1);
    assert.equal(syncCalls, 0);

    service.asyncProcessIdentityObserver = async (pid) => ({
      state: 'live',
      pid,
      process_start_token: '10000000000000902'
    });
    assert.equal(await service.ownedIdentity({
      recoveryMcpPid: process.pid,
      recoveryMcpProcessStartToken: token,
      recoveryMcpDeviceId: deviceId
    }, 'recoveryMcp', 'RECOVERY_MCP'), null);
  });
  test('standalone Recovery MCP authenticates, lists only break-glass tools, and sends only fixed health.repair',async(t)=>{const temp=fs.mkdtempSync(path.join(os.tmpdir(),'webmcp-recovery-mcp-'));t.after(()=>fs.rmSync(temp,{recursive:true,force:true,maxRetries:10,retryDelay:50}));const token=crypto.randomBytes(32).toString('base64url');const hostToken=crypto.randomBytes(32).toString('base64url');const deviceId='12345678-1234-4123-8123-123456789abc';const deviceInstanceId='recovery-device-instance-0001';const recoveryPort=await freePort();let observedBody=null;const hostServer=http.createServer((req,res)=>{assert.equal(req.url,'/v1/call');assert.equal(req.headers.authorization,`Bearer ${hostToken}`);const chunks=[];req.on('data',(c)=>chunks.push(c));req.on('end',()=>{observedBody=JSON.parse(Buffer.concat(chunks));const body=JSON.stringify({ok:true,data:{healthy:true}});res.writeHead(200,{'Content-Type':'application/json','Content-Length':Buffer.byteLength(body)});res.end(body);});});await new Promise((resolve)=>hostServer.listen(0,'127.0.0.1',resolve));t.after(()=>hostServer.close());fs.writeFileSync(path.join(temp,'recovery-host.json'),JSON.stringify({version:1,host:'127.0.0.1',port:hostServer.address().port,token:hostToken,owner:'recovery-host',owner_pid:process.pid,instance_id:'recovery-host-test',device_id:deviceId,device_instance_id:deviceInstanceId,device_display_name:'Recovery test device'}));fs.writeFileSync(path.join(temp,'runtime-state.json'),JSON.stringify({nativePid:process.pid,tunnelPid:process.pid}));let stderr='';const child=spawn(python,['-u',script,'--host','127.0.0.1','--port',String(recoveryPort),'--data-root',temp],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe'],env:{...process.env,WEBCODEX_RECOVERY_AUTH_TOKEN:token,WEBCODEX_RECOVERY_DEVICE_ID:deviceId,WEBCODEX_RECOVERY_DEVICE_INSTANCE_ID:deviceInstanceId,WEBCODEX_RECOVERY_DEVICE_DISPLAY_NAME:'Recovery test device'}});child.stderr.on('data',(chunk)=>{stderr+=chunk.toString();});t.after(()=>stopProcess(child));await waitConnect(recoveryPort);assert.equal(processAlive(child.pid),true,stderr||'Recovery MCP exited before health proof');const health=await httpRequest(recoveryPort,{path:'/healthz'});assert.equal(health.status,200,health.raw);assert.equal(health.body?.service,'recovery-mcp',health.raw);assert.equal(health.body?.mode,'independent_mcp_tunnel_v1',health.raw);assert.equal(health.body?.pid,child.pid,health.raw);assert.equal(health.body?.device_id,deviceId,health.raw);assert.equal(health.body?.device_instance_id,deviceInstanceId,health.raw);const unauthorized=await request(recoveryPort,'wrong-token-which-is-not-valid-00000000',{jsonrpc:'2.0',id:1,method:'ping',params:{}});assert.equal(unauthorized.status,401,unauthorized.raw);assert.equal(unauthorized.body?.error,'unauthorized',unauthorized.raw);const initialized=await request(recoveryPort,token,{jsonrpc:'2.0',id:2,method:'initialize',params:{protocolVersion:'2025-06-18',capabilities:{},clientInfo:{name:'test',version:'1'}}});assert.equal(initialized.body?.result?.protocolVersion,'2025-06-18',initialized.raw);assert.ok(initialized.headers['mcp-session-id']);const listed=await request(recoveryPort,token,{jsonrpc:'2.0',id:3,method:'tools/list',params:{}});assert.deepEqual(listed.body?.result?.tools.map((item)=>item.name),['recovery_status','repair_primary_runtime']);const status=await request(recoveryPort,token,{jsonrpc:'2.0',id:4,method:'tools/call',params:{name:'recovery_status',arguments:{}}});assert.equal(status.body?.result?.structuredContent?.recovery_host?.alive,true,status.raw);assert.equal(status.body?.result?.structuredContent?.device?.device_id,deviceId,status.raw);const refused=await request(recoveryPort,token,{jsonrpc:'2.0',id:5,method:'tools/call',params:{name:'repair_primary_runtime',arguments:{confirm:false}}});assert.match(refused.body?.error?.message||refused.raw,/confirm=true/);const repaired=await request(recoveryPort,token,{jsonrpc:'2.0',id:6,method:'tools/call',params:{name:'repair_primary_runtime',arguments:{confirm:true}}});assert.equal(repaired.body?.result?.structuredContent?.recovery_host?.alive,true,repaired.raw);assert.equal(repaired.body?.result?.structuredContent?.device?.device_id,deviceId,repaired.raw);assert.deepEqual(observedBody,{action:'health.repair',args:[]});});
  test('Recovery Plane replaces a killed owned Recovery MCP with a new device-bound PID on the same port',async(t)=>{const temp=fs.mkdtempSync(path.join(os.tmpdir(),'webmcp-recovery-mcp-replace-'));const token=crypto.randomBytes(32).toString('base64url');const deviceId='12345678-1234-4123-8123-123456789abc';const deviceInstanceId='recovery-device-instance-replace-0001';const recoveryPort=await freePort();const stateFile=path.join(temp,'recovery-plane-state.json');const paths={portablePython:()=>python,recoveryMcpScript:()=>script,recoveryPlaneStateFile:()=>stateFile,recoveryMcpLogFile:()=>path.join(temp,'recovery-mcp.log'),dataRoot:()=>temp};const service=new RecoveryPlaneService({paths,log:{info(){},warn(){},error(){}},deviceIdentity:{version:1,device_id:deviceId,display_name:'Recovery replacement test',created_at:'2026-08-17T00:00:00.000Z'},deviceInstanceId});let activePid=0;t.after(async()=>{if(processAlive(activePid)){await stopExactTree(activePid);await waitForPidExit(activePid).catch(()=>{});}fs.rmSync(temp,{recursive:true,force:true,maxRetries:10,retryDelay:50});});const settings={recoveryMcpPort:recoveryPort};const first=await service.ensureMcp(settings,token);activePid=first.pid;assert.equal(first.state,'healthy');assert.equal(first.replaced,true);assert.equal(first.port,recoveryPort);assert.equal(first.device_id,deviceId);assert.equal(first.device_instance_id,deviceInstanceId);assert.equal(await recoveryTunnelListenerPid(recoveryPort),first.pid);await stopExactTree(first.pid);await waitForPidExit(first.pid);const second=await service.ensureMcp(settings,token);activePid=second.pid;assert.equal(second.state,'healthy');assert.equal(second.replaced,true);assert.notEqual(second.pid,first.pid);assert.equal(second.port,recoveryPort);assert.equal(second.device_id,deviceId);assert.equal(second.device_instance_id,deviceInstanceId);assert.equal(await recoveryTunnelListenerPid(recoveryPort),second.pid);const health=await httpRequest(recoveryPort,{path:'/healthz'});assert.equal(health.status,200,health.raw);assert.equal(health.body?.pid,second.pid,health.raw);assert.equal(health.body?.device_id,deviceId,health.raw);assert.equal(health.body?.device_instance_id,deviceInstanceId,health.raw);const persisted=JSON.parse(fs.readFileSync(stateFile,'utf8'));assert.equal(persisted.recoveryMcpPid,second.pid);assert.equal(persisted.recoveryMcpPort,recoveryPort);assert.equal(persisted.recoveryMcpDeviceId,deviceId);assert.equal(persisted.recoveryMcpDeviceInstanceId,deviceInstanceId);assert.match(persisted.recoveryMcpProcessStartToken,/^[0-9]+$/);});
  test('Recovery MCP health observation reports the exact failed identity predicate without exposing credentials',async(t)=>{const port=await freePort();const server=http.createServer((_request,response)=>{const body=JSON.stringify({ok:true,service:'recovery-mcp',pid:process.pid,instance_id:'observed-instance',device_id:'observed-device',device_instance_id:'observed-lifecycle',activation_epoch_id:'observed-epoch'});response.writeHead(200,{'Content-Type':'application/json','Content-Length':Buffer.byteLength(body)});response.end(body);});await new Promise((resolve)=>server.listen(port,'127.0.0.1',resolve));t.after(()=>server.close());const observation=await recoveryMcpHealthObservation(port,'not-reported','expected-device','observed-lifecycle','observed-epoch',process.pid,'observed-instance',{timeoutMs:5000});assert.equal(observation.ok,false);assert.equal(observation.failure_kind,'device_id_mismatch');assert.equal(observation.payload,null);assert.doesNotMatch(JSON.stringify(observation),/not-reported/);});
  test('Recovery Plane service source keeps tunnel failure domain independent',()=>{const source=fs.readFileSync(path.join(root,'electron','services','recoveryPlaneService.js'),'utf8');assert.match(source,/channel=main/);assert.doesNotMatch(source,/channel=recovery/);assert.match(source,/--require-control-plane-poll/);assert.match(source,/detached:\s*true/);assert.match(source,/recoveryTunnelId/);assert.match(source,/RECOVERY_TUNNEL_ID_NOT_INDEPENDENT/);assert.doesNotMatch(source,/settings\.tunnelId[^\n]*--control-plane\.tunnel-id/);});
  test('Recovery Plane legacy migration remains proof-gated and foreign-device fail-closed',()=>{const source=fs.readFileSync(path.join(root,'electron','services','recoveryPlaneService.js'),'utf8');assert.match(source,/preflightLegacyOwnershipMigration/);assert.match(source,/recoveryMcpHealth/);assert.match(source,/recoveryTunnelReady/);assert.match(source,/RECOVERY_MCP_LEGACY_MIGRATION_UNVERIFIED/);assert.match(source,/RECOVERY_TUNNEL_LEGACY_MIGRATION_UNVERIFIED/);assert.match(source,/RECOVERY_MCP_FOREIGN_DEVICE/);assert.match(source,/RECOVERY_TUNNEL_FOREIGN_DEVICE/);});
  test('Recovery Plane refuses live foreign or unverified owners without terminating the PID',()=>{const deviceId='12345678-1234-4123-8123-123456789abc';const service=new RecoveryPlaneService({paths:{},log:null,deviceIdentity:{version:1,device_id:deviceId,display_name:'F8 live owner test',created_at:'2026-08-17T00:00:00.000Z'},deviceInstanceId:'f8-live-owner-instance-0001'});assert.equal(processAlive(process.pid),true);assert.throws(()=>service.assertOwnedLive(process.pid,'87654321-4321-4321-8321-cba987654321','RECOVERY_MCP'),{code:'RECOVERY_MCP_FOREIGN_DEVICE'});assert.equal(processAlive(process.pid),true);assert.throws(()=>service.assertOwnedLive(process.pid,'','RECOVERY_TUNNEL'),{code:'RECOVERY_TUNNEL_OWNER_UNVERIFIED'});assert.equal(processAlive(process.pid),true);});
  test('Recovery Plane stop never terminates unavailable or tokenless process receipts',async()=>{const deviceId='12345678-1234-4123-8123-123456789abc';const token='10000000000000101';for(const scenario of [{name:'unavailable',state:{state:'unavailable',pid:process.pid,code:'PROCESS_IDENTITY_UNVERIFIED'},code:'RECOVERY_MCP_PROCESS_IDENTITY_UNVERIFIED'},{name:'missing',state:{state:'live',pid:process.pid,process_start_token:token},code:'RECOVERY_MCP_PROCESS_IDENTITY_UNVERIFIED',missing:true}]){let persisted={recoveryMcpPid:process.pid,recoveryMcpProcessStartToken:scenario.missing?null:token,recoveryMcpDeviceId:deviceId};const terminated=[];const service=new RecoveryPlaneService({paths:{},log:null,deviceIdentity:{version:1,device_id:deviceId,display_name:'Exact receipt test',created_at:'2026-08-17T00:00:00.000Z'},deviceInstanceId:'exact-receipt-instance',processIdentityObserver:()=>scenario.state,exactProcessTerminator:async(identity)=>{terminated.push(identity);}});service.readState=()=>persisted;service.updateState=(patch)=>{persisted={...persisted,...patch};};await assert.rejects(service.stop(),{code:scenario.code},scenario.name);assert.deepEqual(terminated,[],scenario.name);assert.equal(persisted.recoveryMcpPid,process.pid,scenario.name);}});
  test('Recovery Plane stop forwards exact MCP identity and clears only the matching receipt',async()=>{const deviceId='12345678-1234-4123-8123-123456789abc';const token='10000000000000103';const temp=fs.mkdtempSync(path.join(os.tmpdir(),'webcodex-recovery-exact-stop-'));const stateFile=path.join(temp,'state.json');fs.writeFileSync(stateFile,JSON.stringify({recoveryMcpPid:process.pid,recoveryMcpProcessStartToken:token,recoveryMcpDeviceId:deviceId}));const terminated=[];const service=new RecoveryPlaneService({paths:{recoveryPlaneStateFile:()=>stateFile},log:null,deviceIdentity:{version:1,device_id:deviceId,display_name:'Exact receipt test',created_at:'2026-08-17T00:00:00.000Z'},deviceInstanceId:'exact-receipt-instance',processIdentityObserver:()=>({state:'live',pid:process.pid,process_start_token:token}),exactProcessTerminator:async(identity)=>{terminated.push(identity);}});try{assert.equal(await service.stop(),true);assert.deepEqual(terminated,[{pid:process.pid,process_start_token:token}]);const persisted=JSON.parse(fs.readFileSync(stateFile,'utf8'));assert.equal(persisted.recoveryMcpPid,null);assert.equal(persisted.recoveryMcpProcessStartToken,null);}finally{fs.rmSync(temp,{recursive:true,force:true});}});
  test('Recovery Plane migrates a live legacy tunnel candidate only after exact fingerprint and readiness proof',async()=>{const settings={recoveryMcpPort:18767,recoveryHealthPort:18083,recoveryTunnelId:'tunnel_recovery_legacy',tunnelId:'tunnel_primary',proxyUrl:''};const authToken='x'.repeat(32);const token=currentProcessStartToken();const deviceIdentity={version:1,device_id:'12345678-1234-4123-8123-123456789abc',display_name:'Recovery migration test',created_at:'2026-08-17T00:00:00.000Z'};const service=new RecoveryPlaneService({paths:{},log:null,deviceIdentity,deviceInstanceId:'device-instance-migration-0001'});let state={recoveryTunnelCandidatePid:process.pid,recoveryTunnelCandidateProcessStartToken:token,recoveryTunnelCandidateFingerprint:recoveryTunnelFingerprint(settings,authToken,''),recoveryTunnelCandidateDeviceId:null};service.readState=()=>state;let updated=null;service.updateState=(patch)=>{updated=patch;state={...state,...patch};};const plan=await service.preflightLegacyOwnershipMigration(settings,authToken,{tunnelReady:async(_paths,port,pid)=>{assert.equal(port,settings.recoveryHealthPort);assert.equal(pid,process.pid);return true;}});assert.equal(plan.required,true);assert.equal(plan.recoveryTunnelCandidatePid,process.pid);assert.equal(plan.recoveryTunnelCandidateProcessStartToken,token);await service.applyLegacyOwnershipMigration(plan);assert.equal(updated.recoveryTunnelCandidateDeviceId,deviceIdentity.device_id);assert.equal(updated.recoveryTunnelCandidateDeviceInstanceId,'device-instance-migration-0001');state={recoveryTunnelCandidatePid:process.pid,recoveryTunnelCandidateProcessStartToken:token,recoveryTunnelCandidateFingerprint:'0'.repeat(64),recoveryTunnelCandidateDeviceId:null};await assert.rejects(service.preflightLegacyOwnershipMigration(settings,authToken,{tunnelReady:async()=>true}),{code:'RECOVERY_TUNNEL_CANDIDATE_LEGACY_MIGRATION_UNVERIFIED'});});
  test('Recovery Plane boundedly rereads an exact legacy candidate until it is promoted',async()=>{const settings={recoveryMcpPort:18767,recoveryHealthPort:18083,recoveryTunnelId:'tunnel_recovery_legacy',tunnelId:'tunnel_primary',proxyUrl:''};const authToken='x'.repeat(32);const token=currentProcessStartToken();const deviceIdentity={version:1,device_id:'12345678-1234-4123-8123-123456789abc',display_name:'Recovery stabilization test',created_at:'2026-08-17T00:00:00.000Z'};const service=new RecoveryPlaneService({paths:{},log:null,deviceIdentity,deviceInstanceId:'device-instance-stabilization-0001'});service.legacyCandidateStabilizationAttempts=2;service.legacyCandidateStabilizationDelayMs=0;const fingerprint=recoveryTunnelFingerprint(settings,authToken,'');let state={recoveryTunnelCandidatePid:process.pid,recoveryTunnelCandidateProcessStartToken:token,recoveryTunnelCandidateFingerprint:fingerprint,recoveryTunnelCandidateDeviceId:null};service.readState=()=>state;let readyCalls=0;const plan=await service.preflightLegacyOwnershipMigration(settings,authToken,{wait:async()=>{},tunnelReady:async(_paths,port,pid)=>{assert.equal(port,settings.recoveryHealthPort);assert.equal(pid,process.pid);readyCalls+=1;if(readyCalls===1){state={recoveryTunnelPid:process.pid,recoveryTunnelProcessStartToken:token,recoveryTunnelFingerprint:fingerprint,recoveryTunnelDeviceId:null,recoveryTunnelCandidatePid:null,recoveryTunnelCandidateProcessStartToken:null,recoveryTunnelCandidateFingerprint:null,recoveryTunnelCandidateDeviceId:null};return false;}return true;}});assert.equal(plan.required,true);assert.equal(plan.recoveryTunnelPid,process.pid);assert.equal(plan.recoveryTunnelProcessStartToken,token);assert.equal(plan.recoveryTunnelCandidatePid,null);assert.equal(readyCalls,2);});
  test('Recovery Plane rejects a candidate PID change during legacy stabilization',async()=>{const settings={recoveryMcpPort:18767,recoveryHealthPort:18083,recoveryTunnelId:'tunnel_recovery_legacy',tunnelId:'tunnel_primary',proxyUrl:''};const authToken='x'.repeat(32);const token=currentProcessStartToken();const deviceIdentity={version:1,device_id:'12345678-1234-4123-8123-123456789abc',display_name:'Recovery stabilization test',created_at:'2026-08-17T00:00:00.000Z'};const service=new RecoveryPlaneService({paths:{},log:null,deviceIdentity,deviceInstanceId:'device-instance-stabilization-0002'});service.legacyCandidateStabilizationAttempts=2;service.legacyCandidateStabilizationDelayMs=0;const fingerprint=recoveryTunnelFingerprint(settings,authToken,'');let reads=0;service.readState=()=>{reads+=1;return{recoveryTunnelCandidatePid:reads===1?process.pid:process.pid+100000,recoveryTunnelCandidateProcessStartToken:token,recoveryTunnelCandidateFingerprint:fingerprint,recoveryTunnelCandidateDeviceId:null};};await assert.rejects(service.preflightLegacyOwnershipMigration(settings,authToken,{wait:async()=>{},tunnelReady:async()=>false}),{code:'RECOVERY_TUNNEL_CANDIDATE_LEGACY_MIGRATION_UNVERIFIED'});});
  test('Recovery Tunnel retires exact owned receipts before unknown listener rejection',()=>{const source=fs.readFileSync(path.join(root,'electron','services','recoveryPlaneService.js'),'utf8');const ensureStart=source.indexOf('async ensureTunnel');const candidateProof=source.indexOf("ownedIdentity(state, 'recoveryTunnelCandidate'",ensureStart);const primaryProof=source.indexOf("ownedIdentity(state, 'recoveryTunnel'",ensureStart);const terminate=source.indexOf('terminateOwnedIdentity(identity, prefix',ensureStart);const listenerCheck=source.indexOf('const refreshedListenerPid = await recoveryTunnelListenerPid',ensureStart);assert.ok(primaryProof>ensureStart&&candidateProof>ensureStart&&terminate>candidateProof&&listenerCheck>terminate);assert.match(source.slice(ensureStart,listenerCheck),/sameProcessIdentity/);assert.doesNotMatch(source.slice(ensureStart,listenerCheck),/taskkill\.exe/);});
  test('Recovery Tunnel startup budget covers the default control-plane long poll',()=>{const source=fs.readFileSync(path.join(root,'electron','services','recoveryPlaneService.js'),'utf8');const match=source.match(/RECOVERY_TUNNEL_START_ATTEMPTS\s*=\s*(\d+)/);assert.ok(match);assert.ok(Number(match[1])>=80,'startup budget must exceed 30s poll + 5s guardrail at 500ms cadence');});
  test('Recovery Tunnel listener ownership resolves the exact loopback PID',async(t)=>{const port=await freePort();const server=net.createServer();await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(port,'127.0.0.1',resolve);});t.after(()=>server.close());assert.equal(await recoveryTunnelListenerPid(port),process.pid);});
  test('Recovery Plane replaces only a killed Recovery Tunnel while preserving the real Recovery MCP PID and device identity',async(t)=>{
    const temp=fs.mkdtempSync(path.join(os.tmpdir(),'webmcp-recovery-tunnel-real-'));
    const fixtureDir=path.join(temp,'tunnel-fixture');
    installTunnelProcessFixture(fixtureDir);
    const authToken=crypto.randomBytes(32).toString('base64url');
    const runtimeApiKey='recovery-runtime-key-local-only';
    const deviceId='12345678-1234-4123-8123-123456789abc';
    const deviceInstanceId='recovery-tunnel-real-instance-0001';
    const recoveryMcpPort=await freePort();
    const recoveryHealthPort=await freePort();
    const stateFile=path.join(temp,'recovery-plane-state.json');
    const paths={
      portablePython:()=>python,
      recoveryMcpScript:()=>script,
      recoveryPlaneStateFile:()=>stateFile,
      recoveryMcpLogFile:()=>path.join(temp,'recovery-mcp.log'),
      recoveryTunnelLogFile:()=>path.join(temp,'recovery-tunnel.log'),
      tunnelExecutable:()=>process.execPath,
      dataRoot:()=>temp
    };
    const service=new RecoveryPlaneService({paths,log:{info(){},warn(){},error(){}},deviceIdentity:{version:1,device_id:deviceId,display_name:'Recovery tunnel PID test',created_at:'2026-08-17T00:00:00.000Z'},deviceInstanceId});
    const settings={recoveryMcpPort,recoveryHealthPort,recoveryTunnelId:'tunnel_recovery_pid_real',tunnelId:'tunnel_primary_pid_real',proxyUrl:'',effectiveProxyUrl:''};
    t.after(async()=>{
      let state={};
      try{state=JSON.parse(fs.readFileSync(stateFile,'utf8'));}catch{}
      for(const pid of [state.recoveryTunnelCandidatePid,state.recoveryTunnelPid,state.recoveryMcpPid]){
        if(processAlive(pid)){await stopExactTree(pid);await waitForPidExit(pid).catch(()=>{});}
      }
      fs.rmSync(temp,{recursive:true,force:true,maxRetries:10,retryDelay:50});
    });

    const first=await withWorkingDirectory(fixtureDir,()=>service.ensure(settings,{authToken,runtimeApiKey}));
    const firstMcpPid=first.mcp.pid;
    const firstTunnelPid=first.tunnel.pid;
    assert.equal(first.mcp.state,'healthy');
    assert.equal(first.tunnel.state,'healthy');
    assert.equal(first.mcp.device_id,deviceId);
    assert.equal(first.mcp.device_instance_id,deviceInstanceId);
    assert.equal(await recoveryTunnelListenerPid(recoveryMcpPort),firstMcpPid);
    assert.equal(await recoveryTunnelListenerPid(recoveryHealthPort),firstTunnelPid);
    const firstTunnelHealth=await httpRequest(recoveryHealthPort,{path:'/healthz'});
    assert.equal(firstTunnelHealth.status,200,firstTunnelHealth.raw);
    assert.equal(firstTunnelHealth.body?.pid,firstTunnelPid,firstTunnelHealth.raw);
    const firstMcpHealth=await httpRequest(recoveryMcpPort,{path:'/healthz'});
    assert.equal(firstMcpHealth.body?.pid,firstMcpPid,firstMcpHealth.raw);
    assert.equal(firstMcpHealth.body?.device_id,deviceId,firstMcpHealth.raw);

    await stopExactTree(firstTunnelPid);
    await waitForPidExit(firstTunnelPid);
    assert.equal(processAlive(firstMcpPid),true,'Recovery MCP must remain alive when only Recovery Tunnel is killed');
    const preservedMcpHealth=await httpRequest(recoveryMcpPort,{path:'/healthz'});
    assert.equal(preservedMcpHealth.body?.pid,firstMcpPid,preservedMcpHealth.raw);
    assert.equal(preservedMcpHealth.body?.device_id,deviceId,preservedMcpHealth.raw);

    const second=await withWorkingDirectory(fixtureDir,()=>service.ensure(settings,{authToken,runtimeApiKey}));
    const secondTunnelPid=second.tunnel.pid;
    assert.equal(second.tunnel.state,'healthy',JSON.stringify(second.tunnel));
    assert.equal(second.mcp.pid,firstMcpPid,JSON.stringify(service.lastMcpCurrentObservation));
    assert.equal(second.mcp.replaced,false);
    assert.notEqual(secondTunnelPid,firstTunnelPid);
    assert.equal(processAlive(secondTunnelPid),true);
    assert.equal(await recoveryTunnelListenerPid(recoveryHealthPort),secondTunnelPid);
    const secondTunnelHealth=await httpRequest(recoveryHealthPort,{path:'/healthz'});
    assert.equal(secondTunnelHealth.body?.pid,secondTunnelPid,secondTunnelHealth.raw);
    const persisted=JSON.parse(fs.readFileSync(stateFile,'utf8'));
    assert.equal(persisted.recoveryMcpPid,firstMcpPid);
    assert.equal(persisted.recoveryMcpPort,recoveryMcpPort);
    assert.equal(persisted.recoveryMcpDeviceId,deviceId);
    assert.equal(persisted.recoveryMcpDeviceInstanceId,deviceInstanceId);
    assert.match(persisted.recoveryMcpProcessStartToken,/^[0-9]+$/);
    assert.equal(persisted.recoveryTunnelPid,secondTunnelPid);
    assert.equal(persisted.recoveryTunnelDeviceId,deviceId);
    assert.equal(persisted.recoveryTunnelDeviceInstanceId,deviceInstanceId);
    assert.match(persisted.recoveryTunnelProcessStartToken,/^[0-9]+$/);
  });
  test('Recovery Tunnel keeps candidate ownership separate until readiness',()=>{const source=fs.readFileSync(path.join(root,'electron','services','recoveryPlaneService.js'),'utf8');assert.match(source,/recoveryTunnelCandidatePid/);assert.match(source,/blocked_health_port_in_use/);assert.match(source,/RECOVERY_TUNNEL_HEALTH_PORT_IN_USE/);assert.match(source,/recoveryTunnelListenerPid\(port\)\s*!==\s*Number\(pid\)/);assert.doesNotMatch(source,/updateState\(\{\s*recoveryTunnelPid:\s*child\.pid,\s*recoveryTunnelFingerprint:\s*fingerprint,\s*recoveryTunnelConfigured:\s*true,\s*recoveryTunnelState:\s*'starting'/);});
  test('Recovery Plane serializes overlapping ensure calls',async()=>{const service=new RecoveryPlaneService({paths:{},log:null});let mcpCalls=0;let tunnelCalls=0;service.ensureMcp=async()=>{mcpCalls+=1;return{state:'healthy'};};service.ensureTunnel=async()=>{tunnelCalls+=1;await new Promise((resolve)=>setTimeout(resolve,40));return{state:'healthy',configured:true,pid:123};};const credentials={authToken:'x'.repeat(32),runtimeApiKey:'configured'};const [first,second]=await Promise.all([service.ensure({},credentials),service.ensure({},credentials)]);assert.equal(mcpCalls,1);assert.equal(tunnelCalls,1);assert.equal(first.tunnel.state,'healthy');assert.equal(second.tunnel.state,'healthy');});
  test('Recovery Plane exposes a stable independent-mode identifier',()=>{const source=fs.readFileSync(path.join(root,'electron','services','recoveryPlaneService.js'),'utf8');const host=fs.readFileSync(path.join(root,'electron','services','recoveryHost.js'),'utf8');assert.match(source,/independent_mcp_tunnel_v1/);assert.match(host,/recovery_plane_mode:\s*centralExecutor\s*\?\s*'central-node-agent-v1'\s*:\s*'independent_mcp_tunnel_v1'/);});
  test('invalid Recovery Tunnel configuration deactivates only exact owned tunnel receipts',()=>{const source=fs.readFileSync(path.join(root,'electron','services','recoveryPlaneService.js'),'utf8');assert.match(source,/async deactivateOwnedTunnel\([\s\S]*ownedIdentity\(state, 'recoveryTunnel'[\s\S]*ownedIdentity\(state, 'recoveryTunnelCandidate'[\s\S]*terminateOwnedIdentity\(identity, prefix[\s\S]*recoveryTunnelPid:\s*null/);assert.match(source,/if \(!tunnelId\)[\s\S]*deactivateOwnedTunnel\(state, \{ configured: false, tunnelState: 'not_configured'[^}]*\}\)/);assert.match(source,/blocked_shared_tunnel_id'[\s\S]*RECOVERY_TUNNEL_ID_NOT_INDEPENDENT/);assert.match(source,/blocked_missing_runtime_key'[\s\S]*RECOVERY_TUNNEL_RUNTIME_KEY_MISSING/);});
  test('Recovery Tunnel operator UI exposes independent settings and live header telemetry',()=>{const settingsHtml=fs.readFileSync(path.join(root,'renderer','index.html'),'utf8');const appJs=fs.readFileSync(path.join(root,'renderer','app.js'),'utf8');const browserHtml=fs.readFileSync(path.join(root,'renderer','browser.html'),'utf8');const browserJs=fs.readFileSync(path.join(root,'renderer','browser.js'),'utf8');const browserCss=fs.readFileSync(path.join(root,'renderer','browser.css'),'utf8');const main=fs.readFileSync(path.join(root,'electron','main.js'),'utf8');assert.match(settingsHtml,/id="recoveryTunnelIdInput"/);assert.match(settingsHtml,/id="saveRecoveryTunnel"/);assert.match(settingsHtml,/data-open="openai-tunnels"/);assert.match(appJs,/recoveryTunnelId:\s*central\s*\?\s*String\(existing\.recoveryTunnelId \|\| ''\)\s*:\s*\$\('#recoveryTunnelIdInput'\)\.value\.trim\(\)/);assert.match(appJs,/Central executor không dùng Recovery OpenAI Tunnel tại Windows/);assert.match(appJs,/recoveryHost\?\.recovery_plane\?\.tunnel/);assert.match(browserHtml,/id="recoveryTunnelState"/);assert.match(browserJs,/recoveryHost\?\.recovery_plane\?\.tunnel/);assert.match(browserJs,/state:\s*'connected'/);assert.match(browserJs,/state:\s*'connecting'/);assert.match(browserJs,/state:\s*'not_configured'/);assert.match(browserCss,/service-state span\.warn i/);assert.match(main,/https:\/\/platform\.openai\.com\/settings\/organization\/tunnels/);});
  test('Recovery Tunnel configuration is colocated with the primary Tunnel under Connections',()=>{const html=fs.readFileSync(path.join(root,'renderer','index.html'),'utf8');const deployStart=html.indexOf('setup-legacy-deploy') >= 0 ? html.indexOf('setup-legacy-deploy') : html.indexOf('data-page-view="deploy"');const settingsStart=html.indexOf('data-page-view="settings"');const recoveryInput=html.indexOf('id="recoveryTunnelIdInput"');assert.ok(deployStart>=0);assert.ok(settingsStart>deployStart);assert.ok(recoveryInput>deployStart&&recoveryInput<settingsStart);assert.match(html.slice(deployStart,settingsStart),/Tunnel ID chính[\s\S]*Recovery Tunnel ID/);assert.doesNotMatch(html.slice(settingsStart),/id="recoveryTunnelIdInput"|<h3>Tunnel cứu hộ<\/h3>/);});
  test('Recovery Plane loopback listener parser distinguishes held, idle and malformed rows', () => {
    const fixture = [
      'Active Connections',
      '',
      '  Proto  Local Address          Foreign Address        State           PID',
      '  TCP    127.0.0.1:18083        0.0.0.0:0              LISTENING       1234',
      '  TCP    127.0.0.1:18767        0.0.0.0:0              LISTENING       5678',
      '  TCP    127.0.0.1:18083        127.0.0.1:54321        ESTABLISHED     9999',
      '  UDP    127.0.0.1:18083        *:*                                    1111'
    ].join('\r\n');
    assert.equal(parseLoopbackListenerPid(fixture, 18083), 1234);
    assert.equal(parseLoopbackListenerPid(fixture, 18767), 5678);
    assert.equal(parseLoopbackListenerPid(fixture, 19999), null);
    assert.equal(parseLoopbackListenerPid('', 18083), null);
    assert.equal(parseLoopbackListenerPid(null, 18083), null);
  });
  test('Recovery Plane stop clears an unverifiable tunnel receipt only when its health port proves idle', async (t) => {
    const deviceId = '12345678-1234-4123-8123-123456789abc';
    const token = '10000000000000201';
    const healthPort = await freePort();
    const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'webmcp-recovery-idle-stop-'));
    t.after(() => fs.rmSync(temp, { recursive: true, force: true, maxRetries: 10, retryDelay: 50 }));
    const stateFile = path.join(temp, 'recovery-plane-state.json');
    fs.writeFileSync(stateFile, JSON.stringify({
      version: 1,
      recoveryTunnelPid: process.pid,
      recoveryTunnelProcessStartToken: token,
      recoveryTunnelInstanceId: 'stale-tunnel-instance-0201',
      recoveryTunnelFingerprint: '0'.repeat(64),
      recoveryTunnelActivationEpochId: 'activation-stale-0201',
      recoveryTunnelDeviceId: deviceId,
      recoveryTunnelDeviceInstanceId: 'stale-device-instance-0201'
    }));
    const terminated = [];
    const warnings = [];
    const service = new RecoveryPlaneService({
      paths: { recoveryPlaneStateFile: () => stateFile },
      log: { info() {}, warn(message, meta) { warnings.push({ message, meta }); }, error() {} },
      deviceIdentity: { version: 1, device_id: deviceId, display_name: 'Idle proof test', created_at: '2026-08-17T00:00:00.000Z' },
      deviceInstanceId: 'idle-proof-instance-0201',
      asyncProcessIdentityObserver: async (pid) => ({ state: 'unavailable', pid, code: 'PROCESS_IDENTITY_UNVERIFIED' }),
      exactProcessTerminator: async (identity) => { terminated.push(identity); }
    });
    assert.equal(await service.stop({ recoveryHealthPort: healthPort }), true);
    assert.deepEqual(terminated, [], 'an unverifiable PID must never be terminated');
    assert.equal(processAlive(process.pid), true);
    const persisted = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
    assert.equal(persisted.recoveryTunnelPid, null);
    assert.equal(persisted.recoveryTunnelProcessStartToken, null);
    assert.equal(persisted.recoveryTunnelInstanceId, null);
    assert.equal(persisted.recoveryTunnelState, 'stopped');
    assert.ok(warnings.some((entry) => entry.meta?.prefix === 'recoveryTunnel' && entry.meta?.pid === process.pid),
      'the idle clear must be auditable');
  });
  test('Recovery Plane stop keeps an unverifiable tunnel receipt when the stored PID holds the port', async (t) => {
    const deviceId = '12345678-1234-4123-8123-123456789abc';
    const token = '10000000000000202';
    const server = net.createServer();
    await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
    const heldPort = server.address().port;
    t.after(() => server.close());
    assert.equal(await recoveryTunnelListenerPid(heldPort), process.pid, 'test precondition: netstat must resolve the held port');
    const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'webmcp-recovery-held-stop-'));
    t.after(() => fs.rmSync(temp, { recursive: true, force: true, maxRetries: 10, retryDelay: 50 }));
    const stateFile = path.join(temp, 'recovery-plane-state.json');
    fs.writeFileSync(stateFile, JSON.stringify({
      version: 1,
      recoveryTunnelPid: process.pid,
      recoveryTunnelProcessStartToken: token,
      recoveryTunnelInstanceId: 'held-tunnel-instance-0202',
      recoveryTunnelFingerprint: '0'.repeat(64),
      recoveryTunnelActivationEpochId: 'activation-held-0202',
      recoveryTunnelDeviceId: deviceId,
      recoveryTunnelDeviceInstanceId: 'held-device-instance-0202'
    }));
    const terminated = [];
    const service = new RecoveryPlaneService({
      paths: { recoveryPlaneStateFile: () => stateFile },
      log: null,
      deviceIdentity: { version: 1, device_id: deviceId, display_name: 'Held proof test', created_at: '2026-08-17T00:00:00.000Z' },
      deviceInstanceId: 'held-proof-instance-0202',
      asyncProcessIdentityObserver: async (pid) => ({ state: 'unavailable', pid, code: 'PROCESS_IDENTITY_UNVERIFIED' }),
      exactProcessTerminator: async (identity) => { terminated.push(identity); }
    });
    await assert.rejects(service.stop({ recoveryHealthPort: heldPort }), { code: 'RECOVERY_TUNNEL_PROCESS_IDENTITY_UNVERIFIED' });
    assert.deepEqual(terminated, []);
    const persisted = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
    assert.equal(persisted.recoveryTunnelPid, process.pid, 'a possibly live port holder must keep its receipt');
  });
  test('Recovery Plane ownedIdentity reuses idle proof without proof, port holder, or other errors', async (t) => {
    const deviceId = '12345678-1234-4123-8123-123456789abc';
    const token = '10000000000000203';
    const idlePort = await freePort();
    const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'webmcp-recovery-owned-idle-'));
    t.after(() => fs.rmSync(temp, { recursive: true, force: true, maxRetries: 10, retryDelay: 50 }));
    const stateFile = path.join(temp, 'recovery-plane-state.json');
    const seed = () => fs.writeFileSync(stateFile, JSON.stringify({
      version: 1,
      recoveryMcpPid: process.pid,
      recoveryMcpProcessStartToken: token,
      recoveryMcpInstanceId: 'owned-idle-instance-0203',
      recoveryMcpDeviceId: deviceId,
      recoveryMcpDeviceInstanceId: 'owned-idle-device-0203'
    }));
    const makeService = () => new RecoveryPlaneService({
      paths: { recoveryPlaneStateFile: () => stateFile },
      log: null,
      deviceIdentity: { version: 1, device_id: deviceId, display_name: 'Owned idle test', created_at: '2026-08-17T00:00:00.000Z' },
      deviceInstanceId: 'owned-idle-proof-0203',
      asyncProcessIdentityObserver: async (pid) => ({ state: 'unavailable', pid, code: 'PROCESS_IDENTITY_UNVERIFIED' }),
      exactProcessTerminator: async () => { throw new Error('must never terminate an unverifiable PID'); }
    });
    seed();
    const withoutProof = makeService();
    await assert.rejects(withoutProof.ownedIdentity(withoutProof.readState(), 'recoveryMcp', 'RECOVERY_MCP'), { code: 'RECOVERY_MCP_PROCESS_IDENTITY_UNVERIFIED' });
    assert.equal(JSON.parse(fs.readFileSync(stateFile, 'utf8')).recoveryMcpPid, process.pid);
    const withProof = makeService();
    assert.equal(await withProof.ownedIdentity(withProof.readState(), 'recoveryMcp', 'RECOVERY_MCP', idlePort), null);
    assert.equal(processAlive(process.pid), true);
    assert.equal(JSON.parse(fs.readFileSync(stateFile, 'utf8')).recoveryMcpPid, null);
  });
  test('Recovery Plane ownedIdentity keeps the receipt when the stored PID holds the proof port', async (t) => {
    const deviceId = '12345678-1234-4123-8123-123456789abc';
    const token = '10000000000000204';
    const server = net.createServer();
    await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
    const heldPort = server.address().port;
    t.after(() => server.close());
    const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'webmcp-recovery-owned-held-'));
    t.after(() => fs.rmSync(temp, { recursive: true, force: true, maxRetries: 10, retryDelay: 50 }));
    const stateFile = path.join(temp, 'recovery-plane-state.json');
    fs.writeFileSync(stateFile, JSON.stringify({
      version: 1,
      recoveryMcpPid: process.pid,
      recoveryMcpProcessStartToken: token,
      recoveryMcpInstanceId: 'owned-held-instance-0204',
      recoveryMcpDeviceId: deviceId,
      recoveryMcpDeviceInstanceId: 'owned-held-device-0204'
    }));
    const service = new RecoveryPlaneService({
      paths: { recoveryPlaneStateFile: () => stateFile },
      log: null,
      deviceIdentity: { version: 1, device_id: deviceId, display_name: 'Owned held test', created_at: '2026-08-17T00:00:00.000Z' },
      deviceInstanceId: 'owned-held-proof-0204',
      asyncProcessIdentityObserver: async (pid) => ({ state: 'unavailable', pid, code: 'PROCESS_IDENTITY_UNVERIFIED' }),
      exactProcessTerminator: async () => { throw new Error('must never terminate an unverifiable PID'); }
    });
    await assert.rejects(service.ownedIdentity(service.readState(), 'recoveryMcp', 'RECOVERY_MCP', heldPort), { code: 'RECOVERY_MCP_PROCESS_IDENTITY_UNVERIFIED' });
    assert.equal(JSON.parse(fs.readFileSync(stateFile, 'utf8')).recoveryMcpPid, process.pid);
  });
  test('Recovery Plane deactivate clears unverifiable receipts when unconfigured and ports prove idle', async (t) => {
    const deviceId = '12345678-1234-4123-8123-123456789abc';
    const token = '10000000000000205';
    const idlePort = await freePort();
    const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'webmcp-recovery-deactivate-idle-'));
    t.after(() => fs.rmSync(temp, { recursive: true, force: true, maxRetries: 10, retryDelay: 50 }));
    const stateFile = path.join(temp, 'recovery-plane-state.json');
    fs.writeFileSync(stateFile, JSON.stringify({
      version: 1,
      recoveryTunnelPid: process.pid,
      recoveryTunnelProcessStartToken: token,
      recoveryTunnelInstanceId: 'deactivate-idle-instance-0205',
      recoveryTunnelDeviceId: deviceId,
      recoveryTunnelDeviceInstanceId: 'deactivate-idle-device-0205'
    }));
    const terminated = [];
    const service = new RecoveryPlaneService({
      paths: { recoveryPlaneStateFile: () => stateFile },
      log: null,
      deviceIdentity: { version: 1, device_id: deviceId, display_name: 'Deactivate idle test', created_at: '2026-08-17T00:00:00.000Z' },
      deviceInstanceId: 'deactivate-idle-proof-0205',
      asyncProcessIdentityObserver: async (pid) => ({ state: 'unavailable', pid, code: 'PROCESS_IDENTITY_UNVERIFIED' }),
      exactProcessTerminator: async (identity) => { terminated.push(identity); }
    });
    const result = await service.deactivateOwnedTunnel(service.readState(), { configured: false, tunnelState: 'not_configured', recoveryHealthPort: idlePort });
    assert.equal(result.state, 'not_configured');
    assert.equal(result.pid, null);
    assert.deepEqual(terminated, []);
    const persisted = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
    assert.equal(persisted.recoveryTunnelPid, null);
    assert.equal(persisted.recoveryTunnelConfigured, false);
  });
}
