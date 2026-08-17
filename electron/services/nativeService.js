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

function isAlive(pid) {
  if (!Number.isInteger(pid)) return false;
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

function currentRuntimeState(input = {}) {
  const allowed = new Set([
    'manualStop', 'tunnelPid', 'tunnelStartedAt', 'tunnelId', 'tunnelFingerprint',
    'tunnelDeviceId', 'tunnelDeviceInstanceId',
    'nativePid', 'nativeFingerprint', 'nativeWorkspace', 'nativePort',
    'nativePermissionMode', 'nativeToolMode', 'nativeCommand', 'nativeCodeRevision', 'nativeInstanceId',
    'nativeDeviceId', 'nativeDeviceInstanceId', 'startedAt',
    'chatgptToolContractSha256', 'chatgptToolContractAcknowledgedAt'
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
    if (isAlive(current.nativePid) && current.nativeFingerprint === fingerprint) {
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
    if (isAlive(current.nativePid)) {
      this.log.info('Phát hiện cấu hình MCP Portable đã thay đổi, đang âm thầm tạo lại', { from: current.nativeWorkspace || '', to: settings.workspace });
      await this.stop();
    }

    progress('native-start', 45, `Đang âm thầm khởi động môi trường runtime portable bằng ${python.version}`);
    ensureParent(this.paths.mcpLogFile());
    rotateLog(this.paths.mcpLogFile());
    const output = fs.openSync(this.paths.mcpLogFile(), 'a');
    const env = {
      ...process.env,
      CODING_TOOLS_MCP_AUTH_MODE: 'bearer',
      CODING_TOOLS_MCP_AUTH_TOKEN: token,
      CODING_TOOLS_MCP_TELEMETRY: 'off',
      CODING_TOOLS_MCP_TOOL_MODE: 'smart',
      CODING_TOOLS_MCP_AUTHORIZED_ROOTS: JSON.stringify(settings.authorizedRoots || []),
      CODING_TOOLS_MCP_LONG_TOOL_HANDOFF_SECONDS: String(settings.progressReportSeconds || 90),
      CODING_TOOLS_MCP_SUPERVISOR_REQUEST_FILE: this.paths.supervisorRequestFile(),
      CODING_TOOLS_MCP_CODE_REVISION: diskRevision
    };
    if (this.device) {
      env.CODING_TOOLS_MCP_DEVICE_ID = this.device.deviceId;
      env.CODING_TOOLS_MCP_DEVICE_INSTANCE_ID = this.device.deviceInstanceId;
      env.CODING_TOOLS_MCP_DEVICE_DISPLAY_NAME = this.device.displayName;
    }
    const bundledTools = path.join(this.paths.resourcesRoot(), 'tools');
    const vendoredPython = path.join(this.paths.resourcesRoot(), 'coding-tools-mcp', 'python_vendor');
    env.PATH = [bundledTools, process.env.PATH || ''].filter(Boolean).join(path.delimiter);
    env.PYTHONPATH = [vendoredPython, path.join(this.paths.resourcesRoot(), 'coding-tools-mcp'), process.env.PYTHONPATH || ''].filter(Boolean).join(path.delimiter);
    const args = [
      ...python.prefixArgs,
      '-m', 'coding_tools_mcp',
      '--workspace', settings.workspace,
      '--host', '127.0.0.1',
      '--port', String(settings.mcpPort),
      '--permission-mode', settings.permissionMode
    ];
    const command = python.launchCommand || python.command;
    let child;
    try {
      assertActivationDeadline(options.expiresAtUnixMs, options.activationProcessMutated === true);
      child = spawn(command, args, {
        detached: true,
        windowsHide: true,
        stdio: ['ignore', output, output],
        env
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
      nativeDeviceId: this.device?.deviceId || '',
      nativeDeviceInstanceId: this.device?.deviceInstanceId || '',
      startedAt: new Date().toISOString(),
      nativeInstanceId: instanceId
    }));
    this.log.info('Môi trường runtime MCP Portable đã khởi động', { pid: child.pid, workspace: settings.workspace, command });
    return { reused: false, pid: child.pid, instanceId, codeRevision: diskRevision, updatePending: false };
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
        nativeDeviceId: '',
        nativeDeviceInstanceId: ''
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

  async status(settings = null) {
    const state = readJson(this.paths.stateFile(), {});
    if (!isAlive(state.nativePid)) return false;
    if (this.device && classifyStoredDeviceOwner(state.nativeDeviceId, this.device.deviceId) !== 'owned') return false;
    return !settings || state.nativeFingerprint === runtimeFingerprint(settings);
  }

  revisionStatus() {
    const state = readJson(this.paths.stateFile(), {});
    const alive = isAlive(state.nativePid);
    try {
      const status = this.revisions.status('coding_mcp', alive ? state.nativeCodeRevision : null);
      if (!alive) return { ...status, update_pending: false, state: 'stopped' };
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

module.exports = { NativeService, isAlive, runtimeFingerprint, currentRuntimeState };
