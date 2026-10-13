'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { EventEmitter } = require('node:events');
const childProcess = require('node:child_process');

// NativeService captures its launch dependencies at module-load time.  Keep
// this behavioral regression isolated to this test worker by substituting a
// deterministic Python probe and detached child before requiring the service.
// The production child_process/environmentService modules are restored
// immediately after the require, so no other test worker or application code
// observes the test doubles.
const environmentService = require('../electron/services/environmentService');
const originalPythonStatus = environmentService.pythonStatus;
const originalSpawn = childProcess.spawn;
const spawnCalls = [];
environmentService.pythonStatus = async () => ({
  installed: true,
  version: 'Python 3.11.7',
  command: 'fake-python',
  launchCommand: 'fake-python',
  prefixArgs: []
});
childProcess.spawn = (command, args, options) => {
  const child = new EventEmitter();
  child.pid = 43000 + spawnCalls.length;
  child.unref = () => {};
  spawnCalls.push({ command, args, options });
  queueMicrotask(() => child.emit('spawn'));
  return child;
};
const {
  NativeService,
  runtimeFingerprint,
  connectorAttestationSecretHash
} = require('../electron/services/nativeService');
childProcess.spawn = originalSpawn;
environmentService.pythonStatus = originalPythonStatus;

const OLD_PROCESS_TOKEN = '10000000000000001';
const NEW_PROCESS_TOKEN = '10000000000000002';

function fixture(t, initialSecret) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-native-attestation-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const appRoot = path.join(root, 'app');
  const resourcesRoot = path.join(appRoot, 'resources');
  const moduleRoot = path.join(resourcesRoot, 'coding-tools-mcp');
  fs.mkdirSync(path.join(moduleRoot, 'coding_tools_mcp'), { recursive: true });
  fs.mkdirSync(path.join(moduleRoot, 'python_vendor'), { recursive: true });
  fs.writeFileSync(path.join(moduleRoot, 'coding_tools_mcp', '__init__.py'), '', 'utf8');

  const settings = {
    workspace: root,
    authorizedRoots: [],
    mcpPort: 0,
    permissionMode: 'safe',
    progressReportSeconds: 90
  };
  const stateFile = path.join(root, 'runtime-state.json');
  fs.writeFileSync(stateFile, JSON.stringify({
    nativePid: process.pid,
    nativeProcessStartToken: OLD_PROCESS_TOKEN,
    nativeFingerprint: runtimeFingerprint(settings),
    nativeRuntimeMode: 'development',
    nativeModuleRoot: moduleRoot,
    nativeActivationEpochId: 'activation-native-attestation-0001',
    nativeActivationExpiresAtUnixMs: null,
    ...(initialSecret === undefined
      ? {}
      : { nativeConnectorAttestationSecretHash: connectorAttestationSecretHash(initialSecret) })
  }), 'utf8');

  const paths = {
    stateFile: () => stateFile,
    appRoot: () => appRoot,
    resourcesRoot: () => resourcesRoot,
    runtimeMode: () => 'development',
    mcpLogFile: () => path.join(root, 'mcp.log'),
    supervisorRequestFile: () => path.join(root, 'supervisor.json')
  };
  return { root, settings, stateFile, paths, moduleRoot };
}

function revisions() {
  return { disk: () => ({ revision: 'r'.repeat(64) }) };
}

function observer(pid) {
  return {
    state: 'live',
    pid,
    process_start_token: pid === process.pid ? OLD_PROCESS_TOKEN : NEW_PROCESS_TOKEN
  };
}

test('NativeService reuses only when a requested attestation secret matches the launch digest', async (t) => {
  spawnCalls.length = 0;
  const secret = 'native-attestation-reuse-secret';
  const harness = fixture(t, secret);
  const terminated = [];
  const native = new NativeService(
    { info() {}, warn() {}, error() {} },
    harness.paths,
    revisions(),
    null,
    {
      processIdentityObserver: observer,
      exactProcessTerminator: async (identity) => { terminated.push(identity); }
    }
  );

  const result = await native.start(harness.settings, 'auth-token', () => {}, {
    activationEpochId: 'activation-native-attestation-0001',
    connectorAttestationSecret: secret
  });

  assert.equal(result.reused, true);
  assert.deepEqual(terminated, []);
  assert.equal(spawnCalls.length, 0);
});

test('NativeService refuses a rotated or unknown launch secret and takes exact replacement path', async (t) => {
  spawnCalls.length = 0;
  const oldSecret = 'native-attestation-old-secret';
  const rotatedSecret = 'native-attestation-rotated-secret';
  const harness = fixture(t, oldSecret);
  const terminated = [];
  const native = new NativeService(
    { info() {}, warn() {}, error() {} },
    harness.paths,
    revisions(),
    null,
    {
      processIdentityObserver: observer,
      exactProcessTerminator: async (identity) => { terminated.push(identity); }
    }
  );

  const result = await native.start(harness.settings, 'auth-token', () => {}, {
    activationEpochId: 'activation-native-attestation-0001',
    connectorAttestationSecret: rotatedSecret
  });
  const state = JSON.parse(fs.readFileSync(harness.stateFile, 'utf8'));

  assert.equal(result.reused, false);
  assert.deepEqual(terminated, [{ pid: process.pid, process_start_token: OLD_PROCESS_TOKEN }]);
  assert.equal(spawnCalls.length, 1);
  assert.equal(spawnCalls[0].args[0], '-B', 'the owned Python runtime must keep packaged resources free of bytecode caches');
  assert.equal(state.nativeConnectorAttestationSecretHash, connectorAttestationSecretHash(rotatedSecret));
  assert.equal(JSON.stringify(state).includes(oldSecret), false);
  assert.equal(JSON.stringify(state).includes(rotatedSecret), false);
  assert.equal(spawnCalls[0].options.env.CODING_TOOLS_MCP_CONNECTOR_ATTESTATION_SECRET, rotatedSecret);
  assert.equal(
    spawnCalls[0].options.env.CODING_TOOLS_MCP_ACTIVATION_GATE,
    'closed',
    'an epoch-bound NativeService replacement must never inherit the Python runtime open default'
  );

  // A legacy live receipt without a digest is also unknown and must not be
  // adopted under a newly supplied capability.
  const legacy = fixture(t, undefined);
  const legacyTerminated = [];
  const legacyNative = new NativeService(
    { info() {}, warn() {}, error() {} },
    legacy.paths,
    revisions(),
    null,
    {
      processIdentityObserver: observer,
      exactProcessTerminator: async (identity) => { legacyTerminated.push(identity); }
    }
  );
  await legacyNative.start(legacy.settings, 'auth-token', () => {}, {
    activationEpochId: 'activation-native-attestation-0001',
    connectorAttestationSecret: rotatedSecret
  });
  assert.deepEqual(legacyTerminated, [{ pid: process.pid, process_start_token: OLD_PROCESS_TOKEN }]);
});
