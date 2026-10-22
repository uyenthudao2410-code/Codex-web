const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'renderer', 'app.js'), 'utf8');
const plain = (value) => JSON.parse(JSON.stringify(value));

function fixture({ write = true, exec = true, accepted = true, executionMode = 'sandboxed' } = {}) {
  const workspace = {
    workspace_id: 'workspace-selected', workspace_generation: 'generation-current',
    display_name: 'Tools-Codex-web', capabilities: { read: true, write, exec }
  };
  const state = {
    snapshot: {
      settings: { executionRole: 'central_executor', executionMode, workspace: 'E:\\legacy-root', controlPlaneServerUrl: 'https://control.example.test/' },
      device: { device_id: 'device-current', display_name: 'Máy hiện tại' },
      status: { signalStale: false, telemetryAvailable: true }
    },
    centralWorkspaces: [workspace], centralWorkspaceSelection: null,
    centralWorkspaceCandidate: 'E:\\old-picker-root', centralWorkspacePreset: 'read',
    centralWorkspaceCapabilities: { read: true, write: false, exec: false },
    centralWorkspaceBusy: false, centralPermissionBusy: false,
    centralWorkspaceInventoryRequest: 0, centralWorkspaceInventoryStatus: 'loaded',
    centralPolicyBusy: false, centralExecBusy: false, centralExecObservations: {},
    centralExecutionMode: 'native_first',
    setupContinuation: null, setupContinuationBusy: false, setupContinuationTimer: null,
    setupContinuationMessage: '', setupStartBusy: false,
    centralEnrollmentStatus: { fresh: true, state: 'approved' }, centralEnrollmentBusy: false,
    centralAuthorityStatus: {
      fresh: true, state: 'active',
      targets: [{ workspace_id: workspace.workspace_id,
        workspace_generation: workspace.workspace_generation, dispatch_state: 'dispatchable',
        capabilities: { read: true, write, exec } }]
    }
  };
  const calls = [];
  const confirmations = [];
  const messages = [];
  const elements = new Map();
  const facadeContract = {
    schema_version: 32, profile: 'control-plane-private-tunnel-service-v1', sha256: 'f'.repeat(64)
  };
  const policy = (hash, target = state.centralWorkspaceReceipt || workspace) => ({
    state: 'enabled', workspace_id: target.workspace_id,
    workspace_generation: target.workspace_generation, policy_sha256: hash,
    facade_contract: { ...facadeContract }, current_facade_contract: { ...facadeContract },
    authority_observed_at_ms: Date.now()
  });
  const hashes = { read: 'a'.repeat(64), write: 'b'.repeat(64), metadata: 'c'.repeat(64), exec: 'd'.repeat(64) };
  let observedFiles = { file_read: null, approved_patch: null };
  let preserveFileObservation = false;
  let execPolicy = null;
  let sandbox = { state: 'available', backend: 'windows_sandbox' };
  let sandboxProbed = false;
  const storage = new Map();
  const timers = new Map();
  let nextTimer = 1;
  const api = {
    chooseWorkspace: async () => { calls.push(['choose']); return 'E:\\wrong-root'; },
    registerControlPlaneWorkspace: async (request) => {
      calls.push(['register', plain(request)]);
      return { ...workspace, workspace_generation: 'generation-new', capabilities: plain(request.capabilities) };
    },
    replaceControlPlaneWorkspace: async (request) => {
      calls.push(['replace', plain(request)]);
      return { ...workspace, workspace_generation: 'generation-new', capabilities: plain(request.capabilities) };
    },
    listControlPlaneWorkspaces: async () => {
      calls.push(['list-workspaces']);
      return state.centralWorkspaceReceipt ? [state.centralWorkspaceReceipt] : state.centralWorkspaces;
    },
    activateControlPlaneWorkspace: async (request) => {
      calls.push(['activate', plain(request)]);
      return { workspace_id: request.workspaceId, workspace_generation: request.workspaceGeneration,
        workspace_path: 'E:\\selected-project' };
    },
    installControlPlaneStandingFilePolicies: async (request) => {
      calls.push(['install-files', plain(request)]);
      const receipt = { state: 'enabled', file_read: policy(hashes.read), approved_patch: request.allowWrite ? policy(hashes.write) : null };
      if (!preserveFileObservation) observedFiles = receipt;
      return receipt;
    },
    inspectControlPlaneStandingFilePolicies: async (request) => {
      calls.push(['inspect-files', plain(request)]);
      return observedFiles;
    },
    inspectControlPlaneExecPolicy: async (request) => {
      calls.push(['inspect-exec', plain(request)]);
      if (request.probeSandbox === true) {
        calls.push(['probe-sandbox']);
        sandboxProbed = sandbox.state === 'available';
      }
      if (state.snapshot.settings.executionMode === 'local') {
        return { policy: execPolicy, sandbox: { state: 'not_required', backend: 'host_user', reason: 'OPERATOR_LOCAL_EXECUTION' } };
      }
      return { policy: execPolicy, sandbox: sandboxProbed || request.probeSandbox === true
        ? sandbox : { state: 'not_checked', reason: 'SANDBOX_PROBE_REQUIRED' } };
    },
    installControlPlaneExecPolicy: async (request) => {
      calls.push(['install-exec', plain(request)]);
      execPolicy = { ...policy(hashes.exec), execution_mode: request.executionMode || 'native_first',
        native_argv_prefixes: plain(request.nativeArgvPrefixes || []) };
      return { ...execPolicy, sandbox: state.snapshot.settings.executionMode === 'local'
        ? { state: 'not_required', backend: 'host_user', reason: 'OPERATOR_LOCAL_EXECUTION' }
        : request.probeSandbox === false
        ? { state: 'not_checked', reason: 'SANDBOX_PROBE_REQUIRED' } : sandbox };
    },
    installControlPlaneReadOnlyPolicyAssignment: async (request) => {
      calls.push(['install-metadata', plain(request)]);
      return { ...policy(hashes.metadata), enabled: true, expires_at_ms: Date.now() + 60 * 60_000 };
    }
  };
  const context = vm.createContext({
    state, api,
    window: { confirm: (message) => { confirmations.push(message); return accepted; } },
    localStorage: {
      getItem: (key) => storage.get(key) || null,
      setItem: (key, value) => storage.set(key, value)
    },
    setTimeout: (callback, delay) => { const id = nextTimer++; timers.set(id, { callback, delay }); return id; },
    clearTimeout: (id) => timers.delete(id),
    $: (selector) => {
      if (!elements.has(selector)) {
        const label = { hidden: false };
        elements.set(selector, {
        checked: false, dataset: {}, style: {}, classList: { remove() {}, add() {}, toggle() {} },
          querySelector: () => ({ textContent: '' }), closest: () => label, scrollIntoView() {}, focus() {}
        });
      }
      return elements.get(selector);
    },
    isCentralExecutor: (settings) => settings?.executionRole === 'central_executor',
    assertPackagedCentralSetup() {}, unwrap: (value) => value,
    renderCentralExecutorMode() {
      context.$('#controlPlaneCapabilityWrite').checked = state.centralWorkspaceCapabilities.write === true;
      context.$('#controlPlaneCapabilityExec').checked = state.centralWorkspaceCapabilities.exec === true;
      context.renderSetupExecution();
    },
    setDot: (element, tone) => { element.tone = tone; },
    renderSetupState() {},
    toast: (...args) => messages.push(args),
    refreshSnapshot: async () => calls.push(['refresh-snapshot']),
    reconcileControlPlaneAuthorityStatus: async (options) => calls.push(['refresh-authority', plain(options)]),
    reconcileControlPlaneEnrollment: async (options) => calls.push(['refresh-enrollment', plain(options)]),
    requestControlPlaneEnrollment: async () => calls.push(['request-enrollment']),
    centralSetupGuidance: () => ({ detail: 'Chờ owner duyệt máy.' }),
    authorityStatusPresentation: () => ({ detail: 'Đích đã bị thu hồi.' }),
    navigate: (page) => calls.push(['navigate', page]),
    openControlPlaneConsole: async () => calls.push(['console']),
    controlPlaneExecSandboxReason: (reason) => reason
  });
  for (const [start, end] of [
    ['function isLocalExecution()', 'function controlPlaneExecSandboxReason('],
    ['const CENTRAL_WORKSPACE_PRESETS', '// Central workspaces are deliberately separate'],
    ['function centralWorkspaceEntries', 'function centralWorkspaceSummary'],
    ['function centralWorkspaceCapabilitiesFromUi', 'function centralRoutePresentation'],
    ['async function addControlPlaneWorkspace', 'async function registerControlPlaneWorkspace'],
    ['async function registerControlPlaneWorkspace', 'async function refreshControlPlaneStandingFilePolicies'],
    ['async function refreshControlPlaneStandingFilePolicies', 'async function installControlPlaneExecPolicy'],
    ['async function installControlPlaneExecPolicy', 'async function installControlPlaneReadOnlyPolicyAssignment'],
    ['async function installControlPlaneReadOnlyPolicyAssignment', 'async function refreshCentralWorkspaceUiAfterCommit'],
    ['async function refreshCentralWorkspaceUiAfterCommit', 'async function retireControlPlaneWorkspace']
  ]) {
    const startIndex = source.indexOf(start);
    const endIndex = source.indexOf(end, startIndex);
    assert.ok(startIndex >= 0 && endIndex > startIndex, `missing renderer range ${start}`);
    vm.runInContext(source.slice(startIndex, endIndex), context);
  }
  // The setup controller is tested independently from markup rendering.
  context.renderSetupExecution = () => {};
  return {
    context, state, workspace, calls, confirmations, messages, storage, timers, hashes,
    setObservedFiles(value) { observedFiles = value; preserveFileObservation = true; },
    setSandbox(value) { sandbox = value; sandboxProbed = false; },
    setExecPolicy(value) { execPolicy = value; },
    async runTimer() {
      const [id, timer] = timers.entries().next().value || [];
      assert.ok(timer, 'expected a pending continuation timer');
      timers.delete(id);
      timer.callback();
      for (let attempt = 0; attempt < 100 && state.setupContinuationBusy; attempt += 1) await Promise.resolve();
      assert.equal(state.setupContinuationBusy, false, 'continuation should settle without wall-clock sleep');
    },
    policy
  };
}

function enableTargetRendering(f) {
  for (const [start, end] of [
    ['function renderSetupExecution(', '\nfunction centralRoutePresentation('],
    ['function renderDevice(', '\nfunction renderSetupState(']
  ]) vm.runInContext(source.slice(source.indexOf(start), source.indexOf(end, source.indexOf(start))), f.context);
}

function assertTargetLabels(f, expected, title = expected) {
  for (const selector of ['#sideWorkspace', '#deviceWorkspace', '#executionWorkspaceLabel', '#selectedWorkspace']) {
    assert.equal(f.context.$(selector).textContent, expected, selector);
    assert.equal(f.context.$(selector).title, title, `${selector} title`);
  }
}

test('adding a folder picks once confirms the exact path and installs full permission without starting Sandbox', async () => {
  const f = fixture({ write: false, exec: false });
  const path = 'E:\\DEV\\Autocad';
  f.context.api.chooseWorkspace = async () => { f.calls.push(['choose']); return path; };
  const register = f.context.api.registerControlPlaneWorkspace;
  f.context.api.registerControlPlaneWorkspace = async (request) => {
    assert.equal(f.confirmations.length, 1, 'consent precedes registration');
    const receipt = await register(request);
    return { ...receipt, display_name: 'Autocad' };
  };
  f.context.api.activateControlPlaneWorkspace = async (request) => {
    f.calls.push(['activate', plain(request)]);
    f.state.centralAuthorityStatus.targets = [{ workspace_id: request.workspaceId,
      workspace_generation: request.workspaceGeneration, dispatch_state: 'dispatchable',
      capabilities: { read: true, write: true, exec: true } }];
    return { workspace_id: request.workspaceId, workspace_generation: request.workspaceGeneration, workspace_path: path };
  };
  const access = await f.context.addControlPlaneWorkspace();
  assert.equal(f.confirmations.length, 1);
  assert.ok(f.confirmations[0].includes(path));
  assert.equal(f.calls.filter(([name]) => name === 'choose').length, 1);
  assert.deepEqual(f.calls.find(([name]) => name === 'register')[1], {
    workspacePath: path, capabilities: { read: true, write: true, exec: true }
  });
  assert.deepEqual(f.calls.find(([name]) => name === 'activate')[1], {
    workspaceId: 'workspace-selected', workspaceGeneration: 'generation-new', confirmActivate: true
  });
  assert.equal(f.calls.some(([name]) => name === 'replace' || name === 'probe-sandbox'), false);
  assert.equal(f.calls.find(([name]) => name === 'install-exec')[1].probeSandbox, false);
  assert.deepEqual(plain(access), { read: true, patch: true, exec: true, executionMode: 'native_first',
    sandbox: { state: 'not_checked', reason: 'SANDBOX_PROBE_REQUIRED' } });
  assert.equal(f.context.centralActiveWorkspacePath(), path);
  assert.equal(f.state.snapshot.settings.workspace, 'E:\\legacy-root', 'action-specific scope preserves native root');
  assert.equal(f.state.setupContinuation, null);
});

test('an existing folder confirmation uses its exact registered path instead of a duplicate display name', async () => {
  const f = fixture();
  f.workspace.display_name = 'Autocad';
  f.workspace.workspace_path = 'E:\\DEV\\Autocad';
  f.state.centralWorkspaces.push({ ...f.workspace, workspace_id: 'workspace-other',
    workspace_generation: 'generation-other', workspace_path: 'E:\\archive\\Autocad' });
  f.context.selectCentralWorkspace(f.workspace);
  await f.context.applyCentralWorkspacePermissions();
  assert.equal(f.confirmations.length, 1);
  assert.match(f.confirmations[0], /Cho phép MCP dùng thư mục “E:\\DEV\\Autocad”/);
  assert.equal(f.confirmations[0].includes('E:\\archive\\Autocad'), false);
  assert.equal(f.confirmations[0].includes('E:\\old-picker-root'), false);
  assert.equal(f.calls.some(([name]) => ['choose', 'register', 'replace'].includes(name)), false);
});

test('cancelling the Add-folder picker or its single permission confirmation performs no registration or activation', async () => {
  for (const cancelPicker of [true, false]) {
    const f = fixture({ accepted: false });
    f.context.api.chooseWorkspace = async () => { f.calls.push(['choose']); return cancelPicker ? '' : 'E:\\DEV\\Autocad'; };
    assert.equal(await f.context.addControlPlaneWorkspace(), null);
    assert.equal(f.calls.some(([name]) => ['register', 'replace', 'activate', 'install-files', 'install-exec', 'probe-sandbox'].includes(name)), false);
    assert.equal(f.confirmations.length, cancelPicker ? 0 : 1);
    assert.equal(f.state.centralWorkspaceBusy, false);
    assert.equal(f.state.setupStartBusy, false);
  }
});

test('using an existing full-permission folder activates its exact generation without registration or replacement', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  await f.context.applyCentralWorkspacePermissions();
  assert.deepEqual(f.calls.filter(([name]) => name === 'activate'), [['activate', {
    workspaceId: f.workspace.workspace_id, workspaceGeneration: f.workspace.workspace_generation, confirmActivate: true
  }]]);
  assert.equal(f.calls.some(([name]) => ['choose', 'register', 'replace'].includes(name)), false);
  assert.equal(f.confirmations.length, 1);
  const operations = f.calls.map(([name]) => name);
  assert.ok(operations.indexOf('activate') < operations.indexOf('refresh-authority'));
  assert.ok(operations.indexOf('refresh-authority') < operations.indexOf('install-files'));
});

test('activation failure or a mismatched activation receipt stops before installing permission', async () => {
  for (const kind of ['rejected', 'wrong-id', 'wrong-generation', 'missing-path', 'unsupported']) {
    const f = fixture();
    f.context.selectCentralWorkspace(f.workspace);
    if (kind === 'unsupported') delete f.context.api.activateControlPlaneWorkspace;
    else f.context.api.activateControlPlaneWorkspace = async () => {
      if (kind === 'rejected') throw new Error('CONTROL_PLANE_WORKSPACE_ACTIVATION_BUSY');
      return { workspace_id: kind === 'wrong-id' ? 'workspace-other' : f.workspace.workspace_id,
        workspace_generation: kind === 'wrong-generation' ? 'generation-other' : f.workspace.workspace_generation,
        ...(kind !== 'missing-path' && { workspace_path: 'E:\\DEV\\Autocad' }) };
    };
    await assert.rejects(f.context.applyCentralWorkspacePermissions(), /ACTIVATION_BUSY|chưa khớp|chưa hỗ trợ/);
    assert.equal(f.calls.some(([name]) => name.startsWith('install-') || name === 'probe-sandbox'), false, kind);
    assert.equal(f.state.centralWorkspaceActivationReceipt, undefined, kind);
    assert.equal(f.state.setupContinuation, null, kind);
    assert.doesNotMatch(f.state.setupContinuationMessage, /Đã xác minh policy/);
  }
});

test('cancelling while activation is pending prevents subsequent policy installation and display-cache update', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  let resolveActivation;
  f.context.api.activateControlPlaneWorkspace = () => new Promise((resolve) => { resolveActivation = resolve; });
  const pending = f.context.applyCentralWorkspacePermissions();
  for (let attempt = 0; attempt < 30 && !resolveActivation; attempt += 1) await Promise.resolve();
  assert.equal(typeof resolveActivation, 'function');
  f.context.cancelSetupContinuation('Đã dừng thiết lập.');
  resolveActivation({ workspace_id: f.workspace.workspace_id,
    workspace_generation: f.workspace.workspace_generation, workspace_path: 'E:\\DEV\\Autocad' });
  assert.equal(await pending, null);
  assert.equal(f.calls.some(([name]) => name.startsWith('install-')), false);
  assert.equal(f.storage.has('coding-tools-active-folder-v1'), false);
  assert.equal(f.state.setupContinuationBusy, false);
});

test('active-folder display cache requires matching current authority and policy before showing the folder', async () => {
  const f = fixture();
  const saved = { origin: 'https://control.example.test', device: 'device-current',
    workspace_id: f.workspace.workspace_id, workspace_generation: f.workspace.workspace_generation,
    workspace_path: 'E:\\DEV\\Autocad' };
  f.storage.set('coding-tools-active-folder-v1', JSON.stringify(saved));
  f.context.restoreCentralWorkspaceActivation();
  assert.equal(f.context.centralActiveWorkspacePath(), '', 'display cache is not permission evidence');
  f.context.selectCentralWorkspace(f.workspace);
  enableTargetRendering(f);
  f.context.renderSetupExecution();
  assertTargetLabels(f, 'Chưa kích hoạt thư mục', '');
  assert.equal(f.context.$('#setupExecCheck').dataset.state, 'pending');
  assert.deepEqual(f.calls, []);
  f.setObservedFiles({ file_read: f.policy(f.hashes.read), approved_patch: f.policy(f.hashes.write) });
  f.setExecPolicy(f.policy(f.hashes.exec));
  await f.context.refreshControlPlaneStandingFilePolicies();
  await f.context.inspectControlPlaneExecPolicy(f.workspace, { quiet: true });
  assertTargetLabels(f, saved.workspace_path);
  assert.equal(f.context.$('#workspaceMeta').textContent, saved.workspace_path);
  assert.equal(f.context.$('#setupExecCheck').dataset.state, 'verified');
  assert.equal(f.state.snapshot.settings.workspace, 'E:\\legacy-root');
  assert.equal(f.state.setupContinuation, null);
  for (const changed of [{ device: 'device-other' }, { origin: 'https://other.example.test' },
    { workspace_generation: 'generation-other' }]) {
    f.state.centralWorkspaceActivationReceipt = { ...saved, ...changed };
    assert.equal(f.context.centralActiveWorkspacePath(), '');
  }
});

test('async inventory and policy observations refresh every target label and clear them on loss of evidence', async () => {
  const f = fixture();
  enableTargetRendering(f);
  f.workspace.workspace_path = 'E:\\DEV\\Autocad';
  f.context.selectCentralWorkspace(f.workspace);
  f.setObservedFiles({ file_read: f.policy(f.hashes.read), approved_patch: f.policy(f.hashes.write) });
  f.setExecPolicy(f.policy(f.hashes.exec));
  await f.context.refreshControlPlaneWorkspaces({ quiet: true });
  assertTargetLabels(f, 'Chưa kích hoạt thư mục', '');
  await f.context.inspectControlPlaneExecPolicy(f.workspace, { quiet: true });
  assertTargetLabels(f, f.workspace.workspace_path);
  assert.equal(f.context.$('#workspaceMeta').textContent, f.workspace.workspace_path);
  assert.equal(f.context.$('#workspaceStatus').textContent, 'Đích cho tác vụ mới');
  assert.equal(f.state.snapshot.settings.workspace, 'E:\\legacy-root');

  let finishInventory;
  f.context.api.listControlPlaneWorkspaces = () => new Promise((resolve) => { finishInventory = resolve; });
  const pending = f.context.refreshControlPlaneWorkspaces({ quiet: true });
  assertTargetLabels(f, 'Chưa kích hoạt thư mục', '');
  finishInventory([f.workspace]);
  await pending;
  assertTargetLabels(f, f.workspace.workspace_path);
  f.context.api.listControlPlaneWorkspaces = async () => { throw new Error('inventory unavailable'); };
  await assert.rejects(f.context.refreshControlPlaneWorkspaces({ quiet: true }), /inventory unavailable/);
  assertTargetLabels(f, 'Chưa kích hoạt thư mục', '');
  f.state.centralWorkspaces = [f.workspace];
  f.state.centralWorkspaceInventoryStatus = 'loaded';
  f.context.renderSetupExecution();
  assertTargetLabels(f, f.workspace.workspace_path);
  f.context.api.inspectControlPlaneStandingFilePolicies = async () => { throw new Error('policy unavailable'); };
  await f.context.refreshControlPlaneStandingFilePolicies();
  assertTargetLabels(f, 'Chưa kích hoạt thư mục', '');
});

test('device and setup displays agree on exact active folder and fail closed for authority or snapshot mismatch', async () => {
  const f = fixture();
  enableTargetRendering(f);
  f.workspace.workspace_path = 'E:\\DEV\\Autocad';
  f.state.snapshot.device.workspace = 'E:\\legacy-root';
  f.state.snapshot.device.git = { available: true, branch: 'main', head_short: '7999c415', dirty: true };
  f.setObservedFiles({ file_read: f.policy(f.hashes.read), approved_patch: f.policy(f.hashes.write) });
  f.setExecPolicy(f.policy(f.hashes.exec));
  await f.context.refreshControlPlaneStandingFilePolicies();
  await f.context.inspectControlPlaneExecPolicy(f.workspace, { quiet: true });
  f.context.renderDevice(f.state.snapshot);
  assertTargetLabels(f, f.workspace.workspace_path);
  assert.equal(f.context.$('#deviceGitState').textContent, 'main @ 7999c415 · dirty');
  assert.equal(f.state.snapshot.device.workspace, 'E:\\legacy-root');

  for (const authorityChange of [{ fresh: false }, { state: 'revoked' }, { state: 'binding_revoked' }, { targets: [] },
    { targets: [{ ...f.state.centralAuthorityStatus.targets[0], workspace_generation: 'different-generation' }] }]) {
    const original = f.state.centralAuthorityStatus;
    f.state.centralAuthorityStatus = { ...original, ...authorityChange };
    f.context.renderDevice(f.state.snapshot);
    assertTargetLabels(f, 'Chưa kích hoạt thư mục', '');
    assert.equal(f.context.$('#workspaceDot').tone, 'warn');
    f.state.centralAuthorityStatus = original;
  }
  for (const otherSnapshot of [
    { ...f.state.snapshot, device: { device_id: 'different-device' } },
    { ...f.state.snapshot, settings: { ...f.state.snapshot.settings, controlPlaneServerUrl: 'https://other.example.test' } },
    { ...f.state.snapshot, status: { telemetryAvailable: false } },
    { ...f.state.snapshot, status: { signalStale: true } }
  ]) {
    f.context.renderDevice(otherSnapshot);
    assertTargetLabels(f, 'Chưa kích hoạt thư mục', '');
  }
  f.context.renderDevice(f.state.snapshot);
  assertTargetLabels(f, f.workspace.workspace_path);
  const earlierFreshSnapshot = { ...f.state.snapshot, status: { signalStale: false, telemetryAvailable: true } };
  f.state.snapshot.status.signalStale = true;
  f.context.renderDevice(earlierFreshSnapshot);
  assertTargetLabels(f, 'Chưa kích hoạt thư mục', '');
});

test('full snapshot render keeps the verified MCP target even when native runtime workspace differs', async () => {
  const f = fixture();
  enableTargetRendering(f);
  f.workspace.workspace_path = 'E:\\DEV\\Autocad';
  f.state.snapshot.secrets = {};
  f.state.snapshot.environment = { python: { installed: true }, workspace: { exists: true } };
  f.state.snapshot.device.workspace = f.state.snapshot.settings.workspace;
  f.setObservedFiles({ file_read: f.policy(f.hashes.read), approved_patch: f.policy(f.hashes.write) });
  f.setExecPolicy(f.policy(f.hashes.exec));
  await f.context.refreshControlPlaneStandingFilePolicies();
  await f.context.inspectControlPlaneExecPolicy(f.workspace, { quiet: true });
  Object.assign(f.context, {
    applyFormValues() {}, renderRecoveryTunnelSettings() {}, renderRuntimeSourceStatus() {},
    renderAuthorizedRoots() {}, renderEnvironment() {}, renderDeploySummary() {},
    centralDispatchableTargetForLocalWorkspace: () => f.state.centralAuthorityStatus.targets[0],
    centralTargetReadiness: () => ({ ready: true }),
    centralRoutePresentation: () => ({ state: 'connected', label: 'Connected', detail: 'Verified' }),
    connectorContractPresentation: () => ({ notice: false }),
    renderCentralExecutorMode() { f.context.renderSetupExecution(); return { central: true, route: f.context.centralRoutePresentation() }; }
  });
  vm.runInContext(source.slice(source.indexOf('function renderSnapshot('), source.indexOf('\nfunction renderAuthorizedRoots(')), f.context);
  f.context.renderSnapshot(f.state.snapshot);
  assertTargetLabels(f, f.workspace.workspace_path);
  assert.equal(f.context.$('#workspaceMeta').textContent, f.workspace.workspace_path);
  assert.equal(f.context.$('#workspaceStatus').textContent, 'Đích cho tác vụ mới');
  assert.equal(f.state.selectedWorkspace, 'E:\\legacy-root', 'the native default remains unchanged');
});

test('stale heartbeat clears all active-folder labels before returning', async () => {
  for (const staleSignal of [{ signalStale: true }, { telemetryAvailable: false }]) {
    const f = fixture();
    enableTargetRendering(f);
    f.workspace.workspace_path = 'E:\\DEV\\Autocad';
    f.setObservedFiles({ file_read: f.policy(f.hashes.read), approved_patch: f.policy(f.hashes.write) });
    f.setExecPolicy(f.policy(f.hashes.exec));
    await f.context.refreshControlPlaneStandingFilePolicies();
    await f.context.inspectControlPlaneExecPolicy(f.workspace, { quiet: true });
    assertTargetLabels(f, f.workspace.workspace_path);
    f.context.renderRecoveryTunnelSettings = () => {};
    vm.runInContext(source.slice(source.indexOf('function applyHeartbeat('), source.indexOf('\nasync function loadLogs(')), f.context);
    f.context.applyHeartbeat(staleSignal);
    assertTargetLabels(f, 'Chưa kích hoạt thư mục', '');
    assert.equal(f.context.$('#workspaceStatus').textContent, 'Chưa kích hoạt');
    assert.equal(f.context.$('#workspaceDot').tone, 'warn');
  }
});

test('direct mode uses its settings workspace consistently instead of device runtime root', () => {
  const f = fixture();
  enableTargetRendering(f);
  f.state.snapshot.settings.executionRole = 'direct';
  f.state.snapshot.settings.workspace = 'E:\\DEV\\DirectProject';
  f.state.snapshot.device.workspace = 'E:\\application-runtime';
  f.state.snapshot.environment = { workspace: { exists: true } };
  f.context.renderDevice(f.state.snapshot);
  assertTargetLabels(f, f.state.snapshot.settings.workspace);
  assert.equal(f.context.$('#workspaceMeta').textContent, f.state.snapshot.settings.workspace);
  assert.equal(f.context.$('#workspaceStatus').textContent, 'Đã ủy quyền');
});

test('reopening after headless activation reconstructs the active folder from verified local inventory and policies', async () => {
  const f = fixture();
  f.workspace.workspace_path = 'E:\\DEV\\Autocad';
  f.setObservedFiles({ file_read: f.policy(f.hashes.read), approved_patch: f.policy(f.hashes.write) });
  f.setExecPolicy(f.policy(f.hashes.exec));
  await f.context.refreshControlPlaneStandingFilePolicies();
  await f.context.inspectControlPlaneExecPolicy(f.workspace, { quiet: true });
  assert.equal(f.context.centralActiveWorkspacePath(), f.workspace.workspace_path);
  assert.equal(f.state.centralWorkspaceActivationReceipt, undefined);
  assert.equal(f.state.setupContinuation, null);
  assert.equal(f.calls.some(([name]) => name === 'activate' || name.startsWith('install-') || name === 'probe-sandbox'), false);
  f.state.centralAuthorityStatus.fresh = false;
  assert.equal(f.context.centralActiveWorkspacePath(), '', 'stale authority cannot keep the active label');
  f.state.centralAuthorityStatus.fresh = true;
  f.state.centralAuthorityStatus.targets[0].workspace_generation = 'generation-other';
  assert.equal(f.context.centralActiveWorkspacePath(), '', 'different active generation cannot inherit a local path');
});

test('selecting a registered folder loads its capabilities by exact identity and clears the previous picker', () => {
  const f = fixture({ write: false, exec: true });
  f.state.centralWorkspaces.unshift({
    workspace_id: 'workspace-other', workspace_generation: 'generation-other',
    display_name: f.workspace.display_name, capabilities: { read: true, write: true, exec: false }
  });
  f.context.selectCentralWorkspace({ ...f.workspace, capabilities: { read: true, write: true, exec: true } });
  assert.deepEqual(plain(f.state.centralWorkspaceSelection), {
    workspace_id: 'workspace-selected', workspace_generation: 'generation-current'
  });
  assert.deepEqual(plain(f.state.centralWorkspaceCapabilities), { read: true, write: false, exec: true });
  assert.equal(f.state.centralWorkspacePreset, 'custom');
  assert.equal(f.state.centralWorkspaceCandidate, '');
  assert.equal(f.state.snapshot.settings.workspace, 'E:\\legacy-root');
  assert.deepEqual(f.calls, []);
});

test('changing the selected permission preset is a draft with no API mutation', () => {
  const f = fixture({ write: false, exec: false });
  f.context.selectCentralWorkspace(f.workspace);
  f.context.chooseCentralWorkspacePreset('code');
  assert.deepEqual(plain(f.state.centralWorkspaceCapabilities), { read: true, write: true, exec: true });
  assert.deepEqual(f.workspace.capabilities, { read: true, write: false, exec: false });
  assert.equal(f.state.centralWorkspaceSelection.workspace_generation, 'generation-current');
  assert.deepEqual(f.calls, []);
  assert.deepEqual(f.confirmations, []);
});

test('applying changed capabilities replaces only the selected ID and generation without another picker', async () => {
  const f = fixture({ write: false, exec: false });
  f.context.selectCentralWorkspace(f.workspace);
  f.context.chooseCentralWorkspacePreset('code');
  f.state.centralWorkspaceCandidate = 'E:\\unrelated-root';
  assert.equal(await f.context.applyCentralWorkspacePermissions({ prepareExec: true }), null);
  assert.deepEqual(f.calls.filter(([name]) => name === 'replace'), [['replace', {
    workspaceId: 'workspace-selected', workspaceGeneration: 'generation-current',
    capabilities: { read: true, write: true, exec: true }, confirmReplace: true
  }]]);
  assert.equal(f.calls.some(([name]) => ['choose', 'install-files', 'install-exec'].includes(name)), false);
  assert.equal(f.confirmations.length, 1);
  assert.match(f.confirmations[0], /Đổi mức quyền.*đóng liên kết và tác vụ/);
  assert.match(f.confirmations[0], /Cho phép MCP dùng thư mục/);
  assert.equal(f.state.centralWorkspaceSelection.workspace_generation, 'generation-new');
  assert.equal(f.state.setupContinuation.workspace_generation, 'generation-new');
  assert.deepEqual(plain(f.state.setupContinuation.capabilities), { read: true, write: true, exec: true });
  assert.equal(f.timers.size, 1);
  assert.equal(f.state.centralWorkspaceCandidate, '');
  assert.equal(f.state.centralWorkspaceBusy, false);
});

test('unchanged capabilities with no exact dispatchable binding wait for owner without opening Console or installing policies', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralAuthorityStatus.targets[0].workspace_generation = 'generation-other';
  assert.equal(await f.context.applyCentralWorkspacePermissions({ prepareExec: true }), null);
  assert.equal(f.calls.some(([name]) => name === 'console' || name.startsWith('install-')), false);
  assert.equal(f.calls.filter(([name]) => name === 'refresh-authority').length, 1);
  assert.equal(f.calls.filter(([name]) => name === 'list-workspaces').length, 1);
  assert.equal(f.confirmations.length, 1);
  assert.equal(f.state.setupContinuation.workspace_generation, 'generation-current');
  assert.equal([...f.timers.values()][0].delay, 15_000);
});

test('retained authority targets cannot grant permissions when freshness refresh still fails and remain pending', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralAuthorityStatus.fresh = false;
  assert.equal(f.context.centralWorkspaceTarget(f.workspace), null);
  assert.equal(await f.context.applyCentralWorkspacePermissions({ prepareExec: true }), null);
  assert.equal(f.calls.some(([name]) => name.startsWith('install-') || name === 'console'), false);
  assert.equal(f.calls.filter(([name]) => name === 'refresh-authority').length, 1);
  assert.equal(f.confirmations.length, 1);
  assert.match(f.state.setupContinuationMessage, /Chưa đọc được trạng thái Ubuntu/);
  assert.equal(f.timers.size, 1);
});

test('successful authority refresh permits the same exact selected target', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralAuthorityStatus.fresh = false;
  f.context.reconcileControlPlaneAuthorityStatus = async (options) => {
    f.calls.push(['refresh-authority', plain(options)]);
    f.state.centralAuthorityStatus.fresh = true;
  };
  await f.context.applyCentralWorkspacePermissions({ prepareExec: true });
  assert.deepEqual(f.calls.find(([name]) => name === 'refresh-authority'), ['refresh-authority', { quiet: true }]);
  assert.equal(f.confirmations.length, 1);
  assert.equal(f.calls.some(([name]) => name === 'install-exec'), true);
});

test('fresh but inactive authority does not reuse a retained dispatchable target or auto-open Console', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralAuthorityStatus.state = 'unknown';
  assert.equal(f.context.centralWorkspaceTarget(f.workspace), null);
  assert.equal(await f.context.applyCentralWorkspacePermissions({ prepareExec: true }), null);
  assert.equal(f.calls.some(([name]) => name.startsWith('install-') || name === 'console'), false);
  assert.equal(f.calls.filter(([name]) => name === 'refresh-authority').length, 1);
  assert.equal(f.confirmations.length, 1);
  assert.equal(f.timers.size, 1);
});

test('pending owner authority resumes on the 15 second check using the same in-memory consent', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralAuthorityStatus.targets = [];
  await f.context.applyCentralWorkspacePermissions({ prepareExec: true });
  const consent = f.state.setupContinuation;
  assert.equal(consent.origin, 'https://control.example.test');
  assert.equal(consent.device, 'device-current');
  assert.equal([...f.timers.values()][0].delay, 15_000);
  const persisted = JSON.parse(f.storage.get('coding-tools-setup-selection-v1'));
  assert.deepEqual(Object.keys(persisted).sort(), ['device', 'origin', 'workspace_generation', 'workspace_id']);
  f.state.centralAuthorityStatus.targets = [{
    workspace_id: f.workspace.workspace_id, workspace_generation: f.workspace.workspace_generation,
    dispatch_state: 'dispatchable', capabilities: { ...f.workspace.capabilities }
  }];
  await f.runTimer();
  assert.equal(f.confirmations.length, 1);
  assert.equal(f.calls.filter(([name]) => name === 'refresh-authority').length, 3);
  assert.deepEqual(f.calls.filter(([name]) => name.startsWith('install-')).map(([name]) => name),
    ['install-files', 'install-exec']);
  assert.equal(f.state.setupContinuation, null);
  assert.equal(f.timers.size, 0);
});

test('a duplicated exact target remains pending rather than silently choosing a binding', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralAuthorityStatus.targets.push({ ...f.state.centralAuthorityStatus.targets[0] });
  assert.equal(f.context.centralWorkspaceTarget(f.workspace), null);
  assert.equal(await f.context.applyCentralWorkspacePermissions({ prepareExec: true }), null);
  assert.equal(f.calls.some(([name]) => name.startsWith('install-')), false);
  assert.equal(f.timers.size, 1);
});

test('dispatchable binding without every selected capability remains pending before local effects', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralAuthorityStatus.targets[0].capabilities.exec = false;
  assert.equal(await f.context.applyCentralWorkspacePermissions({ prepareExec: true }), null);
  assert.equal(f.calls.some(([name]) => name.startsWith('install-')), false);
  assert.equal(f.timers.size, 1);
  assert.equal(f.confirmations.length, 1);
});

test('cancelling pending setup clears the timer and a later authority observation cannot install policies', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralAuthorityStatus.targets = [];
  await f.context.applyCentralWorkspacePermissions({ prepareExec: true });
  assert.equal(f.timers.size, 1);
  f.context.cancelSetupContinuation('Người dùng đã dừng.');
  f.state.centralAuthorityStatus.targets = [{
    workspace_id: f.workspace.workspace_id, workspace_generation: f.workspace.workspace_generation,
    dispatch_state: 'dispatchable', capabilities: { ...f.workspace.capabilities }
  }];
  assert.equal(await f.context.continueSetup(), null);
  assert.equal(f.timers.size, 0);
  assert.equal(f.calls.some(([name]) => name.startsWith('install-')), false);
  assert.equal(f.confirmations.length, 1);
});

test('server, device, generation, and capability changes cancel retained consent before installing policies', async () => {
  for (const change of ['server', 'device', 'generation', 'capability']) {
    const f = fixture();
    f.context.selectCentralWorkspace(f.workspace);
    f.state.centralAuthorityStatus.targets = [];
    await f.context.applyCentralWorkspacePermissions({ prepareExec: true });
    if (change === 'server') f.state.snapshot.settings.controlPlaneServerUrl = 'https://other.example.test';
    if (change === 'device') f.state.snapshot.device.device_id = 'device-other';
    if (change === 'generation') f.state.centralWorkspaces = [{ ...f.workspace, workspace_generation: 'generation-other' }];
    if (change === 'capability') f.state.centralWorkspacePreset = 'read';
    await f.runTimer();
    assert.equal(f.state.setupContinuation, null, change);
    assert.equal(f.calls.some(([name]) => name.startsWith('install-')), false, change);
    assert.equal(f.timers.size, 0, change);
    assert.equal(f.confirmations.length, 1, change);
  }
});

test('waiting stops after its bounded deadline without creating durable consent', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralAuthorityStatus.targets = [];
  await f.context.applyCentralWorkspacePermissions({ prepareExec: true });
  f.state.setupContinuation.deadline = Date.now() - 1;
  await f.runTimer();
  assert.equal(f.state.setupContinuation, null);
  assert.match(f.state.setupContinuationMessage, /10 phút/);
  assert.equal(f.calls.some(([name]) => name.startsWith('install-')), false);
  assert.equal(f.timers.size, 0);
});

test('reopening restores only an exact server/device/generation draft and requires new consent', () => {
  const previous = fixture();
  previous.context.selectCentralWorkspace(previous.workspace);
  const stored = previous.storage.get('coding-tools-setup-selection-v1');
  const reopened = fixture();
  reopened.storage.set('coding-tools-setup-selection-v1', stored);
  reopened.state.centralWorkspaceCandidate = '';
  reopened.context.restoreSetupSelection();
  assert.deepEqual(plain(reopened.state.centralWorkspaceSelection), {
    workspace_id: previous.workspace.workspace_id, workspace_generation: previous.workspace.workspace_generation
  });
  assert.equal(reopened.state.setupContinuation, null);
  assert.equal(reopened.timers.size, 0);
  assert.deepEqual(reopened.calls, []);
  const wrongDevice = fixture();
  wrongDevice.state.centralWorkspaceCandidate = '';
  wrongDevice.state.snapshot.device.device_id = 'device-other';
  wrongDevice.storage.set('coding-tools-setup-selection-v1', stored);
  wrongDevice.context.restoreSetupSelection();
  assert.equal(wrongDevice.state.centralWorkspaceSelection, null);
});

test('unapproved enrollment does not select or register a root or install policies', async () => {
  for (const enrollment of [{ fresh: true, state: 'pending' }, { fresh: false, state: 'approved' }]) {
    const f = fixture();
    f.context.selectCentralWorkspace(f.workspace);
    f.state.centralEnrollmentStatus = enrollment;
    assert.equal(await f.context.applyCentralWorkspacePermissions({ prepareExec: true }), null);
    assert.equal(f.calls.some(([name]) => name.startsWith('install-') || ['choose', 'register', 'replace'].includes(name)), false);
    assert.equal(f.confirmations.length, 0);
    assert.equal(f.state.setupContinuation, null);
    assert.ok(f.calls.some(([name]) => name === 'navigate'));
  }
});

test('standing setup confirms local scope once and verifies files before installing exec without compact assignment', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  const access = await f.context.applyCentralWorkspacePermissions({ prepareExec: true });
  assert.equal(f.confirmations.length, 1);
  assert.match(f.confirmations[0], /Cho phép MCP dùng thư mục.*Máy hiện tại/);
  assert.match(f.confirmations[0], /Quyền đã chọn/);
  assert.match(f.confirmations[0], /Windows Sandbox/);
  const operations = f.calls.map(([name]) => name);
  assert.equal(operations.includes('install-metadata'), false);
  assert.equal(operations.filter((name) => name === 'install-files').length, 1);
  assert.equal(operations.filter((name) => name === 'install-exec').length, 1);
  assert.ok(operations.indexOf('refresh-authority') < operations.indexOf('install-files'));
  assert.ok(operations.indexOf('inspect-files') < operations.indexOf('install-exec'));
  for (const [name, request] of f.calls.filter(([name]) => name.startsWith('install-'))) {
    assert.equal(request.workspaceId, f.workspace.workspace_id, name);
    assert.equal(request.workspaceGeneration, f.workspace.workspace_generation, name);
    assert.equal(request.confirmInstall, true, name);
  }
  assert.equal(f.state.centralPermissionBusy, false);
  assert.equal(f.state.centralPolicyBusy, false);
  assert.equal(f.state.centralExecBusy, false);
  assert.equal(f.state.setupContinuationBusy, false);
  assert.equal(f.state.setupContinuation, null);
  assert.deepEqual(plain(access), { read: true, patch: true, exec: true, executionMode: 'native_first', sandbox: { state: 'available', backend: 'windows_sandbox' } });
});

test('ordinary folder permission setup verifies read write and exec policy without opening Sandbox', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  const access = await f.context.applyCentralWorkspacePermissions();
  assert.equal(access.read, true);
  assert.equal(access.patch, true);
  assert.equal(access.exec, true);
  assert.equal(access.sandbox.state, 'not_checked');
  assert.equal(f.calls.filter(([name]) => name === 'install-files').length, 1);
  assert.equal(f.calls.some(([name]) => name === 'probe-sandbox'), false);
  assert.equal(f.calls.filter(([name]) => name === 'install-exec').length, 1);
  assert.equal(f.calls.find(([name]) => name === 'install-exec')[1].probeSandbox, false);
  assert.ok(f.calls.filter(([name]) => name === 'inspect-exec').every(([, request]) => request.probeSandbox === false));
  assert.match(f.confirmations[0], /metadata Git và phiên bản CLI không mở VM/);
  assert.match(f.state.setupContinuationMessage, /Đã xác minh policy/);
  assert.equal(f.state.setupContinuation, null);
  assert.equal(f.timers.size, 0);
});

test('local folder setup confirms host-user access once and hides sandbox controls without probing', async () => {
  const f = fixture({ executionMode: 'local' });
  f.context.selectCentralWorkspace(f.workspace);
  const access = await f.context.applyCentralWorkspacePermissions({ prepareExec: true });
  assert.equal(f.confirmations.length, 1);
  assert.match(f.confirmations[0], /trực tiếp.*user Windows hiện tại/);
  assert.match(f.confirmations[0], /file và mạng của user/);
  assert.doesNotMatch(f.confirmations[0], /mở Windows Sandbox|ProcessContainer|lệnh không có mạng/);
  assert.equal(access.exec, true);
  assert.equal(access.sandbox.state, 'not_required');
  assert.equal(f.calls.some(([name]) => name === 'probe-sandbox'), false);
  assert.ok(f.calls.filter(([name]) => name === 'inspect-exec' || name === 'install-exec')
    .every(([, request]) => request.probeSandbox === false));
  enableTargetRendering(f);
  f.context.renderSetupExecution();
  assert.equal(f.context.$('#setupPrepareExecAction').hidden, true);
  assert.equal(f.context.$('#controlPlaneExecutionMode').closest('label').hidden, true);
  assert.match(f.context.$('#controlPlaneRunnerState').textContent, /trực tiếp bằng user Windows hiện tại/);
  assert.doesNotMatch(f.context.$('#controlPlaneRunnerState').textContent, /đã kiểm tra|lệnh đã chạy/);
});

test('local advanced execution consent describes host access and ignores sandbox diagnostic requests', async () => {
  const f = fixture({ executionMode: 'local' });
  f.context.selectCentralWorkspace(f.workspace);
  const receipt = await f.context.installControlPlaneExecPolicy(f.workspace, { probeSandbox: true });
  assert.equal(f.confirmations.length, 1);
  assert.match(f.confirmations[0], /trực tiếp bằng user Windows hiện tại/);
  assert.match(f.confirmations[0], /file và mạng của user/);
  assert.doesNotMatch(f.confirmations[0], /Sandbox|ProcessContainer|không có network/);
  assert.equal(receipt.sandbox.state, 'not_required');
  assert.equal(f.calls.some(([name]) => name === 'probe-sandbox'), false);
  assert.equal(f.calls.find(([name]) => name === 'install-exec')[1].probeSandbox, false);
  const confirmationCount = f.confirmations.length;
  const observed = await f.context.inspectControlPlaneExecPolicy(f.workspace, { probeSandbox: true });
  assert.equal(observed.sandbox.state, 'not_required');
  assert.equal(f.confirmations.length, confirmationCount);
  assert.equal(f.calls.some(([name]) => name === 'probe-sandbox'), false);
  assert.ok(f.messages.some(([title, detail]) => title === 'Chạy trực tiếp trên máy'
    && detail.includes('Chưa chạy lệnh kiểm chứng')));
});

test('execution mode is included in the single folder consent and installed without a VM probe', async () => {
  for (const mode of ['native_first', 'native_only', 'isolated']) {
    const f = fixture();
    f.state.centralExecutionMode = mode;
    f.context.selectCentralWorkspace(f.workspace);
    const access = await f.context.applyCentralWorkspacePermissions();
    assert.equal(access.executionMode, mode);
    const request = f.calls.find(([name]) => name === 'install-exec')[1];
    assert.equal(request.executionMode, mode);
    assert.deepEqual(request.nativeArgvPrefixes, []);
    assert.equal(request.probeSandbox, false);
    assert.equal(f.calls.some(([name]) => name === 'probe-sandbox'), false);
    assert.equal(f.confirmations.length, 1);
    assert.match(f.confirmations[0], mode === 'native_only' ? /không mở VM; chặn lệnh/
      : mode === 'isolated' ? /Ưu tiên cách ly/ : /metadata Git và phiên bản CLI không mở VM/);
  }
});

test('changing execution mode reinstalls its exact policy and retains already approved native prefixes', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  const prefixes = [['dotnet', 'build']];
  f.setExecPolicy({ ...f.policy(f.hashes.exec), execution_mode: 'native_first', native_argv_prefixes: prefixes });
  const receipt = await f.context.installControlPlaneExecPolicy(f.workspace, {
    confirmationAccepted: true, executionMode: 'native_only'
  });
  assert.equal(receipt.execution_mode, 'native_only');
  assert.deepEqual(plain(receipt.native_argv_prefixes), prefixes);
  assert.equal(f.calls.filter(([name]) => name === 'install-exec').length, 1);
  assert.equal(f.calls.some(([name]) => name === 'probe-sandbox'), false);
});

test('reopening restores the exact saved native-only or isolated mode before the single folder consent', async () => {
  for (const mode of ['native_only', 'isolated']) {
    const f = fixture();
    f.context.selectCentralWorkspace(f.workspace);
    f.state.centralExecutionMode = null;
    f.setExecPolicy({ ...f.policy(f.hashes.exec), execution_mode: mode, native_argv_prefixes: [] });
    const access = await f.context.applyCentralWorkspacePermissions();
    assert.equal(f.state.centralExecutionMode, mode);
    assert.equal(access.executionMode, mode);
    assert.match(f.confirmations[0], mode === 'native_only' ? /Chỉ native có kiểm soát/ : /Ưu tiên cách ly/);
    assert.equal(f.calls.some(([name]) => name === 'install-exec' || name === 'probe-sandbox'), false,
      'saved mode is reused after fresh authority without policy mutation or VM launch');
    enableTargetRendering(f);
    f.context.renderSetupExecution();
    assert.equal(f.context.$('#controlPlaneExecutionMode').value, mode);
  }
});

test('saved execution mode cannot transfer from another workspace or old generation before consent', async () => {
  for (const delta of [{ workspace_id: 'workspace-other' }, { workspace_generation: 'generation-old' }]) {
    const f = fixture();
    f.context.selectCentralWorkspace(f.workspace);
    f.state.centralExecutionMode = null;
    f.setExecPolicy({ ...f.policy(f.hashes.exec), ...delta, execution_mode: 'native_only', native_argv_prefixes: [] });
    const access = await f.context.applyCentralWorkspacePermissions();
    assert.equal(access.executionMode, 'native_first');
    assert.match(f.confirmations[0], /Native trước theo policy/);
    assert.equal(f.calls.find(([name]) => name === 'install-exec')[1].executionMode, 'native_first');
  }
});

test('advanced execution consent retains a saved exact mode when no draft was selected', async () => {
  const f = fixture({ accepted: false });
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralExecutionMode = null;
  f.setExecPolicy({ ...f.policy(f.hashes.exec), execution_mode: 'native_only',
    current_facade_contract: null, native_argv_prefixes: [] });
  assert.equal(await f.context.installControlPlaneExecPolicy(f.workspace), null);
  assert.match(f.confirmations[0], /Chỉ dùng native ProcessContainer/);
  assert.equal(f.calls.some(([name]) => name.startsWith('install-') || name === 'probe-sandbox'), false);
});

test('selecting another exact workspace clears the previous mode draft and explicit current drafts survive saved mode inspection', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralExecutionMode = 'native_only';
  const other = { ...f.workspace, workspace_id: 'workspace-other', workspace_generation: 'generation-other' };
  f.state.centralWorkspaces.push(other);
  f.context.selectCentralWorkspace(other);
  assert.equal(f.state.centralExecutionMode, null);
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralExecutionMode = 'isolated';
  f.setExecPolicy({ ...f.policy(f.hashes.exec), execution_mode: 'native_only', native_argv_prefixes: [] });
  await f.context.inspectControlPlaneExecPolicy(f.workspace, { probeSandbox: false, quiet: true });
  assert.equal(f.state.centralExecutionMode, 'isolated', 'an explicit current draft wins over a saved policy');
});

test('native permission and resource-limit errors use the actual runtime codes', () => {
  const f = fixture();
  const start = source.indexOf('function controlPlaneExecSandboxReason(');
  vm.runInContext(source.slice(start, source.indexOf('\nfunction ', start + 1)), f.context);
  assert.match(f.context.controlPlaneExecSandboxReason('NATIVE_EXECUTION_NOT_APPROVED'), /chưa được cấp quyền native/);
  assert.match(f.context.controlPlaneExecSandboxReason('NATIVE_RESOURCE_LIMITS_UNAVAILABLE'), /Job Object/);
  assert.match(f.context.controlPlaneExecSandboxReason('NATIVE_ELEVATED_HOST_DENIED'), /quyền quản trị/);
  assert.match(f.context.controlPlaneExecSandboxReason('NATIVE_TOKEN_POSTURE_UNAVAILABLE'), /token quyền hạn/);
  assert.doesNotMatch(source, /NATIVE_EXECUTION_DENIED:/);
});

test('native project approvals cannot transfer from a policy for another workspace or generation', async () => {
  for (const delta of [{ workspace_id: 'workspace-other' }, { workspace_generation: 'generation-old' }]) {
    const f = fixture();
    f.context.selectCentralWorkspace(f.workspace);
    f.setExecPolicy({ ...f.policy(f.hashes.exec), ...delta, execution_mode: 'native_only',
      native_argv_prefixes: [['npm', 'test']] });
    await f.context.installControlPlaneExecPolicy(f.workspace, { confirmationAccepted: true, executionMode: 'native_only' });
    const request = f.calls.find(([name]) => name === 'install-exec')[1];
    assert.deepEqual(request.nativeArgvPrefixes, [], 'approval is bound to the original workspace generation');
  }
});

test('changing execution mode invalidates waiting consent before later authority can install a policy', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralAuthorityStatus.targets = [];
  await f.context.applyCentralWorkspacePermissions();
  assert.equal(f.state.setupContinuation.execution_mode, 'native_first');
  f.state.centralExecutionMode = 'native_only';
  f.state.centralAuthorityStatus.targets = [{ workspace_id: f.workspace.workspace_id,
    workspace_generation: f.workspace.workspace_generation, dispatch_state: 'dispatchable',
    capabilities: { ...f.workspace.capabilities } }];
  await f.runTimer();
  assert.equal(f.state.setupContinuation, null);
  assert.equal(f.calls.some(([name]) => name.startsWith('install-')), false);
});

test('native readiness labels capability separately from Job proof and do not invent VM RAM', () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  enableTargetRendering(f);
  f.state.centralExecObservations[f.context.centralExecObservationKey(f.workspace)] = {
    policy: { ...f.policy(f.hashes.exec), execution_mode: 'native_first', native_argv_prefixes: [] },
    sandbox: { state: 'available', backend: 'process_container', capability_verified: true, execution_verified: false }
  };
  f.context.renderSetupExecution();
  const text = f.context.$('#controlPlaneRunnerState').textContent;
  assert.match(text, /capability ProcessContainer/);
  assert.match(text, /kết quả lệnh được xác nhận từ Job/);
  assert.match(text, /RAM VM: chưa có telemetry trực tiếp/);
  assert.doesNotMatch(text, /0 GB|VM đang chạy|Native Ready/);
  const html = fs.readFileSync(path.join(__dirname, '..', 'renderer', 'index.html'), 'utf8');
  for (const mode of ['native_first', 'native_only', 'isolated']) assert.ok(html.includes(`value="${mode}"`));
});

test('registration and automatic inventory refresh with exec selected never open Sandbox', async () => {
  const f = fixture();
  f.state.centralWorkspacePreset = 'code';
  f.context.reconcileControlPlaneAuthorityStatus = async (options) => {
    f.calls.push(['refresh-authority', plain(options)]);
    const selected = f.state.centralWorkspaceReceipt;
    if (selected) f.state.centralAuthorityStatus.targets = [{ workspace_id: selected.workspace_id,
      workspace_generation: selected.workspace_generation, dispatch_state: 'dispatchable',
      capabilities: { ...selected.capabilities } }];
  };
  const access = await f.context.applyCentralWorkspacePermissions();
  assert.equal(f.calls.filter(([name]) => name === 'register').length, 1);
  assert.equal(access.read, true);
  assert.equal(access.patch, true);
  assert.equal(access.exec, true);
  await f.context.refreshControlPlaneWorkspaces({ quiet: true });
  assert.equal(f.calls.some(([name]) => name === 'probe-sandbox'), false);
  assert.equal(f.calls.find(([name]) => name === 'install-exec')[1].probeSandbox, false);
  assert.ok(f.calls.filter(([name]) => name === 'inspect-exec').every(([, request]) => request.probeSandbox === false));
});

test('automatic authority continuation installs all permissions without opening Sandbox or repeating activation', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralAuthorityStatus.targets = [];
  await f.context.applyCentralWorkspacePermissions();
  f.state.centralAuthorityStatus.targets = [{ workspace_id: f.workspace.workspace_id,
    workspace_generation: f.workspace.workspace_generation, dispatch_state: 'dispatchable',
    capabilities: { ...f.workspace.capabilities } }];
  await f.runTimer();
  assert.equal(f.calls.filter(([name]) => name === 'install-files').length, 1);
  assert.equal(f.calls.some(([name]) => name === 'probe-sandbox'), false);
  assert.equal(f.calls.find(([name]) => name === 'install-exec')[1].probeSandbox, false);
  assert.equal(f.calls.filter(([name]) => name === 'activate').length, 1);
  assert.equal(f.state.setupContinuation, null);
  assert.match(f.state.setupContinuationMessage, /Đã xác minh policy/);
});

test('explicit Sandbox diagnostic after ordinary full permission setup probes once without reinstalling permission', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  await f.context.applyCentralWorkspacePermissions();
  const observation = await f.context.inspectControlPlaneExecPolicy(f.workspace, { probeSandbox: true });
  assert.equal(observation.sandbox.state, 'available');
  assert.equal(f.calls.filter(([name]) => name === 'install-files').length, 1);
  assert.equal(f.calls.filter(([name]) => name === 'probe-sandbox').length, 1);
  assert.equal(f.calls.filter(([name]) => name === 'install-exec').length, 1);
  assert.equal(f.confirmations.length, 2);
  assert.match(f.confirmations[1], /Mở Windows Sandbox/);
  const operations = f.calls.map(([name]) => name);
  assert.ok(operations.indexOf('install-exec') < operations.indexOf('probe-sandbox'));
});

test('a fresh existing exec policy remains authorized when the setup Sandbox receipt is absent or expired', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.setObservedFiles({ file_read: f.policy(f.hashes.read), approved_patch: f.policy(f.hashes.write) });
  f.setExecPolicy(f.policy(f.hashes.exec));
  const access = await f.context.applyCentralWorkspacePermissions();
  assert.equal(access.exec, true);
  assert.equal(access.sandbox.state, 'not_checked');
  assert.equal(f.calls.some(([name]) => name.startsWith('install-') || name === 'probe-sandbox'), false);
  assert.match(f.state.setupContinuationMessage, /Đã xác minh policy/);
  assert.equal(f.confirmations.length, 1);
});

test('declining the explicit exec confirmation performs only status inspection and never starts Sandbox', async () => {
  const f = fixture({ accepted: false });
  f.context.selectCentralWorkspace(f.workspace);
  assert.equal(await f.context.installControlPlaneExecPolicy(f.workspace), null);
  assert.equal(f.calls.filter(([name]) => name === 'inspect-exec').length, 1);
  assert.equal(f.calls.some(([name]) => name === 'probe-sandbox' || name.startsWith('install-')), false);
  assert.match(f.confirmations[0], /Native ProcessContainer xử lý metadata Git/);
});

test('advanced Sandbox inspection requires concrete confirmation before any probe request', async () => {
  const declined = fixture({ accepted: false });
  assert.equal(await declined.context.inspectControlPlaneExecPolicy(declined.workspace, { probeSandbox: true }), null);
  assert.deepEqual(declined.calls, []);
  assert.match(declined.confirmations[0], /Mở Windows Sandbox/);
  assert.match(declined.confirmations[0], /không chạy dự án hoặc cài quyền lệnh/);
  const accepted = fixture();
  await accepted.context.inspectControlPlaneExecPolicy(accepted.workspace, { probeSandbox: true });
  assert.equal(accepted.calls.filter(([name]) => name === 'probe-sandbox').length, 1);
  assert.equal(accepted.calls.some(([name]) => name.startsWith('install-')), false);
});

test('cancelling while an explicitly requested Sandbox probe is running prevents policy installation', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  const inspect = f.context.api.inspectControlPlaneExecPolicy;
  let finishProbe;
  f.context.api.inspectControlPlaneExecPolicy = (request) => {
    if (!request.probeSandbox) return inspect(request);
    f.calls.push(['probe-sandbox']);
    return new Promise((resolve) => { finishProbe = resolve; });
  };
  const pending = f.context.applyCentralWorkspacePermissions({ prepareExec: true });
  for (let attempt = 0; attempt < 100 && !finishProbe; attempt += 1) await Promise.resolve();
  assert.equal(typeof finishProbe, 'function');
  f.context.cancelSetupContinuation('Người dùng dừng kiểm tra Sandbox.');
  finishProbe({ policy: null, sandbox: { state: 'available', backend: 'windows_sandbox' } });
  assert.equal(await pending, null);
  assert.equal(f.calls.filter(([name]) => name === 'probe-sandbox').length, 1);
  assert.equal(f.calls.some(([name]) => name === 'install-exec'), false);
  assert.equal(f.state.centralExecBusy, false);
  assert.equal(f.context.setupWorkspaceAccess(f.workspace).exec, false);
});

test('cancelling setup consent performs no policy or registry mutation', async () => {
  const f = fixture({ accepted: false });
  f.context.selectCentralWorkspace(f.workspace);
  assert.equal(await f.context.applyCentralWorkspacePermissions({ prepareExec: true }), null);
  assert.equal(f.confirmations.length, 1);
  assert.deepEqual(f.calls, [['refresh-enrollment', { quiet: true }]]);
  assert.equal(f.state.centralPermissionBusy, false);
  assert.equal(f.state.setupContinuation, null);
  assert.equal(f.timers.size, 0);
});

test('a partial file policy installation reports its verified read scope and stops before enabling exec', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.context.api.installControlPlaneStandingFilePolicies = async (request) => {
    f.calls.push(['install-files', plain(request)]);
    return { state: 'read_only_partial', file_read: f.policy(f.hashes.read), error_code: 'WRITE_FAILED' };
  };
  f.setObservedFiles({ file_read: f.policy(f.hashes.read), approved_patch: null });
  await assert.rejects(f.context.applyCentralWorkspacePermissions({ prepareExec: true }), /Receipt và policy file chưa khớp/);
  assert.equal(f.calls.some(([name]) => name.includes('exec')), false);
  assert.equal(f.context.setupWorkspaceAccess(f.workspace).read, true);
  assert.equal(f.context.setupWorkspaceAccess(f.workspace).patch, false);
  assert.equal(f.state.setupContinuation, null);
  assert.equal(f.state.centralPermissionBusy, false);
});

test('unverified file policy hashes stop unified enable before exec', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  let inspections = 0;
  f.context.api.inspectControlPlaneStandingFilePolicies = async () => {
    f.calls.push(['inspect-files']);
    return ++inspections === 1 ? { file_read: null, approved_patch: null }
      : { file_read: f.policy('e'.repeat(64)), approved_patch: f.policy('f'.repeat(64)) };
  };
  await assert.rejects(f.context.applyCentralWorkspacePermissions({ prepareExec: true }), /Receipt và policy file chưa khớp/);
  assert.ok(f.messages.some(([title]) => title === 'Quyền file chưa hoàn tất'));
  assert.equal(f.calls.some(([name]) => name === 'install-exec'), false);
  assert.equal(f.state.setupContinuation, null);
});

test('missing, ambiguous or expired compact metadata contexts do not block standing file and exec setup', async () => {
  for (const code of ['CONTROL_PLANE_POLICY_ASSIGNMENT_MISSING', 'CONTROL_PLANE_POLICY_ASSIGNMENT_CONFLICT', 'CONTROL_PLANE_POLICY_ASSIGNMENT_EXPIRED']) {
    const f = fixture();
    f.context.selectCentralWorkspace(f.workspace);
    f.context.api.installControlPlaneReadOnlyPolicyAssignment = async (request) => {
      f.calls.push(['install-metadata', plain(request)]);
      throw new Error(code);
    };
    const access = await f.context.applyCentralWorkspacePermissions({ prepareExec: true });
    assert.equal(access.read, true, code);
    assert.equal(access.patch, true, code);
    assert.equal(access.exec, true, code);
    assert.equal(f.calls.some(([name]) => name === 'install-metadata'), false, code);
    assert.equal(f.calls.filter(([name]) => name === 'install-files').length, 1, code);
    assert.equal(f.calls.filter(([name]) => name === 'install-exec').length, 1, code);
    assert.equal(f.state.setupContinuation, null);
    assert.equal(f.timers.size, 0);
  }
});

test('current standing file and exec policies are observed without reinstalling or requiring compact metadata', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.setObservedFiles({ file_read: f.policy(f.hashes.read), approved_patch: f.policy(f.hashes.write) });
  f.setExecPolicy(f.policy(f.hashes.exec));
  delete f.context.api.installControlPlaneReadOnlyPolicyAssignment;
  const access = await f.context.applyCentralWorkspacePermissions({ prepareExec: true });
  assert.equal(access.read, true);
  assert.equal(access.patch, true);
  assert.equal(access.exec, true);
  assert.equal(f.calls.some(([name]) => name.startsWith('install-')), false);
  assert.equal(f.calls.filter(([name]) => name === 'inspect-exec').length, 1);
  assert.equal(f.calls.filter(([name]) => name === 'refresh-authority').length, 2);
  assert.equal(f.confirmations.length, 1);
  assert.equal(f.state.setupContinuation, null);
});

test('standing file installer authority rejection stops setup before any exec effect', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.context.api.installControlPlaneStandingFilePolicies = async (request) => {
    f.calls.push(['install-files', plain(request)]);
    throw new Error('CONTROL_PLANE_POLICY_AUTHORITY_TARGET_MISMATCH');
  };
  await assert.rejects(f.context.applyCentralWorkspacePermissions({ prepareExec: true }), /CONTROL_PLANE_POLICY_AUTHORITY_TARGET_MISMATCH/);
  assert.equal(f.calls.some(([name]) => name === 'install-metadata' || name.includes('exec')), false);
  assert.equal(f.state.setupContinuation, null);
  assert.doesNotMatch(f.state.setupContinuationMessage, /Đã xác minh policy cho quyền đã chọn/);
});

test('explicit compact metadata synchronization keeps its separate exact-scope consent and receipt', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  const receipt = await f.context.installControlPlaneReadOnlyPolicyAssignment(f.workspace);
  assert.equal(f.confirmations.length, 1);
  assert.match(f.confirmations[0], /policy read-only/);
  assert.deepEqual(f.calls.filter(([name]) => name.startsWith('install-')), [['install-metadata', {
    workspaceId: f.workspace.workspace_id, workspaceGeneration: f.workspace.workspace_generation,
    confirmInstall: true, replaceExisting: true
  }]]);
  assert.equal(f.state.centralPolicyReceipt.workspace_id, f.workspace.workspace_id);
  assert.equal(f.state.centralPolicyReceipt.workspace_generation, f.workspace.workspace_generation);
  assert.equal(f.state.centralPolicyReceipt.expires_at_ms, receipt.expires_at_ms);
});

test('a stale runtime signal stops before standing policy effects despite dispatchable authority', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.snapshot.status.signalStale = true;
  await assert.rejects(f.context.applyCentralWorkspacePermissions({ prepareExec: true }), /Trạng thái runtime đang cũ/);
  assert.equal(f.calls.some(([name]) => name.startsWith('install-')), false);
  assert.equal(f.state.setupContinuation, null);
});

test('unavailable Sandbox retains verified file access and stops before exec installation', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.setSandbox({ state: 'unavailable', reason: 'SANDBOX_NOT_ENABLED' });
  await assert.rejects(f.context.applyCentralWorkspacePermissions({ prepareExec: true }), /SANDBOX_NOT_ENABLED/);
  assert.equal(f.calls.some(([name]) => name === 'install-exec'), false);
  const access = f.context.setupWorkspaceAccess(f.workspace);
  assert.equal(access.read, true);
  assert.equal(access.patch, true);
  assert.equal(access.exec, false);
  assert.equal(f.state.setupContinuation, null);
});

test('mismatched exec receipt hash prevents setup completion even when Sandbox remains available', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.context.api.installControlPlaneExecPolicy = async (request) => {
    f.calls.push(['install-exec', plain(request)]);
    f.setExecPolicy(f.policy('e'.repeat(64)));
    return f.policy(f.hashes.exec);
  };
  await assert.rejects(f.context.applyCentralWorkspacePermissions({ prepareExec: true }), /Quyền đọc\/sửa đã xác minh/);
  assert.ok(f.messages.some(([title]) => title === 'Chưa xác minh được quyền chạy'));
  assert.equal(f.state.setupContinuation, null);
  assert.doesNotMatch(f.state.setupContinuationMessage, /Đã xác minh policy cho quyền đã chọn/);
  assert.equal(f.timers.size, 0);
});

test('cancelling while standing file observation is outstanding prevents subsequent policy effects', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  let resolveObservation;
  f.context.api.inspectControlPlaneStandingFilePolicies = () => {
    f.calls.push(['inspect-files']);
    return new Promise((resolve) => { resolveObservation = resolve; });
  };
  const pending = f.context.applyCentralWorkspacePermissions({ prepareExec: true });
  for (let attempt = 0; attempt < 30 && !resolveObservation; attempt += 1) await Promise.resolve();
  assert.equal(typeof resolveObservation, 'function');
  f.context.cancelSetupContinuation('Người dùng dừng đồng bộ.');
  resolveObservation({ file_read: null, approved_patch: null });
  assert.equal(await pending, null);
  assert.equal(f.calls.some(([name]) => name === 'install-files' || name === 'install-exec'), false);
  assert.equal(f.state.setupContinuation, null);
  assert.equal(f.timers.size, 0);
});

test('cancelling during exec status inspection prevents a later Sandbox probe or policy installation', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  let resolveProbe;
  f.context.api.inspectControlPlaneExecPolicy = (request) => {
    f.calls.push(['inspect-exec', plain(request)]);
    return new Promise((resolve) => { resolveProbe = resolve; });
  };
  const pending = f.context.applyCentralWorkspacePermissions({ prepareExec: true });
  for (let attempt = 0; attempt < 100 && !resolveProbe; attempt += 1) await Promise.resolve();
  assert.equal(typeof resolveProbe, 'function');
  assert.equal(f.state.centralExecBusy, true);
  f.context.cancelSetupContinuation('Người dùng dừng kiểm tra Sandbox.');
  resolveProbe({ policy: null, sandbox: { state: 'available', backend: 'windows_sandbox' } });
  assert.equal(await pending, null);
  assert.equal(f.calls.some(([name]) => name === 'install-exec'), false);
  assert.equal(f.state.centralExecBusy, false);
  assert.equal(f.state.setupContinuationBusy, false);
  assert.equal(f.state.setupContinuation, null);
  assert.equal(f.context.setupWorkspaceAccess(f.workspace).exec, false);
});

test('selecting and inspecting a root preserves independent exec observations for other roots', async () => {
  const f = fixture();
  const old = { ...f.workspace, workspace_id: 'workspace-old', workspace_generation: 'generation-old' };
  const oldKey = f.context.centralExecObservationKey(old);
  f.state.centralExecObservations[oldKey] = { policy: f.policy(f.hashes.exec, old), sandbox: { state: 'available' } };
  f.context.selectCentralWorkspace(f.workspace);
  assert.equal(f.state.centralExecObservations[oldKey].policy.workspace_id, old.workspace_id);
  f.setSandbox({ state: 'unavailable', reason: 'SANDBOX_NOT_ENABLED' });
  assert.equal(await f.context.installControlPlaneExecPolicy(f.workspace, { confirmationAccepted: true, probeSandbox: true }), null);
  assert.equal(f.state.centralExecObservations[oldKey].policy.workspace_id, old.workspace_id);
  assert.equal(f.context.setupWorkspaceAccess(old).exec, true);
  assert.equal(f.context.setupWorkspaceAccess(f.workspace).exec, false);
});

test('two dispatchable workspaces keep independent policy evidence while selection chooses only the new task destination', async () => {
  const f = fixture();
  f.workspace.workspace_path = 'E:\\DEV\\Codex-web';
  const other = { ...f.workspace, workspace_id: 'workspace-autocad', workspace_generation: 'generation-autocad',
    display_name: 'AutoCAD', workspace_path: 'E:\\DEV\\Autocad' };
  f.state.centralWorkspaces.push(other);
  f.state.centralAuthorityStatus.targets.push({ ...other, dispatch_state: 'dispatchable' });
  f.state.centralFileObservations = {};
  for (const workspace of [f.workspace, other]) {
    const key = f.context.centralExecObservationKey(workspace);
    f.state.centralFileObservations[key] = { status: 'loaded', policies: {
      file_read: f.policy(f.hashes.read, workspace), approved_patch: f.policy(f.hashes.write, workspace)
    } };
    f.state.centralExecObservations[key] = { policy: f.policy(f.hashes.exec, workspace) };
  }
  f.context.selectCentralWorkspace(f.workspace);
  assert.equal(f.context.centralActiveWorkspacePath(), f.workspace.workspace_path);
  f.context.selectCentralWorkspace(other);
  assert.equal(f.context.centralActiveWorkspacePath(), other.workspace_path);
  for (const workspace of [f.workspace, other]) {
    const access = f.context.setupWorkspaceAccess(workspace);
    assert.equal(access.read && access.patch && access.exec, true);
  }
  f.context.api.inspectControlPlaneStandingFilePolicies = async (request) => {
    assert.deepEqual(plain(request), { workspaceId: other.workspace_id, workspaceGeneration: other.workspace_generation });
    return f.state.centralFileObservations[f.context.centralExecObservationKey(other)].policies;
  };
  await f.context.refreshControlPlaneStandingFilePolicies();
  const newer = { ...other, workspace_generation: 'generation-newer' };
  assert.equal(f.context.setupWorkspaceAccess(newer).read, false);
  assert.equal(f.context.setupWorkspaceAccess(newer).exec, false);
  assert.equal(f.state.snapshot.settings.workspace, 'E:\\legacy-root');
});

test('a file inspection completing after a selection change caches its own target without overwriting the selected display', async () => {
  const f = fixture({ exec: false });
  const other = { ...f.workspace, workspace_id: 'workspace-autocad', workspace_generation: 'generation-autocad' };
  f.state.centralWorkspaces.push(other);
  f.context.selectCentralWorkspace(f.workspace);
  let finish;
  f.context.api.inspectControlPlaneStandingFilePolicies = () => new Promise((resolve) => { finish = resolve; });
  const pending = f.context.refreshControlPlaneStandingFilePolicies();
  f.context.selectCentralWorkspace(other);
  finish({ file_read: f.policy(f.hashes.read, f.workspace), approved_patch: f.policy(f.hashes.write, f.workspace) });
  await pending;
  assert.equal(f.state.centralFilePolicies, null);
  assert.equal(f.context.setupWorkspaceAccess(f.workspace).read, true);
  assert.equal(f.context.setupWorkspaceAccess(other).read, false);
});

test('capability loss at final authority recheck prevents a completed setup claim', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  let refreshes = 0;
  f.context.reconcileControlPlaneAuthorityStatus = async (options) => {
    f.calls.push(['refresh-authority', plain(options)]);
    if (++refreshes === 2) f.state.centralAuthorityStatus.targets[0].capabilities.exec = false;
  };
  await assert.rejects(f.context.applyCentralWorkspacePermissions({ prepareExec: true }), /Quyền Ubuntu đã hết hạn hoặc thay đổi/);
  assert.equal(f.calls.filter(([name]) => name === 'install-exec').length, 1);
  assert.equal(f.state.setupContinuation, null);
  assert.match(f.state.setupContinuationMessage, /Policy local được giữ/);
  assert.doesNotMatch(f.state.setupContinuationMessage, /Đã xác minh policy cho quyền đã chọn/);
});

test('compact metadata expiry during Sandbox preparation cannot expire verified standing setup', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  const metadata = { ...f.policy(f.hashes.metadata), enabled: true, expires_at_ms: Date.now() + 60_000 };
  f.context.api.installControlPlaneReadOnlyPolicyAssignment = async (request) => {
    f.calls.push(['install-metadata', plain(request)]);
    return metadata;
  };
  const originalInstall = f.context.api.installControlPlaneExecPolicy;
  f.context.api.installControlPlaneExecPolicy = async (request) => {
    metadata.expires_at_ms = Date.now() - 1;
    return originalInstall(request);
  };
  const access = await f.context.applyCentralWorkspacePermissions({ prepareExec: true });
  assert.equal(access.exec, true);
  assert.equal(f.calls.some(([name]) => name === 'install-metadata'), false);
  assert.equal(f.calls.filter(([name]) => name === 'install-exec').length, 1);
  assert.equal(f.state.setupContinuation, null);
  assert.match(f.state.setupContinuationMessage, /Đã xác minh policy cho quyền đã chọn/);
});

test('a stale selected generation fails before confirmation, replacement, or policy installation', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralWorkspaces = [{ ...f.workspace, workspace_generation: 'generation-newer' }];
  await assert.rejects(f.context.applyCentralWorkspacePermissions({ prepareExec: true }), /Đăng ký thư mục đã thay đổi/);
  assert.throws(() => f.context.selectCentralWorkspace(f.workspace), /Thư mục đã thay đổi/);
  assert.deepEqual(f.calls, [['refresh-enrollment', { quiet: true }]]);
  assert.deepEqual(f.confirmations, []);
});

test('an older inventory response cannot overwrite a newer completed refresh', async () => {
  const f = fixture();
  const pending = [];
  f.context.api.listControlPlaneWorkspaces = () => new Promise((resolve) => pending.push(resolve));
  const olderRefresh = f.context.refreshControlPlaneWorkspaces({ quiet: true });
  const newerRefresh = f.context.refreshControlPlaneWorkspaces({ quiet: true });
  assert.equal(pending.length, 2);
  const newer = [{ ...f.workspace, workspace_generation: 'generation-newer' }];
  pending[1](newer);
  await newerRefresh;
  assert.equal(f.state.centralWorkspaceListBusy, false);
  pending[0]([f.workspace]);
  assert.equal(await olderRefresh, null);
  assert.equal(f.state.centralWorkspaces, newer);
  assert.equal(f.state.centralWorkspaceInventoryStatus, 'loaded');
  assert.equal(f.state.centralWorkspaceListBusy, false);
});

test('inventory refresh refuses a workspace mutation except the explicit committed observation', async () => {
  const f = fixture();
  f.state.centralWorkspaceBusy = true;
  assert.equal(await f.context.refreshControlPlaneWorkspaces({ quiet: true }), null);
  assert.deepEqual(f.calls, []);
  assert.equal(f.state.centralWorkspaceInventoryRequest, 0);
  await f.context.refreshControlPlaneWorkspaces({ quiet: true, afterCommit: true });
  assert.equal(f.calls.filter(([name]) => name === 'list-workspaces').length, 1);
  assert.equal(f.state.centralWorkspaceInventoryStatus, 'loaded');
});

for (const mutation of ['register', 'replace']) {
  test(`${mutation} invalidates an earlier inventory read before observing its committed generation`, async () => {
    const f = fixture({ write: false, exec: false });
    let resolveOlder;
    let listCalls = 0;
    f.context.api.listControlPlaneWorkspaces = () => {
      listCalls += 1;
      if (listCalls === 1) return new Promise((resolve) => { resolveOlder = resolve; });
      return Promise.resolve([f.state.centralWorkspaceReceipt]);
    };
    const olderRefresh = f.context.refreshControlPlaneWorkspaces({ quiet: true });
    if (mutation === 'replace') {
      f.context.selectCentralWorkspace(f.workspace);
      f.context.chooseCentralWorkspacePreset('code');
      await f.context.replaceControlPlaneWorkspace(f.workspace);
    } else {
      await f.context.registerControlPlaneWorkspace();
    }
    assert.equal(f.state.centralWorkspaceSelection.workspace_generation, 'generation-new');
    assert.equal(listCalls, 2);
    assert.equal(f.state.centralWorkspaces[0].workspace_generation, 'generation-new');
    resolveOlder([f.workspace]);
    assert.equal(await olderRefresh, null);
    assert.equal(f.state.centralWorkspaces[0].workspace_generation, 'generation-new');
    assert.equal(f.state.centralWorkspaceInventoryStatus, 'loaded');
    assert.equal(f.state.centralWorkspaceBusy, false);
    assert.equal(f.state.centralWorkspaceListBusy, false);
  });
}
