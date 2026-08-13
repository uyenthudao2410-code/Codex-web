const test = require('node:test');
const assert = require('node:assert/strict');
const { normalize, validateRuntimeSettings, mergeRecentWorkspaces, workspaceKey } = require('../electron/services/config');

test('invalid modes fall back to safe defaults', () => {
  const result = normalize({ permissionMode: 'dangerous', toolMode: 'dangerous', proxyMode: 'dangerous' });
  assert.equal(result.permissionMode, 'safe');
  assert.equal(result.toolMode, 'smart');
  assert.equal(result.mcpPort, 18766);
  assert.equal(result.healthPort, 18082);
  assert.equal(result.proxyMode, 'auto');
});

test('legacy tool modes migrate to smart mode', () => {
  for (const toolMode of ['readonly', 'coding', 'build', 'full', 'smart']) assert.equal(normalize({ toolMode }).toolMode, 'smart');
});

test('unknown legacy settings are removed from normalized settings', () => {
  assert.deepEqual(Object.keys(normalize({ obsoleteRuntimeChoice: 'legacy' })).sort(), Object.keys(normalize()).sort());
});

test('trusted values are preserved', () => {
  const result = normalize({ permissionMode: 'trusted', mcpPort: '9000' });
  assert.equal(result.permissionMode, 'trusted');
  assert.equal(result.mcpPort, 9000);
});

test('legacy default port pair migrates without overwriting custom ports', () => {
  const migrated = normalize({ configVersion: 5, mcpPort: 18765, healthPort: 18081 });
  assert.equal(migrated.configVersion, 6);
  assert.equal(migrated.mcpPort, 18766);
  assert.equal(migrated.healthPort, 18082);

  const custom = normalize({ configVersion: 5, mcpPort: 19000, healthPort: 19001 });
  assert.equal(custom.mcpPort, 19000);
  assert.equal(custom.healthPort, 19001);
});

test('runtime ports cannot overlap', () => {
  assert.throws(() => validateRuntimeSettings(normalize({ mcpPort: 9000, healthPort: 9000 })), /không được giống nhau/i);
});

test('proxy credentials are rejected', () => {
  assert.throws(() => validateRuntimeSettings(normalize({ proxyUrl: 'http://user:pass@127.0.0.1:1080' })), /không lưu tên người dùng/i);
});

test('manual proxy mode requires an address', () => {
  assert.throws(() => validateRuntimeSettings(normalize({ proxyMode: 'manual', proxyUrl: '' })), /proxy thủ công/i);
});

test('tunnel id must use the official prefix', () => {
  assert.throws(() => validateRuntimeSettings(normalize({ tunnelId: 'wrong-id' })), /tunnel_/);
});

test('recent workspaces use a 50-item MRU list', () => {
  let recent = [];
  for (let index = 0; index < 55; index += 1) {
    recent = mergeRecentWorkspaces(recent, `C:\\workspace-${index}`);
  }
  assert.equal(recent.length, 50);
  assert.equal(recent[0], 'C:\\workspace-54');
  assert.equal(recent.at(-1), 'C:\\workspace-5');

  recent = mergeRecentWorkspaces(recent, 'c:\\WORKSPACE-20\\');
  assert.equal(recent.length, 50);
  assert.equal(workspaceKey(recent[0]), workspaceKey('C:\\workspace-20'));
  assert.equal(recent.filter((item) => workspaceKey(item) === workspaceKey('C:\\workspace-20')).length, 1);
});
