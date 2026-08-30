const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawn } = require('node:child_process');
const { pythonStatus } = require('./environmentService');
const defaultPaths = require('../paths');
const { readJson, updateJsonAtomic, ensureParent } = require('./jsonStore');
const { rotateLog } = require('./logService');
const { ComponentRevisionTracker } = require('./componentRevision');
const { classifyStoredDeviceOwner } = require('./deviceIdentity');
const { canonicalPath } = require('./runtimeIdentity');
const { CONNECTOR_ATTESTATION_ENV } = require('./connectorAttestation');
const {
  normalizeProcessStartToken,
  observeProcessIdentity,
  observeProcessIdentityAsync,
  processIdentityFrom,
  sameProcessIdentity,
  terminateExactProcessTree
} = require('./processIdentity');

const SECRET_BROKER_ENV = 'CODING_TOOLS_MCP_SECRET_BROKER';
const AUTH_HANDLE_ENV = 'CODING_TOOLS_MCP_AUTH_HANDLE';
const MCP_AUTH_HANDLE = 'secret://mcp/auth';
const OPENAI_API_KEY_HANDLE = 'secret://provider/openai/api-key';
const P5_A0_SEED_ENV = 'CODING_TOOLS_P5_A0_SEED';
const P5_A0_SEED_SECRET = 'p5A0Seed';
const P5_A0_SEED_HANDLE = 'secret://experiment/p5/a';
const CORE_NATIVE_ENV_NAMES = new Set([
  'PATH', 'PATHEXT', 'COMSPEC', 'SYSTEMROOT', 'WINDIR', 'SYSTEMDRIVE',
  'PROGRAMDATA', 'PROGRAMFILES', 'PROGRAMFILES(X86)', 'PROGRAMW6432',
  'COMMONPROGRAMFILES', 'COMMONPROGRAMFILES(X86)', 'COMMONPROGRAMW6432',
  'ALLUSERSPROFILE', 'PUBLIC', 'LOCALAPPDATA', 'APPDATA', 'USERPROFILE',
  'HOMEDRIVE', 'HOMEPATH', 'HOME', 'USER', 'USERNAME', 'TEMP', 'TMP',
  'TMPDIR', 'LANG', 'LC_ALL', 'TERM'
]);

function coreNativeEnvironment(sourceEnv = process.env) {
  const env = {};
  for (const [key, value] of Object.entries(sourceEnv || {})) {
    if (value === undefined || value === null) continue;
    const upper = String(key).toUpperCase();
    if (CORE_NATIVE_ENV_NAMES.has(upper) || upper.startsWith('LC_')) env[upper] = String(value);
  }
  return env;
}

function buildNativeMcpEnv({
  sourceEnv = process.env,
  launch,
  settings,
  token,
  diskRevision,
  supervisorRequestFile,
  device = null,
  p5Seed = '',
  activationEpochId = '',
  activationGate = '',
  activationAllowAcceptancePending = false,
  activationExpiresAtUnixMs = 0,
  connectorAttestationSecret = ''
}) {
  const env = coreNativeEnvironment(sourceEnv);
  const broker = { [MCP_AUTH_HANDLE]: String(token || '') };
  if (String(sourceEnv.OPENAI_API_KEY || '')) broker[OPENAI_API_KEY_HANDLE] = String(sourceEnv.OPENAI_API_KEY);
  // P5-A0 may only reach the child process through a seed explicitly read from
  // the product SecretStore.  The one-shot environment input is consumed and
  // encrypted by mcp_controlled_restart.js before NativeService is invoked;
  // falling back to it here would make a recovery restart silently change the
  // experiment identity.
  const managedP5Seed = String(p5Seed || '');
  if (managedP5Seed) broker[P5_A0_SEED_HANDLE] = managedP5Seed;
  Object.assign(env, {
    CODING_TOOLS_MCP_AUTH_MODE: 'bearer',
    [SECRET_BROKER_ENV]: JSON.stringify(broker),
    [AUTH_HANDLE_ENV]: MCP_AUTH_HANDLE,
    CODING_TOOLS_MCP_TELEMETRY: 'off',
    CODING_TOOLS_MCP_TOOL_MODE: 'smart',
    CODING_TOOLS_MCP_AUTHORIZED_ROOTS: JSON.stringify(settings.authorizedRoots || []),
    CODING_TOOLS_MCP_LONG_TOOL_HANDOFF_SECONDS: String(settings.progressReportSeconds || 90),
    CODING_TOOLS_MCP_SUPERVISOR_REQUEST_FILE: supervisorRequestFile,
    CODING_TOOLS_MCP_CODE_REVISION: diskRevision
  });
  if (String(activationEpochId || '').trim()) env.CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID = String(activationEpochId).trim();
  if (String(connectorAttestationSecret || '').trim()) {
    env[CONNECTOR_ATTESTATION_ENV] = String(connectorAttestationSecret).trim();
  }
  if (String(activationGate || '').trim()) env.CODING_TOOLS_MCP_ACTIVATION_GATE = String(activationGate).trim().toLowerCase();
  if (activationAllowAcceptancePending === true) {
    env.CODING_TOOLS_MCP_ACTIVATION_ALLOW_ACCEPTANCE_PENDING = 'true';
  }
  const activationExpiry = Number(activationExpiresAtUnixMs || 0);
  if (activationExpiry > 0) {
    if (!Number.isSafeInteger(activationExpiry)) {
      throw Object.assign(new Error('Coding MCP activation expiry is invalid.'), {
        code: 'ACTIVATION_EPOCH_EXPIRY_INVALID'
      });
    }
    env.CODING_TOOLS_MCP_ACTIVATION_EXPIRES_AT_UNIX_MS = String(activationExpiry);
  }
  if (device) {
    env.CODING_TOOLS_MCP_DEVICE_ID = device.deviceId;
    env.CODING_TOOLS_MCP_DEVICE_INSTANCE_ID = device.deviceInstanceId;
    env.CODING_TOOLS_MCP_DEVICE_DISPLAY_NAME = device.displayName;
  }
  const bundledTools = path.join(launch.resourcesRoot, 'tools');
  env.PATH = [bundledTools, env.PATH || ''].filter(Boolean).join(path.delimiter);
  env.PYTHONPATH = [launch.moduleRoot, launch.vendoredPython].filter(Boolean).join(path.delimiter);
  return env;
}

function isAlive(pid) {
  if (!Number.isInteger(pid) || pid <= 0) return false;
  try { process.kill(pid, 0); return true; } catch { return false; }
}

function processIdentityError(kind, suffix, message, details = {}) {
  return Object.assign(new Error(message), {
    code: `${String(kind || 'PROCESS')}_PROCESS_IDENTITY_${suffix}`,
    details
  });
}

function storedProcessReceipt(state, pidField, tokenField) {
  const pid = Number(state?.[pidField]);
  return {
    pid: Number.isSafeInteger(pid) && pid > 0 ? pid : null,
    process_start_token: normalizeProcessStartToken(state?.[tokenField])
  };
}

function sameStoredProcessReceipt(state, pidField, tokenField, expected) {
  const actual = storedProcessReceipt(state, pidField, tokenField);
  return actual.pid === (expected?.pid ?? null)
    && actual.process_start_token === (expected?.process_start_token ?? null);
}

function persistenceCleanupFailure(kind, persistenceError, cleanupError) {
  cleanupError.persistenceError = persistenceError;
  cleanupError.details = {
    ...(cleanupError.details || {}),
    persistence_error_code: persistenceError?.code || '',
    persistence_error_message: persistenceError?.message || ''
  };
  if (!cleanupError.code) cleanupError.code = `${kind}_PROCESS_PERSISTENCE_CLEANUP_FAILED`;
  return cleanupError;
}

async function captureSpawnedProcessIdentity(pidValue, {
  processIdentityObserver = observeProcessIdentity,
  sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
  attempts = 5,
  delayMs = 50,
  kind = 'PROCESS'
} = {}) {
  const pid = Number(pidValue);
  if (!Number.isSafeInteger(pid) || pid <= 0) {
    throw processIdentityError(kind, 'UNVERIFIED', 'Spawned process PID is invalid.', { pid: pidValue ?? null });
  }
  let lastObservation = null;
  for (let attempt = 0; attempt < Math.max(1, Number(attempts) || 1); attempt += 1) {
    try { lastObservation = await processIdentityObserver(pid); }
    catch (error) {
      lastObservation = { state: 'unavailable', code: 'PROCESS_IDENTITY_UNVERIFIED', cause_code: error?.code || '' };
    }
    if (lastObservation?.state === 'live') {
      try {
        return processIdentityFrom({ pid, process_start_token: lastObservation.process_start_token });
      } catch { /* retry malformed or unavailable launch observation */ }
    }
    if (lastObservation?.state === 'absent') {
      throw processIdentityError(kind, 'EXITED', 'Spawned process exited before its OS identity was captured.', { pid });
    }
    if (attempt + 1 < Math.max(1, Number(attempts) || 1) && Number(delayMs) > 0) await sleep(Number(delayMs));
  }
  throw processIdentityError(kind, 'UNVERIFIED', 'Spawned process OS identity could not be verified.', {
    pid,
    observed_state: lastObservation?.state || null,
    observed_code: lastObservation?.code || null
  });
}

async function requireExactStoredProcessIdentity({ pid: pidValue, processStartToken }, {
  processIdentityObserver = observeProcessIdentity,
  kind = 'PROCESS'
} = {}) {
  const pid = Number(pidValue);
  if (!Number.isSafeInteger(pid) || pid <= 0 || !isAlive(pid)) return null;
  const token = normalizeProcessStartToken(processStartToken);
  if (!token) {
    throw processIdentityError(kind, 'UNVERIFIED', 'Live process state has no verified OS start token.', { pid });
  }
  let observed;
  try { observed = await processIdentityObserver(pid); }
  catch (error) {
    throw processIdentityError(kind, 'UNVERIFIED', 'Live process OS identity could not be observed.', {
      pid,
      cause_code: error?.code || ''
    });
  }
  if (observed?.state === 'absent') return null;
  if (observed?.state !== 'live') {
    throw processIdentityError(kind, 'UNVERIFIED', 'Live process OS identity could not be verified.', {
      pid,
      observed_state: observed?.state || null,
      observed_code: observed?.code || null
    });
  }
  const identity = processIdentityFrom({ pid, process_start_token: token });
  if (!sameProcessIdentity(identity, observed)) {
    throw processIdentityError(kind, 'CHANGED', 'Stored PID now belongs to a different OS process identity.', {
      pid,
      expected_process_start_token: token,
      observed_process_start_token: normalizeProcessStartToken(observed.process_start_token)
    });
  }
  return identity;
}

function assertActivationDeadline(expiresAtUnixMs, processMutated = false) {
  const expiresAt = Number(expiresAtUnixMs || 0);
  if (expiresAt > 0 && Date.now() >= expiresAt) {
    throw Object.assign(new Error('Activation request expired before Coding MCP process spawn.'), {
      code: 'ACTIVATION_REQUEST_EXPIRED',
      details: { boundary: 'before_native_spawn', process_mutated: processMutated }
    });
  }
}

function runtimeFingerprint(settings) {
  return crypto.createHash('sha256').update(JSON.stringify({
    workspace: path.resolve(String(settings.workspace || '')).toLowerCase(),
    authorizedRoots: (settings.authorizedRoots || []).map((item) => path.resolve(String(item)).toLowerCase()).sort(),
    port: Number(settings.mcpPort),
    permissionMode: settings.permissionMode || 'safe',
    toolMode: 'smart'
  })).digest('hex');
}

// The attestation capability is supplied to the MCP child through its launch
// environment and is intentionally never persisted in plaintext.  A detached
// child cannot be queried for its environment reliably, so keep only a
// one-way digest in the owned runtime receipt.  This lets a subsequent start
// distinguish the exact capability that was used for the live process while
// preserving the existing fail-closed behavior for legacy receipts that have
// no digest.
function connectorAttestationSecretHash(secret) {
  const value = String(secret || '').trim();
  if (!value) return '';
  return crypto.createHash('sha256').update(value, 'utf8').digest('hex');
}

function connectorAttestationSecretMatches(state, secret) {
  const value = String(secret || '').trim();
  // Callers that do not request a managed connector capability retain the
  // historical reuse behavior.  There is no new secret whose binding needs
  // to be established in that case.
  if (!value) return true;
  const observed = String(state?.nativeConnectorAttestationSecretHash || '').trim().toLowerCase();
  if (!/^[0-9a-f]{64}$/.test(observed)) return false;
  const expected = Buffer.from(connectorAttestationSecretHash(value), 'hex');
  const actual = Buffer.from(observed, 'hex');
  return expected.length === actual.length && crypto.timingSafeEqual(actual, expected);
}

function pathKey(value) {
  const normalized = path.normalize(String(value || ''));
  return process.platform === 'win32' ? normalized.toLowerCase() : normalized;
}

function resolveNativeLaunchContract(paths, python) {
  const runtimeMode = typeof paths.runtimeMode === 'function'
    ? String(paths.runtimeMode() || '')
    : 'development';
  if (!['development', 'packaged'].includes(runtimeMode)) {
    throw Object.assign(new Error('Coding MCP runtime mode is invalid.'), { code: 'NATIVE_RUNTIME_MODE_INVALID' });
  }
  const resourcesRoot = canonicalPath(paths.resourcesRoot(), 'resourcesRoot');
  const moduleRoot = canonicalPath(path.join(resourcesRoot, 'coding-tools-mcp'), 'Coding MCP module root');
  const packageMarker = path.join(moduleRoot, 'coding_tools_mcp', '__init__.py');
  if (!fs.existsSync(packageMarker)) {
    throw Object.assign(new Error('Coding MCP source package is missing from the selected runtime resources.'), {
      code: 'NATIVE_MCP_SOURCE_MISSING',
      moduleRoot
    });
  }
  if (runtimeMode === 'development') {
    if (typeof paths.appRoot !== 'function') {
      throw Object.assign(new Error('Development Coding MCP launch authority cannot be verified without appRoot.'), {
        code: 'DEV_MCP_SOURCE_ROOT_UNVERIFIED'
      });
    }
    const expectedModuleRoot = canonicalPath(
      path.join(paths.appRoot(), 'resources', 'coding-tools-mcp'),
      'Development Coding MCP module root'
    );
    if (pathKey(moduleRoot) !== pathKey(expectedModuleRoot)) {
      throw Object.assign(new Error('Development Coding MCP source root does not belong to the current Electron checkout.'), {
        code: 'DEV_MCP_SOURCE_ROOT_MISMATCH',
        moduleRoot,
        expectedModuleRoot
      });
    }
  }
  const command = String(python.launchCommand || python.command || '').trim();
  if (!command) {
    throw Object.assign(new Error('Coding MCP Python launch command is unavailable.'), { code: 'NATIVE_PYTHON_COMMAND_MISSING' });
  }
  return {
    runtimeMode,
    resourcesRoot,
    moduleRoot,
    vendoredPython: path.join(moduleRoot, 'python_vendor'),
    command
  };
}

function currentRuntimeState(input = {}) {
  const allowed = new Set([
    'manualStop', 'tunnelPid', 'tunnelStartedAt', 'tunnelId', 'tunnelFingerprint',
    'tunnelDeviceId', 'tunnelDeviceInstanceId', 'tunnelInstanceId', 'tunnelActivationEpochId', 'tunnelProcessStartToken',
    'nativePid', 'nativeFingerprint', 'nativeWorkspace', 'nativePort',
    'nativePermissionMode', 'nativeToolMode', 'nativeCommand', 'nativeCodeRevision', 'nativeInstanceId', 'nativeActivationEpochId', 'nativeProcessStartToken',
    'nativeActivationExpiresAtUnixMs',
    'nativeConnectorAttestationSecretHash',
    'nativeRuntimeMode', 'nativeModuleRoot',
    'nativeDeviceId', 'nativeDeviceInstanceId', 'startedAt',
    'chatgptToolContractSha256', 'chatgptToolContractAcknowledgedAt', 'chatgptToolContractRediscoveredAt'
  ]);
  return Object.fromEntries(Object.entries(input).filter(([key]) => allowed.has(key)));
}

class NativeService {
  constructor(log, paths = defaultPaths, revisionTracker = null, device = null, options = {}) {
    this.log = log;
    this.paths = paths;
    this.revisions = revisionTracker || new ComponentRevisionTracker({ paths });
    this.device = device;
    this.processIdentityObserver = typeof options.processIdentityObserver === 'function'
      ? options.processIdentityObserver
      : observeProcessIdentity;
    this.asyncProcessIdentityObserver = typeof options.asyncProcessIdentityObserver === 'function'
      ? options.asyncProcessIdentityObserver
      : typeof options.processIdentityObserver === 'function'
        ? options.processIdentityObserver
        : observeProcessIdentityAsync;
    this.exactProcessTerminator = typeof options.exactProcessTerminator === 'function'
      ? options.exactProcessTerminator
      : terminateExactProcessTree;
    this.identitySleep = typeof options.identitySleep === 'function'
      ? options.identitySleep
      : (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  }

  assertOwnedLive(state) {
    if (!this.device || !isAlive(state.nativePid)) return;
    const ownership = classifyStoredDeviceOwner(state.nativeDeviceId, this.device.deviceId);
    if (ownership === 'owned') return;
    const code = ownership === 'foreign' ? 'NATIVE_PROCESS_FOREIGN_DEVICE' : 'NATIVE_PROCESS_OWNER_UNVERIFIED';
    throw Object.assign(new Error(ownership === 'foreign' ? 'Coding MCP process state belongs to another device; refusing to adopt or terminate it.' : 'Coding MCP process state predates device ownership metadata; refusing to adopt or terminate the live process.'), { code, ownerDeviceId: String(state.nativeDeviceId || '') || null, expectedDeviceId: this.device.deviceId });
  }

  async ownedIdentity(state, processIdentityObserver = this.processIdentityObserver) {
    // Establish OS start-token authority before applying device ownership.
    // A live legacy record without a token must surface the typed identity
    // failure and may never be adopted or terminated.
    const identity = await requireExactStoredProcessIdentity({
      pid: state.nativePid,
      processStartToken: state.nativeProcessStartToken
    }, {
      processIdentityObserver,
      kind: 'NATIVE'
    });
    this.assertOwnedLive(state);
    return identity;
  }

  clearOwnedState(expectedReceipt = null) {
    updateJsonAtomic(this.paths.stateFile(), (value) => {
      if (expectedReceipt && !sameStoredProcessReceipt(value, 'nativePid', 'nativeProcessStartToken', expectedReceipt)) {
        throw Object.assign(new Error('Coding MCP process state changed before exact cleanup.'), {
          code: 'NATIVE_PROCESS_STATE_CHANGED'
        });
      }
      return {
        ...value,
        nativePid: null,
        nativeProcessStartToken: null,
        nativeFingerprint: '',
        nativeWorkspace: '',
        nativePort: null,
        nativePermissionMode: '',
        nativeInstanceId: '',
        nativeCodeRevision: '',
        nativeRuntimeMode: '',
        nativeModuleRoot: '',
        nativeDeviceId: '',
        nativeDeviceInstanceId: '',
        nativeActivationEpochId: null,
        nativeActivationExpiresAtUnixMs: null,
        nativeConnectorAttestationSecretHash: ''
      };
    });
  }

  async terminateOwnedIdentity(identity) {
    if (!identity) return false;
    const state = readJson(this.paths.stateFile(), {});
    if (!sameStoredProcessReceipt(state, 'nativePid', 'nativeProcessStartToken', identity)) {
      throw Object.assign(new Error('Coding MCP process state changed before exact termination.'), {
        code: 'NATIVE_PROCESS_STATE_CHANGED'
      });
    }
    await this.exactProcessTerminator(identity, {
      observeProcessIdentity: this.processIdentityObserver
    });
    this.clearOwnedState(identity);
    return true;
  }

  async start(settings, token, progress, options = {}) {
    const python = await pythonStatus(this.paths);
    if (!python.installed) {
      throw new Error('Không tìm thấy Python 3.11+. Gói cài đặt chính thức tích hợp sẵn Python Portable; phiên bản phát triển vui lòng cài đặt Python 3.11+ trước.');
    }
    const launch = resolveNativeLaunchContract(this.paths, python);
    const current = readJson(this.paths.stateFile(), {});
    const fingerprint = runtimeFingerprint(settings);
    const diskRevision = this.revisions.disk('coding_mcp', { force: true }).revision;
    const expectedCodeRevision = String(options.expectedCodeRevision || '');
    if (expectedCodeRevision && diskRevision !== expectedCodeRevision) {
      throw Object.assign(new Error('Coding MCP source revision changed before process start.'), {
        code: 'REVISION_CHANGED',
        expectedRevision: expectedCodeRevision,
        diskRevision
      });
    }
    const currentReceipt = storedProcessReceipt(current, 'nativePid', 'nativeProcessStartToken');
    const currentIdentity = await this.ownedIdentity(current);
    const requestedEpoch = String(options.activationEpochId || '').trim();
    const requestedConnectorAttestationSecret = String(options.connectorAttestationSecret || '').trim();
    const requestedConnectorAttestationSecretHash = connectorAttestationSecretHash(requestedConnectorAttestationSecret);
    const requestedExpiry = Number(options.activationExpiresAtUnixMs || options.expiresAtUnixMs || 0);
    if (requestedExpiry > 0 && !Number.isSafeInteger(requestedExpiry)) {
      throw Object.assign(new Error('Coding MCP activation expiry is invalid.'), {
        code: 'ACTIVATION_EPOCH_EXPIRY_INVALID'
      });
    }
    const launchAuthorityMatches = current.nativeRuntimeMode === launch.runtimeMode
      && pathKey(current.nativeModuleRoot) === pathKey(launch.moduleRoot);
    const epochMatches = !requestedEpoch || String(current.nativeActivationEpochId || '').trim() === requestedEpoch;
    const expiryMatches = !requestedEpoch
      || Number(current.nativeActivationExpiresAtUnixMs || 0) === requestedExpiry;
    const connectorAttestationMatches = connectorAttestationSecretMatches(
      current,
      requestedConnectorAttestationSecret
    );
    if (currentIdentity && current.nativeFingerprint === fingerprint && launchAuthorityMatches && epochMatches && expiryMatches
      && connectorAttestationMatches) {
      // Re-read the receipt immediately before reuse; a concurrent stop or
      // replacement must not turn a stale observation into an owner claim.
      const latest = readJson(this.paths.stateFile(), {});
      let latestIdentity = null;
      try { latestIdentity = await this.ownedIdentity(latest); } catch { latestIdentity = null; }
      if (latestIdentity && sameProcessIdentity(currentIdentity, latestIdentity)
        && latest.nativeFingerprint === fingerprint
        && latest.nativeRuntimeMode === launch.runtimeMode
        && pathKey(latest.nativeModuleRoot) === pathKey(launch.moduleRoot)
        && (!requestedEpoch || String(latest.nativeActivationEpochId || '').trim() === requestedEpoch)
        && (!requestedEpoch || Number(latest.nativeActivationExpiresAtUnixMs || 0) === requestedExpiry)
        && connectorAttestationSecretMatches(latest, requestedConnectorAttestationSecret)) {
        const updatePending = Boolean(latest.nativeCodeRevision && latest.nativeCodeRevision !== diskRevision);
        this.log.info('MCP Portable đã chạy trong thư mục làm việc mục tiêu', { pid: latest.nativePid, workspace: settings.workspace });
        if (updatePending) {
          this.log.info('Coding Tools MCP có source revision mới đang chờ controlled activation', {
            pid: latest.nativePid,
            runningRevision: String(latest.nativeCodeRevision).slice(0, 12),
            diskRevision: diskRevision.slice(0, 12)
          });
        }
        return { reused: true, pid: latest.nativePid, processStartToken: latest.nativeProcessStartToken, codeRevision: latest.nativeCodeRevision || null, updatePending };
      }
    }
    if (currentIdentity && current.nativeFingerprint === fingerprint && (!launchAuthorityMatches || !epochMatches || !expiryMatches)) {
      this.log.warn('Coding MCP đang chạy không có launch authority khớp checkout hiện tại; sẽ tạo lại thay vì reuse', {
        pid: current.nativePid,
        runtimeMode: launch.runtimeMode,
        moduleRoot: launch.moduleRoot,
        requestedActivationEpochId: requestedEpoch || null,
        runningActivationEpochId: String(current.nativeActivationEpochId || '') || null,
        requestedActivationExpiresAtUnixMs: requestedExpiry || null,
        runningActivationExpiresAtUnixMs: Number(current.nativeActivationExpiresAtUnixMs || 0) || null
      });
    }
    if (currentIdentity && current.nativeFingerprint === fingerprint && !connectorAttestationMatches) {
      // Do not expose the secret or its digest in logs.  A missing digest is
      // deliberately treated like a mismatch so a legacy live process is
      // never adopted under a newly supplied capability.
      this.log.warn('Coding MCP đang chạy với connector-attestation capability khác; sẽ tạo lại thay vì reuse', {
        pid: current.nativePid,
        requestedConnectorAttestation: true,
        storedConnectorAttestationDigestPresent: /^[0-9a-f]{64}$/i.test(String(current.nativeConnectorAttestationSecretHash || '').trim())
      });
    }
    if (currentIdentity) {
      this.log.info('Phát hiện cấu hình MCP Portable đã thay đổi, đang âm thầm tạo lại', { from: current.nativeWorkspace || '', to: settings.workspace });
      await this.terminateOwnedIdentity(currentIdentity);
    } else if (current.nativePid || current.nativeProcessStartToken) {
      // The exact stored owner has exited. Clear only the stale receipt; a
      // recycled PID is never adopted or terminated.
      this.clearOwnedState(currentReceipt);
    }

    progress('native-start', 45, `Đang âm thầm khởi động môi trường runtime portable bằng ${python.version}`);
    ensureParent(this.paths.mcpLogFile());
    rotateLog(this.paths.mcpLogFile());
    const output = fs.openSync(this.paths.mcpLogFile(), 'a');
    const env = buildNativeMcpEnv({
      sourceEnv: process.env,
      launch,
      settings,
      token,
      diskRevision,
      supervisorRequestFile: this.paths.supervisorRequestFile(),
      p5Seed: options.p5Seed,
      device: this.device,
      activationEpochId: requestedEpoch,
      activationGate: options.activationGate,
      activationAllowAcceptancePending: options.activationAllowAcceptancePending === true,
      activationExpiresAtUnixMs: requestedExpiry,
      connectorAttestationSecret: options.connectorAttestationSecret || ''
    });
    const args = [
      ...python.prefixArgs,
      '-m', 'coding_tools_mcp',
      '--workspace', settings.workspace,
      '--host', '127.0.0.1',
      '--port', String(settings.mcpPort),
      '--permission-mode', settings.permissionMode
    ];
    const command = launch.command;
    let child;
    let spawnedIdentity;
    try {
      assertActivationDeadline(options.expiresAtUnixMs, options.activationProcessMutated === true);
      child = spawn(command, args, {
        detached: true,
        windowsHide: true,
        stdio: ['ignore', output, output],
        env,
        cwd: launch.moduleRoot
      });
      await new Promise((resolve, reject) => {
        child.once('spawn', resolve);
        child.once('error', reject);
      });
      // The child is detached; release the parent handle even if the OS probe
      // cannot establish a token.  No unverified PID is persisted or killed.
      child.unref();
      spawnedIdentity = await captureSpawnedProcessIdentity(child.pid, {
        processIdentityObserver: this.processIdentityObserver,
        sleep: this.identitySleep,
        kind: 'NATIVE'
      });
    } finally {
      fs.closeSync(output);
    }
    const instanceId = crypto.randomBytes(12).toString('hex');
    try {
      updateJsonAtomic(this.paths.stateFile(), (value) => {
        if (!sameStoredProcessReceipt(value, 'nativePid', 'nativeProcessStartToken', { pid: null, process_start_token: null })) {
          throw Object.assign(new Error('Coding MCP process state changed before launch receipt persistence.'), {
            code: 'NATIVE_PROCESS_STATE_CHANGED'
          });
        }
        return {
          ...currentRuntimeState(value),
          nativePid: child.pid,
          nativeProcessStartToken: spawnedIdentity.process_start_token,
          nativeFingerprint: fingerprint,
          nativeWorkspace: path.resolve(settings.workspace),
          nativePort: Number(settings.mcpPort),
          nativePermissionMode: settings.permissionMode,
          nativeToolMode: 'smart',
          nativeCommand: command,
          nativeCodeRevision: diskRevision,
          nativeRuntimeMode: launch.runtimeMode,
          nativeModuleRoot: launch.moduleRoot,
          nativeConnectorAttestationSecretHash: requestedConnectorAttestationSecretHash,
          nativeDeviceId: this.device?.deviceId || '',
          nativeDeviceInstanceId: this.device?.deviceInstanceId || '',
          startedAt: new Date().toISOString(),
          nativeInstanceId: instanceId,
          nativeActivationEpochId: requestedEpoch || null,
          nativeActivationExpiresAtUnixMs: requestedExpiry || null
        };
      });
    } catch (error) {
      try {
        await this.exactProcessTerminator(spawnedIdentity, {
          observeProcessIdentity: this.processIdentityObserver
        });
      } catch (cleanupError) {
        throw persistenceCleanupFailure('NATIVE', error, cleanupError);
      }
      throw error;
    }
    this.log.info('Môi trường runtime MCP Portable đã khởi động', {
      pid: child.pid,
      workspace: settings.workspace,
      command,
      runtimeMode: launch.runtimeMode,
      moduleRoot: launch.moduleRoot,
      activationEpochId: requestedEpoch || null
    });
    return {
      reused: false,
      pid: child.pid,
      processStartToken: spawnedIdentity.process_start_token,
      instanceId,
      codeRevision: diskRevision,
      updatePending: false,
      runtimeMode: launch.runtimeMode,
      moduleRoot: launch.moduleRoot
    };
  }

  async stop() {
    const state = readJson(this.paths.stateFile(), {});
    const identity = await this.ownedIdentity(state);
    if (!identity) {
      this.clearOwnedState(storedProcessReceipt(state, 'nativePid', 'nativeProcessStartToken'));
      return false;
    }
    return this.terminateOwnedIdentity(identity);
  }

  async markWorkspace(settings) {
    updateJsonAtomic(this.paths.stateFile(), (value) => ({
      ...value,
      nativeFingerprint: runtimeFingerprint(settings),
      nativeWorkspace: path.resolve(settings.workspace),
      nativePort: Number(settings.mcpPort),
      nativePermissionMode: settings.permissionMode,
      nativeToolMode: 'smart'
    }));
    return true;
  }

  async status(settings = null, options = {}) {
    const state = readJson(this.paths.stateFile(), {});
    let identity;
    try { identity = await this.ownedIdentity(state, this.asyncProcessIdentityObserver); } catch { return false; }
    if (!identity) return false;
    if (this.device && classifyStoredDeviceOwner(state.nativeDeviceId, this.device.deviceId) !== 'owned') return false;
    if (settings && state.nativeFingerprint !== runtimeFingerprint(settings)) return false;
    const expectedEpoch = String(options.activationEpochId || '').trim();
    if (expectedEpoch && String(state.nativeActivationEpochId || '').trim() !== expectedEpoch) return false;
    try {
      const latest = await this.ownedIdentity(readJson(this.paths.stateFile(), {}), this.asyncProcessIdentityObserver);
      const exact = Boolean(latest && sameProcessIdentity(identity, latest));
      return options.returnIdentity === true ? (exact ? latest : null) : exact;
    } catch {
      return false;
    }
  }

  revisionStatus(options = {}) {
    const state = readJson(this.paths.stateFile(), {});
    let alive = false;
    if (isAlive(state.nativePid) && normalizeProcessStartToken(state.nativeProcessStartToken)) {
      const expected = {
        pid: state.nativePid,
        process_start_token: state.nativeProcessStartToken
      };
      const verified = options.verifiedProcessIdentity;
      if (verified && sameProcessIdentity(expected, verified)) {
        alive = true;
      } else {
        try {
          const observed = this.processIdentityObserver(state.nativePid);
          alive = !observed?.then && sameProcessIdentity(expected, observed);
        } catch { alive = false; }
      }
    }
    try {
      const status = this.revisions.status('coding_mcp', alive ? state.nativeCodeRevision : null, {
        force: options.force === true
      });
      if (!alive) return { ...status, update_pending: false, state: 'stopped', activation_epoch_id: null };
      status.activation_epoch_id = String(state.nativeActivationEpochId || '') || null;
      return status;
    } catch (error) {
      return {
        running_revision: alive ? String(state.nativeCodeRevision || '') || null : null,
        disk_revision: null,
        update_pending: null,
        state: 'unavailable',
        error_code: String(error?.code || 'REVISION_UNAVAILABLE')
      };
    }
  }
}

module.exports = {
  NativeService,
  isAlive,
  captureSpawnedProcessIdentity,
  requireExactStoredProcessIdentity,
  runtimeFingerprint,
  connectorAttestationSecretHash,
  connectorAttestationSecretMatches,
  currentRuntimeState,
  resolveNativeLaunchContract,
  buildNativeMcpEnv,
  SECRET_BROKER_ENV,
  AUTH_HANDLE_ENV,
  MCP_AUTH_HANDLE,
  OPENAI_API_KEY_HANDLE,
  P5_A0_SEED_ENV,
  P5_A0_SEED_SECRET,
  P5_A0_SEED_HANDLE
};
