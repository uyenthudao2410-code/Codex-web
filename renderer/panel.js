const api = window.panelAssistant;
const $ = (selector) => document.querySelector(selector);

let lastOrchestration = null;
let lastHealth = null;
let lastCommandStartedAt = 0;
let lastSyncAt = 0;
let orchestrationInFlight = null;
let orchestrationError = '';

function unwrap(result) {
  if (!result?.ok) throw new Error(result?.error || 'Thao tác thất bại');
  return result.data;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[char]));
}

function shortTime(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return escapeHtml(value).slice(0, 8);
  return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function formatDuration(milliseconds) {
  const seconds = Math.max(0, Math.floor(Number(milliseconds || 0) / 1000));
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ${seconds % 60}s`;
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
}

function taskProgress(task, status) {
  if (status === 'completed' || status === 'failed' || status === 'stopped') return 100;
  const steps = Array.isArray(task?.steps) ? task.steps : [];
  if (steps.length) {
    const done = steps.filter((step) => String(step?.status || '') === 'completed').length;
    return Math.min(99, Math.max(5, Math.round((done / steps.length) * 100)));
  }
  const step = String(task?.current_step || '').toLowerCase();
  if (step.includes('build')) return 82;
  if (step.includes('test') || step.includes('verify')) return 70;
  if (step.includes('patch') || step.includes('apply')) return 42;
  return status === 'active' ? 18 : 0;
}

function renderSyncState() {
  if (orchestrationError) {
    $('#syncState').textContent = `Điều phối lỗi: ${orchestrationError}`;
    return;
  }
  const health = lastHealth;
  $('#syncState').textContent = health?.fullyReady
    ? 'MCP + Tunnel sẵn sàng'
    : health?.recovering
      ? `Đang khôi phục · ${health.failures || 0} lần fail`
      : health?.recoveryBlocked
        ? `Khôi phục bị chặn: ${health.lastStartFailure || ''}`
        : 'Dịch vụ chưa sẵn sàng';
}

function renderHealth(health) {
  lastHealth = health;
  [['#mcpDot', health?.mcpRunning], ['#tunnelDot', health?.tunnelRunning]].forEach(([selector, value]) => {
    const element = $(selector);
    element.classList.toggle('ready', Boolean(value));
  });
  if (health?.recovering) {
    $('#mcpDot').title = `Đang khôi phục (lần ${health.failures || 0})`;
  }
  renderSyncState();
}

function renderTask(task) {
  const status = String(task?.status || 'idle');
  const badge = $('#taskStatus');
  badge.textContent = status === 'idle' ? 'chưa có' : status;
  badge.className = `badge ${status}`;
  $('#taskObjective').textContent = task?.objective || 'Chưa có nhiệm vụ đang chạy.';
  const progress = taskProgress(task, status);
  $('#taskBar').style.width = `${progress}%`;
  $('#taskPercent').textContent = status === 'idle' ? '' : `${progress}%`;
  const parts = [];
  if (task?.current_step) parts.push(task.current_step);
  if (task?.next_step && status !== 'active') parts.push(`→ ${task.next_step}`);
  if (task?.modified_files?.length) parts.push(`${task.modified_files.length} file đã sửa`);
  if (status === 'paused' && task?.pause_reason) parts.push(task.pause_reason);
  $('#taskStep').textContent = parts.join(' · ') || '—';

  const command = task?.current_command;
  if (command && String(command.status || '') === 'running') {
    const started = Date.parse(command.started_at || '') || 0;
    if (started) lastCommandStartedAt = started;
    const kind = { build: 'Build', test: 'Kiểm thử', command: 'Lệnh' }[String(command.kind || '')] || 'Lệnh';
    $('#taskCommand').textContent = `${kind}: ${String(command.command || '').slice(0, 120)} (${formatDuration(Date.now() - (started || Date.now()))})`;
    $('#taskCommand').hidden = false;
  } else {
    lastCommandStartedAt = 0;
    $('#taskCommand').hidden = true;
  }
}

function renderRun(data) {
  const run = data?.run;
  $('#runStatus').textContent = run?.status || 'chưa có';
  $('#runStatus').className = `badge ${run?.status || ''}`;
  $('#runObjective').textContent = run?.objective || 'Chưa có run điều phối.';

  const waves = Array.isArray(data?.waves) ? data.waves : [];
  const wave = waves[waves.length - 1];
  if (wave) {
    const base = String(wave.base_head || '').slice(0, 7);
    $('#waveLine').textContent = `Wave ${wave.ordinal} · ${wave.execution_mode} · ${wave.status} · base ${base}`;
  } else {
    $('#waveLine').textContent = 'Chưa có wave.';
  }
  const counts = data?.counts;
  if (counts) {
    $('#orchCounts').textContent = `${counts.events} sự kiện · ${counts.waves} wave · ${counts.checkpoints} checkpoint`;
  }
  const capsule = data?.capsule;
  $('#capsuleLine').textContent = capsule
    ? `Capsule: ${shortTime(capsule.created_at)} · v${capsule.version} · ${capsule.status}`
    : 'Chưa có capsule handoff — ghi trước khi xoay chat mới.';
}

function clientFor(data, type, id) {
  const clients = Array.isArray(data?.clients) ? data.clients : [];
  return clients.find((client) => client?.client_id === id)
    || clients.find((client) => client?.client_type === type)
    || null;
}

function renderHub(data) {
  const chatweb = clientFor(data, 'chatweb', 'chatweb');
  const desktop = clientFor(data, 'codex_desktop', 'codex-desktop');
  const opencode = clientFor(data, 'opencode', 'opencode');
  const controller = data?.authority?.controller || {};
  const write = data?.authority?.write || {};
  const controllerOwner = controller.owner_client_id || 'chưa claim';
  const onlineClientCount = [chatweb, desktop, opencode].filter((client) => client?.online).length;
  $('#hubStatus').textContent = onlineClientCount ? `${onlineClientCount} clients` : 'offline';
  $('#hubStatus').className = `badge ${onlineClientCount ? 'active' : 'stopped'}`;
  $('#toDesktopButton').disabled = !desktop?.online || controllerOwner === 'codex-desktop' || !data?.run?.run_id;
  $('#toChatWebButton').disabled = !chatweb?.online || controllerOwner === 'chatweb' || !data?.run?.run_id;
  const continuity = data?.continuity || {};
  const safe = Boolean(continuity.safe_to_rotate_chatweb);
  $('#continuityStatus').textContent = safe ? 'READY' : 'HOLD';
  $('#continuityStatus').className = `badge ${safe ? 'active' : 'blocked'}`;
  }

function renderEvents(events) {
  const list = $('#eventList');
  const items = Array.isArray(events) ? events : [];
  $('#eventCount').textContent = String(items.length);
  list.replaceChildren();
  items.slice().reverse().forEach((event) => {
    const item = document.createElement('li');
    const time = document.createElement('span');
    time.className = 'event-time';
    time.textContent = shortTime(event.event_time);
    const body = document.createElement('div');
    const type = document.createElement('div');
    type.className = 'event-type';
    const flow = event.state_before || event.state_after
      ? ` <span class="flow">${escapeHtml(event.state_before || '·')} → ${escapeHtml(event.state_after || '·')}</span>`
      : '';
    type.innerHTML = `${escapeHtml(event.event_type)}${flow}`;
    const meta = document.createElement('div');
    meta.className = 'event-meta';
    meta.textContent = event.payload ? String(event.payload).slice(0, 160) : '';
    body.append(type, meta);
    item.append(time, body);
    list.appendChild(item);
  });
}

function renderProofs(proofs) {
  const list = $('#proofList');
  const items = Array.isArray(proofs) ? proofs : [];
  list.replaceChildren();
  if (!items.length) {
    list.textContent = 'Chưa có bằng chứng nào.';
    return;
  }
  items.forEach((proof) => {
    const item = document.createElement('li');
    const stage = document.createElement('span');
    stage.className = 'stage';
    stage.textContent = String(proof.stage_id || '').slice(0, 46);
    const result = document.createElement('span');
    result.className = `result ${proof.status}`;
    result.textContent = proof.status;
    const duration = document.createElement('span');
    duration.className = 'duration';
    duration.textContent = proof.duration_ms != null ? `${proof.duration_ms}ms` : '';
    item.append(stage, result, duration);
    list.appendChild(item);
  });
}

function renderDelegations(delegations) {
  const section = $('#delegationsSection');
  const items = Array.isArray(delegations) ? delegations : [];
  section.hidden = items.length === 0;
  if (!items.length) return;
  const list = $('#delegationList');
  list.replaceChildren();
  items.forEach((delegation) => {
    const item = document.createElement('li');
    item.innerHTML = `<span class="route">${escapeHtml(delegation.route_resolved || '—')}</span> `
      + `${escapeHtml(delegation.model || '')} · ${escapeHtml(delegation.effort || '')} · `
      + `<span class="badge ${escapeHtml(delegation.status || '')}">${escapeHtml(delegation.status || '')}</span>`;
    list.appendChild(item);
  });
}

async function refreshOrchestration(force = false) {
  if (document.hidden && !force) return;
  if (orchestrationInFlight) return orchestrationInFlight;
  orchestrationInFlight = (async () => {
    try {
      const data = unwrap(await api.orchestration());
      lastOrchestration = data;
      renderTask(data?.task);
      renderRun(data);
      renderHub(data);
      renderEvents(data?.events);
      renderProofs(data?.proofs);
      renderDelegations(data?.delegations);
      orchestrationError = '';
      lastSyncAt = Date.now();
      renderSyncState();
    } catch (error) {
      orchestrationError = error?.message || String(error);
      renderSyncState();
    } finally {
      orchestrationInFlight = null;
    }
  })();
  return orchestrationInFlight;
}

async function refreshHealth(force = false) {
  if (document.hidden && !force) return;
  try { renderHealth(unwrap(await api.health())); }
  catch { /* giữ trạng thái cũ */ }
}

async function taskAction(action) {
  try {
    if (action === 'pause') unwrap(await api.pauseTask());
    else if (action === 'resume') unwrap(await api.resumeTask());
    else if (action === 'stop') unwrap(await api.stopTask());
    await refreshOrchestration();
  } catch (error) {
    $('#syncState').textContent = error.message;
  }
}

async function recordHandoff() {
  const button = $('#handoffButton');
  button.disabled = true;
  try {
    unwrap(await api.handoff({ summary: lastOrchestration?.task?.objective || '' }));
    $('#syncState').textContent = 'Đã ghi capsule handoff — có thể mở chat mới.';
    await refreshOrchestration();
  } catch (error) {
    $('#syncState').textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

async function transferController(targetClientId) {
  const label = targetClientId === 'codex-desktop' ? 'Codex Desktop' : 'ChatWeb';
  if (!window.confirm(`Chuyển semantic controller sang ${label}? Thao tác này đổi fencing token nhưng không copy transcript hay bật auto-handoff.`)) return;
  const button = targetClientId === 'codex-desktop' ? $('#toDesktopButton') : $('#toChatWebButton');
  button.disabled = true;
  try {
    unwrap(await api.transferController({ targetClientId, runId: lastOrchestration?.run?.run_id || '' }));
    $('#syncState').textContent = `Đã chuyển controller sang ${label}.`;
    await refreshOrchestration();
  } catch (error) {
    $('#syncState').textContent = error.message;
  }
}

async function copyCodexConfig() {
  const button = $('#copyCodexConfigButton');
  button.disabled = true;
  try {
    const result = unwrap(await api.copyCodexConfig());
    $('#syncState').textContent = result?.copied
      ? 'Đã copy cấu hình Codex Desktop thin proxy — không chứa MCP bearer.'
      : 'Không thể copy cấu hình Codex Desktop.';
  } catch (error) {
    $('#syncState').textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

function tick() {
  $('#clock').textContent = new Date().toLocaleTimeString('vi-VN');
  if (lastCommandStartedAt) {
    const command = lastOrchestration?.task?.current_command;
    if (command && String(command.status || '') === 'running') {
      const kind = { build: 'Build', test: 'Kiểm thử', command: 'Lệnh' }[String(command.kind || '')] || 'Lệnh';
      $('#taskCommand').textContent = `${kind}: ${String(command.command || '').slice(0, 120)} (${formatDuration(Date.now() - lastCommandStartedAt)})`;
    }
  }
  if (!orchestrationError && lastSyncAt && Date.now() - lastSyncAt > 8000) {
    $('#syncState').textContent = `Dữ liệu cũ hơn ${Math.round((Date.now() - lastSyncAt) / 1000)}s — kiểm tra MCP`;
  }
}

$('#closeButton').onclick = () => api.close();
$('#pauseTask').onclick = () => taskAction('pause');
$('#resumeTask').onclick = () => taskAction('resume');
$('#stopTask').onclick = () => taskAction('stop');
$('#handoffButton').onclick = () => recordHandoff();
$('#toDesktopButton').onclick = () => transferController('codex-desktop');
$('#toChatWebButton').onclick = () => transferController('chatweb');
$('#copyCodexConfigButton').onclick = () => copyCodexConfig();
$('#refreshButton').onclick = () => { refreshOrchestration(true); refreshHealth(true); };

document.addEventListener('visibilitychange', () => {
  document.body.classList.toggle('is-hidden', document.hidden);
  if (!document.hidden) {
    refreshOrchestration(true);
    refreshHealth(true);
  }
});

refreshHealth();
refreshOrchestration();
setInterval(refreshOrchestration, 2000);
setInterval(refreshHealth, 5000);
setInterval(tick, 1000);
