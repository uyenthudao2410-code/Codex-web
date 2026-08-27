const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { RecoveryIpcClient, loadRecoveryDescriptor, isProcessAlive } = require('./recoveryIpc');
const { sameInstallationIdentity } = require('./runtimeIdentity');
const {
  normalizeProcessStartToken,
  observeProcessIdentity,
  processIdentityFrom,
  sameProcessIdentity,
  terminateExactProcessTree,
  waitForExactProcessExit
} = require('./processIdentity');

const MAX_SUPERVISOR_MANIFEST_BYTES = 64 * 1024;
const ACTIVATION_EPOCH_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/;
const ACTIVATION_OPERATION_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/;

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

function activationEpochId(options = {}) {
  const value = String(options?.activationEpochId || '').trim();
  if (!value) return '';
  if (!ACTIVATION_EPOCH_ID_PATTERN.test(value)) {
    throw Object.assign(new Error('Activation epoch identity is invalid.'), {
      code: 'INVALID_ACTIVATION_EPOCH_ID'
    });
  }
  return value;
}

function activationOperationId(options = {}) {
  const value = String(options?.operationId || '').trim();
  if (!value) return '';
  if (!ACTIVATION_OPERATION_ID_PATTERN.test(value)) {
    throw Object.assign(new Error('Activation operation identity is invalid.'), {
      code: 'INVALID_ACTIVATION_OPERATION_ID'
    });
  }
  return value;
}

function recoveryBootstrapId(options = {}) {
  const value = String(options?.bootstrapId || options?.recoveryBootstrapId || '').trim();
  if (!value) return '';
  if (!ACTIVATION_OPERATION_ID_PATTERN.test(value)) {
    throw Object.assign(new Error('Recovery Host bootstrap identity is invalid.'), {
      code: 'INVALID_RECOVERY_BOOTSTRAP_ID'
    });
  }
  return value;
}

function executableForLaunch(options = {}) {
  const candidate = String(options?.executablePath || process.execPath || '').trim();
  if (!candidate || !path.isAbsolute(candidate)) {
    throw Object.assign(new Error('A qualified Electron executable path is required for Recovery Host launch.'), {
      code: 'RECOVERY_EXECUTABLE_UNAVAILABLE'
    });
  }
  return candidate;
}

function processEnvironment(role, options = {}) {
  const env = { ...process.env, WEBCODEX_PROCESS_ROLE: role };
  const epoch = activationEpochId(options);
  if (epoch) env.CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID = epoch;
  const bootstrap = recoveryBootstrapId(options);
  if (bootstrap) env.WEBCODEX_RECOVERY_BOOTSTRAP_ID = bootstrap;
  return env;
}

function recoveryHostArguments(app, options = {}) {
  const args = app.isPackaged
    ? ['--recovery-host']
    : [app.getAppPath(), '--recovery-host'];
  const operation = activationOperationId(options);
  if (options.expectedOldInstanceId && operation) {
    args.push(`--replace-recovery-host=${options.expectedOldInstanceId}`);
    args.push(`--activation-operation=${operation}`);
  } else if (options.expectedOldInstanceId || operation) {
    throw Object.assign(new Error('Recovery Host replacement requires both old instance and operation identities.'), {
      code: 'RECOVERY_REPLACEMENT_ARGUMENTS_INVALID'
    });
  }
  const bootstrap = recoveryBootstrapId(options);
  if (bootstrap) args.push(`--recovery-bootstrap=${bootstrap}`);
  const epoch = activationEpochId(options);
  if (epoch) args.push(`--activation-epoch-id=${epoch}`);
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
  const child = spawnProcess(executableForLaunch(options), recoveryHostArguments(app, options), {
    detached: true,
    windowsHide: true,
    stdio: 'ignore',
    env: processEnvironment('recovery-host', options)
  });
  await new Promise((resolve, reject) => {
    child.once('spawn', resolve);
    child.once('error', reject);
  });
  child.unref();
  return child.pid;
}

function electronUiArguments(app, options = {}) {
  const args = app.isPackaged ? [] : [app.getAppPath()];
  const epoch = activationEpochId(options);
  if (epoch) args.push(`--activation-epoch-id=${epoch}`);
  return args;
}

async function spawnElectronUi(app, spawnProcess = spawn, options = {}) {
  assertActivationDeadline(options);
  const child = spawnProcess(executableForLaunch(options), electronUiArguments(app, options), {
    detached: true,
    windowsHide: true,
    stdio: 'ignore',
    env: processEnvironment('electron-ui', options)
  });
  await new Promise((resolve, reject) => {
    child.once('spawn', resolve);
    child.once('error', reject);
  });
  child.unref();
  return child.pid;
}

function suppressDevelopmentRecoverySupervisor({ env = process.env, fsApi = fs, now = () => new Date() } = {}) {
  const localAppData = String(env?.LOCALAPPDATA || '').trim();
  if (!localAppData || !path.isAbsolute(localAppData)) return { suppressed: false, reason: 'local_app_data_unavailable' };
  const installRoot = path.join(localAppData, 'WebMcpRecoverySupervisor');
  const manifestFile = path.join(installRoot, 'manifest.json');
  let manifest;
  try {
    const stat = fsApi.statSync(manifestFile);
    if (!stat.isFile() || stat.size > MAX_SUPERVISOR_MANIFEST_BYTES) return { suppressed: false, reason: 'manifest_invalid' };
    manifest = JSON.parse(fsApi.readFileSync(manifestFile, 'utf8'));
  } catch {
    return { suppressed: false, reason: 'manifest_unavailable' };
  }
  if (manifest?.schema_version !== 1 || String(manifest?.mode || '') !== 'development') {
    return { suppressed: false, reason: 'not_development_supervisor' };
  }
  fsApi.mkdirSync(installRoot, { recursive: true });
  fsApi.writeFileSync(path.join(installRoot, 'stop.request'), now().toISOString(), { encoding: 'ascii', mode: 0o600 });
  return { suppressed: true, reason: 'development_supervisor_disabled' };
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

function descriptorRequestOptions(descriptor) {
  const tokenSupplied = descriptor?.owner_process_start_token !== undefined
    && descriptor?.owner_process_start_token !== null
    && String(descriptor.owner_process_start_token).trim() !== '';
  const processStartToken = normalizeProcessStartToken(descriptor?.owner_process_start_token);
  if (tokenSupplied && !processStartToken) {
    throw Object.assign(new Error('Recovery Host descriptor process identity is invalid.'), {
      code: 'RECOVERY_DESCRIPTOR_INVALID'
    });
  }
  return {
    expectedOwnerPid: Number(descriptor?.owner_pid || 0),
    expectedInstanceId: String(descriptor?.instance_id || ''),
    ...(descriptor?.installation_id ? { expectedInstallationId: String(descriptor.installation_id) } : {}),
    ...(processStartToken ? { expectedOwnerProcessStartToken: processStartToken } : {})
  };
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

function isProcessAuthorityError(error) {
  const code = String(error?.code || '');
  return code === 'RECOVERY_HOST_INSTALLATION_MISMATCH'
    || code === 'RECOVERY_DESCRIPTOR_CHANGED'
    || code === 'RECOVERY_DESCRIPTOR_INVALID'
    || code === 'RECOVERY_PROCESS_IDENTITY_UNVERIFIED'
    || code.startsWith('RECOVERY_HOST_DEV_HANDOFF_')
    || code.startsWith('PROCESS_IDENTITY_')
    || code.startsWith('PROCESS_TERMINATION_');
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

async function readVerifiedReadyHost(client, paths, readDescriptor = loadRecoveryDescriptor, attempts = 2) {
  let lastError = null;
  for (let attempt = 0; attempt < Math.max(1, Number(attempts) || 1); attempt += 1) {
    try {
      const descriptor = readDescriptor(paths);
      const status = await client.ping(descriptorRequestOptions(descriptor));
      const descriptorToken = normalizeProcessStartToken(descriptor?.owner_process_start_token);
      const statusToken = normalizeProcessStartToken(status?.process_start_token);
      if (Number(status?.pid || 0) !== Number(descriptor.owner_pid)
        || String(status?.instance_id || '') !== String(descriptor.instance_id || '')
        || (descriptorToken && statusToken !== descriptorToken)) {
        throw Object.assign(new Error('Recovery Host status identity does not match its authenticated descriptor.'), {
          code: 'RECOVERY_DESCRIPTOR_CHANGED',
          details: {
            expected_owner_pid: Number(descriptor.owner_pid || 0) || null,
            observed_owner_pid: Number(status?.pid || 0) || null,
            expected_instance_id: String(descriptor.instance_id || '') || null,
            observed_instance_id: String(status?.instance_id || '') || null,
            expected_owner_process_start_token: descriptorToken || null,
            observed_owner_process_start_token: statusToken || null
          }
        });
      }
      return status?.ready ? { descriptor, status } : null;
    } catch (error) {
      lastError = error;
      if (error?.code !== 'RECOVERY_DESCRIPTOR_CHANGED') throw error;
    }
  }
  throw lastError || Object.assign(new Error('Recovery Host identity could not be stabilized.'), {
    code: 'RECOVERY_DESCRIPTOR_CHANGED'
  });
}

async function retireStaleDevelopmentRecoveryHost({
  client,
  paths,
  expectedIdentity,
  descriptor,
  log,
  readDescriptor = loadRecoveryDescriptor,
  processIdentityObserver = observeProcessIdentity,
  terminateProcess = null,
  waitForExactExit = waitForExactProcessExit,
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
  let baselineObservation;
  try { baselineObservation = await processIdentityObserver(ownerPid); }
  catch (error) {
    throw Object.assign(new Error('Stale development Recovery Host process identity is unavailable.'), {
      code: 'RECOVERY_HOST_DEV_HANDOFF_PROCESS_IDENTITY_UNVERIFIED',
      cause: error
    });
  }
  if (String(baselineObservation?.state || '') !== 'live') {
    throw Object.assign(new Error('Stale development Recovery Host process identity is unavailable.'), {
      code: baselineObservation?.state === 'absent'
        ? 'RECOVERY_HOST_DEV_HANDOFF_TARGET_EXITED'
        : 'RECOVERY_HOST_DEV_HANDOFF_PROCESS_IDENTITY_UNVERIFIED'
    });
  }
  let ownerIdentity;
  try {
    ownerIdentity = processIdentityFrom({
      pid: ownerPid,
      process_start_token: baselineObservation.process_start_token
    });
  } catch (error) {
    throw Object.assign(new Error('Stale development Recovery Host process identity is unavailable.'), {
      code: 'RECOVERY_HOST_DEV_HANDOFF_PROCESS_IDENTITY_UNVERIFIED',
      cause: error
    });
  }
  const descriptorToken = normalizeProcessStartToken(descriptor?.owner_process_start_token);
  const descriptorTokenSupplied = descriptor?.owner_process_start_token !== undefined
    && descriptor?.owner_process_start_token !== null
    && String(descriptor.owner_process_start_token).trim() !== '';
  if (descriptorTokenSupplied && !descriptorToken) {
    throw Object.assign(new Error('Stale development Recovery Host process identity is invalid.'), {
      code: 'RECOVERY_HOST_DEV_HANDOFF_PROCESS_IDENTITY_UNVERIFIED'
    });
  }
  if (descriptorToken && descriptorToken !== ownerIdentity.process_start_token) {
    throw Object.assign(new Error('Recovery Host owner changed before development checkout handoff.'), {
      code: 'RECOVERY_HOST_DEV_HANDOFF_TARGET_CHANGED'
    });
  }

  log?.warn?.('Development checkout changed; retiring the previous Recovery Host before starting the current checkout', {
    oldInstallationId: descriptor?.installation_id || 'legacy',
    newInstallationId: expectedIdentity.installation_id
  });

  // Starting a development checkout is the authority transition. Bind the
  // mutation to the host identity that was already authenticated by ping so a
  // descriptor race cannot stop a replacement process.
  await client.stop({ manual: false }, descriptorRequestOptions(descriptor));

  let verified = null;
  try {
    verified = readDescriptor(paths);
  } catch (error) {
    if (error?.code !== 'RECOVERY_DESCRIPTOR_STALE' && error?.code !== 'ENOENT') throw error;
  }

  if (verified && descriptorMatchesInstallation(verified, expectedIdentity)) {
    return { retired: false, alreadyCurrent: true };
  }
  if (verified && (Number(verified.owner_pid) !== ownerPid || String(verified.instance_id || '') !== instanceId)) {
    throw Object.assign(new Error('Recovery Host owner changed during development checkout handoff.'), {
      code: 'RECOVERY_HOST_DEV_HANDOFF_TARGET_CHANGED'
    });
  }
  const verifiedToken = normalizeProcessStartToken(verified?.owner_process_start_token);
  if (verifiedToken && verifiedToken !== ownerIdentity.process_start_token) {
    throw Object.assign(new Error('Recovery Host owner changed during development checkout handoff.'), {
      code: 'RECOVERY_HOST_DEV_HANDOFF_TARGET_CHANGED'
    });
  }

  let afterStop;
  try { afterStop = await processIdentityObserver(ownerPid); }
  catch (error) {
    throw Object.assign(new Error('Recovery Host process identity became unavailable during development checkout handoff.'), {
      code: 'RECOVERY_HOST_DEV_HANDOFF_PROCESS_IDENTITY_UNVERIFIED',
      cause: error
    });
  }
  if (afterStop?.state === 'absent') return { retired: true, alreadyExited: true };
  if (afterStop?.state !== 'live') {
    throw Object.assign(new Error('Recovery Host process identity became unavailable during development checkout handoff.'), {
      code: 'RECOVERY_HOST_DEV_HANDOFF_PROCESS_IDENTITY_UNVERIFIED'
    });
  }
  if (!sameProcessIdentity(ownerIdentity, afterStop)) {
    return { retired: true, alreadyExited: true, replaced: true };
  }

  const exactTerminator = typeof terminateProcess === 'function'
    ? terminateProcess
    : (identity) => terminateExactProcessTree(identity, { observeProcessIdentity: processIdentityObserver, sleep, timeoutMs });
  await exactTerminator(ownerIdentity);
  try {
    await waitForExactExit(ownerIdentity, {
      observeProcessIdentity: processIdentityObserver,
      sleep,
      timeoutMs
    });
  } catch (error) {
    if (error?.code === 'PROCESS_TERMINATION_TIMEOUT') {
      throw Object.assign(new Error('Previous development Recovery Host did not exit after runtime shutdown.'), {
        code: 'RECOVERY_HOST_DEV_HANDOFF_TIMEOUT',
        cause: error
      });
    }
    throw error;
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
  processIdentityObserver = observeProcessIdentity,
  terminateProcess = null,
  waitForExactExit = waitForExactProcessExit,
  processAlive = isProcessAlive,
  sleep = wait,
  suppressDevelopmentSupervisor = suppressDevelopmentRecoverySupervisor
}) {
  if (!app.isPackaged) {
    const supervisor = suppressDevelopmentSupervisor();
    if (supervisor?.suppressed) {
      log?.warn?.('Disabled a persisted development Recovery Supervisor so it cannot resurrect another checkout.');
    }
  }

  const client = clientFactory({ paths });
  const expectedIdentity = typeof paths.runtimeIdentity === 'function' ? paths.runtimeIdentity() : null;
  try {
    const existing = await readVerifiedReadyHost(client, paths, readDescriptor, 2);
    if (existing?.status?.ready) {
      if (expectedIdentity && descriptorMatchesInstallation(existing.descriptor, expectedIdentity)) return client;
      if (app.isPackaged || !expectedIdentity) throw installationMismatchError(expectedIdentity, existing.descriptor);
      await retireStaleDevelopmentRecoveryHost({
        client,
        paths,
        expectedIdentity,
        descriptor: existing.descriptor,
        log,
        readDescriptor,
        processIdentityObserver,
        terminateProcess,
        waitForExactExit,
        sleep,
        timeoutMs: Math.min(5000, Math.max(1000, Number(timeoutMs) || 5000))
      });
    }
  } catch (error) {
    if (isProcessAuthorityError(error)) throw error;
    // Missing/stale/unreachable host falls through to a current-checkout spawn.
  }

  await spawnRecoveryHost(app, spawnProcess);
  const deadline = Date.now() + Math.max(1000, Number(timeoutMs) || 15_000);
  let lastError = null;
  while (Date.now() < deadline) {
    try {
      const ready = await readVerifiedReadyHost(client, paths, readDescriptor, 2);
      if (ready?.status?.ready) {
        if (!expectedIdentity || descriptorMatchesInstallation(ready.descriptor, expectedIdentity)) return client;
        lastError = installationMismatchError(expectedIdentity, ready.descriptor);
      }
    } catch (error) {
      if (isProcessAuthorityError(error)) throw error;
      lastError = error;
    }
    await sleep(100);
  }
  log?.error?.('Recovery Host không sẵn sàng trong thời gian quy định', { code: lastError?.code || 'RECOVERY_HOST_START_TIMEOUT' });
  throw Object.assign(new Error('Recovery Host không sẵn sàng trong thời gian quy định.'), {
    code: ['RECOVERY_HOST_INSTALLATION_MISMATCH', 'RECOVERY_DESCRIPTOR_CHANGED'].includes(lastError?.code)
      ? lastError.code
      : 'RECOVERY_HOST_START_TIMEOUT',
    cause: lastError
  });
}

module.exports = {
  ensureRecoveryHost,
  spawnRecoveryHost,
  recoveryHostArguments,
  activationOperationId,
  recoveryBootstrapId,
  executableForLaunch,
  recoveryLoginItemArguments,
  electronUiArguments,
  spawnElectronUi,
  assertActivationDeadline,
  suppressDevelopmentRecoverySupervisor,
  descriptorMatchesInstallation,
  descriptorRequestOptions,
  readVerifiedReadyHost,
  retireStaleDevelopmentRecoveryHost,
  waitForProcessExit,
  installationMismatchError,
  MAX_SUPERVISOR_MANIFEST_BYTES
};
