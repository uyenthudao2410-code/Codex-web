'use strict';

// A harmless structured exec proof. This does not accept a RUN or patch.
const test = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');

const marker = 'NEW_MACHINE_SHARED_MCP_EXEC_20261012_OK';

test('new Windows machine runs a Node child through the original exec Job', () => {
  assert.equal(process.platform, 'win32');
  assert.ok(Number(process.versions.node.split('.')[0]) >= 22);
  const child = spawnSync(process.execPath, ['-e', `process.stdout.write('${marker}')`], {
    encoding: 'utf8',
    timeout: 10000,
    windowsHide: true
  });
  assert.equal(child.error, undefined);
  assert.equal(child.status, 0);
  assert.equal(child.stderr, '');
  assert.equal(child.stdout, marker);
  console.log(marker);
});
