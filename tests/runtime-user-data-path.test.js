const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const {
  configureElectronUserDataPath,
  hasExplicitUserDataDirectory
} = require('../electron/services/runtimePaths');

function fakeApp({ appData, userData }) {
  let currentUserData = userData;
  const setCalls = [];
  return {
    setCalls,
    getPath(name) {
      if (name === 'appData') return appData;
      if (name === 'userData') return currentUserData;
      throw new Error(`Unexpected path key: ${name}`);
    },
    setPath(name, value) {
      assert.equal(name, 'userData');
      currentUserData = value;
      setCalls.push(value);
    }
  };
}

test('normal product launch keeps the version-1.0 production profile pin', () => {
  const appData = path.join('C:', 'Users', 'test', 'AppData', 'Roaming');
  const app = fakeApp({ appData, userData: path.join(appData, 'Coding Tools MCP') });
  const resolved = configureElectronUserDataPath(app, {
    argv: ['Coding Tools MCP.exe', '--user-data-dir=C:\\isolated'],
    recoveryHostMode: false
  });

  const expected = path.join(appData, 'web-mcp-assistant');
  assert.equal(resolved, expected);
  assert.deepEqual(app.setCalls, [expected]);
});

test('Recovery Host without an explicit user-data override keeps the production profile pin', () => {
  const appData = path.join('C:', 'Users', 'test', 'AppData', 'Roaming');
  const app = fakeApp({ appData, userData: path.join(appData, 'Coding Tools MCP') });
  const resolved = configureElectronUserDataPath(app, {
    argv: ['Coding Tools MCP.exe', '--recovery-host'],
    recoveryHostMode: true
  });

  const expected = path.join(appData, 'web-mcp-assistant');
  assert.equal(resolved, expected);
  assert.deepEqual(app.setCalls, [expected]);
});

test('isolated Recovery Host preserves Electron userData when an explicit override is present', () => {
  const appData = path.join('C:', 'Users', 'test', 'AppData', 'Roaming');
  const isolated = path.join('C:', 'Temp', 'webmcp-packaged-recovery');
  const app = fakeApp({ appData, userData: isolated });
  const argv = ['Coding Tools MCP.exe', '--recovery-host', `--user-data-dir=${isolated}`];

  assert.equal(hasExplicitUserDataDirectory(argv), true);
  assert.equal(configureElectronUserDataPath(app, { argv, recoveryHostMode: true }), isolated);
  assert.deepEqual(app.setCalls, []);
});

test('empty user-data override is not treated as an isolation boundary', () => {
  assert.equal(hasExplicitUserDataDirectory(['Coding Tools MCP.exe', '--user-data-dir=']), false);
});
