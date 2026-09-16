'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {
  normalizedObservation,
  normalizedRuntimeStatus,
  observeRuntime,
  observeDevelopmentRuntime
} = require('../control_plane/recovery_identity_observer.cjs');
const { buildMcpIdentityObservation } = require('../../electron/services/recoveryHost');
const { RPC_ACTIONS } = require('../../electron/services/recoveryIpc');

const descriptor = Object.freeze({
  installation_id: 'a'.repeat(64),
  runtime_mode: 'development',
  instance_id: 'recovery-host-instance-0001',
  token: 'must-not-be-returned',
  owner_process_start_token: 'must-not-be-returned'
});

test('read-only identity observation binds the exact Recovery Host and omits descriptor secrets', async () => {
  const calls = [];
  const observed = await observeDevelopmentRuntime({
    appRoot: process.cwd(),
    dependencies: {
      createDevelopmentPaths: () => ({ runtimeIdentity: () => ({ mode: 'development', installation_id: 'a'.repeat(64) }) }),
      loadRecoveryDescriptor: () => descriptor,
      descriptorMatchesInstallation: () => true,
      descriptorRequestOptions: (value) => ({ expectedInstanceId: value.instance_id }),
      clientFactory: () => ({
        call: async (...args) => {
          calls.push(args);
          return buildMcpIdentityObservation({
            recoveryHostInstanceId: descriptor.instance_id,
            health: {
              ready: true,
              process_instance_id: 'mcp-process-0001',
              instance_id: 'mcp-server-0001',
              activation_epoch_id: 'activation-epoch-0001',
              tool_contract: { sha256: 'b'.repeat(64) }
            },
            activationEpoch: {
              activation_epoch_id: 'activation-epoch-0001',
              admission_open: true,
              update_incomplete: false
            },
            observedAt: '2026-09-15T03:00:00.000Z'
          });
        }
      })
    }
  });
  assert.deepEqual(calls, [[
    'runtime.identity_observation',
    [],
    { expectedInstanceId: descriptor.instance_id }
  ]]);
  assert.equal(observed.observation_kind, 'mcp_identity_read_only');
  assert.equal(observed.identity_current, true);
  assert.equal(observed.mcp_process_instance_id, 'mcp-process-0001');
  assert.equal(observed.activation_epoch_id, 'activation-epoch-0001');
  assert.equal(JSON.stringify(observed).includes('must-not-be-returned'), false);
  assert.equal(RPC_ACTIONS.includes('runtime.identity_observation'), true);
});

test('read-only identity observation rejects an installation mismatch and does not call IPC', async () => {
  let called = false;
  await assert.rejects(
    observeDevelopmentRuntime({
      appRoot: process.cwd(),
      dependencies: {
        createDevelopmentPaths: () => ({ runtimeIdentity: () => ({ mode: 'development', installation_id: 'a'.repeat(64) }) }),
        loadRecoveryDescriptor: () => descriptor,
        descriptorMatchesInstallation: () => false,
        descriptorRequestOptions: () => ({}),
        clientFactory: () => ({ call: async () => { called = true; } })
      }
    }),
    { code: 'RECOVERY_HOST_INSTALLATION_MISMATCH' }
  );
  assert.equal(called, false);
});

test('identity projection refuses a mismatched activation epoch and strips invalid contract fingerprints', () => {
  const observation = buildMcpIdentityObservation({
    recoveryHostInstanceId: descriptor.instance_id,
    health: {
      ready: true,
      process_instance_id: 'mcp-process-0001',
      instance_id: 'mcp-server-0001',
      activation_epoch_id: 'old-epoch',
      tool_contract: { sha256: 'invalid' }
    },
    activationEpoch: {
      activation_epoch_id: 'new-epoch',
      admission_open: true,
      update_incomplete: false
    }
  });
  assert.equal(observation.identity_current, false);
  assert.equal(observation.tool_contract_sha256, null);
  assert.equal(normalizedObservation(descriptor, observation).identity_current, false);
});

test('packaged runtime status is ready only with exact Recovery Host and current local gates', () => {
  const packaged = {
    ...descriptor,
    runtime_mode: 'packaged',
    owner_pid: 4242,
    owner_process_start_token: '1234567890123'
  };
  const current = normalizedRuntimeStatus(packaged, {
    pid: 4242,
    instance_id: packaged.instance_id,
    process_start_token: packaged.owner_process_start_token,
    state: 'healthy',
    full_clean_activation: { available: true },
    activation_epoch: { admission_open: true, update_incomplete: false },
    runtime: {
      fully_ready: true,
      update_incomplete: false,
      connector_ready: true,
      connector_ack_sha_matches: true
    }
  });
  assert.equal(current.strict_ready, true);
  assert.equal(current.runtime_mode, 'packaged');
  assert.equal(current.observation_kind, 'recovery_runtime_read_only');
  const staleOwner = normalizedRuntimeStatus(packaged, {
    pid: 4243,
    instance_id: packaged.instance_id,
    process_start_token: packaged.owner_process_start_token,
    state: 'healthy',
    full_clean_activation: { available: true },
    activation_epoch: { admission_open: true, update_incomplete: false },
    runtime: {
      fully_ready: true,
      update_incomplete: false,
      connector_ready: true,
      connector_ack_sha_matches: true
    }
  });
  assert.equal(staleOwner.strict_ready, false);
  assert.equal(staleOwner.error_code, 'PACKAGED_RUNTIME_UNREADY');
});

test('identity observer uses the packaged installation identity rather than a development checkout', async (t) => {
  const installRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-packaged-observer-'));
  t.after(() => fs.rmSync(installRoot, { recursive: true, force: true }));
  const adapterDirectory = path.join(installRoot, 'resources', 'resources', 'control-plane');
  const appRoot = path.join(installRoot, 'resources', 'app.asar');
  const appData = path.join(installRoot, 'appdata');
  const executablePath = path.join(installRoot, 'Coding Tools MCP.exe');
  fs.mkdirSync(adapterDirectory, { recursive: true });
  fs.mkdirSync(appRoot, { recursive: true });
  fs.mkdirSync(appData, { recursive: true });
  fs.writeFileSync(executablePath, 'fixture');
  const packagedDescriptor = {
    ...descriptor,
    runtime_mode: 'packaged',
    owner_pid: 8888,
    owner_process_start_token: '1234567890123'
  };
  const paths = { runtimeIdentity: () => ({ mode: 'packaged', installation_id: 'a'.repeat(64) }) };
  const observed = await observeRuntime({
    runtimeMode: 'packaged',
    adapterDirectory,
    dependencies: {
      appData,
      executablePath,
      createRuntimePaths: () => paths,
      RecoveryIpcClient: class RecoveryIpcClient {},
      loadRecoveryDescriptor: () => packagedDescriptor,
      descriptorMatchesInstallation: () => true,
      descriptorRequestOptions: (value) => ({ expectedInstanceId: value.instance_id }),
      clientFactory: () => ({
        call: async () => ({
          observation_schema_version: 1,
          observation_kind: 'mcp_identity_read_only',
          recovery_host_instance_id: packagedDescriptor.instance_id,
          mcp_process_instance_id: 'mcp-process-packaged-0001',
          mcp_server_instance_id: 'mcp-server-packaged-0001',
          activation_epoch_id: 'activation-packaged-0001',
          current_activation_epoch_id: 'activation-packaged-0001',
          tool_contract_sha256: 'c'.repeat(64),
          mcp_ready: true,
          identity_current: true
        })
      })
    }
  });
  assert.equal(observed.runtime_mode, 'packaged');
  assert.equal(observed.installation_id, packagedDescriptor.installation_id);
  assert.equal(observed.mcp_process_instance_id, 'mcp-process-packaged-0001');
});
