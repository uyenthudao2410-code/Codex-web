const crypto = require('node:crypto');
const defaultPaths = require('../paths');
const { readJson, writeJsonAtomic } = require('./jsonStore');
const { DEFAULTS, normalize } = require('./config');

class SettingsStore {
  constructor(paths = defaultPaths) {
    this.paths = paths;
  }

  load() {
    return normalize(readJson(this.paths.settingsFile(), {}));
  }

  save(patch) {
    const next = normalize({ ...this.load(), ...patch });
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
