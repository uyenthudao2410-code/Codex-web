(() => {
  'use strict';

  const api = window.mcpAssistant;
  if (!api) return;

  const ROUTER_KEYS = ['chatweb', 'desktop', 'opencode', 'fast', 'hub', 'deepseek', 'terra', 'writer', 'sol'];
  const COMPUTE_KEYS = ['fast', 'deepseek', 'terra', 'sol'];
  const STATE_RANK = { offline: 0, connected: 1, waiting: 2, blocked: 3, active: 4 };
  const NODE_SUFFIX = {
    chatweb: 'ChatWeb', desktop: 'Desktop', opencode: 'OpenCode', fast: 'Fast', hub: 'Hub',
    deepseek: 'DeepSeek', terra: 'Terra', writer: 'Writer', sol: 'Sol'
  };
  const SVG_NS = 'http://www.w3.org/2000/svg';

  let snapshot = null;
  let orchestration = null;
  let performance = null;
  let refreshInFlight = false;
  let lastPerformanceRead = 0;
  const CONTROL_CENTER_BUSY_POLL_MS = 4000;
  const CONTROL_CENTER_IDLE_POLL_MS = 6000;
  const CONTROL_CENTER_HIDDEN_POLL_MS = 15000;
  const motionQuery = window.matchMedia?.('(prefers-reduced-motion: reduce)');
  let reducedMotion = motionQuery?.matches === true;

  const $ = (selector) => document.querySelector(selector);
  const byId = (id) => document.getElementById(id);

  function unwrap(result) {
    if (!result?.ok) throw new Error(result?.error || 'Control Center request failed');
    return result.data;
  }

  function activePage() {
    return $('.page.active')?.dataset.pageView || 'overview';
  }

  function shouldPoll() {
    return document.visibilityState !== 'hidden' && ['overview', 'task'].includes(activePage());
  }

  function clientFor(data, type, id) {
    const clients = Array.isArray(data?.clients) ? data.clients : [];
    return clients.find((client) => client?.client_id === id)
      || clients.find((client) => client?.client_type === type)
      || null;
  }

  function delegationLane(delegation) {
    const text = `${delegation?.route_resolved || ''} ${delegation?.model || ''}`.toLowerCase();
    if (text.includes('deepseek')) return 'deepseek';
    if (text.includes('terra')) return 'terra';
    if (text.includes('sol')) return 'sol';
    if (text.includes('mini') || text.includes('luna')) return 'fast';
    return '';
  }

  function delegationState(status) {
    const value = String(status || '').toLowerCase();
    if (['active', 'running', 'starting', 'executing', 'in_progress', 'streaming', 'responding'].includes(value)) return 'active';
    if (['waiting', 'queued', 'pending', 'idle'].includes(value)) return 'waiting';
    if (['blocked', 'failed', 'replanned', 'interrupted'].includes(value)) return 'blocked';
    return 'offline';
  }

  function mergeState(current, next) {
    return STATE_RANK[next] > STATE_RANK[current] ? next : current;
  }

  function setText(id, value) {
    const element = byId(id);
    if (element) element.textContent = String(value ?? '—');
  }

  function shortId(value, length = 8) {
    const text = String(value || '');
    return text ? text.slice(0, length) : '—';
  }

  function formatDuration(ms) {
    const value = Number(ms || 0);
    if (!Number.isFinite(value) || value <= 0) return '0s';
    if (value < 1000) return `${Math.round(value)}ms`;
    if (value < 60000) return `${(value / 1000).toFixed(value < 10000 ? 1 : 0)}s`;
    return `${Math.floor(value / 60000)}m ${Math.round((value % 60000) / 1000)}s`;
  }

  function formatTime(value) {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '—';
    return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  function formatLimit(value) {
    return Number.isFinite(Number(value)) && Number(value) > 0 ? String(Number(value)) : 'unknown';
  }

  function finiteNumber(value) {
    if (value === null || value === undefined || value === '') return null;
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
  }

  function compactNumber(value) {
    const number = Number(value || 0);
    if (!Number.isFinite(number) || number < 0) return '0';
    if (number < 1000) return String(Math.round(number));
    if (number < 1000000) return `${(number / 1000).toFixed(number < 10000 ? 1 : 0)}K`;
    return `${(number / 1000000).toFixed(number < 10000000 ? 2 : 1)}M`;
  }

  function appendListRow(container, titleText, metaText, pillText = '', pillState = 'offline') {
    const row = document.createElement('div');
    row.className = 'cc-list-row';
    const main = document.createElement('div');
    const title = document.createElement('b');
    title.textContent = titleText;
    const meta = document.createElement('small');
    meta.textContent = metaText;
    main.append(title, meta);
    row.appendChild(main);
    if (pillText) {
      const state = document.createElement('span');
      state.className = `cc-pill is-${pillState}`;
      state.textContent = pillText;
      row.appendChild(state);
    }
    container.appendChild(row);
  }

  const ORCHESTRATION_ACTIVITY = {
    PREFLIGHT: { phase: 'thinking', label: 'Đang suy nghĩ', state: 'active', busy: true },
    ROUTED: { phase: 'dispatching', label: 'Đang điều phối', state: 'active', busy: true },
    EXECUTING: { phase: 'executing', label: 'Đang thực thi', state: 'active', busy: true },
    PROVING: { phase: 'proving', label: 'Đang kiểm chứng', state: 'active', busy: true },
    ACCEPTING: { phase: 'awaiting_acceptance', label: 'Đang chờ chấp nhận', state: 'waiting', busy: false },
    REPLAN: { phase: 'replanning', label: 'Đang lập lại kế hoạch', state: 'waiting', busy: true },
    CHECKPOINTED: { phase: 'completed', label: 'Đã hoàn tất', state: 'completed', busy: false },
    BLOCKED: { phase: 'blocked', label: 'Đang bị chặn', state: 'blocked', busy: false },
    ABORTED: { phase: 'stopped', label: 'Đã dừng', state: 'offline', busy: false }
  };

  function currentOrchestrationState(data) {
    return String(
      data?.resume_packet?.orchestration_state
      || data?.task?.orchestration?.orchestration_state
      || data?.orchestration_state
      || ''
    ).trim().toUpperCase();
  }

  function executionActivity(data) {
    const task = data?.task || {};
    const write = data?.authority?.write || {};
    const rawState = currentOrchestrationState(data);
    const command = task?.current_command || {};
    const delegations = Array.isArray(data?.delegations) ? data.delegations : [];
    const activeDelegation = delegations.find((item) => delegationState(item?.status) === 'active') || null;
    const delegationStatus = String(activeDelegation?.status || '').toLowerCase();
    const step = String(task.current_step || task.next_step || '').trim();

    if (rawState === 'PROVING') {
      return { ...ORCHESTRATION_ACTIVITY.PROVING, detail: step || 'Đang chạy proof/verification từ control plane.', rawState };
    }
    if (rawState === 'ACCEPTING') {
      return { ...ORCHESTRATION_ACTIVITY.ACCEPTING, detail: step || 'Proof đã xong; đang chờ bước chấp nhận cuối.', rawState };
    }
    if (rawState === 'REPLAN') {
      return { ...ORCHESTRATION_ACTIVITY.REPLAN, detail: task.failure || step || 'Control plane yêu cầu kế hoạch thực thi mới.', rawState };
    }
    if (rawState === 'EXECUTING' && write.status === 'active') {
      return { phase: 'writing', label: 'Đang ghi workspace', state: 'active', busy: true, detail: step || `Write fence #${write.fencing_token || 0} đang hoạt động.`, rawState };
    }
    if (rawState === 'EXECUTING' && ['streaming', 'responding'].includes(delegationStatus)) {
      return { phase: 'streaming', label: 'Đang nhận kết quả', state: 'active', busy: true, detail: step || `${activeDelegation?.model || activeDelegation?.route_resolved || 'Model'} đang streaming.`, rawState };
    }
    if (String(command.status || '').toLowerCase() === 'running') {
      return { phase: 'running', label: 'Đang chạy lệnh', state: 'active', busy: true, detail: String(command.command || step || 'Lệnh cục bộ đang chạy.').slice(0, 140), rawState };
    }
    if (ORCHESTRATION_ACTIVITY[rawState]) {
      return { ...ORCHESTRATION_ACTIVITY[rawState], detail: step || `Orchestration ${rawState.toLowerCase()}.`, rawState };
    }
    if (write.status === 'active') {
      return { phase: 'writing', label: 'Đang ghi workspace', state: 'active', busy: true, detail: step || `Write fence #${write.fencing_token || 0} đang hoạt động.`, rawState };
    }
    if (activeDelegation) {
      return { phase: 'running', label: 'Model đang làm việc', state: 'active', busy: true, detail: `${activeDelegation?.model || activeDelegation?.route_resolved || 'Model'} · ${activeDelegation?.status || 'active'}`, rawState };
    }
    if (String(task.status || '').toLowerCase() === 'active') {
      return { phase: 'working', label: 'Đang xử lý', state: 'active', busy: true, detail: step || 'Task đang hoạt động.', rawState };
    }
    if (String(task.status || '').toLowerCase() === 'waiting' && task.objective) {
      return { phase: 'waiting', label: 'Đang chờ bước tiếp theo', state: 'waiting', busy: false, detail: step || 'Task đang chờ.', rawState };
    }
    return { phase: 'idle', label: 'Đang rảnh', state: 'offline', busy: false, detail: 'Không có bằng chứng thực thi đang hoạt động.', rawState };
  }

  function topology(data) {
    const chatweb = clientFor(data, 'chatweb', 'chatweb');
    const desktop = clientFor(data, 'codex_desktop', 'codex-desktop');
    const opencode = clientFor(data, 'opencode', 'opencode');
    const controllerOwner = String(data?.authority?.controller?.owner_client_id || '');
    const write = data?.authority?.write || {};
    const taskStatus = String(data?.task?.status || 'idle').toLowerCase();
    const activity = executionActivity(data);
    const routes = { fast: 'offline', deepseek: 'offline', terra: 'offline', sol: 'offline' };
    const details = {
      fast: 'Mini / Luna idle',
      deepseek: 'DeepSeek activity requires explicit delegation evidence',
      terra: 'Terra idle',
      sol: 'Sol idle'
    };

    for (const delegation of Array.isArray(data?.delegations) ? data.delegations : []) {
      const lane = delegationLane(delegation);
      if (!lane) continue;
      const next = delegationState(delegation?.status);
      routes[lane] = mergeState(routes[lane], next);
      if (next !== 'offline') {
        details[lane] = `${delegation?.model || delegation?.route_resolved || lane} · ${delegation?.status || next}`;
      }
    }

    const chatwebState = chatweb?.online ? (controllerOwner === 'chatweb' ? 'active' : 'connected') : 'offline';
    const desktopState = desktop?.online ? (controllerOwner === 'codex-desktop' ? 'active' : 'connected') : 'offline';
    // OpenCode heartbeat proves only frontend connectivity. It never proves a
    // specific DeepSeek model is running; that comes exclusively from delegations.
    const opencodeState = opencode?.online ? 'connected' : 'offline';
    const anyClientOnline = Boolean(chatweb?.online || desktop?.online || opencode?.online);
    const anyRouteActive = Object.values(routes).some((state) => state === 'active');
    const mcpRunning = Boolean(snapshot?.status?.runtimeRunning || snapshot?.status?.mcpRunning);
    const hubOnline = Boolean(mcpRunning || anyClientOnline);
    const hubState = hubOnline && (activity.busy || taskStatus === 'active' || anyRouteActive || write.status === 'active')
      ? 'active' : hubOnline ? 'connected' : 'offline';
    const writerState = write.status === 'active' ? 'active' : hubOnline ? 'connected' : 'offline';

    return {
      clients: { chatweb, desktop, opencode },
      controllerOwner,
      write,
      taskStatus,
      routes,
      details,
      activity,
      states: {
        chatweb: chatwebState,
        desktop: desktopState,
        opencode: opencodeState,
        fast: routes.fast,
        hub: hubState,
        deepseek: routes.deepseek,
        terra: routes.terra,
        writer: writerState,
        sol: routes.sol
      },
      hubOnline,
      anyRouteActive
    };
  }

  function setRouterNode(prefix, key, state, detail) {
    const element = byId(`${prefix}Router${NODE_SUFFIX[key]}`);
    if (!element) return;
    for (const name of ['offline', 'connected', 'waiting', 'blocked', 'active']) element.classList.remove(`is-${name}`);
    element.classList.add(`is-${state}`);
    element.dataset.state = state;
    element.title = detail || state;
    const label = element.querySelector('[data-router-state]');
    if (label) {
      const idle = COMPUTE_KEYS.includes(key) || key === 'writer';
      label.textContent = state === 'connected' ? 'online' : state === 'offline' && idle ? 'idle' : state;
    }
  }

  function clearEdgeParticles(group) {
    group?.querySelectorAll?.('.ops-router-particle').forEach((node) => node.remove());
  }

  function clearRouterParticles() {
    document.querySelectorAll('.ops-router-particle').forEach((node) => node.remove());
  }

  function syncEdgeParticles(group, edge, state, flow) {
    if (!group || !edge) return;
    clearEdgeParticles(group);
    const page = group.closest('.page');
    const pageVisible = !page || page.classList.contains('active');
    if (state !== 'active' || flow === 'none' || reducedMotion || document.visibilityState === 'hidden' || !pageVisible) return;
    for (let index = 0; index < 2; index += 1) {
      const particle = document.createElementNS(SVG_NS, 'circle');
      particle.setAttribute('class', 'ops-router-particle');
      particle.setAttribute('r', index === 0 ? '2.6' : '1.8');
      const motion = document.createElementNS(SVG_NS, 'animateMotion');
      motion.setAttribute('dur', `${0.95 + index * 0.23}s`);
      motion.setAttribute('begin', `${index * 0.34}s`);
      motion.setAttribute('repeatCount', 'indefinite');
      motion.setAttribute('calcMode', 'linear');
      motion.setAttribute('keyTimes', '0;1');
      motion.setAttribute('keyPoints', flow === 'reverse' ? '1;0' : '0;1');
      const mpath = document.createElementNS(SVG_NS, 'mpath');
      mpath.setAttribute('href', `#${edge.id}`);
      motion.appendChild(mpath);
      particle.appendChild(motion);
      group.appendChild(particle);
    }
  }

  function routerEdgeFlow(view, data, key) {
    if (COMPUTE_KEYS.includes(key)) {
      const delegation = (Array.isArray(data?.delegations) ? data.delegations : [])
        .find((item) => delegationLane(item) === key && delegationState(item?.status) === 'active');
      if (!delegation) return 'none';
      const status = String(delegation?.status || '').toLowerCase();
      return ['streaming', 'responding'].includes(status) ? 'reverse' : 'forward';
    }
    if (key === 'writer') {
      if (view.activity.rawState === 'PROVING') return 'reverse';
      if (view.write.status === 'active') return 'forward';
    }
    // Frontend connectivity/controller ownership does not prove a provider call.
    return 'none';
  }

  function routerEdgeState(view, key) {
    if (key === 'writer' && view.activity.rawState === 'PROVING') return 'active';
    return view.states[key];
  }

  function setRouterEdge(prefix, key, state, flow = 'none') {
    const element = byId(`${prefix}Edge${NODE_SUFFIX[key]}`);
    if (!element) return;
    for (const name of ['offline', 'connected', 'waiting', 'blocked', 'active']) element.classList.remove(`is-${name}`);
    element.classList.add(`is-${state}`);
    const group = element.closest('.ops-router-edge-group');
    if (group) {
      for (const name of ['offline', 'connected', 'waiting', 'blocked', 'active']) group.classList.remove(`is-${name}`);
      group.classList.add(`is-${state}`);
      group.dataset.flow = flow;
      syncEdgeParticles(group, element, state, flow);
    }
  }

  function renderRouter(prefix, data) {
    const view = topology(data);
    const details = {
      chatweb: view.clients.chatweb?.online
        ? `ChatWeb · ${view.controllerOwner === 'chatweb' ? 'semantic controller' : 'observer'}` : 'ChatWeb offline',
      desktop: view.clients.desktop?.online
        ? `Codex Desktop · ${view.controllerOwner === 'codex-desktop' ? 'semantic controller' : 'worker'}` : 'Codex Desktop offline',
      opencode: view.clients.opencode?.online ? 'OpenCode frontend connected to Execution Hub' : 'OpenCode offline',
      fast: view.details.fast,
      hub: `Execution Hub · ${view.hubOnline ? 'online' : 'offline'} · task ${view.taskStatus}${view.activity.busy ? ` · ${view.activity.label}` : ''}`,
      deepseek: view.details.deepseek,
      terra: view.details.terra,
      writer: view.write.status === 'active'
        ? `MCP write lease active · fence #${view.write.fencing_token || 0}` : 'MCP writer/proof idle',
      sol: view.details.sol
    };
    for (const key of ROUTER_KEYS) setRouterNode(prefix, key, view.states[key], details[key]);
    for (const key of ['chatweb', 'desktop', 'opencode', 'fast', 'deepseek', 'terra', 'writer', 'sol']) {
      setRouterEdge(prefix, key, routerEdgeState(view, key), routerEdgeFlow(view, data, key));
    }
    const onlineClients = Object.values(view.clients).filter((client) => client?.online).length;
    const activeRoutes = Object.values(view.routes).filter((state) => state === 'active').length;
    const fabric = byId(`${prefix}RouterFabric`);
    if (fabric) {
      fabric.dataset.phase = view.activity.phase;
      fabric.classList.toggle('is-processing', view.activity.busy);
      fabric.classList.toggle('motion-reduced', reducedMotion);
    }
    const activitySuffix = view.activity.busy ? ` · ${view.activity.label}` : '';
    setText(`${prefix}RouterSummary`, `${onlineClients}/3 clients · ${activeRoutes} active route${activeRoutes === 1 ? '' : 's'}${activitySuffix}`);
    return view;
  }

  function setPill(id, text, state) {
    const element = byId(id);
    if (!element) return;
    element.textContent = text;
    element.className = `cc-pill is-${state}`;
  }

  function renderActivity(data) {
    const activity = executionActivity(data);
    const element = byId('ccActivityIndicator');
    if (element) {
      element.className = `cc-activity is-${activity.state}${activity.busy ? ' is-busy' : ''}${reducedMotion ? ' motion-reduced' : ''}`;
      element.dataset.phase = activity.phase;
      element.setAttribute('aria-busy', activity.busy ? 'true' : 'false');
    }
    setText('ccActivityLabel', activity.label);
    setText('ccActivityDetail', activity.detail);
    setText('ccMotionMode', reducedMotion ? 'Giảm chuyển động' : activity.busy ? 'Live' : 'Sẵn sàng');
    return activity;
  }

  function renderCommandCenter(data) {
    const view = renderRouter('cc', data);
    renderActivity(data);
    const ready = Boolean(snapshot?.status?.fullyReady);
    const runtimeRunning = Boolean(snapshot?.status?.runtimeRunning);
    const tunnelRunning = Boolean(snapshot?.status?.tunnelRunning);
    const clientsOnline = Object.values(view.clients).filter((client) => client?.online).length;
    const delegations = Array.isArray(data?.delegations) ? data.delegations : [];
    const activeDelegations = delegations.filter((item) => delegationState(item?.status) === 'active');
    const proofs = Array.isArray(data?.proofs) ? data.proofs : [];
    const passedProofs = proofs.filter((proof) => ['passed', 'accepted', 'completed'].includes(String(proof?.status || '').toLowerCase()));
    const latestProof = proofs[proofs.length - 1] || null;
    const task = data?.task || {};
    const run = data?.run || {};
    const waves = Array.isArray(data?.waves) ? data.waves : [];
    const wave = waves[waves.length - 1] || null;

    setPill('ccHealthBadge', ready ? 'Operational' : runtimeRunning ? 'Degraded' : 'Offline', ready ? 'active' : runtimeRunning ? 'waiting' : 'offline');
    setText('ccHeadline', ready ? 'Execution Hub is operational' : runtimeRunning ? 'Runtime is online; connectivity is incomplete' : 'Execution Hub is not running');
    setText('ccSubline', ready
      ? 'Một control plane duy nhất đang giữ task, authority, routing và proof. Chỉ các đường có evidence thật mới được animation.'
      : 'Control Center vẫn hiển thị durable task state và client evidence hiện có; không suy đoán provider/model activity.');

    setText('ccKpiRuntime', runtimeRunning ? 'Online' : 'Stopped');
    setText('ccKpiRuntimeMeta', `MCP ${runtimeRunning ? 'ON' : 'OFF'} · Tunnel ${tunnelRunning ? 'ON' : 'OFF'}`);
    setText('ccKpiClients', `${clientsOnline}/3`);
    setText('ccKpiClientsMeta', ['ChatWeb', 'Codex', 'OpenCode'].filter((_, index) => [view.clients.chatweb, view.clients.desktop, view.clients.opencode][index]?.online).join(' · ') || 'No frontend online');
    setText('ccKpiRoute', activeDelegations.length ? (activeDelegations[0]?.model || activeDelegations[0]?.route_resolved || 'Active') : 'Idle');
    setText('ccKpiRouteMeta', activeDelegations.length ? `${activeDelegations.length} active delegation${activeDelegations.length === 1 ? '' : 's'}` : 'No model lane currently active');
    setText('ccKpiProof', `${passedProofs.length}/${proofs.length}`);
    setText('ccKpiProofMeta', proofs.length ? `Latest ${latestProof?.stage_id || 'proof'} · ${latestProof?.status || 'unknown'}` : 'No proof recorded for current run');

    setPill('ccTaskStatus', String(task.status || 'idle'), String(task.status || 'offline').toLowerCase());
    setText('ccTaskObjective', task.objective || 'Không có task đang chạy.');
    setText('ccTaskStep', task.current_step || task.next_step || 'Waiting for work');
    setText('ccRunMeta', run.run_id
      ? `Run ${shortId(run.run_id)}${wave ? ` · wave ${wave.ordinal || '—'} · ${wave.status || wave.execution_mode || '—'}` : ''}`
      : 'No active orchestration run');

    const controller = data?.authority?.controller || {};
    const write = data?.authority?.write || {};
    setText('ccController', controller.owner_client_id
      ? `${controller.owner_client_id} · ${controller.status || 'claimed'} · fence #${controller.fencing_token || 0}`
      : 'Unclaimed');
    setText('ccWriter', write.status === 'active'
      ? `${write.owner || 'Coding Tools MCP'} · ACTIVE · fence #${write.fencing_token || 0}`
      : 'Coding Tools MCP · idle');
    const continuity = data?.continuity || {};
    setPill('ccContinuity', continuity.safe_to_rotate_chatweb ? 'Continuity ready' : 'Continuity hold', continuity.safe_to_rotate_chatweb ? 'active' : 'waiting');

    setText('ccProofCount', `${proofs.length} proof record${proofs.length === 1 ? '' : 's'}`);
    setText('ccProofLatest', latestProof ? `${latestProof.stage_id || 'proof'} · ${latestProof.status || 'unknown'} · ${latestProof.duration_ms ?? '—'}ms` : 'No proof yet');
    setText('ccDelegationCount', `${delegations.length} delegation record${delegations.length === 1 ? '' : 's'}`);
    setText('ccPerformance', performance?.tool_calls
      ? `${performance.tool_calls} tool calls · local ${formatDuration(performance.local_execution_ms)} · wait ${formatDuration(performance.estimated_wait_ms)}`
      : 'Performance telemetry not recorded yet');
    renderProviderTraffic(data);
    renderRecovery(data);
  }

  function renderProviderTraffic(data) {
    const traffic = data?.provider_traffic || {};
    const policy = traffic?.policy || {};
    const config = policy?.configuration || {};
    const providers = Array.isArray(policy?.providers) ? policy.providers : [];
    const capacity = traffic?.capacity || {};
    const opencodeCapacity = capacity?.opencode || {};
    const codexCooldowns = Array.isArray(capacity?.codex?.capacity_cooldowns) ? capacity.codex.capacity_cooldowns : [];
    const automatic = traffic?.automatic_routing || {};
    const enforced = providers.filter((item) => item?.mode === 'enforced').length;
    const invalid = providers.filter((item) => item?.mode === 'invalid').length;
    const policyLabel = invalid ? 'Invalid · fail closed' : enforced ? ` configured` : 'Limits unknown · Provider quota is not configured; observe-only, no limit is invented';
    setText('ccTrafficPolicy', policyLabel);
    setText('ccTrafficMeta', `${Number(opencodeCapacity?.active_requests || 0)} OpenCode active · auto-route ${automatic?.enabled ? 'ON' : 'OFF'} · ${config?.status || 'unconfigured'}`);

    }

  function renderRecovery(data) {
    const health = snapshot?.status || {};
    const pressure = data?.continuity?.context_pressure || {};
    const failures = Number(health.failures || 0);
    const attempts = Number(health.recoveryAttempts || 0);
    const deferred = Number(health.deferredRecoveryCount || 0);
    const recoveryState = health.recovering ? 'Recovering' : health.recoveryBlocked ? 'Blocked' : failures ? 'Degraded' : 'Stable';
    const detailParts = [];
    if (health.failureKind) detailParts.push(health.failureKind);
    if (failures) detailParts.push(`${failures} consecutive fail${failures === 1 ? '' : 's'}`);
    if (attempts) detailParts.push(`${attempts} recovery attempt${attempts === 1 ? '' : 's'}`);
    if (deferred) detailParts.push(`${deferred} deferred`);
    if (health.lastStartFailure) detailParts.push(`start: ${String(health.lastStartFailure).slice(0, 120)}`);
    const recoveryMeta = detailParts.join(' · ') || 'No local recovery evidence.';
    setText('ccRecoveryState', recoveryState);
    setText('ccRecoveryMeta', recoveryMeta);
    const pressureUnknown = String(pressure?.status || 'unknown').toLowerCase() === 'unknown';
    const pressureSource = String(pressure?.source || 'host_not_exposed');
    setText('ccContextPressure', pressureUnknown ? 'Unknown' : String(pressure.status));
    setText('ccContextMeta', pressureUnknown && pressureSource === 'host_not_exposed'
      ? 'Host does not expose conversation context pressure; UI does not estimate a percentage.'
      : `Source ${pressureSource}`);
  }

  function renderAll() {
    const data = orchestration || {};
    renderCommandCenter(data);
  }

  async function refreshPerformance(force = false) {
    if (!force && Date.now() - lastPerformanceRead < 10000) return;
    lastPerformanceRead = Date.now();
    try { performance = unwrap(await api.performanceTrace()); }
    catch { performance = null; }
  }

  async function refresh(force = false) {
    if (refreshInFlight || (!force && !shouldPoll())) return;
    refreshInFlight = true;
    try {
      const snapshotRequest = force ? api.snapshot() : api.lightweightSnapshot();
      const orchestrationRequest = force ? api.orchestration() : api.liveOrchestration();
      const [snapshotResult, orchestrationResult] = await Promise.allSettled([snapshotRequest, orchestrationRequest]);
      if (snapshotResult.status === 'fulfilled') {
        try {
          const payload = unwrap(snapshotResult.value);
          snapshot = force ? payload : { ...(snapshot || {}), status: payload };
        } catch { snapshot = null; }
      }
      if (orchestrationResult.status === 'fulfilled') {
        try { orchestration = unwrap(orchestrationResult.value); } catch { orchestration = null; }
      }
      await refreshPerformance(force);
      renderAll();
      setText('ccLastSync', `Last sync ${new Date().toLocaleTimeString('vi-VN')}`);
    } finally {
      refreshInFlight = false;
    }
  }

  function controlCenterPollDelay() {
    if (!shouldPoll()) return CONTROL_CENTER_HIDDEN_POLL_MS;
    return executionActivity(orchestration || {}).busy ? CONTROL_CENTER_BUSY_POLL_MS : CONTROL_CENTER_IDLE_POLL_MS;
  }

  async function pollControlCenter() {
    await refresh(false);
    setTimeout(pollControlCenter, controlCenterPollDelay());
  }

  async function restartRuntime() {
    const button = byId('ccRestartButton');
    if (button) button.disabled = true;
    try {
      snapshot = unwrap(await api.restart());
      await refresh(true);
    } catch (error) {
      setText('ccSubline', `Restart failed: ${error.message}`);
    } finally {
      if (button) button.disabled = false;
    }
  }

  byId('ccRestartButton')?.addEventListener('click', restartRuntime);
  byId('ccRefreshButton')?.addEventListener('click', () => refresh(true));

  document.addEventListener('click', (event) => {
    const target = event.target.closest('[data-page],[data-nav]');
    if (!target) return;
    clearRouterParticles();
    setTimeout(() => refresh(true), 0);
  });
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      clearRouterParticles();
      return;
    }
    if (shouldPoll()) refresh(true);
  });
  motionQuery?.addEventListener?.('change', (event) => {
    reducedMotion = Boolean(event.matches);
    renderAll();
  });

  api.onHeartbeat?.((health) => {
    if (!snapshot) snapshot = { status: {} };
    snapshot.status ||= {};
    snapshot.status.runtimeRunning = Boolean(health?.mcpRunning);
    snapshot.status.tunnelRunning = Boolean(health?.tunnelRunning);
    snapshot.status.fullyReady = Boolean(health?.fullyReady);
    snapshot.status.recovering = Boolean(health?.recovering);
    snapshot.status.failures = Number(health?.failures || 0);
    snapshot.status.failureKind = String(health?.failureKind || '');
    snapshot.status.recoveryAttempts = Number(health?.recoveryAttempts || 0);
    snapshot.status.nextRecoveryAt = Number(health?.nextRecoveryAt || 0);
    snapshot.status.recoveryBlocked = Boolean(health?.recoveryBlocked);
    snapshot.status.lastStartFailure = String(health?.lastStartFailure || '');
    snapshot.status.deferredRecoveryCount = Number(health?.deferredRecoveryCount || 0);
    if (shouldPoll() && !refreshInFlight) renderAll();
  });

  refresh(true).finally(() => setTimeout(pollControlCenter, controlCenterPollDelay()));
})();
