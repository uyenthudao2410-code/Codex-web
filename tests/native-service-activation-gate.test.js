const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const os = require('node:os');

const {
  ACTIVATION_GATE_CLOSED,
  ACTIVATION_GATE_OPEN,
  buildNativeMcpEnv,
  normalizeActivationGate
} = require('../electron/services/nativeService');

function launchContract() {
  const root = path.join(os.tmpdir(), 'webcodex-native-gate-test');
  return {
    resourcesRoot: path.join(root, 'resources'),
    moduleRoot: path.join(root, 'module'),
    vendoredPython: path.join(root, 'module', 'python_vendor')
  };
}

function buildEnv(overrides = {}) {
  return buildNativeMcpEnv({
    sourceEnv: { PATH: 'safe-base-path' },
    launch: launchContract(),
    settings: { authorizedRoots: [], progressReportSeconds: 90 },
    token: 'test-mcp-bearer',
    diskRevision: 'r'.repeat(64),
    supervisorRequestFile: path.join(os.tmpdir(), 'webcodex-native-gate-supervisor.json'),
    ...overrides
  });
}

test('epoch-bound NativeService launch defaults to a closed admission gate', () => {
  const activationEpochId = 'activation-native-gate-0001';
  const env = buildEnv({ activationEpochId });

  assert.equal(env.CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID, activationEpochId);
  assert.equal(env.CODING_TOOLS_MCP_ACTIVATION_GATE, ACTIVATION_GATE_CLOSED);
});

test('epoch-bound NativeService launch rejects an explicit open or unknown gate', () => {
  const activationEpochId = 'activation-native-gate-0002';

  assert.throws(
    () => buildEnv({ activationEpochId, activationGate: ACTIVATION_GATE_OPEN }),
    { code: 'ACTIVATION_GATE_INVALID' }
  );
  assert.throws(
    () => buildEnv({ activationEpochId, activationGate: 'unexpected-value' }),
    { code: 'ACTIVATION_GATE_INVALID' }
  );
});

test('legacy launch without an activation epoch keeps implicit-open compatibility', () => {
  const env = buildEnv();
  assert.equal(env.CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID, undefined);
  assert.equal(env.CODING_TOOLS_MCP_ACTIVATION_GATE, undefined);
  assert.equal(normalizeActivationGate('', ACTIVATION_GATE_OPEN), ACTIVATION_GATE_OPEN);
});

test('closed gate input is normalized consistently for an epoch-bound launch', () => {
  assert.equal(
    normalizeActivationGate('activation-native-gate-0003', '  CLOSED '),
    ACTIVATION_GATE_CLOSED
  );
  const env = buildEnv({
    activationEpochId: 'activation-native-gate-0003',
    activationGate: '  CLOSED '
  });
  assert.equal(env.CODING_TOOLS_MCP_ACTIVATION_GATE, ACTIVATION_GATE_CLOSED);
});
