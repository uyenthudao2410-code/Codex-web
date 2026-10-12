const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

function sectionByAttribute(html, attribute) {
  const start = html.indexOf(`<section ${attribute}`);
  assert.ok(start >= 0, `section ${attribute} must exist`);
  const tags = /<section\b[^>]*>|<\/section>/g;
  tags.lastIndex = start;
  let depth = 0;
  for (let match = tags.exec(html); match; match = tags.exec(html)) {
    depth += match[0].startsWith('</') ? -1 : 1;
    if (depth === 0) return html.slice(start, tags.lastIndex);
  }
  assert.fail(`section ${attribute} must close`);
}

test('Settings has one obvious entry and a resumable four-step setup surface', () => {
  const html = read('renderer/index.html');
  assert.match(html, /data-page="system"[^>]*>.*?<span>Cài đặt<\/span>/s);
  assert.match(html, /id="setupSummary"/);
  for (const id of ['setupStepConnection', 'setupStepFolder', 'setupStepAccount', 'setupStepVerify']) {
    assert.match(html, new RegExp(`id="${id}"`));
  }
  assert.match(html, /<b>Liên kết tài khoản<\/b>/);
  for (const id of ['settingsConnectionSummary', 'settingsWorkspaceSummary', 'settingsAppSummary']) {
    assert.match(html, new RegExp(`id="${id}"`));
  }
});

test('Preferences expose per-field save feedback instead of saving the whole form', () => {
  const html = read('renderer/index.html');
  const app = read('renderer/app.js');
  for (const field of ['theme', 'startWithWindows', 'autoStartServices', 'keepRunningOnClose', 'progressReportSeconds']) {
    assert.match(html, new RegExp(`data-setting-state="${field}"`));
  }
  assert.match(app, /async function savePreference\(field, value\)/);
  assert.match(app, /savePreference\('startWithWindows'/);
  assert.match(app, /savePreference\('progressReportSeconds'/);
  assert.match(app, /state\.snapshot\.settings = \{ \.\.\.state\.snapshot\.settings, \.\.\.saved \}/);
});

test('Common settings stay compact and technical controls are in a collapsed disclosure', () => {
  const html = read('renderer/index.html');
  const sectionStart = html.indexOf('<section class="page" data-page-view="settings">');
  const sectionEnd = html.indexOf('</section>', sectionStart);
  assert.ok(sectionStart >= 0 && sectionEnd > sectionStart, 'settings page must exist');
  const page = html.slice(sectionStart, sectionEnd);
  const advancedStart = page.indexOf('<details class="setup-support settings-advanced">');
  assert.ok(advancedStart > 0, 'advanced controls must use a native disclosure');
  const common = page.slice(0, advancedStart);
  const advanced = page.slice(advancedStart, page.indexOf('</details>', advancedStart));
  const disclosureTag = page.match(/<details class="setup-support settings-advanced"[^>]*>/)?.[0] || '';

  for (const id of ['themeSelect', 'startWithWindowsToggle', 'autoStartToggle', 'keepRunningToggle']) {
    assert.match(common, new RegExp(`id="${id}"`), `${id} should stay in common settings`);
  }
  for (const id of ['progressReportSelect', 'removeRuntimeKey', 'regenerateToken']) {
    assert.doesNotMatch(common, new RegExp(`id="${id}"`), `${id} should not crowd common settings`);
    assert.match(advanced, new RegExp(`id="${id}"`), `${id} should remain available under advanced settings`);
  }
  assert.doesNotMatch(common, /smart-v3|about-panel/);
  assert.match(advanced, /smart-v3[\s\S]*?about-panel/);
  assert.match(disclosureTag, /^<details\b/);
  assert.doesNotMatch(disclosureTag, /\bopen\b/, 'advanced settings must start collapsed');
});

test('Connection, folder and execution controls share one setup page without duplicate forms', () => {
  const html = read('renderer/index.html');
  const system = sectionByAttribute(html, 'class="page" data-page-view="system"');
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map((match) => match[1]);
  assert.equal(new Set(ids).size, ids.length, 'DOM IDs must stay unique');
  const sections = ['setupConnectionSection', 'setupFolderSection', 'setupExecutionSection'];
  const positions = sections.map((id) => system.indexOf(`id="${id}"`));
  assert.ok(positions.every((position) => position >= 0));
  assert.ok(positions[0] < positions[1] && positions[1] < positions[2], 'setup must follow connection, scope, execution order');

  for (const id of ['controlPlaneServerUrl', 'requestControlPlaneEnrollment', 'openControlPlaneConsole', 'controlPlaneAuthorityStatusCard']) {
    assert.match(system.slice(positions[0], positions[1]), new RegExp(`id="${id}"`));
  }
  for (const id of ['controlPlaneWorkspaceRegistrations', 'chooseControlPlaneWorkspace', 'registerControlPlaneWorkspace', 'controlPlaneCapabilityExec']) {
    assert.match(system.slice(positions[1], positions[2]), new RegExp(`id="${id}"`));
  }
  for (const id of ['setupExecutionChecklist', 'setupReadCheck', 'setupPatchCheck', 'setupExecCheck', 'setupContinueAction', 'setupContinueStatus', 'setupCancelContinuation']) {
    assert.match(system.slice(positions[2]), new RegExp(`id="${id}"`));
  }
  assert.match(system, /id="setupContinueStatus"[^>]*role="status"/);
  assert.doesNotMatch(html, /data-page-view="(?:deploy|workspace)"/);
  assert.match(system, /data-nav="deploy"/);
  assert.match(system, /data-nav="workspace"/);
  assert.match(system, /data-nav="settings"/);
});

test('Execution setup starts unverified and legacy credentials stay in a collapsed disclosure', () => {
  const html = read('renderer/index.html');
  const system = sectionByAttribute(html, 'class="page" data-page-view="system"');
  for (const id of ['setupReadCheck', 'setupPatchCheck', 'setupExecCheck']) {
    assert.match(system, new RegExp(`id="${id}" data-state="unknown"`));
  }
  const legacyStart = system.indexOf('<details class="setup-legacy"');
  const legacy = system.slice(legacyStart);
  assert.ok(legacyStart > 0);
  assert.doesNotMatch(legacy.match(/^<details[^>]*>/)[0], /\bopen\b/);
  for (const id of ['runtimeKeyInput', 'tunnelIdInput', 'proxyModeSelect', 'mcpPortInput', 'saveWorkspaceRestart']) {
    assert.doesNotMatch(system.slice(0, legacyStart), new RegExp(`id="${id}"`));
    assert.match(legacy, new RegExp(`id="${id}"`));
  }
  assert.match(html, /id="executionWorkspaceLabel"/);
  assert.match(html, /id="executionAccessSummary"/);
  assert.match(html, /id="executionNextAction"/);
});

test('Changing the theme applies it immediately and saves only the theme preference', async () => {
  const app = read('renderer/app.js').replace(/\r\n/g, '\n');
  const applyStart = app.indexOf('function applyTheme(theme) {');
  const applyEnd = app.indexOf('\n}\n', applyStart) + 3;
  const bindStart = app.indexOf('function bindThemePreferenceControl() {');
  const bindEnd = app.indexOf('\n}\n', bindStart) + 3;
  assert.ok(applyStart >= 0 && applyEnd > applyStart, 'applyTheme must exist');
  assert.ok(bindStart >= 0 && bindEnd > bindStart, 'theme change binding must exist');
  const bindEventsStart = app.indexOf('function bindEvents() {');
  assert.ok(bindEventsStart >= 0, 'bindEvents must exist');
  assert.match(app.slice(bindEventsStart), /bindThemePreferenceControl\(\);/);

  const themeSelect = {
    value: 'light',
    listener: null,
    addEventListener(eventName, listener) {
      assert.equal(eventName, 'change');
      this.listener = listener;
    }
  };
  const body = { dataset: {} };
  const saved = [];
  const context = {
    $: (selector) => selector === '#themeSelect' ? themeSelect : null,
    document: { body, documentElement: { dataset: {} } },
    savePreference: async (field, value) => { saved.push([field, value]); }
  };
  vm.runInNewContext(`${app.slice(applyStart, applyEnd)}\n${app.slice(bindStart, bindEnd)}`, context);

  context.bindThemePreferenceControl();
  themeSelect.value = 'dark';
  await themeSelect.listener();

  assert.equal(body.dataset.theme, 'dark');
  assert.equal(context.document.documentElement.dataset.theme, 'dark');
  assert.equal(themeSelect.value, 'dark');
  assert.deepEqual(saved, [['theme', 'dark']]);
  themeSelect.value = 'light';
  await themeSelect.listener();
  assert.equal(body.dataset.theme, 'light');
  assert.equal(context.document.documentElement.dataset.theme, 'light');
});

test('Static preview preserves the theme selected by theme-bootstrap', () => {
  const app = read('renderer/app.js');
  assert.match(app, /theme:\s*document\.body\.dataset\.theme === 'dark' \? 'dark' : 'light'/);
});

test('Central setup never labels a read-only inspection as executor start', () => {
  const app = read('renderer/app.js');
  assert.match(app, /central \? 'Mở kết nối Ubuntu'/);
  assert.match(app, /central \? 'Liên kết & quyền' : 'Kiểm tra kết nối'/);
  assert.match(app, /Đã có target được cấp/);
  assert.match(app, /reconcileControlPlaneAuthorityStatus/);
  assert.match(app, /isCentralExecutor\(state\.snapshot\?\.settings\)\s*\? navigate\('system'\)/);
  assert.doesNotMatch(app, /central \? 'Kiểm tra Executor'/);
});

test('Central route guidance separates local runtime failure from pairing and stale heartbeat', () => {
  const app = read('renderer/app.js').replace(/\r\n/g, '\n');
  const start = app.indexOf('function centralRoutePresentation(status = {}) {');
  const end = app.indexOf('\nfunction centralSetupGuidance', start);
  assert.ok(start >= 0 && end > start, 'central route presentation must exist');
  const present = vm.runInNewContext(`${app.slice(start, end)}\ncentralRoutePresentation`);

  const localRuntime = present({ centralConnected: false, authorityReady: false, centralStatusReason: 'LOCAL_EXECUTOR_NOT_READY' });
  assert.equal(localRuntime.label, 'Runtime Windows chưa sẵn sàng');
  assert.match(localRuntime.detail, /không gửi pairing lại/);
  assert.doesNotMatch(localRuntime.label, /pairing/i);

  const staleHeartbeat = present({ centralConnected: false, authorityReady: false, centralStatusReason: 'CENTRAL_ROUTE_EVIDENCE_STALE' });
  assert.equal(staleHeartbeat.label, 'Heartbeat Ubuntu đã cũ');
  assert.match(staleHeartbeat.detail, /không pairing lại/);
});

test('Authority UI distinguishes a dispatchable binding from an online, ready executor', () => {
  const app = read('renderer/app.js').replace(/\r\n/g, '\n');
  const start = app.indexOf('function authorityStatusPresentation(status) {');
  const end = app.indexOf('\nfunction renderCentralAuthorityStatus', start);
  assert.ok(start >= 0 && end > start, 'authority presentation helpers must exist');
  const helpers = vm.runInNewContext(`${app.slice(start, end)}\n({ authorityStatusPresentation, authorityTargetPresentation });`);
  const targetText = helpers.authorityTargetPresentation({
    capabilities: { read: true, write: true, exec: false },
    dispatch_state: 'dispatchable',
    presence_state: 'offline',
    readiness: 'degraded',
    policy_state: 'unobserved'
  });
  assert.equal(targetText, 'Đọc/Ghi · liên kết/thư mục còn hiệu lực · máy ngoại tuyến · runtime chưa sẵn sàng đầy đủ · policy chưa được xác minh cùng heartbeat mới nhất');

  const active = helpers.authorityStatusPresentation({
    fresh: true,
    state: 'active',
    dispatchable_target_count: 1
  });
  assert.match(active.detail, /không xác nhận máy online, runtime sẵn sàng hoặc policy còn hạn/);
});

test('Central target readiness fails closed on stale authority, offline/degraded runtime, and non-enabled policy', () => {
  const app = read('renderer/app.js').replace(/\r\n/g, '\n');
  const start = app.indexOf('function centralTargetReadiness(status, target) {');
  const end = app.indexOf('\nfunction centralWorkspaceCapabilitiesFromUi', start);
  assert.ok(start >= 0 && end > start, 'central target readiness predicate must exist');
  const ready = vm.runInNewContext(`${app.slice(start, end)}\ncentralTargetReadiness`, {
    authorityStatusPresentation: (status) => ({ label: status.state, detail: `authority=${status.state}` })
  });
  const authority = { fresh: true, state: 'active', dispatchable_target_count: 1 };
  const target = {
    dispatch_state: 'dispatchable', presence_state: 'online', readiness: 'ready', policy_state: 'enabled'
  };
  assert.equal(ready(authority, target).ready, true);
  assert.equal(ready({ ...authority, fresh: false }, target).state, 'status_stale');
  assert.equal(ready(authority, { ...target, presence_state: 'offline' }).state, 'offline');
  assert.equal(ready(authority, { ...target, readiness: 'degraded' }).state, 'runtime_degraded');
  assert.equal(ready(authority, { ...target, readiness: 'blocked' }).state, 'runtime_blocked');
  assert.equal(ready(authority, { ...target, policy_state: 'expired_or_disabled' }).state, 'policy_expired');
  assert.equal(ready(authority, { ...target, policy_state: 'unobserved' }).state, 'policy_unobserved');
  assert.equal(ready(authority, { ...target, policy_state: 'unavailable' }).state, 'policy_unavailable');
  assert.equal(ready(authority, null).state, 'workspace_target_mismatch');
});

test('System setup is the only primary settings entry and preferences remain subordinate', () => {
  const html = read('renderer/index.html');
  const nav = html.match(/<nav class="nav-list"[\s\S]*?<\/nav>/)?.[0] || '';
  assert.match(nav, /data-page="system"[^>]*>[\s\S]*?Cài đặt/);
  assert.doesNotMatch(nav, /data-page="(?:deploy|workspace|settings)"/);
  for (const page of ['deploy', 'workspace']) {
    assert.match(html, new RegExp(`class="setup-section-link" data-nav="${page}"`));
  }
  assert.match(html, /class="setup-preferences-link"[\s\S]*?data-nav="settings"/);
});

test('Central workspace setup uses understandable presets and keeps opaque IDs out of normal UI', () => {
  const html = read('renderer/index.html');
  const app = read('renderer/app.js');
  for (const preset of ['read', 'code', 'custom']) {
    assert.match(html, new RegExp(`name="centralWorkspacePreset" value="${preset}"`));
  }
  assert.match(html, /<b>Chỉ xem<\/b>/);
  assert.match(html, /<b>Làm việc với mã nguồn<\/b>/);
  assert.match(html, /id="centralWorkspaceCustomCapabilities"/);
  assert.match(app, /centralWorkspaceCapabilityLabel/);
  assert.doesNotMatch(app, /workspace\.workspace_id\.slice\(-8\)/);
  assert.doesNotMatch(app, /workspace\.workspace_generation\.slice\(-8\)/);
});

test('Central wizard resumes from the registered Ubuntu inventory, not legacy direct workspace settings', () => {
  const app = read('renderer/app.js');
  assert.match(app, /function centralWorkspaceEntries\(\)/);
  assert.match(app, /function centralDispatchableTargetForLocalWorkspace\(\)/);
  assert.match(app, /const workspaceReady = central\s*\?\s*inventoryKnown && centralWorkspaceEntries\(\)\.length > 0/);
  assert.match(app, /centralWorkspaceInventoryStatus/);
  assert.match(app, /const currentTarget = central \? centralDispatchableTargetForLocalWorkspace\(\) : null;[\s\S]*?const targetReadiness = central \? centralTargetReadiness\(authorityStatus, currentTarget\) : null/);
  assert.match(app, /centralWorkspaceSummary\(\)/);
  assert.match(app, /if \(isCentralExecutor\(state\.snapshot\?\.settings\)\) await chooseControlPlaneWorkspace\(\);/);
  assert.match(app, /action\.dataset\.setupAction[\s\S]*?\? 'account'/);
  assert.match(app, /card\.scrollIntoView\(\{ behavior: 'smooth', block: 'start' \}\)/);
});

test('Central setup rehydrates local workspace inventory after reopening the window', () => {
  const app = read('renderer/app.js');
  assert.match(app, /await reconcileControlPlaneAuthorityStatus\(\{ quiet: true \}\);[\s\S]*?await refreshControlPlaneWorkspaces\(\{ quiet: true \}\)/);
  assert.match(app, /Chưa liên kết tài khoản/);
  assert.match(app, /Đã liên kết/);
});

test('Central setup keeps enrollment resume metadata and inventory failures truthful', () => {
  const app = read('renderer/app.js');
  const nodeAgent = read('control-plane/control_plane/node_agent.py');
  assert.match(app, /status\.server_origin/);
  assert.match(app, /Máy đã có yêu cầu pairing đang lưu/);
  assert.match(app, /workspace-refresh/);
  assert.match(app, /Không đọc được inventory workspace/);
  assert.match(app, /RUNTIME_MISSING/);
  assert.match(nodeAgent, /"server_origin": server_origin/);
});

test('Central connection page hides direct-mode network and deployment controls', () => {
  const html = read('renderer/index.html');
  const app = read('renderer/app.js');
  assert.match(html, /id="centralExecutorNotice"/);
  assert.match(html, /<article class="panel" data-direct-only>[\s\S]*?Mạng & Proxy/);
  assert.match(html, /class="deploy-footer panel accent-panel" data-direct-only/);
  assert.match(html, /class="step-pill" data-direct-only/);
  assert.match(app, /deployTitle\.textContent = central \? 'Kết nối máy chủ Ubuntu'/);
});

test('Central setup supports personal ChatGPT without Business IDs or mandatory OAuth', () => {
  const html = read('renderer/index.html');
  const app = read('renderer/app.js');
  const centralStart = html.indexOf('<div id="centralExecutorNotice"');
  const centralEnd = html.indexOf('id="setupFolderSection"', centralStart);
  assert.ok(centralStart >= 0 && centralEnd > centralStart);
  const centralSetup = html.slice(centralStart, centralEnd);
  assert.match(centralSetup, /id="personalChatGptConnectionHelp"/);
  assert.match(centralSetup, /ChatGPT cá nhân/);
  assert.match(centralSetup, /dùng app Ubuntu Control Plane đã kết nối/);
  assert.match(centralSetup, /không cần Organization ID hoặc ChatGPT Workspace ID/);
  assert.match(centralSetup, /Quyền từng thao tác do Ubuntu quyết định/);
  assert.match(centralSetup, /data-nav="guide">Cách dùng trong ChatGPT Plus/);
  assert.doesNotMatch(centralSetup, /<input\b[^>]*(?:organization|chatgptWorkspace|tunnelId|runtimeKey)/i);
  assert.match(html, /id="centralExecutorGuide"[^>]*>[\s\S]*?ChatGPT web[\s\S]*?Developer mode\/Apps[\s\S]*?workspace_context[\s\S]*?inventory[\s\S]*?bấm Refresh[\s\S]*?Quy trình này không cần gói Business, Organization ID, ChatGPT Workspace ID hoặc cài Codex Desktop/);
  assert.match(html, /id="guideSectionTitle"/);
  assert.doesNotMatch(html, /liên kết tài khoản OAuth và chọn root/);
  assert.doesNotMatch(app, /account OAuth chọn target|Cả hai thành viên ChatGPT Business/);
  assert.match(app, /service principal của tunnel không phân biệt người ChatGPT gọi/);
});

test('The last Ubuntu origin is an ordinary setting, not a credential or context id', () => {
  const config = read('electron/services/config.js');
  const main = read('electron/main.js');
  const app = read('renderer/app.js');
  assert.match(config, /controlPlaneServerUrl: ''/);
  assert.match(main, /settings\.save\(\{ controlPlaneServerUrl: receipt\.server_origin \}\)/);
  assert.match(app, /settings\.controlPlaneServerUrl/);
  assert.doesNotMatch(app, /controlPlaneServerUrl.*ctx_/);
  assert.match(app, /controlPlaneServerUrl: central && controlPlaneField/);
});
