const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

test('Settings has one obvious entry and a resumable four-step setup surface', () => {
  const html = read('renderer/index.html');
  assert.match(html, /data-page="system"[^>]*>.*?<span>Cài đặt<\/span>/s);
  assert.match(html, /id="setupSummary"/);
  for (const id of ['setupStepConnection', 'setupStepFolder', 'setupStepAccount', 'setupStepVerify']) {
    assert.match(html, new RegExp(`id="${id}"`));
  }
  assert.match(html, /<b>Quyền truy cập<\/b>/);
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
  assert.match(app, /isCentralExecutor\(state\.snapshot\?\.settings\)\s*\? navigate\('deploy'\)/);
  assert.doesNotMatch(app, /central \? 'Kiểm tra Executor'/);
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
