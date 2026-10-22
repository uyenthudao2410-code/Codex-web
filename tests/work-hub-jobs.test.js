'use strict';

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
async function settle() { for (let i = 0; i < 8; i += 1) await Promise.resolve(); }
function harness(overrides = {}) {
  const elements = new Map();
  for (const id of ['whJobView', 'whJobMeta', 'whJobKill', 'whJobPoll', 'whJobWrite', 'whJobInput']) {
    elements.set(`#${id}`, { textContent: '', value: '', disabled: false, handlers: {}, addEventListener(event, fn) { this.handlers[event] = fn; } });
  }
  const events = {}, timers = [], alerts = [], awake = [], controls = [], runs = [];
  const api = {
    workhubJobRun: async (payload) => { runs.push(payload); return { ok: true, data: { command_id: 'command-1', status: 'exited', exit_code: 0 } }; },
    workhubJobControl: async (payload) => { controls.push(payload); return { ok: true, data: { command_id: payload.commandId, status: 'running' } }; },
    workhubKeepAwake: async (on) => { awake.push(on); return { ok: true, data: { active: on } }; },
    ...overrides,
  };
  const context = vm.createContext({
    ui: { job: null },
    $: (selector) => elements.get(selector) || null,
    unwrap: (value) => value && typeof value === 'object' && 'ok' in value ? (value.ok ? value.data : null) : value,
    currentProject: () => 'E:/project', TextEncoder, TextDecoder,
    setTimeout: (callback) => { timers.push(callback); return timers.length; },
    window: { mcpAssistant: api, alert: (message) => alerts.push(message), addEventListener: (event, fn) => { events[event] = fn; } },
  });
  vm.runInContext(section('  // ---- A3/F19/F20:', '  // ---- A1: context package'), context);
  vm.runInContext(section("    $('#whJobKill')?.addEventListener", "    $('#whEditFile')?.addEventListener"), context);
  return { context, elements, events, timers, alerts, awake, controls, runs, api,
    click: (id) => elements.get(`#${id}`).handlers.click(),
    async close() { events.pagehide(); await settle(); },
  };
}
const payload = (stdout, total, status = 'running') => ({ command_id: 'command-1', status, stdout, stderr: '', output_retention: { stdout: { total_stream_bytes: total }, stderr: { total_stream_bytes: 0 } } });

test('Run blocks a second dispatch while starting and ignores a reply for a replaced selection', async () => {
  const first = deferred();
  let dispatches = 0;
  const h = harness({ workhubJobRun: () => { dispatches += 1; return first.promise; } });
  const pending = h.context.runRecipeAsJob({ name: 'Test', command: 'npm test' });
  await h.context.runRecipeAsJob({ name: 'Duplicate', command: 'npm test' });
  assert.equal(dispatches, 1);
  assert.equal(h.alerts.length, 1);
  const selected = { name: 'Another selection', status: 'exited', output: 'keep' };
  h.context.ui.job = selected;
  first.resolve({ ok: true, data: payload('old output', 10) });
  await pending;
  assert.equal(selected.output, 'keep');
  assert.equal(selected.commandId, undefined);
  await h.close();
});

test('Cursor output accumulates and initial named-consumer replay is not duplicated', async () => {
  const h = harness();
  const job = h.context.ui.job = { name: 'Test', status: 'running', commandId: 'command-1', output: '' };
  h.context.applyJobResult(job, payload('A\n', 2));
  h.context.applyJobResult(job, payload('A\nB\n', 4));
  h.context.applyJobResult(job, payload('B\n', 6));
  assert.equal(job.output, 'A\nB\nB\n', 'a new repeated line is preserved');
  h.context.applyJobResult(job, { ...payload('', 6, 'exited'), exit_code: 0 });
  assert.equal(job.output, 'A\nB\nB\n', 'empty terminal observation keeps output');
  assert.equal(job.exitCode, 0);
  await h.close();
});

test('Poll and write observations are serialized on the shared cursor', async () => {
  const first = deferred();
  const calls = [];
  const h = harness({ workhubJobControl: (request) => {
    calls.push(request.action);
    return calls.length === 1 ? first.promise : Promise.resolve({ ok: true, data: payload('second\n', 13) });
  } });
  const job = h.context.ui.job = { name: 'Test', status: 'running', commandId: 'command-1', output: '' };
  const poll = h.context.observeJob(job, 'poll');
  const write = h.context.observeJob(job, 'write', { chars: 'help\n' });
  await settle();
  assert.deepEqual(calls, ['poll']);
  first.resolve({ ok: true, data: payload('first\n', 6) });
  assert.equal(await poll, true);
  assert.equal(await write, true);
  assert.deepEqual(calls, ['poll', 'write']);
  assert.equal(job.output, 'first\nsecond\n');
  await h.close();
});

test('Stop stays requested until a terminal response confirms it', async () => {
  const h = harness();
  const job = h.context.ui.job = { name: 'Test', status: 'running', commandId: 'command-1', output: '' };
  await h.click('whJobKill');
  assert.equal(job.status, 'running');
  assert.equal(job.stopRequested, true);
  assert.match(h.elements.get('#whJobMeta').textContent, /chờ xác nhận/);
  h.api.workhubJobControl = async () => ({ ok: true, data: { command_id: 'command-1', status: 'terminated', exit_code: -1 } });
  await h.click('whJobPoll');
  assert.equal(job.status, 'terminated');
  assert.equal(job.stopRequested, false);
  await h.close();
  assert.equal(h.awake.at(-1), false);
});

test('Failed stdin ACK preserves the input and reports uncertain delivery without resending', async () => {
  let writes = 0;
  const h = harness({ workhubJobControl: async () => { writes += 1; throw new Error('connection lost'); } });
  const job = h.context.ui.job = { name: 'Test', status: 'running', commandId: 'command-1', output: '' };
  h.elements.get('#whJobInput').value = 'help\n';
  await h.click('whJobWrite');
  assert.equal(writes, 1);
  assert.equal(h.elements.get('#whJobInput').value, 'help\n');
  assert.equal(job.status, 'unknown');
  assert.match(job.inputDeliveryError, /Chưa xác nhận/);
  assert.equal(h.timers.length, 0);
  await h.close();
});

test('Observation failure releases keep-awake and leaves the Job available for reconciliation', async () => {
  const h = harness({ workhubJobControl: async () => ({ ok: false, error: 'runtime unavailable' }) });
  const job = h.context.ui.job = { name: 'Test', status: 'running', commandId: 'command-1', output: 'existing\n' };
  await h.context.setJobAwake(true);
  assert.equal(await h.context.observeJob(job, 'poll'), false);
  await settle();
  assert.equal(job.status, 'unknown');
  assert.equal(job.output, 'existing\n');
  assert.equal(h.elements.get('#whJobPoll').disabled, false);
  assert.equal(h.awake.at(-1), false);
  await h.close();
});

test('Pagehide releases keep-awake and late responses cannot overwrite the Job', async () => {
  const pending = deferred();
  const h = harness({ workhubJobControl: () => pending.promise });
  const job = h.context.ui.job = { name: 'Test', status: 'running', commandId: 'command-1', output: 'before' };
  await h.context.setJobAwake(true);
  const observation = h.context.observeJob(job, 'poll');
  await settle();
  await h.close();
  pending.resolve({ ok: true, data: payload('late', 4, 'exited') });
  assert.equal(await observation, false);
  assert.equal(job.output, 'before');
  assert.equal(h.awake.at(-1), false);
});

test('A canceled close without pagehide leaves Job observation active', async () => {
  const pending = deferred();
  const h = harness({ workhubJobControl: () => pending.promise });
  const job = h.context.ui.job = { name: 'Test', status: 'running', commandId: 'command-1', output: 'before' };
  await h.context.setJobAwake(true);
  const observation = h.context.observeJob(job, 'poll');
  await settle();
  // The editor can cancel beforeunload. Only the later pagehide event should
  // dispose the Job UI; no pagehide occurs when the user keeps the window open.
  h.events.beforeunload?.();
  pending.resolve({ ok: true, data: payload('after', 5) });
  assert.equal(await observation, true);
  assert.equal(job.output, 'beforeafter');
  assert.equal(h.awake.at(-1), true);
  await h.close();
});

test('An ambiguous dispatch timeout is unknown and does not permit accidental replay', async () => {
  let dispatches = 0;
  const h = harness({ workhubJobRun: async () => { dispatches += 1; return { ok: false, error: 'MCP response timeout' }; } });
  await h.context.runRecipeAsJob({ name: 'Test', command: 'npm test' });
  assert.equal(h.context.ui.job.status, 'unknown');
  await h.context.runRecipeAsJob({ name: 'Retry', command: 'npm test' });
  assert.equal(dispatches, 1);
  await h.close();
});

test('Job captures its project scope and a definite project rejection permits a corrected dispatch', async () => {
  const requests = [];
  const h = harness({ workhubJobRun: async (request) => {
    requests.push(request);
    return requests.length === 1
      ? { ok: false, error: 'Dự án đã thay đổi. Tải lại Work Hub trước khi thực hiện thao tác.' }
      : { ok: true, data: { command_id: 'corrected-command', status: 'exited', exit_code: 0 } };
  } });
  await h.context.runRecipeAsJob({ name: 'First', command: 'npm test', cwd: 'E:/project/subdir' });
  assert.equal(requests[0].expectedWorkspace, 'E:/project');
  assert.equal(requests[0].cwd, 'E:/project/subdir');
  assert.equal(h.context.ui.job.status, 'error');
  assert.match(h.elements.get('#whJobView').textContent, /Lệnh chưa được gửi/);
  assert.doesNotMatch(h.elements.get('#whJobView').textContent, /có thể vẫn chạy/);
  assert.equal(h.context.ui.job.workspace, 'E:/project');
  h.context.currentProject = () => 'E:/next-project';
  h.context.renderJob();
  assert.match(h.elements.get('#whJobMeta').textContent, /Dự án: E:\/project/);
  assert.doesNotMatch(h.elements.get('#whJobMeta').textContent, /next-project/);
  await h.context.runRecipeAsJob({ name: 'Corrected', command: 'npm test' });
  assert.equal(requests.length, 2);
  assert.equal(requests[1].expectedWorkspace, 'E:/next-project');
  assert.equal(requests[1].cwd, 'E:/next-project');
  assert.equal(h.context.ui.job.status, 'exited');
  await h.close();
});

test('A queued input is not sent after the preceding poll proves the command has exited', async () => {
  const first = deferred();
  const calls = [];
  const h = harness({ workhubJobControl: (request) => { calls.push(request.action); return first.promise; } });
  const job = h.context.ui.job = { name: 'Test', status: 'running', commandId: 'command-1', output: '' };
  h.elements.get('#whJobInput').value = 'help\n';
  const poll = h.context.observeJob(job, 'poll');
  const write = h.click('whJobWrite');
  await settle();
  first.resolve({ ok: true, data: { ...payload('done\n', 5, 'exited'), exit_code: 0 } });
  await poll;
  await write;
  assert.deepEqual(calls, ['poll']);
  assert.equal(job.status, 'exited');
  assert.equal(h.elements.get('#whJobInput').value, 'help\n');
  assert.match(job.inputDeliveryError, /kết thúc trước khi gửi/);
  await h.close();
});
