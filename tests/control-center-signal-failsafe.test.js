const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

function runThemeBootstrap(search = '') {
  const context = {
    window: {},
    location: { search },
    document: { body: { dataset: {} }, documentElement: { dataset: {} } },
    URLSearchParams,
    Date,
    Promise
  };
  vm.runInNewContext(read('renderer/theme-bootstrap.js'), context, { filename: 'theme-bootstrap.js' });
  return context;
}

function loadManagerPreload(invokeImpl) {
  let exposed = null;
  const listeners = new Map();
  const timers = [];
  const ipcRenderer = {
    invoke: (channel, ...args) => Promise.resolve(invokeImpl(channel, ...args)),
    on: (channel, listener) => listeners.set(channel, listener),
    removeListener: (channel, listener) => {
      if (listeners.get(channel) === listener) listeners.delete(channel);
    }
  };
  const context = {
    require: (name) => {
      assert.equal(name, 'electron');
      return {
        contextBridge: { exposeInMainWorld: (name, api) => { assert.equal(name, 'mcpAssistant'); exposed = api; } },
        ipcRenderer
      };
    },
    setTimeout: (fn, ms) => {
      const timer = { fn, ms, cleared: false };
      timers.push(timer);
      return timer;
    },
    clearTimeout: (timer) => { if (timer) timer.cleared = true; },
    Date,
    JSON,
    Set,
    Promise
  };
  vm.runInNewContext(read('electron/preload.js'), context, { filename: 'preload.js' });
  return { api: exposed, listeners, timers };
}

test('packaged manager fails closed instead of inventing a healthy preview when preload IPC is missing', async () => {
  const context = runThemeBootstrap('');
  assert.ok(context.window.mcpAssistant, 'missing preload must install the disconnected bridge');
  const result = await context.window.mcpAssistant.snapshot();
  assert.equal(result.ok, true);
  assert.equal(result.data.status.runtimeRunning, false);
  assert.equal(result.data.status.tunnelRunning, false);
  assert.equal(result.data.status.fullyReady, false);
  assert.equal(result.data.status.ipcUnavailable, true);
  assert.equal(result.data.status.signalStale, true);
  const orchestration = await context.window.mcpAssistant.orchestration();
  assert.equal(orchestration.ok, false);
});

test('static preview mode remains explicit and opt-in', () => {
  const context = runThemeBootstrap('?preview=1&theme=light');
  assert.equal(context.window.mcpAssistant, undefined);
  assert.equal(context.document.body.dataset.theme, 'light');
});

test('manager preload expires a missing heartbeat instead of leaving runtime active forever', () => {
  const { api, timers } = loadManagerPreload(() => ({ ok: true, data: {} }));
  const events = [];
  const unsubscribe = api.onHeartbeat((payload) => events.push(payload));
  const watchdog = timers.at(-1);
  assert.equal(watchdog.ms, 15_000);
  watchdog.fn();
  assert.equal(events.length, 1);
  assert.equal(events[0].mcpRunning, null);
  assert.equal(events[0].nativeAlive, null);
  assert.equal(events[0].tunnelRunning, null);
  assert.equal(events[0].fullyReady, false);
  assert.equal(events[0].telemetryAvailable, false);
  assert.equal(events[0].failureKind, 'heartbeat_stale');
  assert.equal(events[0].signalStale, true);
  unsubscribe();
  assert.equal(watchdog.cleared, true);
});

test('manager preload downgrades a stale persisted running command when no fresh execution evidence exists', async () => {
  const old = '2000-01-01T00:00:00.000Z';
  const payload = {
    ok: true,
    data: {
      task: {
        status: 'waiting',
        updated_at: old,
        current_step: 'Waiting for model',
        current_command: { status: 'running', started_at: old, command: 'git push origin main' }
      },
      events: [],
      delegations: [],
      authority: { write: { status: 'released' } },
      resume_packet: { orchestration_state: 'EXECUTING' }
    }
  };
  const { api } = loadManagerPreload((channel) => {
    assert.equal(channel, 'panel:orchestration');
    return payload;
  });
  const result = await api.orchestration();
  assert.equal(result.data.task.current_command.status, 'stale');
  assert.equal(result.data.task.current_command.stale_reason, 'command_evidence_expired');
  assert.equal(result.data.resume_packet.orchestration_state, '');
  assert.equal(result.data.signal_freshness.status, 'stale');
  assert.equal(payload.data.task.current_command.status, 'running', 'sanitizer must not mutate the IPC source object');
});

test('manager preload preserves fresh running-command evidence', async () => {
  const now = new Date().toISOString();
  const payload = {
    ok: true,
    data: {
      task: {
        status: 'waiting',
        updated_at: now,
        current_command: { status: 'running', started_at: now, command: 'npm test' }
      },
      events: [], delegations: [], authority: { write: { status: 'released' } },
      resume_packet: { orchestration_state: 'EXECUTING' }
    }
  };
  const { api } = loadManagerPreload(() => payload);
  const result = await api.orchestration();
  assert.equal(result.data.task.current_command.status, 'running');
  assert.equal(result.data.resume_packet.orchestration_state, 'EXECUTING');
  assert.equal(result.data.signal_freshness, undefined);
});
