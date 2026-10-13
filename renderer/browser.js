const api = window.browserAssistant;
const $ = (selector) => document.querySelector(selector);
let switching = false;
let activeWorkspace = '';
let lastRuntimeState = null;
let lastRuntimeCheckAt = 0;
let taskRefreshInFlight = null;
let taskBusy = false;
let workspaceRefreshInFlight = null;
let lastWorkspaceSignature = '';
const TASK_POLL_BUSY_MS = 2000;
const TASK_POLL_IDLE_MS = 5000;
const TASK_POLL_HIDDEN_MS = 15000;
const WORKSPACE_POLL_VISIBLE_MS = 15000;
const WORKSPACE_POLL_HIDDEN_MS = 60000;

function unwrap(result) {
  if (!result?.ok) throw new Error(result?.error || 'Thao tác thất bại');
  return result.data;
}

function baseName(value) {
  return String(value || '').replace(/[\\/]+$/, '').split(/[\\/]/).pop() || value || 'Chưa chọn';
}

function formatDuration(milliseconds) {
  const seconds = Math.max(0, Math.floor(Number(milliseconds || 0) / 1000));
  if (seconds < 60) return `${seconds} giây`;
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  if (minutes < 60) return `${minutes} phút ${rest} giây`;
  return `${Math.floor(minutes / 60)} giờ ${minutes % 60} phút`;
}

function progressForTask(task, status) {
  if (status === 'completed') return 100;
  const steps = Array.isArray(task?.steps) ? task.steps : [];
  if (steps.length) {
    const completed = steps.filter((step) => String(step?.status || '') === 'completed').length;
    const active = steps.filter((step) => ['in_progress', 'active', 'running'].includes(String(step?.status || ''))).length;
    return Math.max(0, Math.min(100, Math.round(((completed + active * 0.5) / steps.length) * 100)));
  }
  return null;
}

function renderServiceState(state) {
  const staleSignal = !state || state.signalStale === true || state.telemetryAvailable === false;
  const current = staleSignal && lastRuntimeState
    ? { ...lastRuntimeState, ...(state || {}), signalStale: true, telemetryAvailable: false }
    : (state || { signalStale: true, telemetryAvailable: false });
  lastRuntimeState = current;
  lastRuntimeCheckAt = Date.now();
  const failures = Number(current.failures || 0);
  const transient = current.signalStale === true || current.telemetryAvailable === false
    || current.recovering === true || current.recoveryDeferred === true;
  const central = current.executionRole === 'central_executor';
  const servicePresentation = (kind) => {
    const label = kind === 'mcp' ? 'MCP' : central ? 'Ubuntu' : 'Tunnel';
    const value = kind === 'mcp' ? current.mcpRunning : central ? current.centralConnected : current.tunnelRunning;
    if (transient || value == null) return { tone: 'warn', title: `${label}: Telemetry tạm gián đoạn` };
    if (kind === 'tunnel' && central) {
      if (value !== true) return { tone: 'warn', title: 'Ubuntu: Chưa xác nhận kết nối trung tâm; không dùng Tunnel Windows' };
      return { tone: 'ready', title: current.authorityReady === true
        ? 'Ubuntu: Đã kết nối; quyền thao tác cục bộ đã được xác minh'
        : 'Ubuntu: Đã kết nối; đang chờ quyền thao tác cục bộ' };
    }
    if (value === true) return { tone: 'ready', title: `${kind === 'mcp' ? 'MCP' : 'Tunnel'}: Đang hoạt động` };
    if (kind === 'mcp' && current.nativeAlive === true && current.mcpHealthFailureDeterministic !== true) {
      return { tone: 'warn', title: 'MCP: Process còn sống, health check đang được xác minh lại' };
    }
    if (kind === 'tunnel' && failures > 0 && failures < 3) {
      return { tone: 'warn', title: 'Tunnel: Health check tạm thời chưa xác nhận' };
    }
    return { tone: 'error', title: `${kind === 'mcp' ? 'MCP' : 'Tunnel'}: Đã dừng hoặc lỗi đã được xác nhận` };
  };
  [['#mcpState', 'mcp'], ['#tunnelState', 'tunnel']].forEach(([selector, kind]) => {
    const element = $(selector);
    if (kind === 'tunnel' && element) (element.lastChild || element).textContent = central ? 'Ubuntu' : 'Tunnel';
    if (!element) return;
    const presentation = servicePresentation(kind);
    element.classList.remove('ready', 'warn', 'error');
    element.classList.add(presentation.tone);
    element.title = presentation.title;
    element.setAttribute('aria-label', presentation.title);
  });
  const recoveryElement = $('#recoveryTunnelState');
  const recoveryTunnel = current?.recoveryHost?.recovery_plane?.tunnel || null;
  const rawState = String(recoveryTunnel?.state || '').toLowerCase();
  const deterministicRecoveryBlock = rawState.startsWith('blocked_');
  const presentation = transient
    ? { state: 'unknown', tone: 'warn', title: 'Tunnel cứu hộ: Telemetry tạm gián đoạn' }
    : rawState === 'healthy'
    ? { state: 'connected', tone: 'ready', title: 'Tunnel cứu hộ: Đã kết nối' }
    : rawState === 'starting'
      ? { state: 'connecting', tone: 'warn', title: 'Tunnel cứu hộ: Đang kết nối' }
      : rawState === 'not_configured'
        ? { state: 'not_configured', tone: '', title: 'Tunnel cứu hộ: Chưa cấu hình' }
        : deterministicRecoveryBlock
          ? { state: 'error', tone: 'error', title: `Tunnel cứu hộ: Bị chặn (${rawState})` }
          : rawState
            ? { state: 'connecting', tone: 'warn', title: `Tunnel cứu hộ: Đang xác minh lại (${rawState})` }
          : { state: 'not_configured', tone: '', title: 'Tunnel cứu hộ: Đang kiểm tra' };
  recoveryElement.classList.remove('ready', 'warn', 'error');
  if (presentation.tone) recoveryElement.classList.add(presentation.tone);
  recoveryElement.dataset.state = presentation.state;
  recoveryElement.title = presentation.title;
  recoveryElement.setAttribute('aria-label', presentation.title);
  const device = current?.device || null;
  const deviceButton = $('#deviceState');
  const deviceName = String(device?.display_name || current?.recoveryHost?.device_display_name || 'Thiết bị');
  const deviceId = String(device?.device_id || current?.recoveryHost?.device_id || '');
  deviceButton.classList.toggle('ready', !transient && Boolean(deviceId) && device?.online !== false);
  deviceButton.classList.toggle('warn', transient);
  deviceButton.classList.toggle('error', !transient && !deviceId);
  $('#deviceStateName').textContent = deviceName;
  deviceButton.title = transient ? 'Thiết bị: Chưa xác minh telemetry'
    : deviceId ? `Thiết bị hiện tại · ${deviceId}` : 'Không xác định được device_id';
  const git = device?.git || {};
  const gitElement = $('#gitState');
  const gitText = git.available ? `${git.branch || 'detached'} @ ${git.head_short || 'no-head'}${git.dirty ? ' *' : ''}` : 'Git n/a';
  $('#gitStateText').textContent = gitText;
  gitElement.classList.toggle('ready', !transient && Boolean(git.available) && git.dirty === false);
  gitElement.classList.toggle('warn', transient || (Boolean(git.available) && git.dirty === true));
  gitElement.classList.toggle('error', false);
  gitElement.title = transient ? 'Git: Chưa xác minh telemetry'
    : git.available ? `Git: ${gitText}${git.dirty ? ' · dirty' : ' · clean'}` : 'Git: không có dữ liệu';
  renderWorkspaceHealth();
}

function renderWorkspaceHealth() {
  const button = $('#workspaceHealthButton');
  if (!button) return;
  const uncertain = !lastRuntimeState || lastRuntimeState.signalStale === true
    || lastRuntimeState.telemetryAvailable === false || lastRuntimeState.recovering === true
    || lastRuntimeState.recoveryDeferred === true || typeof lastRuntimeState.mcpRunning !== 'boolean';
  const synced = Boolean(activeWorkspace && !uncertain && lastRuntimeState.mcpRunning === true);
  button.classList.toggle('ready', synced);
  button.classList.toggle('warn', Boolean(activeWorkspace) && uncertain);
  button.classList.toggle('error', Boolean(activeWorkspace) && !uncertain && !synced);
  $('#workspaceHealthName').textContent = baseName(activeWorkspace) || 'Chưa chọn workspace';
  $('#workspaceHealthPath').textContent = activeWorkspace || '-';
  $('#workspaceHealthState').textContent = !activeWorkspace ? 'Chưa chọn'
    : uncertain ? 'Chưa xác nhận telemetry' : synced ? '✓ Đã đồng bộ' : 'Chờ đồng bộ';
  $('#workspaceHealthTime').textContent = lastRuntimeCheckAt ? new Date(lastRuntimeCheckAt).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '-';
  button.title = !activeWorkspace ? 'Chưa chọn workspace'
    : uncertain ? 'Không thể xác nhận workspace khi telemetry gián đoạn'
      : synced ? 'Workspace đã đồng bộ với MCP' : 'Workspace đang chờ đồng bộ với MCP';
  renderExecutorSummary();
}

function renderExecutorSummary() {
  const state = lastRuntimeState;
  const runtime = $('#executorRuntimeState');
  const route = $('#executorPolicyState');
  if (!runtime || !route) return;
  const stale = !state || state.signalStale === true || state.telemetryAvailable === false;
  if (stale) {
    runtime.textContent = 'Chưa xác minh telemetry runtime';
    route.textContent = 'Chưa xác minh quyền theo từng thao tác';
  } else {
    runtime.textContent = state.componentsReady === true
      ? 'Các process cục bộ sẵn sàng'
      : 'Đang chờ process cục bộ';
    const central = state.executionRole === 'central_executor';
    const routeReady = central ? state.centralConnected === true : state.tunnelRunning === true;
    route.textContent = routeReady
      ? 'Đã kết nối route; quyền và receipt vẫn kiểm tra riêng'
      : 'Chưa xác minh kết nối route hoặc authority';
  }
  $('#executorWorkspaceState').textContent = activeWorkspace || 'Chưa chọn thư mục làm việc';
}

async function refreshStatus() {
  try { renderServiceState(unwrap(await api.lightweightStatus())); }
  catch { renderServiceState({ signalStale: true, telemetryAvailable: false }); }
}

async function refreshTask(force = false) {
  if (!force && document.visibilityState === 'hidden') return;
  if (taskRefreshInFlight) return taskRefreshInFlight;
  taskRefreshInFlight = (async () => {
    try {
    const control = unwrap(await api.liveOrchestration());
    const task = control?.task || null;
    const status = String(task?.status || 'idle');
    taskBusy = status === 'active';
    const strip = $('#taskStrip');
    strip.className = `task-strip ${status}`;
    $('#taskTitle').textContent = task?.objective || 'Chưa có nhiệm vụ';
    if (!task || status === 'idle') {
      $('#taskStep').textContent = '';
      $('#taskProgressBar').style.width = '0%';
      $('#taskProgressText').textContent = '';
      strip.title = '';
      return;
    }
    const now = Date.now();
    const createdAt = Date.parse(task.created_at || task.updated_at || '') || now;
    const updatedAt = Date.parse(task.updated_at || task.created_at || '') || createdAt;
    const elapsed = formatDuration(now - createdAt);
    const idleFor = now - updatedAt;
    const progress = progressForTask(task, status);
    const parts = [task.current_step || task.next_step || 'Đang xử lý nhiệm vụ'];
    const command = task.current_command && typeof task.current_command === 'object' ? task.current_command : null;
    if (command && String(command.status || '') === 'running') {
      const commandStartedAt = Date.parse(command.started_at || '') || now;
      const kind = { build: 'Build', test: 'Kiểm thử', command: 'Lệnh' }[String(command.kind || '')] || 'Lệnh';
      parts.unshift(`${kind} ${formatDuration(now - commandStartedAt)}`);
    }
    if (['active', 'paused'].includes(status)) parts.push(`Đã chạy ${elapsed}`);
    if (status === 'active' && idleFor >= 30000) parts.push(`Hoạt động gần đây ${formatDuration(idleFor)} trước`);
    if (status === 'active' && idleFor >= 120000) parts.push('Vẫn đang thực thi, không phải bị treo');
    $('#taskStep').textContent = parts.filter(Boolean).join(' · ');
    $('#taskProgressBar').style.width = progress === null ? '0%' : `${progress}%`;
    $('#taskProgressText').textContent = progress === null ? '—' : `${progress}%`;
    strip.title = `Trạng thái: ${status}; Tiến độ giai đoạn: ${progress === null ? 'chưa rõ' : `${progress}%`}; Cập nhật lần cuối: ${new Date(updatedAt).toLocaleString('vi-VN')}`;
    } catch { /* no active workspace/task yet */ }
  })();
  try { await taskRefreshInFlight; }
  finally { taskRefreshInFlight = null; }
}

function taskPollDelay() {
  if (document.visibilityState === 'hidden') return TASK_POLL_HIDDEN_MS;
  return taskBusy ? TASK_POLL_BUSY_MS : TASK_POLL_IDLE_MS;
}

async function pollTask() {
  await refreshTask(false);
  setTimeout(pollTask, taskPollDelay());
}

function renderWorkspace(hub) {
  const recentWorkspaces = Array.isArray(hub?.recentWorkspaces)
    ? hub.recentWorkspaces.filter(Boolean)
    : [];
  const nextWorkspace = String(hub?.activeWorkspace || '');
  const signature = JSON.stringify([nextWorkspace, ...recentWorkspaces]);
  const workspaceListChanged = signature !== lastWorkspaceSignature;
  activeWorkspace = nextWorkspace;
  const activeWorkspaceNode = $('#activeWorkspace');
  const activeWorkspaceText = activeWorkspace || 'Chưa chọn';
  if (activeWorkspaceNode.textContent !== activeWorkspaceText) activeWorkspaceNode.textContent = activeWorkspaceText;
  if (activeWorkspaceNode.title !== activeWorkspace) activeWorkspaceNode.title = activeWorkspace;
  renderWorkspaceHealth();
  if (!workspaceListChanged) return;
  lastWorkspaceSignature = signature;
  const chips = $('#workspaceChips');
  chips.replaceChildren();
  const select = $('#workspaceSelect');
  select.replaceChildren();
  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = `Tất cả workspace (${recentWorkspaces.length})`;
  select.appendChild(placeholder);
  recentWorkspaces.forEach((workspace) => {
    const option = document.createElement('option');
    option.value = workspace;
    option.textContent = workspace === activeWorkspace ? `Hiện tại: ${baseName(workspace)}` : baseName(workspace);
    option.title = workspace;
    select.appendChild(option);
  });
  select.value = '';
  recentWorkspaces.filter((item) => item !== activeWorkspace).slice(0, 4).forEach((workspace) => {
    const button = document.createElement('button');
    button.className = 'workspace-chip';
    button.textContent = baseName(workspace);
    button.title = workspace;
    button.onclick = () => switchWorkspace(workspace, true);
    chips.appendChild(button);
  });
}

async function refreshWorkspace(force = false) {
  if (!force && document.visibilityState === 'hidden') return;
  if (workspaceRefreshInFlight) return workspaceRefreshInFlight;
  workspaceRefreshInFlight = (async () => {
    try { renderWorkspace(unwrap(await api.workspaceHub())); }
    catch { /* retain the last usable workspace state */ }
  })();
  try { await workspaceRefreshInFlight; }
  finally { workspaceRefreshInFlight = null; }
}

function workspacePollDelay() {
  return document.visibilityState === 'hidden' ? WORKSPACE_POLL_HIDDEN_MS : WORKSPACE_POLL_VISIBLE_MS;
}

async function pollWorkspace() {
  await refreshWorkspace(false);
  setTimeout(pollWorkspace, workspacePollDelay());
}

async function switchWorkspace(workspace, showProgress = true) {
  if (switching || !workspace || workspace === activeWorkspace) return;
  switching = true;
  if (showProgress) $('#switchState').textContent = 'MCP đang chuyển workspace ở chế độ nền…';
  try {
    unwrap(await api.switchWorkspace(workspace));
    $('#switchState').textContent = 'Workspace đã sẵn sàng';
    await Promise.all([refreshWorkspace(), refreshStatus(), refreshTask()]);
    setTimeout(() => { $('#switchState').textContent = ''; }, 1800);
  } catch (error) {
    $('#switchState').textContent = error.message;
  } finally {
    switching = false;
  }
}

function renderPanelVisibility(payload) {
  const button = $('#panelToggleButton');
  if (!button) return;
  button.classList.toggle('active', Boolean(payload?.visible));
  button.title = payload?.visible
    ? 'Ẩn bảng điều khiển điều phối'
    : 'Hiện bảng điều khiển điều phối';
}

async function togglePanel() {
  try {
    const result = unwrap(await api.togglePanel());
    renderPanelVisibility(result);
  } catch (error) {
    $('#switchState').textContent = error.message;
  }
}

$('#workspaceHealthButton').onclick = (event) => {
  event.stopPropagation();
  const popover = $('#workspaceHealthPopover');
  const nextHidden = !popover.hidden;
  popover.hidden = nextHidden;
  $('#workspaceHealthButton').setAttribute('aria-expanded', String(!nextHidden));
};
document.addEventListener('click', (event) => {
  const label = $('#workspaceLabel');
  if (label?.contains(event.target)) return;
  const popover = $('#workspaceHealthPopover');
  if (popover && !popover.hidden) {
    popover.hidden = true;
    $('#workspaceHealthButton').setAttribute('aria-expanded', 'false');
  }
});
$('#managerButton').onclick = () => api.openManager();
$('#openChatGPTButton').onclick = async () => {
  const button = $('#openChatGPTButton');
  button.disabled = true;
  try {
    unwrap(await api.openChatGPT());
    $('#executorNotice').textContent = 'Đã mở trang cài đặt kết nối ChatGPT trong trình duyệt mặc định.';
  } catch (error) {
    $('#executorNotice').textContent = error.message;
  } finally {
    button.disabled = false;
  }
};
$('#deviceState').onclick = () => api.openManager();
$('#workspaceSelect').onchange = () => { const workspace = $('#workspaceSelect').value; $('#workspaceSelect').value = ''; if (workspace) switchWorkspace(workspace, true); };
$('#pauseTask').onclick = async () => { try { unwrap(await api.pauseTask()); await refreshTask(); } catch (error) { $('#switchState').textContent = error.message; } };
$('#resumeTask').onclick = async () => { try { unwrap(await api.resumeTask()); await refreshTask(); } catch (error) { $('#switchState').textContent = error.message; } };
$('#stopTask').onclick = async () => { try { unwrap(await api.stopTask()); await refreshTask(); } catch (error) { $('#switchState').textContent = error.message; } };
$('#addAuthorizedRootQuick').onclick = async () => {
  if (switching) return;
  switching = true;
  try {
    // Ubuntu permissions are registered and enabled in the folder manager.
    // Wait for an explicit legacy role before offering its local root grant.
    if (lastRuntimeState?.executionRole !== 'direct_legacy') {
      unwrap(await api.openManager('workspace'));
      $('#switchState').textContent = 'Đã mở Thư mục & quyền. Chọn thư mục và áp dụng mức quyền tại đây.';
      return;
    }
    $('#switchState').textContent = 'Vui lòng chọn thư mục bổ sung để ủy quyền…';
    const result = unwrap(await api.chooseAuthorizedRoot());
    $('#switchState').textContent = result?.selected ? `Đã ủy quyền: ${baseName(result.selected)}` : '';
  } catch (error) {
    $('#switchState').textContent = error.message;
  } finally {
    switching = false;
  }
};
$('#addWorkspace').onclick = async () => {
  if (switching) return;
  switching = true;
  $('#switchState').textContent = 'Vui lòng chọn thư mục làm việc…';
  try {
    const result = unwrap(await api.chooseAndSwitchWorkspace());
    if (result) {
      $('#switchState').textContent = 'Workspace đã thêm';
      await Promise.all([refreshWorkspace(), refreshStatus(), refreshTask()]);
    } else {
      $('#switchState').textContent = '';
    }
  } catch (error) {
    $('#switchState').textContent = error.message;
  } finally {
    switching = false;
  }
};

api.onHeartbeat(renderServiceState);
api.onPanelVisibility(renderPanelVisibility);
api.panelVisibility().then((result) => renderPanelVisibility(unwrap(result))).catch(() => {});
$('#panelToggleButton').onclick = () => togglePanel();
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState !== 'hidden') {
    void refreshTask(true);
    void refreshWorkspace(true);
  }
});
refreshStatus();
refreshWorkspace(true).finally(() => setTimeout(pollWorkspace, workspacePollDelay()));
refreshTask(true).finally(() => setTimeout(pollTask, taskPollDelay()));
