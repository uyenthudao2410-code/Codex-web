const api = window.panelAssistant;
const $ = (selector) => document.querySelector(selector);

let lastOrchestration = null;
let lastHealth = null;
let lastCommandStartedAt = 0;
let lastSyncAt = 0;
let orchestrationInFlight = null;
let healthInFlight = null;
let orchestrationError = '';
let controlPlaneState = 'unknown';
const ORCHESTRATION_POLL_BUSY_MS = 2500;
const ORCHESTRATION_POLL_IDLE_MS = 5000;
const PANEL_POLL_HIDDEN_MS = 15000;
const HEALTH_POLL_MS = 5000;

const CONTROL_PLANE_ACTION_IDS = [
  'pauseTask',
  'resumeTask',
  'stopTask',
  'handoffButton',
  'toChatWebButton',
  'toDesktopButton',
  'copyCodexConfigButton'
];
const ROUTER_KEYS = ['ChatWeb', 'Desktop', 'OpenCode', 'Hub', 'Writer', 'Fast', 'DeepSeek', 'Terra', 'Sol'];
const ROUTER_EDGE_KEYS = ['ChatWeb', 'Desktop', 'OpenCode', 'Writer', 'Fast', 'DeepSeek', 'Terra', 'Sol'];

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
  if (controlPlaneState === 'unavailable') {
    $('#syncState').textContent = 'CONTROL PLANE UNAVAILABLE';
    $('#syncState').title = orchestrationError;
    return;
  }
  if (controlPlaneState !== 'available') {
    $('#syncState').textContent = 'Chưa đồng bộ với control plane';
    $('#syncState').title = '';
    return;
  }
  $('#syncState').title = '';
  const health = lastHealth;
  if (!orchestrationError && lastSyncAt && Date.now() - lastSyncAt > 8000) {
    $('#syncState').textContent = 'Đang đồng bộ lại…';
    return;
  }
  $('#syncState').textContent = health?.fullyReady
    ? 'MCP + Tunnel sẵn sàng'
    : health?.recovering
      ? `Đang khôi phục · ${health.failures || 0} lần fail`
      : health?.recoveryBlocked
        ? `Khôi phục bị chặn: ${health.lastStartFailure || ''}`
        : 'Dịch vụ chưa sẵn sàng';
}

function setControlPlaneActionsEnabled(enabled) {
  CONTROL_PLANE_ACTION_IDS.forEach((id) => {
    const button = $(`#${id}`);
    if (button) button.disabled = !enabled;
  });
}

function renderControlPlaneUnavailable(error) {
  controlPlaneState = 'unavailable';
  orchestrationError = error?.message || String(error);
  lastOrchestration = null;
  lastSyncAt = 0;
  lastCommandStartedAt = 0;
  setControlPlaneActionsEnabled(false);

  const taskStatus = $('#taskStatus');
  taskStatus.textContent = 'Chưa đồng bộ';
  taskStatus.className = 'badge kpi-mini-badge status-waiting';
  $('#taskObjective').textContent = 'Không thể đọc control plane.';
  $('#taskPercent').textContent = '—';
  $('#taskBar').style.width = '0%';
  $('#taskStep').textContent = '—';
  $('#taskCommand').hidden = true;

  const runStatus = $('#runStatus');
  runStatus.textContent = 'Chưa đồng bộ';
  runStatus.className = 'badge kpi-mini-badge status-waiting';
  $('#runObjective').textContent = 'Không thể đọc control plane.';
  $('#waveLine').textContent = '—';
  $('#orchCounts').textContent = '';
  $('#capsuleLine').textContent = 'Không thể đọc control plane.';

  $('#eventCount').textContent = '—';
  $('#routingEvidenceKpi').textContent = 'Chưa đồng bộ';
  const hubStatus = $('#hubStatus');
  hubStatus.textContent = 'Chưa đồng bộ';
  hubStatus.className = 'text-gray';
  const continuity = $('#continuityStatus');
  continuity.textContent = 'Chưa đồng bộ';
  continuity.className = 'badge kpi-mini-badge status-hold';
  $('#runtimeActivitySummary').textContent = 'Chưa đồng bộ';

  ['#eventList', '#proofList', '#runtimeActivityList', '#delegationList'].forEach((selector) => {
    const list = $(selector);
    if (list) list.replaceChildren();
  });
  $('#delegationsSection').hidden = true;

  ROUTER_KEYS.forEach((key) => {
    setFabricState($(`#router${key}`), 'waiting');
    const label = $(`#router${key} .router-state`);
    if (label) label.textContent = '● CHƯA ĐỒNG BỘ';
  });
  ROUTER_EDGE_KEYS.forEach((key) => setFabricState($(`#routerEdge${key}`), 'waiting'));
  renderSyncState();
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
  const statusMap = { idle: 'Đang rảnh', active: 'Đang chạy', paused: 'Tạm dừng', completed: 'Hoàn thành', failed: 'Thất bại', stopped: 'Đã dừng' };
  badge.textContent = statusMap[status] || status;
  badge.className = `badge kpi-mini-badge ${status === 'active' ? 'status-active' : status === 'paused' ? 'status-waiting' : 'status-hold'}`;
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
  const authoritative = controlPlaneState === 'available';
  $('#pauseTask').disabled = !authoritative || status !== 'active';
  $('#resumeTask').disabled = !authoritative || status !== 'paused';
  $('#stopTask').disabled = !authoritative || ['idle', 'completed', 'failed', 'stopped'].includes(status);
}

function truthBadgeClass(state) {
  const normalized = String(state || 'UNKNOWN').toUpperCase();
  if (normalized === 'MATCHED') return 'badge status-active';
  if (normalized === 'MISMATCHED') return 'badge status-hold';
  if (normalized === 'NOT_APPLICABLE') return 'badge status-neutral';
  return 'badge status-waiting';
}

function setTruthBadge(id, value) {
  const el = document.getElementById(id);
  if (!el) return 'UNKNOWN';
  const allowed = new Set(['MATCHED', 'MISMATCHED', 'UNKNOWN', 'NOT_APPLICABLE']);
  const candidate = String(value || '').toUpperCase();
  const state = allowed.has(candidate) ? candidate : 'UNKNOWN';
  el.textContent = state;
  el.className = truthBadgeClass(state);
  el.dataset.state = state;
  return state;
}

function truthShort(value, fallback = 'UNKNOWN') {
  const text = String(value || '').trim();
  return text ? text.slice(0, 12) : fallback;
}

function renderTruthConsole(truthSnapshot) {
  const truth = truthSnapshot && typeof truthSnapshot === 'object' ? truthSnapshot : {};
  const source = truth.source || {};
  const runtime = truth.runtime || {};
  const orchestration = truth.orchestration || {};
  const evidence = truth.evidence || {};
  const latestProof = evidence.latest_proof || {};
  const latestCheckpoint = evidence.latest_checkpoint || {};
  const packageTruth = truth.package || {};
  const comparisons = truth.comparisons || {};

  const sourceState = document.getElementById('truthSourceState');
  const sourceMeta = document.getElementById('truthSourceMeta');
  const runtimeState = document.getElementById('truthRuntimeState');
  const runtimeMeta = document.getElementById('truthRuntimeMeta');
  const objectiveState = document.getElementById('truthObjectiveState');
  const objectiveMeta = document.getElementById('truthObjectiveMeta');
  const evidenceState = document.getElementById('truthEvidenceState');
  const evidenceMeta = document.getElementById('truthEvidenceMeta');

  if (sourceState) sourceState.textContent = truthShort(source.git_head);
  if (sourceMeta) sourceMeta.textContent = source.git_head
    ? `${source.dirty ? 'DIRTY' : 'CLEAN'} · fp ${truthShort(source.worktree_fp)}`
    : 'HEAD / worktree chưa có evidence';
  if (runtimeState) runtimeState.textContent = truthShort(runtime.code_revision);
  if (runtimeMeta) runtimeMeta.textContent = runtime.process_instance_id
    ? `process ${truthShort(runtime.process_instance_id)} · server ${truthShort(runtime.server_instance_id)}`
    : 'Loaded revision / process chưa có evidence';
  if (objectiveState) objectiveState.textContent = orchestration.objective_revision
    ? `REV ${orchestration.objective_revision}`
    : 'UNKNOWN';
  if (objectiveMeta) {
    const objective = String(orchestration.effective_objective || '').trim();
    objectiveMeta.textContent = objective
      ? `${truthShort(orchestration.run_id)} / ${truthShort(orchestration.wave_id)} · ${objective}`
      : 'RUN / WAVE / revision chưa có evidence';
  }
  if (evidenceState) evidenceState.textContent = latestProof.status
    ? String(latestProof.status).toUpperCase()
    : String(packageTruth.state || 'UNKNOWN').toUpperCase();
  if (evidenceMeta) {
    const proof = latestProof.proof_id ? `proof ${truthShort(latestProof.proof_id)}` : 'proof UNKNOWN';
    const checkpoint = latestCheckpoint.checkpoint_id
      ? `checkpoint ${truthShort(latestCheckpoint.checkpoint_id)}`
      : 'checkpoint UNKNOWN';
    evidenceMeta.textContent = `${proof} · ${checkpoint} · package ${packageTruth.state || 'UNKNOWN'}`;
  }

  const states = [
    setTruthBadge('truthRuntimeMatch', comparisons.runtime_code_vs_source_head),
    setTruthBadge('truthWaveBaseMatch', comparisons.wave_base_vs_source_head),
    setTruthBadge('truthWaveWorktreeMatch', comparisons.wave_worktree_vs_source_worktree),
    setTruthBadge('truthPackageMatch', comparisons.package_revision_vs_source_head),
  ];
  const overall = states.includes('MISMATCHED')
    ? 'MISMATCHED'
    : states.includes('UNKNOWN')
      ? 'UNKNOWN'
      : states.every((item) => item === 'NOT_APPLICABLE')
        ? 'NOT_APPLICABLE'
        : 'MATCHED';
  setTruthBadge('truthOverallState', overall);
}

function renderRun(data) {
  renderTruthConsole(data?.truth_snapshot || {});
  const run = data?.run;
  const runState = String(run?.status || 'idle');
  const runStatusMap = { idle: 'Đang rảnh', active: 'Hoạt động', running: 'Đang chạy', completed: 'Hoàn thành', failed: 'Lỗi' };
  $('#runStatus').textContent = runStatusMap[runState] || runState;
  $('#runStatus').className = `badge kpi-mini-badge ${runState === 'idle' ? 'status-waiting' : 'status-active'}`;
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
  $('#handoffButton').disabled = controlPlaneState !== 'available' || !run?.run_id;
  $('#copyCodexConfigButton').disabled = controlPlaneState !== 'available';
}

function clientFor(data, type, id) {
  const clients = Array.isArray(data?.clients) ? data.clients : [];
  return clients.find((client) => client?.client_id === id)
    || clients.find((client) => client?.client_type === type)
    || null;
}

function clientActivity(client) {
  const state = String(client?.activity_state || '').toUpperCase()
    || (client?.online ? 'ACTIVE' : client?.last_seen_at ? 'RECENT' : 'NO_SIGNAL');
  if (state === 'ACTIVE') return { state, fabric: 'active', label: '● ĐANG HOẠT ĐỘNG' };
  if (state === 'RECENT') return { state, fabric: 'connected', label: '● VỪA HOẠT ĐỘNG' };
  return { state: 'NO_SIGNAL', fabric: 'waiting', label: '● CHƯA CÓ TÍN HIỆU' };
}

function renderHub(data) {
  const chatweb = clientFor(data, 'chatweb', 'chatweb');
  const desktop = clientFor(data, 'codex_desktop', 'codex-desktop');
  const opencode = clientFor(data, 'opencode', 'opencode');
  const controller = data?.authority?.controller || {};
  const write = data?.authority?.write || {};
  const controllerOwner = controller.owner_client_id || 'chưa claim';
  const authoritative = controlPlaneState === 'available';
  const chatwebOwnsController = controllerOwner === 'chatweb' || controllerOwner.startsWith('chatweb:');
  const activities = [chatweb, desktop, opencode].map(clientActivity);
  const activeClientCount = activities.filter((item) => item.state === 'ACTIVE').length;
  const recentClientCount = activities.filter((item) => item.state === 'RECENT').length;
  $('#hubStatus').textContent = activeClientCount
    ? `${activeClientCount} hoạt động${recentClientCount ? ` · ${recentClientCount} gần đây` : ''}`
    : recentClientCount
      ? `${recentClientCount} gần đây`
      : 'Chưa có tín hiệu';
  $('#hubStatus').className = activeClientCount ? 'text-green' : recentClientCount ? 'text-orange' : 'text-gray';
  $('#toDesktopButton').disabled = !authoritative || !desktop?.online || controllerOwner === 'codex-desktop' || !data?.run?.run_id;
  $('#toChatWebButton').disabled = !authoritative || !chatweb?.online || chatwebOwnsController || !data?.run?.run_id;
  const continuity = data?.continuity || {};
  const safe = Boolean(continuity.safe_to_rotate_chatweb);
  $('#continuityStatus').textContent = safe ? 'SẴN SÀNG' : 'TẠM GIỮ';
  $('#continuityStatus').className = `badge kpi-mini-badge ${safe ? 'status-active' : 'status-hold'}`;
}

const TERMINAL_DELEGATION_STATUSES = new Set(['completed', 'failed', 'cancelled', 'stopped', 'rejected']);
const LANE_MATCHERS = [
  { key: 'Fast', test: (text) => /(?:^|[^a-z])(mini|luna)(?:[^a-z]|$)/.test(text) },
  { key: 'DeepSeek', test: (text) => text.includes('deepseek') || /(?:^|\s)opencode(?:\s|$)/.test(text) },
  { key: 'Terra', test: (text) => text.includes('terra') },
  { key: 'Sol', test: (text) => /sol_(xhigh|max|ultra)/.test(text) || /(?:^|\s)sol(?:\s|$)/.test(text) },
];

function setFabricState(element, state) {
  if (!element) return;
  element.classList.remove('active', 'connected', 'waiting', 'blocked', 'offline');
  element.classList.add(state);
}

function renderRouting(data) {
  const clients = Array.isArray(data?.clients) ? data.clients : [];
  const clientByType = (type) => clients.find((client) => client?.client_type === type);
  const frontends = [
    ['ChatWeb', clientByType('chatweb')],
    ['Desktop', clientByType('codex_desktop')],
    ['OpenCode', clientByType('opencode')],
  ];
  let activeClients = 0;
  let recentClients = 0;
  frontends.forEach(([key, client]) => {
    const activity = clientActivity(client);
    if (activity.state === 'ACTIVE') activeClients += 1;
    if (activity.state === 'RECENT') recentClients += 1;
    setFabricState($(`#router${key}`), activity.fabric);
    setFabricState($(`#routerEdge${key}`), activity.fabric);
    const label = $(`#router${key} .router-state`);
    if (label) label.textContent = activity.label;
  });

  const runtimeActivity = data?.runtime_activity || {};
  const hubState = String(runtimeActivity.state || 'IDLE').toUpperCase();
  const hubReady = Boolean(data?.runtime?.process_instance_id || data?.runtime?.server_instance_id);
  const hubVisual = !hubReady ? 'offline' : hubState === 'IDLE' ? 'connected' : 'active';
  const hubLabels = {
    IDLE: '● IDLE',
    ACTIVE: '● ACTIVE',
    WRITING: '● WRITING',
    DELEGATING: '● DELEGATING',
  };
  setFabricState($('#routerHub'), hubVisual);
  const hubLabel = $('#routerHub .router-state');
  if (hubLabel) hubLabel.textContent = hubReady ? (hubLabels[hubState] || `● ${hubState}`) : '● NGOẠI TUYẾN';

  const write = data?.authority?.write || {};
  const writing = String(write.status || '').toLowerCase() === 'active';
  setFabricState($('#routerWriter'), writing ? 'active' : hubReady ? 'connected' : 'offline');
  setFabricState($('#routerEdgeWriter'), writing ? 'active' : hubReady ? 'connected' : 'offline');
  const writerLabel = $('#routerWriter .router-state');
  if (writerLabel) writerLabel.textContent = writing ? '● ĐANG GHI' : hubReady ? '● SẴN SÀNG' : '● NGOẠI TUYẾN';

  const delegations = Array.isArray(data?.delegations) ? data.delegations : [];
  const runningCount = delegations.filter((item) => {
    const status = String(item?.status || '').toLowerCase();
    return status !== '' && !TERMINAL_DELEGATION_STATUSES.has(status);
  }).length;
  const laneEvidence = {};
  delegations.forEach((delegation) => {
    const text = `${delegation.route_resolved || ''} ${delegation.model || ''}`.toLowerCase();
    const lane = LANE_MATCHERS.find(({ test }) => test(text));
    if (!lane) return;
    const terminal = TERMINAL_DELEGATION_STATUSES.has(String(delegation.status || '').toLowerCase());
    if (!terminal) laneEvidence[lane.key] = 'active';
    else if (!laneEvidence[lane.key]) laneEvidence[lane.key] = 'connected';
  });
  const automatic = data?.provider_traffic?.automatic_routing || {};
  LANE_MATCHERS.forEach(({ key }) => {
    let state = laneEvidence[key] || '';
    let label = '';
    if (state === 'active') label = '● ĐANG HOẠT ĐỘNG';
    else if (state === 'connected') label = '● CÓ BẰNG CHỨNG';
    else if (automatic.enabled) { state = 'connected'; label = '● SẴN SÀNG'; }
    else { state = 'waiting'; label = '● CHỜ EVIDENCE'; }
    setFabricState($(`#router${key}`), state);
    setFabricState($(`#routerEdge${key}`), state);
    const laneLabel = $(`#router${key} .router-state`);
    if (laneLabel) laneLabel.textContent = label;
  });

  const kpi = $('#routingEvidenceKpi');
  if (kpi) kpi.textContent = `${activeClients}/3 active · ${recentClients} recent · ${runningCount} tuyến chạy`;
}

function renderRuntimeActivity(activity) {
  const summary = $('#runtimeActivitySummary');
  const list = $('#runtimeActivityList');
  if (!summary || !list) return;
  const state = String(activity?.state || 'IDLE').toUpperCase();
  const jobs = Array.isArray(activity?.managed_jobs) ? activity.managed_jobs : [];
  const background = Array.isArray(activity?.background_operations) ? activity.background_operations : [];
  summary.textContent = `${state} · ${Number(activity?.active_tool_calls || 0)} tool · ${Number(activity?.active_commands || 0)} command · ${Number(activity?.active_background_operations || 0)} background`;
  list.replaceChildren();
  jobs.forEach((job) => {
    const item = document.createElement('li');
    item.textContent = `PID ${job?.root_pid || '—'} · ${job?.resource_class || '—'} · ${job?.lifecycle_state || '—'} · ${String(job?.command_id || job?.job_id || '').slice(0, 24)}`;
    list.appendChild(item);
  });
  background.forEach((operation) => {
    const item = document.createElement('li');
    item.textContent = `${operation?.tool || 'background'} · ${operation?.status || 'running'} · ${Number(operation?.elapsed_seconds || 0)}s · ${String(operation?.operation_id || '').slice(0, 24)}`;
    list.appendChild(item);
  });
  if (!jobs.length && !background.length) {
    const item = document.createElement('li');
    item.textContent = 'Không có command/background job đang hoạt động.';
    list.appendChild(item);
  }
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
      controlPlaneState = 'available';
      orchestrationError = '';
      lastSyncAt = Date.now();
      lastOrchestration = data;
      renderTask(data?.task);
      renderRun(data);
      renderHub(data);
      renderRouting(data);
      renderRuntimeActivity(data?.runtime_activity);
      renderEvents(data?.events);
      renderProofs(data?.proofs);
      renderDelegations(data?.delegations);
      renderSyncState();
    } catch (error) {
      renderControlPlaneUnavailable(error);
    } finally {
      orchestrationInFlight = null;
    }
  })();
  return orchestrationInFlight;
}

async function refreshHealth(force = false) {
  if (document.hidden && !force) return;
  if (healthInFlight) return healthInFlight;
  healthInFlight = (async () => {
    try { renderHealth(unwrap(await api.health())); }
    catch {
      lastHealth = null;
      ['#mcpDot', '#tunnelDot'].forEach((selector) => {
        const element = $(selector);
        element.classList.remove('ready');
        element.title = 'Không đọc được trạng thái dịch vụ';
      });
      renderSyncState();
    } finally {
      healthInFlight = null;
    }
  })();
  return healthInFlight;
}

function orchestrationBusy() {
  const taskStatus = String(lastOrchestration?.task?.status || '').toLowerCase();
  const runtimeState = String(lastOrchestration?.runtime_activity?.state || '').toUpperCase();
  return taskStatus === 'active' || ['ACTIVE', 'WRITING', 'DELEGATING'].includes(runtimeState);
}

function orchestrationPollDelay() {
  if (document.hidden) return PANEL_POLL_HIDDEN_MS;
  return orchestrationBusy() ? ORCHESTRATION_POLL_BUSY_MS : ORCHESTRATION_POLL_IDLE_MS;
}

async function pollOrchestration() {
  await refreshOrchestration(false);
  setTimeout(pollOrchestration, orchestrationPollDelay());
}

async function pollHealth() {
  await refreshHealth(false);
  setTimeout(pollHealth, document.hidden ? PANEL_POLL_HIDDEN_MS : HEALTH_POLL_MS);
}

async function taskAction(action) {
  if (controlPlaneState !== 'available') return;
  try {
    if (action === 'pause') unwrap(await api.pauseTask());
    else if (action === 'resume') unwrap(await api.resumeTask());
    else if (action === 'stop') unwrap(await api.stopTask());
    await refreshOrchestration();
  } catch (error) {
    renderControlPlaneUnavailable(error);
  }
}

async function recordHandoff() {
  if (controlPlaneState !== 'available') return;
  const button = $('#handoffButton');
  button.disabled = true;
  try {
    const result = unwrap(await api.handoff());
    await refreshOrchestration();
    alert(`Đã ghi Capsule thành công (v${result.version}). Bạn có thể mở chat mới an toàn.`);
  } catch (error) {
    renderControlPlaneUnavailable(error);
    alert(`Lỗi ghi capsule: ${error.message}`);
  } finally {
    button.disabled = controlPlaneState !== 'available' || !lastOrchestration?.run?.run_id;
  }
}

async function transferController(target) {
  if (controlPlaneState !== 'available') return;
  const confirmMsg = target === 'codex-desktop'
    ? 'Chuyển quyền điều khiển chính sang Codex Desktop?'
    : 'Chuyển quyền điều khiển chính sang ChatWeb?';
  if (!window.confirm(confirmMsg)) return;
  try {
    unwrap(await api.transferController(target));
    await refreshOrchestration();
  } catch (error) {
    renderControlPlaneUnavailable(error);
    alert(`Lỗi chuyển quyền: ${error.message}`);
  }
}

async function copyCodexConfig() {
  if (controlPlaneState !== 'available') return;
  try {
    const config = unwrap(await api.copyCodexConfig());
    await navigator.clipboard.writeText(JSON.stringify(config, null, 2));
    alert('Đã sao chép cấu hình MCP vào clipboard.');
  } catch (error) {
    alert(`Lỗi sao chép cấu hình: ${error.message}`);
  }
}

function updateClock() {
  const now = new Date();
  $('#clock').textContent = now.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  if (lastCommandStartedAt) {
    const duration = formatDuration(Date.now() - lastCommandStartedAt);
    const cmdEl = $('#taskCommand');
    if (cmdEl && !cmdEl.hidden) {
      const parts = cmdEl.textContent.split(' (');
      if (parts.length > 1) {
        cmdEl.textContent = `${parts[0]} (${duration})`;
      }
    }
  }
}

// Bind event listeners
$('#pauseTask').addEventListener('click', () => taskAction('pause'));
$('#resumeTask').addEventListener('click', () => taskAction('resume'));
$('#stopTask').addEventListener('click', () => taskAction('stop'));
$('#handoffButton').addEventListener('click', recordHandoff);
$('#refreshButton').addEventListener('click', () => { refreshOrchestration(true); refreshHealth(true); });
$('#toDesktopButton').addEventListener('click', () => transferController('codex-desktop'));
$('#toChatWebButton').addEventListener('click', () => transferController('chatweb'));
$('#copyCodexConfigButton').addEventListener('click', copyCodexConfig);
$('#closeButton').addEventListener('click', () => api.close());

document.addEventListener('visibilitychange', () => {
  if (!document.hidden) {
    refreshOrchestration(true);
    refreshHealth(true);
  }
});

setInterval(updateClock, 1000);

// Initial call
refreshOrchestration(true).finally(() => setTimeout(pollOrchestration, orchestrationPollDelay()));
refreshHealth(true).finally(() => setTimeout(pollHealth, document.hidden ? PANEL_POLL_HIDDEN_MS : HEALTH_POLL_MS));
updateClock();
