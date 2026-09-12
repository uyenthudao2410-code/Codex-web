const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const net = require('node:net');
const os = require('node:os');
const path = require('node:path');
const { spawn, spawnSync } = require('node:child_process');

const root = path.resolve(__dirname, '..');
const script = path.join(root, 'resources', 'recovery-supervisor', 'recovery-supervisor.ps1');
const launcher = path.join(root, 'resources', 'recovery-supervisor', 'recovery-supervisor-launcher.vbs');
function hash(file) { return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'); }
function writeJson(file, value) { fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, JSON.stringify(value)); }
function run(args, env=process.env) { return new Promise((resolve, reject) => { const child = spawn('powershell.exe', ['-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',script,...args], { cwd: root, windowsHide: true, stdio: ['ignore','pipe','pipe'], env }); let stdout='';let stderr='';child.stdout.on('data',(c)=>stdout+=c);child.stderr.on('data',(c)=>stderr+=c);child.once('error',reject);child.once('exit',(code)=>resolve({code,stdout:stdout.trim(),stderr:stderr.trim()})); }); }
const transientTempCleanupCodes = new Set(['EACCES', 'EBUSY', 'ENOTEMPTY', 'EPERM']);
function sleepSync(ms) { if(ms>0)Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,ms); }
function removeTemp(temp, options={}) {
  const remove=options.remove||fs.rmSync;
  const sleep=options.sleep||sleepSync;
  const maxOuterRetries=Number.isInteger(options.maxOuterRetries)?options.maxOuterRetries:4;
  const retryBaseDelayMs=Number.isInteger(options.retryBaseDelayMs)?options.retryBaseDelayMs:250;
  for(let attempt=0;;attempt+=1){
    try{
      remove(temp,{recursive:true,force:true,maxRetries:8,retryDelay:50});
      return;
    }catch(error){
      const retryable=process.platform==='win32'&&transientTempCleanupCodes.has(String(error?.code||''));
      if(!retryable||attempt>=maxOuterRetries)throw error;
      sleep(Math.min(1000,retryBaseDelayMs*(attempt+1)));
    }
  }
}
function processAlive(pid) { try { process.kill(pid, 0); return true; } catch { return false; } }
function killFixtureTree(pid) { if(!processAlive(pid))return;spawnSync('taskkill.exe',['/PID',String(pid),'/T','/F'],{windowsHide:true,stdio:'ignore'}); }
async function waitForExit(pid, timeoutMs = 5000) { const deadline=Date.now()+timeoutMs; while(Date.now()<deadline && processAlive(pid)) await new Promise((resolve)=>setTimeout(resolve,50)); assert.equal(processAlive(pid),false,`fixture PID ${pid} remained alive`); }
async function waitForStatus(file, predicate, timeoutMs = 15000) { const deadline=Date.now()+timeoutMs; while(Date.now()<deadline){try{const value=JSON.parse(fs.readFileSync(file,'utf8'));if(predicate(value))return value;}catch{}await new Promise((resolve)=>setTimeout(resolve,100));}throw new Error(`timed out waiting for ${path.basename(file)}`); }
function freePort() { return new Promise((resolve,reject)=>{const server=net.createServer();server.once('error',reject);server.listen(0,'127.0.0.1',()=>{const port=server.address().port;server.close((error)=>error?reject(error):resolve(port));});}); }
function recoveryPing(port,token) { return new Promise((resolve,reject)=>{const body=JSON.stringify({action:'recovery.ping',args:[]});const req=http.request({host:'127.0.0.1',port,path:'/v1/call',method:'POST',headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json','Content-Length':Buffer.byteLength(body)},timeout:1500},(res)=>{const chunks=[];res.on('data',(c)=>chunks.push(c));res.on('end',()=>{try{resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')));}catch(error){reject(error);}});});req.once('timeout',()=>req.destroy(new Error('fixture ping timeout')));req.once('error',reject);req.end(body);}); }
function manifest(temp) { const executable=path.join(process.env.SystemRoot||'C:\\Windows','System32','where.exe'); return {schema_version:1,mode:'packaged',executable,executable_sha256:hash(executable),app_root:temp,arguments:['--recovery-host'],data_root:temp,installed_script_sha256:hash(script),installed_at:new Date().toISOString()}; }
function prior(extra={}) { return {version:1,supervisor_pid:1,supervisor_started_at:new Date().toISOString(),state:'degraded',last_check_at:null,last_healthy_at:null,last_host_pid:null,last_host_instance_id:null,consecutive_failures:0,restart_attempts:[],next_attempt_after:null,suppressed_until:null,last_error_code:null,last_error_message:null,last_spawned_pid:null,manifest_sha256:'0'.repeat(64),task_name:'WebMCP Recovery Supervisor',...extra}; }

if (process.platform !== 'win32') test('Recovery Supervisor runtime tests require Windows', { skip: true }, () => {});
else {
  test('Recovery Supervisor test cleanup retries only bounded transient Windows teardown failures', () => {
    const transientDelays=[];
    let transientAttempts=0;
    removeTemp('ignored-transient',{
      maxOuterRetries:2,
      retryBaseDelayMs:10,
      sleep:(ms)=>transientDelays.push(ms),
      remove:()=>{transientAttempts+=1;if(transientAttempts<3)throw Object.assign(new Error('transient'),{code:'EPERM'});}
    });
    assert.equal(transientAttempts,3);
    assert.deepEqual(transientDelays,[10,20]);

    let terminalAttempts=0;
    const terminal=Object.assign(new Error('terminal'),{code:'EINVAL'});
    assert.throws(()=>removeTemp('ignored-terminal',{
      maxOuterRetries:4,
      sleep:()=>assert.fail('non-transient cleanup must not sleep or retry'),
      remove:()=>{terminalAttempts+=1;throw terminal;}
    }),(error)=>error===terminal);
    assert.equal(terminalAttempts,1);

    const exhaustedDelays=[];
    let exhaustedAttempts=0;
    const exhausted=Object.assign(new Error('exhausted'),{code:'EBUSY'});
    assert.throws(()=>removeTemp('ignored-exhausted',{
      maxOuterRetries:2,
      retryBaseDelayMs:7,
      sleep:(ms)=>exhaustedDelays.push(ms),
      remove:()=>{exhaustedAttempts+=1;throw exhausted;}
    }),(error)=>error===exhausted);
    assert.equal(exhaustedAttempts,3);
    assert.deepEqual(exhaustedDelays,[7,14]);
  });
  test('Recovery Supervisor source has a fixed fail-closed boundary', () => { const s=fs.readFileSync(script,'utf8'); const vbs=fs.readFileSync(launcher,'utf8'); const body=s.split(/\r?\n/).filter((line)=>!line.trimStart().startsWith('function ')).join('\n'); const install=s.match(/function Install-Supervisor\{([^\n]+)\}/)?.[1]||''; assert.match(s,/\$FailureThreshold = 4/);assert.match(s,/\$RestartLimit = 4/);assert.match(s,/\$ReplacementStopTimeoutSeconds = 15/);assert.match(s,/recovery\.ping/);assert.match(s,/LIVE_OWNER_UNRESPONSIVE/);assert.match(s,/executable identity changed; reinstall is required/);assert.match(s,/SUPERVISOR_CYCLE_FAILED/);assert.match(s,/deferred_activation_worker_v1=\$true/);assert.match(s,/full_clean_activation_deferred/);assert.match(s,/trusted_recovery_bootstrap/);assert.match(s,/ELECTRON_RUN_AS_NODE'\]='1'/);assert.match(s,/\[IO\.FileMode\]::CreateNew/);assert.match(s,/Set-Content -LiteralPath \$stop/);assert.match(s,/Existing Recovery Supervisor process \$oldPid did not stop/);assert.match(s,/Replacement Recovery Supervisor did not publish a fresh capability-bearing heartbeat/);assert.doesNotMatch(s,/\$pid\s*=/i);assert.ok(install.indexOf('Stop-InstalledSupervisorForReplacement')<install.indexOf('Copy-Item -LiteralPath $src'));assert.match(s,/RepetitionInterval \(New-TimeSpan -Minutes 1\)/);assert.match(s,/MultipleInstances IgnoreNew/);assert.match(s,/New-ScheduledTaskAction -Execute \$wscript -Argument \$taskArgs/);assert.match(s,/\$taskArgs="\/\/B \/\/NoLogo /);assert.match(vbs,/shell\.Run\(command, 0, True\)/i);assert.match(vbs,/-NonInteractive -WindowStyle Hidden /i);assert.doesNotMatch(vbs,/WScript\.Arguments|ShellExecute/i);assert.doesNotMatch(s,/Invoke-Expression|\biex\b|taskkill\.exe|Stop-Process\s+-Name/i);assert.doesNotMatch(body,/\b(?:Assert-Manifest|Test-AbsoluteSafePath|Test-PathEqual|Get-Sha256File|Get-Sha256Text)\(/); });
  test('Recovery Supervisor GUI launcher runs its fixed sibling script without a console entrypoint', (t) => {
    const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'webmcp-rs-launcher-'));
    t.after(() => removeTemp(temp));
    const installedLauncher = path.join(temp, 'recovery-supervisor-launcher.vbs');
    const marker = path.join(temp, 'launcher-result.txt');
    fs.copyFileSync(launcher, installedLauncher);
    fs.writeFileSync(path.join(temp, 'recovery-supervisor.ps1'), `Set-Content -LiteralPath '${marker.replace(/'/g, "''")}' -Value 'ok' -NoNewline; exit 0`, 'utf8');
    const result = spawnSync(path.join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'wscript.exe'), ['//B', '//NoLogo', installedLauncher], {
      cwd: temp,
      windowsHide: true,
      stdio: 'ignore',
      timeout: 5000
    });
    assert.equal(result.status, 0, result.error?.message || 'wscript launcher failed');
    assert.equal(fs.readFileSync(marker, 'utf8'), 'ok');
  });
  test('Recovery Supervisor explicit harness paths isolate the installed stop sentinel', async (t) => { const temp=fs.mkdtempSync(path.join(os.tmpdir(),'webmcp-rs-stop-isolation-'));t.after(()=>removeTemp(temp));const mf=path.join(temp,'manifest.json');const st=path.join(temp,'status.json');writeJson(mf,manifest(temp));const result=await run(['-Action','Once','-ManifestPath',mf,'-StatusPath',st]);assert.equal(result.code,0,result.stderr||result.stdout);const value=JSON.parse(result.stdout);assert.notEqual(value.state,'stopping');assert.equal(value.state,'degraded'); });
  test('Recovery Supervisor reads UTF-8 packaged manifests with Unicode product paths', async (t) => { const temp=fs.mkdtempSync(path.join(os.tmpdir(),'webmcp-rs-unicode-'));t.after(()=>removeTemp(temp));const appRoot=path.join(temp,'Trợ lý Web MCP');fs.mkdirSync(appRoot,{recursive:true});const executable=path.join(appRoot,'Trợ lý Web MCP.exe');fs.copyFileSync(path.join(process.env.SystemRoot||'C:\\Windows','System32','where.exe'),executable);const mf=path.join(temp,'manifest.json');const st=path.join(temp,'status.json');writeJson(mf,{...manifest(temp),mode:'packaged',executable,executable_sha256:hash(executable),app_root:appRoot,arguments:['--recovery-host'],data_root:temp});const result=await run(['-Action','Once','-ManifestPath',mf,'-StatusPath',st]);assert.equal(result.code,0,result.stderr||result.stdout);const value=JSON.parse(result.stdout);assert.equal(value.state,'degraded');assert.equal(value.last_error_code,'DESCRIPTOR_MISSING');assert.equal(value.last_spawned_pid,null); });
  test('Recovery Supervisor accepts authenticated healthy Recovery Host identity', async (t) => { const temp=fs.mkdtempSync(path.join(os.tmpdir(),'webmcp-rs-healthy-'));t.after(()=>removeTemp(temp));const token=crypto.randomBytes(32).toString('base64url');const instance=crypto.randomBytes(16).toString('hex');const server=http.createServer((req,res)=>{assert.equal(req.url,'/v1/call');assert.equal(req.headers.authorization,`Bearer ${token}`);const chunks=[];req.on('data',(c)=>chunks.push(c));req.on('end',()=>{assert.deepEqual(JSON.parse(Buffer.concat(chunks)),{action:'recovery.ping',args:[]});const body=JSON.stringify({ok:true,data:{ready:true,pid:process.pid,instance_id:instance}});res.writeHead(200,{'Content-Type':'application/json','Content-Length':Buffer.byteLength(body)});res.end(body);});});await new Promise((r)=>server.listen(0,'127.0.0.1',r));t.after(()=>server.close());const mf=path.join(temp,'manifest.json');const st=path.join(temp,'status.json');writeJson(mf,manifest(temp));writeJson(path.join(temp,'recovery-host.json'),{version:1,host:'127.0.0.1',port:server.address().port,token,owner:'recovery-host',owner_pid:process.pid,instance_id:instance});const result=await run(['-Action','Once','-ManifestPath',mf,'-StatusPath',st]);assert.equal(result.code,0,result.stderr||result.stdout);const value=JSON.parse(result.stdout);assert.equal(value.state,'healthy');assert.equal(value.last_host_pid,process.pid);assert.equal(value.last_host_instance_id,instance); });
  test('Recovery Supervisor normalizes sparse persisted uninstalled status before a healthy cycle', async (t) => { const temp=fs.mkdtempSync(path.join(os.tmpdir(),'webmcp-rs-sparse-'));t.after(()=>removeTemp(temp));const token=crypto.randomBytes(32).toString('base64url');const instance=crypto.randomBytes(16).toString('hex');const server=http.createServer((req,res)=>{const chunks=[];req.on('data',(c)=>chunks.push(c));req.on('end',()=>{const body=JSON.stringify({ok:true,data:{ready:true,pid:process.pid,instance_id:instance}});res.writeHead(200,{'Content-Type':'application/json','Content-Length':Buffer.byteLength(body)});res.end(body);});});await new Promise((r)=>server.listen(0,'127.0.0.1',r));t.after(()=>server.close());const mf=path.join(temp,'manifest.json');const st=path.join(temp,'status.json');writeJson(mf,manifest(temp));writeJson(st,{version:1,supervisor_pid:null,state:'uninstalled',last_check_at:new Date().toISOString(),task_name:'WebMCP Recovery Supervisor'});writeJson(path.join(temp,'recovery-host.json'),{version:1,host:'127.0.0.1',port:server.address().port,token,owner:'recovery-host',owner_pid:process.pid,instance_id:instance});const result=await run(['-Action','Once','-ManifestPath',mf,'-StatusPath',st]);assert.equal(result.code,0,result.stderr||result.stdout);const value=JSON.parse(result.stdout);assert.equal(value.state,'healthy');assert.equal(value.last_host_pid,process.pid);assert.equal(value.last_host_instance_id,instance);assert.equal(value.consecutive_failures,0);assert.deepEqual(value.restart_attempts,[]);assert.ok(value.last_healthy_at);assert.equal(value.last_spawned_pid,null); });
  test('Recovery Supervisor fails closed while lock owner is alive', async (t) => { const temp=fs.mkdtempSync(path.join(os.tmpdir(),'webmcp-rs-lock-'));t.after(()=>removeTemp(temp));const mf=path.join(temp,'manifest.json');const st=path.join(temp,'status.json');writeJson(mf,manifest(temp));writeJson(st,prior({consecutive_failures:3}));writeJson(path.join(temp,'recovery-host.lock'),{version:1,pid:process.pid,instance_id:'live-owner-00000001'});const result=await run(['-Action','Once','-ManifestPath',mf,'-StatusPath',st]);assert.equal(result.code,0,result.stderr||result.stdout);const value=JSON.parse(result.stdout);assert.equal(value.state,'blocked_live_owner');assert.equal(value.last_error_code,'LIVE_OWNER_UNRESPONSIVE');assert.equal(value.restart_attempts.length,0);assert.equal(value.last_spawned_pid,null); });
  test('Recovery Supervisor starts only fixed recovery argv after bounded dead-host failures', async (t) => { const temp=fs.mkdtempSync(path.join(os.tmpdir(),'webmcp-rs-dead-'));t.after(()=>removeTemp(temp));const mf=path.join(temp,'manifest.json');const st=path.join(temp,'status.json');writeJson(mf,manifest(temp));writeJson(st,prior({consecutive_failures:3}));const result=await run(['-Action','Once','-ManifestPath',mf,'-StatusPath',st]);assert.equal(result.code,0,result.stderr||result.stdout);const value=JSON.parse(result.stdout);assert.equal(value.state,'restart_started');assert.equal(value.restart_attempts.length,1);assert.ok(Number.isInteger(value.last_spawned_pid)&&value.last_spawned_pid>0);assert.ok(value.next_attempt_after);await waitForExit(value.last_spawned_pid); });
  test('Recovery Supervisor launches one deferred worker when optional trusted bootstrap is omitted', async (t) => {
    const temp=fs.mkdtempSync(path.join(os.tmpdir(),'webmcp-rs-deferred-'));
    const marker=path.join(temp,'deferred-worker-observed.json');
    const worker=path.join(temp,'scripts','full-clean-activation.js');
    const queue=path.join(temp,'full-clean-activation');
    const operation='full-clean-cli-supervisor-test-0001';
    const requestPath=path.join(queue,`${operation}.json`);
    const mf=path.join(temp,'manifest.json');
    const st=path.join(temp,'status.json');
    let workerPid=0;
    t.after(async()=>{if(workerPid)killFixtureTree(workerPid);if(workerPid)await waitForExit(workerPid).catch(()=>{});removeTemp(temp);});
    fs.mkdirSync(path.dirname(worker),{recursive:true});
    fs.mkdirSync(queue,{recursive:true});
    fs.writeFileSync(worker,`const fs=require('node:fs');const p=process.env.WEBCODEX_TEST_DEFERRED_MARKER;let a=[];try{a=JSON.parse(fs.readFileSync(p,'utf8'));}catch{};a.push({pid:process.pid,argv:process.argv.slice(2),run_as_node:process.env.ELECTRON_RUN_AS_NODE||null,deferred_worker:process.env.FULL_CLEAN_DEFERRED_WORKER||null,openai_key_present:Object.hasOwn(process.env,'OPENAI_API_KEY')});fs.writeFileSync(p,JSON.stringify(a));`,'utf8');
    writeJson(mf,{schema_version:1,mode:'development',executable:process.execPath,executable_sha256:hash(process.execPath),app_root:temp,arguments:[temp,'--recovery-host'],data_root:temp,installed_script_sha256:hash(script),installed_at:new Date().toISOString()});
    writeJson(path.join(temp,'recovery-host.lock'),{version:1,pid:process.pid,instance_id:'live-owner-deferred-test'});
    const now=Date.now();
    const expiredOperation='full-clean-cli-expired-supervisor-0000';
    writeJson(path.join(queue,`${expiredOperation}.json`),{schema_version:1,kind:'full_clean_activation_deferred',operation_id:expiredOperation,requested_at_unix_ms:now-240000,expires_at_unix_ms:now-120000,parent_pid:process.pid,parent_marker:path.join(queue,`${expiredOperation}.parent.json`),source_checkpoint:{checkpoint_id:'checkpoint-expired-test',run_id:'run-expired-test',wave_id:'wave-expired-test',proof_fingerprint:'a'.repeat(64),git_head:'b'.repeat(40)},installation_id:'c'.repeat(64),runtime_mode:'development',app_root:temp,parent_marker_nonce:'d'.repeat(36),trusted_recovery_bootstrap:{component:'recovery_host'},integrity_sha256:'e'.repeat(64)});
    writeJson(requestPath,{schema_version:1,kind:'full_clean_activation_deferred',operation_id:operation,requested_at_unix_ms:now,expires_at_unix_ms:now+120000,parent_pid:process.pid,parent_marker:path.join(queue,`${operation}.parent.json`),source_checkpoint:{checkpoint_id:'checkpoint-supervisor-test',run_id:'run-supervisor-test',wave_id:'wave-supervisor-test',proof_fingerprint:'a'.repeat(64),git_head:'b'.repeat(40)},installation_id:'c'.repeat(64),runtime_mode:'development',app_root:temp,parent_marker_nonce:'d'.repeat(36),integrity_sha256:'e'.repeat(64)});
    const env={...process.env,WEBCODEX_TEST_DEFERRED_MARKER:marker,OPENAI_API_KEY:'must-not-cross-supervisor-boundary'};
    const first=await run(['-Action','Once','-ManifestPath',mf,'-StatusPath',st],env);
    assert.equal(first.code,0,first.stderr||first.stdout);
    const firstState=JSON.parse(first.stdout);
    assert.equal(firstState.deferred_activation_worker_v1,true);
    assert.equal(firstState.last_deferred_operation_id,operation);
    workerPid=Number(firstState.last_deferred_worker_pid);
    assert.ok(workerPid>0,JSON.stringify(firstState));
    const observed=await waitForStatus(marker,(value)=>Array.isArray(value)&&value.length===1);
    assert.deepEqual(observed[0].argv,['--deferred-worker',requestPath]);
    assert.equal(observed[0].run_as_node,'1');
    assert.equal(observed[0].deferred_worker,'1');
    assert.equal(observed[0].openai_key_present,false);
    assert.equal(fs.existsSync(path.join(queue,`${operation}.supervisor.launch.json`)),true);
    await waitForExit(workerPid);
    const second=await run(['-Action','Once','-ManifestPath',mf,'-StatusPath',st],env);
    assert.equal(second.code,0,second.stderr||second.stdout);
    await new Promise((resolve)=>setTimeout(resolve,250));
    assert.equal(JSON.parse(fs.readFileSync(marker,'utf8')).length,1);
  });
  test('Recovery Supervisor recreates a killed Recovery Host process with a new authenticated identity', async (t) => { const temp=fs.mkdtempSync(path.join(os.tmpdir(),'webmcp-rs-resurrection-'));const token=crypto.randomBytes(32).toString('base64url');const port=await freePort();const hostSource=`const fs=require('node:fs');const http=require('node:http');const path=require('node:path');const crypto=require('node:crypto');if(!process.argv.includes('--recovery-host'))process.exit(2);const root=process.env.WEBCODEX_TEST_DATA_ROOT;const token=process.env.WEBCODEX_TEST_TOKEN;const port=Number(process.env.WEBCODEX_TEST_PORT);const instance=crypto.randomBytes(16).toString('hex');fs.mkdirSync(root,{recursive:true});fs.writeFileSync(path.join(root,'recovery-host.lock'),JSON.stringify({version:1,pid:process.pid,instance_id:instance}));const server=http.createServer((req,res)=>{const chunks=[];req.on('data',(c)=>chunks.push(c));req.on('end',()=>{if(req.url!=='/v1/call'||req.headers.authorization!=='Bearer '+token){res.writeHead(401);res.end();return;}let payload={};try{payload=JSON.parse(Buffer.concat(chunks));}catch{}const body=JSON.stringify({ok:payload.action==='recovery.ping',data:{ready:true,pid:process.pid,instance_id:instance}});res.writeHead(200,{'Content-Type':'application/json','Content-Length':Buffer.byteLength(body)});res.end(body);});});server.listen(port,'127.0.0.1',()=>fs.writeFileSync(path.join(root,'recovery-host.json'),JSON.stringify({version:1,host:'127.0.0.1',port,token,owner:'recovery-host',owner_pid:process.pid,instance_id:instance})));setInterval(()=>{},1000);`;writeJson(path.join(temp,'package.json'),{main:'host.js'});fs.writeFileSync(path.join(temp,'host.js'),hostSource,'utf8');const mf=path.join(temp,'manifest.json');const st=path.join(temp,'status.json');const env={...process.env,WEBCODEX_TEST_DATA_ROOT:temp,WEBCODEX_TEST_TOKEN:token,WEBCODEX_TEST_PORT:String(port)};writeJson(mf,{schema_version:1,mode:'development',executable:process.execPath,executable_sha256:hash(process.execPath),app_root:temp,arguments:[temp,'--recovery-host'],data_root:temp,installed_script_sha256:hash(script),installed_at:new Date().toISOString()});let oldPid=0;let newPid=0;t.after(async()=>{for(const pid of [oldPid,newPid])killFixtureTree(pid);for(const pid of [oldPid,newPid])if(pid>0)await waitForExit(pid).catch(()=>{});await new Promise((resolve)=>setTimeout(resolve,100));removeTemp(temp);});const oldHost=spawn(process.execPath,[temp,'--recovery-host'],{cwd:temp,windowsHide:true,stdio:'ignore',env});oldPid=oldHost.pid;const first=await waitForStatus(path.join(temp,'recovery-host.json'),(value)=>Number(value.owner_pid)===oldPid&&String(value.instance_id||'').length>=16);const firstPing=await recoveryPing(port,token);assert.equal(firstPing.ok,true);assert.equal(firstPing.data.pid,oldPid);const firstInstance=first.instance_id;oldHost.kill();await waitForExit(oldPid);writeJson(st,prior({consecutive_failures:3}));const result=await run(['-Action','Once','-ManifestPath',mf,'-StatusPath',st],env);assert.equal(result.code,0,result.stderr||result.stdout);const value=JSON.parse(result.stdout);assert.equal(value.state,'restart_started');newPid=Number(value.last_spawned_pid);assert.ok(Number.isInteger(newPid)&&newPid>0);assert.notEqual(newPid,oldPid);const replacement=await waitForStatus(path.join(temp,'recovery-host.json'),(entry)=>Number(entry.owner_pid)===newPid&&entry.instance_id!==firstInstance);assert.equal(Number(replacement.owner_pid),newPid);const replacementPing=await recoveryPing(port,token);assert.equal(replacementPing.ok,true);assert.equal(replacementPing.data.ready,true);assert.equal(replacementPing.data.pid,newPid);assert.equal(replacementPing.data.instance_id,replacement.instance_id);assert.notEqual(replacementPing.data.instance_id,firstInstance); });
  test('Recovery Supervisor suppresses restart after the bounded crash-loop limit', async (t) => { const temp=fs.mkdtempSync(path.join(os.tmpdir(),'webmcp-rs-suppressed-'));t.after(()=>removeTemp(temp));const mf=path.join(temp,'manifest.json');const st=path.join(temp,'status.json');const now=Date.now();const attempts=[4,3,2,1].map((seconds)=>new Date(now-seconds*1000).toISOString());writeJson(mf,manifest(temp));writeJson(st,prior({consecutive_failures:3,restart_attempts:attempts,next_attempt_after:null,suppressed_until:null}));const result=await run(['-Action','Once','-ManifestPath',mf,'-StatusPath',st]);assert.equal(result.code,0,result.stderr||result.stdout);const value=JSON.parse(result.stdout);assert.equal(value.state,'suppressed');assert.equal(value.last_error_code,'CRASH_LOOP_SUPPRESSED');assert.deepEqual(value.restart_attempts,attempts);assert.equal(value.last_spawned_pid,null);assert.ok(Date.parse(value.suppressed_until)>now); });
  test('Recovery Supervisor Run mode stays alive across repeated healthy cycles', async (t) => { const temp=fs.mkdtempSync(path.join(os.tmpdir(),'webmcp-rs-loop-'));const token=crypto.randomBytes(32).toString('base64url');const instance=crypto.randomBytes(16).toString('hex');const server=http.createServer((req,res)=>{const chunks=[];req.on('data',(c)=>chunks.push(c));req.on('end',()=>{const body=JSON.stringify({ok:true,data:{ready:true,pid:process.pid,instance_id:instance}});res.writeHead(200,{'Content-Type':'application/json','Content-Length':Buffer.byteLength(body)});res.end(body);});});await new Promise((resolve)=>server.listen(0,'127.0.0.1',resolve));const mf=path.join(temp,'manifest.json');const st=path.join(temp,'status.json');writeJson(mf,manifest(temp));writeJson(path.join(temp,'recovery-host.json'),{version:1,host:'127.0.0.1',port:server.address().port,token,owner:'recovery-host',owner_pid:process.pid,instance_id:instance});const child=spawn('powershell.exe',['-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',script,'-Action','Run','-ManifestPath',mf,'-StatusPath',st],{cwd:root,windowsHide:true,stdio:'ignore'});try{const first=await waitForStatus(st,(value)=>value.state==='healthy'&&value.last_check_at);const firstCheck=first.last_check_at;const second=await waitForStatus(st,(value)=>value.state==='healthy'&&value.last_check_at&&value.last_check_at!==firstCheck,12000);assert.notEqual(second.last_check_at,firstCheck);assert.equal(processAlive(child.pid),true);}finally{if(processAlive(child.pid))child.kill();await waitForExit(child.pid).catch(()=>{});await new Promise((resolve)=>server.close(resolve));removeTemp(temp);} });
  test('Recovery Supervisor Run mode exits through the cooperative stop sentinel', async (t) => { const temp=fs.mkdtempSync(path.join(os.tmpdir(),'webmcp-rs-stop-'));const token=crypto.randomBytes(32).toString('base64url');const instance=crypto.randomBytes(16).toString('hex');const server=http.createServer((req,res)=>{req.resume();req.on('end',()=>{const body=JSON.stringify({ok:true,data:{ready:true,pid:process.pid,instance_id:instance}});res.writeHead(200,{'Content-Type':'application/json','Content-Length':Buffer.byteLength(body)});res.end(body);});});await new Promise((resolve)=>server.listen(0,'127.0.0.1',resolve));const mf=path.join(temp,'manifest.json');const st=path.join(temp,'status.json');writeJson(mf,manifest(temp));writeJson(path.join(temp,'recovery-host.json'),{version:1,host:'127.0.0.1',port:server.address().port,token,owner:'recovery-host',owner_pid:process.pid,instance_id:instance});const child=spawn('powershell.exe',['-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',script,'-Action','Run','-ManifestPath',mf,'-StatusPath',st],{cwd:root,windowsHide:true,stdio:'ignore'});try{await waitForStatus(st,(value)=>value.state==='healthy'&&value.last_check_at);fs.writeFileSync(path.join(temp,'stop.request'),new Date().toISOString(),'ascii');await waitForExit(child.pid,12000);const final=JSON.parse(fs.readFileSync(st,'utf8'));assert.equal(final.state,'stopping');assert.equal(processAlive(child.pid),false);}finally{if(processAlive(child.pid))child.kill();await waitForExit(child.pid).catch(()=>{});await new Promise((resolve)=>server.close(resolve));removeTemp(temp);} });
}
