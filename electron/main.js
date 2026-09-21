const path = require('node:path');
const fs = require('node:fs/promises');
const crypto = require('node:crypto');
const http = require('node:http');
const { performance: nodePerformance } = require('node:perf_hooks');
const { app, BrowserWindow, dialog, ipcMain, shell, Tray, Menu, nativeImage, session, WebContentsView, clipboard } = require('electron');
const { SettingsStore } = require('./services/settingsStore');
const { SecretStore } = require('./services/secretStore');
const { LogService } = require('./services/logService');
const { EnvironmentService, pythonStatus } = require('./services/environmentService');
const { ChatViewController } = require('./chatViewController');
const { ChatEvaluationJournal } = require('./services/chatEvaluationJournal');
const { buildExact: buildExactTokenMeasurement } = require('./services/tokenMeasurement');
const { run } = require('./services/commandRunner');
const { resolveProxy, clearProxyCache } = require('./services/proxyService');
const { BuildVerificationService } = require('./services/buildVerificationService');
const { buildCodexDesktopMcpConfig } = require('./services/codexDesktopConfig');
const { readJson, writeJsonAtomic } = require('./services/jsonStore');
const { panelInset, panelBounds } = require('./services/panelLayout');
const runtimePathApi = require('./paths');
const { resourcesRoot, hubProxyDescriptorFile } = runtimePathApi;
const { createElectronRuntimePaths, configureElectronUserDataPath } = require('./services/runtimePaths');
const { RecoveryIpcClient } = require('./services/recoveryIpc');
const {
  ensureRecoveryHost,
  recoveryLoginItemArguments,
  electronUiArguments,
  assertActivationDeadline
} = require('./services/recoveryHostLauncher');
const { ComponentRevisionTracker } = require('./services/componentRevision');
const { activationSourceCheckpoint } = require('./services/activationClosure');
const { startRecoveryHostApplication } = require('./recoveryHost');
const { UiPerformanceMetrics, jsonByteLength } = require('./services/uiPerformanceMetrics');
const { loadOrCreateDeviceIdentity } = require('./services/deviceIdentity');
const { ControlPlaneEnrollmentService } = require('./services/controlPlaneEnrollment');

// Version 1.0 has a new product identity but retains the existing encrypted
// desktop profile so an upgrade does not orphan its runtime configuration.
const recoveryHostMode = process.argv.includes('--recovery-host') || process.env.WEBCODEX_PROCESS_ROLE === 'recovery-host';
app.setName('Coding Tools MCP');
configureElectronUserDataPath(app, { argv: process.argv, recoveryHostMode });

let chatWindow;
let managerWindow;
let tokenWindow;
let chatController;
let orchestrator;
let forceQuit = false;
let tray = null;
let buildVerification;
let panelView = null;
let panelVisible = false;
let lastRecoveryProgressTime = '';
let runtimeHeartbeatInFlight = null;
const TOOLBAR_HEIGHT = 112;
const PANEL_ORCHESTRATION_TIMEOUT_MS = 10000;
const PANEL_LIVE_CONTROL_TIMEOUT_MS = 2500;
const PANEL_ANALYTICS_TIMEOUT_MS = 10000;
const runtimePaths = createElectronRuntimePaths(app);
runtimePathApi.configureRuntimePaths(runtimePaths);
const settings = new SettingsStore(runtimePaths);
const secrets = new SecretStore(runtimePaths);
const log = new LogService(runtimePaths);
const environment = new EnvironmentService(runtimePaths);
const chatEvaluationJournal = new ChatEvaluationJournal();
const controlPlaneEnrollment = new ControlPlaneEnrollmentService({ paths: runtimePaths });
const uiRevisionTracker = new ComponentRevisionTracker({ paths: runtimePaths });
const uiInstanceId = crypto.randomBytes(16).toString('hex');
const uiStartedAtUnixMs = Date.now();
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

function handleSecondInstance(commandLine = []) {
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
  return 'Coding Tools MCP UI is already running. Use "npm run dev" to inspect/activate the current checkout or "npm run dev:replace" for a verified replacement.';
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
  if (managerWindow && !managerWindow.isDestroyed()) managerWindow.webContents.send(channel, payload);
}

function safeMessage(error) {
  return error instanceof Error ? error.message : String(error);
}

function assertTrustedIpc(event) {
  const url = event.senderFrame?.url || event.sender?.getURL?.() || '';
  if (!url.startsWith('file://')) throw new Error('Đã chặn cuộc gọi IPC từ trang không phải cục bộ.');
}

function isManagerIpc(event) {
  return Boolean(
    managerWindow
    && !managerWindow.isDestroyed()
    && managerWindow.webContents
    && !managerWindow.webContents.isDestroyed()
    && event?.sender === managerWindow.webContents
  );
}

function assertManagerIpc(event) {
  if (!isManagerIpc(event)) throw new Error('Đã chặn telemetry UI từ cửa sổ không phải Command Center.');
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

async function recordHostObservationSpan(event) {
  if (!event || event.event_type !== 'host_turn_span' || !event.run_id || !event.wave_id || !event.trace_id || !event.turn_id) return false;
  const current = settings.load();
  const token = secrets.get('mcpAuthToken');
  if (!token) return false;
  const request = {
    jsonrpc: '2.0',
    id: `host-observation-${Date.now()}`,
    method: 'tools/call',
    params: {
      name: 'task_control',
      arguments: {
        action: 'observation',
        run_id: event.run_id,
        wave_id: event.wave_id,
        observation_span: {
          span_id: event.span_id,
          stage: 'report_visible',
          source: 'electron_chatgpt_dom',
          measurement: event.measurement,
          clock_domain: event.clock_domain,
          start_ms: event.start_ms,
          end_ms: event.end_ms,
          observer_plane: 'electron_chatgpt_dom',
          trace_id: event.trace_id,
          turn_id: event.turn_id
        }
      },
      _meta: {
        'io.modelcontextprotocol/protocolVersion': '2026-07-28',
        'io.modelcontextprotocol/clientCapabilities': {},
        'io.modelcontextprotocol/clientInfo': { name: 'coding-tools-mcp-host-observer', version: app.getVersion() }
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
      'X-Coding-Tools-Client-Id': 'electron-host-observer',
      'X-Coding-Tools-Client-Type': 'electron'
    },
    timeout: 5000
  });
  if (response?.error || response?.result?.isError) throw new Error(response?.error?.message || response?.result?.structuredContent?.error?.message || 'MCP rejected host observation.');
  return true;
}

async function recordControllerUsageReceipt(event) {
  if (!event || event.event_type !== 'controller_usage' || !event.run_id || !event.wave_id) return false;
  // Single validation authority: the shared token measurement contract
  // enforces exact-integer counters, relations and identity shape.
  const measured = buildExactTokenMeasurement({
    turn_id: event.turn_id,
    trace_id: event.trace_id,
    input_tokens: event.input_tokens,
    cached_input_tokens: event.cached_input_tokens,
    output_tokens: event.output_tokens,
    reasoning_output_tokens: event.reasoning_output_tokens,
    model_id: event.model_id,
    accounting_profile: event.accounting_profile,
    source: event.source
  });
  if (!measured) return false;
  const current = settings.load();
  const token = secrets.get('mcpAuthToken');
  if (!token) return false;
  const controllerUsage = {
    schema_version: 1,
    run_id: event.run_id,
    wave_id: event.wave_id,
    turn_id: event.turn_id,
    trace_id: event.trace_id,
    accounting_profile: event.accounting_profile || 'openai_compatible',
    provider_id: event.provider_id || 'openai',
    ...(event.model_id ? { model_id: event.model_id } : {}),
    source: event.source || 'client_reported',
    input_tokens: event.input_tokens,
    cached_input_tokens: event.cached_input_tokens,
    output_tokens: event.output_tokens,
    reasoning_output_tokens: event.reasoning_output_tokens
  };
  const request = {
    jsonrpc: '2.0',
    id: `controller-usage-${Date.now()}`,
    method: 'tools/call',
    params: {
      name: 'task_control',
      arguments: { action: 'audit', run_id: event.run_id, wave_id: event.wave_id, limit: 1 },
      _meta: {
        'io.modelcontextprotocol/protocolVersion': '2026-07-28',
        'io.modelcontextprotocol/clientCapabilities': {},
        'io.modelcontextprotocol/clientInfo': { name: 'coding-tools-mcp-chatweb-usage-bridge', version: app.getVersion() },
        'io.coding-tools/controllerUsage': controllerUsage
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
      'X-Coding-Tools-Client-Id': 'chatweb',
      'X-Coding-Tools-Client-Type': 'chatweb'
    },
    timeout: 5000
  });
  if (response?.error || response?.result?.isError) {
    throw new Error(response?.error?.message || response?.result?.structuredContent?.error?.message || 'MCP rejected ChatWeb controller usage.');
  }
  return true;
}

function layoutViews() {
  if (!chatWindow || chatWindow.isDestroyed()) return;
  const [width, height] = chatWindow.getContentSize();
  if (chatController) chatController.setRightInset(panelInset(width, panelVisible));
  if (panelView && !panelView.webContents.isDestroyed()) {
    const bounds = panelBounds(width, height, TOOLBAR_HEIGHT, panelVisible);
    panelView.setBounds(bounds || { x: width, y: TOOLBAR_HEIGHT, width: 0, height: Math.max(0, height - TOOLBAR_HEIGHT) });
  }
}

function broadcastPanelVisibility() {
  if (chatWindow && !chatWindow.isDestroyed()) chatWindow.webContents.send('panel:visibility', { visible: panelVisible });
}

function createPanelView() {
  if (panelView && !panelView.webContents.isDestroyed()) return panelView;
  panelView = new WebContentsView({
    webPreferences: {
      preload: path.join(__dirname, 'panelPreload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });
  panelView.setBackgroundColor('#ffffff');
  chatWindow.contentView.addChildView(panelView);
  panelView.webContents.loadFile(path.join(__dirname, '..', 'renderer', 'panel.html'));
  return panelView;
}

function destroyPanelView() {
  if (!panelView) return;
  try { chatWindow?.contentView?.removeChildView(panelView); } catch { /* already detached */ }
  if (panelView.webContents && !panelView.webContents.isDestroyed()) panelView.webContents.close();
  panelView = null;
}

function togglePanel() {
  panelVisible = !panelVisible;
  if (panelVisible) createPanelView();
  else destroyPanelView();
  layoutViews();
  broadcastPanelVisibility();
  return panelVisible;
}

function createTray() {
  if (tray && !tray.isDestroyed()) return tray;
  const icon = nativeImage.createFromPath(appIconPath()).resize({ width: 16, height: 16 });
  tray = new Tray(icon);
  tray.setToolTip('Coding Tools MCP · Đang chạy ngầm');
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Mở Coding Tools MCP', click: () => showChatWindow() },
    { label: 'Mở Cấu hình Quản lý', click: () => { showChatWindow(); openManagerWindow(); } },
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
      preload: path.join(__dirname, 'browserPreload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });
  chatWindow.removeMenu();
  const openingWindow = chatWindow;
  const revealOpeningWindow = (attemptsRemaining = 20) => {
    if (openingWindow.isDestroyed()) return;
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
  chatWindow.loadFile(path.join(__dirname, '..', 'renderer', 'browser.html'));

  chatController = new ChatViewController({
    window: chatWindow,
    log,
    settings,
    toolbarHeight: 112,
    onState: (payload) => {
      if (chatWindow && !chatWindow.isDestroyed()) chatWindow.webContents.send('chat:state', payload);
    },
    onDownload: (payload) => {
      if (chatWindow && !chatWindow.isDestroyed()) chatWindow.webContents.send('chat:download', payload);
    },
    onEvaluation: async (events) => {
      const workspace = String(settings.load().workspace || '').trim();
      if (!workspace) return;
      let correlated = [];
      try {
        const productSessionEvents = chatEvaluationJournal.attachProductSession(
          workspace,
          events,
          chatController?.getState()?.url
        );
        chatEvaluationJournal.stagePendingTurns(workspace, productSessionEvents);
        chatEvaluationJournal.stagePendingContinuationConsents(workspace, productSessionEvents);
        correlated = chatEvaluationJournal.attachExplicitBindings(workspace, productSessionEvents);
        chatEvaluationJournal.append(workspace, correlated);
      } catch (error) {
        log.warn('Không thể ghi host-visible evaluation telemetry', { error: safeMessage(error) });
        return;
      }
      for (const event of correlated.filter((item) => ['host_turn_span', 'controller_usage'].includes(item?.event_type))) {
        try {
          if (event.run_id && event.wave_id && event.event_type === 'host_turn_span') await recordHostObservationSpan(event);
          if (event.run_id && event.wave_id && event.event_type === 'controller_usage') await recordControllerUsageReceipt(event);
        } catch (error) {
          log.warn('Không thể ghi ChatWeb host/controller telemetry vào EOCL ledger', {
            event_type: event.event_type,
            error: safeMessage(error)
          });
        } finally {
          chatEvaluationJournal.finalizeCorrelation(workspace, event);
        }
      }
    }
  });
  chatController.mount();
  chatWindow.on('resize', () => layoutViews());

  chatWindow.on('closed', () => {
    if (chatController) chatController.dispose();
    chatController = null;
    destroyPanelView();
    panelVisible = false;
    uiWindowReady = false;
    chatWindow = null;
    if (managerWindow && !managerWindow.isDestroyed()) managerWindow.destroy();
  });
  chatWindow.on('close', (event) => {
    if (forceQuit) return;
    event.preventDefault();
    if (settings.load().keepRunningOnClose) {
      if (managerWindow && !managerWindow.isDestroyed()) managerWindow.hide();
      chatWindow.hide();
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

function openManagerWindow() {
  if (managerWindow && !managerWindow.isDestroyed()) {
    managerWindow.show();
    managerWindow.focus();
    return managerWindow;
  }

  const chatBounds = chatWindow && !chatWindow.isDestroyed() ? chatWindow.getBounds() : null;
  const width = 980;
  const height = 720;
  const x = chatBounds ? Math.round(chatBounds.x + Math.max(0, (chatBounds.width - width) / 2)) : undefined;
  const y = chatBounds ? Math.round(chatBounds.y + Math.max(0, (chatBounds.height - height) / 2)) : undefined;

  managerWindow = new BrowserWindow({
    width,
    height,
    x,
    y,
    minWidth: 820,
    minHeight: 580,
    show: false,
    skipTaskbar: true,
    frame: false,
    transparent: false,
    backgroundColor: '#f7f7f8',
    title: 'Coding Tools MCP · Trung tâm Quản lý',
    icon: appIconPath(),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });
  managerWindow.removeMenu();
  const initialTheme = settings.load().theme === 'light' ? 'light' : 'dark';
  managerWindow.once('ready-to-show', () => managerWindow.show());
  managerWindow.loadFile(path.join(__dirname, '..', 'renderer', 'index.html'), { query: { theme: initialTheme } });
  managerWindow.on('close', (event) => {
    if (forceQuit) return;
    event.preventDefault();
    managerWindow.hide();
    if (chatWindow && !chatWindow.isDestroyed()) {
      chatWindow.show();
      chatWindow.focus();
    }
  });
  managerWindow.on('closed', () => { managerWindow = null; });
  return managerWindow;
}

function openTokenWindow() {
  if (tokenWindow && !tokenWindow.isDestroyed()) {
    tokenWindow.show();
    tokenWindow.focus();
    return tokenWindow;
  }

  tokenWindow = new BrowserWindow({
    width: 1100,
    height: 800,
    minWidth: 900,
    minHeight: 620,
    show: false,
    autoHideMenuBar: true,
    backgroundColor: '#0b0f19',
    title: 'Coding Tools MCP · Bảng Token',
    icon: appIconPath(),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });
  tokenWindow.removeMenu();
  const initialTheme = settings.load().theme === 'light' ? 'light' : 'dark';
  tokenWindow.once('ready-to-show', () => tokenWindow.show());
  tokenWindow.loadFile(path.join(__dirname, '..', 'renderer', 'token-dashboard.html'), { query: { theme: initialTheme } });
  // Destroy (not hide) on close so every open loads current disk files.
  tokenWindow.on('closed', () => { tokenWindow = null; });
  return tokenWindow;
}

function registerIpc() {
  secureHandle('app:snapshot', (_event, options) => invokeSafely(() => orchestrator.snapshot(options || {})));
  secureHandle('app:lightweight-snapshot', (event) => invokeSafely(async () => {
    const startedAt = nodePerformance.now();
    const snapshot = await orchestrator.lightweightSnapshot();
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
    return controlPlaneEnrollment.request({
      serverUrl,
      deviceIdentity: loadOrCreateDeviceIdentity(runtimePaths)
    });
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
    return controlPlaneEnrollment.reconcileEnrollment({
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
    if (managerWindow && !managerWindow.isDestroyed()) managerWindow.hide();
    if (chatWindow && !chatWindow.isDestroyed()) {
      chatWindow.show();
      chatWindow.focus();
    }
    return true;
  }));
  secureHandle('manager:open', () => invokeSafely(async () => { openManagerWindow(); return true; }));
  secureHandle('token-dashboard:open', () => invokeSafely(async () => { openTokenWindow(); return true; }));
  secureHandle('token-dashboard:close', () => invokeSafely(async () => {
    if (tokenWindow && !tokenWindow.isDestroyed()) tokenWindow.close();
    return true;
  }));
  secureHandle('chat:navigate', (_event, action) => invokeSafely(async () => chatController?.navigate(action)));
  secureHandle('chat:status', () => invokeSafely(async () => chatController?.getState() || null));
  secureHandle('panel:toggle', () => invokeSafely(async () => ({ visible: togglePanel() })));
  secureHandle('panel:visibility', () => invokeSafely(async () => ({ visible: panelVisible })));
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
  secureHandle('chat:clear-session', () => invokeSafely(async () => {
    if (!chatController) throw new Error('Trang ChatGPT chưa được khởi tạo.');
    await chatController.clearSession();
    return true;
  }));
  secureHandle('dialog:workspace', () => invokeSafely(async () => {
    const result = await dialog.showOpenDialog(managerWindow || chatWindow, { properties: ['openDirectory', 'createDirectory'] });
    return result.canceled ? '' : result.filePaths[0];
  }));
  secureHandle('settings:save', (_event, patch) => invokeSafely(async () => {
    // Recovery settings stay explicitly operator-controlled and separate from the primary runtime failure domain.
    const allowed = ['permissionMode', 'toolMode', 'mcpPort', 'healthPort', 'recoveryMcpPort', 'recoveryHealthPort', 'proxyMode', 'proxyUrl', 'tunnelId', 'tunnelProfile', 'recoveryTunnelId', 'recoveryTunnelProfile', 'startWithWindows', 'autoStartServices', 'keepRunningOnClose', 'progressReportSeconds', 'theme', 'guideProgress', 'firstRunCompleted', 'costPreset', 'costRateInUsd', 'costRateOutUsd', 'costCurrency', 'costFxRate', 'costBytesPerToken', 'costLaneRates'];
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
    if (target === 'chatgpt-connectors' && chatController) {
      await chatController.openUrl('https://chatgpt.com/#settings/Connectors');
      if (chatWindow && !chatWindow.isDestroyed()) {
        chatWindow.show();
        chatWindow.focus();
      }
      return true;
    }
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
  const hasSingleInstanceLock = app.requestSingleInstanceLock();
  if (!hasSingleInstanceLock) {
    process.stderr.write(`${existingInstanceDiagnostic()}\n`);
    app.quit();
  } else {
    app.on('second-instance', (_event, commandLine) => handleSecondInstance(commandLine));

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
      orchestrator = new RecoveryIpcClient({ paths: runtimePaths });
      log.error(error.message, { stage: 'recovery-host-connect', code: error?.code || '' });
    }
    buildVerification = new BuildVerificationService(log, (payload) => sendManager('build:progress', payload));
    log.on('entry', (payload) => sendManager('logs:entry', payload));
    registerIpc();
    createChatWindow();
    const publishRuntimeHeartbeat = () => {
      if (runtimeHeartbeatInFlight) return runtimeHeartbeatInFlight;
      const operation = orchestrator.lightweightSnapshot().then((status) => {
        const progress = status?.recoveryHost?.last_progress;
        if (progress?.time && progress.time !== lastRecoveryProgressTime) {
          lastRecoveryProgressTime = progress.time;
          sendManager('runtime:progress', progress);
        }
        sendManager('runtime:heartbeat', status);
        if (chatWindow && !chatWindow.isDestroyed()) chatWindow.webContents.send('runtime:heartbeat', status);
        if (tokenWindow && !tokenWindow.isDestroyed()) tokenWindow.webContents.send('runtime:heartbeat', status);
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
