'use strict';
/*
 * W3 native Codex chat tests.
 *
 * A scripted fake plays the runtime's internal codex_bridge tool exactly as
 * codex_bridge.py defines it (run/continue/observe/interrupt/status/threads
 * result shapes). The service under test is the main-process session layer
 * (electron/services/workHubCodexChat.js) with the transport injected — no
 * Electron, no MCP runtime, no Codex provider. Live proof against the real
 * provider is a separate Windows step (provider is live there; the VM
 * snapshot has no provider).
 */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { createWorkHubCodexChat, classifyBridgeError } = require('../electron/services/workHubCodexChat');

const ROOT = '/tmp/workhub-chat-test-workspace';

function makeFakeBridge(overrides = {}) {
  const calls = [];
  const state = {
    observeQueue: [
      { status: 'inProgress', terminal: false, agent_text: 'Đang soạn…', events: [{ cursor: 1, method: 'turn/started', item_type: null, status: 'inProgress' }], next_cursor: 1 },
      { status: 'completed', terminal: true, agent_text: 'Xin chào! Workspace có README.md và thư mục src.', events: [{ cursor: 2, method: 'turn/completed', item_type: null, status: 'completed' }], next_cursor: 2 },
    ],
  };
  const handlers = {
    status: async () => ({ ok: true, connected: true, binary: 'C:\\Users\\Admin\\AppData\\Roaming\\npm\\codex.cmd', codex_version: '0.149.0', codex_home: 'C:\\Users\\Admin\\.codex', workspace: ROOT }),
    threads: async () => ({ ok: true, scope: 'current_workspace_only', note: 'Persisted history only', threads: [{ id: 'desk-1', name: 'Phiên Desktop cũ', preview: 'Hỏi về…', updated_at: 1792000000000, status: 'idle' }] }),
    run: async (args) => ({ ok: true, status: 'running', thread_id: 'thread-1', turn_id: 'turn-1', session_id: 'sess-1', creation_mode: 'new', route: { profile: args.profile, model: 'gpt-5.6-terra', effort: 'medium' } }),
    continue: async () => ({ ok: true, status: 'running', thread_id: 'thread-1', turn_id: 'turn-2', session_id: 'sess-1', creation_mode: 'continue', route: { profile: 'chat', model: 'gpt-5.6-terra', effort: 'medium' } }),
    observe: async () => state.observeQueue.shift() || { status: 'completed', terminal: true, agent_text: '', events: [], next_cursor: 2 },
    interrupt: async () => ({ ok: true, interrupt_requested: true }),
    models: async () => ({ ok: true, models: [{ id: 'gpt-5.6-terra', display_name: 'Terra', is_default: true, default_effort: 'medium', supported_efforts: ['low', 'medium', 'high'] }, { id: 'gpt-5.6-sol', display_name: 'Sol', is_default: false, default_effort: 'high', supported_efforts: ['medium', 'high', 'xhigh'] }] }),
    resume: async (args) => ({ ok: true, resumed: true, thread_id: args.thread_id, session_id: args.session_id || 'sess-1', creation_mode: 'persistent_restore', lifetime: 'persistent', route: { profile: 'chat', model: 'gpt-5.6-terra', effort: 'medium' } }),
    ...overrides,
  };
  const callBridge = async (args) => {
    calls.push({ ...args });
    const handler = handlers[args.action];
    if (!handler) throw new Error(`fake bridge: unexpected action ${args.action}`);
    return handler(args);
  };
  return { callBridge, calls, state };
}

test('(a) probe reports READY with provider identity when the bridge answers', async () => {
  const fake = makeFakeBridge();
  const chat = createWorkHubCodexChat({ callBridge: fake.callBridge });
  const result = await chat.probe(ROOT);
  assert.equal(result.ok, true);
  assert.equal(result.data.state, 'READY');
  assert.match(result.data.availability.binary, /codex\.cmd$/);
  assert.equal(result.data.availability.codexVersion, '0.149.0');
  assert.deepEqual(fake.calls.map((c) => c.action), ['status']);
});

test('(a2) probe maps a missing Codex binary to PROVIDER_UNAVAILABLE and send refuses without calling run', async () => {
  const fake = makeFakeBridge({
    status: async () => { throw new Error('Codex CLI was not found. Install Codex Desktop/CLI or set CODING_TOOLS_MCP_CODEX_BIN.'); },
  });
  const chat = createWorkHubCodexChat({ callBridge: fake.callBridge });
  const probe = await chat.probe(ROOT);
  assert.equal(probe.ok, false);
  assert.equal(probe.data.state, 'PROVIDER_UNAVAILABLE');
  assert.equal(probe.error.code, 'CODEX_NOT_FOUND');
  const send = await chat.send(ROOT, { text: 'Chào bạn' });
  assert.equal(send.ok, false);
  assert.equal(send.error.code, 'CODEX_NOT_FOUND');
  assert.equal(fake.calls.filter((c) => c.action === 'run').length, 0);
});

test('(b) first send creates the thread via run with the chat profile and records a real link only when supplied', async () => {
  const fake = makeFakeBridge();
  const chat = createWorkHubCodexChat({ callBridge: fake.callBridge });
  await chat.probe(ROOT);
  const result = await chat.send(ROOT, { text: 'Workspace này có gì?', link: { runId: 'run-123', taskId: 'task-9' } });
  assert.equal(result.ok, true);
  const runCall = fake.calls.find((c) => c.action === 'run');
  assert.equal(runCall.profile, 'chat');
  assert.equal(runCall.prompt, 'Workspace này có gì?');
  assert.equal(result.data.threadId, 'thread-1');
  assert.equal(result.data.state, 'RUNNING');
  assert.deepEqual(result.data.link, { runId: 'run-123', taskId: 'task-9' });
  assert.deepEqual(result.data.messages.map((m) => [m.role, m.status]), [['user', 'completed'], ['assistant', 'running']]);

  const fake2 = makeFakeBridge();
  const chat2 = createWorkHubCodexChat({ callBridge: fake2.callBridge });
  const noLink = await chat2.send(ROOT, { text: 'Chào' });
  assert.equal(noLink.ok, true);
  assert.equal(noLink.data.link, null);
});

test('(c) poll streams agent_text by cursor and lands on COMPLETED with the final text', async () => {
  const fake = makeFakeBridge();
  const chat = createWorkHubCodexChat({ callBridge: fake.callBridge });
  await chat.send(ROOT, { text: 'Tóm tắt workspace' });
  const first = await chat.poll(ROOT);
  assert.equal(first.data.state, 'RUNNING');
  assert.equal(first.data.messages[1].text, 'Đang soạn…');
  const observeCall = fake.calls.find((c) => c.action === 'observe');
  assert.equal(observeCall.after_cursor, 0);
  const second = await chat.poll(ROOT);
  assert.equal(second.data.state, 'COMPLETED');
  assert.equal(second.data.messages[1].status, 'completed');
  assert.match(second.data.messages[1].text, /README\.md/);
  assert.equal(second.data.events.length, 2);
  // Terminal: further polls are local no-ops, no more bridge calls.
  const before = fake.calls.length;
  const third = await chat.poll(ROOT);
  assert.equal(third.data.state, 'COMPLETED');
  assert.equal(fake.calls.length, before);
});

test('(d) the second send continues the same bridge-owned thread', async () => {
  const fake = makeFakeBridge();
  const chat = createWorkHubCodexChat({ callBridge: fake.callBridge });
  await chat.send(ROOT, { text: 'Câu một' });
  await chat.poll(ROOT);
  await chat.poll(ROOT); // turn completes
  const result = await chat.send(ROOT, { text: 'Câu hai' });
  assert.equal(result.ok, true);
  const cont = fake.calls.find((c) => c.action === 'continue');
  assert.equal(cont.thread_id, 'thread-1');
  assert.equal(result.data.turnId, 'turn-2');
  assert.equal(result.data.messages.length, 4);
});

test('(e) THREAD_NOT_OWNED surfaces OWNERSHIP_LOST, and reset starts a fresh chat', async () => {
  let continueFails = true;
  const fake = makeFakeBridge({
    continue: async () => {
      if (continueFails) throw new Error('The bridge will not control an arbitrary Codex Desktop thread. THREAD_NOT_OWNED');
      return { ok: true, status: 'running', thread_id: 'thread-1', turn_id: 'turn-9', route: { profile: 'chat', model: 'gpt-5.6-terra', effort: 'medium' } };
    },
  });
  const chat = createWorkHubCodexChat({ callBridge: fake.callBridge });
  await chat.send(ROOT, { text: 'Câu một' });
  await chat.poll(ROOT);
  await chat.poll(ROOT);
  const lost = await chat.send(ROOT, { text: 'Câu hai' });
  assert.equal(lost.ok, false);
  assert.equal(lost.data.state, 'OWNERSHIP_LOST');
  assert.equal(lost.error.code, 'THREAD_NOT_OWNED');
  // The timeline survives the ownership loss.
  assert.equal(lost.data.messages.length, 2);
  const reset = chat.reset(ROOT);
  assert.equal(reset.data.threadId, null);
  assert.equal(reset.data.messages.length, 0);
  continueFails = false;
  const fresh = await chat.send(ROOT, { text: 'Chat mới' });
  assert.equal(fresh.ok, true);
  assert.equal(fake.calls.filter((c) => c.action === 'run').length, 2);
});

test('(f) send while a turn is running is refused, empty prompts are rejected, malformed run results are controlled', async () => {
  const fake = makeFakeBridge();
  const chat = createWorkHubCodexChat({ callBridge: fake.callBridge });
  const empty = await chat.send(ROOT, { text: '   ' });
  assert.equal(empty.ok, false);
  assert.equal(empty.error.code, 'CHAT_PROMPT_REQUIRED');
  await chat.send(ROOT, { text: 'Đang chạy' });
  const busy = await chat.send(ROOT, { text: 'Gửi chồng' });
  assert.equal(busy.ok, false);
  assert.equal(busy.error.code, 'TURN_ALREADY_ACTIVE');
  assert.equal(fake.calls.filter((c) => c.action === 'run').length, 1);

  const broken = createWorkHubCodexChat({ callBridge: async () => ({ ok: true }) });
  const malformed = await broken.send(ROOT, { text: 'Chào' });
  assert.equal(malformed.ok, false);
  assert.match(malformed.error.message, /thread_id\/turn_id/);
});

test('(g) history lists persisted Desktop threads as inspect-only', async () => {
  const fake = makeFakeBridge();
  const chat = createWorkHubCodexChat({ callBridge: fake.callBridge });
  const history = await chat.listHistory(ROOT);
  assert.equal(history.ok, true);
  assert.equal(history.data.threads.length, 1);
  assert.equal(history.data.threads[0].continuable, false);
  assert.equal(history.data.threads[0].name, 'Phiên Desktop cũ');
});

test('(h) interrupt calls the bridge and marks the turn interrupted', async () => {
  const fake = makeFakeBridge();
  const chat = createWorkHubCodexChat({ callBridge: fake.callBridge });
  await chat.send(ROOT, { text: 'Lâu lắm' });
  const stopped = await chat.interrupt(ROOT);
  assert.equal(stopped.ok, true);
  assert.equal(stopped.data.state, 'INTERRUPTED');
  assert.equal(fake.calls.at(-1).action, 'interrupt');
  assert.equal(stopped.data.messages[1].status, 'interrupted');
});

test('classifyBridgeError keeps MCP-down distinct from provider-missing', () => {
  assert.equal(classifyBridgeError(new Error('MCP chưa sẵn sàng để chạy lệnh.')).state, 'MCP_UNAVAILABLE');
  assert.equal(classifyBridgeError(new Error('Codex CLI was not found.')).state, 'PROVIDER_UNAVAILABLE');
  assert.equal(classifyBridgeError(new Error('gì đó khác')).code, 'BRIDGE_ERROR');
});

// ---------------- W3-C: fork / durable resume / handoff / route selector ---

function makeFakeTaskControl(overrides = {}) {
  const calls = [];
  const handlers = {
    start: async (args) => ({ state: { task_id: 'task-new-1', objective: args.objective, status: 'active', orchestration: { run_id: 'run-new-1' } } }),
    get: async () => ({ capsule: null, send_replay_directive: null, recommended_next_action: 'Record a bounded handoff capsule before rolling.' }),
    record: async (args) => ({ recorded: true, capsule: { capsule_id: 'cap-1', run_id: args.run_id, payload: args.payload }, recommended_next_action: 'Open a fresh conversation, fetch this capsule, then poll pending messages.' }),
    ...overrides,
  };
  const callTool = async (name, args) => {
    calls.push({ name, args: { ...args } });
    assert.equal(name, 'task_control');
    if (args.action === 'start') return handlers.start(args);
    if (args.action === 'handoff' && args.handoff_action === 'get') return handlers.get(args);
    if (args.action === 'handoff' && args.handoff_action === 'record') return handlers.record(args);
    throw new Error(`fake task_control: unexpected ${args.action}/${args.handoff_action || ''}`);
  };
  return { callTool, calls };
}

test('(i) fork from Desktop history runs profile=history with source_thread_id and the result is continuable', async () => {
  const fake = makeFakeBridge({
    run: async (args) => ({ ok: true, status: 'running', thread_id: 'fork-thread', turn_id: 'fork-turn-1', session_id: 'fork-sess', creation_mode: 'fork', source_thread_id: args.source_thread_id, route: { profile: args.profile, model: 'gpt-5.6-terra', effort: 'medium' } }),
    continue: async () => ({ ok: true, status: 'running', thread_id: 'fork-thread', turn_id: 'fork-turn-2', session_id: 'fork-sess', creation_mode: 'continue', route: { profile: 'history', model: 'gpt-5.6-terra', effort: 'medium' } }),
  });
  const chat = createWorkHubCodexChat({ callBridge: fake.callBridge });
  const history = await chat.listHistory(ROOT);
  assert.equal(history.data.threads[0].forkable, true);
  assert.equal(history.data.threads[0].continuable, false);
  const forked = await chat.fork(ROOT, { sourceThreadId: 'desk-1', text: 'Tiếp tục từ phiên cũ: tóm tắt lại' });
  assert.equal(forked.ok, true);
  const runCall = fake.calls.find((c) => c.action === 'run');
  assert.equal(runCall.profile, 'history');
  assert.equal(runCall.source_thread_id, 'desk-1');
  assert.equal(runCall.lifetime, 'persistent');
  assert.equal(forked.data.threadId, 'fork-thread');
  assert.equal(forked.data.forkedFrom, 'desk-1');
  assert.equal(forked.data.messages.length, 2);
  // The forked thread is bridge-owned, so a follow-up uses continue.
  fake.state.observeQueue = [{ status: 'completed', terminal: true, agent_text: 'Tóm tắt xong.', events: [], next_cursor: 3 }];
  await chat.poll(ROOT);
  const next = await chat.send(ROOT, { text: 'Câu tiếp theo' });
  assert.equal(next.ok, true);
  assert.equal(fake.calls.filter((c) => c.action === 'continue').length, 1);
  // Fork without a first prompt or without a source is refused locally.
  const noPrompt = await chat.fork(ROOT, { sourceThreadId: 'desk-1', text: '  ' });
  assert.equal(noPrompt.error.code, 'CHAT_PROMPT_REQUIRED');
  const noSource = await chat.fork(ROOT, { text: 'Chào' });
  assert.equal(noSource.error.code, 'FORK_SOURCE_REQUIRED');
});

test('(j) a persisted session is resumed on probe after a restart, then continued — not re-run', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wh-chat-registry-'));
  const stateFile = path.join(dir, 'sessions.json');
  const first = makeFakeBridge();
  const chat1 = createWorkHubCodexChat({ callBridge: first.callBridge, stateFile });
  const sent = await chat1.send(ROOT, { text: 'Phiên bền qua restart' });
  assert.equal(sent.ok, true);
  const runCall = first.calls.find((c) => c.action === 'run');
  assert.equal(runCall.lifetime, 'persistent'); // chat threads are durable now
  const registry = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
  const entry = registry.sessions[ROOT];
  assert.equal(entry.threadId, 'thread-1');
  assert.equal(entry.sessionId, 'sess-1');
  assert.equal(entry.profile, 'chat');
  assert.match(entry.title, /Phiên bền/);
  assert.ok(entry.createdAt);

  // New service instance (simulated Electron/MCP restart), same registry.
  const second = makeFakeBridge();
  const chat2 = createWorkHubCodexChat({ callBridge: second.callBridge, stateFile });
  const restoredView = chat2.getView(ROOT);
  assert.equal(restoredView.data.threadId, 'thread-1');
  assert.equal(restoredView.data.ownership.restoredFromRegistry, true);
  assert.equal(restoredView.data.ownership.verified, false);
  assert.equal(restoredView.data.messages.length, 0); // timeline is NOT persisted
  const probe = await chat2.probe(ROOT);
  assert.equal(probe.ok, true);
  const resumeCall = second.calls.find((c) => c.action === 'resume');
  assert.equal(resumeCall.thread_id, 'thread-1');
  assert.equal(resumeCall.session_id, 'sess-1');
  assert.equal(resumeCall.profile, 'chat');
  assert.equal(probe.data.ownership.verified, true);
  assert.equal(probe.data.resume.ok, true);
  const continued = await chat2.send(ROOT, { text: 'Vẫn là tôi đây' });
  assert.equal(continued.ok, true);
  assert.equal(second.calls.filter((c) => c.action === 'run').length, 0);
  assert.equal(second.calls.filter((c) => c.action === 'continue').length, 1);
  fs.rmSync(dir, { recursive: true, force: true });
});

test('(j2) OWNERSHIP_LOST is only declared when the resume itself really fails', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wh-chat-registry-'));
  const stateFile = path.join(dir, 'sessions.json');
  const first = makeFakeBridge();
  const chat1 = createWorkHubCodexChat({ callBridge: first.callBridge, stateFile });
  await chat1.send(ROOT, { text: 'Phiên sẽ mất thread' });

  const gone = makeFakeBridge({
    resume: async () => { throw new Error('Codex did not return the persisted lane thread. PERSISTENT_THREAD_NOT_FOUND'); },
  });
  const chat2 = createWorkHubCodexChat({ callBridge: gone.callBridge, stateFile });
  const probe = await chat2.probe(ROOT);
  assert.equal(probe.ok, false);
  assert.equal(probe.data.state, 'OWNERSHIP_LOST');
  assert.equal(probe.data.resume.ok, false);
  assert.match(probe.data.resume.note, /CODEX_HOME/);
  fs.rmSync(dir, { recursive: true, force: true });
});

test('(k) handoff with a linked RUN reads the directive, records the capsule and reads the lease from the ledger', async () => {
  const fake = makeFakeBridge();
  const tc = makeFakeTaskControl({
    get: async () => ({ capsule: { capsule_id: 'old-cap' }, send_replay_directive: { directive: 'REPLAY_SAFE', state: 'not_attempted', may_replay: true }, recommended_next_action: 'Resume from this capsule; the prompt was never dispatched.' }),
  });
  const chat = createWorkHubCodexChat({
    callBridge: fake.callBridge,
    callTool: tc.callTool,
    readLease: async (root, runId) => ({ leaseId: 'lease-1', owner: 'electron-panel', status: 'active', expiresAt: 1893456000 }),
  });
  await chat.send(ROOT, { text: 'Phân tích workspace rồi đề xuất việc', link: { runId: 'run-123', taskId: 'task-9' } });
  await chat.poll(ROOT); await chat.poll(ROOT); // turn completes
  const result = await chat.handoffToTask(ROOT, {});
  assert.equal(result.ok, true);
  assert.deepEqual(tc.calls.map((c) => `${c.args.action}:${c.args.handoff_action || ''}`), ['handoff:get', 'handoff:record']);
  const record = tc.calls.find((c) => c.args.handoff_action === 'record');
  assert.equal(record.args.run_id, 'run-123');
  assert.equal(record.args.payload.kind, 'codex-chat-handoff');
  assert.equal(record.args.payload.thread_ref.thread_id, 'thread-1');
  assert.equal(record.args.payload.chat_link.run_id, 'run-123');
  assert.deepEqual(record.args.payload.send_checkpoint, { state: 'not_attempted', message_id: '' });
  assert.equal(record.args.payload.recent_turns[0].text, 'Phân tích workspace rồi đề xuất việc');
  const handoff = result.data.handoff;
  assert.equal(handoff.status, 'recorded');
  assert.equal(handoff.capsuleId, 'cap-1');
  assert.equal(handoff.directive, 'REPLAY_SAFE');
  assert.equal(handoff.lease.owner, 'electron-panel');
  assert.equal(handoff.lease.expiresAt, 1893456000);
  // The link stays bidirectional: chat view keeps run/task ids.
  assert.deepEqual(result.data.link, { runId: 'run-123', taskId: 'task-9' });
});

test('(l) a RECONCILE_BEFORE_REPLAY or ALREADY_CONFIRMED directive blocks handoff — nothing is created or recorded', async () => {
  for (const directive of ['RECONCILE_BEFORE_REPLAY', 'ALREADY_CONFIRMED']) {
    const fake = makeFakeBridge();
    const tc = makeFakeTaskControl({
      get: async () => ({ capsule: { capsule_id: 'cap-x' }, send_replay_directive: { directive, state: 'possibly_sent' }, recommended_next_action: `Directive ${directive}: reconcile first.` }),
    });
    const chat = createWorkHubCodexChat({ callBridge: fake.callBridge, callTool: tc.callTool });
    await chat.send(ROOT, { text: 'Việc đang dở', link: { runId: 'run-77', taskId: 'task-7' } });
    await chat.poll(ROOT); await chat.poll(ROOT); // turn completes
    const result = await chat.handoffToTask(ROOT, {});
    assert.equal(result.ok, false, directive);
    assert.equal(result.error.code, 'HANDOFF_DIRECTIVE_BLOCKED');
    assert.match(result.error.message, new RegExp(directive));
    assert.equal(result.data.handoff.status, 'blocked');
    assert.equal(result.data.handoff.directive, directive);
    assert.match(result.data.handoff.recommendedNextAction, /reconcile first/);
    assert.equal(tc.calls.filter((c) => c.args.action === 'start').length, 0, directive);
    assert.equal(tc.calls.filter((c) => c.args.handoff_action === 'record').length, 0, directive);
  }
});

test('(m) handoff without a linked RUN creates the task through task_control start, then records the capsule for the new RUN', async () => {
  const fake = makeFakeBridge();
  const tc = makeFakeTaskControl();
  const chat = createWorkHubCodexChat({ callBridge: fake.callBridge, callTool: tc.callTool });
  await chat.send(ROOT, { text: 'Hãy lập kế hoạch sửa lỗi đăng nhập' });
  await chat.poll(ROOT); await chat.poll(ROOT); // turn completes
  const result = await chat.handoffToTask(ROOT, {});
  assert.equal(result.ok, true);
  const start = tc.calls.find((c) => c.args.action === 'start');
  assert.equal(start.args.objective, 'Hãy lập kế hoạch sửa lỗi đăng nhập');
  assert.deepEqual(result.data.link, { runId: 'run-new-1', taskId: 'task-new-1' });
  const record = tc.calls.find((c) => c.args.handoff_action === 'record');
  assert.equal(record.args.run_id, 'run-new-1');
  assert.equal(result.data.handoff.status, 'recorded');
  assert.equal(result.data.handoff.taskId, 'task-new-1');
});

test('(m2) handoff refuses an empty session and an unwired task channel without side effects', async () => {
  const fake = makeFakeBridge();
  const tc = makeFakeTaskControl();
  const noTool = createWorkHubCodexChat({ callBridge: fake.callBridge });
  await noTool.send(ROOT, { text: 'Có nội dung' });
  const unwired = await noTool.handoffToTask(ROOT, {});
  assert.equal(unwired.ok, false);
  assert.equal(unwired.error.code, 'CHAT_HANDOFF_NOT_WIRED');

  const empty = createWorkHubCodexChat({ callBridge: fake.callBridge, callTool: tc.callTool });
  const refused = await empty.handoffToTask(ROOT, {});
  assert.equal(refused.ok, false);
  assert.equal(refused.error.code, 'CHAT_HANDOFF_NO_CONTENT');
  assert.equal(tc.calls.length, 0);
});

// ---------------- W6 §8.3 regression: sticky startup FAILED ---------------

test('(o) a startup FAILED from a generic bridge error is cleared by the next successful probe; listHistory failure never writes session state', async () => {
  let booting = true;
  const fake = makeFakeBridge({
    status: async () => {
      if (booting) throw new Error('bridge boot exploded before the sidecar was ready');
      return { ok: true, connected: true, binary: 'C:\\Users\\Admin\\AppData\\Roaming\\npm\\codex.cmd', codex_version: '0.149.0', codex_home: 'C:\\Users\\Admin\\.codex', workspace: ROOT };
    },
    threads: async () => { throw new Error('MCP chưa sẵn sàng để chạy lệnh.'); },
  });
  const chat = createWorkHubCodexChat({ callBridge: fake.callBridge });
  // Auxiliary path first (as at app start): its failure must not touch
  // the session state at all — no FAILED, no recorded session error.
  const history = await chat.listHistory(ROOT);
  assert.equal(history.ok, false);
  assert.equal(history.error.code, 'MCP_UNAVAILABLE');
  assert.equal(chat.getView(ROOT).data.state, 'UNKNOWN');
  assert.equal(chat.getView(ROOT).data.error, null);
  // The startup probe is the path that writes FAILED (generic bridge
  // error -> BRIDGE_ERROR through fail()).
  const failedProbe = await chat.probe(ROOT);
  assert.equal(failedProbe.ok, false);
  assert.equal(failedProbe.data.state, 'FAILED');
  assert.equal(failedProbe.error.code, 'BRIDGE_ERROR');
  // Once the bridge is up, a successful probe must recover to READY and
  // clear the error, even though FAILED was the previous state.
  booting = false;
  const recovered = await chat.probe(ROOT);
  assert.equal(recovered.ok, true);
  assert.equal(recovered.data.state, 'READY');
  assert.equal(recovered.data.error, null);
  assert.equal(recovered.data.availability.codexVersion, '0.149.0');
  // A later history failure still leaves the recovered session alone.
  const historyAfter = await chat.listHistory(ROOT);
  assert.equal(historyAfter.ok, false);
  assert.equal(historyAfter.state, 'READY');
  assert.equal(chat.getView(ROOT).data.state, 'READY');
  assert.equal(chat.getView(ROOT).data.error, null);
});

test('(p) send after a startup FAILED is neither blocked nor poisoned — the new turn runs to COMPLETED', async () => {
  const fake = makeFakeBridge({
    status: async () => { throw new Error('bridge boot exploded before the sidecar was ready'); },
  });
  const chat = createWorkHubCodexChat({ callBridge: fake.callBridge });
  const failedProbe = await chat.probe(ROOT);
  assert.equal(failedProbe.data.state, 'FAILED');
  const sent = await chat.send(ROOT, { text: 'Chào sau khi khởi động lỗi' });
  assert.equal(sent.ok, true);
  assert.equal(sent.data.state, 'RUNNING');
  assert.equal(sent.data.error, null);
  await chat.poll(ROOT);
  const done = await chat.poll(ROOT);
  assert.equal(done.data.state, 'COMPLETED');
  assert.match(done.data.messages[1].text, /README\.md/);
});

test('(q) a successful probe does NOT erase a real failed turn (turnId present)', async () => {
  const fake = makeFakeBridge();
  fake.state.observeQueue = [
    { status: 'failed', terminal: true, agent_text: '', error: 'provider blew up mid-turn', events: [], next_cursor: 1 },
  ];
  const chat = createWorkHubCodexChat({ callBridge: fake.callBridge });
  await chat.send(ROOT, { text: 'Lượt sẽ lỗi thật' });
  const polled = await chat.poll(ROOT);
  assert.equal(polled.data.state, 'FAILED');
  assert.equal(polled.data.error.code, 'TURN_FAILED');
  const probe = await chat.probe(ROOT);
  assert.equal(probe.ok, true);
  assert.equal(probe.data.state, 'FAILED', 'the honest record of the failed turn survives a probe');
  assert.ok(probe.data.turnId, 'the failed turn is still the current turn');
});

test('(r) after a restart, a phantom active turn reported on send can be cleared by interrupt even though the session holds no turnId', async () => {
  // W7 fix-round cluster 2: registry restores thread + INTERRUPTED state
  // but no turnId. The first send is classified TURN_ALREADY_ACTIVE ->
  // RUNNING (the App Server still reports the pre-restart turn). The
  // panel's interrupt must not stop at a local NO_ACTIVE_TURN: it calls
  // the bridge with an empty turn_id so the bridge can interrupt the
  // latest turn it tracks for the thread, and then sending works again.
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wh-chat-registry-'));
  const stateFile = path.join(dir, 'sessions.json');
  const first = makeFakeBridge();
  const chat1 = createWorkHubCodexChat({ callBridge: first.callBridge, stateFile });
  await chat1.send(ROOT, { text: 'Phiên trước restart' });
  await chat1.poll(ROOT); await chat1.poll(ROOT); // turn completes

  let phantom = true;
  const second = makeFakeBridge({
    continue: async () => {
      if (phantom) throw new Error('The bridge-owned thread already has an active turn; observe or interrupt it before continuing. TURN_ALREADY_ACTIVE');
      return { ok: true, status: 'running', thread_id: 'thread-1', turn_id: 'turn-after-phantom', session_id: 'sess-1', creation_mode: 'continue', route: { profile: 'chat', model: 'gpt-5.6-terra', effort: 'medium' } };
    },
  });
  const chat2 = createWorkHubCodexChat({ callBridge: second.callBridge, stateFile });
  const probe = await chat2.probe(ROOT);
  assert.equal(probe.ok, true);
  assert.equal(probe.data.turnId, null); // registry never persisted one
  const blocked = await chat2.send(ROOT, { text: 'Lượt đầu sau restart' });
  assert.equal(blocked.ok, false);
  assert.equal(blocked.error.code, 'TURN_ALREADY_ACTIVE');
  assert.equal(blocked.data.state, 'RUNNING');
  assert.equal(blocked.data.turnId, null);
  const stopped = await chat2.interrupt(ROOT);
  assert.equal(stopped.ok, true);
  assert.equal(stopped.data.state, 'INTERRUPTED');
  assert.equal(stopped.data.error, null);
  const interruptCall = second.calls.find((c) => c.action === 'interrupt');
  assert.equal(interruptCall.thread_id, 'thread-1');
  assert.equal(interruptCall.turn_id, '');
  phantom = false;
  const resent = await chat2.send(ROOT, { text: 'Lượt đầu sau restart' });
  assert.equal(resent.ok, true);
  assert.equal(resent.data.turnId, 'turn-after-phantom');
  fs.rmSync(dir, { recursive: true, force: true });
});

test('(n) model/effort selector: listModels maps the bridge list and send forwards a validated override', async () => {
  const fake = makeFakeBridge();
  const chat = createWorkHubCodexChat({ callBridge: fake.callBridge });
  const models = await chat.listModels(ROOT);
  assert.equal(models.ok, true);
  assert.equal(models.data.models.length, 2);
  assert.equal(models.data.models[0].id, 'gpt-5.6-terra');
  assert.deepEqual(models.data.models[1].supportedEfforts, ['medium', 'high', 'xhigh']);
  assert.deepEqual(models.data.chatProfileDefault, { model: 'gpt-5.6-terra', effort: 'medium' });

  const sent = await chat.send(ROOT, { text: 'Dùng Sol nhé', model: 'gpt-5.6-sol', effort: 'high' });
  assert.equal(sent.ok, true);
  const runCall = fake.calls.find((c) => c.action === 'run');
  assert.equal(runCall.model, 'gpt-5.6-sol');
  assert.equal(runCall.effort, 'high');
  assert.deepEqual(sent.data.routeOverride, { model: 'gpt-5.6-sol', effort: 'high' });

  const bad = createWorkHubCodexChat({ callBridge: fake.callBridge });
  const invalid = await bad.send(ROOT, { text: 'Chào', effort: 'ludicrous' });
  assert.equal(invalid.ok, false);
  assert.equal(invalid.error.code, 'CHAT_EFFORT_INVALID');
});

// ---------------- P0 (audit P1): handoff asks the panel's current task --

async function linkedChat(tc, readRunStatus) {
  const fake = makeFakeBridge();
  const chat = createWorkHubCodexChat({
    callBridge: fake.callBridge, callTool: tc.callTool, readRunStatus,
  });
  await chat.send(ROOT, { text: 'Việc cần chuyển', link: { runId: 'run-A', taskId: 'task-A' } });
  await chat.poll(ROOT); await chat.poll(ROOT); // turn completes
  return chat;
}

test('(s) handoff with a stale chat link blocks on mismatch without any write, and each choice resolves it', async () => {
  const tc = makeFakeTaskControl();
  const chat = await linkedChat(tc);
  const current = { runId: 'run-B', taskId: 'task-B' };
  const blocked = await chat.handoffToTask(ROOT, { runId: current.runId, link: current });
  assert.equal(blocked.ok, false);
  assert.equal(blocked.error.code, 'HANDOFF_RUN_MISMATCH');
  assert.equal(blocked.error.linkRunId, 'run-A');
  assert.equal(blocked.error.currentRunId, 'run-B');
  assert.equal(blocked.data.handoffMismatch.linkRunId, 'run-A');
  assert.equal(blocked.data.handoffMismatch.currentRunId, 'run-B');
  assert.equal(blocked.data.handoffMismatch.hasPendingCapsule, false);
  assert.equal(tc.calls.length, 0, 'no get/record/start happens before the operator chooses');

  const bogus = await chat.handoffToTask(ROOT, { runId: current.runId, link: current, choice: 'bogus' });
  assert.equal(bogus.ok, false);
  assert.equal(bogus.error.code, 'HANDOFF_RUN_MISMATCH');
  assert.equal(tc.calls.length, 0);

  const intoCurrent = await chat.handoffToTask(ROOT, { runId: current.runId, link: current, choice: 'current' });
  assert.equal(intoCurrent.ok, true);
  assert.deepEqual(intoCurrent.data.link, { runId: 'run-B', taskId: 'task-B' });
  assert.equal(intoCurrent.data.handoffMismatch, null);
  const recordCurrent = tc.calls.find((c) => c.args.handoff_action === 'record');
  assert.equal(recordCurrent.args.run_id, 'run-B');

  const tcLink = makeFakeTaskControl();
  const chatLink = await linkedChat(tcLink);
  const intoLink = await chatLink.handoffToTask(ROOT, { runId: current.runId, link: current, choice: 'link' });
  assert.equal(intoLink.ok, true);
  assert.deepEqual(intoLink.data.link, { runId: 'run-A', taskId: 'task-A' });
  assert.equal(tcLink.calls.find((c) => c.args.handoff_action === 'record').args.run_id, 'run-A');

  const tcNew = makeFakeTaskControl();
  const chatNew = await linkedChat(tcNew);
  const intoNew = await chatNew.handoffToTask(ROOT, { runId: current.runId, link: current, choice: 'new' });
  assert.equal(intoNew.ok, true);
  assert.equal(tcNew.calls.find((c) => c.args.action === 'start').args.objective, 'Việc cần chuyển');
  assert.deepEqual(intoNew.data.link, { runId: 'run-new-1', taskId: 'task-new-1' });
});

test('(t) a pending capsule from an earlier handoff is flushed into the current RUN instead of creating a new task', async () => {
  const tc = makeFakeTaskControl({
    start: async (args) => ({ state: { task_id: 'task-p', objective: args.objective, status: 'active', orchestration: {} } }),
  });
  const fake = makeFakeBridge();
  const chat = createWorkHubCodexChat({ callBridge: fake.callBridge, callTool: tc.callTool });
  await chat.send(ROOT, { text: 'Việc chưa có RUN' });
  await chat.poll(ROOT); await chat.poll(ROOT);
  const first = await chat.handoffToTask(ROOT, {});
  assert.equal(first.ok, true);
  assert.equal(first.data.handoff.status, 'task_created');
  assert.ok(first.data.handoff.pendingCapsule, 'capsule waits in the registry');
  assert.deepEqual(first.data.link, { runId: null, taskId: 'task-p' });
  const pendingPayload = first.data.handoff.pendingCapsule;

  const callsBefore = tc.calls.length;
  const second = await chat.handoffToTask(ROOT, { runId: 'run-B', link: { runId: 'run-B', taskId: 'task-B' } });
  assert.equal(second.ok, true);
  assert.equal(second.data.handoff.status, 'recorded');
  assert.equal(second.data.handoff.pendingCapsule, null);
  assert.deepEqual(second.data.link, { runId: 'run-B', taskId: 'task-B' });
  const records = tc.calls.slice(callsBefore).filter((c) => c.args.handoff_action === 'record');
  assert.equal(records.length, 2, 'pending flush first, then the fresh capsule');
  assert.deepEqual(records[0].args.payload, pendingPayload);
  assert.equal(records[0].args.run_id, 'run-B');
  assert.equal(records[1].args.payload.chat_link.run_id, 'run-B');
  assert.equal(tc.calls.slice(callsBefore).filter((c) => c.args.action === 'start').length, 0, 'no duplicate task is created');
});

test('(u) handoff into an ended RUN is refused by default and proceeds only with explicit confirmation', async () => {
  const tc = makeFakeTaskControl();
  const chat = await linkedChat(tc, async () => 'completed');
  const refused = await chat.handoffToTask(ROOT, {});
  assert.equal(refused.ok, false);
  assert.equal(refused.error.code, 'HANDOFF_RUN_ENDED');
  assert.equal(refused.error.runId, 'run-A');
  assert.equal(refused.error.runStatus, 'completed');
  assert.equal(tc.calls.length, 0, 'no get/record happens before confirmation');

  const confirmed = await chat.handoffToTask(ROOT, { confirmEnded: true });
  assert.equal(confirmed.ok, true);
  assert.deepEqual(tc.calls.map((c) => `${c.args.action}:${c.args.handoff_action || ''}`), ['handoff:get', 'handoff:record']);
  assert.equal(tc.calls.find((c) => c.args.handoff_action === 'record').args.run_id, 'run-A');
});

test('(v) an unknown RUN status does not block handoff', async () => {
  const tc = makeFakeTaskControl();
  const chat = await linkedChat(tc, async () => null);
  const result = await chat.handoffToTask(ROOT, {});
  assert.equal(result.ok, true);
  assert.equal(result.data.handoff.status, 'recorded');
  assert.equal(tc.calls.find((c) => c.args.handoff_action === 'record').args.run_id, 'run-A');
});
