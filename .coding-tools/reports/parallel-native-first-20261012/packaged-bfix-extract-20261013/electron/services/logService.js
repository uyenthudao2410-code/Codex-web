const fs = require('node:fs');
const path = require('node:path');
const { EventEmitter } = require('node:events');
const defaultPaths = require('../paths');
const { ensureParent } = require('./jsonStore');

const MAX_LOG_BYTES = 10 * 1024 * 1024;
const MAX_LOG_FILES = 5;
const LOG_MAINTENANCE_INTERVAL_MS = 60 * 1000;

function rotateLog(file, maxBytes = MAX_LOG_BYTES, maxFiles = MAX_LOG_FILES) {
  try {
    if (!fs.existsSync(file) || fs.statSync(file).size < maxBytes) return false;
    // Remove the oldest retained segment before shifting.  Without this,
    // repeated rotations leave an unbounded ``.N`` tail on long-lived runs.
    const oldest = `${file}.${maxFiles}`;
    if (fs.existsSync(oldest)) fs.rmSync(oldest, { force: true });
    for (let index = maxFiles - 1; index >= 1; index -= 1) {
      const source = `${file}.${index}`;
      const target = `${file}.${index + 1}`;
      if (fs.existsSync(source)) fs.renameSync(source, target);
    }
    fs.renameSync(file, `${file}.1`);
    return true;
  } catch {
    return false;
  }
}

function pruneLogBackups(file, maxFiles = MAX_LOG_FILES) {
  try {
    const directory = path.dirname(file);
    const prefix = `${path.basename(file)}.`;
    const entries = fs.readdirSync(directory);
    for (const entry of entries) {
      if (!entry.startsWith(prefix)) continue;
      const suffix = entry.slice(prefix.length);
      if (/^\d+$/.test(suffix) && Number(suffix) > maxFiles) {
        fs.rmSync(path.join(directory, entry), { force: true });
      }
    }
  } catch {
    // Log maintenance must never interfere with the runtime.
  }
}

class LogService extends EventEmitter {
  constructor(paths = defaultPaths) {
    super();
    this.paths = paths;
    this.buffer = [];
    this.lastMaintenanceAt = 0;
  }

  write(level, message, meta = {}) {
    const safeMeta = { ...meta };
    for (const key of Object.keys(safeMeta)) {
      if (/key|token|authorization|secret/i.test(key)) safeMeta[key] = '[已隐藏]';
    }
    const event = {
      time: new Date().toISOString(),
      level,
      message: String(message),
      meta: safeMeta
    };
    this.buffer.push(event);
    if (this.buffer.length > 1000) this.buffer.shift();
    const file = this.paths.logFile();
    ensureParent(file);
    rotateLog(file);
    const now = Date.now();
    if (now - this.lastMaintenanceAt >= LOG_MAINTENANCE_INTERVAL_MS) {
      pruneLogBackups(file);
      this.lastMaintenanceAt = now;
    }
    fs.appendFileSync(file, `${JSON.stringify(event)}\n`, 'utf8');
    this.emit('entry', event);
    return event;
  }

  info(message, meta) { return this.write('info', message, meta); }
  warn(message, meta) { return this.write('warn', message, meta); }
  error(message, meta) { return this.write('error', message, meta); }

  read(limit = 300) {
    if (this.buffer.length) return this.buffer.slice(-limit);
    try {
      return fs.readFileSync(this.paths.logFile(), 'utf8').trim().split(/\r?\n/).filter(Boolean)
        .slice(-Math.max(limit * 3, limit))
        .map((line) => {
          try { return JSON.parse(line); } catch { return null; }
        })
        .filter(Boolean)
        .slice(-limit);
    } catch {
      return [];
    }
  }

  clear() {
    this.buffer = [];
    ensureParent(this.paths.logFile());
    fs.writeFileSync(this.paths.logFile(), '', 'utf8');
  }
}

module.exports = {
  LogService,
  rotateLog,
  pruneLogBackups,
  MAX_LOG_BYTES,
  MAX_LOG_FILES,
  LOG_MAINTENANCE_INTERVAL_MS,
};
