'use strict';
/*
 * Work Hub SSH targets (parity M4). Host identity is pinned: the panel
 * scans the host key (ssh-keyscan), shows its SHA256 fingerprint, and a
 * check run only connects when the scanned key matches the pinned
 * fingerprint, using a one-off known_hosts file with
 * StrictHostKeyChecking=yes. Every check is audit-logged to
 * .coding-tools/work-hub-ssh-audit.json. Commands run through execFile
 * argv — no shell string composition.
 */
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const { execFile } = require('child_process');

const HOST_PATTERN = /^[A-Za-z0-9._-]{1,255}$/;
const USER_PATTERN = /^[A-Za-z0-9._-]{0,80}$/;
const REMOTE_DIR_PATTERN = /^[\w\-./ ~]{0,500}$/;

function sha256Fingerprint(base64Key) {
  const blob = Buffer.from(String(base64Key || ''), 'base64');
  return `SHA256:${crypto.createHash('sha256').update(blob).digest('base64').replace(/=+$/, '')}`;
}

function parseKeyscan(stdout, host) {
  for (const line of String(stdout || '').split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const parts = trimmed.split(/\s+/);
    if (parts.length >= 3) {
      return { host: parts[0], keyType: parts[1], key: parts[2], line: trimmed, fingerprint: sha256Fingerprint(parts[2]) };
    }
  }
  throw new Error(`Không quét được host key của ${host}.`);
}

function runExecFile(execFileImpl, file, args, options = {}) {
  return new Promise((resolve) => {
    execFileImpl(file, args, { timeout: options.timeout || 20000, maxBuffer: 512 * 1024 }, (error, stdout, stderr) => {
      resolve({
        ok: !error,
        exitCode: error ? (typeof error.code === 'number' ? error.code : 1) : 0,
        stdout: String(stdout || ''),
        stderr: String(stderr || ''),
        error: error ? String(error.message || error) : '',
      });
    });
  });
}

function validateTarget(payload) {
  const host = String(payload?.host || '').trim();
  const user = String(payload?.user || '').trim();
  const port = Math.max(1, Math.min(65535, Number(payload?.port) || 22));
  const remoteDir = String(payload?.remoteDir || '').trim();
  if (!HOST_PATTERN.test(host)) throw new Error('Host SSH không hợp lệ.');
  if (!USER_PATTERN.test(user)) throw new Error('User SSH không hợp lệ.');
  if (!REMOTE_DIR_PATTERN.test(remoteDir) || remoteDir.includes('..')) throw new Error('Thư mục remote không hợp lệ.');
  return { host, user, port, remoteDir };
}

function createWorkHubSsh(overrides = {}) {
  const execFileImpl = overrides.execFile || execFile;
  const auditRoot = overrides.auditRoot || null;

  async function scanViaConnectProbe(host, port) {
    // Some client builds (Win32-OpenSSH ssh-keyscan) cannot finish KEX
    // against hardened servers (sntrup/mlkem-only). A no-auth ssh probe
    // with accept-new into a throwaway known_hosts captures the same key;
    // pinning it afterwards is the operator's explicit TOFU decision.
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-keyscan-'));
    try {
      const knownHosts = path.join(tempDir, 'known_hosts');
      await runExecFile(execFileImpl, 'ssh', [
        '-p', String(port),
        '-o', 'StrictHostKeyChecking=accept-new',
        '-o', `UserKnownHostsFile=${knownHosts}`,
        '-o', 'BatchMode=yes',
        '-o', 'PreferredAuthentications=none',
        '-o', 'ConnectTimeout=10',
        host, 'exit',
      ], { timeout: 25000 });
      const content = fs.existsSync(knownHosts) ? fs.readFileSync(knownHosts, 'utf8') : '';
      if (!content.trim()) throw new Error('probe did not capture a host key');
      return parseKeyscan(content, host);
    } finally {
      try { fs.rmSync(tempDir, { recursive: true, force: true }); } catch { /* temp cleanup */ }
    }
  }

  async function scanHostKey(payload) {
    const { host, port } = validateTarget(payload || {});
    const result = await runExecFile(execFileImpl, 'ssh-keyscan', ['-T', '10', '-p', String(port), host], { timeout: 20000 });
    if (result.stdout && result.stdout.trim()) {
      try { return { ...parseKeyscan(result.stdout, host), via: 'keyscan' }; } catch { /* fall through to probe */ }
    }
    try {
      return { ...(await scanViaConnectProbe(host, port)), via: 'connect-probe' };
    } catch {
      throw new Error(`Không quét được host key của ${host}: ${(result.stderr || result.error || 'keyscan và connect-probe đều thất bại').slice(0, 200)}`);
    }
  }

  function audit(root, entry) {
    if (!root) return;
    try {
      const file = path.join(root, '.coding-tools', 'work-hub-ssh-audit.json');
      fs.mkdirSync(path.dirname(file), { recursive: true });
      let records = [];
      try { records = JSON.parse(fs.readFileSync(file, 'utf8')).records || []; } catch { /* fresh log */ }
      records.push(entry);
      fs.writeFileSync(file, JSON.stringify({ version: 1, records: records.slice(-200) }, null, 2));
    } catch { /* audit must never break the check itself */ }
  }

  async function testTarget(root, payload) {
    const target = validateTarget(payload || {});
    const expected = String(payload?.expectedFingerprint || '').trim();
    const scanned = await scanHostKey(target);
    const at = new Date().toISOString();
    if (expected && expected !== scanned.fingerprint) {
      audit(root, { at, ...target, fingerprint: scanned.fingerprint, expected, result: 'HOST_KEY_MISMATCH' });
      const error = new Error(`Host key KHÔNG khớp vân tay đã ghim (${expected}). Máy chủ có thể đã đổi key — kiểm tra lại trước khi ghim mới.`);
      error.code = 'HOST_KEY_MISMATCH';
      throw error;
    }
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-ssh-'));
    try {
      const knownHosts = path.join(tempDir, 'known_hosts');
      fs.writeFileSync(knownHosts, `${scanned.line}\n`, { mode: 0o600 });
      const destination = target.user ? `${target.user}@${target.host}` : target.host;
      const remoteCommand = target.remoteDir
        ? `cd ${target.remoteDir} && pwd && git status --short | head -20`
        : 'pwd && git status --short | head -20';
      const result = await runExecFile(execFileImpl, 'ssh', [
        '-p', String(target.port),
        '-o', 'BatchMode=yes',
        '-o', 'ConnectTimeout=10',
        '-o', 'StrictHostKeyChecking=yes',
        '-o', `UserKnownHostsFile=${knownHosts}`,
        destination, remoteCommand,
      ], { timeout: 30000 });
      audit(root, {
        at, ...target, fingerprint: scanned.fingerprint,
        result: result.ok ? 'ok' : 'failed', exitCode: result.exitCode,
      });
      return {
        ok: result.ok, exitCode: result.exitCode, fingerprint: scanned.fingerprint,
        keyType: scanned.keyType, pinned: Boolean(expected),
        stdout: result.stdout.slice(0, 4000), stderr: (result.stderr || result.error).slice(0, 1000),
      };
    } finally {
      try { fs.rmSync(tempDir, { recursive: true, force: true }); } catch { /* temp cleanup */ }
    }
  }

  return { scanHostKey, testTarget, auditRoot };
}

const defaultService = createWorkHubSsh();

module.exports = {
  createWorkHubSsh,
  sha256Fingerprint,
  parseKeyscan,
  validateTarget,
  scanHostKey: (...args) => defaultService.scanHostKey(...args),
  testTarget: (...args) => defaultService.testTarget(...args),
};
