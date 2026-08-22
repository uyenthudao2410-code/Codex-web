const path = require('node:path');

function normalizedPath(value) {
  const text = String(value || '').trim();
  return text ? path.resolve(text).toLowerCase() : '';
}

function samePath(left, right) {
  const normalizedLeft = normalizedPath(left);
  const normalizedRight = normalizedPath(right);
  return Boolean(normalizedLeft && normalizedRight && normalizedLeft === normalizedRight);
}

function controlledRestartGuard({
  expectedWorkspace,
  expectedUserData,
  configuredWorkspace,
  actualUserData
} = {}) {
  const expectedWorkspaceText = String(expectedWorkspace || '').trim();
  const expectedUserDataText = String(expectedUserData || '').trim();
  const configuredWorkspaceText = String(configuredWorkspace || '').trim();
  const actualUserDataText = String(actualUserData || '').trim();

  if (!expectedWorkspaceText) {
    return { ok: false, code: 'EXPECTED_WORKSPACE_REQUIRED' };
  }
  if (!expectedUserDataText) {
    return { ok: false, code: 'EXPECTED_USER_DATA_REQUIRED' };
  }
  if (!configuredWorkspaceText) {
    return { ok: false, code: 'CONFIGURED_WORKSPACE_MISSING' };
  }
  if (!actualUserDataText) {
    return { ok: false, code: 'ACTUAL_USER_DATA_MISSING' };
  }
  if (!samePath(configuredWorkspaceText, expectedWorkspaceText)) {
    return { ok: false, code: 'CONFIGURED_WORKSPACE_MISMATCH' };
  }
  if (!samePath(actualUserDataText, expectedUserDataText)) {
    return { ok: false, code: 'USER_DATA_MISMATCH' };
  }
  return { ok: true, code: 'MATCHED' };
}

module.exports = { controlledRestartGuard, samePath };
