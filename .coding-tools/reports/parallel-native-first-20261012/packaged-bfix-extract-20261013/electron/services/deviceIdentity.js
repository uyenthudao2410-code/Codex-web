const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const { ensureParent } = require('./jsonStore');

const DEVICE_IDENTITY_VERSION = 1;
const MAX_DEVICE_FILE_BYTES = 16 * 1024;
const DEVICE_ID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function identityError(message, cause = null) {
  const error = Object.assign(new Error(message), { code: 'DEVICE_IDENTITY_INVALID' });
  if (cause) error.cause = cause;
  return error;
}

function boundedDisplayName(value) {
  const text = String(value || '').trim();
  if (!text || text.length > 120 || /[\u0000-\u001f]/.test(text)) return '';
  return text;
}

function normalizeDeviceIdentity(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw identityError('Device identity must be a JSON object.');
  }
  const allowed = new Set(['version', 'device_id', 'display_name', 'created_at']);
  if (Object.keys(value).some((key) => !allowed.has(key))) {
    throw identityError('Device identity contains unsupported fields.');
  }
  const deviceId = String(value.device_id || '').toLowerCase();
  const displayName = boundedDisplayName(value.display_name);
  const createdAt = String(value.created_at || '');
  if (value.version !== DEVICE_IDENTITY_VERSION || !DEVICE_ID_PATTERN.test(deviceId) || !displayName || !Number.isFinite(Date.parse(createdAt))) {
    throw identityError('Device identity is incomplete or invalid.');
  }
  return {
    version: DEVICE_IDENTITY_VERSION,
    device_id: deviceId,
    display_name: displayName,
    created_at: createdAt
  };
}

function readDeviceIdentity(file) {
  let raw;
  try {
    raw = fs.readFileSync(file, 'utf8');
  } catch (error) {
    if (error?.code === 'ENOENT') throw error;
    throw identityError('Device identity could not be read.', error);
  }
  if (Buffer.byteLength(raw, 'utf8') > MAX_DEVICE_FILE_BYTES) {
    throw identityError('Device identity exceeded the bounded size.');
  }
  try {
    return normalizeDeviceIdentity(JSON.parse(raw));
  } catch (error) {
    if (error?.code === 'DEVICE_IDENTITY_INVALID') throw error;
    throw identityError('Device identity is not valid JSON.', error);
  }
}

function newDeviceIdentity() {
  return {
    version: DEVICE_IDENTITY_VERSION,
    device_id: crypto.randomUUID().toLowerCase(),
    display_name: boundedDisplayName(os.hostname()) || 'WebCodex device',
    created_at: new Date().toISOString()
  };
}

function loadOrCreateDeviceIdentity(paths) {
  const file = paths.deviceFile();
  try {
    return readDeviceIdentity(file);
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
  }

  ensureParent(file);
  const identity = normalizeDeviceIdentity(newDeviceIdentity());
  let handle;
  try {
    handle = fs.openSync(file, 'wx', 0o600);
    fs.writeFileSync(handle, `${JSON.stringify(identity, null, 2)}\n`, 'utf8');
    fs.fsyncSync(handle);
    try { fs.chmodSync(file, 0o600); } catch { /* best effort on Windows */ }
    return identity;
  } catch (error) {
    if (error?.code === 'EEXIST') return readDeviceIdentity(file);
    if (error?.code === 'DEVICE_IDENTITY_INVALID') throw error;
    throw identityError('Device identity could not be created safely.', error);
  } finally {
    if (handle !== undefined) fs.closeSync(handle);
  }
}

function runtimeDeviceIdentity(deviceIdentity, deviceInstanceId) {
  const device = normalizeDeviceIdentity(deviceIdentity);
  const instance = String(deviceInstanceId || '').trim();
  if (!/^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$/.test(instance)) {
    throw identityError('Device instance identity is invalid.');
  }
  return {
    deviceId: device.device_id,
    deviceInstanceId: instance,
    displayName: device.display_name
  };
}

function classifyStoredDeviceOwner(storedDeviceId, expectedDeviceId) {
  const expected = String(expectedDeviceId || '').trim().toLowerCase();
  if (!expected) return 'unmanaged';
  const stored = String(storedDeviceId || '').trim().toLowerCase();
  if (!stored) return 'legacy';
  return stored === expected ? 'owned' : 'foreign';
}

module.exports = {
  DEVICE_IDENTITY_VERSION,
  DEVICE_ID_PATTERN,
  MAX_DEVICE_FILE_BYTES,
  readDeviceIdentity,
  loadOrCreateDeviceIdentity,
  normalizeDeviceIdentity,
  runtimeDeviceIdentity,
  classifyStoredDeviceOwner
};
