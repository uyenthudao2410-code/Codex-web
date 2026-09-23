const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');

const {
  ControlPlaneEnrollmentService,
  parsePolicyAuthorityObservation,
  parseStandingFilePolicyInstallResult,
  parseStandingFilePolicyObservation
} = require('../electron/services/controlPlaneEnrollment');

const workspaceId = 'workspace_0123456789abcdef0123456789abcdef';
const workspaceGeneration = 'generation_abcdef0123456789abcdef0123456789';
const facade = Object.freeze({ schema_version: 20, profile: 'control-plane-private-tunnel-service-v1', sha256: 'a'.repeat(64) });
const prefixDigest = crypto.createHash('sha256').update('["."]').digest('hex');

function fixturePaths(root) {
  const python = path.join(root, 'python.exe');
  const agent = path.join(root, 'node_agent.py');
  fs.writeFileSync(python, 'fixture');
  fs.writeFileSync(agent, 'fixture');
  return {
    runtimeMode: () => 'packaged', portablePython: () => python,
    controlPlaneNodeAgent: () => agent,
    controlPlaneNodeConfigFile: () => path.join(root, 'control-plane-node.json'),
    controlPlaneWorkspaceRegistryFile: () => path.join(root, 'control-plane-workspaces.json'),
    appRoot: () => root, executablePath: () => path.join(root, 'Coding Tools MCP.exe')
  };
}

function authority() {
  return {
    operation: 'control_plane_policy_authority_observation', owner_id: 'owner_default',
    workspace_id: workspaceId, workspace_generation: workspaceGeneration,
    facade_contract: facade, binding_count: 1, standing_write_enabled: true,
    observed_at_ms: Date.now(), runtime_mode: 'packaged'
  };
}

function installReceipt(kind) {
  const read = kind === 'file_read';
  return {
    operation: read ? 'control_plane_file_read_policy_installed' : 'control_plane_approved_patch_policy_installed',
    enabled: true, authority_mode: 'standing', expires_at_ms: null,
    policy_sha256: (read ? 'b' : 'c').repeat(64),
    allowed_prefix_count: 1, allowed_prefixes_sha256: prefixDigest,
    ...(read ? { max_bytes: 16 * 1024, max_lines: 200 }
      : { max_patch_bytes: 32 * 1024, max_file_bytes: 256 * 1024, validation_profile: 'targeted' }),
    runtime_mode: 'packaged', windows_acl_verified: false
  };
}

function observed(kind, enabled = true) {
  return {
    ...installReceipt(kind),
    operation: kind === 'file_read' ? 'control_plane_file_read_policy_observation' : 'control_plane_approved_patch_policy_observation',
    state: enabled ? 'enabled' : 'expired_or_disabled', enabled,
    workspace_id: workspaceId, workspace_generation: workspaceGeneration
  };
}

test('packaged policy service gets authenticated authority and scopes standing read+patch to the selected registered generation', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-standing-file-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const calls = [];
  const service = new ControlPlaneEnrollmentService({
    paths: fixturePaths(root),
    environment: { PATH: '/safe/path', OPENAI_API_KEY: 'must-not-reach-agent' },
    runner: async (_command, args, options) => {
      calls.push({ args, options });
      const operation = args[2];
      const payload = operation === 'list-workspaces'
        ? { workspaces: [{ workspace_id: workspaceId, workspace_generation: workspaceGeneration,
          display_name: 'fixture', capabilities: { read: true, write: true, exec: false } }] }
        : operation === 'inspect-policy-authority' ? authority()
          : operation === 'inspect-file-read-policy' ? { operation: 'control_plane_file_read_policy_observation',
            state: 'unavailable', reason: 'CONTROL_PLANE_FILE_READ_POLICY_MISSING', runtime_mode: 'packaged', windows_acl_verified: false }
            : operation === 'inspect-approved-patch-policy' ? { operation: 'control_plane_approved_patch_policy_observation',
              state: 'unavailable', reason: 'CONTROL_PLANE_APPROVED_PATCH_POLICY_MISSING', runtime_mode: 'packaged', windows_acl_verified: false }
              : operation === 'install-file-read-policy' ? installReceipt('file_read')
                : operation === 'install-approved-patch-policy' ? installReceipt('approved_patch')
                  : null;
      assert.ok(payload, `unexpected command ${operation}`);
      return { stdout: JSON.stringify(payload) + '\n' };
    }
  });
  const result = await service.installStandingWorkspaceFilePolicies({
    workspaceId, workspaceGeneration, allowWrite: true, replaceExisting: true
  });
  assert.equal(result.state, 'read_and_patch');
  assert.equal(result.workspace_id, workspaceId);
  assert.equal(result.approved_patch.policy_sha256, 'c'.repeat(64));
  assert.deepEqual(calls.map(({ args }) => args[2]), [
    'list-workspaces', 'inspect-policy-authority', 'inspect-file-read-policy',
    'inspect-approved-patch-policy', 'install-file-read-policy', 'install-approved-patch-policy'
  ]);
  for (const { args, options } of calls.slice(-2)) {
    assert.equal(args[args.indexOf('--workspace-id') + 1], workspaceId);
    assert.equal(args[args.indexOf('--workspace-generation') + 1], workspaceGeneration);
    assert.equal(args[args.indexOf('--owner-id') + 1], 'owner_default');
    assert.equal(args[args.indexOf('--facade-sha256') + 1], facade.sha256);
    assert.equal(args[args.indexOf('--allowed-relative-prefix') + 1], '.');
    assert.equal(args.includes('--expires-at-ms'), false);
    assert.equal(args.includes('--confirm-install'), true);
    assert.equal(args.includes('--replace'), true);
    assert.equal(args.includes('must-not-reach-agent'), false);
    assert.deepEqual(options.env, { PATH: '/safe/path' });
  }
});

test('policy receipt parsers reject wrong target, stale mode and narrower or fabricated scope', () => {
  assert.throws(() => parsePolicyAuthorityObservation(JSON.stringify({ ...authority(), workspace_id: 'workspace_' + 'f'.repeat(32) }), workspaceId, workspaceGeneration),
    { code: 'CONTROL_PLANE_POLICY_AUTHORITY_OUTPUT_INVALID' });
  assert.throws(() => parseStandingFilePolicyInstallResult(JSON.stringify({ ...installReceipt('file_read'), allowed_prefix_count: 2 }), 'file_read'),
    { code: 'CONTROL_PLANE_FILE_POLICY_OUTPUT_INVALID' });
  assert.throws(() => parseStandingFilePolicyInstallResult(JSON.stringify({ ...installReceipt('approved_patch'), authority_mode: 'expiring_legacy' }), 'approved_patch'),
    { code: 'CONTROL_PLANE_FILE_POLICY_OUTPUT_INVALID' });
  assert.deepEqual(parseStandingFilePolicyObservation(JSON.stringify(observed('file_read')), 'file_read'), {
    state: 'enabled', enabled: true, workspace_id: workspaceId,
    workspace_generation: workspaceGeneration, policy_sha256: 'b'.repeat(64)
  });
  assert.equal(parseStandingFilePolicyObservation(JSON.stringify({ ...observed('approved_patch'), allowed_prefixes_sha256: 'f'.repeat(64) }), 'approved_patch').state,
    'not_current_standing');
});

test('read-only policy transition disables a previously enabled patch lane before installing a new read lane', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-file-read-only-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const commands = [];
  const service = new ControlPlaneEnrollmentService({
    paths: fixturePaths(root),
    runner: async (_command, args) => {
      const operation = args[2];
      commands.push(operation);
      const payload = operation === 'list-workspaces'
        ? { workspaces: [{ workspace_id: workspaceId, workspace_generation: workspaceGeneration,
          display_name: 'fixture', capabilities: { read: true, write: false, exec: false } }] }
        : operation === 'inspect-policy-authority' ? { ...authority(), standing_write_enabled: false }
          : operation === 'inspect-file-read-policy' ? { operation: 'control_plane_file_read_policy_observation',
            state: 'unavailable', reason: 'CONTROL_PLANE_FILE_READ_POLICY_MISSING', runtime_mode: 'packaged', windows_acl_verified: false }
            : operation === 'inspect-approved-patch-policy' ? observed('approved_patch')
              : operation === 'disable-approved-patch-policy' ? {
                operation: 'control_plane_approved_patch_policy_disabled', enabled: false,
                policy_sha256: 'd'.repeat(64), runtime_mode: 'packaged', windows_acl_verified: false
              }
                : operation === 'install-file-read-policy' ? installReceipt('file_read') : null;
      assert.ok(payload, `unexpected command ${operation}`);
      return { stdout: JSON.stringify(payload) + '\n' };
    }
  });
  const result = await service.installStandingWorkspaceFilePolicies({ workspaceId, workspaceGeneration, allowWrite: false, replaceExisting: true });
  assert.equal(result.state, 'read_only');
  assert.ok(commands.indexOf('disable-approved-patch-policy') < commands.indexOf('install-file-read-policy'));
  assert.equal(commands.includes('install-approved-patch-policy'), false);
});

test('patch installer failure returns an explicit read-only partial receipt after the prior patch lane is disabled', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-file-partial-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const commands = [];
  const service = new ControlPlaneEnrollmentService({
    paths: fixturePaths(root),
    runner: async (_command, args) => {
      const operation = args[2];
      commands.push(operation);
      if (operation === 'install-approved-patch-policy') {
        throw Object.assign(new Error('simulated installer failure'), { code: 'INSTALLER_FAILED' });
      }
      const payload = operation === 'list-workspaces'
        ? { workspaces: [{ workspace_id: workspaceId, workspace_generation: workspaceGeneration,
          display_name: 'fixture', capabilities: { read: true, write: true, exec: false } }] }
        : operation === 'inspect-policy-authority' ? authority()
          : operation === 'inspect-file-read-policy' ? { operation: 'control_plane_file_read_policy_observation',
            state: 'unavailable', reason: 'CONTROL_PLANE_FILE_READ_POLICY_MISSING', runtime_mode: 'packaged', windows_acl_verified: false }
            : operation === 'inspect-approved-patch-policy' ? observed('approved_patch')
              : operation === 'disable-approved-patch-policy' ? {
                operation: 'control_plane_approved_patch_policy_disabled', enabled: false,
                policy_sha256: 'd'.repeat(64), runtime_mode: 'packaged', windows_acl_verified: false
              }
                : operation === 'install-file-read-policy' ? installReceipt('file_read') : null;
      assert.ok(payload, `unexpected command ${operation}`);
      return { stdout: JSON.stringify(payload) + '\n' };
    }
  });
  const result = await service.installStandingWorkspaceFilePolicies({ workspaceId, workspaceGeneration, allowWrite: true, replaceExisting: true });
  assert.equal(result.state, 'read_only_partial');
  assert.equal(result.approved_patch, null);
  assert.equal(result.error_code, 'INSTALLER_FAILED');
  assert.ok(commands.indexOf('disable-approved-patch-policy') < commands.indexOf('install-file-read-policy'));
  assert.ok(commands.indexOf('install-file-read-policy') < commands.indexOf('install-approved-patch-policy'));
});
