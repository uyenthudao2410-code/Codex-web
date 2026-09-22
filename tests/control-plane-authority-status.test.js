const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  parseAuthorityStatusResult,
  ControlPlaneEnrollmentService
} = require('../electron/services/controlPlaneEnrollment');

const identity = Object.freeze({
  version: 1,
  device_id: '12345678-1234-4123-8123-123456789abc',
  display_name: 'DESKTOP-63643J4',
  created_at: '2026-09-16T00:00:00.000Z'
});
function fixturePaths(root) {
  const python = path.join(root, 'python.exe');
  const agent = path.join(root, 'node_agent.py');
  fs.writeFileSync(python, 'fixture');
  fs.writeFileSync(agent, 'fixture');
  return {
    runtimeMode: () => 'packaged',
    portablePython: () => python,
    controlPlaneNodeAgent: () => agent,
    controlPlaneNodeConfigFile: () => path.join(root, 'control-plane-node.json'),
    controlPlaneWorkspaceRegistryFile: () => path.join(root, 'control-plane-workspaces.json'),
    appRoot: () => root,
    executablePath: () => path.join(root, 'Coding Tools MCP.exe')
  };
}

function status(overrides = {}) {
  return {
    device_id: identity.device_id,
    state: 'active',
    node_display_name: identity.display_name,
    workspace_count: 1,
    target_count: 1,
    dispatchable_target_count: 1,
    targets: [{
      node_display_name: identity.display_name,
      workspace_display_name: 'Codex-web',
      capabilities: { read: true, write: true, exec: false },
      binding_state: 'active',
      workspace_state: 'active',
      presence_state: 'online',
      readiness: 'degraded',
      policy_state: 'enabled',
      dispatch_state: 'dispatchable',
      dispatch_blockers: []
    }],
    fresh: true,
    observed_at_ms: 1770000000000,
    error_code: null,
    ...overrides
  };
}

test('authority status parser accepts target state but rejects identifiers or paths', () => {
  const parsed = parseAuthorityStatusResult(JSON.stringify(status()), identity.device_id);
  assert.equal(parsed.state, 'active');
  assert.equal(parsed.targets[0].workspace_display_name, 'Codex-web');
  assert.deepEqual(parsed.targets[0].capabilities, { read: true, write: true, exec: false });
  assert.equal(JSON.stringify(parsed).includes('binding_id'), false);
  assert.equal(JSON.stringify(parsed).includes('workspace_id'), false);
  assert.throws(
    () => parseAuthorityStatusResult(JSON.stringify({ ...status(), targets: [{ ...status().targets[0], local_path: 'C:\\secret' }] }), identity.device_id),
    { code: 'CONTROL_PLANE_AUTHORITY_STATUS_OUTPUT_INVALID' }
  );
});

test('authority status parser preserves opaque workspace identity when supplied', () => {
  const parsed = parseAuthorityStatusResult(JSON.stringify(status({
    targets: [{
      ...status().targets[0],
      workspace_id: 'workspace_0123456789abcdef0123456789abcdef',
      workspace_generation: 'generation_abcdef0123456789abcdef0123456789'
    }]
  })), identity.device_id);
  assert.equal(parsed.targets[0].workspace_id, 'workspace_0123456789abcdef0123456789abcdef');
  assert.equal(parsed.targets[0].workspace_generation, 'generation_abcdef0123456789abcdef0123456789');
});

test('authority status service invokes the packaged node agent without credentials or path arguments', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-authority-status-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const calls = [];
  const service = new ControlPlaneEnrollmentService({
    paths: fixturePaths(root),
    environment: { PATH: '/safe/path', OPENAI_API_KEY: 'must-not-reach-agent' },
    runner: async (...args) => {
      calls.push(args);
      return { code: 0, stdout: JSON.stringify(status()) + '\n', stderr: '' };
    }
  });
  const result = await service.reconcileAuthorityStatus({ deviceIdentity: identity });
  assert.equal(result.state, 'active');
  assert.equal(calls.length, 1);
  const [, args, options] = calls[0];
  assert.deepEqual(args.slice(0, 6), [
    '-I', path.join(root, 'node_agent.py'), 'reconcile-authority-status',
    '--config', path.join(root, 'control-plane-node.json'), '--device-id'
  ]);
  assert.equal(args.includes('must-not-reach-agent'), false);
  assert.deepEqual(options.env, { PATH: '/safe/path' });
});
