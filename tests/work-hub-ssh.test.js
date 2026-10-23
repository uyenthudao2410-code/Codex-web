const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createWorkHubSsh, sha256Fingerprint, parseKeyscan, validateTarget } = require('../electron/services/workHubSsh');

const KEY_B64 = 'ZmFrZS1ob3N0LWtleS1ibG9iLTAxMjM0NTY3ODk=';
const KEY_FP = 'SHA256:LD0dB8zokgnwmXqAw69n4k5/ZCwUSxcF+UiDxkYxDfQ';

function fakeExecFile(scanStdout, sshResult) {
  const calls = [];
  const impl = (file, args, options, callback) => {
    calls.push({ file, args });
    if (file === 'ssh-keyscan') callback(null, scanStdout, '');
    else callback(sshResult?.error || null, sshResult?.stdout || '', sshResult?.stderr || '');
  };
  impl.calls = calls;
  return impl;
}

test('fingerprint matches the OpenSSH SHA256 format for a known key blob', () => {
  assert.equal(sha256Fingerprint(KEY_B64), KEY_FP);
  const parsed = parseKeyscan(`# comment\nexample.com ssh-ed25519 ${KEY_B64}\n`, 'example.com');
  assert.equal(parsed.fingerprint, KEY_FP);
  assert.equal(parsed.keyType, 'ssh-ed25519');
});

test('validateTarget rejects shell metacharacters and traversal', () => {
  assert.throws(() => validateTarget({ host: 'a;rm -rf' }), /không hợp lệ/);
  assert.throws(() => validateTarget({ host: 'ok', remoteDir: '/x/../etc' }), /không hợp lệ/);
  assert.throws(() => validateTarget({ host: 'ok', remoteDir: '/x" ; id' }), /không hợp lệ/);
  assert.equal(validateTarget({ host: 'svhome', user: 'ops', port: 22, remoteDir: '/srv/app' }).remoteDir, '/srv/app');
});

test('scanHostKey parses keyscan output through the injected execFile', async () => {
  const execFile = fakeExecFile(`host.example ssh-rsa ${KEY_B64}\n`);
  const ssh = createWorkHubSsh({ execFile });
  const scanned = await ssh.scanHostKey({ host: 'host.example', port: 2222 });
  assert.equal(scanned.fingerprint, KEY_FP);
  assert.deepEqual(execFile.calls[0].args.slice(0, 4), ['-T', '10', '-p', '2222']);
});

test('scanHostKey falls back to the connect probe when keyscan yields nothing', async () => {
  const impl = (file, args, options, callback) => {
    if (file === 'ssh-keyscan') { callback(null, '', 'choose_kex: unsupported'); return; }
    const kh = args.find((a) => a.startsWith('UserKnownHostsFile=')).slice('UserKnownHostsFile='.length);
    fs.writeFileSync(kh, `host.example ssh-ed25519 ${KEY_B64}\n`);
    callback(new Error('Permission denied'), '', '');
  };
  const ssh = createWorkHubSsh({ execFile: impl });
  const scanned = await ssh.scanHostKey({ host: 'host.example', port: 22 });
  assert.equal(scanned.fingerprint, KEY_FP);
  assert.equal(scanned.via, 'connect-probe');
});

test('testTarget refuses on fingerprint mismatch and audits the refusal', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-ssh-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const execFile = fakeExecFile(`host.example ssh-rsa ${KEY_B64}\n`);
  const ssh = createWorkHubSsh({ execFile });
  await assert.rejects(
    () => ssh.testTarget(root, { host: 'host.example', user: 'ops', expectedFingerprint: 'SHA256:different' }),
    (error) => error.code === 'HOST_KEY_MISMATCH'
  );
  assert.equal(execFile.calls.length, 1, 'ssh must not run after a mismatch');
  const audit = JSON.parse(fs.readFileSync(path.join(root, '.coding-tools', 'work-hub-ssh-audit.json'), 'utf8'));
  assert.equal(audit.records[0].result, 'HOST_KEY_MISMATCH');
});

test('testTarget connects with strict host key checking when the fingerprint matches', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-ssh-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const execFile = fakeExecFile(`host.example ssh-rsa ${KEY_B64}\n`, { stdout: '/srv/app\n M file.js\n' });
  const ssh = createWorkHubSsh({ execFile });
  const result = await ssh.testTarget(root, {
    host: 'host.example', user: 'ops', remoteDir: '/srv/app', expectedFingerprint: KEY_FP,
  });
  assert.equal(result.ok, true);
  assert.equal(result.pinned, true);
  assert.match(result.stdout, /file\.js/);
  const sshCall = execFile.calls.find((c) => c.file === 'ssh');
  assert.ok(sshCall.args.includes('StrictHostKeyChecking=yes'));
  assert.ok(sshCall.args.some((a) => a.startsWith('UserKnownHostsFile=')));
  assert.equal(sshCall.args[sshCall.args.length - 2], 'ops@host.example');
  const audit = JSON.parse(fs.readFileSync(path.join(root, '.coding-tools', 'work-hub-ssh-audit.json'), 'utf8'));
  assert.equal(audit.records[0].result, 'ok');
});
