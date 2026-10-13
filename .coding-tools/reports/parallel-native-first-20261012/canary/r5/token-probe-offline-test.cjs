'use strict';

const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const root = __dirname;
const report = JSON.parse(fs.readFileSync(path.join(root, 'token-probe-build-report-20261013.json'), 'utf8'));
const binary = path.join(root, 'token-child-probe.exe');
assert.equal(crypto.createHash('sha256').update(fs.readFileSync(binary)).digest('hex'), report.binary.sha256);
const launcher = spawnSync(process.execPath, [path.join(root, 'token-child-launcher.js')], {
  cwd: root, encoding: 'utf8', windowsHide: true, timeout: 15000
});
assert.equal(launcher.status, 0, launcher.stderr);
const observed = JSON.parse(launcher.stdout);
assert.equal(observed.shell, false);
assert.equal(observed.child_status, 0);
assert.equal(observed.child_facts.complete, true);
assert.equal(observed.child_facts.open_process_token, true);
assert.equal(observed.child_facts.integrity_sid_valid, true);
assert.equal(observed.child_facts.admin_sid_query_ok, true);
assert.equal(observed.child_facts.sensitive_luid_lookup_success_count, 11);
assert.equal(observed.child_facts.elevated, false);
assert.equal(observed.child_facts.high_or_system_integrity, false);
assert.equal(observed.child_facts.query_errors.elevation, 0);
assert.equal(observed.child_facts.query_errors.app_container, 0);
assert.equal(observed.child_facts.query_errors.integrity, 0);
assert.equal(observed.child_facts.query_errors.groups, 0);
assert.equal(observed.child_facts.query_errors.privileges, 0);
assert.equal(observed.stderr_empty, true);
process.stdout.write('token probe offline test: 1 passed\n');
