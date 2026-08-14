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

  let snapshot = null;
  let orchestration = null;
  let performance = null;
  let refreshInFlight = false;
  let lastPerformanceRead = 0;

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
    return document.visibilityState !== 'hidden' && ['overview', 'routing', 'task'].includes(activePage());
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
    if (['active', 'running', 'starting', 'executing', 'in_progress'].includes(value)) return 'active';
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

  function topology(data) {
    const chatweb = clientFor(data, 'chatweb', 'chatweb');
    const desktop = clientFor(data, 'codex_desktop', 'codex-desktop');
    const opencode = clientFor(data, 'opencode', 'opencode');
    const controllerOwner = String(data?.authority?.controller?.owner_client_id || '');
    const write = data?.authority?.write || {};
    const taskStatus = String(data?.task?.status || 'idle').toLowerCase();
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
    const hubState = hubOnline && (taskStatus === 'active' || anyRouteActive || write.status === 'active')
      ? 'active' : hubOnline ? 'connected' : 'offline';
    const writerState = write.status === 'active' ? 'active' : hubOnline ? 'connected' : 'offline';

    return {
      clients: { chatweb, desktop, opencode },
      controllerOwner,
      write,
      taskStatus,
      routes,
      details,
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

  function setRouterEdge(prefix, key, state) {
    const element = byId(`${prefix}Edge${NODE_SUFFIX[key]}`);
    if (!element) return;
    for (const name of ['offline', 'connected', 'waiting', 'blocked', 'active']) element.classList.remove(`is-${name}`);
    element.classList.add(`is-${state}`);
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
      hub: `Execution Hub · ${view.hubOnline ? 'online' : 'offline'} · task ${view.taskStatus}`,
      deepseek: view.details.deepseek,
      terra: view.details.terra,
      writer: view.write.status === 'active'
        ? `MCP write lease active · fence #${view.write.fencing_token || 0}` : 'MCP writer/proof idle',
      sol: view.details.sol
    };
    for (const key of ROUTER_KEYS) setRouterNode(prefix, key, view.states[key], details[key]);
    for (const key of ['chatweb', 'desktop', 'opencode', 'fast', 'deepseek', 'terra', 'writer', 'sol']) {
      setRouterEdge(prefix, key, view.states[key]);
    }
    const onlineClients = Object.values(view.clients).filter((client) => client?.online).length;
    const activeRoutes = Object.values(view.routes).filter((state) => state === 'active').length;
    setText(`${prefix}RouterSummary`, `${onlineClients}/3 clients · ${activeRoutes} active route${activeRoutes === 1 ? '' : 's'}`);
    return view;
  }

  function setPill(id, text, state) {
    const element = byId(id);
    if (!element) return;
    element.textContent = text;
    element.className = `cc-pill is-${state}`;
  }

  function renderCommandCenter(data) {
    const view = renderRouter('cc', data);
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
  }

  function renderClientCard(prefix, client, latestEventSeq) {
    const online = Boolean(client?.online);
    setPill(`${prefix}State`, online ? 'online' : 'offline', online ? 'active' : 'offline');
    const seq = Number(client?.cursor?.last_event_seq || 0);
    const lag = Math.max(0, Number(latestEventSeq || 0) - seq);
    setText(`${prefix}Meta`, client ? `cursor #${seq}${lag ? ` · lag ${lag}` : ''}` : 'No client record');
  }

  function renderDelegationList(items) {
    const container = byId('routingDelegations');
    if (!container) return;
    container.replaceChildren();
    const list = Array.isArray(items) ? items : [];
    if (!list.length) {
      const empty = document.createElement('div');
      empty.className = 'cc-empty';
      empty.textContent = 'No delegation is active or retained for this run.';
      container.appendChild(empty);
      return;
    }
    for (const item of list.slice().reverse().slice(0, 8)) {
      const row = document.createElement('div');
      row.className = 'cc-list-row';
      const main = document.createElement('div');
      const title = document.createElement('b');
      title.textContent = item.model || item.route_resolved || 'deterministic';
      const meta = document.createElement('small');
      meta.textContent = `${item.route_resolved || 'route —'} · ${item.effort || '—'} · ${item.status || 'unknown'}`;
      main.append(title, meta);
      const state = document.createElement('span');
      state.className = `cc-pill is-${delegationState(item.status)}`;
      state.textContent = item.status || 'unknown';
      row.append(main, state);
      container.appendChild(row);
    }
  }

  function renderEvidenceList(containerId, items, kind) {
    const container = byId(containerId);
    if (!container) return;
    container.replaceChildren();
    const list = Array.isArray(items) ? items : [];
    if (!list.length) {
      const empty = document.createElement('div');
      empty.className = 'cc-empty';
      empty.textContent = kind === 'proof' ? 'No proof records.' : 'No recent orchestration events.';
      container.appendChild(empty);
      return;
    }
    for (const item of list.slice().reverse().slice(0, 6)) {
      const row = document.createElement('div');
      row.className = 'cc-evidence-row';
      const time = document.createElement('time');
      time.textContent = formatTime(kind === 'proof' ? item.created_at : item.event_time);
      const copy = document.createElement('div');
      const title = document.createElement('b');
      title.textContent = kind === 'proof' ? (item.stage_id || 'proof') : (item.event_type || 'event');
      const meta = document.createElement('small');
      if (kind === 'proof') meta.textContent = `${item.status || 'unknown'} · ${item.duration_ms ?? '—'}ms`;
      else meta.textContent = `${item.state_before || '·'} → ${item.state_after || '·'}`;
      copy.append(title, meta);
      row.append(time, copy);
      container.appendChild(row);
    }
  }

  function renderRouting(data) {
    const view = renderRouter('routing', data);
    const latestEventSeq = Number(data?.resume_packet?.latest_event_seq || 0);
    renderClientCard('routingChatWeb', view.clients.chatweb, latestEventSeq);
    renderClientCard('routingDesktop', view.clients.desktop, latestEventSeq);
    renderClientCard('routingOpenCode', view.clients.opencode, latestEventSeq);
    const controller = data?.authority?.controller || {};
    const write = data?.authority?.write || {};
    setText('routingAuthorityController', controller.owner_client_id
      ? `${controller.owner_client_id} · ${controller.status || 'claimed'} · fence #${controller.fencing_token || 0}` : 'Unclaimed');
    setText('routingAuthorityWriter', write.status === 'active'
      ? `${write.owner || 'Coding Tools MCP'} · ACTIVE · fence #${write.fencing_token || 0}` : 'Coding Tools MCP · idle');
    const continuity = data?.continuity || {};
    setPill('routingContinuity', continuity.safe_to_rotate_chatweb ? 'Ready' : 'Hold', continuity.safe_to_rotate_chatweb ? 'active' : 'waiting');
    setText('routingContinuityMeta', Array.isArray(continuity.reason_codes) && continuity.reason_codes.length
      ? continuity.reason_codes.join(' · ') : 'No continuity assessment available');
    renderDelegationList(data?.delegations);
    renderEvidenceList('routingEvents', data?.events, 'event');
    renderEvidenceList('routingProofs', data?.proofs, 'proof');
  }

  function renderAll() {
    const data = orchestration || {};
    renderCommandCenter(data);
    renderRouting(data);
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
      const [snapshotResult, orchestrationResult] = await Promise.allSettled([api.snapshot(), api.orchestration()]);
      if (snapshotResult.status === 'fulfilled') {
        try { snapshot = unwrap(snapshotResult.value); } catch { snapshot = null; }
      }
      if (orchestrationResult.status === 'fulfilled') {
        try { orchestration = unwrap(orchestrationResult.value); } catch { orchestration = null; }
      }
      await refreshPerformance(force);
      renderAll();
      setText('ccLastSync', `Last sync ${new Date().toLocaleTimeString('vi-VN')}`);
      setText('routingLastSync', `Last sync ${new Date().toLocaleTimeString('vi-VN')}`);
    } finally {
      refreshInFlight = false;
    }
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
  byId('routingRefreshButton')?.addEventListener('click', () => refresh(true));

  document.addEventListener('click', (event) => {
    const target = event.target.closest('[data-page],[data-nav]');
    if (!target) return;
    setTimeout(() => refresh(true), 0);
  });
  document.addEventListener('visibilitychange', () => { if (shouldPoll()) refresh(true); });

  api.onHeartbeat?.((health) => {
    if (!snapshot) snapshot = { status: {} };
    snapshot.status ||= {};
    snapshot.status.runtimeRunning = Boolean(health?.mcpRunning);
    snapshot.status.tunnelRunning = Boolean(health?.tunnelRunning);
    snapshot.status.fullyReady = Boolean(health?.fullyReady);
    renderAll();
  });

  refresh(true);
  setInterval(() => refresh(false), 2500);
})();
