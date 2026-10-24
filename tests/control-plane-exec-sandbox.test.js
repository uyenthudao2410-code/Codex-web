const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');

const {
  ControlPlaneEnrollmentService,
  parsePolicyAuthorityObservation,
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
    server_observed_at_ms: Date.now(),
    runtime_mode: 'packaged'
  };
}

function execObservation(installedFacade = facade, executionMode = 'native_first', nativeArgvPrefixes = []) {
  const prefixes = [['git'], ['node'], ['npm'], ['npx'], ['python'], ['python3'], ['dotnet']];
  return { operation: 'control_plane_exec_policy_observation', execution: 'exec_policy_inspected',
    state: 'enabled', enabled: true, authority_mode: 'standing', expires_at_ms: null,
    workspace_id: workspaceId, workspace_generation: workspaceGeneration, facade_contract: installedFacade,
    policy_sha256: 'b'.repeat(64), allowed_argv_prefix_count: prefixes.length,
    allowed_argv_prefixes_sha256: crypto.createHash('sha256').update(JSON.stringify(prefixes)).digest('hex'),
    max_timeout_ms: 300000, max_output_bytes: 65536, max_concurrent: 2, runtime_mode: 'packaged',
    execution_mode: executionMode, native_argv_prefixes: nativeArgvPrefixes };
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

function execInstallReceipt(executionMode, nativeArgvPrefixes) {
  const payload = execObservation(facade, executionMode, nativeArgvPrefixes);
  delete payload.state;
  delete payload.facade_contract;
  return { ...payload, operation: 'control_plane_exec_policy_installed', execution: 'exec_policy_installed' };
}

function installRunner(item, calls, { workspaces = workspaceList, policyAuthority = authority } = {}) {
  let installed = false;
  let executionMode = 'native_first';
  let nativeArgvPrefixes = [];
  return async (command, args, options) => {
    calls.push({ command, args, options });
    assert.equal(command, item.paths.portablePython(), 'installation must not launch the MXC executor');
    if (args[0] === '-B') {
      return { stdout: JSON.stringify({ probe: 'mxc_wsb_child_process_v1', available: true, reason: null }) };
    }
    const operation = args[2];
    if (operation === 'list-workspaces') return { stdout: JSON.stringify(workspaces()) };
    if (operation === 'inspect-policy-authority') return { stdout: JSON.stringify(policyAuthority()) };
    if (operation === 'inspect-exec-policy') return { stdout: JSON.stringify(installed ? execObservation(facade, executionMode, nativeArgvPrefixes) : {
      operation: 'control_plane_exec_policy_observation', execution: 'exec_policy_inspected',
      runtime_mode: 'packaged', state: 'unavailable', reason: 'CONTROL_PLANE_EXEC_POLICY_MISSING'
    }) };
    if (operation === 'install-exec-policy') {
      installed = true;
      executionMode = args[args.indexOf('--execution-mode') + 1];
      nativeArgvPrefixes = args.flatMap((arg, index) => arg === '--native-argv-prefix' ? [JSON.parse(args[index + 1])] : []);
      return { stdout: JSON.stringify(execInstallReceipt(executionMode, nativeArgvPrefixes)) };
    }
    throw new Error(`unexpected node-agent operation ${operation}`);
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
        assert.ok(args[3].includes(JSON.stringify(fs.realpathSync.native(item.workspaceRoot))), 'probe must use the exact locally registered workspace path');
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
    workspaceId, workspaceGeneration, replaceExisting: true, probeSandbox: true, executionMode: 'isolated'
  }), { code: 'WINDOWS_NPM_SCRIPT_PROCESS_UNAVAILABLE' });
  assert.equal(calls.some(({ args }) => args[2] === 'disable-exec-policy'), false,
    'a failed sandbox probe must preserve any previously active policy');
  assert.equal(calls.some(({ args }) => args[2] === 'install-exec-policy'), false,
    'a standing exec policy must not be installed when a required child process is unavailable');
});

test('permission-only exec installation verifies static WSB authority without launching or claiming cached readiness', async (t) => {
  if (process.platform !== 'win32') return t.skip('Windows Sandbox permission installation is Windows-only');
  const item = fixture(t);
  const originalExistsSync = fs.existsSync;
  const systemRoot = path.join(item.root, 'FakeWindows');
  const sandboxPath = path.join(systemRoot, 'System32', 'WindowsSandbox.exe');
  fs.existsSync = (file, ...args) => path.resolve(String(file)) === sandboxPath
    ? true : originalExistsSync(file, ...args);
  try {
    for (const cached of [false, true]) {
      const calls = [];
      const service = new ControlPlaneEnrollmentService({ paths: item.paths,
        experimentalWindowsSandbox: true,
        environment: { SystemRoot: systemRoot, OPENAI_API_KEY: 'never-forward-this' },
        runner: installRunner(item, calls)
      });
      if (cached) {
        const prior = await service.inspectMxcSandbox({ workspaceRoot: item.workspaceRoot, probeSandbox: true });
        assert.equal(prior.state, 'available');
        calls.length = 0;
      }
      const result = await service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration, executionMode: 'isolated' });
      assert.equal(result.state, 'enabled');
      assert.equal(result.workspace_id, workspaceId);
      assert.equal(result.workspace_generation, workspaceGeneration);
      assert.equal(result.sandbox.state, 'not_checked', 'permission does not imply a running Sandbox');
      assert.equal(result.sandbox.backend, 'windows_sandbox');
      assert.equal(result.sandbox.reason, 'SANDBOX_PROBE_REQUIRED');
      assert.equal(result.sandbox.source_commit, 'cbe1774364ea2ec846f56ab744e43a416f751420');
      assert.equal(calls.some(({ args }) => args[0] === '-B'), false, 'cold and cached installation must never probe a VM');
      assert.deepEqual(calls.map(({ args }) => args[2]), [
        'list-workspaces', 'inspect-policy-authority', 'install-exec-policy', 'inspect-exec-policy'
      ]);
      const installation = calls.find(({ args }) => args[2] === 'install-exec-policy');
      const option = (name) => installation.args[installation.args.indexOf(name) + 1];
      assert.equal(option('--owner-id'), 'owner_default');
      assert.equal(option('--workspace-id'), workspaceId);
      assert.equal(option('--workspace-generation'), workspaceGeneration);
      assert.equal(option('--facade-sha256'), facade.sha256);
      assert.equal(option('--max-timeout-ms'), '300000');
      assert.equal(option('--max-output-bytes'), '65536');
      assert.deepEqual(installation.args.flatMap((arg, index, args) => arg === '--allowed-argv-prefix' ? [JSON.parse(args[index + 1])] : []),
        [['git'], ['node'], ['npm'], ['npx'], ['python'], ['python3'], ['dotnet']]);
      assert.equal(installation.options.env.OPENAI_API_KEY, undefined);
    }
  } finally { fs.existsSync = originalExistsSync; }
});

test('explicit exec installation still runs the exact workspace Sandbox probe', async (t) => {
  if (process.platform !== 'win32') return t.skip('Windows Sandbox selection is Windows-only');
  const item = fixture(t);
  const calls = [];
  const originalExistsSync = fs.existsSync;
  const systemRoot = path.join(item.root, 'FakeWindows');
  const sandboxPath = path.join(systemRoot, 'System32', 'WindowsSandbox.exe');
  fs.existsSync = (file, ...args) => path.resolve(String(file)) === sandboxPath
    ? true : originalExistsSync(file, ...args);
  try {
    const service = new ControlPlaneEnrollmentService({ paths: item.paths, experimentalWindowsSandbox: true,
      environment: { SystemRoot: systemRoot }, runner: installRunner(item, calls) });
    const result = await service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration, probeSandbox: true, executionMode: 'isolated' });
    assert.equal(result.sandbox.state, 'available');
    const probes = calls.filter(({ args }) => args[0] === '-B');
    assert.equal(probes.length, 1);
    assert.match(probes[0].args[3], /probe_mxc_windows_sandbox_child_process/);
    assert.ok(probes[0].args[3].includes(JSON.stringify(fs.realpathSync.native(item.workspaceRoot))));
  } finally { fs.existsSync = originalExistsSync; }
});

test('permission-only exec installation rejects invalid backend provenance and missing Windows prerequisites without launching', async (t) => {
  if (process.platform !== 'win32') return t.skip('Windows Sandbox selection is Windows-only');
  const item = fixture(t);
  const originalExistsSync = fs.existsSync;
  const originalReadFileSync = fs.readFileSync;
  const systemRoot = path.join(item.root, 'FakeWindows');
  const sandboxPath = path.join(systemRoot, 'System32', 'WindowsSandbox.exe');
  const candidateDirectory = path.join(item.paths.resourcesRoot(), 'tools', 'mxc-windows-sandbox');
  const candidateBinary = path.join(candidateDirectory, 'wxc-exec.exe');
  const baseBinary = path.join(item.paths.resourcesRoot(), 'tools', 'wxc-exec.exe');
  const provenanceFile = path.join(candidateDirectory, 'mxc-windows-sandbox.provenance.json');
  try {
    for (const [scenario, code] of [
      ['missing-os-feature', 'WINDOWS_SANDBOX_REQUIRED'],
      ['backend-disabled', 'WINDOWS_SANDBOX_REQUIRED'],
      ['invalid-provenance', 'MXC_WSB_PROVENANCE_INVALID'],
      ['modified-candidate', 'MXC_WSB_BINARY_HASH_MISMATCH'],
      ['modified-base-executor', 'MXC_EXECUTOR_HASH_MISMATCH']
    ]) {
      fs.existsSync = (file, ...args) => path.resolve(String(file)) === sandboxPath
        ? scenario !== 'missing-os-feature' : originalExistsSync(file, ...args);
      fs.readFileSync = (file, ...args) => {
        const normalized = path.resolve(String(file));
        if ((scenario === 'modified-candidate' && normalized === candidateBinary)
          || (scenario === 'modified-base-executor' && normalized === baseBinary)) return Buffer.from('modified executor');
        if (scenario === 'invalid-provenance' && normalized === provenanceFile) {
          const provenance = JSON.parse(originalReadFileSync(file, 'utf8'));
          return JSON.stringify({ ...provenance, source_commit: 'f'.repeat(40) });
        }
        return originalReadFileSync(file, ...args);
      };
      const calls = [];
      const service = new ControlPlaneEnrollmentService({ paths: item.paths,
        experimentalWindowsSandbox: scenario !== 'backend-disabled', environment: { SystemRoot: systemRoot },
        runner: installRunner(item, calls) });
      await assert.rejects(service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration, replaceExisting: true, executionMode: 'isolated' }), { code }, scenario);
      assert.equal(calls.some(({ args }) => ['install-exec-policy', 'disable-exec-policy'].includes(args[2]) || args[0] === '-B'), false, scenario);
    }
  } finally { fs.existsSync = originalExistsSync; fs.readFileSync = originalReadFileSync; }
});

test('exec installation rejects stale or incorrect registered authority before changing permission', async (t) => {
  const item = fixture(t);
  for (const [scenario, code] of [
    ['wrong-generation', 'CONTROL_PLANE_WORKSPACE_SELECTION_MISMATCH'],
    ['wrong-authority-target', 'CONTROL_PLANE_POLICY_AUTHORITY_OUTPUT_INVALID'],
    ['invalid-owner', 'CONTROL_PLANE_POLICY_AUTHORITY_OUTPUT_INVALID'],
    ['stale', 'CONTROL_PLANE_POLICY_AUTHORITY_STALE'],
    ['future', 'CONTROL_PLANE_POLICY_AUTHORITY_STALE'],
    ['not-admitted', 'CONTROL_PLANE_EXEC_NOT_ADMITTED']
  ]) {
    const calls = [];
    const service = new ControlPlaneEnrollmentService({ paths: item.paths,
      runner: installRunner(item, calls, {
        workspaces: () => scenario === 'wrong-generation' ? { workspaces: [{ ...workspaceList().workspaces[0], workspace_generation: 'generation_' + 'f'.repeat(32) }] } : workspaceList(),
        policyAuthority: () => ({ ...authority(),
          ...(scenario === 'wrong-authority-target' ? { workspace_generation: 'generation_' + 'f'.repeat(32) } : {}),
          ...(scenario === 'invalid-owner' ? { owner_id: '' } : {}),
          ...(scenario === 'stale' ? { observed_at_ms: Date.now() - 60_000 } : {}),
          ...(scenario === 'future' ? { observed_at_ms: Date.now() + 60_000 } : {}),
          ...(scenario === 'not-admitted' ? { exec_enabled: false } : {})
        })
      })
    });
    await assert.rejects(service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration, replaceExisting: true }), { code }, scenario);
    assert.equal(calls.some(({ args }) => ['install-exec-policy', 'disable-exec-policy'].includes(args[2]) || args[0] === '-B'), false, scenario);
  }
  const service = new ControlPlaneEnrollmentService({ paths: item.paths });
  await assert.rejects(service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration, probeSandbox: 'true' }), {
    code: 'CONTROL_PLANE_EXEC_POLICY_REQUEST_INVALID'
  });
});

test('authenticated authority uses fresh node time while retaining separate server clock provenance', async (t) => {
  const item = fixture(t);
  for (const offset of [-3_600_000, 3_600_000]) {
    const payload = { ...authority(), server_observed_at_ms: Date.now() + offset };
    const service = new ControlPlaneEnrollmentService({ paths: item.paths, runner: async (_command, args) => {
      assert.equal(args[2], 'inspect-policy-authority');
      return { stdout: JSON.stringify(payload) };
    } });
    const observed = await service.inspectCurrentPolicyAuthority({ workspace_id: workspaceId, workspace_generation: workspaceGeneration });
    assert.equal(observed.observed_at_ms, payload.observed_at_ms);
    assert.equal(observed.server_observed_at_ms, payload.server_observed_at_ms);
  }
  for (const invalid of [null, true, 0, -1, '1700000000000', Number.MAX_SAFE_INTEGER + 1]) {
    assert.throws(() => parsePolicyAuthorityObservation(JSON.stringify({ ...authority(), server_observed_at_ms: invalid }),
      workspaceId, workspaceGeneration), { code: 'CONTROL_PLANE_POLICY_AUTHORITY_OUTPUT_INVALID' });
  }
  const missing = authority();
  delete missing.server_observed_at_ms;
  assert.throws(() => parsePolicyAuthorityObservation(JSON.stringify(missing), workspaceId, workspaceGeneration), {
    code: 'CONTROL_PLANE_POLICY_AUTHORITY_OUTPUT_INVALID'
  });
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
        assert.ok(args[3].includes(JSON.stringify(fs.realpathSync.native(item.workspaceRoot))));
        return { stdout: JSON.stringify({
          probe: 'mxc_nested_process_v1', available: false,
          reason: 'WINDOWS_NPM_SCRIPT_PROCESS_UNAVAILABLE'
        }) + '\n' };
      }
      throw new Error('development read-only inspection must not invoke the packaged node-agent');
    }
  });

  const observation = await service.inspectStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration, probeSandbox: true, executionMode: 'isolated' });
  assert.equal(observation.policy.state, 'unavailable');
  assert.equal(observation.sandbox.state, 'unavailable');
  assert.equal(observation.sandbox.reason, 'WINDOWS_NPM_SCRIPT_PROCESS_UNAVAILABLE');
  assert.ok(calls.some(({ command }) => command === mxc));
  assert.ok(calls.some(({ command }) => command === python));
  await assert.rejects(service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration }), {
    code: 'CONTROL_PLANE_EXEC_POLICY_PACKAGED_REQUIRED'
  });
});

test('exec inspection keeps the installed facade distinct from fresh authenticated authority', async (t) => {
  const item = fixture(t);
  for (const installed of [facade, { ...facade, sha256: 'f'.repeat(64) }]) {
    const commands = [];
    const service = new ControlPlaneEnrollmentService({ paths: item.paths,
      runner: async (_command, args) => {
        commands.push(args[2]);
        return { stdout: JSON.stringify(args[2] === 'inspect-policy-authority' ? authority() : execObservation(installed)) };
      }
    });
    service.inspectMxcSandbox = async () => ({ state: 'available' });
    const result = await service.inspectStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration });
    assert.deepEqual(result.policy.facade_contract, installed);
    assert.deepEqual(result.policy.current_facade_contract, facade);
    assert.ok(Number.isSafeInteger(result.policy.authority_observed_at_ms));
    assert.deepEqual(commands, ['inspect-exec-policy', 'inspect-policy-authority']);
  }
});

test('default exec inspection reads installed permission and fresh authority without starting a sandbox', async (t) => {
  const item = fixture(t);
  const commands = [];
  const service = new ControlPlaneEnrollmentService({ paths: item.paths,
    runner: async (command, args) => {
      assert.equal(command, item.paths.portablePython(), 'a status read must not invoke the MXC executor');
      assert.notEqual(args[0], '-B', 'a status read must not invoke a nested-process Sandbox probe');
      commands.push(args[2]);
      return { stdout: JSON.stringify(args[2] === 'inspect-policy-authority' ? authority() : execObservation()) };
    }
  });
  const result = await service.inspectStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration });
  assert.equal(result.policy.state, 'enabled');
  assert.deepEqual(result.policy.current_facade_contract, facade);
  assert.equal(result.sandbox.state, 'not_checked');
  assert.equal(result.sandbox.reason, 'NATIVE_CAPABILITY_NOT_CHECKED');
  assert.deepEqual(commands, ['inspect-exec-policy', 'inspect-policy-authority']);
});

function nativeInstallRunner(item, calls, probe = sandboxProbe()) {
  const install = installRunner(item, calls);
  const executor = path.join(item.paths.resourcesRoot(), 'tools', 'wxc-exec.exe');
  return async (command, args, options) => {
    if (command !== executor) return install(command, args, options);
    calls.push({ command, args, options });
    assert.deepEqual(args, ['--experimental', '--probe'], 'native setup only reads ProcessContainer capability');
    return { stdout: JSON.stringify(probe) };
  };
}

test('native-first setup requires pinned ProcessContainer capability and no Windows Sandbox feature or VM probe', async (t) => {
  const item = fixture(t), calls = [];
  const service = new ControlPlaneEnrollmentService({ paths: item.paths,
    experimentalWindowsSandbox: false,
    environment: { SystemRoot: path.join(item.root, 'NoWindowsSandbox'), OPENAI_API_KEY: 'never-forward-this' },
    runner: nativeInstallRunner(item, calls) });
  const receipt = await service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration });
  assert.equal(receipt.execution_mode, 'native_first');
  assert.deepEqual(receipt.native_argv_prefixes, [], 'workspace consent alone cannot authorize native project code');
  assert.equal(receipt.sandbox.backend, 'process_container');
  assert.equal(receipt.sandbox.capability_verified, true);
  assert.equal(receipt.sandbox.execution_verified, false, 'capability is not a completed command Job');
  assert.equal(calls.filter(({ args }) => args[1] === '--probe').length, 1);
  assert.equal(calls.some(({ args }) => args[0] === '-B'), false, 'no child process or VM probe');
  assert.ok(calls.every(({ options }) => options.env.OPENAI_API_KEY === undefined));
  const installation = calls.find(({ args }) => args[2] === 'install-exec-policy');
  assert.equal(installation.args[installation.args.indexOf('--execution-mode') + 1], 'native_first');
  assert.equal(installation.args.includes('--native-argv-prefix'), false);
  calls.length = 0;
  const observation = await service.inspectStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration });
  assert.equal(observation.policy.execution_mode, 'native_first');
  assert.equal(observation.sandbox.capability_verified, true);
  assert.equal(calls.some(({ args }) => args[1] === '--probe' || args[0] === '-B'), false, 'metadata inspection cannot launch a runner');
});

test('native-only setup preserves explicitly approved build prefixes in the exact installed policy', async (t) => {
  const item = fixture(t), calls = [];
  const service = new ControlPlaneEnrollmentService({ paths: item.paths, runner: nativeInstallRunner(item, calls) });
  const prefixes = [['dotnet', 'build'], ['npm', 'test']];
  const receipt = await service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration,
    executionMode: 'native_only', nativeArgvPrefixes: prefixes });
  assert.equal(receipt.execution_mode, 'native_only');
  assert.deepEqual(receipt.native_argv_prefixes, prefixes);
  const installation = calls.find(({ args }) => args[2] === 'install-exec-policy');
  assert.deepEqual(installation.args.flatMap((arg, index, args) => arg === '--native-argv-prefix' ? [JSON.parse(args[index + 1])] : []), prefixes);
});

test('local setup installs and observes exact standing authority without any runner probe', async (t) => {
  const item = fixture(t), calls = [];
  const service = new ControlPlaneEnrollmentService({ paths: item.paths,
    getExecutionMode: () => 'local', runner: installRunner(item, calls) });
  service.inspectMxcSandbox = async () => { throw new Error('local setup must not probe any container or VM'); };
  const receipt = await service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration,
    executionMode: 'isolated', probeSandbox: true });
  assert.deepEqual(receipt.sandbox, { state: 'not_required', backend: 'host_user', reason: 'OPERATOR_LOCAL_EXECUTION' });
  assert.equal(receipt.execution_mode, 'isolated', 'retain the policy selection for a later sandboxed runtime');
  assert.deepEqual(calls.map(({ args }) => args[2]), [
    'list-workspaces', 'inspect-policy-authority', 'install-exec-policy', 'inspect-exec-policy'
  ]);
  calls.length = 0;
  const observed = await service.inspectStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration, probeSandbox: true });
  assert.equal(observed.policy.state, 'enabled');
  assert.deepEqual(observed.policy.current_facade_contract, facade);
  assert.deepEqual(observed.sandbox, receipt.sandbox);
  assert.deepEqual(calls.map(({ args }) => args[2]), ['inspect-exec-policy', 'inspect-policy-authority']);
});

test('local setup retains current target, authority, packaged and receipt gates', async (t) => {
  const item = fixture(t);
  for (const [scenario, code] of [
    ['wrong-generation', 'CONTROL_PLANE_WORKSPACE_SELECTION_MISMATCH'],
    ['stale', 'CONTROL_PLANE_POLICY_AUTHORITY_STALE'],
    ['not-admitted', 'CONTROL_PLANE_EXEC_NOT_ADMITTED'],
    ['changed-receipt', 'CONTROL_PLANE_EXEC_POLICY_OUTPUT_INVALID']
  ]) {
    const calls = [];
    const install = installRunner(item, calls, {
      workspaces: () => scenario === 'wrong-generation' ? { workspaces: [{ ...workspaceList().workspaces[0],
        workspace_generation: 'generation_' + 'f'.repeat(32) }] } : workspaceList(),
      policyAuthority: () => ({ ...authority(),
        ...(scenario === 'stale' ? { observed_at_ms: Date.now() - 60_000 } : {}),
        ...(scenario === 'not-admitted' ? { exec_enabled: false } : {}) })
    });
    const service = new ControlPlaneEnrollmentService({ paths: item.paths, getExecutionMode: () => 'local',
      runner: async (command, args, options) => {
        const result = await install(command, args, options);
        return scenario === 'changed-receipt' && args[2] === 'install-exec-policy'
          ? { stdout: JSON.stringify({ ...JSON.parse(result.stdout), execution_mode: 'isolated' }) } : result;
      } });
    service.inspectMxcSandbox = async () => { throw new Error('local setup must not probe a runner'); };
    await assert.rejects(service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration }), { code }, scenario);
    if (scenario !== 'changed-receipt') assert.equal(calls.some(({ args }) => args[2] === 'install-exec-policy'), false);
  }
  const development = fixture(t, 'development');
  const service = new ControlPlaneEnrollmentService({ paths: development.paths, getExecutionMode: () => 'local' });
  await assert.rejects(service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration }), {
    code: 'CONTROL_PLANE_EXEC_POLICY_PACKAGED_REQUIRED'
  });
});

test('execution mode comes from current trusted settings and invalid modes cannot bypass setup', async (t) => {
  const item = fixture(t), calls = [];
  let executionMode = 'local';
  const service = new ControlPlaneEnrollmentService({ paths: item.paths, getExecutionMode: () => executionMode,
    runner: async (_command, args) => ({ stdout: JSON.stringify(args[2] === 'inspect-policy-authority' ? authority() : execObservation()) }) });
  service.inspectMxcSandbox = async () => { calls.push('sandbox-probe'); return { state: 'not_checked' }; };
  assert.equal((await service.inspectStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration })).sandbox.state, 'not_required');
  assert.deepEqual(calls, []);
  executionMode = 'sandboxed';
  assert.equal((await service.inspectStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration })).sandbox.state, 'not_checked');
  assert.deepEqual(calls, ['sandbox-probe']);
  executionMode = 'invalid';
  await assert.rejects(service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration }), {
    code: 'CONTROL_PLANE_EXECUTION_MODE_INVALID'
  });
});

test('native setup rejects unsupported capability, modified binary, and invalid selection before permission mutation', async (t) => {
  const item = fixture(t), calls = [];
  const service = new ControlPlaneEnrollmentService({ paths: item.paths,
    runner: nativeInstallRunner(item, calls, { ...sandboxProbe(), needsDaclAugmentation: true }) });
  await assert.rejects(service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration }), { code: 'WINDOWS_BASE_CONTAINER_UNAVAILABLE' });
  assert.equal(calls.some(({ args }) => ['disable-exec-policy', 'install-exec-policy'].includes(args[2])), false);
  calls.length = 0;
  for (const request of [{ executionMode: 'unsafe' }, { nativeArgvPrefixes: [['powershell', '-Command']] },
    { nativeArgvPrefixes: [['node', '--version\n']] }]) {
    await assert.rejects(service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration, ...request }), { code: 'CONTROL_PLANE_EXEC_POLICY_REQUEST_INVALID' });
  }
  assert.deepEqual(calls, [], 'invalid selection must fail before even authority reads');
  const originalRead = fs.readFileSync;
  const executor = path.resolve(item.paths.resourcesRoot(), 'tools', 'wxc-exec.exe');
  fs.readFileSync = (file, ...args) => path.resolve(String(file)) === executor ? Buffer.from('modified executor') : originalRead(file, ...args);
  try {
    await assert.rejects(service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration }), { code: 'MXC_EXECUTOR_HASH_MISMATCH' });
    assert.equal(calls.some(({ args }) => args[1] === '--probe' || ['disable-exec-policy', 'install-exec-policy'].includes(args[2])), false);
  } finally { fs.readFileSync = originalRead; }
});

test('native policy installation rejects a receipt that silently changes the selected execution mode', async (t) => {
  const item = fixture(t), calls = [];
  const runner = nativeInstallRunner(item, calls);
  const service = new ControlPlaneEnrollmentService({ paths: item.paths, runner: async (command, args, options) => {
    const result = await runner(command, args, options);
    return args[2] === 'install-exec-policy'
      ? { stdout: JSON.stringify({ ...JSON.parse(result.stdout), execution_mode: 'isolated' }) } : result;
  } });
  await assert.rejects(service.installStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration }), { code: 'CONTROL_PLANE_EXEC_POLICY_OUTPUT_INVALID' });
});

test('exec inspection cannot reuse missing contract, wrong target, or unknown/stale server authority', async (t) => {
  const item = fixture(t);
  for (const scenario of ['missing', 'invalid', 'wrong-target', 'unavailable', 'stale', 'disabled', 'no-exec-binding']) {
    const service = new ControlPlaneEnrollmentService({ paths: item.paths, runner: async (_command, args) => {
      if (args[2] === 'inspect-policy-authority') {
        if (scenario === 'unavailable') throw Object.assign(new Error('not returned'), { code: 'AUTHORITY_OFFLINE' });
        return { stdout: JSON.stringify({ ...authority(), ...(scenario === 'stale' ? { observed_at_ms: Date.now() - 60_000 } : {}),
          ...(scenario === 'disabled' ? { exec_enabled: false } : {}), ...(scenario === 'no-exec-binding' ? { exec_binding_count: 0 } : {}) }) };
      }
      const payload = execObservation();
      if (scenario === 'missing') delete payload.facade_contract;
      if (scenario === 'invalid') payload.facade_contract = { ...facade, sha256: 'invalid' };
      if (scenario === 'wrong-target') payload.workspace_generation = 'generation_' + 'f'.repeat(32);
      return { stdout: JSON.stringify(payload) };
    } });
    service.inspectMxcSandbox = async () => ({ state: 'available' });
    const result = await service.inspectStandingWorkspaceExecPolicy({ workspaceId, workspaceGeneration });
    assert.ok(!result.policy.current_facade_contract, scenario);
    assert.equal(result.policy.authority_observed_at_ms ?? null, null, scenario);
    if (['disabled', 'no-exec-binding'].includes(scenario)) assert.equal(result.policy.reason, 'CONTROL_PLANE_EXEC_NOT_ADMITTED');
  }
});

test('packaged WSB candidate probes the exact workspace through state-aware lifecycle', async (t) => {
  if (process.platform !== 'win32') return t.skip('Windows Sandbox selection is Windows-only');
  const item = fixture(t, 'packaged');
  const python = item.paths.portablePython();
  const calls = [];
  let releaseProbe;
  const probeGate = new Promise((resolve) => { releaseProbe = resolve; });
  let probeAvailable = true;
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
        assert.ok(args[3].includes(JSON.stringify(fs.realpathSync.native(item.workspaceRoot))));
        assert.equal(options.timeoutMs, 360_000);
        await probeGate;
        return { stdout: JSON.stringify({
          probe: 'mxc_wsb_child_process_v1', available: probeAvailable,
          reason: probeAvailable ? null : 'SANDBOX_BUSY'
        }) + '\n' };
      }
    });
    const statusOnly = await service.inspectMxcSandbox({ workspaceRoot: item.workspaceRoot, probeSandbox: false });
    assert.equal(statusOnly.state, 'not_checked');
    assert.equal(calls.length, 0, 'reading WSB eligibility never provisions or starts a VM');
    const firstProbe = service.inspectMxcSandbox({ workspaceRoot: item.workspaceRoot });
    const secondProbe = service.inspectMxcSandbox({ workspaceRoot: item.workspaceRoot });
    assert.equal(calls.length, 1, 'concurrent explicit probes share one owned probe');
    releaseProbe();
    const [observation, concurrent] = await Promise.all([firstProbe, secondProbe]);
    assert.deepEqual(concurrent, observation);
    assert.equal(service.mxcSandboxProbesInFlight.size, 0);
    assert.equal(observation.state, 'available');
    assert.equal(observation.backend, 'windows_sandbox');
    assert.equal(observation.child_process_spawn, true);
    assert.equal(observation.source_commit, 'cbe1774364ea2ec846f56ab744e43a416f751420');
    const cached = await service.inspectMxcSandbox({ workspaceRoot: item.workspaceRoot, probeSandbox: false });
    assert.equal(cached.state, 'available');
    assert.equal(calls.length, 1, 'WSB candidate does not fall back to ProcessContainer probe');
    for (const entry of service.mxcSandboxProbeCache.values()) entry.expires_at_ms = Date.now() - 1;
    const expired = await service.inspectMxcSandbox({ workspaceRoot: item.workspaceRoot, probeSandbox: false });
    assert.equal(expired.state, 'not_checked');
    assert.equal(calls.length, 1, 'expired evidence does not implicitly reopen Sandbox');
    probeAvailable = false;
    const failed = await service.inspectMxcSandbox({ workspaceRoot: item.workspaceRoot });
    assert.equal(failed.state, 'unavailable');
    const afterFailure = await service.inspectMxcSandbox({ workspaceRoot: item.workspaceRoot, probeSandbox: false });
    assert.equal(afterFailure.state, 'not_checked', 'failed probes are never accepted as readiness evidence');
    assert.equal(calls.length, 2);
    probeAvailable = true;
    const retried = await service.inspectMxcSandbox({ workspaceRoot: item.workspaceRoot });
    assert.equal(retried.state, 'available');
    assert.equal(calls.length, 3, 'a failed probe releases single-flight ownership for an explicit retry');
    const otherRoot = path.join(item.root, 'other-project');
    fs.mkdirSync(otherRoot);
    const other = await service.inspectMxcSandbox({ workspaceRoot: otherRoot, probeSandbox: false });
    assert.equal(other.state, 'not_checked', 'an exact-root receipt never grants readiness to another root');
    const originalReadFileSync = fs.readFileSync;
    const sandboxExecutor = path.join(item.paths.resourcesRoot(), 'tools', 'mxc-windows-sandbox', 'wxc-exec.exe');
    fs.readFileSync = (file, ...args) => String(file).toLowerCase() === sandboxExecutor.toLowerCase()
      ? Buffer.from('modified candidate') : originalReadFileSync(file, ...args);
    try {
      const changedCandidate = await service.inspectMxcSandbox({ workspaceRoot: item.workspaceRoot, probeSandbox: false });
      assert.equal(changedCandidate.state, 'unavailable', 'a receipt cannot survive changed candidate binary hashes');
    } finally { fs.readFileSync = originalReadFileSync; }
    assert.equal(calls.length, 3, 'different-root and invalid-candidate status reads never launch another probe');
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
