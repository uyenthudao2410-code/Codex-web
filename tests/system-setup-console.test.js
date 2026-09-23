const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

function openConsoleHandler({ trusted = true, savedUrl = 'https://saved.tailnet.example' } = {}) {
  const source = read('electron/main.js');
  const start = source.indexOf("secureHandle('control-plane:open-console'");
  const end = source.indexOf("secureHandle('control-plane:enroll'", start);
  assert.ok(start >= 0 && end > start, 'control-plane console IPC fragment must exist');

  let handler;
  const opened = [];
  let settingsReads = 0;
  let settingsWrites = 0;
  vm.runInNewContext(source.slice(start, end), {
    secureHandle: (_name, value) => { handler = value; },
    invokeSafely: (action) => action(),
    assertManagerIpc: () => {
      if (!trusted) throw Object.assign(new Error('Manager required'), { code: 'MANAGER_REQUIRED' });
    },
    centralServerOrigin: (value) => {
      const { centralServerOrigin } = require('../electron/services/controlPlaneEnrollment');
      return centralServerOrigin(value);
    },
    settings: {
      load: () => { settingsReads += 1; return { controlPlaneServerUrl: savedUrl }; },
      save: () => { settingsWrites += 1; throw new Error('settings must not be written'); }
    },
    shell: { openExternal: async (url) => { opened.push(url); } }
  });
  return { handler, opened, get settingsReads() { return settingsReads; }, get settingsWrites() { return settingsWrites; } };
}

test('manager IPC opens only the normalized HTTPS Ubuntu root and has no write side effect', async () => {
  const fixture = openConsoleHandler();
  assert.equal(await fixture.handler({}, 'https://SVHOME.tail0e4032.ts.net/'), true);
  assert.deepEqual(fixture.opened, ['https://svhome.tail0e4032.ts.net/']);
  assert.equal(fixture.settingsReads, 0, 'explicit origin should not read settings');
  assert.equal(fixture.settingsWrites, 0);
});

test('manager IPC uses the saved origin only when no origin is supplied', async () => {
  const fixture = openConsoleHandler({ savedUrl: 'https://saved.tailnet.example/' });
  assert.equal(await fixture.handler({}, undefined), true);
  assert.deepEqual(fixture.opened, ['https://saved.tailnet.example/']);
  assert.equal(fixture.settingsReads, 1);
  assert.equal(fixture.settingsWrites, 0);
});

test('non-manager callers are rejected before settings or browser side effects', async () => {
  const fixture = openConsoleHandler({ trusted: false });
  await assert.rejects(fixture.handler({}), { code: 'MANAGER_REQUIRED' });
  assert.deepEqual(fixture.opened, []);
  assert.equal(fixture.settingsReads, 0);
  assert.equal(fixture.settingsWrites, 0);
});

test('console IPC rejects non-origin URLs, credentials, paths, queries and fragments', async () => {
  const fixture = openConsoleHandler();
  const invalid = [
    'http://svhome.tail0e4032.ts.net',
    'file:///C:/Windows/system32',
    'javascript:alert(1)',
    'https://operator:secret@svhome.tail0e4032.ts.net',
    'https://svhome.tail0e4032.ts.net/mcp',
    'https://svhome.tail0e4032.ts.net/?token=secret',
    'https://svhome.tail0e4032.ts.net/#fragment',
    ' '
  ];
  for (const value of invalid) {
    await assert.rejects(fixture.handler({}, value), { code: 'CONTROL_PLANE_SERVER_URL_INVALID' }, value);
  }
  assert.deepEqual(fixture.opened, []);
  assert.equal(fixture.settingsWrites, 0);
});

function enrollmentStatusHandler({ savedUrl = '', receipt, trusted = true } = {}) {
  const source = read('electron/main.js');
  const start = source.indexOf("secureHandle('control-plane:enrollment-status'");
  const end = source.indexOf("secureHandle('control-plane:authority-status'", start);
  assert.ok(start >= 0 && end > start, 'control-plane enrollment-status IPC fragment must exist');

  let handler;
  let currentSettings = { executionRole: 'central_executor', controlPlaneServerUrl: savedUrl };
  const settingsWrites = [];
  const reconciliations = [];
  vm.runInNewContext(source.slice(start, end), {
    secureHandle: (_name, value) => { handler = value; },
    invokeSafely: (action) => action(),
    assertManagerIpc: () => {
      if (!trusted) throw Object.assign(new Error('Manager required'), { code: 'MANAGER_REQUIRED' });
    },
    settings: {
      load: () => ({ ...currentSettings }),
      save: (patch) => {
        settingsWrites.push({ ...patch });
        currentSettings = { ...currentSettings, ...patch };
      }
    },
    controlPlaneEnrollment: {
      reconcileEnrollment: async (request) => {
        reconciliations.push(request);
        return receipt;
      }
    },
    loadOrCreateDeviceIdentity: () => ({ device_id: 'device-ipc-0001' }),
    runtimePaths: {}
  });
  return {
    handler,
    settingsWrites,
    reconciliations,
    get savedUrl() { return currentSettings.controlPlaneServerUrl; }
  };
}

test('enrollment-status IPC restores an empty Ubuntu origin from the durable receipt', async () => {
  const fixture = enrollmentStatusHandler({
    receipt: {
      device_id: 'device-ipc-0001',
      enrollment_id: 'enroll-ipc-0001',
      state: 'pending_operator_approval',
      server_origin: 'https://svhome.tail0e4032.ts.net'
    }
  });
  const result = await fixture.handler({});
  assert.equal(result.server_origin, 'https://svhome.tail0e4032.ts.net');
  assert.deepEqual(fixture.settingsWrites, [{ controlPlaneServerUrl: 'https://svhome.tail0e4032.ts.net' }]);
  assert.equal(fixture.savedUrl, 'https://svhome.tail0e4032.ts.net');
  assert.equal(fixture.reconciliations.length, 1);
  assert.equal(fixture.reconciliations[0].deviceIdentity.device_id, 'device-ipc-0001');
});

test('enrollment-status IPC never overwrites an explicitly configured Ubuntu origin', async () => {
  const fixture = enrollmentStatusHandler({
    savedUrl: 'https://configured.tailnet.example',
    receipt: {
      device_id: 'device-ipc-0001',
      enrollment_id: 'enroll-ipc-0001',
      state: 'approved',
      server_origin: 'https://different.tailnet.example'
    }
  });
  const result = await fixture.handler({});
  assert.equal(result.server_origin, 'https://different.tailnet.example');
  assert.deepEqual(fixture.settingsWrites, []);
  assert.equal(fixture.savedUrl, 'https://configured.tailnet.example');
});

function guidanceFunction() {
  const source = read('renderer/app.js');
  const start = source.indexOf('function centralSetupGuidance(');
  const end = source.indexOf('\nfunction centralSetupDevelopmentBlocked(', start);
  assert.ok(start >= 0 && end > start, 'central setup guidance function must exist');
  const context = {};
  vm.runInNewContext(source.slice(start, end), context);
  return context.centralSetupGuidance;
}

test('central setup guidance keeps development, stale authority and local runtime blockers distinct', () => {
  const guidance = guidanceFunction();
  const base = {
    current_ui_runtime: { mode: 'packaged', installation_id: 'a'.repeat(64) },
    recoveryHost: { electron_ui_recovery: { runtime_mode: 'packaged', recovery_host_runtime_mode: 'packaged', recovery_host_installation_id: 'a'.repeat(64) } },
    status: { centralConnected: true, authorityReady: false }
  };
  assert.equal(guidance({
    ...base,
    current_ui_runtime: { mode: 'development', installation_id: 'b'.repeat(64) },
    recoveryHost: { electron_ui_recovery: { runtime_mode: 'development', recovery_host_runtime_mode: 'development', recovery_host_installation_id: 'b'.repeat(64) } }
  }, { state: 'approved', fresh: true }, null).key, 'development');
  assert.equal(guidance({
    ...base,
    recoveryHost: { electron_ui_recovery: { runtime_mode: 'development', recovery_host_runtime_mode: 'development', recovery_host_installation_id: 'b'.repeat(64) } }
  }, { state: 'approved', fresh: true }, null).key, 'runtime-mismatch');
  assert.equal(guidance({
    ...base,
    current_ui_runtime: { mode: 'packaged' },
    recoveryHost: { electron_ui_recovery: { runtime_mode: 'packaged', recovery_host_runtime_mode: 'packaged' } },
    recovery_host_connection: { state: 'identity_unverified', code: 'RECOVERY_HOST_IDENTITY_UNVERIFIED' }
  }, { state: 'approved', fresh: true }, null).key, 'runtime-unverified');
  assert.equal(guidance({
    ...base,
    recovery_host_connection: { state: 'blocked', code: 'RECOVERY_HOST_INSTALLATION_MISMATCH' }
  }, { state: 'approved', fresh: true }, null).key, 'runtime-mismatch');
  assert.equal(guidance(base, { state: 'pending_operator_approval', fresh: true }, null).key, 'pending');
  assert.equal(guidance(base, { state: 'approved', fresh: true }, { state: 'active', fresh: false }).key, 'authority-stale');
  assert.equal(guidance({ ...base, status: { ...base.status, centralStatusReason: 'LOCAL_EXECUTOR_NOT_READY' } }, { state: 'approved', fresh: true }, { state: 'active', fresh: true }).key, 'local-executor');
  assert.equal(guidance({ ...base, status: { ...base.status, centralStatusReason: 'CENTRAL_LOCAL_POLICY_NOT_READY' } }, { state: 'approved', fresh: true }, { state: 'no_binding', fresh: true }).key, 'policy');
  assert.equal(guidance(base, { state: 'rejected', fresh: true }, null).key, 'unverified');
  assert.equal(guidance({ status: { centralConnected: false } }, null, null).key, 'runtime-unverified');
  assert.equal(guidance(base, { state: 'approved', fresh: false, error_code: 'CONTROL_PLANE_ENROLLMENT_RUNTIME_MISSING' }, null).key, 'runtime-missing');
});

test('central setup source preserves a single enrollment request and opens operator linking explicitly', () => {
  const app = read('renderer/app.js');
  assert.match(app, /state\.centralEnrollmentStatusChecked/);
  assert.match(app, /Máy đã có yêu cầu pairing đang lưu/);
  assert.match(app, /Mở quản trị & liên kết tài khoản/);
  assert.match(app, /await openControlPlaneConsole\(\)/);
});

function centralSetupReadyFixture(capabilities) {
  const source = read('renderer/app.js');
  const start = source.indexOf('function renderSetupState(snapshot)');
  const end = source.indexOf('\nasync function handleSetupPrimaryAction()', start);
  assert.ok(start >= 0 && end > start, 'setup renderer must exist');

  const elements = new Map();
  const element = (id) => {
    if (!elements.has(id)) {
      const small = { textContent: '' };
      const title = { textContent: id };
      elements.set(id, {
        textContent: '', dataset: {}, className: '',
        classList: { toggle: () => {} },
        querySelector: (selector) => selector === 'small' ? small : selector === 'b' ? title : null,
        setAttribute: () => {}, small
      });
    }
    return elements.get(id);
  };
  const target = { capabilities };
  const context = {
    state: {
      centralWorkspaceInventoryStatus: 'loaded',
      centralEnrollmentStatus: { fresh: true, state: 'approved' },
      centralAuthorityStatus: { fresh: true, state: 'active', dispatchable_target_count: 1 }
    },
    $: (selector) => element(selector.slice(1)),
    isCentralExecutor: () => true,
    centralWorkspaceEntries: () => [{ workspace_id: 'workspace-1', capabilities }],
    centralDispatchableTargetForLocalWorkspace: () => target,
    centralWorkspaceSummary: () => 'Codex-web',
    centralSetupGuidance: () => ({ title: 'Đã kết nối', detail: 'Đã xác nhận', action: 'workspace', actionLabel: 'Mở thư mục' })
  };
  vm.runInNewContext(source.slice(start, end), context);
  context.renderSetupState({
    settings: { executionRole: 'central_executor' },
    status: { centralConnected: true, authorityReady: true, fullyReady: true },
    environment: {}
  });
  return { element };
}

test('central setup ready text limits a read-only target to status and keeps file and command lanes unverified', () => {
  const fixture = centralSetupReadyFixture({ read: true, write: false, exec: false });
  assert.match(fixture.element('setupSummaryTitle').textContent, /target chỉ xem/);
  assert.equal(fixture.element('setupSummaryBadge').textContent, 'SẴN SÀNG · CHỈ XEM');
  assert.match(fixture.element('setupStepVerify').small.textContent, /kiểm tra trạng thái/);
  assert.match(fixture.element('setupSummaryText').textContent, /đọc file, sửa file và chạy lệnh từ ChatGPT cần policy và receipt riêng/);
});

test('central setup does not turn registered write and exec capabilities into ChatGPT execution proof', () => {
  const fixture = centralSetupReadyFixture({ read: true, write: true, exec: true });
  assert.equal(fixture.element('setupSummaryBadge').textContent, 'SẴN SÀNG');
  assert.match(fixture.element('setupSummaryText').textContent, /Quyền đọc file, sửa file và chạy lệnh từ ChatGPT cần policy và receipt riêng/);
  assert.doesNotMatch(fixture.element('setupStepVerify').small.textContent, /Sẵn sàng nhận việc/);
});

function navigationHarness() {
  const source = read('renderer/app.js');
  const start = source.indexOf('function navigate(page)');
  const end = source.indexOf('\nfunction textOr(', start);
  assert.ok(start >= 0 && end > start, 'navigate function must exist');

  const makeElement = (dataset = {}) => {
    const classes = new Set();
    return {
      dataset,
      classList: {
        toggle(name, force) { if (force) classes.add(name); else classes.delete(name); },
        contains(name) { return classes.has(name); }
      },
      setAttribute(name, value) { this[name] = value; },
      removeAttribute(name) { delete this[name]; },
      textContent: ''
    };
  };
  const navItems = ['overview', 'task', 'device', 'system'].map((page) => makeElement({ page }));
  const pages = ['overview', 'system', 'deploy', 'workspace', 'settings'].map((page) => makeElement({ pageView: page }));
  const setupLinks = ['deploy', 'workspace', 'settings'].map((page) => makeElement({ nav: page }));
  const bySelector = new Map([
    ['#pageEyebrow', makeElement()], ['#pageTitle', makeElement()], ['#pageSubtitle', makeElement()],
    ['.content-viewport', { scrollTop: 0 }]
  ]);
  const context = {
    pageMeta: {
      overview: ['OVERVIEW', 'Overview', 'Overview'], task: ['TASK', 'Task', 'Task'], device: ['DEVICE', 'Device', 'Device'],
      system: ['SYSTEM', 'System', 'System'], deploy: ['DEPLOY', 'Deploy', 'Deploy'], workspace: ['WORKSPACE', 'Workspace', 'Workspace'], settings: ['SETTINGS', 'Settings', 'Settings']
    },
    state: { currentPage: 'overview', snapshot: { settings: { executionRole: 'direct_legacy' } } },
    isCentralExecutor: () => false,
    document: { body: { dataset: {} } },
    location: { hash: '' },
    history: { replaceState: (_state, _title, value) => { context.location.hash = value.slice(1); } },
    $: (selector) => bySelector.get(selector),
    $$: (selector) => selector === '.nav-item' ? navItems : selector === '.page' ? pages : setupLinks
  };
  vm.createContext(context);
  vm.runInContext(source.slice(start, end), context);
  return { run: (page) => vm.runInContext(`navigate(${JSON.stringify(page)})`, context), context, navItems, pages };
}

test('system navigation opens the unified setup shell instead of silently redirecting to the old connection page', () => {
  const fixture = navigationHarness();
  fixture.run('system');
  assert.equal(fixture.context.state.currentPage, 'system');
  assert.equal(fixture.context.location.hash, 'system');
  assert.equal(fixture.context.document.body.dataset.setupView, 'system');
  const activePages = fixture.pages.filter((page) => page.classList.contains('active')).map((page) => page.dataset.pageView);
  assert.deepEqual(activePages, ['system']);
  assert.equal(fixture.navItems.find((item) => item.dataset.page === 'system').classList.contains('active'), true);
});

test('development central controls are visibly gated before action handlers run', () => {
  const app = read('renderer/app.js');
  assert.match(app, /key: 'runtime-unverified'/);
  assert.match(app, /centralSetupRuntimeBlocked/);
  assert.match(app, /workspaceChoose\.disabled = !central \|\| development/);
  assert.match(app, /workspaceRefresh\.disabled = !central \|\| development/);
  assert.match(app, /input\.disabled = !central \|\| development \|\| state\.busy/);
  assert.match(app, /centralSetupDevelopmentBlocked\(\)\) return null/);
  for (const action of ['Pairing Ubuntu', 'Chọn workspace Ubuntu', 'Đăng ký workspace Ubuntu', 'Đọc inventory workspace Ubuntu', 'Đồng bộ policy read-only']) {
    assert.match(app, new RegExp(`assertPackagedCentralSetup\\('${action}'\\)`));
  }
});
