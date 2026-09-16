const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function mainHandoff({ role = 'direct_legacy', epoch = {}, trusted = true } = {}) {
  const source = fs.readFileSync(path.join(__dirname, '..', 'electron', 'main.js'), 'utf8');
  const start = source.indexOf("secureHandle('runtime:handoff-central-executor'");
  const end = source.indexOf("secureHandle('runtime:start'", start);
  assert.ok(start >= 0 && end > start);
  const calls = [];
  const snapshot = { settings: { executionRole: role }, status: {}, recoveryHost: { activation_epoch: epoch } };
  let handler;
  vm.runInNewContext(source.slice(start, end), {
    secureHandle: (_name, value) => { handler = value; },
    invokeSafely: (action) => action(),
    assertManagerIpc: () => { if (!trusted) throw Object.assign(new Error('Manager required'), { code: 'MANAGER_REQUIRED' }); },
    settings: { load: () => ({ executionRole: role }) },
    orchestrator: {
      snapshot: async () => snapshot,
      restart: async (options) => { calls.push(JSON.parse(JSON.stringify(options))); return { accepted: true, state: 'HANDOFF' }; }
    },
    fullCleanRestartOptions: () => { throw new Error('Code checkpoint must not be consulted for operator migration'); }
  });
  return { handler, calls, snapshot };
}

test('manager handoff works without an accepted-code closure and forwards only the fixed migration intent', async () => {
  const fixture = mainHandoff();
  const result = await fixture.handler({}, { sourceCheckpoint: 'untrusted', executionRole: 'wrong', tunnelId: 'ignored' });
  assert.equal(result.state, 'HANDOFF');
  assert.deepEqual(fixture.calls, [{
    reason: 'operator_central_executor_handoff',
    executionRole: 'central_executor',
    mode: 'full_clean_execution_role_handoff'
  }]);
});

test('role handoff refuses non-manager callers before runtime mutation', async () => {
  const fixture = mainHandoff({ trusted: false });
  await assert.rejects(fixture.handler({}), { code: 'MANAGER_REQUIRED' });
  assert.equal(fixture.calls.length, 0);
});

test('repeated central handoff does not replace an active verification or healthy READY epoch', async () => {
  for (const epoch of [
    ...['STARTING', 'VERIFYING', 'READY_COMMITTED', 'READY'].map((state) => ({ state, stale: false })),
    { state: 'UPDATE_INCOMPLETE', epoch_state: 'VERIFYING', expires_at_unix_ms: Date.now() + 60_000 }
  ]) {
    const fixture = mainHandoff({ role: 'central_executor', epoch });
    assert.equal(await fixture.handler({}), fixture.snapshot);
    assert.equal(fixture.calls.length, 0);
  }
});

test('central role can explicitly retry a failed or expired onboarding epoch', async () => {
  for (const epoch of [{ state: 'FAILED' }, { state: 'VERIFYING', stale: true }, { state: 'UPDATE_INCOMPLETE' },
    { state: 'UPDATE_INCOMPLETE', epoch_state: 'VERIFYING', expires_at_unix_ms: Date.now() - 1 }]) {
    const fixture = mainHandoff({ role: 'central_executor', epoch });
    assert.equal((await fixture.handler({})).state, 'HANDOFF');
    assert.equal(fixture.calls.length, 1);
    assert.equal(fixture.calls[0].mode, 'full_clean_execution_role_handoff');
  }
});

function rendererHandoff(reply) {
  const source = fs.readFileSync(path.join(__dirname, '..', 'renderer', 'app.js'), 'utf8');
  const start = source.indexOf('async function handoffCentralExecutor()');
  const end = source.indexOf('\nfunction updateProgress(', start);
  assert.ok(start >= 0 && end > start);
  const events = [];
  const context = {
    api: { handoffCentralExecutor: async () => reply },
    unwrap: (value) => { if (!value.ok) throw new Error(value.error); return value.data; },
    setBusy: (value) => events.push(['busy', value]),
    renderSnapshot: (value) => events.push(['render', value]),
    toast: (...args) => events.push(['toast', ...args]),
    refreshSnapshot: async () => events.push(['refresh'])
  };
  vm.createContext(context);
  vm.runInContext(source.slice(start, end), context);
  return { run: () => context.handoffCentralExecutor(), events };
}

test('renderer treats HANDOFF as pending, not as a snapshot or connected success', async () => {
  const fixture = rendererHandoff({ ok: true, data: { accepted: true, state: 'HANDOFF', fully_ready: false } });
  await fixture.run();
  assert.equal(fixture.events.some(([kind]) => kind === 'render'), false);
  assert.ok(fixture.events.some(([kind, title]) => kind === 'toast' && title === 'Đã nhận yêu cầu chuyển sang executor Ubuntu'));
  assert.ok(fixture.events.some(([kind, , message]) => kind === 'toast' && message.includes('chưa xác nhận kết nối Ubuntu')));
  assert.deepEqual(fixture.events.slice(-2), [['busy', false], ['refresh']]);
});

test('renderer keeps errors visible and refreshes state on rejected migration', async () => {
  const fixture = rendererHandoff({ ok: false, error: 'RUNTIME_BUSY' });
  await assert.rejects(fixture.run(), /RUNTIME_BUSY/);
  assert.ok(fixture.events.some(([kind, , message, type]) => kind === 'toast' && type === 'error' && message === 'RUNTIME_BUSY'));
  assert.deepEqual(fixture.events.slice(-2), [['busy', false], ['refresh']]);
});
