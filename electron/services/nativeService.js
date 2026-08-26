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

function buildNativeMcpEnv({ sourceEnv = process.env, launch, settings, token, diskRevision, supervisorRequestFile, device = null, p5Seed = '', activationEpochId = '', activationGate = '' }) {
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
  if (String(activationGate || '').trim()) env.CODING_TOOLS_MCP_ACTIVATION_GATE = String(activationGate).trim().toLowerCase();
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
    'tunnelDeviceId', 'tunnelDeviceInstanceId', 'tunnelInstanceId', 'tunnelActivationEpochId',
    'nativePid', 'nativeFingerprint', 'nativeWorkspace', 'nativePort',
    'nativePermissionMode', 'nativeToolMode', 'nativeCommand', 'nativeCodeRevision', 'nativeInstanceId', 'nativeActivationEpochId',
    'nativeRuntimeMode', 'nativeModuleRoot',
    'nativeDeviceId', 'nativeDeviceInstanceId', 'startedAt',
    'chatgptToolContractSha256', 'chatgptToolContractAcknowledgedAt', 'chatgptToolContractRediscoveredAt'
  ]);
  return Object.fromEntries(Object.entries(input).filter(([key]) => allowed.has(key)));
}

class NativeService {
  constructor(log, paths = defaultPaths, revisionTracker = null, device = null) {
    this.log = log;
    this.paths = paths;
    this.revisions = revisionTracker || new ComponentRevisionTracker({ paths });
    this.device = device;
  }

  assertOwnedLive(state) {
    if (!this.device || !isAlive(state.nativePid)) return;
    const ownership = classifyStoredDeviceOwner(state.nativeDeviceId, this.device.deviceId);
    if (ownership === 'owned') return;
    const code = ownership === 'foreign' ? 'NATIVE_PROCESS_FOREIGN_DEVICE' : 'NATIVE_PROCESS_OWNER_UNVERIFIED';
    throw Object.assign(new Error(ownership === 'foreign' ? 'Coding MCP process state belongs to another device; refusing to adopt or terminate it.' : 'Coding MCP process state predates device ownership metadata; refusing to adopt or terminate the live process.'), { code, ownerDeviceId: String(state.nativeDeviceId || '') || null, expectedDeviceId: this.device.deviceId });
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
    this.assertOwnedLive(current);
    const requestedEpoch = String(options.activationEpochId || '').trim();
    const launchAuthorityMatches = current.nativeRuntimeMode === launch.runtimeMode
      && pathKey(current.nativeModuleRoot) === pathKey(launch.moduleRoot);
    const epochMatches = !requestedEpoch || String(current.nativeActivationEpochId || '').trim() === requestedEpoch;
    if (isAlive(current.nativePid) && current.nativeFingerprint === fingerprint && launchAuthorityMatches && epochMatches) {
      const updatePending = Boolean(current.nativeCodeRevision && current.nativeCodeRevision !== diskRevision);
      this.log.info('MCP Portable đã chạy trong thư mục làm việc mục tiêu', { pid: current.nativePid, workspace: settings.workspace });
      if (updatePending) {
        this.log.info('Coding Tools MCP có source revision mới đang chờ controlled activation', {
          pid: current.nativePid,
          runningRevision: String(current.nativeCodeRevision).slice(0, 12),
          diskRevision: diskRevision.slice(0, 12)
        });
      }
      return { reused: true, pid: current.nativePid, codeRevision: current.nativeCodeRevision || null, updatePending };
    }
    if (isAlive(current.nativePid) && current.nativeFingerprint === fingerprint && (!launchAuthorityMatches || !epochMatches)) {
      this.log.warn('Coding MCP đang chạy không có launch authority khớp checkout hiện tại; sẽ tạo lại thay vì reuse', {
        pid: current.nativePid,
        runtimeMode: launch.runtimeMode,
        moduleRoot: launch.moduleRoot,
        requestedActivationEpochId: requestedEpoch || null,
        runningActivationEpochId: String(current.nativeActivationEpochId || '') || null
      });
    }
    if (isAlive(current.nativePid)) {
      this.log.info('Phát hiện cấu hình MCP Portable đã thay đổi, đang âm thầm tạo lại', { from: current.nativeWorkspace || '', to: settings.workspace });
      await this.stop();
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
      activationGate: options.activationGate
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
      child.unref();
    } finally {
      fs.closeSync(output);
    }
    const instanceId = crypto.randomBytes(12).toString('hex');
    updateJsonAtomic(this.paths.stateFile(), (value) => ({
      ...currentRuntimeState(value),
      nativePid: child.pid,
      nativeFingerprint: fingerprint,
      nativeWorkspace: path.resolve(settings.workspace),
      nativePort: Number(settings.mcpPort),
      nativePermissionMode: settings.permissionMode,
      nativeToolMode: 'smart',
      nativeCommand: command,
      nativeCodeRevision: diskRevision,
      nativeRuntimeMode: launch.runtimeMode,
      nativeModuleRoot: launch.moduleRoot,
      nativeDeviceId: this.device?.deviceId || '',
      nativeDeviceInstanceId: this.device?.deviceInstanceId || '',
      startedAt: new Date().toISOString(),
      nativeInstanceId: instanceId,
      nativeActivationEpochId: requestedEpoch || null
    }));
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
      instanceId,
      codeRevision: diskRevision,
      updatePending: false,
      runtimeMode: launch.runtimeMode,
      moduleRoot: launch.moduleRoot
    };
  }

  async stop() {
    const state = readJson(this.paths.stateFile(), {});
    const alive = isAlive(state.nativePid);
    this.assertOwnedLive(state);
    try {
      if (alive) {
        const { run } = require('./commandRunner');
        await run('taskkill.exe', ['/PID', String(state.nativePid), '/T', '/F'], { allowFailure: true });
      }
      return alive;
    } finally {
      updateJsonAtomic(this.paths.stateFile(), (value) => ({
        ...value,
        nativePid: null,
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
        nativeActivationEpochId: null
      }));
    }
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
    if (!isAlive(state.nativePid)) return false;
    if (this.device && classifyStoredDeviceOwner(state.nativeDeviceId, this.device.deviceId) !== 'owned') return false;
    if (settings && state.nativeFingerprint !== runtimeFingerprint(settings)) return false;
    const expectedEpoch = String(options.activationEpochId || '').trim();
    return !expectedEpoch || String(state.nativeActivationEpochId || '').trim() === expectedEpoch;
  }

  revisionStatus(options = {}) {
    const state = readJson(this.paths.stateFile(), {});
    const alive = isAlive(state.nativePid);
    try {
      const status = this.revisions.status('coding_mcp', alive ? state.nativeCodeRevision : null, options);
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
  runtimeFingerprint,
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
