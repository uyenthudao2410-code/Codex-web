const { spawn } = require('node:child_process');
const { RecoveryIpcClient } = require('./recoveryIpc');

function wait(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

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

async function spawnElectronUi(app, spawnProcess = spawn) {
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

async function ensureRecoveryHost({ app, paths, log, timeoutMs = 15_000, spawnProcess = spawn }) {
  const client = new RecoveryIpcClient({ paths });
  try {
    const status = await client.ping();
    if (status?.ready) return client;
  } catch { /* start below */ }

  await spawnRecoveryHost(app, spawnProcess);
  const deadline = Date.now() + Math.max(1000, Number(timeoutMs) || 15_000);
  let lastError = null;
  while (Date.now() < deadline) {
    try {
      const status = await client.ping();
      if (status?.ready) return client;
    } catch (error) {
      lastError = error;
    }
    await wait(100);
  }
  log?.error?.('Recovery Host không sẵn sàng trong thời gian quy định', { code: lastError?.code || 'RECOVERY_HOST_START_TIMEOUT' });
  throw Object.assign(new Error('Recovery Host không sẵn sàng trong thời gian quy định.'), {
    code: 'RECOVERY_HOST_START_TIMEOUT',
    cause: lastError
  });
}

module.exports = {
  ensureRecoveryHost,
  spawnRecoveryHost,
  recoveryHostArguments,
  recoveryLoginItemArguments,
  electronUiArguments,
  spawnElectronUi
};
