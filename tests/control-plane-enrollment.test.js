const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  centralServerOrigin,
  centralWorkspaceId,
  centralWorkspaceGeneration,
  endpointId,
  parseEnrollmentResult,
  parseEnrollmentStatusResult,
  parseCredentialRotationResult,
  parseReadOnlyPolicyInstallResult,
  parseWorkspaceRegistrationResult,
  parseWorkspaceListResult,
  parseWorkspaceRetirementResult,
  parseWorkspaceReplacementResult,
  normalizeWorkspaceCapabilities,
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

test('central enrollment reconciles durable status after reload without passing the node secret to renderer', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-enrollment-status-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const calls = [];
  const service = new ControlPlaneEnrollmentService({
    paths: fixturePaths(root),
    environment: { PATH: '/safe/path', OPENAI_API_KEY: 'must-not-reach-agent' },
    runner: async (...args) => {
      calls.push(args);
      return { code: 0, stdout: JSON.stringify({
        device_id: identity.device_id,
        enrollment_id: 'enroll_12345678',
        state: 'approved',
        credential_generation: 2,
        fresh: true,
        observed_at_ms: Date.now(),
        error_code: null,
        server_origin: 'https://SVHOME.tail0e4032.ts.net/'
      }) + '\n', stderr: '' };
    }
  });
  const status = await service.reconcileEnrollment({ deviceIdentity: identity });
  assert.equal(status.state, 'approved');
  assert.equal(status.credential_generation, 2);
  assert.equal(status.server_origin, 'https://svhome.tail0e4032.ts.net');
  assert.equal(calls.length, 1);
  const [command, args, options] = calls[0];
  assert.equal(command, path.join(root, 'python.exe'));
  assert.deepEqual(args.slice(0, 6), ['-I', path.join(root, 'node_agent.py'), 'reconcile-enrollment', '--config', path.join(root, 'control-plane-node.json'), '--device-id']);
  assert.equal(args.includes('must-not-reach-agent'), false);
  assert.deepEqual(options.env, { PATH: '/safe/path' });
  assert.throws(
    () => parseEnrollmentStatusResult(JSON.stringify({
      device_id: identity.device_id, enrollment_id: 'enroll_12345678', state: 'approved',
      credential_generation: 2, fresh: true, observed_at_ms: Date.now(), error_code: 'bad code'
    }), identity.device_id),
    { code: 'CONTROL_PLANE_ENROLLMENT_STATUS_OUTPUT_INVALID' }
  );
  assert.throws(
    () => parseEnrollmentStatusResult(JSON.stringify({
      device_id: identity.device_id, enrollment_id: 'enroll_12345678', state: 'approved',
      credential_generation: 2, fresh: true, observed_at_ms: Date.now(), error_code: null,
      server_origin: 'https://operator:secret@svhome.tail0e4032.ts.net/'
    }), identity.device_id),
    { code: 'CONTROL_PLANE_ENROLLMENT_STATUS_OUTPUT_INVALID' }
  );
});

test('central executor runs durable credential rotation through the packaged node agent without exposing a secret', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-credential-rotation-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const calls = [];
  const service = new ControlPlaneEnrollmentService({
    paths: fixturePaths(root),
    environment: { PATH: '/safe/path', OPENAI_API_KEY: 'must-not-reach-agent', NODE_SECRET: 'must-not-reach-agent' },
    runner: async (...args) => {
      calls.push(args);
      return { code: 0, stdout: JSON.stringify({
        device_id: identity.device_id,
        rotation_id: `rotate_${'a'.repeat(32)}`,
        state: 'completed',
        current_generation: 2,
        next_generation: 3,
        fresh: true,
        error_code: null
      }) + '\n', stderr: '' };
    }
  });
  const status = await service.rotateCredential({ deviceIdentity: identity });
  assert.deepEqual(status, {
    device_id: identity.device_id.toLowerCase(),
    rotation_id: `rotate_${'a'.repeat(32)}`,
    state: 'completed',
    current_generation: 2,
    next_generation: 3,
    fresh: true,
    error_code: null
  });
  assert.equal(calls.length, 1);
  const [command, args, options] = calls[0];
  assert.equal(command, path.join(root, 'python.exe'));
  assert.deepEqual(args.slice(0, 6), [
    '-I', path.join(root, 'node_agent.py'), 'rotate-credential',
    '--config', path.join(root, 'control-plane-node.json'), '--project-root'
  ]);
  assert.equal(args.includes('must-not-reach-agent'), false);
  assert.deepEqual(options.env, { PATH: '/safe/path' });
  assert.throws(
    () => parseCredentialRotationResult(JSON.stringify({
      device_id: identity.device_id, rotation_id: `rotate_${'a'.repeat(32)}`,
      state: 'completed', current_generation: 2, next_generation: 4,
      fresh: true, error_code: null
    }), identity.device_id),
    { code: 'CONTROL_PLANE_CREDENTIAL_ROTATION_OUTPUT_INVALID' }
  );
});

test('central executor installs only a locally confirmed, assigned read-only policy for one registered workspace', async (t) => {
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
  const workspaceId = 'workspace_0123456789abcdef0123456789abcdef';
  const workspaceGeneration = 'generation_abcdef0123456789abcdef0123456789';
  const receipt = await service.installReadOnlyPolicyAssignment({ workspaceId, workspaceGeneration, replaceExisting: true });
  assert.deepEqual(receipt, {
    enabled: true, expires_at_ms: receipt.expires_at_ms, policy_sha256: 'b'.repeat(64),
    runtime_mode: 'packaged', windows_acl_verified: false
  });
  assert.equal(calls.length, 1);
  const [command, args, options] = calls[0];
  assert.equal(command, path.join(root, 'python.exe'));
  assert.deepEqual(args.slice(0, 4), ['-I', path.join(root, 'node_agent.py'), 'install-read-only-policy-from-assignment', '--config']);
  assert.equal(args.includes(workspaceId), true);
  assert.equal(args.includes(workspaceGeneration), true);
  assert.equal(args.some((value) => String(value).startsWith('ctx_')), false);
  assert.equal(args.includes('--workspace-registry'), true);
  assert.equal(args.includes(path.join(root, 'control-plane-workspaces.json')), true);
  assert.equal(args.includes('--confirm-install'), true);
  assert.equal(args.includes('--replace'), true);
  assert.equal(args.includes('must-not-reach-agent'), false);
  assert.deepEqual(options.env, { PATH: '/safe/path' });
  assert.equal(centralWorkspaceId(workspaceId.toUpperCase()), workspaceId);
  assert.equal(centralWorkspaceGeneration(workspaceGeneration.toUpperCase()), workspaceGeneration);
  assert.throws(
    () => parseReadOnlyPolicyInstallResult(JSON.stringify({ operation: 'control_plane_read_only_policy_installed', enabled: true, expires_at_ms: Date.now() + 60_000, policy_sha256: 'b'.repeat(64), runtime_mode: 'development', windows_acl_verified: false })),
    { code: 'CONTROL_PLANE_POLICY_OUTPUT_INVALID' }
  );
});

test('central executor registers a local workspace with the safe read-only default without passing secrets or path to Ubuntu receipt', async (t) => {
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
      capabilities: { read: false, write: false, exec: false },
      replayed: false,
      state: 'registered'
    })),
    { code: 'CONTROL_PLANE_WORKSPACE_OUTPUT_INVALID' }
  );
});

test('central executor passes owner-selected write and exec capabilities to the packaged node agent', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-workspace-capabilities-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const workspace = path.join(root, 'fixture-workspace');
  fs.mkdirSync(workspace);
  const calls = [];
  const service = new ControlPlaneEnrollmentService({
    paths: fixturePaths(root),
    environment: { PATH: '/safe/path', OPENAI_API_KEY: 'must-not-reach-agent' },
    runner: async (...args) => {
      calls.push(args);
      return { code: 0, stdout: JSON.stringify({
        workspace_id: 'workspace_0123456789abcdef0123456789abcdef',
        workspace_generation: 'generation_abcdef0123456789abcdef0123456789',
        display_name: 'fixture-workspace',
        capabilities: { read: true, write: true, exec: true },
        replayed: false,
        state: 'registered'
      }) + '\n', stderr: '' };
    }
  });
  const receipt = await service.registerWorkspace({
    workspacePath: workspace,
    capabilities: { read: true, write: true, exec: true }
  });
  assert.deepEqual(receipt.capabilities, { read: true, write: true, exec: true });
  const [, args] = calls[0];
  assert.equal(args.includes('--capability-read'), true);
  assert.equal(args.includes('--capability-write'), true);
  assert.equal(args.includes('--capability-exec'), true);
  assert.equal(args.includes('must-not-reach-agent'), false);
});

test('central executor replaces a registered workspace generation only through explicit packaged confirmation', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-workspace-replace-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const workspace = path.join(root, 'fixture-workspace');
  fs.mkdirSync(workspace);
  const calls = [];
  const service = new ControlPlaneEnrollmentService({
    paths: fixturePaths(root),
    environment: { PATH: '/safe/path', OPENAI_API_KEY: 'must-not-reach-agent' },
    runner: async (...args) => {
      calls.push(args);
      return { code: 0, stdout: JSON.stringify({
        workspace_id: 'workspace_0123456789abcdef0123456789abcdef',
        old_workspace_generation: 'generation_abcdef0123456789abcdef0123456789',
        workspace_generation: 'generation_fedcba9876543210fedcba9876543210',
        display_name: 'fixture-workspace',
        capabilities: { read: true, write: true, exec: true },
        replayed: true,
        state: 'replaced'
      }) + '\n', stderr: '' };
    }
  });
  const receipt = await service.replaceWorkspace({ workspacePath: workspace, capabilities: { read: true, write: true, exec: true } });
  assert.deepEqual(receipt, {
    workspace_id: 'workspace_0123456789abcdef0123456789abcdef',
    old_workspace_generation: 'generation_abcdef0123456789abcdef0123456789',
    workspace_generation: 'generation_fedcba9876543210fedcba9876543210',
    display_name: 'fixture-workspace',
    capabilities: { read: true, write: true, exec: true },
    replayed: true,
    state: 'replaced'
  });
  assert.equal(calls.length, 1);
  const [command, args, options] = calls[0];
  assert.equal(command, path.join(root, 'python.exe'));
  assert.deepEqual(args.slice(0, 4), ['-I', path.join(root, 'node_agent.py'), 'replace-workspace', '--config']);
  assert.equal(args.includes('--confirm-replace'), true);
  assert.equal(args.includes('--capability-read'), true);
  assert.equal(args.includes('--capability-write'), true);
  assert.equal(args.includes('--capability-exec'), true);
  assert.equal(args.includes('must-not-reach-agent'), false);
  assert.deepEqual(options.env, { PATH: '/safe/path' });
  assert.equal(JSON.stringify(receipt).includes(workspace), false);
  assert.throws(
    () => parseWorkspaceReplacementResult(JSON.stringify({
      workspace_id: 'workspace_0123456789abcdef0123456789abcdef',
      old_workspace_generation: 'generation_abcdef0123456789abcdef0123456789',
      workspace_generation: 'generation_fedcba9876543210fedcba9876543210',
      display_name: 'fixture-workspace', capabilities: { read: true, write: true, exec: true },
      replayed: false, state: 'registered'
    })),
    { code: 'CONTROL_PLANE_WORKSPACE_REPLACE_OUTPUT_INVALID' }
  );
});

test('workspace capability input is exact, boolean-only, and always requires read', () => {
  assert.deepEqual(normalizeWorkspaceCapabilities(), { read: true, write: false, exec: false });
  assert.deepEqual(normalizeWorkspaceCapabilities({ read: true, write: true, exec: true }), { read: true, write: true, exec: true });
  for (const value of [
    { read: true, write: false },
    { read: true, write: false, exec: false, shell: true },
    { read: true, write: 'yes', exec: false },
    { read: false, write: true, exec: true }
  ]) {
    assert.throws(() => normalizeWorkspaceCapabilities(value), { code: /CONTROL_PLANE_WORKSPACE_/ });
  }
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
      capabilities: { read: false, write: true, exec: false }
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
  await assert.rejects(
    development.rotateCredential({ deviceIdentity: identity }),
    { code: 'CONTROL_PLANE_CREDENTIAL_ROTATION_PACKAGED_REQUIRED' }
  );
  assert.equal(called, false);
  assert.throws(
    () => parseEnrollmentResult(JSON.stringify({ enrollment_id: 'enroll_12345678', device_id: identity.device_id, state: 'revoked' }), identity.device_id),
    { code: 'CONTROL_PLANE_ENROLLMENT_OUTPUT_INVALID' }
  );
});
