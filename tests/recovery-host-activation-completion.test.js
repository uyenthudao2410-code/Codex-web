const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createRuntimePaths } = require('../electron/services/runtimePaths');
const { RecoveryHost } = require('../electron/services/recoveryHost');

function deferred() {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
}

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-activation-completion-'));
  const paths = createRuntimePaths({
    dataRoot: path.join(root, 'data'),
    resourcesRoot: path.join(root, 'resources'),
    appRoot: path.join(root, 'app')
  });
  const revision = 'a'.repeat(64);
  let epoch = {
    activation_epoch_id: 'activation-completion-0001',
    operation_id: 'operation-completion-0001',
    state: 'VERIFYING',
    admission_state: 'CLOSED',
    expires_at_unix_ms: Date.now() + 60_000,
    component_evidence: { recovery_host: { instance_id: 'old-recovery-host-0001' } }
  };
  const runtime = { mcpRunning: true, nativeAlive: true, tunnelRunning: true };
  const host = new RecoveryHost({
    paths,
    settings: { load: () => ({ autoStartServices: false }) },
    secrets: {},
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    healthService: {},
    orchestrator: {
      completeActivationEpoch: async () => ({}),
      lightweightSnapshot: async () => runtime
    },
    gateway: { start: async () => {}, stop: async () => {} },
    ipcServerFactory: () => ({ start: async () => {}, stop: async () => {} }),
    revisionTracker: {
      captureRunning: () => revision,
      status: () => ({ running_revision: revision, disk_revision: revision, state: 'current' })
    },
    replacement: { activationEpochId: epoch.activation_epoch_id },
    lifecycleProcessIdentityObserver: async (pid) => ({
      state: 'live', pid, process_start_token: '134321000000000000'
    })
  });
  host.activationEpochStore = { current: () => epoch };
  host.autoActivation.start = () => {};
  host.hostStatus = () => ({ activation_epoch: epoch });
  host.decorate = (value) => value;
  host.recordBootstrapEpoch = () => {};
  host.recordSupervisionStatus = (value) => { host.lastSupervisionStatus = value; };
  host.fullCleanActivation = {
    current: () => epoch,
    recordPendingCensus() {},
    finalize: async () => {
      epoch = { ...epoch, state: 'READY', admission_state: 'OPEN' };
      return { state: 'READY', admission_open: true };
    }
  };
  t.after(async () => {
    await host.stop();
    fs.rmSync(root, { recursive: true, force: true });
  });
  return { host, epochId: epoch.activation_epoch_id };
}

function busy(error) {
  assert.equal(error.code, 'RUNTIME_BUSY');
  assert.equal(error.retryable, true);
  return true;
}

test('replacement startup owns receipt production through READY admission and keeps status responsive', async (t) => {
  const { host, epochId } = fixture(t);
  const censusStarted = deferred();
  const releaseCensus = deferred();
  const admissionStarted = deferred();
  const releaseAdmission = deferred();
  let receipt = 0;
  const finish = host.fullCleanActivation.finalize;
  host.fullCleanActivation.finalCensus = async () => {
    const observedReceipt = ++receipt;
    censusStarted.resolve();
    await releaseCensus.promise;
    return { pass: true, receipt: observedReceipt };
  };
  host.fullCleanActivation.finalize = async (_id, census) => {
    admissionStarted.resolve();
    await releaseAdmission.promise;
    assert.equal(census.receipt, receipt, 'the receipt must stay current until admission opens');
    return finish();
  };
  host.fullCleanActivation.continueReplacement = async ({ activationEpochId }) => (
    host.fullCleanActivation.finalize(activationEpochId, await host.fullCleanActivation.finalCensus())
  );
  host.activation.preflight = async () => ({ receipt: ++receipt });
  host.activation.activate = async () => ({ receipt: ++receipt });
  host.fullCleanActivation.restart = async () => ({ receipt: ++receipt });
  const handlers = host.handlers();
  const started = host.start();
  t.after(() => { releaseCensus.resolve(); releaseAdmission.resolve(); });
  await censusStarted.promise;
  await assert.rejects(handlers['runtime.complete_activation_epoch'](epochId), busy);
  await assert.rejects(handlers['code.activation_preflight']({}), busy);
  await assert.rejects(handlers['code.activate_update']({}), busy);
  await assert.rejects(handlers['runtime.restart']({ refresh: true }), busy);
  assert.equal((await handlers['runtime.activation_epoch_status']()).state, 'VERIFYING');
  await host.superviseOnce();
  assert.equal(receipt, 1, 'the watchdog must not produce a competing receipt');
  releaseCensus.resolve();
  await admissionStarted.promise;
  await assert.rejects(handlers['runtime.complete_activation_epoch'](epochId), busy);
  await assert.rejects(handlers['code.activation_preflight']({}), busy);
  await assert.rejects(handlers['code.activate_update']({}), busy);
  await assert.rejects(handlers['runtime.restart']({ refresh: true }), busy);
  releaseAdmission.resolve();
  assert.equal((await started).activation_epoch.state, 'READY');
  assert.equal(host.activationEpochStore.current().admission_state, 'OPEN');
  assert.equal(host.activationCompletionInFlight, null);
  assert.deepEqual(await handlers['code.activation_preflight']({}), { receipt: 2 });
});

test('an earlier activation RPC excludes explicit completion before its second receipt producer', async (t) => {
  for (const action of ['code.activation_preflight', 'code.activate_update', 'runtime.restart']) {
    await t.test(action, async (caseTest) => {
      const { host, epochId } = fixture(caseTest);
      const preflightStarted = deferred();
      const releasePreflight = deferred();
      let censusCalls = 0;
      const producer = async () => {
        preflightStarted.resolve();
        await releasePreflight.promise;
        return { safe: true };
      };
      host.activation.preflight = producer;
      host.activation.activate = producer;
      host.fullCleanActivation.restart = producer;
      host.fullCleanActivation.finalCensus = async () => { censusCalls += 1; return { pass: true }; };
      const handlers = host.handlers();
      const preflight = handlers[action]({ refresh: true });
      caseTest.after(() => releasePreflight.resolve());
      await preflightStarted.promise;
      await assert.rejects(handlers['runtime.complete_activation_epoch'](epochId), busy);
      assert.equal(censusCalls, 0);
      releasePreflight.resolve();
      await preflight;
      assert.equal((await handlers['runtime.complete_activation_epoch'](epochId)).state, 'READY');
      assert.equal(censusCalls, 1);
      assert.equal(host.activationCompletionInFlight, null);
    });
  }
});

test('watchdog completion excludes operator completion and public preflight until READY', async (t) => {
  const { host, epochId } = fixture(t);
  const censusStarted = deferred();
  const releaseCensus = deferred();
  let producers = 0;
  host.running = true;
  host.fullCleanActivation.finalCensus = async () => {
    producers += 1;
    censusStarted.resolve();
    await releaseCensus.promise;
    return { pass: true };
  };
  host.activation.preflight = async () => { producers += 1; return {}; };
  const watchdog = host.superviseOnce();
  t.after(() => releaseCensus.resolve());
  await censusStarted.promise;
  const handlers = host.handlers();
  await assert.rejects(handlers['runtime.complete_activation_epoch'](epochId), busy);
  await assert.rejects(handlers['code.activation_preflight']({}), busy);
  assert.equal(producers, 1);
  releaseCensus.resolve();
  await watchdog;
  assert.equal(host.activationEpochStore.current().state, 'READY');
  assert.equal(host.activationCompletionInFlight, null);
});

test('explicit completion reserves before yielding and releases after census or admission errors', async (t) => {
  for (const stage of ['census', 'finalize', 'preflight']) {
    await t.test(stage, async (caseTest) => {
      const { host, epochId } = fixture(caseTest);
      const failed = Object.assign(new Error(`controlled ${stage} failure`), { code: 'CONTROLLED_FAILURE' });
      const finish = host.fullCleanActivation.finalize;
      host.fullCleanActivation.finalCensus = () => {
        if (stage === 'census') throw failed;
        return { pass: true };
      };
      host.fullCleanActivation.finalize = async () => { throw failed; };
      host.activation.preflight = async () => { throw failed; };
      const handlers = host.handlers();
      const operation = stage === 'preflight'
        ? handlers['code.activation_preflight']({})
        : handlers['runtime.complete_activation_epoch'](epochId);
      await assert.rejects(handlers['runtime.complete_activation_epoch'](epochId), busy);
      await assert.rejects(operation, (error) => error === failed);
      assert.equal(host.activationCompletionInFlight, null);
      host.fullCleanActivation.finalCensus = async () => ({ pass: true });
      host.fullCleanActivation.finalize = finish;
      assert.equal((await handlers['runtime.complete_activation_epoch'](epochId)).state, 'READY');
    });
  }
});

test('automatic activation receipt producers share the host reservation in both directions', async (t) => {
  for (const method of ['preflight', 'activate', 'verifyCheckpointLifecycle']) {
    await t.test(method, async (caseTest) => {
      const { host, epochId } = fixture(caseTest);
      const producerStarted = deferred();
      const releaseProducer = deferred();
      let producers = 0;
      host.activation[method] = async () => {
        producers += 1;
        producerStarted.resolve();
        await releaseProducer.promise;
        return { safe: true };
      };
      host.fullCleanActivation.finalCensus = async () => { producers += 1; return { pass: true }; };
      const automatic = host.autoActivation.activation[method]({});
      caseTest.after(() => releaseProducer.resolve());
      await producerStarted.promise;
      const complete = host.handlers()['runtime.complete_activation_epoch'];
      await assert.rejects(complete(epochId), busy);
      assert.equal(producers, 1);
      releaseProducer.resolve();
      await automatic;
      const censusStarted = deferred();
      const releaseCensus = deferred();
      host.fullCleanActivation.finalCensus = async () => {
        producers += 1;
        censusStarted.resolve();
        await releaseCensus.promise;
        return { pass: true };
      };
      const completed = complete(epochId);
      caseTest.after(() => releaseCensus.resolve());
      await censusStarted.promise;
      await assert.rejects(host.autoActivation.activation[method]({}), busy);
      assert.equal(producers, 2);
      releaseCensus.resolve();
      await completed;
      assert.equal(host.activationCompletionInFlight, null);
    });
  }
});

test('bootstrap restart after IPC starts excludes a public receipt producer', async (t) => {
  const { host, epochId } = fixture(t);
  const bootstrapStarted = deferred();
  const releaseBootstrap = deferred();
  const operationId = host.activationEpochStore.current().operation_id;
  host.bootstrap = { refresh: true, operation_id: operationId };
  host.prepareBootstrapStart = async () => ({
    requiresNewEpoch: true, operationId, expectedRevision: 'a'.repeat(64), expiresAtUnixMs: Date.now() + 60_000
  });
  host.fullCleanActivation.restart = async () => {
    bootstrapStarted.resolve();
    await releaseBootstrap.promise;
    return { state: 'HANDOFF' };
  };
  let publicProducers = 0;
  host.activation.preflight = async () => { publicProducers += 1; return {}; };
  const started = host.start();
  t.after(() => releaseBootstrap.resolve());
  await bootstrapStarted.promise;
  assert.equal(host.running, true, 'IPC is already available at the bootstrap boundary');
  await assert.rejects(host.handlers()['code.activation_preflight']({}), busy);
  assert.equal(publicProducers, 0);
  releaseBootstrap.resolve();
  assert.equal((await started).activation_epoch.activation_epoch_id, epochId);
  assert.equal(host.activationCompletionInFlight, null);
});

test('watchdog ticket and nested supervisor producers defer while another observation owns the receipt', async (t) => {
  const { host, epochId } = fixture(t);
  await host.fullCleanActivation.finalize();
  host.running = true;
  const ticketStarted = deferred();
  const releaseTicket = deferred();
  let tickets = 0;
  let supervision = 0;
  host.orchestrator.serviceSupervisorRestartRequest = async () => {
    tickets += 1;
    ticketStarted.resolve();
    await releaseTicket.promise;
    return { status: 'deferred' };
  };
  host.orchestrator.supervise = async () => { supervision += 1; return {}; };
  const watchdog = host.superviseOnce();
  t.after(() => releaseTicket.resolve());
  await ticketStarted.promise;
  await assert.rejects(host.handlers()['code.activation_preflight']({}), busy);
  releaseTicket.resolve();
  await watchdog;
  assert.equal(tickets, 1);
  assert.equal(supervision, 0);
  const preflightStarted = deferred();
  const releasePreflight = deferred();
  host.activation.preflight = async () => {
    preflightStarted.resolve();
    await releasePreflight.promise;
    return {};
  };
  const preflight = host.handlers()['code.activation_preflight']({});
  t.after(() => releasePreflight.resolve());
  await preflightStarted.promise;
  await host.superviseOnce();
  assert.equal(tickets, 1, 'the ticket is retained for the next idle watchdog tick');
  assert.equal(supervision, 0, 'ordinary supervision also contains a ticket producer');
  releasePreflight.resolve();
  await preflight;
  assert.equal(host.activationCompletionInFlight, null);
  assert.equal(host.activationEpochStore.current().activation_epoch_id, epochId);
});
