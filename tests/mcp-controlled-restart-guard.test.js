const test = require('node:test');
const assert = require('node:assert/strict');
const { controlledRestartGuard, controlledRestartAppRootGuard, controlledRestartOwnerGuard } = require('../electron/services/controlledRestartGuard');

const expectedWorkspace = 'E:\\DEV\\Codex-web';
const expectedUserData = 'C:\\Users\\Admin\\AppData\\Roaming\\web-mcp-assistant';

test('controlled restart guard requires explicit non-empty workspace and userData identities', () => {
  assert.deepEqual(
    controlledRestartGuard({
      expectedWorkspace,
      expectedUserData,
      configuredWorkspace: '',
      actualUserData: expectedUserData
    }),
    { ok: false, code: 'CONFIGURED_WORKSPACE_MISSING' }
  );
  assert.deepEqual(
    controlledRestartGuard({
      expectedWorkspace,
      expectedUserData: '',
      configuredWorkspace: expectedWorkspace,
      actualUserData: expectedUserData
    }),
    { ok: false, code: 'EXPECTED_USER_DATA_REQUIRED' }
  );
});

test('controlled restart guard rejects each identity mismatch and accepts exact paths', () => {
  assert.deepEqual(
    controlledRestartGuard({
      expectedWorkspace,
      expectedUserData,
      configuredWorkspace: 'E:\\DEV\\other',
      actualUserData: expectedUserData
    }),
    { ok: false, code: 'CONFIGURED_WORKSPACE_MISMATCH' }
  );
  assert.deepEqual(
    controlledRestartGuard({
      expectedWorkspace,
      expectedUserData,
      configuredWorkspace: expectedWorkspace,
      actualUserData: 'C:\\Users\\Admin\\AppData\\Roaming\\other'
    }),
    { ok: false, code: 'USER_DATA_MISMATCH' }
  );
  assert.deepEqual(
    controlledRestartGuard({
      expectedWorkspace,
      expectedUserData,
      configuredWorkspace: 'e:\\dev\\CODEX-web',
      actualUserData: 'c:\\users\\admin\\appdata\\roaming\\WEB-MCP-ASSISTANT'
    }),
    { ok: true, code: 'MATCHED' }
  );
});

test('controlled restart owner guard rejects unverified or changed native ownership', () => {
  const state = {
    nativePid: 1234,
    nativeDeviceId: 'device-a',
    nativeDeviceInstanceId: 'device-instance-0001'
  };
  const device = { deviceId: 'device-a', deviceInstanceId: 'device-instance-0001' };
  assert.deepEqual(controlledRestartOwnerGuard({ state, device }), { ok: true, code: 'OWNED' });
  assert.deepEqual(
    controlledRestartOwnerGuard({ state: { ...state, nativeDeviceId: '' }, device }),
    { ok: false, code: 'NATIVE_DEVICE_OWNERSHIP_MISSING' }
  );
  assert.deepEqual(
    controlledRestartOwnerGuard({ state, device: { ...device, deviceInstanceId: 'different-instance' } }),
    { ok: false, code: 'NATIVE_DEVICE_INSTANCE_MISMATCH' }
  );
});

test('controlled restart app-root guard binds a helper to its exact product resources', () => {
  const appRoot = 'E:\\DEV\\Codex-web';
  assert.deepEqual(
    controlledRestartAppRootGuard({ expectedAppRoot: '', actualAppRoot: appRoot, resourcesRoot: `${appRoot}\\resources` }),
    { ok: false, code: 'EXPECTED_APP_ROOT_REQUIRED' }
  );
  assert.deepEqual(
    controlledRestartAppRootGuard({ expectedAppRoot: appRoot, actualAppRoot: 'E:\\DEV\\other', resourcesRoot: 'E:\\DEV\\other\\resources' }),
    { ok: false, code: 'APP_ROOT_MISMATCH' }
  );
  assert.deepEqual(
    controlledRestartAppRootGuard({ expectedAppRoot: appRoot, actualAppRoot: appRoot, resourcesRoot: 'E:\\DEV\\other-resources' }),
    { ok: false, code: 'RESOURCES_ROOT_MISMATCH' }
  );
  assert.deepEqual(
    controlledRestartAppRootGuard({ expectedAppRoot: 'e:\\dev\\CODEX-web', actualAppRoot: appRoot, resourcesRoot: `${appRoot}\\resources` }),
    { ok: true, code: 'APP_ROOT_MATCHED' }
  );
});
