const crypto = require('node:crypto');
const defaultPaths = require('../paths');
const { readJson, writeJsonAtomic } = require('./jsonStore');
const { DEFAULTS, normalize } = require('./config');

class SettingsStore {
  constructor(paths = defaultPaths) {
    this.paths = paths;
  }

  isDevelopmentRuntime() {
    try {
      return typeof this.paths.runtimeMode === 'function' && this.paths.runtimeMode() === 'development';
    } catch {
      return false;
    }
  }

  load() {
    const current = normalize(readJson(this.paths.settingsFile(), {}));
    // Development checkouts are intentionally session-owned. Persisting a
    // Windows login item would pin an arbitrary checkout path in the registry
    // and can resurrect a stale source root after the checkout moves.
    if (this.isDevelopmentRuntime()) current.startWithWindows = false;
    return current;
  }

  save(patch) {
    const next = normalize({ ...this.load(), ...patch });
    if (this.isDevelopmentRuntime()) next.startWithWindows = false;
    writeJsonAtomic(this.paths.settingsFile(), next);
    return next;
  }

  ensureAuthToken() {
    const current = this.load();
    if (!current.authTokenId) {
      current.authTokenId = crypto.randomBytes(16).toString('hex');
      writeJsonAtomic(this.paths.settingsFile(), current);
    }
    return current.authTokenId;
  }
}

module.exports = { SettingsStore, DEFAULTS, normalize };
