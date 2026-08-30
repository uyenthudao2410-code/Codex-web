const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const net = require('node:net');
const os = require('node:os');
const path = require('node:path');

const { RuntimeOrchestrator } = require('../electron/services/runtimeOrchestrator');
const {
  buildNativeMcpEnv,
  normalizeActivationGate,
  ACTIVATION_GATE_CLOSED,
  ACTIVATION_GATE_OPEN
} = require('../electron/services/nativeService');

const REVISION = 'a'.repeat(64);

function readyEpoch(activationEpochId = 'activation-ready-soft-recovery-0001') {
  return {
    activation_epoch_id: activationEpochId,
    operation_id: 'operation-ready-soft-recovery-0001',
    state: 'READY',
    admission_state: 'OPEN',
    expires_at_unix_ms: Date.now() + 60_000,
    component_revisions: { coding_mcp: { disk_revision: REVISION } },
    verification: {
      final_census: {
        running_revision: REVISION,
        disk_revision: REVISION
      }
    }
  };
}

function listen(server, ...args) {
  return new Promise((resolve, reject) => {
    const onError = (error) => {
      server.removeListener('listening', onListening);
      reject(error);
    };
    const onListening = () => {
      server.removeListener('error', onError);
      resolve();
    };
    server.once('error', onError);
    server.once('listening', onListening);
    server.listen(...args);
  });
}

function closeServer(server) {
  if (!server || !server.listening) return Promise.resolve();
  return new Promise((resolve) => server.close(() => resolve()));
}

async function freePort() {
  const server = net.createServer();
  await listen(server, 0, '127.0.0.1');
  const port = server.address().port;
  await closeServer(server);
  return port;
}

async function probeProxy(t) {
  // proxyService only needs a local CONNECT response to mark a manual proxy
  // reachable.  It destroys the socket after the first response line, so the
  // test server deliberately leaves the connection open after responding.
  const server = net.createServer((socket) => {
    socket.once('data', () => {
      socket.write('HTTP/1.1 200 Connection Established\r\n\r\n');
    });
  });
  await listen(server, 0, '127.0.0.1');
  t.after(() => closeServer(server));
  return server.address().port;
}

function assertUpdateIncomplete(error, activationEpochId, {
  epochState = 'READY',
  admissionOpen = true
} = {}) {
  assert.equal(error?.code, 'UPDATE_INCOMPLETE');
  const details = error?.details || {};
  assert.equal(details.full_clean_activation_required, true);
  assert.equal(details.activation_epoch_id, activationEpochId);
  assert.equal(details.epoch_state ?? details.state, epochState);
  assert.equal(details.admission_open, admissionOpen);
  return true;
}

async function harness(t, { durableEpoch = null, activationEpochId = '' } = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-runtime-soft-replacement-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const stateFile = path.join(root, 'runtime-state.json');
  const initialState = {
    manualStop: false,
    nativePid: null,
    nativeProcessStartToken: null,
    tunnelPid: null
  };
  fs.writeFileSync(stateFile, JSON.stringify(initialState), 'utf8');

  const proxyPort = await probeProxy(t);
  const mcpPort = await freePort();
  const healthPort = await freePort();
  const settingsValue = {
    workspace: root,
    mcpPort,
    healthPort,
    tunnelId: 'soft-replacement-test-tunnel',
    proxyMode: 'manual',
    proxyUrl: `http://127.0.0.1:${proxyPort}`,
    autoStartServices: true,
    permissionMode: 'safe',
    authorizedRoots: [root],
    progressReportSeconds: 90
  };

  const orchestrator = new RuntimeOrchestrator({
    paths: {
      stateFile: () => stateFile,
      activationEpochFile: () => path.join(root, 'activation-epoch.json')
    },
    settings: { load: () => settingsValue },
    secrets: {
      get: (name) => name === 'runtimeApiKey' ? 'runtime-api-key' : 'mcp-token',
      set() {}
    },
    environment: {
      inspect: async () => ({
        tunnelClient: { installed: true },
        python: { installed: true, version: '3.11.0' }
      })
    },
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    revisionTracker: {
      disk: () => ({ revision: REVISION }),
      status: () => ({ running_revision: REVISION, disk_revision: REVISION, update_pending: false, state: 'current' })
    },
    activationEpochId
  });

  // Keep the fixture focused on the replacement admission boundary instead of
  // the on-disk ActivationEpochStore schema.  The production store supplies
  // the same current() projection to activationEpochStatus().
  orchestrator.activationEpochStore = {
    current: () => durableEpoch,
    load: () => ({ current: durableEpoch, history: [] })
  };
  orchestrator.validate = () => {};
  orchestrator.ensureToken = async () => 'mcp-token';
  orchestrator.assertActivationRevisionContinuity = () => ({
    verified: false,
    expected_revision: null,
    disk_revision: null
  });

  const calls = {
    nativeStart: 0,
    nativeStop: 0,
    tunnelStart: 0,
    tunnelStop: 0
  };
  const unexpectedMutation = (kind) => Object.assign(
    new Error(`unexpected ${kind} mutation`),
    { code: `UNEXPECTED_${kind.toUpperCase()}_MUTATION` }
  );
  orchestrator.native = {
    start: async () => {
      calls.nativeStart += 1;
      throw unexpectedMutation('native-start');
    },
    stop: async () => {
      calls.nativeStop += 1;
      return true;
    },
    status: async () => false
  };
  orchestrator.tunnel = {
    start: async () => {
      calls.tunnelStart += 1;
      throw unexpectedMutation('tunnel-start');
    },
    stop: async () => {
      calls.tunnelStop += 1;
      return true;
    },
    status: async () => false
  };

  return { orchestrator, calls, stateFile, initialState, settingsValue };
}

test('MCP-only soft recovery refuses a terminal READY/OPEN epoch before any process mutation', async (t) => {
  const durableEpoch = readyEpoch();
  const { orchestrator, calls, stateFile, initialState } = await harness(t, {
    durableEpoch,
    activationEpochId: durableEpoch.activation_epoch_id
  });

  await assert.rejects(
    () => orchestrator.recoverMcpOnly({ replaceLiveOwned: true, reason: 'test-terminal-ready' }),
    (error) => assertUpdateIncomplete(error, durableEpoch.activation_epoch_id)
  );
  assert.deepEqual(calls, {
    nativeStart: 0,
    nativeStop: 0,
    tunnelStart: 0,
    tunnelStop: 0
  });
  assert.equal(orchestrator.busy, false);
  assert.deepEqual(JSON.parse(fs.readFileSync(stateFile, 'utf8')), initialState);
});

test('automatic runtime start refuses replacement under a terminal READY/OPEN epoch before stop/spawn', async (t) => {
  const durableEpoch = readyEpoch('activation-ready-auto-start-0001');
  const { orchestrator, calls, stateFile, initialState } = await harness(t, {
    durableEpoch,
    activationEpochId: durableEpoch.activation_epoch_id
  });

  await assert.rejects(
    () => orchestrator.start({ automatic: true }),
    (error) => assertUpdateIncomplete(error, durableEpoch.activation_epoch_id)
  );
  assert.deepEqual(calls, {
    nativeStart: 0,
    nativeStop: 0,
    tunnelStart: 0,
    tunnelStop: 0
  });
  assert.equal(orchestrator.busy, false);
  assert.deepEqual(JSON.parse(fs.readFileSync(stateFile, 'utf8')), initialState);
});

test('direct Coding MCP revision activation refuses unavailable or unreadable durable epoch authority before mutation', async (t) => {
  for (const [store, expectedErrorCode] of [
    [null, 'ACTIVATION_EPOCH_STORE_UNAVAILABLE'],
    [{ current: () => { throw Object.assign(new Error('invalid epoch store'), { code: 'ACTIVATION_EPOCH_STORE_INVALID' }); } }, 'ACTIVATION_EPOCH_STORE_INVALID']
  ]) {
    const { orchestrator, calls, stateFile, initialState } = await harness(t);
    orchestrator.activationEpochStore = store;

    await assert.rejects(
      () => orchestrator.activateCodingMcpUpdate(REVISION),
      (error) => {
        assert.equal(error?.code, 'UPDATE_INCOMPLETE');
        assert.equal(error?.details?.error_code, expectedErrorCode);
        assert.equal(error?.details?.full_clean_activation_required, true);
        return true;
      }
    );
    assert.deepEqual(calls, {
      nativeStart: 0,
      nativeStop: 0,
      tunnelStart: 0,
      tunnelStop: 0
    });
    assert.equal(orchestrator.busy, false);
    assert.deepEqual(JSON.parse(fs.readFileSync(stateFile, 'utf8')), initialState);
  }
});

test('internal full-clean start refuses committed or failed terminal epochs before mutation', async (t) => {
  for (const [epochState, suffix] of [['READY_COMMITTED', 'committed'], ['FAILED', 'failed']]) {
    const activationEpochId = `activation-terminal-${suffix}-0001`;
    const durableEpoch = {
      ...readyEpoch(activationEpochId),
      state: epochState,
      admission_state: 'CLOSED'
    };
    const { orchestrator, calls, stateFile, initialState } = await harness(t, {
      durableEpoch,
      activationEpochId
    });

    await assert.rejects(
      () => orchestrator.start({
        automatic: true,
        fullClean: true,
        activationEpochId,
        activationGate: ACTIVATION_GATE_CLOSED
      }),
      (error) => assertUpdateIncomplete(error, activationEpochId, {
        epochState,
        admissionOpen: false
      })
    );
    assert.deepEqual(calls, {
      nativeStart: 0,
      nativeStop: 0,
      tunnelStart: 0,
      tunnelStop: 0
    });
    assert.equal(orchestrator.busy, false);
    assert.deepEqual(JSON.parse(fs.readFileSync(stateFile, 'utf8')), initialState);
  }
});

test('busy revision activation cannot change the shared in-memory epoch binding', async (t) => {
  const activationEpochId = 'activation-busy-request-0001';
  const priorEpochId = 'activation-prior-memory-binding-0001';
  const durableEpoch = {
    ...readyEpoch(activationEpochId),
    state: 'VERIFYING',
    admission_state: 'CLOSED'
  };
  const { orchestrator, calls } = await harness(t, {
    durableEpoch,
    activationEpochId: priorEpochId
  });
  orchestrator.busy = true;

  await assert.rejects(
    () => orchestrator.activateCodingMcpUpdate(REVISION, { activationEpochId }),
    { code: 'RUNTIME_BUSY' }
  );
  assert.equal(orchestrator.activationEpochId, priorEpochId);
  assert.deepEqual(calls, {
    nativeStart: 0,
    nativeStop: 0,
    tunnelStart: 0,
    tunnelStop: 0
  });
});

test('MCP-only recovery binds an explicit epoch for health and liveness checks', async (t) => {
  const activationEpochId = 'activation-explicit-soft-recovery-0001';
  const durableEpoch = {
    activation_epoch_id: activationEpochId,
    operation_id: 'operation-explicit-soft-recovery-0001',
    state: 'VERIFYING',
    admission_state: 'CLOSED',
    expires_at_unix_ms: Date.now() + 60_000,
    component_revisions: { coding_mcp: { disk_revision: REVISION } },
    verification: {
      final_census: {
        running_revision: REVISION,
        disk_revision: REVISION
      }
    }
  };
  const { orchestrator } = await harness(t, { durableEpoch });
  // This fixture isolates the epoch propagation after the durable guard; the
  // production watchdog normally calls assertSoftRecoveryAllowed first.
  orchestrator.assertSoftRecoveryAllowed = () => ({
    activation_epoch_id: activationEpochId,
    epoch_state: 'VERIFYING',
    state: 'UPDATE_INCOMPLETE',
    admission_open: false,
    update_incomplete: false
  });
  let healthObservedEpoch = null;
  let statusOptions = null;
  orchestrator.native.start = async () => ({ reused: false });
  orchestrator.native.status = async (_settings, options) => {
    statusOptions = options;
    return false;
  };
  orchestrator.currentMcpHealth = async () => {
    healthObservedEpoch = orchestrator.activationEpochId;
    return null;
  };

  await assert.rejects(
    () => orchestrator.recoverMcpOnly({ activationEpochId }),
    { code: 'MCP_RECOVERY_PROCESS_EXITED' }
  );
  assert.equal(healthObservedEpoch, activationEpochId);
  assert.deepEqual(statusOptions, { activationEpochId });
});

test('Coding MCP revision activation binds an explicit epoch for health and liveness checks', async (t) => {
  const activationEpochId = 'activation-explicit-revision-0001';
  const durableEpoch = {
    activation_epoch_id: activationEpochId,
    operation_id: 'operation-explicit-revision-0001',
    state: 'VERIFYING',
    admission_state: 'CLOSED',
    expires_at_unix_ms: Date.now() + 60_000,
    component_revisions: { coding_mcp: { disk_revision: REVISION } },
    verification: {
      final_census: {
        running_revision: REVISION,
        disk_revision: REVISION
      }
    }
  };
  const { orchestrator } = await harness(t, { durableEpoch });
  const contractSha256 = 'c'.repeat(64);
  let healthReads = 0;
  const healthEpochs = [];
  let statusOptions = null;
  let tunnelOptions = null;
  orchestrator.currentMcpHealth = async () => {
    healthEpochs.push(orchestrator.activationEpochId);
    healthReads += 1;
    if (healthReads === 1) {
      return {
        ready: true,
        process_instance_id: 'old-revision-process',
        instance_id: 'old-revision-server',
        code_revision: REVISION
      };
    }
    if (healthReads === 2) {
      return {
        ready: true,
        process_instance_id: 'new-revision-process',
        instance_id: 'new-revision-server',
        code_revision: 'b'.repeat(64)
      };
    }
    return {
      ready: true,
      activation_epoch_id: activationEpochId,
      process_instance_id: 'new-revision-process',
      instance_id: 'new-revision-server',
      code_revision: REVISION,
      tool_contract: {
        schema_version: 1,
        profile: 'smart-v3',
        sha256: contractSha256
      }
    };
  };
  orchestrator.native = {
    stop: async () => true,
    start: async (_settings, _token, _progress, options) => {
      assert.equal(options.activationEpochId, activationEpochId);
      assert.equal(options.activationGate, ACTIVATION_GATE_CLOSED);
      return { instanceId: 'new-revision-supervisor' };
    },
    status: async (_settings, options) => {
      statusOptions = options;
      return true;
    }
  };
  orchestrator.tunnel.start = async (_settings, _runtimeApiKey, _token, _progress, options) => {
    tunnelOptions = options;
    return { pid: 8080 };
  };

  const result = await orchestrator.activateCodingMcpUpdate(REVISION, { activationEpochId });

  assert.equal(result.new_instance_id, 'new-revision-process');
  assert.equal(result.new_server_instance_id, 'new-revision-server');
  assert.equal(result.health_verified, true);
  assert.deepEqual(statusOptions, { activationEpochId });
  assert.deepEqual(healthEpochs, [activationEpochId, activationEpochId, activationEpochId]);
  assert.equal(result.tunnel_preserved, false);
  assert.equal(result.tunnel_attestation_refreshed, true);
  assert.equal(result.tunnel_pid, 8080);
  assert.ok(tunnelOptions?.connectorAttestation?.secret);
  assert.equal(tunnelOptions?.activationEpochId, activationEpochId);
  assert.equal(tunnelOptions?.connectorAttestation?.activationEpochId, activationEpochId);
  assert.equal(tunnelOptions?.connectorAttestation?.processInstanceId, 'new-revision-process');
  assert.equal(tunnelOptions?.connectorAttestation?.serverInstanceId, 'new-revision-server');
  assert.equal(tunnelOptions?.connectorAttestation?.contractSha256, contractSha256);
  assert.equal(orchestrator.activationEpochId, activationEpochId);
  assert.equal(orchestrator.busy, false);
});

test('Coding MCP revision activation rolls back the new MCP when dependent Tunnel rebind fails', async (t) => {
  const activationEpochId = 'activation-tunnel-rebind-failure-0001';
  const durableEpoch = {
    ...readyEpoch(activationEpochId),
    state: 'VERIFYING',
    admission_state: 'CLOSED'
  };
  const { orchestrator, calls, stateFile, initialState } = await harness(t, {
    durableEpoch,
    activationEpochId
  });
  let healthReads = 0;
  orchestrator.currentMcpHealth = async () => {
    healthReads += 1;
    if (healthReads === 1) {
      return {
        ready: true,
        activation_epoch_id: activationEpochId,
        process_instance_id: 'old-rebind-process',
        instance_id: 'old-rebind-server',
        code_revision: REVISION
      };
    }
    return {
      ready: true,
      activation_epoch_id: activationEpochId,
      process_instance_id: 'new-rebind-process',
      instance_id: 'new-rebind-server',
      code_revision: REVISION,
      tool_contract: {
        schema_version: 1,
        profile: 'smart-v3',
        sha256: 'd'.repeat(64)
      }
    };
  };
  orchestrator.native.start = async () => {
    calls.nativeStart += 1;
    return { instanceId: 'new-rebind-supervisor' };
  };
  orchestrator.native.status = async () => true;
  orchestrator.tunnel.start = async () => {
    calls.tunnelStart += 1;
    throw Object.assign(new Error('managed Tunnel rebind failed'), { code: 'TUNNEL_REBIND_FAILED' });
  };

  await assert.rejects(
    () => orchestrator.activateCodingMcpUpdate(REVISION, { activationEpochId }),
    { code: 'TUNNEL_REBIND_FAILED' }
  );
  assert.deepEqual(calls, {
    nativeStart: 1,
    nativeStop: 2,
    tunnelStart: 1,
    tunnelStop: 0
  });
  assert.equal(orchestrator.busy, false);
  assert.deepEqual(JSON.parse(fs.readFileSync(stateFile, 'utf8')), initialState);
});

test('legacy no-epoch runtime start still reaches NativeService without forcing a gate', async (t) => {
  const { orchestrator } = await harness(t);
  let observedOptions = null;
  orchestrator.native.start = async (_settings, _token, _progress, options) => {
    observedOptions = options;
    throw Object.assign(new Error('legacy launch captured'), { code: 'LEGACY_LAUNCH_CAPTURED' });
  };

  await assert.rejects(orchestrator.start({ automatic: true }), { code: 'LEGACY_LAUNCH_CAPTURED' });
  assert.ok(observedOptions, 'the no-epoch path should reach the native launch boundary');
  assert.equal(observedOptions.activationEpochId, '');
  assert.equal(observedOptions.activationGate, '');
  assert.equal(orchestrator.busy, false);
});

test('NativeService environment preserves implicit-open compatibility when no epoch is bound', () => {
  const launch = {
    resourcesRoot: path.join(os.tmpdir(), 'webcodex-soft-gate-resources'),
    moduleRoot: path.join(os.tmpdir(), 'webcodex-soft-gate-module'),
    vendoredPython: path.join(os.tmpdir(), 'webcodex-soft-gate-module', 'python_vendor')
  };
  const env = buildNativeMcpEnv({
    sourceEnv: { PATH: 'safe-base-path' },
    launch,
    settings: { authorizedRoots: [], progressReportSeconds: 90 },
    token: 'mcp-token',
    diskRevision: REVISION,
    supervisorRequestFile: path.join(os.tmpdir(), 'webcodex-soft-gate-supervisor.json')
  });

  assert.equal(normalizeActivationGate('', ''), '');
  assert.equal(normalizeActivationGate('', ACTIVATION_GATE_OPEN), ACTIVATION_GATE_OPEN);
  assert.equal(env.CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID, undefined);
  assert.equal(env.CODING_TOOLS_MCP_ACTIVATION_GATE, undefined);
  assert.equal(ACTIVATION_GATE_CLOSED, 'closed');
});
