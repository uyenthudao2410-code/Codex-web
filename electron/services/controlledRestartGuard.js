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

function controlledRestartOwnerGuard({ state, device } = {}) {
  const nativePid = Number(state?.nativePid || 0);
  const storedDeviceId = String(state?.nativeDeviceId || '').trim().toLowerCase();
  const storedInstanceId = String(state?.nativeDeviceInstanceId || '').trim();
  const deviceId = String(device?.deviceId || '').trim().toLowerCase();
  const deviceInstanceId = String(device?.deviceInstanceId || '').trim();

  if (!Number.isInteger(nativePid) || nativePid <= 0) {
    return { ok: false, code: 'NATIVE_PID_MISSING' };
  }
  if (!storedDeviceId || !storedInstanceId) {
    return { ok: false, code: 'NATIVE_DEVICE_OWNERSHIP_MISSING' };
  }
  if (!deviceId || !deviceInstanceId) {
    return { ok: false, code: 'RUNTIME_DEVICE_IDENTITY_MISSING' };
  }
  if (storedDeviceId !== deviceId) {
    return { ok: false, code: 'NATIVE_DEVICE_OWNERSHIP_MISMATCH' };
  }
  if (storedInstanceId !== deviceInstanceId) {
    return { ok: false, code: 'NATIVE_DEVICE_INSTANCE_MISMATCH' };
  }
  return { ok: true, code: 'OWNED' };
}

module.exports = { controlledRestartGuard, controlledRestartOwnerGuard, samePath };
