'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {
  runLifecycle,
  uiObservation,
  unavailableObservation,
  createRuntimeDependencies
} = require('../scripts/dev-ui-lifecycle');
const { RecoveryHost } = require('../electron/services/recoveryHost');

const REVISION = 'a'.repeat(64);
const ACCEPTED_HEAD = 'b'.repeat(40);
const PROOF_FINGERPRINT = 'c'.repeat(64);

function acceptedClosure(overrides = {}) {
  return {
    schema_version: 1,
    source_checkpoint_id: 'checkpoint-electron-ui-0001',
    run_id: 'run-electron-ui-0001',
    wave_id: 'wave-electron-ui-0001',
    proof_fingerprint: PROOF_FINGERPRINT,
    accepted_head: ACCEPTED_HEAD,
    source_accepted: true,
    accepted_receipts_complete: true,
    activation_eligible: true,
    eligibility_code: 'ACTIVATABLE',
    affected_components: ['electron_ui'],
    affected_components_valid: true,
    component_receipts_valid: true,
    postflight_receipts: {
      electron_ui: { source_checkpoint_id: 'must-not-be-used-for-prepare' }
    },
    ...overrides
  };
}

function ui(state, instanceId = 'electron-ui-instance-0001', pid = 42001) {
  return {
    state,
    alive: state !== 'MISSING',
    suppressed: false,
    pid: state === 'MISSING' ? null : pid,
    instanceId: state === 'MISSING' ? null : instanceId,
    startedAtUnixMs: state === 'MISSING' ? null : 1234,
    runtimeMode: 'development',
    runningRevision: state === 'CURRENT' ? REVISION : state === 'STALE' ? 'b'.repeat(64) : null,
    diskRevision: REVISION,
    revisionState: state === 'CURRENT' ? 'current' : state === 'STALE' ? 'pending' : 'stopped',
    updatePending: state === 'STALE'
  };
}

function observation(state, instanceId, pid) {
  return {
    hostAvailable: true,
    installationMatches: true,
    descriptor: { owner_pid: 41001, instance_id: 'recovery-host-instance-0001', installation_id: 'c'.repeat(64) },
    client: {},
    status: {},
    ui: ui(state, instanceId, pid),
    errorCode: null
  };
}

function harness(initial) {
  let current = initial;
  let replacementCounter = 0;
  const calls = [];
  const lines = [];
  return {
    calls,
    lines,
    get current() { return current; },
    set current(value) { current = value; },
    deps: {
      inspect: async () => current,
      activate: async () => {
        calls.push('activate');
        current = observation('CURRENT', `activated-ui-instance-${++replacementCounter}`.padEnd(24, '0'), 42100 + replacementCounter);
      },
      suppress: async (value) => {
        calls.push(`suppress:${value.ui.instanceId}`);
        current = { ...current, ui: { ...current.ui, suppressed: true } };
      },
      signal: async (action, instanceId) => {
        calls.push(`signal:${action}:${instanceId}`);
        if (action === 'stop') current = observation('MISSING');
      },
      launch: async () => {
        calls.push('launch');
        current = observation('CURRENT', `launched-ui-instance-${++replacementCounter}`.padEnd(24, '0'), 42200 + replacementCounter);
      },
      processAlive: (pid) => current.ui.alive === true && current.ui.pid === pid,
      sleep: async () => {},
      output: (line) => lines.push(line),
      timeoutMs: 1000,
      pollMs: 1
    }
  };
}

function runtimeStatusHarness() {
  const source = fs.readFileSync(path.resolve(__dirname, '..', 'renderer', 'app.js'), 'utf8');
  const start = source.indexOf('function shortRevision');
  const end = source.indexOf('function renderSnapshot');
  assert.ok(start >= 0 && end > start, 'runtime status presentation functions must remain discoverable');
  const selectors = [
    '#runtimeElectronState', '#runtimeElectronMeta', '#runtimeRecoveryState', '#runtimeRecoveryMeta',
    '#runtimeMcpSourceState', '#runtimeMcpSourceMeta', '#runtimeTunnelSourceState', '#runtimeTunnelSourceMeta',
    '#runtimeSourceSummary', '#sourceUpdateNotice', '#sourceUpdateMessage',
    '#runtimeClosureState', '#runtimeClosureMeta', '#activationClosureNotice', '#activationClosureMessage'
  ];
  const elements = new Map(selectors.map((selector) => [selector, {
    textContent: '',
    dataset: {},
    hidden: false,
    className: ''
  }]));
  const context = vm.createContext({ $: (selector) => elements.get(selector) || null });
  vm.runInContext(source.slice(start, end), context, { filename: 'renderer/app-runtime-status.js' });
  return {
    elements,
    connector(status) {
      context.__status = status;
      return vm.runInContext('connectorContractPresentation(__status)', context);
    },
    render(snapshot) {
      context.__snapshot = snapshot;
      vm.runInContext('renderRuntimeSourceStatus(__snapshot)', context);
    }
  };
}

function runtimeActivationHarness(closure) {
  const calls = [];
  const deps = createRuntimeDependencies({
    paths: {
      runtimeIdentity: () => ({ runtime_mode: 'development', installation_id: 'c'.repeat(64) }),
      executablePath: () => process.execPath,
      appRoot: () => path.resolve(__dirname, '..')
    },
    output: () => {},
    sleep: async () => {}
  });
  const live = observation('STALE');
  live.status = closure === undefined ? {} : { auto_activation: { closure_input: closure } };
  live.client = {
    call: async (method, args) => {
      calls.push({ method, request: args[0] });
      if (method === 'code.activation_preflight') return { safe: true, code: 'READY' };
      if (method === 'code.activate_update') return { state: 'completed' };
      throw new Error(`unexpected method: ${method}`);
    }
  };
  return { calls, deps, live };
}

test('dev focuses an exact current UI and reports process plus revision postflight', async () => {
  const fixture = harness(observation('CURRENT'));
  const result = await runLifecycle('start', fixture.deps);
  assert.equal(result.ui.state, 'CURRENT');
  assert.deepEqual(fixture.calls, ['signal:focus:electron-ui-instance-0001']);
  assert.match(fixture.lines.at(-1), /DEV_UI CURRENT action=start pid=42001/);
  assert.match(fixture.lines.at(-1), new RegExp(`running_revision=${REVISION} disk_revision=${REVISION}`));
});

test('dev:status reports lifecycle state without signaling or activating the UI', async () => {
  const fixture = harness(observation('STALE'));
  const result = await runLifecycle('status', fixture.deps);
  assert.equal(result.ui.state, 'STALE');
  assert.deepEqual(fixture.calls, []);
  assert.match(fixture.lines.at(-1), /DEV_UI STATUS state=STALE host=available installation=current/);
  assert.match(fixture.lines.at(-1), /running_revision=b+ disk_revision=a+/);
});

test('dev:status exposes connector receipt and acknowledgement gate from a read-only runtime snapshot', async () => {
  const fixture = harness(observation('CURRENT'));
  let reads = 0;
  fixture.deps.runtimeSnapshot = async () => {
    reads += 1;
    return {
      toolContract: { sha256: 'f'.repeat(64) },
      connectorContractAcknowledgedSha256: 'e'.repeat(64),
      connectorContractState: 'CHANGED_DISCOVERED_NEEDS_ACK',
      connectorRefreshRequired: false,
      connectorAcknowledgementPending: true,
      connectorRediscovered: true,
      connectorRediscoveredAt: '2026-08-26T01:23:45.000Z'
    };
  };
  await runLifecycle('status', fixture.deps);
  assert.equal(reads, 1);
  assert.deepEqual(fixture.calls, []);
  const line = fixture.lines.at(-1);
  assert.match(line, /connector_state=CHANGED_DISCOVERED_NEEDS_ACK/);
  assert.match(line, /connector_rediscovered=true/);
  assert.match(line, /connector_refresh_required=false/);
  assert.match(line, /connector_ack_pending=true/);
  assert.match(line, new RegExp(`connector_current_sha=${'f'.repeat(64)}`));
  assert.match(line, new RegExp(`connector_ack_sha=${'e'.repeat(64)}`));
});

test('dev routes a stale same-checkout UI through component activation before focus', async () => {
  const fixture = harness(observation('STALE'));
  const result = await runLifecycle('start', fixture.deps);
  assert.equal(result.ui.state, 'CURRENT');
  assert.equal(fixture.calls[0], 'activate');
  assert.match(fixture.calls[1], /^signal:focus:activated-ui-instance-/);
  assert.match(fixture.lines[0], /DEV_UI STALE action=activate/);
});

test('runtime activation binds the exact eligible closure checkpoint into preflight and activate requests', async () => {
  const fixture = runtimeActivationHarness(acceptedClosure());
  await fixture.deps.activate(fixture.live);
  assert.equal(fixture.calls.length, 2);
  assert.deepEqual(fixture.calls.map((call) => call.method), [
    'code.activation_preflight',
    'code.activate_update'
  ]);
  const expected = {
    checkpoint_id: 'checkpoint-electron-ui-0001',
    run_id: 'run-electron-ui-0001',
    wave_id: 'wave-electron-ui-0001',
    proof_fingerprint: PROOF_FINGERPRINT,
    git_head: ACCEPTED_HEAD
  };
  for (const call of fixture.calls) {
    assert.deepEqual(call.request.source_checkpoint, expected);
    assert.equal(Object.hasOwn(call.request.source_checkpoint, 'postflight_receipts'), false);
  }
});

test('runtime activation refuses missing or ineligible closure checkpoints before Recovery IPC', async () => {
  const missing = runtimeActivationHarness(undefined);
  await assert.rejects(missing.deps.activate(missing.live), { code: 'DEV_UI_ACTIVATION_CHECKPOINT_UNAVAILABLE' });
  assert.deepEqual(missing.calls, []);

  for (const override of [
    { schema_version: 99 },
    { source_accepted: false },
    { accepted_receipts_complete: false },
    { activation_eligible: false },
    { affected_components_valid: false },
    { affected_components: ['coding_mcp'] }
  ]) {
    const fixture = runtimeActivationHarness(acceptedClosure(override));
    await assert.rejects(fixture.deps.activate(fixture.live), { code: 'DEV_UI_CHECKPOINT_NOT_ACTIVATABLE' });
    assert.deepEqual(fixture.calls, []);
  }
});

test('runtime activation refuses an invalid closure identity without normalizing it into authority', async () => {
  const fixture = runtimeActivationHarness(acceptedClosure({ proof_fingerprint: ` ${PROOF_FINGERPRINT}` }));
  await assert.rejects(fixture.deps.activate(fixture.live), { code: 'DEV_UI_ACTIVATION_CHECKPOINT_INVALID' });
  assert.deepEqual(fixture.calls, []);
});

test('runtime activation refuses noncanonical IDs or unordered/duplicate component ownership', async () => {
  for (const { override, expectedCode } of [
    {
      override: { source_checkpoint_id: ' checkpoint-electron-ui-0001' },
      expectedCode: 'DEV_UI_ACTIVATION_CHECKPOINT_INVALID'
    },
    {
      override: { affected_components: ['electron_ui', 'recovery_host'], affected_components_valid: true },
      expectedCode: 'DEV_UI_CHECKPOINT_NOT_ACTIVATABLE'
    },
    {
      override: { affected_components: ['electron_ui', 'electron_ui'], affected_components_valid: true },
      expectedCode: 'DEV_UI_CHECKPOINT_NOT_ACTIVATABLE'
    },
    {
      override: { affected_components: ['unknown_component'], affected_components_valid: true },
      expectedCode: 'DEV_UI_CHECKPOINT_NOT_ACTIVATABLE'
    }
  ]) {
    const fixture = runtimeActivationHarness(acceptedClosure(override));
    await assert.rejects(fixture.deps.activate(fixture.live), { code: expectedCode });
    assert.deepEqual(fixture.calls, []);
  }
});

test('dev launches a missing UI and verifies the fresh registration', async () => {
  const fixture = harness(observation('MISSING'));
  const result = await runLifecycle('start', fixture.deps);
  assert.equal(result.ui.state, 'CURRENT');
  assert.deepEqual(fixture.calls.slice(0, 2), ['launch', `signal:focus:${result.ui.instanceId}`]);
  assert.match(fixture.lines[0], /DEV_UI MISSING action=launch/);
});

test('dev:stop suppresses watchdog recovery before signaling the exact UI instance', async () => {
  const fixture = harness(observation('CURRENT'));
  const result = await runLifecycle('stop', fixture.deps);
  assert.equal(result.ui.state, 'MISSING');
  assert.deepEqual(fixture.calls, [
    'suppress:electron-ui-instance-0001',
    'signal:stop:electron-ui-instance-0001'
  ]);
  assert.match(fixture.lines.at(-1), /DEV_UI STOPPED .*services=preserved/);
});

test('dev:stop fails closed when Recovery Host cannot prove whether the UI is running', async () => {
  const fixture = harness(unavailableObservation(Object.assign(new Error('missing'), { code: 'ENOENT' })));
  await assert.rejects(runLifecycle('stop', fixture.deps), { code: 'DEV_UI_HOST_UNAVAILABLE' });
  assert.deepEqual(fixture.calls, []);
  assert.deepEqual(fixture.lines, []);
});

test('dev:stop does not treat transient Recovery Host loss as proof until the exact prior PID exits', async () => {
  const fixture = harness(observation('CURRENT'));
  let aliveChecks = 0;
  fixture.deps.processAlive = () => {
    aliveChecks += 1;
    return aliveChecks < 3;
  };
  fixture.deps.signal = async (action, instanceId) => {
    fixture.calls.push(`signal:${action}:${instanceId}`);
    if (action === 'stop') {
      fixture.current = unavailableObservation(Object.assign(new Error('transient host loss'), { code: 'ECONNREFUSED' }));
    }
  };
  const result = await runLifecycle('stop', fixture.deps);
  assert.equal(result.hostAvailable, false);
  assert.equal(aliveChecks, 3, 'host loss alone must not satisfy the stop postflight');
  assert.match(fixture.lines.at(-1), /DEV_UI STOPPED .*previous_pid=42001/);
});

test('dev:stop does not treat a missing registration as proof while the prior PID remains alive', async () => {
  const fixture = harness(observation('CURRENT'));
  fixture.deps.processAlive = () => true;
  let first = true;
  fixture.deps.inspect = async () => {
    if (first) { first = false; return fixture.current; }
    return observation('MISSING');
  };
  await assert.rejects(runLifecycle('stop', fixture.deps), { code: 'DEV_UI_LIFECYCLE_TIMEOUT' });
  assert.deepEqual(fixture.calls.slice(0, 2), [
    'suppress:electron-ui-instance-0001',
    'signal:stop:electron-ui-instance-0001'
  ]);
});

test('dev:stop activates a stale handler before dispatching the graceful stop signal', async () => {
  const fixture = harness(observation('STALE'));
  await runLifecycle('stop', fixture.deps);
  assert.equal(fixture.calls[0], 'activate');
  assert.match(fixture.calls[1], /^suppress:activated-ui-instance-/);
  assert.match(fixture.calls[2], /^signal:stop:activated-ui-instance-/);
});

test('dev:replace first activates a current handler, then stops and verifies a new instance', async () => {
  const fixture = harness(observation('STALE'));
  const result = await runLifecycle('replace', fixture.deps);
  assert.equal(result.ui.state, 'CURRENT');
  assert.deepEqual(fixture.calls.map((call) => call.split(':')[0]), [
    'activate', 'suppress', 'signal', 'launch'
  ]);
  assert.notEqual(result.ui.instanceId, fixture.calls[1].slice('suppress:'.length));
  assert.match(fixture.lines.at(-1), /DEV_UI REPLACED .*running_revision=.* disk_revision=/);
});

test('dev stop and replace refuse a non-development UI even when revisions match', async () => {
  for (const action of ['stop', 'replace']) {
    const fixture = harness(observation('CURRENT'));
    fixture.deps.inspect = async () => ({
      ...fixture.current,
      ui: { ...fixture.current.ui, runtimeMode: 'production' }
    });
    await assert.rejects(runLifecycle(action, fixture.deps), { code: 'DEV_UI_CURRENT_RECEIPT_INCOMPLETE' });
    assert.deepEqual(fixture.calls, []);
  }
});

test('all mutating lifecycle actions fail closed for another installation', async () => {
  const foreign = { ...observation('CURRENT'), installationMatches: false };
  for (const action of ['start', 'stop', 'replace']) {
    const fixture = harness(foreign);
    await assert.rejects(runLifecycle(action, fixture.deps), { code: 'DEV_UI_INSTALLATION_MISMATCH' });
    assert.deepEqual(fixture.calls, []);
  }
});

test('runtime status classification distinguishes CURRENT, STALE and MISSING', () => {
  assert.equal(uiObservation({
    electron_ui_recovery: { alive: true, pid: 42, instance_id: 'electron-ui-instance-0001', runtime_mode: 'development' },
    electron_ui_revision: { running_revision: REVISION, disk_revision: REVISION, update_pending: false }
  }).state, 'CURRENT');
  assert.equal(uiObservation({
    electron_ui_recovery: { alive: true },
    electron_ui_revision: { running_revision: 'b'.repeat(64), disk_revision: REVISION, update_pending: true }
  }).state, 'STALE');
  assert.equal(uiObservation({ electron_ui_recovery: { alive: false } }).state, 'MISSING');
});

test('Recovery Host exposes bounded UI lifecycle identity without exposing its descriptor token', () => {
  const status = RecoveryHost.prototype.uiRecoveryStatus.call({
    activation: {
      uiRecoveryPreferenceStatus: () => ({ suppressed: false, reason: '' }),
      uiPresence: () => ({ tracked: true, alive: true, pid: 42001, instance_id: 'electron-ui-instance-0001' }),
      hasPendingUiActivation: () => false,
      uiRegistration: { started_at_unix_ms: 1234 }
    },
    paths: { runtimeMode: () => 'development' },
    uiRecoveryAttempts: [],
    uiRecoveryLastState: 'healthy',
    uiRecoveryInitialGraceUntil: 0,
    uiRecoveryCircuitUntil: 0,
    uiRecoveryPendingUntil: 0,
    uiRecoveryNextAttemptAt: 0,
    uiRecoveryLastLaunchPid: 0,
    uiRecoveryLastErrorCode: ''
  });
  assert.equal(status.pid, 42001);
  assert.equal(status.instance_id, 'electron-ui-instance-0001');
  assert.equal(status.started_at_unix_ms, 1234);
  assert.equal(status.runtime_mode, 'development');
  assert.equal(Object.hasOwn(status, 'token'), false);
});

test('Electron main makes duplicate start actionable and accepts only exact UI lifecycle signals', () => {
  const source = fs.readFileSync(path.resolve(__dirname, '..', 'electron', 'main.js'), 'utf8');
  assert.match(source, /Coding Tools MCP UI is already running\. Use "npm run dev"/);
  assert.match(source, /app\.on\('second-instance', \(_event, commandLine\) => handleSecondInstance\(commandLine\)\)/);
  assert.match(source, /request\.instanceId !== uiInstanceId/);
  assert.match(source, /void quitUi\('operator_quit'\)/);
  assert.match(source, /async function codeActivationRequest\(component, allowAcceptancePending = false\)/);
  assert.match(source, /orchestrator\.snapshot\(\{ force: true, reason: 'manual-code-activation-authority' \}\)/);
  assert.match(source, /activationSourceCheckpoint\(snapshot\?\.recoveryHost, component\)/);
  assert.match(source, /full_clean_required: true/);
  assert.match(source, /activation_mode: 'full_clean_activation'/);
  assert.equal((source.match(/await codeActivationRequest\(component, allowAcceptancePending\)/g) || []).length, 2);
  assert.match(source, /async function fullCleanRestartOptions\(\)/);
  assert.match(source, /orchestrator\.snapshot\(\{ force: true, reason: 'manual-full-clean-restart-authority' \}\)/);
  assert.match(source, /sourceCheckpoint: activationSourceCheckpoint\(snapshot\?\.recoveryHost\)/);
  assert.match(source, /orchestrator\.restart\(await fullCleanRestartOptions\(\)\)/);
});

test('Electron task list reads and controls canonical orchestration state instead of task-state files', () => {
  const source = fs.readFileSync(path.resolve(__dirname, '..', 'electron', 'main.js'), 'utf8');
  const start = source.indexOf("secureHandle('task-state:read'");
  const end = source.indexOf("secureHandle('performance:read'", start);
  assert.ok(start >= 0 && end > start);
  const handlers = source.slice(start, end);
  assert.match(handlers, /readOrchestrationControlSnapshot\(\)/);
  assert.match(handlers, /taskList\?\.source !== 'orchestration_ledger'/);
  assert.match(handlers, /taskList\.current/);
  assert.match(handlers, /Array\.isArray\(taskList\.history\)/);
  for (const action of ['clear', 'pause', 'resume', 'stop']) {
    assert.match(handlers, new RegExp(`panelTaskControl\\('${action}'\\)`));
  }
  assert.doesNotMatch(handlers, /workspaceStatePaths|archiveTask|readJson|writeJsonAtomic/);
});

test('Command Center renders loaded-source status and connector enum semantics', () => {
  const root = path.resolve(__dirname, '..');
  const html = fs.readFileSync(path.join(root, 'renderer', 'index.html'), 'utf8');
  const app = fs.readFileSync(path.join(root, 'renderer', 'app.js'), 'utf8');
  for (const id of [
    'runtimeSourceStatusCard', 'runtimeElectronState', 'runtimeRecoveryState',
    'runtimeMcpSourceState', 'runtimeTunnelSourceState', 'sourceUpdateNotice',
    'runtimeClosureState', 'activationClosureNotice'
  ]) assert.match(html, new RegExp(`id="${id}"`));
  assert.match(app, /function renderRuntimeSourceStatus\(snapshot\)/);
  assert.match(app, /UNCHANGED_ACKNOWLEDGED/);
  assert.match(app, /CURRENT_ACKNOWLEDGED/);
  assert.match(app, /CHANGED_NEEDS_DISCOVERY/);
  assert.match(app, /CHANGED_DISCOVERED_NEEDS_ACK/);
  assert.match(app, /function connectorContractPresentation\(status = \{\}\)/);
  assert.match(app, /explicit === 'UNAVAILABLE'/);
  assert.match(app, /api\.snapshot\(options\)/);
});

test('Command Center counts three revisioned components and reports Tunnel readiness separately', () => {
  const fixture = runtimeStatusHarness();
  const revision = { running_revision: REVISION, disk_revision: REVISION, update_pending: false };
  const snapshot = {
    status: {
      runtimeRunning: true,
      tunnelRunning: true,
      codeRevision: { codingMcp: revision }
    },
    recoveryHost: {
      state: 'healthy',
      code_revision: revision,
      electron_ui_revision: revision,
      electron_ui_recovery: { alive: true, pid: 42001, runtime_mode: 'development' }
    }
  };
  fixture.render(snapshot);
  assert.equal(fixture.elements.get('#runtimeTunnelSourceState').textContent, 'READY');
  assert.equal(fixture.elements.get('#runtimeTunnelSourceState').dataset.state, 'ready');
  assert.equal(fixture.elements.get('#runtimeSourceSummary').textContent, 'SOURCE 3/3 CURRENT · TUNNEL READY');
  assert.equal(fixture.elements.get('#runtimeSourceSummary').className, 'cc-pill is-active');

  snapshot.status.tunnelRunning = false;
  fixture.render(snapshot);
  assert.equal(fixture.elements.get('#runtimeTunnelSourceState').textContent, 'STOPPED');
  assert.equal(fixture.elements.get('#runtimeSourceSummary').textContent, 'SOURCE 3/3 CURRENT · TUNNEL STOPPED');
  assert.equal(fixture.elements.get('#runtimeSourceSummary').className, 'cc-pill is-waiting');
});

test('connector fallback refuses to invent acknowledgement when both enum and legacy boolean are absent', () => {
  const fixture = runtimeStatusHarness();
  assert.equal(fixture.connector({}).state, 'UNAVAILABLE');
  assert.equal(fixture.connector({ connectorRefreshRequired: false }).state, 'UNAVAILABLE');
  assert.equal(fixture.connector({ connectorRefreshRequired: true }).state, 'UNAVAILABLE');
  assert.equal(fixture.connector({ connectorContractState: 'UNKNOWN_STATE', connectorRefreshRequired: false }).state, 'UNAVAILABLE');
});

test('connector presentation no longer promotes retired compatible-snapshot state', () => {
  const fixture = runtimeStatusHarness();
  const compatible = fixture.connector({ connectorContractState: 'COMPATIBLE_ACKNOWLEDGED', connectorRefreshRequired: false });
  assert.equal(compatible.state, 'UNAVAILABLE');
  assert.equal(compatible.notice, false);
});

test('Command Center exposes the machine closure state without promoting source health to LIVE_CLOSED', () => {
  const fixture = runtimeStatusHarness();
  const revision = { running_revision: REVISION, disk_revision: REVISION, update_pending: false };
  const snapshot = {
    status: {
      runtimeRunning: true,
      tunnelRunning: true,
      codeRevision: { codingMcp: revision },
      fullyReady: true,
      activationClosure: {
        schema_version: 1,
        source_checkpoint_id: 'checkpoint-closure-0001',
        run_id: 'run-closure-0001',
        wave_id: 'wave-closure-0001',
        proof_fingerprint: PROOF_FINGERPRINT,
        accepted_head: ACCEPTED_HEAD,
        closure_state: 'CONNECTOR_CONTRACT_NOT_CURRENT',
        closure_input_schema_supported: true,
        checkpoint_identity_valid: true,
        source_accepted: true,
        accepted_receipts_complete: true,
        activation_eligible: true,
        affected_components_valid: true,
        component_receipts_valid: true,
        postflight_receipts_valid: true,
        lifecycle_clean: true,
        components_current: true,
        connector_contract_current: true,
        runtime_fully_ready: true,
        release_state: 'NOT_RELEASED',
        production_state: 'NOT_CLAIMED'
      }
    },
    recoveryHost: {
      state: 'healthy',
      code_revision: revision,
      electron_ui_revision: revision,
      electron_ui_recovery: { alive: true }
    }
  };
  fixture.render(snapshot);
  assert.equal(fixture.elements.get('#runtimeClosureState').textContent, 'CONNECTOR_CONTRACT_NOT_CURRENT');
  assert.equal(fixture.elements.get('#activationClosureNotice').hidden, false);
  assert.match(fixture.elements.get('#runtimeClosureMeta').textContent, /NOT_RELEASED.*NOT_CLAIMED/);

  snapshot.status.activationClosure.closure_state = 'LIVE_CLOSED';
  fixture.render(snapshot);
  assert.equal(fixture.elements.get('#runtimeClosureState').textContent, 'LIVE_CLOSED');
  assert.equal(fixture.elements.get('#activationClosureNotice').hidden, true);
});

test('heartbeat code clears omitted closure and connector receipts instead of retaining stale green state', () => {
  const source = fs.readFileSync(path.resolve(__dirname, '..', 'renderer', 'app.js'), 'utf8');
  const start = source.indexOf('function applyHeartbeat');
  const end = source.indexOf('async function loadLogs');
  assert.ok(start >= 0 && end > start);
  const snapshot = {
    status: {
      activationClosure: { closure_state: 'LIVE_CLOSED' },
      connectorContractState: 'CURRENT_ACKNOWLEDGED',
      connectorRefreshRequired: false
    }
  };
  const context = vm.createContext({
    state: { snapshot },
    Object,
    Boolean,
    renderRecoveryTunnelSettings() {},
    renderDevice() {},
    renderRuntimeSourceStatus() {},
    setDot() {},
    $: () => ({ textContent: '' })
  });
  vm.runInContext(source.slice(start, end), context, { filename: 'renderer/app-heartbeat.js' });
  context.__heartbeat = { mcpRunning: true, tunnelRunning: true, fullyReady: true };
  vm.runInContext('applyHeartbeat(__heartbeat)', context);
  assert.equal(Object.hasOwn(snapshot.status, 'activationClosure'), false);
  assert.equal(Object.hasOwn(snapshot.status, 'connectorContractState'), false);
  assert.equal(Object.hasOwn(snapshot.status, 'connectorRefreshRequired'), false);
});
