const fs = require('node:fs');
const { safeStorage } = require('electron');
const defaultPaths = require('../paths');
const { ensureParent } = require('./jsonStore');

const SECRET_STORE_SCHEMA_VERSION = 1;

function backupPath(file) {
  return `${file}.bak`;
}

class SecretStore {
  constructor(paths = defaultPaths, encryption = safeStorage) {
    this.paths = paths;
    this.encryption = encryption;
  }

  _decode(file) {
    const encrypted = fs.readFileSync(file);
    const decoded = JSON.parse(this.encryption.decryptString(encrypted));
    if (!decoded || typeof decoded !== 'object' || Array.isArray(decoded)) {
      throw new Error('secret store payload is invalid');
    }
    // Keep one-way compatibility with the pre-envelope format.  The next
    // successful mutation rewrites it into the versioned crash-safe envelope.
    if (decoded.schema_version === SECRET_STORE_SCHEMA_VERSION
      && decoded.entries && typeof decoded.entries === 'object' && !Array.isArray(decoded.entries)) {
      return decoded.entries;
    }
    if (!Object.hasOwn(decoded, 'schema_version')) return decoded;
    throw new Error('secret store schema is unsupported');
  }

  _readResult() {
    if (!this.encryption.isEncryptionAvailable()) {
      return { value: {}, found: false, valid: false, unavailable: true };
    }
    const primary = this.paths.secretsFile();
    const candidates = [primary, backupPath(primary)];
    let found = false;
    let error = null;
    for (const file of candidates) {
      try {
        if (!fs.existsSync(file)) continue;
        found = true;
        return { value: this._decode(file), found: true, valid: true, unavailable: false, recovered: file !== primary };
      } catch (candidateError) {
        error = candidateError;
      }
    }
    return { value: {}, found, valid: false, unavailable: false, error };
  }

  _readAll() {
    return this._readResult().value;
  }

  _readForMutation() {
    const result = this._readResult();
    if (result.unavailable) {
      throw new Error('Kho lưu trữ an toàn Windows hiện không khả dụng, không thể lưu khóa.');
    }
    if (result.found && !result.valid) {
      throw new Error('Kho lưu trữ an toàn bị hỏng; không ghi đè credential hiện có.');
    }
    return result.value;
  }

  _writeAll(value) {
    if (!this.encryption.isEncryptionAvailable()) {
      throw new Error('Kho lưu trữ an toàn Windows hiện không khả dụng, không thể lưu khóa.');
    }
    ensureParent(this.paths.secretsFile());
    const target = this.paths.secretsFile();
    const backup = backupPath(target);
    const temporary = `${target}.${process.pid}.${Date.now()}.${Math.random().toString(16).slice(2)}.tmp`;
    const payload = JSON.stringify({ schema_version: SECRET_STORE_SCHEMA_VERSION, entries: value });
    const encrypted = this.encryption.encryptString(payload);
    let descriptor = null;
    try {
      descriptor = fs.openSync(temporary, 'wx', 0o600);
      fs.writeFileSync(descriptor, encrypted);
      fs.fsyncSync(descriptor);
      fs.closeSync(descriptor);
      descriptor = null;

      if (process.platform === 'win32' && fs.existsSync(target)) {
        // Windows cannot atomically rename over an existing file.  Move the
        // last good copy aside first; a crash in the gap is recoverable from
        // the backup on the next read.
        fs.rmSync(backup, { force: true });
        fs.renameSync(target, backup);
        try {
          fs.renameSync(temporary, target);
        } catch (error) {
          if (!fs.existsSync(target) && fs.existsSync(backup)) fs.renameSync(backup, target);
          throw error;
        }
      } else {
        if (fs.existsSync(target)) {
          fs.copyFileSync(target, backup);
          fs.chmodSync(backup, 0o600);
        }
        fs.renameSync(temporary, target);
      }
      fs.chmodSync(target, 0o600);
    } finally {
      if (descriptor !== null) {
        try { fs.closeSync(descriptor); } catch { /* best effort after a failed write */ }
      }
      try { fs.unlinkSync(temporary); } catch { /* already renamed or absent */ }
    }
  }

  set(name, value) {
    const text = String(value || '').trim();
    if (!text) throw new Error('Khóa bí mật không được để trống.');
    const all = this._readForMutation();
    all[name] = text;
    this._writeAll(all);
  }

  get(name) {
    return this._readAll()[name] || '';
  }

  remove(name) {
    const all = this._readForMutation();
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
