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
  fs.writeFileSync(path.join(root, 'control-plane-workspaces.json'), JSON.stringify({
    schema_version: 1, entries: [{
      workspace_id: workspaceId, workspace_generation: workspaceGeneration, canonical_path: root
    }]
  }));
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
    exec_enabled: true, exec_binding_count: 1,
    observed_at_ms: Date.now(), server_observed_at_ms: Date.now(), runtime_mode: 'packaged'
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
    facade_contract: facade,
    workspace_id: workspaceId, workspace_generation: workspaceGeneration
  };
}

function missingExecPolicy() {
  return {
    operation: 'control_plane_exec_policy_observation',
    execution: 'exec_policy_inspected',
    runtime_mode: 'packaged',
    state: 'unavailable',
    reason: 'CONTROL_PLANE_EXEC_POLICY_MISSING'
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
          : operation === 'inspect-exec-policy' ? missingExecPolicy()
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
    'inspect-approved-patch-policy',
    'install-file-read-policy', 'install-approved-patch-policy'
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
    workspace_generation: workspaceGeneration, policy_sha256: 'b'.repeat(64), facade_contract: facade
  });
  assert.equal(parseStandingFilePolicyObservation(JSON.stringify({ ...observed('approved_patch'), allowed_prefixes_sha256: 'f'.repeat(64) }), 'approved_patch').state,
    'not_current_standing');
});

test('file observations expose installed facade and authenticate one fresh current contract for both lanes', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-file-contract-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const commands = [];
  const stale = { ...facade, sha256: 'f'.repeat(64) };
  const service = new ControlPlaneEnrollmentService({ paths: fixturePaths(root),
    runner: async (_command, args) => {
      const operation = args[2]; commands.push(operation);
      const payload = operation === 'inspect-policy-authority' ? authority()
        : { ...observed(operation === 'inspect-file-read-policy' ? 'file_read' : 'approved_patch'), facade_contract: stale };
      return { stdout: JSON.stringify(payload) };
    }
  });
  const result = await service.inspectStandingWorkspaceFilePolicies();
  for (const policy of [result.file_read, result.approved_patch]) {
    assert.deepEqual(policy.facade_contract, stale);
    assert.deepEqual(policy.current_facade_contract, facade);
    assert.ok(Number.isSafeInteger(policy.authority_observed_at_ms));
  }
  assert.equal(commands.filter(command => command === 'inspect-policy-authority').length, 1);
  assert.equal(commands.some(command => command.startsWith('install-')), false);
});

test('file observations cannot reuse missing, invalid or unavailable current facade evidence', async (t) => {
  for (const installed of [null, { ...facade, schema_version: 0 }, { ...facade, sha256: 'invalid' }, { ...facade, extra: true }]) {
    assert.throws(() => parseStandingFilePolicyObservation(JSON.stringify({ ...observed('file_read'), facade_contract: installed }), 'file_read'),
      { code: 'CONTROL_PLANE_FILE_POLICY_OBSERVATION_INVALID' });
  }
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-file-contract-unknown-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  for (const freshness of ['stale', 'future', 'unavailable', 'wrong-target']) {
    const service = new ControlPlaneEnrollmentService({ paths: fixturePaths(root), runner: async (_command, args) => {
      if (args[2] === 'inspect-policy-authority') {
        if (freshness === 'unavailable') throw Object.assign(new Error('not returned'), { code: 'AUTHORITY_OFFLINE' });
        const response = authority();
        if (freshness === 'stale') response.observed_at_ms = Date.now() - 60_000;
        if (freshness === 'future') response.observed_at_ms = Date.now() + 60_000;
        if (freshness === 'wrong-target') response.workspace_generation = 'generation_' + 'f'.repeat(32);
        return { stdout: JSON.stringify(response) };
      }
      return { stdout: JSON.stringify(observed(args[2] === 'inspect-file-read-policy' ? 'file_read' : 'approved_patch')) };
    } });
    const result = await service.inspectStandingWorkspaceFilePolicies();
    assert.equal(result.file_read.current_facade_contract, null, freshness);
    assert.equal(result.approved_patch.authority_observed_at_ms, null, freshness);
  }
});

test('file contract observation preserves the server write admission gate independently of read access', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-file-write-disabled-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const service = new ControlPlaneEnrollmentService({ paths: fixturePaths(root), runner: async (_command, args) => ({
    stdout: JSON.stringify(args[2] === 'inspect-policy-authority' ? { ...authority(), standing_write_enabled: false }
      : observed(args[2] === 'inspect-file-read-policy' ? 'file_read' : 'approved_patch'))
  }) });
  const result = await service.inspectStandingWorkspaceFilePolicies();
  assert.deepEqual(result.file_read.current_facade_contract, facade);
  assert.equal(result.approved_patch.current_facade_contract, null);
  assert.equal(result.approved_patch.reason, 'CONTROL_PLANE_PATCH_POLICY_NOT_ADMITTED');
});

test('read-only policy transition disables only the selected generation patch lane before installing its read lane', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-file-read-only-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const commands = [];
  const service = new ControlPlaneEnrollmentService({
    paths: fixturePaths(root),
    runner: async (_command, args) => {
      const operation = args[2];
      commands.push(operation);
      if (operation.startsWith('inspect-') && operation !== 'inspect-policy-authority'
        || operation === 'disable-approved-patch-policy') {
        assert.equal(args[args.indexOf('--workspace-id') + 1], workspaceId);
        assert.equal(args[args.indexOf('--workspace-generation') + 1], workspaceGeneration);
      }
      const payload = operation === 'list-workspaces'
        ? { workspaces: [{ workspace_id: workspaceId, workspace_generation: workspaceGeneration,
          display_name: 'fixture', capabilities: { read: true, write: false, exec: false } }] }
        : operation === 'inspect-policy-authority' ? { ...authority(), standing_write_enabled: false }
          : operation === 'inspect-exec-policy' ? missingExecPolicy()
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
          : operation === 'inspect-exec-policy' ? missingExecPolicy()
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
