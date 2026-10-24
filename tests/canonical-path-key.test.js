'use strict';

// Regression for the r21 CI gate 8.3-alias family (24/10/2026): a directory
// spelled two ways — short name, junction, symlink, subst — is the same
// directory, so every identity key must agree across the alias. A junction
// stands in for the 8.3 short form here: both are alternate spellings that
// only realpath collapses (on Windows, junction creation needs no privilege,
// unlike symlinks). The 89 runner tests themselves prove the true 8.3 case.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { canonicalPathKey, pathTraversesReparsePoint } = require('../electron/services/pathSemantics');
const { workspaceKey } = require('../electron/services/config');
const { samePath } = require('../electron/services/recoveryActionStore');
const { pathHasPrefix } = require('../electron/services/workHubFiles');

function aliasFixture(t) {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'webcodex-canonical-key-'));
  t.after(() => fs.rmSync(temp, { recursive: true, force: true }));
  const target = path.join(temp, 'real-workspace');
  fs.mkdirSync(path.join(target, 'child'), { recursive: true });
  const alias = path.join(temp, 'alias-workspace');
  fs.symlinkSync(target, alias, process.platform === 'win32' ? 'junction' : 'dir');
  return { temp, target, alias };
}

test('canonical path keys match across a directory alias', (t) => {
  const { target, alias } = aliasFixture(t);
  assert.equal(canonicalPathKey(alias), canonicalPathKey(target));
  assert.equal(workspaceKey(alias), workspaceKey(target));
  assert.equal(samePath(alias, target), true);
  // The aliased child exists, so its key resolves through the alias.
  assert.equal(pathHasPrefix(path.join(alias, 'child'), target), true);
  assert.equal(pathHasPrefix(path.join(target, 'child'), alias), true);
  // A sibling with a shared string prefix is not under the prefix.
  assert.equal(pathHasPrefix(`${target}-sibling`, target), false);
});

test('canonical path keys fall back to the resolved spelling for missing paths', (t) => {
  const { temp } = aliasFixture(t);
  const missing = path.join(temp, 'not-yet-created');
  const expected = process.platform === 'win32'
    ? path.normalize(path.resolve(missing)).toLowerCase()
    : path.normalize(path.resolve(missing));
  assert.equal(canonicalPathKey(missing), expected);
  assert.equal(canonicalPathKey(''), '');
});

test('canonical path keys ignore Windows case differences', { skip: process.platform !== 'win32' }, (t) => {
  const { target } = aliasFixture(t);
  assert.equal(canonicalPathKey(target.toUpperCase()), canonicalPathKey(target));
});

test('reparse walk tells alias spellings apart from replaced directories', (t) => {
  const { target, alias } = aliasFixture(t);
  // The alias itself is a reparse point; the plain target is not.
  assert.equal(pathTraversesReparsePoint(alias), true);
  assert.equal(pathTraversesReparsePoint(target), false);
  assert.equal(pathTraversesReparsePoint(path.join(target, 'child')), false);
  // Unstatable paths fail closed.
  assert.equal(pathTraversesReparsePoint(path.join(target, 'missing')), true);
  assert.equal(pathTraversesReparsePoint(''), true);
});
