const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const { ControlPlaneEnrollmentService, parseWorkspaceActivationResult } = require('../electron/services/controlPlaneEnrollment');

const workspaceId = `workspace_${'1'.repeat(32)}`;
const workspaceGeneration = `generation_${'2'.repeat(32)}`;
const receipt = () => ({ device_id: '12345678-1234-4123-8123-123456789abc',
  workspace_id: workspaceId, workspace_generation: workspaceGeneration,
  binding_id: `bind_${'3'.repeat(32)}`, pilot_decision_id: `pilot_${'4'.repeat(32)}`,
  expires_at_ms: Date.now() + 60000, replayed: false, state: 'active' });

function fixture(t, runner) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'activate-folder-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const python = path.join(root, 'python.exe');
  const agent = path.join(root, 'node_agent.py');
  fs.writeFileSync(python, 'fixture'); fs.writeFileSync(agent, 'fixture');
  const registry = path.join(root, 'registry.json');
  const entry = { workspace_id: workspaceId, workspace_generation: workspaceGeneration, canonical_path: fs.realpathSync(root) };
  fs.writeFileSync(registry, JSON.stringify({ schema_version: 1, entries: [entry] }));
  const paths = { runtimeMode: () => 'packaged', portablePython: () => python,
    controlPlaneNodeAgent: () => agent, controlPlaneWorkspaceRegistryFile: () => registry,
    controlPlaneNodeConfigFile: () => path.join(root, 'config.json'), appRoot: () => root,
    executablePath: () => path.join(root, 'Coding Tools MCP.exe') };
  const service = new ControlPlaneEnrollmentService({ paths, runner, environment: { PATH: 'safe', OPENAI_API_KEY: 'private' } });
  return { root, registry, entry, paths, service };
}

test('activation carries exact registered identity and returns only local canonical display path', async (t) => {
  const calls = [];
  const f = fixture(t, async (...args) => { calls.push(args); return { code: 0, stdout: JSON.stringify(receipt()) }; });
  const result = await f.service.activateWorkspace({ workspaceId, workspaceGeneration, confirmActivate: true });
  assert.equal(result.workspace_path, fs.realpathSync.native(f.root));
  const [command, args, options] = calls[0];
  assert.equal(command, f.paths.portablePython());
  assert.deepEqual(args.slice(0, 3), ['-I', f.paths.controlPlaneNodeAgent(), 'activate-workspace']);
  assert.ok(args.includes('--confirm-activate'));
  assert.ok(args.includes(workspaceId)); assert.ok(args.includes(workspaceGeneration));
  assert.equal(args.includes('--workspace-path'), false);
  assert.deepEqual(options.env, { PATH: 'safe' });
});

test('activation rejects absent consent, wrong generation, development, duplicate or concurrent registry change', async (t) => {
  let calls = 0;
  const f = fixture(t, async () => { calls++; return { stdout: JSON.stringify(receipt()) }; });
  await assert.rejects(f.service.activateWorkspace({ workspaceId, workspaceGeneration }), { code: 'CONTROL_PLANE_WORKSPACE_ACTIVATION_CONFIRMATION_REQUIRED' });
  await assert.rejects(f.service.activateWorkspace({ workspaceId, workspaceGeneration: `generation_${'5'.repeat(32)}`, confirmActivate: true }), { code: 'CONTROL_PLANE_WORKSPACE_SELECTION_MISMATCH' });
  f.paths.runtimeMode = () => 'development';
  await assert.rejects(f.service.activateWorkspace({ workspaceId, workspaceGeneration, confirmActivate: true }), { code: 'CONTROL_PLANE_WORKSPACE_PACKAGED_REQUIRED' });
  f.paths.runtimeMode = () => 'packaged';
  fs.writeFileSync(f.registry, JSON.stringify({ schema_version: 1, entries: [f.entry, f.entry] }));
  await assert.rejects(f.service.activateWorkspace({ workspaceId, workspaceGeneration, confirmActivate: true }), { code: 'CONTROL_PLANE_WORKSPACE_SELECTION_MISMATCH' });
  assert.equal(calls, 0);
  fs.writeFileSync(f.registry, JSON.stringify({ schema_version: 1, entries: [f.entry] }));
  f.service.runner = async () => { fs.writeFileSync(f.registry, JSON.stringify({ schema_version: 1, entries: [] })); return { stdout: JSON.stringify(receipt()) }; };
  await assert.rejects(f.service.activateWorkspace({ workspaceId, workspaceGeneration, confirmActivate: true }), { code: 'CONTROL_PLANE_WORKSPACE_SELECTION_MISMATCH' });
});

test('activation receipt rejects wrong target, expired authority, malformed identity and extra path/secret fields', () => {
  const valid = receipt();
  assert.equal(parseWorkspaceActivationResult(JSON.stringify(valid), workspaceId, workspaceGeneration).state, 'active');
  for (const mutation of [{ workspace_id: `workspace_${'6'.repeat(32)}` }, { workspace_generation: `generation_${'7'.repeat(32)}` },
    { expires_at_ms: 0 }, { expires_at_ms: '123' }, { replayed: 1 }, { state: 'registered' },
    { binding_id: 'wrong' }, { pilot_decision_id: 'wrong' }, { device_id: 'wrong' }, { workspace_path: 'E:\\private' }, { token: 'private' }]) {
    assert.throws(() => parseWorkspaceActivationResult(JSON.stringify({ ...valid, ...mutation }), workspaceId, workspaceGeneration),
      { code: 'CONTROL_PLANE_WORKSPACE_ACTIVATION_OUTPUT_INVALID' });
  }
  assert.throws(() => parseWorkspaceActivationResult(JSON.stringify(valid) + '\n{}', workspaceId, workspaceGeneration), { code: 'CONTROL_PLANE_WORKSPACE_ACTIVATION_OUTPUT_INVALID' });
});

test('manager activation IPC grants without the global ledger census even while a provider sidecar is live', async () => {
  const source = fs.readFileSync(path.join(__dirname, '../electron/main.js'), 'utf8');
  const start = source.indexOf("  secureHandle('control-plane:activate-workspace'");
  const end = source.indexOf("  secureHandle('control-plane:replace-workspace'", start);
  let handler, invoked = 0, role = 'central_executor', manager = true, authorized = false;
  // Old gate scenario: a live provider sidecar was counted as active_managed_processes = 1
  // plus an unbound residue, and the grant was refused. The grant path must not consult
  // the global ledger census at all, so the fixture fails loudly if the handler still calls it.
  vm.runInNewContext(source.slice(start, end), { secureHandle: (_name, fn) => { handler = fn; }, invokeSafely: fn => fn(),
    assertManagerIpc: () => { if (!manager) throw new Error('untrusted'); }, settings: { load: () => ({ executionRole: role, workspace: 'E:\\native-root' }) },
    canonicalLedgerCensus: async () => { throw new Error('canonicalLedgerCensus must not be called on the grant path'); }, runtimePaths: {}, path,
    orchestrator: { updateAuthorizedRoots: async roots => { assert.equal(roots.length, 1); assert.equal(roots[0], 'E:\\Autocad'); authorized = true; } },
    controlPlaneEnrollment: { registeredWorkspaceRoot: () => 'E:\\Autocad', activateWorkspace: async request => { assert.equal(authorized, true); invoked++; return request; } } });
  const request = { workspaceId, workspaceGeneration, confirmActivate: true };
  await assert.rejects(handler({}, { ...request, confirmActivate: false }), { code: 'CONTROL_PLANE_WORKSPACE_ACTIVATION_CONFIRMATION_REQUIRED' });
  role = 'standalone';
  await assert.rejects(handler({}, request), { code: 'CONTROL_PLANE_WORKSPACE_ROLE_REQUIRED' });
  role = 'central_executor'; manager = false;
  await assert.rejects(handler({}, request), /untrusted/);
  assert.equal(invoked, 0);
  manager = true; await handler({}, request); assert.equal(invoked, 1);
  assert.equal(source.slice(start, end).includes('switchWorkspace'), false);
  const preload = fs.readFileSync(path.join(__dirname, '../electron/preload.js'), 'utf8');
  assert.match(preload, /activateControlPlaneWorkspace:.*control-plane:activate-workspace/);
});

function activationRootFixture({ workspace = 'E:\\native-root', authorizedRoots = [], grantError = null } = {}) {
  const source = fs.readFileSync(path.join(__dirname, '../electron/main.js'), 'utf8');
  const start = source.indexOf("  secureHandle('control-plane:activate-workspace'");
  const end = source.indexOf("  secureHandle('control-plane:replace-workspace'", start);
  const currentSettings = { executionRole: 'central_executor', workspace, authorizedRoots };
  const grantCalls = [];
  let handler, activations = 0;
  const counts = Object.fromEntries(['active_tool_calls', 'active_commands', 'starting_commands', 'active_background_operations',
    'active_managed_processes', 'foreign_heavy_processes', 'active_agent_lanes', 'owned_codex_sidecar_residues'].map(key => [key, 0]));
  vm.runInNewContext(source.slice(start, end), {
    secureHandle: (_name, fn) => { handler = fn; }, invokeSafely: fn => fn(), assertManagerIpc: () => {},
    settings: { load: () => currentSettings }, runtimePaths: {}, path,
    canonicalLedgerCensus: async () => ({ safe: true, counts, lifecycle: {
      blockers: [], unexplained_active_runs: 0, unbound_live_resource_residues: 0
    } }),
    orchestrator: { updateAuthorizedRoots: async roots => {
      grantCalls.push(Array.from(roots));
      if (grantError) throw grantError;
    } },
    controlPlaneEnrollment: {
      registeredWorkspaceRoot: () => 'E:\\Autocad',
      activateWorkspace: async () => { activations++; return { state: 'active' }; }
    }
  });
  return { activate: () => handler({}, { workspaceId, workspaceGeneration, confirmActivate: true }),
    grantCalls, currentSettings, activationCount: () => activations };
}

test('activation reuses the default root and an authorized root even when 32 additional roots exist', async () => {
  const fullRoots = Array.from({ length: 32 }, (_, index) => `E:\\existing-${index}`);
  for (const configuration of [
    { workspace: 'E:\\Autocad', authorizedRoots: fullRoots },
    { authorizedRoots: ['e:\\autocad', ...fullRoots.slice(1)] }
  ]) {
    const f = activationRootFixture(configuration);
    assert.equal((await f.activate()).state, 'active');
    assert.equal(f.activationCount(), 1);
    assert.deepEqual(f.grantCalls, []);
    assert.equal(f.currentSettings.workspace, configuration.workspace || 'E:\\native-root');
  }
});

test('activation refuses a new root at the limit before granting or switching pilot', async () => {
  const authorizedRoots = Array.from({ length: 32 }, (_, index) => `E:\\existing-${index}`);
  const f = activationRootFixture({ authorizedRoots });
  await assert.rejects(f.activate(), { code: 'CONTROL_PLANE_WORKSPACE_ROOT_LIMIT' });
  assert.equal(f.activationCount(), 0);
  assert.deepEqual(f.grantCalls, []);
  assert.equal(f.currentSettings.authorizedRoots, authorizedRoots);
  assert.equal(f.currentSettings.workspace, 'E:\\native-root');
});

test('activation preserves existing roots and requires the native grant to succeed before pilot switch', async () => {
  const authorizedRoots = ['E:\\existing'];
  const f = activationRootFixture({ authorizedRoots, grantError: Object.assign(new Error('Fixture native grant rejected.'), { code: 'FIXTURE_NATIVE_GRANT_REJECTED' }) });
  await assert.rejects(f.activate(), { code: 'FIXTURE_NATIVE_GRANT_REJECTED' });
  assert.equal(f.activationCount(), 0);
  assert.deepEqual(f.grantCalls, [['E:\\existing', 'E:\\Autocad']]);
  assert.deepEqual(authorizedRoots, ['E:\\existing']);
  assert.equal(f.currentSettings.workspace, 'E:\\native-root');
});
