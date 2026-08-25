const fs = require('node:fs');
const net = require('node:net');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { app } = require('electron');
const { createRuntimePaths } = require('../../electron/services/runtimePaths');
const { RecoveryHost } = require('../../electron/services/recoveryHost');
const { RecoveryIpcClient } = require('../../electron/services/recoveryIpc');
const { readJson, writeJsonAtomic } = require('../../electron/services/jsonStore');

const OLD_REVISION = 'a'.repeat(64);
const NEXT_REVISION = 'b'.repeat(64);

function activationLifecycle(operationId, sourceCheckpoint, fenced) {
  return {
    safe: true,
    code: 'READY',
    reason: 'idle',
    operation_id: operationId,
    counts: {
      active_tool_calls: 0,
      active_commands: 0,
      starting_commands: 0,
      active_background_operations: 0,
      active_managed_processes: 0,
      foreign_heavy_processes: 0,
      active_agent_lanes: 0,
      threshold_sensitive_stale_candidates: 0,
      owned_codex_sidecar_residues: 0
    },
    lifecycle: {
      snapshot: {
        backup_api_copy: true,
        immutable: true,
        query_only: true,
        integrity_check: ['ok'],
        foreign_key_check_rows: 0,
        sha256: 'c'.repeat(64),
        logical_sha256: 'd'.repeat(64)
      },
      unexplained_active_runs: 0,
      unbound_live_resource_residues: 0
    },
    source_checkpoint: { ok: true, code: 'ACTIVATABLE', ...sourceCheckpoint },
    fenced: fenced === true,
    fence_operation_id: fenced === true ? operationId : null
  };
}

function argument(name, fallback = '') {
  const index = process.argv.indexOf(name);
  return index >= 0 && index + 1 < process.argv.length ? process.argv[index + 1] : fallback;
}

function processAlive(pid) {
  try { process.kill(Number(pid), 0); return true; } catch { return false; }
}

function revisionStatus(runningRevision, diskRevision) {
  const running = String(runningRevision || '') || null;
  const disk = String(diskRevision || '') || null;
  return {
    running_revision: running,
    disk_revision: disk,
    update_pending: running && disk ? running !== disk : null,
    state: running && disk ? (running === disk ? 'current' : 'update_pending') : 'unknown'
  };
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

async function runHost(paths, dataRoot, reportFile, errorFile, nodeExecutable) {
  const activationMode = argument('--activation-mode', 'none');
  const externalMcpPid = Number(argument('--mcp-pid', '0'));
  const externalTunnelPid = Number(argument('--tunnel-pid', '0'));
  const useExternalRuntime = activationMode === 'recovery-host'
    && processAlive(externalMcpPid)
    && processAlive(externalTunnelPid);
  let mcp;
  let tunnel;
  if (useExternalRuntime) {
    mcp = { pid: externalMcpPid };
    tunnel = { pid: externalTunnelPid };
  } else {
    [mcp, tunnel] = await Promise.all([
      spawnStandIn(nodeExecutable, 'coding-mcp'),
      spawnStandIn(nodeExecutable, 'coding-tunnel')
    ]);
  }
  let codingMcpRevision = activationMode === 'coding-mcp' ? OLD_REVISION : NEXT_REVISION;
  const hostRunningRevision = argument(
    '--host-running-revision',
    activationMode === 'recovery-host' ? OLD_REVISION : NEXT_REVISION
  );
  const replacementOldInstanceId = argument('--replace-old-instance');
  const replacementOperationId = argument('--activation-operation');
  const replacement = replacementOldInstanceId && replacementOperationId
    ? { expectedOldInstanceId: replacementOldInstanceId, operationId: replacementOperationId }
    : null;
  const replacementReportFile = argument('--replacement-report-file');
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
    acknowledgeConnectorContract: async () => projection(),
    codingMcpRevisionStatus: () => revisionStatus(
      codingMcpRevision,
      activationMode === 'coding-mcp' ? NEXT_REVISION : codingMcpRevision
    ),
    inspectCodeActivation: async () => ({ safe: true, code: 'READY', workspace: dataRoot }),
    prepareCodeActivation: async ({ operationId, sourceCheckpoint }) => ({
      ...activationLifecycle(operationId, sourceCheckpoint, true)
    }),
    verifyCodeActivation: async (operationId, sourceCheckpoint) => ({
      ...activationLifecycle(operationId, sourceCheckpoint, false),
      workspace: dataRoot
    }),
    cancelCodeActivation: async () => true,
    activateCodingMcpUpdate: async (expectedRevision, options = {}) => {
      if (activationMode !== 'coding-mcp') {
        throw Object.assign(new Error('Coding MCP fixture activation is not enabled.'), { code: 'FIXTURE_ACTIVATION_DISABLED' });
      }
      if (expectedRevision !== NEXT_REVISION) {
        throw Object.assign(new Error('Unexpected fixture revision.'), { code: 'REVISION_CHANGED' });
      }
      const expiresAt = Number(options.expiresAtUnixMs || 0);
      if (expiresAt > 0 && Date.now() >= expiresAt) {
        throw Object.assign(new Error('Fixture activation expired before stop.'), { code: 'ACTIVATION_REQUEST_EXPIRED' });
      }
      const previous = mcp;
      const oldPid = previous.pid;
      await stopChild(previous);
      if (expiresAt > 0 && Date.now() >= expiresAt) {
        throw Object.assign(new Error('Fixture activation expired after stop.'), {
          code: 'ACTIVATION_REQUEST_EXPIRED',
          details: { process_mutated: true }
        });
      }
      mcp = await spawnStandIn(nodeExecutable, 'coding-mcp-replacement');
      codingMcpRevision = NEXT_REVISION;
      return {
        old_instance_id: `mcp-process-${oldPid}`,
        new_instance_id: `mcp-process-${mcp.pid}`,
        old_server_instance_id: `mcp-server-${oldPid}`,
        new_server_instance_id: `mcp-server-${mcp.pid}`,
        old_revision: OLD_REVISION,
        new_revision: NEXT_REVISION,
        health_verified: true,
        disk_revision_verified: true,
        tunnel_preserved: true
      };
    }
  };
  const settings = {
    load: () => ({ autoStartServices: false, mcpPort: 65534 })
  };
  const secrets = { get: () => 'fixture-token' };
  const log = { info() {}, warn() {}, error() {}, read: () => [], clear() {} };
  const revisionTracker = {
    captureRunning: (component) => component === 'recovery_host' ? hostRunningRevision : null,
    status: (component, supplied) => {
      if (component === 'recovery_host') {
        const diskRevision = activationMode === 'recovery-host' ? NEXT_REVISION : hostRunningRevision;
        return revisionStatus(supplied || hostRunningRevision, diskRevision);
      }
      return revisionStatus(supplied || null, NEXT_REVISION);
    }
  };
  const spawnReplacement = async (options) => {
    if (!replacementReportFile) {
      throw Object.assign(new Error('Replacement report path is missing.'), { code: 'FIXTURE_REPLACEMENT_UNAVAILABLE' });
    }
    const expiresAt = Number(options?.expiresAtUnixMs || 0);
    if (expiresAt > 0 && Date.now() >= expiresAt) {
      throw Object.assign(new Error('Fixture replacement activation expired before spawn.'), { code: 'ACTIVATION_REQUEST_EXPIRED' });
    }
    const args = [
      __filename,
      '--disable-gpu',
      '--fixture-role', 'host',
      '--data-root', dataRoot,
      '--resources-root', paths.resourcesRoot(),
      '--report-file', replacementReportFile,
      '--error-file', errorFile,
      '--node-executable', nodeExecutable,
      '--activation-mode', 'recovery-host',
      '--mcp-pid', String(mcp.pid),
      '--tunnel-pid', String(tunnel.pid),
      '--host-running-revision', NEXT_REVISION,
      '--replace-old-instance', String(options.expectedOldInstanceId),
      '--activation-operation', String(options.operationId)
    ];
    const env = { ...process.env, ELECTRON_DISABLE_SECURITY_WARNINGS: '1' };
    delete env.ELECTRON_RUN_AS_NODE;
    const child = spawn(process.execPath, args, {
      cwd: path.resolve(__dirname, '..', '..'),
      detached: true,
      windowsHide: true,
      stdio: 'ignore',
      env
    });
    await new Promise((resolve, reject) => {
      child.once('spawn', resolve);
      child.once('error', reject);
    });
    child.unref();
    return child.pid;
  };
  const host = new RecoveryHost({
    paths,
    settings,
    secrets,
    environment: {},
    log,
    orchestrator,
    healthService: { inspect: async () => projection(), repair: async () => projection() },
    revisionTracker,
    replacement,
    spawnRecoveryReplacement: activationMode === 'recovery-host' && !replacement ? spawnReplacement : null,
    exitProcess: (code) => app.exit(code)
  });
  let shuttingDown = false;
  const shutdown = async () => {
    if (shuttingDown) return;
    shuttingDown = true;
    clearInterval(shutdownTimer);
    await host.stop().catch(() => false);
    if (!useExternalRuntime) await Promise.all([stopChild(mcp), stopChild(tunnel)]);
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
      gatewayPort: Number(gateway?.port || 0),
      activationMode,
      hostRunningRevision
    });
  } catch (error) {
    if (!useExternalRuntime) await Promise.all([stopChild(mcp), stopChild(tunnel)]);
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
  const errorFile = path.resolve(argument('--error-file'));
  if (!role || !dataRoot || !resourcesRoot || !reportFile || !errorFile) {
    throw new Error('Recovery process fixture arguments are incomplete.');
  }
  fs.mkdirSync(dataRoot, { recursive: true });
  fs.mkdirSync(resourcesRoot, { recursive: true });
  app.setPath('userData', dataRoot);
  await app.whenReady();
  const paths = createRuntimePaths({ dataRoot, resourcesRoot });
  if (role === 'host') {
    await runHost(paths, dataRoot, reportFile, errorFile, path.resolve(argument('--node-executable')));
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
