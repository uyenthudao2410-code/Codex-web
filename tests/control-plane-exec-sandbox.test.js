const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  ControlPlaneEnrollmentService,
  parseMxcWindowsSandboxChildProcessProbe
} = require('../electron/services/controlPlaneEnrollment');

const workspaceId = 'workspace_0123456789abcdef0123456789abcdef';
const workspaceGeneration = 'generation_abcdef0123456789abcdef0123456789';
const facade = { schema_version: 20, profile: 'control-plane-private-tunnel-service-v1', sha256: 'a'.repeat(64) };

function sandboxProbe() {
  return {
    tier: 'base-container',
    needsDaclAugmentation: false,
    warnings: [],
    probes: { baseContainerApiPresent: true, baseContainerSupportsDenyPaths: true }
  };
}

function authority() {
  return {
    operation: 'control_plane_policy_authority_observation',
    owner_id: 'owner_default',
    workspace_id: workspaceId,
    workspace_generation: workspaceGeneration,
    facade_contract: facade,
    binding_count: 1,
    standing_write_enabled: false,
    exec_enabled: true,
    exec_binding_count: 1,
    observed_at_ms: Date.now(),
    runtime_mode: 'packaged'
  };
}

function workspaceList() {
  return {
    workspaces: [{
      workspace_id: workspaceId,
      workspace_generation: workspaceGeneration,
      display_name: 'selected-project',
      capabilities: { read: true, write: false, exec: true }
    }]
  };
}

function fixture(t, runtimeMode = 'packaged') {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'control-plane-exec-sandbox-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const python = path.join(root, 'python.exe');
  const agent = path.join(root, 'node_agent.py');
  const workspaceRoot = path.join(root, 'selected-project');
  const registry = path.join(root, 'control-plane-workspaces.json');
  fs.writeFileSync(python, 'fixture');
  fs.writeFileSync(agent, 'fixture');
  fs.mkdirSync(workspaceRoot);
  fs.writeFileSync(registry, JSON.stringify({
    schema_version: 1,
    entries: [{
      workspace_id: workspaceId,
      workspace_generation: workspaceGeneration,
      canonical_path: workspaceRoot
    }]
  }));
  const resourcesRoot = path.resolve(__dirname, '..', 'resources');
  const paths = {
    runtimeMode: () => runtimeMode,
    portablePython: () => python,
    controlPlaneNodeAgent: () => agent,
    controlPlaneNodeConfigFile: () => path.join(root, 'control-plane-node.json'),
    controlPlaneWorkspaceRegistryFile: () => registry,
    resourcesRoot: () => resourcesRoot,
    appRoot: () => root,
    executablePath: () => path.join(root, 'Coding Tools MCP.exe')
  };
  return { root, paths, workspaceRoot };
}

test('exec policy installation fails closed when nested processes fail on the selected workspace volume', async (t) => {
  const item = fixture(t);
  const calls = [];
  const python = item.paths.portablePython();
  const mxc = path.join(item.paths.resourcesRoot(), 'tools', 'wxc-exec.exe');
  const service = new ControlPlaneEnrollmentService({
    paths: item.paths,
    environment: { PATH: 'C:\\Windows\\System32', OPENAI_API_KEY: 'never-forward-this' },
    runner: async (command, args, options) => {
      calls.push({ command, args, options });
      if (command === mxc) return { stdout: JSON.stringify(sandboxProbe()) };
      if (command !== python) throw new Error(`unexpected command ${command}`);
      if (args[2] === 'list-workspaces') return { stdout: JSON.stringify(workspaceList()) };
      if (args[2] === 'inspect-policy-authority') return { stdout: JSON.stringify(authority()) };
      if (args[2] === 'inspect-exec-policy') {
        return { stdout: JSON.stringify({
          operation: 'control_plane_exec_policy_observation',
          execution: 'exec_policy_inspected', runtime_mode: 'packaged',
          state: 'unavailable', reason: 'CONTROL_PLANE_EXEC_POLICY_MISSING'
        }) };
      }
      if (args[0] === '-B' && args[1] === '-I' && args[2] === '-c') {
        assert.match(args[3], /probe_mxc_child_process/);
        assert.ok(args[3].includes(JSON.stringify(item.workspaceRoot)), 'probe must use the exact locally registered workspace path');
        assert.equal(args[3].includes('never-forward-this'), false);
        return { stdout: JSON.stringify({
          probe: 'mxc_nested_process_v1',
          available: false,
          reason: 'WINDOWS_NPM_SCRIPT_PROCESS_UNAVAILABLE'
        }) + '\n' };
      }
      throw new Error(`unexpected node-agent operation ${args[2] || args[1]}`);
    }
  });

  await assert.rejects(service.installStandingWorkspaceExecPolicy({
    workspaceId, workspaceGeneration, replaceExisting: true
  }), { code: 'WINDOWS_NPM_SCRIPT_PROCESS_UNAVAILABLE' });
  assert.equal(calls.some(({ args }) => args[2] === 'disable-exec-policy'), false,
    'a failed sandbox probe must preserve any previously active policy');
  assert.equal(calls.some(({ args }) => args[2] === 'install-exec-policy'), false,
    'a standing exec policy must not be installed when a required child process is unavailable');
});

test('development runtime can inspect the exact workspace sandbox but cannot install standing authority', async (t) => {
  const item = fixture(t, 'development');
  const calls = [];
  const python = item.paths.portablePython();
  const mxc = path.join(item.paths.resourcesRoot(), 'tools', 'wxc-exec.exe');
  const service = new ControlPlaneEnrollmentService({
    paths: item.paths,
    environment: { PATH: 'C:\\Windows\\System32' },
    runner: async (command, args) => {
      calls.push({ command, args });
      if (command === mxc) return { stdout: JSON.stringify(sandboxProbe()) };
      if (command === python && args[0] === '-B' && args[1] === '-I' && args[2] === '-c') {
        assert.ok(args[3].includes(JSON.stringify(item.workspaceRoot)));
        return { stdout: JSON.stringify({
          probe: 'mxc_nested_process_v1', available: false,
          reason: 'WINDOWS_NPM_SCRIPT_PROCESS_UNAVAILABLE'
        }) + '\n' };
      }
      throw new Error('development read-only inspection must not invoke the packaged node-agent');
    }
  });

  const observation = await service.inspectStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration });
  assert.equal(observation.policy.state, 'unavailable');
  assert.equal(observation.sandbox.state, 'unavailable');
  assert.equal(observation.sandbox.reason, 'WINDOWS_NPM_SCRIPT_PROCESS_UNAVAILABLE');
  assert.ok(calls.some(({ command }) => command === mxc));
  assert.ok(calls.some(({ command }) => command === python));
  await assert.rejects(service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration }), {
    code: 'CONTROL_PLANE_EXEC_POLICY_PACKAGED_REQUIRED'
  });
});

test('packaged WSB candidate probes the exact workspace through state-aware lifecycle', async (t) => {
  if (process.platform !== 'win32') return t.skip('Windows Sandbox selection is Windows-only');
  const item = fixture(t, 'packaged');
  const python = item.paths.portablePython();
  const calls = [];
  const originalExistsSync = fs.existsSync;
  const sandboxPath = path.resolve('C:\\FakeWindows\\System32\\WindowsSandbox.exe');
  fs.existsSync = (value, ...args) => path.resolve(String(value)) === sandboxPath
    ? true
    : originalExistsSync(value, ...args);
  try {
    const service = new ControlPlaneEnrollmentService({
      paths: item.paths,
      environment: { SystemRoot: 'C:\\FakeWindows', PATH: 'C:\\Windows\\System32' },
      experimentalWindowsSandbox: true,
      runner: async (command, args, options) => {
        calls.push({ command, args, options });
        assert.equal(command, python, 'WSB inspection uses the packaged Python runtime directly');
        assert.deepEqual(args.slice(0, 3), ['-B', '-I', '-c']);
        assert.match(args[3], /probe_mxc_windows_sandbox_child_process/);
        assert.ok(args[3].includes(JSON.stringify(item.workspaceRoot)));
        assert.equal(options.timeoutMs, 360_000);
        return { stdout: JSON.stringify({
          probe: 'mxc_wsb_child_process_v1', available: true, reason: null
        }) + '\n' };
      }
    });
    const observation = await service.inspectMxcSandbox({ workspaceRoot: item.workspaceRoot });
    assert.equal(observation.state, 'available');
    assert.equal(observation.backend, 'windows_sandbox');
    assert.equal(observation.child_process_spawn, true);
    assert.equal(observation.source_commit, 'cbe1774364ea2ec846f56ab744e43a416f751420');
    const cached = await service.inspectMxcSandbox({ workspaceRoot: item.workspaceRoot });
    assert.equal(cached.state, 'available');
    assert.equal(calls.length, 1, 'WSB candidate does not fall back to ProcessContainer probe');
  } finally {
    fs.existsSync = originalExistsSync;
  }
});

test('bounded WSB launcher diagnostics survive the Python-to-Electron probe contract', () => {
  for (const reason of [
    'CHILD_PROCESS_PROBE_OUTPUT_UNPARSEABLE_EXIT_1',
    'SANDBOX_STATE_PHASE_FAILED_START_BACKEND_ERROR'
  ]) {
    assert.deepEqual(parseMxcWindowsSandboxChildProcessProbe(JSON.stringify({
      probe: 'mxc_wsb_child_process_v1',
      available: false,
      reason
    })), { available: false, reason });
  }
});
