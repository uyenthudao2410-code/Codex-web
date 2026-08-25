const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const net = require('node:net');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');
const electronExecutable = require('electron');
const { createRuntimePaths } = require('../../electron/services/runtimePaths');
const { RecoveryIpcClient } = require('../../electron/services/recoveryIpc');

const ROOT = path.resolve(__dirname, '..', '..');
const FIXTURE = path.join(ROOT, 'tests', 'fixtures', 'recovery-host-process-app.js');
const OLD_REVISION = 'a'.repeat(64);
const NEXT_REVISION = 'b'.repeat(64);

function wait(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

function processAlive(pid) {
  try { process.kill(Number(pid), 0); return true; } catch { return false; }
}

function readJson(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return null; }
}

async function waitForJson(file, errorFile, timeoutMs = 20_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const error = readJson(errorFile);
    if (error) throw Object.assign(new Error(error.message), { code: error.code });
    const value = readJson(file);
    if (value) return value;
    await wait(50);
  }
  throw new Error(`Timed out waiting for ${path.basename(file)}.`);
}

async function waitForExit(child, timeoutMs = 10_000) {
  if (!child || child.exitCode !== null || child.signalCode !== null) return true;
  return new Promise((resolve) => {
    const onExit = () => {
      clearTimeout(timer);
      resolve(true);
    };
    const timer = setTimeout(() => {
      child.removeListener('exit', onExit);
      resolve(false);
    }, timeoutMs);
    child.once('exit', onExit);
  });
}

async function stopProcess(child) {
  if (!child || child.exitCode !== null || child.signalCode !== null) return;
  child.kill();
  await waitForExit(child, 5000);
}

function spawnStandIn(component) {
  const child = spawn(process.execPath, [
    '-e',
    'setTimeout(() => process.exit(0), 120000); setInterval(() => {}, 1000);'
  ], {
    windowsHide: true,
    stdio: 'ignore',
    env: { ...process.env, WEBCODEX_RECOVERY_TEST_COMPONENT: component }
  });
  return new Promise((resolve, reject) => {
    child.once('spawn', () => resolve(child));
    child.once('error', reject);
  });
}

async function waitForPidExit(pid, timeoutMs = 10_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (!processAlive(pid)) return true;
    await wait(50);
  }
  return !processAlive(pid);
}

function activationRequest(component, operationId) {
  const now = Date.now();
  return {
    operation_id: operationId,
    component,
    requested_at_unix_ms: now,
    expires_at_unix_ms: now + 30_000,
    expected_disk_revision: NEXT_REVISION,
    allow_acceptance_pending: false,
    source_checkpoint: {
      checkpoint_id: 'checkpoint-process-activation-0001',
      run_id: 'run-process-activation-0001',
      wave_id: 'wave-process-activation-0001',
      proof_fingerprint: 'c'.repeat(64),
      git_head: 'd'.repeat(40)
    }
  };
}

function spawnElectron({
  role,
  dataRoot,
  resourcesRoot,
  reportFile,
  errorFile,
  clientId,
  exitAfterAttach = false,
  activationMode = '',
  mcpPid = 0,
  tunnelPid = 0,
  hostRunningRevision = '',
  replacementReportFile = ''
}) {
  const args = [
    FIXTURE,
    '--disable-gpu',
    '--fixture-role', role,
    '--data-root', dataRoot,
    '--resources-root', resourcesRoot,
    '--report-file', reportFile,
    '--error-file', errorFile,
    '--node-executable', process.execPath
  ];
  if (clientId) args.push('--client-id', clientId);
  if (exitAfterAttach) args.push('--exit-after-attach');
  if (activationMode) args.push('--activation-mode', activationMode);
  if (mcpPid) args.push('--mcp-pid', String(mcpPid));
  if (tunnelPid) args.push('--tunnel-pid', String(tunnelPid));
  if (hostRunningRevision) args.push('--host-running-revision', hostRunningRevision);
  if (replacementReportFile) args.push('--replacement-report-file', replacementReportFile);
  const env = {
    ...process.env,
    ELECTRON_DISABLE_SECURITY_WARNINGS: '1'
  };
  delete env.ELECTRON_RUN_AS_NODE;
  const child = spawn(electronExecutable, args, {
    cwd: ROOT,
    windowsHide: true,
    stdio: ['ignore', 'pipe', 'pipe'],
    env
  });
  let output = '';
  const collect = (chunk) => { output = `${output}${chunk}`.slice(-4000); };
  child.stdout.on('data', collect);
  child.stderr.on('data', collect);
  child.outputTail = () => output;
  return child;
}

function gatewayReachable(port, timeoutMs = 2000) {
  return new Promise((resolve) => {
    const socket = net.connect({ host: '127.0.0.1', port: Number(port) });
    let settled = false;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      socket.destroy();
      resolve(value);
    };
    socket.setTimeout(timeoutMs, () => finish(false));
    socket.once('connect', () => finish(true));
    socket.once('error', () => finish(false));
  });
}

async function waitForSupervision(client, previousCount, timeoutMs = 12_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const snapshot = await client.lightweightSnapshot();
    if (Number(snapshot.supervisionCount) > previousCount) return snapshot;
    await wait(100);
  }
  throw new Error('Recovery Host watchdog did not run after the Electron client exited.');
}

function removeTempTree(target) {
  fs.rmSync(target, {
    recursive: true,
    force: true,
    maxRetries: process.platform === 'win32' ? 10 : 0,
    retryDelay: process.platform === 'win32' ? 100 : 0
  });
}

test('real Electron client can be killed and reattach without replacing Recovery Host runtime ownership', {
  skip: process.platform !== 'win32',
  timeout: 45_000
}, async () => {
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-recovery-process-'));
  const dataRoot = path.join(tempRoot, 'data');
  const resourcesRoot = path.join(tempRoot, 'resources');
  const errorFile = path.join(tempRoot, 'fixture-error.json');
  const hostReportFile = path.join(tempRoot, 'host.json');
  const firstClientReportFile = path.join(tempRoot, 'client-first.json');
  const secondClientReportFile = path.join(tempRoot, 'client-second.json');
  fs.mkdirSync(dataRoot, { recursive: true });
  fs.mkdirSync(resourcesRoot, { recursive: true });
  const paths = createRuntimePaths({ dataRoot, resourcesRoot });
  let host;
  let firstClient;
  let secondClient;
  let hostReport;

  try {
    host = spawnElectron({
      role: 'host', dataRoot, resourcesRoot, reportFile: hostReportFile, errorFile
    });
    hostReport = await waitForJson(hostReportFile, errorFile);
    assert.equal(hostReport.hostPid, host.pid);
    assert.equal(hostReport.gatewayOwnerPid, host.pid);
    assert.equal(processAlive(hostReport.mcpPid), true);
    assert.equal(processAlive(hostReport.tunnelPid), true);

    firstClient = spawnElectron({
      role: 'client',
      dataRoot,
      resourcesRoot,
      reportFile: firstClientReportFile,
      errorFile,
      clientId: 'first'
    });
    const first = await waitForJson(firstClientReportFile, errorFile);
    assert.equal(first.clientPid, firstClient.pid);
    assert.equal(first.hostPid, host.pid);
    assert.equal(first.hostInstanceId, hostReport.hostInstanceId);
    assert.equal(first.mcpPid, hostReport.mcpPid);
    assert.equal(first.tunnelPid, hostReport.tunnelPid);
    assert.equal(first.gatewayOwnerPid, host.pid);
    assert.equal(first.gatewayReachable, true);

    firstClient.kill();
    assert.equal(await waitForExit(firstClient), true, firstClient.outputTail());
    assert.equal(processAlive(host.pid), true);
    assert.equal(processAlive(hostReport.mcpPid), true);
    assert.equal(processAlive(hostReport.tunnelPid), true);
    assert.equal(await gatewayReachable(hostReport.gatewayPort), true);

    const parentClient = new RecoveryIpcClient({ paths });
    const supervised = await waitForSupervision(parentClient, first.supervisionCount);
    assert.equal(supervised.mcpPid, hostReport.mcpPid);
    assert.equal(supervised.tunnelPid, hostReport.tunnelPid);
    assert.equal(supervised.fullyReady, true);

    secondClient = spawnElectron({
      role: 'client',
      dataRoot,
      resourcesRoot,
      reportFile: secondClientReportFile,
      errorFile,
      clientId: 'second',
      exitAfterAttach: true
    });
    const second = await waitForJson(secondClientReportFile, errorFile);
    assert.equal(await waitForExit(secondClient), true, secondClient.outputTail());
    assert.equal(second.hostPid, host.pid);
    assert.equal(second.hostInstanceId, hostReport.hostInstanceId);
    assert.equal(second.mcpPid, hostReport.mcpPid);
    assert.equal(second.tunnelPid, hostReport.tunnelPid);
    assert.equal(second.gatewayOwnerPid, host.pid);
    assert.equal(second.gatewayPort, hostReport.gatewayPort);
    assert.equal(second.gatewayReachable, true);
  } finally {
    await stopProcess(firstClient);
    await stopProcess(secondClient);
    try { fs.writeFileSync(path.join(dataRoot, 'fixture-shutdown.request'), '', 'utf8'); } catch { /* host may not have started */ }
    if (host && !await waitForExit(host, 8000)) await stopProcess(host);
    for (const pid of [hostReport?.mcpPid, hostReport?.tunnelPid]) {
      if (processAlive(pid)) {
        try { process.kill(pid); } catch { /* exact fixture PID cleanup */ }
      }
    }
    removeTempTree(tempRoot);
  }
});

test('real Safe Code Activation replaces Coding MCP process while preserving Tunnel and gateway', {
  skip: process.platform !== 'win32',
  timeout: 45_000
}, async () => {
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-recovery-mcp-activation-'));
  const dataRoot = path.join(tempRoot, 'data');
  const resourcesRoot = path.join(tempRoot, 'resources');
  const errorFile = path.join(tempRoot, 'fixture-error.json');
  const hostReportFile = path.join(tempRoot, 'host.json');
  fs.mkdirSync(dataRoot, { recursive: true });
  fs.mkdirSync(resourcesRoot, { recursive: true });
  const paths = createRuntimePaths({ dataRoot, resourcesRoot });
  let host;
  let hostReport;
  let replacementMcpPid = 0;

  try {
    host = spawnElectron({
      role: 'host', dataRoot, resourcesRoot, reportFile: hostReportFile, errorFile, activationMode: 'coding-mcp'
    });
    hostReport = await waitForJson(hostReportFile, errorFile);
    const client = new RecoveryIpcClient({ paths });
    const request = activationRequest('coding_mcp', 'coding-activation-0001');
    const preflight = await client.activationPreflight(request);
    assert.equal(preflight.safe, true);
    assert.equal(preflight.code, 'READY');

    const activation = await client.activateUpdate(request);
    assert.equal(activation.state, 'completed');
    assert.equal(activation.result.activated, true);
    assert.equal(activation.result.tunnel_preserved, true);
    const status = await client.activationStatus(request.operation_id);
    assert.equal(status.state, 'completed');

    const snapshot = await client.lightweightSnapshot();
    replacementMcpPid = Number(snapshot.mcpPid || 0);
    assert.notEqual(replacementMcpPid, hostReport.mcpPid);
    assert.equal(await waitForPidExit(hostReport.mcpPid, 5000), true);
    assert.equal(processAlive(replacementMcpPid), true);
    assert.equal(snapshot.tunnelPid, hostReport.tunnelPid);
    assert.equal(processAlive(hostReport.tunnelPid), true);
    assert.equal(processAlive(host.pid), true);
    assert.equal(await gatewayReachable(hostReport.gatewayPort), true);
  } finally {
    try { fs.writeFileSync(path.join(dataRoot, 'fixture-shutdown.request'), '', 'utf8'); } catch { /* host may not have started */ }
    if (host && !await waitForExit(host, 8000)) await stopProcess(host);
    for (const pid of [hostReport?.mcpPid, replacementMcpPid, hostReport?.tunnelPid]) {
      if (processAlive(pid)) {
        try { process.kill(pid); } catch { /* exact fixture PID cleanup */ }
      }
    }
    removeTempTree(tempRoot);
  }
});

test('real Recovery Host activation hands ownership to a new Electron host without replacing MCP or Tunnel', {
  skip: process.platform !== 'win32',
  timeout: 60_000
}, async () => {
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-recovery-host-activation-'));
  const dataRoot = path.join(tempRoot, 'data');
  const resourcesRoot = path.join(tempRoot, 'resources');
  const errorFile = path.join(tempRoot, 'fixture-error.json');
  const oldHostReportFile = path.join(tempRoot, 'host-old.json');
  const replacementReportFile = path.join(tempRoot, 'host-replacement.json');
  fs.mkdirSync(dataRoot, { recursive: true });
  fs.mkdirSync(resourcesRoot, { recursive: true });
  const paths = createRuntimePaths({ dataRoot, resourcesRoot });
  let mcp;
  let tunnel;
  let oldHost;
  let oldReport;
  let replacementReport;

  try {
    [mcp, tunnel] = await Promise.all([
      spawnStandIn('external-coding-mcp'),
      spawnStandIn('external-coding-tunnel')
    ]);
    oldHost = spawnElectron({
      role: 'host',
      dataRoot,
      resourcesRoot,
      reportFile: oldHostReportFile,
      errorFile,
      activationMode: 'recovery-host',
      mcpPid: mcp.pid,
      tunnelPid: tunnel.pid,
      hostRunningRevision: OLD_REVISION,
      replacementReportFile
    });
    oldReport = await waitForJson(oldHostReportFile, errorFile);
    assert.equal(oldReport.hostPid, oldHost.pid);
    assert.equal(oldReport.mcpPid, mcp.pid);
    assert.equal(oldReport.tunnelPid, tunnel.pid);

    const oldClient = new RecoveryIpcClient({ paths });
    const request = activationRequest('recovery_host', 'recovery-activation-0001');
    const preflight = await oldClient.activationPreflight(request);
    assert.equal(preflight.safe, true);
    assert.equal(preflight.code, 'READY');
    const accepted = await oldClient.activateUpdate(request);
    assert.equal(accepted.state, 'accepted');

    replacementReport = await waitForJson(replacementReportFile, errorFile, 30_000);
    assert.notEqual(replacementReport.hostPid, oldReport.hostPid);
    assert.notEqual(replacementReport.hostInstanceId, oldReport.hostInstanceId);
    assert.equal(replacementReport.mcpPid, mcp.pid);
    assert.equal(replacementReport.tunnelPid, tunnel.pid);
    assert.equal(processAlive(mcp.pid), true);
    assert.equal(processAlive(tunnel.pid), true);
    assert.equal(await waitForExit(oldHost, 15_000), true, oldHost.outputTail());

    const replacementClient = new RecoveryIpcClient({ paths });
    const ping = await replacementClient.ping();
    assert.equal(ping.pid, replacementReport.hostPid);
    assert.equal(ping.instance_id, replacementReport.hostInstanceId);
    const completed = await replacementClient.activationStatus(request.operation_id);
    assert.equal(completed.state, 'completed');
    assert.equal(completed.result.coding_mcp_preserved, true);
    assert.equal(completed.result.tunnel_preserved, true);
    const snapshot = await replacementClient.lightweightSnapshot();
    assert.equal(snapshot.mcpPid, mcp.pid);
    assert.equal(snapshot.tunnelPid, tunnel.pid);
    assert.equal(replacementReport.gatewayOwnerPid, replacementReport.hostPid);
    assert.equal(await gatewayReachable(replacementReport.gatewayPort), true);
  } finally {
    try { fs.writeFileSync(path.join(dataRoot, 'fixture-shutdown.request'), '', 'utf8'); } catch { /* replacement may not have started */ }
    if (replacementReport?.hostPid && !await waitForPidExit(replacementReport.hostPid, 8000)) {
      try { process.kill(replacementReport.hostPid); } catch { /* exact fixture PID cleanup */ }
    }
    await stopProcess(oldHost);
    await stopProcess(mcp);
    await stopProcess(tunnel);
    removeTempTree(tempRoot);
  }
});
