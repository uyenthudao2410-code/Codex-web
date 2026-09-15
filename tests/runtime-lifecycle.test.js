const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');
const crypto = require('node:crypto');
const {
  NativeService,
  isAlive,
  runtimeFingerprint,
  connectorAttestationSecretHash,
  connectorAttestationSecretMatches,
  currentRuntimeState,
  resolveNativeLaunchContract,
  buildNativeMcpEnv,
  SECRET_BROKER_ENV,
  AUTH_HANDLE_ENV,
  MCP_AUTH_HANDLE,
  OPENAI_API_KEY_HANDLE,
  P5_A0_SEED_ENV,
  P5_A0_SEED_SECRET,
  P5_A0_SEED_HANDLE
} = require('../electron/services/nativeService');
const { TunnelService } = require('../electron/services/tunnelService');
const { observeProcessIdentityAsync } = require('../electron/services/processIdentity');
const { normalizeProxyValue } = require('../electron/services/proxyService');
const runtimePaths = require('../electron/paths');
const runtimeStatePath = path.join(os.tmpdir(), `webcodex-runtime-lifecycle-${process.pid}.json`);
const supervisorRequestPath = path.join(os.tmpdir(), `webcodex-supervisor-request-${process.pid}.json`);
runtimePaths.stateFile = () => runtimeStatePath;
runtimePaths.supervisorRequestFile = () => supervisorRequestPath;
fs.writeFileSync(runtimeStatePath, JSON.stringify({ manualStop: false }), 'utf8');
test.after(() => {
  fs.rmSync(runtimeStatePath, { force: true });
  fs.rmSync(supervisorRequestPath, { force: true });
  fs.rmSync(`${supervisorRequestPath}.bak`, { force: true });
  fs.rmSync(`${supervisorRequestPath}.processing`, { force: true });
  fs.rmSync(`${supervisorRequestPath}.processing.bak`, { force: true });
});
test.beforeEach(() => {
  fs.rmSync(supervisorRequestPath, { force: true });
  fs.rmSync(`${supervisorRequestPath}.bak`, { force: true });
  fs.rmSync(`${supervisorRequestPath}.processing`, { force: true });
  fs.rmSync(`${supervisorRequestPath}.processing.bak`, { force: true });
});
const { RuntimeOrchestrator, readMcpHealth, readMcpHealthObservation, readMcpActivationPreflight, activationPreflightProof, parseGitStatusPorcelainV2, parseLoopbackListenerPid } = require('../electron/services/runtimeOrchestrator');
const { classifyStoredDeviceOwner } = require('../electron/services/deviceIdentity');

test('process liveness rejects missing and non-positive PIDs before OS probing', () => {
  assert.equal(isAlive(null), false);
  assert.equal(isAlive(undefined), false);
  assert.equal(isAlive(0), false);
  assert.equal(isAlive(-1), false);
  assert.equal(isAlive(1.5), false);
});

test('native MCP launch env brokers secrets and excludes ambient loader or secret state', () => {
  const launch = {
    resourcesRoot: path.join(os.tmpdir(), 'bundle-root'),
    moduleRoot: path.join(os.tmpdir(), 'module-root'),
    vendoredPython: path.join(os.tmpdir(), 'module-root', 'python_vendor')
  };
  const env = buildNativeMcpEnv({
    sourceEnv: {
      PATH: 'safe-base-path',
      USERPROFILE: 'C:\\Users\\Test',
      PYTHONPATH: 'ambient-pythonpath-must-not-pass',
      LD_PRELOAD: 'ambient-loader-must-not-pass',
      UNRELATED_SECRET: 'ambient-secret-must-not-pass',
       OPENAI_API_KEY: 'test-provider-secret',
       [P5_A0_SEED_ENV]: 'ambient-p5-seed-material-must-not-win'
    },
    launch,
    settings: { authorizedRoots: [], progressReportSeconds: 90 },
    token: 'test-mcp-bearer',
    p5Seed: 'managed-p5-seed-material',
    diskRevision: 'revision-test',
    supervisorRequestFile: path.join(os.tmpdir(), 'supervisor-test.json')
  });
  assert.equal(env.CODING_TOOLS_MCP_AUTH_TOKEN, undefined);
  assert.equal(env.UNRELATED_SECRET, undefined);
  assert.equal(env.LD_PRELOAD, undefined);
  assert.equal(env.OPENAI_API_KEY, undefined);
  assert.equal(env[P5_A0_SEED_ENV], undefined);
  assert.equal(env[AUTH_HANDLE_ENV], MCP_AUTH_HANDLE);
  const broker = JSON.parse(env[SECRET_BROKER_ENV]);
  assert.equal(broker[MCP_AUTH_HANDLE], 'test-mcp-bearer');
  assert.equal(broker[OPENAI_API_KEY_HANDLE], 'test-provider-secret');
  assert.equal(broker[P5_A0_SEED_HANDLE], 'managed-p5-seed-material');
  assert.ok(env.PATH.includes(path.join(launch.resourcesRoot, 'tools')));
  assert.ok(env.PATH.includes('safe-base-path'));
  assert.ok(env.PYTHONPATH.includes(launch.moduleRoot));
  assert.ok(env.PYTHONPATH.includes(launch.vendoredPython));
  assert.equal(env.PYTHONPATH.includes('ambient-pythonpath-must-not-pass'), false);
});

test('native MCP launch passes the durable installation identity to the child process', () => {
  const launch = {
    resourcesRoot: path.join(os.tmpdir(), 'bundle-root'),
    moduleRoot: path.join(os.tmpdir(), 'module-root'),
    vendoredPython: path.join(os.tmpdir(), 'module-root', 'python_vendor')
  };
  const env = buildNativeMcpEnv({
    sourceEnv: { PATH: 'safe-base-path' },
    launch,
    settings: { authorizedRoots: [], progressReportSeconds: 90 },
    token: 'test-mcp-bearer',
    diskRevision: 'revision-test',
    supervisorRequestFile: path.join(os.tmpdir(), 'supervisor-test.json'),
    device: {
      deviceId: '11111111-1111-4111-8111-111111111111',
      deviceInstanceId: 'device-instance-home-0001',
      displayName: 'Home Workstation'
    }
  });
  assert.equal(env.CODING_TOOLS_MCP_DEVICE_ID, '11111111-1111-4111-8111-111111111111');
  assert.equal(env.CODING_TOOLS_MCP_DEVICE_INSTANCE_ID, 'device-instance-home-0001');
  assert.equal(env.CODING_TOOLS_MCP_DEVICE_DISPLAY_NAME, 'Home Workstation');
  assert.equal(env.CODING_TOOLS_MCP_AUTHORIZED_ROOTS, '[]');
});

test('native MCP launch ignores an ambient P5 seed when no managed SecretStore seed is supplied', () => {
  const launch = {
    resourcesRoot: path.join(os.tmpdir(), 'bundle-root'),
    moduleRoot: path.join(os.tmpdir(), 'module-root'),
    vendoredPython: path.join(os.tmpdir(), 'module-root', 'python_vendor')
  };
  const env = buildNativeMcpEnv({
    sourceEnv: { PATH: 'safe-base-path', [P5_A0_SEED_ENV]: 'ambient-seed-must-not-be-used' },
    launch,
    settings: { authorizedRoots: [], progressReportSeconds: 90 },
    token: 'test-mcp-bearer',
    diskRevision: 'revision-test',
    supervisorRequestFile: path.join(os.tmpdir(), 'supervisor-test.json')
  });
  const broker = JSON.parse(env[SECRET_BROKER_ENV]);
  assert.equal(broker[P5_A0_SEED_HANDLE], undefined);
  assert.equal(env[P5_A0_SEED_ENV], undefined);
});

test('orchestrator obtains the managed P5 seed only from the encrypted secret store', () => {
  const calls = [];
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({}) },
    secrets: { get: (name) => { calls.push(name); return name === P5_A0_SEED_SECRET ? 'managed-seed' : ''; } },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  assert.equal(orchestrator.p5A0Seed(), 'managed-seed');
  assert.deepEqual(calls, [P5_A0_SEED_SECRET]);
});

test('full-clean replacement binds acceptance preservation to the child activation environment', () => {
  const launch = {
    resourcesRoot: path.join(os.tmpdir(), 'bundle-root'),
    moduleRoot: path.join(os.tmpdir(), 'module-root'),
    vendoredPython: path.join(os.tmpdir(), 'module-root', 'python_vendor')
  };
  const env = buildNativeMcpEnv({
    sourceEnv: { PATH: 'safe-base-path' },
    launch,
    settings: { authorizedRoots: [], progressReportSeconds: 90 },
    token: 'test-mcp-bearer',
    diskRevision: 'revision-test',
    supervisorRequestFile: path.join(os.tmpdir(), 'supervisor-test.json'),
    activationEpochId: 'activation-epoch-test-0001',
    activationGate: 'closed',
    activationAllowAcceptancePending: true,
    activationExpiresAtUnixMs: 4_000_000_000_000
  });
  assert.equal(env.CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID, 'activation-epoch-test-0001');
  assert.equal(env.CODING_TOOLS_MCP_ACTIVATION_GATE, 'closed');
  assert.equal(env.CODING_TOOLS_MCP_ACTIVATION_ALLOW_ACCEPTANCE_PENDING, 'true');
});

test('activation epoch status distinguishes a valid empty store from unavailable durable authority', () => {
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({}) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });

  orchestrator.activationEpochStore = { current: () => null };
  assert.deepEqual(orchestrator.activationEpochStatus(), {
    activation_epoch_id: null,
    operation_id: null,
    state: 'NONE',
    admission_open: true,
    update_incomplete: false
  });

  orchestrator.activationEpochStore = null;
  assert.deepEqual(orchestrator.activationEpochStatus(), {
    activation_epoch_id: null,
    operation_id: null,
    state: 'UPDATE_INCOMPLETE',
    admission_open: false,
    update_incomplete: true,
    error_code: 'ACTIVATION_EPOCH_STORE_UNAVAILABLE'
  });
});

test('terminal activation epochs block runtime start before MCP or Tunnel mutation', async () => {
  const calls = { settings: 0, environment: 0, nativeStart: 0, tunnelStart: 0 };
  const orchestrator = new RuntimeOrchestrator({
    settings: {
      load: () => {
        calls.settings += 1;
        return { workspace: process.cwd(), tunnelId: 'terminal-epoch-test' };
      }
    },
    secrets: { get: () => 'unused-terminal-epoch-secret' },
    environment: {
      inspect: async () => {
        calls.environment += 1;
        return { tunnelClient: { installed: true } };
      }
    },
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.native.start = async () => { calls.nativeStart += 1; return true; };
  orchestrator.tunnel.start = async () => { calls.tunnelStart += 1; return true; };

  for (const state of ['READY_COMMITTED', 'READY', 'FAILED']) {
    const suffix = state.toLowerCase().replace('_', '-');
    const activationEpochId = `activation-terminal-${suffix}`;
    orchestrator.activationEpochStore = {
      current: () => ({
        activation_epoch_id: activationEpochId,
        operation_id: `operation-terminal-${suffix}`,
        state,
        admission_state: state === 'READY' ? 'OPEN' : 'CLOSED'
      })
    };
    orchestrator.setActivationEpoch(activationEpochId);

    await assert.rejects(
      orchestrator.start({ automatic: true, fullClean: true, activationEpochId, activationGate: 'closed' }),
      (error) => error?.code === 'UPDATE_INCOMPLETE'
        && error?.details?.epoch_state === state
        && error?.details?.full_clean_activation_required === true
    );
    assert.equal(orchestrator.busy, false);
  }

  assert.deepEqual(calls, { settings: 0, environment: 0, nativeStart: 0, tunnelStart: 0 });
});

test('Coding MCP health is trusted only when workspace and device_id both match', async (t) => {
  const token = 'token';
  const server = http.createServer((request, response) => { assert.equal(request.headers.authorization, `Bearer ${token}`); const body = JSON.stringify({ ready: true, workspace: 'C:\\work\\one', device_id: 'device-a' }); response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) }); response.end(body); });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise((resolve) => server.close(resolve)));
  const port = server.address().port;
  assert.ok(await readMcpHealth(port, token, 'C:\\work\\one', 'device-a'));
  assert.equal(await readMcpHealth(port, token, 'C:\\work\\one', 'device-b'), null);
  assert.equal(await readMcpHealth(port, token, 'C:\\work\\other', 'device-a'), null);
});

test('Coding MCP health classifies deterministic mismatches separately from transient timeout or not-ready state', async (t) => {
  const token = 'token';
  let mode = 'healthy';
  const server = http.createServer((request, response) => {
    if (mode === 'timeout') return;
    if (mode === 'unauthorized') {
      response.writeHead(401);
      response.end();
      return;
    }
    if (mode === 'invalid-json') {
      response.writeHead(200, { 'Content-Type': 'application/json' });
      response.end('{invalid');
      return;
    }
    const payload = mode === 'not-ready'
      ? { ready: false, workspace: 'C:\\work\\one', device_id: 'device-a' }
      : { ready: true, workspace: 'C:\\work\\one', device_id: 'device-a' };
    const body = JSON.stringify(payload);
    response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) });
    response.end(body);
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise((resolve) => server.close(resolve)));
  const port = server.address().port;

  let observed = await readMcpHealthObservation(port, token, 'C:\\work\\other', 'device-a');
  assert.equal(observed.failure.kind, 'workspace_mismatch');
  assert.equal(observed.failure.deterministic, true);

  observed = await readMcpHealthObservation(port, token, 'C:\\work\\one', 'device-b');
  assert.equal(observed.failure.kind, 'device_mismatch');
  assert.equal(observed.failure.deterministic, true);

  mode = 'unauthorized';
  observed = await readMcpHealthObservation(port, token, 'C:\\work\\one', 'device-a');
  assert.equal(observed.failure.kind, 'http_unauthorized');
  assert.equal(observed.failure.deterministic, true);

  mode = 'invalid-json';
  observed = await readMcpHealthObservation(port, token, 'C:\\work\\one', 'device-a');
  assert.equal(observed.failure.kind, 'invalid_json');
  assert.equal(observed.failure.deterministic, true);

  mode = 'not-ready';
  observed = await readMcpHealthObservation(port, token, 'C:\\work\\one', 'device-a');
  assert.equal(observed.failure.kind, 'not_ready');
  assert.equal(observed.failure.deterministic, false);

  mode = 'timeout';
  observed = await readMcpHealthObservation(port, token, 'C:\\work\\one', 'device-a');
  assert.equal(observed.failure.kind, 'timeout');
  assert.equal(observed.failure.deterministic, false);
});

test('activation census can request a bounded health window without weakening identity checks', { timeout: 10_000 }, async (t) => {
  const token = 'token';
  const server = http.createServer((request, response) => {
    assert.equal(request.url, '/__control/health');
    setTimeout(() => {
      const body = JSON.stringify({
        ready: true,
        workspace: 'C:\\work\\one',
        device_id: 'device-a',
        activation_epoch_id: 'activation-health-window-0001'
      });
      response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) });
      response.end(body);
    }, 1_500);
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise((resolve) => server.close(resolve)));
  const observed = await readMcpHealthObservation(
    server.address().port,
    token,
    'C:\\work\\one',
    'device-a',
    'activation-health-window-0001',
    { timeoutMs: 5_000 }
  );
  assert.equal(observed.failure, null);
  assert.equal(observed.health.activation_epoch_id, 'activation-health-window-0001');
});

test('Coding MCP activation preflight requires workspace identity even for a refusal', async (t) => {
  const token = 'token';
  let includeWorkspace = false;
  const server = http.createServer((request, response) => {
    assert.equal(request.url, '/__control/activation');
    assert.equal(request.headers.authorization, `Bearer ${token}`);
    const payload = { safe: false, code: 'RUNTIME_BUSY', reason: 'active_runtime_work' };
    if (includeWorkspace) payload.workspace = 'C:\\work\\one';
    const body = JSON.stringify(payload);
    response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) });
    response.end(body);
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise((resolve) => server.close(resolve)));
  const port = server.address().port;
  await assert.rejects(readMcpActivationPreflight(port, token), { code: 'ORCHESTRATION_STATE_UNCERTAIN' });
  includeWorkspace = true;
  const result = await readMcpActivationPreflight(port, token);
  assert.equal(result.safe, false);
  assert.equal(result.code, 'RUNTIME_BUSY');
  assert.equal(result.workspace, 'C:\\work\\one');
});

test('Coding MCP activation observation allows a bounded multi-second ledger census', { timeout: 10_000 }, async (t) => {
  const token = 'token';
  const server = http.createServer((request, response) => {
    assert.equal(request.url, '/__control/activation');
    setTimeout(() => {
      const body = JSON.stringify({ safe: true, code: 'READY', workspace: 'C:\\work\\one' });
      response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) });
      response.end(body);
    }, 3_250);
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise((resolve) => server.close(resolve)));

  const result = await readMcpActivationPreflight(server.address().port, token);
  assert.equal(result.safe, true);
  assert.equal(result.workspace, 'C:\\work\\one');
});

test('Git and persistent-device ownership helpers project exact local identity state', () => {
  const clean = parseGitStatusPorcelainV2(`# branch.oid ${'a'.repeat(40)}\n# branch.head main\n`);
  assert.deepEqual(clean, { available: true, branch: 'main', head: 'a'.repeat(40), head_short: 'aaaaaaaa', dirty: false });
  const dirty = parseGitStatusPorcelainV2(`# branch.oid ${'b'.repeat(40)}\n# branch.head feature/device\n1 .M N... 100644 100644 100644 a b file.js\n? new.txt\n`);
  assert.equal(dirty.dirty, true);
  const deviceId = '12345678-1234-4123-8123-123456789abc';
  assert.equal(classifyStoredDeviceOwner(deviceId, deviceId), 'owned');
  assert.equal(classifyStoredDeviceOwner('', deviceId), 'legacy');
  assert.equal(classifyStoredDeviceOwner('87654321-4321-4321-8321-cba987654321', deviceId), 'foreign');
  assert.equal(parseLoopbackListenerPid('  TCP    127.0.0.1:18766    0.0.0.0:0    LISTENING    4321\r\n', 18766), 4321);
  assert.equal(parseLoopbackListenerPid('  TCP    127.0.0.1:18766    0.0.0.0:0    LISTENING    4321\r\n  TCP    127.0.0.1:18766    0.0.0.0:0    LISTENING    9999\r\n', 18766), null);
});

test('lightweight Git telemetry serves stale cache while one slow refresh runs in background', { timeout: 2_000 }, async () => {
  const orchestrator = Object.create(RuntimeOrchestrator.prototype);
  const workspace = 'C:\\work\\one';
  const otherWorkspace = 'C:\\work\\two';
  const cached = { available: true, branch: 'main', head: 'a'.repeat(40), head_short: 'aaaaaaaa', dirty: false };
  const refreshed = { available: true, branch: 'main', head: 'b'.repeat(40), head_short: 'bbbbbbbb', dirty: true };
  Object.assign(orchestrator, {
    gitStatusCache: cached,
    gitStatusCacheAt: Date.now() - 10_001,
    gitStatusWorkspace: workspace,
    gitStatusRefreshInFlight: null,
    gitStatusRefreshWorkspace: ''
  });
  let probes = 0;
  let resolveRefresh;
  orchestrator._probeGitStatus = async (target) => {
    assert.equal(target, workspace);
    probes += 1;
    return new Promise((resolve) => { resolveRefresh = resolve; });
  };

  assert.strictEqual(await orchestrator.gitStatus(workspace), cached);
  const refresh = orchestrator.gitStatusRefreshInFlight;
  assert.ok(refresh);
  assert.strictEqual(await orchestrator.gitStatus(workspace), cached);
  assert.equal(probes, 1);

  resolveRefresh(refreshed);
  assert.strictEqual(await refresh, refreshed);
  assert.strictEqual(await orchestrator.gitStatus(workspace), refreshed);
  assert.equal(orchestrator.gitStatusRefreshInFlight, null);

  const other = { available: true, branch: 'feature', head: 'c'.repeat(40), head_short: 'cccccccc', dirty: false };
  orchestrator._probeGitStatus = async (target) => {
    assert.equal(target, otherWorkspace);
    probes += 1;
    return other;
  };
  assert.strictEqual(await orchestrator.gitStatus(otherWorkspace), other);
  assert.equal(probes, 2);
});

test('device-aware process services keep legacy or foreign live owners fail-closed in source contract', () => {
  const nativeSource = fs.readFileSync(path.join(__dirname, '..', 'electron', 'services', 'nativeService.js'), 'utf8');
  const tunnelSource = fs.readFileSync(path.join(__dirname, '..', 'electron', 'services', 'tunnelService.js'), 'utf8');
  const recoverySource = fs.readFileSync(path.join(__dirname, '..', 'electron', 'services', 'recoveryPlaneService.js'), 'utf8');
  for (const source of [nativeSource, tunnelSource, recoverySource]) assert.match(source, /classifyStoredDeviceOwner/);
  assert.match(nativeSource, /NATIVE_PROCESS_OWNER_UNVERIFIED/);
  assert.match(nativeSource, /NATIVE_PROCESS_FOREIGN_DEVICE/);
  assert.match(tunnelSource, /TUNNEL_PROCESS_OWNER_UNVERIFIED/);
  assert.match(tunnelSource, /TUNNEL_PROCESS_FOREIGN_DEVICE/);
  assert.match(recoverySource, /\$\{kind\}_OWNER_UNVERIFIED/);
  assert.match(recoverySource, /exactIdentity\(state, 'recoveryMcp'/);
  assert.match(recoverySource, /exactIdentity\(state, 'recoveryTunnel'/);
  for (const source of [nativeSource, tunnelSource, recoverySource]) {
    assert.match(source, /processStartToken|ProcessStartToken/);
    assert.match(source, /terminateExactProcessTree/);
    assert.doesNotMatch(source, /taskkill\.exe/);
  }
  assert.match(recoverySource, /preflightLegacyOwnershipMigration/);
  assert.match(recoverySource, /RECOVERY_MCP_LEGACY_MIGRATION_UNVERIFIED/);
  assert.match(recoverySource, /RECOVERY_TUNNEL_LEGACY_MIGRATION_UNVERIFIED/);
});

function recoveryHarness(status) {
  const calls = { restart: 0, tunnel: 0, mcp: 0, mcpOptions: [] };
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.lightweightSnapshot = async () => ({ ...status });
  orchestrator.restart = async () => { calls.restart += 1; };
  orchestrator.recoverTunnelOnly = async () => { calls.tunnel += 1; };
  orchestrator.recoverMcpOnly = async (options = {}) => { calls.mcp += 1; calls.mcpOptions.push(options); };
  orchestrator.isManuallyStopped = () => false;
  orchestrator.heartbeatFailures = 2;
  orchestrator.heartbeatFailureKind = status.mcpRunning
    ? 'tunnel_unavailable'
    : (status.nativeAlive ? 'mcp_health_unavailable' : 'mcp_process_exited');
  return { orchestrator, calls };
}

test('native runtime identity changes with workspace and port while tool mode stays smart', () => {
  const base = { workspace: 'C:\\work\\one', mcpPort: 18766, permissionMode: 'safe' };
  assert.equal(runtimeFingerprint(base), runtimeFingerprint({ ...base }));
  assert.notEqual(runtimeFingerprint(base), runtimeFingerprint({ ...base, workspace: 'C:\\work\\two' }));
  assert.notEqual(runtimeFingerprint(base), runtimeFingerprint({ ...base, mcpPort: 18767 }));
  assert.notEqual(runtimeFingerprint(base), runtimeFingerprint({ ...base, authorizedRoots: ['D:\\shared'] }));
  assert.equal(runtimeFingerprint(base), runtimeFingerprint({ ...base, toolMode: 'readonly' }));
});

function nativeLaunchFixture(t, name = 'checkout') {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-native-launch-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const appRoot = path.join(root, name);
  const resourcesRoot = path.join(appRoot, 'resources');
  const moduleRoot = path.join(resourcesRoot, 'coding-tools-mcp');
  fs.mkdirSync(path.join(moduleRoot, 'coding_tools_mcp'), { recursive: true });
  fs.mkdirSync(path.join(moduleRoot, 'python_vendor'), { recursive: true });
  fs.writeFileSync(path.join(moduleRoot, 'coding_tools_mcp', '__init__.py'), '', 'utf8');
  return { root, appRoot, resourcesRoot, moduleRoot };
}

test('development Coding MCP launch is pinned to the current checkout module root', (t) => {
  const fixture = nativeLaunchFixture(t);
  const launch = resolveNativeLaunchContract({
    runtimeMode: () => 'development',
    appRoot: () => fixture.appRoot,
    resourcesRoot: () => fixture.resourcesRoot
  }, { command: 'python.exe', launchCommand: 'pythonw.exe' });
  assert.equal(launch.runtimeMode, 'development');
  assert.equal(launch.moduleRoot, fs.realpathSync(fixture.moduleRoot));
  assert.equal(launch.command, 'pythonw.exe');
  assert.equal(path.dirname(launch.vendoredPython), launch.moduleRoot);
});

test('development Coding MCP launch fails closed when resources belong to another checkout', (t) => {
  const current = nativeLaunchFixture(t, 'checkout-current');
  const foreign = nativeLaunchFixture(t, 'checkout-foreign');
  assert.throws(() => resolveNativeLaunchContract({
    runtimeMode: () => 'development',
    appRoot: () => current.appRoot,
    resourcesRoot: () => foreign.resourcesRoot
  }, { command: 'python.exe' }), { code: 'DEV_MCP_SOURCE_ROOT_MISMATCH' });
});

test('packaged Coding MCP launch accepts its packaged resource root', (t) => {
  const fixture = nativeLaunchFixture(t, 'packaged-app');
  const launch = resolveNativeLaunchContract({
    runtimeMode: () => 'packaged',
    appRoot: () => path.join(fixture.root, 'installed-app-root'),
    resourcesRoot: () => fixture.resourcesRoot
  }, { command: 'python.exe' });
  assert.equal(launch.runtimeMode, 'packaged');
  assert.equal(launch.moduleRoot, fs.realpathSync(fixture.moduleRoot));
});

test('proxy values from Windows settings are normalized', () => {
  assert.equal(normalizeProxyValue('127.0.0.1:7890'), 'http://127.0.0.1:7890');
  assert.equal(normalizeProxyValue('http=127.0.0.1:8080;https=127.0.0.1:7890'), 'http://127.0.0.1:7890');
  assert.equal(normalizeProxyValue('http://user:pass@127.0.0.1:7890'), '');
});

test('background runtime processes are hidden and detached from Recovery Host lifetime', () => {
  const fs = require('node:fs');
  const path = require('node:path');
  const root = path.resolve(__dirname, '..');
  for (const relative of ['electron/services/nativeService.js', 'electron/services/tunnelService.js']) {
    const source = fs.readFileSync(path.join(root, relative), 'utf8');
    assert.match(source, /windowsHide:\s*true/);
    assert.match(source, /detached:\s*true/);
  }
  const runner = fs.readFileSync(path.join(root, 'electron/services/commandRunner.js'), 'utf8');
  assert.doesNotMatch(runner, /spawnDetached/);
  // Process launch policy is shared by the extracted process helper rather
  // than duplicated in server.py.
  const processPolicy = fs.readFileSync(path.join(root, 'resources/coding-tools-mcp/coding_tools_mcp/processes.py'), 'utf8');
  assert.match(processPolicy, /def hidden_process_popen_kwargs/);
  assert.match(processPolicy, /CREATE_NO_WINDOW/);
  const execTools = fs.readFileSync(path.join(root, 'resources/coding-tools-mcp/coding_tools_mcp/exec_tools.py'), 'utf8');
  assert.match(execTools, /encoding="utf-8"/);
});

test('runtime state migration keeps only current native and tunnel fields', () => {
  assert.deepEqual(
    currentRuntimeState({
      nativePid: 1,
      nativeProcessStartToken: '10000000000000001',
      tunnelPid: 2,
      tunnelProcessStartToken: '10000000000000002',
      tunnelStartedAt: '2026-08-17T00:00:00.000Z',
      tunnelId: 'tunnel-device-a',
      tunnelFingerprint: 'f'.repeat(64),
      tunnelDeviceId: '12345678-1234-4123-8123-123456789abc',
      tunnelDeviceInstanceId: 'device-instance-0001',
      nativeCodeRevision: 'abc',
      nativeRuntimeMode: 'development',
      nativeModuleRoot: 'E:\\DEV\\Codex-web\\resources\\coding-tools-mcp',
      obsoletePid: 3
    }),
    {
      nativePid: 1,
      nativeProcessStartToken: '10000000000000001',
      tunnelPid: 2,
      tunnelProcessStartToken: '10000000000000002',
      tunnelStartedAt: '2026-08-17T00:00:00.000Z',
      tunnelId: 'tunnel-device-a',
      tunnelFingerprint: 'f'.repeat(64),
      tunnelDeviceId: '12345678-1234-4123-8123-123456789abc',
      tunnelDeviceInstanceId: 'device-instance-0001',
      nativeCodeRevision: 'abc',
      nativeRuntimeMode: 'development',
      nativeModuleRoot: 'E:\\DEV\\Codex-web\\resources\\coding-tools-mcp'
    }
  );
});

test('native revision status is pending only when the live process has a captured revision', () => {
  const paths = {
    stateFile: () => runtimeStatePath,
    appRoot: () => path.resolve(__dirname, '..'),
    resourcesRoot: () => path.resolve(__dirname, '..', 'resources')
  };
  const revisions = {
    status: (_component, runningRevision) => ({
      running_revision: runningRevision || null,
      disk_revision: 'disk-revision',
      update_pending: runningRevision ? runningRevision !== 'disk-revision' : null,
      state: runningRevision ? (runningRevision === 'disk-revision' ? 'current' : 'update_pending') : 'unknown'
    })
  };
  const processStartToken = '10000000000000001';
  let observerCalls = 0;
  const native = new NativeService({ info() {} }, paths, revisions, null, {
    processIdentityObserver: (pid) => {
      observerCalls += 1;
      return { state: 'live', pid, process_start_token: processStartToken };
    }
  });
  try {
    fs.writeFileSync(runtimeStatePath, JSON.stringify({ nativePid: process.pid, nativeProcessStartToken: processStartToken, nativeCodeRevision: 'running-revision' }));
    const pending = native.revisionStatus({
      verifiedProcessIdentity: { pid: process.pid, process_start_token: processStartToken }
    });
    assert.equal(pending.update_pending, true);
    assert.equal(pending.state, 'update_pending');
    assert.equal(observerCalls, 0, 'an exact identity from the same health snapshot must prevent a duplicate blocking probe');

    fs.writeFileSync(runtimeStatePath, JSON.stringify({ nativePid: process.pid }));
    const legacy = native.revisionStatus();
    assert.equal(legacy.running_revision, null);
    assert.equal(legacy.update_pending, false);
    assert.equal(legacy.state, 'stopped');
  } finally {
    fs.writeFileSync(runtimeStatePath, JSON.stringify({ manualStop: false }));
  }
});

test('runtime recovery projection exposes only local typed supervisor evidence', () => {
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({}) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.recovering = true;
  orchestrator.heartbeatFailures = 3;
  orchestrator.heartbeatFailureKind = 'tunnel_unavailable';
  orchestrator.recoveryAttempts = 2;
  orchestrator.nextRecoveryAt = 123456;
  orchestrator.autoRecoveryBlocked = true;
  orchestrator.lastStartFailure = 'typed local failure';
  orchestrator.deferredRecoveryCount = 1;
  assert.deepEqual(orchestrator.recoveryStatus(), {
    recovering: true,
    failures: 3,
    failureKind: 'tunnel_unavailable',
    recoveryAttempts: 2,
    nextRecoveryAt: 123456,
    recoveryBlocked: true,
    lastStartFailure: 'typed local failure',
    deferredRecoveryCount: 1,
    lastFailureAt: null,
    lastRecoveryAt: null,
    lastHealthyAt: null,
    downtimeMs: 0,
    failureElapsedMs: 0,
    mcpHealthFailureKind: null,
    mcpHealthFailureDeterministic: false
  });
});

test('runtime recovery projection records failure and recovery time markers', async () => {
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({}) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.lightweightSnapshot = async () => ({ fullyReady: true });
  const before = Date.now();
  orchestrator.heartbeatFailures = 2;
  orchestrator.heartbeatFailureSince = before - 30_000;
  const recovered = await orchestrator.supervise();
  assert.equal(recovered.failures, 0);
  assert.ok(recovered.lastFailureAt === null, 'streak đã kết thúc nên không còn mốc fail');
  assert.ok(recovered.lastRecoveryAt && Date.parse(recovered.lastRecoveryAt) >= before - 5, 'phải ghi mốc khôi phục');
  assert.ok(recovered.lastHealthyAt && Date.parse(recovered.lastHealthyAt) >= before - 5, 'phải ghi mốc healthy');
  assert.ok(recovered.downtimeMs >= 29_000, `downtime phải cộng dồn chuỗi lỗi, nhận ${recovered.downtimeMs}`);
  assert.equal(recovered.failureElapsedMs, 0);
});

test('runtime recovery projection marks when a failure streak starts', async () => {
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.lightweightSnapshot = async () => ({ fullyReady: false, mcpRunning: false, nativeAlive: false });
  orchestrator.restart = async () => {};
  orchestrator.recoverMcpOnly = async () => {};
  orchestrator.recoverTunnelOnly = async () => {};
  orchestrator.isManuallyStopped = () => false;
  const before = Date.now();
  const first = await orchestrator.supervise();
  assert.equal(first.failures, 1);
  assert.ok(first.lastFailureAt, 'lần fail đầu phải ghi mốc thời gian');
  assert.ok(Date.parse(first.lastFailureAt) >= before - 5);
  assert.ok(Number(first.failureElapsedMs) >= 0);
});

test('revision observation failure cannot break runtime supervision', () => {
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({}) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.native = { revisionStatus: () => { throw new Error('observer failed'); } };
  assert.deepEqual(orchestrator.codingMcpRevisionStatus(), {
    running_revision: null,
    disk_revision: null,
    update_pending: null,
    state: 'unavailable',
    error_code: 'REVISION_UNAVAILABLE'
  });
});

test('connector contract stays pending until current tools/list rediscovery is observed', () => {
  fs.writeFileSync(runtimeStatePath, JSON.stringify({ manualStop: false }), 'utf8');
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: 'C:\\work\\one' }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  const contract = { schema_version: 1, profile: 'smart-v3', sha256: 'a'.repeat(64) };
  const pending = orchestrator.connectorContractStatus(contract);
  assert.equal(pending.contractState, 'CHANGED_NEEDS_DISCOVERY');
  assert.equal(pending.refreshRequired, true);
  assert.equal(pending.rediscovered, false);
  assert.throws(
    () => orchestrator.acknowledgeConnectorContractHash(contract),
    (error) => error?.code === 'CONNECTOR_CONTRACT_NOT_REDISCOVERED'
  );
  const discovery = {
    current_contract_observed: true,
    identity_source: 'attested_transport',
    attestation_verified: true,
    contract_sha256: contract.sha256,
    observed_at: '2026-08-18T00:00:00.000Z',
    process_instance_id: 'detached-process-0001',
    server_instance_id: 'detached-server-00001'
  };
  assert.equal(orchestrator.connectorContractStatus(contract, discovery).contractState, 'CHANGED_DISCOVERED_NEEDS_ACK');
  assert.throws(
    () => orchestrator.synchronizeConnectorContract(contract, discovery),
    (error) => error?.code === 'CONNECTOR_CONTRACT_NOT_REDISCOVERED'
  );
  assert.equal(JSON.parse(fs.readFileSync(runtimeStatePath, 'utf8')).chatgptToolContractSha256, undefined);
});

test('runtime snapshots expose rediscovery without implicitly acknowledging a changed contract', async () => {
  const acknowledgedSha = 'b'.repeat(64);
  const currentSha = 'c'.repeat(64);
  const activationEpochId = 'activation-runtime-snapshot-0001';
  const processInstanceId = 'runtime-process-snapshot-0001';
  const serverInstanceId = 'runtime-server-snapshot-00001';
  const contract = { schema_version: 1, profile: 'smart-v3', sha256: currentSha };
  const discovery = {
    current_contract_observed: true,
    identity_source: 'attested_transport',
    attestation_verified: true,
    contract_sha256: currentSha,
    observed_at: '2026-08-26T00:00:00.000Z',
    process_instance_id: processInstanceId,
    server_instance_id: serverInstanceId,
    activation_epoch_id: activationEpochId
  };
  fs.writeFileSync(runtimeStatePath, JSON.stringify({
    manualStop: false,
    chatgptToolContractSha256: acknowledgedSha,
    chatgptToolContractAcknowledgedAt: '2026-08-25T00:00:00.000Z'
  }), 'utf8');
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: 'C:\\work\\one' }) },
    secrets: { get: () => 'token', status: () => ({}) },
    environment: { inspect: async () => ({}) },
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    activationEpochId
  });
  orchestrator.currentMcpHealth = async () => ({
    ready: true,
    activation_epoch_id: activationEpochId,
    process_instance_id: processInstanceId,
    instance_id: serverInstanceId,
    tool_contract: contract,
    connector_tool_discovery: discovery
  });
  orchestrator.native = {
    status: async () => true,
    revisionStatus: () => ({ running_revision: 'r', disk_revision: 'r', update_pending: false, state: 'current' })
  };
  orchestrator.tunnel = { status: async () => true };
  orchestrator.activationEpochStatus = () => ({ admission_open: true, update_incomplete: false });
  orchestrator.gitStatus = async () => ({ available: true, branch: 'main', head: null, head_short: null, dirty: true });

  const lightweight = await orchestrator.lightweightSnapshot();
  assert.equal(lightweight.componentsReady, true);
  assert.equal(lightweight.connectorReady, false);
  assert.equal(lightweight.fullyReady, false);
  assert.equal(lightweight.updateIncomplete, true);
  assert.equal(lightweight.connectorContractState, 'CHANGED_DISCOVERED_NEEDS_ACK');
  assert.equal(lightweight.connectorRediscovered, true);
  assert.equal(lightweight.connectorRefreshRequired, false);
  assert.equal(lightweight.connectorAcknowledgementPending, true);
  assert.equal(lightweight.connectorContractAcknowledgedSha256, acknowledgedSha);
  assert.equal(lightweight.toolContract.sha256, currentSha);

  const snapshot = await orchestrator.snapshot({ force: true, reason: 'test-read-only-connector-receipt' });
  assert.equal(snapshot.status.connectorContractState, 'CHANGED_DISCOVERED_NEEDS_ACK');
  assert.equal(snapshot.status.connectorRediscovered, true);
  assert.equal(snapshot.status.connectorAcknowledgementPending, true);
  assert.equal(snapshot.status.connectorContractAcknowledgedSha256, acknowledgedSha);
  assert.equal(JSON.parse(fs.readFileSync(runtimeStatePath, 'utf8')).chatgptToolContractSha256, acknowledgedSha);

  assert.throws(
    () => orchestrator.acknowledgeConnectorContractHash(contract, discovery),
    (error) => error?.code === 'CONNECTOR_CONTRACT_NOT_REDISCOVERED'
  );
  assert.equal(JSON.parse(fs.readFileSync(runtimeStatePath, 'utf8')).chatgptToolContractSha256, acknowledgedSha);
  const acknowledged = orchestrator.acknowledgeExactConnectorDiscovery({
    ready: true,
    activation_epoch_id: activationEpochId,
    process_instance_id: processInstanceId,
    instance_id: serverInstanceId,
    tool_contract: contract,
    connector_tool_discovery: discovery
  }, { activationEpochId, nowUnixMs: Date.now() });
  assert.equal(acknowledged.contractState, 'CURRENT_ACKNOWLEDGED');
  assert.equal(JSON.parse(fs.readFileSync(runtimeStatePath, 'utf8')).chatgptToolContractSha256, currentSha);
  const ready = await orchestrator.lightweightSnapshot();
  assert.equal(ready.componentsReady, true);
  assert.equal(ready.connectorReady, true);
  assert.equal(ready.fullyReady, true);
  assert.equal(ready.updateIncomplete, false);
  fs.writeFileSync(runtimeStatePath, JSON.stringify({ manualStop: false }), 'utf8');
});

test('live runtime snapshot rejects a discovery receipt from a different MCP process tuple', async () => {
  const acknowledgedSha = 'b'.repeat(64);
  const currentSha = 'c'.repeat(64);
  const activationEpochId = 'activation-live-tuple-mismatch-0001';
  const contract = { schema_version: 1, profile: 'smart-v3', sha256: currentSha };
  const discovery = {
    current_contract_observed: true,
    identity_source: 'attested_transport',
    attestation_verified: true,
    contract_sha256: currentSha,
    observed_at: new Date(Date.now() - 10).toISOString(),
    process_instance_id: 'retired-process-tuple-0001',
    server_instance_id: 'retired-server-tuple-00001',
    activation_epoch_id: activationEpochId
  };
  const health = {
    ready: true,
    activation_epoch_id: activationEpochId,
    process_instance_id: 'current-process-tuple-0001',
    instance_id: 'current-server-tuple-00001',
    tool_contract: contract,
    connector_tool_discovery: discovery
  };
  fs.writeFileSync(runtimeStatePath, JSON.stringify({
    manualStop: false,
    chatgptToolContractSha256: acknowledgedSha,
    chatgptToolContractSchemaVersion: 1,
    chatgptToolContractProfile: 'smart-v3'
  }), 'utf8');
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: 'C:\\work\\one' }) },
    secrets: { get: () => 'token', status: () => ({}) },
    environment: { inspect: async () => ({}) },
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    activationEpochId
  });
  orchestrator.currentMcpHealth = async () => health;
  orchestrator.native = {
    status: async () => true,
    revisionStatus: () => ({ running_revision: 'r', disk_revision: 'r', update_pending: false, state: 'current' })
  };
  orchestrator.tunnel = { status: async () => true };
  orchestrator.activationEpochStatus = () => ({ admission_open: true, update_incomplete: false });
  orchestrator.gitStatus = async () => ({ available: true, branch: 'main', head: null, head_short: null, dirty: true });

  // Detached diagnostics still parse the receipt, but the live projection is
  // bound to the exact health process/server/epoch tuple and must reject it.
  assert.equal(orchestrator.connectorContractStatus(contract, discovery).rediscovered, true);
  const live = await orchestrator.lightweightSnapshot();
  assert.equal(live.connectorRediscovered, false);
  assert.equal(live.connectorRediscoveredAt, null);
  assert.equal(live.connectorContractState, 'CHANGED_NEEDS_DISCOVERY');
  assert.equal(live.connectorRefreshRequired, true);
  assert.equal(live.connectorReady, false);
  assert.equal(live.fullyReady, false);
  fs.writeFileSync(runtimeStatePath, JSON.stringify({ manualStop: false }), 'utf8');
});

test('activation connector acknowledgement accepts only an exact current-process discovery receipt', () => {
  const acknowledgedSha = 'b'.repeat(64);
  const currentSha = 'c'.repeat(64);
  const activationEpochId = 'activation-connector-epoch-0001';
  const nowUnixMs = Date.now();
  fs.writeFileSync(runtimeStatePath, JSON.stringify({
    manualStop: false,
    chatgptToolContractSha256: acknowledgedSha,
    chatgptToolContractSchemaVersion: 1,
    chatgptToolContractProfile: 'smart-v3'
  }), 'utf8');
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: 'C:\\work\\one' }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    activationEpochId
  });
  const health = {
    ready: true,
    activation_epoch_id: activationEpochId,
    process_instance_id: 'process-current',
    instance_id: 'server-current',
    tool_contract: { schema_version: 1, profile: 'smart-v3', sha256: currentSha },
    connector_tool_discovery: {
      current_contract_observed: true,
      identity_source: 'attested_transport',
      attestation_verified: true,
      contract_sha256: currentSha,
      observed_at: new Date(nowUnixMs - 1).toISOString(),
      process_instance_id: 'process-current',
      server_instance_id: 'server-current',
      activation_epoch_id: activationEpochId
    }
  };
  assert.throws(
    () => orchestrator.acknowledgeExactConnectorDiscovery({
      ...health,
      connector_tool_discovery: {
        ...health.connector_tool_discovery,
        process_instance_id: 'process-retired'
      }
    }, { activationEpochId, nowUnixMs }),
    { code: 'CONNECTOR_CONTRACT_NOT_REDISCOVERED' }
  );
  assert.equal(JSON.parse(fs.readFileSync(runtimeStatePath, 'utf8')).chatgptToolContractSha256, acknowledgedSha);

  assert.throws(
    () => orchestrator.acknowledgeExactConnectorDiscovery({
      ...health,
      connector_tool_discovery: {
        ...health.connector_tool_discovery,
        activation_epoch_id: 'activation-retired-connector-epoch-0001'
      }
    }, { activationEpochId, nowUnixMs }),
    { code: 'CONNECTOR_CONTRACT_NOT_REDISCOVERED' }
  );
  assert.equal(JSON.parse(fs.readFileSync(runtimeStatePath, 'utf8')).chatgptToolContractSha256, acknowledgedSha);

  for (const invalidHealth of [
    {
      ...health,
      connector_tool_discovery: {
        ...health.connector_tool_discovery,
        server_instance_id: 'server-retired'
      }
    },
    { ...health, process_instance_id: '' },
    { ...health, instance_id: '' },
    {
      ...health,
      connector_tool_discovery: {
        ...health.connector_tool_discovery,
        observed_at: new Date(nowUnixMs + 2_000).toISOString()
      }
    }
  ]) {
    assert.throws(
      () => orchestrator.acknowledgeExactConnectorDiscovery(invalidHealth, { activationEpochId, nowUnixMs }),
      { code: 'CONNECTOR_CONTRACT_NOT_REDISCOVERED' }
    );
    assert.equal(JSON.parse(fs.readFileSync(runtimeStatePath, 'utf8')).chatgptToolContractSha256, acknowledgedSha);
  }

  const futureDiscovery = {
    ...health.connector_tool_discovery,
    observed_at: new Date(nowUnixMs + 2_000).toISOString()
  };
  assert.equal(orchestrator.connectorContractStatus(health.tool_contract, futureDiscovery).rediscovered, false);

  const acknowledged = orchestrator.acknowledgeExactConnectorDiscovery(health, {
    activationEpochId,
    nowUnixMs
  });
  assert.equal(acknowledged.contractState, 'CURRENT_ACKNOWLEDGED');
  assert.equal(acknowledged.acknowledgedSha256, currentSha);
  assert.equal(acknowledged.rediscovered, true);
  assert.equal(JSON.parse(fs.readFileSync(runtimeStatePath, 'utf8')).chatgptToolContractSha256, currentSha);
  fs.writeFileSync(runtimeStatePath, JSON.stringify({ manualStop: false }), 'utf8');
});

test('official connector acknowledgement is bound to the exact health receipt', async (t) => {
  const acknowledgedSha = 'b'.repeat(64);
  const currentSha = 'c'.repeat(64);
  const activationEpochId = 'activation-official-connector-0001';
  const processInstanceId = 'official-process-connector-0001';
  const serverInstanceId = 'official-server-connector-00001';
  const token = 'official-connector-token';
  let health = {
    ready: true,
    workspace: 'C:\\work\\one',
    activation_epoch_id: activationEpochId,
    process_instance_id: processInstanceId,
    instance_id: serverInstanceId,
    tool_contract: { schema_version: 1, profile: 'smart-v3', sha256: currentSha },
    connector_tool_discovery: {
      current_contract_observed: true,
      identity_source: 'attested_transport',
      attestation_verified: true,
      contract_sha256: currentSha,
      observed_at: new Date(Date.now() - 10).toISOString(),
      process_instance_id: processInstanceId,
      server_instance_id: serverInstanceId,
      activation_epoch_id: activationEpochId
    }
  };
  fs.writeFileSync(runtimeStatePath, JSON.stringify({
    manualStop: false,
    chatgptToolContractSha256: acknowledgedSha,
    chatgptToolContractSchemaVersion: 1,
    chatgptToolContractProfile: 'smart-v3'
  }), 'utf8');
  const server = http.createServer((request, response) => {
    assert.equal(request.url, '/__control/health');
    assert.equal(request.headers.authorization, `Bearer ${token}`);
    const body = JSON.stringify(health);
    response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) });
    response.end(body);
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise((resolve) => server.close(resolve)));

  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: 'C:\\work\\one', mcpPort: server.address().port }) },
    secrets: { get: (name) => name === 'mcpAuthToken' ? token : '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    activationEpochId
  });
  orchestrator.snapshot = async () => ({ acknowledged: true });

  const acknowledged = await orchestrator.acknowledgeConnectorContract();
  assert.deepEqual(acknowledged, { acknowledged: true });
  const persisted = JSON.parse(fs.readFileSync(runtimeStatePath, 'utf8'));
  assert.equal(persisted.chatgptToolContractSha256, currentSha);
  assert.equal(persisted.chatgptToolContractRediscoveredSha256, currentSha);
  assert.equal(persisted.chatgptToolContractRediscoveredAt, health.connector_tool_discovery.observed_at);

  health = {
    ...health,
    connector_tool_discovery: {
      ...health.connector_tool_discovery,
      server_instance_id: 'retired-server-connector-00001'
    }
  };
  await assert.rejects(
    () => orchestrator.acknowledgeConnectorContract(),
    (error) => error?.code === 'CONNECTOR_CONTRACT_NOT_REDISCOVERED'
  );
  assert.equal(JSON.parse(fs.readFileSync(runtimeStatePath, 'utf8')).chatgptToolContractSha256, currentSha);
  fs.writeFileSync(runtimeStatePath, JSON.stringify({ manualStop: false }), 'utf8');
});

test('activation connector compatibility bootstrap is exact, no-workspace, and never claims rediscovery', () => {
  const acknowledgedSha = '34cbb4c3ce3668f86ef6340dcb210d07425814c40ba734180ee1c026c96d409c';
  const currentSha = '57ed56a4f008287d9d9fdef035fa248f91cce4d58e935280b28963e4126a8053';
  const activationEpochId = 'activation-compatible-bootstrap-0001';
  const processInstanceId = 'compatible-process-instance-0001';
  const serverInstanceId = 'compatible-server-instance-00001';
  const nowUnixMs = Date.now();
  const observedAt = new Date(nowUnixMs - 10).toISOString();
  fs.writeFileSync(runtimeStatePath, JSON.stringify({
    manualStop: false,
    chatgptToolContractSha256: acknowledgedSha,
    chatgptToolContractSchemaVersion: 1,
    chatgptToolContractProfile: 'smart-v3'
  }), 'utf8');
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: 'C:\\work\\one' }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    activationEpochId
  });
  const bootstrap = {
    observed: true,
    current_contract_contact: true,
    identity_source: 'attested_transport',
    attestation_verified: true,
    client_id: 'chatweb-connector-current',
    client_type: 'chatweb',
    method: 'tools/call',
    tool_name: 'workspace_context',
    workspace_accessed: false,
    contract_sha256: currentSha,
    activation_epoch_id: activationEpochId,
    process_instance_id: processInstanceId,
    server_instance_id: serverInstanceId,
    observed_at: observedAt
  };
  const health = {
    ready: true,
    activation_epoch_id: activationEpochId,
    process_instance_id: processInstanceId,
    instance_id: serverInstanceId,
    tool_contract: {
      schema_version: 1,
      profile: 'smart-v3',
      sha256: currentSha,
      compatible_predecessor_sha256: [acknowledgedSha]
    },
    connector_tool_discovery: null,
    connector_client_contact: null,
    connector_activation_bootstrap: bootstrap
  };

  for (const invalidBootstrap of [
    { ...bootstrap, process_instance_id: 'retired-process-instance-0001' },
    { ...bootstrap, server_instance_id: 'retired-server-instance-00001' },
    { ...bootstrap, activation_epoch_id: 'activation-retired-bootstrap-0001' },
    { ...bootstrap, client_type: 'generic-client' },
    { ...bootstrap, workspace_accessed: true },
    { ...bootstrap, contract_sha256: 'f'.repeat(64) },
    { ...bootstrap, observed_at: new Date(nowUnixMs + 60_000).toISOString() }
  ]) {
    assert.throws(
      () => orchestrator.acknowledgeExactConnectorDiscovery({
        ...health,
        connector_activation_bootstrap: invalidBootstrap
      }, { activationEpochId, nowUnixMs }),
      { code: 'CONNECTOR_CONTRACT_NOT_REDISCOVERED' }
    );
    assert.equal(JSON.parse(fs.readFileSync(runtimeStatePath, 'utf8')).chatgptToolContractSha256, acknowledgedSha);
  }

  const pending = orchestrator.connectorContractStatus(
    health.tool_contract,
    null,
    null,
    bootstrap
  );
  assert.equal(pending.contractState, 'CHANGED_COMPATIBLE_NEEDS_ACK');
  assert.equal(pending.bootstrapCurrent, true);
  assert.equal(pending.rediscovered, false);
  assert.equal(pending.acknowledgementPending, true);

  const acknowledged = orchestrator.acknowledgeExactConnectorDiscovery(health, {
    activationEpochId,
    nowUnixMs
  });
  assert.equal(acknowledged.contractState, 'CURRENT_COMPATIBLE_ACKNOWLEDGED');
  assert.equal(acknowledged.compatibilityAcknowledged, true);
  assert.equal(acknowledged.compatibilityAcknowledgedAt, observedAt);
  assert.equal(acknowledged.rediscovered, false);
  assert.equal(acknowledged.rediscoveredAt, null);
  assert.equal(acknowledged.acknowledgedSha256, currentSha);
  assert.deepEqual(orchestrator.connectorContractFreshness(health, acknowledged), {
    ready: true,
    mode: 'compatible_activation_bootstrap',
    observedAt
  });
  const persisted = JSON.parse(fs.readFileSync(runtimeStatePath, 'utf8'));
  assert.equal(persisted.chatgptToolContractCompatibilitySource, 'declared_exact_predecessor_activation_bootstrap');
  assert.equal(persisted.chatgptToolContractCompatibilityPredecessorSha256, acknowledgedSha);
  assert.equal(persisted.chatgptToolContractCompatibilityContactSha256, currentSha);
  assert.equal(persisted.chatgptToolContractCompatibilityProcessInstanceId, processInstanceId);
  assert.equal(persisted.chatgptToolContractCompatibilityServerInstanceId, serverInstanceId);
  assert.equal(persisted.chatgptToolContractCompatibilityActivationEpochId, activationEpochId);
  assert.equal(Object.hasOwn(persisted, 'chatgptToolContractRediscoveredAt'), false);

  const nextEpochId = 'activation-compatible-bootstrap-0002';
  const nextBootstrap = {
    ...bootstrap,
    activation_epoch_id: nextEpochId,
    process_instance_id: 'compatible-process-instance-0002',
    server_instance_id: 'compatible-server-instance-00002',
    observed_at: new Date(nowUnixMs - 5).toISOString()
  };
  const nextOrchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: 'C:\\work\\one' }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    activationEpochId: nextEpochId
  });
  const nextHealth = {
    ...health,
    activation_epoch_id: nextEpochId,
    process_instance_id: nextBootstrap.process_instance_id,
    instance_id: nextBootstrap.server_instance_id,
    connector_activation_bootstrap: nextBootstrap
  };
  const sameContractPending = nextOrchestrator.connectorContractStatus(
    nextHealth.tool_contract,
    null,
    null,
    nextBootstrap
  );
  assert.equal(sameContractPending.contractState, 'UNCHANGED_COMPATIBLE_NEEDS_ACK');
  const sameContractAcknowledged = nextOrchestrator.acknowledgeExactConnectorDiscovery(nextHealth, {
    activationEpochId: nextEpochId,
    nowUnixMs
  });
  assert.equal(sameContractAcknowledged.contractState, 'CURRENT_COMPATIBLE_ACKNOWLEDGED');
  assert.equal(sameContractAcknowledged.compatibilitySource, 'exact_current_contract_activation_bootstrap');
  assert.equal(sameContractAcknowledged.rediscovered, false);

  const currentDiscovery = {
    current_contract_observed: true,
    identity_source: 'attested_transport',
    attestation_verified: true,
    contract_sha256: currentSha,
    observed_at: new Date(nowUnixMs - 1).toISOString(),
    process_instance_id: nextBootstrap.process_instance_id,
    server_instance_id: nextBootstrap.server_instance_id,
    activation_epoch_id: nextEpochId
  };
  const rediscovered = nextOrchestrator.connectorContractStatus(
    nextHealth.tool_contract,
    currentDiscovery,
    null,
    nextBootstrap
  );
  assert.equal(rediscovered.contractState, 'CURRENT_ACKNOWLEDGED');
  assert.equal(rediscovered.rediscovered, true);
  assert.equal(rediscovered.acknowledgementPending, false);
  assert.deepEqual(nextOrchestrator.connectorContractFreshness({
    ...nextHealth,
    connector_tool_discovery: currentDiscovery
  }, rediscovered), {
    ready: true,
    mode: 'current_process_discovery',
    observedAt: currentDiscovery.observed_at
  });
  fs.writeFileSync(runtimeStatePath, JSON.stringify({ manualStop: false }), 'utf8');
});

test('managed connector attestation binds one Recovery Host secret to one exact MCP identity', () => {
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({}) },
    secrets: { get: () => '', set() {} },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  const health = {
    activation_epoch_id: 'activation-attestation-binding-0001',
    process_instance_id: 'process-attestation-0001',
    instance_id: 'server-attestation-0001',
    tool_contract: { sha256: 'a'.repeat(64) }
  };
  const secret = orchestrator.rotateConnectorAttestationSecret();
  const established = orchestrator.connectorAttestationForHealth(health, { establish: true, secret });
  assert.equal(established.secret, secret);
  assert.deepEqual(orchestrator.connectorAttestationForHealth(health), established);
  assert.throws(
    () => orchestrator.connectorAttestationForHealth({
      ...health,
      process_instance_id: 'replacement-process-attestation-0002'
    }),
    { code: 'CONNECTOR_ATTESTATION_BINDING_UNAVAILABLE' }
  );

  const adopted = new RuntimeOrchestrator({
    settings: { load: () => ({}) },
    secrets: { get: () => '', set() {} },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  adopted.connectorAttestationSecret = 'unrelated-recovery-host-secret';
  assert.throws(
    () => adopted.connectorAttestationForHealth(health),
    { code: 'CONNECTOR_ATTESTATION_BINDING_UNAVAILABLE' }
  );
});

test('native reuse binds a requested connector attestation secret to the launch digest', () => {
  const launchSecret = 'launch-secret-for-native-reuse';
  const rotatedSecret = 'rotated-secret-for-native-reuse';
  const digest = connectorAttestationSecretHash(launchSecret);
  const state = { nativeConnectorAttestationSecretHash: digest };

  assert.match(digest, /^[0-9a-f]{64}$/);
  assert.equal(connectorAttestationSecretMatches(state, launchSecret), true);
  assert.equal(connectorAttestationSecretMatches(state, rotatedSecret), false,
    'a rotated capability must force the exact stop/spawn path');
  assert.equal(connectorAttestationSecretMatches({}, rotatedSecret), false,
    'legacy live receipts without a digest must not be adopted under a new capability');
  assert.equal(connectorAttestationSecretMatches(state, ''), true,
    'callers that do not request a capability retain the legacy reuse behavior');
  assert.equal(JSON.stringify(state).includes(launchSecret), false,
    'the raw launch capability must never be persisted in the runtime receipt');

  const projected = currentRuntimeState({
    nativePid: 123,
    nativeConnectorAttestationSecretHash: digest,
    unrelated: launchSecret
  });
  assert.equal(projected.nativeConnectorAttestationSecretHash, digest);
  assert.equal(projected.unrelated, undefined);
});

test('connector contract state is unavailable without a current contract fingerprint', () => {
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: 'C:\\work\\one' }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  const unavailable = orchestrator.connectorContractStatus(null);
  assert.equal(unavailable.contractState, 'UNAVAILABLE');
  assert.equal(unavailable.available, false);
  assert.equal(unavailable.refreshRequired, false);
  assert.equal(unavailable.acknowledgementPending, false);
});

test('persisted matching connector SHA survives process restart without forcing rediscovery', () => {
  const contract = { schema_version: 1, profile: 'smart-v3', sha256: 'b'.repeat(64) };
  const activationEpochId = 'activation-persisted-connector-0001';
  const processInstanceId = 'persisted-process-connector-0001';
  const serverInstanceId = 'persisted-server-connector-00001';
  fs.writeFileSync(runtimeStatePath, JSON.stringify({
    manualStop: false,
    chatgptToolContractSha256: contract.sha256,
    chatgptToolContractAcknowledgedAt: '2026-08-18T00:00:00.000Z'
  }), 'utf8');
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: 'C:\\work\\one' }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    activationEpochId
  });

  const retainedAcknowledgement = orchestrator.connectorContractStatus(contract);
  assert.equal(retainedAcknowledgement.contractState, 'UNCHANGED_ACKNOWLEDGED');
  assert.equal(retainedAcknowledgement.acknowledgedSha256, contract.sha256);
  assert.equal(retainedAcknowledgement.rediscovered, false);
  assert.equal(retainedAcknowledgement.refreshRequired, false);
  assert.equal(retainedAcknowledgement.acknowledgementPending, false);
  assert.doesNotThrow(() => orchestrator.acknowledgeConnectorContractHash(contract));

  const changedContract = { ...contract, sha256: 'c'.repeat(64) };
  const changedWithoutDiscovery = orchestrator.connectorContractStatus(changedContract);
  assert.equal(changedWithoutDiscovery.contractState, 'CHANGED_NEEDS_DISCOVERY');
  assert.equal(changedWithoutDiscovery.refreshRequired, true);
  assert.equal(changedWithoutDiscovery.rediscovered, false);
  assert.throws(
    () => orchestrator.acknowledgeConnectorContractHash(changedContract),
    (error) => error?.code === 'CONNECTOR_CONTRACT_NOT_REDISCOVERED'
  );

  const discovery = {
    current_contract_observed: true,
    identity_source: 'attested_transport',
    attestation_verified: true,
    contract_sha256: changedContract.sha256,
    observed_at: '2026-08-23T21:40:00.000Z',
    process_instance_id: processInstanceId,
    server_instance_id: serverInstanceId,
    activation_epoch_id: activationEpochId
  };
  const currentDiscovery = orchestrator.connectorContractStatus(changedContract, discovery);
  assert.equal(currentDiscovery.contractState, 'CHANGED_DISCOVERED_NEEDS_ACK');
  assert.equal(currentDiscovery.refreshRequired, false);
  assert.equal(currentDiscovery.acknowledgementPending, true);
  assert.throws(
    () => orchestrator.acknowledgeConnectorContractHash(changedContract, discovery),
    (error) => error?.code === 'CONNECTOR_CONTRACT_NOT_REDISCOVERED'
  );
  const acknowledged = orchestrator.acknowledgeExactConnectorDiscovery({
    ready: true,
    activation_epoch_id: activationEpochId,
    process_instance_id: processInstanceId,
    instance_id: serverInstanceId,
    tool_contract: changedContract,
    connector_tool_discovery: discovery
  }, { activationEpochId, nowUnixMs: Date.now() });
  assert.equal(acknowledged.contractState, 'CURRENT_ACKNOWLEDGED');
  assert.equal(orchestrator.connectorContractStatus(changedContract, discovery).contractState, 'CURRENT_ACKNOWLEDGED');
});

test('reviewed exact predecessor requires live current-process ChatWeb contact before compatibility acknowledgement', () => {
  const acknowledgedSha = '34cbb4c3ce3668f86ef6340dcb210d07425814c40ba734180ee1c026c96d409c';
  const currentSha = '57ed56a4f008287d9d9fdef035fa248f91cce4d58e935280b28963e4126a8053';
  fs.writeFileSync(runtimeStatePath, JSON.stringify({
    manualStop: false,
    chatgptToolContractSha256: acknowledgedSha,
    chatgptToolContractAcknowledgedAt: '2026-08-25T03:33:57.999Z'
  }), 'utf8');
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: 'C:\\work\\one' }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  const contract = {
    schema_version: 1,
    profile: 'smart-v3',
    sha256: currentSha,
    compatible_predecessor_sha256: [acknowledgedSha]
  };

  const changed = orchestrator.connectorContractStatus(contract);
  assert.equal(changed.contractState, 'CHANGED_NEEDS_DISCOVERY');
  assert.equal(changed.refreshRequired, true);
  assert.equal(changed.rediscovered, false);
  assert.equal(changed.backwardCompatible, false);
  assert.equal(changed.compatibilitySource, null);
  assert.equal(changed.acknowledgedSha256, acknowledgedSha);

  const wrongContact = {
    current_contract_contact: true,
    method: 'tools/call',
    contract_sha256: 'f'.repeat(64),
    observed_at: '2026-08-26T06:00:00.000Z',
    process_instance_id: 'process-current',
    server_instance_id: 'server-current'
  };
  assert.equal(orchestrator.connectorContractStatus(contract, null, wrongContact).contractState, 'CHANGED_NEEDS_DISCOVERY');

  const contact = {
    current_contract_contact: true,
    identity_source: 'attested_transport',
    attestation_verified: true,
    method: 'tools/call',
    contract_sha256: currentSha,
    observed_at: '2026-08-26T06:01:00.000Z',
    process_instance_id: 'process-current',
    server_instance_id: 'server-current'
  };
  const compatible = orchestrator.connectorContractStatus(contract, null, contact);
  assert.equal(compatible.contractState, 'CHANGED_COMPATIBLE_NEEDS_ACK');
  assert.equal(compatible.refreshRequired, false);
  assert.equal(compatible.acknowledgementPending, true);
  assert.equal(compatible.rediscovered, false);
  assert.equal(compatible.backwardCompatible, true);
  assert.equal(compatible.compatibilitySource, 'declared_exact_predecessor_live_contact');
  assert.equal(compatible.compatibilityMetadataBackfillPending, true);

  assert.throws(
    () => orchestrator.synchronizeConnectorContract(contract, null, contact),
    (error) => error?.code === 'CONNECTOR_CONTRACT_NOT_REDISCOVERED'
  );
  const persisted = JSON.parse(fs.readFileSync(runtimeStatePath, 'utf8'));
  assert.equal(persisted.chatgptToolContractSha256, acknowledgedSha);
  assert.equal(persisted.chatgptToolContractSchemaVersion, undefined);
  assert.equal(persisted.chatgptToolContractProfile, undefined);
  assert.equal(Object.hasOwn(persisted, 'chatgptToolContractRediscoveredAt'), false);
  assert.equal(Object.hasOwn(persisted, 'chatgptToolContractRediscoveredSha256'), false);
  assert.equal(persisted.chatgptToolContractCompatibilitySource, undefined);
  assert.equal(persisted.chatgptToolContractCompatibilityPredecessorSha256, undefined);
  assert.equal(persisted.chatgptToolContractCompatibilityContactSha256, undefined);
  assert.equal(persisted.chatgptToolContractCompatibilityProcessInstanceId, undefined);
  assert.equal(persisted.chatgptToolContractCompatibilityServerInstanceId, undefined);
});

test('reviewed compatibility closure admits a skipped-version ChatWeb bootstrap without weakening identity gates', () => {
  const currentSha = 'd69436cabfbb6dca7b365df507f4b507857d9b29c11a44883fab77de54f67810';
  const directSha = 'd52c8895711d4655be0bdbe35cff6e3dcd1bd72f5caa98563ad37dd34835b677';
  const skippedSha = '98064347d3d27bec950b64d57319a3bc4a442bc12f6849a583cae7560f395f97';
  const activationEpochId = 'activation-skipped-version-0001';
  const processInstanceId = 'process-skipped-version-0001';
  const serverInstanceId = 'server-skipped-version-00001';
  const observedAt = new Date(Date.now() - 10).toISOString();
  fs.writeFileSync(runtimeStatePath, JSON.stringify({
    manualStop: false,
    chatgptToolContractSha256: skippedSha,
    chatgptToolContractSchemaVersion: 1,
    chatgptToolContractProfile: 'smart-v3'
  }), 'utf8');
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: 'C:\\work\\one' }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    activationEpochId
  });
  const contract = {
    schema_version: 1,
    profile: 'smart-v3',
    sha256: currentSha,
    compatible_predecessor_sha256: [directSha, skippedSha]
  };
  const bootstrap = {
    current_contract_contact: true,
    identity_source: 'attested_transport',
    attestation_verified: true,
    client_id: 'chatweb-skipped-version',
    client_type: 'chatweb',
    method: 'tools/call',
    tool_name: 'workspace_context',
    workspace_accessed: false,
    contract_sha256: currentSha,
    activation_epoch_id: activationEpochId,
    process_instance_id: processInstanceId,
    server_instance_id: serverInstanceId,
    observed_at: observedAt
  };
  const health = {
    ready: true,
    activation_epoch_id: activationEpochId,
    process_instance_id: processInstanceId,
    instance_id: serverInstanceId,
    tool_contract: contract,
    connector_tool_discovery: null,
    connector_client_contact: null,
    connector_activation_bootstrap: bootstrap
  };

  assert.equal(
    orchestrator.connectorContractStatus(contract, null, null, null, health).contractState,
    'CHANGED_NEEDS_DISCOVERY'
  );
  for (const invalidBootstrap of [
    { ...bootstrap, process_instance_id: 'wrong-process' },
    { ...bootstrap, server_instance_id: 'wrong-server' },
    { ...bootstrap, activation_epoch_id: 'wrong-epoch' },
    { ...bootstrap, client_type: 'generic-client' },
    { ...bootstrap, workspace_accessed: true }
  ]) {
    assert.equal(
      orchestrator.connectorContractStatus(contract, null, null, invalidBootstrap, health).contractState,
      'CHANGED_NEEDS_DISCOVERY'
    );
  }

  const compatible = orchestrator.connectorContractStatus(contract, null, null, bootstrap, health);
  assert.equal(compatible.contractState, 'CHANGED_COMPATIBLE_NEEDS_ACK');
  assert.equal(compatible.compatibilitySource, 'declared_exact_predecessor_activation_bootstrap');
  assert.equal(compatible.refreshRequired, false);

  const acknowledged = orchestrator.acknowledgeExactConnectorDiscovery(health, {
    activationEpochId,
    nowUnixMs: Date.now()
  });
  assert.equal(acknowledged.contractState, 'CURRENT_COMPATIBLE_ACKNOWLEDGED');
  assert.equal(acknowledged.acknowledgedSha256, currentSha);
  const persisted = JSON.parse(fs.readFileSync(runtimeStatePath, 'utf8'));
  assert.equal(persisted.chatgptToolContractCompatibilityPredecessorSha256, skippedSha);
  assert.equal(persisted.chatgptToolContractCompatibilityProcessInstanceId, processInstanceId);
  assert.equal(persisted.chatgptToolContractCompatibilityServerInstanceId, serverInstanceId);
  assert.equal(persisted.chatgptToolContractCompatibilityActivationEpochId, activationEpochId);
});

test('compatibility route stays fail closed for undeclared or boundary-changing contracts', () => {
  const acknowledgedSha = 'a'.repeat(64);
  const currentSha = 'b'.repeat(64);
  fs.writeFileSync(runtimeStatePath, JSON.stringify({
    manualStop: false,
    chatgptToolContractSha256: acknowledgedSha,
    chatgptToolContractSchemaVersion: 1,
    chatgptToolContractProfile: 'smart-v3'
  }), 'utf8');
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: 'C:\\work\\one' }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  const contact = {
    current_contract_contact: true,
    method: 'tools/call',
    contract_sha256: currentSha,
    observed_at: '2026-08-26T06:02:00.000Z',
    process_instance_id: 'process-current',
    server_instance_id: 'server-current'
  };

  const undeclared = { schema_version: 1, profile: 'smart-v3', sha256: currentSha, compatible_predecessor_sha256: [] };
  const undeclaredStatus = orchestrator.connectorContractStatus(undeclared, null, contact);
  assert.equal(undeclaredStatus.contractState, 'CHANGED_NEEDS_DISCOVERY');
  assert.equal(undeclaredStatus.refreshRequired, true);
  assert.equal(undeclaredStatus.backwardCompatible, false);

  const breaking = { schema_version: 2, profile: 'smart-v3', sha256: currentSha, compatible_predecessor_sha256: [acknowledgedSha] };
  const blocked = orchestrator.connectorContractStatus(breaking, null, contact);
  assert.equal(blocked.contractState, 'CHANGED_NEEDS_DISCOVERY');
  assert.equal(blocked.refreshRequired, true);
  assert.equal(blocked.backwardCompatible, false);
  assert.throws(
    () => orchestrator.acknowledgeConnectorContractHash(breaking, null, contact),
    (error) => error?.code === 'CONNECTOR_CONTRACT_NOT_REDISCOVERED'
  );
});

test('Coding MCP activation prepare forwards the checkpoint-bound source receipt', async (t) => {
  let observed = null;
  const token = 'activation-test-token';
  const server = http.createServer((request, response) => {
    let body = '';
    request.setEncoding('utf8');
    request.on('data', (chunk) => { body += chunk; });
    request.on('end', () => {
      observed = JSON.parse(body);
      const payload = JSON.stringify({ safe: true, code: 'READY', lifecycle_decision: { clean: true } });
      response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) });
      response.end(payload);
    });
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => server.close());
  const sourceCheckpoint = {
    checkpoint_id: 'checkpoint-forward-0001',
    run_id: 'run-forward-0001',
    wave_id: 'wave-forward-0001',
    proof_fingerprint: 'a'.repeat(64),
    git_head: 'b'.repeat(40)
  };
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: 'C:\\work\\one', mcpPort: server.address().port }) },
    secrets: { get: (name) => name === 'mcpAuthToken' ? token : '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.native = { status: async () => true };
  const result = await orchestrator.prepareCodeActivation({
    operationId: 'operation_forward_0001',
    expiresAtUnixMs: Date.now() + 30_000,
    sourceCheckpoint
  });
  assert.equal(result.safe, true);
  assert.deepEqual(observed.source_checkpoint, sourceCheckpoint);
});

test('Coding MCP activation prepare allows a valid response beyond the former five-second client window', { timeout: 12_000 }, async (t) => {
  const token = 'activation-slow-prepare-token';
  let observed = null;
  const server = http.createServer((request, response) => {
    assert.equal(request.url, '/__control/activation');
    assert.equal(request.method, 'POST');
    let body = '';
    request.setEncoding('utf8');
    request.on('data', (chunk) => { body += chunk; });
    request.on('end', () => {
      observed = JSON.parse(body);
      setTimeout(() => {
        const payload = JSON.stringify({ safe: true, code: 'READY', workspace: 'C:\\work\\one' });
        response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) });
        response.end(payload);
      }, 5_250);
    });
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => server.close());
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: 'C:\\work\\one', mcpPort: server.address().port }) },
    secrets: { get: (name) => name === 'mcpAuthToken' ? token : '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.native = { status: async () => true };

  const result = await orchestrator.prepareCodeActivation({
    operationId: 'operation_slow_prepare_0001',
    expiresAtUnixMs: Date.now() + 30_000
  });

  assert.equal(result.safe, true);
  assert.equal(observed.action, 'prepare');
  assert.equal(observed.operation_id, 'operation_slow_prepare_0001');
});

test('Coding MCP activation verify forwards acceptance-pending preservation', async (t) => {
  let observed = null;
  const token = 'activation-test-token';
  const server = http.createServer((request, response) => {
    let body = '';
    request.setEncoding('utf8');
    request.on('data', (chunk) => { body += chunk; });
    request.on('end', () => {
      observed = JSON.parse(body);
      const payload = JSON.stringify({ safe: true, code: 'READY', workspace: 'C:\\work\\one' });
      response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) });
      response.end(payload);
    });
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => server.close());
  const sourceCheckpoint = {
    checkpoint_id: 'checkpoint-verify-0001',
    run_id: 'run-verify-0001',
    wave_id: 'wave-verify-0001',
    proof_fingerprint: 'a'.repeat(64),
    git_head: 'b'.repeat(40)
  };
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace: 'C:\\work\\one', mcpPort: server.address().port }) },
    secrets: { get: (name) => name === 'mcpAuthToken' ? token : '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });

  const result = await orchestrator.verifyCodeActivation(
    'operation_verify_0001',
    sourceCheckpoint,
    true
  );

  assert.equal(result.safe, true);
  assert.deepEqual(observed, {
    action: 'verify',
    operation_id: 'operation_verify_0001',
    workspace: 'C:\\work\\one',
    source_checkpoint: sourceCheckpoint,
    allow_acceptance_pending: true
  });
});

test('supervisor consumes a fresh workspace-bound restart ticket exactly once', async () => {
  const workspace = 'C:\\work\\one';
  const ticketId = 'restart-ticket-0001';
  const calls = { fullClean: 0 };
  let activationOptions = null;
  const sourceCheckpoint = {
    checkpoint_id: 'checkpoint-supervisor-0001',
    run_id: 'run-supervisor-0001',
    wave_id: 'wave-supervisor-0001',
    proof_fingerprint: 'c'.repeat(64),
    git_head: 'd'.repeat(40)
  };
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace, autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.lightweightSnapshot = async () => ({ fullyReady: true, mcpRunning: true, nativeAlive: true, tunnelRunning: true });
  orchestrator.currentMcpHealth = async () => ({ process_instance_id: 'process-one', instance_id: 'server-one', tool_contract: { sha256: 'e'.repeat(64) } });
  orchestrator.revisions.disk = () => ({ revision: 'a'.repeat(64) });
  orchestrator.activationEpochStore = {
    load: () => ({
      current: {
        activation_epoch_id: 'epoch-supervisor-0001',
        operation_id: ticketId,
        state: 'HANDOFF'
      },
      history: []
    })
  };
  orchestrator.setFullCleanSourceCheckpointResolver(() => sourceCheckpoint);
  orchestrator.setFullCleanActivation({ restart: async (options) => {
    calls.fullClean += 1;
    activationOptions = options;
    return {
      full_clean_activation: true,
      activation_epoch_id: 'epoch-supervisor-0001',
      state: 'HANDOFF',
      admission_open: false,
      fully_ready: false
    };
  } });
  const now = Date.now();
  fs.writeFileSync(supervisorRequestPath, JSON.stringify({
    version: 1,
    action: 'restart',
    ticket_id: ticketId,
    operation_id: ticketId,
    activation_mode: 'full_clean_activation',
    full_clean_required: true,
    process_instance_id: 'process-one',
    server_instance_id: 'server-one',
    tool_contract_sha256: 'e'.repeat(64),
    workspace,
    requested_at_unix_ms: now - 1000,
    not_before_unix_ms: now - 1,
    expires_at_unix_ms: now + 30000
  }), 'utf8');
  const result = await orchestrator.supervise();
  assert.equal(calls.fullClean, 1);
  assert.equal(fs.existsSync(supervisorRequestPath), false);
  assert.equal(fs.existsSync(`${supervisorRequestPath}.processing`), false);
  assert.equal(result.supervisorRequest.ticketId, ticketId);
  assert.equal(result.supervisorRequest.operationId, ticketId);
  assert.equal(result.supervisorRequest.status, 'accepted');
  assert.equal(result.supervisorRequest.component, 'full_system');
  assert.equal(result.supervisorRequest.activation_mode, 'full_clean_activation');
  assert.equal(activationOptions.operationId, ticketId);
  assert.deepEqual(activationOptions.sourceCheckpoint, sourceCheckpoint);
  assert.equal(activationOptions.expectedDiskRevision, 'a'.repeat(64));
  assert.equal(activationOptions.expiresAtUnixMs, undefined,
    'ticket admission expiry must not become the durable full-clean execution deadline');
  assert.equal(activationOptions.automatic, undefined);
  assert.equal(activationOptions.mode, undefined);
});

test('supervisor resumes a claimed processing journal after a Recovery Host crash window', async () => {
  const workspace = 'C:\\work\\one';
  const ticketId = 'restart-processing-resume-0001';
  const calls = { fullClean: 0 };
  const sourceCheckpoint = {
    checkpoint_id: 'checkpoint-processing-resume-0001',
    run_id: 'run-processing-resume-0001',
    wave_id: 'wave-processing-resume-0001',
    proof_fingerprint: 'c'.repeat(64),
    git_head: 'd'.repeat(40)
  };
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace, autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.lightweightSnapshot = async () => ({ fullyReady: true, mcpRunning: true, nativeAlive: true, tunnelRunning: true });
  orchestrator.currentMcpHealth = async () => ({ process_instance_id: 'process-one', instance_id: 'server-one', tool_contract: { sha256: 'e'.repeat(64) } });
  orchestrator.revisions.disk = () => ({ revision: 'a'.repeat(64) });
  orchestrator.activationEpochStore = {
    load: () => ({
      current: { activation_epoch_id: 'epoch-processing-resume-0001', operation_id: ticketId, state: 'HANDOFF' },
      history: []
    })
  };
  orchestrator.setFullCleanSourceCheckpointResolver(() => sourceCheckpoint);
  orchestrator.setFullCleanActivation({ restart: async () => {
    calls.fullClean += 1;
    return { full_clean_activation: true, activation_epoch_id: 'epoch-processing-resume-0001', state: 'READY', admission_open: true, fully_ready: true };
  } });
  const now = Date.now();
  fs.writeFileSync(`${supervisorRequestPath}.processing`, JSON.stringify({
    version: 1,
    action: 'restart',
    ticket_id: ticketId,
    operation_id: ticketId,
    activation_mode: 'full_clean_activation',
    full_clean_required: true,
    process_instance_id: 'process-one',
    server_instance_id: 'server-one',
    tool_contract_sha256: 'e'.repeat(64),
    workspace,
    requested_at_unix_ms: now - 1000,
    not_before_unix_ms: now - 1,
    expires_at_unix_ms: now + 30000
  }), 'utf8');
  const result = await orchestrator.supervise();
  assert.equal(calls.fullClean, 1);
  assert.equal(result.supervisorRequest.status, 'completed');
  assert.equal(fs.existsSync(`${supervisorRequestPath}.processing`), false);
});

test('supervisor retains the processing journal across RUNTIME_BUSY and retries the same operation', async () => {
  const workspace = 'C:\\work\\one';
  const ticketId = 'restart-runtime-busy-retry-0001';
  const sourceCheckpoint = {
    checkpoint_id: 'checkpoint-runtime-busy-retry-0001',
    run_id: 'run-runtime-busy-retry-0001',
    wave_id: 'wave-runtime-busy-retry-0001',
    proof_fingerprint: 'c'.repeat(64),
    git_head: 'd'.repeat(40)
  };
  let attempts = 0;
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace, autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.lightweightSnapshot = async () => ({ fullyReady: true, mcpRunning: true, nativeAlive: true, tunnelRunning: true });
  orchestrator.currentMcpHealth = async () => ({ process_instance_id: 'process-one', instance_id: 'server-one', tool_contract: { sha256: 'e'.repeat(64) } });
  orchestrator.revisions.disk = () => ({ revision: 'a'.repeat(64) });
  orchestrator.activationEpochStore = {
    load: () => ({
      current: attempts > 1 ? { activation_epoch_id: 'epoch-runtime-busy-retry-0001', operation_id: ticketId, state: 'HANDOFF' } : null,
      history: []
    })
  };
  orchestrator.setFullCleanSourceCheckpointResolver(() => sourceCheckpoint);
  orchestrator.setFullCleanActivation({ restart: async () => {
    attempts += 1;
    if (attempts === 1) throw Object.assign(new Error('initiating tool call still active'), { code: 'RUNTIME_BUSY' });
    return { full_clean_activation: true, activation_epoch_id: 'epoch-runtime-busy-retry-0001', state: 'READY', admission_open: true, fully_ready: true };
  } });
  const now = Date.now();
  fs.writeFileSync(supervisorRequestPath, JSON.stringify({
    version: 1,
    action: 'restart',
    ticket_id: ticketId,
    operation_id: ticketId,
    activation_mode: 'full_clean_activation',
    full_clean_required: true,
    process_instance_id: 'process-one',
    server_instance_id: 'server-one',
    tool_contract_sha256: 'e'.repeat(64),
    workspace,
    requested_at_unix_ms: now - 1000,
    not_before_unix_ms: now - 1,
    expires_at_unix_ms: now + 30000
  }), 'utf8');
  const deferred = await orchestrator.supervise();
  assert.equal(deferred.supervisorRequest.status, 'deferred');
  assert.equal(deferred.supervisorRequest.request_retained, true);
  assert.equal(fs.existsSync(`${supervisorRequestPath}.processing`), true);
  const completed = await orchestrator.supervise();
  assert.equal(completed.supervisorRequest.status, 'completed');
  assert.equal(attempts, 2);
  assert.equal(fs.existsSync(`${supervisorRequestPath}.processing`), false);
});

test('supervisor restart ticket fails closed without Recovery Host checkpoint authority', async () => {
  const workspace = 'C:\\work\\one';
  let mutationCalls = 0;
  let fenceCancellations = 0;
  const errors = [];
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace, autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error(message, details) { errors.push({ message, details }); } },
    emitProgress() {},
    fullCleanActivation: { restart: async () => { mutationCalls += 1; } }
  });
  orchestrator.lightweightSnapshot = async () => ({ fullyReady: true, mcpRunning: true, nativeAlive: true, tunnelRunning: true });
  orchestrator.currentMcpHealth = async () => ({ process_instance_id: 'process-one', instance_id: 'server-one', tool_contract: { sha256: 'e'.repeat(64) } });
  orchestrator.activationEpochStore = { load: () => ({ current: null, history: [] }) };
  orchestrator.cancelCodeActivation = async (operationId, options) => {
    assert.equal(operationId, 'ticket-no-authority');
    assert.equal(options?.strict, true);
    fenceCancellations += 1;
    return true;
  };
  const now = Date.now();
  fs.writeFileSync(supervisorRequestPath, JSON.stringify({
    version: 1,
    action: 'restart',
    ticket_id: 'ticket-no-authority',
    operation_id: 'ticket-no-authority',
    activation_mode: 'full_clean_activation',
    full_clean_required: true,
    process_instance_id: 'process-one',
    server_instance_id: 'server-one',
    tool_contract_sha256: 'e'.repeat(64),
    workspace,
    requested_at_unix_ms: now - 1000,
    not_before_unix_ms: now - 1,
    expires_at_unix_ms: now + 30000
  }), 'utf8');
  const result = await orchestrator.supervise();
  assert.equal(mutationCalls, 0);
  assert.equal(fenceCancellations, 1, 'a pre-epoch failure releases only the exact deferred fence');
  assert.equal(result.supervisorRequest.status, 'failed');
  assert.equal(result.supervisorRequest.ticketId, 'ticket-no-authority');
  assert.equal(result.supervisorRequest.operationId, 'ticket-no-authority');
  assert.equal(result.supervisorRequest.activation_mode, 'full_clean_activation');
  assert.equal(result.supervisorRequest.error.code, 'ACTIVATION_SOURCE_CHECKPOINT_UNAVAILABLE');
  assert.equal(errors.at(-1)?.details?.ticketId, 'ticket-no-authority');
});

test('exact stale-run supervisor maintenance uses checkpoint-free full-clean refresh', async () => {
  const workspace = 'C:\\work\\one';
  const ticketId = 'restart-exact-stale-maintenance-0001';
  const runIds = Array.from({ length: 64 }, (_value, index) => index.toString(16).padStart(32, '0'));
  const reason = `exact_stale_runs:${runIds.join(',')}`;
  assert.ok(reason.length > 1024);
  const restartCalls = [];
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace, autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    fullCleanActivation: {
      restart: async (options) => {
        restartCalls.push(options);
        return {
          full_clean_activation: true,
          activation_epoch_id: 'epoch-exact-stale-maintenance-0001',
          state: 'READY',
          admission_open: true,
          fully_ready: true
        };
      }
    }
  });
  orchestrator.lightweightSnapshot = async () => ({ fullyReady: true, mcpRunning: true, nativeAlive: true, tunnelRunning: true });
  orchestrator.currentMcpHealth = async () => ({ process_instance_id: 'process-one', instance_id: 'server-one', tool_contract: { sha256: 'e'.repeat(64) } });
  orchestrator.revisions.disk = () => ({ revision: 'a'.repeat(64) });
  orchestrator.activationEpochStore = {
    load: () => ({
      current: { activation_epoch_id: 'epoch-exact-stale-maintenance-0001', operation_id: ticketId, state: 'READY' },
      history: []
    })
  };
  const now = Date.now();
  fs.writeFileSync(supervisorRequestPath, JSON.stringify({
    version: 1,
    action: 'restart',
    ticket_id: ticketId,
    operation_id: ticketId,
    activation_mode: 'full_clean_activation',
    full_clean_required: true,
    process_instance_id: 'process-one',
    server_instance_id: 'server-one',
    tool_contract_sha256: 'e'.repeat(64),
    workspace,
    reason,
    requested_at_unix_ms: now - 1000,
    not_before_unix_ms: now - 1,
    expires_at_unix_ms: now + 30000
  }), 'utf8');

  const result = await orchestrator.supervise();
  assert.equal(restartCalls.length, 1);
  assert.equal(restartCalls[0].refresh, true);
  assert.equal(restartCalls[0].mode, 'full_clean_refresh');
  assert.equal(restartCalls[0].sourceCheckpoint, null);
  assert.equal(restartCalls[0].reason, reason);
  assert.equal(restartCalls[0].expiresAtUnixMs, undefined,
    'stale-run maintenance must retain the independent full-clean execution deadline after ticket admission');
  assert.equal(result.supervisorRequest.status, 'completed');
  assert.equal(result.supervisorRequest.activation_mode, 'full_clean_refresh');
});

test('supervisor never cancels or reopens a fence after a durable epoch binds the ticket operation', async () => {
  const workspace = 'C:\\work\\one';
  const ticketId = 'restart-epoch-bound-0001';
  let epochBound = false;
  let fenceCancellations = 0;
  const sourceCheckpoint = {
    checkpoint_id: 'checkpoint-supervisor-bound-0001',
    run_id: 'run-supervisor-bound-0001',
    wave_id: 'wave-supervisor-bound-0001',
    proof_fingerprint: 'c'.repeat(64),
    git_head: 'd'.repeat(40)
  };
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace, autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.lightweightSnapshot = async () => ({ fullyReady: true, mcpRunning: true, nativeAlive: true, tunnelRunning: true });
  orchestrator.currentMcpHealth = async () => ({ process_instance_id: 'process-one', instance_id: 'server-one', tool_contract: { sha256: 'e'.repeat(64) } });
  orchestrator.revisions.disk = () => ({ revision: 'a'.repeat(64) });
  orchestrator.setFullCleanSourceCheckpointResolver(() => sourceCheckpoint);
  orchestrator.activationEpochStore = {
    load: () => ({
      current: epochBound ? {
        activation_epoch_id: 'activation-supervisor-bound-0001',
        operation_id: ticketId,
        state: 'FAILED'
      } : null,
      history: []
    })
  };
  orchestrator.cancelCodeActivation = async () => { fenceCancellations += 1; return true; };
  orchestrator.setFullCleanActivation({
    restart: async () => {
      epochBound = true;
      throw Object.assign(new Error('replacement launch failed after durable epoch create'), { code: 'RECOVERY_REPLACEMENT_UNAVAILABLE' });
    }
  });
  const now = Date.now();
  fs.writeFileSync(supervisorRequestPath, JSON.stringify({
    version: 1,
    action: 'restart',
    ticket_id: ticketId,
    operation_id: ticketId,
    activation_mode: 'full_clean_activation',
    full_clean_required: true,
    process_instance_id: 'process-one',
    server_instance_id: 'server-one',
    tool_contract_sha256: 'e'.repeat(64),
    workspace,
    requested_at_unix_ms: now - 1000,
    not_before_unix_ms: now - 1,
    expires_at_unix_ms: now + 30000
  }), 'utf8');
  const result = await orchestrator.supervise();
  assert.equal(result.supervisorRequest.status, 'failed');
  assert.equal(result.supervisorRequest.error.code, 'RECOVERY_REPLACEMENT_UNAVAILABLE');
  assert.equal(epochBound, true);
  assert.equal(fenceCancellations, 0, 'durable FAILED/CLOSED epoch remains fail-closed and authoritative');
});

test('Recovery Host activation preflight capability is operation-bound and HMAC-authenticated', async (t) => {
  const token = 'token';
  const operationId = 'activation-operation-http-0002';
  const server = http.createServer((request, response) => {
    assert.equal(request.url, '/__control/activation');
    assert.equal(request.headers['x-coding-tools-activation-operation'], operationId);
    assert.equal(request.headers['x-coding-tools-activation-proof'], activationPreflightProof(token, operationId));
    const payload = { safe: true, code: 'READY', workspace: 'C:\\work\\one' };
    const body = JSON.stringify(payload);
    response.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) });
    response.end(body);
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise((resolve) => server.close(resolve)));
  const result = await readMcpActivationPreflight(server.address().port, token, { operationId });
  assert.equal(result.safe, true);
  assert.equal(activationPreflightProof(token, operationId), activationPreflightProof(token, operationId));
  assert.notEqual(activationPreflightProof(token, operationId), activationPreflightProof(token, `${operationId}-other`));
});

test('Coding MCP activation without a configured tunnel reports that no tunnel was preserved', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-mcp-activation-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const stateFile = path.join(root, 'runtime-state.json');
  fs.writeFileSync(stateFile, JSON.stringify({ nativeInstanceId: 'old-supervisor', nativeCodeRevision: 'a'.repeat(64) }));
  const expectedRevision = 'b'.repeat(64);
  const expiresAtUnixMs = Date.now() + 30_000;
  const paths = { stateFile: () => stateFile };
  const orchestrator = new RuntimeOrchestrator({
    paths,
    settings: { load: () => ({ workspace: root, mcpPort: 32123 }) },
    secrets: { get: () => 'token' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    revisionTracker: { disk: () => ({ revision: expectedRevision }) }
  });
  orchestrator.activationEpochStore = { current: () => null };
  orchestrator.validate = () => {};
  orchestrator.ensureToken = async () => 'token';
  let health = {
    ready: true,
    workspace: root,
    process_instance_id: 'old-process',
    instance_id: 'old-server',
    code_revision: 'a'.repeat(64)
  };
  orchestrator.currentMcpHealth = async () => health;
  const calls = { stop: 0, start: 0, tunnel: 0 };
  orchestrator.native = {
    stop: async () => { calls.stop += 1; return true; },
    start: async (_settings, _token, _progress, options) => {
      calls.start += 1;
      assert.equal(options.expectedCodeRevision, expectedRevision);
      assert.equal(options.expiresAtUnixMs, expiresAtUnixMs);
      assert.equal(options.activationProcessMutated, true);
      health = {
        ready: true,
        workspace: root,
        process_instance_id: 'new-process',
        instance_id: 'new-server',
        code_revision: expectedRevision
      };
      return { instanceId: 'new-supervisor', codeRevision: expectedRevision };
    },
    status: async () => true
  };
  orchestrator.tunnel = { stop: async () => { calls.tunnel += 1; } };

  const result = await orchestrator.activateCodingMcpUpdate(expectedRevision, { expiresAtUnixMs });

  assert.equal(result.old_instance_id, 'old-process');
  assert.equal(result.new_instance_id, 'new-process');
  assert.equal(result.old_server_instance_id, 'old-server');
  assert.equal(result.new_server_instance_id, 'new-server');
  assert.equal(result.new_revision, expectedRevision);
  assert.equal(result.disk_revision_verified, true);
  assert.equal(result.tunnel_preserved, false);
  assert.equal(result.tunnel_attestation_refreshed, false);
  assert.deepEqual(calls, { stop: 1, start: 1, tunnel: 0 });
});

test('Coding MCP activation refuses an expired request immediately before stopping the old process', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-mcp-activation-expired-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const expectedRevision = 'b'.repeat(64);
  const orchestrator = new RuntimeOrchestrator({
    paths: { stateFile: () => path.join(root, 'runtime-state.json') },
    settings: { load: () => ({ workspace: root, mcpPort: 32123 }) },
    secrets: { get: () => 'token' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    revisionTracker: { disk: () => ({ revision: expectedRevision }) }
  });
  orchestrator.activationEpochStore = { current: () => null };
  orchestrator.validate = () => {};
  orchestrator.ensureToken = async () => 'token';
  orchestrator.currentMcpHealth = async () => ({
    process_instance_id: 'old-process', instance_id: 'old-server', code_revision: 'a'.repeat(64)
  });
  let stopped = false;
  orchestrator.native = { stop: async () => { stopped = true; } };

  await assert.rejects(
    orchestrator.activateCodingMcpUpdate(expectedRevision, { expiresAtUnixMs: Date.now() - 1 }),
    { code: 'ACTIVATION_REQUEST_EXPIRED' }
  );
  assert.equal(stopped, false);
});

test('Coding MCP activation fails closed when disk revision changes after replacement identity verification', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-mcp-activation-post-drift-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const stateFile = path.join(root, 'runtime-state.json');
  fs.writeFileSync(stateFile, JSON.stringify({ nativeInstanceId: 'old-supervisor', nativeCodeRevision: 'a'.repeat(64) }));
  const expectedRevision = 'b'.repeat(64);
  const changedRevision = 'c'.repeat(64);
  let revisionReads = 0;
  const orchestrator = new RuntimeOrchestrator({
    paths: { stateFile: () => stateFile },
    settings: { load: () => ({ workspace: root, mcpPort: 32123 }) },
    secrets: { get: () => 'token' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    revisionTracker: { disk: () => ({ revision: ++revisionReads === 1 ? expectedRevision : changedRevision }) }
  });
  orchestrator.activationEpochStore = { current: () => null };
  orchestrator.validate = () => {};
  orchestrator.ensureToken = async () => 'token';
  let health = {
    process_instance_id: 'old-process', instance_id: 'old-server', code_revision: 'a'.repeat(64)
  };
  orchestrator.currentMcpHealth = async () => health;
  const calls = { stop: 0, start: 0, tunnel: 0 };
  orchestrator.native = {
    stop: async () => { calls.stop += 1; return true; },
    start: async () => {
      calls.start += 1;
      health = { process_instance_id: 'new-process', instance_id: 'new-server', code_revision: expectedRevision };
      return { instanceId: 'new-supervisor', codeRevision: expectedRevision };
    },
    status: async () => true
  };
  orchestrator.tunnel = { stop: async () => { calls.tunnel += 1; } };

  await assert.rejects(orchestrator.activateCodingMcpUpdate(expectedRevision), {
    code: 'REVISION_CHANGED_DURING_ACTIVATION'
  });
  assert.deepEqual(calls, { stop: 2, start: 1, tunnel: 0 });
});

test('Coding MCP activation fails before stop when the requested revision changed', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-mcp-activation-stale-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const paths = { stateFile: () => path.join(root, 'runtime-state.json') };
  const orchestrator = new RuntimeOrchestrator({
    paths,
    settings: { load: () => ({ workspace: root, mcpPort: 32123 }) },
    secrets: { get: () => 'token' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    revisionTracker: { disk: () => ({ revision: 'c'.repeat(64) }) }
  });
  orchestrator.activationEpochStore = { current: () => null };
  orchestrator.validate = () => {};
  orchestrator.ensureToken = async () => 'token';
  let stopped = false;
  orchestrator.native = { stop: async () => { stopped = true; } };

  await assert.rejects(orchestrator.activateCodingMcpUpdate('b'.repeat(64)), { code: 'REVISION_CHANGED' });
  assert.equal(stopped, false);
});

test('supervisor rejects stale or wrong-workspace restart tickets without restarting', async () => {
  const workspace = 'C:\\work\\one';
  const calls = { restart: 0 };
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace, autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.lightweightSnapshot = async () => ({ fullyReady: true, mcpRunning: true, nativeAlive: true, tunnelRunning: true });
  orchestrator.restart = async () => { calls.restart += 1; };
  const now = Date.now();
  fs.writeFileSync(supervisorRequestPath, JSON.stringify({
    version: 1,
    action: 'restart',
    ticket_id: 'ticket-stale',
    workspace: 'C:\\work\\other',
    requested_at_unix_ms: now - 120000,
    not_before_unix_ms: now - 119000,
    expires_at_unix_ms: now - 60000
  }), 'utf8');
  await orchestrator.supervise();
  assert.equal(calls.restart, 0);
  assert.equal(fs.existsSync(supervisorRequestPath), false);
});

test('supervisor rejects every malformed restart envelope without invoking full-clean activation', async () => {
  const workspace = 'C:\\work\\one';
  let fullCleanCalls = 0;
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace, autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    fullCleanActivation: { restart: async () => { fullCleanCalls += 1; } }
  });
  orchestrator.lightweightSnapshot = async () => ({ fullyReady: true, mcpRunning: true, nativeAlive: true, tunnelRunning: true });
  const now = Date.now();
  const base = {
    version: 1,
    action: 'restart',
    ticket_id: 'restart-ticket-0001',
    operation_id: 'restart-ticket-0001',
    activation_mode: 'full_clean_activation',
    full_clean_required: true,
    process_instance_id: 'process-one',
    server_instance_id: 'server-one',
    tool_contract_sha256: 'e'.repeat(64),
    workspace,
    requested_at_unix_ms: now - 1000,
    not_before_unix_ms: now - 1,
    expires_at_unix_ms: now + 30000
  };
  const malformed = [
    ['missing operation_id', ({ ...base, operation_id: undefined })],
    ['operation mismatch', ({ ...base, operation_id: 'restart-ticket-other-0001' })],
    ['short ticket id', ({ ...base, ticket_id: 'restart-short', operation_id: 'restart-short' })],
    ['leading underscore', ({ ...base, ticket_id: '_restart-ticket-0001', operation_id: '_restart-ticket-0001' })],
    ['leading hyphen', ({ ...base, ticket_id: '-restart-ticket-0001', operation_id: '-restart-ticket-0001' })],
    ['invalid character', ({ ...base, ticket_id: 'restart-ticket-00!', operation_id: 'restart-ticket-00!' })],
    ['overlong ticket id', ({ ...base, ticket_id: `restart-${'a'.repeat(123)}`, operation_id: `restart-${'a'.repeat(123)}` })],
    ['numeric ticket id', ({ ...base, ticket_id: 1234567890123456, operation_id: 1234567890123456 })]
  ];
  for (const [label, ticket] of malformed) {
    fs.writeFileSync(supervisorRequestPath, JSON.stringify(ticket), 'utf8');
    await orchestrator.supervise();
    assert.equal(fullCleanCalls, 0, label);
    assert.equal(fs.existsSync(supervisorRequestPath), false, label);
    assert.equal(fs.existsSync(`${supervisorRequestPath}.processing`), false, label);
  }
});

test('supervisor treats the exact ticket expiry instant as already expired', () => {
  const workspace = 'C:\\work\\one';
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace, autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  const now = Date.now();
  fs.writeFileSync(supervisorRequestPath, JSON.stringify({
    version: 1,
    action: 'restart',
    ticket_id: 'restart-expiry-boundary-0001',
    operation_id: 'restart-expiry-boundary-0001',
    activation_mode: 'full_clean_activation',
    full_clean_required: true,
    process_instance_id: 'process-one',
    server_instance_id: 'server-one',
    tool_contract_sha256: 'e'.repeat(64),
    workspace,
    requested_at_unix_ms: now - 1000,
    not_before_unix_ms: now - 1,
    expires_at_unix_ms: now
  }), 'utf8');
  const originalNow = Date.now;
  Date.now = () => now;
  try {
    assert.equal(orchestrator.pendingSupervisorRestartRequest(), null);
  } finally {
    Date.now = originalNow;
  }
  assert.equal(fs.existsSync(supervisorRequestPath), false);
  assert.equal(fs.existsSync(`${supervisorRequestPath}.processing`), false);
});

test('supervisor preserves an accepted ticket when reading its durable journal is uncertain', async () => {
  const workspace = 'C:\\work\\one';
  let fullCleanCalls = 0;
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace, autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    fullCleanActivation: { restart: async () => { fullCleanCalls += 1; } }
  });
  orchestrator.lightweightSnapshot = async () => ({ fullyReady: true, mcpRunning: true, nativeAlive: true, tunnelRunning: true });
  const now = Date.now();
  const ticket = {
    version: 1,
    action: 'restart',
    ticket_id: 'restart-read-uncertain-0001',
    operation_id: 'restart-read-uncertain-0001',
    activation_mode: 'full_clean_activation',
    full_clean_required: true,
    process_instance_id: 'process-one',
    server_instance_id: 'server-one',
    tool_contract_sha256: 'e'.repeat(64),
    workspace,
    requested_at_unix_ms: now - 1000,
    not_before_unix_ms: now - 1,
    expires_at_unix_ms: now + 30000
  };
  fs.writeFileSync(supervisorRequestPath, JSON.stringify(ticket), 'utf8');
  const originalReadFileSync = fs.readFileSync;
  fs.readFileSync = function uncertainSupervisorRead(filePath, ...args) {
    if (String(filePath) === supervisorRequestPath) {
      throw Object.assign(new Error('temporary sharing violation'), { code: 'EACCES' });
    }
    return originalReadFileSync.call(fs, filePath, ...args);
  };
  try {
    await orchestrator.supervise();
  } finally {
    fs.readFileSync = originalReadFileSync;
  }
  assert.equal(fullCleanCalls, 0);
  assert.equal(fs.existsSync(supervisorRequestPath), true);
  assert.equal(fs.existsSync(`${supervisorRequestPath}.processing`), false);
});

test('supervisor never recovers a restart ticket from json backup', async () => {
  const workspace = 'C:\\work\\one';
  const calls = { restart: 0 };
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace, autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.lightweightSnapshot = async () => ({ fullyReady: true, mcpRunning: true, nativeAlive: true, tunnelRunning: true });
  orchestrator.restart = async () => { calls.restart += 1; };
  const now = Date.now();
  fs.writeFileSync(supervisorRequestPath, '{invalid-json', 'utf8');
  fs.writeFileSync(`${supervisorRequestPath}.bak`, JSON.stringify({
    version: 1,
    action: 'restart',
    ticket_id: 'ticket-from-backup',
    workspace,
    requested_at_unix_ms: now - 1000,
    not_before_unix_ms: now - 1,
    expires_at_unix_ms: now + 30000
  }), 'utf8');
  await orchestrator.supervise();
  assert.equal(calls.restart, 0);
  assert.equal(fs.existsSync(supervisorRequestPath), false);
  assert.equal(fs.existsSync(`${supervisorRequestPath}.bak`), false);
});

test('supervisor recovers only the tunnel when MCP remains healthy', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: true,
    nativeAlive: true,
    tunnelRunning: false
  });
  await orchestrator.supervise();
  assert.equal(calls.tunnel, 1);
  assert.equal(calls.restart, 0);
});

test('automatic recovery latches a full-clean-required source refusal after one attempt', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: true,
    nativeAlive: true,
    tunnelRunning: false
  });
  const refusal = Object.assign(
    new Error('Coding MCP source changed; soft recovery requires full-clean activation.'),
    { code: 'UPDATE_INCOMPLETE', details: { full_clean_activation_required: true } }
  );
  orchestrator.recoverTunnelOnly = async () => {
    calls.tunnel += 1;
    throw refusal;
  };

  await orchestrator.supervise();
  assert.equal(calls.tunnel, 1);
  assert.equal(orchestrator.autoRecoveryBlocked, true);
  assert.equal(orchestrator.lastStartFailure, refusal.message);
  assert.equal(orchestrator.recoveryAttempts, 1);
  assert.equal(orchestrator.nextRecoveryAt, 0);

  const blocked = await orchestrator.supervise();
  assert.equal(calls.tunnel, 1, 'later watchdog ticks must not replay the same deterministic soft recovery');
  assert.equal(blocked.recoveryBlocked, true);
  assert.equal(blocked.lastStartFailure, refusal.message);
});

test('automatic recovery keeps transient failures eligible for bounded retry', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: true,
    nativeAlive: true,
    tunnelRunning: false
  });
  orchestrator.recoverTunnelOnly = async () => {
    calls.tunnel += 1;
    throw Object.assign(new Error('temporary tunnel transport failure'), { code: 'ECONNRESET' });
  };

  await orchestrator.supervise();
  assert.equal(calls.tunnel, 1);
  assert.equal(orchestrator.autoRecoveryBlocked, false);

  orchestrator.nextRecoveryAt = 0;
  await orchestrator.supervise();
  assert.equal(calls.tunnel, 2, 'a transient failure remains governed by the existing retry/backoff path');
  assert.equal(orchestrator.autoRecoveryBlocked, false);
});

test('supervisor trusts MCP health over a stale owned-process record', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: true,
    nativeAlive: false,
    tunnelRunning: false
  });
  await orchestrator.supervise();
  assert.equal(calls.tunnel, 1);
  assert.equal(calls.restart, 0);
});

test('supervisor does not kill a live MCP process after transient health failures', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: false,
    nativeAlive: true,
    tunnelRunning: true
  });
  const result = await orchestrator.supervise();
  assert.equal(calls.tunnel, 0);
  assert.equal(calls.restart, 0);
  assert.equal(result.recoveryDeferred, true);
  assert.equal(result.recoveryReason, 'mcp_process_alive_health_unavailable');
});

test('supervisor never escalates deterministic MCP health mismatch into a destructive restart', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: false,
    nativeAlive: true,
    tunnelRunning: true,
    mcpHealthFailureKind: 'workspace_mismatch',
    mcpHealthFailureDeterministic: true
  });
  let result = null;
  for (let attempt = 0; attempt < 10; attempt += 1) {
    orchestrator.nextRecoveryAt = 0;
    result = await orchestrator.supervise();
  }
  assert.equal(calls.restart, 0);
  assert.equal(calls.mcp, 0);
  assert.equal(calls.tunnel, 0);
  assert.equal(result.recoveryBlocked, true);
  assert.equal(result.recoveryDeferred, true);
  assert.equal(result.recoveryReason, 'mcp_health_deterministic_mismatch');
  assert.equal(result.failureKind, 'mcp_health_workspace_mismatch');
  assert.equal(result.mcpHealthFailureKind, 'workspace_mismatch');
  assert.equal(result.mcpHealthFailureDeterministic, true);
});

test('supervisor fail-closes before replacement when the recorded owned PID is still alive but MCP health is unavailable', async (t) => {
  const child = spawn(process.execPath, ['-e', 'setInterval(() => {}, 1000)'], {
    windowsHide: true,
    stdio: 'ignore'
  });
  await new Promise((resolve, reject) => {
    child.once('spawn', resolve);
    child.once('error', reject);
  });
  t.after(async () => {
    fs.writeFileSync(runtimeStatePath, JSON.stringify({ manualStop: false }), 'utf8');
    if (isAlive(child.pid)) child.kill();
    if (child.exitCode === null && child.signalCode === null) {
      await new Promise((resolve) => {
        const timer = setTimeout(resolve, 3000);
        child.once('close', () => { clearTimeout(timer); resolve(); });
      });
    }
  });
  fs.writeFileSync(runtimeStatePath, JSON.stringify({ manualStop: false, nativePid: child.pid }), 'utf8');
  assert.equal(isAlive(child.pid), true);
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: false,
    nativeAlive: true,
    tunnelRunning: true
  });
  const result = await orchestrator.supervise();
  assert.equal(result.recoveryDeferred, true);
  assert.equal(result.recoveryReason, 'mcp_process_alive_health_unavailable');
  assert.equal(calls.mcp, 0);
  assert.equal(calls.tunnel, 0);
  assert.equal(calls.restart, 0);
  assert.equal(isAlive(child.pid), true, 'live recorded owner must remain alive at the fail-closed defer boundary');
});

test('supervisor defers recovery when both health checks fail but MCP process remains alive', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: false,
    nativeAlive: true,
    tunnelRunning: false
  });
  const result = await orchestrator.supervise();
  assert.equal(calls.tunnel, 0);
  assert.equal(calls.restart, 0);
  assert.equal(result.recoveryDeferred, true);
});

test('supervisor recovers only Coding MCP after the owned MCP process exits', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: false,
    nativeAlive: false,
    tunnelRunning: true
  });
  await orchestrator.supervise();
  assert.equal(calls.tunnel, 0);
  assert.equal(calls.mcp, 1);
  assert.equal(calls.restart, 0);
});

test('MCP-only recovery refuses an unexpectedly occupied MCP port without touching Tunnel', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-mcp-only-port-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const stateFile = path.join(root, 'runtime-state.json');
  fs.writeFileSync(stateFile, JSON.stringify({ manualStop: false, nativePid: null, tunnelPid: 4242 }), 'utf8');
  const server = http.createServer((_request, response) => response.end('occupied'));
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise((resolve) => server.close(resolve)));
  const port = server.address().port;
  const orchestrator = new RuntimeOrchestrator({
    paths: { stateFile: () => stateFile },
    settings: { load: () => ({ workspace: root, mcpPort: port, tunnelId: 'tunnel-mcp-port-test', proxyMode: 'auto' }) },
    secrets: { get: () => 'token', set() {} },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {}
  });
  orchestrator.activationEpochStore = { current: () => null };
  orchestrator.validate = () => {};
  let nativeStarts = 0;
  let tunnelTouches = 0;
  orchestrator.native = {
    start: async () => { nativeStarts += 1; },
    stop: async () => { throw new Error('native stop must not run before a new MCP was started'); }
  };
  orchestrator.tunnel = {
    start: async () => { tunnelTouches += 1; },
    stop: async () => { tunnelTouches += 1; }
  };
  await assert.rejects(orchestrator.recoverMcpOnly(), { code: 'MCP_PORT_IN_USE' });
  assert.equal(nativeStarts, 0);
  assert.equal(tunnelTouches, 0);
  assert.equal(JSON.parse(fs.readFileSync(stateFile, 'utf8')).tunnelPid, 4242);
});

test('MCP-only soft recovery stops the replacement when disk revision drifts after spawn', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-mcp-soft-revision-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const stateFile = path.join(root, 'runtime-state.json');
  const expectedRevision = 'a'.repeat(64);
  const changedRevision = 'b'.repeat(64);
  const activationEpochId = 'activation-soft-recovery-0001';
  fs.writeFileSync(stateFile, JSON.stringify({ manualStop: false, nativePid: null, tunnelPid: 4242 }), 'utf8');
  const reservation = http.createServer();
  await new Promise((resolve) => reservation.listen(0, '127.0.0.1', resolve));
  const port = reservation.address().port;
  await new Promise((resolve) => reservation.close(resolve));
  const orchestrator = new RuntimeOrchestrator({
    paths: { stateFile: () => stateFile },
    settings: { load: () => ({ workspace: root, mcpPort: port, tunnelId: 'tunnel-mcp-revision-test', proxyMode: 'auto' }) },
    secrets: { get: () => 'token', set() {} },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    activationEpochId
  });
  orchestrator.validate = () => {};
  orchestrator.activationEpochStore = {
    current: () => ({
      activation_epoch_id: activationEpochId,
      // This fixture isolates the post-spawn disk-drift rollback.  A terminal
      // READY/OPEN epoch is intentionally covered by the dedicated soft-
      // replacement admission tests and must be refused before spawn.
      state: 'VERIFYING',
      admission_state: 'CLOSED',
      component_revisions: { coding_mcp: { disk_revision: expectedRevision } },
      verification: { final_census: { running_revision: expectedRevision, disk_revision: expectedRevision } }
    })
  };
  // Production soft recovery is suppressed for an incomplete epoch.  Bypass
  // that unrelated lifecycle gate here so this test can exercise the later
  // revision-drift fence after a replacement has actually spawned.
  orchestrator.assertSoftRecoveryAllowed = () => ({
    activation_epoch_id: activationEpochId,
    epoch_state: 'VERIFYING',
    state: 'UPDATE_INCOMPLETE',
    admission_open: false,
    update_incomplete: false
  });
  let revisionReads = 0;
  orchestrator.revisions = {
    disk: () => ({ revision: ++revisionReads === 1 ? expectedRevision : changedRevision })
  };
  let replacementServer = null;
  let stops = 0;
  orchestrator.native = {
    start: async (_settings, _token, _progress, options) => {
      assert.equal(options.expectedCodeRevision, expectedRevision);
      replacementServer = http.createServer((_request, response) => response.end('ok'));
      await new Promise((resolve) => replacementServer.listen(port, '127.0.0.1', resolve));
      fs.writeFileSync(stateFile, JSON.stringify({
        manualStop: false,
        nativePid: process.pid,
        nativeCodeRevision: expectedRevision,
        tunnelPid: 4242
      }), 'utf8');
      return { reused: false };
    },
    status: async () => true,
    stop: async () => {
      stops += 1;
      if (replacementServer?.listening) await new Promise((resolve) => replacementServer.close(resolve));
      fs.writeFileSync(stateFile, JSON.stringify({ manualStop: false, nativePid: null, tunnelPid: 4242 }), 'utf8');
      return true;
    }
  };
  orchestrator.currentMcpHealth = async () => ({ ready: true, code_revision: expectedRevision });

  await assert.rejects(orchestrator.recoverMcpOnly(), { code: 'REVISION_CHANGED_DURING_RECOVERY' });
  assert.equal(stops, 1);
  assert.equal(revisionReads, 2);
  assert.equal(JSON.parse(fs.readFileSync(stateFile, 'utf8')).tunnelPid, 4242);
  assert.equal(replacementServer?.listening, false);
});

test('supervisor requires three consecutive failures of the same kind', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: false,
    nativeAlive: true,
    tunnelRunning: true
  });
  orchestrator.heartbeatFailureKind = 'tunnel_unavailable';
  const result = await orchestrator.supervise();
  assert.equal(result.failures, 1);
  assert.equal(calls.tunnel, 0);
  assert.equal(calls.restart, 0);
});

test('supervisor replaces only a hung live MCP after repeated deferrals', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: false,
    nativeAlive: true,
    tunnelRunning: false,
    mcpHealthFailureKind: 'timeout',
    mcpHealthFailureDeterministic: false
  });
  const maxDeferred = 6;
  for (let attempt = 1; attempt < maxDeferred; attempt += 1) {
    orchestrator.nextRecoveryAt = 0;
    const result = await orchestrator.supervise();
    assert.equal(result.recoveryDeferred, true);
    assert.equal(calls.restart, 0);
  }
  orchestrator.nextRecoveryAt = 0;
  await orchestrator.supervise();
  assert.equal(calls.restart, 0);
  assert.equal(calls.mcp, 1);
  assert.deepEqual(calls.mcpOptions, [{ replaceLiveOwned: true, reason: 'hung_mcp_soft_recovery' }]);
  assert.equal(calls.tunnel, 0);
  assert.equal(orchestrator.deferredRecoveryCount, 0);
});

test('supervisor resets the deferral counter once the runtime becomes healthy', async () => {
  const { orchestrator, calls } = recoveryHarness({
    fullyReady: false,
    mcpRunning: false,
    nativeAlive: true,
    tunnelRunning: false
  });
  orchestrator.nextRecoveryAt = 0;
  const deferred = await orchestrator.supervise();
  assert.equal(deferred.recoveryDeferred, true);
  assert.equal(orchestrator.deferredRecoveryCount, 1);
  orchestrator.lightweightSnapshot = async () => ({
    fullyReady: true,
    mcpRunning: true,
    nativeAlive: true,
    tunnelRunning: true
  });
  await orchestrator.supervise();
  assert.equal(orchestrator.deferredRecoveryCount, 0);
  assert.equal(calls.restart, 0);
});

test('native and tunnel stop paths require exact process identity before tree termination', () => {
  const fs = require('node:fs');
  const path = require('node:path');
  const root = path.resolve(__dirname, '..');
  for (const relative of ['electron/services/nativeService.js', 'electron/services/tunnelService.js']) {
    const source = fs.readFileSync(path.join(root, relative), 'utf8');
    assert.match(source, /terminateExactProcessTree/);
    assert.match(source, /ProcessStartToken/);
    assert.doesNotMatch(source, /taskkill\.exe/);
  }
});

test('native and tunnel health probes use non-blocking process identity observation by default', () => {
  const native = new NativeService({ info() {} }, runtimePaths, { status() { return {}; } });
  const tunnel = new TunnelService({ info() {} }, runtimePaths);
  assert.equal(native.asyncProcessIdentityObserver, observeProcessIdentityAsync);
  assert.equal(tunnel.asyncProcessIdentityObserver, observeProcessIdentityAsync);
});

function exactStopHarness(ServiceClass, prefix, token, observed) {
  const file = path.join(os.tmpdir(), `webcodex-exact-stop-${prefix}-${process.pid}-${crypto.randomBytes(4).toString('hex')}.json`);
  const fields = prefix === 'native'
    ? {
      nativePid: process.pid,
      nativeProcessStartToken: token,
      nativeConnectorAttestationSecretHash: 'a'.repeat(64)
    }
    : { tunnelPid: process.pid, tunnelProcessStartToken: token };
  fs.writeFileSync(file, JSON.stringify(fields), 'utf8');
  const paths = { stateFile: () => file };
  const terminated = [];
  const options = {
    processIdentityObserver: () => observed,
    exactProcessTerminator: async (identity) => { terminated.push(identity); }
  };
  const service = ServiceClass === NativeService
    ? new ServiceClass({ info() {} }, paths, { status() { return {}; } }, null, options)
    : new ServiceClass({ info() {} }, paths, null, options);
  return { file, fields, service, terminated };
}

for (const [label, ServiceClass, prefix] of [
  ['native', NativeService, 'native'],
  ['tunnel', TunnelService, 'tunnel']
]) {
  test(`${label} stop forwards the exact stored PID and start token`, async (t) => {
    const token = '10000000000000011';
    const harness = exactStopHarness(ServiceClass, prefix, token, { state: 'live', pid: process.pid, process_start_token: token });
    t.after(() => fs.rmSync(harness.file, { force: true }));
    assert.equal(await harness.service.stop(), true);
    assert.deepEqual(harness.terminated, [{ pid: process.pid, process_start_token: token }]);
    const state = JSON.parse(fs.readFileSync(harness.file, 'utf8'));
    assert.equal(state[`${prefix}Pid`], null);
    assert.equal(state[`${prefix}ProcessStartToken`], null);
    if (prefix === 'native') assert.equal(state.nativeConnectorAttestationSecretHash, '');
  });

  test(`${label} stop clears a retired receipt without terminating its recycled PID`, async (t) => {
    const token = '10000000000000012';
    const harness = exactStopHarness(ServiceClass, prefix, token, { state: 'live', pid: process.pid, process_start_token: '10000000000000013' });
    t.after(() => fs.rmSync(harness.file, { force: true }));
    assert.equal(await harness.service.stop(), false);
    assert.deepEqual(harness.terminated, []);
    const state = JSON.parse(fs.readFileSync(harness.file, 'utf8'));
    assert.equal(state[`${prefix}Pid`], null);
    assert.equal(state[`${prefix}ProcessStartToken`], null);
    assert.doesNotThrow(() => process.kill(process.pid, 0));
  });

  test(`${label} stop rejects unavailable or missing identity without clearing state`, async (t) => {
    const token = '10000000000000014';
    const unavailable = exactStopHarness(ServiceClass, prefix, token, { state: 'unavailable', pid: process.pid, code: 'PROCESS_IDENTITY_UNVERIFIED' });
    t.after(() => fs.rmSync(unavailable.file, { force: true }));
    await assert.rejects(unavailable.service.stop(), { code: `${label.toUpperCase()}_PROCESS_IDENTITY_UNVERIFIED` });
    assert.deepEqual(unavailable.terminated, []);
    assert.deepEqual(JSON.parse(fs.readFileSync(unavailable.file, 'utf8')), unavailable.fields);

    const missing = exactStopHarness(ServiceClass, prefix, null, { state: 'live', pid: process.pid, process_start_token: token });
    t.after(() => fs.rmSync(missing.file, { force: true }));
    await assert.rejects(missing.service.stop(), { code: `${label.toUpperCase()}_PROCESS_IDENTITY_UNVERIFIED` });
    assert.deepEqual(missing.terminated, []);
    assert.deepEqual(JSON.parse(fs.readFileSync(missing.file, 'utf8')), missing.fields);
  });
}

test('authorized child exact stale maintenance preserves supervisor owner and passes target workspace to full-clean', async () => {
  const workspace = 'C:\\work\\one';
  const maintenanceWorkspace = 'C:\\work\\two';
  const ticketId = 'restart-authorized-child-stale-0001';
  const reason = `exact_stale_runs:${'a'.repeat(32)}`;
  const restartCalls = [];
  const orchestrator = new RuntimeOrchestrator({
    settings: { load: () => ({ workspace, authorizedRoots: [maintenanceWorkspace], autoStartServices: true }) },
    secrets: { get: () => '' },
    environment: {},
    log: { info() {}, warn() {}, error() {} },
    emitProgress() {},
    fullCleanActivation: {
      restart: async (options) => {
        restartCalls.push(options);
        return {
          full_clean_activation: true,
          activation_epoch_id: 'epoch-authorized-child-stale-0001',
          state: 'READY',
          admission_open: true,
          fully_ready: true
        };
      }
    }
  });
  orchestrator.lightweightSnapshot = async () => ({ fullyReady: true, mcpRunning: true, nativeAlive: true, tunnelRunning: true });
  orchestrator.currentMcpHealth = async () => ({ process_instance_id: 'process-one', instance_id: 'server-one', tool_contract: { sha256: 'e'.repeat(64) } });
  orchestrator.revisions.disk = () => ({ revision: 'a'.repeat(64) });
  orchestrator.activationEpochStore = {
    load: () => ({
      current: { activation_epoch_id: 'epoch-authorized-child-stale-0001', operation_id: ticketId, state: 'READY' },
      history: []
    })
  };
  const now = Date.now();
  fs.writeFileSync(supervisorRequestPath, JSON.stringify({
    version: 1,
    action: 'restart',
    ticket_id: ticketId,
    operation_id: ticketId,
    activation_mode: 'full_clean_activation',
    full_clean_required: true,
    process_instance_id: 'process-one',
    server_instance_id: 'server-one',
    tool_contract_sha256: 'e'.repeat(64),
    workspace,
    target_workspace: maintenanceWorkspace,
    allow_acceptance_pending: true,
    reason,
    requested_at_unix_ms: now - 1000,
    not_before_unix_ms: now - 1,
    expires_at_unix_ms: now + 30000
  }), 'utf8');

  const result = await orchestrator.supervise();
  assert.equal(restartCalls.length, 1);
  assert.equal(restartCalls[0].refresh, true);
  assert.equal(restartCalls[0].mode, 'full_clean_refresh');
  assert.equal(restartCalls[0].sourceCheckpoint, null);
  assert.equal(restartCalls[0].maintenanceWorkspace, maintenanceWorkspace);
  assert.equal(restartCalls[0].allowAcceptancePending, true);
  assert.equal(result.supervisorRequest.status, 'completed');
});
