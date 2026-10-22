'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {
  resolveInsideRoot, listDir, readTextFile, searchText, gitStatus, gitFileDiff,
} = require('../electron/services/workHubFiles');

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'workhub-'));
  fs.mkdirSync(path.join(root, 'src'));
  fs.writeFileSync(path.join(root, 'src', 'login.js'), 'function login() {\n  return checkPassword();\n}\n');
  fs.writeFileSync(path.join(root, 'README.md'), '# Demo\nMật khẩu được kiểm tra ở login.\n');
  fs.writeFileSync(path.join(root, 'bin.dat'), Buffer.from([0, 1, 2, 0, 3]));
  fs.mkdirSync(path.join(root, 'node_modules', 'pkg'), { recursive: true });
  fs.writeFileSync(path.join(root, 'node_modules', 'pkg', 'index.js'), 'checkPassword in dependency\n');
  return root;
}

test('resolveInsideRoot blocks escaping the workspace', () => {
  const root = fixture();
  assert.equal(resolveInsideRoot(root, 'src/login.js').rel, 'src/login.js');
  assert.throws(() => resolveInsideRoot(root, '../outside.txt'), /ngoài thư mục/);
  assert.throws(() => resolveInsideRoot(root, path.join(os.tmpdir(), 'elsewhere.txt')), /ngoài thư mục/);
});

test('F06 listDir lists dirs first with sizes and respects the cap', () => {
  const root = fixture();
  const { entries, rel } = listDir(root, '');
  assert.equal(rel, '');
  assert.equal(entries[0].type, 'dir');
  const readme = entries.find((e) => e.name === 'README.md');
  assert.ok(readme.size > 0);
  const src = listDir(root, 'src');
  assert.deepEqual(src.entries.map((e) => e.name), ['login.js']);
});

test('F06 readTextFile returns text and flags binary files', () => {
  const root = fixture();
  const text = readTextFile(root, 'src/login.js');
  assert.equal(text.binary, false);
  assert.match(text.content, /checkPassword/);
  const bin = readTextFile(root, 'bin.dat');
  assert.equal(bin.binary, true);
  assert.equal(bin.content, '');
});

test('F06 searchText finds content lines and skips dependency dirs', () => {
  const root = fixture();
  const { results } = searchText(root, 'checkPassword');
  assert.ok(results.some((r) => r.rel === 'src/login.js' && r.line === 2));
  assert.ok(!results.some((r) => r.rel.includes('node_modules')));
  assert.throws(() => searchText(root, 'x'), /ít nhất 2 ký tự/);
});

test('F09 git status and diff report working-tree changes', async () => {
  const root = fixture();
  const { execFileSync } = require('node:child_process');
  execFileSync('git', ['init', '-q'], { cwd: root });
  execFileSync('git', ['config', 'user.email', 'test@example.com'], { cwd: root });
  execFileSync('git', ['config', 'user.name', 'Test'], { cwd: root });
  execFileSync('git', ['add', '.'], { cwd: root });
  execFileSync('git', ['commit', '-qm', 'init'], { cwd: root });
  fs.appendFileSync(path.join(root, 'src', 'login.js'), '// changed\n');
  const status = await gitStatus(root);
  assert.ok(status.some((item) => item.path === 'src/login.js'));
  const { diff } = await gitFileDiff(root, 'src/login.js');
  assert.match(diff, /\+.. changed/);
});
