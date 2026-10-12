const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'renderer', 'app.js'), 'utf8');
const plain = (value) => JSON.parse(JSON.stringify(value));

function fixture({ write = true, exec = true, accepted = true } = {}) {
  const workspace = {
    workspace_id: 'workspace-selected', workspace_generation: 'generation-current',
    display_name: 'Tools-Codex-web', capabilities: { read: true, write, exec }
  };
  const state = {
    snapshot: {
      settings: { executionRole: 'central_executor', workspace: 'E:\\legacy-root', controlPlaneServerUrl: 'https://control.example.test/' },
      device: { device_id: 'device-current', display_name: 'Máy hiện tại' },
      status: { signalStale: false, telemetryAvailable: true }
    },
    centralWorkspaces: [workspace], centralWorkspaceSelection: null,
    centralWorkspaceCandidate: 'E:\\old-picker-root', centralWorkspacePreset: 'read',
    centralWorkspaceCapabilities: { read: true, write: false, exec: false },
    centralWorkspaceBusy: false, centralPermissionBusy: false,
    centralWorkspaceInventoryRequest: 0, centralWorkspaceInventoryStatus: 'loaded',
    centralPolicyBusy: false, centralExecBusy: false, centralExecObservations: {},
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
  const policy = (hash, target = state.centralWorkspaceReceipt || workspace) => ({
    state: 'enabled', workspace_id: target.workspace_id,
    workspace_generation: target.workspace_generation, policy_sha256: hash
  });
  const hashes = { read: 'a'.repeat(64), write: 'b'.repeat(64), metadata: 'c'.repeat(64), exec: 'd'.repeat(64) };
  let observedFiles = { file_read: null, approved_patch: null };
  let preserveFileObservation = false;
  let execPolicy = null;
  let sandbox = { state: 'available', backend: 'windows_sandbox' };
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
    installControlPlaneStandingFilePolicies: async (request) => {
      calls.push(['install-files', plain(request)]);
      const receipt = { state: 'enabled', file_read: policy(hashes.read), approved_patch: request.allowWrite ? policy(hashes.write) : null };
      if (!preserveFileObservation) observedFiles = receipt;
      return receipt;
    },
    inspectControlPlaneStandingFilePolicies: async () => {
      calls.push(['inspect-files']);
      return observedFiles;
    },
    inspectControlPlaneExecPolicy: async (request) => {
      calls.push(['inspect-exec', plain(request)]);
      return { policy: execPolicy, sandbox };
    },
    installControlPlaneExecPolicy: async (request) => {
      calls.push(['install-exec', plain(request)]);
      execPolicy = policy(hashes.exec);
      return execPolicy;
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
      if (!elements.has(selector)) elements.set(selector, {
        checked: false, scrollIntoView() {}, focus() {}
      });
      return elements.get(selector);
    },
    isCentralExecutor: (settings) => settings?.executionRole === 'central_executor',
    assertPackagedCentralSetup() {}, unwrap: (value) => value,
    renderCentralExecutorMode() {
      context.$('#controlPlaneCapabilityWrite').checked = state.centralWorkspaceCapabilities.write === true;
      context.$('#controlPlaneCapabilityExec').checked = state.centralWorkspaceCapabilities.exec === true;
    },
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
    ['const CENTRAL_WORKSPACE_PRESETS', '// Central workspaces are deliberately separate'],
    ['function centralWorkspaceEntries', 'function centralWorkspaceSummary'],
    ['function centralWorkspaceCapabilitiesFromUi', 'function centralRoutePresentation'],
    ['async function registerControlPlaneWorkspace', 'async function refreshControlPlaneStandingFilePolicies'],
    ['async function refreshControlPlaneStandingFilePolicies', 'async function inspectControlPlaneExecPolicy'],
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
    setSandbox(value) { sandbox = value; },
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
  assert.equal(await f.context.applyCentralWorkspacePermissions(), null);
  assert.deepEqual(f.calls.filter(([name]) => name === 'replace'), [['replace', {
    workspaceId: 'workspace-selected', workspaceGeneration: 'generation-current',
    capabilities: { read: true, write: true, exec: true }, confirmReplace: true
  }]]);
  assert.equal(f.calls.some(([name]) => ['choose', 'install-files', 'install-exec'].includes(name)), false);
  assert.equal(f.confirmations.length, 2);
  assert.match(f.confirmations[0], /Liên kết và tác vụ.*bị đóng/);
  assert.match(f.confirmations[1], /Hoàn tất thiết lập/);
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
  assert.equal(await f.context.applyCentralWorkspacePermissions(), null);
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
  assert.equal(await f.context.applyCentralWorkspacePermissions(), null);
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
  await f.context.applyCentralWorkspacePermissions();
  assert.deepEqual(f.calls.find(([name]) => name === 'refresh-authority'), ['refresh-authority', { quiet: true }]);
  assert.equal(f.confirmations.length, 1);
  assert.equal(f.calls.some(([name]) => name === 'install-exec'), true);
});

test('fresh but inactive authority does not reuse a retained dispatchable target or auto-open Console', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralAuthorityStatus.state = 'unknown';
  assert.equal(f.context.centralWorkspaceTarget(f.workspace), null);
  assert.equal(await f.context.applyCentralWorkspacePermissions(), null);
  assert.equal(f.calls.some(([name]) => name.startsWith('install-') || name === 'console'), false);
  assert.equal(f.calls.filter(([name]) => name === 'refresh-authority').length, 1);
  assert.equal(f.confirmations.length, 1);
  assert.equal(f.timers.size, 1);
});

test('pending owner authority resumes on the 15 second check using the same in-memory consent', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralAuthorityStatus.targets = [];
  await f.context.applyCentralWorkspacePermissions();
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
  assert.equal(await f.context.applyCentralWorkspacePermissions(), null);
  assert.equal(f.calls.some(([name]) => name.startsWith('install-')), false);
  assert.equal(f.timers.size, 1);
});

test('dispatchable binding without every selected capability remains pending before local effects', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralAuthorityStatus.targets[0].capabilities.exec = false;
  assert.equal(await f.context.applyCentralWorkspacePermissions(), null);
  assert.equal(f.calls.some(([name]) => name.startsWith('install-')), false);
  assert.equal(f.timers.size, 1);
  assert.equal(f.confirmations.length, 1);
});

test('cancelling pending setup clears the timer and a later authority observation cannot install policies', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.state.centralAuthorityStatus.targets = [];
  await f.context.applyCentralWorkspacePermissions();
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
    await f.context.applyCentralWorkspacePermissions();
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
  await f.context.applyCentralWorkspacePermissions();
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
    assert.equal(await f.context.applyCentralWorkspacePermissions(), null);
    assert.equal(f.calls.some(([name]) => name.startsWith('install-') || ['choose', 'register', 'replace'].includes(name)), false);
    assert.equal(f.confirmations.length, 0);
    assert.equal(f.state.setupContinuation, null);
    assert.ok(f.calls.some(([name]) => name === 'navigate'));
  }
});

test('standing setup confirms local scope once and verifies files before installing exec without compact assignment', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  const access = await f.context.applyCentralWorkspacePermissions();
  assert.equal(f.confirmations.length, 1);
  assert.match(f.confirmations[0], /Hoàn tất thiết lập.*Máy hiện tại/);
  assert.match(f.confirmations[0], /Quyền đã chọn/);
  assert.match(f.confirmations[0], /sandbox/);
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
  assert.deepEqual(plain(access), { read: true, patch: true, exec: true, sandbox: { state: 'available', backend: 'windows_sandbox' } });
});

test('cancelling setup consent performs no policy or registry mutation', async () => {
  const f = fixture({ accepted: false });
  f.context.selectCentralWorkspace(f.workspace);
  assert.equal(await f.context.applyCentralWorkspacePermissions(), null);
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
  await assert.rejects(f.context.applyCentralWorkspacePermissions(), /Receipt và policy file chưa khớp/);
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
  await assert.rejects(f.context.applyCentralWorkspacePermissions(), /Receipt và policy file chưa khớp/);
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
    const access = await f.context.applyCentralWorkspacePermissions();
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
  const access = await f.context.applyCentralWorkspacePermissions();
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
  await assert.rejects(f.context.applyCentralWorkspacePermissions(), /CONTROL_PLANE_POLICY_AUTHORITY_TARGET_MISMATCH/);
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
  await assert.rejects(f.context.applyCentralWorkspacePermissions(), /Trạng thái runtime đang cũ/);
  assert.equal(f.calls.some(([name]) => name.startsWith('install-')), false);
  assert.equal(f.state.setupContinuation, null);
});

test('unavailable Sandbox retains verified file access and stops before exec installation', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  f.setSandbox({ state: 'unavailable', reason: 'SANDBOX_NOT_ENABLED' });
  await assert.rejects(f.context.applyCentralWorkspacePermissions(), /SANDBOX_NOT_ENABLED/);
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
  await assert.rejects(f.context.applyCentralWorkspacePermissions(), /Quyền đọc\/sửa đã xác minh/);
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
  const pending = f.context.applyCentralWorkspacePermissions();
  for (let attempt = 0; attempt < 30 && !resolveObservation; attempt += 1) await Promise.resolve();
  assert.equal(typeof resolveObservation, 'function');
  f.context.cancelSetupContinuation('Người dùng dừng đồng bộ.');
  resolveObservation({ file_read: null, approved_patch: null });
  assert.equal(await pending, null);
  assert.equal(f.calls.some(([name]) => name === 'install-files' || name === 'install-exec'), false);
  assert.equal(f.state.setupContinuation, null);
  assert.equal(f.timers.size, 0);
});

test('cancelling during the actual exec helper Sandbox probe prevents exec policy installation', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  let resolveProbe;
  f.context.api.inspectControlPlaneExecPolicy = (request) => {
    f.calls.push(['inspect-exec', plain(request)]);
    return new Promise((resolve) => { resolveProbe = resolve; });
  };
  const pending = f.context.applyCentralWorkspacePermissions();
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

test('selecting a root invalidates prior exec observations and probing a new root evicts other-root policy state', async () => {
  const f = fixture();
  const old = { ...f.workspace, workspace_id: 'workspace-old', workspace_generation: 'generation-old' };
  const oldKey = f.context.centralExecObservationKey(old);
  f.state.centralExecObservations[oldKey] = { policy: f.policy(f.hashes.exec, old), sandbox: { state: 'available' } };
  f.context.selectCentralWorkspace(f.workspace);
  assert.equal(f.state.centralExecObservations[oldKey], undefined);
  f.state.centralExecObservations[oldKey] = { policy: f.policy(f.hashes.exec, old), sandbox: { state: 'available' } };
  f.setSandbox({ state: 'unavailable', reason: 'SANDBOX_NOT_ENABLED' });
  assert.equal(await f.context.installControlPlaneExecPolicy(f.workspace, { confirmationAccepted: true }), null);
  assert.equal(f.state.centralExecObservations[oldKey], undefined);
  assert.equal(f.context.setupWorkspaceAccess(old).exec, false);
  assert.equal(f.context.setupWorkspaceAccess(f.workspace).exec, false);
});

test('capability loss at final authority recheck prevents a completed setup claim', async () => {
  const f = fixture();
  f.context.selectCentralWorkspace(f.workspace);
  let refreshes = 0;
  f.context.reconcileControlPlaneAuthorityStatus = async (options) => {
    f.calls.push(['refresh-authority', plain(options)]);
    if (++refreshes === 2) f.state.centralAuthorityStatus.targets[0].capabilities.exec = false;
  };
  await assert.rejects(f.context.applyCentralWorkspacePermissions(), /Quyền Ubuntu đã hết hạn hoặc thay đổi/);
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
  const access = await f.context.applyCentralWorkspacePermissions();
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
  await assert.rejects(f.context.applyCentralWorkspacePermissions(), /Đăng ký thư mục đã thay đổi/);
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
