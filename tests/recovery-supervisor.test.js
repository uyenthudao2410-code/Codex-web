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

test('Recovery Supervisor central eligibility helpers evaluate real PowerShell without installed tasks or process launch', (t) => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'webmcp-rs-agent-spec-'));
  t.after(() => removeTemp(temp));
  const appRoot = path.join(temp, 'app');
  const python = path.join(appRoot, 'resources', 'resources', 'native-python', 'python.exe');
  const agent = path.join(appRoot, 'resources', 'resources', 'control-plane', 'node_agent.py');
  const developmentRoot = path.join(temp, 'development');
  const developmentPython = path.join(developmentRoot, 'resources', 'native-python', 'python.exe');
  const developmentAgent = path.join(developmentRoot, 'control-plane', 'control_plane', 'node_agent.py');
  const developmentExecutable = path.join(developmentRoot, 'electron.exe');
  const nodeRuntime = process.execPath;
  fs.mkdirSync(path.dirname(python), { recursive: true });
  fs.mkdirSync(path.dirname(agent), { recursive: true });
  fs.mkdirSync(path.dirname(developmentPython), { recursive: true });
  fs.mkdirSync(path.dirname(developmentAgent), { recursive: true });
  fs.mkdirSync(path.dirname(developmentExecutable), { recursive: true });
  // These fixture files are hashed only. No test branch executes an agent,
  // installs a Scheduled Task, or loads the supervisor's top-level switch.
  fs.writeFileSync(python, 'inert-python-fixture');
  fs.writeFileSync(agent, '# inert-agent-fixture');
  fs.writeFileSync(developmentPython, 'inert-development-python-fixture');
  fs.writeFileSync(developmentAgent, '# inert-development-agent-fixture');
  fs.copyFileSync(path.join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'where.exe'), developmentExecutable);
  const cases = [
    ['valid', {}, {}, {}, 'file_read', 'eligible', 'current'],
    ['minimum-secret', { node_secret: 'x'.repeat(16) }, {}, {}, 'file_read', 'eligible', 'current'],
    ['long-secret', { node_secret: 'x'.repeat(100) }, {}, {}, 'file_read', 'eligible', 'current'],
    ['protected-secret', { node_secret: null, node_secret_dpapi: 'dpapi-v1:' + 'x'.repeat(32) }, {}, {}, 'file_read', 'eligible', 'current'],
    ['short-secret', { node_secret: 'x'.repeat(15) }, {}, {}, 'file_read', 'policy_config_mismatch', 'current'],
    ['two-character-secret', { node_secret: 'xx' }, {}, {}, 'file_read', 'policy_config_mismatch', 'current'],
    ['null-secret', { node_secret: null }, {}, {}, 'file_read', 'policy_config_mismatch', 'current'],
    ['device-mismatch', {}, {}, { device_id: 'other-device' }, 'file_read', 'heartbeat_only', 'current', true],
    ['endpoint-mismatch', {}, {}, { endpoint_id: 'other-endpoint' }, 'file_read', 'heartbeat_only', 'current', true],
    ['origin-mismatch', {}, {}, { server_origin: 'https://other.example.test' }, 'file_read', 'heartbeat_only', 'current', true],
    ['expired-read-only-policy', {}, { expires_at_ms: Date.now() - 1000 }, {}, 'file_read', 'eligible', 'current'],
    ['disabled-read-only-policy', {}, { enabled: false }, {}, 'file_read', 'eligible', 'current'],
    ['standing-policy-missing', {}, {}, null, 'file_read', 'heartbeat_only', 'current', true],
    ['standing-policy-expired', {}, {}, { expires_at_ms: Date.now() - 1000 }, 'file_read', 'heartbeat_only', 'current', true],
    ['standing-approved-patch-only', {}, {}, {}, 'approved_patch', 'eligible', 'current'],
    ['standing-exec-only', {}, {}, {}, 'exec', 'eligible', 'current'],
    ['standing-file-read-schema-mismatch', {}, {}, { schema_version: 2 }, 'file_read', 'heartbeat_only', 'current', true],
    ['standing-approved-patch-schema-mismatch', {}, {}, { schema_version: 2 }, 'approved_patch', 'heartbeat_only', 'current', true],
    ['workspace-registry-missing', {}, {}, {}, 'file_read', 'heartbeat_only', 'missing', true],
    ['workspace-registration-stale', {}, {}, {}, 'file_read', 'heartbeat_only', 'empty', true],
    ['development-mode', {}, {}, {}, 'file_read', 'eligible', 'current', false, 'development']
  ];
  const fixtures = cases.map(([name, configPatch, readOnlyPatch, standingPatch, standingLane, , registryState, , mode = 'packaged']) => {
    const dataRoot = path.join(temp, name);
    const manifestRoot = mode === 'development' ? developmentRoot : appRoot;
    const manifestPython = mode === 'development' ? developmentPython : python;
    const manifestAgent = mode === 'development' ? developmentAgent : agent;
    writeJson(path.join(dataRoot, 'control-plane-node.json'), {
      server_url: 'http://100.116.112.22:8765', device_id: 'fixture-device',
      endpoint_id: 'fixture-endpoint', node_secret: 'x'.repeat(64), ...configPatch
    });
    writeJson(path.join(dataRoot, 'control-plane-read-only-policy.json'), {
      schema_version: 2, enabled: true, server_origin: 'http://100.116.112.22:8765',
      owner_id: 'fixture-owner', device_id: 'fixture-device', endpoint_id: 'fixture-endpoint',
      workspace_id: 'workspace-fixture-0001', workspace_generation: 'generation-fixture-0001',
      expires_at_ms: Date.now() + 600_000, facade_contract: 'fixture-contract', ...readOnlyPatch
    });
    if (standingPatch !== null) {
      const common = {
        schema_version: standingLane === 'exec' ? 2 : 3, enabled: true, authority_mode: 'standing',
        server_origin: 'http://100.116.112.22:8765', owner_id: 'fixture-owner',
        device_id: 'fixture-device', endpoint_id: 'fixture-endpoint',
        workspace_id: 'workspace-fixture-0001', workspace_generation: 'generation-fixture-0001',
        expires_at_ms: null, facade_contract: { schema_version: 1, profile: 'fixture', sha256: 'a'.repeat(64) }
      };
      const policy = standingLane === 'approved_patch'
        ? { ...common, allowed_relative_prefixes: ['fixture.txt'], max_patch_bytes: 1024, max_file_bytes: 4096, validation_profile: 'targeted' }
        : standingLane === 'exec'
          ? { ...common, allowed_argv_prefixes: [['git']], max_timeout_ms: 5000, max_output_bytes: 1024, max_concurrent: 1 }
          : { ...common, allowed_relative_prefixes: ['fixture.txt'], max_bytes: 1024, max_lines: 10 };
      writeJson(path.join(dataRoot, `control-plane-${standingLane === 'approved_patch' ? 'approved-patch' : standingLane === 'exec' ? 'exec' : 'file-read'}-policy.json`), {
        ...policy, ...standingPatch
      });
    }
    if (registryState !== 'missing') {
      // The Supervisor checks that this exact policy generation remains
      // registered and rooted locally. The node agent independently performs
      // the stricter resolve/canonicalization check before an effect.
      writeJson(path.join(dataRoot, 'control-plane-workspaces.json'), {
        schema_version: 1,
        entries: registryState === 'current' ? [{
          workspace_id: 'workspace-fixture-0001',
          workspace_generation: 'generation-fixture-0001',
          canonical_path: dataRoot,
          display_name: 'fixture-root',
          capabilities: { read: true, write: false, exec: false },
          created_at_ms: 1
        }] : []
      });
    }
    return {
      name,
      manifest: {
        mode, app_root: manifestRoot, data_root: dataRoot,
        executable: mode === 'development' ? developmentExecutable : process.execPath,
        executable_sha256: hash(mode === 'development' ? developmentExecutable : process.execPath),
        control_plane_python_path: manifestPython, control_plane_python_sha256: hash(manifestPython),
        control_plane_node_agent_path: manifestAgent, control_plane_node_agent_sha256: hash(manifestAgent),
        control_plane_node_path: nodeRuntime, control_plane_node_sha256: hash(nodeRuntime)
      }
    };
  });
  const origins = [
    ['https://EXAMPLE.test:443/', 'https://example.test'],
    ['http://100.116.112.22:8765/', 'http://100.116.112.22:8765'],
    ['http://[fd7a:115c:a1e0::1]:8765/', 'http://[fd7a:115c:a1e0::1]:8765'],
    ['http://[fd7a:115c:a1e0:0000:0000:0000:0000:0001]:8765/', 'http://[fd7a:115c:a1e0::1]:8765'],
    ['https://user:pass@example.test/', null],
    ['https://example.test/path', null],
    ['https://example.test/?query=1', null],
    ['https://example.test/#fragment', null],
    ['not-an-origin', null]
  ];
  const inputFile = path.join(temp, 'fixture-input.json');
  writeJson(inputFile, { fixtures, origins: origins.map(([value]) => value) });
  const command = `
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$MaxJsonBytes=65536
$parseTokens=$null;$parseErrors=$null
$parsed=[Management.Automation.Language.Parser]::ParseFile($env:WEBCODEX_TEST_SUPERVISOR_SCRIPT,[ref]$parseTokens,[ref]$parseErrors)
if($parseErrors.Count-ne0){throw 'Supervisor PowerShell parser rejected the source.'}
foreach($helperName in @('Get-Sha256File','Read-BoundedJson','Test-PathEqual','Test-AbsoluteSafePath','Get-OptionalProperty','Convert-ToUtc','Test-ProcessAlive','Get-ConnectedAgentDiagnostics','Get-ManifestPath','Get-ControlPlaneAgentConfigPath','Get-ControlPlaneAgentPolicyPath','Get-ControlPlaneStandingPolicyCandidates','Get-ControlPlaneStandingPolicySchema','Get-ControlPlaneWorkspaceRegistryPath','Resolve-ControlPlaneNodePath','Get-ControlPlaneAgentPaths','Test-ControlPlanePropertySet','Test-ControlPlaneNodeCredential','Test-ControlPlaneWorkspaceRegistration','Get-ControlPlaneOrigin','Get-ControlPlaneAgentSpec','Get-ControlPlaneAgentArguments','Stop-ControlPlaneAgentForReplacement','New-State','Invoke-ControlPlaneReadOnlyAgent')){
  $definition=$parsed.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name-eq$helperName},$true)
  if($null-eq$definition){throw 'Required pure supervisor helper missing.'}
  . ([scriptblock]::Create($definition.Extent.Text))
}
foreach($helperName in @('Test-ControlPlaneAgentCurrent','Remove-ControlPlaneAgentLockAfterStop')){
  $definition=$parsed.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name-eq$helperName},$true)
  if($null-eq$definition){throw 'Required agent replacement helper missing.'}
  . ([scriptblock]::Create($definition.Extent.Text))
}
$inputFixture=[IO.File]::ReadAllText($env:WEBCODEX_TEST_SUPERVISOR_FIXTURE)|ConvertFrom-Json
$TaskName='WebMCP Recovery Supervisor'
$ConnectedAgentStatusFileName='control-plane-connected-agent-status.json'
$MaxConnectedAgentStatusBytes=16384
$ConnectedAgentStatusFreshnessMs=120000
$ManifestPath=Join-Path (Split-Path -Parent $env:WEBCODEX_TEST_SUPERVISOR_FIXTURE) 'state-manifest.json'
$StatePath=Join-Path (Split-Path -Parent $env:WEBCODEX_TEST_SUPERVISOR_FIXTURE) 'state-status.json'
[IO.File]::WriteAllText($ManifestPath,($inputFixture.fixtures[0].manifest|ConvertTo-Json -Compress),(New-Object Text.UTF8Encoding($false)))
[IO.File]::WriteAllText($StatePath,(@{manifest_sha256=('0'*64);control_plane_agent_pid=123;control_plane_agent_state='running';control_plane_agent_last_started_at='2026-01-01T00:00:00Z'}|ConvertTo-Json -Compress),(New-Object Text.UTF8Encoding($false)))
$resetState=New-State $inputFixture.fixtures[0].manifest $StatePath
$stateIdentityReset=[pscustomobject]@{agent_pid=$resetState.control_plane_agent_pid;agent_state=$resetState.control_plane_agent_state;agent_started_at=$resetState.control_plane_agent_last_started_at}
$results=@(foreach($fixture in $inputFixture.fixtures){$spec=Get-ControlPlaneAgentSpec $fixture.manifest;[pscustomobject]@{name=$fixture.name;eligible=$spec.eligible;state=$spec.state}})
$originResults=@(foreach($value in $inputFixture.origins){[pscustomobject]@{value=$value;origin=(Get-ControlPlaneOrigin $value)}})
$diagManifest=$inputFixture.fixtures[0].manifest
$diagProcess=Get-Process -Id $PID -ErrorAction Stop
$diagStarted=[DateTimeOffset]($diagProcess.StartTime.ToUniversalTime())
$diagStartedMs=$diagStarted.ToUnixTimeMilliseconds()
$diagNowMs=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$diagAgentStatus=[pscustomobject]@{control_plane_agent_pid=[int]$PID;control_plane_agent_last_started_at=$diagStarted.ToString('o')}
$diagReport=[ordered]@{schema_version=1;kind='control_plane_connected_agent_status';agent_pid=[int]$PID;agent_instance_id=([Guid]::NewGuid().ToString('N'));agent_started_at_ms=$diagStartedMs;updated_at_ms=$diagNowMs;last_attempt_at_ms=[Math]::Max($diagStartedMs,$diagNowMs-1000);last_iteration=1;last_iteration_state='completed';last_heartbeat_state='succeeded';last_heartbeat_at_ms=[Math]::Max($diagStartedMs,$diagNowMs-1000);last_error_scope=$null;last_error_code=$null}
$diagPath=Join-Path ([string]$diagManifest.data_root) 'control-plane-connected-agent-status.json'
[IO.File]::WriteAllText($diagPath,($diagReport|ConvertTo-Json -Compress),(New-Object Text.UTF8Encoding($false)))
$diagFresh=Get-ConnectedAgentDiagnostics ([string]$diagManifest.data_root) $diagAgentStatus
$freshAgentDecision=Test-ControlPlaneAgentCurrent ([int]$PID) $diagAgentStatus ([string]$diagManifest.data_root) $true $false
$changedManifestDecision=Test-ControlPlaneAgentCurrent ([int]$PID) $diagAgentStatus ([string]$diagManifest.data_root) $true $true
$unrecordedAgentStatus=[pscustomobject]@{control_plane_agent_pid=[int]$PID+1;control_plane_agent_last_started_at=$diagStarted.ToString('o')}
$unrecordedAgentDecision=Test-ControlPlaneAgentCurrent ([int]$PID) $unrecordedAgentStatus ([string]$diagManifest.data_root) $true $false
$lockInstanceId='a'*32
$lockExactPath=Join-Path (Split-Path -Parent $env:WEBCODEX_TEST_SUPERVISOR_FIXTURE) 'agent-lock-exact.json'
[IO.File]::WriteAllText($lockExactPath,(@{schema_version=1;instance_id=$lockInstanceId;pid=[int]$PID}|ConvertTo-Json -Compress),(New-Object Text.UTF8Encoding($false)))
$lockExactRemoved=Remove-ControlPlaneAgentLockAfterStop $lockExactPath ([int]$PID) $lockInstanceId
$lockChangedInstancePath=Join-Path (Split-Path -Parent $env:WEBCODEX_TEST_SUPERVISOR_FIXTURE) 'agent-lock-changed-instance.json'
[IO.File]::WriteAllText($lockChangedInstancePath,(@{schema_version=1;instance_id=('b'*32);pid=[int]$PID}|ConvertTo-Json -Compress),(New-Object Text.UTF8Encoding($false)))
$lockChangedInstanceRemoved=Remove-ControlPlaneAgentLockAfterStop $lockChangedInstancePath ([int]$PID) $lockInstanceId
$lockChangedPidPath=Join-Path (Split-Path -Parent $env:WEBCODEX_TEST_SUPERVISOR_FIXTURE) 'agent-lock-changed-pid.json'
[IO.File]::WriteAllText($lockChangedPidPath,(@{schema_version=1;instance_id=$lockInstanceId;pid=([int]$PID+1)}|ConvertTo-Json -Compress),(New-Object Text.UTF8Encoding($false)))
$lockChangedPidRemoved=Remove-ControlPlaneAgentLockAfterStop $lockChangedPidPath ([int]$PID) $lockInstanceId
$ConnectedAgentStatusFreshnessMs=1
$diagReport.updated_at_ms=[Math]::Max($diagStartedMs+1,$diagNowMs-180000)
$diagReport.last_attempt_at_ms=[Math]::Max($diagStartedMs,$diagReport.updated_at_ms-1000)
$diagReport.last_iteration_state='degraded';$diagReport.last_heartbeat_state='failed';$diagReport.last_heartbeat_at_ms=[Math]::Max($diagStartedMs,$diagReport.updated_at_ms-1000);$diagReport.last_error_scope='heartbeat';$diagReport.last_error_code='CONTROL_PLANE_TRANSPORT_UNAVAILABLE'
[IO.File]::WriteAllText($diagPath,($diagReport|ConvertTo-Json -Compress),(New-Object Text.UTF8Encoding($false)))
$diagStale=Get-ConnectedAgentDiagnostics ([string]$diagManifest.data_root) $diagAgentStatus
$diagReport.schema_version='1'
[IO.File]::WriteAllText($diagPath,($diagReport|ConvertTo-Json -Compress),(New-Object Text.UTF8Encoding($false)))
$diagMalformed=Get-ConnectedAgentDiagnostics ([string]$diagManifest.data_root) $diagAgentStatus
$diagReport.schema_version=1
$diagReport.agent_pid=[int]$PID+1
[IO.File]::WriteAllText($diagPath,($diagReport|ConvertTo-Json -Compress),(New-Object Text.UTF8Encoding($false)))
$diagMismatch=Get-ConnectedAgentDiagnostics ([string]$diagManifest.data_root) $diagAgentStatus
$diagnosticResults=[pscustomobject]@{fresh=$diagFresh;stale=$diagStale;malformed=$diagMalformed;mismatch=$diagMismatch}
 $argumentResults=@(foreach($fixture in @($inputFixture.fixtures[0],$inputFixture.fixtures[-1])){$arguments=Get-ControlPlaneAgentArguments $fixture.manifest ([pscustomobject]@{agent_path='agent.py';config_path='config.json';workspace_registry_path='workspaces.json';node_path=[string]$fixture.manifest.control_plane_node_path});[pscustomobject]@{mode=[string]$fixture.manifest.mode;runtime_mode=[string]$arguments[12];node=[string]$arguments[10];executable=[string]$fixture.manifest.executable;data_root_flag=($arguments -contains '--data-root')}})
# New-State uses an OrderedDictionary, not a JSON PSCustomObject. Retain the
# first child PID across polls instead of launching an agent on every cycle.
# Both process boundaries are inert mocks; no process is probed or spawned.
$script:fixtureStartCount=0
function Test-ProcessAlive([int]$ProcessId){$ProcessId-eq123}
function Start-ControlPlaneReadOnlyAgent($M,$Spec){$script:fixtureStartCount+=1;123}
$fixtureState=[ordered]@{control_plane_agent_pid=$null;control_plane_agent_state='not_checked';control_plane_agent_last_error_code=$null;control_plane_agent_last_started_at=$null}
$fixtureState=Invoke-ControlPlaneReadOnlyAgent $inputFixture.fixtures[0].manifest $fixtureState
$firstAgentState=$fixtureState.control_plane_agent_state
$fixtureState=Invoke-ControlPlaneReadOnlyAgent $inputFixture.fixtures[0].manifest $fixtureState
$agentCycle=[pscustomobject]@{first_state=$firstAgentState;second_state=$fixtureState.control_plane_agent_state;starts=$script:fixtureStartCount;pid=$fixtureState.control_plane_agent_pid}
$agentReplacement=[pscustomobject]@{
  fresh_current=$freshAgentDecision
  changed_manifest=$changedManifestDecision
  unrecorded=$unrecordedAgentDecision
  exact_lock_removed=$lockExactRemoved
  exact_lock_absent=(-not(Test-Path -LiteralPath $lockExactPath))
  changed_instance_preserved=((-not$lockChangedInstanceRemoved)-and(Test-Path -LiteralPath $lockChangedInstancePath))
  changed_pid_preserved=((-not$lockChangedPidRemoved)-and(Test-Path -LiteralPath $lockChangedPidPath))
}
[pscustomobject]@{cases=$results;origins=$originResults;agent_arguments=$argumentResults;agent_cycle=$agentCycle;state_identity_reset=$stateIdentityReset;connected_agent_diagnostics=$diagnosticResults;agent_replacement=$agentReplacement}|ConvertTo-Json -Depth 5 -Compress
`;
  const result = spawnSync(process.platform === 'win32' ? 'powershell.exe' : 'pwsh', [
    '-NoProfile', '-NonInteractive', '-EncodedCommand', Buffer.from(command, 'utf16le').toString('base64')
  ], {
    cwd: root, windowsHide: true, encoding: 'utf8', timeout: 30_000,
    env: {
      ...process.env, WEBCODEX_TEST_SUPERVISOR_SCRIPT: script,
      WEBCODEX_TEST_SUPERVISOR_FIXTURE: inputFile
    }
  });
  if (process.platform !== 'win32' && result.error?.code === 'ENOENT') {
    t.skip('PowerShell is unavailable; this helper test is mandatory on Windows');
    return;
  }
  assert.equal(result.status, 0, result.error?.message || result.stderr || result.stdout);
  const observed = JSON.parse(result.stdout.trim());
  assert.deepEqual(observed.cases, cases.map(([name, , , , , state]) => ({ name, eligible: ['eligible', 'heartbeat_only'].includes(state), state })));
  assert.deepEqual(observed.origins, origins.map(([value, origin]) => ({ value, origin })));
  assert.deepEqual(observed.agent_arguments, [
    { mode: 'packaged', runtime_mode: 'packaged', node: process.execPath, executable: process.execPath, data_root_flag: false },
    { mode: 'development', runtime_mode: 'development', node: process.execPath, executable: path.join(temp, 'development', 'electron.exe'), data_root_flag: true }
  ]);
  assert.notEqual(observed.agent_arguments[1].node, observed.agent_arguments[1].executable);
  assert.deepEqual(observed.agent_cycle, { first_state: 'started', second_state: 'running', starts: 1, pid: 123 });
  assert.deepEqual(observed.state_identity_reset, { agent_pid: null, agent_state: 'not_checked', agent_started_at: null });
  assert.equal(observed.connected_agent_diagnostics.fresh.available, true);
  assert.equal(observed.connected_agent_diagnostics.fresh.report_freshness, 'fresh');
  assert.equal(observed.connected_agent_diagnostics.fresh.last_heartbeat_state, 'succeeded');
  assert.equal(observed.connected_agent_diagnostics.stale.available, true);
  assert.equal(observed.connected_agent_diagnostics.stale.report_freshness, 'stale');
  assert.equal(observed.connected_agent_diagnostics.stale.last_error_scope, 'heartbeat');
  assert.equal(observed.connected_agent_diagnostics.stale.last_error_code, 'CONTROL_PLANE_TRANSPORT_UNAVAILABLE');
  assert.equal(observed.connected_agent_diagnostics.malformed.available, false);
  assert.equal(observed.connected_agent_diagnostics.malformed.reason_code, 'AGENT_TELEMETRY_INVALID');
  assert.equal(observed.connected_agent_diagnostics.mismatch.available, false);
  assert.equal(observed.connected_agent_diagnostics.mismatch.reason_code, 'AGENT_TELEMETRY_IDENTITY_MISMATCH');
  assert.deepEqual(observed.agent_replacement, {
    fresh_current: true,
    changed_manifest: false,
    unrecorded: false,
    exact_lock_removed: true,
    exact_lock_absent: true,
    changed_instance_preserved: true,
    changed_pid_preserved: true
  });
});

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
  test('Recovery Supervisor source has a fixed fail-closed boundary', () => { const s=fs.readFileSync(script,'utf8'); const vbs=fs.readFileSync(launcher,'utf8'); const body=s.slice(s.lastIndexOf('\ntry{switch')); const install=s.match(/function Install-Supervisor\{([^\n]+)\}/)?.[1]||''; assert.match(s,/\$FailureThreshold = 4/);assert.match(s,/\$RestartLimit = 4/);assert.match(s,/\$ReplacementStopTimeoutSeconds = 15/);assert.match(s,/recovery\.ping/);assert.match(s,/LIVE_OWNER_UNRESPONSIVE/);assert.match(s,/executable identity changed; reinstall is required/);assert.match(s,/SUPERVISOR_CYCLE_FAILED/);assert.match(s,/deferred_activation_worker_v1=\$true/);assert.match(s,/control_plane_agent_v1=\$true/);assert.match(s,/Get-ControlPlaneAgentSpec/);assert.match(s,/Start-ControlPlaneReadOnlyAgent/);assert.match(s,/Stop-ControlPlaneAgentForReplacement/);assert.match(s,/Get-CimInstance Win32_Process/);assert.match(s,/recognized node-agent process/);assert.match(s,/Test-ControlPlaneWorkspaceRegistration/);assert.match(s,/workspace_registry_unavailable/);assert.match(s,/workspace_registration_not_current/);assert.match(s,/--workspace-registry/);assert.match(s,/policy_config_mismatch/);assert.match(s,/WEBCODEX_PROCESS_ROLE'\]='control-plane-read-only-agent'/);assert.match(s,/full_clean_activation_deferred/);assert.match(s,/trusted_recovery_bootstrap/);assert.match(s,/ELECTRON_RUN_AS_NODE'\]='1'/);assert.match(s,/Resolve-ControlPlaneNodePath/);assert.match(s,/control_plane_node_path/);assert.match(s,/control_plane_node_sha256/);assert.match(s,/Development control-plane node runtime must be node\.exe/);assert.match(s,/Development control-plane data root is unavailable/);assert.match(s,/--data-root/);assert.match(s,/\[IO\.FileMode\]::CreateNew/);assert.match(s,/Set-Content -LiteralPath \$stop/);assert.match(s,/Existing Recovery Supervisor process \$oldPid did not stop/);assert.match(s,/Replacement Recovery Supervisor did not publish a fresh capability-bearing heartbeat/);assert.doesNotMatch(s,/\$pid\s*=/i);assert.ok(install.indexOf('Stop-InstalledSupervisorForReplacement')<install.indexOf('Copy-Item -LiteralPath $src'));assert.match(install,/control_plane_node_agent_sha256/);assert.match(install,/control_plane_node_sha256/);assert.match(s,/native-python\\python\.exe/);assert.match(s,/Get-ControlPlaneAgentArguments/);assert.match(s,/--runtime-mode/);assert.match(s,/RepetitionInterval \(New-TimeSpan -Minutes 1\)/);assert.match(s,/MultipleInstances IgnoreNew/);assert.match(s,/WindowsPowerShell\\v1\.0\\powershell\.exe/);assert.match(s,/New-ScheduledTaskAction -Execute \$powershell -Argument \$taskArgs/);assert.match(s,/\$taskArgs="-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File /);assert.match(vbs,/shell\.Run\(command, 0, True\)/i);assert.match(vbs,/-NonInteractive -WindowStyle Hidden /i);assert.doesNotMatch(vbs,/WScript\.Arguments|ShellExecute/i);assert.doesNotMatch(body,/\b(?:Assert-Manifest|Test-AbsoluteSafePath|Test-PathEqual|Get-Sha256File|Get-Sha256Text)\(/); });
  test('Recovery Supervisor connected-agent preflight does not depend on pilot read-only TTL', () => {
    const s = fs.readFileSync(script, 'utf8');
    assert.match(s, /Get-ControlPlaneStandingPolicyCandidates/);
    assert.match(s, /standing_policy_unavailable/);
    assert.match(s, /Test-ControlPlaneNodeCredential/);
    assert.match(s, /node_secret_dpapi/);
    assert.match(s, /run-connected-agent/);
    assert.doesNotMatch(s, /\$expires-le\[DateTimeOffset\]::UtcNow\.ToUnixTimeMilliseconds\(\)/);
  });
  test('Recovery Supervisor installs into the Task Scheduler-visible roaming data boundary', () => { const s=fs.readFileSync(script,'utf8'); assert.ok(s.includes("function Get-InstallRoot { Join-Path (Get-DataRoot) 'recovery-supervisor' }")); assert.ok(s.includes("function Get-LegacyInstallRoot { Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'WebMcpRecoverySupervisor' }")); assert.match(s,/function Stop-InstalledSupervisorForReplacement[^\n]+Get-LegacyInstallRoot/); assert.match(s,/function Wait-InstalledSupervisorReady[^\n]+Remove-LegacyInstallRoot/); assert.match(s,/function Uninstall-Supervisor\{[^\n]+Remove-LegacyInstallRoot/); });
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
    assert.deepEqual(observed[0].argv,['--deferred-worker',fs.realpathSync.native(requestPath)]);
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
