const test = require('node:test');
const assert = require('node:assert/strict');
const { RuntimeOrchestrator } = require('../electron/services/runtimeOrchestrator');
const { FullCleanActivation } = require('../electron/services/fullCleanActivation');
const { NativeService } = require('../electron/services/nativeService');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

function fixture(prepare = async () => ({ safe: true })) {
  const calls = [];
  const runtime = Object.create(RuntimeOrchestrator.prototype);
  Object.assign(runtime, {
    busy: false,
    native: { status: async () => ({ pid: 12345, process_start_token: '170000000000000000' }),
      stop: async (options) => {
        if (options.expectedIdentity) assert.equal(options.expectedIdentity.pid, 12345);
        calls.push('native-stop');
      } },
    tunnel: { stop: async () => { calls.push('tunnel-stop'); } },
    fullCleanActivation: { prepareOwnedExecutorStop: async (operation) => {
      calls.push(['cleanup', operation]);
      return prepare(operation);
    } },
    setManualStop: () => {}, progress: () => {}, invalidateSnapshot: () => {},
    snapshot: async () => ({ stopped: true })
  });
  return { runtime, calls };
}

test('healthy operator stop confirms owned executor cleanup before any process stops', async () => {
  const f = fixture();
  assert.deepEqual(await f.runtime.stop(), { stopped: true });
  assert.match(f.calls[0][1], /^operation_stop_[a-f0-9]{32}$/);
  assert.deepEqual(f.calls.slice(1), ['tunnel-stop', 'native-stop']);
  assert.equal(f.runtime.executorStopOperationId, '');
  assert.equal(f.runtime.busy, false);
});

test('lost or failed executor cleanup preserves owner and retries the same original operation', async () => {
  const failure = Object.assign(new Error('unknown cleanup'), { code: 'SANDBOX_TEARDOWN_UNCONFIRMED' });
  const f = fixture(async () => { throw failure; });
  await assert.rejects(f.runtime.stop(), { code: failure.code });
  await assert.rejects(f.runtime.stop(), { code: failure.code });
  assert.equal(f.calls.length, 2);
  assert.equal(f.calls[0][1], f.calls[1][1]);
  assert.equal(f.runtime.busy, false);
});

test('full-clean stop reuses its already confirmed fence without issuing another cleanup', async () => {
  const f = fixture(async () => { throw new Error('must not prepare twice'); });
  await f.runtime.stop({ manual: false, fullClean: true });
  assert.deepEqual(f.calls, ['tunnel-stop', 'native-stop']);
});

test('stopped native needs no cleanup and exact native termination errors remain visible', async () => {
  const f = fixture();
  f.runtime.native.status = async () => false;
  f.runtime.native.stop = async () => { throw Object.assign(new Error('identity changed'), { code: 'NATIVE_PROCESS_STATE_CHANGED' }); };
  await assert.rejects(f.runtime.stop(), { code: 'NATIVE_PROCESS_STATE_CHANGED' });
  assert.deepEqual(f.calls, ['tunnel-stop']);
});

test('live native cannot bypass missing cleanup support or a stopped component response', async () => {
  const absent = fixture();
  absent.runtime.fullCleanActivation = null;
  await assert.rejects(absent.runtime.stop(), { code: 'SANDBOX_CLEANUP_UNSUPPORTED' });
  assert.deepEqual(absent.calls, []);
  const stale = fixture(async () => ({ code: 'COMPONENT_STOPPED' }));
  await assert.rejects(stale.runtime.stop(), { code: 'SANDBOX_TEARDOWN_UNCONFIRMED' });
  assert.equal(stale.calls.length, 1);
});

test('stop preparation reuses the existing bounded cleanup observer and exact confirmation validator', async () => {
  const coordinator = Object.create(FullCleanActivation.prototype);
  const operation = 'operation_stop_00000000000000000000000000000001';
  coordinator.now = () => 1_700_000_000_000;
  const confirmed = { safe: true, fenced: true, fence_operation_id: operation,
    executor_cleanup: { state: 'completed', confirmed: true } };
  let observed;
  coordinator._prepareFence = async (...args) => { observed = args; return confirmed; };
  assert.equal(await coordinator.prepareOwnedExecutorStop(operation), confirmed);
  assert.deepEqual(observed, [operation, 1_700_000_485_000, null, true]);
  coordinator._prepareFence = async () => ({ ...confirmed, executor_cleanup: { state: 'pending', confirmed: false } });
  await assert.rejects(coordinator.prepareOwnedExecutorStop(operation), { code: 'SANDBOX_TEARDOWN_UNCONFIRMED' });
});

test('native stop preserves a replacement owner when the prepared exact identity changed', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-prepared-stop-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const stateFile = path.join(root, 'runtime-state.json');
  fs.writeFileSync(stateFile, '{}');
  const service = Object.create(NativeService.prototype);
  service.paths = { stateFile: () => stateFile };
  service.ownedIdentity = async () => ({ pid: 12346, process_start_token: '170000000000000010' });
  service.terminateOwnedIdentity = async () => { throw new Error('replacement must not be terminated'); };
  service.clearOwnedState = () => { throw new Error('replacement state must be preserved'); };
  await assert.rejects(service.stop({ expectedIdentity: { pid: 12345, process_start_token: '170000000000000000' } }),
    { code: 'NATIVE_PROCESS_STATE_CHANGED' });
});
