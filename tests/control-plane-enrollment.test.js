const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  centralServerOrigin,
  centralContextId,
  centralWorkspaceId,
  centralWorkspaceGeneration,
  endpointId,
  parseEnrollmentResult,
  parseReadOnlyPolicyInstallResult,
  parseWorkspaceRegistrationResult,
  parseWorkspaceListResult,
  parseWorkspaceRetirementResult,
  ControlPlaneEnrollmentService
} = require('../electron/services/controlPlaneEnrollment');

const identity = Object.freeze({
  version: 1,
  device_id: '12345678-1234-4123-8123-123456789abc',
  display_name: 'DESKTOP-63643J4',
  created_at: '2026-09-16T00:00:00.000Z'
});

function fixturePaths(root, { mode = 'packaged' } = {}) {
  const python = path.join(root, 'python.exe');
  const agent = path.join(root, 'node_agent.py');
  fs.writeFileSync(python, 'fixture');
  fs.writeFileSync(agent, 'fixture');
  return {
    runtimeMode: () => mode,
    portablePython: () => python,
    controlPlaneNodeAgent: () => agent,
    controlPlaneNodeConfigFile: () => path.join(root, 'control-plane-node.json'),
    controlPlaneWorkspaceRegistryFile: () => path.join(root, 'control-plane-workspaces.json'),
    appRoot: () => root,
    executablePath: () => path.join(root, 'Coding Tools MCP.exe')
  };
}

test('central enrollment accepts only a credential-free HTTPS Ubuntu origin', () => {
  assert.equal(centralServerOrigin('https://SVHOME.tail0e4032.ts.net/'), 'https://svhome.tail0e4032.ts.net');
  assert.throws(() => centralServerOrigin('http://100.116.112.22:8765'), { code: 'CONTROL_PLANE_SERVER_URL_INVALID' });
  assert.throws(() => centralServerOrigin('https://svhome.tail0e4032.ts.net/mcp'), { code: 'CONTROL_PLANE_SERVER_URL_INVALID' });
  assert.equal(endpointId(identity.device_id), 'executor-12345678-1234-4123-8123-123456789abc');
});

test('central enrollment invokes only the packaged node agent and never passes OpenAI secrets', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-enrollment-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const calls = [];
  const service = new ControlPlaneEnrollmentService({
    paths: fixturePaths(root),
    environment: { PATH: '/safe/path', OPENAI_API_KEY: 'must-not-reach-agent', CUSTOM_SECRET: 'must-not-reach-agent' },
    runner: async (...args) => {
      calls.push(args);
      return { code: 0, stdout: JSON.stringify({
        enrollment_id: 'enroll_12345678', device_id: identity.device_id, state: 'pending_operator_approval'
      }) + '\n', stderr: '' };
    }
  });
  const receipt = await service.request({ serverUrl: 'https://svhome.tail0e4032.ts.net/', deviceIdentity: identity });
  assert.deepEqual(receipt, {
    enrollment_id: 'enroll_12345678',
    device_id: identity.device_id,
    state: 'pending_operator_approval',
    server_origin: 'https://svhome.tail0e4032.ts.net',
    endpoint_id: 'executor-12345678-1234-4123-8123-123456789abc',
    display_name: identity.display_name
  });
  assert.equal(calls.length, 1);
  const [command, args, options] = calls[0];
  assert.equal(command, path.join(root, 'python.exe'));
  assert.deepEqual(args.slice(0, 4), ['-I', path.join(root, 'node_agent.py'), 'request-enrollment', '--config']);
  assert.equal(args.includes('--replace-existing-config'), false);
  assert.equal(args.includes('must-not-reach-agent'), false);
  assert.deepEqual(options.env, { PATH: '/safe/path' });
});

test('central executor installs only a locally confirmed, node-scoped read-only policy', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-policy-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const calls = [];
  const service = new ControlPlaneEnrollmentService({
    paths: fixturePaths(root),
    environment: { PATH: '/safe/path', OPENAI_API_KEY: 'must-not-reach-agent', CUSTOM_SECRET: 'must-not-reach-agent' },
    runner: async (...args) => {
      calls.push(args);
      return { code: 0, stdout: JSON.stringify({
        operation: 'control_plane_read_only_policy_installed', enabled: true,
        expires_at_ms: Date.now() + 60_000, policy_sha256: 'b'.repeat(64),
        runtime_mode: 'packaged', windows_acl_verified: false
      }) + '\n', stderr: '' };
    }
  });
  const contextId = 'ctx_0123456789abcdef0123456789abcdef';
  const receipt = await service.installReadOnlyPolicy({ contextId, replaceExisting: true });
  assert.deepEqual(receipt, {
    enabled: true, expires_at_ms: receipt.expires_at_ms, policy_sha256: 'b'.repeat(64),
    runtime_mode: 'packaged', windows_acl_verified: false
  });
  assert.equal(calls.length, 1);
  const [command, args, options] = calls[0];
  assert.equal(command, path.join(root, 'python.exe'));
  assert.deepEqual(args.slice(0, 4), ['-I', path.join(root, 'node_agent.py'), 'install-read-only-policy-from-context', '--config']);
  assert.equal(args.includes(contextId), true);
  assert.equal(args.includes('--workspace-registry'), true);
  assert.equal(args.includes(path.join(root, 'control-plane-workspaces.json')), true);
  assert.equal(args.includes('--confirm-install'), true);
  assert.equal(args.includes('--replace'), true);
  assert.equal(args.includes('must-not-reach-agent'), false);
  assert.deepEqual(options.env, { PATH: '/safe/path' });
  assert.equal(centralContextId(contextId.toUpperCase()), contextId);
  assert.throws(() => centralContextId('ctx_wrong'), { code: 'CONTROL_PLANE_CONTEXT_ID_INVALID' });
  assert.throws(
    () => parseReadOnlyPolicyInstallResult(JSON.stringify({ operation: 'control_plane_read_only_policy_installed', enabled: true, expires_at_ms: Date.now() + 60_000, policy_sha256: 'b'.repeat(64), runtime_mode: 'development', windows_acl_verified: false })),
    { code: 'CONTROL_PLANE_POLICY_OUTPUT_INVALID' }
  );
});

test('central executor registers only a local read-only workspace without passing secrets or path to Ubuntu receipt', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-workspace-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const workspace = path.join(root, 'fixture-workspace');
  fs.mkdirSync(workspace);
  const calls = [];
  const service = new ControlPlaneEnrollmentService({
    paths: fixturePaths(root),
    environment: { PATH: '/safe/path', OPENAI_API_KEY: 'must-not-reach-agent', CUSTOM_SECRET: 'must-not-reach-agent' },
    runner: async (...args) => {
      calls.push(args);
      return { code: 0, stdout: JSON.stringify({
        workspace_id: 'workspace_0123456789abcdef0123456789abcdef',
        workspace_generation: 'generation_abcdef0123456789abcdef0123456789',
        display_name: 'fixture-workspace',
        capabilities: { read: true, write: false, exec: false },
        replayed: false,
        state: 'registered'
      }) + '\n', stderr: '' };
    }
  });

  const receipt = await service.registerWorkspace({ workspacePath: workspace });
  assert.deepEqual(receipt, {
    workspace_id: 'workspace_0123456789abcdef0123456789abcdef',
    workspace_generation: 'generation_abcdef0123456789abcdef0123456789',
    display_name: 'fixture-workspace',
    capabilities: { read: true, write: false, exec: false },
    replayed: false,
    state: 'registered'
  });
  assert.equal(JSON.stringify(receipt).includes(workspace), false);
  assert.equal(calls.length, 1);
  const [command, args, options] = calls[0];
  assert.equal(command, path.join(root, 'python.exe'));
  assert.deepEqual(args.slice(0, 4), ['-I', path.join(root, 'node_agent.py'), 'register-workspace', '--config']);
  assert.equal(args.includes('--workspace-registry'), true);
  assert.equal(args.includes(path.join(root, 'control-plane-workspaces.json')), true);
  assert.equal(args.includes('--workspace-path'), true);
  assert.equal(args.includes(fs.realpathSync.native(workspace)), true);
  assert.equal(args.includes('--capability-read'), true);
  assert.equal(args.includes('--capability-write'), false);
  assert.equal(args.includes('--capability-exec'), false);
  assert.equal(args.includes('must-not-reach-agent'), false);
  assert.deepEqual(options.env, { PATH: '/safe/path' });

  assert.throws(
    () => parseWorkspaceRegistrationResult(JSON.stringify({
      workspace_id: 'workspace_0123456789abcdef0123456789abcdef',
      workspace_generation: 'generation_abcdef0123456789abcdef0123456789',
      display_name: 'fixture-workspace',
      capabilities: { read: true, write: true, exec: false },
      replayed: false,
      state: 'registered'
    })),
    { code: 'CONTROL_PLANE_WORKSPACE_OUTPUT_INVALID' }
  );
});

test('central executor lists and retires only an opaque registered workspace after a central receipt', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-workspace-retire-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const calls = [];
  const workspaceId = 'workspace_0123456789abcdef0123456789abcdef';
  const workspaceGeneration = 'generation_abcdef0123456789abcdef0123456789';
  const service = new ControlPlaneEnrollmentService({
    paths: fixturePaths(root),
    environment: { PATH: '/safe/path', OPENAI_API_KEY: 'must-not-reach-agent', CUSTOM_SECRET: 'must-not-reach-agent' },
    runner: async (...args) => {
      calls.push(args);
      const agentArguments = args[1];
      if (agentArguments.includes('list-workspaces')) {
        return { code: 0, stdout: JSON.stringify({ workspaces: [{
          workspace_id: workspaceId,
          workspace_generation: workspaceGeneration,
          display_name: 'fixture-workspace',
          capabilities: { read: true, write: false, exec: false }
        }] }) + '\n', stderr: '' };
      }
      if (agentArguments.includes('retire-workspace')) {
        return { code: 0, stdout: JSON.stringify({
          workspace_id: workspaceId,
          workspace_generation: workspaceGeneration,
          display_name: 'fixture-workspace',
          capabilities: { read: true, write: false, exec: false },
          replayed: true,
          state: 'retired'
        }) + '\n', stderr: '' };
      }
      throw new Error('unexpected node agent command');
    }
  });

  const listed = await service.listWorkspaces();
  assert.deepEqual(listed, [{
    workspace_id: workspaceId,
    workspace_generation: workspaceGeneration,
    display_name: 'fixture-workspace',
    capabilities: { read: true, write: false, exec: false }
  }]);
  const receipt = await service.retireWorkspace({ workspaceId, workspaceGeneration });
  assert.deepEqual(receipt, {
    workspace_id: workspaceId,
    workspace_generation: workspaceGeneration,
    display_name: 'fixture-workspace',
    capabilities: { read: true, write: false, exec: false },
    replayed: true,
    state: 'retired'
  });
  assert.equal(calls.length, 2);
  const [listCommand, listArgs, listOptions] = calls[0];
  assert.equal(listCommand, path.join(root, 'python.exe'));
  assert.deepEqual(listArgs.slice(0, 4), ['-I', path.join(root, 'node_agent.py'), 'list-workspaces', '--config']);
  assert.equal(listArgs.includes('--workspace-registry'), true);
  assert.equal(listArgs.includes('must-not-reach-agent'), false);
  assert.deepEqual(listOptions.env, { PATH: '/safe/path' });
  const [retireCommand, retireArgs, retireOptions] = calls[1];
  assert.equal(retireCommand, path.join(root, 'python.exe'));
  assert.deepEqual(retireArgs.slice(0, 4), ['-I', path.join(root, 'node_agent.py'), 'retire-workspace', '--config']);
  assert.equal(retireArgs.includes(workspaceId), true);
  assert.equal(retireArgs.includes(workspaceGeneration), true);
  assert.equal(retireArgs.includes('must-not-reach-agent'), false);
  assert.deepEqual(retireOptions.env, { PATH: '/safe/path' });
  assert.equal(centralWorkspaceId(workspaceId.toUpperCase()), workspaceId);
  assert.equal(centralWorkspaceGeneration(workspaceGeneration.toUpperCase()), workspaceGeneration);
  assert.throws(() => centralWorkspaceId('workspace_wrong'), { code: 'CONTROL_PLANE_WORKSPACE_ID_INVALID' });
  assert.throws(() => centralWorkspaceGeneration('generation_wrong'), { code: 'CONTROL_PLANE_WORKSPACE_GENERATION_INVALID' });
  assert.throws(
    () => parseWorkspaceListResult(JSON.stringify({ workspaces: [{
      workspace_id: workspaceId,
      workspace_generation: workspaceGeneration,
      display_name: 'fixture-workspace',
      capabilities: { read: true, write: true, exec: false }
    }] })),
    { code: 'CONTROL_PLANE_WORKSPACE_LIST_OUTPUT_INVALID' }
  );
  assert.throws(
    () => parseWorkspaceRetirementResult(JSON.stringify({
      workspace_id: workspaceId,
      workspace_generation: workspaceGeneration,
      display_name: 'fixture-workspace',
      capabilities: { read: true, write: false, exec: false },
      replayed: false,
      state: 'registered'
    })),
    { code: 'CONTROL_PLANE_WORKSPACE_RETIRE_OUTPUT_INVALID' }
  );
});

test('central enrollment rejects malformed agent output and development source mode before an invocation', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-enrollment-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  let called = false;
  const development = new ControlPlaneEnrollmentService({
    paths: fixturePaths(root, { mode: 'development' }),
    runner: async () => { called = true; return { stdout: '' }; }
  });
  await assert.rejects(
    development.request({ serverUrl: 'https://svhome.tail0e4032.ts.net', deviceIdentity: identity }),
    { code: 'CONTROL_PLANE_ENROLLMENT_PACKAGED_REQUIRED' }
  );
  await assert.rejects(
    development.registerWorkspace({ workspacePath: root }),
    { code: 'CONTROL_PLANE_WORKSPACE_PACKAGED_REQUIRED' }
  );
  assert.equal(called, false);
  assert.throws(
    () => parseEnrollmentResult(JSON.stringify({ enrollment_id: 'enroll_12345678', device_id: identity.device_id, state: 'approved' }), identity.device_id),
    { code: 'CONTROL_PLANE_ENROLLMENT_OUTPUT_INVALID' }
  );
});
