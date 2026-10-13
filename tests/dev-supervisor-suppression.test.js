const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { suppressDevelopmentRecoverySupervisor } = require('../electron/services/recoveryHostLauncher');

function fixture(t, mode, { legacy = false } = {}) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'webmcp-appdata-'));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  const appData = path.join(directory, 'roaming');
  const localAppData = path.join(directory, 'local');
  const installRoot = legacy
    ? path.join(localAppData, 'WebMcpRecoverySupervisor')
    : path.join(appData, 'web-mcp-assistant', 'recovery-supervisor');
  fs.mkdirSync(installRoot, { recursive: true });
  fs.writeFileSync(path.join(installRoot, 'manifest.json'), JSON.stringify({
    schema_version: 1,
    mode,
    executable: 'C:\\fixture\\electron.exe',
    app_root: 'C:\\fixture\\checkout',
    data_root: 'C:\\fixture\\data'
  }), 'utf8');
  return { appData, localAppData, installRoot, env: { APPDATA: appData, LOCALAPPDATA: localAppData } };
}

test('development startup suppresses the current roaming Recovery Supervisor without uninstalling anything', (t) => {
  const { env, localAppData, installRoot } = fixture(t, 'development');
  const legacyRoot = path.join(localAppData, 'WebMcpRecoverySupervisor');
  fs.mkdirSync(legacyRoot, { recursive: true });
  fs.copyFileSync(path.join(installRoot, 'manifest.json'), path.join(legacyRoot, 'manifest.json'));
  const result = suppressDevelopmentRecoverySupervisor({
    env,
    now: () => new Date('2026-08-18T08:00:00.000Z')
  });
  assert.equal(result.suppressed, true);
  assert.equal(
    fs.readFileSync(path.join(installRoot, 'stop.request'), 'ascii'),
    '2026-08-18T08:00:00.000Z'
  );
  assert.equal(fs.existsSync(path.join(legacyRoot, 'stop.request')), false);
});

test('development startup never suppresses a packaged Recovery Supervisor', (t) => {
  const { env, installRoot } = fixture(t, 'packaged');
  const result = suppressDevelopmentRecoverySupervisor({ env });
  assert.equal(result.suppressed, false);
  assert.equal(fs.existsSync(path.join(installRoot, 'stop.request')), false);
});

test('development startup keeps an exact-checkout Supervisor enabled for same-identity recovery', (t) => {
  const { env, installRoot } = fixture(t, 'development');
  const result = suppressDevelopmentRecoverySupervisor({
    env,
    expectedAppRoot: 'C:\\fixture\\checkout',
    expectedExecutable: 'C:\\fixture\\electron.exe'
  });
  assert.deepEqual(result, {
    suppressed: false,
    reason: 'matching_development_supervisor'
  });
  assert.equal(fs.existsSync(path.join(installRoot, 'stop.request')), false);
});

test('missing current and legacy supervisor manifests do not create persistent files', (t) => {
  const { env, installRoot } = fixture(t, 'development');
  fs.unlinkSync(path.join(installRoot, 'manifest.json'));
  const result = suppressDevelopmentRecoverySupervisor({ env });
  assert.equal(result.suppressed, false);
  assert.equal(fs.existsSync(path.join(installRoot, 'stop.request')), false);
  assert.equal(fs.existsSync(path.join(env.LOCALAPPDATA, 'WebMcpRecoverySupervisor', 'stop.request')), false);
});

test('an absent current manifest falls back to the legacy development Supervisor', (t) => {
  const { env, installRoot } = fixture(t, 'development', { legacy: true });
  assert.equal(suppressDevelopmentRecoverySupervisor({ env }).suppressed, true);
  assert.equal(fs.existsSync(path.join(installRoot, 'stop.request')), true);
  assert.equal(fs.existsSync(path.join(env.APPDATA, 'web-mcp-assistant', 'recovery-supervisor')), false);
});

test('invalid current manifest state refuses legacy fallback and suppression', (t) => {
  const { env, installRoot: legacyRoot } = fixture(t, 'development', { legacy: true });
  const currentRoot = path.join(env.APPDATA, 'web-mcp-assistant', 'recovery-supervisor');
  fs.mkdirSync(currentRoot, { recursive: true });
  const manifestFile = path.join(currentRoot, 'manifest.json');
  for (const contents of ['{', JSON.stringify({ schema_version: 2, mode: 'development' }),
    JSON.stringify({ schema_version: 1, mode: 'development' }),
    JSON.stringify({ schema_version: 1, mode: 'development', app_root: 'relative', executable: 'relative' }),
    JSON.stringify({ schema_version: 1, mode: 'unknown' }), ' '.repeat(64 * 1024 + 1)]) {
    fs.writeFileSync(manifestFile, contents);
    assert.throws(() => suppressDevelopmentRecoverySupervisor({ env }), {
      code: 'RECOVERY_HOST_DEV_HANDOFF_SUPERVISOR_UNVERIFIED'
    });
  }
  assert.equal(fs.existsSync(path.join(currentRoot, 'stop.request')), false);
  assert.equal(fs.existsSync(path.join(legacyRoot, 'stop.request')), false);
});

test('unreadable current manifest refuses legacy fallback', (t) => {
  const { env, installRoot: legacyRoot } = fixture(t, 'development', { legacy: true });
  const manifestFile = path.join(env.APPDATA, 'web-mcp-assistant', 'recovery-supervisor', 'manifest.json');
  const fsApi = { ...fs, statSync(file) {
    if (file === manifestFile) throw Object.assign(new Error('denied'), { code: 'EACCES' });
    return fs.statSync(file);
  } };
  assert.throws(() => suppressDevelopmentRecoverySupervisor({ env, fsApi }), {
    code: 'RECOVERY_HOST_DEV_HANDOFF_SUPERVISOR_UNVERIFIED'
  });
  assert.equal(fs.existsSync(path.join(legacyRoot, 'stop.request')), false);
});
