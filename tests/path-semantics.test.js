const test = require('node:test');
const assert = require('node:assert/strict');
const {
  normalizeAbsolutePath,
  sameAbsolutePath,
  joinUnderRoot
} = require('../electron/services/pathSemantics');

test('Windows absolute paths retain Windows semantics on a non-Windows test host', () => {
  const root = 'C:\\Users\\tester\\AppData\\Roaming';
  assert.equal(normalizeAbsolutePath(root), root);
  assert.equal(joinUnderRoot(root, 'web-mcp-assistant'), 'C:\\Users\\tester\\AppData\\Roaming\\web-mcp-assistant');
  assert.equal(sameAbsolutePath('c:\\users\\TESTER\\appdata\\roaming', root), true);
});

test('path identity rejects relative and cross-grammar values', () => {
  assert.equal(normalizeAbsolutePath('relative/path'), '');
  assert.equal(sameAbsolutePath('C:\\fixture\\root', '/fixture/root'), false);
});
