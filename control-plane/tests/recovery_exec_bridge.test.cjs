'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
  normalisedResult,
  serializeExecBridgeError,
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
  assert.equal(calls[0].options.timeout, 330_000);
  assert.equal(result.command_id, 'command-recovery-exec-0001');
  assert.equal(result.job_id, 'job-recovery-exec-0001');
  assert.equal(Object.hasOwn(result, 'token'), false);
});

test('exec bridge preserves the configured short IPC budget for poll and stop', async () => {
  const descriptor = { runtime_mode: 'development', installation_id: 'i'.repeat(32) };
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
  for (const operation of ['exec_poll', 'exec_stop']) {
    await runDevelopmentExecBridge({ ...request, operation }, {
      dependencies: {
        lifecycle: { createDevelopmentPaths: () => paths },
        RecoveryIpcClient: FakeClient,
        loadRecoveryDescriptor: () => descriptor,
        descriptorMatchesInstallation: () => true,
        descriptorRequestOptions: () => ({ expectedOwnerPid: 123, timeout: 17_000 }),
        execBridge: { normaliseExecResult }
      }
    });
  }
  assert.equal(calls.length, 2);
  for (const call of calls) {
    assert.deepEqual(call.options, { expectedOwnerPid: 123, timeout: 17_000 });
  }
});

test('exec bridge normalizer rejects a changed result digest', () => {
  const value = candidate();
  value.stdout = 'changed';
  assert.throws(
    () => normalisedResult({ runtime_mode: 'development', installation_id: 'i'.repeat(32) }, value, request, { normaliseExecResult }),
    { code: 'CONTROL_PLANE_EXEC_RESULT_DIGEST_INVALID' }
  );
});

test('exec bridge preserves only verified backend metadata through the subprocess projection', () => {
  const value = candidate();
  const output = Object.fromEntries(['status', 'exit_code', 'stdout', 'stderr', 'truncated', 'timed_out',
    'command_id', 'job_id', 'run_id', 'wave_id', 'output_refs'].map((key) => [key, value[key]]));
  const metadata = { execution_backend: 'native', isolation_level: 'process_container', policy_decision: 'native_safe_command' };
  Object.assign(value, metadata, { response_sha256: digest({ ...output, ...metadata }) });
  const result = normalisedResult({ runtime_mode: 'development' }, value, request, { normaliseExecResult });
  assert.equal(result.execution_backend, 'native');
  assert.equal(result.isolation_level, 'process_container');
  assert.equal(result.policy_decision, 'native_safe_command');
  assert.throws(() => normalisedResult({}, { ...value, policy_decision: 'native_explicit_approval' }, request,
    { normaliseExecResult }), { code: 'CONTROL_PLANE_EXEC_RESULT_DIGEST_INVALID' });
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

function failingExecOptions(error) {
  const descriptor = { runtime_mode: 'development', installation_id: 'i'.repeat(32), token: 'descriptor-private' };
  const paths = { appRoot: () => '/project', runtimeIdentity: () => ({ installation_id: descriptor.installation_id, mode: 'development' }) };
  class FailingClient { async call() { throw error; } }
  return { dependencies: {
    lifecycle: { createDevelopmentPaths: () => paths }, RecoveryIpcClient: FailingClient,
    loadRecoveryDescriptor: () => descriptor, descriptorMatchesInstallation: () => true,
    descriptorRequestOptions: () => ({ expectedOwnerPid: 123 }), execBridge: { normaliseExecResult }
  } };
}

test('exec bridge correlates authenticated native spawn failure without forwarding private fields', async () => {
  const details = {
    native_error_code: 'SANDBOX_STATE_PHASE_FAILED', phase: 'start', backend_error_code: 'backend_error',
    command_id: '_aJumSgZyYU90Yj_Mt7qu-Gp', job_id: 'a'.repeat(32), job_lifecycle: 'spawn_failed',
    root_pid: 0, execution_started: false, job_finished_at: '2026-10-11T10:27:08.489123Z'
  };
  const error = Object.assign(new Error('private native message'), {
    code: 'CONTROL_PLANE_EXEC_MCP_REJECTED', recoveryResponseReceived: true,
    action_id: 'wrong-action', attempt_id: 'wrong-attempt', task_id: 'wrong-task', writer_lease_generation: 99,
    details: { ...details, token: 'descriptor-private', stdout: 'private output', message: 'private cause' }
  });
  await assert.rejects(runDevelopmentExecBridge(request, failingExecOptions(error)), (received) => {
    assert.deepEqual(serializeExecBridgeError(received), {
      code: 'CONTROL_PLANE_EXEC_MCP_REJECTED', details, recovery_response_received: true,
      action_id: request.action_id, attempt_id: request.attempt_id, task_id: request.task_id,
      writer_lease_generation: request.writer_lease_generation
    });
    assert.equal(JSON.stringify(serializeExecBridgeError(received)).includes('private'), false);
    return true;
  });
});

test('exec bridge does not grant diagnostic provenance to transport loss or unmatched invocations', async () => {
  for (const recoveryResponseReceived of [false, undefined]) {
    const error = Object.assign(new Error('private error'), {
      code: 'CONTROL_PLANE_EXEC_MCP_REJECTED', recoveryResponseReceived,
      details: { native_error_code: 'SANDBOX_STATE_PHASE_FAILED', root_pid: 0 }
    });
    await assert.rejects(runDevelopmentExecBridge(request, failingExecOptions(error)), (received) => {
      assert.deepEqual(serializeExecBridgeError(received), { code: 'CONTROL_PLANE_EXEC_MCP_REJECTED' });
      return true;
    });
  }
  const error = Object.assign(new Error('private error'), {
    code: 'CONTROL_PLANE_EXEC_MCP_REJECTED', recoveryResponseReceived: true,
    details: { native_error_code: 'SANDBOX_STATE_PHASE_FAILED' }
  });
  await assert.rejects(runDevelopmentExecBridge({ ...request, action_id: 'private\ninvalid' }, failingExecOptions(error)), (received) => {
    assert.deepEqual(serializeExecBridgeError(received), { code: 'CONTROL_PLANE_EXEC_MCP_REJECTED' });
    return true;
  });
  assert.deepEqual(serializeExecBridgeError({ code: 'RECOVERY_IPC_TIMEOUT', recovery_response_received: true,
    ...request, details: { native_error_code: 'SANDBOX_STATE_PHASE_FAILED' }, message: 'private' }), { code: 'RECOVERY_IPC_TIMEOUT' });
});

test('exec bridge error serializer rejects malformed diagnostics without inventing completion facts', () => {
  const error = {
    code: 'CONTROL_PLANE_EXEC_MCP_REJECTED', ...request, recovery_response_received: true,
    details: { native_error_code: 'SANDBOX_STATE_PHASE_FAILED', phase: 'shell', backend_error_code: 'secret\nvalue',
      command_id: {}, job_id: 'x'.repeat(161), job_lifecycle: 'complete', root_pid: '0', execution_started: 'false',
      job_finished_at: '2026-02-31T10:27:08Z', token: 'private', stdout: 'private' }
  };
  assert.deepEqual(serializeExecBridgeError(error).details, { native_error_code: 'SANDBOX_STATE_PHASE_FAILED' });
  assert.deepEqual(serializeExecBridgeError({ code: 'private\ncode', message: 'private' }), { code: 'CONTROL_PLANE_EXEC_FAILED' });
});
