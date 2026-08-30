const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { suppressDevelopmentRecoverySupervisor } = require('../electron/services/recoveryHostLauncher');

function fixture(t, mode) {
  const localAppData = fs.mkdtempSync(path.join(os.tmpdir(), 'webmcp-localappdata-'));
  t.after(() => fs.rmSync(localAppData, { recursive: true, force: true }));
  const installRoot = path.join(localAppData, 'WebMcpRecoverySupervisor');
  fs.mkdirSync(installRoot, { recursive: true });
  fs.writeFileSync(path.join(installRoot, 'manifest.json'), JSON.stringify({
    schema_version: 1,
    mode,
    executable: 'C:\\fixture\\electron.exe',
    app_root: 'C:\\fixture\\checkout',
    data_root: 'C:\\fixture\\data'
  }), 'utf8');
  return { localAppData, installRoot };
}

test('development startup neutralizes a previously installed dev Recovery Supervisor without uninstalling anything', (t) => {
  const { localAppData, installRoot } = fixture(t, 'development');
  const result = suppressDevelopmentRecoverySupervisor({
    env: { LOCALAPPDATA: localAppData },
    now: () => new Date('2026-08-18T08:00:00.000Z')
  });
  assert.equal(result.suppressed, true);
  assert.equal(
    fs.readFileSync(path.join(installRoot, 'stop.request'), 'ascii'),
    '2026-08-18T08:00:00.000Z'
  );
});

test('development startup never suppresses a packaged Recovery Supervisor', (t) => {
  const { localAppData, installRoot } = fixture(t, 'packaged');
  const result = suppressDevelopmentRecoverySupervisor({ env: { LOCALAPPDATA: localAppData } });
  assert.equal(result.suppressed, false);
  assert.equal(fs.existsSync(path.join(installRoot, 'stop.request')), false);
});

test('development startup keeps an exact-checkout Supervisor enabled for same-identity recovery', (t) => {
  const { localAppData, installRoot } = fixture(t, 'development');
  const result = suppressDevelopmentRecoverySupervisor({
    env: { LOCALAPPDATA: localAppData },
    expectedAppRoot: 'C:\\fixture\\checkout',
    expectedExecutable: 'C:\\fixture\\electron.exe'
  });
  assert.deepEqual(result, {
    suppressed: false,
    reason: 'matching_development_supervisor'
  });
  assert.equal(fs.existsSync(path.join(installRoot, 'stop.request')), false);
});

test('missing or malformed supervisor state is ignored without creating persistent files', (t) => {
  const localAppData = fs.mkdtempSync(path.join(os.tmpdir(), 'webmcp-localappdata-'));
  t.after(() => fs.rmSync(localAppData, { recursive: true, force: true }));
  const result = suppressDevelopmentRecoverySupervisor({ env: { LOCALAPPDATA: localAppData } });
  assert.equal(result.suppressed, false);
  assert.equal(fs.existsSync(path.join(localAppData, 'WebMcpRecoverySupervisor', 'stop.request')), false);
});
