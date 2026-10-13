'use strict';

// The MCP canary owns one new ordinary fixture; all run evidence stays in .coding-tools.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const marker = 'NEW_MACHINE_SHARED_MCP_WRITE_EXEC_20261012_OK';
const expected = Buffer.from(`${marker}\nstage=exact_patch`, 'utf8');
const target = path.resolve(__dirname, '..', '..', '..', 'tests', 'fixtures', 'new-machine-shared-write-proof-20261012-r8.txt');

test('original shared exec Job reads the exact MCP-created and patched ordinary fixture', () => {
  assert.equal(process.platform, 'win32');
  assert.ok(Number(process.versions.node.split('.')[0]) >= 22);
  const actual = fs.readFileSync(target);
  assert.deepEqual(actual, expected);
  console.log(`${marker} sha256=${crypto.createHash('sha256').update(actual).digest('hex')}`);
});
