'use strict';
/*
 * Work Hub native Codex chat (W3, direction change 2026-10-23 19:03;
 * W3-C additions 2026-10-24: handoff / fork / durable resume / route
 * selector — source + test level only, no live proof claimed).
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
 *   action=models    -> model/list of the App Server (W3-C route selector)
 *   action=threads   -> persisted Desktop history for this workspace only
 *                       (summaries; the bridge cannot read their turns and
 *                       will not continue them — inspect/fork only)
 *   action=run       -> thread/start + turn/start in one call; the thread is
 *                       created together with its first prompt (there is no
 *                       empty-thread create) and becomes bridge-owned.
 *                       With source_thread_id + profile "history" it forks a
 *                       persisted Desktop thread (W3-C fork): the new thread
 *                       is bridge-owned and continuable, but the panel still
 *                       cannot read the old turns — the fork inherits its
 *                       context inside the App Server, not through the panel.
 *   action=continue  -> one more turn, ONLY on a bridge-owned thread of the
 *                       current sidecar process (THREAD_NOT_OWNED after a
 *                       sidecar/MCP restart — see resume below)
 *   action=resume    -> re-own one persistent thread this service durably
 *                       registered at creation (thread_id + session_id must
 *                       match the persisted thread; W3-C). Implemented by
 *                       the bridge on top of the existing persistent-lane
 *                       restore machinery; it launches no turn and cannot
 *                       claim an arbitrary Desktop thread.
 *   action=observe   -> cursor polling: agent_text snapshot + meaningful
 *                       events; this is the only "streaming" the bridge has
 *   action=interrupt -> stops a bridge-owned turn
 *
 * Bridge-wide invariants the UI must state honestly: every turn runs with
 * approvalPolicy=never, a read-only sandbox and no network, whatever the
 * profile — and whatever model/effort override the W3-C selector passes
 * (run/continue accept model/effort; profile "chat" is not route-locked).
 * The chat can discuss the workspace and inspect it read-only; it can never
 * apply changes — edits keep going through the EOCL Job/approval flow.
 *
 * Durable resume (W3-C): chat threads are created with lifetime=persistent
 * and the service persists a small session registry (thread_id, session_id,
 * workspace root, profile, title/created-at, RUN link, fork origin,
 * handoff receipt) to the state file injected by main (beside the app
 * data, following the writeFileSync+rename pattern of the other Electron
 * services). On probe, a registry-restored session is resumed through
 * action=resume BEFORE it may be continued; OWNERSHIP_LOST is only
 * reported when that resume actually fails. Honest limits: resume depends
 * on the App Server still holding the thread in CODEX_HOME, and the panel
 * timeline is NOT persisted — after a restart only thread ownership and
 * the link come back, not the old messages.
 *
 * Handoff (W3-C): "Chuyển thành việc điều hành" reuses the existing Work
 * Hub task/handoff machinery only — task_control action=start creates the
 * operating task when the chat is not linked to a RUN yet, and the
 * capsule is recorded/read through task_control action=handoff
 * (record/get), the same surface panel:handoff / workhub:handoff-get use.
 * No second handoff mechanism is created. Before recording, the current
 * capsule of a linked RUN is read and its W4 send_replay_directive is
 * honored: RECONCILE_BEFORE_REPLAY / ALREADY_CONFIRMED block the transfer
 * (no new task, no new capsule, no blind replay) and the directive +
 * recommended_next_action are surfaced in the view. The controller lease
 * is read-only from the orchestration ledger (holder + expiry, via the
 * injected readLease = workHubCoordination.runDetail); the panel has no
 * lease write API, so the capsule payload itself records that fact
 * instead of inventing one.
 *
 * A thread is linked to a RUN only when the caller supplies a real
 * run_id/task_id captured from the current task state at creation time,
 * or when the handoff flow itself created/linked it through task_control.
 * Nothing is inferred from chat content.
 *
 * Every public method resolves with a result object and never throws:
 *   { ok: true,  state, data }
 *   { ok: false, state, error: { code, message } }
 * mirroring the CoS companion adapter so a dead provider can never take
 * the main process down.
 */
const fs = require('fs');
const path = require('path');
const { canonicalPathKey } = require('./pathSemantics');

const MAX_PROMPT_CHARS = 20_000; // mirrors the bridge prompt bound
const MAX_TEXT_CHARS = 65_536; // mirrors the bridge agent-text bound
const MAX_EVENTS_KEPT = 100;
const VALID_EFFORTS = Object.freeze(['low', 'medium', 'high', 'xhigh', 'max', 'ultra']);
// W4 send_replay_directive values that forbid a blind continuation.
const BLOCKING_DIRECTIVES = Object.freeze(new Set(['RECONCILE_BEFORE_REPLAY', 'ALREADY_CONFIRMED']));
const RESUME_NOTE = 'Resume phụ thuộc App Server còn giữ thread này trong CODEX_HOME; '
  + 'timeline panel không được khôi phục — chỉ quyền sở hữu thread và liên kết RUN quay lại.';

const CHAT_STATES = Object.freeze({
  UNKNOWN: 'UNKNOWN', // never probed
  READY: 'READY', // bridge status OK, no turn running
  RUNNING: 'RUNNING', // a turn is in progress on the current thread
  COMPLETED: 'COMPLETED', // last turn completed
  FAILED: 'FAILED', // last turn failed at the provider/bridge
  INTERRUPTED: 'INTERRUPTED', // last turn interrupted
  PROVIDER_UNAVAILABLE: 'PROVIDER_UNAVAILABLE', // no codex binary / provider
  MCP_UNAVAILABLE: 'MCP_UNAVAILABLE', // the local MCP runtime is not up
  OWNERSHIP_LOST: 'OWNERSHIP_LOST', // resume failed / thread not owned anymore
});

// Terminal RUN statuses in the orchestration ledger (the ledger's own
// terminal_statuses vocabulary). Any other status — including an unknown
// one — is treated as not-ended so the gate never blocks on vocabulary
// it does not recognize.
const TERMINAL_RUN_STATUSES = new Set(['completed', 'failed']);

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
  if (/PERSISTENT_THREAD_NOT_FOUND|PERSISTENT_SESSION_MISMATCH|PERSISTENT_WORKSPACE_MISMATCH|PERSISTENT_THREAD_RESUME_FAILED/i.test(message)) {
    return { code: 'RESUME_FAILED', state: CHAT_STATES.OWNERSHIP_LOST, message };
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
  // Generic MCP tool channel (main wires callMcpTool). Used ONLY for the
  // existing task_control surface (task start + handoff capsule), exactly
  // like the workhub:job-run / workhub:handoff-get handlers do.
  const callTool = typeof options.callTool === 'function' ? options.callTool : null;
  // Read-only controller-lease projection from the orchestration ledger
  // (main wires workHubCoordination.runDetail). There is no lease write
  // API on the panel side; this service never invents one.
  const readLease = typeof options.readLease === 'function' ? options.readLease : null;
  // Read-only RUN status projection from the same ledger read (main wires
  // workHubCoordination.runDetail and returns detail.run.status). Used
  // only for the ended-RUN handoff gate; absence skips the gate and the
  // record path's own binding check remains the backstop.
  const readRunStatus = typeof options.readRunStatus === 'function' ? options.readRunStatus : null;
  // Durable session-registry file (main injects a path beside the app
  // data; tests inject a tmp-dir path). Absent -> in-memory only.
  const stateFile = String(options.stateFile || options.registryFile || '').trim() || null;
  const sessions = new Map(); // canonical workspace key -> session
  // P2: one canonical workspace key. A workspace spelled two ways (8.3
  // short name, junction, subst) is the same directory, so sessions are
  // keyed by canonicalPathKey(root) — never by the raw spelling. A root
  // that canonicalizes to '' (empty / unresolvable) keeps its raw string
  // so empty-root behavior is unchanged.
  function sessionKeyFor(root) {
    return canonicalPathKey(root) || String(root || '');
  }

  // ---------------- durable session registry ----------------------------
  function readRegistry() {
    if (!stateFile) return {};
    try {
      const parsed = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
      return parsed && parsed.sessions && typeof parsed.sessions === 'object' ? parsed.sessions : {};
    } catch {
      return {};
    }
  }

  function persistSession(session) {
    if (!stateFile || !session) return;
    try {
      const all = readRegistry();
      if (session.threadId) {
        all[session.workspace] = {
          workspace: session.workspace,
          threadId: session.threadId,
          sessionId: session.sessionId || null,
          profile: session.profile || 'chat',
          title: session.title || null,
          createdAt: session.createdAt || null,
          updatedAt: session.updatedAt || new Date().toISOString(),
          link: session.link || null,
          forkedFrom: session.forkedFrom || null,
          route: session.route || null,
          handoff: session.handoff || null,
          lastState: session.state,
        };
        // P2 migration: drop the legacy raw-spelling entry once the
        // session is re-persisted under its canonical key.
        if (session.migratedFromKey && session.migratedFromKey !== session.workspace) delete all[session.migratedFromKey];
      } else {
        delete all[session.workspace];
        if (session.migratedFromKey && session.migratedFromKey !== session.workspace) delete all[session.migratedFromKey];
      }
      fs.mkdirSync(path.dirname(stateFile), { recursive: true });
      const temp = `${stateFile}.tmp-${process.pid}`;
      fs.writeFileSync(temp, JSON.stringify({ version: 1, sessions: all }, null, 2));
      fs.renameSync(temp, stateFile);
    } catch {
      // Persistence must never break the chat itself; the in-memory
      // session stays authoritative for this process.
    }
  }

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
      routeOverride: null, // { model, effort } chosen in the panel (W3-C)
      profile: 'chat',
      title: null,
      createdAt: null,
      forkedFrom: null, // source Desktop thread id when forked (W3-C)
      handoff: null, // last handoff receipt / blocked directive (W3-C)
      handoffMismatch: null, // transient P0 choice state: { linkRunId, linkTaskId, currentRunId, currentTaskId, hasPendingCapsule } — never persisted
      resumeInfo: null, // last resume attempt outcome (W3-C)
      ownedVerified: false, // this process holds the thread (created/resumed)
      restoredFromRegistry: false, // thread came from the durable registry
      migratedFromKey: null, // transient P2 migration marker (never persisted; persistSession writes explicit fields only)
      link: null, // { runId, taskId } — real ids only, set at creation
      messages: [], // { role: 'user'|'assistant', text, turnId, status }
      events: [], // { cursor, method, itemType, status }
      error: null,
      updatedAt: null,
    };
  }

  function sessionFor(root) {
    const key = sessionKeyFor(root);
    const rawKey = String(root || '');
    if (!sessions.has(key)) {
      const fresh = newSession(key);
      sessions.set(key, fresh);
      if (stateFile) {
        const registry = readRegistry();
        const canonicalEntry = registry[key];
        // P2 migration (dual-read): a session persisted under a legacy
        // raw-spelling key is still found when the same workspace is
        // addressed by its canonical key; it is re-persisted under the
        // canonical key on the next persist (see persistSession).
        const entry = canonicalEntry || (key !== rawKey ? registry[rawKey] : undefined);
        if (entry && entry.threadId) {
          fresh.threadId = cleanId(entry.threadId);
          fresh.sessionId = cleanId(entry.sessionId);
          fresh.profile = entry.profile ? String(entry.profile) : 'chat';
          fresh.title = entry.title ? String(entry.title) : null;
          fresh.createdAt = entry.createdAt || null;
          fresh.link = entry.link && entry.link.runId
            ? { runId: cleanId(entry.link.runId), taskId: cleanId(entry.link.taskId) || null }
            : null;
          fresh.forkedFrom = entry.forkedFrom ? cleanId(entry.forkedFrom) : null;
          fresh.route = entry.route && typeof entry.route === 'object' ? entry.route : null;
          fresh.handoff = entry.handoff && typeof entry.handoff === 'object' ? entry.handoff : null;
          fresh.state = entry.lastState && entry.lastState !== CHAT_STATES.RUNNING
            ? entry.lastState
            : CHAT_STATES.UNKNOWN;
          fresh.updatedAt = entry.updatedAt || null;
          fresh.restoredFromRegistry = true;
          fresh.ownedVerified = false;
          if (!canonicalEntry && key !== rawKey && registry[rawKey]) fresh.migratedFromKey = rawKey;
        }
      }
    }
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
      routeOverride: session.routeOverride,
      profile: session.profile || 'chat',
      title: session.title,
      createdAt: session.createdAt,
      forkedFrom: session.forkedFrom,
      handoff: session.handoff,
      handoffMismatch: session.handoffMismatch || null,
      resume: session.resumeInfo,
      ownership: {
        verified: session.ownedVerified,
        restoredFromRegistry: session.restoredFromRegistry,
        note: RESUME_NOTE,
      },
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
    if (classified.code === 'THREAD_NOT_OWNED') session.ownedVerified = false;
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

  // Take back a registry-restored thread through bridge action=resume.
  // Only a real resume failure may classify the session OWNERSHIP_LOST.
  async function attemptResume(session) {
    try {
      const result = await bridge(session, {
        action: 'resume',
        thread_id: session.threadId,
        session_id: session.sessionId || '',
        profile: session.profile || 'chat',
      }, 30_000);
      session.ownedVerified = true;
      if (result.session_id) session.sessionId = cleanId(result.session_id);
      if (result.route && typeof result.route === 'object') {
        session.route = {
          profile: String(result.route.profile || session.profile || 'chat'),
          model: result.route.model ? String(result.route.model) : null,
          effort: result.route.effort ? String(result.route.effort) : null,
        };
      }
      session.resumeInfo = { ok: true, at: new Date().toISOString(), note: RESUME_NOTE };
      if (session.state === CHAT_STATES.OWNERSHIP_LOST || session.state === CHAT_STATES.UNKNOWN) {
        session.state = CHAT_STATES.READY;
      }
      session.error = null;
      session.updatedAt = new Date().toISOString();
      persistSession(session);
      return { ok: true };
    } catch (err) {
      const classified = classifyBridgeError(err);
      session.ownedVerified = false;
      session.state = CHAT_STATES.OWNERSHIP_LOST;
      session.error = {
        code: classified.code === 'BRIDGE_ERROR' ? 'RESUME_FAILED' : classified.code,
        message: classified.message,
      };
      session.resumeInfo = { ok: false, at: new Date().toISOString(), note: RESUME_NOTE };
      session.updatedAt = new Date().toISOString();
      persistSession(session);
      return { ok: false, classified };
    }
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
      // A successful probe also clears a startup FAILED (W6 §8.3): a
      // generic bridge failure at app start lands in FAILED through
      // fail(), but no turn ever started (turnId is still empty), so
      // there is no failed turn to stay honest about — the panel must
      // not stay stuck on FAILED while showing a live version. A real
      // failed turn always has a turnId and keeps its FAILED state.
      // Auxiliary paths (listHistory/listModels) never write session
      // state at all — their catch blocks return the error beside the
      // unchanged state — so probe is the only recovery needed here.
      if (session.state === CHAT_STATES.UNKNOWN || session.state === CHAT_STATES.PROVIDER_UNAVAILABLE || session.state === CHAT_STATES.MCP_UNAVAILABLE
        || (session.state === CHAT_STATES.FAILED && !session.turnId)) {
        session.state = CHAT_STATES.READY;
      }
      session.error = null;
      session.updatedAt = new Date().toISOString();
      // W3-C: a session restored from the durable registry must re-own its
      // thread through the bridge before the panel may continue it.
      if (session.threadId && session.restoredFromRegistry && !session.ownedVerified) {
        const resumed = await attemptResume(session);
        if (!resumed.ok) {
          return { ok: false, state: session.state, error: session.error, data: view(session) };
        }
      }
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
            forkedFrom: cleanId(t && t.forked_from_id) || null,
            continuable: false, // bridge: Desktop threads are inspect/fork only
            forkable: true, // W3-C: run + source_thread_id + profile history
          })).filter((t) => t.id),
        },
      };
    } catch (err) {
      const classified = classifyBridgeError(err);
      return { ok: false, state: session.state, error: { code: classified.code, message: classified.message }, data: null };
    }
  }

  async function listModels(root) {
    const session = sessionFor(root);
    try {
      const result = await bridge(session, { action: 'models' }, 30_000);
      const models = (Array.isArray(result.models) ? result.models : []).map((m) => ({
        id: cleanId(m && m.id),
        displayName: boundedText(m && m.display_name, 120) || null,
        isDefault: Boolean(m && m.is_default),
        defaultEffort: m && m.default_effort ? String(m.default_effort) : null,
        supportedEfforts: Array.isArray(m && m.supported_efforts) ? m.supported_efforts.map((e) => String(e)) : [],
      })).filter((m) => m.id);
      return {
        ok: true,
        state: session.state,
        data: {
          models,
          chatProfileDefault: { model: 'gpt-5.6-terra', effort: 'medium' },
          note: 'Để trống = mặc định của profile chat. Override chỉ đổi model/effort; approvalPolicy=never, sandbox read-only và không mạng không đổi.',
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
    session.ownedVerified = true;
    if (result.session_id) session.sessionId = cleanId(result.session_id);
    const route = result.route && typeof result.route === 'object' ? result.route : {};
    session.route = {
      profile: String(route.profile || session.profile || 'chat'),
      model: route.model ? String(route.model) : null,
      effort: route.effort ? String(route.effort) : null,
    };
    session.profile = session.route.profile;
    if (!session.createdAt) session.createdAt = new Date().toISOString();
    if (!session.title) session.title = boundedText(promptText, 120);
    session.messages.push({ role: 'user', text: promptText, turnId, status: 'completed' });
    session.messages.push({ role: 'assistant', text: '', turnId, status: 'running' });
    session.state = CHAT_STATES.RUNNING;
    session.error = null;
    session.updatedAt = new Date().toISOString();
    persistSession(session);
  }

  // Shared prompt/route validation for send + fork. Returns either
  // { error: {...} } or { text, routeArgs }.
  function prepareTurn(session, payload) {
    const text = String(payload.text ?? '').trim();
    if (!text) {
      return { error: { code: 'CHAT_PROMPT_REQUIRED', message: 'Nội dung chat không được trống.' } };
    }
    if (text.length > MAX_PROMPT_CHARS) {
      return { error: { code: 'CHAT_PROMPT_TOO_LARGE', message: `Nội dung chat vượt giới hạn ${MAX_PROMPT_CHARS} ký tự của bridge.` } };
    }
    if (session.state === CHAT_STATES.RUNNING) {
      return { error: { code: 'TURN_ALREADY_ACTIVE', message: 'Lượt chat trước đang chạy; chờ hoàn tất hoặc dừng lượt trước khi gửi tiếp.' } };
    }
    if (session.state === CHAT_STATES.PROVIDER_UNAVAILABLE || session.state === CHAT_STATES.MCP_UNAVAILABLE) {
      return { error: session.error || { code: 'PROVIDER_UNAVAILABLE', message: 'Codex provider chưa sẵn sàng.' } };
    }
    const routeArgs = {};
    const model = cleanId(payload.model).slice(0, 80);
    const effort = String(payload.effort || '').trim().toLowerCase();
    if (effort && !VALID_EFFORTS.includes(effort)) {
      return { error: { code: 'CHAT_EFFORT_INVALID', message: `Effort không hợp lệ: ${effort}. Chọn một trong: ${VALID_EFFORTS.join(', ')}.` } };
    }
    if (model) routeArgs.model = model;
    if (effort) routeArgs.effort = effort;
    if (model || effort) {
      session.routeOverride = { model: model || null, effort: effort || null };
    }
    return { text, routeArgs };
  }

  async function send(root, payload = {}) {
    const session = sessionFor(root);
    const prepared = prepareTurn(session, payload);
    if (prepared.error) {
      return { ok: false, state: session.state, error: prepared.error, data: view(session) };
    }
    const { text, routeArgs } = prepared;
    try {
      if (!session.threadId) {
        const result = await bridge(session, {
          action: 'run', prompt: text, profile: 'chat', lifetime: 'persistent', ...routeArgs,
        }, 30_000);
        // Link only from real ids supplied by the caller (captured from the
        // current task state in the renderer) — never inferred from content.
        const runId = cleanId(payload.link && payload.link.runId);
        const taskId = cleanId(payload.link && payload.link.taskId);
        session.link = runId ? { runId, taskId: taskId || null } : null;
        recordTurnStart(session, result, text);
      } else {
        // A registry-restored thread must be resumed before it is continued.
        if (session.restoredFromRegistry && !session.ownedVerified) {
          const resumed = await attemptResume(session);
          if (!resumed.ok) {
            return { ok: false, state: session.state, error: session.error, data: view(session) };
          }
        }
        try {
          const result = await bridge(session, {
            action: 'continue', thread_id: session.threadId, prompt: text, ...routeArgs,
          }, 30_000);
          recordTurnStart(session, result, text);
        } catch (err) {
          // THREAD_NOT_OWNED is not yet proof of loss: the sidecar may have
          // restarted while this process kept the session. Try ONE resume
          // of the registered persistent thread, then retry continue once.
          // Only a failed resume (or a failed retry) is OWNERSHIP_LOST.
          if (classifyBridgeError(err).code !== 'THREAD_NOT_OWNED') throw err;
          const resumed = await attemptResume(session);
          if (!resumed.ok) {
            // Ownership is only declared lost now that resume has also
            // failed; keep the original THREAD_NOT_OWNED as the headline
            // code and attach the resume failure as evidence.
            const resumeMessage = session.error ? session.error.message : '';
            session.state = CHAT_STATES.OWNERSHIP_LOST;
            session.error = {
              code: 'THREAD_NOT_OWNED',
              message: `${boundedText(err && err.message ? err.message : String(err), 300)} · Resume phiên bền cũng thất bại: ${resumeMessage}`,
            };
            session.updatedAt = new Date().toISOString();
            return { ok: false, state: session.state, error: session.error, data: view(session) };
          }
          const retried = await bridge(session, {
            action: 'continue', thread_id: session.threadId, prompt: text, ...routeArgs,
          }, 30_000);
          recordTurnStart(session, retried, text);
        }
      }
      return { ok: true, state: session.state, data: view(session) };
    } catch (err) {
      return fail(session, classifyBridgeError(err));
    }
  }

  async function fork(root, payload = {}) {
    const session = sessionFor(root);
    const sourceThreadId = cleanId(payload.sourceThreadId || payload.source_thread_id);
    if (!sourceThreadId) {
      return { ok: false, state: session.state, error: { code: 'FORK_SOURCE_REQUIRED', message: 'Chưa chọn thread lịch sử Desktop để fork.' }, data: view(session) };
    }
    const prepared = prepareTurn(session, payload);
    if (prepared.error) {
      return { ok: false, state: session.state, error: prepared.error, data: view(session) };
    }
    const { text, routeArgs } = prepared;
    try {
      const result = await bridge(session, {
        action: 'run',
        prompt: text,
        profile: 'history',
        source_thread_id: sourceThreadId,
        lifetime: 'persistent',
        ...routeArgs,
      }, 30_000);
      // The fork is a NEW chat in this panel: the old timeline belongs to
      // the previous thread and the Desktop turns were never readable
      // here, so the timeline restarts from the fork prompt. The fork
      // inherits context inside the App Server (thread/fork), not by the
      // panel copying turns.
      session.messages = [];
      session.events = [];
      session.cursor = 0;
      session.turnId = '';
      session.threadId = '';
      session.handoff = null;
      session.createdAt = null;
      session.title = null;
      session.forkedFrom = sourceThreadId;
      const runId = cleanId(payload.link && payload.link.runId);
      const taskId = cleanId(payload.link && payload.link.taskId);
      session.link = runId ? { runId, taskId: taskId || null } : null;
      recordTurnStart(session, result, text);
      return { ok: true, state: session.state, data: view(session) };
    } catch (err) {
      return fail(session, classifyBridgeError(err));
    }
  }

  async function resume(root) {
    const session = sessionFor(root);
    if (!session.threadId) {
      return { ok: false, state: session.state, error: { code: 'NO_PERSISTED_THREAD', message: 'Chưa có phiên chat bền nào để resume.' }, data: view(session) };
    }
    const resumed = await attemptResume(session);
    if (!resumed.ok) {
      return { ok: false, state: session.state, error: session.error, data: view(session) };
    }
    return { ok: true, state: session.state, data: view(session) };
  }

  // ---------------- W3-C handoff to an operating task -------------------
  function directiveFrom(result) {
    const raw = result && (result.send_replay_directive ?? result.sendReplayDirective);
    let name = '';
    let checkpointState = null;
    if (typeof raw === 'string') name = raw;
    else if (raw && typeof raw === 'object') {
      name = String(raw.directive || '');
      checkpointState = raw.state || null;
    }
    const recommended = result && typeof result.recommended_next_action === 'string'
      ? result.recommended_next_action
      : null;
    if (!name && !recommended) return null;
    return { directive: name || null, state: checkpointState, recommendedNextAction: recommended };
  }

  function buildCapsule(session, objective, runId, taskId) {
    const recent = session.messages.slice(-6).map((m) => ({ role: m.role, text: boundedText(m.text, 500) }));
    const lastAssistant = [...session.messages].reverse().find((m) => m.role === 'assistant' && m.text);
    return {
      source: 'workhub-codex-chat',
      kind: 'codex-chat-handoff',
      objective: boundedText(objective, 500),
      summary: lastAssistant ? boundedText(lastAssistant.text, 1000) : '',
      recent_turns: recent,
      thread_ref: {
        thread_id: session.threadId || null,
        session_id: session.sessionId || null,
        profile: (session.route && session.route.profile) || session.profile || 'chat',
        forked_from: session.forkedFrom || null,
      },
      chat_link: { run_id: runId || null, task_id: taskId || null },
      // The controller lease (holder + expiry) lives in the orchestration
      // ledger and is read through workHubCoordination.runDetail. The
      // panel has no lease write API — record that here instead of
      // inventing one.
      lease_note: 'Controller lease is read-only from the orchestration ledger (workHubCoordination.runDetail); no panel lease write API exists.',
      send_checkpoint: { state: 'not_attempted', message_id: '' },
    };
  }

  async function handoffToTask(root, payload = {}) {
    const session = sessionFor(root);
    const refuse = (code, message) => ({ ok: false, state: session.state, error: { code, message }, data: view(session) });
    if (!session.messages.length) {
      return refuse('CHAT_HANDOFF_NO_CONTENT', 'Phiên chat chưa có nội dung nào để chuyển thành việc điều hành.');
    }
    if (!callTool) {
      return refuse('CHAT_HANDOFF_NOT_WIRED', 'Kênh task_control chưa được nối trong main process — chưa có đường tạo việc khả thi.');
    }
    if (session.state === CHAT_STATES.RUNNING) {
      return refuse('CHAT_HANDOFF_TURN_ACTIVE', 'Lượt chat đang chạy; chờ hoàn tất hoặc dừng lượt trước khi chuyển thành việc điều hành.');
    }
    const firstUser = session.messages.find((m) => m.role === 'user');
    const objective = boundedText(
      String(payload.objective || '').trim() || (firstUser ? firstUser.text : '') || session.title || '',
      500,
    );
    if (!objective) {
      return refuse('CHAT_HANDOFF_NO_CONTENT', 'Không dựng được mục tiêu cho việc điều hành từ phiên chat này.');
    }
    try {
      // P0 (L1/L5): resolve the target RUN against the panel's CURRENT
      // task before writing anything. The chat link is frozen from
      // creation, while the panel may since have moved to another RUN;
      // silently using the stale link writes the capsule to the wrong
      // task, and silently creating a new task duplicates it. Neither
      // happens here: a mismatch stops and asks the operator to choose.
      const currentRunId = cleanId(payload.runId) || cleanId(payload.link && payload.link.runId);
      const currentTaskId = cleanId(payload.link && payload.link.taskId);
      const linkRunId = cleanId(session.link && session.link.runId);
      const linkTaskId = cleanId(session.link && session.link.taskId);
      let runId = null;
      let taskId = null;
      let createNew = false;
      if (currentRunId && linkRunId && currentRunId !== linkRunId) {
        const choice = String(payload.choice || '').trim();
        if (choice === 'current') {
          runId = currentRunId;
          taskId = currentTaskId || linkTaskId;
        } else if (choice === 'link') {
          runId = linkRunId;
          taskId = linkTaskId;
        } else if (choice === 'new') {
          createNew = true;
        } else {
          session.handoffMismatch = {
            linkRunId,
            linkTaskId: linkTaskId || null,
            currentRunId,
            currentTaskId: currentTaskId || null,
            hasPendingCapsule: Boolean(session.handoff && session.handoff.pendingCapsule),
          };
          session.updatedAt = new Date().toISOString();
          persistSession(session);
          return {
            ok: false,
            state: session.state,
            error: {
              code: 'HANDOFF_RUN_MISMATCH',
              message: `Phiên chat đang liên kết RUN ${linkRunId} nhưng tác vụ hiện tại của panel là RUN ${currentRunId}. Chọn nơi ghi capsule thay vì để hệ thống tự đoán.`,
              linkRunId,
              linkTaskId: linkTaskId || null,
              currentRunId,
              currentTaskId: currentTaskId || null,
            },
            data: view(session),
          };
        }
        session.handoffMismatch = null;
      } else if (currentRunId) {
        runId = currentRunId;
        taskId = currentTaskId || linkTaskId;
      } else if (linkRunId) {
        runId = linkRunId;
        taskId = linkTaskId;
      } else {
        createNew = true;
      }
      let directiveInfo = null;
      if (runId) {
        // P0 (L1 scenario B): writing a capsule into an ended RUN needs
        // an explicit confirmation; by default it is refused. The status
        // comes from the ledger read; when the reader is absent the gate
        // is skipped and the record path's own binding check backstops.
        if (readRunStatus) {
          let runStatus = null;
          try { runStatus = await readRunStatus(root, runId); } catch { runStatus = null; }
          const normalized = typeof runStatus === 'string' ? runStatus.trim().toLowerCase() : '';
          if (normalized && TERMINAL_RUN_STATUSES.has(normalized) && payload.confirmEnded !== true) {
            return {
              ok: false,
              state: session.state,
              error: {
                code: 'HANDOFF_RUN_ENDED',
                message: `RUN ${runId} đã kết thúc (trạng thái ${normalized}). Ghi capsule vào RUN đã kết thúc cần xác nhận rõ ràng.`,
                runId,
                runStatus: normalized,
              },
              data: view(session),
            };
          }
        }
        // Respect the W4 directive of the RUN's current capsule BEFORE
        // recording anything new or creating anything new.
        const getResult = await callTool('task_control', {
          action: 'handoff', handoff_action: 'get', run_id: runId,
        }, 15_000);
        directiveInfo = directiveFrom(getResult);
        if (directiveInfo && BLOCKING_DIRECTIVES.has(directiveInfo.directive)) {
          session.handoff = {
            status: 'blocked',
            runId,
            taskId: taskId || null,
            capsuleId: null,
            directive: directiveInfo.directive,
            recommendedNextAction: directiveInfo.recommendedNextAction,
            lease: null,
            capsuleNote: 'Directive của capsule hiện tại cấm tiếp tục mù: không tạo task mới, không ghi capsule mới, không replay.',
            objective,
            at: new Date().toISOString(),
          };
          session.updatedAt = new Date().toISOString();
          persistSession(session);
          return {
            ok: false,
            state: session.state,
            error: {
              code: 'HANDOFF_DIRECTIVE_BLOCKED',
              message: `Handoff bị chặn bởi directive ${directiveInfo.directive}. ${directiveInfo.recommendedNextAction || 'Hãy reconcile trước khi tiếp tục.'}`,
            },
            data: view(session),
          };
        }
      }
      if (createNew) {
        // Existing Work Hub task-creation path: task_control action=start
        // (the same callMcpTool channel as job-run / handoff-get).
        const startResult = await callTool('task_control', {
          action: 'start',
          objective,
          current_step: 'Đã chuyển từ Chat Codex (native) thành việc điều hành',
          next_step: 'Đọc capsule handoff của phiên chat và tiếp tục từ đó; không replay mù các effect chưa rõ.',
        }, 30_000);
        const started = (startResult && startResult.state) || {};
        taskId = cleanId(started.task_id) || taskId;
        runId = cleanId(started.orchestration && started.orchestration.run_id);
        if (runId || taskId) session.link = { runId: runId || null, taskId: taskId || null };
      }
      const capsulePayload = buildCapsule(session, objective, runId, taskId);
      let capsule = null;
      let capsuleNote = null;
      let recommended = null;
      if (runId) {
        // P0 (L6): flush a pending capsule from an earlier handoff into
        // this RUN instead of leaving it stranded in the registry. It is
        // cleared only after a successful record, so a failed flush never
        // loses it; the fresh capsule for this handoff is recorded after.
        const pending = session.handoff && session.handoff.pendingCapsule ? session.handoff.pendingCapsule : null;
        if (pending) {
          await callTool('task_control', {
            action: 'handoff', handoff_action: 'record', run_id: runId, payload: pending,
          }, 15_000);
          session.handoff.pendingCapsule = null;
        }
        const recordResult = await callTool('task_control', {
          action: 'handoff', handoff_action: 'record', run_id: runId, payload: capsulePayload,
        }, 15_000);
        capsule = (recordResult && recordResult.capsule) || null;
        recommended = recordResult && typeof recordResult.recommended_next_action === 'string'
          ? recordResult.recommended_next_action
          : null;
      } else {
        capsuleNote = 'Task đã tạo nhưng chưa có RUN: capsule và lease của ledger đều khóa theo run_id, '
          + 'nên capsule được giữ ở handoff.pendingCapsule trong registry phiên chat và chỉ ghi vào ledger khi phiên được liên kết một RUN thật.';
      }
      let lease = null;
      if (runId && readLease) {
        try { lease = await readLease(root, runId); } catch { lease = null; }
      }
      session.handoff = {
        status: capsule ? 'recorded' : 'task_created',
        runId: runId || null,
        taskId: taskId || null,
        capsuleId: capsule ? cleanId(capsule.capsule_id) || null : null,
        directive: directiveInfo ? directiveInfo.directive : null,
        recommendedNextAction: (directiveInfo && directiveInfo.recommendedNextAction) || recommended,
        lease: lease
          ? {
            owner: lease.owner || null,
            status: lease.status || null,
            expiresAt: lease.expiresAt || null,
            leaseId: lease.leaseId || null,
          }
          : null,
        leaseNote: lease ? null : 'Không đọc được lease từ ledger cho RUN này — lease chỉ đọc qua workHubCoordination.runDetail, panel không ghi lease.',
        capsuleNote,
        pendingCapsule: capsule ? null : capsulePayload,
        objective,
        at: new Date().toISOString(),
      };
      // A resolved handoff settles the mismatch: the chosen RUN becomes
      // the chat link, so the next handoff compares against it, not the
      // stale creation-time link.
      session.handoffMismatch = null;
      if (runId || taskId) session.link = { runId: runId || null, taskId: taskId || null };
      session.updatedAt = new Date().toISOString();
      persistSession(session);
      return { ok: true, state: session.state, data: view(session) };
    } catch (err) {
      const message = boundedText(err && err.message ? err.message : String(err || 'Handoff thất bại.'), 400);
      return { ok: false, state: session.state, error: { code: 'HANDOFF_FAILED', message }, data: view(session) };
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
        session.updatedAt = new Date().toISOString();
        persistSession(session);
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
    // After a restart the session may hold a thread but no turnId (the
    // registry does not persist one) while the bridge reports an active
    // turn the panel never launched (state RUNNING via the
    // TURN_ALREADY_ACTIVE classification). That orphan turn must still be
    // interruptible: call the bridge with an empty turn_id and let it
    // resolve the latest turn it tracks for the thread.
    if (!session.threadId || (!session.turnId && session.state !== CHAT_STATES.RUNNING)) {
      return { ok: false, state: session.state, error: { code: 'NO_ACTIVE_TURN', message: 'Không có lượt chat nào để dừng.' }, data: view(session) };
    }
    try {
      await bridge(session, { action: 'interrupt', thread_id: session.threadId, turn_id: session.turnId }, 15_000);
      session.error = null;
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
    const key = sessionKeyFor(root);
    const rawKey = String(root || '');
    const previous = sessions.get(key);
    const fresh = newSession(key);
    if (key !== rawKey) fresh.migratedFromKey = rawKey;
    if (previous) fresh.availability = previous.availability;
    fresh.state = fresh.availability ? CHAT_STATES.READY : CHAT_STATES.UNKNOWN;
    sessions.set(key, fresh);
    persistSession(fresh); // no threadId -> removes the registry entry
    return { ok: true, state: fresh.state, data: view(fresh) };
  }

  function getView(root) {
    const session = sessionFor(root);
    return { ok: true, state: session.state, data: view(session) };
  }

  return {
    probe, listHistory, listModels, send, fork, resume, handoffToTask,
    poll, interrupt, reset, getView, CHAT_STATES,
  };
}

module.exports = { createWorkHubCodexChat, CHAT_STATES, classifyBridgeError };
