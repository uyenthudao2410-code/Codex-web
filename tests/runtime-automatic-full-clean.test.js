const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { RuntimeOrchestrator } = require('../electron/services/runtimeOrchestrator');

function makeOrchestrator(t, { fullCleanActivation, recoverError, readyWhen = () => false }) {
  const progress = [];
  const statePath = path.join(os.tmpdir(), `p3-state-${process.pid}-${Math.random().toString(36).slice(2)}.json`);
  fs.writeFileSync(statePath, JSON.stringify({ manualStop: false }), 'utf8');
  t.after(() => fs.rmSync(statePath, { force: true }));
  const failing = () => ({
    componentsReady: false, fullyReady: false, executionRole: 'central_executor',
    mcpRunning: false, nativeAlive: false, tunnelRunning: false,
    mcpHealthFailureDeterministic: false
  });
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: os.tmpdir(), autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress: (event) => { progress.push(event); },
    emitStatus: () => {},
    fullCleanActivation
  });
  orchestrator.paths = { ...orchestrator.paths, stateFile: () => statePath };
  orchestrator.activationEpochId = 'activation-test-epoch-1';
  orchestrator.serviceSupervisorRestartRequest = async () => null;
  orchestrator.lightweightSnapshot = async () => (readyWhen()
    ? { componentsReady: true, fullyReady: true, executionRole: 'central_executor', mcpRunning: true, nativeAlive: true, tunnelRunning: true }
    : failing());
  orchestrator.recoverMcpOnly = async () => { throw recoverError; };
  return { orchestrator, progress };
}

function updateIncompleteError() {
  return Object.assign(new Error('A committed or terminal activation cannot replace Coding MCP in place.'), {
    code: 'UPDATE_INCOMPLETE',
    details: { full_clean_activation_required: true }
  });
}

async function triggerRecovery(orchestrator) {
  await orchestrator.supervise();
  await orchestrator.supervise();
  return orchestrator.supervise();
}

test('P3: UPDATE_INCOMPLETE + full_clean_required triggers exactly one automatic full-clean and reaches READY', async (t) => {
  const calls = [];
  const fake = {
    restart: async (options) => {
      calls.push(options);
      return { state: 'READY', fully_ready: true, admission_open: true, full_clean_activation: true };
    }
  };
  const { orchestrator, progress } = makeOrchestrator(t, { fullCleanActivation: fake, recoverError: updateIncompleteError(), readyWhen: () => calls.length > 0 });
  const result = await triggerRecovery(orchestrator);
  assert.equal(calls.length, 1, 'exactly one automatic full-clean');
  assert.equal(calls[0].refresh, true);
  assert.equal(calls[0].mode, 'full_clean_refresh');
  assert.equal(calls[0].reason, 'automatic_full_clean_update_incomplete');
  assert.equal(result.fullyReady, true, 'supervise returns READY without manual IPC');
  assert.equal(orchestrator.autoRecoveryBlocked, false);
  assert.equal(orchestrator.automaticFullCleanFailed, false);
  const steps = progress.map((e) => e.step);
  assert.ok(steps.includes('automatic-full-clean-start'), 'progress emitted at self-run start');
  assert.ok(steps.includes('automatic-full-clean-ready'), 'progress emitted at self-run end');
  for (const event of progress) assert.equal(String(event.message || '').includes('UPDATE_INCOMPLETE'), false, 'progress must not leak raw error codes');
});

test('P3: after a successful self-run, a still-failing snapshot does not trigger a second automatic full-clean', async (t) => {
  const calls = [];
  const fake = { restart: async () => { calls.push(1); return { state: 'READY', fully_ready: true, admission_open: true, full_clean_activation: true }; } };
  const { orchestrator } = makeOrchestrator(t, { fullCleanActivation: fake, recoverError: updateIncompleteError() });
  await triggerRecovery(orchestrator);
  assert.equal(calls.length, 1);
  await triggerRecovery(orchestrator);
  assert.equal(calls.length, 1, 'no second automatic full-clean without a new manual trigger');
  assert.equal(orchestrator.autoRecoveryBlocked, true, 'blocked honestly after the second failure');
});

test('P3: if the automatic full-clean fails, it stops after one attempt and reports clearly for manual fallback', async (t) => {
  const calls = [];
  const fake = { restart: async () => { calls.push(1); throw new Error('full clean failed in test'); } };
  const { orchestrator, progress } = makeOrchestrator(t, { fullCleanActivation: fake, recoverError: updateIncompleteError() });
  const result = await triggerRecovery(orchestrator);
  assert.equal(calls.length, 1);
  assert.equal(orchestrator.automaticFullCleanFailed, true);
  assert.equal(orchestrator.autoRecoveryBlocked, true);
  assert.equal(result.fullyReady, false);
  const failed = progress.filter((e) => e.step === 'automatic-full-clean-failed');
  assert.equal(failed.length, 1);
  assert.equal(failed[0].message, 'Tự khôi phục không thành công, cần kích hoạt thủ công.');
  await orchestrator.supervise();
  assert.equal(calls.length, 1, 'blocked supervise does not retry the self-run');
});

test('P3: unrelated failures do NOT trigger the automatic full-clean', async (t) => {
  const calls = [];
  const fake = { restart: async () => { calls.push(1); return { state: 'READY', fully_ready: true, admission_open: true, full_clean_activation: true }; } };
  const unrelated = Object.assign(new Error('port in use'), { code: 'MCP_PORT_IN_USE' });
  const { orchestrator, progress } = makeOrchestrator(t, { fullCleanActivation: fake, recoverError: unrelated });
  await triggerRecovery(orchestrator);
  assert.equal(calls.length, 0, 'no automatic full-clean for unrelated failures');
  assert.equal(orchestrator.automaticFullCleanAttempted, false);
  assert.equal(orchestrator.autoRecoveryBlocked, false);
  assert.equal(progress.some((e) => String(e.step || '').startsWith('automatic-full-clean')), false);
});

test('P3: runAutomaticFullCleanOnce directly respects the one-time guard', async (t) => {
  const calls = [];
  const fake = { restart: async () => { calls.push(1); return { state: 'READY', fully_ready: true, admission_open: true, full_clean_activation: true }; } };
  const { orchestrator } = makeOrchestrator(t, { fullCleanActivation: fake, recoverError: updateIncompleteError() });
  const first = await orchestrator.runAutomaticFullCleanOnce();
  assert.equal(first.attempted, true);
  const second = await orchestrator.runAutomaticFullCleanOnce();
  assert.equal(second.attempted, false);
  assert.equal(calls.length, 1, 'direct second call does not run a second full-clean');
});
