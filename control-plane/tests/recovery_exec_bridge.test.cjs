'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
  normalisedResult,
  runDevelopmentExecBridge
} = require('../control_plane/recovery_exec_bridge.cjs');
const {
  digest,
  normaliseExecResult
} = require('../../electron/services/controlPlaneExecBridge');

const request = {
  server_origin: 'https://control.example.test',
  owner_id: 'owner-control-plane-0001',
  device_id: 'device-control-plane-0001',
  endpoint_id: 'endpoint-control-plane-0001',
  workspace_id: 'workspace-control-plane-0001',
  workspace_generation: 'generation-control-plane-0001',
  context_id: 'context-control-plane-0001',
  binding_id: 'binding-control-plane-0001',
  action_id: 'action-control-plane-0001',
  attempt_id: 'attempt-control-plane-0001',
  task_id: `task_${'a'.repeat(32)}`,
  writer_lease_generation: 1,
  tool_name: 'exec_command',
  operation: 'exec_run',
  argv: ['python', '-m', 'pytest', '-q'],
  cwd: '',
  timeout_ms: 30_000,
  max_output_bytes: 16_384,
  expires_at_ms: Date.now() + 30_000,
  facade_contract: {
    schema_version: 14,
    profile: 'control-plane-oauth-bounded-exec-v1',
    sha256: 'f'.repeat(64)
  },
  policy_sha256: 'a'.repeat(64)
};

function candidate() {
  const output = {
    status: 'exited',
    exit_code: 0,
    stdout: 'bridge ok\n',
    stderr: '',
    truncated: false,
    timed_out: false,
    command_id: 'command-recovery-exec-0001',
    job_id: 'job-recovery-exec-0001',
    run_id: '',
    wave_id: '',
    output_refs: null
  };
  return {
    schema_version: 1,
    operation_kind: 'control_plane_exec',
    local_handle: `cp_exec_${'a'.repeat(48)}`,
    action_id: request.action_id,
    attempt_id: request.attempt_id,
    task_id: request.task_id,
    writer_lease_generation: request.writer_lease_generation,
    policy_sha256: request.policy_sha256,
    actor: { client_id: 'electron-control-plane-exec-bridge', client_type: 'electron' },
    facade_contract: { ...request.facade_contract },
    runtime_identity: {
      activation_epoch_id: 'activation-recovery-exec-0001',
      process_instance_id: 'process-recovery-exec-0001',
      server_instance_id: 'server-recovery-exec-0001',
      tool_contract_sha256: 'd'.repeat(64)
    },
    ...output,
    response_sha256: digest(output)
  };
}

test('exec bridge hides Recovery descriptor and returns allowlisted receipt', async () => {
  const descriptor = {
    runtime_mode: 'development',
    installation_id: 'i'.repeat(32),
    token: 'descriptor-token'
  };
  const paths = {
    appRoot: () => '/project',
    runtimeIdentity: () => ({ installation_id: descriptor.installation_id, mode: 'development' })
  };
  const calls = [];
  class FakeClient {
    async call(action, args, options) {
      calls.push({ action, args, options });
      return candidate();
    }
  }
  const result = await runDevelopmentExecBridge(request, {
    dependencies: {
      lifecycle: { createDevelopmentPaths: () => paths },
      RecoveryIpcClient: FakeClient,
      loadRecoveryDescriptor: () => descriptor,
      descriptorMatchesInstallation: (observed, expected) => observed.installation_id === expected.installation_id,
      descriptorRequestOptions: (observed) => ({ token: observed.token }),
      execBridge: { normaliseExecResult },
    }
  });
  assert.equal(calls.length, 1);
  assert.equal(calls[0].action, 'runtime.control_plane_exec');
  assert.deepEqual(calls[0].args, [request]);
  assert.equal(calls[0].options.token, descriptor.token);
  assert.equal(result.command_id, 'command-recovery-exec-0001');
  assert.equal(result.job_id, 'job-recovery-exec-0001');
  assert.equal(Object.hasOwn(result, 'token'), false);
});

test('exec bridge normalizer rejects a changed result digest', () => {
  const value = candidate();
  value.stdout = 'changed';
  assert.throws(
    () => normalisedResult({ runtime_mode: 'development', installation_id: 'i'.repeat(32) }, value, request, { normaliseExecResult }),
    { code: 'CONTROL_PLANE_EXEC_RESULT_DIGEST_INVALID' }
  );
});

test('exec bridge fails closed before IPC when the Recovery installation identity changes', async () => {
  const expectedInstallation = 'i'.repeat(32);
  const calls = [];
  const paths = {
    appRoot: () => '/project',
    runtimeIdentity: () => ({ installation_id: expectedInstallation, mode: 'development' })
  };
  class UnexpectedClient {
    async call(...args) {
      calls.push(args);
      return candidate();
    }
  }
  await assert.rejects(
    runDevelopmentExecBridge(request, {
      dependencies: {
        lifecycle: { createDevelopmentPaths: () => paths },
        RecoveryIpcClient: UnexpectedClient,
        loadRecoveryDescriptor: () => ({ runtime_mode: 'development', installation_id: 'x'.repeat(32), token: 'descriptor-token' }),
        descriptorMatchesInstallation: () => false,
        descriptorRequestOptions: () => ({ token: 'descriptor-token' }),
        execBridge: { normaliseExecResult }
      }
    }),
    { code: 'RECOVERY_HOST_INSTALLATION_MISMATCH' }
  );
  assert.equal(calls.length, 0);
});

test('exec bridge preserves a typed Recovery IPC failure without exposing its descriptor', async () => {
  const descriptor = {
    runtime_mode: 'development',
    installation_id: 'i'.repeat(32),
    token: 'descriptor-token'
  };
  const paths = {
    appRoot: () => '/project',
    runtimeIdentity: () => ({ installation_id: descriptor.installation_id, mode: 'development' })
  };
  class FailingClient {
    async call() {
      throw Object.assign(new Error('transport failed'), { code: 'RECOVERY_IPC_TIMEOUT' });
    }
  }
  await assert.rejects(
    runDevelopmentExecBridge(request, {
      dependencies: {
        lifecycle: { createDevelopmentPaths: () => paths },
        RecoveryIpcClient: FailingClient,
        loadRecoveryDescriptor: () => descriptor,
        descriptorMatchesInstallation: (observed, expected) => observed.installation_id === expected.installation_id,
        descriptorRequestOptions: (observed) => ({ token: observed.token }),
        execBridge: { normaliseExecResult }
      }
    }),
    { code: 'RECOVERY_IPC_TIMEOUT' }
  );
});
