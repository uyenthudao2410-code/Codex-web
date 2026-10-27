'use strict';

// P3 C3: per-workspace Work Hub slots. ui.taskPayload / ui.job stay the
// CURRENT folder's live pointers; ui.taskPayloadSlots / ui.jobSlots hold
// every folder's last-seen state, keyed by the canonical workspace key.
// refresh()'s changed branch saves the outgoing folder before the snapshot
// swap and restores the incoming folder after reset. These tests simulate
// that branch (save -> snapshot swap -> reset -> restore) because slicing
// the whole refresh() would drag in ~20 renderers.

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
function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
async function settle() { for (let i = 0; i < 10; i += 1) await Promise.resolve(); }

function harness(overrides = {}) {
  const elements = new Map();
  function makeEl() {
    return { textContent: '', value: '', hidden: false, disabled: false, dataset: {}, handlers: {},
      replaceChildren() { this.textContent = ''; },
      append() {}, appendChild() {}, focus() {}, click() {},
      addEventListener(event, fn) { this.handlers[event] = fn; },
      setAttribute() {}, removeAttribute() {} };
  }
  const $ = (selector) => {
    if (!elements.has(selector)) elements.set(selector, makeEl());
    return elements.get(selector);
  };
  const ui = { snapshot: { settings: { workspace: 'E:/A', canonicalWorkspace: '' } },
    taskPayload: null, job: null, taskPayloadSlots: new Map(), jobSlots: new Map(),
    boundProject: null, gen: 0, diffLoading: false, viewerRel: '', viewerContent: null,
    viewerHash: '', viewerEditable: false, savingFile: false };
  const S = { workspaceKeyOf: (value) => String(value ?? '').trim().replace(/\\/g, '/').replace(/\/+$/, '').toLowerCase() };
  const runs = [], controls = [], awake = [], alerts = [], statuses = [], stops = [];
  const api = {
    workhubJobRun: async (payload) => { runs.push(payload); return { ok: true, data: { command_id: 'command-1', status: 'exited', exit_code: 0, stdout: '', stderr: '', output_retention: { stdout: { total_stream_bytes: 0 }, stderr: { total_stream_bytes: 0 } } } }; },
    workhubJobControl: async (payload) => { controls.push(payload); return { ok: true, data: { command_id: payload.commandId, status: 'running', stdout: '', stderr: '', output_retention: { stdout: { total_stream_bytes: 0 }, stderr: { total_stream_bytes: 0 } } } }; },
    workhubKeepAwake: async (on) => { awake.push(on); return { ok: true, data: { active: on } }; },
    ...overrides,
  };
  const context = vm.createContext({
    ui, S, $,
    currentProject: () => ui.snapshot?.settings?.workspace || '',
    unwrap: (value) => value && typeof value === 'object' && 'ok' in value ? (value.ok ? value.data : null) : value,
    setTimeout: (callback) => { stops.push(callback); return stops.length; },
    setStatus: (message) => { statuses.push(message); },
    stopCodexChatPolling: () => { stops.push('chat'); },
    TextEncoder, TextDecoder,
    document: { body: { dataset: { page: 'workhub' } }, querySelectorAll: () => [], addEventListener: () => {} },
    window: { mcpAssistant: api, alert: (message) => alerts.push(message), addEventListener: () => {}, navigate: () => {} },
  });
  vm.runInContext(section('  function canonicalProjectKey(', '  function recentProjects('), context);
  vm.runInContext(section('  function resetProjectView(', '  function renderWorkspace('), context);
  vm.runInContext(section('  // ---- A3/F19/F20:', '  // ---- A1: context package'), context);
  vm.runInContext(section('  const fileDrafts', '  function resetProjectView('), context);
  function setWorkspace(raw) { ui.snapshot = { settings: { workspace: raw, canonicalWorkspace: '' } }; }
  // Exactly what refresh()'s changed branch does for slots, in order.
  function switchTo(raw) {
    context.saveWorkHubSlots();
    setWorkspace(raw);
    context.resetProjectView();
    context.restoreWorkHubSlots();
  }
  return { context, elements, $, ui, runs, controls, awake, alerts, statuses, setWorkspace, switchTo,
    meta: () => elements.get('#whJobMeta').textContent };
}

test('job in A survives a switch to B and back with its original cwd and running state', async () => {
  const h = harness({ workhubJobRun: async (payload) => { h.runs.push(payload); return { ok: true, data: { command_id: 'command-1', status: 'running', stdout: '', stderr: '', output_retention: { stdout: { total_stream_bytes: 0 }, stderr: { total_stream_bytes: 0 } } } }; } });
  await h.context.runRecipeAsJob({ name: 'Job A', command: 'npm test' });
  const jobA = h.ui.job;
  assert.ok(jobA);
  assert.equal(jobA.workspace, 'E:/A');
  assert.equal(jobA.status, 'running');
  assert.equal(jobA.commandId, 'command-1');
  assert.equal(h.runs[0].cwd, 'E:/A');
  h.switchTo('E:/B');
  assert.equal(h.ui.job, null);
  assert.equal(h.meta(), 'Chưa chạy lệnh nào trong phiên này.');
  h.switchTo('E:/A');
  assert.equal(h.ui.job, jobA, 'same job object, not a copy');
  assert.equal(h.ui.job.workspace, 'E:/A', 'start-time folder preserved, never rewritten to the current view');
  assert.equal(h.ui.job.status, 'running');
  assert.match(h.meta(), /Job A/);
  assert.match(h.meta(), /E:\/A/);
  h.switchTo('E:/B');
  h.switchTo('E:/A');
  assert.equal(h.ui.jobSlots.size, 2, 'one entry per folder, no duplicates from repeated switches');
  assert.equal(h.ui.jobSlots.get('e:/a'), jobA);
});

test('jobs in A and B are independent; a running job in A does not block starting one in B', async () => {
  const h = harness({ workhubJobRun: async (payload) => { h.runs.push(payload); return { ok: true, data: { command_id: 'command-1', status: 'running', stdout: '', stderr: '', output_retention: { stdout: { total_stream_bytes: 0 }, stderr: { total_stream_bytes: 0 } } } }; } });
  await h.context.runRecipeAsJob({ name: 'Job A', command: 'npm test' });
  const jobA = h.ui.job;
  h.switchTo('E:/B');
  await h.context.runRecipeAsJob({ name: 'Job B', command: 'npm run build', cwd: 'E:/B/custom' });
  const jobB = h.ui.job;
  assert.equal(h.runs.length, 2, 'second dispatch was not blocked by the first folder\'s running job');
  assert.equal(h.alerts.length, 0);
  assert.equal(h.runs[1].cwd, 'E:/B/custom', 'start-time cwd kept, not rewritten');
  assert.match(h.meta(), /Job B/);
  assert.doesNotMatch(h.meta(), /Job A/);
  h.switchTo('E:/A');
  assert.equal(h.ui.job, jobA);
  assert.match(h.meta(), /Job A/);
  assert.doesNotMatch(h.meta(), /Job B/);
  h.switchTo('E:/B');
  assert.equal(h.ui.job, jobB);
});

test('a folder switch mid-dispatch records the outcome on the slot; return restores it and resumes polling', async () => {
  const first = deferred();
  const h = harness({ workhubJobRun: () => first.promise });
  const pending = h.context.runRecipeAsJob({ name: 'Job A', command: 'npm test' });
  const jobA = h.ui.job;
  assert.equal(jobA.status, 'starting');
  h.switchTo('E:/B');
  first.resolve({ ok: true, data: { command_id: 'command-1', status: 'running', stdout: '', stderr: '', output_retention: { stdout: { total_stream_bytes: 0 }, stderr: { total_stream_bytes: 0 } } } });
  await pending;
  assert.equal(jobA.commandId, 'command-1', 'outcome recorded on the slot despite the switch');
  assert.equal(jobA.status, 'running');
  assert.equal(h.ui.job, null, 'background folder\'s view is not painted while viewing B');
  h.switchTo('E:/A');
  await settle();
  assert.equal(h.ui.job, jobA);
  assert.equal(jobA.polling, true, 'poll loop resumed on return');
  assert.ok(h.awake.includes(true), 'keep-awake re-armed for the resumed job');
});

test('resetProjectView does not wipe the slot maps', () => {
  const h = harness();
  const jobA = { name: 'Job A', workspace: 'E:/A', status: 'exited', commandId: 'command-1' };
  h.ui.job = jobA;
  h.ui.taskPayload = { state: { task_id: 'task-a' } };
  h.context.saveWorkHubSlots();
  h.context.resetProjectView();
  assert.equal(h.ui.jobSlots.get('e:/a'), jobA);
  assert.equal(h.ui.taskPayloadSlots.get('e:/a').state.task_id, 'task-a');
  h.context.restoreWorkHubSlots();
  assert.equal(h.ui.job, jobA);
});

test('task payload slots are per folder and restore by identity', () => {
  const h = harness();
  const payloadA = { state: { task_id: 'task-a' } };
  const payloadB = { state: { task_id: 'task-b' } };
  h.ui.taskPayload = payloadA;
  h.switchTo('E:/B');
  assert.equal(h.ui.taskPayload, null);
  h.ui.taskPayload = payloadB;
  h.switchTo('E:/A');
  assert.equal(h.ui.taskPayload, payloadA);
  h.switchTo('E:/B');
  assert.equal(h.ui.taskPayload, payloadB);
});

test('canLeaveFileEdit still fires per folder and a background running job does not block the other folder', async () => {
  const h = harness({ workhubJobRun: async (payload) => { h.runs.push(payload); return { ok: true, data: { command_id: 'command-1', status: 'running', stdout: '', stderr: '', output_retention: { stdout: { total_stream_bytes: 0 }, stderr: { total_stream_bytes: 0 } } } }; } });
  await h.context.runRecipeAsJob({ name: 'Job A', command: 'npm test' });
  assert.equal(h.ui.job.status, 'running');
  const editor = h.$('#whEditor');
  editor.hidden = false;
  h.ui.viewerRel = 'f.txt';
  h.ui.viewerContent = 'original';
  editor.value = 'edited';
  assert.equal(h.context.canLeaveFileEdit(), false, 'unsaved edit blocks leaving');
  editor.value = 'original';
  assert.equal(h.context.canLeaveFileEdit(), true, 'clean editor passes');
  editor.value = 'edited';
  h.context.rememberFileEdit();
  h.setWorkspace('E:/B');
  editor.value = 'original';
  assert.equal(h.context.canLeaveFileEdit(), true, 'the other folder\'s view is not blocked by A\'s edit');
});

test('refresh changed branch wires save before reset and restore after reset (source)', () => {
  const branch = source.slice(source.indexOf('if (changed && ui.boundProject)'), source.indexOf('restoreDraft({ force: true });'));
  assert.ok(branch.includes('saveWorkHubSlots()'), 'save runs with the outgoing folder\'s snapshot still active');
  assert.ok(branch.indexOf('saveWorkHubSlots()') < branch.indexOf('ui.snapshot = snapshot'), 'save precedes the snapshot swap');
  assert.ok(branch.indexOf('resetProjectView()') < branch.indexOf('restoreWorkHubSlots()'), 'restore runs after reset');
});

test('runRecipeAsJob gates only the view refresh on currency, not outcome recording (source)', () => {
  const fn = source.slice(source.indexOf('async function runRecipeAsJob'), source.indexOf('async function pollJobLoop'));
  assert.ok(!fn.includes('ui.job !== job || jobUiUnloaded'), 'no early return drops a switched-away dispatch');
  assert.ok(fn.includes('if (jobUiUnloaded) return;'), 'pagehide still aborts');
  assert.ok(fn.includes('if (ui.job !== job) return;'), 'view refresh still gated on the current job');
});
