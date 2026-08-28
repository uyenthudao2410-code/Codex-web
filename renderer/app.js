const api = window.mcpAssistant || createPreviewApi();

function createPreviewApi() {
  const previewSettings = {
    workspace: 'C:\\Users\\ExampleUser\\Desktop\\my-project', permissionMode: 'safe', toolMode: 'smart',
    mcpPort: 18766, healthPort: 18082, proxyMode: 'auto', proxyUrl: '', tunnelId: 'tunnel_demo',
    recoveryMcpPort: 18767, recoveryHealthPort: 18083, recoveryTunnelId: '',
    theme: 'light', startWithWindows: false, progressReportSeconds: 90, keepRunningOnClose: true, autoStartServices: false, firstRunCompleted: true, guideProgress: {}, authorizedRoots: []
  };
  const snapshot = {
    settings: previewSettings,
    secrets: { runtimeApiKey: true, mcpAuthToken: true },
    environment: {
      python: { installed: true, version: 'Python 3.12.10' },
      proxy: { mode: 'auto', configured: false, reachable: true, source: 'auto-direct', url: '' }, tunnelClient: { installed: true },
      workspace: { configured: true, exists: true }, ports: { mcpListening: true, tunnelListening: true }
    },
    status: { busy: false, runtimeRunning: true, tunnelRunning: true, fullyReady: true, localMcpUrl: 'http://127.0.0.1:18766/mcp', tunnelUiUrl: 'http://127.0.0.1:18082/ui', connectorContractState: 'UNCHANGED_ACKNOWLEDGED', connectorRefreshRequired: false, codeRevision: { codingMcp: { state: 'current', running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64), update_pending: false } } },
    device: { scope: 'current_device_only', registry: 'local', device_id: '12345678-1234-4123-8123-123456789abc', device_instance_id: 'preview-device-instance-0001', display_name: 'Máy bàn', online: true, workspace: previewSettings.workspace, coding: { mcp_running: true, native_alive: true, tunnel_running: true, tunnel_id: 'tunnel_demo', ownership: 'device_id' }, recovery: { host_running: true, mcp_running: true, tunnel_running: false, tunnel_state: 'not_configured', tunnel_id: null }, git: { available: true, branch: 'main', head: 'cf6cb6ddbf29d90515d003ce72490ffda985c37f', head_short: 'cf6cb6dd', dirty: true } },
    recoveryHost: { state: 'healthy', device_id: '12345678-1234-4123-8123-123456789abc', device_instance_id: 'preview-device-instance-0001', device_display_name: 'Máy bàn', code_revision: { state: 'current', running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64), update_pending: false }, electron_ui_revision: { state: 'current', running_revision: 'a'.repeat(64), disk_revision: 'a'.repeat(64), update_pending: false }, electron_ui_recovery: { state: 'healthy', alive: true, pid: 42001, instance_id: 'preview-electron-ui-0001', runtime_mode: 'development' }, recovery_plane: { tunnel: { state: 'not_configured', configured: false, pid: null } } }
  };
  const ok = (data) => Promise.resolve({ ok: true, data });
  return {
    snapshot: () => ok(snapshot), chooseWorkspace: () => ok(snapshot.settings.workspace), switchWorkspace: (workspace) => { snapshot.settings.workspace=workspace; return ok(snapshot); }, updateAuthorizedRoots: (roots) => { snapshot.settings.authorizedRoots=roots; return ok(snapshot); }, closeManager: () => ok(true),
    saveSettings: (patch) => { Object.assign(snapshot.settings, patch); return ok(snapshot.settings); },
    saveRuntimeKey: () => ok(snapshot.secrets), removeRuntimeKey: () => ok(snapshot.secrets), regenerateMcpToken: () => ok(snapshot.secrets),
    start: () => ok(snapshot), stop: () => ok(snapshot), restart: () => ok(snapshot), acknowledgeConnectorContract: () => ok(snapshot),
    logs: () => ok([{ time: new Date().toISOString(), level: 'info', message: 'Chế độ xem trước giao diện tĩnh' }]), clearLogs: () => ok(true),
    taskState: () => ok({ exists: false, state: null }), clearTaskState: () => ok(true), pauseTask: () => ok({}), resumeTask: () => ok({}), stopTask: () => ok({}), taskHistory: () => ok([]), performanceTrace: () => ok(null), clearPerformanceTrace: () => ok(true),
    inspectBuild: () => ok({ type: 'electron', name: 'demo', version: '0.1.0', testCommand: 'npm test', buildCommand: 'npm run dist', artifacts: ['dist'] }), runBuild: () => ok({ overallStatus: 'passed', project: { type: 'electron', name: 'demo', version: '0.1.0' }, testResult: { status: 'passed' }, buildResult: { status: 'passed' }, artifacts: [] }), inspectHealth: () => ok({ healthy: true, checks: [] }), repairHealth: () => ok({ healthy: true, checks: [], actions: [], unresolved: [] }),
    openExternal: () => ok(true), installPython: () => ok(true), detectProxy: () => ok(snapshot.environment.proxy), onProgress: () => () => {}, onLog: () => () => {}, onStatus: () => () => {}, onHeartbeat: () => () => {}, onBuildProgress: () => () => {}
  };
}

const pageMeta = {
  overview: ['EXECUTION CONTROL', 'Command Center', 'Runtime, clients, routing, authority and proof in one operational view.'],
  device: ['DEVICE CONTROL', 'Thiết bị hiện tại', 'Định danh thiết bị, ownership, Coding/Recovery, Tunnel và Git của máy đang chạy Recovery Host.'],
  deploy: ['CONNECTIONS', 'Connections', 'Quản lý Runtime API Key, OpenAI Tunnel và tuyến mạng.'],
  workspace: ['WORKSPACE ACCESS', 'Workspace', 'Quản lý workspace chính, thư mục ủy quyền bổ sung và quyền thực thi lệnh.'],
  task: ['TASKS & PROOF', 'Tasks & Proof', 'Theo dõi durable task state, kiểm thử, proof, lịch sử và hiệu năng.'],
  system: ['SYSTEM & DIAGNOSTICS', 'System', 'Build, health, logs, onboarding và cấu hình nâng cao.'],
  build: ['BUILD & XÁC MINH', 'Xác minh & Build', 'Tự động nhận diện dự án, thực thi kiểm thử và build, đồng thời kiểm tra sản phẩm đầu ra.'],
  health: ['CHẨN ĐOÁN & SỬA CHỮA', 'Chẩn đoán & Sửa chữa', 'Kiểm tra môi trường vận hành và tự động sửa chữa các sự cố an toàn.'],
  guide: ['HƯỚNG DẪN CẤU HÌNH', 'Hướng dẫn Kết nối', 'Hoàn thành các bước kết nối OpenAI Tunnel và ChatGPT Web.'],
  logs: ['CHẨN ĐOÁN', 'Nhật ký Vận hành', 'Xem thông tin chẩn đoán của môi trường portable, MCP và Tunnel.'],
  settings: ['CẤU HÌNH TÙY CHỌN', 'Cài đặt Trợ lý', 'Quản lý giao diện, hành vi khởi động, phản hồi nhiệm vụ và chứng thư cục bộ.']
};

const state = {
  snapshot: null,
  currentPage: 'overview',
  selectedWorkspace: '',
  logFilter: 'all',
  logs: [],
  busy: false,
  initializedForms: false
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function unwrap(result) {
  if (!result?.ok) throw new Error(result?.error || 'Thao tác thất bại');
  return result.data;
}

function toast(title, message = '', type = 'success') {
  const element = document.createElement('div');
  element.className = `toast ${type}`;
  const heading = document.createElement('b');
  heading.textContent = title;
  const detail = document.createElement('span');
  detail.textContent = message;
  element.append(heading, detail);
  $('#toastStack').appendChild(element);
  setTimeout(() => element.remove(), 4200);
}

function setBusy(value, overlay = false) {
  state.busy = value;
  $('#busyOverlay').classList.toggle('visible', value && overlay);
  ['#topStartButton', '#heroStartButton', '#deployNow', '#overviewRestart', '#overviewStop', '#deviceStart', '#deviceRestart', '#deviceStop', '#deviceRepair'].forEach((selector) => {
    const element = $(selector);
    if (element) element.disabled = value;
  });
}

function setDot(element, status) {
  if (!element) return;
  element.classList.remove('ready', 'warn', 'error');
  if (status) element.classList.add(status);
}

function recoveryTunnelPresentation(source) {
  if (source?.status?.signalStale === true || source?.signalStale === true) {
    return { state: 'connecting', label: 'Telemetry gián đoạn', detail: 'Đang giữ receipt gần nhất và chờ heartbeat mới từ Recovery Host.' };
  }
  const tunnel = source?.recoveryHost?.recovery_plane?.tunnel || null;
  const raw = String(tunnel?.state || '').toLowerCase();
  if (raw === 'healthy') return { state: 'connected', label: 'Đã kết nối', detail: 'Recovery Tunnel đã qua health check cục bộ.' };
  if (raw === 'starting') return { state: 'connecting', label: 'Đang kết nối', detail: 'Recovery Tunnel đang khởi tạo và chờ health check.' };
  if (raw === 'not_configured') return { state: 'not_configured', label: 'Chưa cấu hình', detail: 'Chưa có Recovery Tunnel ID riêng.' };
  if (raw === 'blocked_shared_tunnel_id') return { state: 'error', label: 'Bị chặn', detail: 'Recovery Tunnel ID đang trùng với Coding Tunnel ID chính.' };
  if (raw === 'blocked_missing_runtime_key') return { state: 'error', label: 'Thiếu Runtime Key', detail: 'Đã có Recovery Tunnel ID nhưng chưa có Runtime API Key khả dụng.' };
  if (raw.startsWith('blocked_')) return { state: 'error', label: 'Bị chặn', detail: `Recovery Tunnel báo trạng thái: ${raw}.` };
  if (raw) return { state: 'connecting', label: 'Đang xác minh lại', detail: `Recovery Tunnel tạm báo trạng thái: ${raw}.` };
  return { state: 'not_configured', label: 'Đang kiểm tra', detail: 'Chưa nhận được telemetry Recovery Tunnel từ Recovery Host.' };
}

function renderRecoveryTunnelSettings(source) {
  const presentation = recoveryTunnelPresentation(source);
  const badge = $('#recoveryTunnelSettingsBadge');
  const stateChip = $('#recoveryTunnelSettingsState');
  if (badge) {
    badge.textContent = presentation.label;
    badge.dataset.state = presentation.state;
  }
  if (stateChip) {
    stateChip.textContent = presentation.label;
    stateChip.dataset.state = presentation.state;
  }
  const detail = $('#recoveryTunnelSettingsStatus');
  if (detail) detail.textContent = presentation.detail;
}

function renderDevice(source) {
  const device = source?.device || {};
  const settings = source?.settings || state.snapshot?.settings || {};
  const recoveryHost = source?.recoveryHost || {};
  const displayName = String(device.display_name || recoveryHost.device_display_name || 'Thiết bị hiện tại');
  const deviceId = String(device.device_id || recoveryHost.device_id || '');
  const instanceId = String(device.device_instance_id || recoveryHost.device_instance_id || '');
  const online = device.online !== false && Boolean(deviceId);
  const git = device.git || {};
  const gitLabel = git.available ? `${git.branch || 'detached'} @ ${git.head_short || 'no-head'}${git.dirty ? ' · dirty' : ' · clean'}` : 'Không phải Git repo / chưa có dữ liệu';
  const coding = device.coding || {};
  const recovery = device.recovery || {};
  const top = $('#topDeviceButton');
  if (top) { top.classList.remove('ready', 'warn'); top.classList.add(online ? (coding.mcp_running ? 'ready' : 'warn') : 'warn'); top.title = deviceId ? `Current device: ${deviceId}` : 'Device identity unavailable'; }
  if ($('#topDeviceName')) $('#topDeviceName').textContent = displayName;
  if ($('#topDeviceMeta')) $('#topDeviceMeta').textContent = `${device.registry || 'local'} · ${deviceId ? deviceId.slice(0, 8) : 'unknown'} · ${git.available ? `${git.branch || 'detached'} @ ${git.head_short || 'no-head'}` : 'Git n/a'}`;
  if ($('#deviceDisplayName')) $('#deviceDisplayName').textContent = displayName;
  if ($('#deviceOnline')) { $('#deviceOnline').textContent = online ? 'Online' : 'Unknown'; $('#deviceOnline').classList.toggle('neutral', !online); }
  if ($('#deviceId')) { $('#deviceId').textContent = deviceId || '—'; $('#deviceId').title = deviceId; }
  if ($('#deviceInstanceId')) { $('#deviceInstanceId').textContent = instanceId || '—'; $('#deviceInstanceId').title = instanceId; }
  if ($('#deviceWorkspace')) { $('#deviceWorkspace').textContent = device.workspace || settings.workspace || '—'; $('#deviceWorkspace').title = device.workspace || settings.workspace || ''; }
  if ($('#deviceGitState')) $('#deviceGitState').textContent = gitLabel;
  if ($('#deviceCodingState')) $('#deviceCodingState').textContent = coding.mcp_running && coding.tunnel_running ? 'Coding ready' : coding.mcp_running ? 'MCP ready · Tunnel down' : 'Coding stopped';
  if ($('#deviceRecoveryState')) $('#deviceRecoveryState').textContent = recovery.mcp_running && recovery.tunnel_running ? 'Recovery ready' : recovery.mcp_running ? `Recovery MCP ready · ${recovery.tunnel_state || 'Tunnel down'}` : 'Recovery unavailable';
  if ($('#deviceCodingTunnelId')) $('#deviceCodingTunnelId').textContent = `Tunnel: ${coding.tunnel_id || settings.tunnelId || 'chưa cấu hình'}`;
  if ($('#deviceRecoveryTunnelId')) $('#deviceRecoveryTunnelId').textContent = `Tunnel: ${recovery.tunnel_id || settings.recoveryTunnelId || 'chưa cấu hình'}`;
}

function navigate(page) {
  if (!pageMeta[page]) return;
  state.currentPage = page;
  if (location.hash !== `#${page}`) history.replaceState(null, '', `#${page}`);
  const primaryPage = ['build', 'health', 'guide', 'logs', 'settings'].includes(page) ? 'system' : page;
  $$('.nav-item').forEach((item) => item.classList.toggle('active', item.dataset.page === primaryPage));
  $$('.page').forEach((item) => item.classList.toggle('active', item.dataset.pageView === page));
  const [eyebrow, title, subtitle] = pageMeta[page];
  $('#pageEyebrow').textContent = eyebrow;
  $('#pageTitle').textContent = title;
  $('#pageSubtitle').textContent = subtitle;
  $('.content-viewport').scrollTop = 0;
  if (page === 'logs') loadLogs();
  if (page === 'task') loadTaskState();
  if (page === 'build') inspectBuild();
  if (page === 'health') inspectHealth();
}

function textOr(value, fallback = '—') { return String(value ?? '').trim() || fallback; }

function renderTaskList(container, items, render) {
  container.replaceChildren();
  if (!items?.length) {
    const empty = document.createElement('span'); empty.className = 'task-muted'; empty.textContent = 'Chưa có bản ghi'; container.appendChild(empty); return;
  }
  items.forEach((item) => container.appendChild(render(item)));
}

function renderTaskState(payload) {
  const task = payload?.state;
  const hasTask = Boolean(task && (
    textOr(task.objective, '') ||
    textOr(task.current_step, '') ||
    textOr(task.next_step, '') ||
    (Array.isArray(task.steps) && task.steps.length) ||
    (task.status && task.status !== 'idle')
  ));
  $('#taskStateEmpty').hidden = hasTask;
  $('#taskStateContent').hidden = !hasTask;
  if (!hasTask) return;
  $('#taskObjective').textContent = textOr(task.objective, 'Chưa điền mục tiêu hiện tại');
  $('#taskId').textContent = textOr(task.task_id);
  $('#taskStatus').textContent = textOr(task.status, 'idle');
  $('#taskCurrentStep').textContent = textOr(task.current_step);
  $('#taskNextStep').textContent = textOr(task.next_step);
  $('#taskFailureRow').hidden = !task.failure;
  $('#taskFailure').textContent = textOr(task.failure);
  const steps = Array.isArray(task.steps) ? task.steps : [];
  const done = steps.filter((item) => item.status === 'completed').length;
  $('#taskStepCount').textContent = `${done} / ${steps.length}`;
  renderTaskList($('#taskSteps'), steps, (item) => { const row=document.createElement('div'); row.className=`task-step ${item.status || 'pending'}`; const mark=document.createElement('i'); mark.textContent=item.status==='completed'?'✓':item.status==='in_progress'?'→':item.status==='failed'?'!':'•'; const label=document.createElement('span'); label.textContent=textOr(item.text); row.append(mark,label); return row; });
  const command = task.current_command;
  $('#taskCommand').textContent = command ? `${textOr(command.command)}\n${textOr(command.status)} · ${textOr(command.workdir, '.')}` : 'Hiện không có lệnh nào đang chạy';
  const tests = Array.isArray(task.test_results) ? task.test_results.slice(-5).reverse() : [];
  renderTaskList($('#taskTests'), tests, (item) => { const row=document.createElement('div'); row.className=`task-result ${item.status}`; row.textContent=`${item.status === 'passed' ? 'Thành công' : 'Thất bại'} · ${textOr(item.command, 'Kiểm thử')} · ${item.duration_ms ?? 0} ms`; return row; });
  const files = Array.isArray(task.modified_files) ? task.modified_files.slice().reverse() : [];
  $('#taskFileCount').textContent = String(files.length);
  renderTaskList($('#taskFiles'), files, (item) => { const row=document.createElement('div'); row.className='task-file'; const op=document.createElement('b'); op.textContent=textOr(item.operation, 'update').slice(0,1).toUpperCase(); const file=document.createElement('span'); file.textContent=textOr(item.path); row.append(op,file); return row; });
  const report = task.last_build_report;
  const build = $('#taskBuild'); build.replaceChildren();
  if (!report) { build.textContent='Chưa chạy verify_build.'; }
  else {
    const summary=document.createElement('div'); summary.className=`build-summary ${report.overall_status}`; summary.textContent=`${report.overall_status === 'passed' ? 'Xác minh thành công' : 'Xác minh thất bại'} · ${textOr(report.project?.type)} · v${textOr(report.project?.version)}`; build.appendChild(summary);
    (report.artifacts || []).slice(0,8).forEach((item) => { const row=document.createElement('div'); row.className='task-artifact'; const path=document.createElement('span'); path.textContent=textOr(item.path); const hash=document.createElement('code'); hash.textContent=textOr(item.sha256 || item.sha384 || item.sha512).slice(0,16); row.append(path,hash); build.appendChild(row); });
    if (!(report.artifacts || []).length) { const empty=document.createElement('span'); empty.className='task-muted'; empty.textContent=textOr(report.failure, 'Không tìm thấy sản phẩm build'); build.appendChild(empty); }
  }
}

async function loadTaskState() {
  try {
    const [taskPayload] = await Promise.all([api.taskState(), loadTaskHistory(), loadPerformanceTrace()]);
    renderTaskState(unwrap(taskPayload));
  }
  catch (error) { toast('Đọc trạng thái nhiệm vụ thất bại', error.message, 'error'); }
}

function formatDuration(ms) {
  const value = Number(ms || 0);
  if (value < 1000) return `${value} ms`;
  if (value < 60000) return `${(value / 1000).toFixed(1)} giây`;
  return `${Math.floor(value / 60000)} phút ${Math.round((value % 60000) / 1000)} giây`;
}

function renderPerformanceTrace(trace) {
  const metrics = $('#performanceMetrics');
  const timeline = $('#performanceTimeline');
  metrics.replaceChildren(); timeline.replaceChildren();
  if (!trace || !trace.tool_calls) {
    const empty = document.createElement('span'); empty.className = 'task-muted'; empty.textContent = 'Chưa có bản ghi hiệu năng'; metrics.append(empty); return;
  }
  const items = [
    ['Gọi công cụ', trace.tool_calls], ['Thực thi trên máy', formatDuration(trace.local_execution_ms)],
    ['Thời gian chờ ước tính', formatDuration(trace.estimated_wait_ms)], ['Trùng bộ nhớ đệm', trace.cache_hits || 0],
    ['Chắn lặp lại', trace.deduplicated_calls || 0], ['Thất bại', trace.errors || 0]
  ];
  items.forEach(([label, value]) => { const card=document.createElement('div'); card.className='performance-metric'; const b=document.createElement('b'); b.textContent=String(value); const span=document.createElement('span'); span.textContent=label; card.append(b,span); metrics.append(card); });
  (trace.recent || []).slice(-30).reverse().forEach((event) => {
    const row=document.createElement('div'); row.className='performance-event';
    const tool=document.createElement('b'); tool.textContent=textOr(event.tool);
    const local=document.createElement('span'); local.textContent=`Trên máy ${formatDuration(event.duration_ms)}`;
    const wait=document.createElement('span'); wait.textContent=`Thời gian chờ ${formatDuration(event.wait_before_ms)}`;
    const flag=document.createElement('span'); flag.textContent=event.deduplicated ? 'Đã lọc trùng' : event.cache_hit ? 'Bộ nhớ đệm' : event.ok ? 'Hoàn thành' : 'Thất bại'; if (event.cache_hit || event.deduplicated) flag.className='cache-hit';
    row.append(tool,local,wait,flag); timeline.append(row);
  });
}

async function loadPerformanceTrace() {
  try { renderPerformanceTrace(unwrap(await api.performanceTrace())); }
  catch (error) { renderPerformanceTrace(null); }
}

async function loadTaskHistory() {
  const container = $('#taskHistory');
  try {
    const items = unwrap(await api.taskHistory());
    renderTaskList(container, items, (task) => {
      const row = document.createElement('div'); row.className = 'task-history-item';
      const copy = document.createElement('div');
      const title = document.createElement('b'); title.textContent = textOr(task.objective, 'Nhiệm vụ chưa đặt tên');
      const meta = document.createElement('small'); meta.textContent = `${textOr(task.status, 'unknown')} · ${textOr(task.task_id)} · ${new Date(task.archived_at || task.updated_at || Date.now()).toLocaleString('vi-VN')}`;
      copy.append(title, meta); row.append(copy); return row;
    });
  } catch (error) { container.textContent = `Đọc thất bại: ${error.message}`; }
}

function applyTheme(theme) {
  document.body.dataset.theme = theme === 'light' ? 'light' : 'dark';
  $('#themeSelect').value = theme === 'light' ? 'light' : 'dark';
}

function applyFormValues(snapshot, force = false) {
  if (state.initializedForms && !force) return;
  const settings = snapshot.settings;
  state.selectedWorkspace = settings.workspace;
  $('#tunnelIdInput').value = settings.tunnelId || '';
  $('#recoveryTunnelIdInput').value = settings.recoveryTunnelId || '';
  $('#recoveryMcpEndpoint').textContent = `http://127.0.0.1:${settings.recoveryMcpPort || 18767}/mcp`;
  $('#proxyModeSelect').value = settings.proxyMode || 'auto';
  $('#proxyUrlInput').value = settings.proxyUrl || '';
  $('#mcpPortInput').value = settings.mcpPort;
  $('#healthPortInput').value = settings.healthPort;
  $('#startWithWindowsToggle').checked = Boolean(settings.startWithWindows);
  $('#keepRunningToggle').checked = settings.keepRunningOnClose;
  $('#autoStartToggle').checked = settings.autoStartServices;
  $('#progressReportSelect').value = String(settings.progressReportSeconds || 90);
  if ($('#toolModeSelect')) $('#toolModeSelect').value = 'smart';
  $$('input[name="permission"]').forEach((input) => {
    input.checked = input.value === settings.permissionMode;
    input.closest('.choice').classList.toggle('selected', input.checked);
  });
  applyTheme(settings.theme);
  restoreGuideProgress(settings.guideProgress || {});
  renderProxyControls();
  state.initializedForms = true;
}

function shortRevision(value) {
  const revision = String(value || '');
  return revision ? `${revision.slice(0, 12)}${revision.length > 12 ? '…' : ''}` : 'unknown';
}

function componentSourcePresentation(revision, { running = true, label = 'component' } = {}) {
  if (!running) return { state: 'STOPPED', detail: `${label} hiện không chạy.` };
  const runningRevision = String(revision?.running_revision || '');
  const diskRevision = String(revision?.disk_revision || '');
  if (runningRevision && diskRevision && runningRevision === diskRevision && revision?.update_pending !== true) {
    return { state: 'CURRENT', detail: `${shortRevision(runningRevision)} · running = disk` };
  }
  if (diskRevision) {
    return { state: 'STALE', detail: `${shortRevision(runningRevision)} → ${shortRevision(diskRevision)}` };
  }
  return { state: 'UNKNOWN', detail: `${label} chưa có revision receipt.` };
}

function connectorContractPresentation(status = {}) {
  const reported = String(status.connectorContractState || '').toUpperCase();
  const explicit = reported === 'COMPATIBLE_ACKNOWLEDGED' ? 'UNAVAILABLE' : reported;
  if (status.connectorAcknowledgementPending === true
    && ['UNCHANGED_ACKNOWLEDGED', 'CURRENT_ACKNOWLEDGED', 'CURRENT_COMPATIBLE_ACKNOWLEDGED'].includes(explicit)) {
    return {
      state: 'UNAVAILABLE',
      notice: true,
      message: 'Connector receipt đang mâu thuẫn: state đã acknowledged nhưng acknowledgement vẫn pending. Chờ runtime hội tụ trước khi hiển thị xanh.',
      toast: 'Connector acknowledgement chưa hội tụ; không dùng trạng thái xanh cũ.'
    };
  }
  if (explicit === 'UNCHANGED_ACKNOWLEDGED') {
    const activationClosed = status?.activationEpoch?.admission_open === false;
    return {
      state: explicit,
      notice: activationClosed,
      message: activationClosed
        ? 'SHA contract đã acknowledge, nhưng activation mới vẫn chờ discovery hoặc compatibility bootstrap bound với process hiện tại.'
        : 'Tool contract không đổi và SHA hiện tại đã được acknowledge.',
      toast: activationClosed
        ? 'Activation mới vẫn chờ connector freshness bound với process hiện tại.'
        : 'Tool contract không đổi và SHA hiện tại đã được acknowledge.'
    };
  }
  if (explicit === 'CURRENT_ACKNOWLEDGED') {
    return {
      state: explicit,
      notice: false,
      message: 'Tool contract hiện tại đã được discovery và acknowledge.',
      toast: 'Tool contract hiện tại đã được discovery và acknowledge.'
    };
  }
  if (explicit === 'CURRENT_COMPATIBLE_ACKNOWLEDGED') {
    return {
      state: explicit,
      notice: false,
      message: 'Tool contract hiện tại đã được compatibility ACK bằng no-workspace bootstrap của đúng process/epoch; không ghi nhận discovery giả.',
      toast: 'Connector compatibility đã được ACK cho activation hiện tại.'
    };
  }
  if (explicit === 'CHANGED_DISCOVERED_NEEDS_ACK') {
    return {
      state: explicit,
      notice: true,
      message: 'ChatGPT đã discovery contract SHA mới; acknowledgement chính thức vẫn đang chờ Recovery Host hoàn tất.',
      toast: 'Contract SHA mới đã được discovery; acknowledgement chính thức vẫn đang chờ.'
    };
  }
  if (explicit === 'CHANGED_NEEDS_DISCOVERY') {
    return {
      state: explicit,
      notice: true,
      message: 'Tool contract SHA đã đổi. ChatGPT cần discovery contract hiện tại hoặc thực hiện compatibility bootstrap an toàn khi gọi lại workspace_context.',
      toast: 'Connector chưa có discovery hoặc compatibility bootstrap cho activation hiện tại.'
    };
  }
  if (explicit === 'CHANGED_COMPATIBLE_NEEDS_ACK' || explicit === 'UNCHANGED_COMPATIBLE_NEEDS_ACK') {
    return {
      state: explicit,
      notice: true,
      message: 'Đã có no-workspace compatibility bootstrap bound đúng process/epoch; Recovery Host đang hoàn tất ACK chính thức.',
      toast: 'Compatibility bootstrap hợp lệ; đang chờ Recovery Host ACK.'
    };
  }
  if (explicit === 'UNAVAILABLE') {
    return {
      state: explicit,
      notice: false,
      message: 'Chưa có tool contract runtime để đánh giá connector freshness.',
      toast: 'Tool contract runtime hiện chưa khả dụng.'
    };
  }
  if (explicit || typeof status.connectorRefreshRequired !== 'boolean') {
    return {
      state: 'UNAVAILABLE',
      notice: false,
      message: explicit
        ? `Connector contract state không được nhận diện: ${explicit}.`
        : 'Chưa có connector contract state hoặc refresh receipt để đánh giá freshness.',
      toast: 'Connector contract freshness hiện chưa khả dụng.'
    };
  }
  // A legacy boolean can tell us that no refresh is requested, but cannot
  // prove the authenticated acknowledgement/discovery state required by the
  // current closure contract. Keep it visibly unavailable until the enum is
  // present.
  return {
    state: 'UNAVAILABLE',
    notice: false,
    message: 'Runtime chỉ cung cấp cờ tương thích cũ; chưa có connectorContractState để chứng minh freshness/acknowledgement.',
    toast: 'Connector contract freshness hiện chưa có receipt đủ mạnh.'
  };
}

// The backend is the authority for computing activation closure, but the
// renderer must not hide the warning merely because an untrusted/stale
// snapshot happens to contain closure_state="LIVE_CLOSED".  Keep this check
// deliberately redundant and fail-closed: every gate that is rendered green
// must be present, true, and agree with the current runtime status.
function activationClosureDisplayState(closure, status = {}) {
  const value = closure && typeof closure === 'object' ? closure : {};
  const requiredTrue = [
    'closure_input_schema_supported',
    'checkpoint_identity_valid',
    'source_accepted',
    'accepted_receipts_complete',
    'activation_eligible',
    'affected_components_valid',
    'component_receipts_valid',
    'postflight_receipts_valid',
    'lifecycle_clean',
    'components_current',
    'connector_contract_current',
    'runtime_fully_ready'
  ];
  const missingGate = requiredTrue.find((key) => value[key] !== true);
  if (missingGate) return { liveClosed: false, reason: missingGate };
  if (String(value.closure_state || '') !== 'LIVE_CLOSED') return { liveClosed: false, reason: 'closure_state' };
  if (Number(value.schema_version) !== 1) return { liveClosed: false, reason: 'schema_version' };
  if (!String(value.source_checkpoint_id || '').trim()
    || !String(value.run_id || '').trim()
    || !String(value.wave_id || '').trim()
    || !String(value.proof_fingerprint || '').trim()
    || !String(value.accepted_head || '').trim()) {
    return { liveClosed: false, reason: 'checkpoint_identity' };
  }
  if (value.release_state !== 'NOT_RELEASED' || value.production_state !== 'NOT_CLAIMED') {
    return { liveClosed: false, reason: 'release_claim_separation' };
  }
  // If the closure projection carries these fields, they are authenticated
  // runtime facts and must not contradict the point-in-time status.
  if (Object.hasOwn(value, 'connector_refresh_required') && value.connector_refresh_required !== false) {
    return { liveClosed: false, reason: 'connector_refresh_required' };
  }
  if (Object.hasOwn(value, 'runtime_running') && value.runtime_running !== true) {
    return { liveClosed: false, reason: 'runtime_running' };
  }
  if (Object.hasOwn(value, 'tunnel_running') && value.tunnel_running !== true) {
    return { liveClosed: false, reason: 'tunnel_running' };
  }
  if (status.runtimeRunning !== true || status.tunnelRunning !== true || status.fullyReady !== true) {
    return { liveClosed: false, reason: 'runtime_status_disagreement' };
  }
  return { liveClosed: true, reason: null };
}

function renderRuntimeSourceStatus(snapshot) {
  const status = snapshot?.status || {};
  const recoveryHost = snapshot?.recoveryHost || {};
  const uiRecovery = recoveryHost.electron_ui_recovery || {};
  const electron = componentSourcePresentation(recoveryHost.electron_ui_revision, {
    running: uiRecovery.alive === true,
    label: 'Electron UI'
  });
  const recovery = componentSourcePresentation(recoveryHost.code_revision, {
    running: recoveryHost.state === 'healthy',
    label: 'Recovery Host'
  });
  const coding = componentSourcePresentation(status.codeRevision?.codingMcp, {
    running: status.runtimeRunning === true,
    label: 'Coding MCP'
  });
  const tunnel = status.tunnelRunning === true
    ? { state: 'READY', detail: 'Tunnel READY · health receipt present' }
    : { state: 'STOPPED', detail: 'Tunnel hiện chưa kết nối.' };
  const sourcePresentations = [electron, recovery, coding];
  const bindings = [
    ['#runtimeElectronState', '#runtimeElectronMeta', electron, uiRecovery.pid ? `PID ${uiRecovery.pid} · ${uiRecovery.runtime_mode || 'unknown'} · ${electron.detail}` : electron.detail],
    ['#runtimeRecoveryState', '#runtimeRecoveryMeta', recovery, recovery.detail],
    ['#runtimeMcpSourceState', '#runtimeMcpSourceMeta', coding, coding.detail],
    ['#runtimeTunnelSourceState', '#runtimeTunnelSourceMeta', tunnel, tunnel.detail]
  ];
  bindings.forEach(([stateSelector, metaSelector, presentation, detail]) => {
    const stateElement = $(stateSelector);
    const metaElement = $(metaSelector);
    if (stateElement) {
      stateElement.textContent = presentation.state;
      stateElement.dataset.state = presentation.state.toLowerCase();
    }
    if (metaElement) metaElement.textContent = detail;
  });
  const stale = sourcePresentations.filter((item) => item.state === 'STALE').length;
  const current = sourcePresentations.filter((item) => item.state === 'CURRENT').length;
  const tunnelReady = tunnel.state === 'READY';
  const summary = $('#runtimeSourceSummary');
  if (summary) {
    summary.textContent = stale
      ? `SOURCE STALE · ${stale}/3 pending · TUNNEL ${tunnel.state}`
      : `SOURCE ${current}/3 CURRENT · TUNNEL ${tunnel.state}`;
    summary.className = `cc-pill ${stale ? 'is-blocked' : current === 3 && tunnelReady ? 'is-active' : 'is-waiting'}`;
  }
  const notice = $('#sourceUpdateNotice');
  if (notice) notice.hidden = stale === 0;
  const message = $('#sourceUpdateMessage');
  if (message && stale) {
    message.textContent = `${stale} component đang chạy revision khác disk. Dùng controlled activation hoặc npm run dev; service health không thay thế loaded-source proof.`;
  }
  const closure = recoveryHost.activation_closure || snapshot?.activationClosure || status.activationClosure || {};
  const closureState = String(closure.closure_state || 'UNAVAILABLE');
  const closureDisplay = activationClosureDisplayState(closure, status);
  const liveClosed = closureDisplay.liveClosed;
  const closureElement = $('#runtimeClosureState');
  if (closureElement) {
    closureElement.textContent = closureState;
    closureElement.dataset.state = liveClosed ? 'current' : 'stale';
  }
  const closureMeta = $('#runtimeClosureMeta');
  if (closureMeta) {
    const checkpoint = shortRevision(closure.source_checkpoint_id);
    closureMeta.textContent = `${checkpoint} · release ${closure.release_state || 'NOT_RELEASED'} · production ${closure.production_state || 'NOT_CLAIMED'}`;
  }
  const closureNotice = $('#activationClosureNotice');
  if (closureNotice) closureNotice.hidden = liveClosed;
  const closureMessage = $('#activationClosureMessage');
  if (closureMessage && !liveClosed) {
    closureMessage.textContent = `${closureState}: source acceptance, exact postflight, connector freshness và runtime readiness phải cùng thuộc checkpoint hiện tại (${closureDisplay.reason}).`;
  }
}

function renderSnapshot(snapshot, options = {}) {
  state.snapshot = snapshot;
  applyFormValues(snapshot, options.forceForms);
  const { settings, secrets, environment, status } = snapshot;
  state.selectedWorkspace = settings.workspace;
  const ready = status.fullyReady;
  renderRecoveryTunnelSettings(snapshot);
  renderDevice(snapshot);
  renderRuntimeSourceStatus(snapshot);

  const activationIncomplete = status.updateIncomplete === true
    || status.activationEpoch?.update_incomplete === true
    || status.activationEpoch?.state === 'UPDATE_INCOMPLETE';
  $('#sideRuntimeText').textContent = ready
    ? 'Dịch vụ sẵn sàng'
    : activationIncomplete
      ? 'Đang hoàn tất activation epoch'
      : status.runtimeRunning ? 'Đang chờ Tunnel' : 'Dịch vụ chưa chạy';
  setDot($('#sideRuntimeDot'), ready ? 'ready' : status.runtimeRunning ? 'warn' : 'error');
  $('#sideWorkspace').textContent = settings.workspace || 'Chưa chọn thư mục làm việc';
  $('#sideMcp').textContent = status.runtimeRunning ? 'ON' : 'OFF';
  $('#sideTunnel').textContent = status.tunnelRunning ? 'ON' : 'OFF';

  $('#runtimeStatus').textContent = environment.python.installed ? 'Môi trường bình thường' : 'Thiếu môi trường runtime';
  $('#runtimeMeta').textContent = environment.python.version || 'Không tìm thấy Python tích hợp';
  setDot($('#runtimeDot'), environment.python.installed ? 'ready' : 'error');

  $('#mcpStatus').textContent = status.runtimeRunning ? 'Đang chạy bình thường' : 'Chưa khởi động';
  $('#mcpMeta').textContent = status.localMcpUrl;
  setDot($('#mcpDot'), status.runtimeRunning ? 'ready' : 'error');
  $('#tunnelStatus').textContent = status.tunnelRunning ? 'Đã kết nối' : 'Chưa kết nối';
  $('#tunnelMeta').textContent = settings.tunnelId || 'Chưa điền Tunnel ID';
  setDot($('#tunnelDot'), status.tunnelRunning ? 'ready' : settings.tunnelId ? 'warn' : 'error');
  $('#workspaceStatus').textContent = environment.workspace.exists ? 'Đã ủy quyền' : 'Chưa chọn';
  $('#workspaceMeta').textContent = settings.workspace || 'Chỉ thư mục được chọn mới có thể được MCP truy cập';
  setDot($('#workspaceDot'), environment.workspace.exists ? 'ready' : 'error');
  $('#selectedWorkspace').textContent = settings.workspace || 'Chưa chọn thư mục';
  renderAuthorizedRoots(settings.authorizedRoots || []);

  $('#heroBadge').textContent = ready
    ? 'Tất cả dịch vụ đang hoạt động bình thường'
    : activationIncomplete ? 'UPDATE_INCOMPLETE · đang đồng bộ runtime' : 'Chưa hoàn tất triển khai';
  $('#heroTitle').textContent = ready ? 'Workspace lập trình web đã sẵn sàng' : 'Cho phép Web Chat truy cập an toàn thư mục mã nguồn của bạn';
  $('#heroText').textContent = ready
    ? 'Hiện đang chạy qua môi trường portable tích hợp, trang web chỉ có thể truy cập thư mục làm việc đã chọn.'
    : 'Chọn một thư mục làm việc, cấu hình OpenAI Tunnel, sau đó trợ lý sẽ hoàn tất việc khởi động MCP, xác thực, kiểm tra sức khỏe và chẩn đoán sự cố.';
  $('#heroStartButton').textContent = ready ? 'Triển khai lại' : 'Bắt đầu triển khai';
  $('#topStartButton').textContent = ready ? 'Triển khai lại' : 'Khởi động nhanh';

  $('#runtimeKeyHint').textContent = secrets.runtimeApiKey ? 'Đã lưu bằng kho lưu trữ an toàn Windows' : 'Chưa lưu';
  $('#runtimeKeyHint').style.color = secrets.runtimeApiKey ? 'var(--green)' : '';
  $('#settingsKeyState').textContent = secrets.runtimeApiKey ? 'Đã mã hóa và lưu' : 'Chưa lưu';
  $('#guideLocalUrl').textContent = status.localMcpUrl;
  $('#guideTunnelId').textContent = settings.tunnelId || 'Chưa điền';
  const connector = connectorContractPresentation(status);
  const connectorContractNotice = $('#connectorContractNotice');
  if (connectorContractNotice) {
    connectorContractNotice.hidden = !connector.notice;
    if (connector.notice) {
      const shortHash = status.toolContract?.sha256 ? `${status.toolContract.sha256.slice(0, 12)}…` : 'không xác định';
      $('#connectorContractMessage').textContent = `${connector.message} SHA hiện tại: ${shortHash}.`;
    }
  }
  renderEnvironment(environment);
  renderDeploySummary();
}

function renderAuthorizedRoots(roots) {
  const container = $('#authorizedRootsList');
  if (!container) return;
  container.replaceChildren();
  if (!roots.length) {
    const empty = document.createElement('span');
    empty.className = 'task-muted';
    empty.textContent = 'Chưa thêm thư mục ủy quyền bổ sung';
    container.appendChild(empty);
    return;
  }
  roots.forEach((root) => {
    const row = document.createElement('div');
    row.className = 'authorized-root-row';
    const code = document.createElement('code');
    code.textContent = root;
    code.title = root;
    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'danger-button';
    remove.textContent = 'Xóa';
    remove.addEventListener('click', () => removeAuthorizedRoot(root));
    row.append(code, remove);
    container.appendChild(row);
  });
}

async function addAuthorizedRoot() {
  try {
    const selected = unwrap(await api.chooseWorkspace());
    if (!selected) return;
    const current = state.snapshot?.settings?.authorizedRoots || [];
    if (current.some((item) => item.toLowerCase() === selected.toLowerCase())) {
      toast('Thư mục đã được ủy quyền', selected);
      return;
    }
    const snapshot = unwrap(await api.updateAuthorizedRoots([...current, selected]));
    renderSnapshot(snapshot, { forceForms: true });
    toast('Đã thêm thư mục ủy quyền', selected);
  } catch (error) { toast('Ủy quyền thư mục thất bại', error.message, 'error'); }
}

async function removeAuthorizedRoot(root) {
  try {
    const current = state.snapshot?.settings?.authorizedRoots || [];
    const snapshot = unwrap(await api.updateAuthorizedRoots(current.filter((item) => item !== root)));
    renderSnapshot(snapshot, { forceForms: true });
    toast('Đã xóa thư mục ủy quyền', root);
  } catch (error) { toast('Xóa ủy quyền thất bại', error.message, 'error'); }
}

function renderEnvironment(environment) {
  setDot($('#envPythonDot'), environment.python.installed ? 'ready' : 'error');
  $('#envPythonText').textContent = environment.python.installed ? environment.python.version : 'Không tìm thấy Python 3.11+';
  const proxy = environment.proxy;
  const sourceLabels = {
    'auto-direct': 'Tự động phát hiện · Kết nối trực tiếp', 'auto-system': 'Tự động phát hiện · Proxy hệ thống Windows', 'auto-local': 'Tự động phát hiện · Proxy cục bộ',
    'system': 'Proxy hệ thống Windows', 'system-direct': 'Hệ thống không đặt Proxy · Kết nối trực tiếp', manual: 'Proxy thủ công', direct: 'Bắt buộc kết nối trực tiếp',
    'auto-unavailable': 'Không tìm thấy tuyến đường mạng khả dụng', error: 'Kiểm tra proxy thất bại'
  };
  setDot($('#envProxyDot'), proxy.reachable ? 'ready' : 'error');
  $('#envProxyText').textContent = `${sourceLabels[proxy.source] || 'Kiểm tra mạng'}${proxy.url ? ` · ${proxy.url}` : ''}`;
  $('#proxyHint').textContent = proxy.reachable ? 'Tuyến đường mạng hiện tại đã qua xác minh kết nối thực tế.' : 'Tuyến đường hiện tại chưa qua xác minh, có thể kiểm tra lại hoặc chọn proxy thủ công.';
}

function renderProxyControls() {
  const manual = $('#proxyModeSelect').value === 'manual';
  $('#manualProxyField').classList.toggle('disabled', !manual);
  $('#proxyUrlInput').disabled = !manual;
}

function renderDeploySummary() {
  const snapshot = state.snapshot;
  if (!snapshot) return;
  const missing = [];
  const workspace = state.selectedWorkspace || snapshot.settings.workspace;
  const tunnelId = $('#tunnelIdInput').value.trim();
  if (!workspace) missing.push('Thư mục làm việc');
  if (!tunnelId) missing.push('Tunnel ID');
  if (!snapshot.secrets.runtimeApiKey && !$('#runtimeKeyInput').value.trim()) missing.push('Runtime API Key');
  $('#deploySummary').textContent = missing.length ? `Còn cần điền: ${missing.join('、')}` : 'Cấu hình cần thiết cho chế độ portable đã hoàn tất.';
}

async function refreshSnapshot(options = {}) {
  try {
    const snapshot = unwrap(await api.snapshot(options));
    renderSnapshot(snapshot, options);
    return snapshot;
  } catch (error) {
    toast('Kiểm tra trạng thái thất bại', error.message, 'error');
    return null;
  }
}

function collectSettings() {
  return {
    workspace: state.selectedWorkspace,
    permissionMode: $('input[name="permission"]:checked')?.value || 'safe',
    toolMode: 'smart',
    mcpPort: Number($('#mcpPortInput').value),
    healthPort: Number($('#healthPortInput').value),
    proxyMode: $('#proxyModeSelect').value,
    proxyUrl: $('#proxyUrlInput').value.trim(),
    tunnelId: $('#tunnelIdInput').value.trim(),
    recoveryTunnelId: $('#recoveryTunnelIdInput').value.trim(),
    theme: $('#themeSelect').value,
    startWithWindows: $('#startWithWindowsToggle').checked,
    keepRunningOnClose: $('#keepRunningToggle').checked,
    autoStartServices: $('#autoStartToggle').checked,
    progressReportSeconds: Number($('#progressReportSelect').value || 90),
    guideProgress: collectGuideProgress()
  };
}

async function saveSettings(showToast = true) {
  const saved = unwrap(await api.saveSettings(collectSettings()));
  if (showToast) toast('Cài đặt đã được lưu', 'Cấu hình mới sẽ có hiệu lực ở lần triển khai tiếp theo.');
  if (state.snapshot) state.snapshot.settings = saved;
  return saved;
}

async function saveKeyIfPresent() {
  const key = $('#runtimeKeyInput').value.trim();
  if (!key) return false;
  unwrap(await api.saveRuntimeKey(key));
  $('#runtimeKeyInput').value = '';
  return true;
}

function updateProgress(payload) {
  const percent = Math.max(0, Math.min(100, Number(payload.percent || 0)));
  $('#progressPercent').textContent = `${percent}%`;
  $('#progressBar').style.width = `${percent}%`;
  $('#progressRing').style.setProperty('--value', `${percent * 3.6}deg`);
  $('#progressTitle').textContent = payload.step === 'failed' ? 'Triển khai thất bại' : payload.step === 'complete' ? 'Triển khai hoàn tất' : 'Đang thực thi nhiệm vụ triển khai';
  $('#progressMessage').textContent = payload.message;
  $('#progressBadge').textContent = payload.step === 'failed' ? 'Cần xử lý' : payload.step === 'complete' ? 'Đã hoàn thành' : 'Đang chạy';
  if (payload.step === 'failed') toast('Triển khai thất bại', payload.message, 'error');
}

async function runRuntime(action) {
  setBusy(true, false);
  navigate('overview');
  try {
    const result = unwrap(await api[action]());
    renderSnapshot(result, { forceForms: true });
    toast(action === 'stop' ? 'Dịch vụ đã dừng' : 'Thao tác hoàn tất', action === 'stop' ? 'MCP và Tunnel đã dừng an toàn.' : 'MCP và Tunnel đã qua kiểm tra sức khỏe cục bộ.');
  } catch (error) {
    toast('Thao tác thất bại', error.message, 'error');
    if (/工作目录|Thư mục làm việc|Runtime API Key|Tunnel ID|Python/.test(error.message)) navigate('deploy');
  } finally {
    setBusy(false);
    await refreshSnapshot();
  }
}

async function deployNow() {
  setBusy(true, false);
  try {
    await saveKeyIfPresent();
    await saveSettings(false);
    navigate('overview');
    const result = unwrap(await api.start());
    renderSnapshot(result, { forceForms: true });
    toast('Triển khai hoàn tất', 'Bây giờ bạn có thể làm theo trang hướng dẫn để tạo hoặc kiểm tra MCP trong ChatGPT.');
  } catch (error) {
    toast('Triển khai thất bại', error.message, 'error');
  } finally {
    setBusy(false);
    await refreshSnapshot();
  }
}

async function chooseWorkspace() {
  try {
    const selected = unwrap(await api.chooseWorkspace());
    if (!selected) return;
    state.selectedWorkspace = selected;
    $('#selectedWorkspace').textContent = selected;
    renderDeploySummary();
    toast('Đang chuyển thư mục làm việc', 'MCP sẽ âm thầm tạo lại ở chế độ nền, ChatGPT và Tunnel sẽ không bị đóng.');
    const switched = unwrap(await api.switchWorkspace(selected));
    renderSnapshot(switched, { forceForms: true });
    toast('Đã chuyển thư mục làm việc', selected);
  } catch (error) { toast('Không thể chọn thư mục', error.message, 'error'); }
}

async function copyText(text) {
  try { await navigator.clipboard.writeText(text); toast('Đã sao chép', text.length > 70 ? 'Nội dung đã được sao chép vào bộ nhớ tạm.' : text); }
  catch { toast('Sao chép thất bại', 'Vui lòng chọn và sao chép thủ công.', 'error'); }
}

function collectGuideProgress() {
  return Object.fromEntries($$('[data-guide-check]').map((input) => [input.dataset.guideCheck, input.checked]));
}

function restoreGuideProgress(progress) {
  $$('[data-guide-check]').forEach((input) => { input.checked = Boolean(progress[input.dataset.guideCheck]); });
  renderGuideProgress();
}

function renderGuideProgress() {
  const checks = $$('[data-guide-check]');
  const done = checks.filter((input) => input.checked).length;
  const percent = Math.round((done / checks.length) * 100);
  $('#guideProgressPercent').textContent = `${percent}%`;
  $('#guideProgressBar').style.width = `${percent}%`;
  checks.forEach((input, index) => {
    input.closest('.guide-step').classList.toggle('done', input.checked);
    $$('#guideChecklist li')[index]?.classList.toggle('done', input.checked);
  });
}

function appendBuildOutput(text) {
  const consoleElement = $('#buildConsole');
  const next = `${consoleElement.textContent === 'Chưa thực hiện xác minh build.' ? '' : consoleElement.textContent}${text}`;
  consoleElement.textContent = next.slice(-60000);
  consoleElement.scrollTop = consoleElement.scrollHeight;
}

function applyBuildProject(project) {
  $('#buildProjectType').textContent = `${textOr(project.type, 'unknown')} · ${textOr(project.name)}`;
  $('#buildTestCommand').value = project.testCommand || '';
  $('#buildCommand').value = project.buildCommand || '';
  $('#buildArtifacts').value = (project.artifacts || []).join(', ');
}

async function inspectBuild() {
  try { applyBuildProject(unwrap(await api.inspectBuild())); }
  catch (error) { toast('Nhận diện dự án thất bại', error.message, 'error'); }
}

function renderBuildReport(report) {
  $('#buildReportStatus').textContent = report.overallStatus === 'passed' ? 'Xác minh thành công' : 'Xác minh thất bại';
  const container = $('#buildReport'); container.replaceChildren();
  const summary = document.createElement('div'); summary.className = `build-report-summary ${report.overallStatus}`;
  summary.textContent = `${textOr(report.project?.name)} · ${textOr(report.project?.type)} · v${textOr(report.project?.version)} · Kiểm thử ${textOr(report.testResult?.status)} · Build ${textOr(report.buildResult?.status)}`;
  container.append(summary);
  (report.artifacts || []).forEach((artifact) => {
    const row = document.createElement('div'); row.className = 'build-report-artifact';
    const name = document.createElement('b'); name.textContent = textOr(artifact.path);
    const size = document.createElement('span'); size.textContent = `${Number(artifact.size || 0).toLocaleString()} bytes`;
    const hash = document.createElement('code'); hash.textContent = textOr(artifact.sha256);
    row.append(name, size, hash); container.append(row);
  });
  if (!(report.artifacts || []).length) {
    const empty = document.createElement('span'); empty.className = 'task-muted'; empty.textContent = 'Không tìm thấy sản phẩm build.'; container.append(empty);
  }
}

async function runBuildVerification() {
  $('#buildConsole').textContent = '';
  $('#buildStatus').textContent = 'Đang thực thi';
  $('#runBuild').disabled = true;
  try {
    const options = {
      testCommand: $('#buildTestCommand').value.trim(),
      buildCommand: $('#buildCommand').value.trim(),
      artifacts: $('#buildArtifacts').value.split(',').map((item) => item.trim()).filter(Boolean),
      runTests: $('#buildRunTests').checked,
      runBuild: $('#buildRunBuild').checked
    };
    const report = unwrap(await api.runBuild(options));
    renderBuildReport(report);
    $('#buildStatus').textContent = report.overallStatus === 'passed' ? 'Đã vượt qua' : 'Chưa vượt qua';
    toast(report.overallStatus === 'passed' ? 'Xác minh build thành công' : 'Xác minh build không thành công', `${report.artifacts?.length || 0} sản phẩm đã được kiểm tra`, report.overallStatus === 'passed' ? 'success' : 'error');
  } catch (error) {
    $('#buildStatus').textContent = 'Thực thi thất bại'; appendBuildOutput(`\n${error.message}\n`); toast('Xác minh build thất bại', error.message, 'error');
  } finally { $('#runBuild').disabled = false; }
}

function renderHealth(report) {
  $('#healthSummary').textContent = report.healthy ? 'Tất cả bình thường' : 'Cần xử lý';
  const container = $('#healthList'); container.replaceChildren();
  (report.checks || []).forEach((check) => {
    const row = document.createElement('div'); row.className = `health-item ${check.ok ? 'passed' : 'failed'}`;
    const mark = document.createElement('i'); mark.textContent = check.ok ? '✓' : '!';
    const copy = document.createElement('div'); const title = document.createElement('b'); title.textContent = check.label; const detail = document.createElement('small'); detail.textContent = check.detail; copy.append(title, detail);
    const status = document.createElement('span'); status.textContent = check.ok ? 'Bình thường' : 'Chờ xử lý'; row.append(mark, copy, status); container.append(row);
  });
  (report.actions || []).forEach((action) => {
    const row = document.createElement('div'); row.className = 'health-item passed';
    const mark = document.createElement('i'); mark.textContent = '↻';
    const copy = document.createElement('div'); const title = document.createElement('b'); title.textContent = 'Đã thực thi sửa chữa'; const detail = document.createElement('small'); detail.textContent = action; copy.append(title, detail);
    const status = document.createElement('span'); status.textContent = 'Hoàn thành'; row.append(mark, copy, status); container.append(row);
  });
}

async function inspectHealth() {
  try { renderHealth(unwrap(await api.inspectHealth())); }
  catch (error) { toast('Kiểm tra sức khỏe hệ thống thất bại', error.message, 'error'); }
}

async function repairHealth() {
  $('#repairHealth').disabled = true;
  try {
    const report = unwrap(await api.repairHealth()); renderHealth(report);
    toast(report.healthy ? 'Sửa chữa nhanh hoàn tất' : 'Đã hoàn thành các mục có thể xử lý tự động', report.unresolved?.length ? `Vẫn cần xử lý thủ công: ${report.unresolved.join('、')}` : 'Môi trường hiện tại đã qua kiểm tra sức khỏe.', report.healthy ? 'success' : 'error');
  } catch (error) { toast('Sửa chữa nhanh thất bại', error.message, 'error'); }
  finally { $('#repairHealth').disabled = false; }
}

function applyHeartbeat(status) {
  if (!state.snapshot || !status) return;
  if (status.signalStale === true || status.telemetryAvailable === false) {
    state.snapshot.status.signalStale = true;
    renderRecoveryTunnelSettings({ ...state.snapshot, signalStale: true });
    $('#sideRuntimeText').textContent = 'Telemetry tạm gián đoạn';
    $('#mcpStatus').textContent = 'Đang chờ heartbeat mới';
    $('#tunnelStatus').textContent = 'Đang chờ heartbeat mới';
    setDot($('#sideRuntimeDot'), 'warn');
    setDot($('#mcpDot'), 'warn');
    setDot($('#tunnelDot'), 'warn');
    return;
  }
  delete state.snapshot.status.signalStale;
  // Heartbeats are authoritative point-in-time projections. Never retain a
  // previous green closure/connector receipt when the current host omits it.
  for (const key of ['codeRevision', 'toolContract', 'connectorContractState', 'connectorRefreshRequired', 'connectorAcknowledgementPending', 'connectorRediscovered', 'connectorRediscoveredAt', 'activationClosure', 'activationEpoch', 'updateIncomplete']) {
    if (!Object.hasOwn(status, key)) delete state.snapshot.status[key];
  }
  state.snapshot.status.runtimeRunning = Boolean(status.mcpRunning);
  state.snapshot.status.tunnelRunning = Boolean(status.tunnelRunning);
  state.snapshot.status.fullyReady = Boolean(status.fullyReady);
  ['codeRevision', 'toolContract', 'connectorContractState', 'connectorRefreshRequired', 'connectorAcknowledgementPending', 'connectorRediscovered', 'connectorRediscoveredAt', 'activationClosure', 'activationEpoch', 'updateIncomplete'].forEach((key) => {
    if (Object.hasOwn(status, key)) state.snapshot.status[key] = status[key];
  });
  if (status.recoveryHost) state.snapshot.recoveryHost = status.recoveryHost;
  else delete state.snapshot.recoveryHost;
  if (status.device) state.snapshot.device = status.device;
  renderRecoveryTunnelSettings(state.snapshot);
  renderDevice(state.snapshot);
  renderRuntimeSourceStatus(state.snapshot);
  const ready = state.snapshot.status.fullyReady;
  $('#sideMcp').textContent = status.mcpRunning ? 'ON' : 'OFF';
  $('#sideTunnel').textContent = status.tunnelRunning ? 'ON' : 'OFF';
  $('#mcpStatus').textContent = status.mcpRunning ? 'Đang chạy bình thường' : 'Chưa khởi động';
  $('#tunnelStatus').textContent = status.tunnelRunning ? 'Đã kết nối' : 'Chưa kết nối';
  setDot($('#mcpDot'), status.mcpRunning ? 'ready' : 'error');
  setDot($('#tunnelDot'), status.tunnelRunning ? 'ready' : 'error');
  const activationIncomplete = status.updateIncomplete === true
    || status.activationEpoch?.update_incomplete === true
    || status.activationEpoch?.state === 'UPDATE_INCOMPLETE';
  $('#sideRuntimeText').textContent = ready
    ? 'Dịch vụ sẵn sàng'
    : activationIncomplete
      ? 'Đang hoàn tất activation epoch'
      : status.mcpRunning ? 'Đang chờ Tunnel' : 'Dịch vụ chưa chạy';
  setDot($('#sideRuntimeDot'), ready ? 'ready' : status.mcpRunning ? 'warn' : 'error');
}

async function loadLogs() {
  try {
    state.logs = unwrap(await api.logs());
    renderLogs();
  } catch (error) { toast('Đọc nhật ký thất bại', error.message, 'error'); }
}

function renderLogs() {
  const output = $('#logOutput');
  const list = state.logFilter === 'all' ? state.logs : state.logs.filter((item) => item.level === state.logFilter);
  output.replaceChildren();
  if (!list.length) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.innerHTML = '<b>Chưa có nhật ký phù hợp</b><span>Thực hiện triển khai hoặc chuyển điều kiện lọc để xem.</span>';
    output.appendChild(empty);
    return;
  }
  list.forEach((item) => {
    const row = document.createElement('div');
    row.className = `log-line ${item.level}`;
    const time = document.createElement('time');
    time.textContent = new Date(item.time).toLocaleString('vi-VN', { hour12: false });
    const level = document.createElement('em');
    level.textContent = item.level;
    const message = document.createElement('span');
    message.textContent = item.message;
    row.append(time, level, message);
    output.appendChild(row);
  });
  output.scrollTop = output.scrollHeight;
}

function bindEvents() {
  $('#closeManager')?.addEventListener('click', () => api.closeManager());
  $$('.nav-item').forEach((button) => button.addEventListener('click', () => navigate(button.dataset.page)));
  $$('[data-nav]').forEach((button) => button.addEventListener('click', () => navigate(button.dataset.nav)));
  $$('[data-open]').forEach((button) => button.addEventListener('click', async () => {
    try { unwrap(await api.openExternal(button.dataset.open)); }
    catch (error) { toast('Không thể mở trang', error.message, 'error'); }
  }));
  $$('input[name="permission"]').forEach((input) => input.addEventListener('change', () => {
    $$('.choice').forEach((choice) => choice.classList.toggle('selected', choice.contains(input) && input.checked));
  }));

  $('#refreshButton').addEventListener('click', () => refreshSnapshot());
  $('#deviceRefresh')?.addEventListener('click', () => refreshSnapshot());
  $('#deviceStart')?.addEventListener('click', () => runRuntime('start'));
  $('#deviceRestart')?.addEventListener('click', () => runRuntime('restart'));
  $('#deviceStop')?.addEventListener('click', () => runRuntime('stop'));
  $('#deviceRepair')?.addEventListener('click', async () => { await repairHealth(); await refreshSnapshot(); });
  $('#topStartButton').addEventListener('click', () => runRuntime(state.snapshot?.status.fullyReady ? 'restart' : 'start'));
  $('#heroStartButton').addEventListener('click', () => state.snapshot?.status.fullyReady ? runRuntime('restart') : navigate('deploy'));
  $('#overviewRestart').addEventListener('click', () => runRuntime('restart'));
  $('#overviewStop').addEventListener('click', () => runRuntime('stop'));
  $('#deployNow').addEventListener('click', deployNow);
  $('#chooseWorkspace').addEventListener('click', chooseWorkspace);
  $('#addAuthorizedRoot').addEventListener('click', addAuthorizedRoot);
  $('#saveDeploySettings').addEventListener('click', async () => {
    try { await saveKeyIfPresent(); await saveSettings(); await refreshSnapshot({ forceForms: true }); }
    catch (error) { toast('Lưu thất bại', error.message, 'error'); }
  });
  $('#saveWorkspace').addEventListener('click', async () => {
    try { await saveSettings(); await refreshSnapshot({ forceForms: true }); }
    catch (error) { toast('Lưu thất bại', error.message, 'error'); }
  });
  $('#saveWorkspaceRestart').addEventListener('click', async () => {
    try { await saveSettings(false); await runRuntime('restart'); }
    catch (error) { toast('Triển khai lại thất bại', error.message, 'error'); }
  });
  $('#saveRuntimeKey').addEventListener('click', async () => {
    try {
      if (!(await saveKeyIfPresent())) throw new Error('Vui lòng dán Runtime API Key trước.');
      toast('Khóa mật mã đã được lưu an toàn', 'Khóa mật mã đã được mã hóa bằng kho lưu trữ an toàn Windows.');
      await refreshSnapshot();
    } catch (error) { toast('Lưu thất bại', error.message, 'error'); }
  });
  $('#removeRuntimeKey').addEventListener('click', async () => {
    try { unwrap(await api.removeRuntimeKey()); toast('Đã xóa khóa mật mã'); await refreshSnapshot(); }
    catch (error) { toast('Xóa thất bại', error.message, 'error'); }
  });
  $('#saveRecoveryTunnel').addEventListener('click', async () => {
    try {
      const recoveryId = $('#recoveryTunnelIdInput').value.trim();
      const primaryId = $('#tunnelIdInput').value.trim() || String(state.snapshot?.settings?.tunnelId || '').trim();
      if (recoveryId && primaryId && recoveryId === primaryId) throw new Error('Tunnel cứu hộ phải dùng Tunnel ID riêng, khác Tunnel chính.');
      await saveSettings(false);
      toast('Đã lưu Tunnel cứu hộ', recoveryId ? 'Recovery Host sẽ tự thử kết nối trong vài giây.' : 'Tunnel cứu hộ đang để ở trạng thái chưa cấu hình.');
      await refreshSnapshot({ forceForms: true });
    } catch (error) { toast('Lưu Tunnel cứu hộ thất bại', error.message, 'error'); }
  });
  $('#regenerateToken').addEventListener('click', async () => {
    try { unwrap(await api.regenerateMcpToken()); toast('Token xác thực đã được tạo lại', 'Có hiệu lực sau khi triển khai lại.'); }
    catch (error) { toast('Tạo thất bại', error.message, 'error'); }
  });
  $('#clearChatSession').addEventListener('click', async () => {
    if (!confirm('Thao tác này sẽ đăng xuất ChatGPT tích hợp và xóa Cookie cũng như bộ nhớ đệm web do trợ lý này lưu. Bạn có muốn tiếp tục?')) return;
    try {
      unwrap(await api.clearChatSession());
      toast('Dữ liệu đăng nhập ChatGPT đã được xóa', 'Bạn có thể đăng nhập lại sau khi quay lại cửa sổ chat chính.');
    } catch (error) { toast('Xóa thất bại', error.message, 'error'); }
  });
  $('#pythonInstall').addEventListener('click', async () => {
    setBusy(true, true);
    try { unwrap(await api.installPython()); toast('Cài đặt Python hoàn tất', 'Vui lòng kiểm tra lại môi trường.'); await refreshSnapshot(); }
    catch (error) { toast('Cài đặt thất bại', error.message, 'error'); }
    finally { setBusy(false); }
  });
  $('#proxyModeSelect').addEventListener('change', () => { renderProxyControls(); renderDeploySummary(); });
  $('#proxyDetect').addEventListener('click', async () => {
    try {
      await saveSettings(false);
      const result = unwrap(await api.detectProxy());
      toast(result.reachable ? 'Tuyến đường mạng khả dụng' : 'Không phát hiện thấy tuyến đường khả dụng', result.resolvedUrl || (result.reachable ? 'Hiện đang sử dụng kết nối trực tiếp.' : 'Vui lòng kiểm tra cài đặt mạng hoặc proxy thủ công.'), result.reachable ? 'success' : 'error');
      await refreshSnapshot({ forceForms: true });
    } catch (error) { toast('Kiểm tra proxy thất bại', error.message, 'error'); }
  });
  ['#tunnelIdInput', '#proxyUrlInput', '#runtimeKeyInput'].forEach((selector) => $(selector).addEventListener('input', renderDeploySummary));

  $('#themeToggle').addEventListener('click', async () => {
    const next = document.body.dataset.theme === 'light' ? 'dark' : 'light';
    applyTheme(next);
    try { await saveSettings(false); } catch { /* non-critical */ }
  });
  $('#themeSelect').addEventListener('change', async () => { applyTheme($('#themeSelect').value); await saveSettings(false); });
  $('#keepRunningToggle').addEventListener('change', () => saveSettings(false));
  $('#autoStartToggle').addEventListener('change', () => saveSettings(false));

  $$('[data-guide-check]').forEach((input) => input.addEventListener('change', async () => {
    renderGuideProgress();
    try { await saveSettings(false); } catch { /* non-critical */ }
  }));
  $$('[data-copy]').forEach((button) => button.addEventListener('click', () => copyText(button.dataset.copy)));
  $('#copyLocalUrl').addEventListener('click', () => copyText($('#guideLocalUrl').textContent));
  $('#copyTunnelId').addEventListener('click', () => copyText($('#guideTunnelId').textContent));

  $('#refreshLogs').addEventListener('click', loadLogs);
  $('#refreshTaskState').addEventListener('click', loadTaskState);
  $('#refreshTaskHistory').addEventListener('click', loadTaskHistory);
  $('#pauseTask').addEventListener('click', async () => { try { unwrap(await api.pauseTask()); await loadTaskState(); toast('Nhiệm vụ đã tạm dừng', 'Tiến độ hiện tại đã được lưu trong workspace.'); } catch (error) { toast('Tạm dừng thất bại', error.message, 'error'); } });
  $('#resumeTask').addEventListener('click', async () => { try { unwrap(await api.resumeTask()); await loadTaskState(); toast('Nhiệm vụ đã tiếp tục', 'Mô hình web có thể khôi phục từ bước tiếp theo được ghi lại.'); } catch (error) { toast('Tiếp tục thất bại', error.message, 'error'); } });
  $('#stopTask').addEventListener('click', async () => { if (!confirm('Bạn có chắc chắn dừng nhiệm vụ hiện tại không? Các lệnh đang chạy sẽ bị chấm dứt.')) return; try { unwrap(await api.stopTask()); await loadTaskState(); toast('Nhiệm vụ đã dừng', 'Trạng thái và lịch sử vẫn được giữ lại, có thể tiếp tục sau.'); } catch (error) { toast('Dừng thất bại', error.message, 'error'); } });
  $('#clearTaskState').addEventListener('click', async () => { if (!confirm('Bạn có chắc chắn xóa trạng thái nhiệm vụ của workspace hiện tại không?')) return; unwrap(await api.clearTaskState()); renderTaskState(null); toast('Đã xóa trạng thái nhiệm vụ'); });
  $('#refreshPerformance').addEventListener('click', loadPerformanceTrace);
  $('#clearPerformance').addEventListener('click', async () => { if (!confirm('Bạn có chắc chắn xóa sạch các bản ghi hiệu năng của workspace hiện tại không?')) return; try { unwrap(await api.clearPerformanceTrace()); renderPerformanceTrace(null); toast('Đã xóa sạch bản ghi hiệu năng'); } catch (error) { toast('Xóa sạch thất bại', error.message, 'error'); } });
  $('#inspectBuild').addEventListener('click', inspectBuild);
  $('#runBuild').addEventListener('click', runBuildVerification);
  $('#inspectHealth').addEventListener('click', inspectHealth);
  $('#repairHealth').addEventListener('click', repairHealth);
  $('#ackConnectorContract')?.addEventListener('click', async () => {
    try {
      const snapshot = unwrap(await api.snapshot());
      renderSnapshot(snapshot, { forceForms: false });
      toast(
        'Đã kiểm tra lại tool contract',
        connectorContractPresentation(snapshot.status).toast
      );
    } catch (error) { toast('Không thể kiểm tra tool contract', error.message, 'error'); }
  });
  $('#toolModeSelect')?.addEventListener('change', async () => {
    try {
      const wasRunning = Boolean(state.snapshot?.status.runtimeRunning);
      await saveSettings(false);
      toast('Chế độ công cụ đã được lưu', wasRunning ? 'Đang âm thầm tạo lại MCP để áp dụng phạm vi công cụ mới.' : 'Có hiệu lực ở lần khởi động MCP tiếp theo.');
      if (wasRunning) await runRuntime('restart');
    } catch (error) { toast('Chuyển đổi chế độ công cụ thất bại', error.message, 'error'); }
  });
  $('#clearLogs').addEventListener('click', async () => { unwrap(await api.clearLogs()); state.logs = []; renderLogs(); toast('Đã xóa nhật ký'); });
  $$('.log-filter').forEach((button) => button.addEventListener('click', () => {
    state.logFilter = button.dataset.logFilter;
    $$('.log-filter').forEach((item) => item.classList.toggle('active', item === button));
    renderLogs();
  }));
}

async function initialize() {
  try {
    bindEvents();
    api.onProgress(updateProgress);
    api.onLog((entry) => {
      state.logs.push(entry);
      if (state.logs.length > 1000) state.logs.shift();
      if (state.currentPage === 'logs') renderLogs();
    });
    api.onStatus((payload) => {
      if (payload?.snapshot) renderSnapshot(payload.snapshot, { forceForms: false });
    });
    api.onHeartbeat(applyHeartbeat);
    api.onBuildProgress((payload) => {
      if (payload.status === 'output') appendBuildOutput(payload.text || '');
      else if (payload.status === 'running') { $('#buildStatus').textContent = payload.stage === 'test' ? 'Đang kiểm thử' : 'Đang build'; appendBuildOutput(`\n> ${payload.command}\n`); }
      else if (payload.stage === 'complete') $('#buildStatus').textContent = payload.status === 'passed' ? 'Đã vượt qua' : 'Chưa vượt qua';
    });
    const requestedPage = location.hash.slice(1);
    if (pageMeta[requestedPage]) navigate(requestedPage);

    // Show the settings shell immediately. Runtime/network inspection continues
    // in the background so opening Preferences never feels like a diagnostic run.
    document.body.classList.remove('booting');
    document.body.classList.add('booted');
    $('#bootScreen')?.setAttribute('aria-hidden', 'true');

    const firstSnapshot = await refreshSnapshot({ forceForms: true });
    if (firstSnapshot && !firstSnapshot.settings.firstRunCompleted) {
      try {
        navigate('health');
        await inspectHealth();
        unwrap(await api.saveSettings({ firstRunCompleted: true }));
        toast('Kiểm tra sức khỏe lần chạy đầu tiên', 'Đã kiểm tra môi trường hiện tại; có thể nhấp "Sửa chữa nhanh" để xử lý các vấn đề tự động.');
      } catch (error) { toast('Chưa hoàn tất kiểm tra sức khỏe lần chạy đầu tiên', error.message, 'error'); }
    }
  } finally {
    document.body.classList.remove('booting');
    document.body.classList.add('booted');
    $('#bootScreen')?.setAttribute('aria-hidden', 'true');
  }
}

initialize();
