'use strict';

// The MCP write canary creates and patches the target. This checker only reads it.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const marker = 'NEW_MACHINE_SHARED_MCP_WRITE_EXEC_20261012_OK';
const expected = Buffer.from(`${marker}\nstage=exact_patch`, 'utf8');

test('original shared exec Job reads the exact MCP-created and patched bytes', () => {
  assert.equal(process.platform, 'win32');
  assert.ok(Number(process.versions.node.split('.')[0]) >= 22);
  const actual = fs.readFileSync(path.join(__dirname, 'shared-write-proof.txt'));
  assert.deepEqual(actual, expected);
  console.log(`${marker} sha256=${crypto.createHash('sha256').update(actual).digest('hex')}`);
});
