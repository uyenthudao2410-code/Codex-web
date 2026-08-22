const test = require('node:test');
const assert = require('node:assert/strict');
const { controlledRestartGuard } = require('../electron/services/controlledRestartGuard');

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
