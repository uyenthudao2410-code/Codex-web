const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const RUNTIME_IDENTITY_VERSION = 1;
const INSTALLATION_ID_PATTERN = /^[a-f0-9]{64}$/;
const RUNTIME_MODES = new Set(['development', 'packaged']);

function canonicalPath(value, label) {
  const text = String(value || '').trim();
  if (!text) throw new Error(`${label} is required for runtime identity.`);
  const absolute = path.resolve(text);
  if (!path.isAbsolute(absolute)) throw new Error(`${label} must resolve to an absolute path.`);
  try {
    return typeof fs.realpathSync.native === 'function'
      ? fs.realpathSync.native(absolute)
      : fs.realpathSync(absolute);
  } catch {
    return absolute;
  }
}

function pathKey(value) {
  const normalized = path.normalize(String(value || ''));
  return process.platform === 'win32' ? normalized.toLowerCase() : normalized;
}

function normalizeRuntimeMode(value) {
  const mode = String(value || '').trim().toLowerCase();
  if (!RUNTIME_MODES.has(mode)) throw new Error('Runtime mode must be development or packaged.');
  return mode;
}

function createInstallationIdentity({ mode, appRoot, resourcesRoot, executablePath }) {
  const runtimeMode = normalizeRuntimeMode(mode);
  const app = canonicalPath(appRoot, 'appRoot');
  const resources = canonicalPath(resourcesRoot, 'resourcesRoot');
  const executable = canonicalPath(executablePath, 'executablePath');
  const digest = crypto.createHash('sha256');
  for (const value of [
    'webmcp-installation-v1',
    runtimeMode,
    pathKey(app),
    pathKey(resources),
    pathKey(executable)
  ]) {
    digest.update(value);
    digest.update('\0');
  }
  return Object.freeze({
    version: RUNTIME_IDENTITY_VERSION,
    mode: runtimeMode,
    installation_id: digest.digest('hex')
  });
}

function validateInstallationIdentity(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('Runtime installation identity must be an object.');
  }
  const version = Number(value.version || 0);
  const mode = normalizeRuntimeMode(value.mode);
  const installationId = String(value.installation_id || '').toLowerCase();
  if (version !== RUNTIME_IDENTITY_VERSION || !INSTALLATION_ID_PATTERN.test(installationId)) {
    throw new Error('Runtime installation identity is invalid.');
  }
  return { version, mode, installation_id: installationId };
}

function sameInstallationIdentity(left, right) {
  try {
    return validateInstallationIdentity(left).installation_id === validateInstallationIdentity(right).installation_id;
  } catch {
    return false;
  }
}

module.exports = {
  RUNTIME_IDENTITY_VERSION,
  INSTALLATION_ID_PATTERN,
  createInstallationIdentity,
  validateInstallationIdentity,
  sameInstallationIdentity,
  canonicalPath
};
