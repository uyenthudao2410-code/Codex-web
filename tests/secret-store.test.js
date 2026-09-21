const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { SecretStore } = require('../electron/services/secretStore');

function makeEncryption(available = true) {
  return {
    isEncryptionAvailable: () => available,
    encryptString: (value) => Buffer.from(String(value), 'utf8'),
    decryptString: (value) => Buffer.from(value).toString('utf8')
  };
}

function makeFixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-secret-store-'));
  const secretsFile = path.join(root, 'nested', 'secrets.bin');
  const paths = { secretsFile: () => secretsFile };
  const encryption = makeEncryption();
  const store = new SecretStore(paths, encryption);
  return {
    root,
    secretsFile,
    backupFile: `${secretsFile}.bak`,
    encryption,
    store,
    cleanup: () => fs.rmSync(root, { recursive: true, force: true })
  };
}

function readEnvelope(file, encryption = makeEncryption()) {
  return JSON.parse(encryption.decryptString(fs.readFileSync(file)));
}

test('SecretStore writes a versioned encrypted envelope and reads values back', (t) => {
  const fixture = makeFixture();
  t.after(fixture.cleanup);

  fixture.store.set('runtimeApiKey', ' runtime-key ');
  fixture.store.set('mcpAuthToken', 'mcp-token');

  assert.equal(fixture.store.get('runtimeApiKey'), 'runtime-key');
  assert.equal(fixture.store.get('mcpAuthToken'), 'mcp-token');
  assert.deepEqual(fixture.store.status(), {
    runtimeApiKey: true,
    mcpAuthToken: true,
    p5A0Seed: false
  });

  const envelope = readEnvelope(fixture.secretsFile, fixture.encryption);
  assert.equal(envelope.schema_version, 1);
  assert.deepEqual(envelope.entries, {
    runtimeApiKey: 'runtime-key',
    mcpAuthToken: 'mcp-token'
  });
});

test('SecretStore migrates the legacy unversioned payload on the next mutation', (t) => {
  const fixture = makeFixture();
  t.after(fixture.cleanup);
  fs.mkdirSync(path.dirname(fixture.secretsFile), { recursive: true });
  fs.writeFileSync(fixture.secretsFile, fixture.encryption.encryptString(JSON.stringify({
    runtimeApiKey: 'legacy-key'
  })));

  assert.equal(fixture.store.get('runtimeApiKey'), 'legacy-key');
  fixture.store.set('mcpAuthToken', 'mcp-token');

  assert.deepEqual(readEnvelope(fixture.secretsFile, fixture.encryption), {
    schema_version: 1,
    entries: {
      runtimeApiKey: 'legacy-key',
      mcpAuthToken: 'mcp-token'
    }
  });
});

test('SecretStore falls back to the last good backup and refuses to overwrite corruption', (t) => {
  const fixture = makeFixture();
  t.after(fixture.cleanup);

  fixture.store.set('runtimeApiKey', 'first-key');
  fixture.store.set('runtimeApiKey', 'second-key');
  assert.equal(fs.existsSync(fixture.backupFile), true);
  fs.writeFileSync(fixture.secretsFile, Buffer.from('not valid encrypted JSON'));

  assert.equal(fixture.store.get('runtimeApiKey'), 'first-key');
  // A valid backup is enough to recover and safely rewrite the primary.
  fixture.store.set('mcpAuthToken', 'recovered-write');
  assert.equal(fixture.store.get('mcpAuthToken'), 'recovered-write');

  // If both copies are unreadable, a mutation must fail closed instead of
  // destroying the only credential evidence.
  fs.writeFileSync(fixture.secretsFile, Buffer.from('primary-corrupt'));
  fs.writeFileSync(fixture.backupFile, Buffer.from('backup-corrupt'));
  assert.throws(
    () => fixture.store.set('new-token', 'must-not-overwrite'),
    /không ghi đè credential hiện có/
  );
  assert.equal(fs.readFileSync(fixture.secretsFile, 'utf8'), 'primary-corrupt');
  assert.equal(fixture.store.get('mcpAuthToken'), '');
});

test('SecretStore fails closed when encryption is unavailable', (t) => {
  const fixture = makeFixture();
  t.after(fixture.cleanup);
  const unavailable = new SecretStore(
    { secretsFile: () => fixture.secretsFile },
    makeEncryption(false)
  );

  assert.deepEqual(unavailable.status(), {
    runtimeApiKey: false,
    mcpAuthToken: false,
    p5A0Seed: false
  });
  assert.throws(() => unavailable.set('runtimeApiKey', 'key'), /không khả dụng/);
  assert.throws(() => unavailable.remove('runtimeApiKey'), /không khả dụng/);
  assert.equal(fs.existsSync(fixture.secretsFile), false);
});

test('SecretStore leaves owner-only files and cleans temporary writes', (t) => {
  const fixture = makeFixture();
  t.after(fixture.cleanup);

  fixture.store.set('runtimeApiKey', 'key');
  fixture.store.set('mcpAuthToken', 'token');
  const files = fs.readdirSync(path.dirname(fixture.secretsFile));
  assert.equal(files.some((name) => name.endsWith('.tmp')), false);

  if (process.platform !== 'win32') {
    assert.equal(fs.statSync(fixture.secretsFile).mode & 0o777, 0o600);
    assert.equal(fs.statSync(fixture.backupFile).mode & 0o777, 0o600);
  }
});
