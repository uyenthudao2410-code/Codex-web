'use strict';

// P4 (L7/L11): honest post-restart display + thread<->RUN cross-links.
// Slices the real paintCodexChat + renderTaskBoard out of renderer/work-hub.js
// and runs them in vm with stubbed DOM/IPC — same pattern as
// tests/work-hub-render-scope.test.js. No Electron, no live bridge.

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'renderer/work-hub.js'), 'utf8');
function section(start, end) {
  const from = source.indexOf(start);
  const to = source.indexOf(end, from);
  assert.ok(from >= 0 && to > from, `Missing UI fragment: ${start}`);
  return source.slice(from, to);
}

function node(text = '') {
  return {
    text, children: [], disabled: false,
    append(...children) { this.children.push(...children); },
    replaceChildren(...children) { this.children = children; this.text = ''; },
    addEventListener() {},
    get textContent() { return this.text + this.children.map((child) => child.textContent).join(''); },
    set textContent(value) { this.text = String(value ?? ''); this.children = []; },
  };
}

function fixture({ taskPayload = null, history = [] } = {}) {
  const boxes = new Map();
  for (const id of ['whCodexChatState', 'whCodexChatLog', 'whCodexChatEvents', 'whCodexChatLink',
    'whCodexChatHandoffInfo', 'whCodexChatOwnership', 'whCodexChatSend', 'whCodexChatStop',
    'whCodexChatHandoff', 'whTaskBoard']) boxes.set(id, node());
  const workspace = 'E:/Projects/alpha';
  const context = vm.createContext({
    ui: { requests: {}, gen: 0, taskPayload, codexChatView: null },
    currentProject: () => workspace,
    $: (selector) => boxes.get(selector.slice(1)) || null,
    el: (tag, className, text) => node(text === undefined ? '' : text),
    smallButton: (label) => node(label),
    unwrap: (result) => (result && typeof result === 'object' && 'ok' in result)
      ? (result.ok ? result.data : null) : result,
    handoffCodexChatChoice: () => {},
    window: {
      mcpAssistant: { taskHistory: async () => history },
      navigate: () => {},
    },
  });
  vm.runInContext(section('  function requestScope(', '  function saveCurrentDraft('), context);
  vm.runInContext(section('  const CODEX_CHAT_STATE_LABELS = {', '  const codexChatUi'), context);
  vm.runInContext(section('  function paintCodexChat(', '  async function pollCodexChatTurn('), context);
  vm.runInContext(section('  async function renderTaskBoard(', '  async function renderWorkers('), context);
  return {
    context, boxes,
    text: (id) => boxes.get(id).textContent,
    paint: (view) => context.paintCodexChat(view),
    renderBoard: () => context.renderTaskBoard(),
    setTaskPayload: (payload) => { context.ui.taskPayload = payload; },
  };
}

const RESUME_NOTE = 'Resume phụ thuộc App Server còn giữ thread này trong CODEX_HOME; '
  + 'timeline panel không được khôi phục — chỉ quyền sở hữu thread và liên kết RUN quay lại.';

function chatView(overrides = {}) {
  return {
    state: 'READY',
    workspace: 'E:/Projects/alpha',
    availability: {},
    threadId: 'thread-abcdef123456',
    sessionId: null,
    turnId: null,
    route: null,
    routeOverride: null,
    profile: 'chat',
    title: null,
    createdAt: null,
    forkedFrom: null,
    handoff: null,
    handoffMismatch: null,
    resume: null,
    ownership: { verified: false, restoredFromRegistry: false, note: RESUME_NOTE },
    link: null,
    messages: [],
    events: [],
    error: null,
    updatedAt: null,
    ...overrides,
  };
}

test('(p4) restored session renders the ownership note; fresh session renders none', () => {
  const f = fixture();
  f.paint(chatView({ ownership: { verified: false, restoredFromRegistry: true, note: RESUME_NOTE } }));
  assert.match(f.text('whCodexChatOwnership'), /timeline panel không được khôi phục/);
  assert.match(f.text('whCodexChatOwnership'), /chỉ quyền sở hữu thread và liên kết RUN quay lại/);
  f.paint(chatView());
  assert.equal(f.text('whCodexChatOwnership'), '');
});

test('(p4) chat link warns when it differs from the panel current RUN, stays silent when equal', () => {
  const f = fixture();
  f.setTaskPayload({ state: { task_id: 'task-b', run_id: 'run-current', status: 'active' } });
  f.paint(chatView({ link: { runId: 'run-old', taskId: 'task-a' } }));
  assert.match(f.text('whCodexChatLink'), /Liên kết RUN run-old/);
  assert.match(f.text('whCodexChatLink'), /có thể cũ/);
  assert.match(f.text('whCodexChatLink'), /tác vụ hiện tại của panel là RUN run-current/);
  f.paint(chatView({ link: { runId: 'run-current', taskId: 'task-b' } }));
  assert.doesNotMatch(f.text('whCodexChatLink'), /có thể cũ/);
});

test('(p4) chat link warns when the current RUN comes from orchestration projection', () => {
  const f = fixture();
  f.setTaskPayload({ state: { task_id: 'task-b', orchestration: { run_id: 'run-proj' }, status: 'active' } });
  f.paint(chatView({ link: { runId: 'run-old', taskId: 'task-a' } }));
  assert.match(f.text('whCodexChatLink'), /RUN run-proj/);
});

test('(p4) taskboard marks the history row whose RUN matches the painted chat link', async () => {
  const f = fixture({
    history: [
      { run_id: 'run-old', task_id: 'task-a', objective: 'Old task', status: 'done' },
      { run_id: 'run-other', task_id: 'task-c', objective: 'Other task', status: 'done' },
    ],
  });
  f.paint(chatView({ link: { runId: 'run-old', taskId: 'task-a' } }));
  await f.renderBoard();
  const board = f.text('whTaskBoard');
  assert.match(board, /Old task/);
  assert.equal(board.match(/↔ chat thread/g)?.length, 1);
  assert.ok(board.indexOf('↔ chat thread') > board.indexOf('Old task'));
});

test('(p4) taskboard marks the current-task row when the chat link points at it', async () => {
  const f = fixture({
    taskPayload: { state: { task_id: 'task-b', run_id: 'run-current', objective: 'Current task', status: 'active' } },
    history: [{ run_id: 'run-old', task_id: 'task-a', objective: 'Old task', status: 'done' }],
  });
  f.paint(chatView({ link: { runId: 'run-current', taskId: 'task-b' } }));
  await f.renderBoard();
  const board = f.text('whTaskBoard');
  assert.match(board, /▶ Current task/);
  assert.match(board, /↔ chat thread thread-a/);
});

test('(p4) no taskboard marker when the linked RUN is not in the visible list', async () => {
  const f = fixture({
    history: [{ run_id: 'run-other', task_id: 'task-c', objective: 'Other task', status: 'done' }],
  });
  f.paint(chatView({ link: { runId: 'run-absent', taskId: 'task-x' } }));
  await f.renderBoard();
  assert.doesNotMatch(f.text('whTaskBoard'), /↔ chat thread/);
});

test('(p4) no taskboard marker when the painted chat view belongs to another workspace', async () => {
  const f = fixture({
    history: [{ run_id: 'run-old', task_id: 'task-a', objective: 'Old task', status: 'done' }],
  });
  f.paint(chatView({ workspace: 'E:/Projects/beta', link: { runId: 'run-old', taskId: 'task-a' } }));
  await f.renderBoard();
  assert.doesNotMatch(f.text('whTaskBoard'), /↔ chat thread/);
});
