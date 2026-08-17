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
  if (lastOrchestration) renderRouterFabric(lastOrchestration);
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

const continuityReasonLabels = {
  READY: 'Đã có Desktop + capsule + controller phù hợp',
  NO_ACTIVE_EXECUTION: 'Không có execution đang chạy',
  LEDGER_INTEGRITY_FAILED: 'Ledger integrity chưa đạt',
  TASK_NOT_RUNNABLE: 'Task đang pause/stop/fail',
  DESKTOP_OFFLINE: 'Codex Desktop chưa online qua Hub',
  CAPSULE_MISSING: 'Chưa có capsule handoff',
  CAPSULE_STALE: 'Capsule cũ hơn execution/proof hiện tại',
  CONTROLLER_HANDOFF_REQUIRED: 'Chưa chuyển semantic controller sang Codex Desktop'
};

function clientFor(data, type, id) {
  const clients = Array.isArray(data?.clients) ? data.clients : [];
  return clients.find((client) => client?.client_id === id)
    || clients.find((client) => client?.client_type === type)
    || null;
}

function renderClient(prefix, client, latestEventSeq) {
  const state = $(`#${prefix}ClientStatus`);
  const cursor = $(`#${prefix}Cursor`);
  const online = Boolean(client?.online);
  state.textContent = online ? 'online' : 'offline';
  state.className = `client-state ${online ? 'online' : 'offline'}`;
  const seq = Number(client?.cursor?.last_event_seq || 0);
  const lag = Math.max(0, Number(latestEventSeq || 0) - seq);
  cursor.textContent = client ? `cursor #${seq}${lag ? ` · lag ${lag}` : ''}` : 'cursor —';
}

function renderHub(data) {
  const latestEventSeq = Number(data?.resume_packet?.latest_event_seq || 0);
  const chatweb = clientFor(data, 'chatweb', 'chatweb');
  const desktop = clientFor(data, 'codex_desktop', 'codex-desktop');
  const opencode = clientFor(data, 'opencode', 'opencode');
  renderClient('chatweb', chatweb, latestEventSeq);
  renderClient('desktop', desktop, latestEventSeq);
  renderClient('opencode', opencode, latestEventSeq);
  const controller = data?.authority?.controller || {};
  const write = data?.authority?.write || {};
  const controllerOwner = controller.owner_client_id || 'chưa claim';
  $('#controllerLine').textContent = `Controller: ${controllerOwner} · ${controller.status || 'unclaimed'} · fence #${controller.fencing_token || 0}`;
  $('#writeAuthorityLine').textContent = write.status === 'active'
    ? `Writer: ${write.owner || 'MCP'} · ACTIVE · fence #${write.fencing_token || 0}`
    : 'Writer: Coding Tools MCP · hiện không giữ write lease';
  const onlineClientCount = [chatweb, desktop, opencode].filter((client) => client?.online).length;
  $('#hubStatus').textContent = onlineClientCount ? `${onlineClientCount} clients` : 'offline';
  $('#hubStatus').className = `badge ${onlineClientCount ? 'active' : 'stopped'}`;
  $('#toDesktopButton').disabled = !desktop?.online || controllerOwner === 'codex-desktop' || !data?.run?.run_id;
  $('#toChatWebButton').disabled = !chatweb?.online || controllerOwner === 'chatweb' || !data?.run?.run_id;
  const continuity = data?.continuity || {};
  const safe = Boolean(continuity.safe_to_rotate_chatweb);
  $('#continuityStatus').textContent = safe ? 'READY' : 'HOLD';
  $('#continuityStatus').className = `badge ${safe ? 'active' : 'blocked'}`;
  $('#rotationLine').textContent = safe ? 'SAFE TO ROTATE CHATWEB: YES' : 'SAFE TO ROTATE CHATWEB: NO';
  $('#rotationLine').className = `continuity-callout ${safe ? 'safe' : 'unsafe'}`;
  const reasons = Array.isArray(continuity.reason_codes) ? continuity.reason_codes : [];
  $('#continuityReasons').textContent = reasons.length ? reasons.map((code) => continuityReasonLabels[code] || code).join(' · ') : 'Chưa có đánh giá continuity.';
  const pressure = continuity.context_pressure || {};
  $('#contextPressureLine').textContent = pressure.status === 'unknown'
    ? 'Context ChatWeb: host không expose mức sử dụng — Hub không tự ước đoán.'
    : `Context ChatWeb: ${pressure.status || '—'}`;
  const resume = data?.resume_packet || {};
  $('#resumeLine').textContent = resume.run_id
    ? `Resume: ${resume.orchestration_state || resume.task_status || '—'} · event #${resume.latest_event_seq || 0} · ${resume.proofs?.length || 0} proof ref · ${resume.pending_message_count || 0} message chờ`
    : 'Resume: chưa có run đang hoạt động.';
  renderRouterFabric(data);
}

const routerNodeIds = {
  chatweb: 'routerChatWeb',
  desktop: 'routerDesktop',
  opencode: 'routerOpenCode',
  hub: 'routerHub',
  writer: 'routerWriter',
  fast: 'routerFast',
  terra: 'routerTerra',
  sol: 'routerSol',
  deepseek: 'routerDeepSeek'
};

const routerEdgeIds = {
  chatweb: 'routerEdgeChatWeb',
  desktop: 'routerEdgeDesktop',
  opencode: 'routerEdgeOpenCode',
  writer: 'routerEdgeWriter',
  fast: 'routerEdgeFast',
  terra: 'routerEdgeTerra',
  sol: 'routerEdgeSol',
  deepseek: 'routerEdgeDeepSeek'
};

const routerGeometry = {
  chatweb: { from: 'routerChatWeb', to: 'routerHub', fromSide: 'right', toSide: 'left', toRatio: 0.24 },
  desktop: { from: 'routerDesktop', to: 'routerHub', fromSide: 'right', toSide: 'left', toRatio: 0.5 },
  opencode: { from: 'routerOpenCode', to: 'routerHub', fromSide: 'right', toSide: 'left', toRatio: 0.76 },
  fast: { from: 'routerHub', to: 'routerFast', fromSide: 'right', toSide: 'left', fromRatio: 0.18 },
  deepseek: { from: 'routerHub', to: 'routerDeepSeek', fromSide: 'right', toSide: 'left', fromRatio: 0.38 },
  terra: { from: 'routerHub', to: 'routerTerra', fromSide: 'right', toSide: 'left', fromRatio: 0.62 },
  sol: { from: 'routerHub', to: 'routerSol', fromSide: 'right', toSide: 'left', fromRatio: 0.82 },
  writer: { from: 'routerHub', to: 'routerWriter', fromSide: 'bottom', toSide: 'top', fromRatio: 0.5, toRatio: 0.5 }
};

let routerGeometryFrame = 0;

function routerAnchor(element, side, ratio, fabricRect) {
  const rect = element.getBoundingClientRect();
  const x = rect.left - fabricRect.left;
  const y = rect.top - fabricRect.top;
  const anchorRatio = Number.isFinite(ratio) ? ratio : 0.5;
  if (side === 'left') return { x, y: y + rect.height * anchorRatio };
  if (side === 'right') return { x: x + rect.width, y: y + rect.height * anchorRatio };
  if (side === 'top') return { x: x + rect.width * anchorRatio, y };
  return { x: x + rect.width * anchorRatio, y: y + rect.height };
}

function routerCurve(start, end, vertical = false) {
  if (vertical) {
    const bend = Math.max(22, Math.min(72, Math.abs(end.y - start.y) * 0.45));
    return `M ${start.x.toFixed(1)} ${start.y.toFixed(1)} C ${start.x.toFixed(1)} ${(start.y + bend).toFixed(1)}, ${end.x.toFixed(1)} ${(end.y - bend).toFixed(1)}, ${end.x.toFixed(1)} ${end.y.toFixed(1)}`;
  }
  const bend = Math.max(30, Math.min(120, Math.abs(end.x - start.x) * 0.46));
  return `M ${start.x.toFixed(1)} ${start.y.toFixed(1)} C ${(start.x + bend).toFixed(1)} ${start.y.toFixed(1)}, ${(end.x - bend).toFixed(1)} ${end.y.toFixed(1)}, ${end.x.toFixed(1)} ${end.y.toFixed(1)}`;
}

function updateRouterGeometry() {
  const fabric = document.getElementById('routerFabric');
  const overlay = document.getElementById('routingOverlay');
  if (!fabric || !overlay) return;
  const fabricRect = fabric.getBoundingClientRect();
  if (!fabricRect.width || !fabricRect.height) return;
  overlay.setAttribute('viewBox', `0 0 ${fabricRect.width.toFixed(1)} ${fabricRect.height.toFixed(1)}`);
  for (const [key, geometry] of Object.entries(routerGeometry)) {
    const from = document.getElementById(geometry.from);
    const to = document.getElementById(geometry.to);
    const edge = document.getElementById(routerEdgeIds[key]);
    if (!from || !to || !edge) continue;
    const start = routerAnchor(from, geometry.fromSide, geometry.fromRatio, fabricRect);
    const end = routerAnchor(to, geometry.toSide, geometry.toRatio, fabricRect);
    edge.setAttribute('d', routerCurve(start, end, geometry.fromSide === 'bottom' || geometry.toSide === 'top'));
  }
}

function scheduleRouterGeometry() {
  if (routerGeometryFrame) cancelAnimationFrame(routerGeometryFrame);
  routerGeometryFrame = requestAnimationFrame(() => {
    routerGeometryFrame = 0;
    updateRouterGeometry();
  });
}

const routerStateRank = { offline: 0, connected: 1, waiting: 2, blocked: 3, active: 4 };

function mergeRouterState(current, next) {
  return routerStateRank[next] > routerStateRank[current] ? next : current;
}

function delegationRouterLane(delegation) {
  const text = `${delegation?.route_resolved || ''} ${delegation?.model || ''}`.toLowerCase();
  if (text.includes('deepseek')) return 'deepseek';
  if (text.includes('terra')) return 'terra';
  if (text.includes('sol')) return 'sol';
  if (text.includes('mini') || text.includes('luna')) return 'fast';
  return '';
}

function delegationRouterState(status) {
  const value = String(status || '').toLowerCase();
  if (['active', 'running', 'starting', 'executing', 'in_progress'].includes(value)) return 'active';
  if (['waiting', 'queued', 'pending', 'idle'].includes(value)) return 'waiting';
  if (['blocked', 'failed', 'replanned', 'interrupted'].includes(value)) return 'blocked';
  return 'offline';
}

function setRouterNode(key, state, detail) {
  const node = document.getElementById(routerNodeIds[key]);
  if (!node) return;
  node.classList.remove('offline', 'connected', 'active', 'waiting', 'blocked');
  node.classList.add(state);
  const stateLabel = node.querySelector('.router-state');
  if (stateLabel) {
    const idleWhenOffline = ['fast', 'terra', 'sol', 'deepseek', 'writer'].includes(key);
    stateLabel.textContent = state === 'connected' ? 'online' : state === 'offline' && idleWhenOffline ? 'idle' : state;
  }
  node.title = detail || state;
}

function setRouterEdge(key, state) {
  const edge = document.getElementById(routerEdgeIds[key]);
  if (!edge) return;
  edge.classList.remove('offline', 'connected', 'active', 'waiting', 'blocked');
  edge.classList.add(state);
}

function renderRouterFabric(data) {
  const chatweb = clientFor(data, 'chatweb', 'chatweb');
  const desktop = clientFor(data, 'codex_desktop', 'codex-desktop');
  const opencode = clientFor(data, 'opencode', 'opencode');
  const controllerOwner = data?.authority?.controller?.owner_client_id || '';
  const write = data?.authority?.write || {};
  const taskStatus = String(data?.task?.status || '').toLowerCase();
  const routeStates = { fast: 'offline', terra: 'offline', sol: 'offline', deepseek: 'offline' };
  const routeDetails = {
    fast: 'Không có delegation Mini/Luna đang chạy',
    terra: 'Không có delegation Terra đang chạy',
    sol: 'Không có delegation Sol đang chạy',
    deepseek: 'Không có DeepSeek delegation được Hub quan sát'
  };
  const delegations = Array.isArray(data?.delegations) ? data.delegations : [];
  delegations.forEach((delegation) => {
    const lane = delegationRouterLane(delegation);
    if (!lane) return;
    const state = delegationRouterState(delegation?.status);
    routeStates[lane] = mergeRouterState(routeStates[lane], state);
    if (state !== 'offline') routeDetails[lane] = `${delegation?.model || delegation?.route_resolved || lane} · ${delegation?.status || state}`;
  });

  const clientState = (client, controllerId) => client?.online ? (controllerOwner === controllerId ? 'active' : 'connected') : 'offline';
  const chatwebState = clientState(chatweb, 'chatweb');
  const desktopState = clientState(desktop, 'codex-desktop');
  const opencodeState = opencode?.online ? 'connected' : 'offline';
  const anyClientOnline = Boolean(chatweb?.online || desktop?.online || opencode?.online);
  const anyRouteActive = Object.values(routeStates).some((state) => state === 'active');
  const hubOnline = Boolean(lastHealth?.mcpRunning || anyClientOnline);
  const hubState = hubOnline && (taskStatus === 'active' || anyRouteActive || write.status === 'active') ? 'active' : hubOnline ? 'connected' : 'offline';
  const writerState = write.status === 'active' ? 'active' : hubOnline ? 'connected' : 'offline';

  setRouterNode('chatweb', chatwebState, chatweb?.online ? `ChatWeb · ${controllerOwner === 'chatweb' ? 'controller active' : 'observer'}` : 'ChatWeb offline');
  setRouterNode('desktop', desktopState, desktop?.online ? `Codex Desktop · ${controllerOwner === 'codex-desktop' ? 'controller active' : 'worker'}` : 'Codex Desktop offline');
  setRouterNode('opencode', opencodeState, opencode?.online ? 'OpenCode stdio proxy đang heartbeat vào Hub' : 'OpenCode offline');
  setRouterNode('hub', hubState, `Runtime ${lastHealth?.mcpRunning ? 'ready' : anyClientOnline ? 'observed through clients' : 'offline'} · task ${taskStatus || 'idle'}`);
  setRouterNode('writer', writerState, write.status === 'active' ? `Write lease active · fence #${write.fencing_token || 0}` : 'MCP proof/writer idle');
  for (const lane of ['fast', 'terra', 'sol', 'deepseek']) setRouterNode(lane, routeStates[lane], routeDetails[lane]);

  setRouterEdge('chatweb', chatwebState);
  setRouterEdge('desktop', desktopState);
  setRouterEdge('opencode', opencodeState);
  setRouterEdge('writer', writerState);
  for (const lane of ['fast', 'terra', 'sol', 'deepseek']) setRouterEdge(lane, routeStates[lane]);

  const activeRoutes = Object.values(routeStates).filter((state) => state === 'active').length;
  const onlineClients = [chatweb, desktop, opencode].filter((client) => client?.online).length;
  $('#routerSummary').textContent = `${onlineClients}/3 clients · ${activeRoutes} route active`;
  $('#routerSummary').className = `router-kpi badge ${hubState === 'active' ? 'active' : hubOnline ? 'waiting' : 'stopped'}`;
  scheduleRouterGeometry();
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

const routerResizeObserver = typeof ResizeObserver === 'function' ? new ResizeObserver(scheduleRouterGeometry) : null;
if (routerResizeObserver) {
  ['routerFabric', ...Object.values(routerNodeIds)].forEach((id) => {
    const element = document.getElementById(id);
    if (element) routerResizeObserver.observe(element);
  });
} else {
  window.addEventListener('resize', scheduleRouterGeometry);
}

document.addEventListener('visibilitychange', () => {
  document.body.classList.toggle('is-hidden', document.hidden);
  if (!document.hidden) {
    refreshOrchestration(true);
    refreshHealth(true);
  }
});

refreshHealth();
refreshOrchestration();
scheduleRouterGeometry();
setInterval(refreshOrchestration, 2000);
setInterval(refreshHealth, 5000);
setInterval(tick, 1000);
