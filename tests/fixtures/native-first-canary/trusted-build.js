'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const crypto = require('node:crypto');
assert.equal(process.platform, 'win32');
const digest = crypto.createHash('sha256');
for (let i = 1; i <= 100; i += 1) {
  const index = String(i).padStart(3, '0');
  const expected = `NATIVE_FIRST_CANARY_V1\nfile=${index}\nstage=${i <= 20 ? 'patched' : 'seed'}\n`;
  const value = fs.readFileSync(`file-${index}.txt`);
  assert.deepEqual(value, Buffer.from(expected, 'utf8'));
  digest.update(value);
}
const artifact = 'NATIVE_FIRST_CANARY_BUILD_V1 ' + digest.digest('hex') + '\n';
fs.writeFileSync('build-artifact.txt', artifact, {encoding: 'utf8', flag: 'wx'});
console.log(artifact.trim());
