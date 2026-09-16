const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  centralServerOrigin,
  centralContextId,
  endpointId,
  parseEnrollmentResult,
  parseReadOnlyPolicyInstallResult,
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
  assert.equal(called, false);
  assert.throws(
    () => parseEnrollmentResult(JSON.stringify({ enrollment_id: 'enroll_12345678', device_id: identity.device_id, state: 'approved' }), identity.device_id),
    { code: 'CONTROL_PLANE_ENROLLMENT_OUTPUT_INVALID' }
  );
});
