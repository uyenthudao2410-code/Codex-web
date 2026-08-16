const fs = require('node:fs');
const net = require('node:net');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { app } = require('electron');
const { createRuntimePaths } = require('../../electron/services/runtimePaths');
const { RecoveryHost } = require('../../electron/services/recoveryHost');
const { RecoveryIpcClient } = require('../../electron/services/recoveryIpc');
const { readJson, writeJsonAtomic } = require('../../electron/services/jsonStore');

function argument(name, fallback = '') {
  const index = process.argv.indexOf(name);
  return index >= 0 && index + 1 < process.argv.length ? process.argv[index + 1] : fallback;
}

function processAlive(pid) {
  try { process.kill(Number(pid), 0); return true; } catch { return false; }
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

function spawnStandIn(nodeExecutable, component) {
  const child = spawn(nodeExecutable, [
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

async function stopChild(child) {
  if (!child || !processAlive(child.pid)) return;
  child.kill();
  await new Promise((resolve) => {
    const onExit = () => {
      clearTimeout(timer);
      resolve();
    };
    const timer = setTimeout(() => {
      child.removeListener('exit', onExit);
      resolve();
    }, 3000);
    child.once('exit', onExit);
  });
}

function runtimeProjection(mcp, tunnel, supervisionCount) {
  const mcpRunning = processAlive(mcp.pid);
  const tunnelRunning = processAlive(tunnel.pid);
  return {
    mcpRunning,
    tunnelRunning,
    fullyReady: mcpRunning && tunnelRunning,
    recovering: false,
    recoveryBlocked: false,
    mcpPid: mcp.pid,
    tunnelPid: tunnel.pid,
    supervisionCount
  };
}

async function runHost(paths, dataRoot, reportFile, nodeExecutable) {
  const [mcp, tunnel] = await Promise.all([
    spawnStandIn(nodeExecutable, 'coding-mcp'),
    spawnStandIn(nodeExecutable, 'coding-tunnel')
  ]);
  let supervisionCount = 0;
  const projection = () => runtimeProjection(mcp, tunnel, supervisionCount);
  const orchestrator = {
    isManuallyStopped: () => false,
    supervise: async () => { supervisionCount += 1; return projection(); },
    snapshot: async () => ({ status: projection() }),
    lightweightSnapshot: async () => projection(),
    start: async () => projection(),
    stop: async () => projection(),
    restart: async () => projection(),
    switchWorkspace: async () => projection(),
    updateAuthorizedRoots: async () => projection(),
    acknowledgeConnectorContract: async () => projection()
  };
  const settings = {
    load: () => ({ autoStartServices: false, mcpPort: 65534 })
  };
  const secrets = { get: () => 'fixture-token' };
  const log = { info() {}, warn() {}, error() {}, read: () => [], clear() {} };
  const host = new RecoveryHost({
    paths,
    settings,
    secrets,
    environment: {},
    log,
    orchestrator,
    healthService: { inspect: async () => projection(), repair: async () => projection() }
  });
  let shuttingDown = false;
  const shutdown = async () => {
    if (shuttingDown) return;
    shuttingDown = true;
    clearInterval(shutdownTimer);
    await host.stop().catch(() => false);
    await Promise.all([stopChild(mcp), stopChild(tunnel)]);
    app.exit(0);
  };

  try {
    await host.start();
    const gateway = readJson(paths.hubProxyDescriptorFile(), null);
    writeJsonAtomic(reportFile, {
      role: 'recovery-host',
      hostPid: process.pid,
      hostInstanceId: host.instanceId,
      mcpPid: mcp.pid,
      tunnelPid: tunnel.pid,
      gatewayOwnerPid: Number(gateway?.owner_pid || 0),
      gatewayPort: Number(gateway?.port || 0)
    });
  } catch (error) {
    await Promise.all([stopChild(mcp), stopChild(tunnel)]);
    throw error;
  }

  const shutdownRequest = path.join(dataRoot, 'fixture-shutdown.request');
  const shutdownTimer = setInterval(() => {
    if (fs.existsSync(shutdownRequest)) shutdown();
  }, 100);
  app.on('before-quit', (event) => {
    if (shuttingDown) return;
    event.preventDefault();
    shutdown();
  });
}

async function runClient(paths, reportFile, clientId, exitAfterAttach) {
  const client = new RecoveryIpcClient({ paths });
  const ping = await client.ping();
  const snapshot = await client.lightweightSnapshot();
  const gateway = readJson(paths.hubProxyDescriptorFile(), null);
  const reachable = await gatewayReachable(gateway?.port);
  writeJsonAtomic(reportFile, {
    role: 'electron-client',
    clientId,
    clientPid: process.pid,
    hostPid: Number(ping?.pid || 0),
    hostInstanceId: String(ping?.instance_id || ''),
    mcpPid: Number(snapshot?.mcpPid || 0),
    tunnelPid: Number(snapshot?.tunnelPid || 0),
    supervisionCount: Number(snapshot?.supervisionCount || 0),
    gatewayOwnerPid: Number(gateway?.owner_pid || 0),
    gatewayPort: Number(gateway?.port || 0),
    gatewayReachable: reachable
  });
  if (exitAfterAttach) {
    app.exit(0);
    return;
  }
  setInterval(() => {}, 1000);
}

async function main() {
  const role = argument('--fixture-role');
  const dataRoot = path.resolve(argument('--data-root'));
  const resourcesRoot = path.resolve(argument('--resources-root'));
  const reportFile = path.resolve(argument('--report-file'));
  if (!role || !dataRoot || !resourcesRoot || !reportFile) {
    throw new Error('Recovery process fixture arguments are incomplete.');
  }
  fs.mkdirSync(dataRoot, { recursive: true });
  fs.mkdirSync(resourcesRoot, { recursive: true });
  app.setPath('userData', dataRoot);
  await app.whenReady();
  const paths = createRuntimePaths({ dataRoot, resourcesRoot });
  if (role === 'host') {
    await runHost(paths, dataRoot, reportFile, path.resolve(argument('--node-executable')));
    return;
  }
  if (role === 'client') {
    await runClient(
      paths,
      reportFile,
      argument('--client-id', 'client'),
      process.argv.includes('--exit-after-attach')
    );
    return;
  }
  throw new Error(`Unknown recovery process fixture role: ${role}`);
}

main().catch((error) => {
  const errorFile = argument('--error-file');
  if (errorFile) {
    try {
      writeJsonAtomic(path.resolve(errorFile), {
        code: String(error?.code || 'FIXTURE_FAILED'),
        message: String(error?.message || error).slice(0, 1000)
      });
    } catch { /* parent will report the process exit */ }
  }
  app.exit(1);
});
