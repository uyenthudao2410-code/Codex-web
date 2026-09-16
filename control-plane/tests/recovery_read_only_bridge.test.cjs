'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {
  runReadOnlyBridge,
  runDevelopmentReadOnlyBridge,
  normalisedResult
} = require('../control_plane/recovery_read_only_bridge.cjs');
const { RPC_ACTIONS } = require('../../electron/services/recoveryIpc');

const descriptor = Object.freeze({
  installation_id: 'a'.repeat(64),
  runtime_mode: 'development',
  instance_id: 'recovery-host-instance-0001',
  token: 'must-not-be-returned',
  owner_process_start_token: 'must-not-be-returned'
});

const request = Object.freeze({
  server_origin: 'https://control.example.test',
  owner_id: 'owner-0001',
  device_id: 'device-0001',
  endpoint_id: 'endpoint-0001',
  workspace_id: 'workspace-0001',
  workspace_generation: 'generation-0001',
  context_id: 'context-0001',
  binding_id: 'binding-0001',
  action_id: 'action-0001',
  attempt_id: 'attempt-0001',
  tool_name: 'workspace_context',
  arguments: { detail: 'compact', max_entries: 1 },
  expires_at_ms: Date.now() + 60_000,
  facade_contract: {
    schema_version: 3,
    profile: 'control-plane-read-only-queue-v2',
    sha256: 'f'.repeat(64)
  }
});

function safeResult() {
  return {
    schema_version: 1,
    operation_kind: 'control_plane_read_only_workspace_context',
    action_id: request.action_id,
    attempt_id: request.attempt_id,
    local_handle: `cp_ro_${'b'.repeat(48)}`,
    workspace_accessed: true,
    policy_sha256: 'c'.repeat(64),
    actor: { client_id: 'electron-control-plane-bridge', client_type: 'electron' },
    runtime_identity: {
      activation_epoch_id: 'activation-epoch-0001',
      process_instance_id: 'mcp-process-0001',
      server_instance_id: 'mcp-server-0001',
      tool_contract_sha256: 'd'.repeat(64)
    },
    facade_contract: { ...request.facade_contract },
    response_sha256: 'e'.repeat(64)
  };
}

test('read-only bridge forwards only the pre-admitted request and strips IPC descriptor secrets', async () => {
  const calls = [];
  const result = await runDevelopmentReadOnlyBridge(request, {
    appRoot: process.cwd(),
    dependencies: {
      createDevelopmentPaths: () => ({ runtimeIdentity: () => ({ mode: 'development', installation_id: 'a'.repeat(64) }) }),
      loadRecoveryDescriptor: () => descriptor,
      descriptorMatchesInstallation: () => true,
      descriptorRequestOptions: (value) => ({ expectedInstanceId: value.instance_id }),
      clientFactory: () => ({ call: async (...args) => { calls.push(args); return safeResult(); } })
    }
  });
  assert.deepEqual(calls, [[
    'runtime.control_plane_read_only_workspace_context',
    [request],
    { expectedInstanceId: descriptor.instance_id }
  ]]);
  assert.equal(result.workspace_accessed, true);
  assert.equal(result.actor.client_id, 'electron-control-plane-bridge');
  assert.equal(JSON.stringify(result).includes('must-not-be-returned'), false);
  assert.equal(RPC_ACTIONS.includes('runtime.control_plane_read_only_workspace_context'), true);
});

test('read-only bridge allowlists its result so a local workspace path is never exported', () => {
  const unsafe = { ...safeResult(), workspace: 'E:\\private-workspace' };
  // Normalisation is an allowlist, so newly added local result fields must not
  // become part of the Python-to-control-plane receipt payload.
  const result = normalisedResult(descriptor, unsafe);
  assert.equal(Object.hasOwn(result, 'workspace'), false);
  assert.equal(JSON.stringify(result).includes('private-workspace'), false);
});

test('read-only bridge rejects an installation mismatch before it opens Recovery IPC', async () => {
  let called = false;
  await assert.rejects(
    runDevelopmentReadOnlyBridge(request, {
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

test('read-only bridge can use the fixed packaged adapter without a checkout or global Node', async (t) => {
  const installRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-packaged-bridge-'));
  t.after(() => fs.rmSync(installRoot, { recursive: true, force: true }));
  const adapterDirectory = path.join(installRoot, 'resources', 'resources', 'control-plane');
  const appRoot = path.join(installRoot, 'resources', 'app.asar');
  const appData = path.join(installRoot, 'appdata');
  const executablePath = path.join(installRoot, 'Coding Tools MCP.exe');
  fs.mkdirSync(adapterDirectory, { recursive: true });
  fs.mkdirSync(appRoot, { recursive: true });
  fs.mkdirSync(appData, { recursive: true });
  fs.writeFileSync(executablePath, 'fixture');
  const packagedDescriptor = { ...descriptor, runtime_mode: 'packaged' };
  const paths = { runtimeIdentity: () => ({ mode: 'packaged', installation_id: 'a'.repeat(64) }) };
  const result = await runReadOnlyBridge(request, {
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
      clientFactory: () => ({ call: async () => safeResult() })
    }
  });
  assert.equal(result.runtime_mode, 'packaged');
  assert.equal(result.workspace_accessed, true);
  assert.equal(JSON.stringify(result).includes('must-not-be-returned'), false);
});
