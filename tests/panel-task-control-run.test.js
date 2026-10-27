const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const repoRoot = path.resolve(__dirname, '..');
const mainSource = fs.readFileSync(path.join(repoRoot, 'electron', 'main.js'), 'utf8');
const preloadSource = fs.readFileSync(path.join(repoRoot, 'electron', 'preload.js'), 'utf8');
const panelPreloadSource = fs.readFileSync(path.join(repoRoot, 'electron', 'panelPreload.js'), 'utf8');
const appSource = fs.readFileSync(path.join(repoRoot, 'renderer', 'app.js'), 'utf8');
const panelSource = fs.readFileSync(path.join(repoRoot, 'renderer', 'panel.js'), 'utf8');

function panelTaskControlHarness() {
  const start = mainSource.indexOf('async function panelTaskControl');
  const end = mainSource.indexOf('function executionControlCenterProgressObservation', start);
  assert.ok(start >= 0 && end > start, 'panelTaskControl must remain discoverable');
  const calls = [];
  const context = vm.createContext({
    settings: { load: () => ({ mcpPort: 18766 }) },
    secrets: { get: () => 'test-token' },
    app: { getVersion: () => 'test' },
    httpRequestJson: async (options) => {
      calls.push(options);
      return context.__nextResponse;
    },
    console,
  });
  context.__nextResponse = { result: { ok: true } };
  vm.runInContext(mainSource.slice(start, end), context, { filename: 'electron/panel-task-control.js' });
  return {
    calls,
    setResponse(response) { context.__nextResponse = response; },
    control(action, runId) {
      const runArg = runId === undefined ? 'undefined' : JSON.stringify(runId);
      return vm.runInContext(`panelTaskControl(${JSON.stringify(action)}, ${runArg})`, context);
    },
  };
}

test('panel task control forwards the displayed run id to task_control', async () => {
  const harness = panelTaskControlHarness();
  await harness.control('pause', 'run-abc');
  assert.equal(harness.calls.length, 1);
  const options = harness.calls[0];
  assert.equal(options.port, 18766);
  assert.equal(options.token, 'test-token');
  assert.equal(options.body.params.name, 'task_control');
  assert.deepEqual(options.body.params.arguments, { action: 'pause', run_id: 'run-abc' });
});

test('panel task control omits run_id when no run is displayed', async () => {
  const harness = panelTaskControlHarness();
  await harness.control('stop', undefined);
  assert.deepEqual(harness.calls[0].body.params.arguments, { action: 'stop' });
  await harness.control('stop', '   ');
  assert.deepEqual(harness.calls[1].body.params.arguments, { action: 'stop' });
});

test('panel task control rejects an unknown action before any MCP call', async () => {
  const harness = panelTaskControlHarness();
  await assert.rejects(harness.control('explode', 'run-abc'), (err) => Boolean(err && err.message) && harness.calls.length === 0);
  assert.equal(harness.calls.length, 0);
});

test('panel task control surfaces an MCP task_control error', async () => {
  const harness = panelTaskControlHarness();
  harness.setResponse({ result: { isError: true, content: [{ text: 'MCP says no' }] } });
  await assert.rejects(harness.control('pause', 'run-abc'), /MCP says no/);
});

test('main task-state and panel task-control handlers forward the run id', () => {
  const start = mainSource.indexOf("secureHandle('task-state:read'");
  const end = mainSource.indexOf("secureHandle('performance:read'", start);
  assert.ok(start >= 0 && end > start);
  const handlers = mainSource.slice(start, end);
  for (const action of ['clear', 'pause', 'resume', 'stop']) {
    assert.ok(
      handlers.includes(`panelTaskControl('${action}', runId)`),
      `task-state:${action} must forward runId`,
    );
  }
  assert.ok(
    mainSource.includes("panelTaskControl(String(action || ''), runId)"),
    'panel:task-control must forward runId',
  );
});

function preloadApi(source, filename) {
  let exposed = null;
  const invokeCalls = [];
  const electronStub = {
    contextBridge: { exposeInMainWorld: (_name, api) => { exposed = api; } },
    ipcRenderer: {
      invoke: async (...args) => { invokeCalls.push(args); return { ok: true }; },
      on: () => {},
      removeListener: () => {},
    },
  };
  const context = vm.createContext({
    require: (name) => {
      if (name === 'electron') return electronStub;
      throw new Error(`unexpected require: ${name}`);
    },
    setTimeout: (...args) => setTimeout(...args),
    clearTimeout: (...args) => clearTimeout(...args),
    Date,
  });
  vm.runInContext(source, context, { filename });
  assert.ok(exposed, 'preload must expose an api object');
  return { api: exposed, invokeCalls };
}

test('manager preload forwards the run id on every task control', async () => {
  const { api, invokeCalls } = preloadApi(preloadSource, 'electron/preload.js');
  await api.pauseTask('run-1');
  await api.resumeTask('run-1');
  await api.stopTask('run-1');
  await api.clearTaskState('run-1');
  assert.deepEqual(invokeCalls, [
    ['task-state:pause', 'run-1'],
    ['task-state:resume', 'run-1'],
    ['task-state:stop', 'run-1'],
    ['task-state:clear', 'run-1'],
  ]);
  await api.stopTask();
  assert.deepEqual(invokeCalls[invokeCalls.length - 1], ['task-state:stop', undefined]);
});

test('panel preload forwards the run id on every task control', async () => {
  const { api, invokeCalls } = preloadApi(panelPreloadSource, 'electron/panelPreload.js');
  await api.pauseTask('run-9');
  await api.resumeTask('run-9');
  await api.stopTask('run-9');
  assert.deepEqual(invokeCalls, [
    ['panel:task-control', 'pause', 'run-9'],
    ['panel:task-control', 'resume', 'run-9'],
    ['panel:task-control', 'stop', 'run-9'],
  ]);
  await api.pauseTask();
  assert.deepEqual(invokeCalls[invokeCalls.length - 1], ['panel:task-control', 'pause', undefined]);
});

test('manager task view records the displayed run and passes it to every control', () => {
  assert.ok(
    appSource.includes("state.displayedTaskRunId = String(task?.orchestration?.run_id || '').trim() || null;"),
    'renderTaskState must record the displayed run id',
  );
  for (const call of [
    'api.pauseTask(state.displayedTaskRunId)',
    'api.resumeTask(state.displayedTaskRunId)',
    'api.stopTask(state.displayedTaskRunId)',
  ]) {
    assert.ok(appSource.includes(call), `manager button must call ${call}`);
  }
  assert.ok(
    appSource.includes('api.clearTaskState(state.displayedTaskRunId)); renderTaskState(null)'),
    'clear must pass the displayed run before clearing the view',
  );
});

test('panel task actions pass the displayed orchestration run', () => {
  for (const call of [
    'api.pauseTask(lastOrchestration?.run?.run_id)',
    'api.resumeTask(lastOrchestration?.run?.run_id)',
    'api.stopTask(lastOrchestration?.run?.run_id)',
  ]) {
    assert.ok(panelSource.includes(call), `panel taskAction must call ${call}`);
  }
});
