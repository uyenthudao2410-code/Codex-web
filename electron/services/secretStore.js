const fs = require('node:fs');
const { safeStorage } = require('electron');
const defaultPaths = require('../paths');
const { ensureParent } = require('./jsonStore');

class SecretStore {
  constructor(paths = defaultPaths, encryption = safeStorage) {
    this.paths = paths;
    this.encryption = encryption;
  }

  _readAll() {
    try {
      const encrypted = fs.readFileSync(this.paths.secretsFile());
      if (!this.encryption.isEncryptionAvailable()) return {};
      return JSON.parse(this.encryption.decryptString(encrypted));
    } catch {
      return {};
    }
  }

  _writeAll(value) {
    if (!this.encryption.isEncryptionAvailable()) {
      throw new Error('Kho lưu trữ an toàn Windows hiện không khả dụng, không thể lưu khóa.');
    }
    ensureParent(this.paths.secretsFile());
    fs.writeFileSync(this.paths.secretsFile(), this.encryption.encryptString(JSON.stringify(value)), { mode: 0o600 });
  }

  set(name, value) {
    const text = String(value || '').trim();
    if (!text) throw new Error('Khóa bí mật không được để trống.');
    const all = this._readAll();
    all[name] = text;
    this._writeAll(all);
  }

  get(name) {
    return this._readAll()[name] || '';
  }

  remove(name) {
    const all = this._readAll();
    delete all[name];
    this._writeAll(all);
  }

  status() {
    const all = this._readAll();
    return {
      runtimeApiKey: Boolean(all.runtimeApiKey),
      mcpAuthToken: Boolean(all.mcpAuthToken),
      p5A0Seed: Boolean(all.p5A0Seed)
    };
  }
}

module.exports = { SecretStore };
