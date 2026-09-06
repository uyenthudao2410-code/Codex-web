const { contextBridge, ipcRenderer } = require('electron');

const HEARTBEAT_STALE_MS = 15_000;
const COMMAND_EVIDENCE_STALE_MS = 90_000;
const ACTIVE_ORCHESTRATION_STATES = new Set(['PREFLIGHT', 'ROUTED', 'EXECUTING', 'PROVING']);
const ACTIVE_DELEGATION_STATUSES = new Set(['active', 'running', 'starting', 'executing', 'in_progress', 'streaming', 'responding']);

function cloneIpcResult(result) {
  if (!result || result.ok !== true || !result.data) return result;
  try { return { ...result, data: JSON.parse(JSON.stringify(result.data)) }; }
  catch { return result; }
}

function timestampAgeMs(value) {
  const parsed = Date.parse(String(value || ''));
  return Number.isFinite(parsed) ? Math.max(0, Date.now() - parsed) : null;
}

function markStaleRunningCommand(target) {
  if (!target || typeof target !== 'object') return false;
  const command = target.current_command;
  if (!command || typeof command !== 'object' || String(command.status || '').toLowerCase() !== 'running') return false;
  const ageMs = timestampAgeMs(target.updated_at || command.started_at);
  if (ageMs === null || ageMs < COMMAND_EVIDENCE_STALE_MS) return false;
  target.current_command = {
    ...command,
    status: 'stale',
    stale: true,
    stale_reason: 'command_evidence_expired',
    stale_after_ms: COMMAND_EVIDENCE_STALE_MS
  };
  if (String(target.status || '').toLowerCase() === 'active') target.status = 'waiting';
  if (!String(target.current_step || '').trim()) target.current_step = 'Waiting for model';
  return true;
}

function sanitizeTaskStateResult(result) {
  const next = cloneIpcResult(result);
  if (next?.ok !== true || !next.data) return next;
  const target = next.data.state && typeof next.data.state === 'object' ? next.data.state : next.data;
  markStaleRunningCommand(target);
  return next;
}

function sanitizeOrchestrationResult(result) {
  const next = cloneIpcResult(result);
  const data = next?.ok === true && next.data && typeof next.data === 'object' ? next.data : null;
  if (!data) return next;
  const commandStale = markStaleRunningCommand(data.task);
  if (!commandStale) return next;

  const delegationActive = Array.isArray(data.delegations) && data.delegations.some((item) =>
    ACTIVE_DELEGATION_STATUSES.has(String(item?.status || '').toLowerCase())
  );
  const writeActive = String(data.authority?.write?.status || '').toLowerCase() === 'active';
  const latestEvent = Array.isArray(data.events) ? data.events[data.events.length - 1] : null;
  const latestEventAgeMs = timestampAgeMs(latestEvent?.event_time);
  const recentControlEvidence = latestEventAgeMs !== null && latestEventAgeMs < COMMAND_EVIDENCE_STALE_MS;

  // A persisted command can survive a crash/restart. Do not let that old row
  // keep the fabric animated unless another fresh source proves execution.
  if (!delegationActive && !writeActive && !recentControlEvidence) {
    const resumeState = String(data.resume_packet?.orchestration_state || '').toUpperCase();
    if (data.resume_packet && ACTIVE_ORCHESTRATION_STATES.has(resumeState)) {
      data.resume_packet.orchestration_state = '';
    }
    const topState = String(data.orchestration_state || '').toUpperCase();
    if (ACTIVE_ORCHESTRATION_STATES.has(topState)) data.orchestration_state = '';
    data.signal_freshness = {
      status: 'stale',
      reason: 'command_evidence_expired',
      stale_after_ms: COMMAND_EVIDENCE_STALE_MS
    };
  }
  return next;
}

function subscribeWithHeartbeatWatchdog(listener) {
  let timer = null;
  let disposed = false;
  const arm = () => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      if (disposed) return;
      listener({
        mcpRunning: null,
        nativeAlive: null,
        tunnelRunning: null,
        fullyReady: false,
        recovering: false,
        telemetryAvailable: false,
        failureKind: 'heartbeat_stale',
        signalStale: true,
        staleAfterMs: HEARTBEAT_STALE_MS
      });
    }, HEARTBEAT_STALE_MS);
  };
  const wrapped = (_event, payload) => {
    arm();
    listener({ ...(payload || {}), signalStale: false, staleAfterMs: HEARTBEAT_STALE_MS });
  };
  ipcRenderer.on('runtime:heartbeat', wrapped);
  arm();
  return () => {
    disposed = true;
    if (timer) clearTimeout(timer);
    ipcRenderer.removeListener('runtime:heartbeat', wrapped);
  };
}

contextBridge.exposeInMainWorld('mcpAssistant', {
  snapshot: (options) => ipcRenderer.invoke('app:snapshot', options),
  lightweightSnapshot: () => ipcRenderer.invoke('app:lightweight-snapshot'),
  recordUiPerformance: (sample) => ipcRenderer.invoke('ui-performance:record', sample),
  uiPerformance: () => ipcRenderer.invoke('ui-performance:read'),
  orchestration: () => ipcRenderer.invoke('panel:orchestration').then(sanitizeOrchestrationResult),
  liveOrchestration: () => ipcRenderer.invoke('panel:live-control').then(sanitizeOrchestrationResult),
  dashboardAnalytics: () => ipcRenderer.invoke('panel:dashboard-analytics'),
  p5A0: (action) => ipcRenderer.invoke('p5-a0:control', action),
  chooseWorkspace: () => ipcRenderer.invoke('dialog:workspace'),
  switchWorkspace: (workspace) => ipcRenderer.invoke('workspace:switch', workspace),
  updateAuthorizedRoots: (roots) => ipcRenderer.invoke('workspace:authorized-roots', roots),
  taskState: () => ipcRenderer.invoke('task-state:read').then(sanitizeTaskStateResult),
  clearTaskState: () => ipcRenderer.invoke('task-state:clear'),
  pauseTask: () => ipcRenderer.invoke('task-state:pause'),
  resumeTask: () => ipcRenderer.invoke('task-state:resume'),
  stopTask: () => ipcRenderer.invoke('task-state:stop'),
  taskHistory: () => ipcRenderer.invoke('task-state:history'),
  performanceTrace: () => ipcRenderer.invoke('performance:read'),
  clearPerformanceTrace: () => ipcRenderer.invoke('performance:clear'),
  inspectBuild: () => ipcRenderer.invoke('build:inspect'),
  runBuild: (options) => ipcRenderer.invoke('build:run', options),
  inspectHealth: () => ipcRenderer.invoke('health:inspect'),
  repairHealth: () => ipcRenderer.invoke('health:repair'),
  closeManager: () => ipcRenderer.invoke('manager:close'),
  openTokenDashboard: () => ipcRenderer.invoke('token-dashboard:open'),
  closeTokenDashboard: () => ipcRenderer.invoke('token-dashboard:close'),
  saveSettings: (patch) => ipcRenderer.invoke('settings:save', patch),
  saveRuntimeKey: (value) => ipcRenderer.invoke('secrets:runtime-key', value),
  removeRuntimeKey: () => ipcRenderer.invoke('secrets:runtime-key-remove'),
  regenerateMcpToken: () => ipcRenderer.invoke('secrets:mcp-token-regenerate'),
  start: () => ipcRenderer.invoke('runtime:start'),
  stop: () => ipcRenderer.invoke('runtime:stop'),
  restart: () => ipcRenderer.invoke('runtime:restart'),
  activationPreflight: (component, allowAcceptancePending = false) => ipcRenderer.invoke('code:activation-preflight', component, allowAcceptancePending),
  activateUpdate: (component, allowAcceptancePending = false) => ipcRenderer.invoke('code:activate-update', component, allowAcceptancePending),
  activationStatus: (operationId) => ipcRenderer.invoke('code:activation-status', operationId),
  acknowledgeConnectorContract: () => ipcRenderer.invoke('connector:ack-contract'),
  logs: () => ipcRenderer.invoke('logs:read'),
  clearLogs: () => ipcRenderer.invoke('logs:clear'),
  openExternal: (target) => ipcRenderer.invoke('shell:open', target),
  installPython: () => ipcRenderer.invoke('environment:install-python'),
  detectProxy: () => ipcRenderer.invoke('environment:detect-proxy'),
  clearChatSession: () => ipcRenderer.invoke('chat:clear-session'),
  onProgress: (listener) => {
    const wrapped = (_event, payload) => listener(payload);
    ipcRenderer.on('runtime:progress', wrapped);
    return () => ipcRenderer.removeListener('runtime:progress', wrapped);
  },
  onLog: (listener) => {
    const wrapped = (_event, payload) => listener(payload);
    ipcRenderer.on('logs:entry', wrapped);
    return () => ipcRenderer.removeListener('logs:entry', wrapped);
  },
  onStatus: (listener) => { const wrapped = (_event, payload) => listener(payload); ipcRenderer.on('runtime:status-changed', wrapped); return () => ipcRenderer.removeListener('runtime:status-changed', wrapped); },
  onHeartbeat: subscribeWithHeartbeatWatchdog,
  onBuildProgress: (listener) => { const wrapped = (_event, payload) => listener(payload); ipcRenderer.on('build:progress', wrapped); return () => ipcRenderer.removeListener('build:progress', wrapped); }
});
