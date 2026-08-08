const api = window.browserAssistant;
const $ = (selector) => document.querySelector(selector);
let switching = false;
let activeWorkspace = '';
let lastRuntimeState = null;
let lastRuntimeCheckAt = 0;

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
    return Math.max(status === 'active' ? 5 : 0, Math.min(99, Math.round(((completed + active * 0.5) / steps.length) * 100)));
  }
  const kind = String(task?.current_command?.kind || '');
  if (kind === 'build') return 85;
  if (kind === 'test') return 72;
  if (kind === 'command') return 52;
  const step = String(task?.current_step || '').toLowerCase();
  if (step.includes('completed')) return 100;
  if (step.includes('build')) return 82;
  if (step.includes('test') || step.includes('verify')) return 70;
  if (step.includes('apply') || step.includes('modify') || step.includes('patch')) return 42;
  if (status === 'waiting') return 62;
  if (status === 'paused') return 50;
  if (status === 'failed' || status === 'stopped') return 100;
  return status === 'active' ? 18 : 0;
}

function renderChatState(state) {
  if (!state) return;
  $('#backButton').disabled = !state.canGoBack;
  $('#forwardButton').disabled = !state.canGoForward;
  const element = $('#pageState');
  element.classList.toggle('loading', Boolean(state.loading));
  element.classList.toggle('ready', !state.loading && !state.error);
  element.classList.toggle('error', Boolean(state.error));
  element.querySelector('span').textContent = state.error
    ? `Tải thất bại: ${state.error}`
    : state.loading ? 'Đang chuyển trang…' : 'ChatGPT đã sẵn sàng';
}

function renderServiceState(state) {
  lastRuntimeState = state || null;
  lastRuntimeCheckAt = Date.now();
  [['#mcpState', state?.mcpRunning], ['#tunnelState', state?.tunnelRunning]].forEach(([selector, value]) => {
    const element = $(selector);
    element.classList.toggle('ready', Boolean(value));
    element.classList.toggle('error', !value);
  });
  renderWorkspaceHealth();
}

function renderWorkspaceHealth() {
  const button = $('#workspaceHealthButton');
  if (!button) return;
  const synced = Boolean(activeWorkspace && lastRuntimeState?.mcpRunning);
  button.classList.toggle('ready', synced);
  button.classList.toggle('error', Boolean(activeWorkspace) && !synced);
  $('#workspaceHealthName').textContent = baseName(activeWorkspace) || 'Chưa chọn workspace';
  $('#workspaceHealthPath').textContent = activeWorkspace || '-';
  $('#workspaceHealthState').textContent = !activeWorkspace ? 'Chưa chọn' : synced ? '✓ Đã đồng bộ' : lastRuntimeState?.recovering ? 'Đang khôi phục' : 'Chờ đồng bộ';
  $('#workspaceHealthTime').textContent = lastRuntimeCheckAt ? new Date(lastRuntimeCheckAt).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '-';
  button.title = !activeWorkspace ? 'Chưa chọn workspace' : synced ? 'Workspace đã đồng bộ với MCP' : 'Workspace đang chờ đồng bộ với MCP';
}

async function refreshStatus() {
  try { renderServiceState(unwrap(await api.lightweightStatus())); }
  catch { renderServiceState(null); }
}

async function refreshTask() {
  try {
    const payload = unwrap(await api.taskState());
    const task = payload?.state;
    const status = String(task?.status || 'idle');
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
    $('#taskProgressBar').style.width = `${progress}%`;
    $('#taskProgressText').textContent = `${progress}%`;
    strip.title = `Trạng thái: ${status}; Tiến độ giai đoạn: ${progress}%; Cập nhật lần cuối: ${new Date(updatedAt).toLocaleString('vi-VN')}`;
  } catch { /* no active workspace/task yet */ }
}

function renderWorkspace(hub) {
  activeWorkspace = hub.activeWorkspace || '';
  $('#activeWorkspace').textContent = activeWorkspace || 'Chưa chọn';
  $('#activeWorkspace').title = activeWorkspace;
  renderWorkspaceHealth();
  const chips = $('#workspaceChips');
  chips.replaceChildren();
  const select = $('#workspaceSelect');
  select.replaceChildren();
  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = `Tất cả workspace (${(hub.recentWorkspaces || []).length})`;
  select.appendChild(placeholder);
  (hub.recentWorkspaces || []).filter(Boolean).forEach((workspace) => {
    const option = document.createElement('option');
    option.value = workspace;
    option.textContent = workspace === activeWorkspace ? `Hiện tại: ${baseName(workspace)}` : baseName(workspace);
    option.title = workspace;
    select.appendChild(option);
  });
  select.value = '';
  (hub.recentWorkspaces || []).filter((item) => item && item !== activeWorkspace).slice(0, 4).forEach((workspace) => {
    const button = document.createElement('button');
    button.className = 'workspace-chip';
    button.textContent = baseName(workspace);
    button.title = workspace;
    button.onclick = () => switchWorkspace(workspace, true);
    chips.appendChild(button);
  });
}

async function refreshWorkspace() {
  try { renderWorkspace(unwrap(await api.workspaceHub())); }
  catch { /* retain the last usable workspace state */ }
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

async function navigate(action) {
  try { unwrap(await api.navigate(action)); }
  catch (error) { renderChatState({ error: error.message }); }
}

$('#backButton').onclick = () => navigate('back');
$('#forwardButton').onclick = () => navigate('forward');
$('#reloadButton').onclick = () => navigate('reload');
$('#homeButton').onclick = () => navigate('home');
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
$('#workspaceSelect').onchange = () => { const workspace = $('#workspaceSelect').value; $('#workspaceSelect').value = ''; if (workspace) switchWorkspace(workspace, true); };
$('#pauseTask').onclick = async () => { try { unwrap(await api.pauseTask()); await refreshTask(); } catch (error) { $('#switchState').textContent = error.message; } };
$('#resumeTask').onclick = async () => { try { unwrap(await api.resumeTask()); await refreshTask(); } catch (error) { $('#switchState').textContent = error.message; } };
$('#stopTask').onclick = async () => { try { unwrap(await api.stopTask()); await refreshTask(); } catch (error) { $('#switchState').textContent = error.message; } };
$('#addAuthorizedRootQuick').onclick = async () => {
  if (switching) return;
  switching = true;
  $('#switchState').textContent = 'Vui lòng chọn thư mục bổ sung để ủy quyền…';
  try {
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

api.onChatState(renderChatState);
api.onHeartbeat(renderServiceState);
api.onDownload((item) => {
  const node = $('#downloadState');
  if (item.status === 'completed') node.textContent = `Đã lưu: ${baseName(item.path)}`;
  else if (item.status === 'progressing') node.textContent = `Tệp đính kèm ${item.totalBytes ? Math.round((item.receivedBytes / item.totalBytes) * 100) : 0}%`;
  else if (item.error) node.textContent = item.error;
});
api.chatStatus().then((result) => renderChatState(unwrap(result))).catch(() => {});
refreshStatus();
refreshWorkspace();
refreshTask();
setInterval(refreshWorkspace, 15000);
setInterval(refreshTask, 1200);
