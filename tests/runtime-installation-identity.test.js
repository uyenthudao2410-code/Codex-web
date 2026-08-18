const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const {
  COMPONENT_SPECS,
  componentOwnsPath,
  RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS
} = require('../electron/services/componentRevision');
const { createInstallationIdentity } = require('../electron/services/runtimeIdentity');

function canonicalTextSha256(file) {
  const content = fs.readFileSync(file, 'utf8').replace(/\r\n/g, '\n');
  return crypto.createHash('sha256').update(Buffer.from(content, 'utf8')).digest('hex');
}

test('runtime identity source belongs to the Recovery Host component revision', () => {
  const relative = 'electron/services/runtimeIdentity.js';
  assert.equal(componentOwnsPath('recovery_host', relative), true);
  assert.ok(COMPONENT_SPECS.recovery_host.files.includes(relative));
});

test('legacy Recovery Host bridge pins the newly added runtime identity source', () => {
  const relative = 'electron/services/runtimeIdentity.js';
  const expected = RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS[relative];
  assert.match(expected, /^[a-f0-9]{64}$/);
  assert.equal(canonicalTextSha256(path.join(__dirname, '..', relative)), expected);
});

test('installation identity contains no raw checkout path', () => {
  const root = path.resolve(__dirname, '..');
  const identity = createInstallationIdentity({
    mode: 'development',
    appRoot: root,
    resourcesRoot: path.join(root, 'resources'),
    executablePath: process.execPath
  });
  const serialized = JSON.stringify(identity);
  assert.equal(serialized.includes(root), false);
  assert.match(identity.installation_id, /^[a-f0-9]{64}$/);
});
