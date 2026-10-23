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
