'use strict';

// P5 (L10/L12): task/RUN binding on review results and goal preps.
// Slices the real panelTaskLink + renderGitReviewMeta + renderGoal out of
// renderer/work-hub.js and runs them in vm with stubbed DOM — same pattern
// as tests/work-hub-p4-display.test.js. No Electron, no live bridge.

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
    text, children: [],
    append(...children) { this.children.push(...children); },
    replaceChildren(...children) { this.children = children; this.text = ''; },
    addEventListener() {},
    get textContent() { return this.text + this.children.map((child) => child.textContent).join(''); },
    set textContent(value) { this.text = String(value ?? ''); this.children = []; },
  };
}

function fixture() {
  const boxes = new Map();
  for (const id of ['whGitReviewMeta', 'whGoalState']) boxes.set(id, node());
  let prep = null;
  const context = vm.createContext({
    ui: { taskPayload: null, gitReview: null, gitReviewHead: '', gitHead: '', gitReviewBinding: null },
    currentProject: () => 'E:/Projects/alpha',
    $: (selector) => boxes.get(selector.slice(1)) || null,
    store: { goalPrepFor: () => prep },
  });
  vm.runInContext(section('  function panelTaskLink(', '  function gitReviewIsStale('), context);
  vm.runInContext(section('  function gitReviewIsStale(', '  function renderGitReviewResults('), context);
  vm.runInContext(section('  function renderGoal(', '  function renderImports('), context);
  return {
    context, boxes,
    text: (id) => boxes.get(id).textContent,
    setTaskPayload: (payload) => { context.ui.taskPayload = payload; },
    setPrep: (value) => { prep = value; },
    setReview: (review, binding) => {
      context.ui.gitReview = review;
      context.ui.gitReviewBinding = binding === undefined ? null : binding;
    },
    link: () => context.panelTaskLink(),
    meta: () => context.renderGitReviewMeta(),
    goal: () => context.renderGoal(),
  };
}

const REVIEW = {
  from: 'HEAD~1', to: 'HEAD', fromHash: 'aaa', toHash: 'bbb',
  commits: [], files: [], subsystems: [], totals: { commits: 0, files: 0, additions: 0, deletions: 0, renames: 0 },
  fingerprint: '0123456789abcdef', truncated: false,
};

test('(p5) panelTaskLink reads the current panel task, never invents one', () => {
  const f = fixture();
  assert.equal(f.link(), null);
  f.setTaskPayload({ state: { orchestration: { run_id: 'run-9' }, task_id: 'task-1' } });
  const bound = f.link();
  assert.equal(bound.runId, 'run-9');
  assert.equal(bound.taskId, 'task-1');
  f.setTaskPayload({ data: { state: { run_id: 'run-7' } } });
  const runOnly = f.link();
  assert.equal(runOnly.runId, 'run-7');
  assert.equal(runOnly.taskId, '');
  f.setTaskPayload({ state: { task_id: 'task-1' } });
  assert.equal(f.link(), null);
});

test('(p5) review meta shows the binding captured at review time, or says unbound', () => {
  const f = fixture();
  f.setReview(REVIEW, { runId: 'run-9', taskId: 'task-1' });
  f.meta();
  assert.match(f.text('whGitReviewMeta'), /Gắn task task-1 · RUN run-9/);
  f.setReview(REVIEW, { runId: 'run-9', taskId: '' });
  f.meta();
  assert.match(f.text('whGitReviewMeta'), /Gắn RUN run-9/);
  assert.doesNotMatch(f.text('whGitReviewMeta'), /Gắn task/);
  f.setReview(REVIEW, null);
  f.meta();
  assert.match(f.text('whGitReviewMeta'), /Không gắn task \(lúc rà soát chưa có RUN hiện tại\)/);
});

test('(p5) goal display shows the binding, and which task the prep became when the panel moved on', () => {
  const f = fixture();
  f.goal();
  assert.match(f.text('whGoalState'), /Chưa chuẩn bị mục tiêu/);
  f.setPrep({ criteria: 'đạt chuẩn', maxTurns: 3, maxMinutes: 30, taskId: '', runId: '' });
  f.goal();
  assert.match(f.text('whGoalState'), /Không gắn task \(lúc lưu chưa có RUN hiện tại\)/);
  f.setPrep({ criteria: 'đạt chuẩn', maxTurns: 3, maxMinutes: 30, taskId: 'task-1', runId: 'run-9' });
  f.setTaskPayload({ state: { orchestration: { run_id: 'run-9' }, task_id: 'task-1' } });
  f.goal();
  assert.match(f.text('whGoalState'), /Gắn task task-1 · RUN run-9/);
  assert.doesNotMatch(f.text('whGoalState'), /đã thành/);
  f.setTaskPayload({ state: { orchestration: { run_id: 'run-12' }, task_id: 'task-2' } });
  f.goal();
  assert.match(f.text('whGoalState'), /đã thành task task-1/);
  f.setPrep({ criteria: 'đạt chuẩn', maxTurns: 3, maxMinutes: 30, taskId: '', runId: 'run-9' });
  f.goal();
  assert.match(f.text('whGoalState'), /đã thành RUN run-9/);
});
