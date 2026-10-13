'use strict';
// Copy this exact reviewed fixture to native-first-canary/verify-postimages.cjs
// only after the original full canary. It reads known fixtures and writes none.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
assert.equal(process.platform, 'win32');
assert.equal(path.basename(__dirname), 'native-first-canary');
const digest = crypto.createHash('sha256');
for (let i = 1; i <= 100; i += 1) {
  const index = String(i).padStart(3, '0');
  const expected = Buffer.from(`NATIVE_FIRST_CANARY_V1\nfile=${index}\nstage=${i <= 20 ? 'patched' : 'seed'}\n`, 'utf8');
  const file = path.join(__dirname, `file-${index}.txt`);
  const stat = fs.lstatSync(file);
  assert.equal(stat.isFile(), true);
  assert.equal(stat.isSymbolicLink(), false);
  assert.equal(stat.size, expected.length);
  const value = fs.readFileSync(file);
  assert.deepEqual(value, expected);
  digest.update(value);
}
const expectedArtifact = `NATIVE_FIRST_CANARY_BUILD_V1 ${digest.digest('hex')}\n`;
const artifact = path.join(__dirname, 'build-artifact.txt');
assert.equal(fs.lstatSync(artifact).isSymbolicLink(), false);
assert.equal(fs.readFileSync(artifact, 'utf8'), expectedArtifact);
process.stdout.write('NATIVE_FIRST_POSTIMAGES_VERIFIED 100 20 ' + crypto.createHash('sha256').update(expectedArtifact).digest('hex') + '\n');
