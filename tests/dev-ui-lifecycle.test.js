'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { EventEmitter } = require('node:events');
const {
  runLifecycle,
  uiObservation,
  unavailableObservation,
  createRuntimeDependencies,
  refreshLifecycle,
  runtimeReadinessFromSnapshot,
  refreshRuntimeReady,
  classifyRefreshEpoch,
  previousRefreshIdentitiesFromRecord,
  readPostMutationRefreshEpoch
} = require('../scripts/dev-ui-lifecycle');
const { RecoveryHost } = require('../electron/services/recoveryHost');

const REVISION = 'a'.repeat(64);
const ACCEPTED_HEAD = 'b'.repeat(40);
const PROOF_FINGERPRINT = 'c'.repeat(64);

test('package start contract uses stable start/focus while full refresh stays explicit', () => {
  const packageJson = JSON.parse(fs.readFileSync(path.resolve(__dirname, '..', 'package.json'), 'utf8'));
  assert.equal(packageJson.scripts.start, 'node scripts/dev-ui-lifecycle.js start');
  assert.equal(packageJson.scripts.dev, packageJson.scripts.start);
  assert.equal(packageJson.scripts['dev:refresh'], 'node scripts/dev-ui-lifecycle.js refresh');
  assert.equal(packageJson.scripts['dev:control-center'], 'node scripts/dev-ui-lifecycle.js control-center');
});

test('development lifecycle keeps the operator UI visible while helper signals stay hidden', async () => {
  const launches = [];
  const spawnProcess = (command, args, options) => {
    const child = new EventEmitter();
    child.pid = 43001 + launches.length;
    child.unref = () => {};
    launches.push({ command, args, options });
    queueMicrotask(() => {
      child.emit('spawn');
      if (!options.detached) child.emit('exit', 0);
    });
    return child;
  };
  const deps = createRuntimeDependencies({
    paths: {
      runtimeIdentity: () => ({ runtime_mode: 'development', installation_id: 'c'.repeat(64) }),
      executablePath: () => process.execPath,
      appRoot: () => path.resolve(__dirname, '..')
    },
    spawnProcess,
    output: () => {},
    sleep: async () => {}
  });

  await deps.launch();
  await deps.signal('focus', 'electron-ui-instance-0001');

  assert.equal(launches.length, 2);
  assert.equal(launches[0].options.detached, true);
  assert.equal(launches[0].options.windowsHide, false, 'the operator-facing BrowserWindow must be allowed to show');
  assert.equal(launches[0].options.env.WEBCODEX_PROCESS_ROLE, 'electron-ui');
  assert.equal(launches[1].options.detached, false);
  assert.equal(launches[1].options.windowsHide, true, 'the short-lived lifecycle helper must not create a console window');
});

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
      runtimeReadyTimeoutMs: 0,
      runtimeReadiness: async () => ({
        ready: true,
        reason: 'ready',
        mcpRunning: true,
        nativeAlive: true,
        tunnelRunning: true
      }),
      pollMs: 1
    }
  };
}

function activeRefreshRecord({
  epoch = 'full-clean-refresh-reconcile-epoch-0001',
  operation = 'full-clean-refresh-reconcile-operation-0001',
  state = 'VERIFYING',
  expiresAtUnixMs = Date.now() + 60_000,
  overrides = {}
} = {}) {
  return {
    operation_id: operation,
    activation_epoch_id: epoch,
    mode: 'full_clean_activation',
    state,
    admission_state: state === 'READY' ? 'OPEN' : 'CLOSED',
    expires_at_unix_ms: expiresAtUnixMs,
    source_checkpoint: null,
    metadata: { refresh: true },
    request_intent: {
      operation_id: operation,
      mode: 'full_clean_activation',
      source_checkpoint: null,
      metadata: { refresh: true }
    },
    component_evidence: {
      recovery_host: { instance_id: 'old-recovery-host-0001', pid: 41001 },
      electron_ui: { instance_id: 'old-electron-ui-0001', pid: 42001, process_start_token: 'old-ui-token-0001' },
      coding_mcp: {
        process_instance_id: 'old-coding-mcp-process-0001',
        server_instance_id: 'old-coding-mcp-server-0001',
        supervisor_instance_id: 'old-coding-mcp-supervisor-0001',
        pid: 44001
      },
      coding_tunnel: { instance_id: 'old-coding-tunnel-0001', pid: 44002 },
      recovery_mcp: { instance_id: 'old-recovery-mcp-0001', pid: 44003 },
      recovery_tunnel: { instance_id: 'old-recovery-tunnel-0001', pid: 44004 }
    },
    verification: {
      activation_epoch_id: epoch,
      host_pid: 45000,
      process_identity_verified: true,
      process_identity_changed: true,
      tunnel_identity_changed: true,
      tunnel_health_verified: true,
      recovery_host_revision_matches: true,
      recovery_host_epoch_matches: true,
      ui_verified: true,
      ui_instance_id: 'new-electron-ui-0001',
      recovery_mcp_pid: 45003,
      recovery_tunnel_pid: 45004,
      recovery_plane_identity_changed: true,
      recovery_plane_epoch_matches: true,
      recovery_plane_verified: true,
      projection_rebuild_verified: true,
      workspace_matches: true,
      device_matches: true,
      revision_matches: true,
      epoch_matches: true,
      connector_validation: {
        valid: false,
        reasons: ['CURRENT_CONTRACT_NOT_REDISCOVERED']
      },
      runtime: {
        mcpRunning: true,
        tunnelRunning: true,
        nativeAlive: true,
        fullyReady: false,
        connectorContractState: 'CHANGED_NEEDS_DISCOVERY',
        activationEpoch: { activation_epoch_id: epoch, admission_open: false },
        codeRevision: { codingMcp: { running_revision: REVISION, disk_revision: REVISION } }
      }
    },
    ...overrides
  };
}

function runtimeStatusHarness() {
  const source = fs.readFileSync(path.resolve(__dirname, '..', 'renderer', 'app.js'), 'utf8');
  const start = source.indexOf('function isCentralExecutor');
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
  assert.match(fixture.lines.at(-1), /runtime=ready mcp_running=true native_alive=true tunnel_running=true/);
});

test('start postflight accepts a central executor without a local tunnel and keeps direct legacy fail-closed', async () => {
  const centralRuntime = runtimeReadinessFromSnapshot({
    executionRole: 'central_executor',
    mcpRunning: true,
    nativeAlive: true,
    tunnelRunning: false,
    centralConnected: true,
    authorityReady: true,
    fullyReady: true,
    connectorRediscovered: false,
    connectorRefreshRequired: true
  }, { ready: true });
  assert.equal(centralRuntime.ready, true);
  assert.equal(centralRuntime.executionRole, 'central_executor');
  assert.equal(centralRuntime.tunnelRequired, false);
  assert.equal(centralRuntime.tunnelRunning, false);

  const fixture = harness(observation('CURRENT'));
  fixture.deps.runtimeReadiness = async () => centralRuntime;
  await runLifecycle('start', fixture.deps);
  assert.match(fixture.lines.at(-1), /runtime=ready mcp_running=true native_alive=true tunnel_running=false/);
  assert.equal(fixture.lines.some((line) => line.includes('RUNTIME_UNAVAILABLE')), false);

  const directLegacy = runtimeReadinessFromSnapshot({
    executionRole: 'direct_legacy',
    mcpRunning: true,
    nativeAlive: true,
    tunnelRunning: false,
    centralConnected: true,
    authorityReady: true
  });
  assert.equal(directLegacy.ready, false);
  assert.equal(directLegacy.tunnelRequired, true);
  assert.equal(directLegacy.reason, 'runtime_components_not_ready');
});

test('dev:control-center opens the manager through the exact current Electron instance', async () => {
  const fixture = harness(observation('CURRENT'));
  const result = await runLifecycle('control-center', fixture.deps);
  assert.equal(result.ui.state, 'CURRENT');
  assert.deepEqual(fixture.calls, ['signal:control-center:electron-ui-instance-0001']);
  assert.match(fixture.lines.at(-1), /DEV_UI CONTROL_CENTER action=open pid=42001 instance=electron-ui-instance-0001/);
  assert.match(fixture.lines.at(-1), new RegExp(`running_revision=${REVISION} disk_revision=${REVISION}`));
});

test('start bootstraps an absent or dead host through the guarded full-clean lifecycle', async (t) => {
  for (const code of ['ENOENT', 'RECOVERY_DESCRIPTOR_STALE']) {
    await t.test(code, async () => {
      const fixture = harness(unavailableObservation({ code }));
      fixture.deps.ensureRefreshHost = async () => {
        fixture.calls.push('ensure-refresh-host');
        fixture.current = observation('MISSING');
        return fixture.current;
      };
      fixture.deps.refresh = async () => {
        fixture.calls.push('guarded-full-clean');
        throw Object.assign(new Error('canonical census blocks mutation'), { code: 'RUNTIME_BUSY' });
      };
      await assert.rejects(runLifecycle('start', fixture.deps), { code: 'RUNTIME_BUSY' });
      assert.deepEqual(fixture.calls, ['ensure-refresh-host', 'guarded-full-clean']);
      assert.match(fixture.lines[0], /START action=cold_start reason=host_absent/);
    });
  }
});

test('start uses a new guarded epoch when fresh telemetry and PID state prove both primary services stopped', async () => {
  const fixture = harness(observation('MISSING'));
  fixture.deps.runtimeSnapshot = async () => ({
    telemetryAvailable: true, signalStale: false,
    mcpRunning: false, nativeAlive: false, tunnelRunning: false
  });
  fixture.deps.runtimeState = () => ({ nativePid: 44111, tunnelPid: 44112 });
  fixture.deps.processAlive = () => false;
  fixture.deps.refresh = async () => {
    fixture.calls.push('guarded-full-clean');
    throw Object.assign(new Error('source/ledger guard'), { code: 'RUNTIME_BUSY' });
  };
  await assert.rejects(runLifecycle('start', fixture.deps), { code: 'RUNTIME_BUSY' });
  assert.deepEqual(fixture.calls, ['guarded-full-clean']);
  assert.match(fixture.lines[0], /START action=cold_start reason=runtime_stopped/);
});

test('start never turns uncertain, partial, busy or still-live service evidence into a refresh', async (t) => {
  const stopped = { telemetryAvailable: true, signalStale: false, mcpRunning: false, nativeAlive: false, tunnelRunning: false };
  for (const patch of [
    { signalStale: true }, { telemetryAvailable: false }, { snapshotBusy: true },
    { busy: true }, { recovering: true }, { nativeAlive: true }, { tunnelRunning: true },
    { livePid: true }, { manualStop: true }, { snapshotFailure: true }
  ]) {
    await t.test(JSON.stringify(patch), async () => {
      const fixture = harness(observation('CURRENT'));
      fixture.deps.runtimeSnapshot = async () => {
        if (patch.snapshotFailure) throw Object.assign(new Error('unavailable'), { code: 'RECOVERY_REQUEST_TIMEOUT' });
        return { ...stopped, ...patch };
      };
      fixture.deps.runtimeState = () => ({ nativePid: 44111, manualStop: patch.manualStop });
      fixture.deps.processAlive = () => patch.livePid === true;
      fixture.deps.refresh = async () => assert.fail('uncertainty is not refresh authority');
      fixture.deps.runtimeReadiness = async () => ({ ready: false, reason: 'runtime_readiness_unverified' });
      await assert.rejects(runLifecycle('start', fixture.deps), { code: 'DEV_UI_RUNTIME_UNAVAILABLE' });
      assert.deepEqual(fixture.calls, ['signal:focus:electron-ui-instance-0001']);
    });
  }
});

test('start refuses an unreachable host without bootstrapping over an uncertain owner', async () => {
  const fixture = harness(unavailableObservation({ code: 'ECONNREFUSED' }));
  fixture.deps.ensureRefreshHost = async () => assert.fail('do not infer absence from transport failure');
  await assert.rejects(runLifecycle('start', fixture.deps), { code: 'DEV_UI_HOST_UNAVAILABLE' });
  assert.deepEqual(fixture.calls, []);
});

test('dev reports UI_CURRENT and fails typed when Recovery Host backend is not ready', async () => {
  const fixture = harness(observation('CURRENT'));
  fixture.deps.runtimeReadiness = async () => ({
    ready: false,
    reason: 'recovery_host_not_ready',
    error_code: 'RECOVERY_BOOTSTRAP_IN_PROGRESS',
    mcpRunning: false,
    nativeAlive: false,
    tunnelRunning: false
  });

  await assert.rejects(runLifecycle('start', fixture.deps), (error) => {
    assert.equal(error.code, 'DEV_UI_RUNTIME_UNAVAILABLE');
    assert.equal(error.details.reason, 'recovery_host_not_ready');
    return true;
  });

  assert.match(fixture.lines.at(-2), /DEV_UI UI_CURRENT action=start .*runtime=unavailable reason=recovery_host_not_ready/);
  assert.match(fixture.lines.at(-1), /DEV_UI RUNTIME_UNAVAILABLE action=start reason=recovery_host_not_ready error_code=RECOVERY_BOOTSTRAP_IN_PROGRESS/);
  assert.equal(fixture.lines.some((line) => line.startsWith('DEV_UI CURRENT ')), false);
});

test('refresh tolerates only a bounded transient epoch-store read failure after the supported process mutation', async () => {
  const epoch = activeRefreshRecord();
  let reads = 0;
  let sleeps = 0;
  const classified = await readPostMutationRefreshEpoch({
    activationRecordStrict: () => {
      reads += 1;
      if (reads === 1) {
        throw Object.assign(new Error('backup projection is being replaced'), {
          code: 'ACTIVATION_EPOCH_STORE_INVALID'
        });
      }
      return epoch;
    },
    sleep: async () => { sleeps += 1; },
    pollMs: 0,
    epochReadRetryTimeoutMs: 100
  }, epoch.operation_id, 'locating_refresh_epoch');

  assert.equal(classified.kind, 'active');
  assert.equal(classified.operationId, epoch.operation_id);
  assert.equal(reads, 2);
  assert.equal(sleeps, 1);
  await assert.rejects(readPostMutationRefreshEpoch({
    activationRecordStrict: () => {
      throw Object.assign(new Error('persistent corruption'), {
        code: 'ACTIVATION_EPOCH_STORE_INVALID'
      });
    },
    sleep: async () => {},
    pollMs: 0,
    epochReadRetryTimeoutMs: 0
  }, epoch.operation_id, 'locating_refresh_epoch'), (error) => {
    assert.equal(error.code, 'DEV_UI_REFRESH_EPOCH_UNCERTAIN');
    assert.equal(error.details.operation_id, epoch.operation_id);
    assert.equal(error.details.phase, 'locating_refresh_epoch');
    assert.equal(error.details.cause_code, 'ACTIVATION_EPOCH_STORE_INVALID');
    return true;
  });
});

test('dev:status reports lifecycle state without signaling or activating the UI', async () => {
  const fixture = harness(observation('STALE'));
  const result = await runLifecycle('status', fixture.deps);
  assert.equal(result.ui.state, 'STALE');
  assert.deepEqual(fixture.calls, []);
  assert.match(fixture.lines.at(-1), /DEV_UI STATUS state=STALE host=available installation=current/);
  assert.match(fixture.lines.at(-1), /running_revision=b+ disk_revision=a+/);
  assert.match(fixture.lines.at(-1), /connector_rediscovered=unknown/);
});

test('dev:status scopes UI revision and exposes MCP drift plus aggregate runtime freshness', async () => {
  const fixture = harness(observation('CURRENT'));
  const mcpRunningRevision = 'b'.repeat(64);
  const mcpDiskRevision = 'c'.repeat(64);
  fixture.deps.runtimeSnapshot = async () => ({
    codeRevision: {
      codingMcp: {
        state: 'update_pending',
        running_revision: mcpRunningRevision,
        disk_revision: mcpDiskRevision,
        update_pending: true,
        checked_at: '2026-08-30T00:47:29.905Z'
      }
    },
    componentsReady: false,
    fullyReady: false,
    updateIncomplete: true,
    telemetryAvailable: true,
    signalStale: false,
    snapshotSource: 'recovery_host_supervision_cache',
    snapshotAgeMs: 1250
  });

  const result = await runLifecycle('status', fixture.deps);

  assert.equal(result.ui.state, 'CURRENT');
  assert.deepEqual(fixture.calls, []);
  const line = fixture.lines.at(-1);
  assert.match(line, new RegExp(`state=CURRENT .*running_revision=${REVISION} disk_revision=${REVISION}`));
  assert.match(line, /revision_scope=electron_ui/);
  assert.match(line, /mcp_revision_state=update_pending/);
  assert.match(line, new RegExp(`mcp_running_revision=${mcpRunningRevision}`));
  assert.match(line, new RegExp(`mcp_disk_revision=${mcpDiskRevision}`));
  assert.match(line, /mcp_update_pending=true/);
  assert.match(line, /components_ready=false fully_ready=false runtime_update_incomplete=true/);
  assert.match(line, /runtime_telemetry_available=true runtime_signal_stale=false/);
  assert.match(line, /runtime_snapshot_source=recovery_host_supervision_cache runtime_snapshot_age_ms=1250/);
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

test('dev:status falls back to the durable activation census when the live snapshot times out', async () => {
  const fixture = harness(observation('CURRENT'));
  const epoch = 'status-timeout-activation-epoch-0001';
  fixture.deps.runtimeSnapshot = async () => {
    throw Object.assign(new Error('busy census'), { code: 'RECOVERY_REQUEST_TIMEOUT' });
  };
  fixture.deps.activationRecord = () => ({
    activation_epoch_id: epoch,
    state: 'VERIFYING',
    verification: {
      activation_epoch_id: epoch,
      runtime: {
        toolContract: { sha256: 'f'.repeat(64) },
        connectorContractAcknowledgedSha256: 'e'.repeat(64),
        connectorContractState: 'CHANGED_NEEDS_DISCOVERY',
        connectorRefreshRequired: true,
        connectorAcknowledgementPending: false,
        connectorRediscovered: false,
        connectorRediscoveredAt: null
      }
    }
  });

  await runLifecycle('status', fixture.deps);

  const line = fixture.lines.at(-1);
  assert.match(line, /DEV_UI STATUS state=CURRENT host=available installation=current/);
  assert.match(line, /connector_state=CHANGED_NEEDS_DISCOVERY/);
  assert.match(line, /connector_rediscovered=false/);
  assert.match(line, /connector_refresh_required=true/);
  assert.match(line, /connector_ack_pending=false/);
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

test('dev:refresh refreshes the whole owned runtime and keeps connector readiness explicit', async () => {
  const fixture = harness(observation('CURRENT'));
  const oldHost = fixture.current.descriptor.instance_id;
  const oldUi = fixture.current.ui.instanceId;
  const epoch = 'full-clean-refresh-test-0001';
  fixture.deps.refresh = async () => {
    fixture.current = {
      ...observation('CURRENT', 'fresh-ui-instance-0000001', 43001),
      descriptor: {
        ...fixture.current.descriptor,
        instance_id: 'fresh-recovery-host-0001',
        activation_epoch_id: epoch
      }
    };
    return { operationId: 'full-clean-refresh-test-operation-0001', result: { activation_epoch_id: epoch } };
  };
  fixture.deps.runtimeSnapshot = async () => ({
    mcpRunning: true,
    tunnelRunning: true,
    nativeAlive: true,
    fullyReady: false,
    connectorContractState: 'UNAVAILABLE',
    activationEpoch: { activation_epoch_id: epoch, admission_open: false },
    codeRevision: { codingMcp: { running_revision: REVISION, disk_revision: REVISION } }
  });
  fixture.deps.runtimeState = () => ({
    nativePid: 44001,
    tunnelPid: 44002,
    nativeInstanceId: 'fresh-mcp-supervisor-0001',
    tunnelInstanceId: 'fresh-coding-tunnel-0001',
    nativeActivationEpochId: epoch,
    tunnelActivationEpochId: epoch
  });
  fixture.deps.processAlive = () => true;

  const result = await runLifecycle('refresh', fixture.deps);
  assert.equal(result.epochId, epoch);
  assert.notEqual(result.descriptor.instance_id, oldHost);
  assert.notEqual(result.ui.instanceId, oldUi);
  assert.equal(result.readiness.mcpRunning, true);
  assert.equal(result.readiness.tunnelRunning, true);
  assert.equal(result.runtime.fullyReady, false, 'connector gate must not be invented by npm start');
  assert.match(fixture.lines[0], /DEV_UI REFRESH action=full_clean/);
  assert.match(fixture.lines.at(-1), /DEV_UI REFRESHED .*activation=VERIFYING .*admission=closed fully_ready=false connector=pending connector_state=UNAVAILABLE/);
});

test('dev:refresh exits successfully after exact process refresh while connector discovery remains pending', async () => {
  const fixture = harness(observation('CURRENT'));
  const operationId = 'full-clean-refresh-exact-operation-0001';
  const epoch = 'full-clean-refresh-exact-epoch-0001';
  const oldState = {
    nativePid: 44001,
    tunnelPid: 44002,
    nativeInstanceId: 'old-mcp-supervisor-instance-01',
    tunnelInstanceId: 'old-coding-tunnel-instance-01'
  };
  const newState = {
    nativePid: 45001,
    tunnelPid: 45002,
    nativeInstanceId: 'new-mcp-supervisor-instance-01',
    tunnelInstanceId: 'new-coding-tunnel-instance-01',
    nativeActivationEpochId: epoch,
    tunnelActivationEpochId: epoch
  };
  let runtimeStateReads = 0;
  fixture.deps.runtimeState = () => (++runtimeStateReads === 1 ? oldState : newState);
  fixture.deps.recoveryPlaneState = () => ({
    recoveryMcpPid: 44003,
    recoveryTunnelPid: 44004,
    recoveryMcpInstanceId: 'old-recovery-mcp-instance-001',
    recoveryTunnelInstanceId: 'old-recovery-tunnel-instance-1'
  });
  fixture.deps.refresh = async () => ({ operationId, result: { activation_epoch_id: epoch } });
  fixture.deps.descriptor = () => ({
    owner_pid: 45000,
    instance_id: 'new-recovery-host-instance-0001',
    activation_epoch_id: epoch
  });
  const runtime = {
    mcpRunning: true,
    // This is the earlier lightweight observation. The exact tunnel probe in
    // the same final census below is the stronger postflight receipt.
    tunnelRunning: false,
    nativeAlive: true,
    fullyReady: false,
    connectorContractState: 'CHANGED_NEEDS_DISCOVERY',
    activationEpoch: { activation_epoch_id: epoch, admission_open: false },
    codeRevision: { codingMcp: { running_revision: REVISION, disk_revision: REVISION } }
  };
  fixture.deps.activationRecord = () => ({
    operation_id: operationId,
    activation_epoch_id: epoch,
    state: 'VERIFYING',
    admission_state: 'CLOSED',
    verification: {
      activation_epoch_id: epoch,
      host_pid: 45000,
      process_identity_verified: true,
      process_identity_changed: true,
      tunnel_identity_changed: true,
      tunnel_health_verified: true,
      recovery_host_revision_matches: true,
      recovery_host_epoch_matches: true,
      ui_verified: true,
      ui_instance_id: 'new-electron-ui-instance-0001',
      recovery_mcp_pid: 45003,
      recovery_tunnel_pid: 45004,
      recovery_plane_identity_changed: true,
      recovery_plane_epoch_matches: true,
      recovery_plane_verified: true,
      projection_rebuild_verified: true,
      workspace_matches: true,
      device_matches: true,
      revision_matches: true,
      epoch_matches: true,
      connector_validation: {
        valid: false,
        code: 'UPDATE_INCOMPLETE',
        reasons: [
          'CURRENT_CONTRACT_NOT_REDISCOVERED',
          'ACKNOWLEDGED_SHA256_MISMATCH',
          'STATUS_NOT_REDISCOVERED',
          'CONNECTOR_REFRESH_REQUIRED',
          'CONNECTOR_CONTRACT_CHANGED',
          'CONNECTOR_CONTRACT_STATE_INVALID'
        ]
      },
      runtime
    }
  });
  fixture.deps.processAlive = () => true;

  const result = await runLifecycle('refresh', fixture.deps);
  assert.equal(result.epochId, epoch);
  assert.equal(result.readiness.componentCensusVerified, true);
  assert.equal(result.readiness.freshPids, true);
  assert.equal(result.readiness.tunnelRunning, true);
  assert.equal(result.runtime.tunnelRunning, false, 'the stale lightweight bit remains visible as evidence');
  assert.match(fixture.lines.at(-1), /DEV_UI REFRESHED .*activation=VERIFYING .*mcp=ready tunnel=ready admission=closed fully_ready=false connector=pending connector_state=CHANGED_NEEDS_DISCOVERY/);
});

test('dev:status exposes role-aware central readiness without exposing raw status errors', async () => {
  const fixture = harness(observation('CURRENT'));
  fixture.deps.runtimeSnapshot = async () => ({
    executionRole: 'central_executor',
    centralConnected: true,
    authorityReady: true,
    centralStatusReason: null,
    connectorRediscovered: false,
    connectorRefreshRequired: true
  });

  await runLifecycle('status', fixture.deps);

  const line = fixture.lines.at(-1);
  assert.match(line, /execution_role=central_executor/);
  assert.match(line, /central_connected=true authority_ready=true central_status_reason=none/);
  assert.match(line, /connector_rediscovered=false connector_rediscovered_at=none/);
});

test('central-executor refresh accepts route proof without inventing a Coding Tunnel', () => {
  const epoch = 'activation-central-refresh-0001';
  const runtime = {
    executionRole: 'central_executor',
    mcpRunning: true,
    tunnelRunning: false,
    nativeAlive: true,
    activationEpoch: { activation_epoch_id: epoch, admission_open: true },
    codeRevision: { codingMcp: { running_revision: REVISION, disk_revision: REVISION } }
  };
  const state = {
    nativePid: 45001,
    nativeInstanceId: 'central-mcp-instance-0001',
    nativeActivationEpochId: epoch,
    tunnelPid: null,
    tunnelInstanceId: null
  };
  const record = {
    verification: {
      final_census: {
        activation_epoch_id: epoch,
        execution_role: 'central_executor',
        tunnel_required: false,
        host_pid: 45000,
        recovery_mcp_pid: 45003,
        process_identity_verified: true,
        process_identity_changed: true,
        tunnel_identity_changed: null,
        tunnel_health_verified: false,
        recovery_host_revision_matches: true,
        recovery_host_epoch_matches: true,
        ui_verified: true,
        recovery_plane_identity_changed: true,
        recovery_plane_epoch_matches: true,
        recovery_plane_verified: true,
        projection_rebuild_verified: true,
        workspace_matches: true,
        device_matches: true,
        revision_matches: true,
        epoch_matches: true,
        central_connected: true,
        authority_ready: true,
        central_route_verified: true
      }
    }
  };

  const readiness = refreshRuntimeReady(runtime, state, epoch, () => true, record);

  assert.equal(readiness.executionRole, 'central_executor');
  assert.equal(readiness.tunnelRequired, false);
  assert.equal(readiness.tunnelRunning, false);
  assert.equal(readiness.processIdentitiesPresent, true);
  assert.equal(readiness.ownedProcessesAlive, true);
  assert.equal(readiness.freshPids, true);
  assert.equal(readiness.componentCensusVerified, true);
});

test('dev:refresh accepts a central executor without a local tunnel', async () => {
  const fixture = harness(observation('CURRENT'));
  const operationId = 'full-clean-refresh-central-operation-0001';
  const epoch = 'full-clean-refresh-central-epoch-0001';
  const oldState = {
    nativePid: 44001,
    tunnelPid: null,
    nativeInstanceId: 'old-central-mcp-instance-01',
    tunnelInstanceId: null,
    nativeActivationEpochId: 'old-central-epoch-0001',
    tunnelActivationEpochId: null,
    executionRole: 'central_executor'
  };
  const newState = {
    nativePid: 45001,
    tunnelPid: null,
    nativeInstanceId: 'new-central-mcp-instance-01',
    tunnelInstanceId: null,
    nativeActivationEpochId: epoch,
    tunnelActivationEpochId: null,
    executionRole: 'central_executor'
  };
  let runtimeStateReads = 0;
  fixture.deps.runtimeState = () => (++runtimeStateReads === 1 ? oldState : newState);
  fixture.deps.refresh = async () => ({ operationId, result: { activation_epoch_id: epoch } });
  fixture.deps.descriptor = () => ({
    owner_pid: 45000,
    instance_id: 'new-central-recovery-host-0001',
    activation_epoch_id: epoch
  });
  fixture.deps.activationRecord = () => ({
    operation_id: operationId,
    activation_epoch_id: epoch,
    state: 'READY',
    admission_state: 'OPEN',
    metadata: { execution_role: 'central_executor' },
    verification: {
      activation_epoch_id: epoch,
      execution_role: 'central_executor',
      tunnel_required: false,
      host_pid: 45000,
      process_identity_verified: true,
      process_identity_changed: true,
      recovery_host_revision_matches: true,
      recovery_host_epoch_matches: true,
      ui_verified: true,
      ui_instance_id: 'new-central-electron-ui-0001',
      recovery_plane_identity_changed: true,
      recovery_plane_epoch_matches: true,
      recovery_plane_verified: true,
      projection_rebuild_verified: true,
      workspace_matches: true,
      device_matches: true,
      revision_matches: true,
      epoch_matches: true,
      central_connected: true,
      authority_ready: true,
      central_route_verified: true,
      runtime: {
        executionRole: 'central_executor',
        mcpRunning: true,
        nativeAlive: true,
        tunnelRunning: false,
        fullyReady: true,
        connectorContractState: 'CHANGED_NEEDS_DISCOVERY',
        activationEpoch: { activation_epoch_id: epoch, admission_open: true },
        codeRevision: { codingMcp: { running_revision: REVISION, disk_revision: REVISION } }
      }
    }
  });
  fixture.deps.processAlive = () => true;

  const result = await runLifecycle('refresh', fixture.deps);
  assert.equal(result.epochId, epoch);
  assert.equal(result.readiness.executionRole, 'central_executor');
  assert.equal(result.readiness.tunnelRequired, false);
  assert.equal(result.readiness.tunnelRunning, false);
  assert.equal(result.readiness.processIdentitiesPresent, true);
  assert.equal(result.readiness.ownedProcessesAlive, true);
  assert.equal(result.readiness.componentCensusVerified, true);
  assert.equal(result.readiness.freshPids, true);
  assert.match(fixture.lines.at(-1), /mcp=ready tunnel=not-required admission=open fully_ready=true connector=pending connector_state=CHANGED_NEEDS_DISCOVERY/);
});

test('dev:refresh bootstraps a missing Recovery Host and then performs the same full refresh', async () => {
  const fixture = harness(unavailableObservation(Object.assign(new Error('missing'), { code: 'ENOENT' })));
  const epoch = 'full-clean-refresh-cold-0001';
  fixture.deps.ensureRefreshHost = async () => {
    fixture.calls.push('ensure-refresh-host');
    fixture.current = observation('CURRENT', 'bootstrap-ui-instance-0001', 43011);
    fixture.current.descriptor = {
      ...fixture.current.descriptor,
      owner_pid: 43010,
      instance_id: 'bootstrap-recovery-host-0001'
    };
    return fixture.current;
  };
  fixture.deps.refresh = async () => {
    fixture.calls.push('full-clean-refresh');
    fixture.current = observation('CURRENT', 'cold-refresh-ui-instance-001', 43021);
    fixture.current.descriptor = {
      ...fixture.current.descriptor,
      owner_pid: 43020,
      instance_id: 'cold-refresh-recovery-host-01',
      activation_epoch_id: epoch
    };
    return {
      operationId: 'full-clean-refresh-cold-operation-0001',
      result: { activation_epoch_id: epoch }
    };
  };
  fixture.deps.runtimeSnapshot = async () => ({
    mcpRunning: true,
    tunnelRunning: true,
    nativeAlive: true,
    fullyReady: false,
    connectorContractState: 'UNAVAILABLE',
    activationEpoch: { activation_epoch_id: epoch, admission_open: false },
    codeRevision: { codingMcp: { running_revision: REVISION, disk_revision: REVISION } }
  });
  fixture.deps.runtimeState = () => ({
    nativePid: 44011,
    tunnelPid: 44012,
    nativeInstanceId: 'cold-refresh-mcp-instance-01',
    tunnelInstanceId: 'cold-refresh-tunnel-inst-01',
    nativeActivationEpochId: epoch,
    tunnelActivationEpochId: epoch
  });
  fixture.deps.processAlive = () => true;

  const result = await runLifecycle('refresh', fixture.deps);
  assert.equal(result.epochId, epoch);
  assert.deepEqual(fixture.calls, ['ensure-refresh-host', 'full-clean-refresh']);
  assert.match(fixture.lines[0], /DEV_UI REFRESH bootstrap=RecoveryHost source=current-checkout/);
  assert.match(fixture.lines.at(-1), /DEV_UI REFRESHED .*activation=VERIFYING .*admission=closed fully_ready=false connector=pending/);
});

test('refresh reconciles an unexpired durable epoch without invoking a second full-clean operation', async () => {
  const fixture = harness(observation('CURRENT', 'new-electron-ui-0001', 45001));
  const epoch = activeRefreshRecord();
  const operationCalls = [];
  fixture.current.descriptor = {
    ...fixture.current.descriptor,
    instance_id: 'new-recovery-host-0001',
    activation_epoch_id: epoch.activation_epoch_id,
    owner_pid: 45000
  };
  fixture.deps.activationRecord = () => epoch;
  fixture.deps.activationRecordStrict = () => epoch;
  fixture.deps.refresh = async () => {
    operationCalls.push('refresh');
    throw new Error('must not start a competing refresh');
  };
  fixture.deps.descriptor = () => fixture.current.descriptor;
  fixture.deps.runtimeState = () => ({
    nativePid: 45001,
    tunnelPid: 45002,
    nativeInstanceId: 'new-coding-mcp-supervisor-0001',
    tunnelInstanceId: 'new-coding-tunnel-0001',
    nativeActivationEpochId: epoch.activation_epoch_id,
    tunnelActivationEpochId: epoch.activation_epoch_id
  });
  fixture.deps.processAlive = () => true;

  const result = await refreshLifecycle(fixture.deps);
  assert.equal(result.epochId, epoch.activation_epoch_id);
  assert.deepEqual(operationCalls, []);
  assert.match(fixture.lines.find((line) => line.startsWith('DEV_UI REFRESH RECONCILE')),
    /action=full_clean epoch=full-clean-refresh-reconcile-epoch-0001 operation=full-clean-refresh-reconcile-operation-0001/);
});

test('refresh fails closed when an active epoch changes before mutation', async () => {
  const fixture = harness(observation('CURRENT'));
  const first = activeRefreshRecord();
  const changed = activeRefreshRecord({
    epoch: 'full-clean-refresh-reconcile-epoch-0002',
    operation: 'full-clean-refresh-reconcile-operation-0002'
  });
  let reads = 0;
  fixture.deps.activationRecordStrict = () => (++reads === 1 ? first : changed);
  fixture.deps.refresh = async () => { throw new Error('must not refresh after epoch change'); };
  await assert.rejects(refreshLifecycle(fixture.deps), { code: 'DEV_UI_REFRESH_EPOCH_CHANGED' });
});

test('refresh sends an expired validated process-refresh record through the official bootstrap instead of reconciling it', async () => {
  const fixture = harness(observation('CURRENT'));
  const expired = activeRefreshRecord({ expiresAtUnixMs: Date.now() - 1 });
  const refreshedEpoch = 'full-clean-refresh-retried-epoch-0001';
  const refreshedOperation = 'full-clean-refresh-retried-operation-0001';
  const refreshCalls = [];
  let strictReads = 0;
  fixture.deps.activationRecordStrict = () => (++strictReads <= 2 ? expired : null);
  fixture.deps.activationRecord = () => null;
  fixture.deps.refresh = async () => {
    refreshCalls.push('refresh');
    fixture.current = observation('CURRENT', 'retried-electron-ui-instance-001', 46001);
    fixture.current.descriptor = {
      ...fixture.current.descriptor,
      owner_pid: 46000,
      instance_id: 'retried-recovery-host-instance-01',
      activation_epoch_id: refreshedEpoch
    };
    return {
      operationId: refreshedOperation,
      result: { activation_epoch_id: refreshedEpoch }
    };
  };
  fixture.deps.descriptor = () => fixture.current.descriptor;

  await assert.rejects(refreshLifecycle(fixture.deps), { code: 'DEV_UI_REFRESH_POSTFLIGHT_FAILED' });
  assert.deepEqual(refreshCalls, ['refresh']);
  assert.match(fixture.lines.find((line) => line.startsWith('DEV_UI REFRESH ')), /action=full_clean/);
  assert.equal(fixture.lines.some((line) => line.startsWith('DEV_UI REFRESH RECONCILE')), false);
});

test('refresh ignores a predecessor FAILED epoch while locating the replacement operation', async () => {
  const fixture = harness(observation('CURRENT'));
  const requestedOperationId = 'full-clean-refresh-new-operation-0001';
  const newEpochId = 'activation-new-refresh-epoch-0001';
  const predecessor = activeRefreshRecord({
    epoch: 'activation-predecessor-failed-0001',
    operation: 'full-clean-refresh-predecessor-0001',
    state: 'FAILED',
    overrides: {
      admission_state: 'CLOSED',
      failed_at_unix_ms: Date.now(),
      error: { code: 'ACTIVATION_REQUEST_EXPIRED', message: 'predecessor expired' }
    }
  });
  const active = activeRefreshRecord({
    epoch: newEpochId,
    operation: requestedOperationId,
    state: 'VERIFYING'
  });
  const observedOperations = [];
  let strictReads = 0;
  fixture.deps.activationRecordStrict = () => {
    strictReads += 1;
    const record = strictReads <= 3 ? predecessor : active;
    observedOperations.push(record.operation_id);
    return record;
  };
  fixture.deps.activationRecord = () => active;
  let refreshCalls = 0;
  fixture.deps.refresh = async () => {
    refreshCalls += 1;
    return { operationId: requestedOperationId, result: {} };
  };
  const replacementDescriptor = {
    ...fixture.current.descriptor,
    owner_pid: 45000,
    instance_id: 'replacement-host-for-new-operation-01',
    activation_epoch_id: newEpochId
  };
  let descriptorReads = 0;
  fixture.deps.descriptor = () => (++descriptorReads === 1
    ? fixture.current.descriptor
    : replacementDescriptor);
  const oldState = {
    nativePid: 44001,
    tunnelPid: 44002,
    nativeInstanceId: 'old-mcp-supervisor-instance-01',
    tunnelInstanceId: 'old-coding-tunnel-instance-01'
  };
  const replacementState = {
    nativePid: 45001,
    tunnelPid: 45002,
    nativeInstanceId: 'replacement-mcp-instance-0001',
    tunnelInstanceId: 'replacement-tunnel-instance-01',
    nativeActivationEpochId: newEpochId,
    tunnelActivationEpochId: newEpochId
  };
  let runtimeStateReads = 0;
  fixture.deps.runtimeState = () => (++runtimeStateReads === 1 ? oldState : replacementState);
  fixture.deps.recoveryPlaneState = () => ({
    recoveryMcpPid: 44003,
    recoveryTunnelPid: 44004,
    recoveryMcpInstanceId: 'old-recovery-mcp-instance-001',
    recoveryTunnelInstanceId: 'old-recovery-tunnel-instance-1'
  });
  fixture.deps.processAlive = () => true;

  const result = await refreshLifecycle(fixture.deps);
  assert.equal(result.epochId, newEpochId);
  assert.equal(result.refresh.operationId, requestedOperationId);
  assert.equal(result.descriptor.instance_id, replacementDescriptor.instance_id);
  assert.equal(result.ui.instanceId, 'new-electron-ui-0001');
  assert.equal(result.readiness.componentCensusVerified, true);
  assert.equal(result.readiness.freshPids, true);
  assert.equal(refreshCalls, 1, 'the predecessor observation must not start a second refresh request');
  assert.deepEqual(observedOperations, [
    predecessor.operation_id,
    predecessor.operation_id,
    predecessor.operation_id,
    requestedOperationId
  ]);
});

test('refresh still throws a FAILED epoch belonging to the requested replacement operation', async () => {
  const fixture = harness(observation('CURRENT'));
  const requestedOperationId = 'full-clean-refresh-failed-operation-0001';
  const predecessor = activeRefreshRecord({
    epoch: 'activation-prior-failed-epoch-0001',
    operation: 'full-clean-refresh-prior-operation-0001',
    state: 'FAILED',
    overrides: {
      admission_state: 'CLOSED',
      failed_at_unix_ms: Date.now(),
      error: { code: 'ACTIVATION_REQUEST_EXPIRED', message: 'prior operation expired' }
    }
  });
  const requestedFailure = activeRefreshRecord({
    epoch: 'activation-requested-failed-epoch-0001',
    operation: requestedOperationId,
    state: 'FAILED',
    overrides: {
      admission_state: 'CLOSED',
      failed_at_unix_ms: Date.now(),
      error: { code: 'REQUESTED_REFRESH_FAILED', message: 'requested replacement failed' }
    }
  });
  let strictReads = 0;
  fixture.deps.activationRecordStrict = () => (++strictReads <= 2 ? predecessor : requestedFailure);
  let refreshCalls = 0;
  fixture.deps.refresh = async () => {
    refreshCalls += 1;
    return { operationId: requestedOperationId, result: {} };
  };

  await assert.rejects(refreshLifecycle(fixture.deps), (error) => {
    assert.equal(error.code, 'REQUESTED_REFRESH_FAILED');
    assert.equal(error.message, 'requested replacement failed');
    assert.equal(error.details.operation_id, requestedOperationId);
    return true;
  });
  assert.equal(refreshCalls, 1);
  assert.equal(strictReads, 3);
});

test('refresh fails closed when a reconciled durable epoch expires before mutation', async () => {
  const fixture = harness(observation('CURRENT'));
  const originalNow = Date.now;
  let now = 1_800_000_000_000;
  const expiresAtUnixMs = now + 1_000;
  const epoch = activeRefreshRecord({ expiresAtUnixMs });
  let strictReads = 0;
  let refreshCalls = 0;
  fixture.deps.activationRecordStrict = () => {
    strictReads += 1;
    if (strictReads === 2) now = expiresAtUnixMs;
    return epoch;
  };
  fixture.deps.refresh = async () => {
    refreshCalls += 1;
    throw new Error('must not refresh after reconciliation authority expires');
  };
  Date.now = () => now;
  try {
    await assert.rejects(refreshLifecycle(fixture.deps), (error) => {
      assert.equal(error.code, 'ACTIVATION_REQUEST_EXPIRED');
      assert.equal(error.details.activation_epoch_id, epoch.activation_epoch_id);
      assert.equal(error.details.operation_id, epoch.operation_id);
      assert.equal(error.details.expires_at_unix_ms, expiresAtUnixMs);
      assert.equal(error.details.phase, 'preflight');
      return true;
    });
  } finally {
    Date.now = originalNow;
  }
  assert.equal(strictReads, 2);
  assert.equal(refreshCalls, 0);
});

test('refresh epoch classification routes an expired validated refresh to official retry but leaves READY/open terminal records alone', () => {
  const expired = activeRefreshRecord({ expiresAtUnixMs: Date.now() - 1 });
  assert.equal(classifyRefreshEpoch(expired).kind, 'expired');
  const ready = activeRefreshRecord({
    state: 'READY',
    expiresAtUnixMs: Date.now() - 60_000,
    overrides: {
      epoch_state: 'VERIFYING',
      error: { code: 'ACTIVATION_REQUEST_EXPIRED', message: 'stale nested observation' }
    }
  });
  assert.equal(classifyRefreshEpoch(ready).kind, 'terminal');
  assert.equal(classifyRefreshEpoch(ready).state, 'READY');
  assert.throws(() => previousRefreshIdentitiesFromRecord(activeRefreshRecord({
    overrides: { component_evidence: null }
  })), { code: 'DEV_UI_REFRESH_EPOCH_UNCERTAIN' });
});

test('refresh refuses to adopt an active non-refresh activation epoch', () => {
  const nonRefresh = activeRefreshRecord({
    overrides: {
      mode: 'full_clean_activation',
      metadata: { refresh: false },
      request_intent: {
        operation_id: 'full-clean-refresh-reconcile-operation-0001',
        mode: 'full_clean_activation',
        source_checkpoint: {
          checkpoint_id: 'checkpoint-0000001',
          run_id: 'run-00000001',
          wave_id: 'wave-00000001',
          proof_fingerprint: REVISION,
          git_head: 'a'.repeat(40)
        },
        metadata: { refresh: false }
      },
      source_checkpoint: {
        checkpoint_id: 'checkpoint-0000001',
        run_id: 'run-00000001',
        wave_id: 'wave-00000001',
        proof_fingerprint: REVISION,
        git_head: 'a'.repeat(40)
      }
    }
  });
  assert.throws(() => classifyRefreshEpoch(nonRefresh), { code: 'DEV_UI_REFRESH_EPOCH_CONFLICT' });
  assert.throws(() => classifyRefreshEpoch({
    ...nonRefresh,
    mode: 'soft_recovery',
    metadata: { refresh: true },
    request_intent: {
      operation_id: 'full-clean-refresh-reconcile-operation-0001',
      mode: 'soft_recovery',
      source_checkpoint: null,
      metadata: { refresh: true }
    },
    source_checkpoint: null
  }), { code: 'DEV_UI_REFRESH_EPOCH_CONFLICT' });
});

test('refresh dependency suppresses the persisted development supervisor before bootstrap', async () => {
  const calls = [];
  const deps = createRuntimeDependencies({
    paths: {
      runtimeIdentity: () => ({ mode: 'development', installation_id: 'c'.repeat(64) }),
      executablePath: () => process.execPath,
      appRoot: () => path.resolve(__dirname, '..')
    },
    revisions: { disk: () => ({ revision: REVISION }) },
    output: () => {},
    sleep: async () => {},
    suppressDevelopmentSupervisor: () => {
      calls.push('suppress-supervisor');
      return { suppressed: true, reason: 'development_supervisor_disabled' };
    },
    bootstrapRecoveryHost: async (options) => {
      calls.push('bootstrap-recovery-host');
      assert.equal(options.refresh, true);
      assert.equal(options.forceRefresh, true);
      assert.equal(options.sourceCheckpoint, null);
      assert.equal(options.expiresAtUnixMs - options.requestedAtUnixMs, 600_000,
        'the durable epoch must retain a bounded connector phase after the five-minute process-refresh poll');
      assert.ok(options.timeoutMs >= 90_000);
      return { activation_epoch_id: 'full-clean-refresh-dependency-0001' };
    }
  });

  const result = await deps.refresh(observation('CURRENT'));
  assert.deepEqual(calls, ['suppress-supervisor', 'bootstrap-recovery-host']);
  assert.equal(result.result.activation_epoch_id, 'full-clean-refresh-dependency-0001');
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
  for (const action of ['stop', 'replace']) {
    const fixture = harness(foreign);
    await assert.rejects(runLifecycle(action, fixture.deps), { code: 'DEV_UI_INSTALLATION_MISMATCH' });
    assert.deepEqual(fixture.calls, []);
  }
});

test('start routes a packaged host through the guarded refresh handoff', async () => {
  const base = observation('MISSING');
  const packaged = {
    ...base,
    installationMatches: false,
    descriptor: {
      ...base.descriptor,
      runtime_mode: 'packaged',
      installation_id: 'd'.repeat(64)
    }
  };
  const fixture = harness(packaged);
  fixture.deps.inspectRefreshTarget = async () => ({ ...packaged, client: {} });
  fixture.deps.refresh = async () => {
    fixture.calls.push('guarded-packaged-handoff');
    throw Object.assign(new Error('idle proof refused'), { code: 'RECOVERY_HOST_IDLE_HANDOFF_REFUSED' });
  };
  await assert.rejects(runLifecycle('start', fixture.deps), { code: 'RECOVERY_HOST_IDLE_HANDOFF_REFUSED' });
  assert.deepEqual(fixture.calls, ['guarded-packaged-handoff']);
  assert.match(fixture.lines[0], /reason=idle_packaged_handoff/);
});

test('start and refresh still refuse another development checkout', async () => {
  const base = observation('CURRENT');
  const foreignDevelopment = {
    ...base,
    installationMatches: false,
    descriptor: { ...base.descriptor, runtime_mode: 'development' }
  };
  for (const action of ['start', 'refresh']) {
    const fixture = harness(foreignDevelopment);
    fixture.deps.inspectRefreshTarget = async () => foreignDevelopment;
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

test('dev lifecycle reads the explicit UI runtime mode instead of the Recovery Host mode', () => {
  const observed = uiObservation({
    electron_ui_recovery: {
      alive: true,
      pid: 42,
      instance_id: 'electron-ui-instance-0001',
      runtime_mode: 'development',
      recovery_host_runtime_mode: 'development',
      ui_runtime_mode: 'packaged',
      ui_installation_id: 'a'.repeat(64)
    },
    electron_ui_revision: { running_revision: REVISION, disk_revision: REVISION, update_pending: false }
  });
  assert.equal(observed.state, 'CURRENT');
  assert.equal(observed.runtimeMode, 'packaged');
  assert.equal(observed.installationId, 'a'.repeat(64));
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
  assert.match(source, /CODING_TOOLS_MCP_UI_ALREADY_RUNNING/);
  assert.match(source, /function requestUiSingleInstanceLock\(\)\s*\{/);
  assert.match(source, /singleInstanceLockPath\(\{\s*userDataPath: sharedUserDataPath,\s*runtimeMode: uiRuntimeIdentity\.mode\s*\}\)/s);
  assert.match(source, /app\.requestSingleInstanceLock\(\{\s*runtime_mode: uiRuntimeIdentity\.mode,\s*installation_id: uiRuntimeIdentity\.installation_id\s*\}\)/s);
  assert.match(source, /app\.on\('second-instance', \(_event, commandLine, _workingDirectory, additionalData\) => handleSecondInstance\(commandLine, additionalData\)\)/);
  assert.match(source, /CODING_TOOLS_MCP_PACKAGED_BLOCKED_BY_EXISTING_UI/);
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
  const bridgeStart = source.indexOf('function canonicalTaskStateFromControl');
  const bridgeEnd = source.indexOf('async function panelTaskControl', bridgeStart);
  assert.ok(start >= 0 && end > start);
  assert.ok(bridgeStart >= 0 && bridgeEnd > bridgeStart);
  const handlers = source.slice(start, end);
  const bridge = source.slice(bridgeStart, bridgeEnd);
  assert.match(handlers, /readOrchestrationControlSnapshot\(\)/);
  assert.match(handlers, /canonicalTaskStateFromControl\(await readOrchestrationControlSnapshot\(\)\)/);
  assert.match(bridge, /taskList\?\.source !== 'orchestration_ledger'/);
  assert.match(bridge, /taskList\.current/);
  assert.match(bridge, /projectionTaskId === canonicalTaskId/);
  assert.match(bridge, /projectionRunId === canonicalRunId/);
  assert.match(bridge, /controlRunId === canonicalRunId/);
  assert.match(handlers, /Array\.isArray\(taskList\.history\)/);
  for (const action of ['clear', 'pause', 'resume', 'stop']) {
    assert.match(handlers, new RegExp(`panelTaskControl\\('${action}'\\)`));
  }
  assert.doesNotMatch(handlers, /workspaceStatePaths|archiveTask|readJson|writeJsonAtomic/);
});

function taskProjectionBridgeHarness() {
  const source = fs.readFileSync(path.resolve(__dirname, '..', 'electron', 'main.js'), 'utf8');
  const start = source.indexOf('function canonicalTaskStateFromControl');
  const end = source.indexOf('async function panelTaskControl', start);
  assert.ok(start >= 0 && end > start, 'canonical task bridge must remain discoverable');
  const context = vm.createContext({});
  vm.runInContext(source.slice(start, end), context, { filename: 'electron/task-state-bridge.js' });
  return (control) => {
    context.__control = control;
    return JSON.parse(JSON.stringify(vm.runInContext('canonicalTaskStateFromControl(__control)', context)));
  };
}

test('Task projection bridge preserves rich evidence only for the exact canonical task and run', () => {
  const project = taskProjectionBridgeHarness();
  const result = project({
    run_id: 'run-1',
    task_list: {
      source: 'orchestration_ledger',
      current: { task_id: 'task-1', run_id: 'run-1', objective: 'Canonical objective', status: 'accepted', started_at: '2026-09-09T00:00:00Z' }
    },
    task: {
      task_id: 'task-1',
      run_id: 'run-1',
      wave_id: 'wave-1',
      objective: 'projection objective must not override canonical',
      status: 'waiting',
      steps: [{ id: 'step-1', text: 'Done', status: 'completed' }],
      test_results: [{ command: 'node --test focused', status: 'passed', duration_ms: 12 }],
      modified_files: [{ path: 'electron/main.js', operation: 'update' }],
      failure: 'preserved evidence',
      last_build_report: { overall_status: 'passed', project: { type: 'electron', version: '1.0.0' }, artifacts: [] }
    }
  });
  assert.equal(result.exists, true);
  assert.equal(result.state.task_id, 'task-1');
  assert.equal(result.state.orchestration.run_id, 'run-1');
  assert.equal(result.state.objective, 'Canonical objective');
  assert.equal(result.state.status, 'accepted');
  assert.equal(result.state.details_available, true);
  assert.equal(result.state.detail_binding, 'exact');
  assert.equal(result.state.steps[0].text, 'Done');
  assert.equal(result.state.test_results[0].status, 'passed');
  assert.equal(result.state.modified_files[0].path, 'electron/main.js');
  assert.equal(result.state.last_build_report.overall_status, 'passed');
});

test('Task projection bridge drops stale detail instead of building a hybrid task', () => {
  const project = taskProjectionBridgeHarness();
  const result = project({
    run_id: 'run-1',
    task_list: {
      source: 'orchestration_ledger',
      current: { task_id: 'task-1', run_id: 'run-1', objective: 'Canonical objective', status: 'accepted', finished_at: '2026-09-09T00:00:05Z' }
    },
    task: {
      task_id: 'stale-task',
      run_id: 'stale-run',
      steps: [{ id: 'stale-step', text: 'Must not leak', status: 'failed' }],
      test_results: [{ status: 'failed' }],
      modified_files: [{ path: 'stale.js', operation: 'update' }],
      failure: 'stale failure',
      last_build_report: { overall_status: 'failed' }
    }
  });
  assert.equal(result.exists, true);
  assert.equal(result.state.task_id, 'task-1');
  assert.equal(result.state.orchestration.run_id, 'run-1');
  assert.equal(result.state.details_available, false);
  assert.equal(result.state.detail_binding, 'unavailable');
  for (const key of ['steps', 'test_results', 'modified_files', 'failure', 'last_build_report']) {
    assert.equal(Object.hasOwn(result.state, key), false, `${key} must be omitted on binding mismatch`);
  }
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
  assert.match(app, /CURRENT_COMPATIBLE_ACKNOWLEDGED/);
  assert.match(app, /CHANGED_COMPATIBLE_NEEDS_ACK/);
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

test('Command Center reports Ubuntu route evidence instead of a Windows Tunnel for central executors', () => {
  const fixture = runtimeStatusHarness();
  const revision = { running_revision: REVISION, disk_revision: REVISION, update_pending: false };
  const snapshot = {
    settings: { executionRole: 'central_executor' },
    status: {
      executionRole: 'central_executor',
      runtimeRunning: true,
      tunnelRunning: false,
      fullyReady: true,
      centralConnected: true,
      authorityReady: true,
      centralStatusReason: null,
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
  assert.equal(fixture.elements.get('#runtimeTunnelSourceState').textContent, 'CENTRAL');
  assert.equal(fixture.elements.get('#runtimeSourceSummary').textContent, 'SOURCE 3/3 CURRENT · CENTRAL CENTRAL');
  assert.equal(fixture.elements.get('#runtimeSourceSummary').className, 'cc-pill is-active');

  snapshot.status.authorityReady = false;
  snapshot.status.centralStatusReason = 'CENTRAL_LOCAL_POLICY_NOT_READY';
  fixture.render(snapshot);
  assert.equal(fixture.elements.get('#runtimeTunnelSourceState').textContent, 'WAITING');
  assert.match(fixture.elements.get('#runtimeTunnelSourceMeta').textContent, /Đã nối Ubuntu · chờ quyền/);
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

test('connector presentation distinguishes exact activation compatibility ACK from rediscovery', () => {
  const fixture = runtimeStatusHarness();
  const acknowledged = fixture.connector({
    connectorContractState: 'CURRENT_COMPATIBLE_ACKNOWLEDGED',
    connectorRefreshRequired: false,
    connectorRediscovered: false
  });
  assert.equal(acknowledged.state, 'CURRENT_COMPATIBLE_ACKNOWLEDGED');
  assert.equal(acknowledged.notice, false);
  assert.match(acknowledged.message, /connector hiện tại đã sẵn sàng/);
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
    isCentralExecutor: () => false,
    centralRoutePresentation: () => ({ state: 'waiting', label: 'Chờ Ubuntu', detail: '' }),
    setDot() {},
    $: () => ({ textContent: '' })
  });
  vm.runInContext(source.slice(start, end), context, { filename: 'renderer/app-heartbeat.js' });
  context.__staleHeartbeat = {
    mcpRunning: null,
    tunnelRunning: null,
    fullyReady: false,
    telemetryAvailable: false,
    signalStale: true
  };
  vm.runInContext('applyHeartbeat(__staleHeartbeat)', context);
  assert.equal(snapshot.status.signalStale, true);
  assert.equal(snapshot.status.activationClosure.closure_state, 'LIVE_CLOSED',
    'a missing transport heartbeat is uncertainty, not authority to erase the last receipt');
  assert.equal(snapshot.status.connectorContractState, 'CURRENT_ACKNOWLEDGED');
  context.__heartbeat = { mcpRunning: true, tunnelRunning: true, fullyReady: true };
  vm.runInContext('applyHeartbeat(__heartbeat)', context);
  assert.equal(Object.hasOwn(snapshot.status, 'signalStale'), false);
  assert.equal(Object.hasOwn(snapshot.status, 'activationClosure'), false);
  assert.equal(Object.hasOwn(snapshot.status, 'connectorContractState'), false);
  assert.equal(Object.hasOwn(snapshot.status, 'connectorRefreshRequired'), false);
});

function browserServiceStateFixture() {
  const source = fs.readFileSync(path.resolve(__dirname, '..', 'renderer', 'browser.js'), 'utf8');
  const start = source.indexOf('function renderServiceState');
  const end = source.indexOf('function renderWorkspaceHealth');
  assert.ok(start >= 0 && end > start);
  const elements = new Map();
  const element = () => ({
    classes: new Set(),
    classList: {
      add(...values) { values.forEach((value) => this.owner.classes.add(value)); },
      remove(...values) { values.forEach((value) => this.owner.classes.delete(value)); },
      toggle(value, enabled) { if (enabled) this.owner.classes.add(value); else this.owner.classes.delete(value); }
    },
    dataset: {},
    title: '',
    childNodes: [{ nodeName: 'I', textContent: '' }, { nodeName: '#text', textContent: '' }],
    attributes: new Map(),
    get lastChild() { return this.childNodes.at(-1); },
    get textContent() { return this.childNodes.map((node) => node.textContent).join(''); },
    set textContent(value) { this.childNodes = [{ nodeName: '#text', textContent: value }]; },
    setAttribute(name, value) { this.attributes.set(name, value); }
  });
  for (const selector of ['#mcpState', '#tunnelState', '#recoveryTunnelState', '#deviceState', '#deviceStateName', '#gitState', '#gitStateText']) {
    const value = element();
    value.classList.owner = value;
    elements.set(selector, value);
  }
  const context = vm.createContext({
    lastRuntimeState: null,
    lastRuntimeCheckAt: 0,
    Date,
    Number,
    String,
    Boolean,
    $: (selector) => elements.get(selector),
    renderWorkspaceHealth() {}
  });
  vm.runInContext(source.slice(start, end), context, { filename: 'renderer/browser-service-state.js' });
  return { context, elements, render(status) {
    context.__heartbeat = status;
    vm.runInContext('renderServiceState(__heartbeat)', context);
  } };
}

test('chat toolbar renders transient or stale service telemetry as warning instead of false red', () => {
  const { context, elements } = browserServiceStateFixture();
  context.__healthy = {
    mcpRunning: true,
    nativeAlive: true,
    tunnelRunning: true,
    telemetryAvailable: true,
    recoveryHost: { recovery_plane: { tunnel: { state: 'healthy' } } },
    device: { device_id: 'device-toolbar-0001', online: true, git: {} }
  };
  vm.runInContext('renderServiceState(__healthy)', context);
  assert.equal(elements.get('#mcpState').classes.has('ready'), true);
  assert.equal(elements.get('#tunnelState').classes.has('ready'), true);
  assert.equal(elements.get('#recoveryTunnelState').classes.has('ready'), true);

  context.__stale = { signalStale: true, telemetryAvailable: false };
  vm.runInContext('renderServiceState(__stale)', context);
  for (const selector of ['#mcpState', '#tunnelState', '#recoveryTunnelState']) {
    assert.equal(elements.get(selector).classes.has('warn'), true);
    assert.equal(elements.get(selector).classes.has('error'), false);
  }

  context.__transient = {
    mcpRunning: true,
    nativeAlive: true,
    tunnelRunning: false,
    telemetryAvailable: true,
    failures: 1,
    failureKind: 'tunnel_unavailable',
    recoveryHost: { recovery_plane: { tunnel: { state: 'failed' } } },
    device: { device_id: 'device-toolbar-0001', online: true, git: {} }
  };
  vm.runInContext('renderServiceState(__transient)', context);
  assert.equal(elements.get('#tunnelState').classes.has('warn'), true);
  assert.equal(elements.get('#tunnelState').classes.has('error'), false);
  assert.equal(elements.get('#recoveryTunnelState').classes.has('warn'), true);
  assert.equal(elements.get('#recoveryTunnelState').classes.has('error'), false);
});

test('chat toolbar shows the central Ubuntu route without requiring a Windows Tunnel', () => {
  const { elements, render } = browserServiceStateFixture();
  const badge = elements.get('#tunnelState');
  const indicator = badge.childNodes[0];
  const central = {
    executionRole: 'central_executor',
    mcpRunning: true,
    nativeAlive: true,
    tunnelRunning: false,
    centralConnected: true,
    authorityReady: true,
    telemetryAvailable: true,
    device: { device_id: 'device-toolbar-0001', online: true, git: {} }
  };
  render(central);
  assert.equal(badge.textContent, 'Ubuntu');
  assert.equal(badge.classes.has('ready'), true);
  assert.equal(badge.classes.has('error'), false);
  assert.match(badge.title, /Ubuntu: Đã kết nối.*quyền thao tác.*xác minh/);
  assert.equal(badge.attributes.get('aria-label'), badge.title);
  assert.equal(badge.childNodes[0], indicator, 'changing the label preserves the CSS indicator');
  assert.equal(central.tunnelRunning, false, 'route display must not invent a Windows Tunnel');

  render({ ...central, authorityReady: false });
  assert.equal(badge.classes.has('ready'), true, 'connected route remains distinct from pending action authority');
  assert.match(badge.title, /Đã kết nối.*chờ quyền/);

  render({ ...central, centralConnected: false });
  assert.equal(badge.classes.has('warn'), true);
  assert.equal(badge.classes.has('ready'), false, 'authority cannot substitute for central connectivity');
  assert.equal(badge.classes.has('error'), false);
  assert.match(badge.title, /Chưa xác nhận kết nối trung tâm/);

  render({ ...central, centralConnected: undefined, tunnelRunning: true });
  assert.equal(badge.classes.has('warn'), true);
  assert.equal(badge.classes.has('ready'), false, 'a local Tunnel does not prove the central route');

  for (const uncertainty of [{ signalStale: true, telemetryAvailable: false }, { recovering: true }, { recoveryDeferred: true }]) {
    render({ ...central, ...uncertainty });
    assert.equal(badge.textContent, 'Ubuntu');
    assert.equal(badge.classes.has('warn'), true);
    assert.equal(badge.classes.has('ready'), false);
    assert.equal(badge.classes.has('error'), false);
    assert.match(badge.title, /Telemetry tạm gián đoạn/);
  }

  render({ ...central, executionRole: 'direct_legacy', tunnelRunning: false });
  assert.equal(badge.textContent, 'Tunnel');
  assert.equal(badge.classes.has('error'), true, 'direct mode still reports a stopped Tunnel');
  assert.equal(badge.childNodes[0], indicator);
});
