const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const {
  normalize,
  normalizeWorkspacePath,
  validateRuntimeSettings,
  mergeRecentWorkspaces,
  workspaceKey
} = require('../electron/services/config');

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

test('direct local execution is the persistent default and sandboxing is explicit', () => {
  assert.equal(normalize({}).executionMode, 'local');
  assert.equal(normalize({ executionMode: 'invalid' }).executionMode, 'local');
  assert.equal(normalize({ executionMode: 'sandboxed' }).executionMode, 'sandboxed');
  const saved = normalize({ executionMode: 'local' });
  assert.equal(normalize(JSON.parse(JSON.stringify(saved))).executionMode, 'local');
});

test('legacy default port pair migrates without overwriting custom ports', () => {
  const migrated = normalize({ configVersion: 5, mcpPort: 18765, healthPort: 18081 });
  assert.equal(migrated.configVersion, 7);
  assert.equal(migrated.mcpPort, 18766);
  assert.equal(migrated.healthPort, 18082);

  const custom = normalize({ configVersion: 5, mcpPort: 19000, healthPort: 19001 });
  assert.equal(custom.mcpPort, 19000);
  assert.equal(custom.healthPort, 19001);
});

test('execution role is distinct from development or packaged runtime identity', () => {
  const legacy = normalize({ configVersion: 6 });
  assert.equal(legacy.configVersion, 7);
  assert.equal(legacy.executionRole, 'direct_legacy');

  const central = normalize({ executionRole: 'central_executor' });
  assert.equal(central.executionRole, 'central_executor');
  assert.equal(central.tunnelId, '', 'choosing the role does not invent a Tunnel identity');
  assert.equal(central.recoveryTunnelId, '', 'choosing the role does not invent a Recovery Tunnel identity');

  const invalid = normalize({ executionRole: 'runtime_mode' });
  assert.equal(invalid.executionRole, 'direct_legacy');
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

test('central executor validation ignores stale direct and recovery Tunnel settings', () => {
  const central = normalize({
    executionRole: 'central_executor',
    tunnelId: 'legacy-direct-id',
    recoveryTunnelId: 'legacy-recovery-id'
  });
  assert.doesNotThrow(() => validateRuntimeSettings(central));
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

test('workspace paths are fully qualified and preserve filesystem roots', () => {
  const absoluteRoot = path.parse(path.resolve(process.cwd())).root;
  assert.equal(normalizeWorkspacePath(absoluteRoot), path.normalize(absoluteRoot));
  assert.equal(normalizeWorkspacePath('.'), '');
  assert.equal(normalizeWorkspacePath('relative-workspace'), '');

  // A controller/test host may not share the executor's OS. Persisted and
  // health-payload Windows paths must still retain their own path semantics.
  assert.equal(normalizeWorkspacePath('C:'), '');
  assert.equal(normalizeWorkspacePath('E:.'), '');
  assert.equal(normalizeWorkspacePath('C:\\'), 'C:\\');
  assert.equal(normalizeWorkspacePath('C:\\workspace\\'), 'C:\\workspace');
  assert.equal(workspaceKey('C:\\Workspace'), workspaceKey('c:/workspace/'));

  if (process.platform === 'win32') {
    assert.equal(normalizeWorkspacePath('C:'), '');
    assert.equal(normalizeWorkspacePath('E:.'), '');
    assert.equal(normalizeWorkspacePath('C:\\'), 'C:\\');
    assert.equal(normalizeWorkspacePath('C:\\workspace\\'), 'C:\\workspace');
  }
});

test('settings normalization removes cwd-dependent workspace history and roots', () => {
  const activeWorkspace = path.resolve(process.cwd());
  const validRoot = path.parse(activeWorkspace).root;
  const result = normalize({
    workspace: activeWorkspace,
    recentWorkspaces: ['E:.', 'relative-workspace', activeWorkspace],
    authorizedRoots: ['C:', 'relative-root', validRoot]
  });

  assert.deepEqual(result.recentWorkspaces, [activeWorkspace]);
  assert.deepEqual(result.authorizedRoots, workspaceKey(validRoot) === workspaceKey(activeWorkspace) ? [] : [validRoot]);
});
