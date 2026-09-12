const test = require('node:test');
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const http = require('node:http');
const net = require('node:net');
const runtimePaths = require('../electron/paths');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { normalize } = require('../electron/services/config');
const runtimeStatePath = path.join(os.tmpdir(), `webcodex-live-supervisor-${process.pid}.json`);
const supervisorRequestPath = path.join(os.tmpdir(), `webcodex-live-supervisor-request-${process.pid}.json`);
runtimePaths.stateFile = () => runtimeStatePath;
runtimePaths.supervisorRequestFile = () => supervisorRequestPath;
fs.writeFileSync(runtimeStatePath, JSON.stringify({ manualStop: false }), 'utf8');
test.after(() => {
  fs.rmSync(runtimeStatePath, { force: true });
  fs.rmSync(supervisorRequestPath, { force: true });
  fs.rmSync(`${supervisorRequestPath}.bak`, { force: true });
  fs.rmSync(`${supervisorRequestPath}.processing`, { force: true });
  fs.rmSync(`${supervisorRequestPath}.processing.bak`, { force: true });
});
const { RuntimeOrchestrator, readMcpHealth, loopbackListenerPid } = require('../electron/services/runtimeOrchestrator');
const { installTunnelProcessFixture, withWorkingDirectory } = require('./helpers/tunnel-process-fixture');

const MCP_ROOT = path.resolve(__dirname, '..', 'resources', 'coding-tools-mcp');
const PYTHON = process.env.PYTHON || 'python';

const transientTempCleanupCodes = new Set(['EACCES', 'EBUSY', 'ENOTEMPTY', 'EPERM']);

function sleepSync(ms) {
  if (ms > 0) Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

function removeTempTree(target, options = {}) {
  const remove = options.remove || fs.rmSync;
  const sleep = options.sleep || sleepSync;
  const platform = options.platform || process.platform;
  const maxOuterRetries = Number.isInteger(options.maxOuterRetries) ? options.maxOuterRetries : 4;
  const retryBaseDelayMs = Number.isInteger(options.retryBaseDelayMs) ? options.retryBaseDelayMs : 250;
  for (let attempt = 0; ; attempt += 1) {
    try {
      remove(target, {
        recursive: true,
        force: true,
        maxRetries: platform === 'win32' ? 8 : 0,
        retryDelay: platform === 'win32' ? 50 : 0
      });
      return;
    } catch (error) {
      const retryable = platform === 'win32' && transientTempCleanupCodes.has(String(error?.code || ''));
      if (!retryable || attempt >= maxOuterRetries) throw error;
      sleep(Math.min(1000, retryBaseDelayMs * (attempt + 1)));
    }
  }
}

test('live supervisor test cleanup retries only bounded transient Windows teardown failures', () => {
  const transientDelays = [];
  let transientAttempts = 0;
  removeTempTree('ignored-transient', {
    platform: 'win32',
    maxOuterRetries: 2,
    retryBaseDelayMs: 10,
    sleep: (ms) => transientDelays.push(ms),
    remove: () => {
      transientAttempts += 1;
      if (transientAttempts < 3) throw Object.assign(new Error('transient'), { code: 'EPERM' });
    }
  });
  assert.equal(transientAttempts, 3);
  assert.deepEqual(transientDelays, [10, 20]);

  let terminalAttempts = 0;
  const terminal = Object.assign(new Error('terminal'), { code: 'EINVAL' });
  assert.throws(() => removeTempTree('ignored-terminal', {
    platform: 'win32',
    maxOuterRetries: 4,
    sleep: () => assert.fail('non-transient cleanup must not sleep or retry'),
    remove: () => { terminalAttempts += 1; throw terminal; }
  }), (error) => error === terminal);
  assert.equal(terminalAttempts, 1);

  let nonWindowsAttempts = 0;
  const nonWindows = Object.assign(new Error('non-windows'), { code: 'EPERM' });
  assert.throws(() => removeTempTree('ignored-non-windows', {
    platform: 'linux',
    maxOuterRetries: 4,
    sleep: () => assert.fail('non-Windows cleanup must not sleep or retry'),
    remove: () => { nonWindowsAttempts += 1; throw nonWindows; }
  }), (error) => error === nonWindows);
  assert.equal(nonWindowsAttempts, 1);

  const exhaustedDelays = [];
  let exhaustedAttempts = 0;
  const exhausted = Object.assign(new Error('exhausted'), { code: 'EBUSY' });
  assert.throws(() => removeTempTree('ignored-exhausted', {
    platform: 'win32',
    maxOuterRetries: 2,
    retryBaseDelayMs: 7,
    sleep: (ms) => exhaustedDelays.push(ms),
    remove: () => { exhaustedAttempts += 1; throw exhausted; }
  }), (error) => error === exhausted);
  assert.equal(exhaustedAttempts, 3);
  assert.deepEqual(exhaustedDelays, [7, 14]);
});

function waitForHealth(port, timeoutMs = 30000, token = '') {
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + timeoutMs;
    const attempt = () => {
      const request = http.get({ host: '127.0.0.1', port, path: '/__control/health', timeout: 1500, headers: token ? { Authorization: `Bearer ${token}` } : {} }, (response) => {
        response.resume();
        if (response.statusCode === 200) { resolve(true); return; }
        retry();
      });
      request.on('error', retry);
      request.on('timeout', () => { request.destroy(); retry(); });
    };
    const retry = () => {
      if (Date.now() > deadline) { reject(new Error('MCP health timeout')); return; }
      setTimeout(attempt, 150);
    };
    attempt();
  });
}

function freePort() { return new Promise((resolve,reject)=>{const server=net.createServer();server.once('error',reject);server.listen(0,'127.0.0.1',()=>{const port=server.address().port;server.close((error)=>error?reject(error):resolve(port));});}); }
function processAlive(pid) { try { process.kill(Number(pid),0);return Number(pid)>0; } catch { return false; } }
async function waitForPidExit(pid,timeoutMs=5000){const deadline=Date.now()+timeoutMs;while(Date.now()<deadline&&processAlive(pid)){await new Promise((resolve)=>setTimeout(resolve,50));}assert.equal(processAlive(pid),false,`PID ${pid} remained alive`);}
async function readLoopbackJson(port){return new Promise((resolve,reject)=>{const request=http.get({host:'127.0.0.1',port,path:'/healthz',timeout:1500},(response)=>{let body='';response.setEncoding('utf8');response.on('data',(chunk)=>{body+=chunk;});response.on('end',()=>{try{resolve({status:response.statusCode,body:JSON.parse(body)});}catch(error){reject(error);}});});request.on('timeout',()=>request.destroy(new Error('loopback health timeout')));request.on('error',reject);});}
async function startLoopbackProxy(){const server=http.createServer((_request,response)=>{response.writeHead(200,{'Content-Length':'0'});response.end();});let connectCount=0;server.on('connect',(_request,socket)=>{connectCount+=1;socket.write('HTTP/1.1 200 Connection Established\r\nProxy-Agent: webcodex-test\r\n\r\n');socket.end();});await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});return{server,url:`http://127.0.0.1:${server.address().port}`,connectCount:()=>connectCount};}

function spawnMcp(workspace, port, options = {}) {
  const env = {
    ...process.env,
    PYTHONIOENCODING: 'utf-8',
    CODING_TOOLS_MCP_TOOL_MODE: 'smart',
    ...(options.authToken ? { CODING_TOOLS_MCP_AUTH_TOKEN: options.authToken } : {}),
    ...(options.deviceId ? { CODING_TOOLS_MCP_DEVICE_ID: options.deviceId } : {}),
    ...(options.deviceInstanceId ? { CODING_TOOLS_MCP_DEVICE_INSTANCE_ID: options.deviceInstanceId } : {}),
    ...(options.deviceDisplayName ? { CODING_TOOLS_MCP_DEVICE_DISPLAY_NAME: options.deviceDisplayName } : {}),
    ...(options.connectorAttestationSecret ? {
      CODING_TOOLS_MCP_CONNECTOR_ATTESTATION_SECRET: options.connectorAttestationSecret
    } : {})
  };
  const child = spawn(PYTHON, ['-m', 'coding_tools_mcp', '--port', String(port), '--workspace', workspace], {
    cwd: MCP_ROOT,
    env,
    windowsHide: true,
    stdio: ['ignore', 'ignore', 'pipe']
  });
  let stderr = '';
  child.stderr.on('data', (chunk) => { stderr += chunk.toString().slice(-4000); });
  child._stderrTail = () => stderr;
  return child;
}

function makeHarness(mcpProcess, mcpPortSetting, tunnelStatus, failureKind) {
  const calls = { restart: 0, tunnelStarts: 0, mcpReplacements: 0 };
  const orchestrator = new RuntimeOrchestrator({
    settings: {
      load: () => ({
        workspace: '',
        mcpPort: mcpPortSetting,
        tunnelId: 'test-tunnel',
        autoStartServices: true,
        proxyMode: 'auto',
        proxyUrl: '',
        healthPort: 18090
      })
    },
    secrets: {
      get: (key) => ({ runtimeApiKey: 'test-runtime-key', mcpAuthToken: 'test-mcp-token' }[key] || ''),
      set() {}
    },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    emitStatus() {}
  });
  orchestrator.activationEpochStore = { current: () => null };
  orchestrator.heartbeatFailures = 2;
  orchestrator.heartbeatFailureKind = failureKind;
  orchestrator.native = {
    status: async () => mcpProcess.exitCode === null && mcpProcess.signalCode === null
  };
  orchestrator.tunnel = {
    status: async () => tunnelStatus,
    start: async () => { calls.tunnelStarts += 1; }
  };
  orchestrator.restart = async () => {
    calls.restart += 1;
    if (mcpProcess.exitCode === null && mcpProcess.signalCode === null) {
      mcpProcess.kill();
      await new Promise((resolve) => mcpProcess.once('close', resolve));
    }
  };
  const connectorHealth = {
    ready: true,
    process_instance_id: 'managed-mcp-process-test',
    instance_id: 'managed-mcp-server-test',
    tool_contract: { sha256: 'a'.repeat(64) }
  };
  if (failureKind === 'tunnel_unavailable') {
    orchestrator.currentMcpHealth = async () => connectorHealth;
    const connectorSecret = orchestrator.rotateConnectorAttestationSecret();
    orchestrator.connectorAttestationForHealth(connectorHealth, { establish: true, secret: connectorSecret });
  }
  orchestrator.recoverMcpOnly = async (options = {}) => {
    assert.equal(options.replaceLiveOwned, true);
    calls.mcpReplacements += 1;
    if (mcpProcess.exitCode === null && mcpProcess.signalCode === null) {
      mcpProcess.kill();
      await new Promise((resolve) => mcpProcess.once('close', resolve));
    }
  };
  orchestrator.isManuallyStopped = () => false;
  return { orchestrator, calls };
}

test('real primary Tunnel recovery replaces only the Tunnel PID and preserves the real Coding MCP identity', { skip: process.platform !== 'win32' }, async () => {
  const temp=fs.mkdtempSync(path.join(os.tmpdir(),'webcodex-primary-tunnel-real-'));
  const workspace=path.join(temp,'workspace');
  const fixtureDir=path.join(temp,'tunnel-fixture');
  fs.mkdirSync(workspace,{recursive:true});
  installTunnelProcessFixture(fixtureDir);
  const mcpPort=await freePort();
  const healthPort=await freePort();
  const authToken='m'.repeat(48);
  const deviceId='12345678-1234-4123-8123-123456789abc';
  const deviceInstanceId='primary-tunnel-real-instance-0001';
  const connectorAttestationSecret='primary-tunnel-attestation-secret';
  const proxy=await startLoopbackProxy();
  const stateFile=path.join(temp,'runtime-state.json');
  const mcp=spawnMcp(workspace,mcpPort,{authToken,deviceId,deviceInstanceId,deviceDisplayName:'Primary tunnel PID test',connectorAttestationSecret});
  let activeTunnelPid=0;
  try {
    await waitForHealth(mcpPort,30000,authToken);
    const initialHealth=await readMcpHealth(mcpPort,authToken,workspace,deviceId);
    assert.ok(initialHealth,mcp._stderrTail()||'Coding MCP did not expose the expected workspace/device health identity');
    assert.equal(processAlive(mcp.pid),true);
    fs.writeFileSync(stateFile,JSON.stringify({manualStop:false,nativePid:mcp.pid,nativePort:mcpPort,nativeWorkspace:workspace,nativeDeviceId:deviceId,nativeDeviceInstanceId:deviceInstanceId}),'utf8');
    const settings={workspace,mcpPort,tunnelId:'tunnel_primary_pid_real',autoStartServices:true,proxyMode:'manual',proxyUrl:proxy.url,healthPort};
    const orchestrator=new RuntimeOrchestrator({
      settings:{load:()=>settings},
      secrets:{get:(key)=>({runtimeApiKey:'primary-runtime-key-local-only',mcpAuthToken:authToken}[key]||''),set(){}},
      environment:{},
      log:{info(){},warn(){},error(){}},
      emitProgress(){},
      emitStatus(){},
      paths:{stateFile:()=>stateFile,tunnelExecutable:()=>process.execPath,tunnelLogFile:()=>path.join(temp,'primary-tunnel.log')},
      revisionTracker:{},
      deviceIdentity:{version:1,device_id:deviceId,display_name:'Primary tunnel PID test',created_at:'2026-08-17T00:00:00.000Z'},
      deviceInstanceId
    });
    orchestrator.activationEpochStore = { current: () => null };
    orchestrator.connectorAttestationForHealth(initialHealth, {
      establish: true,
      secret: connectorAttestationSecret
    });

    await withWorkingDirectory(fixtureDir,()=>orchestrator.recoverTunnelOnly());
    let state=JSON.parse(fs.readFileSync(stateFile,'utf8'));
    const firstTunnelPid=Number(state.tunnelPid);
    activeTunnelPid=firstTunnelPid;
    assert.ok(firstTunnelPid>0);
    assert.equal(Number(state.nativePid),mcp.pid);
    assert.equal(state.nativeWorkspace,workspace);
    assert.equal(state.nativeDeviceId,deviceId);
    assert.equal(state.tunnelDeviceId,deviceId);
    assert.equal(state.tunnelDeviceInstanceId,deviceInstanceId);
    assert.equal(await loopbackListenerPid(healthPort),firstTunnelPid);
    const firstTunnelHealth=await readLoopbackJson(healthPort);
    assert.equal(firstTunnelHealth.status,200);
    assert.equal(firstTunnelHealth.body.pid,firstTunnelPid);

    process.kill(firstTunnelPid);
    await waitForPidExit(firstTunnelPid);
    activeTunnelPid=0;
    assert.equal(processAlive(mcp.pid),true,'Coding MCP must remain alive when only the primary Tunnel is killed');
    const preservedHealth=await readMcpHealth(mcpPort,authToken,workspace,deviceId);
    assert.ok(preservedHealth,mcp._stderrTail()||'Coding MCP health identity changed after Tunnel-only failure');

    await withWorkingDirectory(fixtureDir,()=>orchestrator.recoverTunnelOnly());
    state=JSON.parse(fs.readFileSync(stateFile,'utf8'));
    const secondTunnelPid=Number(state.tunnelPid);
    activeTunnelPid=secondTunnelPid;
    assert.ok(secondTunnelPid>0);
    assert.notEqual(secondTunnelPid,firstTunnelPid);
    assert.equal(Number(state.nativePid),mcp.pid);
    assert.equal(state.nativeWorkspace,workspace);
    assert.equal(state.nativeDeviceId,deviceId);
    assert.equal(state.nativeDeviceInstanceId,deviceInstanceId);
    assert.equal(await loopbackListenerPid(healthPort),secondTunnelPid);
    const secondTunnelHealth=await readLoopbackJson(healthPort);
    assert.equal(secondTunnelHealth.body.pid,secondTunnelPid);
    assert.ok(await readMcpHealth(mcpPort,authToken,workspace,deviceId));
  } finally {
    if(processAlive(activeTunnelPid)){try{process.kill(activeTunnelPid);}catch{}await waitForPidExit(activeTunnelPid).catch(()=>{});}
    if(mcp.exitCode===null&&mcp.signalCode===null){mcp.kill();await new Promise((resolve)=>mcp.once('close',resolve));}
    await new Promise((resolve)=>proxy.server.close(resolve));
    removeTempTree(temp);
  }
});

test('live supervisor recovers only the tunnel and never kills a healthy MCP', async () => {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-sup-'));
  const port = 19121;
  const mcp = spawnMcp(workspace, port);
  try {
    await waitForHealth(port);
    const { orchestrator, calls } = makeHarness(mcp, port, false, 'tunnel_unavailable');
    await orchestrator.supervise();
    assert.equal(calls.tunnelStarts, 1);
    assert.equal(calls.restart, 0);
    assert.equal(mcp.exitCode, null, 'MCP must still be running after tunnel recovery'); assert.equal(mcp.signalCode, null);
  } finally {
    if (mcp.exitCode === null && mcp.signalCode === null) {
      mcp.kill();
      await new Promise((resolve) => mcp.once('close', resolve));
    }
    removeTempTree(workspace);
  }
});

test('live supervisor escalates by replacing only a hung live MCP after repeated deferrals', async () => {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-sup-'));
  const port = 19122;
  const mcp = spawnMcp(workspace, port);
  try {
    await waitForHealth(port);
    const { orchestrator, calls } = makeHarness(mcp, port + 1, false, 'mcp_health_unavailable');
    orchestrator.heartbeatFailures = 2;
    orchestrator.heartbeatFailureKind = 'mcp_health_unavailable';
    const maxDeferred = 6;
    for (let attempt = 1; attempt < maxDeferred; attempt += 1) {
      orchestrator.nextRecoveryAt = 0;
      const result = await orchestrator.supervise();
      assert.equal(result.recoveryDeferred, true);
      assert.equal(mcp.exitCode, null, 'MCP must survive the deferral phase'); assert.equal(mcp.signalCode, null);
    }
    orchestrator.nextRecoveryAt = 0;
    await orchestrator.supervise();
    assert.equal(calls.restart, 0);
    assert.equal(calls.mcpReplacements, 1);
    assert.equal(mcp.exitCode === null && mcp.signalCode === null, false, 'MCP must be replaced without touching Tunnel');
  } finally {
    if (mcp.exitCode === null && mcp.signalCode === null) {
      mcp.kill();
      await new Promise((resolve) => mcp.once('close', resolve));
    }
    removeTempTree(workspace);
  }
});

test('live supervisor replaces a dead owned Coding MCP and refreshes only its dependent attested Tunnel', { skip: process.platform !== 'win32', timeout: 60000 }, async () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-mcp-only-real-'));
  const workspace = path.join(temp, 'workspace');
  const fixtureDir = path.join(temp, 'tunnel-fixture');
  const dataRoot = path.join(temp, 'data');
  fs.mkdirSync(workspace, { recursive: true });
  fs.mkdirSync(dataRoot, { recursive: true });
  installTunnelProcessFixture(fixtureDir);
  const mcpPort = await freePort();
  const healthPort = await freePort();
  const authToken = 'r'.repeat(48);
  const deviceId = '12345678-1234-4123-8123-123456789abc';
  const deviceInstanceId = 'primary-mcp-recovery-instance-0001';
  const proxy = await startLoopbackProxy();
  const paths = createRuntimePaths({
    dataRoot,
    appRoot: path.resolve(__dirname, '..'),
    resourcesRoot: path.resolve(__dirname, '..', 'resources')
  });
  paths.tunnelExecutable = () => process.execPath;
  fs.writeFileSync(paths.stateFile(), JSON.stringify({ manualStop: false }), 'utf8');
  const settings = normalize({
    workspace,
    mcpPort,
    healthPort,
    tunnelId: 'tunnel_primary_mcp_recovery',
    autoStartServices: true,
    proxyMode: 'manual',
    proxyUrl: proxy.url,
    permissionMode: 'trusted'
  });
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => settings },
    secrets: {
      get: (key) => ({ runtimeApiKey: 'primary-runtime-key-local-only', mcpAuthToken: authToken }[key] || ''),
      set() {}
    },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    emitStatus() {},
    paths,
    deviceIdentity: { version: 1, device_id: deviceId, display_name: 'Primary MCP recovery test', created_at: '2026-08-17T00:00:00.000Z' },
    deviceInstanceId
  });
  let activeMcpPid = 0;
  let activeTunnelPid = 0;
  try {
    const initialMcp = await withWorkingDirectory(fixtureDir, () => orchestrator.recoverMcpOnly());
    activeMcpPid = initialMcp.new_pid;
    activeTunnelPid = initialMcp.tunnel_pid;
    assert.ok(activeMcpPid > 0);
    assert.ok(activeTunnelPid > 0);
    assert.equal(initialMcp.tunnel_attestation_refreshed, true);
    assert.ok(await readMcpHealth(mcpPort, authToken, workspace, deviceId));
    assert.equal(await loopbackListenerPid(mcpPort), activeMcpPid);

    await withWorkingDirectory(fixtureDir, () => orchestrator.recoverTunnelOnly());
    let state = JSON.parse(fs.readFileSync(paths.stateFile(), 'utf8'));
    activeTunnelPid = Number(state.tunnelPid);
    const preservedTunnelPid = activeTunnelPid;
    assert.ok(preservedTunnelPid > 0);
    assert.equal(await loopbackListenerPid(healthPort), preservedTunnelPid);
    assert.equal((await readLoopbackJson(healthPort)).body.pid, preservedTunnelPid);

    const firstMcpPid = activeMcpPid;
    process.kill(firstMcpPid);
    await waitForPidExit(firstMcpPid);
    activeMcpPid = 0;
    assert.equal(processAlive(preservedTunnelPid), true, 'Primary Tunnel must remain alive after Coding MCP exits');
    assert.equal(await loopbackListenerPid(healthPort), preservedTunnelPid);

    orchestrator.heartbeatFailures = 2;
    orchestrator.heartbeatFailureKind = 'mcp_process_exited';
    orchestrator.nextRecoveryAt = 0;
    await withWorkingDirectory(fixtureDir, () => orchestrator.supervise());

    state = JSON.parse(fs.readFileSync(paths.stateFile(), 'utf8'));
    const replacementMcpPid = Number(state.nativePid);
    activeMcpPid = replacementMcpPid;
    assert.ok(replacementMcpPid > 0);
    assert.notEqual(replacementMcpPid, firstMcpPid);
    assert.equal(state.nativeWorkspace, path.resolve(workspace));
    assert.equal(state.nativeDeviceId, deviceId);
    assert.equal(state.nativeDeviceInstanceId, deviceInstanceId);
    const replacementTunnelPid = Number(state.tunnelPid);
    activeTunnelPid = replacementTunnelPid;
    assert.ok(replacementTunnelPid > 0);
    assert.notEqual(replacementTunnelPid, preservedTunnelPid);
    assert.equal(state.tunnelDeviceId, deviceId);
    assert.equal(state.tunnelDeviceInstanceId, deviceInstanceId);
    assert.equal(processAlive(preservedTunnelPid), false);
    assert.equal(await loopbackListenerPid(healthPort), replacementTunnelPid);
    assert.equal((await readLoopbackJson(healthPort)).body.pid, replacementTunnelPid);
    assert.equal(await loopbackListenerPid(mcpPort), replacementMcpPid);
    const replacementHealth = await readMcpHealth(mcpPort, authToken, workspace, deviceId);
    assert.ok(replacementHealth);
    assert.equal(replacementHealth.device_instance_id, deviceInstanceId);
  } finally {
    if (processAlive(activeMcpPid)) {
      await orchestrator.native.stop();
      await waitForPidExit(activeMcpPid, 10000);
    }
    if (processAlive(activeTunnelPid)) {
      try { process.kill(activeTunnelPid); } catch {}
      await waitForPidExit(activeTunnelPid).catch(() => {});
    }
    await new Promise((resolve) => proxy.server.close(resolve));
    removeTempTree(temp);
  }
});
