const fs = require('node:fs');
const { safeStorage } = require('electron');
const { secretsFile } = require('../paths');
const { ensureParent } = require('./jsonStore');

class SecretStore {
  _readAll() {
    try {
      const encrypted = fs.readFileSync(secretsFile());
      if (!safeStorage.isEncryptionAvailable()) return {};
      return JSON.parse(safeStorage.decryptString(encrypted));
    } catch {
      return {};
    }
  }

  _writeAll(value) {
    if (!safeStorage.isEncryptionAvailable()) {
      throw new Error('Kho lưu trữ an toàn Windows hiện không khả dụng, không thể lưu khóa.');
    }
    ensureParent(secretsFile());
    fs.writeFileSync(secretsFile(), safeStorage.encryptString(JSON.stringify(value)), { mode: 0o600 });
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
      mcpAuthToken: Boolean(all.mcpAuthToken)
    };
  }
}

module.exports = { SecretStore };
