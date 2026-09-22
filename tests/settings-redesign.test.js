const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

test('Settings has one obvious entry and a resumable four-step setup surface', () => {
  const html = read('renderer/index.html');
  assert.match(html, /data-page="system"[^>]*>.*?<span>Thiết lập hệ thống<\/span>/s);
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

test('Central setup never labels a read-only inspection as executor start', () => {
  const app = read('renderer/app.js');
  assert.match(app, /central \? 'Mở kết nối Ubuntu'/);
  assert.match(app, /central \? 'Liên kết & quyền' : 'Kiểm tra kết nối'/);
  assert.match(app, /Đã có target được cấp/);
  assert.match(app, /reconcileControlPlaneAuthorityStatus/);
  assert.match(app, /isCentralExecutor\(state\.snapshot\?\.settings\)\s*\? navigate\('system'\)/);
  assert.doesNotMatch(app, /central \? 'Kiểm tra Executor'/);
});

test('System setup is the only primary settings entry and old setup pages remain subordinate links', () => {
  const html = read('renderer/index.html');
  const nav = html.match(/<nav class="nav-list"[\s\S]*?<\/nav>/)?.[0] || '';
  assert.match(nav, /data-page="system"[^>]*>[\s\S]*?Thiết lập hệ thống/);
  assert.doesNotMatch(nav, /data-page="(?:deploy|workspace|settings)"/);
  for (const page of ['deploy', 'workspace', 'settings']) {
    assert.match(html, new RegExp(`class="setup-section-link" data-nav="${page}"`));
  }
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
  assert.match(app, /Boolean\(centralDispatchableTargetForLocalWorkspace\(\)\)/);
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
