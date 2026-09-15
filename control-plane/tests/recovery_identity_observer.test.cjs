'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {
  normalizedObservation,
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
