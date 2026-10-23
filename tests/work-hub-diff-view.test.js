'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const Diff = require('../renderer/diff-view');

const SAMPLE = [
  'diff --git a/src/login.js b/src/login.js',
  'index 1111111..2222222 100644',
  '--- a/src/login.js',
  '+++ b/src/login.js',
  '@@ -1,3 +1,4 @@',
  ' one',
  '-two',
  '+changed',
  '+new',
  ' three',
  '\\ No newline at end of file',
  '',
].join('\n');

test('W2 parseUnifiedDiff numbers context/added/removed like the CoS line model', () => {
  const { lines, truncated, added, removed } = Diff.parseUnifiedDiff(SAMPLE);
  assert.equal(truncated, false);
  assert.equal(added, 2);
  assert.equal(removed, 1);
  const code = lines.filter((line) => ['context', 'added', 'removed'].includes(line.kind));
  assert.deepEqual(code.map((line) => [line.kind, line.old, line.next, line.text]), [
    ['context', 1, 1, 'one'],
    ['removed', 2, null, 'two'],
    ['added', null, 2, 'changed'],
    ['added', null, 3, 'new'],
    ['context', 3, 4, 'three'],
  ]);
  assert.ok(lines.some((line) => line.kind === 'hunk'));
  assert.ok(lines.some((line) => line.kind === 'meta' && line.text.startsWith('diff --git')));
  assert.ok(lines.some((line) => line.kind === 'meta' && line.text.startsWith('\\ No newline')));
});

test('W2 parseUnifiedDiff renumbers at each hunk and never counts section joins', () => {
  const text = [
    '# Đã stage',
    'diff --git a/a.txt b/a.txt',
    '--- a/a.txt',
    '+++ b/a.txt',
    '@@ -10,2 +10,2 @@',
    ' x',
    '-y',
    '+z',
    '',
    '# Chưa stage',
    'diff --git a/a.txt b/a.txt',
    '--- a/a.txt',
    '+++ b/a.txt',
    '@@ -1,1 +1,1 @@',
    '-p',
    '+q',
    '',
  ].join('\n');
  const { lines } = Diff.parseUnifiedDiff(text);
  const code = lines.filter((line) => ['context', 'added', 'removed'].includes(line.kind));
  assert.deepEqual(code.map((line) => [line.kind, line.old, line.next]), [
    ['context', 10, 10],
    ['removed', 11, null],
    ['added', null, 11],
    ['removed', 1, null],
    ['added', null, 1],
  ]);
  assert.ok(lines.some((line) => line.kind === 'meta' && line.text === '# Đã stage'));
  assert.ok(lines.some((line) => line.kind === 'meta' && line.text === '# Chưa stage'));
});

test('W2 parseUnifiedDiff bounds the rendered lines and flags truncation', () => {
  const body = ['diff --git a/big.txt b/big.txt', '--- a/big.txt', '+++ b/big.txt', '@@ -0,0 +1,5000 @@'];
  for (let i = 1; i <= 5000; i += 1) body.push(`+line ${i}`);
  const result = Diff.parseUnifiedDiff(body.join('\n'));
  assert.equal(result.lines.length, Diff.DEFAULT_LIMIT);
  assert.equal(result.truncated, true);
  // Counts stay exact even when the display is bounded.
  assert.equal(result.added, 5000);
  assert.equal(Diff.parseUnifiedDiff(body.join('\n'), { limit: 10 }).lines.length, 10);
});

test('W2 parseUnifiedDiff is total on empty and non-diff text', () => {
  assert.deepEqual(Diff.parseUnifiedDiff(''), { lines: [], truncated: false, added: 0, removed: 0 });
  const plain = Diff.parseUnifiedDiff('Binary files a/x.png and b/x.png differ');
  assert.equal(plain.lines.length, 1);
  assert.equal(plain.lines[0].kind, 'meta');
});
