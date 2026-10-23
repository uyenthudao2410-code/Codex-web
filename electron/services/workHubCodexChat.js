'use strict';
/*
 * Work Hub native Codex chat (W3, direction change 2026-10-23 19:03).
 *
 * This is NOT the CoS companion: no Chat On Steroids app is installed or
 * contacted. The chat lives natively in Codex-web and talks to the local
 * Codex App Server through the runtime's existing internal `codex_bridge`
 * tool — the same panel channel (callMcpTool in electron/main.js) that
 * job-run / handoff-get already use. The public smart-v3 MCP surface is
 * unchanged; no new MCP tool is added.
 *
 * Bridge contract (verified from resources/coding-tools-mcp/coding_tools_mcp/
 * codex_bridge.py, see docs/research/261023_COS_W3_NATIVE_CHAT.md):
 *   action=status    -> sidecar status (SPAWNS the sidecar; fails with
 *                       CODEX_NOT_FOUND when no codex binary exists)
 *   action=threads   -> persisted Desktop history for this workspace only
 *                       (summaries; the bridge cannot read their turns and
 *                       will not continue them — inspect/fork only)
 *   action=run       -> thread/start + turn/start in one call; the thread is
 *                       created together with its first prompt (there is no
 *                       empty-thread create) and becomes bridge-owned
 *   action=continue  -> one more turn, ONLY on a bridge-owned thread of the
 *                       current sidecar process (THREAD_NOT_OWNED after a
 *                       sidecar/MCP restart)
 *   action=observe   -> cursor polling: agent_text snapshot + meaningful
 *                       events; this is the only "streaming" the bridge has
 *   action=interrupt -> stops a bridge-owned turn
 *
 * Bridge-wide invariants the UI must state honestly: every turn runs with
 * approvalPolicy=never, a read-only sandbox and no network, whatever the
 * profile. The chat (profile "chat", added in W3) can discuss the workspace
 * and inspect it read-only; it can never apply changes — edits keep going
 * through the EOCL Job/approval flow.
 *
 * Session state is held here, in the main process, per workspace root. The
 * timeline is exactly what the panel sent plus the bridge's agent_text —
 * nothing is inferred from chat content, and a thread is linked to a RUN
 * only when the caller supplies a real run_id/task_id captured from the
 * current task state at creation time.
 *
 * Every public method resolves with a result object and never throws:
 *   { ok: true,  state, data }
 *   { ok: false, state, error: { code, message } }
 * mirroring the CoS companion adapter so a dead provider can never take
 * the main process down.
 */
const MAX_PROMPT_CHARS = 20_000; // mirrors the bridge prompt bound
const MAX_TEXT_CHARS = 65_536; // mirrors the bridge agent-text bound
const MAX_EVENTS_KEPT = 100;

const CHAT_STATES = Object.freeze({
  UNKNOWN: 'UNKNOWN', // never probed
  READY: 'READY', // bridge status OK, no turn running
  RUNNING: 'RUNNING', // a turn is in progress on the current thread
  COMPLETED: 'COMPLETED', // last turn completed
  FAILED: 'FAILED', // last turn failed at the provider/bridge
  INTERRUPTED: 'INTERRUPTED', // last turn interrupted
  PROVIDER_UNAVAILABLE: 'PROVIDER_UNAVAILABLE', // no codex binary / provider
  MCP_UNAVAILABLE: 'MCP_UNAVAILABLE', // the local MCP runtime is not up
  OWNERSHIP_LOST: 'OWNERSHIP_LOST', // sidecar restarted; thread not owned
});

function boundedText(value, limit = MAX_TEXT_CHARS) {
  const text = String(value ?? '');
  return text.length <= limit ? text : `${text.slice(0, limit)}…`;
}

function cleanId(value) {
  const text = String(value ?? '').trim();
  return text ? text.slice(0, 200) : '';
}

// callMcpTool throws Error(message) — the bridge error code survives only in
// the message text (ToolFailure message), so classification happens here,
// in exactly one place.
function classifyBridgeError(err) {
  const message = boundedText(err && err.message ? err.message : String(err || 'Không rõ lỗi.'), 400);
  if (/CODEX_NOT_FOUND|Codex CLI was not found/i.test(message)) {
    return { code: 'CODEX_NOT_FOUND', state: CHAT_STATES.PROVIDER_UNAVAILABLE, message };
  }
  if (/CODEX_START_FAILED|Failed to start Codex App Server/i.test(message)) {
    return { code: 'CODEX_START_FAILED', state: CHAT_STATES.PROVIDER_UNAVAILABLE, message };
  }
  if (/THREAD_NOT_OWNED/i.test(message)) {
    return { code: 'THREAD_NOT_OWNED', state: CHAT_STATES.OWNERSHIP_LOST, message };
  }
  if (/TURN_ALREADY_ACTIVE|already has an active turn/i.test(message)) {
    return { code: 'TURN_ALREADY_ACTIVE', state: CHAT_STATES.RUNNING, message };
  }
  if (/MCP chưa sẵn sàng|ECONNREFUSED|fetch failed|socket hang up/i.test(message)) {
    return { code: 'MCP_UNAVAILABLE', state: CHAT_STATES.MCP_UNAVAILABLE, message };
  }
  return { code: 'BRIDGE_ERROR', state: CHAT_STATES.FAILED, message };
}

function createWorkHubCodexChat(options = {}) {
  const callBridge = typeof options.callBridge === 'function'
    ? options.callBridge
    : null;
  const sessions = new Map(); // workspace root -> session

  function newSession(root) {
    return {
      workspace: String(root || ''),
      state: CHAT_STATES.UNKNOWN,
      availability: null, // last bridge status projection (binary/version)
      threadId: '',
      sessionId: '',
      turnId: '',
      cursor: 0,
      route: null,
      link: null, // { runId, taskId } — real ids only, set at creation
      messages: [], // { role: 'user'|'assistant', text, turnId, status }
      events: [], // { cursor, method, itemType, status }
      error: null,
      updatedAt: null,
    };
  }

  function sessionFor(root) {
    const key = String(root || '');
    if (!sessions.has(key)) sessions.set(key, newSession(key));
    return sessions.get(key);
  }

  function view(session) {
    return {
      state: session.state,
      workspace: session.workspace,
      availability: session.availability,
      threadId: session.threadId || null,
      sessionId: session.sessionId || null,
      turnId: session.turnId || null,
      route: session.route,
      link: session.link,
      messages: session.messages.map((m) => ({ ...m })),
      events: session.events.slice(-20).map((e) => ({ ...e })),
      error: session.error,
      updatedAt: session.updatedAt,
      invariants: { approvalPolicy: 'never', sandbox: 'read-only', networkAccess: false },
    };
  }

  function fail(session, classified) {
    session.state = classified.state;
    session.error = { code: classified.code, message: classified.message };
    session.updatedAt = new Date().toISOString();
    return { ok: false, state: session.state, error: session.error, data: view(session) };
  }

  async function bridge(session, args, timeoutMs) {
    if (!callBridge) {
      throw Object.assign(new Error('Kênh gọi Codex bridge chưa được nối trong main process.'), { code: 'BRIDGE_NOT_WIRED' });
    }
    const result = await callBridge(args, timeoutMs);
    if (!result || typeof result !== 'object') {
      throw new Error('Codex bridge trả về dữ liệu không hợp lệ.');
    }
    return result;
  }

  async function probe(root) {
    const session = sessionFor(root);
    try {
      const status = await bridge(session, { action: 'status' }, 30_000);
      session.availability = {
        connected: Boolean(status.connected),
        binary: status.binary || null,
        codexVersion: status.codex_version || null,
        codexHome: status.codex_home || null,
        workspace: status.workspace || session.workspace,
      };
      if (session.state === CHAT_STATES.UNKNOWN || session.state === CHAT_STATES.PROVIDER_UNAVAILABLE || session.state === CHAT_STATES.MCP_UNAVAILABLE) {
        session.state = CHAT_STATES.READY;
      }
      session.error = null;
      session.updatedAt = new Date().toISOString();
      return { ok: true, state: session.state, data: view(session) };
    } catch (err) {
      return fail(session, classifyBridgeError(err));
    }
  }

  async function listHistory(root) {
    const session = sessionFor(root);
    try {
      const result = await bridge(session, { action: 'threads', limit: 10 }, 30_000);
      const threads = Array.isArray(result.threads) ? result.threads : [];
      return {
        ok: true,
        state: session.state,
        data: {
          scope: result.scope || 'current_workspace_only',
          note: result.note || '',
          threads: threads.map((t) => ({
            id: cleanId(t && t.id),
            name: boundedText(t && t.name, 200) || null,
            preview: boundedText(t && t.preview, 300) || null,
            status: t && t.status ? String(t.status) : null,
            updatedAt: (t && (t.updated_at || t.recency_at)) || null,
            continuable: false, // bridge: Desktop threads are inspect/fork only
          })).filter((t) => t.id),
        },
      };
    } catch (err) {
      const classified = classifyBridgeError(err);
      return { ok: false, state: session.state, error: { code: classified.code, message: classified.message }, data: null };
    }
  }

  function recordTurnStart(session, result, promptText) {
    const threadId = cleanId(result.thread_id);
    const turnId = cleanId(result.turn_id);
    if (!threadId || !turnId) {
      throw new Error('Codex bridge không trả thread_id/turn_id cho lượt chat mới.');
    }
    session.threadId = threadId;
    session.turnId = turnId;
    session.cursor = 0;
    if (result.session_id) session.sessionId = cleanId(result.session_id);
    const route = result.route && typeof result.route === 'object' ? result.route : {};
    session.route = {
      profile: String(route.profile || 'chat'),
      model: route.model ? String(route.model) : null,
      effort: route.effort ? String(route.effort) : null,
    };
    session.messages.push({ role: 'user', text: promptText, turnId, status: 'completed' });
    session.messages.push({ role: 'assistant', text: '', turnId, status: 'running' });
    session.state = CHAT_STATES.RUNNING;
    session.error = null;
    session.updatedAt = new Date().toISOString();
  }

  async function send(root, payload = {}) {
    const session = sessionFor(root);
    const text = String(payload.text ?? '').trim();
    if (!text) {
      return { ok: false, state: session.state, error: { code: 'CHAT_PROMPT_REQUIRED', message: 'Nội dung chat không được trống.' }, data: view(session) };
    }
    if (text.length > MAX_PROMPT_CHARS) {
      return { ok: false, state: session.state, error: { code: 'CHAT_PROMPT_TOO_LARGE', message: `Nội dung chat vượt giới hạn ${MAX_PROMPT_CHARS} ký tự của bridge.` }, data: view(session) };
    }
    if (session.state === CHAT_STATES.RUNNING) {
      return { ok: false, state: session.state, error: { code: 'TURN_ALREADY_ACTIVE', message: 'Lượt chat trước đang chạy; chờ hoàn tất hoặc dừng lượt trước khi gửi tiếp.' }, data: view(session) };
    }
    if (session.state === CHAT_STATES.PROVIDER_UNAVAILABLE || session.state === CHAT_STATES.MCP_UNAVAILABLE) {
      return { ok: false, state: session.state, error: session.error || { code: 'PROVIDER_UNAVAILABLE', message: 'Codex provider chưa sẵn sàng.' }, data: view(session) };
    }
    try {
      if (!session.threadId) {
        const result = await bridge(session, { action: 'run', prompt: text, profile: 'chat', lifetime: 'ephemeral' }, 30_000);
        // Link only from real ids supplied by the caller (captured from the
        // current task state in the renderer) — never inferred from content.
        const runId = cleanId(payload.link && payload.link.runId);
        const taskId = cleanId(payload.link && payload.link.taskId);
        session.link = runId ? { runId, taskId: taskId || null } : null;
        recordTurnStart(session, result, text);
      } else {
        const result = await bridge(session, { action: 'continue', thread_id: session.threadId, prompt: text }, 30_000);
        recordTurnStart(session, result, text);
      }
      return { ok: true, state: session.state, data: view(session) };
    } catch (err) {
      return fail(session, classifyBridgeError(err));
    }
  }

  async function poll(root) {
    const session = sessionFor(root);
    if (!session.threadId || !session.turnId || session.state !== CHAT_STATES.RUNNING) {
      return { ok: true, state: session.state, data: view(session) };
    }
    try {
      const result = await bridge(session, {
        action: 'observe',
        thread_id: session.threadId,
        turn_id: session.turnId,
        after_cursor: session.cursor,
        wait_ms: 2000,
        max_events: 50,
      }, 15_000);
      if (Number.isFinite(result.next_cursor)) session.cursor = Math.max(session.cursor, Number(result.next_cursor));
      const events = Array.isArray(result.events) ? result.events : [];
      for (const event of events) {
        session.events.push({
          cursor: Number(event && event.cursor) || session.cursor,
          method: boundedText(event && event.method, 120),
          itemType: event && event.item_type ? String(event.item_type) : null,
          status: event && event.status ? String(event.status) : null,
        });
      }
      if (session.events.length > MAX_EVENTS_KEPT) session.events = session.events.slice(-MAX_EVENTS_KEPT);
      const assistant = [...session.messages].reverse().find((m) => m.role === 'assistant' && m.turnId === session.turnId);
      if (assistant && typeof result.agent_text === 'string') assistant.text = boundedText(result.agent_text);
      const status = String(result.status || 'inProgress');
      if (result.terminal || ['completed', 'failed', 'interrupted'].includes(status)) {
        if (assistant) assistant.status = status === 'completed' ? 'completed' : status;
        session.state = status === 'completed'
          ? CHAT_STATES.COMPLETED
          : status === 'interrupted' ? CHAT_STATES.INTERRUPTED : CHAT_STATES.FAILED;
        if (status === 'failed' && result.error) {
          session.error = { code: 'TURN_FAILED', message: boundedText(typeof result.error === 'string' ? result.error : JSON.stringify(result.error), 400) };
        }
      }
      session.updatedAt = new Date().toISOString();
      return { ok: true, state: session.state, data: view(session) };
    } catch (err) {
      const classified = classifyBridgeError(err);
      // A failed poll must not erase the timeline; surface the error and let
      // the panel decide to keep polling or stop.
      session.error = { code: classified.code, message: classified.message };
      if (classified.state === CHAT_STATES.OWNERSHIP_LOST) session.state = CHAT_STATES.OWNERSHIP_LOST;
      session.updatedAt = new Date().toISOString();
      return { ok: false, state: session.state, error: session.error, data: view(session) };
    }
  }

  async function interrupt(root) {
    const session = sessionFor(root);
    if (!session.threadId || !session.turnId) {
      return { ok: false, state: session.state, error: { code: 'NO_ACTIVE_TURN', message: 'Không có lượt chat nào để dừng.' }, data: view(session) };
    }
    try {
      await bridge(session, { action: 'interrupt', thread_id: session.threadId, turn_id: session.turnId }, 15_000);
      const assistant = [...session.messages].reverse().find((m) => m.role === 'assistant' && m.turnId === session.turnId);
      if (assistant && assistant.status === 'running') assistant.status = 'interrupted';
      session.state = CHAT_STATES.INTERRUPTED;
      session.updatedAt = new Date().toISOString();
      return { ok: true, state: session.state, data: view(session) };
    } catch (err) {
      return fail(session, classifyBridgeError(err));
    }
  }

  function reset(root) {
    const key = String(root || '');
    const previous = sessions.get(key);
    const fresh = newSession(key);
    if (previous) fresh.availability = previous.availability;
    fresh.state = fresh.availability ? CHAT_STATES.READY : CHAT_STATES.UNKNOWN;
    sessions.set(key, fresh);
    return { ok: true, state: fresh.state, data: view(fresh) };
  }

  function getView(root) {
    const session = sessionFor(root);
    return { ok: true, state: session.state, data: view(session) };
  }

  return { probe, listHistory, send, poll, interrupt, reset, getView, CHAT_STATES };
}

module.exports = { createWorkHubCodexChat, CHAT_STATES, classifyBridgeError };
