'use strict';
// Verify prepared changes in memory; preserve exact product source bytes.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const Module = require('node:module');
const root = path.resolve(__dirname, '../../../../../..');
const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, 'approved-patch-initial-proof-timeout-r2.json'), 'utf8'));
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const previousLoader = Module._extensions['.js'];
const candidates = new Map();
for (const entry of manifest.changes) {
  const file = path.join(root, entry.file);
  const original = fs.readFileSync(file);
  if (hash(original) !== entry.before_sha256) throw new Error('EXACT_PRODUCT_SOURCE_CHANGED');
  let source = original.toString('utf8').replace(/\r\n/g, '\n');
  for (const replacement of manifest.replacements.filter(item => item.file === entry.file)) source = source.replace(replacement.before, replacement.after);
  if (hash(source) !== entry.candidate_normalized_sha256) throw new Error('CANDIDATE_SOURCE_HASH_MISMATCH');
  candidates.set(file, source);
}
Module._extensions['.js'] = function (module, file) {
  if (candidates.has(file)) return module._compile(candidates.get(file), file);
  return previousLoader(module, file);
};
try {
  require(path.join(root, 'tests/control-plane-approved-patch-runtime.test.js'));
} finally {
  Module._extensions['.js'] = previousLoader;
  for (const entry of manifest.changes) {
    if (hash(fs.readFileSync(path.join(root, entry.file))) !== entry.before_sha256) throw new Error('PRODUCT_SOURCE_WAS_MODIFIED');
  }
}
