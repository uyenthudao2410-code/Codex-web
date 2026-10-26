const path = require('node:path');
const fs = require('node:fs/promises');
const crypto = require('node:crypto');
const http = require('node:http');
const { pathToFileURL } = require('node:url');
const { performance: nodePerformance } = require('node:perf_hooks');
const { app, BrowserWindow, dialog, ipcMain, shell, Tray, Menu, nativeImage, session, clipboard } = require('electron');
const { SettingsStore } = require('./services/settingsStore');
const { SecretStore } = require('./services/secretStore');
const { LogService } = require('./services/logService');
const { EnvironmentService, pythonStatus } = require('./services/environmentService');
const { run } = require('./services/commandRunner');
const { resolveProxy, clearProxyCache } = require('./services/proxyService');
const { BuildVerificationService } = require('./services/buildVerificationService');
const { buildCodexDesktopMcpConfig } = require('./services/codexDesktopConfig');
const { readJson, writeJsonAtomic } = require('./services/jsonStore');
const runtimePathApi = require('./paths');
const { resourcesRoot, hubProxyDescriptorFile } = runtimePathApi;
const {
  createElectronRuntimePaths,
  configureElectronUserDataPath,
  singleInstanceLockPath
} = require('./services/runtimePaths');
const { RecoveryIpcClient } = require('./services/recoveryIpc');
const workHubFiles = require('./services/workHubFiles');
const workHubLsp = require('./services/workHubLsp');
const workHubCoordination = require('./services/workHubCoordination');
const { canonicalPathKey } = require('./services/pathSemantics');
const { CosCompanionAdapter, resolveCosUserDataDir } = require('./services/cosCompanionAdapter');
const { createWorkHubCodexChat } = require('./services/workHubCodexChat');
const workHubGitReview = require('./services/workHubGitReview');
const workHubSsh = require('./services/workHubSsh');
const { createBrowserQa } = require('./services/workHubBrowserQa');
const browserQa = createBrowserQa({
  createWindow: () => new BrowserWindow({
    show: false,
    width: 1280,
    height: 800,
    webPreferences: { offscreen: true, sandbox: true, contextIsolation: true },
  }),
});
const {
  ensureRecoveryHost,
  recoveryLoginItemArguments,
  electronUiArguments,
  assertActivationDeadline
} = require('./services/recoveryHostLauncher');
const { ComponentRevisionTracker } = require('./services/componentRevision');
const { activationSourceCheckpoint } = require('./services/activationClosure');
const { canonicalLedgerCensus } = require('./services/fullCleanActivation');
const { startRecoveryHostApplication } = require('./recoveryHost');
const { UiPerformanceMetrics, jsonByteLength } = require('./services/uiPerformanceMetrics');
const { loadOrCreateDeviceIdentity } = require('./services/deviceIdentity');
const { ControlPlaneEnrollmentService, centralServerOrigin } = require('./services/controlPlaneEnrollment');

// Version 1.0 has a new product identity but retains the existing encrypted
// desktop profile so an upgrade does not orphan its runtime configuration.
const recoveryHostMode = process.argv.includes('--recovery-host') || process.env.WEBCODEX_PROCESS_ROLE === 'recovery-host';
app.setName('Coding Tools MCP');
configureElectronUserDataPath(app, { argv: process.argv, recoveryHostMode });

let chatWindow;
let orchestrator;
let recoveryHostConnectionError = null;
let forceQuit = false;
let tray = null;
let buildVerification;
let lastRecoveryProgressTime = '';
let runtimeHeartbeatInFlight = null;
const trustedRendererPath = path.join(__dirname, '..', 'renderer', 'index.html');
const trustedRendererUrl = pathToFileURL(trustedRendererPath).href;
// The hub rebuilds the orchestration snapshot from the ledger on every GET
// (reconciliation + export_summary over the 101MB ledger; a warm full scan
// measures ~22s), so the old 10s budget failed structurally on a healthy
// epoch. 60s keeps a ~2.7x margin; do not lower this below the scan cost.
const PANEL_ORCHESTRATION_TIMEOUT_MS = 60000;
const PANEL_LIVE_CONTROL_TIMEOUT_MS = 2500;
const PANEL_ANALYTICS_TIMEOUT_MS = 10000;
const TOOLBAR_HEIGHT = 112;
const runtimePaths = createElectronRuntimePaths(app);
runtimePathApi.configureRuntimePaths(runtimePaths);
const settings = new SettingsStore(runtimePaths);
const secrets = new SecretStore(runtimePaths);
const log = new LogService(runtimePaths);
const environment = new EnvironmentService(runtimePaths);
const controlPlaneEnrollment = new ControlPlaneEnrollmentService({
  paths: runtimePaths,
  getExecutionMode: () => settings.load().executionMode,
  experimentalWindowsSandbox: runtimePaths.runtimeMode() === 'packaged'
});
const uiRevisionTracker = new ComponentRevisionTracker({ paths: runtimePaths });
const uiInstanceId = crypto.randomBytes(16).toString('hex');
const uiStartedAtUnixMs = Date.now();
const uiRuntimeIdentity = runtimePaths.runtimeIdentity();
const uiRunningRevision = recoveryHostMode ? null : uiRevisionTracker.captureRunning('electron_ui');
const uiActivationEpochId = (() => {
  const arg = process.argv.find((item) => String(item).startsWith('--activation-epoch-id='));
  const value = String(arg || '').slice('--activation-epoch-id='.length).trim();
  if (/^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(value)) return value;
  try {
    const persisted = readJson(runtimePaths.activationEpochFile(), {});
    const current = persisted?.current;
    // A persisted epoch is safe to inherit only after it is durably READY and
    // admission is OPEN.  During HANDOFF/VERIFYING an unlaunched UI must not
    // present itself as the replacement merely because it can read the JSON
    // projection; the coordinator's argv-bound epoch is the authority then.
    const persistedId = String(current?.activation_epoch_id || '').trim();
    return current?.state === 'READY'
      && current?.admission_state === 'OPEN'
      && /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(persistedId)
      ? persistedId
      : '';
  } catch { return ''; }
})();

function decorateUiRuntimeSnapshot(snapshot) {
  if (!snapshot || typeof snapshot !== 'object' || Array.isArray(snapshot)) return snapshot;
  const recoveryHost = snapshot.recoveryHost;
  const hostRecovery = recoveryHost?.electron_ui_recovery;
  const hostInstallationId = String(
    hostRecovery?.recovery_host_installation_id
      || recoveryHost?.installation_id
      || ''
  ).trim().toLowerCase() || null;
  const hostRuntimeMode = String(
    hostRecovery?.recovery_host_runtime_mode
      || hostRecovery?.runtime_mode
      || recoveryHost?.runtime_mode
      || ''
  ).trim().toLowerCase() || null;
  // A runtime mode alone is not an installation identity.  Legacy Recovery
  // Host descriptors may expose only `runtime_mode`; treating a same-mode
  // descriptor as connected would let a different checkout (or an old
  // packaged install) masquerade as this UI.  Keep the read model explicit
  // and fail closed until the installation hash is present and equal.
  const hostMatchesUi = Boolean(hostInstallationId)
    && hostInstallationId === uiRuntimeIdentity.installation_id;
  const hostIdentityUnverified = !hostInstallationId;
  // P2: one canonical workspace key. The renderer cannot realpath, so
  // main publishes the canonical spelling here; the renderer uses it for
  // store keys (work-hub.js) while IPC scope arguments keep the raw
  // settings spelling (scopedWorkHubRoot stays a lexical fail-closed
  // fence — canonicalizing scope input would change its contract).
  const snapshotSettings = snapshot.settings && typeof snapshot.settings === 'object' && !Array.isArray(snapshot.settings)
    ? snapshot.settings
    : null;
  const canonicalWorkspace = snapshotSettings ? canonicalPathKey(snapshotSettings.workspace) : '';
  return {
    ...snapshot,
    ...(snapshotSettings && canonicalWorkspace ? { settings: { ...snapshotSettings, canonicalWorkspace } } : {}),
    current_ui_runtime: {
      version: uiRuntimeIdentity.version,
      mode: uiRuntimeIdentity.mode,
      installation_id: uiRuntimeIdentity.installation_id,
      instance_id: uiInstanceId,
      pid: process.pid,
      started_at_unix_ms: uiStartedAtUnixMs
    },
    recovery_host_connection: recoveryHostConnectionError
      ? {
        state: 'blocked',
        code: recoveryHostConnectionError.code,
        message: recoveryHostConnectionError.message,
        details: recoveryHostConnectionError.details || null
      }
      : hostMatchesUi
        ? { state: 'connected', code: null, message: null }
        : {
          state: 'identity_unverified',
          code: hostIdentityUnverified
            ? 'RECOVERY_HOST_IDENTITY_UNVERIFIED'
            : 'RECOVERY_HOST_INSTALLATION_MISMATCH',
          message: hostIdentityUnverified
            ? 'Recovery Host installation identity is unavailable.'
            : 'Recovery Host identity is not the current UI installation.'
        }
  };
}
const uiPerformanceMetrics = new UiPerformanceMetrics({
  filePath: path.join(app.getPath('userData'), 'ui-performance.json'),
  context: {
    workspace: settings.load().workspace,
    ui_instance_id: uiInstanceId,
    ui_running_revision: uiRunningRevision || '',
    activation_epoch_id: uiActivationEpochId,
    session_started_at: new Date(uiStartedAtUnixMs).toISOString(),
    pid: process.pid,
    platform: process.platform,
    architecture: process.arch,
    product_version: app.getVersion()
  }
});
let uiRestartScheduled = false;
let uiExitInFlight = false;
let uiWindowReady = false;
let preparedP5A0Manifest = null;
let latestP5A0EpochId = '';
const P5_A0_SEED_HANDLE = 'secret://experiment/p5/a';
const DEV_UI_INSTANCE_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/;

function devUiSecondInstanceRequest(commandLine = []) {
  const controls = (Array.isArray(commandLine) ? commandLine : [])
    .map((value) => String(value || ''))
    .filter((value) => value.startsWith('--dev-ui-focus=')
      || value.startsWith('--dev-ui-stop=')
      || value.startsWith('--dev-ui-control-center='));
  if (!controls.length) return null;
  if (controls.length !== 1) return { action: 'invalid', instanceId: '' };
  const match = /^--dev-ui-(focus|stop|control-center)=(.+)$/.exec(controls[0]);
  if (!match || !DEV_UI_INSTANCE_PATTERN.test(match[2])) return { action: 'invalid', instanceId: '' };
  return { action: match[1], instanceId: match[2] };
}

function handleSecondInstance(commandLine = [], additionalData = null) {
  const incomingMode = String(additionalData?.runtime_mode || '').trim().toLowerCase();
  const incomingInstallationId = String(additionalData?.installation_id || '').trim().toLowerCase();
  if (incomingMode && incomingMode !== uiRuntimeIdentity.mode) {
    log.warn('Một runtime UI khác installation đã bị chặn bởi single-instance lock', {
      stage: 'ui-single-instance',
      current_runtime_mode: uiRuntimeIdentity.mode,
      current_installation_id: uiRuntimeIdentity.installation_id,
      incoming_runtime_mode: incomingMode,
      incoming_installation_id: incomingInstallationId || null
    });
    showChatWindow();
    void dialog.showMessageBox({
      type: 'warning',
      title: 'Coding Tools MCP đang mở bằng runtime khác',
      message: uiRuntimeIdentity.mode === 'development'
        ? 'Bản cài đặt đã được mở nhưng cửa sổ hiện tại là bản development (npm start).'
        : 'Một bản development (npm start) đang giữ phiên của ứng dụng.',
      detail: uiRuntimeIdentity.mode === 'development'
        ? 'Đóng cửa sổ development và Recovery Host của checkout hiện tại, sau đó mở lại Coding Tools MCP từ bản cài đặt. Không pairing hoặc cấp quyền từ cửa sổ này.'
        : 'Đóng bản development đang giữ phiên rồi mở lại bản Coding Tools MCP đã cài. Không chạy song song hai installation trên cùng profile.',
      buttons: ['Đã hiểu']
    }).catch(() => {});
    return;
  }
  const request = devUiSecondInstanceRequest(commandLine);
  if (!request) {
    showChatWindow();
    return;
  }
  if (request.action === 'invalid' || request.instanceId !== uiInstanceId) {
    log.warn('Refused an Electron UI lifecycle signal that did not match the live single instance', {
      stage: 'dev-ui-lifecycle',
      action: request.action
    });
    return;
  }
  if (request.action === 'stop') {
    void quitUi('operator_quit');
    return;
  }
  if (request.action === 'control-center') {
    openManagerWindow();
    return;
  }
  showChatWindow();
}

function existingInstanceDiagnostic(argv = process.argv) {
  const request = devUiSecondInstanceRequest(argv);
  if (request && request.action !== 'invalid') {
    return `DEV_UI SIGNAL_DISPATCHED action=${request.action} target_instance=${request.instanceId}`;
  }
  return uiRuntimeIdentity.mode === 'packaged'
    ? 'CODING_TOOLS_MCP_PACKAGED_BLOCKED_BY_EXISTING_UI Close the development runtime (npm start) and its Recovery Host, then reopen the installed Coding Tools MCP.'
    : 'CODING_TOOLS_MCP_UI_ALREADY_RUNNING Use "npm run dev" to inspect/activate the current checkout or "npm run dev:replace" for a verified replacement.';
}

function requestUiSingleInstanceLock() {
  const sharedUserDataPath = app.getPath('userData');
  const lockPath = singleInstanceLockPath({
    userDataPath: sharedUserDataPath,
    runtimeMode: uiRuntimeIdentity.mode
  });
  // Keep settings/Recovery Host state in the shared profile, while using a
  // mode-specific mutex so a development window cannot consume a packaged
  // launch (or vice versa) before the runtime identity can be displayed.
  app.setPath('userData', lockPath);
  try {
    return app.requestSingleInstanceLock({
      runtime_mode: uiRuntimeIdentity.mode,
      installation_id: uiRuntimeIdentity.installation_id
    });
  } finally {
    app.setPath('userData', sharedUserDataPath);
    // Definitive fix: if a previous run accidentally wrote config to the
    // lock path (instead of the shared profile), migrate those files back.
    // This prevents "empty setup" when builds use different userData dirs.
    try {
      migrateLockPathConfig(lockPath, sharedUserDataPath);
    } catch (_) { /* non-fatal */ }
  }
}

// Copies config files from the single-instance lock directory back to the
// shared profile. Only copies files that don't exist in the shared profile,
// never overwrites. Prevents config fragmentation across builds.
function migrateLockPathConfig(lockPath, sharedPath) {
  const fs = require('fs');
  const path = require('path');
  if (!lockPath || !sharedPath || lockPath === sharedPath) return;
  let entries;
  try {
    entries = fs.readdirSync(lockPath, { withFileTypes: true });
  } catch (_) { return; } // lock path doesn't exist, nothing to migrate
  for (const entry of entries) {
    if (!entry.isFile()) continue;
    // Skip Electron/Chromium internal files, only migrate app config
    if (entry.name === 'lockfile' || entry.name.startsWith('Singleton')) continue;
    const src = path.join(lockPath, entry.name);
    const dest = path.join(sharedPath, entry.name);
    try {
      if (fs.existsSync(dest)) continue; // don't overwrite
      fs.copyFileSync(src, dest);
    } catch (_) { /* skip on error */ }
  }
}

async function codeActivationRequest(component, allowAcceptancePending = false) {
  const allowed = new Set(['coding_mcp', 'electron_ui', 'recovery_host']);
  if (!allowed.has(component)) throw Object.assign(new Error('Component kích hoạt không hợp lệ.'), { code: 'INVALID_COMPONENT' });
  const snapshot = await orchestrator.snapshot({ force: true, reason: 'manual-code-activation-authority' });
  const sourceCheckpoint = activationSourceCheckpoint(snapshot?.recoveryHost, component);
  const now = Date.now();
  return {
    operation_id: crypto.randomBytes(18).toString('base64url'),
    component,
    requested_at_unix_ms: now,
    expires_at_unix_ms: now + 60_000,
    expected_disk_revision: uiRevisionTracker.disk(component, { force: true }).revision,
    allow_acceptance_pending: allowAcceptancePending === true,
    full_clean_required: true,
    activation_mode: 'full_clean_activation',
    source_checkpoint: sourceCheckpoint
  };
}

async function fullCleanRestartOptions() {
  const snapshot = await orchestrator.snapshot({ force: true, reason: 'manual-full-clean-restart-authority' });
  return {
    reason: 'operator_restart',
    sourceCheckpoint: activationSourceCheckpoint(snapshot?.recoveryHost)
  };
}

async function registerUiRevision() {
  if (recoveryHostMode
    || uiRestartScheduled
    || !orchestrator
    || !uiRunningRevision
    || !uiWindowReady
    || !chatWindow
    || chatWindow.isDestroyed()
    || !chatWindow.webContents
    || chatWindow.webContents.isDestroyed()) return null;
  const result = await orchestrator.registerUiRevision({
    instance_id: uiInstanceId,
    pid: process.pid,
    revision: uiRunningRevision,
    started_at_unix_ms: uiStartedAtUnixMs,
    runtime_mode: uiRuntimeIdentity.mode,
    installation_id: uiRuntimeIdentity.installation_id,
    ...(uiActivationEpochId ? { activation_epoch_id: uiActivationEpochId } : {})
  });
  if (result?.restart_required) {
    try {
      assertActivationDeadline({ expiresAtUnixMs: result.expires_at_unix_ms }, 'before_ui_relaunch');
    } catch (error) {
      if (error?.code !== 'ACTIVATION_REQUEST_EXPIRED') throw error;
      await orchestrator.activationStatus(result.operation_id).catch(() => null);
      return { ...result, restart_required: false, expired: true };
    }
    uiRestartScheduled = true;
    forceQuit = true;
    app.relaunch({ execPath: process.execPath, args: electronUiArguments(app, { activationEpochId: result.activation_epoch_id || uiActivationEpochId }) });
    app.exit(0);
  }
  return result;
}

async function suppressUiRecovery(reason) {
  if (recoveryHostMode || !orchestrator || typeof orchestrator.suppressUiRecovery !== 'function') return false;
  try {
    await orchestrator.suppressUiRecovery({ instance_id: uiInstanceId, reason });
    return true;
  } catch (error) {
    log.warn('Không thể ghi ý định tắt Electron UI vào Recovery Host', {
      stage: 'ui-recovery-suppression',
      code: error?.code || '',
      reason
    });
    return false;
  }
}

async function quitUi(reason, { stopRuntime = false } = {}) {
  if (uiExitInFlight) return false;
  uiExitInFlight = true;
  await suppressUiRecovery(reason);
  if (stopRuntime && orchestrator) {
    await orchestrator.stop().catch((error) => log.error(error.message, { stage: 'close' }));
  }
  forceQuit = true;
  app.quit();
  return true;
}

function appIconPath() {
  return path.join(__dirname, 'app-icon.png');
}

function sendManager(channel, payload) {
  if (chatWindow && !chatWindow.isDestroyed()
    && !chatWindow.webContents.isDestroyed()
    && isTrustedRendererUrl(chatWindow.webContents.getURL())) {
    chatWindow.webContents.send(channel, payload);
  }
}

function safeMessage(error) {
  return error instanceof Error ? error.message : String(error);
}

function assertTrustedIpc(event) {
  if (!isManagerIpc(event)) throw new Error('Đã chặn cuộc gọi IPC từ trang không phải Execution Hub.');
}

function isTrustedRendererUrl(value) {
  try {
    const url = new URL(value);
    url.search = '';
    url.hash = '';
    return url.href === trustedRendererUrl;
  } catch { return false; }
}

function isManagerIpc(event) {
  const contents = chatWindow?.webContents;
  return Boolean(
    chatWindow
    && !chatWindow.isDestroyed()
    && contents
    && !contents.isDestroyed()
    && event?.sender === contents
    && event.senderFrame
    && event.senderFrame === contents.mainFrame
    && isTrustedRendererUrl(contents.getURL())
    && isTrustedRendererUrl(event.senderFrame.url)
  );
}

function assertManagerIpc(event) {
  assertTrustedIpc(event);
}

function secureHandle(channel, handler) {
  ipcMain.handle(channel, (event, ...args) => {
    assertTrustedIpc(event);
    return handler(event, ...args);
  });
}

function workspaceStatePaths() {
  const workspace = String(settings.load().workspace || '').trim();
  if (!workspace) throw new Error('Vui lòng chọn thư mục làm việc trước.');
  const root = path.resolve(workspace);
  return {
    root,
    statePath: path.join(root, '.coding-tools', 'task-state.json'),
    historyPath: path.join(root, '.coding-tools', 'task-history.json'),
    performancePath: path.join(root, '.coding-tools', 'performance.json')
  };
}

function archiveTask(state, historyPath, reason) {
  if (!state || typeof state !== 'object' || (!state.task_id && !state.objective)) return;
  const history = readJson(historyPath, []);
  const items = Array.isArray(history) ? history : [];
  items.push({ ...state, archived_at: new Date().toISOString(), archive_reason: reason });
  writeJsonAtomic(historyPath, items.slice(-100));
}

async function invokeSafely(action) {
  try { return { ok: true, data: await action() }; }
  catch (error) { return { ok: false, error: safeMessage(error) }; }
}

function showChatWindow() {
  const target = createChatWindow();
  if (target.isMinimized()) target.restore();
  target.show();
  target.focus();
  return target;
}

function httpRequestJson({ port, path: requestPath, method, token, body, headers = {}, timeout }) {
  return new Promise((resolve, reject) => {
    const payload = body === undefined ? null : JSON.stringify(body);
    const request = http.request({
      host: '127.0.0.1',
      port,
      path: requestPath,
      method,
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(payload ? { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) } : {}),
        ...headers
      },
      timeout
    }, (response) => {
      let data = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { if (data.length < 4 * 1024 * 1024) data += chunk; });
      response.on('end', () => {
        if (response.statusCode >= 400) {
          reject(new Error(`MCP trả về HTTP ${response.statusCode}: ${String(data).slice(0, 200)}`));
          return;
        }
        try { resolve(data ? JSON.parse(data) : null); } catch { resolve(data); }
      });
    });
    request.on('timeout', () => { request.destroy(new Error('Quá thời gian kết nối MCP.')); });
    request.on('error', reject);
    if (payload) request.write(payload);
    request.end();
  });
}

async function readOrchestrationControlSnapshot() {
  const current = settings.load();
  const token = secrets.get('mcpAuthToken');
  if (!token) throw new Error('MCP chưa sẵn sàng để đọc trạng thái điều phối canonical.');
  return httpRequestJson({
    port: current.mcpPort,
    path: '/__control/orchestration',
    method: 'GET',
    token,
    timeout: PANEL_ORCHESTRATION_TIMEOUT_MS
  });
}

function canonicalTaskStateFromControl(control) {
  const taskList = control?.task_list;
  if (taskList?.source !== 'orchestration_ledger') {
    throw new Error('MCP không trả task list canonical từ orchestration ledger.');
  }
  const canonical = taskList.current;
  if (!canonical) return { exists: false, state: null, source: taskList.source };
  const projection = control?.task && typeof control.task === 'object' ? control.task : {};
  const canonicalTaskId = String(canonical.task_id || '').trim();
  const canonicalRunId = String(canonical.run_id || '').trim();
  const projectionTaskId = String(projection.task_id || '').trim();
  const projectionRunId = String(projection.run_id || '').trim();
  const controlRunId = String(control?.run_id || '').trim();
  const exactDetailBinding = Boolean(
    canonicalTaskId
    && canonicalRunId
    && projectionTaskId === canonicalTaskId
    && projectionRunId === canonicalRunId
    && controlRunId === canonicalRunId
  );
  const canonicalState = {
    task_id: canonicalTaskId,
    objective: canonical.objective || '',
    status: canonical.status || 'unknown',
    updated_at: canonical.finished_at || canonical.started_at || null,
    orchestration: { run_id: canonicalRunId, source: taskList.source },
    details_available: exactDetailBinding,
    detail_binding: exactDetailBinding ? 'exact' : 'unavailable'
  };
  if (!exactDetailBinding) return { exists: true, source: taskList.source, state: canonicalState };
  return {
    exists: true,
    source: taskList.source,
    state: {
      ...projection,
      ...canonicalState,
      task_id: canonicalTaskId,
      objective: canonical.objective || projection.objective || '',
      status: canonical.status || projection.status || 'unknown',
      updated_at: canonical.finished_at || canonical.started_at || projection.updated_at || null,
      orchestration: { run_id: canonicalRunId, source: taskList.source }
    }
  };
}

async function callMcpTool(name, toolArguments, timeoutMs = 30000) {
  const current = settings.load();
  const token = secrets.get('mcpAuthToken');
  if (!token) throw new Error('MCP chưa sẵn sàng để chạy lệnh.');
  const request = {
    jsonrpc: '2.0',
    id: `panel-tool-${name}-${Date.now()}`,
    method: 'tools/call',
    params: {
      name,
      arguments: toolArguments,
      _meta: {
        'io.modelcontextprotocol/protocolVersion': '2026-07-28',
        'io.modelcontextprotocol/clientCapabilities': {},
        'io.modelcontextprotocol/clientInfo': { name: 'coding-tools-mcp-panel', version: app.getVersion() }
      }
    }
  };
  const response = await httpRequestJson({
    port: current.mcpPort,
    path: '/mcp',
    method: 'POST',
    token,
    body: request,
    headers: {
      'MCP-Protocol-Version': '2026-07-28',
      'Mcp-Method': 'tools/call',
      'Mcp-Name': name,
      'X-Coding-Tools-Client-Id': 'electron-panel',
      'X-Coding-Tools-Client-Type': 'electron'
    },
    timeout: timeoutMs
  });
  if (response && response.error) throw new Error(response.error.message || `MCP từ chối ${name}.`);
  if (response?.result?.isError) {
    const message = response.result?.structuredContent?.error?.message || response.result?.content?.[0]?.text || `MCP từ chối ${name}.`;
    throw new Error(String(message).slice(0, 400));
  }
  return structuredMcpResult(response?.result) || null;
}

async function panelTaskControl(action) {
  const allowed = new Set(['pause', 'resume', 'stop', 'clear']);
  if (!allowed.has(action)) throw new Error('Thao tác nhiệm vụ từ bảng điều khiển không hợp lệ.');
  const current = settings.load();
  const token = secrets.get('mcpAuthToken');
  if (!token) throw new Error('MCP chưa sẵn sàng để điều khiển nhiệm vụ.');
  const request = {
    jsonrpc: '2.0',
    id: `panel-task-${action}-${Date.now()}`,
    method: 'tools/call',
    params: {
      name: 'task_control',
      arguments: { action },
      _meta: {
        'io.modelcontextprotocol/protocolVersion': '2026-07-28',
        'io.modelcontextprotocol/clientCapabilities': {},
        'io.modelcontextprotocol/clientInfo': { name: 'coding-tools-mcp-panel', version: app.getVersion() }
      }
    }
  };
  const response = await httpRequestJson({
    port: current.mcpPort,
    path: '/mcp',
    method: 'POST',
    token,
    body: request,
    headers: {
      'MCP-Protocol-Version': '2026-07-28',
      'Mcp-Method': 'tools/call',
      'Mcp-Name': 'task_control',
      'X-Coding-Tools-Client-Id': 'electron-panel',
      'X-Coding-Tools-Client-Type': 'electron'
    },
    timeout: 10000
  });
  if (response && response.error) throw new Error(response.error.message || 'MCP từ chối thao tác nhiệm vụ.');
  if (response?.result?.isError) {
    const message = response.result?.structuredContent?.error?.message || response.result?.content?.[0]?.text || 'MCP từ chối thao tác nhiệm vụ.';
    throw new Error(String(message).slice(0, 400));
  }
  return (response && response.result) || null;
}

function structuredMcpResult(result) {
  return result?.structuredContent || result || null;
}

function executionControlCenterProgressObservation(orchestration) {
  const truth = orchestration?.truth_snapshot?.orchestration;
  const runId = String(orchestration?.run_id || truth?.run_id || '').trim().toLowerCase();
  const waveId = String(truth?.wave_id || '').trim().toLowerCase();
  if (!/^[0-9a-f]{32}$/.test(runId) || !/^[0-9a-f]{32}$/.test(waveId)) return null;
  const snapshot = {
    schema_version: 1,
    run_id: runId,
    wave_id: waveId,
    orchestration_state: String(truth?.state || ''),
    run_status: String(truth?.run_status || ''),
    wave_status: String(truth?.wave_status || ''),
    task_status: String(orchestration?.task?.status || '')
  };
  return {
    run_id: runId,
    wave_id: waveId,
    snapshot_fingerprint: crypto.createHash('sha256')
      .update(JSON.stringify(snapshot), 'utf8')
      .digest('hex')
  };
}

async function callP5TaskControl(p5Experiment, requestIdPrefix) {
  const current = settings.load();
  const token = secrets.get('mcpAuthToken');
  if (!token) throw new Error('MCP is not ready for P5-A0 control.');
  const request = {
    jsonrpc: '2.0',
    id: requestIdPrefix + '-' + Date.now(),
    method: 'tools/call',
    params: {
      name: 'task_control',
      arguments: { action: 'p5', p5_experiment: p5Experiment },
      _meta: {
        'io.modelcontextprotocol/protocolVersion': '2026-07-28',
        'io.modelcontextprotocol/clientCapabilities': {},
        'io.modelcontextprotocol/clientInfo': { name: 'coding-tools-mcp-panel', version: app.getVersion() }
      }
    }
  };
  const response = await httpRequestJson({
    port: current.mcpPort,
    path: '/mcp',
    method: 'POST',
    token,
    body: request,
    headers: {
      'MCP-Protocol-Version': '2026-07-28',
      'Mcp-Method': 'tools/call',
      'Mcp-Name': 'task_control',
      'X-Coding-Tools-Client-Id': 'electron-panel',
      'X-Coding-Tools-Client-Type': 'electron'
    },
    timeout: 10000
  });
  if (response?.error) throw new Error(response.error.message || 'P5-A0 MCP call failed.');
  if (response?.result?.isError) {
    const message = response.result?.structuredContent?.error?.message || response.result?.content?.[0]?.text || 'P5-A0 MCP call was rejected.';
    throw new Error(String(message).slice(0, 400));
  }
  return structuredMcpResult(response?.result);
}

function p5EpochIdFromResult(result) {
  return String(result?.p5?.epoch?.activation_epoch_id || result?.p5?.activation_epoch_id || result?.p5?.epoch?.epoch?.activation_epoch_id || '').trim();
}

async function panelP5A0Control(action) {
  const allowed = new Set(['status', 'prepare', 'open', 'analyze', 'pause', 'resume', 'close', 'hard_stop']);
  if (!allowed.has(action)) throw new Error('Invalid P5-A0 control action.');
  if (action === 'status') {
    const result = await callP5TaskControl({ operation: 'status' }, 'panel-p5-status');
    latestP5A0EpochId = p5EpochIdFromResult(result) || latestP5A0EpochId;
    return result;
  }
  if (action === 'prepare') {
    const result = await callP5TaskControl({ operation: 'prepare_a0' }, 'panel-p5-prepare');
    const manifest = result?.p5?.manifest;
    if (!manifest || result?.p5?.phase !== 'P5-A0' || result?.p5?.study_type !== 'shadow_aa') throw new Error('MCP did not return a valid P5-A0 manifest.');
    preparedP5A0Manifest = JSON.parse(JSON.stringify(manifest));
    return result;
  }
  if (action === 'open') {
    if (!preparedP5A0Manifest) throw new Error('Prepare P5-A0 on the current runtime before opening an epoch.');
    const result = await callP5TaskControl({ operation: 'open', manifest: preparedP5A0Manifest, seed_handle: P5_A0_SEED_HANDLE }, 'panel-p5-open');
    preparedP5A0Manifest = null;
    latestP5A0EpochId = p5EpochIdFromResult(result) || latestP5A0EpochId;
    return result;
  }
  if (!latestP5A0EpochId) latestP5A0EpochId = p5EpochIdFromResult(await panelP5A0Control('status'));
  if (!latestP5A0EpochId) throw new Error('No P5-A0 epoch is available for this action.');
  const result = await callP5TaskControl({
    operation: action,
    activation_epoch_id: latestP5A0EpochId,
    ...(action === 'hard_stop' ? { reason: 'operator_hard_stop_from_electron_manager' } : {}),
    ...(action === 'close' ? { reason: 'operator_close_from_electron_manager' } : {})
  }, 'panel-p5-' + action);
  latestP5A0EpochId = p5EpochIdFromResult(result) || latestP5A0EpochId;
  return result;
}


function togglePanel() {
  openManagerWindow('overview');
  sendManager('panel:visibility', { visible: false });
  return false;
}

function createTray() {
  if (tray && !tray.isDestroyed()) return tray;
  const icon = nativeImage.createFromPath(appIconPath()).resize({ width: 16, height: 16 });
  tray = new Tray(icon);
  tray.setToolTip('Coding Tools MCP · Đang chạy ngầm');
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Mở Coding Tools MCP', click: () => showChatWindow() },
    { label: 'Thiết lập máy và thư mục', click: () => openManagerWindow() },
    { type: 'separator' },
    { label: 'Thoát ứng dụng (Giữ dịch vụ MCP)', click: () => { void quitUi('operator_quit'); } }
  ]));
  tray.on('click', () => showChatWindow());
  tray.on('double-click', () => showChatWindow());
  return tray;
}

function createChatWindow() {
  if (chatWindow && !chatWindow.isDestroyed()) {
    chatWindow.show();
    chatWindow.focus();
    return chatWindow;
  }

  uiWindowReady = false;
  chatWindow = new BrowserWindow({
    width: 1360,
    height: 900,
    minWidth: 960,
    minHeight: 640,
    show: false,
    backgroundColor: '#f7f7f8',
    title: 'Coding Tools MCP',
    icon: appIconPath(),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });
  chatWindow.removeMenu();
  const openingWindow = chatWindow;
  openingWindow.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  const guardNavigation = (event, url) => {
    if (!isTrustedRendererUrl(url)) event.preventDefault();
  };
  openingWindow.webContents.on('will-navigate', guardNavigation);
  openingWindow.webContents.on('will-redirect', guardNavigation);
  const revealOpeningWindow = (attemptsRemaining = 20) => {
    if (openingWindow !== chatWindow || openingWindow.isDestroyed()
      || !isTrustedRendererUrl(openingWindow.webContents.getURL())) return;
    openingWindow.show();
    openingWindow.focus();
    if (!openingWindow.isVisible()) {
      if (attemptsRemaining > 1) {
        setTimeout(() => revealOpeningWindow(attemptsRemaining - 1), 50);
      } else {
        log.error('Electron UI window did not become visible after ready-to-show', {
          stage: 'ui-window-ready'
        });
      }
      return;
    }
    uiWindowReady = true;
    void registerUiRevision().catch((error) => log.warn(error.message, {
      stage: 'ui-revision-registration',
      code: error?.code || ''
    }));
  };
  openingWindow.once('ready-to-show', () => revealOpeningWindow());
  const initialTheme = settings.load().theme === 'light' ? 'light' : 'dark';
  openingWindow.loadFile(trustedRendererPath, { query: { theme: initialTheme }, hash: 'system' });

  chatWindow.on('closed', () => {
    if (openingWindow !== chatWindow) return;
    uiWindowReady = false;
    chatWindow = null;
  });
  chatWindow.on('close', (event) => {
    if (forceQuit) return;
    event.preventDefault();
    if (settings.load().keepRunningOnClose) {
      openingWindow.hide();
      return;
    }
    if (!orchestrator) {
      void quitUi('operator_quit');
      return;
    }
    void quitUi('runtime_stop', { stopRuntime: true });
  });
  return chatWindow;
}

function managerNavigationPage(page) {
  if (page == null || page === '') return 'system';
  if (!['system', 'workspace', 'deploy', 'overview', 'device', 'settings'].includes(page)) {
    throw new Error('Trang cấu hình được yêu cầu không hợp lệ.');
  }
  return page;
}

function openManagerWindow(page) {
  const requestedPage = managerNavigationPage(page);
  const targetWindow = showChatWindow();
  const sendNavigation = () => {
    if (targetWindow === chatWindow
      && !targetWindow.isDestroyed()
      && !targetWindow.webContents.isDestroyed()
      && isTrustedRendererUrl(targetWindow.webContents.getURL())) {
      targetWindow.webContents.send('manager:navigate', { page: requestedPage });
    }
  };
  if (targetWindow.webContents.isLoadingMainFrame()) {
    targetWindow.webContents.once('did-finish-load', sendNavigation);
  } else {
    sendNavigation();
  }
  return targetWindow;
}

function registerIpc() {
  secureHandle('app:snapshot', (_event, options) => invokeSafely(async () => (
    decorateUiRuntimeSnapshot(await orchestrator.snapshot(options || {}))
  )));
  secureHandle('app:lightweight-snapshot', (event) => invokeSafely(async () => {
    const startedAt = nodePerformance.now();
    const snapshot = decorateUiRuntimeSnapshot(await orchestrator.lightweightSnapshot());
    if (isManagerIpc(event)) {
      uiPerformanceMetrics.recordMain({
        observed_at_unix_ms: Date.now(),
        snapshot_build_ms: nodePerformance.now() - startedAt,
        snapshot_size_bytes: jsonByteLength(snapshot)
      });
    }
    return snapshot;
  }));
  secureHandle('ui-performance:record', (event, sample) => invokeSafely(async () => {
    assertManagerIpc(event);
    uiPerformanceMetrics.updateContext({ workspace: settings.load().workspace });
    return uiPerformanceMetrics.recordRenderer(sample);
  }));
  secureHandle('ui-performance:read', (event) => invokeSafely(async () => {
    assertManagerIpc(event);
    return uiPerformanceMetrics.report();
  }));
  secureHandle('workspace:hub', () => invokeSafely(async () => { const current = settings.load(); return { activeWorkspace: current.workspace, recentWorkspaces: current.recentWorkspaces || [] }; }));
  // Work Hub (catalog 261022, F06/F09/F12): read-only file browsing, content
  // search and git views, strictly inside the active workspace.
  const workHubRoot = () => {
    const workspace = String(settings.load().workspace || '').trim();
    if (!workspace) throw new Error('Vui lòng chọn thư mục làm việc trước.');
    return path.resolve(workspace);
  };
  // Project-scope fencing (B04/R08): a caller may pin the workspace it
  // rendered for; if the active project has since changed, the request is
  // rejected BEFORE any file, Git or open side effect. Omitting the scope
  // keeps legacy calls working; an explicitly empty scope is rejected.
  const normalizeWorkHubScope = (value) => {
    const resolved = path.resolve(String(value || ''));
    return process.platform === 'win32' ? resolved.toLowerCase() : resolved;
  };
  // P3: a managed worktree of the active project is a valid scope. Managed
  // worktrees live in a sibling "<project>.worktrees" folder (see
  // gitWorktreeAdd); accepting one lets Files/Diff/Chat/Terminal work in
  // the worktree without switching the global settings workspace (which
  // would re-key every surface, L3). Membership uses the same canonical
  // prefix definition as gitWorktreeRemove, so alias spellings of the same
  // managed worktree match; the main-project branch above stays lexical
  // per P2. The base directory itself is not a worktree, and anything
  // outside the project + its managed worktrees still rejects — the fence
  // set does not grow, it only gains the worktree members.
  const managedWorktreeScopeRoot = (root, expectedWorkspace) => {
    const candidate = path.resolve(String(expectedWorkspace || ''));
    const base = path.join(path.dirname(root), `${path.basename(root)}.worktrees`);
    if (!workHubFiles.pathHasPrefix(candidate, base)) return null;
    if (canonicalPathKey(candidate) === canonicalPathKey(base)) return null;
    return candidate;
  };
  const scopedWorkHubRoot = (expectedWorkspace) => {
    const root = workHubRoot();
    if (expectedWorkspace === undefined) return root;
    if (String(expectedWorkspace || '').trim()
      && normalizeWorkHubScope(expectedWorkspace) === normalizeWorkHubScope(root)) {
      return root;
    }
    const worktreeRoot = String(expectedWorkspace || '').trim()
      ? managedWorktreeScopeRoot(root, expectedWorkspace)
      : null;
    if (worktreeRoot) return worktreeRoot;
    throw new Error('Dự án đã thay đổi so với lúc dữ liệu được mở — thao tác bị từ chối, hãy tải lại trang này.');
  };
  secureHandle('workhub:list', (_event, rel, expectedWorkspace) => invokeSafely(async () => workHubFiles.listDir(scopedWorkHubRoot(expectedWorkspace), rel)));
  secureHandle('workhub:read', (_event, rel, expectedWorkspace) => invokeSafely(async () => workHubFiles.readTextFile(scopedWorkHubRoot(expectedWorkspace), rel)));
  secureHandle('workhub:search', (_event, query, expectedWorkspace) => invokeSafely(async () => workHubFiles.searchText(scopedWorkHubRoot(expectedWorkspace), query)));
  secureHandle('workhub:write', (_event, rel, content, expectedHash, expectedWorkspace) => invokeSafely(async () => workHubFiles.writeTextFile(scopedWorkHubRoot(expectedWorkspace), rel, content, expectedHash)));
  secureHandle('workhub:copy-in', (_event, sourceAbsolute, destDirRel, expectedWorkspace) => invokeSafely(async () => workHubFiles.copyIntoWorkspace(scopedWorkHubRoot(expectedWorkspace), sourceAbsolute, destDirRel)));
  secureHandle('workhub:git-status', (_event, expectedWorkspace) => invokeSafely(async () => workHubFiles.gitStatus(scopedWorkHubRoot(expectedWorkspace))));
  secureHandle('workhub:git-diff', (_event, rel, expectedWorkspace) => invokeSafely(async () => workHubFiles.gitFileDiff(scopedWorkHubRoot(expectedWorkspace), rel)));
  secureHandle('workhub:git-log', (_event, limit, expectedWorkspace) => invokeSafely(async () => workHubFiles.gitLog(scopedWorkHubRoot(expectedWorkspace), limit)));
  secureHandle('workhub:git-show', (_event, hash, expectedWorkspace) => invokeSafely(async () => workHubFiles.gitShow(scopedWorkHubRoot(expectedWorkspace), hash)));
  secureHandle('workhub:git-blame', (_event, rel, expectedWorkspace) => invokeSafely(async () => workHubFiles.gitBlame(scopedWorkHubRoot(expectedWorkspace), rel)));
  secureHandle('workhub:read-image', (_event, rel, expectedWorkspace) => invokeSafely(async () => workHubFiles.readImageData(scopedWorkHubRoot(expectedWorkspace), rel)));
  secureHandle('workhub:open-path', (_event, rel, reveal, expectedWorkspace) => invokeSafely(async () => {
    const { target } = workHubFiles.resolveInsideRoot(scopedWorkHubRoot(expectedWorkspace), rel);
    if (reveal) { shell.showItemInFolder(target); return { opened: false, revealed: true }; }
    const failure = await shell.openPath(target);
    if (failure) throw new Error(failure);
    return { opened: true };
  }));
  // A3: recipes run through the runtime's own Job lifecycle (exec_command /
  // command_control), never through a second executor.
  secureHandle('workhub:job-run', (_event, payload) => invokeSafely(async () => {
    const command = String(payload?.command || '').trim();
    if (!command) throw new Error('Lệnh không được trống.');
    const root = scopedWorkHubRoot(payload?.expectedWorkspace);
    // P1 (L2) terminal fence: the recipe cwd must resolve inside the
    // scoped root, exactly like Files (resolveInsideRoot throws outside
    // it, including symlink/junction escapes). An empty cwd still means
    // the root itself. Rejecting — not silently relocating — keeps the
    // command's relative paths honest.
    const cwd = workHubFiles.resolveInsideRoot(root, String(payload?.cwd || '').trim()).target;
    const execArgs = {
      cmd: command,
      cwd,
      yield_time_ms: 8000,
      timeout_ms: 600000,
      verbosity: 'full',
      principal_id: 'workhub',
    };
    // P1 (L2) RUN binding: exec_command requires run_id and wave_id
    // together, and the panel task state carries no wave — so the current
    // wave is resolved from the same ledger read the panel lease uses
    // (waves are ordinal-ordered; the last one is the current wave, the
    // same rule orchestration recovery uses). A requested RUN the ledger
    // does not know is refused rather than run unbound under a bogus id;
    // a RUN with no wave yet (or no local ledger) runs unbound exactly
    // as before, and the binding outcome is reported back so the UI
    // never claims a binding it did not get.
    let workhubRunBinding = null;
    const requestedRunId = String(payload?.runId || '').trim();
    if (requestedRunId) {
      const detail = workHubCoordination.runDetail(root, requestedRunId);
      if (detail && detail.available && !detail.found) {
        throw new Error('RUN không tồn tại trong ledger của dự án này — từ chối chạy lệnh để tránh gắn nhầm task.');
      }
      const waves = detail && detail.found && Array.isArray(detail.waves) ? detail.waves : [];
      if (waves.length) {
        const waveId = waves[waves.length - 1].waveId;
        if (waveId) {
          execArgs.run_id = requestedRunId;
          execArgs.wave_id = waveId;
          workhubRunBinding = { runId: requestedRunId, waveId };
        }
      }
    }
    const result = await callMcpTool('exec_command', execArgs, 30000);
    if (result && typeof result === 'object' && !Array.isArray(result)) {
      return { ...result, workhubRunBinding };
    }
    return result;
  }));
  secureHandle('workhub:handoff-get', (_event, payload) => invokeSafely(async () => {
    // A8: read the recorded handoff capsule for a run through the runtime's
    // own task_control surface (handoff_action "get" is read-only).
    const result = await callMcpTool('task_control', {
      action: 'handoff',
      handoff_action: 'get',
      run_id: String(payload?.runId || ''),
    }, 15000);
    const structured = result?.structuredContent || result?.structured_content;
    if (structured && typeof structured === 'object') return structured;
    const text = result?.content?.find?.((item) => item?.type === 'text')?.text;
    if (typeof text === 'string') { try { return JSON.parse(text); } catch { return { raw: text }; } }
    return result && typeof result === 'object' ? result : { capsule: null };
  }));
  secureHandle('workhub:git-head', (_event, expectedWorkspace) => invokeSafely(async () => workHubFiles.gitHead(scopedWorkHubRoot(expectedWorkspace))));
  secureHandle('workhub:git-commit', (_event, payload) => invokeSafely(async () => workHubFiles.gitCommitFiles(
    scopedWorkHubRoot(payload?.expectedWorkspace), payload?.files, payload?.message, { expectedHead: payload?.expectedHead })));
  secureHandle('workhub:worktree-list', (_event, expectedWorkspace) => invokeSafely(async () => workHubFiles.gitWorktreeList(scopedWorkHubRoot(expectedWorkspace))));
  secureHandle('workhub:worktree-add', (_event, payload) => invokeSafely(async () => workHubFiles.gitWorktreeAdd(
    scopedWorkHubRoot(payload?.expectedWorkspace), payload?.name, payload?.branch)));
  secureHandle('workhub:worktree-remove', (_event, payload) => invokeSafely(async () => workHubFiles.gitWorktreeRemove(
    scopedWorkHubRoot(payload?.expectedWorkspace), payload?.path)));
  secureHandle('workhub:sha256', (_event, text) => invokeSafely(async () => require('crypto').createHash('sha256').update(String(text || '')).digest('hex')));
  secureHandle('workhub:qa-capture', (_event, payload) => invokeSafely(async () => browserQa.capture(
    scopedWorkHubRoot(payload?.expectedWorkspace), payload)));
  secureHandle('workhub:qa-list', (_event, expectedWorkspace) => invokeSafely(async () => browserQa.listCaptures(scopedWorkHubRoot(expectedWorkspace))));
  secureHandle('workhub:ssh-scan', (_event, payload) => invokeSafely(async () => workHubSsh.scanHostKey(payload)));
  secureHandle('workhub:ssh-test', (_event, payload) => invokeSafely(async () => workHubSsh.testTarget(
    scopedWorkHubRoot(payload?.expectedWorkspace), payload)));
  // CoS companion (W1, read-only pilot): the adapter lives in the main
  // process and is the only holder of the CoS Control API token. Handlers
  // return its result view verbatim; when the feature flag is off the
  // adapter answers COS_DISABLED without touching the network or disk.
  let cosCompanionAdapter = null;
  const getCosCompanionAdapter = () => {
    const current = settings.load();
    if (!cosCompanionAdapter) cosCompanionAdapter = new CosCompanionAdapter();
    cosCompanionAdapter.configure({
      enabled: Boolean(current.cosCompanionEnabled),
      userDataDir: resolveCosUserDataDir({ settingDir: current.cosCompanionUserDataDir }),
    });
    return cosCompanionAdapter;
  };
  secureHandle('workhub:cos-status', () => invokeSafely(async () => {
    const adapter = getCosCompanionAdapter();
    if (!adapter.enabled) return { ...adapter.getConnectionView(), status: null, health: null, error: null };
    const probe = await adapter.probe();
    if (!probe.ok) return { ...adapter.getConnectionView(), status: null, health: null, error: probe.error };
    const status = await adapter.getStatus();
    return {
      ...adapter.getConnectionView(),
      health: probe.data.health,
      status: status.ok ? status.data : null,
      error: status.ok ? null : status.error,
    };
  }));
  secureHandle('workhub:cos-sessions', (_event, payload) => invokeSafely(async () => {
    const adapter = getCosCompanionAdapter();
    if (!adapter.enabled) return { ok: false, state: 'DISCONNECTED', error: { code: 'COS_DISABLED', message: 'Tích hợp CoS companion đang tắt.' } };
    return adapter.listSessions({ limit: payload?.limit, cursor: payload?.cursor });
  }));
  secureHandle('workhub:cos-session-events', (_event, payload) => invokeSafely(async () => {
    const adapter = getCosCompanionAdapter();
    if (!adapter.enabled) return { ok: false, state: 'DISCONNECTED', error: { code: 'COS_DISABLED', message: 'Tích hợp CoS companion đang tắt.' } };
    return adapter.getSessionEvents(payload?.sessionId, { from: payload?.from, limit: payload?.limit, kinds: payload?.kinds });
  }));
  secureHandle('workhub:coord-runs', (_event, payload) => invokeSafely(async () => workHubCoordination.listRuns(
    scopedWorkHubRoot(payload?.expectedWorkspace), payload?.limit)));
  secureHandle('workhub:coord-run', (_event, payload) => invokeSafely(async () => workHubCoordination.runDetail(
    scopedWorkHubRoot(payload?.expectedWorkspace), payload?.runId)));
  secureHandle('workhub:steer-list', (_event, expectedWorkspace) => invokeSafely(async () => workHubCoordination.listSteering(
    scopedWorkHubRoot(expectedWorkspace))));
  secureHandle('workhub:steer-save', (_event, payload) => invokeSafely(async () => workHubCoordination.saveSteering(
    scopedWorkHubRoot(payload?.expectedWorkspace), payload)));
  secureHandle('workhub:steer-dispatch', (_event, payload) => invokeSafely(async () => workHubCoordination.dispatchSteering(
    scopedWorkHubRoot(payload?.expectedWorkspace), payload?.id)));
  secureHandle('workhub:lsp-providers', (_event, expectedWorkspace) => invokeSafely(async () => {
    scopedWorkHubRoot(expectedWorkspace);
    return workHubLsp.providers();
  }));
  secureHandle('workhub:lsp-definition', (_event, payload) => invokeSafely(async () => workHubLsp.definition(
    scopedWorkHubRoot(payload?.expectedWorkspace), payload?.rel, Number(payload?.line), Number(payload?.character))));
  secureHandle('workhub:lsp-references', (_event, payload) => invokeSafely(async () => workHubLsp.references(
    scopedWorkHubRoot(payload?.expectedWorkspace), payload?.rel, Number(payload?.line), Number(payload?.character))));
  secureHandle('workhub:lsp-symbols', (_event, payload) => invokeSafely(async () => workHubLsp.symbols(
    scopedWorkHubRoot(payload?.expectedWorkspace), payload?.rel)));
  secureHandle('workhub:job-control', (_event, payload) => invokeSafely(async () => {
    const action = String(payload?.action || 'poll');
    if (!['poll', 'write', 'kill', 'read'].includes(action)) throw new Error('Thao tác Job không hợp lệ.');
    return callMcpTool('command_control', {
      action,
      command_id: String(payload?.commandId || ''),
      chars: action === 'write' ? String(payload?.chars || '') : undefined,
      signal: payload?.signal === 'KILL' ? 'KILL' : 'TERM',
      consumer_id: 'workhub-panel',
      yield_time_ms: 3000,
      verbosity: 'full',
    }, 20000);
  }));
  secureHandle('workhub:check-url', (_event, url) => invokeSafely(async () => {
    const target = new URL(String(url || ''));
    if (!['http:', 'https:'].includes(target.protocol)) throw new Error('Chỉ kiểm tra URL http/https.');
    const started = Date.now();
    const response = await fetch(target, { method: 'GET', redirect: 'follow', signal: AbortSignal.timeout(6000) });
    const text = await response.text().catch(() => '');
    const title = (text.match(/<title[^>]*>([^<]*)<\/title>/i) || [])[1] || '';
    return { url: target.href, status: response.status, ok: response.ok, ms: Date.now() - started, title: title.trim().slice(0, 200) };
  }));
  // W3 native chat: Work Hub talks to the local Codex App Server through
  // the runtime's existing internal codex_bridge tool — the same panel
  // channel as job-run/handoff-get; the public smart-v3 surface is
  // unchanged and no CoS app is involved. Session state lives in the
  // workHubCodexChat service (main process), keyed by canonical workspace key (P2).
  const codexChat = createWorkHubCodexChat({
    callBridge: (args, timeoutMs) => callMcpTool('codex_bridge', args, timeoutMs || 30000),
    // W3-C: handoff reuses the existing task_control surface (task start +
    // handoff capsule record/get) through the same callMcpTool channel;
    // the controller lease is read-only from the orchestration ledger.
    callTool: (name, args, timeoutMs) => callMcpTool(name, args, timeoutMs || 30000),
    readLease: (root, runId) => {
      // P2 (L8): lease lookup uses the canonical root so an alias-spelled
      // panel root reads the same ledger. canonicalPathKey falls back to
      // the resolved spelling when the path does not exist, so
      // absent-ledger behavior is unchanged.
      const key = canonicalPathKey(root);
      const detail = workHubCoordination.runDetail(key || root, runId);
      return detail && detail.found ? detail.lease : null;
    },
    // P0 ended-RUN gate: same ledger read, run status only.
    readRunStatus: (root, runId) => {
      const key = canonicalPathKey(root);
      const detail = workHubCoordination.runDetail(key || root, runId);
      return detail && detail.found ? detail.run.status : null;
    },
    // Durable chat-session registry beside the app data (same folder as
    // settings.json / runtime-state.json), so a persistent chat thread
    // can be resumed after an Electron/MCP restart.
    stateFile: path.join(runtimePaths.dataRoot(), 'workhub-codex-chat-sessions.json'),
    // P2 (4): native-chat usage — current-RUN binding uses the same P0/P5
    // orchestration accessor as the task-state handlers (task_list.current
    // -> run_id/task_id). A snapshot failure degrades the record to
    // unlinked inside the service; it never throws here.
    readCurrentRun: async () => {
      try {
        const control = await readOrchestrationControlSnapshot();
        const current = control && control.task_list ? control.task_list.current : null;
        return current && current.run_id
          ? { runId: String(current.run_id), taskId: current.task_id ? String(current.task_id) : null }
          : null;
      } catch {
        return null;
      }
    },
    // P2 (4): durable usage history beside the session registry (app data,
    // not ledger evidence): one record per terminal turn, counts + model +
    // timestamp only — never prompt, agent text, or tool content.
    usageFile: path.join(runtimePaths.dataRoot(), 'workhub-codex-chat-usage.json'),
  });
  secureHandle('workhub:codex-chat-probe', (_event, payload) => invokeSafely(async () => (
    codexChat.probe(scopedWorkHubRoot(payload?.expectedWorkspace)))));
  secureHandle('workhub:codex-chat-history', (_event, payload) => invokeSafely(async () => (
    codexChat.listHistory(scopedWorkHubRoot(payload?.expectedWorkspace)))));
  secureHandle('workhub:codex-chat-send', (_event, payload) => invokeSafely(async () => (
    codexChat.send(scopedWorkHubRoot(payload?.expectedWorkspace), {
      text: payload?.text,
      model: payload?.model,
      effort: payload?.effort,
      link: payload?.link && typeof payload.link === 'object' ? { runId: payload.link.runId, taskId: payload.link.taskId } : null,
    }))));
  secureHandle('workhub:codex-chat-poll', (_event, payload) => invokeSafely(async () => (
    codexChat.poll(scopedWorkHubRoot(payload?.expectedWorkspace)))));
  secureHandle('workhub:codex-chat-interrupt', (_event, payload) => invokeSafely(async () => (
    codexChat.interrupt(scopedWorkHubRoot(payload?.expectedWorkspace)))));
  secureHandle('workhub:codex-chat-reset', (_event, payload) => invokeSafely(async () => (
    codexChat.reset(scopedWorkHubRoot(payload?.expectedWorkspace)))));
  // W3-C handlers (kept in this block, AFTER workhub:check-url, like the
  // original W3 chat block — the work-hub-scope fixture evaluates main.js
  // only up to workhub:check-url and lacks these factories).
  secureHandle('workhub:codex-chat-models', (_event, payload) => invokeSafely(async () => (
    codexChat.listModels(scopedWorkHubRoot(payload?.expectedWorkspace)))));
  secureHandle('workhub:codex-chat-fork', (_event, payload) => invokeSafely(async () => (
    codexChat.fork(scopedWorkHubRoot(payload?.expectedWorkspace), {
      sourceThreadId: payload?.sourceThreadId,
      text: payload?.text,
      model: payload?.model,
      effort: payload?.effort,
      link: payload?.link && typeof payload.link === 'object' ? { runId: payload.link.runId, taskId: payload.link.taskId } : null,
    }))));
  secureHandle('workhub:codex-chat-resume', (_event, payload) => invokeSafely(async () => (
    codexChat.resume(scopedWorkHubRoot(payload?.expectedWorkspace)))));
  secureHandle('workhub:codex-chat-handoff', (_event, payload) => invokeSafely(async () => (
    codexChat.handoffToTask(scopedWorkHubRoot(payload?.expectedWorkspace), {
      objective: payload?.objective,
      runId: payload?.runId,
      link: payload?.link && typeof payload.link === 'object' ? { runId: payload.link.runId, taskId: payload.link.taskId } : null,
      choice: payload?.choice,
      confirmEnded: payload?.confirmEnded === true,
    }))));
  // W5 git range review (kept AFTER workhub:check-url for the same scope-
  // fixture reason as the W3-C handlers above): read-only range analysis
  // of the scoped workspace; the service builds the range from two revs
  // and validates them, so a bad rev surfaces its own error message.
  secureHandle('workhub:git-review', (_event, payload) => invokeSafely(async () => workHubGitReview.gitRangeReview(
    scopedWorkHubRoot(payload?.expectedWorkspace), { from: payload?.from, to: payload?.to })));
  let workHubAwakeId = null;
  secureHandle('workhub:keep-awake', (_event, on) => invokeSafely(async () => {
    const { powerSaveBlocker } = require('electron');
    if (on && workHubAwakeId === null) workHubAwakeId = powerSaveBlocker.start('prevent-app-suspension');
    if (!on && workHubAwakeId !== null) { powerSaveBlocker.stop(workHubAwakeId); workHubAwakeId = null; }
    return { active: workHubAwakeId !== null };
  }));
  secureHandle('workhub:list-windows', () => invokeSafely(async () => {
    if (process.platform !== 'win32') return { supported: false, windows: [] };
    const { execFile } = require('child_process');
    const script = "Get-Process | Where-Object { $_.MainWindowTitle } | Select-Object ProcessName, Id, MainWindowTitle | ConvertTo-Json -Compress";
    const stdout = await new Promise((resolve, reject) => {
      execFile('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', script], { timeout: 10000, windowsHide: true, maxBuffer: 1024 * 1024 },
        (error, out) => (error ? reject(error) : resolve(String(out || ''))));
    });
    let parsed = [];
    try { parsed = JSON.parse(stdout || '[]'); } catch { parsed = []; }
    if (!Array.isArray(parsed)) parsed = [parsed];
    return { supported: true, windows: parsed.map((w) => ({ process: String(w.ProcessName || ''), pid: Number(w.Id) || 0, title: String(w.MainWindowTitle || '') })).filter((w) => w.title) };
  }));
  secureHandle('control-plane:open-console', (event, serverUrl) => invokeSafely(async () => {
    assertManagerIpc(event);
    // Navigation only: no pairing, credentials, settings writes or runtime
    // changes. Reuse the credential-free HTTPS origin validator; never accept
    // an arbitrary shell URL, /mcp path, token, query or fragment.
    const origin = centralServerOrigin(serverUrl || settings.load().controlPlaneServerUrl);
    await shell.openExternal(`${origin}/`);
    return true;
  }));
  secureHandle('control-plane:enroll', (event, serverUrl) => invokeSafely(async () => {
    // Pairing creates a pending central enrollment record. Keep it confined
    // to the Command Center and an Ubuntu-managed executor; it is neither a
    // role switch nor a grant.
    assertManagerIpc(event);
    if (settings.load().executionRole !== 'central_executor') {
      throw Object.assign(new Error('Pairing Ubuntu chỉ khả dụng cho central executor đã được kích hoạt.'), {
        code: 'CONTROL_PLANE_ENROLLMENT_ROLE_REQUIRED'
      });
    }
    const receipt = await controlPlaneEnrollment.request({
      serverUrl,
      deviceIdentity: loadOrCreateDeviceIdentity(runtimePaths)
    });
    // Keep the non-secret origin so the resumable setup screen can restore
    // the same target after a reload.  node-agent remains the authority for
    // enrollment state and all credentials.
    settings.save({ controlPlaneServerUrl: receipt.server_origin });
    return receipt;
  }));
  secureHandle('control-plane:enrollment-status', (event) => invokeSafely(async () => {
    // Reconcile the durable node enrollment after UI reload/restart.  The
    // node agent owns the secret and returns only a redacted state receipt.
    assertManagerIpc(event);
    if (settings.load().executionRole !== 'central_executor') {
      throw Object.assign(new Error('Kiểm tra pairing Ubuntu chỉ khả dụng cho central executor đã được kích hoạt.'), {
        code: 'CONTROL_PLANE_ENROLLMENT_ROLE_REQUIRED'
      });
    }
    const receipt = await controlPlaneEnrollment.reconcileEnrollment({
      deviceIdentity: loadOrCreateDeviceIdentity(runtimePaths)
    });
    // Resume an existing node enrollment when the ordinary UI setting was
    // lost.  The node-agent returns only a normalized HTTPS origin here; it
    // never returns the node credential or account/binding material.  Do not
    // overwrite a non-empty user setting because changing the target is an
    // explicit replacement flow, not a side effect of opening Settings.
    const currentSettings = settings.load();
    if (!String(currentSettings.controlPlaneServerUrl || '').trim()
      && receipt?.server_origin) {
      settings.save({ controlPlaneServerUrl: receipt.server_origin });
    }
    return receipt;
  }));
  secureHandle('control-plane:authority-status', (event) => invokeSafely(async () => {
    // Enrollment approval is not account/binding authority. This read-only
    // projection lets Settings show the distinction without exposing owner,
    // OAuth, path or credential material to the renderer.
    assertManagerIpc(event);
    if (settings.load().executionRole !== 'central_executor') {
      throw Object.assign(new Error('Kiểm tra liên kết tài khoản chỉ khả dụng cho central executor đã được kích hoạt.'), {
        code: 'CONTROL_PLANE_AUTHORITY_STATUS_ROLE_REQUIRED'
      });
    }
    return controlPlaneEnrollment.reconcileAuthorityStatus({
      deviceIdentity: loadOrCreateDeviceIdentity(runtimePaths)
    });
  }));
  secureHandle('control-plane:rotate-credential', (event, request) => invokeSafely(async () => {
    // Rotation is an owner-only local action.  The node agent creates and
    // persists the candidate; renderer/IPC never receives either credential.
    assertManagerIpc(event);
    if (settings.load().executionRole !== 'central_executor') {
      throw Object.assign(new Error('Đổi credential Ubuntu chỉ khả dụng cho central executor đã được kích hoạt.'), {
        code: 'CONTROL_PLANE_CREDENTIAL_ROTATION_ROLE_REQUIRED'
      });
    }
    if (request?.confirmRotation !== true) {
      throw Object.assign(new Error('Chủ máy phải xác nhận trước khi đổi credential node.'), {
        code: 'CONTROL_PLANE_CREDENTIAL_ROTATION_CONFIRMATION_REQUIRED'
      });
    }
    return controlPlaneEnrollment.rotateCredential({
      deviceIdentity: loadOrCreateDeviceIdentity(runtimePaths)
    });
  }));
  secureHandle('control-plane:register-workspace', (event, request) => invokeSafely(async () => {
    // This records only an opaque workspace identity/generation and the
    // owner-selected local capability inventory with Ubuntu.  The selected
    // local path is canonicalized by the node agent and never sent to Ubuntu,
    // while this action neither changes the global active workspace nor
    // creates a task binding, context, policy, or per-task authority.
    assertManagerIpc(event);
    if (settings.load().executionRole !== 'central_executor') {
      throw Object.assign(new Error('Đăng ký workspace Ubuntu chỉ khả dụng cho central executor đã được kích hoạt.'), {
        code: 'CONTROL_PLANE_WORKSPACE_ROLE_REQUIRED'
      });
    }
    return controlPlaneEnrollment.registerWorkspace({
      workspacePath: request?.workspacePath,
      capabilities: request?.capabilities
    });
  }));
  secureHandle('control-plane:activate-workspace', (event, request) => invokeSafely(async () => {
    assertManagerIpc(event);
    if (settings.load().executionRole !== 'central_executor') {
      throw Object.assign(new Error('Kích hoạt thư mục yêu cầu máy đã kết nối Ubuntu.'), { code: 'CONTROL_PLANE_WORKSPACE_ROLE_REQUIRED' });
    }
    if (request?.confirmActivate !== true) {
      throw Object.assign(new Error('Chủ máy cần xác nhận thư mục trước khi kích hoạt.'), { code: 'CONTROL_PLANE_WORKSPACE_ACTIVATION_CONFIRMATION_REQUIRED' });
    }
    const census = await canonicalLedgerCensus({ paths: runtimePaths, workspace: settings.load().workspace, allowAcceptancePending: true });
    const counts = ['active_tool_calls', 'active_commands', 'starting_commands', 'active_background_operations',
      'active_managed_processes', 'foreign_heavy_processes', 'active_agent_lanes', 'owned_codex_sidecar_residues'];
    if (!Array.isArray(census.lifecycle?.blockers)
      || census.lifecycle.blockers.some((reason) => reason !== 'live_runtime_state_process')
      || (census.safe !== true && census.reason !== 'live_runtime_state_process')
      || census.lifecycle.unexplained_active_runs !== 0 || census.lifecycle.unbound_live_resource_residues !== 0
      || counts.some((key) => census.counts?.[key] !== 0)) {
      throw Object.assign(new Error('Có công việc đang chạy hoặc trạng thái chưa rõ. Hoàn tất công việc rồi thêm thư mục lại.'), { code: 'CONTROL_PLANE_WORKSPACE_ACTIVE_WORK' });
    }
    const workspaceRoot = controlPlaneEnrollment.registeredWorkspaceRoot({
      workspaceId: request?.workspaceId, workspaceGeneration: request?.workspaceGeneration
    });
    const currentSettings = settings.load();
    const roots = Array.isArray(currentSettings.authorizedRoots) ? currentSettings.authorizedRoots : [];
    const key = (value) => path.normalize(value).toLowerCase();
    if (key(workspaceRoot) !== key(currentSettings.workspace) && !roots.some((root) => key(root) === key(workspaceRoot))) {
      if (roots.length >= 32) {
        throw Object.assign(new Error('Đã đạt giới hạn thư mục được cho phép trên máy này.'), { code: 'CONTROL_PLANE_WORKSPACE_ROOT_LIMIT' });
      }
      // Preserve the native default root and epoch; grant this owner-selected
      // root through the existing native authorization API before pilot switch.
      await orchestrator.updateAuthorizedRoots([...roots, workspaceRoot]);
    }
    return controlPlaneEnrollment.activateWorkspace({
      workspaceId: request?.workspaceId, workspaceGeneration: request?.workspaceGeneration, confirmActivate: true
    });
  }));
  secureHandle('control-plane:replace-workspace', (event, request) => invokeSafely(async () => {
    // Replacement is deliberately separate from registration.  It requires
    // an explicit local confirmation and the packaged node-agent journals the
    // retire/register generation transition so a lost ACK cannot overwrite a
    // previously trusted root silently.
    assertManagerIpc(event);
    if (settings.load().executionRole !== 'central_executor') {
      throw Object.assign(new Error('Thay capability workspace Ubuntu chỉ khả dụng cho central executor đã được kích hoạt.'), {
        code: 'CONTROL_PLANE_WORKSPACE_ROLE_REQUIRED'
      });
    }
    if (request?.confirmReplace !== true) {
      throw Object.assign(new Error('Chủ máy phải xác nhận trước khi thay capability workspace cục bộ.'), {
        code: 'CONTROL_PLANE_WORKSPACE_REPLACEMENT_CONFIRMATION_REQUIRED'
      });
    }
    return controlPlaneEnrollment.replaceWorkspace({
      workspacePath: request?.workspacePath,
      workspaceId: request?.workspaceId,
      workspaceGeneration: request?.workspaceGeneration,
      capabilities: request?.capabilities
    });
  }));
  secureHandle('control-plane:list-workspaces', (event) => invokeSafely(async () => {
    // This reads the node-private, path-free inventory through the packaged
    // agent. It does not call Ubuntu, create a binding, or imply task
    // authority; it only lets the local owner select a registered root to
    // retire deliberately.
    assertManagerIpc(event);
    if (settings.load().executionRole !== 'central_executor') {
      throw Object.assign(new Error('Danh sách workspace Ubuntu chỉ khả dụng cho central executor đã được kích hoạt.'), {
        code: 'CONTROL_PLANE_WORKSPACE_ROLE_REQUIRED'
      });
    }
    return controlPlaneEnrollment.listWorkspaces();
  }));
  secureHandle('control-plane:install-read-only-policy-assignment', (event, request) => invokeSafely(async () => {
    // The local owner must explicitly approve this effect for one already
    // registered opaque workspace.  This IPC neither accepts a context ID nor
    // creates a binding/context; Ubuntu may return a policy only for an
    // existing, live internal assignment that exactly matches the node root.
    assertManagerIpc(event);
    if (settings.load().executionRole !== 'central_executor') {
      throw Object.assign(new Error('Đồng bộ policy read-only chỉ khả dụng cho central executor đã được kích hoạt.'), {
        code: 'CONTROL_PLANE_POLICY_ROLE_REQUIRED'
      });
    }
    if (request?.confirmInstall !== true) {
      throw Object.assign(new Error('Chủ máy phải xác nhận trước khi ghi read-only policy cục bộ.'), {
        code: 'CONTROL_PLANE_POLICY_CONFIRMATION_REQUIRED'
      });
    }
    if (typeof request?.replaceExisting !== 'boolean') {
      throw Object.assign(new Error('Lựa chọn thay thế policy cục bộ không hợp lệ.'), {
        code: 'CONTROL_PLANE_POLICY_REPLACE_INVALID'
      });
    }
    return controlPlaneEnrollment.installReadOnlyPolicyAssignment({
      workspaceId: request?.workspaceId,
      workspaceGeneration: request?.workspaceGeneration,
      replaceExisting: request.replaceExisting
    });
  }));
  secureHandle('control-plane:install-standing-file-policies', (event, request) => invokeSafely(async () => {
    assertManagerIpc(event);
    if (settings.load().executionRole !== 'central_executor') {
      throw Object.assign(new Error('Quyền đọc/sửa file Ubuntu chỉ khả dụng cho central executor đã được kích hoạt.'), {
        code: 'CONTROL_PLANE_FILE_POLICY_ROLE_REQUIRED'
      });
    }
    if (request?.confirmInstall !== true) {
      throw Object.assign(new Error('Chủ máy phải xác nhận phạm vi workspace trước khi cài quyền đọc/sửa file.'), {
        code: 'CONTROL_PLANE_FILE_POLICY_CONFIRMATION_REQUIRED'
      });
    }
    if (typeof request?.allowWrite !== 'boolean' || typeof request?.replaceExisting !== 'boolean') {
      throw Object.assign(new Error('Lựa chọn quyền file cục bộ không hợp lệ.'), {
        code: 'CONTROL_PLANE_FILE_POLICY_REQUEST_INVALID'
      });
    }
    return controlPlaneEnrollment.installStandingWorkspaceFilePolicies({
      workspaceId: request?.workspaceId,
      workspaceGeneration: request?.workspaceGeneration,
      allowWrite: request.allowWrite,
      replaceExisting: request.replaceExisting
    });
  }));
  secureHandle('control-plane:inspect-standing-file-policies', (event, request) => invokeSafely(async () => {
    assertManagerIpc(event);
    if (settings.load().executionRole !== 'central_executor') {
      throw Object.assign(new Error('Kiểm tra quyền file Ubuntu chỉ khả dụng cho central executor đã được kích hoạt.'), {
        code: 'CONTROL_PLANE_FILE_POLICY_ROLE_REQUIRED'
      });
    }
    return controlPlaneEnrollment.inspectStandingWorkspaceFilePolicies({
      workspaceId: request?.workspaceId, workspaceGeneration: request?.workspaceGeneration
    });
  }));
  secureHandle('control-plane:install-exec-policy', (event, request) => invokeSafely(async () => {
    assertManagerIpc(event);
    if (settings.load().executionRole !== 'central_executor') {
      throw Object.assign(new Error('Sandboxed exec Ubuntu chỉ khả dụng cho central executor đã được kích hoạt.'), {
        code: 'CONTROL_PLANE_EXEC_POLICY_ROLE_REQUIRED'
      });
    }
    if (request?.confirmInstall !== true || request?.replaceExisting !== true) {
      throw Object.assign(new Error('Chủ máy phải xác nhận cài hoặc thay policy exec cho đúng workspace generation.'), {
        code: 'CONTROL_PLANE_EXEC_POLICY_CONFIRMATION_REQUIRED'
      });
    }
    return controlPlaneEnrollment.installStandingWorkspaceExecPolicy({
      workspaceId: request?.workspaceId,
      workspaceGeneration: request?.workspaceGeneration,
      replaceExisting: request.replaceExisting,
      probeSandbox: request.probeSandbox === undefined ? false : request.probeSandbox,
      executionMode: request?.executionMode,
      nativeArgvPrefixes: request?.nativeArgvPrefixes
    });
  }));
  secureHandle('control-plane:inspect-exec-policy', (event, request) => invokeSafely(async () => {
    assertManagerIpc(event);
    if (settings.load().executionRole !== 'central_executor') {
      throw Object.assign(new Error('Kiểm tra sandbox exec Ubuntu chỉ khả dụng cho central executor đã được kích hoạt.'), {
        code: 'CONTROL_PLANE_EXEC_POLICY_ROLE_REQUIRED'
      });
    }
    return controlPlaneEnrollment.inspectStandingWorkspaceExecPolicy({
      workspaceId: request?.workspaceId,
      workspaceGeneration: request?.workspaceGeneration,
      probeSandbox: request?.probeSandbox === true,
      executionMode: request?.executionMode
    });
  }));
  secureHandle('control-plane:retire-workspace', (event, request) => invokeSafely(async () => {
    // Retirement is an exact opaque identity/generation operation. The node
    // retains its local registry until the central service confirms the
    // retirement receipt, so a lost response can be retried safely.
    assertManagerIpc(event);
    if (settings.load().executionRole !== 'central_executor') {
      throw Object.assign(new Error('Thu hồi workspace Ubuntu chỉ khả dụng cho central executor đã được kích hoạt.'), {
        code: 'CONTROL_PLANE_WORKSPACE_ROLE_REQUIRED'
      });
    }
    return controlPlaneEnrollment.retireWorkspace({
      workspaceId: request?.workspaceId,
      workspaceGeneration: request?.workspaceGeneration
    });
  }));
  secureHandle('workspace:switch', (_event, workspace) => invokeSafely(() => orchestrator.switchWorkspace(workspace)));
  secureHandle('workspace:authorized-roots', (_event, roots) => invokeSafely(() => orchestrator.updateAuthorizedRoots(roots)));
  secureHandle('workspace:choose-authorized-root', () => invokeSafely(async () => {
    const result = await dialog.showOpenDialog(chatWindow, { properties: ['openDirectory', 'createDirectory'] });
    if (result.canceled || !result.filePaths[0]) return null;
    const selected = path.resolve(result.filePaths[0]);
    const current = settings.load();
    const roots = Array.isArray(current.authorizedRoots) ? current.authorizedRoots : [];
    const key = selected.toLowerCase();
    const merged = roots.some((item) => String(item).toLowerCase() === key) ? roots : [...roots, selected];
    const snapshot = await orchestrator.updateAuthorizedRoots(merged);
    return { selected, snapshot };
  }));
  secureHandle('task-state:read', () => invokeSafely(async () => {
    return canonicalTaskStateFromControl(await readOrchestrationControlSnapshot());
  }));
  secureHandle('task-state:clear', () => invokeSafely(() => panelTaskControl('clear')));
  secureHandle('task-state:pause', () => invokeSafely(() => panelTaskControl('pause')));
  secureHandle('task-state:resume', () => invokeSafely(() => panelTaskControl('resume')));
  secureHandle('task-state:stop', () => invokeSafely(() => panelTaskControl('stop')));
  secureHandle('task-state:history', () => invokeSafely(async () => {
    const control = await readOrchestrationControlSnapshot();
    const taskList = control?.task_list;
    if (taskList?.source !== 'orchestration_ledger') {
      throw new Error('MCP không trả task history canonical từ orchestration ledger.');
    }
    return Array.isArray(taskList.history) ? taskList.history : [];
  }));
  secureHandle('performance:read', () => invokeSafely(async () => {
    let performancePath;
    try { ({ performancePath } = workspaceStatePaths()); } catch { return null; }
    try { return JSON.parse(await fs.readFile(performancePath, 'utf8')); }
    catch (error) { if (error?.code === 'ENOENT') return null; throw error; }
  }));
  secureHandle('performance:clear', () => invokeSafely(async () => {
    const { performancePath } = workspaceStatePaths();
    await fs.rm(performancePath, { force: true });
    return true;
  }));
  secureHandle('build:inspect', () => invokeSafely(() => buildVerification.inspect(settings.load().workspace)));
  secureHandle('build:run', (_event, options) => invokeSafely(() => buildVerification.execute(settings.load().workspace, options || {})));
  secureHandle('health:inspect', () => invokeSafely(() => orchestrator.healthInspect()));
  secureHandle('health:repair', () => invokeSafely(() => orchestrator.healthRepair()));
  secureHandle('workspace:choose-and-switch', () => invokeSafely(async () => { const result = await dialog.showOpenDialog(chatWindow, { properties: ['openDirectory', 'createDirectory'] }); if (result.canceled) return null; return orchestrator.switchWorkspace(result.filePaths[0]); }));
  secureHandle('manager:close', () => invokeSafely(async () => {
    if (chatWindow && !chatWindow.isDestroyed()) chatWindow.close();
    return true;
  }));
  secureHandle('manager:open', (_event, page) => invokeSafely(async () => { openManagerWindow(page); return true; }));
  secureHandle('panel:toggle', () => invokeSafely(async () => ({ visible: togglePanel() })));
  secureHandle('panel:visibility', () => invokeSafely(async () => ({ visible: false })));
  secureHandle('panel:live-control', (event) => invokeSafely(async () => {
    const startedAt = nodePerformance.now();
    const current = settings.load();
    const token = secrets.get('mcpAuthToken');
    if (!token) throw new Error('MCP chưa sẵn sàng để đọc trạng thái điều tuyến trực tiếp.');
    const orchestration = await httpRequestJson({
      port: current.mcpPort,
      path: '/__control/orchestration/live',
      method: 'GET',
      token,
      timeout: PANEL_LIVE_CONTROL_TIMEOUT_MS
    });
    if (isManagerIpc(event)) {
      uiPerformanceMetrics.recordMain({
        observed_at_unix_ms: Date.now(),
        orchestration_build_ms: nodePerformance.now() - startedAt,
        orchestration_size_bytes: jsonByteLength(orchestration)
      });
      const progressObservation = executionControlCenterProgressObservation(orchestration);
      if (progressObservation && typeof orchestrator?.recordExecutionControlCenterProgress === 'function') {
        void orchestrator.recordExecutionControlCenterProgress(progressObservation).catch((error) => {
          log.warn('Khong the ghi Control Center progress receipt vao EOCL ledger', {
            stage: 'execution-control-center-observation',
            code: error?.code || '',
            error: safeMessage(error)
          });
        });
      }
    }
    return orchestration;
  }));
  secureHandle('panel:dashboard-analytics', () => invokeSafely(async () => {
    const current = settings.load();
    const token = secrets.get('mcpAuthToken');
    if (!token) throw new Error('MCP chưa sẵn sàng để đọc analytics bảng điều khiển.');
    return httpRequestJson({
      port: current.mcpPort,
      path: '/__control/orchestration/analytics',
      method: 'GET',
      token,
      timeout: PANEL_ANALYTICS_TIMEOUT_MS
    });
  }));
  secureHandle('panel:orchestration', () => invokeSafely(async () => {
    return readOrchestrationControlSnapshot();
  }));
  secureHandle('panel:task-control', (_event, action) => invokeSafely(() => panelTaskControl(String(action || ''))));
  secureHandle('p5-a0:control', (_event, action) => invokeSafely(() => panelP5A0Control(String(action || ''))));
  secureHandle('panel:transfer-controller', (_event, payload) => invokeSafely(async () => {
    const current = settings.load();
    const token = secrets.get('mcpAuthToken');
    if (!token) throw new Error('MCP chưa sẵn sàng để chuyển controller.');
    const targetClientId = String(payload?.targetClientId || '').trim();
    if (!['chatweb', 'codex-desktop'].includes(targetClientId)) throw new Error('Controller target không hợp lệ.');
    const runId = String(payload?.runId || '').trim();
    return httpRequestJson({
      port: current.mcpPort,
      path: '/__control/hub',
      method: 'POST',
      token,
      body: { action: 'transfer_controller', target_client_id: targetClientId, ...(runId ? { run_id: runId } : {}) },
      timeout: 5000
    });
  }));
  secureHandle('panel:copy-codex-config', () => invokeSafely(async () => {
    const python = await pythonStatus();
    if (!python.installed) throw new Error('Không tìm thấy Python 3.11+ để tạo cấu hình Codex Desktop.');
    const moduleRoot = path.join(resourcesRoot(), 'coding-tools-mcp');
    const pythonPath = [path.join(moduleRoot, 'python_vendor'), moduleRoot].join(path.delimiter);
    const config = buildCodexDesktopMcpConfig({
      pythonCommand: python.command,
      prefixArgs: python.prefixArgs || [],
      pythonPath,
      descriptorPath: hubProxyDescriptorFile()
    });
    clipboard.writeText(config.toml);
    return { copied: true, mode: config.mode, descriptorPath: config.descriptorPath, containsBearer: false };
  }));
  secureHandle('panel:handoff', (_event, payload) => invokeSafely(async () => {
    const current = settings.load();
    const token = secrets.get('mcpAuthToken');
    if (!token) throw new Error('MCP chưa sẵn sàng để ghi capsule handoff.');
    const runId = typeof payload?.runId === 'string' ? payload.runId.trim() : '';
    if (!runId) throw new Error('Chọn RUN hiện tại trước khi ghi capsule handoff.');
    const summaryText = String((payload && payload.summary) || '').slice(0, 600);
    const request = {
      jsonrpc: '2.0',
      id: `panel-handoff-${Date.now()}`,
      method: 'tools/call',
      params: {
        name: 'task_control',
        arguments: { action: 'handoff', handoff_action: 'record', run_id: runId, payload: { panel_summary: summaryText } },
        _meta: {
          'io.modelcontextprotocol/protocolVersion': '2026-07-28',
          'io.modelcontextprotocol/clientCapabilities': {},
          'io.modelcontextprotocol/clientInfo': { name: 'coding-tools-mcp-panel', version: app.getVersion() }
        }
      }
    };
    const response = await httpRequestJson({
      port: current.mcpPort,
      path: '/mcp',
      method: 'POST',
      token,
      body: request,
      headers: {
        'MCP-Protocol-Version': '2026-07-28',
        'Mcp-Method': 'tools/call',
        'Mcp-Name': 'task_control',
        'X-Coding-Tools-Client-Id': 'electron-panel',
        'X-Coding-Tools-Client-Type': 'electron'
      },
      timeout: 10000
    });
    if (response && response.error) throw new Error(response.error.message || 'MCP từ chối thao tác handoff.');
    return (response && response.result) || null;
  }));
  secureHandle('dialog:workspace', () => invokeSafely(async () => {
    const result = await dialog.showOpenDialog(chatWindow, { properties: ['openDirectory', 'createDirectory'] });
    return result.canceled ? '' : result.filePaths[0];
  }));
  secureHandle('dialog:files', () => invokeSafely(async () => {
    const result = await dialog.showOpenDialog(chatWindow, { properties: ['openFile', 'multiSelections'] });
    return result.canceled ? [] : result.filePaths;
  }));
  secureHandle('settings:save', (_event, patch) => invokeSafely(async () => {
    // Recovery settings stay explicitly operator-controlled and separate from the primary runtime failure domain.
    const allowed = ['permissionMode', 'executionMode', 'toolMode', 'mcpPort', 'healthPort', 'recoveryMcpPort', 'recoveryHealthPort', 'proxyMode', 'proxyUrl', 'tunnelId', 'tunnelProfile', 'recoveryTunnelId', 'recoveryTunnelProfile', 'controlPlaneServerUrl', 'cosCompanionEnabled', 'cosCompanionUserDataDir', 'startWithWindows', 'autoStartServices', 'keepRunningOnClose', 'progressReportSeconds', 'theme', 'guideProgress', 'firstRunCompleted', 'costPreset', 'costRateInUsd', 'costRateOutUsd', 'costCurrency', 'costFxRate', 'costBytesPerToken', 'costLaneRates'];
    const clean = Object.fromEntries(Object.entries(patch || {}).filter(([key]) => allowed.includes(key)));
    const saved = settings.save(clean);
    if (Object.hasOwn(clean, 'startWithWindows')) {
      app.setLoginItemSettings({
        openAtLogin: Boolean(saved.startWithWindows),
        path: process.execPath,
        args: recoveryLoginItemArguments(app)
      });
    }
    clearProxyCache();
    return saved;
  }));
  secureHandle('environment:detect-proxy', () => invokeSafely(async () => resolveProxy(settings.load(), { force: true })));
  secureHandle('secrets:runtime-key', (_event, value) => invokeSafely(async () => {
    if (String(value || '').trim().length < 12) throw new Error('Độ dài Runtime API Key không hợp lệ.');
    secrets.set('runtimeApiKey', value);
    return secrets.status();
  }));
  secureHandle('secrets:runtime-key-remove', () => invokeSafely(async () => {
    secrets.remove('runtimeApiKey');
    return secrets.status();
  }));
  secureHandle('secrets:mcp-token-regenerate', () => invokeSafely(async () => {
    secrets.set('mcpAuthToken', crypto.randomBytes(32).toString('base64url'));
    return secrets.status();
  }));
  secureHandle('runtime:handoff-central-executor', (event) => invokeSafely(async () => {
    // The renderer may request this one-way role change only from the local
    // Manager. It never supplies a role, credential, Tunnel, or workspace:
    // this is an operator configuration migration, not accepted-code activation.
    // FullCleanActivation still owns the ledger census, fence and role commit.
    assertManagerIpc(event);
    const current = settings.load();
    if (current.executionRole === 'central_executor') {
      const snapshot = await orchestrator.snapshot({ force: true, reason: 'central-executor-handoff-state' });
      const epoch = snapshot?.recoveryHost?.activation_epoch || snapshot?.status?.activationEpoch || {};
      const epochState = epoch.epoch_state || epoch.state;
      const expired = epoch.stale === true || (!['READY', 'FAILED'].includes(epochState)
        && Number(epoch.expires_at_unix_ms) > 0 && Number(epoch.expires_at_unix_ms) <= Date.now());
      // Pairing is available while VERIFYING. Do not replace that active
      // operation on repeated clicks; a failed/expired migration can be retried
      // explicitly after the operator has finished pairing and local policy.
      if (!expired && !['FAILED', 'UPDATE_INCOMPLETE', 'NONE'].includes(epochState)) return snapshot;
    }
    return orchestrator.restart({
      reason: 'operator_central_executor_handoff',
      executionRole: 'central_executor',
      mode: 'full_clean_execution_role_handoff'
    });
  }));
  secureHandle('runtime:start', () => invokeSafely(() => orchestrator.start()));
  secureHandle('runtime:stop', () => invokeSafely(() => orchestrator.stop()));
  secureHandle('runtime:restart', () => invokeSafely(async () => orchestrator.restart(await fullCleanRestartOptions())));
  secureHandle('code:activation-preflight', (_event, component, allowAcceptancePending) => invokeSafely(async () => {
    const request = await codeActivationRequest(component, allowAcceptancePending);
    return { request, preflight: await orchestrator.activationPreflight(request) };
  }));
  secureHandle('code:activate-update', (_event, component, allowAcceptancePending) => invokeSafely(async () => {
    const request = await codeActivationRequest(component, allowAcceptancePending);
    const result = await orchestrator.activateUpdate(request);
    if (component === 'electron_ui') setImmediate(() => registerUiRevision().catch(() => {}));
    return result;
  }));
  secureHandle('code:activation-status', (_event, operationId) => invokeSafely(() => orchestrator.activationStatus(operationId)));
  secureHandle('connector:ack-contract', () => invokeSafely(() => orchestrator.acknowledgeConnectorContract()));
  secureHandle('logs:read', () => invokeSafely(() => orchestrator.readLogs()));
  secureHandle('logs:clear', () => invokeSafely(() => orchestrator.clearLogs()));
  secureHandle('environment:install-python', () => invokeSafely(async () => {
    const result = await run('winget.exe', ['install', '--id', 'Python.Python.3.12', '-e', '--accept-source-agreements', '--accept-package-agreements']);
    return result.stdout;
  }));
  secureHandle('shell:open', (_event, target) => invokeSafely(async () => {
    const allowed = new Set(['chatgpt-connectors', 'openai-tunnels', 'openai-runtime-keys', 'tunnel-ui', 'coding-tools-source']);
    if (!allowed.has(target)) throw new Error('Không được phép mở địa chỉ này.');
    const current = settings.load();
    const urls = {
      'chatgpt-connectors': 'https://chatgpt.com/#settings/Connectors',
      'openai-tunnels': 'https://platform.openai.com/settings/organization/tunnels',
      'openai-runtime-keys': 'https://platform.openai.com/settings/organization/api-keys',
      'tunnel-ui': `http://127.0.0.1:${current.healthPort}/ui`,
      'coding-tools-source': 'https://github.com/xyTom/coding-tools-mcp'
    };
    await shell.openExternal(urls[target]);
    return true;
  }));
}

if (recoveryHostMode) {
  app.whenReady().then(() => startRecoveryHostApplication(app));
} else {
  const hasSingleInstanceLock = requestUiSingleInstanceLock();
  if (!hasSingleInstanceLock) {
    process.stderr.write(`${existingInstanceDiagnostic()}\n`);
    app.quit();
  } else {
    app.on('second-instance', (_event, commandLine, _workingDirectory, additionalData) => handleSecondInstance(commandLine, additionalData));

    app.whenReady().then(async () => {
    app.setLoginItemSettings({
      openAtLogin: Boolean(settings.load().startWithWindows),
      path: process.execPath,
      args: recoveryLoginItemArguments(app)
    });
    session.defaultSession.setPermissionRequestHandler((_webContents, _permission, callback) => callback(false));
    session.defaultSession.setPermissionCheckHandler(() => false);
    app.on('web-contents-created', (_event, contents) => {
      contents.on('will-attach-webview', (event) => event.preventDefault());
    });
    createTray();
    try {
      orchestrator = await ensureRecoveryHost({ app, paths: runtimePaths, log });
    } catch (error) {
      recoveryHostConnectionError = {
        code: String(error?.code || 'RECOVERY_HOST_CONNECT_FAILED'),
        message: String(error?.message || 'Recovery Host connection failed.'),
        details: error?.details && typeof error.details === 'object' ? error.details : null
      };
      // A descriptor from another checkout/installation is still useful for
      // a read-only diagnostic snapshot (so the UI can explain the mismatch),
      // but it must never become the mutation authority for this window.  The
      // client therefore permits status/snapshot reads while refusing every
      // mutating RPC until the operator relaunches against the matching host.
      orchestrator = new RecoveryIpcClient({
        paths: runtimePaths,
        readOnlyError: recoveryHostConnectionError
      });
      log.error(error.message, { stage: 'recovery-host-connect', code: error?.code || '' });
    }
    buildVerification = new BuildVerificationService(log, (payload) => sendManager('build:progress', payload));
    log.on('entry', (payload) => sendManager('logs:entry', payload));
    registerIpc();
    createChatWindow();
    const publishRuntimeHeartbeat = () => {
      if (runtimeHeartbeatInFlight) return runtimeHeartbeatInFlight;
      const operation = orchestrator.lightweightSnapshot().then((status) => {
        status = decorateUiRuntimeSnapshot(status);
        const progress = status?.recoveryHost?.last_progress;
        if (progress?.time && progress.time !== lastRecoveryProgressTime) {
          lastRecoveryProgressTime = progress.time;
          sendManager('runtime:progress', progress);
        }
        sendManager('runtime:heartbeat', status);
      }).then(() => registerUiRevision()).catch(() => {});
      runtimeHeartbeatInFlight = operation;
      return operation.finally(() => {
        if (runtimeHeartbeatInFlight === operation) runtimeHeartbeatInFlight = null;
      });
    };
    setInterval(() => { void publishRuntimeHeartbeat(); }, 5000).unref();
    log.info('Coding Tools MCP UI đã kết nối Recovery Host');
    });

    app.on('before-quit', () => {
      forceQuit = true;
      void uiPerformanceMetrics.flush().catch(() => {});
    });
    app.on('window-all-closed', () => {
      if (!forceQuit && settings.load().keepRunningOnClose) return;
      if (!forceQuit) app.quit();
    });
    app.on('activate', () => showChatWindow());
  }
}
