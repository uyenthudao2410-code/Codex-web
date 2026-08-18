const { spawn } = require('node:child_process');
const { RecoveryIpcClient, loadRecoveryDescriptor, isProcessAlive } = require('./recoveryIpc');
const { sameInstallationIdentity } = require('./runtimeIdentity');

function wait(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

function assertActivationDeadline(options = {}, boundary = 'before_process_spawn') {
  const expiresAt = Number(options.expiresAtUnixMs || 0);
  if (expiresAt > 0 && Date.now() >= expiresAt) {
    throw Object.assign(new Error('Activation request expired before process launch.'), {
      code: 'ACTIVATION_REQUEST_EXPIRED',
      details: { boundary, process_mutated: false }
    });
  }
}

function recoveryHostArguments(app, options = {}) {
  const args = app.isPackaged
    ? ['--recovery-host']
    : [app.getAppPath(), '--recovery-host'];
  if (options.expectedOldInstanceId && options.operationId) {
    args.push(`--replace-recovery-host=${options.expectedOldInstanceId}`);
    args.push(`--activation-operation=${options.operationId}`);
  }
  return args;
}

function recoveryLoginItemArguments(app) {
  const args = recoveryHostArguments(app);
  if (app.isPackaged || !args.length) return args;
  // Windows stores the argument vector in a registry command string. Keep the
  // development app path intact when the checkout lives under a spaced path.
  return [`"${String(args[0]).replace(/"/g, '\\"')}"`, ...args.slice(1)];
}

async function spawnRecoveryHost(app, spawnProcess = spawn, options = {}) {
  assertActivationDeadline(options);
  const child = spawnProcess(process.execPath, recoveryHostArguments(app, options), {
    detached: true,
    windowsHide: true,
    stdio: 'ignore',
    env: { ...process.env, WEBCODEX_PROCESS_ROLE: 'recovery-host' }
  });
  await new Promise((resolve, reject) => {
    child.once('spawn', resolve);
    child.once('error', reject);
  });
  child.unref();
  return child.pid;
}

function electronUiArguments(app) {
  return app.isPackaged ? [] : [app.getAppPath()];
}

async function spawnElectronUi(app, spawnProcess = spawn, options = {}) {
  assertActivationDeadline(options);
  const child = spawnProcess(process.execPath, electronUiArguments(app), {
    detached: true,
    windowsHide: true,
    stdio: 'ignore',
    env: { ...process.env, WEBCODEX_PROCESS_ROLE: 'electron-ui' }
  });
  await new Promise((resolve, reject) => {
    child.once('spawn', resolve);
    child.once('error', reject);
  });
  child.unref();
  return child.pid;
}

function descriptorIdentity(descriptor) {
  if (!descriptor?.installation_id || !descriptor?.runtime_mode) return null;
  return {
    version: 1,
    mode: descriptor.runtime_mode,
    installation_id: descriptor.installation_id
  };
}

function descriptorMatchesInstallation(descriptor, expectedIdentity) {
  return sameInstallationIdentity(descriptorIdentity(descriptor), expectedIdentity);
}

function installationMismatchError(expectedIdentity, descriptor) {
  return Object.assign(
    new Error('Recovery Host belongs to another application checkout or installation.'),
    {
      code: 'RECOVERY_HOST_INSTALLATION_MISMATCH',
      details: {
        expected_installation_id: expectedIdentity?.installation_id || null,
        observed_installation_id: descriptor?.installation_id || null,
        expected_runtime_mode: expectedIdentity?.mode || null,
        observed_runtime_mode: descriptor?.runtime_mode || null
      }
    }
  );
}

async function waitForProcessExit(pid, {
  processAlive = isProcessAlive,
  sleep = wait,
  timeoutMs = 5000
} = {}) {
  const deadline = Date.now() + Math.max(250, Number(timeoutMs) || 5000);
  while (Date.now() < deadline) {
    if (!processAlive(pid)) return true;
    await sleep(50);
  }
  return !processAlive(pid);
}

async function retireStaleDevelopmentRecoveryHost({
  client,
  paths,
  expectedIdentity,
  descriptor,
  log,
  readDescriptor = loadRecoveryDescriptor,
  terminateProcess = (pid) => process.kill(Number(pid), 'SIGTERM'),
  processAlive = isProcessAlive,
  sleep = wait,
  timeoutMs = 5000
}) {
  if (expectedIdentity?.mode !== 'development') {
    throw installationMismatchError(expectedIdentity, descriptor);
  }
  const ownerPid = Number(descriptor?.owner_pid || 0);
  const instanceId = String(descriptor?.instance_id || '');
  if (!Number.isInteger(ownerPid) || ownerPid <= 0 || !instanceId) {
    throw Object.assign(new Error('Stale development Recovery Host identity is incomplete.'), {
      code: 'RECOVERY_HOST_DEV_HANDOFF_UNVERIFIED'
    });
  }

  log?.warn?.('Development checkout changed; retiring the previous Recovery Host before starting the current checkout', {
    oldInstallationId: descriptor?.installation_id || 'legacy',
    newInstallationId: expectedIdentity.installation_id
  });

  // Starting a development checkout is the authority transition. Stop the old
  // primary runtime first so no Coding MCP/Tunnel process from the previous
  // checkout survives the host takeover. Preserve manual-stop intent.
  await client.stop({ manual: false });

  let verified;
  try {
    verified = readDescriptor(paths);
  } catch (error) {
    if (error?.code === 'RECOVERY_DESCRIPTOR_STALE' || error?.code === 'ENOENT') return { retired: true, alreadyExited: true };
    throw error;
  }

  if (descriptorMatchesInstallation(verified, expectedIdentity)) {
    return { retired: false, alreadyCurrent: true };
  }
  if (Number(verified.owner_pid) !== ownerPid || String(verified.instance_id || '') !== instanceId) {
    throw Object.assign(new Error('Recovery Host owner changed during development checkout handoff.'), {
      code: 'RECOVERY_HOST_DEV_HANDOFF_TARGET_CHANGED'
    });
  }

  terminateProcess(ownerPid);
  const exited = await waitForProcessExit(ownerPid, { processAlive, sleep, timeoutMs });
  if (!exited) {
    throw Object.assign(new Error('Previous development Recovery Host did not exit after runtime shutdown.'), {
      code: 'RECOVERY_HOST_DEV_HANDOFF_TIMEOUT'
    });
  }
  return { retired: true, alreadyExited: false };
}

async function ensureRecoveryHost({
  app,
  paths,
  log,
  timeoutMs = 15_000,
  spawnProcess = spawn,
  clientFactory = (options) => new RecoveryIpcClient(options),
  readDescriptor = loadRecoveryDescriptor,
  terminateProcess = (pid) => process.kill(Number(pid), 'SIGTERM'),
  processAlive = isProcessAlive,
  sleep = wait
}) {
  const client = clientFactory({ paths });
  const expectedIdentity = typeof paths.runtimeIdentity === 'function' ? paths.runtimeIdentity() : null;
  let existingDescriptor = null;
  try {
    existingDescriptor = readDescriptor(paths);
    const status = await client.ping();
    if (status?.ready) {
      if (expectedIdentity && descriptorMatchesInstallation(existingDescriptor, expectedIdentity)) return client;
      if (app.isPackaged || !expectedIdentity) throw installationMismatchError(expectedIdentity, existingDescriptor);
      await retireStaleDevelopmentRecoveryHost({
        client,
        paths,
        expectedIdentity,
        descriptor: existingDescriptor,
        log,
        readDescriptor,
        terminateProcess,
        processAlive,
        sleep,
        timeoutMs: Math.min(5000, Math.max(1000, Number(timeoutMs) || 5000))
      });
    }
  } catch (error) {
    if (String(error?.code || '').startsWith('RECOVERY_HOST_DEV_HANDOFF_')
      || error?.code === 'RECOVERY_HOST_INSTALLATION_MISMATCH') {
      throw error;
    }
    // Missing/stale/unreachable host falls through to a current-checkout spawn.
  }

  await spawnRecoveryHost(app, spawnProcess);
  const deadline = Date.now() + Math.max(1000, Number(timeoutMs) || 15_000);
  let lastError = null;
  while (Date.now() < deadline) {
    try {
      const descriptor = readDescriptor(paths);
      const status = await client.ping();
      if (status?.ready) {
        if (!expectedIdentity || descriptorMatchesInstallation(descriptor, expectedIdentity)) return client;
        lastError = installationMismatchError(expectedIdentity, descriptor);
      }
    } catch (error) {
      lastError = error;
    }
    await sleep(100);
  }
  log?.error?.('Recovery Host không sẵn sàng trong thời gian quy định', { code: lastError?.code || 'RECOVERY_HOST_START_TIMEOUT' });
  throw Object.assign(new Error('Recovery Host không sẵn sàng trong thời gian quy định.'), {
    code: lastError?.code === 'RECOVERY_HOST_INSTALLATION_MISMATCH'
      ? 'RECOVERY_HOST_INSTALLATION_MISMATCH'
      : 'RECOVERY_HOST_START_TIMEOUT',
    cause: lastError
  });
}

module.exports = {
  ensureRecoveryHost,
  spawnRecoveryHost,
  recoveryHostArguments,
  recoveryLoginItemArguments,
  electronUiArguments,
  spawnElectronUi,
  assertActivationDeadline,
  descriptorMatchesInstallation,
  retireStaleDevelopmentRecoveryHost,
  waitForProcessExit,
  installationMismatchError
};
